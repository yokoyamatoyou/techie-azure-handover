# ux_heuristic_audit_followup_2026-04-13 ROLLBACK

## Rollback Boundary

- この package の rollback 対象は UI shell / dashboard / panel disclosure / copy / validation に限定する
- rollback owner:
  - `nicegui_app.py`
  - `core/ui/dashboard.py`
  - `core/ui/panels.py`
  - 必要最小限の test file

## Do Not Change

- `core/engine/*`
- `core/aio_analyzer.py`
- `core/scoring_engine.py`
- provider readiness の意味
- legal 判定意味
- DB schema

## Safe Rollback Strategy

1. phase ごとに差分を小さく保つ
2. `PROGRESS.md` の phase evidence を見て直前 phase まで戻れるようにする
3. visual polish と behavior change を同一 phase で混ぜすぎない
4. live verify で重大 regression が出たら、その phase の owner file だけを元に戻す方針で narrow rollback する

## Stop Conditions

- cancel / auto-open 制御のために analysis core の大規模変更が必要になる
- workspace IA 簡略化のために snapshot contract の破壊的変更が必要になる
- dashboard 価値訴求化で履歴導線や保存導線が壊れる
- validation 追加で既存の正常 URL 入力を阻害する

## Known Risk Notes

- `cancel` を真の analysis abort として実装すると io-bound task 側の中断伝播が必要になる可能性がある
- その場合は first step として `stay on page / auto-open off` を先に入れ、完全な abort は separate phase として切り出してよい
- IA 簡略化は `情報の削除` ではなく `primary / secondary の再配置` として扱う
