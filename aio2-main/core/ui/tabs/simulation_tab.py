# -*- coding: utf-8 -*-
"""Citation snippets tab rendering logic (AI予測は削除)."""

import json
from typing import Any, Dict, Optional

from nicegui import ui


def render_simulation_tab(results: Dict[str, Any], state: Optional[object] = None) -> None:
    """Render the citation snippets tab."""
    _ = state
    citation_snippets = results.get("citation_snippets", {})

    ui.label("引用スニペット候補").classes("card-title")
    ui.label(
        "AIに引用されやすい文章候補です。コピーしてそのまま使えます。"
        "スコアが高いほど、AIの回答にそのまま引用されやすい書き方になっています。"
    ).classes("card-hint text-sm")

    snippets = citation_snippets.get("snippets", [])
    if snippets:
        for i, snippet in enumerate(snippets, 1):
            score = snippet.get("score", 0)
            score_color = "text-green-600" if score >= 50 else ("text-yellow-600" if score >= 30 else "text-gray-500")

            with ui.card().classes(f"card p-4 w-full mt-3 animate-slide-up delay-{min(i*100, 500)}").style("border-left: 3px solid #12A594"):
                ui.label(f"候補 {i} (スコア: {score:.0f})").classes(f"card-sub font-bold {score_color}")
                text = snippet.get("text", "")
                ui.label(f'"{text}"').classes("card-sub mt-2 italic")
                ui.label(f"理由: {snippet.get('reason', '')}").classes("card-hint text-xs mt-1")

                with ui.row().classes("gap-2 mt-3 items-center"):
                    async def handle_copy(t=text, btn=None):
                        ui.notify(f"コピーしました: {t[:30]}...", type='positive', icon='content_copy')
                        original_text = btn.text
                        btn.set_text("✓ コピー完了")
                        btn.classes(replace="text-green-600 font-bold")
                        await ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(t)})")
                        await ui.sleep(2.0)
                        btn.set_text(original_text)
                        btn.classes(remove="text-green-600 font-bold")

                    copy_btn = ui.button("引用文をコピー").classes("text-xs font-medium px-3 py-1")
                    copy_btn.props("flat dense outline")
                    copy_btn.on('click', lambda e, b=copy_btn: handle_copy(text, b))

                    ui.label(f"スコア: {score:.0f}").classes(f"text-xs {score_color} font-bold px-2 py-0.5 bg-slate-50 rounded")

        speakable_markup = citation_snippets.get("speakable_markup", "")
        if speakable_markup:
            with ui.expansion("JSON-LD speakable マークアップ", icon="code").classes("w-full mt-4"):
                ui.label("以下のコードをHTMLの<head>内に貼り付けてください。").classes("card-hint text-xs mb-2")
                ui.code(speakable_markup, language="json").classes("text-xs")

                async def copy_speakable_code(markup=speakable_markup, btn=None):
                    ui.notify("マークアップをコピーしました！", type='positive', icon='content_copy')
                    await ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(markup)})")
                    if btn:
                        btn.set_text("✓ コピー完了")
                        await ui.sleep(2.0)
                        btn.set_text("📋 コードをコピー")

                with ui.row().classes("mt-3 gap-2"):
                    cp_btn = ui.button("コードをコピー").classes("text-sm font-medium")
                    cp_btn.props("flat dense outline color=primary")
                    cp_btn.on('click', lambda e, b=cp_btn: copy_speakable_code(speakable_markup, b))
                    ui.label("→ <head>タグ内に貼り付け").classes("card-hint text-xs self-center")
    else:
        ui.label("引用スニペット候補が見つかりませんでした。").classes("card-hint text-gray-500")
