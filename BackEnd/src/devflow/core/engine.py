"""Pipeline Engine - LangGraph based workflow orchestration."""

from datetime import datetime
from typing import Any, Callable
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.types import Command

from devflow.core.state import PipelineState, create_initial_state
from devflow.models.pipeline import Pipeline, PipelineStage, StageType
from devflow.models.execution import Execution, ExecutionStatus, StageResult, Checkpoint
from devflow.agents.base import BaseAgent, AgentResult
from devflow.utils.logging import get_logger
from devflow.utils.exceptions import PipelineError, StageError
from devflow.core.checkpoint import checkpoint_manager

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
        self._checkpointers: dict[str, MemorySaver] = {}  # Per pipeline checkpointer

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

        # Store pipeline reference for use in nested functions
        self._current_pipeline = pipeline

        # Add nodes for each stage
        for stage in pipeline.stages:
            stage_id = stage.id

            def make_stage_node(s: PipelineStage, callback, engine_self):
                async def stage_node(state: PipelineState) -> dict[str, Any]:
                    return await engine_self._execute_stage(s, state, callback)
                return stage_node

            graph.add_node(stage_id, make_stage_node(stage, stage_callback, self))

        # Checkpoint handler - checks status and decides what to do next
        async def checkpoint_handler(state: PipelineState) -> dict[str, Any]:
            """
            Handle checkpoint status check.

            This node runs after each checkpoint stage completes.
            It checks the checkpoint status from checkpoint_manager and
            returns instructions for the routing function.

            Returns:
                - checkpoint_status: Current status (APPROVED/REJECTED/WAITING)
                - rejection_comment: The rejection reason if REJECTED
            """
            current_id = state.get("current_stage_id")
            if not current_id:
                logger.warning("checkpoint_handler: no current_stage_id in state")
                return {"checkpoint_status": "", "rejection_comment": ""}

            cp_in_state = state.get("checkpoints", {}).get(current_id)
            if not cp_in_state:
                logger.warning(
                    "checkpoint_handler: no checkpoint in state for stage",
                    stage_id=current_id,
                )
                return {"checkpoint_status": "", "rejection_comment": ""}

            # Get latest status from checkpoint_manager
            checkpoint_id = cp_in_state.get("id")
            latest_checkpoint = checkpoint_manager.get_checkpoint(checkpoint_id)

            if not latest_checkpoint:
                logger.warning(
                    "checkpoint_handler: checkpoint not found in manager",
                    checkpoint_id=checkpoint_id,
                )
                return {"checkpoint_status": "", "rejection_comment": ""}

            status = latest_checkpoint.status.value
            rejection_comment = latest_checkpoint.comment if status == ExecutionStatus.REJECTED.value else ""

            logger.info(
                "Checkpoint handler processing",
                checkpoint_id=checkpoint_id,
                status=status,
                current_stage=current_id,
            )

            return {
                "checkpoint_status": status,
                "rejection_comment": rejection_comment,
            }

        graph.add_node("checkpoint_handler", checkpoint_handler)

        # Rollback handler - clears current stage results for re-execution
        async def rollback_handler(state: PipelineState) -> dict[str, Any]:
            """
            Handle checkpoint rejection: prepare state for re-executing the current stage.
            
            This clears:
            - The current stage's result (so it will be re-executed)
            - The checkpoint (so a new one will be created)
            
            And preserves:
            - Previous stage results
            - The rejection feedback for the agent to see
            """
            current_id = state.get("current_stage_id")
            rejection_comment = state.get("rejection_comment", "")

            if not current_id:
                return {}

            logger.info(
                "Rollback handler: preparing for re-execution",
                stage=current_id,
                feedback=rejection_comment,
            )

            # Clear results from current stage onwards
            new_results = {}
            found_current = False
            for stage in self._current_pipeline.stages:
                if stage.id == current_id:
                    found_current = True
                elif found_current:
                    # Skip - don't include results after current stage
                    pass
                else:
                    # Keep results from previous stages
                    if stage.id in state.get("results", {}):
                        new_results[stage.id] = state["results"][stage.id]

            # Clear checkpoints from current stage onwards
            new_checkpoints = {}
            for stage_id, cp in state.get("checkpoints", {}).items():
                # Keep checkpoints only from stages before current
                if stage_id != current_id:
                    new_checkpoints[stage_id] = cp

            return {
                "results": new_results,
                "checkpoints": new_checkpoints,
                "status": ExecutionStatus.RUNNING,
                "checkpoint_feedback": rejection_comment,
            }

        graph.add_node("rollback_handler", rollback_handler)

        # Routing: checkpoint_handler decides where to go next
        def checkpoint_routing(state: PipelineState) -> str:
            """
            Route based on checkpoint status (read live from checkpoint_manager).

            WAITING_APPROVAL -> END (wait for external approval via API)
            APPROVED -> next stage
            REJECTED -> rollback_handler
            """
            current_id = state.get("current_stage_id")
            if not current_id:
                return END

            cp_in_state = state.get("checkpoints", {}).get(current_id)
            if not cp_in_state:
                return END

            # Read live status from checkpoint_manager, not from saved state
            checkpoint_id = cp_in_state.get("id")
            latest_checkpoint = checkpoint_manager.get_checkpoint(checkpoint_id)
            if not latest_checkpoint:
                return END

            status = latest_checkpoint.status.value

            if status == ExecutionStatus.WAITING_APPROVAL.value:
                # Checkpoint waiting for approval - end this execution
                # External API will call resume() after approve/reject
                logger.info("Checkpoint waiting for approval, pausing execution")
                return END

            elif status == ExecutionStatus.APPROVED.value:
                # Find next stage
                for i, stage in enumerate(self._current_pipeline.stages):
                    if stage.id == current_id and i + 1 < len(self._current_pipeline.stages):
                        return self._current_pipeline.stages[i + 1].id
                return END

            elif status == ExecutionStatus.REJECTED.value:
                # Rejected -> rollback and retry
                return "rollback_handler"

            return END

        # Routing after rollback_handler
        def rollback_routing(state: PipelineState) -> str:
            """
            After rollback, go back to current stage for re-execution.
            """
            current_id = state.get("current_stage_id")
            if current_id:
                return current_id
            return END

        # Build routing maps
        checkpoint_routing_map = {s.id: s.id for s in pipeline.stages}
        checkpoint_routing_map["rollback_handler"] = "rollback_handler"
        checkpoint_routing_map[END] = END

        rollback_routing_map = {s.id: s.id for s in pipeline.stages}
        rollback_routing_map[END] = END

        # Add conditional edges from checkpoint_handler
        graph.add_conditional_edges(
            "checkpoint_handler",
            checkpoint_routing,
            checkpoint_routing_map,
        )

        # Add conditional edges from rollback_handler
        graph.add_conditional_edges(
            "rollback_handler",
            rollback_routing,
            rollback_routing_map,
        )

        # Add edges based on checkpoint configuration
        for i, stage in enumerate(pipeline.stages):
            if i + 1 < len(pipeline.stages):
                next_stage = pipeline.stages[i + 1]
                if stage.is_checkpoint:
                    # Checkpoint stages go through checkpoint_handler first
                    graph.add_edge(stage.id, "checkpoint_handler")
                else:
                    graph.add_edge(stage.id, next_stage.id)
            else:
                # Last stage -> checkpoint_handler -> END
                graph.add_edge(stage.id, "checkpoint_handler")

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

        current_id = state.get("current_stage_id")

        logger.info(
            "Starting _execute_stage",
            stage_id=stage.id,
            stage_type=stage.stage_type.value,
            current_state_status=state.get("status"),
            is_retry=stage.id == current_id,
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

        # If this is a retry (same stage as before), add the feedback to task
        checkpoint_feedback = state.get("checkpoint_feedback", "")
        task = context["task"]

        if checkpoint_feedback and stage.id == current_id:
            logger.info(
                "Adding checkpoint feedback to task",
                stage_id=stage.id,
                feedback_length=len(checkpoint_feedback),
            )
            task = f"""Previous attempt was rejected. Please review the feedback and revise your work accordingly:

=== Rejection Feedback ===
{checkpoint_feedback}
=======================

Original Task:
{task}"""
            context["task"] = task
            context["checkpoint_feedback"] = checkpoint_feedback

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

        # Handle checkpoint creation - register with checkpoint_manager for API access
        if stage.is_checkpoint:
            checkpoint = checkpoint_manager.create_checkpoint(
                execution_id=state["execution_id"],
                stage_id=stage.id,
                stage_result=stage_result,
            )
            # Also store in state for pipeline engine use
            checkpoints = dict(state.get("checkpoints", {}))
            checkpoints[stage.id] = checkpoint.model_dump()
            new_state["checkpoints"] = checkpoints

        new_state["updated_at"] = dt.utcnow().isoformat()

        # Clear checkpoint_feedback after using it (don't let it leak to other stages)
        new_state["checkpoint_feedback"] = ""

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
        # Use pipeline.id as sole key for checkpointer to ensure resume() can find it
        cache_key = pipeline.id
        if cache_key not in self._compiled:
            graph = self.build_graph(pipeline, stage_callback)
            # Use MemorySaver checkpointer for interrupt support
            checkpointer = MemorySaver()
            self._compiled[cache_key] = graph.compile(checkpointer=checkpointer)
            self._graphs[pipeline.id] = graph
            self._checkpointers[cache_key] = checkpointer  # Save for resume
            logger.info("Graph built and compiled with checkpointer", pipeline_id=pipeline.id)

        # Execute
        compiled_graph = self._compiled[cache_key]

        # Config with thread_id for checkpointer to persist state
        config = {"configurable": {"thread_id": execution_id}}

        try:
            # ainvoke executes the graph until checkpoint or completion
            result = await compiled_graph.ainvoke(initial_state, config)

            # Check if execution reached a checkpoint (waiting for approval)
            if result and result.get("status") == ExecutionStatus.WAITING_APPROVAL:
                logger.info(
                    "Pipeline execution paused at checkpoint",
                    pipeline_id=pipeline.id,
                    execution_id=execution_id,
                    current_stage=result.get("current_stage_id"),
                )
                # Return current state - caller can check for pending checkpoints
                # External API will call resume() after approve/reject
                return result

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

    async def resume(
        self,
        pipeline: Pipeline,
        execution_id: str,
        resume_value: Any = None,
        stage_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> PipelineState:
        """
        Resume a paused pipeline execution after checkpoint approval/rejection.

        Args:
            pipeline: The pipeline being executed
            execution_id: The execution ID (same as thread_id)
            resume_value: Not used - approval status is read from checkpoint_manager
            stage_callback: Optional callback for stage updates

        Returns:
            The final pipeline state after resume
        """
        logger.info(
            "Resuming pipeline execution",
            pipeline_id=pipeline.id,
            execution_id=execution_id,
            resume_value=resume_value,
        )

        # Use the same checkpointer instance that was used for the initial run
        cache_key = pipeline.id
        checkpointer = self._checkpointers.get(cache_key)
        if not checkpointer:
            logger.warning(
                "Checkpointer not found, creating new one",
                pipeline_id=pipeline.id,
            )
            checkpointer = MemorySaver()

        graph = self.build_graph(pipeline, stage_callback)
        compiled_graph = graph.compile(checkpointer=checkpointer)

        # Config with same thread_id to resume from saved state
        config = {"configurable": {"thread_id": execution_id}}

        # Resume execution - force starting from checkpoint_handler to check approval status
        result = {}
        async for chunk in compiled_graph.astream(
            Command(goto="checkpoint_handler"),
            config,
        ):
            logger.info("[astream CHUNK]", chunk=chunk)
            
            # Aggregate all chunk data into result
            if isinstance(chunk, dict):
                for node_name, node_data in chunk.items():
                    if node_name in ("checkpoint_handler", "rollback_handler", "__end__"):
                        # These nodes return status updates, merge into result
                        if isinstance(node_data, dict):
                            result.update(node_data)
                    else:
                        # Stage node - this is what we need for callback
                        if isinstance(node_data, dict) and stage_callback:
                            try:
                                stage_callback(node_name, node_data)
                                logger.info("Stage callback triggered via resume", node_name=node_name)
                            except Exception as e:
                                logger.warning("Stage callback failed in resume", node_name=node_name, error=str(e))
                        # Also aggregate stage results
                        if isinstance(node_data, dict):
                            for key, value in node_data.items():
                                if key not in result or key in ("results", "checkpoints"):
                                    result[key] = value

        # Also read the latest state directly from checkpointer to ensure we have the most up-to-date data
        try:
            saved_state = checkpointer.get(config)
            if saved_state and saved_state.get("channel_values"):
                channel_values = saved_state["channel_values"]
                # Merge checkpoint data if available
                if "checkpoints" in channel_values and isinstance(channel_values["checkpoints"], dict):
                    result["checkpoints"] = channel_values["checkpoints"]
                if "results" in channel_values and isinstance(channel_values["results"], dict):
                    result["results"] = channel_values["results"]
                if "current_stage_id" in channel_values:
                    result["current_stage_id"] = channel_values["current_stage_id"]
                if "status" in channel_values:
                    result["status"] = channel_values["status"]
                logger.info("Read latest state from checkpointer", 
                           results_keys=list(channel_values.get("results", {}).keys()) if isinstance(channel_values.get("results"), dict) else [])
        except Exception as e:
            logger.warning("Failed to read state from checkpointer", error=str(e))

        logger.info(
            "Pipeline execution resumed and completed",
            pipeline_id=pipeline.id,
            execution_id=execution_id,
            status=result.get("status"),
            results_keys=list(result.get("results", {}).keys()) if isinstance(result.get("results"), dict) else [],
        )

        return result

    def get_execution_status(self, execution_id: str) -> PipelineState | None:
        """Get current status of an execution (from cache)."""
        # In a real implementation, this would query the database
        return None


# Global engine instance
pipeline_engine = PipelineEngine()
