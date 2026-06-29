def test_register_creates_user_and_returns_token(client):
    resp = client.post("/auth/register", json={"username": "alice", "password": "pw"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"] == "coordinator"
    assert "token" in body and body["token"]
    assert "user_id" in body


def test_register_rejects_duplicate_username(client):
    client.post("/auth/register", json={"username": "alice", "password": "pw"})
    resp = client.post("/auth/register", json={"username": "alice", "password": "pw"})
    assert resp.status_code == 409


def test_login_succeeds_with_correct_password(client):
    client.post("/auth/register", json={"username": "bob", "password": "secret"})
    resp = client.post("/auth/login", json={"username": "bob", "password": "secret"})
    assert resp.status_code == 200
    assert resp.json()["token"]


def test_login_rejects_wrong_password(client):
    client.post("/auth/register", json={"username": "bob", "password": "secret"})
    resp = client.post("/auth/login", json={"username": "bob", "password": "nope"})
    assert resp.status_code == 401


def test_login_rejects_unknown_user(client):
    resp = client.post("/auth/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401


def test_protected_endpoint_requires_auth(client):
    resp = client.get("/buildings")
    # FastAPI HTTPBearer returns 403 when no Authorization header is present.
    assert resp.status_code in (401, 403)


def test_protected_endpoint_rejects_bad_token(client):
    resp = client.get("/buildings", headers={"Authorization": "Bearer junk"})
    assert resp.status_code == 401
