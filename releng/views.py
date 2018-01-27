from base64 import b64decode
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView

from .models import (Iso, Release)
from mirrors.models import MirrorUrl


def iso_overview(request):
    isos = Iso.objects.all().order_by('-pk')
    successes = dict(Iso.objects.values_list('pk').filter(
        test__success=True).annotate(ct=Count('test')))
    failures = dict(Iso.objects.values_list('pk').filter(
        test__success=False).annotate(ct=Count('test')))
    for iso in isos:
        iso.successes = successes.get(iso.pk, 0)
        iso.failures = failures.get(iso.pk, 0)

    # only show "useful" rows, currently active ISOs or those with results
    isos = [iso for iso in isos if
            iso.active is True or iso.successes > 0 or iso.failures > 0]

    context = {
        'isos': isos
    }
    return render(request, 'releng/iso_overview.html', context)


class ReleaseListView(ListView):
    model = Release


class ReleaseDetailView(DetailView):
    model = Release
    slug_field = 'version'
    slug_url_kwarg = 'version'


def release_torrent(request, version):
    release = get_object_or_404(Release, version=version)
    if not release.torrent_data:
        raise Http404
    data = b64decode(release.torrent_data.encode('utf-8'))
    response = HttpResponse(data, content_type='application/x-bittorrent')
    # TODO: this is duplicated from Release.iso_url()
    filename = 'archlinux-%s-x86_64.iso.torrent' % release.version
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


class ReleaseJSONEncoder(DjangoJSONEncoder):
    release_attributes = ('release_date', 'version', 'kernel_version',
            'created', 'md5_sum', 'sha1_sum')

    def default(self, obj):
        if isinstance(obj, Release):
            data = {attr: getattr(obj, attr) or None
                    for attr in self.release_attributes}
            data['available'] = obj.available
            data['iso_url'] = '/' + obj.iso_url()
            data['magnet_uri'] = obj.magnet_uri()
            data['torrent_url'] = reverse('releng-release-torrent', args=[obj.version])
            data['info'] = obj.info_html()
            torrent_data = obj.torrent()
            if torrent_data:
                torrent_data.pop('url_list', None)
            data['torrent'] = torrent_data
            return data
        return super(ReleaseJSONEncoder, self).default(obj)


def releases_json(request):
    releases = Release.objects.all()
    try:
        latest_version = Release.objects.filter(available=True).values_list(
                'version', flat=True).latest()
    except Release.DoesNotExist:
        latest_version = None

    data = {
        'version': 1,
        'releases': list(releases),
        'latest_version': latest_version,
    }
    to_json = json.dumps(data, ensure_ascii=False, cls=ReleaseJSONEncoder)
    response = HttpResponse(to_json, content_type='application/json')
    return response

def netboot_config(request):
    release_qs = Release.objects.filter(available=True).order_by('-release_date')
    releases = [release.version for release in release_qs]
    mirrorurls = MirrorUrl.objects.filter(protocol__protocol='http',
                                          active=True,
                                          mirror__public=True,
                                          mirror__active=True,
                                          mirror__isos=True)
    mirrorurls = sorted( mirrorurls,
                         key=lambda x: x.mirror.name)
    mirrorurls = sorted( mirrorurls,
                         key=lambda x: x.country.name)
    context = {
        'releases': releases,
        'mirrorurls': mirrorurls,
    }
    return render(request, "releng/archlinux.ipxe", context, content_type='text/plain')

def netboot_info(request):
    return render(request, "releng/netboot.html", None)

# vim: set ts=4 sw=4 et:
