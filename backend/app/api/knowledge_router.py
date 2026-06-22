from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database.mysql import get_db
from ..services.knowledge_service import KnowledgeService
from ..api.user_router import get_current_user
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])

UPLOAD_DIR = "uploads/knowledge"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class DocumentResponse(BaseModel):
    id: int
    title: str
    file_type: str
    chunk_count: int
    status: str
    error_message: Optional[str]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.txt', '.pdf', '.doc', '.docx']:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    if not title:
        title = os.path.splitext(file.filename)[0]

    knowledge_service = KnowledgeService(db)
    try:
        doc = await knowledge_service.upload_document(
            title=title,
            file_path=file_path,
            file_type=file_ext,
            uploaded_by=current_user.id
        )
        return doc
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    knowledge_service = KnowledgeService(db)
    documents = knowledge_service.get_documents(skip=skip, limit=limit)
    return {
        "documents": documents,
        "total": len(documents)
    }


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    knowledge_service = KnowledgeService(db)
    doc = knowledge_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    knowledge_service = KnowledgeService(db)
    success = await knowledge_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"message": "文档删除成功"}


@router.post("/documents/{doc_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    doc_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    knowledge_service = KnowledgeService(db)
    doc = await knowledge_service.reprocess_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@router.get("/search")
async def search_documents(
    query: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    knowledge_service = KnowledgeService(db)
    documents = knowledge_service.search_documents(query)
    return {"documents": documents, "total": len(documents)}
