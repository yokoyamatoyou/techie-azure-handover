from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from core.safe_fetch import safe_fetch_url

LINK_AUDIT_MAX_URLS = 12
LINK_AUDIT_MAX_BYTES = 256 * 1024
LINK_AUDIT_TIMEOUT = 8.0


def normalize_url(url: str) -> str:
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


def audit_internal_urls(
    urls: List[str],
    *,
    fetcher: Optional[Callable[..., Any]] = None,
    max_urls: int = LINK_AUDIT_MAX_URLS,
    timeout: float = LINK_AUDIT_TIMEOUT,
    max_bytes: int = LINK_AUDIT_MAX_BYTES,
) -> Dict[str, Any]:
    """Audit internal URLs for status, redirects, canonical mismatches, and noindex."""
    fetch = fetcher or safe_fetch_url
    candidates: List[str] = []
    seen = set()
    for url in urls:
        normalized = normalize_url(url)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(normalized)
        if len(candidates) >= max_urls:
            break

    audited_targets: List[Dict[str, Any]] = []
    broken_targets: List[Dict[str, Any]] = []
    redirected_targets: List[Dict[str, Any]] = []
    canonical_mismatches: List[Dict[str, Any]] = []
    noindex_targets: List[Dict[str, Any]] = []

    for url in candidates:
        try:
            response = fetch(url, timeout=timeout, max_bytes=max_bytes)
            final_url = normalize_url(getattr(response, "safe_final_url", "") or getattr(response, "url", "") or url)
            redirect_count = int(getattr(response, "safe_redirect_count", 0) or 0)
            redirect_chain = list(getattr(response, "safe_redirect_chain", []) or [url, final_url])
            status_code = int(getattr(response, "status_code", 0) or 0)
            headers = getattr(response, "headers", {}) or {}
            html = getattr(response, "text", "") or ""
            soup = BeautifulSoup(html, "html.parser")
            canonical_url = _extract_canonical_url(soup, base_url=final_url or url)
            meta_noindex = _extract_meta_noindex(soup)
            x_robots_noindex = _extract_x_robots_noindex(headers)
            requested_url = normalize_url(url)

            record = {
                "url": requested_url,
                "final_url": final_url or requested_url,
                "status_code": status_code,
                "redirect_count": redirect_count,
                "redirect_chain": redirect_chain,
                "canonical_url": canonical_url,
                "meta_noindex": meta_noindex,
                "x_robots_noindex": x_robots_noindex,
            }
            audited_targets.append(record)

            if status_code >= 400:
                broken_targets.append(
                    {"url": requested_url, "status_code": status_code, "detail": f"HTTP {status_code}"}
                )
            if redirect_count > 0:
                redirected_targets.append(
                    {
                        "url": requested_url,
                        "final_url": final_url or requested_url,
                        "status_code": status_code,
                        "redirect_count": redirect_count,
                    }
                )
            canonical_normalized = normalize_url(canonical_url)
            if canonical_normalized and canonical_normalized not in {requested_url, final_url}:
                canonical_mismatches.append(
                    {
                        "url": requested_url,
                        "final_url": final_url or requested_url,
                        "canonical_url": canonical_normalized,
                    }
                )
            if meta_noindex or x_robots_noindex:
                noindex_targets.append(
                    {
                        "url": requested_url,
                        "final_url": final_url or requested_url,
                        "detail": "meta noindex" if meta_noindex else "X-Robots-Tag noindex",
                    }
                )
        except Exception as exc:  # pragma: no cover - defensive path
            broken_targets.append({"url": normalize_url(url), "status_code": None, "detail": str(exc)[:160]})

    return {
        "audited_target_count": len(candidates),
        "audited_targets": audited_targets,
        "broken_target_count": len(broken_targets),
        "broken_targets": broken_targets[:5],
        "redirected_target_count": len(redirected_targets),
        "redirected_targets": redirected_targets[:5],
        "canonical_mismatch_count": len(canonical_mismatches),
        "canonical_mismatches": canonical_mismatches[:5],
        "noindex_target_count": len(noindex_targets),
        "noindex_targets": noindex_targets[:5],
    }


def combine_link_health_reports(structure_report: Dict[str, Any], audit_report: Dict[str, Any]) -> Dict[str, Any]:
    """Combine structural link metrics with target-level audit findings."""
    combined = dict(structure_report or {})
    combined.update(audit_report or {})

    structural_score = float((structure_report or {}).get("health_score", 0.0) or 0.0)
    audited = int((audit_report or {}).get("audited_target_count", 0) or 0)
    if audited <= 0:
        combined["health_score"] = round(structural_score, 1)
        return combined

    broken = int((audit_report or {}).get("broken_target_count", 0) or 0)
    redirected = int((audit_report or {}).get("redirected_target_count", 0) or 0)
    canonical = int((audit_report or {}).get("canonical_mismatch_count", 0) or 0)
    noindex = int((audit_report or {}).get("noindex_target_count", 0) or 0)

    audit_penalty = (
        (broken / audited) * 55.0
        + (redirected / audited) * 12.0
        + (canonical / audited) * 18.0
        + (noindex / audited) * 25.0
    )
    target_health = max(0.0, 100.0 - audit_penalty)
    combined_score = round((structural_score * 0.6) + (target_health * 0.4), 1)

    if broken > 0:
        diagnosis = f"内部リンク先にエラーがあります（{broken}件）。リンク切れや移転設定を確認してください。"
    elif noindex > 0:
        diagnosis = f"内部リンク先に noindex が含まれます（{noindex}件）。重要ページの公開設定を確認してください。"
    elif canonical > 0:
        diagnosis = f"内部リンク先で canonical 不整合が見つかりました（{canonical}件）。評価分散に注意してください。"
    elif redirected > 0:
        diagnosis = f"内部リンク先にリダイレクトが含まれます（{redirected}件）。最終URLへ直接リンクしてください。"
    else:
        diagnosis = str((structure_report or {}).get("diagnosis") or "内部リンク構造は良好です。")

    combined["health_score"] = combined_score
    combined["target_health_score"] = round(target_health, 1)
    combined["diagnosis"] = diagnosis
    return combined


def _extract_canonical_url(soup: BeautifulSoup, *, base_url: str) -> str:
    link = soup.find("link", attrs={"rel": lambda value: _has_rel_token(value, "canonical")})
    if not link or not link.get("href"):
        return ""
    return normalize_url(urljoin(base_url, str(link.get("href")).strip()))


def _extract_meta_noindex(soup: BeautifulSoup) -> bool:
    for meta in soup.find_all("meta"):
        name = str(meta.get("name") or meta.get("property") or "").strip().lower()
        if name not in {"robots", "googlebot"}:
            continue
        content = str(meta.get("content") or "").strip().lower()
        if not content:
            continue
        tokens = {part.strip().split(":", 1)[0] for part in content.split(",") if part.strip()}
        if "noindex" in tokens or "none" in tokens:
            return True
    return False


def _extract_x_robots_noindex(headers: Any) -> bool:
    raw = ""
    if hasattr(headers, "get_all"):
        raw = ",".join(headers.get_all("X-Robots-Tag") or [])
    if not raw and hasattr(headers, "get"):
        raw = str(headers.get("X-Robots-Tag") or "")
    raw = raw.lower()
    return "noindex" in raw or "none" in raw


def _has_rel_token(value: Any, expected: str) -> bool:
    if isinstance(value, (list, tuple, set)):
        tokens = [str(item).strip().lower() for item in value]
    else:
        tokens = [token.strip().lower() for token in str(value or "").split()]
    return expected in tokens
