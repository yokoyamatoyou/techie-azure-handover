from __future__ import annotations

import json
from collections import Counter
from typing import Any, Callable

from analysis_lib import (
    aggregate_url_evidence,
    build_evidence_stats,
    build_keyword_stability_map,
    classify_keyword_intent,
    classify_visibility_verdict,
    build_topic_signal_summary,
    dedupe_preserve_order,
    infer_page_gap,
    normalize_domain_host,
    normalize_query_text,
    normalize_text,
    parse_json_object,
    normalize_url_for_match,
    resolve_citation_records,
    resolve_analysis_mode,
    resolve_visibility_score,
)
from config import ANALYSIS_MODE_OWNED_ONLY, AppConfig
from ui.evidence_presenters import find_group_rows


def localize_analysis_mode(mode: str) -> str:
    return "自社監査" if mode == ANALYSIS_MODE_OWNED_ONLY else "市場観測"


def get_latest_rows_by_keyword(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if rows and any(row.get("internal_query_count") is not None or row.get("executed_queries_json") for row in rows):
        return rows
    from analysis_lib import build_query_rollup_rows

    return build_query_rollup_rows(rows)


def extract_competitor_mentions(payload: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for item in payload.get("competitor_mentions") or []:
        value = str(item or "").strip()
        if value and value not in seen:
            seen.append(value)
    return seen


def build_visibility_state_label(score: int, target_hit: bool, brand_hit: bool) -> str:
    return classify_visibility_verdict(score, target_hit, brand_hit)


def build_verdict_text_class(verdict: str) -> str:
    if verdict == "自社優勢":
        return "text-self"
    if verdict in {"外部サイト優勢", "未露出"}:
        return "text-external"
    return "text-competitive"


def build_primary_visibility_label(verdict: str, analysis_mode: str) -> str:
    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        if verdict == "自社優勢":
            return "自社ページが主に引用された"
        if verdict == "自社あり":
            return "自社ページも出るが並走"
        if verdict == "外部サイト優勢":
            return "外部が主に引用された"
        return "自社は確認できず"
    if verdict == "自社優勢":
        return "自社が主に引用された"
    if verdict == "自社あり":
        return "自社も出るが並走"
    if verdict == "外部サイト優勢":
        return "外部が主に引用された"
    return "自社は確認できず"


def build_keyword_verdict_summary(row: dict[str, Any], payload: dict[str, Any]) -> str:
    score = int(row.get("visibility_score") or 0)
    target_hit = bool(row.get("target_domain_hit"))
    brand_hit = bool(row.get("brand_mention_hit"))
    competitors = extract_competitor_mentions(payload)
    verdict = build_visibility_state_label(score, target_hit, brand_hit)
    analysis_mode = resolve_analysis_mode(payload)

    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        if target_hit and score >= 70:
            return "自社サイトだけで、この質問に答える根拠を十分に出せています。"
        if target_hit:
            return "自社サイトだけでも答えは返せますが、根拠や見出しの厚みはまだ弱めです。"
        return "自社サイトだけでは、この質問に答える根拠をまだ作れていません。"

    if verdict == "自社優勢":
        if competitors:
            return (
                f"自社URLが根拠に入り、{', '.join(competitors[:2])} も見えていますが、"
                "この質問では自社が先に見つかっています。"
            )
        return "自社URLが根拠に入り、この質問では自社が先に見つかっています。"
    if verdict == "自社あり":
        if competitors:
            return f"自社URLや名称は出ていますが、{', '.join(competitors[:2])} や外部サイトと並ぶ状態です。"
        return "自社URLや名称は出ていますが、外部サイトと並ぶ状態です。"
    if verdict == "外部サイト優勢":
        if competitors:
            return f"{', '.join(competitors[:2])} や外部サイトが先に見られ、自社はまだ前に出ていません。"
        return "外部サイトが先に見られ、自社はまだ前に出ていません。"
    if competitors:
        return f"この質問では自社URLも名称も確認できず、{', '.join(competitors[:2])} や外部サイトが中心です。"
    return "この質問では自社URLも名称も確認できず、まだ露出を作れていません。"


def build_result_digest(row: dict[str, Any], payload: dict[str, Any]) -> str:
    score = int(row.get("visibility_score") or 0)
    target_hit = bool(row.get("target_domain_hit"))
    brand_hit = bool(row.get("brand_mention_hit"))
    competitors = extract_competitor_mentions(payload)
    verdict = build_visibility_state_label(score, target_hit, brand_hit)
    analysis_mode = resolve_analysis_mode(payload)
    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        if target_hit and score >= 70:
            return "自社資産だけで答え切れています"
        if target_hit:
            return "自社資産だけでも一部は答えられます"
        return "自社資産だけでは答え切れていません"
    if verdict == "自社優勢":
        if competitors:
            return f"{', '.join(competitors[:2])} より前に出ています"
        return "外部サイトより前に出ています"
    if verdict == "自社あり":
        if competitors:
            return f"{', '.join(competitors[:2])} や外部サイトと並んでいます"
        return "外部サイトと並んでいます"
    if verdict == "外部サイト優勢":
        if competitors:
            return f"{', '.join(competitors[:2])} や外部サイトが先行しています"
        return "外部サイトが先行しています"
    if competitors:
        return f"{', '.join(competitors[:2])} に対して自社は確認できていません"
    return "自社の露出を確認できません"


def format_percent_compact(value: float) -> str:
    if abs(value - round(value)) < 0.05:
        return f"{int(round(value))}%"
    return f"{value:.1f}%"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _resolve_row_trial_count(row: dict[str, Any]) -> int:
    return max(
        int(row.get("trial_count") or 0),
        int(row.get("answer_observation_count") or 0),
        int(row.get("result_count") or 0),
        1 if row.get("result_id") else 0,
    )


def build_primary_metric_copy(row: dict[str, Any]) -> dict[str, str | float]:
    trial_count = max(_resolve_row_trial_count(row), 0)
    citation_trial_count = max(
        int(row.get("owned_citation_trial_count") or 0),
        int(row.get("owned_citation_result_count") or 0),
    )
    citation_rate = _safe_float(
        row.get("owned_citation_trial_rate"),
        _safe_float(
            row.get("owned_citation_result_rate"),
            round((citation_trial_count / trial_count) * 100.0, 1) if trial_count > 0 else 0.0,
        ),
    )

    if trial_count and not row.get("owned_citation_trial_count") and not row.get("owned_citation_result_count"):
        citation_trial_count = min(trial_count, max(0, int(round(citation_rate * trial_count / 100.0))))

    summary = "first view では、自社URLが実際に引用された割合だけを表示しています。"
    if trial_count <= 1:
        summary = "今回は、自社URLが実際に引用されたかどうかだけを表示しています。"

    coverage_summary = "見つかっただけの状態はここでは混ぜず、実際に引用されたかだけを主指標にしています。"

    story_summary = f"今回の自社引用率は {format_percent_compact(citation_rate)} です。"

    return {
        "label": "自社引用率",
        "value": citation_rate,
        "value_text": format_percent_compact(citation_rate),
        "summary": summary,
        "coverage_summary": coverage_summary,
        "story_summary": story_summary,
        "trial_count": trial_count,
        "citation_trial_count": citation_trial_count,
    }


def _source_owner_rank(owner_bucket: str) -> int:
    return {"self": 0, "competitor": 1, "external": 2}.get(str(owner_bucket or ""), 9)


def _source_owner_label(owner_bucket: str) -> str:
    return {
        "self": "自社",
        "competitor": "比較対象",
        "external": "外部サイト",
    }.get(str(owner_bucket or ""), "参照元")


def _build_source_page_label(title: Any, host: str, url: Any) -> str:
    value = str(title or "").strip()
    if value and not value.lower().startswith(("http://", "https://")):
        return value
    if host:
        return host
    return str(url or "-").strip() or "-"


def build_source_focus_summary(
    group_rows: list[dict[str, Any]],
    aggregated_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    total_trial_count = sum(
        1
        for row in group_rows
        if str(row.get("result_id") or row.get("executed_query") or row.get("keyword_raw") or "").strip()
    )
    if not group_rows or total_trial_count <= 0:
        return {
            "total_trial_count": total_trial_count,
            "summary": "",
            "lead_source_label": "",
            "lead_source_basis_text": "",
            "domain_items": [],
            "page_items": [],
            "focus_items": [],
            "basis_note": "ページ名とサイト名で要約し、実URLは詳細で確認します。",
        }

    cited_page_meta: dict[str, dict[str, Any]] = {}
    for item in aggregated_evidence:
        if str(item.get("status") or "") != "cited":
            continue
        normalized_url = str(item.get("normalized_url") or normalize_url_for_match(item.get("url")) or "").strip()
        if not normalized_url:
            continue
        cited_page_meta[normalized_url] = {
            "url": str(item.get("url") or "").strip(),
            "host": str(item.get("host") or normalize_domain_host(item.get("url")) or "").strip(),
            "title": str(item.get("title") or "").strip(),
            "owner_bucket": str(item.get("owner_bucket") or "external"),
        }

    domain_trials: dict[str, set[str]] = {}
    page_trials: dict[str, set[str]] = {}
    domain_meta: dict[str, dict[str, Any]] = {}
    page_meta: dict[str, dict[str, Any]] = {}

    for index, row in enumerate(group_rows):
        trial_key = (
            str(row.get("result_id") or "").strip()
            or f"{str(row.get('run_id') or '').strip()}::{index}::{normalize_query_text(str(row.get('executed_query') or row.get('keyword_raw') or ''))}"
        )
        if not trial_key:
            continue
        payload = parse_json_object(row.get("output_json"))
        citations = resolve_citation_records(row, payload)
        seen_hosts: set[str] = set()
        seen_pages: set[str] = set()
        for citation in citations:
            normalized_url = normalize_url_for_match(citation.get("url"))
            if not normalized_url:
                continue
            meta = cited_page_meta.get(normalized_url, {})
            host = str(meta.get("host") or normalize_domain_host(citation.get("url")) or "").strip()
            if not host:
                continue
            owner_bucket = str(meta.get("owner_bucket") or "external")
            page_bucket = page_meta.setdefault(
                normalized_url,
                {
                    "url": str(meta.get("url") or citation.get("url") or "").strip(),
                    "host": host,
                    "owner_bucket": owner_bucket,
                    "title": _build_source_page_label(meta.get("title") or citation.get("title"), host, citation.get("url")),
                },
            )
            title_candidate = _build_source_page_label(
                meta.get("title") or citation.get("title"),
                host,
                citation.get("url"),
            )
            if len(title_candidate) > len(str(page_bucket.get("title") or "")):
                page_bucket["title"] = title_candidate
            domain_bucket = domain_meta.setdefault(
                host,
                {
                    "host": host,
                    "owner_bucket": owner_bucket,
                },
            )
            if _source_owner_rank(owner_bucket) < _source_owner_rank(str(domain_bucket.get("owner_bucket") or "")):
                domain_bucket["owner_bucket"] = owner_bucket
            if host not in seen_hosts:
                domain_trials.setdefault(host, set()).add(trial_key)
                seen_hosts.add(host)
            if normalized_url not in seen_pages:
                page_trials.setdefault(normalized_url, set()).add(trial_key)
                seen_pages.add(normalized_url)

    domain_items = [
        {
            "label": host,
            "host": host,
            "owner_bucket": str(domain_meta.get(host, {}).get("owner_bucket") or "external"),
            "owner_label": _source_owner_label(str(domain_meta.get(host, {}).get("owner_bucket") or "external")),
            "trial_count": len(trial_keys),
            "question_count": len(trial_keys),
            "rate": round((len(trial_keys) / total_trial_count) * 100.0, 1) if total_trial_count else 0.0,
            "rate_text": format_percent_compact(round((len(trial_keys) / total_trial_count) * 100.0, 1) if total_trial_count else 0.0),
            "summary": "今回、回答の根拠としてよく使われたサイトです。",
        }
        for host, trial_keys in domain_trials.items()
    ]
    domain_items.sort(
        key=lambda item: (
            -int(item["question_count"]),
            _source_owner_rank(str(item.get("owner_bucket") or "")),
            str(item.get("host") or ""),
        )
    )

    page_items = [
        {
            "label": str(page_meta.get(normalized_url, {}).get("title") or page_meta.get(normalized_url, {}).get("host") or normalized_url),
            "title": str(page_meta.get(normalized_url, {}).get("title") or page_meta.get(normalized_url, {}).get("host") or normalized_url),
            "host": str(page_meta.get(normalized_url, {}).get("host") or ""),
            "url": str(page_meta.get(normalized_url, {}).get("url") or ""),
            "owner_bucket": str(page_meta.get(normalized_url, {}).get("owner_bucket") or "external"),
            "owner_label": _source_owner_label(str(page_meta.get(normalized_url, {}).get("owner_bucket") or "external")),
            "trial_count": len(trial_keys),
            "question_count": len(trial_keys),
            "rate": round((len(trial_keys) / total_trial_count) * 100.0, 1) if total_trial_count else 0.0,
            "rate_text": format_percent_compact(round((len(trial_keys) / total_trial_count) * 100.0, 1) if total_trial_count else 0.0),
            "summary": "今回、回答の根拠としてよく使われたページです。",
        }
        for normalized_url, trial_keys in page_trials.items()
    ]
    page_items.sort(
        key=lambda item: (
            -int(item["question_count"]),
            _source_owner_rank(str(item.get("owner_bucket") or "")),
            str(item.get("host") or ""),
            str(item.get("title") or ""),
        )
    )

    lead_source = domain_items[0] if domain_items else None
    lead_page = page_items[0] if page_items else None
    lead_source_label = str((lead_source or {}).get("label") or "")
    lead_source_basis_text = "今回、回答の根拠として最もよく使われたサイトです。" if lead_source else ""

    summary = ""
    if lead_source and lead_page:
        summary = (
            f"AI回答に使われた主要ソースは {lead_source['label']} です。"
            f" ページ単位では「{lead_page['title']}」がよく引用されています。"
        )
    elif lead_source:
        summary = f"AI回答に使われた主要ソースは {lead_source['label']} です。"
    elif lead_page:
        summary = f"ページ単位では「{lead_page['title']}」がよく引用されています。"
    else:
        summary = "まだ引用元の傾向は十分に見えていません。"

    focus_items: list[dict[str, Any]] = []
    if page_items:
        for item in page_items[:5]:
            focus_items.append(
                {
                    "label": str(item.get("title") or item.get("label") or "-"),
                    "host": str(item.get("host") or ""),
                    "owner_bucket": str(item.get("owner_bucket") or "external"),
                    "owner_label": str(item.get("owner_label") or "参照元"),
                    "trial_count": int(item.get("trial_count") or item.get("question_count") or 0),
                    "question_count": int(item.get("trial_count") or item.get("question_count") or 0),
                    "summary": f"{int(item.get('trial_count') or item.get('question_count') or 0)}回の試行で根拠に使われました。",
                }
            )
    else:
        for item in domain_items[:5]:
            focus_items.append(
                {
                    "label": str(item.get("label") or "-"),
                    "host": str(item.get("host") or ""),
                    "owner_bucket": str(item.get("owner_bucket") or "external"),
                    "owner_label": str(item.get("owner_label") or "参照元"),
                    "trial_count": int(item.get("trial_count") or item.get("question_count") or 0),
                    "question_count": int(item.get("trial_count") or item.get("question_count") or 0),
                    "summary": f"{int(item.get('trial_count') or item.get('question_count') or 0)}回の試行で根拠に使われました。",
                }
            )

    return {
        "total_trial_count": total_trial_count,
        "summary": summary,
        "lead_source_label": lead_source_label,
        "lead_source_basis_text": lead_source_basis_text,
        "domain_items": domain_items[:5],
        "page_items": page_items[:5],
        "focus_items": focus_items,
        "basis_note": "URLは並べず、ページ名とサイト名で要約しています。実URLは詳細で確認します。",
    }


def build_competitive_snapshot_summary(evidence_stats: dict[str, Any]) -> dict[str, Any]:
    cited_counts = {
        "self": int(evidence_stats.get("self_cited") or 0),
        "competitor": int(evidence_stats.get("competitor_cited") or 0),
        "external": int(evidence_stats.get("external_cited") or 0),
    }
    candidate_counts = {
        "self": int(evidence_stats.get("self_searched_only") or 0),
        "competitor": int(evidence_stats.get("competitor_searched_only") or 0),
        "external": int(evidence_stats.get("external_searched_only") or 0),
    }
    basis_counts = cited_counts if sum(cited_counts.values()) > 0 else candidate_counts
    total = sum(basis_counts.values())
    label_map = {"self": "自社", "competitor": "比較対象", "external": "外部サイト"}
    tone_map = {"self": "self", "competitor": "competitor", "external": "external"}

    buckets: list[dict[str, Any]] = []
    for key in ("self", "competitor", "external"):
        count = int(basis_counts.get(key) or 0)
        share = round((count / total) * 100.0, 1) if total > 0 else 0.0
        buckets.append(
            {
                "key": key,
                "label": label_map[key],
                "tone": tone_map[key],
                "count": count,
                "share": share,
                "share_text": format_percent_compact(share),
            }
        )

    if total <= 0:
        return {
            "headline": "根拠サイトの偏りはまだ見えていません",
            "summary": "引用元が増えると、自社・比較対象・外部サイトのどこが強いかをここに出します。",
            "basis_label": "引用元ベース",
            "total": 0,
            "buckets": buckets,
        }

    top_count = max(int(item["count"]) for item in buckets)
    leader_keys = {str(item["key"]) for item in buckets if int(item["count"]) == top_count and top_count > 0}
    leader = max(buckets, key=lambda item: (float(item["share"]), int(item["count"])))
    self_count = int(basis_counts["self"])
    competitor_count = int(basis_counts["competitor"])
    external_count = int(basis_counts["external"])
    if len(leader_keys) > 1:
        headline = "根拠が複数の相手に分かれています"
    elif leader["key"] == "self":
        headline = "自社が主な根拠に入っています"
    elif leader["key"] == "competitor":
        headline = "比較対象も根拠に入りやすい状態です"
    else:
        headline = "現在は外部サイトが主な参照先です"

    if self_count and (competitor_count or external_count):
        summary = "自社も見えていますが、比較対象や外部サイトも同じ回答面に入っています。"
    elif self_count:
        summary = "今回の根拠は自社寄りです。維持しつつ、改善優先の質問だけを補強します。"
    elif competitor_count:
        summary = "比較対象側の根拠が見られています。どの質問で出たかを下の詳細で確認します。"
    else:
        summary = "現在は外部サイトが主な参照先です。主要ソースと不足情報を確認します。"

    return {
        "headline": headline,
        "summary": summary,
        "basis_label": "引用元ベース" if sum(cited_counts.values()) > 0 else "見つかった候補ベース",
        "total": total,
        "buckets": buckets,
    }


def build_source_influence_rows(source_focus_summary: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(source_focus_summary.get("focus_items") or [], start=1):
        trial_count = int(item.get("trial_count") or item.get("question_count") or 0)
        rows.append(
            {
                "rank": index,
                "label": str(item.get("label") or "-"),
                "host": str(item.get("host") or ""),
                "owner_bucket": str(item.get("owner_bucket") or "external"),
                "owner_label": str(item.get("owner_label") or "参照元"),
                "trial_count": trial_count,
                "adoption_label": f"{trial_count}回採用" if trial_count > 0 else "採用回数なし",
                "summary": str(item.get("summary") or "回答の根拠として使われました。"),
            }
        )
    return rows[:limit]


def _build_owner_share_buckets(counts: dict[str, int]) -> list[dict[str, Any]]:
    total = sum(max(0, int(value or 0)) for value in counts.values())
    label_map = {"self": "自社", "competitor": "比較対象", "external": "外部サイト"}
    tone_map = {"self": "self", "competitor": "competitor", "external": "external"}
    buckets: list[dict[str, Any]] = []
    for key in ("self", "competitor", "external"):
        count = max(0, int(counts.get(key) or 0))
        share = round((count / total) * 100.0, 1) if total > 0 else 0.0
        buckets.append(
            {
                "key": key,
                "label": label_map[key],
                "tone": tone_map[key],
                "count": count,
                "share": share,
                "share_text": format_percent_compact(share),
            }
        )
    return buckets


def _bucket_share(buckets: list[dict[str, Any]], key: str) -> float:
    item = next((bucket for bucket in buckets if str(bucket.get("key") or "") == key), None)
    return float((item or {}).get("share") or 0.0)


def build_evidence_stability_summary(
    evidence_stats: dict[str, Any],
    source_focus_summary: dict[str, Any],
    source_influence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    cited_counts = {
        "self": int(evidence_stats.get("self_cited") or 0),
        "competitor": int(evidence_stats.get("competitor_cited") or 0),
        "external": int(evidence_stats.get("external_cited") or 0),
    }
    candidate_counts = {
        "self": int(evidence_stats.get("self_searched_only") or 0),
        "competitor": int(evidence_stats.get("competitor_searched_only") or 0),
        "external": int(evidence_stats.get("external_searched_only") or 0),
    }
    basis_counts = cited_counts if sum(cited_counts.values()) > 0 else candidate_counts
    total = sum(max(0, int(value or 0)) for value in basis_counts.values())
    buckets = _build_owner_share_buckets(basis_counts)
    total_trials = int(source_focus_summary.get("total_trial_count") or 0)
    top_source = source_influence_rows[0] if source_influence_rows else {}
    top_count = int(top_source.get("trial_count") or 0)
    top_share = round((top_count / total_trials) * 100.0, 1) if total_trials > 0 else 0.0
    top_owner = str(top_source.get("owner_bucket") or "")
    top_label = str(top_source.get("host") or top_source.get("label") or "").strip()

    if total <= 0:
        return {
            "headline": "根拠の安定度はまだ見えていません",
            "summary": "引用元が増えると、自社・比較対象・外部サイトの依存度をここに出します。",
            "badge_label": "材料待ち",
            "badge_tone": "unknown",
            "basis_label": "引用元ベース",
            "basis_note": "比率は引用元分類、集中度は採用回数ベースです。",
            "total": 0,
            "buckets": buckets,
            "top_source_label": top_label or "-",
            "top_source_owner": top_owner or "external",
            "top_source_share": top_share,
            "top_source_share_text": format_percent_compact(top_share),
            "top_source_count": top_count,
            "concentration_label": "集中度なし",
        }

    self_share = _bucket_share(buckets, "self")
    competitor_share = _bucket_share(buckets, "competitor")
    external_share = _bucket_share(buckets, "external")
    basis_label = "引用元ベース" if sum(cited_counts.values()) > 0 else "見つかった候補ベース"

    if top_share >= 70:
        headline = "1サイトに偏っています"
        summary = f"上位1サイトの採用が {format_percent_compact(top_share)} です。判断がそのサイトに寄りやすい状態です。"
        badge_label = "高リスク"
        badge_tone = "high"
    elif external_share >= 65 and self_share < 30:
        headline = "外部サイト依存が強いです"
        summary = f"分類した引用元の {format_percent_compact(external_share)} が外部サイトです。外部評価サイトや口コミ側の見え方を確認します。"
        badge_label = "高リスク"
        badge_tone = "high"
    elif competitor_share >= 50 and self_share < 30:
        headline = "比較対象に寄っています"
        summary = "比較対象も根拠に入りやすい状態です。どの質問で出るかを詳細で確認します。"
        badge_label = "注意"
        badge_tone = "medium"
    elif self_share >= 50 and external_share <= 40 and top_share < 65:
        headline = "自社公式で取れています"
        summary = "分類した引用元では自社公式が主な根拠に入り、外部サイトは補助に回っています。"
        badge_label = "安定"
        badge_tone = "low"
    elif external_share >= 45 or top_share >= 55:
        headline = "外部サイト依存がやや強いです"
        summary = "自社も見えていますが、外部サイトや上位ソースへの依存が残っています。"
        badge_label = "注意"
        badge_tone = "medium"
    else:
        headline = "根拠は分散しています"
        summary = "分類した引用元では、自社・比較対象・外部サイトが大きく偏らず分散しています。"
        badge_label = "安定"
        badge_tone = "low"

    if top_share >= 70:
        concentration_label = "集中"
    elif top_share >= 45:
        concentration_label = "やや集中"
    elif top_share > 0:
        concentration_label = "分散"
    else:
        concentration_label = "集中度なし"

    return {
        "headline": headline,
        "summary": summary,
        "badge_label": badge_label,
        "badge_tone": badge_tone,
        "basis_label": basis_label,
        "basis_note": "比率は引用元分類、集中度は採用回数ベースです。",
        "total": total,
        "buckets": buckets,
        "top_source_label": top_label or "-",
        "top_source_owner": top_owner or "external",
        "top_source_share": top_share,
        "top_source_share_text": format_percent_compact(top_share),
        "top_source_count": top_count,
        "concentration_label": concentration_label,
    }


def build_visibility_stability_summary(row: dict[str, Any]) -> dict[str, Any]:
    trial_count = max(_resolve_row_trial_count(row), 0)
    visible_count = max(
        int(row.get("visible_trial_count") or 0),
        int(row.get("target_hit_count") or 0),
        trial_count if row.get("target_domain_hit") and trial_count == 1 else 0,
    )
    citation_count = max(
        int(row.get("owned_citation_trial_count") or 0),
        int(row.get("owned_citation_result_count") or 0),
        1 if trial_count == 1 and int(row.get("owned_citation_count") or 0) > 0 else 0,
    )
    external_count = max(
        int(row.get("external_lead_trial_count") or 0),
        trial_count
        if classify_visibility_verdict(
            resolve_visibility_score(row),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        == "外部サイト優勢"
        and trial_count == 1
        else 0,
    )
    visible_rate = round((visible_count / trial_count) * 100.0, 1) if trial_count else 0.0
    citation_rate = round((citation_count / trial_count) * 100.0, 1) if trial_count else 0.0
    external_rate = round((external_count / trial_count) * 100.0, 1) if trial_count else 0.0
    score_stddev = _safe_float(row.get("score_stddev"), 0.0)
    variance_label = str(row.get("variance_label") or "").strip()

    if trial_count < 3:
        status_key = "chance"
        headline = "まだ偶然寄りです"
        summary = "観測回数が少ないため、もう少し保存済み結果が増えると安定度を判断しやすくなります。"
        badge_label = "偶然寄り"
    elif score_stddev >= 20 or (visible_rate >= 40 and citation_rate < 20) or external_rate >= 45:
        status_key = "variable"
        headline = "出たり消えたりしています"
        summary = "見つかる回と引用される回に差があります。弱い質問タイプと主要ソースを合わせて確認します。"
        badge_label = "揺れあり"
    elif citation_rate >= 40 and score_stddev <= 15:
        status_key = "stable"
        headline = "安定して見えています"
        summary = "複数回の観測で自社URLが引用されやすく、スコアの揺れも小さめです。"
        badge_label = "安定"
    elif visible_rate >= 60 and score_stddev <= 18:
        status_key = "stable"
        headline = "安定して見えています"
        summary = "自社は継続して見えています。引用に入りきらない質問だけ補強します。"
        badge_label = "安定"
    elif score_stddev >= 12 or variance_label:
        status_key = "variable"
        headline = "出たり消えたりしています"
        summary = "観測ごとの差が残っています。どの質問で弱いかを下の質問タイプで確認します。"
        badge_label = "揺れあり"
    else:
        status_key = "chance"
        headline = "まだ偶然寄りです"
        summary = "大きく悪くはありませんが、安定と言い切るには観測材料がまだ薄い状態です。"
        badge_label = "偶然寄り"

    segments = [
        {"key": "chance", "label": "偶然寄り", "active": status_key == "chance"},
        {"key": "variable", "label": "揺れあり", "active": status_key == "variable"},
        {"key": "stable", "label": "安定", "active": status_key == "stable"},
    ]
    return {
        "headline": headline,
        "summary": summary,
        "badge_label": badge_label,
        "badge_tone": status_key,
        "status_key": status_key,
        "segments": segments,
        "trial_count": trial_count,
        "visible_count": visible_count,
        "citation_count": citation_count,
        "external_count": external_count,
        "visible_rate": visible_rate,
        "citation_rate": citation_rate,
        "external_rate": external_rate,
        "visible_rate_text": format_percent_compact(visible_rate),
        "citation_rate_text": format_percent_compact(citation_rate),
        "external_rate_text": format_percent_compact(external_rate),
        "score_stddev": score_stddev,
        "variance_label": variance_label or "揺れ小",
        "basis_text": f"観測 {trial_count}回 / 自社引用 {citation_count}回",
    }


def _heatmap_rate(row: dict[str, Any], tone: str) -> float:
    for cell in row.get("cells") or []:
        if str(cell.get("tone") or "") == tone:
            return float(cell.get("rate") or 0.0)
    return 0.0


def build_weak_question_type_summary(rows: list[dict[str, Any]], limit: int = 3) -> dict[str, Any]:
    ordered = sorted(
        list(rows or []),
        key=lambda row: (
            -_heatmap_rate(row, "external"),
            _heatmap_rate(row, "cited"),
            -_heatmap_rate(row, "found"),
            str(row.get("label") or ""),
        ),
    )
    items: list[dict[str, Any]] = []
    for row in ordered[:limit]:
        cited_rate = _heatmap_rate(row, "cited")
        found_rate = _heatmap_rate(row, "found")
        external_rate = _heatmap_rate(row, "external")
        if external_rate > max(cited_rate, found_rate):
            status_label = "外部サイトに寄りやすい"
            tone = "high"
        elif found_rate > cited_rate:
            status_label = "見つかるが引用は弱い"
            tone = "medium"
        elif cited_rate > 0:
            status_label = "自社引用あり"
            tone = "low"
        else:
            status_label = "まだ偶然寄り"
            tone = "medium"
        items.append(
            {
                "label": str(row.get("label") or row.get("short_label") or "-"),
                "short_label": str(row.get("short_label") or row.get("label") or "-"),
                "status_label": status_label,
                "tone": tone,
                "cited_rate": cited_rate,
                "found_rate": found_rate,
                "external_rate": external_rate,
                "cited_rate_text": format_percent_compact(cited_rate),
                "found_rate_text": format_percent_compact(found_rate),
                "external_rate_text": format_percent_compact(external_rate),
            }
        )

    if not items:
        return {
            "headline": "弱い質問タイプはまだ見えていません",
            "summary": "質問タイプごとの保存結果が増えると、どこから見るべきかをここに出します。",
            "items": [],
        }

    lead = items[0]
    if str(lead["tone"]) == "low":
        headline = f"{lead['label']}は維持しやすい状態です"
    else:
        headline = f"{lead['label']}の質問で弱い"
    summary = (
        f"{lead['label']}は自社引用 {lead['cited_rate_text']}、"
        f"外部 {lead['external_rate_text']} です。"
    )
    return {"headline": headline, "summary": summary, "items": items}


def build_losing_prompt_heatmap_rows(group_rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    axis_summary = build_question_axis_summary(group_rows)

    def _cell_rate(row: dict[str, Any], tone: str) -> float:
        for cell in row.get("cells") or []:
            if str(cell.get("tone") or "") == tone:
                return float(cell.get("rate") or 0.0)
        return 0.0

    rows = list(axis_summary.get("heatmap_rows") or [])
    rows.sort(
        key=lambda row: (
            -_cell_rate(row, "external"),
            _cell_rate(row, "cited"),
            str(row.get("label") or ""),
        )
    )
    return rows[:limit]


def build_question_axis_summary(group_rows: list[dict[str, Any]]) -> dict[str, Any]:
    short_axis_phrase = {
        "比較": "比較",
        "料金": "料金",
        "事例": "事例",
        "FAQ": "FAQ",
        "サポート": "運用",
        "評判": "評判",
        "導入不安": "不安",
        "手順": "導入",
    }
    total_trial_count = sum(
        _resolve_row_trial_count(row)
        for row in group_rows
        if normalize_query_text(str(row.get("executed_query") or row.get("keyword_raw") or ""))
    )
    prompt_stats: dict[str, dict[str, Any]] = {}
    for row in group_rows:
        executed_query = normalize_query_text(str(row.get("executed_query") or row.get("keyword_raw") or ""))
        if not executed_query:
            continue
        row_trial_count = _resolve_row_trial_count(row)
        try:
            prompt_items = json.loads(str(row.get("prompt_taxonomy_json") or "[]"))
        except Exception:
            prompt_items = []
        if not isinstance(prompt_items, list):
            prompt_items = []

        matched_item = None
        for item in prompt_items:
            if not isinstance(item, dict):
                continue
            item_query = normalize_query_text(str(item.get("query_norm") or item.get("query") or ""))
            if item_query and item_query == executed_query:
                matched_item = item
                break
        if matched_item is None:
            executed_index = int(row.get("executed_query_index") or 0)
            matched_item = next(
                (
                    item
                    for item in prompt_items
                    if isinstance(item, dict) and int(item.get("query_index") or 0) == executed_index
                ),
                None,
            )

        label = str((matched_item or {}).get("prompt_label") or (matched_item or {}).get("prompt_family") or "").strip()
        if not label:
            continue
        bucket = prompt_stats.setdefault(
            label,
            {"label": label, "trial_count": 0, "found_count": 0, "citation_count": 0, "external_count": 0},
        )
        verdict = classify_visibility_verdict(
            resolve_visibility_score(row),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        visible_trial_count = max(
            int(row.get("visible_trial_count") or 0),
            int(row.get("target_hit_count") or 0),
            row_trial_count if row.get("target_domain_hit") and row_trial_count == 1 else 0,
        )
        citation_trial_count = max(
            int(row.get("owned_citation_trial_count") or 0),
            int(row.get("owned_citation_result_count") or 0),
            1 if row_trial_count == 1 and int(row.get("owned_citation_count") or 0) > 0 else 0,
        )
        external_trial_count = max(
            int(row.get("external_lead_trial_count") or 0),
            row_trial_count if verdict == "外部サイト優勢" and row_trial_count == 1 else 0,
        )
        bucket["trial_count"] += row_trial_count
        bucket["found_count"] += visible_trial_count
        bucket["citation_count"] += citation_trial_count
        bucket["external_count"] += external_trial_count

    ordered = sorted(
        prompt_stats.values(),
        key=lambda item: (
            -int(item["citation_count"]),
            -int(item["found_count"]),
            -int(item["trial_count"]),
            str(item["label"]),
        ),
    )
    visible_labels = [str(item["label"]) for item in ordered if int(item["citation_count"]) > 0][:3]
    weak_labels = [str(item["label"]) for item in ordered if int(item["citation_count"]) == 0][:3]

    axis_phrase = {
        "比較": "比較検討",
        "料金": "料金説明",
        "事例": "導入事例",
        "FAQ": "導入前の疑問",
        "サポート": "運用サポート",
        "評判": "第三者評価",
        "導入不安": "導入時の不安",
        "手順": "導入手順",
    }
    visible_phrases = [axis_phrase.get(label, label) for label in visible_labels]
    weak_phrases = [axis_phrase.get(label, label) for label in weak_labels]

    lead_phrase = " / ".join(visible_phrases[:2]) if visible_phrases else ""
    weak_phrase = " / ".join(weak_phrases[:2]) if weak_phrases else ""
    summary = ""
    if visible_phrases and weak_phrases:
        summary = (
            f"{', '.join(visible_phrases[:2])} では自社URLが引用されやすく、"
            f"{', '.join(weak_phrases[:2])} はまだ外部サイトを見られやすい状態です。"
        )
    elif visible_phrases:
        summary = f"今回は {', '.join(visible_phrases[:2])} で自社URLが引用されやすい状態です。"
    elif weak_phrases:
        summary = f"今回は {', '.join(weak_phrases[:2])} でまだ外部サイトを見られやすい状態です。"

    short_summary = ""
    if lead_phrase and weak_phrase:
        short_summary = f"{lead_phrase} で強く、{weak_phrase} が次の改善候補です。"
    elif lead_phrase:
        short_summary = f"{lead_phrase} で自社URLが引用されやすい状態です。"
    elif weak_phrase:
        short_summary = f"{weak_phrase} がまだ弱く、外部サイトへ流れやすい状態です。"

    heatmap_rows: list[dict[str, Any]] = []
    focus_items: list[dict[str, Any]] = []
    top_axis = ordered[0] if ordered else None
    for item in ordered[:5]:
        trial_count = max(total_trial_count, 1)
        found_rate = round((float(item["found_count"]) / float(trial_count)) * 100.0, 1)
        citation_rate = round((float(item["citation_count"]) / float(trial_count)) * 100.0, 1)
        external_rate = round((float(item.get("external_count") or 0) / float(trial_count)) * 100.0, 1)
        axis_label = axis_phrase.get(str(item["label"]), str(item["label"]))
        short_label = short_axis_phrase.get(str(item["label"]), axis_label[:4] or axis_label)
        heatmap_rows.append(
            {
                "label": axis_label,
                "short_label": short_label,
                "cells": [
                    {"axis": "見つかる", "rate": found_rate, "rate_text": format_percent_compact(found_rate), "tone": "found"},
                    {"axis": "引用される", "rate": citation_rate, "rate_text": format_percent_compact(citation_rate), "tone": "cited"},
                    {"axis": "外部先行", "rate": external_rate, "rate_text": format_percent_compact(external_rate), "tone": "external"},
                ],
            }
        )
        if citation_rate >= max(found_rate, external_rate):
            status_label = "自社引用が強い"
        elif external_rate > max(found_rate, citation_rate):
            status_label = "外部先行が多い"
        else:
            status_label = "見つかるが引用は弱い"
        focus_items.append(
            {
                "label": axis_label,
                "status_label": status_label,
                "summary": f"観測した {trial_count} 試行のうち {int(item['citation_count'])} 回で自社URLが引用",
                "detail": (
                    f"見つかる {format_percent_compact(found_rate)} / "
                    f"引用される {format_percent_compact(citation_rate)} / "
                    f"外部先行 {format_percent_compact(external_rate)}"
                ),
            }
        )

    top_axis_basis_text = ""
    if top_axis and total_trial_count > 0:
        top_axis_label = axis_phrase.get(str(top_axis.get("label") or ""), str(top_axis.get("label") or ""))
        top_axis_citation_count = int(top_axis.get("citation_count") or 0)
        top_axis_basis_text = f"{top_axis_label} は観測した {total_trial_count} 試行のうち {top_axis_citation_count} 回で自社URLが引用されました。"

    return {
        "visible_labels": visible_labels,
        "weak_labels": weak_labels,
        "visible_phrases": visible_phrases,
        "weak_phrases": weak_phrases,
        "summary": summary,
        "short_summary": short_summary,
        "lead_phrase": lead_phrase,
        "weak_phrase": weak_phrase,
        "total_trial_count": total_trial_count,
        "total_question_count": total_trial_count,
        "top_axis_label": axis_phrase.get(str((top_axis or {}).get("label") or ""), str((top_axis or {}).get("label") or "")),
        "top_axis_basis_text": top_axis_basis_text,
        "basis_note": "ここに出す率と件数は、すべて同じ試行数ベースです。",
        "heatmap_rows": heatmap_rows,
        "focus_items": focus_items[:3],
    }


def build_evidence_reason_headline(stats: dict[str, Any], visibility_state: str, analysis_mode: str) -> str:
    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        if int(stats["self_cited"]) > 0:
            return "AIは今回は自社ページを主な根拠にして答えています"
        if int(stats["self_searched_only"]) > 0:
            return "自社ページは見つかっていますが、回答の根拠には使われていません"
        return "自社ページの根拠がまだ不足しています"
    if int(stats["self_cited"]) > 0 and int(stats["self_cited"]) >= max(int(stats["external_cited"]), int(stats["competitor_cited"])):
        if int(stats["external_cited"]) > 0 or int(stats["competitor_cited"]) > 0:
            return "AIは自社ページを主な根拠にしていますが、外部サイトも一部参照しています"
        return "AIは今回は自社ページを主な根拠にしています"
    if int(stats["external_cited"]) > max(int(stats["self_cited"]), int(stats["competitor_cited"]), 0):
        return "AIは今回は外部サイトを主に参考にしています"
    if int(stats["competitor_cited"]) > 0 and int(stats["self_cited"]) == 0:
        return "AIは比較対象や外部サイトを参考にしています"
    if int(stats["self_searched_only"]) > 0 and int(stats["self_cited"]) == 0:
        return "自社ページは見つかっていますが、今回は根拠には使われていません"
    if visibility_state == "自社あり":
        return "AIは自社も見ていますが、外部サイトも強く参照しています"
    if visibility_state == "未露出":
        return "AIは自社ページを回答根拠に使えていません"
    return "AIはまだ外部サイト寄りに答えています"


def build_evidence_reason_lines(stats: dict[str, Any], analysis_mode: str) -> list[str]:
    self_cited = int(stats["self_cited"])
    external_cited = int(stats["external_cited"])
    competitor_cited = int(stats["competitor_cited"])
    self_searched_only = int(stats["self_searched_only"])
    unknown_count = int(stats["status_totals"]["unknown"])

    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        if self_cited > 0:
            lines = ["今回は自社サイトの情報がそのまま回答の根拠に使われています。"]
            if self_searched_only > 0:
                lines.append("一部の自社ページは見つかっただけで終わっており、根拠に使われる形への補強余地があります。")
            return lines[:2]
        if self_searched_only > 0:
            return ["自社ページは見つかっていますが、今回は引用まで届かず根拠の中心になれていません。"]
        return ["今回は自社サイトだけで答える根拠が足りず、答えを置くページの追加が必要です。"]

    lines: list[str] = []
    if self_cited > 0 and external_cited == 0 and competitor_cited == 0:
        lines.append("今回は自社ページがそのまま判断材料になっています。")
    elif self_cited > 0:
        if self_cited >= max(external_cited, competitor_cited):
            lines.append("今回は自社ページが根拠の中心ですが、外部サイトも一部並走しています。")
        else:
            lines.append("今回は自社ページも引用されていますが、判断材料はまだ混在しています。")
    elif external_cited > 0 or competitor_cited > 0:
        lines.append("今回は自社ページではなく、外部サイトや比較対象が判断材料の中心です。")

    if self_searched_only > 0 and self_cited == 0:
        lines.append("自社ページは候補に出ていますが、今回は引用まで届いていません。")
    elif self_searched_only > 0:
        lines.append("一部の自社ページは見つかっただけで終わっており、引用される形への改善余地があります。")
    elif unknown_count > 0:
        lines.append("一部のURLは確認が必要な状態なので、引用状況は詳細欄で確認できます。")

    if lines:
        return lines[:2]
    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        return ["自社サイトだけで答える根拠がまだ弱く、追加の説明ページが必要です。"]
    return ["AI回答に使われた主要ソースはまだ少なく、まずは引用されるページを増やす必要があります。"]


def build_action_expectation(page_gap: dict[str, Any], stats: dict[str, Any]) -> str:
    page_type = str(page_gap.get("page_type_label") or "該当ページ")
    if int(stats["self_searched_only"]) > 0 and int(stats["self_cited"]) == 0:
        return f"{page_type}を補強すると、自社URLが見つかるだけの状態から、引用される状態へ上がりやすくなります。"
    if int(stats["external_cited"]) > int(stats["self_cited"]):
        return f"{page_type}を補強すると、外部サイトへ流れている根拠を自社へ戻しやすくなります。"
    if int(stats["competitor_cited"]) > 0:
        return f"{page_type}を補強すると、比較対象より先に自社が根拠として使われやすくなります。"
    return f"{page_type}を補強すると、この質問で自社が答えやすい状態に近づきます。"


def build_page_gap_card_copy(page_gap: dict[str, Any], visibility_state: str) -> dict[str, str]:
    page_type = str(page_gap.get("page_type_label") or "該当ページ")
    priority_label = str(page_gap.get("priority_label") or "")
    summary = str(page_gap.get("summary") or "").strip()

    if priority_label == "維持" and visibility_state == "自社優勢":
        return {
            "badge_label": "緊急判断なし",
            "urgent_label": "先に見る候補",
            "urgent_headline": "いまは大きな欠落なし",
            "urgent_summary": "今回は自社が先に見つかっており、先に大きく入れ替える候補は強く出ていません。",
            "followup_label": "次に強化すべき論点",
            "followup_headline": page_type,
            "followup_summary": (
                f"今回は自社が先に見つかっています。次に強化するなら {page_type} を厚くすると、"
                "この勝ち筋を維持しやすくなります。"
            ),
            "supporting_note": "今回すぐ埋める大きな欠落は強くありません。次の強化候補として見てください。",
        }
    if priority_label == "維持":
        return {
            "badge_label": "緊急判断なし",
            "urgent_label": "先に見る候補",
            "urgent_headline": "いまは大きな欠落なし",
            "urgent_summary": "直近では致命的な欠落より、まず現状維持で見てよい段階です。",
            "followup_label": "次に強化すべき論点",
            "followup_headline": page_type,
            "followup_summary": summary or f"{page_type} を厚くすると、この質問への答え方をさらに安定させやすくなります。",
            "supporting_note": "制作指示ではなく、勝ち筋を太くする補強候補として見てください。",
        }
    return {
        "badge_label": "優先判断あり",
        "urgent_label": "先に見る候補",
        "urgent_headline": page_type,
        "urgent_summary": summary or f"{page_type} を先に補うと、この質問で自社が答えやすくなります。",
        "followup_label": "次に強化すべき論点",
        "followup_headline": "優先候補を見た後で判断",
        "followup_summary": "まずは上のページを優先してください。今回の結果では、その次の強化候補を細かく分ける段階ではありません。",
        "supporting_note": f"この質問では {page_type} を先に補う判断です。",
    }


def resolve_primary_evidence_owner(stats: dict[str, Any], visibility_state: str, analysis_mode: str) -> str:
    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        return "self" if int(stats["self_cited"]) > 0 or int(stats["self_searched_only"]) > 0 else "external"
    self_cited = int(stats["self_cited"])
    external_cited = int(stats["external_cited"])
    competitor_cited = int(stats["competitor_cited"])
    if self_cited > 0 and self_cited >= max(external_cited, competitor_cited):
        return "self"
    if external_cited > 0 and external_cited >= max(self_cited, competitor_cited):
        return "external"
    if competitor_cited > 0:
        return "competitor"
    if int(stats["self_searched_only"]) > 0 or visibility_state in {"自社優勢", "自社あり"}:
        return "self"
    return "external"


def build_current_result_story(
    rollup_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    config: AppConfig,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
) -> dict[str, str]:
    if not rollup_rows:
        return {
            "question_label": "まだありません",
            "overall_label": "今回の結果は未作成",
            "overall_summary": "主結果 3 カードと同じく、ここにも最新の 1 質問だけを表示します。",
            "competition_label": "主要ソースは未作成",
            "competition_summary": "分析を実行すると、どのサイトやページが根拠に使われやすいかを表示します。",
            "action_headline": "次の改善は未判定",
            "action_summary": "分析を実行すると、優先候補と次に強化すべき論点を表示します。",
        }

    latest = rollup_rows[0]
    latest_payload = parse_json_object(latest.get("output_json"))
    selected_group_rows = find_group_rows(latest, raw_rows)
    aggregated_evidence = aggregate_url_evidence(selected_group_rows, source_loader, config) if source_loader else []
    evidence_stats = build_evidence_stats(aggregated_evidence)
    source_focus_summary = build_source_focus_summary(selected_group_rows, aggregated_evidence)
    topic_signals = build_topic_signal_summary(selected_group_rows, aggregated_evidence, config)
    analysis_context = latest_payload.get("analysis_context") or {}
    analysis_mode = resolve_analysis_mode(latest_payload)
    page_gap = infer_page_gap(
        str(latest.get("keyword_raw") or ""),
        latest_payload,
        brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
        target_hit=bool(latest.get("target_domain_hit")),
        brand_hit=bool(latest.get("brand_mention_hit")),
    )
    visibility_state = build_visibility_state_label(
        int(latest.get("visibility_score") or 0),
        bool(latest.get("target_domain_hit")),
        bool(latest.get("brand_mention_hit")),
    )
    verdict_summary = build_keyword_verdict_summary(latest, latest_payload)
    reason_headline = build_evidence_reason_headline(evidence_stats, visibility_state, analysis_mode)
    reason_lines = build_evidence_reason_lines(evidence_stats, analysis_mode)
    page_gap_card = build_page_gap_card_copy(page_gap, visibility_state)
    primary_metric = build_primary_metric_copy(latest)
    question_label = str(latest.get("keyword_raw") or "この質問")
    reason_summary = " ".join(reason_lines[:2]).strip()
    topic_summary = ""
    if topic_signals.get("answer_topics"):
        topic_summary = f"頻出論点は {', '.join(topic_signals['answer_topics'][:3])} です。"
    competition_summary = str(source_focus_summary["summary"] or "").strip() or topic_summary or reason_summary or reason_headline
    action_summary = (
        f"{page_gap_card['urgent_label']}: {page_gap_card['urgent_headline']}。 "
        f"{page_gap_card['followup_label']}: {page_gap_card['followup_headline']}。 "
        f"効く理由: {build_action_expectation(page_gap, evidence_stats)}"
    )

    return {
        "question_label": question_label,
        "overall_label": reason_headline,
        "overall_summary": (
            f"{' '.join(reason_lines[:1])} {primary_metric['story_summary']}"
            + (f" {topic_summary}" if topic_summary else "")
        ),
        "competition_label": "AI回答に使われた主要ソース",
        "competition_summary": competition_summary,
        "action_headline": page_gap_card["urgent_headline"],
        "action_summary": action_summary,
    }


def shorten_action_headline(action: str) -> str:
    text = str(action or "").strip()
    if not text:
        return "優先アクションなし"
    mapping = [
        ("比較", "比較ページを強化"),
        ("FAQ", "FAQを強化"),
        ("料金", "料金説明を補強"),
        ("事例", "導入事例を増やす"),
        ("LP", "LPを強化"),
        ("引用", "根拠を明記"),
        ("見直す", "既存ページを再確認"),
        ("追加", "追加ページを検討"),
    ]
    for needle, headline in mapping:
        if needle in text:
            return headline
    return text[:18] + ("…" if len(text) > 18 else "")


def shorten_question_label(keyword: str, limit: int = 18) -> str:
    text = " ".join(str(keyword or "").split())
    if not text:
        return "この質問"
    return text[:limit] + ("…" if len(text) > limit else "")


def format_scoped_action(keyword: str, action: str) -> str:
    label = shorten_question_label(keyword, limit=20)
    return f"「{label}」: {action}"


def build_scoped_action_headline(keyword: str, action: str) -> str:
    action_label = shorten_action_headline(action)
    keyword_label = shorten_question_label(keyword, limit=12)
    if not keyword or keyword_label == "この質問":
        return action_label
    return f"「{keyword_label}」で {action_label}"


def build_priority_actions(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    ordered: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        keyword = str(row.get("keyword_raw") or "").strip()
        payload = parse_json_object(row.get("output_json"))
        analysis_context = payload.get("analysis_context") or {}
        if payload.get("security_review_required"):
            page_gap = infer_page_gap(
                keyword,
                payload,
                brand_terms=analysis_context.get("brand_terms") or [],
                target_hit=bool(row.get("target_domain_hit")),
                brand_hit=bool(row.get("brand_mention_hit")),
            )
            fallback_action = str(page_gap.get("next_step") or "").strip()
            action_candidates = [fallback_action] if fallback_action else []
        else:
            action_candidates = [str(action or "").strip() for action in (payload.get("recommended_actions") or [])]
        for action in action_candidates:
            localized = str(action or "").strip()
            dedupe_key = (keyword, localized)
            if localized and dedupe_key not in seen:
                seen.add(dedupe_key)
                ordered.append(
                    {
                        "keyword": keyword,
                        "action": localized,
                        "headline": build_scoped_action_headline(keyword, localized),
                        "summary": format_scoped_action(keyword, localized),
                    }
                )
            if len(ordered) >= 3:
                return ordered
    return ordered


def build_intent_map_rows(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    latest_rows = get_latest_rows_by_keyword(rows)
    total_trial_count = sum(_resolve_row_trial_count(row) for row in latest_rows)
    stability_map = build_keyword_stability_map(rows)
    grouped: dict[str, dict[str, Any]] = {}

    for row in latest_rows:
        payload = parse_json_object(row.get("output_json"))
        analysis_context = payload.get("analysis_context") or {}
        intent = classify_keyword_intent(
            str(row.get("keyword_raw") or ""),
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
        )
        page_gap = infer_page_gap(
            str(row.get("keyword_raw") or ""),
            payload,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
            target_hit=bool(row.get("target_domain_hit")),
            brand_hit=bool(row.get("brand_mention_hit")),
        )
        verdict = build_visibility_state_label(
            int(row.get("visibility_score") or 0),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        key = intent["primary"]
        bucket = grouped.setdefault(
            key,
            {
                "intent_label": intent["label"],
                "question_count": 0,
                "trial_count": 0,
                "needs_fix_count": 0,
                "visible_count": 0,
                "score_total": 0,
                "stability_scores": [],
                "page_types": [],
                "keywords": [],
            },
        )
        trial_count = _resolve_row_trial_count(row)
        visible_trial_count = max(
            int(row.get("visible_trial_count") or 0),
            int(row.get("target_hit_count") or 0),
            trial_count if row.get("target_domain_hit") and trial_count == 1 else 0,
        )
        bucket["question_count"] += trial_count
        bucket["trial_count"] += trial_count
        bucket["score_total"] += int(row.get("visibility_score") or 0) * trial_count
        bucket["visible_count"] += visible_trial_count
        bucket["needs_fix_count"] += max(0, trial_count - visible_trial_count)
        bucket["page_types"].append(page_gap["page_type_label"])
        bucket["keywords"].append(shorten_question_label(str(row.get("keyword_raw") or ""), limit=14))
        stability = stability_map.get(normalize_text(str(row.get("keyword_raw") or "")), {})
        if stability:
            bucket["stability_scores"].append(float(stability.get("stability_score") or 0.0))

    intent_rows: list[dict[str, Any]] = []
    for item in grouped.values():
        avg_score = round(item["score_total"] / item["trial_count"], 1) if item["trial_count"] else 0.0
        avg_stability = round(sum(item["stability_scores"]) / len(item["stability_scores"]), 1) if item["stability_scores"] else 0.0
        if avg_stability >= 75:
            stability_label = "安定"
        elif avg_stability >= 50:
            stability_label = "やや揺れる"
        else:
            stability_label = "揺れ大"
        top_page_type = Counter(item["page_types"]).most_common(1)[0][0] if item["page_types"] else "-"
        urgency_score = item["needs_fix_count"] * 2 + max(0, item["trial_count"] - item["visible_count"])
        intent_rows.append(
            {
                "intent_label": item["intent_label"],
                "question_count": item["trial_count"],
                "trial_count": item["trial_count"],
                "total_question_count": total_trial_count,
                "total_trial_count": total_trial_count,
                "needs_fix_count": item["needs_fix_count"],
                "needs_fix_rate": round((item["needs_fix_count"] / total_trial_count) * 100.0, 1) if total_trial_count else 0.0,
                "needs_fix_rate_text": format_percent_compact(round((item["needs_fix_count"] / total_trial_count) * 100.0, 1) if total_trial_count else 0.0),
                "avg_score": avg_score,
                "stability_label": stability_label,
                "top_page_type": top_page_type,
                "sample_questions": " / ".join(dedupe_preserve_order(item["keywords"])[:2]) or "-",
                "urgency_score": urgency_score,
            }
        )

    return sorted(intent_rows, key=lambda row: (-row["urgency_score"], row["avg_score"], -row["question_count"]))


def build_page_gap_rows(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    latest_rows = get_latest_rows_by_keyword(rows)
    total_trial_count = sum(_resolve_row_trial_count(row) for row in latest_rows)
    grouped: dict[str, dict[str, Any]] = {}

    for row in latest_rows:
        payload = parse_json_object(row.get("output_json"))
        analysis_context = payload.get("analysis_context") or {}
        page_gap = infer_page_gap(
            str(row.get("keyword_raw") or ""),
            payload,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
            target_hit=bool(row.get("target_domain_hit")),
            brand_hit=bool(row.get("brand_mention_hit")),
        )
        verdict = build_visibility_state_label(
            int(row.get("visibility_score") or 0),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        key = page_gap["page_type_key"]
        bucket = grouped.setdefault(
            key,
            {
                "page_type_label": page_gap["page_type_label"],
                "gap_label": page_gap["gap_label"],
                "question_count": 0,
                "trial_count": 0,
                "needs_fix_count": 0,
                "priority_score": 0,
                "reasons": [],
                "next_steps": [],
                "keywords": [],
            },
        )
        trial_count = _resolve_row_trial_count(row)
        visible_trial_count = max(
            int(row.get("visible_trial_count") or 0),
            int(row.get("target_hit_count") or 0),
            trial_count if row.get("target_domain_hit") and trial_count == 1 else 0,
        )
        needs_fix_trial_count = max(0, trial_count - visible_trial_count)
        bucket["question_count"] += trial_count
        bucket["trial_count"] += trial_count
        bucket["reasons"].extend(page_gap["gap_reasons"])
        bucket["next_steps"].append(page_gap["next_step"])
        bucket["keywords"].append(shorten_question_label(str(row.get("keyword_raw") or ""), limit=14))
        if verdict in {"外部サイト優勢", "未露出"}:
            bucket["priority_score"] += trial_count * 2
        if not row.get("target_domain_hit"):
            bucket["priority_score"] += trial_count
        bucket["needs_fix_count"] += needs_fix_trial_count

    gap_rows: list[dict[str, Any]] = []
    for item in grouped.values():
        if item["priority_score"] >= 4:
            priority_label = "最優先"
        elif item["priority_score"] >= 2:
            priority_label = "優先"
        else:
            priority_label = "監視"
        next_step = Counter(item["next_steps"]).most_common(1)[0][0] if item["next_steps"] else "-"
        reasons = dedupe_preserve_order(item["reasons"])[:2]
        gap_rows.append(
            {
                "page_type_label": item["page_type_label"],
                "gap_label": item["gap_label"],
                "question_count": item["trial_count"],
                "trial_count": item["trial_count"],
                "total_question_count": total_trial_count,
                "total_trial_count": total_trial_count,
                "needs_fix_count": item["needs_fix_count"],
                "needs_fix_rate": round((item["needs_fix_count"] / total_trial_count) * 100.0, 1) if total_trial_count else 0.0,
                "needs_fix_rate_text": format_percent_compact(round((item["needs_fix_count"] / total_trial_count) * 100.0, 1) if total_trial_count else 0.0),
                "priority_label": priority_label,
                "reason_summary": " / ".join(reasons) if reasons else "-",
                "next_step": next_step,
                "sample_questions": " / ".join(dedupe_preserve_order(item["keywords"])[:2]) or "-",
                "priority_score": item["priority_score"],
            }
        )

    return sorted(gap_rows, key=lambda row: (-row["priority_score"], -row["question_count"], row["page_type_label"]))


def build_page_opportunity_strip_rows(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    short_label_map = {
        "比較ページ": "比較",
        "料金ページ": "料金",
        "FAQページ": "FAQ",
        "導入事例ページ": "事例",
        "地域ページ": "地域",
        "導入手順ページ": "導入手順",
        "指名検索ページ": "指名",
        "論点整理ページ": "論点整理",
    }
    state_label_map = {
        "urgent": "今すぐ",
        "followup": "次に強化",
        "maintain": "維持",
    }
    gap_rows = build_page_gap_rows(rows, config)
    strip_rows: list[dict[str, Any]] = []
    for row in gap_rows[:6]:
        priority_label = str(row.get("priority_label") or "")
        needs_fix_count = int(row.get("needs_fix_count") or 0)
        if priority_label == "最優先":
            state = "urgent"
        elif priority_label == "優先":
            state = "followup"
        elif needs_fix_count > 0:
            state = "followup"
        else:
            state = "maintain"
        strip_rows.append(
            {
                "label": short_label_map.get(str(row.get("page_type_label") or ""), str(row.get("page_type_label") or "")[:6]),
                "page_type_label": str(row.get("page_type_label") or "-"),
                "state": state,
                "state_label": state_label_map[state],
                "summary": str(row.get("reason_summary") or ""),
                "next_step": str(row.get("next_step") or ""),
                "question_count": int(row.get("question_count") or 0),
            }
        )
    return strip_rows


def build_portfolio_story(rows: list[dict[str, Any]], config: AppConfig) -> dict[str, Any]:
    latest_rows = get_latest_rows_by_keyword(rows)
    total_topics = len(latest_rows)
    total_trials = sum(_resolve_row_trial_count(row) for row in latest_rows)
    is_owned_only = config.analysis_mode == ANALYSIS_MODE_OWNED_ONLY
    if total_topics == 0:
        return {
            "overall_label": "AIの推薦先は未確認" if not is_owned_only else "監査前",
            "overall_summary": (
                "まだ分析結果がありません。まずは 1 回実行して、AIが誰を薦めるかを確認してください。"
                if not is_owned_only
                else "まだ自社監査の結果がありません。まずは 1 回実行して、自社サイトだけで答えられるかを確認してください。"
            ),
            "competition_label": "根拠は未確認" if not is_owned_only else "自社監査前",
            "competition_summary": (
                "結果ができると、どのURLや外部名が根拠として使われたかをここに出します。"
                if not is_owned_only
                else "自社監査では、どの自社URLが根拠になるかをここに出します。"
            ),
            "action_headline": "分析を実行" if not is_owned_only else "自社監査を実行",
            "action_summary": (
                "結果ができると、次に強化すべき候補をここに出します。"
                if not is_owned_only
                else "結果ができると、どの情報タイプが不足しているかをここに出します。"
            ),
            "priority_actions": [],
            "total_trials": 0,
            "visible_trials": 0,
            "competitor_trials": 0,
            "needs_fix_trials": 0,
            "third_party_trials": 0,
            "total_topics": 0,
            "visible_topics": 0,
            "competitor_topics": 0,
            "needs_fix_topics": 0,
            "third_party_topics": 0,
            "wins": 0,
            "ties": 0,
            "losses": 0,
        }

    wins = 0
    ties = 0
    losses = 0
    no_visibility = 0
    visible_topics = 0
    competitor_topics = 0
    third_party_topics = 0
    visible_trials = 0
    competitor_trials = 0
    third_party_trials = 0
    competitor_counter: Counter[str] = Counter()

    for row in latest_rows:
        payload = parse_json_object(row.get("output_json"))
        trial_count = _resolve_row_trial_count(row)
        visible_trial_count = max(
            int(row.get("visible_trial_count") or 0),
            int(row.get("target_hit_count") or 0),
            trial_count if row.get("target_domain_hit") and trial_count == 1 else 0,
        )
        verdict = build_visibility_state_label(
            int(row.get("visibility_score") or 0),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        if verdict == "自社優勢":
            wins += 1
        elif verdict == "自社あり":
            ties += 1
        elif verdict == "外部サイト優勢":
            losses += 1
        else:
            no_visibility += 1
        if row.get("target_domain_hit"):
            visible_topics += 1
        visible_trials += visible_trial_count
        competitors = extract_competitor_mentions(payload)
        if competitors:
            competitor_topics += 1
            competitor_trials += trial_count
            competitor_counter.update(competitors)
        if not row.get("target_domain_hit"):
            third_party_topics += 1
        third_party_trials += max(0, trial_count - visible_trial_count)

    needs_fix_topics = losses + no_visibility
    needs_fix_trials = max(0, total_trials - visible_trials)

    if is_owned_only:
        if visible_topics == total_topics and needs_fix_topics == 0:
            overall_label = "自社資産で回答可能"
            overall_summary = (
                f"観測した {total_trials} 試行では、自社サイトだけで答えられる回答がそろっています。"
                " 現状の情報設計で、Owned-only 監査は通過できています。"
            )
        elif visible_topics == 0:
            overall_label = "自社根拠不足"
            overall_summary = (
                f"観測した {total_trials} 試行では、自社サイトだけで根拠を返せた回答がまだありません。"
                " FAQ、比較、料金など答えを直接置くページの補強が必要です。"
            )
        else:
            overall_label = "一部は回答可能"
            overall_summary = (
                f"観測した {total_trials} 試行のうち {visible_trials} 回では自社サイトだけでも答えられますが、"
                f" {needs_fix_trials} 回はまだ不足しています。"
            )
    elif wins * 3 >= total_topics * 2 and needs_fix_topics == 0:
        overall_label = "AIは自社を薦めやすい"
        overall_summary = (
            f"観測した {total_trials} 試行のうち {visible_trials} 回で自社が根拠に入りました。"
            " 改善判断では、自社優位と見てよい状態です。"
        )
    elif no_visibility * 3 >= total_topics * 2:
        overall_label = "AIは自社を薦めていない"
        overall_summary = (
            f"観測した {total_trials} 試行のうち {needs_fix_trials} 回で自社URLも名称も十分に確認できていません。"
            " まずは露出を作るためのFAQや比較ページの補強が必要です。"
        )
    elif needs_fix_topics * 2 >= total_topics and wins == 0:
        overall_label = "AIは外部を薦めやすい"
        overall_summary = (
            f"観測した {total_trials} 試行のうち {needs_fix_trials} 回で自社が前に出ていません。"
            " 外部サイトに押し切られる試行がまだ多い状態です。"
        )
    else:
        overall_label = "AIは自社も薦めるが混在"
        overall_summary = (
            f"観測した {total_trials} 試行のうち {visible_trials} 回で自社の露出はあります。"
            " ただし、まだ外部サイトに押し切られる試行が残っています。"
        )

    top_competitors = [name for name, _count in competitor_counter.most_common(2)]
    configured_competitors = config.competitor_terms or []
    if is_owned_only:
        competition_label = "自社サイトだけで回答可能" if visible_topics else "自社サイトだけでは不足"
        competition_summary = (
            f"自社監査では {visible_trials}/{total_trials} 試行で自社URLが根拠に入りました。"
            f" まだ不足している試行は {needs_fix_trials} 回です。"
        )
    elif top_competitors:
        lead_name = " / ".join(top_competitors)
        if overall_label == "AIは自社を薦めやすい":
            competition_label = f"根拠には {lead_name} も混ざる"
        elif overall_label == "AIは自社も薦めるが混在":
            competition_label = f"根拠は {lead_name} と混在"
        else:
            competition_label = f"根拠は {lead_name} と外部寄り"
        competition_summary = (
            f"観測した {total_trials} 試行のうち {competitor_trials} 回で外部名や外部サイト名が根拠に入りました。"
            " どの試行で自社より外部が根拠を押さえたかを見て、次の強化候補を決める段階です。"
        )
    elif configured_competitors:
        competition_label = "比較対象名の出方は弱い"
        competition_summary = (
            "比較したい名前は設定されていますが、直近結果ではその名前の出現は強くありません。"
            f" 自社がまだ弱い試行は {needs_fix_trials} 回です。"
        )
    else:
        competition_label = "根拠は外部サイト寄り"
        competition_summary = (
            "比較したい名前が未設定のため、いまは自社と外部サイトの出方だけを見ています。"
            " 必要なら後から比較したい名前を追加できます。"
        )

    action_rows = sorted(
        latest_rows,
        key=lambda row: (
            {"未露出": 0, "外部サイト優勢": 1, "自社あり": 2, "自社優勢": 3}.get(
                build_visibility_state_label(
                    int(row.get("visibility_score") or 0),
                    bool(row.get("target_domain_hit")),
                    bool(row.get("brand_mention_hit")),
                ),
                9,
            ),
            row.get("keyword_raw") or "",
        ),
    )
    priority_actions = build_priority_actions(action_rows)
    first_action = priority_actions[0] if priority_actions else None
    action_headline = first_action["headline"] if first_action else "まずは分析を実行して負け筋を特定する"
    action_summary = " / ".join(item["summary"] for item in priority_actions[:3]) if priority_actions else "次に確認する点は結果作成後に表示されます。"

    return {
        "overall_label": overall_label,
        "overall_summary": overall_summary,
        "competition_label": competition_label,
        "competition_summary": competition_summary,
        "action_headline": action_headline,
        "action_summary": action_summary,
        "priority_actions": priority_actions,
        "total_trials": total_trials,
        "visible_trials": visible_trials,
        "competitor_trials": competitor_trials,
        "needs_fix_trials": needs_fix_trials,
        "third_party_trials": third_party_trials,
        "total_topics": total_topics,
        "visible_topics": visible_topics,
        "competitor_topics": competitor_topics,
        "needs_fix_topics": needs_fix_topics,
        "third_party_topics": third_party_topics,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "no_visibility": no_visibility,
    }
