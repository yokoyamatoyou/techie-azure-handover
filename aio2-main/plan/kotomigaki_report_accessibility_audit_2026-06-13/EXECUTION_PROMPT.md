# kotomigaki_report_accessibility_audit_2026-06-13 EXECUTION PROMPT

## autonomous_start_prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\aio2-main\AGENTS.md
- C:\tetie\aio2-main\ALGORITHM.md
- C:\tetie\aio2-main\WORKLOG.md
- C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\README.md
- C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\TASK.md
- C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\PROGRESS.md
- C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\ROLLBACK.md
- C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\EXECUTION_PROMPT.md

今回の実施範囲:
- コトミガキ `aio2-main` の新規レポート品質とアクセシビリティ表示を集中監査する
- 非エンジニアに伝わるか、エンジニア向けUI表示が作業指示として妥当か、アウトプットがパーソナライズされているかを評価する
- Codex が UI から新規分析、保存済み詳細、詳細Markdown出力まで実際に操作できるか確認する
- まず audit-only で進め、UI操作不能やレポート生成不能の audit blocker だけ narrow fix してよい
- score formula / legal meaning / LLMモデル選択 / UI全体再設計は変更しない

最初に必ず読む:
1. C:\tetie\AGENTS.md
2. C:\tetie\aio2-main\AGENTS.md
3. C:\tetie\aio2-main\ALGORITHM.md
4. C:\tetie\aio2-main\WORKLOG.md
5. C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\README.md
6. C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\TASK.md
7. C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\PROGRESS.md
8. C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\ROLLBACK.md
9. C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\EXECUTION_PROMPT.md

実行順:
1. `PROGRESS.md` の Current Phase と Phase Ledger を読む
2. `TASK.md` の Entry Gate を確認する
3. Phase 0 から Phase 7 まで順に進める
4. 各 phase の evidence を `PROGRESS.md` と `artifacts\` に残す
5. 最終的に `artifacts\audit_report_YYYYMMDD_HHMMSS.md` を作成する

Phase:
- Phase 0: package entry review
- Phase 1: static surface inventory
- Phase 2: automated regression gate
- Phase 3: startup and pre-analysis UI check
- Phase 4: UI-driven new analysis
- Phase 5: report quality audit
- Phase 6: accessibility-specific deep check
- Phase 7: final audit report

Shared compile:
C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\site_health\accessibility_checker.py core\site_health\browser_accessibility_scanner.py core\application\accessibility_improvement_builder.py core\application\analysis_run_service.py core\application\markdown_report_service.py core\ui\tabs\seo_tab.py core\ui\saved_workspace.py core\ui\reports\executive_summary.py nicegui_app.py

Shared tests:
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_accessibility_checker.py tests\test_analysis_run_service.py tests\test_markdown_report_service.py tests\test_executive_summary.py tests\test_characterization_ui.py

Browser scanner smoke:
cd /d C:\tetie\aio2-main\tools\accessibility_scanner
npm run smoke:scan

Live startup:
C:\tetie\techie-hub\start.bat force

Live UI targets:
- http://127.0.0.1:8081/
- newly created /runs/{run_id}

UI operation to perform:
1. Open http://127.0.0.1:8081/
2. Confirm history access before analysis
3. Enter https://example.com/
4. Record selected industry/site type/business goal controls if present
5. Start analysis from the UI
6. Wait for completion
7. Record the new run id
8. Open the saved detail page
9. Visit all major tabs
10. Generate or download detailed Markdown
11. Check browser console and C:\tetie\aio2-main\logs\app.log for traceback / 500 / fatal error

Non-engineer audit checks:
- Can a business user tell what happened, why it matters, and who should act next?
- Do primary surfaces avoid code, selector, HTML snippets, `aria-label`, `axe-core`, and internal debug?
- Do primary surfaces avoid `WCAG`, `JIS`, `準拠`, `適合`, `認証`?
- Is accessibility framed as `見やすさ・使いやすさ改善`, `改善スコア`, or `自動検出`?
- Does the report avoid generic-only advice?

Engineer audit checks:
- Does the technical side include `対象要素 / 行うべき作業 / 確認方法 / 検出元`?
- Does it show `実ブラウザ自動検出` or `HTML自動検出` when relevant?
- Are selector/HTML details limited to technical tabs or Markdown technical sections?
- Can an engineer turn the output into concrete work without asking what element or how to verify?

Personalization checks:
- Does the output reflect URL, page title, site type, platform, business goal, page role, search intent, or persona?
- Are FAQ candidates and improvement actions contextualized rather than generic?
- If personalization cannot be proven from one run, mark it `inconclusive` and state what second-run comparison would be needed.

Accessibility-specific checks:
- Confirm `site_health.accessibility.source`
- Confirm browser scanner source or fallback reason
- Confirm zero-finding/generic accessibility cards are not promoted as primary work
- Confirm old compliance-style wording is absent from primary UI
- Confirm Markdown carries accessibility source and useful next action

Final report path:
C:\tetie\aio2-main\plan\kotomigaki_report_accessibility_audit_2026-06-13\artifacts\audit_report_YYYYMMDD_HHMMSS.md

Final report must include:
- Scope
- Environment
- Commands and results
- UI operation result
- Report quality verdict
- Accessibility verdict
- Personalization verdict
- Findings P1/P2/P3 with owner files
- Fix queue
- Evidence files
- Residual risk
- AGENTS / WORKLOG update need

Stop rules:
- Same failure 3 attempts
- Web search 3 attempts for the same failure
- External paid API or credentials required
- Score formula or legal meaning must change
- UI operation is blocked by owner scope outside aio2-main

Completion report:
- 参照ルールファイル
- 今回の実施範囲
- 作成/更新した artifact
- UI操作確認結果
- テスト結果
- findings summary
- AGENTS/WORKLOG更新の要否
```
