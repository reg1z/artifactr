from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class KnownField:
    name: str
    description: str
    field_type: str  # "text", "boolean", "select"
    supported_by: List[str]
    default: Optional[str] = None
    options: List[str] = field(default_factory=list)


KNOWN_FIELDS = [
    KnownField(
        name="argument-hint",
        description="Hint text shown after the skill name in command listings",
        field_type="text",
        supported_by=["claude-code"],
    ),
    KnownField(
        name="disable-model-invocation",
        description="Prevent the AI model from invoking this skill autonomously",
        field_type="boolean",
        supported_by=["claude-code"],
        default="false",
    ),
    KnownField(
        name="user-invocable",
        description="Whether users can invoke this skill via slash command",
        field_type="boolean",
        supported_by=["claude-code"],
        default="true",
    ),
    KnownField(
        name="allowed-tools",
        description="Comma-separated list of tools the skill is allowed to use",
        field_type="text",
        supported_by=["claude-code"],
    ),
    KnownField(
        name="model",
        description="AI model to use when executing this skill",
        field_type="text",
        supported_by=["claude-code"],
    ),
    KnownField(
        name="context",
        description="What context to include when the skill runs",
        field_type="select",
        supported_by=["claude-code"],
        options=["full", "none"],
    ),
    KnownField(
        name="agent",
        description="Agent type to use for skill execution",
        field_type="text",
        supported_by=["claude-code"],
    ),
]


def get_known_field(name):
    for f in KNOWN_FIELDS:
        if f.name == name:
            return f
    return None


def get_known_field_names():
    return [f.name for f in KNOWN_FIELDS]
