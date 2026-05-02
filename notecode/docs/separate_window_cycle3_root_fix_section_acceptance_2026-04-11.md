# separate window cycle3 root fix section acceptance 2026-04-11

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
- C:\tetie\notecode\docs\separate_window_cycle2_fact_owned_micro_skeleton_2026-04-11.md
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
- cycle 1 reject:
  - visible skeleton reduction first は coverage を落とした
- cycle 2 reject:
  - hidden schema に `exclusive_fact_ids / merge_allowed_with / section_mandatory` を足しただけでは output がほぼ変わらなかった
- rollback 済みで、現在は accepted baseline に戻っている
- accepted compare baseline:
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json
- cycle 2 compare artifact:
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-214538-fixed3-cycle2-fact-owned-micro-skeleton\combined_summary.json

今回の mission:
- 対症療法は禁止
- telemetry 追加だけ、schema 追加だけ、文言調整だけ、prompt の言い換えだけは reject する
- 根本解決として `section が standalone で存在できる条件` を変える
- planner schema ではなく `section acceptance / merge / prune gate` を main owner として触る
- `company_grounded` で visible quality が generic / prompt_only に負ける原因を、空節または weak section acceptance の問題として扱う

今回の根本仮説:
- 問題は skeleton をどう書くかではなく、skeleton から writer に渡す前に `弱い節を残してしまう acceptance` にある
- `exclusive fact` や `must_cover` を持たない section が standalone のまま writer に渡ることで、company introduction に薄い説明節が残る
- したがって root fix は `section acceptance gate` であり、writer prompt 調整ではない

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

fixed3:
- ui-short-branding-trust
- ui-short-case-study-explain
- ui-short-branding-company-grounded

固定比較モード:
- generic
- algorithm
- prompt_only

今回の owner scope:
- 第一候補:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- 最小限必要なら:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- do not touch:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - C:\tetie\notecode\note\natural_blog_core.py
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py

今回の narrow hypothesis:
- writer 前の plan acceptance で
  - `exclusive fact = 0`
  - かつ `unique must_cover = 0`
  - かつ `merge_allowed_with` が存在
  の section を standalone 禁止にすると、company_grounded の薄い節が減り、must_cover を落とさず visible quality が改善する

今回やるべき root fix:
- support/planner から受けた section 候補を writer へ渡す前に acceptance gate を通す
- acceptance gate は次を判定する
  - standalone allowed
  - merge target
  - prune reason
- standalone 不許可の section は
  - merge 可能なら merge
  - merge 不可なら prune
- これにより `schema があるのに output に効かない` 状態を終わらせる

今回追加してよい telemetry:
- `section_role`
- `exclusive_fact_count`
- `unique_must_cover_count`
- `standalone_allowed`
- `merge_target`
- `pruned_reason`
- `section_created_without_exclusive_fact`

ただし重要:
- telemetry は証拠のために最小限だけ追加してよい
- telemetry 追加自体は成果ではない
- output surface に効かなければ reject

今回の merge / prune rule 初期案:
- standalone allow:
  - exclusive fact が 1 以上
  - または unique must_cover が 1 以上
  - または source-backed reader question を単独で受け持つ
- merge candidate:
  - result -> condition or closing
  - strength -> operation or closing
  - background -> reason or closing
- prune:
  - merge 先がなく、かつ section が新情報を単独で持たない場合

今回やってよいこと:
- section acceptance gate の追加
- merge/prune 判定の実装
- plan handoff の最小変更
- 必要な focused test 追加
- shared checks
- fixed3 live compare

今回やってはいけないこと:
- writer prompt の visible wording をまた調整すること
- heading progression を書き換えること
- section opening template をいじること
- prompt_only persona を algorithm に寄せること
- broad refactor
- prompt accretion
- module accretion
- telemetry だけ足して keep 判定すること

成功条件:
- company_grounded で
  - must_cover_reflection_rate >= 0.6667 を維持
  - source_trace_coverage = 1.0 を維持
  - generic / prompt_only に対して visible quality の改善または同等以上 + groundedness優位を説明できる
- target 2 cases で keep 条件を満たす
- non-target regression がない

reject 条件:
- company_grounded が generic / prompt_only より明確に弱い
- must_cover_reflection_rate が baseline を下回る
- source_trace_coverage が落ちる
- 空節は減らないのに実装だけ増える
- `root fix` ではなく `prompt tuning` に逃げた

実装イメージ:
- pipeline owner で `section_briefs` か planner result を受けた直後に
  - `_accept_or_merge_sections(...)`
  - `_compute_section_standalone_eligibility(...)`
  のような小さい helper を置いてよい
- helper の責務は
  - section 単位の事実量評価
  - merge target 決定
  - prune 判定
  のみ
- writer へは acceptance 後の section list だけを渡す

開始時に確認するコード:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - planner / support 結果の受け取り
  - writer 直前の handoff
  - repair acceptance と混線しない位置
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - support/planner schema の current 受け口
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - company intro / case study / planner handoff 関連

必ず実施する手順:
1. accepted baseline と cycle 1 / cycle 2 reject 理由を再確認する
2. `section acceptance gate` の narrow diff だけ入れる
3. focused tests
4. shared checks
5. fixed3 live compare
6. keep / rollback / simplify を判定する
7. reject なら rollback して accepted baseline に戻す

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q

live compare command:
- C:\tetie\notecode\.venv\Scripts\python.exe tools\run_minimum_hybrid_compare_matrix.py --live --case-set fixed3 --label cycle3-root-fix-section-acceptance

最終報告で必ず示すこと:
- 読んだ source-of-truth
- cycle 1 / cycle 2 reject reason の再確認
- touched owner
- root hypothesis
- diff
- tests
- live compare result
- `generic / algorithm / prompt_only` の勝敗
- company_grounded の must_cover_reflection_rate / source_trace_coverage / visible quality の変化
- keep / rollback / simplify の判定
- 対症療法ではなく root fix と言える理由
- まだダメなら `company_introduction は skeleton optimization 対象外` と判断すべきか
- AGENTS / WORKLOG 更新の有無
```
