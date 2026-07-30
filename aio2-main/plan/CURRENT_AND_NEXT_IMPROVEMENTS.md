# コトミガキ 改修計画 — 解像度と次のアクション

最終更新: 2026-04-06  
対象: `C:\tetie\aio2-main`

---

## 1. 今の解像度で問題ないか

**結論: 解像度はこのままでよい。** ただし「これからやる改修」の入口を 1 か所にまとめておくと運用しやすい。

### 1.1 完了済み計画の解像度

| 計画 | 粒度 | 状態 | 評価 |
|------|------|------|------|
| **PLAN2** | 6 phase、各 phase に 1 本の md（背景・修正内容・対象ファイル・完了条件） | P01–P06 完了 | コトメイクの puran6 phase と同程度。**十分**。 |
| **GEO/AIO 改善** | P01–P06、PROGRESS + 各 phase 詳細 | 完了 | 同上。 |

- 各 phase に「何を直すか」「どのファイルか」「完了条件」が書かれており、エージェントや開発者が追いかけやすい粒度になっている。
- これ以上細かくする必要はない（タスクを 1 行 1 件にするとかえって管理コストが増える）。

### 1.2 不足しているもの

- **「次の改修」が 1 か所にまとまっていない**
  - AGENTS.md は「STATUS_AND_IMPROVEMENTS.md に次のアクション」と書いているが、**STATUS_AND_IMPROVEMENTS.md は現行 aio2-main にはなく archive にのみ存在**する。
  - コードレビュー（review Phase 2–5）は archive にあり、未着手のまま。現行リポジトリからは参照しづらい。
- このため「次に何をやるか」を探すとき、WORKLOG を遡るか、archive を開く必要がある。

---

## 2. 次の改修候補（1 か所まとめ）

### 2.0 2026-04-13 UX/マーケティング監査 follow-up

- **ヒューリスティック監査 follow-up package**: `plan/ux_heuristic_audit_followup_2026-04-13/`
  - 入口: `README.md`
  - phase / gate / stop rule: `TASK.md`
  - 再開位置: `PROGRESS.md`
  - rollback 境界: `ROLLBACK.md`
  - 別ウインドウ開始 prompt: `EXECUTION_PROMPT.md`
- 対象:
  - input guardrails 強化
  - analysis 中 / 完了後の user control 回復
  - dashboard 上段の価値訴求化
  - saved workspace IA の軽量化
  - `実装・設定` の actionable / reference 分離
- 監査由来の主 finding:
  - 分析中キャンセル不能 + 完了後自動遷移
  - saved workspace の 6 タブ同列提示
  - dashboard 上段の説明過多
  - `実装・設定` の情報混在
  - 入力エラー予防の遅さ

### 2.1 現在の実装用計画パッケージ

- **SEO / LLMO coverage 拡張**: `plan/seo_llmo_coverage_2026-04-06/`
  - 入口: `README.md`
  - 実装順と gate: `TASK.md`
  - 再開位置: `PROGRESS.md`
  - 巻き戻し境界: `ROLLBACK.md`
  - 別ウインドウ実装用: `EXECUTION_PROMPT.md`
- 対象:
  - `hreflang` / `x-default` / `html lang`
  - mobile-first parity
  - Core Web Vitals の `LCP` / `CLS`
  - `X-Robots-Tag` / `max-image-preview` などの追加監査
  - crawlable links / anchor text の SEO 監査
  - page-type 別 schema 深掘り
  - image / video discoverability
  - OpenAI merchant feed / Perplexity WAF・IP allowlist readiness
- UI影響:
  - `SEO改善` / `技術補足` / `内部診断` / `サイトヘルス` タブの表示項目増加を前提に、phase 8 で summary-first のまま情報増加を吸収する。

以下を「これからやる場合の候補」として 1 本にまとめる。優先順は運用で決める。

### 2.2 STATUS_AND_IMPROVEMENTS 由来（archive の内容要約）

| 領域 | 推奨対応 | メモ |
|------|----------|------|
| **リーガル** | 業界分析のコンプライアンスに結合 HTML を渡す | `_generate_industry_analysis` に `combined_html_for_legal` 由来の soup を渡す。 |
| **リーガル** | 利用規約を業界分析のリンク検出に追加 | プライバシー・特商法・会社概要に加え「利用規約」「terms」等。 |
| **リーガル** | depth=0 でも優先ページを取得 | `get_crawl_strategy` で depth=0 のときも `priority_pages` を返し、取得数上限で cap。 |
| **PDF** | 入力データの保証 | `generate_seo_aio_pdf_report` 先頭で必須キーをチェックし、不足時は空 dict を代入。 |
| **PDF** | 空セクションの文言統一 | 「情報はありません」だけでなく短い説明文を追加。 |
| **UI** | ロール別タブ出し分け | 経営/運用/エンジニア/法務等で表示するタブを出し分け（一部は 2026-02-02 で実装済み）。 |

### 2.3 コードレビュー未着手分（archive: review/REVIEW_MASTER.md）

| Phase | 内容 | 状態 |
|-------|------|------|
| Phase 1 | 緊急セキュリティ修正（A-1〜A-4） | 完了 |
| Phase 2 | LLM 安全性・コスト制御（B-1〜B-4） | 未着手 |
| Phase 3 | パイプライン堅牢化（C-1〜C-5） | 未着手 |
| Phase 4 | アーキテクチャ改善（D-1〜D-4） | 未着手 |
| Phase 5 | 法務チェック強化（E-1〜E-4） | 未着手 |

- 詳細は `archive/20260207/aio2-main/review/REVIEW_MASTER.md` および PHASE2–5 の md を参照。
- 実施する場合は、本計画（plan/）に「レビュー対応 Phase N」として phase を追加し、PROGRESS で進捗管理すると解像度が揃う。

### 2.4 運用時の決め方

- **優先度**: リーガル検出・PDF の空セクション・UI のうち、障害や問い合わせが多いものから着手する。
- **粒度**: 上記の「推奨対応」1 件を 1 phase（または 1 タスク）にする程度で十分。PLAN2 の phase と同じ解像度でよい。
- **記録**: 着手したら `plan/PLAN2/PROGRESS.md` の後に「PLAN3」や `plan/next/` を設くか、WORKLOG に「次の改修 Phase N 着手」と書く。

---

## 3. 推奨アクション（運用側）

1. **AGENTS.md の参照を更新する**  
   「STATUS_AND_IMPROVEMENTS.md」→「plan/CURRENT_AND_NEXT_IMPROVEMENTS.md（次の改修候補はここにまとめた）」に変更する。archive の STATUS_AND_IMPROVEMENTS は履歴参照用としてパスを残してもよい。
2. **次にやる改修を決めたら**  
   上記 §2 のいずれかを phase 化し、plan/ に phase 用 md を 1 本追加してから着手する。解像度は PLAN2 の phase レベルでよい。
3. **もっと細かくする必要はない**  
   タスクを 1 行 1 件にしたり、サブタスクを増やしたりしなくてよい。phase 単位（背景・修正内容・対象ファイル・完了条件）で十分。

---

## 4. 参照

- 完了済み: `plan/PLAN2/PROGRESS.md`、`plan/geo_aio_improvement_2026/PROGRESS.md`
- 作業記録: `WORKLOG.md`
- 仕様: `ALGORITHM.md`、`AGENTS.md`
- 履歴: `archive/20260207/aio2-main/STATUS_AND_IMPROVEMENTS.md`、`archive/20260207/aio2-main/review/REVIEW_MASTER.md`
