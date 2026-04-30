"""Human-in-the-Loop Checkpoint Manager."""

from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

from devflow.models.execution import (
    Execution,
    ExecutionStatus,
    Checkpoint,
    StageResult,
    ApprovalAction,
)
from devflow.utils.logging import get_logger
from devflow.utils.exceptions import CheckpointError, StateError

logger = get_logger("checkpoint")


class CheckpointManager:
    """
    Manages human approval checkpoints in the pipeline.

    Features:
    - Create and track checkpoints
    - Handle approval/rejection actions
    - Support rollback on rejection
    - Notification callbacks
    """

    def __init__(self):
        self._checkpoints: dict[str, Checkpoint] = {}
        self._pending_callbacks: dict[str, list[Callable]] = {}
        self._resolved_callbacks: dict[str, list[Callable]] = {}

    def create_checkpoint(
        self,
        execution_id: str,
        stage_id: str,
        stage_result: StageResult,
    ) -> Checkpoint:
        """Create a new checkpoint for approval."""
        checkpoint_id = str(uuid4())

        checkpoint = Checkpoint(
            id=checkpoint_id,
            execution_id=execution_id,
            stage_id=stage_id,
            stage_result=stage_result,
            status=ExecutionStatus.WAITING_APPROVAL,
            created_at=datetime.utcnow(),
        )

        self._checkpoints[checkpoint_id] = checkpoint

        logger.info(
            "Checkpoint created",
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            stage_id=stage_id,
        )

        self._notify_pending(checkpoint)

        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a checkpoint by ID."""
        return self._checkpoints.get(checkpoint_id)

    def get_checkpoint_by_stage(
        self,
        execution_id: str,
        stage_id: str,
    ) -> Checkpoint | None:
        """Get checkpoint for a specific stage."""
        for checkpoint in self._checkpoints.values():
            if checkpoint.execution_id == execution_id and checkpoint.stage_id == stage_id:
                return checkpoint
        return None

    def upsert_checkpoint(
        self,
        execution_id: str,
        stage_id: str,
        stage_result: StageResult,
    ) -> Checkpoint:
        """
        Create or update a checkpoint idempotently.

        This method is designed to be called after interrupt() returns,
        avoiding duplicate checkpoint creation on node re-execution.
        """
        existing = self.get_checkpoint_by_stage(execution_id, stage_id)

        if existing:
            logger.info(
                "Checkpoint already exists, skipping creation",
                checkpoint_id=existing.id,
                execution_id=execution_id,
                stage_id=stage_id,
            )
            return existing

        return self.create_checkpoint(execution_id, stage_id, stage_result)

    def get_pending_checkpoints(
        self,
        execution_id: str | None = None,
    ) -> list[Checkpoint]:
        """Get all pending checkpoints, optionally filtered by execution."""
        checkpoints = [
            c for c in self._checkpoints.values()
            if c.status == ExecutionStatus.WAITING_APPROVAL
        ]

        if execution_id:
            checkpoints = [
                c for c in checkpoints
                if c.execution_id == execution_id
            ]

        return checkpoints

    def approve(
        self,
        checkpoint_id: str,
        approver: str = "human",
        comment: str | None = None,
    ) -> Checkpoint:
        """Approve a checkpoint."""
        checkpoint = self._checkpoints.get(checkpoint_id)

        if not checkpoint:
            raise CheckpointError(
                f"Checkpoint not found: {checkpoint_id}",
                details={"checkpoint_id": checkpoint_id},
            )

        if checkpoint.status != ExecutionStatus.WAITING_APPROVAL:
            raise CheckpointError(
                f"Checkpoint is not pending approval: {checkpoint.status}",
                details={
                    "checkpoint_id": checkpoint_id,
                    "status": checkpoint.status.value,
                },
            )

        checkpoint.status = ExecutionStatus.APPROVED
        checkpoint.decided_at = datetime.utcnow()
        checkpoint.decided_by = approver
        checkpoint.comment = comment
        checkpoint.approval_action = ApprovalAction.APPROVE

        logger.info(
            "Checkpoint approved",
            checkpoint_id=checkpoint_id,
            approver=approver,
        )

        self._notify_resolved(checkpoint)

        return checkpoint

    def reject(
        self,
        checkpoint_id: str,
        rejector: str = "human",
        comment: str | None = None,
    ) -> Checkpoint:
        """Reject a checkpoint and trigger rollback."""
        checkpoint = self._checkpoints.get(checkpoint_id)

        if not checkpoint:
            raise CheckpointError(
                f"Checkpoint not found: {checkpoint_id}",
                details={"checkpoint_id": checkpoint_id},
            )

        if checkpoint.status != ExecutionStatus.WAITING_APPROVAL:
            raise CheckpointError(
                f"Checkpoint is not pending approval: {checkpoint.status}",
                details={
                    "checkpoint_id": checkpoint_id,
                    "status": checkpoint.status.value,
                },
            )

        checkpoint.status = ExecutionStatus.REJECTED
        checkpoint.decided_at = datetime.utcnow()
        checkpoint.decided_by = rejector
        checkpoint.comment = comment
        checkpoint.approval_action = ApprovalAction.REJECT

        logger.info(
            "Checkpoint rejected",
            checkpoint_id=checkpoint_id,
            rejector=rejector,
            comment=comment,
        )

        self._notify_resolved(checkpoint)

        return checkpoint

    def skip(
        self,
        checkpoint_id: str,
        reason: str = "skipped by admin",
    ) -> Checkpoint:
        """Skip a checkpoint (admin override)."""
        checkpoint = self._checkpoints.get(checkpoint_id)

        if not checkpoint:
            raise CheckpointError(
                f"Checkpoint not found: {checkpoint_id}",
                details={"checkpoint_id": checkpoint_id},
            )

        checkpoint.status = ExecutionStatus.APPROVED
        checkpoint.decided_at = datetime.utcnow()
        checkpoint.decided_by = "admin"
        checkpoint.comment = reason
        checkpoint.approval_action = ApprovalAction.SKIP

        logger.info(
            "Checkpoint skipped",
            checkpoint_id=checkpoint_id,
            reason=reason,
        )

        self._notify_resolved(checkpoint)

        return checkpoint

    def register_pending_callback(
        self,
        execution_id: str,
        callback: Callable[[Checkpoint], None],
    ) -> None:
        """Register a callback for pending checkpoint notifications."""
        if execution_id not in self._pending_callbacks:
            self._pending_callbacks[execution_id] = []
        self._pending_callbacks[execution_id].append(callback)

    def register_resolved_callback(
        self,
        execution_id: str,
        callback: Callable[[Checkpoint], None],
    ) -> None:
        """Register a callback for resolved checkpoint notifications."""
        if execution_id not in self._resolved_callbacks:
            self._resolved_callbacks[execution_id] = []
        self._resolved_callbacks[execution_id].append(callback)

    def _notify_pending(self, checkpoint: Checkpoint) -> None:
        """Notify listeners of pending checkpoint."""
        callbacks = self._pending_callbacks.get(checkpoint.execution_id, [])
        for callback in callbacks:
            try:
                callback(checkpoint)
            except Exception as e:
                logger.error("Callback failed", error=str(e))

    def _notify_resolved(self, checkpoint: Checkpoint) -> None:
        """Notify listeners of resolved checkpoint."""
        callbacks = self._resolved_callbacks.get(checkpoint.execution_id, [])
        for callback in callbacks:
            try:
                callback(checkpoint)
            except Exception as e:
                logger.error("Callback failed", error=str(e))

    def get_checkpoint_summary(self, execution_id: str) -> dict[str, Any]:
        """Get a summary of all checkpoints for an execution."""
        checkpoints = [
            c for c in self._checkpoints.values()
            if c.execution_id == execution_id
        ]

        return {
            "execution_id": execution_id,
            "total": len(checkpoints),
            "pending": len([c for c in checkpoints if c.status == ExecutionStatus.WAITING_APPROVAL]),
            "approved": len([c for c in checkpoints if c.status == ExecutionStatus.APPROVED]),
            "rejected": len([c for c in checkpoints if c.status == ExecutionStatus.REJECTED]),
            "checkpoints": [
                {
                    "id": c.id,
                    "stage_id": c.stage_id,
                    "status": c.status.value,
                    "created_at": c.created_at.isoformat(),
                    "decided_at": c.decided_at.isoformat() if c.decided_at else None,
                    "decided_by": c.decided_by,
                }
                for c in checkpoints
            ],
        }


class CheckpointHandler:
    """
    Handles checkpoint integration with the pipeline engine.

    Provides methods for:
    - Pausing pipeline at checkpoints
    - Resuming after approval
    - Rolling back on rejection
    """

    def __init__(self, checkpoint_manager: CheckpointManager):
        self.manager = checkpoint_manager
        self._execution_states: dict[str, dict[str, Any]] = {}

    def save_execution_state(
        self,
        execution_id: str,
        state: dict[str, Any],
    ) -> None:
        """Save execution state before checkpoint."""
        self._execution_states[execution_id] = dict(state)
        logger.debug("Execution state saved", execution_id=execution_id)

    def get_execution_state(self, execution_id: str) -> dict[str, Any] | None:
        """Get saved execution state."""
        return self._execution_states.get(execution_id)

    def prepare_rollback(
        self,
        execution_id: str,
        target_stage_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Prepare rollback state.

        Args:
            execution_id: The execution to rollback
            target_stage_id: Optional stage to rollback to (default: previous checkpoint)

        Returns:
            Rollback instructions for the pipeline engine
        """
        state = self._execution_states.get(execution_id)

        if not state:
            raise StateError(
                f"No saved state found for execution: {execution_id}",
                details={"execution_id": execution_id},
            )

        # Find previous checkpoint or stage
        if target_stage_id is None:
            # Find the last approved checkpoint before the rejected one
            pending = self.manager.get_pending_checkpoints(execution_id)
            if pending:
                # Get the stage before the pending checkpoint
                target_stage_id = pending[0].stage_id

        rollback_plan = {
            "execution_id": execution_id,
            "target_stage_id": target_stage_id,
            "saved_state": state,
            "action": "rollback",
        }

        logger.info(
            "Rollback prepared",
            execution_id=execution_id,
            target_stage_id=target_stage_id,
        )

        return rollback_plan

    def should_wait_at_checkpoint(
        self,
        execution_id: str,
        stage_id: str,
    ) -> bool:
        """Check if pipeline should wait at a checkpoint."""
        checkpoint = self.manager.get_checkpoint_by_stage(execution_id, stage_id)

        if not checkpoint:
            return False

        return checkpoint.status == ExecutionStatus.WAITING_APPROVAL

    def can_proceed_after_checkpoint(
        self,
        execution_id: str,
        stage_id: str,
    ) -> tuple[bool, str]:
        """
        Check if pipeline can proceed after a checkpoint.

        Returns:
            (can_proceed, reason)
        """
        checkpoint = self.manager.get_checkpoint_by_stage(execution_id, stage_id)

        if not checkpoint:
            return True, "No checkpoint found"

        if checkpoint.status == ExecutionStatus.WAITING_APPROVAL:
            return False, "Awaiting human approval"

        if checkpoint.status == ExecutionStatus.REJECTED:
            return False, "Checkpoint rejected - rollback required"

        if checkpoint.status == ExecutionStatus.APPROVED:
            return True, "Checkpoint approved"

        return False, f"Unknown checkpoint status: {checkpoint.status}"


# Global checkpoint manager instance
checkpoint_manager = CheckpointManager()
checkpoint_handler = CheckpointHandler(checkpoint_manager)
