"""Pipeline data models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StageType(str, Enum):
    """Pipeline stage types."""

    DEMAND_ANALYSIS = "demand_analysis"
    SCHEME_DESIGN = "scheme_design"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DELIVERY = "delivery"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentConfig(BaseModel):
    """Agent configuration for a stage."""

    name: str = Field(description="Agent name")
    system_prompt: str = Field(default="", description="System prompt for the agent")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    tools: list[str] = Field(default_factory=list, description="Available tools")


class PipelineStage(BaseModel):
    """A single stage in the pipeline."""

    id: str = Field(description="Unique stage identifier")
    name: str = Field(description="Stage display name")
    stage_type: StageType = Field(description="Stage type")
    description: str = Field(description="Stage description")
    agent: AgentConfig = Field(description="Agent configuration")
    is_checkpoint: bool = Field(
        default=False,
        description="Whether this stage requires human approval",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Stage IDs this stage depends on",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific configuration",
    )


class Pipeline(BaseModel):
    """Pipeline definition."""

    id: str = Field(description="Unique pipeline identifier")
    name: str = Field(description="Pipeline name")
    description: str = Field(description="Pipeline description")
    stages: list[PipelineStage] = Field(description="Ordered list of stages")
    status: PipelineStatus = Field(
        default=PipelineStatus.CREATED,
        description="Pipeline status",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}

    def get_stage(self, stage_id: str) -> PipelineStage | None:
        """Get a stage by ID."""
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None

    def get_next_stage(self, current_stage_id: list[str]) -> PipelineStage | None:
        """Get the next stage after the current one."""
        for i, stage in enumerate(self.stages):
            if stage.id == current_stage_id[0] and i + 1 < len(self.stages):
                return self.stages[i + 1]
        return None

    def get_checkpoint_stages(self) -> list[PipelineStage]:
        """Get all checkpoint stages."""
        return [stage for stage in self.stages if stage.is_checkpoint]
