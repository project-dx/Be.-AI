"""スタッフアカウントをまとめて追加するスクリプト。

実行例:
DATABASE_URL=... uv run python -m app.add_staff

既に同じメールアドレスのアカウントがある場合はスキップする（重複作成しない）。
初期パスワードは全員共通のため、初回ログイン後に各自で変更してもらうこと。
"""

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Profile, User

INITIAL_PASSWORD = "Staff123!"

# (表示名, メールアドレス)
STAFF_MEMBERS: list[tuple[str, str]] = [
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


def run() -> None:
    db = SessionLocal()
    created = 0
    try:
        for display_name, email in STAFF_MEMBERS:
            if db.query(User).filter(User.email == email).first():
                print(f"  スキップ（登録済み）: {display_name} / {email}")
                continue
            user = User(email=email, password_hash=hash_password(INITIAL_PASSWORD), role="staff")
            db.add(user)
            db.flush()
            db.add(Profile(user_id=user.id, display_name=display_name))
            created += 1
            print(f"  作成: {display_name} / {email} / {INITIAL_PASSWORD}")
        db.commit()
        print(f"\n{created}名のスタッフを追加しました")
        if created:
            print("※ 初期パスワードは全員共通です。初回ログイン後に変更してもらってください")
    finally:
        db.close()


if __name__ == "__main__":
    run()
