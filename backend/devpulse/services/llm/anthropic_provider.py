"""Anthropic Provider — 封装 anthropic.AsyncAnthropic."""

from __future__ import annotations

import logging

import anthropic

from devpulse.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API 异步 Provider.

    Args:
        api_key: Anthropic API 密钥.
        model: 模型名称，默认 claude-3-5-haiku-latest.
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest") -> None:
        super().__init__(model)
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(
        self, system_prompt: str, user_prompt: str, **kwargs: str | int | float
    ) -> LLMResponse:
        """调用 Anthropic messages.create.

        Args:
            system_prompt: 系统提示词.
            user_prompt: 用户提示词.
            **kwargs: 可选 max_tokens、temperature.

        Returns:
            LLMResponse，含 content / model / usage.
        """
        max_tokens = int(kwargs.get("max_tokens", 500))
        temperature = float(kwargs.get("temperature", 0.3))

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
            )
        except anthropic.AuthenticationError as exc:
            logger.error("Anthropic authentication failed: %s", exc)
            raise
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", exc)
            raise

        # Anthropic 返回的 content 是 list[ContentBlock]
        content = ""
        if response.content:
            content = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )

        usage = {
            "prompt_tokens": response.usage.input_tokens if response.usage else 0,
            "completion_tokens": response.usage.output_tokens if response.usage else 0,
        }
        logger.info("Anthropic generate success — model=%s tokens=%s", self.model, usage)
        return LLMResponse(content=content, model=self.model, usage=usage)

    async def close(self) -> None:
        """关闭底层 HTTP 客户端."""
        await self._client.close()
