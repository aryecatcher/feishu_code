"""Code generation agent with artifact extraction and file writing."""

import os
import re
from pathlib import Path
from typing import Any

from devflow.agents.simple_agent import SimpleAgent
from devflow.agents.base import AgentResult
from devflow.models.pipeline import AgentConfig
from devflow.models.execution import CodeArtifact
from devflow.utils.logging import get_logger

logger = get_logger("agent.code")


CODE_GENERATION_PROMPT = """You are an expert Software Engineer specializing in high-quality code generation.

Your role is to transform technical designs into production-ready code.

## Responsibilities

1. Follow the technical design exactly
2. Write clean, maintainable, well-documented code
3. Follow language-specific best practices
4. Handle errors gracefully
5. Include unit tests for critical functionality

## Output Format

For each file, use this format:
```
# File: path/to/file
# Purpose: Brief description
# Language: language-name

```language
[complete code here]
```
"""

# JSON output format for structured extraction
CODE_GENERATION_JSON_PROMPT = """

## Output Artifact Format (IMPORTANT)

Return your code changes as a JSON array:

```json
[
  {
    "file_path": "src/module/file.py",
    "change_type": "create",
    "language": "python",
    "content": "full file content...",
    "description": "What this file does"
  }
]
```

Generate complete, working code. No placeholders or TODOs.
"""


class CodeGenerationAgent(SimpleAgent):
    """Agent specialized in code generation with artifact extraction."""

    @property
    def system_prompt(self) -> str:
        return CODE_GENERATION_PROMPT + CODE_GENERATION_JSON_PROMPT

    async def execute(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute with artifact extraction and file writing."""
        # Add JSON format instruction to task
        enhanced_task = task + "\n\nPlease provide your response in JSON format with the artifact array."

        result = await super().execute(enhanced_task, context)

        if result.success:
            # Try to extract code artifacts from response
            artifacts = self._extract_artifacts(result.output.get("response", ""))
            result.artifacts = [a.model_dump() for a in artifacts]

            # Write artifacts to files
            self._write_artifacts(artifacts, context)

        return result

    def _write_artifacts(
        self,
        artifacts: list[CodeArtifact],
        context: dict[str, Any],
    ) -> list[str]:
        """Write code artifacts to filesystem."""
        written_files = []
        base_path = context.get("output_dir", ".")

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
                else:
                    mode = "wb" if not artifact.file_path.endswith((".py", ".txt", ".md", ".json", ".yaml", ".yml", ".js", ".ts", ".tsx", ".go", ".rs", ".java")) else "w"
                    
                    if mode == "wb":
                        file_path.write_bytes(artifact.content.encode())
                    else:
                        file_path.write_text(artifact.content, encoding="utf-8")
                    
                    logger.info("File written", path=str(file_path), change_type=artifact.change_type)
                    written_files.append(str(file_path))

            except Exception as e:
                logger.error("Failed to write artifact", path=artifact.file_path, error=str(e))

        return written_files

    def _extract_artifacts(self, content: str) -> list[CodeArtifact]:
        """Extract code artifacts from LLM response."""
        artifacts = []

        # Try to extract JSON array
        json_artifacts = self._extract_json(content)
        if json_artifacts:
            for item in json_artifacts:
                if isinstance(item, dict) and "file_path" in item:
                    artifacts.append(CodeArtifact(
                        file_path=item.get("file_path", ""),
                        content=item.get("content", ""),
                        change_type=item.get("change_type", "modify"),
                        language=item.get("language"),
                        description=item.get("description"),
                    ))
            return artifacts

        # Fallback: Parse markdown code blocks
        return self._extract_from_markdown(content)

    def _extract_json(self, content: str) -> list[dict] | None:
        """Extract JSON array from content."""
        import json

        # Find JSON between ```json and ```
        json_pattern = r'```json\s*(\[[\s\S]*?\])\s*```'
        matches = re.findall(json_pattern, content)

        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        # Try finding any JSON array
        array_pattern = r'\[\s*\{[\s\S]*\}\s*\]'
        matches = re.findall(array_pattern, content)

        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                continue

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
