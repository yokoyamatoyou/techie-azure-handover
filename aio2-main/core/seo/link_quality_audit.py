from __future__ import annotations

import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup

GENERIC_ANCHOR_TEXTS = {
    "click here",
    "here",
    "read more",
    "learn more",
    "more",
    "view more",
    "see more",
    "details",
    "詳しくはこちら",
    "こちら",
    "詳細はこちら",
    "もっと見る",
    "続きを読む",
    "詳しく見る",
}


def _normalize_text(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    return text


def audit_link_quality(soup: BeautifulSoup) -> Dict[str, Any]:
    anchors = soup.find_all("a")
    issues: List[Dict[str, str]] = []
    status = "pass"

    non_crawlable: List[Dict[str, str]] = []
    empty_anchors: List[Dict[str, str]] = []
    generic_anchors: List[Dict[str, str]] = []
    image_only_missing_alt: List[Dict[str, str]] = []
    scripted_navigation: List[Dict[str, str]] = []

    def add_issue(severity: str, message: str) -> None:
        nonlocal status
        issues.append({"severity": severity, "message": message})
        if severity == "fail":
            status = "fail"
        elif severity == "warn" and status == "pass":
            status = "warn"

    for anchor in anchors:
        href = str(anchor.get("href") or "").strip()
        text = _normalize_text(anchor.get_text(" ", strip=True))
        aria_label = _normalize_text(anchor.get("aria-label"))
        title = _normalize_text(anchor.get("title"))
        imgs = anchor.find_all("img")
        img_alt_texts = [_normalize_text(img.get("alt")) for img in imgs if _normalize_text(img.get("alt"))]
        accessible_text = " ".join(part for part in [text, aria_label, title, " ".join(img_alt_texts)] if part).strip()

        if href.startswith("#") or href.lower().startswith("javascript:"):
            non_crawlable.append({"href": href or "(empty)", "text": accessible_text or "(empty)"})

        if not accessible_text:
            empty_anchors.append({"href": href or "(empty)", "text": "(empty)"})

        if imgs and not text and not aria_label and not title and not img_alt_texts:
            image_only_missing_alt.append({"href": href or "(empty)", "text": "(image-only)"})

        if accessible_text in GENERIC_ANCHOR_TEXTS:
            generic_anchors.append({"href": href or "(empty)", "text": accessible_text})

    for node in soup.find_all(["button", "div", "span"]):
        onclick = str(node.get("onclick") or "").lower()
        if "location.href" in onclick or "window.location" in onclick:
            label = _normalize_text(node.get_text(" ", strip=True)) or _normalize_text(node.get("aria-label")) or "(no label)"
            scripted_navigation.append({"href": "onclick", "text": label})

    if non_crawlable:
        add_issue("warn", f"クロール不能なリンク記法が {len(non_crawlable)} 件あります。`javascript:` や `#` 依存を避けてください。")
    if empty_anchors:
        add_issue("fail", f"リンクテキストが空のアンカーが {len(empty_anchors)} 件あります。")
    if generic_anchors:
        add_issue("warn", f"汎用的なアンカーテキストが {len(generic_anchors)} 件あります。リンク先の内容が分かる文言にしてください。")
    if image_only_missing_alt:
        add_issue("warn", f"画像のみリンクで alt が不足している箇所が {len(image_only_missing_alt)} 件あります。")
    if scripted_navigation:
        add_issue("warn", f"onclick ベースのナビゲーションが {len(scripted_navigation)} 件あります。SEO向けには `<a href>` を優先してください。")

    crawlable_count = max(0, len(anchors) - len(non_crawlable))

    return {
        "status": status,
        "total_anchor_count": len(anchors),
        "crawlable_anchor_count": crawlable_count,
        "non_crawlable_count": len(non_crawlable),
        "empty_anchor_count": len(empty_anchors),
        "generic_anchor_count": len(generic_anchors),
        "image_only_missing_alt_count": len(image_only_missing_alt),
        "scripted_navigation_count": len(scripted_navigation),
        "non_crawlable_examples": non_crawlable[:5],
        "empty_anchor_examples": empty_anchors[:5],
        "generic_anchor_examples": generic_anchors[:5],
        "image_only_missing_alt_examples": image_only_missing_alt[:5],
        "scripted_navigation_examples": scripted_navigation[:5],
        "issues": issues,
        "summary": (
            f"crawlable={crawlable_count}/{len(anchors)} / "
            f"empty={len(empty_anchors)} / generic={len(generic_anchors)} / "
            f"image_only_missing_alt={len(image_only_missing_alt)}"
        ),
    }
