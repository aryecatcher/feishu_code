"""Demand Analysis Agent with structured output."""

from typing import Any

from devflow.agents.base import BaseAgent, AgentResult
from devflow.models.pipeline import AgentConfig
from devflow.schemas.structured_outputs import (
    DemandRequirementSchema,
    DemandAnalysisOutput,
)
from devflow.utils.logging import get_logger

logger = get_logger("agent.demand")


DEMAND_ANALYSIS_SYSTEM_PROMPT = """You are a senior Product Manager and Business Analyst specializing in software requirements analysis.

Transform natural language demand descriptions into structured, actionable requirements.

## Your Responsibilities

1. **Intent Recognition**: Understand the core purpose behind the request
2. **Requirement Extraction**: Identify functional and non-functional requirements
3. **Ambiguity Resolution**: Clarify unclear points with explicit assumptions
4. **Acceptance Criteria**: Define measurable success criteria
5. **Scope Definition**: Clearly outline what's in scope and out of scope

## Output Requirement

You MUST return your output as a structured JSON object with the schema provided.
Be precise, avoid vague language. Think from both user and developer perspectives.

## Guidelines

- Assign unique IDs to each requirement (e.g., FR-001, NFR-001)
- Make acceptance criteria specific and measurable
- List any assumptions you made when interpreting the requirements
- Identify potential risks that could affect implementation
"""


class DemandAnalysisAgent(BaseAgent):
    """Agent specialized in analyzing and structuring demands using structured output.

    This agent uses with_structured_output() to reliably parse LLM responses
    into DemandAnalysisOutput Pydantic models.
    """

    @property
    def system_prompt(self) -> str:
        return DEMAND_ANALYSIS_SYSTEM_PROMPT

    @property
    def output_schema(self):
        """Define the structured output schema."""
        return DemandAnalysisOutput

    async def execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute demand analysis with structured output."""
        try:
            # Use structured output
            result = await self.execute_structured(task, context)

            # Format requirements for output
            requirements = []
            for req in result.requirements:
                requirements.append({
                    "id": req.id,
                    "type": req.type,
                    "title": req.title,
                    "description": req.description,
                    "priority": req.priority,
                    "acceptance_criteria": req.acceptance_criteria,
                })

            return AgentResult(
                success=True,
                output={
                    "summary": result.summary,
                    "requirements": requirements,
                    "scope": result.scope,
                    "questions": result.questions,
                    "assumptions": result.assumptions,
                    "risks": result.risks,
                },
                artifacts=[],
            )

        except Exception as e:
            logger.error("Demand analysis failed", error=str(e))
            return await self._fallback_execute(task, context)

    async def _fallback_execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Fallback to simple text generation."""
        from devflow.agents.simple_agent import SimpleAgent

        logger.warning("Falling back to text-based analysis")

        simple_agent = SimpleAgent(self.config)
        messages = await simple_agent.prepare_messages(task, context)
        response = await simple_agent.invoke_llm(messages)

        return AgentResult(
            success=True,
            output={"response": response.content, "fallback": True},
            artifacts=[],
        )
