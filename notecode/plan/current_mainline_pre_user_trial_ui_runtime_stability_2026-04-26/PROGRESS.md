# PROGRESS

## Current Status

- Package status: phase_01_runtime_validation_rerun_completed / user_trial_still_blocked
- Current phase: Phase 01 `note_writer_app.py` UI lifecycle boundary
- Date: 2026-04-26 JST
- Product code change: yes, owner-limited to `C:\tetie\notecode\note\note_writer_app.py`
- Prompt / persona / source contract / algorithm / threshold / repair / guard / pipeline / image logic change: no
- UI server startup: yes, rerun validation only
- Full-flow validation rerun: no
- WORKLOG update: completed
- AGENTS update: not needed

## Phase 01 Runtime Validation Rerun

- Date: 2026-04-26 JST
- Artifact: `C:\tetie\notecode\logs\pre_user_trial_ui_runtime_validation_rerun_20260426-214042\`
- Scope: pre-user-trial UI runtime validation rerun against `announcement`, `comparative_review`, `company_introduction`; product code unchanged.
- Product code hash diff: `NO_PRODUCT_CODE_HASH_DIFF`
- Startup:
  - before: `8080` listener absent, `8090` present
  - stale non-listening `run_kotomake.py` process was stopped, then `run_kotomake.py` was started on `8080`
  - during/final: `8080` listener retained by PID `8812`
- 9 attempts:
  - `announcement`: attempt 1 `publishable_success / OK`, attempt 2 `ui_harness_failure`, attempt 3 `publishable_success / OK`
  - `comparative_review`: attempt 1 `ui_harness_failure`, attempt 2 `publishable_success / OK`, attempt 3 `publishable_success / OK`
  - `company_introduction`: attempt 1 `publishable_success / OK`, attempt 2 `input_required_block / SYS_QUALITY_WARNINGS_UNRESOLVED / blocked_output_redacted=true`, attempt 3 `input_required_block / SYS_QUALITY_WARNINGS_UNRESOLVED / blocked_output_redacted=true`
- Runtime blocker check:
  - deleted client / deleted slot traceback: not observed in the current rerun window
  - `Accept failed`: not observed in the current rerun window
  - `ERR_CONNECTION_REFUSED`: not observed
  - generic asyncio Proactor connection-reset tracebacks were observed during client close; listener stayed up
- Image:
  - harness `image_check_count=0` because the designated image attempts did not align with successful waited image collection
  - image auto logs/files show representative success for `announcement`, `comparative_review`, and company-introduction route surfaced as `branding`; both `with_text` and `without_text` files exist for each representative log
  - image failure blocking article success: not observed
- Copy / legal representative checks:
  - not completed because `blocked_output_redacted=true` stop condition was observed before supplemental UI operations
- Negative checks:
  - internal-term leakage count: `0`
  - source-outside claim observed count: `0`
  - startup `ImportError` / `ModuleNotFoundError`: not observed
- Decision:
  - UI lifecycle boundary appears to remove the deleted client / deleted slot traceback and listener loss from this rerun shape
  - user trial remains blocked because `company_introduction` produced `blocked_output_redacted=true` in 2/3 attempts and copy/legal representative checks were not completed

## Phase 01 Implementation

- Owner: `C:\tetie\notecode\note\note_writer_app.py`
- Test owner: `C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py`
- Narrow hypothesis: NiceGUI client/page detach 後も `run_generation()` / image auto progress / phase UI update / cleanup / `ui.notify` が stale element / slot を更新して deleted client / deleted slot traceback を発生させる。
- Lifecycle boundary added:
  - active client registry: `_CLIENT_ACTIVE_KEYS`
  - current generation token registry: `_CLIENT_GENERATION_TOKENS`
  - mount boundary: `main_page()` mount で `_activate_client_scope(client_key)` し、stale generation token を clear
  - disconnect boundary: `_release_client_scope(client_key)` で timers deactivate、active client release、generation token invalidation、client-local state/helper/pipeline release
  - mutation boundary: `_run_attached_ui_mutation(...)` が active client + matching generation token を確認し、不一致なら UI setter / refresh / notify を実行しない
  - known NiceGUI detach race: deleted client / deleted slot の `RuntimeError` だけを detached UI race として扱い、client scope を release して return。unrelated exception は propagate
- Guarded UI paths:
  - `_set_generation_phase_ui`
  - live generation progress timer
  - image elapsed timer
  - image progress update
  - generation notify path
  - run_generation prerun / validation feedback / fetch-failure UI / render output / legal postcheck UI / image start-cleanup UI / completion UI / exception UI / final cleanup UI
- Preserved behavior:
  - generation execution remains unchanged
  - prompt / persona / source contract / algorithm / guard / pipeline / image prompt / `blog_image_auto.py` unchanged
  - article snapshot persistence and audit/event logging remain outside the UI mutation boundary
  - image auto generation remains fail-open for article success

## Phase 01 Checks

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\note_writer_app.py`
  - passed
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py C:\tetie\notecode\note\tests\test_note_writer_app_post_success_helpers.py C:\tetie\notecode\note\tests\test_note_writer_app_snapshot_helpers.py C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py C:\tetie\notecode\note\tests\test_current_mainline_ui_generation_state_adapter.py -q`
  - `120 passed in 4.45s`

## Phase 01 Targeted Test Coverage

- UI mutation callback is not called after `_release_client_scope(client_key)`.
- Stale generation token cannot mutate a remounted/current client scope.
- Known deleted client / deleted slot `RuntimeError` is treated as a detached UI race.
- Unrelated `RuntimeError` still propagates.

## Remaining Validation Recommendation

- User trial remains blocked until a narrow UI runtime validation reruns the previous failure shape against 8080.
- Recommended next check: start the UI intentionally in a new validation window, run a minimal detach/remount generation operation or the smallest representative pre-user-trial UI runtime validation, and confirm no deleted client / deleted slot traceback and no listener loss.
- Do not run full-flow validation until this narrow runtime check passes.

## Failure Timeline

- Before validation, `listener_before.json` showed `127.0.0.1:8080` owned by PID `19496`, command `python.exe run_kotomake.py`. `8090` was also present.
- `announcement` attempt 1 and 2 ended as `ui_harness_failure`. The harness waited for `誰の立場で書くか`, while captured UI text was around `STEP3 読者`, indicating selector / state drift.
- `announcement` attempt 3 reached `publishable_success / OK`, but operation collection timed out while the UI showed image generation progress. `app.log` around `20:58:19` contains deleted-client traceback during image progress update.
- `comparative_review` attempt 1 reached `publishable_success / OK` with successful `with_text` and `without_text` image files.
- `comparative_review` attempt 2 ended as harness timeout waiting for `この内容で生成`. `app.log` around `21:00:50` shows generation core completed and then deleted-client / deleted-slot traceback in `_set_generation_phase_ui`, exception handling, cleanup, and `ui.notify`.
- `comparative_review` attempt 3 reached `input_required_block` with `SYS_QUALITY_WARNINGS_UNRESOLVED` and `blocked_output_redacted=true`. This is a stop condition but not the first runtime blocker.
- After that, `gen-897d9ed2` also hit deleted-client / deleted-slot traceback around `21:02:43`.
- At `21:03:16`, `app.log` shows `Accept failed on a socket ... laddr=('127.0.0.1', 8080)`.
- Final listener snapshots show no active `8080` listener. `company_introduction` attempts 2 and 3 failed with `ERR_CONNECTION_REFUSED`.
- Product code hash diff was `NO_PRODUCT_CODE_HASH_DIFF`.

## Classification

| Category | Classification | Notes |
|---|---|---|
| product runtime crash | possible consequence | 8080 listener loss is real, but artifact does not prove external stop vs runtime degradation |
| NiceGUI client lifecycle / deleted slot update | primary blocker | repeated tracebacks in generation/image/cleanup paths |
| background task updating detached UI | primary root-cause candidate | tracebacks occur after client/page lifecycle appears detached |
| harness timeout / selector drift | secondary contributor | explains some operation failures, not listener loss by itself |
| server process externally stopped | not proven | no direct evidence in artifacts |
| generation runtime block | secondary | only `comparative_review` attempt 3 blocked output |
| classification / output guard issue | observed, not first blocker | keep for later after UI runtime is stable |
| source/input insufficiency | not first blocker | `company_introduction` could not be validated because UI/server failed |

## Ranked Root Cause Candidates

1. `note_writer_app.py` async UI mutation after NiceGUI client / slot deletion.
2. Missing or insufficient client-alive / generation-token boundary around `run_generation()` completion, image progress, cleanup, and notification paths.
3. Selenium harness selector/state drift causing repeated navigation and stale pages, which may trigger detach while server work continues.
4. Thin comparative source causing `blocked_output_redacted=true` on one attempt.

## Not Root Cause For First Blocker

- Startup `ImportError` / `ModuleNotFoundError`: not observed in captured excerpts.
- Product code drift: hash diff was `NO_PRODUCT_CODE_HASH_DIFF`.
- GPT Image 2 generation itself: comparative attempt 1 image variants succeeded and image failure did not affect article generation.
- `company_introduction` content quality: not evaluated because all attempts failed at UI operation / connection level.
- User-trial source insufficiency: not actionable before UI runtime stability.
- Persona / algorithm tuning: out of scope and not supported by the blocker evidence.

## First Blocker Decision

Proceed next with:

- owner: `C:\tetie\notecode\note\note_writer_app.py`
- hypothesis: stale NiceGUI client / slot mutation from async generation/image/legal/cleanup paths

Do not proceed with:

- generation-quality tuning
- persona/source contract adjustment
- output guard / quality guard threshold change
- timeout / sleep adjustment
- harness-only fix as the first product owner

## AGENTS Update

Not needed. Existing `AGENTS.md` already routes `note_writer_app.py`, GPT Image 2, and current mainline rules.
