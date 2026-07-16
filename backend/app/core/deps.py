from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import Profile, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="ログインが必要です")
    user_id = decode_token(credentials.credentials, expected_type="access")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="認証情報が無効です。再度ログインしてください")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="アカウントが無効です")
    return user


def require_roles(*roles: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="この操作を行う権限がありません")
        return current_user

    return checker


require_admin = require_roles("admin")
require_staff_or_admin = require_roles("admin", "staff")


def is_assigned_staff(db: Session, staff: User, target_user_id: int) -> bool:
    profile = db.query(Profile).filter(Profile.user_id == target_user_id).first()
    return profile is not None and profile.assigned_staff_id == staff.id


def check_user_access(db: Session, current_user: User, target_user_id: int) -> User:
    """対象利用者へのアクセス権を検証して対象ユーザーを返す。

    - admin: 全員
    - staff: 担当利用者のみ
    - user: 本人のみ
    権限がない場合は404（存在の秘匿）。
    """
    target = db.get(User, target_user_id)
    not_found = HTTPException(status.HTTP_404_NOT_FOUND, detail="対象の利用者が見つかりません")
    if target is None:
        raise not_found
    if current_user.role == "admin":
        return target
    if current_user.role == "staff" and is_assigned_staff(db, current_user, target_user_id):
        return target
    if current_user.id == target_user_id:
        return target
    raise not_found
