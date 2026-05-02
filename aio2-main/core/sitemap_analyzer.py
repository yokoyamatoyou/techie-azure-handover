# -*- coding: utf-8 -*-
"""sitemap.xml metadata analyzer (URL + lastmod only, no page content fetch)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

from core.safe_fetch import safe_fetch_url

SITEMAP_FETCH_TIMEOUT = 10.0
SITEMAP_MAX_BYTES = 5 * 1024 * 1024  # 5MB
LARGE_SITE_THRESHOLD = 10_000
MEDIUM_SITE_THRESHOLD = 1_000
MID_LARGE_SITE_THRESHOLD = 10_000
SAMPLE_LIMIT_MID_LARGE = 500
SAMPLE_LIMIT_LARGE = 100
MAX_SITEMAP_RECURSION = 4
MAX_SUB_SITEMAPS = 200


def fetch_sitemap_urls(base_url: str) -> Dict[str, Any]:
    """
    Fetch and parse sitemap.xml metadata.

    Returns:
        {
            "total_urls": int,
            "sampled_urls": List[str],
            "sampled_count": int,
            "lastmod_dates": List[str],
            "update_frequency": str,
            "url_categories": Dict[str, int],
            "is_large_site": bool,
            "warning": Optional[str],
            "error": Optional[str],
        }
    """
    root_url = _resolve_site_root(base_url)
    if not root_url:
        return _empty_result(error="URLの形式が不正です")

    sitemap_url = f"{root_url}/sitemap.xml"

    try:
        xml_text, status_code = _fetch_xml(sitemap_url)
        if xml_text is None:
            return _empty_result(error=f"sitemap.xml が見つかりません（{status_code}）")
        return _parse_sitemap_xml(
            xml_text,
            root_url=root_url,
            depth=0,
            visited={sitemap_url},
            fetch_queue_count=1,
        )
    except Exception as exc:
        return _empty_result(error=str(exc)[:200])


def _resolve_site_root(url: str) -> Optional[str]:
    parsed = urlparse((url or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _fetch_xml(url: str) -> Tuple[Optional[str], int]:
    resp = safe_fetch_url(
        url,
        timeout=SITEMAP_FETCH_TIMEOUT,
        headers={"User-Agent": "Kotomigaki-SitemapBot/1.0"},
        max_bytes=SITEMAP_MAX_BYTES,
    )
    status_code = int(getattr(resp, "status_code", 0) or 0)
    if status_code != 200:
        return None, status_code

    return resp.text or "", status_code


def _parse_sitemap_xml(
    xml_text: str,
    *,
    root_url: str,
    depth: int,
    visited: set[str],
    fetch_queue_count: int,
) -> Dict[str, Any]:
    try:
        tree = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        return _empty_result(error=f"XMLパースエラー: {exc}")

    namespace = _extract_namespace(tree.tag)

    if _strip_ns(tree.tag).lower() == "sitemapindex":
        if depth >= MAX_SITEMAP_RECURSION:
            return _empty_result(error="sitemapindex の再帰上限に達しました")
        sub_locs = _extract_loc_values(tree, namespace, target_tag="sitemap")
        if not sub_locs:
            return _empty_result(error="sitemapindex に有効な子sitemapがありません")
        allowed_sub_urls = [
            _resolve_allowed_sub_sitemap_url(loc, root_url)
            for loc in sub_locs
        ]
        allowed_sub_urls = [u for u in allowed_sub_urls if u]
        if not allowed_sub_urls:
            return _empty_result(error="子sitemapのURLが許可されていません（同一ホストのみ許可）")
        aggregated_entries: List[Dict[str, str]] = []
        warnings: List[str] = []
        parsed_sitemaps = 1
        media_hints = {"image_sitemap_detected": False, "video_sitemap_detected": False}
        source_sitemaps: List[str] = []

        for sub_url in allowed_sub_urls:
            normalized_sub_url = sub_url.strip()
            if not normalized_sub_url or normalized_sub_url in visited:
                continue
            if len(visited) >= MAX_SUB_SITEMAPS or fetch_queue_count >= MAX_SUB_SITEMAPS:
                warnings.append(f"sitemap の取得件数が上限 {MAX_SUB_SITEMAPS} に達したため途中で打ち切りました。")
                break
            visited.add(normalized_sub_url)
            try:
                source_sitemaps.append(normalized_sub_url)
                lowered_sub_url = normalized_sub_url.lower()
                if "image" in lowered_sub_url:
                    media_hints["image_sitemap_detected"] = True
                if "video" in lowered_sub_url:
                    media_hints["video_sitemap_detected"] = True
                sub_xml, status_code = _fetch_xml(normalized_sub_url)
                if sub_xml is None:
                    warnings.append(f"子sitemapの取得失敗: {normalized_sub_url} ({status_code})")
                    continue
                parsed = _parse_sitemap_xml(
                    sub_xml,
                    root_url=root_url,
                    depth=depth + 1,
                    visited=visited,
                    fetch_queue_count=fetch_queue_count + 1,
                )
                parsed_sitemaps += int(parsed.get("parsed_sitemaps", 0) or 0)
                aggregated_entries.extend(parsed.get("entries", []) or [])
                child_hints = parsed.get("media_hints") or {}
                media_hints["image_sitemap_detected"] = media_hints["image_sitemap_detected"] or bool(child_hints.get("image_sitemap_detected"))
                media_hints["video_sitemap_detected"] = media_hints["video_sitemap_detected"] or bool(child_hints.get("video_sitemap_detected"))
                source_sitemaps.extend(parsed.get("source_sitemaps") or [])
                error_text = str(parsed.get("error") or "").strip()
                if error_text:
                    warnings.append(error_text)
                warning_text = str(parsed.get("warning") or "").strip()
                if warning_text:
                    warnings.append(warning_text)
            except Exception as exc:
                warnings.append(f"子sitemap取得失敗: {normalized_sub_url} ({str(exc)[:120]})")

        if not aggregated_entries:
            warning = " / ".join(warnings[:3]) if warnings else None
            return _empty_result(error="有効な子sitemapを解析できませんでした", warning=warning)
        return _build_result_from_entries(
            aggregated_entries,
            warnings=warnings,
            parsed_sitemaps=parsed_sitemaps,
            media_hints=media_hints,
            source_sitemaps=source_sitemaps,
        )

    if _strip_ns(tree.tag).lower() != "urlset":
        return _empty_result(error="sitemap形式が不明です")

    entries: List[Dict[str, str]] = []
    for url_el in _findall(tree, "url", namespace):
        loc = _findtext(url_el, "loc", namespace).strip()
        lastmod = _findtext(url_el, "lastmod", namespace).strip()
        if loc:
            entries.append({"url": loc, "lastmod": lastmod})

    if not entries:
        return _empty_result(error="sitemapにURLがありません")
    return _build_result_from_entries(
        entries,
        parsed_sitemaps=1,
        media_hints={
            "image_sitemap_detected": "<image:image" in xml_text.lower(),
            "video_sitemap_detected": "<video:video" in xml_text.lower(),
        },
        source_sitemaps=[],
    )


def _build_result_from_entries(
    entries: List[Dict[str, str]],
    *,
    warnings: Optional[List[str]] = None,
    parsed_sitemaps: int = 1,
    media_hints: Optional[Dict[str, bool]] = None,
    source_sitemaps: Optional[List[str]] = None,
) -> Dict[str, Any]:
    deduped_entries = _dedupe_entries(entries)
    total_urls = len(deduped_entries)
    if total_urls == 0:
        return _empty_result(error="sitemapにURLがありません")

    sampled_urls = _select_sampled_urls(deduped_entries)
    sampled_count = len(sampled_urls)
    lastmod_dates = [e["lastmod"] for e in deduped_entries if e.get("lastmod")]
    categories = _build_url_categories(deduped_entries)
    update_frequency = _estimate_update_frequency(lastmod_dates[:50])

    is_large_site = total_urls > LARGE_SITE_THRESHOLD
    warning_messages = [str(item).strip() for item in (warnings or []) if str(item).strip()]
    if is_large_site:
        warning_messages.append(f"大規模サイト（約{total_urls:,}ページ）: 分析はサンプル4ページに限定されます。")

    return {
        "total_urls": total_urls,
        "sampled_urls": sampled_urls,
        "sampled_count": sampled_count,
        "lastmod_dates": lastmod_dates[:20],
        "update_frequency": update_frequency,
        "url_categories": categories,
        "is_large_site": is_large_site,
        "warning": " / ".join(warning_messages[:3]) if warning_messages else None,
        "error": None,
        "parsed_sitemaps": parsed_sitemaps,
        "entries": deduped_entries,
        "media_hints": media_hints or {"image_sitemap_detected": False, "video_sitemap_detected": False},
        "source_sitemaps": sorted(set(source_sitemaps or []))[:20],
    }


def _empty_result(error: Optional[str] = None, warning: Optional[str] = None) -> Dict[str, Any]:
    return {
        "total_urls": 0,
        "sampled_urls": [],
        "sampled_count": 0,
        "lastmod_dates": [],
        "update_frequency": "不明",
        "url_categories": {},
        "is_large_site": False,
        "warning": warning,
        "error": error,
        "parsed_sitemaps": 0,
        "entries": [],
        "media_hints": {"image_sitemap_detected": False, "video_sitemap_detected": False},
        "source_sitemaps": [],
    }


def _extract_namespace(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag[1 : tag.index("}")]
    return ""


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _qualify(tag: str, namespace: str) -> str:
    return f"{{{namespace}}}{tag}" if namespace else tag


def _findall(node: ET.Element, tag: str, namespace: str) -> List[ET.Element]:
    return node.findall(_qualify(tag, namespace))


def _findtext(node: ET.Element, tag: str, namespace: str) -> str:
    text = node.findtext(_qualify(tag, namespace))
    return text or ""


def _extract_loc_values(tree: ET.Element, namespace: str, target_tag: str) -> List[str]:
    values: List[str] = []
    for node in _findall(tree, target_tag, namespace):
        loc = _findtext(node, "loc", namespace).strip()
        if loc:
            values.append(loc)
    return values


def _select_sampled_urls(entries: List[Dict[str, str]]) -> List[str]:
    total = len(entries)
    dated = [e for e in entries if e.get("lastmod")]
    dated.sort(key=lambda x: x.get("lastmod", ""), reverse=True)
    undated = [e for e in entries if not e.get("lastmod")]

    if total <= MEDIUM_SITE_THRESHOLD:
        limit = total
    elif total <= MID_LARGE_SITE_THRESHOLD:
        limit = SAMPLE_LIMIT_MID_LARGE
    else:
        limit = SAMPLE_LIMIT_LARGE

    sampled: List[str] = []
    for item in dated:
        if len(sampled) >= limit:
            break
        sampled.append(item["url"])
    for item in undated:
        if len(sampled) >= limit:
            break
        sampled.append(item["url"])
    return sampled


def _dedupe_entries(entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    deduped: Dict[str, Dict[str, str]] = {}
    for item in entries:
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        lastmod = str(item.get("lastmod") or "").strip()
        existing = deduped.get(url)
        if existing is None or lastmod > str(existing.get("lastmod") or ""):
            deduped[url] = {"url": url, "lastmod": lastmod}
    return list(deduped.values())


def _build_url_categories(entries: List[Dict[str, str]]) -> Dict[str, int]:
    categories: Dict[str, int] = {}
    for item in entries[:500]:
        try:
            path = urlparse(item.get("url", "")).path.strip("/")
            first_segment = path.split("/", 1)[0] if path else "root"
            key = first_segment or "root"
            categories[key] = categories.get(key, 0) + 1
        except Exception:
            continue
    sorted_items = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]
    return dict(sorted_items)


def _estimate_update_frequency(lastmod_strs: List[str]) -> str:
    if len(lastmod_strs) < 2:
        return "不明"

    dates: List[date] = []
    for raw in lastmod_strs:
        normalized = (raw or "").strip()
        if not normalized:
            continue
        # ISO8601の日時/日付の両方を許容
        normalized = normalized.replace("Z", "+00:00")
        parsed = None
        try:
            parsed = datetime.fromisoformat(normalized)
        except Exception:
            try:
                parsed = datetime.fromisoformat(normalized[:10])
            except Exception:
                parsed = None
        if parsed is not None:
            dates.append(parsed.date())

    if len(dates) < 2:
        return "不明"

    dates.sort(reverse=True)
    gaps: List[int] = []
    for idx in range(min(10, len(dates) - 1)):
        diff_days = (dates[idx] - dates[idx + 1]).days
        if diff_days > 0:
            gaps.append(diff_days)

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


def _resolve_allowed_sub_sitemap_url(candidate_url: str, root_url: str) -> Optional[str]:
    """Allow only same-host http/https sitemap URLs to prevent SSRF."""
    if not candidate_url:
        return None
    joined = urljoin(root_url.rstrip("/") + "/", candidate_url.strip())
    parsed = urlparse(joined)
    root_parsed = urlparse(root_url)
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc != root_parsed.netloc:
        return None
    return joined
