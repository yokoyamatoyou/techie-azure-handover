# -*- coding: utf-8 -*-
"""クロール深度戦略モジュール（Phase 02）

リンク数に基づいて動的にクロール深度を決定する。
AIO最適化（構造化文書・リライト提案・エンティティ分析）を目的とするため、
最低 depth=1 とし、キーワード一致ページ（法務・会社概要・FAQ等）を優先取得する。
"""

from typing import Dict, List, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from core.site_health.url_instruction_guard import inspect_url_for_untrusted_instruction

# クロール深度の閾値設定（AIO目的: 構造化・リライト・エンティティ分析のため最低1階層は取得）
CRAWL_DEPTH_THRESHOLDS = {
    "small": {"max_links": 50, "depth": 2, "description": "小規模サイト: 2階層まで"},
    "medium": {"max_links": 200, "depth": 1, "description": "中規模サイト: 1階層まで"},
    "large": {"max_links": float("inf"), "depth": 1, "description": "大規模サイト: キーワード一致ページを優先して1階層取得"},
}

# 優先ページの優先度（高い順）
# 目的: depth=1 で「法務→事業→FAQ」を優先的に拾う
LEGAL_PAGE_PRIORITY = [
    (r"特定商取引|特商法|tokusho|tokutei", 100),
    (r"返品|返金|キャンセル|return|refund", 90),
    (r"会社概要|会社情報|about|company", 80),
    (r"プライバシー|個人情報|privacy|privacy\s*policy|プライバシーポリシー|プライバシー方針", 70),
    (r"利用規約|規約|利用条件|terms|terms\s*of\s*use|terms\s*of\s*service|tos", 60),
]

# 事業関連ページ（法務の次に優先）
BUSINESS_PAGE_PRIORITY = [
    (r"サービス|service|提供|product|製品", 55),
    (r"料金|価格|price|pricing|プラン|plan", 54),
    (r"導入|実績|事例|case|customer|お客様の声|レビュー|review", 53),
    (r"機能|features|仕様|spec", 52),
    (r"お問い合わせ|contact|inquiry|support", 51),
    (r"採用|recruit|careers|求人", 50),
]

# FAQ（最後に優先）
FAQ_PAGE_PRIORITY = [
    (r"FAQ|よくある質問|help|support", 40),
]


def count_internal_links(soup: BeautifulSoup, base_url: str) -> int:
    """ページ内の内部リンク数をカウント"""
    if not soup or not base_url:
        return 0

    base_parsed = urlparse(base_url)
    count = 0

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        # 絶対URL化
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # 同一ドメインかチェック
        if parsed.netloc == base_parsed.netloc or not parsed.netloc:
            count += 1

    return count


def determine_crawl_depth(link_count: int) -> Dict:
    """リンク数に基づいてクロール深度を決定"""
    for size, config in CRAWL_DEPTH_THRESHOLDS.items():
        if link_count <= config["max_links"]:
            return {
                "site_size": size,
                "depth": config["depth"],
                "description": config["description"],
                "reason": config["description"],
                "link_count": link_count,
            }

    # フォールバック（大規模）
    return {
        "site_size": "large",
        "depth": 1,
        "description": CRAWL_DEPTH_THRESHOLDS["large"]["description"],
        "reason": CRAWL_DEPTH_THRESHOLDS["large"]["description"],
        "link_count": link_count,
    }


def get_crawl_strategy(soup: BeautifulSoup, base_url: str) -> Dict:
    """クロール戦略を決定

    Returns:
        {
            "site_size": "small" | "medium" | "large",
            "depth": 0-2,
            "description": str,
            "link_count": int,
            "priority_pages": List[str],  # シード（法務→事業→FAQで多様性確保）
            "priority_candidates": List[str],  # 候補（スコア順、上位を多めに）
        }
    """
    link_count = count_internal_links(soup, base_url)
    strategy = determine_crawl_depth(link_count)

    # 優先度の高いキーワード一致ページ（法務→事業→FAQ）を抽出
    import re
    priority_pages = []
    excluded_untrusted_instruction_urls = []
    base_parsed = urlparse(base_url)

    def _classify_priority(search_text: str) -> Tuple[int, str]:
        # 法務
        for pattern, score in LEGAL_PAGE_PRIORITY:
            if re.search(pattern, search_text, re.IGNORECASE):
                return score, "legal"
        # 事業
        for pattern, score in BUSINESS_PAGE_PRIORITY:
            if re.search(pattern, search_text, re.IGNORECASE):
                return score, "business"
        # FAQ
        for pattern, score in FAQ_PAGE_PRIORITY:
            if re.search(pattern, search_text, re.IGNORECASE):
                return score, "faq"
        return 0, ""

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        title = link.get("title", "") or ""

        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # 外部リンクはスキップ
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            continue

        instruction_screen = inspect_url_for_untrusted_instruction(full_url, link_text=text)
        if instruction_screen.get("status") == "suspicious_untrusted_instruction":
            excluded_untrusted_instruction_urls.append(instruction_screen)
            continue

        # 優先度とカテゴリを計算
        search_text = f"{text} {title} {href}".lower()
        priority, category = _classify_priority(search_text)

        if priority > 0:
            priority_pages.append({
                "url": full_url,
                "text": text[:50],
                "priority": priority,
                "category": category,
            })

    # 優先度でソート（同点はURLで安定化）
    priority_pages.sort(key=lambda x: (-x["priority"], x["url"]))

    # シードは 4 件: 法務(最大2)→事業(1)→FAQ(1)
    seed_pages = 4

    def _pick(category: str, limit: int, picked_urls: set) -> List[str]:
        out = []
        for item in priority_pages:
            if item.get("category") != category:
                continue
            u = item.get("url")
            if not u or u in picked_urls:
                continue
            picked_urls.add(u)
            out.append(u)
            if len(out) >= limit:
                break
        return out

    picked = set()
    selected: List[str] = []
    selected += _pick("legal", 2, picked)
    selected += _pick("business", 1, picked)
    selected += _pick("faq", 1, picked)
    # 余りはスコア順に埋める
    for item in priority_pages:
        if len(selected) >= seed_pages:
            break
        u = item.get("url")
        if not u or u in picked:
            continue
        picked.add(u)
        selected.append(u)

    strategy["priority_pages"] = selected
    # 候補は上位を多めに返す（取得側で文字数ベースで打ち切る）
    strategy["priority_candidates"] = [p.get("url") for p in priority_pages[:20] if p.get("url")]
    if excluded_untrusted_instruction_urls:
        strategy["excluded_untrusted_instruction_urls"] = excluded_untrusted_instruction_urls[:8]

    return strategy
