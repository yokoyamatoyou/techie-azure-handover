# -*- coding: utf-8 -*-
"""FAQ・ヘルプ表示用ユーティリティ"""

from typing import Dict, List, Tuple


def build_faq_pairs(faq_items: List[Dict]) -> List[Tuple[str, str]]:
    """FAQの質問と回答をペア化"""
    pairs = []
    for item in faq_items:
        question = item.get("question", "")
        answer = item.get("answer", "")
        if question and answer:
            pairs.append((question, answer))
    return pairs


def render_faq_section(faq_items: List[Dict], title: str = "よくある質問"):
    """FAQセクションを描画"""
    from nicegui import ui

    pairs = build_faq_pairs(faq_items)
    if not pairs:
        return

    ui.label(title).classes("card-title")
    for question, answer in pairs:
        with ui.expansion(question, icon="help").classes("w-full"):
            ui.label(answer).classes("card-sub")
