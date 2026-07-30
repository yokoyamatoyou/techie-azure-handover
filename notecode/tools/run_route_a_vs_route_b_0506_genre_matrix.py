from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROUTE_B_ROOT = Path(r"C:\Users\横山裕明\Desktop\0506")
CASEBOOK_PATH = PROJECT_ROOT / "note" / "tests" / "fixtures" / "current_mainline_genre_sweep_casebook_2026-03-30.json"
sys.path.insert(0, str(PROJECT_ROOT))

from note.current_mainline_ui_matrix import UISweepCase, build_current_mainline_payload  # noqa: E402
from note.current_mainline_runner import execute_current_mainline_generation  # noqa: E402
from note.llm_client import LLMClient as RouteALLMClient  # noqa: E402
from note.route_b_0506_adapter import (  # noqa: E402
    ROUTE_B_0506_ROUTE_ID,
    _build_0506_extracted_source,
    _load_route_b_0506_modules,
    extract_route_b_source_records,
    inspect_route_b_0506_workspace,
    resolve_route_b_0506_genre,
    resolve_route_b_0506_narrator,
    route_b_source_snapshot_hash,
)
from note.simple_note_pipeline.pipeline import MinimalPipeline  # noqa: E402


GENRE_CASE_IDS = {
    "company_introduction": "bl-branding-company-overview",
    "product_introduction": "bl-branding-service-overview",
    "announcement": "bl-announcement-spec-change",
    "case_study": "st-case-slow-adoption",
    "comparative_review": "st-comparative-small-team",
    "daily_story": "bl-daily-learning-log-grounded",
    "industry_analysis": "st-industry-competition-axis",
}

ROUTE_B_GENRES = {
    "company_introduction": "company_service_intro",
    "product_introduction": "company_service_intro",
    "announcement": "announcement",
    "case_study": "case_study",
    "comparative_review": "comparison_guide",
    "daily_story": "daily_activity",
    "industry_analysis": "market_explanation",
}

PRICING = {
    "gpt-5.4-mini": {
        "input_usd_per_1m_tokens": 0.75,
        "cached_input_usd_per_1m_tokens": 0.075,
        "output_usd_per_1m_tokens": 4.50,
        "source": "https://openai.com/api/pricing/",
    },
    "gpt-5.4": {
        "input_usd_per_1m_tokens": 2.50,
        "cached_input_usd_per_1m_tokens": 0.25,
        "output_usd_per_1m_tokens": 15.00,
        "source": "https://openai.com/api/pricing/",
    },
    "gpt-4.1-mini": {
        "input_usd_per_1m_tokens": 0.40,
        "cached_input_usd_per_1m_tokens": 0.10,
        "output_usd_per_1m_tokens": 1.60,
        "source": "https://developers.openai.com/api/docs/models/gpt-4.1-mini",
    },
    "gpt-4.1-mini-2025-04-14": {
        "input_usd_per_1m_tokens": 0.40,
        "cached_input_usd_per_1m_tokens": 0.10,
        "output_usd_per_1m_tokens": 1.60,
        "source": "https://developers.openai.com/api/docs/models/gpt-4.1-mini",
    },
}

ROUTE_B_FIXED_STAGES = (
    "knowledge_pack_integration",
    "article_brief_builder",
    "draft_writer",
    "opening_editor",
    "global_consistency_editor",
    "style_editor",
    "structural_editor",
)

REVIEW_AXES = (
    "self_perspective_natural",
    "first_person_not_mixed",
    "no_source_external_claim",
    "heading_body_continuity",
    "opening_naturalness",
    "late_half_no_stall",
    "repetition_and_gpt_like_terms",
    "salesy_or_third_party_leakage",
)


class RunBlockedError(RuntimeError):
    def __init__(self, message: str, *, usage_rows: Sequence[Mapping[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.usage_rows = [dict(row) for row in list(usage_rows or [])]


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    return re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[REDACTED_OPENAI_KEY]", text)[:1600]


def _normalize_model_name(model: str) -> str:
    name = str(model or "").strip()
    if name in PRICING:
        return name
    if name.startswith("gpt-4.1-mini"):
        return "gpt-4.1-mini"
    return name


def _cost_usd(model: str, input_tokens: int, cached_input_tokens: int, output_tokens: int) -> float:
    normalized = _normalize_model_name(model)
    if normalized not in PRICING:
        raise RuntimeError(f"pricing_missing_for_model:{model}")
    price = PRICING[normalized]
    cached = max(0, int(cached_input_tokens or 0))
    input_total = max(0, int(input_tokens or 0))
    non_cached_input = max(0, input_total - cached)
    output = max(0, int(output_tokens or 0))
    return round(
        (non_cached_input / 1_000_000) * float(price["input_usd_per_1m_tokens"])
        + (cached / 1_000_000) * float(price["cached_input_usd_per_1m_tokens"])
        + (output / 1_000_000) * float(price["output_usd_per_1m_tokens"]),
        8,
    )


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
            "estimated_cost_usd": 0.0,
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
        "estimated_cost_usd": _cost_usd(model, input_tokens, cached_input_tokens, output_tokens),
    }


def _usage_from_token_tracker_item(item: Any) -> dict[str, Any]:
    model = str(_get_value(item, "model", "") or "")
    stage = str(_get_value(item, "task_type", "") or "")
    input_tokens = int(_get_value(item, "input_tokens", 0) or 0)
    output_tokens = int(_get_value(item, "output_tokens", 0) or 0)
    total_tokens = int(_get_value(item, "total_tokens", input_tokens + output_tokens) or 0)
    return {
        "stage": stage,
        "model": model,
        "input_tokens": input_tokens,
        "cached_input_tokens": 0,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": _cost_usd(model, input_tokens, 0, output_tokens),
    }


class MeteredRouteALLMClient(RouteALLMClient):
    def __init__(self) -> None:
        super().__init__()
        self.raw_usage_records: list[dict[str, Any]] = []

    def _record_usage(self, response: Any, model: str, task_type: str) -> None:  # type: ignore[override]
        super()._record_usage(response, model, task_type)
        self.raw_usage_records.append(_usage_from_response(response, model=str(model or ""), stage=str(task_type or "")))


class MeteredRouteBOpenAIClient:
    def __init__(self, *, model: str = "gpt-5.4-mini", reasoning_effort: str = "high") -> None:
        from openai import OpenAI

        self.model = model
        self.reasoning_effort = reasoning_effort
        self.client = OpenAI()
        self.usage_records: list[dict[str, Any]] = []
        self._schema_validator = import_module("app.services.schema_validator")

    def generate_json(
        self,
        stage_name: str,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        schema = self._schema_validator.load_schema(schema_name)
        response = self.client.responses.create(
            model=self.model,
            reasoning={"effort": self.reasoning_effort},
            input=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": stage_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        self.usage_records.append(_usage_from_response(response, model=self.model, stage=stage_name))
        return json.loads(response.output_text)

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        response = self.client.responses.create(
            model=self.model,
            reasoning={"effort": self.reasoning_effort},
            input=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        self.usage_records.append(_usage_from_response(response, model=self.model, stage=stage_name))
        return str(response.output_text or "")


def _find_case(casebook: Mapping[str, Any], case_id: str) -> dict[str, Any]:
    for group in ("baseline_cases", "stabilization_cases", "experimental_cases"):
        for item in list(casebook.get(group) or []):
            if str(dict(item).get("case_id") or "") == case_id:
                return dict(item)
    raise RuntimeError(f"case_id_not_found:{case_id}")


def _route_b_0506_product_source_supplement() -> dict[str, str]:
    return {
        "title": "0506 ソフト概要",
        "content": (
            "0506 は、日本語ブログ生成アプリケーションである。"
            "URL、PDF、Word ファイル、手入力テキストなど複数のソースを受け取り、"
            "それらのソースだけに根拠づく自然な日本語ブログ記事を生成する。"
            "ソース抽出、知識統合、記事ブリーフ、下書き、編集、品質確認、"
            "必要時の targeted rewrite を分けて扱う staged blog pipeline として実装されている。"
        ),
        "locator": r"C:\Users\横山裕明\Desktop\0506\AGENTS.md",
        "source_type": "local_file",
    }


def _apply_route_b_0506_source_supplements(entry: Mapping[str, Any], *, genre: str) -> dict[str, Any]:
    updated = dict(entry)
    if genre != "product_introduction":
        return updated
    source_documents = [dict(item) for item in list(updated.get("source_documents") or [])]
    supplement = _route_b_0506_product_source_supplement()
    if not any(str(item.get("title") or "") == supplement["title"] for item in source_documents):
        source_documents.append(supplement)
    updated["source_documents"] = source_documents
    source_values = [str(item) for item in list(updated.get("source_values") or [])]
    if supplement["locator"] not in source_values:
        source_values.append(supplement["locator"])
    updated["source_values"] = source_values
    updated["note"] = (
        str(updated.get("note") or "").strip()
        + "\nroute_b_0506_compare_supplement: product subject anchor supplied from local 0506 AGENTS.md."
    ).strip()
    return updated


def _case_from_entry(entry: Mapping[str, Any], *, genre: str) -> UISweepCase:
    entry = _apply_route_b_0506_source_supplements(entry, genre=genre)
    source_mode = "grounded" if list(entry.get("source_documents") or []) else str(entry.get("source_mode") or "grounded")
    article_type = str(entry.get("article_type") or "").strip()
    semantic_overrides = {
        "company_introduction": {"purpose_key": "introduce", "target_key": "company"},
        "product_introduction": {"purpose_key": "introduce", "target_key": "product_service"},
    }
    ui_journey = dict(entry.get("ui_journey") or {})
    ui_journey.update(semantic_overrides.get(genre, {}))
    return UISweepCase(
        case_id=genre,
        article_type=article_type,
        user_prompt_text=str(entry.get("user_prompt_text") or ""),
        audience_profile_input=str(entry.get("audience_profile_input") or ""),
        content_goal_key=str(entry.get("content_goal_key") or "auto"),
        writing_focus_key=str(entry.get("writing_focus_key") or "auto"),
        tone_profile_key=str(entry.get("tone_profile_key") or "auto"),
        length_mode_key=str(entry.get("length_mode_key") or "adaptive"),
        speaker_profile_input=str(entry.get("speaker_profile_input") or ""),
        core_message_input=str(entry.get("core_message_input") or ""),
        allow_experience=bool(entry.get("allow_experience", False)),
        source_values=list(entry.get("source_values") or []),
        source_documents=list(entry.get("source_documents") or []),
        source_mode=source_mode,
        industry_hint=str(entry.get("industry_hint") or ""),
        source_trace=list(entry.get("source_trace") or []),
        interview_answers=dict(entry.get("interview_answers") or {}),
        strict_saas_mode=str(entry.get("strict_saas_mode") or "medium"),
        ui_journey=ui_journey,
        comparison_axes=list(entry.get("comparison_axes") or []),
        note=str(entry.get("note") or ""),
    )


def _build_source_matrix() -> dict[str, Any]:
    casebook = _read_json(CASEBOOK_PATH)
    genres: dict[str, Any] = {}
    for genre, case_id in GENRE_CASE_IDS.items():
        entry = _find_case(casebook, case_id)
        case = _case_from_entry(entry, genre=genre)
        contract = build_current_mainline_payload(case)
        source_documents = list(contract.get("source_documents") or [])
        if not source_documents:
            raise RuntimeError(f"source_documents_missing:{genre}")
        snapshot = [
            {
                "title": str(item.get("title") or ""),
                "content": str(item.get("content") or ""),
                "locator": str(item.get("locator") or item.get("url") or ""),
                "source_type": str(item.get("source_type") or ""),
            }
            for item in source_documents
        ]
        genres[genre] = {
            "casebook_case_id": case_id,
            "route_a_article_type": str(contract.get("article_type") or case.article_type),
            "route_a_semantic_article_key": str(contract.get("semantic_article_key") or ""),
            "route_b_genre": ROUTE_B_GENRES[genre],
            "source_snapshot_hash": _canonical_hash(snapshot),
            "source_count": len(snapshot),
            "source_snapshot": snapshot,
            "user_prompt_text": case.user_prompt_text,
            "audience_profile_input": case.audience_profile_input,
            "ui_journey": dict(case.ui_journey or {}),
            "comparison_axes": list(case.comparison_axes or []),
        }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_policy": "saved_fixture_source_documents_plus_local_0506_product_anchor; no URL refetch during compare",
        "casebook_path": str(CASEBOOK_PATH),
        "source_supplements": {
            "product_introduction": {
                "reason": "Route A product_introduction requires a product_subject_anchor; user identified Desktop 0506 as the source software.",
                "source": _route_b_0506_product_source_supplement(),
            }
        },
        "genres": genres,
    }


def _estimated_plan(source_matrix: Mapping[str, Any], output_root: Path) -> dict[str, Any]:
    genres = dict(source_matrix.get("genres") or {})
    article_count_per_route = len(genres) * 3
    route_a_max_calls_per_article = 6
    route_a_estimated_max_calls = article_count_per_route * route_a_max_calls_per_article
    route_b_calls_per_article = {
        genre: int(info.get("source_count") or 0) + len(ROUTE_B_FIXED_STAGES) + 1
        for genre, info in genres.items()
    }
    route_b_estimated_max_calls = sum(route_b_calls_per_article.values()) * 3
    route_a_max_cost = _estimate_upper_bound_cost(
        model="gpt-5.4",
        call_count=route_a_estimated_max_calls,
        input_tokens_per_call=24_000,
        output_tokens_per_call=4_000,
    )
    route_b_max_cost = _estimate_upper_bound_cost(
        model="gpt-5.4-mini",
        call_count=route_b_estimated_max_calls,
        input_tokens_per_call=20_000,
        output_tokens_per_call=4_000,
    )
    return {
        "phase": "preflight_approval_gate",
        "external_llm_send_status": "not_sent",
        "planned_genre_count": len(genres),
        "planned_generation_count": article_count_per_route * 2,
        "route_a": {
            "route": "current_mainline",
            "default_changed": False,
            "repeat_per_genre": 3,
            "model_plan": {
                "base_model": "gpt-4.1-mini-2025-04-14",
                "task_models": {"section": "gpt-5.4-mini", "outline": "gpt-5.4", "lead": "gpt-5.4"},
                "reasoning_effort": "current config: none",
            },
            "estimated_max_api_call_count": route_a_estimated_max_calls,
            "estimated_max_cost_usd": route_a_max_cost,
        },
        "route_b_0506": {
            "route_id": ROUTE_B_0506_ROUTE_ID,
            "repeat_per_genre": 3,
            "model": "gpt-5.4-mini",
            "reasoning_effort": "high",
            "estimated_max_api_call_count": route_b_estimated_max_calls,
            "estimated_stage_calls_per_article": route_b_calls_per_article,
            "estimated_max_cost_usd": route_b_max_cost,
        },
        "estimated_max_api_call_count": route_a_estimated_max_calls + route_b_estimated_max_calls,
        "estimated_max_cost_usd": round(route_a_max_cost + route_b_max_cost, 6),
        "output_artifact_root": str(output_root),
        "approval_required_before_live": True,
    }


def _estimate_upper_bound_cost(
    *,
    model: str,
    call_count: int,
    input_tokens_per_call: int,
    output_tokens_per_call: int,
) -> float:
    return round(
        call_count * _cost_usd(model, input_tokens_per_call, 0, output_tokens_per_call),
        6,
    )


def _pricing_snapshot() -> dict[str, Any]:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pricing_mode": "standard",
        "note": "estimated_cost uses usage.input/output tokens; cached tokens default to 0 when not present",
        "models": PRICING,
        "official_sources": sorted({str(item["source"]) for item in PRICING.values()}),
    }


def _write_preflight_artifacts(output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    source_matrix = _build_source_matrix()
    api_send_plan = _estimated_plan(source_matrix, output_root)
    pricing_snapshot = _pricing_snapshot()
    _write_json(output_root / "source_matrix.json", source_matrix)
    _write_json(output_root / "api_send_plan.json", api_send_plan)
    _write_json(output_root / "pricing_snapshot.json", pricing_snapshot)
    _write_text(output_root / "api_usage_ledger.jsonl", "")
    _write_json(output_root / "per_article_cost_summary.json", {})
    _write_json(output_root / "per_genre_cost_summary.json", {})
    _write_json(output_root / "overall_cost_summary.json", {})
    _write_json(output_root / "per_genre_compare_summary.json", {})
    _write_json(output_root / "overall_compare_summary.json", {})
    _write_text(output_root / "manual_review_notes.md", _manual_review_template(source_matrix))
    return {
        "source_matrix": source_matrix,
        "api_send_plan": api_send_plan,
        "pricing_snapshot": pricing_snapshot,
    }


def _manual_review_template(source_matrix: Mapping[str, Any]) -> str:
    lines = [
        "# Manual Review Notes",
        "",
        "- status: preflight_only",
        "- external_llm_send: false",
        "- usage_source: pending actual API usage",
        "",
    ]
    for genre in dict(source_matrix.get("genres") or {}):
        lines.extend(
            [
                f"## {genre}",
                "- winner: TBD",
                "- manual Japanese blog naturalness note: TBD",
                "- review axes:",
            ]
        )
        lines.extend(f"  - {axis}: TBD" for axis in REVIEW_AXES)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


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


def _quality_warning_count_route_b(quality: Mapping[str, Any]) -> int:
    q = dict(quality.get("quality_check") or quality)
    return len(list(q.get("issues") or []))


def _source_grounding_warning_count_route_b(quality: Mapping[str, Any]) -> int:
    issues = list(dict(quality.get("quality_check") or quality).get("issues") or [])
    return sum(1 for item in issues if "source" in str(item).lower() or "ground" in str(item).lower())


def _article_id(route: str, genre: str, run_index: int) -> str:
    return f"route_{route.lower()}__{genre}__run_{run_index:02d}"


def _ledger_entries(
    *,
    route: str,
    genre: str,
    run_index: int,
    usage_records: Sequence[Mapping[str, Any]],
    reasoning_effort: str,
) -> list[dict[str, Any]]:
    rows = []
    for record in usage_records:
        rows.append(
            {
                "route": route,
                "genre": genre,
                "run_index": run_index,
                "article_id": _article_id(route, genre, run_index),
                "stage": str(record.get("stage") or ""),
                "model": str(record.get("model") or ""),
                "reasoning_effort": reasoning_effort,
                "input_tokens": int(record.get("input_tokens") or 0),
                "cached_input_tokens": int(record.get("cached_input_tokens") or 0),
                "output_tokens": int(record.get("output_tokens") or 0),
                "total_tokens": int(record.get("total_tokens") or 0),
                "estimated_cost_usd": float(record.get("estimated_cost_usd") or 0.0),
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
        "estimated_cost_usd": round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 8),
    }


def _run_route_a_live(case: UISweepCase, *, genre: str, run_index: int, run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    client = MeteredRouteALLMClient()
    pipeline = MinimalPipeline(llm_client=client)
    contract = build_current_mainline_payload(case)
    rows = _ledger_entries(
        route="A",
        genre=genre,
        run_index=run_index,
        usage_records=[],
        reasoning_effort="current config",
    )
    try:
        result = execute_current_mainline_generation(pipeline, contract, contract["prompt_raw"])
    except Exception as exc:
        usage_records = client.raw_usage_records
        if not usage_records:
            summary = client.get_usage_summary()
            usage_records = [_usage_from_token_tracker_item(item) for item in list(summary.usage_history or [])]
        rows = _ledger_entries(
            route="A",
            genre=genre,
            run_index=run_index,
            usage_records=usage_records,
            reasoning_effort="current config",
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json(run_dir / "api_usage.json", rows)
        raise RunBlockedError(_sanitize_error(exc), usage_rows=rows) from exc
    usage_records = client.raw_usage_records
    if not usage_records:
        summary = client.get_usage_summary()
        usage_records = [_usage_from_token_tracker_item(item) for item in list(summary.usage_history or [])]
    rows = _ledger_entries(
        route="A",
        genre=genre,
        run_index=run_index,
        usage_records=usage_records,
        reasoning_effort="current config",
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "latest_generation_output.json", result)
    _write_text(run_dir / "latest_generation_output.txt", _format_route_a_text(result))
    _write_json(
        run_dir / "latest_generation_quality_report.json",
        {
            "quality_warning_count": _quality_warning_count_route_a(result),
            "source_grounding_warning_count": _source_grounding_warning_count_route_a(result),
            "pipeline_check": dict(result.get("pipeline_check") or {}),
            "quality_pipeline_check": dict(result.get("quality_pipeline_check") or {}),
        },
    )
    _write_json(run_dir / "api_usage.json", rows)
    article = {
        "route": "A",
        "genre": genre,
        "run_index": run_index,
        "article_id": _article_id("A", genre, run_index),
        "status": "completed" if bool(result.get("success", False)) else "blocked",
        "reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or ""),
        "body_char_count": len(str(result.get("body") or "")),
        "qa_warning_count": _quality_warning_count_route_a(result),
        "source_grounding_warning_count": _source_grounding_warning_count_route_a(result),
        "artifact_dir": str(run_dir),
        **_summarize_usage(rows),
    }
    _write_json(run_dir / "article_summary.json", article)
    return article, rows


def _run_route_b_live(
    case: UISweepCase,
    *,
    genre: str,
    run_index: int,
    run_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    modules = _load_route_b_0506_modules(ROUTE_B_ROOT)
    contract = build_current_mainline_payload(case)
    records = extract_route_b_source_records(contract)
    if not records:
        raise RuntimeError(f"route_b_source_documents_missing:{genre}")
    extracted_sources = [
        _build_0506_extracted_source(modules, record, index)
        for index, record in enumerate(records, 1)
    ]
    client = MeteredRouteBOpenAIClient(model="gpt-5.4-mini", reasoning_effort="high")
    logger = modules["PipelineLogger"](run_id=run_dir.name, artifacts_dir=run_dir.parent)
    runner = modules["BlogPipelineRunner"](client=client, logger=logger)
    try:
        result = runner.run_extracted_sources(
            extracted_sources,
            genre_id=resolve_route_b_0506_genre(contract),
            target_reader=str(contract.get("audience_profile") or "初めて内容を知る読者"),
            article_goal=str(contract.get("topic_statement") or contract.get("prompt_raw") or "ソースに基づいて自然なブログ記事を作る"),
            narrator=resolve_route_b_0506_narrator(contract),
        )
    except Exception as exc:
        rows = _ledger_entries(
            route="B",
            genre=genre,
            run_index=run_index,
            usage_records=client.usage_records,
            reasoning_effort="high",
        )
        _write_json(run_dir / "api_usage.json", rows)
        raise RunBlockedError(_sanitize_error(exc), usage_rows=rows) from exc
    rows = _ledger_entries(
        route="B",
        genre=genre,
        run_index=run_index,
        usage_records=client.usage_records,
        reasoning_effort="high",
    )
    _write_json(
        run_dir / "latest_generation_output.json",
        {
            "route_id": ROUTE_B_0506_ROUTE_ID,
            "external_llm_send": True,
            "source_snapshot_hash": route_b_source_snapshot_hash(records),
            "genre_id": resolve_route_b_0506_genre(contract),
            "final_article": result.final_article,
            "source_cards": result.source_cards,
            "knowledge_pack": result.knowledge_pack,
            "article_brief": result.article_brief,
            "quality_check": result.quality_check,
        },
    )
    _write_json(run_dir / "api_usage.json", rows)
    article = {
        "route": "B",
        "genre": genre,
        "run_index": run_index,
        "article_id": _article_id("B", genre, run_index),
        "status": "completed",
        "route_id": ROUTE_B_0506_ROUTE_ID,
        "body_char_count": len(str(result.final_article or "")),
        "qa_warning_count": _quality_warning_count_route_b(result.quality_check),
        "source_grounding_warning_count": _source_grounding_warning_count_route_b(result.quality_check),
        "artifact_dir": str(run_dir),
        **_summarize_usage(rows),
    }
    _write_json(run_dir / "article_summary.json", article)
    return article, rows


def _build_compare_summaries(article_summaries: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    per_article = {str(item.get("article_id")): dict(item) for item in article_summaries}
    per_genre: dict[str, Any] = {}
    for genre in GENRE_CASE_IDS:
        items = [dict(item) for item in article_summaries if str(item.get("genre")) == genre]
        route_a = [item for item in items if item.get("route") == "A"]
        route_b = [item for item in items if item.get("route") == "B"]
        per_genre[genre] = {
            "route_a": _summarize_usage(route_a),
            "route_b": _summarize_usage(route_b),
            "route_a_blocked_count": sum(1 for item in route_a if item.get("status") == "blocked"),
            "route_b_blocked_count": sum(1 for item in route_b if item.get("status") == "blocked"),
            "winner": "blocked" if len(route_a) < 3 or len(route_b) < 3 else "TBD_manual_review_required",
            "manual_japanese_blog_naturalness_note": "TBD",
        }
    overall_rows = [dict(item) for item in article_summaries]
    overall = {
        "decision": "blocked" if any(item.get("status") == "blocked" for item in overall_rows) else "continue_shadow",
        "route_a_estimated_cost_usd": round(
            sum(float(item.get("estimated_cost_usd") or 0.0) for item in overall_rows if item.get("route") == "A"),
            8,
        ),
        "route_b_estimated_cost_usd": round(
            sum(float(item.get("estimated_cost_usd") or 0.0) for item in overall_rows if item.get("route") == "B"),
            8,
        ),
        "total_estimated_cost_usd": round(sum(float(item.get("estimated_cost_usd") or 0.0) for item in overall_rows), 8),
        "total_generation_count": len(overall_rows),
        "usage_was_actual_api_usage": True,
    }
    return per_article, per_genre, overall


def _run_live(output_root: Path) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        blocked = {"status": "blocked", "reason": "OPENAI_API_KEY missing"}
        _write_json(output_root / "blocked.json", blocked)
        return blocked

    preflight = _write_preflight_artifacts(output_root)
    source_matrix = preflight["source_matrix"]
    casebook = _read_json(CASEBOOK_PATH)
    article_summaries: list[dict[str, Any]] = []
    all_ledger_rows: list[dict[str, Any]] = []
    ledger_path = output_root / "api_usage_ledger.jsonl"
    if ledger_path.exists():
        ledger_path.unlink()

    for genre, case_id in GENRE_CASE_IDS.items():
        entry = _find_case(casebook, case_id)
        case = _case_from_entry(entry, genre=genre)
        genre_snapshot = dict(dict(source_matrix["genres"])[genre])
        current_hash = _canonical_hash(genre_snapshot["source_snapshot"])
        if current_hash != genre_snapshot["source_snapshot_hash"]:
            raise RuntimeError(f"source_snapshot_hash_changed:{genre}")
        for run_index in range(1, 4):
            run_dir = output_root / "route_a" / genre / f"run_{run_index:02d}"
            try:
                article, rows = _run_route_a_live(case, genre=genre, run_index=run_index, run_dir=run_dir)
            except Exception as exc:
                rows = list(getattr(exc, "usage_rows", []) or [])
                article = {
                    "route": "A",
                    "genre": genre,
                    "run_index": run_index,
                    "article_id": _article_id("A", genre, run_index),
                    "status": "blocked",
                    "blocked_reason": _sanitize_error(exc),
                    "artifact_dir": str(run_dir),
                }
                _write_json(run_dir / "blocked.json", article)
            article_summaries.append(article)
            all_ledger_rows.extend(rows)
            for row in rows:
                _append_jsonl(ledger_path, row)

    for genre, case_id in GENRE_CASE_IDS.items():
        entry = _find_case(casebook, case_id)
        case = _case_from_entry(entry, genre=genre)
        for run_index in range(1, 4):
            run_dir = output_root / "route_b_0506" / genre / f"run_{run_index:02d}"
            try:
                article, rows = _run_route_b_live(case, genre=genre, run_index=run_index, run_dir=run_dir)
            except Exception as exc:
                rows = list(getattr(exc, "usage_rows", []) or [])
                article = {
                    "route": "B",
                    "genre": genre,
                    "run_index": run_index,
                    "article_id": _article_id("B", genre, run_index),
                    "status": "blocked",
                    "blocked_reason": _sanitize_error(exc),
                    "artifact_dir": str(run_dir),
                }
                _write_json(run_dir / "blocked.json", article)
            article_summaries.append(article)
            all_ledger_rows.extend(rows)
            for row in rows:
                _append_jsonl(ledger_path, row)

    per_article, per_genre, overall = _build_compare_summaries(article_summaries)
    _write_json(output_root / "per_article_cost_summary.json", per_article)
    _write_json(output_root / "per_genre_cost_summary.json", per_genre)
    _write_json(output_root / "overall_cost_summary.json", overall)
    _write_json(output_root / "per_genre_compare_summary.json", per_genre)
    _write_json(output_root / "overall_compare_summary.json", overall)
    _write_json(output_root / "article_run_summaries.json", article_summaries)
    return overall


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--approved-external-send", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    output_root = Path(args.output_root) if args.output_root else PROJECT_ROOT / "logs" / f"route_a_vs_route_b_0506_genre_matrix_{_now_stamp()}"
    if args.live and not args.approved_external_send:
        raise SystemExit("--live requires --approved-external-send")

    if args.live:
        payload = _run_live(output_root)
    else:
        payload = _write_preflight_artifacts(output_root)
        payload["workspace_report_route_b_0506"] = inspect_route_b_0506_workspace(ROUTE_B_ROOT)
        payload["openai_api_key_present"] = bool(os.getenv("OPENAI_API_KEY"))
        if not payload["openai_api_key_present"]:
            blocked = {"status": "blocked", "reason": "OPENAI_API_KEY missing"}
            _write_json(output_root / "blocked.json", blocked)
            payload["blocked"] = blocked

    if args.json:
        print(json.dumps({"output_root": str(output_root), **payload}, ensure_ascii=False, indent=2))
    else:
        print(f"output_root={output_root}")
        print(f"live={bool(args.live)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
