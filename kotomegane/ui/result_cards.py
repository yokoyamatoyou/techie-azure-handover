from __future__ import annotations

from typing import Any, Callable

from nicegui import ui

from analysis_core.topic_signals import build_topic_signal_summary
from analysis_lib import aggregate_url_evidence, build_evidence_stats, format_timestamp, infer_page_gap, parse_json_object, resolve_analysis_mode
from config import AppConfig
from ui.comparison_candidate_builders import build_comparison_candidate_summary
from ui.evidence_presenters import (
    build_evidence_chip_class,
    build_evidence_meaning_label,
    build_evidence_table_rows,
    filter_evidence_items_by_status,
    find_group_rows,
)
from ui.result_story_builders import (
    build_competitive_snapshot_summary,
    build_evidence_stability_summary,
    build_evidence_reason_headline,
    build_evidence_reason_lines,
    build_keyword_verdict_summary,
    build_losing_prompt_heatmap_rows,
    build_page_gap_card_copy,
    build_page_opportunity_strip_rows,
    build_primary_metric_copy,
    build_source_focus_summary,
    build_source_influence_rows,
    build_verdict_text_class,
    build_visibility_state_label,
)

_EVIDENCE_COLUMNS = [
    {"name": "meaning_label", "label": "意味", "field": "meaning_label", "align": "left"},
    {"name": "title", "label": "タイトル", "field": "title", "align": "left"},
    {"name": "host", "label": "ドメイン", "field": "host", "align": "left"},
    {"name": "observation_label", "label": "観測", "field": "observation_label", "align": "left"},
    {"name": "reading", "label": "読み方", "field": "reading", "align": "left"},
]


def _render_topic_chip_row(title: str, items: list[str], chip_class: str) -> None:
    if not items:
        return
    with ui.column().classes("w-full gap-2 mt-3"):
        ui.label(title).classes("summary-eyebrow")
        with ui.row().classes("w-full gap-2 flex-wrap"):
            for item in items[:4]:
                ui.label(str(item)).classes(f"signal-chip {chip_class}")


def _render_network_edge_row(title: str, edges: list[dict[str, Any]]) -> None:
    if not edges:
        return
    with ui.column().classes("w-full gap-2 mt-3"):
        ui.label(title).classes("summary-eyebrow")
        with ui.row().classes("w-full gap-2 flex-wrap"):
            for edge in edges:
                ui.label(f"{edge['source']} ↔ {edge['target']}").classes("signal-chip signal-neutral")


def _render_candidate_chip_row(title: str, items: list[dict[str, Any]]) -> None:
    if not items:
        return
    with ui.column().classes("w-full gap-2 mt-3"):
        ui.label(title).classes("summary-eyebrow")
        with ui.row().classes("w-full gap-2 flex-wrap"):
            for item in items:
                label = str(item.get("name") or "-")
                kind = str(item.get("kind") or "").strip()
                chip_text = f"{label} / {kind}" if kind else label
                chip_class = "signal-positive" if str(item.get("source") or "") == "手入力" else "signal-neutral"
                ui.label(chip_text).classes(f"signal-chip {chip_class}")


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


def _render_question_type_heatmap(rows: list[dict[str, Any]]) -> None:
    if not rows:
        ui.label("まだ質問タイプごとの傾向は十分に見えていません。").classes("text-[13px] leading-6 text-helper mt-3")
        return
    with ui.column().classes("question-heatmap w-full mt-4 gap-2"):
        for row in rows:
            with ui.column().classes("w-full gap-2 rounded-[18px] border border-[#eadfd3] bg-white/70 px-4 py-3"):
                ui.label(str(row.get("label") or "-")).classes("text-[15px] font-bold text-main")
                with ui.row().classes("w-full gap-2 flex-wrap"):
                    for cell in row.get("cells") or []:
                        tone = str(cell.get("tone") or "found")
                        rate = float(cell.get("rate") or 0.0)
                        intensity = _heatmap_intensity_class(rate)
                        chip_class = "signal-neutral"
                        if tone == "cited":
                            chip_class = "signal-positive"
                        elif tone == "external":
                            chip_class = "signal-negative"
                        ui.label(f"{cell.get('axis')} {cell.get('rate_text') or '-'}").classes(
                            f"signal-chip {chip_class} heatmap-{tone} {intensity}"
                        )


def _render_question_focus_list(items: list[dict[str, Any]]) -> None:
    if not items:
        return
    with ui.column().classes("w-full gap-3 mt-4"):
        for item in items[:3]:
            with ui.column().classes("w-full gap-1 rounded-[18px] border border-[#eadfd3] bg-white/70 px-4 py-3"):
                with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                    ui.label(str(item.get("label") or "-")).classes("text-[15px] font-bold text-main")
                    ui.label(str(item.get("status_label") or "-")).classes("signal-chip signal-neutral")
                ui.label(str(item.get("summary") or "-")).classes("text-[14px] leading-6 font-bold text-helper")
                ui.label(str(item.get("detail") or "-")).classes("text-[13px] leading-6 text-support")


def _build_source_chip_class(owner_bucket: str) -> str:
    if owner_bucket == "self":
        return "signal-positive"
    if owner_bucket == "competitor":
        return "signal-neutral"
    return "signal-negative"


def _render_source_focus_list(items: list[dict[str, Any]], *, show_host: bool) -> None:
    if not items:
        return
    with ui.column().classes("w-full gap-3 mt-4"):
        for item in items[:3]:
            with ui.column().classes("w-full gap-1 rounded-[18px] border border-[#eadfd3] bg-white/72 px-4 py-3"):
                with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                    ui.label(str(item.get("label") or "-")).classes("text-[15px] font-bold text-main text-wrap-anywhere")
                    ui.label(str(item.get("owner_label") or "参照元")).classes(
                        f"signal-chip {_build_source_chip_class(str(item.get('owner_bucket') or ''))}"
                    )
                if show_host and str(item.get("host") or "").strip():
                    ui.label(str(item.get("host"))).classes("text-[13px] leading-5 text-helper text-wrap-anywhere support-clamp-1")
                ui.label(str(item.get("summary") or "-")).classes("text-[13px] leading-5 font-bold text-helper text-wrap-anywhere support-clamp-2")


def _render_source_influence_compact(rows: list[dict[str, Any]]) -> None:
    if not rows:
        ui.label("まだ主要ソースの傾向は見えていません。").classes("text-[13px] leading-6 text-helper mt-3")
        return
    max_count = max((int(item.get("trial_count") or 0) for item in rows), default=0)
    with ui.column().classes("source-influence-compact w-full gap-2 mt-4"):
        for item in rows[:3]:
            count = int(item.get("trial_count") or 0)
            width = 0 if max_count <= 0 else max(12, min(100, round((count / max_count) * 100)))
            with ui.row().classes("source-influence-compact-item w-full items-center gap-3"):
                ui.label(str(item.get("rank") or "-")).classes("ranked-source-rank")
                with ui.column().classes("ranked-source-copy gap-1"):
                    ui.label(str(item.get("label") or "-")).classes("ranked-source-title text-wrap-anywhere support-clamp-2")
                    meta_parts = [
                        str(item.get("host") or "").strip(),
                        str(item.get("adoption_label") or "").strip(),
                    ]
                    ui.label(" / ".join(part for part in meta_parts if part)).classes("ranked-source-meta")
                    with ui.element("div").classes("source-influence-bar"):
                        ui.element("div").classes(
                            f"source-influence-bar-fill source-influence-{item.get('owner_bucket') or 'external'}"
                        ).style(f"width: {width}%;")
                ui.label(str(item.get("owner_label") or "参照元")).classes(
                    f"signal-chip {_build_source_chip_class(str(item.get('owner_bucket') or ''))}"
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


def _render_evidence_stability_compact(summary: dict[str, Any]) -> None:
    ui.label("根拠の安定度").classes("summary-eyebrow mt-4")
    with ui.column().classes("judgment-compact-panel w-full gap-3 mt-2"):
        with ui.row().classes("w-full items-start justify-between gap-3 flex-wrap"):
            ui.label(str(summary.get("headline") or "根拠の安定度はまだ見えていません")).classes(
                "judgment-compact-headline"
            )
            ui.label(str(summary.get("badge_label") or "材料待ち")).classes(
                f"judgment-badge judgment-badge-{summary.get('badge_tone') or 'unknown'}"
            )
        _render_judgment_sharebar(list(summary.get("buckets") or []))
        with ui.row().classes("w-full gap-2 flex-wrap"):
            for item in summary.get("buckets") or []:
                ui.label(f"{item['label']} {item['share_text']}").classes(
                    f"competitive-snapshot-chip chip-{item.get('tone')}"
                )
        top_width = 0 if int(summary.get("top_source_count") or 0) <= 0 else max(8, min(100, round(float(summary.get("top_source_share") or 0.0))))
        with ui.column().classes("w-full gap-1"):
            with ui.row().classes("w-full items-center justify-between gap-3"):
                ui.label("上位ソース集中度").classes("judgment-meter-label")
                ui.label(f"{summary.get('concentration_label') or '-'} / {summary.get('top_source_share_text') or '0%'}").classes(
                    "judgment-meter-value"
                )
            with ui.element("div").classes("judgment-meter"):
                ui.element("div").classes(
                    f"judgment-meter-fill source-influence-{summary.get('top_source_owner') or 'external'}"
                ).style(f"width: {top_width}%;")
        ui.label(str(summary.get("summary") or "")).classes("text-[13px] leading-5 text-helper support-clamp-2")


def _render_competitive_snapshot(snapshot: dict[str, Any]) -> None:
    buckets = list(snapshot.get("buckets") or [])
    with ui.column().classes("competitive-snapshot w-full gap-3 mt-4"):
        with ui.row().classes("w-full items-start justify-between gap-3 flex-wrap"):
            with ui.column().classes("gap-1 flex-1 min-w-[220px]"):
                ui.label("AIの主要な参照先").classes("summary-eyebrow")
                ui.label(str(snapshot.get("headline") or "根拠サイトの偏りはまだ見えていません")).classes(
                    "competitive-snapshot-headline"
                )
            ui.label(str(snapshot.get("basis_label") or "引用元ベース")).classes("competitive-snapshot-badge")
        if int(snapshot.get("total") or 0) > 0:
            with ui.row().classes("competitive-sharebar w-full"):
                for item in buckets:
                    share = max(float(item.get("share") or 0.0), 0.0)
                    width = max(8.0, share) if int(item.get("count") or 0) > 0 else 0.0
                    if width <= 0:
                        continue
                    ui.element("div").classes(f"competitive-sharebar-segment segment-{item.get('tone')}").style(
                        f"width: {width}%;"
                    )
        with ui.row().classes("w-full gap-2 flex-wrap"):
            for item in buckets:
                ui.label(f"{item['label']} {item['share_text']}").classes(
                    f"competitive-snapshot-chip chip-{item.get('tone')}"
                )
        ui.label(str(snapshot.get("summary") or "")).classes("text-[13px] leading-5 text-helper support-clamp-2")


def _heatmap_cell_rate(row: dict[str, Any], tone: str) -> float:
    for cell in row.get("cells") or []:
        if str(cell.get("tone") or "") == tone:
            return float(cell.get("rate") or 0.0)
    return 0.0


def _render_priority_question_strip(rows: list[dict[str, Any]]) -> None:
    ui.label("改善優先の質問").classes("summary-eyebrow mt-4")
    if not rows:
        ui.label("まだ質問ごとの差は十分に見えていません。").classes("text-[13px] leading-6 result-strong-note mt-2")
        return
    with ui.column().classes("priority-question-strip w-full gap-2 mt-2"):
        for row in rows[:3]:
            cited_rate = _heatmap_cell_rate(row, "cited")
            found_rate = _heatmap_cell_rate(row, "found")
            external_rate = _heatmap_cell_rate(row, "external")
            with ui.row().classes("priority-question-row w-full items-center gap-2 flex-wrap"):
                ui.label(str(row.get("short_label") or row.get("label") or "-")).classes(
                    "priority-question-label text-wrap-anywhere"
                )
                for label, rate, tone in (
                    ("自社引用", cited_rate, "positive"),
                    ("自社候補", found_rate, "neutral"),
                    ("外部", external_rate, "negative"),
                ):
                    text = f"{label} {rate:.0f}%" if rate > 0 else f"{label} -"
                    ui.label(text).classes(f"priority-question-chip priority-question-{tone}")


def _render_page_opportunity_strip(items: list[dict[str, Any]]) -> None:
    if not items:
        ui.label("まだページタイプごとの改善候補は十分に整理できていません。").classes("text-[13px] leading-6 result-strong-note mt-3")
        return
    with ui.column().classes("w-full gap-3 mt-4"):
        for item in items[:6]:
            state = str(item.get("state") or "followup")
            chip_class = "signal-neutral"
            if state == "urgent":
                chip_class = "signal-negative"
            elif state == "maintain":
                chip_class = "signal-positive"
            with ui.column().classes(f"page-opportunity-item page-state-{state} gap-1 rounded-[18px] border border-[#f0d9c5] bg-white/70 px-4 py-3"):
                with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                    ui.label(str(item.get("page_type_label") or item.get("label") or "-")).classes("text-[15px] font-bold text-main")
                    ui.label(str(item.get("state_label") or "-")).classes(f"signal-chip {chip_class}")
                if str(item.get("summary") or "").strip():
                    ui.label(str(item.get("summary"))).classes("text-[13px] leading-6 result-strong-copy")
                if str(item.get("next_step") or "").strip():
                    ui.label(str(item.get("next_step"))).classes("text-[13px] leading-6 result-strong-note")


def render_hero_observation_snapshot(
    recent_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    config: AppConfig,
    container: ui.column,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
) -> None:
    container.clear()
    with container:
        ui.label("直近の観測サマリー").classes("summary-eyebrow")
        if not recent_rows:
            with ui.row().classes("w-full gap-4 flex-wrap"):
                with ui.card().classes("section-card hero-observation-card p-5 flex-1 min-w-[260px]"):
                    ui.label("まだ観測結果はありません").classes("hero-observation-title")
                    ui.label("1 件実行すると、見えているか / 評価軸 / 次に強化すべき論点 がここに出ます。").classes(
                        "text-[14px] leading-6 text-support mt-2"
                    )
                with ui.card().classes("section-card hero-observation-card p-5 flex-1 min-w-[260px]"):
                    ui.label("この画面で見ること").classes("hero-observation-title")
                    ui.label("市場でどこに見えていて、何が評価され、次に何を足すかを確認します。").classes(
                        "text-[14px] leading-6 text-support mt-2"
                    )
                with ui.card().classes("section-card hero-observation-card p-5 flex-1 min-w-[260px]"):
                    ui.label("改善へ渡す材料").classes("hero-observation-title")
                    ui.label("判断が固まったらコトミガキへ渡し、本文や構成の改善に進みます。").classes(
                        "text-[14px] leading-6 text-support mt-2"
                    )
            return

        latest = recent_rows[0]
        latest_payload = parse_json_object(latest.get("output_json"))
        selected_group_rows = find_group_rows(latest, raw_rows)
        aggregated_evidence = aggregate_url_evidence(selected_group_rows, source_loader, config) if source_loader else []
        evidence_stats = build_evidence_stats(aggregated_evidence)
        analysis_context = latest_payload.get("analysis_context") or {}
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
        page_gap_card = build_page_gap_card_copy(page_gap, visibility_state)
        topic_signals = build_topic_signal_summary(selected_group_rows, aggregated_evidence, config, page_gap=page_gap)
        comparison_candidates = build_comparison_candidate_summary(selected_group_rows, aggregated_evidence, config)
        strong_axes = topic_signals["self_topics"] or topic_signals["candidate_topics"]

        with ui.row().classes("w-full gap-4 flex-wrap items-stretch hero-observation-shell"):
            with ui.card().classes("section-card hero-observation-card p-5 flex-1 min-w-[250px]"):
                ui.label("見えているか").classes("hero-observation-title")
                ui.label(visibility_state).classes("hero-observation-value mt-3")
                ui.label(verdict_summary).classes("text-[14px] leading-6 text-support mt-3")
                ui.label(f"更新 {format_timestamp(latest.get('analyzed_at'))}").classes("text-[12px] leading-5 text-helper mt-3")
            with ui.card().classes("section-card hero-observation-card p-5 flex-1 min-w-[250px]"):
                ui.label("何が評価されているか").classes("hero-observation-title")
                ui.label(" / ".join(topic_signals["answer_topics"][:3]) or "まだ抽出なし").classes("hero-observation-value mt-3")
                ui.label(
                    f"自社引用 {int(evidence_stats['self_cited'])} / 外部引用 {int(evidence_stats['external_cited'])} / 比較対象引用 {int(evidence_stats['competitor_cited'])}"
                ).classes("text-[13px] leading-6 text-support mt-3")
                _render_candidate_chip_row("比較候補", comparison_candidates["observed_candidates"][:3])
            with ui.card().classes("section-card hero-observation-card p-5 flex-1 min-w-[250px]"):
                ui.label("自社が強い軸").classes("hero-observation-title")
                ui.label(" / ".join(strong_axes[:3]) or "まだ強い軸なし").classes("hero-observation-value mt-3")
                _render_topic_chip_row("自社が取れている軸", strong_axes[:4], "signal-positive")
            with ui.card().classes("section-card hero-observation-card p-5 flex-1 min-w-[250px]"):
                ui.label("次に強化すべき論点").classes("hero-observation-title")
                ui.label(page_gap_card["urgent_headline"]).classes("hero-observation-value mt-3")
                ui.label(page_gap_card["urgent_summary"]).classes("text-[14px] leading-6 text-support mt-3")
                _render_topic_chip_row("優先して足す軸", topic_signals["action_topics"][:4], "signal-neutral")
                # Same cross-service link convention/URL as the page header nav
                # (app.py) - contextual entry point at the moment the gap is
                # identified, not a new integration or shared identifier.
                ui.link("コトミガキで改善する", "http://127.0.0.1:8081", new_tab=True).classes(
                    "nav-link text-[13px] mt-3"
                ).style("padding:4px 10px;border:1px solid var(--border);border-radius:8px;display:inline-block;")


def render_latest_result_cards(
    recent_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    config: AppConfig,
    latest_result_container: ui.column,
    previous_delta_summary: dict[str, Any],
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
) -> None:
    latest_result_container.clear()
    with latest_result_container:
        if not recent_rows:
            with ui.card().classes("section-card p-5 w-full"):
                ui.label("今回の結果").classes("section-font section-title text-[28px] font-bold")
                ui.label("まだ保存された分析はありません。まずは 1 回実行して結果を作成してください。").classes("text-[15px] leading-7 soft-label mt-2")
            return

        latest = recent_rows[0]
        latest_payload = parse_json_object(latest.get("output_json"))
        selected_group_rows = find_group_rows(latest, raw_rows)
        aggregated_evidence = aggregate_url_evidence(selected_group_rows, source_loader, config) if source_loader else []
        evidence_stats = build_evidence_stats(aggregated_evidence)
        source_focus_summary = build_source_focus_summary(selected_group_rows, aggregated_evidence)
        competitive_snapshot = build_competitive_snapshot_summary(evidence_stats)
        source_influence_rows = build_source_influence_rows(source_focus_summary, limit=3)
        evidence_stability = build_evidence_stability_summary(evidence_stats, source_focus_summary, source_influence_rows)
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
        page_gap_card = build_page_gap_card_copy(page_gap, visibility_state)
        verdict_text_class = build_verdict_text_class(visibility_state)
        primary_metric = build_primary_metric_copy(latest)
        topic_signals = build_topic_signal_summary(selected_group_rows, aggregated_evidence, config, page_gap=page_gap)
        reason_headline = build_evidence_reason_headline(evidence_stats, visibility_state, analysis_mode)
        reason_lines = build_evidence_reason_lines(evidence_stats, analysis_mode)
        page_opportunities = build_page_opportunity_strip_rows(selected_group_rows, config)
        priority_question_rows = build_losing_prompt_heatmap_rows(selected_group_rows, limit=3)

        with ui.card().classes("stage-note-card w-full"):
            ui.label("今回の結果").classes("summary-eyebrow")
            ui.label("AIの主要な参照先、自社引用率、主要ソース、改善優先の質問、次に強化すべき論点の順で確認します。").classes(
                "text-[13px] leading-5 text-support mt-1"
            )
        with ui.row().classes("w-full gap-5 flex-wrap items-start"):
            with ui.card().classes("section-card result-highlight-card result-highlight-strong p-5 flex-1 min-w-[360px]"):
                ui.label("引用ベース").classes("result-tone-chip")
                ui.label("今回の結論").classes("section-font section-title text-[24px] font-bold mt-4")
                _render_competitive_snapshot(competitive_snapshot)
                with ui.card().classes("mini-stat-card w-full mt-4 gap-1"):
                    ui.label("自社引用率").classes("text-[12px] tracking-[0.18em] soft-label")
                    ui.label(f"{primary_metric['value_text']}").classes("metric-font text-[24px] font-bold text-main")
                    ui.label("AI回答で自社URLが採用された割合").classes("text-[12px] leading-5 text-helper mt-1 support-clamp-1")
                    if str(primary_metric["coverage_summary"] or "").strip():
                        ui.label(str(primary_metric["coverage_summary"])).classes("text-[12px] leading-5 text-helper mt-1 support-clamp-1")
                ui.label("入力した質問").classes("summary-eyebrow mt-4")
                ui.label(str(latest.get("keyword_raw") or "-")).classes("text-[15px] font-bold text-main mt-2 leading-6 text-wrap-anywhere support-clamp-2")
                ui.label(reason_headline).classes(f"section-font text-[30px] leading-[1.35] font-bold mt-5 text-wrap-anywhere headline-clamp-2 {verdict_text_class}")
                ui.label(" ".join(reason_lines[:2]) or verdict_summary).classes("text-[14px] leading-6 text-support mt-3 text-wrap-anywhere support-clamp-3")
                with ui.row().classes("w-full gap-2 mt-4 flex-wrap"):
                    if previous_delta_summary.get("available"):
                        ui.label(f"前回の保存結果との差 {previous_delta_summary['target_hit_rate_delta']:+.1f}pt").classes(
                            "signal-chip signal-positive" if float(previous_delta_summary["target_hit_rate_delta"]) >= 0 else "signal-chip signal-negative"
                        )
            with ui.card().classes("section-card result-highlight-card result-highlight-quiet p-5 flex-1 min-w-[320px]"):
                ui.label("実URLは詳細へ").classes("result-tone-chip")
                ui.label("AI回答に使われた主要ソース").classes("section-font section-title text-[24px] font-bold mt-4")
                if str(source_focus_summary.get("lead_source_label") or "").strip():
                    ui.label("Top 3").classes("summary-eyebrow mt-5")
                    ui.label(str(source_focus_summary["lead_source_label"])).classes("summary-mainline mt-2 text-wrap-anywhere headline-clamp-2 text-self")
                else:
                    ui.label("まだ主要ソースの傾向は見えていません").classes("summary-mainline mt-5 text-wrap-anywhere headline-clamp-2 text-helper")
                if str(source_focus_summary.get("lead_source_basis_text") or "").strip():
                    ui.label(str(source_focus_summary["lead_source_basis_text"])).classes("text-[13px] leading-5 font-bold text-helper mt-3 text-wrap-anywhere support-clamp-2")
                _render_evidence_stability_compact(evidence_stability)
                _render_source_influence_compact(source_influence_rows)
            with ui.card().classes("section-card result-highlight-card result-highlight-quiet p-5 flex-1 min-w-[320px]"):
                ui.label("AIの認識").classes("result-tone-chip")
                ui.label("頻出論点").classes("section-font text-[24px] font-bold mt-4 result-strong-title")
                _render_priority_question_strip(priority_question_rows)
                next_topics = topic_signals.get("action_topics") or topic_signals.get("missing_topics") or topic_signals.get("competitive_topics") or []
                _render_topic_chip_row("次に強化すべき論点", next_topics, "signal-negative")
                _render_page_opportunity_strip(page_opportunities[:3])
                if topic_signals.get("answer_topics"):
                    ui.label("よく扱われる論点").classes("summary-eyebrow result-strong-title mt-4")
                    ui.label(" / ".join(topic_signals["answer_topics"][:3])).classes(
                        "result-strong-headline mt-2 text-wrap-anywhere headline-clamp-2"
                    )
                    ui.label("回答や引用ページで繰り返し出るテーマです。").classes("text-[14px] leading-5 result-strong-copy mt-2 text-wrap-anywhere support-clamp-2")
                else:
                    ui.label("まだ論点の傾向は十分に見えていません").classes(
                        "result-strong-headline mt-4 text-wrap-anywhere headline-clamp-2"
                    )
                _render_topic_chip_row("よく扱われる論点", topic_signals.get("answer_topics") or topic_signals.get("question_topics") or [], "signal-neutral")
                ui.label("質問タイプ別の深掘りや実URLは詳細側で確認します。ここでは改善判断に必要な要点だけを先に読みます。").classes(
                    "text-[13px] leading-5 result-strong-note mt-4 support-clamp-2"
                )


def render_waiting_latest_result_state(
    latest_result_container: ui.column,
    *,
    has_saved_results: bool,
) -> None:
    latest_result_container.clear()
    with latest_result_container:
        with ui.card().classes("section-card current-empty-card p-5 w-full"):
            with ui.row().classes("w-full items-start justify-between gap-3 flex-wrap"):
                with ui.column().classes("gap-1 min-w-[260px]"):
                    ui.label("今回の結果").classes("result-scope-eyebrow")
                    ui.label("今の入力では未分析").classes("section-font section-title text-[28px] font-bold")
                ui.label("未実行").classes("scope-status-chip current-status-chip")
            if has_saved_results:
                ui.label("今の入力ではまだ分析していません。これはエラーではありません。前回の保存結果は下の累積傾向と履歴だけに分けて表示します。").classes(
                    "text-[15px] leading-7 soft-label mt-2"
                )
            else:
                ui.label("まだ保存された分析はありません。質問と自社URLを入れて、まずは 1 回だけ確認してください。").classes(
                    "text-[15px] leading-7 soft-label mt-2"
                )
            ui.label("保存済みの累積傾向は下の過去データとして確認できます。").classes("text-[13px] leading-6 text-helper mt-3")


def render_current_evidence_section(
    query_rollup_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    config: AppConfig,
    source_container: ui.column,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
    *,
    show_current_result: bool = True,
) -> None:
    source_container.clear()
    with source_container:
        ui.label("引用URLは詳細で確認").classes("section-font section-title text-[24px] font-bold")
        ui.label("上段では `AI回答に使われた主要ソース` をページ名とサイト名で要約し、実URLは結果詳細側へ寄せています。").classes(
            "text-[14px] leading-6 soft-label mt-2"
        )
        if not show_current_result:
            ui.label("まだこのセッションでは詳細確認できる引用URLはありません。前回の保存結果は下の累積傾向と履歴で確認できます。").classes(
                "text-[15px] soft-label mt-2"
            )
            return
        if not query_rollup_rows:
            ui.label("まだ保存された引用URLはありません").classes("text-[15px] soft-label mt-2")
            return
        ui.label("実際に根拠に使われたURL、見つかったが未採用のURL、確認が必要なURLは `結果詳細` の中で確認してください。").classes(
            "text-[15px] leading-7 text-support mt-4"
        )
        ui.label("上段では、URL を並べる代わりに `今回の結論 / AI回答に使われた主要ソース / 頻出論点` を先に読めるようにしています。").classes(
            "text-[13px] leading-6 text-helper mt-3"
        )
