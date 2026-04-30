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


# ============ PipelineConfig Schemas ============

class Descriptions(BaseResponse):
    """流水线描述，文字描述该模板"""

    content: str | None = Field(default=None, description="详情")
    title: str = Field(..., description="标题")


class Stages(BaseResponse):
    """流水线阶段配置，连接各阶段StageID"""

    stage_id: str = Field(..., description="阶段编号")


class PipelineConfigResponse(BaseResponse):
    """PipelineConfig 响应格式"""

    config: dict[str, Any] | None = Field(default=None, description="额外配置")
    descriptions: Descriptions = Field(..., description="流水线描述，文字描述该模板")
    pipeline_id: str | None = Field(default=None, description="流水线编号，用于绑定模板")
    stages: list[Stages] = Field(..., description="流水线阶段配置，连接各阶段StageID")


class PipelineUpdate(BaseResponse):
    """Request to update a pipeline."""

    descriptions: Descriptions | None = None
    stages: list[str] | None = None
    config: dict[str, Any] | None = None


class SetDefaultPipelineRequest(BaseModel):
    """Request to set a pipeline as default."""

    pipeline_id: str = Field(..., description="Pipeline ID to set as default")


class DefaultPipelineResponse(BaseResponse):
    """Response for default pipeline info."""

    default_pipeline_id: str | None
    default_pipeline: "PipelineConfigResponse | None" = None


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
    status: list[ExecutionStatus]
    current_stage_id: list[str]
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
    current_stage_id: list[str]
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


class CheckpointAllListResponse(BaseResponse):
    """所有检查点的响应（包含统计信息）"""

    items: list[CheckpointResponse] = Field(description="检查点列表")
    total: int = Field(description="总数")
    pending: int = Field(description="待审批数")
    approved: int = Field(description="已批准数")
    rejected: int = Field(description="已拒绝数")
    by_status: dict[str, int] = Field(description="按状态分组的数量")
    by_execution: dict[str, int] = Field(description="按执行分组的数量")


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
