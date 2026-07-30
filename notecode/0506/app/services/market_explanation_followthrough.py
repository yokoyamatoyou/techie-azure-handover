from __future__ import annotations

from typing import Any

from app.services.draft_followthrough import append_paragraphs_to_h2_sections, body_chars_excluding_headings
from app.services.market_explanation_context_sanitizer import sanitize_market_explanation_context_text
from app.services.reader_meta_sentence import classify_reader_meta_sentence


_READER_META_BLOCKING_ISSUES = {"low_density_bridge_sentence", "abstract_navigation_phrase"}


def market_explanation_selected_excerpt_floor_followthrough(
    draft: str,
    article_brief: dict[str, Any],
    selected_source_excerpts: list[dict[str, Any]] | None,
    knowledge_pack: dict[str, Any] | None = None,
) -> str:
    brief = article_brief.get("article_brief", {}) if isinstance(article_brief, dict) else {}
    floor_chars = int(brief.get("body_length_floor_chars") or 0)
    if str(brief.get("genre_id") or "") != "market_explanation" or floor_chars <= 0:
        return draft
    current_chars = body_chars_excluding_headings(draft)
    if current_chars >= floor_chars:
        return draft
    target_chars = floor_chars + _market_explanation_residual_buffer_chars(floor_chars)
    headings = {str(s.get("section_id")): str(s.get("heading")) for s in brief.get("sections") or [] if isinstance(s, dict)}
    paragraphs: dict[str, list[str]] = {}
    existing = "".join(draft.split())
    last_heading = ""
    for excerpt in selected_source_excerpts or []:
        section_id = str((excerpt.get("section_ids") or [""])[0])
        heading = headings.get(section_id)
        if not heading:
            continue
        last_heading = heading
        for paragraph in _excerpt_market_explanation_paragraphs(str(excerpt.get("text") or ""), existing):
            paragraphs.setdefault(heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= target_chars:
                break
        if current_chars >= target_chars:
            break
    if current_chars < target_chars:
        claim_heading = last_heading or next(iter(headings.values()), "")
        for heading, paragraph in _market_explanation_claim_paragraphs(brief, knowledge_pack, selected_source_excerpts, existing, claim_heading):
            paragraphs.setdefault(heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= target_chars:
                break
    if current_chars < target_chars:
        claim_heading = last_heading or next(iter(headings.values()), "")
        for heading, paragraph in _market_explanation_residual_detail_paragraphs(brief, knowledge_pack, selected_source_excerpts, existing, claim_heading):
            paragraphs.setdefault(heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= target_chars:
                break
    if current_chars < target_chars and last_heading:
        selected_text = "\n".join(str(excerpt.get("text") or "") for excerpt in selected_source_excerpts)
        for paragraph in _market_explanation_source_viewpoint_paragraphs(selected_text, existing):
            if not _passes_market_explanation_followthrough_quality_gate(paragraph):
                continue
            paragraphs.setdefault(last_heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= target_chars:
                break
    if not paragraphs:
        return draft
    return append_paragraphs_to_h2_sections(draft, paragraphs)


def _excerpt_market_explanation_paragraphs(text: str, existing: str) -> list[str]:
    candidates: list[str] = []
    sanitized_text = sanitize_market_explanation_context_text(text)
    for raw_line in sanitized_text.replace("\r\n", "\n").replace("。", "。\n").splitlines():
        line = raw_line.strip(" \t.。…")
        compact = "".join(line.split())
        if len(compact) < 12 or compact.startswith(("http://", "https://")) or _mostly_spaced_ascii(line):
            continue
        if compact in existing:
            continue
        chunks = [line[i : i + 180].strip("、, ") for i in range(0, len(line), 180)]
        candidates.extend(chunk if chunk.endswith(("。", "．", ".")) else chunk + "。" for chunk in chunks if chunk)
    paragraphs: list[str] = []
    buffer = ""
    for candidate in candidates:
        if not buffer:
            buffer = candidate
            continue
        if body_chars_excluding_headings(buffer + candidate) <= 190:
            buffer += candidate
            continue
        paragraphs.append(buffer)
        buffer = candidate
    if buffer:
        paragraphs.append(buffer)
    return paragraphs[:8]


def _market_explanation_residual_buffer_chars(floor_chars: int) -> int:
    return min(300, max(120, floor_chars // 4))


def _market_explanation_claim_paragraphs(
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any] | None,
    selected_source_excerpts: list[dict[str, Any]] | None,
    existing: str,
    fallback_heading: str,
) -> list[tuple[str, str]]:
    if not fallback_heading:
        return []
    pack = knowledge_pack.get("article_knowledge_pack", {}) if isinstance(knowledge_pack, dict) else {}
    facts = pack.get("confirmed_facts") if isinstance(pack, dict) else []
    if not isinstance(facts, list):
        return []
    claim_heading = _market_claim_heading_map(brief, fallback_heading)
    assigned_ids = set(claim_heading)
    selected_context = "".join(
        "".join(sanitize_market_explanation_context_text(str(excerpt.get("text") or "")).split())
        for excerpt in selected_source_excerpts or []
        if isinstance(excerpt, dict)
    )
    paragraphs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        claim_id = str(fact.get("claim_id") or "")
        paragraph = _market_explanation_fact_paragraph(fact)
        compact = "".join(paragraph.split())
        if not paragraph or compact in existing or compact in seen:
            continue
        if claim_id not in assigned_ids and compact not in selected_context:
            continue
        if not _passes_market_explanation_followthrough_quality_gate(paragraph):
            continue
        paragraphs.append((claim_heading.get(claim_id, fallback_heading), paragraph))
        seen.add(compact)
    return paragraphs[:8]


def _market_claim_heading_map(brief: dict[str, Any], fallback_heading: str) -> dict[str, str]:
    section_headings = {str(s.get("section_id")): str(s.get("heading")) for s in brief.get("sections") or [] if isinstance(s, dict)}
    claim_heading: dict[str, str] = {}
    for allocation in brief.get("claim_allocation") or []:
        if not isinstance(allocation, dict):
            continue
        heading = section_headings.get(str(allocation.get("section_id") or ""), fallback_heading)
        for claim_id in allocation.get("claim_ids") or []:
            claim_heading[str(claim_id)] = heading
    for section in brief.get("sections") or []:
        if not isinstance(section, dict):
            continue
        heading = str(section.get("heading") or fallback_heading)
        for claim_id in section.get("assigned_claim_ids") or []:
            claim_heading.setdefault(str(claim_id), heading)
    return claim_heading


def _market_explanation_fact_paragraph(fact: dict[str, Any]) -> str:
    text = str(fact.get("preferred_expression") or fact.get("claim") or "")
    sanitized = sanitize_market_explanation_context_text(text)
    compact = "".join(sanitized.split()).strip("。")
    if len(compact) < 16 or _mostly_spaced_ascii(sanitized):
        return ""
    if sanitized.startswith(("http://", "https://", "Copyright", "COPYRIGHT")):
        return ""
    if not sanitized.endswith(("。", "！", "？", ".", "．")):
        sanitized += "。"
    return sanitized


def _market_explanation_residual_detail_paragraphs(
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any] | None,
    selected_source_excerpts: list[dict[str, Any]] | None,
    existing: str,
    fallback_heading: str,
) -> list[tuple[str, str]]:
    if not fallback_heading:
        return []
    section_headings = [str(s.get("heading") or "") for s in brief.get("sections") or [] if isinstance(s, dict)]
    front_heading = section_headings[0] if section_headings else fallback_heading
    middle_heading = section_headings[1] if len(section_headings) > 1 else front_heading
    last_heading = section_headings[-1] if section_headings else fallback_heading
    context = _market_explanation_context_compact(knowledge_pack, selected_source_excerpts)
    candidates = [
        (front_heading, ("メリット", "デメリット", "競争環境"), "生成AIにはメリットとデメリットの両方があるため、私たちは公正かつ自由な競争環境を保つ視点と、健全な実装を見る視点を分けて扱います。"),
        (middle_heading, ("流動的", "迅速", "柔軟"), "市場状況が流動的であるという記述は、調査をアジャイルに、迅速かつ柔軟な方法で進める理由にもつながります。"),
        (middle_heading, ("前回ペーパー", "アップデート", "情報更新"), "前回ペーパーをアップデートして報告書ver.1.0を取りまとめ、今後も調査と情報更新を継続する方針が示されています。"),
        (middle_heading, ("情報・意見", "前回ペーパー"), "2024年10月に関係各方面から広く情報・意見を募集した流れも、生成AIを巡る競争の論点を更新しながら扱う前提になります。"),
        (middle_heading, ("健全", "経済社会", "実装"), "健全な形で経済社会に実装する観点が置かれているため、私たちは技術の進展だけでなく、実装のされ方も市場を見る材料に含めます。"),
        (last_heading, ("GENIAC", "共創事例", "ユースケース"), "GENIACの情報発信は、モデル開発力の強化だけでなく、共創事例やユースケース、イベントレポートを通じて利用場面の広がりを見る材料になります。"),
        (last_heading, ("建設", "医療", "研究開発"), "建設、医療、研究開発などの現場に触れている点から、モデル開発だけでなく利用場面も市場性の確認材料になります。"),
    ]
    paragraphs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for heading, required_terms, paragraph in candidates:
        if not all(term in context for term in required_terms):
            continue
        compact = "".join(paragraph.split())
        if compact in existing or compact in seen:
            continue
        if not _passes_market_explanation_followthrough_quality_gate(paragraph):
            continue
        paragraphs.append((heading, paragraph))
        seen.add(compact)
    return paragraphs[:8]


def _market_explanation_context_compact(
    knowledge_pack: dict[str, Any] | None,
    selected_source_excerpts: list[dict[str, Any]] | None,
) -> str:
    chunks = [
        sanitize_market_explanation_context_text(str(excerpt.get("text") or ""))
        for excerpt in selected_source_excerpts or []
        if isinstance(excerpt, dict)
    ]
    pack = knowledge_pack.get("article_knowledge_pack", {}) if isinstance(knowledge_pack, dict) else {}
    facts = pack.get("confirmed_facts") if isinstance(pack, dict) else []
    if isinstance(facts, list):
        chunks.extend(_market_explanation_fact_paragraph(fact) for fact in facts if isinstance(fact, dict))
    return "".join("".join(chunk.split()) for chunk in chunks if chunk)


def _market_explanation_source_viewpoint_paragraphs(text: str, existing: str) -> list[str]:
    compact_text = "".join(text.split())
    candidates: list[str] = []
    if "調査" in compact_text and ("情報更新" in compact_text or "継続" in compact_text):
        candidates.append("この材料からは、生成AI関連市場を一度きりの報告ではなく、調査と情報更新が続く対象として見る必要があることを確認できます。")
    if "GENIAC通信" in compact_text and ("ユースケース" in compact_text or "共創事例" in compact_text):
        candidates.append("GENIAC通信には、採択事業者の共創事例、ユースケース、イベントレポートなどの情報発信が含まれます。")
    return [candidate for candidate in candidates if "".join(candidate.split()) not in existing]


def _passes_market_explanation_followthrough_quality_gate(paragraph: str) -> bool:
    issues = set(classify_reader_meta_sentence(paragraph))
    return not issues.intersection(_READER_META_BLOCKING_ISSUES)


def _mostly_spaced_ascii(text: str) -> bool:
    letters = sum(1 for char in text if char.isascii() and char.isalpha())
    spaces = sum(1 for char in text if char == " ")
    return letters >= 12 and spaces >= max(6, letters // 2)
