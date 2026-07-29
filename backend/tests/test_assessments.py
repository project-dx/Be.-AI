from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, UserDailyReport
from app.services.ai.context import build_analysis_context
from tests.conftest import login_headers

ASSESSMENT_BODY = {
    "life_history": "特別支援学校を卒業後、就労移行支援を利用開始",
    "disability_characteristics": "見通しが立たない場面で不安が高まりやすい",
    "thinking_style": "手順が明確な作業で力を発揮しやすい（ハーマンモデル: B象限が優位）",
    "herrmann_a": 45,
    "herrmann_b": 80,
    "herrmann_c": 60,
    "herrmann_d": 30,
    "personal_values": "人の役に立つこと、確実にやり遂げること",
    "strengths": "正確な作業、継続力",
    "support_needs": "予定変更は事前に伝える",
}

PYRAMID_BODY = {
    "wellbeing": "静かな環境で作業に集中できているとき",
    "passion": "パソコンで資料を作ること",
    "vision": "事務の仕事に就いて働き続けたい",
    "mission": "職場のみんなが使いやすい資料をつくる",
}


# ============ 初期アセスメント ============
def test_staff_can_upsert_and_get_assessment(client: TestClient, member: User, staff: User) -> None:
    headers = login_headers(client, staff.email)
    url = f"/api/users/{member.id}/assessment"

    assert client.get(url, headers=headers).status_code == 404

    res = client.put(url, json=ASSESSMENT_BODY, headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["thinking_style"] == ASSESSMENT_BODY["thinking_style"]
    assert body["assessment_date"] == date.today().isoformat()

    # 再度PUTしても1件のまま更新される
    res = client.put(url, json={"strengths": "更新後の強み"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == body["id"]
    assert res.json()["strengths"] == "更新後の強み"
    assert res.json()["life_history"] == ASSESSMENT_BODY["life_history"]  # 他項目は保持

    res = client.get(url, headers=headers)
    assert res.status_code == 200
    assert res.json()["strengths"] == "更新後の強み"


def test_user_can_read_but_not_write_assessment(client: TestClient, member: User, staff: User) -> None:
    client.put(f"/api/users/{member.id}/assessment", json=ASSESSMENT_BODY,
               headers=login_headers(client, staff.email))

    headers = login_headers(client, member.email)
    assert client.get(f"/api/users/{member.id}/assessment", headers=headers).status_code == 200
    assert client.put(f"/api/users/{member.id}/assessment", json=ASSESSMENT_BODY, headers=headers).status_code == 403


# ============ カラフルピラミッド ============
def test_user_can_edit_own_pyramid(client: TestClient, member: User) -> None:
    headers = login_headers(client, member.email)
    url = f"/api/users/{member.id}/pyramid"

    assert client.get(url, headers=headers).status_code == 404

    res = client.put(url, json=PYRAMID_BODY, headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["mission"] == PYRAMID_BODY["mission"]

    res = client.put(url, json={"vision": "書き直したビジョン"}, headers=headers)
    assert res.json()["vision"] == "書き直したビジョン"
    assert res.json()["passion"] == PYRAMID_BODY["passion"]


def test_other_user_cannot_touch_pyramid(client: TestClient, member: User, other_member: User) -> None:
    headers = login_headers(client, other_member.email)
    assert client.put(f"/api/users/{member.id}/pyramid", json=PYRAMID_BODY, headers=headers).status_code == 404


# ============ バイタルデータ ============
def test_daily_report_accepts_vitals(client: TestClient, member: User) -> None:
    headers = login_headers(client, member.email)
    res = client.post(
        f"/api/users/{member.id}/daily-reports",
        json={
            "report_date": date.today().isoformat(),
            "mood": 4, "sleep_hours": 7.0, "sleep_quality": 4,
            "stress_level": 2, "fatigue_level": 2, "social_level": 3,
            "body_temperature": 36.5, "systolic_bp": 118, "diastolic_bp": 74, "pulse": 68,
            "is_draft": False,
        },
        headers=headers,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["body_temperature"] == 36.5
    assert body["systolic_bp"] == 118
    assert body["pulse"] == 68


def test_vitals_out_of_range_rejected(client: TestClient, member: User) -> None:
    headers = login_headers(client, member.email)
    res = client.post(
        f"/api/users/{member.id}/daily-reports",
        json={"report_date": date.today().isoformat(), "body_temperature": 50.0, "is_draft": True},
        headers=headers,
    )
    assert res.status_code == 422


# ============ モニタリング評価 ============
def test_generate_monitoring_evaluation(client: TestClient, db: Session, member: User, staff: User) -> None:
    today = date.today()
    for i in range(10):
        db.add(
            UserDailyReport(
                user_id=member.id,
                report_date=today - timedelta(days=i),
                mood=4, sleep_hours=7.0, sleep_quality=4,
                stress_level=2, fatigue_level=2, social_level=3,
                success_experience="作業を最後までやりきれた" if i % 2 == 0 else None,
                is_draft=False,
            )
        )
    db.commit()

    headers = login_headers(client, staff.email)
    url = f"/api/users/{member.id}/monitoring-evaluations"

    res = client.post(url, json={"period_months": 6}, headers=headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["ai_generated"] is True
    assert body["achievements"]
    assert body["challenges"]
    assert body["score_summary_json"]["report_count"] == 10

    # スタッフが編集して確定できる
    res = client.patch(f"{url}/{body['id']}", json={"staff_comment": "本人と面談のうえ確認済み"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["staff_comment"] == "本人と面談のうえ確認済み"

    res = client.get(url, headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_monitoring_requires_reports(client: TestClient, member: User, staff: User) -> None:
    headers = login_headers(client, staff.email)
    res = client.post(f"/api/users/{member.id}/monitoring-evaluations", json={"period_months": 6}, headers=headers)
    assert res.status_code == 422


def test_user_cannot_generate_monitoring(client: TestClient, member: User) -> None:
    headers = login_headers(client, member.email)
    res = client.post(f"/api/users/{member.id}/monitoring-evaluations", json={"period_months": 6}, headers=headers)
    assert res.status_code == 403


# ============ AI分析入力への統合 ============
def test_analysis_context_includes_assessment_and_vitals(
    client: TestClient, db: Session, member: User, staff: User
) -> None:
    client.put(f"/api/users/{member.id}/assessment", json=ASSESSMENT_BODY,
               headers=login_headers(client, staff.email))
    client.put(f"/api/users/{member.id}/pyramid", json=PYRAMID_BODY,
               headers=login_headers(client, member.email))
    today = date.today()
    db.add(
        UserDailyReport(
            user_id=member.id, report_date=today, mood=4, sleep_hours=7.0,
            body_temperature=36.4, systolic_bp=120, diastolic_bp=76, pulse=70, is_draft=False,
        )
    )
    db.commit()

    context = build_analysis_context(db, member.id, today - timedelta(days=13), today)
    assert context["assessment"]["thinking_style"] == ASSESSMENT_BODY["thinking_style"]
    assert context["assessment"]["herrmann_model"]["b_practical"] == 80
    assert context["pyramid"]["mission"] == PYRAMID_BODY["mission"]
    assert context["daily_reports"][0]["vitals"]["body_temperature"] == 36.4
