# separate window cycle2 fact-owned micro-skeleton 2026-04-11

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\docs\skeleton_role_revision_proposal_2026-04-11.md
- C:\tetie\notecode\docs\separate_window_initial_prompt_2026-04-11_skeleton_role_revision_5x3.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md

今回の開始前提:
- cycle 1 は reject 済み
- reject 理由:
  - visible skeleton を薄くしただけでは `company_grounded` の must_cover_reflection_rate が落ちた
  - grounding は残ったが、source-backed company intro の回収力が落ちた
  - したがって `visible skeleton reduction first` は順番が早すぎた
- rollback 済みで、現在は accepted baseline に戻っている

今回の research conclusion:
- 研究で有効だった骨格は `content planning / source alignment / ordering` の骨格であり、visible prose template の骨格ではない
- 次に試すべきは `role-hidden 化の継続` ではなく `fact-owned micro-skeleton`
- 順番は
  - 1. hidden plan の fact ownership を強める
  - 2. source が薄い role を standalone section にしない
  - 3. その後に visible skeleton を薄くする

今回の mission:
- cycle 2 は `fact-owned micro-skeleton` を narrow に試す
- visible structure lines や writer の prose 自由度にはまだ大きく触れない
- `coverage-preserving hidden plan` を先に作る
- `no source, no standalone section` を hidden plan 側で実装する

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

accepted baseline compare:
- C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json

fixed3:
- ui-short-branding-trust
- ui-short-case-study-explain
- ui-short-branding-company-grounded

固定比較モード:
- generic
- algorithm
- prompt_only

今回の narrow hypothesis:
- planner / support で section candidate ごとに `fact ownership` を持たせると、visible skeleton をまだ保ったままでも、空節を減らし、must_cover を落とさずに section role overlap を減らせる

owner scope:
- 第一候補:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- 必要なら最小限:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- do not touch:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - C:\tetie\notecode\note\natural_blog_core.py
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py

今回の実装方針:
- writer 向け visible structure は今は維持する
- 触るのは hidden planning only
- support/planner handoff に次の概念を足す
  - `exclusive_fact_ids`
  - `merge_allowed_with`
  - 可能なら `fact_count`
  - 可能なら `section_mandatory=false` の概念
- section candidate は次の条件を満たさないと standalone にしない
  - exclusive fact を 1 つ以上持つ
  - または reader question / must_cover を単独で受け持つ

merge rule の初期案:
- result -> condition or closing
- strength -> operation or closing
- background -> reason or closing
- role が source 的に薄い場合は merge を優先する

非交渉ルール:
- `no source, no standalone section`
- `section exists only if it owns at least one exclusive fact or question`
- `merge allowed, invention forbidden`
- `self_reference_policy belongs to realization, not planning`
- `visible skeleton reduction is out of scope for this cycle`

今回やってよいこと:
- support JSON の項目追加
- planner prompt の hidden constraint 追加
- standalone section の生成条件追加
- merge rule の限定追加
- 関連テスト更新

今回やってはいけないこと:
- writer prompt の visible skeleton をさらに薄くする
- heading progression の visible wording を大きく変える
- section opening rule を緩める
- prompt-only persona を algorithm 側へ大きく移植する
- broad refactor
- prompt accretion
- module accretion

実装イメージ:
- support output shape の例:

{
  "reader": "...",
  "core_message": "...",
  "section_briefs": [
    {
      "heading": "...",
      "section_focus": "...",
      "fact_anchor": "...",
      "exclusive_fact_ids": ["fact1"],
      "why_it_matters": "...",
      "do_not_mix": "...",
      "merge_allowed_with": ["closing"]
    }
  ],
  "writing_cautions": ["..."]
}

- planner rule の例:
  - exclusive_fact_ids が空の section は standalone section にしない
  - merge_allowed_with に従って前後 section へ統合してよい
  - must_cover の回収は本文全体で達成し、source が薄い role のために空の節を作らない

開始時に確認するコード:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - support/script prompt
  - planner prompt
  - section_briefs output schema
  - heading progress rule
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - support/planner handoff
  - planner result consumption
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - support/planner prompt assertions
  - company intro / case study prompt tests

必ず実施する手順:
1. accepted baseline と cycle 1 reject 内容を確認する
2. owner-local で narrow diff を入れる
3. owner-local tests
4. shared checks
5. fixed3 live compare
6. keep / rollback / simplify を判定する

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q

live compare command:
- C:\tetie\notecode\.venv\Scripts\python.exe tools\run_minimum_hybrid_compare_matrix.py --live --case-set fixed3 --label cycle2-fact-owned-micro-skeleton

採否ルール:
- keep 条件:
  - target case で prompt_only と同等以上、または groundedness と business-ready の優位を説明できる
  - company_grounded で must_cover_reflection_rate を落とさない
  - source_trace_coverage を落とさない
  - non-target regression がない
- reject 条件:
  - company_grounded の must_cover が baseline より低下
  - source の薄い空節が残る
  - prompt_only / generic より visible quality が落ちる
  - non-target regression
- reject なら rollback する

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 読んだ research conclusion
- touched owner
- hypothesis
- diff
- tests
- live compare result
- `generic / algorithm / prompt_only` の勝敗
- must_cover_reflection_rate と source_trace_coverage の変化
- keep / rollback / simplify の判定
- 次に `visible skeleton reduction` へ進める条件
- AGENTS / WORKLOG 更新の有無
```
