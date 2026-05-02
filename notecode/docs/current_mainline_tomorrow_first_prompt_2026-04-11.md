# current mainline tomorrow first prompt 2026-04-11

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
- C:\tetie\notecode\docs\autonomous_naturalness_repair_plan_2026-04-11.md
- C:\tetie\notecode\docs\stepwise_three_article_gate_2026-04-08.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md

開始時に必ず確認する artifact:
- C:\tetie\notecode\logs\latest_generation_output.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- C:\tetie\notecode\logs\generation_audit_log.jsonl
- C:\tetie\notecode\logs\codex_ui_live_check_20260411\
- latest attempt id は 2026-04-11 09:47:38 の `gen-f914d30e`

今回の mission:
- `branding / company_introduction` の visible AI feel を 10 loop 前後の自律ループで下げる
- 数値改善だけでなく、人が読んだときの改行の呼吸、段落の役割差、文末の自然さを改善する
- `quality warning を UI に見せる` ではなく `内部修正する / 通らなければ止める` へ寄せる
- 毎 loop で `generic / algorithm step-optimized / prompt-only persona` を比較する
- prompt-only persona は日本語ブログ作成者の persona 指示を細かめに与える比較対象として扱う
- prompt-only が継続的に勝つ場合、最終的に `best practice = prompt-only` と判断してよい
- prompt accretion 禁止
- module accretion 禁止
- module removal / split / small helper replacement は許可
- WEB検索を使ってよいが、一次ソースと論文中心にする

fixed operational rules:
- `1 loop = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- same hypothesis unchanged retry は 3 回まで
- 10 loops を上限目安にする
- keep / rollback / simplify のいずれかを毎回判断する
- completed / frozen / archive-only boundary を破らない
- current success path を壊さない

loop priority:
1. `note\simple_note_pipeline\pipeline.py`
   - branding/company intro で `quality warning only success` を減らし、 internal repair / fail-closed へ寄せる
2. `note\simple_note_pipeline\prompt_builder.py`
   - duplicated style / section-shadow / semantic-ledger 指示を削る
3. `note\newalgorithm_pipeline\input_contract.py`
   - prompt surface retention を keep しつつ memo を短くする
4. `note\natural_blog_core.py`
   - source-aware prune の追加確認は必要時のみ
5. `note\newalgorithm_pipeline\output_formatter.py`
   - paragraph breath を均していないか必要時だけ確認
6. `note\newalgorithm_pipeline\pipeline.py`
   - route ownership reopen は最後だけ、branch accretion ではなく simplification と remove を優先する

evaluation battery:
- production-like latest blank prompt
- `ui-short-branding-company-grounded`
- `ui-short-branding-trust`
- guard: `ui-short-case-study-explain`
- compare modes:
  - `generic`
  - `algorithm step-optimized`
  - `prompt-only persona`

必須判定:
- target 2 cases で `generic` baseline より AI feel が低い
- target 2 cases で `prompt-only persona` と比較する
- guard regression なし
- 改行の呼吸が均一すぎない
- 後半が言い換え反復になっていない
- `整理できます / つながります / 見えてきます` 型の説明カード調が減る

metrics keep:
- sentence_length_cv
- paragraph_length_cv
- sentence_ending_entropy
- ending_bucket_max_run
- ending_bucket_monotony_score
- nominalization_rate
- morphological_ngram_entropy
- dependency_depth_avg
- paragraph_break_semantic_score
- prompt_anchor_coverage
- must_cover_reflection_rate
- source_trace_coverage

research references:
- https://aclanthology.org/2023.emnlp-main.136/
- https://aclanthology.org/2024.acl-long.3/
- https://aclanthology.org/2024.emnlp-main.971/
- https://aclanthology.org/2024.lrec-main.1055/
- https://aclanthology.org/2025.acl-long.803/
- https://aclanthology.org/2023.acl-demo.52/
- https://aclanthology.org/2025.coling-main.557/

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 読んだ latest logs
- 各 loop の hypothesis / owner / diff / tests / live verdict
- 各 loop の `generic / algorithm / prompt-only` 比較
- keep した変更
- rollback した変更
- 減らした module / prompt / branch
- まだ残る AI-like symptom
- prompt-only を best practice と判断するか
- SaaS として通せるかの判定
```
