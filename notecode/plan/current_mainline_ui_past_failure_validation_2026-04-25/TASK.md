# current_mainline_ui_past_failure_validation_2026-04-25 TASK

## Global Rules

- `1 phase = 1 narrow hypothesis = 1 owner scope`.
- UI route validation is the primary objective.
- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Runtime algorithm boundaries stay unchanged unless a current keep-state regression is proven.
- Same error may be retried up to `3` times in one phase. Stop after the third same error and report phase, operation, error excerpt, attempted fixes, blocked responsibility, rollback candidate, and residual risk.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | read / package / baseline | plan package only | no | required docs/logs read, package created, baseline tests recorded |
| 1 | UI startup method | inspection / `PROGRESS.md` | no | startup command and URL recorded |
| 2 | UI startup | UI process / browser artifact | no | UI loads and screenshot/log path recorded |
| 3 | UI validation | timestamped logs | behavior validation | Case 1-4 run records saved |
| 4 | quality review | logs / visible outputs | no | leakage, source-outside claim, thinness, UI issue classification recorded |
| 5 | fix decision | UI owner only if needed | optional | no fix or narrow fix with evidence |
| 6 | regression | tests | no additional behavior change | required UI matrix and any extra tests pass |
| 7 | closeout | `PROGRESS.md`, `ROLLBACK.md`, optional `WORKLOG.md` | no additional behavior change | final verdict recorded |

## Phase 0 Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
```

## UI Startup

- Primary command:

```text
$env:HEADLESS='1'; $env:PORT='18080'; C:\tetie\notecode\.venv\Scripts\python.exe -m note.note_writer_app
```

- Expected URL:

```text
http://127.0.0.1:18080/
```

- If the port is occupied, use the next free port and record the actual URL in `PROGRESS.md`.

## Run Record Schema

Each UI run must record:

- run id
- UI route / selected controls
- article_type
- semantic_article_key
- source_mode
- source inputs
- runtime_reason_code
- success / fail-closed / input-boundary
- UI visible result
- repair_required
- repair_applied
- repair_rejected
- repair reject reason
- output_guard reasons
- soft_warning_count
- body_chars
- body/target if available
- source slot coverage if available
- visible internal-term leakage yes/no
- source outside claim suspicion yes/no
- Codex visible evaluation
- UI issue
- next action

## Fix Boundaries

Allowed UI fixes only if isolated:

- UI input mapping
- source mode / semantic key handoff
- generation error display
- stale result / result rendering
- latest snapshot/log persistence

Forbidden fixes:

- target length changes
- repair count changes
- repair acceptance changes
- quality threshold relaxation
- prompt accretion
- additional source packet broadening

## Regression

- No-fix minimum:

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
```

- If code changes are made:

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
```

## Success Criteria

- UI starts and accepts inputs.
- Case 1 and Case 4 do not regress through UI.
- Case 2 and Case 3 do not become false-positive success.
- latest UI output/log snapshots are updated and not stale.
- visible body has no runtime/internal term leakage.
- source-outside claim suspicion is recorded as a problem even when runtime returns success.
