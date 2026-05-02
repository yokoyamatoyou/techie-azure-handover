# -*- coding: utf-8 -*-
"""PDF report sections extracted from high_quality_pdf_generator."""

from typing import Any, Dict, List


def render_decision_summary_section(
    pdf,
    *,
    analysis_results: Dict[str, Any],
    deep_recs: Dict[str, Any],
    aio_results: Dict[str, Any],
    seo_results: Dict[str, Any],
    legal_checks: Dict[str, Any],
    color_mint,
    color_lavender,
    color_peach,
) -> None:
    def _infer_kpi(text: str) -> str:
        text = text or ""
        if any(k in text for k in ["タイトル", "メタ", "OGP"]):
            return "CTR"
        if any(k in text for k in ["速度", "LCP", "INP", "CLS"]):
            return "表示速度"
        if any(k in text for k in ["FAQ", "構造化", "JSON-LD", "引用"]):
            return "AI引用率"
        if any(k in text for k in ["返品", "配送", "送料", "支払い", "特商法"]):
            return "CVR/信頼性"
        return "検索流入/品質"

    def _format_meta_time(raw: str) -> str:
        if not raw:
            return ""
        return raw.replace("T", " ").split(".")[0]

    def _build_decision_actions() -> List[dict]:
        items: List[dict] = []
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
            for imp in (analysis_results.get("summary", {}).get("improvements", []) or [])[:3]:
                items.append({
                    "title": "改善ポイント",
                    "action": imp,
                    "role": "運用/マーケ",
                    "effort": "30〜90分",
                    "kpi": _infer_kpi(imp),
                    "impact": "",
                })
        return items[:3]

    decision_actions = _build_decision_actions()
    if not decision_actions:
        return

    pdf.add_page()
    pdf.add_section_title("意思決定サマリ（今すぐやるTop3）")

    analysis_meta = analysis_results.get("analysis_meta", {}) or {}
    if analysis_meta:
        started_at = _format_meta_time(analysis_meta.get("started_at", ""))
        ended_at = _format_meta_time(analysis_meta.get("ended_at", ""))
        duration = analysis_meta.get("duration_sec")
        progress_log = analysis_meta.get("progress_log", []) or []
        last_stage = progress_log[-1].get("stage") if progress_log else ""
        meta_lines = []
        if started_at:
            meta_lines.append(f"開始: {started_at}")
        if ended_at:
            meta_lines.append(f"終了: {ended_at}")
        if duration is not None:
            meta_lines.append(f"所要: {duration}秒")
        if last_stage:
            meta_lines.append(f"最終ステップ: {last_stage}")
        if meta_lines:
            pdf.add_info_card("解析メタ情報", "\n".join(meta_lines), card_color=color_mint, max_chars=400)

    for i, item in enumerate(decision_actions, 1):
        body = (
            f"担当: {item.get('role', '運用/マーケ')}\n"
            f"想定工数: {item.get('effort', '30〜90分')}\n"
            f"成果指標: {item.get('kpi', '検索流入/品質')}\n"
            f"{item.get('action', '')}"
        )
        if item.get("impact"):
            body += f"\n期待効果: {item.get('impact')}"
        pdf.add_info_card(f"優先度 {i}: {item.get('title', '改善提案')}", body, card_color=color_mint, max_chars=700, allow_split=False)

    ec_section = (legal_checks or {}).get("commercial_transaction", {}) or {}
    ec_formatted = ec_section.get("formatted", {}) or {}
    url_type_meta = analysis_results.get("url_type", {}) or {}
    effective_type = url_type_meta.get("effective") or ""
    if ec_formatted and "EC" in str(effective_type):
        pdf.add_subsection_title("EC法務・購入導線チェック")
        ec_notice = ec_formatted.get("ec_notice") or ""
        ec_detection = ec_formatted.get("ec_detection", {}) or {}
        confidence = ec_detection.get("confidence", "low")
        note = ec_notice or ec_detection.get("note", "")
        pdf.add_info_card(
            "EC判定",
            f"{note}\n信頼度: {confidence}",
            card_color=color_lavender,
            max_chars=400,
        )
        tokushoho = ec_section.get("tokushoho_page", {}) or {}
        if tokushoho.get("found"):
            pdf.add_info_card(
                "特商法ページ",
                f"{tokushoho.get('link_text', '')}\n場所: {tokushoho.get('location', '')}",
                card_color=color_peach,
                max_chars=400,
            )
        else:
            pdf.add_info_card(
                "特商法ページ",
                "特商法ページが検出されませんでした。",
                card_color=color_peach,
                max_chars=400,
            )


def render_executive_brief_section(
    pdf,
    *,
    analysis_results: Dict[str, Any],
    deep_recs: Dict[str, Any],
    aio_results: Dict[str, Any],
    seo_results: Dict[str, Any],
    color_mint,
    color_lavender,
    color_peach,
) -> None:
    def _infer_kpi(text: str) -> str:
        text = text or ""
        if any(k in text for k in ["タイトル", "メタ", "OGP"]):
            return "CTR"
        if any(k in text for k in ["速度", "LCP", "INP", "CLS"]):
            return "表示速度"
        if any(k in text for k in ["FAQ", "構造化", "JSON-LD", "引用"]):
            return "AI引用率"
        if any(k in text for k in ["返品", "配送", "送料", "支払い", "特商法"]):
            return "CVR/信頼性"
        return "検索流入/品質"

    def _score_status(score: float) -> tuple[str, str, str]:
        if score >= 80:
            return ("良好", "▲", "up")
        if score >= 50:
            return ("要改善", "■", "neutral")
        return ("注意", "●", "down")

    def _build_decision_actions() -> List[dict]:
        items: List[dict] = []
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
            for imp in (analysis_results.get("summary", {}).get("improvements", []) or [])[:3]:
                items.append({
                    "title": "改善ポイント",
                    "action": imp,
                    "role": "運用/マーケ",
                    "effort": "30〜90分",
                    "kpi": _infer_kpi(imp),
                    "impact": "",
                })
        return items[:3]

    integrated = analysis_results.get("integrated_results", {}) or {}
    summary = analysis_results.get("summary", {}) or {}
    warnings_list = analysis_results.get("warnings", []) or []
    integrated_score = float(integrated.get("integrated_score", 0))
    seo_score = float(integrated.get("seo_score", 0))
    aio_score = float(integrated.get("aio_score", 0))

    overall_label, overall_symbol, overall_trend = _score_status(integrated_score)
    seo_label, seo_symbol, seo_trend = _score_status(seo_score)
    aio_label, aio_symbol, aio_trend = _score_status(aio_score)

    pdf.add_page()
    pdf.add_section_title("経営サマリー（非エンジニア向け）")

    stats = [
        {"label": "統合スコア", "value": f"{integrated_score:.0f}", "sub_text": f"{overall_symbol}{overall_label}", "trend": overall_trend},
        {"label": "SEOスコア", "value": f"{seo_score:.0f}", "sub_text": f"{seo_symbol}{seo_label}", "trend": seo_trend},
        {"label": "AIOスコア", "value": f"{aio_score:.0f}", "sub_text": f"{aio_symbol}{aio_label}", "trend": aio_trend},
    ]
    pdf.add_stat_cards_row(stats)

    summary_text = summary.get("summary_text") or summary.get("summary") or ""
    if not summary_text:
        summary_text = f"統合スコアは{integrated_score:.0f}点。まずは最優先アクションを実行し、主要KPIの改善を狙います。"
    pdf.add_info_card("現状サマリー", summary_text, card_color=color_lavender, max_chars=700, allow_split=False)

    decision_actions = _build_decision_actions()
    if decision_actions:
        lines = []
        for i, item in enumerate(decision_actions, 1):
            line = f"{i}. {item.get('title', '改善提案')} / KPI:{item.get('kpi', '-')}" \
                   f" / 工数:{item.get('effort', '-')}"
            impact = item.get("impact")
            if impact:
                line += f" / 効果:{impact}"
            lines.append(line)
        pdf.add_info_card("最優先アクション Top3", "\n".join(lines), card_color=color_mint, max_chars=800, allow_split=False)

    if warnings_list:
        warning_lines = [f"・{item}" for item in warnings_list[:3]]
        pdf.add_info_card("主要リスク", "\n".join(warning_lines), card_color=color_peach, max_chars=600, allow_split=False)
    else:
        pdf.add_info_card("主要リスク", "重大なリスクは検出されませんでした。", card_color=color_peach, max_chars=400, allow_split=False)


def render_immediate_actions_section(
    pdf,
    *,
    seo_results: Dict[str, Any],
    aio_results: Dict[str, Any],
    color_mint,
    color_blue,
) -> None:
    seo_immediate = (seo_results or {}).get("immediate_actions", []) or []
    aio_immediate = (aio_results or {}).get("immediate_actions", []) or []
    if not (seo_immediate or aio_immediate):
        return

    pdf.add_page()
    pdf.add_section_title("即時改善アクション（1〜2週間）")

    if aio_immediate:
        pdf.add_subsection_title("AIO 即時改善")
        for item in aio_immediate[:5]:
            action = item.get("action", "") if isinstance(item, dict) else str(item)
            method = item.get("method", "") if isinstance(item, dict) else ""
            content = action
            if method:
                content = f"{action}\n{method}"
            pdf.add_info_card("改善アクション", content, card_color=color_mint, max_chars=600, allow_split=False)

    if seo_immediate:
        pdf.add_subsection_title("SEO 即時改善（プラットフォーム別）")
        for item in seo_immediate[:5]:
            action = item.get("action", "") if isinstance(item, dict) else str(item)
            method = item.get("method", "") if isinstance(item, dict) else ""
            content = action
            if method:
                content = f"{action}\n{method}"
            pdf.add_info_card("改善アクション", content, card_color=color_blue, max_chars=600, allow_split=False)


def render_improvement_section(
    pdf,
    *,
    analysis_results: Dict[str, Any],
    deep_recs: Dict[str, Any],
    aio_results: Dict[str, Any],
    color_mint,
    color_blue,
    color_peach,
) -> None:
    pdf.add_page()
    pdf.add_section_title("改善提案")

    # 非エンジニア向け提案
    pdf.add_subsection_title("非エンジニア向け（すぐにできる改善）")
    business_recs = deep_recs.get("business", [])
    if business_recs:
        for rec in business_recs[:5]:
            title = rec.get("title", "改善提案")
            action = rec.get("recommended_action", "")
            pdf.add_info_card(title, action[:200], card_color=color_mint, allow_split=False)
    else:
        improvements = analysis_results.get("summary", {}).get("improvements", [])
        for i, imp in enumerate(improvements[:5], 1):
            pdf.add_info_card(f"改善点 {i}", imp, card_color=color_mint, allow_split=False)

    # エンジニア向け提案
    pdf.add_subsection_title("エンジニア向け（技術的な改善）")
    technical_recs = deep_recs.get("technical", [])
    if technical_recs:
        for rec in technical_recs[:5]:
            title = rec.get("title", "技術改善")
            impl = rec.get("implementation", "")
            pdf.add_info_card(title, impl[:200], card_color=color_blue, allow_split=False)
    else:
        aio_actions = aio_results.get("immediate_actions", [])
        for action in aio_actions[:5]:
            action_text = action.get("action", "") if isinstance(action, dict) else str(action)
            method = action.get("method", "") if isinstance(action, dict) else ""
            pdf.add_info_card(action_text, method[:200], card_color=color_blue, allow_split=False)

    # リライト案
    rewrite_suggestions = aio_results.get("rewrite_suggestions", [])
    if rewrite_suggestions:
        pdf.add_subsection_title("リライト案（引用されやすい構成）")
        for i, item in enumerate(rewrite_suggestions[:3], 1):
            reason = pdf._truncate_text(item.get("reason", ""), max_chars=160)
            original = pdf._truncate_text(item.get("original_segment", ""), max_chars=180)
            improved = pdf._truncate_text(item.get("improved_segment", ""), max_chars=180)
            body = f"【理由】\n{reason}\n\n【原文】\n{original}\n\n【改善】\n{improved}"
            pdf.add_info_card(f"改善案 {i}", body, card_color=color_peach, allow_split=False)
