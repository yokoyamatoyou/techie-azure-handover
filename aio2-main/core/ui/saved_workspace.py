# -*- coding: utf-8 -*-
"""Saved analysis workspace rendering."""

from __future__ import annotations

import re
from typing import Any, Dict

from nicegui import ui

from core.application.time_display import format_jst_datetime
from core.engineer_handoff_builder import build_engineer_handoff_items
from core.site_health.maintenance_risk import build_maintenance_risk_summary, technical_foundation_score_from_results
from core.ui.panel_components import (
    _clamp_score,
    _compact_copy,
    _diff_html,
    _display_snapshot_label,
    _extract_row_id_from_event_args,
    _headline_metric_hint,
    _normalize_status_key,
    _priority_badge_classes,
    _render_compact_note_rows,
    _render_expandable_generated_card,
    _render_snapshot_cards,
    _render_workspace_header,
    _status_badge_classes,
    _status_label,
)

def _normalized_detail_line_key(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"^[・\-\*\s]+", "", text).strip()
    return text

def _dedupe_detail_lines(
    values: list[Any],
    *,
    seen: set[str] | None = None,
    limit: int = 3,
) -> list[str]:
    if seen is None:
        seen = set()
    lines: list[str] = []
    for value in values:
        text = str(value or "").strip()
        key = _normalized_detail_line_key(text)
        if not key or key in seen:
            continue
        seen.add(key)
        lines.append(text)
        if len(lines) >= limit:
            break
    return lines

_INTENT_SIGNAL_SOURCE_LABELS = {
    "title": "タイトル",
    "heading": "見出し",
    "url_path": "URL",
    "body": "本文",
    "meta_description": "説明文",
    "schema": "構造化データ",
    "json_ld": "構造化データ",
}

_PAGE_SIGNAL_LABELS = {
    "schema_types": "構造化データ",
    "faq_count": "FAQ数",
    "heading_count": "見出し数",
    "word_count": "本文量",
    "title": "タイトル",
    "description": "説明文",
}

def _intent_signal_source_label(value: Any) -> str:
    text = str(value or "").strip()
    return _INTENT_SIGNAL_SOURCE_LABELS.get(text, text or "確認箇所")

def _page_signal_label(value: Any) -> str:
    text = str(value or "").strip()
    return _PAGE_SIGNAL_LABELS.get(text, text or "確認項目")

def _provider_check_status_label(status: Any) -> str:
    return _status_label(status)

def _provider_has_actionable_details(payload: Dict[str, Any]) -> bool:
    checks = payload.get("official_checks") or []
    heuristics = payload.get("heuristic_notes") or []
    for check in checks:
        if str(check.get("status") or "").strip().lower() in {"warn", "fail"}:
            return True
    return bool(heuristics)

def _describe_google_controls(google_controls: Dict[str, Any]) -> list[dict]:
    data_nosnippet_count = int(google_controls.get("data_nosnippet_count") or 0)
    data_nosnippet_text = "検出なし" if data_nosnippet_count <= 0 else f"{data_nosnippet_count}箇所で抜粋除外"

    return [
        {"title": "検索結果への掲載除外（noindex）", "detail": "設定あり" if google_controls.get("noindex") else "設定なし"},
        {"title": "抜粋禁止（nosnippet）", "detail": "設定あり" if google_controls.get("nosnippet") else "設定なし"},
        {"title": "部分的な抜粋除外（data-nosnippet）", "detail": data_nosnippet_text},
    ]

def _build_summary_priority_note(summary_workspace: Dict[str, Any]) -> Dict[str, str]:
    priority_counts = summary_workspace.get("priority_counts") or []
    counts = {
        str(item.get("label") or ""): int(item.get("count") or 0)
        for item in priority_counts
        if str(item.get("label") or "").strip()
    }
    provider_count = counts.get("AI公開条件", 0)
    legal_count = counts.get("表示アドバイス", counts.get("法務・表示", 0))
    public_risk_count = counts.get("公開リスク", 0)
    action_count = counts.get("最優先アクション", 0)

    if provider_count or legal_count or public_risk_count:
        title = "先に直す項目があります"
        status = "warn"
    else:
        title = "大きな停止要因は見えていません"
        status = "pass"

    risk_text = f" / 公開リスク {public_risk_count}件" if public_risk_count else ""
    detail = f"AI公開条件 {provider_count}件 / 表現・見せ方 {legal_count}件{risk_text} / すぐ見る提案 {action_count}件"
    return {"title": title, "detail": detail, "status": status}

def _safe_score_value(value: Any) -> int:
    try:
        return _clamp_score(float(value or 0))
    except (TypeError, ValueError):
        return 0

def _score_status_meta(score: Any) -> tuple[int, str, str]:
    numeric = _safe_score_value(score)
    if numeric >= 80:
        return numeric, "pass", "良好"
    if numeric >= 60:
        return numeric, "warn", "改善余地"
    return numeric, "fail", "要対応"

def _build_saved_run_overall_message(header: Dict[str, Any]) -> str:
    seo_score = _safe_score_value(header.get("seo_score"))
    aio_score = _safe_score_value(header.get("aio_score"))
    legal_score = _safe_score_value(header.get("legal_score"))

    concerns: list[str] = []
    positives: list[str] = []

    if seo_score < 60:
        concerns.append("検索の基礎が弱めです")
    elif seo_score >= 80:
        positives.append("検索の基礎は安定しています")
    else:
        positives.append("検索の基礎は大きく崩れていません")

    if aio_score < 60:
        concerns.append("AI検索で要点を拾われにくい状態です")
    elif aio_score >= 80:
        positives.append("AI検索で拾われやすい土台があります")
    else:
        positives.append("AI検索向けの土台はあります")

    if legal_score < 60:
        concerns.append("表示まわりに確認したい点があります")
    elif legal_score >= 80:
        positives.append("表示まわりの大きな不安は目立ちません")
    else:
        positives.append("表示まわりは概ね許容範囲です")

    if concerns:
        message = " / ".join(concerns[:2]) + "。"
        if positives:
            message += positives[0] + "。"
        return message
    if positives:
        return " / ".join(positives[:2]) + "。"
    return "大きく崩れている評価は見えていません。"

def _build_evaluation_axis_cards(header: Dict[str, Any]) -> list[Dict[str, str]]:
    axis_specs = [
        (
            "検索",
            header.get("seo_score"),
            "検索結果で見つけられやすいかの見立てです。",
            {
                "pass": "検索の基礎は安定しています。",
                "warn": "検索の基礎に改善余地があります。",
                "fail": "検索の基礎を先に見直したい状態です。",
            },
        ),
        (
            "AI",
            header.get("aio_score"),
            "AI検索や要約で要点を拾われやすいかの見立てです。",
            {
                "pass": "AI検索で拾われやすい土台があります。",
                "warn": "AI検索向けの構造に改善余地があります。",
                "fail": "AI検索で要点を拾われにくい状態です。",
            },
        ),
        (
            "表示",
            header.get("legal_score"),
            "表現や見せ方で不安が出にくいかの見立てです。",
            {
                "pass": "表示まわりの大きな不安は目立ちません。",
                "warn": "表示まわりは一度確認したい状態です。",
                "fail": "表示まわりを先に確認したい状態です。",
            },
        ),
    ]

    cards: list[Dict[str, str]] = []
    for label, score, hint, messages in axis_specs:
        numeric, status_key, status_label = _score_status_meta(score)
        cards.append(
            {
                "label": label,
                "score": str(numeric),
                "hint": hint,
                "status_key": status_key,
                "status_label": status_label,
                "message": messages.get(status_key, ""),
            }
        )
    return cards

def _reason_label_hint(label: str) -> str:
    mapping = {
        "AI公開条件": "AIサービス側で拾われにくくなる条件の確認です。",
        "表示アドバイス": "表現や見せ方で不安が出る箇所の確認です。",
        "分析メモ": "今回の評価に影響した補足メモです。",
    }
    return mapping.get(str(label or "").strip(), "")

def _saved_run_reason_title(item: Dict[str, Any]) -> str:
    title = str(item.get("title") or "").strip()
    if title and title not in {"要確認メモ", "補足メモ", "分析メモ"}:
        return title
    detail = str(item.get("detail") or "").strip()
    if detail:
        return _short_reason_text(detail, limit=34)
    label = _display_snapshot_label(str(item.get("label") or ""))
    if label and label != "補足メモ":
        return label
    return "要確認"

def _saved_run_reason_metric(item: Dict[str, Any]) -> str:
    label = _display_snapshot_label(str(item.get("label") or "").strip())
    if label in {"", "補足メモ"}:
        return ""
    return label

def _priority_urgency_caption(priority_level: str) -> str:
    # priority_level=高 means "needs attention soon", not "scored highly" -
    # the badge alone reads as a good score, so pair it with a plain-language caption.
    if priority_level == "高":
        return "早めの対応をおすすめします。"
    if priority_level == "中":
        return "時間のあるときに確認してください。"
    return "急ぎの対応は見当たりません。"

def _render_saved_run_overview(
    summary_workspace: Dict[str, Any],
    header: Dict[str, Any],
    previous_diff: Dict[str, Any],
) -> None:
    summary_note = _build_summary_priority_note(summary_workspace)
    summary_lines = [
        str(line).strip()
        for line in (summary_workspace.get("summary_lines") or [])
        if str(line or "").strip()
    ]
    payload = _build_workspace_improvement_map(summary_workspace, header)
    axes = payload.get("axes") or []
    diff_label = str(previous_diff.get("label") or "").strip()
    detail_parts = [str(summary_note.get("detail") or "").strip()] if str(summary_note.get("detail") or "").strip() else []
    if diff_label and diff_label != "前回なし":
        detail_parts.append(f"前回比 {diff_label}")
    if not detail_parts and not summary_lines and not axes:
        return

    ui.separator()
    with ui.row().classes("summary-visual-grid w-full mt-3"):
        with ui.card().classes("card p-4 summary-radar-card"):
            with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                ui.label(str(summary_note.get("title") or "判断")).classes("generated-title")
                ui.label(f"{len(axes)}軸").classes("fixed-chip")
            if detail_parts:
                ui.label(" / ".join(detail_parts)).classes("card-hint text-sm mt-1")
            if summary_lines:
                with ui.row().classes("w-full gap-2 flex-wrap mt-3"):
                    for line in summary_lines[:3]:
                        ui.label(line).classes("fixed-chip")
            if axes:
                chart = ui.echart(payload["options"]).classes("w-full summary-radar-chart mt-3")
                chart.style("height: 300px;")
                with ui.row().classes("w-full gap-2 flex-wrap mt-2"):
                    for axis in axes:
                        ui.label(f"{axis['label']}: {axis['value']:.0f}").classes("fixed-chip")

        with ui.column().classes("summary-visual-side gap-3"):
            weakest_axes = payload.get("weakest_axes") or []
            if weakest_axes:
                with ui.card().classes("card p-4 w-full"):
                    ui.label("低い軸").classes("card-sub font-bold")
                    for axis in weakest_axes:
                        with ui.row().classes("items-center gap-3 w-full mt-2"):
                            ui.label(str(axis.get("label") or "")).classes("card-hint font-semibold min-w-[84px]")
                            ui.linear_progress(
                                value=max(0.0, min(float(axis.get("value") or 0) / 100.0, 1.0)),
                                size="8px",
                                show_value=False,
                                color="orange",
                            ).classes("flex-1")
                            ui.label(f"{float(axis.get('value') or 0):.0f}").classes("summary-axis-score")

            alerts = payload.get("alerts") or []
            if alerts:
                with ui.card().classes("card p-4 w-full"):
                    with ui.row().classes("w-full gap-2 flex-wrap"):
                        for item in alerts:
                            tone = str(item.get("tone") or "info")
                            tone_class = {
                                "warn": "summary-pill-warn",
                                "pass": "summary-pill-pass",
                            }.get(tone, "summary-pill-info")
                            ui.label(f"{item.get('label')} {item.get('detail')}").classes(f"summary-alert-pill {tone_class}")

    _render_saved_run_intent_role_overview(summary_workspace.get("intent_role_map") or {})

def _render_saved_run_next_actions(
    summary_workspace: Dict[str, Any],
    header: Dict[str, Any],
    *,
    show_title: bool = True,
    accessibility_lookup: Dict[str, Dict[str, Any]] | None = None,
) -> None:
    top_actions = summary_workspace.get("top_actions") or (header.get("top_actions") or [])
    actionable_items = [
        item for item in top_actions[:3]
        if str(item.get("title") or "").strip() or str(item.get("action") or item.get("detail") or "").strip()
    ]
    if not actionable_items:
        return

    if show_title:
        ui.separator()
        ui.label("改善").classes("card-sub font-bold")
    with ui.element("div").classes("evaluation-reason-grid w-full mt-3"):
        for index, item in enumerate(actionable_items, 1):
            with ui.card().classes("card evaluation-reason-card p-4"):
                with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        ui.label(f"優先 {index}").classes("generated-chip")
                        area = str(item.get("area") or "").strip()
                        if area:
                            ui.label(area).classes("generated-metric")
                    effort = str(item.get("effort") or "").strip()
                    if effort:
                        ui.label(effort).classes("card-hint text-xs")
                ui.label(str(item.get("title") or "改善提案")).classes("generated-title")
                accessibility_detail = _accessibility_detail_for_item(item, accessibility_lookup or {})
                action_text, impact_text = _task_action_display_text(item, accessibility_detail)
                if action_text:
                    ui.label(_compact_copy(action_text, 150)).classes("generated-body whitespace-pre-line")
                _render_task_action_detail_lines(item, accessibility_detail)
                if impact_text:
                    ui.label(_compact_copy(impact_text, 84)).classes("card-hint text-xs")

def _render_saved_run_improvement_tab(snapshot: Dict[str, Any]) -> None:
    summary_workspace = snapshot.get("summary_workspace") or {}
    header = snapshot.get("header") or {}
    task_workspace = snapshot.get("task_workspace") or {}
    actions = task_workspace.get("actions") or []
    owner_counts = task_workspace.get("owner_counts") or {}
    primary_actions, secondary_actions = _split_task_actions(actions)
    accessibility_lookup = _build_accessibility_action_lookup(snapshot)

    with ui.card().classes("card workspace-panel p-5 w-full"):
        if owner_counts:
            with ui.row().classes("w-full gap-2 flex-wrap"):
                for owner, count in owner_counts.items():
                    ui.label(f"{owner} {count}件").classes("fixed-chip")

        if primary_actions:
            for item in primary_actions:
                _render_task_action_card(item, _accessibility_detail_for_item(item, accessibility_lookup))
        elif (summary_workspace.get("top_actions") or header.get("top_actions")):
            _render_saved_run_next_actions(
                summary_workspace,
                header,
                show_title=False,
                accessibility_lookup=accessibility_lookup,
            )
            return
        else:
            ui.label("改善案はまだ抽出されていません。").classes("card-sub text-gray-500")
            return

        if secondary_actions:
            remaining_exp = ui.expansion(f"続き {len(secondary_actions)}件", icon="unfold_more", value=False).classes("w-full mt-3")
            with remaining_exp:
                for item in _prioritize_search_intent_secondary_actions(secondary_actions):
                    _render_task_action_card(item, _accessibility_detail_for_item(item, accessibility_lookup))

def _saved_run_has_improvement_tab(snapshot: Dict[str, Any]) -> bool:
    summary_workspace = snapshot.get("summary_workspace") or {}
    header = snapshot.get("header") or {}
    task_workspace = snapshot.get("task_workspace") or {}
    return bool(
        (task_workspace.get("actions") or [])
        or (summary_workspace.get("top_actions") or [])
        or (header.get("top_actions") or [])
    )

def _saved_run_has_writing_tab(snapshot: Dict[str, Any]) -> bool:
    writing_workspace = snapshot.get("writing_workspace") or {}
    faq_summary = writing_workspace.get("faq_detection_summary") or {}
    content_plan = writing_workspace.get("content_plan") or {}
    return bool(
        (writing_workspace.get("title_rewrites") or [])
        or (writing_workspace.get("description_rewrites") or [])
        or (writing_workspace.get("body_rewrites") or [])
        or (writing_workspace.get("citation_phrases") or [])
        or (faq_summary.get("items") or [])
        or (writing_workspace.get("faq_suggestions") or [])
        or (content_plan.get("sections") or [])
    )

def _saved_run_has_implementation_tab(snapshot: Dict[str, Any]) -> bool:
    implementation_workspace = snapshot.get("implementation_workspace") or {}
    technical_workspace = snapshot.get("technical_workspace") or {}
    return bool(
        (implementation_workspace.get("provider_matrix") or [])
        or (implementation_workspace.get("provider_payload") or {})
        or (implementation_workspace.get("google_controls") or {})
        or (implementation_workspace.get("schema_summary") or {})
        or (implementation_workspace.get("llms_notes") or [])
        or (implementation_workspace.get("seo_audit_notes") or [])
        or (implementation_workspace.get("legal_display_notes") or [])
        or (implementation_workspace.get("technical_actions") or [])
        or (implementation_workspace.get("maintenance_risk") or {})
        or (technical_workspace.get("summary_cards") or [])
    )

def _saved_run_has_engineer_tab(snapshot: Dict[str, Any]) -> bool:
    technical_workspace = snapshot.get("technical_workspace") or {}
    return bool(
        (technical_workspace.get("summary_cards") or [])
        or (technical_workspace.get("crawl_scope") or {})
        or (technical_workspace.get("link_health") or {})
        or (technical_workspace.get("schema") or {})
        or (technical_workspace.get("llms") or {})
        or (technical_workspace.get("site_health_checks") or [])
        or (technical_workspace.get("maintenance_risk") or {})
        or (technical_workspace.get("action_items") or [])
        or (technical_workspace.get("actions") or [])
    )

def _saved_run_has_comparison_tab(snapshot: Dict[str, Any], same_url_history: list[dict]) -> bool:
    comparison_workspace = snapshot.get("comparison_workspace") or {}
    competitor_summary = comparison_workspace.get("competitor_summary") or {}
    previous_diff = comparison_workspace.get("previous_diff") or {}
    return bool(same_url_history or competitor_summary or previous_diff)

def _enrich_saved_snapshot_from_result(snapshot: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    if not snapshot or not result:
        return snapshot
    if (result.get("site_health") or {}).get("security"):
        maintenance_summary = build_maintenance_risk_summary(result)
        implementation_workspace = snapshot.setdefault("implementation_workspace", {})
        technical_workspace = snapshot.setdefault("technical_workspace", {})
        summary_workspace = snapshot.setdefault("summary_workspace", {})
        implementation_workspace.setdefault("maintenance_risk", maintenance_summary)
        technical_workspace.setdefault("maintenance_risk", maintenance_summary)
        summary_workspace.setdefault("maintenance_risk_score_snapshot", maintenance_summary.get("score", 100))
        foundation_score = technical_foundation_score_from_results(result)
        if foundation_score:
            summary_workspace.setdefault("technical_foundation_score_snapshot", foundation_score)
    accessibility = ((result.get("site_health") or {}).get("accessibility") or {})
    formatted = accessibility.get("formatted") or {}
    source = str(accessibility.get("source") or formatted.get("detection_source") or "").strip()
    if not source:
        return snapshot

    source_label = "実ブラウザ自動検出" if source == "browser" else "HTML自動検出"
    technical_workspace = snapshot.setdefault("technical_workspace", {})
    site_health_checks = technical_workspace.setdefault("site_health_checks", [])
    for item in site_health_checks:
        if str(item.get("key") or "").strip() != "accessibility":
            continue
        detail = str(item.get("detail") or "").strip()
        if source_label not in detail:
            item["detail"] = " / ".join(bit for bit in (detail, source_label) if bit)
        return snapshot

    score = formatted.get("score") or ((accessibility.get("raw") or {}).get("score")) or 0
    status = formatted.get("status") or ""
    site_health_checks.append(
        {
            "key": "accessibility",
            "title": "見やすさ・使いやすさ",
            "detail": " / ".join(bit for bit in (f"スコア {score}点", str(status).strip(), source_label) if bit),
            "status": "pass",
            "status_label": "通過",
            "score": score,
            "highlights": [],
            "items": [],
            "recommendations": [],
            "issues": [],
        }
    )
    return snapshot

def _render_saved_run_evaluation(bundle: Dict[str, Any]) -> None:
    snapshot = bundle.get("snapshot") or {}
    run = bundle.get("run") or {}
    meta = snapshot.get("meta") or {}
    header = snapshot.get("header") or {}
    summary_workspace = snapshot.get("summary_workspace") or {}
    priority_level = str(header.get("priority_level") or "低")
    previous_diff = header.get("previous_diff") or {}
    summary_note = _build_summary_priority_note(summary_workspace)
    evaluation_cards = _build_evaluation_axis_cards(header)
    reasons = (summary_workspace.get("blocking_issues") or [])[:4]
    analyzed_at = format_jst_datetime(run.get("analyzed_at") or meta.get("analyzed_at"))
    top_actions_preview = summary_workspace.get("top_actions") or (header.get("top_actions") or [])
    first_action_title = str((top_actions_preview[0] or {}).get("title") or "").strip() if top_actions_preview else ""

    with ui.card().classes("card evaluation-summary-card p-5 w-full"):
        with ui.row().classes("items-start justify-between w-full gap-4 flex-wrap"):
            with ui.column().classes("gap-2 min-w-[280px]"):
                ui.label("評価").classes("section-eyebrow")
                ui.label(str(meta.get("url") or run.get("url") or "-")).classes("card-title break-all")
                ui.label(_build_saved_run_overall_message(header)).classes("card-sub")
            with ui.column().classes("items-end gap-2"):
                ui.label("対応優先度").classes("card-hint text-xs")
                ui.label(priority_level).classes(
                    f"text-2xl font-bold px-3 py-1 rounded { _priority_badge_classes(priority_level) }"
                )
                ui.label(_priority_urgency_caption(priority_level)).classes("card-hint text-xs text-right")

        if first_action_title:
            ui.label(f"まず1件: {_compact_copy(first_action_title, 60)}（詳しくは下の「やること」）").classes(
                "card-sub text-sm mt-2"
            )

        with ui.row().classes("w-full gap-2 flex-wrap mt-3"):
            if analyzed_at:
                ui.label(f"分析日時: {analyzed_at}").classes("fixed-chip")
            if previous_diff and str(previous_diff.get("label") or "").strip() not in {"", "前回なし"}:
                ui.label(f"前回比 {previous_diff.get('label')}").classes("fixed-chip")
            note_chip = ui.label(str(summary_note.get("title") or "評価")).classes(
                f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(str(summary_note.get('status') or 'info')) }"
            )

        with ui.element("div").classes("evaluation-grid w-full mt-4"):
            for item in evaluation_cards:
                with ui.card().classes("card evaluation-card p-4"):
                    label = ui.label(str(item.get("label") or "")).classes("evaluation-label")
                    hint = str(item.get("hint") or "")
                    if hint:
                        label.tooltip(hint)
                    with ui.row().classes("items-end justify-between gap-3 mt-2"):
                        with ui.row().classes("items-end gap-1"):
                            ui.label(str(item.get("score") or "0")).classes("evaluation-score")
                            ui.label("/100").classes("evaluation-score-scale")
                        ui.label(str(item.get("status_label") or "")).classes(
                            f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(str(item.get('status_key') or 'info')) }"
                        )
                    ui.label(str(item.get("message") or "")).classes("card-hint text-sm mt-3")

        # 6-axis radar, weakest-axis bars, and the alert pills repeat the score
        # cards above in more detail. Collapsed by default so the summary card
        # stays scannable; still one click away, not removed.
        detail_exp = ui.expansion("詳細診断を見る（軸別スコア・ページ役割）", icon="insights", value=False).classes("w-full mt-3")
        with detail_exp:
            _render_saved_run_overview(summary_workspace, header, previous_diff)

        ui.separator()
        ui.label("理由").classes("card-sub font-bold")
        if reasons:
            with ui.element("div").classes("evaluation-reason-grid w-full mt-3"):
                for item in reasons:
                    status = str(item.get("status") or "info")
                    label_text = str(item.get("label") or "").strip()
                    with ui.card().classes("card evaluation-reason-card p-4"):
                        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                            ui.label(str(_status_label(status))).classes(
                                f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(status) }"
                            )
                            reason_metric = _saved_run_reason_metric(item)
                            if reason_metric:
                                reason_chip = ui.label(reason_metric).classes("generated-chip")
                                label_hint = _reason_label_hint(label_text)
                                if label_hint:
                                    reason_chip.tooltip(label_hint)
                        title_text = _saved_run_reason_title(item)
                        ui.label(title_text).classes("generated-title")
                        detail_text = _compact_copy(item.get("detail"), 160)
                        # title falls back to a short form of detail (see
                        # _saved_run_reason_title); skip the body line when
                        # that makes it word-for-word the same as the title.
                        if detail_text and detail_text.strip() != title_text.strip():
                            ui.label(detail_text).classes("generated-body whitespace-pre-line")
        else:
            ui.label("大きな懸念は先頭では見えていません。").classes("card-hint mt-2")

def _build_workspace_improvement_map(summary_workspace: Dict[str, Any], header: Dict[str, Any]) -> Dict[str, Any]:
    raw_priority_counts = summary_workspace.get("priority_counts") or []
    counts = {
        str(item.get("label") or "").strip(): int(item.get("count") or 0)
        for item in raw_priority_counts
        if str(item.get("label") or "").strip()
    }
    provider_count = counts.get("AI公開条件", 0)
    display_count = counts.get("表示アドバイス", counts.get("法務・表示", 0))
    action_count = counts.get("最優先アクション", 0)

    seo_score = _clamp_score(float(header.get("seo_score") or 0))
    aio_score = _clamp_score(float(header.get("aio_score") or 0))
    legal_score = _clamp_score(float(header.get("legal_score") or 0))
    accessibility_score = _clamp_score(float(
        summary_workspace.get("accessibility_score_snapshot")
        or header.get("accessibility_score")
        or 50
    ))
    provider_score = _clamp_score(100 - min(provider_count, 4) * 25)
    trust_score = _clamp_score((legal_score * 0.60) + (aio_score * 0.40))
    technical_foundation_score = _clamp_score(
        summary_workspace.get("technical_foundation_score_snapshot")
        or header.get("technical_foundation_score")
        or summary_workspace.get("maintenance_risk_score_snapshot")
        or 100
    )

    axes = [
        {"label": "SEO基礎", "value": seo_score, "hint": "検索流入の基礎"},
        {"label": "AI引用", "value": aio_score, "hint": "AI検索で拾われやすい構成"},
        {"label": "信頼情報", "value": trust_score, "hint": "著者・運営者・安心材料"},
        {"label": "公開条件", "value": provider_score, "hint": "AIサービス側の到達性"},
        {"label": "保守・技術基盤", "value": technical_foundation_score, "hint": "リンク健全性 / OGP / セキュリティ / 保守更新"},
        {"label": "見やすさ・使いやすさ", "value": accessibility_score, "hint": "自動検出 / 読み上げ / 操作名"},
    ]
    weakest_axes = sorted(axes, key=lambda item: item["value"])[:3]

    alerts = []
    if provider_count:
        alerts.append({"label": "AI公開条件", "detail": f"要確認 {provider_count}件", "tone": "warn"})
    if display_count:
        alerts.append({"label": "表示アドバイス", "detail": f"要確認 {display_count}件", "tone": "warn"})
    if action_count:
        alerts.append({"label": "最優先アクション", "detail": f"先頭で {action_count}件確認", "tone": "info"})
    if not alerts:
        alerts.append({"label": "先に確認", "detail": "大きな阻害要因は先頭では見えていません", "tone": "pass"})

    options = {
        "animation": True,
        "tooltip": {"trigger": "item"},
        "radar": {
            "radius": "66%",
            "splitNumber": 4,
            "indicator": [{"name": axis["label"], "max": 100} for axis in axes],
            "axisName": {"color": "#5B5347", "fontSize": 12, "fontWeight": "600"},
            "splitLine": {"lineStyle": {"color": "rgba(130, 113, 94, 0.18)"}},
            "splitArea": {
                "areaStyle": {
                    "color": [
                        "rgba(242, 237, 228, 0.18)",
                        "rgba(242, 237, 228, 0.28)",
                        "rgba(242, 237, 228, 0.38)",
                        "rgba(242, 237, 228, 0.48)",
                    ]
                }
            },
            "axisLine": {"lineStyle": {"color": "rgba(130, 113, 94, 0.24)"}},
        },
        "series": [{
            "type": "radar",
            "data": [{
                "value": [axis["value"] for axis in axes],
                "name": "現在地",
                "symbol": "circle",
                "symbolSize": 7,
                "lineStyle": {"color": "#D96B1F", "width": 3},
                "areaStyle": {"color": "rgba(217, 107, 31, 0.18)"},
                "itemStyle": {"color": "#B95416"},
            }],
        }],
    }

    return {
        "axes": axes,
        "weakest_axes": weakest_axes,
        "alerts": alerts[:3],
        "options": options,
    }

def _render_workspace_improvement_map(summary_workspace: Dict[str, Any], header: Dict[str, Any]) -> None:
    payload = _build_workspace_improvement_map(summary_workspace, header)
    axes = payload.get("axes") or []
    if not axes:
        return

    ui.label("改善マップ").classes("card-sub font-bold mt-4")
    with ui.row().classes("summary-visual-grid w-full mt-2"):
        with ui.card().classes("card p-4 summary-radar-card"):
            with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                ui.label(f"{len(axes)}軸で見た現在地").classes("card-sub font-bold")
                ui.label("圧縮表示").classes("fixed-chip")
            ui.label("低い軸ほど、先に直す価値が高い状態です。").classes("card-hint text-xs")
            chart = ui.echart(payload["options"]).classes("w-full summary-radar-chart")
            chart.style("height: 300px;")
            with ui.row().classes("w-full gap-2 flex-wrap mt-2"):
                for axis in axes:
                    ui.label(f"{axis['label']}: {axis['value']:.0f}").classes("fixed-chip")

        with ui.column().classes("summary-visual-side gap-3"):
            with ui.card().classes("card p-4 w-full"):
                ui.label("先に手を入れる軸").classes("card-sub font-bold")
                for axis in payload.get("weakest_axes") or []:
                    with ui.row().classes("items-center gap-3 w-full mt-2"):
                        with ui.column().classes("gap-0 min-w-[84px]"):
                            ui.label(str(axis.get("label") or "")).classes("card-hint font-semibold")
                            ui.label(str(axis.get("hint") or "")).classes("card-hint text-xs")
                        ui.linear_progress(
                            value=max(0.0, min(float(axis.get("value") or 0) / 100.0, 1.0)),
                            size="8px",
                            show_value=False,
                            color="orange",
                        ).classes("flex-1")
                        ui.label(f"{float(axis.get('value') or 0):.0f}").classes("summary-axis-score")

            with ui.card().classes("card p-4 w-full"):
                ui.label("先に確認").classes("card-sub font-bold")
                for item in payload.get("alerts") or []:
                    tone = str(item.get("tone") or "info")
                    tone_class = {
                        "warn": "summary-pill-warn",
                        "pass": "summary-pill-pass",
                    }.get(tone, "summary-pill-info")
                    with ui.row().classes("items-start gap-2 w-full mt-2"):
                        ui.label(str(item.get("label") or "")).classes(f"summary-alert-pill {tone_class}")
                        ui.label(str(item.get("detail") or "")).classes("card-hint")

def _build_provider_focus_summary(provider_matrix: list[Dict[str, Any]]) -> Dict[str, int]:
    summary = {"fail": 0, "warn": 0, "pass": 0, "other": 0}
    for row in provider_matrix:
        status = str(row.get("status") or "").strip()
        if status == "要対応":
            summary["fail"] += 1
        elif status == "注意":
            summary["warn"] += 1
        elif status == "通過":
            summary["pass"] += 1
        else:
            summary["other"] += 1
    return summary

def _build_implementation_stop_message(*, actionable_count: int, refresh_count: int) -> str:
    if actionable_count > 0:
        return f"まずはこの上段 {actionable_count} 件を見れば十分です。参考情報は下の「参考」にまとめています。"
    if refresh_count > 0:
        return "今すぐ止まる要因は見当たりません。旧データ由来の項目だけ、必要に応じて再分析で詳細化してください。"
    return "今すぐ止まる要因は見当たりません。参考情報だけ確認すれば十分です。"

def _filter_actionable_google_controls(google_controls: Dict[str, Any]) -> list[dict]:
    actionable_rows: list[dict] = []
    if google_controls.get("noindex"):
        actionable_rows.append({"title": "検索結果への掲載除外（noindex）", "detail": "設定あり"})
    if google_controls.get("nosnippet"):
        actionable_rows.append({"title": "抜粋禁止（nosnippet）", "detail": "設定あり"})
    data_nosnippet_count = int(google_controls.get("data_nosnippet_count") or 0)
    if data_nosnippet_count > 0:
        actionable_rows.append(
            {"title": "部分的な抜粋除外（data-nosnippet）", "detail": f"{data_nosnippet_count}箇所で抜粋除外"}
        )
    return actionable_rows

def _status_sort_key(status: Any) -> int:
    order = {
        "fail": 0,
        "warn": 1,
        "pass": 2,
        "reference": 3,
        "info": 4,
    }
    return order.get(_normalize_status_key(status), 9)

def _render_status_note_card(
    item: Dict[str, Any],
    *,
    fallback_source_label: str = "",
    card_classes: str = "card p-4 w-full generated-block",
) -> None:
    status_key = _normalize_status_key(item.get("status"))
    status_text = str(item.get("status_label") or _status_label(status_key) or "参考").strip()
    source_text = str(item.get("source_label") or fallback_source_label or "").strip()
    title = str(item.get("title") or "").strip()
    detail = str(item.get("detail") or "").strip()
    summary_text = str(item.get("summary") or "").strip() or detail
    show_raw_detail = bool(detail and summary_text and detail != summary_text)

    with ui.card().classes(card_classes):
        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
            with ui.row().classes("items-center gap-2 flex-wrap"):
                ui.label(status_text).classes(
                    f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(status_key) }"
                )
                if source_text:
                    ui.label(source_text).classes("fixed-chip")
            label_text = str(item.get("label") or "").strip()
            if label_text and label_text not in {source_text, "参考"}:
                ui.label(_display_snapshot_label(label_text)).classes("generated-metric")
        if title:
            ui.label(title).classes("generated-title")
        if summary_text:
            ui.label(summary_text).classes("generated-body whitespace-pre-line")
        if show_raw_detail:
            raw_exp = ui.expansion("実データを見る", icon="insights", value=False).classes("w-full mt-2")
            with raw_exp:
                ui.label(detail).classes("card-hint text-xs whitespace-pre-line")

def _render_engineer_summary_card(
    item: Dict[str, Any],
    *,
    card_classes: str = "card p-4 min-w-[220px] flex-1",
) -> None:
    status_key = _normalize_status_key(item.get("status"))
    status_text = str(item.get("status_label") or _status_label(status_key) or "参考").strip()
    title = str(item.get("title") or "技術サマリー").strip()
    detail = str(item.get("detail") or "").strip()
    metric_text = ""
    if item.get("score") not in (None, ""):
        try:
            metric_text = f"{float(item.get('score')):.0f}点"
        except (TypeError, ValueError):
            metric_text = str(item.get("score"))
    elif item.get("quality_score") not in (None, "", 0):
        metric_text = f"{int(item.get('quality_score'))}点"

    metric_value = None
    try:
        if item.get("score") not in (None, ""):
            metric_value = float(item.get("score"))
        elif item.get("quality_score") not in (None, "", 0):
            metric_value = float(item.get("quality_score"))
    except (TypeError, ValueError):
        metric_value = None

    caution_note = ""
    if metric_value is not None and metric_value >= 80 and status_key in {"warn", "fail"}:
        if status_key == "fail":
            caution_note = "点数は高めですが、致命項目があるため要対応です。"
        else:
            caution_note = "点数は高めですが、注意項目が残っているため確認が必要です。"

    with ui.card().classes(card_classes):
        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
            ui.label(status_text).classes(
                f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(status_key) }"
            )
            if metric_text:
                ui.label(metric_text).classes("generated-metric")
        ui.label(title).classes("generated-title")
        if detail:
            ui.label(detail).classes("card-hint text-xs whitespace-pre-line")
        if caution_note:
            ui.label(caution_note).classes("card-hint text-xs text-orange-700 whitespace-pre-line")


def _render_maintenance_risk_block(maintenance_summary: Dict[str, Any]) -> None:
    cards = [
        item for item in (maintenance_summary.get("cards") or [])
        if isinstance(item, dict)
    ]
    if not cards:
        return
    ui.separator()
    with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
        ui.label("保守・更新管理").classes("card-sub font-bold")
        score = maintenance_summary.get("score")
        if score not in (None, ""):
            ui.label(f"保守更新スコア {score}点").classes("generated-chip")
    summary = str(maintenance_summary.get("summary") or "").strip()
    if summary:
        ui.label(summary).classes("card-hint text-xs")
    with ui.column().classes("w-full gap-3 mt-2"):
        for card in cards:
            status_key = _normalize_status_key(card.get("status"))
            with ui.column().classes("w-full border-l-4 border-amber-300 pl-3 py-2 gap-1"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.label(str(card.get("status_label") or _status_label(status_key))).classes(
                        f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(status_key) }"
                    )
                    ui.label(str(card.get("title") or "保守確認")).classes("card-sub font-bold")
                detail = str(card.get("summary") or card.get("detail") or "").strip()
                if detail:
                    ui.label(detail).classes("card-hint text-xs whitespace-pre-line")
                metrics = card.get("metrics") or {}
                metric_bits = []
                for label, key in (
                    ("フォーム数", "form_count"),
                    ("個人情報項目数", "personal_fields"),
                    ("CSRF/nonce痕跡", "csrf_or_nonce"),
                    ("privacy同意", "privacy_consent"),
                    ("captcha痕跡", "captcha"),
                    ("ファイルアップロード", "file_upload"),
                    ("機微情報の文脈", "sensitive_context"),
                    ("外部送信先", "external_action"),
                    ("確認した送信先", "checked_endpoints"),
                    ("問題のある送信先", "problem_endpoints"),
                ):
                    if key in metrics:
                        metric_bits.append(f"{label}: {metrics.get(key)}")
                if metric_bits:
                    ui.label(" / ".join(metric_bits)).classes("card-hint text-xs")
                for bullet in (card.get("bullets") or [])[:4]:
                    ui.label(f"・{bullet}").classes("card-hint text-xs")

def _accessibility_audience(action: Dict[str, Any]) -> Dict[str, Any]:
    audience = action.get("audience")
    if isinstance(audience, dict) and audience:
        return audience
    return {
        "action": "検出された箇所について、見えない環境でも内容や操作目的が伝わるか見直してください。",
        "impact": "検索・AI回答・読み上げにページ内容が伝わりやすくなります。",
        "review_area": "該当する画像・ボタン・入力欄・見出し",
        "handoff_to": "Web制作担当またはフロントエンド担当",
        "confirmation": "対象要素と実装確認は技術タブで確認してください。",
    }


def _accessibility_engineer(action: Dict[str, Any]) -> Dict[str, Any]:
    engineer = action.get("engineer")
    if isinstance(engineer, dict) and engineer:
        return engineer
    return {
        "target": action.get("target"),
        "target_element": action.get("target_element"),
        "task": action.get("action"),
        "verification": action.get("verification"),
        "detection_source": "保存済み自動検出",
        "raw_issue": action.get("reason"),
    }


_ACCESSIBILITY_GROUP_IDS = {
    "image_alt",
    "interactive_names",
    "form_labels",
    "h1",
    "heading_hierarchy",
    "landmarks",
    "html_lang",
    "title",
    "iframe_titles",
    "color_contrast",
    "zoom_scaling",
    "aria_semantics",
    "keyboard_focus",
    "screen_reader_structure",
}
_ACCESSIBILITY_TITLES = {
    "画像に内容が分かる説明文を入れる",
    "リンクやアイコンボタンに操作名を付ける",
    "入力欄に項目名を付ける",
    "ページの主題をh1で1つ示す",
    "見出しの順番を整理する",
    "ページの主要領域を分かるHTMLにする",
    "ページの言語を指定する",
    "ページ固有のtitleを入れる",
    "埋め込み枠に内容名を付ける",
    "文字色と背景色を読みやすくする",
    "スマホで拡大できる設定にする",
    "ARIAの役割と状態を正しく整理する",
    "キーボードで自然に操作できるようにする",
    "読み上げで伝わるページ構造にする",
}


def _int_value(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _is_accessibility_item(item: Dict[str, Any]) -> bool:
    return (
        str(item.get("category") or "").strip() == "アクセシビリティ"
        or str(item.get("group") or "").strip() in _ACCESSIBILITY_GROUP_IDS
        or str(item.get("title") or "").strip() in _ACCESSIBILITY_TITLES
    )


def _is_actual_accessibility_action(action: Dict[str, Any]) -> bool:
    if not isinstance(action, dict):
        return False
    if action.get("affected_count") not in (None, ""):
        return _int_value(action.get("affected_count")) > 0
    engineer = action.get("engineer")
    if isinstance(engineer, dict) and str(engineer.get("target_element") or "").strip():
        return True
    target_element = str(action.get("target_element") or "").strip()
    target = str(action.get("target") or "").strip()
    return bool(target_element and target_element != target)


def _build_accessibility_action_lookup(snapshot: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for workspace_key in ("technical_workspace", "implementation_workspace"):
        workspace = snapshot.get(workspace_key) or {}
        if not isinstance(workspace, dict):
            continue
        payload = workspace.get("accessibility_improvements") or {}
        if not isinstance(payload, dict):
            continue
        for action in payload.get("actions") or []:
            if not isinstance(action, dict) or not _is_actual_accessibility_action(action):
                continue
            for prefix, value in (
                ("group", action.get("group")),
                ("title", action.get("title")),
            ):
                text = str(value or "").strip()
                if text:
                    lookup.setdefault(f"{prefix}:{text}", action)
    return lookup


def _accessibility_detail_for_item(
    item: Dict[str, Any],
    lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    for prefix, value in (
        ("group", item.get("group")),
        ("title", item.get("title")),
    ):
        text = str(value or "").strip()
        if text and f"{prefix}:{text}" in lookup:
            return lookup[f"{prefix}:{text}"]
    return {}


def _task_action_display_text(item: Dict[str, Any], accessibility_detail: Dict[str, Any] | None = None) -> tuple[str, str]:
    if _is_accessibility_item(item):
        source = accessibility_detail if isinstance(accessibility_detail, dict) and accessibility_detail else item
        audience = _accessibility_audience(source)
        action = str(audience.get("action") or item.get("action") or "").strip()
        impact = str(audience.get("impact") or item.get("impact") or item.get("kpi") or "").strip()
        return (
            action or "見えない環境でも内容や操作目的が伝わるか、該当箇所をWeb制作担当へ確認してください。",
            f"影響: {impact}" if impact and not impact.startswith("影響:") else impact,
        )
    return (
        str(item.get("action") or item.get("detail") or "").strip(),
        str(item.get("impact") or item.get("kpi") or "").strip(),
    )


def _split_task_actions(actions: list[Dict[str, Any]], primary_count: int = 3) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
    if primary_count < 0:
        primary_count = 0
    return actions[:primary_count], actions[primary_count:]

def _prioritize_search_intent_secondary_actions(actions: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    if any(str(item.get("area") or "").strip() == "検索意図" for item in actions[:5]):
        return actions
    search_intent_actions = [
        item for item in actions
        if str(item.get("area") or "").strip() == "検索意図"
    ]
    if not search_intent_actions:
        return actions
    other_actions = [
        item for item in actions
        if str(item.get("area") or "").strip() != "検索意図"
    ]
    return search_intent_actions + other_actions

def _render_task_action_detail_lines(item: Dict[str, Any], accessibility_detail: Dict[str, Any] | None = None) -> None:
    rows: list[tuple[str, str]] = []
    if _is_accessibility_item(item) and accessibility_detail:
        # action/impact are already shown above via _task_action_display_text(),
        # which also reads from _accessibility_audience(). Only add the two
        # audience fields that aren't displayed elsewhere on this card yet.
        # Raw target_element/verification/detection_source stay out of this
        # non-engineer tab; the same accessibility_detail renders those via
        # _accessibility_engineer() in the エンジニア向け tab instead.
        audience = _accessibility_audience(accessibility_detail)
        for label, key in (
            ("見直し箇所", "review_area"),
            ("次に渡す相手", "handoff_to"),
        ):
            value = str(audience.get(key) or "").strip()
            if value:
                rows.append((label, value))
    else:
        for label, key in (
            ("対象", "target"),
            ("対象要素", "target_element"),
            ("確認方法", "verification"),
        ):
            value = str(item.get(key) or "").strip()
            if value:
                rows.append((label, value))

    if not rows:
        return
    with ui.column().classes("w-full border-l-4 border-amber-300 pl-3 py-2 mt-2 gap-1"):
        for label, value in rows[:4]:
            ui.label(f"{label}: {value}").classes("card-hint text-xs whitespace-pre-line break-all")


def _render_task_action_card(item: Dict[str, Any], accessibility_detail: Dict[str, Any] | None = None) -> None:
    with ui.card().classes("card p-4 w-full"):
        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
            with ui.row().classes("items-center gap-2 flex-wrap"):
                ui.label(str(item.get("priority") or "中")).classes(
                    f"text-xs px-2 py-1 rounded { _priority_badge_classes(str(item.get('priority') or '中')) }"
                )
                ui.label(str(item.get("owner") or "運用")).classes("generated-chip")
                if item.get("area"):
                    ui.label(str(item.get("area"))).classes("generated-metric")
            ui.label(str(item.get("effort") or "")).classes("card-hint text-xs")
        ui.label(str(item.get("title") or "改善提案")).classes("generated-title")
        action_text, impact_text = _task_action_display_text(item, accessibility_detail)
        if action_text:
            if len(action_text) <= 140:
                ui.label(action_text).classes("generated-body whitespace-pre-line")
            else:
                action_exp = ui.expansion("手順を見る", icon="unfold_more", value=False).classes("w-full mt-2")
                with action_exp:
                    ui.label(action_text).classes("generated-body whitespace-pre-line")
        _render_task_action_detail_lines(item, accessibility_detail)
        meta_parts = [impact_text] if impact_text else []
        if meta_parts:
            ui.label(" / ".join(str(part) for part in meta_parts)).classes("card-hint text-xs")

def _short_reason_text(value: Any, limit: int = 72) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    shortened = text[:limit]
    for delimiter in ("。", "、", ".", " "):
        cut = shortened.rfind(delimiter)
        if cut >= int(limit * 0.55):
            return shortened[: cut + (1 if delimiter != " " else 0)].strip()
    return shortened.rstrip() + "…"

def _intent_confidence_label(intent_role_map: Dict[str, Any]) -> str:
    label = str(intent_role_map.get("confidence_label") or "").strip()
    if label:
        return label
    return {
        "high": "判定根拠: 高",
        "medium": "判定根拠: 中",
        "low": "判定根拠: 低",
    }.get(str(intent_role_map.get("confidence") or "").strip(), "判定根拠: 低")

def _intent_note_values(notes: Dict[str, Any], key: str) -> list[str]:
    if key == "fix_locations":
        value = notes.get("fix_locations")
        if not value and notes.get("fix_location"):
            value = notes.get("fix_location")
    else:
        value = notes.get(key)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    text = str(value or "").strip()
    return [text] if text else []

def _intent_role_overview_items(intent_role_map: Dict[str, Any]) -> list[Dict[str, str]]:
    if not intent_role_map:
        return []
    raw_items = [
        item for item in (intent_role_map.get("overview_items") or [])
        if isinstance(item, dict)
    ]
    by_label = {
        str(item.get("label") or "").strip(): item
        for item in raw_items
        if str(item.get("label") or "").strip()
    }
    fallback_missing = intent_role_map.get("missing_content") or []
    labels = (
        ("このページの役割", intent_role_map.get("page_role") or ""),
        ("不足", " / ".join(str(item) for item in fallback_missing[:4])),
        ("次にやること", intent_role_map.get("recommended_action") or ""),
    )
    items: list[Dict[str, str]] = []
    for label, fallback_detail in labels:
        source = by_label.get(label) or {}
        title = str(source.get("title") or "").strip()
        detail = str(source.get("detail") or fallback_detail or "").strip()
        if title or detail:
            items.append({"label": label, "title": title, "detail": detail})
    return items[:3]

def _render_saved_run_intent_role_overview(intent_role_map: Dict[str, Any]) -> None:
    overview_items = _intent_role_overview_items(intent_role_map)
    if not overview_items:
        return

    ui.separator()
    ui.label("ページの役割確認").classes("card-sub font-bold")
    with ui.row().classes("w-full gap-3 flex-wrap mt-2"):
        for item in overview_items:
            with ui.card().classes("card p-4 generated-block flex-1 min-w-[220px]"):
                ui.label(item["label"]).classes("card-hint text-xs")
                if item["title"]:
                    ui.label(item["title"]).classes("generated-title")
                if item["detail"]:
                    ui.label(item["detail"]).classes("card-sub whitespace-pre-line")

def _render_workspace_summary_tab(snapshot: Dict[str, Any], *, show_header: bool = True) -> None:
    header = snapshot.get("header") or {}
    summary_workspace = snapshot.get("summary_workspace") or {}
    raw_headline_metrics = summary_workspace.get("headline_metrics") or []
    headline_metrics = [
        metric
        for metric in raw_headline_metrics
        if str(metric.get("label") or "").strip() not in {"法務", "法務・表示", "表示アドバイス"}
    ]
    summary_lines = summary_workspace.get("summary_lines") or []
    raw_priority_counts = summary_workspace.get("priority_counts") or []
    priority_counts = []
    for item in raw_priority_counts:
        normalized = dict(item)
        if str(normalized.get("label") or "").strip() == "法務・表示":
            normalized["label"] = "表示アドバイス"
        priority_counts.append(normalized)
    top_actions = summary_workspace.get("top_actions") or (header.get("top_actions") or [])[:3]
    intent_role_map = summary_workspace.get("intent_role_map") or {}
    raw_blocking_issues = summary_workspace.get("blocking_issues") or []
    blocking_issues = []
    for item in raw_blocking_issues:
        normalized = dict(item)
        if str(normalized.get("label") or "").strip() == "法務・表示":
            normalized["label"] = "表示アドバイス"
        blocking_issues.append(normalized)
    previous_diff = summary_workspace.get("previous_diff") or (header.get("previous_diff") or {})
    summary_note = _build_summary_priority_note(summary_workspace)

    with ui.card().classes("card workspace-panel p-5 w-full"):
        if show_header:
            _render_workspace_header(
                title="サマリー",
                description="結論と最優先事項だけを先に確認できます。",
            )

        with ui.card().classes("card p-4 w-full mt-3"):
            ui.label(str(summary_note.get("title") or "結論")).classes("card-sub font-bold")
            ui.label(str(summary_note.get("detail") or "")).classes("card-sub")
            if summary_lines or previous_diff:
                with ui.row().classes("w-full gap-2 flex-wrap mt-2"):
                    for line in summary_lines[:3]:
                        ui.label(str(line)).classes("fixed-chip")
                    if previous_diff:
                        diff_label = str(previous_diff.get("label", "前回なし"))
                        ui.label(f"前回比 {diff_label}").classes(
                            f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(str(summary_note.get('status') or 'info')) }"
                        )

        if priority_counts:
            with ui.row().classes("w-full gap-2 flex-wrap mt-4"):
                for item in priority_counts:
                    status = str(item.get("status") or "info")
                    with ui.card().classes("card p-3 min-w-[160px]"):
                        ui.label(str(item.get("label") or "-")).classes("card-hint text-xs")
                        ui.label(str(item.get("count") or 0)).classes("text-2xl font-bold")
                        ui.label(str(item.get("detail") or "")).classes(f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(status) }")

        _render_workspace_improvement_map(summary_workspace, header)

        if top_actions:
            ui.separator()
            ui.label("最優先3件").classes("card-sub font-bold")
            with ui.row().classes("w-full gap-3 flex-wrap"):
                for item in top_actions[:3]:
                    _render_expandable_generated_card(
                        title=str(item.get("title") or "改善提案"),
                        body=str(item.get("action") or item.get("detail") or ""),
                        metric=str(item.get("area") or "改善"),
                        card_classes="card p-4 generated-block flex-1 min-w-[220px] action-preview-card",
                        body_expand_label="クリックで全文表示",
                    )

        if intent_role_map:
            ui.separator()
            with ui.row().classes("items-center gap-2 flex-wrap"):
                ui.label("ページの役割確認").classes("card-sub font-bold")
                ui.label(_intent_confidence_label(intent_role_map)).classes(
                    f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(str(intent_role_map.get('status') or 'info')) }"
                )
            ui.label(str(intent_role_map.get("non_engineer_summary") or "")).classes("card-hint text-xs")
            overview_items = intent_role_map.get("overview_items") or []
            with ui.row().classes("w-full gap-3 flex-wrap mt-2"):
                for item in overview_items[:3]:
                    with ui.card().classes("card p-4 generated-block flex-1 min-w-[220px]"):
                        ui.label(str(item.get("label") or "")).classes("card-hint text-xs")
                        ui.label(str(item.get("title") or "")).classes("generated-title")
                        ui.label(str(item.get("detail") or "")).classes("card-sub whitespace-pre-line")
            evidence_terms = intent_role_map.get("evidence_terms") or []
            if evidence_terms:
                with ui.expansion("判定の手がかりを見る", icon="analytics", value=False).classes("w-full mt-2"):
                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        for term in evidence_terms[:10]:
                            ui.label(str(term)).classes("generated-chip")

        if headline_metrics:
            ui.separator()
            ui.label("判断の目安").classes("card-sub font-bold")
            with ui.row().classes("w-full gap-3 flex-wrap mt-2"):
                for metric in headline_metrics[:4]:
                    with ui.card().classes("card p-4 min-w-[140px] flex-1"):
                        label = str(metric.get("label") or "-")
                        ui.label(label).classes("card-hint text-xs")
                        ui.label(str(metric.get("value") or "-")).classes("text-2xl font-bold")
                        hint = _headline_metric_hint(label)
                        if hint:
                            ui.label(hint).classes("card-hint text-xs whitespace-pre-line")

        if blocking_issues:
            ui.separator()
            ui.label("要確認").classes("card-sub font-bold")
            _render_snapshot_cards(
                [
                    {
                        "title": item.get("title"),
                        "detail": item.get("detail"),
                        "label": item.get("label"),
                    }
                    for item in blocking_issues[:8]
                ],
                empty_text="",
                detail_limit=160,
            )

def _render_workspace_task_tab(snapshot: Dict[str, Any], *, show_header: bool = True) -> None:
    task_workspace = snapshot.get("task_workspace") or {}
    actions = task_workspace.get("actions") or []
    owner_counts = task_workspace.get("owner_counts") or {}
    primary_actions, secondary_actions = _split_task_actions(actions)
    accessibility_lookup = _build_accessibility_action_lookup(snapshot)

    with ui.card().classes("card workspace-panel p-5 w-full"):
        if show_header:
            _render_workspace_header(
                title="やること",
                description="担当と優先度で、そのまま実務に渡せる形にまとめています。",
            )
        if owner_counts:
            with ui.row().classes("w-full gap-2 flex-wrap mt-3"):
                for owner, count in owner_counts.items():
                    ui.label(f"{owner} {count}件").classes("fixed-chip")

        if not actions:
            ui.label("実務タスクはまだ抽出されていません。").classes("card-sub text-gray-500 mt-3")
            return

        if primary_actions:
            ui.label("先に着手する3件").classes("card-sub font-bold mt-3")
            for item in primary_actions:
                _render_task_action_card(item, _accessibility_detail_for_item(item, accessibility_lookup))

        if secondary_actions:
            remaining_exp = ui.expansion(f"続きのタスクを見る ({len(secondary_actions)}件)", icon="unfold_more", value=False).classes("w-full mt-3")
            with remaining_exp:
                for item in secondary_actions[:5]:
                    _render_task_action_card(item, _accessibility_detail_for_item(item, accessibility_lookup))

_FAQ_TOPIC_LABELS = {
    "audience_value": "読者への価値",
    "fit": "向き不向き",
    "pricing": "料金",
    "process": "利用の流れ",
    "comparison": "比較検討",
    "trust": "運営・信頼性",
    "case": "導入事例",
    "support": "問い合わせ",
    "security": "セキュリティ",
    "access": "アクセス",
    "hours": "営業時間",
    "reservation": "予約",
    "public_services": "支援・サービス内容",
    "public_eligibility": "対象・利用条件",
    "public_application": "申込手続き",
    "delivery": "配送",
    "returns": "返品",
    "payment": "支払い",
    "cancel": "キャンセル",
    "contact": "問い合わせ",
    "general": "一般",
}

def _faq_topic_display(topic: str) -> str:
    return _FAQ_TOPIC_LABELS.get(str(topic or "").strip(), str(topic or "").strip() or "一般")

def _render_workspace_writing_tab(snapshot: Dict[str, Any], *, show_header: bool = True) -> None:
    writing_workspace = snapshot.get("writing_workspace") or {}
    title_rewrites = writing_workspace.get("title_rewrites") or []
    description_rewrites = writing_workspace.get("description_rewrites") or []
    body_rewrites = writing_workspace.get("body_rewrites") or []
    citation_phrases = writing_workspace.get("citation_phrases") or []
    faq_summary = writing_workspace.get("faq_detection_summary") or {}
    faq_items = faq_summary.get("items") or []
    faq_suggestions = writing_workspace.get("faq_suggestions") or []
    faq_debug = writing_workspace.get("faq_debug") or {}
    content_plan = writing_workspace.get("content_plan") or {}
    sections = content_plan.get("sections") or []

    with ui.card().classes("card workspace-panel p-5 w-full"):
        if show_header:
            _render_workspace_header(
                title="文章改善",
                description="本文・タイトル・FAQ内容など、書き換える内容だけを集約しています。",
            )

        rewrite_groups = [
            ("タイトル改善案", title_rewrites),
            ("説明文改善案", description_rewrites),
        ]
        for title, rows in rewrite_groups:
            if not rows:
                continue
            ui.separator()
            ui.label(title).classes("card-sub font-bold")
            for row in rows[:3]:
                current = str(row.get("current") or "").strip()
                proposed = str(row.get("proposed") or "").strip()
                before_html, after_html = _diff_html(current, proposed)
                with ui.card().classes("card p-4 w-full"):
                    if current:
                        ui.html(f"<div class='diff-block'><span class='diff-label'>現在</span> {before_html}</div>", sanitize=False).classes("card-sub diff-wrap")
                    if proposed:
                        ui.html(f"<div class='diff-block'><span class='diff-label'>提案</span> {after_html}</div>", sanitize=False).classes("card-sub diff-wrap")

        if body_rewrites:
            ui.separator()
            ui.label("本文リライト").classes("card-sub font-bold")
            for item in body_rewrites[:3]:
                before = str(item.get("original_segment") or "").strip()
                after = str(item.get("improved_segment") or "").strip()
                reason = str(item.get("reason") or "").strip()
                before_html, after_html = _diff_html(before, after)
                with ui.card().classes("card p-4 w-full"):
                    ui.html(f"<div class='diff-block'><span class='diff-label'>変更前</span> {before_html}</div>", sanitize=False).classes("card-sub diff-wrap")
                    ui.html(f"<div class='diff-block'><span class='diff-label'>変更後</span> {after_html}</div>", sanitize=False).classes("card-sub diff-wrap")
                    if reason:
                        ui.label(reason).classes("card-hint whitespace-pre-line")

        if citation_phrases:
            ui.separator()
            ui.label("AI引用されやすい文章構造").classes("card-sub font-bold")
            for item in citation_phrases[:4]:
                phrase = str(item.get("phrase") or "引用候補").strip()
                proposal = str(item.get("template_non_engineer") or item.get("template") or "").strip()
                reason = str(item.get("reason") or "").strip()
                exp = ui.expansion(phrase if len(phrase) <= 48 else f"{phrase[:48]}...", icon="edit", value=False).classes("w-full")
                with exp:
                    if proposal:
                        ui.label(proposal).classes("card-sub whitespace-pre-line")
                    if reason:
                        ui.label(reason).classes("card-hint whitespace-pre-line")

        ui.separator()
        if faq_items:
            ui.label("既存FAQ検出").classes("card-sub font-bold")
            ui.label(f"{len(faq_items)}件のFAQ内容を確認できます。").classes("card-hint text-xs")
            for item in faq_items[:5]:
                exp = ui.expansion(str(item.get("question") or "FAQ"), icon="help", value=False).classes("w-full")
                with exp:
                    ui.label(str(item.get("answer") or "")).classes("card-sub whitespace-pre-line")
                    if item.get("source"):
                        ui.label(f"検出元: {item.get('source')}").classes("card-hint text-xs")
        else:
            ui.label("FAQ提案").classes("card-sub font-bold")
            ui.label("質問、回答骨子、設置先を確認できます。本文条件と合うものだけ採用してください。").classes("card-hint text-xs")
            if faq_suggestions:
                for item in faq_suggestions[:5]:
                    with ui.card().classes("card p-4 w-full"):
                        ui.label(str(item.get("question") or "FAQ候補")).classes("generated-title")
                        # source_label ("issue ベース" 等) and evidence_terms/confidence
                        # are internal detection-classification metadata, not something
                        # a content writer acts on. Kept out of this card; the full
                        # item dict (including those fields) still reaches faq_debug's
                        # expansion below for anyone who wants the reasoning trail.
                        with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
                            if item.get("presentation_mode") == "contextualized":
                                ui.label("URL文脈で調整").classes("generated-chip")
                            short_reason = _short_reason_text(item.get("reason"))
                            if short_reason:
                                ui.label(f"理由: {short_reason}").classes("card-hint text-xs")
                        answer_outline = str(item.get("answer_outline") or item.get("answer") or "").strip()
                        if answer_outline:
                            ui.label("回答骨子").classes("card-hint text-xs font-bold mt-2")
                            ui.label(answer_outline).classes("card-sub whitespace-pre-line")
                        if item.get("recommended_section"):
                            ui.label(f"設置先: {item.get('recommended_section')}").classes("card-hint text-xs mt-2")
                        if item.get("risk_if_wrong"):
                            ui.label(f"注意: {item.get('risk_if_wrong')}").classes("card-hint text-xs mt-2")
                        if item.get("persona_label"):
                            ui.label(f"対象読者: {item.get('persona_label')}").classes("card-hint text-xs mt-1")
                if faq_debug:
                    debug_persona = faq_debug.get("persona") or {}
                    debug_context = faq_debug.get("context") or {}
                    debug_candidates = faq_debug.get("candidates") or []
                    debug_exp = ui.expansion("提案理由の見立てを見る", icon="analytics", value=False).classes("w-full mt-2")
                    with debug_exp:
                        if debug_persona.get("label"):
                            ui.label(f"想定読者: {debug_persona.get('label')}").classes("card-sub")
                        if debug_persona.get("confidence") or debug_persona.get("source"):
                            meta_bits = []
                            if debug_persona.get("confidence"):
                                meta_bits.append(f"信頼度: {debug_persona.get('confidence')}")
                            if debug_persona.get("source"):
                                meta_bits.append(f"主根拠: {_intent_signal_source_label(debug_persona.get('source'))}")
                            ui.label(" / ".join(meta_bits)).classes("card-hint text-xs")
                        context_rows = []
                        if debug_context.get("business_goal"):
                            context_rows.append(f"目的: {debug_context.get('business_goal')}")
                        if debug_context.get("page_focus"):
                            context_rows.append(f"ページ要点: {debug_context.get('page_focus')}")
                        audience_clues = debug_context.get("audience_clues") or []
                        if audience_clues:
                            context_rows.append(f"読者手がかり: {', '.join(str(item) for item in audience_clues[:3])}")
                        summary_improvements = debug_context.get("summary_improvements") or []
                        if summary_improvements:
                            context_rows.append(f"改善論点: {', '.join(str(item) for item in summary_improvements[:3])}")
                        page_service_terms = debug_context.get("page_service_terms") or []
                        transaction_terms = debug_context.get("transaction_terms") or []
                        if page_service_terms:
                            context_rows.append(f"業務語: {', '.join(str(item) for item in page_service_terms[:4])}")
                        if transaction_terms:
                            context_rows.append(f"取引語: {', '.join(str(item) for item in transaction_terms[:4])}")
                        for row in context_rows[:4]:
                            ui.label(row).classes("card-hint text-xs")
                        selected_debug_rows = [item for item in debug_candidates if item.get("selected")]
                        if selected_debug_rows:
                            ui.separator()
                            ui.label("採用したFAQ候補").classes("card-sub font-bold")
                            for row in selected_debug_rows[:5]:
                                topic = _faq_topic_display(row.get("topic"))
                                question = str(row.get("base_question") or "").strip()
                                keywords = row.get("matched_keywords") or []
                                detail_parts = [f"分類: {topic}"]
                                if row.get("source_label"):
                                    detail_parts.append(str(row.get("source_label")))
                                if keywords:
                                    detail_parts.append(f"一致語: {', '.join(str(item) for item in keywords[:4])}")
                                ui.label(question or "FAQ候補").classes("card-sub")
                                ui.label(" / ".join(detail_parts)).classes("card-hint text-xs")
                        persona_candidates = debug_persona.get("candidates") or []
                        if persona_candidates:
                            ui.separator()
                            ui.label("ペルソナ候補").classes("card-sub font-bold")
                            for row in persona_candidates[:3]:
                                label = str(row.get("label") or "候補").strip()
                                signals = row.get("signals") or []
                                ui.label(label).classes("card-sub")
                                if signals:
                                    ui.label(", ".join(str(item) for item in signals[:4])).classes("card-hint text-xs")
            else:
                ui.label("FAQ候補はまだ抽出されていません。").classes("card-sub text-gray-500")

        if sections:
            ui.separator()
            ui.label("追加コンテンツ提案").classes("card-sub font-bold")
            for section in sections[:3]:
                _render_expandable_generated_card(
                    title=str(section.get("title") or "新規セクション"),
                    body=str(section.get("purpose") or ""),
                    metric=str(section.get("format") or "提案"),
                    body_expand_label="詳細を見る",
                )

def _render_workspace_implementation_tab(snapshot: Dict[str, Any], *, show_header: bool = True) -> None:
    implementation_workspace = snapshot.get("implementation_workspace") or {}
    technical_workspace = snapshot.get("technical_workspace") or {}
    provider_matrix = implementation_workspace.get("provider_matrix") or []
    provider_payload = implementation_workspace.get("provider_payload") or {}
    google_controls = implementation_workspace.get("google_controls") or {}
    schema_summary = implementation_workspace.get("schema_summary") or {}
    link_health_summary = implementation_workspace.get("link_health_summary") or {}
    link_opportunities = link_health_summary.get("link_opportunities") or []
    intent_role_map = implementation_workspace.get("intent_role_map") or technical_workspace.get("intent_role_map") or {}
    llms_notes = implementation_workspace.get("llms_notes") or []
    seo_audit_notes = implementation_workspace.get("seo_audit_notes") or []
    reference_notes = implementation_workspace.get("reference_notes") or []
    informational_notes = [
        item for item in (implementation_workspace.get("informational_notes") or [])
        if str(item.get("label") or "") != "llms.txt"
    ]
    platform_guidance = implementation_workspace.get("platform_guidance") or {}
    legal_notes = implementation_workspace.get("legal_display_notes") or []
    technical_actions = implementation_workspace.get("technical_actions") or []
    accessibility_improvements = implementation_workspace.get("accessibility_improvements") or {}
    maintenance_summary = implementation_workspace.get("maintenance_risk") or technical_workspace.get("maintenance_risk") or {}
    accessibility_actions = [
        action for action in (accessibility_improvements.get("actions") or [])
        if _is_actual_accessibility_action(action)
    ]
    provider_focus = _build_provider_focus_summary(provider_matrix)
    actionable_provider_rows = [
        row for row in provider_matrix
        if str(row.get("status") or "").strip() in {"注意", "要対応"}
    ]
    actionable_google_controls = _filter_actionable_google_controls(google_controls)
    actionable_provider_payloads = []
    reference_provider_payloads = []
    for key, label in (
        ("google", "Google"),
        ("openai_search", "OpenAI Search"),
        ("perplexity", "Perplexity"),
        ("claude_search", "Claude Search"),
    ):
        payload = provider_payload.get(key) or {}
        if not payload:
            continue
        status_key = _normalize_status_key(payload.get("status"))
        if status_key == "pass" and not _provider_has_actionable_details(payload):
            continue
        row = (label, payload, status_key)
        if status_key in {"fail", "warn"}:
            actionable_provider_payloads.append(row)
        else:
            reference_provider_payloads.append(row)

    refresh_notes = [
        item for item in seo_audit_notes
        if str(item.get("group") or "").strip() == "refresh"
        or str(item.get("source") or "").strip() == "legacy_fallback"
    ]
    actionable_seo_audits = sorted(
        [
            item for item in seo_audit_notes
            if item not in refresh_notes and _normalize_status_key(item.get("status")) in {"fail", "warn"}
        ],
        key=lambda item: (_status_sort_key(item.get("status")), str(item.get("title") or "")),
    )
    reference_seo_audits = sorted(
        [
            item for item in seo_audit_notes
            if item not in refresh_notes and _normalize_status_key(item.get("status")) not in {"fail", "warn"}
        ],
        key=lambda item: (_status_sort_key(item.get("status")), str(item.get("title") or "")),
    )
    technical_summary_cards = [
        item for item in (technical_workspace.get("summary_cards") or [])
        if isinstance(item, dict) and str(item.get("detail") or "").strip()
    ][:3]

    with ui.card().classes("card workspace-panel p-5 w-full"):
        if show_header:
            _render_workspace_header(
                title="実装・設定",
                description="今やること、旧データの再分析対象、参考情報を分けて確認できます。",
            )

        if technical_summary_cards:
            ui.label("重要な技術サマリー").classes("card-sub font-bold mt-3")
            with ui.row().classes("w-full gap-3 flex-wrap mt-2"):
                for item in technical_summary_cards:
                    _render_engineer_summary_card(item)

        if maintenance_summary:
            _render_maintenance_risk_block(maintenance_summary)

        ui.label("要対応 / 注意").classes("card-sub font-bold mt-3")
        with ui.card().classes("card implementation-note-card p-4 w-full mt-2"):
            if provider_matrix:
                ui.label("公開条件の要点").classes("card-sub font-bold")
                ui.label(
                    f"要対応 {provider_focus['fail']}件 / 注意 {provider_focus['warn']}件 / 通過 {provider_focus['pass']}件"
                ).classes("card-sub")
            actionable_count = (
                len(actionable_provider_rows)
                + len(actionable_provider_payloads)
                + len(actionable_google_controls)
                + len(actionable_seo_audits)
                + len(technical_actions)
                + len(accessibility_actions)
                + len(legal_notes)
                + len(link_opportunities[:2])
                + (1 if intent_role_map else 0)
            )
            ui.label("ここまで見れば十分").classes("card-sub font-bold mt-2")
            ui.label(
                _build_implementation_stop_message(
                    actionable_count=actionable_count,
                    refresh_count=len(refresh_notes),
                )
            ).classes("card-hint text-sm")
            if actionable_provider_rows:
                with ui.row().classes("w-full gap-3 flex-wrap mt-2"):
                    for row in actionable_provider_rows:
                        status_text = str(row.get("status") or "未判定")
                        with ui.card().classes("card p-4 min-w-[180px] flex-1"):
                            ui.label(str(row.get("label") or "-")).classes("card-hint text-xs")
                            ui.label(status_text).classes(
                                f"text-xl font-bold px-2 py-1 rounded inline-flex { _status_badge_classes(status_text) }"
                            )
                            if row.get("summary"):
                                ui.label(str(row.get("summary"))).classes("card-hint text-xs")
            if actionable_provider_payloads:
                for label, payload, status_key in actionable_provider_payloads:
                    exp = ui.expansion(
                        f"{label}: {payload.get('status_label') or _status_label(status_key)}",
                        icon="shield",
                        value=True,
                    ).classes("w-full mt-3")
                    with exp:
                        if payload.get("summary"):
                            ui.label(str(payload.get("summary"))).classes("card-sub")
                        checks = payload.get("official_checks") or []
                        visible_checks = [
                            check for check in checks
                            if _normalize_status_key(check.get("status")) in {"warn", "fail"}
                        ]
                        if checks:
                            ui.label("公開条件").classes("card-sub font-bold mt-2")
                            for check in visible_checks or checks[:1]:
                                check_label = _provider_check_status_label(check.get("status"))
                                ui.label(f"{check.get('label')}: {check_label}").classes("card-hint text-xs")
                        heuristics = payload.get("heuristic_notes") or []
                        if heuristics:
                            ui.label("内部ヒューリスティック").classes("card-sub font-bold mt-2")
                            for note in heuristics[:4]:
                                ui.label(f"・{note}").classes("card-hint text-xs")
            if actionable_google_controls:
                ui.label("Google 制御").classes("card-sub font-bold mt-3")
                _render_snapshot_cards(actionable_google_controls, empty_text="", show_label=False)
            if actionable_seo_audits:
                ui.label("SEO / AI Search 追加監査").classes("card-sub font-bold mt-3")
                for item in actionable_seo_audits:
                    _render_status_note_card(item)
            if accessibility_actions:
                ui.label(str(accessibility_improvements.get("title") or "見やすさ・使いやすさ改善")).classes("card-sub font-bold mt-3")
                with ui.card().classes("card p-4 w-full mt-2"):
                    ui.label(
                        f"改善スコア: {accessibility_improvements.get('score', 0)}点 / "
                        f"{accessibility_improvements.get('summary', '検索エンジン・AI・支援技術が読み取りやすいHTML構造として扱います。')}"
                    ).classes("card-sub")
                    ui.label("対象要素、実装作業、確認方法は技術タブへ分けています。ここでは影響と依頼先だけを確認します。").classes("card-hint text-xs")
                    for action in accessibility_actions[:5]:
                        audience = _accessibility_audience(action)
                        with ui.column().classes("w-full border-l-4 border-amber-300 pl-3 py-2 mt-2 gap-1"):
                            ui.label(str(action.get("title") or "改善アクション")).classes("card-sub font-bold")
                            ui.label(str(audience.get("action") or action.get("action") or "")).classes("card-sub")
                            if audience.get("impact"):
                                ui.label(f"影響: {audience.get('impact')}").classes("card-hint text-xs")
                            if audience.get("review_area"):
                                ui.label(f"見直し箇所: {audience.get('review_area')}").classes("card-hint text-xs")
                            if audience.get("handoff_to"):
                                ui.label(f"次に渡す相手: {audience.get('handoff_to')}").classes("card-hint text-xs")
            if intent_role_map:
                ui.label("ページ役割の作業要約").classes("card-sub font-bold mt-3")
                with ui.card().classes("card p-4 w-full mt-2"):
                    ui.label(str(intent_role_map.get("page_role") or "ページ役割")).classes("generated-title")
                    missing = intent_role_map.get("missing_content") or []
                    if missing:
                        ui.label("不足: " + " / ".join(str(item) for item in missing[:4])).classes("card-hint text-xs")
                    if intent_role_map.get("recommended_action"):
                        ui.label("次にやること: " + str(intent_role_map.get("recommended_action"))).classes("card-hint text-xs whitespace-pre-line")
                    notes = intent_role_map.get("engineer_notes") or {}
                    fix_locations = _intent_note_values(notes, "fix_locations")
                    if fix_locations:
                        ui.label("実装場所: " + " / ".join(fix_locations[:5])).classes("card-hint text-xs")
            if link_opportunities:
                ui.label("内部リンク追加候補").classes("card-sub font-bold mt-3")
                ui.label("上位だけ表示しています。詳しい確認条件はエンジニア向けにあります。").classes("card-hint text-xs")
                for item in link_opportunities[:2]:
                    with ui.column().classes("w-full border-l-4 border-amber-300 pl-3 py-2 mt-2 gap-1"):
                        target_url = str(item.get("target_url") or "").strip()
                        source_url = str(item.get("source_url") or "").strip()
                        anchor = str(item.get("recommended_anchor") or "").strip()
                        ui.label(str(item.get("title") or "内部リンクを追加")).classes("card-sub font-bold")
                        if source_url and target_url:
                            ui.label(f"リンク元: {source_url}").classes("card-hint text-xs break-all")
                            ui.label(f"リンク先: {target_url}").classes("card-hint text-xs break-all")
                        elif target_url:
                            ui.label(f"リンク先: {target_url}").classes("card-hint text-xs break-all")
                        if anchor:
                            ui.label(f"推奨アンカー: {anchor}").classes("card-hint text-xs")
            if technical_actions:
                ui.label("技術アクション").classes("card-sub font-bold mt-3")
                _render_snapshot_cards(technical_actions[:3], empty_text="", show_label=False, detail_limit=180)
                if len(technical_actions) > 3:
                    technical_exp = ui.expansion(
                        f"続きの技術アクションを見る ({len(technical_actions) - 3}件)",
                        icon="code",
                        value=False,
                    ).classes("w-full mt-2")
                    with technical_exp:
                        _render_snapshot_cards(technical_actions[3:], empty_text="", show_label=False, detail_limit=180)
            if legal_notes:
                ui.label("表示アドバイスメモ").classes("card-sub font-bold mt-3")
                _render_snapshot_cards(
                    [
                        {
                            "title": item.get("title"),
                            "detail": item.get("detail"),
                            "label": "このページ向け",
                        }
                        for item in legal_notes
                    ],
                    empty_text="",
                    detail_limit=180,
                )

        if refresh_notes:
            ui.separator()
            ui.label("再分析で詳細化").classes("card-sub font-bold")
            with ui.card().classes("card p-4 w-full mt-2"):
                ui.label("旧データ由来のため、追加監査は再分析後に実データへ置き換わります。").classes("card-hint")
                for item in refresh_notes:
                    _render_status_note_card(item, card_classes="card p-4 w-full mt-2")

        reference_section_visible = bool(
            schema_summary
            or reference_seo_audits
            or reference_provider_payloads
            or llms_notes
            or informational_notes
            or platform_guidance
            or reference_notes
            or (google_controls and not actionable_google_controls)
        )
        if reference_section_visible:
            ui.separator()
            ui.label("参考（後で見る）").classes("card-sub font-bold")
        if schema_summary or reference_seo_audits or reference_provider_payloads or (google_controls and not actionable_google_controls):
            with ui.card().classes("card reference-note-card p-4 w-full mt-2"):
                if schema_summary:
                    schema_exp = ui.expansion(
                        "構造化データの詳細を見る（開発者向け）", icon="code", value=False
                    ).classes("w-full")
                    with schema_exp:
                        _render_compact_note_rows(
                            [{"detail": line} for line in (schema_summary.get("summary_lines") or [])],
                            empty_text="構造化データ情報はありません。",
                        )
                        validation = schema_summary.get("validation") or {}
                        suspicious_items = validation.get("suspicious_items") or []
                        if suspicious_items:
                            warn_exp = ui.expansion("整合チェックの注意", icon="warning", value=False).classes("w-full mt-2")
                            with warn_exp:
                                for item in suspicious_items[:4]:
                                    ui.label(str(item.get("question") or item.get("reason") or "")).classes("card-sub")
                                    if item.get("reason"):
                                        ui.label(str(item.get("reason"))).classes("card-hint text-xs")
                if reference_seo_audits:
                    ui.label("SEO / AI Search 追加監査").classes("card-sub font-bold mt-3")
                    for item in reference_seo_audits:
                        _render_status_note_card(item, card_classes="card p-4 w-full mt-2")
                if reference_provider_payloads:
                    provider_exp = ui.expansion("公開条件の詳細を見る", icon="shield", value=False).classes("w-full mt-3")
                    with provider_exp:
                        for label, payload, status_key in reference_provider_payloads:
                            inner = ui.expansion(
                                f"{label}: {payload.get('status_label') or _status_label(status_key)}",
                                icon="check_circle",
                                value=False,
                            ).classes("w-full mt-2")
                            with inner:
                                if payload.get("summary"):
                                    ui.label(str(payload.get("summary"))).classes("card-sub")
                                checks = payload.get("official_checks") or []
                                if checks:
                                    ui.label("公開条件").classes("card-sub font-bold mt-2")
                                    for check in checks[:2]:
                                        check_label = _provider_check_status_label(check.get("status"))
                                        ui.label(f"{check.get('label')}: {check_label}").classes("card-hint text-xs")
                                heuristics = payload.get("heuristic_notes") or []
                                if heuristics:
                                    ui.label("内部ヒューリスティック").classes("card-sub font-bold mt-2")
                                    for note in heuristics[:2]:
                                        ui.label(f"・{note}").classes("card-hint text-xs")
                if google_controls and not actionable_google_controls:
                    google_exp = ui.expansion("Google 制御の現状", icon="tune", value=False).classes("w-full mt-3")
                    with google_exp:
                        _render_snapshot_cards(_describe_google_controls(google_controls), empty_text="", show_label=False)

        if llms_notes:
            llms_exp = ui.expansion("llms.txt（任意）", icon="description", value=False).classes("w-full")
            with llms_exp:
                _render_snapshot_cards(llms_notes, empty_text="", show_label=False, detail_limit=180)

        if informational_notes:
            info_exp = ui.expansion("参考メモ", icon="info", value=False).classes("w-full")
            with info_exp:
                _render_snapshot_cards(
                    [
                        {
                            "title": item.get("label"),
                            "detail": item.get("message"),
                            "label": "参考",
                        }
                        for item in informational_notes[:5]
                    ],
                    empty_text="",
                    detail_limit=180,
                )

        technical_steps = platform_guidance.get("technical_steps") or []
        business_steps = platform_guidance.get("business_steps") or []
        help_links = platform_guidance.get("help_links") or []
        if platform_guidance or reference_notes:
            cms_exp = ui.expansion("CMS別手順", icon="build", value=False).classes("w-full")
            with cms_exp:
                if platform_guidance.get("label"):
                    ui.label(str(platform_guidance.get("label"))).classes("card-hint text-xs")
                for step in technical_steps[:4]:
                    ui.label(f"・{step}").classes("card-sub")
                for step in business_steps[:2]:
                    ui.label(f"・{step}").classes("card-hint")
                for link in help_links[:3]:
                    ui.link(str(link.get("label") or "公式ドキュメント"), str(link.get("url") or "#"), new_tab=True).classes("card-hint")
                if reference_notes:
                    ui.separator()
                    ui.label("運用メモ").classes("card-sub font-bold")
                    _render_snapshot_cards(reference_notes[:5], empty_text="", detail_limit=180)

_ENGINEER_SOURCE_LABELS = {
    "legacy_page_report": "旧公開ページ検査",
    "link_health_summary": "内部リンク検査",
    "schema_summary": "構造化データ検査",
    "llms_summary": "llms.txt検査",
    "priority_actions": "優先アクション一覧",
    "accessibility": "アクセシビリティ検査",
    "site_health.security": "セキュリティ検査",
    "public_technology_risks": "公開技術リスク検査",
    "known_vulnerability_candidate": "既知脆弱性DB照合",
}

def _engineer_source_display(item: Dict[str, Any]) -> str:
    # Handoff items carry a raw detector id (e.g. issue id or module name) in
    # `source`. That's the right value for traceability but reads as a debug
    # slug in the UI, so map known ids to a plain label and fall back to the
    # already-Japanese `category` rather than the slug itself.
    raw = str(item.get("source") or "").strip()
    if raw in _ENGINEER_SOURCE_LABELS:
        return _ENGINEER_SOURCE_LABELS[raw]
    category = str(item.get("category") or "").strip()
    return category or raw

def _render_known_vulnerability_detail(site_health_check_item: Dict[str, Any]) -> None:
    # UI-only surfacing of core/site_health/vulnerability_intelligence.py's fixed
    # known-vulnerability match output. The engineer_tasks list above already turns
    # this into a plain-language task; this block adds the CVE ids / CVSS / KEV /
    # references an engineer needs to look up the advisory, without touching how
    # matches are computed. No detection or scoring logic is read or changed here.
    signals = ((site_health_check_item.get("public_technology_risks") or {}).get("signals")) or {}
    vuln_report = signals.get("fixed_vulnerability_intelligence") or {}
    matches = vuln_report.get("matches") or []
    status = str(vuln_report.get("status") or "")
    if status in {"db_missing", "db_unreadable", "schema_incompatible", "query_failed"}:
        ui.label("固定DBによる照合を完了できませんでした。脆弱性がないことを示す結果ではありません。").classes("card-hint text-xs text-amber-700")
        return
    if not matches:
        return
    database = vuln_report.get("database") or {}
    reference_date = str(database.get("reference_date") or database.get("created_at") or "-").strip() or "-"
    vuln_exp = ui.expansion(
        f"既知脆弱性候補の詳細（CVE） {vuln_report.get('match_count') or len(matches)}件", icon="bug_report", value=False
    ).classes("w-full mt-2")
    with vuln_exp:
        ui.label(f"固定脆弱性DB基準日: {reference_date}").classes("card-hint text-xs")
        if vuln_report.get("omitted_match_count"):
            ui.label(f"表示は安全上必要な範囲に限定しています（ほか{vuln_report.get('omitted_match_count')}件）。").classes("card-hint text-xs")
        for match in matches[:10]:
            component = str(match.get("component") or "-").strip() or "-"
            version = str(match.get("detected_version") or "-").strip() or "-"
            cve_ids = [str(cve).strip() for cve in (match.get("cve_ids") or []) if str(cve).strip()]
            severity = str(match.get("severity") or "medium").strip()
            kev = bool(match.get("kev"))
            cvss_score = match.get("cvss_score")
            fixed_version = str(match.get("fixed_version") or "").strip()
            evidence_url = str(match.get("evidence_url") or "").strip()
            with ui.column().classes("w-full border-l-4 border-red-300 pl-3 py-2 mt-2 gap-1"):
                header_bits = [f"{component} {version}"]
                if cve_ids:
                    header_bits.append(", ".join(cve_ids[:4]))
                ui.label(" / ".join(header_bits)).classes("card-sub font-bold")
                meta_bits = [f"重要度: {severity}"]
                if kev:
                    meta_bits.append("KEV（悪用実績あり）")
                if cvss_score is not None:
                    meta_bits.append(f"CVSS {cvss_score}")
                if fixed_version:
                    meta_bits.append(f"修正版: {fixed_version}")
                ui.label(" / ".join(meta_bits)).classes("card-hint text-xs")
                if evidence_url:
                    ui.label(f"検出URL: {evidence_url}").classes("card-hint text-xs break-all")
                references = [str(ref).strip() for ref in (match.get("references") or []) if str(ref).strip()]
                for ref in references[:2]:
                    ui.link(ref, ref, new_tab=True).classes("card-hint text-xs break-all")
                display_note = str(match.get("display_note") or "").strip()
                if display_note:
                    ui.label(display_note).classes("card-hint text-xs")

def _render_workspace_engineer_tab(snapshot: Dict[str, Any], *, show_header: bool = True) -> None:
    technical_workspace = snapshot.get("technical_workspace") or {}
    summary_cards = [
        item for item in (technical_workspace.get("summary_cards") or [])
        if isinstance(item, dict) and str(item.get("detail") or "").strip()
    ]
    crawl_scope = technical_workspace.get("crawl_scope") or {}
    legacy_pages = technical_workspace.get("legacy_pages") or {}
    link_health = technical_workspace.get("link_health") or {}
    intent_role_map = technical_workspace.get("intent_role_map") or {}
    schema = technical_workspace.get("schema") or {}
    llms = technical_workspace.get("llms") or {}
    site_health_checks = technical_workspace.get("site_health_checks") or []
    accessibility_improvements = (
        technical_workspace.get("accessibility_improvements")
        or (snapshot.get("implementation_workspace") or {}).get("accessibility_improvements")
        or {}
    )
    accessibility_actions = [
        action for action in (accessibility_improvements.get("actions") or [])
        if _is_actual_accessibility_action(action)
    ]
    action_items = technical_workspace.get("action_items") or technical_workspace.get("actions") or []
    handoff_items = build_engineer_handoff_items(snapshot, limit=10)

    def _render_item_lines(items: list[dict], *, value_keys: tuple[str, ...], empty_text: str = "") -> None:
        rendered = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            lead = ""
            for key in value_keys:
                lead = str(item.get(key) or "").strip()
                if lead:
                    break
            if not lead:
                continue
            ui.label(f"・{lead}").classes("card-sub")
            rendered += 1
        if rendered == 0 and empty_text:
            ui.label(empty_text).classes("card-hint text-xs")

    def _render_handoff_items(items: list[dict]) -> None:
        if not items:
            return
        ui.separator()
        ui.label("エンジニア作業票").classes("card-sub font-bold")
        ui.label("対象、行う作業、確認方法だけを先に抜き出しています。担当者へ共有する場合はこのブロックから確認してください。").classes("card-hint text-xs")
        for index, item in enumerate(items, 1):
            with ui.card().classes("card p-4 w-full mt-2"):
                with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                    ui.label(f"{index}. {item.get('category') or '技術対応'}").classes("card-sub font-bold")
                    raw_source = str(item.get("source") or "").strip()
                    source_display = _engineer_source_display(item)
                    if source_display:
                        source_chip = ui.label(source_display).classes(
                            "text-xs px-2 py-1 rounded inline-flex bg-slate-100 text-slate-700"
                        )
                        if raw_source and raw_source != source_display:
                            source_chip.tooltip(f"検出元ID: {raw_source}")
                for label, key in (
                    ("対象", "target"),
                    ("作業", "work"),
                    ("確認方法", "verify"),
                ):
                    value = str(item.get(key) or "").strip()
                    if value:
                        ui.label(f"{label}: {value}").classes("card-hint text-xs whitespace-pre-line break-all")

    with ui.card().classes("card workspace-panel p-5 w-full"):
        if show_header:
            _render_workspace_header(
                title="エンジニア向け",
                description="構造化データ、llms.txt、内部リンク、技術健全性の詳細をまとめています。",
                mode_label="技術詳細",
            )

        _render_handoff_items(handoff_items)

        if summary_cards:
            ui.label("優先確認項目").classes("card-sub font-bold mt-3")
            with ui.row().classes("w-full gap-3 flex-wrap mt-2"):
                for item in summary_cards:
                    _render_engineer_summary_card(item)

        if crawl_scope:
            ui.separator()
            ui.label("クロール範囲").classes("card-sub font-bold")
            with ui.card().classes("card p-4 w-full mt-2"):
                _render_engineer_summary_card(
                    {
                        "title": str(crawl_scope.get("title") or "クロール範囲"),
                        "detail": str(crawl_scope.get("detail") or ""),
                        "status": crawl_scope.get("status"),
                        "status_label": crawl_scope.get("status_label"),
                    },
                    card_classes="card p-0 w-full bg-transparent shadow-none",
                )
                if crawl_scope.get("warning"):
                    ui.label(str(crawl_scope.get("warning"))).classes("card-hint text-xs text-orange-700 mt-2")
                if crawl_scope.get("error"):
                    ui.label(str(crawl_scope.get("error"))).classes("card-hint text-xs text-red-700 mt-1")
                priority_pages = crawl_scope.get("priority_pages") or []
                if priority_pages:
                    scope_exp = ui.expansion("取得できた優先ページ", icon="travel_explore", value=False).classes("w-full mt-2")
                    with scope_exp:
                        for page in priority_pages[:6]:
                            title = str(page.get("title") or page.get("url") or "-")
                            url = str(page.get("url") or "").strip()
                            ui.label(title).classes("card-sub")
                            if url:
                                ui.label(url).classes("card-hint text-xs break-all")
                source_sitemaps = crawl_scope.get("source_sitemaps") or []
                if source_sitemaps:
                    sitemap_exp = ui.expansion("参照した sitemap", icon="account_tree", value=False).classes("w-full mt-2")
                    with sitemap_exp:
                        for item in source_sitemaps[:5]:
                            ui.label(str(item)).classes("card-hint text-xs break-all")

        if intent_role_map:
            ui.separator()
            ui.label("検索意図・ページ役割マップ").classes("card-sub font-bold")
            with ui.card().classes("card p-4 w-full mt-2"):
                ui.label(str(intent_role_map.get("page_role") or "ページ役割")).classes("generated-title")
                ui.label(_intent_confidence_label(intent_role_map)).classes(
                    f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(str(intent_role_map.get('status') or 'info')) }"
                )
                ui.label(f"想定検索意図: {intent_role_map.get('user_intent') or '-'}").classes("card-sub mt-2")
                missing = intent_role_map.get("missing_content") or []
                if missing:
                    ui.label("不足情報: " + " / ".join(str(item) for item in missing[:5])).classes("card-hint text-xs")
                notes = intent_role_map.get("engineer_notes") or {}
                if notes:
                    notes_exp = ui.expansion("作業指示と実装メモ", icon="build", value=True).classes("w-full mt-2")
                    with notes_exp:
                        for label, key in (
                            ("実装場所", "fix_locations"),
                            ("追加見出し", "add_headings"),
                            ("FAQの方向性", "add_faq"),
                            ("構造化データ", "structured_data"),
                            ("内部リンク", "internal_links"),
                        ):
                            values = _intent_note_values(notes, key)
                            if not values:
                                continue
                            ui.label(label).classes("card-sub font-bold mt-2")
                            for value in values[:6]:
                                ui.label(f"・{value}").classes("card-hint text-xs")
                        ui.label("役割マップのFAQは方向性です。本文に採用する具体候補は「文章改善」のFAQ候補、構造化データの実装確認は下の構造化データ欄、内部リンクのリンク元/リンク先は内部リンク欄で確認します。").classes("card-hint text-xs mt-2")
                source_hits = intent_role_map.get("source_hits") or {}
                if source_hits:
                    source_exp = ui.expansion("判断に使った語句", icon="data_object", value=False).classes("w-full mt-2")
                    with source_exp:
                        for source, terms in source_hits.items():
                            if terms:
                                ui.label(
                                    f"{_intent_signal_source_label(source)}: {' / '.join(str(term) for term in terms[:8])}"
                                ).classes("card-hint text-xs")
                signals = intent_role_map.get("intent_signals") or []
                if signals:
                    sig_exp = ui.expansion("検索意図の検出語句", icon="analytics", value=False).classes("w-full mt-2")
                    with sig_exp:
                        for item in signals[:12]:
                            ui.label(
                                f"{_intent_signal_source_label(item.get('source'))}: {item.get('term')}"
                            ).classes("card-hint text-xs")
                page_signals = intent_role_map.get("page_signals") or {}
                if page_signals:
                    signal_exp = ui.expansion("ページ内の手がかり", icon="fact_check", value=False).classes("w-full mt-2")
                    with signal_exp:
                        for key, value in page_signals.items():
                            if isinstance(value, list):
                                value_text = " / ".join(str(item) for item in value[:8])
                            else:
                                value_text = str(value or "").strip()
                            if value_text:
                                ui.label(f"{_page_signal_label(key)}: {value_text}").classes("card-hint text-xs")

        if legacy_pages and int(legacy_pages.get("found_count") or 0) > 0:
            ui.separator()
            ui.label("古い公開ページ").classes("card-sub font-bold")
            with ui.card().classes("card p-4 w-full mt-2"):
                _render_engineer_summary_card(
                    legacy_pages,
                    card_classes="card p-0 w-full bg-transparent shadow-none",
                )
                technical_detail = str(legacy_pages.get("technical_detail") or "").strip()
                if technical_detail:
                    ui.label(technical_detail).classes("card-hint text-xs mt-2")
                pages = legacy_pages.get("pages") or []
                for page in pages[:5]:
                    url = str(page.get("final_url") or page.get("url") or "").strip()
                    if not url:
                        continue
                    ui.label(url).classes("card-sub break-all mt-2")
                    bits = [
                        str(page.get("reason") or "").strip(),
                        str(page.get("title") or "").strip(),
                    ]
                    ui.label(" / ".join(bit for bit in bits if bit)).classes("card-hint text-xs")
                recommendations = legacy_pages.get("recommendations") or []
                if recommendations:
                    rec_exp = ui.expansion("対応方法", icon="build", value=False).classes("w-full mt-2")
                    with rec_exp:
                        for item in recommendations[:3]:
                            ui.label(f"・{item}").classes("card-sub")
                engineer_tasks = legacy_pages.get("engineer_tasks") or []
                if engineer_tasks:
                    ui.label("対応タスク").classes("card-sub font-bold mt-3")
                    for index, item in enumerate(engineer_tasks[:5], 1):
                        with ui.card().classes("card p-3 w-full mt-2"):
                            ui.label(f"{index}. {item.get('title') or '対応'}").classes("card-sub font-bold")
                            if item.get("detail"):
                                ui.label(str(item.get("detail"))).classes("card-hint text-xs")
                verification_steps = legacy_pages.get("verification_steps") or []
                if verification_steps:
                    verify_exp = ui.expansion("完了確認", icon="fact_check", value=False).classes("w-full mt-2")
                    with verify_exp:
                        for item in verification_steps[:5]:
                            title = str(item.get("title") or "確認").strip()
                            detail = str(item.get("detail") or "").strip()
                            ui.label(title).classes("card-sub font-bold")
                            if detail:
                                ui.label(detail).classes("card-hint text-xs")

        if link_health:
            ui.separator()
            ui.label("内部リンク / リンク先監査").classes("card-sub font-bold")
            with ui.card().classes("card p-4 w-full mt-2"):
                _render_engineer_summary_card(
                    link_health,
                    card_classes="card p-0 w-full bg-transparent shadow-none",
                )
                diagnosis = str(link_health.get("diagnosis") or "").strip()
                if diagnosis:
                    ui.label(diagnosis).classes("card-sub mt-2")
                metrics = []
                if link_health.get("total_known_pages"):
                    metrics.append(f"把握ページ {link_health.get('total_known_pages')}件")
                if link_health.get("total_analyzed_pages"):
                    metrics.append(f"分析ページ {link_health.get('total_analyzed_pages')}件")
                if link_health.get("avg_depth") not in (None, ""):
                    metrics.append(f"平均深度 {link_health.get('avg_depth')}")
                if link_health.get("audited_target_count"):
                    metrics.append(f"リンク先監査 {link_health.get('audited_target_count')}件")
                if metrics:
                    ui.label(" / ".join(metrics)).classes("card-hint text-xs mt-2")
                link_opportunities = link_health.get("link_opportunities") or []
                if link_opportunities:
                    ui.label("内部リンク機会マップ").classes("card-sub font-bold mt-3")
                    ui.label("どこから、どこへ、何文言でリンクするかを上位3件だけ表示します。").classes("card-hint text-xs")
                    for index, item in enumerate(link_opportunities[:3], 1):
                        with ui.column().classes("w-full border-l-4 border-amber-300 pl-3 py-2 mt-2 gap-1"):
                            ui.label(f"{index}. {item.get('title') or '内部リンクを追加'}").classes("card-sub font-bold")
                            if item.get("source_url"):
                                ui.label(f"リンク元: {item.get('source_url')}").classes("card-hint text-xs break-all")
                            if item.get("target_url"):
                                ui.label(f"リンク先: {item.get('target_url')}").classes("card-hint text-xs break-all")
                            if item.get("recommended_anchor"):
                                ui.label(f"推奨アンカー: {item.get('recommended_anchor')}").classes("card-hint text-xs")
                            if item.get("placement"):
                                ui.label(f"設置場所: {item.get('placement')}").classes("card-hint text-xs")
                            if item.get("reason"):
                                ui.label(str(item.get("reason"))).classes("card-hint text-xs")
                            if item.get("check"):
                                ui.label(f"完了確認: {item.get('check')}").classes("card-hint text-xs")
                source_candidates = link_health.get("source_page_candidates") or []
                target_candidates = link_health.get("target_page_candidates") or []
                if not link_opportunities and (source_candidates or target_candidates or link_health.get("recommended_anchor")):
                    ui.label("内部リンク追加の作業指示").classes("card-sub font-bold mt-3")
                    if source_candidates:
                        ui.label(
                            "リンク元候補: "
                            + ", ".join(
                                str((item.get("url") or item.get("title")) if isinstance(item, dict) else item)
                                for item in source_candidates[:3]
                            )
                        ).classes("card-hint text-xs break-all")
                    if target_candidates:
                        ui.label(
                            "リンク先候補: "
                            + ", ".join(
                                str((item.get("url") or item.get("title")) if isinstance(item, dict) else item)
                                for item in target_candidates[:3]
                            )
                        ).classes("card-hint text-xs break-all")
                    if link_health.get("recommended_anchor"):
                        ui.label(f"推奨アンカー: {link_health.get('recommended_anchor')}").classes("card-hint text-xs")
                engineering_steps = link_health.get("engineering_steps") or []
                if engineering_steps:
                    steps_exp = ui.expansion("修正手順と合格条件", icon="task_alt", value=False).classes("w-full mt-2")
                    with steps_exp:
                        for item in engineering_steps[:4]:
                            ui.label(str(item.get("observed") or "確認項目")).classes("card-sub font-bold")
                            for label, key in (("修正場所", "fix_location"), ("確認コマンド", "command"), ("合格条件", "pass_condition")):
                                if item.get(key):
                                    ui.label(f"{label}: {item.get(key)}").classes("card-hint text-xs")

                for section_title, items, value_keys in (
                    ("エラーリンク候補", link_health.get("broken_targets") or [], ("detail", "final_url", "url")),
                    ("リダイレクト候補", link_health.get("redirected_targets") or [], ("detail", "final_url", "url")),
                    ("canonical 不整合候補", link_health.get("canonical_mismatches") or [], ("detail", "canonical_url", "url")),
                    ("noindex リンク先候補", link_health.get("noindex_targets") or [], ("detail", "url")),
                ):
                    if not items:
                        continue
                    exp = ui.expansion(section_title, icon="link_off", value=False).classes("w-full mt-2")
                    with exp:
                        _render_item_lines(items[:5], value_keys=value_keys)
                if link_health.get("orphan_pages"):
                    orphan_exp = ui.expansion("孤立ページ候補", icon="warning", value=False).classes("w-full mt-2")
                    with orphan_exp:
                        for item in (link_health.get("orphan_pages") or [])[:5]:
                            ui.label(f"・{item}").classes("card-sub break-all")

        if schema:
            ui.separator()
            ui.label("構造化データ").classes("card-sub font-bold")
            with ui.card().classes("card p-4 w-full mt-2"):
                _render_engineer_summary_card(
                    schema,
                    card_classes="card p-0 w-full bg-transparent shadow-none",
                )
                for line in (schema.get("summary_lines") or [])[:4]:
                    ui.label(str(line)).classes("card-hint text-xs mt-1")
                validation_issues = schema.get("validation_issues") or []
                if validation_issues:
                    validation_exp = ui.expansion("FAQ / schema 整合の注意", icon="rule", value=False).classes("w-full mt-2")
                    with validation_exp:
                        _render_item_lines(validation_issues[:5], value_keys=("question", "reason"))
                suggestions = schema.get("suggestions") or []
                if suggestions:
                    ui.label("追加候補（上位3件）").classes("card-sub font-bold mt-3")
                    for item in suggestions[:3]:
                        with ui.card().classes("card p-4 w-full mt-2"):
                            with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                                ui.label(str(item.get("status_label") or "未設定")).classes(
                                    f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(item.get('status')) }"
                                )
                                ui.label(str(item.get("priority") or "")).classes("generated-metric")
                            ui.label(str(item.get("schema_type") or "Schema")).classes("generated-title")
                            if item.get("summary"):
                                ui.label(str(item.get("summary"))).classes("card-hint text-xs whitespace-pre-line")
                            if item.get("why_for_ai_answer"):
                                ui.label(f"AI回答での価値: {item.get('why_for_ai_answer')}").classes("card-hint text-xs mt-2")
                            required_fields = item.get("required_fields") or []
                            if required_fields:
                                ui.label(f"必須/優先フィールド: {', '.join(str(field) for field in required_fields[:8])}").classes("card-hint text-xs")
                            for label, key in (("実装場所", "fix_location"), ("検証方法", "validation_method")):
                                if item.get(key):
                                    ui.label(f"{label}: {item.get(key)}").classes("card-hint text-xs")
                            template = str(item.get("template") or "").strip()
                            if template:
                                code_exp = ui.expansion("コードを見る", icon="code", value=False).classes("w-full mt-2")
                                with code_exp:
                                    ui.code(template[:2000]).classes("text-xs w-full")
                schema_checks = []
                for label, key in (("検証方法", "validation_method"), ("確認", "command"), ("合格条件", "pass_condition")):
                    if schema.get(key):
                        schema_checks.append(f"{label}: {schema.get(key)}")
                for line in schema_checks:
                    ui.label(line).classes("card-hint text-xs mt-1")

        if llms:
            ui.separator()
            ui.label("llms.txt").classes("card-sub font-bold")
            with ui.card().classes("card p-4 w-full mt-2"):
                _render_engineer_summary_card(
                    llms,
                    card_classes="card p-0 w-full bg-transparent shadow-none",
                )
                found_paths = llms.get("found_paths") or []
                if found_paths:
                    ui.label(f"検出パス: {', '.join(str(item) for item in found_paths[:3])}").classes("card-hint text-xs mt-2")
                setup_lines = []
                for label, key in (("設置判断", "setup_judgment"), ("配置場所", "fix_location"), ("Content-Type", "content_type"), ("確認コマンド", "command"), ("合格条件", "pass_condition")):
                    if llms.get(key):
                        setup_lines.append(f"{label}: {llms.get(key)}")
                for line in setup_lines:
                    ui.label(line).classes("card-hint text-xs mt-1")
                recommended_content = llms.get("recommended_content") or []
                if recommended_content:
                    content_exp = ui.expansion("推奨本文", icon="article", value=False).classes("w-full mt-2")
                    with content_exp:
                        for item in recommended_content[:5]:
                            ui.label(f"・{item}").classes("card-sub")
                if llms.get("issues"):
                    issues_exp = ui.expansion("要確認", icon="report_problem", value=False).classes("w-full mt-2")
                    with issues_exp:
                        for issue in (llms.get("issues") or [])[:4]:
                            ui.label(f"・{issue}").classes("card-sub")
                if llms.get("recommendations"):
                    rec_exp = ui.expansion("改善案", icon="description", value=False).classes("w-full mt-2")
                    with rec_exp:
                        for item in (llms.get("recommendations") or [])[:4]:
                            ui.label(f"・{item}").classes("card-sub")
                checked_paths = llms.get("checked_paths") or []
                if checked_paths and not found_paths:
                    ui.label(f"確認先: {', '.join(str(item) for item in checked_paths[:5])}").classes("card-hint text-xs mt-2")

        if site_health_checks:
            ui.separator()
            ui.label("OGP / セキュリティ / 見やすさ・使いやすさ").classes("card-sub font-bold")
            with ui.row().classes("w-full gap-3 flex-wrap mt-2"):
                for item in site_health_checks:
                    _render_engineer_summary_card(item)
            for item in site_health_checks:
                details_available = bool(
                    item.get("highlights")
                    or item.get("issues")
                    or item.get("recommendations")
                    or item.get("items")
                    or item.get("engineer_tasks")
                )
                if not details_available:
                    continue
                exp = ui.expansion(f"{item.get('title')}の詳細", icon="monitor_heart", value=False).classes("w-full mt-2")
                with exp:
                    rendered_detail_keys: set[str] = set()
                    highlights = _dedupe_detail_lines(
                        item.get("highlights") or [],
                        seen=rendered_detail_keys,
                        limit=3,
                    )
                    issues = _dedupe_detail_lines(
                        item.get("issues") or [],
                        seen=rendered_detail_keys,
                        limit=3,
                    )
                    recommendations = _dedupe_detail_lines(
                        item.get("recommendations") or [],
                        seen=rendered_detail_keys,
                        limit=3,
                    )
                    for line in highlights:
                        ui.label(f"・{line}").classes("card-sub")
                    for line in issues:
                        ui.label(f"・{line}").classes("card-hint text-xs text-orange-700")
                    for line in recommendations:
                        ui.label(f"・{line}").classes("card-hint text-xs")
                    engineer_tasks = item.get("engineer_tasks") or []
                    if engineer_tasks:
                        ui.label("エンジニア向け確認").classes("card-sub font-bold mt-2")
                        for task in engineer_tasks[:4]:
                            title = str(task.get("title") or "確認項目").strip()
                            work = str(task.get("work") or "").strip()
                            verify = str(task.get("verify") or "").strip()
                            ui.label(f"・{title}" + (f": {work}" if work else "")).classes("card-hint text-xs")
                            commands = [str(command).strip() for command in (task.get("commands") or []) if str(command).strip()]
                            for command in commands[:3]:
                                ui.label(f"  確認コマンド: {command}").classes("card-hint text-xs break-all")
                            if verify:
                                ui.label(f"  確認方法: {verify}").classes("card-hint text-xs")
                            pass_condition = str(task.get("pass_condition") or "").strip()
                            if pass_condition:
                                ui.label(f"  合格条件: {pass_condition}").classes("card-hint text-xs")

                    if item.get("key") == "security":
                        _render_known_vulnerability_detail(item)

        if accessibility_actions:
            ui.separator()
            ui.label("アクセシビリティ技術詳細").classes("card-sub font-bold")
            ui.label("対象要素、行うべき作業、確認方法、検出元をエンジニア向けにまとめています。").classes("card-hint text-xs")
            for index, action in enumerate(accessibility_actions[:8], 1):
                engineer = _accessibility_engineer(action)
                with ui.card().classes("card p-4 w-full mt-2"):
                    with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                        ui.label(f"{index}. {action.get('title') or '見やすさ・使いやすさ改善'}").classes("card-sub font-bold")
                        if action.get("affected_count") not in (None, "", 0):
                            ui.label(f"{action.get('affected_count')}件").classes("generated-metric")
                    for label, key in (
                        ("対象要素", "target_element"),
                        ("行うべき作業", "task"),
                        ("確認方法", "verification"),
                        ("検出元", "detection_source"),
                    ):
                        value = str(engineer.get(key) or action.get(key) or "").strip()
                        if value:
                            ui.label(f"{label}: {value}").classes("card-hint text-xs whitespace-pre-line break-all")
                    if engineer.get("raw_issue"):
                        ui.label(f"検出内容: {engineer.get('raw_issue')}").classes("card-hint text-xs text-orange-700")
        elif accessibility_improvements.get("confirmation_items"):
            ui.separator()
            ui.label("アクセシビリティ確認項目").classes("card-sub font-bold")
            for item in (accessibility_improvements.get("confirmation_items") or [])[:3]:
                with ui.card().classes("card p-4 w-full mt-2"):
                    ui.label(str(item.get("title") or "確認項目")).classes("card-sub font-bold")
                    if item.get("detail"):
                        ui.label(str(item.get("detail"))).classes("card-hint text-xs")
                    if item.get("detection_source"):
                        ui.label(f"検出元: {item.get('detection_source')}").classes("card-hint text-xs")

        if action_items:
            ui.separator()
            ui.label("技術アクション").classes("card-sub font-bold")
            _render_snapshot_cards(action_items[:4], empty_text="", show_label=False, detail_limit=180)

def _render_workspace_comparison_tab(snapshot: Dict[str, Any], same_url_history: list[dict], *, show_header: bool = True) -> None:
    comparison_workspace = snapshot.get("comparison_workspace") or {}
    previous_diff = comparison_workspace.get("previous_diff") or {}
    competitor_summary = comparison_workspace.get("competitor_summary") or {}
    display_history = []
    for row in same_url_history:
        display_row = dict(row)
        display_row["analyzed_at"] = format_jst_datetime(row.get("analyzed_at"))
        display_history.append(display_row)

    with ui.card().classes("card workspace-panel p-5 w-full"):
        if show_header:
            _render_workspace_header(
                title="履歴と比較",
                description="前回との差分と競合比較だけをまとめています。",
            )
        ui.label(f"前回比: {previous_diff.get('label', '前回なし')}").classes("card-sub")
        ui.label(str(comparison_workspace.get("run_note") or "")).classes("card-hint text-xs")

        if competitor_summary:
            ui.separator()
            ui.label("競合比較").classes("card-sub font-bold")
            status = str(competitor_summary.get("status") or "")
            if status == "available":
                if competitor_summary.get("url"):
                    ui.label(str(competitor_summary.get("url"))).classes("card-hint text-xs break-all")
                for row in competitor_summary.get("scores") or []:
                    ui.label(
                        f"{row.get('label')}: 自社 {row.get('own')} / 競合 {row.get('competitor')} / 差分 {row.get('diff'):+} ({row.get('verdict')})"
                    ).classes("card-sub")
                if competitor_summary.get("actions"):
                    ui.label("差分アクション").classes("card-sub font-bold mt-2")
                    _render_snapshot_cards(
                        competitor_summary.get("actions") or [],
                        empty_text="",
                        show_label=False,
                        detail_limit=180,
                    )
            else:
                ui.label(str(competitor_summary.get("message") or "比較情報はありません。")).classes(
                    f"card-sub px-2 py-1 rounded inline-flex { _status_badge_classes(status) }"
                )

        ui.separator()
        ui.label("同一URLの履歴").classes("card-sub font-bold")
        if display_history:
            history_columns = [
                {"name": "analyzed_at", "label": "分析日時 (JST)", "field": "analyzed_at", "align": "left"},
                {"name": "seo_score", "label": "SEO", "field": "seo_score", "align": "center"},
                {"name": "aio_score", "label": "AI認識", "field": "aio_score", "align": "center"},
                {"name": "total_issues", "label": "課題数", "field": "total_issues", "align": "center"},
            ]
            table = ui.table(columns=history_columns, rows=display_history, row_key="id", pagination=8).classes("w-full mt-3 text-sm")
            table.props("flat bordered separator=cell")
            table.on(
                "rowClick",
                lambda event: ui.navigate.to(
                    f"/runs/{_extract_row_id_from_event_args(event.args)}"
                ),
            )
        else:
            ui.label("比較できる履歴はまだありません。").classes("card-sub text-gray-500")

def _build_workspace_tab_plan(snapshot: Dict[str, Any], *, same_url_history: list[dict]) -> dict[str, list[dict]]:
    comparison_workspace = snapshot.get("comparison_workspace") or {}
    competitor_summary = comparison_workspace.get("competitor_summary") or {}
    primary = [
        {"name": "サマリー"},
        {"name": "やること"},
        {"name": "文章改善"},
        {"name": "実装・設定"},
    ]
    secondary = [
        {
            "name": "エンジニア向け",
            "icon": "terminal",
            "description": "構造化データ、llms.txt、内部リンク、技術健全性の詳細を見たいときだけ開きます。",
        }
    ]
    if same_url_history or competitor_summary:
        secondary.append(
            {
                "name": "履歴と比較",
                "icon": "history",
                "description": "前回との差分や競合比較を確認するときだけ開きます。",
            }
        )
    return {"primary": primary, "secondary": secondary}

def _render_workspace_tabs(snapshot: Dict[str, Any], *, same_url_history: list[dict]) -> None:
    tab_specs: list[tuple[str, Any]] = [
        ("サマリー", lambda: _render_workspace_summary_tab(snapshot, show_header=False)),
    ]
    if _saved_run_has_improvement_tab(snapshot):
        tab_specs.append(("やること", lambda: _render_workspace_task_tab(snapshot, show_header=False)))
    if _saved_run_has_writing_tab(snapshot):
        tab_specs.append(("文章改善", lambda: _render_workspace_writing_tab(snapshot, show_header=False)))
    if _saved_run_has_implementation_tab(snapshot):
        tab_specs.append(("実装・設定", lambda: _render_workspace_implementation_tab(snapshot, show_header=False)))
    if _saved_run_has_engineer_tab(snapshot):
        tab_specs.append(("エンジニア向け", lambda: _render_workspace_engineer_tab(snapshot, show_header=False)))
    if _saved_run_has_comparison_tab(snapshot, same_url_history):
        tab_specs.append(("履歴と比較", lambda: _render_workspace_comparison_tab(snapshot, same_url_history, show_header=False)))

    with ui.card().classes("card detail-tabs-card p-4 w-full"):
        with ui.tabs().props("outside-arrows mobile-arrows").classes("tabs saved-run-tabs saved-run-tabs-sticky w-full") as workspace_tabs:
            for name, _renderer in tab_specs:
                ui.tab(name)

        with ui.tab_panels(workspace_tabs, value=tab_specs[0][0]).classes("w-full saved-run-tab-panels mt-4"):
            for name, renderer in tab_specs:
                with ui.tab_panel(name).classes("px-0 pt-3"):
                    renderer()

def render_saved_run_workspace(bundle: Dict[str, Any]) -> None:
    snapshot = bundle.get("snapshot") or {}
    snapshot = _enrich_saved_snapshot_from_result(snapshot, bundle.get("result") or {})
    same_url_history = bundle.get("same_url_history") or []

    _render_saved_run_evaluation(bundle)

    tab_specs: list[tuple[str, Any]] = []
    if _saved_run_has_improvement_tab(snapshot):
        tab_specs.append(("やること", lambda: _render_saved_run_improvement_tab(snapshot)))
    if _saved_run_has_writing_tab(snapshot):
        tab_specs.append(("文章改善", lambda: _render_workspace_writing_tab(snapshot, show_header=False)))
    if _saved_run_has_implementation_tab(snapshot):
        tab_specs.append(("実装・設定", lambda: _render_workspace_implementation_tab(snapshot, show_header=False)))
    if _saved_run_has_engineer_tab(snapshot):
        tab_specs.append(("エンジニア向け", lambda: _render_workspace_engineer_tab(snapshot, show_header=False)))
    if _saved_run_has_comparison_tab(snapshot, same_url_history):
        tab_specs.append(("履歴と比較", lambda: _render_workspace_comparison_tab(snapshot, same_url_history, show_header=False)))

    if not tab_specs:
        return

    with ui.card().classes("card detail-tabs-card p-4 w-full"):
        with ui.tabs().props("outside-arrows mobile-arrows").classes("tabs saved-run-tabs saved-run-tabs-sticky w-full") as saved_run_tabs:
            for name, _renderer in tab_specs:
                ui.tab(name)

        with ui.tab_panels(saved_run_tabs, value=tab_specs[0][0]).classes("w-full saved-run-tab-panels mt-4"):
            for name, renderer in tab_specs:
                with ui.tab_panel(name).classes("px-0 pt-3"):
                    renderer()

