# separate window execution prompt nonintrusive next step 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_execution_prompt_ui_direction_test_algorithm_2026-04-16.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_pure_output_guard_triage_2026-04-16.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_mock_path_alignment_2026-04-16.md

今回の実施範囲:
- separate window で next step を進める
- 日本語ブログの current runtime / visible behavior は変更しない
- current source-of-truth は上書きしない
- AGENTS / WORKLOG / current package docs は更新しない
- production path の code edit はしない

前提:
- `natural_blog_core.py` line の narrow 実装は完了している
- `pure output guard` failure は test double 側の stale mock / stale expectation に閉じた
- production path は未変更のまま保たれている
- ここで日本語ブログ runtime を触るのは scope 外

目的:
- 次に production 実装へ進むかどうかを、evidence で判断する
- 実装ではなく compare / inspection / report を行う
- `reference realization policy` line を本当に次の owner に進める価値があるか確認する

絶対条件:
- 日本語ブログは変更なし
- `note\simple_note_pipeline\*.py`
- `note\newalgorithm_pipeline\*.py`
- `note\natural_blog_core.py`
- `note\current_mainline_runner.py`
  を編集しない
- formatter / input_contract / route default / output_guard threshold を触らない

今回やること:
1. current keep-state と separate experimental line の結果を読む
2. `reference realization policy` line が production 実装に進む価値を、compare 設計で判定する
3. compare plan だけを作る
4. 必要なら compare 用の case list / rubric / execution note を docs に新規追加する

今回やってよい変更:
- `C:\tetie\notecode\docs\` 配下の new note / compare plan / execution note の追加
- compare 対象 case の整理
- rubric の整理
- stop / go judgment の文章化

今回やってはいけない変更:
- 日本語ブログ runtime の code change
- current mainline tests を通すための production prompt change
- article-type fixed routing table の追加
- prompt-only winner の断定
- `planning default` の再主張
- hidden reviser accretion

検討対象:
- `company_introduction`
- `branding`
- `explanatory_article`
- `daily_story`

compare で見る観点:
- 会社名や `株式会社` の前景反復が減るか
- `私たち / 当社 / 省略` の配分が自然か
- 主語を毎文言い直していないか
- AI 的な抽象まとめが減るか
- 段落の呼吸が平坦でないか
- explanatory で一人称が不必要に出ないか
- daily へ横展開すべきでない理由が残っていないか

期待する成果物:
- compare 実施前の短い execution note 1本
- compare case list
- human check rubric
- go / no-go judgment rule

推奨ファイル:
- `C:\tetie\notecode\docs\separate_window_compare_plan_reference_realization_policy_2026-04-17.md`

停止条件:
- production code を触らないと compare 設計が作れない
- current source-of-truth を更新したくなった
- article-type fixed rule を作らないと評価できなくなった
- same idea の再記述だけで前進がない

最終報告で必ず示すこと:
1. 読んだ source-of-truth
2. 日本語ブログ runtime を変更していないこと
3. 追加した docs
4. compare case list
5. rubric
6. go / no-go judgment
7. 次に production owner を開くべきかどうか
8. AGENTS / WORKLOG 更新不要であること
```
