"""Factory for creating pipeline agents."""

from devflow.agents.base import BaseAgent
from devflow.agents.simple_agent import SimpleAgent
from devflow.agents.demand_agent import DemandAnalysisAgent
from devflow.agents.scheme_agent import SchemeDesignAgent
from devflow.agents.code_agent import CodeGenerationAgent
from devflow.agents.review_agent import CodeReviewAgent
from devflow.agents.delivery_agent import DeliveryAgent
from devflow.models.pipeline import StageType, AgentConfig
from devflow.utils.logging import get_logger

logger = get_logger("agent.factory")


class AgentFactory:
    """Factory for creating stage-specific agents."""

    _agents: dict[str, type[BaseAgent]] = {
        StageType.DEMAND_ANALYSIS: DemandAnalysisAgent,
        StageType.SCHEME_DESIGN: SchemeDesignAgent,
        StageType.CODE_GENERATION: CodeGenerationAgent,
        StageType.CODE_REVIEW: CodeReviewAgent,
        StageType.DELIVERY: DeliveryAgent,
    }

    @classmethod
    def create(cls, stage_type: StageType, config: AgentConfig) -> BaseAgent:
        """Create an agent for the specified stage type."""
        agent_class = cls._agents.get(stage_type)

        if agent_class is None:
            raise ValueError(f"No agent for stage type: {stage_type.value}")

        return agent_class(config)

    @classmethod
    def create_all(cls) -> dict[StageType, BaseAgent]:
        """Create all agents with default LLM configuration from settings."""
        return {
            stage_type: cls.create(stage_type, AgentConfig(name=stage_type.value))
            for stage_type in cls._agents
        }

    @classmethod
    def register(cls, stage_type: StageType, agent_class: type[BaseAgent]) -> None:
        """Register a custom agent for a stage type."""
        cls._agents[stage_type] = agent_class
        logger.info("Registered agent", stage_type=stage_type.value)
