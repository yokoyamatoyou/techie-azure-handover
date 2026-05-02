from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import unquote, urlsplit

from seo_aio_engine import SEOAIOAnalyzer, ScrapeBlockedError
from core.safe_fetch import UnsafeURLError, ContentTooLargeError, TooManyRedirectsError

from core.config import config
from core.evidence_pipeline import aggregate_legal_check_results
from core.application.faq_signal_profiles import (
    build_domain_profile,
    build_ec_guardrail,
    build_lmo_profile,
)
from core.storage.database import (
    get_history,
    get_previous_run,
    get_run_detail,
    init_database,
    save_analysis_run,
    save_crawl_pages,
    update_run_artifacts,
)
from core.term_glossary import get_all_faqs, get_ec_faq_templates
from core.token_encoder import encode_token_count, format_encoded_cost, format_encoded_tokens

RUNS_DIR = config.POC_OUTPUT_DIR / "runs"
SNAPSHOT_SCHEMA_VERSION = 7
TRANSIENT_RETRY_ATTEMPTS = 2
TRANSIENT_RETRY_DELAY_SECONDS = 1.0


@dataclass
class CompetitorAnalysisOutcome:
    results: Optional[Dict[str, Any]] = None
    action_advice: Optional[Dict[str, Any]] = None
    blocked: Optional[str] = None
    error: Optional[str] = None


_NON_RETRYABLE_ANALYSIS_EXCEPTIONS = (
    UnsafeURLError,
    ContentTooLargeError,
    TooManyRedirectsError,
    ScrapeBlockedError,
)


def _run_with_single_retry(
    action: Callable[[], Any],
    *,
    retry_label: str,
    max_attempts: int = TRANSIENT_RETRY_ATTEMPTS,
    retry_delay_seconds: float = TRANSIENT_RETRY_DELAY_SECONDS,
) -> Any:
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return action()
        except _NON_RETRYABLE_ANALYSIS_EXCEPTIONS:
            raise
        except Exception as exc:
            last_exc = exc
            if attempt >= max_attempts:
                break
            print(f"[WARNING] {retry_label} に失敗したため {retry_delay_seconds:.1f} 秒後に再試行します: {exc}")
            time.sleep(retry_delay_seconds)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"{retry_label} が失敗しました")


def execute_primary_analysis(
    analyzer: Any,
    url: str,
    industry_value: str,
    balance_value: int,
    deep_value: bool,
    platform_value: str,
    url_type_value: str,
    goal_value: str,
    progress_callback: Callable[[str, float, Optional[str]], None],
) -> Dict[str, Any]:
    def _analyze() -> Dict[str, Any]:
        return analyzer.analyze_url(
            url,
            industry_value,
            balance_value,
            deep_value,
            platform_value,
            False,
            url_type_selected=url_type_value,
            business_goal=goal_value,
            progress_callback=progress_callback,
        )

    return _run_with_single_retry(_analyze, retry_label="主分析")


def execute_competitor_analysis(
    competitor_url: str,
    industry_value: str,
    balance_value: int,
    deep_value: bool,
    goal_value: str,
    current_results: Optional[Dict[str, Any]],
    analyzer_factory: Callable[..., Any] = SEOAIOAnalyzer,
) -> CompetitorAnalysisOutcome:
    if not competitor_url:
        return CompetitorAnalysisOutcome()

    competitor_analyzer = analyzer_factory(analysis_mode="standard")
    try:
        competitor_results = _run_with_single_retry(
            lambda: competitor_analyzer.analyze_url(
                competitor_url,
                industry_value,
                balance_value,
                deep_value,
                business_goal=goal_value,
            ),
            retry_label="競合分析",
        )
        action_advice = None
        if competitor_results and current_results:
            try:
                action_advice = competitor_analyzer.generate_competitor_action_advice(
                    current_results,
                    competitor_results,
                    max_actions=5,
                )
                print(
                    "[INFO] Competitor advice generated: "
                    f"{len((action_advice or {}).get('actions', []))} actions"
                )
            except Exception as advice_exc:
                print(f"[WARNING] 競合アドバイス生成エラー: {advice_exc}")
        return CompetitorAnalysisOutcome(
            results=competitor_results,
            action_advice=action_advice,
        )
    except ScrapeBlockedError as exc:
        return CompetitorAnalysisOutcome(blocked=exc.reason)
    except Exception as exc:
        return CompetitorAnalysisOutcome(error=str(exc))


def _safe_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_inline_text(value: Any) -> str:
    text = _safe_text(value)
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text.lstrip(".… ").strip()


def _compact_marketer_excerpt(value: Any, *, limit: int = 120) -> str:
    text = _normalize_inline_text(value)
    if not text:
        return ""
    if len(text) <= limit:
        return text
    shortened = text[:limit]
    for delimiter in ("。", "、", ")", " "):
        cut = shortened.rfind(delimiter)
        if cut >= int(limit * 0.6):
            return shortened[: cut + (1 if delimiter != " " else 0)].strip() + "…"
    return shortened.rstrip() + "…"


def _extract_float(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return None


def _extract_int(pattern: str, text: str) -> Optional[int]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def _build_marketer_audit_summary(title: str, detail: str) -> str:
    normalized_title = _safe_text(title)
    normalized_detail = _normalize_inline_text(detail)
    lowered = normalized_detail.lower()
    if not normalized_title or not normalized_detail:
        return normalized_detail

    if normalized_title == "モバイル / ページ体験":
        lcp_ms = _extract_float(r"LCP\s*([0-9.]+)\s*ms", normalized_detail)
        cls_score = _extract_float(r"CLS\s*([0-9.]+)", normalized_detail)
        parts: List[str] = []
        if lcp_ms is not None:
            if lcp_ms <= 2500:
                parts.append("表示速度は概ね良好です")
            elif lcp_ms <= 4000:
                parts.append("表示速度はやや遅めです")
            else:
                parts.append("表示速度は遅めです")
        if cls_score is not None:
            if cls_score < 0.1:
                parts.append("画面のズレは小さめです")
            elif cls_score < 0.25:
                parts.append("画面のズレにやや改善余地があります")
            else:
                parts.append("画面のズレが大きめです")
        if parts:
            metric_bits = []
            if lcp_ms is not None:
                metric_bits.append(f"LCP {lcp_ms / 1000:.2f}秒")
            if cls_score is not None:
                metric_bits.append(f"CLS {cls_score:.3f}")
            return " / ".join(parts) + (f"（{' / '.join(metric_bits)}）" if metric_bits else "")

    if normalized_title == "リンク品質":
        empty_count = _extract_int(r"empty\s*=\s*([0-9]+)", normalized_detail)
        generic_count = _extract_int(r"generic\s*=\s*([0-9]+)", normalized_detail)
        image_alt_count = _extract_int(r"image_only_missing_alt\s*=\s*([0-9]+)", normalized_detail)
        crawlable_match = re.search(r"crawlable\s*=\s*([0-9]+)\s*/\s*([0-9]+)", normalized_detail, flags=re.IGNORECASE)
        parts: List[str] = []
        if crawlable_match:
            crawled = int(crawlable_match.group(1))
            total = int(crawlable_match.group(2))
            if total > 0 and crawled == total:
                parts.append("主要リンクはたどれる状態です")
            else:
                parts.append(f"リンクの到達性に抜けがあります（{crawled}/{total}）")
        if empty_count:
            parts.append(f"空のリンクが {empty_count} 件あります")
        if generic_count:
            parts.append(f"リンク文言が曖昧な箇所が {generic_count} 件あります")
        if image_alt_count:
            parts.append(f"画像リンクの代替テキスト不足が {image_alt_count} 件あります")
        if parts:
            return " / ".join(parts)

    if normalized_title == "内部リンク健全性":
        health_score = _extract_float(r"健康度\s*([0-9.]+)\s*点", normalized_detail)
        error_count = _extract_int(r"エラー\s*([0-9]+)\s*件", normalized_detail)
        canonical_count = _extract_int(r"canonical\s*([0-9]+)\s*件", normalized_detail)
        parts: List[str] = []
        if health_score is not None:
            if health_score >= 85:
                parts.append("内部リンク全体は概ね良好です")
            elif health_score >= 60:
                parts.append("内部リンクに改善余地があります")
            else:
                parts.append("内部リンクの見直しが必要です")
        if error_count:
            parts.append(f"リンク先エラーが {error_count} 件あります")
        if canonical_count:
            parts.append(f"canonical の不一致が {canonical_count} 件あります")
        if parts:
            return " / ".join(parts)

    if normalized_title == "国際化 / インデックス制御":
        parts: List[str] = []
        if "html lang missing" in lowered:
            parts.append("ページ言語の指定がありません")
        hreflang_count = _extract_int(r"hreflang\s*([0-9]+)\s*件", normalized_detail)
        if hreflang_count:
            parts.append(f"hreflang は {hreflang_count} 件あります")
        if "x-defaultなし" in normalized_detail:
            parts.append("多言語向けのデフォルト指定がありません")
        if "x-robots-tag なし" in lowered:
            parts.append("X-Robots-Tag は未設定です")
        if parts:
            return " / ".join(parts)

    if normalized_title == "OGP":
        parts: List[str] = []
        score = _extract_float(r"スコア\s*([0-9.]+)\s*点", normalized_detail)
        if score is not None:
            if score < 50:
                parts.append("SNSで共有したときの見え方が弱い状態です")
            else:
                parts.append("SNS共有の見え方に改善余地があります")
        if "画像" in normalized_detail:
            parts.append("共有画像や共有URLの設定確認が必要です")
        if parts:
            return " / ".join(parts)

    if normalized_title == "セキュリティ":
        if "https" in lowered and "未設定" in normalized_detail:
            return "HTTPS 自体は使えていますが、保護ヘッダーの追加設定に改善余地があります。"

    if normalized_title == "アクセシビリティ":
        parts: List[str] = []
        if "alt属性がありません" in normalized_detail:
            parts.append("画像の説明文が不足しています")
        if "リンク" in normalized_detail:
            parts.append("リンクの分かりやすさにも改善余地があります")
        if parts:
            return " / ".join(parts)

    if normalized_title == "構造化データ":
        detected = _extract_int(r"検出\s*([0-9]+)\s*種", normalized_detail)
        suggestions = _extract_int(r"追加候補\s*([0-9]+)\s*件", normalized_detail)
        parts: List[str] = []
        if detected:
            parts.append(f"構造化データは {detected} 種見つかっています")
        else:
            parts.append("構造化データは未整備です")
        if suggestions:
            parts.append(f"追加候補が {suggestions} 件あります")
        if "FAQPage なし" in normalized_detail:
            parts.append("FAQPage は未設定です")
        if parts:
            return " / ".join(parts)

    if normalized_title == "画像 / 動画の発見性":
        image_count = _extract_int(r"images\s*=\s*([0-9]+)", normalized_detail)
        discoverable_count = _extract_int(r"discoverable\s*=\s*([0-9]+)", normalized_detail)
        parts: List[str] = []
        if image_count is not None and discoverable_count is not None:
            parts.append(f"画像 {image_count} 点のうち、見つけやすい状態は {discoverable_count} 点です")
        if "image_sitemap=no" in lowered:
            parts.append("画像サイトマップは未設定です")
        if parts:
            return " / ".join(parts)

    return normalized_detail


def _json_clone(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=_json_default))
    except (TypeError, ValueError):
        return value


def _provider_status_label(status: Any) -> str:
    return {
        "pass": "通過",
        "warn": "注意",
        "fail": "要対応",
    }.get(_safe_text(status), "未判定")


def _normalize_status_code(status: Any, *, default: str = "reference") -> str:
    normalized = _safe_text(status).lower()
    if normalized in {"fail", "要対応"}:
        return "fail"
    if normalized in {"warn", "warning", "注意", "要確認"}:
        return "warn"
    if normalized in {"pass", "ok", "通過", "問題なし"}:
        return "pass"
    if normalized in {"reference", "info", "参考"}:
        return "reference"
    return default


def _snapshot_status_label(status: Any) -> str:
    return {
        "fail": "要対応",
        "warn": "注意",
        "pass": "通過",
        "reference": "参考",
    }.get(_normalize_status_code(status), "参考")


def _extract_legal_summary_items(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    legal_summary = results.get("legal_summary") or {}
    top_issues = [item for item in (legal_summary.get("top_issues") or []) if isinstance(item, dict)]

    def _build_marketer_copy(item: Dict[str, Any], *, default_severity: str) -> Dict[str, Any]:
        representative = item.get("representative") or {}
        phrase = _compact_marketer_excerpt(
            representative.get("text") or representative.get("matched_text"),
            limit=36,
        )
        category = _normalize_inline_text(representative.get("category") or item.get("category"))
        concern = _normalize_inline_text(
            representative.get("subtext")
            or representative.get("issue")
            or representative.get("reason")
            or item.get("title")
            or item.get("detail")
        )
        context = _compact_marketer_excerpt(
            item.get("evidence_summary")
            or representative.get("evidence")
            or representative.get("matched_text")
            or item.get("detail"),
            limit=140,
        )

        if phrase:
            title = f"表現「{phrase}」の確認"
        elif concern:
            title = concern
        elif category:
            title = f"{category}の確認"
        else:
            title = "表現・見せ方の確認"

        summary = concern or (f"{category}に関する確認候補" if category else "表現・見せ方の確認候補")
        if context and context != summary:
            detail = f"気になった点: {summary}\n周辺文脈: {context}"
        else:
            detail = summary or context

        return {
            "title": title,
            "summary": summary,
            "detail": detail,
            "severity": item.get("severity") or default_severity,
        }

    if top_issues:
        return [
            _build_marketer_copy(item, default_severity="warning")
            for item in top_issues
        ]

    fallback_items: List[Dict[str, Any]] = []
    severity_by_bucket = {
        "high_priority": "high",
        "medium_priority": "warning",
        "low_priority": "info",
    }
    for bucket in ("high_priority", "medium_priority", "low_priority"):
        for item in legal_summary.get(bucket) or []:
            if not isinstance(item, dict):
                continue
            fallback_items.append(
                _build_marketer_copy(
                    item,
                    default_severity=severity_by_bucket.get(bucket, "warning"),
                )
            )
    return fallback_items


def _calculate_legal_clarity_score(results: Dict[str, Any], legal_checks: Dict[str, Any]) -> int:
    score = 100
    is_ec = "EC" in str(((results or {}).get("url_type") or {}).get("effective", ""))

    premiums_status = ((legal_checks.get("premiums_labeling", {}) or {}).get("formatted", {}) or {}).get("status", "")
    if "要対応" in str(premiums_status):
        score -= 25
    elif "要確認" in str(premiums_status):
        score -= 12

    stealth_status = ((legal_checks.get("stealth_marketing", {}) or {}).get("formatted", {}) or {}).get("status", "")
    if "要対応" in str(stealth_status):
        score -= 20
    elif "要確認" in str(stealth_status):
        score -= 10

    commercial_status = ((legal_checks.get("commercial_transaction", {}) or {}).get("formatted", {}) or {}).get("status", "")
    if is_ec:
        if "要対応" in str(commercial_status):
            score -= 30
        elif "一部未記載" in str(commercial_status):
            score -= 18

    lawyer_report = ((legal_checks.get("consumer_protection", {}) or {}).get("lawyer_report", []) or [])
    high_count = len([item for item in lawyer_report if item.get("severity") == "high"])
    warning_count = len([item for item in lawyer_report if item.get("severity") == "warning"])
    score -= min(24, high_count * 6)
    score -= min(12, warning_count * 3)

    gate_status = ((results or {}).get("output_gate", {}) or {}).get("status", "")
    if gate_status == "block":
        score -= 18
    elif gate_status == "warn":
        score -= 8

    return max(0, min(100, int(round(score))))


def _resolve_legal_score(results: Dict[str, Any], integrated: Dict[str, Any]) -> int:
    legal_score = _safe_int(integrated.get("legal_score"))
    if legal_score > 0:
        return legal_score
    legal_checks = results.get("legal_checks", {}) or {}
    if not legal_checks:
        return legal_score
    return _calculate_legal_clarity_score(results, legal_checks)


def _merge_status_codes(*statuses: Any) -> str:
    normalized = [_normalize_status_code(status, default="reference") for status in statuses if _safe_text(status)]
    if "fail" in normalized:
        return "fail"
    if "warn" in normalized:
        return "warn"
    if "pass" in normalized:
        return "pass"
    return "reference"


def _task_priority_for_index(index: int) -> str:
    if index < 3:
        return "高"
    if index < 8:
        return "中"
    return "低"


def _get_provider_readiness(results: Dict[str, Any]) -> Dict[str, Any]:
    aio_results = results.get("aio_results") or {}
    return aio_results.get("provider_readiness") or (aio_results.get("details") or {}).get("provider_readiness") or {}


def _priority_level(*, integrated_score: int, total_issues: int) -> str:
    if total_issues >= 8 or integrated_score < 45:
        return "高"
    if total_issues >= 4 or integrated_score < 70:
        return "中"
    return "低"


def _fallback_integrated_score(*, seo_score: int, aio_score: int, legal_score: int) -> int:
    return round((seo_score + aio_score) / 2)


def _resolve_run_integrated_score(
    run_row: Optional[Dict[str, Any]],
    *,
    fallback_seo: int = 0,
    fallback_aio: int = 0,
    fallback_legal: int = 0,
) -> int:
    if not run_row:
        return _fallback_integrated_score(
            seo_score=fallback_seo,
            aio_score=fallback_aio,
            legal_score=fallback_legal,
        )

    result_path_raw = _safe_text(run_row.get("result_path"))
    if result_path_raw:
        try:
            result_payload = json.loads(Path(result_path_raw).read_text(encoding="utf-8"))
            value = ((result_payload or {}).get("integrated_results") or {}).get("integrated_score")
            if value is not None:
                return _safe_int(value)
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    snapshot_raw = run_row.get("snapshot_json")
    if snapshot_raw:
        try:
            snapshot = snapshot_raw if isinstance(snapshot_raw, dict) else json.loads(str(snapshot_raw))
            header = (snapshot or {}).get("header") or {}
            value = header.get("integrated_score")
            if value is not None:
                return _safe_int(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    return _fallback_integrated_score(
        seo_score=_safe_int(run_row.get("seo_score", fallback_seo)),
        aio_score=_safe_int(run_row.get("aio_score", fallback_aio)),
        legal_score=_safe_int(run_row.get("legal_score", fallback_legal)),
    )


def _extract_previous_diff(
    previous_run: Optional[Dict[str, Any]],
    *,
    integrated_score: int,
    seo_score: int,
    aio_score: int,
    legal_score: int,
) -> Dict[str, Any]:
    if not previous_run:
        return {"label": "前回なし", "integrated_diff": None}

    prev_seo = _safe_int(previous_run.get("seo_score"))
    prev_aio = _safe_int(previous_run.get("aio_score"))
    prev_legal = _safe_int(previous_run.get("legal_score"))
    prev_integrated = _resolve_run_integrated_score(
        previous_run,
        fallback_seo=prev_seo,
        fallback_aio=prev_aio,
        fallback_legal=prev_legal,
    )
    diff = integrated_score - prev_integrated
    return {
        "label": f"{diff:+d}",
        "integrated_diff": diff,
        "seo_diff": seo_score - prev_seo,
        "aio_diff": aio_score - prev_aio,
        "legal_diff": legal_score - prev_legal,
        "previous_run_id": previous_run.get("id"),
        "previous_analyzed_at": previous_run.get("analyzed_at"),
    }


def _build_priority_actions(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []

    business_actions = ((results.get("deep_recommendations") or {}).get("business") or [])[:6]
    for rec in business_actions:
        title = _safe_text(rec.get("title")) or "改善提案"
        action = _safe_text(rec.get("recommended_action")) or _safe_text(rec.get("current_issue"))
        if not action:
            continue
        actions.append(
            {
                "area": "AI認識改善",
                "label": "対象ページで確認",
                "title": title,
                "action": action,
                "detail": _safe_text(rec.get("expected_impact")),
                "role": "運用",
                "effort": "0.5-2h",
                "kpi": "AI認識",
                "impact": _safe_text(rec.get("expected_impact")),
            }
        )

    seo_actions = (results.get("seo_results") or {}).get("immediate_actions") or []
    for rec in seo_actions[:6]:
        if isinstance(rec, dict):
            title = _safe_text(rec.get("title")) or "SEO改善"
            action = _safe_text(rec.get("action")) or _safe_text(rec.get("detail"))
            detail = _safe_text(rec.get("impact"))
        else:
            title = "SEO改善"
            action = _safe_text(rec)
            detail = ""
        if not action:
            continue
        actions.append(
            {
                "area": "SEO改善",
                "label": "対象ページで確認",
                "title": title,
                "action": action,
                "detail": detail,
                "role": "運用",
                "effort": "0.5-2h",
                "kpi": "SEO",
                "impact": detail,
            }
        )

    aio_actions = (results.get("aio_results") or {}).get("immediate_actions") or []
    for rec in aio_actions[:6]:
        if isinstance(rec, dict):
            title = _safe_text(rec.get("action")) or "AI検索向け改善"
            action = _safe_text(rec.get("method")) or title
            detail = _safe_text(rec.get("reason"))
        else:
            title = "AI検索向け改善"
            action = _safe_text(rec)
            detail = ""
        if not action:
            continue
        actions.append(
            {
                "area": "AI認識改善",
                "label": "対象ページで確認",
                "title": title[:64],
                "action": action,
                "detail": detail,
                "role": "運用",
                "effort": "1-3h",
                "kpi": "AI認識",
                "impact": detail,
            }
        )

    technical_actions = ((results.get("deep_recommendations") or {}).get("technical") or [])[:6]
    for rec in technical_actions:
        title = _safe_text(rec.get("title")) or "技術改善"
        action = _safe_text(rec.get("implementation")) or _safe_text(rec.get("current_issue"))
        if not action:
            continue
        actions.append(
            {
                "area": "技術補足",
                "label": "対象ページで確認",
                "title": title,
                "action": action,
                "detail": _safe_text(rec.get("expected_impact")),
                "role": "エンジニア",
                "effort": "1-4h",
                "kpi": "技術品質",
                "impact": _safe_text(rec.get("expected_impact")),
            }
        )

    deduped: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in actions:
        key = (item["area"], item["title"], item["action"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _build_provider_status_rows(results: Dict[str, Any]) -> List[Dict[str, str]]:
    provider_readiness = _get_provider_readiness(results)
    rows = []
    for label, key in (
        ("Google", "google"),
        ("OpenAI Search", "openai_search"),
        ("Perplexity", "perplexity"),
        ("Claude Search", "claude_search"),
    ):
        status = _safe_text((provider_readiness.get(key) or {}).get("status"))
        mapped = _provider_status_label(status)
        summary = "" if status == "pass" else _safe_text((provider_readiness.get(key) or {}).get("summary"))
        rows.append({"label": label, "status": mapped, "summary": summary})
    return rows


def _build_rewrites(results: Dict[str, Any]) -> List[Dict[str, str]]:
    deep = results.get("deep_recommendations") or {}
    basics = (results.get("seo_results") or {}).get("basics") or {}
    rewrites: List[Dict[str, str]] = []

    current_title = _safe_text(basics.get("title"))
    for candidate in (deep.get("title_rewrites") or [])[:2]:
        rewrites.append(
            {
                "kind": "タイトル",
                "label": "対象ページで確認",
                "current": current_title,
                "proposed": _safe_text(candidate),
            }
        )

    current_desc = _safe_text(basics.get("meta_description"))
    for candidate in (deep.get("description_rewrites") or [])[:2]:
        rewrites.append(
            {
                "kind": "ディスクリプション",
                "label": "対象ページで確認",
                "current": current_desc,
                "proposed": _safe_text(candidate),
            }
        )

    return rewrites


def _brief_texts(items: Any, *, keys: tuple[str, ...], limit: int = 3) -> List[str]:
    texts: List[str] = []
    if not isinstance(items, list):
        return texts
    for item in items:
        text = ""
        if isinstance(item, dict):
            for key in keys:
                text = _safe_text(item.get(key))
                if text:
                    break
        else:
            text = _safe_text(item)
        if not text or text in texts:
            continue
        texts.append(text)
        if len(texts) >= limit:
            break
    return texts


def _score_status(score: float, *, good: float, warn: float) -> str:
    if score >= good:
        return "pass"
    if score >= warn:
        return "warn"
    return "fail"


def _build_llms_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    aio_results = results.get("aio_results") or {}
    llms_payload = aio_results.get("llms_txt") or {}
    if not isinstance(llms_payload, dict):
        llms_payload = {}

    exists = bool(llms_payload.get("exists"))
    found_paths = [str(path).strip() for path in (llms_payload.get("found_paths") or []) if str(path).strip()]
    checked_paths = [str(path).strip() for path in (llms_payload.get("checked_paths") or []) if str(path).strip()]
    quality_score = _safe_int(llms_payload.get("quality_score"))
    quality_level = _safe_text(llms_payload.get("quality_level"))
    issues = _brief_texts(llms_payload.get("quality_issues") or [], keys=("issue",), limit=4)
    recommendations = _brief_texts(llms_payload.get("quality_recommendations") or [], keys=("recommendation",), limit=4)

    if exists:
        status = "pass"
        if quality_score and quality_score < 80:
            status = "warn"
        elif issues:
            status = "warn"
        detail_bits = ["設置済み"]
        if quality_score > 0:
            detail_bits.append(f"品質 {quality_score}点")
        if quality_level:
            detail_bits.append(f"判定 {quality_level}")
        if found_paths:
            detail_bits.append(f"検出: {', '.join(found_paths[:2])}")
        lead = issues[0] if issues else (recommendations[0] if recommendations else "")
        if lead:
            detail_bits.append(lead)
        detail = " / ".join([bit for bit in detail_bits if bit])
        title = "AI向け案内ファイル（llms.txt / 任意）"
    else:
        detail = "未設置です。必須ではありませんが、AI向け案内として運用するなら `/llms.txt` を推奨します。"
        if checked_paths:
            detail = f"{detail} 確認先: {', '.join(checked_paths[:3])}"
        status = "reference"
        title = "AI向け案内ファイル（llms.txt / 任意）"

    return {
        "title": title,
        "detail": detail,
        "status": status,
        "status_label": _snapshot_status_label(status),
        "exists": exists,
        "quality_score": quality_score,
        "quality_level": quality_level,
        "found_paths": found_paths,
        "checked_paths": checked_paths,
        "issues": issues,
        "recommendations": recommendations,
    }


def _build_llms_notes(results: Dict[str, Any]) -> List[Dict[str, str]]:
    summary = _build_llms_summary(results)
    notes = [
        {
            "title": _safe_text(summary.get("title")),
            "detail": _safe_text(summary.get("detail")),
            "label": "対象ページで確認",
        }
    ]
    recommendations = summary.get("recommendations") or []
    if recommendations:
        notes.append(
            {
                "title": "llms.txt 改善メモ",
                "detail": " / ".join(recommendations[:2]),
                "label": "対象ページで確認",
            }
        )
    return [item for item in notes if _safe_text(item.get("detail"))]


def _build_reference_notes(results: Dict[str, Any]) -> List[Dict[str, str]]:
    platform_guidance = results.get("platform_guidance") or {}
    references: List[Dict[str, str]] = []
    for step in (platform_guidance.get("business_steps") or [])[:3]:
        references.append({"title": "運用ガイド", "detail": _safe_text(step), "label": "参考"})
    for step in (platform_guidance.get("technical_steps") or [])[:3]:
        references.append({"title": "技術ガイド", "detail": _safe_text(step), "label": "参考"})
    for link in (platform_guidance.get("help_links") or [])[:3]:
        references.append(
            {
                "title": _safe_text(link.get("label")) or "公式ドキュメント",
                "detail": _safe_text(link.get("url")),
                "label": "参考",
            }
        )
    return references


def _build_crawl_scope_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    sitemap_info = results.get("sitemap_info") or {}
    crawl_strategy = results.get("crawl_strategy") or {}
    priority_pages_crawled = results.get("priority_pages_crawled") or {}
    link_health = results.get("link_health_report") or {}

    total_urls = _safe_int(sitemap_info.get("total_urls"))
    sampled_count = _safe_int(sitemap_info.get("sampled_count"))
    update_frequency = _safe_text(sitemap_info.get("update_frequency"))
    parsed_sitemaps = _safe_int(sitemap_info.get("parsed_sitemaps"))
    warning = _safe_text(sitemap_info.get("warning"))
    error = _safe_text(sitemap_info.get("error"))
    source_sitemaps = [
        _safe_text(item)
        for item in (sitemap_info.get("source_sitemaps") or [])[:5]
        if _safe_text(item)
    ]
    priority_pages = [
        item for item in (priority_pages_crawled.get("pages") or []) if isinstance(item, dict)
    ]
    priority_candidates = crawl_strategy.get("priority_candidates") or crawl_strategy.get("priority_pages") or []
    audited_targets = _safe_int(link_health.get("audited_target_count"))

    detail_bits: List[str] = []
    if total_urls > 0:
        detail_bits.append(f"sitemap {total_urls:,}URL")
    if sampled_count > 0:
        detail_bits.append(f"サンプル {sampled_count:,}URL")
    if priority_pages:
        detail_bits.append(f"優先ページ取得 {len(priority_pages)}件")
    elif priority_candidates:
        detail_bits.append(f"優先候補 {len(priority_candidates)}件")
    if audited_targets > 0:
        detail_bits.append(f"内部リンク先監査 {audited_targets}件")
    if update_frequency and update_frequency != "不明":
        detail_bits.append(f"更新頻度 {update_frequency}")

    status = "warn" if warning or error else "reference"
    detail = " / ".join(detail_bits)
    if error and not detail:
        detail = error
    elif warning:
        detail = f"{detail} / {warning}" if detail else warning

    return {
        "title": "クロール範囲",
        "detail": detail or "sitemap と優先ページ取得の情報はありません。",
        "status": status,
        "status_label": _snapshot_status_label(status),
        "sitemap_total_urls": total_urls,
        "sampled_count": sampled_count,
        "update_frequency": update_frequency,
        "parsed_sitemaps": parsed_sitemaps,
        "warning": warning,
        "error": error,
        "priority_pages_fetched": len(priority_pages),
        "priority_pages_planned": len(priority_candidates),
        "priority_pages": _json_clone(priority_pages[:6]) or [],
        "source_sitemaps": source_sitemaps,
        "audited_target_count": audited_targets,
    }


def _build_link_health_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    internal_summary = results.get("internal_link_summary") or {}
    link_health = results.get("link_health_report") or {}
    if not isinstance(internal_summary, dict):
        internal_summary = {}
    if not isinstance(link_health, dict):
        link_health = {}
    if not internal_summary and not link_health:
        return {}

    health_score = float(link_health.get("health_score", 0.0) or 0.0)
    diagnosis = _safe_text(link_health.get("diagnosis"))
    known_pages = _safe_int(link_health.get("total_known_pages") or internal_summary.get("total_pages"))
    analyzed_pages = _safe_int(link_health.get("total_analyzed_pages") or internal_summary.get("total_pages"))
    orphan_count = _safe_int(link_health.get("orphan_count") or internal_summary.get("orphan_count"))
    low_link_count = _safe_int(link_health.get("low_link_count") or internal_summary.get("low_link_count"))
    avg_depth = float(link_health.get("avg_depth", 0.0) or 0.0)
    audited_targets = _safe_int(link_health.get("audited_target_count"))
    broken_count = _safe_int(link_health.get("broken_target_count"))
    redirected_count = _safe_int(link_health.get("redirected_target_count"))
    canonical_count = _safe_int(link_health.get("canonical_mismatch_count"))
    noindex_count = _safe_int(link_health.get("noindex_target_count"))

    if broken_count > 0 or health_score < 50:
        status = "fail"
    elif redirected_count > 0 or canonical_count > 0 or noindex_count > 0 or orphan_count > 0 or low_link_count > 0 or health_score < 80:
        status = "warn"
    else:
        status = "pass"

    detail_bits: List[str] = []
    if health_score > 0:
        detail_bits.append(f"健康度 {health_score:.0f}点")
    if known_pages > 0:
        detail_bits.append(f"把握 {known_pages}ページ")
    if audited_targets > 0:
        detail_bits.append(f"監査 {audited_targets}件")
    issue_bits: List[str] = []
    if broken_count > 0:
        issue_bits.append(f"エラー {broken_count}件")
    if orphan_count > 0:
        issue_bits.append(f"孤立 {orphan_count}件")
    if redirected_count > 0:
        issue_bits.append(f"リダイレクト {redirected_count}件")
    if canonical_count > 0:
        issue_bits.append(f"canonical {canonical_count}件")
    if noindex_count > 0:
        issue_bits.append(f"noindex {noindex_count}件")
    if low_link_count > 0 and not issue_bits:
        issue_bits.append(f"薄いリンク {low_link_count}件")
    if issue_bits:
        detail_bits.append(" / ".join(issue_bits[:3]))
    elif diagnosis:
        detail_bits.append(diagnosis)

    return {
        "title": "内部リンク健全性",
        "detail": " / ".join([bit for bit in detail_bits if bit]) or "内部リンクの追加情報はありません。",
        "status": status,
        "status_label": _snapshot_status_label(status),
        "score": round(health_score, 1),
        "health_score": round(health_score, 1),
        "diagnosis": diagnosis,
        "total_known_pages": known_pages,
        "total_analyzed_pages": analyzed_pages,
        "orphan_count": orphan_count,
        "low_link_count": low_link_count,
        "avg_depth": round(avg_depth, 2),
        "audited_target_count": audited_targets,
        "broken_target_count": broken_count,
        "redirected_target_count": redirected_count,
        "canonical_mismatch_count": canonical_count,
        "noindex_target_count": noindex_count,
        "hub_pages": _json_clone(link_health.get("hub_pages") or []) or [],
        "broken_targets": _json_clone(link_health.get("broken_targets") or []) or [],
        "redirected_targets": _json_clone(link_health.get("redirected_targets") or []) or [],
        "canonical_mismatches": _json_clone(link_health.get("canonical_mismatches") or []) or [],
        "noindex_targets": _json_clone(link_health.get("noindex_targets") or []) or [],
        "orphan_pages": _json_clone((internal_summary.get("orphan_pages") or [])[:5]) or [],
        "low_link_pages": _json_clone((internal_summary.get("low_link_pages") or [])[:5]) or [],
    }


def _build_site_health_checks(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    site_health = results.get("site_health") or {}
    if not isinstance(site_health, dict):
        site_health = {}

    checks: List[Dict[str, Any]] = []
    definitions = (
        ("ogp", "OGP", 80.0, 50.0),
        ("security", "セキュリティ", 70.0, 40.0),
        ("accessibility", "アクセシビリティ", 80.0, 50.0),
    )
    for key, title, pass_threshold, warn_threshold in definitions:
        payload = site_health.get(key) or {}
        formatted = payload.get("formatted") or {}
        if not isinstance(formatted, dict) or not formatted:
            continue

        score = float(formatted.get("score", 0.0) or 0.0)
        status = _score_status(score, good=pass_threshold, warn=warn_threshold)
        wcag_level = _safe_text(formatted.get("wcag_level"))
        detail_bits = [f"スコア {score:.0f}点"]
        formatted_status = _safe_text(formatted.get("status"))
        if formatted_status:
            detail_bits.append(formatted_status)
        if wcag_level:
            detail_bits.append(wcag_level)

        highlights = _brief_texts(formatted.get("items") or [], keys=("subtext", "text"), limit=3)
        if not highlights:
            highlights = _brief_texts(formatted.get("recommendations") or [], keys=("recommendation",), limit=3)
        if not highlights:
            highlights = _brief_texts(formatted.get("issues") or [], keys=("issue", "suggestion"), limit=3)
        if highlights:
            detail_bits.append(highlights[0])

        checks.append(
            {
                "key": key,
                "title": title,
                "detail": " / ".join([bit for bit in detail_bits if bit]),
                "status": status,
                "status_label": _snapshot_status_label(status),
                "score": round(score, 1),
                "wcag_level": wcag_level,
                "highlights": highlights,
                "items": _json_clone((formatted.get("items") or [])[:6]) or [],
                "recommendations": _brief_texts(formatted.get("recommendations") or [], keys=("recommendation",), limit=4),
                "issues": _brief_texts(formatted.get("issues") or [], keys=("issue", "suggestion"), limit=4),
            }
        )
    return checks


def _build_seo_audit_notes(results: Dict[str, Any]) -> List[Dict[str, str]]:
    seo_results = results.get("seo_results") or {}
    technical = seo_results.get("technical") or {}
    structure = seo_results.get("structure") or {}
    web_vitals = seo_results.get("web_vitals") or {}
    provider_readiness = _get_provider_readiness(results)
    special_notes = provider_readiness.get("special_notes") or {}

    notes: List[Dict[str, str]] = []

    def append_note(
        title: str,
        detail: str,
        *,
        status: Any,
        group: str = "action",
        source: str = "measured",
        source_label: str = "実データ",
    ) -> None:
        text = _safe_text(detail)
        if not text:
            return
        status_code = _normalize_status_code(status)
        notes.append(
            {
                "title": title,
                "detail": text,
                "summary": _build_marketer_audit_summary(title, text),
                "label": source_label,
                "status": status_code,
                "status_label": _snapshot_status_label(status_code),
                "group": group,
                "source": source,
                "source_label": source_label,
            }
        )

    international = technical.get("international_targeting") or {}
    x_robots = technical.get("x_robots_tag") or {}
    if international or x_robots:
        detail_bits = []
        if international:
            detail_bits.append(_safe_text(international.get("summary")))
        if x_robots:
            detail_bits.append(_safe_text(x_robots.get("summary")))
        append_note(
            "国際化 / インデックス制御",
            " / ".join([bit for bit in detail_bits if bit]),
            status=_merge_status_codes(international.get("status"), x_robots.get("status")),
        )

    mobile = technical.get("mobile_parity") or {}
    page_experience = technical.get("page_experience") or {}
    lcp_ms = web_vitals.get("lcp_ms")
    cls_score = web_vitals.get("cls_score")
    if mobile or page_experience:
        vitals_bits = []
        if lcp_ms is not None:
            vitals_bits.append(f"LCP {float(lcp_ms):.0f}ms")
        if cls_score is not None:
            vitals_bits.append(f"CLS {float(cls_score):.3f}")
        detail = _safe_text(page_experience.get("summary"))
        if vitals_bits:
            detail = " / ".join(vitals_bits + ([detail] if detail else []))
        append_note(
            "モバイル / ページ体験",
            detail,
            status=_merge_status_codes(mobile.get("status"), page_experience.get("status")),
        )

    link_quality = structure.get("link_quality") or {}
    append_note(
        "リンク品質",
        _safe_text(link_quality.get("summary")),
        status=link_quality.get("status"),
    )

    media = technical.get("media_discovery") or {}
    append_note(
        "画像 / 動画の発見性",
        _safe_text(media.get("summary")),
        status=media.get("status"),
    )

    link_health_summary = _build_link_health_summary(results)
    append_note(
        _safe_text(link_health_summary.get("title")),
        _safe_text(link_health_summary.get("detail")),
        status=link_health_summary.get("status"),
    )

    schema_summary = _build_schema_summary(results)
    append_note(
        "構造化データ",
        _safe_text(schema_summary.get("detail")),
        status=schema_summary.get("status"),
    )

    for check in _build_site_health_checks(results):
        append_note(
            _safe_text(check.get("title")),
            _safe_text(check.get("detail")),
            status=check.get("status"),
        )

    openai_commerce = special_notes.get("openai_commerce") or {}
    append_note(
        "OpenAI Commerce",
        _safe_text(openai_commerce.get("summary")),
        status=openai_commerce.get("status"),
        group="reference" if _normalize_status_code(openai_commerce.get("status")) == "pass" else "action",
    )

    perplexity_note = special_notes.get("perplexity_operational") or {}
    append_note(
        "Perplexity WAF / IP",
        _safe_text(perplexity_note.get("summary")),
        status=perplexity_note.get("status") or "reference",
        group="reference",
    )

    status_priority = {"fail": 0, "warn": 1, "pass": 2, "reference": 3}
    filtered = sorted(
        [note for note in notes if _safe_text(note.get("detail"))],
        key=lambda note: (
            status_priority.get(_safe_text(note.get("status")), 9),
            _safe_text(note.get("title")),
        ),
    )[:10]
    if filtered:
        return filtered
    return [
        {
            "title": "この保存済みrunは旧データです",
            "detail": "追加監査前の保存データです。再分析すると、モバイル / ページ体験、OpenAI Commerce、Perplexity WAF / IP などの最新監査を実データで表示できます。",
            "label": "旧データ",
            "status": "warn",
            "status_label": "再分析で詳細化",
            "group": "refresh",
            "source": "legacy_fallback",
            "source_label": "旧データ",
        }
    ]


def _contains_any(text: str, keywords: List[str]) -> bool:
    normalized = _safe_text(text).lower()
    return any(keyword.lower() in normalized for keyword in keywords)


def _collect_keyword_hits(text: str, keywords: List[str]) -> List[str]:
    normalized = _safe_text(text).lower()
    hits: List[str] = []
    for keyword in keywords:
        label = _safe_text(keyword)
        if not label:
            continue
        if label.lower() in normalized and label not in hits:
            hits.append(label)
    return hits


def _safe_text_list(values: Any, *, limit: int = 6) -> List[str]:
    normalized: List[str] = []
    for value in values or []:
        text = _safe_text(value)
        if text and text not in normalized:
            normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def _read_context_value(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _clean_page_focus(text: Any) -> str:
    normalized = _safe_text(text)
    if not normalized:
        return ""
    head = re.split(r"[|｜:：/\-‐–—・]", normalized, maxsplit=1)[0].strip()
    head = re.sub(r"\s+", " ", head)
    if head.lower() in {"home", "top", "トップ"}:
        return ""
    return head


def _extract_url_signal_tokens(url: Any) -> List[str]:
    raw = _safe_text(url)
    if not raw:
        return []
    try:
        parsed = urlsplit(raw)
    except Exception:
        parsed = None

    parts: List[str] = []
    if parsed:
        parts.extend(str(parsed.netloc or "").split("."))
        path = unquote(str(parsed.path or ""))
        parts.extend(re.split(r"[/_.\-]+", path))
    else:
        parts.extend(re.split(r"[/_.:\-]+", raw))

    stopwords = {
        "", "www", "http", "https", "com", "jp", "co", "net", "org", "html", "htm", "php",
        "index", "page", "pages", "post", "posts", "entry", "service", "services", "product",
        "products", "item", "items", "category", "categories", "blog", "news", "article", "lp",
    }
    tokens: List[str] = []
    for part in parts:
        token = _safe_text(part).strip().lower()
        if not token or token in stopwords or token.isdigit() or len(token) <= 1:
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens


def _collect_faq_context(results: Dict[str, Any]) -> Dict[str, Any]:
    legal_summary = results.get("legal_summary") or {}
    citation = results.get("citation_insights") or {}
    content_plan = citation.get("content_plan") or {}
    provider_readiness = _get_provider_readiness(results)
    platform_guidance = results.get("platform_guidance") or {}
    deep = results.get("deep_recommendations") or {}
    faq_detection = results.get("faq_detection") or {}
    industry_analysis = results.get("industry_analysis") or {}
    basics = (results.get("seo_results") or {}).get("basics") or {}
    structure = (results.get("seo_results") or {}).get("structure") or {}
    integrated = results.get("integrated_results") or {}
    business_type = results.get("business_type_detection") or {}
    headings = structure.get("headings") or {}

    heading_texts: List[str] = []
    if isinstance(headings, dict):
        for _, value in headings.items():
            if isinstance(value, list):
                heading_texts.extend(_safe_text_list(value, limit=4))
            else:
                text = _safe_text(value)
                if text:
                    heading_texts.append(text)

    url_value = _safe_text(results.get("url"))
    url_signal_tokens = _extract_url_signal_tokens(url_value)
    domain_profile = build_domain_profile(url_value)

    issue_texts: List[str] = []
    for warning in results.get("warnings") or []:
        text = _safe_text(warning)
        if text:
            issue_texts.append(text)
    for item in legal_summary.get("top_issues") or []:
        for value in (item.get("title"), item.get("summary"), item.get("detail")):
            text = _safe_text(value)
            if text:
                issue_texts.append(text)
    for group in ("business", "technical"):
        for item in deep.get(group) or []:
            for value in (
                item.get("title"),
                item.get("current_issue"),
                item.get("recommended_action"),
                item.get("implementation"),
                item.get("expected_impact"),
            ):
                text = _safe_text(value)
                if text:
                    issue_texts.append(text)
    for item in (results.get("summary") or {}).get("improvements") or []:
        text = _safe_text(item)
        if text:
            issue_texts.append(text)
    for item in citation.get("phrases") or []:
        for value in (item.get("phrase"), item.get("reason"), item.get("template_non_engineer"), item.get("template")):
            text = _safe_text(value)
            if text:
                issue_texts.append(text)
    for section in content_plan.get("sections") or []:
        for value in (section.get("title"), section.get("purpose"), section.get("format")):
            text = _safe_text(value)
            if text:
                issue_texts.append(text)
    for provider in provider_readiness.values():
        if not isinstance(provider, dict):
            continue
        summary_text = _safe_text(provider.get("summary"))
        if summary_text:
            issue_texts.append(summary_text)
        for note in provider.get("heuristic_notes") or []:
            text = _safe_text(note)
            if text:
                issue_texts.append(text)
    validation = faq_detection.get("validation") or {}
    for item in validation.get("suspicious_items") or []:
        for value in (item.get("question"), item.get("reason")):
            text = _safe_text(value)
            if text:
                issue_texts.append(text)

    industry = _safe_text(((results.get("final_industry") or {}).get("primary")))
    lmo_profile = build_lmo_profile(
        industry=industry,
        page_title=basics.get("title"),
        meta_description=basics.get("meta_description"),
        heading_texts=heading_texts,
        context_text=" ".join(issue_texts),
        url_tokens=url_signal_tokens,
    )
    ec_guardrail = build_ec_guardrail(
        raw_is_ec=bool(results.get("is_ec")),
        ec_detection_reason=results.get("ec_detection_reason"),
        domain_profile=domain_profile,
        lmo_profile=lmo_profile,
    )

    return {
        "industry": industry,
        "site_type": _safe_text(((results.get("url_type") or {}).get("effective"))),
        "platform": _safe_text(platform_guidance.get("label") or ((results.get("platform") or {}).get("effective"))),
        "is_ec": bool(results.get("is_ec")),
        "effective_is_ec": bool(ec_guardrail.get("effective_is_ec")),
        "ec_detection_reason": _safe_text(results.get("ec_detection_reason")),
        "context_text": " ".join(issue_texts),
        "citation_count": len(citation.get("phrases") or []),
        "business_goal": _safe_text(results.get("business_goal") or integrated.get("business_goal")),
        "audience_clues": _safe_text_list(_read_context_value(industry_analysis, "target_audience_clues") or []),
        "regulatory_indicators": _safe_text_list(_read_context_value(industry_analysis, "regulatory_indicators") or []),
        "page_title": _safe_text(basics.get("title")),
        "meta_description": _safe_text(basics.get("meta_description")),
        "heading_texts": _safe_text_list(heading_texts, limit=6),
        "page_focus": _clean_page_focus(basics.get("title")) or _clean_page_focus(business_type.get("primary_type")),
        "business_type": _safe_text(business_type.get("primary_type")),
        "summary_improvements": _safe_text_list(((results.get("summary") or {}).get("improvements") or []), limit=4),
        "url": url_value,
        "url_signal_tokens": url_signal_tokens[:8],
        "domain_profile": domain_profile,
        "lmo_profile": lmo_profile,
        "ec_guardrail": ec_guardrail,
    }


def _faq_candidate(
    *,
    question: str,
    answer: str,
    score: int,
    source_label: str,
    reason: str,
    topic: str = "",
    matched_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "question": question,
        "answer": answer,
        "score": score,
        "source_label": source_label,
        "reason": reason,
        "topic": _safe_text(topic),
        "matched_keywords": _safe_text_list(matched_keywords or [], limit=6),
    }


def _dedupe_faq_candidates(candidates: List[Dict[str, Any]], max_items: int) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(candidates, key=lambda row: (-int(row.get("score", 0)), str(row.get("question", "")))):
        question = _safe_text(item.get("question"))
        if not question:
            continue
        key = question.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized = dict(item)
        normalized["question"] = question
        normalized["answer"] = _safe_text(item.get("answer"))
        normalized["source_label"] = _safe_text(item.get("source_label"))
        normalized["reason"] = _safe_text(item.get("reason"))
        normalized["topic"] = _safe_text(item.get("topic"))
        normalized["matched_keywords"] = _safe_text_list(item.get("matched_keywords") or [], limit=6)
        deduped.append(normalized)
        if len(deduped) >= max_items:
            break
    return deduped


def _build_faq_persona_candidates(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    audience_clues = _safe_text_list(context.get("audience_clues") or [], limit=6)
    business_goal = _safe_text(context.get("business_goal"))
    url_tokens = _safe_text_list(context.get("url_signal_tokens") or [], limit=8)
    domain_profile = context.get("domain_profile") or {}
    lmo_profile = context.get("lmo_profile") or {}
    ec_guardrail = context.get("ec_guardrail") or {}
    title_text = " ".join(
        [
            _safe_text(context.get("page_title")),
            _safe_text(context.get("meta_description")),
            _safe_text(context.get("page_focus")),
            _safe_text(context.get("business_type")),
            " ".join(_safe_text_list(context.get("heading_texts") or [], limit=4)),
        ]
    )
    context_text = " ".join(
        [
            _safe_text(context.get("context_text")),
            _safe_text(context.get("site_type")),
            _safe_text(context.get("industry")),
            " ".join(_safe_text_list(context.get("summary_improvements") or [], limit=4)),
            " ".join(_safe_text_list(context.get("regulatory_indicators") or [], limit=4)),
        ]
    )
    url_text = " ".join(url_tokens)

    persona_specs = {
        "ec": {
            "label": "購入前ユーザー向け",
            "style": "購入前に条件を確認したい人",
            "headline_keywords": ["shop", "store", "ec", "cart", "checkout", "product", "products", "通販", "購入", "注文", "配送", "送料", "返品", "支払い"],
            "context_keywords": ["購入", "注文", "返品", "配送", "送料", "支払い", "在庫", "発送", "商品"],
        },
        "visitor": {
            "label": "来訪前ユーザー向け",
            "style": "行く前に条件や現地情報を確認したい人",
            "headline_keywords": ["restaurant", "cafe", "menu", "park", "event", "access", "hours", "予約", "営業時間", "アクセス", "駐車場", "メニュー", "店舗", "施設", "会場"],
            "context_keywords": ["最寄り", "アクセス", "駐車場", "営業時間", "定休日", "予約", "来店", "席", "個室", "メニュー", "イベント", "会場"],
        },
        "public": {
            "label": "案内確認ユーザー向け",
            "style": "窓口や利用条件を先に確認したい人",
            "headline_keywords": ["association", "foundation", "chamber", "public", "member", "会議所", "協会", "財団", "法人", "団体", "支援", "会員"],
            "context_keywords": ["窓口", "相談", "支援", "会員", "申請", "申込条件", "対象者", "制度", "利用案内"],
        },
        "executive": {
            "label": "経営判断者向け",
            "style": "比較判断の材料を短時間で揃えたい人",
            "headline_keywords": ["executive", "owner", "founder", "management", "ceo", "president", "経営", "代表", "役員", "意思決定", "戦略", "投資対効果", "roi"],
            "context_keywords": ["経営課題", "ROI", "投資対効果", "部門横断", "意思決定", "役員", "予算判断", "経営改善"],
        },
        "business": {
            "label": "法人担当者向け",
            "style": "社内検討の前に要件を整理したい人",
            "headline_keywords": ["b2b", "business", "enterprise", "company", "corporate", "法人", "企業", "会社", "導入", "比較", "見積", "資料請求", "料金", "プラン"],
            "context_keywords": ["稟議", "導入", "比較検討", "資料請求", "見積", "月額", "初期費用", "担当者", "運用体制", "導入事例"],
        },
        "specialist": {
            "label": "専門職向け",
            "style": "根拠や要件を厳しく確認したい人",
            "headline_keywords": ["medical", "clinic", "legal", "security", "compliance", "医療", "病院", "クリニック", "弁護士", "税理士", "士業", "セキュリティ", "要件"],
            "context_keywords": ["根拠", "要件", "仕様", "ガイドライン", "監修", "エビデンス", "法令", "コンプライアンス", "症例", "診療"],
        },
        "consumer": {
            "label": "個人ユーザー向け",
            "style": "初めて比較検討する人",
            "headline_keywords": ["personal", "consumer", "family", "home", "individual", "個人", "一般", "初心者", "家庭", "自宅", "はじめて", "レビュー", "口コミ"],
            "context_keywords": ["初めて", "口コミ", "レビュー", "体験", "お客様", "ユーザー", "ご利用", "使い方", "不安", "サポート"],
        },
        "default": {
            "label": "比較検討中の担当者向け",
            "style": "問い合わせ前に要点を把握したい人",
            "headline_keywords": [],
            "context_keywords": ["比較", "選び方", "違い", "判断材料", "相談", "問い合わせ"],
        },
    }

    scores = {key: 0.0 for key in persona_specs}
    reasons = {key: [] for key in persona_specs}

    def add_score(key: str, points: float, reason: str) -> None:
        if not reason:
            return
        scores[key] += points
        if reason not in reasons[key]:
            reasons[key].append(reason)

    audience_map = {
        "経営者向け": ("executive", 6.0),
        "法人向け": ("business", 6.0),
        "専門職向け": ("specialist", 6.0),
        "個人向け": ("consumer", 6.0),
    }
    for clue in audience_clues:
        target = audience_map.get(clue)
        if target:
            add_score(target[0], target[1], f"audience_clues:{clue}")

    domain_class = _safe_text(domain_profile.get("domain_class"))

    if ec_guardrail.get("effective_is_ec"):
        add_score("ec", 9.0, "is_ec")
        add_score("consumer", 2.5, "is_ec")

    if lmo_profile.get("is_location_or_visit"):
        visitor_boost = 4.0 if domain_class in {"association_like", "public_like"} else 7.0
        consumer_boost = 1.0 if domain_class in {"association_like", "public_like"} else 2.0
        add_score("visitor", visitor_boost, "lmo:visit_intent")
        add_score("consumer", consumer_boost, "lmo:visit_intent")
    if _contains_any(_safe_text(context.get("industry")), ["飲食", "フード", "レジャー", "観光", "旅行", "ホテル", "宿泊"]):
        add_score("visitor", 2.5, "industry:lmo")

    if domain_class in {"association_like", "public_like"}:
        add_score("public", 6.0, f"domain:{domain_class}")
        if lmo_profile.get("is_location_or_visit"):
            add_score("public", 2.0, "domain:lmo_blend")
        add_score("default", 1.5, f"domain:{domain_class}")

    if _contains_any(_safe_text(context.get("site_type")), ["企業", "法人", "会社"]) and not lmo_profile.get("is_location_or_visit") and domain_class not in {"association_like", "public_like"}:
        add_score("business", 3.0, "site_type:corporate")
        add_score("default", 1.5, "site_type:corporate")
    if _contains_any(_safe_text(context.get("industry")), ["金融", "保険", "医療", "美容", "健康", "士業"]):
        add_score("specialist", 2.5, "industry:regulated")
    if _contains_any(business_goal, ["CV", "リード", "CTA"]):
        add_score("business", 1.5, "goal:lead")
    if _contains_any(business_goal, ["ブランド", "指名検索"]):
        add_score("executive", 1.0, "goal:brand")
    if _contains_any(business_goal, ["技術健全性", "エンジニア"]):
        add_score("specialist", 1.5, "goal:technical")

    for key, spec in persona_specs.items():
        headline_hits = _collect_keyword_hits(title_text, spec["headline_keywords"])
        context_hits = _collect_keyword_hits(context_text, spec["context_keywords"])
        url_hits = _collect_keyword_hits(url_text, spec["headline_keywords"] + spec["context_keywords"])
        for hit in headline_hits[:3]:
            add_score(key, 2.5, f"title:{hit}")
        for hit in context_hits[:3]:
            add_score(key, 1.5, f"context:{hit}")
        for hit in url_hits[:2]:
            add_score(key, 1.0, f"url:{hit}")

    if scores["ec"] >= 9.0:
        scores["ec"] += 1.0

    ranked = sorted(
        (
            {
                "key": key,
                "label": spec["label"],
                "style": spec["style"],
                "score": round(scores[key], 1),
                "signals": reasons[key][:6],
            }
            for key, spec in persona_specs.items()
            if scores[key] > 0
        ),
        key=lambda item: (-float(item.get("score", 0)), str(item.get("label", ""))),
    )
    if ranked:
        return ranked
    return [
        {
            "key": "default",
            "label": "検討中ユーザー向け",
            "style": "必要な条件を先に知りたい人",
            "score": 0.0,
            "signals": ["fallback:generic"],
        }
    ]


def _build_faq_persona(context: Dict[str, Any]) -> Dict[str, Any]:
    candidates = _build_faq_persona_candidates(context)
    business_goal = _safe_text(context.get("business_goal"))
    primary = dict(candidates[0]) if candidates else {
        "key": "default",
        "label": "検討中ユーザー向け",
        "style": "必要な条件を先に知りたい人",
        "score": 0.0,
        "signals": ["fallback:generic"],
    }
    secondary_score = float(candidates[1].get("score", 0)) if len(candidates) > 1 else 0.0
    primary_score = float(primary.get("score", 0) or 0)
    score_gap = primary_score - secondary_score

    if primary_score >= 9 and score_gap >= 4:
        confidence = "high"
    elif primary_score >= 5 and score_gap >= 1.5:
        confidence = "medium"
    else:
        confidence = "low"

    goal_hint_map = {
        "オーガニック流入増加（SEO優先）": "検索段階で比較されやすい論点を先に出す構成",
        "AI検索での引用増加（GEO/AIO優先）": "AIが短く抜き出しやすい言い回し",
        "CV率・リード獲得（CTA改善優先）": "問い合わせ前の不安を減らす説明順",
        "ブランド認知・指名検索強化": "初見でもブランド理解が進む説明順",
        "サイト技術健全性（エンジニア優先）": "要件と根拠を確認しやすい説明順",
    }
    goal_hint = goal_hint_map.get(business_goal, "検討時の不安を減らす説明順")

    return {
        "label": _safe_text(primary.get("label")),
        "style": _safe_text(primary.get("style")),
        "goal_hint": goal_hint,
        "source": _safe_text((primary.get("signals") or ["fallback:generic"])[0]),
        "confidence": confidence,
        "score": primary_score,
        "candidates": candidates[:4],
    }


def _build_offer_label(context: Dict[str, Any]) -> str:
    for value in (
        context.get("page_focus"),
        context.get("business_type"),
        context.get("industry"),
        context.get("site_type"),
    ):
        text = _clean_page_focus(value)
        if text:
            return text
    return "このサービス"


def _personalize_non_ec_faq(candidate: Dict[str, Any], context: Dict[str, Any], persona: Dict[str, str]) -> Dict[str, Any]:
    topic = _safe_text(candidate.get("topic"))
    industry = _safe_text(context.get("industry")) or "このサービス"
    offer_label = _build_offer_label(context)
    site_type = _safe_text(context.get("site_type")) or "サイト"
    business_goal = _safe_text(context.get("business_goal"))
    lmo_profile = context.get("lmo_profile") or {}
    is_saas = _contains_any(industry, ["IT", "SaaS", "ソフトウェア", "システム", "DX"])
    is_corporate = _contains_any(site_type, ["企業", "法人", "会社"])
    is_regulated = _contains_any(industry, ["金融", "保険", "医療", "美容", "健康", "サプリ", "士業"])
    is_lmo = bool(lmo_profile.get("is_location_or_visit"))

    question = _safe_text(candidate.get("question"))
    answer = _safe_text(candidate.get("answer"))

    if topic == "audience_value":
        if is_lmo:
            question = "初めて行く前に、何を確認しておくと安心ですか？"
            answer = "アクセス、営業時間、予約の要否、現地で確認できる設備を先にまとめると、来訪前ユーザーが迷いにくくなります。"
        else:
            question = f"{offer_label}はどんな課題から先に役立ちますか？"
            answer = (
                f"{persona['label']}が読み始めてすぐ判断できるよう、{industry}で起こりやすい課題、"
                "解決できる範囲、導入後に変わることを冒頭で3点に整理すると伝わりやすくなります。"
            )
    elif topic == "fit":
        if persona["label"] == "案内確認ユーザー向け":
            question = "利用対象や会員・一般の違いはどこで確認できますか？"
            answer = "対象者、会員向けと一般向けの違い、申込条件を分けて示すと、制度や窓口の案内として使いやすくなります。"
        else:
            question = "どんな人・企業に向いていて、どんなケースは対象外ですか？"
            answer = (
                f"{persona['style']}が迷わないよう、向いている利用シーン、相性のよい業種や規模、"
                "逆に合わない条件までFAQで並べると問い合わせの質が安定します。"
            )
    elif topic == "pricing":
        if is_saas:
            question = "初期費用・月額・追加料金の考え方は？"
            answer = (
                "初期費用、月額、オプション料金、最低契約期間を1つの表にまとめ、"
                "どこから個別見積になるのかを先に示すとSaaS比較で迷われにくくなります。"
            )
        elif is_corporate:
            question = "見積や費用は何を基準に決まりますか？"
            answer = (
                "費用算定の基準、見積時に必要な情報、追加費用が発生しやすい条件をFAQで明示すると、"
                "担当者が社内説明しやすくなります。"
            )
        else:
            question = "料金に何が含まれますか？追加費用はありますか？"
            answer = (
                "基本料金に含まれる範囲と、追加料金が発生するケースを分けて書くと、"
                "検討ユーザーが比較しやすくなります。"
            )
    elif topic == "process":
        if is_lmo:
            question = "予約や来店までの流れは？"
            answer = "予約の要否、当日受付の有無、来店前に確認したい注意点を時系列で並べると、現地利用の前に迷いにくくなります。"
        elif persona["label"] == "案内確認ユーザー向け":
            question = "相談や申込の流れはどこで確認できますか？"
            answer = "対象者、必要情報、申込方法、結果連絡までの流れを段階ごとに示すと、制度や窓口の利用前に迷いにくくなります。"
        else:
            question = "問い合わせ後、導入や申込まではどんな流れですか？" if is_corporate else "申込から利用開始まではどんな流れですか？"
            answer = (
                "初回相談、必要情報、見積や契約、開始までの段階を時系列で示し、"
                "各ステップの所要日数を添えると不安が減ります。"
            )
    elif topic == "comparison":
        question = "他社サービスと比較するときの確認ポイントは？"
        answer = (
            f"{business_goal or '比較検討'}を意識して、選定基準、向いているケース、"
            "代替案との差が出る条件を3項目程度で並べると判断材料になります。"
        )
    elif topic == "trust":
        question = "監修体制や運営者情報はどこで確認できますか？" if is_regulated else "運営会社・担当者情報はどこで確認できますか？"
        answer = (
            "会社概要、担当者プロフィール、監修者、一次情報の出典、問い合わせ窓口を近い場所にまとめると、"
            f"{persona['label']}にも信頼の根拠が伝わりやすくなります。"
        )
    elif topic == "case":
        question = "導入事例や成果はどのように確認できますか？"
        answer = (
            "事例の有無だけでなく、どの業種・規模で、何を改善できたか、"
            "再現しやすい条件は何かまで短く示すと説得力が上がります。"
        )
    elif topic == "support":
        if persona["label"] == "案内確認ユーザー向け":
            question = "相談窓口と回答目安は？"
            answer = "問い合わせ窓口、受付時間、対象外の相談、回答目安をまとめると、制度案内や窓口案内として分かりやすくなります。"
        else:
            question = "問い合わせ前に準備すべき情報と回答目安は？" if is_corporate else "問い合わせ方法と回答目安は？"
            answer = (
                "窓口、受付時間、返信目安、問い合わせ時に必要な情報をFAQに置くと、"
                "商談前や申込前の往復を減らしやすくなります。"
            )
    elif topic == "security":
        question = "セキュリティ体制と個人情報の扱いは？"
        answer = (
            "保管方法、権限管理、委託先の扱い、個人情報の保存期間をまとめて示すと、"
            f"{industry}で気にされやすい安全面の不安を先回りできます。"
        )
    elif topic == "access":
        question = "アクセス方法・最寄り駅・駐車場は？"
        answer = "最寄り駅、徒歩や車での行き方、駐車場の有無を1つにまとめると、初めて訪れる人が迷いにくくなります。"
    elif topic == "hours":
        question = "営業時間・定休日・混雑しやすい時間帯は？"
        answer = "営業時間、定休日、ラストオーダー、混みやすい時間帯が分かると、来訪前に予定を立てやすくなります。"
    elif topic == "reservation":
        question = "予約方法・当日利用・席や設備の確認方法は？"
        answer = "予約の要否、当日受付、席数や個室、設備の確認方法を先に示すと、来店前や来場前の不安が減ります。"
    elif topic == "public_services":
        question = "どんな支援・サービスが受けられますか？"
        answer = "支援メニューの一覧だけでなく、相談できる内容、利用目的ごとの違い、まず見るべき入口を分けて示すと、案内情報として使いやすくなります。"
    elif topic == "public_eligibility":
        question = "対象者・会員/一般の違い・利用条件は？"
        answer = "対象者、会員向けと一般向けの違い、申込条件、利用できないケースを分けて示すと、自分が対象かどうかを判断しやすくなります。"
    elif topic == "public_application":
        question = "申込に必要な情報と手続きの流れは？"
        answer = "申込方法、必要情報、締切、結果連絡までの流れを段階ごとに示すと、制度や講座の利用前に迷いにくくなります。"

    rewritten = dict(candidate)
    rewritten["base_question"] = _safe_text(candidate.get("question"))
    rewritten["base_answer"] = _safe_text(candidate.get("answer"))
    rewritten["question"] = question
    rewritten["answer"] = answer
    rewritten["persona_label"] = persona["label"]
    rewritten["presentation_mode"] = "contextualized"
    rewritten["goal_hint"] = persona["goal_hint"]
    return rewritten


def _personalize_ec_faq(candidate: Dict[str, Any], context: Dict[str, Any], persona: Dict[str, str]) -> Dict[str, Any]:
    topic = _safe_text(candidate.get("topic"))
    question = _safe_text(candidate.get("question"))
    answer = _safe_text(candidate.get("answer"))

    if topic == "delivery":
        question = "送料・配送日数・到着目安は？"
        answer = "送料、地域差、発送までの日数、到着目安、日時指定の可否を1つのFAQでまとめると購入前の離脱を減らしやすくなります。"
    elif topic == "returns":
        question = "返品・交換の条件は？"
        answer = "返品期限、未開封条件、返送料の負担、不良品時の扱いを分けて書くと、購入前ユーザーが判断しやすくなります。"
    elif topic == "payment":
        question = "使える支払い方法と手数料は？"
        answer = "利用可能な決済手段、ブランド、手数料、支払期限を並べると、カート直前での離脱を抑えやすくなります。"
    elif topic == "cancel":
        question = "キャンセルや注文変更はいつまで可能ですか？"
        answer = "発送前後での扱いの違い、変更受付の締切、連絡方法を先に示すと問い合わせが減ります。"
    elif topic == "contact":
        question = "問い合わせ窓口と回答目安は？"
        answer = "フォーム・メール・電話などの窓口、受付時間、返信目安を明記すると、購入前ユーザーの不安を減らしやすくなります。"

    rewritten = dict(candidate)
    rewritten["base_question"] = _safe_text(candidate.get("question"))
    rewritten["base_answer"] = _safe_text(candidate.get("answer"))
    rewritten["question"] = question
    rewritten["answer"] = answer
    rewritten["persona_label"] = persona["label"]
    rewritten["presentation_mode"] = "contextualized"
    rewritten["goal_hint"] = persona["goal_hint"]
    return rewritten


def _personalize_faq_candidates(candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    persona = _build_faq_persona(context)
    personalized: List[Dict[str, Any]] = []
    for candidate in candidates:
        if context.get("effective_is_ec"):
            personalized.append(_personalize_ec_faq(candidate, context, persona))
        else:
            personalized.append(_personalize_non_ec_faq(candidate, context, persona))
    return personalized


def _build_faq_debug_payload(
    *,
    context: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    suggestions: List[Dict[str, Any]],
    strategy: str,
) -> Dict[str, Any]:
    selected_topics = {(_safe_text(item.get("topic")), _safe_text(item.get("base_question") or item.get("question"))) for item in suggestions}
    debug_candidates = []
    for item in sorted(candidates, key=lambda row: (-int(row.get("score", 0)), str(row.get("question", ""))))[:10]:
        base_question = _safe_text(item.get("question"))
        topic = _safe_text(item.get("topic"))
        debug_candidates.append(
            {
                "topic": topic,
                "base_question": base_question,
                "score": int(item.get("score", 0) or 0),
                "matched_keywords": _safe_text_list(item.get("matched_keywords") or [], limit=6),
                "source_label": _safe_text(item.get("source_label")),
                "selected": (topic, base_question) in selected_topics,
            }
        )

    return {
        "strategy": strategy,
        "persona": _build_faq_persona(context),
        "context": {
            "industry": _safe_text(context.get("industry")),
            "site_type": _safe_text(context.get("site_type")),
            "platform": _safe_text(context.get("platform")),
            "business_goal": _safe_text(context.get("business_goal")),
            "page_focus": _safe_text(context.get("page_focus")),
            "page_title": _safe_text(context.get("page_title")),
            "meta_description": _safe_text(context.get("meta_description")),
            "audience_clues": _safe_text_list(context.get("audience_clues") or [], limit=4),
            "regulatory_indicators": _safe_text_list(context.get("regulatory_indicators") or [], limit=4),
            "summary_improvements": _safe_text_list(context.get("summary_improvements") or [], limit=4),
            "url_signal_tokens": _safe_text_list(context.get("url_signal_tokens") or [], limit=6),
            "domain_profile": _json_clone(context.get("domain_profile") or {}) or {},
            "lmo_profile": _json_clone(context.get("lmo_profile") or {}) or {},
            "ec_guardrail": _json_clone(context.get("ec_guardrail") or {}) or {},
            "context_excerpt": _compact_marketer_excerpt(context.get("context_text"), limit=160),
        },
        "candidates": debug_candidates,
        "selected_count": len(suggestions),
    }


def _build_faq_suggestion_payload(results: Dict[str, Any], max_items: int = 5) -> Dict[str, Any]:
    existing = results.get("faq_suggestions")
    if isinstance(existing, list) and existing:
        context = _collect_faq_context(results)
        existing_rows = _json_clone(existing[:max_items]) or []
        return {
            "suggestions": existing_rows,
            "debug": _build_faq_debug_payload(
                context=context,
                candidates=existing_rows,
                suggestions=existing_rows,
                strategy="precomputed",
            ),
        }

    context = _collect_faq_context(results)
    candidates = _build_ec_faq_candidates(context) if context.get("effective_is_ec") else _build_non_ec_faq_candidates(context)
    selected = _dedupe_faq_candidates(candidates, max_items=max_items)
    if selected:
        personalized = _personalize_faq_candidates(selected, context)
        return {
            "suggestions": _json_clone(personalized) or [],
            "debug": _build_faq_debug_payload(
                context=context,
                candidates=candidates,
                suggestions=personalized,
                strategy="template_plus_context_rewrite",
            ),
        }

    preferred: List[Dict[str, Any]] = []
    blacklist = ("返品", "配送", "送料", "支払い", "注文", "キャンセル")
    for item in get_all_faqs("simple") or []:
        question = _safe_text((item or {}).get("question"))
        if any(word in question for word in blacklist):
            continue
        preferred.append(item)
    fallback = _json_clone(preferred[:max_items]) or []
    return {
        "suggestions": fallback,
        "debug": _build_faq_debug_payload(
            context=context,
            candidates=fallback,
            suggestions=fallback,
            strategy="fallback_glossary",
        ),
    }


def _build_non_ec_faq_candidates(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    industry = context["industry"] or "このサービス"
    site_type = context["site_type"] or "企業サイト"
    platform = context["platform"]
    text = context["context_text"]
    lmo_profile = context.get("lmo_profile") or {}
    domain_profile = context.get("domain_profile") or {}

    issue_keywords = {
        "trust": ["e-e-a-t", "著者", "運営者", "会社", "問い合わせ", "privacy", "個人情報", "信頼"],
        "pricing": ["料金", "費用", "価格", "plan", "プラン", "見積", "コスト"],
        "process": ["導入", "相談", "申込", "予約", "利用開始", "手順", "流れ"],
        "comparison": ["比較", "違い", "選び方", "競合", "他社"],
        "case": ["事例", "実績", "導入社数", "成功", "お客様"],
        "support": ["問い合わせ", "support", "サポート", "連絡", "対応時間"],
        "security": ["セキュリティ", "security", "権限", "個人情報", "認証"],
        "audience": ["対象", "向いて", "おすすめ", "業種", "用途"],
        "access": ["アクセス", "最寄り", "駅", "駐車場", "地図", "行き方"],
        "hours": ["営業時間", "定休日", "受付時間", "営業日", "ラストオーダー"],
        "reservation": ["予約", "席", "個室", "当日利用", "来店", "受付"],
        "public_services": ["支援", "サービス", "講座", "セミナー", "制度", "事業", "メニュー", "相談内容"],
        "public_eligibility": ["対象者", "会員", "一般", "利用条件", "申込条件", "参加対象", "会費"],
        "public_application": ["申込", "申請", "手続き", "必要書類", "締切", "受付", "窓口"],
    }

    is_saas = _contains_any(industry, ["IT", "SaaS", "ソフトウェア", "システム", "DX"])
    is_regulated = _contains_any(industry, ["金融", "保険", "医療", "美容", "健康", "サプリ", "士業"])
    is_corporate = _contains_any(site_type, ["企業", "法人", "会社"])
    is_lmo = bool(lmo_profile.get("is_location_or_visit"))
    prefer_public = bool((domain_profile or {}).get("prefer_public_info"))

    audience_hits = _collect_keyword_hits(text, issue_keywords["audience"])
    comparison_hits = _collect_keyword_hits(text, issue_keywords["comparison"])
    pricing_hits = _collect_keyword_hits(text, issue_keywords["pricing"])
    process_hits = _collect_keyword_hits(text, issue_keywords["process"])
    trust_hits = _collect_keyword_hits(text, issue_keywords["trust"])
    case_hits = _collect_keyword_hits(text, issue_keywords["case"])
    support_hits = _collect_keyword_hits(text, issue_keywords["support"])
    security_hits = _collect_keyword_hits(text, issue_keywords["security"])
    access_hits = _collect_keyword_hits(text, issue_keywords["access"]) or _safe_text_list(((lmo_profile.get("category_hits") or {}).get("access") or []), limit=4)
    hours_hits = _collect_keyword_hits(text, issue_keywords["hours"]) or _safe_text_list(((lmo_profile.get("category_hits") or {}).get("hours") or []), limit=4)
    reservation_hits = _collect_keyword_hits(text, issue_keywords["reservation"]) or _safe_text_list(((lmo_profile.get("category_hits") or {}).get("reservation") or []), limit=4)
    public_service_hits = _collect_keyword_hits(text, issue_keywords["public_services"])
    public_eligibility_hits = _collect_keyword_hits(text, issue_keywords["public_eligibility"])
    public_application_hits = _collect_keyword_hits(text, issue_keywords["public_application"])

    return [
        _faq_candidate(
            question="このサービスはどんな課題を解決できますか？",
            answer=f"{industry}の文脈で、誰のどんな悩みを解決するのかを最初に明示すると理解されやすくなります。対象者、解決できる課題、得られる成果をFAQでも本文でも同じ表現で整理します。",
            score=3 + (2 if audience_hits or comparison_hits else 0) + (1 if prefer_public else 0) - (1 if is_lmo else 0),
            source_label="URL不足ベース",
            reason="対象者と提供価値が一目で分かる導線を補うためのFAQです。",
            topic="audience_value",
            matched_keywords=audience_hits + comparison_hits,
        ),
        _faq_candidate(
            question="どんな人・企業に向いていますか？",
            answer=f"{site_type}として想定している利用者像、向いているケース、逆に適さないケースまで示すと、問い合わせ前の迷いを減らせます。業種や利用シーンを2〜3例で補足する構成が有効です。",
            score=3 + (3 if audience_hits else 0) + (2 if prefer_public else 0),
            source_label="URL不足ベース",
            reason="対象読者が自分ごと化しやすいFAQが不足しているためです。",
            topic="fit",
            matched_keywords=audience_hits,
        ),
        _faq_candidate(
            question="料金や費用感はどのように確認できますか？",
            answer="料金表がまだ出せない場合でも、見積の考え方、最低契約期間、追加費用が発生しやすい条件をFAQに置くと離脱を防ぎやすくなります。",
            score=2 + (5 if pricing_hits else 0) + (1 if is_saas else 0) - (1 if is_lmo or prefer_public else 0),
            source_label="issue / citation ベース",
            reason="料金・費用まわりの説明不足を埋める優先度が高いためです。",
            topic="pricing",
            matched_keywords=pricing_hits,
        ),
        _faq_candidate(
            question="相談から導入・申込までの流れは？",
            answer="初回相談、必要情報、契約、開始までの流れを段階ごとに整理すると、申し込み前の不安が減ります。所要日数や担当者とのやり取りも合わせて記載します。",
            score=2 + (5 if process_hits else 0) + (1 if is_corporate and not is_lmo and not prefer_public else 0) + (1 if prefer_public else 0) - (2 if prefer_public else 0),
            source_label="issue / citation ベース",
            reason="導入導線や手順の見えにくさを解消するためです。",
            topic="process",
            matched_keywords=process_hits,
        ),
        _faq_candidate(
            question="他社サービスとの違いや選び方は？",
            answer=f"{industry}では比較検討で離脱しやすいため、選定基準、向いているケース、比較されやすい代替案との違いをFAQで短く整理すると引用候補にもなりやすくなります。",
            score=2 + (5 if comparison_hits else 0) + (1 if context["citation_count"] > 0 else 0) - (1 if is_lmo or prefer_public else 0),
            source_label="citation / issue ベース",
            reason="比較・選び方の観点が不足しているためです。",
            topic="comparison",
            matched_keywords=comparison_hits,
        ),
        _faq_candidate(
            question="運営会社や監修者の信頼情報はどこで確認できますか？",
            answer="会社概要、担当者プロフィール、監修者、一次情報の出典などを1か所にまとめると、AI検索でも通常検索でも信頼性が伝わりやすくなります。",
            score=2 + (6 if trust_hits else 0),
            source_label="issue ベース",
            reason="運営者・著者・問い合わせなどの信頼情報を補う必要があるためです。",
            topic="trust",
            matched_keywords=trust_hits,
        ),
        _faq_candidate(
            question="導入事例や実績はありますか？",
            answer="事例の有無だけでなく、どの業種・規模で、どんな成果が出たのかを簡潔に示すと説得力が上がります。数字や引用できる事実を添えると効果的です。",
            score=2 + (4 if case_hits else 0) + (1 if context["citation_count"] > 0 else 0) - (1 if is_lmo or prefer_public else 0),
            source_label="citation ベース",
            reason="実績・数値・具体例を補強するFAQ候補です。",
            topic="case",
            matched_keywords=case_hits,
        ),
        _faq_candidate(
            question="問い合わせ方法と回答までの目安は？",
            answer="問い合わせ窓口、受付時間、返信目安、事前に用意するとよい情報をFAQ化すると、商談前の不安を減らせます。",
            score=2 + (4 if support_hits else 0) + (1 if prefer_public else 0),
            source_label="issue ベース",
            reason="問い合わせ前の不明点を減らすためのFAQです。",
            topic="support",
            matched_keywords=support_hits,
        ),
        _faq_candidate(
            question="セキュリティや個人情報保護はどうなっていますか？",
            answer=f"{industry}では安全性への不安が比較の障壁になりやすいため、保管方法、アクセス制御、運用ルール、個人情報の扱いをまとめて説明すると効果的です。",
            score=1 + (5 if security_hits else 0) + (2 if is_saas or is_regulated else 0) + (1 if _contains_any(platform, ["WordPress", "Wix"]) else 0),
            source_label="業界 / platform ベース",
            reason="安全性・個人情報保護への関心が高い業界・構成だからです。",
            topic="security",
            matched_keywords=security_hits,
        ),
        _faq_candidate(
            question="アクセス方法・最寄り駅・駐車場は？",
            answer="最寄り駅、徒歩や車での行き方、駐車場の有無をまとめると、初めて訪れる人が迷いにくくなります。",
            score=1 + (4 if access_hits else 0) + (3 if is_lmo else 0) - (4 if prefer_public else 0),
            source_label="LMO / issue ベース",
            reason="来訪前に必要な現地情報を補うFAQです。",
            topic="access",
            matched_keywords=access_hits,
        ),
        _faq_candidate(
            question="営業時間・定休日・混雑しやすい時間帯は？",
            answer="営業時間、定休日、ラストオーダー、混みやすい時間帯が分かると、来訪前に予定を立てやすくなります。",
            score=1 + (4 if hours_hits else 0) + (3 if is_lmo else 0) - (4 if prefer_public else 0),
            source_label="LMO / issue ベース",
            reason="来訪タイミングの判断に必要な情報を補うFAQです。",
            topic="hours",
            matched_keywords=hours_hits,
        ),
        _faq_candidate(
            question="予約方法・当日利用・席や設備の確認方法は？",
            answer="予約の要否、当日受付、席や個室、設備の確認方法をまとめると、来店前や来場前の不安を減らしやすくなります。",
            score=1 + (4 if reservation_hits else 0) + (3 if is_lmo else 0) - (4 if prefer_public else 0),
            source_label="LMO / issue ベース",
            reason="予約や現地利用に関するFAQが不足しやすいためです。",
            topic="reservation",
            matched_keywords=reservation_hits,
        ),
        _faq_candidate(
            question="どんな支援・サービスが受けられますか？",
            answer="支援内容の一覧だけでなく、相談できる内容、利用目的ごとの違い、まず見るべき入口を分けると案内として使いやすくなります。",
            score=2 + (5 if public_service_hits else 0) + (4 if prefer_public else 0),
            source_label="公共案内 / issue ベース",
            reason="支援メニューやサービス内容を案内しやすくするFAQです。",
            topic="public_services",
            matched_keywords=public_service_hits,
        ),
        _faq_candidate(
            question="対象者・会員/一般の違い・利用条件は？",
            answer="対象者、会員向けと一般向けの違い、利用条件、対象外ケースを整理すると、制度や支援の案内として分かりやすくなります。",
            score=2 + (5 if public_eligibility_hits else 0) + (4 if prefer_public else 0),
            source_label="公共案内 / issue ベース",
            reason="利用条件や対象者を明確にするFAQです。",
            topic="public_eligibility",
            matched_keywords=public_eligibility_hits,
        ),
        _faq_candidate(
            question="申込に必要な情報と手続きの流れは？",
            answer="申込方法、必要情報、締切、結果連絡までの流れを段階ごとに示すと、講座や制度の利用前に迷いにくくなります。",
            score=2 + (5 if public_application_hits else 0) + (4 if prefer_public else 0),
            source_label="公共案内 / issue ベース",
            reason="申込や窓口利用の流れを分かりやすくするFAQです。",
            topic="public_application",
            matched_keywords=public_application_hits,
        ),
    ]


def _build_ec_faq_candidates(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = context["context_text"]
    platform = context["platform"]
    templates = get_ec_faq_templates("simple") or []
    keyword_map = {
        "返品": ["返品", "交換", "返金", "不良品"],
        "送料": ["配送", "送料", "発送", "お届け", "到着"],
        "支払い": ["支払い", "決済", "クレジット", "後払い", "手数料"],
        "キャンセル": ["キャンセル", "取消"],
        "変更": ["注文変更", "変更", "修正"],
        "問い合わせ": ["問い合わせ", "サポート", "連絡", "対応時間"],
    }
    platform_boost = 1 if _contains_any(platform, ["Shopify", "楽天", "Yahoo", "Amazon", "Wix"]) else 0

    candidates: List[Dict[str, Any]] = []
    for template in templates:
        question = _safe_text(template.get("question"))
        answer = _safe_text(template.get("answer"))
        score = 2 + platform_boost
        reason = "EC導線で確認されやすい論点を補うためのFAQです。"
        question_text = question.lower()
        topic = ""
        matched_keywords: List[str] = []
        for label, keywords in keyword_map.items():
            keyword_hits = _collect_keyword_hits(text, keywords)
            if label.lower() in question_text:
                topic_map = {
                    "返品": "returns",
                    "送料": "delivery",
                    "支払い": "payment",
                    "キャンセル": "cancel",
                    "変更": "cancel",
                    "問い合わせ": "contact",
                }
                topic = topic_map.get(label, topic)
            if label.lower() in question_text and keyword_hits:
                score += 5
                reason = f"{label}に関する説明不足を埋めるためです。"
                matched_keywords.extend(keyword_hits)
        candidates.append(
            _faq_candidate(
                question=question,
                answer=answer,
                score=score,
                source_label="EC / issue ベース",
                reason=reason,
                topic=topic,
                matched_keywords=matched_keywords,
            )
        )
    return candidates


def _build_faq_suggestions(results: Dict[str, Any], max_items: int = 5) -> List[Dict[str, Any]]:
    payload = _build_faq_suggestion_payload(results, max_items=max_items)
    return _json_clone(payload.get("suggestions") or []) or []


def _build_summary_workspace(
    results: Dict[str, Any],
    *,
    integrated_score: int,
    seo_score: int,
    aio_score: int,
    legal_score: int,
    issue_count: int,
    previous_diff: Dict[str, Any],
    actions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    provider_readiness = _get_provider_readiness(results)
    legal_issues = _extract_legal_summary_items(results)
    warnings = [_safe_text(item) for item in (results.get("warnings") or []) if _safe_text(item)]
    provider_counts = {"pass": 0, "warn": 0, "fail": 0, "unknown": 0}
    blocking_issues: List[Dict[str, Any]] = []

    for label, key in (
        ("Google", "google"),
        ("OpenAI Search", "openai_search"),
        ("Perplexity", "perplexity"),
        ("Claude Search", "claude_search"),
    ):
        provider = provider_readiness.get(key) or {}
        status = _safe_text(provider.get("status"))
        if status in provider_counts:
            provider_counts[status] += 1
        else:
            provider_counts["unknown"] += 1

        if status not in {"warn", "fail"}:
            continue
        official_labels = [
            _safe_text(check.get("label"))
            for check in (provider.get("official_checks") or [])
            if _safe_text(check.get("status")) in {"warn", "fail"} and _safe_text(check.get("label"))
        ]
        detail = _safe_text(provider.get("summary"))
        if official_labels:
            detail = f"{detail} 条件: {', '.join(official_labels[:3])}".strip()
        blocking_issues.append(
            {
                "title": f"{label}: {_provider_status_label(status)}",
                "detail": detail,
                "label": "AI公開条件",
                "status": status,
                "category": "provider",
            }
        )

    for item in warnings[:4]:
        blocking_issues.append(
            {
                "title": "要確認メモ",
                "detail": item,
                "label": "分析メモ",
                "status": "warn",
                "category": "warning",
            }
        )

    for item in legal_issues[:4]:
        title = _safe_text(item.get("title")) or "表現・見せ方の確認"
        detail = _safe_text(item.get("summary") or item.get("detail"))
        if not (title or detail):
            continue
        blocking_issues.append(
            {
                "title": title,
                "detail": detail,
                "label": "表示アドバイス",
                "status": "fail" if _safe_text(item.get("severity")) == "high" else "warn",
                "category": "legal",
            }
        )

    summary_lines = [
        line
        for line in [
            f"業界見立て: {_safe_text(((results.get('final_industry') or {}).get('primary'))) or '未判定'}",
            f"サイト種別: {_safe_text(((results.get('url_type') or {}).get('effective'))) or '未判定'}",
            f"プラットフォーム: {_safe_text(((results.get('platform') or {}).get('effective'))) or '未判定'}",
        ]
        if line
    ]

    return {
        "headline_metrics": [
            {"label": "AI認識", "value": aio_score, "tone": "score"},
            {"label": "SEO", "value": seo_score, "tone": "score"},
            {
                "label": "総合優先度",
                "value": _priority_level(integrated_score=integrated_score, total_issues=issue_count),
                "tone": "priority",
            },
        ],
        "priority_counts": [
            {
                "label": "AI公開条件",
                "detail": "AIサービス側の確認件数",
                "count": provider_counts["warn"] + provider_counts["fail"],
                "status": "warn" if provider_counts["warn"] + provider_counts["fail"] else "pass",
            },
            {
                "label": "表示アドバイス",
                "detail": "表現・見せ方の確認件数",
                "count": len(legal_issues),
                "status": "warn" if legal_issues else "pass",
            },
            {
                "label": "最優先アクション",
                "detail": "下に出ている提案",
                "count": min(len(actions), 3),
                "status": "info",
            },
        ],
        "provider_status_counts": provider_counts,
        "blocking_issues": blocking_issues[:10],
        "summary_lines": summary_lines,
        "top_actions": actions[:3],
        "previous_diff": previous_diff,
    }


def _build_task_workspace(results: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    legal_issues = _extract_legal_summary_items(results)
    task_actions: List[Dict[str, Any]] = []

    for index, item in enumerate(actions[:12]):
        task_actions.append(
            {
                "area": _safe_text(item.get("area")),
                "title": _safe_text(item.get("title")) or "改善提案",
                "action": _safe_text(item.get("action")),
                "detail": _safe_text(item.get("detail")),
                "owner": _safe_text(item.get("role")) or "運用",
                "priority": _task_priority_for_index(index),
                "effort": _safe_text(item.get("effort")) or "0.5-2h",
                "impact": _safe_text(item.get("impact")) or _safe_text(item.get("detail")),
                "kpi": _safe_text(item.get("kpi")),
                "label": _safe_text(item.get("label")) or "対象ページで確認",
            }
        )

    for issue in legal_issues[:4]:
        title = _safe_text(issue.get("title")) or "表現・見せ方の確認"
        action = _safe_text(issue.get("summary") or issue.get("detail"))
        if not (title or action):
            continue
        task_actions.append(
            {
                "area": "表示アドバイス",
                "title": title,
                "action": action,
                "detail": action,
                "owner": "表示確認",
                "priority": "高" if _safe_text(issue.get("severity")) == "high" else "中",
                "effort": "0.5-2h",
                "impact": _safe_text(issue.get("summary")) or action,
                "kpi": "表示アドバイス",
                "label": "対象ページで確認",
            }
        )

    owner_counts: Dict[str, int] = {}
    priority_counts = {"高": 0, "中": 0, "低": 0}
    for item in task_actions:
        owner = _safe_text(item.get("owner")) or "運用"
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        priority = _safe_text(item.get("priority"))
        if priority in priority_counts:
            priority_counts[priority] += 1

    return {
        "actions": task_actions,
        "owner_counts": owner_counts,
        "priority_counts": priority_counts,
    }


def _build_writing_workspace(results: Dict[str, Any]) -> Dict[str, Any]:
    deep = results.get("deep_recommendations") or {}
    basics = (results.get("seo_results") or {}).get("basics") or {}
    aio_results = results.get("aio_results") or {}
    citation = results.get("citation_insights") or {}
    faq_detection = results.get("faq_detection") or {}
    faq_items = _json_clone((faq_detection.get("items") or [])[:5]) or []
    faq_payload = _build_faq_suggestion_payload(results)

    title_rewrites = [
        {
            "kind": "タイトル",
            "current": _safe_text(basics.get("title")),
            "proposed": _safe_text(candidate),
        }
        for candidate in (deep.get("title_rewrites") or [])[:3]
        if _safe_text(candidate)
    ]
    description_rewrites = [
        {
            "kind": "ディスクリプション",
            "current": _safe_text(basics.get("meta_description")),
            "proposed": _safe_text(candidate),
        }
        for candidate in (deep.get("description_rewrites") or [])[:3]
        if _safe_text(candidate)
    ]

    return {
        "title_rewrites": title_rewrites,
        "description_rewrites": description_rewrites,
        "body_rewrites": _json_clone((aio_results.get("rewrite_suggestions") or [])[:3]) or [],
        "citation_phrases": _json_clone((citation.get("phrases") or [])[:5]) or [],
        "content_plan": _json_clone(citation.get("content_plan") or {}) or {},
        "faq_detection_summary": {
            "count": _safe_int(faq_detection.get("count")),
            "items": faq_items,
            "sources": _json_clone(faq_detection.get("sources") or {}) or {},
            "signals": _json_clone(faq_detection.get("signals") or {}) or {},
            "validation": _json_clone(faq_detection.get("validation") or {}) or {},
        },
        "faq_suggestions": [] if faq_items else _json_clone(faq_payload.get("suggestions") or []) or [],
        "faq_debug": {} if faq_items else _json_clone(faq_payload.get("debug") or {}) or {},
    }


def _build_schema_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    schema_existing = results.get("schema_existing") or {}
    schema_suggestions = results.get("schema_suggestions") or []
    site_health = results.get("site_health") or {}
    structured_data = (site_health.get("structured_data") or {}) if isinstance(site_health, dict) else {}
    types = [str(item).strip() for item in (schema_existing.get("types") or []) if str(item).strip()]
    faq_validation = ((results.get("faq_detection") or {}).get("validation") or {})
    summary_lines: List[str] = []
    suggestion_rows = []
    missing_suggestions = 0
    if types:
        summary_lines.append(f"検出schema: {', '.join(types[:6])}")
    else:
        summary_lines.append("検出schema: なし")
    summary_lines.append(f"FAQPage: {'あり' if 'FAQPage' in types else 'なし'}")
    schema_site_type = _safe_text(structured_data.get("schema_site_type"))
    if schema_site_type:
        summary_lines.append(f"推定ページ型: {schema_site_type}")
    if faq_validation:
        summary_lines.append(
            f"FAQ整合: {faq_validation.get('consistent_count', 0)}/{faq_validation.get('checked', 0)}"
            f"（{faq_validation.get('consistency_level', '-')})"
        )
    for suggestion in schema_suggestions[:3]:
        if not isinstance(suggestion, dict):
            continue
        schema_type = _safe_text(suggestion.get("schema_type")) or "Schema"
        already_present = bool(suggestion.get("already_present"))
        if not already_present:
            missing_suggestions += 1
        explanation = suggestion.get("explanation") or {}
        summary = _safe_text(explanation.get("what_is")) or _safe_text(explanation.get("why_it_matters"))
        suggestion_rows.append(
            {
                "schema_type": schema_type,
                "priority": _safe_text(suggestion.get("priority")) or "secondary",
                "already_present": already_present,
                "status": "pass" if already_present else "warn",
                "status_label": "設定済み" if already_present else "未設定",
                "summary": summary,
                "template": _safe_text(suggestion.get("template")),
            }
        )
    suspicious_items = _json_clone((faq_validation.get("suspicious_items") or [])[:5]) or []
    if not types and suggestion_rows:
        status = "fail"
    elif suspicious_items or missing_suggestions > 0:
        status = "warn"
    elif types:
        status = "pass"
    else:
        status = "reference"
    detail_bits = [f"検出 {len(types)}種"]
    if suggestion_rows:
        detail_bits.append(f"追加候補 {len([row for row in suggestion_rows if not row.get('already_present')])}件")
    if "FAQPage" in types:
        detail_bits.append("FAQPage あり")
    elif suggestion_rows:
        detail_bits.append("FAQPage なし")
    return {
        "title": "構造化データ",
        "types": types,
        "faqpage_present": "FAQPage" in types,
        "validation": _json_clone(faq_validation) or {},
        "raw": _json_clone(schema_existing) or {},
        "summary_lines": summary_lines,
        "detail": " / ".join(detail_bits),
        "status": status,
        "status_label": _snapshot_status_label(status),
        "site_type": schema_site_type,
        "suggestions": suggestion_rows,
        "validation_issues": suspicious_items,
    }


def _build_implementation_workspace(results: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    provider_readiness = _get_provider_readiness(results)
    legal_notes = [
        {
            "title": _safe_text(item.get("title")) or "表現・見せ方の確認",
            "detail": _safe_text(item.get("detail") or item.get("summary")),
            "severity": _safe_text(item.get("severity")) or "medium",
        }
        for item in (_extract_legal_summary_items(results) or [])[:4]
        if _safe_text(item.get("title")) or _safe_text(item.get("summary")) or _safe_text(item.get("detail"))
    ]
    technical_actions = [item for item in actions if item.get("area") == "技術補足"][:8]
    return {
        "provider_matrix": _build_provider_status_rows(results),
        "provider_payload": _json_clone(provider_readiness) or {},
        "google_controls": _json_clone(provider_readiness.get("google_controls") or {}) or {},
        "informational_notes": _json_clone(provider_readiness.get("informational_notes") or []) or [],
        "llms_notes": _build_llms_notes(results),
        "llms_summary": _build_llms_summary(results),
        "seo_audit_notes": _build_seo_audit_notes(results),
        "schema_summary": _build_schema_summary(results),
        "link_health_summary": _build_link_health_summary(results),
        "crawl_scope_summary": _build_crawl_scope_summary(results),
        "site_health_checks": _build_site_health_checks(results),
        "platform_guidance": _json_clone(results.get("platform_guidance") or {}) or {},
        "legal_display_notes": legal_notes,
        "technical_actions": technical_actions,
        "reference_notes": _build_reference_notes(results),
    }


def _build_technical_workspace(
    results: Dict[str, Any],
    implementation_workspace: Dict[str, Any],
    actions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    link_health_summary = implementation_workspace.get("link_health_summary") or {}
    schema_summary = implementation_workspace.get("schema_summary") or {}
    llms_summary = implementation_workspace.get("llms_summary") or {}
    crawl_scope_summary = implementation_workspace.get("crawl_scope_summary") or {}
    summary_cards = [
        item
        for item in [schema_summary, llms_summary, link_health_summary]
        if isinstance(item, dict) and _safe_text(item.get("detail"))
    ]
    return {
        "actions": implementation_workspace.get("technical_actions") or [],
        "summary_cards": summary_cards,
        "crawl_scope": crawl_scope_summary,
        "link_health": link_health_summary,
        "schema": schema_summary,
        "llms": llms_summary,
        "site_health_checks": implementation_workspace.get("site_health_checks") or [],
        "signals": [
            {
                "title": f"{row['label']}の状態",
                "detail": f"{row['status']} {row['summary']}".strip(),
                "label": "対象ページで確認",
            }
            for row in (implementation_workspace.get("provider_matrix") or [])
        ],
        "legal_notes": [
            {
                "title": _safe_text(item.get("title")) or "法務メモ",
                "detail": _safe_text(item.get("detail")),
                "label": "対象ページで確認",
            }
            for item in (implementation_workspace.get("legal_display_notes") or [])
        ],
        "reference": implementation_workspace.get("reference_notes") or [],
        "action_items": [item for item in actions if item.get("area") == "技術補足"][:8],
    }


def _build_competitor_summary(
    results: Dict[str, Any],
    *,
    competitor_results: Optional[Dict[str, Any]] = None,
    competitor_action_advice: Optional[Dict[str, Any]] = None,
    competitor_blocked: Optional[str] = None,
    competitor_error: Optional[str] = None,
) -> Dict[str, Any]:
    if competitor_blocked:
        return {
            "status": "blocked",
            "message": competitor_blocked,
        }
    if competitor_error:
        return {
            "status": "error",
            "message": competitor_error,
        }
    if not competitor_results:
        return {}

    current_integrated = results.get("integrated_results") or {}
    competitor_integrated = competitor_results.get("integrated_results") or {}
    score_rows = []
    for label, key in (
        ("SEOスコア", "seo_score"),
        ("AIOスコア", "aio_score"),
        ("統合スコア", "integrated_score"),
    ):
        own = _safe_int(current_integrated.get(key))
        competitor = _safe_int(competitor_integrated.get(key))
        diff = own - competitor
        verdict = "自社優位" if diff >= 3 else "拮抗" if diff >= -3 else "競合優位"
        score_rows.append(
            {
                "label": label,
                "own": own,
                "competitor": competitor,
                "diff": diff,
                "verdict": verdict,
            }
        )

    return {
        "status": "available",
        "url": _safe_text(competitor_results.get("url")),
        "scores": score_rows,
        "actions": _json_clone((competitor_action_advice or {}).get("actions") or []) or [],
    }


def _build_comparison_workspace(
    run_id: int,
    analyzed_at: str,
    results: Dict[str, Any],
    previous_diff: Dict[str, Any],
    *,
    competitor_results: Optional[Dict[str, Any]] = None,
    competitor_action_advice: Optional[Dict[str, Any]] = None,
    competitor_blocked: Optional[str] = None,
    competitor_error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "previous_diff": previous_diff,
        "competitor_summary": _build_competitor_summary(
            results,
            competitor_results=competitor_results,
            competitor_action_advice=competitor_action_advice,
            competitor_blocked=competitor_blocked,
            competitor_error=competitor_error,
        ),
        "run_metadata": {
            "run_id": run_id,
            "analyzed_at": analyzed_at,
            "url": _safe_text(results.get("url")),
        },
        "run_note": f"保存日時: {analyzed_at.replace('T', ' ')[:16]} / run_id: {run_id}",
    }


def _build_ui_snapshot(
    run_id: int,
    analyzed_at: str,
    results: Dict[str, Any],
    previous_run: Optional[Dict[str, Any]],
    *,
    competitor_results: Optional[Dict[str, Any]] = None,
    competitor_action_advice: Optional[Dict[str, Any]] = None,
    competitor_blocked: Optional[str] = None,
    competitor_error: Optional[str] = None,
) -> Dict[str, Any]:
    integrated = results.get("integrated_results") or {}
    seo_score = _safe_int(integrated.get("seo_score"))
    aio_score = _safe_int(integrated.get("aio_score"))
    legal_score = _resolve_legal_score(results, integrated)
    issue_count = _safe_int((results.get("summary") or {}).get("issue_count")) or len(
        _extract_legal_summary_items(results)
    )
    integrated_score = _safe_int(integrated.get("integrated_score"))
    if integrated_score <= 0:
        integrated_score = _fallback_integrated_score(
            seo_score=seo_score,
            aio_score=aio_score,
            legal_score=legal_score,
        )
    previous_diff = _extract_previous_diff(
        previous_run,
        integrated_score=integrated_score,
        seo_score=seo_score,
        aio_score=aio_score,
        legal_score=legal_score,
    )
    actions = _build_priority_actions(results)
    summary_workspace = _build_summary_workspace(
        results,
        integrated_score=integrated_score,
        seo_score=seo_score,
        aio_score=aio_score,
        legal_score=legal_score,
        issue_count=issue_count,
        previous_diff=previous_diff,
        actions=actions,
    )
    task_workspace = _build_task_workspace(results, actions)
    writing_workspace = _build_writing_workspace(results)
    implementation_workspace = _build_implementation_workspace(results, actions)
    technical_workspace = _build_technical_workspace(results, implementation_workspace, actions)
    comparison_workspace = _build_comparison_workspace(
        run_id,
        analyzed_at,
        results,
        previous_diff,
        competitor_results=competitor_results,
        competitor_action_advice=competitor_action_advice,
        competitor_blocked=competitor_blocked,
        competitor_error=competitor_error,
    )

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "meta": {
            "run_id": int(run_id),
            "url": _safe_text(results.get("url")),
            "analyzed_at": analyzed_at,
            "industry": _safe_text(((results.get("final_industry") or {}).get("primary"))),
            "site_type": _safe_text(((results.get("url_type") or {}).get("effective"))),
            "platform": _safe_text(((results.get("platform") or {}).get("effective"))),
            "business_goal": _safe_text(integrated.get("business_goal")),
            "is_ec": bool(results.get("is_ec", False)),
        },
        "header": {
            "seo_score": seo_score,
            "aio_score": aio_score,
            "legal_score": legal_score,
            "integrated_score": integrated_score,
            "issue_count": issue_count,
            "priority_level": _priority_level(integrated_score=integrated_score, total_issues=issue_count),
            "top_actions": actions[:3],
            "previous_diff": previous_diff,
        },
        "summary_workspace": summary_workspace,
        "task_workspace": task_workspace,
        "writing_workspace": writing_workspace,
        "implementation_workspace": implementation_workspace,
        "comparison_workspace": comparison_workspace,
        "overview": {
            "summary_lines": summary_workspace.get("summary_lines") or [],
            "personalized_findings": summary_workspace.get("blocking_issues") or [],
        },
        "ai_workspace": {
            "actions": [item for item in actions if item.get("area") == "AI認識改善"][:8],
            "provider_status": implementation_workspace.get("provider_matrix") or [],
            "citation_phrases": [
                {
                    "title": _safe_text(item.get("phrase")) or "引用候補",
                    "detail": _safe_text(item.get("template_non_engineer") or item.get("template")),
                    "label": "対象ページで確認",
                }
                for item in (writing_workspace.get("citation_phrases") or [])[:4]
                if _safe_text(item.get("phrase")) or _safe_text(item.get("template"))
            ],
            "reference": implementation_workspace.get("reference_notes") or [],
        },
        "seo_workspace": {
            "actions": [item for item in actions if item.get("area") == "SEO改善"][:8],
            "rewrites": _build_rewrites(results),
            "summary_improvements": [
                {"title": "改善要点", "detail": _safe_text(item), "label": "対象ページで確認"}
                for item in ((results.get("summary") or {}).get("improvements") or [])[:6]
                if _safe_text(item)
            ],
        },
        "history_workspace": {
            "previous_diff": comparison_workspace.get("previous_diff") or previous_diff,
            "run_note": comparison_workspace.get("run_note") or f"保存日時: {analyzed_at.replace('T', ' ')[:16]} / run_id: {run_id}",
        },
        "technical_workspace": technical_workspace,
        "exports": {
            "priority_actions": actions[:20],
        },
    }


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _snapshot_needs_refresh(snapshot: Dict[str, Any]) -> bool:
    if _safe_int(snapshot.get("schema_version")) < SNAPSHOT_SCHEMA_VERSION:
        return True
    implementation = snapshot.get("implementation_workspace") or {}
    if not implementation:
        return True
    if "seo_audit_notes" not in implementation:
        return True
    for required_key in ("llms_summary", "schema_summary", "link_health_summary", "crawl_scope_summary", "site_health_checks"):
        if required_key not in implementation:
            return True
    technical_workspace = snapshot.get("technical_workspace") or {}
    for required_key in ("summary_cards", "crawl_scope", "link_health", "schema", "llms", "site_health_checks"):
        if required_key not in technical_workspace:
            return True
    summary_workspace = snapshot.get("summary_workspace") or {}
    headline_metrics = summary_workspace.get("headline_metrics") or []
    if any(_safe_text(item.get("label")) == "法務" for item in headline_metrics if isinstance(item, dict)):
        return True
    priority_counts = summary_workspace.get("priority_counts") or []
    if any(_safe_text(item.get("label")) == "法務・表示" for item in priority_counts if isinstance(item, dict)):
        return True
    return False


def _write_result_payload(run_id: int, results: Dict[str, Any]) -> Path:
    run_dir = RUNS_DIR / str(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "analysis_result.json"
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    return output_path


def persist_analysis_run(
    url: str,
    results: Optional[Dict[str, Any]],
    *,
    competitor_results: Optional[Dict[str, Any]] = None,
    competitor_action_advice: Optional[Dict[str, Any]] = None,
    competitor_blocked: Optional[str] = None,
    competitor_error: Optional[str] = None,
) -> Optional[int]:
    if not url or not results:
        return None

    init_database()
    legal_checks = results.get("legal_checks", {}) or {}
    aggregated = aggregate_legal_check_results(legal_checks)
    issues = []
    for cluster in aggregated.get("aggregated_issues", []) or []:
        rep = cluster.get("representative", {}) or {}
        issues.append(
            {
                "type": rep.get("type") or rep.get("category") or cluster.get("category"),
                "severity": rep.get("severity") or cluster.get("severity"),
                "title": rep.get("title") or rep.get("issue") or rep.get("matched_text") or "",
                "detail": rep.get("detail") or rep.get("evidence") or "",
                "html_snippet": rep.get("html_snippet"),
                "location": rep.get("location"),
            }
        )

    integrated = results.get("integrated_results", {}) or {}
    legal_score = _resolve_legal_score(results, integrated)
    integrated["legal_score"] = legal_score
    scores = {
        "seo": _safe_int(integrated.get("seo_score", 0)),
        "aio": _safe_int(integrated.get("aio_score", 0)),
        "legal": legal_score,
    }
    run_id = save_analysis_run(
        url,
        scores,
        issues,
        is_ec=bool(results.get("is_ec", True)),
    )

    previous_run: Optional[Dict[str, Any]]
    try:
        previous_run = get_previous_run(url, run_id)
    except Exception:
        previous_run = None

    analyzed_at = _safe_text(results.get("timestamp")) or datetime.now().isoformat()
    result_path = _write_result_payload(run_id, results)
    snapshot = _build_ui_snapshot(
        run_id,
        analyzed_at,
        results,
        previous_run,
        competitor_results=competitor_results,
        competitor_action_advice=competitor_action_advice,
        competitor_blocked=competitor_blocked,
        competitor_error=competitor_error,
    )
    try:
        update_run_artifacts(
            run_id,
            result_path=str(result_path),
            snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        )
    except Exception as artifact_exc:
        print(f"[WARNING] run artifact update error: {artifact_exc}")

    crawl_pages = []
    result_pages = results.get("crawl_pages")
    if isinstance(result_pages, list):
        crawl_pages.extend([page for page in result_pages if isinstance(page, dict)])
    if not crawl_pages:
        strategy = results.get("crawl_strategy") or {}
        priority_pages = strategy.get("priority_pages") or []
        depth = strategy.get("depth")
        for page_url in priority_pages:
            if page_url:
                crawl_pages.append(
                    {
                        "url": page_url,
                        "depth": depth,
                        "status_code": None,
                        "has_schema": None,
                    }
                )
    if crawl_pages:
        save_crawl_pages(run_id, crawl_pages)
    return run_id


def load_saved_run_bundle(run_id: int) -> Optional[Dict[str, Any]]:
    run_detail = get_run_detail(run_id)
    if not run_detail:
        return None

    snapshot = None
    snapshot_raw = _safe_text(run_detail.get("snapshot_json"))
    if snapshot_raw:
        try:
            snapshot = json.loads(snapshot_raw)
        except json.JSONDecodeError:
            snapshot = None

    result_data = None
    result_path_raw = _safe_text(run_detail.get("result_path"))
    if result_path_raw:
        result_path = Path(result_path_raw)
        if result_path.exists():
            try:
                result_data = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result_data = None

    refreshed_snapshot = False
    if result_data and (snapshot is None or _snapshot_needs_refresh(snapshot)):
        previous_run = get_previous_run(_safe_text(run_detail.get("url")), int(run_detail.get("id", 0)))
        snapshot = _build_ui_snapshot(
            int(run_detail["id"]),
            _safe_text(run_detail.get("analyzed_at")) or datetime.now().isoformat(),
            result_data,
            previous_run,
        )
        refreshed_snapshot = True
    if refreshed_snapshot and snapshot:
        try:
            update_run_artifacts(
                int(run_detail["id"]),
                snapshot_json=json.dumps(snapshot, ensure_ascii=False),
            )
        except Exception:
            pass

    same_url_history = get_history(url=_safe_text(run_detail.get("url")), limit=12)
    return {
        "run": run_detail,
        "snapshot": snapshot or {},
        "result": result_data or {},
        "same_url_history": same_url_history,
    }


def build_token_usage_text(token_summary: Any, *, partial: bool = False) -> Optional[str]:
    if token_summary is None:
        return None
    if int(getattr(token_summary, "total_requests", 0) or 0) <= 0:
        return None

    tokens_encoded = format_encoded_tokens(
        getattr(token_summary, "total_input_tokens", 0),
        getattr(token_summary, "total_output_tokens", 0),
    )
    cost_encoded = format_encoded_cost(
        getattr(token_summary, "total_cost_jpy", 0),
        getattr(token_summary, "total_cost_usd", 0),
    )
    if partial:
        return f"📊 トークン使用量（途中まで）: {tokens_encoded} | コスト: {cost_encoded}"
    requests_encoded = encode_token_count(getattr(token_summary, "total_requests", 0))
    return (
        f"📊 トークン使用量: {tokens_encoded} | "
        f"コスト: {cost_encoded} | "
        f"API呼び出し: {requests_encoded}回"
    )
