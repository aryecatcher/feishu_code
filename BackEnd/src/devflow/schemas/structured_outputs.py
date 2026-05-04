"""Structured output schemas for Agent responses.

This module defines Pydantic schemas for structured output from agents,
enabling reliable parsing of LLM responses.
"""

from pydantic import BaseModel, Field
from typing import Literal


class CodeArtifactSchema(BaseModel):
    """单个代码文件"""

    file_path: str = Field(
        description="文件路径，相对于仓库根目录，例如: src/utils/helper.py"
    )
    change_type: Literal["create", "modify", "delete"] = Field(
        default="create",
        description="变更类型: create=新建, modify=修改, delete=删除",
    )
    content: str = Field(
        description="完整的文件内容",
    )
    language: str | None = Field(
        default=None,
        description="编程语言，例如: python, typescript, javascript",
    )
    description: str | None = Field(
        default=None,
        description="文件变更说明",
    )


class CodeGenerationOutput(BaseModel):
    """代码生成阶段输出"""

    artifacts: list[CodeArtifactSchema] = Field(
        description="生成的代码文件列表",
    )
    summary: str = Field(
        description="生成结果的简要说明，包括生成了哪些文件、主要功能等",
    )
    reasoning: str = Field(
        default="",
        description="生成决策的推理过程，说明为什么这样组织代码",
    )


class ReviewIssueSchema(BaseModel):
    """代码评审问题"""

    severity: Literal["critical", "high", "medium", "low"] = Field(
        description="问题严重程度: critical=严重, high=高, medium=中, low=低",
    )
    location: str = Field(
        description="问题位置，例如: src/file.py:42 或 file.py:10-20",
    )
    title: str = Field(
        description="问题简明标题",
    )
    description: str = Field(
        description="问题详细描述，说明具体问题是什么",
    )
    recommendation: str = Field(
        description="修复建议，说明如何修复这个问题",
    )


class CodeReviewOutput(BaseModel):
    """代码评审输出"""

    summary: str = Field(
        description="评审总结，概括整体评审结果",
    )
    verdict: Literal["approve", "request_changes", "approve_with_suggestions"] = Field(
        description="评审结论: approve=通过, request_changes=需要修改, approve_with_suggestions=有建议但通过",
    )
    issues: list[ReviewIssueSchema] = Field(
        default_factory=list,
        description="发现的问题列表",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="代码优点列表",
    )
    suggestion: str | None = Field(
        default=None,
        description="改进建议（非阻塞性）",
    )


class DemandRequirementSchema(BaseModel):
    """单个需求项"""

    id: str = Field(
        description="需求编号，例如: FR-001",
    )
    type: Literal["functional", "non_functional"] = Field(
        description="需求类型: functional=功能性, non_functional=非功能性",
    )
    title: str = Field(
        description="需求标题",
    )
    description: str = Field(
        description="需求详细描述",
    )
    priority: Literal["critical", "high", "medium", "low"] = Field(
        default="medium",
        description="优先级",
    )
    priority: Literal["critical", "high", "medium", "low"] | None = Field(
        default=None,
        description="优先级",
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="验收标准列表",
    )


class DemandAnalysisOutput(BaseModel):
    """需求分析阶段输出"""

    summary: str = Field(
        description="需求概述，简要说明需求的核心内容",
    )
    requirements: list[DemandRequirementSchema] = Field(
        description="提取的功能性和非功能性需求列表",
    )
    scope: dict = Field(
        default_factory=dict,
        description="范围定义，包含 in_scope 和 out_of_scope",
    )
    questions: list[str] = Field(
        default_factory=list,
        description="需要澄清的问题列表",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="已确认的假设条件",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="识别的风险点",
    )


class FileChangeSchema(BaseModel):
    """技术方案中的单个文件变更"""

    file_path: str = Field(
        description="文件路径",
    )
    action: Literal["create", "modify", "delete"] = Field(
        description="操作类型",
    )
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="优先级",
    )
    description: str = Field(
        description="变更说明",
    )


class APIEndpointSchema(BaseModel):
    """API 端点定义"""

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(
        description="HTTP 方法",
    )
    path: str = Field(
        description="API 路径，例如: /api/users",
    )
    description: str = Field(
        description="端点说明",
    )
    request_schema: str | None = Field(
        default=None,
        description="请求数据结构",
    )
    response_schema: str | None = Field(
        default=None,
        description="响应数据结构",
    )


class SchemeDesignOutput(BaseModel):
    """技术方案设计阶段输出"""

    summary: str = Field(
        description="方案概述，简要说明技术方案的核心思路",
    )
    architecture: str = Field(
        description="系统架构设计说明",
    )
    technology_stack: list[str] = Field(
        default_factory=list,
        description="技术栈列表",
    )
    api_design: list[APIEndpointSchema] = Field(
        default_factory=list,
        description="API 设计列表",
    )
    data_model: str | None = Field(
        default=None,
        description="数据模型设计说明",
    )
    file_changes: list[FileChangeSchema] = Field(
        default_factory=list,
        description="需要变更的文件列表",
    )
    implementation_plan: list[str] = Field(
        default_factory=list,
        description="实施计划步骤",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="技术风险点",
    )


class DeploymentStepSchema(BaseModel):
    """部署步骤"""

    step: int = Field(
        description="步骤编号",
    )
    action: str = Field(
        description="执行动作",
    )
    command: str | None = Field(
        default=None,
        description="需要执行的命令",
    )
    verification: str | None = Field(
        default=None,
        description="验证方法",
    )


class DeliveryOutput(BaseModel):
    """交付阶段输出"""

    summary: str = Field(
        description="交付概述",
    )
    changes: dict = Field(
        default_factory=dict,
        description="变更汇总",
    )
    deployment_steps: list[DeploymentStepSchema] = Field(
        default_factory=list,
        description="部署步骤列表",
    )
    rollback_plan: list[str] = Field(
        default_factory=list,
        description="回滚计划步骤",
    )
    verification_commands: list[str] = Field(
        default_factory=list,
        description="验证命令",
    )
    checklist: list[str] = Field(
        default_factory=list,
        description="签收检查清单",
    )
