# current mainline tomorrow first prompt

更新日: 2026-04-02  
用途: 次回セッションで `branding + product_introduction` の blank-topic residual を kept state から安全に再開するための prompt

## copy-paste prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\GPTPRO.txt
- C:\tetie\notecode\research\新しいフォルダー\GPTPRO.txt
- C:\tetie\notecode\research\新しいフォルダー\Claude.txt
- C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-03.md

今回の実施範囲:
- `branding + product_introduction` の blank-topic residual だけを続ける
- current success path を維持する
- prompt accretion と module accretion を禁止する
- DeepResearch の再実施から始めない
- `quality_guard` や `input_decision` を初手で触らない
- まず source grounding / discourse section assignment 側の 1 owner に絞る

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-03.md
5. C:\tetie\notecode\GPTPRO.txt
6. C:\tetie\notecode\research\新しいフォルダー\GPTPRO.txt

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\WORKLOG.md
5. C:\tetie\notecode\GPTPRO.txt
6. C:\tetie\notecode\research\新しいフォルダー\GPTPRO.txt
7. C:\tetie\notecode\research\新しいフォルダー\Claude.txt
8. C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-03.md

開始時に必ず読む artifact:
1. C:\tetie\notecode\logs\latest_generation_output.json
2. C:\tetie\notecode\logs\latest_generation_quality_report.json
3. C:\tetie\notecode\logs\current_mainline_ui_runs\manual_blank_topic_check_2026-04-02\manual-blank-topic-product-intro.json
4. C:\tetie\notecode\logs\current_mainline_ui_runs\manual_blank_topic_check_2026-04-02\manual-blank-topic-product-intro.txt
5. C:\tetie\notecode\logs\current_mainline_ui_runs\manual_blank_topic_check_2026-04-02_rerun2\manual-blank-topic-product-intro-rerun2.json
6. C:\tetie\notecode\logs\current_mainline_ui_runs\manual_blank_topic_check_2026-04-02_rerun2\manual-blank-topic-product-intro-rerun2.txt
7. C:\tetie\notecode\logs\current_mainline_ui_runs\manual_blank_topic_check_2026-04-02_rerun4\manual-blank-topic-product-intro-rerun4.json
8. C:\tetie\notecode\logs\current_mainline_ui_runs\manual_blank_topic_check_2026-04-02_rerun4\manual-blank-topic-product-intro-rerun4.txt

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今日 keep した修正:
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - blank-topic の `product_introduction` で `topic_statement` を `core_message` から rescue
  - `must_cover` へ main focus を再注入しない
  - `focus_bundle.support_points=[]`
  - `focus_bundle.goal_bias=balanced`
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - generation prompt の topic fallback を `topic -> prompt_raw -> topic_statement -> core_message` に変更済み
- C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py
  - `product_introduction` で first hook section の objective/topic_seed へ main focus を直挿ししない

今日の確認結果:
- 空 topic のまま company facts に流れる一次不具合は解消済み
- live rerun-4 でも `topic_statement` は立つ
- live rerun-4 でも `must_cover=["誰のどんな課題に合うか", "選ぶ判断材料", "導入時の注意点"]` まで改善済み
- ただし residual は残る
  - `topic_echo_body_only_ratio=0.5`
  - rubric=7
  - long_form_case_gate=false
- 現在の visible residual は:
  - lead / body の論点配置がまだ source facts 寄り
  - 「DX化の最初はデジタルデータ」が hook と body の一部でまだ直言される
  - `product_introduction` なのに company-history facts の配り方が強い

現時点の判断:
- `quality_guard` はまだ一次 owner ではない
- `need_question.ask=true` と `input_decision=accept` のねじれは残るが、まだ初手ではない
- 次 owner は `source grounding / discourse section assignment`
- とくに `product_introduction` で source fact bucket の配布が company-intro 寄りになっていないかを最初に見る

次にやること:
1. rerun-4 artifact の `discourse_plan` と `source_grounding_items` の section 配布を確認する
2. `product_introduction` で history/overview fact が hook/value/decision にどう割り当たっているかを切る
3. narrow hypothesis を 1 つだけ決める
4. owner は 1 file に固定する
5. owner-local tests
6. blank-topic rerun を 1 回
7. 改善したら同ケースをもう 1 回 rerun
8. 効かなければ rollback して stop

第一候補の narrow slice:
- owner = C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py
- `product_introduction` で history/overview source fact を hook/value/decision へそのまま強配布しない
- hook は課題/用途の切り口を優先し、company history は closing 側か非優先に寄せる

第二候補:
- owner = C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- source grounding の section assignment で `product_introduction` 専用の preferred bucket order を narrow に変える

do-not:
- DeepResearch を追加しない
- `quality_guard.py` を初手で触らない
- `input_decision` のロジック修正から始めない
- prompt を長文化して押し切らない
- new module / new class を足さない
- `human_resonance*` を触らない
- unrelated genre に広げない

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- keep した修正
- 実行した artifact path
- visible residual
- rollback の有無
- 次の narrow slice
- AGENTS / WORKLOG 更新の有無
```
