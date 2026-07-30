# -*- coding: utf-8 -*-
"""SEO tab rendering logic."""

from typing import Any, Dict, Callable

from nicegui import ui

from core.application.accessibility_improvement_builder import build_accessibility_improvement_actions


def _normalize_status(status: Any) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"fail", "要対応"}:
        return "fail"
    if normalized in {"warn", "warning", "注意", "要確認"}:
        return "warn"
    if normalized in {"pass", "ok", "通過", "問題なし"}:
        return "pass"
    if normalized in {"reference", "info", "参考"}:
        return "reference"
    return "reference"


def _status_label(status: Any) -> str:
    return {
        "fail": "要対応",
        "warn": "注意",
        "pass": "通過",
        "reference": "参考",
    }.get(_normalize_status(status), "参考")


def _status_badge_classes(status: Any) -> str:
    return {
        "fail": "bg-red-50 text-red-700",
        "warn": "bg-amber-50 text-amber-700",
        "pass": "bg-emerald-50 text-emerald-700",
        "reference": "bg-slate-100 text-slate-600",
    }.get(_normalize_status(status), "bg-slate-100 text-slate-600")


def _status_sort_key(status: Any) -> int:
    return {
        "fail": 0,
        "warn": 1,
        "pass": 2,
        "reference": 3,
    }.get(_normalize_status(status), 9)


def _merge_status(*statuses: Any) -> str:
    normalized = [_normalize_status(status) for status in statuses if str(status or "").strip()]
    if "fail" in normalized:
        return "fail"
    if "warn" in normalized:
        return "warn"
    if "pass" in normalized:
        return "pass"
    return "reference"


def _accessibility_audience(action: Dict[str, Any]) -> Dict[str, Any]:
    audience = action.get("audience")
    if isinstance(audience, dict) and audience:
        return audience
    return {
        "action": "検出された箇所について、見えない環境でも内容や操作目的が伝わるか見直してください。",
        "impact": "検索・AI回答・読み上げにページ内容が伝わりやすくなります。",
        "review_area": "該当する画像・ボタン・入力欄・見出し",
        "handoff_to": "Web制作担当またはフロントエンド担当",
        "confirmation": "対象要素と実装確認は技術補足で確認してください。",
    }


def _build_additional_audit_rows(seo_results: Dict[str, Any], provider_readiness: Dict[str, Any]) -> list[dict]:
    technical = seo_results.get("technical", {}) or {}
    structure = seo_results.get("structure", {}) or {}
    web_vitals = seo_results.get("web_vitals", {}) or {}
    rows = []

    international = technical.get("international_targeting", {}) or {}
    x_robots = technical.get("x_robots_tag", {}) or {}
    mobile_parity = technical.get("mobile_parity", {}) or {}
    page_experience = technical.get("page_experience", {}) or {}
    link_quality = structure.get("link_quality", {}) or {}
    media_discovery = technical.get("media_discovery", {}) or {}

    if international or x_robots:
        detail = " / ".join(
            [item for item in [international.get("summary"), x_robots.get("summary")] if item]
        )
        rows.append(
            {
                "title": "国際化 / インデックス制御",
                "status": _merge_status(international.get("status"), x_robots.get("status")),
                "detail": detail,
                "source_label": "実データ",
            }
        )

    if mobile_parity or page_experience:
        detail_bits = []
        if web_vitals.get("lcp_ms") is not None:
            detail_bits.append(f"LCP簡易推定 {float(web_vitals.get('lcp_ms')):.0f}ms")
        if web_vitals.get("cls_score") is not None:
            detail_bits.append(f"CLS簡易推定 {float(web_vitals.get('cls_score')):.3f}")
        if page_experience.get("summary"):
            detail_bits.append(str(page_experience.get("summary")))
        rows.append(
            {
                "title": "モバイル / ページ体験",
                "status": _merge_status(mobile_parity.get("status"), page_experience.get("status")),
                "detail": " / ".join(detail_bits),
                "source_label": "実データ＋簡易推定",
            }
        )

    if link_quality:
        rows.append(
            {
                "title": "リンク品質",
                "status": _normalize_status(link_quality.get("status")),
                "detail": str(link_quality.get("summary") or ""),
                "source_label": "実データ",
            }
        )

    if media_discovery:
        rows.append(
            {
                "title": "画像 / 動画の発見性",
                "status": _normalize_status(media_discovery.get("status")),
                "detail": str(media_discovery.get("summary") or ""),
                "source_label": "実データ",
            }
        )

    special_notes = provider_readiness.get("special_notes") or {}
    openai_commerce = special_notes.get("openai_commerce") or {}
    if openai_commerce:
        rows.append(
            {
                "title": "OpenAI Commerce",
                "status": _normalize_status(openai_commerce.get("status")),
                "detail": str(openai_commerce.get("summary") or ""),
                "source_label": "実データ",
            }
        )
    perplexity_note = special_notes.get("perplexity_operational") or {}
    if perplexity_note:
        rows.append(
            {
                "title": "Perplexity WAF / IP",
                "status": _normalize_status(perplexity_note.get("status") or "reference"),
                "detail": str(perplexity_note.get("summary") or ""),
                "source_label": "参考",
            }
        )

    return sorted(rows, key=lambda row: (_status_sort_key(row.get("status")), str(row.get("title") or "")))


def render_seo_tab(
    seo_results: Dict[str, Any],
    aio_results: Dict[str, Any],
    trim_text: Callable[[str, int], str],
    format_reason_text_ui: Callable[[str], str],
    site_health: Dict[str, Any] | None = None,
) -> None:
    """Render the SEO tab."""
    if not seo_results:
        ui.label("SEO分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
        return

    basics = seo_results.get("basics", {})
    structure = seo_results.get("structure", {})
    technical = seo_results.get("technical", {})
    web_vitals = seo_results.get("web_vitals", {})
    provider_readiness = aio_results.get("provider_readiness") or (aio_results.get("details") or {}).get("provider_readiness") or {}
    seo_actions = seo_results.get("immediate_actions", [])
    if not basics and not structure and not technical and not seo_actions:
        ui.label("SEO分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
        return

    ui.label("基本SEO情報").classes("card-title")
    ui.label(f"タイトル: {basics.get('title') or '未取得'}").classes("card-sub")
    ui.label(f"説明文: {basics.get('meta_description') or '未取得'}").classes("card-sub")

    ui.label("ページ構造").classes("card-title")
    ui.label(f"内部リンク数: {structure.get('internal_links_count', 0)}").classes("card-sub")
    ui.label(f"外部リンク数: {structure.get('external_links_count', 0)}").classes("card-sub")
    ui.label(f"画像数: {structure.get('images_count', 0)}").classes("card-sub")

    audit_rows = _build_additional_audit_rows(seo_results, provider_readiness)

    if audit_rows:
        counts = {"fail": 0, "warn": 0, "pass": 0, "reference": 0}
        for row in audit_rows:
            counts[_normalize_status(row.get("status"))] += 1
        with ui.card().classes("card implementation-note-card p-4 w-full mt-3"):
            ui.label(
                f"追加SEO監査: 要対応 {counts['fail']}件 / 注意 {counts['warn']}件 / 通過 {counts['pass']}件 / 参考 {counts['reference']}件"
            ).classes("card-title")
            with ui.expansion("項目ごとの詳細を見る", icon="unfold_more", value=False).classes("w-full mt-2"):
                for row in audit_rows:
                    with ui.card().classes("card p-4 w-full mt-2"):
                        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                            ui.label(str(row.get("title") or "-")).classes("card-sub font-bold")
                            with ui.row().classes("items-center gap-2 flex-wrap"):
                                ui.label(_status_label(row.get("status"))).classes(
                                    f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(row.get('status')) }"
                                )
                                if row.get("source_label"):
                                    ui.label(str(row.get("source_label"))).classes("fixed-chip")
                        if row.get("detail"):
                            ui.label(str(row.get("detail"))).classes("card-hint")

    accessibility_payload = build_accessibility_improvement_actions(site_health or {}, limit=5)
    accessibility_actions = accessibility_payload.get("actions") or []
    if accessibility_actions:
        with ui.card().classes("card implementation-note-card p-4 w-full mt-3"):
            ui.label(str(accessibility_payload.get("title") or "見やすさ・使いやすさ改善")).classes("card-title")
            ui.label(
                f"改善スコア: {accessibility_payload.get('score', 0)}点 / {accessibility_payload.get('summary', '検索エンジン・AI・支援技術が読み取りやすいHTML構造として扱います。')}"
            ).classes("card-sub")
            ui.label("実装の対象要素や確認方法は技術補足に分けています。ここでは影響と依頼先だけを確認します。").classes("card-hint text-xs")
            for action in accessibility_actions[:5]:
                audience = _accessibility_audience(action)
                with ui.card().classes("card p-4 w-full mt-2"):
                    with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                        ui.label(str(action.get("title") or "改善アクション")).classes("card-sub font-bold")
                        if audience.get("review_area"):
                            ui.label(str(audience.get("review_area"))).classes("fixed-chip")
                    ui.label(str(audience.get("action") or action.get("action") or "")).classes("card-sub")
                    if audience.get("impact"):
                        ui.label(f"影響: {audience.get('impact')}").classes("card-hint text-xs")
                    if audience.get("handoff_to"):
                        ui.label(f"次に渡す相手: {audience.get('handoff_to')}").classes("card-hint text-xs")
                    if audience.get("confirmation"):
                        ui.label(f"見直し箇所: {audience.get('confirmation')}").classes("card-hint text-xs")

    if seo_actions:
        ui.label("SEO 即時改善アクション（プラットフォーム別）").classes("card-title")

        for action in seo_actions[:4]:
            ui.label(format_reason_text_ui(f"- {action.get('action') or '確認項目がありません'}")).classes("card-sub whitespace-pre-line")

            method = action.get("method", "")
            if method:
                ui.label(format_reason_text_ui(trim_text(method, 240))).classes("card-hint whitespace-pre-line")
