"""LLM Provider 工厂函数."""

from __future__ import annotations

from devpulse.config import settings
from devpulse.services.llm.base import BaseLLMProvider


def create_llm_provider(provider_name: str | None = None) -> BaseLLMProvider:
    """根据配置创建 LLM Provider 实例.

    Args:
        provider_name: openai / anthropic / ollama，默认使用 settings.LLM_PROVIDER.

    Returns:
        对应 Provider 实例.

    Raises:
        ValueError: 非法的 provider 名称.
    """
    name = provider_name or settings.LLM_PROVIDER

    if name == "openai":
        from devpulse.services.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )
    elif name == "anthropic":
        from devpulse.services.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
        )
    elif name == "deepseek":
        from devpulse.services.llm.deepseek_provider import DeepSeekProvider

        return DeepSeekProvider(
            api_key=settings.DEEPSEEK_API_KEY,
            model=settings.DEEPSEEK_MODEL,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
    elif name == "ollama":
        from devpulse.services.llm.ollama_provider import OllamaProvider

        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {name}")
