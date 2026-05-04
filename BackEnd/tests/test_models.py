"""Unit tests for pipeline models."""

import pytest
from datetime import datetime

from devflow.models.pipeline import (
    Pipeline,
    PipelineStage,
    StageType,
    PipelineStatus,
    AgentConfig,
)
from devflow.models.execution import (
    Execution,
    ExecutionStatus,
    StageResult,
    Checkpoint,
    CodeArtifact,
)


class TestPipelineModels:
    """Tests for pipeline models."""

    def test_pipeline_creation(self):
        """Test pipeline creation."""
        pipeline = Pipeline(
            id="test-pipeline",
            name="Test Pipeline",
            description="A test pipeline",
            stages=[],
        )

        assert pipeline.id == "test-pipeline"
        assert pipeline.name == "Test Pipeline"
        assert pipeline.status == PipelineStatus.CREATED

    def test_pipeline_get_stage(self):
        """Test getting a stage by ID."""
        stages = [
            PipelineStage(
                id="stage-1",
                name="Stage 1",
                stage_type=StageType.DEMAND_ANALYSIS,
                description="",
                agent=AgentConfig(name="Agent"),
            ),
            PipelineStage(
                id="stage-2",
                name="Stage 2",
                stage_type=StageType.SCHEME_DESIGN,
                description="",
                agent=AgentConfig(name="Agent"),
            ),
        ]

        pipeline = Pipeline(
            id="test",
            name="Test",
            description="",
            stages=stages,
        )

        stage = pipeline.get_stage("stage-1")
        assert stage is not None
        assert stage.name == "Stage 1"

        stage = pipeline.get_stage("non-existent")
        assert stage is None

    def test_pipeline_get_next_stage(self):
        """Test getting the next stage."""
        stages = [
            PipelineStage(
                id="stage-1",
                name="Stage 1",
                stage_type=StageType.DEMAND_ANALYSIS,
                description="",
                agent=AgentConfig(name="Agent"),
            ),
            PipelineStage(
                id="stage-2",
                name="Stage 2",
                stage_type=StageType.SCHEME_DESIGN,
                description="",
                agent=AgentConfig(name="Agent"),
            ),
        ]

        pipeline = Pipeline(
            id="test",
            name="Test",
            description="",
            stages=stages,
        )

        next_stage = pipeline.get_next_stage(["stage-1"])
        assert next_stage is not None
        assert next_stage.id == "stage-2"

        next_stage = pipeline.get_next_stage(["stage-2"])
        assert next_stage is None

    def test_pipeline_get_checkpoint_stages(self):
        """Test getting checkpoint stages."""
        stages = [
            PipelineStage(
                id="stage-1",
                name="Stage 1",
                stage_type=StageType.DEMAND_ANALYSIS,
                description="",
                agent=AgentConfig(name="Agent"),
                is_checkpoint=False,
            ),
            PipelineStage(
                id="stage-2",
                name="Stage 2",
                stage_type=StageType.SCHEME_DESIGN,
                description="",
                agent=AgentConfig(name="Agent"),
                is_checkpoint=True,
            ),
        ]

        pipeline = Pipeline(
            id="test",
            name="Test",
            description="",
            stages=stages,
        )

        checkpoints = pipeline.get_checkpoint_stages()
        assert len(checkpoints) == 1
        assert checkpoints[0].id == "stage-2"


class TestExecutionModels:
    """Tests for execution models."""

    def test_execution_creation(self):
        """Test execution creation."""
        execution = Execution(
            id="test-execution",
            pipeline_id="test-pipeline",
        )

        assert execution.id == "test-execution"
        assert execution.status == [ExecutionStatus.PENDING]

    def test_execution_add_result(self):
        """Test adding stage results."""
        execution = Execution(
            id="test",
            pipeline_id="test",
        )

        result = StageResult(
            stage_id="stage-1",
            status=ExecutionStatus.COMPLETED,
            output={"content": "test output"},
        )

        execution.add_result(result)

        retrieved = execution.get_stage_result("stage-1")
        assert retrieved is not None
        assert retrieved.stage_id == "stage-1"
        assert retrieved.output["content"] == "test output"

    def test_execution_get_pending_checkpoint(self):
        """Test getting pending checkpoint."""
        execution = Execution(
            id="test",
            pipeline_id="test",
            checkpoints={
                "stage-1": Checkpoint(
                    id="cp-1",
                    execution_id="test",
                    stage_id="stage-1",
                    stage_result=StageResult(
                        stage_id="stage-1",
                        status=ExecutionStatus.COMPLETED,
                    ),
                    status=ExecutionStatus.WAITING_APPROVAL,
                ),
            },
        )

        pending = execution.get_pending_checkpoint()
        assert pending is not None
        assert pending.stage_id == "stage-1"

    def test_stage_result_is_terminal(self):
        """Test stage result terminal states."""
        result = StageResult(
            stage_id="test",
            status=ExecutionStatus.COMPLETED,
        )
        assert result.is_terminal

        result = StageResult(
            stage_id="test",
            status=ExecutionStatus.RUNNING,
        )
        assert not result.is_terminal


class TestCodeArtifact:
    """Tests for code artifact model."""

    def test_code_artifact_creation(self):
        """Test code artifact creation."""
        artifact = CodeArtifact(
            file_path="src/main.py",
            content="print('hello')",
            change_type="create",
            language="python",
        )

        assert artifact.file_path == "src/main.py"
        assert artifact.change_type == "create"
        assert artifact.language == "python"
