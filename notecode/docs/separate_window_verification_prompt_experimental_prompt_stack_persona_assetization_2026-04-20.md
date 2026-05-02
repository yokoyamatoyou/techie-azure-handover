# separate window verification prompt experimental prompt stack persona assetization 2026-04-20

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- verification window first prompt
- `EXPERIMENTAL_PROMPT_STACK_PERSONA_ASSETIZATION_CHECK`
- implementation prompt ではない
- broad rewrite prompt ではない

今回の目的:
- `experimental_prompt_stack` の persona 文面 asset 化後も、`support -> planner -> writer -> editor -> audit` の live behavior が変わっていないかを確認する
- `announcement / daily_story / branding` で、内容に応じた自然さが崩れていないかを比較確認する
- 過去ログを比較材料として使い、今回の変更が prompt wording の配置替えに留まり、挙動変更を混入させていないかを確認する

current fixed judgment:
- 今回の scope は persona 文面の asset 化のみ
- orchestration / parse / telemetry / gate 判定は code に残す
- 旧アルゴリズムや hierarchical route の断片を新アルゴリズムへ混入させない
- `support lenient parse`、`suffix-only editor`、`audit visibility` を壊さない
- broad rewrite はしない

今回の変更対象ファイル:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\prompt_loader.py
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\prompt_renderer.py
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\personas\common_kernel.md
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\personas\support.md
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\personas\planner.md
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\personas\writer.md
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\personas\editor.md
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\personas\audit.md
- C:\tetie\notecode\note\simple_note_pipeline\experimental_prompt_stack\personas\legal.md

この window の実施範囲:
1. 既存 pytest を回して、`experimental_prompt_stack` の sequence / fallback / parse recovery が壊れていないかを確認する
2. カテゴリ別に visible output を読み、`announcement / daily_story / branding` の自然さを確認する
3. 過去ログから baseline artifact を拾い、今回の出力と比較する
4. persona asset 化のついでに behavior change が紛れ込んでいないかを contamination check する
5. 必要なら docs-only の検証メモを 1 本だけ作る

この window でやらないこと:
- production code edit
- test edit
- prompt wording の追加強化
- stage 追加
- old algorithm / hierarchical route の再導入
- `default flip`
- `st08b4` 修正
- UI 接続作業

推奨の実行順:
1. まず pytest を回す
   - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
2. 必要なら narrow 再確認を回す
   - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py::test_simple_note_pipeline_experimental_prompt_stack_runs_support_planner_writer_editor_sequence note\tests\test_simple_note_pipeline.py::test_simple_note_pipeline_experimental_prompt_stack_falls_back_to_regular_generation_when_support_parse_fails -q
3. 過去ログ baseline を読む
4. 現在の visible output と見比べる
5. contamination check をして最終報告する

過去ログ baseline の第一候補:
- C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\summary.json
  - category baseline の第一候補
  - `genre_summary` に `announcement / branding / daily_story` の pass 数と rubric 平均がある
  - `results[*].artifact_text_path` で本文比較ができる
  - `results[*].artifact_path` で quality / contract / source 周辺を確認できる
  - `casebook_path`:
    - C:\tetie\notecode\note\tests\fixtures\current_mainline_genre_sweep_casebook_2026-03-30.json

baseline の読み方:
- `announcement`
  - pass_count = 2 / 5
  - rubric_mean_total = 5.8
- `branding`
  - pass_count = 4 / 5
  - rubric_mean_total = 7.0
- `daily_story`
  - pass_count = 5 / 5
  - rubric_mean_total = 7.0

補助比較ログ:
- C:\tetie\notecode\logs\latest_generation_output.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- C:\tetie\notecode\logs\experimental_prompt_stack_promotion_evidence_20260420-091225\historical_compare_summary.json
  - compare-ready / compare-ineligible の区別が入っている
  - input-contract block と content output を取り違えないための補助に使う

比較時の重点観点:

1. support
- parse failure 時に recent recovery が壊れていないか
- lenient parse が厳格化されていないか

2. planner
- planner-centered rigid skeleton に戻っていないか
- stage sequence が変わっていないか

3. writer
- article type ごとの差分 prompt が消えていないか
- `announcement / daily_story / branding` で不自然な tone convergence が起きていないか

4. editor
- suffix-only が維持されているか
- full-article rewrite に戻っていないか
- `KEEP_PREFIX / EDIT_TARGET_SUFFIX` の意味が visible output 上で壊れていないか

5. audit
- visibility summary が維持されているか
- fallback を success 扱いする drift がないか

自然さの確認観点:
- `announcement`
  - お知らせとして先に知りたい変更点や対象がわかるか
  - 不要に感情的、抽象的、宣伝調に寄っていないか
- `daily_story`
  - 日々のできごととして小さな変化や実感が自然につながるか
  - 成功談テンプレや教訓テンプレに寄りすぎていないか
- `branding`
  - 会社紹介や考え方の文脈で、説明と温度感のバランスが保たれているか
  - 断定しすぎる宣伝文や硬直した理念文に戻っていないか

比較の進め方:
1. `phase06_surface_realization_card_eval\summary.json` から同カテゴリの artifact を 2 から 3 件拾う
2. `artifact_text_path` を読み、カテゴリごとの自然さの baseline を確認する
3. 今回の run の visible output を同カテゴリで読む
4. 差分を
   - 改善
   - 同等
   - 悪化
   の 3 段で判定する
5. 判定理由は本文表現ベースで短く書く

contamination check:
- old algorithm の route 文面を新 asset に入れていないか
- planner-centered rigid section skeleton に戻していないか
- full-article rewrite を editor に戻していないか
- fallback を success と見なす変更をしていないか
- persona asset 化のついでに behavior change を紛れ込ませていないか

stop conditions:
- pytest が 3 回修正しても戻らない
- asset 化確認なのに orchestration の意味変更が必要に見え始める
- old/shared 側まで触らないと検証不能になる
- `support / editor / audit` の recent recovery が壊れている
- 比較対象が noisy log に流れ、本文比較ができなくなる

必要なら作成してよい file:
- C:\tetie\notecode\docs\experimental_prompt_stack_persona_assetization_verification_note_2026-04-20.md

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実行した pytest
3. 比較に使った過去ログ / artifact
4. `announcement / daily_story / branding` ごとの自然さ判定
5. 挙動変更の有無
6. contamination check 結果
7. production code / tests / AGENTS / WORKLOG を更新していないこと
```
