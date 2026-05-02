# separate window observe article type routes 2026-04-12

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
- C:\tetie\notecode\docs\separate_window_evaluate_external_research_2026-04-12.md
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

今回の役割:
- あなたは implementation worker ではなく observation runner です
- 実装変更はしない
- plan docs も書き換えない
- AGENTS / WORKLOG も更新しない
- 目的は `記事タイプごとに、generic / algorithm / prompt-only のどれが安定して勝つか` を 5 batch の観測で持ち帰ることだけです

重要:
- current success path は壊さない
- current runtime code は変更しない
- compare harness / prompt mode / batch runner を使って観測だけを行う
- broad 解釈や将来設計は最終報告で提案してよいが、コード差分は作らない

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の narrow question:
- 記事タイプにより、`simple / grounded generic` が強いものと、`skeleton / planning / algorithm` が強いものが分かれるか
- もし分かれるなら、次の調整は article type 単位で切るべきか
- `company_introduction` だけの特殊問題なのか、短文系 genre に共通する傾向なのか

今回の article types:
1. 技術解説的記事
2. お知らせ
3. 企業説明
4. 日々のできごと

case 設計ルール:
- 各 article type で代表ケースを 1 つに固定する
- source / must-cover / tone の条件は 5 batch を通して固定する
- 途中で case を差し替えない
- 既存の UI live check case が使えるなら優先する
- 既存 case がない場合は、最小の representative input を作るが、今回の window では code change を伴う fixture 追加はしない

batch 設計:
- 各 article type について 5 batch
- 1 batch = 同一条件で 2 回生成
- compare modes:
  - `generic`
  - `algorithm`
  - `prompt-only persona`
- 可能なら同一 batch の 2 回生成は parallel に近い形で実行する
- ただし batch 内の条件差は乱数的変動以外入れない

観測の主目的:
- 記事タイプごとの winner を決めること
- run-to-run のブレを見ること
- `naturalness` と `coverage` の tradeoff を見ること
- 次に実装実験すべき article type を 1 つに絞ること

今回の前提仮説:
- `company_introduction` は simple / grounded generic 寄りの可能性が高い
- `announcement` は短文だが、必須項目 coverage の制約が強い可能性がある
- `daily` は simple / prompt-like 寄りの可能性がある
- `technical explain` は role diversity 次第で algorithm の利得が残る可能性がある
- ただし今回の window は仮説の検証だけを行い、調整はしない

do:
- 既存の compare / live check / batch runner を確認する
- 4 article type の representative case を固定する
- 各 type で 5 batch x 3 modes x 2 runs を回す
- metrics と human-visible verdict をまとめる
- batch ごとの winner と final winner を出す
- variance が大きい type を明示する
- next implementation candidate を 1 type だけ提案する

do not:
- runtime code を編集しない
- tests を直さない
- compare harness 自体を改造しない
- 結果が悪いからといって途中で prompt や case を変えない
- batch 数を増減しない
- article type を追加しない

必ず確認する baseline:
- C:\tetie\notecode\logs\latest_generation_output.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- compare artifact:
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-225911-fixed3-cycle3-root-fix-section-acceptance\combined_summary.json
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-233627-fixed3-cycle4-root-fix-company-intro-route-exclusion\combined_summary.json
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260412-011207-fixed3-codex-route-bypass-20260412\combined_summary.json

evaluation axes:
1. visible naturalness
- 改行の呼吸が均一すぎないか
- 後半が言い換え反復になっていないか
- 説明カード調になっていないか
- 人が書いたような段落役割差があるか

2. coverage / grounding
- must-cover を落としていないか
- source trace が落ちていないか
- announcement なら重要情報欠落がないか
- technical explain なら説明順の崩れがないか

3. stability
- 2 回生成で勝者がぶれすぎないか
- 5 batch 通して winner が安定するか
- score だけでなく visible verdict が安定するか

4. business readiness
- SaaS で通すならどれが safest か
- 自然だが不安定なのか
- 少し硬いが coverage が安全なのか

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

winner 判定ルール:
- 1 batch ごとに winner を 1 つ出す
- final winner は 5 batch 中 3 回以上勝った mode を first candidate とする
- ただし must_cover / source_trace floor を割る mode は winner にしない
- floor:
  - must_cover_reflection_rate が 0.90 未満なら unsafe
  - source_trace_coverage が 0.95 未満なら unsafe
- visible quality が高くても unsafe なら採用候補から外す

安定判定:
- provisional stable:
  - same mode が 5 batch 中 4 回以上 win/tie
  - unsafe ケースがない
  - visible verdict の崩れが少ない
- unstable:
  - winner が割れる
  - run-to-run 差が大きい
  - quality と coverage の tradeoff が毎回逆転する

article-type 別の見たいポイント:
- 技術解説的記事:
  - role diversity / explanation order / omission の出方
- お知らせ:
  - date / change point / action item / caution の欠落
- 企業説明:
  - company_introduction と同型に simple 側が勝つか
- 日々のできごと:
  - 不自然な整理調や宣伝調が出ないか

結果の保存:
- 各 batch の compare summary path
- article type ごとの集約 summary
- できれば最終的に 1 つの combined report を作る
- ただし code は触らず、結果ファイル / markdown report のみでよい

最終報告で必ず示すこと:
1. 読んだ正本ファイル
2. 固定した 4 article type と各 representative case
3. 実行した batch 数
4. 各 article type の batch ごとの winner
5. 各 article type の final winner
6. stable / unstable 判定
7. `generic / algorithm / prompt-only` の長所短所
8. 次に implementation 実験すべき article type を 1 つ
9. article-type fixed rule に進むべきか、feature-based rule に進むべきか
10. AGENTS / WORKLOG / plan docs は未更新であること

最終的に欲しい結論:
- `company_introduction` だけが simple 寄りなのか
- `announcement` や `daily` も simple 寄りなのか
- `technical explain` は algorithm の利得が残るのか
- 次の separate-window 実装対象をどれにするか
```
