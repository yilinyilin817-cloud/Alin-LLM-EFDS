from ..utils.embedding import get_embedding_model
from ..database.milvus import get_milvus_client
from ..config import get_settings
from ..services.config_service import get_config_service
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
env_settings = get_settings()
config_service = get_config_service()


class RAGService:
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.milvus_client = get_milvus_client()
        self.top_k = config_service.get_rag_top_k()
        self.similarity_threshold = config_service.get_similarity_threshold()

    def _get_dynamic_settings(self):
        self.top_k = config_service.get_rag_top_k()
        self.similarity_threshold = config_service.get_similarity_threshold()

    async def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        try:
            self._get_dynamic_settings()
            query_embedding = self.embedding_model.encode(query)

            results = self.milvus_client.search_vectors(
                query_embedding=query_embedding.tolist(),
                top_k=top_k or self.top_k
            )

            filtered_results = [
                r for r in results
                if r["score"] >= self.similarity_threshold
            ]

            logger.info(f"Retrieved {len(filtered_results)} relevant chunks for query")
            return filtered_results
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            raise

    async def get_context(self, query: str, top_k: Optional[int] = None) -> str:
        results = await self.retrieve(query, top_k)

        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[参考{i}] {result['content']}")

        return "\n\n".join(context_parts)

    async def retrieve_with_scores(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        try:
            query_embedding = self.embedding_model.encode(query)

            results = self.milvus_client.search_vectors(
                query_embedding=query_embedding.tolist(),
                top_k=top_k or self.top_k
            )

            return results
        except Exception as e:
            logger.error(f"RAG retrieval with scores error: {e}")
            raise

    async def index_document(self, document_id: int, chunks: List[str]) -> bool:
        try:
            embeddings = self.embedding_model.encode_batch(chunks)

            self.milvus_client.insert_vectors(
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings.tolist()
            )

            logger.info(f"Indexed document {document_id} with {len(chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Document indexing error: {e}")
            raise

    async def delete_document(self, document_id: int) -> bool:
        try:
            self.milvus_client.delete_by_document(document_id)
            logger.info(f"Deleted document {document_id} from vector store")
            return True
        except Exception as e:
            logger.error(f"Document deletion error: {e}")
            raise


rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service
