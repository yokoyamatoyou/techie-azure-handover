# kotomigaki_report_accessibility_audit_2026-06-13 TASK

このファイルは、Codex がレポート品質とアクセシビリティ表示を迷わず監査するための phase / gate / retry / stop rule を固定する。

## Global Rules

- まず audit-only で進める
- 新規分析は UI から実行してよい
- 分析対象の初期 smoke URL は `https://example.com/`
- product code は原則変更しない
- audit blocker の narrow fix が必要な場合だけ snapshot 後に変更する
- score formula / legal meaning / LLMモデル選択は変更しない
- 各 phase で evidence を `PROGRESS.md` に残す
- 同一 failure の local repair は最大 3 回
- Web 検索は同一 failure につき最大 3 回

## Entry Gate

- `README.md / TASK.md / PROGRESS.md / ROLLBACK.md / EXECUTION_PROMPT.md` が揃っている
- `C:\tetie\AGENTS.md` と `C:\tetie\aio2-main\AGENTS.md` を読んでいる
- `ALGORITHM.md` のアクセシビリティ節を確認している
- `WORKLOG.md` の 2026-06-12 以降のアクセシビリティ / レポート品質関連を確認している

## Shared Commands

### Compile Gate

```text
C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\site_health\accessibility_checker.py core\site_health\browser_accessibility_scanner.py core\application\accessibility_improvement_builder.py core\application\analysis_run_service.py core\application\markdown_report_service.py core\ui\tabs\seo_tab.py core\ui\saved_workspace.py core\ui\reports\executive_summary.py nicegui_app.py
```

### Targeted Regression Gate

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_accessibility_checker.py tests\test_analysis_run_service.py tests\test_markdown_report_service.py tests\test_executive_summary.py tests\test_characterization_ui.py
```

### Browser Scanner Smoke

```text
cd /d C:\tetie\aio2-main\tools\accessibility_scanner
npm run smoke:scan
```

Expected:

- scan completes
- score is present
- report uses `seo_accessibility_ux_v1`
- no secret / local path leakage in stdout

### Live Startup

```text
C:\tetie\techie-hub\start.bat force
```

Confirm:

- `http://127.0.0.1:8081/` opens
- no server traceback / 500 in `C:\tetie\aio2-main\logs\app.log`

## Phase Map

### Phase 0: Package Entry Review

Objective:

- package が実行可能か確認する

Owner:

- docs only

Required checks:

- Entry Gate

Evidence:

- `PROGRESS.md` に読了ファイルと不足なし/不足ありを記録

Exit:

- Phase 1 へ進める状態

### Phase 1: Static Surface Inventory

Objective:

- レポート / UI / アクセシビリティの owner と表示面を固定する

Owner:

- `core/application/markdown_report_service.py`
- `core/application/accessibility_improvement_builder.py`
- `core/ui/saved_workspace.py`
- `core/ui/tabs/seo_tab.py`
- `core/ui/reports/executive_summary.py`
- `core/site_health/browser_accessibility_scanner.py`

Required checks:

- 各 owner file で、非エンジニア用と技術用の出力経路を読む
- `rg` で禁止語/要注意語を確認する

Useful commands:

```text
rg -n "WCAG|JIS|準拠|適合|認証|aria-label|<img|axe-core|selector|対象要素|検出元|実ブラウザ自動検出|HTML自動検出" core PDFreport tests
```

Evidence:

- `artifacts\phase-01-static-surface.md`

Exit:

- 監査で見るべき UI/Markdown/snapshot の場所が一覧化されている

### Phase 2: Automated Regression Gate

Objective:

- UI監査前に既存の決定的な回帰テストを通す

Owner:

- test execution only

Required checks:

- Compile Gate
- Targeted Regression Gate
- Browser Scanner Smoke

Evidence:

- command / result / failure summary を `PROGRESS.md` に記録

Exit:

- green なら Phase 3
- red なら同一 failure 最大 3 回まで narrow fix

### Phase 3: Startup and Pre-Analysis UI Check

Objective:

- 分析前でもトップ画面と履歴導線が壊れていないことを確認する

Owner:

- live UI

Required checks:

- Live Startup
- Browser で `http://127.0.0.1:8081/` を開く
- 分析前の履歴表示を確認する
- 空履歴なら `最近の分析はまだありません` または同等の空状態が分かる
- 履歴検索 / 履歴CSV / URL入力 / 分析開始導線が見える

Evidence:

- `artifacts\phase-03-startup-ui.md`
- screenshot が取れる場合は `artifacts\phase-03-startup.png`

Exit:

- analysis before history access が壊れていない

### Phase 4: UI-Driven New Analysis

Objective:

- Codex が UI から実際に分析を実行し、保存済み詳細まで到達できることを確認する

Owner:

- live UI

Required UI steps:

1. `http://127.0.0.1:8081/` を開く
2. URL入力へ `https://example.com/` を入れる
3. 業界 / サイト種別 / 重視目標などがある場合は、デフォルト値と選択値を記録する
4. `分析する` または同等の主ボタンを押す
5. 進行中表示、失敗表示、完了遷移を観察する
6. 完了後の `/runs/{run_id}` を記録する
7. 保存済み詳細の全主要タブを開く
8. 詳細Markdownをダウンロードまたは生成する

Evidence:

- `artifacts\phase-04-ui-analysis.md`
- new run id
- exported Markdown path
- console/server error status

Exit:

- UIから新規分析、保存詳細、Markdown出力まで到達している

### Phase 5: Report Quality Audit

Objective:

- 非エンジニアに伝わるか、エンジニア向け表示が妥当か、出力がパーソナライズされているかを評価する

Owner:

- UI observation
- exported Markdown
- saved snapshot JSON

Required checks:

- Non-Engineer Report Clarity
- Engineer UI Appropriateness
- Personalization
- Markdown completeness

Non-engineer checklist:

- `何が問題か / なぜ困るか / 次に誰へ渡すか` がある
- primary surface に code / selector / HTML / `aria-label` / `axe-core` が出ていない
- `WCAG`, `JIS`, `準拠`, `適合`, `認証` が primary surface に出ていない
- アクセシビリティは `見やすさ・使いやすさ改善`, `改善スコア`, `自動検出` 系で説明されている

Engineer checklist:

- 技術側に `対象要素 / 行うべき作業 / 確認方法 / 検出元` がある
- `実ブラウザ自動検出` または `HTML自動検出` が分かる
- selector / HTML detail が必要な場合、技術側かMarkdown後半に閉じている

Personalization checklist:

- URL / title / site_type / platform / business_goal / page_role / intent のいずれかが出力に入る
- FAQ候補や改善提案が generic すぎない
- 同じ `SEO改善` ラベルだけが連続しない
- 比較材料が不足する場合は inconclusive と書く

Markdown checklist:

- 分析日時が JST または明示タイムゾーン付き
- 対象URLが明記される
- score / top action / accessibility source が落ちていない
- local path や internal debug が非エンジニア前半に出ない
- 見出し階層と箇条書きが崩れていない

Evidence:

- `artifacts\phase-05-report-quality.md`

Exit:

- pass/fail/inconclusive が根拠付きで出ている

### Phase 6: Accessibility-Specific Deep Check

Objective:

- 新規実装のアクセシビリティ部分が、UI/Markdown/snapshotで期待通りに出るか確認する

Owner:

- `site_health.accessibility`
- UI
- Markdown
- snapshot

Required checks:

- `site_health.accessibility.source` が `browser` または fallback 理由付きで確認できる
- browser source の場合、UIまたはMarkdownに `実ブラウザ自動検出` が出る
- fallback の場合、`HTML自動検出` として過剰に見せていない
- raw issue が 0 のとき、汎用作業カードが primary surface に出ない
- issue があるとき、非エンジニア向けは impact/review_area/handoff、技術向けは task/verification/detection_source に分かれる

Evidence:

- `artifacts\phase-06-accessibility.md`

Exit:

- アクセシビリティ部分の品質リスクが分類されている

### Phase 7: Final Audit Report

Objective:

- 実施結果、finding、fix queue、残リスクを1ファイルにまとめる

Owner:

- docs / artifacts only

Required output:

- `artifacts\audit_report_YYYYMMDD_HHMMSS.md`

Report sections:

- Scope
- Environment
- Commands
- UI operation result
- Report quality verdict
- Accessibility verdict
- Personalization verdict
- Findings P1/P2/P3
- Fix queue with owner files
- Tests and evidence
- Residual risk
- AGENTS/WORKLOG update need

Exit:

- user が修正に進むか、監査完了で止めるか判断できる

## Stop Gate

- 同一 failure で 3 回失敗
- Web 検索 3 回でも解決不能
- external API / paid API の追加送信が必要
- score formula / legal meaning の変更が必要
- UIから新規分析できず、原因が owner scope 外
- product code を大きく直さないと audit が進まない

## Failure Handling

### Local Repair Sequence

1. failure の再現条件を固定する
2. owner file を1つから3つまでに限定する
3. narrow fix を試す
4. Compile Gate と affected pytest を実行する
5. `PROGRESS.md` Failure Log に attempts を残す

### Web Search Sequence

以下すべてを満たす場合のみ使う。

- local context だけでは NiceGUI / Playwright / axe-core などの挙動が確定しない
- primary source が必要
- 同一 failure の検索回数が 3 回未満

記録するもの:

- query
- source URL
- 採用した推論
- 試した fix
- 結果

## Do Not Do

- 監査中に UI全体を作り直す
- score や ranking を変えて品質改善とする
- 非エンジニア向け面に selector / HTML / code を追加する
- 技術タブから作業に必要な根拠を削る
- 古い run id 固定で監査する
- `runs/154` のような過去 run が存在する前提にする
