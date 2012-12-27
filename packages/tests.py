import unittest

from .alpm import AlpmAPI

class AlpmTestCase(unittest.TestCase):
    def test_version(self):
        alpm = AlpmAPI()
        version = alpm.version()
        self.assertIsNotNone(version)
        version = version.split('.')
        # version is a 3-tuple, e.g., '7.0.2'
        self.assertEqual(3, len(version))

    def test_compare_versions(self):
        alpm = AlpmAPI()
        self.assertTrue(alpm.compare_versions("1.0", "<=", "2.0"))
        self.assertTrue(alpm.compare_versions("1.0", "<", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0", ">=", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0", ">", "2.0"))
        self.assertTrue(alpm.compare_versions("1:1.0", ">", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0.2", ">=", "2.1.0"))

        self.assertTrue(alpm.compare_versions("1.0", "=", "1.0"))
        self.assertTrue(alpm.compare_versions("1.0", "=", "1.0-1"))
        self.assertFalse(alpm.compare_versions("1.0", "!=", "1.0"))

# vim: set ts=4 sw=4 et:
