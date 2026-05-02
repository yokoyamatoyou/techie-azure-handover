# current mainline tomorrow first prompt

更新日: 2026-03-29  
用途: 2026-03-30 の初回セッションでそのまま貼る prompt

## 目次
- prompt
- 補足メモ

## prompt

```text
参照ルールファイル:
  - C:\tetie\AGENTS.md
  - C:\tetie\notecode\AGENTS.md

今回の実施範囲:
  - 2026-03-30 の初回起動として、current mainline quality residual と hierarchical generation 候補の次アクション整理を行う
  - external review の結論 `限定A/Bで試すべき` を前提に、announcement dense must_cover route の最小 A/B slice を確定する
  - completed 済みの simple_note_refactor_2026-03-22 plan package は completed のまま扱い、reopen しない
  - prompt accretion / module accretion を避ける

実行モード:
  - PLAN mode
  - 実装は user が明示するまで始めない

開始直後に必ず確認するファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\docs\current_mainline_quality_status_2026-03-23.md
5. C:\tetie\notecode\docs\simple_note_refactor_status_2026-03-23.md
6. C:\tetie\WORKLOG.md
7. C:\tetie\notecode_current_mainline_handoff_2026-03-29.md
8. C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-03-30.md
9. C:\tetie\notecode\docs\hierarchical_ab_slice_plan_announcement_2026-03-30.md
9. latest live artifacts
   - C:\tetie\notecode\logs\codex_grammar_round4.json
   - C:\tetie\notecode\logs\codex_grammar_round5.json
   - C:\tetie\notecode\logs\codex_grammar_round6.json
   - C:\tetie\notecode\logs\current_mainline_ui_runs\codex-round6

開始時の最初の行動:
  - filesystem を確認し、上記 path と現物が一致するか確認する
  - current success path が C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py -> super().generate(...) -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py の single-pass owner であることを再確認する
  - C:\tetie\notecode_current_mainline_handoff_2026-03-29.md と C:\tetie\notecode\docs\hierarchical_ab_slice_plan_announcement_2026-03-30.md の前提が current code と矛盾しないか確認する
  - 実装に入らず、まず plan と success / rollback 条件を固定する

今回の本命:
  - `ui-short-announcement-dense-must-cover` の limited A/B slice を file-level plan へ落とすこと

今回の目的:
  - current residual が grammar ではなく contract reflection / semantic progression に移っていることを再確認する
  - announcement dense must_cover route の最小 A/B slice を定義する
  - ledger 最小仕様を定義する
  - success / rollback 条件を定義する

固定ルール:
  - prompt を長くして解決しようとしない
  - module を増やして正しさを見せかけない
  - 現行の final pass 群は流用前提で考える
  - UI 変更を先にやらない
  - 初手は announcement 1 route 限定で始める

やってはいけないこと:
  - prompt accretion
  - module accretion
  - simple_note_refactor_2026-03-22 を reopen すること
  - external review 結果未確認のまま全面移行を宣言すること
  - 実装に先走ること

最初に見るべき case:
  - ui-short-announcement-dense-must-cover
  - ui-short-explanatory-default
  - ui-short-branding-company-grounded

想定する進め方:
  - まず current code path と latest live artifact を読み、問題が grammar から shifted しているか確認する
  - その後、announcement dense must_cover route に絞って A/B slice を定義する
  - `remaining_must_cover_before/after` ledger の shape を確定する
  - file-level implementation plan を作る
  - ここまでで user に確認を返す
  - user が go を出したら、その次の turn で実装に入る

最終報告で必ず示すこと:
  - 読んだ正本ファイル
  - current success path の file path
  - current residual の要約
  - announcement A/B slice の owner
  - success 条件
  - rollback 条件
  - AGENTS / WORKLOG 更新の有無
```

## 補足メモ

- 2026-03-29 の live では grammar / legal false positive はかなり改善した
- 残差は explanatory / branding の `must_cover_reflection_rate` と `prompt_anchor` の stochastic drift が中心
- current mainline は discourse plan / section generation の部品を持つが、success path はまだ single-pass owner
- external review の最終判定は `限定A/Bで試すべき`
- 明日の first session は「architecture を決め切る」のではなく、「announcement dense must_cover の最小 safe slice を切る」ことを目的にする
