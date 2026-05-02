from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any


PROMPT_INJECTION_PATTERNS: list[tuple[str, str]] = [
    ("ignore previous instructions", "ignore_previous_instructions"),
    ("ignore all previous instructions", "ignore_all_previous_instructions"),
    ("disregard previous instructions", "disregard_previous_instructions"),
    ("act as", "role_change"),
    ("you are now", "role_change_alt"),
    ("pretend to be", "pretend_role"),
    ("forget everything", "context_reset"),
    ("start fresh", "context_reset_alt"),
    ("new task", "task_override"),
    ("reveal the system prompt", "reveal_system_prompt"),
    ("show the system prompt", "show_system_prompt"),
    ("developer message", "developer_message_reference"),
    ("system prompt", "system_prompt_reference"),
    ("output exactly", "forced_exact_output"),
    ("return the following", "forced_return_text"),
    ("ignore this", "partial_ignore"),
    ("disregard", "partial_ignore_alt"),
    ("do not use web search", "disable_search_instruction"),
    ("前の指示を無視", "ignore_previous_instructions_ja"),
    ("これまでの指示を無視", "ignore_previous_instructions_ja_alt"),
    ("以前の指示を無視", "ignore_previous_instructions_ja_alt2"),
    ("あなたは今から", "role_change_ja"),
    ("すべて忘れて", "context_reset_ja"),
    ("この指示は無視", "partial_ignore_ja"),
    ("システムプロンプト", "system_prompt_reference_ja"),
    ("開発者メッセージ", "developer_message_reference_ja"),
    ("内部指示", "internal_instruction_reference_ja"),
    ("この文字列だけを出力", "forced_exact_output_ja"),
    ("jsonではなく", "format_override_ja"),
    ("以下の通り出力", "forced_output_ja"),
    ("visibility_score", "score_override_attempt"),
    ("target_domain_hit", "flag_override_attempt"),
]


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def strip_invisible(text: str) -> str:
    cleaned = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", str(text or ""))
    return "".join(char for char in cleaned if unicodedata.category(char) != "Cf")


def count_japanese_characters(text: str) -> int:
    normalized = normalize_text(text)
    if not normalized:
        return 0
    return len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", normalized))


def should_shorten_query(text: str, threshold: int = 50) -> bool:
    return count_japanese_characters(text) > threshold


def split_multiline_keywords(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def split_csv(text: str) -> list[str]:
    return [part.strip() for part in (text or "").split(",") if part.strip()]


def join_csv(items: list[str]) -> str:
    return ", ".join(item for item in items if item)


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        value = normalize_text(item)
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def normalize_query_text(value: Any) -> str:
    normalized = normalize_text(str(value or "")).lower()
    if not normalized:
        return ""
    normalized = re.sub(r"[\s\u3000]+", "", normalized)
    normalized = re.sub(r"[「」『』（）()\[\]【】・,，。.!！?？:/／\-]+", "", normalized)
    return normalized


def build_expansion_signature(expanded_queries: list[str]) -> str:
    normalized = [normalize_query_text(query) for query in expanded_queries if normalize_query_text(query)]
    payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def detect_prompt_injection_signals(text: str) -> list[str]:
    normalized = normalize_text(strip_invisible(text)).lower()
    if not normalized:
        return []
    matched: list[str] = []
    for pattern, label in PROMPT_INJECTION_PATTERNS:
        if pattern in normalized and label not in matched:
            matched.append(label)
    return matched


def build_prompt_injection_signal(texts: list[str]) -> dict[str, Any]:
    matched_labels: list[str] = []
    for text in texts:
        for label in detect_prompt_injection_signals(text):
            if label not in matched_labels:
                matched_labels.append(label)
    return {
        "suspicious_prompt_injection": bool(matched_labels),
        "matched_patterns": matched_labels,
        "signal_count": len(matched_labels),
    }


def stabilize_analysis_output(output_json: dict[str, Any], keyword_raw: str, keyword_norm: str) -> dict[str, Any]:
    normalized = dict(output_json or {})
    normalized["keyword_raw"] = str(normalized.get("keyword_raw") or keyword_raw or "").strip()
    normalized["keyword_norm"] = str(normalized.get("keyword_norm") or keyword_norm or normalized["keyword_raw"]).strip()
    normalized["answer_snapshot"] = str(normalized.get("answer_snapshot") or "判定保留：回答の読み取りが不安定です。").strip()[:320]
    normalized["answer_text"] = str(normalized.get("answer_text") or normalized["answer_snapshot"] or "").strip()[:900]
    try:
        normalized["visibility_score"] = max(0, min(100, int(normalized.get("visibility_score") or 0)))
    except Exception:
        normalized["visibility_score"] = 0
    normalized["target_domain_hit"] = bool(normalized.get("target_domain_hit"))
    normalized["brand_mention_hit"] = bool(normalized.get("brand_mention_hit"))
    confidence = str(normalized.get("confidence") or "low").strip().lower()
    normalized["confidence"] = confidence if confidence in {"low", "medium", "high"} else "low"

    competitor_mentions: list[str] = []
    for item in normalized.get("competitor_mentions") or []:
        value = str(item or "").strip()
        if value and value not in competitor_mentions:
            competitor_mentions.append(value)
    normalized["competitor_mentions"] = competitor_mentions

    citations: list[dict[str, str]] = []
    for item in normalized.get("citations") or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or url).strip()
        if not url:
            continue
        citations.append({"url": url, "title": title})
    normalized["citations"] = citations[:8]
    normalized["citation_urls"] = [item["url"] for item in citations[:8]]

    recommended_actions: list[str] = []
    for item in normalized.get("recommended_actions") or []:
        value = str(item or "").strip()
        if value:
            recommended_actions.append(value[:100])
    fallback_actions = [
        "引用された外部ページの共通点を確認する",
        "不足している情報タイプのページを見直す",
        "同じ質問で再確認して傾向を比較する",
    ]
    while len(recommended_actions) < 3:
        recommended_actions.append(fallback_actions[len(recommended_actions)])
    normalized["recommended_actions"] = recommended_actions[:3]
    return normalized
