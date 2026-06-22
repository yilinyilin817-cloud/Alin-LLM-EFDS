from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.mysql import get_db
from ..database.models import ModelProvider, ProviderType
from ..api.user_router import get_current_user
from ..api.system_router import log_operation
from pydantic import BaseModel
from typing import Optional, List
import json

router = APIRouter(prefix="/api/models", tags=["模型配置管理"])


class ModelProviderCreate(BaseModel):
    name: str
    provider_type: str = "third_party"
    provider_name: str
    api_base: str
    api_key: str = ""
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    is_default: bool = False
    is_active: bool = True
    extra_config: Optional[dict] = None


class ModelProviderUpdate(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    provider_name: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    extra_config: Optional[dict] = None


class ModelProviderResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    provider_name: str
    api_base: str
    api_key: str
    model_name: str
    temperature: float
    max_tokens: int
    is_default: bool
    is_active: bool
    extra_config: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


def _mask_key(key: str) -> str:
    if not key or len(key) <= 8:
        return key
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def _to_response(provider: ModelProvider, mask: bool = True) -> dict:
    extra = None
    if provider.extra_config:
        try:
            extra = json.loads(provider.extra_config)
        except (json.JSONDecodeError, TypeError):
            extra = None

    return {
        "id": provider.id,
        "name": provider.name,
        "provider_type": provider.provider_type.value if isinstance(provider.provider_type, ProviderType) else provider.provider_type,
        "provider_name": provider.provider_name,
        "api_base": provider.api_base,
        "api_key": _mask_key(provider.api_key) if mask else provider.api_key,
        "model_name": provider.model_name,
        "temperature": provider.temperature,
        "max_tokens": provider.max_tokens,
        "is_default": provider.is_default,
        "is_active": provider.is_active,
        "extra_config": extra,
        "created_at": provider.created_at.isoformat() if provider.created_at else None,
        "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,
    }


@router.get("/", response_model=List[ModelProviderResponse])
async def list_providers(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    providers = db.query(ModelProvider).order_by(ModelProvider.is_default.desc(), ModelProvider.id).all()
    return [_to_response(p) for p in providers]


@router.get("/active", response_model=List[ModelProviderResponse])
async def list_active_providers(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    providers = db.query(ModelProvider).filter(ModelProvider.is_active == True).order_by(ModelProvider.is_default.desc(), ModelProvider.id).all()
    return [_to_response(p, mask=False) for p in providers]


@router.get("/{provider_id}", response_model=ModelProviderResponse)
async def get_provider(
    provider_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    provider = db.query(ModelProvider).filter(ModelProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    return _to_response(provider)


@router.post("/", response_model=ModelProviderResponse)
async def create_provider(
    data: ModelProviderCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    valid_types = ["third_party", "local"]
    if data.provider_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的提供商类型，支持: {valid_types}")

    if data.is_default:
        db.query(ModelProvider).filter(ModelProvider.is_default == True).update({"is_default": False})

    provider = ModelProvider(
        name=data.name,
        provider_type=ProviderType(data.provider_type),
        provider_name=data.provider_name,
        api_base=data.api_base,
        api_key=data.api_key,
        model_name=data.model_name,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        is_default=data.is_default,
        is_active=data.is_active,
        extra_config=json.dumps(data.extra_config, ensure_ascii=False) if data.extra_config else None,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)

    log_operation(db, current_user.id, current_user.username, "创建模型配置", f"名称: {data.name}")
    db.commit()

    return _to_response(provider)


@router.put("/{provider_id}", response_model=ModelProviderResponse)
async def update_provider(
    provider_id: int,
    data: ModelProviderUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    provider = db.query(ModelProvider).filter(ModelProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    update_data = data.dict(exclude_none=True)

    if "provider_type" in update_data:
        valid_types = ["third_party", "local"]
        if update_data["provider_type"] not in valid_types:
            raise HTTPException(status_code=400, detail=f"无效的提供商类型，支持: {valid_types}")
        update_data["provider_type"] = ProviderType(update_data["provider_type"])

    if "extra_config" in update_data:
        update_data["extra_config"] = json.dumps(update_data["extra_config"], ensure_ascii=False) if update_data["extra_config"] else None

    if update_data.get("is_default"):
        db.query(ModelProvider).filter(ModelProvider.is_default == True).update({"is_default": False})

    for key, value in update_data.items():
        if hasattr(provider, key):
            setattr(provider, key, value)

    db.commit()
    db.refresh(provider)

    log_operation(db, current_user.id, current_user.username, "更新模型配置", f"ID: {provider_id}")
    db.commit()

    return _to_response(provider)


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    provider = db.query(ModelProvider).filter(ModelProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    provider_name = provider.name
    db.delete(provider)
    db.commit()

    log_operation(db, current_user.id, current_user.username, "删除模型配置", f"名称: {provider_name}")
    db.commit()

    return {"message": "模型配置已删除"}


@router.post("/{provider_id}/toggle")
async def toggle_provider(
    provider_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    provider = db.query(ModelProvider).filter(ModelProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    provider.is_active = not provider.is_active
    db.commit()

    status = "启用" if provider.is_active else "禁用"
    log_operation(db, current_user.id, current_user.username, f"{status}模型配置", f"名称: {provider.name}")
    db.commit()

    return {"message": f"模型配置已{status}", "is_active": provider.is_active}


@router.post("/{provider_id}/set-default")
async def set_default_provider(
    provider_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    provider = db.query(ModelProvider).filter(ModelProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    db.query(ModelProvider).filter(ModelProvider.is_default == True).update({"is_default": False})
    provider.is_default = True
    db.commit()

    log_operation(db, current_user.id, current_user.username, "设置默认模型", f"名称: {provider.name}")
    db.commit()

    return {"message": f"已将 {provider.name} 设为默认模型"}


@router.get("/providers/supported")
async def get_supported_providers(current_user=Depends(get_current_user)):
    return {
        "third_party": [
            {"name": "openai", "label": "OpenAI", "default_base": "https://api.openai.com/v1"},
            {"name": "deepseek", "label": "DeepSeek", "default_base": "https://api.deepseek.com/v1"},
            {"name": "zhipu", "label": "智谱AI (ChatGLM)", "default_base": "https://open.bigmodel.cn/api/paas/v4"},
            {"name": "qwen", "label": "通义千问", "default_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
            {"name": "moonshot", "label": "Moonshot (Kimi)", "default_base": "https://api.moonshot.cn/v1"},
            {"name": "baichuan", "label": "百川智能", "default_base": "https://api.baichuan-ai.com/v1"},
            {"name": "yi", "label": "零一万物 (Yi)", "default_base": "https://api.lingyiwanwu.com/v1"},
            {"name": "minimax", "label": "MiniMax", "default_base": "https://api.minimax.chat/v1"},
            {"name": "spark", "label": "讯飞星火", "default_base": "https://spark-api-open.xf-yun.com/v1"},
            {"name": "doubao", "label": "豆包 (火山引擎)", "default_base": "https://ark.cn-beijing.volces.com/api/v3"},
            {"name": "openai_compatible", "label": "OpenAI兼容接口", "default_base": ""},
        ],
        "local": [
            {"name": "ollama", "label": "Ollama", "default_base": "http://localhost:11434/v1"},
            {"name": "vllm", "label": "vLLM", "default_base": "http://localhost:8000/v1"},
            {"name": "lmstudio", "label": "LM Studio", "default_base": "http://localhost:1234/v1"},
            {"name": "text_generation", "label": "text-generation-webui", "default_base": "http://localhost:5000/v1"},
            {"name": "local_compatible", "label": "本地OpenAI兼容接口", "default_base": "http://localhost:8000/v1"},
        ]
    }
