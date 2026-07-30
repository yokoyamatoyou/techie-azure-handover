from __future__ import annotations

from typing import Any, Dict, List

from core.application.faq_suggestion_builder import (
    _collect_faq_context,
    _collect_keyword_hits,
    _heading_texts_from_results,
    _json_clone,
    _safe_text,
    _safe_text_list,
)

_PAGE_ROLE_SPECS = [
    {
        "role": "法務/会社情報ページ",
        "intent": "この会社・店舗・運営者が信頼できるか、取引前に確認したい検索意図",
        "keywords": [
            "会社概要", "運営者", "事業者", "特商法", "特定商取引", "プライバシー", "個人情報",
            "利用規約", "所在地", "代表者", "法人", "about", "company", "privacy", "terms", "law",
        ],
        "required_groups": [
            ("会社名・所在地・連絡先", ["会社名", "所在地", "住所", "電話", "連絡先", "メール"]),
            ("責任者・運営者情報", ["代表", "責任者", "運営者", "担当者"]),
            ("法務リンク", ["特商法", "特定商取引", "プライバシー", "個人情報", "利用規約"]),
            ("問い合わせ導線", ["問い合わせ", "相談", "連絡", "フォーム"]),
        ],
        "action": "会社名・所在地・連絡先・責任者・法務リンクを同じページ内で確認できるようにし、主要ページからこのページへ内部リンクを追加します。",
        "summary": "取引前の不安を減らし、AI回答でも運営者情報を根拠として拾いやすくします。",
        "headings": ["運営者情報", "所在地・連絡先", "特定商取引法に基づく表記", "個人情報の取り扱い"],
        "faq": ["問い合わせ前に確認できる情報は何ですか？", "個人情報はどのように扱われますか？"],
        "schema": "Organization / LocalBusiness / ContactPoint",
        "internal_link": "料金・相談・申込・資料請求CTA付近から会社概要または法務ページへリンク",
    },
    {
        "role": "料金/予約/相談・資料請求ページ",
        "intent": "費用、相談、申込、資料請求、予約の条件を確認して次の行動を決めたい検索意図",
        "keywords": [
            "料金", "費用", "価格", "プラン", "見積", "資料請求", "予約", "相談", "問い合わせ", "申込", "申し込み",
            "購入", "注文", "来店", "空き", "初回", "price", "pricing", "plan", "reserve", "booking",
            "contact", "apply", "reservation", "checkout", "cart",
        ],
        "required_groups": [
            ("費用・条件・必要情報", ["料金", "費用", "価格", "プラン", "見積", "条件", "必要", "対象", "送料", "支払い"]),
            ("相談・申込・資料請求の流れ", ["予約", "相談", "申込", "資料請求", "問い合わせ", "購入", "注文", "来店"]),
            ("必要情報・所要時間", ["必要", "持ち物", "所要", "期間", "納期", "当日", "流れ"]),
            ("変更・注意事項・対象外条件", ["変更", "注意事項", "対象外", "キャンセル", "返品", "交換"]),
        ],
        "action": "CTA直前に料金・相談/申込/資料請求の流れ・必要情報・よくある不安をまとめ、役割に合う質問回答を追加します。",
        "summary": "迷っている人が問い合わせ、資料請求、申込、予約などの判断材料を得られ、AI回答でも費用や手順を引用しやすくなります。",
        "headings": ["料金・費用", "相談・申込・資料請求の流れ", "利用前に必要な情報", "よくある質問"],
        "faq": ["料金・追加費用はどこで確認できますか？", "相談・申込・資料請求から利用開始までの流れは？"],
        "schema": "FAQPage / Service / Offer",
        "internal_link": "サービス説明、比較、FAQから料金・相談・申込・資料請求CTAへリンク",
    },
    {
        "role": "比較検討ページ",
        "intent": "複数の選択肢や条件を比べ、自分に合うか判断したい検索意図",
        "keywords": [
            "比較", "選び方", "違い", "おすすめ", "ランキング", "口コミ", "レビュー", "評判",
            "事例", "実績", "導入事例", "メリット", "デメリット", "compare", "review", "case",
        ],
        "required_groups": [
            ("比較軸", ["比較", "選び方", "違い", "メリット", "デメリット"]),
            ("実績・事例・口コミ", ["実績", "事例", "口コミ", "レビュー", "評判", "お客様の声"]),
            ("料金・条件", ["料金", "費用", "条件", "プラン", "対象"]),
            ("次の行動", ["問い合わせ", "相談", "予約", "購入", "資料請求"]),
        ],
        "action": "選び方の比較表、実績/口コミ、料金条件、相談CTAを同じ読了導線に並べます。",
        "summary": "比較中の人が離脱せず判断でき、AI回答にも比較軸と根拠を渡しやすくなります。",
        "headings": ["選び方", "比較表", "実績・事例", "料金と相談方法"],
        "faq": ["選ぶときに見るべき違いは何ですか？", "自分に合う条件はどう確認できますか？"],
        "schema": "FAQPage / Review / Product or Service",
        "internal_link": "集客記事やサービス概要から比較表へ、比較表から料金/相談ページへリンク",
    },
    {
        "role": "信頼補強ページ",
        "intent": "実績、専門性、運営体制を確認して安心できるか判断したい検索意図",
        "keywords": [
            "実績", "事例", "お客様の声", "口コミ", "レビュー", "監修", "専門家", "スタッフ",
            "プロフィール", "認定", "資格", "受賞", "保証", "安全", "case", "voice", "staff",
        ],
        "required_groups": [
            ("実績・事例", ["実績", "事例", "導入事例", "お客様の声", "口コミ", "レビュー"]),
            ("専門性・資格", ["監修", "専門家", "資格", "認定", "受賞", "プロフィール"]),
            ("運営体制", ["スタッフ", "担当者", "サポート", "保証", "安全"]),
            ("問い合わせ導線", ["問い合わせ", "相談", "予約", "資料請求"]),
        ],
        "action": "実績・事例・担当者/監修者情報・相談CTAを近い位置に集約し、主要サービスページから内部リンクします。",
        "summary": "不安を持つユーザーに信頼根拠を示し、AI回答でも専門性や実績として引用されやすくします。",
        "headings": ["実績・事例", "担当者/監修者", "お客様の声", "相談方法"],
        "faq": ["どんな実績がありますか？", "担当者や監修者の専門性はどこで確認できますか？"],
        "schema": "Organization / Person / Review / FAQPage",
        "internal_link": "サービス説明と料金/相談ページから実績・担当者情報へリンク",
    },
    {
        "role": "集客ページ",
        "intent": "課題の解決方法、サービス内容、基礎知識を探している検索意図",
        "keywords": [
            "サービス", "できること", "解決", "方法", "流れ", "特徴", "初めて", "ガイド", "コラム",
            "記事", "ブログ", "ニュース", "悩み", "service", "guide", "column", "blog", "news",
        ],
        "required_groups": [
            ("誰向けか", ["対象", "向け", "こんな方", "初めて", "悩み"]),
            ("提供内容", ["サービス", "内容", "できること", "特徴", "解決"]),
            ("比較・判断材料", ["比較", "料金", "費用", "事例", "実績"]),
            ("次の行動", ["問い合わせ", "相談", "予約", "購入", "資料請求"]),
        ],
        "action": "冒頭に対象者・解決できること・次に見るページを追加し、料金/相談ページとFAQへ内部リンクします。",
        "summary": "検索から来た人が自分向けかすぐ判断でき、AI回答にもページの要点と次の導線を渡せます。",
        "headings": ["このページで分かること", "対象者", "解決できること", "次に見るページ"],
        "faq": ["このサービスはどんな人向けですか？", "次に何を確認すればよいですか？"],
        "schema": "Article / Service / FAQPage",
        "internal_link": "本文末と関連見出しから料金/相談、比較、信頼補強ページへリンク",
    },
]

def _make_intent_signal(source: str, term: str) -> Dict[str, str]:
    return {"source": source, "term": term}

def _collect_role_signals(results: Dict[str, Any]) -> Dict[str, Any]:
    basics = (results.get("seo_results") or {}).get("basics") or {}
    heading_texts = _heading_texts_from_results(results, limit=10)
    context = _collect_faq_context(results)
    title = _safe_text(basics.get("title"))
    meta_description = _safe_text(basics.get("meta_description"))
    url_tokens = _safe_text_list(context.get("url_signal_tokens") or [], limit=10)
    body_terms = _safe_text_list(
        (context.get("page_service_terms") or [])
        + (context.get("location_terms") or [])
        + (context.get("transaction_terms") or [])
        + (context.get("customer_intent_terms") or []),
        limit=12,
    )
    cta_terms = _collect_keyword_hits(
        " ".join([title, meta_description, " ".join(heading_texts), " ".join(url_tokens), " ".join(body_terms)]),
        ["問い合わせ", "相談", "予約", "申込", "申し込み", "購入", "資料請求", "見積", "来店", "contact", "apply", "booking", "reserve", "cart"],
    )
    source_texts = {
        "title": title,
        "meta": meta_description,
        "heading": " ".join(heading_texts),
        "url_path": " ".join(url_tokens),
        "body_word": " ".join(body_terms + _safe_text_list(context.get("summary_improvements") or [], limit=4)),
        "cta": " ".join(cta_terms),
    }
    return {
        "context": context,
        "title": title,
        "meta_description": meta_description,
        "heading_texts": heading_texts,
        "url_tokens": url_tokens,
        "body_terms": body_terms,
        "cta_terms": cta_terms,
        "source_texts": source_texts,
        "all_text": " ".join(value for value in source_texts.values() if value),
    }

def _score_page_role(spec: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    keywords = spec.get("keywords") or []
    score = 0
    source_hits: Dict[str, List[str]] = {}
    intent_signals: List[Dict[str, str]] = []
    for source, text in (signals.get("source_texts") or {}).items():
        hits = _collect_keyword_hits(text, keywords)
        if not hits:
            continue
        source_hits[source] = hits
        weight = {"title": 4, "heading": 3, "cta": 3, "url_path": 2, "meta": 2, "body_word": 1}.get(source, 1)
        score += len(hits) * weight
        for term in hits:
            intent_signals.append(_make_intent_signal(source, term))
    return {"score": score, "source_hits": source_hits, "intent_signals": intent_signals}

def _missing_role_content(spec: Dict[str, Any], all_text: str) -> List[str]:
    missing: List[str] = []
    for label, keywords in spec.get("required_groups") or []:
        if not _collect_keyword_hits(all_text, keywords):
            missing.append(label)
    return missing[:4]

def _role_confidence(score: int, source_hits: Dict[str, List[str]], missing: List[str]) -> str:
    strong_sources = [source for source in ("title", "heading", "url_path", "cta") if source_hits.get(source)]
    if score >= 8 and len(strong_sources) >= 2 and len(missing) <= 2:
        return "high"
    if score >= 3 or strong_sources:
        return "medium"
    return "low"

def _role_confidence_label(confidence: str) -> str:
    return {
        "high": "判定根拠: 高",
        "medium": "判定根拠: 中",
        "low": "判定根拠: 低",
    }.get(_safe_text(confidence), "判定根拠: 低")

def _build_search_intent_role_map(results: Dict[str, Any]) -> Dict[str, Any]:
    signals = _collect_role_signals(results)
    scored = []
    for spec in _PAGE_ROLE_SPECS:
        row = _score_page_role(spec, signals)
        scored.append((row["score"], spec, row))
    score, spec, role_score = sorted(scored, key=lambda item: (-item[0], str(item[1].get("role"))))[0]
    if score <= 0:
        spec = next(item for item in _PAGE_ROLE_SPECS if item["role"] == "集客ページ")
        role_score = _score_page_role(spec, signals)
        score = role_score["score"]

    missing = _missing_role_content(spec, signals.get("all_text") or "")
    confidence = _role_confidence(score, role_score.get("source_hits") or {}, missing)
    evidence_terms = _safe_text_list(
        [item.get("term") for item in (role_score.get("intent_signals") or [])]
        + signals.get("cta_terms", [])
        + signals.get("body_terms", []),
        limit=10,
    )
    if not evidence_terms:
        evidence_terms = _safe_text_list(
            [signals.get("title"), *signals.get("heading_texts", []), *signals.get("url_tokens", [])],
            limit=6,
        )
    missing_text = " / ".join(missing) if missing else "役割に必要な最低限の情報は概ね見えています"
    page_role = _safe_text(spec.get("role"))
    recommended_action = _safe_text(spec.get("action"))
    overview_items = [
        {
            "label": "このページの役割",
            "title": page_role,
            "detail": _safe_text(spec.get("intent")),
            "status": "pass" if confidence == "high" else "warn" if confidence == "medium" else "reference",
        },
        {
            "label": "不足",
            "title": "不足している情報",
            "detail": missing_text,
            "status": "warn" if missing else "pass",
        },
        {
            "label": "次にやること",
            "title": "次の作業",
            "detail": recommended_action,
            "status": "info",
        },
    ]
    return {
        "title": "検索意図・ページ役割マップ",
        "detail": f"{page_role}: {missing_text}",
        "status": "warn" if missing else "pass",
        "status_label": "要整理" if missing else "概ね整理済み",
        "page_role": page_role,
        "intent_signals": role_score.get("intent_signals") or [],
        "user_intent": _safe_text(spec.get("intent")),
        "missing_content": missing,
        "recommended_action": recommended_action,
        "non_engineer_summary": _safe_text(spec.get("summary")),
        "engineer_notes": {
            "fix_locations": ["本文上部", "CTA直前", "FAQセクション", "head内JSON-LD", "関連ページの内部リンク"],
            "add_headings": _safe_text_list(spec.get("headings") or [], limit=6),
            "add_faq": _safe_text_list(spec.get("faq") or [], limit=4),
            "structured_data": _safe_text(spec.get("schema")),
            "internal_links": _safe_text(spec.get("internal_link")),
        },
        "confidence": confidence,
        "confidence_label": _role_confidence_label(confidence),
        "evidence_terms": evidence_terms,
        "overview_items": overview_items[:3],
        "source_hits": role_score.get("source_hits") or {},
        "page_signals": {
            "title": signals.get("title"),
            "meta_description": signals.get("meta_description"),
            "headings": signals.get("heading_texts") or [],
            "url_path_terms": signals.get("url_tokens") or [],
            "cta_terms": signals.get("cta_terms") or [],
            "body_terms": signals.get("body_terms") or [],
        },
    }

build_search_intent_role_map = _build_search_intent_role_map
