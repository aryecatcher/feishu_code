"""Pipeline Engine - LangGraph based workflow orchestration."""

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command

from devflow.core.state import PipelineState, create_initial_state
from devflow.models.pipeline import Pipeline, PipelineStage, StageType
from devflow.models.execution import ExecutionStatus, StageResult
from devflow.agents.base import BaseAgent, AgentResult
from devflow.utils.logging import get_logger
from devflow.utils.exceptions import PipelineError, StageError
from devflow.core.checkpoint import checkpoint_manager

logger = get_logger("engine")


class PipelineEngine:
    """
    LangGraph-based pipeline engine for orchestrating AI agents.

    Uses the official LangGraph dual-node pattern for checkpoint approval:
    - Stage Node: Executes the agent
    - Approval Node: Handles interrupt() and approval/rejection flow

    Key features:
    - interrupt() is called at the beginning of the approval node
    - Side effects (checkpoint creation) happen after interrupt()
    - Command(goto=...) is used for routing after approval/rejection
    """

    def __init__(self):
        self._graphs: dict[str, StateGraph] = {}
        self._compiled: dict[str, Any] = {}
        self._executors: dict[str, BaseAgent] = {}
        self._checkpointers: dict[str, MemorySaver] = {}
        self._current_pipeline: Pipeline | None = None

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
        stage_callback: Any = None,
    ) -> StateGraph:
        """
        Build a LangGraph from pipeline definition.

        Uses dual-node pattern for checkpoint stages:
        - stage_id: Executes the agent
        - stage_id_approval: Handles interrupt() and approval flow
        """
        graph = StateGraph(PipelineState)

        self._current_pipeline = pipeline

        for i, stage in enumerate(pipeline.stages):
            stage_id = stage.id

            if stage.is_checkpoint:
                next_stage_id = pipeline.stages[i + 1].id if i + 1 < len(pipeline.stages) else None
                stage_node = self._make_stage_node(stage, stage_callback)
                approval_node = self._make_approval_node(stage, next_stage_id)

                graph.add_node(stage_id, stage_node)
                graph.add_node(f"{stage_id}_approval", approval_node)
            else:
                stage_node = self._make_stage_node(stage, stage_callback)
                graph.add_node(stage_id, stage_node)

        edges = self._build_edges(pipeline)
        for src, dst in edges:
            graph.add_edge(src, dst)

        if pipeline.stages:
            graph.set_entry_point(pipeline.stages[0].id)
        else:
            graph.set_entry_point(END)

        return graph

    def _build_edges(self, pipeline: Pipeline) -> list[tuple[str, str]]:
        """
        Build edges for the graph.

        For checkpoint stages, approval_node routing is controlled via Command(goto=...)
        in _handle_approval, so we don't add static edges from approval nodes.
        The approval node itself will decide where to route based on the approval decision.
        """
        edges = []
        for i, stage in enumerate(pipeline.stages):
            if stage.is_checkpoint:
                # Static edge: stage -> approval_node
                # Dynamic routing: approval_node -> next/retry/END handled by Command(goto=...)
                edges.append((stage.id, f"{stage.id}_approval"))
            else:
                # Non-checkpoint stage: linear flow
                if i + 1 < len(pipeline.stages):
                    edges.append((stage.id, pipeline.stages[i + 1].id))
                else:
                    edges.append((stage.id, END))
        return edges

    def _make_stage_node(
        self,
        stage: PipelineStage,
        stage_callback: Any,
    ):
        """Create a node function for stage execution."""
        async def stage_node(state: PipelineState) -> dict[str, Any]:
            return await self._execute_stage(stage, state, stage_callback)
        return stage_node

    def _make_approval_node(self, stage: PipelineStage, next_stage_id: str | None):
        """
        Create a node function for checkpoint approval.

        This follows the official LangGraph pattern:
        1. interrupt() at the beginning (for pause)
        2. Side effect (upsert_checkpoint) after interrupt
        3. Command(goto=...) for routing based on approval/rejection

        Routing logic:
        - Approve: goto next_stage_id (or END if last stage)
        - Reject: goto stage.id (retry current stage)
        - Unknown action: goto next_stage_id (default to approve)
        """
        async def approval_node(state: PipelineState) -> Command[Literal]:
            return await self._handle_approval(stage, state, next_stage_id)
        return approval_node

    async def _execute_stage(
        self,
        stage: PipelineStage,
        state: PipelineState,
        stage_callback: Any = None,
    ) -> dict[str, Any]:
        """Execute a single stage (agent execution only)."""
        from datetime import datetime as dt

        current_id = list(state.get("current_stage_id") or [])
        is_retry = stage.id in current_id
        logger.info(
            "Starting stage execution",
            stage_id=stage.id,
            stage_type=stage.stage_type.value,
            is_retry=is_retry,
        )

        agent = self.get_agent(stage.stage_type)
        if not agent:
            raise StageError(
                f"No agent registered for stage type: {stage.stage_type.value}",
                details={"stage_id": stage.id, "stage_type": stage.stage_type.value},
            )

        context = self._prepare_stage_context(stage, state)
        task = context["task"]

        if checkpoint_feedback := state.get("checkpoint_feedback"):
            # 在重试场景下，checkpoint_feedback 会被设置，此时将拒绝原因注入任务
            if stage.id in current_id:
                logger.info(
                    "Adding checkpoint feedback to task",
                    stage_id=stage.id,
                    feedback_length=len(checkpoint_feedback),
                )
                task = f"""Previous attempt was rejected. Please review the feedback and revise:

=== Rejection Feedback ===
{checkpoint_feedback}
=======================

Original Task:
{task}"""
                context["task"] = task

        start_time = dt.utcnow()
        try:
            result = await agent.execute(
                task=context["task"],
                context=context["context"],
            )

            end_time = dt.utcnow()
            duration = (end_time - start_time).total_seconds()

            stage_result = StageResult(
                stage_id=stage.id,
                status=ExecutionStatus.COMPLETED,
                output=result.output,
                artifacts=result.artifacts,
                started_at=start_time,
                completed_at=end_time,
                duration_seconds=duration,
            )

            logger.info("Stage completed", stage_id=stage.id, duration=duration)

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

        new_state = {
            "current_stage_id": [stage.id],
            "status": [ExecutionStatus.RUNNING],
            f"result_{stage.id}": stage_result.model_dump(mode="json"),
        }

        results = dict(state.get("results", {}))
        results[stage.id] = stage_result.model_dump(mode="json")
        new_state["results"] = results

        history = list(state.get("stage_history", []))
        if stage.id not in history:
            history.append(stage.id)
        new_state["stage_history"] = history

        new_state["updated_at"] = dt.utcnow().isoformat()

        if stage_callback:
            try:
                stage_callback(stage.id, new_state)
            except Exception as e:
                logger.warning("Stage callback failed", stage_id=stage.id, error=str(e))

        return new_state

    async def _handle_approval(
        self,
        stage: PipelineStage,
        state: PipelineState,
        next_stage_id: str | None,
    ) -> Command[Literal]:
        """
        Handle checkpoint approval/rejection.

        Follows official LangGraph interrupt pattern:
        1. interrupt() is called first - pauses execution
        2. On resume, interrupt() returns the approval data
        3. upsert_checkpoint is called after interrupt (idempotent)
        4. Command(goto=...) routes based on approval/rejection

        Routing:
        - Approve: goto next_stage_id (or END if this is the last stage)
        - Reject: goto stage.id (retry current stage)
        - Unknown action: default to approve (goto next_stage_id or END)
        """
        from datetime import datetime as dt

        stage_result = state.get("results", {}).get(stage.id)
        if not stage_result:
            raise StageError(
                f"No result found for stage: {stage.id}",
                details={"stage_id": stage.id},
            )

        interrupt_payload = {
            "type": "checkpoint_approval",
            "execution_id": state["execution_id"],
            "stage_id": stage.id,
            "stage_name": stage.name,
            "stage_result": stage_result,
        }

        logger.info(
            "Calling interrupt() for checkpoint approval",
            stage_id=stage.id,
        )

        approval_data = interrupt(interrupt_payload)

        logger.info(
            "interrupt() returned",
            stage_id=stage.id,
            has_value=approval_data is not None,
        )

        stage_result_obj = StageResult(**stage_result)

        checkpoint = checkpoint_manager.upsert_checkpoint(
            execution_id=state["execution_id"],
            stage_id=stage.id,
            stage_result=stage_result_obj,
        )

        # 序列化 checkpoint 为 JSON 兼容的格式，避免状态合并冲突
        checkpoint_dump = checkpoint.model_dump(mode="json")

        new_state = {
            "pending_checkpoint": checkpoint_dump,
            "updated_at": dt.utcnow().isoformat(),
        }

        if not approval_data:
            logger.info(
                "No approval data (first call), waiting for resume",
                stage_id=stage.id,
            )
            return {**new_state, "status": [ExecutionStatus.WAITING_APPROVAL]}

        action = approval_data.get("action")
        comment = approval_data.get("comment", "")
        actor = approval_data.get("actor", "human")

        logger.info(
            "Processing approval decision",
            stage_id=stage.id,
            action=action,
        )

        if action == "approve":
            checkpoint_manager.approve(
                checkpoint_id=checkpoint.id,
                approver=actor,
                comment=comment,
            )
            logger.info(
                "Checkpoint approved, proceeding to next stage",
                stage_id=stage.id,
                next_stage=next_stage_id,
                checkpoint_id=checkpoint.id,
            )
            return Command(
                goto=next_stage_id or END,
                update={
                    **new_state,
                    "status": [ExecutionStatus.RUNNING],
                    "pending_checkpoint": None,
                    "checkpoint_status": "approved",
                },
            )

        elif action == "reject":
            checkpoint_manager.reject(
                checkpoint_id=checkpoint.id,
                rejector=actor,
                comment=comment,
            )
            logger.info(
                "Checkpoint rejected, will retry stage",
                stage_id=stage.id,
                checkpoint_id=checkpoint.id,
            )
            return Command(
                goto=stage.id,
                update={
                    **new_state,
                    "status": [ExecutionStatus.REJECTED],
                    "checkpoint_feedback": comment,
                    "pending_checkpoint": None,
                    "checkpoint_status": "rejected",
                },
            )

        else:
            logger.warning(
                "Unknown approval action, defaulting to approve",
                action=action,
            )
            return Command(
                goto=next_stage_id or END,
                update={
                    **new_state,
                    "status": [ExecutionStatus.RUNNING],
                    "pending_checkpoint": None,
                    "checkpoint_status": "approved",
                },
            )

    def _prepare_stage_context(
        self,
        stage: PipelineStage,
        state: PipelineState,
    ) -> dict[str, Any]:
        """Prepare context for a stage execution."""
        task = ""
        context = dict(state.get("context", {}))

        previous_results = []
        for s_result in state.get("results", {}).values():
            previous_results.append(s_result)

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

    async def execute(
        self,
        pipeline: Pipeline,
        demand: str,
        execution_id: str | None = None,
        stage_callback: Any = None,
    ) -> PipelineState:
        """Execute a pipeline with the given demand input."""
        execution_id = execution_id or str(uuid4())

        logger.info(
            "Starting pipeline execution",
            pipeline_id=pipeline.id,
            execution_id=execution_id,
        )

        initial_state = create_initial_state(
            pipeline_id=pipeline.id,
            execution_id=execution_id,
            demand_input=demand,
        )

        logger.info("Initial state created")

        cache_key = pipeline.id
        if cache_key not in self._compiled:
            graph = self.build_graph(pipeline, stage_callback)
            checkpointer = MemorySaver()
            self._compiled[cache_key] = graph.compile(checkpointer=checkpointer)
            self._graphs[pipeline.id] = graph
            self._checkpointers[cache_key] = checkpointer
            logger.info("Graph built and compiled with checkpointer", pipeline_id=pipeline.id)

        compiled_graph = self._compiled[cache_key]
        config = {"configurable": {"thread_id": execution_id}}

        try:
            result = await compiled_graph.ainvoke(initial_state, config)

            if result and ExecutionStatus.WAITING_APPROVAL in (result.get("status") or []):
                logger.info(
                    "Pipeline paused at checkpoint",
                    pipeline_id=pipeline.id,
                    execution_id=execution_id,
                    current_stage=result.get("current_stage_id") or [],
                )
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
        callback: Any = None,
        stage_callback: Any = None,
    ) -> str:
        """Execute pipeline asynchronously, returns execution_id."""
        import asyncio

        execution_id = execution_id or str(uuid4())

        async def run():
            result = await self.execute(pipeline, demand, execution_id, stage_callback)
            if callback:
                callback(result)

        asyncio.create_task(run())
        return execution_id

    async def resume(
        self,
        pipeline: Pipeline,
        execution_id: str,
        resume_value: dict[str, Any] | None = None,
        stage_callback: Any = None,
    ) -> PipelineState:
        """
        Resume a paused pipeline execution.

        Uses Command(resume=...) to pass approval data to interrupt().
        """
        logger.info(
            "Resuming pipeline execution",
            pipeline_id=pipeline.id,
            execution_id=execution_id,
            resume_value=resume_value,
        )

        cache_key = pipeline.id
        checkpointer = self._checkpointers.get(cache_key)

        if not checkpointer:
            logger.warning("Checkpointer not found, creating new one")
            checkpointer = MemorySaver()

        if cache_key not in self._compiled:
            graph = self.build_graph(pipeline, stage_callback)
            compiled_graph = graph.compile(checkpointer=checkpointer)
            self._compiled[cache_key] = compiled_graph
            self._checkpointers[cache_key] = checkpointer
        else:
            compiled_graph = self._compiled[cache_key]

        config = {"configurable": {"thread_id": execution_id}}

        result = None
        try:
            async for chunk in compiled_graph.astream(Command(resume=resume_value), config):
                logger.debug("[astream CHUNK]", chunk=chunk)

                if isinstance(chunk, dict):
                    for node_name, node_data in chunk.items():
                        if node_name == "__end__":
                            continue

                        if isinstance(node_data, dict) and stage_callback:
                            try:
                                stage_callback(node_name, node_data)
                            except Exception as e:
                                logger.warning("Stage callback failed", node_name=node_name, error=str(e))

                        if isinstance(node_data, dict):
                            result = node_data

            if result is None:
                final_state = compiled_graph.get_state(config)
                if final_state and final_state.values:
                    result = final_state.values

        except Exception as e:
            logger.error(
                "Pipeline resume failed",
                pipeline_id=pipeline.id,
                execution_id=execution_id,
                error=str(e),
            )
            raise PipelineError(
                f"Pipeline resume failed: {e}",
                details={"pipeline_id": pipeline.id, "execution_id": execution_id},
            )

        logger.info(
            "Pipeline resumed",
            pipeline_id=pipeline.id,
            execution_id=execution_id,
            status=result.get("status") if isinstance(result, dict) else None,
        )

        return result if isinstance(result, dict) else {}

    def get_execution_status(self, execution_id: str) -> PipelineState | None:
        """Get current status of an execution (from cache)."""
        return None


pipeline_engine = PipelineEngine()
