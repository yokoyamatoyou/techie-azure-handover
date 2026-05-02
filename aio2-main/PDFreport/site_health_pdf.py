# -*- coding: utf-8 -*-
"""サイトヘルスチェックのPDF統合"""

from typing import Dict, List, Tuple


def _safe_call(pdf, method_name: str, *args, **kwargs):
    method = getattr(pdf, method_name, None)
    if callable(method):
        return method(*args, **kwargs)
    return None


def _collect_scores(site_health: Dict) -> List[float]:
    scores = []
    for key in ("ogp", "security", "accessibility"):
        formatted = site_health.get(key, {}).get("formatted", {})
        score = formatted.get("score")
        if isinstance(score, (int, float)):
            scores.append(float(score))
    return scores


def _overall_status(score: float) -> Tuple[str, str]:
    if score >= 80:
        return "良好", "success"
    if score >= 50:
        return "要確認", "warning"
    return "要対応", "danger"


def _collect_key_issues(site_health: Dict, limit: int = 4) -> List[str]:
    issues = []
    ogp = site_health.get("ogp", {}).get("formatted", {})
    for rec in ogp.get("recommendations", [])[:2]:
        issues.append(rec)

    security = site_health.get("security", {}).get("formatted", {})
    for item in security.get("items", []):
        if "未設定" in item.get("text", ""):
            issues.append(item.get("text", ""))

    accessibility = site_health.get("accessibility", {}).get("formatted", {})
    for item in accessibility.get("items", []):
        if "改善点" in item.get("text", ""):
            issues.append(item.get("text", ""))

    return issues[:limit]


def generate_site_health_summary_page(pdf, result: Dict, mode: str = "simple"):
    """サイトヘルスチェックサマリーページを生成"""
    site_health = result or {}
    scores = _collect_scores(site_health)
    overall_score = int(sum(scores) / len(scores)) if scores else 0
    status_label, status_color = _overall_status(overall_score)

    _safe_call(pdf, "add_page")
    _safe_call(pdf, "add_section_title", "サイトヘルスチェック")
    _safe_call(pdf, "add_subsection_title", "総合サマリー")

    if hasattr(pdf, "add_stat_cards_row"):
        stats = [
            {"label": "総合スコア", "value": f"{overall_score}", "sub_text": "/100"},
            {"label": "ステータス", "value": status_label, "sub_text": ""},
        ]
        pdf.add_stat_cards_row(stats)
    else:
        _safe_call(pdf, "add_info_card", "総合スコア", f"{overall_score}/100")
        _safe_call(pdf, "add_info_card", "ステータス", status_label)

    ogp = site_health.get("ogp", {}).get("formatted", {})
    security = site_health.get("security", {}).get("formatted", {})
    accessibility = site_health.get("accessibility", {}).get("formatted", {})

    _safe_call(pdf, "add_subsection_title", "項目別ステータス")
    for label, formatted in (
        ("OGP/SNS", ogp),
        ("セキュリティ", security),
        ("アクセシビリティ", accessibility),
    ):
        status = formatted.get("status", "未実施")
        score = formatted.get("score", 0)
        _safe_call(pdf, "add_info_card", label, f"{status} / {score}点")

    key_issues = _collect_key_issues(site_health)
    if key_issues:
        _safe_call(pdf, "add_subsection_title", "重要な指摘事項")
        for issue in key_issues:
            if hasattr(pdf, "add_bullet_point"):
                pdf.add_bullet_point(issue)
            else:
                _safe_call(pdf, "add_info_card", "指摘", issue)


def _render_detail_section(pdf, title: str, formatted: Dict, mode: str = "simple"):
    _safe_call(pdf, "add_subsection_title", title)
    status = formatted.get("status", "")
    score = formatted.get("score", "")
    _safe_call(pdf, "add_info_card", "結果", f"{status} / {score}点")

    items = formatted.get("items", [])
    for item in items[:8]:
        text = item.get("text", "")
        hint = item.get("subtext") or item.get("hint") or ""
        if hasattr(pdf, "add_bullet_point"):
            pdf.add_bullet_point(text)
            if hint:
                pdf.add_bullet_point(f"  {hint}")
        else:
            _safe_call(pdf, "add_info_card", "項目", f"{text} {hint}".strip())

    recommendations = formatted.get("recommendations", [])
    if recommendations and mode == "advanced":
        _safe_call(pdf, "add_subsection_title", "推奨対応")
        for rec in recommendations[:4]:
            _safe_call(pdf, "add_info_card", "推奨", rec)


def generate_site_health_detail_pages(pdf, result: Dict, mode: str = "simple"):
    """サイトヘルス詳細ページを生成"""
    site_health = result or {}

    ogp = site_health.get("ogp", {}).get("formatted", {})
    security = site_health.get("security", {}).get("formatted", {})
    accessibility = site_health.get("accessibility", {}).get("formatted", {})

    _safe_call(pdf, "add_page")
    _safe_call(pdf, "add_section_title", "サイトヘルス詳細")

    if ogp:
        _render_detail_section(pdf, "OGP/SNS", ogp, mode)
    if security:
        _render_detail_section(pdf, "セキュリティ", security, mode)
    if accessibility:
        _render_detail_section(pdf, "アクセシビリティ", accessibility, mode)


def generate_action_checklist(pdf, result: Dict, mode: str = "simple"):
    """アクションチェックリストを生成"""
    site_health = result or {}
    actions = []

    ogp = site_health.get("ogp", {}).get("formatted", {})
    actions.extend(ogp.get("recommendations", [])[:3])

    security = site_health.get("security", {}).get("formatted", {})
    for item in security.get("items", []):
        if "未設定" in item.get("text", ""):
            actions.append(item.get("text", ""))

    accessibility = site_health.get("accessibility", {}).get("formatted", {})
    for item in accessibility.get("items", []):
        if "改善点" in item.get("text", ""):
            actions.append(item.get("text", ""))

    if not actions:
        return

    _safe_call(pdf, "add_page")
    _safe_call(pdf, "add_section_title", "アクションチェックリスト")
    for action in actions[:10]:
        if hasattr(pdf, "add_bullet_point"):
            pdf.add_bullet_point(action)
        else:
            _safe_call(pdf, "add_info_card", "対応項目", action)


def generate_site_health_pages(pdf, result: Dict, mode: str = "simple"):
    """サイトヘルスのPDFページを生成（サマリー + 詳細 + チェックリスト）"""
    generate_site_health_summary_page(pdf, result, mode)
    generate_site_health_detail_pages(pdf, result, mode)
    generate_action_checklist(pdf, result, mode)
