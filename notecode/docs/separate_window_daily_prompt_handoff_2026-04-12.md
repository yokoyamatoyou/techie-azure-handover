# separate window daily prompt handoff 2026-04-12

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

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の役割:
- あなたは `daily` の prompt handoff owner です
- 目的は `input_contract.py` に残った daily の source-backed items を writer prompt に十分届かせることです
- article-type policy 全体は変えない
- 4 article type を同時に触らない

今回の前提:
- upstream owner である `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py` には daily 向け retention diff がすでに入っている
- compare gate の結果:
  - `raw / kept / dropped` は改善した
  - `algorithm` は `must_cover_reflection_rate` を少し改善した
  - しかし `source_trace_coverage` は 0.45 に張り付き、5 batch すべて `winner=none_unsafe`
- current interpretation:
  - daily の unsafe 主因は contract retention 単独ではなく、downstream writer handoff が薄いこと

今回の narrow question:
- `simple_note_pipeline/prompt_builder.py` で daily の source-backed support / must-cover を writer に見える形へ narrow に渡せば、grounding stability を改善できるか
- その改善は visible naturalness を壊さずに起こるか

owner:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py

hard rule:
- 1 diff = 1 narrow hypothesis = 1 owner scope = 1 rollback unit
- 初回実験は `prompt_builder.py` のみ
- `input_contract.py` は前提として読むが同時に触らない
- `pipeline.py`、`natural_blog_core.py`、`output_formatter.py` は触らない
- prompt accretion 禁止
- module accretion 禁止
- article-type fixed rule を mainline に入れない
- same hypothesis unchanged retry は 3 回まで

今回の hypothesis:
- daily では source-backed items が contract までは残っているが、prompt_builder 側の prompt surface で writer が使いやすい形に再構成されていない
- `prompt_builder.py` で daily 向け must-cover / support / source anchor の handoff を少しだけ明瞭にすれば、`source_trace_coverage` と safe majority が改善する
- ただし prose style 指示を増やしてはいけない

今回の do:
- `prompt_builder.py` で daily の prompt 組み立て経路を読む
- contract から来ている daily 用 must-cover / support points / source anchor がどこで薄まるか確認する
- writer に渡す daily 向け handoff を narrow に強める
- source-backed items を section-shadow 的テンプレへ増やしすぎない
- owner-local tests
- shared checks
- `daily` の 5 batch compare を再実行する

今回の do not:
- persona 指示を増やさない
- daily 専用の長い hidden schema を追加しない
- `背景 / 変化 / 学び` のような visible template を強化しない
- route selector を触らない
- repair acceptance を触らない
- 4 genre の policy をいま決めない

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
- 今回も 5 batch を回す
- 1 batch = 同一条件で 2 回生成
- 理由:
  - daily は run-to-run の揺れが大きい
  - 前回 compare gate では `none_unsafe x5`
  - single good run では keep 判断ができない

pass condition:
- `algorithm step-optimized` が 5 batch 中 3 回以上 safe winner または safe tie
- `must_cover_reflection_rate >= 0.90`
- `source_trace_coverage >= 0.95`
- visible naturalness が current generic baseline と同等以上
- 説明カード調や template 感を増やしていない
- non-target regression がない

rollback condition:
- 5 batch を回しても safe majority ができない
- `must_cover_reflection_rate` が baseline より悪化
- `source_trace_coverage` が baseline より悪化
- source anchor を増やしたことで本文が硬くなる
- owner scope が `prompt_builder.py` を超えないと成立しない

simplify-needed condition:
- coverage は改善するが visible naturalness が悪化する
- naturalness は保つが safe majority には届かない
- handoff を強めるほど daily が説明カード化する

evaluation axes:
1. grounding stability
- source_trace_coverage
- must_cover_reflection_rate
- prompt_anchor_coverage
- support points の reflection

2. visible naturalness
- 日々のできごととして自然か
- 説明カード調になっていないか
- source anchor を増やしたせいで列挙調になっていないか
- `flat_or_repetitive` が悪化していないか

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
  - contract retention は改善した
  - しかし `source_trace_coverage = 0.45` で頭打ち
  - よって next owner は writer handoff

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
  - `prompt_builder.py` の daily / prompt surface / must-cover handoff 関連 test を探し、必要なら narrow に追加する
- shared checks:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "daily_story or prompt_builder" -q
- known unrelated failure は切り分けて報告する

もし keep になった場合の次 action:
- その時点で初めて `daily` の feature-based route rule へ進む余地を report する
- ただし今回はそこまで進めず、keep / rollback / simplify-needed を返す

最終報告で必ず示すこと:
1. 読んだ正本ファイル
2. 読んだ observation / compare gate report
3. touched owner file
4. 仮説
5. 変更内容
6. 実行した tests
7. `daily` の 5 batch x 2 repeats の結果
8. `generic / algorithm / prompt-only` の batch winner と final winner
9. `must_cover_reflection_rate` / `source_trace_coverage` の summary
10. keep / rollback / simplify-needed の判定
11. AGENTS / WORKLOG / plan docs 更新の有無

最終的に欲しい答え:
- `prompt_builder.py` の handoff 調整だけで daily は safe majority に寄るか
- それとも daily 方向はここで打ち止めにすべきか
```
