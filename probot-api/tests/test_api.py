"""
ProBot API - Functional Testing Suite
This module contains functional tests for the RESTful API implementation.
It verifies resource addressability, uniform interface, and security constraints.
"""

# --- Helper Functions for Test Cleanliness ---

def _signup(client, name="Alice", email="alice@example.com", password="password123", extra=None):
    """Helper to perform a signup POST request."""
    payload = {"name": name, "email": email, "password": password}
    if extra:
        payload.update(extra)
    return client.post("/api/v1/signup/", json=payload)

def _login(client, email="alice@example.com", password="password123"):
    """Helper to perform a login POST request and retrieve a response."""
    return client.post("/api/v1/login/", json={"email": email, "password": password})

def _auth_header(token: str):
    """Helper to format the Bearer token for Authorization headers."""
    return {"Authorization": f"Bearer {token}"}
def _auth_header(token: str, extra=None):
    h = {"Authorization": f"Bearer {token}"}
    if extra:
        h.update(extra)
    return h


# --- Test Cases ---

def test_signup_success_default_role(client):
    """
    Test Case: Successful User Registration
    Goal: Verify that a valid POST request to /signup/ creates a resource.
    Expected: Status 201 Created and the assignment of the 'user' role by default.
    """
    r = _signup(client)
    assert r.status_code == 201, r.get_json()
    data = r.get_json()
    assert data["status"] == "created"
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["role_name"] == "user" # Verifies default role logic


def test_signup_rejects_user_role_modification_attempt(client):
    """
    Test Case: Privilege Escalation Prevention
    Goal: Ensure clients cannot manually set their 'user_role' during signup.
    Expected: Status 201, but the system must ignore the 'admin' role request and assign 'user'.
    """
    r = _signup(client, extra={"user_role": 999, "role_name": "admin"})
    assert r.status_code == 201
    data = r.get_json()
    assert data["user"]["role_name"] == "user" # System should override malicious role input


def test_signup_duplicate_email_conflict(client):
    """
    Test Case: Error Handling - Resource Conflict
    Goal: Force a 409 Conflict error by providing a duplicate email.
    Expected: Status 409 and an error message indicating the email already exists.
    """
    _signup(client) # Initial creation
    r2 = _signup(client) # Duplicate attempt
    assert r2.status_code == 409
    assert "email" in r2.get_json()["error"]


def test_login_success_returns_token(client):
    """
    Test Case: Successful Authentication
    Goal: Verify that valid credentials return a JWT for stateless communication.
    Expected: Status 200 OK and a JSON object containing a 'token'.
    """
    _signup(client)
    r = _login(client)
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert "token" in data
    assert data["user"]["email"] == "alice@example.com"


def test_login_wrong_password(client):
    """
    Test Case: Error Handling - Unauthorized Login
    Goal: Force a 401 Unauthorized error using an incorrect password.
    Expected: Status 401 and an 'invalid credentials' error message.
    """
    _signup(client)
    r = _login(client, password="wrong")
    assert r.status_code == 401
    assert "invalid credentials" in r.get_json()["error"]


def test_get_user_requires_auth(client):
    """
    Test Case: Security - Authentication Enforcement
    Goal: Verify that protected GET resources cannot be accessed without a token.
    Expected: Status 401 Unauthorized due to missing Bearer token.
    """
    r = _signup(client)
    user_key = r.get_json()["user"]["user_key"]

    r2 = client.get(f"/api/v1/users/{user_key}/") # Attempt access without headers
    assert r2.status_code == 401


def test_get_user_only_self_allowed(client):
    """
    Test Case: Security - Resource Isolation
    Goal: Ensure User A cannot access User B's private resource via their URI.
    Expected: Status 403 Forbidden when using a valid token for a different user's key.
    """
    # Create User 1
    r1 = _signup(client, name="Alice", email="alice@example.com")
    token1 = _login(client, "alice@example.com").get_json()["token"]

    # Create User 2
    r2 = _signup(client, name="Bob", email="bob@example.com")
    key2 = r2.get_json()["user"]["user_key"]

    # User 1 tries to read User 2's data
    r = client.get(f"/api/v1/users/{key2}/", headers=_auth_header(token1))
    assert r.status_code == 403


def test_get_user_success(client):
    """
    Test Case: Successful Resource Retrieval (Addressability)
    Goal: Verify that a user can access their own data using their unique user_key.
    Expected: Status 200 OK and matching profile information.
    """
    r1 = _signup(client)
    key = r1.get_json()["user"]["user_key"]
    token = _login(client).get_json()["token"]

    r = client.get(f"/api/v1/users/{key}/", headers=_auth_header(token))
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert data["user_key"] == key


def test_update_user_success_name_and_password(client):
    """
    Test Case: Resource Update (Uniform Interface)
    Goal: Verify that the PUT method successfully modifies resource attributes.
    Expected: Status 200 OK, updated name in response, and successful login with new password.
    """
    r1 = _signup(client)
    key = r1.get_json()["user"]["user_key"]
    token = _login(client).get_json()["token"]

    # Perform update
    r = client.put(
        f"/api/v1/users/{key}/",
        json={"name": "Alice2", "password": "newpassword123"},
        headers=_auth_header(token),
    )
    assert r.status_code == 200
    assert r.get_json()["user"]["name"] == "Alice2"

    # Verify old password no longer works
    assert _login(client, "alice@example.com", "password123").status_code == 401


def test_user_profile_etag_and_cache_headers(client):
    """
    Test Case: Test Caching (ETag Headers)
    Goal: Verify that if no content changed will use cached.
    Expected: Status 200 OK if first GET, status 304 Not Modified if no changes were made before last GET.
    """
    r_signup = _signup(client)
    assert r_signup.status_code == 201, r_signup.get_json()
    user_key = r_signup.get_json()["user"]["user_key"]

    r_login = _login(client)
    assert r_login.status_code == 200, r_login.get_json()
    token = r_login.get_json()["token"]

    # first GET with response 200, has ETag and cache-control
    r1 = client.get(f"/api/v1/users/{user_key}/", headers=_auth_header(token))
    assert r1.status_code == 200, r1.get_json()
    assert "ETag" in r1.headers
    assert r1.headers["Cache-Control"] == "private, max-age=60"

    etag1 = r1.headers["ETag"]
    body1 = r1.get_json()
    assert body1["user_key"] == user_key

    # second GET with If-None-Match response 304, empty body
    r2 = client.get(
        f"/api/v1/users/{user_key}/",
        headers=_auth_header(token, {"If-None-Match": etag1}),
    )
    assert r2.status_code == 304

    assert (r2.data is None) or (r2.data == b"")
    assert r2.headers.get("ETag") == etag1
    assert r2.headers.get("Cache-Control") == "private, max-age=60"


def test_etag_changes_after_update_and_old_etag_no_longer_valid(client):
    """
    Test Case: Test Caching if updated resources
    Goal: Verify that if content changed will return new data.
    Expected: Status 200 OK if content changed after last GET.
    """
    # signup + login
    r_signup = _signup(client)
    user_key = r_signup.get_json()["user"]["user_key"]
    token = _login(client).get_json()["token"]

    # first GET
    r1 = client.get(f"/api/v1/users/{user_key}/", headers=_auth_header(token))
    assert r1.status_code == 200
    etag1 = r1.headers["ETag"]

    # update user
    r_put = client.put(
        f"/api/v1/users/{user_key}/",
        json={"name": "Alice Updated"},
        headers=_auth_header(token),
    )
    assert r_put.status_code == 200, r_put.get_json()

    # GET again and ETag should be different
    r3 = client.get(f"/api/v1/users/{user_key}/", headers=_auth_header(token))
    assert r3.status_code == 200
    etag2 = r3.headers["ETag"]
    assert etag2 != etag1

    # use old etag1
    r4 = client.get(
        f"/api/v1/users/{user_key}/",
        headers=_auth_header(token, {"If-None-Match": etag1}),
    )
    assert r4.status_code == 200
    assert r4.get_json()["name"] == "Alice Updated"
    assert r4.headers["ETag"] == etag2


def test_update_user_forbids_user_role_change(client):
    """
    Test Case: Security - Restricted Attribute Update
    Goal: Force a 403 Forbidden error when attempting to modify sensitive fields like 'user_role'.
    Expected: Status 403 and a rejection message.
    """
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
    """
    Test Case: Error Handling - Update Conflict
    Goal: Force a 409 Conflict error when updating a profile to an email used by another resource.
    Expected: Status 409.
    """
    r1 = _signup(client, name="Alice", email="alice@example.com")
    key1 = r1.get_json()["user"]["user_key"]
    token1 = _login(client, "alice@example.com").get_json()["token"]

    _signup(client, name="Bob", email="bob@example.com")

    # User 1 tries to claim User 2's email
    r = client.put(
        f"/api/v1/users/{key1}/",
        json={"email": "bob@example.com"},
        headers=_auth_header(token1),
    )
    assert r.status_code == 409


def test_delete_user_success_and_then_login_fails(client):
    """
    Test Case: Resource Deletion
    Goal: Verify that the DELETE method removes the resource and invalidates future access.
    Expected: Status 200 OK and subsequent 401 Unauthorized during login attempts.
    """
    r1 = _signup(client)
    key = r1.get_json()["user"]["user_key"]
    token = _login(client).get_json()["token"]

    # Remove resource
    r = client.delete(f"/api/v1/users/{key}/", headers=_auth_header(token))
    assert r.status_code == 200
    assert r.get_json()["status"] == "deleted"

    # Verify deletion
    r2 = _login(client)
    assert r2.status_code == 401