"""LLM Provider 单元测试 — mock 全部外部 API 调用."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from devpulse.services.llm.base import LLMResponse
from devpulse.services.llm.factory import create_llm_provider
from devpulse.services.llm.ollama_provider import OllamaUnreachableError

# ── OpenAI Provider 测试 ───────────────────────────────

@pytest.mark.asyncio
async def test_openai_provider_generate():
    """测试 OpenAI Provider 正常生成."""
    from devpulse.services.llm.openai_provider import OpenAIProvider

    with patch("devpulse.services.llm.openai_provider.AsyncOpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_completion = MagicMock()
        content_str = (
            "概述：一个测试项目\n"
            "要点：1. 功能A 2. 功能B 3. 功能C\n"
            "标签：AI 开发 工具"
        )
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=content_str))
        ]
        mock_completion.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_openai_cls.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        result = await provider.generate(
            system_prompt="你是分析师",
            user_prompt="分析项目 X",
        )

    assert isinstance(result, LLMResponse)
    assert "概述" in result.content
    assert result.model == "gpt-4o-mini"
    assert result.usage["prompt_tokens"] == 100
    assert result.usage["completion_tokens"] == 50


@pytest.mark.asyncio
async def test_openai_provider_auth_error():
    """测试 OpenAI Provider 认证失败."""
    from openai import AuthenticationError

    from devpulse.services.llm.openai_provider import OpenAIProvider

    with patch("devpulse.services.llm.openai_provider.AsyncOpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_err = AuthenticationError(
            message="Invalid API key",
            response=mock_response,
            body={"error": "invalid_api_key"},
        )
        mock_client.chat.completions.create = AsyncMock(side_effect=mock_err)
        mock_openai_cls.return_value = mock_client

        provider = OpenAIProvider(api_key="bad-key")
        with pytest.raises(AuthenticationError):
            await provider.generate("sys", "user")


@pytest.mark.asyncio
async def test_openai_provider_close():
    """测试 OpenAI Provider 关闭."""
    from devpulse.services.llm.openai_provider import OpenAIProvider

    with patch("devpulse.services.llm.openai_provider.AsyncOpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_openai_cls.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key")
        await provider.close()

    mock_client.close.assert_called_once()


# ── Anthropic Provider 测试 ────────────────────────────

@pytest.mark.asyncio
async def test_anthropic_provider_generate():
    """测试 Anthropic Provider 正常生成."""
    from devpulse.services.llm.anthropic_provider import AnthropicProvider

    with patch(
        "devpulse.services.llm.anthropic_provider.anthropic.AsyncAnthropic"
    ) as mock_ant_cls:
        mock_client = MagicMock()
        mock_message = MagicMock()
        text_content = (
            "概述：测试项目\n要点：1. A 2. B 3. C\n标签：ML Python 工具"
        )
        mock_message.content = [MagicMock(text=text_content)]
        mock_message.usage = MagicMock(input_tokens=80, output_tokens=40)
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        mock_ant_cls.return_value = mock_client

        provider = AnthropicProvider(
            api_key="test-key", model="claude-3-5-haiku-latest"
        )
        result = await provider.generate(
            system_prompt="你是分析师",
            user_prompt="分析项目 Y",
        )

    assert isinstance(result, LLMResponse)
    assert "概述" in result.content
    assert result.model == "claude-3-5-haiku-latest"
    assert result.usage["prompt_tokens"] == 80
    assert result.usage["completion_tokens"] == 40


@pytest.mark.asyncio
async def test_anthropic_provider_close():
    """测试 Anthropic Provider 关闭."""
    from devpulse.services.llm.anthropic_provider import AnthropicProvider

    with patch(
        "devpulse.services.llm.anthropic_provider.anthropic.AsyncAnthropic"
    ) as mock_ant_cls:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_ant_cls.return_value = mock_client

        provider = AnthropicProvider(api_key="test-key")
        await provider.close()

    mock_client.close.assert_called_once()


# ── Ollama Provider 测试 ────────────────────────────────

@pytest.mark.asyncio
async def test_ollama_provider_generate():
    """测试 Ollama Provider 正常生成."""
    from devpulse.services.llm.ollama_provider import OllamaProvider

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": (
                "概述：Ollama 项目\n"
                "要点：1. 本地 2. 高效 3. 免费\n"
                "标签：LLM 本地 开源"
            )
        },
        "prompt_eval_count": 50,
        "eval_count": 30,
    }
    mock_response.raise_for_status = MagicMock()

    with patch(
        "devpulse.services.llm.ollama_provider.httpx.AsyncClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        provider = OllamaProvider(
            base_url="http://localhost:11434", model="qwen2.5:7b"
        )
        result = await provider.generate("sys", "user")

    assert isinstance(result, LLMResponse)
    assert "Ollama" in result.content
    assert result.model == "qwen2.5:7b"
    assert result.usage["prompt_tokens"] == 50
    assert result.usage["completion_tokens"] == 30


@pytest.mark.asyncio
async def test_ollama_provider_unreachable():
    """测试 Ollama 不可达时的错误处理."""
    from devpulse.services.llm.ollama_provider import OllamaProvider

    with patch(
        "devpulse.services.llm.ollama_provider.httpx.AsyncClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client_cls.return_value = mock_client

        provider = OllamaProvider(base_url="http://localhost:11434")
        with pytest.raises(OllamaUnreachableError) as exc_info:
            await provider.generate("sys", "user")

    assert "Ollama" in str(exc_info.value)
    assert "不可达" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ollama_provider_close():
    """测试 Ollama Provider 关闭."""
    from devpulse.services.llm.ollama_provider import OllamaProvider

    with patch(
        "devpulse.services.llm.ollama_provider.httpx.AsyncClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        mock_client_cls.return_value = mock_client

        provider = OllamaProvider()
        await provider.close()

    mock_client.aclose.assert_called_once()


# ── Provider Factory 测试 ──────────────────────────────

@pytest.mark.asyncio
async def test_provider_factory_openai():
    """测试工厂创建 OpenAI Provider."""
    from devpulse.services.llm.openai_provider import OpenAIProvider

    with patch("devpulse.services.llm.openai_provider.AsyncOpenAI"):
        provider = create_llm_provider("openai")
        assert isinstance(provider, OpenAIProvider)
        assert provider.model != ""  # 模型名已设置


@pytest.mark.asyncio
async def test_provider_factory_anthropic():
    """测试工厂创建 Anthropic Provider."""
    from devpulse.services.llm.anthropic_provider import AnthropicProvider

    with patch(
        "devpulse.services.llm.anthropic_provider.anthropic.AsyncAnthropic"
    ):
        provider = create_llm_provider("anthropic")
        assert isinstance(provider, AnthropicProvider)
        assert provider.model != ""


@pytest.mark.asyncio
async def test_provider_factory_ollama():
    """测试工厂创建 Ollama Provider."""
    from devpulse.services.llm.ollama_provider import OllamaProvider

    with patch("devpulse.services.llm.ollama_provider.httpx.AsyncClient"):
        provider = create_llm_provider("ollama")
        assert isinstance(provider, OllamaProvider)
        assert provider.model != ""


def test_provider_invalid_name():
    """测试非法 provider 名称抛 ValueError."""
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_llm_provider("invalid-provider")
