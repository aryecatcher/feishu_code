"""Base Agent using LangChain.

All agents use the globally configured LLM provider (set via default_provider in settings).
Supports structured output via Pydantic schemas.
"""

from abc import ABC, abstractmethod
from typing import Any, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from devflow.models.pipeline import AgentConfig
from devflow.llm.factory import llm_manager, LLMResponse
from devflow.utils.logging import get_logger

logger = get_logger("agent")


class AgentResult(BaseModel):
    """Result from agent execution."""

    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[Any] = Field(default_factory=list)
    error: str | None = None
    tokens_used: int = 0


class BaseAgent(ABC):
    """Abstract base class for all agents using LangChain.

    Supports structured output via Pydantic schemas through with_structured_output().
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self._llm = None

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @property
    def output_schema(self) -> Type[BaseModel] | None:
        """
        Return the output schema for structured output.

        Subclasses should override this to enable structured output.
        Return None for simple text output (default).
        """
        return None

    def _get_llm(self) -> BaseChatModel:
        """
        Get the underlying LangChain LLM instance.

        Returns:
            The underlying chat model (ChatOpenAI, ChatAnthropic, etc.)
        """
        return llm_manager.get_langchain_llm()

    def _create_structured_llm(self, strict: bool = True) -> BaseChatModel:
        """
        Create a structured output LLM using with_structured_output().

        Different LLM providers support different structured output methods:
        - OpenAI: supports function_calling, json_schema, json_mode
        - DeepSeek: only supports json_mode (json_schema is unavailable)
        - Anthropic: supports function_calling, json_schema

        Args:
            strict: Whether to use strict mode for structured output.
                    Only affects providers that support it (OpenAI, Anthropic).

        Returns:
            LLM configured for structured output

        Raises:
            ValueError: If output_schema is not defined
        """
        if self.output_schema is None:
            raise ValueError(
                f"{self.__class__.__name__} does not define output_schema. "
                "Set output_schema property to enable structured output."
            )

        llm = self._get_llm()
        provider = self._get_provider_name()

        # DeepSeek does not support json_schema, use json_mode instead
        if provider == "deepseek":
            logger.debug("Using json_mode for DeepSeek structured output")
            return llm.with_structured_output(self.output_schema, method="json_mode")

        # OpenAI, Anthropic, Google support function_calling/json_schema
        return llm.with_structured_output(self.output_schema, strict=strict)

    def _get_provider_name(self) -> str:
        """
        Get the current LLM provider name.

        Returns:
            Provider name: 'openai', 'anthropic', 'google', or 'deepseek'
        """
        langchain_llm = llm_manager.primary_provider
        if langchain_llm:
            return langchain_llm.provider
        return "unknown"

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute the agent with a task and context."""
        pass

    async def invoke_llm(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> LLMResponse:
        """Invoke the LLM with messages using the global llm_manager."""
        return await llm_manager.chat(
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )

    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context dictionary as string."""
        parts = []

        for key, value in context.items():
            if key == "code_context":
                parts.append(f"### Code Context\n```\n{value}\n```")
            elif key == "previous_stages":
                parts.append(f"### Previous Stage Results\n{value}")
            elif isinstance(value, dict):
                parts.append(f"### {key}\n```json\n{value}\n```")
            else:
                parts.append(f"### {key}\n{value}")

        return "\n\n".join(parts) if parts else ""

    async def prepare_and_chat(
        self,
        task: str,
        context: dict[str, Any],
    ) -> LLMResponse:
        """Prepare messages and invoke LLM."""
        messages = await self.prepare_messages(task, context)
        return await self.invoke_llm(messages)

    async def prepare_messages(
        self,
        task: str,
        context: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Prepare messages for LLM from task and context."""
        messages = []

        # System message
        system_content = self.system_prompt

        if context:
            context_str = self._format_context(context)
            system_content += f"\n\n## Context\n{context_str}"

        messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": task})

        return messages

    def _build_langchain_messages(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> list[BaseMessage]:
        """
        Build LangChain messages for structured output.

        Args:
            task: The task/question to send
            context: Optional context dictionary

        Returns:
            List of LangChain messages (SystemMessage, HumanMessage)
        """
        system_content = self.system_prompt

        if context:
            context_str = self._format_context(context)
            system_content += f"\n\n## Context\n{context_str}"

        return [
            SystemMessage(content=system_content),
            HumanMessage(content=task),
        ]

    async def execute_structured(self, task: str, context: dict[str, Any]) -> BaseModel:
        """
        Execute agent with structured output.

        Uses with_structured_output() to get a Pydantic model directly.

        Args:
            task: The task/question
            context: Optional context

        Returns:
            Parsed Pydantic model matching output_schema

        Raises:
            ValueError: If output_schema is not defined
        """
        if self.output_schema is None:
            raise ValueError(
                f"{self.__class__.__name__} does not define output_schema"
            )

        structured_llm = self._create_structured_llm()
        messages = self._build_langchain_messages(task, context)

        try:
            return await structured_llm.ainvoke(messages)
        except Exception as e:
            logger.error(
                "Structured output failed",
                agent=self.__class__.__name__,
                error=str(e),
            )
            raise
