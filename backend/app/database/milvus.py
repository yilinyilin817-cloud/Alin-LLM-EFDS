from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from ..config import get_settings
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class MilvusClient:
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.collection = None

    def connect(self):
        try:
            connections.connect(host=self.host, port=self.port)
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def create_collection(self):
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension)
        ]

        schema = CollectionSchema(fields, description="Knowledge base vectors")
        self.collection = Collection(self.collection_name, schema)

        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.collection.create_index("embedding", index_params)
        logger.info(f"Created collection: {self.collection_name}")

    def insert_vectors(self, document_id: int, chunks: List[str], embeddings: List[List[float]]):
        if not self.collection:
            self.create_collection()

        data = [
            [document_id] * len(chunks),
            list(range(len(chunks))),
            chunks,
            embeddings
        ]

        self.collection.insert(data)
        self.collection.flush()
        logger.info(f"Inserted {len(chunks)} vectors for document {document_id}")

    def search_vectors(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        if not self.collection:
            self.create_collection()

        self.collection.load()

        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 16}
        }

        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["document_id", "chunk_index", "content"]
        )

        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.id,
                    "document_id": hit.entity.get("document_id"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "content": hit.entity.get("content"),
                    "score": hit.score
                })

        return formatted_results

    def delete_by_document(self, document_id: int):
        if not self.collection:
            return

        self.collection.delete(f"document_id == {document_id}")
        self.collection.flush()
        logger.info(f"Deleted vectors for document {document_id}")

    def drop_collection(self):
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            logger.info(f"Dropped collection: {self.collection_name}")


milvus_client: Optional[MilvusClient] = None


def get_milvus_client() -> MilvusClient:
    global milvus_client
    if milvus_client is None:
        milvus_client = MilvusClient()
        milvus_client.connect()
        milvus_client.create_collection()
    return milvus_client
