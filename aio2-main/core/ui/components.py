# -*- coding: utf-8 -*-
"""UIコンポーネント"""

from typing import Dict, List, Optional

from .design_system import resolve_color, resolve_icon


def safe_text(value: str, limit: int = 80) -> str:
    """テキストを適切な長さに丸める"""
    if not value:
        return ""
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)] + "..."


def normalize_item(item: Dict) -> Dict:
    """項目データをUI用に正規化"""
    return {
        "icon": item.get("icon") or "info",
        "text": item.get("text") or "",
        "subtext": item.get("subtext") or item.get("hint") or "",
        "required": bool(item.get("required", False)),
    }


def build_status_card_data(
    title: str,
    status: str,
    status_color: str,
    items: List[Dict],
    summary: Optional[str] = None,
) -> Dict:
    """ステータスカード用の表示データを構築"""
    normalized_items = [normalize_item(item) for item in items]
    return {
        "title": title,
        "status": status,
        "status_color": resolve_color(status_color),
        "status_icon": resolve_icon(status_color),
        "items": normalized_items,
        "summary": summary or "",
    }


def create_status_card(title: str, status: str, status_color: str, items: List[Dict], summary: str = ""):
    """ステータスカードコンポーネント"""
    from nicegui import ui

    card_data = build_status_card_data(title, status, status_color, items, summary)

    with ui.card().classes("card p-4 w-full status-card"):
        ui.label(card_data["title"]).classes("card-title")
        ui.label(card_data["status"]).classes("card-sub font-bold").style(
            f"color: {card_data['status_color']}"
        )
        if card_data["summary"]:
            ui.label(card_data["summary"]).classes("card-hint")

        for item in card_data["items"]:
            icon = item["icon"]
            text = item["text"]
            ui.label(f"{icon} {safe_text(text, 120)}").classes("card-sub")
            if item["subtext"]:
                ui.label(f"  {safe_text(item['subtext'], 140)}").classes("card-hint")

    return card_data
