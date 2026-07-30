# kotomigaki_report_accessibility_audit_2026-06-13

`aio2-main` の新規レポート品質とアクセシビリティ表示を、Codex が別ウィンドウまたは `/goal` でそのまま監査できるように固定する実行パッケージ。

この package は実装計画ではなく、まず **audit-first** で次を確認する。

- レポート内容が非エンジニアに伝わるか
- UI上のエンジニア向け表示が、作業指示として妥当な粒度か
- 出力が URL / ページ役割 / サイト種別 / 重視目標に応じてパーソナライズされているか
- 新規実装のアクセシビリティ部分が、過剰な適合表現や技術詳細漏れを起こしていないか
- Codex が UI から実際に分析、保存済み詳細表示、Markdown出力まで操作できるか

## Package Role

- `README.md`
  - 監査の目的、read order、対象、非対象、成功条件を定義する
- `TASK.md`
  - phase / gate / self-test / stop rule / UI操作確認を固定する
- `PROGRESS.md`
  - current phase、phase ledger、evidence、failure log を管理する
- `ROLLBACK.md`
  - audit-only 境界、変更時の戻し方、stop condition を固定する
- `EXECUTION_PROMPT.md`
  - 別ウィンドウの Codex にそのまま貼れる開始 prompt を保持する
- `artifacts\`
  - UI観察メモ、スクリーンショット、出力Markdown、最終監査レポートの置き場

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\ALGORITHM.md`
4. `C:\tetie\aio2-main\WORKLOG.md`
5. `C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\README.md`
6. `C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\TASK.md`
7. `C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\PROGRESS.md`
8. `C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\ROLLBACK.md`
9. `C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\EXECUTION_PROMPT.md`

## Current Implementation Surfaces

- 分析実行 / 履歴保存 / snapshot JSON:
  - `core/application/analysis_run_service.py`
- 詳細Markdown出力:
  - `core/application/markdown_report_service.py`
- アクセシビリティ採点:
  - `core/site_health/accessibility_checker.py`
  - `core/site_health/browser_accessibility_scanner.py`
- アクセシビリティ改善カード変換:
  - `core/application/accessibility_improvement_builder.py`
- 保存済み詳細workspace:
  - `core/ui/saved_workspace.py`
- SEO/改善タブ:
  - `core/ui/tabs/seo_tab.py`
- 経営サマリー / レーダー:
  - `core/ui/reports/executive_summary.py`
- 内蔵ブラウザスキャナー:
  - `tools/accessibility_scanner\`

## Audit Scope

この package が扱うもの:

- `http://127.0.0.1:8081/` のトップ画面からの新規分析実行
- 分析前の履歴表示、空履歴状態の見え方
- 新規分析後の `/runs/{run_id}` 保存済み詳細
- 詳細Markdownダウンロード
- アクセシビリティの UI / Markdown / snapshot 反映
- 非エンジニア向け表示とエンジニア向け表示の分離
- パーソナライズ性の根拠確認
- 監査レポート作成

この package が扱わないもの:

- score formula の変更
- legal meaning の変更
- LLMプロンプトや外部APIモデルの刷新
- UI全体の再設計
- 古い archived run の復元
- コトメイク / コトメガネ / コトムスビの監査

## Audit Axes

### A. Non-Engineer Report Clarity

非エンジニア向けの主画面、保存済み詳細の上段、改善/設定系タブ、Markdown前半で確認する。

Pass 条件:

- 最初に `何が問題か / なぜ事業上困るか / 次に誰へ渡すか` が分かる
- `aria-label`, `<img>`, CSS selector, `axe-core`, DOM, HTML断片などが primary surface に出ない
- `WCAG`, `JIS`, `準拠`, `適合`, `認証` のような適合判定に見える語が出ない
- アクセシビリティは `見やすさ・使いやすさ改善`, `改善スコア`, `自動検出` 系で説明される
- 汎用テンプレートだけでなく、このURL向けの見直し箇所がある

### B. Engineer UI Appropriateness

保存済み詳細の技術系タブ、Markdown後半、snapshot JSON で確認する。

Pass 条件:

- `対象要素 / 行うべき作業 / 確認方法 / 検出元` が技術側にある
- `実ブラウザ自動検出` または `HTML自動検出` の出所が確認できる
- セレクタや要素名が必要な場合は技術側に閉じている
- 旧snapshotや空検出時に、汎用のアクセシビリティ作業カードが主表示へ出ない
- エンジニア向け情報が長すぎる場合は expansion / 技術タブ / Markdown後半へ後退している

### C. Personalization

新規分析の入力値、保存snapshot、UI、Markdownを照合する。

Pass 条件:

- URL、ページタイトル、サイト種別、プラットフォーム、重視目標、ページ役割、検索意図のいずれかが出力に反映される
- FAQ候補や改善提案が `誰向けのページか` を踏まえた文になっている
- `SEO改善` だけの同名カードが連続せず、優先理由が分かる
- 同一URLでも重視目標を変えた場合、優先アクションやサマリーが完全固定ではないことを確認できる
- 変化を確認できない場合は、`personalization inconclusive` として監査レポートに残す

### D. UI Operation Reality

Codex が Browser または同等の UI 操作で確認する。

Pass 条件:

- トップ画面が HTTP 200 で開く
- 分析前でも履歴検索 / 履歴CSV / 空履歴メッセージが壊れない
- UIから `https://example.com/` の新規分析を開始できる
- 完了後に `/runs/{run_id}` へ到達できる
- 保存済み詳細の主要タブを開ける
- 詳細Markdownをダウンロードまたは生成できる
- ブラウザ console / server log に traceback / 500 / fatal error が出ない

## Success Criteria

- `artifacts\audit_report_YYYYMMDD_HHMMSS.md` が作成され、各 audit axis の pass/fail/inconclusive が明記されている
- UI操作で新規分析から保存済み詳細、Markdown出力まで確認している
- アクセシビリティの非エンジニア表示と技術表示を別々に評価している
- パーソナライズ性を `入力値と出力の対応` として評価している
- 修正が必要な場合、P1/P2/P3 と owner file を付けた fix queue がある
- product code を変更した場合は、開始前 snapshot、検証、WORKLOG 更新がある

## Operating Rule

- まず audit-only で完走する
- UI操作不能、レポート生成不能、明白な 500 など audit blocker は narrow fix してよい
- narrow fix する場合は、先に snapshot を取り、owner file を限定する
- 同一 failure の修正試行は最大 3 回
- local context だけで解決できない場合のみ Web 検索を最大 3 回まで使う
- Web 検索を使った場合は query / source / inference / tried fix を `PROGRESS.md` に残す
- 3 回でも解けなければ停止し、監査レポートに blocker と残作業を残す
