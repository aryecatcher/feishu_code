"""Pipeline Engine - LangGraph based workflow orchestration."""

from datetime import datetime
from typing import Any, Callable
from uuid import uuid4

from langgraph.graph import StateGraph, END

from devflow.core.state import PipelineState, create_initial_state
from devflow.models.pipeline import Pipeline, PipelineStage, StageType
from devflow.models.execution import Execution, ExecutionStatus, StageResult, Checkpoint
from devflow.agents.base import BaseAgent, AgentResult
from devflow.utils.logging import get_logger
from devflow.utils.exceptions import PipelineError, StageError

logger = get_logger("engine")


class PipelineEngine:
    """
    LangGraph-based pipeline engine for orchestrating AI agents.

    Handles:
    - Pipeline compilation and execution
    - Stage state management
    - Human-in-the-loop checkpoints
    - Error handling and recovery
    """

    def __init__(self):
        self._graphs: dict[str, StateGraph] = {}
        self._compiled: dict[str, Any] = {}
        self._executors: dict[str, BaseAgent] = {}

    def register_agent(self, stage_type: StageType, agent: BaseAgent) -> None:
        """Register an agent for a specific stage type."""
        self._executors[stage_type.value] = agent
        logger.info("Registered agent", stage_type=stage_type.value)

    def get_agent(self, stage_type: StageType) -> BaseAgent | None:
        """Get the registered agent for a stage type."""
        return self._executors.get(stage_type.value)

    def build_graph(
        self,
        pipeline: Pipeline,
        stage_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> StateGraph:
        """Build a LangGraph from pipeline definition."""
        graph = StateGraph(PipelineState)

        # Add nodes for each stage
        for stage in pipeline.stages:
            stage_id = stage.id

            # Create node function for this stage
            def make_stage_node(s: PipelineStage, callback):
                async def stage_node(state: PipelineState) -> dict[str, Any]:
                    return await self._execute_stage(s, state, callback)
                return stage_node

            graph.add_node(stage_id, make_stage_node(stage, stage_callback))

        # Add checkpoint handler node (for processing approval status)
        async def checkpoint_handler(state: PipelineState) -> dict[str, Any]:
            """Handle checkpoint approval check."""
            return await self._handle_checkpoint(state)

        graph.add_node("checkpoint_handler", checkpoint_handler)

        # Simple sequential edges between stages
        for i, stage in enumerate(pipeline.stages):
            if i + 1 < len(pipeline.stages):
                next_stage = pipeline.stages[i + 1]
                graph.add_edge(stage.id, next_stage.id)
            else:
                # Last stage -> checkpoint_handler -> END
                graph.add_edge(stage.id, "checkpoint_handler")

        # After checkpoint handler, go to END
        graph.add_edge("checkpoint_handler", END)

        # Set entry point
        if pipeline.stages:
            graph.set_entry_point(pipeline.stages[0].id)
        else:
            graph.set_entry_point(END)

        return graph

    async def _execute_stage(
        self,
        stage: PipelineStage,
        state: PipelineState,
        stage_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Execute a single stage."""
        from datetime import datetime as dt

        logger.info(
            "Starting _execute_stage",
            stage_id=stage.id,
            stage_type=stage.stage_type.value,
            current_state_status=state.get("status"),
        )

        # Get agent for this stage
        agent = self.get_agent(stage.stage_type)
        if not agent:
            raise StageError(
                f"No agent registered for stage type: {stage.stage_type.value}",
                details={"stage_id": stage.id, "stage_type": stage.stage_type.value},
            )

        # Prepare input context
        context = self._prepare_stage_context(stage, state)

        # Execute agent
        start_time = dt.utcnow()
        try:
            result = await agent.execute(
                task=context["task"],
                context=context["context"],
            )

            end_time = dt.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Build stage result
            stage_result = StageResult(
                stage_id=stage.id,
                status=ExecutionStatus.COMPLETED,
                output=result.output,
                artifacts=result.artifacts,
                started_at=start_time,
                completed_at=end_time,
                duration_seconds=duration,
            )

            logger.info(
                "Stage completed",
                stage_id=stage.id,
                duration=duration,
            )

        except Exception as e:
            end_time = dt.utcnow()
            duration = (end_time - start_time).total_seconds()

            logger.error("Stage failed", stage_id=stage.id, error=str(e))

            stage_result = StageResult(
                stage_id=stage.id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                started_at=start_time,
                completed_at=end_time,
                duration_seconds=duration,
            )

        # Build new state - handle status based on checkpoint
        new_status = ExecutionStatus.WAITING_APPROVAL if stage.is_checkpoint else ExecutionStatus.RUNNING

        new_state = {
            "current_stage_id": stage.id,
            "status": new_status,
            f"result_{stage.id}": stage_result.model_dump(),
        }

        # Merge results
        results = dict(state.get("results", {}))
        results[stage.id] = stage_result.model_dump()
        new_state["results"] = results

        # Update stage history
        history = list(state.get("stage_history", []))
        if stage.id not in history:
            history.append(stage.id)
        new_state["stage_history"] = history

        # Handle checkpoint creation
        if stage.is_checkpoint:
            checkpoint = Checkpoint(
                id=str(uuid4()),
                execution_id=state["execution_id"],
                stage_id=stage.id,
                stage_result=stage_result,
                status=ExecutionStatus.WAITING_APPROVAL,
            )
            checkpoints = dict(state.get("checkpoints", {}))
            checkpoints[stage.id] = checkpoint.model_dump()
            new_state["checkpoints"] = checkpoints

        new_state["updated_at"] = dt.utcnow().isoformat()

        # Trigger callback if provided
        if stage_callback:
            try:
                stage_callback(stage.id, new_state)
            except Exception as e:
                logger.warning("Stage callback failed", stage_id=stage.id, error=str(e))

        return new_state

    def _prepare_stage_context(
        self,
        stage: PipelineStage,
        state: PipelineState,
    ) -> dict[str, Any]:
        """Prepare context for a stage execution."""
        task = ""
        context = dict(state.get("context", {}))

        # Get previous stage results for context
        previous_results = []
        for s_result in state.get("results", {}).values():
            previous_results.append(s_result)

        # Build task description based on stage type
        if stage.stage_type == StageType.DEMAND_ANALYSIS:
            task = f"Analyze the following demand and create a structured specification:\n\n{state.get('demand_input', '')}"
            context["previous_stages"] = []

        elif stage.stage_type == StageType.SCHEME_DESIGN:
            demand_result = state.get("results", {}).get(stage.depends_on[0] if stage.depends_on else "")
            task = f"Design a technical scheme based on the demand analysis:\n\n{demand_result.get('output', {}).get('content', '') if demand_result else state.get('demand_input', '')}"
            context["previous_stages"] = previous_results

        elif stage.stage_type == StageType.CODE_GENERATION:
            scheme_result = state.get("results", {}).get(stage.depends_on[0] if stage.depends_on else "")
            task = f"Generate code based on the technical scheme:\n\n{scheme_result.get('output', {}).get('content', '') if scheme_result else ''}"
            context["previous_stages"] = previous_results

        elif stage.stage_type == StageType.CODE_REVIEW:
            code_result = state.get("results", {}).get(stage.depends_on[0] if stage.depends_on else "")
            task = f"Review the generated code:\n\n{code_result.get('output', {}).get('content', '') if code_result else ''}"
            context["previous_stages"] = previous_results

        elif stage.stage_type == StageType.DELIVERY:
            review_result = state.get("results", {}).get(stage.depends_on[0] if stage.depends_on else "")
            task = f"Prepare for delivery:\n\n{review_result.get('output', {}).get('content', '') if review_result else ''}"
            context["previous_stages"] = previous_results

        return {"task": task, "context": context}

    async def _handle_checkpoint(self, state: PipelineState) -> dict[str, Any]:
        """Handle checkpoint waiting for human approval."""
        current_id = state.get("current_stage_id")
        if not current_id:
            return {}

        checkpoint = state.get("checkpoints", {}).get(current_id)
        if not checkpoint:
            return {}

        # Check approval status
        if checkpoint.get("status") == ExecutionStatus.APPROVED.value:
            return {"status": ExecutionStatus.RUNNING}
        elif checkpoint.get("status") == ExecutionStatus.REJECTED.value:
            return {
                "status": ExecutionStatus.RUNNING,
                "checkpoint_feedback": checkpoint.get("comment", ""),
            }

        # Still waiting
        return {"status": ExecutionStatus.WAITING_APPROVAL}

    def _is_checkpoint_approved(self, state: PipelineState) -> bool:
        """Check if current checkpoint is approved."""
        current_id = state.get("current_stage_id")
        if not current_id:
            return True

        checkpoint = state.get("checkpoints", {}).get(current_id)
        if not checkpoint:
            return True

        return checkpoint.get("status") == ExecutionStatus.APPROVED.value

    async def execute(
        self,
        pipeline: Pipeline,
        demand: str,
        execution_id: str | None = None,
        stage_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> PipelineState:
        """Execute a pipeline with the given demand input."""
        execution_id = execution_id or str(uuid4())

        logger.info(
            "Starting pipeline execution",
            pipeline_id=pipeline.id,
            execution_id=execution_id,
        )

        # Create initial state
        initial_state = create_initial_state(
            pipeline_id=pipeline.id,
            execution_id=execution_id,
            demand_input=demand,
        )

        logger.info("Initial state created", initial_state=initial_state)

        # Build graph if not cached (with callback if provided)
        cache_key = f"{pipeline.id}:{stage_callback is not None}"
        if cache_key not in self._compiled or stage_callback is not None:
            graph = self.build_graph(pipeline, stage_callback)
            self._compiled[cache_key] = graph.compile()
            self._graphs[pipeline.id] = graph
            logger.info("Graph built and compiled", pipeline_id=pipeline.id)

        # Execute
        compiled_graph = self._compiled[cache_key]

        try:
            result = await compiled_graph.ainvoke(initial_state)

            logger.info(
                "Pipeline execution completed",
                pipeline_id=pipeline.id,
                execution_id=execution_id,
                status=result.get("status"),
            )

            return result

        except Exception as e:
            logger.error(
                "Pipeline execution failed",
                pipeline_id=pipeline.id,
                execution_id=execution_id,
                error=str(e),
            )
            raise PipelineError(
                f"Pipeline execution failed: {e}",
                details={"pipeline_id": pipeline.id, "execution_id": execution_id},
            )

    async def execute_async(
        self,
        pipeline: Pipeline,
        demand: str,
        execution_id: str | None = None,
        callback: Callable[[PipelineState], None] | None = None,
        stage_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> str:
        """Execute pipeline asynchronously, returns execution_id."""
        execution_id = execution_id or str(uuid4())

        async def run():
            result = await self.execute(pipeline, demand, execution_id, stage_callback)
            if callback:
                callback(result)

        import asyncio
        asyncio.create_task(run())

        return execution_id

    def get_execution_status(self, execution_id: str) -> PipelineState | None:
        """Get current status of an execution (from cache)."""
        # In a real implementation, this would query the database
        return None


# Global engine instance
pipeline_engine = PipelineEngine()
