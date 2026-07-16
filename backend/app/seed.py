"""デモ用初期データ投入スクリプト。

実行: uv run python -m app.seed
本番環境（ENVIRONMENT=production）では --force を付けない限り実行されない。
"""

import argparse
import sys
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    AiAnalysis,
    Goal,
    Profile,
    StaffDailyReport,
    SupportPlan,
    SupportPlanVersion,
    User,
    UserDailyReport,
)
from app.services.ai.context import build_analysis_context
from app.services.ai.factory import get_prompt_version
from app.services.ai.mock import MockAIService
from app.services.risk import evaluate_user_risks
from app.services.scoring import recalculate_range

DEMO_ACCOUNTS = {
    "admin": ("admin@example.com", "Admin123!"),
    "staff": ("staff@example.com", "Staff123!"),
    "user1": ("user1@example.com", "User123!"),
    "user2": ("user2@example.com", "User123!"),
    "user3": ("user3@example.com", "User123!"),
}

DAYS = 20  # 日報の日数


def _mk_user(db: Session, email: str, password: str, role: str, display_name: str,
             assigned_staff_id: int | None = None) -> User:
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()
    db.add(
        Profile(
            user_id=user.id,
            display_name=display_name,
            support_start_date=date.today() - timedelta(days=180),
            assigned_staff_id=assigned_staff_id,
        )
    )
    return user


def _report(user_id: int, d: date, mood: int, sleep: float, bed: str, wake: str,
            quality: int, stress: int, fatigue: int, social: int,
            success: str | None = None, difficulty: str | None = None,
            exercise: int = 20, work: int = 240) -> UserDailyReport:
    return UserDailyReport(
        user_id=user_id,
        report_date=d,
        mood=mood,
        sleep_hours=sleep,
        bedtime=bed,
        wake_time=wake,
        sleep_quality=quality,
        breakfast_status="eaten",
        lunch_status="eaten",
        dinner_status="eaten" if mood >= 3 else "partial",
        exercise_minutes=exercise,
        work_study_minutes=work,
        stress_level=stress,
        fatigue_level=fatigue,
        social_level=social,
        achievement="作業を予定どおり進められた" if mood >= 3 else None,
        success_experience=success,
        difficulty=difficulty,
        tomorrow_goal="明日も日報を入力する",
        free_text=None,
        is_draft=False,
    )


def seed_user1_normal(db: Session, user_id: int, today: date) -> None:
    """正常傾向: 睡眠7〜8時間・ストレス低め・成功体験あり"""
    pattern = [
        (4, 7.5, "23:00", "06:30", 4, 2, 2, 4, "新しい作業手順を覚えられた"),
        (4, 7.0, "23:15", "06:15", 4, 2, 2, 3, None),
        (5, 8.0, "22:45", "06:45", 5, 1, 1, 4, "後輩に作業を教えることができた"),
        (4, 7.5, "23:00", "06:30", 4, 2, 2, 4, None),
        (3, 7.0, "23:30", "06:30", 3, 2, 3, 3, "苦手な電話対応を1件できた"),
    ]
    for i in range(DAYS):
        d = today - timedelta(days=DAYS - 1 - i)
        mood, sleep, bed, wake, quality, stress, fatigue, social, success = pattern[i % len(pattern)]
        db.add(_report(user_id, d, mood, sleep, bed, wake, quality, stress, fatigue, social, success))


def seed_user2_sleep_decline(db: Session, user_id: int, today: date) -> None:
    """睡眠低下傾向: 後半になるほど睡眠時間が短くなる"""
    for i in range(DAYS):
        d = today - timedelta(days=DAYS - 1 - i)
        progress = i / (DAYS - 1)  # 0 → 1
        sleep = round(7.5 - 3.0 * progress, 1)  # 7.5h → 4.5h
        bed_hour = 23 + int(progress * 2)  # 23時 → 25時(1時)
        bed = f"{bed_hour % 24:02d}:30"
        quality = 4 if progress < 0.4 else 3 if progress < 0.7 else 2
        mood = 4 if progress < 0.5 else 3
        fatigue = 2 if progress < 0.5 else 4
        success = "集中して作業できた" if i % 4 == 0 and progress < 0.6 else None
        db.add(
            _report(user_id, d, mood, sleep, bed, "06:30", quality, 3, fatigue, 3,
                    success, difficulty="夜、眠れないことが増えた" if progress > 0.7 else None)
        )


def seed_user3_stress_rise(db: Session, user_id: int, today: date) -> None:
    """ストレス上昇傾向: 後半でストレス5が3日連続（リスク検知の確認用）"""
    for i in range(DAYS):
        d = today - timedelta(days=DAYS - 1 - i)
        progress = i / (DAYS - 1)
        stress = 2 if progress < 0.4 else 3 if progress < 0.6 else 4 if progress < 0.85 else 5
        mood = 4 if progress < 0.4 else 3 if progress < 0.7 else 2
        social = 3 if progress < 0.6 else 2
        db.add(
            _report(user_id, d, mood, 6.5, "23:45", "06:45", 3, stress, 3, social,
                    success="朝の準備が時間どおりにできた" if i % 5 == 0 else None,
                    difficulty="作業量が多く感じる" if progress > 0.6 else None,
                    work=300)
        )


def seed_staff_reports(db: Session, staff_id: int, user_ids: dict[str, int], today: date) -> None:
    entries = [
        (user_ids["user1"], 6, "normal", "作業訓練の見守りと声かけ", "落ち着いて作業に取り組めている",
         "作業の正確さを本人と一緒に確認した", "自分から質問ができていた", None),
        (user_ids["user1"], 2, "normal", "週次面談", "表情が明るい",
         "今後やってみたい作業について話した", "目標を自分の言葉で話せた", None),
        (user_ids["user2"], 5, "normal", "作業訓練の支援", "やや疲れた様子",
         "最近の睡眠について軽く話題にした", "正直に眠れていないと話してくれた", "睡眠時間の減少が気になる"),
        (user_ids["user2"], 3, "caution", "個別面談", "眠そうな様子が目立つ",
         "夜の過ごし方について本人と一緒に振り返った", "スマートフォンの利用時間が増えていると話した",
         "睡眠リズムの乱れが続いている"),
        (user_ids["user2"], 1, "check", "作業中の様子観察", "午後に集中が切れる場面があった",
         "休憩を挟むことを提案した", "提案を受け入れて休憩できた", "疲労の蓄積を確認する必要がある"),
        (user_ids["user3"], 4, "normal", "グループ活動の支援", "参加はできているが口数が少ない",
         "活動後に感想を聞いた", "少し疲れていると話した", None),
        (user_ids["user3"], 2, "caution", "個別声かけ", "表情が硬い",
         "困っていることがないか確認した", "作業量について負担を感じていると話した", "作業量の調整を検討"),
        (user_ids["user3"], 0, "urgent", "緊急面談", "強い疲労とストレスを訴えている",
         "本人の訴えを傾聴し、無理をしないよう伝えた", "少し落ち着いた様子で帰宅した",
         "ストレス評価が高い状態が続いている。早急にチーム内で対応を検討する"),
    ]
    for user_id, days_ago, urgency, content, condition, conversation, response, issues in entries:
        db.add(
            StaffDailyReport(
                user_id=user_id,
                staff_id=staff_id,
                report_date=today - timedelta(days=days_ago),
                support_minutes=45,
                support_content=content,
                user_condition=condition,
                conversation_summary=conversation,
                positive_points="取り組みを続けられている",
                issues=issues,
                behavior_changes=None,
                support_method="傾聴と勇気づけ",
                user_response=response,
                next_check="次回の面談で様子を確認",
                urgency=urgency,
                free_text=None,
            )
        )


def seed_goals(db: Session, user_ids: dict[str, int], today: date) -> None:
    goals = [
        (user_ids["user1"], "週5日、日報を入力する", 80, "active"),
        (user_ids["user1"], "新しい作業工程を1人で完了する", 60, "active"),
        (user_ids["user2"], "23時までに就寝準備を始める", 30, "active"),
        (user_ids["user3"], "困ったときにスタッフへ相談する", 50, "active"),
    ]
    for user_id, title, progress, status in goals:
        db.add(
            Goal(
                user_id=user_id,
                title=title,
                description=None,
                target_date=today + timedelta(days=30),
                status=status,
                progress=progress,
            )
        )


def seed_ai_analyses(db: Session, user_ids: dict[str, int], today: date) -> None:
    mock = MockAIService()
    prompt_version = get_prompt_version("daily_analysis_prompt.md")
    for key in ["user1", "user2", "user3"]:
        user_id = user_ids[key]
        start = today - timedelta(days=13)
        context = build_analysis_context(db, user_id, start, today)
        result = mock.analyze_daily(context)
        db.add(
            AiAnalysis(
                user_id=user_id,
                analysis_date=today,
                analysis_type="daily_analysis",
                input_period_start=start,
                input_period_end=today,
                model_name="mock",
                prompt_version=prompt_version,
                result_json=result.model_dump(),
                status="success",
            )
        )


def seed_support_plans(db: Session, user_ids: dict[str, int], staff_id: int, today: date) -> None:
    mock = MockAIService()

    # user2: AI下書き（未承認）
    context2 = build_analysis_context(db, user_ids["user2"], today - timedelta(days=29), today)
    draft = mock.generate_support_plan(context2)
    plan_draft = SupportPlan(
        user_id=user_ids["user2"],
        title=draft.title,
        status="draft",
        current_issues=draft.current_issues,
        strengths=draft.strengths,
        user_preferences=draft.user_preferences,
        background_hypothesis=draft.background_hypothesis,
        long_term_goal=draft.long_term_goal,
        short_term_goals_json=draft.short_term_goals,
        support_methods_json=draft.support_methods,
        home_actions_json=draft.home_actions,
        office_actions_json=draft.office_actions,
        user_actions_json=draft.user_actions,
        evaluation_metrics_json=draft.evaluation_metrics,
        next_review_date=today + timedelta(days=90),
        notes=draft.notes,
        created_by=staff_id,
    )
    db.add(plan_draft)
    db.flush()
    db.add(
        SupportPlanVersion(
            support_plan_id=plan_draft.id,
            version_number=1,
            snapshot_json={"title": plan_draft.title, "status": "draft"},
            changed_by=staff_id,
            change_reason="AIによる下書き生成（デモ）",
        )
    )

    # user1: 承認済み計画
    from datetime import UTC, datetime

    plan_approved = SupportPlan(
        user_id=user_ids["user1"],
        title="就労準備性の向上に向けた支援計画",
        status="approved",
        current_issues="就労に向けた実践経験がまだ少ない",
        strengths="日報入力の継続、成功体験の具体的な記録ができている",
        user_preferences="事務系の仕事に就きたい",
        background_hypothesis="生活リズムは安定しており、実務経験の機会があれば準備性が高まる可能性がある",
        long_term_goal="6か月後に企業実習へ参加できる状態になる",
        short_term_goals_json=["週5日の通所を4週間継続する", "PC入力の練習を週3回行う"],
        support_methods_json=["週1回の振り返り面談", "実習先候補の情報提供"],
        home_actions_json=["就寝時刻を一定に保つ"],
        office_actions_json=["PC訓練の機会提供", "成功体験の共有"],
        user_actions_json=["日報を毎日入力する", "訓練の記録をつける"],
        evaluation_metrics_json=["通所率", "就労準備度スコアの推移", "訓練の達成度"],
        evaluation_date=today + timedelta(days=60),
        next_review_date=today + timedelta(days=90),
        notes="本人の体調に合わせて無理のない範囲で進める",
        created_by=staff_id,
        approved_by=staff_id,
        approved_at=datetime.now(UTC),
    )
    db.add(plan_approved)
    db.flush()
    for version, reason in [(1, "新規作成"), (2, "本人の希望を反映して修正"), (3, "承認")]:
        db.add(
            SupportPlanVersion(
                support_plan_id=plan_approved.id,
                version_number=version,
                snapshot_json={"title": plan_approved.title, "status": "approved" if version == 3 else "draft"},
                changed_by=staff_id,
                change_reason=reason,
            )
        )


def run_seed(force: bool = False) -> None:
    settings = get_settings()
    if settings.is_production and not force:
        print("本番環境（ENVIRONMENT=production）ではデモデータを作成しません。--force で強制実行できます")
        sys.exit(1)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == DEMO_ACCOUNTS["admin"][0]).first():
            print("デモデータは既に投入済みです（admin@example.com が存在します）")
            return

        today = date.today()

        _mk_user(db, *DEMO_ACCOUNTS["admin"], role="admin", display_name="管理者 太郎")
        staff = _mk_user(db, *DEMO_ACCOUNTS["staff"], role="staff", display_name="支援 花子")
        db.flush()
        user1 = _mk_user(db, *DEMO_ACCOUNTS["user1"], role="user", display_name="佐藤 一郎", assigned_staff_id=staff.id)
        user2 = _mk_user(db, *DEMO_ACCOUNTS["user2"], role="user", display_name="鈴木 二葉", assigned_staff_id=staff.id)
        user3 = _mk_user(db, *DEMO_ACCOUNTS["user3"], role="user", display_name="高橋 三奈", assigned_staff_id=staff.id)
        db.flush()
        user_ids = {"user1": user1.id, "user2": user2.id, "user3": user3.id}

        seed_user1_normal(db, user1.id, today)
        seed_user2_sleep_decline(db, user2.id, today)
        seed_user3_stress_rise(db, user3.id, today)
        seed_staff_reports(db, staff.id, user_ids, today)
        seed_goals(db, user_ids, today)
        db.flush()

        # スコア計算とリスク判定
        for user_id in user_ids.values():
            recalculate_range(db, user_id, today - timedelta(days=DAYS - 1), today)
        db.flush()
        for user_id in user_ids.values():
            evaluate_user_risks(db, user_id, today)
        db.flush()

        seed_ai_analyses(db, user_ids, today)
        seed_support_plans(db, user_ids, staff.id, today)

        db.commit()
        print("デモデータの投入が完了しました")
        print("--- デモアカウント ---")
        for label, (email, password) in DEMO_ACCOUNTS.items():
            print(f"  {label}: {email} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="デモデータ投入")
    parser.add_argument("--force", action="store_true", help="本番環境でも強制実行する")
    args = parser.parse_args()
    run_seed(force=args.force)
