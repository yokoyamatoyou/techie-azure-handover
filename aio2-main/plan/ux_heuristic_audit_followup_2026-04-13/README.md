# ux_heuristic_audit_followup_2026-04-13

`aio2-main` の UI を、2026-04-13 の UX / マーケティング監査結果に基づいて
**別ウインドウの Codex が phase 単位で自律実行できる形に固定する** 実行パッケージ。

この package は単なる TODO 集ではなく、次を current source of truth にする。

- 監査 finding と owner scope の対応
- phase map
- self-test gate
- retry / stop rule
- rollback boundary
- restart prompt

## Objective

- Nielsen の 10 原則、Hick の法則、実務マーケティング観点で指摘された UI 課題を、実装可能な phase に落とす
- 別ウインドウの Codex が `どこから直すか` で迷わない状態にする
- `analysis logic / score meaning / legal meaning` を変えずに、入力体験と結果閲覧体験の主導権・判断速度・価値訴求を改善する
- phase ごとの自己テストと進捗管理を固定し、途中停止時も再開しやすくする

## Package Role

- `README.md`
  - package の目的、read order、findings、phase summary、success criteria を定義する
- `TASK.md`
  - phase / gate / retry / stop / self-test を固定する
- `PROGRESS.md`
  - current phase、phase ledger、evidence、failure log を管理する
- `ROLLBACK.md`
  - rollback boundary、do-not-change、stop condition を固定する
- `EXECUTION_PROMPT.md`
  - 別ウインドウ開始時にそのまま貼れる開始 prompt を保持する
- `artifacts\`
  - baseline memo / screenshot / verify note の置き場

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\ALGORITHM.md`
4. `C:\tetie\aio2-main\WORKLOG.md`
5. `C:\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md`
6. `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\README.md`
7. `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\TASK.md`
8. `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\PROGRESS.md`
9. `C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\README.md`
10. `C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\TASK.md`
11. `C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\PROGRESS.md`
12. `C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\ROLLBACK.md`
13. `C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\EXECUTION_PROMPT.md`

## Audit Findings To Address

### P1

1. 分析中にキャンセルできず、完了後は自動遷移で主導権を失う
   - owner:
     - `nicegui_app.py`
2. 保存済みワークスペースの 6 タブが非技術ユーザーには重い
   - owner:
     - `core/ui/panels.py`
     - optional `nicegui_app.py` CSS

### P2

3. ダッシュボード上段の 2 カードが説明中心で価値訴求が弱い
   - owner:
     - `core/ui/dashboard.py`
     - optional `nicegui_app.py`
4. `実装・設定` タブが要対応と参考情報を長い 1 スクロールで混在させている
   - owner:
     - `core/ui/panels.py`
5. 入力時のエラー予防が遅く、失敗が実行後に発覚しやすい
   - owner:
     - `nicegui_app.py`

## Scope

この package が扱うもの:

- `nicegui_app.py` の入力導線、進行中制御、遷移制御、入力バリデーション、文言、必要最小限の CSS
- `core/ui/dashboard.py` の hero 下 2 カードの価値訴求化
- `core/ui/panels.py` の saved workspace IA と `実装・設定` の情報分離
- UI regression を守るための必要最小限の test 更新
- 実行 progress docs

この package が扱わないもの:

- 分析ロジック変更
- スコア式変更
- provider 判定意味変更
- legal meaning 変更
- DB schema 変更
- unrelated refactor

## Design Constraints

- 現在の analysis output contract はできるだけ維持する
- `score meaning` と `legal notes meaning` は変えない
- `saved workspace` の情報を削除するのではなく、初期表示と後退配置を見直す
- `FAQ` や `履歴比較` を削除しない
- `llms.txt` を hard requirement に戻さない
- auto navigation を完全除去するのではなく、`ユーザーが選べる制御` にする

## Success Criteria

- 分析開始後に `キャンセル` か、少なくとも `完了後に自動で開かない` をユーザーが選べる
- 入力時点で URL の形式不備を先に検出し、無駄な待機を減らせる
- dashboard first view で `このソフトで何が分かるか / 最近の成果 / 次の入口` が伝わる
- saved workspace の primary navigation が非技術ユーザーにも迷いにくい
- `実装・設定` に `ここまで見れば十分` の停止基準があり、参考情報は後退している
- regression が green で、live `/` と `/runs/{run_id}` の主導線が壊れていない

## Phase Summary

| Phase | Name | Goal |
|------|------|------|
| 0 | package bootstrap | docs / phase ledger / restart prompt を固定する |
| 1 | baseline and success lock | finding を owner / success criteria / stop rule に落とす |
| 2 | input guardrails | URL 正規化 / 事前エラー防止 / 補助コピーを整える |
| 3 | analysis control recovery | cancel / stay-on-page / auto-open control を導入する |
| 4 | dashboard value proposition | top 2 cards を価値訴求カードへ置き換える |
| 5 | workspace IA simplification | 非技術ユーザー向け primary tab を絞り、secondary 情報を後退させる |
| 6 | implementation/reference split | `実装・設定` の停止基準と参考情報の分離を明確にする |
| 7 | verification and closeout | regression / live verify / residual risk を整理する |

## Recommended Execution Order

1. Phase 2 を先に進める
   - 理由:
     - narrow fix で影響範囲が読みやすい
2. Phase 3 を次に進める
   - 理由:
     - P1 の主導権喪失を先に解消したい
3. Phase 4 と Phase 5 / 6 を分けて進める
   - 理由:
     - dashboard と workspace は owner と検証画面が異なる

## Operating Rule

- Codex は 1 回に 1 phase だけ進める
- 各 phase で自己テスト -> `PROGRESS.md` 更新 -> gate green のときだけ次 phase へ進む
- 詰まったら owner file に限定して narrow fix を優先する
- local context だけで解決できない場合のみ web 検索を最大 3 回まで行う
- 3 回でも解けなければ停止し、`PROGRESS.md` と user report に failure を残す
