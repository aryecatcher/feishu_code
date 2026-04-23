"""API Schemas for request/response validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from devflow.models.pipeline import PipelineStage, StageType, PipelineStatus
from devflow.models.execution import ExecutionStatus, Checkpoint


class BaseResponse(BaseModel):
    """Base response model with datetime serialization."""

    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
        ser_json_bytes="utf8",
    )


# ============ Pipeline Schemas ============

class PipelineCreate(BaseResponse):
    """Request to create a new pipeline."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    stages: list[PipelineStage] = Field(..., min_length=1)


class PipelineUpdate(BaseResponse):
    """Request to update a pipeline."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    stages: list[PipelineStage] | None = None


class PipelineResponse(BaseResponse):
    """Pipeline response."""

    id: str
    name: str
    description: str
    stages: list[PipelineStage]
    status: PipelineStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineListResponse(BaseResponse):
    """List of pipelines."""

    items: list[PipelineResponse]
    total: int
    page: int
    page_size: int


# ============ Execution Schemas ============

class ExecutionCreate(BaseModel):
    """Request to create and start an execution."""

    pipeline_id: str = Field(..., description="Pipeline ID to execute")
    demand: str = Field(..., description="Demand/requirement description")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution configuration",
    )


class TestRunRequest(BaseModel):
    """Request for test-run endpoint."""

    pipeline_id: str = Field(..., description="Pipeline ID to execute")
    demand: str = Field(..., description="Demand/requirement description")
    output_dir: str = Field(
        default="output",
        description="Output directory for generated files",
    )


class ExecutionResponse(BaseResponse):
    """Execution response."""

    id: str
    pipeline_id: str
    status: ExecutionStatus
    current_stage_id: str | None
    results: dict[str, Any] = Field(default_factory=dict)
    checkpoints: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime | None
    completed_at: datetime | None


class ExecutionStatusResponse(BaseResponse):
    """Detailed execution status."""

    id: str
    pipeline_id: str
    status: ExecutionStatus
    current_stage_id: str | None
    current_stage_name: str | None
    progress: float = Field(description="Progress percentage 0-100")
    results: dict[str, Any]
    checkpoints: dict[str, Any]
    error: str | None
    created_at: datetime
    updated_at: datetime | None


# ============ Checkpoint Schemas ============

class CheckpointApprove(BaseModel):
    """Request to approve a checkpoint."""

    comment: str | None = Field(default=None, description="Optional approval comment")
    approver: str = Field(default="human", description="Approver identifier")


class CheckpointReject(BaseModel):
    """Request to reject a checkpoint."""

    comment: str = Field(..., description="Rejection reason (required)")
    rejector: str = Field(default="human", description="Rejector identifier")


class CheckpointResponse(BaseResponse):
    """Checkpoint response."""

    id: str
    execution_id: str
    stage_id: str
    stage_result: dict[str, Any]
    status: ExecutionStatus
    created_at: datetime
    decided_at: datetime | None
    decided_by: str | None
    comment: str | None
    approval_action: str | None


class CheckpointListResponse(BaseResponse):
    """List of checkpoints."""

    items: list[CheckpointResponse]
    total: int
    pending: int


# ============ Stage Schemas ============

class StageResultResponse(BaseModel):
    """Stage execution result."""

    stage_id: str
    stage_name: str
    status: ExecutionStatus
    output: dict[str, Any]
    artifacts: list[dict[str, Any]]
    error: str | None
    duration_seconds: float | None
    started_at: datetime | None
    completed_at: datetime | None


# ============ Health Schemas ============

class HealthResponse(BaseResponse):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime
    services: dict[str, bool] = Field(default_factory=dict)


# ============ Error Schemas ============

class ErrorResponse(BaseResponse):
    """Error response."""

    error: str
    detail: str | None = None
    code: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
