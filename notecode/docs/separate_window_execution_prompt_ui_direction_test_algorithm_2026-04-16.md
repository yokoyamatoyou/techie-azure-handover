# separate window execution prompt ui direction test algorithm 2026-04-16

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\docs\ui_role_clarity_record_2026-04-08.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_test_algorithm_by_ui_direction_2026-04-16.md

今回の実施範囲:
- separate experimental line として、UI direction aware Japanese test algorithm を narrow に実装する
- current mainline source-of-truth は上書きしない
- AGENTS / WORKLOG / current package docs は更新しない
- fixed routing table を作らない
- prompt-only winner を前提にしない
- `single-pass + optional single repair 1回` を壊さない

目的:
- UI 上のブログ記事の方向性差を、日本語向けの `reference realization policy` と `AI-feel suppression` で narrow に試す
- 特に `会社名 / 私たち / 当社 / 主語省略` の使い分けと、AIっぽい抽象表現の抑制を test する

前提:
- current keep-state:
  - grounded generic default
  - planning opt-in only
  - company intro current-business-first keep line
- do-not-retry:
  - fixed article-type routing table
  - formatter-only polish
  - input-contract-only distilled summary line
  - first section history clamp
  - ambiguous role labels such as `運営側`

今回の first owner:
- C:\tetie\notecode\note\natural_blog_core.py

first hypothesis:
- section-level `speaker_reference_policy` / `subject_reintroduction_policy` / `proper_noun_repeat_cap` を `trust_intro` と `explain_analysis` に追加すると、会社名反復と主語露出過多が減り、日本語 blog-like naturalness が上がる

実装ルール:
1. first owner は 1 file に閉じる
2. まず owner-local tests を追加する
3. 次に実装する
4. shared checks は current package の定義を尊重する
5. 3回失敗したら rollback して停止し、user report

実装で入れてよいもの:
- section plan への lightweight policy field 追加
- prompt builder で消費可能な bounded hint
- lightweight telemetry

実装で入れてはいけないもの:
- article type ごとの hard-coded route table
- hidden reviser の追加
- formatter による後処理依存
- prompt の長文化
- announcement への横展開

最終報告で必ず示すこと:
1. 触った owner files
2. 追加した policy fields
3. どの UI direction family を今回対象にしたか
4. どの failure memory を避けたか
5. owner-local tests
6. shared checks
7. compare した article cases
8. visible improvement / no-improvement
9. rollback 要否
10. current source-of-truth を更新しなかったこと
```
