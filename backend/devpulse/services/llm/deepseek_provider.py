"""DeepSeek Provider — OpenAI 兼容接口，指向 DeepSeek API."""

from __future__ import annotations

import logging

from openai import APIError, APITimeoutError, AsyncOpenAI, AuthenticationError

from devpulse.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


MAX_CONTEXT_TOKENS = 6000  # 单次 prompt 安全上限，超过后自动截断


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek API 异步 Provider（OpenAI 兼容协议）.

    Args:
        api_key: DeepSeek API 密钥.
        model: 模型名称，默认 deepseek-chat.
        base_url: API 基础地址，默认 https://api.deepseek.com.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
    ) -> None:
        super().__init__(model)
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate(
        self, system_prompt: str, user_prompt: str, **kwargs: str | int | float
    ) -> LLMResponse:
        """调用 DeepSeek chat.completions.create.

        Args:
            system_prompt: 系统提示词.
            user_prompt: 用户提示词.
            **kwargs: 可选 temperature、max_tokens.

        Returns:
            LLMResponse，含 content / model / usage.

        Raises:
            AuthenticationError: API Key 无效.
            APITimeoutError: 请求超时.
            APIError: 其它 API 错误.
        """
        max_tokens = int(kwargs.get("max_tokens", 500))
        temperature = float(kwargs.get("temperature", 0.3))

        # 上下文过长时自动截断
        if len(user_prompt) > MAX_CONTEXT_TOKENS * 4:
            logger.warning(
                "Prompt too long (%d chars), truncating to ~%d tokens",
                len(user_prompt),
                MAX_CONTEXT_TOKENS,
            )
            user_prompt = user_prompt[: MAX_CONTEXT_TOKENS * 4]

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except AuthenticationError as exc:
            logger.error("DeepSeek authentication failed: %s", exc)
            raise
        except APITimeoutError as exc:
            logger.error("DeepSeek request timed out: %s", exc)
            raise
        except APIError as exc:
            logger.error("DeepSeek API error: %s", exc)
            raise

        content = response.choices[0].message.content or ""
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        logger.info("DeepSeek generate success — model=%s tokens=%s", self.model, usage)
        return LLMResponse(content=content, model=self.model, usage=usage)

    async def close(self) -> None:
        """关闭底层 HTTP 客户端."""
        await self._client.close()
