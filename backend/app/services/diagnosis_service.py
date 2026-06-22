from sqlalchemy.orm import Session
from ..database.models import FaultCase, Device, Conversation, Message, ModelProvider
from ..services.llm_service import get_llm_service
from ..services.rag_service import get_rag_service
from typing import List, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)


class DiagnosisService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = get_llm_service()
        self.rag_service = get_rag_service()

    def _get_provider_config(self, provider_id: Optional[int] = None) -> dict:
        if provider_id:
            provider = self.db.query(ModelProvider).filter(
                ModelProvider.id == provider_id,
                ModelProvider.is_active == True,
            ).first()
        else:
            provider = self.db.query(ModelProvider).filter(
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

    async def diagnose(
        self,
        user_id: int,
        fault_phenomenon: str,
        device_id: Optional[int] = None,
        model_provider_id: Optional[int] = None,
    ) -> Dict:
        device_info = None
        if device_id:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if device:
                device_info = {
                    "name": device.name,
                    "model": device.model,
                    "manufacturer": device.manufacturer,
                    "category": device.category,
                }

        knowledge_context = await self.rag_service.get_context(fault_phenomenon)

        provider_config = self._get_provider_config(model_provider_id)

        result = await self.llm_service.diagnose_fault(
            fault_phenomenon=fault_phenomenon,
            device_info=device_info,
            knowledge_context=knowledge_context,
            provider_config=provider_config if provider_config else None,
        )

        similar_cases = await self.find_similar_cases(fault_phenomenon)
        result["similar_cases"] = similar_cases

        case = FaultCase(
            device_id=device_id,
            fault_type="diagnosed",
            fault_phenomenon=fault_phenomenon,
            fault_reason=json.dumps(result.get("possible_causes", []), ensure_ascii=False),
            solution=json.dumps(result.get("repair_suggestions", []), ensure_ascii=False),
            severity=result.get("severity", "unknown"),
            status="diagnosed",
        )
        self.db.add(case)
        self.db.commit()

        return result

    async def find_similar_cases(self, fault_phenomenon: str, limit: int = 3) -> List[Dict]:
        results = await self.rag_service.retrieve(fault_phenomenon, top_k=limit)

        similar_cases = []
        for result in results:
            doc_id = result.get("document_id")
            if doc_id:
                similar_cases.append({
                    "content": result["content"],
                    "score": result["score"],
                    "document_id": doc_id,
                })

        return similar_cases

    async def chat(
        self,
        user_id: int,
        query: str,
        conversation_id: Optional[int] = None,
        model_provider_id: Optional[int] = None,
    ) -> Dict:
        if not conversation_id:
            conversation = Conversation(
                user_id=user_id,
                title=query[:50],
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            conversation_id = conversation.id

        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=query,
        )
        self.db.add(user_message)
        self.db.commit()

        conversation_history = []
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(10).all()

        for msg in reversed(messages):
            conversation_history.append({
                "role": msg.role,
                "content": msg.content,
            })

        knowledge_context = await self.rag_service.get_context(query)

        provider_config = self._get_provider_config(model_provider_id)

        response = await self.llm_service.generate_response(
            query=query,
            context=knowledge_context,
            conversation_history=conversation_history,
            provider_config=provider_config if provider_config else None,
        )

        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
        )
        self.db.add(assistant_message)
        self.db.commit()

        return {
            "conversation_id": conversation_id,
            "response": response,
        }

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_user_conversations(self, user_id: int) -> List[Conversation]:
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).all()

    def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

    def get_fault_cases(self, skip: int = 0, limit: int = 100) -> List[FaultCase]:
        return self.db.query(FaultCase).offset(skip).limit(limit).all()

    def get_fault_case(self, case_id: int) -> Optional[FaultCase]:
        return self.db.query(FaultCase).filter(FaultCase.id == case_id).first()

    def update_fault_case(self, case_id: int, **kwargs) -> Optional[FaultCase]:
        case = self.get_fault_case(case_id)
        if not case:
            return None
        for key, value in kwargs.items():
            if hasattr(case, key):
                setattr(case, key, value)
        self.db.commit()
        self.db.refresh(case)
        return case
