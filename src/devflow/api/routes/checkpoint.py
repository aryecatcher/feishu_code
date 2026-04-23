"""Checkpoint API routes - 检查点审批接口"""

from fastapi import APIRouter, HTTPException

from devflow.api.schemas import (
    CheckpointApprove,
    CheckpointReject,
    CheckpointResponse,
    CheckpointListResponse,
)
from devflow.api.service import pipeline_service
from devflow.utils.logging import get_logger

logger = get_logger("api.checkpoint")
router = APIRouter(prefix="/checkpoints", tags=["Checkpoint"])


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
    """
    try:
        checkpoint = pipeline_service.approve_checkpoint(
            execution_id=execution_id,
            stage_id=stage_id,
            comment=data.comment,
            approver=data.approver,
        )
        return CheckpointResponse(**checkpoint)
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
    """
    try:
        checkpoint = pipeline_service.reject_checkpoint(
            execution_id=execution_id,
            stage_id=stage_id,
            comment=data.comment,
            rejector=data.rejector,
        )
        return CheckpointResponse(**checkpoint)
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
