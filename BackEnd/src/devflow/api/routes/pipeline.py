"""Pipeline API routes - 流水线管理接口"""

from fastapi import APIRouter, HTTPException, Query
from typing import Any

from devflow.api.schemas import (
    PipelineCreate,
    PipelineUpdate,
    PipelineResponse,
    PipelineListResponse,
    PipelineConfigResponse,
    Descriptions,
    Stages,
    SetDefaultPipelineRequest,
    DefaultPipelineResponse,
)
from devflow.api.service import pipeline_service
from devflow.utils.logging import get_logger

logger = get_logger("api.pipeline")
router = APIRouter(prefix="/pipelines", tags=["Pipeline"])


@router.post("", response_model=PipelineResponse, status_code=201, summary="创建流水线", description="创建一个新的流水线，定义执行流程和阶段")
async def create_pipeline(data: PipelineCreate) -> PipelineResponse:
    """
    创建新流水线。

    - **name**: 流水线名称（必填）
    - **description**: 流水线描述（可选）
    - **stages**: 阶段列表（至少包含一个阶段）
    """
    try:
        pipeline = pipeline_service.create_pipeline(data.model_dump())
        return PipelineResponse(
            id=pipeline.id,
            name=pipeline.name,
            description=pipeline.description,
            stages=pipeline.stages,
            status=pipeline.status,
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
            metadata=pipeline.metadata,
        )
    except Exception as e:
        logger.error("Failed to create pipeline", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PipelineListResponse, summary="查询流水线列表", description="分页查询所有流水线")
async def list_pipelines(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> PipelineListResponse:
    """
    获取流水线列表（分页）。

    - **page**: 页码，从1开始
    - **page_size**: 每页条目数，最大100
    """
    pipelines, total = pipeline_service.list_pipelines(page, page_size)

    return PipelineListResponse(
        items=[
            PipelineResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                stages=p.stages,
                status=p.status,
                created_at=p.created_at,
                updated_at=p.updated_at,
                metadata=p.metadata,
            )
            for p in pipelines
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{pipeline_id}", response_model=PipelineConfigResponse, summary="获取流水线配置", description="根据ID获取指定流水线的配置信息")
async def get_pipeline(pipeline_id: str) -> PipelineConfigResponse:
    """
    获取流水线配置。

    - **pipeline_id**: 流水线唯一标识

    返回流水线配置信息，包括描述、阶段等信息。
    """
    try:
        pipeline = pipeline_service.get_pipeline(pipeline_id)

        # 构建 stages 列表
        stages_list = [Stages(stage_id=stage.id) for stage in pipeline.stages]

        return PipelineConfigResponse(
            config=pipeline.metadata,
            descriptions=Descriptions(
                content=pipeline.description,
                title=pipeline.name,
            ),
            pipeline_id=pipeline.id,
            stages=stages_list,
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{pipeline_id}", status_code=200, summary="更新流水线", description="更新指定流水线的配置")
async def update_pipeline(
    pipeline_id: str,
    data: PipelineUpdate,
) -> None:
    """
    更新流水线。

    - **pipeline_id**: 流水线唯一标识
    - **name**: 新名称（可选）
    - **description**: 新描述（可选）
    - **stages**: 新阶段列表（可选）

    返回 200 状态码表示更新成功。
    """
    try:
        pipeline_service.update_pipeline(
            pipeline_id,
            data.model_dump(exclude_unset=True),
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{pipeline_id}", status_code=204, summary="删除流水线", description="删除指定流水线")
async def delete_pipeline(pipeline_id: str) -> None:
    """
    删除流水线。

    - **pipeline_id**: 流水线唯一标识
    """
    try:
        pipeline_service.delete_pipeline(pipeline_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/default",
    response_model=DefaultPipelineResponse,
    summary="设置默认流水线",
    description="将指定流水线设置为默认流水线",
)
async def set_default_pipeline(data: SetDefaultPipelineRequest) -> DefaultPipelineResponse:
    """
    设置默认流水线。

    - **pipeline_id**: 要设置为默认的流水线ID
    """
    try:
        pipeline = pipeline_service.set_default_pipeline(data.pipeline_id)
        stages_list = [Stages(stage_id=stage.id) for stage in pipeline.stages]

        return DefaultPipelineResponse(
            default_pipeline_id=pipeline.id,
            default_pipeline=PipelineConfigResponse(
                config=pipeline.metadata,
                descriptions=Descriptions(
                    content=pipeline.description,
                    title=pipeline.name,
                ),
                pipeline_id=pipeline.id,
                stages=stages_list,
            ),
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/default",
    response_model=DefaultPipelineResponse,
    summary="获取默认流水线",
    description="获取当前设置为默认的流水线信息",
)
async def get_default_pipeline() -> DefaultPipelineResponse:
    """
    获取默认流水线信息。
    """
    try:
        pipeline_id = pipeline_service.get_default_pipeline_id()
        if not pipeline_id:
            return DefaultPipelineResponse(
                default_pipeline_id=None,
                default_pipeline=None,
            )

        pipeline = pipeline_service.get_pipeline(pipeline_id)
        stages_list = [Stages(stage_id=stage.id) for stage in pipeline.stages]

        return DefaultPipelineResponse(
            default_pipeline_id=pipeline.id,
            default_pipeline=PipelineConfigResponse(
                config=pipeline.metadata,
                descriptions=Descriptions(
                    content=pipeline.description,
                    title=pipeline.name,
                ),
                pipeline_id=pipeline.id,
                stages=stages_list,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
