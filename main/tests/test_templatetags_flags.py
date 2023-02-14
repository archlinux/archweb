from main.templatetags.flags import country_flag


def test_country_flag(checklocation):
    flag = country_flag(checklocation.country)
    assert checklocation.country.name in flag
    assert checklocation.country.code.lower() in flag
    assert country_flag(None) == ''
