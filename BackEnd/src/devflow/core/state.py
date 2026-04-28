"""Pipeline State definition for LangGraph."""

from typing import Any, TypedDict

from devflow.models.pipeline import PipelineStatus
from devflow.models.execution import ExecutionStatus, StageResult, Checkpoint


class PipelineState(TypedDict, total=False):
    """State passed through the LangGraph pipeline."""

    # Pipeline metadata
    pipeline_id: str
    execution_id: str

    # Current execution status
    status: ExecutionStatus

    # Execution context (shared across all stages)
    demand_input: str
    context: dict[str, Any]

    # Stage results keyed by stage_id
    results: dict[str, StageResult]

    # Current stage tracking
    current_stage_id: str | None
    stage_history: list[str]

    # Checkpoints
    checkpoints: dict[str, Checkpoint]

    # Human feedback at checkpoints
    checkpoint_feedback: dict[str, str]  # stage_id -> feedback

    # Final output
    final_artifacts: list[dict[str, Any]]

    # Error handling
    error: str | None
    error_stage_id: str | None

    # Metadata
    created_at: str
    updated_at: str


def create_initial_state(
    pipeline_id: str,
    execution_id: str,
    demand_input: str,
) -> PipelineState:
    """Create initial state for a new pipeline execution."""
    from datetime import datetime

    return PipelineState(
        pipeline_id=pipeline_id,
        execution_id=execution_id,
        status=ExecutionStatus.PENDING,
        demand_input=demand_input,
        context={"demand": demand_input},
        results={},
        current_stage_id=None,
        stage_history=[],
        checkpoints={},
        checkpoint_feedback={},
        final_artifacts=[],
        error=None,
        error_stage_id=None,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
