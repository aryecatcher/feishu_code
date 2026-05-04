"""Technical Design Agent with structured output."""

from typing import Any

from devflow.agents.base import BaseAgent, AgentResult
from devflow.models.pipeline import AgentConfig
from devflow.schemas.structured_outputs import (
    FileChangeSchema,
    APIEndpointSchema,
    SchemeDesignOutput,
)
from devflow.utils.logging import get_logger

logger = get_logger("agent.scheme")


SCHEME_DESIGN_SYSTEM_PROMPT = """You are a senior Software Architect with expertise in system design and technical decision-making.

Transform structured requirements into comprehensive technical designs.

## Your Responsibilities

1. **Architecture Design**: Define system architecture and components
2. **Technology Selection**: Recommend appropriate technologies
3. **API Design**: Define interfaces with clear contracts
4. **Data Model**: Design database schemas
5. **File Change Analysis**: Identify files to create/modify
6. **Risk Mitigation**: Identify technical risks

## Output Requirement

You MUST return your output as a structured JSON object with the schema provided.
Balance ideal design with practical constraints. Document decisions with rationale.
"""


class SchemeDesignAgent(BaseAgent):
    """Agent specialized in technical design and architecture using structured output.

    This agent uses with_structured_output() to reliably parse LLM responses
    into SchemeDesignOutput Pydantic models.
    """

    @property
    def system_prompt(self) -> str:
        return SCHEME_DESIGN_SYSTEM_PROMPT

    @property
    def output_schema(self):
        """Define the structured output schema."""
        return SchemeDesignOutput

    async def execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute scheme design with structured output."""
        # Enhance task with requirements
        enhanced_task = self._enhance_task(task, context)

        try:
            # Use structured output
            result = await self.execute_structured(enhanced_task, context)

            # Format output
            return AgentResult(
                success=True,
                output={
                    "summary": result.summary,
                    "architecture": result.architecture,
                    "technology_stack": result.technology_stack,
                    "api_design": [a.model_dump() for a in result.api_design],
                    "data_model": result.data_model,
                    "file_changes": [f.model_dump() for f in result.file_changes],
                    "implementation_plan": result.implementation_plan,
                    "risks": result.risks,
                },
                artifacts=[],
            )

        except Exception as e:
            logger.error("Scheme design failed", error=str(e))
            return await self._fallback_execute(task, context)

    def _enhance_task(self, task: str, context: dict[str, Any]) -> str:
        """Enhance task with context."""
        enhancement_parts = [task]

        if requirements := context.get("requirements"):
            enhancement_parts.append(f"\n\n## Requirements\n{requirements}")

        if existing_tech_stack := context.get("existing_tech_stack"):
            enhancement_parts.append(f"\n\n## Existing Tech Stack\n{existing_tech_stack}")

        return "\n".join(enhancement_parts)

    async def _fallback_execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Fallback to simple text generation."""
        from devflow.agents.simple_agent import SimpleAgent

        logger.warning("Falling back to text-based design")

        simple_agent = SimpleAgent(self.config)
        messages = await simple_agent.prepare_messages(task, context)
        response = await simple_agent.invoke_llm(messages)

        return AgentResult(
            success=True,
            output={"response": response.content, "fallback": True},
            artifacts=[],
        )
