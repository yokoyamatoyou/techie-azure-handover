# separate window execution prompt compare reference realization policy 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_test_algorithm_by_ui_direction_2026-04-16.md
- C:\tetie\notecode\docs\separate_window_compare_plan_reference_realization_policy_2026-04-17.md

今回の実施範囲:
- compare を実行する
- current production runtime は変更しない
- AGENTS / WORKLOG / current package docs は更新しない
- current source-of-truth は上書きしない
- compare 実行中に production code を編集しない

目的:
- `reference realization policy` line が visible text に効くかを fixed cases で比較する
- production owner を次に開く価値があるか、`GO / NO_GO` を判断する

絶対条件:
- runtime code edit 禁止
- `note\simple_note_pipeline\*.py`
- `note\newalgorithm_pipeline\*.py`
- `note\natural_blog_core.py`
- `note\current_mainline_runner.py`
- `note_writer_app.py`
  を編集しない
- compare 中に fixed routing table を増やさない
- prompt accretion でその場しのぎしない
- mock path / pure output guard の pass を勝敗条件に使わない

compare lanes:
- lane A:
  - current keep-state baseline
  - production path unchanged
- lane B:
  - separate experimental line
  - `natural_blog_core.py` の section-level `reference realization policy` を含む state
- lane C:
  - optional fallback reference only
  - `prompt-only floor`
  - winner 判定には使わず、B の悪化確認だけに使う

fixed case list:
1. `ui-short-branding-company-grounded`
2. `ui-short-branding-trust`
3. `bl-explanatory-misread-metric`
4. `bl-daily-learning-log-grounded`

case role:
- 1, 2:
  - main target
- 3:
  - main target with `no-first-person` guard
- 4:
  - regression guard only

repeat rule:
- 1 case あたり `3 repeats`
- `single best run` ではなく `median` と `2/3 repeat consistency` で判定する

保存するもの:
- 各 run の full text
- short memo
  - company name repetition
  - pronoun / omission distribution
  - subject reintroduction timing
  - abstraction feel
  - paragraph breath
  - article integrity
- supporting metrics
  - `explicit_subject_ratio`
  - `ending_bucket_max_run`
  - `abstract_term_density`
  - `paragraph_length_cv`
  - company-name / proper-noun repeat count

rubric:
- `C:\tetie\notecode\docs\separate_window_compare_plan_reference_realization_policy_2026-04-17.md`
  の 6項目 `0 / 1 / 2` を使う

judge rule:
- `GO`
  - `company_introduction` と `branding` の median rubric が lane A より `+2` 以上
  - 2 case とも `2/3 repeats` 以上で visible improvement
  - `explanatory_article` は lane A 以上で、一人称悪化なし
  - `daily_story` は regression なし
- `NO_GO`
  - いずれかの main target で company name / `株式会社` の前景反復が残る
  - `explanatory_article` が硬直した説明カード調に寄る
  - `daily_story` が dry / corporate / explanatory に寄る
  - gain が単発 run 依存
  - route / formatter / fixed rule / prompt accretion が欲しくなる

今回作ってよいもの:
- compare result doc
- compare summary doc
- run manifest
- short human evaluation memo

推奨出力ファイル:
- `C:\tetie\notecode\docs\separate_window_compare_result_reference_realization_policy_2026-04-17.md`

停止条件:
- compare 実行に production code edit が必要になった
- lane 定義が崩れた
- same case / same source / same role の固定を守れなくなった
- visible judgment ではなく metrics の数値合わせに流れ始めた

最終報告で必ず示すこと:
1. 実行した lanes
2. compare case list
3. run count
4. rubric summary
5. company / branding の visible improvement 有無
6. explanatory の no-first-person guard 結果
7. daily の regression 有無
8. `GO` か `NO_GO` か
9. next production owner を開くべきか
10. 日本語ブログ runtime を変更していないこと
11. AGENTS / WORKLOG 更新不要であること
```
