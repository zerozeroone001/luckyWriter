"""
AI 服务模块：按 NewAPI / OpenAI 兼容接口调用模型能力。

NewAPI 文档要点：
- 模型列表：GET /v1/models
- 聊天补全：POST /v1/chat/completions
- 鉴权方式：Authorization: Bearer <token>
- 请求体格式：OpenAI Chat Completions 兼容格式
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
import hashlib
import json
import time

import httpx

from config import settings


OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODELS_PATH = "/models"
OPENAI_CHAT_COMPLETIONS_PATH = "/chat/completions"
OPENAI_IMAGES_GENERATIONS_PATH = "/images/generations"
REQUEST_TIMEOUT_SECONDS = 30.0
STREAM_TIMEOUT_SECONDS = 120.0
MODEL_EXCLUDE_KEYWORDS = (
    "embedding",
    "moderation",
    "whisper",
    "tts",
    "dall-e",
    "text-embedding",
    "text-moderation",
    "audio",
    "image",
)


class AIService:
    """统一封装 NewAPI/OpenAI 兼容接口的 AI 调用能力。"""

    def __init__(self):
        self._log_callback = None

    def set_log_callback(self, callback):
        """设置日志回调函数，用于记录模型调用日志。"""
        self._log_callback = callback

    async def _log_api_call(self, log_data: dict):
        """记录API调用日志。"""
        if self._log_callback:
            await self._log_callback(log_data)

    async def get_available_models(
        self,
        provider: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取指定渠道可用模型列表。"""
        provider_name = provider.lower()

        if provider_name in {"openai", "newapi"}:
            return await self._get_openai_compatible_models(api_key, base_url)

        raise ValueError(f"不支持的提供商: {provider}")

    async def test_model_speed(
        self,
        provider: str,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> float:
        """按 NewAPI/OpenAI 兼容规范发送最小非流式测试请求，用于外部统计响应时间。"""
        response = await self._create_openai_compatible_completion(
            messages=[{"role": "user", "content": "say 1"}],
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=10,
            temperature=0,
            stream=False,
            debug_label="模型测速",
        )
        print(f"[模型测速] 响应内容: {self._safe_json_dumps(response)}")
        return 0.0

    def generate_prompt_fingerprint(self, prompt: str) -> str:
        """生成提示词指纹，用于缓存与日志去重。"""
        return hashlib.md5(prompt.encode("utf-8")).hexdigest()

    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: str = "",
        provider: str = "newapi",
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.8,
        max_tokens: int = 4000,
        api_key: str | None = None,
        base_url: str | None = None,
        log_context: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        """根据 provider 选择 NewAPI/OpenAI 兼容渠道并流式生成文本内容。"""
        provider_name = provider.lower()

        if provider_name in {"openai", "newapi"}:
            async for chunk in self._generate_openai_compatible_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                base_url=base_url,
                log_context=log_context,
            ):
                yield chunk
            return

        raise ValueError(f"不支持的AI提供商: {provider}")

    async def generate_image(
        self,
        prompt: str,
        style: str = "realistic",
        size: str = "1024x1024",
    ) -> str:
        """通过 OpenAI 兼容图像接口生成图片，并返回图片 URL。"""
        api_key = self._resolve_api_key(settings.OPENAI_API_KEY)
        base_url = self._normalize_openai_base_url(settings.OPENAI_BASE_URL)
        url = f"{base_url}{OPENAI_IMAGES_GENERATIONS_PATH}"
        style_prompts = {
            "realistic": "photorealistic, high detail, professional photography",
            "anime": "anime style, manga style, Japanese animation",
            "chinese": "Chinese painting style, traditional Chinese art, ink wash",
            "3d": "3D render, Pixar style, cinematic lighting",
        }
        full_prompt = f"{prompt}, {style_prompts.get(style, '')}".strip(", ")

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                headers=self._openai_headers(api_key),
                json={
                    "model": "dall-e-3",
                    "prompt": full_prompt,
                    "size": size,
                    "quality": "standard",
                    "n": 1,
                },
            )

        self._raise_for_api_error(response, "生成图片失败")
        data = response.json()
        image_url = data.get("data", [{}])[0].get("url")

        if not image_url:
            raise RuntimeError("生成图片失败：响应中缺少图片 URL")

        return image_url

    async def _get_openai_compatible_models(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> list[dict[str, Any]]:
        """调用 NewAPI/OpenAI 兼容的 GET /v1/models 获取模型列表。"""
        resolved_api_key = self._resolve_api_key(api_key or settings.OPENAI_API_KEY)
        url = f"{self._normalize_openai_base_url(base_url or settings.OPENAI_BASE_URL)}{OPENAI_MODELS_PATH}"

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=self._openai_headers(resolved_api_key))

        self._raise_for_api_error(response, "获取模型列表失败")
        data = response.json()
        models_data = data.get("data")

        if not isinstance(models_data, list):
            raise RuntimeError("获取模型列表失败：API 响应缺少 data 数组")

        models = []
        for item in models_data:
            model_id = str(item.get("id", "")).strip()
            if not model_id or self._is_non_chat_model(model_id):
                continue

            owned_by = str(item.get("owned_by", "")).strip()
            models.append(
                {
                    "id": model_id,
                    "name": model_id,
                    "description": owned_by or model_id,
                    "owned_by": owned_by,
                }
            )

        if not models:
            raise RuntimeError("该渠道没有返回可用聊天模型")

        return sorted(models, key=lambda model: model["id"])

    async def _generate_openai_compatible_streaming(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        api_key: str | None = None,
        base_url: str | None = None,
        log_context: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        """调用 NewAPI/OpenAI 兼容的 POST /v1/chat/completions 流式生成。"""
        messages = self._build_chat_messages(prompt, system_prompt)
        stream = await self._create_openai_compatible_completion(
            messages=messages,
            model=model,
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url or settings.OPENAI_BASE_URL,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            log_context=log_context,
        )

        async for chunk in stream:
            yield chunk

    async def _create_openai_compatible_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key: str | None,
        base_url: str | None,
        temperature: float = 0.8,
        max_tokens: int = 4000,
        stream: bool = True,
        debug_label: str | None = None,
        log_context: dict | None = None,
    ) -> Any:
        """发送 Chat Completions 请求，按 stream 参数返回普通响应或异步文本流。"""
        resolved_api_key = self._resolve_api_key(api_key or settings.OPENAI_API_KEY)
        url = f"{self._normalize_openai_base_url(base_url or settings.OPENAI_BASE_URL)}{OPENAI_CHAT_COMPLETIONS_PATH}"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if debug_label:
            print(f"[{debug_label}] 请求地址: {url}")
            print(f"[{debug_label}] 请求内容: {self._safe_json_dumps(payload)}")

        if stream:
            return self._stream_openai_compatible_response(url, resolved_api_key, payload, log_context)

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(url, headers=self._openai_headers(resolved_api_key), json=payload)

        if debug_label:
            print(f"[{debug_label}] 响应状态: HTTP {response.status_code}")
            print(f"[{debug_label}] 响应内容: {response.text}")

        self._raise_for_api_error(response, "聊天补全失败")
        return response.json()

    async def _stream_openai_compatible_response(
        self,
        url: str,
        api_key: str,
        payload: dict[str, Any],
        log_context: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        """解析 NewAPI/OpenAI 兼容的 SSE 流式响应。"""
        start_time = time.time()
        status = "success"
        error_message = None
        input_tokens = 0
        output_tokens = 0

        # 提取 prompt（messages 中的内容）
        messages = payload.get("messages", [])
        prompt_parts = [msg.get("content", "") for msg in messages if msg.get("content")]
        full_prompt = "\n".join(prompt_parts)

        try:
            async with httpx.AsyncClient(timeout=STREAM_TIMEOUT_SECONDS) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=self._openai_headers(api_key),
                    json=payload,
                ) as response:
                    self._raise_for_api_error(response, "流式聊天补全失败")

                    async for line in response.aiter_lines():
                        content = self._parse_openai_stream_line(line)
                        if content:
                            output_tokens += len(content) // 4
                            yield content

            input_tokens = len(full_prompt) // 4

        except Exception as e:
            status = "failed"
            error_message = str(e)
            raise
        finally:
            duration = time.time() - start_time
            log_data = {
                "url": url,
                "model": payload.get("model"),
                "prompt": full_prompt[:2000] if full_prompt else None,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration_seconds": duration,
                "status": status,
                "error_message": error_message,
            }
            if log_context:
                log_data.update(log_context)
            await self._log_api_call(log_data)

    def _normalize_openai_base_url(self, base_url: str | None) -> str:
        """标准化 OpenAI 兼容接口 Base URL，确保最终以 /v1 结尾。"""
        resolved_base_url = (base_url or OPENAI_DEFAULT_BASE_URL).rstrip("/")
        return resolved_base_url if resolved_base_url.endswith("/v1") else f"{resolved_base_url}/v1"

    def _openai_headers(self, api_key: str) -> dict[str, str]:
        """生成 NewAPI/OpenAI 兼容接口请求头。"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _resolve_api_key(self, api_key: str | None) -> str:
        """校验并返回 API Key，避免发送无效鉴权请求。"""
        if not api_key:
            raise ValueError("未配置 API 密钥")
        return api_key

    def _build_chat_messages(self, prompt: str, system_prompt: str = "") -> list[dict[str, str]]:
        """构建 Chat Completions 兼容的 messages 数组。"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _is_non_chat_model(self, model_id: str) -> bool:
        """判断模型 ID 是否明显属于非聊天模型。"""
        normalized_model_id = model_id.lower()
        return any(keyword in normalized_model_id for keyword in MODEL_EXCLUDE_KEYWORDS)

    def _parse_openai_stream_line(self, line: str) -> str | None:
        """从 OpenAI 兼容 SSE 单行数据中提取文本增量。"""
        stripped_line = line.strip()
        if not stripped_line or not stripped_line.startswith("data:"):
            return None

        raw_data = stripped_line.removeprefix("data:").strip()
        if raw_data == "[DONE]":
            return None

        data = json.loads(raw_data)
        choices = data.get("choices") or []
        if not choices:
            return None

        delta = choices[0].get("delta") or {}
        message = choices[0].get("message") or {}
        return delta.get("content") or message.get("content")

    def _safe_json_dumps(self, data: Any) -> str:
        """安全格式化控制台调试内容，避免非 JSON 对象打印失败。"""
        try:
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        except TypeError:
            return str(data)

    def _raise_for_api_error(self, response: httpx.Response, action: str) -> None:
        """按 NewAPI/OpenAI 兼容错误结构提取错误信息并抛出异常。"""
        if response.status_code < 400:
            return

        message = response.text
        try:
            error_data = response.json().get("error", {})
            message = error_data.get("message") or message
        except json.JSONDecodeError:
            pass

        raise RuntimeError(f"{action} - HTTP {response.status_code}: {message}")


ai_service = AIService()
