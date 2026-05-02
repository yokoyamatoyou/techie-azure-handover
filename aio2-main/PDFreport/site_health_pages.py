"""
PDF Report Site Health Pages（Phase 06強化版）
"""

from typing import Dict, List

from core.evidence_pipeline import aggregate_legal_check_results, generate_deep_dive_summary
from core.legal_checks.non_ec_summary import build_non_ec_legal_summary, format_non_ec_legal_summary


# 重要度に応じた記号
SEVERITY_MARKERS = {
    "high": "■",
    "medium": "▲",
    "low": "●",
    "info": "○",
}


def _font_family(pdf) -> str:
    """PDFオブジェクトからフォントファミリーを取得"""
    return getattr(pdf, "font_family", "Helvetica")


def add_safe_text(pdf, text: str, height: int = 6) -> None:
    """幅不足の例外を避けながら複数行テキストを描画"""
    if pdf.get_y() + height > 270:
        pdf.add_page()
    content_width = pdf.w - pdf.l_margin - pdf.r_margin
    if content_width <= 0:
        pdf.add_page()
        content_width = pdf.w - pdf.l_margin - pdf.r_margin
    if pdf.get_x() > pdf.w - pdf.r_margin - 1:
        pdf.set_x(pdf.l_margin)
    pdf.multi_cell(content_width, height, text)


def render_site_health_section(pdf, site_health: Dict, url_type_meta: Dict | None = None) -> None:
    """サイトヘルスセクションの描画"""
    pdf.add_page()
    pdf.set_font(_font_family(pdf), "B", 18)
    pdf.cell(0, 15, "サイトヘルスチェック結果", ln=True, align="C")
    pdf.ln(6)
    if url_type_meta:
        selected_type = url_type_meta.get("selected") or "未選択"
        detected_type = url_type_meta.get("detected") or "未検出"
        effective_type = url_type_meta.get("effective") or detected_type
        pdf.set_font(_font_family(pdf), "", 10)
        add_safe_text(
            pdf,
            f"サイト種別: {effective_type}（選択: {selected_type} / 検出: {detected_type}）",
        )
        pdf.ln(3)

    render_ogp_details(pdf, site_health.get("ogp", {}))
    render_security_details(pdf, site_health.get("security", {}))
    render_accessibility_details(pdf, site_health.get("accessibility", {}))


def render_ogp_details(pdf, ogp_data: Dict) -> None:
    """OGPセクションの詳細描画"""
    formatted = ogp_data.get("formatted", {})
    pdf.set_font(_font_family(pdf), "B", 13)
    pdf.cell(0, 8, f"SNSシェア設定 (OGP) - スコア: {formatted.get('score', 0)}点", ln=True)
    pdf.set_font(_font_family(pdf), "", 10)
    for item in formatted.get("items", [])[:10]:
        icon = item.get("icon", "-")
        text = item.get("text", "")
        add_safe_text(pdf, f"{icon} {text}")
    pdf.ln(5)


def render_security_details(pdf, security_data: Dict) -> None:
    """セキュリティセクションの詳細描画"""
    formatted = security_data.get("formatted", {})
    pdf.set_font(_font_family(pdf), "B", 13)
    pdf.cell(0, 8, f"セキュリティ - スコア: {formatted.get('score', 0)}点", ln=True)
    pdf.set_font(_font_family(pdf), "", 10)
    for item in formatted.get("items", [])[:10]:
        icon = item.get("icon", "-")
        text = item.get("text", "")
        add_safe_text(pdf, f"{icon} {text}")
    pdf.ln(5)


def render_accessibility_details(pdf, accessibility_data: Dict) -> None:
    """アクセシビリティセクションの詳細描画"""
    formatted = accessibility_data.get("formatted", {})
    pdf.set_font(_font_family(pdf), "B", 13)
    pdf.cell(0, 8, f"アクセシビリティ - スコア: {formatted.get('score', 0)}点", ln=True)
    pdf.set_font(_font_family(pdf), "", 10)
    for item in formatted.get("items", [])[:10]:
        icon = item.get("icon", "-")
        text = item.get("text", "")
        add_safe_text(pdf, f"{icon} {text}")
    pdf.ln(5)


# ============================================================
# Phase 06: 法務チェック深掘りセクション
# ============================================================

def _is_ec_site(url_type_meta: Dict | None) -> bool:
    """サイト種別メタからECサイトかどうかを推定"""
    if not url_type_meta:
        return True  # 不明な場合は従来通り表示（安全側）
    effective = (url_type_meta.get("effective") or "") if isinstance(url_type_meta, dict) else ""
    return "EC" in str(effective)


def render_legal_checks_section(
    pdf,
    legal_checks: Dict,
    url_type_meta: Dict | None = None,
    analysis_results: Dict | None = None,
) -> None:
    """法務チェックセクションの描画（Phase 06強化版）"""
    if not legal_checks:
        return

    is_ec = _is_ec_site(url_type_meta)
    filtered_legal = dict(legal_checks)
    if not is_ec:
        # 非ECサイトでは特商法（EC専用）をPDFから除外
        filtered_legal.pop("commercial_transaction", None)

    # 何も出すものが無い場合はページを作らない（空白ページ防止）
    has_formatted = False
    for key in ("premiums_labeling", "stealth_marketing", "commercial_transaction"):
        formatted = (filtered_legal.get(key, {}) or {}).get("formatted", {}) or {}
        if formatted:
            has_formatted = True
            break

    aggregated = aggregate_legal_check_results(filtered_legal)
    summary = generate_deep_dive_summary(aggregated)
    has_deep_dive = bool(summary.get("total_issues", 0))

    if not has_formatted and not has_deep_dive:
        return

    pdf.add_page()
    pdf.set_font(_font_family(pdf), "B", 18)
    pdf.cell(0, 15, "法的リスクチェック結果", ln=True, align="C")
    pdf.ln(6)

    if not is_ec and analysis_results:
        non_ec_summary = build_non_ec_legal_summary(analysis_results)
        formatted = format_non_ec_legal_summary(non_ec_summary, max_len=32, max_actions=2)
        if formatted:
            pdf.set_font(_font_family(pdf), "B", 12)
            pdf.cell(0, 8, formatted.get("title", "非EC向け 法務・信頼性チェック"), ln=True)
            pdf.set_font(_font_family(pdf), "", 10)
            summary_text = formatted.get("summary")
            if summary_text:
                add_safe_text(pdf, summary_text)
            for line in formatted.get("items", []):
                add_safe_text(pdf, f"・{line}")
            for action in formatted.get("actions", []):
                add_safe_text(pdf, f"→ {action}")
            note = formatted.get("note")
            if note:
                pdf.set_font(_font_family(pdf), "", 9)
                add_safe_text(pdf, note)
                pdf.set_font(_font_family(pdf), "", 10)
            pdf.ln(4)

    # 各チェック結果を描画
    render_premiums_labeling(pdf, filtered_legal.get("premiums_labeling", {}))
    render_stealth_marketing(pdf, filtered_legal.get("stealth_marketing", {}))
    if is_ec:
        render_commercial_transaction(pdf, filtered_legal.get("commercial_transaction", {}))

    # 深掘り分析セクション（出力があるときのみ）
    if has_deep_dive:
        render_legal_deep_dive(pdf, filtered_legal)


def render_premiums_labeling(pdf, premiums_data: Dict) -> None:
    """景品表示法チェック結果の描画"""
    formatted = premiums_data.get("formatted", {})
    if not formatted:
        return

    pdf.set_font(_font_family(pdf), "B", 13)
    status = formatted.get("status", "")
    pdf.cell(0, 8, f"景品表示法チェック - {status}", ln=True)

    pdf.set_font(_font_family(pdf), "", 10)
    for item in formatted.get("items", [])[:8]:
        icon = item.get("icon", "-")
        text = item.get("text", "")
        add_safe_text(pdf, f"{icon} {text}")

    # 推奨事項
    recommendations = formatted.get("recommendations", [])
    if recommendations:
        pdf.set_font(_font_family(pdf), "B", 10)
        pdf.cell(0, 6, "推奨事項:", ln=True)
        pdf.set_font(_font_family(pdf), "", 9)
        for rec in recommendations[:3]:
            add_safe_text(pdf, f"  ・{rec}")

    pdf.ln(4)


def render_stealth_marketing(pdf, stealth_data: Dict) -> None:
    """ステマ規制チェック結果の描画"""
    formatted = stealth_data.get("formatted", {})
    if not formatted:
        return

    pdf.set_font(_font_family(pdf), "B", 13)
    status = formatted.get("status", "")
    pdf.cell(0, 8, f"ステルスマーケティング規制チェック - {status}", ln=True)

    pdf.set_font(_font_family(pdf), "", 10)
    for item in formatted.get("items", [])[:6]:
        icon = item.get("icon", "-")
        text = item.get("text", "")
        add_safe_text(pdf, f"{icon} {text}")

    # テンプレート提案
    template = formatted.get("template_suggestion")
    if template:
        pdf.set_font(_font_family(pdf), "B", 10)
        pdf.cell(0, 6, "推奨PR表記:", ln=True)
        pdf.set_font(_font_family(pdf), "", 9)
        add_safe_text(pdf, f"  {template}")

    pdf.ln(4)


def render_commercial_transaction(pdf, commercial_data: Dict) -> None:
    """特定商取引法チェック結果の描画（Phase 06強化版）"""
    formatted = commercial_data.get("formatted", {})
    if not formatted:
        return

    pdf.set_font(_font_family(pdf), "B", 13)
    status = formatted.get("status", "")
    compliance_rate = formatted.get("compliance_rate", 0)
    pdf.cell(0, 8, f"特定商取引法チェック - {status} (適合率: {compliance_rate})", ln=True)

    # 特商法ページ検出情報
    tokushoho_page = commercial_data.get("tokushoho_page", {})
    if tokushoho_page:
        pdf.set_font(_font_family(pdf), "", 10)
        if tokushoho_page.get("found"):
            add_safe_text(pdf, f"● 特商法ページ検出: {tokushoho_page.get('link_text', '')} ({tokushoho_page.get('location', '')})")
        else:
            add_safe_text(pdf, "▲ 特商法ページが見つかりません（ECサイトの場合は作成を推奨）")

    # 検出項目
    pdf.set_font(_font_family(pdf), "", 10)
    for item in formatted.get("items", [])[:10]:
        icon = item.get("icon", "-")
        text = item.get("text", "")
        hint = item.get("hint", "")
        if hint:
            add_safe_text(pdf, f"{icon} {text}")
            pdf.set_font(_font_family(pdf), "", 8)
            add_safe_text(pdf, f"    → {hint}")
            pdf.set_font(_font_family(pdf), "", 10)
        else:
            add_safe_text(pdf, f"{icon} {text}")

    pdf.ln(4)


def render_legal_deep_dive(pdf, legal_checks: Dict) -> None:
    """法務チェック深掘り分析セクション（Phase 06）"""
    # 結果を集約
    aggregated = aggregate_legal_check_results(legal_checks)
    summary = generate_deep_dive_summary(aggregated)
    if not summary.get("total_issues", 0):
        return

    # 深掘り分析セクションを新ページで開始
    pdf.add_page()
    pdf.set_font(_font_family(pdf), "B", 16)
    pdf.cell(0, 12, "法務チェック深掘り分析", ln=True, align="C")
    pdf.ln(4)

    # ヘッドライン
    pdf.set_font(_font_family(pdf), "B", 12)
    add_safe_text(pdf, summary["headline"])
    pdf.ln(3)

    # 統計情報
    pdf.set_font(_font_family(pdf), "", 10)
    add_safe_text(pdf, f"検出件数: {summary['total_issues']}件")

    category_breakdown = summary.get("category_breakdown", {})
    if category_breakdown:
        categories_str = " / ".join([f"{cat}: {count}件" for cat, count in category_breakdown.items()])
        add_safe_text(pdf, f"カテゴリ別: {categories_str}")
    pdf.ln(4)

    # 重要な問題
    high_priority = summary.get("high_priority", [])
    if high_priority:
        pdf.set_font(_font_family(pdf), "B", 12)
        pdf.set_text_color(200, 0, 0)  # 赤
        pdf.cell(0, 8, "■ 重要（要対応）", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(_font_family(pdf), "", 10)

        for cluster in high_priority[:5]:
            render_issue_cluster(pdf, cluster, "high")
        pdf.ln(3)

    # 注意が必要な問題
    medium_priority = summary.get("medium_priority", [])
    if medium_priority:
        pdf.set_font(_font_family(pdf), "B", 12)
        pdf.set_text_color(200, 100, 0)  # オレンジ
        pdf.cell(0, 8, "▲ 注意（要確認）", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(_font_family(pdf), "", 10)

        for cluster in medium_priority[:5]:
            render_issue_cluster(pdf, cluster, "medium")
        pdf.ln(3)

    # 参考情報
    low_priority = summary.get("low_priority", [])
    if low_priority:
        pdf.set_font(_font_family(pdf), "B", 12)
        pdf.set_text_color(0, 100, 200)  # 青
        pdf.cell(0, 8, "● 参考", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(_font_family(pdf), "", 10)

        for cluster in low_priority[:3]:
            render_issue_cluster(pdf, cluster, "low")


def render_issue_cluster(pdf, cluster: Dict, severity: str) -> None:
    """個別の問題クラスターを描画"""
    representative = cluster.get("representative", {})
    member_count = cluster.get("member_count", 1)
    evidence_summary = cluster.get("evidence_summary", "")

    marker = SEVERITY_MARKERS.get(severity, "○")

    # 問題テキスト
    matched_text = representative.get("matched_text", "")[:60]
    if member_count > 1:
        add_safe_text(pdf, f"  {marker} {matched_text} (+{member_count - 1}件)")
    else:
        add_safe_text(pdf, f"  {marker} {matched_text}")

    # 根拠スニペット
    if evidence_summary:
        pdf.set_font(_font_family(pdf), "", 8)
        add_safe_text(pdf, f"      根拠: {evidence_summary[:80]}")
        pdf.set_font(_font_family(pdf), "", 10)

    # 位置情報
    location = representative.get("location", "")
    if location:
        pdf.set_font(_font_family(pdf), "", 8)
        add_safe_text(pdf, f"      位置: {location}")
        pdf.set_font(_font_family(pdf), "", 10)

    # カテゴリ
    category = representative.get("category", "")
    if category:
        pdf.set_font(_font_family(pdf), "", 8)
        add_safe_text(pdf, f"      カテゴリ: {category}")
        pdf.set_font(_font_family(pdf), "", 10)

    # HTMLスニペット
    html_snippet = representative.get("html_snippet", "")
    if html_snippet:
        pdf.set_font(_font_family(pdf), "", 8)
        add_safe_text(pdf, f"      HTML: {html_snippet[:120]}")
        pdf.set_font(_font_family(pdf), "", 10)

    # 改善提案
    suggestion = representative.get("suggestion", "")
    if suggestion:
        pdf.set_font(_font_family(pdf), "", 8)
        add_safe_text(pdf, f"      改善: {suggestion[:100]}")
        pdf.set_font(_font_family(pdf), "", 10)
