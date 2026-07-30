"""Thin adapter for the 0506 staged blog algorithm UI route."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping

from note.route_0506_article_genre_contract import (
    COMPANY_INTRO_THICK_SECTION_COUNT,
    COMPANY_INTRO_THICK_TARGET_LENGTH_CHARS,
    apply_route_0506_company_intro_section_planning_contract as _route_0506_apply_company_intro_section_planning_contract,
    build_route_0506_article_genre_contract,
    enrich_route_0506_article_brief_builder_payload,
    normalize_route_0506_company_intro_article_brief_metadata,
    resolve_route_0506_genre,
    resolve_route_0506_narrator,
)
from note.route_0506_security_gate import (
    evaluate_route_0506_security_gate,
    is_local_file_locator,
    normalize_uploaded_file_locator,
    is_unsafe_url_label,
)
from note.route_0506_structured_blog_result_adapter import (
    build_route_0506_blocked_result,
    build_route_0506_visible_result,
    write_route_0506_result_artifacts,
)
from note.route_0506_stage_output_guard import (
    route_0506_is_visible_output_contract_violation_type,
    route_0506_stage_output_guard_violations,
    route_0506_visible_output_contract_violations,
    wrap_route_0506_stage_output_guard,
)
from note.route_0506_usage_ledger import ROUTE_0506_ID, build_not_sent_usage_row


ROUTE_0506_ROOT_ENV = "NOTECODE_0506_STRUCTURED_BLOG_ROOT"
LOCAL_0506_REFERENCE_ROOT = Path(__file__).resolve().parents[1] / "0506"


def resolve_default_route_0506_root() -> Path:
    override = os.getenv(ROUTE_0506_ROOT_ENV)
    return Path(override) if override else LOCAL_0506_REFERENCE_ROOT


DEFAULT_0506_ROOT = resolve_default_route_0506_root()
ROUTE_0506_CLIENT_MODE_ENV = "NOTECODE_ROUTE_0506_CLIENT_MODE"
LOCAL_DETERMINISTIC_VALIDATION = "local_deterministic_validation"
OPENAI_GENERATION_CANDIDATE = "openai_generation_candidate"
ROUTE_0506_VISIBLE_OUTPUT_CONTRACT_FAILED = "ROUTE_0506_VISIBLE_OUTPUT_CONTRACT_FAILED"
ROUTE_0506_STRUCTURAL_EDITOR_ARTICLE_RETURN_CONTRACT = (
    "Return contract: return only the complete reader-facing article body in Markdown. "
    "Do not return review notes, analysis, checklists, comments, explanations, change summaries, "
    "wrapper headings, or code fences. If no structural edit is needed, return the original "
    "article body unchanged."
)
ROUTE_0506_OPENING_EDITOR_ARTICLE_RETURN_CONTRACT = (
    "Opening editor contract: return only the complete reader-facing article body in Markdown. "
    "Do not return a short preface, summary, collapse, or message about the edited article. "
    "Do not begin with reader-facing wrapper lines such as 'below is the article' or "
    "'this is the revised article'. If no opening edit is needed, return the original "
    "article body unchanged."
)
ROUTE_0506_DRAFT_WRITER_BRIEF_REALIZATION_CONTRACT = (
    "Draft writer contract: article_brief is the design contract for this draft. "
    "Treat article_brief.target_length_chars as a soft planning reference, not a hard user length request; "
    "article_brief.section_count and article_brief.sections as the section plan, "
    "and each section's assigned_claim_ids / claim_allocation as required claim coverage. "
    "Use only confirmed claims from knowledge_pack; if source evidence cannot support the full target length, "
    "stay grounded at the natural category/source-backed length and do not pad or repeat unsupported facts."
)
ROUTE_0506_GLOBAL_CONSISTENCY_PRESERVE_DEPTH_CONTRACT = (
    "Global consistency editor contract: remove only exact or near-duplicate motifs. "
    "Preserve source-backed claims, section-level reader decision depth, company context, and inquiry-path detail. "
    "Do not compress claim-supporting paragraphs merely to shorten the article. "
    "When article_brief.target_length_chars is a soft natural reference, preserve the natural source-backed length "
    "unless the text is genuinely repetitive."
)
MAX_SOURCE_DOCUMENTS = 5
MAX_SOURCE_CHARS = 24000
MAX_TYPED_SOURCE_FIELD_CHARS = 900
ROUTE_0506_SENTENCE_LONG_LIMIT_FALLBACK = 90
COMPANY_INTRO_SCRIPT_FIELDS = (
    ("current_business", "現在事業"),
    ("entry_point", "顧客接点"),
    ("support_boundary", "支援範囲"),
    ("process", "進め方"),
    ("reader_decision", "相談前判断"),
)
COMPANY_INTRO_SLOT_FIELDS = (
    ("current_business", "現在事業"),
    ("customer_situation_or_entry_point", "顧客接点"),
    ("support_scope_boundary", "支援範囲"),
    ("operating_process_steps", "運用手順"),
    ("pre_contact_decision", "相談前判断"),
    ("proof_signal", "根拠シグナル"),
    ("source_limit", "source limit"),
)
COMPANY_INTRO_REQUIRED_BUCKETS = (
    "current_business",
    "customer_situation_or_entry_point",
    "support_scope_boundary",
)
COMPANY_INTRO_OPTIONAL_BUCKETS = (
    "operating_process_steps",
    "pre_contact_decision",
    "proof_signal",
)
COMPANY_INTRO_BUCKET_KEYWORDS = {
    "current_business": (
        "リージャパン",
        "株式会社リージャパン",
        "東大阪市",
        "売買に特化",
        "手掛けています",
        "不動産会社",
    ),
    "customer_situation_or_entry_point": (
        "はじめて",
        "不安",
        "お困り",
        "電話",
        "訪問",
        "ダイレクトメール",
        "他社で断られた",
        "相談",
    ),
    "support_scope_boundary": (
        "一括査定",
        "窓口",
        "代行",
        "査定",
        "売却",
        "買取",
        "リフォーム",
        "セカンドオピニオン",
    ),
    "operating_process_steps": (
        "査定",
        "相談",
        "依頼",
        "契約",
        "現金化",
        "窓口",
    ),
    "pre_contact_decision": (
        "疑問",
        "不安",
        "このタイミング",
        "相談",
        "検討",
        "お気軽に",
        "連絡",
    ),
    "proof_signal": (
        "安心",
        "満足",
        "プロフェッショナル",
        "確かな知識",
        "販売戦略",
        "ご納得",
        "セカンドオピニオン",
        "大手不動産会社",
        "過去の売買事例",
        "将来性",
        "専門家",
    ),
}
COMPANY_INTRO_HARD_GUIDE_TERMS = (
    "REINS",
    "レインズ",
    "インターネット掲載",
    "チラシ",
    "内覧",
    "書類",
    "住み替え",
    "売り先行",
    "買い先行",
    "媒介契約",
    "買取保証",
    "離婚",
    "財産分与",
    "土地",
    "境界線",
    "買取価格",
    "3～6ヶ月",
    "3〜6ヶ月",
    "住宅ローン",
    "転居先",
    "高く売りたい",
    "荷物を家に置いたまま",
    "1平米",
    "1平方メートル",
    "資金計画",
    "二重ローン",
    "新居",
    "仮住まい",
    "任意売却",
    "競売",
)
COMPANY_INTRO_SOFT_GUIDE_TERMS = (
    "2種類",
    "売却方法",
    "仲介売却",
    "不動産業者買取",
    "現金化",
)
COMPANY_INTRO_SOURCE_LIMIT_TERMS = (
    "もっとも一般的",
    "最適です",
    "おすすめです",
    "おすすめします",
    "リスクなし",
    "多々ございます",
    "必ず",
)
COMPANY_INTRO_NOISE_TERMS = (
    "お問い合わせ",
    "Copyright",
    "トップページ",
    "メニュー",
    "プライバシーポリシー",
    "サイトマップ",
    "詳しくはこちら",
)
COMPANY_INTRO_SELECTED_UNITS_PER_SOURCE = 8
COMPANY_INTRO_SELECTED_CHARS_PER_SOURCE = 1100
OPENAI_STRUCTURED_OUTPUT_UNSUPPORTED_KEYS = {
    "$schema",
    "$id",
    "title",
    "uniqueItems",
    "minLength",
    "maxLength",
}
OPENAI_STRUCTURED_OUTPUT_SUPPORTED_FORMATS = {
    "date-time",
    "time",
    "date",
    "duration",
    "email",
    "hostname",
    "ipv4",
    "ipv6",
    "uuid",
}
ROUTE_0506_OPENAI_UNIQUE_ARRAY_KEYS = {
    "assigned_claim_ids",
    "claim_ids",
    "config_refs",
    "deduped_themes",
    "discourse_rules",
    "involved_fact_ids",
    "main_topics",
    "persona_refs",
    "reasons",
    "risk_flags",
    "source_card_ids",
    "style_rules",
    "supporting_fact_ids",
}
WINDOWS_LEGACY_MAX_PATH = 260
WINDOWS_LONG_PATH_PREFIX = "\\\\?\\"


class Route0506AdapterError(RuntimeError):
    """Raised when the 0506 UI route adapter must fail closed."""


@dataclass(frozen=True)
class Route0506SourceRecord:
    title: str
    content: str
    locator: str
    source_type: str
    source_span_id: str


def resolve_route_0506_client_mode(mode: str | None = None) -> str:
    raw = str(mode or os.getenv(ROUTE_0506_CLIENT_MODE_ENV) or LOCAL_DETERMINISTIC_VALIDATION).strip().lower()
    aliases = {
        "": LOCAL_DETERMINISTIC_VALIDATION,
        "local": LOCAL_DETERMINISTIC_VALIDATION,
        "local_deterministic": LOCAL_DETERMINISTIC_VALIDATION,
        "local_deterministic_validation": LOCAL_DETERMINISTIC_VALIDATION,
        "openai": OPENAI_GENERATION_CANDIDATE,
        "gpt": OPENAI_GENERATION_CANDIDATE,
        "gpt-5.4-mini": OPENAI_GENERATION_CANDIDATE,
        "openai_generation_candidate": OPENAI_GENERATION_CANDIDATE,
    }
    resolved = aliases.get(raw)
    if not resolved:
        raise Route0506AdapterError(f"unsupported_route_0506_client_mode:{raw}")
    return resolved


def extract_route_0506_source_records(
    input_contract: Mapping[str, Any],
    *,
    max_sources: int = MAX_SOURCE_DOCUMENTS,
    max_chars_per_source: int = MAX_SOURCE_CHARS,
) -> list[Route0506SourceRecord]:
    saved_company_intro_records = _extract_company_introduction_saved_source_records(
        input_contract,
        max_sources=max_sources,
        max_chars_per_source=max_chars_per_source,
    )
    if saved_company_intro_records:
        return saved_company_intro_records[:max_sources]

    typed_records = _extract_company_introduction_source_records(
        input_contract,
        max_chars_per_source=max_chars_per_source,
    )
    if typed_records:
        return typed_records[:max_sources]

    docs = input_contract.get("source_documents")
    if not isinstance(docs, list):
        raise Route0506AdapterError("source_documents_required")

    records: list[Route0506SourceRecord] = []
    for index, item in enumerate(docs[:max_sources], start=1):
        if not isinstance(item, Mapping):
            continue
        locator = _validated_source_locator(item, index)
        content = str(item.get("content") or item.get("text") or item.get("extracted_text") or "").strip()
        if not content:
            continue
        source_type = str(item.get("source_type") or "").strip().lower()
        if source_type not in {"url", "pdf", "word", "manual"}:
            source_type = "url" if locator.startswith(("http://", "https://")) else "manual"
        title = str(item.get("title") or item.get("source_label") or locator or f"source {index}").strip()
        records.append(
            Route0506SourceRecord(
                title=title or f"source {index}",
                content=content[:max_chars_per_source],
                locator=locator,
                source_type=source_type,
                source_span_id=str(item.get("source_span_id") or item.get("span_id") or f"notecode_{index:03d}"),
            )
        )
    if not records:
        raise Route0506AdapterError("source_documents_with_content_required")
    return records


def _extract_company_introduction_source_records(
    input_contract: Mapping[str, Any],
    *,
    max_chars_per_source: int,
) -> list[Route0506SourceRecord]:
    if not _is_company_introduction_contract(input_contract):
        return []

    script_packet = input_contract.get("_company_introduction_script_packet")
    source_contract = input_contract.get("_company_introduction_source_contract")
    grounding_items = input_contract.get("source_grounding_items")

    if not any(
        [
            isinstance(script_packet, Mapping),
            isinstance(source_contract, Mapping),
            isinstance(grounding_items, list),
        ]
    ):
        return []

    records: list[Route0506SourceRecord] = []
    _append_typed_source_record(
        records,
        title="company introduction script packet",
        locator="notecode_typed_contract:company_introduction_script_packet",
        source_span_id="notecode_company_intro_script_packet",
        lines=_field_lines(script_packet, COMPANY_INTRO_SCRIPT_FIELDS),
        max_chars_per_source=max_chars_per_source,
    )

    slots = source_contract.get("slots") if isinstance(source_contract, Mapping) else None
    _append_typed_source_record(
        records,
        title="company introduction source contract slots",
        locator="notecode_typed_contract:company_introduction_source_contract",
        source_span_id="notecode_company_intro_source_contract",
        lines=_field_lines(slots, COMPANY_INTRO_SLOT_FIELDS),
        max_chars_per_source=max_chars_per_source,
    )

    _append_typed_source_record(
        records,
        title="company introduction grounding items",
        locator="notecode_typed_contract:source_grounding_items",
        source_span_id="notecode_company_intro_grounding_items",
        lines=_source_grounding_item_lines(grounding_items),
        max_chars_per_source=max_chars_per_source,
    )

    return records


def _is_company_introduction_contract(input_contract: Mapping[str, Any]) -> bool:
    article_type = str(input_contract.get("article_type") or "").strip().lower()
    semantic_key = str(input_contract.get("semantic_article_key") or "").strip().lower()
    return semantic_key == "company_introduction" or (
        article_type == "branding" and semantic_key in {"", "company_introduction"}
    )


def _extract_company_introduction_saved_source_records(
    input_contract: Mapping[str, Any],
    *,
    max_sources: int,
    max_chars_per_source: int,
) -> list[Route0506SourceRecord]:
    if not _is_company_introduction_contract(input_contract):
        return []

    docs = input_contract.get("source_documents")
    if not isinstance(docs, list):
        return []

    records: list[Route0506SourceRecord] = []
    per_source_limit = min(max_chars_per_source, COMPANY_INTRO_SELECTED_CHARS_PER_SOURCE)
    for index, item in enumerate(docs[:max_sources], start=1):
        if not isinstance(item, Mapping):
            continue
        locator = _validated_source_locator(item, index)
        source_text = str(item.get("content") or item.get("text") or item.get("extracted_text") or "")
        selected_text = _select_company_intro_saved_text(item, per_source_limit)
        if not selected_text:
            continue
        source_type = str(item.get("source_type") or "").strip().lower()
        if source_type not in {"url", "pdf", "word", "manual"}:
            source_type = "url" if locator.startswith(("http://", "https://")) else "manual"
        title = str(item.get("title") or item.get("source_label") or locator or f"source {index}").strip()
        if selected_text.strip() == source_text.strip():
            continue
        records.append(
            Route0506SourceRecord(
                title=title or f"source {index}",
                content=selected_text,
                locator=locator,
                source_type=source_type,
                source_span_id=f"route0506_company_intro_saved_{index:03d}",
            )
        )
    return records


def _select_company_intro_saved_text(source_doc: Mapping[str, Any], max_chars: int) -> str:
    title = str(source_doc.get("title") or source_doc.get("source_label") or "").strip()
    source_text = str(source_doc.get("content") or source_doc.get("text") or source_doc.get("extracted_text") or "")
    fact_card_text = _select_company_intro_saved_fact_card_text(source_doc, source_text, max_chars)
    if fact_card_text:
        return fact_card_text

    scored_units: list[dict[str, Any]] = []
    for offset, unit in _company_intro_sentence_units(source_text):
        score, buckets = _score_company_intro_unit(unit, title)
        if score <= 0:
            continue
        if _company_intro_source_limit_flag(unit):
            continue
        if _company_intro_hard_guide_flag(unit) and not _company_intro_has_company_service_anchor(unit, buckets):
            continue
        scored_units.append({"offset": offset, "score": score, "text": unit, "buckets": buckets})

    selected = sorted(scored_units, key=lambda item: (-int(item["score"]), int(item["offset"])))
    selected = selected[:COMPANY_INTRO_SELECTED_UNITS_PER_SOURCE]
    selected = sorted(selected, key=lambda item: int(item["offset"]))
    joined = "\n".join(str(item["text"]) for item in selected).strip()
    if len(joined) > max_chars:
        joined = _trim_to_complete_japanese_sentence(joined[:max_chars].rstrip())
    return joined


def _select_company_intro_saved_fact_card_text(
    source_doc: Mapping[str, Any],
    source_text: str,
    max_chars: int,
) -> str:
    if not _is_company_intro_saved_fact_card_doc(source_doc, source_text):
        return ""

    selected_lines: list[str] = []
    for line in _company_intro_saved_fact_card_lines(source_text):
        if any(term in line for term in COMPANY_INTRO_NOISE_TERMS):
            continue
        if _company_intro_source_limit_flag(line):
            continue
        selected_lines.append(line)
        if len(selected_lines) >= COMPANY_INTRO_SELECTED_UNITS_PER_SOURCE:
            break

    joined = "\n".join(selected_lines).strip()
    if len(joined) > max_chars:
        joined = _trim_to_complete_japanese_sentence(joined[:max_chars].rstrip())
    return joined


def _is_company_intro_saved_fact_card_doc(source_doc: Mapping[str, Any], source_text: str) -> bool:
    source_kind = str(source_doc.get("source_kind") or "").strip()
    source_origin = str(source_doc.get("source_origin") or "").strip()
    if source_kind == "local_0506_saved_source_card_facts" or source_origin.endswith("source_cards.json"):
        return True

    lines = [line.strip() for line in str(source_text or "").splitlines() if line.strip()]
    return any(line == "source_kind: local_0506_saved_source_card_facts" for line in lines) or any(
        line.startswith("source_origin:") and line.endswith("source_cards.json") for line in lines
    )


def _company_intro_saved_fact_card_lines(source_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in str(source_text or "").splitlines():
        line = " ".join(raw_line.strip().split())
        if not line:
            continue
        if line.startswith(("locator:", "source_origin:", "source_kind:", "url_refetched:")):
            continue
        if line.startswith("#"):
            lines.append(line)
            continue
        if line.startswith("- "):
            lines.append(line)
    return lines


def _company_intro_sentence_units(text: str) -> list[tuple[int, str]]:
    units: list[tuple[int, str]] = []
    for match in re.finditer(r"[^。！？\n]{12,260}[。！？]?", str(text or "")):
        unit = " ".join(match.group(0).split())
        if len(unit) < 20:
            continue
        if any(term in unit for term in COMPANY_INTRO_NOISE_TERMS):
            continue
        units.append((match.start(), unit))
    return units


def _score_company_intro_unit(unit: str, title: str) -> tuple[int, list[str]]:
    buckets = _company_intro_buckets(unit)
    if not buckets:
        return 0, []

    score = len(buckets) * 4
    if any(term in unit for term in ("リージャパン", "株式会社リージャパン", "当社", "弊社")):
        score += 4
    if "会社案内" in title or "代表挨拶" in title:
        score += 2
    if "ワンストップ" in title or "一括査定" in title:
        score += 1
    if _company_intro_hard_guide_flag(unit):
        score -= 8
    if _company_intro_source_limit_flag(unit):
        score -= 10
    soft_guide_hits = sum(1 for term in COMPANY_INTRO_SOFT_GUIDE_TERMS if term in unit)
    if soft_guide_hits and not _company_intro_has_company_service_anchor(unit, buckets):
        score -= soft_guide_hits * 3
    return score, buckets


def _company_intro_buckets(text: str) -> list[str]:
    return [
        bucket
        for bucket, keywords in COMPANY_INTRO_BUCKET_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]


def _company_intro_hard_guide_flag(text: str) -> bool:
    return any(term in text for term in COMPANY_INTRO_HARD_GUIDE_TERMS)


def _company_intro_soft_guide_flag(text: str) -> bool:
    return any(term in text for term in COMPANY_INTRO_SOFT_GUIDE_TERMS)


def _company_intro_source_limit_flag(text: str) -> bool:
    return any(term in text for term in COMPANY_INTRO_SOURCE_LIMIT_TERMS)


def _company_intro_sell_method_guide_flag(text: str, buckets: list[str] | None = None) -> bool:
    bucket_values = buckets if buckets is not None else _company_intro_buckets(text)
    if _company_intro_hard_guide_flag(text):
        return True
    return _company_intro_soft_guide_flag(text) and not _company_intro_has_company_service_anchor(text, bucket_values)


def _company_intro_has_company_service_anchor(text: str, buckets: list[str]) -> bool:
    if any(term in text for term in ("リージャパン", "株式会社リージャパン", "当社", "弊社")):
        return True
    return any(bucket in buckets for bucket in COMPANY_INTRO_REQUIRED_BUCKETS)


def build_route_0506_company_intro_source_surface_preflight(input_contract: Mapping[str, Any]) -> dict[str, Any]:
    records = extract_route_0506_source_records(input_contract)
    source_docs = input_contract.get("source_documents") if isinstance(input_contract, Mapping) else None
    source_doc_by_locator: dict[str, str] = {}
    original_saved_total_chars = 0
    if isinstance(source_docs, list):
        for index, item in enumerate(source_docs[:MAX_SOURCE_DOCUMENTS], start=1):
            if not isinstance(item, Mapping):
                continue
            locator = _validated_source_locator(item, index)
            text = str(item.get("content") or item.get("text") or item.get("extracted_text") or "")
            source_doc_by_locator[locator] = text
            original_saved_total_chars += len(text)

    bucket_chars = {bucket: 0 for bucket in (*COMPANY_INTRO_REQUIRED_BUCKETS, *COMPANY_INTRO_OPTIONAL_BUCKETS)}
    selected_total_chars = 0
    company_service_chars = 0
    guide_chars = 0
    source_limit_selected_chars = 0
    substring_backed = True
    raw_full_source_documents_passed = False
    selected_records: list[dict[str, Any]] = []
    for record in records:
        source_text = source_doc_by_locator.get(record.locator, "")
        record_lines: list[dict[str, Any]] = []
        if source_text and record.content.strip() == source_text.strip():
            raw_full_source_documents_passed = True
        for line in [item.strip() for item in record.content.splitlines() if item.strip()]:
            buckets = _company_intro_buckets(line)
            chars = len(line)
            selected_total_chars += chars
            if buckets:
                company_service_chars += chars
            if _company_intro_sell_method_guide_flag(line, buckets):
                guide_chars += chars
            if _company_intro_source_limit_flag(line):
                source_limit_selected_chars += chars
            for bucket in buckets:
                bucket_chars[bucket] += chars
            line_substring_backed = bool(source_text) and line in source_text
            substring_backed = substring_backed and line_substring_backed
            record_lines.append(
                {
                    "text": line,
                    "chars": chars,
                    "article_type_buckets": buckets,
                    "sell_method_guide_flag": _company_intro_sell_method_guide_flag(line, buckets),
                    "source_limit_flag": _company_intro_source_limit_flag(line),
                    "substring_backed": line_substring_backed,
                }
            )
        selected_records.append(
            {
                "title": record.title,
                "locator": record.locator,
                "source_type": record.source_type,
                "source_span_id": record.source_span_id,
                "selected_chars": len(record.content),
                "lines": record_lines,
            }
        )

    selected_record_total_chars = sum(len(record.content) for record in records)
    required_present = [bucket for bucket in COMPANY_INTRO_REQUIRED_BUCKETS if bucket_chars.get(bucket, 0) > 0]
    source_thickness = (
        "thick"
        if selected_record_total_chars >= 1500 and len(required_present) == len(COMPANY_INTRO_REQUIRED_BUCKETS)
        else "medium"
    )
    target_length = COMPANY_INTRO_THICK_TARGET_LENGTH_CHARS if source_thickness == "thick" else 1200
    section_count = COMPANY_INTRO_THICK_SECTION_COUNT if source_thickness == "thick" else 2
    return {
        "selected_source_count": len(records),
        "selected_total_chars": selected_record_total_chars,
        "selected_total_chars_without_newlines": selected_total_chars,
        "original_saved_total_chars": original_saved_total_chars,
        "company_service_bucket_coverage": {
            "chars": company_service_chars,
            "ratio": round(company_service_chars / selected_total_chars, 4) if selected_total_chars else 0.0,
            "bucket_chars": bucket_chars,
            "required_buckets_present": required_present,
        },
        "sell_method_guide_span_ratio": round(guide_chars / selected_total_chars, 4) if selected_total_chars else 0.0,
        "source_limit_material_excluded": source_limit_selected_chars == 0,
        "source_limit_selected_chars": source_limit_selected_chars,
        "url_identity_preserved": all(record.source_type == "url" and record.locator.startswith(("http://", "https://")) for record in records),
        "substring_backed_selected_text": substring_backed,
        "target_length_proposal": target_length,
        "target_length_semantics": "soft_natural_reference",
        "padding_risk_policy": "do_not_pad_when_source_backed_facts_do_not_support_length",
        "section_allocation_proposal": {
            "section_count": section_count,
            "sections": [
                {
                    "bucket_focus": ["current_business", "proof_signal"],
                    "main_subject": "リージャパンの会社姿勢と東大阪市での不動産売却支援",
                },
                {
                    "bucket_focus": ["customer_situation_or_entry_point", "support_scope_boundary"],
                    "main_subject": "一括査定の負担や売却相談を支えるサービス範囲",
                },
                {
                    "bucket_focus": ["pre_contact_decision", "operating_process_steps"],
                    "main_subject": "相談前に整理したいことと問い合わせ導線",
                },
            ][:section_count],
        },
        "source_thickness_proposal": source_thickness,
        "expected_title_anchors": ["リージャパン", "東大阪市", "不動産売却支援"],
        "expected_lead_anchors": ["私たち", "リージャパン", "東大阪市", "相談"],
        "expected_final_paragraph_anchors": ["他社で断られた物件", "一括査定", "相談"],
        "url_refetch": False,
        "route_a_regenerated": False,
        "route_a_fallback_used": False,
        "raw_full_source_documents_passed": raw_full_source_documents_passed,
        "selected_records": selected_records,
    }


def _field_lines(payload: Any, fields: tuple[tuple[str, str], ...]) -> list[str]:
    if not isinstance(payload, Mapping):
        return []
    lines: list[str] = []
    for key, _label in fields:
        text = _typed_source_text(payload.get(key))
        if text:
            lines.append(text)
    return lines


def _source_grounding_item_lines(payload: Any) -> list[str]:
    if not isinstance(payload, list):
        return []
    lines: list[str] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, Mapping):
            continue
        fact_text = _typed_source_text(item.get("fact_text"))
        if not fact_text:
            continue
        lines.append(fact_text)
    return lines


def _typed_source_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        text = " / ".join(_typed_source_text(item) for item in value)
    elif isinstance(value, Mapping):
        for preferred_key in ("summary", "fact_text", "quote", "text", "content"):
            preferred = _typed_source_text(value.get(preferred_key))
            if preferred:
                text = preferred
                break
        else:
            text = " / ".join(
                _typed_source_text(child)
                for key, child in value.items()
                if key not in {"status", "source_title", "locator", "url"} and _typed_source_text(child)
            )
    else:
        text = str(value)
    text = " ".join(text.split())
    if len(text) > MAX_TYPED_SOURCE_FIELD_CHARS:
        text = text[:MAX_TYPED_SOURCE_FIELD_CHARS].rstrip()
    return _trim_to_complete_japanese_sentence(text)


def _trim_to_complete_japanese_sentence(text: str) -> str:
    stripped = str(text or "").strip()
    last_end = max(stripped.rfind(marker) for marker in ("。", "！", "？"))
    if last_end >= 0:
        return stripped[: last_end + 1].strip()
    return stripped


def _append_typed_source_record(
    records: list[Route0506SourceRecord],
    *,
    title: str,
    locator: str,
    source_span_id: str,
    lines: list[str],
    max_chars_per_source: int,
) -> None:
    content = "\n".join(line for line in lines if line).strip()
    if not content:
        return
    records.append(
        Route0506SourceRecord(
            title=title,
            content=content[:max_chars_per_source],
            locator=locator,
            source_type="manual",
            source_span_id=source_span_id,
        )
    )


def route_0506_source_snapshot(records: list[Route0506SourceRecord]) -> dict[str, Any]:
    payload = [
        {
            "title": record.title,
            "content": record.content,
            "locator": record.locator,
            "source_type": record.source_type,
            "source_span_id": record.source_span_id,
        }
        for record in records
    ]
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "route_id": ROUTE_0506_ID,
        "canonical_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "source_count": len(records),
        "sources": payload,
    }


def inspect_route_0506_workspace(route_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(route_root) if route_root is not None else resolve_default_route_0506_root()
    required_files = [
        "AGENTS.md",
        "docs/CURRENT_ALGORITHM.md",
        "app/services/pipeline_runner.py",
        "app/services/source_acquisition.py",
        "app/services/pipeline_logging.py",
        "app/services/local_llm_client.py",
        "app/schemas/source_card.schema.json",
    ]
    missing = [relative for relative in required_files if not (root / relative).exists()]
    return {
        "route_id": ROUTE_0506_ID,
        "workspace": str(root),
        "exists": root.exists(),
        "missing_required_files": missing,
    }


def prepare_route_0506_adapter_plan(
    input_contract: Mapping[str, Any],
    *,
    artifact_root: Path | str,
    approved_root: Path | str | None = None,
    client_mode: str | None = None,
) -> dict[str, Any]:
    resolved_client_mode = resolve_route_0506_client_mode(client_mode)
    records = extract_route_0506_source_records(input_contract)
    snapshot = route_0506_source_snapshot(records)
    security_gate = evaluate_route_0506_security_gate(
        input_contract,
        artifact_root=artifact_root,
        **({"approved_root": approved_root} if approved_root is not None else {}),
    )
    usage_row = build_not_sent_usage_row(stage="adapter_plan", artifact_root=artifact_root)
    article_genre_contract = build_route_0506_article_genre_contract(input_contract)
    return {
        "route_id": ROUTE_0506_ID,
        "genre_id": article_genre_contract["genre_id"],
        "narrator": article_genre_contract["narrator"],
        "source_records": records,
        "source_snapshot": snapshot,
        "security_gate": security_gate,
        "usage_row": usage_row,
        "client_mode": resolved_client_mode,
        "external_llm_send": resolved_client_mode == OPENAI_GENERATION_CANDIDATE,
        "route_a_fallback_used": False,
        "url_refetch": False,
        "local_file_read_fallback": False,
    }


def run_route_0506_local_scaffold(
    input_contract: Mapping[str, Any],
    *,
    artifact_root: Path | str,
    route_root: Path | str | None = None,
    run_id: str = "route_0506_structured_blog_ui_v1",
    client_mode: str | None = None,
) -> dict[str, Any]:
    plan = prepare_route_0506_adapter_plan(input_contract, artifact_root=artifact_root, client_mode=client_mode)
    security_gate = dict(plan["security_gate"])
    if security_gate.get("decision") != "pass":
        result = build_route_0506_blocked_result(
            input_contract=input_contract,
            artifact_root=artifact_root,
            reason_code="ROUTE_0506_SECURITY_GATE_BLOCKED",
            blocked_reason=",".join(security_gate.get("blocked_reasons") or []),
            security_gate=security_gate,
        )
        write_route_0506_result_artifacts(
            artifact_root,
            result,
            input_contract=input_contract,
            source_snapshot=plan["source_snapshot"],
            security_gate=security_gate,
        )
        return result

    resolved_route_root = Path(route_root) if route_root is not None else resolve_default_route_0506_root()
    workspace_report = inspect_route_0506_workspace(resolved_route_root)
    if workspace_report["missing_required_files"]:
        result = build_route_0506_blocked_result(
            input_contract=input_contract,
            artifact_root=artifact_root,
            reason_code="ROUTE_0506_WORKSPACE_MISSING",
            blocked_reason="0506_workspace_missing_required_files",
            security_gate=security_gate,
        )
        write_route_0506_result_artifacts(
            artifact_root,
            result,
            input_contract=input_contract,
            source_snapshot=plan["source_snapshot"],
            security_gate=security_gate,
        )
        return result

    modules = _load_0506_modules(resolved_route_root)
    _install_route_0506_markdown_quality_boundary_shim()
    extracted_sources = [
        _build_0506_extracted_source(modules, record, index)
        for index, record in enumerate(plan["source_records"], start=1)
    ]
    logger = modules["PipelineLogger"](
        run_id=run_id,
        artifacts_dir=_route_0506_stage_artifacts_dir_for_logger(artifact_root, run_id=run_id),
    )
    client = _build_0506_pipeline_client(modules, str(plan["client_mode"]))
    runner = modules["BlogPipelineRunner"](client=client, logger=logger)
    result = runner.run_extracted_sources(
        extracted_sources,
        genre_id=str(plan["genre_id"]),
        target_reader=_target_reader(input_contract),
        article_goal=_article_goal(input_contract),
        narrator=plan["narrator"],
    )
    quality_check = enrich_route_0506_sentence_too_long_issue_text(result.quality_check, result.final_article)
    visible_output_contract = route_0506_visible_output_contract_gate_result(client, result.final_article)
    if not visible_output_contract["pass"]:
        blocked = build_route_0506_visible_output_contract_blocked_result(
            input_contract=input_contract,
            artifact_root=artifact_root,
            visible_output_contract=visible_output_contract,
            quality_check=quality_check,
            security_gate=security_gate,
        )
        write_route_0506_result_artifacts(
            artifact_root,
            blocked,
            input_contract=input_contract,
            source_snapshot=plan["source_snapshot"],
            security_gate=security_gate,
        )
        return blocked
    visible = build_route_0506_visible_result(
        {
            "final_article": result.final_article,
            "quality_check": quality_check,
            "genre_id": plan["genre_id"],
            "source_snapshot_hash": plan["source_snapshot"]["canonical_hash"],
            "client_mode": plan["client_mode"],
            "usage_summary": {
                "api_send": plan["external_llm_send"],
                "status": str(plan["client_mode"]),
                "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini") if plan["external_llm_send"] else "",
                "reasoning_effort": os.getenv("OPENAI_REASONING_EFFORT", "high") if plan["external_llm_send"] else "",
                "actual_usage_available": False,
            },
        },
        input_contract=input_contract,
        artifact_root=artifact_root,
    )
    write_route_0506_result_artifacts(
        artifact_root,
        visible,
        input_contract=input_contract,
        source_snapshot=plan["source_snapshot"],
        security_gate=security_gate,
    )
    return visible


def route_0506_visible_output_contract_gate_result(client: Any, final_article: str) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    for item in route_0506_stage_output_guard_violations(client):
        violation_types = [
            str(violation)
            for violation in item.get("violation_types", [])
            if route_0506_is_visible_output_contract_violation_type(str(violation))
        ]
        if not violation_types:
            continue
        violations.append(
            {
                "source": "stage_output_guard",
                "stage_name": str(item.get("stage_name") or ""),
                "violation_types": violation_types,
                "previous_char_count": int(item.get("previous_char_count") or 0),
                "generated_char_count": int(item.get("generated_char_count") or 0),
            }
        )

    final_violation_types = route_0506_visible_output_contract_violations(final_article)
    if final_violation_types:
        violations.append(
            {
                "source": "final_article",
                "stage_name": "final_article",
                "violation_types": final_violation_types,
                "generated_char_count": len(str(final_article or "").strip()),
            }
        )

    return {
        "pass": not violations,
        "violations": violations,
    }


def build_route_0506_visible_output_contract_blocked_result(
    *,
    input_contract: Mapping[str, Any],
    artifact_root: Path | str,
    visible_output_contract: Mapping[str, Any],
    quality_check: Mapping[str, Any],
    security_gate: Mapping[str, Any],
) -> dict[str, Any]:
    blocked_reason = route_0506_visible_output_contract_blocked_reason(visible_output_contract)
    blocked = build_route_0506_blocked_result(
        input_contract=input_contract,
        artifact_root=artifact_root,
        reason_code=ROUTE_0506_VISIBLE_OUTPUT_CONTRACT_FAILED,
        blocked_reason=blocked_reason,
        security_gate=security_gate,
        schema_report={"status": "fail", "visible_output_contract": dict(visible_output_contract)},
    )
    quality_report = dict(blocked.get("quality_report") or {})
    quality_report["visible_output_contract"] = dict(visible_output_contract)
    quality_report["qa_gate_result"] = "blocked_by_visible_output_contract"
    quality_report["upstream_quality_check"] = dict(quality_check)
    blocked["quality_report"] = quality_report
    return blocked


def route_0506_visible_output_contract_blocked_reason(visible_output_contract: Mapping[str, Any]) -> str:
    parts: list[str] = []
    violations = visible_output_contract.get("violations")
    if isinstance(violations, list):
        for item in violations:
            if not isinstance(item, Mapping):
                continue
            stage = str(item.get("stage_name") or item.get("source") or "unknown")
            types = item.get("violation_types")
            type_text = ",".join(str(value) for value in types) if isinstance(types, list) else "unknown"
            parts.append(f"{stage}:{type_text}")
    return "visible_output_contract_failed:" + ";".join(parts or ["unknown"])


def route_0506_markdown_heading_sentence_boundaries(text: str) -> str:
    """Make markdown headings sentence boundaries for Desktop 0506 stylometry."""

    lines: list[str] = []
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.endswith(("。", "！", "？", "!", "?")):
            lines.append(f"{line}。")
        else:
            lines.append(line)
    return "\n".join(lines)


def enrich_route_0506_sentence_too_long_issue_text(
    quality_check: Mapping[str, Any],
    article_text: str,
) -> dict[str, Any]:
    enriched = json.loads(json.dumps(dict(quality_check), ensure_ascii=False))
    quality = enriched.get("quality_check")
    if not isinstance(quality, dict):
        return enriched
    issues = quality.get("issues")
    if not isinstance(issues, list):
        return enriched
    long_sentences = route_0506_long_sentences(
        article_text,
        long_limit=_route_0506_quality_long_sentence_limit(quality),
    )
    if not long_sentences:
        return enriched
    longest = long_sentences[0]
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        if issue.get("type") == "sentence_too_long" and not str(issue.get("text") or "").strip():
            issue["text"] = longest
    return enriched


def route_0506_long_sentences(article_text: str, *, long_limit: int = ROUTE_0506_SENTENCE_LONG_LIMIT_FALLBACK) -> list[str]:
    text = route_0506_markdown_heading_sentence_boundaries(article_text)
    sentences = _route_0506_split_japanese_sentences(text)
    return [
        sentence
        for sentence in sorted(sentences, key=lambda item: len(item.rstrip("。！？!?")), reverse=True)
        if len(sentence.rstrip("。！？!?")) > long_limit
    ]


def _route_0506_split_japanese_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    current: list[str] = []
    for char in str(text or ""):
        current.append(char)
        if char in "。！？!?":
            sentence = "".join(current).strip()
            if sentence:
                sentences.append(sentence)
            current = []
    trailing = "".join(current).strip()
    if trailing:
        sentences.append(trailing)
    return sentences


def _route_0506_quality_long_sentence_limit(quality: Mapping[str, Any]) -> int:
    try:
        stylometry_module = import_module("app.services.stylometry")
        cfg = stylometry_module.load_stylometry_config()
        return int(cfg.get("sentence", {}).get("long_sentence_chars", ROUTE_0506_SENTENCE_LONG_LIMIT_FALLBACK))
    except Exception:
        return ROUTE_0506_SENTENCE_LONG_LIMIT_FALLBACK


def _install_route_0506_markdown_quality_boundary_shim() -> None:
    stylometry_module = import_module("app.services.stylometry")
    checker_module = import_module("app.agents.japanese_quality_checker")
    if getattr(stylometry_module, "_notecode_markdown_quality_boundary_installed", False):
        checker_module.analyze_text = stylometry_module.analyze_text
        return

    original_analyze_text = stylometry_module.analyze_text

    def analyze_text_with_markdown_boundaries(text: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        return original_analyze_text(route_0506_markdown_heading_sentence_boundaries(text), config)

    stylometry_module.analyze_text = analyze_text_with_markdown_boundaries
    checker_module.analyze_text = analyze_text_with_markdown_boundaries
    stylometry_module._notecode_markdown_quality_boundary_installed = True


def _source_locator(item: Mapping[str, Any], index: int) -> str:
    return str(
        item.get("locator")
        or item.get("url")
        or item.get("canonical_url")
        or item.get("source_label")
        or f"notecode_source:{index}"
    ).strip()


def _validated_source_locator(item: Mapping[str, Any], index: int) -> str:
    locator = _source_locator(item, index)
    if is_local_file_locator(locator):
        uploaded_locator = normalize_uploaded_file_locator(locator)
        if not uploaded_locator:
            raise Route0506AdapterError("local_file_locator_rejected")
        embedded_locator = _embedded_uploaded_source_locator(item)
        if embedded_locator:
            return embedded_locator
        return uploaded_locator
    if is_unsafe_url_label(locator):
        raise Route0506AdapterError("unsafe_url_scheme_rejected")
    return locator


def _embedded_uploaded_source_locator(item: Mapping[str, Any]) -> str:
    content = str(item.get("content") or item.get("text") or item.get("extracted_text") or "")
    match = re.search(r"(?m)^\s*LOCATOR:\s*(.+?)\s*$", content)
    if not match:
        return ""
    locator = str(match.group(1) or "").strip()
    if not locator or is_local_file_locator(locator) or is_unsafe_url_label(locator):
        return ""
    return locator[:400]


def _target_reader(input_contract: Mapping[str, Any]) -> str:
    return str(input_contract.get("audience_profile") or input_contract.get("target_reader") or "first-time reader").strip()


def _article_goal(input_contract: Mapping[str, Any]) -> str:
    return str(
        input_contract.get("topic_statement")
        or input_contract.get("core_message")
        or input_contract.get("prompt_raw")
        or "write a grounded blog article from the provided source_documents"
    ).strip()


def _load_0506_modules(route_root: Path) -> dict[str, Any]:
    root = route_root.resolve()
    existing_app = sys.modules.get("app")
    if existing_app is not None:
        app_file = str(getattr(existing_app, "__file__", "") or "")
        if app_file and not Path(app_file).resolve().is_relative_to(root):
            raise Route0506AdapterError(f"python_module_app_already_loaded_from_other_root:{app_file}")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    route_site_packages = root / ".venv" / "Lib" / "site-packages"
    if route_site_packages.exists() and str(route_site_packages) not in sys.path:
        sys.path.insert(1, str(route_site_packages))
    try:
        pipeline_runner = import_module("app.services.pipeline_runner")
        pipeline_logging = import_module("app.services.pipeline_logging")
        llm_client = import_module("app.services.llm_client")
        schema_validator = import_module("app.services.schema_validator")
        local_llm_client = import_module("app.services.local_llm_client")
        source_acquisition = import_module("app.services.source_acquisition")
    except Exception as exc:  # pragma: no cover - host dependency details vary.
        raise Route0506AdapterError(f"route_0506_import_failed:{type(exc).__name__}:{exc}") from exc
    return {
        "BlogPipelineRunner": pipeline_runner.BlogPipelineRunner,
        "PipelineLogger": pipeline_logging.PipelineLogger,
        "select_default_llm_client": llm_client.select_default_llm_client,
        "llm_client_module": llm_client,
        "schema_validator_module": schema_validator,
        "LocalPipelineClient": local_llm_client.LocalPipelineClient,
        "ExtractedSource": source_acquisition.ExtractedSource,
        "SourceSpan": source_acquisition.SourceSpan,
        "stable_source_id": source_acquisition.stable_source_id,
    }


def _route_0506_stage_artifacts_dir_for_logger(artifact_root: Path | str, *, run_id: str) -> Path:
    artifacts_dir = Path(artifact_root) / "route_0506" / "pipeline_stage_artifacts"
    if os.name != "nt":
        return artifacts_dir

    ledger_path = artifacts_dir / str(run_id) / "openai_inflight_ledger.jsonl"
    absolute_ledger_path = _route_0506_absolute_path(ledger_path)
    if len(str(absolute_ledger_path)) < WINDOWS_LEGACY_MAX_PATH:
        return artifacts_dir
    return _route_0506_windows_long_path(_route_0506_absolute_path(artifacts_dir))


def _route_0506_absolute_path(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve(strict=False)
    return (Path.cwd() / path).resolve(strict=False)


def _route_0506_windows_long_path(path: Path) -> Path:
    text = str(path)
    if text.startswith(WINDOWS_LONG_PATH_PREFIX):
        return path
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text.lstrip("\\"))
    return Path(WINDOWS_LONG_PATH_PREFIX + text)


def _build_0506_pipeline_client(modules: Mapping[str, Any], client_mode: str) -> Any:
    if client_mode == LOCAL_DETERMINISTIC_VALIDATION:
        return _Route0506LocalDeterministicCompatClient(modules["LocalPipelineClient"]())
    if client_mode == OPENAI_GENERATION_CANDIDATE:
        if os.getenv("BLOGGEN_LLM_MODE") != "openai":
            raise Route0506AdapterError("route_0506_openai_mode_requires_BLOGGEN_LLM_MODE_openai")
        if not os.getenv("OPENAI_API_KEY"):
            raise Route0506AdapterError("route_0506_openai_mode_requires_OPENAI_API_KEY")
        _install_openai_schema_compatibility_shim(modules)
        client = _Route0506OpenAIStructuredOutputCompatClient(modules["select_default_llm_client"]())
        return wrap_route_0506_stage_output_guard(client)
    raise Route0506AdapterError(f"unsupported_route_0506_client_mode:{client_mode}")


class _Route0506LocalDeterministicCompatClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def generate_json(
        self,
        stage_name: str,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        effective_payload = (
            enrich_route_0506_article_brief_builder_payload(payload)
            if schema_name == "article_brief.schema.json"
            else payload
        )
        result = self._client.generate_json(stage_name, instructions, effective_payload, schema_name)
        if schema_name != "article_brief.schema.json":
            return result
        normalized = normalize_route_0506_openai_unique_array_fields(schema_name, result)
        return _route_0506_apply_company_intro_section_planning_contract(normalized, effective_payload)


class _Route0506OpenAIStructuredOutputCompatClient:
    def __init__(self, client: Any) -> None:
        self._client = client
        self._source_card_indexes: dict[str, int] = {}
        self._next_source_card_index = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        return self._client.generate_text(
            stage_name,
            route_0506_openai_text_stage_contract_instruction(stage_name, instructions),
            payload,
        )

    def generate_json(
        self,
        stage_name: str,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        effective_payload = (
            enrich_route_0506_article_brief_builder_payload(payload)
            if schema_name == "article_brief.schema.json"
            else payload
        )
        result = self._client.generate_json(stage_name, instructions, effective_payload, schema_name)
        normalized = normalize_route_0506_openai_unique_array_fields(schema_name, result)
        if schema_name == "source_card.schema.json":
            return normalize_route_0506_source_card_fact_ids(
                normalized,
                source_index=self._source_card_index(payload),
            )
        return normalized

    def _source_card_index(self, payload: Mapping[str, Any]) -> int:
        packet = payload.get("source_packet") if isinstance(payload, Mapping) else None
        source_id = str(packet.get("source_id") or "").strip() if isinstance(packet, Mapping) else ""
        if source_id and source_id in self._source_card_indexes:
            return self._source_card_indexes[source_id]
        self._next_source_card_index += 1
        if source_id:
            self._source_card_indexes[source_id] = self._next_source_card_index
        return self._next_source_card_index


def route_0506_structural_editor_return_contract_instruction(stage_name: str, instructions: str) -> str:
    if stage_name != "structural_editor":
        return instructions
    text = str(instructions or "").rstrip()
    if ROUTE_0506_STRUCTURAL_EDITOR_ARTICLE_RETURN_CONTRACT in text:
        return text
    return f"{text}\n\n{ROUTE_0506_STRUCTURAL_EDITOR_ARTICLE_RETURN_CONTRACT}".strip()


def route_0506_opening_editor_return_contract_instruction(stage_name: str, instructions: str) -> str:
    if stage_name != "opening_editor":
        return instructions
    text = str(instructions or "").rstrip()
    if ROUTE_0506_OPENING_EDITOR_ARTICLE_RETURN_CONTRACT in text:
        return text
    return f"{text}\n\n{ROUTE_0506_OPENING_EDITOR_ARTICLE_RETURN_CONTRACT}".strip()


def route_0506_draft_writer_brief_realization_contract_instruction(stage_name: str, instructions: str) -> str:
    if stage_name != "draft_writer":
        return instructions
    text = str(instructions or "").rstrip()
    if ROUTE_0506_DRAFT_WRITER_BRIEF_REALIZATION_CONTRACT in text:
        return text
    return f"{text}\n\n{ROUTE_0506_DRAFT_WRITER_BRIEF_REALIZATION_CONTRACT}".strip()


def route_0506_global_consistency_preserve_depth_contract_instruction(stage_name: str, instructions: str) -> str:
    if stage_name != "global_consistency_editor":
        return instructions
    text = str(instructions or "").rstrip()
    if ROUTE_0506_GLOBAL_CONSISTENCY_PRESERVE_DEPTH_CONTRACT in text:
        return text
    return f"{text}\n\n{ROUTE_0506_GLOBAL_CONSISTENCY_PRESERVE_DEPTH_CONTRACT}".strip()


def route_0506_openai_text_stage_contract_instruction(stage_name: str, instructions: str) -> str:
    text = route_0506_structural_editor_return_contract_instruction(stage_name, instructions)
    text = route_0506_opening_editor_return_contract_instruction(stage_name, text)
    text = route_0506_draft_writer_brief_realization_contract_instruction(stage_name, text)
    return route_0506_global_consistency_preserve_depth_contract_instruction(stage_name, text)


def make_openai_structured_output_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Convert the 0506 jsonschema subset into OpenAI Structured Outputs strict subset."""

    return _sanitize_openai_structured_output_node(schema)


def normalize_route_0506_openai_unique_array_fields(schema_name: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not schema_name.endswith(".schema.json"):
        return dict(payload)
    normalized = _normalize_route_0506_unique_array_node(payload)
    if schema_name == "knowledge_pack.schema.json":
        return _normalize_route_0506_single_fact_conflicts(normalized)
    if schema_name == "article_brief.schema.json":
        return normalize_route_0506_company_intro_article_brief_metadata(normalized)
    return normalized


def normalize_route_0506_source_card_fact_ids(payload: Mapping[str, Any], *, source_index: int) -> dict[str, Any]:
    result = dict(payload)
    facts = result.get("facts")
    if not isinstance(facts, list):
        return result

    normalized_facts: list[Any] = []
    for fact_index, fact in enumerate(facts, start=1):
        if not isinstance(fact, Mapping):
            normalized_facts.append(fact)
            continue
        next_fact = dict(fact)
        next_fact["fact_id"] = f"F{source_index:02d}{fact_index:02d}"
        normalized_facts.append(next_fact)
    result["facts"] = normalized_facts
    return result


def _normalize_route_0506_single_fact_conflicts(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    pack = result.get("article_knowledge_pack")
    if not isinstance(pack, Mapping):
        return result

    conflicts = pack.get("conflicts")
    if not isinstance(conflicts, list):
        return result

    next_conflicts: list[Any] = []
    single_fact_caveats: list[str] = []
    for conflict in conflicts:
        if not isinstance(conflict, Mapping):
            next_conflicts.append(conflict)
            continue
        fact_ids = conflict.get("involved_fact_ids")
        if isinstance(fact_ids, list) and len(fact_ids) == 1:
            single_fact_caveats.append(_route_0506_single_fact_caveat_text(conflict, str(fact_ids[0])))
            continue
        next_conflicts.append(dict(conflict))

    if not single_fact_caveats:
        return result

    next_pack = dict(pack)
    next_pack["conflicts"] = next_conflicts
    existing_do_not_infer = next_pack.get("do_not_infer")
    if isinstance(existing_do_not_infer, list):
        next_pack["do_not_infer"] = [*existing_do_not_infer, *single_fact_caveats]
    else:
        next_pack["do_not_infer"] = single_fact_caveats
    result["article_knowledge_pack"] = next_pack
    return result


def _route_0506_single_fact_caveat_text(conflict: Mapping[str, Any], fact_id: str) -> str:
    issue = str(conflict.get("issue") or "").strip()
    resolution = str(conflict.get("resolution") or "").strip()
    parts = [f"single_fact_caveat:{fact_id}"]
    if issue:
        parts.append(f"issue={issue}")
    if resolution:
        parts.append(f"resolution={resolution}")
    if conflict.get("do_not_mention") is True:
        parts.append("do_not_mention=true")
    return " | ".join(parts)


def _normalize_route_0506_unique_array_node(value: Any, *, key_name: str = "") -> Any:
    if isinstance(value, list):
        items = [_normalize_route_0506_unique_array_node(item) for item in value]
        if key_name in ROUTE_0506_OPENAI_UNIQUE_ARRAY_KEYS:
            return _dedupe_route_0506_list(items)
        return items
    if isinstance(value, Mapping):
        return {str(key): _normalize_route_0506_unique_array_node(child, key_name=str(key)) for key, child in value.items()}
    return value


def _dedupe_route_0506_list(items: list[Any]) -> list[Any]:
    deduped: list[Any] = []
    seen: set[str] = set()
    for item in items:
        marker = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(item)
    return deduped


def _install_openai_schema_compatibility_shim(modules: Mapping[str, Any]) -> None:
    llm_client = modules["llm_client_module"]
    original_load_schema = getattr(llm_client, "load_schema")
    if getattr(llm_client, "_notecode_openai_schema_compat_installed", False):
        return

    def load_openai_schema(schema_name: str) -> dict[str, Any]:
        return make_openai_structured_output_schema(original_load_schema(schema_name))

    # Keep 0506's local jsonschema validation on the original schemas. Only
    # the schema sent to OpenAI Structured Outputs needs the stricter subset.
    llm_client.load_schema = load_openai_schema
    llm_client._notecode_openai_schema_compat_installed = True


def _sanitize_openai_structured_output_node(value: Any, *, in_properties: bool = False) -> Any:
    if isinstance(value, list):
        return [_sanitize_openai_structured_output_node(item) for item in value]
    if not isinstance(value, Mapping):
        return value

    node: dict[str, Any] = {}
    for key, child in value.items():
        if not in_properties and key in OPENAI_STRUCTURED_OUTPUT_UNSUPPORTED_KEYS:
            continue
        if key == "format" and child not in OPENAI_STRUCTURED_OUTPUT_SUPPORTED_FORMATS:
            continue
        if key == "additionalProperties":
            node[key] = False
            continue
        node[key] = _sanitize_openai_structured_output_node(child, in_properties=(key == "properties"))

    if _is_object_schema(node):
        properties = node.get("properties")
        if isinstance(properties, Mapping):
            node["required"] = list(properties.keys())
        node["additionalProperties"] = False
    return node


def _is_object_schema(node: Mapping[str, Any]) -> bool:
    schema_type = node.get("type")
    if schema_type == "object":
        return True
    return isinstance(schema_type, list) and "object" in schema_type


def _build_0506_extracted_source(modules: Mapping[str, Any], record: Route0506SourceRecord, index: int) -> Any:
    source_id = modules["stable_source_id"](record.source_type, record.title, record.locator or record.content)
    confidence = "high" if len(record.content) >= 500 else "medium" if len(record.content) >= 120 else "low"
    span = modules["SourceSpan"](record.source_span_id or f"notecode_{index:03d}", record.content, record.locator)
    extraction_method = (
        "notecode_company_intro_saved_source_surface_v1"
        if record.source_span_id.startswith("route0506_company_intro_saved_")
        else "notecode_input_contract_source_documents"
    )
    return modules["ExtractedSource"](
        source_id=source_id,
        source_type=record.source_type,
        title=record.title,
        extracted_text=record.content,
        source_spans=[span],
        metadata={
            "source_label": record.title,
            "url": record.locator if record.locator.startswith(("http://", "https://")) else None,
            "canonical_url": record.locator if record.locator.startswith(("http://", "https://")) else None,
            "source_priority": 5,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "extraction_method": extraction_method,
        },
        warnings=[] if confidence != "low" else ["saved source text is thin"],
        extraction_confidence=confidence,
        can_proceed=confidence in {"high", "medium"},
    )
