## Context

The CLI currently has three vault resolution patterns: multi-vault (link/unlink only), single-vault (most commands), and all-vaults (tool info, vault list). The `_resolve_vault_scope()` function already handles repeatable + comma-separated `-V` flags with name/path resolution. Most commands use a simple single-vault pattern that resolves `--vault` or falls back to default.

Import summary output is identical regardless of `--link`, and `proj ls`/`conf ls` strip link state during cache parsing.

## Goals / Non-Goals

**Goals:**
- Extend multi-vault `-V` to all commands where it makes sense
- Show link state in import summaries and list output
- Add `--all` discovery flags for tool commands
- Update README Extended Usage section

**Non-Goals:**
- Changing `art rm` or `art edit` to multi-vault (destructive/editing operations stay single-vault)
- Refactoring the vault resolution into a unified framework (pragmatic per-command changes)
- Adding new commands or subcommands

## Decisions

### 1. Reuse `_resolve_vault_scope()` for multi-vault commands

The existing `_resolve_vault_scope()` already handles repeatable + comma-separated vault flags. Rather than creating a new abstraction, extend the pattern: commands that need multi-vault will use `action="append"` on their `-V` flag and call `_resolve_vault_scope()` to get a list of vault labels/paths.

For commands that operate on vault paths (not labels), a parallel `_resolve_vault_paths()` helper will return `list[Path]` instead of `list[str]`. This avoids changing the existing function's return type.

**Alternative considered:** A single `resolve_vaults()` returning both labels and paths. Rejected because the label-based resolution (for cache lookups) and path-based resolution (for filesystem operations) have different needs.

### 2. Loop-at-handler-level for multi-vault commands

For commands like `store`, `create`, and `tool add` that now accept multiple vaults: the handler loops over resolved vaults and runs the core operation for each. This keeps the core logic (e.g., `store_artifacts()`, `create_artifact()`) unchanged.

For listing commands (`art ls`, `tool ls`), results are aggregated across vaults before display. `art ls` adds a VAULT column when listing multiple vaults.

### 3. Import summary tracks link state per-type

The import result dict gains link state info. The summary function uses it:
```
claude-code:
  skills: 3 (linked)
  commands: 1 (copied)
```

The `result["imported"]` dict values change from `int` counts to `dict` with `{"count": N, "link_state": "linked"|"copied"|None}`, or more simply, parallel `imported_linked` / `imported_copied` dicts. The simpler approach: pass the link flag to `print_import_summary()` and append it to the total line.

**Decision:** Pass link mode as a parameter to `print_import_summary()`. All artifacts in a single import share the same link mode, so per-type tracking is unnecessary — just append `(linked)` or `(copied)` to each non-zero line.

### 4. List output format with arrows and STATE column

`_load_cache_entries()` and `_load_global_cache_entries()` currently strip the `:suffix`. Change them to preserve and return the link state. Display format:

```
NAME               TYPE      TOOL         VAULT       STATE
helping-hand  →    skill     claude-code  favorites   linked
code-review        skill     claude-code  favorites   copied
deploy-prod   ⇒    command   opencode     favorites   hardlinked
```

Arrow is prepended to type column or appended to name for alignment simplicity. `win_hardlinked` displays as `hardlinked`. Legacy entries (no suffix) display as `copied`.

### 5. `--all` flag semantics for tool commands

- `art tool ls --all`: Calls `load_all_vault_tools()` to get tools from every catalog vault, plus `load_global_tools()`. Aggregates and displays with vault source column.
- `art tool info --all`: Shows all tool definitions from all sources (built-in, global config, every catalog vault). Extends existing `_tool_info_catalog()` which already has multi-source logic.

### 6. `-V` on proj/conf ls, rm, wipe

These commands operate on the import cache. The cache entries already contain vault labels. Adding `-V` filters entries by vault label before display/removal. This is a filter operation, not a vault resolution — no filesystem vault access needed.

## Risks / Trade-offs

- **Output formatting complexity**: Adding STATE column and arrows increases formatting logic. Mitigated by keeping it in the existing tabular output pattern.
- **Multi-vault store could be slow**: Storing into N vaults means N copies. Acceptable since this is an explicit user action and vault count is typically small (2-3).
- **`--all` on tool info could be verbose**: Many vaults × many tools = large output. Acceptable for a discovery/diagnostic command.
