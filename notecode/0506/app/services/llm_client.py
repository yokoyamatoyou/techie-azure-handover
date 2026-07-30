from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Protocol

from app.services.openai_retry_ledger import OpenAITransientRetryController
from app.services.openai_schema_compat import (
    OPENAI_UNSUPPORTED_SCHEMA_KEYS,
    normalize_openai_json_for_local_schema,
    schema_for_openai_response_format,
)
from app.services.schema_validator import load_schema


_schema_for_openai_response_format = schema_for_openai_response_format


def _resolve_env_var(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    if os.name != "nt":
        return ""
    try:
        import winreg
    except ImportError:
        return ""

    locations = (
        (winreg.HKEY_CURRENT_USER, "Environment"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
    )
    for hive, path in locations:
        try:
            with winreg.OpenKey(hive, path) as key:
                raw, _ = winreg.QueryValueEx(key, name)
        except OSError:
            continue
        value = str(raw or "").strip()
        if value:
            os.environ[name] = value
            return value
    return ""


class LLMClient(Protocol):
    def generate_json(
        self,
        stage_name: str,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        ...

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        ...


class OpenAIResponsesClient:
    def __init__(
        self,
        model: str | None = None,
        *,
        client: Any | None = None,
        max_source_card_retries: int | None = None,
        request_timeout_seconds: float | None = None,
        initial_backoff_seconds: float | None = None,
        max_backoff_seconds: float | None = None,
        jitter_seconds: float | None = None,
        sleep_func: Callable[[float], None] | None = None,
        random_func: Callable[[], float] | None = None,
    ) -> None:
        if client is None:
            from openai import OpenAI

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
        self.reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "high") if _supports_reasoning(self.model) else ""
        self.temperature = _float_env_optional("ROUTE_0506_OPENAI_TEMPERATURE")
        self.retry_controller = OpenAITransientRetryController(
            model=self.model,
            reasoning_effort=self.reasoning_effort,
            max_source_card_retries=max_source_card_retries,
            request_timeout_seconds=request_timeout_seconds,
            initial_backoff_seconds=initial_backoff_seconds,
            max_backoff_seconds=max_backoff_seconds,
            jitter_seconds=jitter_seconds,
            sleep_func=sleep_func,
            random_func=random_func,
        )
        self.request_timeout_seconds = self.retry_controller.request_timeout_seconds
        self.client = client if client is not None else OpenAI(timeout=self.request_timeout_seconds, max_retries=0)

    def set_inflight_ledger_path(self, path: Path | str) -> None:
        self.retry_controller.set_inflight_ledger_path(path)

    def generate_json(
        self,
        stage_name: str,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        schema = load_schema(schema_name)
        response_schema = schema_for_openai_response_format(schema)
        create_kwargs = {
            "model": self.model,
            "input": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": stage_name,
                    "schema": response_schema,
                    "strict": True,
                }
            },
            "timeout": self.request_timeout_seconds,
        }
        self._apply_model_parameters(create_kwargs)
        if self.retry_controller.uses_source_card_retry(stage_name, schema_name):
            response = self.retry_controller.create_source_card_response_with_retry(
                self.client.responses,
                stage_name=stage_name,
                schema_name=schema_name,
                payload=payload,
                create_kwargs=create_kwargs,
            )
        else:
            response = self.retry_controller.create_json_response_with_retry(
                self.client.responses,
                stage_name=stage_name,
                schema_name=schema_name,
                payload=payload,
                create_kwargs=create_kwargs,
            )
        return normalize_openai_json_for_local_schema(json.loads(response.output_text), schema_name)

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        create_kwargs = {
            "model": self.model,
            "input": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "timeout": self.request_timeout_seconds,
        }
        self._apply_model_parameters(create_kwargs)
        if self.retry_controller.uses_text_stage_retry(stage_name):
            response = self.retry_controller.create_text_response_with_retry(
                self.client.responses,
                stage_name=stage_name,
                payload=payload,
                create_kwargs=create_kwargs,
            )
        else:
            response = self.client.responses.create(**create_kwargs)
        return response.output_text

    def _apply_model_parameters(self, create_kwargs: dict[str, Any]) -> None:
        if _supports_reasoning(self.model):
            create_kwargs["reasoning"] = {"effort": self.reasoning_effort or "high"}
            return
        if self.temperature is not None:
            create_kwargs["temperature"] = self.temperature


def select_default_llm_client() -> LLMClient:
    if os.getenv("BLOGGEN_LLM_MODE") == "openai":
        if not _resolve_env_var("OPENAI_API_KEY"):
            raise RuntimeError("BLOGGEN_LLM_MODE=openai requires OPENAI_API_KEY")
        return OpenAIResponsesClient()
    from app.services.local_llm_client import LocalPipelineClient

    return LocalPipelineClient()


def _supports_reasoning(model: str) -> bool:
    value = str(model or "").strip().lower()
    return value.startswith(("gpt-5", "o1", "o3", "o4"))


def _float_env_optional(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
