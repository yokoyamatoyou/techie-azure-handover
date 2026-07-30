# opening_frame_redesign_2026-04-18 EXECUTION PROMPT

## next startup use

- 次回起動時の canonical prompt path は次を使う
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md`
- current planning source-of-truth は `opening_frame_redesign_2026-04-18` package に固定する
- current parked boundary は `naturalness_recovery_2026-04-07` package に固定する
- current package `naturalness_recovery_2026-04-07` は parked / not fixed のまま維持する
- first code owner は `not fixed`
- first code step は `not started`
- next step は `docs-first design triage`
- `minimal_control_layer` は first design question であり package theme ではない
- research synthesis note と research 3 本は evidence only として読む
- `prompt_builder.py` simplification-first wording line / `pipeline.py` current-first triage / `pipeline.py` core_message current-first hint は unchanged retry しない
- production code / tests / AGENTS / WORKLOG / current package docs はこの prompt では編集しない
- tentative future code candidate が必要な場合だけ、`newalgorithm_pipeline/pipeline.py` 周辺の最小 opening-frame control surface に触れてよい

## prompt

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
- C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- docs-first design-triage follow-up
- `OPENING_FRAME_REDESIGN_DOCS_FIRST_CONTINUE`
- implementation prompt ではない
- current package reopen prompt ではない

今回の実施範囲:
- `opening_frame_redesign_2026-04-18` package の docs-first triage を続ける
- `naturalness_recovery_2026-04-07` package は parked / not fixed のまま維持する
- production code / tests / AGENTS / WORKLOG / current package docs は編集しない

current fixed judgment:
- current package:
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07
- current package state:
  - parked / not fixed
- current decision:
  - opening frame redesign is a separate redesign line
- first code owner:
  - not fixed
- first code step:
  - not started
- next step:
  - docs-first design triage

this window will do:
1. `opening frame ownership / role separation / current-business-first invariant` の docs-first boundary を保つ
2. `prompt_builder` frame card / `pipeline.py` opening-frame control surface / tiny deterministic guard を code なしで比較する
3. legal な `1 owner / 1 hypothesis` candidate があるかだけを判断する

this window will not do:
- production code edit
- test edit
- current package reopen
- `prompt_builder.py` unchanged retry
- `pipeline.py` unchanged retry
- prompt accretion continuation
- fixed routing table
- planning / skeleton default reopen
- giant rewrite

stop conditions:
- current package reopen と実質同じ内容に戻る
- first code owner を early fix したくなる
- `minimal_control_layer` implementation を先に固定したくなる
- multiple owner implementation planning が必要になる

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. docs-first triage で固定した判断
4. legal な next owner candidate があるかどうか
5. first code owner をまだ fixed していないこと
6. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
7. WEB検索を使ったかどうか
```
