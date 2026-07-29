from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import RiskAlert, StaffDailyReport, User
from app.services.risk import evaluate_staff_report_risk, evaluate_user_risks
from tests.conftest import add_report, login_headers

TODAY = date.today()


def alert_types(db) -> set[str]:
    return {a.alert_type for a in db.query(RiskAlert).all()}


def test_stress_streak_alert(db, member):
    for i in range(3):
        add_report(db, member.id, TODAY - timedelta(days=i), stress=5)
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    assert "stress_high_streak" in alert_types(db)


def test_stress_streak_not_triggered_by_two_days(db, member):
    add_report(db, member.id, TODAY, stress=5)
    add_report(db, member.id, TODAY - timedelta(days=1), stress=5)
    add_report(db, member.id, TODAY - timedelta(days=2), stress=4)
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    assert "stress_high_streak" not in alert_types(db)


def test_mood_low_streak_alert(db, member):
    for i in range(3):
        add_report(db, member.id, TODAY - timedelta(days=i), mood=1)
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    assert "mood_low_streak" in alert_types(db)


def test_sleep_critical_alert(db, member):
    add_report(db, member.id, TODAY, sleep=2.5)
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    assert "sleep_critical" in alert_types(db)


def test_risky_expression_alert_requires_confirmation_note(db, member):
    add_report(db, member.id, TODAY, difficulty="最近つらくて、消えたいと思うことがある")
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    alerts = db.query(RiskAlert).filter(RiskAlert.alert_type == "risky_expression").all()
    assert len(alerts) == 1
    # 断定せず、スタッフ確認を必須とする文言
    assert "スタッフによる確認が必要" in alerts[0].reason
    # 本文そのものは保存しない（件数のみ）
    assert "消えたい" not in str(alerts[0].source_data_json)


def test_report_gap_alert(db, member):
    add_report(db, member.id, TODAY - timedelta(days=5))
    add_report(db, member.id, TODAY - timedelta(days=4))
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    assert "report_gap" in alert_types(db)


def test_no_duplicate_open_alerts(db, member):
    for i in range(3):
        add_report(db, member.id, TODAY - timedelta(days=i), stress=5)
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    alerts = db.query(RiskAlert).filter(RiskAlert.alert_type == "stress_high_streak").all()
    assert len(alerts) == 1


def test_acknowledge_records_who_and_when(client, db, staff, member):
    add_report(db, member.id, TODAY, sleep=2.0)
    evaluate_user_risks(db, member.id, TODAY)
    db.commit()
    alert = db.query(RiskAlert).first()

    headers = login_headers(client, "staff@test.com")
    res = client.post(f"/api/risk-alerts/{alert.id}/acknowledge", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "acknowledged"
    assert data["acknowledged_by"] == staff.id
    assert data["acknowledged_at"] is not None


def test_staff_sees_only_assigned_users_alerts(client, db, staff, member, other_member):
    add_report(db, member.id, TODAY, sleep=2.0)
    add_report(db, other_member.id, TODAY, sleep=2.0)
    evaluate_user_risks(db, member.id, TODAY)
    evaluate_user_risks(db, other_member.id, TODAY)
    db.commit()

    headers = login_headers(client, "staff@test.com")
    alerts = client.get("/api/risk-alerts", headers=headers).json()
    assert all(a["user_id"] == member.id for a in alerts)
    assert len(alerts) == 1


def test_user_cannot_access_risk_alerts(client, member):
    headers = login_headers(client, "member@test.com")
    res = client.get("/api/risk-alerts", headers=headers)
    assert res.status_code == 403


def test_staff_report_risky_expression_creates_alert(db: Session, member: User, staff: User) -> None:
    """支援記録の本文に自傷などの表現があればアラートを作成する"""
    report = StaffDailyReport(
        user_id=member.id, staff_id=staff.id, report_date=date.today(),
        support_content="作業中に興奮され、自傷行為を行って腕を噛もうとされていました。",
        urgency="normal",
    )
    db.add(report)
    db.flush()

    alert = evaluate_staff_report_risk(db, report)
    assert alert is not None
    assert alert.alert_type == "risky_expression"
    assert alert.severity == "high"
    assert "確認が必要" in alert.reason


def test_staff_report_without_risky_expression_creates_no_alert(
    db: Session, member: User, staff: User
) -> None:
    report = StaffDailyReport(
        user_id=member.id, staff_id=staff.id, report_date=date.today(),
        support_content="箱折作業に集中して取り組めていました。挨拶もしっかり出来ています。",
        urgency="normal",
    )
    db.add(report)
    db.flush()
    assert evaluate_staff_report_risk(db, report) is None


def test_staff_report_urgent_still_creates_alert(db: Session, member: User, staff: User) -> None:
    report = StaffDailyReport(
        user_id=member.id, staff_id=staff.id, report_date=date.today(),
        support_content="強い疲労を訴えている", urgency="urgent",
    )
    db.add(report)
    db.flush()
    alert = evaluate_staff_report_risk(db, report)
    assert alert is not None
    assert alert.alert_type == "staff_urgent"
