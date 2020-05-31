import pytest

from fastapi import HTTPException

from app.api import utils
from tests.conftest import FAKE_TIME


def test_get_timestamp(datetime_now):
    timestamp = utils.get_timestamp()
    expected_datetime = FAKE_TIME.strftime("%Y-%m-%d %H:%M:%S")
    assert timestamp == expected_datetime


def test_check_user_id():
    # when ids are equal, we should receive `True`
    assert utils.check_user_id(1, 1, "fake_section") is True

    # test exception when ids doesn't match
    expected_message = utils.UNAUTHORIZED_USER_QUERY_MSG.format(
        section="fake_section", user_id=1,
    )
    with pytest.raises(HTTPException) as http_exception:
        utils.check_user_id(1, 2, "fake_section")
    assert expected_message in str(http_exception)
