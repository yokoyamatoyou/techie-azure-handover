"""Speaker entity helpers for Route V self-perspective contracts."""
from __future__ import annotations

import re
from typing import Any


GENERIC_COMPANY_SPEAKERS = {"会社側の担当者", "担当者", "会社", "私たち"}


def infer_speaker_entity(company_speaker: str, source_documents: list[dict[str, Any]]) -> str:
    speaker = str(company_speaker or "").strip()
    if speaker and speaker not in GENERIC_COMPANY_SPEAKERS:
        return speaker
    for item in source_documents:
        for value in (item.get("title"), item.get("content")):
            name = extract_company_name(str(value or ""))
            if name:
                return name
    return "私たち"


def extract_company_name(text: str) -> str:
    patterns = (
        r"(?:株式会社|有限会社|合同会社)[^\s\|｜「」]{1,40}",
        r"[^\s\|｜「」]{1,40}(?:株式会社|有限会社|合同会社)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip(" 　。、「」|｜")
    return ""
