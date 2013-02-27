import unittest

from .alpm import AlpmAPI


alpm = AlpmAPI()


class AlpmTestCase(unittest.TestCase):

    @unittest.skipUnless(alpm.available, "ALPM is unavailable")
    def test_version(self):
        version = alpm.version()
        self.assertIsNotNone(version)
        version = version.split('.')
        # version is a 3-tuple, e.g., '7.0.2'
        self.assertEqual(3, len(version))

    @unittest.skipUnless(alpm.available, "ALPM is unavailable")
    def test_vercmp(self):
        self.assertEqual(0, alpm.vercmp("1.0", "1.0"))
        self.assertEqual(1, alpm.vercmp("1.1", "1.0"))

    @unittest.skipUnless(alpm.available, "ALPM is unavailable")
    def test_compare_versions(self):
        self.assertTrue(alpm.compare_versions("1.0", "<=", "2.0"))
        self.assertTrue(alpm.compare_versions("1.0", "<", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0", ">=", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0", ">", "2.0"))
        self.assertTrue(alpm.compare_versions("1:1.0", ">", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0.2", ">=", "2.1.0"))

        self.assertTrue(alpm.compare_versions("1.0", "=", "1.0"))
        self.assertTrue(alpm.compare_versions("1.0", "=", "1.0-1"))
        self.assertFalse(alpm.compare_versions("1.0", "!=", "1.0"))

    def test_behavior_when_unavailable(self):
        mock_alpm = AlpmAPI()
        mock_alpm.available = False

        self.assertIsNone(mock_alpm.version())
        self.assertIsNone(mock_alpm.vercmp("1.0", "1.0"))
        self.assertIsNone(mock_alpm.compare_versions("1.0", "=", "1.0"))


# vim: set ts=4 sw=4 et:
