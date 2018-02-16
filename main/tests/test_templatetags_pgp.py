from django.conf import settings
from django.test import TestCase

from main.templatetags.pgp import pgp_key_link, format_key, pgp_fingerprint


class PGPTemplateTest(TestCase):


    def test_format_key(self):
        # 40 len case
        pgp_key = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
        pgp_key_len = len(pgp_key)

        output = format_key(pgp_key)
        spaces = output.count(' ') + output.count('\xa0')  # nbsp
        self.assertEqual(pgp_key_len + spaces, len(output))

        # 21 - 39 len case
        pgp_key = '3E2C81117BFB1108D234DAFZ'
        pgp_key_len = len(pgp_key) + len('0x')
        self.assertEqual(pgp_key_len, len(format_key(pgp_key)))

        # 8, 20 len case
        pgp_key = '3E2C81117BFB1108DEFF'
        pgp_key_len = len(pgp_key) + len('0x')
        self.assertEqual(pgp_key_len, len(format_key(pgp_key)))

        # 0 - 7 len case
        pgp_key = 'B1108D'
        pgp_key_len = len(pgp_key) + len('0x')
        self.assertEqual(pgp_key_len, len(format_key(pgp_key)))

    def assert_pgp_key_link(self, pgp_key):
        output = pgp_key_link(int(pgp_key, 16))
        self.assertIn(pgp_key[2:], output)
        self.assertIn("https", output)

    def test_pgp_key_link(self):
        self.assertEqual(pgp_key_link(""), "Unknown")

        pgp_key = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
        output = pgp_key_link(pgp_key)
        self.assertIn(pgp_key, output)
        self.assertIn("https", output)

        output = pgp_key_link(pgp_key, "test")
        self.assertIn("test", output)
        self.assertIn("https", output)

        # Numeric key_id <= 8
        self.assert_pgp_key_link('0x0023BDC7')

        # Numeric key_id <= 16
        self.assert_pgp_key_link('0xBDC7FF5E34A12F')

        # Numeric key_id <= 40
        self.assert_pgp_key_link('0xA10E234343EA8BDC7FF5E34A12F')

        pgp_key = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
        server = getattr(settings, 'PGP_SERVER')

        with self.settings(PGP_SERVER=''):
            self.assertNotIn(server, pgp_key_link(pgp_key))

        with self.settings(PGP_SERVER_SECURE=False):
            pgp_key = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
            self.assertNotIn("https", pgp_key_link(pgp_key))

    def test_pgp_fingerprint(self):
        self.assertEqual(pgp_fingerprint(None), "")
        keyid = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
        fingerprint = pgp_fingerprint(keyid)
        self.assertTrue(len(fingerprint) > len(keyid))
