# ux_commercial_readiness_2026-04-05

`aio2-main` の分析後 UI を、`情報設計は成立しているが commercial polish が未完` の状態から、  
**Codex が phase 単位で自律実行し、自己テスト完了後に次 phase へ進める** 実行パッケージ。

この package は単なる TODO 集ではなく、次を current source of truth にする。

- phase map
- owner scope
- self-test gate
- retry / stop rule
- web search retry rule
- progress ledger
- restart prompt

## Objective

- `aio2-main` の post-analysis UI を商用公開前提の polish 段階まで押し上げる
- Nielsen / Hick-Hyman / Shneiderman / Google 系 design guidance と矛盾しない IA と視覚階層へ整える
- Codex が別ウィンドウ / 別日再開でも迷わず進められる進捗管理を固定する
- phase ごとに自己テストし、green gate のみ次 phase へ進める運用を明文化する

## Package Role

- `README.md`
  - package の目的、read order、baseline findings、phase summary を定義する
- `TASK.md`
  - phase / gate / retry / stop / self-test / web search retry rule を固定する
- `PROGRESS.md`
  - current phase、attempt、evidence、phase ledger、failure log を管理する
- `ROLLBACK.md`
  - rollback boundary、do-not-retry、stop condition を固定する
- `EXECUTION_PROMPT.md`
  - 次回再開時にそのまま貼れる開始 prompt を保持する
- `artifacts\`
  - baseline / phase screenshot / verify memo の置き場

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\ALGORITHM.md`
4. `C:\tetie\aio2-main\WORKLOG.md`
5. `C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\README.md`
6. `C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\TASK.md`
7. `C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\PROGRESS.md`
8. `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\README.md`
9. `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\TASK.md`
10. `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\PROGRESS.md`
11. `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\ROLLBACK.md`
12. `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\EXECUTION_PROMPT.md`

## Current Baseline

2026-04-05 時点の current code 状態:

- 5 タブ IA は実装済み
  - `サマリー / やること / 文章改善 / 実装・設定 / 履歴と比較`
- live / saved は同じ workspace renderer を使う
- FAQ fallback は URL context ベースに改善済み
- `実装・設定` の raw value 露出は一部抑制済み
- targeted regression は pass

ただし commercial readiness 観点では次が残っている。

1. hero / top copy と actual IA の整合が未完
   - 画面導線に旧 `現状 / 改善方法 / 詳細` の copy が残る箇所がある
2. first screen の hierarchy がまだ card 密度寄り
   - 初見で `結論 -> 重要件数 -> Top3` がさらに速く読める余地がある
3. `実装・設定` は pass noise を抑えたが、判断面としての圧縮はまだ改善余地あり
4. accessibility / mobile / keyboard / contrast の明示的 gate が package 化されていない
5. Codex 自律実行の restart / phase ledger / failure handling package がまだない

## Scope

この package が扱うのは次だけ。

- `nicegui_app.py` の hero / guide / shell copy / CSS / layout polish
- `core/ui/panels.py` の workspace hierarchy / disclosure / wording polish
- `core/ui/dashboard.py` の dashboard density / mobile readability polish
- 必要最小限の UI helper test 追加
- progress / execution docs

この package が扱わないもの:

- 分析ロジック変更
- score formula 変更
- legal meaning 変更
- provider 判定意味変更
- `zip` 配下 mock 変更
- unrelated refactor

## Design Constraints

- analysis logic / score meaning / legal meaning は変えない
- IA は 5 タブを維持する
- FAQ は消さず、位置と personalization を維持する
- `llms.txt` を hard requirement に戻さない
- `Google-Extended` / `GPTBot` / `ClaudeBot` / `CCBot` は informational を維持する
- live / saved parity を崩さない

## Success Criteria

- entry copy と actual IA が一致している
- first view 30 秒で `結論 / 要対応件数 / Top3` が分かる
- `実装・設定` は warn/fail 中心で読め、pass noise が主画面を汚さない
- keyboard / contrast / mobile / empty state の明示 gate が pass
- `PROGRESS.md` の current phase と phase ledger が再開時の唯一の運用基準として機能する

## Phase Summary

| Phase | Name | Goal |
|------|------|------|
| 0 | package bootstrap | docs / baseline / verify contract を固定する |
| 1 | UX criteria lock | 評価基準、対象 screen、商用判定基準を固定する |
| 2 | IA copy alignment | entry copy と actual UI を一致させる |
| 3 | summary/task hierarchy | first screen の hierarchy を強化する |
| 4 | implementation compression | `実装・設定` を判断面として圧縮する |
| 5 | FAQ rationale polish | FAQ の personalized rationale を見やすくする |
| 6 | dashboard density/mobile | dashboard / mobile の密度を再調整する |
| 7 | accessibility/live verify | keyboard / contrast / zoom / mobile を確認する |
| 8 | commercial review closeout | residual / stop condition / next risks を最終整理する |

## Operating Rule

- Codex は 1 回に 1 phase だけ進める
- 各 phase で自己テスト -> `PROGRESS.md` 更新 -> gate green -> 次 phase へ自動 advance
- phase 内で bug / error が出た場合、**ローカル修正を優先**
- それで解けない場合のみ **Web 検索を最大 3 回まで** 実施して修正を試す
- 3 回でも解けなければ停止し、`PROGRESS.md` の failure log と user report を更新する
