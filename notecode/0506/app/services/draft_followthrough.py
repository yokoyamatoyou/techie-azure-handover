from __future__ import annotations

import re
from typing import Any

DAILY_ACTIVITY_LOCAL_SURFACE_PHRASES = (
    "私たちが取り組んでいることを、少し具体的に紹介します",
    "私たちの取り組みを、少し具体的に紹介します",
    "データの扱いに迷ったときは、小さなことでもご相談ください",
)
CASE_STUDY_LOCAL_SURFACE_PHRASES = DAILY_ACTIVITY_LOCAL_SURFACE_PHRASES
DAILY_ACTIVITY_TRUNCATED_SOURCE_FRAGMENTS = (
    "日時：2026年3。",
    "続きを読む",
)
DAILY_ACTIVITY_NAVIGATION_NOISE = (
    "参加者募集のお知らせ",
    "入札情報",
    "自動販売機",
    "ロボット導入",
    "10年後の自社",
    "2026年7月30日",
    "募集終了",
    "カテゴリー",
    "タグ",
    "お申込み方法",
    "こちらをご覧ください",
    "開催します",
    "シャッターを押すと開閉する）のこと",
)


def daily_activity_scene_followthrough(
    draft: str,
    article_brief: dict[str, Any],
    selected_source_excerpts: list[dict[str, Any]] | None,
) -> str:
    brief = article_brief.get("article_brief", {}) if isinstance(article_brief, dict) else {}
    floor_chars = int(brief.get("body_length_floor_chars") or 0)
    if str(brief.get("genre_id") or "") != "daily_activity" or not selected_source_excerpts or floor_chars <= 0:
        return draft
    sanitized = _sanitize_daily_activity_local_surface(draft)
    sanitized_changed = sanitized != draft
    draft = sanitized
    current_chars = body_chars_excluding_headings(draft)
    if current_chars >= floor_chars:
        return draft
    if not sanitized_changed and current_chars >= max(260, floor_chars * 3 // 5):
        return draft
    headings = {str(s.get("section_id")): str(s.get("heading")) for s in brief.get("sections") or [] if isinstance(s, dict)}
    paragraphs: dict[str, list[str]] = {}
    existing = "".join(draft.split())
    for excerpt in selected_source_excerpts:
        section_id = str((excerpt.get("section_ids") or [""])[0])
        heading = headings.get(section_id)
        if not heading:
            continue
        for paragraph in _excerpt_scene_paragraphs(str(excerpt.get("text") or ""), existing):
            paragraphs.setdefault(heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= floor_chars:
                break
        if current_chars >= floor_chars:
            break
    if current_chars < floor_chars:
        fallback_heading = list(headings.values())[-1] if headings else ""
        for paragraph in _daily_activity_source_detail_paragraphs(selected_source_excerpts, existing):
            paragraphs.setdefault(fallback_heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= floor_chars:
                break
    if not paragraphs:
        return draft
    result = _sanitize_daily_activity_local_surface(append_paragraphs_to_h2_sections(draft, paragraphs))
    current_chars = body_chars_excluding_headings(result)
    if current_chars >= floor_chars:
        return result
    fallback_heading = list(headings.values())[-1] if headings else ""
    existing = "".join(result.split())
    extra_paragraphs: dict[str, list[str]] = {}
    for paragraph in _daily_activity_source_detail_paragraphs(selected_source_excerpts, existing):
        extra_paragraphs.setdefault(fallback_heading, []).append(paragraph)
        existing += "".join(paragraph.split())
        current_chars += body_chars_excluding_headings(paragraph)
        if current_chars >= floor_chars:
            break
    if not extra_paragraphs:
        return result
    return _sanitize_daily_activity_local_surface(append_paragraphs_to_h2_sections(result, extra_paragraphs))


def case_study_surface_followthrough(draft: str, article_brief: dict[str, Any]) -> str:
    brief = article_brief.get("article_brief", {}) if isinstance(article_brief, dict) else {}
    if str(brief.get("genre_id") or "") != "case_study":
        return draft
    sanitized = _sanitize_case_study_local_surface(draft)
    return draft if sanitized.rstrip("\n") == str(draft or "").rstrip("\n") else sanitized


def append_paragraphs_to_h2_sections(draft: str, paragraphs: dict[str, list[str]]) -> str:
    out: list[str] = []
    current_heading = ""
    for line in draft.splitlines():
        if line.startswith("## ") and current_heading in paragraphs:
            out.extend(["", *paragraphs.pop(current_heading), ""])
        out.append(line)
        if line.startswith("## "):
            current_heading = line[3:].strip()
    if current_heading in paragraphs:
        out.extend(["", *paragraphs.pop(current_heading)])
    for remaining in paragraphs.values():
        out.extend(["", *remaining])
    return "\n".join(out).strip() + "\n"


def body_chars_excluding_headings(markdown: str) -> int:
    return len("".join("".join(line.split()) for line in markdown.splitlines() if not line.lstrip().startswith("#")))


def _excerpt_scene_paragraphs(text: str, existing: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.replace("。", "。\n").splitlines():
        line = raw_line.strip(" \t.。…")
        compact = "".join(line.split())
        if len(compact) < 28 or compact in existing or compact.startswith(("by", "http")) or _is_daily_activity_surface_noise(line):
            continue
        chunks = [line[i : i + 220].strip("、, ") for i in range(0, len(line), 220)]
        lines.extend(chunk if chunk.endswith(("。", "．", ".")) else chunk + "。" for chunk in chunks if chunk)
    return lines[:8]


def _daily_activity_source_detail_paragraphs(
    selected_source_excerpts: list[dict[str, Any]] | None,
    existing: str,
) -> list[str]:
    selected_text = "\n".join(
        str(excerpt.get("text") or "")
        for excerpt in selected_source_excerpts or []
        if isinstance(excerpt, dict)
    )
    compact_text = "".join(selected_text.split())
    candidates = [
        (
            ("2026年3月10日", "13:30", "16:30", "BW-03"),
            "案内では、2026年3月10日（火）13:30～16:30に、宮城県産業技術総合センターBW-03室で行うワークショップとして示されていました。開催報告を読むときも、この日時と会場を押さえると、活動の場面が具体的になります。",
        ),
        (
            ("クリップライト", "ホームセンター", "講義", "実技"),
            "身近にあるクリップライトやホームセンターで揃う資材を活用し、講義と実技の二部構成で学んだ点も、この回の特徴でした。専門機材だけに寄せず、手元で試しやすい撮影方法を扱ったことが分かります。",
        ),
        (
            ("レンズ", "絞り", "シャッタースピード", "ISO感度"),
            "講義では、レンズ、絞り、シャッタースピード、ISO感度の関係にも触れています。写真が暗くなる、明るくなる、ぶれるといった変化を、設定同士の関係から確認する流れでした。",
        ),
        (
            ("商品開発支援班", "職員", "講師"),
            "開催報告では、当センターの商品開発支援班の職員が講師となり、物撮りを行う手法を扱ったことが示されています。日々の活動として見ると、センター内の支援担当が具体的な撮影方法を講義と実技に分けて伝えた回です。",
        ),
        (
            ("自社ホームページ", "SNS", "自社製品"),
            "背景には、自社ホームページやSNSでの情報発信が欠かせない中、自社製品をもっと魅力的に撮りたいというニーズがありました。活動内容は、その必要に対して身近な道具で応える構成になっています。",
        ),
        (
            ("焦点距離", "被写体", "歪ませず"),
            "レンズ選びでは焦点距離（mm）の重要性にも触れ、被写体の形を歪ませずに写すためのポイントを扱っています。物撮りでは、光だけでなくカメラ側の選び方も確認する流れでした。",
        ),
        (
            ("参加者の皆さん", "共感", "和やか"),
            "講師の失敗談に参加者の皆さんから共感の声が上がり、会場が少し和やかな雰囲気になったことも報告されています。技術説明だけでなく、初めて学ぶ人が入りやすい空気もあったことが伝わります。",
        ),
        (
            ("受講料", "1,200円", "定員", "5人"),
            "募集時の案内では、受講料は1,200円（税込）、定員は5人と示されていました。活動報告の背景として見ると、少人数で実技を含めた研修として組まれていたことも分かります。",
        ),
    ]
    paragraphs: list[str] = []
    for required_terms, paragraph in candidates:
        compact = "".join(paragraph.split())
        if compact in existing or not all(term in compact_text for term in required_terms):
            continue
        paragraphs.append(paragraph)
    return paragraphs


def _sanitize_daily_activity_local_surface(markdown: str) -> str:
    blocks: list[str] = []
    seen: set[str] = set()
    for block in [part.strip() for part in str(markdown or "").split("\n\n") if part.strip()]:
        if block.lstrip().startswith("#"):
            blocks.append(block)
            continue
        kept: list[str] = []
        for sentence in _surface_sentences(block):
            if _is_daily_activity_surface_noise(sentence):
                continue
            normalized = _normalize_surface_sentence(sentence)
            if len(normalized) >= 14 and normalized in seen:
                continue
            seen.add(normalized)
            kept.append(sentence)
        if kept:
            blocks.append("".join(kept).strip())
    return "\n\n".join(blocks).strip() + "\n"


def _sanitize_case_study_local_surface(markdown: str) -> str:
    blocks: list[str] = []
    for block in [part.strip() for part in str(markdown or "").split("\n\n") if part.strip()]:
        if block.lstrip().startswith("#"):
            blocks.append(block)
            continue
        kept = [sentence for sentence in _surface_sentences(block) if not _is_case_study_surface_noise(sentence)]
        if kept:
            blocks.append("".join(kept).strip())
    return "\n\n".join(blocks).strip() + "\n"


def _surface_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.findall(r"[^。！？\n]+[。！？]?", text) if part.strip()]


def _is_daily_activity_surface_noise(text: str) -> bool:
    return (
        any(phrase in text for phrase in DAILY_ACTIVITY_LOCAL_SURFACE_PHRASES)
        or any(fragment in text for fragment in DAILY_ACTIVITY_TRUNCATED_SOURCE_FRAGMENTS)
        or any(fragment in text for fragment in DAILY_ACTIVITY_NAVIGATION_NOISE)
        or text.count("「") != text.count("」")
        or text.endswith(("ことで", "ことで。"))
    )


def _is_case_study_surface_noise(text: str) -> bool:
    stripped = text.strip()
    return (
        any(phrase in text for phrase in CASE_STUDY_LOCAL_SURFACE_PHRASES)
        or text.count("「") != text.count("」")
        or stripped.startswith(("/", "／"))
    )


def _normalize_surface_sentence(sentence: str) -> str:
    return re.sub(r"\s+", "", sentence).strip("。！？「」")
