"""かべなしクラウドの6月分「提供実績記録」を取り込むスクリプト。

実行例:
DATABASE_URL=... uv run python -m app.import_june_records

処理内容:
1. 9名を利用者（role=user）として整備する（既にスタッフとして作成済みなら役割を変更）
2. 記録者「竹多」をスタッフとして作成し、9名の担当に設定する
3. 三木涼太郎さんの6月分の支援記録を取り込む（他8名は6月の記録なし）
4. リスク検知（自傷・体調不良などのキーワード）を実行する

同じ日付の記録が既にある場合は重複作成しない。
"""

from datetime import date

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Profile, StaffDailyReport, User
from app.services.risk import evaluate_staff_report_risk

USER_PASSWORD = "User123!"
STAFF_PASSWORD = "Staff123!"

# かべなしクラウドの利用者（表示名, メールアドレス）
MEMBERS: list[tuple[str, str]] = [
    ("三木 涼太郎", "miki@example.com"),
    ("山口 乙羽", "yamaguchi@example.com"),
    ("瀬戸 千夏", "seto@example.com"),
    ("小谷 悠人", "kotani@example.com"),
    ("大瀬 嘉也", "ose@example.com"),
    ("南野 花奈", "minamino@example.com"),
    ("直居 理央", "naoi@example.com"),
    ("今井 隆希", "imai@example.com"),
    ("松本 瑠那", "matsumoto@example.com"),
]

RECORDER_NAME = "竹多"
RECORDER_EMAIL = "takeda@example.com"

# 三木涼太郎さんの6月分（日付, 支援時間(分), 緊急度, 支援記録）
MIKI_JUNE_RECORDS: list[tuple[date, int | None, str, str]] = [
    (
        date(2026, 6, 3), 75, "normal",
        "本日、初めての面談を行いました。\n"
        "本人、お母様、相談支援員徳田様、竹多の4人での面談を行いました。\n"
        "昨日と本日と、学校は下痢を起こして体調不良で休んでいますが、面談中は椅子に座り、"
        "時計を見ながら、質問に答えながら過ごしています。\n"
        "お母様にジョブキャンバスカラフル・金沢の契約書をお渡ししています。\n"
        "アセスメントを取るために、今後の予定を立てました。\n"
        "本人の普段の生活の様子を確認しています。\n"
        "会話をつなぐコミュニケーションは取れませんが、返答など聞き方によって返事はします。"
        "静かに過ごすことが好きなようです。時計を見ていると落ち着いて過ごすことが出来ています。",
    ),
    (
        date(2026, 6, 6), 60, "check",
        "JR美川駅での会議室で、書類のハンコ押しの練習を行いました。\n"
        "何個も押していて、曲がってしまうと興奮して、自傷行為を行って右手の上の方を噛もうとして、"
        "Tシャツを引っ張っています。お母様も同席されていて、困惑されていました。"
        "ミスを起こしてしまうと興奮することがありますが、本日は目つきも座って怖い表情になったと"
        "お母様が怖がっていました。\n"
        "挨拶はしっかり出来ています。\n"
        "JR美川駅は、佛子園の利用者様が掃除などを行っていて、好きではないとのことです。\n"
        "次回の面談は、別の場所を提案して、下見に行かれました。\n"
        "お菓子が好きだとのことで、スタッフからご褒美のお菓子を渡したときには、しっかり感謝を述べられています。\n"
        "次回も、就労アセスメントでの面談をお伝えしてあります。",
    ),
    (
        date(2026, 6, 10), 60, "normal",
        "本日、JR美川駅にて面談を行いました。本人とお母様と支援員3人で行い、"
        "後半は相談支援員の徳田様も参加されています。\n"
        "ハンコ押しの実践作業を行いました。丁寧にゆっくり確実に押すことが出来ていて、"
        "終了後は「出来ました」と報告を自分から声を出して伝えることが出来ていました。"
        "作業を落ち着て出来たことを褒めました。\n"
        "お母様に普段の様子を確認しています。\n"
        "面談の途中も時計を見ています。自宅では時計と音楽を聴くことが好きとのことです。"
        "突然、気分の変調があるそうですが、本日は1時間穏やかに過ごされています。\n"
        "クスリの副作用などもあるかと心配されていました。\n"
        "石川療育センターなぎしたみちこ先生が主治医です。最近5月20日の薬が変わったそうで、"
        "普段は2ヶ月に一回の受診ですが、今月は早めに受診とのことです。"
        "服用しながら副作用の点を確認し、生活リズムの確認を行っていきます。\n"
        "夏休みの過ごし方なども、相談支援員の方に確認を行っています。"
        "本人は見学に行きたくないと言ってたそうですが、面談時には見学に行くよ承諾していました。\n"
        "帰りの挨拶などもしっかり行うことが出来ています。",
    ),
    (
        date(2026, 6, 15), 75, "normal",
        "就労継続B型事象所一歩での箱折作業での実習で確認しています。\n"
        "挨拶は出来ています。すぐの作業に取り掛かり、箱折作業を行っています。"
        "15個の見本作業では出来ています。その後15個分とりかかり、完成を積み重ね、"
        "横にもう一度15個分を向きをそろえての作業で、数を数えながら向きにも注意し、集中しています。\n"
        "左手の最後のたたむ箇所での折り目が付き、気を付けるポイントを説明しています。"
        "真ん中に折り目を付けるだけではなく、端の折り目を付けるところはポイントです。"
        "伝えると、気を付けることが出来ています。\n"
        "学校の担任の先生も見学していて、確認作業を行っています。情報共有しています。\n"
        "毎日確認することを伝えてあります。",
    ),
    (
        date(2026, 6, 16), None, "caution",
        "【欠席記録】本日、実習予定でしたが、ご本人が「行きたくない」と言われたために、"
        "欠席されるという連絡が、お母様からありました。\n"
        "就労選択支援員が同行予定にしていましたが、突然のキャンセルの為対応しました。"
        "本人の就労に対する意識の確認は明日させていただきます。\n"
        "お母様には、承知しましたと連絡済みです。お母様からは、昨日のお礼も含めてのコメントありです。\n"
        "実習二日目での欠席で、何が嫌だったのかを確認する必要あります。"
        "体調不良ではなく、精神的に欠席を申し出たのだと思われます。"
        "自分ではっきり言えたことは、明日褒めますが、就労に向けての意識の確認が必要です。\n"
        "就労選択支援員として、準備をしていたので、欠席の記録を記入します。",
    ),
    (
        date(2026, 6, 17), 60, "normal",
        "本日、ハーネスの作業に取り掛かり、線を差し込み一本一本丁寧に行っています。\n"
        "いつもの時計は、机の下に置いての作業になります。\n"
        "作業を行いながら、きょろきょろしていました。\n"
        "元気に挨拶を出来たことを褒めました。",
    ),
    (
        date(2026, 6, 18), 60, "normal",
        "本人が来る前に、就労選択支援員が待機し、来る時間を待ちました。"
        "入ってくるときの挨拶の仕方などを確認し、挨拶は出来ています。表情は穏やかでした。"
        "トイレに行き、その後からすぐ作業を始めました。\n"
        "丁寧に箱折作業を行っています。\n"
        "スタッフの声掛けにもしっかり返事をしています。\n"
        "お母様からの連絡帳には、箱折と本人がどう向き合いか見守りたいとの記載がありました。",
    ),
    (
        date(2026, 6, 19), 60, "normal",
        "穏やかの表情で作業に取り掛かれています。\n"
        "作業前にはトイレに行き、その後に開始します。\n"
        "自分から箱を取りに行き、作業に取り掛かっていました。\n"
        "集中して行うことが出来ています。また、後日面談をさせてくださいと伝えると"
        "「はい」としっかり返事をしています。\n"
        "夕方は、保護者のからも作業を見学に行きます。",
    ),
]


def _get_or_create(db, email: str, display_name: str, role: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        if user.role != role:
            print(f"  役割を変更: {display_name} （{user.role} → {role}）")
            user.role = role
        return user
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name=display_name))
    db.flush()
    print(f"  作成: {display_name} / {email}（{role}）")
    return user


def run() -> None:
    db = SessionLocal()
    try:
        # 1. 記録者をスタッフとして用意
        print("--- スタッフ ---")
        recorder = _get_or_create(db, RECORDER_EMAIL, RECORDER_NAME, "staff", STAFF_PASSWORD)
        db.flush()

        # 2. 9名を利用者として整備し、担当スタッフを設定
        print("--- 利用者 ---")
        members: dict[str, User] = {}
        for display_name, email in MEMBERS:
            user = _get_or_create(db, email, display_name, "user", USER_PASSWORD)
            profile = db.query(Profile).filter(Profile.user_id == user.id).first()
            if profile and profile.assigned_staff_id != recorder.id:
                profile.assigned_staff_id = recorder.id
            members[display_name] = user
        db.flush()

        # 3. 6月分の支援記録を取り込む
        print("--- 6月分の支援記録 ---")
        miki = members["三木 涼太郎"]
        imported = 0
        for report_date, minutes, urgency, content in MIKI_JUNE_RECORDS:
            exists = (
                db.query(StaffDailyReport)
                .filter(
                    StaffDailyReport.user_id == miki.id,
                    StaffDailyReport.report_date == report_date,
                )
                .first()
            )
            if exists:
                print(f"  スキップ（登録済み）: {report_date}")
                continue
            report = StaffDailyReport(
                user_id=miki.id,
                staff_id=recorder.id,
                report_date=report_date,
                support_minutes=minutes,
                support_content=content,
                urgency=urgency,
            )
            db.add(report)
            db.flush()
            evaluate_staff_report_risk(db, report)  # 自傷などのキーワードを検知
            imported += 1
            print(f"  取り込み: {report_date}（{urgency}）")

        db.commit()
        print(f"\n三木 涼太郎さんの6月分を{imported}件取り込みました")
        print("※ 他8名は6月の支援記録が空欄のため、取り込む記録はありません")
    finally:
        db.close()


if __name__ == "__main__":
    run()
