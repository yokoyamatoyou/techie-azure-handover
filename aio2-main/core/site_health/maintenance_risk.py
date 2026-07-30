from __future__ import annotations

from typing import Any, Dict, Iterable, List


MAINTENANCE_RISK_ISSUE_IDS = {
    "cms_generator_public",
    "wordpress_rest_users_public",
    "jquery_before_3_5",
    "outdated_frontend_asset",
    "legacy_ie_polyfills",
    "stale_or_static_sitemap",
    "sitemap_unavailable_or_invalid",
    "visible_update_date_old",
    "update_signal_mismatch",
    "form_action_http",
    "form_action_external",
    "password_form_without_https_page",
    "file_upload_form_without_captcha_hint",
    "personal_form_without_privacy_consent_hint",
    "personal_form_without_public_protection_hints",
    "post_form_without_csrf_hint",
    "external_cdn_without_sri",
    "universal_analytics_tag",
    "internal_http_navigation_link",
    "suspicious_external_asset_domain",
    "target_blank_without_noopener",
    "robots_txt_html_fake_200",
    "robots_txt_invalid_or_empty",
    "sitemap_endpoint_html_fake_200",
    "unused_endpoint_fake_200",
    "soft_404_missing_url_200",
    "server_environment_header_exposed",
}

FORM_ISSUE_IDS = {
    "form_action_http",
    "form_action_external",
    "password_form_without_https_page",
    "file_upload_form_without_captcha_hint",
    "personal_form_without_privacy_consent_hint",
    "personal_form_without_public_protection_hints",
    "post_form_without_csrf_hint",
}

FRONTEND_ASSET_ISSUE_IDS = {
    "jquery_before_3_5",
    "outdated_frontend_asset",
    "legacy_ie_polyfills",
}

WORDPRESS_ISSUE_IDS = {
    "cms_generator_public",
    "wordpress_rest_users_public",
    "jquery_before_3_5",
    "outdated_frontend_asset",
    "legacy_ie_polyfills",
}

SITEMAP_ISSUE_IDS = {
    "stale_or_static_sitemap",
    "sitemap_unavailable_or_invalid",
    "update_signal_mismatch",
    "visible_update_date_old",
}

ENDPOINT_HEALTH_ISSUE_IDS = {
    "robots_txt_html_fake_200",
    "robots_txt_invalid_or_empty",
    "sitemap_endpoint_html_fake_200",
    "unused_endpoint_fake_200",
    "soft_404_missing_url_200",
    "server_environment_header_exposed",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else ([] if value in (None, "", {}) else [value])


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _clamp_score(value: Any) -> float:
    return max(0.0, min(_safe_float(value), 100.0))


def _status_label(status: str) -> str:
    return {"fail": "要対応", "warn": "注意", "pass": "通過", "reference": "参考"}.get(status, "参考")


def _status_from_issue_count(count: int) -> str:
    return "warn" if count else "reference"


def _issue_id(issue: Dict[str, Any]) -> str:
    return _text(issue.get("id"))


def _issue_lookup(issues: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    lookup: Dict[str, List[Dict[str, Any]]] = {}
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        lookup.setdefault(_issue_id(issue), []).append(issue)
    return lookup


def _severity_penalty(severity: Any) -> int:
    return {"high": 18, "medium": 10, "low": 4}.get(_text(severity).lower(), 4)


def _security_raw_from_results(results: Dict[str, Any]) -> Dict[str, Any]:
    source = _as_dict(results.get("site_health") if "site_health" in results else results)
    return _as_dict(_as_dict(source.get("security")).get("raw"))


def _public_risks_from_results(results: Dict[str, Any]) -> Dict[str, Any]:
    raw = _security_raw_from_results(results)
    public_risks = _as_dict(raw.get("public_technology_risks"))
    if public_risks:
        return public_risks
    for workspace_key in ("technical_workspace", "implementation_workspace"):
        workspace = _as_dict(results.get(workspace_key))
        for check in _as_list(workspace.get("site_health_checks")):
            if isinstance(check, dict) and _text(check.get("key")) == "security":
                public_risks = _as_dict(check.get("public_technology_risks"))
                if public_risks:
                    return public_risks
    return {}


def maintenance_issues(public_risks: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        issue
        for issue in _as_list(public_risks.get("issues"))
        if isinstance(issue, dict) and _issue_id(issue) in MAINTENANCE_RISK_ISSUE_IDS
    ]


def calculate_maintenance_risk_score(public_risks: Dict[str, Any]) -> int:
    score = 100
    for issue in maintenance_issues(public_risks):
        score -= _severity_penalty(issue.get("severity"))
    return max(0, score)


def maintenance_risk_score_from_results(results: Dict[str, Any]) -> int:
    return calculate_maintenance_risk_score(_public_risks_from_results(results))


def technical_foundation_score_from_results(results: Dict[str, Any]) -> float:
    site_health = _as_dict(results.get("site_health"))
    values: List[float] = []
    link_score = _safe_float(_as_dict(results.get("link_health_report")).get("health_score"))
    if link_score > 0:
        values.append(_clamp_score(link_score))
    for key in ("ogp", "security"):
        formatted = _as_dict(_as_dict(site_health.get(key)).get("formatted"))
        score = _safe_float(formatted.get("score"))
        if score > 0:
            values.append(_clamp_score(score))
    if site_health.get("security") or _public_risks_from_results(results):
        values.append(float(maintenance_risk_score_from_results(results)))
    return round(sum(values) / len(values), 1) if values else 0.0


def _card(key: str, title: str, status: str, summary: str, *, bullets: List[str] | None = None, metrics: Dict[str, Any] | None = None, issue_ids: List[str] | None = None) -> Dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "status": status,
        "status_label": _status_label(status),
        "summary": summary,
        "detail": summary,
        "bullets": [item for item in (bullets or []) if _text(item)][:6],
        "metrics": metrics or {},
        "issue_ids": issue_ids or [],
    }


def _issue_titles(issues: List[Dict[str, Any]], *, limit: int = 4) -> List[str]:
    # Multiple issues can share one title (e.g. the same "古いjQueryが
    # 読み込まれています" finding once per URL it was detected on); collapse
    # those to a single bullet instead of repeating identical text.
    seen: set[str] = set()
    titles: List[str] = []
    for issue in issues:
        text = _text(issue.get("title") or issue.get("issue") or issue.get("detail"))
        if not text or text in seen:
            continue
        seen.add(text)
        titles.append(text)
        if len(titles) >= limit:
            break
    return titles


def _browser_defense_card(security_raw: Dict[str, Any]) -> Dict[str, Any]:
    header_rows = _as_list(_as_dict(security_raw.get("headers")).get("headers"))
    required = {
        "Strict-Transport-Security": "HSTS",
        "Content-Security-Policy": "CSP",
        "X-Frame-Options": "X-Frame-Options",
        "X-Content-Type-Options": "X-Content-Type-Options",
    }
    found = set()
    missing = []
    for row in header_rows:
        if not isinstance(row, dict):
            continue
        header = _text(row.get("header"))
        if header not in required:
            continue
        if _text(row.get("status")) == "ok":
            found.add(header)
        else:
            missing.append(required[header])
    if not header_rows:
        return _card("browser_defense", "ブラウザ防御設定", "reference", "HTTPヘッダーの詳細は保存データにありません。")
    if missing:
        return _card(
            "browser_defense",
            "ブラウザ防御設定",
            "warn",
            "ブラウザ側で攻撃を受けにくくする基本設定が不足しています。サーバー/CDN/CMSの設定を保守会社に確認してください。",
            bullets=[f"不足: {', '.join(missing)}", f"設定確認済み: {', '.join(required[name] for name in found) or 'なし'}"],
        )
    return _card("browser_defense", "ブラウザ防御設定", "pass", "主要なブラウザ防御ヘッダーは公開レスポンス上で確認できます。")


def _forms_card(signals: Dict[str, Any], issue_lookup: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    forms = _as_dict(signals.get("forms"))
    form_rows = [row for row in _as_list(forms.get("forms")) if isinstance(row, dict)]
    form_count = int(forms.get("form_count") or len(form_rows) or 0)
    form_issues = [issue for issue_id in FORM_ISSUE_IDS for issue in issue_lookup.get(issue_id, [])]
    metrics = {
        "form_count": form_count,
        "personal_fields": sum(1 for row in form_rows if row.get("has_personal_fields")),
        "csrf_or_nonce": sum(1 for row in form_rows if row.get("has_csrf_hint")),
        "privacy_consent": sum(1 for row in form_rows if row.get("has_privacy_consent")),
        "captcha": sum(1 for row in form_rows if row.get("has_captcha_hint")),
        "file_upload": sum(1 for row in form_rows if row.get("has_file_upload")),
        "sensitive_context": sum(1 for row in form_rows if row.get("has_sensitive_context")),
        "external_action": sum(1 for row in form_rows if row.get("is_external_action")),
    }
    if form_issues:
        return _card(
            "forms",
            "フォーム確認",
            "warn",
            "フォーム確認: 要確認",
            bullets=_issue_titles(form_issues) + [
                f"フォーム数: {form_count}",
                f"personal fields: {metrics['personal_fields']} / sensitive: {metrics['sensitive_context']} / CSRF/nonce痕跡: {metrics['csrf_or_nonce']} / privacy同意: {metrics['privacy_consent']} / captcha痕跡: {metrics['captcha']} / file upload: {metrics['file_upload']} / external action: {metrics['external_action']}",
            ],
            metrics=metrics,
            issue_ids=[_issue_id(issue) for issue in form_issues],
        )
    if form_count:
        return _card(
            "forms",
            "フォーム確認",
            "reference",
            "外部入力フォームあり。公開HTML上では基本的な対策痕跡があります。フォームプラグイン・スパム対策・保存先権限は保守会社に確認してください。",
            bullets=[
                f"フォーム数: {form_count}",
                f"personal fields: {metrics['personal_fields']} / sensitive: {metrics['sensitive_context']} / CSRF/nonce痕跡: {metrics['csrf_or_nonce']} / privacy同意: {metrics['privacy_consent']} / captcha痕跡: {metrics['captcha']} / file upload: {metrics['file_upload']} / external action: {metrics['external_action']}",
            ],
            metrics=metrics,
        )
    return _card("forms", "フォーム確認", "reference", "公開HTML上では問い合わせ等の外部入力フォームは目立ちません。", metrics=metrics)


def _endpoint_health_card(signals: Dict[str, Any], issue_lookup: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    endpoint_signal = _as_dict(signals.get("endpoint_health"))
    checked = [row for row in _as_list(endpoint_signal.get("checked_endpoints")) if isinstance(row, dict)]
    endpoint_issues = [issue for issue_id in ENDPOINT_HEALTH_ISSUE_IDS for issue in issue_lookup.get(issue_id, [])]
    metrics = {
        "checked_endpoints": len(checked),
        "problem_endpoints": len(endpoint_issues),
    }
    if endpoint_issues:
        endpoint_bullets = _issue_titles(endpoint_issues)
        for issue in endpoint_issues[:3]:
            details = _as_dict(issue.get("evidence_details"))
            url = _text(details.get("url") or issue.get("evidence"))
            status = _text(details.get("status_code"))
            content_type = _text(details.get("content_type"))
            urgency = _text(issue.get("urgency") or details.get("urgency"))
            if url:
                endpoint_bullets.append(
                    f"{url} / HTTP {status or '-'} / Content-Type: {content_type or '-'} / {urgency or '確認候補'}"
                )
        return _card(
            "endpoint_health",
            "公開設定の応答確認",
            "warn",
            "robots.txt、sitemap、存在しないURLの返し方、公開ヘッダーに、保守会社へ確認したい公開サインがあります。",
            bullets=endpoint_bullets,
            metrics=metrics,
            issue_ids=[_issue_id(issue) for issue in endpoint_issues],
        )
    if checked:
        return _card(
            "endpoint_health",
            "公開設定の応答確認",
            "reference",
            "robots.txt、sitemap、存在しないURLの返し方に大きなズレは保存データ上では目立ちません。",
            bullets=[f"確認endpoint数: {len(checked)}"],
            metrics=metrics,
        )
    return _card("endpoint_health", "公開設定の応答確認", "reference", "公開設定の応答確認データはありません。", metrics=metrics)


def build_maintenance_risk_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    security_raw = _security_raw_from_results(results)
    public_risks = _public_risks_from_results(results)
    signals = _as_dict(public_risks.get("signals"))
    issues = maintenance_issues(public_risks)
    lookup = _issue_lookup(issues)
    score = calculate_maintenance_risk_score(public_risks)

    update_issues = [issue for issue_id in ("sitemap_unavailable_or_invalid", "update_signal_mismatch", "visible_update_date_old", "stale_or_static_sitemap") for issue in lookup.get(issue_id, [])]
    update_signal = _as_dict(signals.get("update_signal_consistency"))
    update_summary = "更新通知と見える更新日の大きなズレは保存データ上では目立ちません。"
    if update_issues:
        mismatch = lookup.get("update_signal_mismatch")
        update_summary = _text((mismatch[0] if mismatch else update_issues[0]).get("detail"))
    update_card = _card(
        "update_consistency",
        "更新整合性チェック",
        _status_from_issue_count(len(update_issues)),
        update_summary,
        bullets=_issue_titles(update_issues) + [
            f"visible date: {update_signal.get('visible_date') or _as_dict(signals.get('visible_update_freshness')).get('newest_visible_date') or '-'}",
            f"sitemap lastmod: {update_signal.get('sitemap_lastmod') or _as_dict(signals.get('sitemap')).get('newest_lastmod') or '-'}",
        ],
        issue_ids=[_issue_id(issue) for issue in update_issues],
    )

    generator = _text(signals.get("generator"))
    rest_signal = _as_dict(signals.get("wordpress_rest"))
    public_users = [row for row in _as_list(rest_signal.get("public_users")) if isinstance(row, dict)]
    has_wordpress_surface = bool(
        generator
        or public_users
        or lookup.get("cms_generator_public")
        or lookup.get("wordpress_rest_users_public")
    )
    wordpress_issue_ids = WORDPRESS_ISSUE_IDS if has_wordpress_surface else {"cms_generator_public", "wordpress_rest_users_public"}
    wp_issues = [issue for issue_id in wordpress_issue_ids for issue in lookup.get(issue_id, [])]
    has_admin = any(_text(row.get("slug") or row.get("name")).lower() == "admin" for row in public_users)
    wp_bullets = []
    if generator:
        wp_bullets.append(f"WordPress generator/versionが見える: {generator}")
    if public_users:
        wp_bullets.append(f"REST APIでユーザー名が見える: {len(public_users)}件")
    if has_admin:
        wp_bullets.append("admin が見える場合はログイン攻撃の材料になり得ます。")
    if any(_issue_id(issue) in FRONTEND_ASSET_ISSUE_IDS for issue in wp_issues):
        wp_bullets.append("古いテーマ/プラグイン由来のJSが残っている可能性があります。")
    wp_card = _card(
        "wordpress_maintenance",
        "WordPress保守確認",
        _status_from_issue_count(len(wp_issues) or int(bool(generator or public_users))),
        "WordPressの保守会社に確認すべき公開サインがあります。" if (wp_issues or generator or public_users) else "WordPress特有の公開サインは保存データ上では目立ちません。",
        bullets=wp_bullets or _issue_titles(wp_issues),
        issue_ids=[_issue_id(issue) for issue in wp_issues],
    )

    asset_issues = [issue for issue_id in FRONTEND_ASSET_ISSUE_IDS for issue in lookup.get(issue_id, [])]
    asset_card = _card(
        "frontend_assets",
        "古いフロントエンド資産",
        _status_from_issue_count(len(asset_issues)),
        "古い可能性のあるフロントエンド資産が残っています。テーマ・プラグイン・CDN読み込みの棚卸しをしてください。" if asset_issues else "URLから明確な古いフロントエンド資産は目立ちません。",
        bullets=_issue_titles(asset_issues),
        issue_ids=[_issue_id(issue) for issue in asset_issues],
    )

    sitemap_issues = [issue for issue_id in ("sitemap_unavailable_or_invalid", "stale_or_static_sitemap", "update_signal_mismatch") for issue in lookup.get(issue_id, [])]
    sitemap_card = _card(
        "sitemap_robots",
        "sitemap/robots整合性",
        _status_from_issue_count(len(sitemap_issues)),
        "sitemap.xml、robots.txt内のSitemap指定、CMS/SEOプラグインの生成状態を確認してください。" if sitemap_issues else "sitemap/robots の大きな不整合は保存データ上では目立ちません。",
        bullets=_issue_titles(sitemap_issues),
        issue_ids=[_issue_id(issue) for issue in sitemap_issues],
    )

    cards = [
        update_card,
        _endpoint_health_card(signals, lookup),
        wp_card,
        _forms_card(signals, lookup),
        asset_card,
        _browser_defense_card(security_raw),
        sitemap_card,
    ]

    return {
        "score": score,
        "status": "pass" if score >= 80 else ("warn" if score >= 50 else "fail"),
        "status_label": _status_label("pass" if score >= 80 else ("warn" if score >= 50 else "fail")),
        "summary": f"保守会社に確認すべき公開サイン {len(issues)}件 / 保守更新スコア {score}点",
        "cards": cards,
        "issues": issues,
        "issue_ids": [_issue_id(issue) for issue in issues],
        "public_technology_risks": public_risks,
    }
