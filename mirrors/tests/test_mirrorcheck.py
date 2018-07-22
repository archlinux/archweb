import mock
import time


from django.utils.timezone import now
from datetime import timedelta


from django.test import TestCase
from django.core.management import call_command


from mirrors.tests import create_mirror_url
from mirrors.models import MirrorLog


class MirrorCheckTest(TestCase):
    def setUp(self):
        self.mirror_url = create_mirror_url()

    def tearDown(self):
        self.mirror_url.delete()

    @mock.patch('urllib2.Request')
    @mock.patch('urllib2.urlopen')
    def test_invalid(self, urlopen, Request):
        urlopen.return_value.read.return_value = 'data'
        Request.get_host.return_value = 'archlinux.org'
        Request.type.return_value = 'https'

        call_command('mirrorcheck')
        mirrorlog = MirrorLog.objects.first()
        self.assertNotEqual(mirrorlog.error, '')
        self.assertEqual(mirrorlog.is_success, False)

    @mock.patch('urllib2.Request')
    @mock.patch('urllib2.urlopen')
    def test_valid(self, urlopen, Request):
        urlopen.return_value.read.return_value = str(int(time.time()))
        Request.get_host.return_value = 'archlinux.org'
        Request.type.return_value = 'https'

        call_command('mirrorcheck')
        mirrorlog = MirrorLog.objects.first()
        self.assertEqual(mirrorlog.error, '')
        self.assertEqual(mirrorlog.is_success, True)

    @mock.patch('urllib2.Request')
    @mock.patch('urllib2.urlopen')
    def test_valid(self, urlopen, Request):
        urlopen.return_value.read.return_value = str(int(time.time()))
        Request.get_host.return_value = 'archlinux.org'
        Request.type.return_value = 'https'

        date = now() - timedelta(days=600)
        MirrorLog.objects.create(url=self.mirror_url, check_time=date)
        call_command('mirrorcheck')
        self.assertEqual(len(MirrorLog.objects.all()), 1)
