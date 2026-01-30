"""Tool adapter for opencode."""

from pathlib import Path

from .base import ToolAdapter


class OpenCodeAdapter(ToolAdapter):
    """Adapter for opencode AI coding assistant."""

    @property
    def name(self) -> str:
        return "opencode"

    def get_destination(self, artifact_type: str, target_repo: Path) -> Path:
        return target_repo / ".opencode" / artifact_type
