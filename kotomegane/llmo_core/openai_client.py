from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from openai import OpenAI

from analysis_lib import (
    build_prompt_injection_signal,
    dedupe_preserve_order,
    normalize_domain_host,
    normalize_text,
    resolve_prompt_cache_retention,
    stabilize_analysis_output,
    usage_to_dict,
)
from config import (
    ALLOWED_DOMAINS_HARD_NOTE,
    ALLOWED_DOMAINS_SOFT_NOTE,
    ANALYSIS_MODE_OWNED_ONLY,
    AppConfig,
    get_provider_batch_completion_window,
    get_provider_batch_endpoint,
    provider_supports_prompt_cache,
    resolve_provider_cache_policy,
)
from run_policy import resolve_run_policy

from llmo_core.models import AnalysisResult, BatchImportRecord, BatchJobHandle, BatchRequestItem, SourceItem
from llmo_core.prompts import build_analysis_system_prompt

class LLMOClient:
    def __init__(self) -> None:
        self.client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self.client is None:
            self.client = OpenAI()
        return self.client

    def analyze_keyword(self, keyword: str, config: AppConfig) -> AnalysisResult:
        response = self._get_client().responses.create(**self._build_responses_request_body(keyword, config))
        return self._analysis_result_from_response(response, keyword, config)

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
        request_items = self.build_batch_request_items(config, execution_requests=execution_requests)
        batch_input_path = self._write_batch_input_file(request_items)
        try:
            with batch_input_path.open("rb") as handle:
                input_file = self._get_client().files.create(file=handle, purpose="batch")
            self._get_client().files.wait_for_processing(input_file.id, poll_interval=2.0, max_wait_seconds=300)
            batch = self._get_client().batches.create(
                input_file_id=input_file.id,
                endpoint=endpoint,
                completion_window=completion_window,
                metadata=self._build_batch_metadata(config, len(request_items)),
            )
        finally:
            batch_input_path.unlink(missing_ok=True)

        return self._batch_handle_from_api(batch), request_items

    def retrieve_batch(self, batch_job_id: str) -> BatchJobHandle:
        batch = self._get_client().batches.retrieve(batch_job_id)
        return self._batch_handle_from_api(batch)

    def import_batch_results(
        self,
        batch: BatchJobHandle,
        config: AppConfig,
        request_items: dict[str, dict[str, Any]],
    ) -> list[BatchImportRecord]:
        records: list[BatchImportRecord] = []
        seen_custom_ids: set[str] = set()
        if batch.output_file_id:
            output_text = self._get_client().files.retrieve_content(batch.output_file_id)
            for line in self._parse_jsonl(output_text):
                record = self._parse_batch_result_line(line, config, request_items)
                if record is None:
                    continue
                records.append(record)
                seen_custom_ids.add(record.custom_id)
        if batch.error_file_id:
            error_text = self._get_client().files.retrieve_content(batch.error_file_id)
            for line in self._parse_jsonl(error_text):
                custom_id = str(line.get("custom_id") or "").strip()
                if not custom_id or custom_id in seen_custom_ids:
                    continue
                record = self._parse_batch_result_line(line, config, request_items)
                if record is None:
                    continue
                records.append(record)
                seen_custom_ids.add(record.custom_id)
        return records

    def build_batch_request_items(
        self,
        config: AppConfig,
        execution_requests: list[dict[str, Any]] | None = None,
    ) -> list[BatchRequestItem]:
        items: list[BatchRequestItem] = []
        endpoint = get_provider_batch_endpoint(config.provider)
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
                            "body": self._build_responses_request_body(
                                keyword,
                                config,
                                include_prompt_cache=False,
                            ),
                        },
                    )
                )
            return items

        for keyword_index, keyword in enumerate(config.keywords, start=1):
            for iteration_index in range(1, config.repeat_count + 1):
                keyword_norm = normalize_text(keyword)
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
                            "body": self._build_responses_request_body(
                                keyword,
                                config,
                                include_prompt_cache=False,
                            ),
                        },
                    )
                )
        return items

    def _build_responses_request_body(
        self,
        keyword: str,
        config: AppConfig,
        *,
        include_prompt_cache: bool = True,
    ) -> dict[str, Any]:
        reasoning_effort = self._resolve_reasoning_effort(config)
        supports_prompt_cache = provider_supports_prompt_cache(config.provider)
        effective_prompt_cache_retention = (
            resolve_prompt_cache_retention(config.model, config.prompt_cache_retention)
            if supports_prompt_cache
            else "in_memory"
        )
        body: dict[str, Any] = {
            "model": config.model,
            "reasoning": {"effort": reasoning_effort},
            "tools": [self._build_web_search_tool(config)],
            "tool_choice": "required",
            "include": ["web_search_call.action.sources"],
            "input": self._build_input_messages(keyword, config, reasoning_effort),
            "max_output_tokens": config.max_output_tokens,
        }
        if include_prompt_cache and supports_prompt_cache:
            body["prompt_cache_key"] = config.prompt_cache_key
            body["prompt_cache_retention"] = effective_prompt_cache_retention
        return body

    def _build_input_messages(
        self,
        keyword: str,
        config: AppConfig,
        reasoning_effort: str,
    ) -> list[dict[str, Any]]:
        include_owned_context = self._llm_input_includes_owned_context(config)
        keyword_norm = normalize_text(keyword)
        owned_only_domains = self._build_owned_only_domains(config)
        allowed_domains_mode = "hard_filter" if config.analysis_mode == ANALYSIS_MODE_OWNED_ONLY else "soft_preference_only"
        runtime_note = ALLOWED_DOMAINS_HARD_NOTE if allowed_domains_mode == "hard_filter" else ALLOWED_DOMAINS_SOFT_NOTE
        cache_policy = resolve_provider_cache_policy(config.provider, config.model, config.prompt_cache_retention)
        payload = {
            "keyword_raw": keyword,
            "keyword_norm": keyword_norm,
            "analysis_mode": config.analysis_mode,
            "llm_input_scope": "targeted_audit" if include_owned_context else "query_only",
            "reasoning_effort_requested": config.reasoning_effort,
            "reasoning_effort_effective": reasoning_effort,
            "prompt_cache_retention_requested": config.prompt_cache_retention,
            "prompt_cache_retention_effective": cache_policy["effective"],
            "prompt_cache_policy_label": cache_policy["display_label"],
            "prompt_cache_policy_note": cache_policy["note"],
            "instruction": self._build_runtime_instruction(
                include_owned_context=include_owned_context,
                allowed_domains_mode=allowed_domains_mode,
            ),
        }
        if include_owned_context:
            payload.update(
                {
                    "target_domain": config.target_domain,
                    "brand_terms": config.brand_terms,
                    "market_context_terms": config.market_context_terms,
                    "competitor_terms": config.competitor_terms,
                    "allowed_domains": config.allowed_domains,
                    "owned_only_domains": owned_only_domains,
                    "allowed_domains_mode": allowed_domains_mode,
                    "allowed_domains_runtime_note": runtime_note,
                }
            )
        return [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": self._build_analysis_prompt(config)}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(payload, ensure_ascii=False),
                    }
                ],
            },
        ]

    def _build_web_search_tool(self, config: AppConfig) -> dict[str, Any]:
        tool: dict[str, Any] = {
            "type": "web_search",
            "search_context_size": config.search_context_size,
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
                tool["filters"] = {"allowed_domains": allowed_domains}
        return tool

    def _resolve_reasoning_effort(self, config: AppConfig) -> str:
        return "low" if config.reasoning_effort == "minimal" else config.reasoning_effort

    def _llm_input_includes_owned_context(self, config: AppConfig) -> bool:
        return config.analysis_mode == ANALYSIS_MODE_OWNED_ONLY

    def _build_analysis_prompt(self, config: AppConfig) -> str:
        return build_analysis_system_prompt(include_owned_context=self._llm_input_includes_owned_context(config))

    def _build_runtime_instruction(self, *, include_owned_context: bool, allowed_domains_mode: str) -> str:
        if include_owned_context:
            return (
                "Search the web and evaluate AI visibility for this keyword. "
                "Return the required JSON only. "
                + (
                    "This run is an owned-only audit. Search only within the owned allow-list and judge whether the owned site alone can answer the question."
                    if allowed_domains_mode == "hard_filter"
                    else "If allowed_domains is present, treat it as a soft preference only. Prioritize evidence from those domains when useful, but do not pretend it is a hard search filter."
                )
            )
        return (
            "Search the web and summarize the likely answer direction for this keyword. "
            "Treat this as a market observation from the query alone. "
            "Do not assume any owned site, target brand, competitor list, or supplemental business hint. "
            "Return the required JSON only."
        )

    def _analysis_result_from_response(
        self,
        response: Any,
        keyword: str,
        config: AppConfig,
    ) -> AnalysisResult:
        body = {
            "output_text": (getattr(response, "output_text", None) or "").strip(),
            "usage": usage_to_dict(getattr(response, "usage", None)),
            "output": self._model_output_to_plain_list(getattr(response, "output", []) or []),
        }
        return self._analysis_result_from_response_body(
            body,
            keyword,
            config,
            user_query_raw=keyword,
            executed_query=keyword,
        )

    def _analysis_result_from_response_body(
        self,
        body: dict[str, Any],
        keyword: str,
        config: AppConfig,
        *,
        user_query_raw: str | None = None,
        executed_query: str | None = None,
    ) -> AnalysisResult:
        keyword_norm = normalize_text(keyword)
        reasoning_effort = self._resolve_reasoning_effort(config)
        output_text = self._extract_output_text(body)
        output_json = self._parse_json_output(output_text, keyword, keyword_norm)
        output_json = stabilize_analysis_output(output_json, keyword, keyword_norm)
        resolved_user_query_raw = normalize_text(user_query_raw or keyword)
        resolved_executed_query = normalize_text(executed_query or keyword)
        output_json["analysis_context"] = self._build_analysis_context(
            resolved_executed_query,
            config,
            reasoning_effort,
            user_query_raw=resolved_user_query_raw,
            executed_query=resolved_executed_query,
        )
        sources = self._extract_sources_from_output_items(body.get("output") or [])
        security_signal = build_prompt_injection_signal(
            [
                *[str(source.title or "") for source in sources],
                *[str(source.url or "") for source in sources],
            ]
        )
        if security_signal["suspicious_prompt_injection"]:
            output_json["confidence"] = "low"
        output_json["security_signals"] = {
            **security_signal,
            "low_trust_source_detected": any(
                any(host in str(source.url or "").lower() for host in ["reddit.com", "x.com", "pastebin.com", "gist.github.com"])
                for source in sources
            ),
        }
        output_json["security_review_required"] = bool(
            output_json["security_signals"].get("suspicious_prompt_injection")
            or output_json["security_signals"].get("low_trust_source_detected")
        )
        usage = usage_to_dict(body.get("usage"))
        web_search_calls = max(1, self._count_web_search_calls_from_output_items(body.get("output") or []))
        citation_urls = output_json.get("citation_urls") or []
        citations = output_json.get("citations") or []
        if citations and not citation_urls:
            output_json["citation_urls"] = [str(item.get("url") or "") for item in citations if str(item.get("url") or "").strip()][:8]
        if not output_json.get("answer_text"):
            output_json["answer_text"] = output_json.get("answer_snapshot") or output_text
        return AnalysisResult(
            keyword_raw=keyword,
            keyword_norm=keyword_norm,
            output_text=output_text,
            output_json=output_json,
            usage=usage,
            web_search_calls=web_search_calls,
            sources=sources,
        )

    def _build_analysis_context(
        self,
        keyword: str,
        config: AppConfig,
        reasoning_effort: str,
        *,
        user_query_raw: str | None = None,
        executed_query: str | None = None,
    ) -> dict[str, Any]:
        cache_policy = resolve_provider_cache_policy(config.provider, config.model, config.prompt_cache_retention)
        effective_prompt_cache_retention = cache_policy["effective"]
        resolved_executed_query = normalize_text(executed_query or keyword)
        resolved_user_query_raw = normalize_text(user_query_raw or resolved_executed_query)
        return {
            "question": resolved_executed_query,
            "user_query_raw": resolved_user_query_raw,
            "executed_query": resolved_executed_query,
            "analysis_mode": config.analysis_mode,
            "llm_input_scope": "targeted_audit" if self._llm_input_includes_owned_context(config) else "query_only",
            "target_domain": config.target_domain,
            "brand_terms": config.brand_terms,
            "market_context_terms": config.market_context_terms,
            "competitor_terms": config.competitor_terms,
            "allowed_domains": config.allowed_domains,
            "owned_only_domains": self._build_owned_only_domains(config),
            "model": config.model,
            "reasoning_effort": reasoning_effort,
            "search_context_size": config.search_context_size,
            "prompt_cache_retention_requested": config.prompt_cache_retention,
            "prompt_cache_retention_effective": effective_prompt_cache_retention,
            "prompt_cache_policy_label": cache_policy["display_label"],
            "prompt_cache_policy_note": cache_policy["note"],
        }

    def _parse_json_output(
        self,
        output_text: str,
        keyword_raw: str,
        keyword_norm: str,
    ) -> dict[str, Any]:
        try:
            parsed = json.loads(output_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            extracted = self._extract_json_object_candidate(output_text)
            if extracted is not None:
                return extracted
            repaired = self._repair_truncated_json_output(output_text)
            if repaired is not None:
                return repaired
        return {
            "keyword_raw": keyword_raw,
            "keyword_norm": keyword_norm,
            "answer_snapshot": "応答を読み取れませんでした。生のレスポンスを確認してください。",
            "answer_text": "応答本文を読み取れませんでした。生返答と引用元を確認してから再実行してください。",
            "visibility_score": 0,
            "target_domain_hit": False,
            "brand_mention_hit": False,
            "competitor_mentions": [],
            "confidence": "low",
            "recommended_actions": [
                "生のレスポンスを確認する",
                "質問を短くするか条件を絞る",
                "API 応答形式を確認して再実行する",
            ],
            "citations": [],
            "citation_urls": [],
        }

    def _repair_truncated_json_output(self, output_text: str) -> dict[str, Any] | None:
        normalized = str(output_text or "").strip()
        if not normalized.startswith("{"):
            return None
        for cut_key in ('"citation_urls"', '"citations"'):
            cut_index = normalized.find(cut_key)
            if cut_index == -1:
                continue
            prefix = normalized[:cut_index].rstrip().rstrip(",")
            candidate = prefix + "}"
            try:
                parsed = json.loads(candidate)
            except Exception:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    def _extract_json_object_candidate(self, output_text: str) -> dict[str, Any] | None:
        text = str(output_text or "").strip()
        start_index = text.find("{")
        if start_index < 0:
            return None
        depth = 0
        in_string = False
        escape = False
        for index in range(start_index, len(text)):
            char = text[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start_index : index + 1]
                    try:
                        parsed = json.loads(candidate)
                    except Exception:
                        return None
                    return parsed if isinstance(parsed, dict) else None
        return None

    def _extract_output_text(self, body: dict[str, Any]) -> str:
        output_text = str(body.get("output_text") or "").strip()
        if output_text:
            return output_text
        texts: list[str] = []
        for item in body.get("output") or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    continue
                if content.get("type") in {"output_text", "text"}:
                    text = str(content.get("text") or "").strip()
                    if text:
                        texts.append(text)
        return "\n".join(texts).strip()

    def _extract_sources_from_output_items(self, output_items: list[Any]) -> list[SourceItem]:
        sources: list[SourceItem] = []
        for item in output_items:
            item_dict = self._item_to_plain_dict(item)
            item_type = item_dict.get("type")
            if item_type not in {"web_search_call", "web_search_preview_call"}:
                continue
            action = item_dict.get("action") or {}
            raw_sources = action.get("sources") or []
            for source in raw_sources:
                source_dict = self._item_to_plain_dict(source)
                sources.append(
                    SourceItem(
                        url=str(source_dict.get("url") or ""),
                        title=str(source_dict.get("title") or ""),
                        kind="source",
                    )
                )
        return sources

    def _count_web_search_calls_from_output_items(self, output_items: list[Any]) -> int:
        count = 0
        for item in output_items:
            item_type = self._item_to_plain_dict(item).get("type")
            if item_type in {"web_search_call", "web_search_preview_call"}:
                count += 1
        return count

    def _build_batch_custom_id(self, keyword: str, iteration_index: int, keyword_index: int) -> str:
        keyword_fragment = re.sub(r"\s+", "-", normalize_text(keyword))[:48]
        keyword_fragment = re.sub(r"[^\w\-ぁ-んァ-ヶ一-龠ー]", "-", keyword_fragment, flags=re.UNICODE)
        keyword_fragment = re.sub(r"-{2,}", "-", keyword_fragment).strip("-") or f"keyword-{keyword_index:03d}"
        return f"iter-{iteration_index:03d}__kw-{keyword_index:03d}__{keyword_fragment}"

    def _build_batch_metadata(self, config: AppConfig, request_count: int) -> dict[str, str]:
        return {
            "app": "kotomegane",
            "mode": "batch",
            "analysis_mode": config.analysis_mode[:32],
            "model": config.model[:64],
            "request_count": str(request_count),
            "repeat_count": str(config.repeat_count),
        }

    def _build_owned_only_domains(self, config: AppConfig) -> list[str]:
        domains = [normalize_domain_host(config.target_domain), *[normalize_domain_host(item) for item in config.allowed_domains]]
        return dedupe_preserve_order([domain for domain in domains if domain])

    def _write_batch_input_file(self, request_items: list[BatchRequestItem]) -> Path:
        fd, raw_path = tempfile.mkstemp(suffix=".jsonl", text=True)
        path = Path(raw_path)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for item in request_items:
                    handle.write(json.dumps(item.request_line, ensure_ascii=False))
                    handle.write("\n")
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return path

    def _batch_handle_from_api(self, batch: Any) -> BatchJobHandle:
        request_counts = getattr(batch, "request_counts", None)
        if request_counts is None:
            request_count_total = 0
            request_count_completed = 0
            request_count_failed = 0
        else:
            request_count_total = int(getattr(request_counts, "total", 0) or 0)
            request_count_completed = int(getattr(request_counts, "completed", 0) or 0)
            request_count_failed = int(getattr(request_counts, "failed", 0) or 0)
        raw_batch = batch.to_dict() if hasattr(batch, "to_dict") else {}
        return BatchJobHandle(
            batch_job_id=str(getattr(batch, "id", "") or ""),
            status=str(getattr(batch, "status", "") or ""),
            input_file_id=str(getattr(batch, "input_file_id", "") or ""),
            endpoint=str(getattr(batch, "endpoint", "") or ""),
            completion_window=str(getattr(batch, "completion_window", "") or ""),
            output_file_id=str(getattr(batch, "output_file_id", "") or ""),
            error_file_id=str(getattr(batch, "error_file_id", "") or ""),
            request_counts_total=request_count_total,
            request_counts_completed=request_count_completed,
            request_counts_failed=request_count_failed,
            raw_batch=raw_batch if isinstance(raw_batch, dict) else {},
        )

    def _parse_jsonl(self, raw_text: str) -> list[dict[str, Any]]:
        lines: list[dict[str, Any]] = []
        for raw_line in (raw_text or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except Exception:
                continue
            if isinstance(parsed, dict):
                lines.append(parsed)
        return lines

    def _parse_batch_result_line(
        self,
        line: dict[str, Any],
        config: AppConfig,
        request_items: dict[str, dict[str, Any]],
    ) -> BatchImportRecord | None:
        custom_id = str(line.get("custom_id") or "").strip()
        if not custom_id:
            return None
        request_item = request_items.get(custom_id)
        if request_item is None:
            return BatchImportRecord(
                custom_id=custom_id,
                remote_request_id="",
                response_status_code=None,
                result=None,
                error_text="custom_id に対応するローカルのBatch項目が見つかりません。",
            )

        response = line.get("response") or {}
        error = line.get("error") or {}
        status_code = response.get("status_code")
        request_id = str(response.get("request_id") or line.get("id") or "").strip()
        if status_code and 200 <= int(status_code) < 300 and isinstance(response.get("body"), dict):
            executed_query = str(request_item.get("executed_query") or request_item.get("keyword_raw") or "").strip()
            user_query_raw = str(request_item.get("user_query_raw") or request_item.get("keyword_raw") or "").strip()
            result = self._analysis_result_from_response_body(
                response["body"],
                executed_query,
                config,
                user_query_raw=user_query_raw,
                executed_query=executed_query,
            )
            return BatchImportRecord(
                custom_id=custom_id,
                remote_request_id=request_id,
                response_status_code=int(status_code),
                result=result,
            )

        error_message = str(error.get("message") or "").strip()
        if not error_message and isinstance(response.get("body"), dict):
            error_body = response["body"]
            error_message = str(
                (
                    (error_body.get("error") or {}).get("message")
                    if isinstance(error_body.get("error"), dict)
                    else error_body.get("message")
                )
                or ""
            ).strip()
        if not error_message:
            error_message = "Batch 実行結果の取り込みに失敗しました。"
        return BatchImportRecord(
            custom_id=custom_id,
            remote_request_id=request_id,
            response_status_code=int(status_code) if status_code else None,
            result=None,
            error_text=error_message,
        )

    def _model_output_to_plain_list(self, output_items: list[Any]) -> list[dict[str, Any]]:
        return [self._item_to_plain_dict(item) for item in output_items]

    def _item_to_plain_dict(self, item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return item
        if item is None:
            return {}
        if hasattr(item, "to_dict"):
            value = item.to_dict()
            return value if isinstance(value, dict) else {}
        if hasattr(item, "model_dump"):
            value = item.model_dump()
            return value if isinstance(value, dict) else {}
        result: dict[str, Any] = {}
        for name in ("type", "action", "content", "url", "title"):
            if hasattr(item, name):
                result[name] = getattr(item, name)
        return result


