post_data_user = {
    "headers": {"X-Token": "coneofsilence"},
    "json": {"username": "johndoe", "password": "string"},

}
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


def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Welcome to user-service"}


def test_create_user(client, datetime_now):
    response = client.post("/users/", **post_data_user)
    assert response.status_code == 200
    assert response.json() == expected_user


def test_create_user_when_already_created(client):
    # test exception when user already registered
    expected_response = {'detail': 'username already registered'}
    response = client.post("/users/", **post_data_user)
    assert response.status_code == 400
    assert response.json() == expected_response


def test_read_user(client):
    response = client.get("/users/1", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    assert response.json() == expected_user
