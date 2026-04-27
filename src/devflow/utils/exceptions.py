"""Custom exceptions for DevFlow Engine."""

from typing import Any


class DevFlowError(Exception):
    """Base exception for all DevFlow errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PipelineError(DevFlowError):
    """Raised when a pipeline operation fails."""
    pass


class StageError(DevFlowError):
    """Raised when a stage execution fails."""
    pass


class AgentError(DevFlowError):
    """Raised when an agent operation fails."""
    pass


class LLMError(DevFlowError):
    """Raised when an LLM operation fails."""
    pass


class ValidationError(DevFlowError):
    """Raised when input validation fails."""
    pass


class NotFoundError(DevFlowError):
    """Raised when a requested resource is not found."""
    pass


class CheckpointError(DevFlowError):
    """Raised when a checkpoint operation fails."""
    pass


class StateError(DevFlowError):
    """Raised when pipeline state is invalid."""
    pass
