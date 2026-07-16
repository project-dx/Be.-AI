from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user, require_staff_or_admin
from app.models import ScoreResult, User
from app.schemas.misc import ScoreResultOut
from app.services.audit import record_audit
from app.services.scoring import recalculate_range

router = APIRouter(prefix="/api/users/{user_id}/scores", tags=["スコア"])


class RecalculateRequest(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    days: int = Field(default=30, ge=1, le=366)


@router.get("", response_model=list[ScoreResultOut])
def list_scores(
    user_id: int,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ScoreResult]:
    check_user_access(db, current_user, user_id)
    query = db.query(ScoreResult).filter(ScoreResult.user_id == user_id)
    if date_from:
        query = query.filter(ScoreResult.score_date >= date_from)
    if date_to:
        query = query.filter(ScoreResult.score_date <= date_to)
    return query.order_by(ScoreResult.score_date).all()


@router.post("/recalculate")
def recalculate(
    user_id: int,
    body: RecalculateRequest,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    check_user_access(db, current_user, user_id)
    date_to = body.date_to or date.today()
    date_from = body.date_from or (date_to - timedelta(days=body.days - 1))
    count = recalculate_range(db, user_id, date_from, date_to)
    record_audit(db, current_user.id, "score.recalculate", "user", user_id,
                 {"from": date_from.isoformat(), "to": date_to.isoformat(), "calculated_days": count})
    db.commit()
    return {"calculated_days": count, "from": date_from.isoformat(), "to": date_to.isoformat()}
