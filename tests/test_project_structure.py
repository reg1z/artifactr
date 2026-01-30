"""Tests for project structure (Task 1.1)."""

import sys
from pathlib import Path


def test_package_importable():
    """Verify artifactr package can be imported."""
    import artifactr
    assert hasattr(artifactr, "__version__")
    assert artifactr.__version__ == "0.1.0"


def test_tools_subpackage_importable():
    """Verify tools subpackage can be imported."""
    import artifactr.tools
    assert artifactr.tools is not None


def test_project_structure_exists():
    """Verify expected directories exist."""
    project_root = Path(__file__).parent.parent

    assert (project_root / "src" / "artifactr").is_dir()
    assert (project_root / "src" / "artifactr" / "tools").is_dir()
    assert (project_root / "tests").is_dir()
    assert (project_root / "pyproject.toml").is_file()


if __name__ == "__main__":
    test_package_importable()
    test_tools_subpackage_importable()
    test_project_structure_exists()
    print("All tests passed!")
