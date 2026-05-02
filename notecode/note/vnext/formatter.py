"""Output formatter for vNext."""
from __future__ import annotations

import re
from typing import Dict, List

from .types import RenderedSection, VNextThinContract

_ARTICLE_LABELS = {
    "announcement": "お知らせ",
    "branding": "ブランド記事",
    "daily_story": "日常記事",
    "explanatory_article": "解説記事",
    "case_study": "事例記事",
    "comparative_review": "比較レビュー",
    "industry_analysis": "業界分析",
}


def _compact_text(text: str, *, limit: int = 42) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip(" 　、。")
    if len(value) <= limit:
        return value
    return value[:limit].rstrip(" 　、。")


def _build_title(contract: VNextThinContract) -> str:
    seed = _compact_text(contract.topic_statement or contract.prompt_raw, limit=30)
    label = _ARTICLE_LABELS.get(contract.article_type, "記事")
    if not seed:
        return label
    return f"{seed}を整理する{label}"


def _build_lead(contract: VNextThinContract, sections: List[RenderedSection]) -> str:
    if not sections:
        return ""
    opening = sections[0].body.split("\n", 1)[0].strip()
    if contract.article_type == "announcement":
        return f"{opening} 読み手が次の確認に進みやすい順番で整理します。".strip()
    return f"{opening} この記事では、{contract.audience_profile}が迷いやすいポイントを順にほどきます。".strip()


def _build_body(sections: List[RenderedSection]) -> str:
    chunks: List[str] = []
    for section in sections:
        body = str(section.body or "").strip()
        if not body:
            continue
        chunks.append(f"## {section.heading}\n{body}")
    return "\n\n".join(chunks).strip()


def _build_references(contract: VNextThinContract) -> str:
    references: List[str] = []
    for document in contract.canonical_documents[:4]:
        title = str(document.metadata.get("title") or "").strip()
        locator = str(document.metadata.get("locator") or "").strip()
        if title and locator:
            references.append(f"- {title}: {locator}")
        elif title:
            references.append(f"- {title}")
        elif locator:
            references.append(f"- {locator}")
    return "\n".join(references).strip()


def format_vnext_output(contract: VNextThinContract, sections: List[RenderedSection]) -> Dict[str, str]:
    title = _build_title(contract)
    lead = _build_lead(contract, sections)
    body = _build_body(sections)
    references = _build_references(contract)
    chunks = [item for item in (title, lead, body, references) if item]
    return {
        "title": title,
        "lead": lead,
        "body": body,
        "references": references,
        "hashtags": "",
        "full_text": "\n\n".join(chunks).strip(),
    }
