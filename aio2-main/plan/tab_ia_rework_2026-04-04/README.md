# tab_ia_rework_2026-04-04

`aio2-main` の分析後 UI を、認知負荷を上げずに「見る場所が一意に分かる」構成へ再設計する実装パッケージ。  
この package は **タブ名変更だけ** ではなく、`live workspace` / `saved workspace` / `snapshot 保存粒度` をまとめて見直す。

## Objective

- 上位タブを平易な 5 タブに再編する
- `各AIの通過状況` を 1 か所に集約する
- `文章改善` と `実装・設定` の責務を分離する
- `saved workspace` でも live と同じ判断ができる保存粒度に広げる
- FAQ / llms.txt / 構造化データの扱いを、最新の公式情報に沿って hard / soft / informational に整理する

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\README.md`
4. `C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\TASK.md`
5. `C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\PROGRESS.md`
6. `C:\tetie\aio2-main\ALGORITHM.md`
7. `C:\tetie\aio2-main\WORKLOG.md`

## Decision Summary

- 採用タブ名:
  - `サマリー`
  - `やること`
  - `文章改善`
  - `実装・設定`
  - `履歴と比較`
- `法務・表示` は常設タブにしない
  - 法務 issue が 1 件以上ある場合のみ `実装・設定` 内の強調セクションで表示
- `各AIの通過状況` は `実装・設定` のみに置く
  - `サマリー` には件数だけ置く
- FAQ は 2 系統に分ける
  - 読者向け FAQ 内容案: `文章改善`
  - FAQPage / JSON-LD / 整合チェック: `実装・設定`
- `llms.txt` は `実装・設定` の任意セクションだけに置く
  - `サマリー` や `やること` に再掲しない

## Current Findings

現行 UI は、次の理由で「どこを見ればよいか」が曖昧になっている。

- live 画面に上位タブ `現状 / 改善方法 / 詳細 / 内部診断` があり、その中の `詳細` にさらに `引用候補 / SEO / AIO / 業界 / サイトヘルス / 比較` がある
  - owner: `core/ui/panels.py`
- saved workspace では `概要 / AI認識改善 / SEO改善 / 履歴 / 実装メモ` の別体系になっている
  - owner: `core/ui/panels.py`
- provider 状態が `AIO`、技術チェック、saved workspace に重複して出る
  - owner: `core/ui/tabs/aio_tab.py`, `core/ui/panels.py`
- saved workspace の snapshot は provider 詳細を十分に保存しておらず、`official_checks` / `heuristic_notes` / `informational_notes` の粒度が落ちる
  - owner: `core/application/analysis_run_service.py`

## IA Principles

- nested tabs をやめる
- タブ名は抽象語ではなく、読む前に内容が予測できる語にする
- 同じ情報を 2 タブに置かない
- 最初に見せるのは「判断」と「次の行動」だけに絞る
- 長文は省略記号で切らず、初期表示を短くして展開で全文を見せる
- fixed / reference 情報は primary surface から後退させる
- live / saved で同じタブ体系を使う

## Latest Validation For LLMO / AI Search Conditions

### 1. Hard gate として維持する項目

以下は **UI 上も `公開条件` として扱ってよい**。

| 項目 | 判定 | 扱い |
|------|------|------|
| `noindex` | hard | Google Search / AI features の公開不可 |
| `nosnippet` / `max-snippet` / `data-nosnippet` | hard | Google の AI features を含む snippet 制御 |
| `Googlebot` crawl 可否 | hard | Google の crawl 条件 |
| `OAI-SearchBot` | hard | ChatGPT search 表示条件 |
| `PerplexityBot` | hard | Perplexity index 条件 |
| `Claude-SearchBot` | hard | Claude search / web result 用条件 |

補足:

- Google は AI features も Search の一部として扱い、制御は `Googlebot` と snippet 制御を使う
- OpenAI は Search 表示に `OAI-SearchBot` を使い、`ChatGPT-User` は Search inclusion 判定には使わない
- Perplexity は `PerplexityBot` が robots.txt を尊重すると案内している
- Anthropic は `Claude-SearchBot` / `ClaudeBot` / user-triggered fetch を分けて説明している

### 2. Informational に下げる項目

以下は **表示してよいが hard pass/fail に混ぜない**。

| 項目 | 判断 | 理由 |
|------|------|------|
| `llms.txt` | informational | 主要プロバイダの公式要件としては確認できない |
| `Google-Extended` | informational | Google Search の掲載可否・順位シグナルではない |
| `GPTBot` | informational | 学習利用の opt-out 管理。Search inclusion とは別 |
| `ClaudeBot` | informational | 学習/収集の bot。Claude Search とは別 |
| `CCBot` | informational | Common Crawl 系の収集管理。直接の検索公開条件ではない |

### 3. Soft heuristic として残す項目

以下は **内部ヒューリスティックとして残してよいが、公式条件としては言わない**。

| 項目 | 判断 | 実装方針 |
|------|------|------|
| Answer-first 要約 | keep | `文章改善` と `サマリー` に反映 |
| FAQ / Q&A 本文 | keep | 読者理解と AI 抽出しやすさの両面で有効 |
| 比較表 / 定義文 / 数値根拠 | keep | 引用候補とセットで扱う |
| 著者 / 会社 / 一次情報の明示 | keep | E-E-A-T 補強の内部基準として維持 |
| JSON-LD / schema | keep with downgrade | 補助シグナルとして扱い、単独 pass/fail にしない |

### 4. FAQPage の扱い

- FAQ 本文は今後も強く使ってよい
- ただし `FAQPage` structured data は、Google の rich result 対象が well-known government / health sites に大きく限定されている
- したがって `FAQPage 実装 = 一般サイトの公開条件` とは扱わない
- UI では
  - `文章改善`: FAQ 内容案
  - `実装・設定`: FAQPage / JSON-LD / 本文との整合
  に分ける

## Recommended Tab Spec

### 1. サマリー

役割:

- まず何を判断すべきかを 30 秒で把握する面

表示するもの:

- 総合スコア / SEO / AI検索 / 法務
- 優先度バッジ
- `最優先3件`
- `AI公開条件: 要対応 n件`
- `法務・表示: 要対応 n件`
- 前回比の要約

表示しないもの:

- provider 名ごとの詳細
- FAQ 本文
- llms.txt 説明
- 一般論のヘルプ

UI rule:

- 数字 + バッジ + 短い 1 行所見を中心にする
- 長文説明は置かない

### 2. やること

役割:

- 担当者ごとの実務タスクを一番見やすくする面

表示するもの:

- action の統合一覧
- `担当` チップ: `運用 / 制作 / エンジニア / 法務`
- `優先度` チップ
- `影響` と `工数` の短いメモ
- クリック展開で手順

表示しないもの:

- provider hard gate の詳細表
- FAQ の全文
- 参考用 glossary

UI rule:

- 初期表示は 6〜8 件まで
- area ごとの分断をやめ、同じ action list に統合する
- area は色ではなく chip で示す

### 3. 文章改善

役割:

- 書き換える内容だけを集約する面

表示するもの:

- タイトル改善案
- ディスクリプション改善案
- 本文リライト案
- AI引用されやすい文章構造
- 既存 FAQ 検出
- FAQ 提案
- 比較表 / 追加見出し / 定義文の提案

FAQ rule:

- 既存 FAQ があれば先に出す
- なければ issue / 業界 / EC テンプレートから 3〜5 件を提案する
- `FAQ 内容` と `FAQPage 実装` は分離する

### 4. 実装・設定

役割:

- エンジニアに渡すべき内容を 1 面に集める

表示するもの:

- `各AIの通過状況` の一覧
- provider 別:
  - status
  - summary
  - official_checks
  - heuristic_notes
  - informational_notes
- crawl / index / snippet 制御
- robots / noindex / nosnippet / max-snippet / data-nosnippet
- JSON-LD / schema
- FAQPage 整合チェック
- llms.txt
- platform_guidance
- 技術アクション
- 必要ならコードスニペット

表示しないもの:

- タイトルや本文のリライト案
- Top 3 action の再掲

UI rule:

- 先頭に provider matrix を置く
- 下に `クロール`, `表示制御`, `構造化`, `AI向け案内`, `CMS別手順` の 5 ブロックを置く
- 赤黄緑の意味を固定する

### 5. 履歴と比較

役割:

- 過去との差分と競合比較だけを扱う面

表示するもの:

- 前回比
- 同一URLの履歴
- competitor compare
- run metadata

UI rule:

- 比較がない時は空状態を明示する
- `履歴だけ` と `競合比較` を 1 面にまとめる

## Current To New Mapping

| 現行 | 新タブ | 備考 |
|------|--------|------|
| `現状` | `サマリー` | URL 固有所見を 3〜4 件まで圧縮 |
| `改善方法` | `やること` + `文章改善` + `実装・設定` | 1 面に混在させない |
| `詳細 > 引用候補` | `文章改善` | 引用候補と FAQ を隣接させる |
| `詳細 > SEO` | `文章改善` と `実装・設定` に分割 | 文案は前者、設定系は後者 |
| `詳細 > AIO` | `実装・設定` | provider 詳細の唯一面 |
| `詳細 > サイトヘルス` | `実装・設定` | 実装・設定寄りだけ残す |
| `詳細 > 比較` | `履歴と比較` | 常設ではなく条件表示 |
| `内部診断` | 原則廃止 | 残すなら `実装・設定` 内の fold |
| saved `AI認識改善` | `やること` と `文章改善` | action と文案を分離 |
| saved `SEO改善` | `文章改善` | リライト案の primary owner |
| saved `実装メモ` | `実装・設定` | provider / llms / platform の owner |

## FAQ Handling Policy

FAQ は消さず、むしろ位置を正す。

- `文章改善`
  - `既存FAQ検出`
  - `FAQ提案`
  - `比較するとどう違うか`
  - `導入前に何を確認すべきか`
  - `料金 / 納期 / 対応範囲 / セキュリティ / 実績`
- `実装・設定`
  - FAQPage 有無
  - JSON-LD と本文の整合
  - schema source 件数
  - suspicious FAQ の警告

最低でも拾う対象:

- `results.faq_detection.items`
- `results.faq_detection.validation`
- `results.schema_existing.types`
- `panels._build_faq_suggestions()`
- `term_glossary.get_ec_faq_templates()`

## Snapshot / Persistence Upgrade

saved workspace の情報量不足は UI ではなく snapshot の問題が大きい。  
次を snapshot に追加する。

### 必須追加

- `summary_workspace`
  - `headline_metrics`
  - `priority_counts`
  - `blocking_issues`
- `task_workspace`
  - action の統合配列
  - `owner`
  - `priority`
  - `effort`
  - `impact`
- `writing_workspace`
  - title rewrites
  - description rewrites
  - body rewrites
  - citation phrases
  - faq detection summary
  - faq suggestions
- `implementation_workspace`
  - provider full payload
  - google_controls
  - llms notes
  - schema summary
  - platform guidance
  - legal display notes
  - technical actions
- `comparison_workspace`
  - previous diff
  - competitor summary

### 明示的に保存する粒度

- `official_checks` は label / status / detail まで保持
- `heuristic_notes` はそのまま保持
- `informational_notes` は label / message を保持
- FAQ は `question / answer / source / validation` を保持
- snapshot だけで `saved workspace` を再構成できる状態を目指す

## Removal Targets

- `詳細` の中の nested tabs
- `内部診断` の独立タブ
- provider 状態の重複表示
- `llms.txt` の複数箇所表示
- 固定 FAQ / 一般論の常設表示
- `ここでは要点だけを短く表示します` のようなメタ説明
- `実装メモ` のような抽象ラベル

## Visual Rules

- 1 タブ 1 目的
- 1 カード 1 判断
- 1 行目で意味が分かる見出しだけ残す
- 本文は `2〜4 行 + 展開`
- 説明文で補うのではなく、badge / chip / status row / before-after で見せる
- `赤 = 要対応`, `黄 = 注意`, `緑 = 通過`, `灰 = 任意/参考` を全タブで固定
- デフォルト開閉:
  - `サマリー`: 全閉不要
  - `やること`: 先頭 3 件だけ半展開
  - `文章改善`: before/after は開く、長い理由は閉じる
  - `実装・設定`: fail / warn だけ開く

## Acceptance Criteria

- live / saved の上位タブが同一である
- provider 状態は `実装・設定` でしか見えない
- FAQ 内容案は `文章改善`、FAQPage は `実装・設定` へ分離されている
- `サマリー` が 30 秒以内で読める
- 途中省略だけで意味が落ちる表示が残っていない
- `saved workspace` でも `official_checks` と `heuristic_notes` が見える
- `llms.txt` は任意項目としてだけ表示される
- `Google-Extended` は Search 公開条件として扱われていない

## External Sources

- Nielsen Norman Group, 10 usability heuristics  
  https://www.nngroup.com/articles/ten-usability-heuristics/
- Nielsen Norman Group, Progressive Disclosure  
  https://www.nngroup.com/articles/progressive-disclosure/
- Microsoft, Tabs guidance  
  https://learn.microsoft.com/en-us/windows/win32/uxguide/ctrl-tabs
- Google Search Central, AI features and your website  
  https://developers.google.com/search/docs/appearance/ai-features
- Google Search Central, FAQ structured data  
  https://developers.google.com/search/docs/appearance/structured-data/faqpage
- Google crawling docs, Google-Extended  
  https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
- Google Search Central, guidance on generative AI content  
  https://developers.google.com/search/docs/fundamentals/using-gen-ai-content
- OpenAI, Overview of OpenAI crawlers  
  https://developers.openai.com/api/docs/bots
- Anthropic Help Center, web crawling and bot controls  
  https://support.claude.com/fr/articles/8896518-anthropic-effectue-t-il-un-crawling-des-donnees-sur-le-web-et-comment-les-proprietaires-de-sites-peuvent-ils-bloquer-le-crawler
- Perplexity Help Center, robots.txt compliance  
  https://www.perplexity.ai/help-center/zh-CN/articles/10354969-perplexity-%E5%A6%82%E4%BD%95%E9%81%B5%E5%BE%AA-robots-txt
- llms.txt project reference  
  https://llmstxt.org/
