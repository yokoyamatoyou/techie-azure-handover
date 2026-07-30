"""article_fetcher.py - Content acquisition module for URL/text/PDF."""
from __future__ import annotations

import io
import logging
import math
import mimetypes
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from core.app_config import get_source_reading_config
from note.safe_fetch import ContentTooLargeError, SafeFetchError, UnsafeURLError, safe_fetch_url, validate_public_url

logger = logging.getLogger(__name__)


@dataclass
class FetchedContent:
    title: str
    content: str
    url: Optional[str] = None
    source_type: str = "url"  # "url" | "file" | "image"
    source_path: Optional[str] = None
    content_type: Optional[str] = None
    notices: List[str] = field(default_factory=list)


@dataclass
class FetchFailure:
    source: str
    reason: str
    detail: str


class ArticleFetcher:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    TIMEOUT = 20
    ROBOTS_TIMEOUT = 6
    MAX_CHARS = 12000
    MAX_PAGES = 50
    MAX_FILE_BYTES = 10 * 1024 * 1024
    MAX_URL_BYTES = 10 * 1024 * 1024
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
    DOCX_EXTENSIONS = {".docx"}
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", *DOCX_EXTENSIONS, *IMAGE_EXTENSIONS}
    # NOTE: "ad" は短すぎるため部分一致だと "upfade/downfade" 等を誤検知する。
    NOISE_EXACT_TOKENS = {"ad", "ads"}
    NOISE_PREFIX_KEYWORDS = (
        "advert", "banner", "sponsor", "promo",
        "related", "recommend", "ranking", "footer",
        "sns", "share", "breadcrumb", "copyright",
        "subscribe",
    )
    PDF_PRIORITY_KEYWORDS = (
        "結論", "要点", "ポイント", "課題", "背景", "目的", "方針", "施策",
        "対策", "注意", "リスク", "影響", "比較", "分析", "根拠", "実績",
        "売上", "利益", "業績", "増加", "減少", "前年比", "計画", "戦略",
        "知的財産", "著作権", "AI", "生成AI",
    )
    HTML_MIN_CONTENT_CHARS = 260
    HTML_CANDIDATE_NOISE_RATIO_MAX = 0.45
    HTML_NOISE_LINE_PATTERNS = (
        r"(?:広告|スポンサー|PR|関連記事|おすすめ|ランキング|シェア|フォロー)",
        r"(?:プライバシー|利用規約|お問い合わせ|会社概要|採用情報|免責事項)",
        r"(?:copyright|all rights reserved|cookie policy|terms of service|privacy policy)",
        r"(?:ログイン|会員登録|メニュー|breadcrumb|パンくず)",
    )

    def __init__(self) -> None:
        source_cfg = get_source_reading_config()
        configured_max = source_cfg.get("max_chars_per_source", self.MAX_CHARS) if isinstance(source_cfg, dict) else self.MAX_CHARS
        self.MAX_CHARS = int(configured_max)

    @property
    def _uploads_dir(self) -> Path:
        return Path(__file__).resolve().parent / "uploads"

    def _is_safe_url(self, url: str) -> bool:
        """Prevent SSRF by allowing only public http(s) targets."""
        try:
            validate_public_url(url)
            return True
        except UnsafeURLError:
            return False

    def _is_safe_path(self, path: str) -> bool:
        """Prevent LFI/Directory Traversal by restricting access to the uploads directory."""
        try:
            p = Path(path).resolve()
            # Must be within UPLOAD_DIR
            uploads_dir = self._uploads_dir.resolve()
            return uploads_dir in p.parents or p == uploads_dir
        except (OSError, RuntimeError, TypeError, ValueError):
            return False

    def _redact_source_for_log(self, source: str) -> str:
        parsed = urlparse(str(source or ""))
        if parsed.scheme not in ("http", "https"):
            return str(source or "")
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        redacted = parsed._replace(
            netloc=host,
            query="[redacted]" if parsed.query else "",
            fragment="",
        )
        return redacted.geturl()

    def _robots_allows(self, url: str) -> Tuple[bool, str]:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            resp = safe_fetch_url(
                robots_url,
                headers=self.HEADERS,
                timeout=self.ROBOTS_TIMEOUT,
                max_bytes=512 * 1024,
                max_redirects=2,
            )
        except UnsafeURLError as exc:
            return False, f"安全でないrobots.txtのためブロックされました: {exc.reason}"
        except (SafeFetchError, requests.RequestException):
            return True, ""

        if resp.status_code in (401, 403):
            return False, f"robots.txt へのアクセスが拒否されました ({resp.status_code})"
        if resp.status_code >= 400:
            return True, ""

        robots_text = bytes(resp.content or b"").decode(resp.encoding or "utf-8", errors="replace")

        parser = RobotFileParser()
        parser.parse(robots_text.splitlines())
        user_agent = self.HEADERS.get("User-Agent", "*")
        if not parser.can_fetch(user_agent, url):
            return False, "robots.txt でアクセス禁止です"
        return True, ""

    def fetch_url(self, url: str) -> FetchedContent:
        """Fetch content from a URL (HTML or PDF)."""
        if not self._is_safe_url(url):
            raise ValueError("CRITICAL: Access to internal or unsafe URL blocked")
        allowed, reason = self._robots_allows(url)
        if not allowed:
            raise ValueError(f"CRITICAL: robots.txt disallows crawling: {reason}")
        data, content_type, header_encoding, apparent_encoding = self._fetch_url_payload(url)
        parsed, _ = self._parse_url_payload(
            url=url,
            data=data,
            content_type=content_type,
            header_encoding=header_encoding,
            apparent_encoding=apparent_encoding,
            persist_image=True,
        )
        return parsed

    def check_scraping_allowed(self, url: str) -> Tuple[bool, str]:
        """Check robots.txt policy for a URL (best-effort)."""
        if not self._is_safe_url(url):
            return False, "安全でないURLのためブロックされました"
        return self._robots_allows(url)

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate URL format/safety/robots and endpoint accessibility before adding."""
        parsed = urlparse(url or "")
        if parsed.scheme not in ("http", "https"):
            return False, "URLはhttp/httpsで入力してください"
        if not parsed.netloc:
            return False, "URLの形式が不正です（ホスト名がありません）"
        if not self._is_safe_url(url):
            return False, "安全でないURLのためブロックされました"

        allowed, reason = self._robots_allows(url)
        if not allowed:
            return False, f"スクレイピング禁止です: {reason}"

        try:
            data, content_type, header_encoding, apparent_encoding = self._fetch_url_payload(url)
            parsed_content, used_encoding = self._parse_url_payload(
                url=url,
                data=data,
                content_type=content_type,
                header_encoding=header_encoding,
                apparent_encoding=apparent_encoding,
                persist_image=False,
            )
            if parsed_content.source_type == "url" and not parsed_content.content:
                return False, "URL本文を抽出できませんでした"
            logger.info(
                "Validated URL content: url=%s content_type=%s chars=%s notices=%s used_encoding=%s",
                url,
                parsed_content.content_type or content_type,
                len(parsed_content.content or ""),
                len(parsed_content.notices or []),
                used_encoding or "",
            )
        except requests.HTTPError as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (401, 403):
                return False, f"アクセス拒否のため取得できません ({status})"
            if status is not None:
                return False, f"URLにアクセスできません ({status})"
            return False, f"URL接続に失敗しました: {type(exc).__name__}"
        except requests.RequestException as exc:
            return False, f"URL接続に失敗しました: {type(exc).__name__}"
        except (ValueError, RuntimeError, OSError) as exc:
            return False, f"URL本文の検証に失敗しました: {exc}"
        return True, ""

    def _fetch_url_payload(
        self,
        url: str,
    ) -> Tuple[bytes, str, Optional[str], Optional[str]]:
        try:
            resp = safe_fetch_url(
                url,
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
                max_bytes=self.MAX_URL_BYTES,
                max_redirects=5,
            )
        except ContentTooLargeError as exc:
            raise ValueError("CRITICAL: URL content too large (>10MB)") from exc
        except UnsafeURLError as exc:
            raise ValueError(f"CRITICAL: unsafe URL blocked: {exc.reason}") from exc
        except SafeFetchError as exc:
            raise ValueError(f"CRITICAL: URL fetch blocked: {exc}") from exc
        resp.raise_for_status()
        content_type = (resp.headers.get("content-type") or "").lower()
        data = bytes(resp.content or b"")
        header_encoding = self._extract_charset_from_content_type(content_type)
        apparent_encoding = self._detect_apparent_encoding(data)
        return data, content_type, header_encoding, apparent_encoding

    def _parse_url_payload(
        self,
        *,
        url: str,
        data: bytes,
        content_type: str,
        header_encoding: Optional[str],
        apparent_encoding: Optional[str],
        persist_image: bool,
    ) -> Tuple[FetchedContent, Optional[str]]:
        if content_type.startswith("image/") or self._has_image_extension(url):
            if persist_image:
                return self._store_url_image(data, url=url, content_type=content_type), None
            return (
                FetchedContent(
                    title=self._title_from_url(url) or "画像",
                    content="",
                    url=url,
                    source_type="image",
                    content_type=content_type or "image/png",
                ),
                None,
            )
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            title = self._title_from_url(url)
            parsed_pdf = self._parse_pdf_bytes(
                data,
                title=title,
                url=url,
                content_type=content_type,
            )
            return parsed_pdf, None

        html, used_encoding = self._decode_html_bytes(
            data,
            header_encoding=header_encoding,
            apparent_encoding=apparent_encoding,
        )
        logger.info(
            "Decoded HTML: url=%s content_type=%s header_encoding=%s apparent_encoding=%s used_encoding=%s",
            url,
            content_type,
            header_encoding or "",
            apparent_encoding or "",
            used_encoding,
        )
        parsed_html = self._parse_html(html, url=url, content_type=content_type)
        return parsed_html, used_encoding

    def load_file(self, path: str) -> FetchedContent:
        """Load text/PDF/DOCX from a local file path with safety check."""
        if not self._is_safe_path(path):
            raise ValueError(f"CRITICAL: Unauthorized file access blocked: {path}")
            
        p = Path(path)
        if p.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"CRITICAL: Unsupported file extension: {p.suffix}")
        if p.exists() and p.stat().st_size > self.MAX_FILE_BYTES:
            raise ValueError(f"CRITICAL: File too large (>10MB): {path}")
            
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = p.suffix.lower()
        if suffix in self.IMAGE_EXTENSIONS:
            mime = mimetypes.guess_type(str(p))[0] or "image/png"
            return FetchedContent(
                title=p.stem,
                content="",
                source_type="image",
                source_path=str(p),
                content_type=mime,
            )
        if suffix == ".pdf":
            return self._parse_pdf_bytes(
                p.read_bytes(),
                title=p.stem,
                source_path=str(p),
                content_type="application/pdf",
            )
        if suffix == ".docx":
            return self._parse_docx_bytes(
                p.read_bytes(),
                title=p.stem,
                source_path=str(p),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        content = p.read_text(encoding="utf-8", errors="ignore")
        content = self._normalize_text(content)
        content, text_notice = self._truncate_with_notice(content)
        notices: List[str] = []
        if text_notice:
            notices.append(text_notice)
        return FetchedContent(
            title=p.stem,
            content=content,
            source_type="file",
            source_path=str(p),
            content_type="text/plain",
            notices=notices,
        )

    def _normalize_source(self, source: Any) -> str:
        if isinstance(source, Path):
            return str(source)
        if isinstance(source, str):
            return source
        value = getattr(source, "value", None)
        if value is not None:
            return str(value)
        if isinstance(source, dict) and "value" in source:
            return str(source["value"])
        return str(source)

    def fetch(self, source: Any) -> FetchedContent:
        """Auto-detect URL vs local file."""
        normalized = self._normalize_source(source)
        if normalized.startswith(("http://", "https://")):
            return self.fetch_url(normalized)
        return self.load_file(normalized)

    def _classify_fetch_error(self, source: str, exc: Exception) -> FetchFailure:
        detail = str(exc)
        if isinstance(exc, requests.HTTPError):
            status = getattr(getattr(exc, "response", None), "status_code", None)
            detail = f"http_status:{status or 'unknown'}"
        elif isinstance(exc, requests.RequestException):
            detail = type(exc).__name__
        if "robots.txt" in detail:
            return FetchFailure(source=source, reason="robots_blocked", detail=detail)
        if "CRITICAL: Access to internal or unsafe URL blocked" in detail:
            return FetchFailure(source=source, reason="invalid_or_unsafe_url", detail=detail)
        if "UNSAFE_URL:" in detail or "CRITICAL: unsafe URL blocked" in detail:
            return FetchFailure(source=source, reason="invalid_or_unsafe_url", detail=detail)
        if "TOO_MANY_REDIRECTS:" in detail:
            return FetchFailure(source=source, reason="redirect_not_supported", detail=detail)
        if "CRITICAL: Unauthorized file access blocked" in detail:
            return FetchFailure(source=source, reason="unauthorized_file_path", detail=detail)
        if "File not found:" in detail:
            return FetchFailure(source=source, reason="file_not_found", detail=detail)
        if "PDF extractor not available" in detail:
            return FetchFailure(source=source, reason="pdf_extractor_missing", detail=detail)
        if "No extractable text found in PDF" in detail:
            return FetchFailure(source=source, reason="pdf_no_text", detail=detail)
        if "PDF parsing failed" in detail:
            return FetchFailure(source=source, reason="pdf_parse_failed", detail=detail)
        if "DOCX extractor not available" in detail:
            return FetchFailure(source=source, reason="docx_extractor_missing", detail=detail)
        if "No extractable text found in DOCX" in detail:
            return FetchFailure(source=source, reason="docx_no_text", detail=detail)
        if "DOCX parsing failed" in detail:
            return FetchFailure(source=source, reason="docx_parse_failed", detail=detail)
        if isinstance(exc, requests.HTTPError):
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 403:
                return FetchFailure(source=source, reason="http_403_forbidden", detail=detail)
            return FetchFailure(source=source, reason="http_error", detail=detail)
        if isinstance(exc, requests.RequestException):
            return FetchFailure(source=source, reason="network_error", detail=detail)
        return FetchFailure(source=source, reason="fetch_failed", detail=detail)

    def fetch_multiple_with_errors(
        self,
        sources: List[Any],
        request_id: str = "",
    ) -> Tuple[List[FetchedContent], List[FetchFailure]]:
        """Fetch multiple sources and return both results and failures."""
        results: List[FetchedContent] = []
        failures: List[FetchFailure] = []
        for source in sources:
            normalized = self._normalize_source(source)
            started = time.monotonic()
            try:
                fetched = self.fetch(normalized)
                elapsed_ms = int((time.monotonic() - started) * 1000)
                results.append(fetched)
                logger.info(
                    "Fetched source: request_id=%s source=%s source_type=%s content_type=%s chars=%s notices=%s elapsed_ms=%s",
                    request_id,
                    self._redact_source_for_log(fetched.url or fetched.source_path or normalized),
                    fetched.source_type,
                    fetched.content_type or "",
                    len(fetched.content or ""),
                    len(fetched.notices or []),
                    elapsed_ms,
                )
            except (
                ValueError,
                FileNotFoundError,
                RuntimeError,
                OSError,
                requests.RequestException,
            ) as exc:
                elapsed_ms = int((time.monotonic() - started) * 1000)
                failure = self._classify_fetch_error(normalized, exc)
                failures.append(failure)
                logger.warning(
                    "Failed to fetch source: request_id=%s source=%s reason=%s elapsed_ms=%s detail=%s",
                    request_id,
                    self._redact_source_for_log(normalized),
                    failure.reason,
                    elapsed_ms,
                    failure.detail,
                )
        return results, failures

    def fetch_multiple(self, sources: List[Any], request_id: str = "") -> List[FetchedContent]:
        """Backward-compatible wrapper that ignores failures."""
        results, _ = self.fetch_multiple_with_errors(sources, request_id=request_id)
        return results

    def _has_noise_marker(self, attrs: str) -> bool:
        lowered = (attrs or "").lower()
        if not lowered:
            return False
        tokens = [token for token in re.split(r"[^a-z0-9]+", lowered) if token]
        if not tokens:
            return False
        token_set = set(tokens)
        if any(marker in token_set for marker in self.NOISE_EXACT_TOKENS):
            return True
        for token in tokens:
            if any(token.startswith(prefix) for prefix in self.NOISE_PREFIX_KEYWORDS):
                return True
        return False

    def _is_noise_line(self, line: str) -> bool:
        stripped = (line or "").strip()
        if not stripped:
            return True
        compact = re.sub(r"\s+", "", stripped)
        if len(compact) <= 1:
            return True
        if re.fullmatch(r"[\W_]+", compact):
            return True
        for pattern in self.HTML_NOISE_LINE_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                return True
        return False

    def _clean_html_root(self, root: Any) -> Any:
        for tag in root.find_all(
            [
                "script",
                "style",
                "noscript",
                "iframe",
                "nav",
                "footer",
                "aside",
                "header",
                "table",
                "thead",
                "tbody",
                "tfoot",
                "tr",
                "td",
                "th",
            ]
        ):
            tag.decompose()
        for tag in root.find_all(True):
            if tag.parent is None:
                continue
            attrs = " ".join(
                [
                    str(tag.get("id", "")),
                    " ".join(
                        tag.get("class", [])
                        if isinstance(tag.get("class"), list)
                        else [str(tag.get("class", ""))]
                    ),
                    str(tag.get("role", "")),
                    str(tag.get("aria-label", "")),
                ]
            ).lower()
            if attrs and self._has_noise_marker(attrs):
                tag.decompose()
        return root

    def _extract_text_from_html_root(self, root: Any) -> Dict[str, Any]:
        cloned = BeautifulSoup(str(root), "html.parser")
        candidate_root = cloned.find("body") or cloned
        cleaned = self._clean_html_root(candidate_root)
        raw_text = cleaned.get_text(separator="\n", strip=True)
        raw_lines = [line.strip() for line in raw_text.splitlines() if line and line.strip()]
        normalized = self._normalize_text(raw_text)
        line_count = len(raw_lines)
        if line_count <= 0:
            return {"text": normalized, "chars": len(normalized), "noise_ratio": 1.0}
        noise_lines = sum(1 for line in raw_lines if self._is_noise_line(line))
        noise_ratio = noise_lines / max(1, line_count)
        return {
            "text": normalized,
            "chars": len(normalized),
            "line_count": line_count,
            "noise_ratio": noise_ratio,
        }

    def _extract_html_fallback_text(self, soup: BeautifulSoup) -> str:
        cloned = BeautifulSoup(str(soup), "html.parser")
        root = cloned.body or cloned
        for tag in root.find_all(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        lines: List[str] = []
        for tag in root.find_all(["h1", "h2", "h3", "h4", "h5", "p", "li", "blockquote"]):
            line = tag.get_text(" ", strip=True)
            if not line:
                continue
            if self._is_noise_line(line):
                continue
            lines.append(line)
        fallback = self._normalize_text("\n".join(lines))
        if len(fallback) >= self.HTML_MIN_CONTENT_CHARS:
            return fallback
        raw = root.get_text(separator="\n", strip=True)
        filtered_lines = [
            line.strip()
            for line in raw.splitlines()
            if line and line.strip() and not self._is_noise_line(line)
        ]
        return self._normalize_text("\n".join(filtered_lines))

    def _extract_best_html_text(self, soup: BeautifulSoup) -> Tuple[str, Optional[str]]:
        roots: List[Tuple[str, Any]] = []
        for label, candidate in (
            ("article", soup.find("article")),
            ("main", soup.find("main")),
            ("body", soup.body),
            ("document", soup),
        ):
            if candidate is None:
                continue
            if any(candidate is existing for _, existing in roots):
                continue
            roots.append((label, candidate))

        scores: List[Dict[str, Any]] = []
        priority = {"article": 4, "main": 3, "body": 2, "document": 1}
        for label, root in roots:
            result = self._extract_text_from_html_root(root)
            result["label"] = label
            result["priority"] = priority.get(label, 0)
            scores.append(result)

        candidates = [item for item in scores if int(item.get("chars", 0) or 0) > 0]
        if not candidates:
            fallback = self._extract_html_fallback_text(soup)
            return fallback, "本文候補が空だったため代替抽出を適用しました。"

        filtered = [
            item
            for item in candidates
            if float(item.get("noise_ratio", 1.0) or 1.0) <= self.HTML_CANDIDATE_NOISE_RATIO_MAX
        ]
        pool = filtered if filtered else candidates
        selected = max(
            pool,
            key=lambda item: (
                int(item.get("chars", 0) or 0),
                -float(item.get("noise_ratio", 1.0) or 1.0),
                int(item.get("priority", 0) or 0),
            ),
        )
        selected_text = str(selected.get("text") or "")
        if len(selected_text) >= self.HTML_MIN_CONTENT_CHARS:
            return selected_text, None

        fallback = self._extract_html_fallback_text(soup)
        if len(fallback) > len(selected_text):
            logger.info(
                "HTML fallback extraction used: selected_label=%s selected_chars=%s fallback_chars=%s",
                selected.get("label", ""),
                len(selected_text),
                len(fallback),
            )
            return fallback, "本文が短いため代替抽出を適用しました。"
        return selected_text, None

    def _parse_html(self, html: str, url: Optional[str], content_type: str) -> FetchedContent:
        soup = BeautifulSoup(html, "html.parser")
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        if not title and url:
            title = self._title_from_url(url)
        notices: List[str] = []
        extraction_notice: Optional[str] = None
        try:
            text, extraction_notice = self._extract_best_html_text(soup)
            if extraction_notice:
                notices.append(extraction_notice)
        except Exception as exc:
            logger.warning("HTML extraction failed. Falling back to body text (fail-open).")
            logger.debug("HTML extraction fallback detail.", exc_info=exc)
            fallback_root = soup.body or soup
            text = self._normalize_text(fallback_root.get_text(separator="\n", strip=True))

        text, text_notice = self._truncate_with_notice(text)
        if text_notice:
            notices.append(text_notice)
        return FetchedContent(
            title=title,
            content=text,
            url=url,
            source_type="url",
            content_type=content_type,
            notices=notices,
        )

    def _parse_pdf_bytes(
        self,
        data: bytes,
        title: str,
        url: Optional[str] = None,
        source_path: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> FetchedContent:
        text, meta_title, page_notice = self._extract_pdf_text(data)
        final_title = meta_title or title or (self._title_from_url(url) if url else "PDF")
        text = self._normalize_text(text)
        text, text_notice = self._truncate_with_notice(text)
        notices: List[str] = []
        if page_notice:
            notices.append(page_notice)
        if text_notice:
            notices.append(text_notice)
        return FetchedContent(
            title=final_title,
            content=text,
            url=url,
            source_type="file" if source_path else "url",
            source_path=source_path,
            content_type=content_type or "application/pdf",
            notices=notices,
        )

    def _parse_docx_bytes(
        self,
        data: bytes,
        title: str,
        source_path: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> FetchedContent:
        text = self._extract_docx_text(data)
        text = self._normalize_text(text)
        text, text_notice = self._truncate_with_notice(text)
        notices: List[str] = []
        if text_notice:
            notices.append(text_notice)
        return FetchedContent(
            title=title or "DOCX",
            content=text,
            source_type="file",
            source_path=source_path,
            content_type=content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            notices=notices,
        )

    def _extract_pdf_text(self, data: bytes) -> Tuple[str, Optional[str], Optional[str]]:
        """Extract text from PDF bytes using available backends."""
        parse_errors: List[str] = []
        backend_available = False
        empty_text = False

        try:
            import pdfplumber  # type: ignore
            backend_available = True

            with pdfplumber.open(io.BytesIO(data)) as pdf:
                total_pages = len(pdf.pages)
                limited = total_pages > self.MAX_PAGES
                pages_to_read = pdf.pages[: self.MAX_PAGES] if limited else pdf.pages
                pages = [page.extract_text() or "" for page in pages_to_read]
                meta = pdf.metadata or {}
            text, compressed = self._build_pdf_digest_text(pages, self.MAX_CHARS)
            if text:
                notice_parts: List[str] = []
                if limited:
                    notice_parts.append(f"PDFは{total_pages}ページのため、先頭{self.MAX_PAGES}ページのみ取り込みました。")
                if compressed:
                    notice_parts.append(
                        f"取り込んだPDF本文を全体から要点抽出し、{self.MAX_CHARS}文字以内に圧縮しました。"
                    )
                notice = " ".join(notice_parts) if notice_parts else None
                return text, meta.get("Title") or meta.get("title"), notice
            empty_text = True
        except Exception as exc:
            parse_errors.append(f"pdfplumber:{type(exc).__name__}")
            logger.debug("pdfplumber extraction failed, falling back to pypdf", exc_info=exc)

        try:
            from pypdf import PdfReader  # type: ignore
            backend_available = True

            reader = PdfReader(io.BytesIO(data))
            total_pages = len(reader.pages)
            limited = total_pages > self.MAX_PAGES
            pages_to_read = reader.pages[: self.MAX_PAGES] if limited else reader.pages
            pages = [page.extract_text() or "" for page in pages_to_read]
            meta = reader.metadata or {}
            text, compressed = self._build_pdf_digest_text(pages, self.MAX_CHARS)
            title = None
            if isinstance(meta, dict):
                title = meta.get("/Title") or meta.get("Title")
            if text:
                notice_parts: List[str] = []
                if limited:
                    notice_parts.append(f"PDFは{total_pages}ページのため、先頭{self.MAX_PAGES}ページのみ取り込みました。")
                if compressed:
                    notice_parts.append(
                        f"取り込んだPDF本文を全体から要点抽出し、{self.MAX_CHARS}文字以内に圧縮しました。"
                    )
                notice = " ".join(notice_parts) if notice_parts else None
                return text, title, notice
            empty_text = True
        except Exception as exc:
            parse_errors.append(f"pypdf:{type(exc).__name__}")

        if not backend_available:
            raise RuntimeError(
                f"PDF extractor not available. Install 'pdfplumber' or 'pypdf'. (python={sys.executable})"
            )

        if empty_text:
            raise RuntimeError(
                "No extractable text found in PDF (image-based scan or protected content)."
            )

        reason = ", ".join(parse_errors[:3]) if parse_errors else "unknown"
        raise RuntimeError(f"PDF parsing failed. backends_tried={reason}")

    def _build_pdf_digest_text(self, pages: List[str], max_chars: int) -> Tuple[str, bool]:
        cleaned_pages = [re.sub(r"\s+", " ", (page or "")).strip() for page in pages if (page or "").strip()]
        if not cleaned_pages:
            return "", False

        full_text = "\n".join(cleaned_pages).strip()
        if len(full_text) <= max_chars:
            return full_text, False

        candidates: List[Tuple[int, str, int]] = []
        for page_index, page_text in enumerate(cleaned_pages):
            sentences = self._split_sentences(page_text)
            if not sentences:
                continue
            first = sentences[0]
            candidates.append((page_index, first, self._score_pdf_sentence(first) + 2))
            if len(sentences) > 1:
                best = max(sentences[:12], key=self._score_pdf_sentence)
                if best != first:
                    candidates.append((page_index, best, self._score_pdf_sentence(best)))

        if not candidates:
            return full_text[:max_chars], True

        bucket_count = min(8, max(3, len(cleaned_pages)))
        bucket_size = max(1, math.ceil(len(cleaned_pages) / bucket_count))

        selected: List[Tuple[int, str, int]] = []
        seen_norm: set[str] = set()
        per_page_count: Dict[int, int] = {}

        # Pass 1: one strong sentence per bucket to keep document-wide coverage.
        for bucket in range(bucket_count):
            start = bucket * bucket_size
            end = min(len(cleaned_pages), (bucket + 1) * bucket_size)
            pool = [c for c in candidates if start <= c[0] < end]
            if not pool:
                continue
            best = max(pool, key=lambda x: x[2])
            norm = re.sub(r"\s+", "", best[1])
            if norm and norm not in seen_norm:
                selected.append(best)
                seen_norm.add(norm)
                per_page_count[best[0]] = 1

        # Pass 2: fill with high-score sentences while avoiding over-concentration.
        for page_index, sentence, score in sorted(candidates, key=lambda x: x[2], reverse=True):
            norm = re.sub(r"\s+", "", sentence)
            if not norm or norm in seen_norm:
                continue
            if per_page_count.get(page_index, 0) >= 2:
                continue
            selected.append((page_index, sentence, score))
            seen_norm.add(norm)
            per_page_count[page_index] = per_page_count.get(page_index, 0) + 1
            if len(selected) >= 36:
                break

        selected.sort(key=lambda x: (x[0], -x[2]))
        lines: List[str] = []
        total_len = 0
        reserve = 40
        for page_index, sentence, _ in selected:
            line = f"[p{page_index + 1}] {sentence}"
            add_len = len(line) + (1 if lines else 0)
            if total_len + add_len > max_chars - reserve:
                continue
            lines.append(line)
            total_len += add_len

        if not lines:
            # Final fallback: distributed snippets from head/middle/tail pages.
            sample_count = min(6, len(cleaned_pages))
            indices = sorted(
                {
                    round(i * (len(cleaned_pages) - 1) / max(1, sample_count - 1))
                    for i in range(sample_count)
                }
            )
            for idx in indices:
                snippet = cleaned_pages[idx][:220]
                line = f"[p{idx + 1}] {snippet}"
                if total_len + len(line) + 1 > max_chars - reserve:
                    break
                lines.append(line)
                total_len += len(line) + 1

        digest = "\n".join(lines).strip()
        if not digest:
            digest = full_text[:max_chars]
        return digest, True

    def _split_sentences(self, text: str) -> List[str]:
        if not text:
            return []
        raw_parts = re.split(r"(?<=[。！？.!?])\s+|\n+", text)
        result: List[str] = []
        for part in raw_parts:
            sentence = part.strip(" \t-・")
            if not sentence:
                continue
            if len(sentence) < 16:
                continue
            if len(sentence) > 220:
                sentence = sentence[:220].rstrip()
            result.append(sentence)
        return result

    def _score_pdf_sentence(self, sentence: str) -> int:
        score = 0
        if re.search(r"\d", sentence):
            score += 2
        if re.search(r"(％|%|円|億|万|件|社|人|年|月)", sentence):
            score += 1
        for keyword in self.PDF_PRIORITY_KEYWORDS:
            if keyword in sentence:
                score += 1
        length = len(sentence)
        if 24 <= length <= 120:
            score += 2
        elif length <= 180:
            score += 1
        if re.search(r"(目次|脚注|出典|copyright|all rights reserved)", sentence, re.I):
            score -= 2
        return score

    def _extract_docx_text(self, data: bytes) -> str:
        try:
            from docx import Document  # type: ignore
        except Exception as exc:
            raise RuntimeError("DOCX extractor not available. Install 'python-docx'.") from exc

        try:
            doc = Document(io.BytesIO(data))
        except Exception as exc:
            raise RuntimeError(f"DOCX parsing failed. parser={type(exc).__name__}") from exc

        lines: List[str] = []
        for paragraph in doc.paragraphs:
            line = (paragraph.text or "").strip()
            if line:
                lines.append(line)

        text = "\n".join(lines).strip()
        if not text:
            raise RuntimeError("No extractable text found in DOCX.")
        return text

    def _title_from_url(self, url: str) -> str:
        if not url:
            return ""
        name = url.split("/")[-1]
        name = re.sub(r"\?.*$", "", name)
        return name or url

    def _normalize_text(self, text: str) -> str:
        # Pre-limit to avoid CPU exhaustion during regex on massive strings
        text = text[: self.MAX_CHARS * 2]
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            compact = re.sub(r"\s+", "", line)
            if not compact:
                continue
            # Drop highly tabular/noise lines to prioritize prose text.
            digits = sum(1 for ch in compact if ch.isdigit())
            digit_ratio = digits / max(1, len(compact))
            col_like = bool(re.search(r"\t|\s{2,}|\|", line))
            if digit_ratio >= 0.55 and col_like:
                continue
            if len(line) <= 2 and re.search(r"^\d+$", line):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    def _has_image_extension(self, url: str) -> bool:
        lower = url.lower()
        return any(lower.endswith(ext) for ext in self.IMAGE_EXTENSIONS)

    def _store_url_image(self, data: bytes, url: str, content_type: str) -> FetchedContent:
        uploads_dir = self._uploads_dir
        uploads_dir.mkdir(parents=True, exist_ok=True)
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None
        if not ext:
            for candidate in self.IMAGE_EXTENSIONS:
                if url.lower().endswith(candidate):
                    ext = candidate
                    break
        ext = ext or ".png"
        filename = f"{uuid.uuid4().hex}{ext}"
        dest = uploads_dir / filename
        dest.write_bytes(data)
        mime = content_type or mimetypes.guess_type(str(dest))[0] or "image/png"
        return FetchedContent(
            title=self._title_from_url(url) or "画像",
            content="",
            url=url,
            source_type="image",
            source_path=str(dest),
            content_type=mime,
        )

    def _truncate(self, text: str) -> str:
        if len(text) <= self.MAX_CHARS:
            return text
        return text[: self.MAX_CHARS]

    def _truncate_with_notice(self, text: str) -> Tuple[str, Optional[str]]:
        raw_len = len(text)
        if raw_len <= self.MAX_CHARS:
            return text, None
        truncated = text[: self.MAX_CHARS]
        notice = (
            f"抽出文字数{raw_len}文字が上限{self.MAX_CHARS}文字を超えたため、"
            f"先頭{self.MAX_CHARS}文字のみ取り込みました。"
        )
        return truncated, notice

    def _extract_charset_from_content_type(self, content_type: str) -> Optional[str]:
        if not content_type:
            return None
        match = re.search(r"charset\s*=\s*([a-zA-Z0-9_\-]+)", content_type, re.IGNORECASE)
        if not match:
            return None
        return match.group(1).strip()

    def _extract_meta_charset(self, data: bytes) -> Optional[str]:
        head = data[:8192]
        match = re.search(
            br"<meta[^>]+charset\s*=\s*[\"']?\s*([a-zA-Z0-9_\-]+)",
            head,
            re.IGNORECASE,
        )
        if not match:
            match = re.search(
                br"<meta[^>]+content\s*=\s*[\"'][^\"']*charset=([a-zA-Z0-9_\-]+)",
                head,
                re.IGNORECASE,
            )
        if not match:
            return None
        return match.group(1).decode("ascii", errors="ignore").strip() or None

    def _decode_html_bytes(
        self,
        data: bytes,
        *,
        header_encoding: Optional[str],
        apparent_encoding: Optional[str],
    ) -> Tuple[str, str]:
        candidates: List[str] = []

        def _push(enc: Optional[str]) -> None:
            if not enc:
                return
            normalized = enc.strip()
            if not normalized:
                return
            lower = normalized.lower()
            if lower in {"iso-8859-1", "latin-1", "latin1"}:
                # text/html で charset 未指定時の既定値が入りやすいため優先しない
                return
            if all(lower != c.lower() for c in candidates):
                candidates.append(normalized)

        _push(header_encoding)
        _push(self._extract_meta_charset(data))
        _push(apparent_encoding)
        _push("utf-8")
        _push("cp932")
        _push("shift_jis")

        for enc in candidates:
            try:
                return data.decode(enc, errors="strict"), enc
            except Exception:
                continue

        # 最後の保険: 破損を最小化して復元
        logger.debug(
            "All charset candidates failed. Falling back to utf-8-ignore. candidates=%s",
            candidates,
        )
        return data.decode("utf-8", errors="ignore"), "utf-8-ignore"

    def _detect_apparent_encoding(self, data: bytes) -> Optional[str]:
        if not data:
            return None
        try:
            from charset_normalizer import from_bytes  # type: ignore

            best = from_bytes(data).best()
            if best and getattr(best, "encoding", None):
                return str(best.encoding)
        except Exception:
            pass
        try:
            import chardet  # type: ignore

            detected = chardet.detect(data or b"")
            encoding = (detected or {}).get("encoding")
            return str(encoding) if encoding else None
        except Exception:
            return None

    def _read_response_bytes(self, resp: requests.Response, limit: int) -> bytes:
        """Read response content with a hard size limit."""
        chunks: List[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > limit:
                raise ValueError("CRITICAL: URL content too large (>10MB)")
            chunks.append(chunk)
        return b"".join(chunks)
