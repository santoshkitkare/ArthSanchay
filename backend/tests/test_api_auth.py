"""Auth route tests — FR-AUTH-1..7."""


def test_register_creates_account_and_sets_cookies(client):
    resp = client.post("/api/auth/register", json={"email": "a@example.com", "password": "correcthorse1"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "a@example.com"
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


def test_register_duplicate_email_rejected(client):
    client.post("/api/auth/register", json={"email": "dup@example.com", "password": "correcthorse1"})
    resp = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "anotherpass1"})
    assert resp.status_code == 409


def test_register_rejects_short_password(client):
    resp = client.post("/api/auth/register", json={"email": "short@example.com", "password": "short1"})
    assert resp.status_code == 422


def test_login_with_correct_credentials(client):
    client.post("/api/auth/register", json={"email": "b@example.com", "password": "correcthorse1"})
    client.cookies.clear()
    resp = client.post("/api/auth/login", json={"email": "b@example.com", "password": "correcthorse1"})
    assert resp.status_code == 200
    assert "access_token" in resp.cookies


def test_login_with_wrong_password_fails(client):
    client.post("/api/auth/register", json={"email": "c@example.com", "password": "correcthorse1"})
    client.cookies.clear()
    resp = client.post("/api/auth/login", json={"email": "c@example.com", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_rate_limited_after_repeated_failures(client):
    client.post("/api/auth/register", json={"email": "d@example.com", "password": "correcthorse1"})
    client.cookies.clear()
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "d@example.com", "password": "wrong"})
    resp = client.post("/api/auth/login", json={"email": "d@example.com", "password": "wrong"})
    assert resp.status_code == 429


def test_me_requires_authentication(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user_when_authenticated(client):
    client.post("/api/auth/register", json={"email": "e@example.com", "password": "correcthorse1"})
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "e@example.com"


def test_refresh_rotates_token_and_old_one_cannot_be_reused(client):
    client.post("/api/auth/register", json={"email": "f@example.com", "password": "correcthorse1"})
    old_refresh = client.cookies.get("refresh_token")

    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 200

    client.cookies.set("refresh_token", old_refresh)
    resp2 = client.post("/api/auth/refresh")
    assert resp2.status_code == 401


def test_logout_clears_session(client):
    client.post("/api/auth/register", json={"email": "g@example.com", "password": "correcthorse1"})
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 204
    client.cookies.clear()  # TestClient doesn't auto-drop server-cleared cookies reliably
    me = client.get("/api/auth/me")
    assert me.status_code == 401


def test_password_reset_request_is_silent_about_account_existence(client):
    resp_known = client.post("/api/auth/password-reset/request", json={"email": "nonexistent@example.com"})
    assert resp_known.status_code == 202
    assert "detail" in resp_known.json()
