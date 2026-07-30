# company_intro_length_source_diagnosis_2026-04-25 PROGRESS

## Current Status

- Package status: active
- Current phase: Phase 6 closeout
- Behavior change: no
- Current hypothesis:
  - `company_introduction` shortness under source-rich conditions is reproducible, but the previous audit did not separate target/length decision from source-packet compression and section realization.
- Current verdict:
  - `source-rich shortness reproduced`
  - primary cause: `compression_loss_suspected`
  - secondary symptom: `realization_shallow_suspected`
  - no runtime fix selected in this window

## Baseline Notes

- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current mainline remains `single-pass + optional single repair 1回`.
- `company_introduction_operational_source_contract_v1` remains runtime keep.
- Required company introduction slots remain:
  - `current_business`
  - `customer_situation_or_entry_point`
  - `support_scope_boundary`
  - `operating_process_steps`
  - `pre_contact_decision`

## Phase Ledger

| Phase | Owner files | Changed responsibility / audit responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | `plan/company_intro_length_source_diagnosis_2026-04-25/*` | new diagnosis package; required docs/logs read; baseline checks completed | no | `pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`; `pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q` | `255 passed`; `343 passed` | 0 | Phase 1 |
| 1 | `plan/company_intro_length_source_diagnosis_2026-04-25/*`; code/log inspection only | metric source map for target/source packet/realization/repair candidate fields | no | inspection only | complete | 0 | Phase 2 |
| 2 | `plan/company_intro_length_source_diagnosis_2026-04-25\diagnosis_runner.py` | diagnosis runner and log schema; raw result / metrics / visible excerpt / error files | no runtime change | `python -m py_compile plan\company_intro_length_source_diagnosis_2026-04-25\diagnosis_runner.py` | passed | 0 | Phase 3 |
| 3 | `logs/company_intro_length_source_diagnosis_20260425-095537/*`; `logs/company_intro_length_source_diagnosis_20260425-100613/*` | Kyoto Kogyo 15-run diagnosis plus optional Yoshinomore 5-run fail-closed supplement | no runtime change | runner executions | Kyoto: 13 success / 2 fail-closed; optional: 0 success / 5 fail-closed | 0 | Phase 4 |
| 4 | `logs/company_intro_length_source_diagnosis_20260425-095537/classification.*` | classify target/compression/realization/repair rejection | no | manual Codex visual review of excerpts and generated metrics | primary `compression_loss_suspected`; secondary `realization_shallow_suspected`; target/repair not primary | 0 | Phase 5 |
| 5 | none | no fix selected | no | not run | measurement sufficient for next decision, not for immediate behavior change | 0 | Phase 6 |
| 6 | `PROGRESS.md`; `ROLLBACK.md`; `C:\tetie\WORKLOG.md` | closeout record | no | baseline already green; runner py_compile passed | complete | 0 | close |

## Prior Evidence Read

- Previous source compression audit verdict:
  - `OK_with_watch_items`
  - runtime change not recommended in that package
- Company introduction watch item:
  - source total chars: `3242`
  - source packet chars: `638`
  - prior audit successful body chars: `1274`, `933`
  - previous 10-run success average: about `1105.6`
  - required operational slots reflected
  - target chars unavailable in prior artifacts
- Current diagnosis gap:
  - target / length-mode decision is not captured
  - source packet composition and section realization need per-run comparison
  - repair candidate improvement vs rejection needs direct inspection when present

## Phase 0 Notes

- Required docs read:
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12
  - current naturalness package README/TASK/PROGRESS/ROLLBACK
  - pipeline responsibility split PROGRESS
  - source compression length adequacy README/TASK/PROGRESS/ROLLBACK
  - specified prior logs
  - `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode` and `C:\tetie` did not appear to be git repository roots in this environment.
- `rg` was not usable because the bundled executable was denied by Windows; PowerShell file enumeration is used instead.
- Baseline tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
    - `255 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
    - `343 passed`

## Next Action

- Create Phase 2 diagnosis runner under this package.
- Run Kyoto Kogyo source-rich 15-run diagnosis and save raw result / metrics / visible excerpts.

## Phase 1 Instrumentation Audit Design

- No runtime code change is needed for the first diagnosis pass.
- Run entrypoint:
  - use `note.current_mainline_runner.execute_current_mainline_generation`
  - use `note.simple_note_pipeline.pipeline.MinimalPipeline`
  - same pattern as prior `source_compression_length_adequacy_2026-04-25\audit_runner.py` and `pipeline_responsibility_split_2026-04-24\live_validation_runner.py`
- Target / length fields:
  - observed `target_chars` can appear in result diagnostics / quality metrics, but was not captured by the prior audit runner
  - runner will recursively collect observed `target_chars` / `max_tokens` from result JSON when present
  - runner will also compute `estimated_target_chars` from `prompt_builder.target_chars(length_mode, article_type, source_count)`
  - `length_mode` comes from `pipeline_check.input_contract.length_mode` or payload fallback
- Source compression fields:
  - `pipeline_check.input_contract._source_packet`
  - `pipeline_check.input_contract.source_documents`
  - `pipeline_check.input_contract.source_grounding_items`
  - `pipeline_check.input_contract.must_cover`
  - company intro script packet from `body_generation.company_introduction_script_packet` and `_company_introduction_script_packet`
- Source slot fields:
  - prefer `body_generation.company_intro_observability.source_slot_coverage_final`
  - fallback to `body_generation.company_introduction_source_contract_validation`
  - failure payload can expose `pipeline_check.error.company_introduction_source_contract_repair`
- Realization fields:
  - runner-side section parser records headings, section char distribution, shortest/final section, and final paragraph chars
  - title / lead / body char counts are runner-side deterministic metrics
- Repair rejection fields:
  - `body_generation.repair_entry`
  - `body_generation.repair_call`
  - `body_generation.company_intro_observability.repair`
  - failure payload repair telemetry if present
  - `repair_candidate_summary.body_chars`, headings, section excerpts, and candidate source slot coverage when present
- Unavailable fields:
  - record as `not available`
  - do not infer zero

## Phase 2 Diagnosis Runner

- Created:
  - `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\diagnosis_runner.py`
- Runtime behavior change:
  - no
- Runner behavior:
  - calls current mainline through `execute_current_mainline_generation`
  - writes timestamped logs under `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_YYYYMMDD-HHMMSS\`
  - writes per-run raw result JSON, metrics JSON, visible excerpt TXT, and error TXT for failed runs
  - writes aggregate `metrics.jsonl`, `metrics.json`, and `metrics.md`
  - prints only ASCII-safe JSON summaries to console
- Check:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile plan\company_intro_length_source_diagnosis_2026-04-25\diagnosis_runner.py`
    - passed

## Phase 3 Diagnosis Runs

- Main artifact:
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\metrics.json`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\metrics.md`
  - per-run raw result / metrics / visible excerpt files
- Main profile:
  - `kyotokogyo_source_rich_v1`
- Result:
  - runs: `15`
  - success: `13`
  - fail-closed: `2`
  - successful body chars: `803-1288`
  - successful body average: `1106.23`
  - target chars: `1800`
  - average body / target ratio: `0.6146`
  - source total chars: `3242`
  - source summary chars: `452`
  - source packet chars: `638`
  - source packet fact count: `5`
  - grounding item count: `5`
  - must-cover count: `8`
  - required slot coverage: `5/5` on successful visible outputs
  - average shortest section chars: `200.38`
  - average final section chars: `285.31`
  - successful repair rejected: `9/13`
  - successful repair applied: `4/13`
- Optional artifact:
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-100613\metrics.json`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-100613\metrics.md`
- Optional profile:
  - `yoshinomore_law_source_rich_v1`
- Optional result:
  - runs: `5`
  - success: `0`
  - fail-closed: `5`
  - fail reason: `Company introduction naturalness rescue remained unresolved after repair`
  - source total chars: `8030`
  - source packet chars: `564`
  - target chars: `2800`
  - interpretation: fail-closed evidence only; not included as successful length sample

## Phase 4 Classification

- Output:
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\classification.md`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\classification.json`
- Classification:
  - primary cause: `compression_loss_suspected`
  - secondary symptom: `realization_shallow_suspected`
  - `target_low_suspected`: not primary
  - `repair_rejection_suspected`: not primary
  - fail-closed rows: correct containment
- Why:
  - target is `1800`, not around `1200`
  - successful body chars cluster at `803-1288`, average `1106.23`
  - source is rich enough (`3242` chars), but packet is only `638` chars with five compact facts
  - slot value lengths are very short: `19 / 5 / 35 / 46 / 63`
  - sections remain shallow, but the shallow realization appears downstream of the compressed packet
  - rejected repair candidates generally did not improve explanation quantity

## Phase 5 Decision

- Runtime fix selected:
  - no
- Reason:
  - The measurement isolates target-low and repair-rejection as unlikely primary causes.
  - The strongest next candidate is source-packet adequacy, but this package objective was diagnosis first.
  - A runtime fix should be opened as a separate narrow implementation decision, not mixed into the measurement package.
- Next decision if continuing:
  - open or defer a narrow `company_introduction` source-packet adequacy fix
  - preferred fix candidate if opened: keep slightly more source-backed explanation material for required slots
  - do not start with target length or repair acceptance

## Phase 6 Closeout

- Runtime code changes:
  - none
- Tests / checks:
  - baseline simple note / quality: `255 passed`
  - baseline current mainline shared: `343 passed`
  - diagnosis runner py_compile: passed
- WORKLOG:
  - updated `C:\tetie\WORKLOG.md`
- AGENTS:
  - not updated; current source-of-truth routing remains valid
- Next engineering decision:
  - decide whether to open a separate narrow source-packet adequacy implementation package for `company_introduction`
  - do not broaden article length globally
