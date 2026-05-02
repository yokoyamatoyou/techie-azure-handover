# separate window daily compare gate 2026-04-12

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
- あなたは `daily` input-contract diff の compare gate runner です
- 新しい実装はしない
- 既に入った `input_contract.py` の owner-local diff を前提に、5 batch compare を回して keep / rollback を判断する
- 判断がつくまでに必要な最小限の確認だけを行う

現在の前提:
- touched owner file:
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- daily の prompt/source から surface label を保持する経路が追加済み
- daily は抽象 default `背景 / 変化 / 学び` ではなく、source-backed な
  - `伝わっていないと感じた場面`
  - `何を変えたか`
  - `翌日に持ち越す学び`
  を `focus_bundle.support_points` と `must_cover` に持てる状態
- telemetry:
  - `prompt_surface_items` に daily 用の `raw / kept / dropped` を追加済み
- added test:
  - C:\tetie\notecode\note\tests\test_intent_profile.py

既知の検証状態:
- passed:
  - `note\tests\test_intent_profile.py` 15 passed
  - `note\tests\test_current_mainline_runner.py` 41 passed
  - `note\tests\test_current_mainline_regressions.py` 24 passed
  - `note\tests\test_current_mainline_ui_matrix.py` 24 passed
  - `note\tests\test_newalgorithm_phase03_pipeline.py -k "daily_story or input_contract"` 7 passed
- known unrelated failure:
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py:4134`
  - `test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
  - 現行 formatter title 期待値ズレであり、今回の daily/input-contract diff とは別系統

今回の narrow question:
- `input_contract.py` の daily 向け source/must-cover retention は、5 batch の compare で safe majority を作れるか
- それとも visible naturalness は維持しても grounding stability の改善が足りず rollback すべきか

hard rule:
- 今回は compare gate のみ
- 新規 code edit 禁止
- tests を直さない
- prompt を足さない
- owner scope を広げない
- AGENTS / WORKLOG / plan docs は更新しない
- keep か rollback か simplify-needed かを明示する

target case:
- primary:
  - `bl-daily-learning-log-grounded`
- optional confirm:
  - 既存の近い daily 系 case が runner で使えるなら 1 件まで追加可
- ただし fixture 追加や code edit はしない

compare modes:
- `generic`
- `algorithm step-optimized`
- `prompt-only persona`

batch plan:
- 5 batch 実施する
- 1 batch = 同一条件で 2 回生成
- つまり primary case だけでも `5 batch x 2 repeats x 3 modes`
- optional confirm case を足すなら同じ batch discipline を守る

なぜ今回も 5 batch か:
- daily は run-to-run の揺れが大きかった
- 単発の当たり run では keep 判断ができない
- 今回のゴールは visible improvement ではなく safe majority の確認

pass condition:
- `algorithm step-optimized` が 5 batch 中 3 回以上 safe winner または safe tie
- `must_cover_reflection_rate >= 0.90`
- `source_trace_coverage >= 0.95`
- visible naturalness が current generic baseline と同等以上
- `prompt-only` の単発当たり依存ではなく再現性がある
- non-target regression がない

rollback condition:
- 5 batch を回しても safe majority ができない
- `must_cover_reflection_rate` が baseline より悪化
- `source_trace_coverage` が baseline より悪化
- visible naturalness が明確に悪化
- retained labels が visible prose を硬くし、説明カード調を増やす

simplify-needed condition:
- coverage は改善するが visible naturalness が落ちる
- visible naturalness は保つが safe majority には届かない
- この場合は keep でも rollback でもなく、`input_contract` 単独での前進限界として持ち帰る

evaluation axes:
1. grounding stability
- source_trace_coverage
- must_cover_reflection_rate
- prompt_anchor_coverage
- raw / kept / dropped surface items の挙動

2. visible naturalness
- 日々のできごととして自然か
- 説明カード調になっていないか
- 事実保持のために本文が固くなっていないか
- `flat_or_repetitive` が悪化していないか

3. stability
- 2 回生成で大崩れしないか
- 5 batch 通して winner が寄るか
- 当たり run だけでなく外れ run の安全性が上がるか

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

実行:
- 既存 compare harness を使う
- result artifact root を明示して保存する
- batch ごとの summary と combined report を残す

最終報告で必ず示すこと:
1. 読んだ正本ファイル
2. 読んだ observation report
3. touched owner file
4. 現在の diff の要点
5. 実行した compare 条件
6. 5 batch x 2 repeats の結果
7. `generic / algorithm / prompt-only` の batch winner と final winner
8. `must_cover_reflection_rate` / `source_trace_coverage` の summary
9. keep / rollback / simplify-needed の判定
10. AGENTS / WORKLOG / plan docs 更新の有無

最終的に欲しい答え:
- この `input_contract.py` 差分だけで daily は safe majority に寄るか
- それとも方向性が弱く、次に進む前に rollback すべきか
```
