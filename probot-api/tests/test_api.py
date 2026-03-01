def _signup(client, name="Alice", email="alice@example.com", password="password123", extra=None):
    payload = {"name": name, "email": email, "password": password}
    if extra:
        payload.update(extra)
    return client.post("/api/v1/signup/", json=payload)

def _login(client, email="alice@example.com", password="password123"):
    return client.post("/api/v1/login/", json={"email": email, "password": password})

def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_signup_success_default_role(client):
    r = _signup(client)
    assert r.status_code == 201, r.get_json()
    data = r.get_json()
    assert data["status"] == "created"
    assert data["user"]["email"] == "alice@example.com"

    assert data["user"]["role_name"] == "user"
    assert isinstance(data["user"]["user_role"], int)


def test_signup_rejects_user_role_modification_attempt(client):

    r = _signup(client, extra={"user_role": 999, "role_name": "admin"})
    assert r.status_code == 201
    data = r.get_json()
    assert data["user"]["role_name"] == "user"


def test_signup_duplicate_email_conflict(client):
    r1 = _signup(client)
    assert r1.status_code == 201
    r2 = _signup(client)
    assert r2.status_code == 409
    assert "email" in r2.get_json()["error"]


def test_login_success_returns_token(client):
    _signup(client)
    r = _login(client)
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert "token" in data
    assert data["user"]["email"] == "alice@example.com"


def test_login_wrong_password(client):
    _signup(client)
    r = _login(client, password="wrong")
    assert r.status_code == 401
    assert "invalid credentials" in r.get_json()["error"]


def test_get_user_requires_auth(client):
    # signup
    r = _signup(client)
    user_key = r.get_json()["user"]["user_key"]

    # no token
    r2 = client.get(f"/api/v1/users/{user_key}/")
    assert r2.status_code == 401


def test_get_user_only_self_allowed(client):
    # user1
    r1 = _signup(client, name="Alice", email="alice@example.com")
    key1 = r1.get_json()["user"]["user_key"]
    token1 = _login(client, "alice@example.com").get_json()["token"]

    # user2
    r2 = _signup(client, name="Bob", email="bob@example.com")
    key2 = r2.get_json()["user"]["user_key"]

    # user1 tries to read user2
    r = client.get(f"/api/v1/users/{key2}/", headers=_auth_header(token1))
    assert r.status_code == 403


def test_get_user_success(client):
    r1 = _signup(client)
    key = r1.get_json()["user"]["user_key"]
    token = _login(client).get_json()["token"]

    r = client.get(f"/api/v1/users/{key}/", headers=_auth_header(token))
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert data["user_key"] == key
    assert data["email"] == "alice@example.com"


def test_update_user_success_name_and_password(client):
    r1 = _signup(client)
    key = r1.get_json()["user"]["user_key"]
    token = _login(client).get_json()["token"]

    # update name + password
    r = client.put(
        f"/api/v1/users/{key}/",
        json={"name": "Alice2", "password": "newpassword123"},
        headers=_auth_header(token),
    )
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["user"]["name"] == "Alice2"

    # login with old password should fail
    r_old = _login(client, "alice@example.com", "password123")
    assert r_old.status_code == 401

    # login with new password should succeed
    r_new = _login(client, "alice@example.com", "newpassword123")
    assert r_new.status_code == 200


def test_update_user_forbids_user_role_change(client):
    r1 = _signup(client)
    key = r1.get_json()["user"]["user_key"]
    token = _login(client).get_json()["token"]

    r = client.put(
        f"/api/v1/users/{key}/",
        json={"user_role": 2},
        headers=_auth_header(token),
    )
    assert r.status_code == 403
    assert "cannot be modified" in r.get_json()["error"]


def test_update_user_duplicate_email_conflict(client):
    # create two users
    r1 = _signup(client, name="Alice", email="alice@example.com")
    key1 = r1.get_json()["user"]["user_key"]
    token1 = _login(client, "alice@example.com").get_json()["token"]

    _signup(client, name="Bob", email="bob@example.com")

    # user1 tries to change email to bob@example.com
    r = client.put(
        f"/api/v1/users/{key1}/",
        json={"email": "bob@example.com"},
        headers=_auth_header(token1),
    )
    assert r.status_code == 409


def test_delete_user_success_and_then_login_fails(client):
    r1 = _signup(client)
    key = r1.get_json()["user"]["user_key"]
    token = _login(client).get_json()["token"]

    r = client.delete(f"/api/v1/users/{key}/", headers=_auth_header(token))
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["status"] == "deleted"

    # login should fail (user not found or invalid creds)
    r2 = _login(client)
    assert r2.status_code == 401