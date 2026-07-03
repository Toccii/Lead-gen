from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.jobs.schedule import get_system_settings
from app.schemas.system_settings import SystemSettingsRead, SystemSettingsUpdate

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


@router.get("", response_model=SystemSettingsRead)
def read_system_settings(db: Session = Depends(get_db)) -> SystemSettingsRead:
    return get_system_settings(db)


@router.put("", response_model=SystemSettingsRead)
def update_system_settings(payload: SystemSettingsUpdate, db: Session = Depends(get_db)) -> SystemSettingsRead:
    settings_row = get_system_settings(db)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings_row, field_name, value)
    db.commit()
    db.refresh(settings_row)
    return settings_row
