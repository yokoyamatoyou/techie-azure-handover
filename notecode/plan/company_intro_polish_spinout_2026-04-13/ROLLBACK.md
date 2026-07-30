# company_intro_polish_spinout_2026-04-13 ROLLBACK

## Restore Boundary

- current package source-of-truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- runtime path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- separate package only:
  - `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\`

## Keep Baseline

- current package keep baseline:
  - `C:\tetie\notecode\logs\codex_blank_company_intro_prompt_builder_first_section_20260413-200211\summary.json`
  - `C:\tetie\notecode\logs\codex_blank_company_intro_prompt_builder_first_section_20260413-200211\comparison_to_baselines.json`
- prompt-only floor:
  - `C:\tetie\notecode\logs\codex_parallel_evidence_sprint_blank_company_intro_20260413-213955\combined_summary.json`

## Rollback Lines Not To Reopen

- `C:\tetie\notecode\note\natural_blog_core.py`
  - first section history clamp
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
  - formatter-only surface polish
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - upstream distilled summary only

## Spin-Out Rollback Rule

- rollback unit is only:
  - `input_contract.py` narrow diff
  - `prompt_builder.py` narrow diff
  - focused test additions
- if keep baseline と prompt-only floor の両方に勝てなければ rollback
- if first heading stays current-business-first only by dropping must-cover / grounding / anchor, rollback
- if paired line needs third owner, stop and rollback

## Actual Rollback Outcome

- best attempt artifact:
  - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-234809\summary.json`
  - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-234809\comparison_to_baselines.json`
- confirmatory failed attempt:
  - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-235302\summary.json`
  - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-235302\comparison_to_baselines.json`
- rollback reason:
  - attempt 1 は company-name repetition と anchor を改善したが avg ai_index が keep baseline と prompt-only floor の両方に届かなかった
  - attempt 2 は handoff を softer にしても avg ai_index がさらに悪化した
  - same bounded hypothesis のまま third try を続けても keep 条件を満たす見込みが弱い
- final state:
  - owner diff rollback 済み
  - current package source-of-truth untouched
  - spin-out docs / logs only retain evidence

## Expected Failure Modes

- history label stays in main focus and reorders must-cover
- core_message becomes too explanatory and raises brochure/card feel
- prompt brief becomes longer instead of cleaner
- public web compare pattern is mimicked superficially while source grounding weakens
