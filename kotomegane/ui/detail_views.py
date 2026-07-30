from __future__ import annotations

from typing import Any, Callable

from nicegui import ui

from analysis_lib import (
    aggregate_url_evidence,
    build_answer_structure_fields,
    build_evidence_stats,
    build_topic_signal_summary,
    format_timestamp,
    join_csv,
    normalize_query_text,
    parse_json_object,
    resolve_analysis_mode,
    sanitize_external_url,
    split_url_evidence_sections,
)
from config import ANALYSIS_MODE_MARKET, AppConfig
from ui.evidence_presenters import build_evidence_table_rows, extract_cited_sources, find_group_rows, localize_url_action_label
from ui.result_story_builders import (
    build_evidence_stability_summary,
    build_losing_prompt_heatmap_rows,
    build_source_focus_summary,
    build_source_influence_rows,
    build_visibility_stability_summary,
    build_weak_question_type_summary,
    build_visibility_state_label,
    localize_analysis_mode,
)


def _resolve_row_trial_count(row: dict[str, Any]) -> int:
    return max(
        int(row.get("trial_count") or 0),
        int(row.get("answer_observation_count") or 0),
        int(row.get("result_count") or 0),
        1 if row.get("result_id") else 0,
    )


def build_trial_basis_counts(selected_row: dict[str, Any], group_rows: list[dict[str, Any]]) -> dict[str, int]:
    seed_rows = group_rows or ([selected_row] if selected_row.get("result_id") else [])
    if not seed_rows:
        return {
            "trial_count": 0,
            "visible_trial_count": 0,
            "citation_trial_count": 0,
            "external_lead_trial_count": 0,
            "self_candidate_trial_count": 0,
        }

    counts = {
        "trial_count": 0,
        "visible_trial_count": 0,
        "citation_trial_count": 0,
        "external_lead_trial_count": 0,
        "self_candidate_trial_count": 0,
    }
    for row in seed_rows:
        row_trial_count = _resolve_row_trial_count(row)
        verdict = build_visibility_state_label(
            int(row.get("visibility_score") or 0),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        visible_trial_count = max(
            int(row.get("visible_trial_count") or 0),
            int(row.get("target_hit_count") or 0),
            row_trial_count if row.get("target_domain_hit") and row_trial_count == 1 else 0,
        )
        citation_trial_count = max(
            int(row.get("citation_trial_count") or 0),
            int(row.get("owned_citation_trial_count") or 0),
            int(row.get("owned_citation_result_count") or 0),
            1 if row_trial_count == 1 and int(row.get("owned_citation_count") or 0) > 0 else 0,
        )
        external_lead_trial_count = max(
            int(row.get("external_lead_trial_count") or 0),
            row_trial_count if verdict == "外部サイト優勢" and row_trial_count == 1 else 0,
        )
        self_candidate_trial_count = max(
            int(row.get("self_candidate_trial_count") or 0),
            max(0, visible_trial_count - citation_trial_count),
        )
        counts["trial_count"] += row_trial_count
        counts["visible_trial_count"] += visible_trial_count
        counts["citation_trial_count"] += citation_trial_count
        counts["external_lead_trial_count"] += external_lead_trial_count
        counts["self_candidate_trial_count"] += self_candidate_trial_count
    return counts


def localize_run_mode(run_mode: Any) -> str:
    mode = str(run_mode or "").strip().lower()
    if mode == "scheduled":
        return "自動チェック"
    if mode == "batch":
        return "まとめて分析"
    return "1回だけ確認"


def build_verdict_chip_class(verdict: str) -> str:
    if verdict == "自社優勢":
        return "signal-positive"
    if verdict in {"外部サイト優勢", "未露出"}:
        return "signal-negative"
    return "signal-neutral"


def _heatmap_intensity_class(rate: float) -> str:
    if rate >= 75:
        return "heatmap-intensity-4"
    if rate >= 50:
        return "heatmap-intensity-3"
    if rate >= 25:
        return "heatmap-intensity-2"
    if rate > 0:
        return "heatmap-intensity-1"
    return "heatmap-intensity-0"


def _owner_chip_class(owner_bucket: str) -> str:
    if owner_bucket == "self":
        return "signal-positive"
    if owner_bucket == "competitor":
        return "signal-neutral"
    return "signal-negative"


def _render_losing_prompt_heatmap(rows: list[dict[str, Any]]) -> None:
    ui.label("改善優先の質問").classes("summary-eyebrow mt-5")
    if not rows:
        ui.label("まだ質問タイプごとの差は十分に見えていません。").classes("text-[13px] leading-6 text-helper mt-2")
        return
    with ui.column().classes("mini-heatmap w-full mt-3 gap-2"):
        with ui.row().classes("mini-heatmap-header w-full items-center gap-2"):
            ui.label("質問").classes("mini-heatmap-question")
            for label in ("自社引用", "自社候補", "外部"):
                ui.label(label).classes("mini-heatmap-axis")
        for row in rows[:5]:
            cells = list(row.get("cells") or [])
            cited_rate = next((float(cell.get("rate") or 0.0) for cell in cells if str(cell.get("tone") or "") == "cited"), 0.0)
            external_rate = next((float(cell.get("rate") or 0.0) for cell in cells if str(cell.get("tone") or "") == "external"), 0.0)
            found_rate = next((float(cell.get("rate") or 0.0) for cell in cells if str(cell.get("tone") or "") == "found"), 0.0)
            with ui.row().classes("mini-heatmap-row w-full items-center gap-2"):
                ui.label(str(row.get("short_label") or row.get("label") or "-")).classes("mini-heatmap-question")
                for tone, rate in (("cited", cited_rate), ("found", found_rate), ("external", external_rate)):
                    ui.label(f"{rate:.0f}%" if rate > 0 else "-").classes(
                        f"mini-heatmap-cell heatmap-{tone} {_heatmap_intensity_class(rate)}"
                    )


def _render_source_influence_ranking(rows: list[dict[str, Any]]) -> None:
    ui.label("AI回答に使われた主要ソース").classes("summary-eyebrow mt-5")
    if not rows:
        ui.label("まだランキング化できる引用元はありません。").classes("text-[13px] leading-6 text-helper mt-2")
        return
    max_count = max((int(item.get("trial_count") or 0) for item in rows), default=0)
    with ui.column().classes("ranked-source-list w-full"):
        for item in rows[:5]:
            count = int(item.get("trial_count") or 0)
            width = 0 if max_count <= 0 else max(12, min(100, round((count / max_count) * 100)))
            with ui.row().classes("ranked-source-item w-full"):
                ui.label(str(item.get("rank") or "-")).classes("ranked-source-rank")
                with ui.column().classes("ranked-source-copy gap-0"):
                    ui.label(str(item.get("label") or "-")).classes("ranked-source-title text-wrap-anywhere support-clamp-2")
                    meta_parts = [
                        str(item.get("host") or "").strip(),
                        str(item.get("adoption_label") or "").strip(),
                    ]
                    ui.label(" / ".join(part for part in meta_parts if part)).classes("ranked-source-meta")
                    with ui.element("div").classes("source-influence-bar mt-2"):
                        ui.element("div").classes(
                            f"source-influence-bar-fill source-influence-{item.get('owner_bucket') or 'external'}"
                        ).style(f"width: {width}%;")
                ui.label(str(item.get("owner_label") or "参照元")).classes(
                    f"signal-chip {_owner_chip_class(str(item.get('owner_bucket') or ''))}"
                )


def _render_judgment_sharebar(buckets: list[dict[str, Any]]) -> None:
    if not any(int(item.get("count") or 0) > 0 for item in buckets):
        return
    with ui.row().classes("judgment-sharebar w-full"):
        for item in buckets:
            count = int(item.get("count") or 0)
            if count <= 0:
                continue
            width = max(8.0, float(item.get("share") or 0.0))
            ui.element("div").classes(f"judgment-sharebar-segment segment-{item.get('tone')}").style(f"width: {width}%;")


def _render_visibility_segments(summary: dict[str, Any]) -> None:
    with ui.row().classes("judgment-segments w-full"):
        for item in summary.get("segments") or []:
            active_class = "judgment-segment-active" if item.get("active") else ""
            ui.label(str(item.get("label") or "-")).classes(f"judgment-segment judgment-segment-{item.get('key')} {active_class}")


def _render_weak_question_items(summary: dict[str, Any]) -> None:
    items = list(summary.get("items") or [])
    if not items:
        ui.label("まだ質問タイプごとの差は十分に見えていません。").classes("text-[13px] leading-6 text-helper mt-2")
        return
    with ui.column().classes("w-full gap-2 mt-2"):
        for item in items[:3]:
            with ui.column().classes("judgment-question-row w-full gap-2"):
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    ui.label(str(item.get("short_label") or item.get("label") or "-")).classes("judgment-question-label")
                    ui.label(str(item.get("status_label") or "-")).classes(
                        f"judgment-small-badge judgment-small-badge-{item.get('tone') or 'medium'}"
                    )
                with ui.row().classes("w-full gap-2 flex-wrap"):
                    ui.label(f"自社引用 {item.get('cited_rate_text') or '0%'}").classes("priority-question-chip priority-question-positive")
                    ui.label(f"自社候補 {item.get('found_rate_text') or '0%'}").classes("priority-question-chip priority-question-neutral")
                    ui.label(f"外部 {item.get('external_rate_text') or '0%'}").classes("priority-question-chip priority-question-negative")


def _summary_bucket_share(summary: dict[str, Any], key: str) -> float:
    for bucket in summary.get("buckets") or []:
        if str(bucket.get("key") or "") == key:
            return float(bucket.get("share") or 0.0)
    return 0.0


def _priority_tone_from_badge(value: Any) -> str:
    tone = str(value or "").strip()
    if tone in {"high", "variable"}:
        return "high"
    if tone in {"medium", "chance"}:
        return "medium"
    if tone in {"low", "stable"}:
        return "low"
    return "unknown"


def _render_judgment_priority_strip(
    evidence_stability: dict[str, Any],
    visibility_stability: dict[str, Any],
    weak_question_summary: dict[str, Any],
) -> None:
    external_share = _summary_bucket_share(evidence_stability, "external")
    top_source_share = float(evidence_stability.get("top_source_share") or 0.0)
    evidence_tone = _priority_tone_from_badge(evidence_stability.get("badge_tone"))
    if external_share >= 55 or top_source_share >= 65:
        evidence_tone = "high"
    elif external_share >= 35 or top_source_share >= 45:
        evidence_tone = "medium" if evidence_tone != "high" else evidence_tone
    external_share_text = next(
        (
            str(bucket.get("share_text") or "0%")
            for bucket in evidence_stability.get("buckets") or []
            if str(bucket.get("key") or "") == "external"
        ),
        "0%",
    )

    visibility_tone = _priority_tone_from_badge(visibility_stability.get("status_key") or visibility_stability.get("badge_tone"))
    weak_items = list(weak_question_summary.get("items") or [])
    weak_lead = weak_items[0] if weak_items else {}
    weak_tone = _priority_tone_from_badge(weak_lead.get("tone") if weak_lead else "unknown")
    weak_label = str(weak_lead.get("short_label") or weak_lead.get("label") or "未判定")

    steps = [
        {
            "icon": "public",
            "title": "外部サイト依存",
            "value": f"外部 {external_share_text}",
            "next": "主要ソースを見る",
            "tone": evidence_tone,
        },
        {
            "icon": "shuffle",
            "title": "見え方の揺れ",
            "value": str(visibility_stability.get("badge_label") or "偶然寄り"),
            "next": "観測回数を見る",
            "tone": visibility_tone,
        },
        {
            "icon": "priority_high",
            "title": "弱い質問タイプ",
            "value": weak_label,
            "next": "質問タイプを見る",
            "tone": weak_tone,
        },
    ]
    with ui.column().classes("judgment-priority-strip w-full gap-3 mt-5"):
        with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
            ui.label("先に見る順番").classes("summary-eyebrow")
            ui.label("危ない順に確認").classes("judgment-small-badge judgment-small-badge-medium")
        with ui.row().classes("w-full gap-2 flex-wrap"):
            for index, step in enumerate(steps, start=1):
                with ui.row().classes(f"judgment-priority-step priority-step-{step['tone']} flex-1 min-w-[220px]"):
                    ui.label(str(index)).classes("priority-step-index")
                    ui.icon(str(step["icon"])).classes("priority-step-icon")
                    with ui.column().classes("gap-0 min-w-0"):
                        ui.label(str(step["title"])).classes("priority-step-title")
                        ui.label(str(step["value"])).classes("priority-step-value")
                        ui.label(str(step["next"])).classes("priority-step-next")


def _render_judgment_summary_panels(
    evidence_stability: dict[str, Any],
    visibility_stability: dict[str, Any],
    weak_question_summary: dict[str, Any],
) -> None:
    _render_judgment_priority_strip(evidence_stability, visibility_stability, weak_question_summary)
    with ui.row().classes("judgment-panel-grid w-full gap-3 mt-5"):
        with ui.column().classes("judgment-summary-panel flex-1 min-w-[260px] gap-3"):
            with ui.row().classes("w-full items-start justify-between gap-2"):
                ui.label("根拠の安定度").classes("summary-eyebrow")
                ui.label(str(evidence_stability.get("badge_label") or "材料待ち")).classes(
                    f"judgment-badge judgment-badge-{evidence_stability.get('badge_tone') or 'unknown'}"
                )
            ui.label(str(evidence_stability.get("headline") or "根拠の安定度はまだ見えていません")).classes("judgment-card-headline")
            _render_judgment_sharebar(list(evidence_stability.get("buckets") or []))
            with ui.row().classes("w-full gap-2 flex-wrap"):
                for item in evidence_stability.get("buckets") or []:
                    ui.label(f"{item['label']} {item['share_text']}").classes(
                        f"competitive-snapshot-chip chip-{item.get('tone')}"
                    )
            top_width = (
                0
                if int(evidence_stability.get("top_source_count") or 0) <= 0
                else max(8, min(100, round(float(evidence_stability.get("top_source_share") or 0.0))))
            )
            with ui.column().classes("w-full gap-1"):
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    ui.label("上位ソース集中度").classes("judgment-meter-label")
                    ui.label(
                        f"{evidence_stability.get('concentration_label') or '-'} / {evidence_stability.get('top_source_share_text') or '0%'}"
                    ).classes("judgment-meter-value")
                with ui.element("div").classes("judgment-meter"):
                    ui.element("div").classes(
                        f"judgment-meter-fill source-influence-{evidence_stability.get('top_source_owner') or 'external'}"
                    ).style(f"width: {top_width}%;")
            ui.label(str(evidence_stability.get("summary") or "")).classes("text-[13px] leading-5 text-helper")

        with ui.column().classes("judgment-summary-panel flex-1 min-w-[260px] gap-3"):
            with ui.row().classes("w-full items-start justify-between gap-2"):
                ui.label("見え方の安定度").classes("summary-eyebrow")
                ui.label(str(visibility_stability.get("badge_label") or "偶然寄り")).classes(
                    f"judgment-badge judgment-badge-{visibility_stability.get('badge_tone') or 'chance'}"
                )
            ui.label(str(visibility_stability.get("headline") or "まだ偶然寄りです")).classes("judgment-card-headline")
            _render_visibility_segments(visibility_stability)
            with ui.row().classes("w-full gap-2 flex-wrap"):
                ui.label(str(visibility_stability.get("basis_text") or "観測 0回 / 自社引用 0回")).classes("judgment-small-badge judgment-small-badge-medium")
                ui.label(f"外部先行 {visibility_stability.get('external_rate_text') or '0%'}").classes("judgment-small-badge judgment-small-badge-high")
            ui.label(str(visibility_stability.get("summary") or "")).classes("text-[13px] leading-5 text-helper")

        with ui.column().classes("judgment-summary-panel flex-1 min-w-[260px] gap-3"):
            ui.label("弱い質問タイプ").classes("summary-eyebrow")
            ui.label(str(weak_question_summary.get("headline") or "弱い質問タイプはまだ見えていません")).classes("judgment-card-headline")
            ui.label(str(weak_question_summary.get("summary") or "")).classes("text-[13px] leading-5 text-helper")
            _render_weak_question_items(weak_question_summary)


def _render_url_bucket(
    title: str,
    items: list[dict[str, Any]],
    *,
    empty_text: str,
    chip_class: str,
) -> None:
    ui.label(title).classes("summary-eyebrow mt-4")
    if not items:
        ui.label(empty_text).classes("text-[14px] soft-label mt-2")
        return
    for item in items[:8]:
        safe_url = sanitize_external_url(item.get("url"))
        with ui.row().classes("w-full items-start justify-between gap-3 mt-2 flex-wrap"):
            with ui.column().classes("gap-0"):
                if safe_url:
                    ui.link(str(item.get("title") or item.get("url") or "-"), safe_url, new_tab=True).classes("evidence-link text-[14px]")
                else:
                    ui.label(str(item.get("title") or item.get("url") or "-")).classes("evidence-link text-[14px]")
                meta = str(item.get("host") or item.get("url") or "-")
                detail = meta
                status = str(item.get("status") or "")
                if status:
                    detail += f" / {localize_url_action_label(status)}"
                if not item.get("is_confident"):
                    detail += " / 確認が必要"
                if not safe_url:
                    detail += " / 無効なURL"
                ui.label(detail).classes("text-[12px] leading-6 text-helper")
            ui.label(title).classes(f"signal-chip {chip_class}")


def render_topic_chip_row(title: str, items: list[str], chip_class: str) -> None:
    chips = [str(item).strip() for item in items if str(item).strip()]
    if not chips:
        return
    ui.label(title).classes("summary-eyebrow mt-4")
    with ui.row().classes("w-full gap-2 mt-2 flex-wrap"):
        for item in chips[:5]:
            ui.label(item).classes(f"signal-chip {chip_class}")


def build_next_action_copy(
    selected_row: dict[str, Any],
    topic_signals: dict[str, Any],
    evidence_stability: dict[str, Any],
    weak_question_summary: dict[str, Any],
) -> dict[str, str]:
    action_topics = [str(item).strip() for item in topic_signals.get("action_topics") or [] if str(item).strip()]
    missing_topics = [str(item).strip() for item in topic_signals.get("missing_topics") or [] if str(item).strip()]
    weak_headline = str(weak_question_summary.get("headline") or "").strip()
    evidence_headline = str(evidence_stability.get("headline") or "").strip()
    query = str(selected_row.get("keyword_raw") or selected_row.get("keyword_norm") or "選択中の質問").strip()
    if action_topics:
        action = f"{action_topics[0]} を説明できるページや見出しを先に確認する"
        reason = "今回の回答と根拠URLで、次に強化すべき論点として目立っています。"
    elif missing_topics:
        action = f"{missing_topics[0]} について、自社ページ側の説明不足を確認する"
        reason = "外部サイト側で目立つ話題が、自社根拠として拾われていない可能性があります。"
    elif weak_headline and "まだ" not in weak_headline:
        action = "弱い質問タイプの上位から、回答に必要な情報を補う"
        reason = weak_headline
    elif evidence_headline:
        action = "AI回答に使われた主要ソースを確認する"
        reason = evidence_headline
    else:
        action = "自社URLが根拠に入ったかを確認する"
        reason = "まだ次の改善対象を絞るには材料が少ないため、引用有無から確認します。"
    return {
        "action": action,
        "reason": reason,
        "scope": f"対象質問: {query}",
        "next": "下の主要ソース、弱い質問タイプ、根拠URLを順に確認します。",
    }


def render_next_action_card(copy: dict[str, str]) -> None:
    with ui.column().classes("detail-result-block w-full gap-2 mt-4"):
        ui.label("次にやること").classes("detail-tone-chip")
        ui.label(str(copy.get("action") or "-")).classes("section-font section-title text-[22px] font-bold text-main")
        ui.label(str(copy.get("reason") or "-")).classes("text-[14px] leading-6 text-support")
        with ui.row().classes("w-full gap-2 flex-wrap"):
            ui.label(str(copy.get("scope") or "-")).classes("signal-chip signal-neutral")
            ui.label(str(copy.get("next") or "-")).classes("signal-chip signal-positive")


def format_list_or_dash(items: list[str] | None) -> str:
    values = [str(item).strip() for item in (items or []) if str(item).strip()]
    return ", ".join(values) if values else "-"


def build_analysis_context_lines(payload: dict[str, Any]) -> list[str]:
    analysis_context = payload.get("analysis_context") or {}
    if not analysis_context:
        return []
    lines = [
        f"監査モード: {localize_analysis_mode(str(analysis_context.get('analysis_mode') or ANALYSIS_MODE_MARKET))}",
        f"自社URL: {analysis_context.get('target_domain') or '-'}",
        f"名称: {format_list_or_dash(analysis_context.get('brand_terms'))}",
    ]
    market_context_terms = format_list_or_dash(analysis_context.get("market_context_terms"))
    if market_context_terms != "-":
        lines.append(f"重点テーマ: {market_context_terms}")
    competitor_terms = format_list_or_dash(analysis_context.get("competitor_terms"))
    if competitor_terms != "-":
        lines.append(f"比較対象: {competitor_terms}")
    return lines


def localize_snapshot_text(text: Any) -> str:
    return str(text or "").replace("競合", "比較対象")


def refresh_result_detail_views(
    rollup_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    detail_select: ui.select,
    detail_container: ui.column,
    config: AppConfig,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
    *,
    show_current_result: bool = True,
) -> None:
    options = {
        row["result_id"]: f"{format_timestamp(row.get('analyzed_at'))} | {row.get('keyword_raw')}"
        for row in rollup_rows[:80]
    }
    current_value = detail_select.value if detail_select.value in options else None
    if current_value is None and options:
        current_value = next(iter(options))
    detail_select.options = options
    detail_select.value = current_value
    detail_select.update()

    selected_row = next((row for row in rollup_rows if row.get("result_id") == current_value), None)
    detail_container.clear()
    with detail_container:
        if not selected_row:
            ui.label("結果詳細はまだありません").classes("text-[15px] soft-label")
            return
        unique_questions = len({str(row.get("keyword_raw") or row.get("keyword_norm") or "") for row in rollup_rows if row.get("result_id")})
        result_count = len(rollup_rows)
        ui.label(
            f"対象質問 {unique_questions}件 / 保存済み結果 {result_count}件"
        ).classes("text-[13px] leading-6 text-helper")
        ui.label(str(selected_row.get("keyword_raw") or "-")).classes("text-[16px] font-bold text-main mt-2 text-wrap-anywhere")
        if not show_current_result:
            ui.label(
                "この詳細は保存済み結果です: "
                f"{format_timestamp(selected_row.get('analyzed_at'))} / "
                f"{selected_row.get('keyword_raw') or '-'} / "
                f"{selected_row.get('target_domain') or config.target_domain or '-'} / "
                f"{localize_run_mode(selected_row.get('run_mode'))}"
            ).classes("text-[13px] leading-6 text-helper mt-1 text-wrap-anywhere")
        payload = parse_json_object(selected_row.get("output_json"))
        selected_group_rows = find_group_rows(selected_row, raw_rows)
        answer_text = str(selected_row.get("answer_text") or payload.get("answer_text") or "").strip()
        citations = extract_cited_sources(selected_row, payload)
        aggregated_evidence = aggregate_url_evidence(selected_group_rows, source_loader, config)
        evidence_sections = split_url_evidence_sections(aggregated_evidence)
        source_focus_summary = build_source_focus_summary(selected_group_rows, aggregated_evidence)
        source_influence_rows = build_source_influence_rows(source_focus_summary)
        losing_heatmap_rows = build_losing_prompt_heatmap_rows(selected_group_rows)
        evidence_stability = build_evidence_stability_summary(
            build_evidence_stats(aggregated_evidence),
            source_focus_summary,
            source_influence_rows,
        )
        visibility_stability = build_visibility_stability_summary(selected_row)
        weak_question_summary = build_weak_question_type_summary(losing_heatmap_rows)
        topic_signals = build_topic_signal_summary(selected_group_rows, aggregated_evidence, config)
        analysis_context_lines = build_analysis_context_lines(payload)
        answer_structure = build_answer_structure_fields(selected_row, config)
        trial_basis_counts = build_trial_basis_counts(selected_row, selected_group_rows)
        trial_count = int(trial_basis_counts["trial_count"])
        visible_trial_count = int(trial_basis_counts["visible_trial_count"])
        citation_trial_count = int(trial_basis_counts["citation_trial_count"])
        external_lead_trial_count = int(trial_basis_counts["external_lead_trial_count"])
        self_candidate_trial_count = int(trial_basis_counts["self_candidate_trial_count"])
        next_action_copy = build_next_action_copy(
            selected_row,
            topic_signals,
            evidence_stability,
            weak_question_summary,
        )
        verdict = build_visibility_state_label(
            int(selected_row.get("visibility_score") or 0),
            bool(selected_row.get("target_domain_hit")),
            bool(selected_row.get("brand_mention_hit")),
        )
        with ui.card().classes("card-detail p-5 w-full"):
            ui.label("今回の結果" if show_current_result else "保存済み結果").classes("result-tone-chip")
            render_next_action_card(next_action_copy)
            ui.label("改善判断サマリー").classes("section-font section-title text-[24px] font-bold mt-4")
            ui.label(f"{selected_row.get('keyword_raw')}").classes("text-[18px] font-bold text-main mt-2")
            with ui.row().classes("w-full gap-2 mt-3 flex-wrap"):
                ui.label(verdict).classes(f"signal-chip {build_verdict_chip_class(verdict)}")
                ui.label(str(answer_structure.get("answer_type_label") or "返答分析未分類")).classes("signal-chip signal-neutral")
            _render_judgment_summary_panels(evidence_stability, visibility_stability, weak_question_summary)
            with ui.column().classes("detail-result-block w-full gap-0 mt-4"):
                ui.label("今回の結論").classes("detail-tone-chip")
                ui.label(localize_snapshot_text(selected_row.get("answer_snapshot") or payload.get("answer_snapshot") or "-")).classes(
                    "text-[15px] leading-7 text-support mt-4"
                )
                _render_source_influence_ranking(source_influence_rows)
                render_topic_chip_row("次に強化すべき論点", topic_signals["action_topics"], "signal-neutral")
                render_topic_chip_row("外部サイト側で目立った話題", topic_signals["missing_topics"], "signal-negative")
                ui.label("結果詳細").classes("detail-tone-chip mt-5")
                ui.label("観測回数ベースの内訳").classes("summary-eyebrow mt-5")
                ui.label("今回は何回の確認で、何回そうなったかをそのまま見ています。").classes(
                    "text-[13px] leading-6 text-helper mt-2"
                )
                with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("観測した回数").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(f"{trial_count}回").classes("metric-font text-[18px] font-bold text-main")
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("自社が見つかった回数").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(f"{visible_trial_count}回").classes("metric-font text-[18px] font-bold text-self")
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("自社URLが引用された回数").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(f"{citation_trial_count}回").classes("metric-font text-[18px] font-bold text-self")
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("外部先行だった回数").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(f"{external_lead_trial_count}回").classes("metric-font text-[18px] font-bold text-external")
                ui.label("観測回数ベースの割合").classes("summary-eyebrow mt-5")
                with ui.row().classes("w-full gap-3 mt-2 flex-wrap"):
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("自社露出率").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(f"{(visible_trial_count / trial_count * 100.0):.1f}%" if trial_count else "0.0%").classes("metric-font text-[18px] font-bold text-self")
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("自社引用率").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(f"{(citation_trial_count / trial_count * 100.0):.1f}%" if trial_count else "0.0%").classes("metric-font text-[18px] font-bold text-self")
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("外部先行率").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(f"{(external_lead_trial_count / trial_count * 100.0):.1f}%" if trial_count else "0.0%").classes("metric-font text-[18px] font-bold text-external")
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("見つかったが未採用だった率").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(f"{(self_candidate_trial_count / trial_count * 100.0):.1f}%" if trial_count else "0.0%").classes("metric-font text-[18px] font-bold text-main")
                ui.label("返答の特徴").classes("summary-eyebrow mt-5")
                with ui.row().classes("w-full gap-3 mt-2 flex-wrap"):
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("返答タイプ").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label(str(answer_structure.get("answer_type_label") or "-")).classes("metric-font text-[18px] font-bold text-main")
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("自社名の言及").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label("あり" if answer_structure.get("owned_mention_hit") else "なし").classes(
                            f"metric-font text-[18px] font-bold {'text-self' if answer_structure.get('owned_mention_hit') else 'text-support'}"
                        )
                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                        ui.label("比較対象の言及").classes("text-[12px] tracking-[0.18em] soft-label")
                        ui.label("あり" if answer_structure.get("competitor_mention_hit") else "なし").classes(
                            f"metric-font text-[18px] font-bold {'text-competitive' if answer_structure.get('competitor_mention_hit') else 'text-support'}"
                        )
                render_topic_chip_row("AIが重視した論点", topic_signals["answer_topics"], "signal-neutral")
                render_topic_chip_row("外部サイト側で目立った話題", topic_signals["competitive_topics"], "signal-negative")
                render_topic_chip_row("自社が拾われやすかった話題", topic_signals["candidate_topics"], "signal-neutral")
                ui.label("ここに出る語は、今回の回答や根拠URLで繰り返し出てきた話題です。").classes(
                    "text-[13px] leading-6 text-helper mt-4"
                )
            with ui.column().classes("detail-result-block w-full gap-0 mt-5"):
                ui.label("根拠URLの状態").classes("detail-tone-chip")
                ui.label("今回、根拠に使われたURL").classes("summary-eyebrow mt-4")
                ui.label("まずは、AIが答えを作るときに根拠として使ったURLだけを見せます。").classes(
                    "text-[14px] leading-6 text-support mt-2"
                )
                _render_url_bucket("外部サイト", evidence_sections["cited"]["external"], empty_text="今回ここに入る外部引用はありません。", chip_class="signal-negative")
                _render_url_bucket("自社", evidence_sections["cited"]["self"], empty_text="今回ここに入る自社引用はありません。", chip_class="signal-positive")
                _render_url_bucket("比較対象", evidence_sections["cited"]["competitor"], empty_text="今回ここに入る比較対象引用はありません。", chip_class="signal-neutral")
                with ui.column().classes("w-full mt-5 panel-card p-4 gap-0"):
                    ui.label("見つかったが根拠には使われなかったURL").classes("summary-eyebrow")
                    ui.label("あと一歩で使われる可能性があったURLです。ページの中身や見せ方を見直す候補として使います。").classes(
                        "text-[13px] leading-6 text-helper mt-2"
                    )
                    _render_url_bucket("外部サイト", evidence_sections["searched_only"]["external"], empty_text="未引用の外部URLはありません。", chip_class="signal-negative")
                    _render_url_bucket("自社", evidence_sections["searched_only"]["self"], empty_text="未引用の自社URLはありません。", chip_class="signal-positive")
                    _render_url_bucket("比較対象", evidence_sections["searched_only"]["competitor"], empty_text="未引用の比較対象URLはありません。", chip_class="signal-neutral")
                with ui.column().classes("w-full mt-4 panel-card p-4 gap-0"):
                    ui.label("まだ確認が必要なURL").classes("summary-eyebrow")
                    ui.label("保存状況の都合で、使われたかどうかを今すぐ断定しにくいURLです。参考情報として見てください。").classes(
                        "text-[13px] leading-6 text-helper mt-2"
                    )
                    _render_url_bucket("外部サイト", evidence_sections["unknown"]["external"], empty_text="確認が必要な外部URLはありません。", chip_class="signal-negative")
                    _render_url_bucket("自社", evidence_sections["unknown"]["self"], empty_text="確認が必要な自社URLはありません。", chip_class="signal-positive")
                    _render_url_bucket("比較対象", evidence_sections["unknown"]["competitor"], empty_text="確認が必要な比較対象URLはありません。", chip_class="signal-neutral")
            with ui.column().classes("detail-result-block w-full gap-0 mt-5"):
                ui.label("今回の回答と根拠").classes("detail-tone-chip")
                ui.label("生返答").classes("summary-eyebrow mt-4")
                ui.label(answer_text or "保存された answer_text はありません。").classes("text-[15px] leading-7 text-main mt-2")
                ui.label("回答で使われた引用元").classes("summary-eyebrow mt-5")
                if citations:
                    for citation in citations[:8]:
                        safe_url = sanitize_external_url(citation.get("url"))
                        if safe_url:
                            ui.link(citation.get("title") or citation.get("url") or "-", safe_url, new_tab=True).classes(
                                "evidence-link text-[14px] block mt-2"
                            )
                        else:
                            ui.label(citation.get("title") or citation.get("url") or "-").classes("evidence-link text-[14px] block mt-2")
                else:
                    ui.label("保存された引用元はありません。").classes("text-[14px] soft-label mt-2")
            with ui.column().classes("detail-fixed-block w-full gap-0 mt-5"):
                ui.label("今回の条件").classes("detail-tone-chip")
                ui.label("入力した条件").classes("summary-eyebrow mt-4")
                if analysis_context_lines:
                    for line in analysis_context_lines:
                        ui.label(line).classes("text-[14px] leading-6 text-support mt-2")
                else:
                    ui.label("保存された条件はありません。").classes("text-[14px] soft-label mt-2")
            if selected_row.get("error_text"):
                ui.label("エラー").classes("summary-eyebrow mt-5")
                ui.label(str(selected_row.get("error_text") or "")).classes("text-[14px] leading-6 text-external mt-2")
