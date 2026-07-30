# current_mainline_fingerprint_guard_remaining_2026-04-25 TASK

## Global Rules

- Case 1 と Case 4 を別々に分類する。
- `1 phase = 1 narrow hypothesis = 1 owner scope`。
- threshold 緩和、repair 回数増加、prompt accretion、target length tuning をしない。
- source grounding weak reflection が混じる場合は fingerprint fix と混ぜず、別 follow-up に回す。
- 同じ error が 3 回続いたら停止して report する。

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | read / package / baseline | plan package | no | required docs/logs read and baseline recorded |
| 1 | runner-equivalent final guard triage | logs / guard connection | no initially | backend artifacts are rechecked through same final guard policy |
| 2 | visible quality review | logs | no | Case 1 / Case 4 body and candidate quality classified |
| 3 | root cause classification | PROGRESS | no | true quality / false-positive / connection issue split |
| 4 | narrow fix A | one owner | conditional | one connection or runtime hypothesis fixed |
| 5 | narrow fix B | one owner, only if needed | conditional | independent residual only |
| 6 | owner-local regression | tests | no additional | local regression green |
| 7 | backend rerun | logs | validation | exact UI input_contract rerun saved |
| 8 | actual UI operation validation | UI logs | validation | Case 1 / Case 4 actual UI results saved |
| 9 | shared regression / closeout | PROGRESS / ROLLBACK / WORKLOG | no additional | final state recorded |

## Required Triage Fields

- runtime reason code
- output guard reasons / hard reasons / soft warnings
- repair required / applied / rejected / rejection reason
- fingerprint before / after / final flags
- repair candidate summary
- final draft summary
- final body chars and section headings
- source contract validation
- source grounding weak reflection
- candidate vs final draft fingerprint and identity
- final guard strict mode and whether guard was recomputed or reused

## Classification Candidates

- `true_flat_output`
- `fingerprint_false_positive`
- `repair_candidate_not_reflected`
- `final_guard_reads_original`
- `fingerprint_metadata_stale`
- `acceptance_rejects_improved_candidate`
- `final_guard_policy_matches_ui`
- `stale_non_strict_output_guard_reused`
- `source_reflection_mixed_issue`
- `unknown`

## Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
```

If code changes:

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -q -k "output_guard or soft_warnings or fingerprint"
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "fingerprint or repair or company_intro or case_study"
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
```

## Log Targets

- `C:\tetie\notecode\logs\current_mainline_fingerprint_guard_remaining_YYYYMMDD-HHMMSS\`
- UI validation:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_guard_remaining_YYYYMMDD-HHMMSS\ui\`

## Stop Boundary

- Same UI `fingerprint_guard_remaining` repeats 3 times after runner-equivalent final guard fix.
- Required fix crosses multiple product owners.
- Fix requires quality/fingerprint threshold relaxation or repair count increase.
- Candidate and final body are both visibly flat/bad.
- Fix requires source-outside claims, generic padding, or visible internal terms.
