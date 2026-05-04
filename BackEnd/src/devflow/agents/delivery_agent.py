"""Delivery Agent with structured output."""

from typing import Any

from devflow.agents.base import BaseAgent, AgentResult
from devflow.models.pipeline import AgentConfig
from devflow.schemas.structured_outputs import (
    DeploymentStepSchema,
    DeliveryOutput,
)
from devflow.utils.logging import get_logger

logger = get_logger("agent.delivery")


DELIVERY_SYSTEM_PROMPT = """You are a Release Engineer responsible for preparing and packaging code for delivery.

## Your Responsibilities

1. **Change Summary**: Clear summary of all changes
2. **Documentation**: Ensure documentation is updated
3. **Package Preparation**: Prepare artifacts for deployment
4. **Rollback Plan**: Document rollback procedures
5. **Deployment Guide**: Step-by-step deployment instructions

## Output Requirement

You MUST return your output as a structured JSON object with the schema provided.
Be thorough - assume minimal context. Include all commands and configurations.
"""


class DeliveryAgent(BaseAgent):
    """Agent specialized in delivery preparation using structured output.

    This agent uses with_structured_output() to reliably parse LLM responses
    into DeliveryOutput Pydantic models.
    """

    @property
    def system_prompt(self) -> str:
        return DELIVERY_SYSTEM_PROMPT

    @property
    def output_schema(self):
        """Define the structured output schema."""
        return DeliveryOutput

    async def execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute delivery preparation with structured output."""
        # Enhance task with changes info
        enhanced_task = self._enhance_task(task, context)

        try:
            # Use structured output
            result = await self.execute_structured(enhanced_task, context)

            # Format output
            return AgentResult(
                success=True,
                output={
                    "summary": result.summary,
                    "changes": result.changes,
                    "deployment_steps": [s.model_dump() for s in result.deployment_steps],
                    "rollback_plan": result.rollback_plan,
                    "verification_commands": result.verification_commands,
                    "checklist": result.checklist,
                },
                artifacts=[],
            )

        except Exception as e:
            logger.error("Delivery preparation failed", error=str(e))
            return await self._fallback_execute(task, context)

    def _enhance_task(self, task: str, context: dict[str, Any]) -> str:
        """Enhance task with context."""
        enhancement_parts = [task]

        if changed_files := context.get("changed_files"):
            if isinstance(changed_files, list):
                enhancement_parts.append(
                    "\n\n## Changed Files\n" + "\n".join(f"- {f}" for f in changed_files)
                )

        if deployment_env := context.get("deployment_environment"):
            enhancement_parts.append(f"\n\n## Target Environment\n{deployment_env}")

        return "\n".join(enhancement_parts)

    async def _fallback_execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Fallback to simple text generation."""
        from devflow.agents.simple_agent import SimpleAgent

        logger.warning("Falling back to text-based delivery")

        simple_agent = SimpleAgent(self.config)
        messages = await simple_agent.prepare_messages(task, context)
        response = await simple_agent.invoke_llm(messages)

        return AgentResult(
            success=True,
            output={"response": response.content, "fallback": True},
            artifacts=[],
        )
