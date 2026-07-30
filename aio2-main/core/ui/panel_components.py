# -*- coding: utf-8 -*-
"""Shared NiceGUI panel drawing helpers."""

from __future__ import annotations

import difflib
import html
import re
from typing import Any, Tuple

from nicegui import ui

_DIFF_MAX_CHARS = 220

def _extract_row_id_from_event_args(args: Any) -> int:
    if isinstance(args, dict):
        if "row" in args:
            return int((args.get("row") or {}).get("id", 0) or 0)
        return int(args.get("id", 0) or 0)
    if isinstance(args, list) and args:
        for item in args:
            if isinstance(item, dict):
                if "row" in item:
                    row_id = int((item.get("row") or {}).get("id", 0) or 0)
                else:
                    row_id = int(item.get("id", 0) or 0)
                if row_id:
                    return row_id
    return 0

def _render_generated_card(
    *,
    title: str = "",
    body: str = "",
    metric: str = "",
    label: str = "分析結果",
    body_classes: str = "generated-body",
    card_classes: str = "card p-4 w-full generated-block",
) -> None:
    with ui.card().classes(card_classes):
        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
            ui.label(label).classes("generated-chip")
            if metric:
                ui.label(metric).classes("generated-metric")
        if title:
            ui.label(title).classes("generated-title")
        if body:
            ui.label(body).classes(body_classes)

def _render_expandable_generated_card(
    *,
    title: str = "",
    body: str = "",
    metric: str = "",
    label: str = "分析結果",
    card_classes: str = "card p-4 w-full generated-block",
    body_expand_label: str = "全文を見る",
) -> None:
    clean_body = str(body or "").strip()
    with ui.card().classes(card_classes):
        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
            ui.label(label).classes("generated-chip")
            if metric:
                ui.label(metric).classes("generated-metric")
        if title:
            ui.label(title).classes("generated-title whitespace-pre-line")
        if clean_body:
            if len(clean_body) <= 120:
                ui.label(clean_body).classes("generated-body whitespace-pre-line")
            else:
                body_exp = ui.expansion(body_expand_label, icon="unfold_more", value=False).classes("w-full mt-2")
                with body_exp:
                    ui.label(clean_body).classes("generated-body whitespace-pre-line")

def _render_workspace_header(
    *,
    title: str,
    description: str,
    mode_label: str = "分析結果",
) -> None:
    with ui.row().classes("items-start justify-between w-full gap-3 flex-wrap"):
        with ui.column().classes("gap-1 min-w-[220px]"):
            ui.label(title).classes("card-title")
            ui.label(description).classes("card-hint text-sm")
        ui.label(mode_label).classes("generated-chip")

def _diff_html(before: str, after: str) -> Tuple[str, str]:
    """Generate minimal diff markup for before/after strings."""
    before = before or ""
    after = after or ""
    # Limit to keep UI fast
    if len(before) > _DIFF_MAX_CHARS:
        before = before[: _DIFF_MAX_CHARS] + "…"
    if len(after) > _DIFF_MAX_CHARS:
        after = after[: _DIFF_MAX_CHARS] + "…"

    a = list(before)
    b = list(after)
    matcher = difflib.SequenceMatcher(a=a, b=b)
    before_parts = []
    after_parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            segment = html.escape("".join(a[i1:i2]))
            before_parts.append(segment)
            after_parts.append(segment)
        elif tag == "delete":
            segment = html.escape("".join(a[i1:i2]))
            if segment:
                before_parts.append(f"<span class='diff-del'>{segment}</span>")
        elif tag == "insert":
            segment = html.escape("".join(b[j1:j2]))
            if segment:
                after_parts.append(f"<span class='diff-add'>{segment}</span>")
        elif tag == "replace":
            seg_before = html.escape("".join(a[i1:i2]))
            seg_after = html.escape("".join(b[j1:j2]))
            if seg_before:
                before_parts.append(f"<span class='diff-del'>{seg_before}</span>")
            if seg_after:
                after_parts.append(f"<span class='diff-add'>{seg_after}</span>")
    return "".join(before_parts), "".join(after_parts)

def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))

def _display_snapshot_label(label: str) -> str:
    normalized = str(label or "").strip()
    mapping = {
        "今回のURL": "このページ向け",
        "対象ページで確認": "このページ向け",
        "このページ向け": "このページ向け",
        "表示アドバイス": "表現・見せ方",
        "分析メモ": "補足メモ",
        "参考": "参考情報",
    }
    return mapping.get(normalized, normalized)

def _compact_copy(value: Any, limit: int = 110) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    shortened = text[:limit]
    for delimiter in ("。", "、", ".", " "):
        cut = shortened.rfind(delimiter)
        if cut >= int(limit * 0.65):
            return shortened[: cut + (1 if delimiter != " " else 0)].strip() + "…"
    return shortened.rstrip() + "…"

def _headline_metric_hint(label: str) -> str:
    normalized = str(label or "").strip()
    hints = {
        "AI認識": "AI検索や要約で、このページの要点が拾われやすいかの目安です。",
        "SEO": "検索結果で見つけられやすいかの目安です。",
        "総合優先度": "点数ではなく、スコアと課題数から見た着手の急ぎ度です。",
    }
    return hints.get(normalized, "")

def _render_snapshot_cards(
    items: list[dict],
    *,
    empty_text: str,
    compact: bool = False,
    show_title: bool = True,
    show_label: bool = True,
    detail_limit: int | None = None,
) -> None:
    if not items:
        ui.label(empty_text).classes("card-sub text-gray-500")
        return
    for item in items:
        title = str(item.get("title", "") or "").strip()
        detail = str(item.get("detail", "") or "").strip()
        label = str(item.get("label", "") or "").strip()
        metric = _display_snapshot_label(label) if label and show_label else ""
        long_detail = bool(detail and detail_limit and len(detail) > detail_limit)
        if long_detail:
            _render_expandable_generated_card(
                title=title if show_title else "",
                body=detail,
                metric=metric,
                label="確認ポイント",
                body_expand_label="クリックで全文表示",
            )
            continue
        _render_generated_card(
            title=title if show_title else "",
            body=detail,
            metric=metric,
            label="確認ポイント",
            body_classes="generated-body whitespace-pre-line" if (detail and not compact) else "generated-body",
        )

def _render_compact_note_rows(items: list[dict], *, empty_text: str) -> None:
    if not items:
        ui.label(empty_text).classes("card-sub text-gray-500")
        return
    with ui.element("div").classes("compact-note-list"):
        for item in items:
            with ui.element("div").classes("compact-note-row"):
                detail = str(item.get("detail") or item.get("title") or "").strip()
                if detail:
                    ui.label(detail).classes("card-sub whitespace-pre-line")

def _priority_badge_classes(priority_level: str) -> str:
    if priority_level == "高":
        return "bg-red-50 text-red-700"
    if priority_level == "中":
        return "bg-amber-50 text-amber-700"
    return "bg-emerald-50 text-emerald-700"

def _normalize_status_key(status: Any) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"fail", "要対応"}:
        return "fail"
    if normalized in {"warn", "warning", "注意", "要確認"}:
        return "warn"
    if normalized in {"pass", "ok", "通過", "問題なし"}:
        return "pass"
    if normalized in {"reference", "info", "参考"}:
        return "reference"
    if normalized in {"unknown", "unverified", "unchecked", "未確認", "未判定"}:
        return "unverified"
    if normalized in {"not_applicable", "not-applicable", "n/a", "na", "対象外"}:
        return "not_applicable"
    if normalized in {"error", "failed", "取得エラー", "検査エラー"}:
        return "error"
    if normalized in {"blocked", "ブロック"}:
        return "blocked"
    return "unverified"

def _status_label(status: Any) -> str:
    return {
        "pass": "通過",
        "warn": "注意",
        "fail": "要対応",
        "reference": "参考",
        "unverified": "未確認",
        "not_applicable": "対象外",
        "blocked": "取得制限",
        "error": "取得エラー",
    }.get(_normalize_status_key(status), "未確認")

def _status_badge_classes(status: str) -> str:
    mapping = {
        "pass": "bg-emerald-50 text-emerald-700",
        "warn": "bg-amber-50 text-amber-700",
        "fail": "bg-red-50 text-red-700",
        "reference": "bg-slate-100 text-slate-600",
        "unverified": "bg-slate-100 text-slate-700",
        "not_applicable": "bg-slate-100 text-slate-600",
        "blocked": "bg-amber-50 text-amber-700",
        "error": "bg-red-50 text-red-700",
    }
    return mapping.get(_normalize_status_key(status), "bg-slate-100 text-slate-600")

