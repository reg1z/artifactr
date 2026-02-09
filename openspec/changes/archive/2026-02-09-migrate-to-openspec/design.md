## Context

Artifactr's specs and plans are currently maintained using an in-house system:

- 3 spec files (`specs/artifactr_spec.md`, `v2_features_spec.md`, `v3_features_spec.md`) using an addendum model
- 3 paired plan files (`plans/*_plan.md`) with phase/task checklists
- AI meta-prompts (`prompts/`) that instruct agents to study specs and implement tasks
- A manual traceability table (`LUT.md`) mapping spec sections to source files
- Agent coding conventions in `AGENTS.md`

All features across all three spec/plan generations are fully implemented. This migration is purely a documentation restructuring — no code changes.

## Goals / Non-Goals

**Goals:**
- Decompose monolithic specs into 5 capability-based OpenSpec specs (`core`, `importing`, `vaults`, `discovery`, `cli`)
- Merge addendum content (v2, v3) into the relevant capability specs so each spec is a complete source of truth
- Archive the original spec + plan pairs as completed OpenSpec changes with git-derived dates
- Configure `openspec/config.yaml` with project context
- Clean up `AGENTS.md` to remove the now-obsolete addendum convention

**Non-Goals:**
- Modifying any application code
- Rewriting requirement language — preserve the existing spec language, reformatted into OpenSpec's requirement/scenario structure
- Migrating `LUT.md` — it serves a separate cross-cutting purpose
- Migrating `prompts/` — these are historical artifacts
- Deleting the original `specs/` or `plans/` directories (the user can do this later if desired)

## Decisions

### 1. Capability decomposition follows interface/logic separation

The 5 capabilities split along a clear boundary: 4 capability specs describe *what the system does* (core, importing, vaults, discovery) and 1 spec describes *how users interact with it* (cli). This means a future GUI/TUI would add its own interface spec alongside `cli/` without touching the capability specs.

**Alternative considered:** A single monolithic spec. Rejected because it doesn't support granular delta-specs for future changes and defeats the purpose of OpenSpec's capability model.

### 2. Addendum content is merged, not layered

v2 and v3 requirements are folded into the capability spec where they belong (e.g., `--artifacts` goes into `importing/`, `--all` goes into `vaults/`). This eliminates the addendum chain and gives each spec a single, complete view of its capability.

**Alternative considered:** Keeping addendum structure within OpenSpec. Rejected because OpenSpec's delta-spec workflow replaces the need for manual addendums.

### 3. Archive naming uses git commit dates

Archive directories use the date from the git commit that introduced each spec/plan pair:
- `2026-01-30-initial-implementation` (initial commit)
- `2026-02-07-v2-features` (v2 commit)
- `2026-02-07-v3-features` (v3 commit)

These archives contain the original files as historical reference, not full OpenSpec artifacts (since proposal/design/tasks never existed for those changes).

### 4. Original files are preserved

The `specs/` and `plans/` directories are not deleted during this migration. The user can remove them after verifying the OpenSpec specs are complete. This is a safe, non-destructive migration.

## Risks / Trade-offs

- **[Spec completeness]** Decomposing and reformatting requirements could drop details. → Mitigation: Cross-reference the original specs during review; keep originals until verified.
- **[Duplicate truth]** During transition, both old `specs/` and new `openspec/specs/` exist. → Mitigation: Document that `openspec/specs/` is now authoritative; old files are reference-only.
- **[Archive fidelity]** Archived changes won't have proposal/design/tasks artifacts. → Mitigation: Acceptable — they represent pre-OpenSpec history and serve as dated snapshots, not active workflow artifacts.
