from sentence_transformers import SentenceTransformer
from ..config import get_settings
from typing import List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingModel:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.model = None

    def load(self):
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def encode(self, text: str) -> np.ndarray:
        self.load()
        return self.model.encode(text, convert_to_numpy=True)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        self.load()
        return self.model.encode(texts, convert_to_numpy=True, batch_size=32, show_progress_bar=True)


embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    global embedding_model
    if embedding_model is None:
        embedding_model = EmbeddingModel()
    return embedding_model
