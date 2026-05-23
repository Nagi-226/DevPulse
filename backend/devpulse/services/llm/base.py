"""LLM Provider 抽象基类与通用数据结构."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM 生成响应统一结构.

    Attributes:
        content: 生成的文本内容.
        model: 使用的模型名称.
        usage: token 用量统计，包含 prompt_tokens 与 completion_tokens.
    """

    content: str
    model: str
    usage: dict[str, int]


class BaseLLMProvider(ABC):
    """LLM 服务提供者抽象基类.

    所有 Provider（OpenAI / Anthropic / Ollama）必须实现 generate 与 close 方法。
    """

    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    async def generate(
        self, system_prompt: str, user_prompt: str, **kwargs: str | int | float
    ) -> LLMResponse:
        """生成 LLM 响应.

        Args:
            system_prompt: 系统提示词.
            user_prompt: 用户提示词.
            **kwargs: 额外参数（如 temperature、max_tokens 等）.

        Returns:
            LLMResponse 统一结构化响应.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """关闭底层连接."""
        ...
