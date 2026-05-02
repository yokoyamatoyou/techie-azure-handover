# separate window daily grounding stability 2026-04-12

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
- C:\tetie\notecode\docs\skeleton_role_revision_proposal_2026-04-11.md
- C:\tetie\notecode\docs\separate_window_observe_article_type_routes_2026-04-12.md
- C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-12.md
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
- article type observation result:
  - C:\tetie\notecode\logs\codex_article_type_route_observation\20260412-094857-fourtype-fivebatch\combined_report.md
  - C:\tetie\notecode\logs\codex_article_type_route_observation\20260412-094857-fourtype-fivebatch\combined_report.json

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の役割:
- あなたは `daily` の narrow implementation worker です
- article-type 全体の policy を今すぐ mainline に入れる役ではありません
- `daily` だけを対象に、simple/generic 寄りの自然さを保ちながら grounding stability を上げる小さな diff を試してください

今回の bottom line:
- article-type observation では `daily` が最も情報価値の高い次対象だった
- visible naturalness は `generic / prompt-only` 側に寄るが、grounding が崩れて safe winner にならなかった
- したがって次の仮説は `daily では prompt を増やす` ではなく `source / must-cover state を writer まで lossless に渡す` です

今回の narrow question:
- `daily` の unsafe は style 不足ではなく、contract compression や writer handoff で source anchor / must-cover が落ちることが主因か
- もしそうなら、`input_contract.py` の narrow diff だけで safe majority に寄せられるか

owner:
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py

hard rule:
- 1 diff = 1 narrow hypothesis = 1 owner scope = 1 rollback unit
- 初回実験は `input_contract.py` のみ
- `prompt_builder.py`、`pipeline.py`、`natural_blog_core.py`、`output_formatter.py` は同時に触らない
- prompt accretion 禁止
- module accretion 禁止
- completed / frozen / archive-only boundary を破らない
- same hypothesis unchanged retry は 3 回まで

今回の hypothesis:
- `daily` は route 自体より、writer に渡る source anchor / prompt surface / must-cover memo の圧縮で grounding を落としている
- `input_contract.py` で `daily` 向けの surface retention と source-backed memo を narrow に keep すれば、visible naturalness を壊さず safe winner に近づく

今回の do:
- `input_contract.py` で `daily` case の raw / kept / dropped surface items と source anchor retention を読む
- `daily` で writer に残すべき source-backed items を narrow に保持する
- contract memo を長くしすぎない
- telemetry に raw / kept / dropped の差が見えるようにする
- owner-local tests
- shared checks
- `daily` 専用 compare を再実行する

今回の do not:
- `daily` 用 persona を増やさない
- prose style 指示を増やさない
- route selector を触らない
- repair acceptance を触らない
- article-type fixed rule を mainline に入れない
- 4 article type 全体を同時に再調整しない

今回の target case:
- primary:
  - `bl-daily-learning-log-grounded`
- optional confirm:
  - 既存で近い daily 系 case があれば 1 件まで追加してよい
- ただし fixture 追加のための code change はしない

比較モード:
- `generic`
- `algorithm step-optimized`
- `prompt-only persona`

batch 方針:
- はい、今回も 5 batch を回してください
- 1 batch = 同一条件で 2 回生成
- 理由:
  - daily は run-to-run の揺れが大きかった
  - single good run では keep 判断が危険
  - 今回の目的は visible 当たりを作ることではなく safe majority を作ること

pass condition:
- `daily` で 5 batch 中 3 回以上 `algorithm step-optimized` が safe winner か safe tie になる
- `must_cover_reflection_rate >= 0.90`
- `source_trace_coverage >= 0.95`
- visible naturalness が current generic baseline 以上
- `prompt-only` の当たり runにしか勝てない状態ではなく、再現性が出る
- non-target regression がない

rollback condition:
- 5 batch を回しても safe majority ができない
- `must_cover_reflection_rate` または `source_trace_coverage` が baseline より悪化する
- visible naturalness が明確に悪化する
- owner scope が `input_contract.py` を超えないと成立しない

evaluation axes:
1. grounding stability
- source_trace_coverage
- must_cover_reflection_rate
- prompt_anchor_coverage
- dropped surface item count

2. visible naturalness
- flat_or_repetitive が減るか
- 日記/日々のできごととして自然か
- 整理カード調になりすぎないか
- 宣伝調や説明ロボット化が出ないか

3. stability
- 2 回生成で大崩れしないか
- 5 batch 通して winner が寄るか
- 当たり run だけでなく外れ run の安全性が上がるか

必ず確認する observation:
- company / announcement は provisional に generic 寄り
- technical explain は algorithm 利得より coverage stop-loss が先
- daily は style 改善余地があるのに grounding が崩れるため、次 diff の情報価値が最も高い

metrics keep:
- prompt_anchor_coverage
- must_cover_reflection_rate
- source_trace_coverage
- sentence_ending_entropy
- ending_bucket_max_run
- ending_bucket_monotony_score
- paragraph_break_semantic_score
- sentence_length_cv
- paragraph_length_cv
- nominalization_rate
- flat_zone_count

tests:
- owner-local:
  - `input_contract.py` の surface retention / telemetry / daily 関連 test を探し、必要なら narrow に追加する
- shared checks:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q

もし keep になった場合の次 action:
- その時点で初めて `daily` を feature-based route rule の代表ケースとして扱う
- 次 owner 候補は `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- ただし今回はそこまで進めず、keep できたかどうかだけを持ち帰る

最終報告で必ず示すこと:
1. 読んだ正本ファイル
2. 読んだ observation report
3. touched owner file
4. 仮説
5. 変更内容
6. 実行した tests
7. `daily` の 5 batch x 2 repeats の結果
8. `generic / algorithm / prompt-only` の比較結果
9. keep / rollback / simplify の判定
10. AGENTS / WORKLOG / plan docs 更新の有無
```
