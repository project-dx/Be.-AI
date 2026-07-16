from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models import SystemSetting, User
from app.schemas.misc import ScoringWeightsUpdate
from app.services.audit import record_audit
from app.services.scoring import DEFAULT_WEIGHTS, get_weights

router = APIRouter(prefix="/api/settings", tags=["システム設定"])


@router.get("/scoring-weights")
def get_scoring_weights(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return {"weights": get_weights(db), "defaults": DEFAULT_WEIGHTS}


@router.put("/scoring-weights")
def update_scoring_weights(
    body: ScoringWeightsUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    # 妥当性検証: 既知のグループ・キー・数値のみ許可
    for group, values in body.weights.items():
        if group not in DEFAULT_WEIGHTS or not isinstance(values, dict):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"不明な設定グループです: {group}")
        for key, value in values.items():
            if key not in DEFAULT_WEIGHTS[group]:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"不明な設定項目です: {group}.{key}")
            if not isinstance(value, (int, float)) or value < 0 or value > 100:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"配点は0〜100の数値で指定してください: {group}.{key}")

    row = db.query(SystemSetting).filter(SystemSetting.setting_key == "scoring_weights").first()
    if row is None:
        row = SystemSetting(setting_key="scoring_weights", setting_value_json=body.weights)
        db.add(row)
    else:
        row.setting_value_json = body.weights
    row.updated_by = current_user.id
    record_audit(db, current_user.id, "settings.update_scoring_weights", "system_setting", None)
    db.commit()
    return {"weights": get_weights(db)}
