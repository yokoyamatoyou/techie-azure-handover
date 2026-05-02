# -*- coding: utf-8 -*-
"""FAQ detection helpers."""

import re
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup


FAQ_CONTEXT_PATTERN = re.compile(
    r"(?:\bfaq\b|q\s*[&＆]\s*a|よくある質問|よくある問合せ|よくある問い合わせ|質問集)",
    re.IGNORECASE,
)

QUESTION_HINT_PATTERN = re.compile(
    r"(?:\?|？|ですか|ますか|でしょうか|できますか|可能ですか|ありますか|必要ですか|とは|なぜ|どう|いつ|どこ|いくら|何)",
    re.IGNORECASE,
)

NON_FAQ_CONTEXT_PATTERN = re.compile(
    r"(?:お知らせ|ニュース|新着|プレスリリース|トップメッセージ|代表[挨拶談]|ミッション|ビジョン|会社概要|沿革|採用|ir|投資家情報|csr)",
    re.IGNORECASE,
)


def _normalize_faq_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\s+", "", text).lower()
    cleaned = re.sub(r"[「」『』（）()\[\]【】〈〉\"'、。,\.・:：;；!?！？\-‐―ー]", "", cleaned)
    return cleaned


def _build_faq_key(question: str) -> str:
    return _normalize_faq_text(question)[:120]


def _dedupe_faq_items(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    deduped = []
    for item in items:
        key = _build_faq_key(item.get("question", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _contains_faq_keyword(text: str) -> bool:
    return bool(text and FAQ_CONTEXT_PATTERN.search(text))


def _looks_like_question(text: str) -> bool:
    if not text:
        return False
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) < 4 or len(cleaned) > 120:
        return False
    return bool(QUESTION_HINT_PATTERN.search(cleaned))


def _looks_non_faq_context(text: str) -> bool:
    return bool(text and NON_FAQ_CONTEXT_PATTERN.search(text))


def _tag_text_for_context(tag) -> str:
    if not tag:
        return ""
    tag_name = str(getattr(tag, "name", "") or "").lower()
    class_text = " ".join(tag.get("class", [])) if hasattr(tag, "get") and isinstance(tag.get("class"), list) else ""
    id_text = str(tag.get("id", "")) if hasattr(tag, "get") else ""
    aria_label = str(tag.get("aria-label", "")) if hasattr(tag, "get") else ""

    # get_text() は親要素でページ全体文字列を含みやすいため、
    # 見出し要素に限定して文脈判定に使う。
    heading_text = ""
    if tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"} and hasattr(tag, "get_text"):
        heading_text = tag.get_text(" ", strip=True)

    parts = [heading_text, class_text, id_text, aria_label]
    return " ".join([p for p in parts if p]).strip()


def _is_in_faq_context(tag) -> bool:
    """Return True when a tag is located in a FAQ-like section."""
    if not tag:
        return False

    # Own / ancestor class, id, text
    current = tag
    for _ in range(4):
        if not current:
            break
        if _contains_faq_keyword(_tag_text_for_context(current)):
            return True
        current = getattr(current, "parent", None)

    # Closest previous heading
    prev_heading = tag.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
    if prev_heading and _contains_faq_keyword(prev_heading.get_text(" ", strip=True)):
        return True

    return False


def _is_in_non_faq_context(tag) -> bool:
    """Return True when a tag is likely in non-FAQ sections such as news/company info."""
    if not tag:
        return False

    current = tag
    for _ in range(4):
        if not current:
            break
        if _looks_non_faq_context(_tag_text_for_context(current)):
            return True
        current = getattr(current, "parent", None)

    prev_heading = tag.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
    if prev_heading and _looks_non_faq_context(prev_heading.get_text(" ", strip=True)):
        return True

    return False


def _score_faq_candidate(
    *,
    question: str,
    answer: str,
    in_faq_context: bool,
    in_non_faq_context: bool,
    has_faq_heading: bool,
) -> int:
    """Score FAQ candidate from HTML and accept only sufficiently strong candidates."""
    score = 0
    q = (question or "").strip()
    a = (answer or "").strip()

    if in_faq_context:
        score += 3
    elif has_faq_heading:
        score += 1

    if _looks_like_question(q):
        score += 3
    if "?" in q or "？" in q:
        score += 1

    if 20 <= len(a) <= 600:
        score += 1
    if len(a) < 10 or len(a) > 900:
        score -= 2

    if _looks_non_faq_context(q) or in_non_faq_context:
        score -= 3

    return score


def _extract_faqs_from_schema_item(item: Dict[str, Any]) -> List[Dict[str, str]]:
    faqs = []
    if not isinstance(item, dict):
        return faqs

    item_type = item.get("@type")
    if isinstance(item_type, list):
        is_faq = "FAQPage" in item_type
    else:
        is_faq = item_type == "FAQPage"

    if is_faq:
        main_entity = item.get("mainEntity", [])
        if isinstance(main_entity, dict):
            main_entity = [main_entity]
        for q_item in main_entity:
            if not isinstance(q_item, dict):
                continue
            question = (q_item.get("name") or q_item.get("question") or "").strip()
            answer_text = ""
            answer_obj = q_item.get("acceptedAnswer") or q_item.get("suggestedAnswer") or {}
            if isinstance(answer_obj, list) and answer_obj:
                answer_obj = answer_obj[0]
            if isinstance(answer_obj, dict):
                answer_text = (answer_obj.get("text") or answer_obj.get("answer") or "").strip()
            if question and answer_text:
                faqs.append({
                    "question": question,
                    "answer": answer_text,
                    "source": "json_ld",
                })

    graph_items = item.get("@graph") or []
    if isinstance(graph_items, list):
        for node in graph_items:
            if isinstance(node, dict):
                faqs.extend(_extract_faqs_from_schema_item(node))

    return faqs


def extract_faqs_from_json_ld(json_ld: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    faqs: List[Dict[str, str]] = []
    for item in json_ld:
        if isinstance(item, dict):
            faqs.extend(_extract_faqs_from_schema_item(item))
    return _dedupe_faq_items(faqs)


def extract_faqs_from_html(
    soup: BeautifulSoup,
    *,
    return_meta: bool = False,
) -> List[Dict[str, str]] | Tuple[List[Dict[str, str]], Dict[str, Any]]:
    faqs: List[Dict[str, str]] = []
    html_candidates = 0
    html_filtered_out = 0

    def clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())

    has_faq_heading = any(
        _contains_faq_keyword(h.get_text(" ", strip=True))
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    )

    # dl/dt/dd 形式
    for dl in soup.find_all("dl"):
        in_faq_context = _is_in_faq_context(dl)
        in_non_faq_context = _is_in_non_faq_context(dl)
        dl_candidates: List[Dict[str, str]] = []
        dl_question_like_count = 0
        for dt in dl.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            question = clean_text(dt.get_text(" ", strip=True))
            answer = clean_text(dd.get_text(" ", strip=True))
            html_candidates += 1
            if not (10 <= len(answer) <= 500):
                html_filtered_out += 1
                continue
            score = _score_faq_candidate(
                question=question,
                answer=answer,
                in_faq_context=in_faq_context,
                in_non_faq_context=in_non_faq_context,
                has_faq_heading=has_faq_heading,
            )
            question_like = _looks_like_question(question)
            if question_like:
                dl_question_like_count += 1
            # FAQ文脈にない場合は、質問らしさが弱い候補を除外
            if score < 3:
                html_filtered_out += 1
                continue
            if 4 <= len(question) <= 120:
                dl_candidates.append({
                    "question": question,
                    "answer": answer,
                    "source": "html",
                })
            else:
                html_filtered_out += 1

        # ブロック単位の最終判定:
        # FAQ文脈がないのに質問らしい項目が少ないdlはFAQとして扱わない
        if not in_faq_context and dl_candidates:
            if dl_question_like_count == 0:
                html_filtered_out += len(dl_candidates)
                dl_candidates = []

        faqs.extend(dl_candidates)

    # Q: / A: 形式の簡易抽出
    text_lines = [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]
    q_pattern = re.compile(r"^(?:Q|Ｑ)[\s:：．\.]+(.+)")
    a_pattern = re.compile(r"^(?:A|Ａ)[\s:：．\.]+(.+)")
    current_q = ""
    for line in text_lines:
        q_match = q_pattern.match(line)
        if q_match:
            current_q = q_match.group(1).strip()
            continue
        a_match = a_pattern.match(line)
        if a_match and current_q:
            answer = a_match.group(1).strip()
            html_candidates += 1
            score = _score_faq_candidate(
                question=current_q,
                answer=answer,
                in_faq_context=has_faq_heading,
                in_non_faq_context=False,
                has_faq_heading=has_faq_heading,
            )
            if 4 <= len(current_q) <= 120 and 10 <= len(answer) <= 500 and score >= 2:
                faqs.append({
                    "question": current_q,
                    "answer": answer,
                    "source": "html",
                })
            else:
                html_filtered_out += 1
            current_q = ""

    deduped = _dedupe_faq_items(faqs)
    if return_meta:
        return deduped, {
            "has_faq_heading": has_faq_heading,
            "html_candidates": html_candidates,
            "html_filtered_out": html_filtered_out,
        }
    return deduped


def _validate_faq_consistency(items: List[Dict[str, str]], soup: BeautifulSoup) -> Dict[str, Any]:
    """FAQと本文の整合性を簡易検証（決定的判定ではなく、乖離検知の補助）。"""
    page_text_norm = _normalize_faq_text(soup.get_text(" ", strip=True))
    total = len(items)
    consistent = 0
    suspicious_items: List[Dict[str, str]] = []

    for item in items:
        question = str(item.get("question", "") or "")
        answer = str(item.get("answer", "") or "")
        source = str(item.get("source", "") or "")

        # HTML抽出FAQは同じ本文由来のため原則整合扱い
        if source == "html":
            consistent += 1
            continue

        q_norm = _normalize_faq_text(question)
        a_norm = _normalize_faq_text(answer)
        q_anchor = q_norm[:24] if len(q_norm) >= 8 else q_norm
        a_anchor = a_norm[:24] if len(a_norm) >= 12 else a_norm
        q_hit = bool(q_anchor and q_anchor in page_text_norm)
        a_hit = bool(a_anchor and a_anchor in page_text_norm)

        if q_hit or a_hit:
            consistent += 1
            continue

        suspicious_items.append({
            "question": question[:120],
            "reason": "本文との一致が弱い可能性（JSON-LDのみ記載の可能性）",
            "source": source or "unknown",
        })

    suspicious = len(suspicious_items)
    if total == 0:
        ratio = 1.0
    else:
        ratio = consistent / total

    if ratio >= 0.9:
        level = "high"
    elif ratio >= 0.6:
        level = "medium"
    else:
        level = "low"

    recommendations: List[str] = []
    if suspicious > 0:
        recommendations.append("JSON-LDのFAQ内容が本文にも表示されているか確認してください。")
        recommendations.append("FAQ本文とJSON-LDを同時更新する運用に統一してください。")

    return {
        "checked": total,
        "consistent_count": consistent,
        "suspicious_count": suspicious,
        "consistency_ratio": round(ratio, 2),
        "consistency_level": level,
        "suspicious_items": suspicious_items[:5],
        "recommendations": recommendations[:3],
    }


def build_faq_detection(json_ld: List[Dict[str, Any]], soup: BeautifulSoup) -> Dict[str, Any]:
    schema_faqs = extract_faqs_from_json_ld(json_ld)
    html_result = extract_faqs_from_html(soup, return_meta=True)
    if isinstance(html_result, tuple):
        html_faqs, html_meta = html_result
    else:
        html_faqs, html_meta = html_result, {}
    combined = _dedupe_faq_items(schema_faqs + html_faqs)
    validation = _validate_faq_consistency(combined, soup)
    return {
        "items": combined,
        "count": len(combined),
        "sources": {
            "json_ld": len(schema_faqs),
            "html": len(html_faqs),
        },
        "signals": html_meta,
        "validation": validation,
    }
