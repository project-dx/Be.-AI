from datetime import date

from tests.conftest import add_week_reports, login_headers

TODAY = date.today()


def _generate_plan(client, db, member_id: int) -> tuple[dict, dict]:
    add_week_reports(db, member_id, TODAY, days=7)
    headers = login_headers(client, "staff@test.com")
    res = client.post(f"/api/users/{member_id}/support-plans/generate", headers=headers)
    assert res.status_code == 201, res.text
    return res.json(), headers


def test_generate_draft_plan(client, db, staff, member):
    plan, _headers = _generate_plan(client, db, member.id)
    assert plan["status"] == "draft"
    assert plan["title"]
    assert plan["current_issues"]
    assert isinstance(plan["short_term_goals_json"], list)


def test_edit_creates_version(client, db, staff, member):
    plan, headers = _generate_plan(client, db, member.id)
    res = client.patch(f"/api/support-plans/{plan['id']}", headers=headers,
                       json={"long_term_goal": "修正後の長期目標", "change_reason": "面談内容を反映"})
    assert res.status_code == 200
    assert res.json()["long_term_goal"] == "修正後の長期目標"

    versions = client.get(f"/api/support-plans/{plan['id']}/versions", headers=headers).json()
    assert len(versions) == 2  # 生成時 + 編集
    assert versions[0]["change_reason"] == "面談内容を反映"


def test_approve_plan(client, db, staff, member):
    plan, headers = _generate_plan(client, db, member.id)
    res = client.post(f"/api/support-plans/{plan['id']}/approve", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == staff.id
    assert data["approved_at"] is not None


def test_cannot_approve_twice(client, db, staff, member):
    plan, headers = _generate_plan(client, db, member.id)
    client.post(f"/api/support-plans/{plan['id']}/approve", headers=headers)
    res = client.post(f"/api/support-plans/{plan['id']}/approve", headers=headers)
    assert res.status_code == 400


def test_approve_via_patch_rejected(client, db, staff, member):
    """PATCHでの直接承認は禁止（承認APIを通す）"""
    plan, headers = _generate_plan(client, db, member.id)
    res = client.patch(f"/api/support-plans/{plan['id']}", headers=headers, json={"status": "approved"})
    assert res.status_code == 400


def test_user_cannot_generate_plan(client, db, staff, member):
    add_week_reports(db, member.id, TODAY, days=7)
    headers = login_headers(client, "member@test.com")
    res = client.post(f"/api/users/{member.id}/support-plans/generate", headers=headers)
    assert res.status_code == 403


def test_support_action_records_effect(client, db, staff, member):
    plan, headers = _generate_plan(client, db, member.id)
    res = client.post(f"/api/users/{member.id}/support-actions", headers=headers, json={
        "support_plan_id": plan["id"],
        "action_date": TODAY.isoformat(),
        "action_content": "勇気づけ面談を実施",
        "user_response": "落ち着いて話せた",
        "effect_score": 4,
        "next_action": "1週間後に再度面談",
    })
    assert res.status_code == 201, res.text
    assert res.json()["effect_score"] == 4

    actions = client.get(f"/api/users/{member.id}/support-actions", headers=headers).json()
    assert len(actions) == 1
