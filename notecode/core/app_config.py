"""app_config.py - Load application configuration from config.json."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMConfig:
    model_name: str
    fallback_model: str
    reasoning_effort: str
    timeout: float
    top_p: Optional[float]
    presence_penalty: float
    frequency_penalty: float
    disable_temperature_model_prefixes: tuple[str, ...]
    disable_top_p_model_prefixes: tuple[str, ...]
    disable_penalty_model_prefixes: tuple[str, ...]
    allow_model_fallback: bool
    max_same_model_retries: int
    retryable_error_classes: tuple[str, ...]
    task_models: Dict[str, str]
    article_type_params: Dict[str, Dict[str, Any]]


@dataclass(frozen=True)
class SecurityConfig:
    prompt_injection_mode: str
    blocked_input_fields: tuple[str, ...]
    extra_injection_patterns: tuple[str, ...]


@dataclass(frozen=True)
class ImageConfig:
    model_name: str
    fallback_model: str
    description_model_name: str
    description_fallback_model: str
    quality: str
    text_quality: str
    size: str
    count: int
    output_format: str
    background: str
    moderation: str
    note_width: int
    note_height: int
    no_text_in_image: bool
    text_overlay_font_path: str
    generated_images_dir: str


@dataclass(frozen=True)
class QualityPipelineConfig:
    enabled: bool
    mode: str
    rollout_percent: int
    fail_open: bool
    phase01_lexical_enabled: bool
    phase01_tokenizer: str
    phase02_burstiness_enabled: bool
    phase03_nominalization_enabled: bool
    phase04_style_drift_enabled: bool
    phase05_layout_guard_enabled: bool
    phase06_orchestrator_enabled: bool
    phase07_rollout_enabled: bool
    lexical_threshold: float
    burstiness_target_min: float
    burstiness_target_max: float
    nominalization_alert_threshold: float
    style_alignment_min_score: float
    domain_guard_strictness: str
    supplement_min_position_ratio: float
    intro_max_length_ratio: float
    section_coherence_min_score: float
    global_rewrite_ratio_cap: float
    conflict_resolution_policy: str
    quality_gate_min_score: float
    max_rewrite_ratio: float
    max_sentence_split_ratio: float
    max_nominalization_rewrite_ratio: float
    fingerprint_enabled: bool
    resonance_tuning_enabled: bool


DEFAULT_LLM_CONFIG: dict[str, Any] = {
    "model_name": "gpt-4.1-mini-2025-04-14",
    "fallback_model": "gpt-5-nano",
    "reasoning_effort": "low",
    "timeout": 30.0,
    "top_p": None,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "disable_temperature_model_prefixes": ["gpt-5", "o3", "o1"],
    "disable_top_p_model_prefixes": ["gpt-5"],
    "disable_penalty_model_prefixes": ["gpt-5", "o3", "o1"],
    "allow_model_fallback": False,
    "max_same_model_retries": 2,
    "retryable_error_classes": ["rate_limit", "timeout", "upstream_5xx", "network_reset"],
    "task_models": {},
    "article_type_params": {},
}

DEFAULT_SECURITY: dict[str, Any] = {
    "prompt_injection_mode": "block",
    "blocked_input_fields": ["prompt_raw", "topic", "speaker_profile", "audience_profile", "topic_statement", "core_message"],
    "extra_injection_patterns": [],
}

DEFAULT_IMAGE_CONFIG: dict[str, Any] = {
    "model_name": "gpt-image-2",
    "fallback_model": "gpt-image-1.5",
    "description_model_name": "gpt-4.1-mini-2025-04-14",
    "description_fallback_model": "gpt-4.1-mini-2025-04-14",
    "quality": "low",
    "text_quality": "medium",
    "size": "1280x672",
    "count": 2,
    "output_format": "jpeg",
    "background": "opaque",
    "moderation": "auto",
    "note_width": 1280,
    "note_height": 670,
    "no_text_in_image": True,
    "text_overlay_font_path": "",
    "generated_images_dir": "",
}


def _config_path() -> Path:
    override = str(os.getenv("TECHIE_CONFIG_PATH") or "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "config.json"


def _load_config_file() -> dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Failed to read config.json: %s", exc)
        return {}


def _coerce_float(value: Any, default: Optional[float]) -> Optional[float]:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _coerce_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _coerce_str(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _coerce_str_list(value: Any, default: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list):
        return tuple(default)
    cleaned = []
    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned.append(item.strip())
    if not cleaned:
        return tuple(default)
    return tuple(cleaned)


def _coerce_str_dict(value: Any, default: Dict[str, str]) -> Dict[str, str]:
    if not isinstance(value, dict):
        return dict(default)
    cleaned: Dict[str, str] = {}
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, str) and key.strip() and item.strip():
            cleaned[key.strip()] = item.strip()
    if not cleaned:
        return dict(default)
    return cleaned


def _coerce_nested_str_float_dict(value: Any, default: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(value, dict):
        return dict(default)
    cleaned: Dict[str, Dict[str, Any]] = {}
    allowed_keys = {
        "temperature",
        "verbosity",
        "presence_penalty",
        "frequency_penalty",
        "max_tokens",
        "reasoning_effort",
    }
    for outer_key, outer_value in value.items():
        if not isinstance(outer_key, str) or not outer_key.strip() or not isinstance(outer_value, dict):
            continue
        normalized_outer: Dict[str, Any] = {}
        for inner_key, inner_value in outer_value.items():
            if not isinstance(inner_key, str):
                continue
            key = inner_key.strip()
            if key not in allowed_keys:
                continue
            if key in {"verbosity", "reasoning_effort"}:
                if isinstance(inner_value, str) and inner_value.strip():
                    normalized_outer[key] = inner_value.strip()
                continue
            if key == "max_tokens":
                normalized_outer[key] = _coerce_int(inner_value, 0)
                continue
            normalized_outer[key] = _coerce_float(inner_value, None)
        cleaned[outer_key.strip()] = normalized_outer
    if not cleaned:
        return dict(default)
    return cleaned


def get_llm_config() -> LLMConfig:
    raw = _load_config_file().get("llm", {})
    merged = {**DEFAULT_LLM_CONFIG, **(raw if isinstance(raw, dict) else {})}
    return LLMConfig(
        model_name=_coerce_str(merged.get("model_name"), DEFAULT_LLM_CONFIG["model_name"]),
        fallback_model=_coerce_str(merged.get("fallback_model"), DEFAULT_LLM_CONFIG["fallback_model"]),
        reasoning_effort=_coerce_str(merged.get("reasoning_effort"), DEFAULT_LLM_CONFIG["reasoning_effort"]),
        timeout=_coerce_float(merged.get("timeout"), DEFAULT_LLM_CONFIG["timeout"]) or DEFAULT_LLM_CONFIG["timeout"],
        top_p=_coerce_float(merged.get("top_p"), DEFAULT_LLM_CONFIG["top_p"]),
        presence_penalty=_clamp_float(
            merged.get("presence_penalty"),
            DEFAULT_LLM_CONFIG["presence_penalty"],
            min_value=-2.0,
            max_value=2.0,
        ),
        frequency_penalty=_clamp_float(
            merged.get("frequency_penalty"),
            DEFAULT_LLM_CONFIG["frequency_penalty"],
            min_value=-2.0,
            max_value=2.0,
        ),
        disable_temperature_model_prefixes=_coerce_str_list(
            merged.get("disable_temperature_model_prefixes"),
            DEFAULT_LLM_CONFIG["disable_temperature_model_prefixes"],
        ),
        disable_top_p_model_prefixes=_coerce_str_list(
            merged.get("disable_top_p_model_prefixes"),
            DEFAULT_LLM_CONFIG["disable_top_p_model_prefixes"],
        ),
        disable_penalty_model_prefixes=_coerce_str_list(
            merged.get("disable_penalty_model_prefixes"),
            DEFAULT_LLM_CONFIG["disable_penalty_model_prefixes"],
        ),
        allow_model_fallback=bool(merged.get("allow_model_fallback", DEFAULT_LLM_CONFIG["allow_model_fallback"])),
        max_same_model_retries=max(
            0,
            min(
                5,
                _coerce_int(
                    merged.get("max_same_model_retries"),
                    DEFAULT_LLM_CONFIG["max_same_model_retries"],
                ),
            ),
        ),
        retryable_error_classes=_coerce_str_list(
            merged.get("retryable_error_classes"),
            DEFAULT_LLM_CONFIG["retryable_error_classes"],
        ),
        task_models=_coerce_str_dict(merged.get("task_models"), DEFAULT_LLM_CONFIG["task_models"]),
        article_type_params=_coerce_nested_str_float_dict(
            merged.get("article_type_params"),
            DEFAULT_LLM_CONFIG["article_type_params"],
        ),
    )


def get_security_config() -> SecurityConfig:
    raw = _load_config_file().get("security", {})
    merged = {**DEFAULT_SECURITY, **(raw if isinstance(raw, dict) else {})}
    mode = _coerce_str(merged.get("prompt_injection_mode"), DEFAULT_SECURITY["prompt_injection_mode"]).lower()
    if mode not in {"block", "shadow"}:
        mode = DEFAULT_SECURITY["prompt_injection_mode"]
    return SecurityConfig(
        prompt_injection_mode=mode,
        blocked_input_fields=_coerce_str_list(
            merged.get("blocked_input_fields"),
            DEFAULT_SECURITY["blocked_input_fields"],
        ),
        extra_injection_patterns=_coerce_str_list(
            merged.get("extra_injection_patterns"),
            DEFAULT_SECURITY["extra_injection_patterns"],
        ),
    )


DEFAULT_HUMAN_RESONANCE: dict[str, Any] = {
    "phrase_max_per_paragraph": 2,
    "phrase_probability": 0.75,
    "phrase_min_occurrences": 2,
    "pronoun_reduction_ratio": 0.5,
    "pronoun_reduction_min_count": 4,
    "use_llm_for_editor": True,
    "use_llm_for_legal": True,
    "phase_skip_thresholds": {
        "enabled": False,
        "min_samples": 5,
        "max_char_ratio": 0.02,
    },
}


DEFAULT_QUALITY_PIPELINE: dict[str, Any] = {
    "enabled": False,
    "mode": "off",
    "rollout_percent": 100,
    "fail_open": True,
    "phase01_lexical_enabled": False,
    "phase01_tokenizer": "auto",
    "phase02_burstiness_enabled": False,
    "phase03_nominalization_enabled": False,
    "phase04_style_drift_enabled": False,
    "phase05_layout_guard_enabled": False,
    "phase06_orchestrator_enabled": False,
    "phase07_rollout_enabled": False,
    "lexical_threshold": 0.32,
    "burstiness_target_min": 0.18,
    "burstiness_target_max": 0.52,
    "nominalization_alert_threshold": 0.18,
    "style_alignment_min_score": 0.72,
    "domain_guard_strictness": "normal",
    "supplement_min_position_ratio": 0.45,
    "intro_max_length_ratio": 0.35,
    "section_coherence_min_score": 0.40,
    "global_rewrite_ratio_cap": 0.2,
    "conflict_resolution_policy": "safe_first",
    "quality_gate_min_score": 0.55,
    "max_rewrite_ratio": 0.15,
    "max_sentence_split_ratio": 0.12,
    "max_nominalization_rewrite_ratio": 0.12,
    "fingerprint_enabled": True,
    "resonance_tuning_enabled": False,
}

DEFAULT_COGNITIVE_DRIFT: dict[str, Any] = {
    "enabled": True,
    "paragraph_enabled": True,
    "paragraph_min_blocks": 3,
    "paragraph_max_blocks": 4,
    "paragraph_temp_swing": 0.08,
    "paragraph_generation_mode": "paragraph",
    "fatigue_enabled": True,
    "fatigue_onset_ratio": 0.55,
    "fatigue_syntax_relaxation": 0.3,
    "fatigue_vocab_repetition_tolerance": 0.4,
    "fatigue_meta_linguistic_allowed": True,
}

DEFAULT_SOURCE_READING: dict[str, Any] = {
    "max_chars_per_source": 12000,
    "quality_context_source_text_max_chars": 12000,
    "style_drift_source_text_max_chars": 12000,
}


def _clamp_float(value: Any, default: float, min_value: float, max_value: float) -> float:
    coerced = _coerce_float(value, default)
    if coerced is None:
        coerced = default
    return max(min_value, min(max_value, float(coerced)))


def _clamp_int(value: Any, default: int, min_value: int, max_value: int) -> int:
    coerced = _coerce_int(value, default)
    return max(min_value, min(max_value, int(coerced)))


def _coerce_choice(value: Any, default: str, allowed: tuple[str, ...]) -> str:
    candidate = _coerce_str(value, default).lower()
    if candidate in allowed:
        return candidate
    return default


def get_quality_pipeline_config() -> QualityPipelineConfig:
    raw = _load_config_file().get("quality_pipeline", {})
    merged = {**DEFAULT_QUALITY_PIPELINE, **(raw if isinstance(raw, dict) else {})}
    burstiness_target_min = _clamp_float(
        merged.get("burstiness_target_min"),
        DEFAULT_QUALITY_PIPELINE["burstiness_target_min"],
        min_value=0.0,
        max_value=1.0,
    )
    burstiness_target_max = _clamp_float(
        merged.get("burstiness_target_max"),
        DEFAULT_QUALITY_PIPELINE["burstiness_target_max"],
        min_value=0.0,
        max_value=1.0,
    )
    if burstiness_target_max < burstiness_target_min:
        burstiness_target_min, burstiness_target_max = burstiness_target_max, burstiness_target_min

    return QualityPipelineConfig(
        enabled=_coerce_bool(merged.get("enabled"), DEFAULT_QUALITY_PIPELINE["enabled"]),
        mode=_coerce_choice(merged.get("mode"), DEFAULT_QUALITY_PIPELINE["mode"], ("off", "shadow", "enforce")),
        rollout_percent=_clamp_int(
            merged.get("rollout_percent"),
            DEFAULT_QUALITY_PIPELINE["rollout_percent"],
            min_value=0,
            max_value=100,
        ),
        fail_open=_coerce_bool(merged.get("fail_open"), DEFAULT_QUALITY_PIPELINE["fail_open"]),
        phase01_lexical_enabled=_coerce_bool(
            merged.get("phase01_lexical_enabled"),
            DEFAULT_QUALITY_PIPELINE["phase01_lexical_enabled"],
        ),
        phase01_tokenizer=_coerce_choice(
            merged.get("phase01_tokenizer"),
            DEFAULT_QUALITY_PIPELINE["phase01_tokenizer"],
            ("auto", "regex", "sudachi"),
        ),
        phase02_burstiness_enabled=_coerce_bool(
            merged.get("phase02_burstiness_enabled"),
            DEFAULT_QUALITY_PIPELINE["phase02_burstiness_enabled"],
        ),
        phase03_nominalization_enabled=_coerce_bool(
            merged.get("phase03_nominalization_enabled"),
            DEFAULT_QUALITY_PIPELINE["phase03_nominalization_enabled"],
        ),
        phase04_style_drift_enabled=_coerce_bool(
            merged.get("phase04_style_drift_enabled"),
            DEFAULT_QUALITY_PIPELINE["phase04_style_drift_enabled"],
        ),
        phase05_layout_guard_enabled=_coerce_bool(
            merged.get("phase05_layout_guard_enabled"),
            DEFAULT_QUALITY_PIPELINE["phase05_layout_guard_enabled"],
        ),
        phase06_orchestrator_enabled=_coerce_bool(
            merged.get("phase06_orchestrator_enabled"),
            DEFAULT_QUALITY_PIPELINE["phase06_orchestrator_enabled"],
        ),
        phase07_rollout_enabled=_coerce_bool(
            merged.get("phase07_rollout_enabled"),
            DEFAULT_QUALITY_PIPELINE["phase07_rollout_enabled"],
        ),
        lexical_threshold=_clamp_float(
            merged.get("lexical_threshold"),
            DEFAULT_QUALITY_PIPELINE["lexical_threshold"],
            min_value=0.0,
            max_value=1.0,
        ),
        burstiness_target_min=burstiness_target_min,
        burstiness_target_max=burstiness_target_max,
        nominalization_alert_threshold=_clamp_float(
            merged.get("nominalization_alert_threshold"),
            DEFAULT_QUALITY_PIPELINE["nominalization_alert_threshold"],
            min_value=0.0,
            max_value=1.0,
        ),
        style_alignment_min_score=_clamp_float(
            merged.get("style_alignment_min_score"),
            DEFAULT_QUALITY_PIPELINE["style_alignment_min_score"],
            min_value=0.0,
            max_value=1.0,
        ),
        domain_guard_strictness=_coerce_choice(
            merged.get("domain_guard_strictness"),
            DEFAULT_QUALITY_PIPELINE["domain_guard_strictness"],
            ("relaxed", "normal", "strict"),
        ),
        supplement_min_position_ratio=_clamp_float(
            merged.get("supplement_min_position_ratio"),
            DEFAULT_QUALITY_PIPELINE["supplement_min_position_ratio"],
            min_value=0.2,
            max_value=0.9,
        ),
        intro_max_length_ratio=_clamp_float(
            merged.get("intro_max_length_ratio"),
            DEFAULT_QUALITY_PIPELINE["intro_max_length_ratio"],
            min_value=0.1,
            max_value=0.8,
        ),
        section_coherence_min_score=_clamp_float(
            merged.get("section_coherence_min_score"),
            DEFAULT_QUALITY_PIPELINE["section_coherence_min_score"],
            min_value=0.0,
            max_value=1.0,
        ),
        global_rewrite_ratio_cap=_clamp_float(
            merged.get("global_rewrite_ratio_cap"),
            DEFAULT_QUALITY_PIPELINE["global_rewrite_ratio_cap"],
            min_value=0.0,
            max_value=1.0,
        ),
        conflict_resolution_policy=_coerce_choice(
            merged.get("conflict_resolution_policy"),
            DEFAULT_QUALITY_PIPELINE["conflict_resolution_policy"],
            ("safe_first", "readability_first", "diversity_first"),
        ),
        quality_gate_min_score=_clamp_float(
            merged.get("quality_gate_min_score"),
            DEFAULT_QUALITY_PIPELINE["quality_gate_min_score"],
            min_value=0.0,
            max_value=1.0,
        ),
        max_rewrite_ratio=_clamp_float(
            merged.get("max_rewrite_ratio"),
            DEFAULT_QUALITY_PIPELINE["max_rewrite_ratio"],
            min_value=0.0,
            max_value=1.0,
        ),
        max_sentence_split_ratio=_clamp_float(
            merged.get("max_sentence_split_ratio"),
            DEFAULT_QUALITY_PIPELINE["max_sentence_split_ratio"],
            min_value=0.0,
            max_value=1.0,
        ),
        max_nominalization_rewrite_ratio=_clamp_float(
            merged.get("max_nominalization_rewrite_ratio"),
            DEFAULT_QUALITY_PIPELINE["max_nominalization_rewrite_ratio"],
            min_value=0.0,
            max_value=1.0,
        ),
        fingerprint_enabled=_coerce_bool(
            merged.get("fingerprint_enabled"),
            DEFAULT_QUALITY_PIPELINE["fingerprint_enabled"],
        ),
        resonance_tuning_enabled=_coerce_bool(
            merged.get("resonance_tuning_enabled"),
            DEFAULT_QUALITY_PIPELINE["resonance_tuning_enabled"],
        ),
    )


def _parse_phase_skip_thresholds(raw: Any) -> dict[str, Any]:
    """phase_skip_thresholds をパースして正規化する。"""
    defaults = DEFAULT_HUMAN_RESONANCE["phase_skip_thresholds"]
    if not isinstance(raw, dict):
        return dict(defaults)
    return {
        "enabled": _coerce_bool(raw.get("enabled"), defaults["enabled"]),
        "min_samples": _coerce_int(raw.get("min_samples"), defaults["min_samples"]),
        "max_char_ratio": _coerce_float(raw.get("max_char_ratio"), defaults["max_char_ratio"]) or defaults["max_char_ratio"],
    }


def get_human_resonance_config() -> dict[str, Any]:
    """config.json の human_resonance（Phase5 言い回し揺らぎ等）を返す。"""
    raw = _load_config_file().get("human_resonance", {})
    merged = {**DEFAULT_HUMAN_RESONANCE, **(raw if isinstance(raw, dict) else {})}
    return {
        "phrase_max_per_paragraph": _coerce_int(merged.get("phrase_max_per_paragraph"), DEFAULT_HUMAN_RESONANCE["phrase_max_per_paragraph"]),
        "phrase_probability": _coerce_float(merged.get("phrase_probability"), DEFAULT_HUMAN_RESONANCE["phrase_probability"]) or DEFAULT_HUMAN_RESONANCE["phrase_probability"],
        "phrase_min_occurrences": _coerce_int(merged.get("phrase_min_occurrences"), DEFAULT_HUMAN_RESONANCE["phrase_min_occurrences"]),
        "pronoun_reduction_ratio": _coerce_float(merged.get("pronoun_reduction_ratio"), DEFAULT_HUMAN_RESONANCE["pronoun_reduction_ratio"]) or DEFAULT_HUMAN_RESONANCE["pronoun_reduction_ratio"],
        "pronoun_reduction_min_count": _coerce_int(merged.get("pronoun_reduction_min_count"), DEFAULT_HUMAN_RESONANCE["pronoun_reduction_min_count"]),
        "use_llm_for_editor": _coerce_bool(merged.get("use_llm_for_editor"), DEFAULT_HUMAN_RESONANCE["use_llm_for_editor"]),
        "use_llm_for_legal": _coerce_bool(merged.get("use_llm_for_legal"), DEFAULT_HUMAN_RESONANCE["use_llm_for_legal"]),
        "phase_skip_thresholds": _parse_phase_skip_thresholds(merged.get("phase_skip_thresholds")),
    }


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def get_cognitive_drift_config() -> dict[str, Any]:
    """config.json の cognitive_drift（セクション+段落の認知温度ドリフト）を返す。"""
    raw = _load_config_file().get("cognitive_drift", {})
    merged = {**DEFAULT_COGNITIVE_DRIFT, **(raw if isinstance(raw, dict) else {})}
    paragraph_min = _clamp_int(
        merged.get("paragraph_min_blocks"),
        DEFAULT_COGNITIVE_DRIFT["paragraph_min_blocks"],
        min_value=2,
        max_value=6,
    )
    paragraph_max_raw = _clamp_int(
        merged.get("paragraph_max_blocks"),
        DEFAULT_COGNITIVE_DRIFT["paragraph_max_blocks"],
        min_value=2,
        max_value=6,
    )
    paragraph_max = max(paragraph_min, paragraph_max_raw)
    return {
        "enabled": _coerce_bool(merged.get("enabled"), DEFAULT_COGNITIVE_DRIFT["enabled"]),
        "paragraph_enabled": _coerce_bool(
            merged.get("paragraph_enabled"),
            DEFAULT_COGNITIVE_DRIFT["paragraph_enabled"],
        ),
        "paragraph_min_blocks": paragraph_min,
        "paragraph_max_blocks": paragraph_max,
        "paragraph_temp_swing": _clamp_float(
            merged.get("paragraph_temp_swing"),
            DEFAULT_COGNITIVE_DRIFT["paragraph_temp_swing"],
            min_value=0.0,
            max_value=0.20,
        ),
        "fatigue_enabled": _coerce_bool(
            merged.get("fatigue_enabled"),
            DEFAULT_COGNITIVE_DRIFT["fatigue_enabled"],
        ),
        "fatigue_onset_ratio": _clamp_float(
            merged.get("fatigue_onset_ratio"),
            DEFAULT_COGNITIVE_DRIFT["fatigue_onset_ratio"],
            min_value=0.3,
            max_value=0.8,
        ),
        "fatigue_syntax_relaxation": _clamp_float(
            merged.get("fatigue_syntax_relaxation"),
            DEFAULT_COGNITIVE_DRIFT["fatigue_syntax_relaxation"],
            min_value=0.0,
            max_value=1.0,
        ),
        "fatigue_vocab_repetition_tolerance": _clamp_float(
            merged.get("fatigue_vocab_repetition_tolerance"),
            DEFAULT_COGNITIVE_DRIFT["fatigue_vocab_repetition_tolerance"],
            min_value=0.0,
            max_value=1.0,
        ),
        "fatigue_meta_linguistic_allowed": _coerce_bool(
            merged.get("fatigue_meta_linguistic_allowed"),
            DEFAULT_COGNITIVE_DRIFT["fatigue_meta_linguistic_allowed"],
        ),
        "paragraph_generation_mode": str(
            merged.get("paragraph_generation_mode",
                       DEFAULT_COGNITIVE_DRIFT["paragraph_generation_mode"])
        ),
    }


DEFAULT_STYLE_PROFILES: dict[str, dict[str, Any]] = {
    "column": {
        "bracket_limit": 3, "ambiguous_word_limit": 5,
        "emotional_waveform": "dynamic", "digression_allowed": True,
        "orthographic_variation_rate": 0.2,
    },
    "how_to": {
        "bracket_limit": 2, "ambiguous_word_limit": 3,
        "emotional_waveform": "steady", "digression_allowed": False,
        "orthographic_variation_rate": 0.1,
    },
    "opinion": {
        "bracket_limit": 4, "ambiguous_word_limit": 6,
        "emotional_waveform": "rising", "digression_allowed": True,
        "orthographic_variation_rate": 0.25,
    },
    "announcement": {
        "bracket_limit": 1, "ambiguous_word_limit": 1,
        "emotional_waveform": "flat", "digression_allowed": False,
        "orthographic_variation_rate": 0.0,
    },
    "hobby": {
        "bracket_limit": 5, "ambiguous_word_limit": 7,
        "emotional_waveform": "dynamic", "digression_allowed": True,
        "orthographic_variation_rate": 0.3,
    },
    "technical": {
        "bracket_limit": 2, "ambiguous_word_limit": 2,
        "emotional_waveform": "steady", "digression_allowed": False,
        "orthographic_variation_rate": 0.05,
    },
}

# R6-T08: content_type/genre -> profile mapping
_CONTENT_TYPE_MAP: dict[str, str] = {
    "コラム": "column", "column": "column",
    "ハウツー": "how_to", "how_to": "how_to", "howto": "how_to",
    "意見": "opinion", "opinion": "opinion", "オピニオン": "opinion",
    "お知らせ": "announcement", "announcement": "announcement", "ニュース": "announcement", "news": "announcement",
    "趣味": "hobby", "hobby": "hobby", "ライフスタイル": "hobby", "lifestyle": "hobby",
    "技術": "technical", "technical": "technical", "テクニカル": "technical", "tech": "technical",
}


def get_style_profiles() -> dict[str, dict[str, Any]]:
    """Load style profiles from config.json, merged with defaults."""
    raw = _load_config_file().get("style_profiles", {})
    if not isinstance(raw, dict):
        return dict(DEFAULT_STYLE_PROFILES)
    merged = dict(DEFAULT_STYLE_PROFILES)
    for key, profile in raw.items():
        if isinstance(profile, dict):
            base = merged.get(key, {})
            merged[key] = {**base, **profile}
    return merged


def map_content_type_to_profile(
    content_type: str = "",
    genre: str = "",
) -> dict[str, Any]:
    """Map content_type or genre string to a style profile (R6-T08).

    Falls back to 'column' if no match is found.
    """
    profiles = get_style_profiles()
    for candidate in (content_type, genre):
        candidate_lower = (candidate or "").strip().lower()
        mapped_key = _CONTENT_TYPE_MAP.get(candidate_lower)
        if mapped_key and mapped_key in profiles:
            return dict(profiles[mapped_key])
        # Direct key match
        if candidate_lower in profiles:
            return dict(profiles[candidate_lower])
    return dict(profiles.get("column", DEFAULT_STYLE_PROFILES["column"]))


DEFAULT_FINGERPRINT_THRESHOLD_PRESETS: dict[str, dict[str, float]] = {
    "superhuman": {
        "sentence_length_cv": 0.22,
        "paragraph_length_cv": 0.18,
        "conjunction_repetition_rate_high": 0.34,
        "subject_explicit_rate_high": 0.38,
        "particle_entropy_low": 2.1,
        "pos_bigram_monotonicity_low": 0.58,
        "mtld_low": 58.0,
        "nominalization_rate_high": 0.16,
    },
    "relaxed": {
        "sentence_length_cv": 0.07,
        "paragraph_length_cv": 0.07,
        "conjunction_repetition_rate_high": 0.60,
        "subject_explicit_rate_high": 0.65,
        "particle_entropy_low": 1.5,
        "pos_bigram_monotonicity_low": 0.30,
        "mtld_low": 30.0,
        "nominalization_rate_high": 0.30,
    },
    "standard": {
        "sentence_length_cv": 0.10,
        "paragraph_length_cv": 0.10,
        "conjunction_repetition_rate_high": 0.50,
        "subject_explicit_rate_high": 0.55,
        "particle_entropy_low": 1.8,
        "pos_bigram_monotonicity_low": 0.40,
        "mtld_low": 40.0,
        "nominalization_rate_high": 0.25,
    },
    "strict": {
        "sentence_length_cv": 0.15,
        "paragraph_length_cv": 0.15,
        "conjunction_repetition_rate_high": 0.40,
        "subject_explicit_rate_high": 0.45,
        "particle_entropy_low": 2.0,
        "pos_bigram_monotonicity_low": 0.50,
        "mtld_low": 50.0,
        "nominalization_rate_high": 0.20,
    },
}


def get_fingerprint_threshold_presets() -> dict[str, Any]:
    """Load fingerprint threshold presets from config.json (R7-T03).

    Returns dict with 'active_preset' key and per-preset threshold dicts.
    """
    raw = _load_config_file().get("fingerprint_threshold_presets", {})
    if not isinstance(raw, dict):
        return {"active_preset": "standard", **DEFAULT_FINGERPRINT_THRESHOLD_PRESETS}
    active = raw.get("active_preset", "standard")
    if active not in ("superhuman", "relaxed", "standard", "strict"):
        active = "standard"
    presets: dict[str, dict[str, float]] = {}
    for name in ("superhuman", "relaxed", "standard", "strict"):
        default_set = DEFAULT_FINGERPRINT_THRESHOLD_PRESETS[name]
        raw_set = raw.get(name, {})
        if not isinstance(raw_set, dict):
            raw_set = {}
        merged: dict[str, float] = {}
        for key, default_val in default_set.items():
            val = raw_set.get(key, default_val)
            try:
                merged[key] = float(val)
            except (TypeError, ValueError):
                merged[key] = default_val
        presets[name] = merged
    return {"active_preset": active, **presets}


def get_active_fingerprint_thresholds() -> dict[str, float]:
    """Return the currently active fingerprint threshold set (R7-T03)."""
    all_presets = get_fingerprint_threshold_presets()
    active = all_presets.get("active_preset", "standard")
    return dict(all_presets.get(active, all_presets.get("standard", DEFAULT_FINGERPRINT_THRESHOLD_PRESETS["standard"])))


DEFAULT_SEMANTIC_DEDUPE: dict[str, Any] = {
    "enabled": True,
    "rewrite_enabled": False,
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

DEFAULT_VNEXT_OVERLAP_RUNTIME: dict[str, float] = {
    "similarity_threshold": 0.62,
    "content_overlap_threshold": 0.77,
    "high_overlap_shortcut_threshold": 0.83,
}


def get_generation_mode() -> str:
    """Return the active generation mode.

    Allowed mode: 'zero_base_v2'.
    Unknown values are rejected and safely fall back to zero_base_v2.
    """
    raw = _load_config_file().get("generation_mode", "zero_base_v2")
    return _coerce_choice(raw, "zero_base_v2", ("zero_base_v2",))


def get_vnext_overlap_runtime_config() -> dict[str, float]:
    """Load vNext overlap runtime seed thresholds without affecting mainline dedupe."""
    raw = _load_config_file().get("vnext_overlap_runtime", {})
    merged = {**DEFAULT_VNEXT_OVERLAP_RUNTIME, **(raw if isinstance(raw, dict) else {})}
    content_overlap_threshold = _clamp_float(
        merged.get("content_overlap_threshold"),
        DEFAULT_VNEXT_OVERLAP_RUNTIME["content_overlap_threshold"],
        min_value=0.10,
        max_value=0.95,
    )
    high_overlap_shortcut_threshold = _clamp_float(
        merged.get("high_overlap_shortcut_threshold"),
        DEFAULT_VNEXT_OVERLAP_RUNTIME["high_overlap_shortcut_threshold"],
        min_value=0.20,
        max_value=0.99,
    )
    if high_overlap_shortcut_threshold < content_overlap_threshold:
        high_overlap_shortcut_threshold = content_overlap_threshold
    return {
        "similarity_threshold": _clamp_float(
            merged.get("similarity_threshold"),
            DEFAULT_VNEXT_OVERLAP_RUNTIME["similarity_threshold"],
            min_value=0.50,
            max_value=0.99,
        ),
        "content_overlap_threshold": content_overlap_threshold,
        "high_overlap_shortcut_threshold": high_overlap_shortcut_threshold,
    }


def get_semantic_dedupe_config() -> dict[str, Any]:
    """Load semantic dedupe configuration for zero_base_v2."""
    raw = _load_config_file().get("semantic_dedupe", {})
    merged = {**DEFAULT_SEMANTIC_DEDUPE, **(raw if isinstance(raw, dict) else {})}
    similarity_threshold = _clamp_float(
        merged.get("similarity_threshold"),
        DEFAULT_SEMANTIC_DEDUPE["similarity_threshold"],
        min_value=0.50,
        max_value=0.99,
    )
    relaxed_similarity_threshold = _clamp_float(
        merged.get("relaxed_similarity_threshold"),
        DEFAULT_SEMANTIC_DEDUPE["relaxed_similarity_threshold"],
        min_value=0.40,
        max_value=0.99,
    )
    if relaxed_similarity_threshold > similarity_threshold:
        relaxed_similarity_threshold = similarity_threshold
    return {
        "enabled": _coerce_bool(merged.get("enabled"), DEFAULT_SEMANTIC_DEDUPE["enabled"]),
        "rewrite_enabled": _coerce_bool(
            merged.get("rewrite_enabled"),
            DEFAULT_SEMANTIC_DEDUPE["rewrite_enabled"],
        ),
        "provider_mode": _coerce_choice(
            merged.get("provider_mode"),
            DEFAULT_SEMANTIC_DEDUPE["provider_mode"],
            ("hybrid", "local_only"),
        ),
        "model": _coerce_str(merged.get("model"), DEFAULT_SEMANTIC_DEDUPE["model"]),
        "similarity_threshold": similarity_threshold,
        "content_overlap_threshold": _clamp_float(
            merged.get("content_overlap_threshold"),
            DEFAULT_SEMANTIC_DEDUPE["content_overlap_threshold"],
            min_value=0.10,
            max_value=0.95,
        ),
        "high_overlap_shortcut_threshold": _clamp_float(
            merged.get("high_overlap_shortcut_threshold"),
            DEFAULT_SEMANTIC_DEDUPE["high_overlap_shortcut_threshold"],
            min_value=0.20,
            max_value=0.99,
        ),
        "relaxed_similarity_threshold": relaxed_similarity_threshold,
        "min_shared_content_words": _clamp_int(
            merged.get("min_shared_content_words"),
            DEFAULT_SEMANTIC_DEDUPE["min_shared_content_words"],
            min_value=1,
            max_value=8,
        ),
        "timeout_seconds": _clamp_float(
            merged.get("timeout_seconds"),
            DEFAULT_SEMANTIC_DEDUPE["timeout_seconds"],
            min_value=1.0,
            max_value=60.0,
        ),
        "max_retries": _clamp_int(
            merged.get("max_retries"),
            DEFAULT_SEMANTIC_DEDUPE["max_retries"],
            min_value=0,
            max_value=2,
        ),
        "retry_backoff_seconds": _clamp_float(
            merged.get("retry_backoff_seconds"),
            DEFAULT_SEMANTIC_DEDUPE["retry_backoff_seconds"],
            min_value=0.1,
            max_value=3.0,
        ),
        "network_fail_cooldown_seconds": _clamp_float(
            merged.get("network_fail_cooldown_seconds"),
            DEFAULT_SEMANTIC_DEDUPE["network_fail_cooldown_seconds"],
            min_value=0.0,
            max_value=900.0,
        ),
        "max_sentences": _clamp_int(
            merged.get("max_sentences"),
            DEFAULT_SEMANTIC_DEDUPE["max_sentences"],
            min_value=8,
            max_value=240,
        ),
        "max_chars_per_sentence": _clamp_int(
            merged.get("max_chars_per_sentence"),
            DEFAULT_SEMANTIC_DEDUPE["max_chars_per_sentence"],
            min_value=80,
            max_value=600,
        ),
    }


def get_section_generation_config() -> dict[str, Any]:
    """config.json の section_generation 設定を返す。"""
    raw = _load_config_file().get("section_generation", {})
    defaults = {
        "parallel_sections": False,
        "novelty_gate": {
            "enabled": False,
            "max_retries": 3,
            "intro_novelty_min": 0.20,
            "middle_novelty_min": 0.30,
            "closing_novelty_min": 0.35,
            "focus_relaxation": 0.03,
            "min_candidate_terms": 10,
            "max_forbidden_terms": 10,
        },
        "context_overlap": {
            "enabled": False,
            "base_ratio": 0.40,
            "intro_ratio": 0.45,
            "middle_ratio": 0.35,
            "closing_ratio": 0.28,
            "min_ratio": 0.10,
            "max_ratio": 0.55,
            "reduce_on_redundancy": 0.08,
        },
        "hard_soft_thresholds": {
            "enabled": False,
            "mode": "shadow",
            "hard_max_rewrite_ratio": 0.20,
            "hard_max_grammar_breaks_per_1k": 3.0,
            "hard_preserve_headings": True,
            "soft_min_unpredictability": 0.45,
            "soft_max_flat_zone_count": 6,
            "soft_max_semantic_issue_count": 2,
            "soft_max_ai_template_ending_count": 3,
        },
        "lexical_policy": {
            "enabled": True,
            "extra_banned_phrases": [],
        },
    }
    merged = {**defaults, **(raw if isinstance(raw, dict) else {})}

    novelty_defaults = defaults["novelty_gate"]
    novelty_raw = merged.get("novelty_gate")
    novelty = {**novelty_defaults, **(novelty_raw if isinstance(novelty_raw, dict) else {})}

    overlap_defaults = defaults["context_overlap"]
    overlap_raw = merged.get("context_overlap")
    overlap = {**overlap_defaults, **(overlap_raw if isinstance(overlap_raw, dict) else {})}

    hard_soft_defaults = defaults["hard_soft_thresholds"]
    hard_soft_raw = merged.get("hard_soft_thresholds")
    hard_soft = {
        **hard_soft_defaults,
        **(hard_soft_raw if isinstance(hard_soft_raw, dict) else {}),
    }

    lexical_defaults = defaults["lexical_policy"]
    lexical_raw = merged.get("lexical_policy")
    lexical = {**lexical_defaults, **(lexical_raw if isinstance(lexical_raw, dict) else {})}

    extra_banned = lexical.get("extra_banned_phrases", lexical_defaults["extra_banned_phrases"])
    if not isinstance(extra_banned, list):
        extra_banned = []
    cleaned_extra_banned = [item.strip() for item in extra_banned if isinstance(item, str) and item.strip()]

    min_ratio = _clamp_float(
        overlap.get("min_ratio"),
        overlap_defaults["min_ratio"],
        min_value=0.0,
        max_value=0.9,
    )
    max_ratio_raw = _clamp_float(
        overlap.get("max_ratio"),
        overlap_defaults["max_ratio"],
        min_value=0.0,
        max_value=0.9,
    )
    max_ratio = max(min_ratio, max_ratio_raw)

    soft_max_flat_zone_count = _clamp_int(
        hard_soft.get("soft_max_flat_zone_count"),
        hard_soft_defaults["soft_max_flat_zone_count"],
        min_value=1,
        max_value=32,
    )
    soft_max_semantic_issue_count = _clamp_int(
        hard_soft.get("soft_max_semantic_issue_count"),
        hard_soft_defaults["soft_max_semantic_issue_count"],
        min_value=0,
        max_value=24,
    )
    soft_max_ai_template_ending_count = _clamp_int(
        hard_soft.get("soft_max_ai_template_ending_count"),
        hard_soft_defaults["soft_max_ai_template_ending_count"],
        min_value=1,
        max_value=40,
    )

    return {
        "parallel_sections": _coerce_bool(merged.get("parallel_sections"), False),
        "novelty_gate": {
            "enabled": _coerce_bool(novelty.get("enabled"), novelty_defaults["enabled"]),
            "max_retries": _clamp_int(
                novelty.get("max_retries"),
                novelty_defaults["max_retries"],
                min_value=1,
                max_value=3,
            ),
            "intro_novelty_min": _clamp_float(
                novelty.get("intro_novelty_min"),
                novelty_defaults["intro_novelty_min"],
                min_value=0.0,
                max_value=1.0,
            ),
            "middle_novelty_min": _clamp_float(
                novelty.get("middle_novelty_min"),
                novelty_defaults["middle_novelty_min"],
                min_value=0.0,
                max_value=1.0,
            ),
            "closing_novelty_min": _clamp_float(
                novelty.get("closing_novelty_min"),
                novelty_defaults["closing_novelty_min"],
                min_value=0.0,
                max_value=1.0,
            ),
            "focus_relaxation": _clamp_float(
                novelty.get("focus_relaxation"),
                novelty_defaults["focus_relaxation"],
                min_value=0.0,
                max_value=0.20,
            ),
            "min_candidate_terms": _clamp_int(
                novelty.get("min_candidate_terms"),
                novelty_defaults["min_candidate_terms"],
                min_value=4,
                max_value=40,
            ),
            "max_forbidden_terms": _clamp_int(
                novelty.get("max_forbidden_terms"),
                novelty_defaults["max_forbidden_terms"],
                min_value=1,
                max_value=24,
            ),
        },
        "context_overlap": {
            "enabled": _coerce_bool(overlap.get("enabled"), overlap_defaults["enabled"]),
            "base_ratio": _clamp_float(
                overlap.get("base_ratio"),
                overlap_defaults["base_ratio"],
                min_value=0.0,
                max_value=0.9,
            ),
            "intro_ratio": _clamp_float(
                overlap.get("intro_ratio"),
                overlap_defaults["intro_ratio"],
                min_value=0.0,
                max_value=0.9,
            ),
            "middle_ratio": _clamp_float(
                overlap.get("middle_ratio"),
                overlap_defaults["middle_ratio"],
                min_value=0.0,
                max_value=0.9,
            ),
            "closing_ratio": _clamp_float(
                overlap.get("closing_ratio"),
                overlap_defaults["closing_ratio"],
                min_value=0.0,
                max_value=0.9,
            ),
            "min_ratio": min_ratio,
            "max_ratio": max_ratio,
            "reduce_on_redundancy": _clamp_float(
                overlap.get("reduce_on_redundancy"),
                overlap_defaults["reduce_on_redundancy"],
                min_value=0.0,
                max_value=0.40,
            ),
        },
        "hard_soft_thresholds": {
            "enabled": _coerce_bool(hard_soft.get("enabled"), hard_soft_defaults["enabled"]),
            "mode": _coerce_choice(
                hard_soft.get("mode"),
                hard_soft_defaults["mode"],
                ("off", "shadow", "enforce"),
            ),
            "hard_max_rewrite_ratio": _clamp_float(
                hard_soft.get("hard_max_rewrite_ratio"),
                hard_soft_defaults["hard_max_rewrite_ratio"],
                min_value=0.0,
                max_value=1.0,
            ),
            "hard_max_grammar_breaks_per_1k": _clamp_float(
                hard_soft.get("hard_max_grammar_breaks_per_1k"),
                hard_soft_defaults["hard_max_grammar_breaks_per_1k"],
                min_value=0.0,
                max_value=30.0,
            ),
            "hard_preserve_headings": _coerce_bool(
                hard_soft.get("hard_preserve_headings"),
                hard_soft_defaults["hard_preserve_headings"],
            ),
            "soft_min_unpredictability": _clamp_float(
                hard_soft.get("soft_min_unpredictability"),
                hard_soft_defaults["soft_min_unpredictability"],
                min_value=0.0,
                max_value=1.0,
            ),
            "soft_max_flat_zone_count": soft_max_flat_zone_count,
            "soft_max_semantic_issue_count": soft_max_semantic_issue_count,
            "soft_max_ai_template_ending_count": soft_max_ai_template_ending_count,
        },
        "lexical_policy": {
            "enabled": _coerce_bool(lexical.get("enabled"), lexical_defaults["enabled"]),
            "extra_banned_phrases": cleaned_extra_banned,
        },
    }


def get_postprocess_config() -> dict[str, Any]:
    """config.json の postprocess（repair-only等）を返す。"""
    raw = _load_config_file().get("postprocess", {})
    defaults = {
        "repair_only": {
            "enabled": False,
            "mode": "shadow",
            "rewrite_ratio_cap": 0.08,
            "llm_trigger_severity": "high",
            "min_chars_for_llm": 260,
            "max_violations_per_1k": 2.0,
        },
        "concise_compaction": {
            "enabled": True,
            "dedupe_similarity_ratio": 0.86,
            "dedupe_jaccard_ratio": 0.62,
            "summary_overlap_ratio": 0.58,
            "max_sentence_chars": 90,
            "max_connective_openings_per_paragraph": 2,
            "max_splits_per_sentence": 2,
            "target_reduction_ratio": 0.22,
            "aggressive_keep_ratio": 0.60,
            "aggressive_min_sentences_per_paragraph": 3,
            "aggressive_min_chars": 1600,
            "paragraph_clog_min_chars": 165,
            "paragraph_clog_min_sentences": 4,
            "paragraph_clog_min_commas": 5,
            "paragraph_clog_min_comma_density": 0.017,
            "paragraph_clog_threshold_jitter": 0.12,
        },
    }
    merged = {**defaults, **(raw if isinstance(raw, dict) else {})}
    repair_defaults = defaults["repair_only"]
    repair_raw = merged.get("repair_only")
    repair = {**repair_defaults, **(repair_raw if isinstance(repair_raw, dict) else {})}
    concise_defaults = defaults["concise_compaction"]
    concise_raw = merged.get("concise_compaction")
    concise = {**concise_defaults, **(concise_raw if isinstance(concise_raw, dict) else {})}
    return {
        "repair_only": {
            "enabled": _coerce_bool(repair.get("enabled"), repair_defaults["enabled"]),
            "mode": _coerce_choice(
                repair.get("mode"),
                repair_defaults["mode"],
                ("off", "shadow", "enforce"),
            ),
            "rewrite_ratio_cap": _clamp_float(
                repair.get("rewrite_ratio_cap"),
                repair_defaults["rewrite_ratio_cap"],
                min_value=0.0,
                max_value=1.0,
            ),
            "llm_trigger_severity": _coerce_choice(
                repair.get("llm_trigger_severity"),
                repair_defaults["llm_trigger_severity"],
                ("off", "high", "mid"),
            ),
            "min_chars_for_llm": _clamp_int(
                repair.get("min_chars_for_llm"),
                repair_defaults["min_chars_for_llm"],
                min_value=80,
                max_value=5000,
            ),
            "max_violations_per_1k": _clamp_float(
                repair.get("max_violations_per_1k"),
                repair_defaults["max_violations_per_1k"],
                min_value=0.0,
                max_value=30.0,
            ),
        },
        "concise_compaction": {
            "enabled": _coerce_bool(concise.get("enabled"), concise_defaults["enabled"]),
            "dedupe_similarity_ratio": _clamp_float(
                concise.get("dedupe_similarity_ratio"),
                concise_defaults["dedupe_similarity_ratio"],
                min_value=0.55,
                max_value=0.98,
            ),
            "dedupe_jaccard_ratio": _clamp_float(
                concise.get("dedupe_jaccard_ratio"),
                concise_defaults["dedupe_jaccard_ratio"],
                min_value=0.35,
                max_value=0.95,
            ),
            "summary_overlap_ratio": _clamp_float(
                concise.get("summary_overlap_ratio"),
                concise_defaults["summary_overlap_ratio"],
                min_value=0.35,
                max_value=0.95,
            ),
            "max_sentence_chars": _clamp_int(
                concise.get("max_sentence_chars"),
                concise_defaults["max_sentence_chars"],
                min_value=60,
                max_value=140,
            ),
            "max_connective_openings_per_paragraph": _clamp_int(
                concise.get("max_connective_openings_per_paragraph"),
                concise_defaults["max_connective_openings_per_paragraph"],
                min_value=0,
                max_value=3,
            ),
            "max_splits_per_sentence": _clamp_int(
                concise.get("max_splits_per_sentence"),
                concise_defaults["max_splits_per_sentence"],
                min_value=1,
                max_value=3,
            ),
            "target_reduction_ratio": _clamp_float(
                concise.get("target_reduction_ratio"),
                concise_defaults["target_reduction_ratio"],
                min_value=0.0,
                max_value=0.40,
            ),
            "aggressive_keep_ratio": _clamp_float(
                concise.get("aggressive_keep_ratio"),
                concise_defaults["aggressive_keep_ratio"],
                min_value=0.45,
                max_value=0.90,
            ),
            "aggressive_min_sentences_per_paragraph": _clamp_int(
                concise.get("aggressive_min_sentences_per_paragraph"),
                concise_defaults["aggressive_min_sentences_per_paragraph"],
                min_value=3,
                max_value=6,
            ),
            "aggressive_min_chars": _clamp_int(
                concise.get("aggressive_min_chars"),
                concise_defaults["aggressive_min_chars"],
                min_value=600,
                max_value=12000,
            ),
            "paragraph_clog_min_chars": _clamp_int(
                concise.get("paragraph_clog_min_chars"),
                concise_defaults["paragraph_clog_min_chars"],
                min_value=120,
                max_value=320,
            ),
            "paragraph_clog_min_sentences": _clamp_int(
                concise.get("paragraph_clog_min_sentences"),
                concise_defaults["paragraph_clog_min_sentences"],
                min_value=2,
                max_value=8,
            ),
            "paragraph_clog_min_commas": _clamp_int(
                concise.get("paragraph_clog_min_commas"),
                concise_defaults["paragraph_clog_min_commas"],
                min_value=0,
                max_value=16,
            ),
            "paragraph_clog_min_comma_density": _clamp_float(
                concise.get("paragraph_clog_min_comma_density"),
                concise_defaults["paragraph_clog_min_comma_density"],
                min_value=0.0,
                max_value=0.08,
            ),
            "paragraph_clog_threshold_jitter": _clamp_float(
                concise.get("paragraph_clog_threshold_jitter"),
                concise_defaults["paragraph_clog_threshold_jitter"],
                min_value=0.0,
                max_value=0.35,
            ),
        },
    }


def get_source_reading_config() -> dict[str, Any]:
    """config.json の source_reading（ソース読み取り上限）設定を返す。"""
    raw = _load_config_file().get("source_reading", {})
    merged = {**DEFAULT_SOURCE_READING, **(raw if isinstance(raw, dict) else {})}

    max_chars_per_source = _clamp_int(
        merged.get("max_chars_per_source"),
        DEFAULT_SOURCE_READING["max_chars_per_source"],
        min_value=2000,
        max_value=20000,
    )
    quality_context_source_text_max_chars = _clamp_int(
        merged.get("quality_context_source_text_max_chars"),
        DEFAULT_SOURCE_READING["quality_context_source_text_max_chars"],
        min_value=2000,
        max_value=20000,
    )
    style_drift_source_text_max_chars = _clamp_int(
        merged.get("style_drift_source_text_max_chars"),
        DEFAULT_SOURCE_READING["style_drift_source_text_max_chars"],
        min_value=2000,
        max_value=20000,
    )

    return {
        "max_chars_per_source": max_chars_per_source,
        "quality_context_source_text_max_chars": quality_context_source_text_max_chars,
        "style_drift_source_text_max_chars": style_drift_source_text_max_chars,
    }


def get_experience_pattern_config() -> dict[str, Any]:
    """config.json の experience_pattern（経験談パターン制御）を返す。"""
    raw = _load_config_file().get("experience_pattern", {})
    defaults = {
        "enabled": True,
        "auto_detect": True,
        "rules": {},
        "fallback_policy": "conservative",
    }
    merged = {**defaults, **(raw if isinstance(raw, dict) else {})}
    return {
        "enabled": _coerce_bool(merged.get("enabled"), defaults["enabled"]),
        "auto_detect": _coerce_bool(merged.get("auto_detect"), defaults["auto_detect"]),
        "rules": merged.get("rules", defaults["rules"]),
        "fallback_policy": _coerce_str(merged.get("fallback_policy"), defaults["fallback_policy"]),
    }


def get_image_config() -> ImageConfig:
    raw = _load_config_file().get("images", {})
    merged = {**DEFAULT_IMAGE_CONFIG, **(raw if isinstance(raw, dict) else {})}
    return ImageConfig(
        model_name=_coerce_str(merged.get("model_name"), DEFAULT_IMAGE_CONFIG["model_name"]),
        fallback_model=_coerce_str(merged.get("fallback_model"), DEFAULT_IMAGE_CONFIG["fallback_model"]),
        description_model_name=_coerce_str(
            merged.get("description_model_name"),
            DEFAULT_IMAGE_CONFIG["description_model_name"],
        ),
        description_fallback_model=_coerce_str(
            merged.get("description_fallback_model"),
            DEFAULT_IMAGE_CONFIG["description_fallback_model"],
        ),
        quality=_coerce_str(merged.get("quality"), DEFAULT_IMAGE_CONFIG["quality"]),
        text_quality=_coerce_str(merged.get("text_quality"), DEFAULT_IMAGE_CONFIG["text_quality"]),
        size=_coerce_str(merged.get("size"), DEFAULT_IMAGE_CONFIG["size"]),
        count=_coerce_int(merged.get("count"), DEFAULT_IMAGE_CONFIG["count"]),
        output_format=_coerce_str(merged.get("output_format"), DEFAULT_IMAGE_CONFIG["output_format"]),
        background=_coerce_str(merged.get("background"), DEFAULT_IMAGE_CONFIG["background"]),
        moderation=_coerce_str(merged.get("moderation"), DEFAULT_IMAGE_CONFIG["moderation"]),
        note_width=_coerce_int(merged.get("note_width"), DEFAULT_IMAGE_CONFIG["note_width"]),
        note_height=_coerce_int(merged.get("note_height"), DEFAULT_IMAGE_CONFIG["note_height"]),
        no_text_in_image=_coerce_bool(merged.get("no_text_in_image"), DEFAULT_IMAGE_CONFIG["no_text_in_image"]),
        text_overlay_font_path=_coerce_str(merged.get("text_overlay_font_path"), DEFAULT_IMAGE_CONFIG["text_overlay_font_path"]),
        generated_images_dir=_coerce_str(merged.get("generated_images_dir"), DEFAULT_IMAGE_CONFIG["generated_images_dir"]),
    )
