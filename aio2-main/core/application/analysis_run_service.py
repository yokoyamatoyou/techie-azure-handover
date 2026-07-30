from __future__ import annotations

import hashlib
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
from core.application.artifact_paths import resolve_existing_result_path
from core.application.faq_suggestion_builder import (
    build_faq_suggestion_payload as _build_faq_suggestion_payload,
    build_faq_suggestions as _build_faq_suggestions,
)
from core.application.intent_role_map import build_search_intent_role_map as _build_search_intent_role_map
from core.application.technical_summary_builder import (
    build_crawl_scope_summary as _build_crawl_scope_summary,
    build_legacy_page_summary as _build_legacy_page_summary,
    build_link_health_summary as _build_link_health_summary,
    build_llms_notes as _build_llms_notes,
    build_llms_summary as _build_llms_summary,
    build_reference_notes as _build_reference_notes,
    build_schema_summary as _build_schema_summary,
    build_site_health_checks as _build_site_health_checks,
)
from core.application.accessibility_improvement_builder import build_accessibility_improvement_actions
from core.evidence_pipeline import aggregate_legal_check_results
from core.legal_checks import format_stealth_marketing_result
from core.site_health.maintenance_risk import (
    build_maintenance_risk_summary,
    technical_foundation_score_from_results,
)
from core.storage.database import (
    get_history,
    get_previous_run,
    get_run,
    get_run_detail,
    init_database,
    save_analysis_run,
    save_crawl_pages,
    update_run_artifacts,
)
from core.application.time_display import format_jst_datetime
from core.token_encoder import encode_token_count, format_encoded_cost, format_encoded_tokens

RUNS_DIR = config.POC_OUTPUT_DIR / "runs"
SNAPSHOT_SCHEMA_VERSION = 14
CANONICAL_PRIORITY_ACTION_LIMIT = 20
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
    finally:
        close_fn = getattr(competitor_analyzer, "close", None)
        if callable(close_fn):
            close_fn()


def _safe_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _accessibility_score_snapshot(results: Dict[str, Any]) -> int:
    site_health = results.get("site_health") or {}
    formatted = ((site_health.get("accessibility") or {}).get("formatted") or {})
    return _safe_int(formatted.get("score"))


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
                metric_bits.append(f"LCP簡易推定 {lcp_ms / 1000:.2f}秒")
            if cls_score is not None:
                metric_bits.append(f"CLS簡易推定 {cls_score:.3f}")
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
    }.get(_safe_text(status), "未確認")


def _normalize_status_code(status: Any, *, default: str = "unverified") -> str:
    normalized = _safe_text(status).lower()
    if normalized in {"fail", "要対応"}:
        return "fail"
    if normalized in {"warn", "warning", "注意", "要確認"}:
        return "warn"
    if normalized in {"pass", "ok", "success", "通過", "問題なし"}:
        return "pass"
    if normalized in {"reference", "info", "参考"}:
        return "reference"
    if normalized in {"unknown", "unverified", "unchecked", "未確認", "未判定"}:
        return "unverified"
    if normalized in {"not_applicable", "not-applicable", "n/a", "na", "対象外"}:
        return "not_applicable"
    if normalized in {"error", "failed", "取得エラー", "検査エラー"}:
        return "error"
    return default


def _snapshot_status_label(status: Any) -> str:
    return {
        "fail": "要対応",
        "warn": "注意",
        "pass": "通過",
        "reference": "参考",
        "unverified": "未確認",
        "not_applicable": "対象外",
        "error": "取得エラー",
    }.get(_normalize_status_code(status), "未確認")


def _extract_legal_summary_items(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    legal_summary = results.get("legal_summary") or {}

    def _is_actionable_legal_summary_item(item: Dict[str, Any]) -> bool:
        representative = item.get("representative") or {}
        legal_decision = representative.get("legal_decision") or item.get("legal_decision")
        if legal_decision in {"safe_context", "review_needed"}:
            return False
        explicit_issue_text = any(
            _safe_text(value)
            for value in (
                item.get("title"),
                item.get("summary"),
                item.get("detail"),
                item.get("issue"),
                item.get("reason"),
                item.get("recommendation"),
                representative.get("subtext"),
                representative.get("issue"),
                representative.get("reason"),
                representative.get("detail"),
            )
        )
        status = _normalize_status_code(
            item.get("status")
            or item.get("compliance_status")
            or representative.get("status")
            or representative.get("status_color"),
            default="reference",
        )
        icon = _safe_text(representative.get("icon"))
        text = _safe_text(representative.get("text"))
        pass_like_text = any(token in text for token in ("検出されず", "問題なし", "通過"))

        if status == "pass" and not explicit_issue_text:
            return False
        if icon in {"✓", "✅"} and not explicit_issue_text:
            return False
        if pass_like_text and not explicit_issue_text:
            return False
        return True

    top_issues = [
        item
        for item in (legal_summary.get("top_issues") or [])
        if isinstance(item, dict) and _is_actionable_legal_summary_item(item)
    ]

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
            if not _is_actionable_legal_summary_item(item):
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


def _refresh_saved_legal_formatters(results: Dict[str, Any]) -> Dict[str, Any]:
    """Rebuild display-only legal formatter payloads for saved runs."""
    if not isinstance(results, dict):
        return results
    legal_checks = results.get("legal_checks")
    if not isinstance(legal_checks, dict):
        return results
    stealth = legal_checks.get("stealth_marketing")
    if not isinstance(stealth, dict):
        return results
    raw = stealth.get("raw")
    if not isinstance(raw, dict):
        return results
    try:
        stealth["formatted"] = format_stealth_marketing_result(raw)
    except Exception:
        pass
    return results


def _merge_status_codes(*statuses: Any) -> str:
    normalized = [_normalize_status_code(status, default="unverified") for status in statuses if _safe_text(status)]
    if "error" in normalized:
        return "error"
    if "fail" in normalized:
        return "fail"
    if "warn" in normalized:
        return "warn"
    if "pass" in normalized:
        return "pass"
    if "unverified" in normalized:
        return "unverified"
    if "not_applicable" in normalized:
        return "not_applicable"
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
            result_path = resolve_existing_result_path(result_path_raw, runs_dir=RUNS_DIR)
            if result_path is None:
                raise OSError("result_path_outside_runs_dir")
            result_payload = json.loads(result_path.read_text(encoding="utf-8"))
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


_IMPACT_RANK = {"高": 3, "中": 2, "低": 1}
_URGENCY_RANK = {"高": 3, "中": 2, "低": 1}
_EFFORT_RANK = {"低": 3, "中": 2, "高": 1}
_CATEGORY_RANK = {
    "アクセシビリティ": 0,
    "法務": 1,
    "技術": 2,
    "AIO": 3,
    "SEO": 4,
}

_CRITICAL_ACCESSIBILITY_GROUPS = {
    "image_alt",
    "interactive_names",
    "form_labels",
    "color_contrast",
    "zoom_scaling",
    "aria_semantics",
    "keyboard_focus",
}
_SEO_ACCESSIBILITY_GROUPS = {"image_alt", "html_lang", "title", "h1", "heading_hierarchy", "landmarks", "screen_reader_structure"}


def _normalized_rank(value: Any, rank_map: Dict[str, int], *, default: str = "中") -> str:
    text = _safe_text(value)
    lowered = text.lower()
    if text in rank_map:
        return text
    if lowered in {"high", "critical", "fail", "要対応", "重要"}:
        return "高"
    if lowered in {"medium", "warning", "warn", "注意", "要確認"}:
        return "中"
    if lowered in {"low", "info", "reference", "参考"}:
        return "低"
    return default


def _effort_bucket(value: Any) -> str:
    text = _safe_text(value)
    if not text:
        return "中"
    lowered = text.lower()
    if any(token in lowered for token in ("0.5", "30", "1h", "90分", "低")):
        return "低"
    if any(token in lowered for token in ("4h", "1日", "high", "高")):
        return "高"
    return "中"


def _normalize_priority_action(
    *,
    category: str,
    title: str,
    action: str,
    area: Optional[str] = None,
    label: str = "対象ページで確認",
    detail: str = "",
    role: str = "運用",
    effort: str = "0.5-2h",
    impact: Any = "中",
    urgency: Any = "中",
    kpi: str = "",
    target_element: str = "",
    group: str = "",
) -> Dict[str, Any]:
    normalized_category = _safe_text(category) or "SEO"
    normalized_effort = _effort_bucket(effort)
    item = {
        "area": _safe_text(area) or normalized_category,
        "label": _safe_text(label) or "対象ページで確認",
        "title": _safe_text(title) or "改善提案",
        "action": _safe_text(action),
        "detail": _safe_text(detail),
        "role": _safe_text(role) or "運用",
        "effort": normalized_effort,
        "effort_detail": _safe_text(effort),
        "kpi": _safe_text(kpi) or normalized_category,
        "impact": _normalized_rank(impact, _IMPACT_RANK),
        "urgency": _normalized_rank(urgency, _URGENCY_RANK),
        "category": normalized_category,
    }
    if target_element:
        item["target_element"] = _safe_text(target_element)
    if group:
        item["group"] = _safe_text(group)
    return item


def _canonical_action_id(item: Dict[str, Any]) -> str:
    identity = [
        _safe_text(item.get("category")),
        _safe_text(item.get("area")),
        _safe_text(item.get("group")),
        _safe_text(item.get("title")),
        _safe_text(item.get("action")),
    ]
    digest = hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return f"act_{digest}"


def _canonical_action_audience(item: Dict[str, Any]) -> Dict[str, str]:
    audience = item.get("audience")
    if isinstance(audience, dict):
        return {
            "role": _safe_text(audience.get("role") or item.get("role")) or "運用",
            "label": _safe_text(audience.get("label") or item.get("label")) or "対象ページで確認",
        }
    return {
        "role": _safe_text(item.get("role")) or "運用",
        "label": _safe_text(item.get("label")) or "対象ページで確認",
    }


def _canonical_action_evidence(item: Dict[str, Any]) -> Dict[str, str]:
    evidence = item.get("evidence")
    if isinstance(evidence, dict):
        return {
            "source": _safe_text(evidence.get("source") or item.get("category")) or "分析結果",
            "detail": _safe_text(evidence.get("detail") or item.get("detail")),
            "group": _safe_text(evidence.get("group") or item.get("group")),
        }
    return {
        "source": _safe_text(item.get("category")) or "分析結果",
        "detail": _safe_text(item.get("detail")),
        "group": _safe_text(item.get("group")),
    }


def _priority_action_sort_key(row: tuple[int, Dict[str, Any]]) -> tuple[int, int, int, int, int, int]:
    index, item = row
    impact = _IMPACT_RANK.get(_safe_text(item.get("impact")), 2)
    urgency = _URGENCY_RANK.get(_safe_text(item.get("urgency")), 2)
    effort = _EFFORT_RANK.get(_safe_text(item.get("effort")), 2)
    category = _CATEGORY_RANK.get(_safe_text(item.get("category")), 9)
    affected = _safe_int(item.get("affected_count"))
    return (-impact, -urgency, -effort, category, -affected, index)


def _is_critical_accessibility_group(group: Dict[str, Any]) -> bool:
    group_id = _safe_text(group.get("id"))
    if group_id not in _CRITICAL_ACCESSIBILITY_GROUPS:
        return False
    max_severity = _safe_text(group.get("max_severity"))
    if max_severity:
        return max_severity == "critical"
    status = _safe_text(group.get("status"))
    affected_count = _safe_int(group.get("affected_count"))
    total_count = _safe_int(group.get("total_count"))
    if status == "needs_work":
        return True
    return affected_count >= 2 or (total_count > 0 and affected_count == total_count)


def _build_accessibility_priority_actions(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    payload = build_accessibility_improvement_actions(results.get("site_health") or {}, limit=8)
    raw = (((results.get("site_health") or {}).get("accessibility") or {}).get("raw") or {})
    groups = {
        _safe_text(group.get("id")): group
        for group in (raw.get("issue_groups") or [])
        if isinstance(group, dict)
    }

    actions: List[Dict[str, Any]] = []
    for rec in payload.get("actions") or []:
        group_id = _safe_text(rec.get("group"))
        audience = rec.get("audience") if isinstance(rec.get("audience"), dict) else {}
        group = groups.get(group_id, {})
        is_critical = _is_critical_accessibility_group(group)
        if is_critical:
            area = "見やすさ・使いやすさ"
            impact = "高"
            urgency = "高"
            role = "制作/開発"
            kpi = "見やすさ・使いやすさ / SEO / AI認識"
        else:
            area = "SEO改善" if group_id in _SEO_ACCESSIBILITY_GROUPS else "技術補足"
            impact = "中"
            urgency = "中"
            role = "運用" if area == "SEO改善" else "エンジニア"
            kpi = "SEO" if area == "SEO改善" else "技術品質"
        normalized = _normalize_priority_action(
            category="アクセシビリティ",
            area=area,
            label="自動検出",
            title=_safe_text(rec.get("title")) or "見やすさ・使いやすさ改善",
            action=_safe_text(audience.get("action") or rec.get("action")),
            detail=_safe_text(audience.get("impact") or rec.get("reason")),
            role=role,
            effort="0.5-2h",
            impact=impact,
            urgency=urgency,
            kpi=kpi,
            group=group_id,
        )
        normalized["affected_count"] = _safe_int(rec.get("affected_count"))
        actions.append(normalized)
    return actions



def _build_priority_actions(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    legacy_report = _build_legacy_page_summary(results)
    if _safe_int(legacy_report.get("found_count")) > 0:
        sample_urls = [
            _safe_text(item.get("final_url") or item.get("url"))
            for item in (legacy_report.get("pages") or [])[:2]
            if isinstance(item, dict) and _safe_text(item.get("final_url") or item.get("url"))
        ]
        detail = " / ".join(sample_urls)
        actions.append(
            _normalize_priority_action(
                category="技術",
                area="技術補足",
                label="公開リスク",
                title="古い公開ページを整理",
                action="検索やAI回答が古い情報を拾わないよう、古いURLを現行ページへ整理してください。対応は制作・開発担当に依頼する内容です。",
                detail=detail,
                role="エンジニア",
                effort="0.5-2h",
                kpi="SEO / AI回答",
                impact="高",
                urgency="高",
            )
        )

    actions.extend(_build_accessibility_priority_actions(results))

    for issue in _extract_legal_summary_items(results)[:6]:
        title = _safe_text(issue.get("title")) or "表現・見せ方の確認"
        action = _safe_text(issue.get("summary") or issue.get("detail"))
        if not action:
            continue
        severity = _safe_text(issue.get("severity"))
        actions.append(
            _normalize_priority_action(
                category="法務",
                area="表示アドバイス",
                label="対象ページで確認",
                title=title,
                action=action,
                detail=_safe_text(issue.get("detail")),
                role="表示確認",
                effort="0.5-2h",
                kpi="法務 / 信頼",
                impact="高" if severity == "high" else "中",
                urgency="高" if severity == "high" else "中",
            )
        )

    business_actions = ((results.get("deep_recommendations") or {}).get("business") or [])[:6]
    for rec in business_actions:
        title = _safe_text(rec.get("title")) or "改善提案"
        action = _safe_text(rec.get("recommended_action")) or _safe_text(rec.get("current_issue"))
        if not action:
            continue
        actions.append(
            _normalize_priority_action(
                category="AIO",
                area="AI認識改善",
                label="対象ページで確認",
                title=title,
                action=action,
                detail=_safe_text(rec.get("expected_impact")),
                role="運用",
                effort="0.5-2h",
                kpi="AI認識",
                impact=rec.get("expected_impact") or "中",
                urgency="中",
            )
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
            _normalize_priority_action(
                category="SEO",
                area="SEO改善",
                label="対象ページで確認",
                title=title,
                action=action,
                detail=detail,
                role="運用",
                effort="0.5-2h",
                kpi="SEO",
                impact=rec.get("impact") if isinstance(rec, dict) else "中",
                urgency="中",
            )
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
            _normalize_priority_action(
                category="AIO",
                area="AI認識改善",
                label="対象ページで確認",
                title=title[:64],
                action=action,
                detail=detail,
                role="運用",
                effort="1-3h",
                kpi="AI認識",
                impact="中",
                urgency="中",
            )
        )

    technical_actions = ((results.get("deep_recommendations") or {}).get("technical") or [])[:6]
    for rec in technical_actions:
        title = _safe_text(rec.get("title")) or "技術改善"
        action = _safe_text(rec.get("implementation")) or _safe_text(rec.get("current_issue"))
        if not action:
            continue
        actions.append(
            _normalize_priority_action(
                category="技術",
                area="技術補足",
                label="対象ページで確認",
                title=title,
                action=action,
                detail=_safe_text(rec.get("expected_impact")),
                role="エンジニア",
                effort="1-4h",
                kpi="技術品質",
                impact=rec.get("expected_impact") or "中",
                urgency="中",
            )
        )

    intent_role_map = _build_search_intent_role_map(results)
    if intent_role_map:
        missing = intent_role_map.get("missing_content") or []
        actions.append(
            _normalize_priority_action(
                category="SEO",
                area="検索意図",
                label="対象ページで確認",
                title=f"{intent_role_map.get('page_role') or 'ページ役割'}として不足を補う",
                action=_safe_text(intent_role_map.get("recommended_action")),
                detail="不足: " + (" / ".join(str(item) for item in missing) if missing else "大きな不足は未検出"),
                role="運用",
                effort="1-3h",
                impact="低",
                urgency="低",
                kpi="検索意図",
                group="search_intent",
            )
        )

    deduped: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in actions:
        key = (item["area"], item["title"], item["action"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    ranked = [item for _, item in sorted(enumerate(deduped), key=_priority_action_sort_key)]
    canonical_actions: List[Dict[str, Any]] = []
    for rank, item in enumerate(ranked[:CANONICAL_PRIORITY_ACTION_LIMIT], 1):
        canonical = dict(item)
        canonical["action_id"] = _canonical_action_id(canonical)
        canonical["priority_rank"] = rank
        canonical["priority"] = _task_priority_for_index(rank - 1)
        canonical["audience"] = _canonical_action_audience(canonical)
        canonical["evidence"] = _canonical_action_evidence(canonical)
        canonical["status"] = _normalize_status_code(
            canonical.get("status") or canonical.get("evidence_status"),
            default="unverified",
        )
        canonical["status_label"] = _snapshot_status_label(canonical["status"])
        canonical_actions.append(canonical)
    return canonical_actions


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




























def _build_seo_audit_notes(results: Dict[str, Any]) -> List[Dict[str, str]]:
    seo_results = results.get("seo_results") or {}
    technical = seo_results.get("technical") or {}
    structure = seo_results.get("structure") or {}
    web_vitals = seo_results.get("web_vitals") or {}
    provider_readiness = _get_provider_readiness(results)
    special_notes = provider_readiness.get("special_notes") or {}
    legacy_summary = _build_legacy_page_summary(results)

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

    if _safe_int(legacy_summary.get("found_count")) > 0:
        append_note(
            "古い公開ページ",
            _safe_text(legacy_summary.get("detail")),
            status="fail",
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
            source="heuristic",
            source_label="実データ＋簡易推定",
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
    accessibility_score = _accessibility_score_snapshot(results)
    maintenance_summary = build_maintenance_risk_summary(results)
    technical_foundation_score = technical_foundation_score_from_results(results)
    warnings = [_safe_text(item) for item in (results.get("warnings") or []) if _safe_text(item)]
    legacy_summary = _build_legacy_page_summary(results)
    intent_role_map = _build_search_intent_role_map(results)
    legacy_found_count = _safe_int(legacy_summary.get("found_count"))
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

    if legacy_found_count > 0:
        sample_urls = [
            _safe_text(item.get("final_url") or item.get("url"))
            for item in (legacy_summary.get("pages") or [])[:2]
            if isinstance(item, dict) and _safe_text(item.get("final_url") or item.get("url"))
        ]
        detail = _safe_text(legacy_summary.get("detail"))
        if sample_urls:
            detail = f"{detail} 例: {', '.join(sample_urls)}"
        blocking_issues.insert(
            0,
            {
                "title": "古い公開ページの整理",
                "detail": detail,
                "label": "公開リスク",
                "status": "fail",
                "category": "legacy_pages",
            },
        )

    missing_content = [
        _safe_text(item)
        for item in (intent_role_map.get("missing_content") or [])
        if _safe_text(item)
    ]
    previous_label = _safe_text(previous_diff.get("label"))
    top_action_title = _safe_text((actions[0] or {}).get("title")) if actions else ""
    summary_lines = [
        line
        for line in [
            f"ページ役割: {_safe_text(intent_role_map.get('page_role'))}" if _safe_text(intent_role_map.get("page_role")) else "",
            f"不足: {', '.join(missing_content[:3])}" if missing_content else "",
            f"最初の一手: {top_action_title}" if top_action_title else "",
            f"前回比: {previous_label}" if previous_label and previous_label != "前回なし" else "",
            f"業界見立て: {_safe_text(((results.get('final_industry') or {}).get('primary'))) or '未判定'}",
            f"サイト種別: {_safe_text(((results.get('url_type') or {}).get('effective'))) or '未判定'}",
            f"プラットフォーム: {_safe_text(((results.get('platform') or {}).get('effective'))) or '未判定'}",
        ]
        if line
    ][:7]

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
        "accessibility_score_snapshot": accessibility_score,
        "maintenance_risk_score_snapshot": maintenance_summary.get("score", 100),
        "technical_foundation_score_snapshot": technical_foundation_score,
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
            *(
                [
                    {
                        "label": "公開リスク",
                        "detail": "古い公開ページの確認件数",
                        "count": legacy_found_count,
                        "status": "fail",
                    }
                ]
                if legacy_found_count > 0
                else []
            ),
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
        "summary_personalization_version": 1,
        "top_actions": actions[:3],
        "intent_role_map": intent_role_map,
        "previous_diff": previous_diff,
    }


def _build_task_workspace(results: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    task_actions: List[Dict[str, Any]] = []

    for index, item in enumerate(actions):
        task_actions.append(
            {
                "action_id": _safe_text(item.get("action_id")),
                "priority_rank": _safe_int(item.get("priority_rank")) or index + 1,
                "area": _safe_text(item.get("area")),
                "category": _safe_text(item.get("category")),
                "group": _safe_text(item.get("group")),
                "title": _safe_text(item.get("title")) or "改善提案",
                "action": _safe_text(item.get("action")),
                "detail": _safe_text(item.get("detail")),
                "owner": _safe_text(item.get("role")) or "運用",
                "priority": _safe_text(item.get("priority")) or _task_priority_for_index(index),
                "effort": _safe_text(item.get("effort")) or "0.5-2h",
                "impact": _safe_text(item.get("impact")) or _safe_text(item.get("detail")),
                "kpi": _safe_text(item.get("kpi")),
                "label": _safe_text(item.get("label")) or "対象ページで確認",
                "affected_count": _safe_int(item.get("affected_count")),
                "audience": _json_clone(item.get("audience")) or {},
                "evidence": _json_clone(item.get("evidence")) or {},
                "status": _normalize_status_code(item.get("status"), default="unverified"),
                "status_label": _snapshot_status_label(item.get("status")),
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
    accessibility_improvements = build_accessibility_improvement_actions(
        results.get("site_health") or {},
        limit=8,
    )
    maintenance_summary = build_maintenance_risk_summary(results)
    return {
        "provider_matrix": _build_provider_status_rows(results),
        "provider_payload": _json_clone(provider_readiness) or {},
        "google_controls": _json_clone(provider_readiness.get("google_controls") or {}) or {},
        "informational_notes": _json_clone(provider_readiness.get("informational_notes") or []) or [],
        "llms_notes": _build_llms_notes(results),
        "llms_summary": _build_llms_summary(results),
        "seo_audit_notes": _build_seo_audit_notes(results),
        "intent_role_map": _build_search_intent_role_map(results),
        "schema_summary": _build_schema_summary(results),
        "link_health_summary": _build_link_health_summary(results),
        "crawl_scope_summary": _build_crawl_scope_summary(results),
        "legacy_page_summary": _build_legacy_page_summary(results),
        "site_health_checks": _build_site_health_checks(results),
        "maintenance_risk": maintenance_summary,
        "accessibility_improvements": accessibility_improvements,
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
    legacy_page_summary = implementation_workspace.get("legacy_page_summary") or {}
    intent_role_map = implementation_workspace.get("intent_role_map") or {}
    summary_cards = [
        item
        for item in [legacy_page_summary, schema_summary, llms_summary, link_health_summary]
        if isinstance(item, dict) and _safe_text(item.get("detail"))
    ]
    return {
        "actions": implementation_workspace.get("technical_actions") or [],
        "summary_cards": summary_cards,
        "crawl_scope": crawl_scope_summary,
        "intent_role_map": intent_role_map,
        "legacy_pages": legacy_page_summary,
        "link_health": link_health_summary,
        "schema": schema_summary,
        "llms": llms_summary,
        "site_health_checks": implementation_workspace.get("site_health_checks") or [],
        "maintenance_risk": implementation_workspace.get("maintenance_risk") or {},
        "accessibility_improvements": implementation_workspace.get("accessibility_improvements") or {},
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
            "analyzed_at_display": format_jst_datetime(analyzed_at),
            "url": _safe_text(results.get("url")),
        },
        "run_note": f"保存日時: {format_jst_datetime(analyzed_at)} / run_id: {run_id}",
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
            "analyzed_at_display": format_jst_datetime(analyzed_at),
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
            "run_note": comparison_workspace.get("run_note") or f"保存日時: {format_jst_datetime(analyzed_at)} / run_id: {run_id}",
        },
        "technical_workspace": technical_workspace,
        "exports": {
            "priority_actions": actions,
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
    exports = snapshot.get("exports") or {}
    priority_actions = exports.get("priority_actions") or []
    task_actions = (snapshot.get("task_workspace") or {}).get("actions") or []
    top_actions = (snapshot.get("summary_workspace") or {}).get("top_actions") or []
    for action in [*priority_actions, *task_actions, *top_actions]:
        if not isinstance(action, dict):
            return True
        if any(key not in action for key in ("action_id", "priority_rank", "audience", "evidence", "status")):
            return True
    for required_key in ("llms_summary", "schema_summary", "link_health_summary", "crawl_scope_summary", "site_health_checks", "intent_role_map"):
        if required_key not in implementation:
            return True
    technical_workspace = snapshot.get("technical_workspace") or {}
    for required_key in ("summary_cards", "crawl_scope", "intent_role_map", "link_health", "schema", "llms", "site_health_checks"):
        if required_key not in technical_workspace:
            return True
    summary_workspace = snapshot.get("summary_workspace") or {}
    if "accessibility_score_snapshot" not in summary_workspace:
        return True
    if _safe_int(summary_workspace.get("summary_personalization_version")) < 1:
        return True
    headline_metrics = summary_workspace.get("headline_metrics") or []
    if any(_safe_text(item.get("label")) == "法務" for item in headline_metrics if isinstance(item, dict)):
        return True
    priority_counts = summary_workspace.get("priority_counts") or []
    if any(_safe_text(item.get("label")) == "法務・表示" for item in priority_counts if isinstance(item, dict)):
        return True
    return False


def _preserve_persisted_snapshot_context(
    rebuilt_snapshot: Dict[str, Any],
    persisted_snapshot: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not isinstance(persisted_snapshot, dict):
        return rebuilt_snapshot

    persisted_comparison = persisted_snapshot.get("comparison_workspace") or {}
    persisted_competitor = persisted_comparison.get("competitor_summary")
    if isinstance(persisted_competitor, dict) and persisted_competitor:
        comparison = rebuilt_snapshot.setdefault("comparison_workspace", {})
        comparison["competitor_summary"] = _json_clone(persisted_competitor)

    meta = rebuilt_snapshot.setdefault("meta", {})
    meta["view_rehydrated_from_schema_version"] = _safe_int(persisted_snapshot.get("schema_version"))
    meta["persisted_snapshot_unchanged"] = True
    return rebuilt_snapshot


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

    saved_run = get_run(run_id) or {}
    analyzed_at = _safe_text(saved_run.get("analyzed_at")) or _safe_text(results.get("timestamp")) or datetime.now().isoformat()
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
        result_path = resolve_existing_result_path(result_path_raw, runs_dir=RUNS_DIR)
        if result_path is not None:
            try:
                result_data = json.loads(result_path.read_text(encoding="utf-8"))
                result_data = _refresh_saved_legal_formatters(result_data)
            except json.JSONDecodeError:
                result_data = None

    persisted_snapshot = _json_clone(snapshot) if isinstance(snapshot, dict) else None
    if result_data and (snapshot is None or _snapshot_needs_refresh(snapshot)):
        previous_run = get_previous_run(_safe_text(run_detail.get("url")), int(run_detail.get("id", 0)))
        snapshot = _preserve_persisted_snapshot_context(_build_ui_snapshot(
            int(run_detail["id"]),
            _safe_text(run_detail.get("analyzed_at")) or datetime.now().isoformat(),
            result_data,
            previous_run,
        ), persisted_snapshot)

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
