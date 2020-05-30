import jwt
import pytest
from fastapi import HTTPException
from sqlalchemy import orm

from app import main
from tests.api.test_security import expected_token, test_password

headers_authenticated_user = {
    "Content-Type": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Bearer {expected_token.decode('utf-8')}",
}

post_data_user = {"username": "johndoe", "password": test_password}
expected_user = {
    "username": "johndoe",
    "id": 1,
    "is_active": False,
    "actions": [
        {
            "title": "Account created",
            "id": 1,
            "owner_id": 1,
            "timestamp": "2020-05-30 17:35:55",
        }
    ],
}
expected_credentials_exception = (
    "<ExceptionInfo HTTPException(status_code=401, "
    "detail='Could not validate credentials') tblen=2>"
)


@pytest.fixture
def mock_get_db_yield():
    yield from main.get_db()


class FakeJwtReturnValueNone:
    """Fake jwt object that returns `None` when executing `decode`."""
    return_value = None

    @classmethod
    def decode(cls, *args, **kwargs):
        return {"sub": cls.return_value}


class FakeJwtRaiseException:
    """Fake jwt object that raises `jwt.PyJWTError` when executing `decode`."""
    def decode(*args, **kwargs):
        raise jwt.PyJWTError


class FakeJwtReturnValueUser(FakeJwtReturnValueNone):
    """
    Subclass of `FakeJwtReturnValueNone` that modifies returns an `string`
    (representing an username) when executing `decode`.
    """
    return_value = "non-existent-user"


@pytest.fixture
def mock_jwt_decode_return_none(monkeypatch):
    monkeypatch.setattr(main, "jwt", FakeJwtReturnValueNone)


@pytest.fixture
def mock_jwt_decode_return_user(monkeypatch):
    monkeypatch.setattr(main, "jwt", FakeJwtReturnValueUser)


@pytest.fixture
def mock_jwt_decode_raise_exception(monkeypatch):
    monkeypatch.setattr(main, "jwt", FakeJwtRaiseException)


def get_superuser_token_headers(client):
    r = client.post("/authenticate", data=post_data_user)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


def test_get_db(mock_get_db_yield):
    assert isinstance(mock_get_db_yield, orm.session.Session)


def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Welcome to user-service"}


def test_create_user(client, datetime_now):
    response = client.post("/users/", json=post_data_user)
    assert response.status_code == 200
    assert response.json() == expected_user


def test_create_user_when_already_created(client):
    # test exception when user already registered
    expected_response = {"detail": "username already registered"}
    response = client.post("/users/", json=post_data_user)
    assert response.status_code == 400
    assert response.json() == expected_response


def test_authenticate(client, datetime_now):
    response = client.post(
        "/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=post_data_user,
    )
    assert response.status_code == 200
    assert response.json() == {
        "access_token": expected_token.decode("utf-8"),
        "token_type": "bearer",
    }


def test_read_user_not_authenticated(client):
    response = client.get("/users/1", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_read_user(client):
    session_headers_with_token = get_superuser_token_headers(client)
    response = client.get("/users/1", headers=session_headers_with_token)
    response_json = response.json()
    assert response.status_code == 200
    assert "actions" in response_json

    # remove actions and test that we below two actions (the ones we mocked
    # the datetime: test_create_user and test_authenticate) are in our result
    response_actions = response_json.pop("actions")
    first_two_expected_actions = [
        {
            "title": "Account created",
            "id": 1,
            "owner_id": 1,
            "timestamp": "2020-05-30 17:35:55",
        },
        {
            "title": "Logged into account",
            "id": 2,
            "owner_id": 1,
            "timestamp": "2020-05-30 17:35:55",
        },
    ]
    for ac in first_two_expected_actions:
        assert (ac in response_actions) is True
    assert (len(response_actions) > 2) is True

    # Check remaining data against our expected user
    for key in response_json.keys():
        assert response_json[key] == expected_user[key]

    # Test that an user cannot get info from another user
    expected_msg = {
        "detail": (
            "You are not allowed to view the profile of another user, "
            f"please, use your own id: `{expected_user['id']}`."
        )
    }
    response = client.get("/users/2", headers=session_headers_with_token)
    assert response.status_code == 401
    assert response.json() == expected_msg


def test_login_with_wrong_credentials(client):
    response = client.post(
        "/authenticate",
        data={
            "username": post_data_user["username"],
            "password": post_data_user["password"] + "x",
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_authenticate_user_non_existent(client):
    response = client.post(
        "/authenticate",
        data={
            "username": post_data_user["username"] + "x",
            "password": post_data_user["password"],
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


@pytest.mark.asyncio
async def test_get_current_user_payload_error(
        mock_jwt_decode_return_none, mock_get_db_yield,
):
    with pytest.raises(HTTPException) as excinfo:
        await main.get_current_user(
            "whatever",
            mock_get_db_yield,
        )
    assert str(excinfo) == expected_credentials_exception


@pytest.mark.asyncio
async def test_get_current_user_jwt_exception(
        mock_jwt_decode_raise_exception, mock_get_db_yield,
):
    with pytest.raises(HTTPException) as excinfo:
        await main.get_current_user(
            "whatever",
            mock_get_db_yield,
        )
    assert str(excinfo) == expected_credentials_exception


@pytest.mark.asyncio
async def test_get_current_user_db_error_no_user(
        mock_jwt_decode_return_user, mock_get_db_yield,
):
    with pytest.raises(HTTPException) as excinfo:
        await main.get_current_user(
            "non-existent-user",
            mock_get_db_yield,
        )
    assert str(excinfo) == expected_credentials_exception
