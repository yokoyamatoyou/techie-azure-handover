"""Prompt intent profiling shared by interview and contract resolution."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

_TARGET_EXPLICIT_RE = re.compile(
    r"(?:向け|向けに|向けの|対象|読者|利用者|ユーザー|担当者|候補者|既存顧客|導入検討者)"
)
_PROMPT_DETAIL_RE = re.compile(
    r"(?:なぜ|理由|背景|課題|判断軸|比較|違い|注意点|手順|流れ|対象|開始日|導入|運用|活用|価値|事例|理念|文化)"
)
_COMPANY_INTRO_RE = re.compile(
    r"(?:自社説明|自社紹介|会社説明|会社紹介|会社概要|企業紹介|事業内容|沿革|創業|今後方針|私たちについて)"
)
_WRITING_GUIDANCE_RE = re.compile(
    r"(?:書き方|何を書|どう書|投稿方法|始め方|コツ|ノウハウ|運用方法|発信方法|文章の作り方|テーマの決め方)"
)
_NOTE_MEDIA_RE = re.compile(r"(?:\bnote\b|noteに|noteへ|note向け|初めて投稿|投稿する)")
_FIRST_POST_RE = re.compile(r"(?:初めて投稿|初回投稿|初めてのnote投稿)")
_TONE_RE = re.compile(r"(?:事務的|口調|文体|トーン|やわらか|柔らか|堅すぎ|硬すぎ)")
_STYLE_CLAUSE_RE = re.compile(
    r"(?:を)?(?:事務的|口調|文体|トーン|やわらか|柔らか|堅すぎ|硬すぎ)[^。]*?(?:してください|してほしい|表示してください|書いてください)?$"
)
_META_REQUEST_RE = re.compile(
    r"(?:AIモデル|モデルは何|モデル名|使用モデル|使っているモデル|"
    r"どういうアルゴリズム|どんなアルゴリズム|アルゴリズムで動いて|"
    r"仕組みを教えて|内部指示|system prompt|developer message)",
    re.I,
)
_GENERATION_CONTENT_RE = re.compile(
    r"(?:記事|本文|ブログ|投稿|お知らせ|事例|業界分析|比較レビュー|会社紹介|自社紹介|解説)",
    re.I,
)
_GENERATION_ACTION_RE = re.compile(
    r"(?:書(?:いて|きたい)|作成(?:して)?|生成(?:して)?|まとめ(?:て)?|整理(?:して)?|出力(?:して)?)",
    re.I,
)
_DX_INITIAL_STAGE_RE = re.compile(
    r"DX[^。]*?(?:最初|初期)[^。]*?(?:アナログデータ|紙|帳票)[^。]*?(?:デジタル化|電子化)"
)
_AUDIENCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("一般読者", re.compile(r"一般読者")),
    ("DXを推進する方", re.compile(r"DXを推進する(?:方|人|担当者|責任者|方向け)")),
    ("DX担当者", re.compile(r"(?:DX担当者|DX推進担当者)")),
    ("実務担当者", re.compile(r"実務担当者")),
    ("経営層", re.compile(r"経営層")),
)


def _first_sentence(text: str) -> str:
    stripped = str(text or "").strip()
    if not stripped:
        return ""
    parts = re.split(r"[。!?！？]\s*", stripped, maxsplit=1)
    return parts[0].strip()


def build_source_excerpt(source_texts: Optional[Iterable[str]], *, limit_chars: int = 840) -> str:
    if not source_texts:
        return ""
    chunks = []
    remaining = max(0, int(limit_chars))
    for item in source_texts:
        if remaining <= 0:
            break
        text = str(item or "").strip()
        if not text:
            continue
        chunk = text[:remaining]
        chunks.append(chunk)
        remaining -= len(chunk)
    return " ".join(chunks)


def compute_prompt_detail_score(prompt: str) -> int:
    text = str(prompt or "").strip()
    score = 0
    if len(text) >= 48:
        score += 1
    if len(text) >= 96:
        score += 1
    if _PROMPT_DETAIL_RE.search(text):
        score += 1
    if any(mark in text for mark in ("、", "。", "・", "／", "/", ":", "：")):
        score += 1
    return score


def detect_target_explicit(prompt: str, source_excerpt: str = "") -> bool:
    text = str(prompt or "").strip()
    if _TARGET_EXPLICIT_RE.search(text):
        return True
    excerpt = str(source_excerpt or "").strip()
    return bool(re.search(r"(?:対象|利用者|読者|ユーザー|担当者|候補者|既存顧客)", excerpt))


def _extract_prompt_audience_candidates(prompt: str) -> List[str]:
    value = str(prompt or "").strip()
    if not value:
        return []
    audiences: List[str] = []
    for label, pattern in _AUDIENCE_PATTERNS:
        if pattern.search(value) and label not in audiences:
            audiences.append(label)
    return audiences


def _derive_company_intro_context_items(prompt: str) -> List[str]:
    value = str(prompt or "").strip()
    if not value:
        return []
    items: List[str] = []
    audiences = _extract_prompt_audience_candidates(value)
    if audiences:
        items.append(f"{audiences[0]}にも伝わる言葉で書く")
    for audience in audiences[1:]:
        if audience == "DXを推進する方":
            items.append("DXを推進する方が自社の文脈で読める視点も入れる")
        else:
            items.append(f"{audience}の関心にも触れる")
    if _DX_INITIAL_STAGE_RE.search(value) or (
        "DX" in value and "デジタル化" in value and ("アナログ" in value or "紙" in value)
    ):
        items.append("DXの初期段階として、アナログデータのデジタル化を起点にする")
    elif "DX" in value:
        items.append("DXを進める読者が自社文脈で読める説明にする")
    return items


def _derive_company_intro_topic(prompt: str) -> str:
    text = _first_sentence(prompt)
    if not text:
        return ""
    company_first_post = bool(_NOTE_MEDIA_RE.search(prompt) and _FIRST_POST_RE.search(prompt))
    text = re.sub(r"^(?:noteに初めて投稿するので|初めて投稿するので|初回投稿として)[、,\s]*", "初回投稿として、", text)
    text = re.sub(r"(?:noteに|noteへ|note向けに)[^、。]*[、,\s]*", "", text)
    text = _STYLE_CLAUSE_RE.sub("", text).strip(" 、。")
    intro_prefix = "会社として初めてのnote投稿で、" if company_first_post else "初回投稿として、"
    if "自社説明" in text:
        return intro_prefix + "自社を紹介する"
    if "自社紹介" in text:
        return intro_prefix + "自社を紹介する"
    if "会社説明" in text:
        return intro_prefix + "会社を紹介する"
    if "会社紹介" in text:
        return intro_prefix + "会社を紹介する"
    if re.search(r"(事業内容|データエントリ|データエントリー)", text) and re.search(r"(歴史|沿革|歩み|創業)", text):
        if re.search(r"(データエントリ|データエントリー)", text):
            return "自社のデータエントリー事業と歩みを紹介する"
        return "自社の事業内容と歩みを紹介する"
    if re.search(r"(事業内容|サービス内容|何をしている会社)", text):
        if re.search(r"(データエントリ|データエントリー)", text):
            return "自社のデータエントリー事業を紹介する"
        return "自社の事業内容を紹介する"
    if re.search(r"(歴史|沿革|歩み|創業)", text):
        return "自社の歩みを紹介する"
    if text and not text.endswith("する"):
        if text.endswith("ください") or text.endswith("表示"):
            text = re.sub(r"(?:表示)?してください$", "", text).strip(" 、。")
        if text:
            if re.search(r"(書いて|かいて|作成|生成|まとめ)", text):
                return ""
            return text
    return text


def derive_prompt_intent_profile(
    user_prompt: str,
    article_type: str,
    *,
    source_excerpt: str = "",
) -> Dict[str, Any]:
    prompt = str(user_prompt or "").strip()
    article_key = str(article_type or "").strip().lower()
    prompt_detail_score = compute_prompt_detail_score(prompt)
    target_explicit = detect_target_explicit(prompt, source_excerpt)
    company_intro_signal = bool(_COMPANY_INTRO_RE.search(prompt))
    writing_guidance_signal = bool(_WRITING_GUIDANCE_RE.search(prompt))
    note_media_signal = bool(_NOTE_MEDIA_RE.search(prompt))
    tone_signal = bool(_TONE_RE.search(prompt))
    meta_request_signal = bool(_META_REQUEST_RE.search(prompt))
    content_generation_signal = bool(
        _GENERATION_CONTENT_RE.search(prompt)
        or _GENERATION_ACTION_RE.search(prompt)
        or company_intro_signal
        or writing_guidance_signal
        or note_media_signal
    )

    primary_intent = "generic"
    if meta_request_signal and not content_generation_signal:
        primary_intent = "meta_request"
    elif article_key == "announcement":
        primary_intent = "announcement"
    elif company_intro_signal and writing_guidance_signal:
        primary_intent = "ambiguous_company_intro_vs_guidance"
    elif company_intro_signal:
        primary_intent = "company_introduction"
    elif writing_guidance_signal:
        primary_intent = "writing_guidance"
    elif article_key in {"branding", "corporate_culture"} and note_media_signal and tone_signal:
        primary_intent = "company_introduction"

    preferred_topic_statement = ""
    prefer_prompt_topic = primary_intent == "company_introduction"
    prompt_audience_candidates = _extract_prompt_audience_candidates(prompt) if prefer_prompt_topic else []
    prompt_context_items = _derive_company_intro_context_items(prompt) if prefer_prompt_topic else []
    if prefer_prompt_topic:
        preferred_topic_statement = _derive_company_intro_topic(prompt)

    ambiguity_detected = primary_intent == "ambiguous_company_intro_vs_guidance"
    if not ambiguity_detected and company_intro_signal and note_media_signal and writing_guidance_signal:
        ambiguity_detected = True

    return {
        "primary_intent": primary_intent,
        "company_intro_signal": company_intro_signal,
        "writing_guidance_signal": writing_guidance_signal,
        "note_media_signal": note_media_signal,
        "tone_signal": tone_signal,
        "meta_request_signal": meta_request_signal,
        "content_generation_signal": content_generation_signal,
        "prompt_detail_score": prompt_detail_score,
        "target_explicit": target_explicit,
        "prefer_prompt_topic": prefer_prompt_topic,
        "preferred_topic_statement": preferred_topic_statement,
        "prompt_audience_candidates": prompt_audience_candidates,
        "prompt_context_items": prompt_context_items,
        "ambiguity_detected": ambiguity_detected,
    }


def decide_need_question(
    *,
    article_type: str,
    user_prompt: str,
    source_count: int,
    source_chars: int,
    fact_score: int,
    answered: int = 0,
    source_excerpt: str = "",
) -> Dict[str, Any]:
    profile = derive_prompt_intent_profile(
        user_prompt,
        article_type,
        source_excerpt=source_excerpt,
    )
    article_key = str(article_type or "").strip().lower()
    prompt_detail_score = int(profile["prompt_detail_score"])
    target_explicit = bool(profile["target_explicit"])

    if bool(profile["ambiguity_detected"]):
        ask = True
        reason = "intent_ambiguous"
    elif bool(profile["prefer_prompt_topic"]) and source_count >= 2 and (source_chars >= 1000 or fact_score >= 5):
        ask = False
        reason = "prompt_intent_clear_company_intro"
    elif answered >= 2:
        ask = False
        reason = "already_answered"
    elif article_key == "announcement":
        enough_source = source_count >= 1 and (source_chars >= 900 or fact_score >= 6)
        enough_prompt = prompt_detail_score >= 2
        ask = not (enough_source and (target_explicit or enough_prompt))
        reason = "announcement_missing_detail" if ask else "announcement_sufficient_input"
    elif article_key in {"branding", "corporate_culture", "ai"}:
        enough_source = source_count >= 1 and (source_chars >= 700 or fact_score >= 5)
        enough_prompt = prompt_detail_score >= 3 or (prompt_detail_score >= 2 and target_explicit)
        ask = not (enough_source and enough_prompt)
        reason = "category_requires_clarification" if ask else "category_sufficient_input"
    else:
        ask = not (target_explicit and prompt_detail_score >= 2)
        reason = "default_needs_clarification" if ask else "default_sufficient_input"

    return {
        "ask": ask,
        "reason": reason,
        "source_chars": int(source_chars or 0),
        "source_count": int(source_count or 0),
        "fact_score": int(fact_score or 0),
        "prompt_detail_score": prompt_detail_score,
        "target_explicit": target_explicit,
        "primary_intent": str(profile["primary_intent"]),
        "prefer_prompt_topic": bool(profile["prefer_prompt_topic"]),
        "preferred_topic_statement": str(profile["preferred_topic_statement"] or ""),
        "ambiguity_detected": bool(profile["ambiguity_detected"]),
    }
