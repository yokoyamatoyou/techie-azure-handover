# SEO / LLMO / Accessibility / Security マトリクス

## 1. 判定

`pass` は実装・安全な回帰テスト・公式基準が一致した範囲、`partial` は有効な実装があるが意味/coverage/運用に残余がある範囲、`fail` は誤判定または公開前 blocker、`unverified` は今回の境界で実行証拠を得ていない範囲を示す。

## 2. SEO

| 領域 | 判定 | 実装 evidence | 公式基準との照合 | 主要 gap | owner / acceptance |
|---|---|---|---|---|---|
| URL fetch / SSRF | pass | `core/safe_fetch.py:20-374`; rebind/private redirect/port tests | OWASP SSRF の allowlist、redirect、DNS/IP 防御方針と整合 | browser scanner は別実装で残余 | safe-fetch owner。現 regression を保持 |
| crawl bounds | pass/partial | `orchestrator.py:1120-1230` 最大8 page/2MB/15秒/15k chars | resource exhaustion 防御として妥当 | live 大規模 site、robots crawl-delay、JS rendering は未確認 | crawler owner。budget metadata を結果に出す |
| robots / indexability | fail | `aio_analyzer.py:141-174,278-343,1117-1146`; `orchestrator.py:3151-3164` | botごとの規則、対象 path、meta/header を一つの判定にする必要 | fetch failure false-pass、root-only path、X-Robots 分離 | provider-readiness owner。4-state evidence contract |
| title/description/H1 | partial | `orchestrator.py:3371-3525` | 基礎 SEO として有効 | presence 単純加点で quality/duplicate/site context が弱い | SEO score owner。evidence を site/page に分離 |
| canonical | fail | 非空なら加点 `orchestrator.py:3521-3525` | absolute/valid/self/redirect/indexability consistency が必要 | malformed/contradictory canonical でも加点 | SEO score owner。validity gate と target fetch state |
| content quantity | fail | whitespace word count `:3169-3172,3487-3493` | 日本語の本文量を空白語数で表せない | nav/footer 混入、language/DOM main 無視 | content evidence owner。language-aware metric |
| internal/external links | partial | count score `:3495-3501`; separate link audit | count は usefulness/到達性を表さない | timeout=broken、crawl sample と score の関係が不透明 | link evidence owner。状態分離と sample coverage |
| international SEO | partial | `orchestrator.py:3038-3044` 等に詳細 | hreflang/canonical/locale の整合が重要 | public score へ接続せず、surface 間で重要度差 | SEO score owner。hard finding と evidence trace |
| sitemap / endpoint health | partial | `orchestrator.py:1340-1403`; bounded endpoint checker | discovery evidence として有効 | score/priority contract が別 | evidence ledger owner。source/time/coverage を明示 |
| page experience / CWV | fail | `page_experience_audit.py:81-101,156-165` 固定 proxy | Google は field/lab source と p75 を区別 | 実測風 LCP/CLS を表示 | page-experience owner。未測定と risk factor のみにする |
| freshness | fail | `aio_analyzer.py:1660-1722` | future/updated/published の意味を分ける必要 | 2099 年で最高点 | freshness owner。future skew と date-role validation |
| structured data | fail | `schema_validator.py` と複数 validator | Google/Schema.org の graph 構造を正規化すべき | `@graph` false missing、consumer 不一致 | structured-data owner。単一 normalized graph |

## 3. LLMO / AI search readiness

| 領域 | 判定 | current evidence | 2026-07-10 公式基準 | gap / リスク | acceptance |
|---|---|---|---|---|---|
| Google AI features | partial | SEO/AIO/引用候補を統合 | Google は基礎 SEO を適用し、特別な technical requirement、特別 schema、AI file は不要。表示保証なし | UI の「AI引用判断に直結」「+30〜40%」が因果を過大表示 | 保証/因果数値を削除または出典と観測条件を必須化 |
| `llms.txt` | fail（文言/priority） | LLMO 実装候補に置き得る | Google 2026-06-15 更新では不要で、visibility に正負効果なし | 有効性を一般化すると誤誘導 | optional experimental artifact とし provider 別 support evidence を表示 |
| FAQ schema | fail（提案 eligibility） | `schema_suggester.py:19-46` 等が一般提案 | Google は 2026-06-15 に FAQ rich result docs を削除し、feature はもう表示されないと案内 | rich-result 効果を期待させる | Google rich result 目的から除外。semantic content 用途と分離 |
| speakable | fail（対象範囲） | generic speakable を生成 `citation_generator.py:119-151` | Google 文書は beta、米国英語の news/Google Home 文脈 | 日本語一般 site へ過剰適用 | eligibility を満たさなければ not-applicable。generic copy button を出さない |
| OpenAI crawler roles | partial | provider bot access をまとめて評価 | OAI-SearchBot、GPTBot、ChatGPT-User は目的が独立 | 一つの provider pass へ集約 | bot×purpose×path×evidence の matrix |
| Perplexity / Anthropic crawlers | partial | robots bot map | provider docs は crawler identity と制御を個別定義 | fetch failure false-pass、更新日なし | official source date と user-agent rule を versioned data 化 |
| source citation / grounding | fail | deep citation prompt は境界強化、一部 suggestion は schema sanitize のみ | 出典と生成主張の対応が必要 | 架空数値/文を High impact へ出せる | sentence→source span/id、unsupported claim reject |
| product feed / merchant data | unverified | current auditで owner path 未確認 | OpenAI は merchant/product feed の仕様を公開 | 対象 site が commerce の場合だけ必要 | site category と provider eligibility を先に判定し、別 owner で扱う |

## 4. WCAG 2.2 AA / product accessibility

| 領域 | 判定 | evidence | gap | acceptance |
|---|---|---|---|---|
| semantic landmarks / headings | fail | `nicegui_app.py:652-669` は heading 風 label | `main/h1` contract がない | native/ARIA landmark と論理 heading、実 DOM 検証 |
| input label / error | fail | URL input + 別 error label `:663-668,776-808` | `aria-invalid`, `aria-describedby`, focus guidance なし | input と説明/error id を関連付け、invalid 時に通知 |
| status messages | fail | progress/status text `:746-869` | `role=status` / `aria-live` なし | WCAG 4.1.3 に沿う live region、重複通知を避ける |
| keyboard operation | fail | mobile history click card `dashboard.py:281-318` | native button/link、tabindex、Enter/Space なし | keyboard-only で主要 journey 完走 |
| focus visible | partial | `styles.py:6` に focus-visible CSS | click card 等 non-focusable 要素には効かない | 全 interactive を native focusable にし、視覚確認 |
| contrast | unverified | current-run screenshot/DOM style 測定なし | browser runtime timeout | axe + manual contrast、状態色/disabled/text を確認 |
| reflow / zoom | unverified | responsive code はある | 200%/400% zoom の実証なし | 320 CSS px、200/400% で loss/overlap なし |
| screen reader journey | unverified | ARIA 実装不足を静的確認 | NVDA/読み上げ未実施 | heading/landmark/form/status/table/link を NVDA で確認 |
| site-under-test HTML fallback | partial | lang/title/heading/alt/label 等 `accessibility_checker.py` | contrast/focus/keyboard/zoom を見ない | source を HTML-only と明記、未確認 SC を列挙 |
| browser scanner availability | fail | `browser_accessibility_enabled() == False` | node_modules 不在 | 配布時に dependency pin + startup self-check |
| scanner standard | fail | wcag2a/2aa, JIS 2016 / WCAG2.0 | WCAG 2.2 AA 追加基準なし | versioned WCAG2.2 tags + manual SC list |
| DOCX accessibility | partial | Heading style、underlined links | title/lang/header metadata/説明なし | Word Accessibility Checker、文書 title/lang/table header |

## 5. Security / privacy

| 領域 | 判定 | evidence | risk | acceptance |
|---|---|---|---|---|
| Python fetch SSRF | pass | `safe_fetch.py:20-374`; security tests | 主経路は IP pin と hop 再検証あり | regression 維持、全 network caller が必ず利用 |
| JS browser scanner SSRF | partial | private/IP/route interception あり | arbitrary port、hostname DNS cache、IP pin なし | port allowlist、per-hop revalidation、rebind fixture |
| resource exhaustion | pass/partial | crawl/page/byte/time bounds | browser process/memory と concurrent run 実負荷は未確認 | global concurrency/memory budget と cancellation |
| authentication / authorization | fail for external | run id only、tenant column なし | 外部公開で IDOR / cross-tenant | tenant-bound queries、403/404 tests、local profile 分離 |
| URL secret handling | fail | query 保持、DB/export 出力 | token/session leakage | raw fetch URL と redacted persistent URL を分離 |
| XSS / HTML output | pass/partial | diff escape、nav sanitizer、Markdown escape | future `ui.html(...sanitize=False)` regression | central safe renderer + malicious fixture |
| CSV injection | partial | ASCII formula prefix | Unicode whitespace/control、apostrophe依存、local path leak | OWASP boundary fixtures、artifact id、consumer guidance |
| prompt injection | partial | deep citation prompt に untrusted data/strict schema | suggestion/citation の grounded entailment なし | instruction/data separation + evidence validator |
| fixed vulnerability DB | partial | exploit text 非保持、固定 DB | DB open が read-only 強制でない、range coverage 不足 | `mode=ro`, `query_only`, checksum/version、range fixtures |
| dependency vulnerability | unverified | `pip check` pass | advisory/CVE scan 未実施 | pinned lock/SBOM と approved advisory scan evidence |
| logging | partial | 10MB×5 rotation | centralized secret redactor なし | URL/header/error redaction tests |
| artifact isolation | fail for external | global output dirs / run route | shared deploymentでtenant mixing | tenant prefix、authenticated download、retention policy |

## 6. 公式参照（2026-07-10 確認）

| 組織 | 文書 | URL | 今回の用途 |
|---|---|---|---|
| Nielsen Norman Group | 10 Usability Heuristics | https://www.nngroup.com/articles/ten-usability-heuristics/ | UX 10原則 |
| Nielsen Norman Group | Progressive Disclosure | https://www.nngroup.com/articles/progressive-disclosure/ | primary/secondary 情報設計 |
| W3C | WCAG 2.2 | https://www.w3.org/TR/WCAG22/ | AA 基準 |
| W3C | Understanding Status Messages | https://www.w3.org/WAI/WCAG22/Understanding/status-messages | status/progress 通知 |
| Google Search Central | Documentation updates | https://developers.google.com/search/updates | 2026-06-15 FAQ / llms.txt 更新 |
| Google Search Central | AI features and your website | https://developers.google.com/search/docs/appearance/ai-features | AI 機能に特別要件/保証なし |
| Google Search Central | Core Web Vitals | https://developers.google.com/search/docs/appearance/core-web-vitals | field metric 定義 |
| PageSpeed Insights | About PSI | https://developers.google.com/speed/docs/insights/v5/about | field/lab の区別 |
| Google Search Central | Speakable structured data | https://developers.google.com/search/docs/appearance/structured-data/speakable | beta/eligibility |
| OpenAI | Crawlers | https://developers.openai.com/api/docs/bots | bot purpose の分離 |
| OpenAI | Product feed spec | https://developers.openai.com/commerce/specs/file-upload/products | commerce 対象時の一次仕様 |
| OpenAI | Merchants | https://chatgpt.com/merchants/ | merchant 導線 |
| Perplexity | Perplexity crawlers | https://docs.perplexity.ai/docs/resources/perplexity-crawlers | provider bot 一次仕様 |
| Anthropic | Web crawler controls | https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler | provider bot 一次仕様 |
| OWASP | SSRF Prevention Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html | URL/IP/redirect 防御 |
| OWASP | CSV Injection | https://owasp.org/www-community/attacks/CSV_Injection | spreadsheet formula 境界 |
| OWASP | LLM Prompt Injection Prevention | https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html | prompt/data 分離 |

## 7. Release gates

- Local-only: F-06/F-07/F-08 の saved truth contract、F-01/F-02 の誤判定を閉じる。
- Browser accessibility claim: scanner dependency、WCAG 2.2 profile、HTML-only fallback 表示を閉じる。
- External/Azure: tenant/auth/artifact isolation、URL secret redaction を閉じるまで公開しない。
- AI/SEO 効果 claim: 公式基準日、根拠、観測条件がない定量因果表現を公開面へ出さない。

