from tests.conftest import login_headers


def test_login_success(client, admin):
    res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "Password1!"})
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"]
    assert data["refresh_token"]


def test_login_wrong_password(client, admin):
    res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "wrong"})
    assert res.status_code == 401
    assert "正しくありません" in res.json()["detail"]


def test_login_inactive_user(client, db, admin):
    admin.is_active = False
    db.commit()
    res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "Password1!"})
    assert res.status_code == 401


def test_me(client, staff):
    headers = login_headers(client, "staff@test.com")
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "staff@test.com"
    assert data["role"] == "staff"
    assert data["profile"]["display_name"] == "スタッフA"


def test_me_without_token(client, db):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_with_invalid_token(client, db):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert res.status_code == 401


def test_refresh(client, admin):
    login = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "Password1!"}).json()
    res = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert res.status_code == 200
    assert res.json()["access_token"]


def test_refresh_with_access_token_rejected(client, admin):
    login = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "Password1!"}).json()
    res = client.post("/api/auth/refresh", json={"refresh_token": login["access_token"]})
    assert res.status_code == 401


def test_login_records_audit_log(client, db, admin):
    login_headers(client, "admin@test.com")
    headers = login_headers(client, "admin@test.com")
    res = client.get("/api/audit-logs", headers=headers)
    assert res.status_code == 200
    assert any(log["action"] == "auth.login" for log in res.json())
