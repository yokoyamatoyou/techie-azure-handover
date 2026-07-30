# enterprise_saas_redesign_2026-04-02 TASK

このファイルは Phase 0-7、gate、自己テスト、停止条件、screenshot rule を固定する。

## Global Rules

- 分析ロジック、スコア計算、判定意味は変更しない
- 1 回に 1 phase だけ進める
- phase ごとに自己テストを行う
- phase ごとに `desktop + mobile screenshot` を保存する
- phase 完了ごとに `PROGRESS.md` を更新する
- 同一 phase の自己修正は最大 3 回
- 3 回失敗したら停止し、失敗内容 / 試した修正 / 推定原因 / 次に必要な判断を user report する
- gate が green にならない限り次 phase に進まない

## Gates

### Entry Gate

- `README.md / TASK.md / PROGRESS.md / ROLLBACK.md / EXECUTION_PROMPT.md` が揃っている
- baseline screenshot と baseline findings が package に固定されている
- current owner / rollback boundary / removal targets が明文化されている

### Phase Pass Gate

- phase-specific implementation が owner scope 内で完了している
- required self-tests が pass している
- required screenshot が保存されている
- `PROGRESS.md` に evidence / test result / next action が記録されている

### Auto-Advance Gate

- current phase が `completed`
- next phase の objective / owner / checks / risks が `PROGRESS.md` に初期化されている

### Stop Gate

- 同一 phase で 3 回失敗
- analysis logic change が必要
- rollback 不可能な差分が必要
- live verify で重大 regression

## Shared Check Commands

### Compile Gate

```text
C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py core\storage\database.py
```

### Regression Gate

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py
```

### Live Verify

```text
C:\tetie\techie-hub\start.bat force
```

確認対象:

- `http://127.0.0.1:8081/`
- `http://127.0.0.1:8081/runs/{run_id}`

## Screenshot Rule

- baseline は `artifacts\baseline\`
- 各 phase は `artifacts\phase-0N\`
- 最低保存物:
  - `home-desktop.png`
  - `home-mobile.png`
  - `detail-desktop.png` or nearest equivalent for current phase
  - `detail-mobile.png` or nearest equivalent for current phase

## Phase Map

### Phase 0: baseline と実行パッケージ作成

- Objective:
  - execution package と baseline artifacts を固定する
  - current `/` / `/report/print` / history UI の removal / inheritance を整理する
  - pytest gate を user 指定コマンドで通る状態にする
- Owner:
  - package docs
  - test bootstrap
- Required checks:
  - Compile Gate
  - Regression Gate
- Exit:
  - docs 5 点作成済み
  - baseline screenshots 保存済み
  - `.venv\Scripts\pytest.exe -q ...` が通る

### Phase 1: IA + visual system

- Objective:
  - enterprise SaaS の information architecture と visual rules を固定する
- Owner:
  - `nicegui_app.py`
  - `core/ui/dashboard.py`
  - `core/ui/panels.py`
- Required checks:
  - Compile Gate
  - Regression Gate
  - live screenshot
- Exit:
  - wireframe 相当の UI hierarchy と visual rules が実装反映されている

### Phase 2: persistence upgrade with result_path + snapshot JSON

- Objective:
  - DB migration, result JSON persistence, UI snapshot persistence, rehydrate API を成立させる
- Owner:
  - `core/storage/database.py`
  - `core/application/analysis_run_service.py`
- Required checks:
  - Compile Gate
  - Regression Gate
  - new persistence tests
- Exit:
  - saved run detail を file + DB snapshot から再構成できる

### Phase 3: dashboard/home 実装

- Objective:
  - `/` を enterprise dashboard に再構成し、履歴詳細に入れるようにする
- Owner:
  - `nicegui_app.py`
  - `core/ui/dashboard.py`
- Required checks:
  - Compile Gate
  - Regression Gate
  - dashboard tests
  - live screenshot
- Exit:
  - dashboard から `詳細を見る` で saved detail に入れる

### Phase 4: detail workspace 実装

- Objective:
  - `/runs/{run_id}` を新設し、AI認識改善 / SEO改善 / 履歴 / 技術補足 を left rail で再表示する
- Owner:
  - `nicegui_app.py`
  - `core/ui/panels.py`
- Required checks:
  - Compile Gate
  - Regression Gate
  - detail workspace tests
  - live screenshot
- Exit:
  - saved run を再表示できる
  - personalized advice と fixed/reference の格差が視覚上明確

### Phase 5: CSV export + PDF removal

- Objective:
  - 2 系統の CSV export を追加し、PDF / print 依存を除去する
- Owner:
  - `core/application/analysis_run_service.py`
  - `core/ui/dashboard.py`
  - `nicegui_app.py`
- Required checks:
  - Compile Gate
  - Regression Gate
  - new CSV tests
- Exit:
  - 優先アクションCSV / 履歴一覧CSV が動く
  - PDF route / print link / pdf export path が消えている

### Phase 6: polish + accessibility

- Objective:
  - desktop / mobile / zoom / keyboard / contrast を整える
- Owner:
  - UI shell and CSS only
- Required checks:
  - Compile Gate
  - Regression Gate
  - live screenshot
- Exit:
  - 崩れ、過密、視認性問題がない

### Phase 7: prompt injection / pipeline / code review

- Objective:
  - prompt injection / pipeline boundary / dead code / duplicate CSS / unused import / test gap を最終レビューする
- Owner:
  - review and narrow cleanup only
- Required checks:
  - Compile Gate
  - Regression Gate
  - live verify
- Exit:
  - review record が残り、残リスクが明文化されている
