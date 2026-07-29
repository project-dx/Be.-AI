from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from app.services.wellbeing_cards import CARDS
from tests.conftest import login_headers

THREE = ["gratitude", "growth", "peace"]


def test_card_master_has_32_cards(client: TestClient, member: User) -> None:
    assert len(CARDS) == 32
    headers = login_headers(client, member.email)
    res = client.get("/api/wellbeing-cards", headers=headers)
    assert res.status_code == 200
    cards = res.json()
    assert len(cards) == 32
    assert {c["category"] for c in cards} == {"self", "people", "world"}
    assert all(c["label"] and c["description"] for c in cards)


def test_user_can_save_and_update_selection(client: TestClient, member: User) -> None:
    headers = login_headers(client, member.email)

    res = client.post(f"/api/users/{member.id}/wellbeing-selections",
                      json={"card_ids": THREE, "note": "今週がんばったこと"}, headers=headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["card_ids"] == THREE
    assert body["note"] == "今週がんばったこと"

    # 同じ日に選び直すと上書きされる（レコードは増えない）
    res = client.post(f"/api/users/{member.id}/wellbeing-selections",
                      json={"card_ids": ["love", "hope", "en"]}, headers=headers)
    assert res.status_code == 201
    assert res.json()["id"] == body["id"]

    res = client.get(f"/api/users/{member.id}/wellbeing-selections", headers=headers)
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["card_ids"] == ["love", "hope", "en"]


def test_selection_validation(client: TestClient, member: User) -> None:
    headers = login_headers(client, member.email)
    url = f"/api/users/{member.id}/wellbeing-selections"

    # 2枚はエラー
    assert client.post(url, json={"card_ids": THREE[:2]}, headers=headers).status_code == 422
    # 4枚はエラー
    assert client.post(url, json={"card_ids": THREE + ["love"]}, headers=headers).status_code == 422
    # 重複はエラー
    assert client.post(url, json={"card_ids": ["love", "love", "en"]}, headers=headers).status_code == 422
    # 存在しないIDはエラー
    assert client.post(url, json={"card_ids": ["love", "hope", "unknown_card"]}, headers=headers).status_code == 422


def test_other_user_cannot_access(client: TestClient, member: User, other_member: User) -> None:
    # 権限がない場合は404（存在の秘匿）が返る
    headers = login_headers(client, other_member.email)
    res = client.post(f"/api/users/{member.id}/wellbeing-selections",
                      json={"card_ids": THREE}, headers=headers)
    assert res.status_code == 404
    assert client.get(f"/api/users/{member.id}/wellbeing-selections", headers=headers).status_code == 404


def test_assigned_staff_can_view(client: TestClient, member: User, staff: User) -> None:
    user_headers = login_headers(client, member.email)
    client.post(f"/api/users/{member.id}/wellbeing-selections",
                json={"card_ids": THREE}, headers=user_headers)

    staff_headers = login_headers(client, staff.email)
    res = client.get(f"/api/users/{member.id}/wellbeing-selections", headers=staff_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_admin_dashboard_shows_who_selected_what(client: TestClient, member: User, admin: User) -> None:
    """管理者ダッシュボードで「誰が・いつ・どの3枚を選んだか」が確認できる"""
    client.post(f"/api/users/{member.id}/wellbeing-selections",
                json={"card_ids": THREE, "note": "今週の気持ち"},
                headers=login_headers(client, member.email))

    res = client.get("/api/dashboard/admin", headers=login_headers(client, admin.email))
    assert res.status_code == 200, res.text
    selections = res.json()["wellbeing_selections"]
    assert len(selections) == 1
    row = selections[0]
    assert row["user_name"] == "利用者1"
    assert row["selection_date"]
    assert row["updated_at"]
    assert [c["id"] for c in row["cards"]] == THREE
    assert [c["label"] for c in row["cards"]] == ["感謝", "成長", "平和"]
    assert row["note"] == "今週の気持ち"


def test_staff_dashboard_shows_only_assigned_users(
    client: TestClient, member: User, other_member: User, staff: User
) -> None:
    """スタッフのダッシュボードには担当利用者の選択のみ表示される"""
    client.post(f"/api/users/{member.id}/wellbeing-selections", json={"card_ids": THREE},
                headers=login_headers(client, member.email))
    client.post(f"/api/users/{other_member.id}/wellbeing-selections", json={"card_ids": THREE},
                headers=login_headers(client, other_member.email))

    res = client.get("/api/dashboard/staff", headers=login_headers(client, staff.email))
    assert res.status_code == 200
    selections = res.json()["wellbeing_selections"]
    assert len(selections) == 1
    assert selections[0]["user_id"] == member.id
