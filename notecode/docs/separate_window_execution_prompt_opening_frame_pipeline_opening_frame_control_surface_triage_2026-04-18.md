# separate window execution prompt opening frame pipeline opening frame control surface triage 2026-04-18

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
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md
- C:\tetie\notecode\docs\opening_frame_minimal_control_comparison_note_2026-04-18.md
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\WORKLOG.md

今回の依頼種別:
- docs-only triage prompt
- `OPENING_FRAME_PIPELINE_CONTROL_SURFACE_TRIAGE`
- implementation prompt ではない
- current package reopen prompt ではない

今回の実施範囲:
- winner `PIPELINE_OPENING_FRAME_CONTROL_SURFACE` を
  `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  owner 1 file の legal な next hypothesis に落とせるか docs-only で triage する
- code diff は作らない
- production code / tests / AGENTS / WORKLOG / current package docs / redesign package docs は編集しない

current fixed judgment:
- current redesign package:
  - C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18
- current parked package:
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07
- current parked state:
  - naturalness_recovery_2026-04-07 は parked / not fixed の boundary を継承して読む
- Phase 01 comparison winner:
  - PIPELINE_OPENING_FRAME_CONTROL_SURFACE
- this winner means:
  - opener ownership / role separation / current-business-first invariant を
    upstream handoff state として最小に持つ可能性を triage する
- this winner does not mean:
  - `prompt_builder.py` simplification-first wording retry
  - `pipeline.py` current-first source ordering / hint triage retry
  - `pipeline.py` core_message current-first hint retry
  - planning / skeleton default reopen
  - tiny deterministic guard first
  - implementation start

core question:
- `newalgorithm_pipeline/pipeline.py` だけで持てる
  minimal `opening_frame_control_surface`
  は何か
- それは inherited do-not-retry と衝突せず、
  `title / lead / first heading / first section`
  の role separation と
  `current-business-first`
  invariant を narrow に handoff できるか

what to define:
1. pipeline owner が持つ state は何か
2. その state が downstream に渡す最小 field は何か
3. 何を explicit non-goal にして old retry と切り分けるか
4. first code step を still legal な `1 owner / 1 hypothesis` にできるか
5. できないならどこで stop するか

what to compare inside this triage:
1. source reorder heuristic retry との違い
2. core_message hint retry との違い
3. prompt_builder frame card first との違い
4. tiny deterministic guard first との違い
5. rollback-first clarity
6. prompt accretion continuation に見えないか

required output shape:
- docs-only triage note 1 本
- conclusion は exactly one:
  - `LEGAL_NEXT_OWNER`
  - `STOP`
- if `LEGAL_NEXT_OWNER`:
  - exact owner file
  - exact narrow hypothesis
  - max 3 control fields
  - exact non-goals
  - why this is not old retry
  - exact next prompt type
    - `implementation prompt`
    - ただしこの window 自体は implementation しない
- if `STOP`:
  - why pipeline winner でも legal な 1 owner に落ちなかったか
  - which collision blocked it

recommended output file:
- C:\tetie\notecode\docs\opening_frame_pipeline_control_surface_triage_note_2026-04-18.md

strong bias:
- source ordering branch の再命名 retry に戻らない
- core_message current-first hint の再命名 retry に戻らない
- prompt_builder wording へ先に逃がさない
- tiny guard を easy answer にしない
- multiple owner solution にしない
- implementation を始めない

stop conditions:
- source ordering retry と区別できない
- prompt_builder change が first code step に必須になる
- tiny guard が primary owner になってしまう
- multiple owner implementation planning が必要になる
- current package reopen と実質同じ話に戻る

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. winner を pipeline candidate として読んだ理由
4. `LEGAL_NEXT_OWNER` か `STOP`
5. owner / hypothesis / non-goals
6. old retry との切り分け
7. WEB検索を使ったかどうか
8. production code / tests / AGENTS / WORKLOG / current package docs / redesign package docs を更新していないこと
```
