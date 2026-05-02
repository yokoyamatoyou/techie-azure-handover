# separate window cycle4 root fix company intro route exclusion 2026-04-11

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
- C:\tetie\notecode\docs\separate_window_cycle3_root_fix_section_acceptance_2026-04-11.md
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
  - hidden schema を足しても company_grounded の visible quality は動かなかった
- cycle 3 reject:
  - section acceptance gate を足しても company_grounded で applied=false / merged_section_count=0 / pruned_section_count=0 となり、actuation しなかった
  - company_grounded の algorithm は must_cover_reflection_rate=0.3333 まで落ち、prompt_only が 1.0 / 1.0 で勝った
- rollback 済みで、現在は accepted baseline に戻っている

今回の local root-cause reading:
- current code では company_introduction は compact_plan safe scope に入っている
- しかし generation prompt では company_introduction に対して `SECTION_SHADOW` を suppress している
- つまり company_intro は
  - planning 側には入っている
  - しかし realization 側では section-level handoff を意図的に使っていない
- この `half-on / half-off` の route mismatch により、compact_plan optimization が company_intro に効かない
- cycle 3 の actuation false は、その mismatch の証拠として扱う

今回の research conclusion:
- Step-by-Step / DYPLOC / PLANET 系の研究では、planning は realization に尊重される必要がある
- planning と realization が disjoint だと output is not guaranteed to respect the planning results
- notecode の company_intro はまさにこの disconnection 状態にある
- したがって root fix は `planning をもっと足す` ことではなく、`company_intro を half-on planning route から外すか、完全に接続し直すか` のどちらか
- prompt accretion / telemetry accretion / weak section pruning 再挑戦は root fix ではない

今回の mission:
- root fix として `company_introduction を compact-plan optimization 対象外にする` 仮説を検証する
- つまり company_intro の primary generation では compact_plan scaffold / compact_plan-driven structure を使わず、
  - source-aware prune
  - company intro writer brief
  - preflight
  - source grounding
  を mainline owner として使う
- これは「骨格の使い方調整」ではなく、「不整合な route ownership を解消する」 root fix として扱う

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

accepted baseline compare:
- C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json

cycle 3 compare artifact:
- C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-225911-fixed3-cycle3-root-fix-section-acceptance\combined_summary.json

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
- company_introduction を compact-plan safe scope から外し、source-aware writer-brief route に一本化すると、disconnected planning の悪影響が消え、company_grounded の must_cover と visible quality が prompt_only / generic に近づく

今回の root fix 内容:
- company_introduction は current architecture では compact-plan optimization の valid target ではない、と明示的に扱う
- company_introduction primary generation では
  - compact_plan build をしない
  - compact_plan scaffold を primary generation に入れない
  - writer brief / preflight / source grounding を main owner にする
- trust / case-study など他 semantic は現状 route を維持する

今回やってよいこと:
- `_compact_plan_safe_scope()` など route eligibility の company_intro 条件を見直す
- company_intro だけ compact_plan primary generation を opt-out する
- それで repair / diagnostics が壊れる場合は company_intro 専用の最小 fail-open / no-plan handling を入れる
- focused tests を追加する
- shared checks
- fixed3 live compare

今回やってはいけないこと:
- writer prompt の wording を調整して誤魔化すこと
- prompt_only persona を algorithm に移植すること
- section acceptance telemetry を増やして成果扱いすること
- company_intro 以外まで route を広げること
- broad refactor
- prompt accretion
- module accretion

確認すべき local evidence:
- pipeline.py の `_compact_plan_safe_scope()` に company_introduction が入っていること
- prompt_builder.py の generation prompt では `SECTION_SHADOW` が `semantic_key != company_introduction` 条件で suppress されていること
- この 2 つが同時成立しているなら、company_intro は route mismatch 状態にある

開始時に確認するコード:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - `_compact_plan_safe_scope()`
  - `_compact_plan_scaffold_enabled()`
  - `_maybe_build_compact_plan()`
  - company_intro primary generation path
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - company intro writer brief
  - preflight company intro generation blocks
  - `SECTION_SHADOW` suppress 条件
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - compact plan safe scope
  - company intro generation prompt tests

成功条件:
- company_grounded で
  - must_cover_reflection_rate >= 0.6667
  - source_trace_coverage = 1.0
  - generic / prompt_only と同等以上、または groundedness を保ったまま visible quality の改善を説明できる
- target 2 cases keep、guard regression なし
- company_intro route mismatch を 1 owner scope で解消したと言える

reject 条件:
- company_grounded の must_cover が baseline を下回る
- generic / prompt_only より弱い
- trust / case-study に regression
- compact_plan opt-out しただけで visible quality も coverage も改善しない

手順:
1. accepted baseline と cycle 1-3 reject reason を再確認する
2. company_intro route mismatch を local code で確認する
3. company_intro compact-plan opt-out の narrow diff を入れる
4. focused tests
5. shared checks
6. fixed3 live compare
7. keep / rollback / simplify を判定する
8. reject なら rollback

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q

live compare command:
- C:\tetie\notecode\.venv\Scripts\python.exe tools\run_minimum_hybrid_compare_matrix.py --live --case-set fixed3 --label cycle4-root-fix-company-intro-route-exclusion

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 読んだ research conclusion
- company_intro route mismatch の local evidence
- touched owner
- root hypothesis
- diff
- tests
- live compare result
- `generic / algorithm / prompt_only` の勝敗
- company_grounded の must_cover_reflection_rate / source_trace_coverage / visible quality の変化
- keep / rollback / simplify の判定
- これが対症療法ではなく root fix である理由
- まだダメなら `company_introduction は prompt-only-like / generic-like mainline が正` と判断すべきか
- AGENTS / WORKLOG 更新の有無
```
