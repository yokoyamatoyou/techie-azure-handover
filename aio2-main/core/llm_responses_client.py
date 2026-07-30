# -*- coding: utf-8 -*-
"""Shared helper for calling OpenAI's Responses API with a reasoning-capable model.

Generalizes the pattern already proven in
`core/application/accessibility_improvement_builder.py`: structured JSON
output via strict `json_schema`, `reasoning={"effort": ...}` as a nested
param (Responses API shape, distinct from Chat Completions' flat
`reasoning_effort=` kwarg), and fail-closed behavior.

This module only wraps the API call and JSON parsing. It does not decide
what to ask the model, how to score anything, or what a caller should do on
failure - callers keep their own fallback behavior, same as
accessibility_improvement_builder.py's `build_accessibility_improvement_actions`.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


class LLMResponseError(RuntimeError):
    """Raised when a Responses API call fails or returns unparseable JSON.

    `status_code` is copied from the underlying OpenAI SDK exception when
    present (e.g. `openai.APIStatusError.status_code`), so callers with their
    own retry-on-429/500/503 logic keyed off `status_code` keep working
    after wrapping.
    """

    def __init__(self, message: str, *, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


# Confirmed live against the real API (2026-07-09): gpt-5.4-nano rejects both
# `temperature` ("Unsupported parameter: 'temperature' is not supported with
# this model", HTTP 400) and `top_p` (same error shape) even via the
# Responses API. This matches notecode's core/app_config.py
# disable_temperature_model_prefixes / disable_top_p_model_prefixes lists.
# accessibility_improvement_builder.py also routes its optional LLM formatting
# through this helper, so the same parameter compatibility gate applies there.
#
# gpt-5-series models have no sampling-randomness knob at all: the only
# supported controls are `reasoning.effort` (how much internal reasoning to
# do) and `text.verbosity` (targeted output length/detail). Neither one
# substitutes for what temperature used to buy (stylistic variation,
# consumer-natural tone vs. strict-analytical tone). Callers that relied on a
# specific temperature for that kind of effect need to ask for it explicitly
# in the prompt instead - the parameter itself will be silently dropped for
# these models by this module, not simulated.
_SAMPLING_UNSUPPORTED_MODEL_PREFIXES = ("gpt-5", "o1", "o3")


def supports_temperature(model: str) -> bool:
    name = str(model or "").strip().lower()
    return not name.startswith(_SAMPLING_UNSUPPORTED_MODEL_PREFIXES)


def supports_top_p(model: str) -> bool:
    name = str(model or "").strip().lower()
    return not name.startswith(_SAMPLING_UNSUPPORTED_MODEL_PREFIXES)


# Confirmed live against the real API (2026-07-09): the inverse problem also
# exists. gpt-4.1-mini (still aio2-main/PDFreport's actual default model)
# rejects `reasoning.effort` outright via the Responses API ("Unsupported
# parameter: 'reasoning.effort' is not supported with this model", HTTP 400).
# So `reasoning` must be gated the same way temperature/top_p are, just with
# the opposite prefix set - only gpt-5/o1/o3-family models accept it.
_REASONING_SUPPORTED_MODEL_PREFIXES = ("gpt-5", "o1", "o3")


def supports_reasoning(model: str) -> bool:
    name = str(model or "").strip().lower()
    return name.startswith(_REASONING_SUPPORTED_MODEL_PREFIXES)


def pydantic_model_to_strict_schema(model_cls: Any) -> Dict[str, Any]:
    """Convert a Pydantic BaseModel class to an OpenAI strict `json_schema`.

    OpenAI's strict mode requires every property to appear in `required`
    (even fields Pydantic treats as optional-with-default) and
    `additionalProperties: false` at every object level - neither is true of
    Pydantic's own `model_json_schema()` output by default. This walks the
    schema and enforces both, resolving `$ref`/`$defs` for nested models.
    """
    schema = model_cls.model_json_schema()
    defs = schema.get("$defs") or {}
    return _enforce_strict_object(schema, defs)


def _enforce_strict_object(node: Dict[str, Any], defs: Dict[str, Any]) -> Dict[str, Any]:
    if "$ref" in node:
        ref_name = str(node["$ref"]).rsplit("/", 1)[-1]
        return _enforce_strict_object(dict(defs.get(ref_name) or {}), defs)
    node = dict(node)
    node.pop("$defs", None)
    node.pop("default", None)
    if "properties" in node:
        properties = node.get("properties") or {}
        node["properties"] = {
            key: _enforce_strict_object(dict(value), defs) for key, value in properties.items()
        }
        node["required"] = list(properties.keys())
        node["additionalProperties"] = False
    if node.get("type") == "array" and "items" in node:
        node["items"] = _enforce_strict_object(dict(node["items"]), defs)
    return node


def parse_json_response(response: Any) -> Dict[str, Any]:
    """Extract a JSON object from a Responses API response.

    Mirrors accessibility_improvement_builder.py's `_parse_llm_json_response`,
    generalized to return the full parsed object instead of a fixed field set.
    """
    # Confirmed live (2026-07-09): when the model runs out of
    # `max_output_tokens` mid-generation, the API does not return an HTTP
    # error - it returns HTTP 200 with `response.status == "incomplete"` and
    # `response.incomplete_details.reason == "max_output_tokens"`. Checking
    # this explicitly (rather than relying on the resulting partial JSON to
    # fail `json.loads`) catches truncation even in the rare case where the
    # cut-off text still happens to parse as valid JSON.
    if str(getattr(response, "status", "") or "") == "incomplete":
        details = getattr(response, "incomplete_details", None)
        reason = str(getattr(details, "reason", "") or "unknown")
        raise LLMResponseError(f"response_incomplete: reason={reason}")
    text = str(getattr(response, "output_text", "") or "")
    if not text:
        chunks: List[str] = []
        for item in getattr(response, "output", None) or []:
            for content in getattr(item, "content", []) or []:
                value = getattr(content, "text", None)
                if value:
                    chunks.append(str(value))
        text = "\n".join(chunks)
    if not text.strip():
        raise LLMResponseError("empty_response_text")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"invalid_json_response: {exc}") from exc
    if not isinstance(parsed, dict):
        raise LLMResponseError("response_not_object")
    return parsed


def _build_kwargs(
    *,
    model: str,
    reasoning_effort: str,
    input_messages: List[Dict[str, str]],
    json_schema_name: str,
    json_schema: Dict[str, Any],
    max_output_tokens: int,
    temperature: Optional[float],
    top_p: Optional[float],
    verbosity: Optional[str],
) -> Dict[str, Any]:
    text_format: Dict[str, Any] = {
        "format": {
            "type": "json_schema",
            "name": json_schema_name,
            "schema": json_schema,
            "strict": True,
        }
    }
    # Confirmed live (2026-07-09): unlike temperature/top_p/reasoning,
    # verbosity is not a clean supported/unsupported split per model family -
    # gpt-4.1-mini accepts the parameter but only the literal value "medium"
    # ("Unsupported value: 'low' is not supported with the
    # 'gpt-4.1-mini-2025-04-14' model. Supported values are: 'medium'.").
    # Rather than track each model's allowed value set, verbosity is only
    # ever sent for reasoning-capable models (gpt-5/o1/o3), matching
    # `supports_reasoning`; non-reasoning models simply don't get this
    # control, since they had no equivalent knob before this migration either.
    if verbosity and supports_reasoning(model):
        text_format["verbosity"] = verbosity
    kwargs: Dict[str, Any] = {
        "model": model,
        "input": input_messages,
        "text": text_format,
        "max_output_tokens": max_output_tokens,
    }
    if reasoning_effort and supports_reasoning(model):
        kwargs["reasoning"] = {"effort": reasoning_effort}
    if temperature is not None and supports_temperature(model):
        kwargs["temperature"] = temperature
    if top_p is not None and supports_top_p(model):
        kwargs["top_p"] = top_p
    return kwargs


def call_structured(
    client: Any,
    *,
    model: str,
    reasoning_effort: str,
    input_messages: List[Dict[str, str]],
    json_schema_name: str,
    json_schema: Dict[str, Any],
    max_output_tokens: int,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    verbosity: Optional[str] = None,
) -> tuple[Dict[str, Any], Any]:
    """Call the Responses API (sync client) and return (parsed JSON, raw response).

    The raw response is returned alongside the parsed data so callers can
    read `response.usage.input_tokens` / `.output_tokens` (Responses API
    naming, confirmed live to differ from Chat Completions'
    `prompt_tokens`/`completion_tokens`) for token tracking, without this
    module needing to know about any particular tracker.

    `temperature` / `top_p` are silently omitted for models that reject them
    (see `supports_temperature` / `supports_top_p`), and `reasoning` is
    silently omitted for models that reject *it* instead (non gpt-5/o1/o3
    models - see `supports_reasoning`) - so callers can keep passing their
    previously-tuned values unconditionally regardless of which model is
    configured. `verbosity`
    (Responses API's output-length control, confirmed live to belong inside
    `text`, not as a top-level kwarg) is passed through as-is when given.

    Raises LLMResponseError on any failure (network, API, or JSON parsing).
    Callers are responsible for fail-closed fallback behavior. Use
    `call_structured_async` for an `AsyncOpenAI`-backed client.
    """
    kwargs = _build_kwargs(
        model=model,
        reasoning_effort=reasoning_effort,
        input_messages=input_messages,
        json_schema_name=json_schema_name,
        json_schema=json_schema,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        verbosity=verbosity,
    )
    try:
        response = client.responses.create(**kwargs)
    except Exception as exc:
        raise LLMResponseError(f"responses_api_call_failed: {exc}", status_code=getattr(exc, "status_code", None)) from exc
    return parse_json_response(response), response


async def call_structured_async(
    client: Any,
    *,
    model: str,
    reasoning_effort: str,
    input_messages: List[Dict[str, str]],
    json_schema_name: str,
    json_schema: Dict[str, Any],
    max_output_tokens: int,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    verbosity: Optional[str] = None,
) -> tuple[Dict[str, Any], Any]:
    """Async twin of `call_structured` for an `AsyncOpenAI`-backed client

    (PDFreport's `OpenAIAdapter._raw` is an `AsyncOpenAI` instance). Same
    contract, parameters, and compatibility handling as `call_structured`.
    """
    kwargs = _build_kwargs(
        model=model,
        reasoning_effort=reasoning_effort,
        input_messages=input_messages,
        json_schema_name=json_schema_name,
        json_schema=json_schema,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        verbosity=verbosity,
    )
    try:
        response = await client.responses.create(**kwargs)
    except Exception as exc:
        raise LLMResponseError(f"responses_api_call_failed: {exc}", status_code=getattr(exc, "status_code", None)) from exc
    return parse_json_response(response), response
