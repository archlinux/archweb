import re

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.mail import EmailMessage
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader, Context
from django.utils.timezone import now
from django.views.decorators.cache import cache_page, never_cache

from ..models import FlagRequest
from main.models import Package


class FlagForm(forms.Form):
    email = forms.EmailField(label='E-mail Address')
    message = forms.CharField(label='Message To Developer',
            widget=forms.Textarea)
    # The field below is used to filter out bots that blindly fill out all
    # input elements
    website = forms.CharField(label='',
            widget=forms.TextInput(attrs={'style': 'display:none;'}),
            required=False)

    def __init__(self, *args, **kwargs):
        # we remove the 'email' field if this form is being shown to a
        # logged-in user, e.g., a developer.
        auth = kwargs.pop('authenticated', False)
        super(FlagForm, self).__init__(*args, **kwargs)
        if auth:
            del self.fields['email']

    def clean_message(self):
        data = self.cleaned_data['message']
        # make sure the message isn't garbage (only punctuation or whitespace)
        # and ensure a certain minimum length
        if re.match(r'^[^0-9A-Za-z]+$', data) or len(data) < 3:
            raise forms.ValidationError(
                    "Enter a valid and useful out-of-date message.")
        return data


@cache_page(3600)
def flaghelp(request):
    return render(request, 'packages/flaghelp.html')


@never_cache
def flag(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    if pkg.flag_date is not None:
        # already flagged. do nothing.
        return render(request, 'packages/flagged.html', {'pkg': pkg})
    # find all packages from (hopefully) the same PKGBUILD
    pkgs = Package.objects.normal().filter(
            pkgbase=pkg.pkgbase, flag_date__isnull=True,
            repo__testing=pkg.repo.testing,
            repo__staging=pkg.repo.staging).order_by(
            'pkgname', 'repo__name', 'arch__name')

    authenticated = request.user.is_authenticated()

    if request.POST:
        form = FlagForm(request.POST, authenticated=authenticated)
        if form.is_valid() and form.cleaned_data['website'] == '':
            # save the package list for later use
            flagged_pkgs = list(pkgs)

            # find a common version if there is one available to store
            versions = set((pkg.pkgver, pkg.pkgrel, pkg.epoch)
                    for pkg in flagged_pkgs)
            if len(versions) == 1:
                version = versions.pop()
            else:
                version = ('', '', 0)

            message = form.cleaned_data['message']
            ip_addr = request.META.get('REMOTE_ADDR')
            if authenticated:
                email = request.user.email
            else:
                email = form.cleaned_data['email']

            @transaction.atomic
            def perform_updates():
                current_time = now()
                pkgs.update(flag_date=current_time)
                # store our flag request
                flag_request = FlagRequest(created=current_time,
                        user_email=email, message=message,
                        ip_address=ip_addr, pkgbase=pkg.pkgbase,
                        repo=pkg.repo, pkgver=version[0], pkgrel=version[1],
                        epoch=version[2], num_packages=len(flagged_pkgs))
                if authenticated:
                    flag_request.user = request.user
                flag_request.save()

            perform_updates()

            maints = pkg.maintainers
            if not maints:
                toemail = settings.NOTIFICATIONS
                subject = 'Orphan %s package [%s] marked out-of-date' % \
                        (pkg.repo.name, pkg.pkgname)
            else:
                toemail = []
                subject = '%s package [%s] marked out-of-date' % \
                        (pkg.repo.name, pkg.pkgname)
                for maint in maints:
                    if maint.userprofile.notify is True:
                        toemail.append(maint.email)

            if toemail:
                # send notification email to the maintainers
                tmpl = loader.get_template('packages/outofdate.txt')
                ctx = Context({
                    'email': email,
                    'message': message,
                    'pkg': pkg,
                    'packages': flagged_pkgs,
                })
                msg = EmailMessage(subject,
                        tmpl.render(ctx),
                        'Arch Website Notification <nobody@archlinux.org>',
                        toemail,
                        headers={"Reply-To": email }
                )
                msg.send(fail_silently=True)

            return redirect('package-flag-confirmed', name=name, repo=repo,
                    arch=arch)
    else:
        form = FlagForm(authenticated=authenticated)

    context = {
        'package': pkg,
        'packages': pkgs,
        'form': form
    }
    return render(request, 'packages/flag.html', context)

def flag_confirmed(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    pkgs = Package.objects.normal().filter(
            pkgbase=pkg.pkgbase, flag_date=pkg.flag_date,
            repo__testing=pkg.repo.testing,
            repo__staging=pkg.repo.staging).order_by(
            'pkgname', 'repo__name', 'arch__name')

    context = {'package': pkg, 'packages': pkgs}

    return render(request, 'packages/flag_confirmed.html', context)

@permission_required('main.change_package')
def unflag(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    pkg.flag_date = None
    pkg.save()
    return redirect(pkg)

@permission_required('main.change_package')
def unflag_all(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    # find all packages from (hopefully) the same PKGBUILD
    pkgs = Package.objects.filter(pkgbase=pkg.pkgbase,
            repo__testing=pkg.repo.testing, repo__staging=pkg.repo.staging)
    pkgs.update(flag_date=None)
    return redirect(pkg)

# vim: set ts=4 sw=4 et:
