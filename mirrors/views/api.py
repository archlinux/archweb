from datetime import timedelta
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from ..models import (Mirror, MirrorUrl, MirrorProtocol, MirrorLog,
        CheckLocation)
from ..utils import get_mirror_statuses, DEFAULT_CUTOFF


class MirrorStatusJSONEncoder(DjangoJSONEncoder):
    '''Base JSONEncoder extended to handle datetime.timedelta and MirrorUrl
    serialization. The base class takes care of datetime.datetime types.'''
    url_attributes = ('url', 'protocol', 'last_sync', 'completion_pct',
            'delay', 'duration_avg', 'duration_stddev', 'score', 'active')

    def default(self, obj):
        if isinstance(obj, timedelta):
            # always returned as integer seconds
            return obj.days * 24 * 3600 + obj.seconds
        if isinstance(obj, MirrorUrl):
            data = {attr: getattr(obj, attr) for attr in self.url_attributes}
            country = obj.country
            data['country'] = str(country.name)
            data['country_code'] = country.code
            data['isos'] = obj.mirror.isos
            data['ipv4'] = obj.has_ipv4
            data['ipv6'] = obj.has_ipv6
            data['details'] = obj.get_full_url()
            return data
        if isinstance(obj, MirrorProtocol):
            return str(obj)
        return super(MirrorStatusJSONEncoder, self).default(obj)


class ExtendedMirrorStatusJSONEncoder(MirrorStatusJSONEncoder):
    '''Adds URL check history information.'''
    log_attributes = ('check_time', 'last_sync', 'duration', 'is_success',
            'location_id')

    def default(self, obj):
        if isinstance(obj, MirrorUrl):
            data = super(ExtendedMirrorStatusJSONEncoder, self).default(obj)
            cutoff = now() - DEFAULT_CUTOFF
            data['logs'] = list(obj.logs.filter(
                    check_time__gte=cutoff).order_by('check_time'))
            return data
        if isinstance(obj, MirrorLog):
            data = {attr: getattr(obj, attr) for attr in self.log_attributes}
            data['error'] = obj.error or None
            return data
        return super(ExtendedMirrorStatusJSONEncoder, self).default(obj)


class LocationJSONEncoder(DjangoJSONEncoder):
    '''Base JSONEncoder extended to handle CheckLocation objects.'''

    def default(self, obj):
        if isinstance(obj, CheckLocation):
            return {
                'id': obj.pk,
                'hostname': obj.hostname,
                'source_ip': obj.source_ip,
                'country': str(obj.country.name),
                'country_code': obj.country.code,
                'ip_version': obj.ip_version,
            }
        return super(LocationJSONEncoder, self).default(obj)


def status_json(request, tier=None):
    if tier is not None:
        tier = int(tier)
        if tier not in [t[0] for t in Mirror.TIER_CHOICES]:
            raise Http404
    status_info = get_mirror_statuses()
    data = status_info.copy()
    if tier is not None:
        data['urls'] = [url for url in data['urls'] if url.mirror.tier == tier]
    data['version'] = 3
    to_json = json.dumps(data, ensure_ascii=False, cls=MirrorStatusJSONEncoder)
    response = HttpResponse(to_json, content_type='application/json')
    return response


def mirror_details_json(request, name):
    authorized = request.user.is_authenticated()
    mirror = get_object_or_404(Mirror, name=name)
    if not authorized and (not mirror.public or not mirror.active):
        raise Http404
    status_info = get_mirror_statuses(mirror_id=mirror.id,
            show_all=authorized)
    data = status_info.copy()
    data['version'] = 4
    data['details'] = mirror.get_full_url()
    if authorized and request.user.has_perm('mirrors.change_mirror'):
        data['admin_email'] = mirror.admin_email
        data['alternate_email'] = mirror.alternate_email
    to_json = json.dumps(data, ensure_ascii=False,
            cls=ExtendedMirrorStatusJSONEncoder)
    response = HttpResponse(to_json, content_type='application/json')
    return response


def locations_json(request):
    data = {}
    data['version'] = 1
    data['locations'] = list(CheckLocation.objects.all().order_by('pk'))
    to_json = json.dumps(data, ensure_ascii=False, cls=LocationJSONEncoder)
    response = HttpResponse(to_json, content_type='application/json')
    return response

# vim: set ts=4 sw=4 et:
