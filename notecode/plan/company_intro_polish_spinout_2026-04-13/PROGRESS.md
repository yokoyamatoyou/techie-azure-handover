# company_intro_polish_spinout_2026-04-13 PROGRESS

## Current Goal

- blank `branding/company_introduction` で paired line が keep baseline と prompt-only floor を同時に超えられるかを判定する

## Current Status

- package status:
  - active
- current phase:
  - S3 compare and verdict
- status:
  - rollback_stop
- hypothesis:
  - blank company intro の残差は `input_contract.py` 単独でも `prompt_builder.py` 単独でもなく、current-business distilled summary と writer-facing handoff の境界で起きている
- owner scope:
  - `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - supporting tests only
- attempts used:
  - 2/3

## Baseline Snapshot

- keep baseline:
  - avg ai_index around `0.2378`
  - current-business-first first heading kept
  - company-name repetition low
- prompt-only floor:
  - avg ai_index around `0.2651`
  - repetition higher
  - must-cover / anchor weaker
- input-contract-only rollback:
  - avg ai_index around `0.3089`
  - history-led first heading drift
  - must-cover / anchor strong but naturalness worse

## Decision Boundary

- keep as separate line only if:
  - keep baseline と prompt-only floor の両方に勝つ
  - must-cover / grounding / anchor を落とさない
  - public web compare pattern に近づく
- rollback if:
  - naturalness改善が history-led drift や anchor drop と引き換えになる
- stop if:
  - paired owner set を超える必要が出る

## Next Step

- separate line verdict は `rollback / stop`
- code owner diff は rollback 済み
- artifacts と package docs だけを evidence として残す

## Execution Record

- attempt 1:
  - paired diff:
    - `input_contract.py`
      - blank company intro の `topic_statement / core_message` を current-business-first に寄せる
    - `prompt_builder.py`
      - background label を blank company intro brief に反映する
  - artifact:
    - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-234809\summary.json`
    - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-234809\comparison_to_baselines.json`
  - result:
    - first heading / company-name repetition / anchor は維持
    - avg ai_index `0.2665`
    - keep baseline `0.2378` と prompt-only floor `0.2651` の両方を超えられず
- attempt 2:
  - paired diff:
    - `input_contract.py`
      - focus/background hint を shadow handoff に追加
    - `prompt_builder.py`
      - core message verbatim 露出を減らし、focus hint 化して brief へ渡す
  - artifact:
    - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-235302\summary.json`
    - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-235302\comparison_to_baselines.json`
  - result:
    - first heading / company-name repetition / anchor は維持
    - avg ai_index `0.3089`
    - attempt 1 より悪化

## Final Decision

- best separate artifact:
  - `C:\tetie\notecode\logs\codex_company_intro_polish_spinout_20260413-20260413-234809\summary.json`
- why not keep:
  - keep baseline と prompt-only floor の両方に勝てなかった
  - current-business-first は維持できても、brochure/card feel と repeated phrasing が残った
  - paired line は repeatability / ai_index の勝ち筋を示せなかった
- package closeout:
  - separate line as code diff is rolled back
  - package docs と rerun artifacts は keep
