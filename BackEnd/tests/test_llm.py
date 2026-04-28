"""Tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from devflow.llm.base import BaseLLMProvider, LLMResponse
from devflow.llm.openai import OpenAIProvider
from devflow.llm.factory import LLMFactory, LLMManager


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    @pytest.fixture
    def provider(self):
        """Create a provider with mocked client."""
        with patch("devflow.llm.openai.AsyncOpenAI") as mock_client:
            yield OpenAIProvider(
                api_key="test-key",
                model="gpt-4-turbo-preview",
            )

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.model = "gpt-4-turbo-preview"

        provider.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        messages = [{"role": "user", "content": "Hello"}]
        response = await provider.chat(messages)

        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.provider == "openai"

    @pytest.mark.asyncio
    async def test_validate_connection(self, provider):
        """Test connection validation."""
        provider.client.models.list = AsyncMock(return_value=MagicMock())
        result = await provider.validate_connection()
        assert result is True


class TestLLMFactory:
    """Tests for LLM factory."""

    def test_create_provider(self):
        """Test creating a provider."""
        provider = LLMFactory.create("openai", api_key="test-key")
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-key"

    def test_create_unknown_provider(self):
        """Test creating unknown provider raises error."""
        with pytest.raises(Exception):
            LLMFactory.create("unknown-provider")

    def test_list_providers(self):
        """Test listing available providers."""
        providers = LLMFactory.list_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers


class TestLLMManager:
    """Tests for LLM manager."""

    @pytest.mark.asyncio
    async def test_configure(self):
        """Test manager configuration."""
        manager = LLMManager()

        with patch.object(LLMFactory, "get") as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            manager.configure(primary="openai", fallback="anthropic")

            assert manager.primary_provider is not None
            assert manager.fallback_provider is not None
