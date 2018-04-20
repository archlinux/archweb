from datetime import datetime
import json
from operator import attrgetter

from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_control, cache_page

from devel.models import MasterKey, DeveloperKey, PGPSignature, StaffGroup, UserProfile
from main.models import Arch, Repo, Donor
from mirrors.models import MirrorUrl
from news.models import News
from releng.models import Release
from .utils import get_recent_updates


@cache_control(max_age=307)
def index(request):
    if request.user.is_authenticated():
        def updates():
            return get_recent_updates(testing=True, staging=True)
    else:
        def updates():
            return get_recent_updates()
    domain = "%s://%s" % (request.scheme, request.META.get('HTTP_HOST'))
    context = {
        'news_updates': News.objects.order_by('-postdate', '-id')[:15],
        'pkg_updates': updates,
        'staff_groups': StaffGroup.objects.all(),
        'domain': domain,
    }
    return render(request, 'public/index.html', context)


@cache_control(max_age=307)
def people(request, slug):
    group = get_object_or_404(StaffGroup, slug=slug)
    users = User.objects.filter(groups=group.group).order_by(
            'first_name', 'last_name').select_related('userprofile')

    context = {'group': group, 'users': users}
    return render(request, 'public/userlist.html', context)


@cache_control(max_age=307)
def donate(request):
    context = {
        'donors': Donor.objects.filter(visible=True).order_by('name'),
    }
    return render(request, 'public/donate.html', context)


def _mirror_urls():
    '''In order to ensure this is lazily evaluated since we can't do
    sorting at the database level, make it a callable.'''
    urls = MirrorUrl.objects.select_related('mirror').filter(
            active=True, protocol__default=True,
            mirror__public=True, mirror__active=True, mirror__isos=True)
    sort_by = attrgetter('country.name', 'mirror.name')
    return sorted(urls, key=sort_by)


@cache_control(max_age=307)
def download(request):
    try:
        release = Release.objects.filter(available=True).latest()
    except Release.DoesNotExist:
        release = None

    context = {
        'release': release,
        'mirror_urls': _mirror_urls,
    }
    return render(request, 'public/download.html', context)


@cache_control(max_age=307)
def feeds(request):
    repos = Repo.objects.all()
    if not request.user.is_authenticated():
        repos = repos.filter(staging=False)
    context = {
        'arches': Arch.objects.all(),
        'repos': repos,
    }
    return render(request, 'public/feeds.html', context)


@cache_control(max_age=307)
def keys(request):
    profile_ids = UserProfile.allowed_repos.through.objects.values('userprofile_id')
    users = User.objects.filter(
            is_active=True, userprofile__id__in=profile_ids).order_by('first_name', 'last_name')
    user_key_ids = frozenset(user.userprofile.pgp_key[-16:] for user in users
            if user.userprofile.pgp_key)

    not_expired = Q(expires__gt=datetime.utcnow()) | Q(expires__isnull=True)
    master_keys = MasterKey.objects.select_related('owner', 'revoker',
            'owner__userprofile', 'revoker__userprofile').filter(
            revoked__isnull=True)

    sig_counts = PGPSignature.objects.filter(not_expired, revoked__isnull=True,
            signee__in=user_key_ids).order_by().values_list('signer').annotate(
            Count('signer'))
    sig_counts = {key_id[-16:]: ct for key_id, ct in sig_counts}

    for key in master_keys:
        key.signature_count = sig_counts.get(key.pgp_key[-16:], 0)

    # frozenset because we are going to do lots of __contains__ lookups
    signatures = frozenset(PGPSignature.objects.filter(
            not_expired, revoked__isnull=True).values_list('signer', 'signee'))

    cross_signatures = PGPSignature.objects.filter(
            not_expired, revoked__isnull=True).order_by('created')
    # filter in python so we aren't sending a crazy long query to the DB
    cross_signatures = [s for s in cross_signatures
            if s.signer in user_key_ids and s.signee in user_key_ids]

    developer_keys = DeveloperKey.objects.select_related(
            'owner').filter(owner__isnull=False)
    developer_keys = {key.key[-16:]: key for key in developer_keys}

    context = {
        'keys': master_keys,
        'active_users': users,
        'signatures': signatures,
        'cross_signatures': cross_signatures,
        'developer_keys': developer_keys,
    }
    return render(request, 'public/keys.html', context)


@cache_page(1789)
def keys_json(request):
    profile_ids = UserProfile.allowed_repos.through.objects.values('userprofile_id')
    users = User.objects.filter(
            is_active=True, userprofile__id__in=profile_ids).order_by('first_name', 'last_name')
    node_list = [{
            'name': user.get_full_name(),
            'key': user.userprofile.pgp_key,
            'group': 'packager'
        } for user in users]

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

    not_expired = Q(expires__gt=datetime.utcnow()) | Q(expires__isnull=True)
    signatures = PGPSignature.objects.filter(not_expired, revoked__isnull=True)
    edge_list = [{ 'signee': sig.signee, 'signer': sig.signer }
            for sig in signatures]

    data = { 'nodes': node_list, 'edges': edge_list }

    to_json = json.dumps(data, ensure_ascii=False)
    return HttpResponse(to_json, content_type='application/json')

# vim: set ts=4 sw=4 et:
