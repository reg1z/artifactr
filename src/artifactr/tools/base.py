"""Base class for tool adapters."""

from abc import ABC, abstractmethod
from pathlib import Path

# Artifact types supported by all tools (tool-agnostic)
ARTIFACT_TYPES = ["skills", "agents", "commands"]


def get_source(artifact_type: str, vault_path: Path) -> Path:
    """Return the source path for an artifact type in the vault.

    This is a module-level function because sources are tool-agnostic.
    All tools read from the same vault structure.
    """
    return vault_path / artifact_type


class ToolAdapter(ABC):
    """Base class for tool-specific import logic.

    Each adapter defines only the DESTINATION paths for a specific tool.
    Source paths are tool-agnostic (see get_source function).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool's identifier (e.g., 'claude-code')."""
        pass

    @property
    @abstractmethod
    def config_dir(self) -> str:
        """Return the tool's config directory name (e.g., '.claude')."""
        pass

    @abstractmethod
    def get_destination(self, artifact_type: str, target_repo: Path) -> Path:
        """Return the destination path for an artifact type in the target repo."""
        pass

    @abstractmethod
    def get_global_destination(self, artifact_type: str) -> Path:
        """Return the global config path for an artifact type."""
        pass
