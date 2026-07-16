from datetime import date

from tests.conftest import add_report, login_headers


def test_user_cannot_view_other_users_reports(client, db, member, other_member):
    """利用者は他の利用者の日報を閲覧できない（404で存在も秘匿）"""
    add_report(db, other_member.id, date.today())
    headers = login_headers(client, "member@test.com")
    res = client.get(f"/api/users/{other_member.id}/daily-reports", headers=headers)
    assert res.status_code == 404


def test_user_cannot_view_other_users_profile(client, member, other_member):
    headers = login_headers(client, "member@test.com")
    res = client.get(f"/api/users/{other_member.id}", headers=headers)
    assert res.status_code == 404


def test_user_can_view_own_profile(client, member):
    headers = login_headers(client, "member@test.com")
    res = client.get(f"/api/users/{member.id}", headers=headers)
    assert res.status_code == 200


def test_staff_can_view_assigned_user(client, db, staff, member):
    add_report(db, member.id, date.today())
    headers = login_headers(client, "staff@test.com")
    res = client.get(f"/api/users/{member.id}/daily-reports", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_staff_cannot_view_unassigned_user(client, db, staff, other_member):
    add_report(db, other_member.id, date.today())
    headers = login_headers(client, "staff@test.com")
    res = client.get(f"/api/users/{other_member.id}/daily-reports", headers=headers)
    assert res.status_code == 404


def test_admin_can_view_all_users(client, db, admin, member, other_member):
    headers = login_headers(client, "admin@test.com")
    for target in (member, other_member):
        res = client.get(f"/api/users/{target.id}", headers=headers)
        assert res.status_code == 200


def test_staff_user_list_only_assigned(client, staff, member, other_member):
    headers = login_headers(client, "staff@test.com")
    res = client.get("/api/users", headers=headers)
    assert res.status_code == 200
    ids = [u["id"] for u in res.json()]
    assert member.id in ids
    assert other_member.id not in ids


def test_user_cannot_list_users(client, member):
    headers = login_headers(client, "member@test.com")
    res = client.get("/api/users", headers=headers)
    assert res.status_code == 403


def test_user_cannot_create_account(client, member):
    headers = login_headers(client, "member@test.com")
    res = client.post("/api/users", headers=headers, json={
        "email": "new@test.com", "password": "Password1!", "role": "user",
        "profile": {"display_name": "新規"},
    })
    assert res.status_code == 403


def test_staff_cannot_view_audit_logs(client, staff):
    headers = login_headers(client, "staff@test.com")
    res = client.get("/api/audit-logs", headers=headers)
    assert res.status_code == 403


def test_user_cannot_run_ai_analysis(client, db, member):
    add_report(db, member.id, date.today())
    headers = login_headers(client, "member@test.com")
    res = client.post(f"/api/users/{member.id}/ai-analyses", headers=headers,
                      json={"analysis_type": "daily_analysis", "period_days": 14})
    assert res.status_code == 403


def test_user_sees_only_filtered_analysis(client, db, staff, member):
    """利用者本人にはスタッフ向け項目を含まない結果のみ表示される"""
    add_report(db, member.id, date.today())
    staff_headers = login_headers(client, "staff@test.com")
    res = client.post(f"/api/users/{member.id}/ai-analyses", headers=staff_headers,
                      json={"analysis_type": "daily_analysis", "period_days": 14})
    assert res.status_code == 201
    assert "staff_recommendations" in res.json()["result_json"]

    member_headers = login_headers(client, "member@test.com")
    res = client.get(f"/api/users/{member.id}/ai-analyses", headers=member_headers)
    assert res.status_code == 200
    result = res.json()[0]["result_json"]
    assert "staff_recommendations" not in result
    assert "user_recommendations" in result


def test_user_cannot_see_draft_support_plan(client, db, staff, member):
    add_report(db, member.id, date.today())
    staff_headers = login_headers(client, "staff@test.com")
    res = client.post(f"/api/users/{member.id}/support-plans/generate", headers=staff_headers)
    assert res.status_code == 201

    member_headers = login_headers(client, "member@test.com")
    res = client.get(f"/api/users/{member.id}/support-plans", headers=member_headers)
    assert res.status_code == 200
    assert res.json() == []  # 下書きは本人に表示されない

    staff_view = client.get(f"/api/users/{member.id}/support-plans", headers=staff_headers)
    assert len(staff_view.json()) == 1
