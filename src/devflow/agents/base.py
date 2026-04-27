"""Base Agent using LangChain.

All agents use the globally configured LLM provider (set via default_provider in settings).
"""

from abc import ABC, abstractmethod
from typing import Any

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
    """Abstract base class for all agents using LangChain."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._llm = None

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

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
