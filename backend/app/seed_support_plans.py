"""利用者3名と個別支援計画のダミーデータを投入するスクリプト。

実行例:
DATABASE_URL=... uv run python -m app.seed_support_plans

既に同じメールアドレスのアカウントがある場合は、計画のみ追加する。
"""

from datetime import date, timedelta

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Profile, SupportPlan, SupportPlanVersion, User, UserDailyReport
from app.services.scoring import recalculate_range

PASSWORD = "User123!"
CREATED_DATE = date(2026, 7, 29)
EVALUATION_DATE = date(2026, 10, 31)  # 評価時期: 10月
TARGET_DATE = date(2027, 1, 31)  # 達成時期: 1月（期限終了）

# (利用者番号, 表示名, メール, 計画の内容)
PLANS: list[tuple[str, str, str, dict]] = [
    (
        "10001",
        "山田 花子",
        "member10001@example.com",
        {
            "title": "Webデザイナーとしての就労に向けた個別支援計画",
            "overall_policy": (
                "集中力が高く意欲的である反面、オーバーワークになりがちなため、"
                "体調管理とペース配分を意識しながら支援を行っていきます。\n"
                "Webデザイナーとしての就労に向けて、デザインスキルの向上と作品制作をサポートします。"
            ),
            "long_term_goal": "体調を安定して維持し、Webデザイナーとして一般就労する。",
            "short_term_goals": [
                "ペース配分を意識して安定した通所を継続する。",
                "HTML/CSSの基礎を習得し、ポートフォリオ（作品集）作成の準備を進める。",
            ],
            "current_issues": (
                "【優先1】オーバーワークを防ぎ、体調を崩さず安定して通所する。"
                "集中しすぎると疲れを溜め込んでしまうため、適切なペース配分を身に着ける。"
                "日報等を通して自身の疲労度を客観的に把握する。\n"
                "【優先2】Webデザイン（HTML/CSS）のスキル向上を図る。"
                "デザインスキルを高め、就労に向けた実践的な課題に取り組む。"
                "わからない箇所で手が止まった際は、スムーズに質問ができるようにする。"
            ),
            "strengths": "集中力が高く、意欲的に学習へ取り組める。",
            "user_preferences": "Webデザイナーとして就労したい。",
            "support_methods": [
                "日報や定期面談を活用し、疲労度や睡眠状況の確認を行います。",
                "学習の合間に適度な休憩を取るようスタッフから声掛けを行い、セルフコントロールができるよう支援します。",
                "本人のペースに合わせたWebデザインのカリキュラムや実践課題を提供します。",
                "躓いた際に質問しやすいよう、スタッフからこまめに進捗確認や声掛けを行い、フィードバックを実施します。",
            ],
            "user_actions": [
                "日報で疲労度を記録し、自身の状態を客観的に把握する。",
                "学習の合間に休憩を取り、ペース配分を意識する。",
                "わからない箇所で手が止まったら、スタッフに質問する。",
            ],
            "office_actions": [
                "本人のペースに合わせたWebデザインのカリキュラム・実践課題の提供",
                "こまめな進捗確認と声掛け、フィードバックの実施",
            ],
            "home_actions": ["十分な睡眠時間を確保する。"],
            "evaluation_metrics": ["通所の安定度", "疲労度の推移", "HTML/CSSの習得状況", "ポートフォリオの準備状況"],
        },
    ),
    (
        "10002",
        "佐藤 健一",
        "member10002@example.com",
        {
            "title": "ITエンジニア・プログラマーとしての就労に向けた個別支援計画",
            "overall_policy": (
                "将来への不安やスキルに対する自信のなさを和らげ、精神的な安定を図りながら支援を行っていきます。\n"
                "ITエンジニア・プログラマーとしての就労に向け、スモールステップで成功体験を積めるようサポートします。"
            ),
            "long_term_goal": "精神的に安定した状態で、ITエンジニア・プログラマーとして一般就労する。",
            "short_term_goals": [
                "不安を溜め込まずスタッフに相談できるようになる。",
                "Pythonの基礎学習を進め、小さな課題達成を通じて自信をつける。",
            ],
            "current_issues": (
                "【優先1】将来やスキルに対する不安を軽減し、自信を持つ。"
                "自信をなくしやすいため、精神的なフォローを受けながら学習を進める。"
                "一人で悩みを抱え込まず、定期的に相談できる環境を作る。\n"
                "【優先2】Python等、プログラミングスキルの習得。"
                "ITエンジニアに向けた基礎知識を身に着ける。基礎から実践へ、段階的に課題に取り組む。"
            ),
            "strengths": "学習に真面目に取り組み、着実に積み上げることができる。",
            "user_preferences": "ITエンジニア・プログラマーとして就労したい。",
            "support_methods": [
                "定期的な面談（チェックイン）を実施し、本人の不安を傾聴・整理します。",
                "学習の小さな進捗や日々の通所をこまめに承認・フィードバックし、自己肯定感を高められるよう支援します。",
                "本人の理解度やペースに合わせたスモールステップの課題を提供します。",
                "「できた」という達成感を実感しやすいカリキュラムを組み、技術的な疑問点には丁寧にサポートします。",
            ],
            "user_actions": [
                "不安を感じたら一人で抱え込まず、スタッフに相談する。",
                "小さな課題から段階的に取り組み、できたことを記録する。",
            ],
            "office_actions": [
                "定期的なチェックイン面談の実施",
                "小さな進捗の承認・フィードバック",
                "スモールステップの課題提供",
            ],
            "home_actions": ["学習時間を決めて、無理のない範囲で継続する。"],
            "evaluation_metrics": ["相談できた回数", "Pythonの学習進捗", "自己肯定感の変化", "通所の継続状況"],
        },
    ),
    (
        "10003",
        "高橋 直樹",
        "member10003@example.com",
        {
            "title": "事務職としての就労に向けた個別支援計画",
            "overall_policy": (
                "持ち前の前向きさやコミュニケーション能力を活かしつつ、事務職への就労を目指して支援を行っていきます。\n"
                "業務の正確性を高めるため、作業手順の確認や見直しの習慣化をサポートします。"
            ),
            "long_term_goal": "PCスキルを活かし、事務職として一般就労する。",
            "short_term_goals": [
                "作業時のケアレスミスを減らし、見直しの習慣をつける。",
                "Word/Excel等のオフィスソフトの基礎スキル（資格取得レベル）を習得する。",
            ],
            "current_issues": (
                "【優先1】事務作業における正確性の向上。"
                "作業スピードは速いがケアレスミスが発生しやすいため、細部への注意力を高める。"
                "見直し（セルフチェック）の習慣を身に着ける。\n"
                "【優先2】事務職に必要なPCスキル（Excel/Word等）の習得。"
                "バックオフィス業務で求められるPCスキルを身に着ける。MOS資格などの取得に向けて学習を進める。"
            ),
            "strengths": "前向きさとコミュニケーション能力が高く、作業スピードが速い。",
            "user_preferences": "事務職として就労したい。MOS資格を取得したい。",
            "support_methods": [
                "作業完了後に必ず見直しを行うよう促し、セルフチェックの習慣づけを支援します。",
                "ミスを防ぐためのチェックリストの作成・活用方法を提案し、一緒に実践を通して練習します。",
                "実践的な事務課題（データ入力や文書作成など）や、資格取得に向けた学習プログラムを提供します。",
                "日々のコミュニケーションを大切にしながら、学習の進捗確認とフィードバックを行います。",
            ],
            "user_actions": [
                "作業が終わったら必ず見直し（セルフチェック）を行う。",
                "チェックリストを活用してミスを防ぐ。",
                "MOS資格取得に向けて学習を進める。",
            ],
            "office_actions": [
                "セルフチェックの習慣づけ支援",
                "チェックリストの作成・活用の提案",
                "実践的な事務課題と資格学習プログラムの提供",
            ],
            "home_actions": ["学習した内容を復習する時間をつくる。"],
            "evaluation_metrics": ["ケアレスミスの発生件数", "見直しの実施率", "Word/Excelの習得状況", "MOS資格の学習進捗"],
        },
    ),
]


# 個別支援計画の人物像に沿った日報のパターン
# key: 利用者番号, value: 期間の進み具合(0.0〜1.0)から日報の値を作る関数の設定
REPORT_PATTERNS: dict[str, dict] = {
    # 山田花子: 集中しすぎてオーバーワークになりやすい。後半はペース配分が身につき疲労が改善
    "10001": {
        "mood": lambda p: 4 if p > 0.5 else 3,
        "sleep": lambda p: round(5.5 + 1.5 * p, 1),
        "fatigue": lambda p: 4 if p < 0.5 else 2,
        "stress": lambda p: 3 if p < 0.5 else 2,
        "social": lambda p: 3,
        "achievements": ["Webデザインの動画学習", "HTML/CSSの基礎練習", "バナー制作の課題", "ポートフォリオの構成案作成"],
        "success": "作業の区切りで休憩を取れた",
        "difficulty": "集中しすぎて休憩を忘れてしまった",
    },
    # 佐藤健一: 不安を抱えやすい。相談できるようになり後半は気分が安定
    "10002": {
        "mood": lambda p: 2 if p < 0.4 else 3 if p < 0.7 else 4,
        "sleep": lambda p: round(6.0 + 1.0 * p, 1),
        "fatigue": lambda p: 3,
        "stress": lambda p: 4 if p < 0.4 else 3 if p < 0.7 else 2,
        "social": lambda p: 2 if p < 0.5 else 3,
        "achievements": ["Pythonの基礎学習", "変数と条件分岐の練習", "簡単な計算プログラムの作成", "リスト操作の練習"],
        "success": "わからない箇所をスタッフに質問できた",
        "difficulty": "自分のスキルに自信が持てず不安になった",
    },
    # 高橋直樹: 前向きで安定。作業は速いがケアレスミスが課題
    "10003": {
        "mood": lambda p: 4,
        "sleep": lambda p: 7.0,
        "fatigue": lambda p: 2,
        "stress": lambda p: 2,
        "social": lambda p: 4,
        "achievements": ["Excelの関数練習", "データ入力の実践課題", "Wordでの文書作成", "MOS模擬テスト"],
        "success": "見直しでミスを見つけて直せた",
        "difficulty": "急いで進めてケアレスミスが出た",
    },
}


def _seed_daily_reports(db, user: User, number: str, today: date, months: int = 6) -> int:
    """人物像に沿った日報を平日のみ作成する（すでにある日はスキップ）。"""
    pattern = REPORT_PATTERNS[number]
    start = today - timedelta(days=months * 30)
    created = 0
    day = start
    index = 0
    while day <= today:
        if day.weekday() < 5:  # 平日のみ通所
            progress = (day - start).days / max((today - start).days, 1)
            exists = (
                db.query(UserDailyReport)
                .filter(UserDailyReport.user_id == user.id, UserDailyReport.report_date == day)
                .first()
            )
            if not exists:
                fatigue = pattern["fatigue"](progress)
                db.add(
                    UserDailyReport(
                        user_id=user.id,
                        report_date=day,
                        mood=pattern["mood"](progress),
                        sleep_hours=pattern["sleep"](progress),
                        bedtime="23:30",
                        wake_time="07:00",
                        sleep_quality=3 if fatigue >= 4 else 4,
                        breakfast_status="eaten",
                        lunch_status="eaten",
                        dinner_status="eaten",
                        exercise_minutes=20,
                        work_study_minutes=300,
                        stress_level=pattern["stress"](progress),
                        fatigue_level=fatigue,
                        social_level=pattern["social"](progress),
                        achievement=pattern["achievements"][index % len(pattern["achievements"])],
                        success_experience=pattern["success"] if index % 3 == 0 else None,
                        difficulty=pattern["difficulty"] if fatigue >= 4 and index % 4 == 0 else None,
                        is_draft=False,
                    )
                )
                created += 1
            index += 1
        day += timedelta(days=1)
    return created


def _get_or_create_user(db, email: str, display_name: str, staff_id: int | None) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"  既存: {display_name} / {email}")
        return user
    user = User(email=email, password_hash=hash_password(PASSWORD), role="user")
    db.add(user)
    db.flush()
    db.add(
        Profile(
            user_id=user.id,
            display_name=display_name,
            support_start_date=CREATED_DATE,
            assigned_staff_id=staff_id,
        )
    )
    db.flush()
    print(f"  作成: {display_name} / {email} / {PASSWORD}")
    return user


def run() -> None:
    db = SessionLocal()
    try:
        # 担当スタッフ（いなければ割り当てなしで作成する）
        staff = db.query(User).filter(User.role == "staff").order_by(User.id).first()
        staff_id = staff.id if staff else None

        today = date.today()
        print("--- 利用者 ---")
        created_plans = 0
        for number, display_name, email, plan_data in PLANS:
            user = _get_or_create_user(db, email, display_name, staff_id)

            # 人物像に沿った6か月分の日報とスコア
            created_reports = _seed_daily_reports(db, user, number, today)
            if created_reports:
                db.flush()
                recalculate_range(db, user.id, today - timedelta(days=180), today)
                db.flush()
                print(f"    日報を{created_reports}件作成し、スコアを算出しました")

            existing = db.query(SupportPlan).filter(SupportPlan.user_id == user.id).first()
            if existing:
                print(f"    支援計画は登録済みのためスキップ: {display_name}")
                continue

            plan = SupportPlan(
                user_id=user.id,
                title=plan_data["title"],
                status="approved",
                overall_policy=plan_data["overall_policy"],
                current_issues=plan_data["current_issues"],
                strengths=plan_data["strengths"],
                user_preferences=plan_data["user_preferences"],
                long_term_goal=plan_data["long_term_goal"],
                short_term_goals_json=plan_data["short_term_goals"],
                support_methods_json=plan_data["support_methods"],
                home_actions_json=plan_data["home_actions"],
                office_actions_json=plan_data["office_actions"],
                user_actions_json=plan_data["user_actions"],
                evaluation_metrics_json=plan_data["evaluation_metrics"],
                evaluation_date=EVALUATION_DATE,
                next_review_date=TARGET_DATE,
                notes=f"利用者番号 {number}／目標達成時期: 6か月（評価時期 10月・達成時期 1月）",
                created_by=staff_id,
                approved_by=staff_id,
            )
            db.add(plan)
            db.flush()
            db.add(
                SupportPlanVersion(
                    support_plan_id=plan.id,
                    version_number=1,
                    snapshot_json={"title": plan.title, "status": plan.status},
                    changed_by=staff_id,
                    change_reason="個別支援計画の新規作成",
                )
            )
            created_plans += 1
            print(f"    支援計画を作成: {plan_data['title']}")

        db.commit()
        print(f"\n{created_plans}件の個別支援計画を作成しました")
    finally:
        db.close()


if __name__ == "__main__":
    run()
