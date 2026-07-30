# company_intro_source_packet_thickness_2026-04-25 TASK

## Global Rules

- `1 issue = 1 narrow hypothesis = 1 owner scope`.
- Green phases continue without waiting for user confirmation.
- Same error may be retried up to `3` times in one phase. Stop after the third same error and report phase, command, error excerpt, attempted fixes, blocked responsibility, rollback candidate, and residual risk.
- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Company introduction required slots remain:
  - `current_business`
  - `customer_situation_or_entry_point`
  - `support_scope_boundary`
  - `operating_process_steps`
  - `pre_contact_decision`
- Fix scope is only `article_type=branding` plus `semantic_article_key=company_introduction`.

## Forbidden Changes

- Broad length increase across article types.
- `target_chars` / `length_mode` change.
- `quality_guard.py` threshold relaxation.
- Repair count increase.
- Repair acceptance change.
- Prompt accretion.
- Persona / editor / trial names in runtime prompt or visible text.
- Internal terms such as `source_limit`, `hidden`, `PATCH_SCOPE`, or validation wording in visible article text.
- Source-outside claim permission.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | read / baseline / package | plan package only | no | required docs/logs read, package created, baseline tests recorded |
| 1 | code map / hypothesis | code inspection and `PROGRESS.md` | no | source packet compression path and one owner selected |
| 2 | focused failing/regression test | one test file | no runtime behavior change | focused test proves current material is too terse or locks current metrics |
| 3 | narrow implementation | one owner scope selected in Phase 1 | yes | required slot explanation material kept bounded and source-backed |
| 4 | focused tests | tests only | no additional runtime change | focused and owner-local tests pass |
| 5 | live validation | timestamped logs | behavior validation | 10 Kyoto source-rich runs recorded and classified |
| 6 | shared regression | boundary tests | no additional runtime change | shared tests pass if live did not worsen |
| 7 | closeout | `PROGRESS.md`, optional `WORKLOG.md` | no additional runtime change | final verdict recorded |

## Phase 0 Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
```

## Phase 1 Code Map

- Inspect company introduction source packet / runtime source contract / script packet / must-cover / grounding flow.
- Identify where `source_total_chars=3242` becomes `source_packet_chars=638`.
- Select one owner before code changes.
- Candidate owner order:
  - `note/simple_note_pipeline/pipeline.py`
  - `note/simple_note_pipeline/company_intro_source_contract_guard.py`
  - `note/newalgorithm_pipeline/input_contract.py` only if compression is upstream and narrow
  - `note/simple_note_pipeline/prompt_builder.py` only if the existing packet is present but not consumed

## Phase 2 Focused Test

- Add a Kyoto source-rich fixture based test for `company_introduction`.
- Expected assertion target is packet / contract material thickness, not final body length.
- Candidate assertions:
  - required slot extracted text is not only a short phrase
  - `support_scope_boundary` and `pre_contact_decision` retain source-backed sentence material
  - company intro source packet chars increase from current baseline but stay bounded
  - internal terms do not enter the source packet or visible prompt material
- If red cannot be produced, lock the current compressed metrics as a regression assertion first.

## Phase 3 Implementation Boundaries

- Change only the Phase 1 owner.
- Keep each required slot explanation material roughly `80-180` chars when source supports it.
- Keep total company intro packet / contract material bounded.
- Preserve source-backed wording; do not invent facts.
- Keep non-company-introduction behavior unchanged.

## Phase 4 Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "company_intro_source_contract or company_introduction_source_contract"
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
```

## Phase 5 Live Validation

- Run Kyoto Kogyo source-rich `company_introduction` for `10` runs.
- Save under:

```text
C:\tetie\notecode\logs\company_intro_source_packet_thickness_YYYYMMDD-HHMMSS\
```

- Record:
  - success rate and fail-closed count
  - body chars min / max / avg
  - body / target avg
  - source total chars
  - source packet chars
  - source packet / contract material lengths by required slot
  - required slot visible coverage
  - source-outside claim check
  - internal-term leakage check
  - Codex visible evaluation
  - old/new failure classification

## Phase 6 Shared Regression

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_vnext_current_boundary_freeze.py -q
```

## Success Criteria

- Required slot visible coverage remains `5/5`.
- Source-outside claim increase is `0`.
- Internal-term leakage is `0`.
- Fail-closed count does not increase materially.
- Body / target average improves from `0.6146`, preferably toward `0.70-0.85`, without padding.
- Codex visible review reads as source-backed explanation, not redundancy.
