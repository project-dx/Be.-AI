from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user, require_admin, require_staff_or_admin
from app.core.security import hash_password
from app.models import Profile, User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/api/users", tags=["利用者・アカウント"])


@router.get("", response_model=list[UserOut])
def list_users(
    role: str | None = Query(default=None, pattern="^(admin|staff|user)$"),
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    query = db.query(User).options(joinedload(User.profile))
    if role:
        query = query.filter(User.role == role)
    if current_user.role == "staff":
        # スタッフは担当利用者のみ
        query = query.join(Profile, Profile.user_id == User.id).filter(
            Profile.assigned_staff_id == current_user.id
        )
    return query.order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="このメールアドレスは既に登録されています")
    user = User(email=body.email, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, **body.profile.model_dump()))
    record_audit(db, current_user.id, "user.create", "user", user.id, {"role": body.role})
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return check_user_access(db, current_user, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    target = check_user_access(db, current_user, user_id)
    is_admin = current_user.role == "admin"
    is_self = current_user.id == user_id

    if not is_admin and not is_self:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="この操作を行う権限がありません")
    if not is_admin and (body.role is not None or body.is_active is not None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="ロール・有効状態の変更は管理者のみ可能です")
    if not is_admin and body.profile is not None and body.profile.assigned_staff_id is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="担当スタッフの変更は管理者のみ可能です")

    if body.email is not None and body.email != target.email:
        if db.query(User).filter(User.email == body.email).first():
            raise HTTPException(status.HTTP_409_CONFLICT, detail="このメールアドレスは既に登録されています")
        target.email = body.email
    if body.password is not None:
        target.password_hash = hash_password(body.password)
    if body.role is not None:
        target.role = body.role
    if body.is_active is not None:
        target.is_active = body.is_active
    if body.profile is not None:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if profile is None:
            profile = Profile(user_id=user_id, display_name=body.profile.display_name)
            db.add(profile)
        for key, value in body.profile.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)
    record_audit(db, current_user.id, "user.update", "user", user_id)
    db.commit()
    db.refresh(target)
    return target
