"""Checkpoint API routes - 检查点审批接口"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from devflow.api.schemas import (
    CheckpointApprove,
    CheckpointReject,
    CheckpointResponse,
    CheckpointListResponse,
    CheckpointAllListResponse,
)
from devflow.api.service import pipeline_service
from devflow.models.execution import ExecutionStatus, StageResult, Checkpoint
from devflow.utils.logging import get_logger

logger = get_logger("api.checkpoint")
router = APIRouter(prefix="/checkpoints", tags=["Checkpoint"])


def sync_execution_from_engine(
    execution_id: str,
    engine_result: dict[str, Any],
) -> None:
    """
    将 Engine 执行结果同步到 Execution 记录。

    在 checkpoint 审批后调用，确保 Execution 状态与 Engine 内部状态一致。
    """
    try:
        execution = pipeline_service.get_execution(execution_id)
    except Exception as e:
        logger.error("Failed to get execution for sync", execution_id=execution_id, error=str(e))
        return

    # 同步 results
    for stage_id, result_data in engine_result.get("results", {}).items():
        if isinstance(result_data, dict):
            if stage_id not in execution.results:
                execution.results[stage_id] = StageResult(**result_data)
            else:
                # 更新已存在的 result
                execution.results[stage_id] = StageResult(**result_data)

    # 同步 checkpoints
    for stage_id, cp_data in engine_result.get("checkpoints", {}).items():
        if isinstance(cp_data, dict):
            if stage_id not in execution.checkpoints:
                execution.checkpoints[stage_id] = Checkpoint(**cp_data)
            else:
                # 更新已存在的 checkpoint
                execution.checkpoints[stage_id] = Checkpoint(**cp_data)

    # 同步 current_stage_id
    if engine_result.get("current_stage_id") and len(engine_result["current_stage_id"]) > 0:
        execution.current_stage_id = list(engine_result["current_stage_id"])

    # 同步 status
    result_status = engine_result.get("status")
    if result_status:
        try:
            execution.status = ExecutionStatus(result_status)
        except ValueError:
            logger.warning("Unknown status from engine", status=result_status)

    # 同步 error
    if engine_result.get("error"):
        execution.error = engine_result["error"]

    execution.updated_at = datetime.utcnow()

    logger.info(
        "Execution state synced from engine",
        execution_id=execution_id,
        current_stage=list(execution.current_stage_id or []),
        status=execution.status.value,
        results_count=len(execution.results),
        checkpoints_count=len(execution.checkpoints),
    )


@router.get("", response_model=CheckpointListResponse, summary="查询待审批检查点", description="获取所有待审批的检查点列表")
async def list_pending_checkpoints(
    execution_id: str | None = None,
) -> CheckpointListResponse:
    """
    查询待审批的检查点。

    - **execution_id**: 可选，按执行ID筛选

    只有处于等待审批状态的检查点会出现在列表中。
    """
    checkpoints = pipeline_service.get_pending_checkpoints(execution_id)

    return CheckpointListResponse(
        items=[CheckpointResponse(**c) for c in checkpoints],
        total=len(checkpoints),
        pending=len(checkpoints),
    )


@router.get("/all", response_model=CheckpointAllListResponse, summary="获取所有检查点")
async def list_all_checkpoints(
    execution_id: str | None = None,
    status: str | None = None,
) -> CheckpointAllListResponse:
    """
    获取所有检查点（不限于待审批状态）。

    - **execution_id**: 可选，按执行ID筛选
    - **status**: 可选，按状态筛选 (WAITING_APPROVAL / APPROVED / REJECTED)
    """
    from devflow.models.execution import ExecutionStatus

    checkpoints = pipeline_service.get_all_checkpoints(execution_id, status)

    # 统计
    total = len(checkpoints)
    pending = len([c for c in checkpoints if c.get("status") == ExecutionStatus.WAITING_APPROVAL.value])
    approved = len([c for c in checkpoints if c.get("status") == ExecutionStatus.APPROVED.value])
    rejected = len([c for c in checkpoints if c.get("status") == ExecutionStatus.REJECTED.value])

    # 按状态分组
    by_status = {
        "WAITING_APPROVAL": pending,
        "APPROVED": approved,
        "REJECTED": rejected,
    }

    # 按执行分组
    by_execution: dict[str, int] = {}
    for c in checkpoints:
        exec_id = c.get("execution_id", "unknown")
        by_execution[exec_id] = by_execution.get(exec_id, 0) + 1

    return CheckpointAllListResponse(
        items=[CheckpointResponse(**c) for c in checkpoints],
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected,
        by_status=by_status,
        by_execution=by_execution,
    )


@router.get("/{execution_id}/{stage_id}", response_model=CheckpointResponse, summary="获取检查点详情", description="获取指定执行中特定阶段的检查点信息")
async def get_checkpoint(execution_id: str, stage_id: str) -> CheckpointResponse:
    """
    获取检查点详情。

    - **execution_id**: 执行唯一标识
    - **stage_id**: 阶段标识（如 scheme-design、code-review）

    返回检查点的状态、创建时间、审批人等信息。
    """
    try:
        checkpoints = pipeline_service.get_pending_checkpoints(execution_id)
        for c in checkpoints:
            if c["stage_id"] == stage_id:
                return CheckpointResponse(**c)

        raise HTTPException(
            status_code=404,
            detail=f"Checkpoint not found for execution {execution_id}, stage {stage_id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{execution_id}/{stage_id}/approve", response_model=CheckpointResponse, summary="批准检查点", description="批准检查点以继续流水线执行")
async def approve_checkpoint(
    execution_id: str,
    stage_id: str,
    data: CheckpointApprove,
) -> CheckpointResponse:
    """
    批准检查点。

    - **execution_id**: 执行唯一标识
    - **stage_id**: 阶段标识
    - **comment**: 审批意见（可选）
    - **approver**: 审批人标识（默认 "human"）

    批准后流水线将继续执行下一阶段。
    
    使用 LangGraph interrupt() 模式：
    1. 直接调用 engine.resume() 传入审批数据
    2. engine 内部处理状态更新和回滚逻辑
    """
    from devflow.core.engine import pipeline_engine

    try:
        # 获取 pipeline 信息
        execution = pipeline_service.get_execution(execution_id)
        pipeline = pipeline_service.get_pipeline(execution.pipeline_id)

        # 准备审批数据（传递给 interrupt()）
        approval_data = {
            "action": "approve",
            "comment": data.comment,
            "approver": data.approver,
            "stage_id": stage_id,
        }

        # 调用 resume，engine 内部会更新 checkpoint 状态和处理回滚
        logger.info("Resuming pipeline after approval", execution_id=execution_id, stage_id=stage_id)
        engine_result = await pipeline_engine.resume(
            pipeline, 
            execution_id, 
            resume_value=approval_data
        )

        # 同步 Engine 执行结果到 Execution
        sync_execution_from_engine(execution_id, engine_result)

        # 获取检查点状态
        checkpoint = pipeline_service.get_pending_checkpoints(execution_id)
        for cp in checkpoint:
            if cp["stage_id"] == stage_id:
                return CheckpointResponse(**cp)

        # 如果没有待审批的 checkpoint（可能已通过或回滚），返回空响应
        return CheckpointResponse(
            id="",
            execution_id=execution_id,
            stage_id=stage_id,
            stage_result={},
            status=ExecutionStatus.APPROVED,
            created_at=execution.updated_at,
            decided_at=datetime.utcnow(),
            decided_by=data.approver,
            comment=data.comment,
            approval_action="approved",
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{execution_id}/{stage_id}/reject", response_model=CheckpointResponse, summary="拒绝检查点", description="拒绝检查点并触发回滚")
async def reject_checkpoint(
    execution_id: str,
    stage_id: str,
    data: CheckpointReject,
) -> CheckpointResponse:
    """
    拒绝检查点。

    - **execution_id**: 执行唯一标识
    - **stage_id**: 阶段标识
    - **comment**: 拒绝原因（必填）
    - **rejector**: 拒绝人标识（默认 "human"）

    拒绝后将触发回滚流程。
    
    使用 LangGraph interrupt() 模式：
    1. 直接调用 engine.resume() 传入拒绝数据
    2. engine 内部会清除当前阶段结果并准备重新执行
    """
    from devflow.core.engine import pipeline_engine

    try:
        # 获取 pipeline 信息
        execution = pipeline_service.get_execution(execution_id)
        pipeline = pipeline_service.get_pipeline(execution.pipeline_id)

        # 准备拒绝数据（传递给 interrupt()）
        rejection_data = {
            "action": "reject",
            "comment": data.comment,
            "approver": data.rejector,
            "stage_id": stage_id,
        }

        # 调用 resume，engine 内部会处理回滚逻辑
        logger.info("Resuming pipeline after rejection", execution_id=execution_id, stage_id=stage_id)
        engine_result = await pipeline_engine.resume(
            pipeline, 
            execution_id, 
            resume_value=rejection_data
        )

        # 同步 Engine 执行结果到 Execution
        sync_execution_from_engine(execution_id, engine_result)

        # 获取检查点状态
        checkpoint = pipeline_service.get_pending_checkpoints(execution_id)
        for cp in checkpoint:
            if cp["stage_id"] == stage_id:
                return CheckpointResponse(**cp)

        # 如果回滚后重试，可能没有待审批的 checkpoint
        return CheckpointResponse(
            id="",
            execution_id=execution_id,
            stage_id=stage_id,
            stage_result={},
            status=ExecutionStatus.REJECTED,
            created_at=execution.updated_at,
            decided_at=datetime.utcnow(),
            decided_by=data.rejector,
            comment=data.comment,
            approval_action="rejected",
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}/summary", response_model=dict, summary="获取检查点汇总", description="获取指定执行的所有检查点汇总信息")
async def get_checkpoint_summary(execution_id: str) -> dict:
    """
    获取检查点汇总。

    - **execution_id**: 执行唯一标识

    返回检查点总数、待审批数、已批准数、已拒绝数等统计信息。
    """
    from devflow.core.checkpoint import checkpoint_manager

    try:
        summary = checkpoint_manager.get_checkpoint_summary(execution_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
