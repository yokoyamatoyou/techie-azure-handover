"""Pure output guard evaluation for current mainline results."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from note.prompt_echo_detector import build_prompt_echo_references, detect_prompt_echo_sentences
from note.newalgorithm_pipeline.strict_saas import normalize_strict_saas_mode

_OUTPUT_GUARD_MAX_SEMANTIC_ISSUES = 5
_OUTPUT_GUARD_MIN_ALIGNMENT_SCORE = 0.45
_OUTPUT_GUARD_MIN_MUST_COVER_REFLECTION = 0.50
_OUTPUT_GUARD_MIN_PROMPT_ANCHOR_COVERAGE = 0.34
_OUTPUT_GUARD_MIN_ANCHOR_TERM_COVERAGE = 0.30
_OUTPUT_GUARD_MIN_SECTION_FOCUS_COVERAGE = 0.60
_OUTPUT_GUARD_MIN_SOURCE_TRACE_COVERAGE_FOR_WARNING_ONLY = 0.50
_OUTPUT_GUARD_MIN_SPEAKER_CONSISTENCY = 0.55
_OUTPUT_GUARD_MIN_PRONOUN_CONSISTENCY = 0.50
_OUTPUT_GUARD_MIN_RELATIONSHIP_CONSISTENCY = 0.50
_OUTPUT_GUARD_MIN_HEADING_ALIGNMENT_MEAN = 0.12
_OUTPUT_GUARD_SOFT_MAX_TOPIC_OPENING_RATIO = 0.32
_OUTPUT_GUARD_SOFT_MAX_AWKWARD_ENDING_RATIO = 0.20
_OUTPUT_GUARD_SOFT_MAX_AI_TEMPLATE_ENDING_RATIO = 0.10
_OUTPUT_GUARD_MIN_PROPOSITION_SENTENCE_COUNT = 10
_OUTPUT_GUARD_ANNOUNCEMENT_MIN_PROPOSITION_INFORMATIVE_RATIO = 0.52
_OUTPUT_GUARD_ANNOUNCEMENT_MAX_PROPOSITION_LOW_INFO_RATIO = 0.28
_OUTPUT_GUARD_SOFT_MIN_PROPOSITION_INFORMATIVE_RATIO = 0.45
_OUTPUT_GUARD_SOFT_MAX_PROPOSITION_LOW_INFO_RATIO = 0.36
_AI_EXPLANATORY_FOCUS_KEYS = {"analysis", "explanation"}
_COMPANY_INTRO_ARTICLE_TYPES = {"corporate_culture", "announcement", "company_introduction"}
_BRANDING_ARTICLE_TYPES = {"branding", "case_study"}
_WEB_SOURCE_MODE_BLOCKED_ARTICLE_TYPES = {"announcement"}
_WEB_SOURCE_MODE_BLOCKED_SEMANTIC_KEYS = {"company_introduction"}
_RETRY_PROMPT_CATEGORY_HINTS: Dict[str, List[str]] = {
    "ai_explanatory": [
        "- 定義→仕組み→活用例→注意点の順で説明し、論点を一本化する",
        "- 会社紹介・採用・福利厚生など主題外の話題へ寄らない",
    ],
    "company_introduction": [
        "- 事業内容・提供価値・沿革/背景・今後の方針を中心に構成する",
        "- 一般論のハウツー調や命令口調を減らし、会社紹介の文脈を維持する",
    ],
    "branding": [
        "- 商品/ブランド価値、選定軸、利用シーンを中心に具体化する",
        "- 社内制度・採用・福利厚生など運営内部の話題は避ける",
    ],
    "general": [
        "- 見出しごとに主題との接続を明示し、無関係な代表例を入れない",
    ],
}

_PROPOSITION_LOW_SIGNAL_PATTERN = re.compile(
    r"(?:"
    r"重要(?:です|だ)|"
    r"大切(?:です|だ)|"
    r"必要(?:です|だ)|"
    r"求められ(?:ます|る)|"
    r"期待できます|"
    r"と言(?:え|える)(?:ます|でしょう)?|"
    r"かもしれません|"
    r"ではないでしょうか|"
    r"と考えます|"
    r"につながります|"
    r"ことができます|"
    r"が挙げられます|"
    r"がポイントです"
    r")"
)
_PROPOSITION_CONCRETE_SIGNAL_PATTERN = re.compile(
    r"(?:"
    r"\d|%|％|年|月|日|時|分|秒|円|人|社|件|回|"
    r"「|」|『|』|https?://|"
    r"追加|更新|公開|開始|終了|廃止|改善|変更|対応|提供|導入|移行|修正|発表|告知"
    r")"
)
_PROPOSITION_TOKEN_PATTERN = re.compile(r"[一-龥]{2,}|[ァ-ヴー]{3,}|[A-Za-z]{3,}")
_PROPOSITION_STOP_TOKENS = {
    "こと",
    "もの",
    "ため",
    "よう",
    "それ",
    "これ",
    "今回",
    "記事",
    "内容",
    "情報",
    "視点",
    "読者",
    "自分",
    "相手",
    "必要",
    "重要",
    "可能",
    "状況",
    "場合",
}


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _safe_round_float(value: Any, digits: int = 4, default: float = 0.0) -> float:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return default


def _build_proposition_density_target_text(result: Dict[str, Any]) -> str:
    lead = str(result.get("lead", "") or "").strip()
    body = str(result.get("body", "") or "").strip()
    if lead or body:
        return "\n\n".join(part for part in (lead, body) if part)
    return str(result.get("full_text", "") or "").strip()


def _extract_proposition_sentences(text: str) -> List[str]:
    source = (text or "").strip()
    if not source:
        return []

    kept_lines: List[str] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if re.match(r"^(?:[-*]|[0-9]+[.)])\s+", line):
            line = re.sub(r"^(?:[-*]|[0-9]+[.)])\s+", "", line, count=1).strip()
        if line:
            kept_lines.append(line)
    if not kept_lines:
        return []

    merged = " ".join(kept_lines).strip()
    if not merged:
        return []

    raw_sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*", merged) if s.strip()]
    return raw_sentences or [merged]


def _count_proposition_content_terms(sentence: str) -> int:
    tokens = []
    for token in _PROPOSITION_TOKEN_PATTERN.findall(sentence or ""):
        normalized = token.strip().lower()
        if normalized and normalized not in _PROPOSITION_STOP_TOKENS:
            tokens.append(normalized)
    return len(set(tokens))


def _classify_proposition_sentence(sentence: str) -> str:
    normalized = re.sub(r"\s+", "", str(sentence or ""))
    if not normalized:
        return "skip"

    length = len(normalized)
    concrete_signal = bool(_PROPOSITION_CONCRETE_SIGNAL_PATTERN.search(normalized))
    low_signal = bool(_PROPOSITION_LOW_SIGNAL_PATTERN.search(normalized))
    content_terms = _count_proposition_content_terms(normalized)

    if concrete_signal:
        return "informative"
    if content_terms >= 3 and length >= 22:
        return "informative"
    if low_signal and content_terms <= 2:
        return "low"
    if content_terms <= 1 and length < 30:
        return "low"
    if length <= 10:
        return "low"
    if content_terms >= 2 and length >= 16:
        return "medium"
    return "low"


def _analyze_proposition_density(text: str) -> Dict[str, Any]:
    sentences = _extract_proposition_sentences(text)
    if not sentences:
        return {
            "sentence_count": 0,
            "informative_count": 0,
            "medium_count": 0,
            "low_info_count": 0,
            "informative_ratio": 0.0,
            "low_info_ratio": 0.0,
            "low_info_examples": [],
        }

    informative_count = 0
    medium_count = 0
    low_info_count = 0
    low_info_examples: List[str] = []
    for sentence in sentences:
        label = _classify_proposition_sentence(sentence)
        if label == "informative":
            informative_count += 1
        elif label == "medium":
            medium_count += 1
        elif label == "low":
            low_info_count += 1
            if len(low_info_examples) < 4:
                low_info_examples.append(sentence[:96])

    sentence_count = len(sentences)
    return {
        "sentence_count": sentence_count,
        "informative_count": informative_count,
        "medium_count": medium_count,
        "low_info_count": low_info_count,
        "informative_ratio": _safe_round_float(informative_count / max(1, sentence_count), 4, 0.0),
        "low_info_ratio": _safe_round_float(low_info_count / max(1, sentence_count), 4, 0.0),
        "low_info_examples": low_info_examples,
    }


def build_output_guard_inputs(
    result: Dict[str, Any],
    *,
    pipeline_check: Dict[str, Any] | None = None,
    hard_soft_eval: Dict[str, Any] | None = None,
    contextual_naturalness_report: Dict[str, Any] | None = None,
    final_quality_eval: Dict[str, Any] | None = None,
    proposition_density: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    pipeline = _to_plain_dict(pipeline_check if isinstance(pipeline_check, dict) else result.get("pipeline_check"))
    native = _to_plain_dict(pipeline.get("output_guard_inputs"))
    if native:
        return native
    resolved_proposition_density = _to_plain_dict(proposition_density)
    if not resolved_proposition_density:
        resolved_proposition_density = _analyze_proposition_density(
            _build_proposition_density_target_text(result)
        )
    return {
        "hard_soft_eval": _to_plain_dict(hard_soft_eval) or _to_plain_dict(pipeline.get("hard_soft_eval")),
        "contextual_naturalness_report": _to_plain_dict(contextual_naturalness_report)
        or _to_plain_dict(pipeline.get("contextual_naturalness_report")),
        "proposition_density": resolved_proposition_density,
        "contract_alignment": _to_plain_dict(pipeline.get("contract_alignment")),
        "final_quality_eval": _to_plain_dict(final_quality_eval) or _to_plain_dict(pipeline.get("final_quality_eval")),
    }


def _build_failed_parameters_from_guard_inputs(
    result: Dict[str, Any],
    guard_inputs: Dict[str, Any],
) -> Dict[str, Any]:
    hard_soft_eval = _to_plain_dict(guard_inputs.get("hard_soft_eval"))
    naturalness = _to_plain_dict(guard_inputs.get("contextual_naturalness_report"))
    proposition_density = _to_plain_dict(guard_inputs.get("proposition_density"))
    contract_alignment = _to_plain_dict(guard_inputs.get("contract_alignment"))
    final_quality_eval = _to_plain_dict(guard_inputs.get("final_quality_eval"))
    hard_soft_metrics = _to_plain_dict(hard_soft_eval.get("metrics"))
    instructional_fragment_count = max(
        int(naturalness.get("instructional_fragment_count", 0) or 0),
        int(hard_soft_metrics.get("instructional_fragment_count", 0) or 0),
    )
    return {
        "has_failure": not bool(result.get("success", True)),
        "runtime_reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or "OK"),
        "runtime_error_class": str(result.get("runtime_error_class") or ""),
        "retry_failures": [],
        "hard_soft_eval": hard_soft_eval,
        "repair_only_report": {},
        "contextual_naturalness_report": naturalness,
        "proposition_density": proposition_density,
        "instructional_fragment_count": instructional_fragment_count,
        "output_guard": _to_plain_dict(extract_existing_output_guard(result)),
        "contract_alignment": contract_alignment,
        "quality_mode_resolution": {},
        "fingerprint_phase": {},
        "final_quality_eval": final_quality_eval,
    }


def scan_instructional_fragments(
    *texts: str,
    references: List[str] | None = None,
    max_hits: int = 5,
) -> List[str]:
    hits: List[str] = []
    refs = list(references or [])
    for text in texts:
        source = str(text or "")
        if not source:
            continue
        remain = max(0, max_hits - len(hits))
        if remain <= 0:
            break
        hits.extend(
            detect_prompt_echo_sentences(
                source,
                references=refs,
                max_hits=remain,
                reference_coverage=0.8,
            )
        )
        if len(hits) >= max_hits:
            return hits[:max_hits]
    return hits


def _prompt_echo_scan_texts(result: Dict[str, Any], *, article_type_key: str) -> List[str]:
    texts: List[str] = []
    title = str(result.get("title", "") or "")
    lead = str(result.get("lead", "") or "")
    body = str(result.get("body", "") or "")
    if article_type_key != "announcement" and title:
        texts.append(title)
    if lead:
        texts.append(lead)
    if body:
        texts.append(body)
    return texts


def _resolve_prompt_echo_user_prompt(result: Dict[str, Any], input_contract: Dict[str, Any]) -> str:
    return str(
        result.get("user_prompt")
        or result.get("prompt_raw")
        or input_contract.get("prompt_raw")
        or input_contract.get("topic")
        or ""
    ).strip()


def extract_existing_output_guard(result: Dict[str, Any]) -> Dict[str, Any]:
    direct_guard = _to_plain_dict(result.get("output_guard"))
    if direct_guard:
        return direct_guard
    pipeline = _to_plain_dict(result.get("pipeline_check"))
    return _to_plain_dict(pipeline.get("output_guard"))


def attach_output_guard_to_result(result: Dict[str, Any], guard: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(result or {})
    normalized_guard = _to_plain_dict(guard)
    pipeline_check = _to_plain_dict(enriched.get("pipeline_check"))
    pipeline_check["output_guard"] = normalized_guard
    enriched["pipeline_check"] = pipeline_check
    enriched["output_guard"] = normalized_guard
    return enriched


def _all_fingerprint_warning_codes(items: List[Any]) -> bool:
    codes = [str(item or "").strip() for item in items if str(item or "").strip()]
    return bool(codes) and all(code.startswith("fingerprint:") for code in codes)


def _has_non_fingerprint_warning(items: List[Any]) -> bool:
    return any(
        str(item or "").strip() and not str(item or "").strip().startswith("fingerprint:")
        for item in items
    )


def _has_non_fingerprint_quality_hard_reason(items: List[Any]) -> bool:
    return any(
        str(item or "").strip()
        and str(item or "").strip() != "SYS_QUALITY_WARNINGS_UNRESOLVED"
        and not str(item or "").strip().startswith("fingerprint:")
        for item in items
    )


def is_fingerprint_only_warning_observable(
    result: Dict[str, Any],
    guard: Dict[str, Any],
) -> bool:
    """Return true when strict UI fail-close may be shown as warning-only.

    This does not alter fingerprint thresholds. It only recognizes the narrow
    case where final guard failure is fingerprint-only and source/contract
    grounding already passed the existing hard checks.
    """
    normalized_guard = _to_plain_dict(guard)
    if not bool(normalized_guard.get("blocked", False)):
        return False
    if str(normalized_guard.get("reason_code") or "") != "SYS_QUALITY_WARNINGS_UNRESOLVED":
        return False
    if not bool(normalized_guard.get("warning_fail_closed", False)):
        return False
    if _to_plain_list(normalized_guard.get("hard_reasons")):
        return False
    if _to_plain_list(normalized_guard.get("manual_instructional_hits")):
        return False
    if _to_plain_list(normalized_guard.get("needs_input_items")):
        return False

    reasons = _to_plain_list(normalized_guard.get("reasons"))
    soft_warnings = _to_plain_list(normalized_guard.get("soft_warnings"))
    if not _all_fingerprint_warning_codes(reasons):
        return False
    if not _all_fingerprint_warning_codes(soft_warnings):
        return False

    pipeline = _to_plain_dict(result.get("pipeline_check"))
    failed_parameters = _to_plain_dict(normalized_guard.get("failed_parameters"))
    final_quality_eval = (
        _to_plain_dict(failed_parameters.get("final_quality_eval"))
        or _to_plain_dict(pipeline.get("final_quality_eval"))
    )
    final_quality_hard_reasons = _to_plain_list(final_quality_eval.get("hard_fail_reasons"))
    if _has_non_fingerprint_quality_hard_reason(final_quality_hard_reasons):
        return False
    if int(final_quality_eval.get("instructional_fragment_count") or 0) > 0:
        return False
    if int(final_quality_eval.get("semantic_issue_count") or 0) > 0:
        return False
    if _has_non_fingerprint_warning(_to_plain_list(final_quality_eval.get("soft_warnings"))):
        return False

    hard_soft_eval = (
        _to_plain_dict(failed_parameters.get("hard_soft_eval"))
        or _to_plain_dict(pipeline.get("hard_soft_eval"))
    )
    hard_soft_hard_reasons = _to_plain_list(hard_soft_eval.get("hard_fail_reasons"))
    if _has_non_fingerprint_quality_hard_reason(hard_soft_hard_reasons):
        return False
    if _has_non_fingerprint_warning(_to_plain_list(hard_soft_eval.get("soft_warnings"))):
        return False
    hard_soft_metrics = _to_plain_dict(hard_soft_eval.get("metrics"))
    if int(hard_soft_metrics.get("instructional_fragment_count") or 0) > 0:
        return False

    naturalness = (
        _to_plain_dict(failed_parameters.get("contextual_naturalness_report"))
        or _to_plain_dict(pipeline.get("contextual_naturalness_report"))
    )
    if int(naturalness.get("instructional_fragment_count") or 0) > 0:
        return False
    if int(naturalness.get("semantic_issue_count") or 0) > 0:
        return False
    if int(naturalness.get("issue_count") or 0) > 0:
        return False

    contract_alignment = (
        _to_plain_dict(failed_parameters.get("contract_alignment"))
        or _to_plain_dict(pipeline.get("contract_alignment"))
    )
    if bool(contract_alignment.get("category_mismatch_detected", False)):
        return False
    forbidden_topic_hits = _to_plain_list(contract_alignment.get("forbidden_topic_hits"))
    forbidden_topic_hit_count = int(contract_alignment.get("forbidden_topic_hit_count", 0) or 0)
    if forbidden_topic_hits or forbidden_topic_hit_count > 0:
        return False
    if int(contract_alignment.get("section_contract_issue_count") or 0) > 0:
        return False
    if _safe_round_float(contract_alignment.get("speaker_consistency_score"), 4, 1.0) < _OUTPUT_GUARD_MIN_SPEAKER_CONSISTENCY:
        return False
    if _safe_round_float(contract_alignment.get("pronoun_consistency_score"), 4, 1.0) < _OUTPUT_GUARD_MIN_PRONOUN_CONSISTENCY:
        return False
    if _safe_round_float(contract_alignment.get("relationship_consistency_score"), 4, 1.0) < _OUTPUT_GUARD_MIN_RELATIONSHIP_CONSISTENCY:
        return False

    must_cover_count = int(contract_alignment.get("must_cover_count", 0) or 0)
    must_cover_reflection_rate = _safe_round_float(
        contract_alignment.get("must_cover_reflection_rate"),
        4,
        0.0,
    )
    if must_cover_count < 2 or must_cover_reflection_rate < _OUTPUT_GUARD_MIN_MUST_COVER_REFLECTION:
        return False

    input_contract = _to_plain_dict(pipeline.get("input_contract"))
    source_grounding_required = bool(input_contract.get("source_grounding_required"))
    source_trace_coverage = _safe_round_float(
        contract_alignment.get("source_trace_coverage"),
        4,
        0.0,
    )
    if not source_grounding_required:
        return False
    if source_trace_coverage < _OUTPUT_GUARD_MIN_SOURCE_TRACE_COVERAGE_FOR_WARNING_ONLY:
        return False

    return True


def demote_fingerprint_only_output_guard_to_warning(guard: Dict[str, Any]) -> Dict[str, Any]:
    normalized_guard = _to_plain_dict(guard)
    demoted = dict(normalized_guard)
    demoted["blocked"] = False
    demoted["reasons"] = []
    demoted["error_class"] = ""
    demoted["reason_code"] = ""
    demoted["warning_fail_closed"] = False
    demoted["fingerprint_only_warning_observable"] = True
    demoted["demoted_from_warning_fail_closed"] = True
    return demoted


def evaluate_generation_output_guard(result: Dict[str, Any]) -> Dict[str, Any]:
    pipeline = _to_plain_dict(result.get("pipeline_check"))
    guard_inputs = build_output_guard_inputs(result, pipeline_check=pipeline)
    failed_parameters = _build_failed_parameters_from_guard_inputs(result, guard_inputs)
    hard_soft_eval = _to_plain_dict(guard_inputs.get("hard_soft_eval"))
    naturalness = _to_plain_dict(guard_inputs.get("contextual_naturalness_report"))
    proposition_density = _to_plain_dict(guard_inputs.get("proposition_density"))
    contract_alignment = _to_plain_dict(guard_inputs.get("contract_alignment"))
    input_contract = _to_plain_dict(pipeline.get("input_contract"))
    strict_saas_mode = normalize_strict_saas_mode(
        input_contract.get("strict_saas_mode"),
    )
    article_type_key = str(
        input_contract.get("article_type")
        or result.get("article_type")
        or ""
    ).strip().lower()
    semantic_article_key = str(input_contract.get("semantic_article_key") or "").strip().lower()
    source_mode = str(input_contract.get("source_mode") or "").strip().lower()
    source_trace_policy = str(input_contract.get("source_trace_policy") or "").strip().lower()
    source_trace = [
        _to_plain_dict(item)
        for item in _to_plain_list(input_contract.get("source_trace"))
        if _to_plain_dict(item)
    ]

    issue_count = int(naturalness.get("issue_count", 0) or 0)
    semantic_issue_count = int(naturalness.get("semantic_issue_count", 0) or 0)
    instructional_fragment_count = int(
        failed_parameters.get("instructional_fragment_count", 0) or 0
    )
    prompt_echo_references = build_prompt_echo_references(
        user_prompt=_resolve_prompt_echo_user_prompt(result, input_contract),
        include_must_cover=False,
    )
    manual_instructional_hits = scan_instructional_fragments(
        *_prompt_echo_scan_texts(result, article_type_key=article_type_key),
        references=prompt_echo_references,
    )

    needs_input_items: List[Dict[str, Any]] = []

    hard_reasons: List[str] = []
    if bool(result.get("hard_failed", False)):
        hard_reasons.append("result_hard_failed")
    for reason in _to_plain_list(result.get("hard_fail_reasons")):
        reason_text = str(reason or "").strip()
        if reason_text:
            hard_reasons.append(f"result_hard_fail_reason={reason_text}")
    if instructional_fragment_count > 0:
        hard_reasons.append(f"instructional_fragment_count={instructional_fragment_count}")
    if manual_instructional_hits:
        hard_reasons.append(f"manual_instructional_hits={len(manual_instructional_hits)}")
    if source_mode == "web":
        if (
            article_type_key in _WEB_SOURCE_MODE_BLOCKED_ARTICLE_TYPES
            or semantic_article_key in _WEB_SOURCE_MODE_BLOCKED_SEMANTIC_KEYS
        ):
            hard_reasons.append("web_source_mode_blocked_category")
        valid_trace_count = 0
        trace_publishers: set[str] = set()
        missing_trace_fields = False
        for item in source_trace:
            missing_fields = [
                field
                for field in ("query", "url", "publisher", "exact_date", "excerpt")
                if not str(item.get(field) or "").strip()
            ]
            if missing_fields:
                missing_trace_fields = True
                break
            valid_trace_count += 1
            trace_publishers.add(str(item.get("publisher") or "").strip())
        if source_trace_policy == "web_trace_required":
            if missing_trace_fields:
                hard_reasons.append("web_source_trace_missing_fields")
            if valid_trace_count < 2:
                hard_reasons.append("web_source_trace_count<2")
            if len([item for item in trace_publishers if item]) < 2:
                hard_reasons.append("web_source_trace_publishers<2")

    alignment_score = _safe_round_float(contract_alignment.get("alignment_score"), 4, 0.0)
    must_cover_count = int(contract_alignment.get("must_cover_count", 0) or 0)
    must_cover_reflection_rate = _safe_round_float(
        contract_alignment.get("must_cover_reflection_rate"),
        4,
        1.0,
    )
    prompt_anchor_coverage = _safe_round_float(
        contract_alignment.get("prompt_anchor_coverage"),
        4,
        1.0,
    )
    anchor_term_coverage = _safe_round_float(
        contract_alignment.get("anchor_term_coverage"),
        4,
        1.0,
    )
    section_focus_coverage = _safe_round_float(
        contract_alignment.get("section_focus_coverage"),
        4,
        1.0,
    )
    section_focus_total = int(contract_alignment.get("section_focus_total", 0) or 0)
    anchor_terms = _to_plain_list(contract_alignment.get("anchor_terms"))
    forbidden_topic_hits = _to_plain_list(contract_alignment.get("forbidden_topic_hits"))
    forbidden_topic_hit_count = int(contract_alignment.get("forbidden_topic_hit_count", 0) or 0)
    if not forbidden_topic_hit_count and forbidden_topic_hits:
        forbidden_topic_hit_count = len(forbidden_topic_hits)
    default_speaker_score = 1.0 if str(
        contract_alignment.get("speaker_profile")
        or input_contract.get("speaker_profile")
        or ""
    ).strip() else 0.0
    speaker_consistency_score = _safe_round_float(
        contract_alignment.get("speaker_consistency_score"),
        4,
        default_speaker_score,
    )
    pronoun_consistency_score = _safe_round_float(
        contract_alignment.get("pronoun_consistency_score"),
        4,
        1.0,
    )
    relationship_consistency_score = _safe_round_float(
        contract_alignment.get("relationship_consistency_score"),
        4,
        1.0,
    )
    section_contract_issue_count = int(contract_alignment.get("section_contract_issue_count", 0) or 0)
    semantic_layout = _to_plain_dict(naturalness.get("semantic_layout"))
    heading_alignment_raw = semantic_layout.get("heading_alignment_mean")
    has_heading_alignment_mean = (
        "heading_alignment_mean" in semantic_layout and heading_alignment_raw is not None
    )
    heading_alignment_mean = _safe_round_float(
        heading_alignment_raw,
        4,
        0.0,
    )
    topic_opening_ratio = _safe_round_float(
        naturalness.get("topic_opening_ratio"),
        4,
        0.0,
    )
    awkward_ending_ratio = _safe_round_float(
        naturalness.get("awkward_ending_ratio"),
        4,
        0.0,
    )
    ai_template_ending_ratio = _safe_round_float(
        naturalness.get("ai_template_ending_ratio"),
        4,
        0.0,
    )
    proposition_sentence_count = int(proposition_density.get("sentence_count", 0) or 0)
    proposition_informative_ratio = _safe_round_float(
        proposition_density.get("informative_ratio"),
        4,
        0.0,
    )
    proposition_low_info_ratio = _safe_round_float(
        proposition_density.get("low_info_ratio"),
        4,
        0.0,
    )

    if bool(contract_alignment.get("category_mismatch_detected", False)):
        hard_reasons.append("contract_alignment_category_mismatch")
    if forbidden_topic_hit_count > 0:
        hard_reasons.append(
            "contract_alignment_forbidden_topics="
            + ",".join(str(item) for item in forbidden_topic_hits[:4])
        )
    if speaker_consistency_score < _OUTPUT_GUARD_MIN_SPEAKER_CONSISTENCY:
        hard_reasons.append(
            f"contract_alignment_speaker_consistency<{_OUTPUT_GUARD_MIN_SPEAKER_CONSISTENCY:.2f}"
        )
    if pronoun_consistency_score < _OUTPUT_GUARD_MIN_PRONOUN_CONSISTENCY:
        hard_reasons.append(
            f"contract_alignment_pronoun_consistency<{_OUTPUT_GUARD_MIN_PRONOUN_CONSISTENCY:.2f}"
        )
    if relationship_consistency_score < _OUTPUT_GUARD_MIN_RELATIONSHIP_CONSISTENCY:
        hard_reasons.append(
            f"contract_alignment_relationship_consistency<{_OUTPUT_GUARD_MIN_RELATIONSHIP_CONSISTENCY:.2f}"
        )
    if section_contract_issue_count > 0:
        hard_reasons.append(f"contract_alignment_section_contract_issues={section_contract_issue_count}")

    soft_warnings: List[str] = []
    if bool(hard_soft_eval.get("hard_failed", False)):
        soft_warnings.append("hard_soft_thresholds_hard_failed")
    if issue_count > 0:
        soft_warnings.append(f"contextual_issue_count={issue_count}")
    if semantic_issue_count >= _OUTPUT_GUARD_MAX_SEMANTIC_ISSUES:
        soft_warnings.append(f"semantic_issue_count={semantic_issue_count}")
    if alignment_score < _OUTPUT_GUARD_MIN_ALIGNMENT_SCORE:
        soft_warnings.append(
            f"contract_alignment_score<{_OUTPUT_GUARD_MIN_ALIGNMENT_SCORE:.2f}"
        )
    if must_cover_count >= 2 and must_cover_reflection_rate < _OUTPUT_GUARD_MIN_MUST_COVER_REFLECTION:
        soft_warnings.append(
            f"contract_alignment_must_cover_reflection_rate<{_OUTPUT_GUARD_MIN_MUST_COVER_REFLECTION:.2f}"
        )
    if (
        anchor_terms
        and prompt_anchor_coverage < _OUTPUT_GUARD_MIN_PROMPT_ANCHOR_COVERAGE
        and anchor_term_coverage < _OUTPUT_GUARD_MIN_ANCHOR_TERM_COVERAGE
        and section_focus_coverage < 0.75
    ):
        soft_warnings.append(
            f"contract_alignment_prompt_anchor_coverage<{_OUTPUT_GUARD_MIN_PROMPT_ANCHOR_COVERAGE:.2f}"
        )
    if section_focus_total >= 3 and section_focus_coverage < _OUTPUT_GUARD_MIN_SECTION_FOCUS_COVERAGE:
        soft_warnings.append(
            f"contract_alignment_section_focus_coverage<{_OUTPUT_GUARD_MIN_SECTION_FOCUS_COVERAGE:.2f}"
        )
    if (
        has_heading_alignment_mean
        and heading_alignment_mean < _OUTPUT_GUARD_MIN_HEADING_ALIGNMENT_MEAN
    ):
        soft_warnings.append(
            f"heading_alignment_mean<{_OUTPUT_GUARD_MIN_HEADING_ALIGNMENT_MEAN:.2f}"
        )
    if (
        article_type_key == "announcement"
        and proposition_sentence_count >= _OUTPUT_GUARD_MIN_PROPOSITION_SENTENCE_COUNT
        and proposition_informative_ratio < _OUTPUT_GUARD_ANNOUNCEMENT_MIN_PROPOSITION_INFORMATIVE_RATIO
    ):
        soft_warnings.append(
            "proposition_density_informative_ratio<"
            f"{_OUTPUT_GUARD_ANNOUNCEMENT_MIN_PROPOSITION_INFORMATIVE_RATIO:.2f}"
        )
    if (
        article_type_key == "announcement"
        and proposition_sentence_count >= _OUTPUT_GUARD_MIN_PROPOSITION_SENTENCE_COUNT
        and proposition_low_info_ratio > _OUTPUT_GUARD_ANNOUNCEMENT_MAX_PROPOSITION_LOW_INFO_RATIO
    ):
        soft_warnings.append(
            "proposition_density_low_info_ratio>"
            f"{_OUTPUT_GUARD_ANNOUNCEMENT_MAX_PROPOSITION_LOW_INFO_RATIO:.2f}"
        )
    if (
        proposition_sentence_count >= 6
        and proposition_informative_ratio < _OUTPUT_GUARD_SOFT_MIN_PROPOSITION_INFORMATIVE_RATIO
    ):
        soft_warnings.append(
            "proposition_density_informative_ratio<"
            f"{_OUTPUT_GUARD_SOFT_MIN_PROPOSITION_INFORMATIVE_RATIO:.2f}"
        )
    if (
        proposition_sentence_count >= 6
        and proposition_low_info_ratio > _OUTPUT_GUARD_SOFT_MAX_PROPOSITION_LOW_INFO_RATIO
    ):
        soft_warnings.append(
            "proposition_density_low_info_ratio>"
            f"{_OUTPUT_GUARD_SOFT_MAX_PROPOSITION_LOW_INFO_RATIO:.2f}"
        )
    if topic_opening_ratio > _OUTPUT_GUARD_SOFT_MAX_TOPIC_OPENING_RATIO:
        soft_warnings.append(
            f"topic_opening_ratio>{_OUTPUT_GUARD_SOFT_MAX_TOPIC_OPENING_RATIO:.2f}"
        )
    if awkward_ending_ratio > _OUTPUT_GUARD_SOFT_MAX_AWKWARD_ENDING_RATIO:
        soft_warnings.append(
            f"awkward_ending_ratio>{_OUTPUT_GUARD_SOFT_MAX_AWKWARD_ENDING_RATIO:.2f}"
        )
    if ai_template_ending_ratio > _OUTPUT_GUARD_SOFT_MAX_AI_TEMPLATE_ENDING_RATIO:
        soft_warnings.append(
            f"ai_template_ending_ratio>{_OUTPUT_GUARD_SOFT_MAX_AI_TEMPLATE_ENDING_RATIO:.2f}"
        )
    for item in list(hard_soft_eval.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)

    blocked = False
    error_class: str | None = None
    reason_code: str | None = None
    blocking_reasons: List[str] = []

    if hard_reasons:
        blocked = True
        blocking_reasons = list(hard_reasons)
        if manual_instructional_hits:
            error_class = "policy"
            reason_code = "POL_PROMPT_ECHO"
        elif any(str(reason).startswith("web_source_mode_blocked_category") for reason in hard_reasons):
            error_class = "user_input"
            reason_code = "POL_WEB_SOURCE_MODE_BLOCKED"
        elif any(str(reason).startswith("web_source_trace_") for reason in hard_reasons):
            error_class = "user_input"
            reason_code = "POL_WEB_SOURCE_TRACE_REQUIRED"
        elif instructional_fragment_count > 0:
            error_class = "policy"
            reason_code = "POL_PROMPT_INJECTION"
        elif any("contract_alignment_forbidden_topics=" in str(reason) for reason in hard_reasons):
            error_class = "system"
            reason_code = "SYS_FORBIDDEN_TOPIC_DRIFT"
        elif any(
            any(
                marker in str(reason)
                for marker in (
                    "contract_alignment_speaker_consistency<",
                    "contract_alignment_pronoun_consistency<",
                    "contract_alignment_relationship_consistency<",
                    "contract_alignment_section_contract_issues=",
                )
            )
            for reason in hard_reasons
        ):
            error_class = "system"
            reason_code = "SYS_SPEAKER_CONTRACT_MISMATCH"
        elif any(str(reason).startswith("proposition_density_") for reason in hard_reasons):
            error_class = "system"
            reason_code = "SYS_LOW_PROPOSITION_DENSITY"
        elif any(str(reason).startswith("contract_alignment_") for reason in hard_reasons):
            error_class = "system"
            reason_code = "SYS_CONTRACT_ALIGNMENT_MISMATCH"
        elif any("legal" in str(reason).lower() for reason in hard_reasons):
            error_class = "policy"
            reason_code = "POL_LEGAL_HARD_FAIL"
        else:
            error_class = "system"
            reason_code = "SYS_QUALITY_GATE_HARD_FAIL"
    elif strict_saas_mode in {"medium", "large"} and soft_warnings:
        blocked = True
        blocking_reasons = list(soft_warnings)
        error_class = "system"
        reason_code = "SYS_QUALITY_WARNINGS_UNRESOLVED"

    return {
        "blocked": blocked,
        "reasons": blocking_reasons,
        "hard_reasons": hard_reasons,
        "hard_reason_count": len(hard_reasons),
        "soft_warnings": soft_warnings,
        "soft_warning_count": len(soft_warnings),
        "strict_saas_mode": strict_saas_mode,
        "warning_fail_closed": bool(
            not hard_reasons
            and strict_saas_mode in {"medium", "large"}
            and soft_warnings
        ),
        "manual_instructional_hits": manual_instructional_hits,
        "prompt_echo_references": prompt_echo_references,
        "failed_parameters": failed_parameters,
        "issue_count": issue_count,
        "semantic_issue_count": semantic_issue_count,
        "instructional_fragment_count": instructional_fragment_count,
        "proposition_density": proposition_density,
        "error_class": error_class,
        "reason_code": reason_code,
        "needs_input_items": needs_input_items,
    }


def apply_generation_output_guard(result: Dict[str, Any]) -> Dict[str, Any]:
    guard = extract_existing_output_guard(result) or evaluate_generation_output_guard(result)
    enriched = attach_output_guard_to_result(result, guard)
    if not bool(guard.get("blocked", False)):
        return enriched
    reason_code = str(
        guard.get("reason_code")
        or enriched.get("runtime_reason_code")
        or enriched.get("reason_code")
        or "SYS_QUALITY_GATE_HARD_FAIL"
    )
    error_class = str(
        guard.get("error_class")
        or enriched.get("runtime_error_class")
        or "system"
    )
    enriched["success"] = False
    enriched["reason_code"] = reason_code
    enriched["runtime_reason_code"] = reason_code
    enriched["runtime_error_class"] = error_class
    if guard.get("needs_input_items") and not enriched.get("needs_input_items"):
        enriched["needs_input_items"] = _to_plain_list(guard.get("needs_input_items"))
    return enriched


def _extract_guard_forbidden_topics(reasons: List[Any]) -> List[str]:
    topics: List[str] = []
    for reason in reasons:
        text = str(reason or "")
        marker = "contract_alignment_forbidden_topics="
        if marker not in text:
            continue
        payload = text.split(marker, 1)[1].strip()
        for token in payload.split(","):
            normalized = str(token or "").strip()
            if normalized and normalized not in topics:
                topics.append(normalized)
    return topics[:8]


def _resolve_guard_retry_category(article_type_key: str, writing_focus_key: str) -> str:
    article_key = str(article_type_key or "").strip().lower()
    focus_key = str(writing_focus_key or "").strip().lower()
    if article_key in _BRANDING_ARTICLE_TYPES:
        return "branding"
    if article_key in _COMPANY_INTRO_ARTICLE_TYPES:
        return "company_introduction"
    if article_key == "ai" or focus_key in _AI_EXPLANATORY_FOCUS_KEYS:
        return "ai_explanatory"
    return "general"


def is_guard_auto_repair_candidate(guard: Dict[str, Any]) -> bool:
    if not bool(guard.get("blocked", False)):
        return False
    if str(guard.get("error_class") or "") != "system":
        return False
    return str(guard.get("reason_code") or "") in {
        "SYS_FORBIDDEN_TOPIC_DRIFT",
        "SYS_SPEAKER_CONTRACT_MISMATCH",
        "SYS_CONTRACT_ALIGNMENT_MISMATCH",
        "SYS_LOW_PROPOSITION_DENSITY",
        "SYS_QUALITY_GATE_HARD_FAIL",
    }


def build_guard_retry_prompt(
    base_prompt: str,
    guard: Dict[str, Any],
    *,
    article_type_key: str = "",
    writing_focus_key: str = "",
) -> str:
    raw_prompt = str(base_prompt or "").strip()
    reasons = guard.get("reasons", [])
    if not isinstance(reasons, list):
        reasons = []
    forbidden_topics = _extract_guard_forbidden_topics(reasons)
    reason_code = str(guard.get("reason_code") or "")
    retry_category = _resolve_guard_retry_category(article_type_key, writing_focus_key)
    category_hints = _RETRY_PROMPT_CATEGORY_HINTS.get(
        retry_category,
        _RETRY_PROMPT_CATEGORY_HINTS["general"],
    )
    instructions: List[str] = [
        "直前生成では品質ガードに抵触しました。次は必ず以下を守ってください。",
        "- ユーザープロンプトの主題から逸脱しない",
        "- 話者・読者・一人称を本文全体で一貫させる",
        f"- 再試行カテゴリ: {retry_category}",
    ]
    instructions.extend(category_hints)
    if forbidden_topics:
        instructions.append("- 禁止話題: " + "、".join(forbidden_topics))
    if reason_code == "SYS_SPEAKER_CONTRACT_MISMATCH":
        instructions.append("- 話者プロファイルで指定した立場を各見出しで維持する")
    elif reason_code == "SYS_CONTRACT_ALIGNMENT_MISMATCH":
        instructions.append("- 各見出しでユーザープロンプトの主題語を1つ以上扱う")
    elif reason_code == "SYS_LOW_PROPOSITION_DENSITY":
        instructions.append("- 各見出しで「変更点・対象・時期・影響」のうち2要素以上を具体文で示す")
        instructions.append("- 「重要です」「必要です」など抽象結論だけの文を連続させない")
    if reason_code:
        instructions.append(f"- 直前 reason_code: {reason_code}")
    if reasons:
        instructions.append("- 直前の主要指摘:")
        instructions.extend([f"  - {str(item)}" for item in reasons[:3]])
    hint_block = "\n".join(instructions)
    if raw_prompt:
        return f"{raw_prompt}\n\n【品質ガード再試行メモ】\n{hint_block}"
    return f"【品質ガード再試行メモ】\n{hint_block}"
