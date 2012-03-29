from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import cache_page
from django.views.generic.simple import direct_to_template

from main.models import Package, Arch, Repo
from devel.models import MasterKey, PGPSignature

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

    def build_map(name, arch, repo):
        key = '%s:%s' % (repo or '', arch or '')
        return {
            'key': key,
            'name': name,
            'arch': arch,
            'repo': repo,
            'data': [],
        }

    # now transform these results into two mappings: one ordered (repo, arch),
    # and one ordered (arch, repo).
    arch_groups = dict((a, build_map(a, a, None)) for a in arches)
    repo_groups = dict((r, build_map(r, None, r)) for r in repos)
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


@cache_page(1800)
def pgp_keys(request):
    node_list = []

    users = User.objects.filter(is_active=True).select_related('userprofile')
    node_list.extend({
            'name': dev.get_full_name(),
            'key': dev.userprofile.pgp_key,
            'group': 'dev'
        } for dev in users.filter(groups__name='Developers'))
    node_list.extend({
            'name': tu.get_full_name(),
            'key': tu.userprofile.pgp_key,
            'group': 'tu'
        } for tu in users.filter(groups__name='Trusted Users').exclude(
            groups__name='Developers'))

    master_keys = MasterKey.objects.select_related('owner').filter(
            revoked__isnull=True)
    node_list.extend({
            'name': 'Master Key (%s)' % key.owner.get_full_name(),
            'key': key.pgp_key,
            'group': 'master'
        } for key in master_keys)

    node_list.append({
        'name': 'CA Cert Signing Authority',
        'key': 'A31D4F81EF4EBD07B456FA04D2BB0D0165D0FD58',
        'group': 'cacert',
    })

    not_expired = Q(expires__gt=datetime.utcnow) | Q(expires__isnull=True)
    signatures = PGPSignature.objects.filter(not_expired, valid=True)
    edge_list = [{ 'signee': sig.signee, 'signer': sig.signer }
            for sig in signatures]

    data = { 'nodes': node_list, 'edges': edge_list }

    to_json = simplejson.dumps(data, ensure_ascii=False)
    return HttpResponse(to_json, mimetype='application/json')

# vim: set ts=4 sw=4 et:
