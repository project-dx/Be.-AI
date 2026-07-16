"""起動時の初期化処理。

本番デプロイ時、DBにユーザーが1人も存在しない場合に限り、
環境変数 ADMIN_EMAIL / ADMIN_PASSWORD から初期管理者を作成する。
（既にユーザーがいる場合は何もしないため、既存環境には影響しない）
"""

import logging

from app.core.config import get_settings

logger = logging.getLogger("app")


def bootstrap_initial_admin() -> None:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return

    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models import Profile, User

    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        user = User(
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role="admin",
        )
        db.add(user)
        db.flush()
        db.add(Profile(user_id=user.id, display_name="管理者"))
        db.commit()
        logger.info("初期管理者アカウントを作成しました")
    except Exception:
        db.rollback()
        logger.exception("初期管理者アカウントの作成に失敗しました")
    finally:
        db.close()
