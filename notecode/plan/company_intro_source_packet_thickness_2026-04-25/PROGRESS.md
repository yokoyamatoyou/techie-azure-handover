# company_intro_source_packet_thickness_2026-04-25 PROGRESS

## Current Status

- Package status: complete
- Current phase: Phase 7 closeout
- Behavior change: yes
- Current hypothesis:
  - `company_introduction` required slots are present, but the writer-facing source material attached to each required slot is too terse. The first implementation candidate is a bounded, company-introduction-only source packet / source contract material thickening.

## Baseline Notes

- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current mainline remains `single-pass + optional single repair 1回`.
- `company_introduction_operational_source_contract_v1` remains runtime keep.
- No runtime code changes have been made in this package yet.

## Diagnosis Inherited

- Kyoto Kogyo source-rich diagnosis:
  - success: `13/15`
  - fail-closed: `2/15`
  - successful body chars: `803-1288`
  - successful average body chars: `1106.23`
  - target chars: `1800`
  - average body / target ratio: `0.6146`
  - source total chars: `3242`
  - source packet chars: `638`
  - required visible coverage: `5/5`
- Cause classification:
  - primary: `compression_loss_suspected`
  - secondary: `realization_shallow_suspected`
  - not primary: `target_low_suspected`
  - not primary: `repair_rejection_suspected`

## Phase Ledger

| Phase | Owner files | Changed responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | `plan/company_intro_source_packet_thickness_2026-04-25/*` | new package; required docs/logs read; baseline completed | no | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`; `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q` | `255 passed`; `343 passed` | 0 | Phase 1 |
| 1 | `note/simple_note_pipeline/pipeline.py`; `note/simple_note_pipeline/company_intro_source_contract_guard.py`; `note/current_mainline_persona_trial.py`; `note/simple_note_pipeline/prompt_builder.py` inspection only | selected one owner for compression path | no | inspection and local behavior probe | owner selected: `note/simple_note_pipeline/pipeline.py` | 0 | Phase 2 |
| 2 | `note/tests/test_simple_note_pipeline.py` | added focused Kyoto source-rich packet material regression | no runtime behavior change | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "source_packet_keeps_bounded_explanation_material"` | red first: `相談したい` was 5 chars | 0 | Phase 3 |
| 3 | `note/simple_note_pipeline/pipeline.py` | company_intro required slots filled from short grounding items now prefer bounded source-document explanation candidates | yes | same focused test | green: `1 passed, 233 deselected` | 0 | Phase 4 |
| 4 | `note/tests/test_simple_note_pipeline.py`; `note/simple_note_pipeline/pipeline.py` | focused and owner-local regression | no additional behavior change | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "company_intro_source_contract or company_introduction_source_contract"`; `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q` | `15 passed, 219 deselected`; `256 passed` | 0 | Phase 5 |
| 5 | `logs/company_intro_source_packet_thickness_20260425-103407/*` | Kyoto source-rich 10-run live validation | behavior validation | reused diagnosis runner with new out-dir | `9/10` success, `1/10` fail-closed, body/target avg `0.6333`, packet chars `1693`, leakage `0/10` | 0 | Phase 6 |
| 6 | current mainline boundary tests | shared regression | no additional behavior change | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`; `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q`; `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_vnext_current_boundary_freeze.py -q` | `343 passed`; `36 passed`; `6 passed` | 0 | Phase 7 |
| 7 | `PROGRESS.md`; `ROLLBACK.md`; `C:\tetie\WORKLOG.md` | closeout record | no additional behavior change | docs update | complete | 0 | close |

## Phase 0 Read Notes

- Read:
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\PROGRESS.md`
  - `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\PROGRESS.md`
  - `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\README.md`
  - `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\TASK.md`
  - `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\PROGRESS.md`
  - `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\ROLLBACK.md`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\classification.md`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\metrics.md`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\classification.md`
  - `C:\tetie\notecode\logs\pipeline_responsibility_split_live_validation_20260425-001548\summary_enriched.json`
  - `C:\tetie\WORKLOG.md`

## Phase 1 Code Map / Hypothesis

- Observed path:
  - `_prepare_runtime_source_contracts()` calls `_prepare_company_intro_runtime_contract()` before `enrich_persona_trial_contract()`.
  - `_prepare_company_intro_runtime_contract()` builds `initial_source_pack = build_source_pack(base_contract)`.
  - `_build_company_intro_runtime_source_contract()` fills required slots from explicit contract, then existing `source_grounding_items`, then source document sentences only for still-empty slots.
  - Because Kyoto source-rich input already has compact grounding items, slots are filled by short `fact_text` values such as `相談したい` and `前処理から後処理まで一貫対応`.
  - `_merge_company_intro_runtime_contract_into_payload()` replaces `source_grounding_items` and `must_cover` with those slot values.
  - `enrich_persona_trial_contract()` then builds `_source_packet.source_facts` from the private company intro slots, so the terse slot values become the writer-facing packet.
- Local behavior probe on Kyoto source-rich fixture:
  - slot lengths: `current_business=19`, `customer_situation_or_entry_point=5`, `support_scope_boundary=14`, `operating_process_steps=67`, `pre_contact_decision=17`
  - `_source_packet.source_facts` exactly matched these terse slot values.
- Selected owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Why not other owners:
  - `company_intro_source_contract_guard.py` currently owns constants and pure validation helpers, not the runtime selection of source-backed material.
  - `current_mainline_persona_trial.py` only consumes private slot values; changing it would add a second owner and would not fix grounding / must_cover.
  - `prompt_builder.py` already consumes the prepared packet and should not be expanded.
  - `newalgorithm_pipeline/input_contract.py` would broaden source compression across routes and is not needed for this local path.
- Narrow hypothesis:
  - When a required slot is filled from a short grounding item, `pipeline.py` should replace or augment it with the best bounded source-document sentence/window for that same slot, limited to `company_introduction` and source-backed material only.

## Implementation

- Changed owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Test owner:
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- Runtime behavior:
  - only `article_type=branding` plus `semantic_article_key=company_introduction`
  - explicit runtime source contracts are preserved
  - if a required slot is filled from a short grounding item, source-document sentence/window candidates are scored for the same slot
  - selected explanation material is bounded and remains source-backed
  - no target length, repair count, repair acceptance, or quality threshold change

## Live Validation

- Artifact:
  - `C:\tetie\notecode\logs\company_intro_source_packet_thickness_20260425-103407\metrics.md`
  - `C:\tetie\notecode\logs\company_intro_source_packet_thickness_20260425-103407\classification.md`
- Result:
  - run count: `10`
  - success: `9`
  - fail-closed: `1`
  - successful body chars: `864-1358`
  - successful body avg: `1139.89`
  - body / target avg: `0.6333`
  - target chars: `1800`
  - source total chars: `3242`
  - source packet chars: `1693`
  - slot lengths: `141 / 155 / 118 / 170 / 173`
  - required visible coverage: `5/5`
  - internal-term leakage: `0/10`
- Before / after:
  - packet chars: `638 -> 1693`
  - body / target avg: `0.6146 -> 0.6333`
  - fail-closed: `2/15 -> 1/10`
- Judgment:
  - source packet thickness improved
  - visible body depth improved only slightly
  - residual should be treated as `realization_shallow_suspected` in a future separate phase, not by further packet broadening in this package

## Next Action

- Package is closed.
- If continuing later, open a separate narrow `realization_shallow_suspected` package.
