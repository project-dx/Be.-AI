"""imported.user1〜3にそれぞれ専用の担当スタッフを割り当てるワンオフスクリプト。

実行例:
DATABASE_URL=... uv run python -m app.assign_dedicated_staff
"""

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Profile, StaffDailyReport, User

STAFF_DEFS = {
    "imported.user1@example.com": ("staff.sato@example.com", "高橋 沙織"),  # 佐藤花子担当
    "imported.user2@example.com": ("staff.yamada@example.com", "伊藤 健"),  # 山田太郎担当
    "imported.user3@example.com": ("staff.suzuki@example.com", "田中 誠"),  # 鈴木一郎担当
}
STAFF_PASSWORD = "Staff123!"


def get_or_create_staff(db, email: str, display_name: str) -> User:
    staff = db.query(User).filter(User.email == email).first()
    if staff:
        return staff
    staff = User(email=email, password_hash=hash_password(STAFF_PASSWORD), role="staff")
    db.add(staff)
    db.flush()
    db.add(Profile(user_id=staff.id, display_name=display_name))
    db.flush()
    print(f"  作成: {display_name} -> {email} / {STAFF_PASSWORD}")
    return staff


def run() -> None:
    db = SessionLocal()
    try:
        for user_email, (staff_email, staff_name) in STAFF_DEFS.items():
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                print(f"  スキップ: {user_email} が見つかりません")
                continue
            staff = get_or_create_staff(db, staff_email, staff_name)
            profile = db.query(Profile).filter(Profile.user_id == user.id).first()
            profile.assigned_staff_id = staff.id
            db.query(StaffDailyReport).filter(StaffDailyReport.user_id == user.id).update(
                {StaffDailyReport.staff_id: staff.id}
            )
            print(f"  {user_email} -> 担当: {staff_name}")
        db.commit()
        print("担当スタッフの割り当てが完了しました")
    finally:
        db.close()


if __name__ == "__main__":
    run()
