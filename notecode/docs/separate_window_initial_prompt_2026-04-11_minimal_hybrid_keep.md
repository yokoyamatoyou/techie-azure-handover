# separate window initial prompt 2026-04-11 minimal hybrid keep

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
- C:\tetie\notecode\docs\separate_window_initial_prompt_2026-04-11_prompt_only_compare5.md
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

今回の mission:
- `best practice = minimal hybrid keep` を前提に、`prompt-only より高品質な algorithm` を目標に続行する
- `branding / company_introduction` の visible AI feel をさらに下げる
- `prompt-only` に寄せる方向で simplification を続けるが、full prompt-only へはまだ切らない
- `speaker / audience / must_cover / source grounding` の visible retention は保つ
- prompt accretion ではなく prompt simplification で進める

現在の判断:
- keep decision:
  - `minimal hybrid keep`
- まだ final close しない理由:
  - `company-grounded` は改善したが `flat_or_repetitive` が残る
  - `prompt-only` は比較対象として有効だが、安定して business-ready 勝ちとはまだ言えない
  - current best direction は `algorithm を prompt-only に近づける simplification`

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の keep diff:
- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- keep 1:
  - company-introduction generation では `SECTION_SHADOW` を出さない
  - semantic ledger と evidence は keep
- keep 2:
  - company-introduction repair では `SECTION_SHADOW` を narrow guidance として keep
  - target heading の support / fact だけを戻す
- keep 3:
  - branding の instruction-heavy long prompt は `topic=` に丸ごと残さず compact 化する

今回読んで比較すべき artifact:
1. production-like baseline
   - C:\tetie\notecode\logs\latest_generation_output.txt
   - C:\tetie\notecode\logs\latest_generation_output.json
   - C:\tetie\notecode\logs\latest_generation_quality_report.json
   - attempt id `gen-f914d30e`
2. prior prompt-only compare
   - C:\tetie\notecode\logs\codex_prompt_only_compare5\20260411-112803\summary.json
3. current compare loop A
   - C:\tetie\notecode\logs\codex_prompt_builder_compare\20260411-115155\combined_summary.json
4. current compare loop B
   - C:\tetie\notecode\logs\codex_prompt_builder_compare\20260411-115900\combined_summary.json

current evidence summary:
- loop A:
  - `company-grounded`
    - generic 勝ち
    - algorithm は `rubric_total = 7`
    - `must_cover_reflection_rate = 0.3333`
  - `trust`
    - algorithm 勝ち
  - `guard`
    - algorithm 勝ち
- loop B:
  - `company-grounded`
    - algorithm 勝ち
    - `rubric_total = 8`
    - `must_cover_reflection_rate = 0.6667`
    - `prompt_anchor_coverage = 0.1667`
    - `source_trace_coverage = 1.0`
  - `trust`
    - prompt-only 勝ち
  - `guard`
    - prompt-only 勝ち
  - prompt-only `company-grounded` は `TRN_PRIMARY_MODEL_UPSTREAM_5XX` で失敗しているため、content superiority の根拠には使わない

現在の practical interpretation:
- company-introduction の primary blockage は prompt density と instruction competition がまだ強いこと
- `SECTION_SHADOW` を generation から抜いたのは keep
- 次に削るべき候補は `STYLE` と `STRUCTURE` 内の company-intro 専用重複
- `algorithm` が target A で持ち直したのは、topic compaction により long prompt が `topic=` を汚しにくくなったためと説明できる
- したがって next owner も `prompt_builder.py` のままでよい

今回の next owner:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`

next loop priority:
1. loop 1
   - owner: `prompt_builder.py`
   - objective:
     - company-introduction の `STYLE` と `STRUCTURE` の重複をさらに減らす
     - must_cover / semantic ledger / evidence と意味が重なる補助文を削る
   - target:
     - `ui-short-branding-company-grounded`
   - keep if:
     - `must_cover_reflection_rate` を落とさず
     - `company card` 調や説明カード調が減る
2. loop 2
   - owner: `prompt_builder.py`
   - objective:
     - `trust` 側で still useful な guidance と `company-intro` でノイズになる guidance を分ける
     - branding generic guidance を semantic key ごとにさらに分離する
3. loop 3
   - owner: `prompt_builder.py`
   - objective:
     - repair prompt 側で company-intro narrow guidance をさらに短くできるか確認する
     - `shadow_section_drift` の patch scope と duplicate instruction を縮める
4. loop 4+
   - only if still blocked
   - `input_contract.py` ではなく `prompt_builder.py` のまま進める根拠がなくなった場合だけ owner 再検討

絶対ルール:
- `1 loop = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- current success path を壊さない
- completed / frozen / archive-only boundary を破らない
- prompt accretion 禁止
- module accretion 禁止
- same hypothesis unchanged retry は 3 回まで
- compare を回さないまま keep にしない

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

今回の goal wording:
- 単に `prompt-only と同等` ではなく
- `prompt-only より高品質`
- ただし upstream 5xx や runtime failure は content superiority の根拠に使わない

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q

開始時に必ず確認するコード location:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - `_compact_topic_for_prompt`
  - `_build_company_intro_structure_lines`
  - generation の `SECTION_SHADOW` emit 条件
  - repair の company-intro narrow shadow guidance
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - company-intro prompt tests
  - company-intro repair prompt tests

開始アクション:
1. latest compare artifacts 2 本を読む
2. `company-grounded` の generic / algorithm / prompt-only 本文を再読する
3. `prompt_builder.py` の company-intro `STYLE` / `STRUCTURE` 重複候補を 1 loop 分だけ選ぶ
4. owner-local test
5. shared checks
6. live 3-way compare
7. keep / rollback / simplify を判定する

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 読んだ compare artifact
- 各 loop の owner / hypothesis / diff / tests / live verdict
- `generic / algorithm / prompt-only` 比較
- keep した変更
- rollback した変更
- 減らした prompt / shadow / branch
- まだ残る AI-like symptom
- `minimal hybrid keep` を継続するか
- `prompt-only より高品質` に到達したか
- AGENTS / WORKLOG 更新の有無
```
