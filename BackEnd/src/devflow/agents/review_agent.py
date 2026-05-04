"""Code Review Agent with structured output."""

from typing import Any

from devflow.agents.base import BaseAgent, AgentResult
from devflow.models.pipeline import AgentConfig
from devflow.models.execution import CodeArtifact
from devflow.schemas.structured_outputs import (
    ReviewIssueSchema,
    CodeReviewOutput,
)
from devflow.utils.logging import get_logger

logger = get_logger("agent.review")


CODE_REVIEW_SYSTEM_PROMPT = """You are a senior Code Reviewer with expertise in software quality, security, and best practices.

## Review Dimensions

### 1. Correctness
- Does the code implement requirements correctly?
- Are edge cases handled?
- Is the algorithm correct?

### 2. Security
- Potential vulnerabilities?
- Input validation?
- Injection risks?

### 3. Code Quality
- Readability and organization?
- Naming conventions?
- Documentation?

### 4. Performance
- Obvious performance issues?
- Efficiency improvements?

### 5. Best Practices
- Language/framework conventions?
- Error handling?
- Logging?

## Output Requirement

You MUST return your output as a structured JSON object with the schema provided.
Be thorough but constructive. Focus on production-impacting issues.

## Guidelines

- Set verdict to "approve" if no issues found
- Set verdict to "request_changes" if there are critical or high severity issues
- Set verdict to "approve_with_suggestions" if only medium/low severity issues exist
- Each issue should include a clear recommendation for fixing
"""


class CodeReviewAgent(BaseAgent):
    """Agent specialized in code review using structured output.

    This agent uses with_structured_output() to reliably parse LLM responses
    into CodeReviewOutput Pydantic models with structured issue lists.
    """

    @property
    def system_prompt(self) -> str:
        return CODE_REVIEW_SYSTEM_PROMPT

    @property
    def output_schema(self):
        """Define the structured output schema."""
        return CodeReviewOutput

    async def execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute code review with structured output.

        Uses with_structured_output() to get reliable structured data
        with issue lists and verdicts.
        """
        # Enhance task with code to review
        enhanced_task = self._enhance_task(task, context)

        try:
            # Use structured output
            result = await self.execute_structured(enhanced_task, context)

            # Count issues by severity
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for issue in result.issues:
                if issue.severity in severity_counts:
                    severity_counts[issue.severity] += 1

            return AgentResult(
                success=True,
                output={
                    "summary": result.summary,
                    "verdict": result.verdict,
                    "total_issues": len(result.issues),
                    "severity_counts": severity_counts,
                    "strengths": result.strengths,
                    "suggestion": result.suggestion,
                    "issues": [i.model_dump() for i in result.issues],
                },
                artifacts=[],
            )

        except Exception as e:
            logger.error("Code review failed", error=str(e))
            return await self._fallback_execute(task, context)

    def _enhance_task(self, task: str, context: dict[str, Any]) -> str:
        """Enhance task with code context."""
        enhancement_parts = [task]

        # Add code to review
        if code_content := context.get("code_content"):
            enhancement_parts.append(f"\n\n## Code to Review\n```\n{code_content}\n```")

        # Add files to review
        if files := context.get("files"):
            if isinstance(files, list):
                enhancement_parts.append(f"\n\n## Files to Review\n" + "\n".join(f"- {f}" for f in files))

        return "\n".join(enhancement_parts)

    async def _fallback_execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Fallback to simple text generation."""
        from devflow.agents.simple_agent import SimpleAgent

        logger.warning("Falling back to text-based review")

        simple_agent = SimpleAgent(self.config)
        messages = await simple_agent.prepare_messages(task, context)
        response = await simple_agent.invoke_llm(messages)

        return AgentResult(
            success=True,
            output={"response": response.content, "fallback": True},
            artifacts=[],
        )
