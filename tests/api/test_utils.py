import datetime
import pytest

from app.api import utils

FAKE_TIME = datetime.datetime(2020, 5, 30, 17, 35, 55)


@pytest.fixture
def patch_datetime_now(monkeypatch):

    class FakeDateTime:
        @classmethod
        def now(cls):
            return FAKE_TIME

    monkeypatch.setattr(utils, 'datetime', FakeDateTime)


def test_get_timestamp(patch_datetime_now):
    timestamp = utils.get_timestamp()
    expected_datetime = FAKE_TIME.strftime("%Y-%m-%d %H:%M:%S")
    assert timestamp == expected_datetime
