from __future__ import annotations

import json
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from analysis_lib import normalize_text
from config import ANALYSIS_MODE_OWNED_ONLY, AppConfig, get_provider_api_key, get_provider_batch_completion_window, get_provider_batch_endpoint
from run_policy import resolve_run_policy

from llmo_core.models import AnalysisResult, BatchImportRecord, BatchJobHandle, BatchRequestItem
from llmo_core.openai_client import LLMOClient

class ClaudeClient(LLMOClient):
    ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_BATCHES_URL = "https://api.anthropic.com/v1/messages/batches"
    ANTHROPIC_VERSION = "2023-06-01"
    ANTHROPIC_BATCH_BETA = "message-batches-2024-09-24"

    def analyze_keyword(self, keyword: str, config: AppConfig) -> AnalysisResult:
        response_body = self._post_messages_request(keyword, config)
        internal_body = self._claude_response_to_internal_body(response_body)
        result = self._analysis_result_from_response_body(
            internal_body,
            keyword,
            config,
            user_query_raw=keyword,
            executed_query=keyword,
        )
        if not result.output_json.get("citations"):
            result.output_json["citations"] = self._extract_claude_citations(response_body)
        if not result.output_json.get("citation_urls"):
            result.output_json["citation_urls"] = [
                str(item.get("url") or "").strip()
                for item in result.output_json.get("citations") or []
                if str(item.get("url") or "").strip()
            ][:8]
        result.web_search_calls = self._claude_web_search_call_count(response_body)
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
        request_items = self._build_claude_batch_request_items(config, execution_requests=execution_requests)
        response_body = self._claude_json_request(
            self.ANTHROPIC_BATCHES_URL,
            method="POST",
            api_key=self._require_anthropic_api_key(config.provider),
            payload={
                "requests": [
                    {
                        "custom_id": item.custom_id,
                        "params": item.request_line.get("body") or {},
                    }
                    for item in request_items
                ]
            },
            include_batch_beta=True,
        )
        return self._claude_batch_handle_from_api(response_body), request_items

    def retrieve_batch(self, batch_job_id: str) -> BatchJobHandle:
        response_body = self._claude_json_request(
            f"{self.ANTHROPIC_BATCHES_URL}/{batch_job_id}",
            method="GET",
            api_key=self._require_anthropic_api_key("claude"),
            include_batch_beta=True,
        )
        return self._claude_batch_handle_from_api(response_body)

    def import_batch_results(
        self,
        batch: BatchJobHandle,
        config: AppConfig,
        request_items: dict[str, dict[str, Any]],
    ) -> list[BatchImportRecord]:
        raw_text = self._claude_batch_results_text(batch.batch_job_id)
        records: list[BatchImportRecord] = []
        seen_custom_ids: set[str] = set()
        for line in self._parse_jsonl(raw_text):
            custom_id = str(line.get("custom_id") or "").strip()
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
            result_payload = line.get("result") or {}
            result_type = str(result_payload.get("type") or "").strip().lower()
            if result_type == "succeeded" and isinstance(result_payload.get("message"), dict):
                message_body = result_payload["message"]
                executed_query = str(request_item.get("executed_query") or request_item.get("keyword_raw") or "").strip()
                user_query_raw = str(request_item.get("user_query_raw") or request_item.get("keyword_raw") or "").strip()
                internal_body = self._claude_response_to_internal_body(message_body)
                result = self._analysis_result_from_response_body(
                    internal_body,
                    executed_query,
                    config,
                    user_query_raw=user_query_raw,
                    executed_query=executed_query,
                )
                if not result.output_json.get("citations"):
                    result.output_json["citations"] = self._extract_claude_citations(message_body)
                if not result.output_json.get("citation_urls"):
                    result.output_json["citation_urls"] = [
                        str(item.get("url") or "").strip()
                        for item in result.output_json.get("citations") or []
                        if str(item.get("url") or "").strip()
                    ][:8]
                result.web_search_calls = self._claude_web_search_call_count(message_body)
                records.append(
                    BatchImportRecord(
                        custom_id=custom_id,
                        remote_request_id=str(message_body.get("id") or custom_id).strip(),
                        response_status_code=200,
                        result=result,
                    )
                )
                continue
            error_text = str(
                result_payload.get("error", {}).get("message")
                if isinstance(result_payload.get("error"), dict)
                else result_payload.get("message")
            ).strip()
            if not error_text:
                error_text = "Claude Batch 実行結果の取り込みに失敗しました。"
            error_code = result_payload.get("error", {}).get("status_code") if isinstance(result_payload.get("error"), dict) else None
            records.append(
                BatchImportRecord(
                    custom_id=custom_id,
                    remote_request_id=str(line.get("id") or custom_id).strip(),
                    response_status_code=int(error_code) if str(error_code or "").isdigit() else None,
                    result=None,
                    error_text=error_text,
                )
            )
        return records

    def _post_messages_request(self, keyword: str, config: AppConfig) -> dict[str, Any]:
        request_body = self._build_messages_request_body(keyword, config)
        return self._claude_json_request(
            self.ANTHROPIC_MESSAGES_URL,
            method="POST",
            api_key=self._require_anthropic_api_key(config.provider),
            payload=request_body,
        )

    def _build_messages_request_body(self, keyword: str, config: AppConfig) -> dict[str, Any]:
        reasoning_effort = self._resolve_reasoning_effort(config)
        payload = self._build_input_messages(keyword, config, reasoning_effort)[1]["content"][0]["text"]
        return {
            "model": config.model,
            "max_tokens": int(config.max_output_tokens or 1200),
            "system": self._build_analysis_prompt(config),
            "messages": [{"role": "user", "content": payload}],
            "tools": [self._build_claude_web_search_tool(config)],
        }

    def _build_claude_batch_request_items(
        self,
        config: AppConfig,
        execution_requests: list[dict[str, Any]] | None = None,
    ) -> list[BatchRequestItem]:
        items: list[BatchRequestItem] = []
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
                            "url": "/v1/messages",
                            "body": self._build_messages_request_body(keyword, config),
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
                            "url": "/v1/messages",
                            "body": self._build_messages_request_body(keyword, config),
                        },
                    )
                )
        return items

    def _require_anthropic_api_key(self, provider_key: str) -> str:
        api_key = get_provider_api_key(provider_key)
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY が見つかりません。")
        return api_key

    def _claude_json_request(
        self,
        url: str,
        *,
        method: str,
        api_key: str,
        payload: dict[str, Any] | None = None,
        include_batch_beta: bool = False,
    ) -> dict[str, Any]:
        request_payload = None
        if payload is not None:
            request_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "x-api-key": api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
        }
        if include_batch_beta:
            headers["anthropic-beta"] = self.ANTHROPIC_BATCH_BETA
        request = urllib_request.Request(
            url,
            data=request_payload,
            headers=headers,
            method=method,
        )
        try:
            with urllib_request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            error_text = exc.read().decode("utf-8", errors="ignore")
            message = self._extract_http_error_message(error_text) or error_text or str(exc)
            raise RuntimeError(f"Claude request failed ({exc.code}): {message}") from exc
        except urllib_error.URLError as exc:
            raise RuntimeError(f"Claude request failed: {exc.reason}") from exc

    def _claude_batch_results_text(self, batch_job_id: str) -> str:
        request = urllib_request.Request(
            f"{self.ANTHROPIC_BATCHES_URL}/{batch_job_id}/results",
            headers={
                "x-api-key": self._require_anthropic_api_key("claude"),
                "anthropic-version": self.ANTHROPIC_VERSION,
                "anthropic-beta": self.ANTHROPIC_BATCH_BETA,
            },
            method="GET",
        )
        try:
            with urllib_request.urlopen(request, timeout=180) as response:
                return response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            error_text = exc.read().decode("utf-8", errors="ignore")
            message = self._extract_http_error_message(error_text) or error_text or str(exc)
            raise RuntimeError(f"Claude request failed ({exc.code}): {message}") from exc
        except urllib_error.URLError as exc:
            raise RuntimeError(f"Claude request failed: {exc.reason}") from exc

    def _claude_batch_handle_from_api(self, response_body: dict[str, Any]) -> BatchJobHandle:
        request_counts = response_body.get("request_counts") or {}
        processing_count = int(request_counts.get("processing") or 0)
        succeeded_count = int(request_counts.get("succeeded") or 0)
        errored_count = int(request_counts.get("errored") or 0)
        expired_count = int(request_counts.get("expired") or 0)
        canceled_count = int(request_counts.get("canceled") or request_counts.get("cancelled") or 0)
        total_count = processing_count + succeeded_count + errored_count + expired_count + canceled_count
        raw_status = str(response_body.get("processing_status") or "").strip().lower()
        status = self._normalize_claude_batch_status(
            raw_status,
            total_count,
            succeeded_count,
            errored_count,
            expired_count,
            canceled_count,
        )
        results_url = str(response_body.get("results_url") or "").strip()
        output_file_id = results_url if results_url and status in {"completed", "failed", "expired", "cancelled"} else ""
        error_file_id = results_url if results_url and (errored_count or expired_count or canceled_count) else ""
        return BatchJobHandle(
            batch_job_id=str(response_body.get("id") or "").strip(),
            status=status,
            input_file_id="inline_requests",
            endpoint=self.ANTHROPIC_BATCHES_URL,
            completion_window=get_provider_batch_completion_window("claude"),
            output_file_id=output_file_id,
            error_file_id=error_file_id,
            request_counts_total=total_count,
            request_counts_completed=succeeded_count,
            request_counts_failed=errored_count + expired_count + canceled_count,
            raw_batch=response_body,
        )

    def _normalize_claude_batch_status(
        self,
        raw_status: str,
        total_count: int,
        succeeded_count: int,
        errored_count: int,
        expired_count: int,
        canceled_count: int,
    ) -> str:
        if raw_status == "in_progress":
            return "in_progress"
        if raw_status in {"canceling", "cancelling"}:
            return "cancelling"
        if raw_status == "ended":
            if total_count and expired_count >= total_count and succeeded_count == 0 and errored_count == 0:
                return "expired"
            if total_count and canceled_count >= total_count and succeeded_count == 0 and errored_count == 0:
                return "cancelled"
            if total_count and errored_count >= total_count and succeeded_count == 0:
                return "failed"
            return "completed"
        return raw_status or "in_progress"

    def _build_claude_web_search_tool(self, config: AppConfig) -> dict[str, Any]:
        tool: dict[str, Any] = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5,
            "user_location": {
                "type": "approximate",
                "country": config.user_location_country,
                "city": config.user_location_city,
                "region": config.user_location_region,
                "timezone": config.timezone,
            },
        }
        if config.analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
            allowed_domains = self._build_owned_only_domains(config)
            if allowed_domains:
                tool["allowed_domains"] = allowed_domains
        return tool

    def _claude_response_to_internal_body(self, response_body: dict[str, Any]) -> dict[str, Any]:
        content_blocks = response_body.get("content") or []
        output_texts = [
            str(block.get("text") or "").strip()
            for block in content_blocks
            if isinstance(block, dict) and block.get("type") == "text" and str(block.get("text") or "").strip()
        ]
        sources = self._extract_claude_sources(response_body)
        usage_payload = response_body.get("usage") or {}
        usage = {
            "input_tokens": int(usage_payload.get("input_tokens") or 0),
            "output_tokens": int(usage_payload.get("output_tokens") or 0),
            "total_tokens": int(
                (usage_payload.get("input_tokens") or 0)
                + (usage_payload.get("output_tokens") or 0)
                + (usage_payload.get("cache_creation_input_tokens") or 0)
            ),
            "input_tokens_details": {
                "cached_tokens": int(usage_payload.get("cache_read_input_tokens") or 0),
            },
            "server_tool_use": usage_payload.get("server_tool_use") or {},
        }
        output_items: list[dict[str, Any]] = []
        if sources:
            output_items.append(
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": sources,
                    },
                }
            )
        return {
            "output_text": "\n".join(output_texts).strip(),
            "usage": usage,
            "output": output_items,
        }

    def _extract_claude_sources(self, response_body: dict[str, Any]) -> list[dict[str, str]]:
        sources: list[dict[str, str]] = []
        for block in response_body.get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "web_search_tool_result":
                continue
            for item in block.get("content") or []:
                if not isinstance(item, dict) or item.get("type") != "web_search_result":
                    continue
                url = str(item.get("url") or "").strip()
                title = str(item.get("title") or "").strip()
                if url:
                    sources.append({"url": url, "title": title})
        return self._dedupe_url_records(sources)

    def _extract_claude_citations(self, response_body: dict[str, Any]) -> list[dict[str, str]]:
        citations: list[dict[str, str]] = []
        for block in response_body.get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "text":
                continue
            for citation in block.get("citations") or []:
                if not isinstance(citation, dict):
                    continue
                url = str(citation.get("url") or "").strip()
                title = str(citation.get("title") or "").strip()
                if url:
                    citations.append({"url": url, "title": title})
        return self._dedupe_url_records(citations)[:8]

    def _claude_web_search_call_count(self, response_body: dict[str, Any]) -> int:
        usage_payload = response_body.get("usage") or {}
        server_tool_use = usage_payload.get("server_tool_use") or {}
        if server_tool_use:
            return int(server_tool_use.get("web_search_requests") or 0)
        count = 0
        for block in response_body.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "server_tool_use" and block.get("name") == "web_search":
                count += 1
        return count

    def _extract_http_error_message(self, raw_text: str) -> str:
        try:
            payload = json.loads(raw_text)
        except Exception:
            return str(raw_text or "").strip()
        error_payload = payload.get("error") if isinstance(payload, dict) else {}
        if isinstance(error_payload, dict):
            return str(error_payload.get("message") or "").strip()
        return str(raw_text or "").strip()

    def _dedupe_url_records(self, records: list[dict[str, str]]) -> list[dict[str, str]]:
        seen_urls: set[str] = set()
        deduped: list[dict[str, str]] = []
        for record in records:
            url = str(record.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            deduped.append(record)
        return deduped


