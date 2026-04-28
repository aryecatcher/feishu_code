"""Execution data models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status for a stage or overall pipeline."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalAction(str, Enum):
    """Human approval actions."""

    APPROVE = "approve"
    REJECT = "reject"
    SKIP = "skip"


class CodeArtifact(BaseModel):
    """A code artifact produced by an agent."""

    file_path: str = Field(description="File path relative to repository root")
    content: str = Field(description="File content or patch")
    change_type: str = Field(
        default="modify",
        description="Type of change: create, modify, delete",
    )
    language: str | None = Field(default=None, description="Programming language")
    description: str | None = Field(default=None, description="Change description")


class StageResult(BaseModel):
    """Result of a stage execution."""

    stage_id: str = Field(description="Stage ID")
    status: ExecutionStatus = Field(description="Execution status")
    output: dict[str, Any] = Field(default_factory=dict, description="Stage output")
    artifacts: list[CodeArtifact] = Field(default_factory=list)
    error: str | None = Field(default=None, description="Error message if failed")
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_seconds: float | None = Field(default=None)

    @property
    def is_success(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.APPROVED,
            ExecutionStatus.REJECTED,
        }


class Checkpoint(BaseModel):
    """Human-in-the-loop checkpoint."""

    id: str = Field(description="Unique checkpoint identifier")
    execution_id: str = Field(description="Execution ID")
    stage_id: str = Field(description="Stage ID")
    stage_result: StageResult = Field(description="Stage result to review")
    status: ExecutionStatus = Field(default=ExecutionStatus.WAITING_APPROVAL)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: datetime | None = Field(default=None)
    decided_by: str | None = Field(default=None, description="Human approver")
    comment: str | None = Field(default=None, description="Approval/rejection comment")
    approval_action: ApprovalAction | None = Field(default=None)

    @property
    def is_pending(self) -> bool:
        return self.status == ExecutionStatus.WAITING_APPROVAL


class Execution(BaseModel):
    """Pipeline execution instance."""

    id: str = Field(description="Unique execution identifier")
    pipeline_id: str = Field(description="Pipeline ID")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Shared execution context",
    )
    results: dict[str, StageResult] = Field(
        default_factory=dict,
        description="Stage execution results keyed by stage_id",
    )
    checkpoints: dict[str, Checkpoint] = Field(
        default_factory=dict,
        description="Checkpoints keyed by stage_id",
    )
    current_stage_id: str | None = Field(default=None)
    error: str | None = Field(default=None, description="Error message if execution failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)

    def get_stage_result(self, stage_id: str) -> StageResult | None:
        """Get result for a specific stage."""
        return self.results.get(stage_id)

    def add_result(self, result: StageResult) -> None:
        """Add or update a stage result."""
        self.results[result.stage_id] = result
        self.updated_at = datetime.utcnow()

    def get_pending_checkpoint(self) -> Checkpoint | None:
        """Get the first pending checkpoint."""
        for checkpoint in self.checkpoints.values():
            if checkpoint.is_pending:
                return checkpoint
        return None

    def get_current_checkpoint(self) -> Checkpoint | None:
        """Get checkpoint for current stage if exists."""
        if self.current_stage_id:
            return self.checkpoints.get(self.current_stage_id)
        return None
