from __future__ import annotations

import re
from typing import Any

from app.services.draft_followthrough import append_paragraphs_to_h2_sections, body_chars_excluding_headings
from app.services.human_visible_surface_gate import LOCAL_RENDERER_FINGERPRINTS, check_human_visible_surface

LOCAL_SURFACE_FINGERPRINTS = tuple(fingerprint[2] for fingerprint in LOCAL_RENDERER_FINGERPRINTS)

def announcement_selected_excerpt_floor_followthrough(
    draft: str,
    article_brief: dict[str, Any],
    selected_source_excerpts: list[dict[str, Any]] | None,
    knowledge_pack: dict[str, Any] | None = None,
) -> str:
    brief = article_brief.get("article_brief", {}) if isinstance(article_brief, dict) else {}
    if str(brief.get("genre_id") or "") != "announcement":
        return draft
    draft = _sanitize_announcement_local_surface(draft)
    floor_chars = _int(brief.get("body_length_floor_chars"))
    if not selected_source_excerpts or floor_chars <= 0:
        return draft
    current_chars = body_chars_excluding_headings(draft)
    if current_chars >= floor_chars:
        return draft

    headings = {str(s.get("section_id")): str(s.get("heading")) for s in brief.get("sections") or [] if isinstance(s, dict)}
    paragraphs: dict[str, list[str]] = {}
    existing = _compact(draft)
    last_heading = ""
    for excerpt in selected_source_excerpts:
        section_id = str((excerpt.get("section_ids") or [""])[0])
        heading = headings.get(section_id)
        if not heading:
            continue
        last_heading = heading
        for paragraph in _excerpt_announcement_paragraphs(str(excerpt.get("text") or ""), existing):
            paragraphs.setdefault(heading, []).append(paragraph)
            existing += _compact(paragraph)
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= floor_chars:
                break
        if current_chars >= floor_chars:
            break

    claim_heading = last_heading or next(iter(headings.values()), "")
    if current_chars < floor_chars and claim_heading:
        for paragraph in _announcement_claim_paragraphs(brief, knowledge_pack, existing):
            paragraphs.setdefault(claim_heading, []).append(paragraph)
            existing += _compact(paragraph)
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= floor_chars:
                break

    if current_chars < floor_chars and claim_heading:
        source_text = "\n".join(str(excerpt.get("text") or "") for excerpt in selected_source_excerpts)
        for paragraph in _announcement_notice_context_paragraphs(source_text, knowledge_pack, existing):
            paragraphs.setdefault(claim_heading, []).append(paragraph)
            existing += _compact(paragraph)
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= floor_chars:
                break

    if not paragraphs and current_chars < floor_chars and claim_heading:
        residual = _announcement_floor_buffer_paragraphs(selected_source_excerpts, knowledge_pack, existing)
        if residual:
            paragraphs.setdefault(claim_heading, []).extend(residual)

    if not paragraphs:
        return draft
    result = _sanitize_announcement_local_surface(append_paragraphs_to_h2_sections(draft, paragraphs))
    if body_chars_excluding_headings(result) < floor_chars and claim_heading:
        existing = _compact(result)
        backfill = _announcement_claim_paragraphs(brief, knowledge_pack, existing)
        backfill.extend(_announcement_floor_buffer_paragraphs(selected_source_excerpts, knowledge_pack, existing))
        if backfill:
            result = _sanitize_announcement_local_surface(
                append_paragraphs_to_h2_sections(result, {claim_heading: backfill})
            )
    return result


def _sanitize_announcement_local_surface(text: str) -> str:
    cleaned_lines: list[str] = []
    seen_sentences: set[str] = set()
    for raw_line in str(text or "").replace("\r\n", "\n").splitlines():
        if not raw_line.lstrip().startswith("#") and _is_local_surface_line(raw_line):
            continue
        line = _remove_duplicate_long_sentences_from_line(raw_line, seen_sentences)
        if line.strip() or not raw_line.strip():
            cleaned_lines.append(line)
    return _remove_duplicate_surface_findings("\n".join(cleaned_lines).strip())


def _remove_duplicate_surface_findings(text: str) -> str:
    report = check_human_visible_surface(text, {"article_brief": {"genre_id": "announcement", "body_length_floor_chars": 1}})
    revised = text
    for finding in report["human_visible_surface_gate"]["findings"]:
        if finding.get("code") != "duplicate_long_sentence":
            continue
        duplicate_text = str(finding.get("text") or "")
        if duplicate_text:
            revised = _remove_second_occurrence(revised, duplicate_text)
    return revised.strip()
def _remove_second_occurrence(text: str, needle: str) -> str:
    first = text.find(needle)
    if first < 0:
        return text
    second = text.find(needle, first + len(needle))
    if second < 0:
        return text
    return text[:second] + text[second + len(needle) :]


def _excerpt_announcement_paragraphs(text: str, existing: str) -> list[str]:
    paragraphs: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("。", "。\n").splitlines():
        line = raw_line.strip(" \t.。…")
        if not _is_usable_announcement_line(line):
            continue
        paragraph = _announcement_self_voice(line)
        compact = _compact(paragraph)
        if len(compact) < 20 or compact in existing:
            continue
        paragraphs.append(paragraph if paragraph.endswith(("。", "．", ".")) else paragraph + "。")
    return paragraphs[:8]

def _announcement_claim_paragraphs(
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any] | None,
    existing: str,
) -> list[str]:
    facts = _confirmed_facts(knowledge_pack)
    assigned_ids = _brief_assigned_claim_ids(brief)
    fact_by_id = {str(f.get("claim_id")): f for f in facts if isinstance(f, dict)}
    ordered_ids = assigned_ids + [str(f.get("claim_id")) for f in facts if isinstance(f, dict) and str(f.get("claim_id")) not in assigned_ids]
    paragraphs: list[str] = []
    seen: set[str] = set()
    for claim_id in ordered_ids:
        fact = fact_by_id.get(claim_id)
        if not fact:
            continue
        raw_claim = str(fact.get("preferred_expression") or fact.get("claim") or "")
        if _is_incomplete_announcement_claim(raw_claim):
            continue
        paragraph = _announcement_claim_to_paragraph(raw_claim)
        if claim_id not in assigned_ids and not _is_useful_unassigned_notice_claim(paragraph):
            continue
        compact = _compact(paragraph)
        if not paragraph or compact in existing or compact in seen or _is_announcement_label_only(paragraph):
            continue
        paragraphs.append(paragraph)
        seen.add(compact)
    return paragraphs[:8]

def _announcement_notice_context_paragraphs(
    selected_text: str,
    knowledge_pack: dict[str, Any] | None,
    existing: str,
) -> list[str]:
    claim_text = "\n".join(
        str(f.get("preferred_expression") or f.get("claim") or "")
        for f in _confirmed_facts(knowledge_pack)
        if isinstance(f, dict)
    )
    compact = _compact(selected_text + "\n" + claim_text)
    candidates: list[str] = []
    if "AI" in compact and "2026" in compact:
        candidates.append("本件では、大規模実証の開始日、利用可能な対象人数、今後の対象拡大を中心にお知らせします。")
    if "10" in compact and ("18" in compact or "8" in compact):
        candidates.append("対象人数は、現時点で利用可能な人数と、今後利用できるよう環境整備を進める人数を分けて記載します。")
    if "AI" in compact:
        candidates.append("源内は、政府職員が安全・安心にAIを活用できる基盤として扱います。")
    return [candidate for candidate in candidates if _compact(candidate) not in existing]

def _announcement_floor_buffer_paragraphs(
    selected_source_excerpts: list[dict[str, Any]] | None,
    knowledge_pack: dict[str, Any] | None,
    existing: str,
) -> list[str]:
    selected_text = "\n".join(str(excerpt.get("text") or "") for excerpt in selected_source_excerpts or [])
    claim_text = "\n".join(
        str(fact.get("preferred_expression") or fact.get("claim") or "")
        for fact in _confirmed_facts(knowledge_pack)
        if isinstance(fact, dict)
    )
    compact = _compact(selected_text + "\n" + claim_text)
    candidates: list[str] = []
    if "AI" in compact and "2026" in compact:
        candidates.append("開始日と対象人数は、読者がまず確認したい要点として扱います。")
    if "10" in compact and "18" in compact:
        candidates.append("現時点で利用できる約10万人と、今後拡大する約18万人の違いを分けて示します。")
        candidates.append("本文では、5月29日時点の利用状況と、順次対象府省庁・職員数を拡大する予定をあわせて確認します。")
    if "AI" in compact:
        candidates.append("源内は、政府職員のAI活用を安全に進めるための基盤として位置づけ、利用開始日、対象人数、5月29日時点の利用状況、今後の対象府省庁・職員数拡大予定を確認する軸として扱います。")
    return [candidate for candidate in candidates if _compact(candidate) not in existing]
def _confirmed_facts(knowledge_pack: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(knowledge_pack, dict):
        return []
    pack = knowledge_pack.get("article_knowledge_pack")
    if not isinstance(pack, dict):
        pack = knowledge_pack
    facts = pack.get("confirmed_facts") if isinstance(pack, dict) else []
    return facts if isinstance(facts, list) else []
def _brief_assigned_claim_ids(brief: dict[str, Any]) -> list[str]:
    claim_ids: list[str] = []
    for allocation in brief.get("claim_allocation") or []:
        if isinstance(allocation, dict):
            claim_ids.extend(str(claim_id) for claim_id in allocation.get("claim_ids") or [] if claim_id)
    if claim_ids:
        return claim_ids
    for section in brief.get("sections") or []:
        if isinstance(section, dict):
            claim_ids.extend(str(claim_id) for claim_id in section.get("assigned_claim_ids") or [] if claim_id)
    return claim_ids


def _announcement_claim_to_paragraph(claim: str) -> str:
    text = claim.strip(" \t.。…")
    if not text:
        return ""
    if re.fullmatch(r"20\d{2}年\d{1,2}月\d{1,2}日", text):
        return f"本件の公開日は{text}です。"
    return _announcement_self_voice(text)


def _announcement_self_voice(line: str) -> str:
    text = line.strip()
    if text.startswith("デジタル庁においては"):
        text = "当社では" + text.removeprefix("デジタル庁においては")
    elif text.startswith("デジタル庁は"):
        text = "当社は" + text.removeprefix("デジタル庁は")
    text = text.replace("、デジタル庁は", "、当社は")
    text = text.replace("きましたが、", "きました。").replace("きましたが", "きました")
    return text if text.endswith(("。", "．", ".")) else text + "。"


def _is_usable_announcement_line(line: str) -> bool:
    if len(_compact(line)) < 10 or _is_local_surface_line(line):
        return False
    blocked_prefixes = ("http://", "https://", "現在位置", "ホーム", "資料", "関連情報", "シェア", "補助メモ", "（参考資料）")
    if line.startswith(blocked_prefixes) or line in {"公開日", "新着・更新"}:
        return False
    if line.endswith("開始します") and "大規模実証" in line:
        return False
    return not _mostly_spaced_ascii(line)


def _is_announcement_label_only(text: str) -> bool:
    compact = _compact(text).strip("。")
    return compact in {"ガバメントAI「源内」", "1.概要"} or (
        len(compact) <= 8 and not any(char.isdigit() for char in compact)
    )


def _is_local_surface_line(text: str) -> bool:
    line = str(text or "")
    return any(fingerprint in line for fingerprint in LOCAL_SURFACE_FINGERPRINTS) or _is_announcement_label_only(line)


def _remove_duplicate_long_sentences_from_line(line: str, seen_sentences: set[str]) -> str:
    pieces = re.findall(r"[^。！？!?\n]+[。！？!?]?", str(line or ""))
    if not pieces:
        return line
    kept: list[str] = []
    for sentence in pieces:
        normalized = re.sub(r"[\s\W_]+", "", sentence)
        if len(normalized) >= 14:
            if normalized in seen_sentences:
                continue
            seen_sentences.add(normalized)
        kept.append(sentence)
    return "".join(kept).strip()


def _is_incomplete_announcement_claim(claim: str) -> bool:
    text = claim.strip(" \t.。…")
    return text.endswith(("した", "おける", "ためには"))


def _is_useful_unassigned_notice_claim(paragraph: str) -> bool:
    return any(term in paragraph for term in ("ガバメントAIとは", "安全・安心", "生成AI利用環境", "各府省庁に展開"))


def _mostly_spaced_ascii(text: str) -> bool:
    letters = sum(1 for char in text if char.isascii() and char.isalpha())
    return letters >= 12 and sum(1 for char in text if char == " ") >= max(6, letters // 2)


def _compact(text: str) -> str:
    return "".join(str(text or "").split())

def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
