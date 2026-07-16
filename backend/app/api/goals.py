from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user
from app.models import Goal, User
from app.schemas.misc import GoalCreate, GoalOut, GoalUpdate
from app.services.audit import record_audit

router = APIRouter(tags=["目標"])


@router.get("/api/users/{user_id}/goals", response_model=list[GoalOut])
def list_goals(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Goal]:
    check_user_access(db, current_user, user_id)
    return db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.created_at.desc()).all()


@router.post("/api/users/{user_id}/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    user_id: int,
    body: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Goal:
    check_user_access(db, current_user, user_id)
    goal = Goal(user_id=user_id, **body.model_dump())
    db.add(goal)
    db.flush()
    record_audit(db, current_user.id, "goal.create", "goal", goal.id)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/api/goals/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: int,
    body: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Goal:
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="目標が見つかりません")
    check_user_access(db, current_user, goal.user_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(goal, key, value)
    record_audit(db, current_user.id, "goal.update", "goal", goal.id)
    db.commit()
    db.refresh(goal)
    return goal
