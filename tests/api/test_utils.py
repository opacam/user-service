from app.api import utils
from tests.conftest import FAKE_TIME


def test_get_timestamp(datetime_now):
    timestamp = utils.get_timestamp()
    expected_datetime = FAKE_TIME.strftime("%Y-%m-%d %H:%M:%S")
    assert timestamp == expected_datetime
