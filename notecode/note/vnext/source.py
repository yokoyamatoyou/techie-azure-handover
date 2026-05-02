"""Canonical source normalization for vNext."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping

from .types import CanonicalDocument, FactCard

_TOKEN_RE = re.compile(r"[A-Za-z0-9一-龥ぁ-んァ-ヶー]{2,32}")
_DATE_RE = re.compile(r"\d{4}年(?:\d{1,2}月(?:\d{1,2}日)?)?")


def _normalize_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"[\r\t]+", " ", text)
    text = re.sub(r"[ \u3000]+", " ", text)
    return text.strip()


def _split_blocks(text: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for index, raw_block in enumerate(re.split(r"\n\s*\n", str(text or ""))):
        block_text = _normalize_text(raw_block)
        if not block_text:
            continue
        blocks.append(
            {
                "block_id": f"block_{index + 1:03d}",
                "text": block_text,
                "char_count": len(block_text),
            }
        )
    if not blocks and str(text or "").strip():
        single = _normalize_text(text)
        blocks.append({"block_id": "block_001", "text": single, "char_count": len(single)})
    return blocks


def _extract_entity(text: str) -> str:
    for token in _TOKEN_RE.findall(str(text or "")):
        if len(token) >= 4:
            return token
    return ""


def _infer_fact_type(text: str) -> str:
    candidate = str(text or "")
    if _DATE_RE.search(candidate):
        return "dated_fact"
    if re.search(r"(変更|開始|停止|更新|提供|リリース|告知)", candidate):
        return "announcement_fact"
    if re.search(r"(強み|特徴|価値|課題|背景)", candidate):
        return "value_fact"
    if re.search(r"(結果|改善|導入|運用|事例|再発防止)", candidate):
        return "case_fact"
    return "general"


def _critical_span(text: str, locator: str) -> Dict[str, Any]:
    return {
        "text": str(text or "")[:160],
        "locator": str(locator or ""),
        "kind": "fact_anchor",
    }


def _fact_card_from_grounding_item(item: Mapping[str, Any], index: int) -> FactCard | None:
    fact_text = _normalize_text(item.get("fact_text") or "")
    if not fact_text:
        return None
    date_match = _DATE_RE.search(fact_text)
    return FactCard(
        fact_id=f"fact_{index + 1:03d}",
        fact_text=fact_text,
        fact_type=_infer_fact_type(fact_text),
        entity=_extract_entity(fact_text),
        date_or_period=date_match.group(0) if date_match else "",
        source_title=_normalize_text(item.get("source_title") or ""),
        locator=_normalize_text(item.get("locator") or ""),
        confidence=0.8,
        critical=bool(item.get("bucket") in {"overview", "strength", "history"}),
    )


def _fact_cards_from_documents(source_documents: Iterable[Mapping[str, Any]], start_index: int = 0) -> List[FactCard]:
    fact_cards: List[FactCard] = []
    next_index = start_index
    for document in source_documents:
        content = _normalize_text(document.get("content") or "")
        title = _normalize_text(document.get("title") or "")
        locator = _normalize_text(document.get("locator") or "")
        sentences = [
            _normalize_text(item)
            for item in re.split(r"(?<=[。！？])", content)
            if _normalize_text(item)
        ]
        for sentence in sentences[:3]:
            date_match = _DATE_RE.search(sentence)
            fact_cards.append(
                FactCard(
                    fact_id=f"fact_{next_index + 1:03d}",
                    fact_text=sentence,
                    fact_type=_infer_fact_type(sentence),
                    entity=_extract_entity(sentence) or title,
                    date_or_period=date_match.group(0) if date_match else "",
                    source_title=title,
                    locator=locator,
                    confidence=0.65,
                    critical=bool(date_match),
                )
            )
            next_index += 1
    return fact_cards


def build_fact_cards_from_current_contract(contract: Mapping[str, Any]) -> List[FactCard]:
    grounding_items = contract.get("source_grounding_items") or []
    fact_cards: List[FactCard] = []
    seen: set[str] = set()
    if isinstance(grounding_items, list):
        for index, item in enumerate(grounding_items):
            if not isinstance(item, Mapping):
                continue
            fact_card = _fact_card_from_grounding_item(item, index)
            if fact_card is None:
                continue
            dedupe_key = "".join(fact_card.fact_text.split())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            fact_cards.append(fact_card)
    source_documents = contract.get("source_documents") or []
    if isinstance(source_documents, list) and len(fact_cards) < 3:
        normalized_documents = [item for item in source_documents if isinstance(item, Mapping)]
        for fact_card in _fact_cards_from_documents(normalized_documents, start_index=len(fact_cards)):
            dedupe_key = "".join(fact_card.fact_text.split())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            fact_cards.append(fact_card)
    return fact_cards[:12]


def build_canonical_documents_from_current_contract(
    contract: Mapping[str, Any],
    fact_cards: List[FactCard],
) -> List[CanonicalDocument]:
    source_documents = contract.get("source_documents") or []
    documents: List[CanonicalDocument] = []
    if not isinstance(source_documents, list):
        return documents
    for raw_document in source_documents:
        if not isinstance(raw_document, Mapping):
            continue
        raw_text = _normalize_text(raw_document.get("content") or "")
        title = _normalize_text(raw_document.get("title") or "")
        locator = _normalize_text(raw_document.get("locator") or "")
        if not raw_text and not title and not locator:
            continue
        source_title_cards = [card for card in fact_cards if card.source_title == title or card.locator == locator]
        documents.append(
            CanonicalDocument(
                raw_text=raw_text,
                norm_text=_normalize_text(raw_text),
                blocks=_split_blocks(raw_text),
                metadata={
                    "title": title,
                    "locator": locator,
                    "notices": list(raw_document.get("notices") or [])[:4],
                },
                critical_spans=[_critical_span(card.fact_text, card.locator or locator) for card in source_title_cards[:3]],
                source_type=_normalize_text(raw_document.get("source_type") or "url") or "url",
                ocr_mode="text",
                fact_cards=source_title_cards,
            )
        )
    return documents


def build_source_context_summary(
    fact_cards: List[FactCard],
    canonical_documents: List[CanonicalDocument],
) -> Dict[str, Any]:
    source_types: Dict[str, int] = {}
    total_chars = 0
    for document in canonical_documents:
        source_type = str(document.source_type or "unknown")
        source_types[source_type] = int(source_types.get(source_type, 0)) + 1
        total_chars += len(document.norm_text)
    return {
        "document_count": len(canonical_documents),
        "fact_card_count": len(fact_cards),
        "source_types": source_types,
        "total_source_chars": total_chars,
        "document_titles": [str(document.metadata.get("title") or "") for document in canonical_documents[:4]],
    }
