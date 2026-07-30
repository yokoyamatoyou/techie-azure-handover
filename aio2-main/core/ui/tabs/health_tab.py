# -*- coding: utf-8 -*-
"""Site health tab rendering logic."""

import re
from typing import Any, Dict

from nicegui import ui

from core.legal_checks.non_ec_summary import (
    build_non_ec_legal_summary,
    format_non_ec_legal_summary,
    is_ec_site,
)
from core.platform_detector import PlatformDetector
from core.platform_guidance import build_platform_risk_profile
from core.site_health.advice_generator import HealthAdviceGenerator
from core.site_health.maintenance_risk import build_maintenance_risk_summary
from core.structured_data.platform_guides import get_implementation_guide
from core.ui.components import create_status_card
from core.ui.detail_panels import (
    render_detail_panel,
    render_tokushoho_detection_info,
)
from core.ui.help_system import render_faq_section


def _normalize_status(status: Any) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"fail", "要対応"}:
        return "fail"
    if normalized in {"warn", "warning", "注意", "要確認"}:
        return "warn"
    if normalized in {"pass", "ok", "通過", "問題なし"}:
        return "pass"
    if normalized in {"reference", "info", "参考"}:
        return "reference"
    return "reference"


def _status_label(status: Any) -> str:
    return {
        "fail": "要対応",
        "warn": "注意",
        "pass": "通過",
        "reference": "参考",
    }.get(_normalize_status(status), "参考")


def _status_badge_classes(status: Any) -> str:
    return {
        "fail": "bg-red-50 text-red-700",
        "warn": "bg-amber-50 text-amber-700",
        "pass": "bg-emerald-50 text-emerald-700",
        "reference": "bg-slate-100 text-slate-600",
    }.get(_normalize_status(status), "bg-slate-100 text-slate-600")


def _status_sort_key(status: Any) -> int:
    return {
        "fail": 0,
        "warn": 1,
        "pass": 2,
        "reference": 3,
    }.get(_normalize_status(status), 9)


def _merge_status(*statuses: Any) -> str:
    normalized = [_normalize_status(status) for status in statuses if str(status or "").strip()]
    if "fail" in normalized:
        return "fail"
    if "warn" in normalized:
        return "warn"
    if "pass" in normalized:
        return "pass"
    return "reference"


def _render_url_instruction_screen(analysis_result: Dict[str, Any]) -> None:
    screen = analysis_result.get("url_instruction_screen") or {}
    excluded = (analysis_result.get("crawl_strategy") or {}).get("excluded_untrusted_instruction_urls") or []
    observations = [screen] + [item for item in excluded if isinstance(item, dict)]
    suspicious = [item for item in observations if item.get("status") == "suspicious_untrusted_instruction"]
    with ui.card().classes("card p-4 w-full"):
        ui.label("URL文字列の安全確認").classes("card-title")
        if not suspicious:
            ui.label("確認したURL文字列には、AIへの不審な指示と判断できるパターンは観測できませんでした。").classes("card-hint")
            ui.label("これはURL文字列の限定的な確認であり、ページ本文などの不信データの安全性を保証するものではありません。").classes("card-hint text-xs")
            return
        ui.label("URL文字列に、AIへの不審な指示に見えるパターンを観測しました。プロンプトインジェクションとは断定せず、追加取得・AI入力から除外しています。").classes("card-hint text-amber-800")
        for item in suspicious[:4]:
            labels = {"instruction_override_request": "既存指示の無効化要求", "ai_prompt_direct_address": "AIへの直接呼びかけ", "secret_exfiltration_request": "秘密情報の取得要求", "external_send_request": "外部送信要求", "tool_or_fetch_instruction": "ツール・追加取得の要求", "zero_width_obfuscation": "不可視文字", "bidi_control": "表示方向制御文字", "confusable_instruction_token": "見た目が似た文字"}
            signals = [labels.get(str(value), "難読化または命令パターン") for value in (item.get("signals") or [])]
            ui.label("・検出箇所: " + ("リンク候補" if item.get("location") == "link_text" else "URLの一部") + " / " + "、".join(signals[:3])).classes("card-hint text-xs")


def _render_maintenance_cards(analysis_result: Dict[str, Any]) -> None:
    maintenance = build_maintenance_risk_summary(analysis_result)
    cards = [item for item in (maintenance.get("cards") or []) if isinstance(item, dict)]
    if not cards:
        return
    ui.label("保守・更新管理").classes("text-xl font-bold mt-6")
    if maintenance.get("summary"):
        ui.label(str(maintenance.get("summary"))).classes("card-hint text-xs")
    with ui.column().classes("w-full gap-3 mt-2"):
        for card in cards:
            status_key = _normalize_status(card.get("status"))
            with ui.column().classes("w-full border-l-4 border-amber-300 pl-3 py-2 gap-1"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.label(str(card.get("status_label") or _status_label(status_key))).classes(
                        f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(status_key) }"
                    )
                    ui.label(str(card.get("title") or "保守確認")).classes("card-sub font-bold")
                detail = str(card.get("summary") or card.get("detail") or "").strip()
                if detail:
                    ui.label(detail).classes("card-hint text-xs")
                metrics = card.get("metrics") or {}
                metric_bits = []
                for label, key in (
                    ("フォーム数", "form_count"),
                    ("個人情報項目数", "personal_fields"),
                    ("CSRF/nonce痕跡", "csrf_or_nonce"),
                    ("privacy同意", "privacy_consent"),
                    ("captcha痕跡", "captcha"),
                    ("ファイルアップロード", "file_upload"),
                    ("機微情報の文脈", "sensitive_context"),
                    ("外部送信先", "external_action"),
                    ("確認した送信先", "checked_endpoints"),
                    ("問題のある送信先", "problem_endpoints"),
                ):
                    if key in metrics:
                        metric_bits.append(f"{label}: {metrics.get(key)}")
                if metric_bits:
                    ui.label(" / ".join(metric_bits)).classes("card-hint text-xs")
                for bullet in (card.get("bullets") or [])[:3]:
                    ui.label(f"・{bullet}").classes("card-hint text-xs")


def _format_platform_label(value: Any) -> str:
    text = str(value or "").strip()
    replacements = {
        "未検出": "判定なし",
        "カスタム/その他": "その他 / 独自設定",
        "その他": "その他 / 独自設定",
    }
    return replacements.get(text, text) or "判定なし"


def _compact_marketer_excerpt(value: Any, *, limit: int = 160) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    text = text.lstrip(".… ").strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    shortened = text[:limit]
    for delimiter in ("。", "、", ")", " "):
        cut = shortened.rfind(delimiter)
        if cut >= int(limit * 0.6):
            return shortened[: cut + (1 if delimiter != " " else 0)].strip() + "…"
    return shortened.rstrip() + "…"


def _resolve_platform_label(analysis_result: Dict[str, Any]) -> str:
    """Resolve effective platform label with fallback to detector."""
    platform_meta = analysis_result.get("platform", {}) or {}
    platform_guidance = analysis_result.get("platform_guidance", {}) or {}
    platform_label = platform_guidance.get("label") or platform_meta.get("effective") or ""
    if platform_label:
        return _format_platform_label(platform_label)

    html = analysis_result.get("html", "") or ""
    detector = PlatformDetector()
    platform_key = detector.detect(html)
    return _format_platform_label(detector.get_platform_info(platform_key).get("name", "未検出"))


def _get_llms_status(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract llms.txt status from analysis payloads."""
    aio_results = analysis_result.get("aio_results", {}) or {}
    llms_payload = aio_results.get("llms_txt", {}) or {}
    if not isinstance(llms_payload, dict):
        llms_payload = {}
    return {
        "exists": bool(llms_payload.get("exists")),
        "found_paths": llms_payload.get("found_paths", []) or [],
        "checked_paths": llms_payload.get("checked_paths", []) or [],
    }


def _render_link_health_section(link_health: Dict[str, Any]) -> None:
    """Render internal-link health section."""
    if not link_health:
        return

    score = float(link_health.get("health_score", 0.0) or 0.0)
    diagnosis = str(link_health.get("diagnosis", "") or "")
    orphan_count = int(link_health.get("orphan_count", 0) or 0)
    known_pages = int(link_health.get("total_known_pages", 0) or 0)
    analyzed_pages = int(link_health.get("total_analyzed_pages", 0) or 0)
    avg_depth = float(link_health.get("avg_depth", 0.0) or 0.0)
    audited_targets = int(link_health.get("audited_target_count", 0) or 0)
    broken_count = int(link_health.get("broken_target_count", 0) or 0)
    redirected_count = int(link_health.get("redirected_target_count", 0) or 0)
    canonical_mismatch_count = int(link_health.get("canonical_mismatch_count", 0) or 0)
    noindex_count = int(link_health.get("noindex_target_count", 0) or 0)
    hub_pages = list(link_health.get("hub_pages", []) or [])

    color = "green" if score >= 80 else ("amber" if score >= 50 else "red")
    with ui.card().classes("card diagnostic-note-card p-4 w-full"):
        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
            ui.label("内部リンク構造").classes("card-title")
            ui.label("健康診断").classes("fixed-chip")
        with ui.row().classes("items-center gap-3 w-full"):
            ui.linear_progress(
                value=max(0.0, min(score / 100.0, 1.0)),
                size="10px",
                show_value=False,
                color=color,
            ).classes("w-32")
            ui.label(f"{score:.0f}点").classes("card-sub font-bold")
        if diagnosis:
            ui.label(diagnosis).classes("card-sub")
        ui.label(
            f"把握ページ: {known_pages}件 / クロール分析ページ: {analyzed_pages}件 / 平均深度: {avg_depth:.2f}"
        ).classes("card-hint")
        if audited_targets > 0:
            ui.label(
                f"リンク先監査: {audited_targets}件 / エラー {broken_count}件 / リダイレクト {redirected_count}件 / canonical不整合 {canonical_mismatch_count}件 / noindex {noindex_count}件"
            ).classes("card-hint")
        if orphan_count > 0:
            ui.label(f"孤立ページ（推定）: {orphan_count}件").classes("card-hint text-orange-600")
        if hub_pages:
            ui.label("ハブページ（被リンク上位）").classes("card-hint")
            for hub in hub_pages[:3]:
                ui.label(f"・{hub}").classes("card-hint text-blue-600")
        for title, items in [
            ("エラーリンク候補", link_health.get("broken_targets", []) or []),
            ("リダイレクトリンク候補", link_health.get("redirected_targets", []) or []),
            ("canonical不整合候補", link_health.get("canonical_mismatches", []) or []),
            ("noindexリンク先候補", link_health.get("noindex_targets", []) or []),
        ]:
            if not items:
                continue
            ui.label(title).classes("card-hint")
            for item in items[:3]:
                detail = (
                    item.get("detail")
                    or item.get("final_url")
                    or item.get("canonical_url")
                    or item.get("url")
                    or ""
                )
                ui.label(f"・{item.get('url', '')} -> {detail}".strip(" ->")).classes("card-hint text-orange-700")
        ui.label("※クロール4ページと sitemap メタデータに基づく推定です。").classes("card-hint text-xs text-gray-500")
    ui.separator()


def _render_seo_discovery_section(seo_results: Dict[str, Any]) -> None:
    if not seo_results:
        return

    technical = seo_results.get("technical", {}) or {}
    structure = seo_results.get("structure", {}) or {}
    web_vitals = seo_results.get("web_vitals", {}) or {}
    rows = []

    if technical.get("mobile_parity") or technical.get("page_experience"):
        detail = []
        if web_vitals.get("lcp_ms") is not None:
            detail.append(f"LCP {float(web_vitals.get('lcp_ms')):.0f}ms")
        if web_vitals.get("cls_score") is not None:
            detail.append(f"CLS {float(web_vitals.get('cls_score')):.3f}")
        summary = str((technical.get("page_experience") or {}).get("summary") or "")
        if summary:
            detail.append(summary)
        rows.append(
            {
                "title": "モバイル / ページ体験",
                "detail": " / ".join(detail),
                "status": _merge_status(
                    (technical.get("mobile_parity") or {}).get("status"),
                    (technical.get("page_experience") or {}).get("status"),
                ),
            }
        )

    if technical.get("media_discovery"):
        rows.append(
            {
                "title": "画像 / 動画の発見性",
                "detail": str((technical.get("media_discovery") or {}).get("summary") or ""),
                "status": _normalize_status((technical.get("media_discovery") or {}).get("status")),
            }
        )

    if structure.get("link_quality"):
        rows.append(
            {
                "title": "リンク品質",
                "detail": str((structure.get("link_quality") or {}).get("summary") or ""),
                "status": _normalize_status((structure.get("link_quality") or {}).get("status")),
            }
        )

    if not rows:
        return

    rows = sorted(rows, key=lambda row: (_status_sort_key(row.get("status")), str(row.get("title") or "")))
    with ui.card().classes("card implementation-note-card p-4 w-full"):
        with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
            ui.label("実装確認メモ").classes("card-title")
            ui.label("実装メモ").classes("fixed-chip")
        ui.label("健康診断の補足として、設定変更が必要な項目だけをまとめています。").classes("card-hint text-xs")
        for row in rows:
            with ui.card().classes("card p-4 w-full mt-2"):
                with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                    ui.label(str(row.get("title") or "-")).classes("card-sub font-bold")
                    ui.label(_status_label(row.get("status"))).classes(
                        f"text-xs px-2 py-1 rounded inline-flex { _status_badge_classes(row.get('status')) }"
                    )
                if row.get("detail"):
                    ui.label(str(row.get("detail"))).classes("card-hint")
    ui.separator()


def render_legal_section(analysis_result: Dict[str, Any], *, leading_separator: bool = True) -> None:
    """Render legal checks section shared by site health and legal tabs."""
    legal_checks = analysis_result.get("legal_checks", {})
    if not legal_checks:
        return

    url_type_meta = analysis_result.get("url_type", {}) or {}
    is_ec = is_ec_site(url_type_meta)

    if leading_separator:
        ui.separator()
    ui.label("法的リスクチェック").classes("card-title")
    legal_summary = analysis_result.get("legal_summary") or {}
    if legal_summary.get("headline"):
        ui.label(legal_summary["headline"]).classes("card-hint")

    non_ec_summary = build_non_ec_legal_summary(analysis_result)
    if non_ec_summary:
        formatted = format_non_ec_legal_summary(non_ec_summary, max_len=40, max_actions=2)
        with ui.card().classes("p-4 w-full"):
            ui.label(formatted.get("title", "非EC向け 表示アドバイス・信頼性チェック")).classes("card-title")
            summary_text = formatted.get("summary")
            if summary_text:
                ui.label(summary_text).classes("card-sub")
            for line in formatted.get("items", []):
                ui.label(f"・{line}").classes("card-hint")
            for action in formatted.get("actions", []):
                ui.label(f"→ {action}").classes("card-hint")
            note = formatted.get("note")
            if note:
                ui.label(note).classes("card-hint text-xs")

    premiums = legal_checks.get("premiums_labeling", {}).get("formatted", {})
    if premiums:
        create_status_card(
            premiums.get("title", "景品表示法チェック"),
            premiums.get("status", ""),
            premiums.get("status_color", "info"),
            premiums.get("items", []),
        )
        if premiums.get("recommendations"):
            render_detail_panel("景品表示法の推奨事項", [{"issue": r} for r in premiums.get("recommendations", [])])

    stealth = legal_checks.get("stealth_marketing", {}).get("formatted", {})
    if stealth:
        create_status_card(
            stealth.get("title", "ステマ規制チェック"),
            stealth.get("status", ""),
            stealth.get("status_color", "info"),
            stealth.get("items", []),
            summary=stealth.get("summary", ""),
        )
        if stealth.get("recommendations"):
            render_detail_panel("ステマ規制の推奨事項", [{"issue": r} for r in stealth.get("recommendations", [])])

    commercial = legal_checks.get("commercial_transaction", {}).get("formatted", {})
    if commercial and is_ec:
        create_status_card(
            commercial.get("title", "特定商取引法チェック"),
            commercial.get("status", ""),
            commercial.get("status_color", "info"),
            commercial.get("items", []),
            summary=f"適合率: {commercial.get('compliance_rate', 0)}",
        )
        ec_notice = commercial.get("ec_notice")
        if ec_notice:
            ui.label(ec_notice).classes("card-hint text-xs")
        else:
            ec_detection = commercial.get("ec_detection", {}) or {}
            if ec_detection:
                ui.label(
                    f"EC判定: {ec_detection.get('note', '')}（信頼度: {ec_detection.get('confidence', 'low')}）"
                ).classes("card-hint text-xs")
        render_tokushoho_detection_info(commercial)

        if commercial.get("recommendations"):
            render_detail_panel("特定商取引法の推奨事項", [{"issue": r} for r in commercial.get("recommendations", [])])

    ui.separator()

    consumer_protection = legal_checks.get("consumer_protection", {})
    lawyer_report = consumer_protection.get("lawyer_report", [])

    # サイト種別に応じてフィルタリング
    if lawyer_report:
        from core.legal_checks.lawyer_perspective import filter_issues_by_site_type
        effective_type = url_type_meta.get("effective") or ""
        lawyer_report = filter_issues_by_site_type(lawyer_report, effective_type, is_ec)

    if lawyer_report:
        section_title = "専門家による法的分析" if is_ec else "サイト改善の参考情報"
        ui.label(section_title).classes("card-title")

        if is_ec:
            ui.label("ECサイトに必要な法的表示を確認しています。各項目の「修正方法」を参考に改善してください。").classes("card-hint text-xs text-gray-500")
        else:
            ui.label("このサイトはECサイトではないため、法的義務はありません。ユーザビリティ向上の参考としてご確認ください。").classes("card-hint text-xs text-gray-500")

        for item in lawyer_report[:5]:
            with ui.card().classes("card p-4 w-full"):
                # タイトルと重要度
                title = item.get("title", "指摘事項")
                severity = item.get("severity", "info")
                severity_colors = {"high": "text-red-600", "warning": "text-orange-600", "info": "text-blue-600"}
                severity_labels = {"high": "重要", "warning": "注意", "info": "参考"}

                with ui.row().classes("items-center gap-2"):
                    ui.badge(severity_labels.get(severity, "参考")).classes(f"text-xs {severity_colors.get(severity, 'text-blue-600')}")
                    ui.label(title).classes("card-sub font-bold")

                # チェック対象（何を分析したか）
                what_is_checked = item.get("what_is_checked", "")
                if what_is_checked:
                    ui.label(f"チェック対象: {what_is_checked}").classes("card-hint text-xs text-gray-600")

                # 該当箇所の表示
                location = item.get("location", "")
                detail = item.get("detail", "")
                if location or detail:
                    with ui.row().classes("items-start gap-2 bg-amber-50 p-2 rounded mt-2"):
                        ui.icon("place").classes("text-amber-600 text-sm")
                        with ui.column().classes("gap-0"):
                            if location:
                                ui.label(f"見つかった場所: {location}").classes("card-hint text-xs text-amber-800 font-bold")
                            if detail:
                                clean_detail = _compact_marketer_excerpt(detail, limit=180)
                                detail_label = "検出内容" if len(clean_detail) <= 60 else "周辺文脈"
                                ui.label(f"{detail_label}: {clean_detail}").classes("card-hint text-xs text-amber-700")

                # 弁護士コメント（法的リスク）
                comment = item.get("lawyer_comment", "")
                if comment:
                    ui.label(f"⚠️ {comment}").classes("card-sub text-red-700 mt-1")

                # 法的根拠
                legal_basis = item.get("legal_basis", "")
                if legal_basis:
                    ui.label(f"📜 法的根拠: {legal_basis}").classes("card-hint text-xs text-gray-600")

                # ベストプラクティスと修正方法
                best_practice = item.get("best_practice", "")
                bad_example = item.get("bad_example", "")
                good_example = item.get("good_example", "")
                how_to_fix = item.get("how_to_fix", "")

                if best_practice or how_to_fix or bad_example or good_example:
                    with ui.column().classes("bg-green-50 p-3 rounded mt-2 gap-1"):
                        if best_practice:
                            ui.label(f"✅ ベストプラクティス: {best_practice}").classes("card-hint text-xs text-green-800 font-bold")

                        if bad_example or good_example:
                            with ui.row().classes("gap-4 mt-1"):
                                if bad_example:
                                    with ui.column().classes("gap-0"):
                                        ui.label("❌ 悪い例:").classes("card-hint text-xs text-red-600 font-bold")
                                        ui.label(bad_example).classes("card-hint text-xs text-red-700 bg-red-100 p-1 rounded")
                                if good_example:
                                    with ui.column().classes("gap-0"):
                                        ui.label("✅ 良い例:").classes("card-hint text-xs text-green-600 font-bold")
                                        ui.label(good_example).classes("card-hint text-xs text-green-700 bg-green-100 p-1 rounded")

                        if how_to_fix:
                            ui.label(f"🔧 修正方法: {how_to_fix}").classes("card-sub text-xs text-green-800 mt-1")

        ui.separator()


def render_health_tab(analysis_result: Dict[str, Any], display_mode: str, *, include_legal: bool = True) -> None:
    """Render the site health tab."""
    if not analysis_result:
        ui.label("サイトヘルス分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
        return

    site_health = analysis_result.get("site_health", {})
    if not site_health:
        ui.label("サイトヘルス分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
        return

    advanced = display_mode == "advanced"
    url_type_meta = analysis_result.get("url_type", {}) or {}
    effective_type = url_type_meta.get("effective") or ""
    is_ec = is_ec_site(url_type_meta)

    advice_generator = HealthAdviceGenerator()
    ogp_score = site_health.get("ogp", {}).get("formatted", {}).get("score", 100)
    security_score = site_health.get("security", {}).get("formatted", {}).get("score", 100)
    accessibility_score = site_health.get("accessibility", {}).get("formatted", {}).get("score", 100)
    industry_label = analysis_result.get("final_industry", {}).get("primary", "")
    advice_list = advice_generator.generate_personalized_advice(
        site_health=site_health,
        industry=industry_label,
        scores={
            "ogp": ogp_score,
            "security": security_score,
            "accessibility": accessibility_score,
        },
    )
    if advice_list:
        top_advice = advice_list[0]
        with ui.card().classes("card p-4 w-full"):
            ui.label("結論").classes("card-title")
            ui.label(f"優先度1: {top_advice['category']} — {top_advice['action']}").classes("card-sub")
            ui.label("詳しい理由と他の候補は、このタブの一番下「優先改善アドバイス」にまとめています。").classes("card-hint text-xs")
        ui.separator()

    site_type_notes = []
    if effective_type in ("EC", "企業（EC機能あり）"):
        site_type_notes.append("EC向け注意: 特商法ページと景品表示法の表記整合を優先確認")
    if effective_type in ("企業", "企業（EC機能あり）"):
        site_type_notes.append("企業向け注意: 会社情報/採用/プライバシー等の信頼情報を明示")
    if site_type_notes:
        ui.label("サイト種別の注意").classes("card-title")
        for note in site_type_notes[:2]:
            ui.label(f"- {note}").classes("card-hint")

    _render_url_instruction_screen(analysis_result)

    _render_seo_discovery_section(analysis_result.get("seo_results", {}) or {})
    _render_link_health_section(analysis_result.get("link_health_report") or {})

    if include_legal:
        render_legal_section(analysis_result)

    platform_label = _resolve_platform_label(analysis_result)
    platform_risk_profile = build_platform_risk_profile(platform_label)

    ogp_data = site_health.get("ogp", {})
    ogp_formatted = ogp_data.get("formatted", {})
    if ogp_formatted:
        create_status_card(
            ogp_formatted.get("title", "OGPチェック"),
            ogp_formatted.get("status", ""),
            ogp_formatted.get("status_color", "info"),
            ogp_formatted.get("items", []),
            summary=f"スコア: {ogp_formatted.get('score', 0)}点",
        )
        ui.label(
            f"スコア: {ogp_formatted.get('score', 0)}点\n"
            f"ステータス: {ogp_formatted.get('status', '')}"
        ).classes("card-hint whitespace-pre-line")
        preview = ogp_formatted.get("preview", {})
        if preview:
            ui.label("プレビュー").classes("card-title")
            ui.label(f"タイトル: {preview.get('title', '')}").classes("card-sub")
            ui.label(f"説明文: {preview.get('description', '')}").classes("card-sub")
            if preview.get("image"):
                ui.label(f"画像: {preview.get('image')}").classes("card-hint")

        recommendations = ogp_formatted.get("recommendations", [])
        if recommendations:
            rec_items = [{"issue": rec} for rec in recommendations]
            render_detail_panel("OGPの推奨事項", rec_items)

        if advanced:
            platform_suggestions = ogp_data.get("platform_suggestions", {})
            if platform_suggestions:
                with ui.card().classes("mode-advanced w-full"):
                    ui.label("SNS別の最適化").classes("card-title")
                    for platform in platform_suggestions.values():
                        name = platform.get("name", "")
                        notes = platform.get("notes", "")
                        ui.label(f"{name}: {notes}").classes("card-sub")
                        for suggestion in platform.get("suggestions", [])[:3]:
                            ui.label(f"・{suggestion}").classes("card-hint")

        render_faq_section(ogp_formatted.get("faq", []), title="OGPのFAQ")
        ui.separator()

    security_data = site_health.get("security", {})
    security_formatted = security_data.get("formatted", {})
    if security_formatted:
        create_status_card(
            security_formatted.get("title", "セキュリティチェック"),
            security_formatted.get("status", ""),
            security_formatted.get("status_color", "info"),
            security_formatted.get("items", []),
            summary=f"スコア: {security_formatted.get('score', 0)}点",
        )

        if advanced:
            issues = security_formatted.get("issues", [])
            if issues:
                issue_rows = [{"issue": issue.get("issue", issue)} for issue in issues[:6]]
                render_detail_panel("重要ヘッダーの不足", issue_rows)

        security_faq = security_formatted.get("faq", [])
        common_risks = platform_risk_profile.get("common_risks", [])[:3]
        platform_specific_risks = platform_risk_profile.get("platform_specific_risks", [])[:3]
        if security_faq or common_risks or platform_specific_risks:
            with ui.expansion("一般的な補足情報（必要なときだけ確認）", icon="help_outline", value=False).classes("w-full"):
                ui.label("このブロックは一般的な補足です。今回のサイト固有の優先改善より後で確認してください。").classes("card-hint text-xs")
                if security_faq:
                    render_faq_section(security_faq, title="セキュリティFAQ")
                if common_risks or platform_specific_risks:
                    with ui.card().classes("p-4 w-full"):
                        ui.label(
                            f"一般的なリスクメモ（{_format_platform_label(platform_risk_profile.get('label', '未検出'))}）"
                        ).classes("card-title")
                        if common_risks:
                            ui.label("共通リスク").classes("card-sub font-semibold")
                            for item in common_risks:
                                ui.label(f"・{item.get('term')}: {item.get('plain')}").classes("card-sub")
                                ui.label(f"  リスク: {item.get('risk')}").classes("card-hint")
                                ui.label(f"  対処: {item.get('action')}").classes("card-hint")
                        if platform_specific_risks:
                            ui.label("このプラットフォームで特に注意するリスク").classes("card-sub font-semibold mt-2")
                            for item in platform_specific_risks:
                                ui.label(f"・{item.get('term')}: {item.get('plain')}").classes("card-sub")
                                ui.label(f"  リスク: {item.get('risk')}").classes("card-hint")
                                ui.label(f"  対処: {item.get('action')}").classes("card-hint")
        ui.separator()

    accessibility_data = site_health.get("accessibility", {})
    accessibility_formatted = accessibility_data.get("formatted", {})
    if accessibility_formatted:
        accessibility_source = accessibility_data.get("source") or accessibility_formatted.get("detection_source") or "html"
        source_label = "実ブラウザ自動検出" if accessibility_source == "browser" else "HTML自動検出"
        create_status_card(
            accessibility_formatted.get("title", "見やすさ・使いやすさ改善スコア"),
            accessibility_formatted.get("status", ""),
            accessibility_formatted.get("status_color", "info"),
            accessibility_formatted.get("items", []),
            summary=f"改善スコア: {accessibility_formatted.get('score', 0)}点 / {source_label}",
        )
        sample_confidence = accessibility_formatted.get("sample_confidence")
        manual_risk_count = (accessibility_data.get("raw") or {}).get("manual_review_pending_count")
        if sample_confidence or manual_risk_count:
            bits = []
            if sample_confidence:
                bits.append(f"サンプル信頼度: {sample_confidence}")
            if manual_risk_count:
                bits.append(f"手動確認が必要: {manual_risk_count}件")
            ui.label(" / ".join(bits)).classes("card-hint text-xs")
        if accessibility_formatted.get("faq"):
            render_faq_section(accessibility_formatted.get("faq", []), title="自動検出の補足")

        if advanced:
            raw_checks = accessibility_data.get("raw", {}) or {}
            issues = []
            if isinstance(raw_checks, dict) and isinstance(raw_checks.get("issue_groups"), list):
                check_values = raw_checks.get("issue_groups", [])
            elif isinstance(raw_checks, dict):
                check_values = raw_checks.values()
            elif isinstance(raw_checks, list):
                check_values = raw_checks
            else:
                check_values = [raw_checks]

            for check in check_values:
                if isinstance(check, dict):
                    raw_issues = check.get("issues", [])
                elif isinstance(check, list):
                    raw_issues = check
                elif isinstance(check, str):
                    raw_issues = [check]
                else:
                    raw_issues = []

                if not isinstance(raw_issues, list):
                    raw_issues = [raw_issues]

                for issue in raw_issues:
                    if isinstance(issue, dict):
                        issues.append(issue)
                    elif isinstance(issue, str) and issue.strip():
                        issues.append({"issue": issue})
            if issues:
                with ui.card().classes("mode-advanced w-full"):
                    render_detail_panel("自動検出した改善候補", issues[:8])
        ui.separator()

    schema_suggestions = analysis_result.get("schema_suggestions", [])
    if schema_suggestions:
        ui.separator()
        ui.label("構造化データ提案").classes("card-title")
        existing_types = analysis_result.get("schema_existing", {}).get("types", [])
        if existing_types:
            ui.label(f"検出済み: {', '.join(existing_types[:6])}").classes("card-sub")

        for suggestion in schema_suggestions[:6]:
            schema_type = suggestion.get("schema_type", "Schema")
            priority = suggestion.get("priority", "secondary")
            already = suggestion.get("already_present")
            status_text = "設定済み" if already else "未設定"
            ui.label(f"{schema_type}（{priority}）: {status_text}").classes("card-sub")
            explanation = suggestion.get("explanation", {})
            if explanation:
                ui.label(explanation.get("what_is", "")).classes("card-hint")
            if advanced and suggestion.get("template"):
                with ui.expansion(f"{schema_type}の実装例", icon="code").classes("w-full mode-advanced"):
                    ui.code(suggestion.get("template")[:800]).classes("text-xs")

        schema_faq = analysis_result.get("schema_faq", [])
        render_faq_section(schema_faq, title="構造化データのFAQ")

        structured_data = analysis_result.get("structured_data", {}) or {}
        platform_key = platform_label.lower() if platform_label else ""
        detector = PlatformDetector()
        if not platform_key:
            html = analysis_result.get("html", "") or ""
            platform_key = detector.detect(html)
            platform_label = detector.get_platform_info(platform_key).get("name", "未検出")

        with ui.card().classes("p-4 w-full"):
            ui.label(f"検出されたプラットフォーム: {platform_label or '未検出'}").classes("font-bold")

            has_organization = structured_data.get("has_organization")
            if has_organization is None:
                has_organization = any(str(schema_type).lower() == "organization" for schema_type in existing_types)

            if not has_organization:
                guide = get_implementation_guide("Organization", platform_key or "custom")
                with ui.expansion("Organization スキーマの実装方法", icon="unfold_more", value=False).classes("w-full mt-4"):
                    ui.label(
                        f"難易度: {guide.get('difficulty') or '未設定'} | "
                        f"推定時間: {guide.get('estimated_time') or '未設定'}"
                    ).classes("card-sub")
                    ui.label("実装手順:").classes("font-semibold mt-2")
                    for step in guide.get("steps", []):
                        ui.label(step).classes("ml-4 card-sub")
                    if guide.get("limitations"):
                        ui.label("制限事項:").classes("font-semibold mt-2 text-orange-600")
                        for limitation in guide["limitations"]:
                            ui.label(f"- {limitation}").classes("ml-4 text-sm text-orange-600")

    llms_status = _get_llms_status(analysis_result)
    with ui.card().classes("p-4 w-full"):
        status_text = "設置済み" if llms_status.get("exists") else "未設置"
        ui.label(f"AI向け案内ファイル（llms.txt / 任意）: {status_text}").classes("card-title")
        if llms_status.get("exists"):
            found_paths = llms_status.get("found_paths", [])
            if found_paths:
                ui.label(f"検出パス: {', '.join(found_paths[:3])}").classes("card-sub")
        else:
            ui.label("未設置でも公式公開条件の不適合ではありません。必要に応じてAI向け案内として運用します。").classes("card-sub")
        best_practice_exp = ui.expansion("配置ベストプラクティス（参考）", icon="menu_book", value=False).classes("w-full mt-2")
        with best_practice_exp:
            for tip in platform_risk_profile.get("llms_txt_best_practices", [])[:5]:
                ui.label(f"・{tip}").classes("card-hint")


    _render_maintenance_cards(analysis_result)

    if advice_list:
        ui.label("優先改善アドバイス").classes("text-xl font-bold mt-6")
        for i, advice in enumerate(advice_list[:3], 1):
            with ui.card().classes("p-4 bg-gradient-to-r from-blue-50 to-indigo-50 mt-2 w-full"):
                ui.label(f"優先度 {i}: {advice['category']}").classes("font-bold text-lg")
                ui.label(f"なぜ重要: {advice['why']}").classes("mt-2")
                ui.label(f"対策: {advice['action']}").classes("mt-1")
                ui.label(f"期待効果: {advice['expected_impact']}").classes("mt-1 text-green-600")
