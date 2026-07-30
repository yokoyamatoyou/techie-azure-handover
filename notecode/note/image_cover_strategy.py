"""Cover-image strategy helpers for note / Hatena-style blog eyecatches."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CoverStrategy:
    role: str
    visual_brief: str
    display_copy_shape: str
    text_variant_note: str
    no_text_variant_note: str
    preferred_subject_patterns: tuple[str, ...] = ()
    preferred_focus_terms: tuple[str, ...] = ()


_DEFAULT_COVER_STRATEGY = CoverStrategy(
    role="A horizontal blog cover that makes the article theme recognizable in a feed.",
    visual_brief="Use one clear subject, article-specific supporting context, and a polished visual mood.",
    display_copy_shape="Keep the copy concrete: subject plus one useful focus term.",
    text_variant_note="The text is a cover cue, not the article title.",
    no_text_variant_note="Use subject, composition, color, and atmosphere instead of text.",
)

_COVER_STRATEGIES: dict[str, CoverStrategy] = {
    "announcement": CoverStrategy(
        role="A notice cover for readers who need to notice a concrete change or start date.",
        visual_brief="Show the changed target, affected range, or next action clearly without dramatic promotion.",
        display_copy_shape="Use the change target plus what readers should check before acting.",
        text_variant_note="The copy should read like a useful blog notice cue, not a plain label or slogan.",
        no_text_variant_note="Represent the change through calendar, interface, object, or workflow cues without letters or numbers.",
        preferred_focus_terms=("変更前", "改定前", "確認", "対象範囲", "開始前"),
    ),
    "daily_story": CoverStrategy(
        role="A reflective personal-story cover for a small scene and the feeling it leaves.",
        visual_brief="Show a familiar everyday scene, a small object or moment, and a quiet emotional cue.",
        display_copy_shape="Use a small scene plus one realization; keep it soft and human.",
        text_variant_note="The copy may be warmer than the title, but must stay concrete.",
        no_text_variant_note="Use place, light, gesture, and object detail to carry the story without text.",
    ),
    "explanatory_article": CoverStrategy(
        role="An explanatory cover that signals the question and the axis for understanding it.",
        visual_brief="Make the concept tangible with one readable metaphor or work scene plus relevant details.",
        display_copy_shape="Use a question, condition, or overlooked judgment axis that makes readers want the explanation.",
        text_variant_note="The copy should point to the explanatory axis, not summarize the whole article or become a label.",
        no_text_variant_note="Use visual comparison, process, or layered objects to imply the question without text.",
        preferred_subject_patterns=(r"生成AI", r"AI", r"SaaS"),
        preferred_focus_terms=("運用条件", "判断軸", "見る指標", "導入条件", "権限", "確認体制"),
    ),
    "comparative_review": CoverStrategy(
        role="A comparison cover for readers choosing between options under different conditions.",
        visual_brief="Show multiple option paths, a comparison axis, or side-by-side decision contexts while avoiding a winner-takes-all look.",
        display_copy_shape="Use the decision axis or an overlooked comparison point; avoid ranking language.",
        text_variant_note="The copy is separate from the title and should cue why this comparison is worth opening.",
        no_text_variant_note="Communicate comparison through balanced objects, paths, or workspace zones with no labels.",
        preferred_subject_patterns=(r"AI議事録ツール", r"AI議事録", r"SaaS"),
        preferred_focus_terms=("話者分離", "比較軸", "要約精度", "共有管理"),
    ),
    "case_study": CoverStrategy(
        role="A case-study cover that shows before/after change and a practical learning point.",
        visual_brief="Show a process shift, visible improvement, or work scene before and after the change.",
        display_copy_shape="Use before/after change plus learning or condition.",
        text_variant_note="The copy should not overstate results beyond the article source.",
        no_text_variant_note="Use visual contrast and process cues instead of result numbers or labels.",
    ),
    "branding": CoverStrategy(
        role="A brand or company-introduction cover for readers judging whether the value context fits them.",
        visual_brief="Show reader touchpoint, support context, and operational trust instead of abstract brand ideals.",
        display_copy_shape="Use a reader contact point, support boundary, or small adoption tension.",
        text_variant_note="The copy is not the article title; it should cue the reader's contact point or decision context.",
        no_text_variant_note="Use service scene, workflow, hands, documents, or quiet workplace detail without logos or text.",
        preferred_subject_patterns=(r"小規模SaaS", r"SaaS"),
        preferred_focus_terms=("導入初期", "業務定着", "採用力", "相談前", "相談", "支援範囲"),
    ),
    "company_introduction": CoverStrategy(
        role="A company-introduction cover that makes the current business and service areas recognizable at a glance.",
        visual_brief=(
            "Show the company's present business fields, products or services, operating area, facilities, "
            "or field work from the source; avoid inquiry funnels, consultation scenes, and history-first visuals."
        ),
        display_copy_shape=(
            "Use a short business-area phrase: products/services, handled fields, regional footprint, "
            "facilities, or company characteristics. Do not force a question."
        ),
        text_variant_note="The copy should identify what business the company handles, not invite consultation or inquiries.",
        no_text_variant_note=(
            "Use present-day business, field, equipment, service, region, or facility cues without logos, text, "
            "founder/history symbolism, or generic corporate imagery."
        ),
        preferred_subject_patterns=(
            r"LNG",
            r"LPガス",
            r"ガス",
            r"電気",
            r"住まい",
            r"山陰酸素",
            r"データ化",
            r"デジタル化",
            r"データ入力",
            r"スキャニング",
        ),
        preferred_focus_terms=(
            "事業内容",
            "製品",
            "サービス",
            "対応領域",
            "エネルギー",
            "LNG",
            "LPガス",
            "ガス",
            "電気",
            "住まい",
            "地域",
            "拠点",
            "設備",
            "住宅リフォーム",
            "創エネ",
            "省エネ",
            "データ化",
            "デジタル化",
            "データ入力",
            "スキャニング",
            "RPA",
            "Webリサーチ",
        ),
    ),
}

_WEAK_DISPLAY_TEXT_RE = re.compile(
    r"(?:要点|変化|価値|導線|ポイント|これから|進め方|整える|迷わない|選び方|始め方|見方)"
)
_LABEL_LIKE_DISPLAY_TEXT_RE = re.compile(
    r"^(?:.+の)?(?:導入初期|運用条件|話者分離|進め方|選び方|見方|比較軸|要点)$"
)
_REPEATED_DISPLAY_SEGMENT_RE = re.compile(r"^(.{2,12})(?:の|・|、)\1(?:？)?$")
_OVERCLAIM_DISPLAY_TEXT_RE = re.compile(
    r"(?:絶対|必ず|確実|売上が伸びる|成果が出る|失敗しない|成功する|劇的|最強|完全)"
)
_GENERIC_HOOK_DISPLAY_TEXT_RE = re.compile(
    r"^(?:どこから相談できる|どこから相談する|どこまで頼める|どう整える|何を見ればいい|"
    r"何を見る|どこを見る|どこで見る|どこで選ぶ|何を確認する|"
    r"比較前に見る条件|変更前に確認したいこと|開始前に見ること|導入前に見る条件|"
    r"運用前に見る条件|選ぶ前に見る比較軸|失敗しない選び方|導入すべき理由|完全ガイド|"
    r"会社紹介のポイント)[？]?$"
)
_COMPANY_INTRO_CONTACT_DISPLAY_TEXT_RE = re.compile(
    r"(?:相談|問い合わせ|問合せ|どこから|どこまで頼める|どこまで？|導入初期|どこで迷う|"
    r"相談前|相談の入口|相談窓口|支援範囲、どこまで)"
)
_INTERNAL_TERM_DISPLAY_TEXT_RE = re.compile(
    r"(?:SEMANTICLEDGER|SECTIONSHADOW|PATCHSCOPE|article_type|display_text|"
    r"fallback|currentmainline|qualityguard|outputguard|promptbuilder)",
    flags=re.I,
)
_UNNATURAL_ENTITY_SUFFIX_RE = re.compile(
    r"(?:減らす|増やす|選ぶ|整える|決める|考える|始める|進める|見る|支える)[A-Za-z0-9][A-Za-z0-9.+_-]*$"
)
_BASE_CORE_SUBJECT_PATTERNS = (
    r"小規模SaaS",
    r"AI議事録ツール",
    r"AI議事録",
    r"生成AI",
)
_BASE_FOCUS_KEYWORDS = (
    "導入初期",
    "運用条件",
    "話者分離",
    "比較軸",
    "要約精度",
    "共有管理",
    "採用力",
    "業務定着",
    "相談",
    "支援範囲",
    "データ化",
    "変更前",
    "改定前",
    "事業内容",
    "製品",
    "サービス",
    "対応領域",
    "エネルギー",
    "LNG",
    "LPガス",
    "ガス",
    "電気",
    "住まい",
    "地域",
    "拠点",
    "設備",
    "住宅リフォーム",
    "創エネ",
    "省エネ",
    "データ化",
    "デジタル化",
    "データ入力",
    "スキャニング",
    "RPA",
    "Webリサーチ",
)
_COMPANY_INTRO_BUSINESS_TERMS = (
    "事業内容",
    "製品",
    "サービス",
    "対応領域",
    "エネルギー",
    "LNG",
    "LPガス",
    "産業用ガス",
    "医療用ガス",
    "ガス",
    "電気",
    "住まい",
    "地域",
    "拠点",
    "設備",
    "住宅リフォーム",
    "創エネ",
    "省エネ",
    "データ化",
    "デジタル化",
    "データ入力",
    "スキャニング",
    "市場調査",
    "Webリサーチ",
    "業務整理",
)


def resolve_cover_strategy(article_type: str, semantic_key: str = "") -> CoverStrategy:
    semantic = str(semantic_key or "").strip().lower()
    if semantic in _COVER_STRATEGIES:
        return _COVER_STRATEGIES[semantic]
    article = str(article_type or "").strip().lower()
    return _COVER_STRATEGIES.get(article, _DEFAULT_COVER_STRATEGY)


def clean_display_text(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.I).strip()
    match = re.search(r'"(?:text|display_text|copy)"\s*:\s*"([^"]+)"', text)
    if match:
        text = match.group(1)
    text = re.sub(r"[「」『』\"'`#*_\\[\]{}()（）]", "", text)
    text = re.sub(r"\s+", "", text)
    text = text.replace("?", "？")
    keep_question = text.endswith("？") and text.count("？") == 1
    text = re.sub(r"[？]", "", text)
    text = text.strip("、。,.!！:：;-ー")
    if keep_question and text and len(text) < 18:
        text = f"{text}？"
    return text[:18]


def _compact_text(value: str, *, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


def _subject_patterns(article_type: str) -> tuple[str, ...]:
    strategy = resolve_cover_strategy(article_type)
    return tuple(dict.fromkeys((*strategy.preferred_subject_patterns, *_BASE_CORE_SUBJECT_PATTERNS)))


def _focus_terms(article_type: str) -> tuple[str, ...]:
    strategy = resolve_cover_strategy(article_type)
    terms = tuple(dict.fromkeys((*strategy.preferred_focus_terms, *_BASE_FOCUS_KEYWORDS)))
    if str(article_type or "").strip().lower() == "company_introduction":
        blocked = {"相談", "支援範囲", "導入初期", "業務定着"}
        return tuple(term for term in terms if term not in blocked)
    return terms


def extract_core_subject(title: str, lead: str = "", *, article_type: str = "") -> str:
    source = re.sub(r"\s+", "", f"{title or ''} {lead or ''}")
    for pattern in _subject_patterns(article_type):
        match = re.search(pattern, source, flags=re.I)
        if match:
            return clean_display_text(match.group(0))
    match = re.search(r"[A-Za-z0-9][A-Za-z0-9.+_-]{2,14}", source)
    return clean_display_text(match.group(0)) if match else ""


def extract_focus_terms(title: str, lead: str = "", *, article_type: str = "") -> list[str]:
    source = re.sub(r"\s+", "", f"{title or ''} {lead or ''}")
    terms: list[str] = []
    for keyword in _focus_terms(article_type):
        if keyword in source and keyword not in terms:
            terms.append(keyword)
    return terms[:4]


def _source_text(title: str, lead: str = "") -> str:
    return re.sub(r"\s+", "", f"{title or ''} {lead or ''}")


def _has_any(source: str, terms: tuple[str, ...]) -> bool:
    return any(term in source for term in terms)


def _has_repeated_display_segment(text: str) -> bool:
    return bool(_REPEATED_DISPLAY_SEGMENT_RE.match(clean_display_text(text)))


def _short_topic_hook(topic: str, hook: str) -> str:
    candidate = clean_display_text(f"{topic}、{hook}")
    return candidate if 6 <= len(candidate) <= 18 else ""


def _company_contact_hook_display_text(title: str, lead: str = "", *, article_type: str = "") -> str:
    source = _source_text(title, lead)
    core_subject = extract_core_subject(title, lead, article_type=article_type)
    if core_subject and "相談" in source:
        candidate = _short_topic_hook(core_subject, "どこから相談する？")
        if candidate:
            return candidate
    if "データ化" in source and "相談" in source:
        return "データ化、どこから相談する？"
    if _has_any(source, ("入力業務", "入力作業", "データ入力")) and _has_any(source, ("相談", "支援", "頼")):
        return "入力業務、どこまで頼める？"
    if "紙" in source and _has_any(source, ("情報", "申込書", "台帳", "整理", "整える")):
        return "紙の情報、どう整える？"
    if "支援範囲" in source:
        return "支援範囲、どこまで？"
    if "導入初期" in source:
        return "導入初期、どこで迷う？"
    if "業務定着" in source:
        return "業務定着、何を確認する？"
    return ""


def _short_company_name(title: str, lead: str = "") -> str:
    source = _source_text(title, lead)
    match = re.search(r"([一-龥ぁ-んァ-ヴーA-Za-z0-9]{2,18})(?:株式会社|有限会社|合同会社)", source)
    if not match:
        return ""
    name = clean_display_text(match.group(1))
    return name[:10] if len(name) >= 2 else ""


def _company_intro_business_display_text(title: str, lead: str = "") -> str:
    source = _source_text(title, lead)
    if _has_any(source, ("ガス", "LPガス", "LNG")) and "電気" in source and "住まい" in source:
        return "ガス・電気・住まいを支える"
    if "データ化" in source and "デジタル化" in source:
        return "データ化・デジタル化事業"
    if "データ入力" in source and "スキャニング" in source:
        return "データ入力とスキャニング"
    if "データ入力" in source and _has_any(source, ("市場調査", "Webリサーチ", "業務整理")):
        return "データ入力と業務支援"
    if "LNG" in source and _has_any(source, ("地域", "エネルギー", "ガス")):
        return "LNGと地域のエネルギー"
    if "ガス" in source and "電気" in source:
        return "ガスと電気の事業領域"
    if "ガス" in source and "住まい" in source:
        return "ガスと住まいの対応領域"
    if "エネルギー" in source and _has_any(source, ("暮らし", "住まい", "地域")):
        return "エネルギーと暮らしの事業"
    company = _short_company_name(title, lead)
    if company and "事業内容" in source:
        candidate = clean_display_text(f"事業内容から見る{company}")
        if 6 <= len(candidate) <= 18:
            return candidate
    for term in _COMPANY_INTRO_BUSINESS_TERMS:
        if term in source:
            candidate = clean_display_text(f"{term}の対応領域")
            if 6 <= len(candidate) <= 18:
                return candidate
    return ""


def _announcement_hook_display_text(title: str, lead: str = "") -> str:
    source = _source_text(title, lead)
    if "料金" in source and "改定" in source:
        return "料金改定前に見ること"
    if "手順" in source and _has_any(source, ("変更", "切り替え")):
        return "手順変更、何を確認する？"
    if "対象範囲" in source and _has_any(source, ("変更", "改定", "開始", "公開", "提供")):
        return "対象範囲、何を確認する？"
    if "提供" in source and "開始" in source:
        return "提供開始前に見ること"
    return ""


def _article_type_hook_display_text(title: str, lead: str = "", *, article_type: str = "") -> str:
    article = str(article_type or "").strip().lower()
    source = _source_text(title, lead)
    focus_terms = extract_focus_terms(title, lead, article_type=article_type)

    if article == "announcement":
        specific = _announcement_hook_display_text(title, lead)
        if specific:
            return specific
        if any(term in source for term in ("変更", "改定", "切り替え")):
            return "変更内容、何を確認する？"
        if any(term in source for term in ("開始", "公開", "提供")):
            return "開始内容、何を確認する？"

    if article == "comparative_review":
        for focus in ("話者分離", "要約精度", "共有管理"):
            if focus in focus_terms or focus in source:
                return clean_display_text(f"{focus}でどこを見る？")
        if "比較軸" in focus_terms or "比較" in source:
            return "選ぶ前に見る比較軸"

    if article == "branding":
        contact_hook = _company_contact_hook_display_text(title, lead, article_type=article_type)
        if contact_hook:
            return contact_hook
        if "導入初期" in source:
            return "導入初期、どこで迷う？"
        if "支援範囲" in source or "支援" in source:
            return "支援範囲、どこまで？"

    if article == "company_introduction":
        business_copy = _company_intro_business_display_text(title, lead)
        if business_copy:
            return business_copy

    if article == "explanatory_article":
        if "運用条件" in source or "運用" in source:
            return "運用前に見る条件"
        if "導入条件" in source or "導入" in source:
            return "導入前に見る条件"
        if focus_terms:
            candidate = clean_display_text(f"{focus_terms[0]}どこで見る？")
            if 6 <= len(candidate) <= 18:
                return candidate

    return ""


def _compose_core_display_text(title: str, lead: str = "", *, article_type: str = "") -> str:
    core_subject = extract_core_subject(title, lead, article_type=article_type)
    focus_terms = extract_focus_terms(title, lead, article_type=article_type)
    if core_subject and focus_terms:
        for focus in focus_terms:
            if focus == core_subject or focus in core_subject or core_subject in focus:
                continue
            candidate = clean_display_text(f"{core_subject}の{focus}")
            if 6 <= len(candidate) <= 18:
                return candidate
    if core_subject and 6 <= len(core_subject) <= 18:
        return core_subject
    return ""


def _title_based_display_text(title: str, lead: str = "", *, article_type: str = "") -> str:
    text = re.sub(r"\s+", "", str(title or "")).strip()
    text = re.sub(r"^#+", "", text)
    text = re.split(r"(?:――|--|：|:|。|、|？|\?)", text, maxsplit=1)[0]
    text = re.sub(r"(?:には|は)?何(?:が|を|で).*$", "", text)
    text = re.sub(r"(?:には|は)?どう.*$", "", text)
    text = re.sub(r"(?:とは|って何).*$", "", text)
    if len(text) > 18:
        for separator in ("で", "から", "まで"):
            head = text.split(separator, 1)[0]
            if 6 <= len(head) <= 18:
                text = head
                break
    if len(text) > 18:
        combined = _compose_core_display_text(title, lead, article_type=article_type)
        if combined:
            return combined
    return clean_display_text(text)


def _strong_article_anchor_terms(title: str, lead: str = "") -> list[str]:
    source = _source_text(title, lead)
    terms: list[str] = []
    for pattern in (
        r"[A-Za-z0-9][A-Za-z0-9.+_-]{1,12}",
        r"[一-龥ぁ-んァ-ヴーA-Za-z0-9]{2,18}(?:初期|条件|分離|精度|管理|比較軸|議事録|採用力|運用|業務|相談|支援範囲|データ化)",
        r"(?:生成AI|AI議事録|小規模SaaS)",
    ):
        for match in re.finditer(pattern, source):
            term = clean_display_text(match.group(0))
            if len(term) >= 3 and term not in terms and not _WEAK_DISPLAY_TEXT_RE.fullmatch(term):
                terms.append(term)
    for term in _COMPANY_INTRO_BUSINESS_TERMS:
        if term in source and term not in terms:
            terms.append(term)
    return terms[:8]


def _is_company_intro_specific_display_text(text: str, title: str, lead: str = "") -> bool:
    if _COMPANY_INTRO_CONTACT_DISPLAY_TEXT_RE.search(text):
        return False
    if _GENERIC_HOOK_DISPLAY_TEXT_RE.match(text):
        return False
    source = _source_text(title, lead)
    if not source:
        return False
    company = _short_company_name(title, lead)
    if company and company in text:
        return True
    supported_terms = [term for term in _COMPANY_INTRO_BUSINESS_TERMS if term in text and term in source]
    if len(supported_terms) >= 1 and not _WEAK_DISPLAY_TEXT_RE.search(text):
        return True
    return len(supported_terms) >= 2


def _has_supported_hook_axis(text: str, title: str, lead: str = "", *, article_type: str = "") -> bool:
    source = _source_text(title, lead)
    if not source:
        return False
    candidate_terms = (
        *extract_focus_terms(title, lead, article_type=article_type),
        *_strong_article_anchor_terms(title, lead),
        "相談",
        "導入",
        "運用",
        "比較",
        "分離",
        "条件",
        "範囲",
        "支援",
        "確認",
        "変更",
        "改定",
        "データ化",
    )
    for term in dict.fromkeys(term for term in candidate_terms if len(term) >= 2):
        if term in text and term in source:
            return True
    return False


def _is_hook_shaped_display_text(text: str) -> bool:
    return bool(re.search(r"(?:？|どこ|なぜ|何|前に|つまずく|迷う|比べる|選ぶ|相談|確認|見る)", text))


def is_article_specific_display_text(candidate: str, title: str, lead: str = "", *, article_type: str = "") -> bool:
    text = clean_display_text(candidate)
    if not text:
        return False
    if _GENERIC_HOOK_DISPLAY_TEXT_RE.match(text):
        return False
    if _INTERNAL_TERM_DISPLAY_TEXT_RE.search(text):
        return False
    if _OVERCLAIM_DISPLAY_TEXT_RE.search(text):
        return False
    if _has_repeated_display_segment(text):
        return False
    if _UNNATURAL_ENTITY_SUFFIX_RE.search(text):
        return False
    if _LABEL_LIKE_DISPLAY_TEXT_RE.match(text):
        return False
    if str(article_type or "").strip().lower() == "company_introduction":
        return _is_company_intro_specific_display_text(text, title, lead)
    core_subject = extract_core_subject(title, lead, article_type=article_type)
    has_hook_axis = _is_hook_shaped_display_text(text) and _has_supported_hook_axis(
        text,
        title,
        lead,
        article_type=article_type,
    )
    if core_subject and core_subject not in text and not has_hook_axis:
        return False
    anchors = _strong_article_anchor_terms(title, lead)
    if not anchors:
        return not _WEAK_DISPLAY_TEXT_RE.search(text) or has_hook_axis
    if any(anchor in text or text in anchor for anchor in anchors):
        return not _LABEL_LIKE_DISPLAY_TEXT_RE.match(text) or has_hook_axis
    if has_hook_axis:
        return True
    return not _WEAK_DISPLAY_TEXT_RE.search(text)


def fallback_display_text(title: str, lead: str = "", *, article_type: str = "") -> str:
    hook_copy = _article_type_hook_display_text(title, lead, article_type=article_type)
    if hook_copy:
        return hook_copy[:18]
    core_copy = _compose_core_display_text(title, lead, article_type=article_type)
    if core_copy:
        return core_copy[:18]
    anchored = _title_based_display_text(title, lead, article_type=article_type)
    if anchored:
        return anchored[:18]
    cleaned = clean_display_text(title)
    if cleaned:
        return cleaned[:18]
    for anchor in _strong_article_anchor_terms(title, lead):
        if anchor:
            return anchor[:18]
    return "記事の要点"


def build_display_copy_prompt(
    *,
    title: str,
    lead: str,
    body: str,
    article_type: str = "",
) -> tuple[str, str]:
    strategy = resolve_cover_strategy(article_type)
    fallback = fallback_display_text(title, lead, article_type=article_type)
    core_subject = extract_core_subject(title, lead, article_type=article_type) or "未抽出"
    focus_terms = extract_focus_terms(title, lead, article_type=article_type)
    focus_text = " / ".join(focus_terms) if focus_terms else "未抽出"
    if str(article_type or "").strip().lower() == "company_introduction":
        copy_direction = "\n".join(
            [
                "- 会社紹介では、問い・相談導線・判断軸ではなく、事業領域、サービス、設備、地域、現在の仕事を短く示す",
                "- 「相談」「問い合わせ」「判断軸」「見方」のような検討フックに寄せない",
                "- 沿革の年号だけを主役にせず、現在扱っている業務やサービスが伝わる語を優先する",
            ]
        )
    else:
        copy_direction = "\n".join(
            [
                "- 問い、違和感、判断軸を使ってよい",
                "- 形は「具体テーマ + 読者の問い」または「読者の状況 + 判断軸」に寄せる",
                "- 主題エンティティまたは記事固有の判断軸を残す",
            ]
        )
    prompt = f"""
記事内容から、ブログの見出し画像に1回だけ入れる短い日本語コピーを作ってください。

条件:
- 6〜18文字
- 日本語として自然
- 記事タイトルとは別のカバー用コピーにする
- 記事タイトルや本文の主題に合う
- 説明ラベルではなく、読者が開く理由になる短いカバーコピーにする
{copy_direction}
- 「どこから相談できる？」「何を見ればいい？」のような具体テーマのない一般質問にしない
- 読者を釣る煽りや、本文にない成果・効果を入れない
- 抽象的なスローガンだけにしない
- 記号は自然な疑問符1つまで。引用符、改行、説明文を入れない
- 出力はコピー本文のみ

カバー方針:
- 役割: {strategy.role}
- コピー型: {strategy.display_copy_shape}
- 文字入り画像での扱い: {strategy.text_variant_note}

構造化メモ:
- 主題エンティティ（必ず含める）: {core_subject}
- 主要焦点（必要なら組み合わせる）: {focus_text}
- 推奨コピー候補: {fallback}

記事タイプ: {article_type or "未指定"}
タイトル: {_compact_text(title, max_chars=120) or "未指定"}
リード: {_compact_text(lead, max_chars=220) or "未指定"}
本文要約: {_compact_text(body, max_chars=800) or "未指定"}
""".strip()
    return prompt, fallback


def build_cover_visual_brief_lines(*, article_type: str, variant_key: str) -> list[str]:
    strategy = resolve_cover_strategy(article_type)
    variant_note = strategy.text_variant_note if variant_key == "with_text" else strategy.no_text_variant_note
    return [
        f"Cover role: {strategy.role}",
        f"Article-type visual brief: {strategy.visual_brief}",
        f"Display-copy guidance: {strategy.display_copy_shape}",
        f"Variant-specific guidance: {variant_note}",
    ]
