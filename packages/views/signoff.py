import json
from operator import attrgetter

from django import forms
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import get_list_or_404, redirect, render
from django.utils.timezone import now
from django.views.decorators.cache import never_cache

from main.models import Package, Arch, Repo
from ..models import SignoffSpecification, Signoff
from ..utils import (get_signoff_groups, approved_by_signoffs,
        PackageSignoffGroup)

@permission_required('packages.change_signoff')
def signoffs(request):
    signoff_groups = sorted(get_signoff_groups(), key=attrgetter('pkgbase'))
    for group in signoff_groups:
        group.user = request.user

    context = {
        'signoff_groups': signoff_groups,
        'arches': Arch.objects.all(),
        'repo_names': sorted({g.target_repo for g in signoff_groups}),
    }
    return render(request, 'packages/signoffs.html', context)

@permission_required('packages.change_signoff')
@never_cache
def signoff_package(request, name, repo, arch, revoke=False):
    packages = get_list_or_404(Package, pkgbase=name,
            arch__name=arch, repo__name__iexact=repo, repo__testing=True)
    package = packages[0]

    spec = SignoffSpecification.objects.get_or_default_from_package(package)

    if revoke:
        try:
            signoff = Signoff.objects.get_from_package(
                    package, request.user, False)
        except Signoff.DoesNotExist:
            raise Http404
        signoff.revoked = now()
        signoff.save(update_fields=('revoked',))
        created = False
    else:
        # ensure we should even be accepting signoffs
        if spec.known_bad or not spec.enabled:
            return render(request, '403.html', status=403)
        signoff, created = Signoff.objects.get_or_create_from_package(
                package, request.user)

    all_signoffs = Signoff.objects.for_package(package)

    if request.is_ajax():
        data = {
            'created': created,
            'revoked': bool(signoff.revoked),
            'approved': approved_by_signoffs(all_signoffs, spec),
            'required': spec.required,
            'enabled': spec.enabled,
            'known_bad': spec.known_bad,
            'user': str(request.user),
        }
        return HttpResponse(json.dumps(data, ensure_ascii=False),
                content_type='application/json')

    return redirect('package-signoffs')

class SignoffOptionsForm(forms.ModelForm):
    apply_all = forms.BooleanField(required=False,
        help_text="Apply these options to all architectures?")

    class Meta:
        model = SignoffSpecification
        fields = ('required', 'enabled', 'known_bad', 'comments')

def _signoff_options_all(request, name, repo):
    seen_ids = set()
    with transaction.atomic():
        # find or create a specification for all architectures, then
        # graft the form data onto them
        packages = Package.objects.filter(pkgbase=name,
            repo__name__iexact=repo, repo__testing=True)
        for package in packages:
            try:
                spec = SignoffSpecification.objects.get_from_package(package)
                if spec.pk in seen_ids:
                    continue
            except SignoffSpecification.DoesNotExist:
                spec = SignoffSpecification(pkgbase=package.pkgbase,
                        pkgver=package.pkgver, pkgrel=package.pkgrel,
                        epoch=package.epoch, arch=package.arch,
                        repo=package.repo)

            if spec.user is None:
                spec.user = request.user

            form = SignoffOptionsForm(request.POST, instance=spec)
            if form.is_valid():
                form.save()
            seen_ids.add(form.instance.pk)

@permission_required('main.change_package')
@never_cache
def signoff_options(request, name, repo, arch):
    packages = get_list_or_404(Package, pkgbase=name,
            arch__name=arch, repo__name__iexact=repo, repo__testing=True)
    package = packages[0]

    if request.user != package.packager and \
            request.user not in package.maintainers:
        return render(request, '403.html', status=403)

    try:
        spec = SignoffSpecification.objects.get_from_package(package)
    except SignoffSpecification.DoesNotExist:
        # create a fake one, but don't save it just yet
        spec = SignoffSpecification(pkgbase=package.pkgbase,
                pkgver=package.pkgver, pkgrel=package.pkgrel,
                epoch=package.epoch, arch=package.arch, repo=package.repo)

    if spec.user is None:
        spec.user = request.user

    if request.POST:
        form = SignoffOptionsForm(request.POST, instance=spec)
        if form.is_valid():
            if form.cleaned_data['apply_all']:
                _signoff_options_all(request, name, repo)
            else:
                form.save()
            return redirect('package-signoffs')
    else:
        form = SignoffOptionsForm(instance=spec)

    context = {
        'packages': packages,
        'package': package,
        'form': form,
    }
    return render(request, 'packages/signoff_options.html', context)

class SignoffJSONEncoder(DjangoJSONEncoder):
    '''Base JSONEncoder extended to handle all serialization of all classes
    related to signoffs.'''
    signoff_group_attrs = ['arch', 'last_update', 'maintainers', 'packager',
            'pkgbase', 'repo', 'signoffs', 'target_repo', 'version']
    signoff_spec_attrs = ['required', 'enabled', 'known_bad', 'comments']
    signoff_attrs = ['user', 'created', 'revoked']

    def default(self, obj):
        if isinstance(obj, PackageSignoffGroup):
            data = {attr: getattr(obj, attr)
                    for attr in self.signoff_group_attrs}
            data['pkgnames'] = [p.pkgname for p in obj.packages]
            data['package_count'] = len(obj.packages)
            data['approved'] = obj.approved()
            data.update((attr, getattr(obj.specification, attr))
                    for attr in self.signoff_spec_attrs)
            return data
        elif isinstance(obj, Signoff):
            return {attr: getattr(obj, attr) for attr in self.signoff_attrs}
        elif isinstance(obj, Arch) or isinstance(obj, Repo):
            return str(obj)
        elif isinstance(obj, User):
            return obj.username
        elif isinstance(obj, set):
            return list(obj)
        return super(SignoffJSONEncoder, self).default(obj)

@permission_required('packages.change_signoff')
def signoffs_json(request):
    signoff_groups = sorted(get_signoff_groups(), key=attrgetter('pkgbase'))
    data = {
        'version': 2,
        'signoff_groups': signoff_groups,
    }
    to_json = json.dumps(data, ensure_ascii=False, cls=SignoffJSONEncoder)
    response = HttpResponse(to_json, content_type='application/json')
    return response

# vim: set ts=4 sw=4 et:
