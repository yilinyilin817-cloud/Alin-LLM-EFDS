from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import json
from datetime import datetime

app = FastAPI(title="LLM-EFDS", version="1.0.0", description="基于大模型的设备故障诊断系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads/knowledge"
os.makedirs(UPLOAD_DIR, exist_ok=True)

documents_db = []
devices_db = []
conversations_db = []


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class DocumentContent(BaseModel):
    content: str


@app.get("/")
async def root():
    return {"name": "LLM-EFDS", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/users/login")
async def login(username: str = "admin", password: str = "admin"):
    return {"access_token": "demo-token-12345", "token_type": "bearer"}


@app.post("/api/users/register")
async def register(username: str, email: str, password: str):
    return {"id": 1, "username": username, "email": email, "is_active": True, "role": "user"}


@app.get("/api/knowledge/documents")
async def get_documents(skip: int = 0, limit: int = 100):
    return {"documents": documents_db[skip:skip+limit], "total": len(documents_db)}


@app.post("/api/knowledge/upload")
async def upload_document(file: UploadFile = File(...), title: Optional[str] = None):
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = ['.txt', '.pdf', '.doc', '.docx', '.xlsx', '.xls', '.csv', '.md']

    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_ext}")

    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    text_content = ""
    if file_ext in ['.txt', '.csv', '.md']:
        try:
            text_content = content.decode('utf-8')
        except:
            text_content = content.decode('gbk', errors='ignore')

    doc_id = len(documents_db) + 1
    doc = {
        "id": doc_id,
        "title": title or os.path.splitext(file.filename)[0],
        "file_path": file_path,
        "file_type": file_ext,
        "content": text_content,
        "chunk_count": max(1, len(content) // 500),
        "status": "completed",
        "error_message": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    documents_db.append(doc)
    return doc


@app.get("/api/knowledge/documents/{doc_id}")
async def get_document(doc_id: int):
    for doc in documents_db:
        if doc["id"] == doc_id:
            return doc
    raise HTTPException(status_code=404, detail="文档不存在")


@app.get("/api/knowledge/documents/{doc_id}/content")
async def get_document_content(doc_id: int):
    for doc in documents_db:
        if doc["id"] == doc_id:
            content = doc.get("content", "")
            if not content and doc.get("file_path") and os.path.exists(doc["file_path"]):
                try:
                    with open(doc["file_path"], "r", encoding="utf-8") as f:
                        content = f.read()
                except:
                    try:
                        with open(doc["file_path"], "r", encoding="gbk") as f:
                            content = f.read()
                    except:
                        content = "[无法读取文件内容]"
            return {"id": doc_id, "content": content, "title": doc["title"]}
    raise HTTPException(status_code=404, detail="文档不存在")


@app.put("/api/knowledge/documents/{doc_id}/content")
async def update_document_content(doc_id: int, data: DocumentContent):
    for doc in documents_db:
        if doc["id"] == doc_id:
            doc["content"] = data.content
            doc["updated_at"] = datetime.now().isoformat()

            if doc.get("file_path") and os.path.exists(doc["file_path"]):
                try:
                    with open(doc["file_path"], "w", encoding="utf-8") as f:
                        f.write(data.content)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")

            doc["chunk_count"] = max(1, len(data.content) // 500)
            return doc
    raise HTTPException(status_code=404, detail="文档不存在")


@app.put("/api/knowledge/documents/{doc_id}")
async def update_document(doc_id: int, data: DocumentUpdate):
    for doc in documents_db:
        if doc["id"] == doc_id:
            if data.title is not None:
                doc["title"] = data.title
            if data.content is not None:
                doc["content"] = data.content
                doc["chunk_count"] = max(1, len(data.content) // 500)
            doc["updated_at"] = datetime.now().isoformat()
            return doc
    raise HTTPException(status_code=404, detail="文档不存在")


@app.delete("/api/knowledge/documents/{doc_id}")
async def delete_document(doc_id: int):
    global documents_db
    doc_to_delete = None
    for doc in documents_db:
        if doc["id"] == doc_id:
            doc_to_delete = doc
            break

    if doc_to_delete:
        if doc_to_delete.get("file_path") and os.path.exists(doc_to_delete["file_path"]):
            try:
                os.remove(doc_to_delete["file_path"])
            except:
                pass
        documents_db = [d for d in documents_db if d["id"] != doc_id]
        return {"message": "文档删除成功"}

    raise HTTPException(status_code=404, detail="文档不存在")


@app.post("/api/knowledge/documents/{doc_id}/reprocess")
async def reprocess_document(doc_id: int):
    for doc in documents_db:
        if doc["id"] == doc_id:
            doc["status"] = "processing"
            doc["updated_at"] = datetime.now().isoformat()
            return doc
    raise HTTPException(status_code=404, detail="文档不存在")


@app.get("/api/knowledge/search")
async def search_documents(query: str):
    results = []
    for doc in documents_db:
        if query.lower() in doc["title"].lower() or query.lower() in doc.get("content", "").lower():
            content_preview = doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
            results.append({
                "document_id": doc["id"],
                "content": content_preview,
                "score": 0.85 + (hash(query) % 15) / 100,
            })
    return {"documents": results}


@app.post("/api/diagnosis/diagnose")
async def diagnose_fault(fault_phenomenon: str, device_id: Optional[int] = None):
    return {
        "possible_causes": [
            "轴承磨损或损坏",
            "转子不平衡",
            "润滑不足或润滑脂变质",
            "电机安装不当，地脚松动",
        ],
        "repair_suggestions": [
            "检查轴承状况，必要时更换轴承",
            "进行动平衡校正",
            "更换润滑脂，确保润滑充分",
            "检查并紧固地脚螺栓",
        ],
        "preventive_measures": [
            "建立定期巡检制度",
            "制定设备润滑保养计划",
            "安装振动监测传感器",
        ],
        "severity": "high",
        "similar_cases": [
            {"content": "某型号三相异步电机运行3个月后出现异常振动", "score": 0.92},
            {"content": "液压泵站电机温度异常升高，原因为润滑脂干涸", "score": 0.87},
        ],
    }


@app.post("/api/diagnosis/chat")
async def chat(query: str, conversation_id: Optional[int] = None):
    conv_id = conversation_id or len(conversations_db) + 1
    response = f"关于您的问题 '{query}'，这是一个专业的设备故障诊断问题。\n\n根据知识库分析，建议您：\n1. 首先检查设备的运行状态\n2. 查看相关传感器数据\n3. 参考历史故障案例"
    return {"conversation_id": conv_id, "response": response}


@app.get("/api/chat/conversations")
async def get_conversations():
    return []


@app.get("/api/devices/")
async def get_devices(skip: int = 0, limit: int = 100):
    return devices_db[skip:skip+limit]


@app.post("/api/devices/")
async def create_device(name: str, model: str, category: str, manufacturer: Optional[str] = None, location: Optional[str] = None, description: Optional[str] = None):
    device = {
        "id": len(devices_db) + 1,
        "name": name,
        "model": model,
        "manufacturer": manufacturer,
        "category": category,
        "location": location,
        "status": "normal",
        "installation_date": datetime.now().isoformat(),
        "description": description,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    devices_db.append(device)
    return device


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
