from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from statistics import mean, median, pvariance
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "app" / "config" / "stylometry.yaml"
SENTENCE_RE = re.compile(r"[^。！？!?]+[。！？!?]?")


def load_stylometry_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("stylometry config must be a mapping")
    return data


def split_sentences(text: str) -> list[str]:
    return [match.group(0).strip() for match in SENTENCE_RE.finditer(text) if match.group(0).strip()]


def split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]


def strip_markdown_headings(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def ending_bucket(sentence: str) -> str:
    stripped = sentence.rstrip("。！？!? \t\r\n")
    if stripped.endswith("できます"):
        return "できます"
    for suffix in ("ました", "ます", "です", "でしょう", "ください"):
        if stripped.endswith(suffix):
            return suffix
    if stripped.endswith(("か", "か。", "か？")):
        return "問いかけ"
    if stripped and re.search(r"[\u4e00-\u9fff\u30a0-\u30ff]$", stripped):
        return "名詞止め"
    return "other"


def _count_terms(text: str, terms: list[str]) -> dict[str, int]:
    return {term: text.count(term) for term in terms if text.count(term) > 0}


def _paragraph_shape(paragraphs: list[str]) -> list[int]:
    return [len(split_sentences(paragraph)) for paragraph in paragraphs]


def _issue(type_: str, severity: str, reason: str) -> dict[str, str]:
    return {"type": type_, "severity": severity, "reason": reason}


def analyze_text(text: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or load_stylometry_config()
    prose_text = strip_markdown_headings(text)
    sentences = split_sentences(prose_text)
    paragraphs = split_paragraphs(prose_text)
    sentence_lengths = [len(sentence.rstrip("。！？!?")) for sentence in sentences]
    paragraph_shape = _paragraph_shape(paragraphs)
    buckets = [ending_bucket(sentence) for sentence in sentences]
    connector_counts = _count_terms(text, cfg.get("connectors", []))
    first_person_counts = _count_terms(text, cfg.get("first_person_variants", []))
    third_party_counts = _count_terms(text, cfg.get("third_party_terms", []))
    frequent_word_counts = _count_terms(text, cfg.get("model_frequent_words", []))

    issue_candidates: list[dict[str, str]] = []
    long_limit = int(cfg.get("sentence", {}).get("long_sentence_chars", 90))
    if any(length > long_limit for length in sentence_lengths):
        issue_candidates.append(_issue("sentence_too_long", "medium", "long sentence exceeds configured limit"))

    if len(set(first_person_counts)) > 1:
        issue_candidates.append(_issue("narrator_mixing", "high", "multiple first-person variants appear"))
    if third_party_counts:
        issue_candidates.append(_issue("third_party_viewpoint_leakage", "high", "third-party viewpoint terms appear"))

    repeated_connectors = [term for term, count in connector_counts.items() if count >= 2]
    if repeated_connectors:
        issue_candidates.append(_issue("connector_repetition", "medium", "connector appears repeatedly"))

    repeated_frequent = [term for term, count in frequent_word_counts.items() if count >= 2]
    if repeated_frequent:
        issue_candidates.append(_issue("model_frequent_word", "medium", "model-frequent word appears repeatedly"))

    if len(buckets) >= 4:
        last_half = buckets[len(buckets) // 2 :]
        most_common_count = Counter(last_half).most_common(1)[0][1]
        if most_common_count / len(last_half) >= 0.75:
            issue_candidates.append(
                _issue("ending_bucket_monotony", "medium", "late-half endings concentrate in one bucket")
            )

    if len(paragraph_shape) >= 3 and len(set(paragraph_shape)) == 1:
        issue_candidates.append(
            _issue("paragraph_rhythm_monotony", "medium", "paragraphs share the same sentence count")
        )

    return {
        "sentence_count": len(sentences),
        "avg_sentence_length": mean(sentence_lengths) if sentence_lengths else 0,
        "median_sentence_length": median(sentence_lengths) if sentence_lengths else 0,
        "max_sentence_length": max(sentence_lengths) if sentence_lengths else 0,
        "sentence_length_variance": pvariance(sentence_lengths) if len(sentence_lengths) > 1 else 0,
        "paragraph_count": len(paragraphs),
        "paragraph_shape": paragraph_shape,
        "ending_distribution": dict(Counter(buckets)),
        "repeated_connectors": repeated_connectors,
        "first_person_variants": list(first_person_counts),
        "third_party_terms": list(third_party_counts),
        "model_frequent_words": [
            {"term": term, "count": count, "risk": "medium" if count >= 2 else "low"}
            for term, count in frequent_word_counts.items()
        ],
        "issue_candidates": issue_candidates,
    }
