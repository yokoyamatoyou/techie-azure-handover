# ux_commercial_readiness_2026-04-05 TASK

このファイルは、Codex が迷わず完走するための **phase / gate / retry / stop rule** を固定する。

## Global Rules

- analysis logic、score formula、判定意味は変更しない
- 1 回に 1 phase だけ進める
- phase 開始前に対象 scope を 1 つに固定する
- phase ごとに自己テストする
- phase ごとに `PROGRESS.md` を更新する
- gate green 以外では次 phase に進まない
- 同一 phase 内の自己修正は最大 3 回
- bug / error で詰まった場合、ローカル修正を優先し、それでも解決しない場合のみ Web 検索を使う
- Web 検索は **同一 failure につき最大 3 回**
- 3 回の Web 検索でも解決しない場合は停止し、失敗内容 / 試した修正 / 推定原因 / user に必要な判断を report する
- `C:\tetie\zip` は mock として参照のみ。変更しない

## Gates

### Entry Gate

- `README.md / TASK.md / PROGRESS.md / ROLLBACK.md / EXECUTION_PROMPT.md` が揃っている
- current scope と non-scope が docs に明記されている
- baseline findings と success criteria が `README.md` にある
- current phase と phase ledger が `PROGRESS.md` にある

### Phase Pass Gate

- phase-specific 実装が owner scope で完了している
- required self-tests が pass している
- required evidence が `PROGRESS.md` に記録されている
- failure attempts / web search attempts が更新されている

### Auto-Advance Gate

- current phase の status が `completed`
- next phase の objective / owner / checks / risks が `PROGRESS.md` に初期化済み
- stop condition に該当しない

### Stop Gate

- 同一 phase で 3 回失敗
- Web 検索 3 回でも修正不能
- algorithm / score / legal meaning の変更が必要
- rollback 不能な差分が必要
- live verify で重大 regression

## Shared Check Commands

### Compile Gate

```text
C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py core\ui\dashboard.py core\ui\tabs\aio_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py
```

### Targeted Regression Gate

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py
```

### UX / Dashboard Extended Gate

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_dashboard_ui.py
```

### Live Verify Gate

```text
C:\tetie\techie-hub\start.bat force
```

確認対象:

- `http://127.0.0.1:8081/`
- `http://127.0.0.1:8081/runs/{run_id}`

## Evidence Rule

- screenshot を強制しない phase でも、最低限 `PROGRESS.md` に確認結果を書く
- visual 変更 phase では screenshot or live observation memo のどちらかを必ず残す
- screenshot 保存先:
  - baseline: `artifacts\baseline\`
  - 各 phase: `artifacts\phase-0N\`

## Failure Handling Protocol

### Local Repair Sequence

1. stack trace / failing test / failing route を固定する
2. owner file のみで narrow fix を試す
3. Compile Gate / affected pytest を再実行する

### Web Search Repair Sequence

以下すべてを満たす場合のみ Web 検索を使う。

- local context だけでは仕様・挙動が確定しない
- primary source の確認が必要
- failure が UI framework / browser / platform guidance / accessibility guidance に関係する

Web 検索のルール:

- 同一 failure あたり最大 3 回
- source は primary or official を優先する
- query / source / inference / tried fix を `PROGRESS.md` failure log に残す
- 3 回失敗したら停止する

## Phase Map

### Phase 0: package bootstrap

- Objective:
  - execution package、phase ledger、restart protocol を固定する
- Owner:
  - package docs only
- Required checks:
  - Entry Gate review
- Exit:
  - docs 5 点 + `artifacts\` が揃っている
  - baseline findings / success criteria / stop rule が固定されている

### Phase 1: UX criteria lock

- Objective:
  - commercial readiness 判定基準、対象 screen、phase success metrics を固定する
- Owner:
  - docs + verify memo
- Required checks:
  - current `/` / `/runs/{run_id}` の確認
  - Compile Gate
- Exit:
  - `README.md` と `PROGRESS.md` に baseline findings と target state が明文化されている

### Phase 2: IA copy alignment

- Objective:
  - hero / onboarding / guide copy を actual 5 タブ IA に一致させる
- Owner:
  - `nicegui_app.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify for entry copy
- Exit:
  - old `現状 / 改善方法 / 詳細` copy が current mainline の primary surface に残っていない

### Phase 3: summary / task hierarchy

- Objective:
  - `サマリー` と `やること` の first-view hierarchy を強化する
- Owner:
  - `core/ui/panels.py`
  - optional `nicegui_app.py` CSS
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify desktop + mobile
- Exit:
  - first 30 秒で `結論 / 要対応件数 / Top3` が読める

### Phase 4: implementation compression

- Objective:
  - `実装・設定` を warn/fail 中心の判断面に寄せる
- Owner:
  - `core/ui/panels.py`
  - optional `core\application\analysis_run_service.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify saved + live
- Exit:
  - pass noise が primary surface を汚さない
  - raw technical value が user-facing surface に戻っていない

### Phase 5: FAQ rationale polish

- Objective:
  - FAQ personalization を UI 上でも即読できるようにする
- Owner:
  - `core\application\analysis_run_service.py`
  - `core\ui\panels.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - FAQ あり / FAQ なし の live verify
- Exit:
  - FAQ suggestion が generic help へ戻っていない
  - why-this-FAQ が短く伝わる

### Phase 6: dashboard density / mobile

- Objective:
  - `/` の dashboard、history、mobile readability を再調整する
- Owner:
  - `core\ui\dashboard.py`
  - `nicegui_app.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - `tests\test_dashboard_ui.py`
  - live verify desktop + mobile
- Exit:
  - home の密度が過剰でない
  - mobile history / CTA / KPI が崩れない

### Phase 7: accessibility / interaction verify

- Objective:
  - keyboard、focus、contrast、zoom、empty state を確認し必要なら narrow fix する
- Owner:
  - UI shell and CSS only
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live verify
- Exit:
  - keyboard tab 移動で主導線が追える
  - contrast / zoom / empty state に重大欠落がない

### Phase 8: commercial review closeout

- Objective:
  - residual、rollback boundary、known risks、next action を整理して close する
- Owner:
  - review + docs + narrow cleanup only
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - final live verify
- Exit:
  - `PROGRESS.md` ledger が complete
  - residual risk と stop reason が明文化されている

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

- score formula を変えて UI を整えようとする
- `llms.txt` を hard requirement に戻す
- FAQ を generic template 一覧へ戻す
- fixed/reference 情報を primary surface に戻す
- phase gate 未通過で unrelated owner に差分を広げる
