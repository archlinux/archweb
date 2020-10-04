from datetime import timedelta

from django.test import SimpleTestCase

from mirrors.templatetags.mirror_status import duration, hours, percentage


class MirrorTemplateTagTest(SimpleTestCase):
    def test_duration(self):
        self.assertEqual(duration(None), u'')

        self.assertEqual(duration(timedelta(hours=5)), '5:00')
        self.assertEqual(duration(timedelta(hours=5, seconds=61)), '5:01')
        # Microseconds are skipped
        self.assertEqual(duration(timedelta(microseconds=9999), ), '0:00')

    def test_hours(self):
        self.assertEqual(hours(None), u'')

        self.assertEqual(hours(timedelta(hours=5)), '5 hours')
        self.assertEqual(hours(timedelta(hours=1)), '1 hour')
        self.assertEqual(hours(timedelta(seconds=60 * 60)), '1 hour')

    def test_percentage(self):
        self.assertEqual(percentage(None), u'')
        self.assertEqual(percentage(10), '1000.0%')
        self.assertEqual(percentage(10, 2), '1000.00%')
