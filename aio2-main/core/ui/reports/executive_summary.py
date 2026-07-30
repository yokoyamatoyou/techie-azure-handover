# -*- coding: utf-8 -*-
"""Executive summary section rendering."""

from typing import Any, Dict, List, Callable

from nicegui import ui

from core.site_health.maintenance_risk import technical_foundation_score_from_results


def _title_with_hint(title: str, hint: str, *, title_classes: str = "card-title") -> None:
    with ui.row().classes("items-center gap-2"):
        ui.label(title).classes(title_classes)
        ui.icon("info_outline").classes("text-sm text-[#9B7A60] opacity-70 cursor-help").tooltip(hint)


def _format_summary_value(value: Any) -> str:
    """Normalize internal placeholder values for user-facing summary text."""
    text = str(value or "").strip()
    if text in {"", "自動判定", "未検出", "指定なし"}:
        return ""
    replacements = {
        "カスタム/その他": "その他 / 独自設定",
        "その他": "その他 / 独自設定",
    }
    return replacements.get(text, text)


def _format_business_goal_label(value: Any) -> str:
    """Convert business goal labels to plain-language copy."""
    text = str(value or "").strip()
    replacements = {
        "オーガニック流入増加（SEO優先）": "検索からの流入を増やすこと",
        "AI検索での引用増加（GEO/AIO優先）": "AI検索で見つけられやすくすること",
        "CV率・リード獲得（CTA改善優先）": "問い合わせや成約につなげること",
        "ブランド認知・指名検索強化": "ブランド認知や指名検索を増やすこと",
        "サイト技術健全性（エンジニア優先）": "サイトの基盤を安定させること",
    }
    return replacements.get(text, text)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp_score(value: Any) -> float:
    return max(0.0, min(100.0, _safe_float(value)))


def _average_scores(values: List[Any]) -> float:
    normalized = [_safe_float(value) for value in values if value is not None]
    usable = [value for value in normalized if value > 0]
    if not usable:
        return 0.0
    return _clamp_score(sum(usable) / len(usable))


def _normalize_inline_text(value: Any) -> str:
    text = _format_summary_value(value)
    if not text:
        return ""
    text = " ".join(text.split()).strip()
    return text.lstrip(".… ").strip()


def _compact_marketer_excerpt(value: Any, *, limit: int = 120) -> str:
    text = _normalize_inline_text(value)
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


def _extract_legal_summary_items(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    legal_summary = results.get("legal_summary") or {}

    def _is_actionable_legal_summary_item(item: Dict[str, Any]) -> bool:
        representative = item.get("representative") or {}
        legal_decision = representative.get("legal_decision") or item.get("legal_decision")
        if legal_decision in {"safe_context", "review_needed"}:
            return False
        explicit_issue_text = any(
            _normalize_inline_text(value)
            for value in (
                item.get("title"),
                item.get("summary"),
                item.get("detail"),
                item.get("issue"),
                item.get("reason"),
                item.get("recommendation"),
                representative.get("subtext"),
                representative.get("issue"),
                representative.get("reason"),
                representative.get("detail"),
            )
        )
        status = _normalize_inline_text(
            item.get("status")
            or item.get("compliance_status")
            or representative.get("status")
            or representative.get("status_color")
        ).lower()
        icon = _normalize_inline_text(representative.get("icon"))
        text = _normalize_inline_text(representative.get("text"))
        pass_like_status = status in {"pass", "ok", "success", "通過", "問題なし"}
        pass_like_text = any(token in text for token in ("検出されず", "問題なし", "通過"))

        if pass_like_status and not explicit_issue_text:
            return False
        if icon in {"✓", "✅"} and not explicit_issue_text:
            return False
        if pass_like_text and not explicit_issue_text:
            return False
        return True

    top_issues = [
        item
        for item in (legal_summary.get("top_issues") or [])
        if isinstance(item, dict) and _is_actionable_legal_summary_item(item)
    ]

    def _build_marketer_copy(item: Dict[str, Any], *, default_severity: str) -> Dict[str, Any]:
        representative = item.get("representative") or {}
        phrase = _compact_marketer_excerpt(
            representative.get("text") or representative.get("matched_text"),
            limit=36,
        )
        category = _normalize_inline_text(representative.get("category") or item.get("category"))
        concern = _normalize_inline_text(
            representative.get("subtext")
            or representative.get("issue")
            or representative.get("reason")
            or item.get("title")
            or item.get("detail")
        )
        context = _compact_marketer_excerpt(
            item.get("evidence_summary")
            or representative.get("evidence")
            or representative.get("matched_text")
            or item.get("detail"),
            limit=140,
        )

        if phrase:
            title = f"表現「{phrase}」の確認"
        elif concern:
            title = concern
        elif category:
            title = f"{category}の確認"
        else:
            title = "表現・見せ方の確認"

        summary = concern or (f"{category}に関する確認候補" if category else "表現・見せ方の確認候補")
        if context and context != summary:
            detail = f"気になった点: {summary}\n周辺文脈: {context}"
        else:
            detail = summary or context

        return {
            "title": title,
            "summary": summary,
            "detail": detail,
            "severity": item.get("severity") or default_severity,
        }

    if top_issues:
        return [
            _build_marketer_copy(item, default_severity="warning")
            for item in top_issues
        ]

    fallback_items: List[Dict[str, Any]] = []
    severity_by_bucket = {
        "high_priority": "high",
        "medium_priority": "warning",
        "low_priority": "info",
    }
    for bucket in ("high_priority", "medium_priority", "low_priority"):
        for item in legal_summary.get(bucket) or []:
            if not isinstance(item, dict):
                continue
            if not _is_actionable_legal_summary_item(item):
                continue
            fallback_items.append(
                _build_marketer_copy(
                    item,
                    default_severity=severity_by_bucket.get(bucket, "warning"),
                )
            )
    return fallback_items


def _calculate_legal_clarity_score(results: Dict[str, Any]) -> float:
    legal_checks = results.get("legal_checks", {}) or {}
    if not legal_checks:
        return 0.0

    score = 100.0
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


def _provider_status_score(status: Any) -> float:
    normalized = str(status or "").strip().lower()
    if normalized == "pass":
        return 100.0
    if normalized == "warn":
        return 60.0
    if normalized == "fail":
        return 20.0
    return 50.0


def _build_sitemap_scope_text(sitemap_info: Dict[str, Any]) -> str:
    """Build business-facing sitemap scope text."""
    if not sitemap_info:
        return ""

    total_pages = int(sitemap_info.get("total_urls") or 0)
    if total_pages <= 0:
        return ""

    sampled_count = int(sitemap_info.get("sampled_count") or 0)
    freq = sitemap_info.get("update_frequency") or "不明"

    scope_text = (
        f"サイト規模: 全{total_pages:,}ページ中、メタデータ解析{sampled_count:,}件"
        f"（更新頻度: {freq}）"
    )
    if sitemap_info.get("is_large_site"):
        scope_text += " - 大規模サイトのため分析はサンプル4ページです"
    return scope_text


def _build_sitemap_note_text(sitemap_info: Dict[str, Any]) -> str:
    """Build non-technical sitemap note text."""
    if not sitemap_info:
        return ""
    error_text = str(sitemap_info.get("error") or "")
    if "同一ホストのみ許可" in error_text:
        return "補足: 安全のため、別サーバーにあるサイトマップは対象外にしています。"
    return ""


def _build_site_understanding_items(results: Dict[str, Any], integrated: Dict[str, Any]) -> list[str]:
    """Build short business-facing statements that explain how the site was understood."""
    items: list[str] = []

    url_type = _format_summary_value((results.get("url_type") or {}).get("effective"))
    industry = _format_summary_value((results.get("final_industry") or {}).get("primary"))
    platform = _format_summary_value(
        ((results.get("platform_guidance") or {}).get("label") or "")
        or ((results.get("platform") or {}).get("effective") or "")
    )

    site_line_parts = []
    if url_type:
        site_line_parts.append(f"サイト種別は「{url_type}」")
    if industry:
        site_line_parts.append(f"業種の見立ては「{industry}」")
    if platform:
        site_line_parts.append(f"運用基盤は「{platform}」")
    if site_line_parts:
        items.append("、".join(site_line_parts) + "として分析しました。")

    business_goal = _format_business_goal_label(integrated.get("business_goal"))
    if business_goal and business_goal != "自動判定":
        items.append(f"今回は「{business_goal}」を重視して、改善順を並べています。")

    sitemap_scope_text = _build_sitemap_scope_text(integrated.get("sitemap_info") or {})
    if sitemap_scope_text:
        items.append(sitemap_scope_text + "。")

    return items


def _build_personalized_summary_text(
    results: Dict[str, Any],
    integrated: Dict[str, Any],
    summary: Dict[str, Any],
) -> str:
    """Build a URL-specific lead sentence for the executive summary."""
    url_type = _format_summary_value((results.get("url_type") or {}).get("effective"))
    industry = _format_summary_value((results.get("final_industry") or {}).get("primary"))
    business_goal = _format_business_goal_label(integrated.get("business_goal"))

    seo_score = float(integrated.get("seo_score", 0) or 0)
    aio_score = float(integrated.get("aio_score", 0) or 0)
    geo_score = float(integrated.get("geo_score", 0) or 0)
    legal_score = float(integrated.get("legal_score", 0) or 0)
    if legal_score <= 0:
        legal_score = _calculate_legal_clarity_score(results)

    subject_parts = []
    if industry:
        subject_parts.append(industry)
    if url_type:
        subject_parts.append(url_type)
    subject = " / ".join(subject_parts) if subject_parts else "このURL"

    if geo_score < 45:
        state_phrase = "検索エンジン向けの基礎はある程度ありますが、内部診断上はAI検索で要点を拾われやすい形にはまだ届いていません"
    elif aio_score + 10 < seo_score:
        state_phrase = "従来のSEOよりも、AI検索向けの構造と引用準備の整備が遅れています"
    elif seo_score + 10 < aio_score:
        state_phrase = "AI検索向けの構造は比較的整っており、次は検索流入を取りこぼさないSEO整備が主課題です"
    elif legal_score and legal_score < 60:
        state_phrase = "集客以前に、表示表現や信頼情報の整備を先に見直したい状態です"
    else:
        state_phrase = "検索向けとAI検索向けの基礎は大きく崩れていませんが、先頭の要約と信頼情報の出し方で伸びしろがあります"

    goal_phrase = ""
    if business_goal:
        goal_phrase = f"今回は「{business_goal}」を優先する前提で、初手を並べています。"

    issue_count = int(summary.get("issue_count", 0) or 0)
    issue_phrase = ""
    if issue_count > 0:
        issue_phrase = f"優先して見るべき論点は {issue_count} 件です。"

    return f"{subject}は、{state_phrase}。{goal_phrase}{issue_phrase}".strip()


def _compact_top_action_text(action_text: str, format_reason_text_ui: Callable[[str], str]) -> str:
    """Keep the top action short enough to stay on page 1 in print."""
    formatted = format_reason_text_ui(action_text or "")
    if not formatted:
        return ""

    lines = []
    total_chars = 0
    for raw_line in formatted.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("例"):
            break
        if line.startswith("<"):
            break
        if "例：" in line:
            line = line.split("例：", 1)[0].rstrip()
        if not line:
            continue
        lines.append(line)
        total_chars += len(line)
        if len(lines) >= 3 or total_chars >= 180:
            break

    compact_text = "\n".join(lines).strip()
    if compact_text and compact_text != formatted:
        compact_text += "\n詳細は下の「改善方法」で確認できます。"
    return compact_text or formatted


def _get_provider_readiness(results: Dict[str, Any]) -> Dict[str, Any]:
    aio_results = results.get("aio_results") or {}
    return aio_results.get("provider_readiness") or (aio_results.get("details") or {}).get("provider_readiness") or {}


def _accessibility_score_from_results(results: Dict[str, Any]) -> float:
    """Return saved accessibility score first, then the live site health score."""
    snapshot_score = results.get("accessibility_score_snapshot")
    if snapshot_score is not None:
        return _clamp_score(snapshot_score)

    site_health = results.get("site_health") or {}
    formatted = ((site_health.get("accessibility") or {}).get("formatted") or {})
    if formatted.get("score") is not None:
        return _clamp_score(formatted.get("score"))

    return 0.0


def _build_improvement_map_payload(results: Dict[str, Any], integrated: Dict[str, Any]) -> Dict[str, Any]:
    aio_results = results.get("aio_results") or {}
    aio_scores = aio_results.get("scores") or {}
    aio_details = aio_results.get("details") or {}
    provider_readiness = _get_provider_readiness(results)
    site_health = results.get("site_health") or {}
    link_health = results.get("link_health_report") or {}
    legal_issues = _extract_legal_summary_items(results)
    sitemap_info = integrated.get("sitemap_info") or {}

    seo_score = _clamp_score(integrated.get("seo_score"))
    aio_score = _clamp_score(integrated.get("aio_score"))
    geo_score = _clamp_score(integrated.get("geo_score"))
    citation_score = _clamp_score((aio_scores.get("citation") or {}).get("score"))
    accessibility_score = _accessibility_score_from_results(results)
    eeat_raw = (
        (aio_scores.get("eeat") or {}).get("score")
        or (aio_details.get("inline_eeat") or {}).get("combined_score")
        or 0.0
    )
    trust_score = _clamp_score(_safe_float(eeat_raw) * 10.0)

    provider_values = []
    provider_blockers = 0
    for key in ("google", "openai_search", "perplexity", "claude_search"):
        provider = provider_readiness.get(key) or {}
        status = provider.get("status")
        provider_values.append(_provider_status_score(status))
        if str(status or "").strip().lower() in {"warn", "fail"}:
            provider_blockers += 1
    provider_score = _average_scores(provider_values)

    technical_fallback = _clamp_score((aio_scores.get("technical") or {}).get("score"))
    technical_score = technical_foundation_score_from_results(results) or technical_fallback

    ai_citation_score = _clamp_score((aio_score * 0.55) + (geo_score * 0.25) + (citation_score * 0.20))

    axes = [
        {"label": "SEO基礎", "value": round(seo_score, 1), "hint": "title / meta / 構造 / 発見性"},
        {"label": "AI引用", "value": round(ai_citation_score, 1), "hint": "AI検索向けの要約・引用準備"},
        {"label": "信頼情報", "value": round(trust_score, 1), "hint": "著者・運営者・一次情報の見せ方"},
        {"label": "公開条件", "value": round(provider_score, 1), "hint": "AIサービスごとの到達性"},
        {"label": "保守・技術基盤", "value": round(technical_score, 1), "hint": "リンク健全性 / OGP / セキュリティ / 保守更新"},
        {"label": "見やすさ・使いやすさ", "value": round(accessibility_score, 1), "hint": "自動検出 / 読み上げ / 操作名"},
    ]

    weakest_axes = sorted(axes, key=lambda item: item["value"])[:3]
    alerts = []
    if provider_blockers:
        alerts.append({
            "label": "AI公開条件",
            "detail": f"要確認 {provider_blockers}件",
            "tone": "warn",
        })
    legal_issue_count = len(legal_issues)
    if legal_issue_count:
        alerts.append({
            "label": "表示アドバイス",
            "detail": f"要確認 {legal_issue_count}件",
            "tone": "warn",
        })
    if sitemap_info.get("is_large_site"):
        alerts.append({
            "label": "分析範囲",
            "detail": "本文はサンプル4ページ",
            "tone": "info",
        })
    if not alerts:
        alerts.append({
            "label": "先に確認",
            "detail": "大きな阻害要因は先頭では見えていません",
            "tone": "pass",
        })

    radar_options = {
        "animation": True,
        "tooltip": {"trigger": "item"},
        "radar": {
            "radius": "66%",
            "splitNumber": 4,
            "indicator": [{"name": axis["label"], "max": 100} for axis in axes],
            "axisName": {"color": "#5B5347", "fontSize": 12, "fontWeight": "600"},
            "splitLine": {"lineStyle": {"color": "rgba(130, 113, 94, 0.18)"}},
            "splitArea": {
                "areaStyle": {
                    "color": [
                        "rgba(242, 237, 228, 0.18)",
                        "rgba(242, 237, 228, 0.28)",
                        "rgba(242, 237, 228, 0.38)",
                        "rgba(242, 237, 228, 0.48)",
                    ]
                }
            },
            "axisLine": {"lineStyle": {"color": "rgba(130, 113, 94, 0.24)"}},
        },
        "series": [{
            "type": "radar",
            "data": [{
                "value": [axis["value"] for axis in axes],
                "name": "現在地",
                "symbol": "circle",
                "symbolSize": 7,
                "lineStyle": {"color": "#D96B1F", "width": 3},
                "areaStyle": {"color": "rgba(217, 107, 31, 0.18)"},
                "itemStyle": {"color": "#B95416"},
            }],
        }],
    }

    return {
        "axes": axes,
        "weakest_axes": weakest_axes,
        "alerts": alerts[:3],
        "options": radar_options,
    }


def _render_improvement_map(results: Dict[str, Any], integrated: Dict[str, Any]) -> None:
    payload = _build_improvement_map_payload(results, integrated)
    axes = payload.get("axes") or []
    if not axes:
        return

    ui.label("改善マップ").classes("card-sub font-bold mt-3")
    with ui.row().classes("summary-visual-grid w-full mt-1"):
        with ui.card().classes("card p-4 summary-radar-card"):
            with ui.row().classes("items-center justify-between gap-2 flex-wrap"):
                ui.label("6軸で見た現在地").classes("card-sub font-bold")
                ui.label("圧縮表示").classes("fixed-chip")
            ui.label("へこみが大きい軸ほど、先に手を入れる余地が大きい状態です。").classes("card-hint text-xs")
            chart = ui.echart(payload["options"]).classes("w-full summary-radar-chart")
            chart.style("height: 300px;")
            with ui.row().classes("w-full gap-2 flex-wrap mt-2"):
                for axis in axes:
                    ui.label(f"{axis['label']}: {axis['value']:.0f}").classes("fixed-chip")

        with ui.column().classes("summary-visual-side gap-3"):
            with ui.card().classes("card p-4 w-full"):
                ui.label("先に手を入れる軸").classes("card-sub font-bold")
                for axis in payload.get("weakest_axes") or []:
                    with ui.row().classes("items-center gap-3 w-full mt-2"):
                        with ui.column().classes("gap-0 min-w-[84px]"):
                            ui.label(axis["label"]).classes("card-hint font-semibold")
                            ui.label(axis["hint"]).classes("card-hint text-xs")
                        ui.linear_progress(
                            value=max(0.0, min(axis["value"] / 100.0, 1.0)),
                            size="8px",
                            show_value=False,
                            color="orange",
                        ).classes("flex-1")
                        ui.label(f"{axis['value']:.0f}").classes("summary-axis-score")

            with ui.card().classes("card p-4 w-full"):
                ui.label("先に確認").classes("card-sub font-bold")
                for item in payload.get("alerts") or []:
                    tone = str(item.get("tone") or "info")
                    tone_class = {
                        "warn": "summary-pill-warn",
                        "pass": "summary-pill-pass",
                    }.get(tone, "summary-pill-info")
                    with ui.row().classes("items-start gap-2 w-full mt-2"):
                        ui.label(str(item.get("label") or "")).classes(f"summary-alert-pill {tone_class}")
                        ui.label(str(item.get("detail") or "")).classes("card-hint")


def render_executive_summary(
    results: Dict[str, Any],
    integrated: Dict[str, Any],
    summary: Dict[str, Any],
    decision_actions: List[Dict[str, Any]],
    format_reason_text_ui: Callable[[str], str],
) -> None:
    """Render executive summary for non-technical stakeholders."""

    def _score_status(score: float) -> tuple[str, str]:
        if score >= 80:
            return ("良好", "🟢")
        if score >= 50:
            return ("要改善", "🟡")
        return ("要対応", "🔴")

    _title_with_hint("今回の分析結果", "この欄には今回のURLの検出結果と、先に見てほしい実行項目だけをまとめています。")
    business_goal = _format_business_goal_label(integrated.get("business_goal"))
    if business_goal and business_goal != "自動判定":
        ui.label(f"今回の判断軸: {business_goal}").classes("card-hint text-blue-600 font-bold")

    def _gauge_color(score: float) -> str:
        if score >= 80:
            return "green"
        if score >= 50:
            return "amber"
        return "red"

    # メインスコア 3枚（統合・SEO・AIO）— 円形ゲージ付き
    with ui.row().classes("section-grid"):
        for label, key in (
            ("全体", "integrated_score"),
            ("検索", "seo_score"),
            ("AI検索", "aio_score"),
        ):
            value = float(integrated.get(key, 0))
            status_label, status_symbol = _score_status(value)
            with ui.column().classes("metric items-center gap-1"):
                gauge = ui.circular_progress(
                    value=value, min=0, max=100, size="80px",
                    show_value=False, color=_gauge_color(value),
                )
                gauge.props(f'aria-label="{label}: {value:.0f}点 ({status_label})"')
                with gauge:
                    ui.label(f"{value:.0f}").classes("text-base font-bold")
                ui.label(label).classes("metric-label text-center text-xs")
                ui.label(f"{status_symbol} {status_label}").classes("text-xs text-center").props(
                    f'aria-label="ステータス: {status_label}"'
                )

    # サマリー文（1行）
    summary_text = summary.get("summary_text") or summary.get("summary") or ""
    personalized_text = _build_personalized_summary_text(results, integrated, summary)
    if summary_text:
        summary_text = (
            f"{personalized_text}\n{summary_text}"
            if personalized_text and personalized_text not in summary_text
            else summary_text
        )
    else:
        summary_text = personalized_text or (
            f"統合スコアは{integrated.get('integrated_score', 0):.0f}点。"
            "最優先アクションを先に実行し、主要KPIの改善を狙います。"
        )
    ui.label("このURLの現状").classes("card-sub font-bold mt-2")
    ui.label(summary_text).classes("card-sub whitespace-pre-line")

    # 最優先アクション（1件のみ — 詳細はレポートパネルで確認）
    if decision_actions:
        top = decision_actions[0]
        compact_action = _compact_top_action_text(top.get("action", ""), format_reason_text_ui)
        ui.label("あなたに最初にお願いしたいこと").classes("card-sub font-bold mt-2")
        with ui.card().classes("card p-4 w-full summary-top-action"):
            ui.label(f"最優先の提案: {top['title']}").classes("card-sub font-bold")
            ui.label(compact_action).classes("card-sub whitespace-pre-line")
            ui.label(
                f"担当: {top.get('role', '運用/マーケ')} / 工数: {top.get('effort', '30〜90分')}"
            ).classes("card-hint text-xs text-green-600")
        if len(decision_actions) > 1:
            ui.label(
                f"他 {len(decision_actions) - 1} 件の提案は下の「改善方法」で確認できます。"
            ).classes("card-hint")

    _render_improvement_map(results, integrated)
