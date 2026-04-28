"""Simple agent implementation using LangChain."""

from typing import Any

from devflow.agents.base import BaseAgent, AgentResult
from devflow.models.pipeline import AgentConfig
from devflow.utils.logging import get_logger

logger = get_logger("agent.simple")


class SimpleAgent(BaseAgent):
    """
    Simple agent that makes a single LLM call.

    Suitable for straightforward tasks like:
    - Demand analysis
    - Scheme design
    - Delivery preparation
    """

    async def execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute using a single LLM call."""
        try:
            response = await self.prepare_and_chat(task, context)

            return AgentResult(
                success=True,
                output={"response": response.content},
                artifacts=[],
                tokens_used=response.usage.get("total_tokens", 0) if response.usage else 0,
            )

        except Exception as e:
            logger.error("Agent execution failed", error=str(e))
            return AgentResult(
                success=False,
                error=str(e),
            )

    async def validate_output(self, output: dict[str, Any]) -> bool:
        """Validate agent output."""
        content = output.get("response", "")
        return bool(content and len(content) > 0)
