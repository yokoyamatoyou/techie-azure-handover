# separate window initial prompt 2026-04-11 minimum hybrid research handoff

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
- C:\tetie\notecode\docs\separate_window_initial_prompt_2026-04-11_minimal_hybrid_keep.md
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

追加で必ず読む research handoff:
- C:\tetie\notecode\research\新しいフォルダー (9)\00_RESEARCH_PROMPT.md
- C:\tetie\notecode\research\新しいフォルダー (9)\01_CONTEXT_AND_STATUS_2026-04-11.md
- C:\tetie\notecode\research\新しいフォルダー (9)\02_WEB_RESEARCH_SUMMARY_2026-04-11.md
- C:\tetie\notecode\research\新しいフォルダー (9)\新しいフォルダー\AI生成記事の品質改善計画レビュー.md
- C:\tetie\notecode\research\新しいフォルダー (9)\新しいフォルダー\deep-research-report (27).md
- C:\tetie\notecode\research\新しいフォルダー (9)\新しいフォルダー\新規 テキスト ドキュメント.txt
- C:\tetie\notecode\research\新しいフォルダー (9)\新しいフォルダー\新規 テキスト ドキュメント (2).txt

今回の mission:
- `best practice = minimum hybrid keep` を current 第一候補として継続する
- `prompt-only` を強い比較対象として維持するが、現時点では本番全面採用しない
- `branding / company_introduction` の visible AI feel をさらに下げる
- 特に `company_introduction` で
  - 改行の呼吸
  - 段落の役割差
  - 必要なところだけ主語を置く
  - 後半の言い換え反復回避
  を改善する
- prompt accretion ではなく
  - backend synthesized prompt
  - prompt preflight
  - section-local grounding
  - narrow repair
  の再配置で進める

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

current keep state:
- owner:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- keep:
  - company-introduction generation では `SECTION_SHADOW` を出さない
  - semantic ledger と evidence は keep
  - company-introduction repair では narrow shadow guidance を keep
  - `topic=` へ raw long prompt を丸ごと残さず compact 化する
  - company-introduction では backend synthesized writer brief を keep
  - company-introduction では preflight で `hints=` と no-op auto tone を落とす keep diff が入っている

今回の current code diff の要点:
- `prompt_builder.py`
  - `_build_company_intro_writer_brief` を導入
  - `_preflight_company_intro_generation_blocks` を導入
  - company-introduction では
    - UI入力を短い writer brief に再合成
    - `hints=` を削除
    - `トーン補足: 記事タイプに合わせて自然な語り口を選ぶ。` を削除
- ただし external deep research 4 本は
  - `preflight は必要だが現状はまだ浅い`
  - `STRUCTURE / STYLE の重複がまだ残っている`
  - `section-local fact_anchor / do_not_mix が必要`
  - `evaluation / repair trigger 感度不足` を共通指摘している

必ず読む recent artifact:
1. production-like baseline
   - C:\tetie\notecode\logs\latest_generation_output.txt
   - C:\tetie\notecode\logs\latest_generation_output.json
   - C:\tetie\notecode\logs\latest_generation_quality_report.json
   - attempt id `gen-f914d30e`
2. latest live compare
   - C:\tetie\notecode\logs\codex_prompt_builder_compare\20260411-125807\combined_summary.json
3. latest copied compare summary
   - C:\tetie\notecode\research\新しいフォルダー (9)\04_compare_summary_20260411-125807.json

current evidence summary:
- baseline:
  - `human_visible_ai_feel = flat_or_repetitive`
  - `ending_bucket_max_run = 9`
  - `ending_bucket_monotony_score = 0.3333`
  - `flat_zone_count = 7`
  - `repair_applied = false`
  - `patch_path_used = false`
- latest compare 20260411-125807:
  - `ui-short-branding-company-grounded`
    - generic: `rubric_total = 8`, `soft_warning_count = 5`, `must_cover_reflection_rate = 0.6667`
    - algorithm: `rubric_total = 8`, `soft_warning_count = 3`, `must_cover_reflection_rate = 0.6667`
    - prompt-only: `rubric_total = 7`, `soft_warning_count = 4`, `must_cover_reflection_rate = 0.3333`
    - verdict: algorithm 勝ち
  - `ui-short-branding-trust`
    - prompt-only 勝ち
  - `ui-short-case-study-explain`
    - algorithm / prompt-only ほぼ並び

external research 4 本の practical consensus:
- `minimum hybrid keep` は条件付きで妥当
- `prompt-only` は比較対象として強いが、本番全面採用はまだ早い
- current problem の本質は
  - dense prompt
  - instruction competition
  - section role overlap
  - evaluation / repair trigger 感度不足
- preflight は必要だが、現状 diff は `まだほぼ何も削れていない` に近い
- source は raw dump へ戻さず compact facts を維持する
- ただし company-introduction だけ
  - heading ごとの `fact_anchor`
  - `do_not_mix`
  のような section-local grounding を最小限戻す案が有力
- 日本語のブロガーっぽさは prompt だけでなく `architecture + evaluation` で持つべき
- `explicit_subject_ratio` を上げる方向は悪手
- `heading_reanchor_miss_count` と section overlap を下げる方向が本質

今回の next owner:
- 第一候補:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- 第二候補:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - ただし repair trigger / acceptance を触るときだけ

next loop priority:
1. loop 1
   - owner: `prompt_builder.py`
   - objective:
     - company-introduction の preflight を本当に pruning として効かせる
     - `STRUCTURE` と writer brief の重複を削る
     - block budget を入れる
   - keep if:
     - `must_cover_reflection_rate` を落とさず
     - `company-grounded` の soft warnings と card 調が減る
2. loop 2
   - owner: `prompt_builder.py`
   - objective:
     - company-introduction に minimal な `fact_anchor / do_not_mix` を heading 単位で戻す
     - raw source は戻さない
   - keep if:
     - `fact_slot_coverage` か `example_specificity_count` に改善兆候
     - `section role overlap` が減る
3. loop 3
   - owner: `pipeline.py` か `quality_guard.py` ではなく、まず `pipeline.py` 周辺の narrow repair gate
   - objective:
     - soft warnings が一定以上なら narrow repair が本当に走るようにする
     - `repair_applied=false` のまま warning success を減らす
4. loop 4
   - owner: `prompt_builder.py`
   - objective:
     - `branding-trust` 用 brief を semantic-specific に分離する
     - prompt-only が勝っている理由を 1 行だけ取り込む

絶対ルール:
- `1 loop = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- current success path を壊さない
- completed / frozen / archive-only boundary を破らない
- prompt accretion 禁止
- module accretion 禁止
- same hypothesis unchanged retry は 3 回まで
- compare を回さないまま keep にしない
- experimental prompt stack と minimum hybrid を混在させない

3-way compare の固定対象:
- generic
- algorithm step-optimized
- prompt-only persona

prompt-only persona の固定方針:
- 日本語の note / ブログ記事を整える編集者
- 会社紹介・導入支援・事例記事を宣伝カード調に寄せすぎない
- 文末を揃えすぎない
- 段落の長さを揃えすぎない
- 必要なところだけ主語を置く
- 後半を言い換え反復にしない
- source にない実績や数値を足さない

今回の pass condition:
- target 2 cases で `algorithm` が `generic` より高品質
- target 2 cases で `algorithm` が `prompt-only` より高品質、または少なくとも business-ready / stable / grounded で優位と説明できる
- guard regression なし
- `company-grounded` で `flat_or_repetitive` の体感がさらに弱まる
- `must_cover_reflection_rate` と `source_trace_coverage` を崩さない

今回の strongest external recommendations:
- `preflight budget A/B`
- `section-local fact_anchor / do_not_mix A/B`
- `repair trigger threshold / narrow repair A/B`
- `trust` semantic 用の brief portability test

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q

開始時に必ず確認する code location:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - `_build_company_intro_writer_brief`
  - `_preflight_company_intro_generation_blocks`
  - `_build_company_intro_structure_lines`
  - generation の `SECTION_SHADOW` emit 条件
  - repair の company-intro narrow shadow guidance
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - company-intro prompt tests
  - company-intro repair prompt tests

開始アクション:
1. latest compare artifact `20260411-125807` を読む
2. external deep research 4 本の結論一致点をメモする
3. `prompt_builder.py` の current preflight が何を削れていないかを列挙する
4. 1 loop 分だけ pruning hypothesis を選ぶ
5. owner-local test
6. shared checks
7. live 3-way compare
8. keep / rollback / simplify を判定する

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 読んだ research handoff
- 各 loop の owner / hypothesis / diff / tests / live verdict
- `generic / algorithm / prompt-only` 比較
- keep した変更
- rollback した変更
- 減らした prompt / shadow / branch
- まだ残る AI-like symptom
- `minimum hybrid keep` を継続するか
- `prompt-only より高品質` に到達したか
- AGENTS / WORKLOG 更新の有無
```
