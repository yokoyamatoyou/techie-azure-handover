# Phase 03: sitemap.xml メタデータ解析

優先度: 🟡 中
状態: ✅ 完了

---

## 背景・目的

現状、入力URLのページとその下層4ページのみを分析しているため、
サイト全体の規模や構造が把握できない。

**目標:** sitemap.xml を「コンテンツ取得なし・URLとメタデータのみ」で解析し、
- サイト全体のページ数
- 更新頻度（lastmod から推定）
- URL構造（カテゴリ分布）

を経営サマリーに表示する。コンテンツ取得上限（4ページ）は**変更しない**。

### サイト規模別の設計方針

| 規模 | sitemap URL数 | 処理方針 |
|------|-------------|---------|
| 小 | ≤100 | 全件解析 |
| 中 | ≤1,000 | 全件解析（メタデータのみ） |
| 大 | ≤10,000 | 上位500件（lastmod降順） |
| 超大 | >10,000 | 100件サンプリング + 警告表示 |

Wikipedia 等の超大規模サイト → 「大規模サイト: 分析はサンプル4ページです」と表示して終了。

---

## 実装内容

### 新規ファイル: `core/sitemap_analyzer.py`

```python
# -*- coding: utf-8 -*-
"""sitemap.xml メタデータ解析（コンテンツ取得なし）"""

import re
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET

SITEMAP_FETCH_TIMEOUT = 10.0
SITEMAP_MAX_BYTES = 5 * 1024 * 1024   # 5MB 上限
LARGE_SITE_THRESHOLD = 10_000
SAMPLE_LIMIT_LARGE = 100

def fetch_sitemap_urls(base_url: str) -> Dict[str, Any]:
    """
    sitemap.xml を取得し URL リストとメタデータを返す。
    コンテンツ（ページ本文）は取得しない。

    Returns:
        {
            "total_urls": int,
            "sampled_urls": List[str],   # 分析候補（lastmod降順で最大100件）
            "lastmod_dates": List[str],
            "update_frequency": str,     # "毎日" | "週1〜2回" | "月1〜2回" | "低頻度"
            "url_categories": Dict[str, int],  # パスセグメント別カウント
            "is_large_site": bool,
            "warning": Optional[str],
            "error": Optional[str],
        }
    """
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    sitemap_url = f"{root}/sitemap.xml"

    try:
        resp = requests.get(
            sitemap_url,
            timeout=SITEMAP_FETCH_TIMEOUT,
            headers={"User-Agent": "Kotomagaki-Bot/1.0"},
            stream=True,
        )
        if resp.status_code != 200:
            return {"error": f"sitemap.xml が見つかりません（{resp.status_code}）", "total_urls": 0}

        content = b""
        for chunk in resp.iter_content(1024 * 64):
            content += chunk
            if len(content) > SITEMAP_MAX_BYTES:
                break

        return _parse_sitemap_xml(content.decode("utf-8", errors="replace"), root)

    except Exception as e:
        return {"error": str(e)[:200], "total_urls": 0}


def _parse_sitemap_xml(xml_text: str, root_url: str) -> Dict[str, Any]:
    """XML をパースして URL リストとメタデータを抽出"""
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    try:
        tree = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return {"error": f"XMLパースエラー: {e}", "total_urls": 0}

    entries = []
    tag = tree.tag.lower()

    # sitemapindex（複数 sitemap を束ねる場合）は最初の子サイトマップのみ処理
    if "sitemapindex" in tag:
        sub_locs = [el.text for el in tree.findall(".//sm:loc", ns) if el.text]
        if sub_locs:
            # 最初の子サイトマップを再帰取得（1段のみ）
            try:
                resp2 = requests.get(sub_locs[0], timeout=SITEMAP_FETCH_TIMEOUT,
                                     headers={"User-Agent": "Kotomagaki-Bot/1.0"})
                if resp2.status_code == 200:
                    return _parse_sitemap_xml(resp2.text, root_url)
            except Exception:
                pass
        return {"error": "sitemapindex のサブサイトマップ取得失敗", "total_urls": 0}

    # 通常の urlset
    for url_el in tree.findall(".//sm:url", ns):
        loc = (url_el.findtext("sm:loc", namespaces=ns) or "").strip()
        lastmod = (url_el.findtext("sm:lastmod", namespaces=ns) or "").strip()
        if loc:
            entries.append({"url": loc, "lastmod": lastmod})

    total = len(entries)
    is_large = total > LARGE_SITE_THRESHOLD
    warning = f"大規模サイト（約{total:,}ページ）: 分析はサンプル4ページに限定されます。" if is_large else None

    # lastmod 降順でサンプリング
    dated = [(e["lastmod"], e["url"]) for e in entries if e["lastmod"]]
    dated.sort(reverse=True)
    undated = [e["url"] for e in entries if not e["lastmod"]]
    sampled = [u for _, u in dated[:SAMPLE_LIMIT_LARGE]] + undated[:max(0, SAMPLE_LIMIT_LARGE - len(dated))]

    # 更新頻度を lastmod から推定
    update_frequency = _estimate_update_frequency([d for d, _ in dated[:50]])

    # URL カテゴリ分類（第1パスセグメント）
    categories: Dict[str, int] = {}
    for e in entries[:500]:
        try:
            seg = urlparse(e["url"]).path.strip("/").split("/")[0] or "root"
            categories[seg] = categories.get(seg, 0) + 1
        except Exception:
            pass
    top_categories = dict(sorted(categories.items(), key=lambda x: -x[1])[:10])

    return {
        "total_urls": total,
        "sampled_urls": sampled[:SAMPLE_LIMIT_LARGE],
        "lastmod_dates": [d for d, _ in dated[:20]],
        "update_frequency": update_frequency,
        "url_categories": top_categories,
        "is_large_site": is_large,
        "warning": warning,
        "error": None,
    }


def _estimate_update_frequency(lastmod_strs: List[str]) -> str:
    """lastmod 日付リストから更新頻度を推定"""
    if len(lastmod_strs) < 2:
        return "不明"
    dates = []
    for s in lastmod_strs:
        try:
            dates.append(datetime.fromisoformat(s[:10]))
        except Exception:
            pass
    if len(dates) < 2:
        return "不明"
    dates.sort(reverse=True)
    gaps = [(dates[i] - dates[i+1]).days for i in range(min(10, len(dates)-1)) if (dates[i] - dates[i+1]).days > 0]
    if not gaps:
        return "不明"
    avg_gap = sum(gaps) / len(gaps)
    if avg_gap <= 1:
        return "毎日"
    if avg_gap <= 7:
        return "週1〜2回"
    if avg_gap <= 30:
        return "月1〜2回"
    return "低頻度"
```

### 変更: `core/engine/orchestrator.py` — sitemap 解析を analyze_url() に追加

```python
# analyze_url() 内、メイン URL 取得後（L860付近）に追加
from core.sitemap_analyzer import fetch_sitemap_urls

# sitemap メタデータ取得（コンテンツ取得なし・軽量）
sitemap_info = {}
try:
    sitemap_info = fetch_sitemap_urls(url)
except Exception as e:
    logger.warning(f"sitemap取得スキップ: {e}")

# last_analysis_results の return dict に追加
"sitemap_info": sitemap_info,
```

### 変更: `core/ui/reports/executive_summary.py` — 経営サマリーにサイト規模表示

```python
# GEO スコア行の下に追加
sitemap_info = integrated.get("sitemap_info") or {}
total_pages = sitemap_info.get("total_urls", 0)
if total_pages > 0:
    freq = sitemap_info.get("update_frequency", "不明")
    scope_text = f"サイト規模: 約{total_pages:,}ページ（更新頻度: {freq}）"
    if sitemap_info.get("is_large_site"):
        scope_text += " — 大規模サイトのため分析はサンプル4ページです"
    ui.label(scope_text).classes("card-hint")
```

---

## 対象ファイル

| ファイル | 変更種別 |
|---------|---------|
| `core/sitemap_analyzer.py` | **新規作成** |
| `core/engine/orchestrator.py` | `analyze_url()` に sitemap 取得追加 |
| `core/ui/reports/executive_summary.py` | サイト規模テキスト表示追加 |
| `WORKLOG.md` | 完了記録追記 |

---

## 完了条件

- [ ] `py -m py_compile core/sitemap_analyzer.py` エラーなし
- [ ] sitemap.xml を持つサイト（例: 自社サイト）で `total_urls > 0` が返る
- [ ] sitemap.xml がないサイトで `error` フィールドが返り、分析自体はクラッシュしない
- [ ] 経営サマリーに「サイト規模: 約XXページ」が表示される
- [ ] 10,000ページ超のサイトで「大規模サイト」警告が表示される
- [ ] WORKLOG.md 更新

---

## 注意事項

- **コンテンツ取得しない**: URL と lastmod メタデータのみ読む。本文・HTML は取得しない
- sitemap がない場合（error あり）は静かにスキップ。ユーザーへのエラー表示は不要
- `sitemapindex`（複数サイトマップを束ねる形式）は1段のみ再帰処理。無限再帰しない
- タイムアウト 10秒・5MB 上限で大容量サイトマップも安全に処理
- `requests` は既に依存関係に含まれている（確認: `requirements.txt` または `pyproject.toml`）
