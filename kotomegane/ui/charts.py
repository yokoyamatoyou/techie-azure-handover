from __future__ import annotations

from typing import Any, Callable

import plotly.graph_objects as go
from nicegui import ui

from analysis_lib import (
    aggregate_url_evidence,
    build_evidence_stats,
    build_intent_cluster_series,
    build_overall_visibility_series,
    build_page_gap_trend_series,
    build_query_rollup_rows,
    build_query_drilldown_series,
    build_visibility_focus_series,
    classify_visibility_verdict,
    format_timestamp,
    normalize_text,
    parse_json_object,
)
from config import AppConfig
from ui.evidence_presenters import build_source_groups, extract_cited_sources, normalize_host
from ui.result_story_builders import build_visibility_state_label
from ui.styles import (
    THEME_BRAND,
    THEME_GRID_SOFT,
    THEME_GRID_STRONG,
    THEME_SERIES_AMBER,
    THEME_SERIES_BLUE,
    THEME_SERIES_CORAL,
    THEME_SERIES_SLATE,
    THEME_SERIES_TEAL,
    THEME_TEXT_HELPER,
    THEME_TEXT_MAIN,
)


def metric_card(label: str, value: str, detail: str) -> tuple[ui.label, ui.label]:
    with ui.card().classes("section-card metric-card p-5 flex-1"):
        ui.label(label).classes("text-[12px] uppercase tracking-[0.22em] soft-label")
        value_label = ui.label(value).classes("metric-font metric-value text-[34px] font-bold mt-3")
        detail_label = ui.label(detail).classes("text-[14px] leading-6 text-support mt-2")
    return value_label, detail_label


def insight_card(label: str, headline: str, detail: str) -> tuple[ui.label, ui.label]:
    with ui.card().classes("card-secondary insight-card p-4 flex-1 min-w-[240px]"):
        ui.label(label).classes("text-[12px] uppercase tracking-[0.22em] soft-label")
        headline_label = ui.label(headline).classes("section-font insight-headline text-[26px] font-bold mt-3")
        detail_label = ui.label(detail).classes("text-[15px] leading-7 text-support mt-3")
    return headline_label, detail_label


def localize_run_mode(run_mode: Any) -> str:
    mode = str(run_mode or "").lower()
    if mode == "scheduled":
        return "自動定期分析"
    if mode == "batch":
        return "定期分析"
    return "手動スポット確認"


def shorten_question_label(keyword: str, limit: int = 18) -> str:
    text = " ".join(str(keyword or "").split())
    if not text:
        return "この質問"
    return text[:limit] + ("…" if len(text) > limit else "")


def wrap_chart_question_label(text: Any, chunk_size: int = 16, max_chars: int = 32) -> str:
    value = str(text or "").strip()
    if not value:
        return "-"
    compact = value[:max_chars]
    chunks = [compact[index : index + chunk_size] for index in range(0, len(compact), chunk_size)]
    label = "<br>".join(chunks)
    if len(value) > max_chars:
        label += "…"
    return label


def build_citation_share_series(rows: list[dict[str, Any]], config: AppConfig, limit: int = 8) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        payload = parse_json_object(row.get("output_json"))
        grouped_sources = build_source_groups(extract_cited_sources(row, payload), payload, config)
        for category in ("self", "competitor", "third_party"):
            seen_hosts: set[str] = set()
            for source in grouped_sources[category]:
                host = normalize_host(source.get("host") or source.get("url"))
                if not host or host in seen_hosts:
                    continue
                seen_hosts.add(host)
                key = (category, host)
                counts[key] = counts.get(key, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0][1]))[:limit]
    return [{"category": category, "host": host, "count": count} for (category, host), count in ordered]


def build_keyword_volatility_series(rows: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        keyword = str(row.get("keyword_raw") or "").strip()
        if not keyword:
            continue
        grouped.setdefault(keyword, []).append(row)

    ordered_keywords = sorted(
        grouped.items(),
        key=lambda item: max(float(entry.get("analyzed_at") or 0.0) for entry in item[1]),
        reverse=True,
    )[:limit]

    series: list[dict[str, Any]] = []
    for keyword, items in ordered_keywords:
        ordered_items = sorted(items, key=lambda row: float(row.get("analyzed_at") or 0.0))
        points = []
        for item in ordered_items:
            score = int(item.get("visibility_score") or 0)
            verdict = build_visibility_state_label(
                score,
                bool(item.get("target_domain_hit")),
                bool(item.get("brand_mention_hit")),
            )
            points.append(
                {
                    "timestamp": format_timestamp(item.get("analyzed_at")),
                    "score": score,
                    "verdict": verdict,
                    "label": str(item.get("keyword_raw") or keyword),
                }
            )
        series.append({"keyword": keyword, "points": points})
    return series


def _find_heatmap_group_rows(selected_row: dict[str, Any], raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target_query = normalize_text(str(selected_row.get("keyword_raw") or selected_row.get("keyword_norm") or ""))
    target_run_id = str(selected_row.get("run_id") or "")
    matched = [
        row
        for row in raw_rows
        if normalize_text(str(row.get("keyword_raw") or row.get("keyword_norm") or "")) == target_query
        and str(row.get("run_id") or "") == target_run_id
    ]
    return matched or [selected_row]


def build_question_result_heatmap_chart(
    query_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    config: AppConfig,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
    limit: int = 12,
) -> go.Figure:
    fig = go.Figure()
    if not query_rows:
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 24, "r": 18, "t": 18, "b": 24},
            font={"color": THEME_TEXT_MAIN, "size": 14},
            annotations=[
                {
                    "text": "まだ質問別の結果を並べられるデータがありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ],
        )
        return fig

    verdict_rank = {"未露出": 0, "外部サイト優勢": 1, "自社あり": 2, "自社優勢": 3}
    base_rows = query_rows[:limit]
    display_rows: list[dict[str, Any]] = []
    for row in base_rows:
        group_rows = _find_heatmap_group_rows(row, raw_rows)
        aggregated_evidence = aggregate_url_evidence(group_rows, source_loader, config) if source_loader else []
        stats = build_evidence_stats(aggregated_evidence)
        verdict = classify_visibility_verdict(
            int(row.get("visibility_score") or 0),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        display_rows.append(
            {
                "result_id": str(row.get("result_id") or ""),
                "question": str(row.get("keyword_raw") or "-"),
                "verdict": verdict,
                "score": int(row.get("visibility_score") or 0),
                "self_cited": int(stats.get("self_cited") or 0),
                "competitor_cited": int(stats.get("competitor_cited") or 0),
                "external_cited": int(stats.get("external_cited") or 0),
                "self_candidate": int(stats.get("self_searched_only") or 0),
            }
        )

    display_rows = sorted(
        display_rows,
        key=lambda item: (
            verdict_rank.get(str(item["verdict"]), 9),
            int(item["score"]),
            str(item["question"]),
        ),
    )

    columns = ["判定", "自社引用", "比較対象引用", "外部引用", "自社候補"]
    inactive_color = "rgba(233, 227, 218, 0.72)"
    verdict_colors = {
        "自社優勢": THEME_SERIES_TEAL,
        "自社あり": THEME_SERIES_BLUE,
        "外部サイト優勢": THEME_SERIES_AMBER,
        "未露出": THEME_SERIES_CORAL,
    }
    column_colors = {
        "自社引用": THEME_SERIES_TEAL,
        "比較対象引用": THEME_SERIES_AMBER,
        "外部引用": THEME_SERIES_CORAL,
        "自社候補": THEME_SERIES_BLUE,
    }

    x_values: list[str] = []
    y_values: list[str] = []
    colors: list[str] = []
    texts: list[str] = []
    text_colors: list[str] = []
    customdata: list[list[str]] = []
    y_order: list[str] = []

    for item in display_rows:
        y_label = wrap_chart_question_label(item["question"], chunk_size=14, max_chars=30)
        y_order.append(y_label)
        cell_map = {
            "判定": {
                "active": True,
                "text": str(item["verdict"]),
                "detail": f"現在の判定は {item['verdict']} です。参考スコア {item['score']}。",
            },
            "自社引用": {
                "active": int(item["self_cited"]) > 0,
                "text": str(item["self_cited"]) if int(item["self_cited"]) > 0 else "",
                "detail": f"自社URLが根拠として {int(item['self_cited'])}件引用されました。"
                if int(item["self_cited"]) > 0
                else "この質問では自社URLの引用を確認できていません。",
            },
            "比較対象引用": {
                "active": int(item["competitor_cited"]) > 0,
                "text": str(item["competitor_cited"]) if int(item["competitor_cited"]) > 0 else "",
                "detail": f"比較対象URLが根拠として {int(item['competitor_cited'])}件引用されました。"
                if int(item["competitor_cited"]) > 0
                else "この質問では比較対象URLの引用は目立っていません。",
            },
            "外部引用": {
                "active": int(item["external_cited"]) > 0,
                "text": str(item["external_cited"]) if int(item["external_cited"]) > 0 else "",
                "detail": f"外部サイトが根拠として {int(item['external_cited'])}件引用されました。"
                if int(item["external_cited"]) > 0
                else "この質問では外部サイトの引用は目立っていません。",
            },
            "自社候補": {
                "active": int(item["self_candidate"]) > 0,
                "text": str(item["self_candidate"]) if int(item["self_candidate"]) > 0 else "",
                "detail": f"自社URLは候補として {int(item['self_candidate'])}件出ましたが、引用には届いていません。"
                if int(item["self_candidate"]) > 0
                else "この質問では自社URLの候補もまだ弱い状態です。",
            },
        }
        for column in columns:
            cell = cell_map[column]
            x_values.append(column)
            y_values.append(y_label)
            if column == "判定":
                colors.append(verdict_colors.get(str(item["verdict"]), inactive_color))
                text_colors.append("white")
            else:
                colors.append(column_colors[column] if cell["active"] else inactive_color)
                text_colors.append("white" if cell["active"] else THEME_TEXT_HELPER)
            texts.append(str(cell["text"]))
            customdata.append([item["question"], column, str(cell["detail"]), str(item["result_id"])])

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="markers+text",
            marker={
                "symbol": "square",
                "size": 36,
                "color": colors,
                "line": {"color": "rgba(255,255,255,0.88)", "width": 1.5},
            },
            text=texts,
            textposition="middle center",
            textfont={"size": 11, "color": text_colors, "family": "Noto Sans JP, sans-serif"},
            customdata=customdata,
            hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 24},
        font={"color": THEME_TEXT_MAIN, "size": 13},
        xaxis={
            "side": "top",
            "showgrid": False,
            "zeroline": False,
            "fixedrange": True,
            "tickfont": {"size": 12},
        },
        yaxis={
            "showgrid": False,
            "zeroline": False,
            "fixedrange": True,
            "categoryorder": "array",
            "categoryarray": list(reversed(y_order)),
            "automargin": True,
            "tickfont": {"size": 12},
        },
        hovermode="closest",
        showlegend=False,
        height=max(300, 110 + len(display_rows) * 42),
    )
    return fig


def build_score_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_citation_share_series(rows, config)
    if not series:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 24, "r": 18, "t": 18, "b": 24},
            font={"color": THEME_TEXT_MAIN, "size": 14},
            annotations=[
                {
                    "text": "まだ引用シェアを出せる根拠URLがありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ],
        )
        return fig

    color_map = {"self": THEME_SERIES_TEAL, "competitor": THEME_SERIES_AMBER, "third_party": THEME_SERIES_CORAL}
    label_map = {"self": "自社", "competitor": "比較対象", "third_party": "外部"}
    fig = go.Figure(
        go.Bar(
            x=[row["count"] for row in series],
            y=[wrap_chart_question_label(row["host"], chunk_size=18, max_chars=36) for row in series],
            orientation="h",
            marker={"color": [color_map[row["category"]] for row in series]},
            text=[f'{row["count"]}件' for row in series],
            textposition="outside",
            customdata=[[row["host"], label_map[row["category"]]] for row in series],
            hovertemplate="%{customdata[0]}<br>区分 %{customdata[1]}<br>引用登場 %{x}件<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 220, "r": 18, "t": 18, "b": 24},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "引用登場回数", "gridcolor": THEME_GRID_STRONG},
        yaxis={"automargin": True},
    )
    fig.update_traces(cliponaxis=False)
    return fig


def build_visibility_focus_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_visibility_focus_series(rows, config)
    fig = go.Figure()
    if series:
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in series],
                y=[point["visible_rate"] for point in series],
                mode="lines+markers",
                name="自社露出率",
                line={"width": 3, "color": THEME_SERIES_TEAL},
                marker={"size": 8},
                customdata=[[localize_run_mode(point["run_mode"]), point["question_set_name"], point["total_trials"]] for point in series],
                hovertemplate="%{x}<br>自社露出率 %{y}%<br>%{customdata[0]} / %{customdata[1]}<br>試行数 %{customdata[2]}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in series],
                y=[point["external_lead_rate"] for point in series],
                mode="lines+markers",
                name="外部サイト優勢率",
                line={"width": 3, "color": THEME_SERIES_CORAL},
                marker={"size": 8},
                customdata=[[localize_run_mode(point["run_mode"]), point["question_set_name"], point["total_trials"]] for point in series],
                hovertemplate="%{x}<br>外部サイト優勢率 %{y}%<br>%{customdata[0]} / %{customdata[1]}<br>試行数 %{customdata[2]}<extra></extra>",
            )
        )
    else:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ履歴の推移を描ける結果がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 24, "r": 18, "t": 18, "b": 24},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"gridcolor": THEME_GRID_STRONG},
        yaxis={"title": "割合 (%)", "gridcolor": THEME_GRID_STRONG, "rangemode": "tozero"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
    )
    fig.update_traces(cliponaxis=False)
    return fig


def build_history_chart(rows: list[dict[str, Any]]) -> go.Figure:
    series = build_keyword_volatility_series(rows)
    fig = go.Figure()
    palette = [THEME_BRAND, THEME_SERIES_BLUE, THEME_SERIES_TEAL, THEME_SERIES_AMBER, THEME_SERIES_SLATE]
    for index, item in enumerate(series):
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in item["points"]],
                y=[point["score"] for point in item["points"]],
                mode="lines+markers",
                name=shorten_question_label(item["keyword"], limit=16),
                line={"width": 3, "color": palette[index % len(palette)]},
                marker={"size": 8},
                customdata=[[point["verdict"], point["label"]] for point in item["points"]],
                hovertemplate="%{x}<br>参考スコア %{y}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
            )
        )
    if not series:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ揺れ幅を出せる履歴がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "確認時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "参考スコア", "range": [0, 100], "gridcolor": THEME_GRID_STRONG},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig


def build_overall_visibility_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_overall_visibility_series(rows, config)
    fig = go.Figure()
    if series:
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in series],
                y=[point["avg_score"] for point in series],
                mode="lines+markers",
                name="全体の見えやすさ",
                line={"width": 3, "color": THEME_BRAND},
                marker={"size": 8},
                customdata=[
                    [point["visible_rate"], point["score_stddev"], point["variance_label"], localize_run_mode(point["run_mode"]), point["question_set_name"]]
                    for point in series
                ],
                hovertemplate="%{x}<br>平均スコア %{y}<br>自社可視率 %{customdata[0]}%<br>標準偏差 %{customdata[1]} / %{customdata[2]}<br>%{customdata[3]} / %{customdata[4]}<extra></extra>",
            )
        )
    else:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ全体トレンドを描ける履歴がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "実行時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "平均スコア", "range": [0, 100], "gridcolor": THEME_GRID_STRONG},
    )
    return fig


def build_intent_cluster_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_intent_cluster_series(rows, config)
    fig = go.Figure()
    palette = [THEME_BRAND, THEME_SERIES_BLUE, THEME_SERIES_TEAL, THEME_SERIES_AMBER]
    for index, item in enumerate(series):
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in item["points"]],
                y=[point["score"] for point in item["points"]],
                mode="lines+markers",
                name=item["label"],
                line={"width": 3, "color": palette[index % len(palette)]},
                marker={"size": 7},
                customdata=[[localize_run_mode(point["run_mode"])] for point in item["points"]],
                hovertemplate="%{x}<br>%{fullData.name} %{y}<br>%{customdata[0]}<extra></extra>",
            )
        )
    if not series:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ意図クラスタの時系列がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "実行時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "意図別スコア", "range": [0, 100], "gridcolor": THEME_GRID_STRONG},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig


def build_page_gap_trend_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_page_gap_trend_series(rows, config)
    fig = go.Figure()
    palette = [THEME_SERIES_CORAL, THEME_SERIES_AMBER, THEME_SERIES_SLATE, THEME_BRAND]
    for index, item in enumerate(series):
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in item["points"]],
                y=[point["count"] for point in item["points"]],
                mode="lines+markers",
                name=item["label"],
                line={"width": 3, "color": palette[index % len(palette)]},
                marker={"size": 7},
                customdata=[[localize_run_mode(point["run_mode"])] for point in item["points"]],
                hovertemplate="%{x}<br>%{fullData.name} 未解消 %{y}件<br>%{customdata[0]}<extra></extra>",
            )
        )
    if not series:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ不足ページの推移を描ける履歴がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "実行時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "未解消ページ件数", "gridcolor": THEME_GRID_STRONG},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig


def build_query_drilldown_chart(rows: list[dict[str, Any]], keyword: str) -> go.Figure:
    series = build_query_drilldown_series(rows, keyword)
    fig = go.Figure()
    if series:
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in series],
                y=[point["score"] for point in series],
                mode="lines+markers",
                name="質問別推移",
                line={"width": 3, "color": THEME_SERIES_BLUE},
                marker={"size": 8},
                customdata=[[point["verdict"], localize_run_mode(point["run_mode"])] for point in series],
                hovertemplate="%{x}<br>スコア %{y}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
            )
        )
    else:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだこの質問の履歴がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "確認時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "質問別スコア", "range": [0, 100], "gridcolor": THEME_GRID_STRONG},
    )
    return fig
