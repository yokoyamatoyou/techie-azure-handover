# -*- coding: utf-8 -*-
"""Enterprise dashboard helpers for saved analysis runs."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List
from urllib.parse import urlparse

from nicegui import ui

from core.application.artifact_paths import resolve_existing_result_path
from core.application.time_display import format_jst_datetime, format_jst_datetime_compact
from core.config import config

RUNS_DIR = config.POC_OUTPUT_DIR / "runs"


def _safe_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _compact_copy(value: Any, limit: int) -> str:
    text = _safe_text(value)
    if not text:
        return "-"
    if len(text) <= limit:
        return text
    return f"{text[: max(limit - 1, 1)].rstrip()}…"


def _render_dashboard_action_card(
    *,
    title: str,
    detail: str,
    area: str,
    level_label: str,
    card_classes: str,
    detail_expand_label: str = "全文を見る",
) -> None:
    clean_title = _safe_text(title) or "改善提案"
    clean_detail = _safe_text(detail)
    with ui.card().classes(f"card generated-block p-4 w-full {card_classes}"):
        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
            ui.label(level_label).classes("dashboard-action-chip")
            ui.label(area or "分析結果").classes("generated-metric")
        ui.label(clean_title).classes("generated-title whitespace-pre-line")
        if clean_detail:
            if len(clean_detail) <= 120:
                ui.label(clean_detail).classes("generated-body whitespace-pre-line")
            else:
                detail_exp = ui.expansion(detail_expand_label, icon="unfold_more", value=False).classes("w-full mt-2")
                with detail_exp:
                    ui.label(clean_detail).classes("generated-body whitespace-pre-line")


def _compact_url(value: Any, limit: int = 56) -> str:
    text = _safe_text(value)
    if not text:
        return "-"
    try:
        parsed = urlparse(text)
    except ValueError:
        return _compact_copy(text, limit)

    host = parsed.netloc or parsed.path
    path = parsed.path if parsed.netloc else ""
    if not path or path == "/":
        return _compact_copy(host or text, limit)

    compact_path = _compact_copy(path, max(limit - len(host) - 2, 12))
    return _compact_copy(f"{host}{compact_path}", limit)


def _compact_datetime(value: Any) -> str:
    formatted = format_jst_datetime_compact(value)
    if not formatted:
        return "-"
    return _compact_copy(formatted, 18)


def _extract_row_id_from_event_args(args: Any) -> int:
    if isinstance(args, dict):
        if "row" in args:
            return _safe_int((args.get("row") or {}).get("id"))
        return _safe_int(args.get("id"))
    if isinstance(args, list) and args:
        for item in args:
            if isinstance(item, dict):
                if "row" in item:
                    row_id = _safe_int((item.get("row") or {}).get("id"))
                else:
                    row_id = _safe_int(item.get("id"))
                if row_id:
                    return row_id
    return 0


def _parse_snapshot(raw_value: Any) -> Dict[str, Any]:
    if isinstance(raw_value, dict):
        return raw_value
    if not raw_value:
        return {}
    try:
        return json.loads(str(raw_value))
    except json.JSONDecodeError:
        return {}


def _resolve_integrated_score(snapshot: Dict[str, Any], row: Dict[str, Any]) -> int:
    result_path = _safe_text(row.get("result_path"))
    if result_path:
        try:
            safe_result_path = resolve_existing_result_path(result_path, runs_dir=RUNS_DIR)
            if safe_result_path is None:
                raise OSError("result_path_outside_runs_dir")
            result_payload = json.loads(safe_result_path.read_text(encoding="utf-8"))
            actual = _safe_int(((result_payload or {}).get("integrated_results") or {}).get("integrated_score"))
            if actual > 0:
                return actual
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    header = snapshot.get("header") or {}
    integrated_score = _safe_int(header.get("integrated_score"))
    if integrated_score > 0:
        return integrated_score

    seo_score = _safe_int(row.get("seo_score"))
    aio_score = _safe_int(row.get("aio_score"))
    return round((seo_score + aio_score) / 2)


def _format_previous_diff_label(previous_diff: Dict[str, Any]) -> str:
    label = _safe_text(previous_diff.get("label")) or "前回なし"
    if label == "前回なし":
        return label
    return f"前回比 {label}"


def build_history_rows(history_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in history_rows:
        snapshot = _parse_snapshot(item.get("snapshot_json"))
        meta = snapshot.get("meta") or {}
        header = snapshot.get("header") or {}
        top_actions = header.get("top_actions") or []
        previous_diff = header.get("previous_diff") or {}
        seo_score = _safe_int(item.get("seo_score"))
        aio_score = _safe_int(item.get("aio_score"))
        integrated_score = _resolve_integrated_score(snapshot, item)
        rows.append(
            {
                "id": _safe_int(item.get("id")),
                "analyzed_at": format_jst_datetime(item.get("analyzed_at")) or _safe_text(item.get("analyzed_at")),
                "display_date": _compact_datetime(item.get("analyzed_at")),
                "url": _safe_text(item.get("url")),
                "display_url": _compact_url(item.get("url")),
                "site_type": _safe_text(meta.get("site_type")) or "-",
                "industry": _safe_text(meta.get("industry")) or "-",
                "seo_score": seo_score,
                "aio_score": aio_score,
                "score_summary": f"総合 {integrated_score} / AI {aio_score} / SEO {seo_score}",
                "legal_score": _safe_int(item.get("legal_score")),
                "integrated_score": integrated_score,
                "priority_level": _safe_text(header.get("priority_level")) or "-",
                "total_issues": _safe_int(item.get("total_issues")),
                "issue_summary": f"{_safe_int(item.get('total_issues'))}件",
                "top_action": _safe_text((top_actions[0] or {}).get("title")) if top_actions else "-",
                "top_action_compact": _compact_copy((top_actions[0] or {}).get("title"), 48) if top_actions else "-",
                "top_actions": top_actions[:3],
                "previous_diff_label": _format_previous_diff_label(previous_diff),
                "result_path": _safe_text(item.get("result_path")),
                "snapshot_json": item.get("snapshot_json"),
            }
        )
    return rows


def build_dashboard_kpis(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not rows:
        return [
            {"label": "保存済み分析", "value": "0", "helper": "履歴がまだありません"},
            {"label": "平均 AI認識", "value": "-", "helper": "分析後に表示"},
            {"label": "高優先度", "value": "0", "helper": "優先対応なし"},
        ]

    avg_aio = round(sum(_safe_int(row.get("aio_score")) for row in rows) / len(rows))
    high_priority = sum(1 for row in rows if _safe_text(row.get("priority_level")) == "高")
    return [
        {"label": "保存済み分析", "value": str(len(rows)), "helper": "履歴全体"},
        {"label": "平均 AI認識", "value": f"{avg_aio}", "helper": "現在の一覧"},
        {"label": "高優先度", "value": str(high_priority), "helper": "対応優先の run"},
    ]


def build_dashboard_value_cards(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = [
        {
            "eyebrow": "このソフトで分かること",
            "title": "検索と AI 回答の両方で、先に直す場所を整理できます",
            "body": "AI認識、SEO、表示アドバイスをまとめて見て、改善の優先順を保存済みワークスペースへ残します。",
            "chips": ["AI認識", "SEO", "表示アドバイス"],
        }
    ]
    if rows:
        latest = rows[0]
        top_action = _safe_text(latest.get("top_action_compact"))
        cards.append(
            {
                "eyebrow": "最近の成果",
                "title": "直近の保存結果から、そのまま次の一手に進めます",
                "body": (
                    f"{_safe_text(latest.get('display_url'))} は {_safe_text(latest.get('score_summary'))}、"
                    f"優先度 {_safe_text(latest.get('priority_level'))}、課題 {_safe_text(latest.get('issue_summary'))}。"
                    f"まずは「{top_action or '保存済みワークスペースを開いて確認'}」から着手できます。"
                ),
                "chips": [
                    f"保存済み {len(rows)}件",
                    _safe_text(latest.get("previous_diff_label")) or "前回なし",
                ],
            }
        )
    else:
        cards.append(
            {
                "eyebrow": "次の入口",
                "title": "最初の 1 件を作ると、履歴と再表示の導線が整います",
                "body": "対象URLを入れると、保存済みワークスペースで優先度、改善提案、履歴比較まで続けて確認できます。",
                "chips": ["保存済みワークスペース", "履歴から再表示"],
            }
        )
    return cards


def render_dashboard_kpis(kpis: List[Dict[str, str]]) -> None:
    with ui.row().classes("w-full gap-3 items-stretch"):
        for kpi in kpis[:3]:
            with ui.card().classes("card p-4 flex-1 min-w-[180px]"):
                ui.label(kpi["label"]).classes("text-xs uppercase tracking-wide text-[#9B7A60]")
                ui.label(kpi["value"]).classes("text-3xl font-bold text-[#231815]")
                ui.label(kpi["helper"]).classes("text-sm text-gray-500")


def render_dashboard_summary_cards(rows: List[Dict[str, Any]]) -> None:
    with ui.column().classes("w-full gap-3"):
        for card in build_dashboard_value_cards(rows):
            with ui.card().classes("card dashboard-overview-card p-5 w-full"):
                ui.label(str(card.get("eyebrow") or "")).classes("section-eyebrow")
                ui.label(str(card.get("title") or "")).classes("card-title")
                ui.label(str(card.get("body") or "")).classes("card-hint text-sm")
                with ui.row().classes("w-full gap-2 flex-wrap mt-3"):
                    for chip in card.get("chips") or []:
                        ui.label(str(chip)).classes("generated-chip")


def _priority_badge_class(priority_level: str) -> str:
    if priority_level == "高":
        return "dashboard-priority-high"
    if priority_level == "中":
        return "dashboard-priority-mid"
    return "dashboard-priority-low"


def _render_score_bar(*, label: str, score: int, fill_class: str) -> None:
    with ui.row().classes("dashboard-score-row w-full items-center"):
        ui.label(label).classes("dashboard-score-label")
        with ui.element("div").classes("dashboard-score-track"):
            ui.element("div").classes(f"dashboard-score-fill {fill_class}").style(f"width: {max(0, min(score, 100))}%")
        ui.label(str(score)).classes("dashboard-score-value")


def _render_history_mobile_list(rows: List[Dict[str, Any]], *, on_open_run: Callable[[int], None]) -> None:
    shown_count = {"value": min(8, len(rows))}

    @ui.refreshable
    def mobile_list() -> None:
        visible_rows = rows[: shown_count["value"]]
        with ui.column().classes("dashboard-history-list w-full"):
            for row in visible_rows:
                card = ui.card().classes("card dashboard-history-card w-full")
                with card:
                    with ui.row().classes("dashboard-history-head w-full items-start"):
                        with ui.column().classes("gap-1 min-w-0 flex-1"):
                            ui.label(str(row.get("display_url", "-"))).classes("dashboard-history-url")
                            ui.label(str(row.get("display_date", "-"))).classes("dashboard-history-date")
                        with ui.column().classes("items-end shrink-0"):
                            ui.label(str(row.get("priority_level", "-"))).classes(
                                f"dashboard-priority-badge { _priority_badge_class(str(row.get('priority_level', '-'))) }"
                            )
                            ui.label(str(row.get("issue_summary", "-"))).classes("dashboard-history-issues")
                    with ui.column().classes("dashboard-score-stack w-full"):
                        _render_score_bar(label="AI", score=_safe_int(row.get("aio_score")), fill_class="dashboard-score-ai")
                        _render_score_bar(label="SEO", score=_safe_int(row.get("seo_score")), fill_class="dashboard-score-seo")
                    if _safe_text(row.get("top_action")) not in {"", "-"}:
                        ui.label(str(row.get("top_action"))).classes("dashboard-history-action whitespace-pre-line")
                    with ui.row().classes("w-full justify-end items-center mt-1"):
                        ui.button(
                            "結果を開く",
                            icon="arrow_forward",
                            on_click=lambda _event=None, run_id=row["id"]: on_open_run(run_id),
                            color=None,
                        ).props("flat no-caps").classes("dashboard-history-open action-link")

        if shown_count["value"] < len(rows):
            ui.button(f"さらに表示 ({len(rows) - shown_count['value']}件)", on_click=_show_more, color=None).props("no-caps").classes("secondary-btn w-full").style(
                "background: rgba(255, 251, 246, 0.96); color: #7A3A16; border: 1px solid rgba(122, 98, 83, 0.18);"
            )
        elif len(rows) > 8:
            ui.button("上位だけに戻す", on_click=_collapse, color=None).props("no-caps").classes("secondary-btn w-full").style(
                "background: rgba(255, 251, 246, 0.96); color: #7A3A16; border: 1px solid rgba(122, 98, 83, 0.18);"
            )

        ui.label("「結果を開く」から保存済みワークスペースへ進めます。").classes("dashboard-history-mobile-hint")

    def _show_more() -> None:
        shown_count["value"] = min(shown_count["value"] + 8, len(rows))
        mobile_list.refresh()

    def _collapse() -> None:
        shown_count["value"] = min(8, len(rows))
        mobile_list.refresh()

    mobile_list()


def render_history_table(rows: List[Dict[str, Any]], *, on_open_run: Callable[[int], None]) -> None:
    if not rows:
        with ui.card().classes("card p-5 w-full"):
            ui.label("最近の分析はまだありません").classes("card-title")
            ui.label("URLを入れて分析すると、ここから再表示できます。").classes("card-sub")
        return

    columns = [
        {"name": "analyzed_at", "label": "分析日時 (JST)", "field": "analyzed_at", "align": "left"},
        {"name": "display_url", "label": "URL", "field": "display_url", "align": "left"},
        {"name": "score_summary", "label": "スコア", "field": "score_summary", "align": "center"},
        {"name": "priority_level", "label": "優先度", "field": "priority_level", "align": "center"},
        {"name": "top_action", "label": "最優先アクション", "field": "top_action", "align": "left"},
        {"name": "open", "label": "操作", "field": "open", "align": "center"},
    ]

    with ui.card().classes("card p-5 w-full"):
        with ui.row().classes("items-center justify-between w-full gap-3 flex-wrap"):
            with ui.column().classes("gap-1"):
                ui.label("最近の分析").classes("card-title")
                ui.label("各行の「結果を開く」から評価を表示できます。").classes("card-hint text-sm")
            ui.label(f"{len(rows)}件").classes("fixed-chip")

        with ui.element("div").classes("dashboard-history-desktop w-full mt-3"):
            table = ui.table(columns=columns, rows=rows, row_key="id", pagination=20).classes("w-full text-sm")
            table.props("flat bordered separator=cell wrap-cells")
            table.add_slot(
                "body-cell-open",
                '''
                <q-td :props="props">
                  <q-btn
                    flat no-caps
                    label="結果を開く"
                    icon-right="arrow_forward"
                    class="dashboard-history-open action-link"
                    :aria-label="`${props.row.display_url} の結果を開く`"
                    @click="$parent.$emit('open_run', props.row.id)"
                  />
                </q-td>
                ''',
            )
            table.on("open_run", lambda event: on_open_run(int(event.args)))

        with ui.element("div").classes("dashboard-history-mobile w-full mt-3"):
            _render_history_mobile_list(rows, on_open_run=on_open_run)
