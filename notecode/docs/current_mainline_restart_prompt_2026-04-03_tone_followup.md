# current mainline restart prompt

更新日: 2026-04-03  
用途: コトメイク current mainline の wizard 必須項目移動と tone tuning の続きから安全に再開するための prompt

## copy-paste prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\README.md
- C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\TASK.md
- C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md
- C:\tetie\notecode\docs\current_mainline_restart_prompt_2026-04-03_tone_followup.md

今回の実施範囲:
- コトメイク current mainline の post-package tuning を続ける
- current success path を壊さない
- 直近で実施済みの wizard 必須項目移動は keep する
- 直近で実施済みの tone tuning は keep しつつ、必要なら本文中盤の温度感差をさらに広げる
- 対象は current mainline のみ
- kotomegane は今回のスコープ外

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\README.md
4. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\TASK.md
5. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md
6. C:\tetie\notecode\ALGORITHM.md
7. C:\tetie\WORKLOG.md
8. C:\tetie\notecode\docs\current_mainline_restart_prompt_2026-04-03_tone_followup.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\WORKLOG.md
5. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md
6. C:\tetie\notecode\docs\current_mainline_restart_prompt_2026-04-03_tone_followup.md

開始時に必ず読む直近 artifact:
1. C:\tetie\notecode\logs\tone_probe_live_2026-04-03_round6.json
2. C:\tetie\notecode\logs\tone_probe_live_2026-04-03_round5.json
3. C:\tetie\notecode\logs\tone_probe_live_2026-04-03_round4.json

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回 keep する変更:
- C:\tetie\notecode\note\note_writer_app.py
  - journey wizard の STEP 4 に生成必須項目を移動済み
  - moved fields:
    - 記事の目的
    - 話者
    - 主な読者
    - 語り口
    - 核メッセージ
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - tone_profile の指示を summary 1行から複数行へ拡張済み
  - title / lead 用の tone guidance を追加済み
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - explanatory_article の title / lead shaping を追加済み
- C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
  - live current mainline 経路でも final title / final lead に tone shaping が効くように追加済み
- C:\tetie\notecode\note\newalgorithm_pipeline\editor_guard.py
  - conditional clause (`〜いれば。`) を next sentence と join できるように追加済み
- tests:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py

直近の確認結果:
- 2026-04-03 の最終 live rerun は:
  - C:\tetie\notecode\logs\tone_probe_live_2026-04-03_round6.json
- 同一入力 / 3 conditions:
  - warm
  - calm
  - formal
- result:
  - 3/3 success
  - sentence_integrity_warning_count = 0 for all
  - title / lead の温度感差は live 経路でも visible
- latest visible difference:
  - warm title:
    - 「機能比較の前に、運用定着の見方をそろえて迷いを減らす実務の見方」
  - calm title:
    - 「機能比較の前に、運用定着の見方をそろえるべき理由から考える実務の見方」
  - formal title:
    - 「機能比較の前に、運用定着の見方をそろえる判断軸を整理する」
  - warm lead:
    - 「導入前は、何から見ればよいか迷いやすいものです。...」
  - calm lead:
    - 「機能比較へ進む前に、前提と判断軸をそろえておく必要があります。...」
  - formal lead:
    - 「本稿では、比較に先立って確認すべき前提と判断軸を整理します。...」

直近で通っている targeted checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "tone or style or shapes_explanatory_opening_by_tone_profile" -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st16a_explanatory_formatter_shapes_opening_by_tone_profile or st05ag2" -q

再開時の最初の手順:
1. 参照ルールファイルと本 prompt を読む
2. `tone_probe_live_2026-04-03_round6.json` を確認して latest state を把握する
3. 以下の targeted checks を再実行して green を確認する
   - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "tone or style or shapes_explanatory_opening_by_tone_profile" -q
   - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st16a_explanatory_formatter_shapes_opening_by_tone_profile or st05ag2" -q
4. その後、必要なら同一入力で `warm/calm/formal` の live 3-run を 1 回だけ再確認する

次の narrow slice 候補:
- 第一候補:
  - owner = C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - scope = 本文中盤の温度感差を広げる
  - goal = title / lead だけでなく section body の sentence rhythm / assertion strength / empathy distance に差を増やす
- 第二候補:
  - owner = C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
  - scope = explanatory_article 以外への tone shaping 適用可否を narrow に検討する
  - goal = branding / case_study / industry_analysis へ安易に横展開せず、必要性がある genre だけに限定適用する

do-not:
- current success path を崩さない
- compare stabilization package の completed state を reopen しない
- human_resonance* を触らない
- いきなり全 genre sweep を回さない
- wizard 周りを再度広範囲に組み替えない
- lead/title shaping を broad な文言置換で他 genre へ横展開しない
- output formatter の表層 tweak だけで押し切らない

再開時に user へ最初に報告すること:
- 読んだ正本ファイル
- 今回の実施範囲
- latest artifact path
- keep する変更
- 次に触る owner scope

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- keep した変更
- 実行した test / artifact path
- visible residual
- rollback の有無
- AGENTS / WORKLOG 更新の有無
```
