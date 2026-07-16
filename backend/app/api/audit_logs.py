from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models import AuditLog, User
from app.schemas.misc import AuditLogOut

router = APIRouter(prefix="/api/audit-logs", tags=["監査ログ"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    actor: int | None = None,
    action: str | None = None,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AuditLogOut]:
    query = db.query(AuditLog)
    if actor is not None:
        query = query.filter(AuditLog.actor_user_id == actor)
    if action:
        query = query.filter(AuditLog.action.like(f"%{action}%"))
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from.isoformat())
    if date_to:
        query = query.filter(AuditLog.created_at <= f"{date_to.isoformat()} 23:59:59")
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    actor_ids = {log.actor_user_id for log in logs if log.actor_user_id is not None}
    emails = {
        u.id: u.email for u in db.query(User).filter(User.id.in_(actor_ids or [-1])).all()
    }
    results = []
    for log in logs:
        out = AuditLogOut.model_validate(log)
        out.actor_email = emails.get(log.actor_user_id)
        results.append(out)
    return results
