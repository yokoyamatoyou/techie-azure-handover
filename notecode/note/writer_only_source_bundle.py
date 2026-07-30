"""Strict URL intake and source bundle creation for writer-only generation."""
from __future__ import annotations

import codecs
import fnmatch
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urldefrag, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from note.safe_fetch import (
    ContentTooLargeError,
    SafeFetchError,
    UnsafeURLError,
    safe_fetch_url,
    validate_public_url,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data" / "writer_only_sources"
UPLOAD_ROOT = Path(__file__).resolve().parent / "uploads"
USER_AGENT = "JapaneseWritingMVPBot"
MAX_URLS = 6
ROBOTS_TIMEOUT = 5
BODY_TIMEOUT = 10
ROBOTS_READ_LIMIT = 512 * 1024
BODY_READ_LIMIT = 2_000_000
FULL_TEXT_LIMIT = 12_000
EXCERPT_LIMIT = 800
CLAIMS_LIMIT = 8
SUPPORTED_UPLOAD_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
_LOW_CONFIDENCE_DECLARED_ENCODINGS = {
    "ascii",
    "cp1252",
    "iso-8859-1",
    "iso8859-1",
    "latin-1",
    "latin1",
    "latin_1",
    "windows-1252",
}
_COMMON_PAGE_CHROME_LINES = {
    "akiya",
    "kashi",
    "lineで問合せ",
    "top",
    "電話する",
    "無料査定依頼",
}
_EMBEDDED_ENCODING_RE = re.compile(
    rb"(?:charset|encoding)\s*=\s*[\"']?\s*([A-Za-z0-9._-]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class UrlPolicyResult:
    url: str
    normalized_url: str
    allowed: bool
    reason_code: str
    detail: str


class SourceIntakeError(ValueError):
    def __init__(self, message: str, policy_results: List[UrlPolicyResult] | None = None) -> None:
        super().__init__(message)
        self.policy_results = policy_results or []


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_url(url: str) -> tuple[str, str]:
    raw = str(url or "").strip()
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https"}:
        return raw, "invalid_scheme"
    if not parsed.hostname:
        return raw, "invalid_host"
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
    )
    return urldefrag(urlunparse(normalized))[0], ""


def _host_patterns_from_env(name: str) -> list[str]:
    raw = str(os.getenv(name) or "").strip()
    if not raw:
        return []
    return [part.strip().lower() for part in raw.split(",") if part.strip()]


def _host_matches(host: str, patterns: Iterable[str]) -> bool:
    lowered = host.lower()
    return any(fnmatch.fnmatch(lowered, pattern) for pattern in patterns)


def evaluate_url_batch(urls: Iterable[str]) -> List[UrlPolicyResult]:
    denylist = _host_patterns_from_env("NOTECODE_WRITER_ONLY_URL_DENYLIST_HOSTS")
    allowlist = _host_patterns_from_env("NOTECODE_WRITER_ONLY_URL_ALLOWLIST_HOSTS")
    normalized_items: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    results: List[UrlPolicyResult] = []

    for raw_url in urls:
        normalized, error = _normalize_url(raw_url)
        if error:
            results.append(UrlPolicyResult(str(raw_url), normalized, False, error, "URL format is not supported"))
            continue
        if normalized in seen:
            results.append(UrlPolicyResult(str(raw_url), normalized, False, "duplicate_url", "duplicate URL"))
            continue
        seen.add(normalized)
        normalized_items.append((str(raw_url), normalized, urlparse(normalized).hostname or ""))

    if len(normalized_items) > MAX_URLS:
        return [
            UrlPolicyResult(raw, normalized, False, "too_many_urls", "URL count exceeds limit")
            for raw, normalized, _host in normalized_items
        ] + results

    for raw, normalized, host in normalized_items:
        if denylist and _host_matches(host, denylist):
            results.append(UrlPolicyResult(raw, normalized, False, "denylist_match", "host is denylisted"))
            continue
        if allowlist and not _host_matches(host, allowlist):
            results.append(UrlPolicyResult(raw, normalized, False, "not_allowlisted", "host is not allowlisted"))
            continue
        try:
            target = validate_public_url(normalized)
        except UnsafeURLError as exc:
            results.append(UrlPolicyResult(raw, normalized, False, exc.reason, "URL target is not public"))
            continue
        results.append(_evaluate_robots(raw, target.normalized_url))
    return results


def evaluate_source_batch(sources: Iterable[str]) -> List[UrlPolicyResult]:
    url_sources: list[str] = []
    local_results: list[UrlPolicyResult] = []
    malformed_sources: list[str] = []

    for source in sources:
        raw = str(source or "").strip()
        if raw.startswith(("http://", "https://")):
            url_sources.append(raw)
        elif _looks_like_local_path(raw):
            local_results.append(_evaluate_uploaded_document_path(raw))
        else:
            malformed_sources.append(raw)

    return evaluate_url_batch(url_sources) + local_results + evaluate_url_batch(malformed_sources)


def _looks_like_local_path(value: str) -> bool:
    if not value:
        return False
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return True
    if value.startswith("\\\\"):
        return True
    try:
        return Path(value).is_absolute()
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def _evaluate_uploaded_document_path(raw_path: str) -> UrlPolicyResult:
    try:
        resolved = Path(raw_path).resolve(strict=False)
        uploads_root = UPLOAD_ROOT.resolve(strict=False)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        return UrlPolicyResult(raw_path, raw_path, False, "invalid_local_path", f"local path is invalid: {exc}")

    normalized = str(resolved)
    if not _is_within_directory(resolved, uploads_root):
        return UrlPolicyResult(raw_path, normalized, False, "local_file_outside_upload_dir", "local file is outside upload directory")
    if resolved.suffix.lower() not in SUPPORTED_UPLOAD_DOCUMENT_EXTENSIONS:
        return UrlPolicyResult(raw_path, normalized, False, "unsupported_local_file_extension", "uploaded document extension is not supported")
    if not resolved.exists():
        return UrlPolicyResult(raw_path, normalized, False, "local_file_missing", "uploaded document file does not exist")
    if not resolved.is_file():
        return UrlPolicyResult(raw_path, normalized, False, "invalid_local_path", "uploaded document path is not a file")
    return UrlPolicyResult(raw_path, normalized, True, "allowed_local_file", "uploaded document allowed")


def _is_within_directory(path: Path, directory: Path) -> bool:
    return path == directory or directory in path.parents


def _evaluate_robots(raw_url: str, normalized_url: str) -> UrlPolicyResult:
    parsed = urlparse(normalized_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = safe_fetch_url(
            robots_url,
            headers={"User-Agent": USER_AGENT},
            timeout=ROBOTS_TIMEOUT,
            max_bytes=ROBOTS_READ_LIMIT,
            max_redirects=2,
        )
    except requests.Timeout:
        return UrlPolicyResult(raw_url, normalized_url, False, "robots_timeout", "robots.txt timed out")
    except ContentTooLargeError:
        return UrlPolicyResult(raw_url, normalized_url, False, "size_limit", "robots.txt too large")
    except UnsafeURLError as exc:
        return UrlPolicyResult(raw_url, normalized_url, False, exc.reason, "robots.txt target is not public")
    except (SafeFetchError, requests.RequestException):
        return UrlPolicyResult(raw_url, normalized_url, False, "robots_unavailable", "robots.txt unavailable")

    if response.status_code in {401, 403}:
        return UrlPolicyResult(raw_url, normalized_url, False, "robots_denied", "robots.txt access denied")
    if response.status_code != 200:
        return UrlPolicyResult(raw_url, normalized_url, False, "robots_unavailable", "robots.txt unavailable")
    content = bytes(response.content or b"")
    text = content.decode(response.encoding or "utf-8", errors="replace")
    parser = RobotFileParser()
    parser.parse(text.splitlines())
    if not parser.can_fetch(USER_AGENT, normalized_url):
        return UrlPolicyResult(raw_url, normalized_url, False, "robots_denied", "robots.txt disallows this path")
    return UrlPolicyResult(raw_url, normalized_url, True, "allowed", "URL allowed")


def fetch_and_store_sources(urls: Iterable[str], *, run_id: str) -> Dict[str, Any]:
    policy_results = evaluate_source_batch(urls)
    blocked = [item for item in policy_results if not item.allowed and item.reason_code != "duplicate_url"]
    if blocked:
        raise SourceIntakeError("URL policy blocked source intake", policy_results)
    allowed = [item for item in policy_results if item.allowed]
    source_root = DATA_ROOT / run_id
    source_root.mkdir(parents=True, exist_ok=True)
    bundle_sources: list[dict[str, Any]] = []
    stored_sources: list[dict[str, Any]] = []
    for index, policy in enumerate(allowed, start=1):
        if policy.reason_code == "allowed_local_file":
            stored, bundle = _store_uploaded_document(policy, source_root=source_root, index=index)
        else:
            stored, bundle = _fetch_store_one(policy, source_root=source_root, index=index)
        stored_sources.append(stored)
        bundle_sources.append(bundle)
    source_bundle = {
        "created_at": _utc_now(),
        "source_count": len(bundle_sources),
        "sources": bundle_sources,
    }
    (source_root / "source_bundle.json").write_text(
        json.dumps(source_bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "source_root": str(source_root),
        "policy_results": [item.__dict__ for item in policy_results],
        "stored_sources": stored_sources,
        "source_bundle": source_bundle,
    }


def _fetch_store_one(policy: UrlPolicyResult, *, source_root: Path, index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        response = safe_fetch_url(
            policy.normalized_url,
            headers={"User-Agent": USER_AGENT},
            timeout=BODY_TIMEOUT,
            max_bytes=BODY_READ_LIMIT,
            max_redirects=5,
        )
    except ContentTooLargeError as exc:
        raise SourceIntakeError("size_limit", [policy]) from exc
    except (SafeFetchError, requests.RequestException) as exc:
        raise SourceIntakeError(f"network_error: {exc}", [policy]) from exc
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        raise SourceIntakeError(f"http_error:{status or 'unknown'}", [policy]) from exc
    content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type not in {"text/html", "application/xhtml+xml", "text/plain", ""}:
        raise SourceIntakeError(f"unsupported_content_type: {content_type}", [policy])
    data = bytes(response.content or b"")
    encoding = _choose_response_encoding(response, data)
    raw_text = data.decode(encoding, errors="replace")
    title, full_text = _extract_text(raw_text, content_type=content_type)
    full_text = full_text[:FULL_TEXT_LIMIT]
    sha256 = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
    final_url = str(getattr(response, "safe_final_url", policy.normalized_url) or policy.normalized_url)
    stored = {
        "url": policy.url,
        "normalized_url": final_url,
        "requested_url": policy.normalized_url,
        "redirect_chain": list(getattr(response, "safe_redirect_chain", []) or []),
        "fetched_at": _utc_now(),
        "title": title,
        "full_text": full_text,
        "char_count": len(full_text),
        "policy_result": policy.__dict__,
        "sha256": sha256,
    }
    path = source_root / f"source_{index:03d}.json"
    path.write_text(json.dumps(stored, ensure_ascii=False, indent=2), encoding="utf-8")
    bundle = {
        "url": policy.url,
        "normalized_url": final_url,
        "requested_url": policy.normalized_url,
        "title": title,
        "char_count": len(full_text),
        "sha256": sha256,
        "excerpt": full_text[:EXCERPT_LIMIT],
        "claims": _extract_claims(full_text),
    }
    return {**stored, "path": str(path)}, bundle


def _store_uploaded_document(policy: UrlPolicyResult, *, source_root: Path, index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    from note.article_fetcher import ArticleFetcher

    try:
        fetched = ArticleFetcher().load_file(policy.normalized_url)
    except Exception as exc:
        raise SourceIntakeError(f"document_source_error: {exc}", [policy]) from exc

    full_text = str(fetched.content or "")[:FULL_TEXT_LIMIT]
    sha256 = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
    source_path = fetched.source_path or policy.normalized_url
    title = fetched.title or Path(source_path).stem
    stored = {
        "url": policy.url,
        "normalized_url": policy.normalized_url,
        "fetched_at": _utc_now(),
        "title": title,
        "full_text": full_text,
        "char_count": len(full_text),
        "policy_result": policy.__dict__,
        "sha256": sha256,
        "source_type": "file",
        "source_path": source_path,
        "content_type": fetched.content_type or "",
        "notices": list(fetched.notices or []),
    }
    path = source_root / f"source_{index:03d}.json"
    path.write_text(json.dumps(stored, ensure_ascii=False, indent=2), encoding="utf-8")
    bundle = {
        "url": policy.url,
        "normalized_url": policy.normalized_url,
        "title": title,
        "char_count": len(full_text),
        "sha256": sha256,
        "excerpt": full_text[:EXCERPT_LIMIT],
        "claims": _extract_claims(full_text),
        "source_type": "file",
        "source_path": source_path,
        "content_type": fetched.content_type or "",
        "notices": list(fetched.notices or []),
    }
    return {**stored, "path": str(path)}, bundle


def _choose_response_encoding(response: Any, data: bytes | None = None) -> str:
    declared = _normalize_encoding_name(getattr(response, "encoding", ""))
    apparent = _normalize_encoding_name(getattr(response, "apparent_encoding", ""))
    embedded = _encoding_from_html_bytes(data or b"")
    if embedded and (not declared or declared in _LOW_CONFIDENCE_DECLARED_ENCODINGS):
        return embedded
    if apparent and declared in _LOW_CONFIDENCE_DECLARED_ENCODINGS:
        return apparent
    return declared or apparent or "utf-8"


def _normalize_encoding_name(value: Any) -> str:
    name = str(value or "").strip().strip("\"'").lower()
    if not name:
        return ""
    try:
        return codecs.lookup(name).name
    except LookupError:
        return name


def _encoding_from_html_bytes(data: bytes) -> str:
    head = bytes(data or b"")[:4096]
    match = _EMBEDDED_ENCODING_RE.search(head)
    if not match:
        return ""
    return _normalize_encoding_name(match.group(1).decode("ascii", errors="ignore"))


def _extract_text(text: str, *, content_type: str) -> tuple[str, str]:
    if content_type == "text/plain":
        return "", _normalize_text(text)
    soup = BeautifulSoup(text, "html.parser")
    title = _normalize_text(soup.title.get_text(" ")) if soup.title else ""
    for tag in soup(["head", "script", "style", "noscript", "template", "svg", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    return title, _normalize_text(soup.get_text("\n"), drop_page_chrome=True)


def _normalize_text(text: str, *, drop_page_chrome: bool = False) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in str(text or "").splitlines()]
    if drop_page_chrome:
        lines = [line for line in lines if line.lower() not in _COMMON_PAGE_CHROME_LINES]
    return "\n".join(line for line in lines if line)


def _extract_claims(text: str) -> list[str]:
    claims: list[str] = []
    for block in _normalize_text(text).splitlines():
        sentences = re.split(r"(?<=[。！？!?])\s*", block)
        for sentence in sentences:
            cleaned = sentence.strip()
            if 24 <= len(cleaned) <= 180:
                claims.append(cleaned)
            if len(claims) >= CLAIMS_LIMIT:
                return claims
    return claims
