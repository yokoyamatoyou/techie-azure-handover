# current mainline tomorrow plan (2026-03-13)

## scope
- primary target: `comparative_review` long の本文品質残課題
- current mainline を正本とし、`strict live short -> promoted long` を維持したまま `comparative_axis_shift_count` と本文の軸ぶれを下げる
- owner は引き続き body owner に限定する

## current state
- `semantic_dedupe` の tail blanking true owner fix は完了
- `case_study long` の末尾節欠落は解消済み
- `comparative_review long` の closing 節欠落も解消済み
- strict runtime policy は維持中
  - `gpt-5.4`
  - `allow_model_fallback = false`
- strict live short は `7/7 pass`
- strict live promoted long も `7/7 pass`
- 残課題は `comparative_review long` の本文品質
  - latest long: `comparative_axis_shift_count=22`
  - absolute winner claim は `0`
  - 末尾節は復帰済み

## what is already fixed
- `output_formatter / prompt_echo_detector / output_guard` 境界の prompt echo 問題
- `natural_blog_core / section_generator` の local-first anchor と bridge summary
- `semantic_dedupe` の truncation tail blanking

## tomorrow objective
- `comparative_review` の `criteria -> comparison -> fit -> caution -> closing` の軸 continuity を本文品質ベースで改善する
- metrics のみを追わず、artifact 本文の自然さと用途別の切り分けを優先する
- observe-only owner へは広げない

## files to inspect first
- `C:\tetie\AGENTS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\notecode\note\natural_blog_core.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`
- `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_latest.json`
- `C:\tetie\notecode\logs\current_mainline_ui_long_matrix_latest.json`
- `C:\tetie\notecode\logs\current_mainline_ui_runs\20260312-202908-short\ui-short-comparative-review.txt` if present
- `C:\tetie\notecode\logs\current_mainline_ui_runs\20260312-222043-long\ui-short-comparative-review-promoted-long.txt`

## working assumptions
- true owner of the remaining issue is not `semantic_dedupe`
- mainline runtime is healthy
- `comparative_axis_shift_count` may overcount in parts, but tomorrow's slice stays owner-only unless本文が十分に良いのに metric だけが残ると確認できた場合

## execution plan
1. artifact と latest metrics を再確認し、どの節で軸が飛ぶかを本文でマークする
2. `natural_blog_core` の comparative contract と `discourse_planner / section_generator` の carry-over を確認し、どこで criteria から用途別へ自然に遷移できていないかを切る
3. minimal fix を `natural_blog_core / discourse_planner / section_generator` に限定して実装する
4. targeted regression を追加する
5. fixed test を回す
6. strict live short -> promoted long を再実行する
7. artifact を人手確認し、本文品質と metric の差分をまとめる

## success criteria
- `comparative_review long` の各節が同じ評価軸の上でつながる
- `closing` が急に一般論へ逃げない
- `comparative_axis_shift_count` が現状より下がる、または本文は改善して metric だけが残ることを明示できる
- strict live short / promoted long の `7/7 pass` を維持する
- prompt echo / runtime blocker / tail blanking を再発させない

## stop conditions
- 本文が十分改善し、残るのが watch metric だけなら owner-only で停止する
- owner が observe-only 側に移る証拠が新たに出ない限り、slice を広げない

## notes
- `case_study` は今回の primary target ではない
- `semantic_dedupe` は regression watch のみ
