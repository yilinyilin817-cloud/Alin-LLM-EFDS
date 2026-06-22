from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LLM-EFDS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "llm_efds"

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "knowledge_vectors"

    EMBEDDING_MODEL: str = "shibing624/text2vec-base-chinese"
    EMBEDDING_DIMENSION: int = 768

    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = "your-api-key"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    return Settings()
