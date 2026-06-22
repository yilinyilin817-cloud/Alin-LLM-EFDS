from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.mysql import get_db
from ..database.models import MaintenanceRecord, Device
from ..api.user_router import get_current_user
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/maintenance", tags=["维护记录"])


class MaintenanceCreate(BaseModel):
    device_id: int
    maintenance_type: str
    title: str
    content: Optional[str] = None
    technician: Optional[str] = None
    cost: Optional[float] = 0
    parts_replaced: Optional[str] = None
    next_maintenance_date: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    maintenance_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    technician: Optional[str] = None
    cost: Optional[float] = None
    parts_replaced: Optional[str] = None
    next_maintenance_date: Optional[str] = None
    status: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: int
    device_id: int
    maintenance_type: str
    title: str
    content: Optional[str]
    technician: Optional[str]
    cost: float
    parts_replaced: Optional[str]
    next_maintenance_date: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=MaintenanceResponse)
async def create_maintenance(
    data: MaintenanceCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == data.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    next_date = None
    if data.next_maintenance_date:
        try:
            next_date = datetime.strptime(data.next_maintenance_date, "%Y-%m-%d")
        except ValueError:
            pass

    record = MaintenanceRecord(
        device_id=data.device_id,
        maintenance_type=data.maintenance_type,
        title=data.title,
        content=data.content,
        technician=data.technician,
        cost=data.cost or 0,
        parts_replaced=data.parts_replaced,
        next_maintenance_date=next_date,
        status="completed"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/device/{device_id}", response_model=List[MaintenanceResponse])
async def get_device_maintenance(
    device_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return db.query(MaintenanceRecord).filter(
        MaintenanceRecord.device_id == device_id
    ).order_by(MaintenanceRecord.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{record_id}", response_model=MaintenanceResponse)
async def get_maintenance(
    record_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="维护记录不存在")
    return record


@router.put("/{record_id}", response_model=MaintenanceResponse)
async def update_maintenance(
    record_id: int,
    data: MaintenanceUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="维护记录不存在")

    update_data = data.dict(exclude_unset=True)

    if "next_maintenance_date" in update_data and update_data["next_maintenance_date"]:
        try:
            update_data["next_maintenance_date"] = datetime.strptime(
                update_data["next_maintenance_date"], "%Y-%m-%d"
            )
        except ValueError:
            del update_data["next_maintenance_date"]

    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}")
async def delete_maintenance(
    record_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="维护记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "维护记录删除成功"}


@router.get("/stats/summary")
async def get_maintenance_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total = db.query(MaintenanceRecord).count()
    this_month = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.created_at >= datetime.utcnow().replace(day=1)
    ).count()
    pending = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.status == "pending"
    ).count()

    return {
        "total": total,
        "this_month": this_month,
        "pending": pending
    }
