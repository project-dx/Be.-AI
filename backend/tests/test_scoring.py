from datetime import date, timedelta

from app.services.scoring import (
    DEFAULT_WEIGHTS,
    calc_stress_status,
    calculate_scores_for_date,
    sleep_duration_ratio,
    stability_ratio,
    time_to_minutes,
)
from tests.conftest import add_report, add_week_reports

TODAY = date.today()


# --- 単体: 睡眠時間の境界値 ---

def test_sleep_duration_zero_hours():
    assert sleep_duration_ratio(0) == 0.0


def test_sleep_duration_optimal_range():
    assert sleep_duration_ratio(7) == 1.0
    assert sleep_duration_ratio(8) == 1.0
    assert sleep_duration_ratio(9) == 1.0


def test_sleep_duration_boundaries():
    assert sleep_duration_ratio(6) == 0.75
    assert sleep_duration_ratio(5) == 0.5
    assert sleep_duration_ratio(4) == 0.25
    assert sleep_duration_ratio(3.9) == 0.0


def test_sleep_duration_extremely_long():
    assert sleep_duration_ratio(24) == 0.0
    assert sleep_duration_ratio(11) == 0.5
    assert sleep_duration_ratio(12) == 0.0


def test_sleep_duration_missing():
    assert sleep_duration_ratio(None) is None


# --- 単体: 時刻・安定性 ---

def test_time_to_minutes_midnight_crossing():
    # 就寝時刻は18:00起点: 23:00 -> 300分, 01:00 -> 420分（深夜跨ぎで連続）
    assert time_to_minutes("23:00", anchor_minutes=18 * 60) == 300
    assert time_to_minutes("01:00", anchor_minutes=18 * 60) == 420


def test_time_to_minutes_invalid():
    assert time_to_minutes(None) is None
    assert time_to_minutes("abc") is None


def test_stability_insufficient_data():
    ratio, insufficient = stability_ratio([300])
    assert insufficient is True
    assert ratio == 0.65


def test_stability_stable():
    ratio, _ = stability_ratio([300, 310, 305, 300])
    assert ratio == 1.0


def test_stability_unstable():
    ratio, _ = stability_ratio([100, 300, 500])
    assert ratio == 0.0


# --- 結合: DBを使ったスコア計算 ---

def test_score_with_single_report(db, member):
    """日報が1件だけでもスコアが算出される（安定性は中立値）"""
    add_report(db, member.id, TODAY, sleep=8.0, quality=5, mood=5, stress=1, fatigue=1, social=5)
    result = calculate_scores_for_date(db, member.id, TODAY)
    db.commit()
    assert result is not None
    assert result.mental_score == 100
    assert result.breakdown_json["sleep"]["insufficient_data"] is True
    # 睡眠: 40(時間) + 25(質) + 15*0.65 + 20*0.65 = 87.75 -> 88
    assert result.sleep_score == 88


def test_score_with_seven_reports(db, member):
    add_week_reports(db, member.id, TODAY, days=7, sleep=7.5, quality=4)
    result = calculate_scores_for_date(db, member.id, TODAY)
    db.commit()
    assert result is not None
    # 同一時刻の就寝・起床 -> 安定係数1.0
    assert "insufficient_data" not in result.breakdown_json["sleep"]
    # 睡眠: 40 + 18.75 + 15 + 20 = 93.75 -> 94
    assert result.sleep_score == 94
    assert result.breakdown_json["report_days_in_week"] == 7


def test_score_no_report_returns_none(db, member):
    assert calculate_scores_for_date(db, member.id, TODAY) is None


def test_score_with_missing_fields(db, member):
    """未入力項目がある場合は0点扱い+missing_fields記録（クラッシュしない）"""
    from app.models import UserDailyReport

    add_report(db, member.id, TODAY, sleep=7.0)
    r = db.query(UserDailyReport).filter(UserDailyReport.report_date == TODAY).first()
    r.mood = None
    r.stress_level = None
    db.commit()
    result = calculate_scores_for_date(db, member.id, TODAY)
    db.commit()
    assert result is not None
    assert "mood" in result.breakdown_json["mental"]["missing_fields"]
    assert "stress" in result.breakdown_json["mental"]["missing_fields"]


def test_draft_reports_are_ignored(db, member):
    add_report(db, member.id, TODAY, is_draft=True)
    assert calculate_scores_for_date(db, member.id, TODAY) is None


def test_stress_status_levels(db, member):
    for i, stress in enumerate([5, 5, 5]):
        add_report(db, member.id, TODAY - timedelta(days=i), stress=stress)
    result = calculate_scores_for_date(db, member.id, TODAY)
    db.commit()
    assert result.stress_status == "high"


def test_stress_status_boundaries():
    class R:
        def __init__(self, s):
            self.stress_level = s

    assert calc_stress_status([R(2), R(2)]) == "low"
    assert calc_stress_status([R(3), R(3)]) == "normal"
    assert calc_stress_status([R(4), R(4)]) == "elevated"
    assert calc_stress_status([R(5), R(4)]) == "high"
    assert calc_stress_status([]) is None


def test_weights_sum_to_100():
    for group, weights in DEFAULT_WEIGHTS.items():
        assert sum(weights.values()) == 100, f"{group} の配点合計が100ではありません"


def test_custom_weights_applied(db, member):
    """system_settings の配点変更が反映される"""
    from app.models import SystemSetting

    db.add(SystemSetting(setting_key="scoring_weights",
                         setting_value_json={"mental": {"mood": 100, "stress": 0, "fatigue": 0, "social": 0}}))
    db.commit()
    add_report(db, member.id, TODAY, mood=5, stress=5, fatigue=5, social=1)
    result = calculate_scores_for_date(db, member.id, TODAY)
    db.commit()
    assert result.mental_score == 100  # moodのみ100点配点
