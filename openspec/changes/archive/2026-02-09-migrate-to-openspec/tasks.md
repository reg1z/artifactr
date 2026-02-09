## 1. OpenSpec Configuration

- [x] 1.1 Update `openspec/config.yaml` with project context (tech stack: Python 3, argparse, pathlib, PyYAML; conventions: type hints, `art` CLI, decoupled logic)

## 2. Create Capability Specs

- [x] 2.1 Create `openspec/specs/core/spec.md` — cross-platform compatibility, config storage, vault structure, terminology, dependencies
- [x] 2.2 Create `openspec/specs/importing/spec.md` — tool adapters, import mapping, import command, git exclude, selective import, art-cache tracking, global import, force overwrite
- [x] 2.3 Create `openspec/specs/vaults/spec.md` — vault add, rm, select, list, list hierarchy, name
- [x] 2.4 Create `openspec/specs/discovery/spec.md` — artifact probing logic, spelunk command, store command
- [x] 2.5 Create `openspec/specs/cli/spec.md` — CLI invocation, argparse framework, default vault behavior, vault identifier resolution, tool selection, error handling

## 3. Archive Historical Changes

- [x] 3.1 Create `openspec/changes/archive/2026-01-30-initial-implementation/` containing `specs/artifactr_spec.md` and `plans/artifactr_plan.md`
- [x] 3.2 Create `openspec/changes/archive/2026-02-07-v2-features/` containing `specs/v2_features_spec.md` and `plans/v2_features_plan.md`
- [x] 3.3 Create `openspec/changes/archive/2026-02-07-v3-features/` containing `specs/v3_features_spec.md` and `plans/v3_features_plan.md`

## 4. Update AGENTS.md

- [x] 4.1 Remove the "Writing specs" section from `AGENTS.md` (the addendum convention about treating each spec as an addendum to the previous)
