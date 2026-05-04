"""Unit tests for structured output schemas and agents."""

import pytest
from pydantic import ValidationError

from devflow.schemas.structured_outputs import (
    CodeArtifactSchema,
    CodeGenerationOutput,
    ReviewIssueSchema,
    CodeReviewOutput,
    DemandRequirementSchema,
    DemandAnalysisOutput,
    FileChangeSchema,
    APIEndpointSchema,
    SchemeDesignOutput,
    DeploymentStepSchema,
    DeliveryOutput,
)


class TestCodeArtifactSchema:
    """Tests for CodeArtifactSchema."""

    def test_create_code_artifact(self):
        """Test creating a code artifact."""
        artifact = CodeArtifactSchema(
            file_path="src/utils/helper.py",
            change_type="create",
            content="def helper(): pass",
            language="python",
            description="Helper utility",
        )

        assert artifact.file_path == "src/utils/helper.py"
        assert artifact.change_type == "create"
        assert artifact.language == "python"

    def test_change_type_validation(self):
        """Test change_type validation."""
        artifact = CodeArtifactSchema(
            file_path="test.py",
            change_type="modify",
            content="code",
        )
        assert artifact.change_type == "modify"

        artifact = CodeArtifactSchema(
            file_path="test.py",
            change_type="delete",
            content="",
        )
        assert artifact.change_type == "delete"

    def test_invalid_change_type(self):
        """Test invalid change_type raises error."""
        with pytest.raises(ValidationError):
            CodeArtifactSchema(
                file_path="test.py",
                change_type="invalid",
                content="code",
            )


class TestCodeGenerationOutput:
    """Tests for CodeGenerationOutput."""

    def test_create_code_generation_output(self):
        """Test creating code generation output."""
        artifacts = [
            CodeArtifactSchema(
                file_path="src/main.py",
                change_type="create",
                content="print('hello')",
                language="python",
            ),
            CodeArtifactSchema(
                file_path="src/config.py",
                change_type="create",
                content="config = {}",
                language="python",
            ),
        ]

        output = CodeGenerationOutput(
            artifacts=artifacts,
            summary="Generated 2 Python files",
            reasoning="Created main entry point and config file",
        )

        assert len(output.artifacts) == 2
        assert output.summary == "Generated 2 Python files"

    def test_empty_artifacts(self):
        """Test output with no artifacts."""
        output = CodeGenerationOutput(
            artifacts=[],
            summary="No code needed",
        )

        assert len(output.artifacts) == 0


class TestReviewIssueSchema:
    """Tests for ReviewIssueSchema."""

    def test_create_review_issue(self):
        """Test creating a review issue."""
        issue = ReviewIssueSchema(
            severity="high",
            location="src/auth.py:42",
            title="SQL Injection vulnerability",
            description="User input not sanitized",
            recommendation="Use parameterized queries",
        )

        assert issue.severity == "high"
        assert issue.location == "src/auth.py:42"

    def test_all_severity_levels(self):
        """Test all severity levels."""
        for severity in ["critical", "high", "medium", "low"]:
            issue = ReviewIssueSchema(
                severity=severity,
                location="test.py:1",
                title="Test issue",
                description="Test",
                recommendation="Test fix",
            )
            assert issue.severity == severity


class TestCodeReviewOutput:
    """Tests for CodeReviewOutput."""

    def test_approve_verdict(self):
        """Test approve verdict."""
        output = CodeReviewOutput(
            summary="Code looks good",
            verdict="approve",
            issues=[],
            strengths=["Clean code", "Good naming"],
        )

        assert output.verdict == "approve"
        assert len(output.issues) == 0
        assert len(output.strengths) == 2

    def test_request_changes_verdict(self):
        """Test request_changes verdict."""
        issues = [
            ReviewIssueSchema(
                severity="critical",
                location="src/auth.py:1",
                title="Security issue",
                description="Critical",
                recommendation="Fix immediately",
            ),
        ]

        output = CodeReviewOutput(
            summary="Has critical issues",
            verdict="request_changes",
            issues=issues,
        )

        assert output.verdict == "request_changes"
        assert len(output.issues) == 1

    def test_approve_with_suggestions_verdict(self):
        """Test approve_with_suggestions verdict."""
        issues = [
            ReviewIssueSchema(
                severity="low",
                location="src/main.py:10",
                title="Minor style issue",
                description="Could improve",
                recommendation="Consider refactoring",
            ),
        ]

        output = CodeReviewOutput(
            summary="Good code with minor suggestions",
            verdict="approve_with_suggestions",
            issues=issues,
            suggestion="Optional: consider using type hints",
        )

        assert output.verdict == "approve_with_suggestions"
        assert output.suggestion is not None


class TestDemandAnalysisOutput:
    """Tests for DemandAnalysisOutput."""

    def test_create_demand_analysis_output(self):
        """Test creating demand analysis output."""
        requirements = [
            DemandRequirementSchema(
                id="FR-001",
                type="functional",
                title="User login",
                description="Users should be able to login",
                priority="high",
                acceptance_criteria=["Given user exists, when login, then authenticated"],
            ),
        ]

        output = DemandAnalysisOutput(
            summary="User authentication system",
            requirements=requirements,
            scope={"in_scope": ["login", "logout"], "out_of_scope": ["password reset"]},
            questions=["Should we support 2FA?"],
            assumptions=["Users have email addresses"],
            risks=["Integration with existing auth system"],
        )

        assert output.summary == "User authentication system"
        assert len(output.requirements) == 1
        assert output.requirements[0].id == "FR-001"

    def test_requirement_types(self):
        """Test functional and non-functional requirements."""
        functional = DemandRequirementSchema(
            id="FR-001",
            type="functional",
            title="Feature X",
            description="Does X",
        )

        non_functional = DemandRequirementSchema(
            id="NFR-001",
            type="non_functional",
            title="Performance",
            description="Must be fast",
        )

        assert functional.type == "functional"
        assert non_functional.type == "non_functional"


class TestSchemeDesignOutput:
    """Tests for SchemeDesignOutput."""

    def test_create_scheme_design_output(self):
        """Test creating scheme design output."""
        api_design = [
            APIEndpointSchema(
                method="POST",
                path="/api/users",
                description="Create user",
                request_schema='{"name": "str"}',
                response_schema='{"id": "str"}',
            ),
        ]

        file_changes = [
            FileChangeSchema(
                file_path="src/models/user.py",
                action="create",
                priority="high",
                description="User model",
            ),
        ]

        output = SchemeDesignOutput(
            summary="REST API design",
            architecture="Microservices with API gateway",
            technology_stack=["FastAPI", "PostgreSQL", "Redis"],
            api_design=api_design,
            data_model="User table with roles",
            file_changes=file_changes,
            implementation_plan=["Create models", "Implement API", "Add tests"],
            risks=["Database migration complexity"],
        )

        assert output.summary == "REST API design"
        assert len(output.api_design) == 1
        assert len(output.file_changes) == 1
        assert "FastAPI" in output.technology_stack

    def test_api_methods(self):
        """Test all HTTP methods."""
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            api = APIEndpointSchema(
                method=method,
                path="/test",
                description="Test endpoint",
            )
            assert api.method == method


class TestDeliveryOutput:
    """Tests for DeliveryOutput."""

    def test_create_delivery_output(self):
        """Test creating delivery output."""
        deployment_steps = [
            DeploymentStepSchema(
                step=1,
                action="Backup database",
                command="pg_dump > backup.sql",
                verification="Check backup file exists",
            ),
            DeploymentStepSchema(
                step=2,
                action="Deploy new version",
                command="kubectl apply -f deployment.yaml",
                verification="Check pod status",
            ),
        ]

        output = DeliveryOutput(
            summary="v1.2.0 release",
            changes={
                "features": ["New login flow"],
                "bugfixes": ["Fixed memory leak"],
            },
            deployment_steps=deployment_steps,
            rollback_plan=["Revert to previous image", "Restore database"],
            verification_commands=["curl /health", "npm test"],
            checklist=["Code reviewed", "Tests passing"],
        )

        assert output.summary == "v1.2.0 release"
        assert len(output.deployment_steps) == 2
        assert len(output.rollback_plan) == 2

    def test_deployment_step_order(self):
        """Test deployment steps are ordered."""
        steps = [
            DeploymentStepSchema(step=3, action="Deploy"),
            DeploymentStepSchema(step=1, action="Backup"),
            DeploymentStepSchema(step=2, action="Migrate"),
        ]

        output = DeliveryOutput(
            summary="Test release",
            deployment_steps=steps,
        )

        # Steps should be in the order they were added
        assert output.deployment_steps[0].step == 3
        assert output.deployment_steps[1].step == 1
        assert output.deployment_steps[2].step == 2
