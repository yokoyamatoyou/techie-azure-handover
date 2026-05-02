from __future__ import annotations

from collections import Counter
from typing import Any

from analysis_core.common_constants import INTENT_DEFINITIONS, LOCAL_SUFFIX_RE, PAGE_GAP_DEFINITIONS
from analysis_core.domain_utils import _contains_named_term
from analysis_core.text_utils import dedupe_preserve_order, normalize_text


def _contains_signal(text: str, signals: list[str]) -> bool:
    haystack = text.lower()
    return any(signal.lower() in haystack for signal in signals)


def classify_keyword_intent(keyword: str, brand_terms: list[str] | None = None) -> dict[str, Any]:
    normalized = normalize_text(keyword)
    haystack = normalized.lower()
    matches: list[str] = []

    normalized_brand_terms = [normalize_text(term).lower() for term in (brand_terms or []) if normalize_text(term)]
    if normalized_brand_terms and any(term in haystack for term in normalized_brand_terms):
        matches.append("branded")

    if _contains_signal(haystack, INTENT_DEFINITIONS["price"]["signals"]):
        matches.append("price")
    if _contains_signal(haystack, INTENT_DEFINITIONS["comparison"]["signals"]):
        matches.append("comparison")
    if _contains_signal(haystack, INTENT_DEFINITIONS["case_study"]["signals"]):
        matches.append("case_study")
    if _contains_signal(haystack, INTENT_DEFINITIONS["faq"]["signals"]) or "?" in haystack or "？" in haystack:
        matches.append("faq")
    if _contains_signal(haystack, INTENT_DEFINITIONS["how_to"]["signals"]):
        matches.append("how_to")

    has_local_signal = _contains_signal(haystack, INTENT_DEFINITIONS["local"]["signals"])
    if not has_local_signal and LOCAL_SUFFIX_RE.search(normalized):
        has_local_signal = any(token in normalized for token in ("京都", "大阪", "東京", "横浜", "札幌", "福岡", "名古屋", "神戸"))
    if has_local_signal:
        matches.append("local")

    if not matches:
        matches.append("faq" if ("?" in haystack or "？" in haystack or "とは" in haystack) else "how_to")

    ordered_matches = dedupe_preserve_order(matches)
    priority = ["price", "comparison", "local", "case_study", "faq", "how_to", "branded", "general"]
    primary = next((key for key in priority if key in ordered_matches), ordered_matches[0])
    if not ordered_matches:
        ordered_matches = ["general"]
        primary = "general"

    return {
        "primary": primary,
        "label": INTENT_DEFINITIONS.get(primary, INTENT_DEFINITIONS["general"])["label"],
        "labels": [INTENT_DEFINITIONS.get(key, INTENT_DEFINITIONS["general"])["label"] for key in ordered_matches],
        "matched": ordered_matches,
    }


def classify_answer_type(
    keyword: str,
    answer_text: str,
    citation_titles: str,
    citation_domains: list[str],
    *,
    brand_terms: list[str] | None = None,
) -> dict[str, Any]:
    keyword_norm = normalize_text(keyword)
    answer_norm = normalize_text(answer_text)
    combined = normalize_text(" ".join([keyword_norm, answer_norm, citation_titles, " ".join(citation_domains)])).lower()
    keyword_haystack = keyword_norm.lower()
    scores: Counter[str] = Counter()

    for key, definition in INTENT_DEFINITIONS.items():
        if key == "general":
            continue
        for signal in definition["signals"]:
            if not _contains_named_term(combined, signal):
                continue
            scores[key] += 2 if _contains_named_term(keyword_haystack, signal) else 1

    if "?" in keyword_norm or "？" in keyword_norm or "?" in answer_norm or "？" in answer_norm:
        scores["faq"] += 2
    if LOCAL_SUFFIX_RE.search(keyword_norm) or LOCAL_SUFFIX_RE.search(answer_norm):
        scores["local"] += 1
    if brand_terms and any(_contains_named_term(combined, term) for term in brand_terms):
        scores["branded"] += 1

    if not scores:
        return classify_keyword_intent(keyword_norm or answer_norm, brand_terms=brand_terms)

    priority = ["comparison", "price", "faq", "case_study", "local", "how_to", "branded", "general"]
    matched = [key for key in priority if scores.get(key, 0) > 0]
    primary = max(matched, key=lambda item: (scores[item], -priority.index(item)))
    return {
        "primary": primary,
        "label": INTENT_DEFINITIONS.get(primary, INTENT_DEFINITIONS["general"])["label"],
        "labels": [INTENT_DEFINITIONS.get(key, INTENT_DEFINITIONS["general"])["label"] for key in matched],
        "matched": matched,
    }


def infer_page_gap(
    keyword: str,
    payload: dict[str, Any],
    *,
    brand_terms: list[str] | None = None,
    target_hit: bool = False,
    brand_hit: bool = False,
) -> dict[str, Any]:
    intent = classify_keyword_intent(keyword, brand_terms=brand_terms)
    keyword_haystack = normalize_text(keyword).lower()
    action_text = " ".join(str(item or "") for item in (payload.get("recommended_actions") or []))
    snapshot_text = str(payload.get("answer_snapshot") or "")
    citation_text = " ".join(str(item or "") for item in (payload.get("citation_urls") or []))
    combined = normalize_text(" ".join([keyword, action_text, snapshot_text, citation_text])).lower()

    page_key = intent["primary"]
    explicit_local_query = (
        intent["primary"] == "local"
        and not _contains_signal(keyword_haystack, INTENT_DEFINITIONS["comparison"]["signals"])
        and not _contains_signal(keyword_haystack, INTENT_DEFINITIONS["price"]["signals"])
    )
    if not explicit_local_query:
        if _contains_signal(combined, INTENT_DEFINITIONS["comparison"]["signals"]):
            page_key = "comparison"
        elif _contains_signal(combined, INTENT_DEFINITIONS["price"]["signals"]):
            page_key = "price"
        elif _contains_signal(combined, INTENT_DEFINITIONS["case_study"]["signals"]):
            page_key = "case_study"
        elif _contains_signal(combined, INTENT_DEFINITIONS["faq"]["signals"]):
            page_key = "faq"
        elif _contains_signal(combined, INTENT_DEFINITIONS["local"]["signals"]):
            page_key = "local"
        elif _contains_signal(combined, INTENT_DEFINITIONS["how_to"]["signals"]):
            page_key = "how_to"
        elif "branded" in intent["matched"]:
            page_key = "branded"

    spec = PAGE_GAP_DEFINITIONS.get(page_key, PAGE_GAP_DEFINITIONS["general"])
    reasons = [spec["gap_label"]]
    for candidate_key in ("comparison", "price", "faq", "local", "case_study", "how_to"):
        if candidate_key == page_key:
            continue
        if _contains_signal(combined, INTENT_DEFINITIONS[candidate_key]["signals"]):
            reasons.append(PAGE_GAP_DEFINITIONS[candidate_key]["gap_label"])

    if not target_hit:
        reasons.append("自社URLの根拠不足")
    elif not brand_hit and page_key != "branded":
        reasons.append("ブランド想起不足")

    ordered_reasons = dedupe_preserve_order(reasons)[:3]
    priority_label = "高" if not target_hit else ("中" if not brand_hit else "維持")
    return {
        "intent_key": intent["primary"],
        "intent_label": intent["label"],
        "intent_labels": intent["labels"],
        "page_type_key": page_key,
        "page_type_label": spec["page_type_label"],
        "gap_label": spec["gap_label"],
        "gap_reasons": ordered_reasons,
        "next_step": spec["next_step"],
        "priority_label": priority_label,
        "summary": f"{spec['page_type_label']}を優先。{ordered_reasons[0]}を先に埋める。",
    }
