"""指定したアカウントの役割（role）を変更するスクリプト。

実行例:
DATABASE_URL=... uv run python -m app.set_role staff miki@example.com yamaguchi@example.com
DATABASE_URL=... uv run python -m app.set_role user miki@example.com

日報・支援記録などのデータは削除しない（役割だけを変更する）。
"""

import argparse

from app.core.database import SessionLocal
from app.models import Profile, StaffDailyReport, User, UserDailyReport

ROLES = ("admin", "staff", "user")


def run(role: str, emails: list[str]) -> None:
    db = SessionLocal()
    try:
        changed = 0
        for email in emails:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                print(f"  見つかりません: {email}")
                continue
            profile = db.query(Profile).filter(Profile.user_id == user.id).first()
            name = profile.display_name if profile else email

            if user.role == role:
                print(f"  変更なし: {name}（すでに {role}）")
                continue

            # 役割を変えると表示場所が変わる記録がないか確認して知らせる
            support_records = (
                db.query(StaffDailyReport).filter(StaffDailyReport.user_id == user.id).count()
            )
            daily_reports = db.query(UserDailyReport).filter(UserDailyReport.user_id == user.id).count()

            print(f"  {name}: {user.role} → {role}")
            if role != "user" and (support_records or daily_reports):
                print(
                    f"    ※ 支援記録{support_records}件・日報{daily_reports}件は残りますが、"
                    "「利用者一覧」には表示されなくなります"
                )
            user.role = role
            # スタッフ・管理者になる場合は担当スタッフの割り当てを外す
            if role != "user" and profile and profile.assigned_staff_id is not None:
                profile.assigned_staff_id = None
            changed += 1

        db.commit()
        print(f"\n{changed}件の役割を変更しました")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="アカウントの役割を変更する")
    parser.add_argument("role", choices=ROLES, help="変更後の役割")
    parser.add_argument("emails", nargs="+", help="対象のメールアドレス")
    args = parser.parse_args()
    run(args.role, args.emails)
