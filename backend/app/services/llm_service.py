from openai import AsyncOpenAI
from ..config import get_settings
from ..services.config_service import get_config_service
from typing import List, Dict, Optional, AsyncGenerator
import logging
import json

logger = logging.getLogger(__name__)
env_settings = get_settings()
config_service = get_config_service()


class LLMProviderClient:
    def __init__(
        self,
        api_base: str,
        api_key: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=api_base)
        self.model = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ):
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=stream,
            )

            if stream:
                return response

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise


class LLMService:
    def __init__(self):
        self.default_client = LLMProviderClient(
            api_base=env_settings.LLM_API_BASE,
            api_key=env_settings.LLM_API_KEY,
            model_name=config_service.get_llm_model(),
            temperature=config_service.get_temperature(),
            max_tokens=config_service.get_max_tokens(),
        )

    def _get_client(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMProviderClient:
        if api_base is None and api_key is None and model_name is None:
            self.default_client.model = config_service.get_llm_model()
            self.default_client.temperature = config_service.get_temperature()
            self.default_client.max_tokens = config_service.get_max_tokens()
            return self.default_client
        return LLMProviderClient(
            api_base=api_base or env_settings.LLM_API_BASE,
            api_key=api_key if api_key is not None else env_settings.LLM_API_KEY,
            model_name=model_name or config_service.get_llm_model(),
            temperature=temperature if temperature is not None else config_service.get_temperature(),
            max_tokens=max_tokens or config_service.get_max_tokens(),
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        client = self._get_client(api_base, api_key, model_name, temperature, max_tokens)
        return await client.chat(messages, temperature, max_tokens, stream)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        client = self._get_client(api_base, api_key, model_name, temperature, max_tokens)
        try:
            stream = await client.chat(messages, temperature, max_tokens, stream=True)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield f"\n\n[错误] 模型调用失败: {str(e)}"

    async def diagnose_fault(
        self,
        fault_phenomenon: str,
        device_info: Optional[Dict] = None,
        knowledge_context: Optional[str] = None,
        provider_config: Optional[Dict] = None,
    ) -> Dict:
        system_prompt = """你是一个专业的设备故障诊断专家。请根据用户描述的故障现象，提供：
1. 可能的故障原因（按可能性排序）
2. 详细的维修建议
3. 预防措施

请以JSON格式返回结果，格式如下：
{
    "possible_causes": ["原因1", "原因2", ...],
    "repair_suggestions": ["建议1", "建议2", ...],
    "preventive_measures": ["措施1", "措施2", ...],
    "severity": "high/medium/low"
}"""

        user_content = f"故障现象：{fault_phenomenon}"
        if device_info:
            user_content += f"\n设备信息：{json.dumps(device_info, ensure_ascii=False)}"
        if knowledge_context:
            user_content += f"\n相关知识库内容：\n{knowledge_context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        kwargs = provider_config or {}
        response = await self.chat(messages, **kwargs)

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = {
                "possible_causes": [response],
                "repair_suggestions": [],
                "preventive_measures": [],
                "severity": "unknown",
            }

        return result

    async def generate_response(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        provider_config: Optional[Dict] = None,
    ) -> str:
        system_prompt = """你是一个专业的设备故障诊断助手，能够帮助用户解答设备相关问题。
请根据提供的知识库内容和对话历史，给出专业、准确的回答。
如果知识库中没有相关信息，请基于你的专业知识回答，并说明这是通用建议。"""

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history[-6:])

        user_content = query
        if context:
            user_content = f"参考知识库内容：\n{context}\n\n用户问题：{query}"

        messages.append({"role": "user", "content": user_content})

        kwargs = provider_config or {}
        return await self.chat(messages, **kwargs)

    async def generate_response_stream(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        provider_config: Optional[Dict] = None,
    ) -> AsyncGenerator[str, None]:
        system_prompt = """你是一个专业的设备故障诊断助手，能够帮助用户解答设备相关问题。
请根据提供的知识库内容和对话历史，给出专业、准确的回答。
如果知识库中没有相关信息，请基于你的专业知识回答，并说明这是通用建议。"""

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history[-10:])

        user_content = query
        if context:
            user_content = f"参考知识库内容：\n{context}\n\n用户问题：{query}"

        messages.append({"role": "user", "content": user_content})

        kwargs = provider_config or {}
        async for chunk in self.chat_stream(messages, **kwargs):
            yield chunk


llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
