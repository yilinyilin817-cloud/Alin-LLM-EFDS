from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database.mysql import get_db
from ..database.models import IssueReport, WorkProgress, Device
from ..api.user_router import get_current_user
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/issues", tags=["问题上报"])


class IssueCreate(BaseModel):
    device_id: Optional[int] = None
    title: str
    description: str
    issue_type: str
    severity: Optional[str] = "medium"
    priority: Optional[str] = "normal"
    reporter_name: str
    reporter_department: Optional[str] = None
    assignee_name: Optional[str] = None
    assignee_department: Optional[str] = None
    location: Optional[str] = None
    due_date: Optional[str] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee_name: Optional[str] = None
    assignee_department: Optional[str] = None
    location: Optional[str] = None
    progress_percent: Optional[int] = None
    due_date: Optional[str] = None


class ProgressCreate(BaseModel):
    user_name: str
    user_department: Optional[str] = None
    progress_note: str
    progress_percent: Optional[int] = None
    status: Optional[str] = None
    action_taken: Optional[str] = None
    hours_spent: Optional[float] = 0


class ProgressResponse(BaseModel):
    id: int
    issue_id: int
    user_name: str
    user_department: Optional[str]
    progress_note: str
    progress_percent: Optional[int]
    status: Optional[str]
    action_taken: Optional[str]
    hours_spent: float
    created_at: datetime

    class Config:
        from_attributes = True


class IssueResponse(BaseModel):
    id: int
    device_id: Optional[int]
    title: str
    description: str
    issue_type: str
    severity: str
    priority: str
    status: str
    reporter_name: str
    reporter_department: Optional[str]
    assignee_name: Optional[str]
    assignee_department: Optional[str]
    location: Optional[str]
    attachment_url: Optional[str]
    progress_percent: int
    due_date: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    progress_logs: List[ProgressResponse] = []

    class Config:
        from_attributes = True


class IssueListResponse(BaseModel):
    id: int
    device_id: Optional[int]
    title: str
    issue_type: str
    severity: str
    priority: str
    status: str
    reporter_name: str
    reporter_department: Optional[str]
    assignee_name: Optional[str]
    assignee_department: Optional[str]
    progress_percent: int
    due_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentStats(BaseModel):
    department: str
    total: int
    open: int
    in_progress: int
    resolved: int
    avg_progress: float


@router.post("/", response_model=IssueResponse)
async def create_issue(
    data: IssueCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.device_id:
        device = db.query(Device).filter(Device.id == data.device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")

    due_date = None
    if data.due_date:
        try:
            due_date = datetime.strptime(data.due_date, "%Y-%m-%d")
        except ValueError:
            pass

    issue = IssueReport(
        device_id=data.device_id,
        title=data.title,
        description=data.description,
        issue_type=data.issue_type,
        severity=data.severity,
        priority=data.priority,
        status="open",
        reporter_name=data.reporter_name,
        reporter_department=data.reporter_department,
        assignee_name=data.assignee_name,
        assignee_department=data.assignee_department,
        location=data.location,
        due_date=due_date,
        progress_percent=0
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


@router.get("/", response_model=List[IssueListResponse])
async def get_issues(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    department: Optional[str] = None,
    assignee_department: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(IssueReport)
    if status:
        query = query.filter(IssueReport.status == status)
    if severity:
        query = query.filter(IssueReport.severity == severity)
    if department:
        query = query.filter(
            (IssueReport.reporter_department == department) |
            (IssueReport.assignee_department == department)
        )
    if assignee_department:
        query = query.filter(IssueReport.assignee_department == assignee_department)
    return query.order_by(IssueReport.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/departments", response_model=List[str])
async def get_departments(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reporter_depts = db.query(IssueReport.reporter_department).distinct().all()
    assignee_depts = db.query(IssueReport.assignee_department).distinct().all()
    all_depts = set()
    for dept in reporter_depts:
        if dept[0]:
            all_depts.add(dept[0])
    for dept in assignee_depts:
        if dept[0]:
            all_depts.add(dept[0])
    return sorted(list(all_depts))


@router.get("/department-stats", response_model=List[DepartmentStats])
async def get_department_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    departments = set()
    reporter_depts = db.query(IssueReport.reporter_department).distinct().all()
    assignee_depts = db.query(IssueReport.assignee_department).distinct().all()
    for dept in reporter_depts:
        if dept[0]:
            departments.add(dept[0])
    for dept in assignee_depts:
        if dept[0]:
            departments.add(dept[0])

    stats = []
    for dept in departments:
        total = db.query(IssueReport).filter(
            (IssueReport.reporter_department == dept) |
            (IssueReport.assignee_department == dept)
        ).count()
        open_count = db.query(IssueReport).filter(
            ((IssueReport.reporter_department == dept) | (IssueReport.assignee_department == dept)),
            IssueReport.status == "open"
        ).count()
        in_progress = db.query(IssueReport).filter(
            ((IssueReport.reporter_department == dept) | (IssueReport.assignee_department == dept)),
            IssueReport.status == "in_progress"
        ).count()
        resolved = db.query(IssueReport).filter(
            ((IssueReport.reporter_department == dept) | (IssueReport.assignee_department == dept)),
            IssueReport.status == "resolved"
        ).count()
        avg_progress = db.query(func.avg(IssueReport.progress_percent)).filter(
            (IssueReport.reporter_department == dept) |
            (IssueReport.assignee_department == dept)
        ).scalar() or 0

        stats.append(DepartmentStats(
            department=dept,
            total=total,
            open=open_count,
            in_progress=in_progress,
            resolved=resolved,
            avg_progress=round(float(avg_progress), 1)
        ))

    return sorted(stats, key=lambda x: x.total, reverse=True)


@router.get("/by-department")
async def get_issues_by_department(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    departments = set()
    assignee_depts = db.query(IssueReport.assignee_department).distinct().all()
    for dept in assignee_depts:
        if dept[0]:
            departments.add(dept[0])

    result = {}
    for dept in departments:
        issues = db.query(IssueReport).filter(
            IssueReport.assignee_department == dept
        ).order_by(IssueReport.created_at.desc()).all()
        result[dept] = [
            {
                "id": i.id,
                "title": i.title,
                "status": i.status,
                "severity": i.severity,
                "progress_percent": i.progress_percent,
                "assignee_name": i.assignee_name,
                "created_at": i.created_at.isoformat() if i.created_at else None
            }
            for i in issues
        ]

    unassigned = db.query(IssueReport).filter(
        IssueReport.assignee_department.is_(None)
    ).order_by(IssueReport.created_at.desc()).all()
    if unassigned:
        result["未分配部门"] = [
            {
                "id": i.id,
                "title": i.title,
                "status": i.status,
                "severity": i.severity,
                "progress_percent": i.progress_percent,
                "assignee_name": i.assignee_name,
                "created_at": i.created_at.isoformat() if i.created_at else None
            }
            for i in unassigned
        ]

    return result


@router.get("/device/{device_id}", response_model=List[IssueListResponse])
async def get_device_issues(
    device_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(IssueReport).filter(
        IssueReport.device_id == device_id
    ).order_by(IssueReport.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题工单不存在")
    return issue


@router.put("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    data: IssueUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题工单不存在")

    update_data = data.dict(exclude_unset=True)

    if "due_date" in update_data and update_data["due_date"]:
        try:
            update_data["due_date"] = datetime.strptime(update_data["due_date"], "%Y-%m-%d")
        except ValueError:
            del update_data["due_date"]

    for key, value in update_data.items():
        setattr(issue, key, value)

    if data.status == "resolved" and not issue.resolved_at:
        issue.resolved_at = datetime.utcnow()
        issue.progress_percent = 100

    db.commit()
    db.refresh(issue)
    return issue


@router.delete("/{issue_id}")
async def delete_issue(
    issue_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题工单不存在")
    db.delete(issue)
    db.commit()
    return {"message": "问题工单删除成功"}


@router.post("/{issue_id}/progress", response_model=ProgressResponse)
async def add_progress(
    issue_id: int,
    data: ProgressCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题工单不存在")

    progress = WorkProgress(
        issue_id=issue_id,
        user_name=data.user_name,
        user_department=data.user_department,
        progress_note=data.progress_note,
        progress_percent=data.progress_percent,
        status=data.status,
        action_taken=data.action_taken,
        hours_spent=data.hours_spent or 0
    )
    db.add(progress)

    if data.progress_percent is not None:
        issue.progress_percent = data.progress_percent
    if data.status:
        issue.status = data.status
        if data.status == "resolved":
            issue.resolved_at = datetime.utcnow()
            issue.progress_percent = 100

    db.commit()
    db.refresh(progress)
    return progress


@router.get("/{issue_id}/progress", response_model=List[ProgressResponse])
async def get_progress_logs(
    issue_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题工单不存在")
    return db.query(WorkProgress).filter(
        WorkProgress.issue_id == issue_id
    ).order_by(WorkProgress.created_at.desc()).all()


@router.get("/stats/summary")
async def get_issue_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total = db.query(IssueReport).count()
    open_count = db.query(IssueReport).filter(IssueReport.status == "open").count()
    in_progress = db.query(IssueReport).filter(IssueReport.status == "in_progress").count()
    resolved = db.query(IssueReport).filter(IssueReport.status == "resolved").count()
    critical = db.query(IssueReport).filter(
        IssueReport.severity == "critical",
        IssueReport.status != "resolved"
    ).count()
    overdue = db.query(IssueReport).filter(
        IssueReport.due_date < datetime.utcnow(),
        IssueReport.status != "resolved"
    ).count()

    total_hours = db.query(func.sum(WorkProgress.hours_spent)).scalar() or 0

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "critical": critical,
        "overdue": overdue,
        "total_hours_spent": round(float(total_hours), 1)
    }
