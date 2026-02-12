import sys

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Rule,
    Select,
    Static,
    Switch,
    TextArea,
)

from .creator import create_skill, resolve_project_target, resolve_vault_target
from .known_fields import KNOWN_FIELDS, get_known_field


class FieldPickerScreen(ModalScreen[str | None]):
    """Modal screen for picking a field to add."""

    CSS = """
    FieldPickerScreen {
        align: center middle;
    }

    #picker-container {
        width: 72;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #picker-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #custom-field-input {
        margin-bottom: 1;
    }

    #known-fields-label {
        margin-top: 1;
        margin-bottom: 1;
        text-style: bold;
        color: $text-muted;
    }

    #known-fields-list {
        height: auto;
        max-height: 20;
    }

    #known-fields-list > ListItem {
        padding: 0;
        height: auto;
    }

    .field-entry {
        height: auto;
        padding: 0 1;
    }

    .field-name {
        text-style: bold;
    }

    .field-desc {
        color: $text-muted;
    }

    .field-tool {
        color: $success;
    }

    .field-separator {
        margin: 0;
        color: $border;
    }

    #picker-buttons {
        margin-top: 1;
        align: center middle;
    }
    """

    def __init__(self, added_field_names: set[str]) -> None:
        super().__init__()
        self.added_field_names = added_field_names

    def compose(self) -> ComposeResult:
        available = [f for f in KNOWN_FIELDS if f.name not in self.added_field_names]

        with Vertical(id="picker-container"):
            yield Label("Add Field", id="picker-title")
            yield Input(placeholder="Custom field name (press Enter to add)...", id="custom-field-input")
            yield Label("Known Fields", id="known-fields-label")

            items = []
            for i, f in enumerate(available):
                tools_str = ", ".join(f.supported_by)
                children = []
                if i > 0:
                    children.append(Rule(classes="field-separator"))
                children.append(
                    Vertical(
                        Static(f.name, classes="field-name"),
                        Static(f.description, classes="field-desc"),
                        Static(f"Tool: {tools_str}", classes="field-tool"),
                        classes="field-entry",
                    )
                )
                items.append(ListItem(*children, name=f.name))

            yield ListView(*items, id="known-fields-list")
            with Horizontal(id="picker-buttons"):
                yield Button("Cancel", variant="default", id="picker-cancel")

    @on(Input.Submitted, "#custom-field-input")
    def on_custom_submit(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if value:
            self.dismiss(f"custom:{value}")

    @on(ListView.Selected, "#known-fields-list")
    def on_known_selected(self, event: ListView.Selected) -> None:
        field_name = event.item.name
        if field_name:
            self.dismiss(f"known:{field_name}")

    @on(Button.Pressed, "#picker-cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)


class CreateSkillApp(App):
    """Textual TUI for interactive skill creation."""

    CSS = """
    #form-scroll {
        height: 1fr;
        padding: 1 2;
    }

    .form-label {
        margin-top: 1;
        text-style: bold;
    }

    .field-row {
        height: auto;
        margin-top: 1;
    }

    .field-header {
        height: 1;
    }

    .field-label {
        text-style: bold;
        width: 1fr;
    }

    .tooltip-text {
        color: $text-muted;
        margin-left: 2;
    }

    .remove-btn {
        width: auto;
        min-width: 8;
    }

    #buttons {
        dock: bottom;
        height: 3;
        padding: 0 2;
        margin-bottom: 1;
        align: right middle;
    }

    #create-btn {
        margin-left: 1;
    }

    #description-input {
        border: tall $error;
    }

    #description-input.valid {
        border: tall $success;
    }
    """

    BINDINGS = [
        Binding("escape", "quit", "Cancel"),
    ]

    def __init__(
        self,
        skill_name: str,
        here: bool = False,
        vault: str | None = None,
        tools: str | None = None,
    ) -> None:
        super().__init__()
        self.skill_name = skill_name
        self.here = here
        self.vault = vault
        self.tools_str = tools
        self.added_fields: dict[str, dict] = {}
        self.result_code = 1  # default to error/cancel

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with VerticalScroll(id="form-scroll"):
            yield Label("Name", classes="form-label")
            yield Input(value=self.skill_name, id="name-input")
            yield Label("Description (required)", classes="form-label")
            yield Input(placeholder="What does this skill do?", id="description-input")
            yield Button("+ Add Field", variant="primary", id="add-field-btn")
            yield Vertical(id="extra-fields-container")
            yield Label("Content", classes="form-label")
            yield TextArea(id="content-area")
        with Horizontal(id="buttons"):
            yield Button("Cancel", variant="default", id="cancel-btn")
            yield Button("Create", variant="success", id="create-btn", disabled=True)
        yield Footer()

    @on(Input.Changed, "#description-input")
    def on_description_changed(self, event: Input.Changed) -> None:
        create_btn = self.query_one("#create-btn", Button)
        desc_input = self.query_one("#description-input", Input)
        has_desc = bool(event.value.strip())
        create_btn.disabled = not has_desc
        if has_desc:
            desc_input.add_class("valid")
        else:
            desc_input.remove_class("valid")

    @on(Button.Pressed, "#add-field-btn")
    def on_add_field(self) -> None:
        self.push_screen(
            FieldPickerScreen(set(self.added_fields.keys())),
            self._on_field_picked,
        )

    def _on_field_picked(self, result: str | None) -> None:
        if result is None:
            return

        if result.startswith("custom:"):
            field_name = result[7:]
            self._add_custom_field(field_name)
        elif result.startswith("known:"):
            field_name = result[6:]
            self._add_known_field(field_name)

    def _add_custom_field(self, name: str) -> None:
        if name in self.added_fields:
            return

        container = self.query_one("#extra-fields-container", Vertical)
        field_id = f"field-{name}"

        row = Vertical(id=field_id, classes="field-row")
        container.mount(row)

        header = Horizontal(classes="field-header")
        row.mount(header)
        header.mount(Label(name, classes="field-label"))
        remove_btn = Button("Remove", variant="error", classes="remove-btn", name=name)
        header.mount(remove_btn)

        widget = Input(id=f"input-{name}")
        row.mount(widget)

        self.added_fields[name] = {"type": "custom", "widget_id": f"input-{name}"}

    def _add_known_field(self, name: str) -> None:
        if name in self.added_fields:
            return

        known = get_known_field(name)
        if known is None:
            return

        container = self.query_one("#extra-fields-container", Vertical)
        field_id = f"field-{name}"

        row = Vertical(id=field_id, classes="field-row")
        container.mount(row)

        header = Horizontal(classes="field-header")
        row.mount(header)
        header.mount(Label(name, classes="field-label"))
        remove_btn = Button("Remove", variant="error", classes="remove-btn", name=name)
        header.mount(remove_btn)

        tools_str = ", ".join(known.supported_by)
        tooltip = Static(
            f"  {known.description} (Supported by: {tools_str})",
            classes="tooltip-text",
        )
        row.mount(tooltip)

        widget_id = f"input-{name}"
        if known.field_type == "boolean":
            default_val = known.default == "true" if known.default else False
            widget = Switch(value=default_val, id=widget_id)
        elif known.field_type == "select" and known.options:
            options = [(opt, opt) for opt in known.options]
            widget = Select(options, id=widget_id, allow_blank=True)
        else:
            widget = Input(id=widget_id)

        row.mount(widget)
        self.added_fields[name] = {
            "type": known.field_type,
            "widget_id": widget_id,
        }

    @on(Button.Pressed, ".remove-btn")
    def on_remove_field(self, event: Button.Pressed) -> None:
        field_name = event.button.name
        if field_name and field_name in self.added_fields:
            field_id = f"field-{field_name}"
            row = self.query_one(f"#{field_id}", Vertical)
            row.remove()
            del self.added_fields[field_name]

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self) -> None:
        self.result_code = 0
        self.exit()

    @on(Button.Pressed, "#create-btn")
    def on_create(self) -> None:
        name_val = self.query_one("#name-input", Input).value.strip()
        desc_val = self.query_one("#description-input", Input).value.strip()
        content_val = self.query_one("#content-area", TextArea).text.strip() or None

        if not desc_val:
            return

        # Use edited name for both frontmatter and directory
        skill_name = name_val or self.skill_name
        display_name = skill_name

        # Collect extra fields
        extra_fields = {}
        for field_name, info in self.added_fields.items():
            widget_id = info["widget_id"]
            if info["type"] == "boolean":
                widget = self.query_one(f"#{widget_id}", Switch)
                extra_fields[field_name] = str(widget.value).lower()
            elif info["type"] == "select":
                widget = self.query_one(f"#{widget_id}", Select)
                if widget.value is not Select.BLANK:
                    extra_fields[field_name] = str(widget.value)
            else:
                widget = self.query_one(f"#{widget_id}", Input)
                if widget.value.strip():
                    extra_fields[field_name] = widget.value.strip()

        # Resolve targets using the (possibly edited) name
        if self.here:
            tools_list = None
            if self.tools_str:
                tools_list = [t.strip() for t in self.tools_str.split(",")]
            resolution = resolve_project_target(skill_name, tools=tools_list)
            if not resolution["success"]:
                self.notify(f"Error: {resolution['error']}", severity="error")
                return
            targets = resolution["paths"]
        else:
            resolution = resolve_vault_target(skill_name, vault=self.vault)
            if not resolution["success"]:
                self.notify(f"Error: {resolution['error']}", severity="error")
                return
            targets = [resolution["path"]]

        # Create at each target
        for target_path in targets:
            result = create_skill(
                name=display_name,
                description=desc_val,
                content=content_val,
                extra_fields=extra_fields if extra_fields else None,
                target_path=target_path,
            )
            if not result["success"]:
                self.notify(f"Error: {result['error']}", severity="error")
                return
            self.notify(f"Created: {result['path']}", severity="information")

        self.result_code = 0
        self.exit()

    def action_quit(self) -> None:
        self.result_code = 0
        self.exit()


def run_create_skill_tui(
    skill_name: str,
    here: bool = False,
    vault: str | None = None,
    tools: str | None = None,
) -> int:
    """Launch the TUI for interactive skill creation.

    Args:
        skill_name: The skill identifier (directory name).
        here: Whether to create in the current project.
        vault: Optional vault name or path.
        tools: Optional comma-separated tool list.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    app = CreateSkillApp(
        skill_name=skill_name,
        here=here,
        vault=vault,
        tools=tools,
    )
    app.run()
    return app.result_code
