from main.templatetags.flags import country_flag
from mirrors.tests.conftest import checklocation  # noqa: F401


def test_country_flag(checklocation):  # noqa: F811
    flag = country_flag(checklocation.country)
    assert checklocation.country.name in flag
    assert checklocation.country.code.lower() in flag
    assert country_flag(None) == ''
