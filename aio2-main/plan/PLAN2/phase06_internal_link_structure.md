# Phase 06: 内部リンク構造スコア

優先度: 🟢 低
状態: ✅ 完了
依存: P03（sitemap.xml解析）完了後が望ましい

---

## 背景・目的

現状、内部リンクは「カウント」のみ行われている（`core/seo/internal_graph.py`）。
AI検索・SEO 両面において、**サイト内リンク構造の品質**が重要：

- **孤立ページ（Orphan Page）**: 内部リンクゼロ → Google も AI もたどり着けない
- **ハブページ**: 多くのページからリンクされる重要ページ → 引用されやすい
- **リンク深度**: トップから何クリックで到達できるか → 深すぎると評価低下

### スコープ（実用的な最小実装）

- sitemap.xml から全 URL を取得（P03 で実装済みのものを活用）
- クロール済み4ページのリンク情報から孤立・ハブを推定
- サイトヘルスタブに「内部リンク健全性」セクションを追加

---

## 実装内容

### 変更1: `core/seo/internal_graph.py` — 孤立ページ・ハブ検出を追加

既存の `InternalLinkGraph` クラスを拡張する。
まず既存コードを確認してから実装すること（`get_summary()` の現状出力を把握する）。

```python
# 既存クラスに追加するメソッド

def get_health_report(self, all_known_urls: list = None) -> dict:
    """
    内部リンク構造の健全性レポートを返す。

    Args:
        all_known_urls: sitemap から取得した全 URL リスト（P03 の sampled_urls）

    Returns:
        {
            "total_analyzed_pages": int,    # クロールで取得したページ数
            "total_known_pages": int,        # sitemap から把握した総ページ数
            "orphan_count": int,             # 孤立ページ数（内部リンクなし）
            "orphan_ratio": float,           # 孤立比率 (0.0〜1.0)
            "hub_pages": List[str],          # 多くのリンクを受けるページ Top5
            "avg_depth": float,              # 平均リンク深度
            "health_score": float,           # 0〜100 の健全性スコア
            "diagnosis": str,                # 評価メッセージ
        }
    """
    linked_urls = set()
    for source, targets in self._links.items():  # 既存の _links dict を活用
        linked_urls.update(targets)

    analyzed = list(self._links.keys())
    orphans = [u for u in (all_known_urls or analyzed) if u not in linked_urls]
    orphan_ratio = len(orphans) / max(len(all_known_urls or analyzed), 1)

    # ハブページ: 最も多くリンクされているページ
    in_degree = {}
    for targets in self._links.values():
        for t in targets:
            in_degree[t] = in_degree.get(t, 0) + 1
    hub_pages = sorted(in_degree, key=lambda u: -in_degree[u])[:5]

    # 健全性スコア: 孤立比率が低いほど高スコア
    health_score = max(0.0, 100.0 - orphan_ratio * 100)

    if health_score >= 80:
        diagnosis = "内部リンク構造は良好です。"
    elif health_score >= 50:
        diagnosis = f"孤立ページが{len(orphans)}件あります。内部リンクを追加してください。"
    else:
        diagnosis = f"孤立ページが多数（{len(orphans)}件）。サイト構造の見直しを推奨します。"

    return {
        "total_analyzed_pages": len(analyzed),
        "total_known_pages": len(all_known_urls or analyzed),
        "orphan_count": len(orphans),
        "orphan_ratio": round(orphan_ratio, 3),
        "hub_pages": hub_pages,
        "health_score": round(health_score, 1),
        "diagnosis": diagnosis,
    }
```

### 変更2: `core/engine/orchestrator.py` — health_report を生成して結果に含める

```python
# analyze_url() 内の internal_link_summary 生成部分（L930付近）を拡張

internal_link_summary = None
link_health_report = None
try:
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    graph = InternalLinkGraph(url)
    graph.add_page(url, links)

    # クロール済み優先ページのリンクも追加
    for page_url, page_html in priority_pages_result.get("pages", {}).items():
        page_soup = BeautifulSoup(page_html, "html.parser")
        page_links = [a.get("href") for a in page_soup.find_all("a", href=True)]
        graph.add_page(page_url, page_links)

    internal_link_summary = graph.get_summary()

    # P06: 孤立ページ・ハブ検出
    all_known = (sitemap_info or {}).get("sampled_urls", [])
    link_health_report = graph.get_health_report(all_known_urls=all_known or None)

except Exception as e:
    logger.warning(f"内部リンク分析エラー: {e}")
    internal_link_summary = None
    link_health_report = None

# last_analysis_results に追加
"link_health_report": link_health_report,
```

### 変更3: `core/ui/tabs/health_tab.py` — 内部リンク健全性セクション追加

既存のサイトヘルスタブに新規セクションを追加する。
`render_health_tab()` の引数に `link_health_report` を追加する必要がある。
まず既存シグネチャを確認してから変更すること。

```python
# health_tab.py に追加するセクション
def _render_link_health(link_health: dict) -> None:
    if not link_health:
        return
    ui.label("内部リンク構造").classes("card-title")
    score = link_health.get("health_score", 0.0)
    diagnosis = link_health.get("diagnosis", "")
    orphan_count = link_health.get("orphan_count", 0)
    hub_pages = link_health.get("hub_pages", [])

    color = "green" if score >= 80 else ("amber" if score >= 50 else "red")
    with ui.row().classes("items-center gap-3"):
        ui.linear_progress(value=score/100, size="10px", show_value=False, color=color).classes("w-32")
        ui.label(f"{score:.0f}点").classes("card-sub font-bold")
    ui.label(diagnosis).classes("card-sub")

    if orphan_count > 0:
        ui.label(f"孤立ページ（内部リンクなし）: {orphan_count}件").classes("card-hint text-orange-600")
    if hub_pages:
        ui.label(f"ハブページ（多くリンクされているページ）:").classes("card-hint")
        for hp in hub_pages[:3]:
            ui.label(f"  {hp}").classes("card-hint text-blue-600")
```

---

## 対象ファイル

| ファイル | 変更箇所 |
|---------|---------|
| `core/seo/internal_graph.py` | `get_health_report()` メソッド追加 |
| `core/engine/orchestrator.py` | 優先ページのリンクも graph に追加 + `link_health_report` 生成 |
| `core/ui/tabs/health_tab.py` | `_render_link_health()` 追加 |
| `core/ui/panels.py` | health_tab 呼び出し時に `link_health_report` を渡す |

---

## 完了条件

- [ ] `py_compile` 全変更ファイルエラーなし
- [ ] `get_health_report(all_known_urls=[])` がエラーなく `health_score >= 0` を返す
- [ ] サイトヘルスタブに「内部リンク構造」セクションが表示される
- [ ] 孤立ページが0件のサイトで `health_score = 100.0` になる
- [ ] P03 の sitemap が取得できている場合は `total_known_pages > 0` になる
- [ ] WORKLOG.md 更新

---

## 注意事項

- **P03 完了前でも動作すること**: `all_known_urls=None` のとき、クロール済みページのみで判定する。
  sitemap がなくてもゼロ除算やクラッシュしないこと。
- `InternalLinkGraph._links` の構造を先に確認すること（dict の形式が不明なため）。
  `get_summary()` の戻り値を見て `_links` がどう管理されているか把握してから実装する。
- 孤立ページ検出の精度は限定的（クロール4ページのリンク情報のみ）。
  UIでは「推定値」であることを明示する（「※クロール4ページに基づく推定です」）。
- Wikipedia 等の超大規模サイトでは sitemap_urls が 100件サンプルのため、
  孤立率の精度は低い。これも UI で注記する。
