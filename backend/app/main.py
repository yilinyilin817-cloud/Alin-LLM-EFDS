from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database.mysql import engine
from .database.models import Base
from .api import user_router, diagnosis_router, knowledge_router, chat_router, maintenance_router, issue_router, system_router, model_router
from .api.device_router import router as device_router
from .api.system_router import SystemSettings, OperationLog
import logging

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于大模型的设备故障诊断系统"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(diagnosis_router)
app.include_router(knowledge_router)
app.include_router(chat_router)
app.include_router(device_router)
app.include_router(maintenance_router)
app.include_router(issue_router)
app.include_router(system_router)
app.include_router(model_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up LLM-EFDS application...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
