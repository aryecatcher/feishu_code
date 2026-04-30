"""Pipeline service for business logic."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from devflow.models.pipeline import Pipeline, PipelineStage, StageType, PipelineStatus, AgentConfig
from devflow.models.execution import Execution, ExecutionStatus
from devflow.agents.factory import AgentFactory
from devflow.core.engine import pipeline_engine
from devflow.core.checkpoint import checkpoint_manager
from devflow.utils.logging import get_logger
from devflow.utils.exceptions import NotFoundError, ValidationError

logger = get_logger("service.pipeline")


class PipelineService:
    """Service for pipeline operations."""

    def __init__(self):
        self._pipelines: dict[str, Pipeline] = {}
        self._executions: dict[str, Execution] = {}
        self._agent_factory = AgentFactory()
        self._default_pipeline_id: str | None = None

    def create_pipeline(self, data: dict[str, Any]) -> Pipeline:
        """Create a new pipeline."""
        pipeline_id = str(uuid4())

        pipeline = Pipeline(
            id=pipeline_id,
            name=data["name"],
            description=data.get("description", ""),
            stages=data["stages"],
        )

        self._pipelines[pipeline_id] = pipeline

        # Register agents for each stage
        for stage in pipeline.stages:
            agent = self._agent_factory.create(stage.stage_type, stage.agent)
            pipeline_engine.register_agent(stage.stage_type, agent)

        logger.info("Pipeline created", pipeline_id=pipeline_id)

        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        """Get a pipeline by ID."""
        if pipeline_id == "default":
            if self._default_pipeline_id and self._default_pipeline_id in self._pipelines:
                return self._pipelines[self._default_pipeline_id]
            raise NotFoundError(
                "No default pipeline set. Please set a default pipeline first.",
                details={"default_pipeline_id": self._default_pipeline_id},
            )

        pipeline = self._pipelines.get(pipeline_id)

        if not pipeline:
            raise NotFoundError(
                f"Pipeline not found: {pipeline_id}",
                details={"pipeline_id": pipeline_id},
            )

        return pipeline

    def list_pipelines(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Pipeline], int]:
        """List all pipelines with pagination."""
        pipelines = list(self._pipelines.values())
        total = len(pipelines)

        start = (page - 1) * page_size
        end = start + page_size

        return pipelines[start:end], total

    def update_pipeline(
        self,
        pipeline_id: str,
        data: dict[str, Any],
    ) -> Pipeline:
        """Update an existing pipeline."""
        pipeline = self.get_pipeline(pipeline_id)

        # 处理 descriptions
        if data.get("descriptions"):
            descriptions = data["descriptions"]
            if isinstance(descriptions, dict):
                if descriptions.get("title"):
                    pipeline.name = descriptions["title"]
                if descriptions.get("content") is not None:
                    pipeline.description = descriptions["content"]

        # 处理 stages (stage_id 列表)
        if data.get("stages"):
            stage_ids = data["stages"]
            # 根据 stage_id 筛选对应的阶段
            updated_stages = [stage for stage in pipeline.stages if stage.id in stage_ids]
            if updated_stages:
                pipeline.stages = updated_stages

        # 处理 config
        if data.get("config") is not None:
            pipeline.metadata = data["config"]

        pipeline.updated_at = datetime.utcnow()

        logger.info("Pipeline updated", pipeline_id=pipeline_id)

        return pipeline

    def delete_pipeline(self, pipeline_id: str) -> None:
        """Delete a pipeline."""
        if pipeline_id not in self._pipelines:
            raise NotFoundError(
                f"Pipeline not found: {pipeline_id}",
                details={"pipeline_id": pipeline_id},
            )

        del self._pipelines[pipeline_id]

        if self._default_pipeline_id == pipeline_id:
            self._default_pipeline_id = None

        logger.info("Pipeline deleted", pipeline_id=pipeline_id)

    def set_default_pipeline(self, pipeline_id: str) -> Pipeline:
        """Set a pipeline as the default pipeline."""
        if pipeline_id not in self._pipelines:
            raise NotFoundError(
                f"Pipeline not found: {pipeline_id}",
                details={"pipeline_id": pipeline_id},
            )

        self._default_pipeline_id = pipeline_id
        logger.info("Default pipeline set", pipeline_id=pipeline_id)

        return self._pipelines[pipeline_id]

    def get_default_pipeline_id(self) -> str | None:
        """Get the default pipeline ID."""
        return self._default_pipeline_id

    def create_execution(
        self,
        pipeline_id: str,
        demand: str,
        config: dict[str, Any] | None = None,
    ) -> Execution:
        """Create and start a pipeline execution."""
        pipeline = self.get_pipeline(pipeline_id)

        execution_id = str(uuid4())

        execution = Execution(
            id=execution_id,
            pipeline_id=pipeline_id,
            status=[ExecutionStatus.PENDING],
            context={"demand": demand, "config": config or {}},
            current_stage_id=[pipeline.stages[0].id] if pipeline.stages else [],
        )

        self._executions[execution_id] = execution

        logger.info(
            "Execution created",
            execution_id=execution_id,
            pipeline_id=pipeline_id,
        )

        return execution

    def get_execution(self, execution_id: str) -> Execution:
        """Get an execution by ID."""
        execution = self._executions.get(execution_id)

        if not execution:
            raise NotFoundError(
                f"Execution not found: {execution_id}",
                details={"execution_id": execution_id},
            )

        return execution

    def get_execution_status(self, execution_id: str) -> dict[str, Any]:
        """Get detailed execution status."""
        execution = self.get_execution(execution_id)
        pipeline = self.get_pipeline(execution.pipeline_id)

        # Calculate progress
        completed_stages = sum(
            1 for r in execution.results.values()
            if r.is_terminal
        )
        total_stages = len(pipeline.stages)
        progress = (completed_stages / total_stages * 100) if total_stages > 0 else 0

        # Get current stage name
        current_stage_name = None
        if execution.current_stage_id and len(execution.current_stage_id) > 0:
            stage = pipeline.get_stage(execution.current_stage_id[0])
            if stage:
                current_stage_name = stage.name

        return {
            "id": execution.id,
            "pipeline_id": execution.pipeline_id,
            "status": execution.status.value,
            "current_stage_id": list(execution.current_stage_id or []),
            "current_stage_name": current_stage_name,
            "progress": progress,
            "results": {
                k: v.model_dump() for k, v in execution.results.items()
            },
            "checkpoints": {
                k: v.model_dump() for k, v in execution.checkpoints.items()
            },
            "error": execution.error,
            "created_at": execution.created_at.isoformat(),
            "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
        }

    def list_executions(
        self,
        pipeline_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Execution], int]:
        """List executions with optional pipeline filter."""
        executions = list(self._executions.values())

        if pipeline_id:
            executions = [e for e in executions if e.pipeline_id == pipeline_id]

        total = len(executions)

        start = (page - 1) * page_size
        end = start + page_size

        return executions[start:end], total

    def approve_checkpoint(
        self,
        execution_id: str,
        stage_id: str,
        comment: str | None = None,
        approver: str = "human",
    ) -> dict[str, Any]:
        """Approve a checkpoint."""
        checkpoint = checkpoint_manager.get_checkpoint_by_stage(execution_id, stage_id)

        if not checkpoint:
            raise NotFoundError(
                f"Checkpoint not found for stage: {stage_id}",
                details={"execution_id": execution_id, "stage_id": stage_id},
            )

        checkpoint_manager.approve(checkpoint.id, approver, comment)

        logger.info(
            "Checkpoint approved via API",
            checkpoint_id=checkpoint.id,
            execution_id=execution_id,
            stage_id=stage_id,
        )

        return checkpoint.model_dump()

    def reject_checkpoint(
        self,
        execution_id: str,
        stage_id: str,
        comment: str,
        rejector: str = "human",
    ) -> dict[str, Any]:
        """Reject a checkpoint."""
        checkpoint = checkpoint_manager.get_checkpoint_by_stage(execution_id, stage_id)

        if not checkpoint:
            raise NotFoundError(
                f"Checkpoint not found for stage: {stage_id}",
                details={"execution_id": execution_id, "stage_id": stage_id},
            )

        checkpoint_manager.reject(checkpoint.id, rejector, comment)

        logger.info(
            "Checkpoint rejected via API",
            checkpoint_id=checkpoint.id,
            execution_id=execution_id,
            stage_id=stage_id,
        )

        return checkpoint.model_dump()

    def get_pending_checkpoints(
        self,
        execution_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get pending checkpoints."""
        checkpoints = checkpoint_manager.get_pending_checkpoints(execution_id)
        return [c.model_dump() for c in checkpoints]

    def cancel_execution(self, execution_id: str) -> Execution:
        """Cancel a running or pending execution."""
        execution = self.get_execution(execution_id)

        if execution.status in {ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED}:
            raise ValidationError(
                f"Cannot cancel execution in status: {execution.status.value}",
                details={"execution_id": execution_id, "status": execution.status.value},
            )

        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        execution.updated_at = datetime.utcnow()

        logger.info("Execution cancelled", execution_id=execution_id)

        return execution

    def pause_execution(self, execution_id: str) -> Execution:
        """Pause a running execution."""
        execution = self.get_execution(execution_id)

        if execution.status != ExecutionStatus.RUNNING:
            raise ValidationError(
                f"Cannot pause execution in status: {execution.status.value}",
                details={"execution_id": execution_id, "status": execution.status.value},
            )

        execution.status = ExecutionStatus.WAITING_APPROVAL
        execution.updated_at = datetime.utcnow()

        logger.info("Execution paused", execution_id=execution_id)

        return execution

    def resume_execution(self, execution_id: str) -> Execution:
        """Resume a paused execution."""
        execution = self.get_execution(execution_id)

        if execution.status != ExecutionStatus.WAITING_APPROVAL:
            raise ValidationError(
                f"Cannot resume execution in status: {execution.status.value}",
                details={"execution_id": execution_id, "status": execution.status.value},
            )

        execution.status = ExecutionStatus.RUNNING
        execution.updated_at = datetime.utcnow()

        logger.info("Execution resumed", execution_id=execution_id)

        return execution


# Global service instance
pipeline_service = PipelineService()


def create_default_pipeline() -> Pipeline:
    """Create the default DevFlow pipeline."""
    stages = [
        PipelineStage(
            id="demand-analysis",
            name="需求分析",
            stage_type=StageType.DEMAND_ANALYSIS,
            description="分析和结构化需求描述",
            agent=AgentConfig(name="DemandAnalyzer"),
            is_checkpoint=False,
        ),
        PipelineStage(
            id="scheme-design",
            name="方案设计",
            stage_type=StageType.SCHEME_DESIGN,
            description="设计技术方案",
            agent=AgentConfig(name="SchemeDesigner"),
            is_checkpoint=True,  # Human-in-the-loop checkpoint
            depends_on=["demand-analysis"],
        ),
        PipelineStage(
            id="code-generation",
            name="代码生成",
            stage_type=StageType.CODE_GENERATION,
            description="生成代码变更",
            agent=AgentConfig(name="CodeGenerator"),
            is_checkpoint=False,
            depends_on=["scheme-design"],
        ),
        PipelineStage(
            id="code-review",
            name="代码评审",
            stage_type=StageType.CODE_REVIEW,
            description="评审代码质量",
            agent=AgentConfig(name="CodeReviewer"),
            is_checkpoint=True,  # Human-in-the-loop checkpoint
            depends_on=["code-generation"],
        ),
        PipelineStage(
            id="delivery",
            name="交付集成",
            stage_type=StageType.DELIVERY,
            description="准备交付物",
            agent=AgentConfig(name="DeliveryEngineer"),
            is_checkpoint=False,
            depends_on=["code-review"],
        ),
    ]

    return pipeline_service.create_pipeline({
        "name": "DevFlow Default Pipeline",
        "description": "标准研发流程: 需求分析 → 方案设计 → 代码生成 → 代码评审 → 交付",
        "stages": stages,
    })
