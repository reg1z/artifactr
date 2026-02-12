## ADDED Requirements

### Requirement: TUI application
The interactive mode MUST launch a Textual application for guided skill creation.

#### Scenario: TUI launch
- **WHEN** `art create skill my-skill` is run without content flags
- **THEN** a Textual TUI form is displayed in the terminal

#### Scenario: TUI exit on cancel
- **WHEN** the user selects "Cancel" in the TUI
- **THEN** no files are created and the command exits with code 0

#### Scenario: TUI exit on create
- **WHEN** the user fills in fields and selects "Create"
- **THEN** the skill is created using the provided values and a confirmation is printed

### Requirement: Default form fields
The TUI form MUST display a minimal set of fields by default.

#### Scenario: Pre-populated name
- **WHEN** the TUI launches for `art create skill my-skill`
- **THEN** the Name field is pre-populated with "my-skill" and is editable

#### Scenario: Description field
- **WHEN** the TUI launches
- **THEN** a Description text input field is displayed

#### Scenario: Content area
- **WHEN** the TUI launches
- **THEN** a Content textarea is displayed for the markdown body

### Requirement: Add Field picker
The TUI MUST provide an "Add Field" button that opens a modal for adding fields to the form.

#### Scenario: Picker opens
- **WHEN** the user activates the "Add Field" button
- **THEN** a modal picker is displayed

#### Scenario: Custom field first
- **WHEN** the picker modal is displayed
- **THEN** a custom field name input appears at the top, above the known fields list

#### Scenario: Adding a custom field
- **WHEN** the user enters a custom field name and confirms
- **THEN** a new text input field is added to the form with that name as the label

#### Scenario: Known fields list
- **WHEN** the picker modal is displayed
- **THEN** all known fields from the registry are listed below the custom field input

#### Scenario: Search/filter
- **WHEN** the user types in the picker search input
- **THEN** both custom field creation and the known fields list are filtered by the search text

### Requirement: Known field tooltips
Each known field in the picker and on the form MUST display tooltip information.

#### Scenario: Tooltip content
- **WHEN** a known field's tooltip is displayed
- **THEN** it shows the field's description and which tools support it (e.g., "Supported by: claude-code")

#### Scenario: Tooltip on picker
- **WHEN** a known field is listed in the picker
- **THEN** a tooltip icon or hover area is available to view the field's description

#### Scenario: Tooltip on form
- **WHEN** a known field has been added to the form
- **THEN** a tooltip icon is displayed next to the field showing its description and tool compatibility

### Requirement: Known field input types
Known fields MUST render with appropriate input widgets based on their field type.

#### Scenario: Text field
- **WHEN** a known field with type "text" is added (e.g., `argument-hint`, `allowed-tools`)
- **THEN** a text input widget is displayed

#### Scenario: Boolean field
- **WHEN** a known field with type "boolean" is added (e.g., `disable-model-invocation`, `user-invocable`)
- **THEN** a checkbox/switch widget is displayed with the correct default value

#### Scenario: Select field
- **WHEN** a known field with type "select" is added (e.g., `context`)
- **THEN** a dropdown select widget is displayed with the field's valid options

### Requirement: Field removal
Users MUST be able to remove added fields from the form.

#### Scenario: Remove button
- **WHEN** a field has been added via the picker
- **THEN** a remove/delete affordance is displayed next to the field

#### Scenario: Removing a field
- **WHEN** the user activates the remove affordance for a field
- **THEN** the field is removed from the form and becomes available again in the picker

### Requirement: Form validation
The TUI MUST validate required fields before allowing creation.

#### Scenario: Missing description
- **WHEN** the user attempts to create without entering a description
- **THEN** the description field is highlighted and creation is prevented

#### Scenario: Valid form
- **WHEN** name and description are filled
- **THEN** the Create button is enabled
