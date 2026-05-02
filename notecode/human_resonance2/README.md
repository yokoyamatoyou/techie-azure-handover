# human_resonance2 Planning Workspace

## Purpose
`human_resonance2` is a planning-first sandbox for improving article human-likeness and layout stability without directly changing the existing `human_resonance` pipeline.

This folder stores:
- phase-by-phase execution plans
- progress tracking
- work logs
- config/integration contracts
- metric definitions for baseline and acceptance

## Scope
- In-scope: planning documents and execution instructions
- Out-of-scope: production code changes in this workspace

## Operating Rules
1. Update `PROGRESS.md` for status changes only.
2. Record actions and evidence in `WORKLOG.md`.
3. Keep implementation instructions only in `phases/*.md`.
4. On phase completion, update both `PROGRESS.md` and `WORKLOG.md`.
5. Error handling rule:
   - try one self-fix once
   - if still failing, stop and report status to user

## Planned Phases
1. `PHASE_00_BOOTSTRAP.md`
2. `PHASE_01_LEXICAL_DIVERSITY.md`
3. `PHASE_02_BURSTINESS.md`
4. `PHASE_03_NOMINALIZATION.md`
5. `PHASE_04_STYLE_DRIFT.md`
6. `PHASE_05_LAYOUT_GUARD.md`
7. `PHASE_06_ORCHESTRATOR.md`
8. `PHASE_07_INTEGRATION_ROLLOUT.md`

## Integration Direction
- Keep `human_resonance` untouched initially.
- Build a separate quality layer.
- Integrate in final rollout phase with config-guarded toggles and rollback path.

