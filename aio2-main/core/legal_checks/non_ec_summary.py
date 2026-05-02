# -*- coding: utf-8 -*-
"""Non-EC legal summary builder shared by UI/PDF."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

STATUS_OK = "ok"
STATUS_PARTIAL = "partial"
STATUS_MISSING = "missing"

LABEL_LONG = {
    STATUS_OK: "確認済み",
    STATUS_PARTIAL: "一部確認",
    STATUS_MISSING: "未検出",
}

LABEL_SHORT = {
    STATUS_OK: "済",
    STATUS_PARTIAL: "一部",
    STATUS_MISSING: "未",
}

KEYWORDS = {
    "company": [
        # 日本語
        "会社概要", "会社情報", "企業情報", "企業概要", "会社案内", "会社紹介",
        "運営会社", "運営者", "運営者情報", "事業者情報", "事業者",
        "当社について", "私たちについて", "弊社について", "自社紹介",
        "代表挨拶", "代表者", "経営理念", "企業理念", "沿革", "歴史",
        "組織図", "グループ会社", "関連会社", "本社", "拠点",
        # 英語
        "about", "about us", "company", "corporate", "who we are",
        "our company", "profile", "company profile", "overview",
    ],
    "contact": [
        # 日本語
        "お問い合わせ", "お問合せ", "お問合わせ", "問い合わせ", "問合せ",
        "ご連絡", "連絡先", "連絡", "ご相談", "相談窓口",
        "メール", "メールフォーム", "フォーム", "電話番号", "電話",
        "カスタマーサポート", "サポート", "ヘルプデスク",
        # 英語
        "contact", "contact us", "inquiry", "enquiry", "support",
        "help", "customer service", "get in touch", "reach us",
        "email", "mail", "tel", "phone", "call",
    ],
    "privacy": [
        # 日本語
        "プライバシー", "プライバシーポリシー", "個人情報", "個人情報保護",
        "個人情報保護方針", "個人情報取扱", "個人情報の取り扱い", "プライバシー方針",
        "情報セキュリティ", "セキュリティポリシー", "データ保護",
        "cookie", "クッキー", "クッキーポリシー",
        # 英語
        "privacy", "privacy policy", "personal information",
        "data protection", "gdpr", "cookie policy",
    ],
    "terms": [
        # 日本語
        "利用規約", "規約", "サービス規約", "サービス利用規約",
        "ご利用条件", "利用条件", "利用規程", "約款", "免責事項", "免責",
        "著作権", "知的財産", "法的情報",
        # 英語
        "terms", "terms of use", "terms of service", "tos",
        "agreement", "legal", "disclaimer", "copyright",
    ],
    "address": [
        # 日本語
        "住所", "所在地", "アクセス", "地図", "マップ",
        "本社", "オフィス", "事業所", "拠点", "店舗情報",
        "電話", "電話番号", "fax", "ファックス",
        "〒",  # 郵便番号記号
        # 英語
        "address", "location", "map", "directions", "office",
        "headquarters", "hq", "tel", "phone", "fax",
    ],
}


def is_ec_site(url_type_meta: Optional[Dict[str, Any]]) -> bool:
    """サイト種別メタからECサイトかどうかを推定."""
    if not url_type_meta:
        return True
    effective = (url_type_meta.get("effective") or "") if isinstance(url_type_meta, dict) else ""
    return "EC" in str(effective)


def build_non_ec_legal_summary(analysis_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """非EC向け法務サマリーを作成."""
    url_type_meta = analysis_result.get("url_type", {}) or {}
    if is_ec_site(url_type_meta):
        return None

    html = analysis_result.get("html") or ""
    compliance_text = ""
    industry_payload = analysis_result.get("industry_analysis")
    if isinstance(industry_payload, dict):
        compliance_text = industry_payload.get("compliance_check", "") or ""
    if not compliance_text:
        aio_results = analysis_result.get("aio_results")
        if isinstance(aio_results, dict):
            aio_industry = aio_results.get("industry_analysis")
            if isinstance(aio_industry, dict):
                compliance_text = aio_industry.get("compliance_check", "") or ""
    schema_existing = (analysis_result.get("schema_existing") or {}).get("types", []) or []
    structured_data = analysis_result.get("structured_data", {}) or {}
    legal_checks = analysis_result.get("legal_checks", {}) or {}

    trust_status = _detect_trust_signals(
        html=html,
        compliance_text=compliance_text,
        schema_existing=schema_existing,
        structured_data=structured_data,
    )
    trust_evidence = _detect_trust_evidence(html=html)
    ad_risk = _classify_ad_risk(legal_checks)
    ad_evidence = _extract_ad_evidence(legal_checks)
    visibility_state = _classify_visibility(legal_checks)
    visibility_evidence = _extract_visibility_evidence(legal_checks)

    summary_line = _make_line(
        _build_summary_text(trust_status),
        _build_summary_text(trust_status, short=True),
    )

    company_note = trust_evidence.get("company") or ""
    contact_note = trust_evidence.get("contact") or ""
    trust_line = _make_line(
        f"信頼情報: 会社情報{LABEL_LONG[trust_status['company']]}{company_note} / 連絡手段{LABEL_LONG[trust_status['contact']]}{contact_note}",
        f"信頼情報: 会社{LABEL_SHORT[trust_status['company']]} / 連絡{LABEL_SHORT[trust_status['contact']]}",
    )

    privacy_line = _make_line(
        f"プライバシー: {LABEL_LONG[trust_status['privacy']]}{trust_evidence.get('privacy') or ''}",
        f"プライバシー: {LABEL_SHORT[trust_status['privacy']]}",
    )
    terms_line = _make_line(
        f"規約: {LABEL_LONG[trust_status['terms']]}{trust_evidence.get('terms') or ''}",
        f"規約: {LABEL_SHORT[trust_status['terms']]}",
    )

    ad_line = _make_line(
        _ad_text(ad_risk) + (f"（例: {ad_evidence}）" if ad_evidence and ad_risk in ("high", "warn") else ""),
        _ad_text(ad_risk, short=True),
    )

    visibility_line = _make_line(
        _visibility_text(visibility_state) + (f"（例: {visibility_evidence}）" if visibility_evidence and visibility_state in ("small_font", "hidden") else ""),
        _visibility_text(visibility_state, short=True),
    )

    actions = _build_actions(trust_status, ad_risk, visibility_state, ad_evidence=ad_evidence, visibility_evidence=visibility_evidence)
    action_lines = [_make_line(action, _shorten_action(action)) for action in actions]

    note = _make_line(
        "構造化データ: 検索エンジンに情報を伝える名札",
        "構造化データ: 情報を伝える名札",
    )

    return {
        "title": "非EC向け 法務・信頼性チェック",
        "summary": summary_line,
        "items": [trust_line, privacy_line, terms_line, ad_line, visibility_line],
        "actions": action_lines,
        "note": note,
    }


def format_non_ec_legal_summary(summary: Optional[Dict[str, Any]], max_len: int, max_actions: int = 2) -> Dict[str, Any]:
    """表示用に短文化したテキストを返す."""
    if not summary:
        return {}

    items = [_select_line_text(line, max_len) for line in summary.get("items", [])]
    actions = [_select_line_text(line, max_len) for line in summary.get("actions", [])][:max_actions]
    return {
        "title": summary.get("title", ""),
        "summary": _select_line_text(summary.get("summary", {}), max_len),
        "items": [line for line in items if line],
        "actions": [line for line in actions if line],
        "note": _select_line_text(summary.get("note", {}), max_len),
    }


def _make_line(primary: str, short: Optional[str] = None) -> Dict[str, str]:
    return {
        "primary": primary,
        "short": short or primary,
    }


def _select_line_text(line: Dict[str, str], max_len: int) -> str:
    if not line:
        return ""
    primary = line.get("primary", "")
    short = line.get("short", "")
    if primary and len(primary) <= max_len:
        return primary
    if short and len(short) <= max_len:
        return short
    candidates = [text for text in (short, primary) if text]
    return min(candidates, key=len) if candidates else ""


def _build_summary_text(trust_status: Dict[str, str], short: bool = False) -> str:
    missing = sum(1 for key in ("company", "contact", "privacy") if trust_status.get(key) == STATUS_MISSING)
    if missing >= 2:
        return "総評: 信頼情報に不足。明示が必要。" if not short else "総評: 信頼情報に不足。"
    if missing == 1:
        return "総評: 概ね良好。改善余地あり。" if not short else "総評: 概ね良好。"
    return "総評: 信頼情報は良好。" if not short else "総評: 信頼情報は良好。"


def _ad_text(risk: str, short: bool = False) -> str:
    if risk == "high":
        return "表示表現: 誇大・優良誤認の恐れ" if not short else "表示表現: 誇大表現の恐れ"
    if risk == "warn":
        return "表示表現: 注意が必要な表現あり" if not short else "表示表現: 注意が必要"
    return "表示表現: 重大なリスクは未検出" if not short else "表示表現: 問題なし"


def _visibility_text(state: str, short: bool = False) -> str:
    if state == "small_font":
        return "視認性: 法務表記の文字が小さい箇所" if not short else "視認性: 文字が小さい"
    if state == "hidden":
        return "視認性: 法務表記が見つけづらい" if not short else "視認性: 見つけづらい"
    return "視認性: 法務関連の視認性は良好" if not short else "視認性: 良好"


def _classify_ad_risk(legal_checks: Dict[str, Any]) -> str:
    premiums = (legal_checks.get("premiums_labeling", {}) or {}).get("formatted", {}) or {}
    stealth = (legal_checks.get("stealth_marketing", {}) or {}).get("formatted", {}) or {}
    statuses = [premiums.get("status", ""), stealth.get("status", "")]

    if any("要対応" in status for status in statuses):
        return "high"
    if any("要確認" in status for status in statuses):
        return "warn"
    items = (premiums.get("items", []) or []) + (stealth.get("items", []) or [])
    return "warn" if items else "ok"


def _classify_visibility(legal_checks: Dict[str, Any]) -> str:
    consumer = legal_checks.get("consumer_protection", {}) or {}
    issues = consumer.get("visibility", []) or []
    if any(issue.get("type") == "small_font_legal" for issue in issues):
        return "small_font"
    if any(issue.get("type") in ("hidden_text", "low_reachability") for issue in issues):
        return "hidden"
    return "ok"


def _build_actions(
    trust_status: Dict[str, str],
    ad_risk: str,
    visibility_state: str,
    *,
    ad_evidence: str = "",
    visibility_evidence: str = "",
) -> List[str]:
    actions: List[str] = []
    if trust_status.get("company") == STATUS_MISSING:
        actions.append("優先対応: 会社情報リンクをフッターに明示")
    if trust_status.get("contact") == STATUS_MISSING:
        actions.append("優先対応: お問い合わせ導線を明確化")
    if trust_status.get("privacy") == STATUS_MISSING:
        actions.append("優先対応: プライバシー方針を明示")
    if ad_risk in ("high", "warn"):
        suffix = f"（例: {ad_evidence}）" if ad_evidence else ""
        actions.append(f"優先対応: 断定表現を緩和し根拠を添記{suffix}")
    if visibility_state in ("small_font", "hidden"):
        suffix = f"（例: {visibility_evidence}）" if visibility_evidence else ""
        actions.append(f"優先対応: 法務表記の文字サイズを改善{suffix}")

    if not actions:
        actions.append("優先対応: 信頼情報の配置を再確認")
    return actions[:3]


def _shorten_action(text: str) -> str:
    text = text.replace("優先対応: ", "")
    return f"優先対応: {text}"


def _detect_trust_signals(
    html: str,
    compliance_text: str,
    schema_existing: List[str],
    structured_data: Dict[str, Any],
) -> Dict[str, str]:
    soup = None
    if html:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            soup = None

    link_texts: List[Dict[str, str]] = []
    body_text = ""
    if soup:
        for anchor in soup.find_all("a", href=True):
            # テキストリンク
            link_text = anchor.get_text(strip=True).lower()
            href = (anchor.get("href") or "").lower()

            # 画像リンクのalt属性
            img = anchor.find("img")
            img_alt = (img.get("alt") or "").lower() if img else ""

            # aria-label, title属性
            aria_label = (anchor.get("aria-label") or "").lower()
            title_attr = (anchor.get("title") or "").lower()

            # すべてのテキストを結合して検索対象に
            combined_text = " ".join([link_text, img_alt, aria_label, title_attr])

            link_texts.append(
                {
                    "text": combined_text,
                    "href": href,
                }
            )
        body_text = soup.get_text(" ", strip=True).lower()

    compliance_flags = _parse_compliance_text(compliance_text or "")
    has_org_schema = structured_data.get("has_organization")
    if has_org_schema is None:
        has_org_schema = any(str(item).lower() == "organization" for item in schema_existing)

    statuses = {}
    for key, keywords in KEYWORDS.items():
        link_found = _find_link_hit(link_texts, keywords)
        body_found = _find_body_hit(body_text, keywords)

        if compliance_flags.get(key) == STATUS_OK:
            link_found = True
        elif compliance_flags.get(key) == STATUS_MISSING:
            link_found = link_found or False

        schema_found = False
        if key in ("company", "contact") and has_org_schema:
            schema_found = True

        statuses[key] = _status_from_flags(link_found, body_found, schema_found)

    return statuses


def _detect_trust_evidence(html: str) -> Dict[str, str]:
    """各カテゴリの『どこを見て判断したか』の代表例を返す（UI向けの根拠表示）."""
    if not html:
        return {}
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return {}

    def _infer_location(anchor) -> str:
        parent = anchor
        for _ in range(10):
            if not parent:
                break
            name = getattr(parent, "name", "") or ""
            if name in ("footer", "header", "nav", "aside"):
                return {"footer": "フッター", "header": "ヘッダー", "nav": "ナビ", "aside": "サイド"}[name]
            parent = getattr(parent, "parent", None)
        return "本文"

    evidence: Dict[str, str] = {}
    # category -> keywords list (reuse KEYWORDS)
    for key, keywords in KEYWORDS.items():
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            text = (a.get_text(strip=True) or "").strip()
            title = (a.get("title") or "").strip()
            aria = (a.get("aria-label") or "").strip()
            combined = " ".join([text, title, aria, href]).lower()
            hit = False
            for kw in keywords:
                if kw.lower() in combined:
                    hit = True
                    break
            if hit:
                loc = _infer_location(a)
                label = text or title or aria or "(ラベルなし)"
                short_href = href[:60] + ("..." if len(href) > 60 else "")
                evidence[key] = f"（例: {loc} / {label} / {short_href}）"
                break
        # if not found, leave empty
    return evidence


def _extract_ad_evidence(legal_checks: Dict[str, Any]) -> str:
    """表示表現（景表法/ステマ）の代表例を抽出."""
    if not isinstance(legal_checks, dict):
        return ""
    for key in ("premiums_labeling", "stealth_marketing"):
        section = legal_checks.get(key, {}) or {}
        raw = section.get("raw", {}) or {}
        for issue in (raw.get("issues", []) or [])[:5]:
            phrase = issue.get("matched_text") or issue.get("phrase") or issue.get("text") or ""
            if phrase:
                return str(phrase)[:60]
        formatted = section.get("formatted", {}) or {}
        for item in (formatted.get("items", []) or [])[:5]:
            phrase = item.get("matched_text") or item.get("issue") or item.get("text") or ""
            if phrase:
                return str(phrase)[:60]
    return ""


def _extract_visibility_evidence(legal_checks: Dict[str, Any]) -> str:
    """視認性/到達性の代表例（location/detail/html_snippet等）を抽出."""
    if not isinstance(legal_checks, dict):
        return ""
    consumer = legal_checks.get("consumer_protection", {}) or {}
    issues = consumer.get("visibility", []) or []
    if not issues:
        return ""
    issue = issues[0] or {}
    loc = issue.get("location") or ""
    detail = issue.get("detail") or issue.get("issue") or ""
    snippet = issue.get("html_snippet") or ""
    parts = []
    if loc:
        parts.append(str(loc))
    if detail:
        parts.append(str(detail)[:60])
    if snippet:
        parts.append(str(snippet)[:60])
    return " / ".join(parts)[:120]


def _find_link_hit(link_texts: List[Dict[str, str]], keywords: List[str]) -> bool:
    for entry in link_texts:
        text = entry.get("text", "")
        href = entry.get("href", "")
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text or keyword_lower in href:
                return True
    return False


def _find_body_hit(body_text: str, keywords: List[str]) -> bool:
    if not body_text:
        return False
    for keyword in keywords:
        if keyword.lower() in body_text:
            return True
    return False


def _status_from_flags(link_found: bool, body_found: bool, schema_found: bool) -> str:
    if link_found and body_found:
        return STATUS_OK
    if link_found or body_found or schema_found:
        return STATUS_PARTIAL
    return STATUS_MISSING


def _parse_compliance_text(text: str) -> Dict[str, str]:
    text = text or ""
    flags: Dict[str, str] = {}
    if "プライバシーポリシーへのリンクあり" in text:
        flags["privacy"] = STATUS_OK
    if "プライバシーポリシーへのリンクが見つかりません" in text:
        flags["privacy"] = STATUS_MISSING
    if "会社概要/運営者情報へのリンクあり" in text:
        flags["company"] = STATUS_OK
    if "会社概要・運営者情報へのリンクが見つかりません" in text:
        flags["company"] = STATUS_MISSING
    return flags
