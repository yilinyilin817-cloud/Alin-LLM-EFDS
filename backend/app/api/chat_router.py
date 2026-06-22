from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database.mysql import get_db
from ..database.models import Conversation, Message, ModelProvider, ProviderType
from ..services.diagnosis_service import DiagnosisService
from ..services.llm_service import get_llm_service
from ..services.rag_service import get_rag_service
from ..api.user_router import get_current_user
from pydantic import BaseModel
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["智能问答"])


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    model_provider_id: Optional[int] = None


class MessageCreate(BaseModel):
    content: str
    use_knowledge: bool = True
    model_provider_id: Optional[int] = None


class ConversationResponse(BaseModel):
    id: int
    title: str
    model_provider_id: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    metadata: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


def _get_provider_config(db: Session, provider_id: Optional[int] = None) -> dict:
    if provider_id:
        provider = db.query(ModelProvider).filter(
            ModelProvider.id == provider_id,
            ModelProvider.is_active == True,
        ).first()
    else:
        provider = db.query(ModelProvider).filter(
            ModelProvider.is_default == True,
            ModelProvider.is_active == True,
        ).first()

    if not provider:
        return {}

    return {
        "api_base": provider.api_base,
        "api_key": provider.api_key,
        "model_name": provider.model_name,
        "temperature": provider.temperature,
        "max_tokens": provider.max_tokens,
    }


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()

    return [
        {
            "id": c.id,
            "title": c.title or "新对话",
            "model_provider_id": getattr(c, "model_provider_id", None),
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "updated_at": c.updated_at.isoformat() if c.updated_at else "",
        }
        for c in conversations
    ]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title or "新对话",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model_provider_id": data.model_provider_id,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else "",
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else "",
    }


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "metadata": m.metadata,
            "created_at": m.created_at.isoformat() if m.created_at else "",
        }
        for m in messages
    ]


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")

    if not conversation.title or conversation.title == "新对话":
        conversation.title = data.content[:50]
        db.commit()

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=data.content,
    )
    db.add(user_message)
    db.commit()

    conversation_history = []
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc()).limit(10).all()

    for msg in reversed(messages):
        conversation_history.append({
            "role": msg.role,
            "content": msg.content,
        })

    knowledge_context = ""
    knowledge_refs = []
    if data.use_knowledge:
        try:
            rag_service = get_rag_service()
            results = await rag_service.retrieve(data.content)
            if results:
                context_parts = []
                for i, result in enumerate(results, 1):
                    context_parts.append(f"[参考{i}] {result['content']}")
                    knowledge_refs.append({
                        "index": i,
                        "content": result["content"][:200],
                        "score": round(result.get("score", 0), 4),
                        "document_id": result.get("document_id"),
                    })
                knowledge_context = "\n\n".join(context_parts)
        except Exception as e:
            logger.warning(f"Knowledge retrieval failed: {e}")

    provider_config = _get_provider_config(db, data.model_provider_id)

    llm_service = get_llm_service()
    response = await llm_service.generate_response(
        query=data.content,
        context=knowledge_context,
        conversation_history=conversation_history,
        provider_config=provider_config if provider_config else None,
    )

    meta = {}
    if knowledge_refs:
        meta["knowledge_refs"] = knowledge_refs

    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=response,
        metadata=json.dumps(meta, ensure_ascii=False) if meta else None,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "id": assistant_message.id,
        "role": "assistant",
        "content": response,
        "metadata": meta,
        "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else "",
    }


@router.post("/conversations/{conversation_id}/stream")
async def stream_message(
    conversation_id: int,
    data: MessageCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")

    if not conversation.title or conversation.title == "新对话":
        conversation.title = data.content[:50]
        db.commit()

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=data.content,
    )
    db.add(user_message)
    db.commit()

    conversation_history = []
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc()).limit(10).all()

    for msg in reversed(messages):
        conversation_history.append({
            "role": msg.role,
            "content": msg.content,
        })

    knowledge_context = ""
    knowledge_refs = []
    if data.use_knowledge:
        try:
            rag_service = get_rag_service()
            results = await rag_service.retrieve(data.content)
            if results:
                context_parts = []
                for i, result in enumerate(results, 1):
                    context_parts.append(f"[参考{i}] {result['content']}")
                    knowledge_refs.append({
                        "index": i,
                        "content": result["content"][:200],
                        "score": round(result.get("score", 0), 4),
                        "document_id": result.get("document_id"),
                    })
                knowledge_context = "\n\n".join(context_parts)
        except Exception as e:
            logger.warning(f"Knowledge retrieval failed: {e}")

    provider_config = _get_provider_config(db, data.model_provider_id)
    llm_service = get_llm_service()

    async def event_generator():
        full_response = ""

        if knowledge_refs:
            refs_data = json.dumps({"type": "knowledge_refs", "refs": knowledge_refs}, ensure_ascii=False)
            yield f"data: {refs_data}\n\n"

        async for chunk in llm_service.generate_response_stream(
            query=data.content,
            context=knowledge_context,
            conversation_history=conversation_history,
            provider_config=provider_config if provider_config else None,
        ):
            full_response += chunk
            chunk_data = json.dumps({"type": "content", "content": chunk}, ensure_ascii=False)
            yield f"data: {chunk_data}\n\n"

        meta = {}
        if knowledge_refs:
            meta["knowledge_refs"] = knowledge_refs

        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
            metadata=json.dumps(meta, ensure_ascii=False) if meta else None,
        )
        db.add(assistant_message)
        db.commit()

        done_data = json.dumps({"type": "done", "message_id": assistant_message.id}, ensure_ascii=False)
        yield f"data: {done_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")

    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.delete(conversation)
    db.commit()

    return {"message": "对话删除成功"}


@router.put("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    data: ConversationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")

    if data.title:
        conversation.title = data.title
        db.commit()

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else "",
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else "",
    }
