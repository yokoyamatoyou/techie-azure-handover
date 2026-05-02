"""Bootstrap style learner for the simple note refactor."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List, Mapping, Sequence

try:
    from sklearn.ensemble import RandomForestClassifier
    _SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency in local env
    RandomForestClassifier = Any  # type: ignore[assignment]
    _SKLEARN_AVAILABLE = False

FEATURE_NAMES: tuple[str, ...] = (
    "sentence_length_mean",
    "sentence_length_cv",
    "paragraph_length_mean",
    "paragraph_length_cv",
    "token_diversity",
    "repeated_opening_ratio",
    "duplicate_paragraph_ratio",
    "first_person_start_ratio",
    "same_ending_run_ratio",
    "topic_opening_ratio",
    "heading_density",
    "punctuation_mix_score",
)
_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{1,}")
_FIRST_PERSON_RE = re.compile(r"^(?:私たち|当社|弊社|私|わたし|僕|ぼく)")
_HEADING_RE = re.compile(r"^##\s+.+$", re.MULTILINE)
_ENDING_RE = re.compile(r"(です。|ます。|でした。|ました。|だ。|である。|した。|いる。|ない。)$")
_PUNCTUATION = "、。！？"


def default_calibration_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "human_corpus" / "simple_note_refactor_2026-03-22" / "learner_calibration_bootstrap.json"


def _clean_text(text: Any) -> str:
    return str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _split_paragraphs(text: Any) -> List[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", cleaned) if chunk.strip()]


def _split_sentences(text: Any) -> List[str]:
    merged = re.sub(r"\n+", " ", _clean_text(text))
    if not merged:
        return []
    return [part.strip() for part in re.split(r"(?<=[。！？!?])\s*", merged) if part.strip()]


def _tokens(text: Any) -> List[str]:
    return [token.lower() for token in _TOKEN_RE.findall(_clean_text(text))]


def _coefficient_of_variation(values: Sequence[float]) -> float:
    filtered = [float(value) for value in values if float(value) > 0]
    if len(filtered) < 2:
        return 0.0
    avg = mean(filtered)
    if avg <= 0:
        return 0.0
    return round(pstdev(filtered) / avg, 4)


def _sentence_ending_category(sentence: str) -> str:
    stripped = str(sentence or "").strip()
    if not stripped:
        return ""
    matched = _ENDING_RE.search(stripped)
    return matched.group(1) if matched else stripped[-2:]


def extract_style_features(text: str, *, topic_anchors: Sequence[str] | None = None) -> Dict[str, float]:
    paragraphs = _split_paragraphs(text)
    headings = _HEADING_RE.findall(text or "")
    body_paragraphs = [paragraph for paragraph in paragraphs if not paragraph.startswith("## ")] or paragraphs
    sentences = _split_sentences(text)
    sentence_lengths = [len(sentence) for sentence in sentences]
    paragraph_lengths = [len(paragraph) for paragraph in body_paragraphs]
    tokens = _tokens(text)
    token_diversity = round(len(set(tokens)) / max(1, len(tokens)), 4)
    normalized_paragraphs = [re.sub(r"\s+", "", paragraph) for paragraph in body_paragraphs]
    opening_keys = [re.sub(r"[、。！？!?「」『』（）()]", "", paragraph)[:10] for paragraph in normalized_paragraphs]
    repeated_openings = sum(max(0, opening_keys.count(key) - 1) for key in set(opening_keys) if key)
    duplicate_paragraphs = len(normalized_paragraphs) - len(set(normalized_paragraphs))
    first_person_starts = sum(1 for paragraph in body_paragraphs if _FIRST_PERSON_RE.match(paragraph))
    endings = [_sentence_ending_category(sentence) for sentence in sentences if _sentence_ending_category(sentence)]
    same_ending_runs = 0
    previous = ""
    consecutive = 0
    for ending in endings:
        if ending == previous:
            consecutive += 1
            if consecutive >= 2:
                same_ending_runs += 1
        else:
            consecutive = 0
        previous = ending
    anchor_hits = 0
    anchors = [anchor.lower() for anchor in (topic_anchors or []) if str(anchor or "").strip()]
    for paragraph in body_paragraphs:
        first_sentence = _split_sentences(paragraph[:120])
        opener = (first_sentence[0] if first_sentence else paragraph[:60]).lower()
        if anchors and any(anchor in opener for anchor in anchors):
            anchor_hits += 1
    punctuation_mix = len({ch for ch in _clean_text(text) if ch in _PUNCTUATION})
    return {
        "sentence_length_mean": round(mean(sentence_lengths), 4) if sentence_lengths else 0.0,
        "sentence_length_cv": _coefficient_of_variation(sentence_lengths),
        "paragraph_length_mean": round(mean(paragraph_lengths), 4) if paragraph_lengths else 0.0,
        "paragraph_length_cv": _coefficient_of_variation(paragraph_lengths),
        "token_diversity": token_diversity,
        "repeated_opening_ratio": round(repeated_openings / max(1, len(body_paragraphs)), 4),
        "duplicate_paragraph_ratio": round(max(0, duplicate_paragraphs) / max(1, len(body_paragraphs)), 4),
        "first_person_start_ratio": round(first_person_starts / max(1, len(body_paragraphs)), 4),
        "same_ending_run_ratio": round(same_ending_runs / max(1, len(sentences)), 4),
        "topic_opening_ratio": round(anchor_hits / max(1, len(body_paragraphs)), 4),
        "heading_density": round(len(headings) / max(1, len(body_paragraphs)), 4),
        "punctuation_mix_score": round(punctuation_mix / len(_PUNCTUATION), 4),
    }


def _normalize_training_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        features = {name: float((row.get("features") or {}).get(name, 0.0) or 0.0) for name in FEATURE_NAMES}
        label = str(row.get("label") or "").strip().lower()
        if label not in {"human_like", "ai_like"}:
            raise ValueError(f"Unsupported label at row {index}: {label!r}")
        normalized.append(
            {
                "row_id": str(row.get("row_id") or f"row_{index:03d}"),
                "label": label,
                "article_type": str(row.get("article_type") or ""),
                "source_kind": str(row.get("source_kind") or ""),
                "source_ref": str(row.get("source_ref") or ""),
                "features": features,
            }
        )
    if len(normalized) < 4:
        raise ValueError("Style learner requires at least four training rows.")
    if len({row["label"] for row in normalized}) < 2:
        raise ValueError("Style learner requires both human_like and ai_like rows.")
    return normalized


def _feature_vector(features: Mapping[str, float]) -> List[float]:
    return [float(features.get(name, 0.0) or 0.0) for name in FEATURE_NAMES]


@dataclass(frozen=True)
class LearnerPrediction:
    label: str
    human_probability: float
    ai_probability: float
    confidence: float
    calibration_version: str
    model_name: str
    feature_vector: Dict[str, float]
    feature_highlights: List[Dict[str, float]]


class StyleLearner:
    """Trainable RandomForest wrapper for AI-likeness scoring."""

    def __init__(
        self,
        *,
        classifier: RandomForestClassifier,
        calibration_version: str,
        training_rows: Sequence[Mapping[str, Any]],
    ) -> None:
        self._classifier = classifier
        self.calibration_version = calibration_version
        self.training_rows = list(training_rows)
        self.feature_names = FEATURE_NAMES
        self.model_name = "RandomForest"
        self.feature_importances = {
            name: round(float(importance), 6)
            for name, importance in zip(self.feature_names, getattr(classifier, "feature_importances_", []))
        }

    @classmethod
    def from_training_rows(
        cls,
        rows: Iterable[Mapping[str, Any]],
        *,
        calibration_version: str,
        random_state: int = 42,
    ) -> "StyleLearner":
        if not _SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn is unavailable")
        normalized_rows = _normalize_training_rows(rows)
        x_values = [_feature_vector(row["features"]) for row in normalized_rows]
        y_values = [1 if row["label"] == "human_like" else 0 for row in normalized_rows]
        classifier = RandomForestClassifier(
            n_estimators=96,
            max_depth=6,
            min_samples_leaf=1,
            random_state=random_state,
        )
        classifier.fit(x_values, y_values)
        return cls(classifier=classifier, calibration_version=calibration_version, training_rows=normalized_rows)

    @classmethod
    def from_calibration_file(cls, path: Path | None = None) -> "StyleLearner":
        calibration_path = path or default_calibration_path()
        payload = json.loads(calibration_path.read_text(encoding="utf-8"))
        return cls.from_training_rows(
            payload.get("training_rows") or [],
            calibration_version=str(payload.get("version") or calibration_path.name),
        )

    def predict_from_text(
        self,
        text: str,
        *,
        topic_anchors: Sequence[str] | None = None,
    ) -> LearnerPrediction:
        features = extract_style_features(text, topic_anchors=topic_anchors)
        probabilities = self._classifier.predict_proba([_feature_vector(features)])[0]
        ai_probability = round(float(probabilities[0]), 4)
        human_probability = round(float(probabilities[1]), 4)
        confidence = round(abs(human_probability - ai_probability), 4)
        label = "human_like" if human_probability >= ai_probability else "ai_like"
        top_features = sorted(
            (
                {
                    "name": name,
                    "importance": round(self.feature_importances.get(name, 0.0), 6),
                    "value": round(float(features.get(name, 0.0) or 0.0), 4),
                }
                for name in self.feature_names
            ),
            key=lambda item: item["importance"],
            reverse=True,
        )[:5]
        return LearnerPrediction(
            label=label,
            human_probability=human_probability,
            ai_probability=ai_probability,
            confidence=confidence,
            calibration_version=self.calibration_version,
            model_name=self.model_name,
            feature_vector=features,
            feature_highlights=top_features,
        )


def build_aiindex_ready_payload(prediction: LearnerPrediction) -> Dict[str, Any]:
    return {
        "learner_ready": True,
        "learner_model": prediction.model_name,
        "learner_calibration_version": prediction.calibration_version,
        "learner_label": prediction.label,
        "learner_human_probability": prediction.human_probability,
        "learner_ai_probability": prediction.ai_probability,
        "learner_confidence": prediction.confidence,
        "learner_feature_highlights": prediction.feature_highlights,
    }


def load_default_style_learner() -> StyleLearner:
    return StyleLearner.from_calibration_file(default_calibration_path())
