from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from tests.conftest import add_report, login_headers

TODAY = date.today()

VALID_REPORT = {
    "report_date": TODAY.isoformat(),
    "mood": 4,
    "sleep_hours": 7.5,
    "bedtime": "23:00",
    "wake_time": "06:30",
    "sleep_quality": 4,
    "breakfast_status": "eaten",
    "lunch_status": "partial",
    "dinner_status": "eaten",
    "exercise_minutes": 30,
    "work_study_minutes": 240,
    "stress_level": 2,
    "fatigue_level": 2,
    "social_level": 4,
    "success_experience": "新しい作業ができた",
    "is_draft": False,
}


def test_create_and_get_daily_report(client, member):
    headers = login_headers(client, "member@test.com")
    res = client.post(f"/api/users/{member.id}/daily-reports", headers=headers, json=VALID_REPORT)
    assert res.status_code == 201, res.text
    report_id = res.json()["id"]

    res = client.get(f"/api/users/{member.id}/daily-reports/{report_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["mood"] == 4


def test_create_report_calculates_score(client, member):
    headers = login_headers(client, "member@test.com")
    client.post(f"/api/users/{member.id}/daily-reports", headers=headers, json=VALID_REPORT)
    res = client.get(f"/api/users/{member.id}/scores", headers=headers)
    assert res.status_code == 200
    scores = res.json()
    assert len(scores) == 1
    assert scores[0]["sleep_score"] is not None


def test_duplicate_date_returns_409(client, member):
    headers = login_headers(client, "member@test.com")
    client.post(f"/api/users/{member.id}/daily-reports", headers=headers, json=VALID_REPORT)
    res = client.post(f"/api/users/{member.id}/daily-reports", headers=headers, json=VALID_REPORT)
    assert res.status_code == 409
    assert "既に存在" in res.json()["detail"]


def test_submit_requires_fields(client, member):
    """確定時は必須項目チェック（日本語エラー）"""
    headers = login_headers(client, "member@test.com")
    body = {"report_date": TODAY.isoformat(), "is_draft": False}
    res = client.post(f"/api/users/{member.id}/daily-reports", headers=headers, json=body)
    assert res.status_code == 422
    assert "入力してください" in res.json()["detail"]


def test_draft_allows_missing_fields(client, member):
    headers = login_headers(client, "member@test.com")
    body = {"report_date": TODAY.isoformat(), "mood": 3, "is_draft": True}
    res = client.post(f"/api/users/{member.id}/daily-reports", headers=headers, json=body)
    assert res.status_code == 201
    assert res.json()["is_draft"] is True


def test_draft_then_submit(client, member):
    headers = login_headers(client, "member@test.com")
    body = {"report_date": TODAY.isoformat(), "mood": 3, "is_draft": True}
    report_id = client.post(f"/api/users/{member.id}/daily-reports", headers=headers, json=body).json()["id"]

    update = {**VALID_REPORT, "is_draft": False}
    del update["report_date"]
    res = client.patch(f"/api/users/{member.id}/daily-reports/{report_id}", headers=headers, json=update)
    assert res.status_code == 200
    assert res.json()["is_draft"] is False


def test_invalid_mood_range(client, member):
    headers = login_headers(client, "member@test.com")
    res = client.post(f"/api/users/{member.id}/daily-reports", headers=headers,
                      json={**VALID_REPORT, "mood": 6})
    assert res.status_code == 422


def test_staff_cannot_create_user_report(client, db, staff, member):
    headers = login_headers(client, "staff@test.com")
    res = client.post(f"/api/users/{member.id}/daily-reports", headers=headers, json=VALID_REPORT)
    assert res.status_code == 403


def test_staff_does_not_see_drafts(client, db, staff, member):
    add_report(db, member.id, TODAY, is_draft=True)
    add_report(db, member.id, TODAY - timedelta(days=1), is_draft=False)
    headers = login_headers(client, "staff@test.com")
    res = client.get(f"/api/users/{member.id}/daily-reports", headers=headers)
    assert len(res.json()) == 1
    assert res.json()[0]["is_draft"] is False


# --- スタッフ日報 ---

STAFF_REPORT = {
    "report_date": TODAY.isoformat(),
    "support_minutes": 45,
    "support_content": "作業訓練の支援",
    "user_condition": "落ち着いている",
    "urgency": "normal",
}


def test_staff_report_crud(client, db, staff, member):
    headers = login_headers(client, "staff@test.com")
    res = client.post(f"/api/users/{member.id}/staff-reports", headers=headers, json=STAFF_REPORT)
    assert res.status_code == 201, res.text
    report_id = res.json()["id"]
    assert res.json()["staff_name"] == "スタッフA"

    res = client.patch(f"/api/users/{member.id}/staff-reports/{report_id}",
                       headers=headers, json={"issues": "疲労が見られる"})
    assert res.status_code == 200
    assert res.json()["issues"] == "疲労が見られる"

    res = client.get(f"/api/users/{member.id}/staff-reports", headers=headers)
    assert len(res.json()) == 1


def test_urgent_staff_report_creates_alert(client, db, staff, member):
    headers = login_headers(client, "staff@test.com")
    res = client.post(f"/api/users/{member.id}/staff-reports", headers=headers,
                      json={**STAFF_REPORT, "urgency": "urgent"})
    assert res.status_code == 201

    alerts = client.get("/api/risk-alerts", headers=headers).json()
    assert any(a["alert_type"] == "staff_urgent" and a["user_id"] == member.id for a in alerts)


def test_other_staff_cannot_edit_report(client, db, staff, other_staff, member, admin):
    headers = login_headers(client, "staff@test.com")
    report_id = client.post(f"/api/users/{member.id}/staff-reports", headers=headers,
                            json=STAFF_REPORT).json()["id"]
    # 管理者は担当外でも編集可能
    admin_headers = login_headers(client, "admin@test.com")
    res = client.patch(f"/api/users/{member.id}/staff-reports/{report_id}",
                       headers=admin_headers, json={"issues": "管理者による追記"})
    assert res.status_code == 200


def test_user_cannot_view_staff_reports(client, db, staff, member):
    staff_headers = login_headers(client, "staff@test.com")
    client.post(f"/api/users/{member.id}/staff-reports", headers=staff_headers, json=STAFF_REPORT)
    member_headers = login_headers(client, "member@test.com")
    res = client.get(f"/api/users/{member.id}/staff-reports", headers=member_headers)
    assert res.status_code == 403


# ============ 全利用者横断のスタッフ日報一覧 ============
def _make_staff_report(client: TestClient, staff_email: str, user_id: int, urgency: str = "normal") -> None:
    res = client.post(
        f"/api/users/{user_id}/staff-reports",
        json={"report_date": date.today().isoformat(), "support_content": "面談を実施", "urgency": urgency},
        headers=login_headers(client, staff_email),
    )
    assert res.status_code == 201, res.text


def test_admin_sees_all_staff_reports(
    client: TestClient, member: User, other_member: User, staff: User, other_staff: User, admin: User
) -> None:
    _make_staff_report(client, staff.email, member.id)
    _make_staff_report(client, other_staff.email, other_member.id, urgency="urgent")

    res = client.get("/api/staff-reports", headers=login_headers(client, admin.email))
    assert res.status_code == 200, res.text
    rows = res.json()
    assert len(rows) == 2
    # 一覧では利用者名とスタッフ名が付与される
    assert {r["user_name"] for r in rows} == {"利用者1", "利用者2"}
    assert all(r["staff_name"] for r in rows)


def test_staff_sees_only_assigned_users_reports(
    client: TestClient, member: User, other_member: User, staff: User, other_staff: User
) -> None:
    _make_staff_report(client, staff.email, member.id)
    _make_staff_report(client, other_staff.email, other_member.id)

    res = client.get("/api/staff-reports", headers=login_headers(client, staff.email))
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["user_id"] == member.id


def test_staff_reports_filter_by_urgency_and_user(
    client: TestClient, member: User, other_member: User, staff: User, other_staff: User, admin: User
) -> None:
    _make_staff_report(client, staff.email, member.id, urgency="urgent")
    _make_staff_report(client, other_staff.email, other_member.id, urgency="normal")
    headers = login_headers(client, admin.email)

    res = client.get("/api/staff-reports?urgency=urgent", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["urgency"] == "urgent"

    res = client.get(f"/api/staff-reports?user_id={other_member.id}", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["user_id"] == other_member.id


def test_user_cannot_list_all_staff_reports(client: TestClient, member: User) -> None:
    res = client.get("/api/staff-reports", headers=login_headers(client, member.email))
    assert res.status_code == 403


def test_staff_report_visible_even_if_target_became_staff(
    client: TestClient, db: Session, member: User, staff: User, admin: User
) -> None:
    """記録の対象者が後からスタッフ役割に変わっても、記録は一覧に残り続ける"""
    _make_staff_report(client, staff.email, member.id)

    member.role = "staff"
    db.commit()

    res = client.get("/api/staff-reports", headers=login_headers(client, admin.email))
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["user_id"] == member.id
    assert rows[0]["user_name"] == "利用者1"


def test_staff_reports_never_exposed_to_user_role(
    client: TestClient, member: User, staff: User
) -> None:
    """利用者ロールには支援記録の一覧を見せない"""
    _make_staff_report(client, staff.email, member.id)
    headers = login_headers(client, member.email)

    assert client.get("/api/staff-reports", headers=headers).status_code == 403
    assert client.get(f"/api/staff-reports?user_id={member.id}", headers=headers).status_code == 403
