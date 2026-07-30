# current_mainline_source_grounding_reflection_diagnosis_2026-04-25 ROLLBACK

## Baseline

- Current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- Completed predecessor:
  - `C:\tetie\notecode\plan\current_mainline_fingerprint_policy_resolution_2026-04-25\`

## Rollback Boundary

- Product rollback target:
  - none
- Package rollback target:
  - remove or supersede this docs-only package if a better diagnosis package replaces it.
- No runtime files, tests, prompts, guards, thresholds, or UI files were changed.

## Do Not Roll Back For

- Fingerprint-only warnings remaining visible in internal observability.
- Case 1 / Case 4 continuing to fail-closed when `source_grounding:weak_reflection` appears.
- Body being acceptable but strict source-anchor reflection remaining below threshold.

## Do-Not-Retry

- `source_grounding:weak_reflection` warning-only demotion.
- Fingerprint-only demotion scope expansion.
- Fingerprint threshold relaxation.
- Source grounding threshold relaxation.
- `quality_guard.py` relaxation.
- Prompt accretion.
- Repair trigger or repair count increase.
- Target chars / length mode workaround.
- Broad `output_guard.py` recomputation.
- `note_writer_app.py` UI-side additional demotion.
- `simple_note_pipeline\pipeline.py` ad-hoc branch accumulation.

## Stop Boundary

- This package is stopped before implementation.
- A future implementation must be a separate package with one owner file and one hypothesis.
- If the next fix requires multiple owners, guard relaxation, or prompt / repair growth, stop and report rather than implementing.

## Candidate Follow-Up Boundary

- Allowed first owner if management chooses to continue:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Allowed first hypothesis:
  - expose deduped / matched / missing source-grounding anchor groups for diagnosis.
- Not allowed as first step:
  - changing blocking policy
  - changing source grounding threshold
  - changing prompt content
  - changing repair behavior
  - changing UI demotion logic
