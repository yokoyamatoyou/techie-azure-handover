# opening frame minimal control comparison note 2026-04-18

## 参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\TASK.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\ROLLBACK.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md`
- `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\compass_artifact_wf-d9cf85b5-5c9c-4b24-b87e-d34499c64d36_text_markdown.md`
- `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\deep-research-report (31).md`
- `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\新規 テキスト ドキュメント.txt`

## 今回の実施範囲

- `opening_frame_redesign_2026-04-18` package の Phase 01 として、minimal control placement の 3 案を docs-only で比較した。
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない前提で判断した。
- local source-of-truth と local research を使い、winner を 1 本に絞るか `NOT_FIXED_YET` に止めるかを判定した。

## 比較した 3 案

1. `PROMPT_BUILDER_FRAME_CARD`
2. `PIPELINE_OPENING_FRAME_CONTROL_SURFACE`
3. `TINY_DETERMINISTIC_GUARD`

## 比較軸

1. inherited do-not-retry と衝突しないか
2. prompt accretion continuation に見えないか
3. current package reopen の rename retry に見えないか
4. `title / lead / first heading / first section` の role separation を自然に持てるか
5. `current-business-first` invariant を prose rule ではなく安定して持てるか
6. future `1 owner / 1 hypothesis` に narrow に落とせるか
7. rollback-first で扱いやすいか
8. hidden reviser accumulation や giant rewrite へ滑りにくいか

## local structure read

- `prompt_builder.py` には company introduction 向けの opening 指示が既に厚く入り、`_preflight_company_intro_generation_blocks()` で `title・lead・最初の見出し・1節目本文` を直接そろえる line が入っている。
- `simple_note_pipeline/pipeline.py` には downstream 側の opener drift 判定と local patch acceptance が既にあり、tiny guard / acceptance を先に勝ち筋へ上げると current parked boundary の `guard first` と衝突しやすい。
- `newalgorithm_pipeline/pipeline.py` には upstream orchestration と company introduction 向け source handling の hook があり、opening frame を prompt wording ではなく handoff state として持つ余地がある。
- ただし `pipeline.py` の過去 retry は `current-first source ordering / hint triage` と `core_message current-first hint` であり、この note の winner はそれらの unchanged retry を意味しない。

## comparison summary

| candidate | wins | loses now | verdict |
|---|---|---|---|
| `PROMPT_BUILDER_FRAME_CARD` | visible writer に近く、role separation の表現はしやすい | inherited do-not-retry に最も近い。既存の company-intro opening 指示面へ戻るため、rename retry と prompt accretion continuation に見えやすい | lose |
| `PIPELINE_OPENING_FRAME_CONTROL_SURFACE` | opener ownership を upstream handoff として 1 回だけ決められる。prompt wording と invariant を分離しやすい。`1 owner / 1 hypothesis` に落としやすい | 過去の `pipeline.py` retry と混線しやすいが、`source ordering / hint retry` と切り分ければ legal line を作れる | win |
| `TINY_DETERMINISTIC_GUARD` | invariant の fail-closed だけなら最小 | owner ではなく detector に留まり、`title / lead / first heading / first section` の role separation を持てない。guard first / detect-only 再開に寄りやすい | lose |

## conclusion

`PIPELINE_OPENING_FRAME_CONTROL_SURFACE`

## why this one wins

- current parked boundary が止めたのは `prompt_builder.py` wording simplification と `pipeline.py` source ordering / hint triage の retry line であり、残っている design question は `opening frame ownership` そのものだった。
- `prompt_builder.py` には company-intro opening 指示が既に集積しているため、frame card をそこへ置くと「整理」の名目でも surface rule 面へ戻りやすい。
- `TINY_DETERMINISTIC_GUARD` は fail 判定には使えても、冒頭 4 要素の役割分離を正に持つ owner にはならない。
- `newalgorithm_pipeline/pipeline.py` 周辺なら、`title / lead / first heading / first section` が従う最小 handoff state を 1 回だけ決め、downstream はそれを render するだけに寄せられる。
- これは `prompt accretion continuation` でも `planning / skeleton default reopen` でもなく、`opening frame ownership` を 1 箇所へ寄せる minimal control placement として説明しやすい。

## why the other two lose now

### `PROMPT_BUILDER_FRAME_CARD`

- inherited do-not-retry と最も衝突する。
- current package reopen の rename retry に見えやすい。
- 既存の company-intro opening rule 密度を前提にすると、new card より「新しい prompt 文面の置き方」に議論が戻りやすい。
- invariant を prose rule に寄せる面が強く、`current-business-first` を安定した owner state にしにくい。

### `TINY_DETERMINISTIC_GUARD`

- detect はできても owner にはならない。
- `title / lead / first heading / first section` の role separation を guard だけでは設計できない。
- current parked boundary の `quality_guard.py first` / `repair acceptance reopen first` を別名で再開する形に見えやすい。
- hidden reviser accumulation や post-hoc patch path へ滑る入口になりやすい。

## future legal `1 owner / 1 hypothesis`

- owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- hypothesis:
  - `opening frame control surface` を upstream handoff state として 1 箇所に持てば、`current-business-first` invariant と `title / lead / first heading / first section` の role separation を、`source ordering / hint retry` や `prompt_builder` wording retry に戻らず narrow に保持できる
- explicit non-goals:
  - `prompt_builder.py` simplification-first retry を再開しない
  - `pipeline.py` current-first source ordering / hint triage を再開しない
  - `pipeline.py` core_message current-first hint を再開しない
  - `TINY_DETERMINISTIC_GUARD` を first owner にしない
  - planning / skeleton default reopen に戻さない

## exact first prompt type

- `triage prompt`
- implementation prompt ではない

## next prompt

- created:
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_opening_frame_pipeline_opening_frame_control_surface_triage_2026-04-18.md`
- purpose:
  - `PIPELINE_OPENING_FRAME_CONTROL_SURFACE` を `newalgorithm_pipeline/pipeline.py` owner 1 file の legal な next hypothesis へ narrow に落とせるかを docs-only で確認する

## WEB検索を使ったかどうか

- not used
- local source-of-truth / local research / local code surface の読取りだけを使った

## non-updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- `naturalness_recovery_2026-04-07` package docs は更新していない
- `opening_frame_redesign_2026-04-18` package docs も更新していない
