from mirrors.models import MirrorUrl, MirrorProtocol, Mirror


def create_mirror_url(name='mirror1', country='US',
                      protocol='http', url='https://archlinux.org/'):
        mirror = Mirror.objects.create(name=name,
                                       admin_email='admin@archlinux.org')
        mirror_protocol = MirrorProtocol.objects.create(protocol=protocol)
        mirror_url = MirrorUrl.objects.create(url=url,
                                              protocol=mirror_protocol,
                                              mirror=mirror,
                                              country=country)
        return mirror_url
