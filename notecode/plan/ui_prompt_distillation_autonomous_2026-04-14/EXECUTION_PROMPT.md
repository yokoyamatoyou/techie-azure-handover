# ui_prompt_distillation_autonomous_2026-04-14 EXECUTION PROMPT

## prompt

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
- C:\tetie\notecode\docs\management_window_route_policy_coordinator_2026-04-12.md
- C:\tetie\notecode\docs\separate_experiment_prompt_runtime_distillation_handoff_2026-04-13.md
- C:\tetie\notecode\docs\separate_experiment_fixed3_naturalness_final_report_2026-04-13.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\README.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\TASK.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\PROGRESS.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\ROLLBACK.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\README.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\TASK.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\PROGRESS.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\ROLLBACK.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\EXECUTION_PROMPT.md

今回の実施範囲:
- current package の continuation ではなく separate autonomous line
- fixed category inventory:
  - explanatory_article
  - industry_analysis
  - branding
  - announcement
  - case_study
  - comparative_review
  - daily_story
- source-of-truth は current package ではなくこの package
- current package keep-state は壊さない
- UI は触らない
- route default は壊さない

本線仮説:
- UI input -> distilled prompt -> single-pass generation
- distilled prompt は以下の 5 要素に固定:
  - task sentence
  - core message
  - source digest
  - voice policy
  - style hints
- raw UI dump をそのまま prompt にしない
- company intro は neutral explainer default
- self voice は必要時のみ `私たち`
- heavy editor rewrite は本線にしない

フェーズ:
- Phase 0 inventory freeze
- Phase 1 distillation design
- Phase 2 implementation phase 1
- Phase 3 implementation phase 2
- Phase 4 baseline compare
- Phase 5 category evaluation
- Phase 6 category repair loop
- Phase 7 final judgment

評価ルール:
- 各カテゴリ 3 reruns
- Codex 視認評価で自然さ / lead / title / brochure feel / repetition / paragraph breathing / grounding を判定
- fail category は仮説を変えながら最大 7 回修正
- 3回連続で同じ failure mode が改善しないなら stop 候補

最終報告で必ず示すこと:
1. created separate package files
2. fixed category inventory
3. phase ledger
4. touched owner files by phase
5. each phase の tests
6. each phase の rerun / compare artifacts
7. WEB検索で使った sources
8. 各カテゴリの 3 reruns 視認評価結果
9. 各カテゴリの修正 loop 回数と採用 / 不採用
10. stable pass categories
11. unstable pass categories
12. unresolved categories
13. current package keep baseline に対して勝った点 / 負けた点
14. prompt-only floor に対して勝った点 / 負けた点
15. public web compare に対して勝った点 / 負けた点
16. direct GPT web compare の可否
17. separate line 全体 verdict
18. current package keep-state を更新したかどうか
19. AGENTS / WORKLOG 更新有無
```
