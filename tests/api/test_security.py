import datetime
import pytest

from passlib.context import CryptContext

from app.api import security

test_password = "my_precious_password"
expected_hash = "$2b$12$xwpxT094Q7KvXIoEKJqj2uFh/r8JzkHbWcMXVKfSKLuwV/OPUfDym"
token_timedelta = datetime.timedelta(
    minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
)
expected_token = (
    b"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjo"
    b"xNTkwODYxOTU1fQ.Fa-D3YT2rph_UZiKClk7la4UPR48ARdrO25Le_vmgi0"
)


def test_password_context():
    assert isinstance(security.pwd_context, CryptContext)
    assert len(security.pwd_context.schemes()) > 0


def test_verify_password():
    assert security.verify_password(test_password, expected_hash) is True
    assert (
        security.verify_password(
            test_password + "any_modification", expected_hash
        )
        is False
    )


def test_get_password_hash():
    """Test that `get_password_hash` return a string"""
    assert isinstance(security.get_password_hash(test_password), str)


@pytest.mark.parametrize("with_delta", (None, token_timedelta,))
def test_create_access_token(datetime_now, with_delta):
    """Test that `create_access_token` behaves as expected."""
    access_token = security.create_access_token(
        data={"sub": "johndoe"}, expires_delta=with_delta
    )
    assert isinstance(access_token, bytes)
    assert access_token == expected_token
