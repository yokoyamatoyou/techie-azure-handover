from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from analysis_lib import (
    build_expansion_signature,
    dedupe_preserve_order,
    normalize_query_text,
    normalize_text,
    should_shorten_query,
)
from config import AppConfig, get_provider_option, get_provider_total_question_budget

DEFAULT_QUERY_EXPANSION_SUFFIX_RULES: dict[str, list[tuple[str, list[str]]]] = {
    "business_ja": [
        ("比較 違い", ["比較", "違い", "vs", "versus", "おすすめ", "代替"]),
        ("料金 月額 初期費用", ["料金", "価格", "費用", "相場", "プラン", "月額"]),
        ("導入事例 実績", ["事例", "導入", "実績", "成功例", "レビュー"]),
        ("FAQ 導入前の疑問", ["faq", "よくある質問", "とは", "疑問", "できますか"]),
        ("サポート 運用体制", ["サポート", "運用", "体制", "保守"]),
        ("評判 口コミ", ["評判", "口コミ", "イメージ"]),
        ("導入前の不安", ["不安", "失敗", "注意点"]),
        ("使い方 導入手順", ["使い方", "方法", "手順", "howto"]),
    ]
}

QUERY_PLANNING_SYSTEM_PROMPT = """
You create an internal execution plan for a single Japanese business search question.

Return JSON only. No markdown.

Goals:
1. If the original Japanese question exceeds 50 Japanese characters, optionally shorten it for internal measurement.
2. Never remove these kinds of details when they exist: brand names, competitor names, region, pricing conditions, target audience, comparison axis.
3. Generate up to 4 additional relevant derived questions.
4. Total queries must be at most 5 including the base query.
5. Keep the original user question unchanged outside this internal plan.

Expansion rules:
- Prefer relevant variants such as comparison, pricing, FAQ, case study.
- If those axes are unnatural, use reputation/image, adoption anxiety, or how-to.
- Do not force all four axes.
- Avoid near-duplicate questions.

Output schema:
{
  "short_query": "string",
  "query_was_shortened": true,
  "shortening_note": "string",
  "expansions": ["string", "string"]
}

Rules:
- short_query must be the internal base query. If shortening is unnecessary, keep it equal to the original.
- If must_shorten is true, short_query must be meaningfully shorter than the original while preserving key constraints.
- Prefer short_query within about 40 Japanese characters when possible.
- query_was_shortened must be true only when the base query is materially shortened.
- shortening_note must briefly say what was preserved and stay under 80 Japanese characters.
- expansions must exclude the base query itself. Return at most 4 items.
- Each expansion should be a natural search query, not a sentence, and usually stay under 45 Japanese characters.
""".strip()


@dataclass
class QueryPlanSpec:
    user_query_raw: str
    user_query_short: str
    query_was_shortened: bool
    shortening_note: str
    expanded_queries: list[str]
    expansion_mode: str
    expansion_signature: str
    reused_previous: bool = False


@dataclass
class ExecutionJob:
    query_plan_id: str
    user_query_raw: str
    executed_query: str
    executed_query_index: int


@dataclass
class ExecutionRequest:
    query_plan_id: str
    user_query_raw: str
    executed_query: str
    executed_query_index: int
    iteration_index: int


@dataclass
class ExecutionPlan:
    jobs: list[ExecutionJob]
    requests: list[ExecutionRequest]
    total_unique_queries: int
    total_request_count: int
    total_question_budget: int
    execution_order: str


class QueryPlanner:
    def __init__(self) -> None:
        self._client: OpenAI | None = None

    def prepare_query_plan(
        self,
        user_query: str,
        config: AppConfig,
        previous_plan: dict[str, Any] | None = None,
        *,
        remaining_total_queries: int | None = None,
    ) -> QueryPlanSpec:
        normalized_query = normalize_text(user_query)
        max_total_queries, _ = self._resolve_query_limits(config, remaining_total_queries=remaining_total_queries)
        if not normalized_query:
            return QueryPlanSpec(
                user_query_raw="",
                user_query_short="",
                query_was_shortened=False,
                shortening_note="",
                expanded_queries=[],
                expansion_mode="raw",
                expansion_signature=build_expansion_signature([]),
                reused_previous=False,
            )
        reused = self._reuse_previous_plan(
            normalized_query,
            previous_plan,
            config,
            max_total_queries=max_total_queries,
        )
        if reused is not None:
            return reused
        try:
            planned = self._plan_with_openai(
                normalized_query,
                config,
                max_total_queries=max_total_queries,
            )
        except Exception:
            planned = self._plan_with_fallback(
                normalized_query,
                config,
                max_total_queries=max_total_queries,
            )
        return planned

    def build_provider_cache_policy(self, config: AppConfig) -> str:
        provider = get_provider_option(config.provider)
        requested_cache = config.prompt_cache_retention if provider.supports_prompt_cache else "in_memory"
        return (
            f"{config.provider}:{provider.cache_policy_mode};"
            f"planner={config.query_planner_model};"
            f"execution_order={config.query_execution_order};"
            f"execution_prompt_cache={requested_cache};"
            f"planner_reuse={'enabled' if provider.supports_query_planner_reuse else 'disabled'}"
        )

    def build_planner_signature(self, config: AppConfig) -> str:
        provider = get_provider_option(config.provider)
        payload = {
            "provider": provider.key,
            "planner_model": config.query_planner_model,
            "planner_reasoning_effort": config.query_planner_reasoning_effort,
            "planner_max_output_tokens": int(config.query_planner_max_output_tokens or 0),
            "query_expansion_max_total_queries": int(config.query_expansion_max_total_queries or 0),
            "provider_max_expansion_queries": int(provider.max_expansion_queries or 0),
            "query_expansion_shorten_threshold_chars": int(config.query_expansion_shorten_threshold_chars or 0),
            "query_expansion_template_set": str(config.query_expansion_template_set or ""),
            "query_execution_order": str(config.query_execution_order or ""),
            "provider_cache_policy": self.build_provider_cache_policy(config),
        }
        return build_expansion_signature([json.dumps(payload, ensure_ascii=False, sort_keys=True)])

    def _reuse_previous_plan(
        self,
        normalized_query: str,
        previous_plan: dict[str, Any] | None,
        config: AppConfig,
        *,
        max_total_queries: int,
    ) -> QueryPlanSpec | None:
        if not previous_plan:
            return None
        provider = get_provider_option(config.provider)
        if not provider.supports_query_planner_reuse:
            return None
        current_signature = self.build_planner_signature(config)
        previous_signature = str(previous_plan.get("planner_signature") or "").strip()
        if previous_signature != current_signature:
            return None
        previous_raw = normalize_text(previous_plan.get("user_query_raw") or "")
        if previous_raw != normalized_query:
            return None
        _, max_expansion_queries = self._resolve_query_limits(config, remaining_total_queries=max_total_queries)
        try:
            raw_expanded_queries = json.loads(str(previous_plan.get("expanded_queries_json") or "[]"))
        except Exception:
            raw_expanded_queries = []
        expanded_queries = self._sanitize_expanded_queries(
            normalized_query,
            normalize_text(previous_plan.get("user_query_short") or ""),
            bool(previous_plan.get("query_was_shortened")),
            raw_expanded_queries,
            max_total_queries=max_total_queries,
            max_expansion_queries=max_expansion_queries,
        )
        if not expanded_queries:
            return None
        return QueryPlanSpec(
            user_query_raw=normalized_query,
            user_query_short=normalize_text(previous_plan.get("user_query_short") or normalized_query),
            query_was_shortened=bool(previous_plan.get("query_was_shortened")),
            shortening_note=normalize_text(previous_plan.get("shortening_note") or ""),
            expanded_queries=expanded_queries,
            expansion_mode=str(previous_plan.get("expansion_mode") or self._resolve_expansion_mode(expanded_queries, bool(previous_plan.get("query_was_shortened")))),
            expansion_signature=str(previous_plan.get("expansion_signature") or build_expansion_signature(expanded_queries)),
            reused_previous=True,
        )

    def _plan_with_openai(
        self,
        normalized_query: str,
        config: AppConfig,
        *,
        max_total_queries: int,
    ) -> QueryPlanSpec:
        _, max_expansion_queries = self._resolve_query_limits(config, remaining_total_queries=max_total_queries)
        response = self._client_instance().responses.create(
            model=config.query_planner_model,
            reasoning={"effort": config.query_planner_reasoning_effort},
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": QUERY_PLANNING_SYSTEM_PROMPT}]},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {
                                    "user_query_raw": normalized_query,
                                    "must_shorten": should_shorten_query(
                                        normalized_query,
                                        threshold=config.query_expansion_shorten_threshold_chars,
                                    ),
                                },
                                ensure_ascii=False,
                            ),
                        }
                    ],
                },
            ],
            max_output_tokens=config.query_planner_max_output_tokens,
        )
        output_text = str(getattr(response, "output_text", "") or "").strip()
        parsed = self._parse_plan_payload(output_text)
        short_query = normalize_text(parsed.get("short_query") or normalized_query)
        if (
            should_shorten_query(
                normalized_query,
                threshold=config.query_expansion_shorten_threshold_chars,
            )
            and short_query == normalized_query
        ):
            short_query = self._fallback_short_query(
                normalized_query,
                shorten_threshold=config.query_expansion_shorten_threshold_chars,
            )
        query_was_shortened = short_query != normalized_query and (
            bool(parsed.get("query_was_shortened"))
            or should_shorten_query(
                normalized_query,
                threshold=config.query_expansion_shorten_threshold_chars,
            )
        )
        expansions = parsed.get("expansions") if isinstance(parsed.get("expansions"), list) else []
        expanded_queries = self._sanitize_expanded_queries(
            normalized_query,
            short_query,
            query_was_shortened,
            expansions,
            max_total_queries=max_total_queries,
            max_expansion_queries=max_expansion_queries,
        )
        if len(expanded_queries) <= 1:
            expanded_queries = self._sanitize_expanded_queries(
                normalized_query,
                short_query,
                query_was_shortened,
                self._build_fallback_expansions(
                    short_query,
                    normalized_query,
                    template_set=config.query_expansion_template_set,
                    max_expansions=max_expansion_queries,
                ),
                max_total_queries=max_total_queries,
                max_expansion_queries=max_expansion_queries,
            )
        else:
            expanded_queries = self._sanitize_expanded_queries(
                normalized_query,
                short_query,
                query_was_shortened,
                expanded_queries[1:],
                max_total_queries=max_total_queries,
                max_expansion_queries=max_expansion_queries,
            )
        return QueryPlanSpec(
            user_query_raw=normalized_query,
            user_query_short=short_query,
            query_was_shortened=query_was_shortened,
            shortening_note=normalize_text(parsed.get("shortening_note") or ""),
            expanded_queries=expanded_queries,
            expansion_mode=self._resolve_expansion_mode(expanded_queries, query_was_shortened),
            expansion_signature=build_expansion_signature(expanded_queries),
            reused_previous=False,
        )

    def _plan_with_fallback(
        self,
        normalized_query: str,
        config: AppConfig,
        *,
        max_total_queries: int,
    ) -> QueryPlanSpec:
        _, max_expansion_queries = self._resolve_query_limits(config, remaining_total_queries=max_total_queries)
        short_query = self._fallback_short_query(
            normalized_query,
            shorten_threshold=config.query_expansion_shorten_threshold_chars,
        )
        query_was_shortened = short_query != normalized_query
        shortening_note = (
            "地域・対象・価格条件・比較軸を残して内部用に短く整えました。"
            if query_was_shortened
            else ""
        )
        fallback_expansions = self._build_fallback_expansions(
            short_query,
            normalized_query,
            template_set=config.query_expansion_template_set,
            max_expansions=max_expansion_queries,
        )
        expanded_queries = self._sanitize_expanded_queries(
            normalized_query,
            short_query,
            query_was_shortened,
            fallback_expansions,
            max_total_queries=max_total_queries,
            max_expansion_queries=max_expansion_queries,
        )
        return QueryPlanSpec(
            user_query_raw=normalized_query,
            user_query_short=short_query,
            query_was_shortened=query_was_shortened,
            shortening_note=shortening_note,
            expanded_queries=expanded_queries,
            expansion_mode=self._resolve_expansion_mode(expanded_queries, query_was_shortened),
            expansion_signature=build_expansion_signature(expanded_queries),
            reused_previous=False,
        )

    def _parse_plan_payload(self, output_text: str) -> dict[str, Any]:
        parsed = json.loads(output_text)
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("planner output is not a JSON object")

    def _fallback_short_query(self, normalized_query: str, *, shorten_threshold: int) -> str:
        if not should_shorten_query(normalized_query, threshold=shorten_threshold):
            return normalized_query
        compact = normalize_text(normalized_query)
        replacements = {
            "導入支援サービス": "導入支援",
            "サポート体制": "サポート",
            "他社比較まで含めて": "他社比較",
            "比較まで含めて": "比較",
            "知りたい": "",
            "教えてください": "",
            "教えて": "",
            "確認したい": "",
            "について": "",
            "できるか": "可否",
        }
        for old, new in replacements.items():
            compact = compact.replace(old, new)
        compact = re.sub(r"[、。]+", " ", compact)
        compact = re.sub(r"\s+", " ", compact).strip(" 　")
        if compact != normalized_query:
            return compact
        return normalized_query

    def _build_fallback_expansions(
        self,
        short_query: str,
        original_query: str,
        *,
        template_set: str,
        max_expansions: int,
    ) -> list[str]:
        base_query = normalize_text(short_query or original_query)
        lowered = normalize_query_text(base_query)
        suffix_rules = DEFAULT_QUERY_EXPANSION_SUFFIX_RULES.get(
            template_set,
            DEFAULT_QUERY_EXPANSION_SUFFIX_RULES["business_ja"],
        )
        fallback_expansions: list[str] = []
        for suffix, signals in suffix_rules:
            if any(signal in lowered for signal in signals):
                continue
            fallback_expansions.append(f"{base_query} {suffix}")
            if len(fallback_expansions) >= max(0, max_expansions):
                break
        return fallback_expansions

    def _sanitize_expanded_queries(
        self,
        user_query_raw: str,
        short_query: str,
        query_was_shortened: bool,
        expansions: list[Any],
        *,
        max_total_queries: int = 5,
        max_expansion_queries: int | None = None,
    ) -> list[str]:
        base_query = short_query if query_was_shortened and short_query else user_query_raw
        ordered = [base_query]
        expansion_limit = None if max_expansion_queries is None else max(0, int(max_expansion_queries))
        expansion_count = 0
        for item in expansions:
            value = normalize_text(str(item or ""))
            if not value:
                continue
            if expansion_limit is not None and expansion_count >= expansion_limit:
                break
            ordered.append(value)
            expansion_count += 1
        deduped: list[str] = []
        seen_keys: set[str] = set()
        for item in ordered:
            key = normalize_query_text(item)
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(item)
            if len(deduped) >= max(1, max_total_queries):
                break
        return deduped or [user_query_raw]

    def _resolve_expansion_mode(self, expanded_queries: list[str], query_was_shortened: bool) -> str:
        if len(expanded_queries) > 1:
            return "expanded"
        if query_was_shortened:
            return "shortened"
        return "raw"

    def _client_instance(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI()
        return self._client

    def _resolve_query_limits(
        self,
        config: AppConfig,
        *,
        remaining_total_queries: int | None = None,
    ) -> tuple[int, int]:
        provider = get_provider_option(config.provider)
        provider_total_budget = get_provider_total_question_budget(provider.key)
        max_total_queries = max(1, int(config.query_expansion_max_total_queries or 1))
        if remaining_total_queries is not None:
            max_total_queries = min(max_total_queries, max(1, int(remaining_total_queries)))
        max_total_queries = min(max_total_queries, provider_total_budget)
        max_expansion_queries = max(0, min(int(provider.max_expansion_queries or 0), max_total_queries - 1))
        return max_total_queries, max_expansion_queries


def build_execution_plan(query_plans: list[dict[str, Any]], config: AppConfig) -> ExecutionPlan:
    jobs: list[ExecutionJob] = []
    for plan in query_plans:
        try:
            expanded_queries = json.loads(str(plan.get("expanded_queries_json") or "[]"))
        except Exception:
            expanded_queries = []
        for index, executed_query in enumerate(expanded_queries, start=1):
            normalized_query = normalize_text(executed_query)
            if not normalized_query:
                continue
            jobs.append(
                ExecutionJob(
                    query_plan_id=str(plan.get("query_plan_id") or ""),
                    user_query_raw=str(plan.get("user_query_raw") or ""),
                    executed_query=normalized_query,
                    executed_query_index=index,
                )
            )

    execution_order = normalize_text(config.query_execution_order) or "query_then_repeat"
    requests: list[ExecutionRequest] = []
    if execution_order == "repeat_then_query":
        for iteration_index in range(1, config.repeat_count + 1):
            for job in jobs:
                requests.append(
                    ExecutionRequest(
                        query_plan_id=job.query_plan_id,
                        user_query_raw=job.user_query_raw,
                        executed_query=job.executed_query,
                        executed_query_index=job.executed_query_index,
                        iteration_index=iteration_index,
                    )
                )
    else:
        execution_order = "query_then_repeat"
        for job in jobs:
            for iteration_index in range(1, config.repeat_count + 1):
                requests.append(
                    ExecutionRequest(
                        query_plan_id=job.query_plan_id,
                        user_query_raw=job.user_query_raw,
                        executed_query=job.executed_query,
                        executed_query_index=job.executed_query_index,
                        iteration_index=iteration_index,
                    )
                )

    return ExecutionPlan(
        jobs=jobs,
        requests=requests,
        total_unique_queries=len(jobs),
        total_request_count=len(requests),
        total_question_budget=get_provider_total_question_budget(config.provider),
        execution_order=execution_order,
    )
