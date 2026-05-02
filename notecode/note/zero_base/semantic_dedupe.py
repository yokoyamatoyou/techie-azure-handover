"""Semantic dedupe utilities for zero_base_v2."""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from math import sqrt
from typing import Any, Dict, List, Optional, Protocol, Sequence, Set, Tuple

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional import failure guard
    OpenAI = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*")
CONTENT_WORD_RE = re.compile(r"[一-龯々〆ヵヶぁ-んァ-ヶA-Za-z0-9]{2,}")
OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")
BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{12,}")
SECRET_KV_RE = re.compile(r"(?i)\b(api[_-]?key|authorization|password|secret)\s*[:=]\s*\S+")
ANNOUNCEMENT_DATETIME_RE = re.compile(
    r"(\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}|午前|午後|\d{1,2}時)"
)

DEFAULT_SEMANTIC_DEDUPE_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "provider_mode": "hybrid",
    "model": "text-embedding-3-small",
    "similarity_threshold": 0.84,
    "content_overlap_threshold": 0.42,
    "high_overlap_shortcut_threshold": 0.62,
    "relaxed_similarity_threshold": 0.78,
    "min_shared_content_words": 3,
    "timeout_seconds": 20.0,
    "max_retries": 1,
    "retry_backoff_seconds": 0.8,
    "network_fail_cooldown_seconds": 180.0,
    "max_sentences": 96,
    "max_chars_per_sentence": 280,
}

LOCAL_LEXICAL_SIMILARITY_THRESHOLD = 0.9
_EMBEDDING_CIRCUIT_STATE: Dict[str, Dict[str, float]] = {}


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        """Return embedding vectors in input order."""


@dataclass
class SentenceUnit:
    index: int
    line_index: int
    text: str
    normalized: str
    content_words: Set[str]
    required: bool = False
    embedding: List[float] = field(default_factory=list)


@dataclass(frozen=True)
class PairEvidence:
    overlap: float
    common_words: int
    exact_text_match: bool
    containment_match: bool
    lexical_similarity: float
    local_duplicate: bool
    remote_candidate: bool


@dataclass
class SemanticDedupeAudit:
    model: str
    provider_mode: str = "hybrid"
    resolved_provider_mode: str = "hybrid"
    sentence_count: int = 0
    compared_pairs: int = 0
    duplicate_pairs: int = 0
    local_duplicate_pairs: int = 0
    merged_pairs: int = 0
    fail_open: bool = False
    fail_reason: str = ""
    embedding_attempted: bool = False
    embedding_used: bool = False
    embedding_sentence_count: int = 0
    remote_candidate_pair_count: int = 0
    embedding_skipped_reason: str = ""
    circuit_open: bool = False
    must_cover_protected_count: int = 0
    category_protected_count: int = 0
    regenerated_paragraphs: int = 0
    redaction_applied_count: int = 0
    deletion_reasons: List[Dict[str, Any]] = field(default_factory=list)
    protection_reasons: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "provider_mode": self.provider_mode,
            "resolved_provider_mode": self.resolved_provider_mode,
            "sentence_count": self.sentence_count,
            "compared_pairs": self.compared_pairs,
            "duplicate_pairs": self.duplicate_pairs,
            "local_duplicate_pairs": self.local_duplicate_pairs,
            "merged_pairs": self.merged_pairs,
            "fail_open": self.fail_open,
            "fail_reason": self.fail_reason,
            "embedding_attempted": self.embedding_attempted,
            "embedding_used": self.embedding_used,
            "embedding_sentence_count": self.embedding_sentence_count,
            "remote_candidate_pair_count": self.remote_candidate_pair_count,
            "embedding_skipped_reason": self.embedding_skipped_reason,
            "circuit_open": self.circuit_open,
            "must_cover_protected_count": self.must_cover_protected_count,
            "category_protected_count": self.category_protected_count,
            "regenerated_paragraphs": self.regenerated_paragraphs,
            "redaction_applied_count": self.redaction_applied_count,
            "deletion_reasons": list(self.deletion_reasons),
            "protection_reasons": list(self.protection_reasons),
        }


class OpenAIEmbeddingProvider:
    """OpenAI embeddings wrapper with bounded retry (DoS-safe)."""

    def __init__(
        self,
        *,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        retry_backoff_seconds: float,
        api_key: Optional[str] = None,
    ) -> None:
        if OpenAI is None:
            raise RuntimeError("openai package is unavailable")
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        self.model = model
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff_seconds = max(0.1, float(retry_backoff_seconds))
        self.client = OpenAI(api_key=resolved_key, timeout=float(timeout_seconds))

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return "rate limit" in text or "too many requests" in text or " 429" in text or text.startswith("429")

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                response = self.client.embeddings.create(model=self.model, input=list(texts))
                data = getattr(response, "data", None)
                if data is None and isinstance(response, dict):
                    data = response.get("data")
                if not isinstance(data, list):
                    raise RuntimeError("embeddings response does not include data list")
                sorted_data = sorted(
                    data,
                    key=lambda item: getattr(item, "index", item.get("index", 0) if isinstance(item, dict) else 0),
                )
                vectors: List[List[float]] = []
                for item in sorted_data:
                    if isinstance(item, dict):
                        vector = item.get("embedding")
                    else:
                        vector = getattr(item, "embedding", None)
                    if not isinstance(vector, list):
                        raise RuntimeError("embedding vector is missing")
                    vectors.append([float(value) for value in vector])
                if len(vectors) != len(texts):
                    raise RuntimeError("embedding response length mismatch")
                return vectors
            except Exception as exc:
                if attempt < attempts - 1 and self._is_rate_limit_error(exc):
                    wait_time = self.retry_backoff_seconds * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                raise
        raise RuntimeError("unreachable embedding retry state")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _split_sentences(text: str) -> List[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []
    pieces = [item.strip() for item in SENTENCE_SPLIT_RE.split(normalized) if item.strip()]
    if not pieces:
        return [normalized]
    return pieces


def _extract_content_words(text: str) -> Set[str]:
    words: Set[str] = set()
    for token in CONTENT_WORD_RE.findall(text):
        cleaned = token.strip().lower()
        if len(cleaned) >= 2:
            words.add(cleaned)
    return words


def _content_overlap_score(words_a: Set[str], words_b: Set[str]) -> float:
    if not words_a or not words_b:
        return 0.0
    common = len(words_a & words_b)
    baseline = max(1, min(len(words_a), len(words_b)))
    return common / baseline


def _cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    numerator = sum(float(a) * float(b) for a, b in zip(vec_a, vec_b))
    denom_a = sqrt(sum(float(a) * float(a) for a in vec_a))
    denom_b = sqrt(sum(float(b) * float(b) for b in vec_b))
    if denom_a <= 0.0 or denom_b <= 0.0:
        return 0.0
    return numerator / (denom_a * denom_b)


def _lexical_similarity_score(text_a: str, text_b: str) -> float:
    normalized_a = _normalize_text(text_a)
    normalized_b = _normalize_text(text_b)
    if not normalized_a or not normalized_b:
        return 0.0
    if normalized_a == normalized_b:
        return 1.0
    return SequenceMatcher(None, normalized_a, normalized_b).ratio()


def _pair_key(index_a: int, index_b: int) -> Tuple[int, int]:
    if index_a <= index_b:
        return index_a, index_b
    return index_b, index_a


def _is_embedding_circuit_open(model: str, cooldown_seconds: float) -> bool:
    state = _EMBEDDING_CIRCUIT_STATE.get(str(model or ""))
    if not state:
        return False
    open_until = float(state.get("open_until", 0.0) or 0.0)
    if open_until <= time.monotonic():
        _EMBEDDING_CIRCUIT_STATE.pop(str(model or ""), None)
        return False
    return open_until > time.monotonic() and cooldown_seconds > 0.0


def _record_embedding_circuit_failure(model: str, cooldown_seconds: float) -> None:
    if cooldown_seconds <= 0.0:
        return
    _EMBEDDING_CIRCUIT_STATE[str(model or "")] = {
        "open_until": time.monotonic() + float(cooldown_seconds),
    }


def _record_embedding_circuit_success(model: str) -> None:
    _EMBEDDING_CIRCUIT_STATE.pop(str(model or ""), None)


def _mask_sensitive_text(text: str) -> Tuple[str, bool]:
    masked = text or ""
    original = masked
    masked = OPENAI_KEY_RE.sub("[REDACTED_OPENAI_KEY]", masked)
    masked = BEARER_RE.sub("Bearer [REDACTED_TOKEN]", masked)
    masked = SECRET_KV_RE.sub(r"\1=[REDACTED]", masked)
    return masked, masked != original


def _prepare_embedding_input(text: str, max_chars: int) -> Tuple[str, bool]:
    masked, changed = _mask_sensitive_text(text)
    compact = _normalize_text(masked)
    if len(compact) > max_chars:
        compact = compact[:max_chars]
        changed = True
    return compact or "内容", changed


def _safe_excerpt(text: str, max_chars: int = 90) -> str:
    masked, _ = _mask_sensitive_text(text)
    compact = _normalize_text(masked)
    if len(compact) > max_chars:
        return compact[:max_chars]
    return compact


def _is_structural_line(line: str) -> bool:
    stripped = (line or "").strip()
    if not stripped:
        return True
    if stripped.startswith("#") or stripped.startswith("- ") or stripped.startswith("出典:"):
        return True
    if re.match(r"^https?://", stripped):
        return True
    return False


def _is_announcement_contract(contract: Dict[str, Any]) -> bool:
    article_type = str(contract.get("article_type", "") or "").strip().lower()
    category_template = str(contract.get("category_base_template", "") or "").strip().lower()
    return article_type == "announcement" or category_template == "announcement"


def _contains_datetime(text: str) -> bool:
    return bool(ANNOUNCEMENT_DATETIME_RE.search(text or ""))


def _extract_datetime_sentences(text: str) -> List[str]:
    results: List[str] = []
    for sentence in _split_sentences(text):
        if _contains_datetime(sentence):
            results.append(sentence)
    return results


def _select_duplicate_sentence(base: str, candidate: str) -> str:
    clean_base = _normalize_text(base)
    clean_candidate = _normalize_text(candidate)
    if not clean_base:
        return clean_candidate
    if not clean_candidate:
        return clean_base
    if clean_candidate in clean_base:
        return clean_base
    if clean_base in clean_candidate:
        return clean_candidate
    base_words = _extract_content_words(clean_base)
    candidate_words = _extract_content_words(clean_candidate)
    base_score = _sentence_info_score(clean_base, base_words)
    candidate_score = _sentence_info_score(clean_candidate, candidate_words)
    if candidate_score > base_score:
        return clean_candidate
    return clean_base


def _sentence_info_score(sentence: str, words: Optional[Set[str]] = None) -> float:
    normalized = _normalize_text(sentence)
    if not normalized:
        return 0.0
    resolved_words = words if words is not None else _extract_content_words(normalized)
    score = len(resolved_words) * 2.0 + min(120, len(normalized)) * 0.025
    if re.search(r"\d", normalized):
        score += 0.8
    if "?" in normalized or "？" in normalized:
        score += 0.4
    if re.search(r"(具体|手順|要点|注意|根拠|比較|例|実務|条件|前提|限界|結果|変化)", normalized):
        score += 0.6
    return score


def _regenerate_fallback_sentence(removed_texts: Sequence[str]) -> str:
    best_sentence = ""
    best_score = -1.0
    for text in removed_texts:
        normalized = _normalize_text(text)
        if not normalized:
            continue
        score = _sentence_info_score(normalized)
        if score > best_score:
            best_sentence = normalized
            best_score = score
    return best_sentence


def _must_cover_items(contract: Dict[str, Any]) -> List[str]:
    raw = contract.get("must_cover", [])
    if not isinstance(raw, list):
        return []
    items: List[str] = []
    for item in raw:
        value = _normalize_text(str(item or ""))
        if value:
            items.append(value)
    return items


def _normalize_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(DEFAULT_SEMANTIC_DEDUPE_CONFIG)
    if isinstance(config, dict):
        merged.update(config)
    provider_mode = str(merged.get("provider_mode") or DEFAULT_SEMANTIC_DEDUPE_CONFIG["provider_mode"]).strip().lower()
    if provider_mode not in {"hybrid", "local_only"}:
        provider_mode = str(DEFAULT_SEMANTIC_DEDUPE_CONFIG["provider_mode"])
    return {
        "enabled": bool(merged.get("enabled", True)),
        "provider_mode": provider_mode,
        "model": str(merged.get("model") or DEFAULT_SEMANTIC_DEDUPE_CONFIG["model"]),
        "similarity_threshold": float(merged.get("similarity_threshold", 0.84)),
        "content_overlap_threshold": float(merged.get("content_overlap_threshold", 0.42)),
        "high_overlap_shortcut_threshold": float(merged.get("high_overlap_shortcut_threshold", 0.62)),
        "relaxed_similarity_threshold": float(merged.get("relaxed_similarity_threshold", 0.78)),
        "min_shared_content_words": int(merged.get("min_shared_content_words", 3)),
        "timeout_seconds": float(merged.get("timeout_seconds", 20.0)),
        "max_retries": int(merged.get("max_retries", 1)),
        "retry_backoff_seconds": float(merged.get("retry_backoff_seconds", 0.8)),
        "network_fail_cooldown_seconds": float(merged.get("network_fail_cooldown_seconds", 180.0)),
        "max_sentences": int(merged.get("max_sentences", 96)),
        "max_chars_per_sentence": int(merged.get("max_chars_per_sentence", 280)),
    }


def semantic_dedupe_text(
    body: str,
    contract: Dict[str, Any],
    *,
    config: Optional[Dict[str, Any]] = None,
    embedder: Optional[EmbeddingProvider] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Apply embedding-based semantic dedupe with fail-open behavior."""
    resolved_config = _normalize_config(config)
    audit = SemanticDedupeAudit(
        model=resolved_config["model"],
        provider_mode=str(resolved_config["provider_mode"]),
        resolved_provider_mode=str(resolved_config["provider_mode"]),
    )
    text = body or ""
    if not resolved_config["enabled"] or not text.strip():
        return text, audit.to_dict()

    lines = text.split("\n")
    units: List[SentenceUnit] = []
    line_to_sentence_indices: Dict[int, List[int]] = {}
    must_cover = _must_cover_items(contract)
    announcement_mode = _is_announcement_contract(contract)
    reason_limit = 40

    def _append_reason(bucket: List[Dict[str, Any]], payload: Dict[str, Any]) -> None:
        if len(bucket) < reason_limit:
            bucket.append(payload)

    for line_index, line in enumerate(lines):
        stripped = line.strip()
        if _is_structural_line(line):
            continue
        sentences = _split_sentences(stripped)
        if not sentences:
            continue
        indices: List[int] = []
        for sentence in sentences:
            normalized = _normalize_text(sentence)
            if not normalized:
                continue
            required_by_must_cover = any(item and item in normalized for item in must_cover)
            required_by_category = announcement_mode and _contains_datetime(normalized)
            unit = SentenceUnit(
                index=len(units),
                line_index=line_index,
                text=normalized,
                normalized=normalized,
                content_words=_extract_content_words(normalized),
                required=required_by_must_cover or required_by_category,
            )
            if required_by_must_cover:
                audit.must_cover_protected_count += 1
                _append_reason(
                    audit.protection_reasons,
                    {
                        "sentence_index": unit.index,
                        "line_index": line_index,
                        "reason": "must_cover_protected",
                        "text_excerpt": _safe_excerpt(normalized),
                    },
                )
            if required_by_category:
                audit.category_protected_count += 1
                _append_reason(
                    audit.protection_reasons,
                    {
                        "sentence_index": unit.index,
                        "line_index": line_index,
                        "reason": "category_datetime_protected",
                        "text_excerpt": _safe_excerpt(normalized),
                    },
                )
            units.append(unit)
            indices.append(unit.index)
        if indices:
            line_to_sentence_indices[line_index] = indices

    audit.sentence_count = len(units)
    if len(units) <= 1:
        return text, audit.to_dict()

    limited_units = units[: max(1, resolved_config["max_sentences"])]
    if len(limited_units) < len(units):
        # In fail-open spirit: keep truncated analysis scope, keep untouched tail.
        units = limited_units
        line_to_sentence_indices = {
            line_idx: filtered_indices
            for line_idx, indices in line_to_sentence_indices.items()
            if (filtered_indices := [idx for idx in indices if idx < len(units)])
        }

    similarity_threshold = float(resolved_config["similarity_threshold"])
    overlap_threshold = float(resolved_config["content_overlap_threshold"])
    high_overlap_shortcut = float(resolved_config["high_overlap_shortcut_threshold"])
    relaxed_similarity_threshold = float(resolved_config["relaxed_similarity_threshold"])
    min_shared_content_words = max(1, int(resolved_config["min_shared_content_words"]))
    pair_evidence_map: Dict[Tuple[int, int], PairEvidence] = {}
    remote_candidate_pairs: List[Tuple[int, int]] = []

    for unit in units:
        for other in units[: unit.index]:
            overlap = _content_overlap_score(unit.content_words, other.content_words)
            common_words = len(unit.content_words & other.content_words)
            exact_text_match = unit.normalized == other.normalized
            containment_match = bool(
                unit.normalized
                and other.normalized
                and (unit.normalized in other.normalized or other.normalized in unit.normalized)
            )
            lexical_similarity = _lexical_similarity_score(unit.normalized, other.normalized)
            local_duplicate = bool(
                exact_text_match
                or (
                    overlap >= high_overlap_shortcut
                    and common_words >= min_shared_content_words
                    and (containment_match or lexical_similarity >= LOCAL_LEXICAL_SIMILARITY_THRESHOLD)
                )
            )
            remote_candidate = bool(
                not local_duplicate
                and overlap >= overlap_threshold
                and common_words >= min_shared_content_words
            )
            if not (local_duplicate or remote_candidate):
                continue
            pair_evidence_map[_pair_key(unit.index, other.index)] = PairEvidence(
                overlap=overlap,
                common_words=common_words,
                exact_text_match=exact_text_match,
                containment_match=containment_match,
                lexical_similarity=lexical_similarity,
                local_duplicate=local_duplicate,
                remote_candidate=remote_candidate,
            )
            if remote_candidate:
                remote_candidate_pairs.append((other.index, unit.index))

    audit.remote_candidate_pair_count = len(remote_candidate_pairs)
    provider = embedder
    circuit_cooldown_seconds = max(0.0, float(resolved_config["network_fail_cooldown_seconds"]))

    def _degrade_to_local_only(reason: str, exc: Optional[Exception] = None) -> None:
        audit.fail_open = True
        audit.fail_reason = reason
        audit.circuit_open = circuit_cooldown_seconds > 0.0
        audit.resolved_provider_mode = "local_only_after_remote_failure"
        audit.embedding_skipped_reason = reason.split(":", 1)[0]
        _record_embedding_circuit_failure(str(resolved_config["model"]), circuit_cooldown_seconds)
        if exc is None:
            logger.warning("semantic_dedupe degraded to local-only: %s", reason)
            return
        logger.warning("semantic_dedupe degraded to local-only: %s", exc)
        logger.debug("semantic_dedupe remote failure detail.", exc_info=exc)

    if audit.provider_mode == "local_only":
        audit.embedding_skipped_reason = "provider_mode_local_only"
        audit.resolved_provider_mode = "local_only"
    elif not remote_candidate_pairs:
        audit.embedding_skipped_reason = "no_remote_candidate_pairs"
    else:
        audit.circuit_open = _is_embedding_circuit_open(str(resolved_config["model"]), circuit_cooldown_seconds)
        if audit.circuit_open:
            audit.embedding_skipped_reason = "circuit_open"
            audit.resolved_provider_mode = "local_only_circuit_open"
        else:
            candidate_indices = sorted({idx for pair in remote_candidate_pairs for idx in pair})
            audit.embedding_attempted = True
            audit.embedding_sentence_count = len(candidate_indices)
            if provider is None:
                try:
                    provider = OpenAIEmbeddingProvider(
                        model=resolved_config["model"],
                        timeout_seconds=resolved_config["timeout_seconds"],
                        max_retries=resolved_config["max_retries"],
                        retry_backoff_seconds=resolved_config["retry_backoff_seconds"],
                    )
                except Exception as exc:
                    _degrade_to_local_only(f"embedder_init_failed:{type(exc).__name__}", exc)
                    provider = None
            if provider is not None:
                embedding_inputs: List[str] = []
                for idx in candidate_indices:
                    prepared, redacted = _prepare_embedding_input(
                        units[idx].text,
                        max_chars=max(80, resolved_config["max_chars_per_sentence"]),
                    )
                    embedding_inputs.append(prepared)
                    if redacted:
                        audit.redaction_applied_count += 1
                try:
                    vectors = provider.embed_texts(embedding_inputs)
                    if len(vectors) != len(candidate_indices):
                        raise RuntimeError("embedding_length_mismatch")
                except Exception as exc:
                    if isinstance(exc, RuntimeError) and str(exc) == "embedding_length_mismatch":
                        _degrade_to_local_only("embedding_length_mismatch", exc)
                    else:
                        _degrade_to_local_only(f"embed_call_failed:{type(exc).__name__}", exc)
                else:
                    for idx, vector in zip(candidate_indices, vectors):
                        units[idx].embedding = vector
                    audit.embedding_used = True
                    _record_embedding_circuit_success(str(resolved_config["model"]))

    representative_map: Dict[int, int] = {}
    representatives: List[int] = []

    def _match_details(unit: SentenceUnit, rep_unit: SentenceUnit) -> Tuple[bool, str, float, float, int]:
        evidence = pair_evidence_map.get(_pair_key(unit.index, rep_unit.index))
        if evidence is None:
            return False, "", 0.0, 0.0, 0
        if evidence.local_duplicate:
            if evidence.exact_text_match:
                return True, "exact_text_match", 1.0, evidence.overlap, evidence.common_words
            if evidence.containment_match:
                return True, "local_containment_match", max(0.95, evidence.lexical_similarity), evidence.overlap, evidence.common_words
            return True, "local_lexical_match", evidence.lexical_similarity, evidence.overlap, evidence.common_words
        if not evidence.remote_candidate or not audit.embedding_used:
            return False, "", 0.0, evidence.overlap, evidence.common_words
        similarity = _cosine_similarity(unit.embedding, rep_unit.embedding)
        audit.compared_pairs += 1
        meets_direct = (
            similarity >= similarity_threshold
            and evidence.common_words >= min_shared_content_words
        )
        meets_shortcut = (
            evidence.overlap >= high_overlap_shortcut
            and similarity >= relaxed_similarity_threshold
            and evidence.common_words >= (min_shared_content_words + 1)
        )
        if not (meets_direct or meets_shortcut):
            return False, "", similarity, evidence.overlap, evidence.common_words
        rule = "direct_threshold" if meets_direct else "high_overlap_shortcut"
        return True, rule, similarity, evidence.overlap, evidence.common_words

    def _is_local_rule(rule: str) -> bool:
        return rule in {"exact_text_match", "local_containment_match", "local_lexical_match"}

    for unit in units:
        if unit.required:
            for rep_index in list(representatives):
                rep_unit = units[rep_index]
                if rep_unit.required:
                    continue
                matched, rule, similarity, overlap, common_words = _match_details(unit, rep_unit)
                if not matched:
                    continue
                previous_rep = rep_index
                representative_map[previous_rep] = unit.index
                for key, mapped in list(representative_map.items()):
                    if mapped == previous_rep:
                        representative_map[key] = unit.index
                representatives = [idx for idx in representatives if idx != previous_rep]
                audit.duplicate_pairs += 1
                if _is_local_rule(rule):
                    audit.local_duplicate_pairs += 1
                _append_reason(
                    audit.deletion_reasons,
                    {
                        "removed_index": previous_rep,
                        "kept_index": unit.index,
                        "reason": "required_sentence_priority",
                        "match_rule": rule,
                        "similarity": round(similarity, 4),
                        "content_overlap": round(overlap, 4),
                        "common_words": common_words,
                    },
                )
            representative_map[unit.index] = unit.index
            representatives.append(unit.index)
            continue

        best_rep: Optional[int] = None
        best_similarity = 0.0
        best_overlap = 0.0
        best_common_words = 0
        best_rule = ""
        for rep_index in representatives:
            rep_unit = units[rep_index]
            matched, similarity, overlap, common_words = False, 0.0, 0.0, 0
            matched, rule, similarity, overlap, common_words = _match_details(unit, rep_unit)
            if not matched:
                continue
            if similarity > best_similarity:
                best_similarity = similarity
                best_rep = rep_index
                best_overlap = overlap
                best_common_words = common_words
                best_rule = rule

        if best_rep is None:
            representative_map[unit.index] = unit.index
            representatives.append(unit.index)
            continue

        representative_map[unit.index] = best_rep
        audit.duplicate_pairs += 1
        if _is_local_rule(best_rule):
            audit.local_duplicate_pairs += 1
        selected = _select_duplicate_sentence(units[best_rep].text, unit.text)
        original_rep_text = units[best_rep].text
        if selected != original_rep_text:
            units[best_rep].text = selected
            units[best_rep].normalized = selected
            units[best_rep].content_words = _extract_content_words(selected)
            if selected not in {original_rep_text, unit.text}:
                audit.merged_pairs += 1
        _append_reason(
            audit.deletion_reasons,
            {
                "removed_index": unit.index,
                "kept_index": best_rep,
                "reason": best_rule or "semantic_duplicate",
                "similarity": round(best_similarity, 4),
                "content_overlap": round(best_overlap, 4),
                "common_words": best_common_words,
            },
        )

    rebuilt_lines: List[str] = []
    for line_index, line in enumerate(lines):
        if line_index not in line_to_sentence_indices:
            rebuilt_lines.append(line)
            continue
        sentence_indices = line_to_sentence_indices[line_index]
        if not sentence_indices:
            rebuilt_lines.append(line)
            continue
        kept_sentences: List[str] = []
        removed_sentences: List[str] = []
        for idx in sentence_indices:
            rep_idx = representative_map.get(idx, idx)
            if rep_idx == idx:
                kept_sentences.append(units[idx].text)
            else:
                removed_sentences.append(units[idx].text)
        if kept_sentences:
            rebuilt_lines.append("".join(kept_sentences))
            continue
        # 空段落化を避ける
        rebuilt_lines.append(_regenerate_fallback_sentence(removed_sentences))
        audit.regenerated_paragraphs += 1

    deduped_text = "\n".join(rebuilt_lines)

    for item in must_cover:
        if not item or item in deduped_text:
            continue
        fallback_sentence = ""
        for sentence in _split_sentences(text):
            normalized_sentence = _normalize_text(sentence)
            if item in normalized_sentence:
                fallback_sentence = normalized_sentence
                break
        if fallback_sentence and fallback_sentence not in deduped_text:
            deduped_text = deduped_text.rstrip() + "\n\n" + fallback_sentence
            audit.must_cover_protected_count += 1
            _append_reason(
                audit.protection_reasons,
                {
                    "reason": "must_cover_restored_after_dedupe",
                    "text_excerpt": _safe_excerpt(fallback_sentence),
                },
            )

    if announcement_mode:
        original_datetime_sentences = _extract_datetime_sentences(text)
        deduped_datetime_sentences = _extract_datetime_sentences(deduped_text)
        if original_datetime_sentences and not deduped_datetime_sentences:
            deduped_text = deduped_text.rstrip() + "\n\n" + original_datetime_sentences[0]
            audit.category_protected_count += 1
            _append_reason(
                audit.protection_reasons,
                {
                    "reason": "announcement_datetime_restored",
                    "text_excerpt": _safe_excerpt(original_datetime_sentences[0]),
                },
            )

    return deduped_text, audit.to_dict()
