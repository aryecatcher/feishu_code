"""Agent data models."""

from typing import Any

from pydantic import BaseModel, Field


class AgentOutput(BaseModel):
    """Output from an agent execution."""

    content: str = Field(description="Agent's textual response")
    artifacts: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Structured artifacts (code, files, etc.)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    usage: dict[str, int] | None = Field(
        default=None,
        description="Token usage information",
    )

    def get_artifacts_by_type(self, artifact_type: str) -> list[dict[str, Any]]:
        """Get artifacts filtered by type."""
        return [a for a in self.artifacts if a.get("type") == artifact_type]


class AgentMessage(BaseModel):
    """A message in agent conversation."""

    role: str = Field(description="Role: system, user, or assistant")
    content: str = Field(description="Message content")
    name: str | None = Field(default=None)


class AgentState(BaseModel):
    """Agent execution state."""

    task: str = Field(description="Current task description")
    context: dict[str, Any] = Field(default_factory=dict)
    history: list[AgentMessage] = Field(default_factory=list)
    current_stage: str | None = Field(default=None)
    iteration: int = Field(default=0)
    max_iterations: int = Field(default=10)
    tools_used: list[str] = Field(default_factory=list)
