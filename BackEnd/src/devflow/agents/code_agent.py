"""Code generation agent with structured output and file writing."""

import re
from pathlib import Path
from typing import Any

from devflow.agents.base import BaseAgent, AgentResult
from devflow.models.pipeline import AgentConfig
from devflow.models.execution import CodeArtifact
from devflow.schemas.structured_outputs import (
    CodeArtifactSchema,
    CodeGenerationOutput,
)
from devflow.utils.logging import get_logger

logger = get_logger("agent.code")


CODE_GENERATION_SYSTEM_PROMPT = """You are an expert Software Engineer specializing in high-quality code generation.

Your role is to transform technical designs into production-ready code.

## Responsibilities

1. Follow the technical design exactly
2. Write clean, maintainable, well-documented code
3. Follow language-specific best practices
4. Handle errors gracefully
5. Include unit tests for critical functionality

## Output Requirement

You MUST return your output as a structured JSON object with the schema provided.
Generate complete, working code. No placeholders or TODOs.

## Guidelines

- For new files, set change_type to "create"
- For existing files, set change_type to "modify"
- For files to be removed, set change_type to "delete"
- The content field should contain the complete file content
- Use appropriate language identifiers (python, typescript, javascript, etc.)
"""


class CodeGenerationAgent(BaseAgent):
    """Agent specialized in code generation using structured output.

    This agent uses with_structured_output() to reliably parse LLM responses
    into CodeGenerationOutput Pydantic models, eliminating the need for
    fragile regex-based parsing.
    """

    @property
    def system_prompt(self) -> str:
        return CODE_GENERATION_SYSTEM_PROMPT

    @property
    def output_schema(self):
        """Define the structured output schema."""
        return CodeGenerationOutput

    async def execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute with structured output and file writing.

        Uses with_structured_output() to get reliable structured data,
        then writes the generated code to the filesystem.
        """
        # Enhance task with target repository info
        enhanced_task = self._enhance_task(task, context)

        try:
            # Use structured output - this returns a CodeGenerationOutput instance
            result = await self.execute_structured(enhanced_task, context)

            # Convert structured output to AgentResult
            artifacts = []
            written_files = []

            for artifact_schema in result.artifacts:
                # Convert schema to CodeArtifact model
                artifact = CodeArtifact(
                    file_path=artifact_schema.file_path,
                    content=artifact_schema.content,
                    change_type=artifact_schema.change_type,
                    language=artifact_schema.language,
                    description=artifact_schema.description,
                )
                artifacts.append(artifact)

            # Write artifacts to filesystem
            if context.get("write_files", True):
                written_files = self._write_artifacts(artifacts, context)

            return AgentResult(
                success=True,
                output={
                    "summary": result.summary,
                    "reasoning": result.reasoning,
                    "artifacts_count": len(result.artifacts),
                },
                artifacts=[a.model_dump() for a in artifacts],
            )

        except Exception as e:
            logger.error("Code generation failed", error=str(e))

            # Fallback: try simple text generation
            return await self._fallback_execute(task, context)

    def _enhance_task(self, task: str, context: dict[str, Any]) -> str:
        """Enhance task with additional context."""
        enhancement_parts = [task]

        # Add target repository info
        if target_repo := context.get("target_repo"):
            enhancement_parts.append(f"\n\n## Target Repository\n{target_repo}")

        # Add existing files for reference
        if existing_files := context.get("existing_files"):
            if isinstance(existing_files, list):
                files_list = "\n".join(f"- {f}" for f in existing_files[:20])
                enhancement_parts.append(f"\n\n## Existing Files (for reference)\n{files_list}")

        # Add language preference
        if language := context.get("preferred_language"):
            enhancement_parts.append(f"\n\n## Preferred Language\n{language}")

        # Output format requirements to ensure correct field names
        output_format_instruction = """
## Output Format Requirements (CRITICAL)

You MUST return a JSON object with the following structure:

```json
{
  "artifacts": [
    {
      "file_path": "src/components/Hello.vue",
      "content": "完整的文件内容...",
      "change_type": "create",
      "language": "vue",
      "description": "组件说明"
    }
  ],
  "summary": "生成结果说明",
  "reasoning": "决策推理过程"
}
```

**Field Requirements:**
- `file_path`: 文件相对路径（相对于仓库根目录），**必须使用 `file_path` 而非 `filename`**
- `content`: 完整的文件内容字符串
- `change_type`: 必须是 "create"、"modify" 或 "delete"
- `language`: 编程语言，如 "python"、"typescript"、"vue"、"html" 等
- `summary`: 生成结果的简要说明
- `reasoning`: 代码组织的决策推理

**Common Mistakes to Avoid:**
- ❌ Do NOT use "filename" - use "file_path" instead
- ❌ Do NOT use "code" as content field - use "content"
- ❌ Do NOT wrap content in code blocks within the JSON
"""
        enhancement_parts.append(output_format_instruction)

        return "\n".join(enhancement_parts)

    def _write_artifacts(
        self,
        artifacts: list[CodeArtifact],
        context: dict[str, Any],
    ) -> list[str]:
        """Write code artifacts to filesystem."""
        written_files = []
        base_path = context.get("output_dir", context.get("target_repo", "output"))

        for artifact in artifacts:
            try:
                file_path = Path(base_path) / artifact.file_path
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Handle different change types
                if artifact.change_type == "delete":
                    if file_path.exists():
                        file_path.unlink()
                        logger.info("File deleted", path=str(file_path))
                        written_files.append(str(file_path))
                elif artifact.change_type == "create":
                    # Only write if file doesn't exist (unless overwrite is enabled)
                    if file_path.exists() and not context.get("overwrite", False):
                        logger.warning("File exists, skipping", path=str(file_path))
                        continue

                    content = artifact.content or ""
                    file_path.write_text(content, encoding="utf-8")
                    logger.info("File written", path=str(file_path), change_type=artifact.change_type)
                    written_files.append(str(file_path))

                elif artifact.change_type == "modify":
                    # For modifications, we still write the content
                    content = artifact.content or ""
                    file_path.write_text(content, encoding="utf-8")
                    logger.info("File modified", path=str(file_path), change_type=artifact.change_type)
                    written_files.append(str(file_path))

            except Exception as e:
                logger.error("Failed to write artifact", path=artifact.file_path, error=str(e))

        return written_files

    async def _fallback_execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Fallback to simple text generation with regex parsing.

        This is called when structured output fails.
        """
        from devflow.agents.simple_agent import SimpleAgent

        logger.warning("Falling back to text-based generation")

        # Use parent class simple execution
        simple_agent = SimpleAgent(self.config)

        # Add JSON format instruction to task
        enhanced_task = task + "\n\nPlease provide your response as a JSON array of code artifacts."

        messages = await simple_agent.prepare_messages(enhanced_task, context)
        response = await simple_agent.invoke_llm(messages)

        # Try to extract artifacts using regex (old method)
        artifacts = self._extract_artifacts_fallback(response.content)

        # Write artifacts to filesystem
        written_files = []
        if context.get("write_files", True) and artifacts:
            written_files = self._write_artifacts(artifacts, context)

        return AgentResult(
            success=True,
            output={"response": response.content, "fallback": True, "written_files": written_files},
            artifacts=[a.model_dump() for a in artifacts],
        )

    def _extract_artifacts_fallback(self, content: str) -> list[CodeArtifact]:
        """Fallback extraction using regex (preserved for backward compatibility)."""
        logger.info("Fallback content preview", content=content[:1000])

        artifacts = []

        # Try JSON extraction
        json_artifacts = self._extract_json(content)
        logger.info("JSON extraction result", result=json_artifacts)

        if json_artifacts:
            for item in json_artifacts:
                if isinstance(item, dict) and ("file_path" in item or "filename" in item or "path" in item):
                    raw_content = item.get("content") or item.get("code", "")

                    # Handle content that is an object instead of string (LLM sometimes returns parsed JSON)
                    if isinstance(raw_content, dict):
                        import json as json_module
                        raw_content = json_module.dumps(raw_content, ensure_ascii=False, indent=2)
                    elif not isinstance(raw_content, str):
                        raw_content = str(raw_content)

                    artifacts.append(CodeArtifact(
                        file_path=item.get("file_path") or item.get("filename", "") or item.get("path", ""),
                        content=raw_content,
                        change_type=item.get("change_type", "modify"),
                        language=item.get("language"),
                        description=item.get("description"),
                    ))
            if artifacts:
                return artifacts

        # Fallback: Parse markdown code blocks
        return self._extract_from_markdown(content)

    def _extract_json(self, content: str) -> list[dict] | None:
        """Extract JSON array from content."""
        import json
        import re

        content = content.strip()

        # Try direct JSON parse (if content is already a JSON array)
        try:
            stripped = re.sub(r'^```json\s*', '', content)
            stripped = re.sub(r'\s*```$', '', stripped)
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

        # Find JSON using position indices - find first ```json, then first closing ```
        start_marker = '```json'
        end_marker = '```'
        start_idx = content.find(start_marker)
        if start_idx != -1:
            after_start = content[start_idx + len(start_marker):]
        else:
            after_start = content

        end_idx = after_start.find(end_marker)
        if end_idx == -1:
            end_idx = len(after_start)

        candidate = after_start[:end_idx].strip()

        # Try progressively shorter candidates, removing trailing content
        while len(candidate) > 0:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Remove last character and try again
            candidate = candidate[:-1]

        # Fallback: find first [ in content
        first_bracket = content.find('[')
        if first_bracket == -1:
            return None

        candidate = content[first_bracket:]
        while len(candidate) > 0:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            candidate = candidate[:-1]

        return None

    def _extract_from_markdown(self, content: str) -> list[CodeArtifact]:
        """Extract artifacts from markdown format."""
        artifacts = []

        # Pattern: # File: filename\n...```\ncode\n```
        pattern = r'#\s*File:\s*(.+?)(?:\n|#|$)(.*?)(?:```[\w]*\n)(.*?)(?:```|$)'
        matches = re.findall(pattern, content, re.DOTALL)

        for file_path, meta, code in matches:
            file_path = file_path.strip()
            code = code.strip()

            if not file_path or not code:
                continue

            ext = file_path.split(".")[-1] if "." in file_path else ""
            lang_map = {
                "py": "python", "js": "javascript", "ts": "typescript",
                "tsx": "typescript", "go": "go", "rs": "rust", "java": "java",
            }

            artifacts.append(CodeArtifact(
                file_path=file_path,
                content=code,
                change_type="create",
                language=lang_map.get(ext, "text"),
            ))

        return artifacts
