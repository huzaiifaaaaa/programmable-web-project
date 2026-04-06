"""LLM route tests for chat and conversation workflows."""

import jwt
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from probotapi.auth_utils import create_jwt
from probotapi.models import Chat, Conversation
from probotapi.routes import llm_routes

AUTH_SIGNUP_CANONICAL = "/api/v1/auth/signup"
AUTH_LOGIN_CANONICAL = "/api/v1/auth/login"


def _signup(client, name="Alice", email="alice@example.com", password="password123"):
    return client.post(
        AUTH_SIGNUP_CANONICAL,
        json={"name": name, "email": email, "password": password},
    )


def _login(client, email="alice@example.com", password="password123"):
    return client.post(
        AUTH_LOGIN_CANONICAL,
        json={"email": email, "password": password},
    )


def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def _create_user_and_token(client, name, email):
    signup = _signup(client, name=name, email=email)
    assert signup.status_code == 201, signup.get_json()
    user_key = signup.get_json()["user"]["user_key"]

    login = _login(client, email=email)
    assert login.status_code == 200, login.get_json()
    token = login.get_json()["token"]

    return user_key, token


def _token_for_claims(app, claims):
    with app.app_context():
        return create_jwt(claims)


def test_create_chat_requires_auth(client):
    res = client.post("/api/v1/chats")
    assert res.status_code == 401


def test_create_chat_success(client):
    _, token = _create_user_and_token(client, "Alice", "alice-chat@example.com")

    res = client.post("/api/v1/chats", headers=_auth_header(token))
    assert res.status_code == 201, res.get_json()
    payload = res.get_json()
    assert payload["status"] == "created"
    assert payload["chat"]["chat_key"]


def test_list_user_chats_forbidden_for_other_user(client):
    _, token_a = _create_user_and_token(client, "Alice", "alice-forbid@example.com")
    user_key_b, token_b = _create_user_and_token(client, "Bob", "bob-forbid@example.com")

    create_for_bob = client.post("/api/v1/chats", headers=_auth_header(token_b))
    assert create_for_bob.status_code == 201

    res = client.get(f"/api/v1/users/{user_key_b}/chats", headers=_auth_header(token_a))
    assert res.status_code == 403


def test_list_user_chats_success(client):
    user_key, token = _create_user_and_token(client, "Alice", "alice-list@example.com")

    first = client.post("/api/v1/chats", headers=_auth_header(token))
    second = client.post("/api/v1/chats", headers=_auth_header(token))
    assert first.status_code == 201
    assert second.status_code == 201

    res = client.get(f"/api/v1/users/{user_key}/chats", headers=_auth_header(token))
    assert res.status_code == 200, res.get_json()
    payload = res.get_json()
    assert payload["count"] == 2
    assert len(payload["chats"]) == 2


def test_send_conversation_success(monkeypatch, client, app):
    _, token = _create_user_and_token(client, "Alice", "alice-send@example.com")

    create_chat = client.post("/api/v1/chats", headers=_auth_header(token))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    def fake_gemini_response(prompt, model_key):
        assert prompt == "Hello bot"
        assert model_key
        return "Hello human", None

    monkeypatch.setattr(
        "probotapi.routes.llm_routes.get_gemini_response",
        fake_gemini_response,
    )

    res = client.post(
        f"/api/v1/chats/{chat_key}/conversations",
        json={"message": "Hello bot"},
        headers=_auth_header(token),
    )
    assert res.status_code == 201, res.get_json()
    body = res.get_json()
    assert body["status"] == "message_sent"
    assert body["conversation"]["request"] == "Hello bot"
    assert body["conversation"]["response"] == "Hello human"

    with app.app_context():
        assert Conversation.query.count() == 1


def test_send_conversation_model_not_found(client):
    _, token = _create_user_and_token(client, "Alice", "alice-model@example.com")

    create_chat = client.post("/api/v1/chats", headers=_auth_header(token))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    res = client.post(
        f"/api/v1/chats/{chat_key}/conversations",
        json={"message": "Hello", "model_key": "not-a-real-model"},
        headers=_auth_header(token),
    )
    assert res.status_code == 404
    assert "model" in res.get_json()["error"]


def test_send_conversation_llm_error_returns_502(monkeypatch, client):
    _, token = _create_user_and_token(client, "Alice", "alice-llmerr@example.com")

    create_chat = client.post("/api/v1/chats", headers=_auth_header(token))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    monkeypatch.setattr(
        "probotapi.routes.llm_routes.get_gemini_response",
        lambda _prompt, _model: (None, "boom"),
    )

    res = client.post(
        f"/api/v1/chats/{chat_key}/conversations",
        json={"message": "Hello"},
        headers=_auth_header(token),
    )
    assert res.status_code == 502
    assert "llm_error" in res.get_json()["error"]


def test_get_conversation_history_and_legacy_alias(monkeypatch, client):
    _, token = _create_user_and_token(client, "Alice", "alice-history@example.com")

    create_chat = client.post("/api/v1/chats", headers=_auth_header(token))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    monkeypatch.setattr(
        "probotapi.routes.llm_routes.get_gemini_response",
        lambda _prompt, _model: ("Stored response", None),
    )

    send = client.post(
        f"/api/v1/chats/{chat_key}/conversations",
        json={"message": "First"},
        headers=_auth_header(token),
    )
    assert send.status_code == 201

    canonical = client.get(
        f"/api/v1/chats/{chat_key}/conversations",
        headers=_auth_header(token),
    )
    assert canonical.status_code == 200, canonical.get_json()
    body = canonical.get_json()
    assert len(body["conversations"]) == 1
    assert len(body["messages"]) == 1

    legacy = client.get(
        f"/api/v1/chats/{chat_key}/messages",
        headers=_auth_header(token),
    )
    assert legacy.status_code == 200, legacy.get_json()


def test_delete_chat_forbidden_for_non_owner(client):
    _, token_a = _create_user_and_token(client, "Alice", "alice-del@example.com")
    _, token_b = _create_user_and_token(client, "Bob", "bob-del@example.com")

    create_chat = client.post("/api/v1/chats", headers=_auth_header(token_a))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    res = client.delete(f"/api/v1/chats/{chat_key}", headers=_auth_header(token_b))
    assert res.status_code == 403


def test_delete_chat_success(client, app):
    _, token = _create_user_and_token(client, "Alice", "alice-del-ok@example.com")

    create_chat = client.post("/api/v1/chats", headers=_auth_header(token))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    delete_res = client.delete(f"/api/v1/chats/{chat_key}", headers=_auth_header(token))
    assert delete_res.status_code == 200, delete_res.get_json()
    assert delete_res.get_json()["status"] == "deleted"

    with app.app_context():
        assert Chat.query.count() == 0


def test_llm_helper_functions(app):
    with app.test_request_context(json={"k": "v"}):
        assert llm_routes.get_json() == {"k": "v"}

    with app.test_request_context(json=["not", "dict"]):
        assert llm_routes.get_json() is None

    assert llm_routes._canonical_model_key(" gemini-3-flash-preview ") == "models/gemini-3-flash-preview"
    assert llm_routes._canonical_model_key("models/gemini-3-flash-preview") == "models/gemini-3-flash-preview"
    assert llm_routes._limit_words("a b c d", max_words=2) == "a b"


def test_get_gemini_response_missing_api_key(app):
    with app.app_context():
        app.config["GEMINI_API_KEY"] = ""
        response, err = llm_routes.get_gemini_response("hello", "gemini-3-flash-preview")
    assert response is None
    assert err == "Gemini API key not configured"


def test_create_chat_user_not_found(client, app):
    token = _token_for_claims(
        app,
        {"user_key": "missing-user", "user_id": 9999, "role_id": 1},
    )
    res = client.post("/api/v1/chats", headers=_auth_header(token))
    assert res.status_code == 404
    assert res.get_json()["error"] == "user not found"


def test_create_chat_handles_integrity_error(monkeypatch, client):
    _, token = _create_user_and_token(client, "Alice", "alice-chat-int@example.com")

    def raise_integrity_error():
        raise IntegrityError("stmt", "params", Exception("db"))

    monkeypatch.setattr("probotapi.routes.llm_routes.db.session.commit", raise_integrity_error)

    res = client.post("/api/v1/chats", headers=_auth_header(token))
    assert res.status_code == 500
    assert "failed to create chat" in res.get_json()["error"]


def test_list_user_chats_user_not_found(client, app):
    token = _token_for_claims(
        app,
        {"user_key": "unknown-user-key", "user_id": 1, "role_id": 1},
    )
    res = client.get("/api/v1/users/unknown-user-key/chats", headers=_auth_header(token))
    assert res.status_code == 404
    assert res.get_json()["error"] == "user not found"


def test_send_message_chat_not_found(client):
    _, token = _create_user_and_token(client, "Alice", "alice-nochat@example.com")
    res = client.post(
        "/api/v1/chats/not-a-chat/messages",
        json={"message": "hello"},
        headers=_auth_header(token),
    )
    assert res.status_code == 404
    assert res.get_json()["error"] == "chat not found"


def test_send_message_forbidden_for_non_owner(client):
    _, token_a = _create_user_and_token(client, "Alice", "alice-owner@example.com")
    _, token_b = _create_user_and_token(client, "Bob", "bob-owner@example.com")

    create_chat = client.post("/api/v1/chats", headers=_auth_header(token_a))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    res = client.post(
        f"/api/v1/chats/{chat_key}/messages",
        json={"message": "hello"},
        headers=_auth_header(token_b),
    )
    assert res.status_code == 403
    assert res.get_json()["error"] == "forbidden"


def test_send_message_handles_integrity_error(monkeypatch, client):
    _, token = _create_user_and_token(client, "Alice", "alice-msg-int@example.com")
    create_chat = client.post("/api/v1/chats", headers=_auth_header(token))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    monkeypatch.setattr(
        "probotapi.routes.llm_routes.get_gemini_response",
        lambda _prompt, _model: ("ok", None),
    )

    def raise_integrity_error():
        raise IntegrityError("stmt", "params", Exception("db"))

    monkeypatch.setattr("probotapi.routes.llm_routes.db.session.commit", raise_integrity_error)

    res = client.post(
        f"/api/v1/chats/{chat_key}/messages",
        json={"message": "hello"},
        headers=_auth_header(token),
    )
    assert res.status_code == 500
    assert "failed to save conversation" in res.get_json()["error"]


def test_get_message_history_not_found(client):
    _, token = _create_user_and_token(client, "Alice", "alice-hist404@example.com")
    res = client.get("/api/v1/chats/does-not-exist/messages", headers=_auth_header(token))
    assert res.status_code == 404
    assert res.get_json()["error"] == "chat not found"


def test_get_message_history_forbidden(client):
    _, token_a = _create_user_and_token(client, "Alice", "alice-hist403@example.com")
    _, token_b = _create_user_and_token(client, "Bob", "bob-hist403@example.com")

    create_chat = client.post("/api/v1/chats", headers=_auth_header(token_a))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    res = client.get(f"/api/v1/chats/{chat_key}/messages", headers=_auth_header(token_b))
    assert res.status_code == 403
    assert res.get_json()["error"] == "forbidden"


def test_delete_chat_not_found(client):
    _, token = _create_user_and_token(client, "Alice", "alice-del404@example.com")
    res = client.delete("/api/v1/chats/no-chat", headers=_auth_header(token))
    assert res.status_code == 404
    assert res.get_json()["error"] == "chat not found"


def test_delete_chat_handles_sqlalchemy_error(monkeypatch, client):
    _, token = _create_user_and_token(client, "Alice", "alice-del500@example.com")
    create_chat = client.post("/api/v1/chats", headers=_auth_header(token))
    chat_key = create_chat.get_json()["chat"]["chat_key"]

    def raise_sqlalchemy_error():
        raise SQLAlchemyError("db")

    monkeypatch.setattr("probotapi.routes.llm_routes.db.session.commit", raise_sqlalchemy_error)

    res = client.delete(f"/api/v1/chats/{chat_key}", headers=_auth_header(token))
    assert res.status_code == 500
    assert "failed to delete chat" in res.get_json()["error"]
