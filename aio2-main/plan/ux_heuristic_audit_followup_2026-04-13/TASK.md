# ux_heuristic_audit_followup_2026-04-13 TASK

このファイルは、Codex が別ウインドウでも迷わず完走するための
**phase / gate / retry / stop rule** を固定する。

## Global Rules

- `analysis logic / score formula / legal meaning` は変更しない
- 1 回に 1 phase だけ進める
- phase 開始前に owner file を固定する
- phase ごとに自己テストする
- phase ごとに `PROGRESS.md` を更新する
- gate green 以外では次 phase に進まない
- 同一 phase 内の自己修正は最大 3 回
- bug / error は local context で narrow fix を優先する
- Web 検索は同一 failure につき最大 3 回
- `C:\tetie\zip` は参照のみ。変更しない

## Gates

### Entry Gate

- `README.md / TASK.md / PROGRESS.md / ROLLBACK.md / EXECUTION_PROMPT.md` が揃っている
- current scope / non-scope / success criteria が `README.md` にある
- `Current phase` と `Phase Ledger` が `PROGRESS.md` にある

### Phase Pass Gate

- phase-specific 実装が owner scope で完了している
- required self-tests が pass している
- required evidence が `PROGRESS.md` に記録されている
- failure attempts / web search attempts が更新されている

### Auto-Advance Gate

- current phase が `completed`
- next phase の objective / owner / checks / risks が `PROGRESS.md` に初期化済み
- stop gate に触れていない

### Stop Gate

- 同一 phase で 3 回失敗
- Web 検索 3 回でも修正不能
- algorithm / score / legal meaning の変更が必要
- rollback 不能な差分が必要
- live verify で重大 regression

## Shared Check Commands

### Compile Gate

```text
C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py
```

### Targeted Regression Gate

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_dashboard_ui.py tests\test_characterization_ui.py tests\test_analysis_run_service.py tests\test_executive_summary.py
```

### Live Verify Gate

```text
C:\tetie\techie-hub\start.bat force
```

確認対象:

- `http://127.0.0.1:8081/`
- `http://127.0.0.1:8081/runs/84`

## Evidence Rule

- UI 変更 phase では screenshot または live observation memo のどちらかを `PROGRESS.md` に残す
- screenshot 保存先:
  - baseline: `artifacts\baseline\`
  - 各 phase: `artifacts\phase-0N\`
- screenshot を取れない場合でも、`何を見て pass と判断したか` を文章で残す

## Failure Handling Protocol

### Local Repair Sequence

1. failing test / failing route / broken interaction を固定する
2. owner file のみで narrow fix を試す
3. Compile Gate と affected pytest を再実行する

### Web Search Repair Sequence

以下すべてを満たす場合のみ Web 検索を使う。

- local context だけでは仕様・挙動が確定しない
- primary source の確認が必要
- failure が NiceGUI / Quasar / accessibility / browser behavior に関係する

Web 検索のルール:

- 同一 failure あたり最大 3 回
- source は official / primary を優先する
- query / source / inference / tried fix を `PROGRESS.md` failure log に残す
- 3 回失敗したら停止する

## Phase Map

### Phase 0: package bootstrap

- Objective:
  - execution package、phase ledger、restart prompt を固定する
- Owner:
  - docs only
- Required checks:
  - Entry Gate review
- Exit:
  - docs が揃っている

### Phase 1: baseline and success lock

- Objective:
  - 監査 finding を `実装対象 / 非対象 / 成功条件 / 停止条件` に固定する
- Owner:
  - docs + baseline memo
- Required checks:
  - Compile Gate
  - `/` と `/runs/84` の現状確認
- Exit:
  - success criteria と phase order が `README.md` と `PROGRESS.md` に明記されている

### Phase 2: input guardrails

- Objective:
  - 空入力以外の事前エラー防止を追加し、URL 形式不備を実行前に出す
- Owner:
  - `nicegui_app.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify on invalid URL / valid URL
- Exit:
  - main URL と competitor URL の誤入力が実行前に検出される
  - helper copy が冗長すぎない

### Phase 3: analysis control recovery

- Objective:
  - 分析中 / 完了後の主導権を user に戻す
- Owner:
  - `nicegui_app.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify on start / cancel or stay-on-page / open saved run
- Exit:
  - user が `今は移動しない` を選べる
  - 主ボタンが一方通行になっていない

### Phase 4: dashboard value proposition

- Objective:
  - dashboard 上段の説明カードを価値訴求カードへ置き換える
- Owner:
  - `core/ui/dashboard.py`
  - optional `nicegui_app.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify desktop + mobile
- Exit:
  - first view で価値と次アクションが分かる
  - 説明だけのカードが primary surface を占有していない

### Phase 5: workspace IA simplification

- Objective:
  - non-technical primary navigation を軽くする
- Owner:
  - `core/ui/panels.py`
  - optional `nicegui_app.py` CSS
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify desktop + mobile
- Exit:
  - primary tabs は 3 つ前後で読める
  - `エンジニア向け` と `履歴と比較` は secondary 扱いになっている

### Phase 6: implementation/reference split

- Objective:
  - `実装・設定` で要対応と参考を混在させず、停止基準を作る
- Owner:
  - `core/ui/panels.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify saved + live
- Exit:
  - `ここまで見れば十分` が分かる
  - 参考情報は後退している

### Phase 7: verification and closeout

- Objective:
  - regression、live verify、residual risk、next action を整理して close する
- Owner:
  - review + docs + narrow cleanup only
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - final live verify
- Exit:
  - `PROGRESS.md` ledger が complete
  - residual risk と未着手理由が明文化されている

## Required PROGRESS Update Fields Per Phase

各 phase 完了時に最低限これを更新する。

- `Current phase`
- `Status`
- `Attempts used`
- `Web search attempts used`
- `Implementation`
- `Self-tests`
- `Evidence`
- `Next action`
- `Failure log` if any

## Do Not Do

- score meaning を変えて UX を直したことにする
- `履歴と比較` や `FAQ` を消して単純化する
- reference 情報を削除で済ませる
- phase gate 未通過で unrelated owner に差分を広げる
- user choice が必要な UX を hidden behavior で勝手に決める
