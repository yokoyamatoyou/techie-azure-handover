from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from openai import OpenAI

from analysis_lib import dedupe_preserve_order, normalize_domain_host, normalize_text, resolve_prompt_cache_retention, usage_to_dict
from config import (
    ALLOWED_DOMAINS_HARD_NOTE,
    ALLOWED_DOMAINS_SOFT_NOTE,
    ANALYSIS_MODE_OWNED_ONLY,
    AppConfig,
    get_provider_batch_completion_window,
    get_provider_batch_endpoint,
    get_provider_option,
    provider_supports_batch,
    provider_supports_prompt_cache,
)

ANALYSIS_SYSTEM_PROMPT = """
You are an AI visibility analyst for a local LLMO proof of concept.

You must evaluate a single keyword or prompt by using web search inside the Responses API and return a single JSON object.

The business goal is to understand whether a brand or target domain is visible in AI-grounded answer generation for a given prompt. The output is used in a dashboard, so it must be concise, stable, and machine-readable.

You are not writing a marketing article. You are producing a measurement artifact.

Core evaluation objectives:
1. Determine whether the target domain appears directly in the search-grounded answer context or source list.
2. Determine whether any brand terms appear in the answer context or source list.
3. Determine whether competitors appear in the answer context or source list.
4. Produce a short executive verdict that tells a stakeholder what the likely AI answer direction is.
5. Produce a visibility score from 0 to 100.
6. Produce recommended actions that are concrete and short.
7. Be conservative. If uncertain, say uncertain rather than inventing confidence.

Scoring rubric:
- 90 to 100: target domain is clearly present in sources and the answer direction strongly favors the target brand or owned content.
- 70 to 89: target domain or brand is visible and relevant, but not dominant.
- 50 to 69: weak or partial visibility, indirect brand presence, or mixed source position.
- 20 to 49: competitors or third-party sites dominate and the target is marginal.
- 0 to 19: no meaningful visibility for the target.

Decision rules:
- target_domain_hit is true only if the target domain appears in a cited or discovered source URL, or the answer explicitly references the target domain.
- brand_mention_hit is true only if any supplied brand term appears in the answer direction, a cited source title, or a source URL.
- competitor_mentions must be a list of the competitor terms that appear relevant in the answer direction or sources. Do not fabricate names not provided by the user.
- citation_urls should prefer URLs found in actual search sources.

Output rules:
- Return JSON only.
- Do not wrap the JSON in markdown.
- Do not include prose outside the JSON object.
- Keep the snapshot under 320 characters.
- answer_snapshot must begin with one of these Japanese verdicts:
  「自社が優勢」「競合と拮抗」「競合が優勢」「第三者が優勢」
- Put a full-width Japanese colon `：` immediately after that verdict label.
- answer_text must be a fuller Japanese answer for business review, not just the verdict label.
- Keep answer_text under 900 characters and write it as plain prose, not bullets.
- Keep each recommended action under 100 characters.
- recommended_actions must contain exactly 3 items.
- confidence must be one of: low, medium, high.
- answer_snapshot and recommended_actions must be written in plain Japanese for non-technical business users.
- answer_text must also be written in plain Japanese for non-technical business users.
- Avoid unnecessary English. Product names and service names may remain in their original spelling.
- recommended_actions should sound like weekly marketing actions, not internal analyst notes.
- Avoid jargon such as SEO, LLMO, optimization, prompt engineering unless absolutely necessary.

Required JSON schema:
{
  "keyword_raw": "string",
  "keyword_norm": "string",
  "answer_snapshot": "string",
  "answer_text": "string",
  "visibility_score": 0,
  "target_domain_hit": true,
  "brand_mention_hit": true,
  "competitor_mentions": ["string"],
  "confidence": "low",
  "recommended_actions": ["string", "string", "string"],
  "citations": [{"url": "https://example.com", "title": "Example"}],
  "citation_urls": ["https://example.com"]
}

Measurement reminders:
- Prefer exact URLs and real sources over intuition.
- If the search result is noisy, reduce confidence instead of overstating certainty.
- If the keyword looks transactional or comparative, call that out in the snapshot.
- If the keyword looks educational or exploratory, call that out in the snapshot.
- If no citation is available, return an empty list for citation_urls.
- If no citation is available, return an empty list for citations as well.
- Preserve the keyword in both raw and normalized forms.

Extended measurement checklist:
- Read the task as a visibility measurement problem, not as a content generation problem.
- Favor precision over breadth.
- Prefer direct evidence from source titles and source URLs.
- If the target domain is visible but weak, keep the score in the middle range.
- If the target domain is absent and competitors dominate, keep the score low.
- If no competitor list is supplied, return an empty competitor list rather than inventing one.
- If the prompt appears navigational or branded, note that the result may be biased toward owned assets.
- If the prompt appears informational, note whether third-party review sites dominate.
- If the prompt appears commercial, note whether comparison or pricing pages dominate.
- If the prompt appears local, note the local angle only when the web search actually shows it.
- Do not guess at brand ownership from partial string overlap when the evidence is weak.
- Avoid generic action items such as "improve SEO" or "make better content".
- If competitor terms are supplied and appear, explicitly say whether the target is ahead, tied, or behind them.
- Recommended actions should map to observed gaps such as comparison content, pricing pages, FAQ coverage, or stronger evidence pages.
- If the same domain appears multiple times in sources, that can justify a stronger visibility score.
- If only aggregator or marketplace pages appear, do not award a high target-domain score.
- If the target domain appears only in low-signal results, keep confidence lower.
- Keep the answer snapshot oriented toward a stakeholder reading a dashboard card.
- Keep actions concrete enough to discuss in a weekly growth or content review.
- Keep the JSON compact enough for storage in a local SQLite row.
- The output must remain stable across repeated runs of similar prompts.

Stable scoring examples:
- Example A: owned domain appears in multiple citations, brand terms appear in the answer direction, and the query is commercial -> likely 80+.
- Example B: owned domain appears once but third-party reviews dominate -> likely 55 to 75 depending on prominence.
- Example C: no owned domain, no brand mention, competitor review pages dominate -> likely 10 to 40.
- Example D: educational query with mixed neutral sources and one owned citation -> likely 45 to 65.
- Example E: branded query where owned domain is present but not cited -> likely 50 to 70 with medium confidence.

Action template examples:
- Publish a tighter comparison page for this prompt cluster.
- Strengthen pricing or proof content for commercial variants.
- Expand FAQ coverage on the owned domain for this topic.
- Create a citation-friendly explainer page with clear headings.
- Improve evidence and examples on the landing page most aligned with this query.
- Add an explicit page for use case, buyer type, or workflow language seen in the query.

Forbidden behaviors:
- Do not output markdown.
- Do not include code fences.
- Do not include commentary outside the JSON object.
- Do not fabricate URLs.
- Do not invent competitors not present in the provided list.
- Do not claim certainty without source support.
- Do not return more or fewer than 3 recommended actions.

The same static instructions are intentionally reused across calls for prompt caching.
The dashboard tracks cached tokens, cost, and repetition behavior, so consistency matters.
The JSON structure must remain identical across requests.
""".strip()


@dataclass
class SourceItem:
    url: str
    title: str
    kind: str


@dataclass
class AnalysisResult:
    keyword_raw: str
    keyword_norm: str
    output_text: str
    output_json: dict[str, Any]
    usage: dict[str, Any]
    web_search_calls: int
    sources: list[SourceItem]
    estimated_cost_usd: float = 0.0


@dataclass
class BatchRequestItem:
    custom_id: str
    keyword_raw: str
    keyword_norm: str
    iteration_index: int
    request_line: dict[str, Any]


@dataclass
class BatchJobHandle:
    batch_job_id: str
    status: str
    input_file_id: str
    endpoint: str
    completion_window: str
    output_file_id: str = ""
    error_file_id: str = ""
    request_counts_total: int = 0
    request_counts_completed: int = 0
    request_counts_failed: int = 0
    raw_batch: dict[str, Any] | None = None


@dataclass
class BatchImportRecord:
    custom_id: str
    remote_request_id: str
    response_status_code: int | None
    result: AnalysisResult | None
    error_text: str = ""


class ProviderClient(Protocol):
    def analyze_keyword(self, keyword: str, config: AppConfig) -> AnalysisResult:
        ...

    def submit_batch(
        self,
        config: AppConfig,
        execution_requests: list[dict[str, Any]] | None = None,
    ) -> tuple[BatchJobHandle, list[BatchRequestItem]]:
        ...

    def retrieve_batch(self, batch_job_id: str) -> BatchJobHandle:
        ...

    def import_batch_results(
        self,
        batch: BatchJobHandle,
        config: AppConfig,
        request_items: dict[str, dict[str, Any]],
    ) -> list[BatchImportRecord]:
        ...


class NotImplementedProviderClient:
    def __init__(self, provider_key: str) -> None:
        self.provider_key = provider_key

    def analyze_keyword(self, keyword: str, config: AppConfig) -> AnalysisResult:
        raise NotImplementedError(
            f"provider '{self.provider_key}' is not wired yet. "
            "OpenAI is the only live provider in this PoC."
        )

    def submit_batch(
        self,
        config: AppConfig,
        execution_requests: list[dict[str, Any]] | None = None,
    ) -> tuple[BatchJobHandle, list[BatchRequestItem]]:
        raise NotImplementedError(
            f"provider '{self.provider_key}' does not support Batch mode in this PoC."
        )

    def retrieve_batch(self, batch_job_id: str) -> BatchJobHandle:
        raise NotImplementedError(
            f"provider '{self.provider_key}' does not support Batch mode in this PoC."
        )

    def import_batch_results(
        self,
        batch: BatchJobHandle,
        config: AppConfig,
        request_items: dict[str, dict[str, Any]],
    ) -> list[BatchImportRecord]:
        raise NotImplementedError(
            f"provider '{self.provider_key}' does not support Batch mode in this PoC."
        )


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
        if not endpoint or not completion_window or not provider_supports_batch(config.provider):
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
        keyword_norm = normalize_text(keyword)
        owned_only_domains = self._build_owned_only_domains(config)
        allowed_domains_mode = "hard_filter" if config.analysis_mode == ANALYSIS_MODE_OWNED_ONLY else "soft_preference_only"
        runtime_note = ALLOWED_DOMAINS_HARD_NOTE if allowed_domains_mode == "hard_filter" else ALLOWED_DOMAINS_SOFT_NOTE
        payload = {
            "keyword_raw": keyword,
            "keyword_norm": keyword_norm,
            "analysis_mode": config.analysis_mode,
            "target_domain": config.target_domain,
            "brand_terms": config.brand_terms,
            "competitor_terms": config.competitor_terms,
            "allowed_domains": config.allowed_domains,
            "owned_only_domains": owned_only_domains,
            "allowed_domains_mode": allowed_domains_mode,
            "allowed_domains_runtime_note": runtime_note,
            "reasoning_effort_requested": config.reasoning_effort,
            "reasoning_effort_effective": reasoning_effort,
            "prompt_cache_retention_requested": config.prompt_cache_retention,
            "prompt_cache_retention_effective": (
                resolve_prompt_cache_retention(config.model, config.prompt_cache_retention)
                if provider_supports_prompt_cache(config.provider)
                else "in_memory"
            ),
            "instruction": (
                "Search the web and evaluate AI visibility for this keyword. "
                "Return the required JSON only. "
                + (
                    "This run is an owned-only audit. Search only within the owned allow-list and judge whether the owned site alone can answer the question."
                    if allowed_domains_mode == "hard_filter"
                    else "If allowed_domains is present, treat it as a soft preference only. Prioritize evidence from those domains when useful, but do not pretend it is a hard search filter."
                )
            ),
        }
        return [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": ANALYSIS_SYSTEM_PROMPT}],
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
        effective_prompt_cache_retention = (
            resolve_prompt_cache_retention(config.model, config.prompt_cache_retention)
            if provider_supports_prompt_cache(config.provider)
            else "in_memory"
        )
        resolved_executed_query = normalize_text(executed_query or keyword)
        resolved_user_query_raw = normalize_text(user_query_raw or resolved_executed_query)
        return {
            "question": resolved_executed_query,
            "user_query_raw": resolved_user_query_raw,
            "executed_query": resolved_executed_query,
            "analysis_mode": config.analysis_mode,
            "target_domain": config.target_domain,
            "brand_terms": config.brand_terms,
            "competitor_terms": config.competitor_terms,
            "allowed_domains": config.allowed_domains,
            "owned_only_domains": self._build_owned_only_domains(config),
            "model": config.model,
            "reasoning_effort": reasoning_effort,
            "search_context_size": config.search_context_size,
            "prompt_cache_retention_requested": config.prompt_cache_retention,
            "prompt_cache_retention_effective": effective_prompt_cache_retention,
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
            pass
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
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".jsonl", delete=False)
        try:
            for item in request_items:
                handle.write(json.dumps(item.request_line, ensure_ascii=False))
                handle.write("\n")
        finally:
            handle.close()
        return Path(handle.name)

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


PROVIDER_CLIENT_FACTORIES: dict[str, type[ProviderClient]] = {
    "openai": LLMOClient,
}


def build_provider_client(provider_key: str) -> ProviderClient:
    provider = get_provider_option(provider_key)
    client_factory = PROVIDER_CLIENT_FACTORIES.get(provider.key)
    if client_factory is not None and provider.supports_live_requests:
        return client_factory()
    return NotImplementedProviderClient(provider.key)
