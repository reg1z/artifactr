"""Generic tool adapter driven by tool definition data."""

import os
from pathlib import Path

# Artifact types supported by the system (tool-agnostic)
ARTIFACT_TYPES = ["skills", "agents", "commands"]

# Keys in a tool definition that correspond to repo-local artifact paths
_REPO_PATH_KEYS = {"skills", "commands", "agents"}

# Keys in a tool definition that correspond to global artifact paths
_GLOBAL_PATH_KEYS = {"global_skills", "global_commands", "global_agents"}


def get_source(artifact_type: str, vault_path: Path) -> Path:
    """Return the source path for an artifact type in the vault.

    This is a module-level function because sources are tool-agnostic.
    All tools read from the same vault structure.
    """
    return vault_path / artifact_type


class GenericToolAdapter:
    """Config-driven tool adapter.

    Constructed from a tool name and a config dict that follows the
    tool definition schema. Derives supported artifact types from
    which path keys are present.
    """

    def __init__(self, name: str, config: dict) -> None:
        self._name = name
        self._config = config

        # Derive supported types from which repo-local path keys are present
        self._supported_types: list[str] = []
        for key in ("skills", "commands", "agents"):
            if key in config:
                self._supported_types.append(key)

        # Expand environment variables and ~ in all path values
        self._expanded: dict[str, str] = {}
        for key in list(_REPO_PATH_KEYS | _GLOBAL_PATH_KEYS):
            if key in config:
                raw = config[key]
                expanded = os.path.expandvars(raw)
                expanded = str(Path(expanded).expanduser())
                self._expanded[key] = expanded

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_types(self) -> list[str]:
        return list(self._supported_types)

    @property
    def aliases(self) -> list[str]:
        return self._config.get("aliases", [])

    def get_destination(self, artifact_type: str, target_repo: Path) -> Path:
        """Return the destination path for an artifact type in the target repo."""
        if artifact_type not in self._supported_types:
            raise ValueError(
                f"Tool '{self._name}' does not support artifact type '{artifact_type}'"
            )
        repo_path = self._expanded[artifact_type]
        return target_repo / repo_path

    def get_global_destination(self, artifact_type: str) -> Path:
        """Return the global config path for an artifact type."""
        if artifact_type not in self._supported_types:
            raise ValueError(
                f"Tool '{self._name}' does not support artifact type '{artifact_type}'"
            )
        global_key = f"global_{artifact_type}"
        if global_key not in self._expanded:
            raise ValueError(
                f"Tool '{self._name}' has no global path for artifact type '{artifact_type}'"
            )
        return Path(self._expanded[global_key])
