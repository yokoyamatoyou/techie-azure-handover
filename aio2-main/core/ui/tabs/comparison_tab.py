# -*- coding: utf-8 -*-
"""Comparison tab rendering logic."""

from typing import Any, Callable, Dict

from nicegui import ui


def render_comparison_tab(
    state: Any,
    results: Dict[str, Any],
    integrated: Dict[str, Any],
    format_reason_text_ui: Callable[[str], str],
) -> None:
    """Render competitor comparison tab."""
    comp = state.competitor_results
    if not comp:
        ui.label("競合比較データがありません。").classes("card-sub")
        return

    comp_integrated = comp.get("integrated_results", {})

    ui.label("競合比較（要約）").classes("card-title")
    ui.label(f"競合URL: {comp.get('url') or '未設定'}").classes("card-sub")

    overall_diff = float(integrated.get("integrated_score", 0)) - float(comp_integrated.get("integrated_score", 0))
    if overall_diff > 0:
        ui.label(f"結論: 統合スコアで自社が競合より{overall_diff:.0f}点優勢です。").classes("card-sub text-self font-bold")
    elif overall_diff < 0:
        ui.label(f"結論: 統合スコアで競合が自社より{abs(overall_diff):.0f}点優勢です。").classes("card-sub text-competitive font-bold")
    else:
        ui.label("結論: 統合スコアは自社と競合でほぼ互角です。").classes("card-sub font-bold")

    for label, key in (
        ("SEOスコア", "seo_score"),
        ("AIOスコア", "aio_score"),
        ("統合スコア", "integrated_score"),
    ):
        own = float(integrated.get(key, 0))
        comp_val = float(comp_integrated.get(key, 0))
        diff = own - comp_val
        ui.label(f"{label}: 自社 {own:.0f} / 競合 {comp_val:.0f} (差分 {diff:+.0f})").classes("card-sub")

    own_aio = results.get("aio_results", {})
    comp_aio = comp.get("aio_results", {})
    own_struct = own_aio.get("structure_results", {})
    comp_struct = comp_aio.get("structure_results", {})

    if own_struct or comp_struct:
        ui.separator()
        with ui.expansion("信頼情報・画像対応の詳細", icon="unfold_more", value=False).classes("w-full mt-2"):
            own_eeat = own_struct.get("eeat", {})
            comp_eeat = comp_struct.get("eeat", {})
            if own_eeat or comp_eeat:
                own_auth = "あり" if own_eeat.get("has_author") else "なし"
                comp_auth = "あり" if comp_eeat.get("has_author") else "なし"
                auth_color = "text-self" if own_eeat.get("has_author") else "text-gray-500"
                ui.label(f"著者情報 (Author): 自社 {own_auth} vs 競合 {comp_auth}").classes(f"card-sub {auth_color}")

                own_org = "あり" if own_eeat.get("has_organization") else "なし"
                comp_org = "あり" if comp_eeat.get("has_organization") else "なし"
                org_color = "text-self" if own_eeat.get("has_organization") else "text-gray-500"
                ui.label(f"運営組織 (Org): 自社 {own_org} vs 競合 {comp_org}").classes(f"card-sub {org_color}")

            own_multi = own_struct.get("multimodal", {})
            comp_multi = comp_struct.get("multimodal", {})
            if own_multi or comp_multi:
                own_alt = own_multi.get("alt_quality_score", 0.0) * 100
                comp_alt = comp_multi.get("alt_quality_score", 0.0) * 100
                alt_diff = own_alt - comp_alt
                ui.label(f"画像Alt品質: 自社 {own_alt:.0f}% vs 競合 {comp_alt:.0f}% (差分 {alt_diff:+.0f}%)").classes(
                    "card-sub"
                )

    own_citation = results.get("citation_insights", {})
    comp_citation = comp.get("citation_insights", {})

    own_axes = {a.get("axis"): a for a in own_citation.get("axes", []) if a.get("axis")}
    comp_axes = {a.get("axis"): a for a in comp_citation.get("axes", []) if a.get("axis")}
    axis_keys = list(own_axes.keys() or comp_axes.keys())

    if axis_keys:
        ui.label("引用されやすさ（軸別差分）").classes("card-title")
        wins = sum(
            1
            for k in axis_keys
            if float(own_axes.get(k, {}).get("quality_score", 0)) >= float(comp_axes.get(k, {}).get("quality_score", 0))
        )
        ui.label(f"{len(axis_keys)}項目中 {wins}項目で自社が競合以上のスコアです。").classes("card-hint")

        for key in axis_keys:
            own_axis = own_axes.get(key, {})
            comp_axis = comp_axes.get(key, {})
            label = own_axis.get("label") or comp_axis.get("label") or key
            own_score = float(own_axis.get("quality_score", 0))
            comp_score = float(comp_axis.get("quality_score", 0))
            diff = own_score - comp_score
            ui.label(f"{label}: 自社 {own_score:.0f} / 競合 {comp_score:.0f} (差分 {diff:+.0f})").classes("card-sub")

            if diff < 0:
                recs = own_axis.get("recommendations", []) or []
                if recs:
                    for rec in recs[:2]:
                        action = rec.get("action", "改善アクション")
                        example = rec.get("example", "")
                        impact = rec.get("impact", "")
                        ui.label(f"・{action}").classes("card-sub")
                        if example:
                            ui.label(f"  例: {example}").classes("card-sub")
                        if impact:
                            ui.label(f"  期待効果: {impact}").classes("card-sub")
    else:
        ui.label("引用されやすさの比較は深掘り解析を有効にしてください。").classes("card-sub")

    advice_data = state.competitor_action_advice
    if advice_data and advice_data.get("success"):
        ui.separator()
        ui.label("🎯 競合に勝つためのアクション").classes("card-title")

        summary = advice_data.get("summary", "")
        if summary:
            ui.label(summary).classes("card-hint text-sm italic")

        actions = advice_data.get("actions", [])
        if actions:
            for i, action in enumerate(actions, 1):
                priority = action.get("priority", i)
                area = action.get("area", "")
                action_text = action.get("action", "")
                impact = action.get("impact", "")
                difficulty = action.get("difficulty", "中")

                diff_color = "text-green-600" if difficulty == "低" else ("text-yellow-600" if difficulty == "中" else "text-red-600")
                delay_class = f"delay-{min(i * 100, 500)}"

                with ui.card().classes(f"card p-4 w-full mt-3 animate-slide-up {delay_class}").style("border-left: 3px solid #12A594"):
                    with ui.row().classes("items-center justify-between"):
                        ui.label(f"優先度 {priority}: {area}").classes("card-sub font-bold")
                        ui.badge(f"難易度: {difficulty}").classes(f"{diff_color} px-2 py-1 rounded-full text-xs")

                    ui.label(format_reason_text_ui(action_text)).classes("card-sub mt-2 whitespace-pre-line")

                    if impact:
                        ui.label(format_reason_text_ui(f"期待効果: {impact}")).classes("card-hint text-xs mt-1 text-green-600 whitespace-pre-line")
        else:
            ui.label("競合との差分が少ないため、現状維持で問題ありません。").classes("card-hint")
