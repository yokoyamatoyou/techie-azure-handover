# AIOアルゴリズム仕様書

最終更新: 2026-03-29
対象ファイル: `core/aio_analyzer.py`, `core/scoring_engine.py`

---

## 1. 全体アーキテクチャ

```
URL入力
  │
  ├─ [SEO分析]  seo_analyzer → SEOスコア（0〜100）
  │
  └─ [AIO分析]  AIOContentAnalyzer.analyze()
       │
       ├─ Layer 1: hard gate / provider gate
       │    ├─ Google: Googlebot, noindex, nosnippet, max-snippet, data-nosnippet
       │    ├─ OpenAI Search: OAI-SearchBot
       │    ├─ Perplexity: PerplexityBot
       │    └─ Claude Search: Claude-SearchBot
       ├─ Layer 2: soft score
       │    ├─ PID
       │    ├─ HTML構造
       │    ├─ soft technical（HTTPS / 応答速度）
       │    ├─ E-E-A-T
       │    ├─ Citation readiness / Freshness / AEO
       │    ├─ Entity linking
       │    └─ GEO補助（TL;DR / 統計密度）
       └─ Layer 3: informational note
            ├─ llms.txt
            ├─ Google-Extended
            ├─ GPTBot / ChatGPT-User
            └─ ClaudeBot / Claude-User / CCBot

ScoringEngine.integrate()
  ├─ Intent係数α（内部ヒューリスティック）
  ├─ 通常業界ブースト
  ├─ 軽いヒューリスティック補正（寄生コンテンツ疑義のみ）
  ├─ YMYL注意喚起（点数乗算なし）
  ├─ GEOスコア計算（内部診断）
  └─ 統合スコア = SEOスコア × α + AIOスコア × (1-α)
```

---

## 2. AIO raw_score 計算式

### 2-A. 各コンポーネントスコアと重み

| コンポーネント | 変数名 | スケール | 重み | 扱い |
|---|---|---|---|---|
| 命題密度（PID） | `pid_score` | 0〜1 | 0.20 | soft score |
| HTML構造 | `structure_score` | 0〜1 | 0.15 | soft score |
| エンティティ重要度 | `entity_score` | 0〜1 | 0.12 | soft score |
| soft technical | `tech_score` | 0〜1 | 0.10 | soft score |
| 文中E-E-A-T | `eeat_normalized` | 0〜1 | 0.08 | soft score |
| 引用準備度 | `citation_score` | 0〜1 | 0.10 | soft score |
| 情報鮮度 | `freshness_score` | 0〜1 | 0.06 | soft score |
| AEOパターン | `aeo_score` | 0〜1 | 0.05 | soft score |
| 知識グラフ | `entity_linking_score` | 0〜1 | 0.04 | soft score |
| GEO（TL;DR） | `tldr_result["score"]` | 0〜5 | ÷5×0.05 | soft score |
| GEO（統計密度） | `stats_density["score"]` | 0〜10 | ÷10×0.05 | soft score |

補足:
- provider別の公開条件は raw score に加点しない
- `llms.txt`, `GPTBot`, `Google-Extended`, `CCBot`, `ClaudeBot` は raw score に入れない
- `raw_score` と `total_score` は現在同値で、`penalty_multiplier` は `1.0`

**raw_score 計算式（v2）**
```
eeat_normalized = combined_score / 10.0

raw_score = (
    pid_score            * 0.20 +
    structure_score      * 0.15 +
    entity_score         * 0.12 +
    tech_score           * 0.10 +
    eeat_normalized      * 0.08 +
    citation_score       * 0.10 +
    freshness_score      * 0.06 +
    aeo_score            * 0.05 +
    entity_linking_score * 0.04 +
    (tldr_score / 5.0)   * 0.05 +
    (stats_score / 10.0) * 0.05
) * 100
```

### 2-B. 調整係数

`core/aio_analyzer.py` 側では multiplicative penalty を実質廃止し、以下の扱いに変更した。

- `penalty_multiplier = 1.0`
- provider別の block / noindex / snippet 制御は `details["provider_readiness"]` に保持
- `llms.txt` や学習用 bot の扱いは `informational_notes` に保持

---

## 3. 各コンポーネントの詳細

### 3-1. 命題密度（PID）

**算出:** `calculate_pid(text)`

```
PID = 命題語数 / 総語数
```

命題語: 動詞・形容詞・形状詞など。体言のみの連続は命題として弱い。

### 3-2. HTML構造スコア

**算出:** `analyze_structure(html)`

| 項目 | 満点 | 条件 |
|---|---|---|
| セマンティックタグ | 0.20 | `<article>`,`<section>`,`<header>`,`<main>` を1要素ごとに+0.05（最大0.20） |
| 見出し階層 | 0.25 | H1=1個で+0.10、H2≥3で+0.10（H2≥1なら+0.05）、H3≥2で+0.05 |
| リスト | 0.12 | `<ul>/<ol>` を1要素ごとに+0.03（最大0.12） |
| テーブル | 0.08 | `<table>` を1要素ごとに+0.04（最大0.08） |
| FAQ / Q&A 可視構造 | 0.15 | 「よくある質問」「FAQ」「Q:」等の可視テキストパターン |
| JSON-LD | 0.00 | **存在は保持するが、構造スコアへは直接加点しない** |

補足:
- FAQPage schema そのものを一般加点しない
- JSON-LD は `has_json_ld` / `eeat` / `schema_validation` で保持し、補助シグナルとして扱う

### 3-3. soft technical スコア

**算出:** `check_technical_aio(base_url, response_time_ms)`

| 項目 | 加点 | 条件 |
|---|---|---|
| HTTPS | +0.25 | URLが `https://` |
| 応答速度 | +0.50 | `<500ms` で最大、`>2000ms` で減衰 |
| ベースライン | +0.25 | fail-open |
| llms.txt | +0.00 | informational note のみ |
| bot許可 | +0.00 | provider gate のみ |

### 3-4. provider readiness

**算出:** `assess_provider_readiness(soup, tech_results, structure_results, inline_eeat)`

返り値は numeric score ではなく、providerごとの `status / official_checks / heuristic_notes`。

#### Google

| 種別 | 判定対象 | ラベル |
|---|---|---|
| 公式要件 | `Googlebot` | `Googlebot のクロール許可` |
| 公式要件 | `noindex` | `noindex が無効` |
| 公式要件 | `nosnippet` | `nosnippet が無効` |
| 公式に方向性あり | `max-snippet` | `max-snippet 制御` |
| 公式に方向性あり | `data-nosnippet` | `data-nosnippet 利用` |
| ヒューリスティック | `JSON-LD`, `E-E-A-T` | `heuristic_notes` |

#### OpenAI Search / Perplexity / Claude Search

| provider | 公式 gate |
|---|---|
| OpenAI Search | `OAI-SearchBot` |
| Perplexity | `PerplexityBot` |
| Claude Search | `Claude-SearchBot` |

#### informational note

- `llms.txt`
- `Google-Extended`
- `GPTBot`
- `ChatGPT-User`
- `Claude-User`
- `ClaudeBot`
- `CCBot`

### 3-5. 文中E-E-A-T検出（P02: 日本語対応）

**算出:** `detect_inline_eeat(text, soup, json_ld_eeat)`

JSON-LDに依存せず、日本語本文から資格・著者明示・組織・一次情報シグナルを正規表現で検出する。

### 3-6. TL;DR冒頭要約検出（P03）

**算出:** `detect_tldr_summary(text, soup)`

先頭2000字を対象に、明示ラベル・冒頭箇条書き・最初の段落長を評価する。

### 3-7. 統計・数値密度（P03）

**算出:** `calculate_statistics_density(text)`

数値・単位・比較表現・調査出典・引用表記を検出し、`density_per_1k` を算出する。

---

## 4. GEOスコア（内部診断）

**算出:** `ScoringEngine.integrate()` 内

```
geo_score_100 = min(100.0,
    (tldr_score  / 5.0)  * 40.0 +
    (stats_score / 10.0) * 35.0 +
    (eeat_score  / 10.0) * 25.0
)
```

注意:
- `geo_score` は Google / OpenAI / Perplexity / Claude の公式条件ではない
- UIでは「内部診断（GEO）」として表示する

---

## 5. Intent係数α（SEO/AIOバランス）

**定義:** `INTENT_ALPHA` in `scoring_engine.py`

| クエリ意図 | α (SEO比率) | AIO比率 | 根拠ラベル |
|---|---|---|---|
| transactional | 0.7 | 0.3 | 内部ヒューリスティック |
| informational | 0.2 | 0.8 | 内部ヒューリスティック |
| navigational | 0.8 | 0.2 | 内部ヒューリスティック |
| unknown | 0.5 | 0.5 | 内部ヒューリスティック |

補足:
- 数値係数に official primary source の直接根拠はない
- 今回は維持し、文書上で internal heuristic と明示する

---

## 6. 業界ブースト / YMYL / penalty

### 6-A. 通常業界ブースト

| 業界キー | SEO倍率 | AIO倍率 |
|---|---|---|
| b2b saas | 1.0 | 1.2 |
| real estate | 1.1 | 1.1 |
| ecommerce | 1.3 | 1.0 |

### 6-B. YMYL

- `YMYL_KEYWORDS` と `seo_results.eeat.is_ymyl` を併用して YMYL context を判定する
- **YMYL の数値乗算は適用しない**
- `is_ymyl_context and aio eeat_score < 4.0` の場合は warning / heuristic note を出す

### 6-C. 軽い penalty

| フラグ | AIO倍率 | 根拠ラベル |
|---|---|---|
| `parasitic_content_flag` | ×0.85 | 内部ヒューリスティック |

---

## 7. スコア正規化・スケール一覧

| スコア | スケール | UI表示 |
|---|---|---|
| AIO raw_score | 0〜100 | /100 |
| AIO total_score | 0〜100 | /100 |
| PID | 0〜1 | ×100 |
| 構造・技術・エンティティ | 0〜1 | ×100 |
| E-E-A-T（文中） | 0〜10 | /10 |
| TL;DR | 0〜5 | /5 |
| 統計密度 | 0〜10 | /10 |
| GEOスコア | 0〜100 | /100（内部診断） |
| provider readiness | `pass / warn / fail` | status 表示 |
| 統合スコア | 0〜100 | /100 |

---

## 8. データフロー（主要キー）

```
AIOContentAnalyzer.analyze()
├─ scores["eeat"]             → {"score": combined_score, "detail": inline_eeat}
├─ scores["geo_tldr"]         → {"score": tldr_score, "detail": tldr_result}
├─ scores["geo_stats"]        → {"score": stats_score, "detail": stats_density}
├─ details["inline_eeat"]     → {signals, combined_score, has_json_ld_eeat}
├─ details["geo_tldr"]        → {score, has_explicit_tldr, has_early_bullets, advice}
├─ details["geo_stats"]       → {score, stats_count, density_per_1k, density_level}
└─ details["provider_readiness"]
   ├─ google / openai_search / perplexity / claude_search
   │  ├─ status
   │  ├─ official_checks
   │  └─ heuristic_notes
   └─ informational_notes

ScoringEngine.integrate()
├─ "integrated_score"   → SEO×α + AIO×(1-α)
├─ "applied_penalties"  → 軽い penalty のみ
├─ "heuristic_notes"    → YMYL 等の内部メモ
├─ "geo_score"          → 0〜100（内部診断）
└─ "geo_breakdown"      → {tldr, stats_density, eeat}
```

---

## 9. パラメータ調整履歴

| 日付 | パラメータ | 旧値 | 新値 | 根拠 |
|---|---|---|---|---|
| 2026-02-27 | INTENT_ALPHA.informational | 0.3 | 0.2 | 内部ヒューリスティック調整 |
| 2026-02-27 | INTENT_ALPHA.transactional | 0.8 | 0.7 | 内部ヒューリスティック調整 |
| 2026-02-27 | INTENT_ALPHA.navigational | 1.0 | 0.8 | 内部ヒューリスティック調整 |
| 2026-03-29 | YMYL数値補正 | 1.2 / 0.7 / 0.5 | 廃止 | 公式方向性と内部注意喚起を分離し、点数乗算を停止 |
| 2026-03-29 | provider別 numeric 推定 | あり | 廃止 | 公式公開条件と内部推定を混同しないため |
| 2026-03-29 | parasitic_content penalty | 0.7 | 0.85 | 根拠が薄いため穏やかな内部ヒューリスティックへ変更 |

次回調整の目安: 統計密度閾値（3.0/千字等）は実ユーザーデータ収集後に `plan/` 配下で記録。

---

## 10. 主要ファイルマップ

| ファイル | 役割 |
|---|---|
| `core/aio_analyzer.py` | AIOContentAnalyzer クラス（全コンポーネント分析） |
| `core/scoring_engine.py` | ScoringEngine（統合スコア・YMYL・GEO） |
| `core/knowledge_graph.py` | エンティティカテゴリ重み・正規化関数 |
| `core/wikidata_client.py` | Wikidata QIDルックアップ（30日キャッシュ） |
| `core/aio_suggestions.py` | プラットフォーム別アドバイステンプレート |
| `core/ui/tabs/aio_tab.py` | AIOタブUI（GEO・E-E-A-T・プラットフォーム表示） |
| `core/ui/reports/executive_summary.py` | 経営サマリー（統合/SEO/AIO/GEOスコード） |
| `plan/geo_aio_improvement_2026/` | 改善計画・フェーズ詳細・進捗管理 |
