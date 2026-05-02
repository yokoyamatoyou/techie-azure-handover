"""Build a compact, writer-facing brief from the UI-resolved contract."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping


_CORPORATE_SELF_REFERENCES = {"私たち", "当社", "弊社"}


def _clean_text(value: Any, *, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def _ensure_sentence(text: Any, *, limit: int = 120) -> str:
    cleaned = _clean_text(text, limit=limit).strip(" 　")
    if not cleaned:
        return ""
    if cleaned[-1] not in "。！？":
        cleaned = f"{cleaned}。"
    return cleaned


def _dedupe(items: Iterable[Any], *, limit: int) -> List[str]:
    kept: List[str] = []
    for item in items:
        text = _clean_text(item)
        if not text or text in kept:
            continue
        kept.append(text)
        if len(kept) >= limit:
            break
    return kept


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _is_company_introduction(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    return article_type == "branding" and semantic_key == "company_introduction"


def _normalized_allowed_pronouns(contract: Mapping[str, Any]) -> List[str]:
    return [
        str(item or "").strip()
        for item in _to_plain_list(contract.get("allowed_pronouns"))
        if str(item or "").strip()
    ][:4]


def _focus_bundle(contract: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(contract.get("focus_bundle") or {})


def _main_focus(contract: Mapping[str, Any]) -> str:
    focus_bundle = _focus_bundle(contract)
    for candidate in (
        focus_bundle.get("main_focus"),
        contract.get("topic_statement"),
        contract.get("core_message"),
        contract.get("topic"),
        contract.get("prompt_raw"),
    ):
        text = _clean_text(candidate, limit=72)
        if text:
            return text
    return ""


def _support_points(contract: Mapping[str, Any]) -> List[str]:
    focus_bundle = _focus_bundle(contract)
    points = _dedupe(focus_bundle.get("support_points") or [], limit=2)
    if points:
        return points
    return _dedupe(contract.get("must_cover") or [], limit=2)


def _is_longform_explanatory(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    return article_type == "explanatory_article" and length_mode in {"normal", "long"}


def _source_documents(contract: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    return [item for item in _to_plain_list(contract.get("source_documents")) if isinstance(item, Mapping)]


def _is_long_single_source_explanatory(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type != "explanatory_article":
        return False
    documents = _source_documents(contract)
    if len(documents) != 1:
        return False
    content = str(documents[0].get("content") or "")
    return len(content) >= 4000


def _looks_like_source_outline_focus(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    if re.search(r"(エグゼクティブサマリー|背景と問題の所在|目的と構成|章|節)", value):
        return True
    if value.lstrip().startswith(("#", "*", "-", "・")):
        return True
    return bool(re.fullmatch(r"\d+(?:[.．]\d+)*\s*.{1,32}", value))


def _grounding_items(contract: Mapping[str, Any], source_pack: Mapping[str, Any]) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    for item in _to_plain_list(source_pack.get("grounding_items")):
        if isinstance(item, Mapping):
            candidates.append(dict(item))
    if candidates:
        return candidates
    for item in _to_plain_list(contract.get("source_grounding_items")):
        if isinstance(item, Mapping):
            candidates.append(dict(item))
    return candidates


def _split_sentences(text: Any, *, limit: int) -> List[str]:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if not cleaned:
        return []
    chunks = re.split(r"(?<=[。！？])\s*", cleaned)
    sentences: List[str] = []
    for chunk in chunks:
        sentence = _clean_text(chunk, limit=limit)
        if not sentence:
            continue
        sentences.append(sentence)
        if len(sentences) >= 3:
            break
    return sentences


def _fallback_digest_candidates(contract: Mapping[str, Any], source_pack: Mapping[str, Any]) -> List[str]:
    candidates: List[str] = []
    for item in _to_plain_list(contract.get("source_documents")):
        if not isinstance(item, Mapping):
            continue
        for sentence in _split_sentences(item.get("content") or "", limit=120):
            if sentence and sentence not in candidates:
                candidates.append(sentence)
            if len(candidates) >= 6:
                return candidates
    for item in _to_plain_list(source_pack.get("source_summaries")):
        if not isinstance(item, Mapping):
            continue
        excerpt = _clean_text(item.get("excerpt") or "", limit=120)
        if excerpt and excerpt not in candidates:
            candidates.append(excerpt)
        if len(candidates) >= 6:
            return candidates
    return candidates[:6]


def _clean_explanatory_source_text(value: Any, *, limit: int = 140) -> str:
    text = _clean_text(value, limit=limit + 24)
    text = text.replace(r"\*\*", "**")
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"^[#>\-*・\s]+", "", text)
    text = re.sub(r"^\d+(?:[.．]\d+)*\s*", "", text)
    text = re.sub(r"^(?:分析結果|解釈|背景|目的|要旨|概要)\s*[:：]\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip(" 　-・、。")
    if not text:
        return ""
    if len(text) > limit:
        clipped = text[:limit].rstrip(" 　、")
        last_stop = max(clipped.rfind("。"), clipped.rfind("！"), clipped.rfind("？"))
        if last_stop >= 48:
            clipped = clipped[: last_stop + 1]
        text = clipped
    trailing_fragment = re.search(r"。(?:これ|この|その|また|さらに)$", text)
    if trailing_fragment:
        text = text[: trailing_fragment.start() + 1]
    return text


def _explanatory_source_chunks(contract: Mapping[str, Any]) -> List[str]:
    chunks: List[str] = []
    for document in _source_documents(contract):
        content = str(document.get("content") or "")
        for raw_part in re.split(r"[\r\n]+|(?<=[。！？])\s*", content):
            raw = str(raw_part or "").strip()
            if not raw or raw.startswith("#"):
                continue
            text = _clean_explanatory_source_text(raw, limit=140)
            if not text or text in chunks:
                continue
            if len(text) < 12 and not re.search(r"(AI|LLM|DX|UX|SEO|API|[0-9])", text):
                continue
            chunks.append(text)
    return chunks


def _explanatory_pick(
    candidates: Iterable[str],
    pattern: str,
    used: set[str],
    *,
    prefer_later: bool = False,
) -> str:
    regex = re.compile(pattern, re.IGNORECASE)
    matches: List[tuple[int, int, str]] = []
    for index, candidate in enumerate(candidates):
        text = _clean_explanatory_source_text(candidate, limit=140)
        if not text or text in used or not regex.search(text):
            continue
        if not prefer_later:
            used.add(text)
            return text
        score = len(text)
        score += min(index, 80)
        matches.append((-score, index, text))
    if not matches:
        return ""
    matches.sort()
    selected = matches[0][2]
    used.add(selected)
    return selected


def _explanatory_digest_candidates(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
    items: List[Dict[str, str]],
) -> List[str]:
    raw_candidates: List[str] = []
    for item in items:
        raw_text = str(item.get("fact_text") or "")
        if raw_text.strip().startswith("#"):
            continue
        text = _clean_explanatory_source_text(raw_text, limit=140)
        if text and text not in raw_candidates:
            raw_candidates.append(text)
    for text in _fallback_digest_candidates(contract, source_pack):
        cleaned = _clean_explanatory_source_text(text, limit=140)
        if cleaned and cleaned not in raw_candidates:
            raw_candidates.append(cleaned)
    for text in _explanatory_source_chunks(contract):
        if text not in raw_candidates:
            raw_candidates.append(text)

    used: set[str] = set()
    ordered = [
        _explanatory_pick(
            raw_candidates,
            r"(なぜ.*AIっぽ|AI生成テキスト.*感じ|不気味の谷|言語学的|認知科学)",
            used,
        ),
        _explanatory_pick(
            raw_candidates,
            r"(違和感|不自然|認知|負荷|予測|読み手|単調|平板)",
            used,
            prefer_later=True,
        ),
        _explanatory_pick(
            raw_candidates,
            r"(Evenness|Dispersion|Disparity|Variety-Repetition|Volume|Abundance|ユニークな単語|名詞化|現在分詞|文末|です・ます|バースト)",
            used,
        ),
        _explanatory_pick(
            raw_candidates,
            r"(堆積した文体|Sedimented Style|RLHF|instruction tuning|テンプレート)",
            used,
        ),
        _explanatory_pick(
            raw_candidates,
            r"(日本語|文末|です・ます|明示性|Markdown|箇条書き|テンプレート)",
            used,
            prefer_later=True,
        ),
    ]
    for text in raw_candidates:
        if len([item for item in ordered if item]) >= 6:
            break
        if text and text not in used:
            ordered.append(text)
            used.add(text)
    return _dedupe([item for item in ordered if item], limit=6)


def _web_trace_digest_candidates(contract: Mapping[str, Any]) -> List[str]:
    if str(contract.get("source_mode") or "").strip().lower() != "web":
        return []
    candidates: List[str] = []
    for item in _to_plain_list(contract.get("source_trace")):
        if not isinstance(item, Mapping):
            continue
        exact_date = _clean_text(item.get("exact_date") or "", limit=16)
        excerpt = _clean_text(item.get("excerpt") or "", limit=96)
        publisher = _clean_text(item.get("publisher") or "", limit=36)
        if not exact_date or not excerpt:
            continue
        if publisher:
            candidates.append(f"{exact_date}時点で、{publisher}では{excerpt}")
        else:
            candidates.append(f"{exact_date}時点で、{excerpt}")
        if len(candidates) >= 6:
            break
    return candidates[:6]


def _general_digest_candidates(items: List[Dict[str, str]]) -> List[str]:
    ordered: List[str] = []
    for bucket_name in ("overview", "strength", "other", "history"):
        for item in items:
            if str(item.get("bucket") or "").strip() != bucket_name:
                continue
            fact_text = _clean_text(item.get("fact_text") or "", limit=120)
            if fact_text and fact_text not in ordered:
                ordered.append(fact_text)
    for item in items:
        fact_text = _clean_text(item.get("fact_text") or "", limit=120)
        if fact_text and fact_text not in ordered:
            ordered.append(fact_text)
    return ordered[:6]


def _company_intro_digest_candidates(items: List[Dict[str, str]]) -> List[str]:
    overview: List[str] = []
    strength: List[str] = []
    history: List[str] = []
    other: List[str] = []
    for item in items:
        fact_text = _clean_text(item.get("fact_text") or "", limit=120)
        bucket = str(item.get("bucket") or "").strip().lower()
        if not fact_text:
            continue
        if bucket == "overview":
            overview.append(fact_text)
        elif bucket == "strength":
            strength.append(fact_text)
        elif bucket == "history":
            history.append(fact_text)
        else:
            other.append(fact_text)
    ordered = [*overview[:3], *strength[:2]]
    if history:
        ordered.append(f"背景として、{history[0]}")
    for item in other:
        if len(ordered) >= 6:
            break
        if item not in ordered:
            ordered.append(item)
    return _dedupe(ordered, limit=6)


def _comparative_digest_candidates(items: List[Dict[str, str]]) -> List[str]:
    by_title: List[str] = []
    seen_titles: set[str] = set()
    for item in items:
        fact_text = _clean_text(item.get("fact_text") or "", limit=120)
        title = _clean_text(item.get("source_title") or "", limit=32)
        if not fact_text:
            continue
        if title and title not in seen_titles:
            seen_titles.add(title)
            by_title.append(fact_text)
    if len(by_title) >= 3:
        return by_title[:4]
    return _general_digest_candidates(items)[:4]


def _build_source_digest(contract: Mapping[str, Any], source_pack: Mapping[str, Any]) -> List[str]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    source_mode = str(contract.get("source_mode") or "").strip().lower()
    if article_type == "daily_story" and source_mode == "prompt_only":
        return []
    web_trace_candidates = _web_trace_digest_candidates(contract)
    if web_trace_candidates:
        return [_ensure_sentence(item, limit=128) for item in web_trace_candidates if _ensure_sentence(item, limit=128)][:6]
    items = _grounding_items(contract, source_pack)
    if not items:
        fallback_candidates = _fallback_digest_candidates(contract, source_pack)
        if fallback_candidates:
            return [_ensure_sentence(item, limit=128) for item in fallback_candidates if _ensure_sentence(item, limit=128)][:6]
        must_cover = _dedupe(contract.get("must_cover") or [], limit=3)
        return [_ensure_sentence(f"{must_cover[0]}を外さない。", limit=120)] if must_cover else []
    if _is_company_introduction(contract):
        candidates = _company_intro_digest_candidates(items)
    elif article_type == "comparative_review":
        candidates = _comparative_digest_candidates(items)
    elif _is_long_single_source_explanatory(contract):
        candidates = _explanatory_digest_candidates(contract, source_pack, items)
    else:
        candidates = _general_digest_candidates(items)
    return [_ensure_sentence(item, limit=128) for item in candidates if _ensure_sentence(item, limit=128)][:6]


def build_explanatory_source_use_digest(contract: Mapping[str, Any], source_pack: Mapping[str, Any]) -> List[str]:
    if not _is_long_single_source_explanatory(contract):
        return []
    return _explanatory_digest_candidates(contract, source_pack, _grounding_items(contract, source_pack))


def _build_task_sentence(contract: Mapping[str, Any]) -> str:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    audience = _clean_text(contract.get("audience_profile") or "読者", limit=32) or "読者"
    main_focus = _main_focus(contract)
    if semantic_key == "company_introduction":
        return f"{audience}が、この会社の今の事業と支え方を自然に読み取れる会社紹介にする。"
    if article_type == "branding":
        return f"{audience}が、価値の背景と現場の工夫を読み物として追えるブランド記事にする。"
    if article_type == "announcement":
        return f"{audience}が、変更点と必要な行動を迷わず追える告知記事にする。"
    if article_type == "case_study":
        return f"{audience}が、課題から再現条件まで順に追える事例記事にする。"
    if article_type == "comparative_review":
        return f"{audience}が、比較軸ごとの差と向く条件を同じ順番で追える比較記事にする。"
    if article_type == "daily_story":
        return f"{audience}が、出来事から学びまで自然に入れる日常記事にする。"
    if article_type == "industry_analysis":
        return f"{audience}が、市場の前提と差分を判断材料として読める分析記事にする。"
    if article_type == "explanatory_article":
        if _is_long_single_source_explanatory(contract) and _looks_like_source_outline_focus(main_focus):
            return f"{audience}が、資料の核になる問い・具体例・注意点を自然に追える解説記事にする。"
        focus = main_focus or "前提と判断軸"
        if _is_longform_explanatory(contract):
            return f"{audience}が、{focus}を今どこから判断するかまで2000〜3000字帯で自然に追える解説記事にする。"
        return f"{audience}が、{focus}を実務の判断材料として読める解説記事にする。"
    return f"{audience}が、{main_focus or '主要論点'}を自然に追える記事にする。"


def _build_core_message(contract: Mapping[str, Any]) -> str:
    explicit = _clean_text(contract.get("core_message") or "", limit=100)
    if explicit:
        return _ensure_sentence(explicit, limit=108)
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    support_points = _support_points(contract)
    if semantic_key == "company_introduction":
        return "今の事業と導入初期を支える姿勢を先に示し、歩みは背景として後ろに回す。"
    if article_type == "comparative_review":
        return "順位づけより、比較軸ごとの差と向く条件を先に示す。"
    if article_type == "case_study":
        return "成功談の総括ではなく、何を直し何が変わったかと再現条件を残す。"
    if article_type == "announcement":
        return "対象者が迷わないよう、対象・時期・確認事項を混ぜずに整理する。"
    if article_type == "daily_story":
        return "出来事の説明だけで終えず、その場の引っかかりから学びへつなぐ。"
    if article_type == "explanatory_article" and _is_long_single_source_explanatory(contract):
        return "章順の要約ではなく、説明対象、読者のつまずき、具体例、注意点を読み手の順番に組み替える。"
    if article_type == "explanatory_article" and _is_longform_explanatory(contract):
        return "問いに短い結論を先に置き、背景、判断軸、実務での使い方、次の確認点へ流す。"
    if support_points:
        joined = "、".join(support_points[:2])
        return _ensure_sentence(f"{joined}が自然につながる流れを優先する", limit=108)
    return _ensure_sentence(_main_focus(contract) or "主要論点を自然につなぐ", limit=108)


def _build_voice_policy(contract: Mapping[str, Any]) -> str:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    self_reference_policy = str(contract.get("self_reference_policy") or "").strip().lower()
    allowed_pronouns = _normalized_allowed_pronouns(contract)
    preferred_pronoun = next((item for item in allowed_pronouns if item in _CORPORATE_SELF_REFERENCES), "")
    if semantic_key == "company_introduction":
        if preferred_pronoun == "私たち" or self_reference_policy == "watashitachi":
            return "neutral explainer を基本にし、社名を一人称にせず、必要な自己参照だけ『私たち』を使う。"
        return "neutral explainer を基本にし、社名を一人称にせず、会社の説明主体として落ち着いて書く。"
    if article_type == "branding" and preferred_pronoun == "私たち":
        return "neutral explainer を基本にし、自己参照が必要な場面だけ『私たち』を使う。"
    if article_type == "daily_story":
        return "体験者の視点で書いてよいが、『私』を段落頭で繰り返さない。"
    if article_type == "case_study":
        return "neutral narrator を基本にし、一人称は必要な箇所だけに絞る。"
    if article_type == "announcement":
        return "neutral formal を基本にし、一人称は原則使わない。"
    if article_type == "explanatory_article":
        return "neutral explainer を基本にし、書き手指定は文体の距離感だけに使う。構成と具体例は資料の論点から決める。"
    return "neutral explainer を基本にし、説明主体を前に出しすぎない。"


def _build_style_hints(contract: Mapping[str, Any]) -> List[str]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    shared = "短い段落と中くらいの段落を混ぜ、同じ主語や書き出しを続けない。"
    if semantic_key == "company_introduction":
        return [
            "lead は事業か判断軸から入り、沿革や抽象的な理念から始めない。",
            "社名の反復を抑え、歩みは必要な背景として後半で短く触れる。",
        ]
    if article_type == "branding":
        return [
            "lead は価値の背景か読者の迷いから入り、パンフレットの定型句を避ける。",
            shared,
        ]
    if article_type == "announcement":
        return [
            "1文1要件を優先し、対象・時期・確認事項を混ぜない。",
            "見出しごとに役割を分け、案内文を感情語で膨らませない。",
        ]
    if article_type == "case_study":
        return [
            "課題、対応、変化、再現条件の順で進め、成功談の総括だけで閉じない。",
            shared,
        ]
    if article_type == "comparative_review":
        return [
            "比較軸を先に置き、順位語より向く条件を先に書く。",
            "タイトルと lead は『比較軸』をそのまま見出し語にせず、選び方・見分け方・向く条件から入る。",
        ]
    if article_type == "daily_story":
        if str(contract.get("source_mode") or "").strip().lower() == "prompt_only":
            return [
                "1行テーマは素材メモとして扱い、統計・価格・法務・医療・金融・比較優位・会社実績を足さない。",
                "出来事、言葉のズレ、次に変える一つの行動へ自然に戻す。",
            ]
        return [
            "出来事、引っかかり、学びの順で進め、説明だけで畳まない。",
            shared,
        ]
    if article_type == "industry_analysis":
        return [
            "lead は論点か判断条件から入り、レポートの要約文で始めない。",
            "市場の前提、差分、示唆を混ぜずに進める。",
        ]
    if article_type == "explanatory_article" and _is_long_single_source_explanatory(contract):
        return [
            "長い単一資料は章順に要約せず、問い、つまずき、具体例、注意点の順へ組み替える。",
            "source の用語を見出し名に丸写しせず、各節に一つずつ自然に置く。",
            shared,
        ]
    if article_type == "explanatory_article" and _is_longform_explanatory(contract):
        return [
            "導入は問いか引っかかりから入り、2文目までに短い結論を置く。『この記事では』を定型句にしない。",
            "背景、判断軸、実務の使い方、まとめで役割差を作り、全部を同じ密度で説明しない。",
            "各見出しの冒頭を『〜が重要です』『〜が必要です』でそろえず、問いや判断の分かれ目から入る。",
        ]
    return [
        "lead は論点か場面から入り、『この記事では』で始めない。",
        shared,
    ]


def build_distilled_prompt_brief(contract: Mapping[str, Any], source_pack: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "task_sentence": _ensure_sentence(_build_task_sentence(contract), limit=108),
        "core_message": _build_core_message(contract),
        "source_digest": _build_source_digest(contract, source_pack),
        "voice_policy": _ensure_sentence(_build_voice_policy(contract), limit=108),
        "style_hints": [_ensure_sentence(item, limit=108) for item in _build_style_hints(contract)],
    }


__all__ = ["build_distilled_prompt_brief", "build_explanatory_source_use_digest"]
