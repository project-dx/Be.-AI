from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import is_assigned_staff, require_staff_or_admin
from app.models import Profile, RiskAlert, User
from app.schemas.misc import RiskAlertOut
from app.services.audit import record_audit

router = APIRouter(prefix="/api/risk-alerts", tags=["リスクアラート"])


def _to_out(db: Session, alert: RiskAlert) -> RiskAlertOut:
    out = RiskAlertOut.model_validate(alert)
    profile = db.query(Profile).filter(Profile.user_id == alert.user_id).first()
    out.user_name = profile.display_name if profile else None
    return out


@router.get("", response_model=list[RiskAlertOut])
def list_alerts(
    alert_status: str | None = Query(default=None, alias="status", pattern="^(open|acknowledged)$"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> list[RiskAlertOut]:
    query = db.query(RiskAlert)
    if alert_status:
        query = query.filter(RiskAlert.status == alert_status)
    if current_user.role == "staff":
        assigned_ids = [
            p.user_id
            for p in db.query(Profile).filter(Profile.assigned_staff_id == current_user.id).all()
        ]
        query = query.filter(RiskAlert.user_id.in_(assigned_ids or [-1]))
    alerts = query.order_by(RiskAlert.created_at.desc()).limit(limit).all()
    return [_to_out(db, a) for a in alerts]


@router.post("/{alert_id}/acknowledge", response_model=RiskAlertOut)
def acknowledge(
    alert_id: int,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> RiskAlertOut:
    alert = db.get(RiskAlert, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="アラートが見つかりません")
    if current_user.role == "staff" and not is_assigned_staff(db, current_user, alert.user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="アラートが見つかりません")
    if alert.status == "acknowledged":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="このアラートは確認済みです")
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now(UTC)
    record_audit(db, current_user.id, "risk_alert.acknowledge", "risk_alert", alert.id)
    db.commit()
    db.refresh(alert)
    return _to_out(db, alert)
