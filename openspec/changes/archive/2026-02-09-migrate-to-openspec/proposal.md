## Why

The project's documentation and specs use an in-house method: addendum-style specs (`specs/artifactr_spec.md`, `v2_features_spec.md`, `v3_features_spec.md`), paired implementation plans (`plans/*_plan.md`), and AI meta-prompts (`prompts/`). This approach worked for initial development but doesn't scale — specs grow by accretion without consolidation, there's no structured change workflow, and the relationship between requirements and changes is implicit. Migrating to OpenSpec gives the project a proper spec-driven change workflow going forward.

## What Changes

- Decompose the three existing spec files into 5 capability-based OpenSpec specs: `core`, `importing`, `vaults`, `discovery`, `cli`
- Content from v2 and v3 addendum specs is merged into the relevant capability specs (single source of truth)
- Archive the original spec + plan file pairs as completed OpenSpec changes with date-based naming
- Update `openspec/config.yaml` with project context (tech stack, conventions)
- Remove the "writing specs" section from `AGENTS.md` (the addendum convention is replaced by OpenSpec's delta-spec workflow)
- `LUT.md` and `prompts/` are left untouched — they serve separate purposes

## Capabilities

### New Capabilities
- `core`: Cross-platform compatibility, configuration storage, vault structure, and dependencies (from main spec §1, §2, §3, §9)
- `importing`: Import logic, tool adapters, import mapping, selective import, art-cache tracking, global import, and force overwrite (from main spec §4, §5, §7.1 + v2 §2, §3 + v3 §1, §2)
- `vaults`: Vault CRUD operations — add, rm, select, list, name, hierarchy display (from main spec §7.2–§7.6 + v2 §1)
- `discovery`: Artifact discovery and collection — spelunk and store commands (from v2 §4, §5)
- `cli`: CLI interface conventions — argparse, `art` command, vault identifier resolution, error handling (from main spec §6, §8)

### Modified Capabilities
<!-- No existing OpenSpec capabilities to modify — this is a greenfield migration -->

## Impact

- `openspec/specs/` — 5 new spec directories created
- `openspec/changes/archive/` — 3 archived change records created
- `openspec/config.yaml` — updated with project context
- `AGENTS.md` — minor edit (remove one section)
- No code changes — this is purely a documentation/spec migration
