"""Rule-based smoke evaluator for writer-only output."""
from __future__ import annotations

import re
from typing import Any, Dict


SELF_PERSPECTIVE_TERMS = ("私たち", "当社", "私", "自分")
THIRD_PERSON_PATTERNS = (
    r"(?:この記事|本記事|当記事)では[^。！？\n]{0,120}(?:ご)?(?:紹介|解説|説明)します",
    r"筆者(?:が|は)[^。！？\n]{0,120}(?:ご)?(?:紹介|解説|説明)します",
    r"まとめサイト(?:風|のよう)?",
    r"第三者紹介文",
    r"〜について(?:ご)?紹介",
)
CONSULTATION_VOICE_TERMS = ("相談", "ご相談", "現場", "お客様", "所有者", "伺", "見て", "感じ", "知る", "背景", "共感", "整理", "一緒")
READER_RELEVANCE_TERMS = (
    "迷",
    "相談",
    "相談前",
    "整理",
    "判断",
    "知る",
    "背景",
    "関心",
    "手がかり",
    "売るか",
    "売却",
    "貸すか",
    "賃貸",
    "活用するか",
    "活用相談",
    "先送り",
    "困",
    "断ら",
)
GENERIC_READER_RELEVANCE_TERMS = (
    "課題",
    "お悩み",
    "悩み",
    "不安",
    "困",
    "迷",
    "検討",
    "知りたい",
    "分から",
    "わから",
    "目的",
    "必要",
    "理由",
    "背景",
    "選ば",
    "導入",
    "利用",
    "読者",
    "顧客",
    "企業",
    "企業様",
    "お客様",
    "応募",
    "候補者",
    "現場",
    "業務",
    "品質",
    "安全",
    "信頼",
    "支援",
    "サポート",
    "ヒアリング",
    "お問い合わせ",
    "DX",
    "デジタル",
    "データ",
    "データ化",
    "手書き",
    "紙",
    "効率化",
    "セキュリティ",
)
UNSUPPORTED_GENERALIZATION_TERMS = (
    "人口減少",
    "再開発",
    "利便性",
    "市場動向",
    "地域特性",
    "周辺環境の変化",
    "長期的に収益",
    "将来の家族",
)
STRONG_ASSERTION_TERMS = ("重要です", "必要です", "変わってきます", "左右されます", "低迷しやすい", "広がります")
EDITORIAL_BRIDGE_MARKERS = (
    "ような場面",
    "考えるきっかけ",
    "整理しやすい観点",
    "相談前に整理",
    "見直したくなる",
)
ABSOLUTE_FACT_TERMS = ("必ず", "確実に", "すべて", "誰でも", "例外なく", "断言できます")
PROHIBITED_CLAIM_PATTERNS = {
    "unsupported_price": ("価格", "料金", "費用", "円", "万円", "無料"),
    "unsupported_outcome": ("売上", "成約", "集客", "導入効果", "改善効果", "成果"),
    "unsupported_legal_advice": ("法的", "違法", "契約", "訴訟", "弁護士", "相続", "税制"),
    "unsupported_medical_advice": ("医療", "治療", "薬", "診断", "症状", "医師"),
    "unsupported_financial_advice": ("投資", "融資", "保険", "税務", "利回り", "資産運用"),
    "unsupported_local_market_trend": ("市場動向", "地域特性", "賃貸需要", "売却価格", "人口減少", "再開発"),
    "unsupported_customer_case": ("顧客事例", "導入事例", "お客様の声", "成功事例", "実績事例"),
    "unsupported_superiority_claim": ("業界No.1", "日本一", "最高品質", "唯一", "他社より", "トップクラス", "圧倒的"),
    "unsupported_public_procedure": ("行政代執行", "許認可", "補助金", "申請手続き", "行政手続き"),
}
NUMBER_WITH_UNIT_PATTERN = re.compile(r"\d[\d,]*(?:\.\d+)?\s*(?:%|％|円|万円|億円|年|年以上|件|社|倍|割|人|名|店舗|拠点)")
VISIBLE_MEDIA_NAME_PATTERNS = (
    r"企業note",
    r"(?<![A-Za-z0-9_])note(?![A-Za-z0-9_])",
    r"はてなブログ",
    r"Hatena\s*Blog",
)
ARTICLE_BODY_MIN_CHARS = 300
ARTICLE_BODY_MAX_CHARS = 2000


def evaluate_writer_only_smoke(article_markdown: str, brief: Dict[str, Any], route_flags: Dict[str, Any]) -> Dict[str, Any]:
    text = str(article_markdown or "")
    lines = [line.strip() for line in text.splitlines()]
    persona = brief.get("persona") if isinstance(brief.get("persona"), dict) else {}
    sections = _split_h2_sections(text)
    source_claim_text = _source_claim_text(brief)
    evidence_text = _evidence_text(brief)
    section_relevance_terms = _section_relevance_terms(brief, persona, source_claim_text)
    article_min_chars, article_max_chars = _article_body_limits(brief)
    source_url_coverage = _source_url_coverage(text, brief)
    prohibited_claims = _prohibited_claims(text, evidence_text)
    bridge_warnings = _editorial_bridge_warnings(text)
    japanese_warnings = _japanese_style_warnings(text)
    checks = {
        "markdown_title": bool(lines and lines[0].startswith("# ")),
        "markdown_sections": sum(1 for line in lines if line.startswith("## ")) >= 2,
        "article_body_length": article_min_chars <= len(text.strip()) <= article_max_chars,
        "self_perspective": any(term in text for term in SELF_PERSPECTIVE_TERMS),
        "no_third_person_article_voice": not _has_third_person_article_voice(text),
        "audience_anchor": _has_audience_anchor(text, persona),
        "voice_consistency": _has_consultation_voice(text),
        "section_reader_relevance": bool(sections) and all(
            _section_starts_from_reader_relevance(section, section_relevance_terms) for section in sections
        ),
        "source_grounding": not _unsupported_generalizations(text, source_claim_text),
        "prohibited_claim_guard": not prohibited_claims,
        "visible_media_name_absent": not _has_visible_media_name(text),
        "url_count_within_limit": len(brief.get("urls") or []) <= 6,
        "source_url_coverage": source_url_coverage["passed"],
        "persona_enabled": all(
            str(persona.get(key) or "").strip()
            for key in ("target_reader", "reader_problem", "article_goal", "company_speaker")
        ),
        "writer_contract_first_person": bool(
            (brief.get("writer_contract") or {}).get("must_use_first_person")
        ),
        "route_0506_not_used": route_flags.get("route_0506_used") is False,
        "route_a_not_used": route_flags.get("route_a_used") is False,
        "repair_not_used": route_flags.get("repair_used") is False,
    }
    failed = [key for key, value in checks.items() if not value]
    return {
        "passed": not failed,
        "checks": checks,
        "failed": failed,
        "details": {
            "article_char_count": len(text.strip()),
            "article_min_chars": article_min_chars,
            "article_max_chars": article_max_chars,
            "source_count": _source_count(brief),
            "source_char_total": _source_char_total(brief),
            "claims_count": _claims_count(brief),
            "required_source_url_count": source_url_coverage["required"],
            "mentioned_source_urls": source_url_coverage["mentioned"],
            "missing_source_urls": source_url_coverage["missing"],
            "unsupported_generalizations": _unsupported_generalizations(text, source_claim_text),
            "prohibited_claim_hits": prohibited_claims,
            "editorial_bridge_warnings": bridge_warnings,
            "japanese_style_warnings": japanese_warnings,
        },
    }


def _has_audience_anchor(text: str, persona: Dict[str, Any]) -> bool:
    opening = text[:500]
    target = str(persona.get("target_reader") or "")
    problem = str(persona.get("reader_problem") or "")
    target_hits = _keyword_hits(opening, target)
    problem_hits = _keyword_hits(opening, problem)
    generic_reader_hits = _term_hits(opening, GENERIC_READER_RELEVANCE_TERMS)
    return (target_hits >= 2 and problem_hits >= 2) or (
        target_hits >= 1 and problem_hits >= 2 and generic_reader_hits >= 2
    ) or (
        problem_hits >= 2 and generic_reader_hits >= 3
    )


def _has_consultation_voice(text: str) -> bool:
    for match in re.finditer(r"私たち|当社|私|自分", text):
        window = text[max(0, match.start() - 80) : match.end() + 120]
        if any(term in window for term in CONSULTATION_VOICE_TERMS):
            return True
    return False


def _has_third_person_article_voice(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in THIRD_PERSON_PATTERNS)


def _section_starts_from_reader_relevance(section: str, dynamic_terms: tuple[str, ...]) -> bool:
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    if not lines:
        return False
    lead = "\n".join(lines[:3])[:260]
    return (
        _term_hits(lead, READER_RELEVANCE_TERMS) >= 1
        or _term_hits(lead, GENERIC_READER_RELEVANCE_TERMS) >= 2
        or (
            _term_hits(lead, dynamic_terms) >= 2
            and _term_hits(lead, GENERIC_READER_RELEVANCE_TERMS) >= 1
        )
    )


def _unsupported_generalizations(text: str, source_claim_text: str) -> list[str]:
    findings: list[str] = []
    for sentence in re.split(r"(?<=[。！？])", text):
        if not any(term in sentence for term in STRONG_ASSERTION_TERMS):
            continue
        for term in UNSUPPORTED_GENERALIZATION_TERMS:
            if term in sentence and term not in source_claim_text:
                findings.append(term)
    return sorted(set(findings))


def _prohibited_claims(text: str, evidence_text: str) -> list[Dict[str, str]]:
    findings: list[Dict[str, str]] = []
    evidence = str(evidence_text or "")
    document_context = "\n".join([evidence, str(text or "")[:800]])
    for sentence in _sentences(text):
        sentence_findings: list[tuple[str, str]] = []
        for number in NUMBER_WITH_UNIT_PATTERN.findall(sentence):
            if number and number not in evidence:
                sentence_findings.append(("unsupported_number", number))
        for claim_class, patterns in PROHIBITED_CLAIM_PATTERNS.items():
            for pattern in patterns:
                if pattern not in sentence:
                    continue
                if _is_guarded_prohibited_claim_mention(sentence, claim_class, pattern, document_context):
                    continue
                if pattern in evidence and not _uses_absolute_unsupported_language(sentence):
                    continue
                sentence_findings.append((claim_class, pattern))
        for claim_class, marker in sentence_findings:
            findings.append(
                {
                    "class": claim_class,
                    "marker": marker,
                    "sentence": sentence.strip(),
                }
            )
    unique: dict[tuple[str, str, str], Dict[str, str]] = {}
    for finding in findings:
        key = (finding["class"], finding["marker"], finding["sentence"])
        unique[key] = finding
    return list(unique.values())


def _is_guarded_prohibited_claim_mention(
    sentence: str,
    claim_class: str,
    pattern: str,
    document_context: str,
) -> bool:
    """Allow explicit avoidance notes without weakening positive unsupported claims."""
    if claim_class == "unsupported_medical_advice" and pattern == "症状":
        housing_terms = ("住まい", "住宅", "店舗", "不具合", "修繕", "補修", "水まわり", "建具", "内装", "箇所")
        medical_terms = ("医療", "治療", "薬", "診断", "医師", "病院", "患者")
        context = "\n".join([sentence, document_context])
        if any(term in context for term in housing_terms) and not any(term in context for term in medical_terms):
            return True
    guarded_markers = (
        "断定しない",
        "決め打ちせず",
        "飛ばず",
        "保証するものではありません",
        "禁止",
        "書かない",
        "扱わない",
    )
    if claim_class in {
        "unsupported_price",
        "unsupported_local_market_trend",
        "unsupported_public_procedure",
        "unsupported_legal_advice",
        "unsupported_medical_advice",
        "unsupported_financial_advice",
    } and any(marker in sentence for marker in guarded_markers):
        return True
    return False


def _uses_absolute_unsupported_language(sentence: str) -> bool:
    return any(term in sentence for term in ABSOLUTE_FACT_TERMS)


def _editorial_bridge_warnings(text: str) -> list[Dict[str, str]]:
    warnings: list[Dict[str, str]] = []
    for sentence in _sentences(text):
        if not any(marker in sentence for marker in EDITORIAL_BRIDGE_MARKERS):
            continue
        absolute = [term for term in ABSOLUTE_FACT_TERMS if term in sentence]
        if absolute:
            warnings.append(
                {
                    "type": "editorial_bridge_absolute_language",
                    "markers": ", ".join(absolute),
                    "sentence": sentence.strip(),
                }
            )
    return warnings


def _japanese_style_warnings(text: str) -> list[Dict[str, str]]:
    warnings: list[Dict[str, str]] = []
    endings = _sentence_endings(text)
    repeated = _longest_run(endings)
    if repeated[1] >= 4:
        warnings.append({"type": "repeated_sentence_endings", "marker": repeated[0], "count": str(repeated[1])})
    paragraphs = [len(paragraph.strip()) for paragraph in re.split(r"\n\s*\n", text) if len(paragraph.strip()) >= 30]
    if len(paragraphs) >= 4 and max(paragraphs) - min(paragraphs) <= 20:
        warnings.append({"type": "uniform_paragraph_length", "count": str(len(paragraphs))})
    abstract_hits = [term for term in ("価値", "重要性", "可能性", "課題", "目的", "背景") if text.count(term) >= 4]
    if abstract_hits:
        warnings.append({"type": "abstract_noun_run", "markers": ", ".join(abstract_hits)})
    comma_sentences = [
        sentence.strip()
        for sentence in _sentences(text)
        if len(sentence) >= 80 and sentence.count("、") >= 5
    ]
    if comma_sentences:
        warnings.append({"type": "comma_density_warning", "count": str(len(comma_sentences))})
    h2_openings = [_normalize_h2_opening(section) for section in _split_h2_sections(text)]
    if len(h2_openings) >= 3 and len(set(h2_openings)) == 1:
        warnings.append({"type": "h2_opening_pattern_repetition", "marker": h2_openings[0]})
    return warnings


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[。！？])|\n+", str(text or "")) if sentence.strip()]


def _evidence_text(brief: Dict[str, Any]) -> str:
    parts = [_source_claim_text(brief)]
    bundle = brief.get("source_bundle") if isinstance(brief.get("source_bundle"), dict) else {}
    for source in bundle.get("sources") or []:
        if not isinstance(source, dict):
            continue
        parts.extend(
            str(source.get(key) or "")
            for key in ("title", "excerpt", "normalized_url", "url")
        )
    for item in brief.get("verified_external_context") or []:
        if not isinstance(item, dict):
            continue
        parts.extend(
            str(item.get(key) or "")
            for key in ("short_fact", "source_url", "retrieved_at")
        )
    return "\n".join(parts)


def _sentence_endings(text: str) -> list[str]:
    endings: list[str] = []
    for sentence in _sentences(text):
        match = re.search(r"([ぁ-んァ-ン一-龥A-Za-z0-9]+(?:です|ます|ました|ません|でしょう|だ|である|します|しています|しています。)?)。?$", sentence)
        if match:
            endings.append(match.group(1)[-6:])
    return endings


def _longest_run(values: list[str]) -> tuple[str, int]:
    best_value = ""
    best_count = 0
    current_value = ""
    current_count = 0
    for value in values:
        if value == current_value:
            current_count += 1
        else:
            current_value = value
            current_count = 1
        if current_count > best_count:
            best_value = current_value
            best_count = current_count
    return best_value, best_count


def _normalize_h2_opening(section: str) -> str:
    first_line = section.splitlines()[0] if section.splitlines() else ""
    if "相談前" in first_line:
        return "相談前"
    if "迷" in first_line:
        return "迷い"
    return first_line[:6]


def _has_visible_media_name(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in VISIBLE_MEDIA_NAME_PATTERNS)


def _source_claim_text(brief: Dict[str, Any]) -> str:
    bundle = brief.get("source_bundle") if isinstance(brief.get("source_bundle"), dict) else {}
    claims: list[str] = []
    for source in bundle.get("sources") or []:
        if not isinstance(source, dict):
            continue
        claims.extend(str(claim) for claim in source.get("claims") or [])
    return "\n".join(claims)


def _article_body_limits(brief: Dict[str, Any]) -> tuple[int, int]:
    contract = brief.get("article_body_contract") if isinstance(brief.get("article_body_contract"), dict) else {}
    try:
        min_chars = int(contract.get("min_chars") or 0)
    except (TypeError, ValueError):
        min_chars = 0
    try:
        max_chars = int(contract.get("max_chars") or 0)
    except (TypeError, ValueError):
        max_chars = 0
    if min_chars <= 0:
        min_chars = _dynamic_min_chars_from_brief(brief)
    if max_chars <= 0:
        max_chars = ARTICLE_BODY_MAX_CHARS
    return min_chars, max_chars


def _dynamic_min_chars_from_brief(brief: Dict[str, Any]) -> int:
    source_count = _source_count(brief)
    source_char_total = _source_char_total(brief)
    claims_count = _claims_count(brief)
    if source_count >= 3 or source_char_total >= 3000 or claims_count >= 12:
        return 1300
    if source_count >= 2 or source_char_total >= 1800 or claims_count >= 8:
        return 900
    return ARTICLE_BODY_MIN_CHARS


def _source_url_coverage(text: str, brief: Dict[str, Any]) -> Dict[str, Any]:
    source_urls = _source_urls(brief)
    required = _required_source_url_count(brief, len(source_urls))
    mentioned = [url for url in source_urls if _normalize_url_for_match(url) in _mentioned_url_set(text)]
    missing = [url for url in source_urls if url not in mentioned]
    return {
        "passed": len(mentioned) >= required,
        "required": required,
        "mentioned": mentioned,
        "missing": missing,
    }


def _required_source_url_count(brief: Dict[str, Any], source_count: int) -> int:
    contract = brief.get("source_reference_contract") if isinstance(brief.get("source_reference_contract"), dict) else {}
    try:
        required = int(contract.get("min_url_mentions") or -1)
    except (TypeError, ValueError):
        required = -1
    if required >= 0:
        return min(required, source_count)
    if source_count >= 4:
        return 3
    if source_count >= 2:
        return 2
    return 0


def _source_urls(brief: Dict[str, Any]) -> list[str]:
    contract = brief.get("source_reference_contract") if isinstance(brief.get("source_reference_contract"), dict) else {}
    urls = [str(url or "").strip() for url in contract.get("source_urls") or [] if str(url or "").strip()]
    if not urls:
        bundle = brief.get("source_bundle") if isinstance(brief.get("source_bundle"), dict) else {}
        for source in bundle.get("sources") or []:
            if not isinstance(source, dict):
                continue
            url = str(source.get("normalized_url") or source.get("url") or "").strip()
            if url:
                urls.append(url)
    if not urls:
        urls = [str(url or "").strip() for url in brief.get("urls") or [] if str(url or "").strip()]
    return list(dict.fromkeys(urls))


def _mentioned_url_set(text: str) -> set[str]:
    return {
        _normalize_url_for_match(match)
        for match in re.findall(r"https?://[^\s\]\)）>、。]+", str(text or ""))
    }


def _normalize_url_for_match(url: str) -> str:
    return str(url or "").strip().rstrip(".,;:!?、。）」』】>").rstrip("/")


def _source_count(brief: Dict[str, Any]) -> int:
    bundle = brief.get("source_bundle") if isinstance(brief.get("source_bundle"), dict) else {}
    sources = [source for source in bundle.get("sources") or [] if isinstance(source, dict)]
    if sources:
        return len(sources)
    try:
        return int(bundle.get("source_count") or len(brief.get("urls") or []))
    except (TypeError, ValueError):
        return len(brief.get("urls") or [])


def _source_char_total(brief: Dict[str, Any]) -> int:
    bundle = brief.get("source_bundle") if isinstance(brief.get("source_bundle"), dict) else {}
    total = 0
    for source in bundle.get("sources") or []:
        if not isinstance(source, dict):
            continue
        try:
            total += int(source.get("char_count") or 0)
        except (TypeError, ValueError):
            pass
    return total


def _claims_count(brief: Dict[str, Any]) -> int:
    bundle = brief.get("source_bundle") if isinstance(brief.get("source_bundle"), dict) else {}
    total = 0
    for source in bundle.get("sources") or []:
        if not isinstance(source, dict):
            continue
        claims = source.get("claims") if isinstance(source.get("claims"), list) else []
        total += len(claims)
    return total


def _section_relevance_terms(brief: Dict[str, Any], persona: Dict[str, Any], source_claim_text: str) -> tuple[str, ...]:
    source_text = "\n".join(
        str(value or "")
        for value in (
            persona.get("target_reader"),
            persona.get("reader_problem"),
            persona.get("article_goal"),
            brief.get("instruction"),
            brief.get("category_direction"),
            source_claim_text,
        )
    )
    terms = [term for term in _content_terms(source_text) if len(term) >= 2]
    return tuple(dict.fromkeys(terms))


def _split_h2_sections(text: str) -> list[str]:
    parts = re.split(r"(?m)^##\s+", text)
    return [part.strip() for part in parts[1:] if part.strip()]


def _keyword_hits(text: str, source: str) -> int:
    keywords = [term for term in _content_terms(source) if term in text]
    return len(set(keywords))


def _term_hits(text: str, terms: tuple[str, ...]) -> int:
    return len({term for term in terms if term in text})


def _content_terms(text: str) -> list[str]:
    probe_terms = (
        "空き家",
        "貸家",
        "売る",
        "売却",
        "貸す",
        "賃貸",
        "活用",
        "迷",
        "所有",
        "相談",
        "整理",
        "判断",
        "知る",
        "背景",
        "関心",
        "手がかり",
        "先送り",
        "課題",
    )
    raw_terms = [term for term in probe_terms if term in text]
    raw_terms.extend(
        term
        for term in re.split(r"[、。・\s/]|や|を|に|が|で|と|か|の|は|へ", text)
        if len(term) >= 2
    )
    stop_terms = {
        "こと",
        "ため",
        "よう",
        "ある",
        "する",
        "いる",
        "分からず",
        "分からない",
        "しがち",
        "相談前",
    }
    return [term for term in raw_terms if term not in stop_terms]
