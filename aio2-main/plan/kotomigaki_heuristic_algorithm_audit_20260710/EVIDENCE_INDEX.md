# Evidence Index

## 1. Snapshot と境界

| 項目 | 記録 |
|---|---|
| 監査開始 | 2026-07-10 13:15:04 JST |
| 対象 | ローカル filesystem working snapshot |
| Git | `git status` / `git rev-parse` は「not a git repository」。commit hash なし |
| 外部 API | 実行なし |
| 実装/現行仕様変更 | なし。監査 folder の新規 7 report のみ |
| 実 UI | in-app Browser runtime 初期化が 3 回 timeout/kernel reset。停止条件により未確認 |
| browser accessibility scanner | `browser_accessibility_enabled()` は `False`; `tools/accessibility_scanner/node_modules` 不在 |

## 2. Current docs

| 証拠 | 用途 |
|---|---|
| `../../../AGENTS.md` | 全体 read order、current owner hygiene、報告規則 |
| `../../AGENTS.md` | aio2-main 固有境界、current route/UI/algorithm 入口 |
| `../../ALGORITHM.md` | current algorithm / legal state contract |
| `../../WORKLOG.md` | 履歴。current owner としては使用しない |
| `../CURRENT_AND_NEXT_IMPROVEMENTS.md` | current/next 候補の確認 |
| `../seo_llmo_coverage_2026-04-06/PROGRESS.md` | package completed state |
| `../tab_ia_rework_2026-04-04/PROGRESS.md` | planning/not-started state |
| `../ux_heuristic_audit_followup_2026-04-13/PROGRESS.md:133-145` | tab follow-up completed claim と current renderer の比較 |
| `EXECUTION_PROMPT_GPT56SOL.md` | 今回の owner、成果物、禁止事項、監査軸 |

## 3. UI / saved workspace evidence

| Topic | 主な code evidence | Test/再現 |
|---|---|---|
| URL input/error | `nicegui_app.py:652-669,776-808` | static ARIA/enable-state trace |
| progress/status | `nicegui_app.py:736-768,825-869,990-1160` | static trace; browser unverified |
| auto-open opt-out | `nicegui_app.py:749-752,780-787,1163` | cancel ではないことを確認 |
| saved route/download | `nicegui_app.py:1180-1225` | auth/tenant 条件なし |
| tab helper vs renderer | `core/ui/saved_workspace.py:2562-2586,2613-2643` | `tests/test_characterization_ui.py:305-312` は helper のみ |
| UI action slicing | `saved_workspace.py:371-405` | 最大5件、先頭3件表示の追跡 |
| base/workspace actions | `analysis_run_service.py:906-926,1520-1574` | legal再追加、UI-only action |
| export actions | `analysis_run_service.py:1928-1930`; CSV `:33-54`; MD `:583-590` | surface parity static trace |
| legacy GET mutation | `analysis_run_service.py:2034-2049,2101-2118,1747-1748` | competitor omission path |
| unknown mapping | `panel_components.py:212-231`; `seo_tab.py:11-46`; `aio_tab.py:47-53`; `analysis_run_service.py:396-415` | state mapping comparison |
| history keyboard | `core/ui/dashboard.py:281-356`; `styles.py:6` | click card/rowClick、native semantics 不在 |
| role split | `saved_workspace.py:1083-1101,1710-1734,2001-2076` | primary と engineer detail 比較 |
| DOCX/Markdown scope | `nicegui_app.py:1227-1240`; `docx_report_service.py:340-350`; `markdown_report_service.py:308-466` | technical/raw 内容を test が固定 |

## 4. Algorithm evidence

| Topic | 主な code evidence | 安全な再現/結果 |
|---|---|---|
| provider false-pass | `core/aio_analyzer.py:141-174,278-343,1117-1146`; `orchestrator.py:3151-3164` | empty bot map + fetch error で全 pass。path-specific rule は None |
| score bounds/focus | `core/scoring_engine.py:71-93,132-160` | 90/90 ecommerce → 117/103.5。90/50 → SEO83/AIO17 |
| SEO simple score | `orchestrator.py:3169-3172,3371-3525` | 7 components、non-empty canonical、whitespace words |
| advanced SEO disconnect | `orchestrator.py:1340-1474,3038-3290` | international/mobile/link/media/sitemap が score 外/後付け |
| Schema graph | `core/aio/schema_validator.py:52-69,119-201`; `orchestrator.py:3064-3144`; `technical_summary_builder.py:909-916` | valid @graph Product/Offer → `found_types=['']`, score 30 |
| rewrite grounding | `core/aio_suggestions.py:88-103,273-318`; `orchestrator.py:3803-3813,5103-5432`; `citation_generator.py:91-108` | source外の sample sentence を受理 |
| FAQ/speakable | `schema_suggester.py:19-46`; `technical_summary_builder.py:887-905`; `citation_generator.py:119-151`; `simulation_tab.py:15-68` | official eligibility と比較 |
| AI causal claims | `nicegui_app.py:386-388`; `aio_analyzer.py:87,942,1327-1349`; `panels.py:1560-1561` | 出典/観測条件なしの定量文言 |
| CWV proxy | `page_experience_audit.py:81-101,156-165`; `seo_tab.py:103-114`; `analysis_run_service.py:1173-1189` | fixed formula と表示の追跡 |
| future freshness | `aio_analyzer.py:1660-1722` | 2099 date → score 1.0 / negative months |
| timeout=broken | `core/seo/link_audit.py:116-132`; `technical_summary_builder.py:519-526` | state mapping trace |

## 5. Accessibility / security evidence

| Topic | 主な code evidence | 検証 |
|---|---|---|
| Python SSRF | `core/safe_fetch.py:20-24,67-82,121-374` | `test_safe_fetch_security.py:65-166` pass |
| browser scanner availability | `browser_accessibility_scanner.py:44-52`; `site_health_engine.py:101-123` | runtime helper `False` |
| HTML fallback coverage | `accessibility_checker.py:13-23,459-518` | contrast/focus/keyboard/zoom 対象外 |
| scanner standard | `tools/accessibility_scanner/safeUrlScanner.mjs:23-25`; `scoring.mjs:4,744` | WCAG2a/2aa, JIS2016/WCAG2.0 wording |
| scanner URL safety | `urlSafety.mjs:110-147`; `safeUrlScanner.mjs:93-133,267-277` | private IP check はあり、port/IP pin はなし |
| auth/tenant | `database.py:53-64,227-234`; `nicegui_app.py:1180-1269` | localhost既定、tenant/auth条件なし |
| URL secrets | `nicegui_app.py:209-225`; `safe_fetch.py:106-113`; `database.py:123-140`; `analysis_run_service.py:1982-2049` | query が persistence/exportへ伝播 |
| XSS/output | `panel_components.py:87-122`; `nicegui_app.py:87-98,605-619`; `markdown_report_service.py:18-31` | escape/sanitize 経路を確認 |
| CSV | `csv_export_service.py:14-29,77-98` | formula prefix と local result path |
| DOCX | `docx_report_service.py:93-152,242-317` | language/title/table metadata 不在 |
| fixed vuln DB | `vulnerability_intelligence.py:1-6,129-201,250-269,369-405` | exploit本文非保持、read-only強制/complex range不足 |
| log bounds | `run_app.py:37-60` | 10MB×5 rotation |

## 6. Tests / commands

| 実行 | 結果 | 意味 |
|---|---:|---|
| `.venv\Scripts\python.exe -B -m pytest -q` targeted 30 modules | `192 passed in 52.74s` | 横断回帰。外部 API なし |
| UI/saved targeted 7 files | `77 passed in 8.46s` | helper/export/current service 回帰 |
| SEO/LLMO targeted 9 modules | `23 passed in 25.36s` | bot/SEO/Schema/page experience 回帰 |
| Security/a11y targeted set | `72 passed in 6.11s` | fetch/scanner/output 回帰 |
| owner module `py_compile` | pass | syntax compile |
| `.venv\Scripts\python.exe -m pip check` | `No broken requirements found.` | dependency consistency。CVE/advisory ではない |

集合は重複するため pass 数は合算しない。pytest は `PYTHONDONTWRITEBYTECODE=1` と cache provider 無効で実行した。`py_compile` は許可された構文確認であり、通常の `__pycache__` side effect を持つ。

## 7. Browser evidence / blocker log

確認予定だった URL は `http://127.0.0.1:8081/` と、分析完了後に生成される同一 origin の `/runs/{id}`。保存 GET に書込残余が見つかったため、read-only 監査で既存 run を開くこと自体も証拠保全上のリスクとして扱った。current-run screenshot は 0 件であり、存在するとは記録していない。

| attempt | 操作 | 結果 |
|---:|---|---|
| 1 | in-app Browser setup + page取得 | 30秒 timeout、kernel reset |
| 2 | setup + page取得 | 60秒 timeout、kernel reset |
| 3 | setup only | 60秒 timeout、kernel reset |

同一箇所 3 回失敗の停止条件により終了した。別 browser、standalone Playwright、API分析へ切替えていない。過去 screenshot/log を current visual evidence として流用していない。

## 8. 監査中に観測した外部状態変化

監査開始後の timestamp 確認で、`aio2-main/data/poc_outputs/runs/42/analysis_result.json` と `kotomegane/data/llmo_poc.db` に更新時刻が付いた。監査開始前から稼働していた Python process が存在し、本監査はそれを起動・停止しておらず、API/live分析も実行していない。原因を断定せず、これらの data を監査の再現証拠には使っていない。したがって「workspace 全データが監査中に静止していた」とは主張しない。

## 9. 公式資料（2026-07-10 checked）

- Nielsen Norman Group, 10 Usability Heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/
- Nielsen Norman Group, Progressive Disclosure: https://www.nngroup.com/articles/progressive-disclosure/
- W3C, WCAG 2.2: https://www.w3.org/TR/WCAG22/
- W3C, Status Messages: https://www.w3.org/WAI/WCAG22/Understanding/status-messages
- Google Search documentation updates: https://developers.google.com/search/updates
- Google AI features and your website: https://developers.google.com/search/docs/appearance/ai-features
- Google Core Web Vitals: https://developers.google.com/search/docs/appearance/core-web-vitals
- PageSpeed Insights field/lab: https://developers.google.com/speed/docs/insights/v5/about
- Google speakable: https://developers.google.com/search/docs/appearance/structured-data/speakable
- OpenAI crawlers: https://developers.openai.com/api/docs/bots
- OpenAI product feed: https://developers.openai.com/commerce/specs/file-upload/products
- OpenAI merchants: https://chatgpt.com/merchants/
- Perplexity crawlers: https://docs.perplexity.ai/docs/resources/perplexity-crawlers
- Anthropic crawler controls: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- OWASP SSRF Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP CSV Injection: https://owasp.org/www-community/attacks/CSV_Injection
- OWASP LLM Prompt Injection Prevention: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html

## 10. 未確認リスト

- current-run visual screenshots、actual route、console/page error
- keyboard-only、NVDA、200%/400% zoom、contrast、axe WCAG2.2 AA
- live robots/provider/CWV/link behavior
- dependency advisory/CVE scan と SBOM
- Azure auth/SAS/tenant isolation
- Word Accessibility Checker
- background runtime による data update の発生源
