# PROGRESS

## Status

Completed.

## Hard Decision

Decision: `metric correction package needed`.

Case 4 live observation showed repeated valid weak attempts where the body was acceptable and source-aware, but item-based reflection failed because duplicated title-like source items inflated the denominator. This is not a reason to lower thresholds or demote the warning globally; it is a reason to align source grounding evaluation with deduped source-use groups for this narrow shape.

## Candidate Comparison

| Candidate | Decision | Reason |
| --- | --- | --- |
| Keep item-based only | Reject | Leaves Case 4 false positive unchanged even when duplicated title-like group is the only miss. |
| Exclude duplicate/title-like groups from denominator | Reject | Too broad; risks hiding true omissions where title-like items are still important. |
| Group-level auxiliary pass | Chosen | Narrowly suppresses the weak warning only when item ratio fails but deduped group ratio passes and all missing groups are duplicated title-like. |
| Observe only | Reject for Case 4 | Live evidence is sufficient for a narrow correction; Case 1 remains observe-only/mixed. |

## Correction Schema

Internal-only metrics added to `_source_grounding_metrics()`:

- `source_grounding_group_reflection_ratio`
- `source_grounding_group_auxiliary_pass`
- `source_grounding_group_auxiliary_pass_reason`

Auxiliary pass is true only when all are true:

- existing item ratio is `< 0.5`
- deduped group ratio is `>= 0.5`
- duplicate group exists
- every missing group has `title_like=true` and `duplicate_count > 1`
- no non-title-like missing group exists

Existing item-based metrics remain unchanged:

- `source_grounding_reflected_count`
- `source_grounding_reflection_ratio`

## Verification

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q -k "source_grounding"`
  - `5 passed, 25 deselected`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
  - `33 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - `108 passed`

## UI Validation

- Artifact root:
  - `C:\tetie\notecode\logs\current_mainline_source_grounding_metric_correction_ui_validation_20260425-214032\`
- UI server:
  - `HEADLESS=1`
  - `PORT=18080`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m note.note_writer_app`
- Product code change during validation:
  - none
- Harness note:
  - Browser Use hit a brittle custom-dropdown / validation-bubble path before generation.
  - Selenium actual UI operation was used with a fresh browser profile per attempt.
  - Current UI did not expose `この内容で生成`; after confirmation, `不足を確認` started generation and fresh `latest_generation_output.json` was used as the completion signal.

### Attempt Results

| Case | Attempt | Runtime | Classification | Item ratio | Group ratio | Auxiliary pass | `source_grounding:weak_reflection` | UI/body internal leakage |
| --- | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| Case 4 | 1 | `OK` | fingerprint warning success | `0.6667` | `0.8` | false | no | none |
| Case 4 | 2 | `OK` | fingerprint warning success | `0.7778` | `0.8` | false | no | none |
| Case 4 | 3 | `OK` | fingerprint warning success | `0.6667` | `0.8` | false | no | none |
| Case 1 | 1 | `OK` | fingerprint warning success | `0.6` | `0.6` | false | no | none |
| Case 1 | 2 | `OK` | fingerprint warning success | `0.8` | `0.8` | false | no | none |
| Case 1 | 3 | `OK` | fingerprint warning success | `0.6` | `0.6` | false | no | none |

### UI Validation Classification

- Case 4:
  - actual UI operation produced 3/3 warning successes.
  - `source_grounding:weak_reflection` did not appear.
  - fingerprint warnings remained warning-only as expected.
  - The exact old false-positive shape was not re-hit because item ratios were already `>= 0.5`; therefore `source_grounding_group_auxiliary_pass` stayed false in all three UI runs.
- Case 1:
  - actual UI operation produced 3/3 warning successes.
  - `source_grounding_group_auxiliary_pass` stayed false in all three runs.
  - No Case 1 mixed missing run appeared in this 3-attempt UI sample, so the live UI sample does not prove mixed fail-closed behavior directly.
  - The guarded fixture coverage above remains the direct evidence that Case 1 mixed and true omission shapes keep `source_grounding:weak_reflection`.
- UI leakage:
  - no visible/body leakage of `source_grounding`, `fingerprint`, `SYS_*`, `contract_alignment`, `must_cover`, or `PATCH_SCOPE` was recorded in the six UI attempts.

### Shared Regression After UI Validation

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
  - `33 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `144 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `260 passed`

## Implementation Result

- Owner file remained limited to `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`.
- Existing item metrics remain unchanged:
  - `source_grounding_reflected_count`
  - `source_grounding_reflection_ratio`
- Added internal-only group auxiliary metrics:
  - `source_grounding_group_reflection_ratio`
  - `source_grounding_group_auxiliary_pass`
  - `source_grounding_group_auxiliary_pass_reason`
- Changed only the `source_grounding:weak_reflection` append condition so it does not fire when `source_grounding_group_auxiliary_pass` is true.
- No prompt, repair, threshold, output guard, UI demote, target length, or fingerprint policy change.

## Guarded Fixtures

- Case 4 false positive shape:
  - old item ratio remains `< 0.5`.
  - deduped group ratio is `>= 0.5`.
  - only missing group is duplicated title-like.
  - auxiliary pass is true.
  - `source_grounding:weak_reflection` is not emitted.
- Case 1 mixed shape:
  - partial and non-title-like missing groups remain.
  - auxiliary pass is false.
  - `source_grounding:weak_reflection` remains.
- True omission shape:
  - duplicated title-like group may exist, but non-title-like source groups are missing.
  - auxiliary pass is false.
  - `source_grounding:weak_reflection` remains.

## Closeout

Completed. AGENTS was not updated because current source-of-truth routing did not change.
