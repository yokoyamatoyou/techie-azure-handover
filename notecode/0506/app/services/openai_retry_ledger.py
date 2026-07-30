from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any, Callable

from app.services.openai_retry_helpers import (
    float_env,
    int_env,
    is_timeout_error,
    is_transient_openai_error,
    packet_id,
    payload_sha256,
    redact_error_text,
    request_id_from_error,
    request_id_from_response,
    response_id,
    response_id_from_error,
    retry_after_seconds,
    status_code,
    utc_timestamp,
)

SOURCE_CARD_STAGE_NAME = "source_card_extraction"
SOURCE_CARD_SCHEMA_NAME = "source_card.schema.json"
DRAFT_WRITER_STAGE_NAME = "draft_writer"
EDITOR_TEXT_STAGE_NAMES = {
    "opening_editor",
    "global_consistency_editor",
    "style_editor",
    "structural_editor",
}


class OpenAITransientRetryController:
    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str,
        max_source_card_retries: int | None = None,
        request_timeout_seconds: float | None = None,
        initial_backoff_seconds: float | None = None,
        max_backoff_seconds: float | None = None,
        jitter_seconds: float | None = None,
        sleep_func: Callable[[float], None] | None = None,
        random_func: Callable[[], float] | None = None,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.source_card_max_retries = (
            int(max_source_card_retries)
            if max_source_card_retries is not None
            else int_env("ROUTE_0506_SOURCE_CARD_MAX_RETRIES", 2)
        )
        self.json_stage_max_retries = int_env("ROUTE_0506_JSON_STAGE_MAX_RETRIES", 1)
        self.draft_writer_max_retries = int_env("ROUTE_0506_DRAFT_WRITER_MAX_RETRIES", 1)
        self.editor_stage_max_retries = int_env("ROUTE_0506_EDITOR_STAGE_MAX_RETRIES", 1)
        self.request_timeout_seconds = (
            float(request_timeout_seconds)
            if request_timeout_seconds is not None
            else float_env("ROUTE_0506_OPENAI_REQUEST_TIMEOUT_SECONDS", 180.0)
        )
        self.initial_backoff_seconds = (
            float(initial_backoff_seconds)
            if initial_backoff_seconds is not None
            else float_env("ROUTE_0506_OPENAI_RETRY_INITIAL_BACKOFF_SECONDS", 1.0)
        )
        self.max_backoff_seconds = (
            float(max_backoff_seconds)
            if max_backoff_seconds is not None
            else float_env("ROUTE_0506_OPENAI_RETRY_MAX_BACKOFF_SECONDS", 8.0)
        )
        self.jitter_seconds = (
            float(jitter_seconds)
            if jitter_seconds is not None
            else float_env("ROUTE_0506_OPENAI_RETRY_JITTER_SECONDS", 0.5)
        )
        self.max_server_retry_after_seconds = float_env(
            "ROUTE_0506_OPENAI_RETRY_MAX_SERVER_HINT_SECONDS",
            120.0,
        )
        self._sleep = sleep_func or time.sleep
        self._random = random_func or random.random
        self._inflight_ledger_path: Path | None = None

    def set_inflight_ledger_path(self, path: Path | str) -> None:
        self._inflight_ledger_path = Path(path)

    def uses_source_card_retry(self, stage_name: str, schema_name: str) -> bool:
        return stage_name == SOURCE_CARD_STAGE_NAME and schema_name == SOURCE_CARD_SCHEMA_NAME

    def uses_draft_writer_retry(self, stage_name: str) -> bool:
        return stage_name == DRAFT_WRITER_STAGE_NAME

    def uses_text_stage_retry(self, stage_name: str) -> bool:
        return self.uses_draft_writer_retry(stage_name) or stage_name in EDITOR_TEXT_STAGE_NAMES

    def create_source_card_response_with_retry(
        self,
        responses_api: Any,
        *,
        stage_name: str,
        schema_name: str,
        payload: dict[str, Any],
        create_kwargs: dict[str, Any],
    ) -> Any:
        return self._create_response_with_retry(
            responses_api,
            stage_name=stage_name,
            schema_name=schema_name,
            payload=payload,
            create_kwargs=create_kwargs,
            max_retries=self.source_card_max_retries,
        )

    def create_draft_writer_response_with_retry(
        self,
        responses_api: Any,
        *,
        stage_name: str,
        payload: dict[str, Any],
        create_kwargs: dict[str, Any],
    ) -> Any:
        return self._create_response_with_retry(
            responses_api,
            stage_name=stage_name,
            schema_name="",
            payload=payload,
            create_kwargs=create_kwargs,
            max_retries=self.draft_writer_max_retries,
        )

    def create_text_response_with_retry(
        self,
        responses_api: Any,
        *,
        stage_name: str,
        payload: dict[str, Any],
        create_kwargs: dict[str, Any],
    ) -> Any:
        max_retries = (
            self.draft_writer_max_retries
            if self.uses_draft_writer_retry(stage_name)
            else self.editor_stage_max_retries
        )
        return self._create_response_with_retry(
            responses_api,
            stage_name=stage_name,
            schema_name="",
            payload=payload,
            create_kwargs=create_kwargs,
            max_retries=max_retries,
        )

    def create_json_response_with_retry(
        self,
        responses_api: Any,
        *,
        stage_name: str,
        schema_name: str,
        payload: dict[str, Any],
        create_kwargs: dict[str, Any],
    ) -> Any:
        return self._create_response_with_retry(
            responses_api,
            stage_name=stage_name,
            schema_name=schema_name,
            payload=payload,
            create_kwargs=create_kwargs,
            max_retries=self.json_stage_max_retries,
        )

    def _create_response_with_retry(
        self,
        responses_api: Any,
        *,
        stage_name: str,
        schema_name: str,
        payload: dict[str, Any],
        create_kwargs: dict[str, Any],
        max_retries: int,
    ) -> Any:
        retry_limit = max(0, int(max_retries))
        max_attempts = retry_limit + 1
        for attempt in range(1, max_attempts + 1):
            started_at = utc_timestamp()
            self._append_ledger_row(
                self._ledger_base_row(stage_name, schema_name, payload, attempt, started_at, "inflight_unmetered", retry_limit)
            )
            try:
                response = responses_api.create(**create_kwargs)
            except KeyboardInterrupt as exc:
                self._append_terminal_error_row(
                    stage_name, schema_name, payload, attempt, started_at, "cancelled", exc, False, 0.0, retry_limit
                )
                raise
            except Exception as exc:
                will_retry = is_transient_openai_error(exc) and attempt < max_attempts
                status = "timeout" if is_timeout_error(exc) else "failed"
                retry_after = self._retry_delay_seconds(attempt, exc) if will_retry else 0.0
                self._append_terminal_error_row(
                    stage_name,
                    schema_name,
                    payload,
                    attempt,
                    started_at,
                    status,
                    exc,
                    will_retry,
                    retry_after,
                    retry_limit,
                )
                if not will_retry:
                    raise
                self._sleep(retry_after)
                continue
            self._append_ledger_row(
                {
                    **self._ledger_base_row(stage_name, schema_name, payload, attempt, started_at, "success", retry_limit),
                    "ended_at": utc_timestamp(),
                    "request_id": request_id_from_response(response),
                    "response_id": response_id(response),
                    "terminal": True,
                    "will_retry": False,
                }
            )
            return response
        raise RuntimeError("unreachable_openai_retry_state")

    def _ledger_base_row(
        self,
        stage_name: str,
        schema_name: str,
        payload: dict[str, Any],
        attempt: int,
        started_at: str,
        status: str,
        max_retries: int,
    ) -> dict[str, Any]:
        return {
            "timestamp": utc_timestamp(),
            "stage": stage_name,
            "schema_name": schema_name,
            "packet_id": packet_id(payload),
            "attempt": int(attempt),
            "max_retries": int(max_retries),
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "request_timeout_seconds": float(self.request_timeout_seconds),
            "started_at": started_at,
            "ended_at": "",
            "status": status,
            "actual_usage_available": False,
            "usage_status": "inflight_unmetered" if status == "inflight_unmetered" else "requested_unmetered",
            "payload_sha256": payload_sha256(payload),
            "error_type": "",
            "error_status_code": 0,
            "request_id": "",
            "response_id": "",
            "terminal": False,
            "will_retry": False,
            "retry_after_seconds": 0.0,
        }

    def _append_terminal_error_row(
        self,
        stage_name: str,
        schema_name: str,
        payload: dict[str, Any],
        attempt: int,
        started_at: str,
        status: str,
        exc: BaseException,
        will_retry: bool,
        retry_after_seconds: float,
        max_retries: int,
    ) -> None:
        self._append_ledger_row(
            {
                **self._ledger_base_row(stage_name, schema_name, payload, attempt, started_at, status, max_retries),
                "ended_at": utc_timestamp(),
                "error_type": type(exc).__name__,
                "error_status_code": status_code(exc),
                "error_message_redacted": redact_error_text(exc),
                "request_id": request_id_from_error(exc),
                "response_id": response_id_from_error(exc),
                "terminal": True,
                "will_retry": bool(will_retry),
                "retry_after_seconds": float(retry_after_seconds),
            }
        )

    def _append_ledger_row(self, row: dict[str, Any]) -> None:
        if self._inflight_ledger_path is None:
            return
        self._inflight_ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self._inflight_ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    def _retry_delay_seconds(self, attempt: int, exc: BaseException | None = None) -> float:
        base = self.initial_backoff_seconds * (2 ** max(0, attempt - 1))
        jitter = self._random() * max(0.0, self.jitter_seconds)
        local_backoff = min(self.max_backoff_seconds, base + jitter)
        if exc is None:
            return local_backoff
        server_hint = min(
            retry_after_seconds(exc),
            max(0.0, self.max_server_retry_after_seconds),
        )
        return max(local_backoff, server_hint)
