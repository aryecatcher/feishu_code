"""LLM Provider layer using LangChain.

This module provides a unified interface to multiple LLM providers
using LangChain's pre-built integrations.
"""

from typing import Any
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from devflow.utils.config import settings
from devflow.utils.logging import get_logger
from devflow.utils.exceptions import LLMError

logger = get_logger("llm")


class LangChainLLM:
    """
    Unified LLM wrapper using LangChain.

    Supports OpenAI, Anthropic (Claude), Google (Gemini), and OpenAI-compatible APIs (e.g., DeepSeek) via LangChain.
    """

    def __init__(
        self,
        provider: str,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ):
        self.provider = provider
        self._llm: Any = None
        self._api_key = api_key
        self._model = model or self._get_default_model(provider)
        self._base_url = base_url
        self._extra_kwargs = kwargs

    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider."""
        defaults = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-opus-20240229",
            "google": "gemini-pro",
            "deepseek": "deepseek-chat",
        }
        return defaults.get(provider, "gpt-4-turbo-preview")

    def _get_api_key(self, provider: str) -> str:
        """Get API key from config or parameter."""
        if self._api_key:
            return self._api_key

        config = settings.llm_config.get(provider, {})
        return config.get("api_key", "")

    def _get_base_url(self) -> str | None:
        """Get base URL for OpenAI-compatible APIs."""
        if self._base_url:
            return self._base_url
        # DeepSeek is OpenAI-compatible
        if "deepseek" in self._model.lower():
            return "https://api.deepseek.com"
        return None

    def _create_llm(self) -> Any:
        """Create the underlying LangChain LLM instance."""
        api_key = self._get_api_key(self.provider)
        base_url = self._get_base_url()

        if not api_key:
            logger.warning(f"No API key for {self.provider}")

        # Use OpenAI client for DeepSeek (OpenAI-compatible)
        if base_url or "deepseek" in self._model.lower():
            return ChatOpenAI(
                api_key=api_key,
                model=self._model,
                base_url=base_url,
                **self._extra_kwargs,
            )
        elif self.provider == "openai":
            return ChatOpenAI(
                api_key=api_key,
                model=self._model,
                **self._extra_kwargs,
            )
        elif self.provider == "anthropic":
            return ChatAnthropic(
                api_key=api_key,
                model=self._model,
                **self._extra_kwargs,
            )
        elif self.provider == "google":
            return ChatGoogleGenerativeAI(
                api_key=api_key,
                model=self._model,
                **self._extra_kwargs,
            )
        else:
            raise LLMError(f"Unsupported provider: {self.provider}")

    @property
    def llm(self) -> Any:
        """Lazy-load the LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> "LLMResponse":
        """Send a chat request."""
        # Convert messages to LangChain format
        langchain_messages = self._convert_messages(messages)

        try:
            # Build invoke parameters based on provider
            invoke_params = {"temperature": temperature, **kwargs}

            if self.provider == "anthropic":
                invoke_params["max_tokens"] = max_tokens
            elif self.provider == "google":
                invoke_params["max_output_tokens"] = max_tokens
            else:
                invoke_params["max_tokens"] = max_tokens

            response = await self.llm.ainvoke(langchain_messages, **invoke_params)

            return LLMResponse(
                content=self._extract_content(response),
                raw_response=response,
                usage=self._extract_usage(response),
                model=self._model,
                provider=self.provider,
            )
        except Exception as e:
            logger.error(f"{self.provider} chat failed", error=str(e))
            raise LLMError(f"LLM call failed: {e}")

    def _convert_messages(self, messages: list[dict[str, str]]) -> list[BaseMessage]:
        """Convert our message format to LangChain messages."""
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        langchain_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))

        return langchain_messages

    def _extract_content(self, response: Any) -> str:
        """Extract content from LangChain response."""
        if hasattr(response, "content"):
            return response.content
        return str(response)

    def _extract_usage(self, response: Any) -> dict[str, int]:
        """Extract token usage from response."""
        usage = {}

        if hasattr(response, "usage_metadata"):
            meta = response.usage_metadata
            if "input_tokens" in meta:
                usage["input_tokens"] = meta["input_tokens"]
            if "output_tokens" in meta:
                usage["output_tokens"] = meta["output_tokens"]
            if "total_tokens" in meta:
                usage["total_tokens"] = meta["total_tokens"]

        return usage

    async def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ):
        """Stream chat response."""
        langchain_messages = self._convert_messages(messages)

        invoke_params = {"temperature": temperature, **kwargs}

        if self.provider == "anthropic":
            invoke_params["max_tokens"] = max_tokens
        elif self.provider == "google":
            invoke_params["max_output_tokens"] = max_tokens
        else:
            invoke_params["max_tokens"] = max_tokens

        async for chunk in self.llm.astream(langchain_messages, **invoke_params):
            if hasattr(chunk, "content"):
                yield chunk.content
            else:
                yield str(chunk)

    async def validate_connection(self) -> bool:
        """Validate API connection."""
        try:
            test_messages = [{"role": "user", "content": "Hi"}]
            await self.chat(test_messages, max_tokens=10)
            return True
        except Exception:
            return False


class LLMResponse:
    """Standardized LLM response."""

    def __init__(
        self,
        content: str,
        raw_response: Any,
        usage: dict[str, int] | None = None,
        model: str = "",
        provider: str = "",
    ):
        self.content = content
        self.raw_response = raw_response
        self.usage = usage or {}
        self.model = model
        self.provider = provider
