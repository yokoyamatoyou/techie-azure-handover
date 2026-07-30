"""Build post-success image context from writer-only generation artifacts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


DEFAULT_ARTICLE_TYPE = "explanatory_article"
LEAD_MAX_CHARS = 260
SOURCE_CLAIMS_LIMIT = 6
IMAGE_ARTICLE_TYPE_ALIASES = {
    "company_introduction": "company_introduction",
    "company_service_intro": "company_introduction",
    "product_introduction": "company_introduction",
    "industry_analysis": "explanatory_article",
    "market_explanation": "explanatory_article",
    "comparison_guide": "comparative_review",
    "daily_activity": "daily_story",
}


def build_writer_only_image_context(
    result: Mapping[str, Any],
    artifact_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return the small context needed before post-success image generation."""
    body = _first_text(result.get("body"), result.get("full_text"))
    root = _resolve_artifact_root(result, artifact_root)
    brief = _load_json(root / "brief.json") if root else {}
    input_contract = _load_json(root / "input_contract.json") if root else {}
    source_bundle = _load_source_bundle(root, brief)

    return {
        "title": _first_text(result.get("title"), _extract_h1(body), "writer-only draft"),
        "lead": _shorten(_first_text(result.get("lead"), _first_non_heading_paragraph(body)), LEAD_MAX_CHARS),
        "body": body,
        "article_type": _resolve_image_article_type(result, brief, input_contract),
        "source_claims": _extract_source_claims(source_bundle, limit=SOURCE_CLAIMS_LIMIT),
        "source_context_note": "Source context uses source claims and metadata only.",
    }


def _resolve_image_article_type(
    result: Mapping[str, Any],
    brief: Mapping[str, Any],
    input_contract: Mapping[str, Any],
) -> str:
    explicit = _first_text(result.get("image_article_type"), input_contract.get("image_article_type"))
    if explicit:
        return IMAGE_ARTICLE_TYPE_ALIASES.get(explicit, explicit)
    semantic_key = _first_text(result.get("semantic_article_key"), input_contract.get("semantic_article_key"))
    if semantic_key in IMAGE_ARTICLE_TYPE_ALIASES:
        return IMAGE_ARTICLE_TYPE_ALIASES[semantic_key]
    raw = _first_text(brief.get("internal_category"), input_contract.get("article_type"), result.get("article_type"), DEFAULT_ARTICLE_TYPE)
    return IMAGE_ARTICLE_TYPE_ALIASES.get(raw, raw)


def _resolve_artifact_root(result: Mapping[str, Any], artifact_root: str | Path | None) -> Path | None:
    raw = artifact_root if artifact_root is not None else result.get("artifact_root")
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    return Path(text)


def _load_source_bundle(root: Path | None, brief: Mapping[str, Any]) -> Mapping[str, Any]:
    if root:
        source_bundle = _load_json(root / "source_bundle.json")
        if source_bundle:
            return source_bundle
    embedded = brief.get("source_bundle") if isinstance(brief, Mapping) else None
    return embedded if isinstance(embedded, Mapping) else {}


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, Mapping) else {}


def _extract_source_claims(source_bundle: Mapping[str, Any], *, limit: int) -> list[dict[str, str]]:
    claims: list[dict[str, str]] = []
    for source in source_bundle.get("sources") or []:
        if not isinstance(source, Mapping):
            continue
        metadata = {
            "source_title": _first_text(source.get("title")),
            "source_url": _first_text(source.get("normalized_url"), source.get("url")),
        }
        for claim in source.get("claims") or []:
            text = _first_text(claim)
            if not text:
                continue
            claims.append({"claim": text, **metadata})
            if len(claims) >= limit:
                return claims
    return claims


def _extract_h1(markdown: str) -> str:
    for line in str(markdown or "").splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def _first_non_heading_paragraph(markdown: str) -> str:
    for block in re.split(r"\n\s*\n", str(markdown or "")):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or all(line.startswith("#") for line in lines):
            continue
        non_heading = [line for line in lines if not line.startswith("#")]
        if non_heading:
            return " ".join(non_heading).strip()
    return ""


def _shorten(text: str, max_chars: int) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def _first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""
