"""LLM Provider factory using LangChain."""

from typing import Any

from devflow.llm.langchain_llm import LangChainLLM, LLMResponse
from devflow.utils.logging import get_logger
from devflow.utils.exceptions import LLMError
from devflow.utils.config import settings

logger = get_logger("llm.factory")


class LLMFactory:
    """Factory for creating LLM provider instances using LangChain."""

    _providers: list[str] = ["openai", "anthropic", "google", "deepseek"]
    _instances: dict[str, LangChainLLM] = {}

    @classmethod
    def create(
        cls,
        provider: str,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> LangChainLLM:
        """Create an LLM provider instance."""
        if provider not in cls._providers:
            available = ", ".join(cls._providers)
            raise LLMError(
                f"Unknown provider: {provider}. Available: {available}",
                details={"provider": provider, "available": available},
            )

        return LangChainLLM(
            provider=provider,
            api_key=api_key,
            model=model,
            **kwargs,
        )

    @classmethod
    def get(
        cls,
        provider: str,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> LangChainLLM:
        """Get or create a cached LLM provider instance."""
        cache_key = f"{provider}:{model or 'default'}"

        if cache_key not in cls._instances:
            cls._instances[cache_key] = cls.create(provider, api_key, model, **kwargs)
            logger.info("Created LLM provider", provider=provider, model=model)

        return cls._instances[cache_key]

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all available providers."""
        return cls._providers.copy()

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached provider instances."""
        cls._instances.clear()
        logger.info("Cleared LLM provider cache")


class LLMManager:
    """High-level LLM management with fallback support."""

    def __init__(self):
        self._primary: LangChainLLM | None = None
        self._fallback: LangChainLLM | None = None
        self._configured = False

    def configure(
        self,
        primary: str,
        fallback: str | None = None,
        **kwargs,
    ) -> None:
        """Configure primary and fallback providers."""
        self._primary = LLMFactory.get(primary, **kwargs)

        if fallback:
            self._fallback = LLMFactory.get(fallback, **kwargs)
            logger.info("Configured LLM with fallback", primary=primary, fallback=fallback)
        else:
            logger.info("Configured LLM", primary=primary)

        self._configured = True

    def auto_configure(self) -> None:
        """Auto-configure LLM from settings."""
        if self._configured:
            return

        provider = settings.default_provider
        config = settings.llm_config.get(provider, {})

        if config.get("api_key"):
            self.configure(
                primary=provider,
                model=config.get("model"),
                api_key=config.get("api_key"),
            )
        else:
            logger.warning(
                f"No API key configured for provider: {provider}. "
                "Please set the appropriate API key in .env"
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_fallback: bool = False,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request with optional fallback."""
        # Auto-configure if not configured
        if not self._configured:
            self.auto_configure()

        provider = self._fallback if use_fallback else self._primary

        if provider is None:
            raise LLMError("No LLM provider configured")

        try:
            return await provider.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        except Exception as e:
            if not use_fallback and self._fallback:
                logger.warning("Primary failed, trying fallback", error=str(e))
                return await self.chat(
                    messages, temperature, max_tokens, use_fallback=True, **kwargs
                )
            raise

    @property
    def primary_provider(self) -> LangChainLLM | None:
        return self._primary

    @property
    def fallback_provider(self) -> LangChainLLM | None:
        return self._fallback

    def get_langchain_llm(self, use_fallback: bool = False) -> Any:
        """
        获取底层的 LangChain LLM 实例，用于 with_structured_output 等操作。

        Args:
            use_fallback: 是否使用 fallback provider

        Returns:
            底层的 LangChain LLM 实例 (ChatOpenAI, ChatAnthropic 等)
        """
        from langchain_core.language_models import BaseChatModel

        provider = self._fallback if use_fallback else self._primary

        if provider is None:
            raise LLMError("No LLM provider configured")

        return provider.llm


# Global LLM manager instance
llm_manager = LLMManager()
