from mirrors.models import MirrorUrl, MirrorProtocol, Mirror


def create_mirror_url():
        mirror = Mirror.objects.create(name='mirror1',
                                       admin_email='admin@archlinux.org')
        mirror_protocol = MirrorProtocol.objects.create(protocol='http')
        mirror_url = MirrorUrl.objects.create(url='https://archlinux.org',
                                              protocol=mirror_protocol,
                                              mirror=mirror,
                                              country='US')
        return mirror_url
