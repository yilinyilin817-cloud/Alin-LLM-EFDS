from sqlalchemy.orm import Session
from ..database.models import KnowledgeDocument, DocumentStatus
from ..utils.text_processor import TextProcessor
from ..services.rag_service import get_rag_service
from typing import List, Optional
import logging
import os

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
        self.text_processor = TextProcessor()
        self.rag_service = get_rag_service()

    async def upload_document(
        self,
        title: str,
        file_path: str,
        file_type: str,
        uploaded_by: int
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            title=title,
            file_path=file_path,
            file_type=file_type,
            status=DocumentStatus.PENDING,
            uploaded_by=uploaded_by
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        try:
            doc.status = DocumentStatus.PROCESSING
            self.db.commit()

            content = self.text_processor.read_file(file_path)
            chunks = self.text_processor.split_text(content)

            await self.rag_service.index_document(doc.id, chunks)

            doc.content = content
            doc.chunk_count = len(chunks)
            doc.status = DocumentStatus.COMPLETED
            self.db.commit()
            self.db.refresh(doc)

            logger.info(f"Document {doc.id} processed successfully with {len(chunks)} chunks")
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            self.db.commit()
            logger.error(f"Document processing failed: {e}")
            raise

        return doc

    def get_document(self, doc_id: int) -> Optional[KnowledgeDocument]:
        return self.db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

    def get_documents(self, skip: int = 0, limit: int = 100) -> List[KnowledgeDocument]:
        return self.db.query(KnowledgeDocument).offset(skip).limit(limit).all()

    async def delete_document(self, doc_id: int) -> bool:
        doc = self.get_document(doc_id)
        if not doc:
            return False

        try:
            await self.rag_service.delete_document(doc_id)

            if doc.file_path and os.path.exists(doc.file_path):
                os.remove(doc.file_path)

            self.db.delete(doc)
            self.db.commit()
            logger.info(f"Deleted document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Document deletion failed: {e}")
            raise

    async def reprocess_document(self, doc_id: int) -> Optional[KnowledgeDocument]:
        doc = self.get_document(doc_id)
        if not doc:
            return None

        try:
            doc.status = DocumentStatus.PROCESSING
            self.db.commit()

            content = self.text_processor.read_file(doc.file_path)
            chunks = self.text_processor.split_text(content)

            await self.rag_service.delete_document(doc_id)
            await self.rag_service.index_document(doc_id, chunks)

            doc.content = content
            doc.chunk_count = len(chunks)
            doc.status = DocumentStatus.COMPLETED
            doc.error_message = None
            self.db.commit()
            self.db.refresh(doc)

            return doc
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            self.db.commit()
            logger.error(f"Document reprocessing failed: {e}")
            raise

    def search_documents(self, query: str) -> List[KnowledgeDocument]:
        return self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.title.contains(query) |
            KnowledgeDocument.content.contains(query)
        ).all()
