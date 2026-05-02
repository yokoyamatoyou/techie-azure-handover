from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup


def _grade_lcp(lcp_ms: float) -> str:
    if lcp_ms <= 2500:
        return "good"
    if lcp_ms <= 4000:
        return "needs_improvement"
    return "poor"


def _grade_cls(cls_score: float) -> str:
    if cls_score <= 0.1:
        return "good"
    if cls_score <= 0.25:
        return "needs_improvement"
    return "poor"


def audit_page_experience(
    soup: BeautifulSoup,
    page_url: str,
    *,
    page_size_kb: float,
    has_viewport: bool,
    image_count: int,
    script_count: int,
    stylesheet_count: int,
) -> Dict[str, Any]:
    images_without_dimensions = 0
    eager_images = 0
    hidden_mobile_signals: List[str] = []
    separate_mobile_urls: List[str] = []
    fixed_ui_candidates = 0

    for img in soup.find_all("img"):
        has_width = str(img.get("width") or "").strip()
        has_height = str(img.get("height") or "").strip()
        if not has_width or not has_height:
            images_without_dimensions += 1
        if str(img.get("loading") or "").strip().lower() == "eager":
            eager_images += 1

    for node in soup.find_all(True):
        class_text = " ".join(node.get("class") or [])
        id_text = str(node.get("id") or "")
        attrs = f"{class_text} {id_text}".lower()
        if any(token in attrs for token in ("mobile-hide", "hide-mobile", "sp-hidden", "pc-only", "desktop-only")):
            hidden_mobile_signals.append(attrs.strip())
        style = str(node.get("style") or "").lower()
        if "position:fixed" in style or "position: sticky" in style or "position:sticky" in style:
            fixed_ui_candidates += 1

    for link in soup.find_all("link", href=True):
        rel = link.get("rel") or []
        rel_values = [str(item).strip().lower() for item in rel] if isinstance(rel, list) else [str(rel).strip().lower()]
        if "alternate" not in rel_values:
            continue
        media = str(link.get("media") or "").lower()
        href = urljoin(page_url, str(link.get("href") or "").strip())
        host = urlsplit(href).netloc.lower()
        if "max-width" in media or host.startswith("m."):
            separate_mobile_urls.append(href)

    lcp_ms = 1800.0
    if page_size_kb > 300:
        lcp_ms += 350.0
    if page_size_kb > 800:
        lcp_ms += 650.0
    if image_count > 10:
        lcp_ms += min(900.0, float(image_count - 10) * 45.0)
    if script_count > 12:
        lcp_ms += min(800.0, float(script_count - 12) * 35.0)
    if stylesheet_count > 4:
        lcp_ms += min(300.0, float(stylesheet_count - 4) * 40.0)
    if eager_images:
        lcp_ms -= min(250.0, float(eager_images) * 50.0)
    lcp_ms = max(1200.0, round(lcp_ms, 1))

    cls_score = 0.03
    if images_without_dimensions:
        cls_score += min(0.25, images_without_dimensions * 0.03)
    if fixed_ui_candidates > 1:
        cls_score += min(0.14, (fixed_ui_candidates - 1) * 0.03)
    cls_score = min(0.45, round(cls_score, 3))

    lcp_grade = _grade_lcp(lcp_ms)
    cls_grade = _grade_cls(cls_score)

    mobile_status = "pass"
    mobile_issues: List[Dict[str, str]] = []

    def add_mobile_issue(severity: str, message: str) -> None:
        nonlocal mobile_status
        mobile_issues.append({"severity": severity, "message": message})
        if severity == "fail":
            mobile_status = "fail"
        elif severity == "warn" and mobile_status == "pass":
            mobile_status = "warn"

    if not has_viewport:
        add_mobile_issue("fail", "viewport が未設定です。モバイル向け表示幅が固定化される可能性があります。")
    if hidden_mobile_signals:
        add_mobile_issue("warn", "mobile/desktop で内容差が出るクラス名が見つかりました。重要本文の parity を確認してください。")
    if separate_mobile_urls:
        add_mobile_issue("warn", "モバイル専用URLまたは media alternate が検出されました。metadata と本文の parity を確認してください。")

    cwv_status = "pass"
    cwv_issues: List[Dict[str, str]] = []

    def add_cwv_issue(severity: str, message: str) -> None:
        nonlocal cwv_status
        cwv_issues.append({"severity": severity, "message": message})
        if severity == "fail":
            cwv_status = "fail"
        elif severity == "warn" and cwv_status == "pass":
            cwv_status = "warn"

    if lcp_grade == "poor":
        add_cwv_issue("fail", "LCP 推定が poor です。画像・JS・HTMLサイズの見直しが必要です。")
    elif lcp_grade == "needs_improvement":
        add_cwv_issue("warn", "LCP 推定が needs_improvement です。主要画像やJSの軽量化を検討してください。")

    if cls_grade == "poor":
        add_cwv_issue("fail", "CLS 推定が poor です。画像や埋め込みの予約領域を確保してください。")
    elif cls_grade == "needs_improvement":
        add_cwv_issue("warn", "CLS 推定が needs_improvement です。画像サイズ指定や固定UIの影響を確認してください。")

    if images_without_dimensions:
        add_cwv_issue("warn", f"width/height 未指定の画像が {images_without_dimensions} 件あります。CLS 悪化要因になりやすいです。")

    return {
        "mobile_parity": {
            "status": mobile_status,
            "issues": mobile_issues,
            "summary": f"viewport={'yes' if has_viewport else 'no'} / hidden_mobile_signals={len(hidden_mobile_signals)} / separate_mobile_urls={len(separate_mobile_urls)}",
            "hidden_mobile_signal_count": len(hidden_mobile_signals),
            "separate_mobile_urls": separate_mobile_urls[:5],
        },
        "core_web_vitals": {
            "status": cwv_status,
            "measurement": "heuristic",
            "lcp_ms": lcp_ms,
            "lcp_grade": lcp_grade,
            "cls_score": cls_score,
            "cls_grade": cls_grade,
            "images_without_dimensions": images_without_dimensions,
            "issues": cwv_issues,
            "summary": f"LCP={lcp_ms:.0f}ms ({lcp_grade}) / CLS={cls_score:.3f} ({cls_grade})",
        },
    }
