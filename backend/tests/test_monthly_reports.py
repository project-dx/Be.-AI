from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import StaffDailyReport, User, UserDailyReport
from app.services.ai.monthly import build_monthly_data, generate_monthly_report_mock, month_period
from tests.conftest import login_headers

YM = "2026-07"


def _add_month_data(db: Session, member: User, staff: User) -> None:
    for day in [1, 2, 3, 6, 7]:
        db.add(
            UserDailyReport(
                user_id=member.id,
                report_date=date(2026, 7, day),
                mood=4 if day < 6 else 2,
                sleep_quality=3,
                fatigue_level=2 if day < 6 else 4,
                breakfast_status="eaten",
                achievement="MOSエクセルの勉強",
                free_text="体調: 普通 ／ 達成感: 3.0/5",
                is_draft=False,
            )
        )
    db.add(
        StaffDailyReport(
            user_id=member.id,
            staff_id=staff.id,
            report_date=date(2026, 7, 8),
            support_content="「体調不良のためお休みします」と連絡あり。欠席。",
            urgency="caution",
        )
    )
    db.commit()


def test_month_period() -> None:
    assert month_period("2026-07") == (date(2026, 7, 1), date(2026, 7, 31))
    assert month_period("2026-02") == (date(2026, 2, 1), date(2026, 2, 28))


def test_build_monthly_data(db: Session, member: User, staff: User) -> None:
    _add_month_data(db, member, staff)
    facts, ai_context = build_monthly_data(db, date(2026, 7, 1), date(2026, 7, 31))

    assert facts["total_users"] == 1
    assert facts["total_reports"] == 5
    assert facts["user_names"][str(member.id)] == "利用者1"
    assert facts["attendance"][0]["absence_dates"] == ["2026-07-08"]
    assert facts["condition_distribution"].get("普通") == 5
    assert facts["skill_distribution"].get("事務・Office系") == 5

    # AIコンテキストに氏名を含めない
    assert "user_names" not in ai_context
    assert ai_context["users"][0]["user_id"] == member.id


def test_mock_monthly_report(db: Session, member: User, staff: User) -> None:
    _add_month_data(db, member, staff)
    _, ai_context = build_monthly_data(db, date(2026, 7, 1), date(2026, 7, 31))
    result = generate_monthly_report_mock(ai_context)

    assert result.analysis_points
    assert result.skill_trends
    assert len(result.user_analyses) == 1
    assert result.user_analyses[0].user_id == member.id
    assert len(result.action_plan) == 3


def test_generate_and_get_report_api(client: TestClient, db: Session, member: User, staff: User) -> None:
    _add_month_data(db, member, staff)
    headers = login_headers(client, staff.email)

    res = client.post("/api/monthly-reports", json={"year_month": YM}, headers=headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["year_month"] == YM
    assert body["status"] == "success"
    assert body["result_json"]["user_analyses"][0]["display_name"] == "利用者1"
    assert body["facts_json"]["total_reports"] == 5

    res = client.get(f"/api/monthly-reports/latest?year_month={YM}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == body["id"]

    res = client.get("/api/monthly-reports", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_generate_requires_staff(client: TestClient, db: Session, member: User, staff: User) -> None:
    _add_month_data(db, member, staff)
    headers = login_headers(client, member.email)
    res = client.post("/api/monthly-reports", json={"year_month": YM}, headers=headers)
    assert res.status_code == 403


def test_generate_empty_month_rejected(client: TestClient, db: Session, staff: User) -> None:
    headers = login_headers(client, staff.email)
    res = client.post("/api/monthly-reports", json={"year_month": "2026-01"}, headers=headers)
    assert res.status_code == 422
