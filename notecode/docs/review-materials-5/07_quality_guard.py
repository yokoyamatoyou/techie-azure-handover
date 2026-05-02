"""Quality guard scorer for the simple note pipeline."""

from __future__ import annotations

import importlib
import re
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Mapping

from note.simple_note_pipeline.postprocess import DraftSections

_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")
_NO1_RE = re.compile(r"(?:No\.?\s*1|ナンバーワン|日本一|世界一|業界一)")
_SUPERIORITY_RE = re.compile(r"(?:最高|最強|唯一|圧倒的|絶対的|完全無欠)")
_GUARANTEE_RE = re.compile(r"(?:必ず|100%|絶対に|確実に|保証します|保証できる|完全に解決)")
_LEGAL_CITATION_RE = re.compile(r"(?:景品表示法|個人情報保護法|下請法|特定商取引法|薬機法|第\d+条|法律)")
_STEALTH_RE = re.compile(r"(?:知らないと損|今だけ|限定|急いで|秘密|こっそり|バレずに|誰にも言わず)")
_FIRST_PERSON_RE = re.compile(r"^(?:私たち|当社|弊社|私|わたし|僕|ぼく)")
_HEADING_RE = re.compile(r"^##\s+.+$", re.MULTILINE)
_ENDING_RE = re.compile(r"(です。|ます。|でした。|ました。|だ。|である。|した。|いる。|ない。)$")


def _clean_text(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _split_paragraphs(text: Any) -> List[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", cleaned) if chunk.strip()]


def _split_sentences(text: Any) -> List[str]:
    merged = re.sub(r"\n+", " ", _clean_text(text))
    if not merged:
        return []
    return [part.strip() for part in re.split(r"(?<=[。！？!?])\s*", merged) if part.strip()]


def _sentence_ending_category(sentence: str) -> str:
    stripped = str(sentence or "").strip()
    if not stripped:
        return ""
    matched = _ENDING_RE.search(stripped)
    return matched.group(1) if matched else stripped[-2:]


def _sentence_ending_bucket(sentence: str) -> str:
    stripped = str(sentence or "").strip()
    if not stripped:
        return "other"
    if re.search(r"(かもしれない。|だろう。|ようだ。|と思う。)$", stripped):
        return "soft_modal"
    if re.search(r"(のだ。|ためだ。|からだ。|わけだ。)$", stripped):
        return "reason_explanatory"
    if re.search(r"(です。|ます。|でした。|ました。)$", stripped):
        return "polite"
    if re.search(r"(だ。|である。|した。|いる。|ない。|といえる。)$", stripped):
        return "plain_assertive"
    return "other"


def _topic_anchors(contract: Mapping[str, Any]) -> List[str]:
    seeds = [
        str(contract.get("topic") or ""),
        str(contract.get("core_message") or ""),
        " ".join(str(item or "") for item in list(contract.get("must_cover") or [])[:4]),
    ]
    anchors: List[str] = []
    for token in _TOKEN_RE.findall(" ".join(seeds)):
        normalized = token.lower().strip()
        if normalized and normalized not in anchors:
            anchors.append(normalized)
        if len(anchors) >= 8:
            break
    return anchors


def _allowed_first_person_ratio(article_type: str) -> float:
    if article_type == "daily_story":
        return 0.34
    if article_type == "branding":
        return 0.18
    return 0.05


@lru_cache(maxsize=1)
def _load_style_learner_bundle() -> Dict[str, Any]:
    try:
        module = importlib.import_module("note.simple_note_pipeline.style_learner")
        learner = module.load_default_style_learner()
        return {
            "available": True,
            "module": module,
            "learner": learner,
        }
    except Exception as exc:  # pragma: no cover - fallback path depends on env
        return {
            "available": False,
            "error": str(exc),
        }


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _coverage_rate(text: str, items: Iterable[Any]) -> float:
    normalized_text = str(text or "")
    candidates = [str(item or "").strip() for item in items if str(item or "").strip()]
    if not candidates:
        return 1.0
    covered = 0
    for item in candidates:
        keywords = [token.lower() for token in _TOKEN_RE.findall(item)][:4]
        if not keywords:
            continue
        if any(keyword in normalized_text.lower() for keyword in keywords):
            covered += 1
    return round(covered / max(1, len(candidates)), 4)


def _anchor_tokens(text: str, *, limit: int = 4) -> List[str]:
    tokens: List[str] = []
    for token in _TOKEN_RE.findall(str(text or "")):
        normalized = token.lower().strip()
        if not normalized or normalized in tokens:
            continue
        tokens.append(normalized)
        if len(tokens) >= limit:
            break
    return tokens


def _semantic_ledger_entries(contract: Mapping[str, Any]) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    raw_items = contract.get("_semantic_ledger")
    if not isinstance(raw_items, list):
        return entries
    for item in raw_items[:6]:
        if not isinstance(item, Mapping):
            continue
        heading = str(item.get("heading") or "").strip()
        anchor = str(item.get("anchor") or heading).strip()
        claim = str(item.get("claim") or item.get("key_message") or "").strip()
        bridge = str(item.get("bridge") or "").strip()
        if not claim:
            continue
        entries.append(
            {
                "heading": heading,
                "anchor": anchor,
                "claim": claim,
                "bridge": bridge,
            }
        )
    return entries


def _split_body_sections(body: str) -> List[Dict[str, str]]:
    sections: List[Dict[str, str]] = []
    current_heading = ""
    current_lines: List[str] = []
    for raw_line in _clean_text(body).splitlines():
        matched = re.match(r"^##\s+(.+)$", raw_line.strip())
        if matched:
            if current_heading:
                sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
            current_heading = matched.group(1).strip()
            current_lines = []
            continue
        if current_heading:
            current_lines.append(raw_line)
    if current_heading:
        sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
    return sections


def _measure_heading_reanchor_metrics(body: str, semantic_entries: List[Dict[str, str]]) -> Dict[str, Any]:
    section_map = {
        str(entry.get("heading") or "").strip(): entry
        for entry in semantic_entries
        if str(entry.get("heading") or "").strip()
    }
    checked_section_count = 0
    miss_count = 0
    soft_warnings: List[str] = []
    for section in _split_body_sections(body):
        entry = section_map.get(section["heading"])
        if not entry:
            continue
        first_sentence = next((sentence for sentence in _split_sentences(section["body"]) if sentence), "")
        anchor_tokens = _anchor_tokens(entry.get("anchor") or section["heading"])
        if not first_sentence or not anchor_tokens:
            continue
        checked_section_count += 1
        opener = first_sentence.lower()
        if any(token in opener for token in anchor_tokens):
            continue
        miss_count += 1
        soft_warnings.append(f"heading_reanchor:{section['heading']}")
    miss_ratio = round(miss_count / max(1, checked_section_count), 4) if checked_section_count else 0.0
    return {
        "heading_reanchor_checked_section_count": checked_section_count,
        "heading_reanchor_miss_count": miss_count,
        "heading_reanchor_miss_ratio": miss_ratio,
        "omission_ambiguity_score": miss_ratio,
        "omission_soft_warnings": soft_warnings[:6],
    }


def _measure_ending_bucket_metrics(sentences: Iterable[str]) -> Dict[str, Any]:
    bucket_counts = {
        "polite": 0,
        "plain_assertive": 0,
        "soft_modal": 0,
        "reason_explanatory": 0,
        "other": 0,
    }
    previous_bucket = ""
    current_run = 0
    max_run = 0
    observed = 0
    for sentence in sentences:
        bucket = _sentence_ending_bucket(sentence)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        observed += 1
        if bucket == previous_bucket:
            current_run += 1
        else:
            current_run = 1
        previous_bucket = bucket
        max_run = max(max_run, current_run)
    monotony_score = round(min(1.0, max_run / max(1, observed)), 4) if observed else 0.0
    return {
        "ending_bucket_counts": bucket_counts,
        "ending_bucket_max_run": max_run,
        "ending_bucket_monotony_score": monotony_score,
    }


def _build_ending_control_lines(diagnostics: Mapping[str, Any]) -> List[str]:
    max_run = int(diagnostics.get("ending_bucket_max_run", 0) or 0)
    if max_run < 3:
        return []
    bucket_counts = dict(diagnostics.get("ending_bucket_counts") or {})
    dominant_bucket = max(bucket_counts, key=bucket_counts.get) if bucket_counts else "other"
    lines = [f"同一文末bucketの{max_run}連続を崩し、隣接3文で同じ終わり方を続けない。"]
    if dominant_bucket == "polite":
        lines.append("です/ます系を3文以上続けず、1文は言い切りか説明口調へずらす。")
    elif dominant_bucket == "plain_assertive":
        lines.append("だ/である系を3文以上続けず、1文は説明口調か柔らかい言い回しへずらす。")
    elif dominant_bucket == "reason_explanatory":
        lines.append("のだ/ためだ/からだ系を段落冒頭で連打しない。")
    elif dominant_bucket == "soft_modal":
        lines.append("だろう/かもしれない/ようだ系を続けず、断定か説明へ戻して揺れを作る。")
    else:
        lines.append("同じ文末の反復箇所だけを局所的にずらし、段落全体の意味役割は保つ。")
    return lines


def _measure_comparative_section_metrics(body: str) -> Dict[str, Any]:
    thin_headings: List[str] = []
    for section in _split_body_sections(body):
        sentence_count = len([sentence for sentence in _split_sentences(section["body"]) if sentence])
        if sentence_count <= 1:
            thin_headings.append(section["heading"])
    return {
        "comparative_thin_section_count": len(thin_headings),
        "comparative_thin_section_headings": thin_headings[:4],
    }


def _build_heuristic_summary(
    *,
    article_type: str,
    diagnostics: Mapping[str, Any],
    feature_vector: Mapping[str, float],
) -> Dict[str, Any]:
    sentence_variation_risk = _clamp(1.0 - min(1.0, float(feature_vector.get("sentence_length_cv", 0.0)) / 0.45))
    paragraph_variation_risk = _clamp(1.0 - min(1.0, float(feature_vector.get("paragraph_length_cv", 0.0)) / 0.5))
    opener_repetition_risk = _clamp(max(float(feature_vector.get("repeated_opening_ratio", 0.0)), float(diagnostics.get("repeated_opening_count", 0) or 0) / 3.0))
    explicit_subject_risk = _clamp(max(0.0, float(feature_vector.get("first_person_start_ratio", 0.0)) - _allowed_first_person_ratio(article_type)) / 0.25)
    ending_monotony_risk = _clamp(max(float(feature_vector.get("same_ending_run_ratio", 0.0)) * 3.5, float(diagnostics.get("same_ending_runs", 0) or 0) / 6.0))
    topic_echo_ratio = float(feature_vector.get("topic_opening_ratio", 0.0))
    topic_echo_risk = _clamp(max(0.0, topic_echo_ratio - 0.45) / 0.35)
    duplicate_risk = _clamp(max(float(feature_vector.get("duplicate_paragraph_ratio", 0.0)) * 2.0, float(diagnostics.get("duplicate_paragraph_count", 0) or 0)))
    weighted_score = _clamp(
        0.16 * sentence_variation_risk
        + 0.14 * paragraph_variation_risk
        + 0.2 * opener_repetition_risk
        + 0.16 * explicit_subject_risk
        + 0.18 * ending_monotony_risk
        + 0.08 * topic_echo_risk
        + 0.08 * duplicate_risk
    )
    return {
        "score": weighted_score,
        "signals": {
            "sentence_variation": sentence_variation_risk,
            "paragraph_variation": paragraph_variation_risk,
            "opener_repetition": opener_repetition_risk,
            "explicit_subject_behavior": explicit_subject_risk,
            "ending_monotony": ending_monotony_risk,
            "topic_echo": topic_echo_risk,
            "duplicate_paragraph": duplicate_risk,
        },
        "feature_vector": {key: round(float(value), 4) for key, value in feature_vector.items()},
    }


def measure_diagnostics(
    contract: Mapping[str, Any],
    draft: DraftSections,
    *,
    editor_report: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    daily_story = article_type == "daily_story"
    normalized_editor_report = dict(editor_report or {})
    grammar_repair_count = int(normalized_editor_report.get("grammar_repair_count", 0) or 0)
    sentence_integrity_repair_count = int(normalized_editor_report.get("sentence_integrity_repair_count", 0) or 0)
    sentence_integrity_warning_count = int(normalized_editor_report.get("sentence_integrity_warning_count", 0) or 0)
    paragraphs = [paragraph for paragraph in _split_paragraphs(draft.body) if not paragraph.startswith("## ")]
    sentences = _split_sentences(f"{draft.lead}\n{draft.body}")
    first_person_hits = sum(1 for paragraph in paragraphs if _FIRST_PERSON_RE.match(paragraph))
    paragraph_first_person_starts = first_person_hits
    openers: Dict[str, int] = {}
    duplicate_paragraph_count = 0
    seen_paragraphs: set[str] = set()
    for paragraph in paragraphs:
        normalized = re.sub(r"\s+", "", paragraph)
        normalized = re.sub(r"[、。！？!?「」『』（）()]", "", normalized)
        opener = normalized[:10]
        if opener:
            openers[opener] = openers.get(opener, 0) + 1
        if normalized in seen_paragraphs:
            duplicate_paragraph_count += 1
        seen_paragraphs.add(normalized)
    repeated_opening_count = sum(max(0, count - 1) for count in openers.values())
    endings = [_sentence_ending_category(sentence) for sentence in sentences if _sentence_ending_category(sentence)]
    same_ending_runs = 0
    previous_ending = ""
    consecutive = 0
    for ending in endings:
        if ending == previous_ending:
            consecutive += 1
            if consecutive >= 2:
                same_ending_runs += 1
        else:
            consecutive = 0
        previous_ending = ending

    topic_anchors = _topic_anchors(contract)
    paragraph_opening_with_topic = 0
    for paragraph in paragraphs:
        first_sentence = _split_sentences(paragraph[:120])
        opener = (first_sentence[0] if first_sentence else paragraph[:60]).lower()
        if any(anchor in opener for anchor in topic_anchors):
            paragraph_opening_with_topic += 1
    topic_opening_ratio = round(paragraph_opening_with_topic / max(1, len(paragraphs)), 4)
    must_cover_rate = _coverage_rate(f"{draft.title}\n{draft.lead}\n{draft.body}", list(contract.get("must_cover") or []))
    prompt_anchor_rate = _coverage_rate(f"{draft.title}\n{draft.lead}\n{draft.body}", [contract.get("topic"), contract.get("core_message")])
    semantic_entries = _semantic_ledger_entries(contract)
    semantic_anchor_rate = _coverage_rate(
        f"{draft.title}\n{draft.lead}\n{draft.body}",
        [item["anchor"] for item in semantic_entries if item.get("anchor")],
    )
    semantic_claim_rate = _coverage_rate(
        f"{draft.title}\n{draft.lead}\n{draft.body}",
        [item["claim"] for item in semantic_entries if item.get("claim")],
    )
    omission_metrics = _measure_heading_reanchor_metrics(draft.body, semantic_entries)
    ending_bucket_metrics = _measure_ending_bucket_metrics(sentences)
    comparative_metrics = (
        _measure_comparative_section_metrics(draft.body)
        if article_type == "comparative_review"
        else {
            "comparative_thin_section_count": 0,
            "comparative_thin_section_headings": [],
        }
    )
    heading_count = len(_HEADING_RE.findall(draft.body))
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    if length_mode == "short":
        target_chars = 1600 if article_type == "announcement" else 1800
        heading_target = 4 if semantic_key == "company_introduction" else 3
    elif length_mode == "long":
        target_chars = 3800
        heading_target = 5
    elif length_mode == "normal":
        target_chars = 2800
        heading_target = 4
    else:
        target_chars = 2200 if article_type == "announcement" else 2600
        heading_target = 4
    repair_instructions: List[str] = []
    review_points: List[str] = []
    severity = 0

    allowed_first_person_starts = 2 if daily_story else 1 if article_type == "branding" else 0
    if paragraph_first_person_starts > allowed_first_person_starts:
        severity += 2
        repair_instructions.append("段落冒頭の一人称を減らし、主語省略や名詞への置き換えを使う。")
        review_points.append("文体: 主語の出し直しが多いため、一人称と会社主語を整理しました。")
    if repeated_opening_count > 1:
        severity += 2
        repair_instructions.append("段落の書き出しを変え、同じ導入を繰り返さない。")
        review_points.append("構成: 似た書き出しが続かないよう、段落の役割を分けました。")
    if duplicate_paragraph_count > 0:
        severity += 3
        repair_instructions.append("重複した説明を統合し、言い換え反復を削る。")
        review_points.append("構成: 重複気味の説明を圧縮し、論点の前進を優先しました。")
    if same_ending_runs > 2:
        severity += 1
        repair_instructions.append("文末の単調さを減らし、文の終わり方を自然に変える。")
        review_points.append("文体: 文末の単調さを抑えて読み味を整えました。")
    if heading_count < 2:
        severity += 1
        repair_instructions.append("見出しを増やして話題の切り替えを明確にする。")
    company_intro_structure_shortfall = False
    if semantic_key == "company_introduction" and heading_count < heading_target:
        severity += 2
        company_intro_structure_shortfall = True
        repair_instructions.append("企業紹介は短文でも見出しを4本前後に保ち、事業内容・運用支援の強み・向き合い方を分ける。")
    if len(draft.body) < int(target_chars * 0.72):
        severity += 1
        repair_instructions.append("要点を保ったまま情報密度を上げ、本文を少し厚くする。")
        if semantic_key == "company_introduction":
            company_intro_structure_shortfall = True
    if article_type == "announcement" and re.search(r"[！!?]", draft.body):
        severity += 1
        repair_instructions.append("お知らせ文として感情記号や勢いの強い語調を抑える。")
    if grammar_repair_count > 0 or sentence_integrity_repair_count > 0:
        review_points.append("文法: 接続や文末の崩れを軽く補修し、読み筋を整えました。")
    if sentence_integrity_warning_count > 0:
        severity += 2
        repair_instructions.append("文の切れや接続不全を解消し、途中でぶつ切りになる表現を残さない。")
        review_points.append("文法: 文のつながりに未解消の崩れが残るため、再修正を優先します。")
    if semantic_entries and semantic_claim_rate < 0.72:
        severity += 2
        repair_instructions.append("各見出しで semantic ledger の claim を言い切り、導入で先食いした論点は見出し本文へ戻す。")
        review_points.append("構成: 節ごとの意味役割が抜けないよう、claim 単位で整理しました。")
    if semantic_entries and semantic_anchor_rate < 0.6:
        severity += 1
        repair_instructions.append("節冒頭で対象を短く再アンカーし、誰・何の話か曖昧な文を減らす。")
        review_points.append("文体: 節の冒頭で対象を立て直し、主語省略の曖昧さを抑えました。")
    comparative_thin_section_count = int(comparative_metrics.get("comparative_thin_section_count", 0) or 0)
    if article_type == "comparative_review" and comparative_thin_section_count >= 2:
        severity += 2
        repair_instructions.append("比較レビューでは各見出しを1文で終えず、差が出る理由か向く条件をもう1文足す。")
        review_points.append("構成: 比較見出しが薄い箇所に、差の理由か向く条件を補いました。")
    if must_cover_rate < 0.55:
        review_points.append("根拠: 必須で触れる論点の反映を優先して整理しました。")

    return {
        "first_person_hits": first_person_hits,
        "paragraph_first_person_starts": paragraph_first_person_starts,
        "repeated_opening_count": repeated_opening_count,
        "duplicate_paragraph_count": duplicate_paragraph_count,
        "same_ending_runs": same_ending_runs,
        "ending_bucket_counts": dict(ending_bucket_metrics.get("ending_bucket_counts") or {}),
        "ending_bucket_max_run": int(ending_bucket_metrics.get("ending_bucket_max_run", 0) or 0),
        "ending_bucket_monotony_score": float(ending_bucket_metrics.get("ending_bucket_monotony_score", 0.0) or 0.0),
        "topic_opening_ratio": topic_opening_ratio,
        "heading_count": heading_count,
        "body_chars": len(draft.body),
        "target_chars": target_chars,
        "must_cover_reflection_rate": must_cover_rate,
        "prompt_anchor_coverage": prompt_anchor_rate,
        "anchor_term_coverage": prompt_anchor_rate,
        "semantic_anchor_coverage": semantic_anchor_rate,
        "semantic_claim_coverage": semantic_claim_rate,
        "semantic_ledger_count": len(semantic_entries),
        "heading_reanchor_checked_section_count": int(omission_metrics.get("heading_reanchor_checked_section_count", 0) or 0),
        "heading_reanchor_miss_count": int(omission_metrics.get("heading_reanchor_miss_count", 0) or 0),
        "heading_reanchor_miss_ratio": float(omission_metrics.get("heading_reanchor_miss_ratio", 0.0) or 0.0),
        "omission_ambiguity_score": float(omission_metrics.get("omission_ambiguity_score", 0.0) or 0.0),
        "omission_soft_warnings": list(omission_metrics.get("omission_soft_warnings") or []),
        "comparative_thin_section_count": comparative_thin_section_count,
        "comparative_thin_section_headings": list(comparative_metrics.get("comparative_thin_section_headings") or []),
        "section_focus_coverage": round(min(1.0, heading_count / max(2, heading_target)), 4),
        "grammar_repair_count": grammar_repair_count,
        "sentence_integrity_repair_count": sentence_integrity_repair_count,
        "sentence_integrity_warning_count": sentence_integrity_warning_count,
        "company_intro_structure_shortfall": company_intro_structure_shortfall,
        "repair_instructions": repair_instructions,
        "review_points": review_points[:3],
        "severity": severity,
        "semantic_issue_count": duplicate_paragraph_count + repeated_opening_count,
        "issue_count": len(review_points),
    }


def _build_learner_summary(text: str, *, topic_anchors: List[str]) -> Dict[str, Any]:
    bundle = _load_style_learner_bundle()
    if not bundle.get("available"):
        return {
            "available": False,
            "score": None,
            "label": "unavailable",
            "error": str(bundle.get("error") or ""),
            "payload": {},
        }
    module = bundle["module"]
    learner = bundle["learner"]
    prediction = learner.predict_from_text(text, topic_anchors=topic_anchors)
    payload = module.build_aiindex_ready_payload(prediction)
    return {
        "available": True,
        "score": _clamp(payload.get("learner_ai_probability", 0.0)),
        "label": str(payload.get("learner_label") or ""),
        "payload": payload,
    }


def _legal_sources(source_pack: Mapping[str, Any]) -> str:
    parts: List[str] = []
    for item in list(source_pack.get("source_documents") or [])[:6]:
        if not isinstance(item, Mapping):
            continue
        parts.append(str(item.get("title") or ""))
        parts.append(str(item.get("content") or "")[:400])
        parts.append(str(item.get("locator") or ""))
    return "\n".join(parts)


def _build_legal_summary(text: str, source_pack: Mapping[str, Any]) -> Dict[str, Any]:
    normalized_text = _clean_text(text)
    source_text = _legal_sources(source_pack)
    flags: List[Dict[str, Any]] = []

    if _NO1_RE.search(normalized_text):
        flags.append({"category": "no1_claim", "risk": 0.85, "message": "No.1表現は根拠がない限り削るか条件を明示する。"})
    if _SUPERIORITY_RE.search(normalized_text):
        flags.append({"category": "superiority_claim", "risk": 0.62, "message": "最上級・唯一表現は根拠がない限り弱める。"})
    if _GUARANTEE_RE.search(normalized_text):
        flags.append({"category": "guarantee_claim", "risk": 0.8, "message": "保証・断定表現を避け、条件付きまたは可能性表現へ弱める。"})
    if _LEGAL_CITATION_RE.search(normalized_text):
        verified = any(token in source_text for token in ("景品表示法", "個人情報保護法", "下請法", "特定商取引法", "薬機法", "第"))
        flags.append(
            {
                "category": "unverified_legal_citation" if not verified else "legal_reference_watch",
                "risk": 0.72 if not verified else 0.32,
                "message": "法令名や条文番号を出すなら出典を確認し、未確認なら一般論へ言い換える。",
            }
        )
    if _STEALTH_RE.search(normalized_text):
        flags.append({"category": "stealth_like_copy", "risk": 0.58, "message": "煽り・秘匿・限定訴求を抑え、企業発信として自然な説明に戻す。"})

    risk_score = _clamp(sum(float(item["risk"]) for item in flags) / max(1, len(flags))) if flags else 0.0
    return {
        "risk_score": risk_score,
        "issue_count": len(flags),
        "flagged_categories": [str(item["category"]) for item in flags],
        "warnings": [str(item["message"]) for item in flags],
    }


def _dedupe_lines(items: Iterable[str], *, limit: int = 8) -> List[str]:
    normalized: List[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text or text in normalized:
            continue
        normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def evaluate_quality_guard(
    *,
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    article_type = str(contract.get("article_type") or "explanatory_article").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    text = _clean_text(f"{draft.lead}\n\n{draft.body}")
    topic_anchors = _topic_anchors(contract)
    learner_summary = _build_learner_summary(text, topic_anchors=topic_anchors)

    feature_vector: Dict[str, float] = {}
    feature_vector_supported = False
    if learner_summary.get("available"):
        feature_vector = dict((learner_summary.get("payload") or {}).get("feature_vector") or {})
        feature_vector_supported = True
    if not feature_vector:
        bundle = _load_style_learner_bundle()
        if bundle.get("available"):
            module = bundle["module"]
            feature_vector = module.extract_style_features(text, topic_anchors=topic_anchors)
            feature_vector_supported = True
        else:  # pragma: no cover - depends on missing sklearn env
            feature_vector = {
                "sentence_length_cv": 0.0,
                "paragraph_length_cv": 0.0,
                "repeated_opening_ratio": 0.0,
                "first_person_start_ratio": 0.0,
                "same_ending_run_ratio": 0.0,
                "topic_opening_ratio": 0.0,
                "duplicate_paragraph_ratio": 0.0,
            }

    heuristic_summary = _build_heuristic_summary(
        article_type=article_type,
        diagnostics=diagnostics,
        feature_vector=feature_vector,
    )
    signals = heuristic_summary["signals"]
    rhythm_flatness_cluster = (
        feature_vector_supported
        and
        length_mode == "short"
        and float(signals.get("sentence_variation", 0.0)) >= 0.85
        and float(signals.get("paragraph_variation", 0.0)) >= 0.85
        and max(float(signals.get("ending_monotony", 0.0)), float(signals.get("opener_repetition", 0.0))) >= 0.3
    )
    heuristic_score = float(heuristic_summary["score"])
    learner_score = learner_summary.get("score")
    ai_index_score = _clamp(0.55 * heuristic_score + 0.45 * float(learner_score)) if learner_score is not None else heuristic_score
    ai_index_label = "ai_like" if ai_index_score >= 0.58 else "borderline" if ai_index_score >= 0.42 else "human_like"

    legal_summary = _build_legal_summary(text, source_pack)
    structural_score = _clamp(float(diagnostics.get("severity", 0) or 0) / 5.0)
    sentence_integrity_warning_count = int(diagnostics.get("sentence_integrity_warning_count", 0) or 0)
    grammar_repair_count = int(diagnostics.get("grammar_repair_count", 0) or 0)
    sentence_integrity_repair_count = int(diagnostics.get("sentence_integrity_repair_count", 0) or 0)
    repair_trigger_score = _clamp(max(float(legal_summary.get("risk_score", 0.0)), 0.7 * ai_index_score + 0.3 * structural_score))
    if semantic_key == "company_introduction" and bool(diagnostics.get("company_intro_structure_shortfall")):
        repair_trigger_score = max(repair_trigger_score, 0.6)
    if article_type == "comparative_review" and int(diagnostics.get("comparative_thin_section_count", 0) or 0) >= 2:
        repair_trigger_score = max(repair_trigger_score, 0.6)
    if rhythm_flatness_cluster:
        repair_trigger_score = max(repair_trigger_score, 0.6)
    if sentence_integrity_warning_count > 0:
        repair_trigger_score = max(repair_trigger_score, 0.62)

    repair_instructions = _dedupe_lines(
        [
            *list(diagnostics.get("repair_instructions") or []),
            "文の切れや接続不全を解消し、途中でぶつ切りになる表現を残さない。" if sentence_integrity_warning_count > 0 else "",
            "短めの記事でも文長・段落長・文末のリズムを散らし、同じ流れを続けない。" if rhythm_flatness_cluster else "",
            "文長と段落長の揺れを増やし、同じリズムを続けない。" if heuristic_summary["signals"]["sentence_variation"] >= 0.55 or heuristic_summary["signals"]["paragraph_variation"] >= 0.55 else "",
            "段落の書き出しを変え、同じ導入を繰り返さない。" if heuristic_summary["signals"]["opener_repetition"] >= 0.45 else "",
            "段落冒頭の主語を減らし、企業主語や一人称の連打を避ける。" if heuristic_summary["signals"]["explicit_subject_behavior"] >= 0.45 else "",
            *(_build_ending_control_lines(diagnostics) if heuristic_summary["signals"]["ending_monotony"] >= 0.45 else []),
            "段落冒頭で同じ話題語を反復しすぎない。" if heuristic_summary["signals"]["topic_echo"] >= 0.45 else "",
            *list(legal_summary.get("warnings") or []),
        ],
        limit=10,
    )
    soft_warnings = _dedupe_lines(
        [
            "grammar:sentence_integrity" if sentence_integrity_warning_count > 0 else "",
            "grammar:editor_repair_applied" if grammar_repair_count > 0 or sentence_integrity_repair_count > 0 else "",
            "ai:rhythm_flatness_cluster" if rhythm_flatness_cluster else "",
            "comparative:thin_sections" if article_type == "comparative_review" and int(diagnostics.get("comparative_thin_section_count", 0) or 0) >= 2 else "",
            "ending:bucket_monotony" if int(diagnostics.get("ending_bucket_max_run", 0) or 0) >= 3 else "",
            *(f"ai:{name}" for name, value in heuristic_summary["signals"].items() if float(value) >= 0.45),
            *(f"legal:{name}" for name in legal_summary.get("flagged_categories") or []),
            f"ai_index:{ai_index_label}" if ai_index_score >= 0.42 else "",
        ],
        limit=12,
    )

    ai_index_payload = {
        "score": ai_index_score,
        "label": ai_index_label,
        "heuristic_score": heuristic_score,
        "learner_score": learner_score,
        "learner_available": bool(learner_summary.get("available")),
        "signals": heuristic_summary["signals"],
    }
    if learner_summary.get("available"):
        payload = dict(learner_summary.get("payload") or {})
        ai_index_payload.update(
            {
                "learner_label": payload.get("learner_label"),
                "learner_model": payload.get("learner_model"),
                "learner_calibration_version": payload.get("learner_calibration_version"),
                "learner_confidence": payload.get("learner_confidence"),
                "learner_feature_highlights": payload.get("learner_feature_highlights"),
            }
        )
    return {
        "ai_index": ai_index_payload,
        "heuristic_summary": heuristic_summary,
        "learner_summary": learner_summary,
        "legal_summary": legal_summary,
        "repair_trigger_score": repair_trigger_score,
        "repair_required": repair_trigger_score >= 0.58,
        "repair_instructions": repair_instructions,
        "soft_warnings": soft_warnings,
    }
