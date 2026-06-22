from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.mysql import get_db
from ..services.diagnosis_service import DiagnosisService
from ..api.user_router import get_current_user
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/diagnosis", tags=["故障诊断"])


class DiagnosisRequest(BaseModel):
    fault_phenomenon: str
    device_id: Optional[int] = None


class DiagnosisResponse(BaseModel):
    possible_causes: List[str]
    repair_suggestions: List[str]
    preventive_measures: List[str]
    severity: str
    similar_cases: List[dict]


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: int
    response: str


class FaultCaseResponse(BaseModel):
    id: int
    device_id: Optional[int]
    fault_type: str
    fault_phenomenon: str
    fault_reason: Optional[str]
    solution: Optional[str]
    severity: Optional[str]
    status: str

    class Config:
        from_attributes = True


@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose_fault(
    request: DiagnosisRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    diagnosis_service = DiagnosisService(db)
    try:
        result = await diagnosis_service.diagnose(
            user_id=current_user.id,
            fault_phenomenon=request.fault_phenomenon,
            device_id=request.device_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    diagnosis_service = DiagnosisService(db)
    try:
        result = await diagnosis_service.chat(
            user_id=current_user.id,
            query=request.query,
            conversation_id=request.conversation_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


@router.get("/cases", response_model=List[FaultCaseResponse])
async def get_fault_cases(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    diagnosis_service = DiagnosisService(db)
    return diagnosis_service.get_fault_cases(skip=skip, limit=limit)


@router.get("/cases/{case_id}", response_model=FaultCaseResponse)
async def get_fault_case(
    case_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    diagnosis_service = DiagnosisService(db)
    case = diagnosis_service.get_fault_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    return case


@router.put("/cases/{case_id}", response_model=FaultCaseResponse)
async def update_fault_case(
    case_id: int,
    status: Optional[str] = None,
    solution: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    diagnosis_service = DiagnosisService(db)
    update_data = {}
    if status:
        update_data["status"] = status
    if solution:
        update_data["solution"] = solution

    case = diagnosis_service.update_fault_case(case_id, **update_data)
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    return case
