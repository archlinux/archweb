import mock
import time


from django.utils.timezone import now
from datetime import timedelta


from django.test import TestCase
from django.core.management import call_command


from mirrors.tests import create_mirror_url
from mirrors.models import MirrorLog, CheckLocation


class MirrorCheckTest(TestCase):
    def setUp(self):
        self.mirror_url = create_mirror_url()

    def tearDown(self):
        self.mirror_url.delete()

    @mock.patch('urllib.request.Request')
    @mock.patch('urllib.request.urlopen')
    def test_invalid(self, urlopen, Request):
        urlopen.return_value.read.return_value = 'data'
        Request.get_host.return_value = 'archlinux.org'
        Request.type.return_value = 'https'

        call_command('mirrorcheck')
        mirrorlog = MirrorLog.objects.first()
        self.assertNotEqual(mirrorlog.error, '')
        self.assertEqual(mirrorlog.is_success, False)

    @mock.patch('urllib.request.Request')
    @mock.patch('urllib.request.urlopen')
    def test_valid(self, urlopen, Request):
        urlopen.return_value.read.return_value = str(int(time.time()))
        Request.get_host.return_value = 'archlinux.org'
        Request.type.return_value = 'https'

        call_command('mirrorcheck')
        mirrorlog = MirrorLog.objects.first()
        self.assertEqual(mirrorlog.error, '')
        self.assertEqual(mirrorlog.is_success, True)

    @mock.patch('urllib.request.Request')
    @mock.patch('urllib.request.urlopen')
    def test_valid(self, urlopen, Request):
        urlopen.return_value.read.return_value = str(int(time.time()))
        Request.get_host.return_value = 'archlinux.org'
        Request.type.return_value = 'https'

        date = now() - timedelta(days=600)
        MirrorLog.objects.create(url=self.mirror_url, check_time=date)
        call_command('mirrorcheck')
        self.assertEqual(len(MirrorLog.objects.all()), 1)

    def test_checklocation(self):
        with self.assertRaises(CheckLocation.DoesNotExist) as e:
            call_command('mirrorcheck', '-l', '1')
        self.assertEqual('CheckLocation matching query does not exist.', str(e.exception))

    def test_checklocation_model(self):
        checkloc = CheckLocation.objects.create(hostname='archlinux.org',
                                                     source_ip='1.1.1.1')
        with mock.patch('mirrors.management.commands.mirrorcheck.logger') as logger:
            call_command('mirrorcheck', '-l', '1')
        logger.info.assert_called()

        checkloc.delete()
