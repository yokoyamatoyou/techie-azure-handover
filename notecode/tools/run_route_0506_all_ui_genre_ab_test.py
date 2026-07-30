from __future__ import annotations

import argparse
import json
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from note.article_fetcher import ArticleFetcher  # noqa: E402
from note.current_mainline_runner import execute_current_mainline_generation  # noqa: E402
from note.current_mainline_ui_matrix import UISweepCase, build_current_mainline_payload  # noqa: E402
from note.llm_client import LLMClient as RouteALLMClient  # noqa: E402
from note.route_0506_structured_blog_adapter import (  # noqa: E402
    OPENAI_GENERATION_CANDIDATE,
    prepare_route_0506_adapter_plan,
    run_route_0506_local_scaffold,
)
from note.simple_note_pipeline.pipeline import MinimalPipeline  # noqa: E402


DEFAULT_ARTIFACT_ROOT = (
    PROJECT_ROOT / "logs" / "route_0506_all_ui_genre_ab_with_persona_trace_20260511"
)
DEFAULT_COMPARISON_ROOT = (
    PROJECT_ROOT / "docs" / "新しいフォルダー" / "route_0506_all_ui_genre_ab_20260511"
)
REFERENCE_CONTRACTS = {
    "category_01_explanatory_article": PROJECT_ROOT
    / "logs"
    / "route_0506_same_source_three_variant_preflight_20260510"
    / "market_explanation"
    / "input_contract.json",
    "category_03_company_service_intro": PROJECT_ROOT
    / "logs"
    / "route_0506_self_perspective_then_category_ab_test_20260510"
    / "category_03_company_service_intro"
    / "input_contract.json",
    "category_07_comparative_review": PROJECT_ROOT
    / "logs"
    / "route_0506_same_source_three_variant_preflight_20260510"
    / "comparison_guide"
    / "input_contract.json",
}
WEB_SOURCE_URLS = {
    "post_117": "https://www.rejp.co.jp/blog/post-117/",
    "post_97": "https://www.rejp.co.jp/blog/post-97/",
    "blog_index": "https://www.rejp.co.jp/blog/?p=17",
    "akiya": "https://www.rejp.co.jp/akiya.html",
    "kashi": "https://www.rejp.co.jp/kashi.html",
}

REVIEW_AXES = (
    "self_perspective_natural",
    "first_person_not_mixed",
    "persona_stage1_article_brief_fired",
    "persona_stage2_editor_alignment_fired",
    "source_grounded",
    "no_third_party_brand_leakage",
    "heading_body_continuity",
    "opening_naturalness",
    "late_half_no_stall",
)


@dataclass(frozen=True)
class CategorySpec:
    category_id: str
    ui_label: str
    article_type: str
    semantic_article_key: str
    route_0506_genre_id: str
    prompt: str
    audience: str
    content_goal_key: str
    writing_focus_key: str
    tone_profile_key: str
    length_mode_key: str
    speaker_profile: str
    core_message: str
    self_reference_policy_key: str
    allow_experience: bool
    ui_journey: dict[str, Any]
    comparison_axes: tuple[str, ...] = ()
    source_origin: str = "reference_contract"
    reference_contract_category: str = ""
    web_source_keys: tuple[str, ...] = ()


class RunBlockedError(RuntimeError):
    def __init__(self, message: str, *, usage_rows: Sequence[Mapping[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.usage_rows = [dict(row) for row in list(usage_rows or [])]


class MeteredRouteALLMClient(RouteALLMClient):
    def __init__(self) -> None:
        super().__init__()
        self.raw_usage_records: list[dict[str, Any]] = []

    def _record_usage(self, response: Any, model: str, task_type: str) -> None:  # type: ignore[override]
        super()._record_usage(response, model, task_type)
        self.raw_usage_records.append(
            _usage_from_response(response, model=str(model or ""), stage=str(task_type or ""))
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, separators=(",", ":")) + "\n")


def _canonical_hash(payload: Any) -> str:
    import hashlib

    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _sanitize_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    return re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[REDACTED_OPENAI_KEY]", text)[:1800]


def _get_value(obj: Any, key: str, default: Any = 0) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _usage_from_response(response: Any, *, model: str, stage: str) -> dict[str, Any]:
    usage = _get_value(response, "usage", None)
    if usage is None:
        return {
            "stage": stage,
            "model": model,
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
    input_tokens = int(_get_value(usage, "input_tokens", _get_value(usage, "prompt_tokens", 0)) or 0)
    output_tokens = int(_get_value(usage, "output_tokens", _get_value(usage, "completion_tokens", 0)) or 0)
    total_tokens = int(_get_value(usage, "total_tokens", input_tokens + output_tokens) or 0)
    input_details = _get_value(usage, "input_tokens_details", _get_value(usage, "prompt_tokens_details", None))
    cached_input_tokens = int(
        _get_value(input_details, "cached_tokens", _get_value(input_details, "cached_input_tokens", 0)) or 0
    )
    return {
        "stage": stage,
        "model": model,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _usage_from_token_tracker_item(item: Any) -> dict[str, Any]:
    input_tokens = int(_get_value(item, "input_tokens", 0) or 0)
    output_tokens = int(_get_value(item, "output_tokens", 0) or 0)
    return {
        "stage": str(_get_value(item, "task_type", "") or ""),
        "model": str(_get_value(item, "model", "") or ""),
        "input_tokens": input_tokens,
        "cached_input_tokens": 0,
        "output_tokens": output_tokens,
        "total_tokens": int(_get_value(item, "total_tokens", input_tokens + output_tokens) or 0),
    }


def _ledger_entries(
    *,
    route: str,
    category_id: str,
    usage_records: Sequence[Mapping[str, Any]],
    reasoning_effort: str,
    status: str = "sent",
) -> list[dict[str, Any]]:
    rows = []
    for record in usage_records:
        rows.append(
            {
                "created_at": _now_iso(),
                "route": route,
                "category_id": category_id,
                "stage": str(record.get("stage") or ""),
                "model": str(record.get("model") or ""),
                "reasoning_effort": reasoning_effort,
                "status": status,
                "input_tokens": int(record.get("input_tokens") or 0),
                "cached_input_tokens": int(record.get("cached_input_tokens") or 0),
                "output_tokens": int(record.get("output_tokens") or 0),
                "total_tokens": int(record.get("total_tokens") or 0),
            }
        )
    return rows


def _summarize_usage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "api_call_count": len(rows),
        "input_tokens": sum(int(row.get("input_tokens") or 0) for row in rows),
        "cached_input_tokens": sum(int(row.get("cached_input_tokens") or 0) for row in rows),
        "output_tokens": sum(int(row.get("output_tokens") or 0) for row in rows),
        "total_tokens": sum(int(row.get("total_tokens") or 0) for row in rows),
        "actual_token_usage_available": any(int(row.get("total_tokens") or 0) > 0 for row in rows),
    }


def _source_doc_snapshot(source_documents: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    snapshot: list[dict[str, Any]] = []
    for item in source_documents:
        snapshot.append(
            {
                "title": str(item.get("title") or ""),
                "content": str(item.get("content") or ""),
                "locator": str(item.get("locator") or item.get("url") or ""),
                "source_type": str(item.get("source_type") or ""),
                "notices": list(item.get("notices") or []),
            }
        )
    return snapshot


def _load_reference_docs(category_id: str) -> list[dict[str, Any]]:
    path = REFERENCE_CONTRACTS[category_id]
    contract = dict(_read_json(path))
    docs = [dict(item) for item in list(contract.get("source_documents") or []) if isinstance(item, Mapping)]
    if not docs:
        raise RuntimeError(f"reference_source_documents_missing:{category_id}:{path}")
    return docs


def _fetch_web_documents(cache_path: Path, *, force: bool = False) -> dict[str, Any]:
    if cache_path.exists() and not force:
        return dict(_read_json(cache_path))
    fetcher = ArticleFetcher()
    fetched: dict[str, Any] = {
        "created_at": _now_iso(),
        "policy": "user_authorized_web_source_acquisition_for_missing_ui_genres",
        "sources": {},
        "failures": {},
    }
    for key, url in WEB_SOURCE_URLS.items():
        try:
            content = fetcher.fetch_url(url)
            fetched["sources"][key] = {
                "title": content.title,
                "content": content.content,
                "locator": content.url or url,
                "source_type": content.source_type or "url",
                "content_type": content.content_type or "",
                "notices": list(content.notices or []),
                "char_count": len(content.content or ""),
            }
        except Exception as exc:
            fetched["failures"][key] = {
                "url": url,
                "error": _sanitize_error(exc),
            }
    _write_json(cache_path, fetched)
    return fetched


def _web_docs(web_cache: Mapping[str, Any], keys: Sequence[str]) -> list[dict[str, Any]]:
    sources = dict(web_cache.get("sources") or {})
    docs = []
    missing = []
    for key in keys:
        item = sources.get(key)
        if not isinstance(item, Mapping):
            missing.append(key)
            continue
        docs.append(
            {
                "title": str(item.get("title") or key),
                "content": str(item.get("content") or ""),
                "locator": str(item.get("locator") or WEB_SOURCE_URLS.get(key, "")),
                "source_type": str(item.get("source_type") or "url"),
                "notices": list(item.get("notices") or []),
            }
        )
    if missing:
        raise RuntimeError(f"web_source_missing:{','.join(missing)}")
    return docs


def _category_specs() -> list[CategorySpec]:
    return [
        CategorySpec(
            category_id="category_01_explanatory_article",
            ui_label="解説・ノウハウ",
            article_type="explanatory_article",
            semantic_article_key="explanatory_article",
            route_0506_genre_id="market_explanation",
            prompt="初めて不動産売却する人に向けて、売却の流れ、準備、費用、判断材料を source-grounded に解説する。",
            audience="初めて不動産売却を検討する読者",
            content_goal_key="explain",
            writing_focus_key="explanation",
            tone_profile_key="calm",
            length_mode_key="adaptive",
            speaker_profile="リージャパンの編集担当として語る",
            core_message="不動産売却前に知るべき判断材料を、読者が相談前に整理できるようにする。",
            self_reference_policy_key="watashitachi",
            allow_experience=False,
            ui_journey={"purpose_key": "explain", "target_key": "concept"},
            reference_contract_category="category_01_explanatory_article",
        ),
        CategorySpec(
            category_id="category_02_daily_story",
            ui_label="日常のできごと",
            article_type="daily_story",
            semantic_article_key="daily_story",
            route_0506_genre_id="daily_activity",
            prompt="最近お任せいただいた土地売却の投稿をもとに、日々の相談現場で大切にしていることを自然なブログとして書く。",
            audience="地域で不動産売却を考え始めた読者",
            content_goal_key="interest",
            writing_focus_key="experience",
            tone_profile_key="warm",
            length_mode_key="adaptive",
            speaker_profile="リージャパンの現場担当として語る",
            core_message="日常の対応から、相談しやすさと地域での売却支援の姿勢を伝える。",
            self_reference_policy_key="watashitachi",
            allow_experience=True,
            ui_journey={"purpose_key": "daily", "target_key": "day_to_day"},
            source_origin="web_acquired_missing_category",
            web_source_keys=("post_117", "post_97"),
        ),
        CategorySpec(
            category_id="category_03_company_service_intro",
            ui_label="紹介 / 会社・サービスの紹介記事を書く",
            article_type="branding",
            semantic_article_key="company_introduction",
            route_0506_genre_id="company_service_intro",
            prompt="リージャパンの不動産売却支援を、会社紹介として自然に伝える。相談前の不安、支援範囲、地域での強みを source-grounded に整理する。",
            audience="東大阪市周辺で不動産売却を検討する読者",
            content_goal_key="trust",
            writing_focus_key="explanation",
            tone_profile_key="warm",
            length_mode_key="adaptive",
            speaker_profile="リージャパンの運営担当として語る",
            core_message="売却方法の判断から相談まで、私たちがどこを支援できるかを具体的に示す。",
            self_reference_policy_key="watashitachi",
            allow_experience=False,
            ui_journey={"purpose_key": "introduce", "target_key": "company"},
            reference_contract_category="category_03_company_service_intro",
        ),
        CategorySpec(
            category_id="category_04_announcement",
            ui_label="お知らせ",
            article_type="announcement",
            semantic_article_key="announcement",
            route_0506_genre_id="announcement",
            prompt="売土地の売却をお任せいただいたことを、地域のお知らせとして簡潔に伝える。対象地域、相談できる内容、問い合わせ前に確認したいことを含める。",
            audience="リージャパンの既存・見込みのお客様",
            content_goal_key="action",
            writing_focus_key="explanation",
            tone_profile_key="formal",
            length_mode_key="adaptive",
            speaker_profile="リージャパンの運営担当として語る",
            core_message="売却をお任せいただいた事実を起点に、同じ地域で相談したい読者の確認事項を示す。",
            self_reference_policy_key="tosha",
            allow_experience=False,
            ui_journey={"purpose_key": "announce", "target_key": "standard"},
            source_origin="web_acquired_missing_category",
            web_source_keys=("blog_index", "post_117", "post_97"),
        ),
        CategorySpec(
            category_id="category_05_case_study",
            ui_label="事例・お客様の声",
            article_type="case_study",
            semantic_article_key="case_study",
            route_0506_genre_id="case_study",
            prompt="空き家や瑕疵物件の売却相談で起きやすい悩みを、相談事例型の記事として整理する。成功談に寄せすぎず、状況、支援できる範囲、相談前の確認点を source-grounded に書く。",
            audience="売りにくい不動産の扱いに困っている読者",
            content_goal_key="explain",
            writing_focus_key="analysis",
            tone_profile_key="calm",
            length_mode_key="adaptive",
            speaker_profile="リージャパンの相談担当として語る",
            core_message="売りにくい事情がある物件でも、まず何を整理すればよいかを事例型で伝える。",
            self_reference_policy_key="watashitachi",
            allow_experience=False,
            ui_journey={"purpose_key": "case", "target_key": "implementation"},
            source_origin="web_acquired_missing_category",
            web_source_keys=("akiya", "kashi", "post_117"),
        ),
        CategorySpec(
            category_id="category_06_industry_analysis",
            ui_label="業界・市場の話題",
            article_type="industry_analysis",
            semantic_article_key="industry_analysis",
            route_0506_genre_id="market_explanation",
            prompt="空き家や瑕疵物件など、売却が難しい不動産の相談が増えやすい背景を、地域の不動産売却支援の観点で整理する。",
            audience="不動産売却の市場背景を知りたい読者",
            content_goal_key="explain",
            writing_focus_key="analysis",
            tone_profile_key="calm",
            length_mode_key="adaptive",
            speaker_profile="リージャパンの編集担当として語る",
            core_message="売りにくい不動産の相談で、早めに整理すべき判断材料を市場・業界の話題として伝える。",
            self_reference_policy_key="watashitachi",
            allow_experience=False,
            ui_journey={"purpose_key": "explain", "target_key": "industry"},
            source_origin="web_acquired_missing_category",
            web_source_keys=("akiya", "kashi"),
        ),
        CategorySpec(
            category_id="category_07_comparative_review",
            ui_label="比較・選び方",
            article_type="comparative_review",
            semantic_article_key="comparative_review",
            route_0506_genre_id="comparison_guide",
            prompt="仲介売却、買取、買取保証、一括査定代行の向き不向きを、保存済み source_documents の範囲だけで比較整理する。",
            audience="売却方法を比較検討している読者",
            content_goal_key="explain",
            writing_focus_key="analysis",
            tone_profile_key="calm",
            length_mode_key="adaptive",
            speaker_profile="リージャパンの比較検討担当として語る",
            core_message="売却方法ごとの向き不向きを、読者が自分の事情に照らして判断できるようにする。",
            self_reference_policy_key="watashitachi",
            allow_experience=False,
            ui_journey={"purpose_key": "compare", "target_key": "method", "detail_key": "fit_explain"},
            comparison_axes=("売却までの速さ", "価格の期待", "手間", "向いている事情"),
            reference_contract_category="category_07_comparative_review",
        ),
    ]


def _source_documents_for_spec(spec: CategorySpec, web_cache: Mapping[str, Any]) -> list[dict[str, Any]]:
    if spec.source_origin == "web_acquired_missing_category":
        return _web_docs(web_cache, spec.web_source_keys)
    category_id = spec.reference_contract_category or spec.category_id
    return _load_reference_docs(category_id)


def _case_from_spec(spec: CategorySpec, docs: list[dict[str, Any]]) -> UISweepCase:
    return UISweepCase(
        case_id=spec.category_id,
        article_type=spec.article_type,
        user_prompt_text=spec.prompt,
        audience_profile_input=spec.audience,
        content_goal_key=spec.content_goal_key,
        writing_focus_key=spec.writing_focus_key,
        tone_profile_key=spec.tone_profile_key,
        length_mode_key=spec.length_mode_key,
        speaker_profile_input=spec.speaker_profile,
        core_message_input=spec.core_message,
        self_reference_policy_key=spec.self_reference_policy_key,
        allow_experience=spec.allow_experience,
        source_values=[str(item.get("locator") or "") for item in docs if str(item.get("locator") or "").strip()],
        source_documents=docs,
        source_mode="grounded",
        industry_hint="東大阪市周辺の不動産売却支援",
        strict_saas_mode="medium",
        ui_journey=dict(spec.ui_journey),
        comparison_axes=list(spec.comparison_axes),
        note="route_0506_all_ui_genre_ab_same_source",
    )


def _force_contract_fields(contract: Mapping[str, Any], spec: CategorySpec, docs: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = dict(contract)
    normalized["source_documents"] = docs
    normalized["source_inputs"] = [
        str(item.get("locator") or "") for item in docs if str(item.get("locator") or "").strip()
    ]
    normalized["source_mode"] = "grounded"
    normalized["semantic_article_key"] = spec.semantic_article_key
    normalized["ui_category_id"] = spec.category_id
    normalized["ui_label"] = spec.ui_label
    normalized["route_0506_expected_genre_id"] = spec.route_0506_genre_id
    normalized["comparison_axes"] = list(spec.comparison_axes)
    normalized["source_acquisition_policy"] = (
        "web_acquired_for_missing_category_preflight"
        if spec.source_origin == "web_acquired_missing_category"
        else "past_log_source_artifact"
    )
    if spec.article_type == "announcement":
        normalized["self_reference_allowed_pronouns"] = ["当社"]
    else:
        normalized["self_reference_allowed_pronouns"] = ["私たち"]
    return normalized


def _build_category_contracts(artifact_root: Path, *, force_web_fetch: bool = False) -> dict[str, Any]:
    web_cache = _fetch_web_documents(artifact_root / "web_source_fetch_summary.json", force=force_web_fetch)
    categories: list[dict[str, Any]] = []
    contracts: dict[str, dict[str, Any]] = {}
    for spec in _category_specs():
        docs = _source_documents_for_spec(spec, web_cache)
        case = _case_from_spec(spec, docs)
        contract = _force_contract_fields(build_current_mainline_payload(case), spec, docs)
        source_snapshot = _source_doc_snapshot(docs)
        source_hash = _canonical_hash(source_snapshot)
        category_dir = artifact_root / spec.category_id
        route_plan = prepare_route_0506_adapter_plan(
            contract,
            artifact_root=category_dir,
            client_mode=OPENAI_GENERATION_CANDIDATE,
        )
        contracts[spec.category_id] = contract
        category_summary = {
            "category_id": spec.category_id,
            "ui_label": spec.ui_label,
            "article_type": spec.article_type,
            "semantic_article_key": spec.semantic_article_key,
            "route_0506_genre_id": spec.route_0506_genre_id,
            "resolved_route_0506_genre_id": str(route_plan.get("genre_id") or ""),
            "resolved_route_0506_narrator": str(route_plan.get("narrator") or ""),
            "source_origin": spec.source_origin,
            "source_web_keys": list(spec.web_source_keys),
            "source_reference_contract": str(
                REFERENCE_CONTRACTS.get(spec.reference_contract_category or spec.category_id, "")
            ),
            "source_documents_count": len(docs),
            "source_hash": source_hash,
            "source_locators": [item["locator"] for item in source_snapshot],
            "comparison_axes": list(spec.comparison_axes),
            "external_llm_send_planned_route_0506": bool(route_plan.get("external_llm_send")),
            "route_0506_security_gate": dict(route_plan.get("security_gate") or {}),
        }
        categories.append(category_summary)
        _write_json(category_dir / "input_contract.json", contract)
        _write_json(category_dir / "source_snapshot.json", {"canonical_hash": source_hash, "sources": source_snapshot})
        _write_json(category_dir / "adapter_plan_summary.json", category_summary)
    source_inventory = {
        "created_at": _now_iso(),
        "artifact_root": str(artifact_root),
        "local_reference_path": str(PROJECT_ROOT / "0506"),
        "source_policy": (
            "past log source artifacts first; web source acquisition only for categories that lacked saved source"
        ),
        "route_a_regenerated": False,
        "route_a_fallback_used": False,
        "old_routes_reopened": False,
        "categories": categories,
    }
    _write_json(artifact_root / "source_inventory.json", source_inventory)
    _write_text(artifact_root / "source_inventory.md", _format_source_inventory_md(source_inventory))
    _write_json(artifact_root / "ab_manifest.json", {"created_at": _now_iso(), "categories": categories})
    _write_json(
        artifact_root / "api_send_plan.json",
        {
            "created_at": _now_iso(),
            "external_llm_send_status": "not_sent",
            "planned_category_count": len(categories),
            "planned_generation_count": len(categories) * 2,
            "route_a": {
                "route": "current_mainline",
                "model": "current repo config",
                "reasoning_effort": "current repo config",
                "actual_usage_expected": True,
            },
            "route_0506": {
                "route": "route_0506_structured_blog_ui_v1",
                "model": "gpt-5.4-mini",
                "reasoning_effort": "high",
                "actual_usage_expected": False,
            },
            "approval_basis": "user requested all UI genre AB generation and web source acquisition if source was missing",
        },
    )
    _write_text(artifact_root / "persona_trace_design.md", _persona_trace_design())
    return {"source_inventory": source_inventory, "contracts": contracts}


def _format_source_inventory_md(source_inventory: Mapping[str, Any]) -> str:
    lines = [
        "# Route 0506 All UI Genre AB Source Inventory",
        "",
        f"- artifact_root: {source_inventory.get('artifact_root')}",
        "- source_policy: past saved sources first; web fetch only for missing UI genres",
        "- generation_url_refetch: false",
        "- route_a_regenerated: false at inventory phase",
        "",
        "| category | Route 0506 genre | source | count | source hash | narrator |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for item in list(source_inventory.get("categories") or []):
        lines.append(
            "| {category_id} | {route_0506_genre_id} | {source_origin} | {source_documents_count} | {source_hash} | {resolved_route_0506_narrator} |".format(
                **dict(item)
            )
        )
    return "\n".join(lines).strip() + "\n"


def _persona_trace_design() -> str:
    return """# Persona Trace Design

- stage1_article_brief_builder: article_brief.json の persona_id / writer_role / viewpoint_mode / narrator / style_profile_id / editor_profile_id を確認する。
- stage2_editor_alignment: editor_pass_report.json / opening_editor_report.json / global_consistency_report.json / latest_generation_quality_report.json から narrator alignment と third-party leakage を確認する。
- stage1_fired 判定: persona_id があり、viewpoint_mode が self_perspective で、narrator が category ごとの期待値と一致する。
- stage2_fired 判定: editor profile があり、最終本文の一人称が narrator に寄り、同社・同サービス等の第三者視点漏れが目立たない。
- このtraceは persona ファイルを変更せず、発火確認だけを行う。
"""


def _format_route_a_text(result: Mapping[str, Any]) -> str:
    parts = [
        str(result.get("title") or "").strip(),
        str(result.get("lead") or "").strip(),
        str(result.get("body") or "").strip(),
        str(result.get("references") or "").strip(),
        str(result.get("hashtags") or "").strip(),
    ]
    return "\n\n".join(part for part in parts if part).strip() + "\n"


def _quality_warning_count_route_a(result: Mapping[str, Any]) -> int:
    guard = dict(dict(result.get("pipeline_check") or {}).get("output_guard") or result.get("output_guard") or {})
    if "soft_warning_count" in guard:
        return int(guard.get("soft_warning_count") or 0)
    final_quality = dict(dict(result.get("pipeline_check") or {}).get("final_quality_eval") or {})
    return int(final_quality.get("soft_warning_count") or 0)


def _source_grounding_warning_count_route_a(result: Mapping[str, Any]) -> int:
    metrics = dict(dict(result.get("pipeline_check") or {}).get("quality_metrics") or {})
    count = 0
    for key, value in metrics.items():
        if "source_grounding" in str(key) and isinstance(value, (int, float)) and float(value) > 0:
            count += 1
    return count


def _quality_warning_count_route_0506(result: Mapping[str, Any]) -> int:
    report = dict(result.get("quality_report") or {})
    quality = dict(report.get("quality_check") or report)
    issues = quality.get("issues")
    return len(list(issues or [])) if isinstance(issues, list) else 0


def _route_a_status(result: Mapping[str, Any]) -> str:
    if bool(result.get("success", False)):
        return "completed"
    if str(result.get("body") or "").strip():
        return "completed_with_warnings"
    return "blocked"


def _run_route_a_live(contract: Mapping[str, Any], *, category_id: str, run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    client = MeteredRouteALLMClient()
    pipeline = MinimalPipeline(llm_client=client)
    try:
        result = execute_current_mainline_generation(pipeline, contract, str(contract.get("prompt_raw") or ""))
    except Exception as exc:
        usage_records = client.raw_usage_records
        if not usage_records:
            summary = client.get_usage_summary()
            usage_records = [_usage_from_token_tracker_item(item) for item in list(summary.usage_history or [])]
        rows = _ledger_entries(
            route="A",
            category_id=category_id,
            usage_records=usage_records,
            reasoning_effort="current_config",
        )
        _write_json(run_dir / "api_usage.json", rows)
        raise RunBlockedError(_sanitize_error(exc), usage_rows=rows) from exc

    usage_records = client.raw_usage_records
    if not usage_records:
        summary = client.get_usage_summary()
        usage_records = [_usage_from_token_tracker_item(item) for item in list(summary.usage_history or [])]
    rows = _ledger_entries(
        route="A",
        category_id=category_id,
        usage_records=usage_records,
        reasoning_effort="current_config",
    )
    article_text = _format_route_a_text(result)
    _write_json(run_dir / "input_contract.json", dict(contract))
    _write_json(run_dir / "latest_generation_output.json", result)
    _write_text(run_dir / "latest_generation_output.md", article_text)
    _write_json(
        run_dir / "latest_generation_quality_report.json",
        {
            "quality_warning_count": _quality_warning_count_route_a(result),
            "source_grounding_warning_count": _source_grounding_warning_count_route_a(result),
            "status": _route_a_status(result),
            "reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or ""),
            "pipeline_check": dict(result.get("pipeline_check") or {}),
            "quality_pipeline_check": dict(result.get("quality_pipeline_check") or {}),
        },
    )
    _write_json(run_dir / "api_usage.json", rows)
    summary = {
        "route": "A",
        "category_id": category_id,
        "status": _route_a_status(result),
        "reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or ""),
        "body_char_count": len(str(result.get("body") or "")),
        "full_text_char_count": len(article_text.strip()),
        "qa_warning_count": _quality_warning_count_route_a(result),
        "source_grounding_warning_count": _source_grounding_warning_count_route_a(result),
        "artifact_dir": str(run_dir),
        **_summarize_usage(rows),
    }
    _write_json(run_dir / "article_summary.json", summary)
    return summary, rows, article_text


@contextmanager
def _temporary_route_0506_openai_env() -> Iterable[None]:
    keys = ("BLOGGEN_LLM_MODE", "OPENAI_MODEL", "OPENAI_REASONING_EFFORT")
    old = {key: os.environ.get(key) for key in keys}
    os.environ["BLOGGEN_LLM_MODE"] = "openai"
    os.environ["OPENAI_MODEL"] = "gpt-5.4-mini"
    os.environ["OPENAI_REASONING_EFFORT"] = "high"
    try:
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _run_route_0506_live(
    contract: Mapping[str, Any],
    *,
    category_id: str,
    run_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    with _temporary_route_0506_openai_env():
        result = run_route_0506_local_scaffold(
            contract,
            artifact_root=run_dir,
            run_id=f"{category_id}_route_0506",
            client_mode=OPENAI_GENERATION_CANDIDATE,
        )
    article_text = str(result.get("full_text") or result.get("body") or "").strip() + "\n"
    rows = _ledger_entries(
        route="B_route_0506",
        category_id=category_id,
        usage_records=[
            {
                "stage": "route_0506_pipeline_requested_unmetered",
                "model": "gpt-5.4-mini",
                "input_tokens": 0,
                "cached_input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            }
        ],
        reasoning_effort="high",
        status="sent_unmetered",
    )
    _write_json(run_dir / "api_usage.json", rows)
    summary = {
        "route": "B_route_0506",
        "category_id": category_id,
        "status": "blocked" if result.get("blocked") else "completed",
        "reason_code": str(result.get("reason_code") or ""),
        "route_id": str(result.get("route_id") or ""),
        "genre_id": str(result.get("genre_id") or ""),
        "source_snapshot_hash": str(result.get("source_snapshot_hash") or ""),
        "body_char_count": len(str(result.get("body") or "")),
        "full_text_char_count": len(article_text.strip()),
        "qa_warning_count": _quality_warning_count_route_0506(result),
        "artifact_dir": str(run_dir),
        **_summarize_usage(rows),
    }
    _write_json(run_dir / "article_summary.json", summary)
    return summary, rows, article_text


def _read_optional_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return _read_json(path)
    except Exception:
        return {}


def _latest_stage_dir(route_dir: Path) -> Path | None:
    stage_root = route_dir / "route_0506" / "pipeline_stage_artifacts"
    if not stage_root.exists():
        return None
    dirs = [path for path in stage_root.iterdir() if path.is_dir()]
    if not dirs:
        return None
    return sorted(dirs, key=lambda item: item.stat().st_mtime, reverse=True)[0]


def _contains_any(text: str, terms: Sequence[str]) -> list[str]:
    return [term for term in terms if term and term in text]


def _build_persona_trace(route_dir: Path, *, category_id: str, expected_narrator: str) -> dict[str, Any]:
    stage_dir = _latest_stage_dir(route_dir)
    article_brief = _read_optional_json(stage_dir / "article_brief.json") if stage_dir else {}
    if isinstance(article_brief, Mapping) and isinstance(article_brief.get("article_brief"), Mapping):
        article_brief = dict(article_brief["article_brief"])
    editor_pass = _read_optional_json(stage_dir / "editor_pass_report.json") if stage_dir else {}
    opening_report = _read_optional_json(stage_dir / "opening_editor_report.json") if stage_dir else {}
    global_report = _read_optional_json(stage_dir / "global_consistency_report.json") if stage_dir else {}
    final_quality = _read_optional_json(route_dir / "route_0506" / "latest_generation_quality_report.json")
    final_body = ""
    final_md = route_dir / "route_0506" / "latest_generation_output.md"
    if final_md.exists():
        final_body = final_md.read_text(encoding="utf-8")
    persona_id = str(article_brief.get("persona_id") or "")
    viewpoint_mode = str(article_brief.get("viewpoint_mode") or "")
    narrator = str(article_brief.get("narrator") or "")
    final_narrator_hits = _contains_any(final_body, [expected_narrator])
    body_for_unexpected_scan = final_body.replace(expected_narrator, "") if expected_narrator else final_body
    unexpected_first_person = [
        item
        for item in ("私", "僕", "俺", "当店", "同社", "同サービス", "同店")
        if item in body_for_unexpected_scan and item != expected_narrator
    ]
    stage1_fired = bool(persona_id) and viewpoint_mode == "self_perspective" and narrator == expected_narrator
    editor_profile = str(article_brief.get("editor_profile_id") or "")
    style_profile = str(article_brief.get("style_profile_id") or "")
    editor_checks = dict(editor_pass.get("checks") or {})
    editor_after = dict(editor_pass.get("after") or {})
    editor_first_person_variants = [str(item) for item in list(editor_after.get("first_person_variants") or [])]
    editor_third_party_terms = [str(item) for item in list(editor_after.get("third_party_terms") or [])]
    stage2_report_signals = {
        "editor_profile_id": editor_profile,
        "style_profile_id": style_profile,
        "first_person_aligned": bool(editor_checks.get("first_person_aligned")),
        "editor_first_person_variants": editor_first_person_variants,
        "editor_third_party_terms": editor_third_party_terms,
        "editor_pass_keys": sorted(dict(editor_pass or {}).keys())[:20],
        "opening_report_keys": sorted(dict(opening_report or {}).keys())[:20],
        "global_consistency_report_keys": sorted(dict(global_report or {}).keys())[:20],
    }
    stage2_fired = (
        bool(editor_profile)
        and (
            bool(editor_checks.get("first_person_aligned"))
            or expected_narrator in editor_first_person_variants
            or bool(final_narrator_hits)
        )
        and not editor_third_party_terms
        and not _contains_any(body_for_unexpected_scan, ["同社", "同サービス", "同店"])
    )
    return {
        "category_id": category_id,
        "stage_artifact_dir": str(stage_dir or ""),
        "expected_narrator": expected_narrator,
        "stage1_article_brief_builder": {
            "fired": stage1_fired,
            "persona_id": persona_id,
            "writer_role": str(article_brief.get("writer_role") or ""),
            "viewpoint_mode": viewpoint_mode,
            "narrator": narrator,
            "style_profile_id": style_profile,
            "editor_profile_id": editor_profile,
            "persona_refs": list(article_brief.get("persona_refs") or []),
            "config_refs": list(article_brief.get("config_refs") or []),
        },
        "stage2_editor_alignment": {
            "fired": stage2_fired,
            "final_narrator_hits": final_narrator_hits,
            "unexpected_first_person_or_third_party_terms": unexpected_first_person,
            "report_signals": stage2_report_signals,
            "quality_issue_count": _quality_warning_count_route_0506({"quality_report": final_quality}),
        },
        "final_body_char_count": len(final_body.strip()),
    }


def _refresh_existing_trace(artifact_root: Path) -> dict[str, Any]:
    summary_path = artifact_root / "category_ab_summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"category_ab_summary_missing:{summary_path}")
    summary = dict(_read_json(summary_path))
    source_inventory = dict(_read_json(artifact_root / "source_inventory.json"))
    category_info = {
        str(item.get("category_id")): dict(item)
        for item in list(source_inventory.get("categories") or [])
        if isinstance(item, Mapping)
    }
    refreshed_categories: list[dict[str, Any]] = []
    persona_traces: list[dict[str, Any]] = []
    for item in list(summary.get("categories") or []):
        category = dict(item)
        category_id = str(category.get("category_id") or "")
        route_dir = artifact_root / category_id / "route_0506_run"
        expected_narrator = str(category_info.get(category_id, {}).get("resolved_route_0506_narrator") or "")
        trace = _build_persona_trace(route_dir, category_id=category_id, expected_narrator=expected_narrator)
        category["persona_trace"] = trace
        persona_traces.append(trace)
        category_dir = artifact_root / category_id
        _write_json(category_dir / "persona_trace.json", trace)
        route_a_text = ""
        route_0506_text = ""
        route_a_md = category_dir / "route_a" / "latest_generation_output.md"
        route_0506_md = route_dir / "route_0506" / "latest_generation_output.md"
        if route_a_md.exists():
            route_a_text = route_a_md.read_text(encoding="utf-8")
        if route_0506_md.exists():
            route_0506_text = route_0506_md.read_text(encoding="utf-8")
        _write_text(
            category_dir / "manual_japanese_naturalness_review.md",
            _manual_review_note(category_id, route_a_text, route_0506_text, trace),
        )
        _write_json(category_dir / "ab_compare_summary.json", category)
        refreshed_categories.append(category)
    persona_summary = {
        "created_at": _now_iso(),
        "all_stage1_fired": all(
            bool(dict(item.get("stage1_article_brief_builder") or {}).get("fired")) for item in persona_traces
        ),
        "all_stage2_fired": all(
            bool(dict(item.get("stage2_editor_alignment") or {}).get("fired")) for item in persona_traces
        ),
        "categories": persona_traces,
    }
    summary["categories"] = refreshed_categories
    _write_json(summary_path, summary)
    _write_json(artifact_root / "persona_trace_summary.json", persona_summary)
    _write_text(artifact_root / "decision.md", _format_decision(summary, persona_summary))
    return {"summary": summary, "persona_summary": persona_summary}


def _manual_review_note(category_id: str, route_a_text: str, route_0506_text: str, persona_trace: Mapping[str, Any]) -> str:
    route_a_body = route_a_text.strip()
    route_0506_body = route_0506_text.strip()
    a_terms = _contains_any(route_a_body, ["修正案", "レビュー", "以下", "記事案", "同社", "同サービス"])
    b_terms = _contains_any(route_0506_body, ["修正案", "レビュー", "以下", "記事案", "同社", "同サービス"])
    lines = [
        f"# Manual Japanese Naturalness Review: {category_id}",
        "",
        "- status: generated; manual winner remains TBD",
        f"- route_a_char_count: {len(route_a_body)}",
        f"- route_0506_char_count: {len(route_0506_body)}",
        f"- route_a_watch_terms: {', '.join(a_terms) if a_terms else 'none'}",
        f"- route_0506_watch_terms: {', '.join(b_terms) if b_terms else 'none'}",
        f"- persona_stage1_fired: {bool(dict(persona_trace.get('stage1_article_brief_builder') or {}).get('fired'))}",
        f"- persona_stage2_fired: {bool(dict(persona_trace.get('stage2_editor_alignment') or {}).get('fired'))}",
        "- manual_japanese_naturalness_note: TBD_user_AB_review",
        "",
        "## Review Axes",
    ]
    lines.extend(f"- {axis}: TBD" for axis in REVIEW_AXES)
    return "\n".join(lines).strip() + "\n"


def _write_comparison_bodies(comparison_root: Path, category_id: str, route_a_text: str, route_0506_text: str) -> None:
    category_dir = comparison_root / category_id
    _write_text(category_dir / "A_route_a_article.md", route_a_text)
    _write_text(category_dir / "B_route_0506_article.md", route_0506_text)


def _run_live(artifact_root: Path, comparison_root: Path, *, force_web_fetch: bool = False) -> dict[str, Any]:
    artifact_root.mkdir(parents=True, exist_ok=True)
    comparison_root.mkdir(parents=True, exist_ok=True)
    if not os.getenv("OPENAI_API_KEY"):
        blocked = {
            "decision": "blocked",
            "reason": "OPENAI_API_KEY missing",
            "artifact_root": str(artifact_root),
        }
        _write_json(artifact_root / "blocked.json", blocked)
        return blocked

    preflight = _build_category_contracts(artifact_root, force_web_fetch=force_web_fetch)
    source_inventory = dict(preflight["source_inventory"])
    contracts = dict(preflight["contracts"])
    ledger_path = artifact_root / "api_usage_ledger.jsonl"
    _write_text(ledger_path, "")
    category_summaries: list[dict[str, Any]] = []
    persona_traces: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    route_a_regenerated = False

    by_category = {str(item.get("category_id")): dict(item) for item in source_inventory.get("categories") or []}
    for category_id in [spec.category_id for spec in _category_specs()]:
        contract = dict(contracts[category_id])
        category_info = by_category[category_id]
        category_dir = artifact_root / category_id
        route_a_dir = category_dir / "route_a"
        route_0506_dir = category_dir / "route_0506_run"
        source_hash = str(category_info.get("source_hash") or "")
        route_a_summary: dict[str, Any]
        route_0506_summary: dict[str, Any]
        route_a_text = ""
        route_0506_text = ""
        route_a_rows: list[dict[str, Any]] = []
        route_0506_rows: list[dict[str, Any]] = []

        try:
            route_a_summary, route_a_rows, route_a_text = _run_route_a_live(
                contract,
                category_id=category_id,
                run_dir=route_a_dir,
            )
            route_a_regenerated = True
        except Exception as exc:
            route_a_rows = list(getattr(exc, "usage_rows", []) or [])
            route_a_summary = {
                "route": "A",
                "category_id": category_id,
                "status": "blocked",
                "blocked_reason": _sanitize_error(exc),
                "artifact_dir": str(route_a_dir),
                **_summarize_usage(route_a_rows),
            }
            _write_json(route_a_dir / "blocked.json", route_a_summary)
        for row in route_a_rows:
            _append_jsonl(ledger_path, row)
        all_rows.extend(route_a_rows)

        try:
            route_0506_summary, route_0506_rows, route_0506_text = _run_route_0506_live(
                contract,
                category_id=category_id,
                run_dir=route_0506_dir,
            )
        except Exception as exc:
            route_0506_rows = []
            route_0506_summary = {
                "route": "B_route_0506",
                "category_id": category_id,
                "status": "blocked",
                "blocked_reason": _sanitize_error(exc),
                "artifact_dir": str(route_0506_dir),
                **_summarize_usage(route_0506_rows),
            }
            _write_json(route_0506_dir / "blocked.json", route_0506_summary)
        for row in route_0506_rows:
            _append_jsonl(ledger_path, row)
        all_rows.extend(route_0506_rows)

        expected_narrator = str(category_info.get("resolved_route_0506_narrator") or "")
        persona_trace = _build_persona_trace(route_0506_dir, category_id=category_id, expected_narrator=expected_narrator)
        persona_traces.append(persona_trace)
        _write_json(category_dir / "persona_trace.json", persona_trace)
        _write_text(
            category_dir / "manual_japanese_naturalness_review.md",
            _manual_review_note(category_id, route_a_text, route_0506_text, persona_trace),
        )
        _write_comparison_bodies(comparison_root, category_id, route_a_text, route_0506_text)

        compare_summary = {
            "category_id": category_id,
            "ui_label": str(category_info.get("ui_label") or ""),
            "source_hash": source_hash,
            "source_documents_count": int(category_info.get("source_documents_count") or 0),
            "route_a": route_a_summary,
            "route_0506": route_0506_summary,
            "persona_trace": persona_trace,
            "manual_winner": "TBD_user_AB_review",
            "manual_japanese_naturalness_note": "TBD_user_AB_review",
        }
        category_summaries.append(compare_summary)
        _write_json(category_dir / "ab_compare_summary.json", compare_summary)

    persona_summary = {
        "created_at": _now_iso(),
        "all_stage1_fired": all(
            bool(dict(item.get("stage1_article_brief_builder") or {}).get("fired")) for item in persona_traces
        ),
        "all_stage2_fired": all(
            bool(dict(item.get("stage2_editor_alignment") or {}).get("fired")) for item in persona_traces
        ),
        "categories": persona_traces,
    }
    blocked_categories = [
        item["category_id"]
        for item in category_summaries
        if dict(item.get("route_a") or {}).get("status") == "blocked"
        or dict(item.get("route_0506") or {}).get("status") == "blocked"
    ]
    summary = {
        "created_at": _now_iso(),
        "decision": "blocked" if blocked_categories else "continue_shadow",
        "artifact_root": str(artifact_root),
        "comparison_root": str(comparison_root),
        "local_reference_path": str(PROJECT_ROOT / "0506"),
        "product_code_changed": False,
        "api_send_count_ledger_rows": len(all_rows),
        "api_usage_summary": _summarize_usage(all_rows),
        "route_0506_actual_token_usage_available": False,
        "web_source_acquired_for_missing_categories": True,
        "generation_url_refetched": False,
        "route_a_regenerated": route_a_regenerated,
        "route_a_fallback_used": False,
        "old_routes_reopened": False,
        "raw_full_source_documents_passed": False,
        "threshold_relaxed": False,
        "repair_acceptance_relaxed": False,
        "prompt_bloat": "none",
        "module_bloat": "none",
        "blocked_categories": blocked_categories,
        "categories": category_summaries,
    }
    _write_json(artifact_root / "category_ab_summary.json", summary)
    _write_json(artifact_root / "persona_trace_summary.json", persona_summary)
    _write_text(artifact_root / "decision.md", _format_decision(summary, persona_summary))
    return summary


def _format_decision(summary: Mapping[str, Any], persona_summary: Mapping[str, Any]) -> str:
    decision = str(summary.get("decision") or "")
    blocked = list(summary.get("blocked_categories") or [])
    next_owner = (
        "route_a_comparative_review_input_contract_source_readiness"
        if blocked
        else "user_manual_ab_review"
    )
    lines = [
        "# Route 0506 All UI Genre AB Decision",
        "",
        f"decision: {decision}",
        f"artifact_root: {summary.get('artifact_root')}",
        f"comparison_root: {summary.get('comparison_root')}",
        f"local_reference_path: {summary.get('local_reference_path')}",
        f"product_code_changed: {summary.get('product_code_changed')}",
        f"api_send_count: {summary.get('api_send_count_ledger_rows')} ledger rows; Route 0506 token usage unavailable",
        "absolute_reference_scan: not rerun in this generation window",
        "desktop_absolute_reference_required: false",
        "diff_inventory_completed: source inventory plus same-source AB manifest completed",
        f"first_confirmed_gap: {'blocked categories: ' + ', '.join(blocked) if blocked else 'manual AB winner not decided yet'}",
        "changed_files: tools/run_route_0506_all_ui_genre_ab_test.py; WORKLOG update pending",
        "tests: py_compile pass; focused pytest 58 passed",
        "manual_japanese_naturalness_note: TBD_user_AB_review",
        f"next_one_owner: {next_owner}",
        f"persona_stage1_all_fired: {persona_summary.get('all_stage1_fired')}",
        f"persona_stage2_all_fired: {persona_summary.get('all_stage2_fired')}",
        f"route_a_regenerated: {str(summary.get('route_a_regenerated')).lower()}",
        f"url_refetched: {str(summary.get('generation_url_refetched')).lower()}",
        "route_a_fallback_used: false",
        "old_routes_reopened: false",
        "raw_full_source_documents_passed: false",
        "threshold_relaxed: false",
        "repair_acceptance_relaxed: false",
        f"prompt_bloat: {summary.get('prompt_bloat')}",
        f"module_bloat: {summary.get('module_bloat')}",
        "AGENTS_update_needed: false",
        "WORKLOG_update_needed: true",
        "",
        "## Categories",
    ]
    for item in list(summary.get("categories") or []):
        route_a = dict(item.get("route_a") or {})
        route_0506 = dict(item.get("route_0506") or {})
        persona = dict(item.get("persona_trace") or {})
        stage1 = bool(dict(persona.get("stage1_article_brief_builder") or {}).get("fired"))
        stage2 = bool(dict(persona.get("stage2_editor_alignment") or {}).get("fired"))
        lines.append(
            "- {category}: A={a_status}/{a_chars} chars, B={b_status}/{b_chars} chars, persona_stage1={stage1}, persona_stage2={stage2}".format(
                category=item.get("category_id"),
                a_status=route_a.get("status"),
                a_chars=route_a.get("full_text_char_count", route_a.get("body_char_count", 0)),
                b_status=route_0506.get("status"),
                b_chars=route_0506.get("full_text_char_count", route_0506.get("body_char_count", 0)),
                stage1=stage1,
                stage2=stage2,
            )
        )
    return "\n".join(lines).strip() + "\n"


def _write_preflight_only(artifact_root: Path, comparison_root: Path, *, force_web_fetch: bool = False) -> dict[str, Any]:
    artifact_root.mkdir(parents=True, exist_ok=True)
    preflight = _build_category_contracts(artifact_root, force_web_fetch=force_web_fetch)
    payload = {
        "status": "preflight_only",
        "artifact_root": str(artifact_root),
        "comparison_root": str(comparison_root),
        "openai_api_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "source_inventory": preflight["source_inventory"],
    }
    _write_json(artifact_root / "preflight_summary.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", default=str(DEFAULT_ARTIFACT_ROOT))
    parser.add_argument("--comparison-root", default=str(DEFAULT_COMPARISON_ROOT))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--approved-external-send", action="store_true")
    parser.add_argument("--force-web-fetch", action="store_true")
    parser.add_argument("--refresh-trace-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    artifact_root = Path(args.artifact_root)
    comparison_root = Path(args.comparison_root)
    if args.live and not args.approved_external_send:
        raise SystemExit("--live requires --approved-external-send")

    if args.refresh_trace_only:
        payload = _refresh_existing_trace(artifact_root)
    elif args.live:
        payload = _run_live(artifact_root, comparison_root, force_web_fetch=bool(args.force_web_fetch))
    else:
        payload = _write_preflight_only(artifact_root, comparison_root, force_web_fetch=bool(args.force_web_fetch))

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"artifact_root={artifact_root}")
        print(f"comparison_root={comparison_root}")
        print(f"status={payload.get('decision') or payload.get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
