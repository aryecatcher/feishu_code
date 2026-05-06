"""Code context builder for agents.

Provides file reading, directory structure, and git diff capabilities.
"""

import re
from pathlib import Path
from typing import Any

import git

from devflow.utils.logging import get_logger

logger = get_logger("context")


class CodeContextBuilder:
    """Build code context from a repository for agent consumption."""

    def __init__(self, repo_path: str | None = None):
        self.repo_path = repo_path
        self._repo: git.Repo | None = None

    @property
    def repo(self) -> git.Repo | None:
        """Lazy load git repository."""
        if self._repo is None and self.repo_path:
            try:
                self._repo = git.Repo(self.repo_path)
            except git.InvalidGitRepositoryError:
                logger.warning("Not a valid git repository", path=self.repo_path)
                self._repo = None
        return self._repo

    def build_file_context(
        self,
        file_paths: list[str],
        max_lines: int = 500,
    ) -> str:
        """Build context string from specific files."""
        context_parts = []
        logger.info("Building file context", repo_path=self.repo_path, files=file_paths)

        for file_path in file_paths:
            full_path = Path(self.repo_path) / file_path if self.repo_path else Path(file_path)
            logger.debug("Processing file", file_path=file_path, full_path=str(full_path))

            try:
                if not full_path.exists():
                    logger.warning("File not found", file_path=file_path, full_path=str(full_path))
                    context_parts.append(f"// File not found: {file_path}")
                    continue

                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[:max_lines]
                    content = "".join(lines)

                    logger.info(
                        "File read successfully",
                        file_path=file_path,
                        lines_read=len(lines),
                        total_lines_in_file=len(lines),
                    )

                    context_parts.append(f"// ===== {file_path} =====")
                    context_parts.append(content)

                    if len(lines) >= max_lines:
                        context_parts.append(f"// ... (truncated, {max_lines}+ lines)")

            except Exception as e:
                logger.error("Failed to read file", file=file_path, error=str(e))
                context_parts.append(f"// Error reading {file_path}: {e}")

        return "\n\n".join(context_parts)

    def build_directory_context(
        self,
        directory: str,
        extensions: list[str] | None = None,
        max_files: int = 20,
    ) -> str:
        """Build context from a directory structure."""
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java"]

        context_parts = [f"// Directory: {directory}\n// Structure:"]

        try:
            dir_path = Path(self.repo_path) / directory if self.repo_path else Path(directory)

            if not dir_path.exists():
                return f"// Directory not found: {directory}"

            files = []
            for ext in extensions:
                files.extend(dir_path.rglob(f"*{ext}"))

            files = files[:max_files]

            for file_path in sorted(files)[:max_files]:
                rel_path = file_path.relative_to(dir_path)
                context_parts.append(f"//   {rel_path}")

            if len(files) > max_files:
                context_parts.append(f"//   ... and {len(files) - max_files} more files")

        except Exception as e:
            logger.warning("Failed to read directory", directory=directory, error=str(e))

        return "\n".join(context_parts)

    def build_diff_context(
        self,
        base_commit: str = "HEAD",
        target: str = "HEAD",
    ) -> str:
        """Build context from git diff."""
        if not self.repo:
            return "// Git repository not available"

        try:
            base = self.repo.commit(base_commit)
            target_commit = self.repo.commit(target)

            diff = target_commit.diff(base)

            context_parts = ["// Git Diff:"]

            for diff_item in diff:
                if diff_item.a_path:
                    context_parts.append(f"// File: {diff_item.a_path}")

                    if diff_item.diff:
                        diff_text = diff_item.diff.decode("utf-8", errors="replace")
                        if len(diff_text) > 5000:
                            diff_text = diff_text[:5000] + "\n// ... (truncated)"
                        context_parts.append(diff_text)

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.warning("Failed to generate diff", error=str(e))
            return f"// Error generating diff: {e}"

    def get_file_structure(
        self,
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Get file structure of the repository."""
        if not self.repo_path:
            return {}

        structure = {}

        try:
            root = Path(self.repo_path)

            for item in root.iterdir():
                if item.name.startswith(".") or item.name in ["node_modules", "__pycache__", "venv"]:
                    continue

                if item.is_file():
                    structure[item.name] = "file"
                elif item.is_dir():
                    structure[item.name] = self._get_dir_structure(item, max_depth - 1)

        except Exception as e:
            logger.warning("Failed to get file structure", error=str(e))

        return structure

    def _get_dir_structure(
        self,
        path: Path,
        max_depth: int,
    ) -> dict[str, Any]:
        """Recursively get directory structure."""
        if max_depth <= 0:
            return {"...": "truncated"}

        structure = {}

        try:
            for item in path.iterdir():
                if item.name.startswith("."):
                    continue

                if item.is_file():
                    structure[item.name] = "file"
                elif item.is_dir():
                    if item.name not in ["node_modules", "__pycache__", "venv", ".git"]:
                        structure[item.name] = self._get_dir_structure(item, max_depth - 1)

        except PermissionError:
            return {"[permission denied]": "..."}

        return structure

    def parse_code_structure(
        self,
        file_path: str,
    ) -> dict[str, Any]:
        """Parse code structure using simple regex patterns."""
        try:
            full_path = Path(self.repo_path) / file_path if self.repo_path else Path(file_path)

            if not full_path.exists():
                return {"error": "File not found"}

            ext = full_path.suffix.lstrip(".")

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            structure = {
                "file": str(file_path),
                "language": ext,
                "functions": [],
                "classes": [],
            }

            # Extract based on file type
            if ext == "py":
                self._extract_python_defs(content, structure)
            elif ext in ["js", "ts", "tsx"]:
                self._extract_js_ts_defs(content, structure)
            elif ext == "go":
                self._extract_go_defs(content, structure)

            return structure

        except Exception as e:
            logger.warning("Failed to parse code", file=file_path, error=str(e))
            return {"error": str(e)}

    def _extract_python_defs(self, content: str, structure: dict) -> None:
        """Extract Python function and class definitions."""
        # Classes: class ClassName(...)
        class_pattern = r'^class\s+(\w+)'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            structure["classes"].append(match.group(1))

        # Functions: def func_name(...)
        func_pattern = r'^def\s+(\w+)\s*\('
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            structure["functions"].append(match.group(1))

    def _extract_js_ts_defs(self, content: str, structure: dict) -> None:
        """Extract JavaScript/TypeScript function and class definitions."""
        # Classes: class ClassName
        class_pattern = r'\bclass\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            structure["classes"].append(match.group(1))

        # Functions: function name(...) or const name = (...) => ...
        func_pattern = r'\b(?:function|const|let)\s+(\w+)\s*(?:=\s*)?(?:async\s*)?\('
        for match in re.finditer(func_pattern, content):
            structure["functions"].append(match.group(1))

    def _extract_go_defs(self, content: str, structure: dict) -> None:
        """Extract Go function and type definitions."""
        # Types/Structs: type Name struct or type Name interface
        type_pattern = r'^type\s+(\w+)\s+(?:struct|interface)'
        for match in re.finditer(type_pattern, content, re.MULTILINE):
            structure["classes"].append(match.group(1))

        # Functions: func Name(...) or func (receiver) Name(...)
        func_pattern = r'^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\('
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            structure["functions"].append(match.group(1))

    def build_full_context(
        self,
        focus_files: list[str] | None = None,
        directory: str | None = None,
    ) -> str:
        """Build complete context for an agent."""
        context_parts = []

        # Add file structure
        structure = self.get_file_structure()
        if structure:
            context_parts.append("// Repository Structure:")
            context_parts.append(str(structure))
            context_parts.append("")

        # Add focus files
        if focus_files:
            logger.info("Adding focus files to context", file_count=len(focus_files), files=focus_files)
            context_parts.append(self.build_file_context(focus_files))
            context_parts.append("")
        else:
            logger.info("No focus files provided")

        # Add directory context
        if directory:
            logger.info("Adding directory context", directory=directory)
            context_parts.append(self.build_directory_context(directory))
            context_parts.append("")

        total_length = sum(len(p) for p in context_parts)
        logger.info("Context built", focus_files_count=len(focus_files) if focus_files else 0, total_chars=total_length)

        return "\n".join(context_parts)
