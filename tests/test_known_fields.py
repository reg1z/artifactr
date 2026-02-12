"""Tests for known_fields module."""

import pytest

from artifactr.known_fields import (
    KNOWN_FIELDS,
    KnownField,
    get_known_field,
    get_known_field_names,
)


class TestKnownFieldsRegistry:
    """Tests for the known fields registry structure."""

    def test_registry_is_list(self):
        """Verify KNOWN_FIELDS is a list."""
        assert isinstance(KNOWN_FIELDS, list)

    def test_all_entries_are_known_field(self):
        """Verify all entries are KnownField instances."""
        for field in KNOWN_FIELDS:
            assert isinstance(field, KnownField)

    def test_required_attributes(self):
        """Verify all fields have required attributes."""
        for field in KNOWN_FIELDS:
            assert field.name, f"Field missing name"
            assert field.description, f"Field {field.name} missing description"
            assert field.field_type in ("text", "boolean", "select"), (
                f"Field {field.name} has invalid type: {field.field_type}"
            )
            assert isinstance(field.supported_by, list), (
                f"Field {field.name} supported_by must be list"
            )
            assert len(field.supported_by) > 0, (
                f"Field {field.name} must be supported by at least one tool"
            )

    def test_select_fields_have_options(self):
        """Verify select-type fields have options defined."""
        for field in KNOWN_FIELDS:
            if field.field_type == "select":
                assert len(field.options) > 0, (
                    f"Select field {field.name} has no options"
                )

    def test_unique_names(self):
        """Verify all field names are unique."""
        names = [f.name for f in KNOWN_FIELDS]
        assert len(names) == len(set(names))


class TestRequiredFields:
    """Tests for required Claude Code fields being present."""

    REQUIRED_FIELDS = [
        "argument-hint",
        "disable-model-invocation",
        "user-invocable",
        "allowed-tools",
        "model",
        "context",
        "agent",
    ]

    def test_all_required_fields_present(self):
        """Verify all required Claude Code fields are in the registry."""
        names = get_known_field_names()
        for field_name in self.REQUIRED_FIELDS:
            assert field_name in names, f"Required field missing: {field_name}"

    def test_boolean_fields(self):
        """Verify boolean fields have correct type."""
        for name in ["disable-model-invocation", "user-invocable"]:
            field = get_known_field(name)
            assert field is not None
            assert field.field_type == "boolean"

    def test_context_is_select(self):
        """Verify context field is a select type with options."""
        field = get_known_field("context")
        assert field is not None
        assert field.field_type == "select"
        assert "full" in field.options
        assert "none" in field.options

    def test_text_fields(self):
        """Verify text fields have correct type."""
        for name in ["argument-hint", "allowed-tools", "model", "agent"]:
            field = get_known_field(name)
            assert field is not None
            assert field.field_type == "text"


class TestHelperFunctions:
    """Tests for registry helper functions."""

    def test_get_known_field_found(self):
        """Verify get_known_field returns correct field."""
        field = get_known_field("context")
        assert field is not None
        assert field.name == "context"

    def test_get_known_field_not_found(self):
        """Verify get_known_field returns None for unknown fields."""
        field = get_known_field("nonexistent-field")
        assert field is None

    def test_get_known_field_names(self):
        """Verify get_known_field_names returns all names."""
        names = get_known_field_names()
        assert len(names) == len(KNOWN_FIELDS)
        assert all(isinstance(n, str) for n in names)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
