# separate window daily prompt simplify final loop 2026-04-12

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
- C:\tetie\notecode\docs\separate_window_daily_grounding_stability_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_daily_compare_gate_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_daily_prompt_handoff_2026-04-12.md
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
- daily compare gate result:
  - C:\tetie\notecode\logs\codex_daily_compare_gate\20260412-110830-daily-input-contract-fivebatch\combined_report.md
  - C:\tetie\notecode\logs\codex_daily_compare_gate\20260412-110830-daily-input-contract-fivebatch\combined_report.json
- latest daily prompt handoff result:
  - handoff diff 後の combined_report.md / combined_report.json を確認する
  - mean_must_cover が `0.6667 -> 0.8667`
  - mean_source_trace が `0.45 -> 0.65`
  - safe majority は未達

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の役割:
- あなたは `daily` の最終 narrow simplify loop worker です
- 目的は `prompt_builder.py` の daily handoff をこれ以上太くせず、最小化と再圧縮で safe majority に寄せられるかを確認することです
- これは daily 方向の final local attempt です

今回の前提:
- `input_contract.py` の retention diff は前提として残っている
- `prompt_builder.py` の daily handoff diff も前提として存在する
- 直近の結果では改善は出たが keep 判定には届かなかった
- current interpretation:
  - handoff 方向は誤っていない
  - ただし今の handoff は still too wide / too explicit の可能性がある
  - 次にやるべきは強化ではなく simplification

今回の narrow question:
- `prompt_builder.py` の daily 向け handoff をさらに太くするのではなく、最小の核に圧縮したほうが source_trace と naturalness の両立に効くか
- それでも safe majority ができないなら、daily 方向はこの owner で打ち止めにすべきか

owner:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py

hard rule:
- 1 diff = 1 narrow hypothesis = 1 owner scope = 1 rollback unit
- 今回も `prompt_builder.py` のみ
- `input_contract.py` を同時に触らない
- `pipeline.py`、`natural_blog_core.py`、`output_formatter.py` を触らない
- prompt accretion 禁止
- hidden schema accretion 禁止
- daily 用のラベルや section role を増やさない
- same hypothesis unchanged retry は今回で終了

今回の hypothesis:
- daily の handoff は source-backed items を writer に渡す方向で改善した
- ただし support / must_cover / source_fact_pool / shadow を見せすぎて、daily が still rigid かつ grounding も十分伸びていない
- `prompt_builder.py` で writer に渡す daily handoff を 2-3 核へ再圧縮すれば、coverage を大きく落とさず naturalness と source_trace のバランスが改善する可能性がある

今回の do:
- `prompt_builder.py` の daily 向け handoff を読む
- current daily handoff のどの部分が重複かを確認する
- must_cover / support / source_fact_pool のうち writer に本当に必要な最小核だけを残す
- SECTION_SHADOW を強化するのではなく薄くする方向で調整する
- ラベル文言が visible prose を説明カード化しないようにする
- owner-local tests
- shared checks
- `daily` の 5 batch compare を再実行する

今回の do not:
- 新しい daily 専用 prompt block を足さない
- persona 指示を増やさない
- route policy を変えない
- article-type fixed rule を導入しない
- 4 genre の観測をやり直さない
- daily 以外に触らない

今回の target case:
- primary:
  - `bl-daily-learning-log-grounded`
- optional confirm:
  - 既存の近い daily 系 case が使えるなら 1 件まで追加可
- fixture 追加のための code change はしない

compare modes:
- `generic`
- `algorithm step-optimized`
- `prompt-only persona`

batch plan:
- 今回も 5 batch
- 1 batch = 同一条件で 2 回生成
- これが daily 方向の final gate

pass condition:
- `algorithm step-optimized` が 5 batch 中 3 回以上 safe winner または safe tie
- `must_cover_reflection_rate >= 0.90`
- `source_trace_coverage >= 0.95`
- visible naturalness が current generic baseline と同等以上
- 説明カード調 / 列挙調 / hidden template 感を増やしていない

rollback condition:
- 5 batch を回しても safe majority ができない
- `must_cover_reflection_rate` または `source_trace_coverage` が前 loop より悪化
- simplification したのに visible naturalness も改善しない
- owner scope が `prompt_builder.py` を超えないと前進しない

keep-but-stop condition:
- metrics が少し改善しても safe majority ができない
- この場合、diff は workspace に残してよいが、daily 方向の separate-window loop はここで停止する
- 次 owner へは進めず、daily は unresolved として持ち帰る

evaluation axes:
1. grounding stability
- source_trace_coverage
- must_cover_reflection_rate
- prompt_anchor_coverage

2. visible naturalness
- 日々のできごととして自然か
- 説明カード調や列挙調が減るか
- source anchor を残しつつ硬さが減るか
- `flat_or_repetitive` が悪化しないか

3. stability
- 2 回生成で大崩れしないか
- 5 batch 通して winner が寄るか
- 当たり run だけでなく外れ run の安全性が上がるか

必ず確認する local evidence:
- article-type observation:
  - company / announcement は provisional に generic 寄り
  - technical explain は algorithm 利得より coverage stop-loss が先
  - daily は style 改善余地があるのに grounding が崩れる
- daily compare gate:
  - contract retention は改善したが source_trace は 0.45
- daily prompt handoff:
  - must_cover / source_trace は改善したが safe majority には届かない
  - よって final local attempt は simplification

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
  - `prompt_builder.py` の daily / prompt surface / handoff 関連 test を narrow に更新する
- shared checks:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "daily_story or prompt_builder" -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "daily_story or prompt_builder" -q
- known unrelated failure は切り分けて報告する

最終報告で必ず示すこと:
1. 読んだ正本ファイル
2. 読んだ observation / compare gate / prompt handoff report
3. touched owner file
4. 仮説
5. 変更内容
6. 実行した tests
7. `daily` の 5 batch x 2 repeats の結果
8. `generic / algorithm / prompt-only` の batch winner と final winner
9. `must_cover_reflection_rate` / `source_trace_coverage` の summary
10. keep / rollback / keep-but-stop の判定
11. AGENTS / WORKLOG / plan docs 更新の有無

最終的に欲しい答え:
- simplification だけで daily は safe majority に寄るか
- それとも daily 方向はここで停止し、別 article type または別 owner 問題として切り直すべきか
```
