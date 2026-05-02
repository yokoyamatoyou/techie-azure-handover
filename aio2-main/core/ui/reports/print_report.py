# -*- coding: utf-8 -*-
"""Print-friendly report rendering."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Callable

from nicegui import ui


def render_print_report(
    state: Any,
    results: Dict[str, Any],
    integrated: Dict[str, Any],
    trim_text: Callable[[str, int], str],
    format_reason_text_ui: Callable[[str], str],
    calc_citation_index: Callable[[Dict[str, Any]], float],
) -> None:
    """Render print-friendly version of the analysis report."""
    ui.add_head_html(
        """
        <style>
          body { background: #ffffff !important; }
          .print-shell { max-width: 900px; margin: 32px auto; font-family: 'Sora', 'Noto Sans JP', sans-serif; }
          .print-title { font-size: 26px; font-weight: 700; color: #0B1420; }
          .print-sub { color: #5F6B7A; font-size: 12px; }
          .print-card { border: 1px solid #E2E8F0; border-radius: 14px; padding: 16px 18px; margin-top: 14px; }
          .print-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }
          .print-metric { background: #F4F7F9; border-radius: 12px; padding: 12px 14px; }
          .print-metric strong { display: block; font-size: 18px; }
          .print-actions { margin-top: 16px; }
          @media print {
            .print-actions { display: none; }
            body { margin: 0; }
          }
        </style>
        """
    )

    with ui.column().classes("print-shell"):
        if not results:
            ui.label("分析結果がありません。").classes("card-sub")
            return

        seo_results = results.get("seo_results", {})
        aio_results = results.get("aio_results", {})

        aio_actions = aio_results.get("immediate_actions", [])
        if aio_actions:
            with ui.column().classes("print-card"):
                ui.label("即時改善アクション（1〜2週間）").classes("card-title")
                for action in aio_actions[:6]:
                    ui.label(f"- {action.get('action', 'N/A')}").classes("card-sub")
                    method = action.get("method", "")
                    if method:
                        ui.label(format_reason_text_ui(trim_text(method, 240))).classes("card-sub whitespace-pre-line")

        citation = results.get("citation_insights", {})
        deep_recs = results.get("deep_recommendations", {})

        ui.label("SEO/AIO Intelligence Report").classes("print-title")
        ui.label(f"URL: {results.get('url', 'N/A')}").classes("print-sub")
        ui.label(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}").classes("print-sub")

        with ui.row().classes("print-actions"):
            ui.button("印刷", on_click=lambda: ui.run_javascript("window.print()")).classes("primary-btn")

        with ui.column().classes("print-card"):
            ui.label("スコア概要").classes("card-title")
            with ui.row().classes("print-grid"):
                for label, key in (
                    ("SEOスコア", "seo_score"),
                    ("AIOスコア", "aio_score"),
                    ("統合スコア", "integrated_score"),
                ):
                    with ui.column().classes("print-metric"):
                        ui.label(label).classes("card-sub")
                        ui.label(f"{integrated.get(key, 0):.0f}/100").classes("card-title")

        platform_meta = results.get("platform", {})
        platform_guidance = results.get("platform_guidance", {})
        if platform_meta or platform_guidance:
            effective_platform = platform_guidance.get("label") or platform_meta.get("effective") or "未検出"
            selected_platform = platform_meta.get("selected") or "未選択"
            detected_platforms = ", ".join(platform_meta.get("detected", []) or []) or "未検出"
            with ui.column().classes("print-card"):
                ui.label("プラットフォーム別ガイド").classes("card-title")
                ui.label(
                    f"選択: {selected_platform} / 検出: {detected_platforms} / 適用: {effective_platform}"
                ).classes("card-sub")
                business_steps = platform_guidance.get("business_steps", [])
                technical_steps = platform_guidance.get("technical_steps", [])
                help_links = platform_guidance.get("help_links", [])
                if business_steps:
                    ui.label("非エンジニア向け（操作ガイド）").classes("card-title")
                    for step in business_steps[:3]:
                        ui.label(f"- {trim_text(step, 300)}").classes("card-sub")
                if technical_steps:
                    ui.label("エンジニア向け（実装ガイド）").classes("card-title")
                    for step in technical_steps[:3]:
                        ui.label(f"- {trim_text(step, 300)}").classes("card-sub")
                if help_links:
                    ui.label("公式ヘルプ").classes("card-title")
                    for link in help_links[:3]:
                        ui.label(f"- {link.get('label', '公式ヘルプ')}: {link.get('url', '')}").classes("card-sub")

        ai_crawler = aio_results.get("ai_crawler", {})
        if ai_crawler:
            with ui.column().classes("print-card"):
                ui.label("AIクローラー適合性").classes("card-title")
                ui.label(f"応答速度: {ai_crawler.get('response_time_ms', 0):.0f} ms").classes("card-sub")
                ui.label(f"レンダリング推定: {ai_crawler.get('render_note', 'N/A')}").classes("card-sub")

        if citation:
            with ui.column().classes("print-card"):
                index = calc_citation_index(citation)
                ui.label("引用準備指数（Citation Readiness Index）").classes("card-title")
                if index is not None:
                    ui.label(f"{index:.0f}/100").classes("card-sub")
                ui.label("引用されやすさ（優先順）").classes("card-title")
                if citation.get("note"):
                    ui.label(citation.get("note", "")).classes("card-sub")
                for axis in citation.get("axes", []):
                    label = axis.get("label", axis.get("axis"))
                    ui.label(f"{label}: {axis.get('quality_score', 0):.0f}/100").classes("card-sub")

                phrases = citation.get("phrases", [])
                if phrases:
                    ui.label("引用候補フレーズ").classes("card-title")
                    for item in phrases[:3]:
                        ui.label(f"「{item.get('phrase', '')}」").classes("card-sub")
                        ui.label(f"理由: {item.get('reason', '')}").classes("card-sub")
                        template = item.get("template", "")
                        if template:
                            ui.label(f"改善テンプレ（Template）: {template}").classes("card-sub")

                ui.label("引用されやすさ最優先の実装ガイド").classes("card-title")
                for item in (
                    "ページ冒頭に結論→要約の短いブロックを配置",
                    "FAQまたは比較表で要点を構造化",
                    "数値・一次ソースの根拠を明示（出典リンク/調査元）",
                    "定義・用語を明確化し、引用しやすい短文を用意",
                    "更新日・監修者などの信頼情報を明示",
                ):
                    ui.label(f"・{item}").classes("card-sub")

                content_plan = citation.get("content_plan", {}) or {}
                sections = content_plan.get("sections", []) or []
                summary = content_plan.get("summary", "")
                if sections or summary:
                    ui.label("ページ専用のコンテンツ追加案").classes("card-title")
                    if summary:
                        ui.label(summary).classes("card-sub")
                    for section in sections[:4]:
                        title = section.get("title", "追加セクション")
                        fmt = section.get("format", "")
                        ui.label(f"{title}（{fmt}）").classes("card-sub")
                        purpose = section.get("purpose", "")
                        if purpose:
                            ui.label(f"目的: {purpose}").classes("card-sub")
                        for bullet in (section.get("bullets", []) or [])[:3]:
                            ui.label(f"・{bullet}").classes("card-sub")
                else:
                    ui.label("深掘り解析を有効にすると、ページ専用の追加案が表示されます。").classes("card-sub")

                comp = state.competitor_results
                if comp:
                    comp_citation = comp.get("citation_insights", {})
                    comp_axes = {a.get("axis"): a for a in comp_citation.get("axes", []) if a.get("axis")}
                    own_axes = {a.get("axis"): a for a in citation.get("axes", []) if a.get("axis")}
                    axis_keys = list(own_axes.keys() or comp_axes.keys())
                    if axis_keys:
                        ui.label("引用されやすさ（軸別差分）").classes("card-title")
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

        if deep_recs:
            business_recs = deep_recs.get("business", [])
            technical_recs = deep_recs.get("technical", [])
            if business_recs:
                with ui.column().classes("print-card"):
                    ui.label("非エンジニア向け提案").classes("card-title")
                    for rec in business_recs[:3]:
                        ui.label(f"- {rec.get('title', '提案')}").classes("card-sub")
                        ui.label(rec.get("recommended_action", "")[:160]).classes("card-sub")
            if technical_recs:
                with ui.column().classes("print-card"):
                    ui.label("エンジニア向け提案").classes("card-title")
                    for rec in technical_recs[:3]:
                        ui.label(f"- {rec.get('title', '提案')}").classes("card-sub")
                        ui.label(rec.get("implementation", "")[:160]).classes("card-sub")

        warnings_list = results.get("warnings", [])
        if warnings_list:
            with ui.column().classes("print-card"):
                ui.label("注意事項").classes("card-title")
                for item in warnings_list[:10]:
                    ui.label(f"- {item}").classes("card-sub")

        summary = results.get("summary", {})
        if summary.get("improvements"):
            with ui.column().classes("print-card"):
                ui.label("推奨改善ポイント").classes("card-title")
                for item in summary.get("improvements", [])[:10]:
                    ui.label(f"- {item}").classes("card-sub")

        with ui.column().classes("print-card"):
            ui.label("基本SEO情報").classes("card-title")
            basics = seo_results.get("basics", {})
            ui.label(f"タイトル: {basics.get('title', 'N/A')}").classes("card-sub")
            ui.label(f"説明文: {basics.get('meta_description', 'N/A')}").classes("card-sub")
            seo_actions = seo_results.get("immediate_actions", [])
            if seo_actions:
                with ui.column().classes("print-card"):
                    ui.label("SEO 即時改善アクション（プラットフォーム別）").classes("card-title")
                    for action in seo_actions[:6]:
                        ui.label(f"- {action.get('action', 'N/A')}").classes("card-sub")
                        method = action.get("method", "")
                        if method:
                            ui.label(format_reason_text_ui(trim_text(method, 240))).classes("card-sub whitespace-pre-line")

        graph_paths = []
        seo_graph = results.get("seo_graph_path")
        aio_graph = results.get("aio_graph_path")
        if seo_graph and Path(seo_graph).exists():
            graph_paths.append(("SEOグラフ", seo_graph))
        if aio_graph and Path(aio_graph).exists():
            graph_paths.append(("AIOグラフ", aio_graph))
        if graph_paths:
            with ui.column().classes("print-card"):
                ui.label("簡易グラフ").classes("card-title")
                for label, path in graph_paths:
                    ui.label(label).classes("card-sub")
                    ui.image(path).classes("w-full").style("max-height: 320px; object-fit: contain;")
