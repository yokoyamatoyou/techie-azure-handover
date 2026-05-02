from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from analysis_core.common_constants import COMPOUND_PUBLIC_SUFFIXES, GENERIC_BRAND_TOKENS, NOISY_CITATION_SUBDOMAINS
from analysis_core.text_utils import dedupe_preserve_order, normalize_text


def normalize_domain_host(value: Any) -> str:
    raw = normalize_text(str(value or ""))
    if not raw:
        return ""
    candidate = raw if "://" in raw else f"https://{raw}"
    parsed = urlparse(candidate)
    host = normalize_text((parsed.netloc or parsed.path or "").lower())
    if host.startswith("www."):
        host = host[4:]
    host = host.split("/")[0]
    host = host.split(":")[0]
    return host


def normalize_citation_domain(value: Any) -> str:
    host = normalize_domain_host(value)
    if not host:
        return ""
    labels = [part for part in host.split(".") if part]
    while len(labels) > 2 and labels[0] in NOISY_CITATION_SUBDOMAINS:
        labels = labels[1:]
    if len(labels) <= 2:
        return ".".join(labels)
    compound_suffix = ".".join(labels[-2:])
    if compound_suffix in COMPOUND_PUBLIC_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text))


def _build_match_pattern(term: str) -> str:
    escaped = re.escape(term)
    return escaped.replace(r"\ ", r"[\s\-_/]*")


def _contains_named_term(haystack: str, term: str) -> bool:
    normalized_term = normalize_text(term).lower()
    if not normalized_term:
        return False
    if _contains_cjk(normalized_term):
        return normalized_term in haystack
    pattern = _build_match_pattern(normalized_term)
    return re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", haystack) is not None


def _candidate_aliases(term: str) -> list[str]:
    normalized = normalize_text(term)
    if not normalized:
        return []
    aliases: list[str] = [normalized, normalized.lower()]

    citation_domain = normalize_citation_domain(normalized)
    if citation_domain:
        aliases.append(citation_domain)
        labels = citation_domain.split(".")
        if labels:
            aliases.append(labels[0])

    lowered = normalized.lower()
    ascii_tokens = [
        token
        for token in re.split(r"[^a-z0-9]+", lowered)
        if token and token not in GENERIC_BRAND_TOKENS and len(token) >= 3
    ]
    aliases.extend(ascii_tokens)
    if len(ascii_tokens) >= 2:
        aliases.append("".join(ascii_tokens))
        aliases.append(" ".join(ascii_tokens))

    compact = re.sub(r"[\s\-_/]+", "", lowered)
    if compact and compact not in GENERIC_BRAND_TOKENS and (len(compact) >= 3 or _contains_cjk(compact)):
        aliases.append(compact)
    return dedupe_preserve_order(aliases)
