# pipeline_responsibility_split_2026-04-24 PROGRESS

## Current Status

- Package status: complete
- Current phase: Phase 7 complete
- Behavior change: yes; narrow source-clearing repair acceptance/final draft reflection connection

## Phase Ledger

| Phase | Owner files | Moved responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | docs / inspection only | baseline map | no | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q` | `254 passed` | 0 | Phase 1 |
| 1 | `note/simple_note_pipeline/hidden_late_validation.py`, `note/simple_note_pipeline/pipeline.py` | hidden late validation constants, contract builder, forbidden heading/body leakage checks, required-token evaluation, failure/improvement predicates | no | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "hidden_late"` | `11 passed, 221 deselected` | 0 | Phase 2 |
| 2 | `note/simple_note_pipeline/company_intro_source_contract_guard.py`, `note/simple_note_pipeline/pipeline.py` | company intro source slot constants, source contract failure/improvement predicates, validation snapshot builder | no | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "company_intro_source_contract or company_introduction_source_contract"` | `14 passed, 218 deselected` | 0 | Phase 3 |
| 3 | `note/simple_note_pipeline/company_intro_opener_guard.py`, `note/simple_note_pipeline/pipeline.py` | company intro visible opener drift evaluation and operational identity heading rescue helper | no | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "visible_opener_guard"` | `8 passed, 224 deselected` | 0 | Phase 4 |
| 4 | `note/simple_note_pipeline/repair_acceptance.py`, `note/simple_note_pipeline/pipeline.py` | pure repair acceptance predicates for alignment preservation, ending monotony, longform growth, and fingerprint improvement | no | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "repair or source_contract_clear or fingerprint"` | `60 passed, 172 deselected` | 0 | Phase 5 |
| 5 | `note/simple_note_pipeline/*`, `note/tests/test_simple_note_pipeline.py`, `note/tests/test_simple_note_quality_guard.py` | owner-local regression after extraction | no | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q` | `254 passed` | 0 | Phase 6 |
| 6 | `note/current_mainline_runner.py`, `note/newalgorithm_pipeline/pipeline.py`, `note/simple_note_pipeline/pipeline.py`, boundary tests | shared regression for current success path, UI matrix, observability, and vnext boundary freeze | no | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`; `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q`; `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_vnext_current_boundary_freeze.py -q` | `343 passed`; `36 passed`; `6 passed` | 0 | Phase 7 |
| 7 | `note/simple_note_pipeline/pipeline.py`, `note/tests/test_simple_note_pipeline.py`, `plan/pipeline_responsibility_split_2026-04-24/live_validation_runner.py` | source-clearing repair candidate acceptance now clears the alignment gate so the repaired draft and diagnostics are reflected into final validation; added live validation runner and regression coverage | yes | `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "source_contract_clear"`; `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`; shared Phase 6 commands rerun; `C:\tetie\notecode\.venv\Scripts\python.exe plan\pipeline_responsibility_split_2026-04-24\live_validation_runner.py` | `5 passed, 228 deselected`; `255 passed`; `343 passed`; `36 passed`; `6 passed`; live `9/10 OK`, old reflection failure `0`, new/different failure `1` | 0 | closeout |

## Live Validation

- Artifact directory: `C:\tetie\notecode\logs\pipeline_responsibility_split_live_validation_20260425-001548\`
- Enriched summary: `C:\tetie\notecode\logs\pipeline_responsibility_split_live_validation_20260425-001548\summary_enriched.json`
- Conditions:
  - `article_type=branding`
  - `semantic_article_key=company_introduction`
  - `source_mode=grounded`
  - source URLs:
    - `https://www.kyotokogyo.co.jp/`
    - `https://www.kyotokogyo.co.jp/about/coprof/`
    - `https://www.kyotokogyo.co.jp/about/history/`
    - `https://www.kyotokogyo.co.jp/service/input_scaning/`
- Result: 9/10 OK.
- Old failure classification: 0/10. The pre-extraction failure shape was `repair candidate cleared=true` with final draft still failing hard validation; this did not recur.
- New/different failure classification: 1/10. Run 2 failed hard validation, but the repair candidate did not clear the source contract (`cleared=false`, `after_failure_count=1`), so it is not the prior acceptance/final-reflection connection.
- Console output note: first live runner execution wrote all 10 result files and jsonl rows, then failed only while printing run 10 to a cp932 console. The runner was fixed to print ASCII-safe JSON, and `summary_enriched.json` / `company_intro_10run_summary_enriched.jsonl` were regenerated from the raw run files without re-running LLM calls.

## Remaining Split Note

- Phase 2 intentionally kept the company intro runtime contract builders and full validation evaluator in `pipeline.py` because they still share source-pack construction, script packet building, and diagnostics mutation with the surrounding runtime flow. The extracted slice is limited to source-slot constants, failure/improvement predicates, and validation snapshot helpers.
- A future source-contract phase can move the runtime builder/evaluator as a separate owner scope after those dependencies are isolated.

## Observed Baseline

- Latest 10-run validation: 9/10 OK.
- Residual failure: `Company introduction hard source contract trigger remained after repair`.
- Repair candidate in failed run:
  - `cleared=true`
  - `improved=true`
  - `after_failure_count=0`
  - `hidden_late_after_trigger_ids=[]`
- The source-clearing repair candidate final-reflection connection was fixed after extraction green in Phase 7.
