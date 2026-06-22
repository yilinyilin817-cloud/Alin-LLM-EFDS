from sqlalchemy.orm import Session
from ..database.mysql import SessionLocal
from ..config import get_settings
from typing import Any, Optional
import logging
import time

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "llm_model": "gpt-3.5-turbo",
    "embedding_model": "shibing624/text2vec-base-chinese",
    "rag_top_k": 5,
    "similarity_threshold": 0.7,
    "max_tokens": 2048,
    "temperature": 0.7,
}


class ConfigService:
    _instance = None
    _cache = {}
    _cache_time = 0
    _cache_ttl = 5

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_from_db(self) -> dict:
        try:
            from ..api.system_router import SystemSettings

            db = SessionLocal()
            try:
                settings = db.query(SystemSettings).all()
                result = DEFAULT_SETTINGS.copy()

                for setting in settings:
                    if setting.key in result:
                        try:
                            if isinstance(result[setting.key], int):
                                result[setting.key] = int(setting.value)
                            elif isinstance(result[setting.key], float):
                                result[setting.key] = float(setting.value)
                            else:
                                result[setting.key] = setting.value
                        except (ValueError, TypeError):
                            pass

                return result
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to load settings from database: {e}")
            return DEFAULT_SETTINGS.copy()

    def get_settings(self, force_reload: bool = False) -> dict:
        current_time = time.time()

        if force_reload or current_time - self._cache_time > self._cache_ttl:
            self._cache = self._load_from_db()
            self._cache_time = current_time

        return self._cache.copy()

    def get(self, key: str, default: Any = None) -> Any:
        settings = self.get_settings()
        return settings.get(key, default)

    def get_llm_model(self) -> str:
        return self.get("llm_model", "gpt-3.5-turbo")

    def get_temperature(self) -> float:
        return float(self.get("temperature", 0.7))

    def get_max_tokens(self) -> int:
        return int(self.get("max_tokens", 2048))

    def get_rag_top_k(self) -> int:
        return int(self.get("rag_top_k", 5))

    def get_similarity_threshold(self) -> float:
        return float(self.get("similarity_threshold", 0.7))

    def get_embedding_model(self) -> str:
        return self.get("embedding_model", "shibing624/text2vec-base-chinese")

    def reload(self):
        self._cache = self._load_from_db()
        self._cache_time = time.time()
        logger.info("Configuration reloaded from database")

    def get_env_settings(self):
        return get_settings()


config_service = ConfigService()


def get_config_service() -> ConfigService:
    return config_service
