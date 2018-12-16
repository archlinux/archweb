import json
import operator
from functools import reduce

from django import forms
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.views.generic import ListView

from devel.models import UserProfile
from main.models import Package, Arch, Repo
from main.utils import empty_response, make_choice
from ..models import PackageRelation
from ..utils import attach_maintainers, PackageJSONEncoder


class PackageSearchForm(forms.Form):
    limit = forms.CharField(required=False)
    page = forms.CharField(required=False)
    repo = forms.MultipleChoiceField(required=False)
    arch = forms.MultipleChoiceField(required=False)
    name = forms.CharField(required=False)
    desc = forms.CharField(required=False)
    q = forms.CharField(required=False)
    sort = forms.CharField(required=False, widget=forms.HiddenInput())
    maintainer = forms.ChoiceField(required=False)
    packager = forms.ChoiceField(required=False)
    flagged = forms.ChoiceField(
            choices=[('', 'All')] + make_choice(['Flagged', 'Not Flagged']),
            required=False)

    def __init__(self, *args, **kwargs):
        show_staging = kwargs.pop('show_staging', False)
        super(PackageSearchForm, self).__init__(*args, **kwargs)
        repos = Repo.objects.all()
        if not show_staging:
            repos = repos.filter(staging=False)
        self.fields['repo'].choices = make_choice(
                        [repo.name for repo in repos])
        self.fields['arch'].choices = make_choice(
                        [arch.name for arch in Arch.objects.all()])
        self.fields['q'].widget.attrs.update({"size": "30"})

        profile_ids = UserProfile.allowed_repos.through.objects.values('userprofile_id')
        people = User.objects.filter(
                is_active=True, userprofile__id__in=profile_ids).order_by(
                'first_name', 'last_name')
        maintainers = [('', 'All'), ('orphan', 'Orphan')] + \
                 [(p.username, p.get_full_name()) for p in people]
        packagers = [('', 'All'), ('unknown', 'Unknown')] + \
                 [(p.username, p.get_full_name()) for p in people]

        self.fields['maintainer'].choices = maintainers
        self.fields['packager'].choices = packagers

    def exact_matches(self):
        # only do exact match search if 'q' is sole parameter
        if self.changed_data != ['q']:
            return []
        return Package.objects.normal().filter(pkgname=self.cleaned_data['q'])


def parse_form(form, packages):
    if form.cleaned_data['repo']:
        packages = packages.filter(
                repo__name__in=form.cleaned_data['repo'])

    if form.cleaned_data['arch']:
        packages = packages.filter(
                arch__name__in=form.cleaned_data['arch'])

    if form.cleaned_data['maintainer'] == 'orphan':
        inner_q = PackageRelation.objects.all().values('pkgbase')
        packages = packages.exclude(pkgbase__in=inner_q)
    elif form.cleaned_data['maintainer']:
        inner_q = PackageRelation.objects.filter(
                user__username=form.cleaned_data['maintainer']).values('pkgbase')
        packages = packages.filter(pkgbase__in=inner_q)

    if form.cleaned_data['packager'] == 'unknown':
        packages = packages.filter(packager__isnull=True)
    elif form.cleaned_data['packager']:
        packages = packages.filter(
                packager__username=form.cleaned_data['packager'])

    if form.cleaned_data['flagged'] == 'Flagged':
        packages = packages.filter(flag_date__isnull=False)
    elif form.cleaned_data['flagged'] == 'Not Flagged':
        packages = packages.filter(flag_date__isnull=True)

    if form.cleaned_data['name']:
        name = form.cleaned_data['name']
        packages = packages.filter(pkgname=name)

    if form.cleaned_data['desc']:
        desc = form.cleaned_data['desc']
        packages = packages.filter(pkgdesc__icontains=desc)

    if form.cleaned_data['q']:
        query = form.cleaned_data['q']
        q_pkgname = reduce(operator.__and__,
                           (Q(pkgname__icontains=q) for q in query.split()))
        q_pkgdesc = reduce(operator.__and__,
                           (Q(pkgdesc__icontains=q) for q in query.split()))
        packages = packages.filter(q_pkgname | q_pkgdesc)

    return packages


class SearchListView(ListView):
    template_name = "packages/search.html"
    paginate_by = 100

    sort_fields = ("arch", "repo", "pkgname", "pkgbase", "compressed_size",
            "installed_size", "build_date", "last_update", "flag_date")
    allowed_sort = list(sort_fields) + ["-" + s for s in sort_fields]

    def get(self, request, *args, **kwargs):
        if request.method == 'HEAD':
            return empty_response()
        self.form = PackageSearchForm(data=request.GET,
                show_staging=self.request.user.is_authenticated)
        return super(SearchListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        packages = Package.objects.normal()
        if not self.request.user.is_authenticated:
            packages = packages.filter(repo__staging=False)
        if self.form.is_valid():
            packages = parse_form(self.form, packages)
            sort = self.form.cleaned_data['sort']
            if sort in self.allowed_sort:
                packages = packages.order_by(sort)
            else:
                packages = packages.order_by('pkgname')
            return packages

        # Form had errors so don't return any results
        return Package.objects.none()

    def get_context_data(self, **kwargs):
        context = super(SearchListView, self).get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['current_query'] = query_params.urlencode()
        context['search_form'] = self.form
        return context


def search_json(request):
    limit = 250

    container = {
        'version': 2,
        'limit': limit,
        'valid': False,
        'results': [],
    }

    if request.GET:
        form = PackageSearchForm(data=request.GET,
                show_staging=request.user.is_authenticated)
        if form.is_valid():
            form_limit = form.cleaned_data['limit']
            limit = min(limit, int(form_limit)) if form_limit else limit
            container['limit'] = limit

            packages = Package.objects.select_related('arch', 'repo',
                    'packager')
            if not request.user.is_authenticated:
                packages = packages.filter(repo__staging=False)
            packages = parse_form(form, packages)

            paginator = Paginator(packages, limit)
            container['num_pages'] = paginator.num_pages

            page = form.cleaned_data.get('page')
            page = int(page) if page else 1
            container['page'] = page
            try:
                packages = paginator.page(page)
            except PageNotAnInteger:
                packages = paginator.page(1)
            except EmptyPage:
                packages = paginator.page(paginator.num_pages)

            attach_maintainers(packages)
            container['results'] = packages
            container['valid'] = True

    to_json = json.dumps(container, ensure_ascii=False, cls=PackageJSONEncoder)
    return HttpResponse(to_json, content_type='application/json')

# vim: set ts=4 sw=4 et:
