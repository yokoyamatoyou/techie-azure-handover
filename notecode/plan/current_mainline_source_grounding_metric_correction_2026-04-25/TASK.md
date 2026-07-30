# TASK

## Phase 0: Package Start

- Create README / TASK / PROGRESS / ROLLBACK.
- Record hard decision, owner scope, candidate comparison, and rollback boundary.

## Phase 1: Focused Tests First

Add focused tests in `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`.

Required fixtures:

- Case 4 false positive:
  - duplicated title-like anchors are present.
  - old item ratio is below `0.5`.
  - deduped group ratio is at least `0.5`.
  - missing groups are duplicated title-like only.
  - auxiliary pass is true.
  - `source_grounding:weak_reflection` is not emitted.
- Case 1 mixed:
  - partial group and non-title-like missing groups remain.
  - auxiliary pass is false.
  - `source_grounding:weak_reflection` remains.
- True omission:
  - duplicated title-like group can exist, but main non-title-like source groups are missing.
  - auxiliary pass is false.
  - `source_grounding:weak_reflection` remains.

## Phase 2: Narrow Owner Implementation

Implement only in `quality_observability_mixin.py`.

- Add internal-only metrics:
  - `source_grounding_group_reflection_ratio`
  - `source_grounding_group_auxiliary_pass`
  - `source_grounding_group_auxiliary_pass_reason`
- Change only the `source_grounding:weak_reflection` append condition to use the auxiliary pass.
- Keep existing item-based source grounding metrics unchanged.

## Phase 3: Verification

Run:

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q -k "source_grounding"`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`

## Phase 4: Closeout

- Update PROGRESS with test results and final decision.
- Update `C:\tetie\WORKLOG.md`.
- Do not update AGENTS unless source-of-truth routing changes.
