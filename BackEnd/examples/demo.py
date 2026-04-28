"""Example script to demonstrate DevFlow Engine."""

import asyncio
import json
from devflow.models.pipeline import PipelineStage, StageType, AgentConfig
from devflow.agents.factory import AgentFactory
from devflow.core.engine import pipeline_engine
from devflow.llm.factory import llm_manager
from devflow.utils.config import settings
from devflow.utils.logging import setup_logging, logger


def create_demo_pipeline() -> list[PipelineStage]:
    """Create a demo pipeline configuration."""
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
            is_checkpoint=True,
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
            is_checkpoint=True,
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
    return stages


async def demo_single_agent():
    """Demonstrate a single agent execution."""
    logger.info("=== Demo: Single Agent Execution ===")

    # Configure LLM
    llm_manager.configure(primary="openai")

    # Create agent
    config = AgentConfig(
        name="DemandAnalyzer",
        system_prompt="You are a helpful assistant.",
    )
    agent = AgentFactory.create(StageType.DEMAND_ANALYSIS, config)

    # Execute
    task = "我需要一个用户登录功能，包含用户名密码验证和记住登录状态"
    context = {}

    logger.info("Executing agent with task", task=task)

    result = await agent.execute(task, context)

    logger.info("Agent execution completed", success=result.success)

    if result.success:
        print("\n" + "=" * 50)
        print("AGENT OUTPUT:")
        print("=" * 50)
        print(result.output.get("response", ""))
        print("=" * 50)

    return result


async def demo_pipeline():
    """Demonstrate full pipeline execution."""
    logger.info("=== Demo: Full Pipeline Execution ===")

    # Configure LLM
    llm_manager.configure(primary="openai")

    # Register agents
    stages = create_demo_pipeline()
    for stage in stages:
        agent = AgentFactory.create(stage.stage_type, stage.agent)
        pipeline_engine.register_agent(stage.stage_type, agent)

    # Create pipeline object
    from devflow.models.pipeline import Pipeline
    pipeline = Pipeline(
        id="demo-pipeline",
        name="Demo Pipeline",
        description="演示流水线",
        stages=stages,
    )

    # Execute with demand
    demand = """
    需求：为一个博客系统添加评论功能

    功能要求：
    1. 用户可以对文章发表评论
    2. 支持回复评论（嵌套评论，最多3层）
    3. 评论需要审核后才能显示
    4. 支持表情评论
    5. 需要防止垃圾评论（频率限制）

    技术要求：
    - 使用 RESTful API
    - 数据库使用 PostgreSQL
    - 响应时间 < 200ms
    """

    logger.info("Starting pipeline execution")

    result = await pipeline_engine.execute(pipeline, demand)

    logger.info("Pipeline execution completed", status=result.get("status"))

    # Print results
    print("\n" + "=" * 60)
    print("PIPELINE RESULTS:")
    print("=" * 60)

    for stage_id, stage_result in result.get("results", {}).items():
        print(f"\n### Stage: {stage_id}")
        print(f"Status: {stage_result.get('status')}")

        output = stage_result.get("output", {})
        if "response" in output:
            content = output["response"]
            if len(content) > 1000:
                content = content[:1000] + "\n... (truncated)"
            print(f"\n{content}")

    print("\n" + "=" * 60)

    return result


async def main():
    """Run demos."""
    setup_logging()

    print("DevFlow Engine - Demo Script")
    print("=" * 60)

    try:
        # Run single agent demo
        # await demo_single_agent()

        # Run full pipeline demo
        result = await demo_pipeline()

        print("\nDemo completed successfully!")

    except Exception as e:
        logger.error("Demo failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
