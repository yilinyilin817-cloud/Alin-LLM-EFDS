from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from ..database.mysql import get_db
from ..database.models import Base
from ..api.user_router import get_current_user
from ..services.config_service import get_config_service
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["系统管理"])
config_service = get_config_service()


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(String(255))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    username = Column(String(50))
    action = Column(String(255), nullable=False)
    detail = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class SettingsUpdate(BaseModel):
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    rag_top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


def get_default_settings() -> Dict[str, Any]:
    return {
        "llm_model": "gpt-3.5-turbo",
        "embedding_model": "shibing624/text2vec-base-chinese",
        "rag_top_k": 5,
        "similarity_threshold": 0.7,
        "max_tokens": 2048,
        "temperature": 0.7,
    }


@router.get("/settings")
async def get_settings(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    settings = db.query(SystemSettings).all()
    result = get_default_settings()

    for setting in settings:
        if setting.key in result:
            try:
                if isinstance(result[setting.key], int):
                    result[setting.key] = int(setting.value)
                elif isinstance(result[setting.key], float):
                    result[setting.key] = float(setting.value)
                else:
                    result[setting.key] = setting.value
            except (ValueError, TypeError):
                pass

    return result


@router.put("/settings")
async def update_settings(
    settings_data: SettingsUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    settings_dict = settings_data.dict(exclude_none=True)

    for key, value in settings_dict.items():
        existing = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if existing:
            existing.value = str(value)
        else:
            new_setting = SystemSettings(key=key, value=str(value))
            db.add(new_setting)

    log_operation(db, current_user.id, current_user.username, "更新系统设置", str(settings_dict))
    db.commit()

    config_service.reload()

    return {"message": "设置已更新"}


@router.get("/logs")
async def get_logs(
    skip: int = 0,
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    logs = db.query(OperationLog).order_by(OperationLog.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "user": log.username,
            "action": log.action,
            "detail": log.detail,
            "ip": log.ip_address,
            "time": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
        }
        for log in logs
    ]


def log_operation(db: Session, user_id: int, username: str, action: str, detail: str = None, ip: str = None):
    log = OperationLog(
        user_id=user_id,
        username=username,
        action=action,
        detail=detail,
        ip_address=ip or "127.0.0.1",
    )
    db.add(log)
