from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

_LANG_PATTERN = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$")
_PARAM_DIRECTIVES = {
    "max-snippet",
    "max-image-preview",
    "max-video-preview",
    "unavailable_after",
}


def _normalize_lang(value: str | None) -> str:
    raw = str(value or "").strip().lower().replace("_", "-")
    if raw == "x-default":
        return raw
    return raw


def _is_valid_lang(value: str) -> bool:
    if not value:
        return False
    if value == "x-default":
        return True
    return bool(_LANG_PATTERN.match(value))


def _canonicalize_url(url: str) -> str:
    clean, _ = urldefrag(str(url or "").strip())
    parsed = urlsplit(clean)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parsed.query, ""))


def audit_international_targeting(soup: BeautifulSoup, page_url: str) -> Dict[str, Any]:
    html_tag = soup.find("html")
    html_lang = str((html_tag or {}).get("lang") or "").strip()
    normalized_html_lang = _normalize_lang(html_lang)

    alternates: List[Dict[str, Any]] = []
    lang_counts: Dict[str, int] = {}
    normalized_page_url = _canonicalize_url(page_url)

    for link in soup.find_all("link", href=True):
        rel = link.get("rel") or []
        rel_values = [str(item).strip().lower() for item in rel] if isinstance(rel, list) else [str(rel).strip().lower()]
        if "alternate" not in rel_values:
            continue
        hreflang = _normalize_lang(link.get("hreflang"))
        if not hreflang:
            continue
        href = urljoin(page_url, str(link.get("href") or "").strip())
        normalized_href = _canonicalize_url(href)
        entry = {
            "language": hreflang,
            "href": href,
            "is_default": hreflang == "x-default",
            "is_self": normalized_href == normalized_page_url,
            "is_valid_language": _is_valid_lang(hreflang),
        }
        alternates.append(entry)
        lang_counts[hreflang] = lang_counts.get(hreflang, 0) + 1

    issues: List[Dict[str, str]] = []
    notes: List[str] = []
    status = "pass"

    def add_issue(severity: str, message: str) -> None:
        nonlocal status
        issues.append({"severity": severity, "message": message})
        if severity == "fail":
            status = "fail"
        elif severity == "warn" and status == "pass":
            status = "warn"

    if not normalized_html_lang:
        add_issue("fail", "html lang が未設定です。ページ言語を明示してください。")
    elif not _is_valid_lang(normalized_html_lang):
        add_issue("warn", f"html lang `{html_lang}` の形式が標準的ではありません。")

    if alternates:
        duplicate_langs = sorted([lang for lang, count in lang_counts.items() if count > 1 and lang != "x-default"])
        if duplicate_langs:
            add_issue("warn", f"hreflang が重複しています: {', '.join(duplicate_langs)}")

        invalid_hreflang = [entry["language"] for entry in alternates if not entry["is_valid_language"]]
        if invalid_hreflang:
            add_issue("warn", f"標準的でない hreflang 値があります: {', '.join(sorted(set(invalid_hreflang)))}")

        if normalized_html_lang:
            has_self_reference = any(
                entry["is_self"] and entry["language"] == normalized_html_lang
                for entry in alternates
            )
            if not has_self_reference:
                add_issue("warn", f"現在URLに対応する self-referencing hreflang `{normalized_html_lang}` が見つかりません。")

        locale_alternates = [entry for entry in alternates if not entry["is_default"]]
        if len(locale_alternates) >= 2 and not any(entry["is_default"] for entry in alternates):
            add_issue("warn", "複数ロケールがあるのに x-default がありません。デフォルトページがある場合は追加を検討してください。")
    else:
        notes.append("hreflang は検出されませんでした。単一言語サイトなら必須ではありません。")

    summary_parts = []
    if normalized_html_lang:
        summary_parts.append(f"html lang={normalized_html_lang}")
    else:
        summary_parts.append("html lang missing")
    if alternates:
        x_default_text = "x-defaultあり" if any(entry["is_default"] for entry in alternates) else "x-defaultなし"
        summary_parts.append(f"hreflang {len(alternates)}件 ({x_default_text})")
    else:
        summary_parts.append("hreflang なし")

    return {
        "status": status,
        "html_lang": html_lang,
        "normalized_html_lang": normalized_html_lang,
        "alternate_count": len(alternates),
        "has_x_default": any(entry["is_default"] for entry in alternates),
        "alternates": alternates,
        "issues": issues,
        "notes": notes,
        "summary": " / ".join(summary_parts),
    }


def _extract_header_values(headers: Any, header_name: str) -> List[str]:
    if headers is None:
        return []
    if hasattr(headers, "get_all"):
        values = headers.get_all(header_name) or []
        return [str(value).strip() for value in values if str(value).strip()]
    if isinstance(headers, Mapping):
        value = headers.get(header_name) or headers.get(header_name.lower())
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []
    return []


def _split_header_directives(raw_values: Iterable[str]) -> List[str]:
    directives: List[str] = []
    for raw in raw_values:
        for part in str(raw or "").split(","):
            token = part.strip()
            if token:
                directives.append(token)
    return directives


def audit_x_robots_tag(headers: Any) -> Dict[str, Any]:
    raw_values = _extract_header_values(headers, "X-Robots-Tag")
    directives = _split_header_directives(raw_values)
    issues: List[Dict[str, str]] = []
    status = "pass"

    parsed_rules: List[Dict[str, str]] = []
    global_directives: Dict[str, str] = {}

    def add_issue(severity: str, message: str) -> None:
        nonlocal status
        issues.append({"severity": severity, "message": message})
        if severity == "fail":
            status = "fail"
        elif severity == "warn" and status == "pass":
            status = "warn"

    for directive in directives:
        lowered = directive.lower()
        if ":" in lowered:
            key, value = [part.strip() for part in lowered.split(":", 1)]
            if key in _PARAM_DIRECTIVES:
                parsed_rules.append({"scope": "global", "directive": key, "value": value})
                global_directives[key] = value
            else:
                parsed_rules.append({"scope": key, "directive": value, "value": ""})
        else:
            parsed_rules.append({"scope": "global", "directive": lowered, "value": ""})
            global_directives[lowered] = ""

    if "none" in global_directives:
        add_issue("fail", "X-Robots-Tag に `none` が設定されています。検索表示とインデックスの両方を抑止します。")
    if "noindex" in global_directives:
        add_issue("fail", "X-Robots-Tag に `noindex` が設定されています。")
    if "nosnippet" in global_directives:
        add_issue("warn", "X-Robots-Tag に `nosnippet` が設定されています。検索結果やAI回答での引用露出が弱くなる可能性があります。")
    if global_directives.get("max-snippet") == "0":
        add_issue("warn", "X-Robots-Tag の `max-snippet:0` によりテキスト抜粋が抑制されています。")
    if global_directives.get("max-image-preview") == "none":
        add_issue("warn", "X-Robots-Tag の `max-image-preview:none` により画像プレビュー露出が制限されています。")
    if global_directives.get("max-video-preview") == "0":
        add_issue("warn", "X-Robots-Tag の `max-video-preview:0` により動画プレビュー露出が制限されています。")
    if "noimageindex" in global_directives:
        add_issue("warn", "X-Robots-Tag に `noimageindex` が設定されています。画像発見性に影響する可能性があります。")

    summary = "X-Robots-Tag なし"
    if directives:
        summary = "X-Robots-Tag: " + ", ".join(directives)

    return {
        "status": status,
        "raw_values": raw_values,
        "directives": directives,
        "rules": parsed_rules,
        "issues": issues,
        "summary": summary,
        "has_header": bool(directives),
    }
