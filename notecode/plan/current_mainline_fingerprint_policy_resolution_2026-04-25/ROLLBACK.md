# current_mainline_fingerprint_policy_resolution_2026-04-25 ROLLBACK

## Baseline

- Current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`

## Rollback Boundary

- Product rollback target:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
  - `C:\tetie\notecode\note\note_writer_app.py`
  - focused tests added for this package
- Roll back only:
  - fingerprint-only warning classification helper
  - UI final guard demotion call
  - matching focused tests

## Do Not Roll Back For

- Fingerprint-only warnings still being present in observability.
- Case 1 stopping when `source_grounding:weak_reflection` or another non-fingerprint warning recurs.
- Bad or weak artifacts stopping when source / contract / leakage conditions are not green.

## Do-Not-Retry

- Product-wide recomputation of existing non-strict `output_guard`.
- Fingerprint threshold relaxation.
- `quality_guard.py` threshold relaxation.
- Repair count increase.
- Prompt accretion.
- Target chars / length mode workaround.
- Source packet broadening.
- Runtime/internal terms in visible body or UI.

## Stop Boundary

- Public contract tests regress.
- Warning-only classification requires multiple product owners beyond `output_guard.py` + UI connection.
- Case 4 remains fail-closed after focused policy and 3 UI attempts.
- Any visible output shows internal terms.
