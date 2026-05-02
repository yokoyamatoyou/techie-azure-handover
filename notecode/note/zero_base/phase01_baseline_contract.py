"""Phase01 baseline extraction and Intent Contract definitions."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from statistics import mean
from typing import Any

from note.policy_engine import resolve_category_policy

REQUIRED_INTENT_FIELDS = [
    "article_type",
    "category_base_template",
    "category_policy_source",
    "thesis",
    "audience",
    "intent",
    "style",
    "must_cover",
    "must_not_repeat",
    "pre_generation_questions",
    "pre_generation_answers",
    "unresolved_items",
    "cta",
    "evidence_mode",
    "question_source_priority",
]

DEFAULT_QUESTION_SOURCE_PRIORITY = [
    "interview_answers",
    "user_prompt",
    "unresolved_items",
]

_SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|authorization|secret|password|access[_-]?token|refresh[_-]?token|bearer)",
    re.IGNORECASE,
)

_KPI_KEYS = [
    "semantic_issue_count",
    "semantic_duplicate_rate",
    "transition_coherence_score",
    "subject_explicit_rate",
    "category_consistency_score",
    "question_reflection_rate",
]


def _is_blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _ensure_string(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return default
    return str(value).strip()


def _unique_non_empty(items: Sequence[Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        text = _ensure_string(item)
        if not text:
            continue
        key = _normalize_text(text)
        if key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def sanitize_sensitive(data: Any, *, key_hint: str = "") -> Any:
    """Redact sensitive values by key name to avoid leaking secrets."""
    if isinstance(data, Mapping):
        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            key_text = _ensure_string(key)
            if _SECRET_KEY_PATTERN.search(key_text):
                sanitized[key_text] = "***REDACTED***"
            else:
                sanitized[key_text] = sanitize_sensitive(value, key_hint=key_text)
        return sanitized
    if isinstance(data, list):
        return [sanitize_sensitive(item, key_hint=key_hint) for item in data]
    if _SECRET_KEY_PATTERN.search(key_hint):
        return "***REDACTED***"
    return data


def load_jsonl_records(log_path: Path) -> tuple[list[dict[str, Any]], int]:
    """Load JSONL records and skip malformed lines (fail-open)."""
    records: list[dict[str, Any]] = []
    malformed_count = 0

    if not log_path.exists():
        return records, malformed_count

    for line in log_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            malformed_count += 1
            continue
        if isinstance(parsed, dict):
            records.append(parsed)

    return records, malformed_count


def extract_recent_baseline(
    records: Sequence[dict[str, Any]],
    *,
    sample_size: int = 20,
    recommended_minimum: int = 10,
) -> dict[str, Any]:
    selected_count = min(sample_size, len(records))
    selected = list(records[-selected_count:])

    return {
        "metadata": {
            "requested_sample_size": sample_size,
            "selected_sample_size": selected_count,
            "total_valid_records": len(records),
            "recommended_minimum": recommended_minimum,
            "recommended_minimum_met": selected_count >= recommended_minimum,
        },
        "records": [sanitize_sensitive(record) for record in selected],
    }


def _read_nested(source: Mapping[str, Any], *path: str) -> Any:
    current: Any = source
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _extract_semantic_duplicate_rate(record: Mapping[str, Any]) -> float | None:
    retry_failures = _read_nested(record, "failed_parameters", "retry_failures")
    if isinstance(retry_failures, list):
        total = len(retry_failures)
        if total == 0:
            return 0.0
        redundant = 0
        for item in retry_failures:
            if isinstance(item, Mapping) and bool(item.get("redundant")):
                redundant += 1
        return redundant / total

    direct_value = _read_nested(record, "metrics", "semantic_duplicate_rate")
    return _as_float(direct_value)


def _extract_semantic_issue_count(record: Mapping[str, Any]) -> float | None:
    for path in (
        ("failed_parameters", "final_quality_eval", "metrics", "semantic_issue_count"),
        ("failed_parameters", "hard_soft_eval", "metrics", "semantic_issue_count"),
        ("failed_parameters", "contextual_naturalness_report", "semantic_issue_count"),
        ("metrics", "semantic_issue_count"),
    ):
        value = _as_float(_read_nested(record, *path))
        if value is not None:
            return value
    return None


def _extract_transition_coherence(record: Mapping[str, Any]) -> float | None:
    for path in (
        (
            "failed_parameters",
            "contextual_naturalness_report",
            "semantic_layout",
            "transition_jaccard_mean",
        ),
        ("metrics", "transition_coherence_score"),
    ):
        value = _as_float(_read_nested(record, *path))
        if value is not None:
            return value
    return None


def _extract_subject_explicit_rate(record: Mapping[str, Any]) -> float | None:
    for path in (
        ("failed_parameters", "fingerprint_phase", "subject_explicit_rate"),
        ("metrics", "subject_explicit_rate"),
    ):
        value = _as_float(_read_nested(record, *path))
        if value is not None:
            return value
    return None


def compute_category_consistency_score(
    article_type: str,
    category_base_template: str,
) -> float:
    if _is_blank(article_type) or _is_blank(category_base_template):
        return 0.0

    policy = resolve_category_policy(article_type)
    expected = _ensure_string(policy.base_template)
    if not expected:
        return 0.0
    return 1.0 if expected == _ensure_string(category_base_template) else 0.0


def compute_question_reflection_rate(contract: Mapping[str, Any]) -> float:
    answers_raw = contract.get("pre_generation_answers", {})
    must_cover_raw = contract.get("must_cover", [])

    if not isinstance(answers_raw, Mapping):
        return 0.0

    must_cover_text = " ".join(
        _normalize_text(item) for item in must_cover_raw if isinstance(item, str)
    )

    answered_values = [
        _normalize_text(value)
        for value in answers_raw.values()
        if isinstance(value, str) and value.strip()
    ]
    if not answered_values:
        return 1.0

    reflected = 0
    for answer in answered_values:
        if answer and answer in must_cover_text:
            reflected += 1

    return reflected / len(answered_values)


def compute_baseline_entry_kpis(record: Mapping[str, Any]) -> dict[str, float | None]:
    article_type = _ensure_string(record.get("article_type"))
    category_base_template = _ensure_string(record.get("category_base_template"))
    return {
        "semantic_issue_count": _extract_semantic_issue_count(record),
        "semantic_duplicate_rate": _extract_semantic_duplicate_rate(record),
        "transition_coherence_score": _extract_transition_coherence(record),
        "subject_explicit_rate": _extract_subject_explicit_rate(record),
        "category_consistency_score": (
            compute_category_consistency_score(article_type, category_base_template)
            if article_type and category_base_template
            else None
        ),
        "question_reflection_rate": None,
    }


def summarize_kpis(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, list[float]] = {key: [] for key in _KPI_KEYS}

    for record in records:
        snapshot = compute_baseline_entry_kpis(record)
        for key, value in snapshot.items():
            if isinstance(value, (int, float)):
                metrics[key].append(float(value))

    summary: dict[str, Any] = {}
    for key in _KPI_KEYS:
        values = metrics[key]
        if not values:
            summary[key] = {
                "count": 0,
                "mean": None,
                "min": None,
                "max": None,
            }
            continue
        summary[key] = {
            "count": len(values),
            "mean": round(mean(values), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }
    return summary


def _normalize_questions(raw_questions: Any) -> list[dict[str, str]]:
    if not isinstance(raw_questions, list):
        return []

    questions: list[dict[str, str]] = []
    for item in raw_questions:
        if not isinstance(item, Mapping):
            continue
        q_id = _ensure_string(item.get("id"))
        question = _ensure_string(item.get("question"))
        if not q_id:
            continue
        questions.append({"id": q_id, "question": question})
    return questions


def _normalize_answers(raw_answers: Any) -> dict[str, str]:
    if not isinstance(raw_answers, Mapping):
        return {}
    answers: dict[str, str] = {}
    for key, value in raw_answers.items():
        question_id = _ensure_string(key)
        answer = _ensure_string(value)
        if not question_id:
            continue
        answers[question_id] = answer
    return answers


def _question_role(question_id: str) -> str:
    key = _ensure_string(question_id).lower()
    if key in {"target", "audience", "reader"}:
        return "target"
    if key in {"perspective", "viewpoint", "persona"}:
        return "perspective"
    if key in {"message", "core_message", "main_message"}:
        return "message"
    if key in {"evidence", "fact", "proof"}:
        return "evidence"
    return key or "other"


def build_intent_contract(seed: Mapping[str, Any]) -> dict[str, Any]:
    questions = _normalize_questions(seed.get("pre_generation_questions"))
    answers = _normalize_answers(seed.get("pre_generation_answers"))

    must_cover_seed = list(seed.get("must_cover", []))
    answered_values = [
        value
        for qid, value in answers.items()
        if value and _question_role(qid) not in {"target", "perspective"}
    ]
    must_cover = _unique_non_empty([*must_cover_seed, *answered_values])
    must_not_repeat = _unique_non_empty(list(seed.get("must_not_repeat", [])))

    unresolved_seed = _unique_non_empty(list(seed.get("unresolved_items", [])))
    unresolved = list(unresolved_seed)
    for question in questions:
        q_id = question["id"]
        if not answers.get(q_id) and q_id not in unresolved:
            unresolved.append(q_id)

    question_source_priority_raw = seed.get("question_source_priority")
    question_source_priority = _unique_non_empty(
        list(question_source_priority_raw)
        if isinstance(question_source_priority_raw, list)
        else DEFAULT_QUESTION_SOURCE_PRIORITY
    )
    if not question_source_priority:
        question_source_priority = list(DEFAULT_QUESTION_SOURCE_PRIORITY)

    contract = {
        "article_type": _ensure_string(seed.get("article_type"), default="unknown"),
        "category_base_template": _ensure_string(seed.get("category_base_template")),
        "category_policy_source": _ensure_string(
            seed.get("category_policy_source"),
            default="phase01_contract",
        ),
        "thesis": _ensure_string(seed.get("thesis")),
        "audience": _ensure_string(seed.get("audience")),
        "intent": _ensure_string(seed.get("intent")),
        "style": _ensure_string(seed.get("style")),
        "must_cover": must_cover,
        "must_not_repeat": must_not_repeat,
        "pre_generation_questions": questions,
        "pre_generation_answers": answers,
        "unresolved_items": unresolved,
        "cta": _ensure_string(seed.get("cta")),
        "evidence_mode": _ensure_string(seed.get("evidence_mode"), default="normal"),
        "question_source_priority": question_source_priority,
    }
    return contract


def compute_contract_kpis(contract: Mapping[str, Any]) -> dict[str, float]:
    return {
        "category_consistency_score": compute_category_consistency_score(
            _ensure_string(contract.get("article_type")),
            _ensure_string(contract.get("category_base_template")),
        ),
        "question_reflection_rate": compute_question_reflection_rate(contract),
    }


def build_intent_contract_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Intent Contract",
        "type": "object",
        "required": REQUIRED_INTENT_FIELDS,
        "properties": {
            "article_type": {"type": "string", "minLength": 1},
            "category_base_template": {"type": "string"},
            "category_policy_source": {"type": "string"},
            "thesis": {"type": "string"},
            "audience": {"type": "string"},
            "intent": {"type": "string"},
            "style": {"type": "string"},
            "must_cover": {"type": "array", "items": {"type": "string"}},
            "must_not_repeat": {"type": "array", "items": {"type": "string"}},
            "pre_generation_questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "question"],
                    "properties": {
                        "id": {"type": "string", "minLength": 1},
                        "question": {"type": "string"},
                    },
                },
            },
            "pre_generation_answers": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
            "unresolved_items": {"type": "array", "items": {"type": "string"}},
            "cta": {"type": "string"},
            "evidence_mode": {"type": "string"},
            "question_source_priority": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
            },
        },
        "additionalProperties": True,
    }


def _render_kpi_markdown(kpi_summary: Mapping[str, Any]) -> str:
    lines = [
        "# KPI Definition (Phase01)",
        "",
        "| KPI | Description | Baseline mean | Count |",
        "|---|---|---:|---:|",
    ]
    descriptions = {
        "semantic_issue_count": "意味不整合・論点ずれの件数（低いほど良い）",
        "semantic_duplicate_rate": "同義反復率（retry冗長判定比率、低いほど良い）",
        "transition_coherence_score": "セクション遷移の一貫性（高いほど良い）",
        "subject_explicit_rate": "主語明示率（高すぎる直訳調を監視）",
        "category_consistency_score": "article_type と category_base_template の整合率",
        "question_reflection_rate": "生成前質問回答の must_cover 反映率",
    }
    for key in _KPI_KEYS:
        item = kpi_summary.get(key, {})
        mean_value = item.get("mean")
        count_value = item.get("count")
        mean_text = "-" if mean_value is None else f"{mean_value:.4f}"
        count_text = "-" if count_value is None else str(count_value)
        lines.append(
            f"| {key} | {descriptions[key]} | {mean_text} | {count_text} |"
        )
    lines.append("")
    lines.append("備考: category/question KPIは phase04以降で実測値を主計測へ移行。")
    return "\n".join(lines)


def _build_default_contract_seed(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    latest = records[-1] if records else {}
    article_type = _ensure_string(latest.get("article_type"), default="ai")
    category_policy = resolve_category_policy(article_type)
    category_base_template = _ensure_string(category_policy.base_template, default="ai")
    return {
        "article_type": article_type,
        "category_base_template": category_base_template,
        "category_policy_source": "policy_engine.resolve_category_policy",
        "thesis": "一次情報ベースで論点を明確化する",
        "audience": "業務で活用したい実務担当者",
        "intent": "判断材料を提供し、次の行動を明確化する",
        "style": "balanced",
        "must_cover": [],
        "must_not_repeat": ["同義反復", "過度な断定表現"],
        "pre_generation_questions": [
            {"id": "message", "question": "核心メッセージを1文で教えてください。"},
            {"id": "target", "question": "主な読者層は誰ですか。"},
            {"id": "evidence", "question": "優先する根拠種別は何ですか。"},
        ],
        "pre_generation_answers": {
            "message": "結論と根拠を分けて示す",
            "target": "導入検討中の担当者",
        },
        "unresolved_items": [],
        "cta": "次の検証ステップを1つ実行する",
        "evidence_mode": "strict",
        "question_source_priority": list(DEFAULT_QUESTION_SOURCE_PRIORITY),
    }


def write_phase01_artifacts(
    *,
    log_path: Path,
    output_dir: Path,
    sample_size: int = 20,
) -> dict[str, Path]:
    records, malformed_count = load_jsonl_records(log_path)
    baseline = extract_recent_baseline(records, sample_size=sample_size)
    baseline["metadata"]["malformed_lines_skipped"] = malformed_count
    baseline["kpi_summary"] = summarize_kpis(baseline["records"])

    contract_seed = _build_default_contract_seed(baseline["records"])
    contract = build_intent_contract(contract_seed)
    contract_kpis = compute_contract_kpis(contract)

    schema = build_intent_contract_schema()
    schema["examples"] = [contract]

    output_dir.mkdir(parents=True, exist_ok=True)
    date_tag = "2026-03-04"

    baseline_path = output_dir / f"baseline_{date_tag}.json"
    schema_path = output_dir / f"intent_contract_schema_{date_tag}.json"
    kpi_path = output_dir / f"kpi_definition_{date_tag}.md"
    result_path = output_dir / f"phase01_result_{date_tag}.md"

    baseline_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    schema_path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    kpi_path.write_text(_render_kpi_markdown(baseline["kpi_summary"]), encoding="utf-8")

    result_markdown = "\n".join(
        [
            "# Phase01 Result",
            "",
            "## Summary",
            f"- baseline_records: {baseline['metadata']['selected_sample_size']}",
            f"- malformed_lines_skipped: {baseline['metadata']['malformed_lines_skipped']}",
            f"- category_consistency_score(contract): {contract_kpis['category_consistency_score']:.4f}",
            f"- question_reflection_rate(contract): {contract_kpis['question_reflection_rate']:.4f}",
            "",
            "## Generated Files",
            f"- {baseline_path.name}",
            f"- {schema_path.name}",
            f"- {kpi_path.name}",
            "",
            "## Notes",
            "- baseline抽出は破損JSON行をスキップする fail-open 実装。",
            "- 質問回答は must_cover へ自動反映し、未回答は unresolved_items へ集約。",
            "",
        ]
    )
    result_path.write_text(result_markdown, encoding="utf-8")

    return {
        "baseline": baseline_path,
        "schema": schema_path,
        "kpi": kpi_path,
        "result": result_path,
    }
