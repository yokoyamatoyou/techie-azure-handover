# separate window initial prompt 2026-04-11

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
- C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-11.md
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
- latest attempt id は `gen-f914d30e` を baseline とする

今回の mission:
- `branding / company_introduction` の visible AI feel を下げる
- 数値だけでなく、人が読んだときの改行の呼吸、段落の役割差、文末の自然さ、後半の言い換え反復の少なさを改善する
- `quality warning を UI に見せる` ではなく `内部で修正する / 通らなければ止める` に寄せる
- 対症療法の追加ではなく simplification を含めて判断する
- prompt accretion 禁止
- module accretion 禁止
- module removal / split / small helper replacement は許可
- WEB検索は許可。一次ソースと論文中心に使う

固定比較条件:
- 全 loop で `generic / algorithm step-optimized / prompt-only persona` の 3-way compare を行う
- `prompt-only persona` は日本語ブログ作成者の細かめ persona 指示を与える強い比較対象として扱う
- prompt-only が継続優位なら、algorithm を足すより減らす
- prompt-only が安定して勝つなら、最終的に `best practice = prompt-only` を選んでよい

prompt-only persona の方針:
- 日本語の note / ブログ記事を自然に仕上げる編集者として振る舞う
- 会社紹介、導入支援、事例記事を、宣伝調に寄せすぎず、読者が無理なく読める読み物へ落とす
- 文末を揃えすぎない
- 段落の長さを揃えすぎない
- 主語は必要なときだけ置く
- `整理できます / つながります / 見えてきます` 型の説明カード調を避ける
- ソースにない実績や数値を足さない

実行ルール:
- `10 loop` を上限目安にする
- `1 loop = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- same hypothesis unchanged retry は 3 回まで
- 各 loop で `keep / rollback / simplify` を必ず判定する
- current success path は壊さない
- completed / frozen / archive-only boundary は破らない

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

evaluation battery:
- production-like latest blank prompt
- `ui-short-branding-company-grounded`
- `ui-short-branding-trust`
- guard: `ui-short-case-study-explain`

必須判定:
- target 2 cases で `generic` baseline より AI feel が低い
- target 2 cases で `prompt-only persona` と比較する
- guard regression がない
- 改行の呼吸が均一すぎない
- 文末の型が続きすぎない
- 後半が言い換え反復になっていない
- 会社紹介として自然で、説明ロボット化していない

metrics keep:
- sentence_length_cv
- paragraph_length_cv
- sentence_ending_entropy
- sentence_ending_fine_entropy
- ending_bucket_max_run
- ending_bucket_monotony_score
- nominalization_rate
- morphological_ngram_entropy
- pos_sequence_entropy
- dependency_depth_avg
- paragraph_break_semantic_score
- prompt_anchor_coverage
- must_cover_reflection_rate
- source_trace_coverage

loop priority:
1. `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
   - `quality warning only success` を減らし、internal repair / fail-closed に寄せる
2. `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
   - duplicated style / section-shadow / semantic-ledger 指示を削る
3. `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
   - prompt surface retention を keep しつつ memo を短くする
4. `C:\tetie\notecode\note\natural_blog_core.py`
   - abstract filler が残る場合のみ
5. `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
   - paragraph breath が still artificial な場合のみ
6. `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
   - route ownership reopen は最後だけ。branch accretion ではなく simplification を優先する

research references:
- https://aclanthology.org/2023.emnlp-main.136/
- https://aclanthology.org/2024.acl-long.3/
- https://aclanthology.org/2024.emnlp-main.971/
- https://aclanthology.org/2024.lrec-main.1055/
- https://aclanthology.org/2025.acl-long.803/
- https://aclanthology.org/2023.acl-demo.52/
- https://aclanthology.org/2025.coling-main.557/

各 loop の必須出力:
- hypothesis
- touched owner
- changed files
- baseline metrics
- after metrics
- `generic / algorithm / prompt-only` 比較
- human-visible verdict
- keep / rollback / simplify
- complexity delta

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 読んだ latest logs
- 10 loop の実施結果
- keep した変更
- rollback した変更
- 減らした module / prompt / branch
- まだ残る AI-like symptom
- prompt-only を best practice と判断するか
- SaaS として通せるかの判定

開始アクション:
1. latest logs と latest live artifacts を読み、baseline を要約する
2. production-like latest blank prompt と target 2 cases の現在問題を列挙する
3. prompt-only persona baseline を先に 1 回生成して保存する
4. loop 1 の owner を `simple_note_pipeline/pipeline.py` に固定し、internal repair / fail-closed の narrow hypothesis を立てる
5. tests -> live compare -> keep/rollback/simplify を進める
```
