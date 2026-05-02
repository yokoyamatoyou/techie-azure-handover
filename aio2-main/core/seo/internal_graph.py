# -*- coding: utf-8 -*-
"""内部リンク構造分析モジュール"""
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse, urljoin, urlunparse


class InternalLinkGraph:
    """内部リンクのグラフ構造を管理"""

    def __init__(self, base_url: str):
        self.root_url = self._normalize_url(base_url)
        self.base_domain = urlparse(self.root_url).netloc
        self.edges: List[Tuple[str, str]] = []
        self.inbound_count: Dict[str, int] = defaultdict(int)
        self.outbound_count: Dict[str, int] = defaultdict(int)
        self.pages: Set[str] = set()

    def add_page(self, url: str, links: List[str]) -> None:
        """ページとそのリンクを追加"""
        normalized_url = self._normalize_url(url)
        self.pages.add(normalized_url)
        seen_targets: Set[str] = set()

        for link in links:
            full_link = self._normalize_url(urljoin(normalized_url, link))
            link_domain = urlparse(full_link).netloc
            if not full_link or link_domain != self.base_domain or full_link in seen_targets:
                continue
            seen_targets.add(full_link)
            if link_domain == self.base_domain:
                self.edges.append((normalized_url, full_link))
                self.outbound_count[normalized_url] += 1
                self.inbound_count[full_link] += 1
                self.pages.add(full_link)

    def find_orphan_pages(self) -> List[str]:
        """インバウンドリンクがゼロのページを検出"""
        return [p for p in self.pages if self.inbound_count[p] == 0]

    def find_low_link_pages(self, threshold: int = 2) -> List[str]:
        """インバウンドリンクが少ないページを検出"""
        return [p for p in self.pages if 0 < self.inbound_count[p] < threshold]

    def get_summary(self) -> Dict[str, object]:
        """分析サマリーを返す"""
        orphans = self.find_orphan_pages()
        low_link = self.find_low_link_pages()
        return {
            "total_pages": len(self.pages),
            "total_internal_links": len(self.edges),
            "orphan_pages": orphans,
            "orphan_count": len(orphans),
            "low_link_pages": low_link,
            "low_link_count": len(low_link),
            "avg_inbound_links": sum(self.inbound_count.values()) / max(len(self.pages), 1),
        }

    def get_health_report(self, all_known_urls: List[str] = None) -> Dict[str, object]:
        """内部リンク構造の健全性レポートを返す。"""
        analyzed_pages = set(self.pages)
        known_pages = {
            self._normalize_url(page)
            for page in (all_known_urls or analyzed_pages)
            if self._is_same_domain(page)
        }
        if not known_pages:
            known_pages = set(analyzed_pages)

        inbound_map: Dict[str, int] = defaultdict(int)
        for _, target in self.edges:
            inbound_map[target] += 1

        # ルートページは特性上インバウンドがゼロでも孤立扱いしない
        orphan_pages = [
            page for page in known_pages
            if page != self.root_url and inbound_map.get(page, 0) == 0
        ]
        orphan_ratio = len(orphan_pages) / max(len(known_pages), 1)

        hub_candidates = sorted(
            inbound_map.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        hub_pages = [url for url, count in hub_candidates if count > 0][:5]

        avg_depth = self._estimate_average_depth()
        health_score = max(0.0, 100.0 - orphan_ratio * 100.0)

        if health_score >= 80:
            diagnosis = "内部リンク構造は良好です。"
        elif health_score >= 50:
            diagnosis = f"孤立ページが{len(orphan_pages)}件あります。内部リンクを追加してください。"
        else:
            diagnosis = f"孤立ページが多数（{len(orphan_pages)}件）です。サイト構造の見直しを推奨します。"

        return {
            "total_analyzed_pages": len(analyzed_pages),
            "total_known_pages": len(known_pages),
            "orphan_count": len(orphan_pages),
            "orphan_ratio": round(orphan_ratio, 3),
            "low_link_count": len(self.find_low_link_pages()),
            "hub_pages": hub_pages,
            "avg_depth": round(avg_depth, 2),
            "health_score": round(health_score, 1),
            "diagnosis": diagnosis,
        }

    def build_audit_candidates(self, all_known_urls: List[str] = None, limit: int = 12) -> List[str]:
        """Build a stable, bounded set of URLs for link-target auditing."""
        known_pages = [
            self._normalize_url(page)
            for page in (all_known_urls or [])
            if self._is_same_domain(page)
        ]
        prioritized_groups = [
            [self.root_url],
            sorted(self.pages),
            sorted(self.find_orphan_pages()),
            sorted(self.find_low_link_pages()),
            self.get_health_report(all_known_urls=all_known_urls).get("hub_pages", []),
            sorted(known_pages),
        ]

        selected: List[str] = []
        seen: Set[str] = set()
        for group in prioritized_groups:
            for url in group:
                normalized = self._normalize_url(str(url or ""))
                if not normalized or normalized in seen or not self._is_same_domain(normalized):
                    continue
                seen.add(normalized)
                selected.append(normalized)
                if len(selected) >= limit:
                    return selected
        return selected

    def _estimate_average_depth(self) -> float:
        """ルートから到達可能なページの平均深度を推定する。"""
        if not self.pages:
            return 0.0

        adjacency: Dict[str, Set[str]] = defaultdict(set)
        for src, dst in self.edges:
            adjacency[src].add(dst)

        start = self.root_url if self.root_url in self.pages else next(iter(self.pages))
        depths: Dict[str, int] = {start: 0}
        queue: List[str] = [start]
        head = 0
        while head < len(queue):
            current = queue[head]
            head += 1
            for nxt in adjacency.get(current, set()):
                if nxt in depths:
                    continue
                depths[nxt] = depths[current] + 1
                queue.append(nxt)

        if not depths:
            return 0.0
        return sum(depths.values()) / len(depths)

    def _is_same_domain(self, url: str) -> bool:
        normalized = self._normalize_url(url)
        return bool(normalized) and urlparse(normalized).netloc == self.base_domain

    @staticmethod
    def _normalize_url(url: str) -> str:
        raw = str(url or "").strip()
        if not raw:
            return ""
        parsed = urlparse(raw)
        if not parsed.scheme or not parsed.netloc:
            return ""

        scheme = parsed.scheme.lower()
        hostname = (parsed.hostname or "").lower()
        port = parsed.port
        if port and ((scheme == "http" and port != 80) or (scheme == "https" and port != 443)):
            netloc = f"{hostname}:{port}"
        else:
            netloc = hostname
        path = parsed.path or "/"
        return urlunparse((scheme, netloc, path, "", parsed.query, ""))


if __name__ == "__main__":
    graph = InternalLinkGraph("https://example.com")
    graph.add_page("https://example.com/", ["/about", "/products", "/contact"])
    graph.add_page("https://example.com/about", ["/", "/products"])
    graph.add_page("https://example.com/products", ["/", "/about"])
    summary = graph.get_summary()
    print(f"Total pages: {summary['total_pages']}")
    print(f"Orphan pages: {summary['orphan_pages']}")
