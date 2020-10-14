from main.templatetags.pgp import pgp_key_link, format_key, pgp_fingerprint


def test_format_key():
    # 40 len case
    pgp_key = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
    pgp_key_len = len(pgp_key)

    output = format_key(pgp_key)
    spaces = output.count(' ') + output.count('\xa0')  # nbsp
    assert pgp_key_len + spaces == len(output)

    # 21 - 39 len case
    pgp_key = '3E2C81117BFB1108D234DAFZ'
    pgp_key_len = len(pgp_key) + len('0x')
    assert pgp_key_len == len(format_key(pgp_key))

    # 8, 20 len case
    pgp_key = '3E2C81117BFB1108DEFF'
    pgp_key_len = len(pgp_key) + len('0x')
    assert pgp_key_len == len(format_key(pgp_key))

    # 0 - 7 len case
    pgp_key = 'B1108D'
    pgp_key_len = len(pgp_key) + len('0x')
    assert pgp_key_len == len(format_key(pgp_key))


def assert_pgp_key_link(pgp_key):
    output = pgp_key_link(int(pgp_key, 16))
    assert pgp_key[2:] in output
    assert "https" in output


def test_pgp_key_link(settings):
    assert pgp_key_link("") == "Unknown"

    pgp_key = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
    output = pgp_key_link(pgp_key)
    assert pgp_key in output
    assert "https" in output

    output = pgp_key_link(pgp_key, "test")
    assert "test" in output
    assert "https" in output

    # Numeric key_id <= 8
    assert_pgp_key_link('0x0023BDC7')

    # Numeric key_id <= 16
    assert_pgp_key_link('0xBDC7FF5E34A12F')

    # Numeric key_id <= 40
    assert_pgp_key_link('0xA10E234343EA8BDC7FF5E34A12F')

    pgp_key = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
    server = settings.PGP_SERVER

    settings.PGP_SERVER = ''
    assert server not in pgp_key_link(pgp_key)


    settings.PGP_SERVER_SECURE = False
    settings.PGP_SERVER = server
    pgp_key = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
    assert not "https" in pgp_key_link(pgp_key)

def test_pgp_fingerprint():
    assert pgp_fingerprint(None) == ""
    keyid = '423423fD9004FB063E2C81117BFB1108D234DAFZ'
    fingerprint = pgp_fingerprint(keyid)
    assert len(fingerprint) > len(keyid)
