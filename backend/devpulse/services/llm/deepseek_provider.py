"""DeepSeek Provider — OpenAI 兼容接口，含费用追踪."""

from __future__ import annotations

import logging

from openai import APIError, APITimeoutError, AsyncOpenAI, AuthenticationError

from devpulse.config import settings
from devpulse.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


MAX_CONTEXT_TOKENS = 6000  # 单次 prompt 安全上限，超过后自动截断


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek API 异步 Provider（OpenAI 兼容协议）.

    包含 token 消耗统计，用于 LLM 成本追踪.

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
        # ── 费用追踪 ──────────────────────────────
        self._total_prompt_tokens: int = 0
        self._total_completion_tokens: int = 0
        self._total_cost: float = 0.0

    @property
    def total_prompt_tokens(self) -> int:
        """累计 prompt tokens."""
        return self._total_prompt_tokens

    @property
    def total_completion_tokens(self) -> int:
        """累计 completion tokens."""
        return self._total_completion_tokens

    @property
    def total_cost(self) -> float:
        """累计费用 (USD)."""
        return self._total_cost

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """根据 DeepSeek 定价计算费用.

        DeepSeek 定价:
            - 输入: $0.14 / 1M tokens
            - 输出: $0.28 / 1M tokens

        Args:
            prompt_tokens: 输入 token 数.
            completion_tokens: 输出 token 数.

        Returns:
            费用 (USD).
        """
        input_price = settings.DEEPSEEK_PRICE_INPUT_PER_1K / 1000  # per token
        output_price = settings.DEEPSEEK_PRICE_OUTPUT_PER_1K / 1000  # per token
        return prompt_tokens * input_price + completion_tokens * output_price

    async def generate(
        self, system_prompt: str, user_prompt: str, **kwargs: str | int | float
    ) -> LLMResponse:
        """调用 DeepSeek chat.completions.create（含费用追踪）.

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

        # 检查月度预算
        if self._total_cost >= settings.LLM_MONTHLY_BUDGET:
            logger.warning(
                "LLM monthly budget exceeded: $%.4f / $%.2f",
                self._total_cost,
                settings.LLM_MONTHLY_BUDGET,
            )
            # 不抛出异常，但警告日志

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
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        cost = self._calculate_cost(prompt_tokens, completion_tokens)

        # ── 累计追踪 ──────────────────────────────
        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens
        self._total_cost += cost

        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": round(cost, 6),
            "total_cost": round(self._total_cost, 6),
        }
        logger.info(
            "DeepSeek generate success — model=%s tokens=%s cost=$%.6f total=$%.4f",
            self.model,
            {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
            cost,
            self._total_cost,
        )
        return LLMResponse(content=content, model=self.model, usage=usage)

    async def close(self) -> None:
        """关闭底层 HTTP 客户端并记录最终费用."""
        logger.info(
            "DeepSeek provider closed — total: prompt=%d, completion=%d, cost=$%.4f",
            self._total_prompt_tokens,
            self._total_completion_tokens,
            self._total_cost,
        )
        await self._client.close()
