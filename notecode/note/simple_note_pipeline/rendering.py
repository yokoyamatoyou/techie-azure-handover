"""Source digest and output rendering helpers for the simple note pipeline."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping

from note.prompt_sanitizer import sanitize_untrusted_text
from note.source_document_utils import normalize_source_document_entry

_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")
_STOPWORDS = {
    "こと",
    "もの",
    "ため",
    "よう",
    "これ",
    "それ",
    "今回",
    "記事",
    "内容",
    "情報",
    "紹介",
    "会社",
    "企業",
    "サービス",
    "製品",
    "について",
    "ます",
    "です",
}
_LINKEDIN_CTA_BY_TYPE = {
    "announcement": "変更点や確認事項は本文で整理しています。必要な方は保存してご活用ください。",
    "daily_story": "近い経験や気づきがあれば、コメントで教えていただけると嬉しいです。",
    "branding": "背景や価値の整理は本文にまとめています。必要な方はあとで読み返せるよう保存してください。",
    "default": "背景と要点は本文にまとめています。必要な方は保存してご活用ください。",
}
_CORPORATE_ANCHOR_RE = re.compile(r"(?:当社|弊社|私たち|わたしたち)")
_CORPORATE_NAME_RE = re.compile(r"(?:株式会社[一-龥A-Za-z0-9・ー]{1,24}|[一-龥A-Za-z0-9・ー]{1,24}株式会社)")
_GUIDE_TONE_RE = re.compile(r"(?:紹介します|整理します|見ていきます|お伝えします|確認します|触れます|考えていきます)")
_ADVICE_TONE_RE = re.compile(
    r"(?:するとよいでしょう|すると良いでしょう|ことが重要です|ことが効果的です|ことが望ましいでしょう|が鍵になります)"
)
_LINKEDIN_MAX_CHARS = 700
_LINKEDIN_MIN_BODY_CHARS = 180


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _runtime_error_class(reason_code: str) -> str:
    code = str(reason_code or "").upper()
    if code.startswith("INP_"):
        return "user_input"
    if code.startswith(("POL_", "SEC_")):
        return "policy"
    if code.startswith("TRN_"):
        return "transient"
    return "system"


def _clean_inline_text(value: Any, *, limit: int = 300) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _clean_multiline_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_keywords(text: str, *, limit: int = 8) -> List[str]:
    keywords: List[str] = []
    for token in _TOKEN_RE.findall(str(text or "")):
        normalized = token.strip().lower()
        if not normalized or normalized in _STOPWORDS or normalized in keywords:
            continue
        keywords.append(normalized)
        if len(keywords) >= limit:
            break
    return keywords


def _extract_company_anchor_terms(source_pack: Mapping[str, Any]) -> List[str]:
    terms: List[str] = ["当社", "弊社", "私たち"]
    for item in _to_plain_list(source_pack.get("source_documents"))[:4]:
        normalized = normalize_source_document_entry(item, include_content_type=False)
        for candidate in (normalized.get("title"), normalized.get("content")):
            for matched in _CORPORATE_NAME_RE.findall(str(candidate or "")):
                term = _clean_inline_text(matched, limit=32)
                if term and term not in terms:
                    terms.append(term)
                if len(terms) >= 8:
                    return terms
    return terms


def _compute_contract_voice_scores(
    contract: Mapping[str, Any],
    draft: Any,
    diagnostics: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    text = _clean_multiline_text(f"{getattr(draft, 'lead', '')}\n\n{getattr(draft, 'body', '')}")
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    speaker_profile = str(contract.get("speaker_profile") or "").strip()
    relationship_mode = str(contract.get("relationship_mode") or "").strip().lower()
    paragraph_first_person_starts = int(diagnostics.get("paragraph_first_person_starts", 0) or 0)
    explicit_subject_ratio = float(diagnostics.get("explicit_subject_ratio", 0.0) or 0.0)

    company_anchor_terms = _extract_company_anchor_terms(source_pack)
    company_anchor_hit_terms = [
        term
        for term in company_anchor_terms
        if term and term in text
    ]
    company_anchor_hit_count = len(company_anchor_hit_terms)
    guide_tone_count = len(_GUIDE_TONE_RE.findall(text))
    advice_tone_count = len(_ADVICE_TONE_RE.findall(text))
    corporate_voice_expected = semantic_key == "company_introduction" or (
        article_type == "branding"
        and any(token in speaker_profile for token in ("運営", "広報", "会社", "企業"))
    )

    speaker_consistency_score = 1.0 if speaker_profile else 0.8
    if corporate_voice_expected:
        if company_anchor_hit_count <= 0:
            speaker_consistency_score = min(speaker_consistency_score, 0.68)
        elif company_anchor_hit_count == 1:
            speaker_consistency_score = min(speaker_consistency_score, 0.84)
    if corporate_voice_expected and advice_tone_count >= 2:
        speaker_consistency_score = min(speaker_consistency_score, 0.74)

    pronoun_consistency_score = 1.0
    if paragraph_first_person_starts > 2:
        pronoun_consistency_score = 0.8
    if corporate_voice_expected and company_anchor_hit_count <= 0:
        pronoun_consistency_score = min(pronoun_consistency_score, 0.85)
    if explicit_subject_ratio > 0.45:
        pronoun_consistency_score = min(pronoun_consistency_score, 0.8)

    relationship_consistency_score = 1.0 if relationship_mode else 0.8
    if relationship_mode == "guide" and guide_tone_count <= 0:
        relationship_consistency_score = min(relationship_consistency_score, 0.85)

    return {
        "speaker_consistency_score": round(max(0.0, speaker_consistency_score), 4),
        "pronoun_consistency_score": round(max(0.0, pronoun_consistency_score), 4),
        "relationship_consistency_score": round(max(0.0, relationship_consistency_score), 4),
        "company_anchor_terms": company_anchor_terms[:8],
        "company_anchor_hit_terms": company_anchor_hit_terms[:6],
        "company_anchor_hit_count": int(company_anchor_hit_count),
        "speaker_advice_tone_count": int(advice_tone_count),
        "relationship_guide_tone_count": int(guide_tone_count),
    }


def normalize_hashtags(raw: str, *, fallback_terms: Iterable[str]) -> str:
    found = re.findall(r"#(?:[A-Za-z0-9_一-龥ぁ-んァ-ヴー]{2,24})", str(raw or ""))
    normalized: List[str] = []
    for tag in found:
        if tag not in normalized:
            normalized.append(tag)
        if len(normalized) >= 5:
            break
    if not normalized:
        for term in fallback_terms:
            cleaned = re.sub(r"[^A-Za-z0-9一-龥ぁ-んァ-ヴー]", "", str(term or ""))[:20]
            if len(cleaned) < 2:
                continue
            tag = f"#{cleaned}"
            if tag not in normalized:
                normalized.append(tag)
            if len(normalized) >= 4:
                break
    if "#note" not in normalized and len(normalized) < 5:
        normalized.append("#note")
    return " ".join(normalized[:5]).strip()


def build_source_pack(contract: Mapping[str, Any]) -> Dict[str, Any]:
    source_documents = [
        normalize_source_document_entry(item, include_content_type=False)
        for item in _to_plain_list(contract.get("source_documents"))
    ]
    source_documents = [item for item in source_documents if item]
    grounding_items = []
    for item in _to_plain_list(contract.get("source_grounding_items"))[:10]:
        if not isinstance(item, Mapping):
            continue
        fact_text = _clean_inline_text(item.get("fact_text") or "", limit=180)
        source_title = _clean_inline_text(item.get("source_title") or "", limit=80)
        locator = _clean_inline_text(item.get("locator") or "", limit=120)
        bucket = _clean_inline_text(item.get("bucket") or "", limit=24)
        if not fact_text:
            continue
        reference = " / ".join(part for part in (source_title, locator) if part)
        grounding_items.append({"bucket": bucket, "fact_text": fact_text, "reference": reference})
    source_summaries = []
    for item in source_documents[:4]:
        title = _clean_inline_text(item.get("title") or item.get("locator") or "", limit=100)
        content = sanitize_untrusted_text(str(item.get("content") or "")[:700])
        source_summaries.append({"title": title, "excerpt": content})
    return {
        "grounding_items": grounding_items,
        "source_summaries": source_summaries,
        "source_documents": source_documents,
    }


def build_references_markdown(source_documents: Iterable[Any]) -> str:
    entries: List[str] = []
    for item in list(source_documents)[:6]:
        normalized = normalize_source_document_entry(item, include_content_type=False)
        title = _clean_inline_text(normalized.get("title") or "", limit=120)
        locator = _clean_inline_text(normalized.get("locator") or "", limit=180)
        if title and locator and title != locator:
            entries.append(f"- {title}\n  {locator}")
        elif title:
            entries.append(f"- {title}")
        elif locator:
            entries.append(f"- {locator}")
    if not entries:
        return ""
    return "## 参考情報\n" + "\n".join(entries)


def _build_linkedin_cta(article_type: str) -> str:
    return _LINKEDIN_CTA_BY_TYPE.get(article_type, _LINKEDIN_CTA_BY_TYPE["default"])


def format_for_linkedin(lead: str, body: str, hashtags: str, article_type: str) -> str:
    text = re.sub(r"^##\s*", "📌 ", str(body or ""), flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"【\1】", text)
    text = re.sub(r"^-\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    linkedin_cta = _build_linkedin_cta(article_type)
    tag_text = " ".join(str(hashtags or "").split()[:4])
    target_chars = _LINKEDIN_MAX_CHARS
    overhead = len(lead) + len(linkedin_cta) + len(tag_text) + 6
    body_limit = max(_LINKEDIN_MIN_BODY_CHARS, target_chars - overhead)
    if len(text) > body_limit:
        text = text[:body_limit].rstrip()
        last_break = max(text.rfind("。"), text.rfind("！"), text.rfind("？"), text.rfind("\n"))
        if last_break >= int(body_limit * 0.6):
            text = text[: last_break + 1].rstrip()
    parts = [str(lead or "").strip(), "", text, "", linkedin_cta, "", tag_text]
    return "\n".join(part for part in parts if part is not None).strip()


def build_result(
    *,
    contract: Mapping[str, Any],
    draft: Any,
    source_pack: Mapping[str, Any],
    diagnostics: Mapping[str, Any],
    editor_report: Mapping[str, Any],
    llm_metadata: Mapping[str, Any],
    repair_metadata: Mapping[str, Any],
    repair_applied: bool,
) -> Dict[str, Any]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    normalized_editor_report = _to_plain_dict(editor_report)
    references = build_references_markdown(source_pack.get("source_documents") or [])
    full_body = "\n\n".join(part for part in (draft.lead, draft.body, references) if part)
    full_text_parts = [draft.title, full_body]
    if draft.hashtags:
        full_text_parts.extend(["---", draft.hashtags])
    full_text = "\n\n".join(part for part in full_text_parts if part).strip()
    linkedin_text = format_for_linkedin(draft.lead, draft.body, draft.hashtags, article_type)
    voice_scores = _compute_contract_voice_scores(contract, draft, diagnostics, source_pack)
    base_alignment_score = round(
        0.35 * float(diagnostics.get("must_cover_reflection_rate") or 0.0)
        + 0.25 * float(diagnostics.get("prompt_anchor_coverage") or 0.0)
        + 0.20 * float(diagnostics.get("section_focus_coverage") or 0.0)
        + 0.20,
        4,
    )
    alignment_multiplier = round(
        0.55
        + 0.25 * float(voice_scores.get("speaker_consistency_score") or 0.0)
        + 0.10 * float(voice_scores.get("pronoun_consistency_score") or 0.0)
        + 0.10 * float(voice_scores.get("relationship_consistency_score") or 0.0),
        4,
    )
    contract_alignment = {
        "article_type": article_type,
        "semantic_article_key": str(contract.get("semantic_article_key") or ""),
        "speaker_profile": str(contract.get("speaker_profile") or ""),
        "audience_profile": str(contract.get("audience_profile") or ""),
        "must_cover_count": len(_to_plain_list(contract.get("must_cover"))),
        "must_cover_reflection_rate": float(diagnostics.get("must_cover_reflection_rate") or 0.0),
        "prompt_anchor_coverage": float(diagnostics.get("prompt_anchor_coverage") or 0.0),
        "anchor_term_coverage": float(diagnostics.get("anchor_term_coverage") or 0.0),
        "semantic_anchor_coverage": float(diagnostics.get("semantic_anchor_coverage") or 0.0),
        "semantic_claim_coverage": float(diagnostics.get("semantic_claim_coverage") or 0.0),
        "section_focus_coverage": float(diagnostics.get("section_focus_coverage") or 0.0),
        "section_focus_total": int(diagnostics.get("heading_count") or 0),
        "speaker_consistency_score": float(voice_scores.get("speaker_consistency_score") or 0.0),
        "pronoun_consistency_score": float(voice_scores.get("pronoun_consistency_score") or 0.0),
        "relationship_consistency_score": float(voice_scores.get("relationship_consistency_score") or 0.0),
        "question_reflection_rate": 1.0 if _to_plain_dict(contract.get("interview_answers")) else 0.0,
        "category_consistency_score": 1.0,
        "company_anchor_terms": list(voice_scores.get("company_anchor_terms") or [])[:8],
        "company_anchor_hit_terms": list(voice_scores.get("company_anchor_hit_terms") or [])[:6],
        "company_anchor_hit_count": int(voice_scores.get("company_anchor_hit_count", 0) or 0),
        "speaker_advice_tone_count": int(voice_scores.get("speaker_advice_tone_count", 0) or 0),
        "relationship_guide_tone_count": int(voice_scores.get("relationship_guide_tone_count", 0) or 0),
        "alignment_score": round(min(1.0, base_alignment_score * alignment_multiplier), 4),
    }
    contextual_naturalness_report = {
        "issue_count": int(diagnostics.get("issue_count") or 0),
        "semantic_issue_count": int(diagnostics.get("semantic_issue_count") or 0),
        "topic_opening_ratio": float(diagnostics.get("topic_opening_ratio") or 0.0),
        "omission_ambiguity_score": float(diagnostics.get("omission_ambiguity_score") or 0.0),
        "ending_bucket_monotony_score": float(diagnostics.get("ending_bucket_monotony_score") or 0.0),
        "awkward_ending_ratio": round(min(1.0, int(diagnostics.get("same_ending_runs", 0) or 0) / 6), 4),
        "ai_template_ending_ratio": round(min(1.0, int(diagnostics.get("duplicate_paragraph_count", 0) or 0) / 4), 4),
        "instructional_fragment_count": 0,
        "semantic_layout": {
            "heading_alignment_mean": 0.5 if int(diagnostics.get("heading_count", 0) or 0) >= 2 else 0.0,
            "heading_reanchor_miss_count": int(diagnostics.get("heading_reanchor_miss_count", 0) or 0),
        },
        "ai_index_score": float(_to_plain_dict(diagnostics.get("ai_index")).get("score") or 0.0),
    }
    output_guard = {
        "blocked": False,
        "reasons": [],
        "hard_reasons": [],
        "hard_reason_count": 0,
        "soft_warnings": [str(item) for item in _to_plain_list(diagnostics.get("soft_warnings") or diagnostics.get("repair_instructions"))][:12],
        "soft_warning_count": len(_to_plain_list(diagnostics.get("soft_warnings") or diagnostics.get("repair_instructions"))),
        "manual_instructional_hits": [],
        "prompt_echo_references": [],
        "failed_parameters": {},
        "issue_count": int(diagnostics.get("issue_count") or 0),
        "semantic_issue_count": int(diagnostics.get("semantic_issue_count") or 0),
        "instructional_fragment_count": 0,
        "error_class": "",
        "reason_code": "",
        "needs_input_items": [],
    }
    io_contract = {
        "contract_resolve": {"in": ["payload"], "out": ["input_contract"]},
        "source_digest": {"in": ["input_contract", "source_documents"], "out": ["source_pack"]},
        "semantic_plan": {"in": ["input_contract", "source_pack"], "out": ["semantic_ledger"] if _to_plain_list(contract.get("_semantic_ledger")) else []},
        "single_pass_generation": {"in": ["input_contract", "source_pack"], "out": ["draft"]},
        "light_guard": {"in": ["draft"], "out": ["diagnostics"]},
        "repair": {"in": ["draft", "diagnostics"], "out": ["repaired_draft"] if repair_applied else []},
        "output_format": {"in": ["draft", "diagnostics"], "out": ["result"]},
        "telemetry": {"in": ["result"], "out": ["pipeline_check"]},
    }
    semantic_ledger = []
    for item in _to_plain_list(contract.get("_semantic_ledger"))[:6]:
        entry = _to_plain_dict(item)
        if not entry:
            continue
        semantic_ledger.append(
            {
                "heading": str(entry.get("heading") or ""),
                "purpose": str(entry.get("purpose") or ""),
                "anchor": str(entry.get("anchor") or ""),
                "claim": str(entry.get("claim") or entry.get("key_message") or ""),
                "bridge": str(entry.get("bridge") or ""),
            }
        )
    pipeline_check = {
        "pipeline_name": "simple_note_pipeline",
        "pipeline_version": "simple-note-v1",
        "input_contract": contract,
        "io_contract": io_contract,
        "semantic_plan": {
            "enabled": bool(semantic_ledger),
            "section_count": len(semantic_ledger),
            "entries": semantic_ledger,
        },
        "contract_alignment": contract_alignment,
        "output_guard_inputs": {
            "hard_soft_eval": {"hard_failed": False, "mode": "observe", "metrics": {"instructional_fragment_count": 0}},
            "contextual_naturalness_report": contextual_naturalness_report,
            "final_quality_eval": {
                "evaluated": True,
                "score": max(0.0, round(1.0 - (float(diagnostics.get("severity") or 0) * 0.12), 4)),
                "soft_warning_count": len(_to_plain_list(diagnostics.get("soft_warnings") or diagnostics.get("repair_instructions"))),
            },
            "contract_alignment": contract_alignment,
            "ai_index": _to_plain_dict(diagnostics.get("ai_index")),
            "legal_summary": _to_plain_dict(diagnostics.get("legal_summary")),
            "proposition_density": _to_plain_dict(diagnostics.get("proposition_density")),
        },
        "quality_metrics": {
            "body_chars": int(diagnostics.get("body_chars") or 0),
            "section_count": int(diagnostics.get("heading_count") or 0),
            "topic_echo_body_only_ratio": float(diagnostics.get("topic_opening_ratio") or 0.0),
            "prompt_follow_anchor_coverage": float(diagnostics.get("prompt_anchor_coverage") or 0.0),
            "semantic_anchor_coverage": float(diagnostics.get("semantic_anchor_coverage") or 0.0),
            "semantic_claim_coverage": float(diagnostics.get("semantic_claim_coverage") or 0.0),
            "heading_reanchor_miss_count": int(diagnostics.get("heading_reanchor_miss_count", 0) or 0),
            "heading_reanchor_miss_ratio": float(diagnostics.get("heading_reanchor_miss_ratio") or 0.0),
            "omission_ambiguity_score": float(diagnostics.get("omission_ambiguity_score") or 0.0),
            "ending_bucket_counts": _to_plain_dict(diagnostics.get("ending_bucket_counts")),
            "ending_bucket_max_run": int(diagnostics.get("ending_bucket_max_run", 0) or 0),
            "ending_bucket_monotony_score": float(diagnostics.get("ending_bucket_monotony_score") or 0.0),
            "proposition_sentence_count": int(diagnostics.get("proposition_sentence_count", 0) or 0),
            "proposition_informative_ratio": float(diagnostics.get("proposition_informative_ratio") or 0.0),
            "proposition_low_info_ratio": float(diagnostics.get("proposition_low_info_ratio") or 0.0),
            "proposition_low_info_examples": _to_plain_list(diagnostics.get("proposition_low_info_examples"))[:4],
            "flagged_span_count": int(diagnostics.get("flagged_span_count", 0) or 0),
            "ai_index_score": float(_to_plain_dict(diagnostics.get("ai_index")).get("score") or 0.0),
            "legal_risk_score": float(_to_plain_dict(diagnostics.get("legal_summary")).get("risk_score") or 0.0),
            "repair_trigger_score": float(diagnostics.get("repair_trigger_score") or 0.0),
            "grammar_repair_count": int(normalized_editor_report.get("grammar_repair_count", 0) or 0),
            "sentence_integrity_repair_count": int(
                normalized_editor_report.get("sentence_integrity_repair_count", 0) or 0
            ),
            "sentence_integrity_warning_count": int(
                normalized_editor_report.get("sentence_integrity_warning_count", 0) or 0
            ),
        },
        "body_generation": {
            "repair_applied": repair_applied,
            "repair_trigger_score": float(diagnostics.get("repair_trigger_score") or 0.0),
            "primary_call": llm_metadata,
            "repair_call": repair_metadata,
        },
        "editor_report": normalized_editor_report,
        "ai_index": _to_plain_dict(diagnostics.get("ai_index")),
        "legal_summary": _to_plain_dict(diagnostics.get("legal_summary")),
        "review_points": _to_plain_list(diagnostics.get("review_points")),
        "output_guard": output_guard,
    }
    return {
        "success": True,
        "title": draft.title,
        "lead": draft.lead,
        "body": draft.body,
        "full_body": full_body,
        "references": references,
        "hashtags": draft.hashtags,
        "full_text": full_text,
        "linkedin_text": linkedin_text,
        "pipeline_check_linkedin": {
            "platform": "linkedin",
            "pipeline_name": "simple_note_pipeline",
            "pipeline_version": "simple-note-v1",
        },
        "pipeline_check": pipeline_check,
        "quality_pipeline_check": {},
        "review_points": _to_plain_list(diagnostics.get("review_points")),
        "hard_failed": False,
        "hard_fail_reasons": [],
        "output_guard": output_guard,
        "reason_code": "OK",
        "runtime_reason_code": "OK",
        "runtime_error_class": "success",
    }


def build_input_stop_result(
    contract: Mapping[str, Any],
    reason_code: str,
    needs_input_items: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    return {
        "success": False,
        "title": "",
        "lead": "",
        "body": "",
        "references": "",
        "hashtags": "",
        "full_text": "",
        "reason_code": reason_code,
        "runtime_reason_code": reason_code,
        "runtime_error_class": _runtime_error_class(reason_code),
        "needs_input_items": list(needs_input_items or []),
        "pipeline_check": {
            "pipeline_name": "simple_note_pipeline",
            "pipeline_version": "simple-note-v1",
            "input_contract": contract,
        },
    }
