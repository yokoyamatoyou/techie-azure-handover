# pipeline_responsibility_split_2026-04-24 TASK

## Global Rules

- Behavior-preserving extraction first.
- Keep private helper compatibility through imports in `pipeline.py`.
- New helper modules must not import `pipeline.py`.
- Keep runtime / internal terms out of visible article text.
- Same error may be retried up to 3 times per phase.

## Phase Map

| Phase | Responsibility | Owner Files | Required Check |
|---|---|---|---|
| 0 | Baseline | docs only | `pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q` |
| 1 | Hidden late validation | `hidden_late_validation.py`, `pipeline.py` | `pytest note\tests\test_simple_note_pipeline.py -q -k "hidden_late"` |
| 2 | Company intro source contract guard | `company_intro_source_contract_guard.py`, `pipeline.py` | `pytest note\tests\test_simple_note_pipeline.py -q -k "company_intro_source_contract or company_introduction_source_contract"` |
| 3 | Visible opener guard | `company_intro_opener_guard.py`, `pipeline.py` | `pytest note\tests\test_simple_note_pipeline.py -q -k "visible_opener_guard"` |
| 4 | Repair acceptance helpers | `repair_acceptance.py`, `pipeline.py` | `pytest note\tests\test_simple_note_pipeline.py -q -k "repair or source_contract_clear or fingerprint"` |
| 5 | Owner-local regression | split modules, `pipeline.py` | `pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q` |
| 6 | Shared regression | current success path | shared commands from user prompt |
| 7 | Post-green connection investigation | narrow TBD | live validation and targeted tests |

## Stop Rule

- Stop after 3 repeated failures with the same error in one phase.
- Report phase, command, error excerpt, attempted fixes, blocked responsibility, rollback candidate.
