"""llm_client.py - OpenAI Responses API wrapper."""
from __future__ import annotations

import base64
import inspect
import logging
import mimetypes
import os
import random
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, List

from openai import OpenAI

from core.app_config import get_llm_config
from core.token_tracker import TokenTracker
from note.image_config import (
    DEFAULT_IMAGE_COUNT,
    DEFAULT_IMAGE_BACKGROUND,
    DEFAULT_IMAGE_DESCRIPTION_MODEL,
    DEFAULT_IMAGE_MODERATION,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_IMAGE_OUTPUT_FORMAT,
    DEFAULT_IMAGE_QUALITY,
    DEFAULT_IMAGE_SIZE,
    FALLBACK_IMAGE_DESCRIPTION_MODEL,
    GENERATED_IMAGES_DIR,
    NO_TEXT_IN_IMAGE,
    NOTE_IMAGE_SIZE,
)
from note.prompt_sanitizer import sanitize_untrusted_text, to_prompt_json_string

LLM_CONFIG = get_llm_config()
MODEL_NAME = LLM_CONFIG.model_name
FALLBACK_MODEL = LLM_CONFIG.fallback_model
REASONING_EFFORT = LLM_CONFIG.reasoning_effort
DEFAULT_TIMEOUT = LLM_CONFIG.timeout
DEFAULT_TOP_P = LLM_CONFIG.top_p
DEFAULT_PRESENCE_PENALTY = LLM_CONFIG.presence_penalty
DEFAULT_FREQUENCY_PENALTY = LLM_CONFIG.frequency_penalty
DISABLE_TEMPERATURE_MODEL_PREFIXES = LLM_CONFIG.disable_temperature_model_prefixes
DISABLE_TOP_P_MODEL_PREFIXES = LLM_CONFIG.disable_top_p_model_prefixes
DISABLE_PENALTY_MODEL_PREFIXES = LLM_CONFIG.disable_penalty_model_prefixes
ALLOW_MODEL_FALLBACK = LLM_CONFIG.allow_model_fallback
MAX_SAME_MODEL_RETRIES = LLM_CONFIG.max_same_model_retries
RETRYABLE_ERROR_CLASSES = LLM_CONFIG.retryable_error_classes
TASK_MODELS = LLM_CONFIG.task_models
ARTICLE_TYPE_PARAMS = LLM_CONFIG.article_type_params

logger = logging.getLogger(__name__)
LONG_FORM_TASKS = {"section", "lead", "verification", "legal_check", "editor_review", "outline"}
MAX_RATE_LIMIT_WAIT_SECONDS = 30.0
LONG_FORM_RETRY_MAX_TOKENS = 8192


class LLMRuntimeError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        reason_code: str,
        call_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.call_metadata = dict(call_metadata or {})


class LLMClient:
    def __init__(
        self,
        model: str = MODEL_NAME,
        reasoning_effort: str = REASONING_EFFORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.task_models = dict(TASK_MODELS)
        self._last_call_metadata: Dict[str, Any] = self._default_call_metadata(primary_model=model)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables.")
            raise ValueError(
                "CRITICAL: OPENAI_API_KEY is missing. "
                "Please create a .env file and set OPENAI_API_KEY."
            )
            
        self.client = OpenAI(timeout=timeout)
        self.token_tracker = TokenTracker()

    def get_last_call_metadata(self) -> Dict[str, Any]:
        return dict(self._last_call_metadata)

    def _default_call_metadata(self, *, primary_model: str = "") -> Dict[str, Any]:
        resolved_model = str(primary_model or self.model or "")
        return {
            "primary_model": resolved_model,
            "selected_model": resolved_model,
            "base_model": str(self.model or ""),
            "model_source": "base_model",
            "task_type": "",
            "article_type": "",
            "requested_reasoning_effort": "",
            "requested_temperature": None,
            "requested_top_p": None,
            "requested_presence_penalty": None,
            "requested_frequency_penalty": None,
            "requested_verbosity": "",
            "effective_reasoning_effort": "",
            "effective_temperature": None,
            "effective_top_p": None,
            "effective_presence_penalty": None,
            "effective_frequency_penalty": None,
            "effective_verbosity": "",
            "compatibility_suppressed_params": [],
            "same_model_retry_count": 0,
            "retry_events": [],
            "last_retry_event": "",
            "model_fallback_attempted": False,
            "model_fallback_blocked": not ALLOW_MODEL_FALLBACK,
            "prompt_truncation_attempted": False,
            "prompt_truncation_blocked": False,
            "last_error_class": "",
            "last_reason_code": "OK",
            "execution_mode": "llm",
        }

    def _resolve_selected_model(self, task_type: str) -> tuple[str, str]:
        key = str(task_type or "").strip()
        if key and key in self.task_models:
            return str(self.task_models.get(key) or self.model), f"task_models.{key}"
        return str(self.model or ""), "base_model"

    @staticmethod
    def _append_compatibility_suppressed_param(metadata: Dict[str, Any], param_name: str) -> None:
        current = metadata.get("compatibility_suppressed_params", [])
        if not isinstance(current, list):
            current = []
        if param_name not in current:
            current.append(param_name)
        metadata["compatibility_suppressed_params"] = current

    @staticmethod
    def _append_retry_event(metadata: Dict[str, Any], event_name: str) -> None:
        text = str(event_name or "").strip()
        if not text:
            return
        current = metadata.get("retry_events", [])
        if not isinstance(current, list):
            current = []
        current.append(text)
        metadata["retry_events"] = current
        metadata["last_retry_event"] = text

    @staticmethod
    def _sync_effective_param_metadata(metadata: Dict[str, Any], params: Dict[str, Any]) -> None:
        metadata["selected_model"] = str(params.get("model") or metadata.get("selected_model") or "")
        metadata["primary_model"] = str(metadata.get("primary_model") or metadata["selected_model"])
        metadata["effective_reasoning_effort"] = str(params.get("reasoning_effort") or "")
        metadata["effective_temperature"] = params.get("temperature")
        metadata["effective_top_p"] = params.get("top_p")
        metadata["effective_presence_penalty"] = params.get("presence_penalty")
        metadata["effective_frequency_penalty"] = params.get("frequency_penalty")
        metadata["effective_verbosity"] = str(params.get("verbosity") or "")

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1200,
        task_type: str = "article",
        temperature_override: Optional[float] = None,
        verbosity: Optional[str] = None,
        article_type: Optional[str] = None,
        runtime_policy: Optional[Dict[str, Any]] = None,
    ) -> str:
        selected_model, model_source = self._resolve_selected_model(task_type)
        profile = self._resolve_article_type_profile(article_type)
        resolved_runtime_policy = self._resolve_runtime_policy(runtime_policy, selected_model)
        resolved_max_tokens = int(profile.get("max_tokens") or max_tokens)
        requested_temperature = (
            temperature_override
            if temperature_override is not None
            else profile.get("temperature", random.uniform(0.8, 1.1))
        )
        requested_top_p = self._parse_top_p(DEFAULT_TOP_P)
        compatibility_suppressed_params: list[str] = []
        top_p = requested_top_p if self._supports_top_p(selected_model) else None
        if requested_top_p is not None and top_p is None:
            compatibility_suppressed_params.append("top_p")
        use_temperature = requested_temperature if self._supports_temperature(selected_model) else None
        if requested_temperature is not None and use_temperature is None:
            compatibility_suppressed_params.append("temperature")
        if top_p is not None:
            # Prefer top_p over temperature (OpenAI guidance).
            use_temperature = None
        requested_verbosity = str(verbosity or profile.get("verbosity") or "")
        resolved_verbosity = requested_verbosity
        requested_presence_penalty = self._resolve_penalty_value(
            profile.get("presence_penalty"),
            DEFAULT_PRESENCE_PENALTY,
        )
        requested_frequency_penalty = self._resolve_penalty_value(
            profile.get("frequency_penalty"),
            DEFAULT_FREQUENCY_PENALTY,
        )
        if self._supports_penalties(selected_model):
            presence_penalty = requested_presence_penalty
            frequency_penalty = requested_frequency_penalty
        else:
            presence_penalty = None
            frequency_penalty = None
            if requested_presence_penalty is not None:
                compatibility_suppressed_params.append("presence_penalty")
            if requested_frequency_penalty is not None:
                compatibility_suppressed_params.append("frequency_penalty")
        requested_reasoning = str(profile.get("reasoning_effort") or self.reasoning_effort or "")
        resolved_reasoning = requested_reasoning
        if self._supports_reasoning(selected_model):
            resolved_reasoning = str(self._resolve_reasoning_effort(selected_model, requested_reasoning) or "")
        else:
            resolved_reasoning = ""
            if requested_reasoning:
                compatibility_suppressed_params.append("reasoning_effort")

        params = self._build_params(
            model=selected_model,
            prompt=prompt,
            max_tokens=resolved_max_tokens,
            reasoning_effort=resolved_reasoning,
            temperature=use_temperature,
            top_p=top_p,
            verbosity=resolved_verbosity,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
        )
        call_context = self._default_call_metadata(primary_model=selected_model)
        call_context.update(
            {
                "primary_model": selected_model,
                "selected_model": selected_model,
                "base_model": str(self.model or ""),
                "model_source": model_source,
                "task_type": str(task_type or ""),
                "article_type": str(article_type or ""),
                "requested_reasoning_effort": requested_reasoning,
                "requested_temperature": requested_temperature,
                "requested_top_p": requested_top_p,
                "requested_presence_penalty": requested_presence_penalty,
                "requested_frequency_penalty": requested_frequency_penalty,
                "requested_verbosity": requested_verbosity,
                "compatibility_suppressed_params": list(dict.fromkeys(compatibility_suppressed_params)),
            }
        )
        self._sync_effective_param_metadata(call_context, params)
        return self._call_with_fallback(
            params,
            task_type=task_type,
            runtime_policy=resolved_runtime_policy,
            call_context=call_context,
        )

    def _resolve_article_type_profile(self, article_type: Optional[str]) -> dict:
        key = str(article_type or "").strip()
        if not key:
            return {}
        value = ARTICLE_TYPE_PARAMS.get(key, {})
        return dict(value) if isinstance(value, dict) else {}

    def _resolve_runtime_policy(
        self,
        runtime_policy: Optional[Dict[str, Any]],
        primary_model: str,
    ) -> Dict[str, Any]:
        policy = dict(runtime_policy or {})
        allowed_retry_classes = policy.get("retryable_error_classes", RETRYABLE_ERROR_CLASSES)
        if isinstance(allowed_retry_classes, (list, tuple)):
            retryable_error_classes = tuple(str(item).strip() for item in allowed_retry_classes if str(item).strip())
        else:
            retryable_error_classes = RETRYABLE_ERROR_CLASSES
        return {
            "primary_model": primary_model,
            "allow_model_fallback": bool(policy.get("allow_model_fallback", ALLOW_MODEL_FALLBACK)),
            "max_same_model_retries": max(
                0,
                int(policy.get("max_same_model_retries", MAX_SAME_MODEL_RETRIES) or 0),
            ),
            "retryable_error_classes": retryable_error_classes or RETRYABLE_ERROR_CLASSES,
        }

    def _resolve_penalty_value(self, value: Optional[float], default: float) -> Optional[float]:
        resolved = value if value is not None else default
        if resolved is None:
            return None
        try:
            numeric = float(resolved)
        except (TypeError, ValueError):
            return None
        return max(-2.0, min(2.0, numeric))

    def _supports_temperature(self, model: str) -> bool:
        return not self._matches_prefixes(model, DISABLE_TEMPERATURE_MODEL_PREFIXES)

    def _supports_top_p(self, model: str) -> bool:
        return not self._matches_prefixes(model, DISABLE_TOP_P_MODEL_PREFIXES)

    def _supports_penalties(self, model: str) -> bool:
        return not self._matches_prefixes(model, DISABLE_PENALTY_MODEL_PREFIXES)

    def _matches_prefixes(self, model: str, prefixes: tuple[str, ...]) -> bool:
        name = (model or "").lower()
        if not name:
            return False
        for prefix in prefixes:
            if name.startswith((prefix or "").lower()):
                return True
        return False

    def _parse_top_p(self, value: Optional[float | str]) -> Optional[float]:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            parsed = float(value)
        except ValueError:
            return None
        if parsed <= 0 or parsed > 1:
            return None
        return parsed

    def _build_params(
        self,
        model: str,
        prompt: str,
        max_tokens: int,
        reasoning_effort: Optional[str],
        temperature: Optional[float],
        top_p: Optional[float],
        verbosity: Optional[str],
        presence_penalty: Optional[float],
        frequency_penalty: Optional[float],
    ) -> dict:
        params = {
            "model": model,
            "prompt": prompt,  # Store original prompt for truncation retry
            "max_tokens": max_tokens,
        }
        resolved_reasoning = self._resolve_reasoning_effort(model, reasoning_effort)
        if resolved_reasoning and self._supports_reasoning(model):
            params["reasoning_effort"] = resolved_reasoning
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if verbosity:
            params["verbosity"] = verbosity
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        return params

    def _resolve_reasoning_effort(self, model: str, reasoning_effort: Optional[str]) -> Optional[str]:
        effort = (reasoning_effort or "").strip().lower()
        if not effort:
            return None
        name = (model or "").lower()
        # The exact "gpt-5" alias does not accept reasoning_effort=none.
        if effort == "none" and name == "gpt-5":
            return "low"
        return effort

    def _supports_reasoning(self, model: str) -> bool:
        name = (model or "").lower()
        if name.startswith("gpt-5") or name.startswith("o1") or name.startswith("o3"):
            return True
        return False

    def _classify_retryable_error(self, exc: Exception) -> tuple[str, str]:
        text = str(exc).lower()
        error_class_name = type(exc).__name__.lower()
        if self._is_rate_limit_error(exc):
            return "rate_limit", "TRN_PRIMARY_MODEL_RATE_LIMIT"
        if "timeout" in text or "timed out" in text:
            return "timeout", "TRN_PRIMARY_MODEL_TIMEOUT"
        if (
            "apiconnectionerror" in error_class_name
            or "connection error" in text
            or "connection reset" in text
            or "network reset" in text
            or "connection aborted" in text
            or "broken pipe" in text
        ):
            return "network_reset", "TRN_PRIMARY_MODEL_NETWORK_RESET"
        if (
            "upstream" in text
            or "server error" in text
            or "internal server error" in text
            or "bad gateway" in text
            or "service unavailable" in text
            or "gateway timeout" in text
            or " 500" in text
            or " 502" in text
            or " 503" in text
            or " 504" in text
        ):
            return "upstream_5xx", "TRN_PRIMARY_MODEL_UPSTREAM_5XX"
        return "", ""

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        if (
            "rate_limit" in text
            or "rate limit" in text
            or "too many requests" in text
            or " 429" in text
            or text.startswith("429")
        ):
            return True
        if getattr(exc, "status_code", None) == 429:
            return True
        response = getattr(exc, "response", None)
        if getattr(response, "status_code", None) == 429:
            return True
        return False

    def _parse_wait_seconds(self, value) -> Optional[float]:
        if value is None:
            return None
        raw = str(value).strip().lower()
        if not raw:
            return None
        try:
            if raw.endswith("ms"):
                return float(raw[:-2]) / 1000.0
            if raw.endswith("s"):
                return float(raw[:-1])
            return float(raw)
        except ValueError:
            match = re.search(r"(\d+(?:\.\d+)?)", raw)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
        return None

    def _retry_after_seconds(self, exc: Exception) -> Optional[float]:
        header_candidates = (
            "retry-after",
            "x-ratelimit-reset-requests",
            "x-ratelimit-reset-tokens",
        )
        containers = [getattr(exc, "headers", None), getattr(getattr(exc, "response", None), "headers", None)]
        for headers in containers:
            if not headers:
                continue
            if hasattr(headers, "items"):
                lowered = {str(k).lower(): v for k, v in headers.items()}
            else:
                continue
            for key in header_candidates:
                wait = self._parse_wait_seconds(lowered.get(key))
                if wait is not None and wait > 0:
                    return wait
        return None

    def _log_retry(self, message: str, exc: Exception) -> None:
        logger.warning(message)
        logger.debug("Retry detail: %s", exc, exc_info=True)

    def _call_with_fallback(
        self,
        params: dict,
        task_type: str,
        runtime_policy: Dict[str, Any],
        call_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        max_attempts = max(1, int(runtime_policy.get("max_same_model_retries", 0)) + 1)
        primary_model = str(runtime_policy.get("primary_model") or params.get("model") or self.model)
        allow_model_fallback = bool(runtime_policy.get("allow_model_fallback", False))
        retryable_error_classes = set(runtime_policy.get("retryable_error_classes", RETRYABLE_ERROR_CLASSES))
        metadata: Dict[str, Any] = self._default_call_metadata(primary_model=primary_model)
        metadata.update(dict(call_context or {}))
        metadata["primary_model"] = primary_model
        metadata["model_fallback_blocked"] = not allow_model_fallback
        self._sync_effective_param_metadata(metadata, params)
        self._last_call_metadata = dict(metadata)
        for attempt in range(max_attempts):
            try:
                self._sync_effective_param_metadata(metadata, params)
                prompt = params.get("prompt", "")
                messages = [{"role": "user", "content": prompt}]
                request_params = {
                    "model": params.get("model", ""),
                    "messages": messages,
                    "max_completion_tokens": params.get("max_tokens", 1200),
                    "temperature": params.get("temperature"),
                    "top_p": params.get("top_p"),
                    "reasoning_effort": params.get("reasoning_effort"),
                    "verbosity": params.get("verbosity"),
                    "presence_penalty": params.get("presence_penalty"),
                    "frequency_penalty": params.get("frequency_penalty"),
                }
                # SDKが reasoning_effort / verbosity をシグネチャに持たない場合でも、
                # extra_body 経由でAPIへ透過送信して実効化する。
                direct_supported = self._filter_supported_params(
                    self.client.chat.completions.create,
                    request_params,
                )
                extra_body = {}
                reasoning_effort = params.get("reasoning_effort")
                if (
                    reasoning_effort is not None
                    and "reasoning_effort" not in direct_supported
                ):
                    extra_body["reasoning_effort"] = reasoning_effort
                verbosity = params.get("verbosity")
                if verbosity is not None and "verbosity" not in direct_supported:
                    extra_body["verbosity"] = verbosity
                presence_penalty = params.get("presence_penalty")
                if presence_penalty is not None and "presence_penalty" not in direct_supported:
                    extra_body["presence_penalty"] = presence_penalty
                frequency_penalty = params.get("frequency_penalty")
                if frequency_penalty is not None and "frequency_penalty" not in direct_supported:
                    extra_body["frequency_penalty"] = frequency_penalty

                request_params = {
                    k: v for k, v in direct_supported.items() if v is not None
                }
                if extra_body:
                    request_params["extra_body"] = extra_body
                response = self.client.chat.completions.create(**request_params)
                choices = getattr(response, "choices", None) or []
                finish_reason = getattr(choices[0], "finish_reason", None) if choices else None
                if finish_reason == "length" and task_type in LONG_FORM_TASKS:
                    current_max = int(params.get("max_tokens", 1200))
                    new_max = min(int(current_max * 1.5), LONG_FORM_RETRY_MAX_TOKENS)
                    if new_max > current_max and attempt < max_attempts - 1:
                        params["max_tokens"] = new_max
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "finish_reason_length")
                        logger.warning(
                            "Response truncated (finish_reason=length). Retrying with max_tokens=%s",
                            new_max,
                        )
                        continue
                    if new_max > current_max and attempt >= max_attempts - 1:
                        logger.warning(
                            "Response truncated (finish_reason=length) and retry budget exhausted. "
                            "Accepting current partial response (current=%s next=%s task_type=%s).",
                            current_max,
                            new_max,
                            task_type,
                        )
                    else:
                        logger.warning(
                            "Response truncated (finish_reason=length) but max_tokens cannot increase further "
                            "(current=%s cap=%s task_type=%s).",
                            current_max,
                            LONG_FORM_RETRY_MAX_TOKENS,
                            task_type,
                        )
                text = self._extract_text(response, task_type=task_type)
                self._record_usage(response, params.get("model", ""), task_type)
                metadata["last_error_class"] = ""
                metadata["last_reason_code"] = "OK"
                self._sync_effective_param_metadata(metadata, params)
                self._last_call_metadata = dict(metadata)
                return text
            except Exception as exc:
                error_text = str(exc).lower()
                retryable_class, retryable_reason_code = self._classify_retryable_error(exc)
                metadata["last_error_class"] = retryable_class
                metadata["last_reason_code"] = retryable_reason_code or "SYS_PRIMARY_MODEL_RETRY_EXHAUSTED"

                if self._is_rate_limit_error(exc):
                    wait_hint = self._retry_after_seconds(exc)
                    wait_time = wait_hint if wait_hint is not None else (2 ** attempt) + random.uniform(0, 1)
                    wait_time = min(max(wait_time, 0.1), MAX_RATE_LIMIT_WAIT_SECONDS)
                    if retryable_class in retryable_error_classes and attempt < max_attempts - 1:
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "retryable_rate_limit")
                        logger.warning("Rate limited. Retrying in %.1fs", wait_time)
                        time.sleep(wait_time)
                        continue
                
                # Handle context length exceeded by truncating input
                if "context_length" in error_text or "maximum context" in error_text or "too many tokens" in error_text:
                    current_prompt = params.get("prompt", "")
                    allow_prompt_truncation = bool(runtime_policy.get("allow_prompt_truncation", True))
                    if allow_prompt_truncation and len(current_prompt) > 2000 and attempt < max_attempts - 1:
                        # Truncate prompt to ~70% of current length
                        truncated = current_prompt[:int(len(current_prompt) * 0.7)]
                        params["prompt"] = truncated + "\n\n[入力が長いため一部省略]\n"
                        metadata["prompt_truncation_attempted"] = True
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "context_length_prompt_truncation")
                        logger.warning("Truncating prompt due to context length: %d -> %d chars", 
                                       len(current_prompt), len(truncated))
                        continue
                    if not allow_prompt_truncation:
                        metadata["prompt_truncation_blocked"] = True

                if attempt < max_attempts - 1:
                    if "temperature" in error_text:
                        params.pop("temperature", None)
                        self._append_compatibility_suppressed_param(metadata, "temperature")
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "compatibility_temperature")
                        self._log_retry("Retrying without temperature parameter", exc)
                        continue
                    if "top_p" in error_text:
                        params.pop("top_p", None)
                        self._append_compatibility_suppressed_param(metadata, "top_p")
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "compatibility_top_p")
                        self._log_retry("Retrying without top_p parameter", exc)
                        continue
                    if "verbosity" in error_text and ("parameter" in error_text or "keyword" in error_text):
                        params.pop("verbosity", None)
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "compatibility_verbosity")
                        self._log_retry("Retrying without verbosity parameter", exc)
                        continue
                    if "presence_penalty" in error_text:
                        params.pop("presence_penalty", None)
                        self._append_compatibility_suppressed_param(metadata, "presence_penalty")
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "compatibility_presence_penalty")
                        self._log_retry("Retrying without presence_penalty parameter", exc)
                        continue
                    if "frequency_penalty" in error_text:
                        params.pop("frequency_penalty", None)
                        self._append_compatibility_suppressed_param(metadata, "frequency_penalty")
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "compatibility_frequency_penalty")
                        self._log_retry("Retrying without frequency_penalty parameter", exc)
                        continue
                    if (
                        ("reasoning_effort" in error_text and ("parameter" in error_text or "keyword" in error_text))
                        or ("reasoning" in error_text and "parameter" in error_text)
                    ):
                        params.pop("reasoning_effort", None)
                        self._append_compatibility_suppressed_param(metadata, "reasoning_effort")
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, "compatibility_reasoning_effort")
                        self._log_retry("Retrying without reasoning parameters", exc)
                        continue
                    if retryable_class in retryable_error_classes:
                        metadata["same_model_retry_count"] += 1
                        self._append_retry_event(metadata, f"retryable_{retryable_class}")
                        self._log_retry(f"Retrying on primary model after {retryable_class}", exc)
                        continue
                self._last_call_metadata = dict(metadata)
                raise LLMRuntimeError(
                    str(exc),
                    reason_code=retryable_reason_code or "SYS_PRIMARY_MODEL_RETRY_EXHAUSTED",
                    call_metadata=metadata,
                ) from exc
        self._last_call_metadata = dict(metadata)
        raise LLMRuntimeError(
            "Primary model retry budget exhausted",
            reason_code="SYS_PRIMARY_MODEL_RETRY_EXHAUSTED",
            call_metadata=metadata,
        )

    def _extract_text(self, response, *, task_type: str = "") -> str:
        if hasattr(response, "choices") and response.choices:
            message = getattr(response.choices[0], "message", None)
            content = getattr(message, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                chunks: List[str] = []
                for block in content:
                    if isinstance(block, dict):
                        value = block.get("text") or block.get("content")
                    else:
                        value = getattr(block, "text", None) or getattr(block, "content", None)
                    if isinstance(value, str) and value:
                        chunks.append(value)
                if chunks:
                    return "\n".join(chunks)
        logger.warning("LLM response empty for task_type=%s", task_type or "unknown")
        return ""

    def _record_usage(self, response, model: str, task_type: str) -> None:
        usage = getattr(response, "usage", None)
        if not usage:
            return
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        try:
            self.token_tracker.add_usage(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                task_type=task_type,
            )
        except (AttributeError, TypeError, ValueError) as exc:
            logger.debug("Failed to record token usage", exc_info=exc)

    def _get_usage_value(self, obj, key: str):
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    def _extract_image_usage(self, response) -> Optional[dict]:
        usage = self._get_usage_value(response, "usage")
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
        if usage is None:
            return None

        input_tokens = self._get_usage_value(usage, "input_tokens") or 0
        output_tokens = self._get_usage_value(usage, "output_tokens") or 0
        total_tokens = self._get_usage_value(usage, "total_tokens") or (input_tokens + output_tokens)

        input_details = self._get_usage_value(usage, "input_tokens_details")
        output_details = self._get_usage_value(usage, "output_tokens_details")

        input_text_tokens = self._get_usage_value(input_details, "text_tokens") or 0
        input_image_tokens = self._get_usage_value(input_details, "image_tokens") or 0
        if input_details is None and input_tokens:
            input_text_tokens = input_tokens

        output_text_tokens = self._get_usage_value(output_details, "text_tokens") or 0
        output_image_tokens = self._get_usage_value(output_details, "image_tokens") or 0
        if output_details is None and output_tokens:
            output_image_tokens = output_tokens

        return {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_tokens": int(total_tokens),
            "input_text_tokens": int(input_text_tokens),
            "input_image_tokens": int(input_image_tokens),
            "output_text_tokens": int(output_text_tokens),
            "output_image_tokens": int(output_image_tokens),
        }

    def _estimate_image_output_tokens(self, size: str, quality: str, n: int) -> Optional[int]:
        if not size or not quality:
            return None
        quality_key = quality.lower()
        size_key = size.lower()
        token_table = {
            "low": {
                "1024x1024": 272,
                "1024x1536": 408,
                "1536x1024": 400,
            },
            "medium": {
                "1024x1024": 1056,
                "1024x1536": 1584,
                "1536x1024": 1568,
            },
            "high": {
                "1024x1024": 4160,
                "1024x1536": 6240,
                "1536x1024": 6208,
            },
        }
        per_image = token_table.get(quality_key, {}).get(size_key)
        if per_image is None:
            return None
        return int(per_image) * max(int(n or 1), 1)

    def _record_image_usage(self, response, model: str, size: str, quality: str, n: int) -> None:
        usage = self._extract_image_usage(response)
        if usage is None:
            if self._is_gpt_image2_model(model):
                return
            output_image_tokens = self._estimate_image_output_tokens(size, quality, n)
            if output_image_tokens is None:
                return
            usage = {
                "input_text_tokens": 0,
                "input_image_tokens": 0,
                "output_text_tokens": 0,
                "output_image_tokens": output_image_tokens,
            }
        else:
            if usage.get("output_image_tokens", 0) == 0 and usage.get("output_tokens", 0):
                usage["output_image_tokens"] = int(usage.get("output_tokens", 0))
            if usage.get("input_text_tokens", 0) == 0 and usage.get("input_tokens", 0):
                usage["input_text_tokens"] = int(usage.get("input_tokens", 0))

        try:
            self.token_tracker.add_image_usage(
                model=model,
                task_type="image_generation",
                input_text_tokens=int(usage.get("input_text_tokens", 0)),
                input_image_tokens=int(usage.get("input_image_tokens", 0)),
                output_text_tokens=int(usage.get("output_text_tokens", 0)),
                output_image_tokens=int(usage.get("output_image_tokens", 0)),
            )
        except (AttributeError, TypeError, ValueError) as exc:
            logger.debug("Failed to record image token usage", exc_info=exc)

    def _image_path_to_data_url(self, image_path: str) -> str:
        path = Path(image_path)
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        data = path.read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def _extract_responses_text(self, response) -> str:
        text = getattr(response, "output_text", None)
        if text:
            return text.strip()
        outputs = getattr(response, "output", None) or []
        for output in outputs:
            content = getattr(output, "content", None) or []
            for block in content:
                if getattr(block, "type", "") == "output_text":
                    value = getattr(block, "text", None)
                    if value:
                        return value.strip()
        return ""

    def _filter_supported_params(self, func, params: dict) -> dict:
        try:
            sig = inspect.signature(func)
        except (TypeError, ValueError):
            return params
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            return params
        return {k: v for k, v in params.items() if k in sig.parameters}

    def describe_image(self, image_path: str, prompt: Optional[str] = None) -> str:
        text_prompt = prompt or "画像の内容を日本語で簡潔に説明してください。"
        data_url = self._image_path_to_data_url(image_path)
        request_input = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": text_prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ]
        primary_model = str(DEFAULT_IMAGE_DESCRIPTION_MODEL or self.model or "").strip() or str(self.model or "").strip()
        fallback_model = (
            str(FALLBACK_IMAGE_DESCRIPTION_MODEL or "").strip()
            or str(self.model or "").strip()
        )
        try:
            response = self.client.responses.create(
                model=primary_model,
                input=request_input,
            )
        except Exception as exc:
            if fallback_model and fallback_model != primary_model:
                self._log_retry(
                    "Image description failed. Retrying with fallback image description model.",
                    exc,
                )
                response = self.client.responses.create(
                    model=fallback_model,
                    input=request_input,
                )
            else:
                raise
        return self._extract_responses_text(response)

    def _resize_for_note(self, image_path: Path) -> Path:
        try:
            from PIL import Image
        except ImportError:
            return image_path

        target_w, target_h = NOTE_IMAGE_SIZE
        img = Image.open(image_path)
        img = img.convert("RGB")
        w, h = img.size
        target_ratio = target_w / target_h
        current_ratio = w / h if h else 1.0
        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = max(0, (w - new_w) // 2)
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / target_ratio) if target_ratio else h
            top = max(0, (h - new_h) // 2)
            img = img.crop((0, top, w, top + new_h))
        img = img.resize((target_w, target_h), Image.LANCZOS)
        out_path = image_path.with_name(f"{image_path.stem}_note.jpg")
        img.save(out_path, format="JPEG", quality=85, optimize=True)
        return out_path

    def _build_image_variation_prompt(
        self,
        prompt: str,
        index: int,
        pattern_key: str = "simple",
    ) -> str:
        pattern_map = {
            "simple": {
                "label": "Clear Context Style",
                "composition": [
                    "centered main subject with model-adaptive supporting context and at least 15% breathing room",
                    "rule of thirds with one focal point plus article-specific contextual objects as needed",
                    "simple symmetrical layout with useful article-specific context",
                    "clean editorial layout with at least 15% uncluttered space",
                    "subject on left third with supporting context on the right",
                    "subject on lower third with contextual background details",
                ],
                "lighting": [
                    "soft diffused light with no harsh shadows",
                    "gentle even lighting",
                    "warm soft glow",
                    "flat ambient light for clarity",
                    "subtle side light with low contrast",
                ],
                "palette": [
                    "muted pastel palette",
                    "monochromatic with one accent color",
                    "soft earth tones",
                    "calm blue-gray palette with warm accent",
                    "neutral beige-gray palette with one deep accent",
                ],
                "detail": [
                    "coherent supporting objects chosen to clarify the article, no clutter",
                    "main element plus contextual details tied to the article",
                    "simple scene with enough concrete cues to explain the topic",
                    "one clear subject with readable surroundings",
                ],
                "style_family": [
                    "paper-cut collage illustration with layered simple shapes",
                    "editorial flat illustration with geometric forms",
                    "soft watercolor-like illustration with gentle edges",
                    "minimal photorealistic scene",
                ],
                "text_safe": [
                    "keep at least 15% clean breathing room near a readable headline area",
                    "keep a calm open band for readable headline placement without making the image sparse",
                    "maintain clear spacing around the headline area while preserving context",
                    "leave one readable margin and use the remaining area for article-specific details",
                ],
                "closing": "Let GPT Image 2 choose the supporting detail level; keep it clear, readable, and article-specific.",
            },
            "balanced": {
                "label": "Balanced Context Style",
                "composition": [
                    "one main subject with model-adaptive supporting elements and at least 15% breathing room",
                    "editorial composition with a focal subject and a small contextual cluster",
                    "subject in foreground with one secondary layer behind it",
                    "clean asymmetrical layout with moderate article-specific context",
                ],
                "lighting": [
                    "soft studio lighting with gentle depth",
                    "natural daylight with mild contrast",
                    "warm editorial lighting with clear separation",
                    "soft cinematic lighting without harsh shadows",
                ],
                "palette": [
                    "muted palette with coordinated colors",
                    "earth-tone palette with one restrained accent color",
                    "brand-neutral contemporary palette with subtle contrast",
                    "calm urban palette with warm highlight",
                ],
                "detail": [
                    "coherent supporting elements chosen by GPT Image 2 to explain the article, no clutter",
                    "main subject plus a few supporting objects tied to the topic",
                    "moderate contextual detail while keeping the scene tidy",
                    "readable visual story with controlled density",
                ],
                "style_family": [
                    "modern editorial illustration with soft texture",
                    "clean photorealistic workspace scene",
                    "stylized realistic illustration with contemporary layout",
                    "soft 3D editorial scene with simple forms",
                ],
                "text_safe": [
                    "leave at least 15% open space on one side for readable headline placement",
                    "keep a clean upper area for readable headline placement while retaining context",
                    "maintain readable open space around the focal subject",
                    "reserve one calm side area without making the image too empty",
                ],
                "closing": "Let GPT Image 2 choose enough context for the article while preserving readability.",
            },
            "rich": {
                "label": "Rich Context Style",
                "composition": [
                    "layered composition with foreground, middle ground, and background context",
                    "main subject supported by a wider contextual scene with depth",
                    "editorial wide shot that shows the surrounding situation clearly",
                    "scene with multiple related elements arranged in a readable flow",
                ],
                "lighting": [
                    "cinematic soft light with clear depth cues",
                    "natural realistic lighting with layered highlights",
                    "warm ambient light with subtle shadows for depth",
                    "polished editorial lighting with rich but controlled contrast",
                ],
                "palette": [
                    "coordinated colors with nuanced contrast",
                    "rich earth and neutral palette with one deep accent",
                    "contemporary magazine-style palette with layered tones",
                    "balanced warm-cool palette that adds depth without noise",
                ],
                "detail": [
                    "layered coherent context chosen by GPT Image 2, still readable",
                    "show surrounding tools, environment, and cues tied to the topic",
                    "richer environmental storytelling without visual chaos",
                    "higher information density while preserving one clear focal path",
                ],
                "style_family": [
                    "editorial illustration with layered scene design",
                    "polished photorealistic lifestyle scene",
                    "detailed mixed-media illustration with modern composition",
                    "realistic branded environment with controlled styling",
                ],
                "text_safe": [
                    "keep at least 15% open space for readable headline placement without flattening the scene",
                    "leave one readable margin while preserving contextual richness",
                    "maintain a calm text-safe edge area with layered scene depth",
                    "reserve subtle negative space near one side of the image",
                ],
                "closing": "Let GPT Image 2 decide how much contextual richness is useful; keep it readable at a glance.",
            },
        }
        selected = pattern_map.get(str(pattern_key or "").strip().lower(), pattern_map["simple"])
        style_family_options = selected["style_family"]
        text_safe_options = selected["text_safe"]
        hint = (
            "Variation {idx} [{label}]: {composition}; {lighting}; "
            "{palette}; {detail}; style family: {style_family}; {text_safe}. "
            "{closing}"
        ).format(
            idx=index + 1,
            label=selected["label"],
            composition=random.choice(selected["composition"]),
            lighting=random.choice(selected["lighting"]),
            palette=random.choice(selected["palette"]),
            detail=random.choice(selected["detail"]),
            style_family=style_family_options[index % len(style_family_options)],
            text_safe=text_safe_options[index % len(text_safe_options)],
            closing=selected["closing"],
        )
        return prompt.rstrip() + "\n\n" + hint

    def _is_gpt_image2_model(self, model: str) -> bool:
        return str(model or "").strip().lower().startswith("gpt-image-2")

    def _normalize_image_output_format(self, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"png", "jpeg", "webp"}:
            return normalized
        if normalized == "jpg":
            return "jpeg"
        return ""

    def _normalize_image_background(self, model: str, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized == "transparent" and self._is_gpt_image2_model(model):
            return ""
        if normalized in {"opaque", "auto"}:
            return normalized
        return ""

    def _normalize_image_moderation(self, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"auto", "low"}:
            return normalized
        return ""

    def _build_image_generation_params(
        self,
        *,
        model: str,
        prompt: str,
        n: int,
        size: str,
        quality: str,
        output_format: str,
        background: str,
        moderation: str,
    ) -> dict:
        params = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
        }
        resolved_output_format = self._normalize_image_output_format(output_format)
        if resolved_output_format:
            params["output_format"] = resolved_output_format
        resolved_background = self._normalize_image_background(model, background)
        if resolved_background:
            params["background"] = resolved_background
        resolved_moderation = self._normalize_image_moderation(moderation)
        if resolved_moderation:
            params["moderation"] = resolved_moderation
        return params

    def generate_images(
        self,
        prompt: str,
        n: int = DEFAULT_IMAGE_COUNT,
        size: str = DEFAULT_IMAGE_SIZE,
        quality: str = DEFAULT_IMAGE_QUALITY,
        model: str = DEFAULT_IMAGE_MODEL,
        pattern_key: str = "simple",
        output_format: str = DEFAULT_IMAGE_OUTPUT_FORMAT,
        background: str = DEFAULT_IMAGE_BACKGROUND,
        moderation: str = DEFAULT_IMAGE_MODERATION,
        allow_text: bool = False,
    ) -> List[Path]:
        output_dir = Path(GENERATED_IMAGES_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)

        def _request_images(request_prompt: str, count: int) -> List[Path]:
            if NO_TEXT_IN_IMAGE and not allow_text:
                request_prompt = request_prompt.rstrip() + "\n\nNo text, letters, or words in the image."
            params = self._build_image_generation_params(
                model=model,
                prompt=request_prompt,
                n=count,
                size=size,
                quality=quality,
                output_format=output_format,
                background=background,
                moderation=moderation,
            )
            params = self._filter_supported_params(self.client.images.generate, params)
            response = self.client.images.generate(**params)

            try:
                self._record_image_usage(
                    response,
                    model=params.get("model", model),
                    size=params.get("size", size),
                    quality=params.get("quality", quality),
                    n=params.get("n", count),
                )
            except (AttributeError, TypeError, ValueError) as exc:
                logger.debug("Failed to record image usage after generation", exc_info=exc)

            results: List[Path] = []
            skipped_without_b64 = 0
            for i, item in enumerate(getattr(response, "data", []) or []):
                b64 = getattr(item, "b64_json", None)
                if not b64 and isinstance(item, dict):
                    b64 = item.get("b64_json")
                if not b64:
                    skipped_without_b64 += 1
                    continue
                raw = base64.b64decode(b64)
                resolved_format = self._normalize_image_output_format(str(params.get("output_format") or output_format))
                extension = "jpg" if resolved_format in {"", "jpeg"} else resolved_format
                filename = f"gen_{uuid.uuid4().hex}_{i}.{extension}"
                raw_path = output_dir / filename
                raw_path.write_bytes(raw)
                results.append(self._resize_for_note(raw_path))
            if not results and skipped_without_b64 > 0:
                logger.warning(
                    "No images saved: response contained %s item(s) without b64 payload. "
                    "Check image API output format settings.",
                    skipped_without_b64,
                )
            return results

        if n <= 1:
            return _request_images(prompt, n)

        results: List[Path] = []
        for i in range(int(n)):
            varied_prompt = self._build_image_variation_prompt(prompt, i, pattern_key=pattern_key)
            results.extend(_request_images(varied_prompt, 1))
        return results

    def get_usage_summary(self):
        return self.token_tracker.get_summary()

    def optimize_genre_prompt(self, user_input: str) -> dict:
        """
        Optimize user input into a structured genre definition.
        
        Returns:
            dict: {"key": "...", "label": "...", "prompt": "..."}
        """
        import json as _json
        import re as _re
        
        safe_user_input = to_prompt_json_string(user_input, empty_value="指定なし", max_length=600)
        fallback_user_input = sanitize_untrusted_text(user_input, max_length=120)
        _empty_input = not fallback_user_input
        if _empty_input:
            fallback_user_input = "一般的なテーマ"

        prompt = f"""
ユーザーが以下のジャンルを追加したいと言っています。

ユーザー入力（JSON文字列）: {safe_user_input}

これをnote記事生成システムに適した形式に最適化してください。
このシステムは「読者への共感」と「人間味のある文章」を最重要視していますが、ジャンルによっては「正確な解説」も必要です。

【判断基準】
ユーザー入力に「分析」「比較」「検証」「レポート」「統計」「データ」等が含まれる場合 → 【Informative Style】を選び、根拠重視の文面にする
ユーザー入力に「企業ブランディング」「コーポレート」「企業紹介」「会社紹介」「理念」「ビジョン」「ミッション」「価値訴求」等が含まれる場合 → 【Brand Value Style】を選択
ユーザー入力に「解説」「紹介」「まとめ」等の意図が含まれる場合 → 【Informative Style】を選択
それ以外（エッセイ、体験談などで、個人の経験共有が主目的）の場合 → 【Narrative Style】を選択

【必須要件（共通）】
- 記事の「目的」はあくまで内部ガイド。
- 読者が「自分ごと」として捉えられる導入（共感フック）は必須。
- 「教科書的な棒読み」は禁止。

【出力形式】
次のJSON形式で出力してください：
{{"key": "英数字のキー(スネークケース)", "label": "日本語のラベル(10文字以内)", "prompt": "執筆ガイドライン"}}

【promptフィールドのテンプレート（以下のいずれかを使用）】

パターンA：Informative Style（解説系）用
【内部ガイド】目的: [ユーザーの意図]のわかりやすい翻訳と価値伝達
【スタイル: Informative & Empathy】
1. 導入(Context): なぜ今、これを知る必要があるのか。読者のどんな悩みや好奇心に応えるかを示す。
2. 解説(Translation): 専門用語を日常語に「翻訳」しながら解説する（PREP法を意識）。
3. 展開(Scenario): その知識があると、読者の生活や仕事がどう良くなるかを描写。
4. 結び(Action): すぐ確認できる具体策を提示。
【禁止】専門用語の羅列、突き放したような説明。

※分析系（比較/検証/データ）なら以下を追加:
- 事実→解釈→示唆の順で整理する
- 数字・固有名詞は根拠不明なら断定せず抽象化する
- 断言しすぎず、読者の判断材料を提示する

パターンB：Brand Value Style（企業ブランディング・会社紹介系）用
【内部ガイド】目的: [ユーザーの意図]に沿って、自社の価値・信頼・独自性をわかりやすく伝える
【スタイル: Brand Value & Trust】
1. 導入(Context): 会社の存在意義と提供価値を1〜2文で明確に示す。
2. 本文(Value): 自社が大切にしている考え方と実際の取り組みを具体的に示す。
3. 根拠(Proof): 公式情報・実績・方針など、確認可能な要素を整理して示す。
4. 結び(Message): 読者にとっての意味（選ぶ理由・期待できる価値）を端的に伝える。
【禁止】体験談や葛藤の必須化、過度な自分語り、根拠のない最上級表現。

パターンC：Narrative Style（ストーリー系）用
【内部ガイド】目的: [ユーザーの意図]を通じた共感と気づき
【スタイル: Narrative & Insight】
1. 導入(Episode): 読者が共感できる「あるある」や具体的な失敗談・体験から入る。
2. 展開(Drama): 感情の動きや気づきの瞬間を、エッセイのように描く。
3. 解決(Message): 個人の体験から得られた、普遍的な教訓を伝える。
4. 結び(Hope): 読者の背中を押す温かいメッセージ。
【禁止】「解説します」「メリットは」等の事務的な言葉。

【出力】
JSONのみを出力してください。
""".strip()
        
        raw = ""
        try:
            raw = self.generate_text(prompt, max_tokens=300, task_type="genre_optimize")
        except Exception as exc:
            logger.warning("Genre prompt optimization failed. Using fallback genre.", exc_info=exc)

        if raw:
            match = _re.search(r"\{.*\}", raw, _re.S)
            if match:
                try:
                    data = _json.loads(match.group(0))
                except (_json.JSONDecodeError, TypeError, ValueError) as exc:
                    logger.debug("Failed to parse optimized genre JSON", exc_info=exc)
                else:
                    if all(k in data for k in ["key", "label", "prompt"]):
                        data["key"] = _re.sub(r"[^a-z0-9_]", "_", data["key"].lower())
                        return data

        fallback_key = _re.sub(r"[^a-z0-9]", "_", fallback_user_input[:20].lower())
        narrative_hint = _re.search(r"(体験|経験|エッセイ|日記|失敗談|気づき|想い)", fallback_user_input)
        analysis_hint = _re.search(r"(分析|比較|検証|レポート|統計|データ|調査)", fallback_user_input)
        branding_hint = _re.search(
            r"(企業ブランディング|コーポレート|企業紹介|会社紹介|企業情報|理念|ミッション|ビジョン|パーパス|アイデンティティ|identity|philosophy|価値訴求|ブランド戦略)",
            fallback_user_input,
            _re.I,
        )
        if analysis_hint:
            fallback_prompt = (
                f"【内部ガイド】目的: {fallback_user_input}の分析と実務判断に役立つ示唆を伝える\n"
                "【スタイル: Informative & Evidence】\n"
                "1. 導入(Context): 何を判断するための分析かを明確にする。\n"
                "2. 分析(Evidence): 事実→解釈→示唆の順で整理し、比較観点を示す。\n"
                "3. 実務(Decision): 読者が次に取れる行動を提案する。\n"
                "【禁止】根拠のない断定、数字の誇張。"
            )
        elif branding_hint:
            fallback_prompt = (
                f"【内部ガイド】目的: {fallback_user_input}に沿って、自社の価値・信頼・独自性をわかりやすく伝える\n"
                "【スタイル: Brand Value & Trust】\n"
                "1. 導入(Context): 会社の存在意義と提供価値を端的に示す。\n"
                "2. 本文(Value): 取り組み・方針・強みを具体的に示す。\n"
                "3. 根拠(Proof): 公式情報や確認可能な事実を中心に整理する。\n"
                "4. 結び(Message): 読者にとっての価値を明確に伝える。\n"
                "【禁止】体験談の必須化、葛藤の演出、誇張表現。"
            )
        elif narrative_hint:
            fallback_prompt = (
                f"【内部ガイド】目的: {fallback_user_input}を通じた共感と気づき\n"
                "【スタイル: Narrative & Insight】\n"
                "1. 導入(Episode): 体験や具体的な場面から入る。\n"
                "2. 展開(Drama): 感情の揺れと学びを描く。\n"
                "3. 結び(Hope): 読者が自分で試せる視点を残して締める。\n"
                "【禁止】事務的な定型句。"
            )
        else:
            fallback_prompt = (
                f"【内部ガイド】目的: {fallback_user_input}のわかりやすい翻訳と価値伝達\n"
                "【スタイル: Informative & Empathy】\n"
                "1. 導入(Context): 読者の疑問に寄り添う。\n"
                "2. 解説(Translation): 専門用語を噛み砕いて説明する。\n"
                "3. 結び(Action): 実践しやすい具体策を示す。\n"
                "【禁止】専門用語の羅列。"
            )
        return {
            "key": fallback_key or "custom_genre",
            "label": "一般記事" if _empty_input else fallback_user_input[:10],
            "prompt": fallback_prompt,
        }
