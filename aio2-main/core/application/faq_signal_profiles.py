from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlsplit


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_text_list(values: Any, *, limit: int = 6) -> List[str]:
    normalized: List[str] = []
    for value in values or []:
        text = _safe_text(value)
        if text and text not in normalized:
            normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def _contains_any(text: Any, keywords: List[str]) -> bool:
    normalized = _safe_text(text).lower()
    return any(_safe_text(keyword).lower() in normalized for keyword in keywords if _safe_text(keyword))


def _collect_keyword_hits(text: Any, keywords: List[str], *, limit: int = 4) -> List[str]:
    normalized = _safe_text(text).lower()
    hits: List[str] = []
    for keyword in keywords:
        label = _safe_text(keyword)
        if not label:
            continue
        if label.lower() in normalized and label not in hits:
            hits.append(label)
        if len(hits) >= limit:
            break
    return hits


def build_domain_profile(url: Any) -> Dict[str, Any]:
    raw = _safe_text(url)
    host = ""
    if raw:
        try:
            host = (urlsplit(raw).netloc or "").lower()
        except Exception:
            host = ""
    host = host.removeprefix("www.")

    domain_class = "general"
    label = "一般ドメイン"
    if host.endswith("or.jp"):
        domain_class = "association_like"
        label = "団体・協会系ドメイン"
    elif any(host.endswith(suffix) for suffix in ("go.jp", "lg.jp", "ac.jp", "ed.jp")):
        domain_class = "public_like"
        label = "公共・教育系ドメイン"
    elif host.endswith("co.jp"):
        domain_class = "corporate"
        label = "企業ドメイン"

    return {
        "host": host,
        "domain_class": domain_class,
        "label": label,
        "is_special": domain_class in {"association_like", "public_like"},
        "prefer_public_info": domain_class in {"association_like", "public_like"},
        "prefer_non_ec": domain_class in {"association_like", "public_like"},
    }


def build_lmo_profile(
    *,
    industry: Any,
    page_title: Any,
    meta_description: Any,
    heading_texts: Any,
    context_text: Any,
    url_tokens: Any,
) -> Dict[str, Any]:
    title_text = " ".join(
        [
            _safe_text(page_title),
            _safe_text(meta_description),
            " ".join(_safe_text_list(heading_texts, limit=6)),
        ]
    )
    context_blob = " ".join(
        [
            _safe_text(industry),
            title_text,
            _safe_text(context_text),
            " ".join(_safe_text_list(url_tokens, limit=8)),
        ]
    )

    access_keywords = ["アクセス", "最寄り", "駅", "駐車場", "地図", "所在地", "行き方", "アクセス方法"]
    hours_keywords = ["営業時間", "営業日", "定休日", "受付時間", "営業時間帯", "open", "close"]
    reservation_keywords = ["予約", "席", "来店", "当日利用", "個室", "受付", "受付方法", "利用方法"]
    local_service_keywords = ["メニュー", "コース", "ランチ", "ディナー", "イベント", "チケット", "会場", "施設", "パーク", "restaurant", "cafe", "menu", "park"]

    category_hits = {
        "access": _collect_keyword_hits(context_blob, access_keywords),
        "hours": _collect_keyword_hits(context_blob, hours_keywords),
        "reservation": _collect_keyword_hits(context_blob, reservation_keywords),
        "local_service": _collect_keyword_hits(context_blob, local_service_keywords),
    }

    industry_visit = _contains_any(industry, ["飲食", "フード", "レジャー", "観光", "旅行", "ホテル", "宿泊", "イベント"])
    category_count = sum(1 for hits in category_hits.values() if hits)
    score = float(category_count * 2 + (2 if industry_visit else 0))
    is_location_or_visit = bool(
        industry_visit and category_count >= 1
        or category_count >= 2
        or (category_hits["reservation"] and category_hits["access"])
    )

    signals: List[str] = []
    for key, hits in category_hits.items():
        if hits:
            signals.append(f"{key}:{hits[0]}")

    return {
        "is_location_or_visit": is_location_or_visit,
        "score": score,
        "industry_visit": industry_visit,
        "category_hits": category_hits,
        "signals": signals[:6],
    }


def build_ec_guardrail(
    *,
    raw_is_ec: bool,
    ec_detection_reason: Any,
    domain_profile: Dict[str, Any],
    lmo_profile: Dict[str, Any],
) -> Dict[str, Any]:
    reason_text = _safe_text(ec_detection_reason).lower()
    hard_reasons = [
        marker for marker in ("user_selected", "business_type: ec_retail")
        if marker in reason_text
    ]
    commerce_reasons = [
        marker for marker in ("checkout", "price_display")
        if marker in reason_text
    ]
    weak_reasons = [
        marker for marker in ("product_indicators", "support_terms")
        if marker in reason_text
    ]

    forced_non_ec_reasons: List[str] = []
    if raw_is_ec and domain_profile.get("prefer_non_ec") and not hard_reasons:
        forced_non_ec_reasons.append(f"domain:{domain_profile.get('domain_class')}")
    if raw_is_ec and lmo_profile.get("is_location_or_visit") and not hard_reasons:
        forced_non_ec_reasons.append("lmo:visit_intent")

    effective_is_ec = bool(raw_is_ec) and not forced_non_ec_reasons
    return {
        "raw_is_ec": bool(raw_is_ec),
        "effective_is_ec": effective_is_ec,
        "hard_reasons": hard_reasons,
        "commerce_reasons": commerce_reasons,
        "weak_reasons": weak_reasons,
        "forced_non_ec_reasons": forced_non_ec_reasons,
    }
