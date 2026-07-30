from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core.safe_fetch import safe_fetch_url

LEGACY_HTML_PROBE_PATHS = [
    "data.html",
    "system.html",
    "company.html",
    "profile.html",
    "about.html",
    "service.html",
    "services.html",
    "contact.html",
    "recruit.html",
    "privacy.html",
    "security.html",
    "case.html",
    "news.html",
    "rpa.html",
    "input.html",
    "scan.html",
    "scanning.html",
    "analysis.html",
    "index.html",
]

LEGACY_PROBE_MAX_CANDIDATES = 24
LEGACY_PROBE_MAX_BYTES = 256 * 1024
LEGACY_PROBE_TIMEOUT = 8.0


def audit_legacy_html_pages(
    base_url: str,
    *,
    known_urls: Optional[Iterable[str]] = None,
    fetcher: Optional[Callable[..., Any]] = None,
    max_candidates: int = LEGACY_PROBE_MAX_CANDIDATES,
    timeout: float = LEGACY_PROBE_TIMEOUT,
    max_bytes: int = LEGACY_PROBE_MAX_BYTES,
) -> Dict[str, Any]:
    """Find old static HTML pages that still look indexable.

    The probe is intentionally bounded: it checks common legacy filenames plus a
    few slug-derived candidates, then only reports pages that are still `.html`,
    return HTTP 200, are indexable, and do not declare a canonical URL.
    """
    root_url = _site_root(base_url)
    if not root_url:
        return _empty_result(error="URLの形式が不正です")

    fetch = fetcher or safe_fetch_url
    candidate_urls = _build_candidate_urls(root_url, known_urls or [], max_candidates=max_candidates)
    checked_urls: List[str] = []
    pages: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    for candidate_url in candidate_urls:
        checked_urls.append(candidate_url)
        try:
            response = fetch(candidate_url, timeout=timeout, max_bytes=max_bytes)
        except Exception as exc:
            errors.append({"url": candidate_url, "error": str(exc)[:160]})
            continue

        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code != 200:
            continue

        final_url = str(
            getattr(response, "safe_final_url", "")
            or getattr(response, "url", "")
            or candidate_url
        )
        if not _is_same_origin(final_url, root_url):
            continue
        if not (urlparse(final_url).path or "").lower().endswith(".html"):
            continue

        html = str(getattr(response, "text", "") or "")
        soup = BeautifulSoup(html, "html.parser")
        canonical = _extract_canonical(soup, final_url)
        meta_robots = _extract_meta_robots(soup)
        x_robots = _extract_x_robots(getattr(response, "headers", {}) or {})
        if canonical or _has_noindex(meta_robots) or _has_noindex(x_robots):
            continue

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        pages.append(
            {
                "url": candidate_url,
                "final_url": final_url,
                "status_code": status_code,
                "title": title,
                "robots": meta_robots,
                "x_robots": x_robots,
                "canonical": canonical,
                "reason": "200 / index可能 / canonicalなし",
            }
        )

    found_count = len(pages)
    if found_count:
        status = "fail"
        detail = f"古いHTML候補が {found_count} 件公開されたままです。"
    else:
        status = "pass"
        detail = "代表的な旧HTML候補は見つかりませんでした。"

    return {
        "title": "古い公開ページ",
        "status": status,
        "status_label": "要対応" if status == "fail" else "通過",
        "detail": detail,
        "checked_count": len(checked_urls),
        "candidate_count": len(candidate_urls),
        "found_count": found_count,
        "pages": pages[:10],
        "checked_urls": checked_urls[:12],
        "errors": errors[:5],
        "recommendations": [
            "対応する現行ページへ301リダイレクトしてください。",
            "残す必要がある場合は canonical または noindex を設定してください。",
            "古いページが検索やAI回答に引用されないよう公開状態を整理してください。",
        ],
    }


def _empty_result(error: str = "") -> Dict[str, Any]:
    return {
        "title": "古い公開ページ",
        "status": "reference",
        "status_label": "参考",
        "detail": "",
        "checked_count": 0,
        "candidate_count": 0,
        "found_count": 0,
        "pages": [],
        "checked_urls": [],
        "errors": [{"url": "", "error": error}] if error else [],
        "recommendations": [],
    }


def _site_root(url: str) -> str:
    parsed = urlparse(str(url or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def _build_candidate_urls(root_url: str, known_urls: Iterable[str], *, max_candidates: int) -> List[str]:
    paths: List[str] = []
    seen_paths: set[str] = set()

    def add_path(path: str) -> None:
        normalized = path.strip().lstrip("/")
        if not normalized or normalized in seen_paths:
            return
        seen_paths.add(normalized)
        paths.append(normalized)

    for path in LEGACY_HTML_PROBE_PATHS:
        add_path(path)

    for known_url in known_urls:
        if len(paths) >= max_candidates:
            break
        if not _is_same_origin(str(known_url), root_url):
            continue
        parts = [part for part in (urlparse(str(known_url)).path or "").split("/") if part]
        for part in parts:
            if len(paths) >= max_candidates:
                break
            slug = part.strip().lower()
            if not slug or slug.endswith(".html") or slug.isdigit() or len(slug) < 3:
                continue
            add_path(f"{slug}.html")

    return [urljoin(root_url.rstrip("/") + "/", path) for path in paths[:max_candidates]]


def _is_same_origin(url: str, root_url: str) -> bool:
    parsed = urlparse(str(url or "").strip())
    root = urlparse(root_url)
    return bool(parsed.scheme and parsed.netloc and parsed.scheme.lower() == root.scheme and parsed.netloc.lower() == root.netloc)


def _extract_canonical(soup: BeautifulSoup, final_url: str) -> str:
    for tag in soup.find_all("link"):
        rel = tag.get("rel")
        rel_text = " ".join(rel) if isinstance(rel, list) else str(rel or "")
        if "canonical" not in rel_text.lower():
            continue
        href = str(tag.get("href") or "").strip()
        return urljoin(final_url, href) if href else ""
    return ""


def _extract_meta_robots(soup: BeautifulSoup) -> str:
    values: List[str] = []
    for tag in soup.find_all("meta"):
        name = str(tag.get("name") or "").strip().lower()
        if name not in {"robots", "googlebot"}:
            continue
        content = str(tag.get("content") or "").strip()
        if content:
            values.append(content)
    return ", ".join(values)


def _extract_x_robots(headers: Any) -> str:
    if not headers:
        return ""
    try:
        value = headers.get("X-Robots-Tag") or headers.get("x-robots-tag")
    except AttributeError:
        value = ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value or "").strip()


def _has_noindex(value: str) -> bool:
    tokens = [token.strip().lower() for token in str(value or "").replace(";", ",").split(",")]
    return "noindex" in tokens
