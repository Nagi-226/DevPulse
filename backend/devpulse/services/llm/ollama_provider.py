"""Ollama Provider — 使用 httpx 调用本地 Ollama API."""

from __future__ import annotations

import logging

import httpx

from devpulse.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OllamaUnreachableError(Exception):
    """Ollama 服务不可达异常."""


class OllamaProvider(BaseLLMProvider):
    """Ollama 本地 LLM 异步 Provider.

    Args:
        base_url: Ollama 服务地址，默认 http://localhost:11434.
        model: 模型名称，默认 qwen2.5:7b.
    """

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"
    ) -> None:
        super().__init__(model)
        self._base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url, timeout=httpx.Timeout(120))

    async def generate(
        self, system_prompt: str, user_prompt: str, **kwargs: str | int | float
    ) -> LLMResponse:
        """调用 Ollama /api/chat.

        Args:
            system_prompt: 系统提示词.
            user_prompt: 用户提示词.
            **kwargs: 可选 temperature、max_tokens（Ollama 对应 num_predict）.

        Returns:
            LLMResponse，含 content / model / usage.

        Raises:
            OllamaUnreachableError: Ollama 服务不可达.
        """
        temperature = float(kwargs.get("temperature", 0.3))
        # Ollama 用 num_predict 替代 max_tokens，取较小值避免 token 耗尽
        num_predict = int(kwargs.get("max_tokens", 500))

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }

        try:
            response = await self._client.post("/api/chat", json=payload)
        except httpx.ConnectError as exc:
            logger.error("Ollama unreachable at %s: %s", self._base_url, exc)
            raise OllamaUnreachableError(
                f"Ollama 服务不可达 ({self._base_url})，请确认 Ollama 已启动"
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error("Ollama request timed out: %s", exc)
            raise

        response.raise_for_status()
        data = response.json()

        content = data.get("message", {}).get("content", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }
        logger.info("Ollama generate success — model=%s tokens=%s", self.model, usage)
        return LLMResponse(content=content, model=self.model, usage=usage)

    async def close(self) -> None:
        """关闭底层 HTTP 客户端."""
        await self._client.aclose()
