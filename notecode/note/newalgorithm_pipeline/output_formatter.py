"""Output formatter for note-oriented newalgorithm pipeline."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, Iterable, List, Tuple

from .editor_guard import apply_minimal_editor_guard

_ARTICLE_LABELS = {
    "explanatory_article": "解説",
    "daily_story": "日常",
    "branding": "ブランド",
    "announcement": "お知らせ",
    "case_study": "事例",
    "industry_analysis": "業界分析",
    "comparative_review": "比較レビュー",
}

_GENERIC_BRANDING_TERMS = {
    "価値が必要な背景を示す",
    "現場の工夫を具体化する",
    "読者が自分ごと化できる形で締める",
}
_PREFER_GENERATED_HEAD_ARTICLE_TYPES = {
    "announcement",
    "branding",
    "case_study",
    "explanatory_article",
    "industry_analysis",
}
_LEAD_META_PATTERN = re.compile(r"(として語るとして|この記事で|この記事として言えば|この記事で伝えたい)")
_GENERIC_COMPANY_INTRO_SEED_RE = re.compile(r"(?:企業|会社|自社)(?:の)?紹介$")
_BURSTINESS_TARGET_ARTICLE_TYPES = {"explanatory_article", "industry_analysis"}
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？])\s*")
_BREATHING_PARAGRAPH_LEAD_RE = re.compile(r"^(?:たとえば|例えば|つまり|そのため|一方で|ただし|なお)")
_COMPARE_ENDING_VARIANTS = (
    (re.compile(r"候補に入りやすいです。$"), "候補として残りやすいです。", "candidate"),
    (re.compile(r"向いています。$"), "向く場面があります。", "fit"),
    (re.compile(r"向きます。$"), "向いています。", "fit"),
    (re.compile(r"合いやすいです。$"), "相性が出やすいです。", "fit"),
    (re.compile(r"しやすいです。$"), "しやすい傾向があります。", "ease"),
    (re.compile(r"扱いやすいです。$"), "回しやすいです。", "ease"),
    (re.compile(r"見やすいです。$"), "追いやすいです。", "visibility"),
)
_COMPANY_REANCHOR_CONTEXT_MARKERS = (
    "現場",
    "利用者",
    "顧客",
    "担当者",
    "管理者",
    "導入担当",
    "問い合わせ",
    "運用担当",
    "医療機関",
    "製薬企業",
)


def _normalize_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" 　、。")


def _coefficient_of_variation(lengths: List[int]) -> float:
    if len(lengths) < 2:
        return 0.0
    mean = sum(lengths) / len(lengths)
    if mean <= 0:
        return 0.0
    variance = sum((length - mean) ** 2 for length in lengths) / len(lengths)
    return (variance ** 0.5) / mean


def _reflow_flat_paragraph_cadence(body: str, article_type: str) -> str:
    if article_type not in _BURSTINESS_TARGET_ARTICLE_TYPES:
        return body

    before_lengths = [len(paragraph) for paragraph in _extract_body_paragraphs(body)]
    before_cv = _coefficient_of_variation(before_lengths)
    if len(before_lengths) < 4 or before_cv >= 0.22:
        return body

    blocks = [chunk.strip() for chunk in re.split(r"\n{2,}", str(body or "").strip()) if chunk.strip()]
    rewritten_blocks: List[str] = []
    split_count = 0
    for block in blocks:
        if block.startswith("## "):
            rewritten_blocks.append(block)
            continue
        if re.search(r"(?m)^\s*(?:[-*・]|\d+\.)\s", block) or re.match(r"^https?://", block):
            rewritten_blocks.append(block)
            continue

        sentences = [sentence.strip() for sentence in _SENTENCE_BOUNDARY_RE.split(block) if sentence.strip()]
        if len(sentences) < 3:
            rewritten_blocks.append(block)
            continue

        first_sentence = sentences[0]
        remaining = "".join(sentences[1:]).strip()
        if (
            len(first_sentence) < 22
            or len(first_sentence) > 72
            or len(remaining) < 60
            or _BREATHING_PARAGRAPH_LEAD_RE.match(first_sentence)
        ):
            rewritten_blocks.append(block)
            continue

        rewritten_blocks.extend([first_sentence, remaining])
        split_count += 1

    if split_count < 2:
        return body

    candidate = "\n\n".join(rewritten_blocks).strip()
    after_lengths = [len(paragraph) for paragraph in _extract_body_paragraphs(candidate)]
    after_cv = _coefficient_of_variation(after_lengths)
    if after_cv < before_cv + 0.12:
        return body
    return candidate


def _expand_announcement_anchor_terms(text: str) -> str:
    normalized = str(text or "")
    replacements = (
        (r"(?m)(^|[。！？]\s*)対象は(?=、|管理者|利用者|既存)", r"\1対象者は"),
        (r"対象範囲", "対象者の範囲"),
        (r"(?:作業|更新)当日は、更新後に", "当日の確認事項として、更新後に"),
        (r"確認が必要です。", "確認が必要になります。"),
    )
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized)
    return normalized


def _normalize_announcement_output_body(text: str, contract_dict: Dict[str, Any]) -> str:
    normalized = str(text or "")
    must_cover_items = [
        str(item or "").strip()
        for item in (contract_dict.get("must_cover", []) or [])
        if str(item or "").strip()
    ]
    authoritative_dates: list[str] = []
    route_phrase = ""
    for item in must_cover_items:
        for literal in re.findall(r"\d{4}年\d{1,2}月\d{1,2}日", item):
            if literal and literal not in authoritative_dates:
                authoritative_dates.append(literal)
        if not route_phrase and "公式サイトの専用ページ" in item:
            route_phrase = "公式サイトの専用ページ"

    if len(authoritative_dates) == 1:
        normalized = re.sub(r"\d{4}年\d{1,2}月\d{1,2}日", authoritative_dates[0], normalized)
    if route_phrase:
        normalized = re.sub(
            r"申し込みは(?:当社の)?(?:指定の|専用の)?(?:ウェブ)?フォームから(行(?:っていただきます|えます|います)|受付(?:を開始)?します)",
            f"申し込みは{route_phrase}から\\1",
            normalized,
        )
        normalized = normalized.replace("当社専用ウェブサイトの申込フォーム", f"当社{route_phrase}")
        normalized = normalized.replace("この専用ページ", route_phrase)
    normalized = re.sub(
        r"多くの場合(?=[^。]{0,40}(?:専用ページ|公式|ご確認|お申し込み|お手続き))",
        "",
        normalized,
    )
    normalized = re.sub(
        r"可能性が高く(?=[^。]{0,24}(?:進め|確認|対応|ご利用|お手続き))",
        "",
        normalized,
    )
    return _expand_announcement_anchor_terms(normalized)


def _drop_known_transition_fragments(text: str) -> str:
    normalized = str(text or "")
    for pattern in (
        r"(?:対象と時期を確認したうえで、)?次に利用者への影響を確認してください。",
        r"次に、?対象者と開始時期を確認してください。",
        r"次に移行時の注意点を確認してください。",
        r"次に移行時の注意点を確認する場合も、同じく対象と時期を先に揃えると判断しやすくなります。",
        r"公式情報の確認先はどこか(?:については)?、?[^。]{0,24}(?:見てから対応してください|ご覧ください)。",
        r"(?:その評価軸|最初に決めた判断基準)に沿って(?:見ていく|見れば)。",
        r"逆に、全社展開を前提に比較するなら、前提をそろえたうえで価格と運用負荷を並べ。",
    ):
        normalized = re.sub(pattern, "", normalized)
    return normalized


def _apply_article_type_output_body_normalizers(text: str, article_type: str, contract_dict: Dict[str, Any]) -> str:
    normalized = _soften_company_intro_externalized_self_reference(text, contract_dict)
    normalized = _suppress_repeated_company_subjects(normalized, contract_dict)
    if article_type == "comparative_review":
        normalized = _soften_comparative_opener_and_ranking(normalized)
        normalized = _diversify_comparative_surface(normalized)
    normalized = _reflow_flat_paragraph_cadence(normalized, article_type)
    normalized = _rebalance_company_intro_paragraph_cadence(normalized, contract_dict)
    if article_type == "announcement":
        normalized, _ = apply_minimal_editor_guard(normalized)
    return normalized


def _normalize_output_lines(text: str) -> str:
    normalized_lines: list[str] = []
    for raw_line in str(text or "").splitlines():
        compact_line = re.sub(r"[ \t]{2,}", " ", raw_line).strip()
        if compact_line:
            normalized_lines.append(compact_line)
            continue
        if normalized_lines and normalized_lines[-1] != "":
            normalized_lines.append("")
    return "\n".join(normalized_lines).strip()


def _soften_comparative_opener_and_ranking(text: str) -> str:
    normalized = str(text or "")
    sentence_parts = re.split(r"(?<=[。！？])", normalized)
    rewritten_parts: list[str] = []
    for part in sentence_parts:
        sentence = str(part or "")
        stripped = sentence.strip()
        if "はいずれも" in stripped and "前提にしている" in stripped and "が違います" in stripped:
            match = re.search(r"前提にしている(.+?)が違います", stripped)
            if match:
                suffix = match.group(1).strip()
                sentence = f"比べると、前提にしている{suffix}が違います。"
        rewritten_parts.append(sentence)
    normalized = "".join(rewritten_parts)
    replacements = (
        ("第一候補になりやすい", "候補に入りやすい"),
        ("第一候補です", "候補です"),
        ("第一候補", "有力候補"),
        ("最有力候補", "有力候補"),
        ("本命候補", "候補"),
    )
    for before, after in replacements:
        normalized = normalized.replace(before, after)
    normalized = re.sub(
        r"(?:最も|一番)([^。\n]{0,12}(?:向いて|向きます|向く|合う|適して|おすすめ|選びやす|本命))",
        r"\1",
        normalized,
    )
    return normalized


def _rewrite_compare_sentence_ending(sentence: str) -> tuple[str, str]:
    normalized = str(sentence or "").strip()
    for pattern, replacement, bucket in _COMPARE_ENDING_VARIANTS:
        candidate = pattern.sub(replacement, normalized)
        if candidate != normalized:
            return candidate, bucket
    return normalized, ""


def _comparative_ending_bucket(sentence: str) -> str:
    normalized = str(sentence or "").strip()
    for pattern, _, bucket in _COMPARE_ENDING_VARIANTS:
        if pattern.search(normalized):
            return bucket
    return ""


def _diversify_comparative_surface(text: str) -> str:
    blocks = re.split(r"(\n\s*\n)", str(text or "").strip())
    rewritten_blocks: list[str] = []
    for block in blocks:
        if not block or re.fullmatch(r"\n\s*\n", block):
            rewritten_blocks.append(block)
            continue
        stripped = block.strip()
        if not stripped or stripped.startswith("## "):
            rewritten_blocks.append(block)
            continue
        sentences = [item.strip() for item in _SENTENCE_BOUNDARY_RE.split(stripped) if item.strip()]
        if len(sentences) < 3:
            rewritten_blocks.append(block)
            continue
        repaired: list[str] = []
        previous_bucket = ""
        run_length = 0
        for sentence in sentences:
            bucket = _comparative_ending_bucket(sentence)
            if bucket and bucket == previous_bucket:
                run_length += 1
            else:
                previous_bucket = bucket
                run_length = 1 if bucket else 0
            updated = sentence
            if bucket and run_length >= 3:
                candidate, candidate_bucket = _rewrite_compare_sentence_ending(sentence)
                if candidate != sentence and candidate_bucket:
                    updated = candidate
                    previous_bucket = candidate_bucket
                    run_length = 1
            repaired.append(updated)
        rewritten_blocks.append("".join(repaired).strip())
    return "".join(rewritten_blocks).strip()


def normalize_output_body(body: str, contract: Dict[str, Any] | None) -> str:
    text = str(body or "")
    contract_dict = dict(contract) if isinstance(contract, dict) else {}
    article_type = str(contract_dict.get("article_type") or "")
    normalized = text

    if article_type == "announcement":
        normalized = _normalize_announcement_output_body(normalized, contract_dict)
    normalized = _drop_known_transition_fragments(normalized)
    normalized = _apply_article_type_output_body_normalizers(normalized, article_type, contract_dict)
    return _normalize_output_lines(normalized)


def _looks_prompt_like_topic(text: str) -> bool:
    candidate = _normalize_text(text)
    if not candidate:
        return False
    return bool(
        re.search(
            r"(してください|したい|してほしい|表示してください|まとめてください|投稿する|投稿したい|"
            r"書きたい|書いてください|かいてください|作成してください|生成してください|教えてください)",
            candidate,
        )
    )


def _extract_interview_message(contract: Dict[str, Any] | None) -> str:
    if not isinstance(contract, dict):
        return ""
    answers = contract.get("interview_answers", {}) or {}
    if not isinstance(answers, dict):
        return ""
    for key in ("message", "core_message", "main_message"):
        value = _normalize_text(answers.get(key, ""))
        if value:
            return value
    return ""


def _extract_narrative_axis(contract: Dict[str, Any] | None) -> str:
    if not isinstance(contract, dict):
        return ""
    return _normalize_branding_focus(contract.get("narrative_axis", ""))


def _extract_knowledge_lenses(contract: Dict[str, Any] | None) -> List[str]:
    if not isinstance(contract, dict):
        return []
    raw_values = contract.get("knowledge_lenses", [])
    if isinstance(raw_values, str):
        raw_values = [raw_values]
    if not isinstance(raw_values, list):
        return []
    normalized: List[str] = []
    for item in raw_values:
        value = _normalize_text(item)
        if value and value not in normalized:
            normalized.append(value)
    return normalized[:4]


def _normalize_branding_focus(text: str) -> str:
    candidate = _normalize_text(text)
    if not candidate:
        return ""
    candidate = re.sub(r"(?:からの視点|の視点)$", "", candidate).strip(" 　、。")
    candidate = re.sub(r"(?:で整理する|を前面に出す|を重視する)$", "", candidate).strip(" 　、。")
    if candidate in _GENERIC_BRANDING_TERMS:
        return ""
    return candidate[:40]


def _is_generic_company_intro_seed(text: str) -> bool:
    candidate = _normalize_text(text)
    if not candidate:
        return False
    return bool(_GENERIC_COMPANY_INTRO_SEED_RE.search(candidate))


def _compact_knowledge_lens_label(text: str) -> str:
    candidate = _normalize_text(text)
    if not candidate:
        return ""
    if re.search(r"(法務|コンプライアンス|リーガル)", candidate, re.I):
        return "法務・コンプライアンスの知見"
    if re.search(r"(ブランド|ブランディング|広報)", candidate, re.I):
        return "企業ブランディング担当の知見"
    if re.search(r"(編集|記者|ジャーナリスト)", candidate, re.I):
        return "編集の知見"
    candidate = re.sub(r"を混ぜる$", "", candidate).strip(" 　、。")
    return candidate[:28]


def _branding_focus_clause(text: str) -> str:
    candidate = _normalize_branding_focus(text)
    if not candidate:
        return ""
    if re.search(r"(視点|軸)$", candidate):
        return f"{candidate}で"
    if re.search(r"(する|伝える|示す|整理する|考える)$", candidate):
        return f"{candidate}視点を軸に"
    return f"{candidate}を軸に"


def _compact_audience_profile(text: str) -> str:
    candidate = _normalize_text(text)
    if not candidate:
        return ""
    preferred_labels = (
        "経営者",
        "意思決定者",
        "実務担当者",
        "導入担当者",
        "比較検討中の読者",
        "導入検討者",
        "既存顧客",
        "既存利用者",
        "一般読者",
        "読者",
        "利用者",
        "ユーザー",
        "顧客",
    )
    for label in preferred_labels:
        if label in candidate:
            return label
    return candidate[:20]


def _compact_industry_title_label(text: str) -> str:
    candidate = _normalize_text(text)
    if not candidate:
        return ""
    replacements = (
        ("構成とサイズ", "構成"),
        ("主要な数値", "数値"),
        ("使う環境", "利用環境"),
        ("意思決定の示唆", "判断材料"),
    )
    for before, after in replacements:
        candidate = candidate.replace(before, after)
    candidate = re.sub(r"(?:を先に見ておく必要があります|を見ておく必要があります)$", "", candidate).strip(" 　、。")
    candidate = re.sub(r"(?:が運用を左右します|は利用者だけでなく情報の性質で決めます)$", "", candidate).strip(" 　、。")
    candidate = re.sub(r"(?:に求められるのは段階設計です)$", "の段階設計", candidate).strip(" 　、。")
    if len(candidate) > 18:
        candidate = candidate[:18].rstrip(" 　、。")
    return candidate


def _extract_headings(body: str) -> List[str]:
    headings: List[str] = []
    for match in re.findall(r"^##\s+(.+)$", str(body or ""), re.MULTILINE):
        heading = str(match or "").strip()
        if not heading:
            continue
        if heading == "目次":
            continue
        headings.append(heading)
    return headings


def _extract_body_paragraphs(body: str) -> List[str]:
    paragraphs: List[str] = []
    current: List[str] = []
    for raw_line in str(body or "").splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        if line.startswith("## "):
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current).strip())
    return [paragraph for paragraph in paragraphs if paragraph]


def _clean_generated_title(value: Any) -> str:
    return re.sub(r"^#+\s*", "", str(value or "")).strip(" 「」『』")


def _clean_generated_lead(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\r", " ").replace("\n", " ")).strip()


def _topic_hint_for_tone_shaping(topic: str, contract: Dict[str, Any] | None) -> str:
    contract_dict = dict(contract or {})
    candidate = _normalize_text(
        contract_dict.get("topic_statement")
        or topic
        or contract_dict.get("core_message")
        or ""
    )
    if not candidate:
        candidate = _normalize_text(
            contract_dict.get("core_message")
            or topic
            or ""
        )
    candidate = re.split(r"[。！？!?]", candidate, maxsplit=1)[0].strip(" 、,")
    return candidate[:96]


def _shape_explanatory_title_by_tone(title: str, tone_profile: str) -> str:
    normalized = _clean_generated_title(title)
    if not normalized:
        return normalized
    legacy_seed = "運用定着の見方をそろえるべき理由から考える実務の見方"
    if legacy_seed in normalized:
        if tone_profile == "warm":
            return normalized.replace(
                legacy_seed,
                "運用定着の見方をそろえて迷いを減らす実務の見方",
            ) or normalized
        if tone_profile == "formal":
            updated = normalized.replace(
                legacy_seed,
                "運用定着の見方をそろえる判断軸を整理する",
            )
            updated = updated.replace("まず", "")
            return re.sub(r"、{2,}", "、", updated).strip(" 、,") or normalized
    if normalized == "比較表の前に置くべき前提から考える実務の見方":
        if tone_profile == "warm":
            return "比較表の前に置くべき前提をそろえて迷いを減らす実務の見方"
        if tone_profile == "calm":
            return "比較表の前に置くべき前提を整理して考える実務の見方"
        if tone_profile == "formal":
            return "比較表の前に置くべき前提と判断軸を整理する"
    generic_suffix = "から考える実務の見方"
    if normalized.endswith(generic_suffix):
        stem = normalized[: -len(generic_suffix)].rstrip(" 、,")
        if stem:
            if tone_profile == "warm":
                return f"{stem}をそろえて迷いを減らす実務の見方"
            if tone_profile == "calm":
                return f"{stem}を整理して考える実務の見方"
            if tone_profile == "formal":
                return f"{stem}と判断軸を整理する"
    if tone_profile == "warm":
        return normalized
    if tone_profile == "formal":
        updated = normalized.replace("まず", "")
        return re.sub(r"、{2,}", "、", updated).strip(" 、,") or normalized
    return normalized


def _shape_explanatory_lead_by_tone(topic: str, tone_profile: str, contract: Dict[str, Any] | None) -> str:
    return ""


def _apply_explanatory_tone_opening_shape(
    *,
    topic: str,
    article_type: str,
    title: str,
    lead: str,
    contract: Dict[str, Any] | None,
) -> tuple[str, str]:
    contract_dict = dict(contract or {})
    tone_profile = _normalize_text(contract_dict.get("tone_profile") or "auto").lower()
    if article_type != "explanatory_article" or tone_profile not in {"warm", "calm", "formal"}:
        return title, lead
    shaped_title = _shape_explanatory_title_by_tone(title, tone_profile)
    shaped_lead = _shape_explanatory_lead_by_tone(topic, tone_profile, contract_dict) or lead
    return shaped_title or title, shaped_lead or lead


def _shape_daily_story_title(title: str) -> str:
    normalized = _clean_generated_title(title)
    suffix = "から見えたこと"
    if not normalized.endswith(suffix):
        return normalized
    stem = normalized[: -len(suffix)].strip(" 、,")
    if not stem:
        return normalized
    rewritten = re.sub(r"^(?P<context>.+?)に、(?P<subject>.+?)があった$", r"\g<context>にあった、\g<subject>", stem)
    if rewritten == stem:
        rewritten = re.sub(r"^(?P<context>.+?)に、?(?P<subject>.+?)があった$", r"\g<context>にあった、\g<subject>", stem)
    cleaned = re.sub(r"でした$", "", rewritten).strip(" 、,")
    cleaned = re.sub(r"、{2,}", "、", cleaned)
    return cleaned or normalized


def _apply_daily_story_title_shape(*, article_type: str, title: str) -> str:
    if article_type != "daily_story":
        return title
    shaped = _shape_daily_story_title(title)
    return shaped or title


def _is_title_prompt_echo(title: str, topic: str) -> bool:
    """Detect titles that are truncated copies of the prompt/topic text."""
    norm_title = _normalize_text(title)
    norm_topic = _normalize_text(topic)
    if not norm_title or not norm_topic:
        return False
    common = len(os.path.commonprefix([norm_title, norm_topic]))
    if common >= 20:
        return True
    inner = norm_title.rstrip("。！？")
    if re.search(r"[。！？]", inner):
        return True
    return False


def _prefer_generated_title(article_type: str, candidate: Any, *, topic: str = "") -> str:
    if article_type not in _PREFER_GENERATED_HEAD_ARTICLE_TYPES:
        return ""
    normalized = _clean_generated_title(candidate)
    if not normalized or normalized == "互換生成タイトル":
        return ""
    if _looks_prompt_like_topic(normalized):
        return ""
    if article_type == "explanatory_article":
        return normalized[:56]
    if article_type == "branding" and _is_generic_company_intro_seed(normalized):
        return ""
    if _is_title_prompt_echo(normalized, topic):
        return ""
    return normalized[:56]


def _prefer_generated_lead(article_type: str, candidate: Any, body: str) -> str:
    if article_type not in _PREFER_GENERATED_HEAD_ARTICLE_TYPES:
        return ""
    normalized = _clean_generated_lead(candidate)
    if not normalized or _LEAD_META_PATTERN.search(normalized) or _looks_prompt_like_topic(normalized):
        return ""
    first_paragraph = _clean_generated_lead((_extract_body_paragraphs(body) or [""])[0])
    if article_type == "announcement" and first_paragraph:
        candidate_first_sentence = re.split(r"(?<=[。！？])\s*", normalized, maxsplit=1)[0]
        body_first_sentence = re.split(r"(?<=[。！？])\s*", first_paragraph, maxsplit=1)[0]
        normalized_candidate_sentence = re.sub(r"\s+", "", candidate_first_sentence)
        normalized_body_sentence = re.sub(r"\s+", "", body_first_sentence)
        if len(os.path.commonprefix([normalized_candidate_sentence, normalized_body_sentence])) >= 12:
            return ""
    if first_paragraph and normalized == first_paragraph:
        return ""
    return normalized


def _extract_source_grounding_items(contract: Dict[str, Any] | None) -> List[Dict[str, str]]:
    if not isinstance(contract, dict):
        return []
    items = contract.get("source_grounding_items", []) or []
    if not isinstance(items, list):
        return []
    normalized: List[Dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        fact_text = _normalize_text(item.get("fact_text", ""))
        if not fact_text:
            continue
        normalized.append(
            {
                "bucket": _normalize_text(item.get("bucket", "")),
                "fact_text": fact_text,
                "source_title": _normalize_text(item.get("source_title", "")),
            }
        )
    return normalized[:6]


_COMPANY_NAME_PROCESS_FRAGMENT_RE = re.compile(
    r"(?:導入の流れ|お問い合わせ|お問合せ|お電話|メールフォーム|ヒアリング|見積|発注|納品|ご契約|相談内容|作業範囲|依頼範囲|お気軽)"
)
_COMPANY_NAME_UNSAFE_PROCESS_BUCKETS = {
    "operating_process_steps",
    "運用工程",
}


def _looks_like_process_fragment_for_company_name(text: str, bucket: str = "") -> bool:
    normalized = _normalize_text(text)
    if not normalized:
        return False
    if str(bucket or "").strip() in _COMPANY_NAME_UNSAFE_PROCESS_BUCKETS:
        return True
    return bool(_COMPANY_NAME_PROCESS_FRAGMENT_RE.search(normalized))


def _extract_company_name(source_items: List[Dict[str, str]]) -> str:
    for item in source_items:
        fact_text = str(item.get("fact_text") or "")
        if _looks_like_process_fragment_for_company_name(fact_text, str(item.get("bucket") or "")):
            continue
        match = re.match(r"^(.{2,24}?)(?:株式会社)?は", fact_text)
        if match:
            company_name = match.group(1).strip(" 　、。")
            company_name = re.sub(r"^(?:私たち|弊社|当社)", "", company_name).strip(" 　、。")
            if _looks_like_process_fragment_for_company_name(company_name):
                continue
            return company_name
    return ""


def _is_company_introduction_contract(contract: Dict[str, Any] | None) -> bool:
    if not isinstance(contract, dict):
        return False
    return str(contract.get("semantic_article_key") or "").strip().lower() == "company_introduction"


_COMPANY_INTRO_SOURCE_CONTRACT_KEYS = (
    "company_introduction_source_contract",
    "company_intro_source_contract",
    "_company_introduction_source_contract",
    "_company_intro_source_contract",
)
_COMPANY_INTRO_OPERATIONAL_SLOT_KEYS = (
    "current_business",
    "customer_situation_or_entry_point",
    "support_scope_boundary",
    "operating_process_steps",
    "pre_contact_decision",
)
_COMPANY_INTRO_CURRENT_SOURCE_BUCKETS = {
    "overview",
    "strength",
    "current_business",
    "support_scope_boundary",
    "operating_process_steps",
    "pre_contact_decision",
    "現在事業",
    "支援範囲",
    "運用工程",
    "相談前",
}
_COMPANY_INTRO_HISTORY_FIRST_RE = re.compile(r"(?:歩み|沿革|歴史|創業|順にたど)")
_COMPANY_INTRO_OPERATIONAL_OPENING_RE = re.compile(
    r"(?:データ|入力|スキャニング|分析|支援|相談|問い合わせ|ヒアリング|前処理|後処理|進め方|支援範囲|対応範囲|事業内容)"
)
_COMPANY_INTRO_GENERIC_FOCUS_RE = re.compile(
    r"^(?:何をしている会社か|会社の輪郭(?:を.*)?|どんな事業を担っているか)$"
)


def _extract_company_intro_source_contract(contract: Dict[str, Any] | None) -> Dict[str, str]:
    if not isinstance(contract, dict):
        return {}
    for key in _COMPANY_INTRO_SOURCE_CONTRACT_KEYS:
        value = contract.get(key)
        if not isinstance(value, dict):
            continue
        if isinstance(value.get("slots"), dict):
            value = value.get("slots") or {}
        normalized = {
            str(slot_key): _normalize_text(slot_value)
            for slot_key, slot_value in value.items()
            if _normalize_text(slot_value)
        }
        if normalized:
            return normalized
    return {}


def _company_intro_slot_presence_telemetry(contract: Dict[str, Any] | None) -> Dict[str, Dict[str, Any]]:
    source_contract = _extract_company_intro_source_contract(contract)
    return {
        key: {
            "present": bool(source_contract.get(key)),
            "excerpt": str(source_contract.get(key) or "")[:80],
        }
        for key in _COMPANY_INTRO_OPERATIONAL_SLOT_KEYS
    }


def _company_intro_has_operational_source(
    contract: Dict[str, Any] | None,
    source_items: List[Dict[str, str]] | None = None,
) -> bool:
    if not _is_company_introduction_contract(contract):
        return False
    source_contract = _extract_company_intro_source_contract(contract)
    if any(source_contract.get(key) for key in _COMPANY_INTRO_OPERATIONAL_SLOT_KEYS):
        return True
    items = source_items if source_items is not None else _extract_source_grounding_items(contract)
    return any(
        str(item.get("bucket") or "").strip() in _COMPANY_INTRO_CURRENT_SOURCE_BUCKETS
        for item in items
    )


def _company_intro_has_process_or_contact_slot(contract: Dict[str, Any] | None) -> bool:
    source_contract = _extract_company_intro_source_contract(contract)
    return any(
        source_contract.get(key)
        for key in ("support_scope_boundary", "operating_process_steps", "pre_contact_decision")
    )


def _company_intro_history_first_drift(text: str) -> bool:
    normalized = _normalize_text(text)
    if not normalized or not _COMPANY_INTRO_HISTORY_FIRST_RE.search(normalized):
        return False
    return not bool(_COMPANY_INTRO_OPERATIONAL_OPENING_RE.search(normalized))


def _company_intro_business_lead_phrase(contract: Dict[str, Any] | None) -> str:
    source_contract = _extract_company_intro_source_contract(contract)
    current_business = source_contract.get("current_business", "")
    labels: List[str] = []
    for token, label in (
        ("データ入力", "データ入力"),
        ("スキャニング", "スキャニング"),
        ("分析", "分析"),
    ):
        if token in current_business and label not in labels:
            labels.append(label)
    if labels:
        return "・".join(labels)
    return "事業内容"


def _soften_company_intro_externalized_self_reference(text: str, contract: Dict[str, Any] | None) -> str:
    if not _is_company_introduction_contract(contract):
        return text
    source_items = _extract_source_grounding_items(contract)
    company_name = _extract_company_name(source_items)
    if not company_name:
        return text

    normalized = str(text or "")
    escaped_company_name = re.escape(company_name)
    targeted_patterns = (
        (
            rf"{escaped_company_name}のような外部パートナーを検討する際は、",
            "外部パートナーを検討する際は、",
        ),
        (
            rf"{escaped_company_name}が選ばれている理由のひとつは、",
            "選ばれている理由のひとつは、",
        ),
        (
            rf"{escaped_company_name}の紹介で見えてくるのは、",
            "大切にしているのは、",
        ),
        (
            rf"{escaped_company_name}は、その入口で相談しやすい存在として機能しています。",
            "相談しやすい入口であることを大切にしています。",
        ),
    )
    for pattern, replacement in targeted_patterns:
        normalized = re.sub(pattern, replacement, normalized)
    return normalized


def _split_markdown_sections(body: str) -> List[tuple[str, str]]:
    sections: List[tuple[str, str]] = []
    current_heading = ""
    current_lines: List[str] = []
    for raw_line in str(body or "").splitlines():
        matched = re.match(r"^##\s+(.+)$", raw_line.strip())
        if matched:
            if current_heading:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = matched.group(1).strip()
            current_lines = []
            continue
        if current_heading:
            current_lines.append(raw_line)
    if current_heading:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    return sections


def _join_markdown_sections(sections: List[tuple[str, str]]) -> str:
    chunks: List[str] = []
    for heading, section_body in sections:
        clean_heading = str(heading or "").strip()
        clean_body = str(section_body or "").strip()
        if not clean_heading or not clean_body:
            continue
        chunks.append(f"## {clean_heading}\n\n{clean_body}")
    return "\n\n".join(chunks).strip()


def _paragraph_sentence_count(text: str) -> int:
    return len([sentence for sentence in _SENTENCE_BOUNDARY_RE.split(str(text or "").strip()) if sentence.strip()])


def _paragraph_needs_company_reanchor(previous_paragraph: str, company_name: str) -> bool:
    prior = str(previous_paragraph or "").strip()
    if not prior or company_name in prior:
        return False
    return any(marker in prior for marker in _COMPANY_REANCHOR_CONTEXT_MARKERS)


def _suppress_repeated_company_subjects(body: str, contract: Dict[str, Any] | None) -> str:
    if not _is_company_introduction_contract(contract):
        return body
    source_items = _extract_source_grounding_items(contract)
    company_name = _extract_company_name(source_items)
    if not company_name:
        return body

    escaped_company_name = re.escape(company_name)
    leading_patterns = (
        (re.compile(rf"^{escaped_company_name}の強みは、"), "強みは、"),
        (re.compile(rf"^{escaped_company_name}が導入初期に重視しているのは、"), "導入初期に重視しているのは、"),
        (re.compile(rf"^{escaped_company_name}が大切にしているのは、"), "大切にしているのは、"),
        (re.compile(rf"^{escaped_company_name}では、"), ""),
        (re.compile(rf"^{escaped_company_name}は、その"), "その"),
        (re.compile(rf"^{escaped_company_name}は、"), ""),
        (re.compile(rf"^{escaped_company_name}が"), ""),
    )

    rewritten_sections: List[tuple[str, str]] = []
    for heading, section_body in _split_markdown_sections(body):
        paragraphs = [chunk.strip() for chunk in re.split(r"\n{2,}", section_body) if chunk.strip()]
        rewritten_paragraphs: List[str] = []
        explicit_company_starts = 0
        reanchor_budget_used = 0
        previous_paragraph = ""
        for paragraph in paragraphs:
            sentences = [sentence.strip() for sentence in _SENTENCE_BOUNDARY_RE.split(paragraph) if sentence.strip()]
            rewritten_sentences: List[str] = []
            allow_reanchor = (
                reanchor_budget_used < 1
                and _paragraph_needs_company_reanchor(previous_paragraph, company_name)
            )
            for sentence_index, sentence in enumerate(sentences):
                updated = sentence
                if updated.startswith(company_name):
                    explicit_company_starts += 1
                    preserve_explicit_subject = explicit_company_starts == 1 or (
                        allow_reanchor and sentence_index == 0
                    )
                    if preserve_explicit_subject and explicit_company_starts > 1:
                        reanchor_budget_used += 1
                    if not preserve_explicit_subject:
                        for pattern, replacement in leading_patterns:
                            candidate = pattern.sub(replacement, updated, count=1)
                            if candidate != updated:
                                updated = candidate.strip()
                                break
                rewritten_sentences.append(updated)
            rewritten_paragraph = "".join(rewritten_sentences).strip()
            rewritten_paragraphs.append(rewritten_paragraph)
            previous_paragraph = paragraph
        rewritten_sections.append((heading, "\n\n".join(chunk for chunk in rewritten_paragraphs if chunk).strip()))
    return _join_markdown_sections(rewritten_sections) or str(body or "").strip()


def _rebalance_company_intro_paragraph_cadence(body: str, contract: Dict[str, Any] | None) -> str:
    if not _is_company_introduction_contract(contract):
        return body

    sections = _split_markdown_sections(body)
    if len(sections) < 3:
        return body

    rewritten_sections: List[tuple[str, str]] = []
    merged_count = 0
    for heading, section_body in sections:
        paragraphs = [chunk.strip() for chunk in re.split(r"\n{2,}", section_body) if chunk.strip()]
        if len(paragraphs) < 3:
            rewritten_sections.append((heading, section_body))
            continue

        rebuilt: List[str] = []
        index = 0
        while index < len(paragraphs):
            current = paragraphs[index]
            next_paragraph = paragraphs[index + 1] if index + 1 < len(paragraphs) else ""
            current_sentences = _paragraph_sentence_count(current)
            next_sentences = _paragraph_sentence_count(next_paragraph)
            combined_length = len(_normalize_text(current + next_paragraph))
            if (
                next_paragraph
                and current_sentences <= 2
                and next_sentences <= 3
                and combined_length <= 270
                and merged_count < 4
            ):
                rebuilt.append(f"{current}\n{next_paragraph}".strip())
                merged_count += 1
                index += 2
                continue
            rebuilt.append(current)
            index += 1
        rewritten_sections.append((heading, "\n\n".join(rebuilt).strip()))

    if merged_count < 2:
        return body
    return _join_markdown_sections(rewritten_sections) or str(body or "").strip()


def _nounize_focus(text: str) -> str:
    value = _normalize_text(text)
    if not value:
        return ""
    value = re.sub(
        r"(?:表示してください|まとめてください|作成してください|生成してください|書いてください|かいてください|教えてください)$",
        "",
        value,
    ).strip(" 　、。")
    replacements = (
        (r"を紹介する$", ""),
        (r"を整理する$", ""),
        (r"を伝える$", ""),
        (r"を説明する$", ""),
        (r"を深掘りする$", ""),
        (r"を見直す$", ""),
    )
    for pattern, repl in replacements:
        next_value = re.sub(pattern, repl, value)
        if next_value != value:
            value = next_value
            break
    value = re.sub(r"^(?:自社の全体像|会社として初めてのnote投稿で、自社)", "自社", value)
    value = re.sub(r"から価値$", "から見る価値", value)
    value = value.strip(" 　、。")
    return value[:40]


def _extract_focus_bundle(contract: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(contract, dict):
        return {}
    value = contract.get("focus_bundle", {}) or {}
    return dict(value) if isinstance(value, dict) else {}


def _extract_must_cover_labels(contract: Dict[str, Any] | None, *, limit: int = 3) -> List[str]:
    if not isinstance(contract, dict):
        return []
    raw = contract.get("must_cover", []) or []
    if not isinstance(raw, list):
        return []
    items: List[str] = []
    for item in raw:
        normalized = _nounize_focus(str(item or "")) or _normalize_text(item)
        if not normalized or normalized in items:
            continue
        items.append(normalized[:18])
        if len(items) >= limit:
            break
    return items


def _case_study_compact_label(text: str) -> str:
    value = _nounize_focus(text) or _normalize_text(text)
    if not value:
        return ""
    value = value.replace("改善の前後差", "改善前後の差")
    value = value.replace("改善の前後", "改善前後")
    value = value.replace("前後差", "前後の差")
    for pattern in (
        r"までを?共有(?:する)?$",
        r"と条件を具体的に共有(?:する)?$",
        r"を具体的に共有(?:する)?$",
        r"を共有(?:する)?$",
        r"を整理(?:する)?$",
        r"を説明(?:する)?$",
    ):
        value = re.sub(pattern, "", value).strip(" 　、。")
    if "だけでなく" in value:
        primary, trailing = value.split("だけでなく", 1)
        if primary.strip(" 　、。") and re.search(r"(条件|再現|結果|変化|進め方|前後)", trailing):
            value = primary.strip(" 　、。")
    if "と" in value:
        parts = [part.strip(" 　、。") for part in value.split("と") if part.strip()]
        if len(parts) >= 2 and re.search(r"(条件|再現|結果|変化|進め方|前後|次)", parts[1]):
            value = parts[0]
        elif len(value) > 16 and parts:
            value = parts[0]
    return value[:16]


def _case_study_lead_labels(contract: Dict[str, Any] | None, *, limit: int = 3) -> List[str]:
    if not isinstance(contract, dict):
        return []
    raw = contract.get("must_cover", []) or []
    if not isinstance(raw, list):
        return []
    labels: List[str] = []
    for item in raw:
        normalized = _case_study_compact_label(str(item or ""))
        if not normalized or normalized in labels:
            continue
        labels.append(normalized)
        if len(labels) >= limit:
            break
    return labels


def _case_study_lead_focus(contract: Dict[str, Any] | None) -> str:
    if not isinstance(contract, dict):
        return ""
    for raw in (
        contract.get("core_message", ""),
        _extract_interview_message(contract),
    ):
        normalized = _case_study_compact_label(str(raw or ""))
        if normalized and not _looks_prompt_like_topic(normalized):
            return normalized

    case_labels = _case_study_lead_labels(contract, limit=4)
    preferred = next(
        (
            label
            for label in case_labels
            if re.search(r"(導入前|課題|迷い|つまずき|原因|負荷|遅延|背景)", label)
        ),
        "",
    )
    if preferred:
        return preferred
    if case_labels:
        return case_labels[0]
    return ""


def _case_study_lead_progression(body: str, contract: Dict[str, Any] | None) -> str:
    signals = _extract_headings(body) + _case_study_lead_labels(contract, limit=4)
    has_change = any(re.search(r"(進め方|組み替え|見直し|対応|立て直し|改善)", item) for item in signals)
    has_result = any(re.search(r"(結果|変わった|変化|前後|差)", item) for item in signals)
    has_condition = any(re.search(r"(条件|再現|前提|防ぐ|防止)", item) for item in signals)

    if has_change and has_result and has_condition:
        return "進め方を組み替えた後の変化と再現条件までを順に追います。"
    if has_result and has_condition:
        return "見直し後の変化と再現条件までを順に追います。"
    if has_change and has_result:
        return "進め方を組み替えた後の変化までを順に追います。"
    if has_change and has_condition:
        return "進め方を組み替えた流れと再現条件までを順に追います。"
    if has_condition:
        return "変化が出た条件までを順に追います。"
    if has_change:
        return "進め方を組み替えた流れまでを順に追います。"
    return "前後の変化と再現条件までを順に追います。"


def _lead_must_cover_labels(contract: Dict[str, Any] | None, *, article_type: str = "", limit: int = 4) -> List[str]:
    items = _extract_must_cover_labels(contract, limit=limit)
    if article_type == "comparative_review":
        filtered = [item for item in items if not re.search(r"文脈を踏まえる$", item)]
        if filtered:
            return filtered[:limit]
    return items[:limit]


def _compress_branding_title_seed(seed: str) -> str:
    value = _nounize_focus(seed)
    if not value:
        return ""
    if _is_generic_company_intro_seed(value):
        return ""
    if "導入初期" in value and "運用の迷いを減らす価値" in value:
        return "導入初期の運用の迷いを減らす価値"
    if len(value) > 28 and "より" in value:
        tail = value.split("より", 1)[1].strip(" 　、。")
        if "導入初期" in value:
            return f"導入初期の{tail}"[:28]
        return tail[:28]
    if len(value) > 28 and "価値" in value:
        match = re.search(r"(.{0,18}?価値)", value)
        if match:
            return match.group(1).strip(" 　、。")
    return value[:28]


def _branding_title_from_body_and_sources(topic: str, body: str, contract: Dict[str, Any] | None) -> str:
    focus_bundle = _extract_focus_bundle(contract)
    source_items = _extract_source_grounding_items(contract)
    company_name = _extract_company_name(source_items)
    company_intro = _is_company_introduction_contract(contract)
    headings = _extract_headings(body)
    focus_seed = _compress_branding_title_seed(str(focus_bundle.get("main_focus") or ""))
    if not focus_seed:
        focus_seed = _compress_branding_title_seed(_branding_title_seed(topic, body, contract))
    operational_company_intro = bool(
        company_intro and _company_intro_has_operational_source(contract, source_items)
    )
    if operational_company_intro and (
        _company_intro_history_first_drift(focus_seed)
        or bool(_COMPANY_INTRO_GENERIC_FOCUS_RE.match(focus_seed))
    ):
        focus_seed = ""
    if focus_seed.startswith("自社の"):
        focus_seed = focus_seed.replace("自社の", "", 1)
    if focus_seed in {"自社", "会社"}:
        focus_seed = ""
    if company_name:
        has_overview = any(str(item.get("bucket") or "") == "overview" for item in source_items)
        has_history = any(str(item.get("bucket") or "") == "history" for item in source_items)
        if focus_seed:
            if (
                focus_seed in {"会社の輪郭", "会社の輪郭を最初に置く", "会社の輪郭をあらためて結ぶ"}
                and has_overview
                and len(source_items) >= 2
            ):
                return f"{company_name}の事業内容と強み"[:56]
            candidate = f"{company_name}の{focus_seed}"
            return candidate[:56]
        if company_intro and _company_intro_has_operational_source(contract, source_items):
            if has_overview and len(source_items) >= 2:
                return f"{company_name}の事業内容と強み"[:56]
            if has_overview:
                return f"{company_name}の事業内容"[:56]
            return f"{company_name}の事業内容と進め方"[:56]
        if has_history:
            return f"{company_name}の事業と歩み"[:56]
        if has_overview and len(source_items) >= 2:
            return f"{company_name}の事業内容と強み"[:56]
        if has_overview:
            return f"{company_name}の事業内容"[:56]
        if headings:
            return f"{company_name}の{_normalize_text(headings[0])}"[:56]
    if focus_seed:
        return focus_seed[:56]
    if headings:
        return _normalize_text(headings[0])[:56]
    return _normalize_text(topic)[:56]


def _take_lead_sentences(text: str, *, max_sentences: int = 2, max_chars: int = 96) -> str:
    sentences = [segment.strip() for segment in re.split(r"(?<=[。！？])", str(text or "")) if segment.strip()]
    collected: List[str] = []
    total = 0
    for sentence in sentences:
        if _LEAD_META_PATTERN.search(sentence):
            continue
        if _looks_prompt_like_topic(sentence):
            continue
        collected.append(sentence)
        total += len(sentence)
        if len(collected) >= max_sentences or total >= max_chars:
            break
    return "".join(collected).strip()


def _build_natural_branding_lead_with_reason(
    topic: str,
    body: str,
    contract: Dict[str, Any] | None,
) -> Tuple[str, str]:
    paragraphs = _extract_body_paragraphs(body)
    first_paragraph = paragraphs[0] if paragraphs else ""
    source_items = _extract_source_grounding_items(contract)
    company_name = _extract_company_name(source_items)
    company_intro = _is_company_introduction_contract(contract)
    focus_bundle = _extract_focus_bundle(contract)
    focus_seed = _nounize_focus(
        str(focus_bundle.get("main_focus") or "")
        or str((contract or {}).get("topic_statement") or "")
        or str((contract or {}).get("narrative_axis") or "")
        or _extract_interview_message(contract)
    )
    overview_fact = next((item["fact_text"] for item in source_items if str(item.get("bucket") or "") == "overview"), "")
    history_fact = next((item["fact_text"] for item in source_items if str(item.get("bucket") or "") == "history"), "")

    if company_intro and company_name and _company_intro_has_operational_source(contract, source_items):
        if _company_intro_has_process_or_contact_slot(contract):
            return (
                f"{_company_intro_business_lead_phrase(contract)}の支援範囲と、相談前に確認したい進め方を先に整理します。",
                "company_intro_source_contract_operational_lead",
            )
        if overview_fact:
            return "事業内容と強みが見える順で整理します。", "company_intro_current_business_lead"
    if company_intro and company_name and history_fact:
        return "どんな事業を続け、どんな歩みを重ねてきたのかを、本文では順にたどります。", "company_intro_history_lead"
    if company_intro and company_name and overview_fact:
        return "事業内容と強みが見える順で整理します。", "company_intro_overview_lead"
    if company_name and history_fact:
        return f"{company_name}が続けてきた事業と歩みを、本文では順にたどります。", "branding_history_lead"
    if company_name and overview_fact:
        return f"{company_name}の事業内容と強みが見える順で整理します。", "branding_overview_lead"
    lead_from_body = _take_lead_sentences(first_paragraph)
    if lead_from_body and len(lead_from_body) >= 12 and lead_from_body not in {"本文です。", "本文です"}:
        return lead_from_body, "body_first_paragraph_lead"
    if focus_seed:
        return f"{focus_seed}について、事業の中身と背景がつながる順で整理します。", "focus_seed_lead"
    return (
        f"{_branding_title_from_body_and_sources(topic, body, contract)}を、本文の流れに沿ってたどります。",
        "title_seed_lead",
    )


def _build_natural_branding_lead(topic: str, body: str, contract: Dict[str, Any] | None) -> str:
    lead, _reason = _build_natural_branding_lead_with_reason(topic, body, contract)
    return lead


def _branding_title_seed(topic: str, body: str, contract: Dict[str, Any] | None) -> str:
    topic_statement = _normalize_branding_focus((contract or {}).get("topic_statement", ""))
    if _looks_prompt_like_topic(topic_statement) or _is_generic_company_intro_seed(topic_statement):
        topic_statement = ""
    narrative_axis = _extract_narrative_axis(contract)
    if _looks_prompt_like_topic(narrative_axis):
        narrative_axis = ""
    message = _normalize_branding_focus(_extract_interview_message(contract))
    if _looks_prompt_like_topic(message):
        message = ""
    headings = _extract_headings(body)
    first_heading = _normalize_branding_focus(headings[0] if headings else "")
    raw_topic = _normalize_text(topic)
    candidates = [topic_statement, narrative_axis, message, first_heading]
    if raw_topic and not _looks_prompt_like_topic(raw_topic) and not _is_generic_company_intro_seed(re.split(r"[。!?！？]", raw_topic, maxsplit=1)[0]):
        candidates.append(raw_topic[:40])
    for candidate in candidates:
        if candidate:
            return candidate
    return raw_topic[:40]


def _case_study_title_seed(topic: str, body: str = "", contract: Dict[str, Any] | None = None) -> str:
    headings = _extract_headings(body)
    if headings:
        return f"{_normalize_text(headings[0])}から考える事例"[:40]
    must_cover = _case_study_lead_labels(contract)
    if len(must_cover) >= 2:
        return f"{must_cover[0]}から{must_cover[1]}までを追った事例"[:40]
    if must_cover:
        return f"{must_cover[0]}から考える事例"[:40]
    base = str(topic or "").strip()
    if not base:
        return "課題と進め方を整理した事例"
    first_sentence = re.split(r"[。!?！？]", base, maxsplit=1)[0].strip()
    if first_sentence and not _looks_prompt_like_topic(first_sentence):
        return first_sentence
    return "課題と進め方を整理した事例"


def _comparative_review_title_seed(topic: str, body: str = "", contract: Dict[str, Any] | None = None) -> str:
    must_cover = _extract_must_cover_labels(contract, limit=3)
    if len(must_cover) >= 2:
        return f"{must_cover[0]}と{must_cover[1]}で見る選定基準"[:40]
    headings = _extract_headings(body)
    if headings:
        first_heading = _normalize_text(headings[0])
        if first_heading.endswith("をそろえる"):
            first_heading = first_heading[:-5]
        elif first_heading.endswith("を先に決める"):
            first_heading = first_heading[:-7]
        if first_heading:
            return f"{first_heading}で見る比較ポイント"[:40]
    base = str(topic or "").strip()
    if base and not _looks_prompt_like_topic(base):
        first_sentence = re.split(r"[。!?！？]", base, maxsplit=1)[0].strip()
        if first_sentence:
            return first_sentence[:40]
    return "比較条件と選定基準の見方"


def _announcement_title_seed(topic: str) -> str:
    base = str(topic or "").strip()
    if not base:
        return ""
    first_sentence = re.split(r"[。!?！？]", base, maxsplit=1)[0].strip()
    if first_sentence:
        return first_sentence
    return base


def _compact_explanatory_heading_seed(heading: str) -> str:
    normalized = _normalize_text(heading)
    if not normalized:
        return ""
    match = re.match(r"(.+?)では[、,]?(?:まず)?(.+?)が求められる$", normalized)
    if match:
        context = match.group(1).strip(" 　、。")
        subject = match.group(2).strip(" 　、。")
        if context and subject:
            return f"{context}で求められる{subject}"[:24]
    return normalized[:24]


def _explanatory_title_seed(
    topic: str,
    body: str = "",
    contract: Dict[str, Any] | None = None,
    *,
    allow_generic_fallback: bool = True,
) -> str:
    headings = _extract_headings(body)
    must_cover = _lead_must_cover_labels(contract, article_type="explanatory_article")
    if headings:
        heading_seed = _compact_explanatory_heading_seed(headings[0])
        if heading_seed:
            return f"{heading_seed}から考える実務の見方"[:40]
    if len(must_cover) >= 2:
        return f"{must_cover[0]}と{must_cover[1]}から考える実務の見方"[:40]
    if must_cover:
        return f"{must_cover[0]}から考える実務の見方"[:40]
    focus_bundle = _extract_focus_bundle(contract)
    for raw in (
        focus_bundle.get("main_focus", ""),
        str((contract or {}).get("topic_statement") or ""),
        str((contract or {}).get("core_message") or ""),
        _extract_interview_message(contract),
    ):
        normalized = _nounize_focus(str(raw or "")) or _normalize_text(raw)
        normalized = re.split(r"[。!?！？]", normalized, maxsplit=1)[0].strip(" 、,")
        if normalized and not _looks_prompt_like_topic(normalized):
            return f"{normalized}から考える実務の見方"[:40]
    base = str(topic or "").strip()
    if base and not _looks_prompt_like_topic(base):
        return re.split(r"[。!?！？]", base, maxsplit=1)[0].strip()[:40]
    if not allow_generic_fallback:
        return ""
    return "前提と判断軸から考える実務の見方"


def _daily_story_title_seed(topic: str, body: str = "", contract: Dict[str, Any] | None = None) -> str:
    headings = _extract_headings(body)
    must_cover = _lead_must_cover_labels(contract, article_type="daily_story")
    if headings:
        return f"{_normalize_text(headings[0])}から見えたこと"[:40]
    if must_cover:
        return f"{must_cover[0]}から見えたこと"[:40]
    base = str(topic or "").strip()
    if base and not _looks_prompt_like_topic(base):
        return re.split(r"[。!?！？]", base, maxsplit=1)[0].strip()[:40]
    return "日々の出来事から見えたこと"


def _daily_story_lead_from_headings(body: str) -> str:
    headings = [_normalize_text(item) for item in _extract_headings(body) if _normalize_text(item)]
    if headings:
        first = headings[0]
        if re.search(r"(した|していた|なかった|止めた|見直した|崩れた|詰まった|変えた|試した)$", first):
            first = f"{first}こと"
        return f"{first}から、そのあとに何が変わって見えたかを整理します。"
    return ""


def _industry_analysis_title_seed(topic: str, body: str = "", contract: Dict[str, Any] | None = None) -> str:
    headings = _extract_headings(body)
    must_cover = _lead_must_cover_labels(contract, article_type="industry_analysis")
    compact_labels = [
        label
        for label in (_compact_industry_title_label(item) for item in must_cover)
        if label
    ]
    if not str(topic or "").strip() and len(compact_labels) >= 2:
        return f"{compact_labels[0]}と{compact_labels[1]}から整理する業界の見方"[:40]
    if headings:
        heading_seed = _compact_industry_title_label(headings[0])
        if heading_seed:
            return f"{heading_seed}から考える業界の見方"[:40]
    if len(compact_labels) >= 2:
        return f"{compact_labels[0]}と{compact_labels[1]}から整理する業界の見方"[:40]
    if compact_labels:
        return f"{compact_labels[0]}から整理する業界の見方"[:40]
    base = str(topic or "").strip()
    if base and not _looks_prompt_like_topic(base):
        return re.split(r"[。!?！？]", base, maxsplit=1)[0].strip()[:40]
    return "市場の前提から考える業界の見方"


def _compact_title(topic: str, article_type: str, *, body: str = "", contract: Dict[str, Any] | None = None) -> str:
    base = str(topic or "").strip()
    if not base:
        if article_type == "explanatory_article":
            seed = _explanatory_title_seed("", body=body, contract=contract, allow_generic_fallback=False)
            if seed:
                return seed[:40]
        if article_type == "industry_analysis":
            seed = _industry_analysis_title_seed("", body=body, contract=contract)
            if seed:
                return seed[:40]
        return _ARTICLE_LABELS.get(article_type, "記事")
    if article_type == "explanatory_article":
        return _explanatory_title_seed(base, body=body, contract=contract)[:40]
    if article_type == "daily_story":
        return _daily_story_title_seed(base, body=body, contract=contract)[:40]
    if article_type == "industry_analysis":
        return _industry_analysis_title_seed(base, body=body, contract=contract)[:40]
    if article_type == "case_study":
        return _case_study_title_seed(base, body=body, contract=contract)[:40]
    if article_type == "announcement":
        return _announcement_title_seed(base)[:42]
    if article_type == "comparative_review":
        return _comparative_review_title_seed(base, body=body, contract=contract)[:40]
    if article_type == "branding":
        seed = _branding_title_from_body_and_sources(base, body, contract)
        if seed:
            return seed[:56]
    return base[:56]


def _lead_for_type(topic: str, article_type: str, *, contract: Dict[str, Any] | None = None) -> str:
    body = str((contract or {}).get("__body_for_lead") or "")
    paragraphs = _extract_body_paragraphs(body)
    lead_from_body = _take_lead_sentences(paragraphs[0] if paragraphs else "")
    must_cover = _lead_must_cover_labels(contract, article_type=article_type)
    if article_type == "branding":
        if not _LEAD_META_PATTERN.search(lead_from_body) and lead_from_body:
            return _build_natural_branding_lead(topic, body, contract)
        return _build_natural_branding_lead(topic, body, contract)
    if article_type == "announcement":
        if len(must_cover) >= 3:
            return f"{must_cover[0]}、{must_cover[1]}、{must_cover[2]}を先に整理し、対応前に押さえたい流れを短くまとめます。"
        return "変更点、対象、確認事項を先に整理し、対応前に押さえたい流れを短くまとめます。"
    if article_type == "explanatory_article":
        if len(must_cover) >= 3:
            return f"{must_cover[0]}、{must_cover[1]}、{must_cover[2]}を順に整理し、実務の判断につながる形でまとめます。"
        if len(must_cover) >= 2:
            return f"{must_cover[0]}と{must_cover[1]}を先にそろえ、実務での使いどころまで整理します。"
        return "前提と判断軸を先にそろえ、実務での使いどころまで整理します。"
    if article_type == "daily_story":
        lead_from_headings = _daily_story_lead_from_headings(body)
        if lead_from_headings and not _looks_prompt_like_topic(lead_from_headings):
            return lead_from_headings
        if len(must_cover) >= 3:
            return f"{must_cover[0]}から入り、{must_cover[1]}と{must_cover[2]}までを順にたどります。"
        if len(must_cover) >= 2:
            return f"{must_cover[0]}から入り、{must_cover[1]}までを順にたどります。"
        return "その日の出来事から入り、あとから見えた変化までを順にたどります。"
    if article_type == "case_study":
        focus = _case_study_lead_focus(contract)
        progression = _case_study_lead_progression(body, contract)
        if focus:
            return f"{focus}を起点に、{progression}"
        return f"課題の起点から入り、{progression}"
    if article_type == "industry_analysis":
        if len(must_cover) >= 3:
            return f"{must_cover[0]}、{must_cover[1]}、{must_cover[2]}を軸に、判断材料になる形で整理します。"
        if len(must_cover) >= 2:
            return f"{must_cover[0]}と{must_cover[1]}を軸に、判断材料になる形で整理します。"
        return "市場の前提と構造変化を軸に、判断材料になる形で整理します。"
    if article_type == "comparative_review":
        if len(must_cover) >= 2:
            fit_label = next((item for item in must_cover[2:] if "用途" in item or "向き不向き" in item), "用途別の向き不向き")
            return f"{must_cover[0]}と{must_cover[1]}の差がどこで効くかを見ながら、{fit_label}まで順に整理します。"
        if lead_from_body and not _looks_prompt_like_topic(lead_from_body):
            return lead_from_body
        return "評価軸ごとの差分と用途別の向き不向きを、本文の順序で整理します。"
    return f"{topic}について、背景から実務で使える判断軸まで整理します。"


def _resolve_note_scaffold_mode(article_type: str, body: str, headings: List[str]) -> str:
    if article_type in {"announcement", "daily_story"}:
        return "none"
    if article_type == "explanatory_article":
        return "none"
    if len(headings) < 4:
        return "none"
    body_chars = len(str(body or ""))
    if article_type == "comparative_review":
        if body_chars >= 3200:
            return "summary_toc"
        if body_chars >= 2600:
            return "summary_only"
        return "none"
    if article_type in {"branding", "case_study"}:
        if body_chars >= 2600:
            return "summary_toc"
        if body_chars >= 1800:
            return "summary_only"
        return "none"
    if body_chars >= 1800:
        return "summary_toc"
    return "none"


def _build_summary_block(headings: List[str]) -> str:
    if not headings:
        return ""
    summary_points = headings[:3]
    lines = ["この記事でわかること"]
    lines.extend(f"- {heading}" for heading in summary_points)
    return "\n".join(lines).strip()


def _build_toc_block(headings: List[str]) -> str:
    if not headings:
        return ""
    lines = ["目次"]
    lines.extend(f"- {heading}" for heading in headings)
    return "\n".join(lines).strip()


def _body_has_markdown_toc(body: str) -> bool:
    return bool(re.search(r"(?m)^##\s+目次\s*$", str(body or "")))


def _resolve_output_title(
    *,
    topic: str,
    article_type: str,
    body: str,
    contract: Dict[str, Any] | None,
    existing_title: str,
) -> str:
    title, _reason = _resolve_output_title_with_reason(
        topic=topic,
        article_type=article_type,
        body=body,
        contract=contract,
        existing_title=existing_title,
    )
    return title


def _resolve_output_title_with_reason(
    *,
    topic: str,
    article_type: str,
    body: str,
    contract: Dict[str, Any] | None,
    existing_title: str,
) -> Tuple[str, str]:
    preferred = _prefer_generated_title(article_type, existing_title, topic=topic)
    if preferred and article_type == "branding" and _is_company_introduction_contract(contract):
        source_items = _extract_source_grounding_items(contract)
        if _company_intro_has_operational_source(contract, source_items) and _company_intro_history_first_drift(preferred):
            preferred = ""
    if preferred:
        return preferred, "existing_generated_title"
    title = _compact_title(topic, article_type, body=body, contract=contract)
    if article_type == "branding" and _is_company_introduction_contract(contract):
        source_items = _extract_source_grounding_items(contract)
        if _company_intro_has_operational_source(contract, source_items):
            return title, "company_intro_current_business_title"
        if any(str(item.get("bucket") or "") == "history" for item in source_items):
            return title, "company_intro_history_title"
    return title, f"formatter_{article_type or 'unknown'}_title"


def _resolve_output_lead(
    *,
    topic: str,
    article_type: str,
    body: str,
    contract: Dict[str, Any] | None,
    existing_lead: str,
) -> str:
    lead, _reason = _resolve_output_lead_with_reason(
        topic=topic,
        article_type=article_type,
        body=body,
        contract=contract,
        existing_lead=existing_lead,
    )
    return lead


def _resolve_output_lead_with_reason(
    *,
    topic: str,
    article_type: str,
    body: str,
    contract: Dict[str, Any] | None,
    existing_lead: str,
) -> Tuple[str, str]:
    preferred = _prefer_generated_lead(article_type, existing_lead, body)
    if preferred and article_type == "branding" and _is_company_introduction_contract(contract):
        source_items = _extract_source_grounding_items(contract)
        if _company_intro_has_operational_source(contract, source_items) and _company_intro_history_first_drift(preferred):
            preferred = ""
    if preferred:
        return preferred, "existing_generated_lead"
    if article_type == "announcement":
        return "", "announcement_omits_lead"
    lead_contract = dict(contract or {})
    lead_contract["__body_for_lead"] = body
    if article_type == "branding":
        return _build_natural_branding_lead_with_reason(topic, body, lead_contract)
    return _lead_for_type(topic, article_type, contract=lead_contract), f"formatter_{article_type or 'unknown'}_lead"


def _resolve_output_scaffold(article_type: str, body: str) -> tuple[str, str]:
    headings = _extract_headings(body)
    if _body_has_markdown_toc(body):
        return "", ""
    scaffold_mode = _resolve_note_scaffold_mode(article_type, body, headings)
    summary = _build_summary_block(headings) if scaffold_mode in {"summary_only", "summary_toc"} else ""
    toc = _build_toc_block(headings) if scaffold_mode == "summary_toc" else ""
    return summary, toc


def _build_output_full_body(lead: str, summary: str, toc: str, body: str) -> str:
    full_body_parts = [lead]
    if summary:
        full_body_parts.append(summary)
    if toc:
        full_body_parts.append(toc)
    full_body_parts.append(body)
    return "\n\n".join(part for part in full_body_parts if str(part).strip()).strip()


def _build_source_grounding_order_telemetry(source_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "index": str(index),
            "bucket": str(item.get("bucket") or ""),
            "source_title": str(item.get("source_title") or ""),
            "fact_excerpt": str(item.get("fact_text") or "")[:80],
        }
        for index, item in enumerate(source_items)
    ]


def _build_output_formatter_telemetry(
    *,
    topic: str,
    article_type: str,
    contract: Dict[str, Any] | None,
    existing_title: str,
    existing_lead: str,
    resolved_title: str,
    resolved_lead: str,
    final_title: str,
    final_lead: str,
    title_source_reason: str,
    lead_source_reason: str,
) -> Dict[str, Any]:
    contract_dict = dict(contract or {}) if isinstance(contract, dict) else {}
    focus_bundle = _extract_focus_bundle(contract_dict)
    source_items = _extract_source_grounding_items(contract_dict)
    return {
        "formatter_applied": True,
        "output_formatter_version": "company_intro_current_business_opening_v1",
        "article_type": str(article_type or ""),
        "semantic_article_key": str(contract_dict.get("semantic_article_key") or ""),
        "topic": str(topic or "")[:120],
        "topic_statement": str(contract_dict.get("topic_statement") or "")[:120],
        "focus_bundle_main_focus": str(focus_bundle.get("main_focus") or "")[:120],
        "pre_format_title": str(existing_title or ""),
        "resolved_title_before_shape": str(resolved_title or ""),
        "post_format_title": str(final_title or ""),
        "title_source_reason": str(title_source_reason or ""),
        "title_shape_adjusted": bool(str(resolved_title or "") != str(final_title or "")),
        "pre_format_lead": str(existing_lead or ""),
        "resolved_lead_before_shape": str(resolved_lead or ""),
        "post_format_lead": str(final_lead or ""),
        "lead_source_reason": str(lead_source_reason or ""),
        "lead_shape_adjusted": bool(str(resolved_lead or "") != str(final_lead or "")),
        "source_grounding_item_order": _build_source_grounding_order_telemetry(source_items),
        "company_intro_source_contract_slots": _company_intro_slot_presence_telemetry(contract_dict),
    }


def format_output(
    *,
    topic: str,
    article_type: str,
    body: str,
    source_inputs: Iterable[str] | None = None,
    contract: Dict[str, Any] | None = None,
    existing_title: str = "",
    existing_lead: str = "",
) -> Dict[str, Any]:
    title, title_source_reason = _resolve_output_title_with_reason(
        topic=topic,
        article_type=article_type,
        body=body,
        contract=contract,
        existing_title=existing_title,
    )
    lead, lead_source_reason = _resolve_output_lead_with_reason(
        topic=topic,
        article_type=article_type,
        body=body,
        contract=contract,
        existing_lead=existing_lead,
    )
    resolved_title = title
    resolved_lead = lead
    title, lead = _apply_explanatory_tone_opening_shape(
        topic=topic,
        article_type=article_type,
        title=title,
        lead=lead,
        contract=contract,
    )
    title = _apply_daily_story_title_shape(article_type=article_type, title=title)
    source_count = len(list(source_inputs or []))
    references = "参考: 入力ソースをもとに再構成" if source_count else ""
    summary, toc = _resolve_output_scaffold(article_type, body)
    hashtags = ""
    full_body = _build_output_full_body(lead, summary, toc, body)
    full_text = "\n\n".join([title, full_body]).strip()
    format_telemetry = _build_output_formatter_telemetry(
        topic=topic,
        article_type=article_type,
        contract=contract,
        existing_title=existing_title,
        existing_lead=existing_lead,
        resolved_title=resolved_title,
        resolved_lead=resolved_lead,
        final_title=title,
        final_lead=lead,
        title_source_reason=title_source_reason,
        lead_source_reason=lead_source_reason,
    )
    return {
        "title": title,
        "lead": lead,
        "summary": summary,
        "toc": toc,
        "body": body,
        "full_body": full_body,
        "references": references,
        "hashtags": hashtags,
        "full_text": full_text,
        "format_telemetry": format_telemetry,
    }
