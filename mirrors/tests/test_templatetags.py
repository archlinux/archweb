from datetime import timedelta

from mirrors.templatetags.mirror_status import duration, hours, percentage


def test_duration():
    assert duration(None) == ''

    assert duration(timedelta(hours=5)) == '5:00'
    assert duration(timedelta(hours=5, seconds=61)) == '5:01'

    # Microseconds are skipped
    assert duration(timedelta(microseconds=9999)) == '0:00'


def test_hours():
    assert hours(None) == ''

    assert hours(timedelta(hours=5)) == '5 hours'
    assert hours(timedelta(hours=1)) == '1 hour'
    assert hours(timedelta(seconds=60*60)) == '1 hour'


def test_percentage():
    assert percentage(None) == ''
    assert percentage(10) == '1000.0%'
    assert percentage(10, 2) == '1000.00%'
