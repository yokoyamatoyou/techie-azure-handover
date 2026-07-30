# -*- coding: utf-8 -*-
"""Industry tab rendering logic."""

from typing import Any, Dict

from nicegui import ui


def _format_industry_value(value: Any) -> str:
    text = str(value or "").strip()
    replacements = {
        "自動判定": "",
        "未検出": "判定なし",
        "指定なし": "判定なし",
        "カスタム/その他": "その他 / 独自設定",
    }
    return replacements.get(text, text) or "判定なし"


def _format_industry_source(value: Any) -> str:
    text = str(value or "").strip()
    if text == "ユーザー入力（自動判定で確認済み）":
        return "入力内容を優先（自動推定でも一致）"
    if text.startswith("ユーザー入力（自動判定:"):
        return text.replace("ユーザー入力（自動判定:", "入力内容を優先（自動推定:", 1)
    if text.startswith("自動判定（信頼度:"):
        return text.replace("自動判定", "自動推定", 1).replace("信頼度", "確からしさ", 1)
    return text or "補足なし"


def render_industry_tab(industry: Dict[str, Any], results: Dict[str, Any]) -> None:
    """Render the industry tab."""
    industry_label = _format_industry_value(industry.get("primary")) 
    if industry_label == "判定なし":
        industry_label = _format_industry_value(industry.get("auto_primary"))
    ui.label("業界判定").classes("card-title")
    ui.label(f"業界の見立て: {industry_label}").classes("card-sub")
    ui.label(f"信頼度: {industry.get('confidence', 0):.1f}%").classes("card-sub")
    ui.label(f"判断のもと: {_format_industry_source(industry.get('source'))}").classes("card-sub")

    regulatory_check = results.get("regulatory_check")
    if not regulatory_check:
        return

    ui.separator()
    ui.label("規制コンプライアンスチェック").classes("card-title")
    applicable = ", ".join(regulatory_check.get("applicable_regulations", []))
    ui.label(f"適用規制: {applicable}").classes("card-sub")
    passed = regulatory_check.get("passed", True)
    high_count = regulatory_check.get("high_risk_count", 0)
    medium_count = regulatory_check.get("medium_risk_count", 0)
    low_count = regulatory_check.get("low_risk_count", 0)
    if passed:
        ui.label("✓ チェック通過（重大な問題なし）").classes("card-sub text-green-600")
    else:
        ui.label("⚠ 要確認（修正推奨）").classes("card-sub text-red-600")
    ui.label(f"検出数: 高リスク {high_count} / 中リスク {medium_count} / 低リスク {low_count}").classes(
        "card-hint text-xs"
    )

    warnings = regulatory_check.get("warnings", [])
    if warnings:
        with ui.expansion('検出された表現（クリックで展開）', icon='warning').classes('w-full'):
            for w in warnings[:8]:
                severity_class = (
                    "text-red-600"
                    if w.get("severity") == "high"
                    else ("text-orange-500" if w.get("severity") == "medium" else "text-gray-600")
                )
                ui.label(f"「{w.get('word')}」- {w.get('category')}").classes(f"card-sub {severity_class}")
                ui.label(f"  理由: {w.get('reason')}").classes("card-hint text-xs")
                ui.label(f"  推奨: {w.get('suggestion')}").classes("card-hint text-xs text-blue-600")
