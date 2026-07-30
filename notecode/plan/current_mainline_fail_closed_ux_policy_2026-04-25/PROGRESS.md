# current_mainline_fail_closed_ux_policy_2026-04-25 PROGRESS

## Current Status

- Package status: implemented
- Current phase: closeout
- Product owner: `C:\tetie\notecode\note\note_writer_app.py`
- Hypothesis: the UI final-guard branch can render a non-success review draft for eligible warning-only blocked outputs without changing guard thresholds or generation behavior.
- Copy/save policy: warning付き許可。

## Evidence Read

- `current_mainline_article_type_ui_quality_validation_20260425-223000` showed bodies exist for company introduction, announcement, and daily fail-closed attempts.
- Observed body/visible internal leakage: none in collected attempts.
- Observed source outside claim evidence: none in collected bodies.
- `fingerprint-only` warning success already has a separate scoped policy and is not expanded here.
- source grounding metric correction is complete and is not reopened here.

## Classification Table

| Case | Classification | Notes |
| --- | --- | --- |
| `company_introduction_kyoto_4urls` | `review_required_draft` | rich source body exists; source reflection/style warnings remain |
| `bl-announcement-spec-change` | `review_required_draft` | route match and must-cover complete; body exists |
| `bl-daily-learning-log-grounded` attempt 2 | `review_required_draft` | synthetic UX evidence; non-legal warning shape |
| `bl-daily-learning-log-grounded` attempt 1 | `input_required_block` | legal/guarantee warning shape blocks display |
| `bl-branding-values-stance` | `input_required_block` | route mismatch and empty body |

## Implementation Notes

- Do not mark draft as `success`.
- Do not set runtime reason to `OK`.
- Persist snapshot with `blocked=True`.
- Display copy must stay sanitized and not expose internal codes.
- Non-eligible blocked outputs keep the existing blocked behavior.

## Verification

- Implemented in `C:\tetie\notecode\note\note_writer_app.py` only.
- `current_mainline_ui_result_adapter.py` was not changed.
- Added focused tests in `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`.
- Actual artifact classification check:
  - company: `review_required_draft`
  - announcement: `review_required_draft`
  - daily non-legal shape: `review_required_draft`
  - daily legal shape: `input_required_block`
  - branding mismatch: `input_required_block`
- Tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py -q` -> `29 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q` -> `137 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q` -> `36 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q` -> `260 passed`

## Actual UI Validation 2026-04-26 JST

- Execution mode: normal actual UI validation
- UI server: `HEADLESS=1`, `PORT=18080`, `C:\tetie\notecode\.venv\Scripts\python.exe -m note.note_writer_app`
- Artifact root: `C:\tetie\notecode\logs\current_mainline_fail_closed_ux_policy_ui_validation_20260426-001500\`
- Product code change: no
- Prompt / threshold / repair / success demote change: no
- Validation harness change: logs-only artifact script update for this run
- Browser reachability check: in-app browser reached `http://127.0.0.1:18080/`

### UI Results

| Case | Attempts | Runtime result | UI classification | Body visible | Warning/copy-save | Internal leakage |
|---|---:|---|---|---|---|---|
| `bl-announcement-spec-change` | 2 | 2/2 `SYS_QUALITY_WARNINGS_UNRESOLVED` | 2/2 `review_required_draft` | yes | review warning + copy/save warning visible | none |
| `bl-daily-learning-log-grounded` | 2 | 2/2 `SYS_QUALITY_WARNINGS_UNRESOLVED` | attempt 1 `review_required_draft`, attempt 2 `input_required_block` | review attempt yes, block attempt no | review attempt warning + copy/save warning visible; block attempt body-hidden warning visible | none |
| `bl-branding-values-stance` | 2 | 2/2 `SYS_PIPELINE_FAILURE` | 2/2 `input_required_block` | no | review/copy-save warning not shown | none |
| `company_introduction_kyoto_4urls` | 1 valid + 4 harness-error attempts | valid attempt `OK` | `success` | yes | review_required branch not reproduced in this run | none |

### Observations

- `review_required_draft` 実UIでは、本文 title/body が表示され、`blocked=True` / `blocked_output_redacted=True` / `runtime_reason_code=SYS_QUALITY_WARNINGS_UNRESOLVED` のまま保存された。
- `review_required_draft` の visible warning は公開前確認を促す文言で、copy/save は「確認が必要」扱いの warning として見えた。
- `input_required_block` 実UIでは、本文 title/body は表示されなかった。
- UI visible text に `SYS_*`, `source_grounding`, `fingerprint`, `contract_alignment`, `must_cover`, `PATCH_SCOPE` の漏れはなかった。
- `company_introduction_kyoto_4urls` は今回の有効 attempt では `OK` となり、`review_required_draft` 分岐の再現にはならなかった。初期 attempts 1-4 は旧 harness wait condition による `UI_HARNESS_OPERATION_ERROR` で、product code failure ではない。

### Regression

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q` -> `137 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q` -> `36 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q` -> `260 passed`
