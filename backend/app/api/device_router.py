from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.mysql import get_db
from ..database.models import Device
from ..api.user_router import get_current_user
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/devices", tags=["设备管理"])


class DeviceCreate(BaseModel):
    name: str
    model: str
    manufacturer: Optional[str] = None
    category: str
    location: Optional[str] = None
    installation_date: Optional[str] = None
    description: Optional[str] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class DeviceResponse(BaseModel):
    id: int
    name: str
    model: Optional[str]
    manufacturer: Optional[str]
    category: Optional[str]
    location: Optional[str]
    status: str
    installation_date: Optional[datetime]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=DeviceResponse)
async def create_device(
    device_data: DeviceCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    install_date = None
    if device_data.installation_date:
        try:
            install_date = datetime.strptime(device_data.installation_date, "%Y-%m-%d")
        except ValueError:
            install_date = datetime.utcnow()

    device = Device(
        name=device_data.name,
        model=device_data.model,
        manufacturer=device_data.manufacturer,
        category=device_data.category,
        location=device_data.location,
        installation_date=install_date or datetime.utcnow(),
        status="normal",
        description=device_data.description
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Device)
    if category:
        query = query.filter(Device.category == category)
    if status:
        query = query.filter(Device.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    update_data = device_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(device, key, value)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    db.delete(device)
    db.commit()
    return {"message": "设备删除成功"}


@router.get("/stats/summary")
async def get_device_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total = db.query(Device).count()
    normal = db.query(Device).filter(Device.status == "normal").count()
    warning = db.query(Device).filter(Device.status == "warning").count()
    fault = db.query(Device).filter(Device.status == "fault").count()

    categories = db.query(Device.category).distinct().all()

    return {
        "total": total,
        "normal": normal,
        "warning": warning,
        "fault": fault,
        "categories": [cat[0] for cat in categories if cat[0]]
    }
