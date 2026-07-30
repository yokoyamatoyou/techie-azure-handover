# -*- coding: utf-8 -*-
"""UI panels split from nicegui_app."""

from datetime import datetime
from typing import Any, Dict, Optional
import re

from nicegui import ui
from core.application.analysis_run_service import _build_priority_actions, _build_ui_snapshot
from core.application.time_display import format_jst_datetime
from core.ui.panel_components import (
    _clamp_score,
    _diff_html,
    _extract_row_id_from_event_args,
    _render_expandable_generated_card,
    _render_generated_card,
    _render_workspace_header,
)
from core.ui.saved_workspace import (
    _provider_check_status_label,
    _provider_has_actionable_details,
    _describe_google_controls,
    _build_summary_priority_note,
    _safe_score_value,
    _score_status_meta,
    _build_saved_run_overall_message,
    _build_evaluation_axis_cards,
    _reason_label_hint,
    _saved_run_reason_title,
    _saved_run_reason_metric,
    _render_saved_run_overview,
    _render_saved_run_next_actions,
    _render_saved_run_improvement_tab,
    _saved_run_has_improvement_tab,
    _saved_run_has_writing_tab,
    _saved_run_has_implementation_tab,
    _saved_run_has_engineer_tab,
    _saved_run_has_comparison_tab,
    _render_saved_run_evaluation,
    _build_workspace_improvement_map,
    _render_workspace_improvement_map,
    _build_provider_focus_summary,
    _build_implementation_stop_message,
    _filter_actionable_google_controls,
    _status_sort_key,
    _render_status_note_card,
    _render_engineer_summary_card,
    _split_task_actions,
    _prioritize_search_intent_secondary_actions,
    _render_task_action_card,
    _short_reason_text,
    _intent_confidence_label,
    _intent_note_values,
    _intent_role_overview_items,
    _render_saved_run_intent_role_overview,
    _render_workspace_summary_tab,
    _render_workspace_task_tab,
    _render_workspace_writing_tab,
    _render_workspace_implementation_tab,
    _render_workspace_engineer_tab,
    _render_workspace_comparison_tab,
    _build_workspace_tab_plan,
    _render_workspace_tabs,
    render_saved_run_workspace,
)
from core.ui.panel_context import PanelContext, build_panel_context


_panel_context: Optional[PanelContext] = None
_DIFF_MAX_CHARS = 220


def bind_panel_dependencies(*, state, trim_text, format_reason_text_ui, calc_citation_index, aio_score_labels, aio_score_help) -> None:
    set_panel_context(
        build_panel_context(
            state=state,
            trim_text=trim_text,
            format_reason_text_ui=format_reason_text_ui,
            calc_citation_index=calc_citation_index,
            aio_score_labels=aio_score_labels,
            aio_score_help=aio_score_help,
        )
    )


def set_panel_context(context: PanelContext) -> None:
    global _panel_context
    _panel_context = context


def _require_panel_context() -> PanelContext:
    if _panel_context is None:
        raise RuntimeError("panel dependencies are not bound: context")
    return _panel_context


def _require_state():
    return _require_panel_context().state


def _require_trim_text():
    return _require_panel_context().trim_text


def _require_format_reason_text_ui():
    return _require_panel_context().format_reason_text_ui


def _require_calc_citation_index():
    return _require_panel_context().calc_citation_index


def _require_aio_score_labels() -> Dict[str, str]:
    return _require_panel_context().aio_score_labels


def _require_aio_score_help() -> Dict[str, str]:
    return _require_panel_context().aio_score_help




def _title_with_hint(
    title: str,
    hint: str,
    *,
    title_classes: str = "card-title",
    row_classes: str = "items-center gap-2",
) -> None:
    with ui.row().classes(row_classes):
        ui.label(title).classes(title_classes)
        ui.icon("info_outline").classes("text-sm text-[#9B7A60] opacity-70 cursor-help").tooltip(hint)










def _infer_kpi(action_text: str) -> str:
    text = action_text or ""
    if any(k in text for k in ["タイトル", "メタ", "OGP"]):
        return "CTR"
    if any(k in text for k in ["速度", "LCP", "INP", "CLS"]):
        return "表示速度"
    if any(k in text for k in ["FAQ", "構造化", "JSON-LD", "引用"]):
        return "AI引用率"
    if any(k in text for k in ["返品", "配送", "送料", "支払い", "特商法"]):
        return "CVR/信頼性"
    return "検索流入/品質"


def _format_context_value(value: Any, *, missing_label: str = "未設定") -> str:
    """Normalize internal status labels for non-engineer-facing UI text."""
    text = str(value or "").strip()
    replacements = {
        "自動判定": "おまかせ",
        "未選択": missing_label,
        "未検出": "判定なし",
        "指定なし": "判定なし",
        "カスタム/その他": "その他 / 独自設定",
        "その他": "その他 / 独自設定",
    }
    if not text:
        return missing_label
    return replacements.get(text, text)


def _format_industry_source(source: Any) -> str:
    """Normalize industry source copy for non-engineers."""
    text = str(source or "").strip()
    if not text:
        return ""
    if text == "ユーザー入力（自動判定で確認済み）":
        return "入力内容を優先（自動推定でも一致）"
    if text.startswith("ユーザー入力（自動判定:"):
        return text.replace("ユーザー入力（自動判定:", "入力内容を優先（自動推定:", 1)
    if text == "ユーザー入力":
        return "入力内容を使用"
    if text.startswith("自動判定（信頼度:"):
        return text.replace("自動判定", "自動推定", 1).replace("信頼度", "確からしさ", 1)
    if text == "判定困難":
        return "判定が難しい状態"
    return text


def _build_decision_actions(
    *,
    deep_recs: Dict[str, Any],
    aio_results: Dict[str, Any],
    seo_results: Dict[str, Any],
    summary: Dict[str, Any],
    business_goal: str = "自動判定",
    results: Optional[Dict[str, Any]] = None,
) -> list[dict]:
    if results:
        priority_actions = _build_priority_actions(results)
        if priority_actions:
            return priority_actions[:3]

    items: list[dict] = []
    business_recs = deep_recs.get("business", []) or []
    technical_recs = deep_recs.get("technical", []) or []
    for rec in business_recs[:2]:
        action_text = rec.get("recommended_action", "")
        items.append({
            "title": rec.get("title", "改善提案"),
            "action": action_text,
            "role": "運用/マーケ",
            "effort": "30〜90分",
            "kpi": _infer_kpi(action_text),
            "impact": rec.get("expected_impact", ""),
        })
    if technical_recs:
        rec = technical_recs[0]
        action_text = rec.get("implementation", "") or rec.get("title", "")
        items.append({
            "title": rec.get("title", "技術改善"),
            "action": action_text,
            "role": "開発",
            "effort": "0.5〜1日",
            "kpi": _infer_kpi(action_text),
            "impact": rec.get("expected_impact", ""),
        })
    if len(items) < 3:
        for action in (aio_results.get("immediate_actions", []) or [])[:3]:
            action_text = action.get("action", "") if isinstance(action, dict) else str(action)
            method = action.get("method", "") if isinstance(action, dict) else ""
            items.append({
                "title": action_text or "即時改善",
                "action": method or action_text,
                "role": "運用/マーケ",
                "effort": "30〜90分",
                "kpi": _infer_kpi(action_text),
                "impact": action.get("expected_impact", "") if isinstance(action, dict) else "",
            })
            if len(items) >= 3:
                break
    if len(items) < 3:
        for action in (seo_results.get("immediate_actions", []) or [])[:3]:
            action_text = action.get("action", "") if isinstance(action, dict) else str(action)
            method = action.get("method", "") if isinstance(action, dict) else ""
            items.append({
                "title": action_text or "SEO改善",
                "action": method or action_text,
                "role": "運用/マーケ",
                "effort": "30〜90分",
                "kpi": _infer_kpi(action_text),
                "impact": action.get("expected_impact", "") if isinstance(action, dict) else "",
            })
            if len(items) >= 3:
                break
    if len(items) < 3:
        for imp in (summary.get("improvements", []) or [])[:3]:
            items.append({
                "title": "改善ポイント",
                "action": imp,
                "role": "運用/マーケ",
                "effort": "30〜90分",
                "kpi": _infer_kpi(imp),
                "impact": "",
            })
    items = _sort_decision_actions_by_goal(items, business_goal)
    return items[:3]


def _sort_decision_actions_by_goal(actions: list[dict], business_goal: str) -> list[dict]:
    if not actions or not business_goal or business_goal == "自動判定":
        return list(actions or [])

    goal_keywords = {
        "オーガニック流入増加（SEO優先）": ["seo", "キーワード", "ctr", "検索流入", "構造化", "schema"],
        "AI検索での引用増加（GEO/AIO優先）": ["aio", "geo", "eeat", "e-e-a-t", "tldr", "引用", "ai引用", "統計", "entity"],
        "CV率・リード獲得（CTA改善優先）": ["cta", "cv", "lead", "リード", "問い合わせ", "cvr", "faq", "信頼", "trust"],
        "ブランド認知・指名検索強化": ["ブランド", "指名", "entity", "eeat", "schema", "認知", "trust"],
        "サイト技術健全性（エンジニア優先）": ["cwv", "security", "技術", "performance", "速度", "accessibility", "crawl", "robots"],
    }
    keys = goal_keywords.get(business_goal, [])
    if not keys:
        return list(actions or [])

    ranked: list[tuple[int, int, dict]] = []
    for idx, action in enumerate(actions):
        text = " ".join(
            str(action.get(field, ""))
            for field in ("title", "action", "kpi", "impact", "role")
        ).lower()
        rank = 999
        for key_idx, key in enumerate(keys):
            if key.lower() in text:
                rank = key_idx
                break
        ranked.append((rank, idx, action))
    ranked.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in ranked]


def _render_output_gate_notice(results: Dict[str, Any]) -> bool:
    gate = (results or {}).get("output_gate", {}) or {}
    status = gate.get("status")
    if not status:
        return False

    strict = gate.get("strict_check", {}) or {}
    consumer = gate.get("consumer_check", {}) or {}
    strict_label = strict.get("decision") or strict.get("risk_level") or "-"
    consumer_label = consumer.get("decision") or consumer.get("risk_level") or "-"

    if status == "block":
        with ui.column().classes("callout w-full"):
            ui.label("通知").classes("notice-chip")
            ui.label("一部の分析結果を非表示にしています").classes("card-title")
            ui.label(f"消費者庁視点: {strict_label} / 一般消費者視点: {consumer_label}").classes("card-sub")
            reason = gate.get("reason")
            if reason:
                ui.label(reason).classes("card-sub")
            reasons = gate.get("reasons", []) or []
            for item in reasons[:3]:
                ui.label(f"・{item}").classes("card-hint")
            ui.label("詳細な分析結果はゲートにより非表示です。").classes("card-hint")
        return True

    if status == "warn":
        with ui.column().classes("callout w-full"):
            ui.label("注意").classes("notice-chip")
            ui.label("表現の見直し候補があります").classes("card-title")
            ui.label(f"消費者庁視点: {strict_label} / 一般消費者視点: {consumer_label}").classes("card-sub")
            reason = gate.get("reason")
            if reason:
                ui.label(reason).classes("card-hint")
    return False




def _extract_social_channels(html_text: str) -> list[str]:
    if not html_text:
        return []
    patterns = [
        ("X", r"(?:https?:)?//(?:www\.)?(?:x\.com|twitter\.com)/"),
        ("Instagram", r"(?:https?:)?//(?:www\.)?instagram\.com/"),
        ("Facebook", r"(?:https?:)?//(?:www\.)?facebook\.com/"),
        ("YouTube", r"(?:https?:)?//(?:www\.)?(?:youtube\.com|youtu\.be)/"),
        ("LinkedIn", r"(?:https?:)?//(?:www\.)?linkedin\.com/"),
        ("TikTok", r"(?:https?:)?//(?:www\.)?tiktok\.com/"),
        ("LINE", r"(?:https?:)?//(?:www\.)?(?:line\.me|lin\.ee)/"),
    ]
    channels = []
    for label, pattern in patterns:
        if re.search(pattern, html_text, re.IGNORECASE):
            channels.append(label)
    return channels


def _has_any_keyword(text: str, keywords: list[str]) -> bool:
    if not text:
        return False
    lower_text = text.lower()
    for keyword in keywords:
        if keyword.lower() in lower_text:
            return True
    return False


def _build_transparency_signals(results: Dict[str, Any]) -> tuple[list[Dict[str, Any]], list[str]]:
    html_text = (results or {}).get("html") or ""
    business_type = ((results or {}).get("business_type_detection") or {}).get("primary_type", "") or ""
    industry = ((results or {}).get("final_industry") or {}).get("primary", "") or ""
    effective_type = ((results or {}).get("url_type") or {}).get("effective", "") or ""

    is_ec = "EC" in effective_type or business_type == "ec_retail"
    is_food = ("飲食" in industry) or ("フード" in industry)
    regulated = (
        business_type in {"healthcare", "cosmetics", "food_supplement", "finance"}
        or any(k in industry for k in ["医療", "化粧品", "健康食品", "サプリ", "金融", "保険"])
    )
    content_heavy = business_type in {"healthcare", "cosmetics", "food_supplement", "finance", "education", "affiliate_media"}
    needs_supervisor = regulated and not is_food
    needs_human_capital = business_type in {"corporate", "recruitment"} and not is_ec
    show_sns = business_type not in {"finance"} or is_ec

    social_channels = _extract_social_channels(html_text)

    signals: list[Dict[str, Any]] = [
        {
            "key": "company_info",
            "label": "会社情報（会社概要/運営者）",
            "present": _has_any_keyword(html_text, ["会社概要", "企業情報", "運営会社", "事業者情報", "about us", "company profile"]),
            "weight": 3,
        },
        {
            "key": "contact",
            "label": "連絡先（問い合わせ導線）",
            "present": _has_any_keyword(html_text, ["お問い合わせ", "contact", "電話", "メール", "support"]),
            "weight": 3,
        },
        {
            "key": "privacy",
            "label": "プライバシーポリシー",
            "present": _has_any_keyword(html_text, ["プライバシー", "privacy policy", "個人情報"]),
            "weight": 2,
        },
        {
            "key": "terms",
            "label": "利用規約/免責",
            "present": _has_any_keyword(html_text, ["利用規約", "terms", "免責", "disclaimer"]),
            "weight": 2,
        },
    ]

    if content_heavy or regulated:
        signals.append(
            {
                "key": "update_date",
                "label": "更新日/公開日の明示",
                "present": bool(re.search(r"(更新日|最終更新|公開日|改訂日|\d{4}[./-]\d{1,2}[./-]\d{1,2})", html_text)),
                "weight": 2,
            }
        )
        signals.append(
            {
                "key": "sources",
                "label": "根拠/出典の明示",
                "present": _has_any_keyword(
                    html_text,
                    ["出典", "参考", "引用", "厚生労働省", "消費者庁", "統計", "research", "source"],
                ),
                "weight": 2,
            }
        )

    if needs_supervisor:
        signals.append(
            {
                "key": "supervisor",
                "label": "監修者・責任者情報",
                "present": _has_any_keyword(
                    html_text,
                    ["監修", "監修者", "医師", "薬剤師", "管理栄養士", "弁護士", "公認会計士", "author"],
                ),
                "weight": 2,
            }
        )

    if needs_human_capital:
        signals.append(
            {
                "key": "human_capital",
                "label": "人的資本・組織情報",
                "present": _has_any_keyword(
                    html_text,
                    ["人的資本", "従業員", "ダイバーシティ", "育休", "離職率", "エンゲージメント", "human capital"],
                ),
                "weight": 1,
            }
        )

    if show_sns:
        signals.append(
            {
                "key": "sns",
                "label": "公式SNS導線",
                "present": bool(social_channels),
                "weight": 1,
                "detail": " / ".join(social_channels) if social_channels else "",
            }
        )

    return signals, social_channels


def _score_transparency(signals: list[Dict[str, Any]]) -> int:
    total = sum(int(item.get("weight", 1)) for item in signals) or 1
    gained = sum(int(item.get("weight", 1)) for item in signals if item.get("present"))
    return _clamp_score((gained / total) * 100)


def _calculate_legal_clarity_score(results: Dict[str, Any], legal_checks: Dict[str, Any]) -> int:
    score = 100
    is_ec = "EC" in str(((results or {}).get("url_type") or {}).get("effective", ""))

    premiums_status = ((legal_checks.get("premiums_labeling", {}) or {}).get("formatted", {}) or {}).get("status", "")
    if "要対応" in str(premiums_status):
        score -= 25
    elif "要確認" in str(premiums_status):
        score -= 12

    stealth_status = ((legal_checks.get("stealth_marketing", {}) or {}).get("formatted", {}) or {}).get("status", "")
    if "要対応" in str(stealth_status):
        score -= 20
    elif "要確認" in str(stealth_status):
        score -= 10

    commercial_status = ((legal_checks.get("commercial_transaction", {}) or {}).get("formatted", {}) or {}).get("status", "")
    if is_ec:
        if "要対応" in str(commercial_status):
            score -= 30
        elif "一部未記載" in str(commercial_status):
            score -= 18

    lawyer_report = ((legal_checks.get("consumer_protection", {}) or {}).get("lawyer_report", []) or [])
    high_count = len([item for item in lawyer_report if item.get("severity") == "high"])
    warning_count = len([item for item in lawyer_report if item.get("severity") == "warning"])
    score -= min(24, high_count * 6)
    score -= min(12, warning_count * 3)

    gate_status = ((results or {}).get("output_gate", {}) or {}).get("status", "")
    if gate_status == "block":
        score -= 18
    elif gate_status == "warn":
        score -= 8

    return _clamp_score(score)


def _build_management_actions(
    *,
    results: Dict[str, Any],
    integrated: Dict[str, Any],
    citation_index: Optional[float],
    legal_checks: Dict[str, Any],
    signals: list[Dict[str, Any]],
    social_channels: list[str],
) -> Dict[str, list[str]]:
    aio_actions: list[str] = []
    legal_actions: list[str] = []

    aio_score = float(integrated.get("aio_score", 0) or 0)
    if aio_score < 70:
        aio_actions.append("結論先出し・FAQ・比較表を優先し、AIが要点を抜き出しやすい構成にします。")
    if citation_index is not None and citation_index < 65:
        aio_actions.append("本文に短い定義文と根拠付きの数値文を追加し、引用されやすい文型を増やします。")

    signal_map = {item.get("key"): item for item in signals}
    if signal_map.get("update_date") and not signal_map["update_date"].get("present"):
        aio_actions.append("各重要ページに更新日を明記し、情報の鮮度が伝わる状態にします。")
    if signal_map.get("sources") and not signal_map["sources"].get("present"):
        aio_actions.append("一次情報の出典リンクを明記し、記述の裏付けを可視化します。")
    if signal_map.get("sns") and not signal_map["sns"].get("present"):
        aio_actions.append("公式SNSリンクをフッター等に設置し、検索以外の導線で自社サイト流入を増やします。")
    elif signal_map.get("sns") and social_channels:
        aio_actions.append(f"既存SNS導線（{' / '.join(social_channels[:3])}）を主要ページから辿れる位置に統一します。")

    gate_status = ((results or {}).get("output_gate", {}) or {}).get("status", "")
    if gate_status == "block":
        legal_actions.append("表示前ゲートで停止判定です。誤解される表現を先に修正してから再評価します。")
    elif gate_status == "warn":
        legal_actions.append("表示前ゲートで注意判定です。誇張・断定表現を優先して言い換えます。")

    premiums_status = ((legal_checks.get("premiums_labeling", {}) or {}).get("formatted", {}) or {}).get("status", "")
    if "要対応" in str(premiums_status) or "要確認" in str(premiums_status):
        legal_actions.append("No.1/最上級/価格比較の表現は、根拠の明示か安全な表現への修正を行います。")

    stealth_status = ((legal_checks.get("stealth_marketing", {}) or {}).get("formatted", {}) or {}).get("status", "")
    if "要対応" in str(stealth_status) or "要確認" in str(stealth_status):
        legal_actions.append("広告・PR・提供の関係は記事冒頭で明示し、誤認されない表示に統一します。")

    is_ec = "EC" in str(((results or {}).get("url_type") or {}).get("effective", ""))
    commercial = (legal_checks.get("commercial_transaction", {}) or {}).get("formatted", {}) or {}
    if is_ec and ("要対応" in str(commercial.get("status", "")) or "一部未記載" in str(commercial.get("status", ""))):
        legal_actions.append("特商法の未記載項目（販売者情報/返品/支払等）を優先して埋めます。")

    if signal_map.get("company_info") and not signal_map["company_info"].get("present"):
        legal_actions.append("会社情報ページへの導線を明示し、運営主体への誤解を防ぎます。")
    if signal_map.get("contact") and not signal_map["contact"].get("present"):
        legal_actions.append("問い合わせ手段（フォーム/メール/電話）を必ず1つ以上明示します。")

    if not aio_actions:
        aio_actions.append("AI検索向けの観点では大きな欠落はありません。更新日と出典の運用ルールを維持します。")
    if not legal_actions:
        legal_actions.append("表現リスクの観点では重大な欠落はありません。新規ページ公開時の確認運用を継続します。")

    return {
        "aio": aio_actions[:4],
        "legal": legal_actions[:4],
    }


def _render_management_brief(
    *,
    state: Any,
    results: Dict[str, Any],
    integrated: Dict[str, Any],
    citation: Dict[str, Any],
    legal_checks: Dict[str, Any],
) -> None:
    calc_citation_index = _require_calc_citation_index()
    citation_index = calc_citation_index(citation or {})
    aio_score = float(integrated.get("aio_score", 0) or 0)
    aio_readiness = _clamp_score(aio_score * 0.75 + (float(citation_index) * 0.25 if citation_index is not None else aio_score * 0.25))
    legal_score = _calculate_legal_clarity_score(results, legal_checks)
    signals, social_channels = _build_transparency_signals(results)
    trust_score = _score_transparency(signals)
    management_score = _clamp_score(aio_readiness * 0.45 + legal_score * 0.35 + trust_score * 0.20)
    actions = _build_management_actions(
        results=results,
        integrated=integrated,
        citation_index=citation_index,
        legal_checks=legal_checks,
        signals=signals,
        social_channels=social_channels,
    )

    _title_with_hint("結論サマリ", "分析結果から整理した結論だけを表示します。前提や技術メモは『内部診断』で確認できます。")

    with ui.row().classes("w-full section-grid"):
        metrics = [
            ("全体判断", management_score, "全体"),
            ("AI検索", aio_readiness, "AI検索"),
            ("SEO", float(integrated.get("seo_score", 0) or 0), "SEO"),
        ]
        for label, value, tag in metrics:
            with ui.column().classes("metric"):
                ui.label(label).classes("metric-label")
                ui.label(f"{value}/100").classes("metric-value")
                ui.label(tag).classes("card-hint text-xs")

    if management_score >= 80:
        ui.label("判定: 守りと攻めのバランスは良好です。運用で維持してください。").classes("card-sub text-green-700")
    elif management_score >= 60:
        ui.label("判定: 実務運用は可能です。誤解防止の表記を先に整えると安定します。").classes("card-sub text-amber-700")
    else:
        ui.label("判定: 表現と信頼情報の整理を優先してください。公開前レビューを推奨します。").classes("card-sub text-red-700")

    missing_signals = [str(item.get("label")) for item in signals if not item.get("present")]
    if missing_signals:
        ui.label("信頼情報の不足: " + " / ".join(missing_signals[:3])).classes("card-hint")
    else:
        ui.label("信頼情報の基礎表示は大きく崩れていません。").classes("card-hint text-green-700")

    ui.separator()
    ui.label("先に整えること").classes("card-title")

    ui.label("AI検索で見つけられやすくする観点").classes("card-sub font-bold")
    for item in actions.get("aio", [])[:3]:
        ui.label(f"・{item}").classes("card-sub")

    ui.label("表現リスクを減らす観点").classes("card-sub font-bold mt-2")
    for item in actions.get("legal", [])[:3]:
        ui.label(f"・{item}").classes("card-sub")


def _build_context_note_rows(
    *,
    results: Dict[str, Any],
    aio_results: Dict[str, Any],
    integrated: Dict[str, Any],
    summary: Dict[str, Any],
    previous_run: Optional[Dict[str, Any]] = None,
) -> tuple[list[str], list[str]]:
    url_type_meta = results.get("url_type", {}) or {}
    final_industry = results.get("final_industry", {}) or {}
    crawl_strategy = results.get("crawl_strategy") or {}
    schema_validation = aio_results.get("schema_validation") or {}
    content_gap = aio_results.get("content_schema_gap") or {}
    internal_link_summary = results.get("internal_link_summary") or {}
    link_health_report = results.get("link_health_report") or {}
    is_ec = results.get("is_ec")
    ec_reason = results.get("ec_detection_reason") or ""

    premise_rows: list[str] = []
    diagnostic_rows: list[str] = []

    if url_type_meta:
        selected_type = _format_context_value(url_type_meta.get("selected"), missing_label="未設定")
        detected_type = _format_context_value(url_type_meta.get("detected"), missing_label="判定なし")
        effective_type = _format_context_value(
            url_type_meta.get("effective") or url_type_meta.get("detected"),
            missing_label="判定なし",
        )
        premise_rows.append(
            f"サイト種別: {effective_type} / 入力: {selected_type} / 自動推定: {detected_type}"
        )

    if final_industry:
        industry_label = _format_context_value(final_industry.get("primary"), missing_label="判定なし")
        if industry_label in {"おまかせ", "判定なし"}:
            industry_label = _format_context_value(final_industry.get("auto_primary"), missing_label="判定なし")
        source = _format_industry_source(final_industry.get("source"))
        confidence = final_industry.get("confidence")
        if source and confidence is not None:
            premise_rows.append(
                f"業界見立て: {industry_label} / 判断のもと: {source} / 確からしさ: {confidence:.0f}%"
            )
        elif source:
            premise_rows.append(f"業界見立て: {industry_label} / 判断のもと: {source}")
        else:
            premise_rows.append(f"業界見立て: {industry_label}")

    if is_ec is not None:
        label = "ECサイト" if is_ec else "非ECサイト"
        if ec_reason:
            premise_rows.append(f"EC判定: {label} / 理由: {ec_reason}")
        else:
            premise_rows.append(f"EC判定: {label}")

    if previous_run:
        current_seo = int(integrated.get("seo_score", 0) or 0)
        current_aio = int(integrated.get("aio_score", 0) or 0)
        current_issue_count = int(summary.get("issue_count", 0) or 0)

        prev_seo = int(previous_run.get("seo_score", 0) or 0)
        prev_aio = int(previous_run.get("aio_score", 0) or 0)
        prev_issue_count = int(previous_run.get("total_issues", 0) or 0)
        analyzed_at = format_jst_datetime(previous_run.get("analyzed_at")) or "前回"

        diagnostic_rows.append(
            "前回比較: "
            f"SEO {current_seo - prev_seo:+d} / "
            f"AI検索 {current_aio - prev_aio:+d} / "
            f"課題数 {current_issue_count - prev_issue_count:+d} "
            f"(比較対象: ID {previous_run.get('id')} / {analyzed_at})"
        )

    if isinstance(crawl_strategy, dict) and crawl_strategy:
        reason = crawl_strategy.get("reason") or crawl_strategy.get("description") or ""
        depth = crawl_strategy.get("depth")
        link_count = crawl_strategy.get("link_count", results.get("links_found"))
        crawl_bits = []
        if reason:
            crawl_bits.append(f"確認範囲: {reason}")
        if link_count is not None:
            crawl_bits.append(f"リンク数: {link_count}")
        if depth is not None:
            crawl_bits.append(f"深さ: {depth}")
        if crawl_bits:
            diagnostic_rows.append(" / ".join(crawl_bits))

    if isinstance(schema_validation, dict) and schema_validation:
        found = schema_validation.get("found_types") or []
        missing = schema_validation.get("missing_recommended") or []
        score = schema_validation.get("score")
        schema_row = f"構造化データ: {len(found)}種確認 / 未設定 {len(missing)}"
        if score is not None:
            schema_row += f" / スコア {score}"
        diagnostic_rows.append(schema_row)

    if isinstance(content_gap, dict) and content_gap:
        potential = content_gap.get("aio_improvement_potential")
        gap_count = len(content_gap.get("gaps") or [])
        if potential is not None or gap_count:
            diagnostic_rows.append(
                f"AI検索向けの改善余地: {potential or 0}/100 / 不足項目 {gap_count}件"
            )

    if isinstance(internal_link_summary, dict) and internal_link_summary:
        orphan_count = internal_link_summary.get("orphan_count", 0)
        total_pages = internal_link_summary.get("total_pages", 0)
        diagnostic_rows.append(
            f"内部リンク: 総ページ {total_pages} / 孤立ページ {orphan_count}"
        )
    if isinstance(link_health_report, dict) and link_health_report:
        audited = int(link_health_report.get("audited_target_count", 0) or 0)
        broken = int(link_health_report.get("broken_target_count", 0) or 0)
        redirected = int(link_health_report.get("redirected_target_count", 0) or 0)
        canonical = int(link_health_report.get("canonical_mismatch_count", 0) or 0)
        noindex = int(link_health_report.get("noindex_target_count", 0) or 0)
        if audited:
            diagnostic_rows.append(
                f"リンク先監査: {audited}件確認 / エラー {broken} / リダイレクト {redirected} / canonical不整合 {canonical} / noindex {noindex}"
            )

    return premise_rows, diagnostic_rows


def _render_result_context_notes(
    *,
    state: Any,
    results: Dict[str, Any],
    aio_results: Dict[str, Any],
    integrated: Dict[str, Any],
    summary: Dict[str, Any],
    previous_run: Optional[Dict[str, Any]] = None,
) -> None:
    premise_rows, diagnostic_rows = _build_context_note_rows(
        results=results,
        aio_results=aio_results,
        integrated=integrated,
        summary=summary,
        previous_run=previous_run,
    )
    if not premise_rows and not diagnostic_rows:
        return

    _title_with_hint(
        "内部診断",
        "分析の前提、前回比較、技術メモです。意思決定に必要な要点は上段で完結しています。",
        title_classes="card-sub font-bold",
    )
    if premise_rows:
        ui.label("分析前提").classes("card-sub font-bold")
        for row in premise_rows:
            ui.label(row).classes("card-hint")
    if diagnostic_rows:
        if premise_rows:
            ui.separator()
        ui.label("比較・技術メモ").classes("card-sub font-bold")
        for row in diagnostic_rows:
            ui.label(row).classes("card-hint")


def _build_url_specific_highlights(
    *,
    results: Dict[str, Any],
    integrated: Dict[str, Any],
    seo_results: Dict[str, Any],
    aio_results: Dict[str, Any],
    summary: Dict[str, Any],
    max_items: int = 4,
) -> list[dict]:
    """Create URL-specific highlights for the summary/workbench view."""
    url_type = _format_context_value((results.get("url_type") or {}).get("effective"), missing_label="判定なし")
    industry = _format_context_value((results.get("final_industry") or {}).get("primary"), missing_label="判定なし")
    platform = _format_context_value(
        ((results.get("platform_guidance") or {}).get("label") or "")
        or ((results.get("platform") or {}).get("effective") or ""),
        missing_label="判定なし",
    )
    business_goal = _format_context_value(integrated.get("business_goal"), missing_label="未設定")

    seo_score = float(integrated.get("seo_score", 0) or 0)
    aio_score = float(integrated.get("aio_score", 0) or 0)
    geo_score = float(integrated.get("geo_score", 0) or 0)
    legal_score = float(integrated.get("legal_score", 0) or 0)

    basics = seo_results.get("basics", {}) or {}
    structure = seo_results.get("structure", {}) or {}
    headings = structure.get("headings", {}) or {}
    h1_count = sum(1 for heading in headings if str(heading).startswith("h1"))
    title_len = len(str(basics.get("title", "") or ""))
    desc_len = len(str(basics.get("meta_description", "") or ""))

    faq_items = ((results.get("faq_detection") or {}).get("items") or [])
    schema_types = ((results.get("schema_existing") or {}).get("types") or [])
    eeat_score = float((aio_results.get("scores", {}).get("eeat") or {}).get("score", 0) or 0)

    items: list[dict] = []
    if geo_score < 45:
        items.append(
            {
                "title": "AI検索で伝わりにくい状態です",
                "body": "要点のまとめ、数値の根拠、運営者情報の3点が不足している可能性があります。",
                "metric": f"検索 {seo_score:.0f} / AI検索 {aio_score:.0f}",
            }
        )
    elif aio_score + 10 < seo_score:
        items.append(
            {
                "title": "検索より AI検索 の整備が遅れています",
                "body": "検索向けの基礎はありますが、AIが拾いやすい要約やQ&Aの整備が足りていません。",
                "metric": f"検索 {seo_score:.0f} / AI検索 {aio_score:.0f}",
            }
        )
    elif seo_score + 10 < aio_score:
        items.append(
            {
                "title": "AI検索は比較的強く、検索の詰めが次です",
                "body": "要点整理は進んでいるため、タイトル・見出し・説明文を整えると流入改善につながりやすい状態です。",
                "metric": f"検索 {seo_score:.0f} / AI検索 {aio_score:.0f}",
            }
        )

    if legal_score and legal_score < 60:
        items.append(
            {
                "title": "信頼表示の先回りが必要",
                "body": "集客施策より前に、特商法・景表法・問い合わせ導線・運営情報の見せ方を先に整えた方が安全です。",
                "metric": f"表示アドバイス {legal_score:.0f}",
            }
        )
    elif eeat_score < 4.0:
        items.append(
            {
                "title": "著者・運営者の信頼情報が弱い",
                "body": "本文内の監修者・資格・一次情報の提示が薄く、YMYL領域ではAI評価の足を引っ張る要因になります。",
                "metric": f"信頼情報 {eeat_score:.1f} / 10",
            }
        )

    page_hygiene = []
    if title_len and not 28 <= title_len <= 36:
        page_hygiene.append(f"タイトル{title_len}文字")
    if desc_len and not 80 <= desc_len <= 120:
        page_hygiene.append(f"説明文{desc_len}文字")
    if h1_count != 1:
        page_hygiene.append(f"H1が{h1_count}個")
    if page_hygiene:
        items.append(
            {
                "title": "検索の基礎設定に軽い崩れがあります",
                "body": " / ".join(page_hygiene) + "。細かな設定差ですが、検索結果での見え方と理解しやすさに影響します。",
                "metric": "URL固有のHTML検出結果",
            }
        )

    if faq_items:
        items.append(
            {
                "title": "既存FAQが見つかっています",
                "body": f"ページ内で {len(faq_items)} 件のFAQを検出しました。AI検索向けの回答素材として使えるため、整合性だけ確認すれば活かせます。",
                "metric": "FAQはURL固有の実データ",
            }
        )
    else:
        schema_note = "構造化データあり" if schema_types else "構造化データなし"
        items.append(
            {
                "title": "FAQや説明用の定型ブロックが不足気味です",
                "body": "既存FAQが見つからないため、説明・比較・Q&Aの塊を追加するとAI検索でも人間の理解でも有利になります。",
                "metric": schema_note,
            }
        )

    improvements = summary.get("improvements", []) or []
    if improvements:
        items.append(
            {
                "title": "このURLで最初に効く改善",
                "body": str(improvements[0]),
                "metric": "分析結果から自動抽出",
            }
        )

    return items[:max_items]


def _render_url_specific_highlights(
    *,
    results: Dict[str, Any],
    integrated: Dict[str, Any],
    seo_results: Dict[str, Any],
    aio_results: Dict[str, Any],
    summary: Dict[str, Any],
    lead_text: str = "ここは今回のURLから実際に見つかった結果だけをまとめています。",
    max_items: int = 4,
) -> None:
    items = _build_url_specific_highlights(
        results=results,
        integrated=integrated,
        seo_results=seo_results,
        aio_results=aio_results,
        summary=summary,
        max_items=max_items,
    )
    if not items:
        return

    _title_with_hint("現状", lead_text)
    with ui.row().classes("section-grid w-full"):
        for item in items:
            _render_generated_card(
                title=str(item.get("title", "所見")),
                body=str(item.get("body", "") or ""),
                metric=str(item.get("metric", "") or ""),
            )


def _build_provider_summary_rows(aio_results: Dict[str, Any]) -> list[dict]:
    provider_readiness = aio_results.get("provider_readiness") or aio_results.get("details", {}).get("provider_readiness", {}) or {}
    rows = []
    for key, label, note in (
        ("google", "Google", "Googlebot / noindex / snippet"),
        ("openai_search", "OpenAI Search", "OAI-SearchBot"),
        ("perplexity", "Perplexity", "PerplexityBot"),
        ("claude_search", "Claude Search", "Claude-SearchBot"),
    ):
        provider = provider_readiness.get(key, {}) or {}
        status = str(provider.get("status") or "")
        if status == "pass":
            badge, tone = "通過", "text-green-600"
        elif status == "warn":
            badge, tone = "注意", "text-amber-600"
        elif status == "fail":
            badge, tone = "要対応", "text-red-600"
        else:
            badge, tone = "未判定", "text-gray-500"
        rows.append({
            "label": label,
            "status": badge,
            "tone": tone,
            "note": note,
        })
    return rows


def _render_provider_summary_strip(aio_results: Dict[str, Any]) -> None:
    rows = _build_provider_summary_rows(aio_results)
    if not rows:
        return
    _title_with_hint("各AIサービスの公開条件", "公開されやすい状態かどうかを一覧で見ています。細かい条件は展開して確認できます。")
    with ui.row().classes("w-full gap-2 flex-wrap"):
        for row in rows:
            ui.label(f"{row['label']} {row['status']}").classes(f"hero-chip {row['tone']}")


@ui.refreshable

def results_panel() -> None:
    state = _require_state()
    trim_text = _require_trim_text()
    format_reason_text_ui = _require_format_reason_text_ui()
    """BOX2: スコア診断結果（採点理由を含む）"""

    if not state.results:

        ui.label("分析結果はまだありません。").classes("card-sub")

        return

    results = state.results
    state.result_expansions = []

    integrated = results.get("integrated_results", {})
    seo_results = results.get("seo_results", {})
    aio_results = results.get("aio_results", {})

    summary = results.get("summary", {})

    warnings_list = results.get("warnings", [])
    deep_recs = results.get("deep_recommendations", {}) or {}

    if _render_output_gate_notice(results):
        return

    # スコアは経営サマリー内で表示（重複を避ける）
    decision_actions = _build_decision_actions(
        deep_recs=deep_recs,
        aio_results=aio_results,
        seo_results=seo_results,
        summary=summary,
        business_goal=integrated.get("business_goal", "自動判定"),
        results=results,
    )

    from core.ui.reports.executive_summary import render_executive_summary
    render_executive_summary(results, integrated, summary, decision_actions, format_reason_text_ui)

    if warnings_list:
        with ui.column().classes("callout w-full"):
            ui.label("注意・通知").classes("notice-chip")
            ui.label(f"先に確認したい注意点が {len(warnings_list)} 件あります").classes("card-title")
            visible_warnings = warnings_list[:3]
            for item in visible_warnings:
                ui.label(f"- {item}").classes("card-sub")
            remaining = max(len(warnings_list) - len(visible_warnings), 0)
            if remaining:
                ui.label(f"ほか {remaining} 件は詳細側で確認してください。").classes("card-hint")
    _render_url_specific_highlights(
        results=results,
        integrated=integrated,
        seo_results=seo_results,
        aio_results=aio_results,
        summary=summary,
        max_items=3,
    )

    if state.competitor_blocked:

        with ui.column().classes("callout"):

            ui.label("通知").classes("notice-chip")
            ui.label("競合比較は一部のみ表示しています").classes("card-title")

            ui.label(f"競合URLは取得不可: {state.competitor_blocked}").classes("card-sub")

            ui.label("競合がスクレイピングを制限している可能性があり、比較は限定的です。").classes("card-sub")

            ui.label("相対的に自社が情報提供に積極的という優位性を示します。").classes("card-sub")

    elif state.competitor_error:

        with ui.column().classes("callout"):

            ui.label("通知").classes("notice-chip")
            ui.label("競合比較を完了できませんでした").classes("card-title")

            ui.label("競合URLの分析に失敗しました。URL形式とアクセス可否をご確認ください。").classes("card-sub")




@ui.refreshable

def detail_tabs() -> None:
    state = _require_state()
    trim_text = _require_trim_text()
    format_reason_text_ui = _require_format_reason_text_ui()
    AIO_SCORE_LABELS = _require_aio_score_labels()
    AIO_SCORE_HELP = _require_aio_score_help()

    if not state.results:
        ui.label("分析結果はまだありません。").classes("card-sub")
        return

    if _render_output_gate_notice(state.results):
        return

    results = state.results

    aio_results = results.get("aio_results", {})
    seo_results = results.get("seo_results", {})
    industry = results.get("final_industry", {})
    integrated = results.get("integrated_results", {})

    # タブ順: 価値の高さ・対象の広さ順（コンテンツ/SEO/AIO → 競合比較 → 専門・技術）
    ordered_tabs = ["引用候補", "SEO", "AIO", "業界", "サイトヘルス"]
    if state.competitor_results:
        ordered_tabs.insert(3, "比較")  # AIOの直後に挿入
    visible_tabs = ordered_tabs

    # 詳細タブ
    with ui.tabs().classes("tabs") as tabs:
        for tab in visible_tabs:
            ui.tab(tab)

    default_tab = visible_tabs[0]
    with ui.tab_panels(tabs, value=default_tab).classes("w-full"):
        if "サイトヘルス" in visible_tabs:
            with ui.tab_panel("サイトヘルス"):
                from core.ui.tabs.health_tab import render_health_tab
                render_health_tab(results, state.display_mode, include_legal=False)

        if "業界" in visible_tabs:
            with ui.tab_panel("業界"):
                from core.ui.tabs.industry_tab import render_industry_tab
                render_industry_tab(industry, results)

        if "SEO" in visible_tabs:
            with ui.tab_panel("SEO"):
                from core.ui.tabs.seo_tab import render_seo_tab
                render_seo_tab(
                    seo_results,
                    aio_results,
                    trim_text,
                    format_reason_text_ui,
                    results.get("site_health") or {},
                )

        if "AIO" in visible_tabs:
            with ui.tab_panel("AIO"):
                from core.ui.tabs.aio_tab import render_aio_tab
                render_aio_tab(aio_results, AIO_SCORE_LABELS, AIO_SCORE_HELP, trim_text, format_reason_text_ui)

        if "引用候補" in visible_tabs:
            with ui.tab_panel("引用候補"):
                from core.ui.tabs.simulation_tab import render_simulation_tab
                render_simulation_tab(results, state)

        if state.competitor_results and "比較" in visible_tabs:
            with ui.tab_panel("比較"):
                from core.ui.tabs.comparison_tab import render_comparison_tab
                render_comparison_tab(state, results, integrated, format_reason_text_ui)


@ui.refreshable

def report_panel() -> None:
    state = _require_state()
    trim_text = _require_trim_text()
    format_reason_text_ui = _require_format_reason_text_ui()
    """BOX3: 改善提案（非エンジニア/エンジニア分離）"""

    if not state.results:
        ui.label("分析結果はまだありません。").classes("card-sub")
        return

    if _render_output_gate_notice(state.results):
        return

    integrated = state.results.get("integrated_results", {})
    seo_results = state.results.get("seo_results", {})
    aio_results = state.results.get("aio_results", {})

    citation = state.results.get("citation_insights", {})
    deep_recs = state.results.get("deep_recommendations", {})
    platform_guidance = state.results.get("platform_guidance", {})

    summary = state.results.get("summary", {})
    url_type_meta = state.results.get("url_type", {}) or {}
    effective_type = url_type_meta.get("effective") or ""
    legal_checks = state.results.get("legal_checks", {}) or {}
    schema_existing = state.results.get("schema_existing", {}) or {}
    previous_run: Optional[Dict[str, Any]] = None
    state.report_expansions = []

    try:
        from core.storage.database import get_previous_run

        current_url = state.results.get("url") or ""
        previous_run = get_previous_run(current_url, getattr(state, "last_run_id", None))
    except Exception:
        pass

    same_url_history: list[dict] = []
    try:
        from core.storage.database import get_history

        current_url = state.results.get("url") or ""
        if current_url:
            same_url_history = get_history(url=current_url, limit=12)
    except Exception:
        same_url_history = []

    live_snapshot = _build_ui_snapshot(
        int(getattr(state, "last_run_id", 0) or 0),
        _safe_text(state.results.get("timestamp")) or datetime.now().isoformat(),
        state.results,
        previous_run,
        competitor_results=state.competitor_results,
        competitor_action_advice=state.competitor_action_advice,
        competitor_blocked=state.competitor_blocked,
        competitor_error=state.competitor_error,
    )
    _render_workspace_tabs(live_snapshot, same_url_history=same_url_history)
    return

    decision_actions = _build_decision_actions(
        deep_recs=deep_recs,
        aio_results=aio_results,
        seo_results=seo_results,
        summary=summary,
        business_goal=integrated.get("business_goal", "自動判定"),
    )

    visible_sections = ["rewrite", "ops", "engineer"]

    def _render_operations_section() -> None:
        _title_with_hint("すぐできる改善", "専門知識がなくても、管理画面や運用フローで着手できる改善だけを並べています。")

        # プラットフォーム別ガイド（非エンジニア向け）
        if platform_guidance:
            effective_platform = _format_context_value(platform_guidance.get("label"), missing_label="判定なし")
            ui.label(f"このサイトの運用基盤: {effective_platform}").classes("card-sub font-bold")

            business_steps = platform_guidance.get("business_steps", [])
            if business_steps:
                ops_guide_exp = ui.expansion('操作ガイド（管理画面から実行）', icon='settings').classes('w-full')
                state.report_expansions.append(ops_guide_exp)
                with ops_guide_exp:
                    for i, step in enumerate(business_steps[:8], 1):
                        ui.label(f"{i}. {trim_text(step, 400)}").classes("card-sub")

        # 深掘り提案（非エンジニア向け）
        business_recs = deep_recs.get("business", [])
        if business_recs:
            ui.separator()
            ui.label("優先度順の改善提案").classes("card-title")
            for i, rec in enumerate(business_recs[:6], 1):
                title = rec.get('title', '提案')
                action = rec.get("recommended_action", "")
                rec_exp = ui.expansion(f'{i}. {title}', icon='check_circle').classes('w-full')
                state.report_expansions.append(rec_exp)
                with rec_exp:
                    ui.label(format_reason_text_ui(action)).classes("card-sub whitespace-pre-line")
                    impact = rec.get("expected_impact", "")
                    if impact:
                        ui.label(format_reason_text_ui(f"期待効果: {impact}")).classes("card-hint text-green-600 whitespace-pre-line")
        else:
            # フォールバック: summary.improvements
            improvements = summary.get("improvements", [])
            if improvements:
                ui.separator()
                ui.label("推奨改善ポイント").classes("card-title")
                for i, imp in enumerate(improvements[:6], 1):
                    ui.label(f"{i}. {imp}").classes("card-sub")

        site_type_action = None
        if effective_type == "EC":
            site_type_action = "特商法・景表法の表記と購入導線の明確化を優先"
        elif effective_type == "企業":
            site_type_action = "会社概要/沿革/採用など信頼情報の明示を優先"
        elif effective_type == "企業（EC機能あり）":
            site_type_action = "特商法と会社情報の両方を整備し信頼情報を強化"
        if site_type_action:
            ui.separator()
            ui.label("サイト種別の優先アクション").classes("card-title")
            with ui.card().classes("card p-4 w-full"):
                ui.label(site_type_action).classes("card-sub")

        ec_section = legal_checks.get("commercial_transaction", {}) or {}
        ec_formatted = ec_section.get("formatted", {}) or {}
        if ec_formatted and "EC" in effective_type:
            ui.separator()
            ui.label("EC表示アドバイス・購入導線チェック").classes("card-title")
            ec_notice = ec_formatted.get("ec_notice", "")
            ec_detection = ec_formatted.get("ec_detection", {}) or {}
            confidence = ec_detection.get("confidence", "low")
            if ec_notice:
                ui.label(ec_notice).classes("card-hint text-xs")
            else:
                ui.label(f"EC判定: {ec_detection.get('note', '判定中')}（信頼度: {confidence}）").classes("card-hint text-xs")

            tokushoho = ec_section.get("tokushoho_page", {}) or {}
            if tokushoho.get("found"):
                ui.label(f"特商法ページ検出: {tokushoho.get('link_text', '')} / {tokushoho.get('location', '')}").classes("card-sub")
            else:
                ui.label("特商法ページが未検出です。フッターやガイド内にリンクがあるか確認してください。").classes("card-hint text-xs")

            missing = ec_formatted.get("missing_items_simple", []) or []
            if missing:
                ui.label("未検出の必須項目").classes("card-sub font-bold")
                ui.label("・" + "、".join(missing[:6])).classes("card-hint text-xs")

            faq_schema = "FAQPage" in (schema_existing.get("types") or [])
            ui.label(f"FAQ構造化: {'あり' if faq_schema else 'なし'}").classes("card-hint text-xs")

            sources = (ec_section.get("frame_sources", []) or []) + (ec_section.get("related_sources", []) or [])
            if sources:
                ui.label("参照した補助ページ").classes("card-sub font-bold")
                for src in sources[:3]:
                    ui.label(f"・{src}").classes("card-hint text-xs")

        # 即効性のある改善（具体例）
        ui.separator()
        ui.label("今日からできること（例）").classes("card-title")
        basics = seo_results.get("basics", {})
        title_len = len(basics.get("title", ""))
        desc_len = len(basics.get("meta_description", ""))

        quick_fixes = []
        if title_len < 20 or title_len > 40:
            quick_fixes.append(f"タイトルを20-40文字に調整（推奨は28-36文字、現在{title_len}文字）")
        if desc_len < 80 or desc_len > 160:
            quick_fixes.append(f"メタディスクリプションを80-120文字に調整（許容上限160文字、現在{desc_len}文字）")

        headings = seo_results.get("structure", {}).get("headings", {})
        h1_count = sum(1 for h in headings if h.startswith("h1"))
        if h1_count != 1:
            quick_fixes.append(f"H1タグを1つに統一（現在{h1_count}個）")

        if quick_fixes:
            for fix in quick_fixes[:3]:
                ui.label(f"・{fix}").classes("card-sub")
        else:
            ui.label("・基本的なSEO要素は適切に設定されています").classes("card-sub text-green-600")

    def _render_engineer_section() -> None:
        _title_with_hint("技術設定", "コード変更や設定変更が必要な項目です。")

        # 深掘り提案（エンジニア向け）
        technical_recs = deep_recs.get("technical", [])
        if technical_recs:
            ui.label("実装ガイド").classes("card-title")
            for i, rec in enumerate(technical_recs[:6], 1):
                title = rec.get('title', '技術改善')
                impl = rec.get("implementation", "")
                tech_exp = ui.expansion(f'{i}. {title}', icon='code').classes('w-full')
                state.report_expansions.append(tech_exp)
                with tech_exp:
                    ui.label(format_reason_text_ui(impl)).classes("card-sub whitespace-pre-line")
                    code_snippet = rec.get("code_snippet", "")
                    if code_snippet:
                        ui.code(code_snippet[:500]).classes("text-xs")

        # プラットフォーム別技術ガイド
        if platform_guidance:
            technical_steps = platform_guidance.get("technical_steps", [])
            if technical_steps:
                ui.separator()
                ui.label("プラットフォーム別実装手順").classes("card-title")
                for i, step in enumerate(technical_steps[:6], 1):
                    ui.label(f"{i}. {trim_text(step, 400)}").classes("card-sub")

            help_links = platform_guidance.get("help_links", [])
            if help_links:
                ui.label("公式ドキュメント").classes("card-title")
                for link in help_links[:3]:
                    ui.link(link.get("label", "公式ヘルプ"), link.get("url", "#"), new_tab=True).classes("card-sub")

        # AIO即時改善アクション
        aio_actions = aio_results.get("immediate_actions", [])
        if aio_actions:
            ui.separator()
            ui.label("AI検索向けの改善アクション（1-2週間で実行可能）").classes("card-title")
            for i, action in enumerate(aio_actions[:6], 1):
                action_text = action.get('action', '') if isinstance(action, dict) else str(action)
                method = action.get('method', '') if isinstance(action, dict) else ''
                display_action_text = format_reason_text_ui(action_text)
                aio_exp = ui.expansion(
                    f'{i}. {display_action_text[:60]}{"..." if len(display_action_text) > 60 else ""}',
                    icon='build',
                ).classes('w-full')
                state.report_expansions.append(aio_exp)
                with aio_exp:
                    if method:
                        formatted = format_reason_text_ui(method)
                        for line in formatted.split('\n'):
                            line = line.strip()
                            if line:
                                if line.startswith('【'):
                                    ui.label(line).classes("card-sub font-bold text-blue-600")
                                elif line.startswith('原文:') or line.startswith('改善:'):
                                    ui.label(line).classes("card-sub text-gray-700").style('word-break: break-all; white-space: pre-wrap;')
                                else:
                                    ui.label(line).classes("card-sub")

        # 技術チェックリスト
        ui.separator()
        ui.label("技術チェックリスト").classes("card-title")
        tech_details = aio_results.get("details", {}).get("tech", {})
        structure_details = aio_results.get("details", {}).get("structure", {})
        provider_readiness = aio_results.get("provider_readiness") or aio_results.get("details", {}).get("provider_readiness", {}) or {}

        provider_rows = [
            ("Google", (provider_readiness.get("google") or {}).get("status"), "Googlebot / noindex / snippet 制御"),
            ("OpenAI Search", (provider_readiness.get("openai_search") or {}).get("status"), "OAI-SearchBot"),
            ("Perplexity", (provider_readiness.get("perplexity") or {}).get("status"), "PerplexityBot"),
            ("Claude Search", (provider_readiness.get("claude_search") or {}).get("status"), "Claude-SearchBot"),
        ]
        for name, status, desc in provider_rows:
            if name == "Perplexity" and status == "pass":
                continue
            if status == "pass":
                icon, color, label = "✓", "text-green-600", "通過"
            elif status == "warn":
                icon, color, label = "△", "text-amber-600", "注意"
            else:
                icon, color, label = "✗", "text-red-600", "要対応"
            ui.label(f"{icon} {name}: {desc} [{label}]").classes(f"card-sub {color}")

        checklist = [
            ("JSON-LD", structure_details.get("has_json_ld", False), "構造化データ（補助シグナル）"),
            ("セマンティックタグ", structure_details.get("has_semantic_tags", False), "<article>, <section>等"),
        ]
        for name, status, desc in checklist:
            icon = "✓" if status else "✗"
            color = "text-green-600" if status else "text-red-600"
            ui.label(f"{icon} {name}: {desc}").classes(f"card-sub {color}")

        llms_exists = tech_details.get("llms_txt", False)
        llms_icon = "✓" if llms_exists else "△"
        llms_color = "text-green-600" if llms_exists else "text-amber-600"
        ui.label(f"{llms_icon} llms.txt（任意）: 公式要件ではなく、AI向け案内ファイル").classes(f"card-sub {llms_color}")

    def _render_rewrite_section() -> None:
        _title_with_hint("文章の改善案", "タイトル、説明文、本文、FAQ の改善案をまとめています。")

        tone = deep_recs.get("tone")
        tone_reason = deep_recs.get("tone_reason")
        if tone:
            tone_label = "人間味のあるトーン" if tone == "human" else "淡々としたトーン"
            ui.label(f"提案トーン: {tone_label}").classes("card-sub font-bold")
            if tone_reason:
                ui.label(f"理由: {tone_reason}").classes("card-hint text-xs")

        basics = seo_results.get("basics", {})
        current_title = basics.get("title", "")
        current_desc = basics.get("meta_description", "")
        title_rewrites = deep_recs.get("title_rewrites", [])
        desc_rewrites = deep_recs.get("description_rewrites", [])
        suggestions = aio_results.get("rewrite_suggestions", []) or []
        citation_phrases = citation.get("phrases", []) if citation else []
        faq_detection = state.results.get("faq_detection", {}) if state.results else {}
        existing_faqs = faq_detection.get("items", []) if isinstance(faq_detection, dict) else []
        content_plan = citation.get("content_plan", {}) if citation else {}
        sections = content_plan.get("sections", [])
        placements = content_plan.get("placements", [])
        has_compact_rewrite_content = any(
            [
                current_title,
                current_desc,
                title_rewrites,
                desc_rewrites,
                suggestions,
                citation_phrases,
                existing_faqs,
                sections,
                placements,
            ]
        )
        if not has_compact_rewrite_content:
            ui.label("このURLに対する具体的な改善候補はまだ十分に抽出できていません。まずは冒頭要約、数値根拠、運営者情報の追加を優先してください。").classes("card-hint")
            return

        if current_title or title_rewrites:
            ui.separator()
            ui.label("タイトルの改善案").classes("card-title")
        if current_title:
            title_len = len(current_title)
            ui.label(f"現在: 「{current_title}」({title_len}文字)").classes("card-sub")

            title_issues = []
            if title_len < 20:
                title_issues.append("短すぎ: キーワードを追加して情報量を増やす")
            elif title_len > 40:
                title_issues.append("長すぎ: 検索結果で途切れる可能性あり")
            elif title_len < 28 or title_len > 36:
                title_issues.append("推奨範囲外: 28-36文字に寄せると欠けにくい")
            if not any(c in current_title for c in ["｜", "|", "-", "："]):
                title_issues.append("区切り文字なし: ブランド名やカテゴリを「｜」で追加推奨")

            if title_issues:
                ui.label("改善ポイント:").classes("card-sub font-bold")
                for issue in title_issues:
                    ui.label(f"・{issue}").classes("card-sub text-amber-600")
            if title_rewrites:
                ui.label("提案タイトル（変更点を強調）:").classes("card-sub font-bold text-green-600")
                for i, rewrite in enumerate(title_rewrites[:2], 1):
                    _, after_html = _diff_html(current_title, rewrite)
                    ui.html(f"<div class='diff-line'><span class='diff-index'>{i}.</span>「{after_html}」</div>", sanitize=False).classes("card-sub diff-wrap")
        elif title_rewrites:
            ui.label("現在のタイトルは取得できませんでしたが、候補だけ抽出しています。").classes("card-hint text-sm")
            for i, rewrite in enumerate(title_rewrites[:2], 1):
                ui.label(f"{i}. {rewrite}").classes("card-sub text-green-700")
        elif current_title == "":
            ui.label("タイトルが検出されませんでした。").classes("card-sub text-red-600")

        if current_desc or desc_rewrites:
            ui.separator()
            ui.label("メタディスクリプションの改善案").classes("card-title")
        if current_desc:
            desc_len = len(current_desc)
            ui.label(f"現在: 「{current_desc[:100]}{'...' if len(current_desc) > 100 else ''}」({desc_len}文字)").classes("card-sub")

            desc_issues = []
            if desc_len < 80:
                desc_issues.append("短すぎ: CTAや具体的な価値提案を追加")
            elif desc_len > 160:
                desc_issues.append("長すぎ: モバイル検索で途切れる可能性")
            elif desc_len > 120:
                desc_issues.append("許容範囲だが長め: 80-120文字に収めると表示が安定")
            if "。" not in current_desc:
                desc_issues.append("文末の句点なし: 読みやすさ向上のため追加推奨")

            if desc_issues:
                ui.label("改善ポイント:").classes("card-sub font-bold")
                for issue in desc_issues:
                    ui.label(f"・{issue}").classes("card-sub text-amber-600")
            if desc_rewrites:
                ui.label("提案ディスクリプション（変更点を強調）:").classes("card-sub font-bold text-green-600")
                for i, rewrite in enumerate(desc_rewrites[:2], 1):
                    _, after_html = _diff_html(current_desc, rewrite)
                    ui.html(f"<div class='diff-line'><span class='diff-index'>{i}.</span>「{after_html}」</div>", sanitize=False).classes("card-sub diff-wrap")
        elif desc_rewrites:
            ui.label("現在の説明文は取得できませんでしたが、候補だけ抽出しています。").classes("card-hint text-sm")
            for i, rewrite in enumerate(desc_rewrites[:2], 1):
                ui.label(f"{i}. {rewrite}").classes("card-sub text-green-700")
        elif current_desc == "":
            ui.label("メタディスクリプションが検出されませんでした。").classes("card-sub text-red-600")
            ui.label("80-120文字程度で、ページの価値とCTAを含めて設定してください。").classes("card-hint")

        if suggestions:
            ui.separator()
            ui.label("本文リライト（変更前 / 変更後）").classes("card-title")
            for i, suggestion in enumerate(suggestions[:2], 1):
                before = str(suggestion.get("original_segment", "") or "")
                after = str(suggestion.get("improved_segment", "") or "")
                reason = str(suggestion.get("reason", "") or "")
                before_html, after_html = _diff_html(before, after)
                ui.label(f"提案 {i}").classes("card-sub font-bold")
                ui.html(f"<div class='diff-block'><span class='diff-label'>変更前</span> {before_html}</div>", sanitize=False).classes("card-sub diff-wrap")
                ui.html(f"<div class='diff-block'><span class='diff-label'>変更後</span> {after_html}</div>", sanitize=False).classes("card-sub diff-wrap")
                if reason:
                    ui.label(format_reason_text_ui(f"理由: {reason}")).classes("card-hint whitespace-pre-line")
        if citation_phrases:
            ui.separator()
            ui.label("AI引用されやすい文章構造").classes("card-title")
            ui.label("AIが回答に引用しやすいフォーマットに変換する提案です。").classes("card-hint text-sm")
            ui.label("引用候補フレーズ（改善前→改善後）:").classes("card-sub font-bold")
            for item in citation_phrases[:4]:
                phrase = item.get('phrase', '')
                template = item.get('template', '')
                template_non = item.get('template_non_engineer', '')
                template_eng = item.get('template_engineer', '')
                reason = item.get('reason', '')
                phrase_exp = ui.expansion(f'「{phrase[:40]}...」', icon='edit').classes('w-full')
                state.report_expansions.append(phrase_exp)
                with phrase_exp:
                    ui.label(f"現在: {phrase}").classes("card-sub")
                    if template:
                        ui.label(format_reason_text_ui(f"改善案: {template}")).classes("card-sub text-green-600 whitespace-pre-line")
                    if template_non:
                        ui.label(format_reason_text_ui(f"読み手向けの説明: {template_non}")).classes("card-sub text-emerald-600 whitespace-pre-line")
                    if template_eng:
                        ui.label(format_reason_text_ui(f"実装担当向けメモ: {template_eng}")).classes("card-sub text-blue-600 whitespace-pre-line")
                    if reason:
                        ui.label(format_reason_text_ui(f"理由: {reason}")).classes("card-hint whitespace-pre-line")
        if existing_faqs:
            ui.separator()
            ui.label("既存FAQ検出").classes("card-title")
            sources = faq_detection.get("sources", {}) if isinstance(faq_detection, dict) else {}
            source_text = f"（JSON-LD: {sources.get('json_ld', 0)}件 / HTML: {sources.get('html', 0)}件）" if sources else ""
            ui.label(f"ページ内のFAQを{len(existing_faqs)}件検出しました。{source_text}").classes("card-hint text-sm")
            validation = faq_detection.get("validation", {}) if isinstance(faq_detection, dict) else {}
            if validation:
                ui.label(
                    f"整合チェック: {validation.get('consistent_count', 0)}/{validation.get('checked', 0)}件が本文と整合 "
                    f"（レベル: {validation.get('consistency_level', '-')})"
                ).classes("card-hint text-sm")
                if validation.get("suspicious_count", 0):
                    ui.label(f"要確認: {validation.get('suspicious_count', 0)}件").classes("card-hint text-sm text-amber-700")
                    for rec in (validation.get("recommendations", []) or [])[:2]:
                        ui.label(f"・{rec}").classes("card-hint text-xs")
            for faq in existing_faqs[:4]:
                question = faq.get("question", "")
                answer = faq.get("answer", "")
                source = faq.get("source", "")
                faq_exp = ui.expansion(question or "FAQ", icon="help").classes("w-full")
                state.report_expansions.append(faq_exp)
                with faq_exp:
                    if source:
                        ui.label(f"検出元: {source}").classes("card-hint text-xs")
                    ui.label(answer).classes("card-sub whitespace-pre-line")
        elif not citation_phrases and not suggestions and not sections and not placements:
            ui.separator()
            ui.label("FAQ提案（既存FAQ未検出）").classes("card-title")
            ui.label("今回はこのURL固有のFAQ候補を確定できませんでした。実際の問い合わせで多い質問を整理して追加してください。").classes("card-hint text-sm")
            signals = faq_detection.get("signals", {}) if isinstance(faq_detection, dict) else {}
            if signals:
                ui.label(
                    f"FAQ候補を{signals.get('html_candidates', 0)}件確認し、"
                    f"{signals.get('html_filtered_out', 0)}件を除外しました。"
                ).classes("card-hint text-sm")
        if sections:
            ui.separator()
            ui.label("追加コンテンツ提案").classes("card-title")
            for section in sections[:3]:
                title = section.get("title", "新規セクション")
                fmt = section.get("format", "")
                purpose = section.get("purpose", "")
                section_exp = ui.expansion(f'{title}（{fmt}）', icon='add_circle').classes('w-full')
                state.report_expansions.append(section_exp)
                with section_exp:
                    if purpose:
                        ui.label(f"目的: {purpose}").classes("card-sub")
                    for bullet in (section.get("bullets", []) or [])[:5]:
                        ui.label(f"・{bullet}").classes("card-sub")
        if placements:
            ui.separator()
            ui.label("配置提案（引用されやすさ重視）").classes("card-title")
            for item in placements[:4]:
                content_type = item.get("content_type", "コンテンツ")
                position = item.get("recommended_position", "配置位置")
                reason = item.get("reason", "")
                place_exp = ui.expansion(f'{content_type}: {position}', icon='place').classes('w-full')
                state.report_expansions.append(place_exp)
                with place_exp:
                    if reason:
                        ui.label(f"理由: {reason}").classes("card-sub")

    def _render_url_specific_tab() -> None:
        _render_url_specific_highlights(
            results=state.results,
            integrated=integrated,
            seo_results=seo_results,
            aio_results=aio_results,
            summary=summary,
            lead_text="このタブには、今回のURLで見つかった現状だけをまとめています。改善方法は『改善方法』タブで確認してください。",
        )

        if state.results.get("legal_checks"):
            from core.ui.tabs.health_tab import render_legal_section
            from core.legal_checks.non_ec_summary import is_ec_site

            ui.separator()
            url_type_for_legal = state.results.get("url_type", {}) or {}
            is_ec_for_legal = is_ec_site(url_type_for_legal)
            legal_label = "表示アドバイス（重要）" if is_ec_for_legal else "表示アドバイス（参考）"
            legal_exp = ui.expansion(legal_label, icon="gavel", value=is_ec_for_legal).classes("w-full")
            state.report_expansions.append(legal_exp)
            with legal_exp:
                if not is_ec_for_legal:
                    ui.label("非ECサイトでは義務表示の一部は参考情報です。信頼表示や誤認防止の観点を中心に確認してください。").classes("card-hint text-xs")
                render_legal_section(state.results, leading_separator=False)

        if state.competitor_results:
            ui.separator()
            comp_integrated = state.competitor_results.get("integrated_results", {})
            with ui.card().classes("card p-4 w-full"):
                ui.label("競合比較の要点").classes("card-sub font-bold")
                for label, key in (
                    ("SEOスコア", "seo_score"),
                    ("AIOスコア", "aio_score"),
                    ("統合スコア", "integrated_score"),
                ):
                    own = float(integrated.get(key, 0) or 0)
                    comp = float(comp_integrated.get(key, 0) or 0)
                    diff = own - comp
                    verdict = "自社優位" if diff >= 3 else "拮抗" if diff >= -3 else "競合優位"
                    ui.label(f"{label}: 自社 {own:.0f} / 競合 {comp:.0f} / 差分 {diff:+.0f} ({verdict})").classes("card-sub")

    def _render_action_plan_tab() -> None:
        _render_management_brief(
            state=state,
            results=state.results,
            integrated=integrated,
            citation=citation,
            legal_checks=legal_checks,
        )

        if decision_actions:
            ui.separator()
            _title_with_hint("今すぐやること（上位3件）", "今回の分析結果から優先度順に抜き出した実行項目です。会議や外注指示にそのまま使えます。")
            for i, item in enumerate(decision_actions, 1):
                with ui.card().classes("card p-4 w-full"):
                    ui.label(f"優先度 {i}: {item['title']}").classes("card-sub font-bold")
                    ui.label(format_reason_text_ui(item.get("action", ""))).classes("card-sub whitespace-pre-line")
                    ui.label(f"担当: {item.get('role', '運用')} / 想定工数: {item.get('effort', '30〜90分')}").classes("card-hint text-xs")
                    ui.label(f"成果指標: {item.get('kpi', '検索流入/品質')}").classes("card-hint text-xs text-green-600")
                    if item.get("impact"):
                        ui.label(f"期待効果: {item.get('impact')}").classes("card-hint text-xs")

        section_meta = [
            ("rewrite", "文章の改善案", "edit"),
            ("ops", "すぐできる改善", "person"),
            ("engineer", "技術設定", "code"),
        ]
        for key, title, icon in section_meta:
            if key not in visible_sections:
                continue
            default_open = key == "rewrite"
            exp = ui.expansion(title, icon=icon, value=default_open).classes("w-full")
            state.report_expansions.append(exp)
            with exp:
                if key == "ops":
                    _render_operations_section()
                elif key == "rewrite":
                    _render_rewrite_section()
                else:
                    _render_engineer_section()

    def _render_supplement_tab() -> None:
        _render_result_context_notes(
            state=state,
            results=state.results,
            aio_results=aio_results,
            integrated=integrated,
            summary=summary,
            previous_run=previous_run,
        )











































































































