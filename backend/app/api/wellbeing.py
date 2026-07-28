from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user
from app.models import User, WellbeingCardSelection
from app.schemas.wellbeing import WellbeingCardOut, WellbeingSelectionCreate, WellbeingSelectionOut
from app.services.audit import record_audit
from app.services.wellbeing_cards import CARDS

router = APIRouter(prefix="/api", tags=["ウェルビーイングカード"])


@router.get("/wellbeing-cards", response_model=list[WellbeingCardOut])
def list_cards(_: User = Depends(get_current_user)) -> list[WellbeingCardOut]:
    return [WellbeingCardOut(**c) for c in CARDS]


@router.get("/users/{user_id}/wellbeing-selections", response_model=list[WellbeingSelectionOut])
def list_selections(
    user_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WellbeingSelectionOut]:
    check_user_access(db, current_user, user_id)
    rows = (
        db.query(WellbeingCardSelection)
        .filter(WellbeingCardSelection.user_id == user_id)
        .order_by(WellbeingCardSelection.selection_date.desc())
        .limit(limit)
        .all()
    )
    return [WellbeingSelectionOut.model_validate(r) for r in rows]


@router.post(
    "/users/{user_id}/wellbeing-selections",
    response_model=WellbeingSelectionOut,
    status_code=status.HTTP_201_CREATED,
)
def save_selection(
    user_id: int,
    body: WellbeingSelectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WellbeingSelectionOut:
    check_user_access(db, current_user, user_id)
    selection_date = body.selection_date or date.today()

    existing = (
        db.query(WellbeingCardSelection)
        .filter(
            WellbeingCardSelection.user_id == user_id,
            WellbeingCardSelection.selection_date == selection_date,
        )
        .first()
    )
    if existing:
        # 同じ日の選び直しは上書き
        existing.card_ids = body.card_ids
        existing.note = body.note
        selection = existing
        action = "wellbeing_selection.update"
    else:
        selection = WellbeingCardSelection(
            user_id=user_id,
            selection_date=selection_date,
            card_ids=body.card_ids,
            note=body.note,
        )
        db.add(selection)
        action = "wellbeing_selection.create"

    db.flush()
    record_audit(db, current_user.id, action, "wellbeing_selection", selection.id,
                 {"target_user_id": user_id, "date": selection_date.isoformat()})
    db.commit()
    db.refresh(selection)
    return WellbeingSelectionOut.model_validate(selection)
