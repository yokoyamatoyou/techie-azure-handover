from __future__ import annotations

import json
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from analysis_lib import normalize_text
from config import AppConfig, get_provider_api_key, get_provider_batch_completion_window, get_provider_batch_endpoint
from run_policy import resolve_run_policy

from llmo_core.models import AnalysisResult, BatchImportRecord, BatchJobHandle, BatchRequestItem
from llmo_core.openai_client import LLMOClient

class GeminiClient(LLMOClient):
    GEMINI_API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
    GEMINI_REST_ROOT = "https://generativelanguage.googleapis.com/v1beta"

    def analyze_keyword(self, keyword: str, config: AppConfig) -> AnalysisResult:
        response_body = self._post_generate_content(keyword, config)
        internal_body = self._gemini_response_to_internal_body(response_body)
        result = self._analysis_result_from_response_body(
            internal_body,
            keyword,
            config,
            user_query_raw=keyword,
            executed_query=keyword,
        )
        result.web_search_calls = self._gemini_web_search_call_count(response_body)
        return result

    def submit_batch(
        self,
        config: AppConfig,
        execution_requests: list[dict[str, Any]] | None = None,
    ) -> tuple[BatchJobHandle, list[BatchRequestItem]]:
        endpoint = get_provider_batch_endpoint(config.provider)
        completion_window = get_provider_batch_completion_window(config.provider)
        batch_policy = resolve_run_policy(config, "batch")
        if not endpoint or not completion_window or not batch_policy.allowed:
            raise NotImplementedError(
                f"provider '{config.provider}' does not support Batch mode in this PoC."
            )
        request_items = self._build_gemini_batch_request_items(config, execution_requests=execution_requests)
        response_body = self._gemini_json_request(
            f"{self.GEMINI_API_ROOT}/{config.model}:batchGenerateContent",
            method="POST",
            payload={
                "batch": {
                    "display_name": self._build_gemini_batch_display_name(config, len(request_items)),
                    "input_config": {
                        "requests": {
                            "requests": [
                                {
                                    "request": item.request_line.get("body") or {},
                                    "metadata": {"key": item.custom_id},
                                }
                                for item in request_items
                            ]
                        }
                    },
                }
            },
            api_key=self._require_gemini_api_key(config.provider),
        )
        return self._gemini_batch_handle_from_api(response_body, len(request_items)), request_items

    def retrieve_batch(self, batch_job_id: str) -> BatchJobHandle:
        response_body = self._gemini_json_request(
            f"{self.GEMINI_REST_ROOT}/{batch_job_id.lstrip('/')}",
            method="GET",
            api_key=self._require_gemini_api_key("gemini"),
        )
        return self._gemini_batch_handle_from_api(response_body)

    def import_batch_results(
        self,
        batch: BatchJobHandle,
        config: AppConfig,
        request_items: dict[str, dict[str, Any]],
    ) -> list[BatchImportRecord]:
        records: list[BatchImportRecord] = []
        seen_custom_ids: set[str] = set()
        for item in self._extract_gemini_batch_result_items(batch.raw_batch or {}):
            custom_id = self._extract_gemini_batch_custom_id(item)
            if not custom_id or custom_id in seen_custom_ids:
                continue
            seen_custom_ids.add(custom_id)
            request_item = request_items.get(custom_id)
            if request_item is None:
                records.append(
                    BatchImportRecord(
                        custom_id=custom_id,
                        remote_request_id="",
                        response_status_code=None,
                        result=None,
                        error_text="custom_id に対応するローカルのBatch項目が見つかりません。",
                    )
                )
                continue
            response_body = item.get("response") or {}
            error_body = item.get("error") or {}
            remote_request_id = str(
                item.get("name")
                or item.get("id")
                or response_body.get("responseId")
                or custom_id
            ).strip()
            if isinstance(response_body, dict) and response_body:
                executed_query = str(request_item.get("executed_query") or request_item.get("keyword_raw") or "").strip()
                user_query_raw = str(request_item.get("user_query_raw") or request_item.get("keyword_raw") or "").strip()
                internal_body = self._gemini_response_to_internal_body(response_body)
                result = self._analysis_result_from_response_body(
                    internal_body,
                    executed_query,
                    config,
                    user_query_raw=user_query_raw,
                    executed_query=executed_query,
                )
                result.web_search_calls = self._gemini_web_search_call_count(response_body)
                records.append(
                    BatchImportRecord(
                        custom_id=custom_id,
                        remote_request_id=remote_request_id,
                        response_status_code=200,
                        result=result,
                    )
                )
                continue
            error_text = str(error_body.get("message") or "").strip() or "Gemini Batch 実行結果の取り込みに失敗しました。"
            response_status_code = error_body.get("code")
            records.append(
                BatchImportRecord(
                    custom_id=custom_id,
                    remote_request_id=remote_request_id,
                    response_status_code=int(response_status_code) if str(response_status_code or "").isdigit() else None,
                    result=None,
                    error_text=error_text,
                )
            )
        return records

    def _post_generate_content(self, keyword: str, config: AppConfig) -> dict[str, Any]:
        request_body = self._build_generate_content_request_body(keyword, config)
        endpoint = f"{self.GEMINI_API_ROOT}/{config.model}:generateContent"
        return self._gemini_json_request(
            endpoint,
            method="POST",
            payload=request_body,
            api_key=self._require_gemini_api_key(config.provider),
        )

    def _build_generate_content_request_body(self, keyword: str, config: AppConfig) -> dict[str, Any]:
        reasoning_effort = self._resolve_reasoning_effort(config)
        payload = self._build_input_messages(keyword, config, reasoning_effort)[1]["content"][0]["text"]
        return {
            "system_instruction": {"parts": [{"text": self._build_analysis_prompt(config)}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": payload}],
                }
            ],
            "tools": [{"google_search": {}}],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": int(config.max_output_tokens or 1200),
            },
        }

    def _gemini_response_to_internal_body(self, response_body: dict[str, Any]) -> dict[str, Any]:
        candidates = response_body.get("candidates") or []
        candidate = candidates[0] if candidates and isinstance(candidates[0], dict) else {}
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        output_texts = [
            str(part.get("text") or "").strip()
            for part in parts
            if isinstance(part, dict) and str(part.get("text") or "").strip()
        ]
        grounding_metadata = candidate.get("groundingMetadata") or {}
        search_queries = [
            str(query or "").strip()
            for query in grounding_metadata.get("webSearchQueries") or []
            if str(query or "").strip()
        ]
        sources: list[dict[str, str]] = []
        for chunk in grounding_metadata.get("groundingChunks") or []:
            if not isinstance(chunk, dict):
                continue
            web = chunk.get("web") or {}
            url = str(web.get("uri") or "").strip()
            title = str(web.get("title") or "").strip()
            if url:
                sources.append({"url": url, "title": title})
        usage_metadata = response_body.get("usageMetadata") or {}
        usage = {
            "input_tokens": int(usage_metadata.get("promptTokenCount") or 0),
            "output_tokens": int(usage_metadata.get("candidatesTokenCount") or 0),
            "total_tokens": int(usage_metadata.get("totalTokenCount") or 0),
            "input_tokens_details": {
                "cached_tokens": int(usage_metadata.get("cachedContentTokenCount") or 0),
            },
        }
        output_items: list[dict[str, Any]] = []
        if sources or search_queries:
            output_items.append(
                {
                    "type": "web_search_call",
                    "action": {
                        "queries": search_queries,
                        "sources": sources,
                    },
                }
            )
        return {
            "output_text": "\n".join(output_texts).strip(),
            "usage": usage,
            "output": output_items,
        }

    def _build_gemini_batch_request_items(
        self,
        config: AppConfig,
        execution_requests: list[dict[str, Any]] | None = None,
    ) -> list[BatchRequestItem]:
        items: list[BatchRequestItem] = []
        endpoint = f"models/{config.model}:batchGenerateContent"
        if execution_requests:
            for request_index, request in enumerate(execution_requests, start=1):
                keyword = str(request.get("executed_query") or request.get("keyword") or "").strip()
                if not keyword:
                    continue
                iteration_index = int(request.get("iteration_index") or 1)
                custom_id = str(request.get("custom_id") or "").strip() or self._build_batch_custom_id(
                    keyword,
                    iteration_index,
                    request_index,
                )
                items.append(
                    BatchRequestItem(
                        custom_id=custom_id,
                        keyword_raw=keyword,
                        keyword_norm=normalize_text(keyword),
                        iteration_index=iteration_index,
                        request_line={
                            "custom_id": custom_id,
                            "method": "POST",
                            "url": endpoint,
                            "body": self._build_generate_content_request_body(keyword, config),
                        },
                    )
                )
            return items
        for keyword_index, keyword in enumerate(config.keywords, start=1):
            keyword_norm = normalize_text(keyword)
            for iteration_index in range(1, config.repeat_count + 1):
                custom_id = self._build_batch_custom_id(keyword, iteration_index, keyword_index)
                items.append(
                    BatchRequestItem(
                        custom_id=custom_id,
                        keyword_raw=keyword,
                        keyword_norm=keyword_norm,
                        iteration_index=iteration_index,
                        request_line={
                            "custom_id": custom_id,
                            "method": "POST",
                            "url": endpoint,
                            "body": self._build_generate_content_request_body(keyword, config),
                        },
                    )
                )
        return items

    def _build_gemini_batch_display_name(self, config: AppConfig, request_count: int) -> str:
        return f"kotomegane-{config.analysis_mode}-{config.model}-{request_count}"

    def _require_gemini_api_key(self, provider_key: str) -> str:
        api_key = get_provider_api_key(provider_key)
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY が見つかりません。")
        return api_key

    def _gemini_json_request(
        self,
        url: str,
        *,
        method: str,
        api_key: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_payload = None
        if payload is not None:
            request_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib_request.Request(
            url,
            data=request_payload,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "x-goog-api-key": api_key,
            },
            method=method,
        )
        try:
            with urllib_request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            error_text = exc.read().decode("utf-8", errors="ignore")
            message = self._extract_http_error_message(error_text) or error_text or str(exc)
            raise RuntimeError(f"Gemini request failed ({exc.code}): {message}") from exc
        except urllib_error.URLError as exc:
            raise RuntimeError(f"Gemini request failed: {exc.reason}") from exc

    def _gemini_batch_handle_from_api(
        self,
        response_body: dict[str, Any],
        request_count_hint: int = 0,
    ) -> BatchJobHandle:
        batch_job_id = str(response_body.get("name") or "").strip()
        raw_state = self._extract_gemini_batch_state(response_body)
        result_items = self._extract_gemini_batch_result_items(response_body)
        completed_count = sum(1 for item in result_items if isinstance(item.get("response"), dict) and item.get("response"))
        failed_count = sum(1 for item in result_items if item.get("error"))
        total_count = self._extract_gemini_batch_request_count(response_body)
        if total_count <= 0:
            total_count = len(result_items) or int(request_count_hint or 0)
        status = self._normalize_gemini_batch_status(raw_state, response_body, total_count, completed_count, failed_count)
        output_file_id = "inline_response" if result_items else ""
        error_file_id = "inline_error" if failed_count else ""
        if status in {"failed", "cancelled", "expired"} and not error_file_id:
            error_file_id = "batch_error"
        return BatchJobHandle(
            batch_job_id=batch_job_id,
            status=status,
            input_file_id="inline_requests",
            endpoint=str(response_body.get("target") or response_body.get("endpoint") or ""),
            completion_window=get_provider_batch_completion_window("gemini"),
            output_file_id=output_file_id,
            error_file_id=error_file_id,
            request_counts_total=total_count,
            request_counts_completed=completed_count,
            request_counts_failed=failed_count,
            raw_batch=response_body,
        )

    def _extract_gemini_batch_state(self, response_body: dict[str, Any]) -> str:
        metadata = response_body.get("metadata") or {}
        state = metadata.get("state") or response_body.get("state") or ""
        if isinstance(state, dict):
            return str(state.get("name") or state.get("state") or "").strip()
        return str(state or "").strip()

    def _normalize_gemini_batch_status(
        self,
        raw_state: str,
        response_body: dict[str, Any],
        total_count: int,
        completed_count: int,
        failed_count: int,
    ) -> str:
        state = raw_state.upper()
        if state.endswith("SUCCEEDED"):
            return "completed"
        if state.endswith("FAILED"):
            return "failed"
        if state.endswith("CANCELLED") or state.endswith("CANCELED"):
            return "cancelled"
        if state.endswith("EXPIRED"):
            return "expired"
        if state:
            return "in_progress"
        if bool(response_body.get("done")):
            if total_count and failed_count >= total_count and completed_count == 0:
                return "failed"
            if completed_count or response_body.get("response"):
                return "completed"
            if response_body.get("error"):
                return "failed"
        return "in_progress"

    def _extract_gemini_batch_request_count(self, response_body: dict[str, Any]) -> int:
        metadata = response_body.get("metadata") or {}
        for key in ("requestCount", "request_count", "totalRequests", "total_requests"):
            value = metadata.get(key)
            if value is None:
                continue
            try:
                return int(value)
            except Exception:
                continue
        return 0

    def _extract_gemini_batch_result_items(self, response_body: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = [
            response_body.get("inlinedResponses"),
            (response_body.get("dest") or {}).get("inlinedResponses"),
            (response_body.get("response") or {}).get("inlinedResponses"),
            ((response_body.get("response") or {}).get("dest") or {}).get("inlinedResponses"),
        ]
        for candidate in candidates:
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
            if isinstance(candidate, dict):
                nested = candidate.get("responses") or candidate.get("inlinedResponses") or candidate.get("items")
                if isinstance(nested, list):
                    return [item for item in nested if isinstance(item, dict)]
        return []

    def _extract_gemini_batch_custom_id(self, item: dict[str, Any]) -> str:
        metadata = item.get("metadata") or {}
        request_metadata = item.get("requestMetadata") or {}
        return str(
            metadata.get("key")
            or metadata.get("custom_id")
            or request_metadata.get("key")
            or request_metadata.get("custom_id")
            or item.get("key")
            or item.get("custom_id")
            or ""
        ).strip()

    def _extract_http_error_message(self, raw_text: str) -> str:
        try:
            payload = json.loads(raw_text)
        except Exception:
            return str(raw_text or "").strip()
        error_payload = payload.get("error") if isinstance(payload, dict) else {}
        if isinstance(error_payload, dict):
            return str(error_payload.get("message") or "").strip()
        return str(raw_text or "").strip()

    def _gemini_web_search_call_count(self, response_body: dict[str, Any]) -> int:
        candidates = response_body.get("candidates") or []
        candidate = candidates[0] if candidates and isinstance(candidates[0], dict) else {}
        grounding_metadata = candidate.get("groundingMetadata") or {}
        if grounding_metadata.get("webSearchQueries") or grounding_metadata.get("groundingChunks"):
            return 1
        return 0


