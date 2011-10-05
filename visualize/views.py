from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import cache_page
from django.views.generic.simple import direct_to_template

from main.models import Package, Arch, Repo

def index(request):
    return direct_to_template(request, 'visualize/index.html', {})

def arch_repo_data():
    qs = Package.objects.select_related().values(
            'arch__name', 'repo__name').annotate(
            count=Count('pk'), csize=Sum('compressed_size'),
            isize=Sum('installed_size'),
            flagged=Count('flag_date')).order_by()
    arches = Arch.objects.values_list('name', flat=True)
    repos = Repo.objects.values_list('name', flat=True)

    # now transform these results into two mappings: one ordered (repo, arch),
    # and one ordered (arch, repo).
    arch_groups = dict((a, { 'name': a, 'key': ':%s' % a, 'arch': a, 'repo': None, 'data': [] }) for a in arches)
    repo_groups = dict((r, { 'name': r, 'key': '%s:' % r, 'arch': None, 'repo': r, 'data': [] }) for r in repos)
    for row in qs:
        arch = row['arch__name']
        repo = row['repo__name']
        values = {
            'arch': arch,
            'repo': repo,
            'name': '%s (%s)' % (repo, arch),
            'key': '%s:%s' % (repo, arch),
            'csize': row['csize'],
            'isize': row['isize'],
            'count': row['count'],
            'flagged': row['flagged'],
        }
        arch_groups[arch]['data'].append(values)
        repo_groups[repo]['data'].append(values)

    data = {
        'by_arch': { 'name': 'Architectures', 'data': arch_groups.values() },
        'by_repo': { 'name': 'Repositories', 'data': repo_groups.values() },
    }
    return data

@cache_page(1800)
def by_arch(request):
    data = arch_repo_data()
    to_json = simplejson.dumps(data['by_arch'], ensure_ascii=False)
    return HttpResponse(to_json, mimetype='application/json')

@cache_page(1800)
def by_repo(request):
    data = arch_repo_data()
    to_json = simplejson.dumps(data['by_repo'], ensure_ascii=False)
    return HttpResponse(to_json, mimetype='application/json')

# vim: set ts=4 sw=4 et:
