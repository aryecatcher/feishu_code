"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from devflow.api.routes import pipeline, execution, checkpoint
from devflow.api.service import create_default_pipeline
from devflow.api.schemas import HealthResponse, ErrorResponse
from devflow.llm import llm_manager
from devflow.utils.config import settings
from devflow.utils.logging import setup_logging, logger

# Setup logging
setup_logging()

# Configure LLM manager at startup
llm_manager.auto_configure()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(
        "Starting DevFlow Engine",
        version=settings.app_version,
        debug=settings.debug,
    )

    # Initialize default pipeline
    try:
        pipeline = create_default_pipeline()
        logger.info("Default pipeline initialized", pipeline_id=pipeline.id)
    except Exception as e:
        logger.warning("Failed to initialize default pipeline", error=str(e))

    yield

    logger.info("Shutting down DevFlow Engine")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
## AI 驱动开发流水线引擎

基于 LangGraph 的智能开发流水线系统，支持多阶段 AI Agent 协作和人工审批机制。

### 核心功能

- **流水线编排**: 定义和管理多阶段开发流程
- **AI Agent 协作**: 需求分析、方案设计、代码生成、代码评审
- **人工审批**: 在关键节点设置检查点，实现 Human-in-the-Loop
- **异步执行**: 后台运行，支持状态轮询

### 流程说明

```
需求输入 → 需求分析 → 方案设计[审批] → 代码生成 → 代码评审[审批] → 交付
```

### Swagger 使用流程

1. **启动执行**: `POST /executions` 创建执行并启动流水线
2. **轮询状态**: `GET /executions/{execution_id}` 查看执行进度
3. **等待审批**: 当状态变为 `waiting_approval` 时，到检查点接口查看待审批项
4. **审批检查点**: `POST /checkpoints/{execution_id}/{stage_id}/approve` 批准继续执行
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    import traceback
    error_detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("Unhandled exception", path=str(request.url), error=error_detail)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=error_detail,
            code="INTERNAL_ERROR",
        ).model_dump(mode="json"),
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"], summary="健康检查", description="检查服务是否正常运行")
async def health_check() -> HealthResponse:
    """
    健康检查接口。

    返回服务状态、版本号和时间戳。
    """
    # Check LLM connectivity
    llm_healthy = False
    try:
        if llm_manager.primary_provider:
            llm_healthy = await llm_manager.primary_provider.validate_connection()
    except Exception:
        llm_healthy = False

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        services={
            "api": True,
            "llm": llm_healthy,
        },
    )


# Include routers
app.include_router(pipeline.router)
app.include_router(execution.router)
app.include_router(checkpoint.router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
