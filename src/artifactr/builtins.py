"""Built-in skill and command files bundled with the artifactr package."""

import shutil
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path


def get_builtin_skills_root() -> Traversable:
    """Return the Traversable path to the builtin_skills package data directory."""
    return files("artifactr") / "builtin_skills"


def install_builtin_skills(
    target_skills_dir: Path,
    target_commands_dir: Path | None,
) -> dict:
    """Copy built-in skill directories and command files to target directories.

    Silently overwrites existing files.

    Args:
        target_skills_dir: Destination directory for skill subdirectories.
        target_commands_dir: Destination directory for command .md files. If None,
                             commands are skipped.

    Returns:
        {"skills_installed": int, "commands_installed": int}
    """
    root = get_builtin_skills_root()
    skills_installed = 0
    commands_installed = 0

    # Install skills (directory per skill)
    builtin_skills = root / "skills"
    target_skills_dir.mkdir(parents=True, exist_ok=True)
    for skill_entry in builtin_skills.iterdir():
        skill_name = skill_entry.name
        dest_skill_dir = target_skills_dir / skill_name
        dest_skill_dir.mkdir(parents=True, exist_ok=True)
        for file_entry in skill_entry.iterdir():
            dest_file = dest_skill_dir / file_entry.name
            dest_file.write_bytes(file_entry.read_bytes())
        skills_installed += 1

    # Install commands (flat .md files)
    if target_commands_dir is not None:
        builtin_commands = root / "commands"
        target_commands_dir.mkdir(parents=True, exist_ok=True)
        for cmd_entry in builtin_commands.iterdir():
            if cmd_entry.name.endswith(".md"):
                dest_file = target_commands_dir / cmd_entry.name
                dest_file.write_bytes(cmd_entry.read_bytes())
                commands_installed += 1

    return {"skills_installed": skills_installed, "commands_installed": commands_installed}
