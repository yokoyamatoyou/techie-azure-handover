# コトミガキ ALGORITHM

最終更新: 2026-04-20
対象: `C:\tetie\aio2-main`

このドキュメントは、コトミガキ（SEO/AIO分析）の現行アルゴリズム仕様を管理する正本です。  
実装の一次参照は `core/engine/orchestrator.py`, `core/aio_analyzer.py`, `core/scoring_engine.py`。

## 1. 目的

- Webページを対象に、SEO・AIO・法務・サイトヘルスを統合診断する
- スコアだけでなく、実行可能な改善提案と UI / CSV 出力を提供する

## 2. 分析フロー（概要）

1. 取得・前処理  
URLをクロールし、本文・構造・メタデータを抽出。

2. SEO分析  
SEO系指標を算出し `seo_results` を生成。

3. AIO分析（`AIOContentAnalyzer.analyze()`）  
主に以下を評価:
- PID（命題密度）
- HTML構造（見出し/セマンティック/FAQ）
- エンティティ重要度
- Soft technical（HTTPS / 応答速度など）
- 文中E-E-A-T
- Citation readiness
- Contextual freshness
- AEO pattern
- Entity linking
- GEO補助（TL;DR、統計密度）
- provider別の公開条件チェック（Google / OpenAI Search / Perplexity / Claude Search）
- informational note（llms.txt, GPTBot, Google-Extended, CCBot など）

4. AIO raw score 計算  
`core/aio_analyzer.py` の重み付き合算を実施。

5. 統合スコア計算（`ScoringEngine.integrate`）  
- intent係数 `alpha` を適用（SEO/AIO配分）
- 業界ブースト（通常業界のみ。YMYL数値補正は行わない）
- 軽いヒューリスティック補正（寄生コンテンツ疑義のみ）
- YMYLは warning / note として扱い、点数乗算しない
- `integrated_score = seo_score * seo_weight + aio_score_after_penalty * aio_weight`

6. レポート化  
UI（NiceGUI）と saved snapshot / CSV 向け形式へ整形し、改善アクションを出力。

## 2.1 Current owner / 責務境界（2026-03-09）

- current engine owner: `core/engine/orchestrator.py::SEOAIOAnalyzer.analyze_url`
- UI shell: `nicegui_app.py`
- UI向け分析実行・履歴保存・saved detail rehydrate の application owner: `core/application/analysis_run_service.py`
- CSV export owner: `core/application/csv_export_service.py`
- monitoring persistence owner: `core/monitoring/history_store.py`
- panel dependency context owner: `core/ui/panel_context.py`
- panel rendering owner: `core/ui/panels.py`
- `SEOAIOAnalyzer._get/_load/_save_monitoring_history()` は monitoring store の互換 wrapper

## 2.2 出力経路

- 画面表示は `nicegui_app.py` が dashboard と `/runs/{run_id}` route を担当し、描画は `core/ui/dashboard.py` と `core/ui/panels.py` が担当する。
- 履歴DB保存は `core/storage/database.py`、saved detail の result file / snapshot JSON 保存は `core/application/analysis_run_service.py` を正本とする。
- CSV出力は `core/application/csv_export_service.py` が担当する。
- AIO monitoring JSON 保存は `core/monitoring/history_store.py` を正本とする。

## 2.3 FAQ提案生成（2026-04-20）

- FAQ未検出時の提案生成 owner は `core/application/analysis_run_service.py`。
- 現行は「固定テンプレートをそのまま表示」ではなく、以下の 2 段構成で生成する。
  1. `industry / site_type / platform / legal_notes / citation_phrases / summary_improvements / target_audience_clues` などから FAQ候補を採点する
  2. 採用候補を `business_goal / page_focus / audience_clues` に応じて文面リライトし、`persona_label` と `presentation_mode=contextualized` を付与する
- ペルソナは単純な `if/elif` ではなく、`page_title / meta_description / headings / context_text / url slug / audience_clues / site_type / industry / business_goal` を信号として候補を採点する。
- URL slug は補助信号として扱い、`b2b / enterprise / pricing / clinic / shop` などの語を低ウェイトで加点する。
- 特殊ドメイン (`or.jp / go.jp / lg.jp / ac.jp / ed.jp`) は `domain_profile` として別扱いし、公共・団体寄りの prior と FAQ guardrail に使う。
- 飲食・来訪型ページは `LMO` signal として `アクセス / 営業時間 / 予約 / 現地設備` を優先し、`来訪前ユーザー向け` のペルソナ候補を別に持つ。
- EC FAQ は raw `is_ec` のみで出さず、`ec_detection_reason` と `domain_profile / lmo_profile` を使った guardrail で `effective_is_ec` を決めてから出し分ける。
- 公共・団体系では `public_services / public_eligibility / public_application` を優先候補に加え、`LMO` の `access / hours / reservation` は補助候補へ後退させる。
- 生成根拠は `writing_workspace.faq_debug` として snapshot JSON に保存する。
- `faq_debug` には少なくとも `strategy / persona / context / candidates / selected_count` を保持し、`persona` 内に `confidence / source / candidates` も保持して saved workspace の「文章改善」から確認できるようにする。
- fallback は残すが、具体候補がある場合は generic glossary を優先しない。

## 3. AIO raw score（v2）

`core/aio_analyzer.py` の実装に従い、以下を 0〜1 正規化で加重合算:

- PID: 0.20
- Structure: 0.15
- Entity: 0.12
- Tech: 0.10
- Inline E-E-A-T: 0.08
- Citation readiness: 0.10
- Freshness: 0.06
- AEO patterns: 0.05
- Entity linking: 0.04
- GEO TL;DR: 0.05
- GEO stats density: 0.05

補足:
- raw score は soft score 層のみで構成する
- provider別の公開条件は raw score に加点しない
- `llms.txt`, `Google-Extended`, `GPTBot`, `ClaudeBot`, `CCBot` は informational note として保持する
- `INTENT_ALPHA` の数値自体は official primary source の係数ではなく、内部ヒューリスティックとして維持する

注: 重みや式の更新時は、コードと本ファイルを同時更新する。

## 4. GEO score（統合側）

`core/scoring_engine.py` で100点換算:
- TL;DR: 40%
- 統計密度: 35%
- E-E-A-T: 25%

補足:
- `geo_score` は内部診断値であり、provider gate や Google の公式要件そのものではない
- UI では「内部診断（GEO）」として表示する

## 4.1 YMYL補正とペナルティ条件

- YMYL業界判定は `core/scoring_engine.py::YMYL_KEYWORDS` と `seo_results.eeat.is_ymyl` を併用する。
- YMYL は **点数乗算しない**。`aio_score` / `integrated_score` に対して `1.2x / 0.7x / 0.5x` の補正は適用しない。
- 現行は `is_ymyl_context and aio eeat_score < 4.0` の場合に warning / heuristic note を出す。
- 目的:
  - 日本語ページでの過剰減点を避ける
  - 「公式に方向性があること」と「内部ヒューリスティックによる注意喚起」を分離する

## 4.2 penalty / note の扱い

- hard gate:
  - Google: `Googlebot`, `noindex`, `nosnippet`, `max-snippet`, `data-nosnippet`
  - OpenAI Search: `OAI-SearchBot`
  - Perplexity: `PerplexityBot`
  - Claude Search: `Claude-SearchBot`
- soft score:
  - AIO raw score の 11指標
- informational note:
  - `llms.txt`
  - `Google-Extended`
  - `GPTBot`
  - `ChatGPT-User`
  - `Claude-User`
  - `ClaudeBot`
  - `CCBot`

## 4.3 provider別出力

- `core/aio_analyzer.py` は provider別の numeric score / overall score を出さない
- 代わりに `details.provider_readiness` として次を返す
  - `status`: `pass / warn / fail`
  - `official_checks`: 公式に確認できた条件
  - `heuristic_notes`: 内部ヒューリスティック
  - `informational_notes`: 任意メモ / 情報目的

## 5. 変更管理

- スコア式や重みを変更した場合は本ファイルを必ず更新。
- engine / ui / report / persistence の owner を変更した場合も本ファイルを更新。
- 変更履歴は `aio2-main/WORKLOG.md` に追記。
- 全体導線に影響する場合のみ `C:\tetie\ALGORITHM.md` / `C:\tetie\AGENTS.md` も更新。
