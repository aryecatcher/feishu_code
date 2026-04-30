"""Execution API routes - 执行管理接口"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query

from devflow.api.schemas import (
    ExecutionCreate,
    ExecutionResponse,
    ExecutionStatusResponse,
    TestRunRequest,
)
from devflow.api.service import pipeline_service, create_default_pipeline
from devflow.core.engine import pipeline_engine
from devflow.utils.logging import get_logger
from devflow.utils.exceptions import NotFoundError, ValidationError

logger = get_logger("api.execution")
router = APIRouter(prefix="/executions", tags=["Execution"])


async def run_pipeline(execution_id: str, pipeline_id: str, demand: str) -> None:
    """后台任务：运行流水线"""
    import traceback
    from devflow.models.execution import ExecutionStatus, StageResult, Checkpoint

    logger.info("run_pipeline started", execution_id=execution_id, pipeline_id=pipeline_id)

    try:
        # 更新状态为 running
        execution = pipeline_service.get_execution(execution_id)
        execution.status = ExecutionStatus.RUNNING
        execution.updated_at = datetime.utcnow()

        pipeline = pipeline_service.get_pipeline(pipeline_id)
        logger.info("Starting pipeline execution", execution_id=execution_id, pipeline_id=pipeline_id)

        # Stage 完成时的回调，同步状态到 execution
        def sync_stage_callback(stage_id: str, state: dict[str, Any]) -> None:
            """每个 stage 完成后同步状态到 execution"""
            try:
                ex = pipeline_service.get_execution(execution_id)
                ex.current_stage_id = state.get("current_stage_id") or []
                ex.updated_at = datetime.utcnow()

                # 同步已完成阶段的结果
                for sid, result_data in state.get("results", {}).items():
                    if sid not in ex.results:
                        ex.results[sid] = StageResult(**result_data)

                # 同步 checkpoints
                for sid, cp_data in state.get("checkpoints", {}).items():
                    if sid not in ex.checkpoints:
                        ex.checkpoints[sid] = Checkpoint(**cp_data)

                logger.info("Stage state synced", execution_id=execution_id, stage_id=stage_id)
            except Exception as e:
                logger.warning("Failed to sync stage state", execution_id=execution_id, stage_id=stage_id, error=str(e))

        result = await pipeline_engine.execute(
            pipeline,
            demand,
            execution_id=execution_id,
            stage_callback=sync_stage_callback,
        )

        # 同步 engine 返回的最终结果到 execution
        # 注意：需要检查 result.status 以判断是正常完成还是暂停在 checkpoint
        execution.results = {
            stage_id: StageResult(**stage_data)
            for stage_id, stage_data in result.get("results", {}).items()
        }
        execution.checkpoints = {
            stage_id: Checkpoint(**cp_data)
            for stage_id, cp_data in result.get("checkpoints", {}).items()
        }
        execution.current_stage_id = (result.get("current_stage_id") or [])
        
        # 根据 engine 返回的状态判断实际执行状态
        result_status_list = result.get("status") or []
        if ExecutionStatus.WAITING_APPROVAL in result_status_list:
            # 执行暂停在 checkpoint 等待审批
            execution.status = ExecutionStatus.WAITING_APPROVAL
        else:
            # 正常完成
            execution.status = ExecutionStatus.COMPLETED
            
        execution.updated_at = datetime.utcnow()

        logger.info("Pipeline execution completed", execution_id=execution_id, final_status=execution.status.value)
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error("Pipeline execution failed", execution_id=execution_id, error=error_detail)
        # 更新状态为 failed
        try:
            execution = pipeline_service.get_execution(execution_id)
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.updated_at = datetime.utcnow()
        except Exception:
            pass


@router.post("", response_model=ExecutionResponse, status_code=201, summary="创建并启动执行", description="创建新的执行任务并异步启动流水线")
async def create_execution(
    data: ExecutionCreate,
    background_tasks: BackgroundTasks,
) -> ExecutionResponse:
    """
    创建并启动执行。

    - **pipeline_id**: 流水线ID（使用 "default" 使用默认流水线）
    - **demand**: 需求描述
    - **config**: 执行配置（可选）

    执行会异步启动，可以通过返回的 ID 追踪执行状态。
    """
    try:
        execution = pipeline_service.create_execution(
            pipeline_id=data.pipeline_id,
            demand=data.demand,
            config=data.config,
        )

        # 后台启动执行
        background_tasks.add_task(
            run_pipeline,
            execution.id,
            data.pipeline_id,
            data.demand,
        )

        return ExecutionResponse(
            id=execution.id,
            pipeline_id=execution.pipeline_id,
            status=list(execution.status or []),
            current_stage_id=execution.current_stage_id or [],
            results={},
            checkpoints={},
            created_at=execution.created_at,
            updated_at=execution.updated_at,
            completed_at=execution.completed_at,
        )

    except Exception as e:
        logger.error("Failed to create execution", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=dict, summary="查询执行列表", description="分页查询执行历史记录")
async def list_executions(
    pipeline_id: str | None = Query(None, description="按流水线ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> dict:
    """
    获取执行列表。

    - **pipeline_id**: 可选，按流水线ID筛选
    - **page**: 页码
    - **page_size**: 每页数量
    """
    executions, total = pipeline_service.list_executions(
        pipeline_id=pipeline_id,
        page=page,
        page_size=page_size,
    )

    return {
        "items": [
            {
                "id": e.id,
                "pipeline_id": e.pipeline_id,
                "status": e.status.value,
                "current_stage_id": e.current_stage_id or [],
                "created_at": e.created_at.isoformat(),
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in executions
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{execution_id}", response_model=ExecutionStatusResponse, summary="获取执行详情", description="查看指定执行的详细状态和进度")
async def get_execution(execution_id: str) -> ExecutionStatusResponse:
    """
    获取执行详情。

    - **execution_id**: 执行唯一标识

    返回执行状态、当前阶段、进度百分比和检查点信息。
    """
    try:
        status = pipeline_service.get_execution_status(execution_id)
        return ExecutionStatusResponse(**status)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}/status", response_model=ExecutionStatusResponse, summary="获取执行状态", description="获取执行状态的快捷方式")
async def get_execution_status(execution_id: str) -> ExecutionStatusResponse:
    """获取执行状态的快捷接口"""
    return await get_execution(execution_id)


@router.post("/{execution_id}/cancel", response_model=dict, summary="取消执行", description="取消正在运行的执行")
async def cancel_execution(execution_id: str) -> dict:
    """
    取消执行。

    - **execution_id**: 执行唯一标识
    """
    try:
        execution = pipeline_service.cancel_execution(execution_id)
        return {
            "status": "cancelled",
            "execution_id": execution_id,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{execution_id}/pause", response_model=dict, summary="暂停执行", description="暂停正在运行的执行")
async def pause_execution(execution_id: str) -> dict:
    """
    暂停执行。

    - **execution_id**: 执行唯一标识
    """
    try:
        execution = pipeline_service.pause_execution(execution_id)
        return {
            "status": "paused",
            "execution_id": execution_id,
            "current_stage_id": execution.current_stage_id or [],
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{execution_id}/resume", response_model=dict, summary="恢复执行", description="从暂停状态恢复执行")
async def resume_execution(execution_id: str) -> dict:
    """
    恢复执行。

    - **execution_id**: 执行唯一标识
    """
    from devflow.models.execution import ExecutionStatus, StageResult, Checkpoint

    def sync_stage_callback(stage_id: str, state: dict[str, Any]) -> None:
        """每个 stage 完成后同步状态到 execution"""
        try:
            ex = pipeline_service.get_execution(execution_id)
            ex.current_stage_id = list(state.get("current_stage_id") or [])
            ex.updated_at = datetime.utcnow()

            # 同步已完成阶段的结果
            for sid, result_data in state.get("results", {}).items():
                if sid not in ex.results:
                    ex.results[sid] = StageResult(**result_data)

            # 同步 checkpoints
            for sid, cp_data in state.get("checkpoints", {}).items():
                if sid not in ex.checkpoints:
                    ex.checkpoints[sid] = Checkpoint(**cp_data)

            logger.info("Stage state synced during resume", execution_id=execution_id, stage_id=stage_id)
        except Exception as e:
            logger.warning("Failed to sync stage state during resume", execution_id=execution_id, stage_id=stage_id, error=str(e))

    try:
        # 1. 获取 execution 和 pipeline
        execution = pipeline_service.get_execution(execution_id)
        pipeline = pipeline_service.get_pipeline(execution.pipeline_id)

        # 2. 更新状态为 running
        execution.status = ExecutionStatus.RUNNING
        execution.updated_at = datetime.utcnow()

        logger.info("Starting pipeline resume", execution_id=execution_id, pipeline_id=pipeline.id)

        # 3. 调用 engine.resume() 恢复执行，传入回调以同步状态
        result = await pipeline_engine.resume(
            pipeline,
            execution_id,
            stage_callback=sync_stage_callback,
        )

        # 4. 同步 engine 返回的完整状态到 execution
        # 重新获取最新状态，覆盖式同步（而非增量合并）
        ex = pipeline_service.get_execution(execution_id)
        
        # 同步所有结果（覆盖已存在的以获取最新状态）
        if "results" in result:
            ex.results = {
                sid: StageResult(**stage_data) 
                for sid, stage_data in result["results"].items()
            }

        # 同步所有 checkpoints
        if "checkpoints" in result:
            ex.checkpoints = {
                sid: Checkpoint(**cp_data)
                for sid, cp_data in result["checkpoints"].items()
            }

        # 同步关键状态字段
            ex.current_stage_id = result.get("current_stage_id") or []
        
        # 处理状态值（可能是枚举或字符串）
        result_status = result.get("status")
        if isinstance(result_status, str):
            ex.status = ExecutionStatus(result_status)
        elif isinstance(result_status, ExecutionStatus):
            ex.status = result_status
        else:
            ex.status = ExecutionStatus.RUNNING

        # 如果执行完成，更新完成时间
        if ex.status in {ExecutionStatus.COMPLETED, ExecutionStatus.FAILED}:
            ex.completed_at = datetime.utcnow()

        ex.updated_at = datetime.utcnow()

        logger.info(
            "Pipeline resumed and completed",
            execution_id=execution_id,
            current_stage=ex.current_stage_id or [],
            status=ex.status.value,
            results_count=len(ex.results),
        )

        return {
            "status": ex.status.value,
            "execution_id": execution_id,
            "current_stage_id": list(ex.current_stage_id or []),
            "results_count": len(ex.results),
            "checkpoints_count": len(ex.checkpoints),
        }

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error("Resume execution failed", execution_id=execution_id, error=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-run", summary="测试运行流水线", description="直接测试流水线执行（同步），自动将生成的代码文件写入指定目录")
async def test_run_pipeline(data: TestRunRequest) -> dict:
    """
    直接测试流水线执行，不使用后台任务。
    生成的代码文件会自动写入 output_dir 目录。

    - **pipeline_id**: 流水线ID
    - **demand**: 需求描述
    - **output_dir**: 输出目录，默认为 "output"
    """
    import os
    from pathlib import Path

    try:
        logger.info("Test run started", pipeline_id=data.pipeline_id, demand=data.demand, output_dir=data.output_dir)

        pipeline = pipeline_service.get_pipeline(data.pipeline_id)
        result = await pipeline_engine.execute(pipeline, data.demand)

        # 提取并写入 artifacts
        artifacts_written = []
        code_stage_id = None

        # 找到 code-generation 阶段的 artifacts
        results = result.get("results", {})
        for stage_id, stage_result in results.items():
            if isinstance(stage_result, dict):
                stage_type = stage_result.get("stage_id", "")
                # 查找包含 artifacts 的阶段
                artifacts_list = stage_result.get("artifacts", [])
                if artifacts_list:
                    for artifact in artifacts_list:
                        if isinstance(artifact, dict) and artifact.get("file_path"):
                            artifacts_written.append(artifact)

        # 创建输出目录并写入文件
        if artifacts_written:
            output_path = Path(data.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            written_files = []
            for artifact in artifacts_written:
                file_path = artifact.get("file_path", "")
                content = artifact.get("content", "")

                if not file_path or not content:
                    continue

                # 处理路径：如果 file_path 包含目录，需要创建
                full_path = output_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # 写入文件
                full_path.write_text(content, encoding="utf-8")
                written_files.append(str(full_path.absolute()))
                logger.info("Written artifact", file_path=str(full_path), size=len(content))

            logger.info("Test run completed", result_status=result.get("status"), files_written=len(written_files))

            return {
                "status": "completed",
                "result": {
                    "status": result.get("status"),
                    "current_stage_id": result.get("current_stage_id") or [],
                    "results": result.get("results", {}),
                    "output": {
                        "files_written": written_files,
                        "count": len(written_files),
                    },
                }
            }

        logger.info("Test run completed", result_status=result.get("status"), files_written=0)

        return {
            "status": "completed",
            "result": {
                "status": result.get("status"),
                    "current_stage_id": result.get("current_stage_id") or [],
                "results": result.get("results", {}),
                "output": {
                    "files_written": [],
                    "count": 0,
                    "message": "No artifacts to write",
                },
            }
        }
    except Exception as e:
        import traceback
        logger.error("Test run failed", error=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
