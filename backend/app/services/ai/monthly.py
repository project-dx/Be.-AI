"""月次利用者分析レポートの構築。

- 事実データ（出席・体調分布・気分分布）はコードで集計する（AI任せにしない）
- 分析文（メンタル/体調/スキル/傾向と対策・アクションプラン）はAIが生成する
- AIへは氏名などの個人情報を渡さず、user_idのみで紐付ける
"""

import calendar
import re
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models import Profile, StaffDailyReport, User, UserDailyReport
from app.schemas.ai import ActionPlanStep, MonthlyReportResult, MonthlyUserAnalysis

# 気分1〜5の表示ラベル
MOOD_LABELS = {1: "つらい", 2: "不調ぎみ", 3: "普通", 4: "落ち着いている", 5: "やる気あり"}

# 疲労度から体調ラベルへのフォールバック
FATIGUE_TO_CONDITION = {1: "良好", 2: "普通", 3: "普通", 4: "だるい・眠い", 5: "不調"}

CONDITION_PATTERN = re.compile(r"体調[:：]\s*([^／\s]+)")

# 活動内容からスキル分野を推定する簡易辞書
SKILL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("事務・Office系", ["Excel", "エクセル", "Word", "ワード", "PowerPoint", "パワーポイント", "MOS", "関数", "表計算", "データ入力", "資料", "スライド", "文書"]),
    ("Web・プログラミング", ["HTML", "CSS", "JavaScript", "Python", "プログラ", "コーディング", "Web", "アプリ", "API", "Flask", "GitHub", "SQL"]),
    ("デザイン・制作", ["デザイン", "Illustrator", "Photoshop", "Figma", "Canva", "チラシ", "バナー", "ポートフォリオ", "動画編集", "Blender", "名刺"]),
    ("ビジネススキル", ["ビジネスマナー", "メール", "敬語", "面接", "履歴書", "職務経歴書", "就活", "タイピング", "一般常識"]),
]


def month_period(year_month: str) -> tuple[date, date]:
    year, month = int(year_month[:4]), int(year_month[5:7])
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _condition_label(report: UserDailyReport) -> str:
    m = CONDITION_PATTERN.search(report.free_text or "")
    if m:
        return m.group(1)
    if report.fatigue_level is not None:
        return FATIGUE_TO_CONDITION.get(report.fatigue_level, "普通")
    return "未記録"


def _skill_categories(texts: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for text in texts:
        for category, keywords in SKILL_KEYWORDS:
            if any(k.lower() in text.lower() for k in keywords):
                counts[category] = counts.get(category, 0) + 1
                break
    return counts


def build_monthly_data(db: Session, period_start: date, period_end: date) -> tuple[dict[str, Any], dict[str, Any]]:
    """(facts, ai_context) を返す。factsは保存・表示用、ai_contextはAI入力用（匿名）。"""
    users = (
        db.query(User)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == "user", User.is_active.is_(True))
        .all()
    )

    user_names: dict[str, str] = {}
    attendance: list[dict[str, Any]] = []
    condition_dist: dict[str, int] = {}
    mood_dist: dict[str, int] = {}
    all_activity_texts: list[str] = []
    per_user_context: list[dict[str, Any]] = []

    for user in users:
        reports = (
            db.query(UserDailyReport)
            .filter(
                UserDailyReport.user_id == user.id,
                UserDailyReport.report_date >= period_start,
                UserDailyReport.report_date <= period_end,
                UserDailyReport.is_draft.is_(False),
            )
            .order_by(UserDailyReport.report_date)
            .all()
        )
        staff_reports = (
            db.query(StaffDailyReport)
            .filter(
                StaffDailyReport.user_id == user.id,
                StaffDailyReport.report_date >= period_start,
                StaffDailyReport.report_date <= period_end,
            )
            .order_by(StaffDailyReport.report_date)
            .all()
        )
        if not reports and not staff_reports:
            continue  # 期間内に記録がない利用者はレポート対象外

        user_names[str(user.id)] = user.profile.display_name if user.profile else f"利用者#{user.id}"

        absence_dates = [
            s.report_date.isoformat()
            for s in staff_reports
            if "欠席" in (s.support_content or "")
        ]
        attendance.append(
            {
                "user_id": user.id,
                "attended_dates": [r.report_date.isoformat() for r in reports],
                "absence_dates": absence_dates,
                "report_count": len(reports),
            }
        )

        activity_texts = [r.achievement for r in reports if r.achievement]
        all_activity_texts.extend(activity_texts)

        for r in reports:
            cond = _condition_label(r)
            condition_dist[cond] = condition_dist.get(cond, 0) + 1
            if r.mood is not None:
                label = MOOD_LABELS.get(r.mood, str(r.mood))
                mood_dist[label] = mood_dist.get(label, 0) + 1

        moods = [r.mood for r in reports if r.mood is not None]
        mid = period_start + (period_end - period_start) / 2
        first_half = [r.mood for r in reports if r.mood is not None and r.report_date <= mid]
        second_half = [r.mood for r in reports if r.mood is not None and r.report_date > mid]

        per_user_context.append(
            {
                "user_id": user.id,
                "report_count": len(reports),
                "absence_count": len(absence_dates),
                "avg_mood": round(sum(moods) / len(moods), 2) if moods else None,
                "avg_mood_first_half": round(sum(first_half) / len(first_half), 2) if first_half else None,
                "avg_mood_second_half": round(sum(second_half) / len(second_half), 2) if second_half else None,
                "conditions": [_condition_label(r) for r in reports],
                "sleep_quality_values": [r.sleep_quality for r in reports if r.sleep_quality is not None],
                "fatigue_values": [r.fatigue_level for r in reports if r.fatigue_level is not None],
                "achievement_scores": _achievement_scores(reports),
                "activities": activity_texts,
                "staff_notes": [
                    {"date": s.report_date.isoformat(), "note": s.support_content, "urgency": s.urgency}
                    for s in staff_reports
                ],
                "skill_categories": _skill_categories(activity_texts),
            }
        )

    facts = {
        "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
        "user_names": user_names,
        "attendance": attendance,
        "condition_distribution": condition_dist,
        "mood_distribution": mood_dist,
        "skill_distribution": _skill_categories(all_activity_texts),
        "total_users": len(attendance),
        "total_reports": sum(a["report_count"] for a in attendance),
    }
    ai_context = {
        "period": facts["period"],
        "users": per_user_context,
        "condition_distribution": condition_dist,
        "mood_distribution": mood_dist,
        "skill_distribution": facts["skill_distribution"],
    }
    return facts, ai_context


def _achievement_scores(reports: list[UserDailyReport]) -> list[float]:
    """free_textの「達成感: X/5」を抽出する。"""
    values: list[float] = []
    for r in reports:
        m = re.search(r"達成感[:：]\s*([\d.]+)", r.free_text or "")
        if m:
            values.append(float(m.group(1)))
    return values


def generate_monthly_report_mock(ai_context: dict[str, Any]) -> MonthlyReportResult:
    """ルールベースの月次レポート生成（モックAI・フォールバック用）。"""
    users = ai_context.get("users", [])
    mood_dist = ai_context.get("mood_distribution", {})
    skill_dist = ai_context.get("skill_distribution", {})

    total_reports = sum(u["report_count"] for u in users)
    positive = mood_dist.get("やる気あり", 0) + mood_dist.get("落ち着いている", 0)
    negative = mood_dist.get("つらい", 0) + mood_dist.get("不調ぎみ", 0)

    top_skills = sorted(skill_dist.items(), key=lambda x: -x[1])
    skill_names = "、".join(k for k, _ in top_skills[:3]) if top_skills else "実務的な学習"

    analysis_points = (
        f"期間中は{len(users)}名の利用者から計{total_reports}件の日報が記録されました。"
        f"気分の記録では前向きな回答が{positive}件、負担を示す回答が{negative}件で、"
        + (
            "全体として安定した傾向が見られます。"
            if positive >= negative
            else "負担を示す記録がやや多く、個別の状況確認が必要です。"
        )
        + f"学習面では{skill_names}を中心に取り組みが進んでいます。"
        "一人ひとりの活動ペースには違いがあるため、一律の進め方ではなく、"
        "無理なく継続できるペース配分と小さな達成感の積み重ねを重視した支援が有効と考えられます。"
    )

    user_analyses: list[MonthlyUserAnalysis] = []
    concern_count = 0
    for u in users:
        avg1, avg2 = u.get("avg_mood_first_half"), u.get("avg_mood_second_half")
        avg_mood = u.get("avg_mood")

        # メンタル
        if avg1 is not None and avg2 is not None and avg2 - avg1 <= -0.7:
            mental = f"月の前半（平均{avg1}）に比べ後半（平均{avg2}）に気分の低下傾向が見られます。負担になっている要因がないか、面談での確認が必要です。"
            concern_count += 1
        elif avg1 is not None and avg2 is not None and avg2 - avg1 >= 0.7:
            mental = f"月の後半にかけて気分が上向いています（前半平均{avg1}→後半平均{avg2}）。取り組みが軌道に乗ってきている可能性があります。"
        elif avg_mood is not None and avg_mood >= 3.5:
            mental = f"期間を通じて気分は安定しており（平均{avg_mood}）、意欲的に活動へ取り組めています。"
        elif avg_mood is not None and avg_mood <= 2.5:
            mental = f"気分の自己評価が平均{avg_mood}と低めの傾向があります。活動量の調整と、安心して話せる場面づくりが必要です。"
            concern_count += 1
        else:
            mental = "気分は日によって波がありますが、大きな崩れはなく活動を継続できています。"

        # 体調
        conditions = u.get("conditions", [])
        bad_days = sum(1 for c in conditions if c in ("だるい・眠い", "不調", "頭痛", "だるい", "眠い"))
        absence = u.get("absence_count", 0)
        sleep_vals = u.get("sleep_quality_values", [])
        poor_sleep = sum(1 for s in sleep_vals if s <= 2)
        condition_parts = []
        if bad_days >= max(3, len(conditions) // 3):
            condition_parts.append(f"体調不良の訴え（だるさ・眠気など）が{bad_days}日と多め")
            concern_count += 1
        if poor_sleep >= 3:
            condition_parts.append(f"睡眠の質の低下（入眠困難・中途覚醒）が{poor_sleep}日")
        if absence >= 3:
            condition_parts.append(f"欠席が{absence}回")
        condition = (
            "、".join(condition_parts) + "見られます。休息の確保と活動量の調整を意識した支援が必要です。"
            if condition_parts
            else "体調は概ね安定しており、活動への大きな支障は見られません。"
        )

        # スキル
        cats = u.get("skill_categories", {})
        activities = u.get("activities", [])
        top_cat = max(cats.items(), key=lambda x: x[1])[0] if cats else None
        recent = activities[-1] if activities else None
        skill = (
            f"{top_cat}を中心に学習が進んでいます。" + (f"直近は「{recent}」に取り組みました。" if recent else "")
            if top_cat
            else "期間中の活動記録が少なく、学習面の傾向はまだ判断できません。"
        )

        # 傾向と対策
        ach = u.get("achievement_scores", [])
        avg_ach = round(sum(ach) / len(ach), 1) if ach else None
        if concern_count and (avg_mood is not None and avg_mood <= 2.5 or bad_days >= 5):
            plan = "心身の負担サインが複数見られるため、活動目標を一時的に軽くし、達成しやすい小さな課題で成功体験を積み重ねることを優先します。定期的な面談で本人の負担感を確認してください。"
        elif avg_ach is not None and avg_ach >= 3.5:
            plan = f"達成感の自己評価が平均{avg_ach}と高く、学習のポジティブなサイクルができています。成果を具体的に言語化して称賛し、少し難易度の高い次の課題を提示することで更なる成長を促します。"
        else:
            plan = "作業を細かい手順に分けると力を発揮しやすい傾向があります。チェックリストの活用と、短時間で完了できる課題の積み重ねで自信につなげていきます。"

        user_analyses.append(
            MonthlyUserAnalysis(user_id=u["user_id"], mental=mental, condition=condition, skill=skill, plan=plan)
        )

    action_plan = [
        ActionPlanStep(
            title="課題の特定",
            detail=(
                "気分低下・体調不良のサインが見られる利用者への早期の個別確認、"
                "個々のバイオリズムに合わせた活動計画、記録の継続支援を中核的課題とします。"
                if concern_count
                else "現在の安定した状態の維持と、個々の興味関心に合わせた学習テーマの深化を課題とします。"
            ),
        ),
        ActionPlanStep(
            title="事業所全体の介入策",
            detail="コンディションに応じて選べる「体調別タスクリスト」の導入と、週1回の振り返りの場で小さな達成を共有する仕組みで、予防的かつ柔軟な支援体制を作ります。",
        ),
        ActionPlanStep(
            title="個別アプローチの徹底",
            detail="本レポートの利用者別分析に基づき、一人ひとりに合わせた面談・計画調整・声かけを実行します。翌月のレポートで効果を確認し、支援内容を見直します。",
        ),
    ]

    return MonthlyReportResult(
        analysis_points=analysis_points,
        skill_trends=(
            f"{skill_names}が学習の中心です。"
            + ("関心分野が複数に分かれているため、個々の興味に応じた課題設定が有効です。" if len(top_skills) >= 2 else "")
        ),
        user_analyses=user_analyses,
        action_plan=action_plan,
        confidence=0.6 if total_reports >= 30 else 0.4,
        data_limitations=["本結果はルールベースの参考情報です。必ずスタッフが内容を確認してください"],
    )
