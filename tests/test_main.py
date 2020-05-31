from types import MappingProxyType

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

# welcome to the world of mutable/immutable dicts...since there is a bug in
# `cpython` (MappingProxy objects should JSON serialize just like a dictionary)
# affecting python 3.8 (at least), we are enforced to duplicate the
# `post_data_user`...or some of our tests will fail when trying to serialize
# data. So, imho, is easier to create a duplicate of the object than messing
# with previously wrote tests. This affects one of our test
# helpers: `get_superuser_token_headers`
#
# See also: https://bugs.python.org/issue34858
post_data_user = {"username": "johndoe", "password": test_password}
post_data_user_in_mpt = MappingProxyType(post_data_user)
to_delete_user = {"username": "johndoe2", "password": test_password}

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

expected_delete_user = {
    "username": "johndoe2",
    "id": 2,
    "is_active": False,
    "actions": [
        {
            "title": "Account created",
            "id": 2,
            "owner_id": 2,
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


def get_superuser_token_headers(client, user_data=post_data_user_in_mpt):
    r = client.post("/authenticate", data=user_data)
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


@pytest.mark.parametrize(
    "user_data, expected_data",
    [(post_data_user, expected_user), (to_delete_user, expected_delete_user)]
)
def test_create_user(client, datetime_now, user_data, expected_data):
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    assert response.json() == expected_data


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
            "id": 3,
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
        "detail": [
            main.UNAUTHORIZED_USER_QUERY_MSG.format(
                section="profile", user_id=1,
            ),
        ],
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


@pytest.mark.parametrize("user_id,expected_status_code", [(1, 200), (2, 401)])
def test_read_actions_basic(client, user_id, expected_status_code):
    # test query with default parameters
    session_headers_with_token = get_superuser_token_headers(client)
    response = client.get(
        f"/users/{user_id}/actions", headers=session_headers_with_token,
    )
    response_json = response.json()
    assert response.status_code == expected_status_code
    if user_id == 1:
        # user tries to get his data
        assert isinstance(response_json, list) is True
        # we expect at least two actions: create account and
        # one login, but we could have more actions registered
        assert len(response_json) > 2
        for action in response_json:
            expected_keys = {"title", "id", "owner_id", "timestamp"}
            for key in expected_keys:
                assert (key in action) is True
                assert action[key] not in {"", None, False, 0}
    else:
        expected_msg = {
            "detail": main.UNAUTHORIZED_USER_QUERY_MSG.format(
                    section="actions", user_id=1,
            ),
        }
        assert response.json() == expected_msg


@pytest.mark.parametrize(
    "limit,sort", ((2, "asc"), (2, "desc"), (0, "asc"), (0, "desc")),
)
def test_read_actions_with_params(client, limit, sort):
    session_headers_with_token = get_superuser_token_headers(client)
    response = client.get(
        f"/users/1/actions?limit={limit}&sort={sort}",
        headers=session_headers_with_token,
    )
    assert response.status_code == 200
    if limit == 0:
        assert len(response.json()) > 2
    else:
        assert len(response.json()) == 2
    if sort == "asc":
        assert response.json()[0]["title"] == "Account created"
    else:
        assert response.json()[0]["title"] == "Logged into account"


def test_read_actions_wrong_sort_param(client):
    session_headers_with_token = get_superuser_token_headers(client)
    response = client.get(
        "/users/1/actions?sort=wrong_word", headers=session_headers_with_token,
    )
    expected_msg = {
        "detail": main.WRONG_QUERY_ARGUMENTS_MSG.format(
            query_arg="order_direction"
        ) + "It should be one of: `asc` or `desc`."
    }
    assert response.status_code == 400
    assert response.json() == expected_msg


@pytest.mark.parametrize("user_id,expected_status_code", [(1, 200), (2, 401)])
def test_read_last_actions(client, user_id, expected_status_code):
    session_headers_with_token = get_superuser_token_headers(client)
    response = client.get(
        f"/users/{user_id}/last_actions", headers=session_headers_with_token,
    )
    assert response.status_code == expected_status_code
    if user_id == 1:
        # user tries to get his data
        assert isinstance(response.json(), list) is True
    else:
        expected_msg = {
            "detail": main.UNAUTHORIZED_USER_QUERY_MSG.format(
                    section="last actions", user_id=1,
            ),
        }
        assert response.json() == expected_msg


@pytest.mark.parametrize("user_id,expected_status_code", [(1, 401), (2, 200)])
def test_delete_user(client, user_id, expected_status_code):
    user_authentication_data = {1: post_data_user, 2: to_delete_user}

    session_headers_with_token = get_superuser_token_headers(
        client, user_data=MappingProxyType(user_authentication_data[user_id])
    )
    response = client.delete(
        f"/users/2", headers=session_headers_with_token,
    )
    assert response.status_code == expected_status_code
    if user_id == 1:
        assert response.json() == {
            "detail": [
                main.UNAUTHORIZED_USER_QUERY_MSG.format(
                    section="profile", user_id=1
                )
            ]
        }
    else:
        assert response.json() == {"username": "johndoe2", "id": 2}
