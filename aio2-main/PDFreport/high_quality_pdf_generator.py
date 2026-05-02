# -*- coding: utf-8 -*-
"""Compact fpdf2 PDF generator (executive + engineer focused)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from fpdf import FPDF

from core.config import config
from core.evidence_pipeline import aggregate_legal_check_results, generate_deep_dive_summary
from core.platform_guidance import build_platform_risk_profile, get_platform_guidance


COLOR_PRIMARY = (26, 71, 111)
COLOR_ACCENT = (18, 165, 148)
COLOR_MUTED = (90, 90, 90)
COLOR_BORDER = (220, 220, 220)


def _font_paths() -> Tuple[Path, Path]:
    font_dir = Path(__file__).resolve().parent / "fonts"
    return font_dir / config.PDF_FONT_REGULAR, font_dir / config.PDF_FONT_BOLD


def _setup_fonts(pdf: FPDF) -> None:
    regular_path, bold_path = _font_paths()
    if regular_path.exists() and bold_path.exists():
        pdf.add_font("NotoSansJP", "", str(regular_path), uni=True)
        pdf.add_font("NotoSansJP", "B", str(bold_path), uni=True)
        pdf.set_font("NotoSansJP", "", 11)
        return
    pdf.set_font("Helvetica", "", 11)


def _set_title(pdf: FPDF, text: str) -> None:
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.set_font(size=20, style="B")
    pdf.cell(0, 10, text, ln=True)
    pdf.set_text_color(0, 0, 0)


def _section_title(pdf: FPDF, text: str) -> None:
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.set_font(size=13, style="B")
    pdf.cell(0, 8, text, ln=True)
    pdf.set_text_color(0, 0, 0)


def _muted(pdf: FPDF, text: str) -> None:
    pdf.set_text_color(*COLOR_MUTED)
    pdf.set_font(size=9)
    width = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(width, 5, text)
    pdf.set_text_color(0, 0, 0)


def _no_data_notice(pdf: FPDF, label: str) -> None:
    _muted(pdf, f"{label}は未取得です。必要に応じて再解析や設定をご確認ください。")


def _bullet_list(pdf: FPDF, items: List[str], max_items: int = 5) -> None:
    pdf.set_font(size=10)
    width = pdf.w - pdf.l_margin - pdf.r_margin
    for item in items[:max_items]:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(width, 5, f"・{item}")


def _card(pdf: FPDF, title: str, body: str) -> None:
    x, y = pdf.get_x(), pdf.get_y()
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(x, y, w, 28, style="DF")
    pdf.set_xy(x + 2, y + 2)
    pdf.set_font(size=11, style="B")
    pdf.cell(0, 6, title, ln=True)
    pdf.set_font(size=9)
    pdf.multi_cell(w - 4, 4.5, body)
    pdf.set_xy(x, y + 30)


def _two_col_kv(pdf: FPDF, rows: List[Tuple[str, str]]) -> None:
    """Simple two-column key/value table."""
    pdf.set_font(size=10)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    key_w = max(42, int(w * 0.28))
    val_w = w - key_w
    for k, v in rows:
        pdf.set_x(pdf.l_margin)
        pdf.set_font(size=10, style="B")
        pdf.cell(key_w, 6, str(k), border=0)
        pdf.set_font(size=10)
        pdf.multi_cell(val_w, 6, str(v))


def _rewrite_block(pdf: FPDF, label: str, before: str, after: str, reason: str = "", max_chars: int = 240) -> None:
    """Before/After block with light styling (PDF版差分カード)."""
    before = (before or "").strip()
    after = (after or "").strip()
    if max_chars and len(before) > max_chars:
        before = before[: max_chars - 1] + "…"
    if max_chars and len(after) > max_chars:
        after = after[: max_chars - 1] + "…"

    w = pdf.w - pdf.l_margin - pdf.r_margin
    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_x(x)
    pdf.set_font(size=11, style="B")
    pdf.cell(0, 6, label, ln=True)

    # Before
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(x, pdf.get_y(), w, 18, style="DF")
    pdf.set_xy(x + 2, pdf.get_y() + 1)
    pdf.set_font(size=9, style="B")
    pdf.cell(0, 5, "Before", ln=True)
    pdf.set_font(size=9)
    pdf.multi_cell(w - 4, 4.5, before or "（未検出）")
    pdf.ln(1)

    # After
    pdf.set_x(x)
    pdf.set_fill_color(236, 252, 248)  # light green
    pdf.rect(x, pdf.get_y(), w, 18, style="DF")
    pdf.set_xy(x + 2, pdf.get_y() + 1)
    pdf.set_font(size=9, style="B")
    pdf.cell(0, 5, "After", ln=True)
    pdf.set_font(size=9)
    pdf.multi_cell(w - 4, 4.5, after or "（提案なし）")
    pdf.ln(1)

    if reason:
        _muted(pdf, f"理由: {reason[:160]}{'…' if len(reason) > 160 else ''}")


def _extract_improvements(analysis_results: Dict[str, Any]) -> List[str]:
    summary = (analysis_results.get("summary") or {}).get("improvements") or []
    if summary:
        return summary
    integrated = analysis_results.get("integrated_results", {}) or {}
    return integrated.get("improvements", []) or []


def _build_exec_summary(analysis_results: Dict[str, Any]) -> str:
    integrated = analysis_results.get("integrated_results", {}) or {}
    focus = "AIO" if integrated.get("aio_score", 0) < integrated.get("seo_score", 0) else "SEO"
    url_type = (analysis_results.get("url_type") or {}).get("effective") or "未検出"
    industry = (analysis_results.get("final_industry") or {}).get("primary") or "未検出"
    is_ec = analysis_results.get("is_ec")
    ec_label = "EC" if is_ec else "非EC" if is_ec is not None else "不明"
    return (
        f"業界: {industry} / URL種別: {url_type} / 判定: {ec_label}\n"
        f"優先領域: {focus}（スコア差から判定）"
    )


def _legal_engineer_notes(analysis_results: Dict[str, Any]) -> Tuple[str, List[str]]:
    legal_checks = analysis_results.get("legal_checks", {}) or {}
    summary = analysis_results.get("legal_summary") or {}
    if not summary:
        aggregated = aggregate_legal_check_results(legal_checks) if isinstance(legal_checks, dict) else {}
        summary = generate_deep_dive_summary(aggregated) if isinstance(aggregated, dict) else {}
    headline = summary.get("headline") or "法務リスクの要約はUIで確認してください。"
    items = []
    for cluster in (summary.get("high_priority") or []) + (summary.get("medium_priority") or []):
        rep = cluster.get("representative", {}) or {}
        text = rep.get("title") or rep.get("issue") or rep.get("matched_text") or "要確認"
        items.append(text)
    return headline, items


def _extract_llms_status(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    aio_results = analysis_results.get("aio_results", {}) or {}
    llms_payload = aio_results.get("llms_txt", {}) or {}
    if not isinstance(llms_payload, dict):
        llms_payload = {}
    return {
        "exists": bool(llms_payload.get("exists")),
        "found_paths": llms_payload.get("found_paths", []) or [],
        "quality_score": llms_payload.get("quality_score"),
        "quality_level": llms_payload.get("quality_level"),
        "quality_issues": llms_payload.get("quality_issues", []) or [],
        "quality_recommendations": llms_payload.get("quality_recommendations", []) or [],
    }


def _collect_missing_security_items(analysis_results: Dict[str, Any]) -> List[str]:
    site_health = analysis_results.get("site_health", {}) or {}
    security = (site_health.get("security", {}) or {}).get("formatted", {}) or {}
    missing: List[str] = []
    for item in security.get("items", []) or []:
        text = str(item.get("text", "") or "")
        subtext = str(item.get("subtext", "") or "")
        if "未設定" in text or "未対応" in text:
            line = text
            if subtext:
                line = f"{text} / {subtext}"
            missing.append(line)
    return missing[:4]


def _render_platform_risk_and_llms(
    pdf: FPDF,
    analysis_results: Dict[str, Any],
    platform_label: str,
) -> None:
    profile = build_platform_risk_profile(platform_label)
    label = profile.get("label", "未検出")

    _section_title(pdf, f"プラットフォーム別リスク整理（{label}）")

    pdf.set_font(size=11, style="B")
    pdf.cell(0, 6, "共通リスク（用語説明 + 対処）", ln=True)
    common_items = []
    for item in profile.get("common_risks", [])[:3]:
        common_items.append(
            f"{item.get('term')}: {item.get('plain')} "
            f"リスク: {item.get('risk')} / 対処: {item.get('action')}"
        )
    _bullet_list(pdf, common_items, max_items=3)

    pdf.ln(1)
    pdf.set_font(size=11, style="B")
    pdf.cell(0, 6, "このプラットフォームで特に注意するリスク", ln=True)
    specific_items = []
    for item in profile.get("platform_specific_risks", [])[:3]:
        specific_items.append(
            f"{item.get('term')}: {item.get('plain')} "
            f"リスク: {item.get('risk')} / 対処: {item.get('action')}"
        )
    _bullet_list(pdf, specific_items, max_items=3)

    detected_missing = _collect_missing_security_items(analysis_results)
    if detected_missing:
        pdf.ln(1)
        pdf.set_font(size=11, style="B")
        pdf.cell(0, 6, "このサイトで検出した未設定項目", ln=True)
        _bullet_list(pdf, detected_missing, max_items=4)

    llms_status = _extract_llms_status(analysis_results)
    pdf.ln(2)
    pdf.set_font(size=11, style="B")
    status = "設置済み" if llms_status.get("exists") else "未設置"
    pdf.cell(0, 6, f"AIクローラー向け案内（llms.txt）: {status}", ln=True)
    if llms_status.get("exists"):
        found_paths = llms_status.get("found_paths", [])
        if found_paths:
            _muted(pdf, f"検出パス: {', '.join(found_paths[:3])}")
        quality_score = llms_status.get("quality_score")
        quality_level = llms_status.get("quality_level") or "-"
        if isinstance(quality_score, (int, float)):
            _muted(pdf, f"品質スコア: {int(quality_score)}/100（{quality_level}）")
        quality_issues = llms_status.get("quality_issues", []) or []
        if quality_issues:
            pdf.set_font(size=10, style="B")
            pdf.cell(0, 6, "llms.txt の改善ポイント", ln=True)
            _bullet_list(pdf, [str(x) for x in quality_issues[:3]], max_items=3)
        quality_recs = llms_status.get("quality_recommendations", []) or []
        if quality_recs:
            pdf.set_font(size=10, style="B")
            pdf.cell(0, 6, "推奨対応", ln=True)
            _bullet_list(pdf, [str(x) for x in quality_recs[:3]], max_items=3)

    pdf.set_font(size=10, style="B")
    pdf.cell(0, 6, "llms.txt 配置ベストプラクティス", ln=True)
    _bullet_list(pdf, [str(s) for s in profile.get("llms_txt_best_practices", [])[:5]], max_items=5)


def _render_faq_llmo_policy(
    pdf: FPDF,
    analysis_results: Dict[str, Any],
    platform_label: str,
) -> None:
    """Render FAQ policy for LLMO with platform constraints."""
    faq_detection = analysis_results.get("faq_detection", {}) or {}
    faq_items = faq_detection.get("items", []) if isinstance(faq_detection, dict) else []
    sources = faq_detection.get("sources", {}) if isinstance(faq_detection, dict) else {}
    validation = faq_detection.get("validation", {}) if isinstance(faq_detection, dict) else {}
    has_faq = bool(faq_items)

    platform_caps = (get_platform_guidance(platform_label) or {}).get("capabilities", {}) or {}
    can_jsonld = platform_caps.get("can_add_jsonld")
    is_ec = analysis_results.get("is_ec")

    _section_title(pdf, "FAQ実装方針（LLMO）")
    _muted(
        pdf,
        "FAQはAI回答で参照されやすい要素ですが、全ページ必須ではありません。"
        "自然な質問があるページだけ実装し、無理な水増しは避けます。",
    )

    base_policy = [
        "有効性: FAQはLLMOで有効（引用候補になりやすい）",
        "前提: 実際の問い合わせ・比較検討で発生する質問のみ採用",
        "禁止: 誇大表現・未検証の断定・本文と不整合な回答は入れない",
    ]
    _bullet_list(pdf, base_policy, max_items=3)

    placement = [
        "配置1: 商品/サービスページの中段〜下段に3〜5問",
        "配置2: CTA直前に短いFAQ（不安解消用）",
        "配置3: 専用FAQページを作成し、関連ページから内部リンク",
    ]
    if is_ec is False:
        placement = [
            "配置1: サービス説明ページの中段〜下段に3〜5問",
            "配置2: 問い合わせ導線の直前に短いFAQ",
            "配置3: 専用FAQページを作成し、主要ページから内部リンク",
        ]
    _bullet_list(pdf, placement, max_items=3)

    if can_jsonld is False:
        _muted(
            pdf,
            "プラットフォーム制約: FAQPageのJSON-LDを直接実装しにくい環境です。"
            "本文Q&Aの明確化を優先し、必要なら自社サイト側で構造化データを補完します。",
        )
    elif can_jsonld == "limited":
        _muted(
            pdf,
            "プラットフォーム制約: FAQPageの実装に制限があります。"
            "対応可能範囲でJSON-LDを設定し、不足分は本文Q&Aで補完します。",
        )
    else:
        _muted(
            pdf,
            "実装方針: FAQ本文に加え、FAQPageのJSON-LDを設定して機械可読性を高めます。",
        )

    if has_faq:
        _muted(
            pdf,
            f"検出状況: 既存FAQを{len(faq_items)}件検出（JSON-LD: {sources.get('json_ld', 0)}件 / HTML: {sources.get('html', 0)}件）。",
        )
        if validation:
            _muted(
                pdf,
                f"整合チェック: {validation.get('consistent_count', 0)}/{validation.get('checked', 0)}件が本文と整合 "
                f"（レベル: {validation.get('consistency_level', '-')}, 要確認: {validation.get('suspicious_count', 0)}件）。",
            )
            for rec in (validation.get("recommendations", []) or [])[:2]:
                _muted(pdf, f"・{rec}")
    else:
        _muted(
            pdf,
            "検出状況: 既存FAQは未検出です。ページ目的に沿う3〜5問から先行実装を推奨します。",
        )


def generate_seo_aio_pdf_report(
    analysis_results: Dict[str, Any],
    output_path: str,
    use_phase4_layout: bool = True,
) -> Dict[str, Any]:
    """拡張版PDF生成器（fpdf2）- 詳細セクション付き"""
    if not analysis_results:
        return {"success": False, "error": "分析結果がありません"}

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    _setup_fonts(pdf)

    url = analysis_results.get("url", "N/A")
    integrated = analysis_results.get("integrated_results", {}) or {}
    aio_results = analysis_results.get("aio_results", {}) or {}
    seo_results = analysis_results.get("seo_results", {}) or {}
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ===== Page 1: 表紙 =====
    _set_title(pdf, "SEO/AIO 統合分析レポート")
    _muted(pdf, f"対象URL: {url}\n生成日時: {generated_at}")

    # EC判定
    is_ec = analysis_results.get("is_ec")
    if is_ec is not None:
        ec_label = "ECサイト" if is_ec else "非ECサイト"
        ec_reason = analysis_results.get("ec_detection_reason", "")
        _muted(pdf, f"サイト種別: {ec_label}" + (f"（{ec_reason}）" if ec_reason else ""))

    pdf.ln(6)
    _section_title(pdf, "スコア")
    _two_col_kv(
        pdf,
        [
            ("統合スコア", f"{round(integrated.get('integrated_score', 0))}/100"),
            ("SEO", f"{round(integrated.get('seo_score', 0))}/100"),
            ("AIO", f"{round(integrated.get('aio_score', 0))}/100"),
            ("法務", f"{round(integrated.get('legal_score', 0))}/100" if integrated.get("legal_score") is not None else "未算出"),
        ],
    )

    # ===== Page 2: 総合サマリー（経営層） =====
    pdf.add_page()
    _section_title(pdf, "総合サマリー")
    _card(pdf, "状況サマリー", _build_exec_summary(analysis_results))

    improvements = _extract_improvements(analysis_results)
    if improvements:
        pdf.ln(4)
        _section_title(pdf, "優先改善ポイント（Top5）")
        _bullet_list(pdf, improvements, max_items=5)
    else:
        pdf.ln(4)
        _section_title(pdf, "優先改善ポイント")
        _no_data_notice(pdf, "改善ポイント")

    # ===== Page 3-4: 非エンジニア向け（リライト込み） =====
    pdf.add_page()
    _section_title(pdf, "非エンジニア向けレポート（1/2）")
    deep_recs = analysis_results.get("deep_recommendations", {}) or {}
    title_rewrites = deep_recs.get("title_rewrites", []) or []
    desc_rewrites = deep_recs.get("description_rewrites", []) or []
    current_title = (seo_results.get("basics", {}) or {}).get("title", "") or ""
    current_desc = (seo_results.get("basics", {}) or {}).get("meta_description", "") or ""

    _rewrite_block(pdf, "タイトル改善（提案1）", current_title, (title_rewrites[0] if title_rewrites else ""), "")
    _rewrite_block(pdf, "メタディスクリプション改善（提案1）", current_desc, (desc_rewrites[0] if desc_rewrites else ""), "")

    # 本文リライト（1件だけ）
    suggestions = (aio_results.get("rewrite_suggestions", []) or [])
    if suggestions:
        s0 = suggestions[0] or {}
        _rewrite_block(
            pdf,
            "本文リライト（Before/After）",
            str(s0.get("original_segment", "") or ""),
            str(s0.get("improved_segment", "") or ""),
            str(s0.get("reason", "") or ""),
            max_chars=320,
        )
    else:
        _no_data_notice(pdf, "本文リライト案")

    # Page 4: Non-engineer 2/2 (actions + platform business steps)
    pdf.add_page()
    _section_title(pdf, "非エンジニア向けレポート（2/2）")
    business = (deep_recs.get("business", []) or [])
    if business:
        items = []
        for rec in business[:6]:
            title = rec.get("title") or "提案"
            action = rec.get("recommended_action") or ""
            text = f"{title}: {action}".strip(": ")
            if text:
                items.append(text)
        if items:
            _section_title(pdf, "優先提案（今日からできる）")
            _bullet_list(pdf, items, max_items=6)
    else:
        _no_data_notice(pdf, "非エンジニア向け提案")

    platform_guidance = analysis_results.get("platform_guidance", {}) or {}
    platform_label = platform_guidance.get("label") or (analysis_results.get("platform", {}) or {}).get("effective") or "未検出"
    business_steps = platform_guidance.get("business_steps", []) or []
    _section_title(pdf, f"プラットフォーム別（{platform_label}）操作ガイド")
    if business_steps:
        _bullet_list(pdf, [str(s) for s in business_steps[:8]], max_items=8)
    else:
        _no_data_notice(pdf, "操作ガイド")

    # ===== Page 5-7: エンジニア向け（プラットフォーム別） =====
    pdf.add_page()
    _section_title(pdf, f"エンジニア向けレポート（1/3）: {platform_label}")
    _render_platform_risk_and_llms(pdf, analysis_results, platform_label)
    pdf.ln(2)
    _render_faq_llmo_policy(pdf, analysis_results, platform_label)

    pdf.add_page()
    _section_title(pdf, f"エンジニア向けレポート（2/3）: {platform_label}")
    technical_steps = platform_guidance.get("technical_steps", []) or []
    if technical_steps:
        _section_title(pdf, "実装手順（上位）")
        _bullet_list(pdf, [str(s) for s in technical_steps[:10]], max_items=10)
    else:
        _no_data_notice(pdf, "実装手順")

    schema_validation = aio_results.get("schema_validation") or {}
    found_types = (schema_validation.get("found_types") or []) if isinstance(schema_validation, dict) else []
    missing = (schema_validation.get("missing_recommended") or []) if isinstance(schema_validation, dict) else []
    _section_title(pdf, "構造化データ（要点）")
    _two_col_kv(pdf, [("検出", ", ".join(found_types[:8]) if found_types else "なし"), ("推奨未設定", ", ".join(missing[:8]) if missing else "なし")])

    # Page 7: Engineer 3/3 (SEO/AIO tech summary)
    pdf.add_page()
    _section_title(pdf, "エンジニア向けレポート（3/3）")
    seo_scores = seo_results.get("scores", {}) or {}
    aio_scores = aio_results.get("scores", {}) or {}
    _section_title(pdf, "主要スコア内訳")
    rows = []
    if seo_scores:
        rows.append(("SEO: タイトル", str(seo_scores.get("title", "N/A"))))
        rows.append(("SEO: 見出し", str(seo_scores.get("headings", "N/A"))))
        rows.append(("SEO: 画像", str(seo_scores.get("images", "N/A"))))
    if aio_scores:
        rows.append(("AIO: 構造化", str(aio_scores.get("structured_data", "N/A"))))
        rows.append(("AIO: E-E-A-T", str(aio_scores.get("eeat", "N/A"))))
        rows.append(("AIO: 引用適性", str(aio_scores.get("citation_potential", "N/A"))))
    if rows:
        _two_col_kv(pdf, [(k, f"{v}/100" if v not in ("N/A", "") else "N/A") for k, v in rows])
    else:
        _no_data_notice(pdf, "技術指標")

    internal_links = analysis_results.get("internal_link_summary") or {}
    if internal_links:
        _section_title(pdf, "内部リンク（要点）")
        _two_col_kv(
            pdf,
            [
                ("総ページ", str(internal_links.get("total_pages", 0))),
                ("孤立ページ", str(internal_links.get("orphan_count", 0))),
                ("低リンク", str(internal_links.get("low_link_count", 0))),
            ],
        )

    # ===== Page 8: 法務（OK/NG + 根拠） =====
    pdf.add_page()
    _section_title(pdf, "法務チェック（OK/NG + 根拠）")
    headline, legal_items = _legal_engineer_notes(analysis_results)
    _muted(pdf, headline)
    if legal_items:
        _bullet_list(pdf, legal_items, max_items=8)
    else:
        _muted(pdf, "重大な問題は検出されませんでした。")

    pdf.output(output_path)
    return {"success": True, "pages": pdf.page_no(), "path": output_path}
