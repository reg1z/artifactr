"""Tool adapter for claude-code."""

from pathlib import Path

from .base import ToolAdapter


class ClaudeCodeAdapter(ToolAdapter):
    """Adapter for claude-code AI coding assistant."""

    @property
    def name(self) -> str:
        return "claude-code"

    def get_destination(self, artifact_type: str, target_repo: Path) -> Path:
        return target_repo / ".claude" / artifact_type
