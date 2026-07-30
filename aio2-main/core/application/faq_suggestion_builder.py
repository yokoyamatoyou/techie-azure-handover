from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import unquote, urlsplit

from core.application.faq_signal_profiles import (
    build_domain_profile,
    build_ec_guardrail,
    build_lmo_profile,
)
from core.term_glossary import get_all_faqs, get_ec_faq_templates

def _safe_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0

def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()

def _normalize_inline_text(value: Any) -> str:
    text = _safe_text(value)
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
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

def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)

def _json_clone(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=_json_default))
    except (TypeError, ValueError):
        return value

def _get_provider_readiness(results: Dict[str, Any]) -> Dict[str, Any]:
    aio_results = results.get("aio_results") or {}
    return aio_results.get("provider_readiness") or (aio_results.get("details") or {}).get("provider_readiness") or {}

def _contains_any(text: str, keywords: List[str]) -> bool:
    normalized = _safe_text(text).lower()
    return any(keyword.lower() in normalized for keyword in keywords)

def _collect_keyword_hits(text: str, keywords: List[str]) -> List[str]:
    normalized = _safe_text(text).lower()
    hits: List[str] = []
    for keyword in keywords:
        label = _safe_text(keyword)
        if not label:
            continue
        if label.lower() in normalized and label not in hits:
            hits.append(label)
    return hits

def _safe_text_list(values: Any, *, limit: int = 6) -> List[str]:
    normalized: List[str] = []
    for value in values or []:
        text = _safe_text(value)
        if text and text not in normalized:
            normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized

def _read_context_value(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)

def _clean_page_focus(text: Any) -> str:
    normalized = _safe_text(text)
    if not normalized:
        return ""
    head = re.split(r"[|｜:：/\-‐–—・]", normalized, maxsplit=1)[0].strip()
    head = re.sub(r"\s+", " ", head)
    if head.lower() in {"home", "top", "トップ"}:
        return ""
    return head

def _extract_url_signal_tokens(url: Any) -> List[str]:
    raw = _safe_text(url)
    if not raw:
        return []
    try:
        parsed = urlsplit(raw)
    except Exception:
        parsed = None

    parts: List[str] = []
    if parsed:
        parts.extend(str(parsed.netloc or "").split("."))
        path = unquote(str(parsed.path or ""))
        parts.extend(re.split(r"[/_.\-]+", path))
    else:
        parts.extend(re.split(r"[/_.:\-]+", raw))

    stopwords = {
        "", "www", "http", "https", "com", "jp", "co", "net", "org", "html", "htm", "php",
        "index", "page", "pages", "post", "posts", "entry", "service", "services", "product",
        "products", "item", "items", "category", "categories", "blog", "news", "article", "lp",
    }
    tokens: List[str] = []
    for part in parts:
        token = _safe_text(part).strip().lower()
        if not token or token in stopwords or token.isdigit() or len(token) <= 1:
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens

def _collect_faq_context(results: Dict[str, Any]) -> Dict[str, Any]:
    legal_summary = results.get("legal_summary") or {}
    citation = results.get("citation_insights") or {}
    content_plan = citation.get("content_plan") or {}
    provider_readiness = _get_provider_readiness(results)
    platform_guidance = results.get("platform_guidance") or {}
    deep = results.get("deep_recommendations") or {}
    faq_detection = results.get("faq_detection") or {}
    industry_analysis = results.get("industry_analysis") or {}
    basics = (results.get("seo_results") or {}).get("basics") or {}
    structure = (results.get("seo_results") or {}).get("structure") or {}
    integrated = results.get("integrated_results") or {}
    business_type = results.get("business_type_detection") or {}
    headings = structure.get("headings") or {}

    heading_texts: List[str] = []
    if isinstance(headings, dict):
        for _, value in headings.items():
            if isinstance(value, list):
                heading_texts.extend(_safe_text_list(value, limit=4))
            else:
                text = _safe_text(value)
                if text:
                    heading_texts.append(text)

    url_value = _safe_text(results.get("url"))
    url_signal_tokens = _extract_url_signal_tokens(url_value)
    domain_profile = build_domain_profile(url_value)

    issue_texts: List[str] = []
    for warning in results.get("warnings") or []:
        text = _safe_text(warning)
        if text:
            issue_texts.append(text)
    for item in legal_summary.get("top_issues") or []:
        for value in (item.get("title"), item.get("summary"), item.get("detail")):
            text = _safe_text(value)
            if text:
                issue_texts.append(text)
    for group in ("business", "technical"):
        for item in deep.get(group) or []:
            for value in (
                item.get("title"),
                item.get("current_issue"),
                item.get("recommended_action"),
                item.get("implementation"),
                item.get("expected_impact"),
            ):
                text = _safe_text(value)
                if text:
                    issue_texts.append(text)
    for item in (results.get("summary") or {}).get("improvements") or []:
        text = _safe_text(item)
        if text:
            issue_texts.append(text)
    for item in citation.get("phrases") or []:
        for value in (item.get("phrase"), item.get("reason"), item.get("template_non_engineer"), item.get("template")):
            text = _safe_text(value)
            if text:
                issue_texts.append(text)
    for section in content_plan.get("sections") or []:
        for value in (section.get("title"), section.get("purpose"), section.get("format")):
            text = _safe_text(value)
            if text:
                issue_texts.append(text)
    for provider in provider_readiness.values():
        if not isinstance(provider, dict):
            continue
        summary_text = _safe_text(provider.get("summary"))
        if summary_text:
            issue_texts.append(summary_text)
        for note in provider.get("heuristic_notes") or []:
            text = _safe_text(note)
            if text:
                issue_texts.append(text)
    validation = faq_detection.get("validation") or {}
    for item in validation.get("suspicious_items") or []:
        for value in (item.get("question"), item.get("reason")):
            text = _safe_text(value)
            if text:
                issue_texts.append(text)

    industry = _safe_text(((results.get("final_industry") or {}).get("primary")))
    context_text = " ".join(issue_texts)
    raw_page_title_headings = _safe_text_list(
        [
            basics.get("title"),
            basics.get("meta_description"),
            *heading_texts,
        ],
        limit=10,
    )
    page_signal_text = " ".join(
        [
            *raw_page_title_headings,
            " ".join(url_signal_tokens),
            _safe_text(business_type.get("primary_type")),
            industry,
        ]
    )

    service_terms = _collect_keyword_hits(
        f"{page_signal_text} {context_text}",
        [
            "査定", "売却", "買取", "空き家", "相続", "相談", "管理", "リフォーム",
            "導入", "資料請求", "見積", "料金", "プラン", "セミナー", "講座", "支援",
            "データ入力", "スキャニング", "システム", "RPA", "分析", "サービス",
        ],
    )
    location_terms = _collect_keyword_hits(
        f"{page_signal_text} {context_text}",
        ["アクセス", "駅", "駐車場", "営業時間", "定休日", "予約", "来店", "京都", "大阪", "店舗", "地域"],
    )
    transaction_terms = _collect_keyword_hits(
        f"{page_signal_text} {context_text}",
        ["料金", "費用", "見積", "契約", "申込", "査定", "売却", "買取", "納期", "期間", "必要書類", "手続き", "送料", "返品", "支払い"],
    )
    customer_intent_terms = _collect_keyword_hits(
        f"{page_signal_text} {context_text}",
        ["比較", "相談", "依頼", "問い合わせ", "資料請求", "予約", "購入", "売却", "査定", "導入", "申込"],
    )

    lmo_profile = build_lmo_profile(
        industry=industry,
        page_title=basics.get("title"),
        meta_description=basics.get("meta_description"),
        heading_texts=heading_texts,
        context_text=context_text,
        url_tokens=url_signal_tokens,
    )
    ec_guardrail = build_ec_guardrail(
        raw_is_ec=bool(results.get("is_ec")),
        ec_detection_reason=results.get("ec_detection_reason"),
        domain_profile=domain_profile,
        lmo_profile=lmo_profile,
    )

    return {
        "industry": industry,
        "site_type": _safe_text(((results.get("url_type") or {}).get("effective"))),
        "platform": _safe_text(platform_guidance.get("label") or ((results.get("platform") or {}).get("effective"))),
        "is_ec": bool(results.get("is_ec")),
        "effective_is_ec": bool(ec_guardrail.get("effective_is_ec")),
        "ec_detection_reason": _safe_text(results.get("ec_detection_reason")),
        "context_text": context_text,
        "citation_count": len(citation.get("phrases") or []),
        "business_goal": _safe_text(results.get("business_goal") or integrated.get("business_goal")),
        "audience_clues": _safe_text_list(_read_context_value(industry_analysis, "target_audience_clues") or []),
        "regulatory_indicators": _safe_text_list(_read_context_value(industry_analysis, "regulatory_indicators") or []),
        "page_title": _safe_text(basics.get("title")),
        "meta_description": _safe_text(basics.get("meta_description")),
        "heading_texts": _safe_text_list(heading_texts, limit=6),
        "raw_page_title_headings": raw_page_title_headings,
        "page_service_terms": service_terms[:8],
        "location_terms": location_terms[:8],
        "transaction_terms": transaction_terms[:8],
        "customer_intent_terms": customer_intent_terms[:8],
        "page_focus": _clean_page_focus(basics.get("title")) or _clean_page_focus(business_type.get("primary_type")),
        "business_type": _safe_text(business_type.get("primary_type")),
        "summary_improvements": _safe_text_list(((results.get("summary") or {}).get("improvements") or []), limit=4),
        "url": url_value,
        "url_signal_tokens": url_signal_tokens[:8],
        "domain_profile": domain_profile,
        "lmo_profile": lmo_profile,
        "ec_guardrail": ec_guardrail,
    }

def _heading_texts_from_results(results: Dict[str, Any], *, limit: int = 8) -> List[str]:
    structure = (results.get("seo_results") or {}).get("structure") or {}
    headings = structure.get("headings") or {}
    heading_texts: List[str] = []
    if isinstance(headings, dict):
        for value in headings.values():
            if isinstance(value, list):
                heading_texts.extend(_safe_text_list(value, limit=limit))
            else:
                text = _safe_text(value)
                if text:
                    heading_texts.append(text)
    elif isinstance(headings, list):
        heading_texts.extend(_safe_text_list(headings, limit=limit))
    return _safe_text_list(heading_texts, limit=limit)

def _faq_candidate(
    *,
    question: str,
    answer: str,
    score: int,
    source_label: str,
    reason: str,
    topic: str = "",
    matched_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "question": question,
        "answer": answer,
        "score": score,
        "source_label": source_label,
        "reason": reason,
        "topic": _safe_text(topic),
        "matched_keywords": _safe_text_list(matched_keywords or [], limit=6),
    }

def _dedupe_faq_candidates(candidates: List[Dict[str, Any]], max_items: int) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(candidates, key=lambda row: (-int(row.get("score", 0)), str(row.get("question", "")))):
        question = _safe_text(item.get("question"))
        if not question:
            continue
        key = question.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized = dict(item)
        normalized["question"] = question
        normalized["answer"] = _safe_text(item.get("answer"))
        normalized["source_label"] = _safe_text(item.get("source_label"))
        normalized["reason"] = _safe_text(item.get("reason"))
        normalized["topic"] = _safe_text(item.get("topic"))
        normalized["matched_keywords"] = _safe_text_list(item.get("matched_keywords") or [], limit=6)
        for key in ("answer_outline", "recommended_section", "schema_candidate", "confidence", "risk_if_wrong"):
            if key in item:
                normalized[key] = _safe_text(item.get(key))
        if "evidence_terms" in item:
            normalized["evidence_terms"] = _safe_text_list(item.get("evidence_terms") or [], limit=8)
        deduped.append(normalized)
        if len(deduped) >= max_items:
            break
    return deduped

def _faq_page_signal_text(context: Dict[str, Any]) -> str:
    return " ".join(
        [
            _safe_text(context.get("page_title")),
            _safe_text(context.get("meta_description")),
            _safe_text(context.get("page_focus")),
            _safe_text(context.get("business_type")),
            _safe_text(context.get("industry")),
            " ".join(_safe_text_list(context.get("heading_texts") or [], limit=6)),
            " ".join(_safe_text_list(context.get("url_signal_tokens") or [], limit=8)),
        ]
    )

def _faq_consumer_profile(context: Dict[str, Any]) -> Dict[str, Any]:
    signal_text = f"{_faq_page_signal_text(context)} {_safe_text(context.get('context_text'))}"
    audience_text = " ".join(_safe_text_list(context.get("audience_clues") or [], limit=6))
    domain_profile = context.get("domain_profile") or {}
    if _safe_text(domain_profile.get("domain_class")) in {"association_like", "public_like"} or bool(domain_profile.get("prefer_public_info")):
        return {}
    explicit_b2b = _contains_any(
        f"{signal_text} {audience_text}",
        ["b2b", "enterprise", "法人向け", "企業向け", "IT・SaaS", "SaaS", "ソフトウェア", "稟議", "社内検討", "部署", "管理者", "導入事例", "導入支援"],
    )
    if explicit_b2b:
        return {}
    profile_specs = [
        {
            "key": "real_estate",
            "label": "不動産売却・査定",
            "keywords": ["不動産", "売却", "査定", "買取", "空き家", "相続", "土地", "住宅", "マンション", "戸建"],
            "section": "サービスページのCTA直前",
            "pricing_question": "査定や売却相談に費用はかかりますか？",
            "pricing_answer": "査定費用、相談料、仲介手数料、買取時の費用、必要書類を分けて示すと、売却前の不安を減らせます。",
            "process_question": "査定から売却完了まではどんな流れですか？",
            "process_answer": "相談、現地確認、査定、媒介契約または買取判断、引き渡しまでを時系列で示し、各段階の目安日数を添えてください。",
            "support_question": "空き家や相続不動産も相談できますか？",
            "support_answer": "空き家、相続、住み替え、買取など対応できる相談範囲と、事前に必要な情報を分けて示すと問い合わせ前の迷いを減らせます。",
        },
        {
            "key": "food",
            "label": "飲食・店舗",
            "keywords": ["飲食", "レストラン", "カフェ", "居酒屋", "焼肉", "メニュー", "ランチ", "ディナー", "席", "個室", "予約", "来店"],
            "section": "メニュー・予約導線の直前",
            "pricing_question": "メニューや予算の目安はどこで確認できますか？",
            "pricing_answer": "代表メニュー、価格帯、コース有無、追加料金が発生する条件をまとめると、来店前の比較判断がしやすくなります。",
            "process_question": "予約から来店までの流れは？",
            "process_answer": "予約方法、当日受付、人数変更、来店前の注意点を時系列で示すと、初めての来店でも迷いにくくなります。",
            "support_question": "アレルギー・子連れ・個室などは相談できますか？",
            "support_answer": "アレルギー対応、子連れ可否、個室、駐車場、支払い方法など来店前に確認されやすい条件を明記します。",
        },
        {
            "key": "care",
            "label": "介護・福祉",
            "keywords": ["介護", "福祉", "老人ホーム", "デイサービス", "訪問介護", "施設", "見学", "送迎", "ケア", "要介護", "利用者"],
            "section": "利用案内・問い合わせCTAの直前",
            "pricing_question": "利用料金や自己負担額はどのように確認できますか？",
            "pricing_answer": "基本料金、介護保険の自己負担、追加費用、見学時に確認すべき費用を分けると、家族が比較しやすくなります。",
            "process_question": "見学・相談から利用開始までの流れは？",
            "process_answer": "問い合わせ、見学、面談、必要書類、契約、利用開始までを段階ごとに示し、各段階の目安期間を添えます。",
            "support_question": "対応エリアや医療連携、送迎範囲は？",
            "support_answer": "対応エリア、送迎範囲、医療連携、受け入れ条件、相談窓口を整理すると、利用前の不安を減らせます。",
        },
        {
            "key": "apparel",
            "label": "アパレル・物販",
            "keywords": ["アパレル", "服", "洋服", "ファッション", "サイズ", "試着", "素材", "ブランド", "コーデ", "返品", "交換"],
            "section": "商品説明・購入導線の直前",
            "pricing_question": "価格帯や送料・返品条件はどこで確認できますか？",
            "pricing_answer": "価格帯、送料、返品交換条件、セール対象外条件を近くに置くと、購入前の迷いを減らせます。",
            "process_question": "サイズ選びや試着・交換の流れは？",
            "process_answer": "サイズ表、着用感、試着可否、交換手順をまとめると、購入前ユーザーが自分に合うか判断しやすくなります。",
            "support_question": "素材・サイズ感・お手入れ方法は確認できますか？",
            "support_answer": "素材、透け感、伸縮性、洗濯方法、サイズ感の目安をFAQ化すると、返品や問い合わせを減らしやすくなります。",
        },
        {
            "key": "beauty",
            "label": "美容・サロン",
            "keywords": ["美容", "サロン", "エステ", "脱毛", "ネイル", "整体", "施術", "予約", "カウンセリング"],
            "section": "料金・予約導線の直前",
            "pricing_question": "施術料金や追加費用はありますか？",
            "pricing_answer": "基本料金、初回料金、オプション、指名料、キャンセル料を分けると、予約前の不安を減らせます。",
            "process_question": "予約から施術当日までの流れは？",
            "process_answer": "予約、カウンセリング、施術、所要時間、来店前の注意点を時系列で示すと、初回ユーザーが安心しやすくなります。",
            "support_question": "キャンセル、持ち物、肌トラブル時の対応は？",
            "support_answer": "キャンセル期限、必要な持ち物、注意事項、トラブル時の相談先を明記します。",
        },
        {
            "key": "education",
            "label": "教育・スクール",
            "keywords": ["塾", "スクール", "教室", "習い事", "講座", "体験", "入会", "月謝", "教材", "対象学年"],
            "section": "体験申込・入会案内の直前",
            "pricing_question": "月謝・教材費・追加費用はどこで確認できますか？",
            "pricing_answer": "月謝、入会金、教材費、振替や追加講座の費用を分けると、保護者や受講者が比較しやすくなります。",
            "process_question": "体験申込から入会までの流れは？",
            "process_answer": "体験申込、見学、面談、入会手続き、初回受講までを段階ごとに示します。",
            "support_question": "対象学年や振替、サポート範囲は？",
            "support_answer": "対象学年、レベル、振替制度、質問対応、保護者連絡の方法をまとめると検討しやすくなります。",
        },
    ]
    scored = []
    for spec in profile_specs:
        hits = _collect_keyword_hits(signal_text, spec["keywords"])
        if hits:
            row = dict(spec)
            row["hits"] = hits[:8]
            row["score"] = len(hits)
            scored.append(row)
    if scored:
        best_profile = sorted(scored, key=lambda row: (-int(row.get("score", 0)), str(row.get("label", ""))))[0]
        if int(best_profile.get("score", 0)) >= 2:
            return best_profile

    generic_hits = _collect_keyword_hits(
        signal_text,
        ["個人", "一般", "初めて", "口コミ", "レビュー", "予約", "来店", "購入", "サイズ", "料金", "費用", "営業時間", "アクセス", "相談"],
    )
    if generic_hits and not explicit_b2b:
        return {
            "key": "generic_b2c",
            "label": "BtoCサービス",
            "hits": generic_hits[:8],
            "score": len(generic_hits),
            "section": "サービス説明またはCTAの直前",
            "pricing_question": "料金・費用・追加料金はどこで確認できますか？",
            "pricing_answer": "基本料金、追加費用が発生する条件、支払い方法、比較時に見落としやすい条件を分けて示します。",
            "process_question": "予約・相談・申込から利用開始までの流れは？",
            "process_answer": "問い合わせ、予約または申込、必要情報、当日の流れ、利用開始までを時系列で示すと、初めての人が迷いにくくなります。",
            "support_question": "問い合わせ前に確認しておくことは？",
            "support_answer": "受付時間、返信目安、準備しておく情報、対象外の条件をまとめると、問い合わせ前の不安を減らせます。",
        }
    return {}

def _is_real_estate_context(context: Dict[str, Any]) -> bool:
    return _safe_text((_faq_consumer_profile(context) or {}).get("key")) == "real_estate"

def _faq_business_goal_for_copy(context: Dict[str, Any]) -> str:
    goal = _safe_text(context.get("business_goal"))
    if not goal or goal == "自動判定" or "自動判定" in goal:
        return "比較検討"
    return goal

def _faq_recommended_section(topic: str, context: Dict[str, Any]) -> str:
    consumer_profile = _faq_consumer_profile(context)
    if consumer_profile and topic in {"pricing", "process", "support", "fit", "audience_value"}:
        return _safe_text(consumer_profile.get("section")) or "サービス説明またはCTAの直前"
    mapping = {
        "pricing": "料金・見積説明の直下",
        "process": "申込・導入フローの直下",
        "comparison": "サービス比較・選び方セクション",
        "trust": "会社概要・運営者情報の近く",
        "case": "事例・実績セクション",
        "support": "問い合わせCTAの直前",
        "security": "セキュリティ・個人情報ページ",
        "access": "アクセス情報の直下",
        "hours": "営業時間案内の直下",
        "reservation": "予約導線の直前",
        "public_services": "支援メニュー一覧の直下",
        "public_eligibility": "対象者・利用条件の直下",
        "public_application": "申込方法・窓口案内の直下",
        "audience_value": "サービス概要の直下",
        "fit": "対象者・利用シーンの直下",
    }
    return mapping.get(topic, "ページ下部のFAQセクション")

def _faq_value_fields(candidate: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    topic = _safe_text(candidate.get("topic"))
    matched = _safe_text_list(candidate.get("matched_keywords") or [], limit=6)
    evidence_terms = list(matched)
    topic_terms = {
        "pricing": context.get("transaction_terms") or [],
        "process": (context.get("transaction_terms") or []) + (context.get("customer_intent_terms") or []),
        "comparison": context.get("customer_intent_terms") or [],
        "support": context.get("customer_intent_terms") or [],
        "access": context.get("location_terms") or [],
        "hours": context.get("location_terms") or [],
        "reservation": context.get("location_terms") or [],
        "audience_value": context.get("page_service_terms") or [],
        "fit": context.get("page_service_terms") or [],
    }.get(topic, context.get("page_service_terms") or [])
    evidence_terms.extend(_safe_text_list(topic_terms, limit=6))
    evidence_terms = _safe_text_list(evidence_terms, limit=8)
    score = _safe_int(candidate.get("score"))
    if len(matched) >= 2 or score >= 7:
        confidence = "high"
    elif evidence_terms or score >= 4:
        confidence = "medium"
    else:
        confidence = "low"
    risk = "本文にない条件を断定しないでください。料金・期限・対象者は実データで確認してから公開します。"
    if confidence == "low":
        risk = "ページ文脈との一致が弱いため、実際の問い合わせ内容や担当者の確認を入れてから採用してください。"
    return {
        "answer_outline": _safe_text(candidate.get("answer")),
        "recommended_section": _faq_recommended_section(topic, context),
        "schema_candidate": "FAQPage候補（本文FAQとして公開後にJSON-LD化を検討）",
        "evidence_terms": evidence_terms,
        "confidence": confidence,
        "risk_if_wrong": risk,
    }

def _build_faq_persona_candidates(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    audience_clues = _safe_text_list(context.get("audience_clues") or [], limit=6)
    business_goal = _safe_text(context.get("business_goal"))
    url_tokens = _safe_text_list(context.get("url_signal_tokens") or [], limit=8)
    domain_profile = context.get("domain_profile") or {}
    lmo_profile = context.get("lmo_profile") or {}
    ec_guardrail = context.get("ec_guardrail") or {}
    consumer_profile = _faq_consumer_profile(context)
    title_text = " ".join(
        [
            _safe_text(context.get("page_title")),
            _safe_text(context.get("meta_description")),
            _safe_text(context.get("page_focus")),
            _safe_text(context.get("business_type")),
            " ".join(_safe_text_list(context.get("heading_texts") or [], limit=4)),
        ]
    )
    context_text = " ".join(
        [
            _safe_text(context.get("context_text")),
            _safe_text(context.get("site_type")),
            _safe_text(context.get("industry")),
            " ".join(_safe_text_list(context.get("summary_improvements") or [], limit=4)),
            " ".join(_safe_text_list(context.get("regulatory_indicators") or [], limit=4)),
        ]
    )
    url_text = " ".join(url_tokens)

    persona_specs = {
        "ec": {
            "label": "購入前ユーザー向け",
            "style": "購入前に条件を確認したい人",
            "headline_keywords": ["shop", "store", "ec", "cart", "checkout", "product", "products", "通販", "購入", "注文", "配送", "送料", "返品", "支払い"],
            "context_keywords": ["購入", "注文", "返品", "配送", "送料", "支払い", "在庫", "発送", "商品"],
        },
        "visitor": {
            "label": "来訪前ユーザー向け",
            "style": "行く前に条件や現地情報を確認したい人",
            "headline_keywords": ["restaurant", "cafe", "menu", "park", "event", "access", "hours", "予約", "営業時間", "アクセス", "駐車場", "メニュー", "店舗", "施設", "会場"],
            "context_keywords": ["最寄り", "アクセス", "駐車場", "営業時間", "定休日", "予約", "来店", "席", "個室", "メニュー", "イベント", "会場"],
        },
        "public": {
            "label": "案内確認ユーザー向け",
            "style": "窓口や利用条件を先に確認したい人",
            "headline_keywords": ["association", "foundation", "chamber", "public", "member", "会議所", "協会", "財団", "法人", "団体", "支援", "会員"],
            "context_keywords": ["窓口", "相談", "支援", "会員", "申請", "申込条件", "対象者", "制度", "利用案内"],
        },
        "executive": {
            "label": "経営判断者向け",
            "style": "比較判断の材料を短時間で揃えたい人",
            "headline_keywords": ["executive", "owner", "founder", "management", "ceo", "president", "経営", "代表", "役員", "意思決定", "戦略", "投資対効果", "roi"],
            "context_keywords": ["経営課題", "ROI", "投資対効果", "部門横断", "意思決定", "役員", "予算判断", "経営改善"],
        },
        "business": {
            "label": "法人担当者向け",
            "style": "社内検討の前に要件を整理したい人",
            "headline_keywords": ["b2b", "business", "enterprise", "company", "corporate", "法人", "企業", "会社", "導入", "比較", "見積", "資料請求", "料金", "プラン"],
            "context_keywords": ["稟議", "導入", "比較検討", "資料請求", "見積", "月額", "初期費用", "担当者", "運用体制", "導入事例"],
        },
        "specialist": {
            "label": "専門職向け",
            "style": "根拠や要件を厳しく確認したい人",
            "headline_keywords": ["medical", "clinic", "legal", "security", "compliance", "医療", "病院", "クリニック", "弁護士", "税理士", "士業", "セキュリティ", "要件"],
            "context_keywords": ["根拠", "要件", "仕様", "ガイドライン", "監修", "エビデンス", "法令", "コンプライアンス", "症例", "診療"],
        },
        "consumer": {
            "label": "個人ユーザー向け",
            "style": "初めて比較検討する人",
            "headline_keywords": ["personal", "consumer", "family", "home", "individual", "個人", "一般", "初心者", "家庭", "自宅", "はじめて", "レビュー", "口コミ"],
            "context_keywords": ["初めて", "口コミ", "レビュー", "体験", "お客様", "ユーザー", "ご利用", "使い方", "不安", "サポート"],
        },
        "default": {
            "label": "比較検討中の担当者向け",
            "style": "問い合わせ前に要点を把握したい人",
            "headline_keywords": [],
            "context_keywords": ["比較", "選び方", "違い", "判断材料", "相談", "問い合わせ"],
        },
    }

    scores = {key: 0.0 for key in persona_specs}
    reasons = {key: [] for key in persona_specs}

    def add_score(key: str, points: float, reason: str) -> None:
        if not reason:
            return
        scores[key] += points
        if reason not in reasons[key]:
            reasons[key].append(reason)

    audience_map = {
        "経営者向け": ("executive", 6.0),
        "法人向け": ("business", 6.0),
        "専門職向け": ("specialist", 6.0),
        "個人向け": ("consumer", 6.0),
    }
    for clue in audience_clues:
        target = audience_map.get(clue)
        if target:
            add_score(target[0], target[1], f"audience_clues:{clue}")

    domain_class = _safe_text(domain_profile.get("domain_class"))

    if ec_guardrail.get("effective_is_ec"):
        add_score("ec", 9.0, "is_ec")
        add_score("consumer", 2.5, "is_ec")

    if lmo_profile.get("is_location_or_visit"):
        visitor_boost = 4.0 if domain_class in {"association_like", "public_like"} else 7.0
        consumer_boost = 1.0 if domain_class in {"association_like", "public_like"} else 2.0
        add_score("visitor", visitor_boost, "lmo:visit_intent")
        add_score("consumer", consumer_boost, "lmo:visit_intent")
    if _contains_any(_safe_text(context.get("industry")), ["飲食", "フード", "レジャー", "観光", "旅行", "ホテル", "宿泊"]):
        add_score("visitor", 2.5, "industry:lmo")

    if domain_class in {"association_like", "public_like"}:
        add_score("public", 6.0, f"domain:{domain_class}")
        if lmo_profile.get("is_location_or_visit"):
            add_score("public", 2.0, "domain:lmo_blend")
        add_score("default", 1.5, f"domain:{domain_class}")

    if (
        _contains_any(_safe_text(context.get("site_type")), ["企業", "法人", "会社"])
        and not lmo_profile.get("is_location_or_visit")
        and domain_class not in {"association_like", "public_like"}
        and not consumer_profile
    ):
        add_score("business", 3.0, "site_type:corporate")
        add_score("default", 1.5, "site_type:corporate")
    if _contains_any(_safe_text(context.get("industry")), ["金融", "保険", "医療", "美容", "健康", "士業"]):
        add_score("specialist", 2.5, "industry:regulated")
    if consumer_profile:
        add_score("consumer", 5.0, f"b2c:{consumer_profile.get('key')}")
        add_score("default", 2.0, f"b2c:{consumer_profile.get('key')}:comparison_intent")
        if _contains_any(_safe_text(consumer_profile.get("key")), ["food", "beauty"]):
            add_score("visitor", 2.0, f"b2c:{consumer_profile.get('key')}:visit_intent")
    if _contains_any(business_goal, ["CV", "リード", "CTA"]):
        add_score("business", 1.5, "goal:lead")
    if _contains_any(business_goal, ["ブランド", "指名検索"]):
        add_score("executive", 1.0, "goal:brand")
    if _contains_any(business_goal, ["技術健全性", "エンジニア"]):
        add_score("specialist", 1.5, "goal:technical")

    for key, spec in persona_specs.items():
        headline_hits = _collect_keyword_hits(title_text, spec["headline_keywords"])
        context_hits = _collect_keyword_hits(context_text, spec["context_keywords"])
        url_hits = _collect_keyword_hits(url_text, spec["headline_keywords"] + spec["context_keywords"])
        for hit in headline_hits[:3]:
            add_score(key, 2.5, f"title:{hit}")
        for hit in context_hits[:3]:
            add_score(key, 1.5, f"context:{hit}")
        for hit in url_hits[:2]:
            add_score(key, 1.0, f"url:{hit}")

    if scores["ec"] >= 9.0:
        scores["ec"] += 1.0

    ranked = sorted(
        (
            {
                "key": key,
                "label": spec["label"],
                "style": spec["style"],
                "score": round(scores[key], 1),
                "signals": reasons[key][:6],
            }
            for key, spec in persona_specs.items()
            if scores[key] > 0
        ),
        key=lambda item: (-float(item.get("score", 0)), str(item.get("label", ""))),
    )
    if ranked:
        return ranked
    return [
        {
            "key": "default",
            "label": "検討中ユーザー向け",
            "style": "必要な条件を先に知りたい人",
            "score": 0.0,
            "signals": ["fallback:generic"],
        }
    ]

def _build_faq_persona(context: Dict[str, Any]) -> Dict[str, Any]:
    candidates = _build_faq_persona_candidates(context)
    business_goal = _safe_text(context.get("business_goal"))
    primary = dict(candidates[0]) if candidates else {
        "key": "default",
        "label": "検討中ユーザー向け",
        "style": "必要な条件を先に知りたい人",
        "score": 0.0,
        "signals": ["fallback:generic"],
    }
    secondary_score = float(candidates[1].get("score", 0)) if len(candidates) > 1 else 0.0
    primary_score = float(primary.get("score", 0) or 0)
    score_gap = primary_score - secondary_score

    if primary_score >= 9 and score_gap >= 4:
        confidence = "high"
    elif primary_score >= 5 and score_gap >= 1.5:
        confidence = "medium"
    else:
        confidence = "low"

    goal_hint_map = {
        "オーガニック流入増加（SEO優先）": "検索段階で比較されやすい論点を先に出す構成",
        "AI検索での引用増加（GEO/AIO優先）": "AIが短く抜き出しやすい言い回し",
        "CV率・リード獲得（CTA改善優先）": "問い合わせ前の不安を減らす説明順",
        "ブランド認知・指名検索強化": "初見でもブランド理解が進む説明順",
        "サイト技術健全性（エンジニア優先）": "要件と根拠を確認しやすい説明順",
    }
    goal_hint = goal_hint_map.get(business_goal, "検討時の不安を減らす説明順")

    return {
        "label": _safe_text(primary.get("label")),
        "style": _safe_text(primary.get("style")),
        "goal_hint": goal_hint,
        "source": _safe_text((primary.get("signals") or ["fallback:generic"])[0]),
        "confidence": confidence,
        "score": primary_score,
        "candidates": candidates[:4],
    }

def _build_offer_label(context: Dict[str, Any]) -> str:
    for value in (
        context.get("page_focus"),
        context.get("business_type"),
        context.get("industry"),
        context.get("site_type"),
    ):
        text = _clean_page_focus(value)
        if text:
            return text
    return "このサービス"

def _personalize_non_ec_faq(candidate: Dict[str, Any], context: Dict[str, Any], persona: Dict[str, str]) -> Dict[str, Any]:
    topic = _safe_text(candidate.get("topic"))
    industry = _safe_text(context.get("industry")) or "このサービス"
    offer_label = _build_offer_label(context)
    site_type = _safe_text(context.get("site_type")) or "サイト"
    business_goal = _safe_text(context.get("business_goal"))
    lmo_profile = context.get("lmo_profile") or {}
    is_saas = _contains_any(industry, ["IT", "SaaS", "ソフトウェア", "システム", "DX"])
    is_corporate = _contains_any(site_type, ["企業", "法人", "会社"])
    is_regulated = _contains_any(industry, ["金融", "保険", "医療", "美容", "健康", "サプリ", "士業"])
    is_lmo = bool(lmo_profile.get("is_location_or_visit"))
    consumer_profile = _faq_consumer_profile(context)
    is_consumer_context = bool(consumer_profile)
    is_corporate_copy = is_corporate and not is_consumer_context

    question = _safe_text(candidate.get("question"))
    answer = _safe_text(candidate.get("answer"))

    if topic == "audience_value":
        if is_lmo:
            question = "初めて行く前に、何を確認しておくと安心ですか？"
            answer = "アクセス、営業時間、予約の要否、現地で確認できる設備を先にまとめると、来訪前ユーザーが迷いにくくなります。"
        elif is_consumer_context:
            question = f"{_safe_text(consumer_profile.get('label')) or offer_label}は初めてでも利用しやすいですか？"
            answer = (
                "初めての人が判断できるよう、対象者、利用シーン、料金の見方、問い合わせ前に確認することを"
                "冒頭とFAQで同じ言葉にそろえると伝わりやすくなります。"
            )
        else:
            question = f"{offer_label}はどんな課題から先に役立ちますか？"
            answer = (
                f"{persona['label']}が読み始めてすぐ判断できるよう、{industry}で起こりやすい課題、"
                "解決できる範囲、導入後に変わることを冒頭で3点に整理すると伝わりやすくなります。"
            )
    elif topic == "fit":
        if persona["label"] == "案内確認ユーザー向け":
            question = "利用対象や会員・一般の違いはどこで確認できますか？"
            answer = "対象者、会員向けと一般向けの違い、申込条件を分けて示すと、制度や窓口の案内として使いやすくなります。"
        elif is_consumer_context:
            question = "どんな人に向いていて、どんな場合は事前相談が必要ですか？"
            answer = "向いている利用シーン、対象外になりやすい条件、事前に相談した方がよいケースを分けると、初めての人が判断しやすくなります。"
        else:
            question = "どんな人・企業に向いていて、どんなケースは対象外ですか？"
            answer = (
                f"{persona['style']}が迷わないよう、向いている利用シーン、相性のよい業種や規模、"
                "逆に合わない条件までFAQで並べると問い合わせの質が安定します。"
            )
    elif topic == "pricing":
        if is_consumer_context:
            question = _safe_text(consumer_profile.get("pricing_question")) or "料金・費用・追加料金はどこで確認できますか？"
            answer = _safe_text(consumer_profile.get("pricing_answer")) or "基本料金、追加費用、支払い方法、比較時に見落としやすい条件を分けて示します。"
        elif is_saas:
            question = "初期費用・月額・追加料金の考え方は？"
            answer = (
                "初期費用、月額、オプション料金、最低契約期間を1つの表にまとめ、"
                "どこから個別見積になるのかを先に示すとSaaS比較で迷われにくくなります。"
            )
        elif is_corporate_copy:
            question = "見積や費用は何を基準に決まりますか？"
            answer = (
                "費用算定の基準、見積時に必要な情報、追加費用が発生しやすい条件をFAQで明示すると、"
                "担当者が社内説明しやすくなります。"
            )
        else:
            question = "料金に何が含まれますか？追加費用はありますか？"
            answer = (
                "基本料金に含まれる範囲と、追加料金が発生するケースを分けて書くと、"
                "検討ユーザーが比較しやすくなります。"
            )
    elif topic == "process":
        if is_consumer_context:
            question = _safe_text(consumer_profile.get("process_question")) or "予約・相談・申込から利用開始までの流れは？"
            answer = _safe_text(consumer_profile.get("process_answer")) or "問い合わせ、予約または申込、必要情報、当日の流れ、利用開始までを時系列で示します。"
        elif is_lmo:
            question = "予約や来店までの流れは？"
            answer = "予約の要否、当日受付の有無、来店前に確認したい注意点を時系列で並べると、現地利用の前に迷いにくくなります。"
        elif persona["label"] == "案内確認ユーザー向け":
            question = "相談や申込の流れはどこで確認できますか？"
            answer = "対象者、必要情報、申込方法、結果連絡までの流れを段階ごとに示すと、制度や窓口の利用前に迷いにくくなります。"
        else:
            question = "問い合わせ後、導入や申込まではどんな流れですか？" if is_corporate_copy else "申込から利用開始まではどんな流れですか？"
            answer = (
                "初回相談、必要情報、見積や契約、開始までの段階を時系列で示し、"
                "各ステップの所要日数を添えると不安が減ります。"
            )
    elif topic == "comparison":
        question = "他社サービスと比較するときの確認ポイントは？"
        answer = (
            f"{_faq_business_goal_for_copy(context)}を意識して、選定基準、向いているケース、"
            "代替案との差が出る条件を3項目程度で並べると判断材料になります。"
        )
    elif topic == "trust":
        question = "監修体制や運営者情報はどこで確認できますか？" if is_regulated else "運営会社・担当者情報はどこで確認できますか？"
        answer = (
            "会社概要、担当者プロフィール、監修者、一次情報の出典、問い合わせ窓口を近い場所にまとめると、"
            f"{persona['label']}にも信頼の根拠が伝わりやすくなります。"
        )
    elif topic == "case":
        question = "導入事例や成果はどのように確認できますか？"
        answer = (
            "事例の有無だけでなく、どの業種・規模で、何を改善できたか、"
            "再現しやすい条件は何かまで短く示すと説得力が上がります。"
        )
    elif topic == "support":
        if is_consumer_context:
            question = _safe_text(consumer_profile.get("support_question")) or "問い合わせ前に確認しておくことは？"
            answer = _safe_text(consumer_profile.get("support_answer")) or "受付時間、返信目安、準備しておく情報、対象外の条件をまとめると問い合わせ前の不安を減らせます。"
        elif persona["label"] == "案内確認ユーザー向け":
            question = "相談窓口と回答目安は？"
            answer = "問い合わせ窓口、受付時間、対象外の相談、回答目安をまとめると、制度案内や窓口案内として分かりやすくなります。"
        else:
            question = "問い合わせ前に準備すべき情報と回答目安は？" if is_corporate_copy else "問い合わせ方法と回答目安は？"
            answer = (
                "窓口、受付時間、返信目安、問い合わせ時に必要な情報をFAQに置くと、"
                "商談前や申込前の往復を減らしやすくなります。"
            )
    elif topic == "security":
        question = "セキュリティ体制と個人情報の扱いは？"
        answer = (
            "保管方法、権限管理、委託先の扱い、個人情報の保存期間をまとめて示すと、"
            f"{industry}で気にされやすい安全面の不安を先回りできます。"
        )
    elif topic == "access":
        question = "アクセス方法・最寄り駅・駐車場は？"
        answer = "最寄り駅、徒歩や車での行き方、駐車場の有無を1つにまとめると、初めて訪れる人が迷いにくくなります。"
    elif topic == "hours":
        question = "営業時間・定休日・混雑しやすい時間帯は？"
        answer = "営業時間、定休日、ラストオーダー、混みやすい時間帯が分かると、来訪前に予定を立てやすくなります。"
    elif topic == "reservation":
        question = "予約方法・当日利用・席や設備の確認方法は？"
        answer = "予約の要否、当日受付、席数や個室、設備の確認方法を先に示すと、来店前や来場前の不安が減ります。"
    elif topic == "public_services":
        question = "どんな支援・サービスが受けられますか？"
        answer = "支援メニューの一覧だけでなく、相談できる内容、利用目的ごとの違い、まず見るべき入口を分けて示すと、案内情報として使いやすくなります。"
    elif topic == "public_eligibility":
        question = "対象者・会員/一般の違い・利用条件は？"
        answer = "対象者、会員向けと一般向けの違い、申込条件、利用できないケースを分けて示すと、自分が対象かどうかを判断しやすくなります。"
    elif topic == "public_application":
        question = "申込に必要な情報と手続きの流れは？"
        answer = "申込方法、必要情報、締切、結果連絡までの流れを段階ごとに示すと、制度や講座の利用前に迷いにくくなります。"

    rewritten = dict(candidate)
    rewritten["base_question"] = _safe_text(candidate.get("question"))
    rewritten["base_answer"] = _safe_text(candidate.get("answer"))
    rewritten["question"] = question
    rewritten["answer"] = answer
    rewritten["persona_label"] = persona["label"]
    rewritten["presentation_mode"] = "contextualized"
    rewritten["goal_hint"] = persona["goal_hint"]
    rewritten.update(_faq_value_fields(rewritten, context))
    return rewritten

def _personalize_ec_faq(candidate: Dict[str, Any], context: Dict[str, Any], persona: Dict[str, str]) -> Dict[str, Any]:
    topic = _safe_text(candidate.get("topic"))
    question = _safe_text(candidate.get("question"))
    answer = _safe_text(candidate.get("answer"))

    if topic == "delivery":
        question = "送料・配送日数・到着目安は？"
        answer = "送料、地域差、発送までの日数、到着目安、日時指定の可否を1つのFAQでまとめると購入前の離脱を減らしやすくなります。"
    elif topic == "returns":
        question = "返品・交換の条件は？"
        answer = "返品期限、未開封条件、返送料の負担、不良品時の扱いを分けて書くと、購入前ユーザーが判断しやすくなります。"
    elif topic == "payment":
        question = "使える支払い方法と手数料は？"
        answer = "利用可能な決済手段、ブランド、手数料、支払期限を並べると、カート直前での離脱を抑えやすくなります。"
    elif topic == "cancel":
        question = "キャンセルや注文変更はいつまで可能ですか？"
        answer = "発送前後での扱いの違い、変更受付の締切、連絡方法を先に示すと問い合わせが減ります。"
    elif topic == "contact":
        question = "問い合わせ窓口と回答目安は？"
        answer = "フォーム・メール・電話などの窓口、受付時間、返信目安を明記すると、購入前ユーザーの不安を減らしやすくなります。"

    rewritten = dict(candidate)
    rewritten["base_question"] = _safe_text(candidate.get("question"))
    rewritten["base_answer"] = _safe_text(candidate.get("answer"))
    rewritten["question"] = question
    rewritten["answer"] = answer
    rewritten["persona_label"] = persona["label"]
    rewritten["presentation_mode"] = "contextualized"
    rewritten["goal_hint"] = persona["goal_hint"]
    rewritten.update(_faq_value_fields(rewritten, context))
    return rewritten

def _personalize_faq_candidates(candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    persona = _build_faq_persona(context)
    personalized: List[Dict[str, Any]] = []
    for candidate in candidates:
        if context.get("effective_is_ec"):
            personalized.append(_personalize_ec_faq(candidate, context, persona))
        else:
            personalized.append(_personalize_non_ec_faq(candidate, context, persona))
    return personalized

def _build_faq_debug_payload(
    *,
    context: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    suggestions: List[Dict[str, Any]],
    strategy: str,
) -> Dict[str, Any]:
    selected_topics = {(_safe_text(item.get("topic")), _safe_text(item.get("base_question") or item.get("question"))) for item in suggestions}
    debug_candidates = []
    for item in sorted(candidates, key=lambda row: (-int(row.get("score", 0)), str(row.get("question", ""))))[:10]:
        base_question = _safe_text(item.get("question"))
        topic = _safe_text(item.get("topic"))
        debug_candidates.append(
            {
                "topic": topic,
                "base_question": base_question,
                "score": int(item.get("score", 0) or 0),
                "matched_keywords": _safe_text_list(item.get("matched_keywords") or [], limit=6),
                "source_label": _safe_text(item.get("source_label")),
                "selected": (topic, base_question) in selected_topics,
            }
        )

    return {
        "strategy": strategy,
        "persona": _build_faq_persona(context),
        "context": {
            "industry": _safe_text(context.get("industry")),
            "site_type": _safe_text(context.get("site_type")),
            "platform": _safe_text(context.get("platform")),
            "business_goal": _safe_text(context.get("business_goal")),
            "page_focus": _safe_text(context.get("page_focus")),
            "page_title": _safe_text(context.get("page_title")),
            "meta_description": _safe_text(context.get("meta_description")),
            "raw_page_title_headings": _safe_text_list(context.get("raw_page_title_headings") or [], limit=6),
            "page_service_terms": _safe_text_list(context.get("page_service_terms") or [], limit=6),
            "location_terms": _safe_text_list(context.get("location_terms") or [], limit=6),
            "transaction_terms": _safe_text_list(context.get("transaction_terms") or [], limit=6),
            "customer_intent_terms": _safe_text_list(context.get("customer_intent_terms") or [], limit=6),
            "audience_clues": _safe_text_list(context.get("audience_clues") or [], limit=4),
            "regulatory_indicators": _safe_text_list(context.get("regulatory_indicators") or [], limit=4),
            "summary_improvements": _safe_text_list(context.get("summary_improvements") or [], limit=4),
            "url_signal_tokens": _safe_text_list(context.get("url_signal_tokens") or [], limit=6),
            "domain_profile": _json_clone(context.get("domain_profile") or {}) or {},
            "lmo_profile": _json_clone(context.get("lmo_profile") or {}) or {},
            "ec_guardrail": _json_clone(context.get("ec_guardrail") or {}) or {},
            "context_excerpt": _compact_marketer_excerpt(context.get("context_text"), limit=160),
        },
        "candidates": debug_candidates,
        "selected_count": len(suggestions),
    }

def _build_faq_suggestion_payload(results: Dict[str, Any], max_items: int = 5) -> Dict[str, Any]:
    existing = results.get("faq_suggestions")
    if isinstance(existing, list) and existing:
        context = _collect_faq_context(results)
        existing_rows = _json_clone(existing[:max_items]) or []
        return {
            "suggestions": existing_rows,
            "debug": _build_faq_debug_payload(
                context=context,
                candidates=existing_rows,
                suggestions=existing_rows,
                strategy="precomputed",
            ),
        }

    context = _collect_faq_context(results)
    candidates = _build_ec_faq_candidates(context) if context.get("effective_is_ec") else _build_non_ec_faq_candidates(context)
    selected = _dedupe_faq_candidates(candidates, max_items=max_items)
    if selected:
        personalized = _personalize_faq_candidates(selected, context)
        return {
            "suggestions": _json_clone(personalized) or [],
            "debug": _build_faq_debug_payload(
                context=context,
                candidates=candidates,
                suggestions=personalized,
                strategy="template_plus_context_rewrite",
            ),
        }

    preferred: List[Dict[str, Any]] = []
    blacklist = ("返品", "配送", "送料", "支払い", "注文", "キャンセル")
    for item in get_all_faqs("simple") or []:
        question = _safe_text((item or {}).get("question"))
        if any(word in question for word in blacklist):
            continue
        preferred.append(item)
    fallback = _json_clone(preferred[:max_items]) or []
    return {
        "suggestions": fallback,
        "debug": _build_faq_debug_payload(
            context=context,
            candidates=fallback,
            suggestions=fallback,
            strategy="fallback_glossary",
        ),
    }

def _build_non_ec_faq_candidates(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    industry = context["industry"] or "このサービス"
    site_type = context["site_type"] or "企業サイト"
    platform = context["platform"]
    text = context["context_text"]
    lmo_profile = context.get("lmo_profile") or {}
    domain_profile = context.get("domain_profile") or {}

    issue_keywords = {
        "trust": ["e-e-a-t", "著者", "運営者", "会社", "問い合わせ", "privacy", "個人情報", "信頼"],
        "pricing": ["料金", "費用", "価格", "plan", "プラン", "見積", "コスト"],
        "process": ["導入", "相談", "申込", "予約", "利用開始", "手順", "流れ"],
        "comparison": ["比較", "違い", "選び方", "競合", "他社"],
        "case": ["事例", "実績", "導入社数", "成功", "お客様"],
        "support": ["問い合わせ", "support", "サポート", "連絡", "対応時間"],
        "security": ["セキュリティ", "security", "権限", "個人情報", "認証"],
        "audience": ["対象", "向いて", "おすすめ", "業種", "用途"],
        "access": ["アクセス", "最寄り", "駅", "駐車場", "地図", "行き方"],
        "hours": ["営業時間", "定休日", "受付時間", "営業日", "ラストオーダー"],
        "reservation": ["予約", "席", "個室", "当日利用", "来店", "受付"],
        "public_services": ["支援", "サービス", "講座", "セミナー", "制度", "事業", "メニュー", "相談内容"],
        "public_eligibility": ["対象者", "会員", "一般", "利用条件", "申込条件", "参加対象", "会費"],
        "public_application": ["申込", "申請", "手続き", "必要書類", "締切", "受付", "窓口"],
    }

    is_saas = _contains_any(industry, ["IT", "SaaS", "ソフトウェア", "システム", "DX"])
    is_regulated = _contains_any(industry, ["金融", "保険", "医療", "美容", "健康", "サプリ", "士業"])
    is_corporate = _contains_any(site_type, ["企業", "法人", "会社"])
    is_lmo = bool(lmo_profile.get("is_location_or_visit"))
    prefer_public = bool((domain_profile or {}).get("prefer_public_info"))

    audience_hits = _collect_keyword_hits(text, issue_keywords["audience"])
    comparison_hits = _collect_keyword_hits(text, issue_keywords["comparison"])
    pricing_hits = _collect_keyword_hits(text, issue_keywords["pricing"])
    process_hits = _collect_keyword_hits(text, issue_keywords["process"])
    trust_hits = _collect_keyword_hits(text, issue_keywords["trust"])
    case_hits = _collect_keyword_hits(text, issue_keywords["case"])
    support_hits = _collect_keyword_hits(text, issue_keywords["support"])
    security_hits = _collect_keyword_hits(text, issue_keywords["security"])
    access_hits = _collect_keyword_hits(text, issue_keywords["access"]) or _safe_text_list(((lmo_profile.get("category_hits") or {}).get("access") or []), limit=4)
    hours_hits = _collect_keyword_hits(text, issue_keywords["hours"]) or _safe_text_list(((lmo_profile.get("category_hits") or {}).get("hours") or []), limit=4)
    reservation_hits = _collect_keyword_hits(text, issue_keywords["reservation"]) or _safe_text_list(((lmo_profile.get("category_hits") or {}).get("reservation") or []), limit=4)
    public_service_hits = _collect_keyword_hits(text, issue_keywords["public_services"])
    public_eligibility_hits = _collect_keyword_hits(text, issue_keywords["public_eligibility"])
    public_application_hits = _collect_keyword_hits(text, issue_keywords["public_application"])

    return [
        _faq_candidate(
            question="このサービスはどんな課題を解決できますか？",
            answer=f"{industry}の文脈で、誰のどんな悩みを解決するのかを最初に明示すると理解されやすくなります。対象者、解決できる課題、得られる成果をFAQでも本文でも同じ表現で整理します。",
            score=3 + (2 if audience_hits or comparison_hits else 0) + (1 if prefer_public else 0) - (1 if is_lmo else 0),
            source_label="URL不足ベース",
            reason="対象者と提供価値が一目で分かる導線を補うためのFAQです。",
            topic="audience_value",
            matched_keywords=audience_hits + comparison_hits,
        ),
        _faq_candidate(
            question="どんな人・企業に向いていますか？",
            answer=f"{site_type}として想定している利用者像、向いているケース、逆に適さないケースまで示すと、問い合わせ前の迷いを減らせます。業種や利用シーンを2〜3例で補足する構成が有効です。",
            score=3 + (3 if audience_hits else 0) + (2 if prefer_public else 0),
            source_label="URL不足ベース",
            reason="対象読者が自分ごと化しやすいFAQが不足しているためです。",
            topic="fit",
            matched_keywords=audience_hits,
        ),
        _faq_candidate(
            question="料金や費用感はどのように確認できますか？",
            answer="料金表がまだ出せない場合でも、見積の考え方、最低契約期間、追加費用が発生しやすい条件をFAQに置くと離脱を防ぎやすくなります。",
            score=2 + (5 if pricing_hits else 0) + (1 if is_saas else 0) - (1 if is_lmo or prefer_public else 0),
            source_label="issue / citation ベース",
            reason="料金・費用まわりの説明不足を埋める優先度が高いためです。",
            topic="pricing",
            matched_keywords=pricing_hits,
        ),
        _faq_candidate(
            question="相談から導入・申込までの流れは？",
            answer="初回相談、必要情報、契約、開始までの流れを段階ごとに整理すると、申し込み前の不安が減ります。所要日数や担当者とのやり取りも合わせて記載します。",
            score=2 + (5 if process_hits else 0) + (1 if is_corporate and not is_lmo and not prefer_public else 0) + (1 if prefer_public else 0) - (2 if prefer_public else 0),
            source_label="issue / citation ベース",
            reason="導入導線や手順の見えにくさを解消するためです。",
            topic="process",
            matched_keywords=process_hits,
        ),
        _faq_candidate(
            question="他社サービスとの違いや選び方は？",
            answer=f"{industry}では比較検討で離脱しやすいため、選定基準、向いているケース、比較されやすい代替案との違いをFAQで短く整理すると引用候補にもなりやすくなります。",
            score=2 + (5 if comparison_hits else 0) + (1 if context["citation_count"] > 0 else 0) - (1 if is_lmo or prefer_public else 0),
            source_label="citation / issue ベース",
            reason="比較・選び方の観点が不足しているためです。",
            topic="comparison",
            matched_keywords=comparison_hits,
        ),
        _faq_candidate(
            question="運営会社や監修者の信頼情報はどこで確認できますか？",
            answer="会社概要、担当者プロフィール、監修者、一次情報の出典などを1か所にまとめると、AI検索でも通常検索でも信頼性が伝わりやすくなります。",
            score=2 + (6 if trust_hits else 0),
            source_label="issue ベース",
            reason="運営者・著者・問い合わせなどの信頼情報を補う必要があるためです。",
            topic="trust",
            matched_keywords=trust_hits,
        ),
        _faq_candidate(
            question="導入事例や実績はありますか？",
            answer="事例の有無だけでなく、どの業種・規模で、どんな成果が出たのかを簡潔に示すと説得力が上がります。数字や引用できる事実を添えると効果的です。",
            score=2 + (4 if case_hits else 0) + (1 if context["citation_count"] > 0 else 0) - (1 if is_lmo or prefer_public else 0),
            source_label="citation ベース",
            reason="実績・数値・具体例を補強するFAQ候補です。",
            topic="case",
            matched_keywords=case_hits,
        ),
        _faq_candidate(
            question="問い合わせ方法と回答までの目安は？",
            answer="問い合わせ窓口、受付時間、返信目安、事前に用意するとよい情報をFAQ化すると、商談前の不安を減らせます。",
            score=2 + (4 if support_hits else 0) + (1 if prefer_public else 0),
            source_label="issue ベース",
            reason="問い合わせ前の不明点を減らすためのFAQです。",
            topic="support",
            matched_keywords=support_hits,
        ),
        _faq_candidate(
            question="セキュリティや個人情報保護はどうなっていますか？",
            answer=f"{industry}では安全性への不安が比較の障壁になりやすいため、保管方法、アクセス制御、運用ルール、個人情報の扱いをまとめて説明すると効果的です。",
            score=1 + (5 if security_hits else 0) + (2 if is_saas or is_regulated else 0) + (1 if _contains_any(platform, ["WordPress", "Wix"]) else 0),
            source_label="業界 / platform ベース",
            reason="安全性・個人情報保護への関心が高い業界・構成だからです。",
            topic="security",
            matched_keywords=security_hits,
        ),
        _faq_candidate(
            question="アクセス方法・最寄り駅・駐車場は？",
            answer="最寄り駅、徒歩や車での行き方、駐車場の有無をまとめると、初めて訪れる人が迷いにくくなります。",
            score=1 + (4 if access_hits else 0) + (3 if is_lmo else 0) - (4 if prefer_public else 0),
            source_label="LMO / issue ベース",
            reason="来訪前に必要な現地情報を補うFAQです。",
            topic="access",
            matched_keywords=access_hits,
        ),
        _faq_candidate(
            question="営業時間・定休日・混雑しやすい時間帯は？",
            answer="営業時間、定休日、ラストオーダー、混みやすい時間帯が分かると、来訪前に予定を立てやすくなります。",
            score=1 + (4 if hours_hits else 0) + (3 if is_lmo else 0) - (4 if prefer_public else 0),
            source_label="LMO / issue ベース",
            reason="来訪タイミングの判断に必要な情報を補うFAQです。",
            topic="hours",
            matched_keywords=hours_hits,
        ),
        _faq_candidate(
            question="予約方法・当日利用・席や設備の確認方法は？",
            answer="予約の要否、当日受付、席や個室、設備の確認方法をまとめると、来店前や来場前の不安を減らしやすくなります。",
            score=1 + (4 if reservation_hits else 0) + (3 if is_lmo else 0) - (4 if prefer_public else 0),
            source_label="LMO / issue ベース",
            reason="予約や現地利用に関するFAQが不足しやすいためです。",
            topic="reservation",
            matched_keywords=reservation_hits,
        ),
        _faq_candidate(
            question="どんな支援・サービスが受けられますか？",
            answer="支援内容の一覧だけでなく、相談できる内容、利用目的ごとの違い、まず見るべき入口を分けると案内として使いやすくなります。",
            score=(2 + (5 if public_service_hits else 0) + 4) if prefer_public else 0,
            source_label="公共案内 / issue ベース",
            reason="支援メニューやサービス内容を案内しやすくするFAQです。",
            topic="public_services",
            matched_keywords=public_service_hits,
        ),
        _faq_candidate(
            question="対象者・会員/一般の違い・利用条件は？",
            answer="対象者、会員向けと一般向けの違い、利用条件、対象外ケースを整理すると、制度や支援の案内として分かりやすくなります。",
            score=(2 + (5 if public_eligibility_hits else 0) + 4) if prefer_public else 0,
            source_label="公共案内 / issue ベース",
            reason="利用条件や対象者を明確にするFAQです。",
            topic="public_eligibility",
            matched_keywords=public_eligibility_hits,
        ),
        _faq_candidate(
            question="申込に必要な情報と手続きの流れは？",
            answer="申込方法、必要情報、締切、結果連絡までの流れを段階ごとに示すと、講座や制度の利用前に迷いにくくなります。",
            score=(2 + (5 if public_application_hits else 0) + 4) if prefer_public else 0,
            source_label="公共案内 / issue ベース",
            reason="申込や窓口利用の流れを分かりやすくするFAQです。",
            topic="public_application",
            matched_keywords=public_application_hits,
        ),
    ]

def _build_ec_faq_candidates(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = context["context_text"]
    platform = context["platform"]
    templates = get_ec_faq_templates("simple") or []
    keyword_map = {
        "返品": ["返品", "交換", "返金", "不良品"],
        "送料": ["配送", "送料", "発送", "お届け", "到着"],
        "支払い": ["支払い", "決済", "クレジット", "後払い", "手数料"],
        "キャンセル": ["キャンセル", "取消"],
        "変更": ["注文変更", "変更", "修正"],
        "問い合わせ": ["問い合わせ", "サポート", "連絡", "対応時間"],
    }
    platform_boost = 1 if _contains_any(platform, ["Shopify", "楽天", "Yahoo", "Amazon", "Wix"]) else 0

    candidates: List[Dict[str, Any]] = []
    for template in templates:
        question = _safe_text(template.get("question"))
        answer = _safe_text(template.get("answer"))
        score = 2 + platform_boost
        reason = "EC導線で確認されやすい論点を補うためのFAQです。"
        question_text = question.lower()
        topic = ""
        matched_keywords: List[str] = []
        for label, keywords in keyword_map.items():
            keyword_hits = _collect_keyword_hits(text, keywords)
            if label.lower() in question_text:
                topic_map = {
                    "返品": "returns",
                    "送料": "delivery",
                    "支払い": "payment",
                    "キャンセル": "cancel",
                    "変更": "cancel",
                    "問い合わせ": "contact",
                }
                topic = topic_map.get(label, topic)
            if label.lower() in question_text and keyword_hits:
                score += 5
                reason = f"{label}に関する説明不足を埋めるためです。"
                matched_keywords.extend(keyword_hits)
        candidates.append(
            _faq_candidate(
                question=question,
                answer=answer,
                score=score,
                source_label="EC / issue ベース",
                reason=reason,
                topic=topic,
                matched_keywords=matched_keywords,
            )
        )
    return candidates

def _build_faq_suggestions(results: Dict[str, Any], max_items: int = 5) -> List[Dict[str, Any]]:
    payload = _build_faq_suggestion_payload(results, max_items=max_items)
    return _json_clone(payload.get("suggestions") or []) or []

build_faq_suggestion_payload = _build_faq_suggestion_payload
build_faq_suggestions = _build_faq_suggestions
