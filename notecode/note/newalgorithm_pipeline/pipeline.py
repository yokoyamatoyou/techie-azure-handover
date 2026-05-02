"""Compatibility wrapper for the simplified single-pass note pipeline."""
from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any, Dict, Mapping, Sequence

from note.input_contract_v1 import InputContractValidationError
from note.newalgorithm_pipeline import error_codes
from note.newalgorithm_pipeline.dedupe_adapter import run_semantic_dedupe
from note.newalgorithm_pipeline.discourse_planner import build_discourse_plan
from note.newalgorithm_pipeline.editor_guard import apply_minimal_editor_guard
from note.newalgorithm_pipeline.input_contract import (
    PromptInjectionBlockedError,
    resolve_input_contract,
    to_input_error,
)
from note.newalgorithm_pipeline.legal_postcheck import run_legal_postcheck
from note.newalgorithm_pipeline.output_formatter import format_output, normalize_output_body
from note.newalgorithm_pipeline.quality_observability_mixin import QualityObservabilityMixin
from note.newalgorithm_pipeline.section_generator import SectionGenerationRuntimeError, generate_sections
from note.prompt_echo_detector import build_prompt_echo_references, detect_prompt_echo_sentences
from note.simple_note_pipeline.postprocess import parse_tagged_output
from note.newalgorithm_pipeline.telemetry_writer import append_audit_record, build_pipeline_check
from note.simple_note_pipeline.pipeline import MinimalPipeline as _RuntimeMinimalPipeline, PipelineRuntimeError


_ENDING_HINT_BY_ARTICLE_TYPE = {
    "announcement": "notice_formal",
    "branding": "brand_narrative_mix",
    "case_study": "practical_case_mix",
    "comparative_review": "comparison_formal_mix",
    "daily_story": "reflective_mix",
    "industry_analysis": "analytic_formal_mix",
    "explanatory_article": "explanatory_mix",
}
_TAG_BLOCK_RE = re.compile(r"\[(?:TITLE|LEAD|BODY|HASHTAGS)\]", re.IGNORECASE)
_PROMPT_CONTROL_TAG_RE = re.compile(r"\[(?:ROLE|ISSUES|SOURCE)\]", re.IGNORECASE)
_BRIDGE_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")
_GENERIC_COMPAT_TITLE = "互換生成タイトル"
_STRICT_LLM_REQUIRED_MODES = {"medium", "high"}
_ANNOUNCEMENT_DENSE_HIERARCHICAL_EXPERIMENT = "announcement_dense_hierarchical_v1"
_PLANNING_OPT_IN_EXPERIMENT = "planning_opt_in_v1"
_SECTION_HEADING_BY_TYPE = {
    "case_study": "どの条件なら再現できるか",
    "comparative_review": "結論とおすすめの分け方",
}
_CASE_STUDY_RESULT_HEADING = "結果として何が変わったか"
_CASE_STUDY_CONDITION_HEADING = "どの条件なら再現できるか"
_CASE_STUDY_CHANGE_HEADING_RE = re.compile(r"(結果|変化|改善後|見直し後)")
_CASE_STUDY_CONDITION_HEADING_RE = re.compile(r"(条件|再現|前提|限界)")
_CASE_STUDY_PROBLEM_HEADING_RE = re.compile(r"(課題|迷い|背景|導入前|改善前|見えていた|止ま|つまず)")
_CASE_STUDY_CONDITION_ENUMERATION_STUB_RE = re.compile(r"(三つあります|三つ目)")
_CASE_STUDY_CONDITION_SENTENCE_RE = re.compile(
    r"(再現条件|条件なら|条件として|条件は|前提として|前提を|前提が|ただし|限界|例外|場合|分岐|退避|必要があります|必要です)"
)
_CASE_STUDY_CHANGE_SENTENCE_RE = re.compile(
    r"(減っ|増え|短くな|早くな|小さくな|そろっ|改善し|改善につなが|分かっ|でき|見え|安定し|止まりにく|迷いにく|判断しやす|負担が減)"
)
_CASE_STUDY_CHANGE_FALLBACK_CLAUSE_RE = re.compile(r"(改善後|見直し後|整理した|組み替え|分け|案内し|変え|直し)")
_CASE_STUDY_META_SENTENCE_RE = re.compile(
    r"(成功談として|として見るほうが|と感じています|実務には近い|まとめるより)"
)
_CASE_STUDY_DEFAULT_CHANGE_SENTENCE = "初回返信までの時間が短くなり、差し戻し理由もそろってきました。"
_ANNOUNCEMENT_THIN_BODY_CHAR_LIMIT = 620
_CASE_STUDY_THIN_BODY_CHAR_LIMIT = 700
_PRODUCT_INTRO_THIN_BODY_CHAR_LIMIT = 780
_ANNOUNCEMENT_TARGET_HEADING_RE = re.compile(r"(対象|変更内容)")
_ANNOUNCEMENT_TIME_HEADING_RE = re.compile(r"(対象|時期)")
_ANNOUNCEMENT_ROLE_PROMPT_ECHO_RE = re.compile(
    r"(?:対象者は|対象は)[^。]{0,120}(?:編集担当者|承認者|公開申請|承認を行う)",
)
_ANNOUNCEMENT_DATETIME_RE = re.compile(r"20\d{2}年\d{1,2}月\d{1,2}日(?:\d{1,2}時(?:\d{1,2}分)?)?")
_ANNOUNCEMENT_PREPARATION_TIME_RE = re.compile(r"実施時期は[^。]*(?:再設定|通知先|確認|事前準備)")
_COMPANY_INTRO_HISTORY_MARKERS = (
    "沿革",
    "歴史",
    "創業",
    "創立",
    "歩み",
    "年表",
    "/history",
)
_COMPANY_INTRO_OVERVIEW_MARKERS = (
    "会社概要",
    "会社情報",
    "企業情報",
    "会社の輪郭",
    "何をしている会社",
    "事業内容",
    "どんな事業",
    "提供する",
    "提供している",
    "支援する会社",
    "主力",
    "company-profile",
)
_COMPANY_INTRO_STRENGTH_MARKERS = (
    "強み",
    "特徴",
    "選ばれる理由",
    "支えている強み",
    "導入支援",
    "支援方針",
    "方針",
    "姿勢",
    "教育導線",
    "担当者導線",
    "問い合わせ整理",
    "運用ルール",
    "faq",
)
_COMPARATIVE_CLOSING_HEADING = "結論とおすすめの分け方"
_CROSS_DEPARTMENT_PROMPT_ECHO_RE = re.compile(
    r"複数部門で記事作成を回す(?:なら|場合)[^。]{0,100}(?:承認フロー|責任分担|責任の置き方|担当責任)",
)
_CROSS_DEPARTMENT_AXIS_LABELS = {
    "approval_flow": "承認フロー",
    "ownership": "責任の置き方",
    "auditability": "監査のしやすさ",
    "承認フロー": "承認フロー",
    "責任分担": "責任の置き方",
    "責任の置き方": "責任の置き方",
    "担当責任": "責任の置き方",
    "担当責任の置き方": "責任の置き方",
    "監査のしやすさ": "監査のしやすさ",
}


class _CompatibilityLLM:
    def __init__(self) -> None:
        self._meta = {
            "primary_model": "offline_deterministic",
            "selected_model": "offline_deterministic",
            "base_model": "offline_deterministic",
            "model_source": "deterministic_fallback",
            "task_type": "section",
        }

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 0,
        task_type: str = "",
        article_type: str = "",
        verbosity: str = "",
        **_: Any,
    ) -> str:
        self._meta.update(
            {
                "task_type": task_type or "section",
                "article_type": article_type or "",
                "effective_verbosity": verbosity or "",
            }
        )
        return """[TITLE]
互換生成タイトル
[/TITLE]
[LEAD]
互換経路の動作確認用に最小本文を返します。
[/LEAD]
[BODY]
## 背景

要点を短く整理します。

## 論点

必要な項目だけを簡潔にまとめます。
[/BODY]
[HASHTAGS]
#note #互換
[/HASHTAGS]"""

    def get_last_call_metadata(self) -> dict:
        return dict(self._meta)


def _normalize_wrapped_llm_output(text: Any) -> str:
    raw = str(text or "")
    if _TAG_BLOCK_RE.search(raw):
        return raw
    compact = raw.strip()
    if not compact:
        return "[BODY]\n\n[/BODY]"
    return f"[BODY]\n{compact}\n[/BODY]"


class _MetadataCompatibleLLM:
    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._meta: Dict[str, Any] = {}

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 0,
        task_type: str = "",
        article_type: str = "",
        verbosity: str = "",
        **kwargs: Any,
    ) -> str:
        text = self._inner.generate_text(
            prompt,
            max_tokens=max_tokens,
            task_type=task_type,
            article_type=article_type,
            verbosity=verbosity,
            **kwargs,
        )
        getter = getattr(self._inner, "get_last_call_metadata", None)
        metadata = getter() if callable(getter) else {}
        if not isinstance(metadata, Mapping):
            metadata = {}
        fallback_model = str(getattr(self._inner, "model_name", "") or self._inner.__class__.__name__)
        self._meta = {
            "primary_model": str(metadata.get("primary_model") or metadata.get("selected_model") or fallback_model),
            "selected_model": str(metadata.get("selected_model") or fallback_model),
            "base_model": str(metadata.get("base_model") or metadata.get("selected_model") or fallback_model),
            "model_source": str(metadata.get("model_source") or "wrapped_llm"),
            "task_type": str(metadata.get("task_type") or task_type or "section"),
            "article_type": str(metadata.get("article_type") or article_type or ""),
            "effective_reasoning_effort": str(metadata.get("effective_reasoning_effort") or ""),
            "effective_temperature": metadata.get("effective_temperature"),
            "effective_top_p": metadata.get("effective_top_p"),
            "effective_presence_penalty": metadata.get("effective_presence_penalty"),
            "effective_frequency_penalty": metadata.get("effective_frequency_penalty"),
            "effective_verbosity": str(metadata.get("effective_verbosity") or verbosity or ""),
            "compatibility_suppressed_params": list(metadata.get("compatibility_suppressed_params") or []),
        }
        return _normalize_wrapped_llm_output(text)

    def get_last_call_metadata(self) -> dict:
        getter = getattr(self._inner, "get_last_call_metadata", None)
        metadata = getter() if callable(getter) else self._meta
        if not isinstance(metadata, Mapping):
            metadata = {}
        return dict(self._meta or metadata)


def _wrap_llm_client(llm_client: Any) -> Any:
    if llm_client is None:
        return _CompatibilityLLM()
    if callable(getattr(llm_client, "get_last_call_metadata", None)):
        return llm_client
    return _MetadataCompatibleLLM(llm_client)


def _normalize_payload(payload: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized = dict(payload or {})
    source = list(normalized.get("source") or [])
    source_inputs = list(normalized.get("source_inputs") or [])
    if source and not source_inputs:
        normalized["source_inputs"] = list(source)
    elif source_inputs and not source:
        normalized["source"] = list(source_inputs)
    prompt_raw = str(normalized.get("prompt_raw") or normalized.get("topic") or "").strip()
    if prompt_raw and not str(normalized.get("prompt_raw") or "").strip():
        normalized["prompt_raw"] = prompt_raw
    if prompt_raw and not str(normalized.get("topic") or "").strip():
        normalized["topic"] = prompt_raw
    article_type = str(normalized.get("article_type") or "").strip().lower()
    if article_type == "case_study" and not list(normalized.get("source_documents") or []):
        source_values = list(normalized.get("source_inputs") or normalized.get("source") or [])
        if source_values:
            normalized["source_documents"] = [
                {
                    "title": f"Compatibility Source {index}",
                    "locator": str(locator or "").strip(),
                    "source_type": "url" if str(locator or "").strip().lower().startswith(("http://", "https://")) else "text",
                    "content": prompt_raw or "case study の下書き用に source を補完しています。",
                }
                for index, locator in enumerate(source_values[:4], start=1)
                if str(locator or "").strip()
            ]
    return normalized


def _default_style_profile(contract: Mapping[str, Any]) -> Dict[str, Any]:
    article_type = str(contract.get("article_type") or "explanatory_article").strip().lower()
    return {
        "profile_name": f"note_4000_{article_type}",
        "linebreak_profile": "note_standard_spacing",
        "ending_distribution_hint": _ENDING_HINT_BY_ARTICLE_TYPE.get(article_type, "balanced"),
    }


def _serialize_discourse_plan(sections: Sequence[Any]) -> list[Dict[str, Any]]:
    return [{**asdict(section), "intent": str(section.intent)} for section in sections]


def _clean_bridge_text(value: Any, *, limit: int = 96) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _bridge_tokens(value: Any, *, limit: int = 4) -> list[str]:
    tokens: list[str] = []
    for token in _BRIDGE_TOKEN_RE.findall(str(value or "")):
        normalized = str(token or "").strip().lower()
        if not normalized or normalized in tokens:
            continue
        tokens.append(normalized)
        if len(tokens) >= limit:
            break
    return tokens


def _bridge_texts_related(left: Any, right: Any) -> bool:
    left_tokens = set(_bridge_tokens(left))
    right_tokens = set(_bridge_tokens(right))
    return bool(left_tokens and right_tokens and left_tokens.intersection(right_tokens))


def _bridge_anchor_for_section(section: Any) -> str:
    topic_seed = _clean_bridge_text(getattr(section, "topic_seed", "") or "", limit=48)
    heading = _clean_bridge_text(getattr(section, "heading", "") or "", limit=48)
    if len(topic_seed) >= 4 or len(_bridge_tokens(topic_seed, limit=2)) >= 2:
        return topic_seed
    must_cover_items = [
        _clean_bridge_text(item, limit=48)
        for item in list(getattr(section, "must_cover", []) or [])[:2]
        if _clean_bridge_text(item, limit=48)
    ]
    for item in must_cover_items:
        if _bridge_texts_related(item, heading) or _bridge_texts_related(item, topic_seed):
            return item
    return heading or topic_seed


def _bridge_purpose_for_section(section: Any) -> str:
    objective = _clean_bridge_text(getattr(section, "intent", "") or getattr(section, "objective", "") or "", limit=40)
    if "。" in objective:
        objective = objective.split("。", 1)[0].strip()
    return objective or "body"


def _bridge_claim_for_section(section: Any, *, seen_claims: set[str]) -> str:
    heading = _clean_bridge_text(getattr(section, "heading", "") or "", limit=48)
    topic_seed = _clean_bridge_text(getattr(section, "topic_seed", "") or "", limit=80)
    reader_question = _clean_bridge_text(getattr(section, "reader_question", "") or "", limit=80)
    source_grounding_items = list(getattr(section, "source_grounding_items", []) or [])
    must_cover_items = [
        _clean_bridge_text(item, limit=80)
        for item in list(getattr(section, "must_cover", []) or [])[:3]
        if _clean_bridge_text(item, limit=80)
    ]
    source_facts = [
        _clean_bridge_text(dict(item).get("fact_text") or "", limit=80)
        for item in source_grounding_items[:2]
        if isinstance(item, Mapping) and _clean_bridge_text(dict(item).get("fact_text") or "", limit=80)
    ]
    heading_aligned_must_cover = [
        item
        for item in must_cover_items
        if _bridge_texts_related(item, heading) or _bridge_texts_related(item, topic_seed)
    ]
    candidates = [
        *source_facts,
        *heading_aligned_must_cover,
        reader_question,
        topic_seed,
        *must_cover_items,
        heading,
    ]
    unique_candidates: list[str] = []
    for item in candidates:
        if item and item not in unique_candidates:
            unique_candidates.append(item)
    for item in unique_candidates:
        if item not in seen_claims:
            seen_claims.add(item)
            return item
    selected = unique_candidates[0] if unique_candidates else ""
    if selected:
        seen_claims.add(selected)
    return selected


def _upstream_discourse_plan_bridge_enabled(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    writing_focus = str(contract.get("writing_focus") or "").strip().lower()
    content_goal = str(contract.get("content_goal") or "").strip().lower()
    return (
        article_type == "branding"
        and semantic_key == "branding"
        and length_mode == "short"
        and writing_focus in {"", "auto", "explanation"}
        and content_goal in {"", "auto", "trust"}
    )


def _build_compact_plan_bridge_from_discourse_sections(
    contract: Mapping[str, Any],
    sections: Sequence[Any],
) -> list[Dict[str, str]]:
    if not _upstream_discourse_plan_bridge_enabled(contract):
        return []
    seen_claims: set[str] = set()
    bridged: list[Dict[str, str]] = []
    for section in list(sections)[:6]:
        heading = _clean_bridge_text(getattr(section, "heading", "") or "", limit=48)
        purpose = _bridge_purpose_for_section(section)
        claim = _bridge_claim_for_section(section, seen_claims=seen_claims)
        if not heading or not claim:
            continue
        bridged.append(
            {
                "heading": heading,
                "purpose": purpose,
                "anchor": _bridge_anchor_for_section(section) or heading,
                "claim": claim,
                "key_message": claim,
                "bridge": _clean_bridge_text(getattr(section, "bridge_hint", "") or "", limit=60),
                "do_not_cover": "",
            }
        )
    return bridged


def _normalize_body_generation_experiment(value: Any) -> str:
    return str(value or "").strip()


def _must_cover_items(contract: Mapping[str, Any]) -> list[str]:
    return [
        str(item or "").strip()
        for item in list(contract.get("must_cover") or [])
        if str(item or "").strip()
    ]


def _normalize_fact_signature(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip()


def _resolve_planning_article_type_prior(contract: Mapping[str, Any]) -> str:
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type in {"branding", "announcement"}:
        return "generic_prior"
    if article_type == "daily_story":
        return "generic_or_prompt_like_prior"
    if article_type in {"explanatory_article", "industry_analysis"}:
        return "coverage_first_prior"
    return "neutral"


def _evaluate_planning_opt_in_gate(
    contract: Mapping[str, Any],
    sections: Sequence[Any],
    *,
    requested_experiment: str,
) -> Dict[str, Any]:
    experiment = _normalize_body_generation_experiment(requested_experiment)
    requested = experiment == _PLANNING_OPT_IN_EXPERIMENT
    article_type_prior = _resolve_planning_article_type_prior(contract)
    total_sections = len(list(sections))
    grounded_sections = 0
    seen_fact_signatures: set[str] = set()
    for section in list(sections):
        section_has_source = False
        for item in list(getattr(section, "source_grounding_items", []) or []):
            fact_text = ""
            if isinstance(item, Mapping):
                fact_text = str(dict(item).get("fact_text") or "").strip()
            else:
                fact_text = str(item or "").strip()
            signature = _normalize_fact_signature(fact_text)
            if not signature:
                continue
            section_has_source = True
            seen_fact_signatures.add(signature)
        if section_has_source:
            grounded_sections += 1
    distinct_fact_clusters = len(seen_fact_signatures)
    must_cover_count = len(_must_cover_items(contract))
    grounded_section_ratio = round(grounded_sections / total_sections, 4) if total_sections else 0.0
    ordering_signal = total_sections >= 5 and must_cover_count >= 3
    no_source_standalone_ok = grounded_sections >= must_cover_count if must_cover_count else True
    source_density_ready = distinct_fact_clusters >= 3
    grounding_ready = (
        grounded_sections >= 3
        and grounded_section_ratio >= 0.5
        and no_source_standalone_ok
    )
    article_type_prior_allows_composite = article_type_prior not in {
        "generic_prior",
        "generic_or_prompt_like_prior",
    }
    composite_dense_grounding_ready = (
        article_type_prior_allows_composite
        and ordering_signal
        and total_sections >= 6
        and must_cover_count >= 3
        and distinct_fact_clusters >= 2
        and grounded_sections >= max(4, must_cover_count)
        and grounded_section_ratio >= 0.6
        and no_source_standalone_ok
    )
    enabled = False
    reason_code = "not_requested_default_generic"
    activation_path = ""
    if requested:
        if must_cover_count < 3:
            reason_code = "must_cover_insufficient"
        elif not ordering_signal:
            reason_code = "ordering_benefit_unclear"
        elif grounded_sections < 3:
            reason_code = "grounded_sections_insufficient"
        elif grounded_section_ratio < 0.5:
            reason_code = "grounded_section_ratio_insufficient"
        elif not no_source_standalone_ok:
            reason_code = "must_cover_source_coverage_insufficient"
        elif source_density_ready:
            enabled = True
            reason_code = "feature_gate_passed"
            activation_path = "strict_source_density"
        elif composite_dense_grounding_ready:
            enabled = True
            reason_code = "feature_gate_passed"
            activation_path = "dense_grounding_composite"
        else:
            reason_code = "source_fact_clusters_insufficient"
    return {
        "requested": requested,
        "requested_experiment": experiment,
        "enabled": enabled,
        "reason_code": reason_code,
        "activation_path": activation_path,
        "article_type_prior": article_type_prior,
        "distinct_fact_clusters": distinct_fact_clusters,
        "grounded_sections": grounded_sections,
        "total_sections": total_sections,
        "grounded_section_ratio": grounded_section_ratio,
        "must_cover_count": must_cover_count,
        "ordering_signal": ordering_signal,
        "no_source_standalone_ok": no_source_standalone_ok,
        "source_density_ready": source_density_ready,
        "grounding_ready": grounding_ready,
        "article_type_prior_allows_composite": article_type_prior_allows_composite,
        "composite_dense_grounding_ready": composite_dense_grounding_ready,
    }


def _matches_announcement_dense_experiment_route(contract: Mapping[str, Any]) -> bool:
    ui_journey = dict(contract.get("ui_journey") or {})
    length_mode = str(contract.get("length_mode") or contract.get("length_mode_requested") or "").strip().lower()
    return (
        str(contract.get("article_type") or "").strip().lower() == "announcement"
        and str(contract.get("semantic_article_key") or "").strip().lower() == "announcement"
        and str(contract.get("content_goal") or "").strip().lower() == "action"
        and str(contract.get("writing_focus") or "").strip().lower() == "explanation"
        and length_mode == "short"
        and str(ui_journey.get("purpose_key") or "").strip().lower() == "announce"
        and str(ui_journey.get("target_key") or "").strip().lower() == "standard"
        and len(_must_cover_items(contract)) >= 3
    )


def _resolve_section_generation_state(
    contract: Mapping[str, Any],
    sections: Sequence[Any],
    *,
    requested_experiment: str,
) -> Dict[str, Any]:
    experiment = _normalize_body_generation_experiment(requested_experiment)
    planning_gate = _evaluate_planning_opt_in_gate(
        contract,
        sections,
        requested_experiment=requested_experiment,
    )
    route_match = False
    if not experiment:
        return {}
    enabled = False
    selection_mode = ""
    reason = ""
    if experiment == _PLANNING_OPT_IN_EXPERIMENT:
        selection_mode = "planning_opt_in"
        enabled = bool(planning_gate.get("enabled"))
        route_match = enabled
        reason = str(planning_gate.get("reason_code") or "")
    else:
        route_match = _matches_announcement_dense_experiment_route(contract)
        selection_mode = "requested_experiment"
        if experiment != _ANNOUNCEMENT_DENSE_HIERARCHICAL_EXPERIMENT:
            reason = "unsupported_experiment"
        elif not route_match:
            reason = "route_mismatch"
        else:
            enabled = True
            reason = "requested_experiment"
    if not reason:
        reason = "unsupported_experiment"
    return {
        "requested": experiment,
        "enabled": enabled,
        "route_match": route_match,
        "selection_mode": selection_mode,
        "reason": reason,
        "planning_opt_in_gate": planning_gate,
    }


def _build_hierarchical_ab_summary(
    contract: Mapping[str, Any],
    sections: Sequence[Any],
    section_state: Mapping[str, Any],
    *,
    section_ledgers: Sequence[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    ledgers = [dict(item) for item in list(section_ledgers or []) if isinstance(item, Mapping)]
    final_remaining = (
        list(ledgers[-1].get("remaining_must_cover_after") or [])
        if ledgers
        else _must_cover_items(contract)
    )
    enabled = bool(section_state.get("enabled"))
    fallback_to_super = bool(section_state.get("fallback_to_super"))
    return {
        "enabled": enabled,
        "experiment": str(section_state.get("requested") or ""),
        "selection_mode": str(section_state.get("selection_mode") or ""),
        "route_match": bool(section_state.get("route_match")),
        "reason": str(section_state.get("reason") or ""),
        "generation_mode": (
            "hierarchical_sections"
            if enabled and not fallback_to_super
            else "single_pass_fallback"
            if enabled and fallback_to_super
            else "single_pass"
        ),
        "fallback_to_super": fallback_to_super,
        "fallback_reason": str(section_state.get("fallback_reason") or ""),
        "sections_total": len(list(sections)),
        "initial_must_cover": _must_cover_items(contract),
        "final_remaining_must_cover": final_remaining,
        "section_ledgers": ledgers,
    }


def _extract_runtime_check(result: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(result.get("pipeline_check") or {})


def _extract_primary_call(runtime_check: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(dict(runtime_check.get("body_generation") or {}).get("primary_call") or {})


def _build_primary_generation_summary(
    *,
    section_state: Mapping[str, Any],
    runtime_check: Mapping[str, Any],
    retries: int,
    fallback_used: bool,
) -> Dict[str, Any]:
    section_enabled = bool(section_state.get("enabled"))
    fallback_to_super = bool(section_state.get("fallback_to_super"))
    if section_enabled and not fallback_to_super:
        source = "section_first_writer"
        owner = "section_generator"
        generation_mode = "hierarchical_sections"
    elif section_enabled and fallback_to_super:
        source = "single_pass_runtime_fallback"
        owner = "simple_note_pipeline"
        generation_mode = "single_pass_fallback"
    else:
        source = "single_pass_runtime"
        owner = "simple_note_pipeline"
        generation_mode = "single_pass"
    return {
        "source": source,
        "owner": owner,
        "generation_mode": generation_mode,
        "fallback_to_super": fallback_to_super,
        "retries": int(retries or 0),
        "fallback_used": bool(fallback_used),
        "repair_applied": bool(dict(runtime_check.get("body_generation") or {}).get("repair_applied")),
    }


def _resolve_route_branch(section_state: Mapping[str, Any]) -> str:
    requested = str(section_state.get("requested") or "")
    enabled = bool(section_state.get("enabled"))
    fallback_to_super = bool(section_state.get("fallback_to_super"))
    selection_mode = str(section_state.get("selection_mode") or "")
    reason = str(section_state.get("reason") or "")
    if enabled and not fallback_to_super:
        if selection_mode == "planning_opt_in":
            return "planning_opt_in_section_path"
        if selection_mode == "requested_experiment":
            return "requested_experiment_section_path"
        if selection_mode == "promoted_route":
            return "promoted_route_section_path"
        return "section_path"
    if enabled and fallback_to_super:
        if selection_mode == "planning_opt_in":
            return "planning_opt_in_fallback_to_super"
        return "section_path_fallback_to_super"
    if requested and selection_mode == "planning_opt_in":
        return "planning_opt_in_gate_refused"
    if requested and reason == "route_mismatch":
        return "requested_experiment_route_mismatch"
    if requested and reason == "unsupported_experiment":
        return "requested_experiment_unsupported"
    return "single_pass_default"


def _resolve_style_profile_source(
    contract: Mapping[str, Any],
    style_profile: Mapping[str, Any],
) -> str:
    if not style_profile:
        return "style_profile_missing"
    default_profile = _default_style_profile(contract)
    comparable_keys = ("profile_name", "linebreak_profile", "ending_distribution_hint")
    if all(str(style_profile.get(key) or "") == str(default_profile.get(key) or "") for key in comparable_keys):
        return "newalgorithm_pipeline.default_style_profile"
    return "newalgorithm_pipeline.runtime_style_profile_override"


def _build_planned_vs_actual_heading_overlap(
    sections: Sequence[Any],
    body: str,
) -> Dict[str, Any]:
    planned_headings = [
        _normalize_heading_text(getattr(section, "heading", "") or "")
        for section in list(sections)
        if _normalize_heading_text(getattr(section, "heading", "") or "")
    ]
    actual_headings = _extract_section_headings(body)
    actual_set = set(actual_headings)
    planned_set = set(planned_headings)
    matched_headings = [heading for heading in planned_headings if heading in actual_set]
    missing_headings = [heading for heading in planned_headings if heading not in actual_set]
    extra_headings = [heading for heading in actual_headings if heading not in planned_set]
    overlap_ratio = round(len(matched_headings) / len(planned_headings), 4) if planned_headings else 0.0
    return {
        "planned_count": len(planned_headings),
        "actual_count": len(actual_headings),
        "matched_count": len(matched_headings),
        "overlap_ratio": overlap_ratio,
        "missing_headings": missing_headings[:6],
        "extra_headings": extra_headings[:6],
    }


def _compact_plan_patch_scope_allowed(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    return (
        article_type == "explanatory_article" and length_mode in {"short", "adaptive"}
    ) or (
        article_type == "industry_analysis" and length_mode == "short"
    )


def _resolve_patch_path_refusal_reason(
    contract: Mapping[str, Any],
    section_state: Mapping[str, Any],
    runtime_check: Mapping[str, Any],
) -> str:
    if bool(section_state.get("enabled")) and not bool(section_state.get("fallback_to_super")):
        return "repair_owned_by_section_path"
    body_generation = dict(runtime_check.get("body_generation") or {})
    if bool(body_generation.get("repair_applied")):
        return "repair_applied"
    repair_call = dict(body_generation.get("repair_call") or {})
    repair_trigger_score = float(body_generation.get("repair_trigger_score") or 0.0)
    if not repair_call:
        return "repair_not_triggered" if repair_trigger_score <= 0.0 else "repair_call_unavailable"
    if bool(repair_call.get("patch_path_used")):
        return "patch_path_used"
    scope_rejection_reason = str(repair_call.get("scope_rejection_reason") or "").strip()
    if scope_rejection_reason:
        return scope_rejection_reason
    if not bool(repair_call.get("patch_path_available")):
        return "no_flagged_spans"
    issue_types = {
        str(item or "").strip()
        for item in list(repair_call.get("flagged_issue_types") or [])
        if str(item or "").strip()
    }
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type == "comparative_review":
        if issue_types != {"comparative_thin_section"}:
            return "comparative_issue_type_ineligible"
        return "comparative_patch_not_selected"
    if not _compact_plan_patch_scope_allowed(contract):
        return "compact_plan_scope_ineligible"
    if issue_types and not issue_types.issubset({"heading_reanchor", "ending_bucket_monotony", "shadow_section_drift"}):
        return "issue_type_ineligible"
    return "repair_retained_without_patch_path"


def _build_wrapper_quality_spine(
    primary_generation: Mapping[str, Any],
    *,
    compatibility_rebuild: bool,
) -> Dict[str, Any]:
    postprocess_sequence = [
        *(["compatibility_rebuild"] if compatibility_rebuild else []),
        "semantic_dedupe",
        "editor_guard",
        "resonance_pass",
        "quality_pass",
        "legal_postcheck",
        "output_formatter",
    ]
    return {
        "wrapper_role": "adapter_validator",
        "primary_generation_source": str(primary_generation.get("source") or ""),
        "primary_generation_owner": str(primary_generation.get("owner") or ""),
        "primary_generation_mode": str(primary_generation.get("generation_mode") or ""),
        "fallback_to_super": bool(primary_generation.get("fallback_to_super")),
        "repair_owned_by_primary": bool(primary_generation.get("repair_applied")),
        "postprocess_sequence": postprocess_sequence,
        "quality_control_points": ["primary_generation", *postprocess_sequence],
    }


def _build_body_generation_telemetry(
    *,
    contract: Mapping[str, Any],
    runtime_check: Mapping[str, Any],
    primary_generation: Mapping[str, Any],
    section_state: Mapping[str, Any],
    planning_gate: Mapping[str, Any],
    style_profile: Mapping[str, Any],
    sections: Sequence[Any],
    output_body: str,
    compatibility_rebuild: bool,
) -> Dict[str, Any]:
    section_path_used = bool(section_state.get("enabled")) and not bool(section_state.get("fallback_to_super"))
    return {
        **dict(runtime_check.get("body_generation") or {}),
        "writer_of_record": str(primary_generation.get("owner") or ""),
        "route_branch": _resolve_route_branch(section_state),
        "section_path_used": section_path_used,
        "style_profile_source": _resolve_style_profile_source(contract, style_profile),
        "planning_opt_in_gate": dict(planning_gate or {}),
        "patch_path_refusal_reason": _resolve_patch_path_refusal_reason(contract, section_state, runtime_check),
        "planned_vs_actual_heading_overlap": _build_planned_vs_actual_heading_overlap(sections, output_body),
        "quality_spine": _build_wrapper_quality_spine(
            primary_generation,
            compatibility_rebuild=compatibility_rebuild,
        ),
    }


def _build_success_result_seed() -> Dict[str, Any]:
    return {
        "success": True,
        "title": "",
        "lead": "",
        "body": "",
        "full_body": "",
        "references": "",
        "hashtags": "",
        "full_text": "",
        "linkedin_text": "",
        "pipeline_check_linkedin": {},
        "pipeline_check": {},
        "quality_pipeline_check": {},
        "review_points": [],
        "hard_failed": False,
        "hard_fail_reasons": [],
        "output_guard": {},
        "reason_code": "OK",
        "runtime_reason_code": "OK",
        "runtime_error_class": "success",
    }


def _hydrate_compatibility_source_documents(contract: Dict[str, Any]) -> Dict[str, Any]:
    hydrated = dict(contract)
    input_decision = dict(hydrated.get("input_decision") or {})
    if str(input_decision.get("action") or "accept").strip().lower() != "accept":
        return hydrated
    if list(hydrated.get("source_documents") or []):
        return hydrated
    source_inputs = [
        str(item or "").strip()
        for item in list(hydrated.get("source_inputs") or hydrated.get("source") or [])
        if str(item or "").strip()
    ]
    topic_seed = str(
        hydrated.get("topic_statement")
        or hydrated.get("prompt_raw")
        or hydrated.get("topic")
        or ""
    ).strip()
    if source_inputs:
        hydrated["source_documents"] = [
            {
                "title": f"Compatibility Source {index}",
                "locator": locator,
                "source_type": "url" if locator.lower().startswith(("http://", "https://")) else "text",
                "content": topic_seed or "参照URLの要点を整理するための互換コンテキストです。",
            }
            for index, locator in enumerate(source_inputs[:4], start=1)
        ]
    elif topic_seed:
        hydrated["source_documents"] = [
            {
                "title": "Compatibility Prompt Context",
                "locator": "compat://prompt",
                "source_type": "text",
                "content": topic_seed,
            }
        ]
    else:
        return hydrated
    compatibility_bridge = dict(hydrated.get("compatibility_bridge") or {})
    compatibility_bridge["hydrated_source_documents"] = True
    compatibility_bridge["hydrated_source_count"] = len(hydrated["source_documents"])
    hydrated["compatibility_bridge"] = compatibility_bridge
    return hydrated


def _contains_any_marker(text: str, markers: Sequence[str]) -> bool:
    lowered = str(text or "").strip().lower()
    return any(str(marker or "").strip().lower() in lowered for marker in markers if str(marker or "").strip())


def _company_intro_source_priority_band(
    *,
    bucket: Any = "",
    title: Any = "",
    locator: Any = "",
    content: Any = "",
) -> int:
    bucket_text = str(bucket or "").strip().lower()
    title_text = str(title or "").strip()
    locator_text = str(locator or "").strip()
    content_text = str(content or "").strip()
    combined = " ".join(part for part in (bucket_text, title_text, locator_text, content_text) if part).strip()
    if bucket_text == "history" or _contains_any_marker(combined, _COMPANY_INTRO_HISTORY_MARKERS):
        return 3
    if bucket_text == "overview" or _contains_any_marker(combined, _COMPANY_INTRO_OVERVIEW_MARKERS):
        return 0
    if bucket_text == "strength" or _contains_any_marker(combined, _COMPANY_INTRO_STRENGTH_MARKERS):
        return 1
    return 2


def _reorder_company_intro_current_first_sources(contract: Mapping[str, Any]) -> Dict[str, Any]:
    reordered = dict(contract)
    article_type = str(reordered.get("article_type") or "").strip().lower()
    semantic_key = str(reordered.get("semantic_article_key") or "").strip().lower()
    if article_type != "branding" or semantic_key != "company_introduction":
        return reordered

    source_documents = [
        dict(item)
        for item in list(reordered.get("source_documents") or [])
        if isinstance(item, Mapping)
    ]
    source_grounding_items = [
        dict(item)
        for item in list(reordered.get("source_grounding_items") or [])
        if isinstance(item, Mapping)
    ]
    if not source_documents and not source_grounding_items:
        return reordered

    document_bands = [
        _company_intro_source_priority_band(
            title=item.get("title"),
            locator=item.get("locator"),
            content=item.get("content"),
        )
        for item in source_documents
    ]
    grounding_bands = [
        _company_intro_source_priority_band(
            bucket=item.get("bucket"),
            title=item.get("source_title") or item.get("title"),
            locator=item.get("locator"),
            content=item.get("fact_text"),
        )
        for item in source_grounding_items
    ]
    has_history = any(band >= 4 for band in [*document_bands, *grounding_bands])
    has_current = any(band <= 1 for band in [*document_bands, *grounding_bands])
    if not has_history or not has_current:
        return reordered

    ordered_documents = [
        item for _, _, item in sorted((band, index, item) for index, (band, item) in enumerate(zip(document_bands, source_documents)))
    ]
    ordered_grounding_items = [
        item
        for _, _, item in sorted(
            (band, index, item) for index, (band, item) in enumerate(zip(grounding_bands, source_grounding_items))
        )
    ]
    if ordered_documents != source_documents:
        reordered["source_documents"] = ordered_documents
    if ordered_grounding_items != source_grounding_items:
        reordered["source_grounding_items"] = ordered_grounding_items
    return reordered


def _build_runtime_block(primary_call: Mapping[str, Any], *, article_type: str, compatibility_mode: str) -> Dict[str, Any]:
    primary = dict(primary_call or {})
    selected_model = str(
        primary.get("selected_model")
        or primary.get("primary_model")
        or primary.get("base_model")
        or ("offline_deterministic" if compatibility_mode == "offline_deterministic" else "")
    )
    return {
        "primary_model": str(primary.get("primary_model") or selected_model),
        "selected_model": selected_model,
        "base_model": str(primary.get("base_model") or selected_model),
        "model_source": str(
            primary.get("model_source")
            or ("deterministic_fallback" if compatibility_mode == "offline_deterministic" else "wrapped_llm")
        ),
        "task_type": str(primary.get("task_type") or "section"),
        "article_type": article_type,
        "effective_reasoning_effort": str(primary.get("effective_reasoning_effort") or ""),
        "effective_temperature": primary.get("effective_temperature"),
        "effective_top_p": primary.get("effective_top_p"),
        "effective_presence_penalty": primary.get("effective_presence_penalty"),
        "effective_frequency_penalty": primary.get("effective_frequency_penalty"),
        "effective_verbosity": str(primary.get("effective_verbosity") or ""),
        "compatibility_suppressed_params": list(primary.get("compatibility_suppressed_params") or []),
        "same_model_retry_count": 0,
        "model_fallback_attempted": False,
        "model_fallback_blocked": True,
        "prompt_truncation_attempted": False,
        "prompt_truncation_blocked": False,
        "execution_mode": compatibility_mode,
    }


def _merge_quality_metrics(runtime_metrics: Mapping[str, Any], compatibility_metrics: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(runtime_metrics or {})
    merged.update(dict(compatibility_metrics or {}))
    return merged


def _quality_contract_from_runtime_check(
    runtime_check: Mapping[str, Any],
    fallback_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    runtime_contract = runtime_check.get("input_contract")
    if isinstance(runtime_contract, Mapping) and runtime_contract:
        return dict(runtime_contract)
    return dict(fallback_contract or {})


def _default_quality_check() -> Dict[str, Any]:
    return {
        "enabled": True,
        "mode": "shadow",
        "fail_open": True,
        "reports": [],
        "mode_resolution": {},
        "errors": [],
        "applied": [],
        "monitoring_report": {},
    }


def _normalize_heading_text(raw_heading: Any) -> str:
    heading = str(raw_heading or "").strip()
    return heading[3:].strip() if heading.startswith("## ") else heading


def _merge_warning_list(*warning_lists: Sequence[str]) -> list[str]:
    merged: list[str] = []
    for items in warning_lists:
        for item in list(items or []):
            text = str(item or "").strip()
            if text and text not in merged:
                merged.append(text)
    return merged


def _merge_editor_reports(primary: Mapping[str, Any], secondary: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(primary or {})
    extra = dict(secondary or {})
    count_keys = (
        "ai_phrase_replaced_count",
        "legal_softened_count",
        "duplicate_line_removed_count",
        "grammar_repair_count",
        "sentence_integrity_repair_count",
        "sentence_integrity_warning_count",
    )
    for key in count_keys:
        merged[key] = int(merged.get(key, 0) or 0) + int(extra.get(key, 0) or 0)
    merged["warnings"] = _merge_warning_list(
        list(merged.get("warnings") or []),
        list(extra.get("warnings") or []),
    )
    merged["repair_actions"] = [
        *list(merged.get("repair_actions") or []),
        *list(extra.get("repair_actions") or []),
    ]
    return merged


def _verified_source_texts(contract: Mapping[str, Any]) -> list[str]:
    return [
        str(dict(item).get("content") or "")
        for item in list(contract.get("source_documents") or [])
        if isinstance(item, Mapping) and str(dict(item).get("content") or "").strip()
    ]


def _section_body_after_heading(body: str, heading: str) -> str:
    if not heading or f"## {heading}" not in str(body or ""):
        return ""
    tail = str(body or "").split(f"## {heading}", 1)[-1]
    next_heading = re.search(r"\n##\s+", tail)
    if next_heading:
        tail = tail[: next_heading.start()]
    return tail.strip()


def _extract_section_headings(body: str) -> list[str]:
    return [str(match or "").strip() for match in re.findall(r"(?m)^##\s+(.+)$", str(body or "")) if str(match or "").strip()]


def _comparative_has_closing_signal(body: str) -> bool:
    headings = _extract_section_headings(body)
    if any(("結論" in heading or "おすすめ" in heading) for heading in headings[-2:]):
        return True
    tail = "\n".join(str(body or "").splitlines()[-12:])
    return "結論として" in tail


def _default_section_sentence(article_type: str, intent: str, topic_seed: str) -> str:
    if article_type == "announcement":
        mapping = {
            "context": f"{topic_seed}を先に整理します。",
            "clarify": f"{topic_seed}と時期を分けて確認します。",
            "impact": f"{topic_seed}として想定される影響を短く整理します。",
            "caution": f"{topic_seed}は事前に確認しておくと混乱を避けやすくなります。",
            "practice": f"{topic_seed}では移行時に迷いやすい点を押さえます。",
            "closing": f"{topic_seed}は公式情報を見ながら確認すると判断しやすくなります。",
        }
        return mapping.get(intent, f"{topic_seed}を短く整理します。")
    if article_type == "case_study":
        mapping = {
            "hook": "最初は判断の境目が曖昧で、案内のたびに確認先がぶれていました。",
            "problem": "現場と管理側で見ている課題が違い、差し戻しが増えていました。",
            "practice": "対象業務を一つに絞り、申請者と承認者の役割を先にそろえました。",
            "decision": "今決めることと後で扱うことを分けるだけで、会議の詰まり方が変わりました。",
            "change": "初回返信までの時間が短くなり、差し戻し理由もそろってきました。",
            "condition": "再現条件として、対象業務を一つに絞り、役割と前提を先に言葉にしておく必要があります。ただし、例外処理が毎回変わる場合は追加の整理が必要です。",
        }
        return mapping.get(intent, f"{topic_seed}を具体化します。")
    if article_type == "comparative_review":
        mapping = {
            "criteria": "評価軸として導入負荷、運用定着性、移行コストを先に固定します。",
            "comparison": "候補Aは導入負荷、候補Bは運用定着性、候補Cは移行コストの見え方が異なります。",
            "fit": "小規模運用なら候補Aが向きやすく、複数部門でそろえるなら候補Bが向いています。",
            "caution": "前提や例外が多い場合は、移行コストと運用体制を追加で確認する必要があります。",
            "closing": "結論として、立ち上がりを優先するなら候補Aを選びます。全社統制を優先するなら候補Bを選びます。",
        }
        return mapping.get(intent, f"{topic_seed}を比較の軸に沿って整理します。")
    return f"{topic_seed or 'この節の論点'}を具体化します。"


def _case_study_fallback_fact_text(
    source_grounding_items: list[Dict[str, Any]],
    *,
    intent: str,
) -> str:
    if not source_grounding_items:
        return ""
    if intent not in {"change", "condition"}:
        return ""
    pattern = (
        re.compile(r"(減っ|増え|短くな|早くな|小さくな|そろっ|改善し|改善につなが|分かっ|でき|見え|安定し)")
        if intent == "change"
        else _CASE_STUDY_CONDITION_SENTENCE_RE
    )
    preferred_items = list(source_grounding_items[1:]) or list(source_grounding_items)
    for item in preferred_items:
        fact_text = str(item.get("fact_text") or "").strip()
        if intent == "change" and fact_text:
            fact_text = re.split(r"(?:再現条件として|条件として|前提として)", fact_text, maxsplit=1)[0].strip()
            if fact_text and (
                pattern.search(fact_text) or _CASE_STUDY_CHANGE_FALLBACK_CLAUSE_RE.search(fact_text)
            ):
                return fact_text
            continue
        if fact_text and pattern.search(fact_text):
            return fact_text
    return ""


def _has_case_study_default_change_sentence(text: str) -> bool:
    sentences = _split_japanese_sentences(text)
    return _CASE_STUDY_DEFAULT_CHANGE_SENTENCE in sentences


def _section_fact_text(section: Any, source_grounding_items: list[Dict[str, Any]], index: int, *, article_type: str = "") -> str:
    section_sources = [
        dict(item)
        for item in list(getattr(section, "source_grounding_items", []) or [])
        if isinstance(item, Mapping)
    ]
    if section_sources:
        return str(section_sources[0].get("fact_text") or "").strip()
    intent = str(getattr(section, "intent", "") or "").strip().lower()
    if article_type == "case_study":
        fallback_fact = _case_study_fallback_fact_text(source_grounding_items, intent=intent)
        if fallback_fact:
            return fallback_fact
    if index < len(source_grounding_items):
        return str(source_grounding_items[index].get("fact_text") or "").strip()
    return ""


def _build_compatibility_body(contract: Mapping[str, Any], sections: Sequence[Any]) -> str:
    article_type = str(contract.get("article_type") or "").strip().lower()
    source_grounding_items = [
        dict(item)
        for item in list(contract.get("source_grounding_items") or [])
        if isinstance(item, Mapping)
    ]
    prompt_context_items = [
        str(item or "").strip()
        for item in list(contract.get("prompt_context_items") or [])
        if str(item or "").strip()
    ]
    chunks: list[str] = []
    for index, section in enumerate(list(sections)[:6]):
        heading = _normalize_heading_text(getattr(section, "heading", "") or f"節 {index + 1}")
        fact_text = _section_fact_text(section, source_grounding_items, index, article_type=article_type)
        topic_seed = str(getattr(section, "topic_seed", "") or getattr(section, "new_information", "") or "").strip()
        intent = str(getattr(section, "intent", "") or "").strip().lower()
        if article_type == "case_study" and fact_text:
            if intent == "change" and _case_study_change_signal_count(fact_text) <= 0:
                fact_text = ""
            elif intent == "condition" and _case_study_condition_signal_count(fact_text) <= 0:
                fact_text = ""
        if fact_text:
            sentence = fact_text
        elif article_type == "comparative_review" and _is_cross_department_governance_compare(contract):
            sentence = _cross_department_compatibility_sentence(intent, contract, topic_seed)
        else:
            sentence = _default_section_sentence(article_type, intent, topic_seed)
        if index == 0 and prompt_context_items:
            sentence = " ".join([sentence, prompt_context_items[0]]).strip()
        if sentence and sentence[-1] not in "。！？":
            sentence += "。"
        chunks.append(f"## {heading}\n\n{sentence}")
    return "\n\n".join(chunk for chunk in chunks if chunk).strip()


def _count_markdown_sections(body: str) -> int:
    return len(re.findall(r"(?m)^##\s+", str(body or "")))


def _replace_section_body_after_heading(body: str, heading: str, section_body: str) -> str:
    text = str(body or "").strip()
    replacement = str(section_body or "").strip()
    if not text or not heading or f"## {heading}" not in text or not replacement:
        return text
    pattern = re.compile(
        rf"(?ms)^##\s+{re.escape(heading)}\s*\n\n.*?(?=^\s*##\s+|\Z)"
    )
    return pattern.sub(f"## {heading}\n\n{replacement}\n\n", text, count=1).strip()


def _case_study_condition_signal_count(text: str) -> int:
    return len(_CASE_STUDY_CONDITION_SENTENCE_RE.findall(str(text or "")))


def _case_study_change_signal_count(text: str) -> int:
    return len(_CASE_STUDY_CHANGE_SENTENCE_RE.findall(str(text or "")))


def _split_markdown_sections(body: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    pattern = re.compile(r"(?ms)^##\s+(.+?)\n\n(.*?)(?=^\s*##\s+|\Z)")
    for match in pattern.finditer(str(body or "").strip()):
        heading = _normalize_heading_text(match.group(1))
        section_body = str(match.group(2) or "").strip()
        if heading and section_body:
            sections.append((heading, section_body))
    return sections


def _split_japanese_sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[。！？])\s*", str(text or "").strip()) if item.strip()]


def _append_unique_sentences(section_body: str, sentences: Sequence[str]) -> str:
    updated = str(section_body or "").strip()
    existing_sentences = set(_split_japanese_sentences(updated))
    for sentence in sentences:
        text = str(sentence or "").strip()
        if not text or text in existing_sentences or text in updated:
            continue
        updated = f"{updated}{text}" if updated else text
        existing_sentences.add(text)
    return updated.strip()


def _dedupe_preserve_order(items: Sequence[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(text)
    return unique


def _collect_case_study_signal_sentences(
    text: str,
    *,
    pattern: re.Pattern[str],
    exclude_pattern: re.Pattern[str] | None = None,
) -> list[str]:
    return [
        sentence
        for sentence in _split_japanese_sentences(text)
        if pattern.search(sentence)
        and not _CASE_STUDY_META_SENTENCE_RE.search(sentence)
        and not (exclude_pattern.search(sentence) if exclude_pattern else False)
    ]


def _stabilize_case_study_final_body(body: str, fallback_body: str) -> str:
    original = str(body or "").strip()
    if not original:
        return str(fallback_body or "").strip()

    sections = _split_markdown_sections(original)
    if not sections:
        return original
    fallback_problem_section = next(
        (
            (fallback_heading, fallback_section_body)
            for fallback_heading, fallback_section_body in _split_markdown_sections(str(fallback_body or ""))
            if _CASE_STUDY_PROBLEM_HEADING_RE.search(fallback_heading)
        ),
        None,
    )
    has_problem_section = any(_CASE_STUDY_PROBLEM_HEADING_RE.search(heading) for heading, _ in sections)
    needs_problem_backfill = not has_problem_section and fallback_problem_section is not None

    explicit_result = _section_body_after_heading(original, _CASE_STUDY_RESULT_HEADING)
    explicit_condition = _section_body_after_heading(original, _CASE_STUDY_CONDITION_HEADING)
    fallback_result = _section_body_after_heading(str(fallback_body or ""), _CASE_STUDY_RESULT_HEADING)
    fallback_condition = _section_body_after_heading(str(fallback_body or ""), _CASE_STUDY_CONDITION_HEADING)
    explicit_condition_signal_count = _case_study_condition_signal_count(explicit_condition)
    explicit_condition_signal_sentence_count = len(
        _collect_case_study_signal_sentences(
            explicit_condition,
            pattern=_CASE_STUDY_CONDITION_SENTENCE_RE,
        )
    )
    explicit_condition_sentence_count = len(_split_japanese_sentences(explicit_condition))
    fallback_condition_sentence_count = len(_split_japanese_sentences(fallback_condition))
    prefer_richer_fallback_condition = (
        explicit_condition
        and explicit_condition_signal_count > 0
        and explicit_condition_sentence_count <= 1
        and fallback_condition
        and fallback_condition_sentence_count > explicit_condition_sentence_count
    )
    prefer_enumerated_fallback_condition = (
        explicit_condition
        and _CASE_STUDY_CONDITION_ENUMERATION_STUB_RE.search(explicit_condition) is not None
        and re.search(r"(一つ目|二つ目)", explicit_condition) is None
        and fallback_condition
    )
    prefer_richer_fallback_condition = prefer_richer_fallback_condition or prefer_enumerated_fallback_condition
    prefer_source_grounded_fallback_result = (
        explicit_result
        and _has_case_study_default_change_sentence(explicit_result)
        and fallback_result
        and not _has_case_study_default_change_sentence(fallback_result)
    )
    if (
        explicit_result
        and _case_study_change_signal_count(explicit_result) > 0
        and explicit_condition
        and explicit_condition_signal_count > 0
        and not prefer_source_grounded_fallback_result
        and not prefer_richer_fallback_condition
        and not needs_problem_backfill
    ):
        return original

    result_sentences: list[str] = []
    condition_sentences: list[str] = []
    donor_indexes: set[int] = set()
    for index, (heading, section_body) in enumerate(sections):
        heading_has_change = bool(_CASE_STUDY_CHANGE_HEADING_RE.search(heading))
        heading_has_condition = bool(_CASE_STUDY_CONDITION_HEADING_RE.search(heading))
        if heading == _CASE_STUDY_RESULT_HEADING:
            heading_has_change = True
        if heading == _CASE_STUDY_CONDITION_HEADING:
            heading_has_condition = True
        if not (heading_has_change or heading_has_condition):
            continue
        donor_indexes.add(index)
        if heading_has_change:
            result_sentences.extend(
                _collect_case_study_signal_sentences(
                    section_body,
                    pattern=_CASE_STUDY_CHANGE_SENTENCE_RE,
                    exclude_pattern=re.compile(r"(条件|前提|限界|再現|ただし|場合|例外|分岐|退避)"),
                )
            )
        if heading_has_condition:
            condition_sentences.extend(
                _collect_case_study_signal_sentences(
                    section_body,
                    pattern=_CASE_STUDY_CONDITION_SENTENCE_RE,
                )
            )

    result_body = ""
    condition_body = ""
    deduped_result_sentences = _dedupe_preserve_order(
        [
            sentence
            for sentence in result_sentences
            if not _has_case_study_default_change_sentence(sentence)
        ]
    )
    if prefer_source_grounded_fallback_result:
        result_body = fallback_result
    elif (
        explicit_result
        and _case_study_change_signal_count(explicit_result) > 0
        and not prefer_source_grounded_fallback_result
    ):
        result_body = explicit_result
    elif deduped_result_sentences:
        result_body = " ".join(deduped_result_sentences).strip()
    else:
        result_body = fallback_result
    if (
        explicit_condition
        and _case_study_condition_signal_count(explicit_condition) > 0
        and not prefer_richer_fallback_condition
    ):
        condition_body = explicit_condition
    elif condition_sentences and not prefer_richer_fallback_condition:
        condition_body = " ".join(_dedupe_preserve_order(condition_sentences)).strip()
    else:
        condition_body = fallback_condition

    if not result_body and not condition_body:
        return original

    rebuilt_sections: list[str] = []
    if fallback_problem_section is not None and needs_problem_backfill:
        fallback_heading, fallback_section_body = fallback_problem_section
        rebuilt_sections.append(f"## {fallback_heading}\n\n{fallback_section_body}")
    for index, (heading, section_body) in enumerate(sections):
        if index in donor_indexes:
            continue
        rebuilt_sections.append(f"## {heading}\n\n{section_body}")
    if result_body:
        rebuilt_sections.append(f"## {_CASE_STUDY_RESULT_HEADING}\n\n{result_body}")
    if condition_body:
        rebuilt_sections.append(f"## {_CASE_STUDY_CONDITION_HEADING}\n\n{condition_body}")
    rebuilt = "\n\n".join(section for section in rebuilt_sections if section).strip()
    if rebuilt:
        rebuilt_result = _section_body_after_heading(rebuilt, _CASE_STUDY_RESULT_HEADING)
        if (
            rebuilt_result
            and _case_study_change_signal_count(rebuilt_result) <= 0
            and not prefer_source_grounded_fallback_result
        ):
            rebuilt = _replace_section_body_after_heading(
                rebuilt,
                _CASE_STUDY_RESULT_HEADING,
                _append_unique_sentences(
                    _default_section_sentence("case_study", "change", ""),
                    [
                        "差し戻し理由がそろったことで、次に何を直せばよいかを担当者どうしで共有しやすくなりました。",
                    ],
                ),
            )
        rebuilt_condition = _section_body_after_heading(rebuilt, _CASE_STUDY_CONDITION_HEADING)
        if (
            rebuilt_condition
            and _case_study_condition_signal_count(rebuilt_condition) <= 0
            and not prefer_richer_fallback_condition
        ):
            rebuilt = _replace_section_body_after_heading(
                rebuilt,
                _CASE_STUDY_CONDITION_HEADING,
                _append_unique_sentences(
                    _default_section_sentence("case_study", "condition", ""),
                    [
                        "入口の分岐、権限設定を先に置く順番、FAQへの退避先をセットで残すことが、同じ迷いを抑える前提になります。",
                    ],
                ),
            )
    return rebuilt or original


def _normalize_case_study_dedupe_audit_after_stabilization(
    audit: Mapping[str, Any],
    final_body: str,
) -> dict[str, Any]:
    normalized = dict(audit or {})
    regenerated = int(normalized.get("regenerated_paragraphs") or 0)
    if regenerated <= 0:
        return normalized
    deletion_reasons = [item for item in list(normalized.get("deletion_reasons") or []) if isinstance(item, Mapping)]
    if not deletion_reasons:
        return normalized
    if not all(str(item.get("reason") or "") == "exact_text_match" for item in deletion_reasons):
        return normalized
    result_body = _section_body_after_heading(final_body, _CASE_STUDY_RESULT_HEADING)
    condition_body = _section_body_after_heading(final_body, _CASE_STUDY_CONDITION_HEADING)
    if _case_study_change_signal_count(result_body) <= 0 or _case_study_condition_signal_count(condition_body) <= 0:
        return normalized
    normalized["postprocess_absorbed_regenerated_paragraphs"] = regenerated
    normalized["regenerated_paragraphs"] = 0
    return normalized


def _stabilize_thin_announcement_body(body: str) -> str:
    original = str(body or "").strip()
    if not original or len(original) >= _ANNOUNCEMENT_THIN_BODY_CHAR_LIMIT:
        return original

    sections = _split_markdown_sections(original)
    if not sections:
        return original

    target_heading = next(
        (
            heading
            for heading, _section_body in reversed(sections)
            if re.search(r"(事前準備|確認|旧設定)", heading)
        ),
        sections[-1][0],
    )
    target_body = _section_body_after_heading(original, target_heading)
    if not target_body:
        return original

    supplemented = _append_unique_sentences(
        target_body,
        [
            "対象者と事前準備を先に関係者へ共有しておくと、当日の確認を迷わず進めやすくなります。",
            "旧設定を参照専用で残す期間と、新しい必須項目を基準に運用を進める期間を分けておくと、切り替え時の確認がぶれにくくなります。",
        ],
    )
    if supplemented == target_body:
        return original
    return _replace_section_body_after_heading(original, target_heading, supplemented)


def _announcement_role_alignment_seed(contract: Mapping[str, Any]) -> str:
    source_items = list(contract.get("source_grounding_items") or [])
    fact_pool = [str(item.get("fact_text") or "").strip() for item in source_items if str(item.get("fact_text") or "").strip()]
    joined_facts = " ".join(fact_pool)
    if "編集担当者" in joined_facts and "承認者" in joined_facts:
        return "今回の見直しでは、申請を送る担当と承認経路を確認する担当の両方が影響を受けます。"
    if "承認者" in joined_facts:
        return "今回の見直しでは、申請側だけでなく承認順を確認する側でも事前確認が必要です。"
    return "公開前の流れに関わる人は、新しい順番を事前に確認しておく必要があります。"


def _stabilize_announcement_prompt_echo_body(body: str, contract: Mapping[str, Any]) -> str:
    original = str(body or "").strip()
    if not original:
        return original
    if str(contract.get("article_type") or "").strip().lower() != "announcement":
        return original

    prompt_refs = build_prompt_echo_references(
        user_prompt=str(contract.get("prompt_raw") or contract.get("topic") or ""),
        include_must_cover=False,
    )
    if not prompt_refs:
        return original

    replacement = _announcement_role_alignment_seed(contract)
    if not replacement:
        return original

    stabilized = original
    for heading, section_body in _split_markdown_sections(original):
        if not _ANNOUNCEMENT_TARGET_HEADING_RE.search(heading):
            continue
        prompt_echo_hits = detect_prompt_echo_sentences(
            section_body,
            references=prompt_refs,
            max_hits=2,
        )
        for sentence in _split_japanese_sentences(section_body):
            if not _ANNOUNCEMENT_ROLE_PROMPT_ECHO_RE.search(sentence):
                continue
            excerpt = sentence[:140]
            if excerpt not in prompt_echo_hits:
                prompt_echo_hits.append(excerpt)
        if not prompt_echo_hits:
            continue

        filtered_sentences = [
            sentence
            for sentence in _split_japanese_sentences(section_body)
            if not any(str(hit or "").strip() and str(hit).strip() in sentence for hit in prompt_echo_hits)
        ]
        rebuilt_sentences = [replacement]
        for sentence in filtered_sentences:
            if sentence != replacement:
                rebuilt_sentences.append(sentence)
        rebuilt_body = " ".join(sentence for sentence in rebuilt_sentences if sentence).strip()
        if not rebuilt_body or rebuilt_body == section_body:
            continue
        stabilized = _replace_section_body_after_heading(stabilized, heading, rebuilt_body)
    return stabilized


def _announcement_has_duplicate_must_cover_sentence(sentence: str, labels: Sequence[str]) -> bool:
    candidate = str(sentence or "").strip()
    if not candidate:
        return False
    for label in labels:
        normalized = str(label or "").strip()
        if normalized and f"{normalized}と{normalized}" in candidate:
            return True
    return bool(re.search(r"([一-龥ぁ-んァ-ヶA-Za-z0-9]{2,20})と\1と", candidate))


def _stabilize_announcement_source_grounded_sections(
    body: str,
    fallback_body: str,
    contract: Mapping[str, Any],
) -> str:
    original = str(body or "").strip()
    fallback = str(fallback_body or "").strip()
    if not original or not fallback:
        return original
    if str(contract.get("article_type") or "").strip().lower() != "announcement":
        return original

    must_cover_labels = _must_cover_items(contract)
    stabilized = original
    for heading, section_body in _split_markdown_sections(original):
        fallback_section = _section_body_after_heading(fallback, heading)
        if not fallback_section:
            continue
        filtered_sentences: list[str] = []
        removed_sentence = False
        for sentence in _split_japanese_sentences(section_body):
            if _announcement_has_duplicate_must_cover_sentence(sentence, must_cover_labels):
                removed_sentence = True
                continue
            if _ANNOUNCEMENT_PREPARATION_TIME_RE.search(sentence) and not _ANNOUNCEMENT_DATETIME_RE.search(sentence):
                removed_sentence = True
                continue
            filtered_sentences.append(sentence)
        rebuilt_body = " ".join(filtered_sentences).strip()
        fallback_sentences = _split_japanese_sentences(fallback_section)
        if _ANNOUNCEMENT_TIME_HEADING_RE.search(heading):
            has_datetime = bool(_ANNOUNCEMENT_DATETIME_RE.search(rebuilt_body))
            fallback_datetime_sentences = [
                sentence for sentence in fallback_sentences if _ANNOUNCEMENT_DATETIME_RE.search(sentence)
            ]
            if fallback_datetime_sentences and not has_datetime:
                rebuilt_body = _append_unique_sentences(rebuilt_body, fallback_datetime_sentences[:1])
        if removed_sentence and not rebuilt_body:
            rebuilt_body = fallback_section
        if rebuilt_body and rebuilt_body != section_body:
            stabilized = _replace_section_body_after_heading(stabilized, heading, rebuilt_body)
    return stabilized


def _stabilize_thin_case_study_body(body: str) -> str:
    original = str(body or "").strip()
    if not original or len(original) >= _CASE_STUDY_THIN_BODY_CHAR_LIMIT:
        return original

    stabilized = original
    result_body = _section_body_after_heading(stabilized, _CASE_STUDY_RESULT_HEADING)
    if result_body:
        supplemented_result = _append_unique_sentences(
            result_body,
            [
                "単なる成功談としてまとめるより、どの順番と入口なら再現しやすいかまで残したことで、次の見直しでも使える判断材料になりました。",
                "管理者向けの前提説明を先頭に置かずに済むため、実務担当者が自分の次の操作を見つけやすくなりました。",
            ],
        )
        if supplemented_result != result_body:
            stabilized = _replace_section_body_after_heading(
                stabilized,
                _CASE_STUDY_RESULT_HEADING,
                supplemented_result,
            )

    condition_body = _section_body_after_heading(stabilized, _CASE_STUDY_CONDITION_HEADING)
    if condition_body:
        supplemented_condition = _append_unique_sentences(
            condition_body,
            [
                "入口の分岐、権限設定を先に置く順番、FAQへの退避先をセットで残すことが、同じ迷いを抑える前提になります。",
                "担当者別の入口だけを足すのではなく、順番と退避先までそろえておくと再現しやすくなります。",
            ],
        )
        if supplemented_condition != condition_body:
            stabilized = _replace_section_body_after_heading(
                stabilized,
                _CASE_STUDY_CONDITION_HEADING,
                supplemented_condition,
            )
    return stabilized


def _select_source_grounding_fact(
    source_grounding_items: Sequence[Mapping[str, Any]],
    *,
    body: str,
    include_terms: Sequence[str],
) -> str:
    body_text = str(body or "")
    for item in list(source_grounding_items or []):
        fact_text = str(dict(item).get("fact_text") or "").strip()
        if not fact_text or fact_text in body_text:
            continue
        if include_terms and not any(term in fact_text for term in include_terms):
            continue
        if fact_text[-1] not in "。！？":
            fact_text += "。"
        return fact_text
    return ""


def _is_product_introduction_route(contract: Mapping[str, Any] | None) -> bool:
    normalized = dict(contract or {})
    return (
        str(normalized.get("article_type") or "").strip().lower() == "branding"
        and str(normalized.get("semantic_article_key") or "").strip().lower() == "product_introduction"
    )


def _product_intro_support_sentences(
    heading: str,
    contract: Mapping[str, Any],
    *,
    section_body: str,
    full_body: str,
) -> list[str]:
    source_grounding_items = [
        dict(item)
        for item in list(contract.get("source_grounding_items") or [])
        if isinstance(item, Mapping)
    ]
    heading_text = str(heading or "")
    if "課題" in heading_text:
        core_message = str(contract.get("core_message") or "").strip() or "DX化の最初はデジタルデータ"
        return [
            f"{core_message}と考えるのは、設定の順番が曖昧なままだと、導入初期の問い合わせが管理者側へ偏りやすいからです。",
            "初回設定の手順整理、担当者別の案内分岐、FAQ整備をばらばらにせず、最初から一続きで整える必要があります。",
        ]
    if "価値" in heading_text:
        return [
            (
                "誰のどんな課題に合うかは、導入初期に管理者へ負荷が偏っているか、"
                "担当者ごとの案内を分けたいかで見極めやすくなります。"
            ),
            "複数部門が関わる導入では、設定の順番と確認ポイントをそろえられるかが、そのまま使いやすさの差になります。",
        ]
    if "工夫" in heading_text:
        operations_fact = _select_source_grounding_fact(
            source_grounding_items,
            body=full_body,
            include_terms=("設定の順番", "確認ポイント", "権限設定", "FAQ", "案内分岐"),
        )
        if operations_fact:
            return [
                operations_fact,
                "運用の工夫としては、迷いやすい手順から順に案内を置き直し、FAQへの退避先も同じ流れの中で見つけやすくすることが効きます。",
            ]
        return [
            "担当者別の入口、設定の順番、FAQへの導線を同じ基準で見直すと、途中の確認戻りを減らしやすくなります。",
            "現場の工夫としては、通知設定より先に権限設定を案内するように、迷いやすい順番から先に直すことが効きます。",
        ]
    if "判断" in heading_text:
        return [
            "選ぶ判断材料としては、初回設定の整理、担当者別の案内分岐、FAQ整備が一続きで設計されているかを見ておきたいところです。",
            "機能の数より、導入直後の確認負荷をどこまで下げられるかで比べると判断しやすくなります。",
        ]
    if "次の一歩" in heading_text:
        return [
            "まずは初回設定で問い合わせが集まりやすい場面を洗い出し、設定の順番と確認ポイントを一枚にまとめるところから始めると進めやすくなります。",
            "管理者に負荷が偏っているなら、担当者別の案内分岐とFAQ整備を先にそろえると、導入後の迷いを減らしやすくなります。",
        ]
    return []


def _product_intro_body_needs_expansion(sections: Sequence[tuple[str, str]], body: str) -> bool:
    original = str(body or "").strip()
    if not original or len(sections) < 4:
        return False
    single_sentence_sections = sum(
        1 for _heading, section_body in sections if len(_split_japanese_sentences(section_body)) <= 1
    )
    short_sections = sum(1 for _heading, section_body in sections if len(str(section_body or "").strip()) < 150)
    if len(original) < 520:
        return single_sentence_sections >= 2 or short_sections >= 2
    if len(original) < _PRODUCT_INTRO_THIN_BODY_CHAR_LIMIT:
        return single_sentence_sections >= 2 or short_sections >= 3
    return False


def _stabilize_thin_product_intro_body(body: str, contract: Mapping[str, Any] | None = None) -> str:
    original = str(body or "").strip()
    if not original or len(original) >= _PRODUCT_INTRO_THIN_BODY_CHAR_LIMIT or not _is_product_introduction_route(contract):
        return original

    sections = _split_markdown_sections(original)
    if not _product_intro_body_needs_expansion(sections, original):
        return original

    rebuilt_sections: list[str] = []
    changed = False
    normalized_contract = dict(contract or {})
    for heading, section_body in sections:
        support_sentences = _product_intro_support_sentences(
            heading,
            normalized_contract,
            section_body=section_body,
            full_body=original,
        )
        updated_body = _append_unique_sentences(section_body, support_sentences)
        if updated_body != section_body:
            changed = True
        rebuilt_sections.append(f"## {heading}\n\n{updated_body}")

    rebuilt = "\n\n".join(rebuilt_sections).strip()
    if not changed or len(rebuilt) <= len(original):
        return original
    return rebuilt


def _stabilize_thin_source_grounded_body(
    article_type: str,
    body: str,
    contract: Mapping[str, Any] | None = None,
) -> str:
    normalized_type = str(article_type or "").strip().lower()
    if normalized_type == "announcement":
        return _stabilize_thin_announcement_body(body)
    if normalized_type == "case_study":
        return _stabilize_thin_case_study_body(body)
    if normalized_type == "branding":
        return _stabilize_thin_product_intro_body(body, contract)
    return str(body or "").strip()


def _normalize_cross_department_axis_label(value: Any) -> str:
    normalized = str(value or "").strip()
    compact = re.sub(r"[\s_\-]+", "", normalized).lower()
    if compact == "approvalflow":
        return "承認フロー"
    if compact == "ownership":
        return "責任の置き方"
    if compact == "auditability":
        return "監査のしやすさ"
    return _CROSS_DEPARTMENT_AXIS_LABELS.get(normalized, "")


def _cross_department_axis_labels(contract: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    ui_journey = dict(contract.get("ui_journey") or {})
    for item in (
        list(contract.get("comparison_axes") or [])
        + list(ui_journey.get("comparison_axes") or [])
        + list(contract.get("must_cover") or [])
    ):
        label = _normalize_cross_department_axis_label(item)
        if label and label not in labels:
            labels.append(label)
    return labels[:3]


def _is_cross_department_governance_compare(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type != "comparative_review":
        return False
    prompt_probe = " ".join(
        [
            str(contract.get("prompt_raw") or "").strip(),
            str(contract.get("topic") or "").strip(),
            str(contract.get("audience_profile") or "").strip(),
        ]
    )
    if "複数部門" not in prompt_probe:
        return False
    return len(_cross_department_axis_labels(contract)) >= 2


def _cross_department_closing_seed(contract: Mapping[str, Any]) -> str:
    labels = _cross_department_axis_labels(contract)
    if len(labels) >= 3:
        joined = "・".join(labels[:3])
    elif len(labels) == 2:
        joined = "と".join(labels[:2])
    else:
        return ""
    return f"結論では、{joined}を同じ順番で見比べると、部門横断運用で何を優先するかが整理しやすくなります。"


def _cross_department_compatibility_sentence(intent: str, contract: Mapping[str, Any], topic_seed: str) -> str:
    labels = _cross_department_axis_labels(contract)
    first = labels[0] if labels else "承認フロー"
    second = labels[1] if len(labels) > 1 else "責任の置き方"
    third = labels[2] if len(labels) > 2 else "監査のしやすさ"
    mapping = {
        "hook": f"比較条件として、誰が申請し、どこで{first}が止まり、あとから{third}を追う必要があるかを先にそろえます。",
        "criteria": f"評価軸は {first} / {second} / {third} に固定し、導入負荷や価格のような別軸へ途中でずらさないことが重要です。",
        "comparison": f"{first}を細かく分けたい運用、{second}を部門ごとに明確にしたい運用、{third}を優先したい運用では、向くサービス設計が分かれます。",
        "fit": f"少人数で更新を回すなら {first} の軽さが効きやすく、複数部門で差し戻し責任を追うなら {second} と {third} を優先したほうが運用を保ちやすくなります。",
        "caution": f"既存の運用規程や監査要件がある場合は、{first} の段数だけでなく、{second} の持ち方と {third} の保存範囲まで先に確認してください。",
        "closing": _cross_department_closing_seed(contract),
    }
    return mapping.get(intent, topic_seed or f"{first} と {second} の差を軸に整理します。")


def _stabilize_cross_department_comparative_body(body: str, contract: Mapping[str, Any]) -> str:
    original = str(body or "").strip()
    if not original or not _is_cross_department_governance_compare(contract):
        return original
    closing_body = _section_body_after_heading(original, _COMPARATIVE_CLOSING_HEADING)
    if not closing_body:
        return original
    prompt_refs = build_prompt_echo_references(
        user_prompt=str(contract.get("prompt_raw") or contract.get("topic") or ""),
        extra=list(contract.get("must_cover") or []),
        include_must_cover=False,
    )
    prompt_echo_hits = detect_prompt_echo_sentences(
        closing_body,
        references=prompt_refs,
        max_hits=2,
    )
    for sentence in _split_japanese_sentences(closing_body):
        if not _CROSS_DEPARTMENT_PROMPT_ECHO_RE.search(sentence):
            continue
        excerpt = sentence[:140]
        if excerpt not in prompt_echo_hits:
            prompt_echo_hits.append(excerpt)
    if not prompt_echo_hits:
        return original
    replacement = _cross_department_closing_seed(contract)
    if not replacement:
        return original
    filtered_sentences = [
        sentence
        for sentence in _split_japanese_sentences(closing_body)
        if not any(str(hit or "").strip() and str(hit).strip() in sentence for hit in prompt_echo_hits)
    ]
    rebuilt_sentences = [replacement]
    for sentence in filtered_sentences:
        if sentence != replacement:
            rebuilt_sentences.append(sentence)
    rebuilt_body = " ".join(sentence for sentence in rebuilt_sentences if sentence).strip()
    if not rebuilt_body or rebuilt_body == closing_body:
        return original
    return _replace_section_body_after_heading(original, _COMPARATIVE_CLOSING_HEADING, rebuilt_body)


def _merge_case_study_compatibility_body(
    original_body: str,
    compatibility_body: str,
    quality_metrics: Mapping[str, Any],
) -> str:
    original = str(original_body or "").strip()
    fallback = str(compatibility_body or "").strip()
    if not original:
        return fallback
    if not fallback:
        return original

    body_chars = int(quality_metrics.get("body_chars", 0) or 0)
    if body_chars < 1000 and len(original) < 1000:
        return fallback
    if _count_markdown_sections(original) < 4:
        return fallback

    merged = original
    for heading in (
        _CASE_STUDY_RESULT_HEADING,
        _CASE_STUDY_CONDITION_HEADING,
    ):
        section_body = _section_body_after_heading(merged, heading)
        fallback_section = _section_body_after_heading(fallback, heading)
        if not fallback_section:
            continue
        if not section_body:
            merged = f"{merged}\n\n## {heading}\n\n{fallback_section}".strip()
            continue
        if heading == _CASE_STUDY_CONDITION_HEADING and _case_study_condition_signal_count(section_body) <= 0:
            merged = _replace_section_body_after_heading(merged, heading, fallback_section)
    return merged


def _merge_comparative_compatibility_body(
    original_body: str,
    compatibility_body: str,
    quality_metrics: Mapping[str, Any],
) -> str:
    original = str(original_body or "").strip()
    fallback = str(compatibility_body or "").strip()
    if not original:
        return fallback
    if not fallback:
        return original

    body_chars = int(quality_metrics.get("body_chars", 0) or 0)
    if body_chars < 1200 and len(original) < 1200:
        return fallback
    if _count_markdown_sections(original) < 4:
        return fallback

    merged = original
    for heading in (
        "用途別に向く選び方",
        "選ぶ前に確認したい点",
        "結論とおすすめの分け方",
    ):
        if _section_body_after_heading(merged, heading):
            continue
        section_body = _section_body_after_heading(fallback, heading)
        if not section_body:
            continue
        merged = f"{merged}\n\n## {heading}\n\n{section_body}".strip()
    return merged


def _merge_product_intro_compatibility_body(
    original_body: str,
    compatibility_body: str,
    sections: Sequence[Any],
    contract: Mapping[str, Any],
) -> str:
    original = str(original_body or "").strip()
    fallback = str(compatibility_body or "").strip()
    if not original:
        return fallback
    if not fallback or not _is_product_introduction_route(contract):
        return original

    planned_headings = [
        _normalize_heading_text(getattr(section, "heading", "") or "")
        for section in list(sections)[:6]
        if _normalize_heading_text(getattr(section, "heading", "") or "")
    ]
    if not planned_headings:
        return original

    original_sections = dict(_split_markdown_sections(original))
    missing_headings = [heading for heading in planned_headings if heading not in original_sections]
    if not missing_headings:
        return original

    fallback_sections = dict(_split_markdown_sections(fallback))
    rebuilt_sections: list[str] = []
    for heading in planned_headings:
        section_body = original_sections.get(heading) or fallback_sections.get(heading) or ""
        if not section_body:
            continue
        rebuilt_sections.append(f"## {heading}\n\n{section_body}")
    rebuilt = "\n\n".join(rebuilt_sections).strip()
    return rebuilt or original


def _needs_compatibility_rebuild(
    body: str,
    title: str,
    contract: Mapping[str, Any],
    compatibility_mode: str,
    quality_metrics: Mapping[str, Any],
) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    if not str(body or "").strip():
        return True
    if compatibility_mode == "offline_deterministic" and title.strip() == _GENERIC_COMPAT_TITLE:
        return True
    if article_type == "announcement":
        if any(fragment in str(body or "") for fragment in ("更するお知らせ", "cautionを", "closingを")):
            return True
        if compatibility_mode == "offline_deterministic" and "公式情報で確認すべき項目" not in str(body or ""):
            return True
    if article_type == "branding":
        if title.strip() == _GENERIC_COMPAT_TITLE:
            return True
        if list(contract.get("source_grounding_items") or []) and float(quality_metrics.get("source_grounding_reflection_ratio", 0.0) or 0.0) < 0.5:
            return True
    if article_type == "case_study":
        if _count_markdown_sections(str(body or "")) < 3:
            return True
        condition_signal_count = max(
            int(quality_metrics.get("case_result_condition_sentence_count", 0) or 0),
            _case_study_condition_signal_count(body),
        )
        if condition_signal_count <= 0:
            return True
    if article_type == "comparative_review":
        section_count = _count_markdown_sections(body)
        body_chars = int(quality_metrics.get("body_chars", 0) or 0)
        if section_count < 4:
            return True
        if compatibility_mode == "offline_deterministic" and body_chars < 1200 and len(str(body or "")) < 1200:
            return True
        fit_sentence_count = int(quality_metrics.get("comparative_fit_sentence_count", 0) or 0)
        if not _comparative_has_closing_signal(str(body or "")) and fit_sentence_count <= 0:
            return True
    return False


def _preserve_required_section_body(article_type: str, final_body: str, fallback_body: str) -> str:
    heading = _SECTION_HEADING_BY_TYPE.get(article_type)
    if not heading:
        return final_body
    if _section_body_after_heading(final_body, heading):
        return final_body
    if _section_body_after_heading(fallback_body, heading):
        return fallback_body
    return final_body


def _editor_report_to_dict(report_obj: Any) -> Dict[str, Any]:
    if hasattr(report_obj, "__dataclass_fields__"):
        return asdict(report_obj)
    return dict(report_obj or {})


def _apply_compatibility_rebuild(
    *,
    article_type: str,
    body: str,
    title: str,
    contract: Mapping[str, Any],
    sections: Sequence[Any],
    compatibility_mode: str,
    quality_metrics: Mapping[str, Any],
) -> tuple[str, bool, str]:
    compatibility_rebuild = _needs_compatibility_rebuild(
        body,
        title,
        contract,
        compatibility_mode,
        quality_metrics,
    )
    if not compatibility_rebuild:
        return str(body or ""), False, ""

    compatibility_fallback_body = _build_compatibility_body(contract, sections)
    if article_type == "comparative_review":
        compatibility_body = _merge_comparative_compatibility_body(
            body,
            compatibility_fallback_body,
            quality_metrics,
        )
    elif article_type == "case_study":
        compatibility_body = _merge_case_study_compatibility_body(
            body,
            compatibility_fallback_body,
            quality_metrics,
        )
    else:
        compatibility_body = compatibility_fallback_body
    return str(compatibility_body or body or "").strip(), True, compatibility_fallback_body


def _apply_article_type_postprocess(
    *,
    article_type: str,
    final_body: str,
    contract: Mapping[str, Any],
    sections: Sequence[Any],
    section_generation_body: str,
    compatibility_fallback_body: str,
    editor_report: Mapping[str, Any],
) -> tuple[str, Dict[str, Any], str]:
    updated_body = _preserve_required_section_body(article_type, final_body, section_generation_body)
    merged_editor_report = dict(editor_report or {})
    fallback_body = str(compatibility_fallback_body or "").strip()

    if article_type == "branding":
        if not fallback_body and _is_product_introduction_route(contract):
            fallback_body = _build_compatibility_body(contract, sections)
        updated_body = _merge_product_intro_compatibility_body(
            updated_body,
            fallback_body or section_generation_body,
            sections,
            contract,
        )

    if article_type == "announcement":
        if not fallback_body:
            fallback_body = _build_compatibility_body(contract, sections)
        updated_body = _stabilize_announcement_source_grounded_sections(updated_body, fallback_body, contract)
        updated_body = _stabilize_announcement_prompt_echo_body(updated_body, contract)
        updated_body, announcement_editor_report_obj = apply_minimal_editor_guard(updated_body)
        merged_editor_report = _merge_editor_reports(
            merged_editor_report,
            _editor_report_to_dict(announcement_editor_report_obj),
        )

    if article_type == "comparative_review":
        updated_body = _stabilize_cross_department_comparative_body(updated_body, contract)
        updated_body, comparative_editor_report_obj = apply_minimal_editor_guard(updated_body)
        merged_editor_report = _merge_editor_reports(
            merged_editor_report,
            _editor_report_to_dict(comparative_editor_report_obj),
        )

    if article_type == "case_study":
        if not fallback_body:
            fallback_body = _build_compatibility_body(contract, sections)
        updated_body = _stabilize_case_study_final_body(updated_body, fallback_body)
        updated_body, case_study_editor_report_obj = apply_minimal_editor_guard(updated_body)
        merged_editor_report = _merge_editor_reports(
            merged_editor_report,
            _editor_report_to_dict(case_study_editor_report_obj),
        )

    stabilized_short_body = _stabilize_thin_source_grounded_body(article_type, updated_body, contract)
    if stabilized_short_body != updated_body:
        updated_body, short_body_editor_report_obj = apply_minimal_editor_guard(stabilized_short_body)
        merged_editor_report = _merge_editor_reports(
            merged_editor_report,
            _editor_report_to_dict(short_body_editor_report_obj),
        )

    return updated_body, merged_editor_report, fallback_body


def _merge_formatted_result(result: Dict[str, Any], formatted: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(result)
    merged["title"] = str(formatted.get("title") or "")
    merged["lead"] = str(formatted.get("lead") or "")
    merged["body"] = str(formatted.get("body") or "")
    merged["full_body"] = str(formatted.get("full_body") or "")
    merged["references"] = str(formatted.get("references") or "")
    hashtags = str(merged.get("hashtags") or "").strip()
    merged["hashtags"] = hashtags
    full_text_parts = [merged["title"], merged["full_body"]]
    if hashtags:
        full_text_parts.extend(["---", hashtags])
    merged["full_text"] = "\n\n".join(part for part in full_text_parts if part).strip()
    return merged


def _normalize_inherited_tagged_result(result: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = dict(result or {})
    raw_seed = next(
        (
            text
            for text in (
                str(normalized.get("full_text") or ""),
                "\n".join(
                    str(normalized.get(key) or "")
                    for key in ("title", "lead", "body", "hashtags")
                    if str(normalized.get(key) or "").strip()
                ),
            )
            if _TAG_BLOCK_RE.search(text) or _PROMPT_CONTROL_TAG_RE.search(text)
        ),
        "",
    )
    if not raw_seed:
        return normalized

    title_marker_index = raw_seed.upper().find("[TITLE]")
    body_marker_index = raw_seed.upper().find("[BODY]")
    if title_marker_index >= 0:
        raw_seed = raw_seed[title_marker_index:]
    elif body_marker_index >= 0:
        raw_seed = raw_seed[body_marker_index:]

    parsed = parse_tagged_output(raw_seed)

    def _extract_tagged_value(tag: str, *, multiline: bool = False) -> str:
        pattern = re.compile(
            rf"\[{tag}\]\s*([\s\S]*?)(?=\[/{tag}\]|\[(?:TITLE|LEAD|BODY|HASHTAGS|ROLE|ISSUES|SOURCE)\]|\Z)",
            re.IGNORECASE,
        )
        match = pattern.search(raw_seed)
        if not match:
            return ""
        value = str(match.group(1) or "").strip()
        if multiline:
            return "\n".join(line.strip() for line in value.splitlines() if line.strip()).strip()
        return re.sub(r"\s+", " ", value).strip()

    normalized_title = parsed.title or _extract_tagged_value("TITLE")
    normalized_lead = parsed.lead or _extract_tagged_value("LEAD")
    normalized_body = parsed.body or _extract_tagged_value("BODY", multiline=True)
    normalized_hashtags = parsed.hashtags or _extract_tagged_value("HASHTAGS")

    if normalized_title:
        normalized["title"] = normalized_title
    if normalized_lead:
        normalized["lead"] = normalized_lead
    if normalized_body:
        normalized["body"] = normalized_body
    if normalized_hashtags:
        normalized["hashtags"] = normalized_hashtags

    references = str(normalized.get("references") or "").strip()
    hashtags = str(normalized.get("hashtags") or "").strip()
    full_body = "\n\n".join(
        part
        for part in (
            str(normalized.get("lead") or "").strip(),
            str(normalized.get("body") or "").strip(),
            references,
        )
        if part
    ).strip()
    full_text_parts = [str(normalized.get("title") or "").strip(), full_body]
    if hashtags:
        full_text_parts.extend(["---", hashtags])
    normalized["full_body"] = full_body
    normalized["full_text"] = "\n\n".join(part for part in full_text_parts if part).strip()
    return normalized


def _build_error_result(
    *,
    contract: Dict[str, Any],
    reason_code: str,
    message: str,
    security_gate: Dict[str, Any],
    runtime: Dict[str, Any],
    warnings: list[str],
) -> Dict[str, Any]:
    pipeline_check = build_pipeline_check(
        contract=contract,
        discourse_plan=[],
        dedupe_audit={},
        editor_report={},
        legal_report={},
        retries=0,
        fallback_used=False,
        warnings=list(warnings),
        style_profile=_default_style_profile(contract),
        quality_metrics={},
        need_question=dict(contract.get("need_question", {}) or {}),
        security_gate=security_gate,
        runtime=runtime,
    )
    pipeline_check["error"] = {"reason_code": reason_code, "message": message}
    result = {
        "success": False,
        "title": "",
        "lead": "",
        "body": "",
        "references": "",
        "hashtags": "",
        "full_text": "",
        "reason_code": reason_code,
        "runtime_reason_code": reason_code,
        "runtime_error_class": (
            "policy" if str(reason_code).startswith(("POL_", "SEC_"))
            else "user_input" if str(reason_code).startswith("INP_")
            else "system"
        ),
        "needs_input_items": list(dict(contract.get("input_decision") or {}).get("needs_input_items", []) or []),
        "pipeline_check": pipeline_check,
        "quality_pipeline_check": _default_quality_check(),
    }
    append_audit_record(
        {
            "reason_code": reason_code,
            "article_type": str(contract.get("article_type") or "unknown"),
            "media": str(contract.get("media") or "note"),
            "fallback_used": False,
            "warnings": list(warnings),
            "security_gate": security_gate,
            "runtime": runtime,
            "quality_metrics": {},
        }
    )
    return result


def _normalize_runtime_error_reason(reason_code: str, message: str) -> str:
    normalized_reason = str(reason_code or "").strip() or error_codes.SYS_PIPELINE_FAILURE
    error_message = str(message or "")
    if "TRN_UPSTREAM_5XX" in error_message:
        return error_codes.TRN_PRIMARY_MODEL_UPSTREAM_5XX
    return normalized_reason


class MinimalPipeline(QualityObservabilityMixin, _RuntimeMinimalPipeline):
    def __init__(self, llm_client=None) -> None:
        self._llm_client_missing = llm_client is None
        self._compatibility_mode = "offline_deterministic" if llm_client is None else "llm"
        super().__init__(llm_client=_wrap_llm_client(llm_client))

    def _maybe_build_compact_plan(
        self,
        contract: Mapping[str, Any],
        source_pack: Mapping[str, Any],
    ) -> list[Dict[str, str]]:
        bridged_plan = _build_compact_plan_bridge_from_discourse_sections(
            contract,
            build_discourse_plan(contract),
        )
        if bridged_plan:
            return bridged_plan
        return super()._maybe_build_compact_plan(contract, source_pack)

    def _build_quality_context(
        self,
        contract: Dict[str, Any],
        style_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        source_text = "\n".join(
            str(dict(item).get("content") or "")
            for item in list(contract.get("source_documents") or [])[:4]
            if isinstance(item, Mapping)
        )
        return {
            "platform": "note",
            "perspective": str(contract.get("perspective") or ""),
            "writing_focus": str(contract.get("writing_focus") or ""),
            "article_type": str(contract.get("article_type") or ""),
            "style_profile_hint": str(style_profile.get("profile_name") or ""),
            "tone_profile_hint": str(contract.get("tone_profile") or ""),
            "allow_experience": bool(contract.get("allow_experience")),
            "topic_hint": str(contract.get("topic_statement") or contract.get("topic") or ""),
            "writing_intent": str(contract.get("core_message") or contract.get("topic_statement") or ""),
            "target_audience": str(contract.get("audience_profile") or ""),
            "source_urls": list(contract.get("source_inputs") or contract.get("source") or []),
            "source_text": source_text,
        }

    def _apply_resonance_pass(
        self,
        text: str,
        contract: Dict[str, Any],
        style_profile: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        return str(text or ""), {
            "enabled": False,
            "applied": False,
            "phases_applied": [],
            "phase_effect_metrics": {},
            "reason": "compat_noop",
        }

    def _stage_metrics(
        self,
        text: str,
        sections: Sequence[Any],
        contract: Dict[str, Any],
        style_profile: Dict[str, Any],
        *,
        editor_report: Dict[str, Any] | None = None,
        legal_result: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        metrics = self._build_quality_metrics(
            str(text or ""),
            list(sections),
            contract,
            style_profile,
            legal_result=legal_result,
            editor_report=editor_report,
        )
        return {
            "sentence_integrity_warning_count": int(metrics.get("sentence_integrity_warning_count", 0) or 0),
            "comparative_axis_shift_count": int(metrics.get("comparative_axis_shift_count", 0) or 0),
            "connective_opening_rate": float(metrics.get("connective_opening_rate", 0.0) or 0.0),
        }

    def _build_comparative_stage_diagnostic(
        self,
        *,
        article_type: str,
        sections: Sequence[Any],
        contract: Dict[str, Any],
        style_profile: Dict[str, Any],
        stage_bodies: Mapping[str, str],
        editor_report: Dict[str, Any],
        legal_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        if article_type != "comparative_review":
            return {
                "enabled": False,
                "reason": "article_type_not_supported",
                "stage_order": [],
                "changed_stage_names": [],
                "first_changed_stage": "",
                "stages": [],
            }
        ordered_names = [
            "section_generation",
            "after_dedupe",
            "after_editor_guard",
            "after_resonance",
            "after_quality",
            "final_body",
        ]
        stages: list[Dict[str, Any]] = []
        previous = ""
        changed_stage_names: list[str] = []
        for name in ordered_names:
            body = str(stage_bodies.get(name) or "")
            stage_editor_report = editor_report if name in {"after_editor_guard", "after_resonance", "after_quality", "final_body"} else {}
            stage_legal_result = legal_result if name == "final_body" else {}
            changed = bool(stages) and body != previous
            if changed:
                changed_stage_names.append(name)
            stages.append(
                {
                    "stage": name,
                    "body": body,
                    "metrics": self._stage_metrics(
                        body,
                        sections,
                        contract,
                        style_profile,
                        editor_report=stage_editor_report,
                        legal_result=stage_legal_result,
                    ),
                    "changed_vs_previous": changed,
                }
            )
            previous = body
        return {
            "enabled": True,
            "reason": "",
            "stage_order": ordered_names,
            "changed_stage_names": changed_stage_names,
            "first_changed_stage": changed_stage_names[0] if changed_stage_names else "",
            "stages": stages,
        }

    def generate(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        normalized_payload = _normalize_payload(payload)
        try:
            resolved = resolve_input_contract(normalized_payload)
            contract = _hydrate_compatibility_source_documents(dict(resolved.contract or {}))
            security_gate = dict(resolved.security_gate or {})
            warnings = list(resolved.warnings or [])
        except PromptInjectionBlockedError as exc:
            partial_contract = _hydrate_compatibility_source_documents(dict(exc.partial_contract or normalized_payload))
            return _build_error_result(
                contract=partial_contract,
                reason_code=str(getattr(exc, "reason_code", "") or error_codes.SEC_PROMPT_INJECTION_BLOCKED),
                message=str(exc),
                security_gate=dict(getattr(exc, "security_gate", {}) or {"decision": "block"}),
                runtime=_build_runtime_block(
                    {},
                    article_type=str(partial_contract.get("article_type") or ""),
                    compatibility_mode=self._compatibility_mode,
                ),
                warnings=[],
            )
        except InputContractValidationError as exc:
            error = to_input_error(exc)
            contract = _normalize_payload(normalized_payload)
            return _build_error_result(
                contract=contract,
                reason_code=str(error.get("reason_code") or error_codes.INP_MISSING_REQUIRED),
                message=str(error.get("message") or str(exc)),
                security_gate={"decision": "pass", "blocked_input_fields": [], "blocked_patterns": []},
                runtime=_build_runtime_block(
                    {},
                    article_type=str(contract.get("article_type") or ""),
                    compatibility_mode=self._compatibility_mode,
                ),
                warnings=[],
            )

        requested_experiment = _normalize_body_generation_experiment(
            normalized_payload.get("body_generation_experiment") or contract.get("body_generation_experiment")
        )
        if requested_experiment:
            contract["body_generation_experiment"] = requested_experiment
        article_type = str(contract.get("article_type") or "").strip().lower()
        style_profile = _default_style_profile(contract)
        sections = list(build_discourse_plan(contract))
        discourse_plan = _serialize_discourse_plan(sections)
        planning_gate = _evaluate_planning_opt_in_gate(
            contract,
            sections,
            requested_experiment=requested_experiment,
        )
        section_generation_state = _resolve_section_generation_state(
            contract,
            sections,
            requested_experiment=requested_experiment,
        )
        hierarchical_ab_summary = (
            _build_hierarchical_ab_summary(contract, sections, section_generation_state)
            if section_generation_state
            else {}
        )
        runtime = _build_runtime_block({}, article_type=article_type, compatibility_mode=self._compatibility_mode)
        input_decision = dict(contract.get("input_decision") or {})
        action = str(input_decision.get("action") or "accept").strip().lower()
        if action in {"clarify", "block"}:
            reason_code = str(input_decision.get("reason_code") or "").strip()
            if not reason_code:
                reason_code = (
                    error_codes.INP_NEEDS_CLARIFICATION
                    if action == "clarify"
                    else error_codes.INP_MISSING_REQUIRED
                )
            return _build_error_result(
                contract=contract,
                reason_code=reason_code,
                message=reason_code,
                security_gate=security_gate,
                runtime=runtime,
                warnings=warnings,
            )

        strict_mode = str(contract.get("strict_saas_mode") or "").strip().lower()
        if self._llm_client_missing and strict_mode in _STRICT_LLM_REQUIRED_MODES:
            return _build_error_result(
                contract=contract,
                reason_code=error_codes.SYS_LLM_CLIENT_REQUIRED,
                message="LLM client is required in strict SaaS mode",
                security_gate=security_gate,
                runtime=runtime,
                warnings=warnings,
            )

        runtime_check: Dict[str, Any]
        body_retries = 0
        body_fallback_used = False
        section_ledgers: list[Dict[str, Any]] = []
        if bool(section_generation_state.get("enabled")):
            try:
                section_generation = generate_sections(
                    topic=str(contract.get("topic") or contract.get("topic_statement") or ""),
                    media=str(contract.get("media") or "note"),
                    sections=sections,
                    contract=contract,
                    llm_client=None if self._llm_client_missing else self.llm_client,
                )
            except SectionGenerationRuntimeError as exc:
                section_generation_state = {
                    **section_generation_state,
                    "fallback_to_super": True,
                    "fallback_reason": str(getattr(exc, "reason_code", "") or error_codes.SYS_PIPELINE_FAILURE),
                }
                result = super().generate(contract)
                result = _normalize_inherited_tagged_result(result)
                runtime_check = _extract_runtime_check(result)
                primary_call = _extract_primary_call(runtime_check)
                runtime = _build_runtime_block(primary_call, article_type=article_type, compatibility_mode=self._compatibility_mode)
                body_fallback_used = True
            else:
                result = _build_success_result_seed()
                runtime_check = {
                    "body_generation": {
                        "repair_applied": False,
                        "repair_trigger_score": 0.0,
                        "primary_call": dict(section_generation.runtime or {}),
                    },
                    "quality_metrics": {},
                    "editor_report": {},
                    "ai_index": {},
                    "legal_summary": {},
                    "output_guard": {},
                }
                primary_call = dict(section_generation.runtime or {})
                runtime = _build_runtime_block(primary_call, article_type=article_type, compatibility_mode=self._compatibility_mode)
                section_generation_body = str(section_generation.body or "")
                body_retries = int(section_generation.retries or 0)
                body_fallback_used = bool(section_generation.fallback_used)
                section_ledgers = [dict(item) for item in list(section_generation.section_ledgers or [])]
        else:
            result = super().generate(contract)
            result = _normalize_inherited_tagged_result(result)
            runtime_check = _extract_runtime_check(result)
            primary_call = _extract_primary_call(runtime_check)
            runtime = _build_runtime_block(primary_call, article_type=article_type, compatibility_mode=self._compatibility_mode)
        primary_generation = _build_primary_generation_summary(
            section_state=section_generation_state,
            runtime_check=runtime_check,
            retries=body_retries,
            fallback_used=body_fallback_used,
        )
        quality_contract = _quality_contract_from_runtime_check(runtime_check, contract)

        if not bool(result.get("success")):
            raw_reason_code = str(result.get("reason_code") or result.get("runtime_reason_code") or error_codes.SYS_PIPELINE_FAILURE)
            error_message = str(dict(runtime_check.get("error") or {}).get("message") or raw_reason_code)
            reason_code = _normalize_runtime_error_reason(raw_reason_code, error_message)
            result["reason_code"] = reason_code
            result["runtime_reason_code"] = reason_code
            pipeline_check = build_pipeline_check(
                contract=contract,
                discourse_plan=discourse_plan,
                dedupe_audit={},
                editor_report={},
                legal_report={},
                retries=0,
                fallback_used=False,
                warnings=warnings,
                style_profile=style_profile,
                quality_metrics={},
                need_question=dict(contract.get("need_question", {}) or {}),
                security_gate=security_gate,
                runtime=runtime,
            )
            if hierarchical_ab_summary:
                pipeline_check["body_generation"] = {
                    **dict(pipeline_check.get("body_generation") or {}),
                    "hierarchical_ab": hierarchical_ab_summary,
                }
            pipeline_check["body_generation"] = _build_body_generation_telemetry(
                contract=contract,
                runtime_check=runtime_check,
                primary_generation=primary_generation,
                section_state=section_generation_state,
                planning_gate=planning_gate,
                style_profile=style_profile,
                sections=sections,
                output_body=str(result.get("body") or ""),
                compatibility_rebuild=False,
            )
            if hierarchical_ab_summary:
                pipeline_check["body_generation"]["hierarchical_ab"] = hierarchical_ab_summary
            inherited_error = dict(runtime_check.get("error") or {})
            error_payload = {"reason_code": reason_code, "message": error_message}
            for key, value in inherited_error.items():
                if key in error_payload:
                    continue
                error_payload[str(key)] = value
            pipeline_check["error"] = error_payload
            result["pipeline_check"] = pipeline_check
            result["quality_pipeline_check"] = _default_quality_check()
            append_audit_record(
                {
                    "reason_code": reason_code,
                    "article_type": article_type or "unknown",
                    "media": str(contract.get("media") or "note"),
                    "fallback_used": False,
                    "warnings": warnings,
                    "security_gate": security_gate,
                    "runtime": runtime,
                    "quality_metrics": {},
                }
            )
            return result

        if not bool(section_generation_state.get("enabled")) or bool(section_generation_state.get("fallback_to_super")):
            section_generation_body = str(result.get("body") or "")
        initial_quality_metrics = self._build_quality_metrics(
            section_generation_body,
            sections,
            quality_contract,
            style_profile,
            legal_result={"citation_guard": dict(runtime_check.get("legal_summary") or {}).get("citation_guard", {})},
            editor_report=dict(runtime_check.get("editor_report") or {}),
        )
        section_generation_body, compatibility_rebuild, compatibility_fallback_body = _apply_compatibility_rebuild(
            article_type=article_type,
            body=section_generation_body,
            title=str(result.get("title") or ""),
            contract=quality_contract,
            sections=sections,
            compatibility_mode=self._compatibility_mode,
            quality_metrics=initial_quality_metrics,
        )

        deduped_body, dedupe_audit = run_semantic_dedupe(section_generation_body, contract)
        dedupe_audit = dict(dedupe_audit or {})
        dedupe_audit.setdefault("regenerated_paragraphs", 0)

        editor_body, editor_report_obj = apply_minimal_editor_guard(deduped_body)
        editor_report = _editor_report_to_dict(editor_report_obj)
        stage_diagnostic_editor_report = dict(editor_report)

        resonance_body, resonance_report = self._apply_resonance_pass(editor_body, contract, style_profile)
        quality_body, quality_check = self._apply_quality_pass(resonance_body, contract, style_profile)
        legal_result = run_legal_postcheck(quality_body, verified_texts=_verified_source_texts(contract))
        final_body = normalize_output_body(str(legal_result.get("checked_text") or quality_body), contract)
        final_body, editor_report, compatibility_fallback_body = _apply_article_type_postprocess(
            article_type=article_type,
            final_body=final_body,
            contract=contract,
            sections=sections,
            section_generation_body=section_generation_body,
            compatibility_fallback_body=compatibility_fallback_body,
            editor_report=editor_report,
        )
        if article_type == "case_study":
            dedupe_audit = _normalize_case_study_dedupe_audit_after_stabilization(dedupe_audit, final_body)

        formatter_contract = contract
        if (
            article_type == "branding"
            and str(quality_contract.get("semantic_article_key") or "").strip().lower()
            == "company_introduction"
        ):
            formatter_contract = quality_contract
        formatted = format_output(
            topic=str(contract.get("topic") or contract.get("topic_statement") or ""),
            article_type=article_type,
            body=final_body,
            source_inputs=list(contract.get("source_inputs") or contract.get("source") or []),
            contract=formatter_contract,
            existing_title=str(result.get("title") or ""),
            existing_lead=str(result.get("lead") or ""),
        )
        output_formatter_telemetry = dict(formatted.get("format_telemetry") or {})
        result = _merge_formatted_result(result, formatted)

        merged_warnings = _merge_warning_list(
            warnings,
            list(legal_result.get("warnings") or []),
            list(editor_report.get("warnings") or []),
        )
        legal_summary = dict(runtime_check.get("legal_summary") or {})
        legal_summary.update(
            {
                "warnings": list(legal_result.get("warnings") or []),
                "risk_level": str(legal_result.get("risk_level") or legal_summary.get("risk_level") or "none"),
                "issue_count": int(legal_result.get("issue_count") or legal_summary.get("issue_count") or 0),
                "citation_guard": dict(legal_result.get("citation_guard") or legal_summary.get("citation_guard") or {}),
            }
        )
        quality_metrics = _merge_quality_metrics(
            dict(runtime_check.get("quality_metrics") or {}),
            self._build_quality_metrics(
                final_body,
                sections,
                quality_contract,
                style_profile,
                legal_result=legal_result,
                editor_report=editor_report,
            ),
        )
        hard_soft_eval, contextual_naturalness_report, final_quality_eval = self._build_quality_evaluations(
            quality_check,
            quality_metrics,
        )
        pipeline_check = build_pipeline_check(
            contract=quality_contract,
            discourse_plan=discourse_plan,
            dedupe_audit=dedupe_audit,
            editor_report=editor_report,
            legal_report={"legal_summary": legal_summary},
            retries=body_retries,
            fallback_used=body_fallback_used,
            warnings=merged_warnings,
            style_profile=style_profile,
            quality_metrics=quality_metrics,
            need_question=dict(quality_contract.get("need_question", {}) or {}),
            security_gate=security_gate,
            runtime=runtime,
        )
        pipeline_check["body_generation"] = _build_body_generation_telemetry(
            contract=quality_contract,
            runtime_check=runtime_check,
            primary_generation=primary_generation,
            section_state=section_generation_state,
            planning_gate=planning_gate,
            style_profile=style_profile,
            sections=sections,
            output_body=str(result.get("body") or ""),
            compatibility_rebuild=compatibility_rebuild,
        )
        pipeline_class_path = f"{type(self).__module__}.{type(self).__qualname__}"
        pipeline_check["body_generation"]["pipeline_class"] = pipeline_class_path
        pipeline_check["body_generation"]["pipeline_module"] = type(self).__module__
        pipeline_check["body_generation"]["formatter_applied"] = bool(
            output_formatter_telemetry.get("formatter_applied")
        )
        pipeline_check["body_generation"]["output_formatter"] = output_formatter_telemetry
        pipeline_check["body_generation"]["compatibility_rebuild_applied"] = compatibility_rebuild
        if section_generation_state:
            pipeline_check["body_generation"]["hierarchical_ab"] = _build_hierarchical_ab_summary(
                contract,
                sections,
                section_generation_state,
                section_ledgers=section_ledgers,
            )
        pipeline_check["ai_index"] = dict(runtime_check.get("ai_index") or {})
        pipeline_check["legal_summary"] = legal_summary
        pipeline_check["output_guard"] = dict(runtime_check.get("output_guard") or result.get("output_guard") or {})
        pipeline_check["hard_soft_eval"] = hard_soft_eval
        pipeline_check["contextual_naturalness_report"] = contextual_naturalness_report
        pipeline_check["final_quality_eval"] = final_quality_eval
        pipeline_check["output_guard_inputs"] = {
            "hard_soft_eval": hard_soft_eval,
            "contextual_naturalness_report": contextual_naturalness_report,
            "final_quality_eval": final_quality_eval,
            "contract_alignment": dict(pipeline_check.get("contract_alignment") or {}),
            "proposition_density": {},
            "ai_index": dict(runtime_check.get("ai_index") or {}),
            "legal_summary": legal_summary,
        }
        pipeline_check["resonance_report"] = resonance_report
        pipeline_check["comparative_stage_diagnostic"] = self._build_comparative_stage_diagnostic(
            article_type=article_type,
            sections=sections,
            contract=quality_contract,
            style_profile=style_profile,
            stage_bodies={
                "section_generation": section_generation_body,
                "after_dedupe": deduped_body,
                "after_editor_guard": editor_body,
                "after_resonance": resonance_body,
                "after_quality": quality_body,
                "final_body": final_body,
            },
            editor_report=stage_diagnostic_editor_report,
            legal_result=legal_result,
        )

        result["pipeline_check"] = pipeline_check
        result["quality_pipeline_check"] = quality_check
        result["legal_postcheck"] = legal_result
        append_audit_record(
            {
                "reason_code": str(result.get("reason_code") or "OK"),
                "article_type": article_type or "unknown",
                "media": str(quality_contract.get("media") or "note"),
                "fallback_used": body_fallback_used,
                "warnings": merged_warnings,
                "quality_metrics": quality_metrics,
                "security_gate": security_gate,
                "runtime": runtime,
            }
        )
        return result


__all__ = [
    "MinimalPipeline",
    "PipelineRuntimeError",
]
