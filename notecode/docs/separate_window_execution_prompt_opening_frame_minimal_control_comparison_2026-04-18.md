# separate window execution prompt opening frame minimal control comparison 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\TASK.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\ROLLBACK.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\compass_artifact_wf-d9cf85b5-5c9c-4b24-b87e-d34499c64d36_text_markdown.md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\deep-research-report (31).md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\新規 テキスト ドキュメント.txt

今回の依頼種別:
- docs-only comparison prompt
- `OPENING_FRAME_MINIMAL_CONTROL_COMPARISON`
- implementation prompt ではない
- current package reopen prompt ではない

今回の実施範囲:
- `opening_frame_redesign_2026-04-18` package の Phase 01 として、
  minimal control placement の 3 案を docs-only で比較する
- code diff は作らない
- production code / tests / AGENTS / WORKLOG / current package docs は編集しない
- `naturalness_recovery_2026-04-07` package は parked / not fixed のまま維持する

current fixed judgment:
- current redesign package:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`
- current parked package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- current parked boundary:
  - `prompt_builder.py` simplification-first wording line の unchanged retry 禁止
  - `pipeline.py` current-first source ordering / hint triage の unchanged retry 禁止
  - `pipeline.py` core_message current-first hint の unchanged retry 禁止
- first code owner:
  - `not fixed`
- first code step:
  - `not started`

comparison target:
1. `PROMPT_BUILDER_FRAME_CARD`
   - `title / lead / first heading / first section` の役割分離を
     `prompt_builder.py` 側の最小 frame card / variable block に寄せる案
2. `PIPELINE_OPENING_FRAME_CONTROL_SURFACE`
   - opener ownership / current-business-first invariant を
     `newalgorithm_pipeline/pipeline.py` 周辺の最小 control surface に寄せる案
3. `TINY_DETERMINISTIC_GUARD`
   - opener invariant を tiny deterministic guard / detector として持つ案

core question:
- `opening frame ownership / role separation / current-business-first invariant`
  を最も少ない accidental complexity で保てる最小 control placement はどれか

what to compare:
1. inherited do-not-retry と衝突しないか
2. prompt accretion continuation に見えないか
3. current package reopen の rename retry に見えないか
4. `title / lead / first heading / first section` の role separation を自然に持てるか
5. `current-business-first` invariant を prose rule ではなく安定して持てるか
6. future `1 owner / 1 hypothesis` に narrow に落とせるか
7. rollback-first で扱いやすいか
8. hidden reviser accumulation や giant rewrite へ滑りにくいか

required output shape:
- docs-only comparison note 1 本
- conclusion は exactly one:
  - `PROMPT_BUILDER_FRAME_CARD`
  - `PIPELINE_OPENING_FRAME_CONTROL_SURFACE`
  - `TINY_DETERMINISTIC_GUARD`
  - `NOT_FIXED_YET`
- if not `NOT_FIXED_YET`:
  - why this one wins
  - why the other two lose now
  - future legal `1 owner / 1 hypothesis`
  - exact first prompt type
    - `triage prompt`
    - not implementation prompt

strong bias:
- 3案を同時採用しない
- code 実装へ進まない
- `pipeline.py` を自動的に winner にしない
- `prompt_builder.py` を自動的に winner にしない
- tiny guard を easy answer として雑に採用しない
- multiple owner solution にしない
- prompt accretion continuation に戻らない
- fixed routing table に戻らない
- planning / skeleton default reopen に戻らない

comparison method guidance:
- local source-of-truth と research の両方を使う
- ただし research は evidence only
- winner 判定は `simplicity / retry collision / rollback clarity / role separation fit / invariant stability`
  を優先する
- broad capability や理論的 elegance より、
  current repo の stop boundary と矛盾しないことを優先する

recommended output file:
- C:\tetie\notecode\docs\opening_frame_minimal_control_comparison_note_2026-04-18.md

optional next prompt:
- winner が 1 本に絞れた場合だけ、
  docs-only triage prompt を 1 本だけ作ってよい
- triage prompt は implementation prompt ではない
- recommended path:
  - C:\tetie\notecode\docs\separate_window_execution_prompt_opening_frame_<winner>_triage_2026-04-18.md

what not to do:
- production code edit
- test edit
- live validation
- current package docs update
- current redesign package source-of-truth broad rewrite
- implementation plan の詳細化
- 複数 winner の併記

stop conditions:
- 3案を 1 winner か `NOT_FIXED_YET` に絞れない
- current package reopen と実質同じ話に戻る
- first code owner を早く fixed したくなった
- implementation を始めたくなった

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. 比較した 3 案
4. 比較軸
5. conclusion
6. winner か `NOT_FIXED_YET` の理由
7. next prompt を作ったかどうか
8. WEB検索を使ったかどうか
9. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
