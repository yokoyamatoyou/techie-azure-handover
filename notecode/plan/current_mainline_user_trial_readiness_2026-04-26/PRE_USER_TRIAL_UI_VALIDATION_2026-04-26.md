# PRE_USER_TRIAL_UI_VALIDATION_2026-04-26

Date: 2026-04-26 JST

## Scope

- Objective: user trial 前 UI 実操作 validation
- Product code change: none
- Prompt / threshold / repair count / quality guard / output guard / pipeline / UI / image logic change: none
- UI URL used: `http://127.0.0.1:8080/`
- Existing listeners were used; no new product server was started.
- Fixed source snapshot:
  - `C:\tetie\notecode\logs\post_phase06a_success_path_ui_smoke_20260426-200726\source_snapshot_manifest_used.json`
- Artifact:
  - `C:\tetie\notecode\logs\pre_user_trial_ui_validation_20260426-205318\`

## Result

| Article type | Attempt 1 | Attempt 2 | Attempt 3 |
|---|---|---|---|
| `announcement` | `ui_harness_failure` | `ui_harness_failure` | `publishable_success` / `OK` / body `431` |
| `comparative_review` | `publishable_success` / `OK` / body `1858` / image success | `ui_harness_failure` | `input_required_block` / `SYS_QUALITY_WARNINGS_UNRESOLVED` / `blocked_output_redacted=true` |
| `company_introduction` | `ui_harness_failure` | `ui_harness_failure` / `ERR_CONNECTION_REFUSED` | `ui_harness_failure` / `ERR_CONNECTION_REFUSED` |

## Image

- Required target was 1 image check per article type.
- Completed:
  - `comparative_review` attempt 1
    - `with_text`: success, file exists, readable
    - `without_text`: success, file exists, readable
    - image failure did not affect article success
- Not completed:
  - `announcement`: image-designated attempt failed before article success
  - `company_introduction`: image-designated attempt failed before article success

## Copy / Legal

- Representative copy-button check: not completed.
- Representative legal-panel check: not completed.
- Reason: UI operation failures occurred, then 8080 stopped accepting connections before those checks could be performed.

## Stop Conditions Observed

- `blocked_output_redacted=true` on `comparative_review` attempt 3.
- 8080 listener was lost during the run; later attempts received `ERR_CONNECTION_REFUSED`.
- App log contains runtime tracebacks around deleted NiceGUI client/slot state:
  - `RuntimeError: The client this element belongs to has been deleted.`
  - `RuntimeError: The parent element this slot belongs to has been deleted.`
  - `Accept failed on a socket ... laddr=('127.0.0.1', 8080)`

## Negative Checks

- Startup ImportError / ModuleNotFoundError: not observed in captured excerpt.
- Internal-term leakage in completed captured attempts: not observed.
- Source-outside claim in completed captured attempts: not observed.
- UI/summary classification mismatch: not proven on completed attempts; `company_introduction` could not be validated.
- Product code hash diff: `NO_PRODUCT_CODE_HASH_DIFF`.
- `18080` final listener: none.

## Judgment

Do not proceed to first user trial from this run. The run found blocking UI/server stability issues and did not complete the required `company_introduction`, `announcement` image, copy, or legal representative checks.
