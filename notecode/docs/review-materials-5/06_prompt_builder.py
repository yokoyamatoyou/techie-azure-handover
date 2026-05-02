"""Prompt builders for the simple note pipeline."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, Mapping, Sequence

from note.prompt_sanitizer import sanitize_untrusted_text
from note.simple_note_pipeline.postprocess import DraftSections

_BLOCK_LIKE_RE = re.compile(r"^\[/?[A-Z_]+\]$")
_ARTICLE_STYLE_RULES = {
    "announcement": {
        "label": "お知らせ",
        "voice": "淡々としたビジネス文書寄り。誇張や感情語を抑え、変更点・時期・対象を明確にする。",
        "first_person": "一人称は原則使わない。必要でも最小限。",
        "structure": "冒頭で要点を示し、見出しごとに変更点・背景・対象者・今後の案内を整理する。",
    },
    "daily_story": {
        "label": "日々のできごと",
        "voice": "やさしく自然。出来事の説明だけで終えず、その場で引っかかった点、気持ちの揺れ、後から見えた学びを短く残す。",
        "first_person": "一人称は使ってよいが、段落冒頭で繰り返さない。",
        "structure": "起きたこと、引っかかり、見え直した意味、次に試すことが流れるようにつながる構成にする。",
    },
    "branding": {
        "label": "ブランディング",
        "voice": "紹介文として自然。宣伝の押しつけを避け、価値・背景・利用文脈を具体化する。",
        "first_person": "『私たち』『当社』『弊社』を段落ごとに立て直さない。必要なら会社名や主語省略を自然に使う。",
        "structure": "事業内容、導入時に重視すること、選ばれる理由、現場で大切にする姿勢を自然につなぐ。",
    },
    "case_study": {
        "label": "事例",
        "voice": "課題、対応、結果を具体的に整理する。一般論に逃げず、各見出しで状態変化か判断理由を残す。",
        "first_person": "一人称は抑え、事例の対象や状況を主語にする。",
        "structure": "改善前の迷い、組み替えた対応、途中で効いた工夫、結果、再現条件を順に置く。",
    },
    "industry_analysis": {
        "label": "業界分析",
        "voice": "平易だが薄くしない。背景、変化、示唆を具体化する。",
        "first_person": "一人称は原則不要。",
        "structure": "背景、現状、論点、示唆を整理する。",
    },
    "comparative_review": {
        "label": "比較レビュー",
        "voice": "比較軸を固定し、各見出しでは候補名より先に軸名を置き、少なくとも2候補を同じ軸で並べて差が出る理由を書く。勝者断定を急がない。",
        "first_person": "一人称は最小限。",
        "structure": "比較条件、価格や運用など軸ごとの差、向くケース、選ぶ前の確認点、結論を順に置き、候補ごとの紹介見出しは作らない。",
    },
    "explanatory_article": {
        "label": "解説",
        "voice": "平易で読みやすく、必要な専門性は残す。",
        "first_person": "一人称は原則不要。",
        "structure": "前提、判断軸、実務上の見方を順につなぎ、要点だけで畳まない。",
    },
}
_SEMANTIC_RULES = {
    "company_introduction": "企業紹介。会社概要の羅列ではなく、何をしていて、誰にどんな価値を出しているかを中心に書く。",
    "product_introduction": "製品紹介。機能列挙だけでなく、利用シーンと選定理由を入れる。",
    "activity_introduction": "取り組み紹介。目的、内容、意味合いが伝わるようにする。",
    "recruit_culture": "採用・カルチャー紹介。制度紹介の羅列を避け、働く文脈と価値観を自然に示す。",
    "announcement": "お知らせ。告知として必要な事実を優先する。",
    "implementation_case": "導入事例。顧客課題と導入後の変化を軸にする。",
    "improvement_case": "改善事例。改善前後の変化と学びを明確にする。",
    "incident_case": "トラブル・対応事例。事実関係と再発防止を明確にする。",
    "learning_case": "学びの事例。経験から得た視点を整理する。",
}
_TONE_RULES = {
    "calm": "落ち着いて解説する。感情を前に出しすぎず、判断しやすい整理を優先する。",
    "warm": "やさしく寄り添う。押しつけや断定を弱め、読者の迷いを受け止める。",
    "passionate": "熱意をにじませる。ただし演技的に盛り上げず、前向きさは具体例で示す。",
    "formal": "端正にまとめる。整ったビジネス文として簡潔に言い切る。",
    "auto": "記事タイプに合わせて自然な語り口を選ぶ。",
}
_HEADING_PROGRESS_RULES = {
    "case_study": "改善前→対応→工夫→結果→再現条件の順で進め、各見出しで変化か理由を1つ入れる。",
    "comparative_review": "比較条件→価格/運用/用途など軸差→向くケース→確認点→結論の順で進め、各見出しでは少なくとも2候補を同じ軸で並べて差の理由を1つ入れる。候補紹介だけの見出しは禁止。",
    "explanatory_article": "前提→判断軸→実務上の見方の順で進める。",
}
_SEMANTIC_HEADING_PROGRESS_RULES = {
    "company_introduction": "事業内容→導入時重視点→選ばれる理由→姿勢の順で進める。",
}
_COMPARATIVE_AXIS_KEYWORDS = (
    "価格",
    "運用体制",
    "導入負荷",
    "運用定着性",
    "移行コスト",
    "用途",
    "確認事項",
    "比較条件",
    "評価軸",
)
_COMPARATIVE_AXIS_ALIASES = {
    "price": "価格",
    "use_case": "用途",
    "approval_flow": "承認フロー",
    "governance": "ガバナンス",
    "review_flow": "レビューの流れ",
    "onboarding": "導入のしやすさ",
    "support_density": "サポートの厚み",
}
_COMPARATIVE_GOAL_RULES = {
    "fit_explain": "優劣を1位で決め切るより、条件別にどれが向くかを分けて説明する。",
    "organize": "勝ち負けを急がず、同じ軸で何が違うかを整理することを優先する。",
    "prioritize": "優先順位を付ける場合も、前提条件と例外を先に示してから結論を置く。",
}


def _normalize_inline_text(value: str, *, char_limit: int) -> str:
    text = sanitize_untrusted_text(str(value or ""), max_length=max(32, int(char_limit)))
    text = re.sub(r"\s+", " ", text).strip()
    if _BLOCK_LIKE_RE.match(text):
        text = f"data:{text}"
    return text


def _to_plain_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _clean_inline_text(value: Any, *, limit: int = 300) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _compact_topic_for_prompt(article_type: str, topic: Any) -> str:
    text = _clean_inline_text(topic or "", limit=180)
    if str(article_type or "").strip().lower() != "comparative_review":
        return text
    first_clause = re.split(r"[。！？!?]", text, maxsplit=1)[0].strip()
    return first_clause or text


def target_chars(length_mode: str, article_type: str) -> int:
    normalized = str(length_mode or "").strip().lower()
    if normalized == "short":
        return 1600 if article_type == "announcement" else 1800
    if normalized == "long":
        return 3800
    if normalized == "normal":
        return 2800
    return 2200 if article_type == "announcement" else 2600


def heading_target(length_mode: str, article_type: str = "", semantic_key: str = "") -> int:
    normalized = str(length_mode or "").strip().lower()
    if normalized == "short":
        if str(semantic_key or "").strip().lower() == "company_introduction":
            return 4
        return 3
    if normalized == "long":
        return 5
    return 4


def build_article_style_lines(contract: Mapping[str, Any]) -> list[str]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    tone_profile = str(contract.get("tone_profile") or "auto").strip().lower()
    base = _ARTICLE_STYLE_RULES.get(article_type, _ARTICLE_STYLE_RULES["explanatory_article"])
    instructions = [
        f"- 記事タイプ: {base['label']}",
        f"- 文体方針: {base['voice']}",
        f"- 主語方針: {base['first_person']}",
        f"- 構成方針: {base['structure']}",
        f"- トーン補足: {_TONE_RULES.get(tone_profile, _TONE_RULES['auto'])}",
    ]
    semantic_rule = _SEMANTIC_RULES.get(semantic_key)
    if semantic_rule:
        instructions.append(f"- ルート補足: {semantic_rule}")
    return instructions


def resolve_title_hint(contract: Mapping[str, Any]) -> str:
    article_type = str(contract.get("article_type") or "").strip().lower()
    prompt_topic = _clean_inline_text(contract.get("topic") or contract.get("prompt_raw") or "", limit=42)
    return prompt_topic or _ARTICLE_STYLE_RULES.get(article_type, _ARTICLE_STYLE_RULES["explanatory_article"])["label"]


def _clean_items(items: Iterable[str], *, limit: int = 6, char_limit: int = 160) -> list[str]:
    normalized: list[str] = []
    for item in items:
        text = _normalize_inline_text(str(item or ""), char_limit=char_limit)
        if not text:
            continue
        normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def _humanize_comparison_axis(value: Any) -> str:
    text = _normalize_inline_text(str(value or ""), char_limit=72)
    if not text:
        return ""
    lookup_key = re.sub(r"[\s\-]+", "_", text).lower()
    return _COMPARATIVE_AXIS_ALIASES.get(lookup_key, text)


def _normalize_style_lines(lines: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for line in lines:
        text = _normalize_inline_text(str(line or ""), char_limit=80)
        if text.startswith("- "):
            text = text[2:].strip()
        if text:
            normalized.append(text)
        if len(normalized) >= 4:
            break
    return normalized


def _append_block(buffer: list[str], title: str, lines: Sequence[str]) -> None:
    clean_lines = [sanitize_untrusted_text(str(line), max_length=400).strip() for line in lines if str(line).strip()]
    if not clean_lines:
        return
    if buffer:
        buffer.append("")
    buffer.append(f"[{title}]")
    buffer.extend(clean_lines)


def _repair_structure_guard_lines(body: str) -> list[str]:
    heading_count = len(re.findall(r"^##\s+", str(body or ""), flags=re.MULTILINE))
    if heading_count < 2:
        return []
    return [
        f"現在の見出し数{heading_count}本を下回らない。見出しだけ残す圧縮は禁止。",
        "見出し前の前置きは1段落までに抑え、主要論点は各見出しの本文で扱う。",
    ]


def _build_omission_repair_lines(diagnostics: Mapping[str, Any]) -> list[str]:
    if not bool(diagnostics.get("omission_repair_active")):
        return []
    if int(diagnostics.get("heading_reanchor_miss_count", 0) or 0) <= 0:
        return []
    headings: list[str] = []
    for item in _to_plain_list(diagnostics.get("omission_soft_warnings"))[:4]:
        text = str(item or "").strip()
        if not text.startswith("heading_reanchor:"):
            continue
        heading = text.split(":", 1)[1].strip()
        if heading and heading not in headings:
            headings.append(_clean_inline_text(heading, limit=32))
    lines = [
        "見出し直後の1文目では対象を短く再アンカーし、主語省略で誰の話か曖昧にしない。",
        "claim と anchor は保ち、補修は見出し冒頭2文の表層だけに限定する。",
    ]
    if headings:
        lines.append(f"再アンカー不足の見出し: {' / '.join(headings[:3])}")
    return lines


def _summarize_flagged_spans(flagged_spans: Iterable[Mapping[str, Any]] | None) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(flagged_spans or [], start=1):
        issue_type = _clean_inline_text(item.get("issue_type") or "", limit=24)
        section_heading = _clean_inline_text(item.get("section_heading") or "", limit=32)
        sentence_window = _clean_inline_text(item.get("sentence_window") or "", limit=32)
        if not issue_type:
            continue
        parts = [f"issue={issue_type}"]
        if section_heading:
            parts.append(f"section={section_heading}")
        if sentence_window:
            parts.append(f"window={sentence_window}")
        lines.append(f"span[{index}]=" + " / ".join(parts))
        if len(lines) >= 4:
            break
    return lines


def _build_heading_progress_rule(article_type: str, semantic_key: str) -> str:
    semantic_rule = _SEMANTIC_HEADING_PROGRESS_RULES.get(str(semantic_key or "").strip().lower())
    if semantic_rule:
        return semantic_rule
    return _HEADING_PROGRESS_RULES.get(str(article_type or "").strip().lower(), "見出しごとに別の観点を進める。")


def _resolve_comparison_axes(
    article_type: str,
    topic: str,
    comparison_axes: Iterable[str],
    must_cover: Iterable[str],
) -> list[str]:
    if str(article_type or "").strip().lower() != "comparative_review":
        return _clean_items(comparison_axes, limit=4, char_limit=72)
    merged: list[str] = []
    for item in comparison_axes:
        axis_label = _humanize_comparison_axis(item)
        if not axis_label or axis_label in merged:
            continue
        merged.append(axis_label)
        if len(merged) >= 4:
            break
    probe_text = " ".join(str(item or "") for item in [topic, *must_cover])
    for keyword in _COMPARATIVE_AXIS_KEYWORDS:
        if keyword in probe_text and keyword not in merged:
            merged.append(keyword)
        if len(merged) >= 4:
            break
    return merged[:4]


def _build_generation_blocks(
    *,
    article_type: str,
    semantic_key: str,
    target_chars: int,
    heading_target: int,
    speaker_profile: str,
    audience_profile: str,
    core_message: str,
    relationship_mode: str,
    topic: str,
    topic_probe: str,
    style_lines: Iterable[str],
    must_cover: Iterable[str],
    comparison_axes: Iterable[str],
    system_hints: Iterable[str],
    source_titles: Iterable[str],
    compare_goal_rule: str,
) -> Dict[str, list[str]]:
    comparison_items = _resolve_comparison_axes(article_type, topic_probe or topic, comparison_axes, must_cover)
    must_cover_items = _clean_items(must_cover, char_limit=72)
    hint_items = _clean_items(system_hints, limit=4, char_limit=72)
    source_title_items = _clean_items(source_titles, limit=4, char_limit=40)
    compact_style_lines = [
        line
        for line in _normalize_style_lines(style_lines)
        if line and not line.startswith("記事タイプ:")
    ]

    hard_contract_lines = [
        f"type={article_type or 'explanatory_article'} semantic={semantic_key or article_type or 'explanatory_article'}",
        f"speaker={speaker_profile or '自動判定'} / audience={audience_profile or '一般読者'} / relation={relationship_mode or 'guide'}",
        f"topic={topic or '未指定'}",
    ]
    if core_message:
        hard_contract_lines.append(f"core={core_message}")
    if must_cover_items:
        hard_contract_lines.append("must_cover=" + " / ".join(must_cover_items))
    if comparison_items:
        hard_contract_lines.append("compare=" + " / ".join(comparison_items))
    if hint_items:
        hard_contract_lines.append("hints=" + " / ".join(hint_items))

    structure_lines = [
        f"chars≈{target_chars} / headings≈{heading_target}",
        f"見出しは##のみ、{heading_target}本前後。H3なし。導入で主要論点を言い切らず、見出し前の前置きは1段落まで。{_build_heading_progress_rule(article_type, semantic_key)}",
        "2500字以上かつ見出し4本以上だけ## 目次。BODYにタイトル・タグ・CTAを書かない。",
    ]
    if article_type == "comparative_review":
        structure_lines.append("各見出しの冒頭で比較軸名を先に示し、2つ以上の候補を同じ軸で並べて差を書く。")
        structure_lines.append("sourceに具体名がない場合は、立ち上がり重視・運用定着重視・統制重視のようなタイプ名で比べ、候補A/Bのダミー表現を使わない。")
        if compare_goal_rule:
            structure_lines.append(compare_goal_rule)
        if source_title_items:
            structure_lines.append("candidates=" + " / ".join(source_title_items))

    style_block_lines = compact_style_lines or ["auto: 記事タイプに合わせて自然な語り口を選ぶ。"]

    return {
        "HARD_CONTRACT": hard_contract_lines,
        "STRUCTURE": structure_lines,
        "STYLE": style_block_lines,
    }


def _strip_code_fences(text: str) -> str:
    stripped = re.sub(r"^\s*`{3,}[^\S\n]*\S*[^\S\n]*\n", "", str(text or ""))
    stripped = re.sub(r"\n\s*`{3,}[^\S\n]*$", "", stripped)
    return stripped.strip()


def _summarize_compact_plan(compact_plan: Iterable[Mapping[str, Any]] | None) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(list(compact_plan or [])[:6], start=1):
        heading = _clean_inline_text(item.get("heading") or "", limit=40)
        purpose = _clean_inline_text(item.get("purpose") or "", limit=24)
        anchor = _clean_inline_text(item.get("anchor") or heading, limit=40)
        claim = _clean_inline_text(item.get("claim") or item.get("key_message") or "", limit=72)
        bridge = _clean_inline_text(item.get("bridge") or "", limit=48)
        do_not_cover = _clean_inline_text(item.get("do_not_cover") or "", limit=60)
        if not heading:
            continue
        parts = [f"plan[{index}]={heading}"]
        if purpose:
            parts.append(f"purpose={purpose}")
        if anchor:
            parts.append(f"anchor={anchor}")
        if claim:
            parts.append(f"claim={claim}")
        if bridge:
            parts.append(f"bridge={bridge}")
        if do_not_cover:
            parts.append(f"avoid={do_not_cover}")
        lines.append(" / ".join(parts))
    return lines


def _summarize_semantic_ledger(compact_plan: Iterable[Mapping[str, Any]] | None) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(list(compact_plan or [])[:6], start=1):
        heading = _clean_inline_text(item.get("heading") or "", limit=40)
        anchor = _clean_inline_text(item.get("anchor") or heading, limit=40)
        claim = _clean_inline_text(item.get("claim") or item.get("key_message") or "", limit=72)
        bridge = _clean_inline_text(item.get("bridge") or item.get("do_not_cover") or "", limit=48)
        if not heading or not claim:
            continue
        parts = [f"sem[{index}]={heading}"]
        parts.append(f"anchor={anchor or heading}")
        parts.append(f"claim={claim}")
        if bridge:
            parts.append(f"bridge={bridge}")
        lines.append(" / ".join(parts))
    return lines


def build_compact_plan_prompt_from_contract(contract: Mapping[str, Any], source_pack: Mapping[str, Any]) -> str:
    article_type = str(contract.get("article_type") or "").strip().lower() or "explanatory_article"
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower() or article_type
    length_mode = str(contract.get("length_mode") or "")
    must_cover = [str(item).strip() for item in _to_plain_list(contract.get("must_cover")) if str(item).strip()][:6]
    comparison_axes = [str(item).strip() for item in _to_plain_list(contract.get("comparison_axes")) if str(item).strip()][:4]
    system_hints = [str(item).strip() for item in _to_plain_list(contract.get("system_hint_items")) if str(item).strip()][:4]
    source_lines = _clean_items(
        [
            str(item.get("fact_text") or "")
            for item in list(source_pack.get("grounding_items") or [])[:6]
            if isinstance(item, Mapping)
        ],
        limit=6,
        char_limit=120,
    )
    if not source_lines:
        source_lines = _clean_items(
            [
                f"{item.get('title')}: {item.get('excerpt')}"
                for item in list(source_pack.get("source_summaries") or [])[:4]
                if isinstance(item, Mapping)
            ],
            limit=4,
            char_limit=120,
        )
    prompt_lines: list[str] = []
    _append_block(prompt_lines, "ROLE", ["note本文の前に compact semantic plan を作る。本文は書かず JSON だけを返す。"])
    _append_block(
        prompt_lines,
        "INPUT",
        [
            f"type={article_type} semantic={semantic_key}",
            f"topic={_clean_inline_text(contract.get('topic') or contract.get('prompt_raw') or '', limit=180) or '未指定'}",
            f"chars≈{target_chars(length_mode, article_type)} / headings≈{heading_target(length_mode, article_type, semantic_key)}",
            *([("must_cover=" + " / ".join(_clean_items(must_cover, char_limit=72)))] if must_cover else []),
            *([("compare=" + " / ".join(_resolve_comparison_axes(article_type, str(contract.get('topic') or ''), comparison_axes, must_cover)))] if comparison_axes or article_type == "comparative_review" else []),
            *([("hints=" + " / ".join(_clean_items(system_hints, limit=4, char_limit=72)))] if system_hints else []),
        ],
    )
    _append_block(prompt_lines, "SOURCE", source_lines or ["sourceなし"])
    _append_block(
        prompt_lines,
        "SCHEMA",
        [
            '{"sections":[{"heading":"見出し","purpose":"hook|problem|decision|closing","anchor":"その節で主語や対象になる中心語","claim":"その節で必ず言い切る意味","key_message":"writer向け補助メモ","bridge":"前節から受ける論点","do_not_cover":"この節で先回りしない論点"}]}',
        ],
    )
    _append_block(
        prompt_lines,
        "RULES",
        [
            "3〜6 sections。heading / purpose / anchor / claim / key_message / do_not_cover を全 section に入れる。bridge は必要な section だけ。",
            "purpose は structure の進行順が分かる短語にする。claim は意味を固定する短文にし、writer は wording を言い換えてよい。",
            "anchor は誰・何の話かが一読で分かる名詞句にする。bridge は前節から受ける論点を短く書く。",
            "do_not_cover には直前節で扱う論点か、次節へ回す論点を短く書く。",
            "JSON only.",
        ],
    )
    return "\n".join(prompt_lines).strip()


def parse_compact_plan_output(raw: str, *, max_sections: int) -> list[Dict[str, str]]:
    cleaned = _strip_code_fences(raw)
    if not cleaned:
        return []
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        return []
    try:
        payload = json.loads(match.group(0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    sections = payload.get("sections", []) if isinstance(payload, Mapping) else []
    if not isinstance(sections, list):
        return []
    parsed: list[Dict[str, str]] = []
    for item in sections:
        if not isinstance(item, Mapping):
            continue
        heading = _clean_inline_text(item.get("heading") or "", limit=48)
        purpose = _clean_inline_text(item.get("purpose") or "", limit=24)
        anchor = _clean_inline_text(item.get("anchor") or heading, limit=48)
        claim = _clean_inline_text(item.get("claim") or item.get("key_message") or "", limit=80)
        key_message = _clean_inline_text(item.get("key_message") or claim, limit=80)
        bridge = _clean_inline_text(item.get("bridge") or "", limit=60)
        do_not_cover = _clean_inline_text(item.get("do_not_cover") or "", limit=80)
        if not heading or not purpose or not claim:
            continue
        parsed.append(
            {
                "heading": heading,
                "purpose": purpose,
                "anchor": anchor or heading,
                "claim": claim,
                "key_message": key_message,
                "bridge": bridge,
                "do_not_cover": do_not_cover,
            }
        )
        if len(parsed) >= max(1, int(max_sections)):
            break
    return parsed


def build_generation_prompt(
    *,
    article_type: str,
    semantic_key: str,
    target_chars: int,
    heading_target: int,
    speaker_profile: str,
    audience_profile: str,
    core_message: str,
    relationship_mode: str,
    topic: str,
    topic_probe: str = "",
    style_lines: Iterable[str],
    must_cover: Iterable[str],
    comparison_axes: Iterable[str],
    system_hints: Iterable[str],
    source_titles: Iterable[str],
    source_facts: Iterable[str],
    source_excerpts: Iterable[str],
    compare_goal_rule: str = "",
    compact_plan: Iterable[Mapping[str, Any]] | None = None,
) -> str:
    prompt_lines: list[str] = []
    block_map = _build_generation_blocks(
        article_type=article_type,
        semantic_key=semantic_key,
        target_chars=target_chars,
        heading_target=heading_target,
        speaker_profile=speaker_profile,
        audience_profile=audience_profile,
        core_message=core_message,
        relationship_mode=relationship_mode,
        topic=topic,
        topic_probe=topic_probe or topic,
        style_lines=style_lines,
        must_cover=must_cover,
        comparison_axes=comparison_axes,
        system_hints=system_hints,
        source_titles=source_titles,
        compare_goal_rule=compare_goal_rule,
    )
    _append_block(
        prompt_lines,
        "ROLE",
        [
            "note向け日本語記事を一回で仕上げる編集者。自然さ優先、AIっぽい反復禁止。",
        ],
    )
    _append_block(
        prompt_lines,
        "HARD_CONTRACT",
        [
            "facts外の断定禁止。topicの語順をそのままなぞる導入を避け、主語・書き出し・言い換え反復を避け、1段落1〜4文で自然改行し、各見出しを1文で終えない。",
            *block_map["HARD_CONTRACT"],
        ],
    )
    structure_lines = list(block_map["STRUCTURE"])
    plan_lines = _summarize_compact_plan(compact_plan)
    semantic_lines = _summarize_semantic_ledger(compact_plan)
    if plan_lines:
        structure_lines = [*plan_lines, *structure_lines]
    _append_block(prompt_lines, "STRUCTURE", structure_lines)
    if semantic_lines:
        _append_block(
            prompt_lines,
            "SEMANTIC_LEDGER",
            [
                "claim は意味の固定。表現は言い換えてよいが、論点を落とさない。",
                "anchor は節の冒頭で一度だけ自然に示し、その後は曖昧になるときだけ再アンカーする。",
                "bridge は前節の論点を受けるが、同じ説明を繰り返さない。",
                *semantic_lines,
            ],
        )
    _append_block(prompt_lines, "STYLE", block_map["STYLE"])
    evidence_lines = _clean_items(source_facts, limit=10, char_limit=140)
    if not evidence_lines:
        evidence_lines = _clean_items(source_excerpts, limit=6, char_limit=140)
    _append_block(prompt_lines, "EVIDENCE", evidence_lines or ["sourceなし。未確認情報は膨らませない。"])
    _append_block(
        prompt_lines,
        "OUTPUT_SCHEMA",
        [
            "タグ以外を出さない。hashtagsは3〜5個。",
            "[TITLE]",
            "タイトル",
            "[/TITLE]",
            "[LEAD]",
            "120〜220字の導入文",
            "[/LEAD]",
            "[BODY]",
            "見出し付き本文",
            "[/BODY]",
            "[HASHTAGS]",
            "#タグ1 #タグ2 #タグ3",
            "[/HASHTAGS]",
        ],
    )
    return "\n".join(prompt_lines).strip()


def build_repair_prompt(
    *,
    article_type: str,
    issues: Iterable[str],
    title: str,
    lead: str,
    body: str,
    hashtags: str,
    semantic_ledger: Iterable[str] | None = None,
    flagged_spans: Iterable[Mapping[str, Any]] | None = None,
) -> str:
    issue_lines = _clean_items(issues, limit=6, char_limit=96) or ["重複・主語反復・文末単調を局所補修する。"]
    issue_lines.extend(_repair_structure_guard_lines(body))
    prompt_lines: list[str] = []
    _append_block(
        prompt_lines,
        "ROLE",
        [
            "元記事の事実と流れを保ったまま局所補修する。全文書き直し禁止。",
        ],
    )
    _append_block(
        prompt_lines,
        "ISSUES",
        [f"article_type={article_type or 'explanatory_article'}"] + issue_lines,
    )
    semantic_lines = _clean_items(semantic_ledger or [], limit=8, char_limit=120)
    if semantic_lines:
        _append_block(
            prompt_lines,
            "SEMANTIC_LEDGER",
            [
                "claim と anchor は保ち、直すのは表層だけ。見出しの意味役割を入れ替えない。",
                *semantic_lines,
            ],
        )
    flagged_span_lines = _summarize_flagged_spans(flagged_spans)
    if flagged_span_lines:
        _append_block(
            prompt_lines,
            "PATCH_SCOPE",
            [
                "変更は flag span と前後2文だけ。未指定箇所の意味・見出し順・節の役割は保つ。",
                *flagged_span_lines,
            ],
        )
    _append_block(
        prompt_lines,
        "SOURCE",
        [
            "[TITLE]",
            title,
            "[/TITLE]",
            "[LEAD]",
            lead,
            "[/LEAD]",
            "[BODY]",
            body,
            "[/BODY]",
            "[HASHTAGS]",
            hashtags,
            "[/HASHTAGS]",
        ],
    )
    _append_block(
        prompt_lines,
        "OUTPUT",
        [
            "同じタグ形式だけを返す。CTAや余計な要約を足さない。",
        ],
    )
    return "\n".join(prompt_lines).strip()


def build_generation_prompt_from_contract(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
    *,
    compact_plan: Iterable[Mapping[str, Any]] | None = None,
) -> str:
    if compact_plan is None:
        compact_plan = list(contract.get("_semantic_ledger") or []) if isinstance(contract.get("_semantic_ledger"), list) else None
    article_type = str(contract.get("article_type") or "").strip().lower() or "explanatory_article"
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower() or article_type
    length_mode = str(contract.get("length_mode") or "")
    must_cover = [str(item).strip() for item in _to_plain_list(contract.get("must_cover")) if str(item).strip()][:6]
    comparison_axes = [str(item).strip() for item in _to_plain_list(contract.get("comparison_axes")) if str(item).strip()][:4]
    system_hints = [str(item).strip() for item in _to_plain_list(contract.get("system_hint_items")) if str(item).strip()][:4]
    raw_topic = _clean_inline_text(contract.get("topic") or contract.get("prompt_raw") or "", limit=180)
    compact_topic = _compact_topic_for_prompt(article_type, raw_topic)
    ui_journey = contract.get("ui_journey") if isinstance(contract.get("ui_journey"), Mapping) else {}
    compare_goal_key = str(ui_journey.get("detail_key") or "").strip().lower()
    grounding_items = list(source_pack.get("grounding_items") or [])
    source_facts: list[str] = []
    for item in grounding_items[:10]:
        fact_text = sanitize_untrusted_text(str(item.get("fact_text") or ""), max_length=140)
        if not fact_text:
            continue
        bucket = _clean_inline_text(item.get("bucket") or "", limit=24)
        reference = _clean_inline_text(item.get("reference") or "", limit=72)
        fact_line = f"[{bucket}] {fact_text}" if bucket else fact_text
        if reference:
            fact_line = f"{fact_line} ({reference})"
        source_facts.append(fact_line)
    source_excerpts: list[str] = []
    source_titles: list[str] = []
    if not source_facts:
        for item in list(source_pack.get("source_summaries") or [])[:4]:
            title = sanitize_untrusted_text(str(item.get("title") or ""), max_length=48)
            excerpt = sanitize_untrusted_text(str(item.get("excerpt") or ""), max_length=120)
            if title and excerpt:
                source_excerpts.append(f"{title}: {excerpt}")
            elif excerpt:
                source_excerpts.append(excerpt)
            if title:
                source_titles.append(title)
    else:
        for item in list(source_pack.get("source_summaries") or [])[:4]:
            title = sanitize_untrusted_text(str(item.get("title") or ""), max_length=48)
            if title:
                source_titles.append(title)
    return build_generation_prompt(
        article_type=article_type,
        semantic_key=semantic_key,
        target_chars=target_chars(length_mode, article_type),
        heading_target=heading_target(length_mode, article_type, semantic_key),
        speaker_profile=_clean_inline_text(contract.get("speaker_profile") or "自動判定", limit=80),
        audience_profile=_clean_inline_text(contract.get("audience_profile") or "一般読者", limit=80),
        core_message=_clean_inline_text(contract.get("core_message") or "", limit=120),
        relationship_mode=_clean_inline_text(contract.get("relationship_mode") or "guide", limit=40),
        topic=compact_topic,
        topic_probe=raw_topic,
        style_lines=build_article_style_lines(contract),
        must_cover=must_cover,
        comparison_axes=comparison_axes,
        system_hints=system_hints,
        source_titles=source_titles,
        source_facts=source_facts,
        source_excerpts=source_excerpts,
        compare_goal_rule=_COMPARATIVE_GOAL_RULES.get(compare_goal_key, ""),
        compact_plan=compact_plan,
    )


def build_repair_prompt_from_diagnostics(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Mapping[str, Any],
    *,
    compact_plan: Iterable[Mapping[str, Any]] | None = None,
    flagged_spans: Iterable[Mapping[str, Any]] | None = None,
) -> str:
    issues = [str(item) for item in list(diagnostics.get("repair_instructions") or []) if str(item).strip()]
    issues.extend(_build_omission_repair_lines(diagnostics))
    if not issues:
        issues = ["重複と主語反復を減らし、段落の流れを自然にする。"]
    article_type = str(contract.get("article_type") or "").strip().lower() or "explanatory_article"
    effective_plan = compact_plan
    if effective_plan is None and isinstance(contract.get("_semantic_ledger"), list):
        effective_plan = list(contract.get("_semantic_ledger") or [])
    effective_flagged_spans = flagged_spans
    if effective_flagged_spans is None and isinstance(diagnostics.get("flagged_spans"), list):
        effective_flagged_spans = list(diagnostics.get("flagged_spans") or [])
    return build_repair_prompt(
        article_type=article_type,
        issues=issues,
        title=draft.title,
        lead=draft.lead,
        body=draft.body,
        hashtags=draft.hashtags,
        semantic_ledger=_summarize_semantic_ledger(effective_plan),
        flagged_spans=effective_flagged_spans,
    )
