"""Prompt builders for the simple note pipeline."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, Mapping, Sequence

from note.natural_blog_core import build_note4000_style_profile
from note.newalgorithm_pipeline.legal_postcheck import build_legal_rewrite_guard_lines
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
        "voice": "比較軸を固定し、各見出しでは候補名より先に軸名を置き、少なくとも2候補を同じ軸で並べて差が出る理由を書く。勝者断定を急がない。導入で『A、B、Cはいずれも〜ですが』のような横並び要約を置かず、先に判断条件を置く。",
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
    "branding": "ブランド記事。会社紹介の雛形に寄せすぎず、読者が抱える迷い、価値の背景、判断材料を自然につなぐ。",
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
    "calm": {
        "summary": "落ち着いて解説する。感情を前に出しすぎず、判断しやすい整理を優先する。",
        "rhythm": "文のテンポは安定寄り。短文連打より、論点を静かにつなぐ。",
        "stance": "評価語は控えめにし、『〜と整理できます』寄りで落ち着かせる。",
        "distance": "共感の言葉を前に出しすぎず、先に状況整理と判断材料を置く。",
        "body": "本文中盤では、各節の冒頭で前提か理由を先に置き、そのあとに確認点を静かに並べる。",
        "section_opening": "各見出しの1文目は『〜が前提になります』『〜を先に見ておく必要があります』のように、判断条件から入る。",
        "title": "タイトルは判断軸や論点を先に出し、煽りや感情語を入れすぎない。",
        "lead": "導入は問題設定か判断条件から入り、読者への呼びかけより先に論点整理を置く。",
    },
    "warm": {
        "summary": "やさしく寄り添う。押しつけや断定を弱め、読者の迷いを受け止める。",
        "rhythm": "節の入りで迷い・負担を受け止めてから説明へ進む。",
        "stance": "『〜しておくと安心です』『〜しやすいです』の柔らかい言い方を混ぜる。",
        "distance": "命令調を避け、伴走する距離で話しかける。",
        "body": "本文中盤では、各節の冒頭で『迷いやすい』『止まりやすい』場面を短く受け止めてから、判断材料へつなぐ。",
        "section_opening": "各見出しの1文目は『ここで迷いやすいのは〜です』『導入初期は〜で止まりやすいです』のように、負担の受け止めから入ってよい。",
        "title": "タイトルは結論だけで閉じず、読者が抱えやすい迷いか確認点をやわらかくにじませる。",
        "lead": "導入1文目で迷い・負担を受け止め、そのあとに整理すると見通しが立つ流れへつなぐ。",
    },
    "passionate": {
        "summary": "熱意をにじませる。ただし演技的に盛り上げず、前向きさは具体例で示す。",
        "rhythm": "短めの文を時々入れて推進力を出すが、せかしすぎない。",
        "stance": "熱量は感嘆ではなく、変化の手応えや具体動作で見せる。",
        "distance": "背中を押す語りにしても、誇張や煽りは避ける。",
        "title": "タイトルは前向きな変化や進め方を示してよいが、誇張表現で強引に押し出さない。",
        "lead": "導入は動き出す価値を先に示しつつ、勢いだけで押し切らず具体の変化で支える。",
    },
    "formal": {
        "summary": "端正にまとめる。整ったビジネス文として簡潔に言い切る。",
        "rhythm": "結論→理由→補足の順で端的に進め、余談を挟まない。",
        "stance": "くだけた相づちや情緒語を抑え、です・ますを整える。",
        "distance": "読者への呼びかけは最小限にし、事実と判断を先に置く。",
        "body": "本文中盤では、各節で要件か判断を先に述べ、続けて理由と補足を短く添える。",
        "section_opening": "各見出しの1文目は『〜が重要です』『〜を確認する必要があります』のように、要件を明確に言い切る。",
        "title": "タイトルは論点と目的を簡潔に置き、比喩や会話調を避ける。",
        "lead": "導入は必要性か判断理由を先に言い切り、短めの文で整然と始める。",
    },
    "auto": {
        "summary": "記事タイプに合わせて自然な語り口を選ぶ。",
        "rhythm": "",
        "stance": "",
        "distance": "",
        "body": "",
        "section_opening": "",
        "title": "",
        "lead": "",
    },
}
_PARAGRAPH_BREAK_GUIDANCE = {
    "value_or_scene_shift": "価値説明・具体場面・判断材料の役割が切り替わるところでだけ段落を変える。",
    "structure_or_metric_shift": "市場構造・根拠・指標・示唆の役割が切り替わるところで段落を変える。",
    "criteria_or_usecase_shift": "比較条件・評価軸・用途別結論の役割が切り替わるところで段落を変える。",
    "phase_shift": "課題・進行・工夫・結果・再現条件の役割が切り替わるところで段落を変える。",
    "scene_or_feeling_shift": "出来事・感覚・気づきの役割が切り替わるところで段落を変える。",
    "fact_or_action_shift": "変更点・影響・確認事項・行動の役割が切り替わるところで段落を変える。",
    "example_or_reason_shift": "理由・具体例・補足の役割が切り替わるところで段落を変える。",
    "topic_or_role_shift": "話題か役割が切り替わるところで段落を変える。",
}
_ENDING_DISTRIBUTION_GUIDANCE = {
    "brand_narrative_mix": "抽象まとめだけで閉じず、同じ感想語尾を続けない。",
    "analytic_formal_mix": "判断文の型を固定せず、説明の同型反復を避ける。",
    "comparison_formal_mix": "同じ比較断定を続けず、条件付きの言い切りを混ぜる。",
    "case_process_mix": "結果文だけに寄せず、変化と条件の閉じ方を混ぜる。",
    "reflective_mix": "内省語尾を固定せず、余韻の型をずらす。",
    "notice_formal": "案内文は曖昧にぼかさず、確認事項を明瞭に閉じる。",
    "explanatory_mix": "説明の同型反復を避け、断定と留保の型を混ぜる。",
    "balanced": "同じ終わり方を続けず、段落ごとに閉じ方の型をずらす。",
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
    "performance": "性能",
    "use_case": "用途",
    "safety": "安全性",
    "overall": "総合",
    "initial_setup": "初期設定",
    "approval_flow": "承認フロー",
    "governance": "ガバナンス",
    "review_flow": "レビューの流れ",
    "review_lightness": "レビューの軽さ",
    "onboarding": "導入のしやすさ",
    "support_density": "サポートの厚み",
    "ownership": "担当責任の置き方",
    "auditability": "監査のしやすさ",
}
_COMPARATIVE_GOAL_RULES = {
    "fit_explain": "優劣を1位で決め切るより、条件別にどれが向くかを分けて説明する。",
    "organize": "勝ち負けを急がず、同じ軸で何が違うかを整理することを優先する。",
    "prioritize": "優先順位を付ける場合も、前提条件と例外を先に示してから結論を置く。",
}
_EXPERIMENTAL_STAGE_MODEL_CONFIG = {
    "support": {"model": "gpt-5.4-nano", "reasoning_effort": "low"},
    "planner": {"model": "gpt-5.4-mini", "reasoning_effort": "medium"},
    "writer": {"model": "gpt-5.4-mini", "reasoning_effort": "medium"},
    "editor": {"model": "gpt-5.4-mini", "reasoning_effort": "medium"},
    "legal": {"model": "gpt-5.4-mini", "reasoning_effort": "low"},
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


def target_chars(length_mode: str, article_type: str, *, source_count: int = 0) -> int:
    normalized = str(length_mode or "").strip().lower()
    normalized_article_type = str(article_type or "").strip().lower()
    source_count = max(0, int(source_count or 0))
    if normalized == "short":
        return 1400 if normalized_article_type == "announcement" else 1800
    if normalized == "long":
        return 3800
    if normalized == "normal":
        if normalized_article_type == "announcement":
            return 2000
        if normalized_article_type == "explanatory_article" and source_count >= 3:
            return 3200
        return 2800
    if normalized_article_type == "announcement":
        if source_count >= 3:
            return 1400
        if source_count >= 2:
            return 1250
        return 1100
    if normalized_article_type == "explanatory_article":
        if source_count >= 4:
            return 3400
        if source_count >= 3:
            return 3200
        if source_count >= 2:
            return 2900
        return 2400
    if normalized_article_type == "branding":
        return 2800 if source_count >= 3 else 2400
    return 2900 if source_count >= 3 else 2500


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
    source_count = len(_to_plain_list(contract.get("source_documents")))
    base = _ARTICLE_STYLE_RULES.get(article_type, _ARTICLE_STYLE_RULES["explanatory_article"])
    tone_rule = _TONE_RULES.get(tone_profile, _TONE_RULES["auto"])
    structure_line = base["structure"]
    if article_type == "branding" and semantic_key == "branding":
        structure_line = "読者が抱えやすい迷い、価値の背景、判断の基準、続けやすさにつながる根拠を自然につなぐ。"
    instructions = [
        f"- 記事タイプ: {base['label']}",
        f"- 文体方針: {base['voice']}",
        f"- 主語方針: {base['first_person']}",
        f"- 構成方針: {structure_line}",
        f"- トーン補足: {tone_rule['summary']}",
    ]
    if tone_rule.get("rhythm"):
        instructions.append(f"- 温度感リズム: {tone_rule['rhythm']}")
    if tone_rule.get("stance"):
        instructions.append(f"- 温度感スタンス: {tone_rule['stance']}")
    if tone_rule.get("distance"):
        instructions.append(f"- 温度感距離: {tone_rule['distance']}")
    if tone_rule.get("body"):
        instructions.append(f"- 温度感本文: {tone_rule['body']}")
    if tone_rule.get("section_opening"):
        instructions.append(f"- 温度感節冒頭: {tone_rule['section_opening']}")
    if tone_rule.get("title"):
        instructions.append(f"- 温度感タイトル: {tone_rule['title']}")
    if tone_rule.get("lead"):
        instructions.append(f"- 温度感導入: {tone_rule['lead']}")
    if article_type == "announcement":
        instructions.append("- 文長方針: お知らせは1文1要件を優先し、短めの文で切る。説明を足すときも冗長に伸ばさない。")
    elif article_type == "explanatory_article" and source_count >= 3:
        instructions.append("- 文長方針: 複数資料の解説では短文だけに寄せず、判断理由をつなぐやや長めの文も混ぜて厚みを出す。")
    else:
        instructions.append("- 文長方針: 短文・中文・やや長めを混ぜ、全段落を同じテンポにそろえない。")
    semantic_rule = _SEMANTIC_RULES.get(semantic_key)
    if semantic_rule:
        instructions.append(f"- ルート補足: {semantic_rule}")
    instructions.extend(_build_natural_profile_style_lines(contract))
    return instructions


def _resolve_prompt_style_profile_mode(article_type: str, tone_profile: str) -> str:
    if tone_profile == "warm":
        return "casual"
    if tone_profile in {"formal", "calm"} or article_type == "announcement":
        return "formal"
    return "balanced"


def _build_natural_profile_style_lines(contract: Mapping[str, Any]) -> list[str]:
    article_type = str(contract.get("article_type") or "explanatory_article").strip().lower() or "explanatory_article"
    tone_profile = str(contract.get("tone_profile") or "auto").strip().lower() or "auto"
    focus = str(contract.get("writing_focus") or "auto").strip().lower() or "auto"
    register_policy = dict(contract.get("register_policy") or {})
    base_register = str(register_policy.get("base_register") or "polite").strip().lower() or "polite"
    style_profile = build_note4000_style_profile(
        article_type=article_type,
        focus=focus,
        tone_profile=tone_profile,
        style_profile=_resolve_prompt_style_profile_mode(article_type, tone_profile),
        base_register=base_register,
    )
    preferred_endings = [str(item or "").strip() for item in list(style_profile.preferred_endings or []) if str(item or "").strip()]
    preferred_endings = [ending.rstrip("。") for ending in preferred_endings[:4]]
    preferred_text = "・".join(preferred_endings) if preferred_endings else "です・ます"
    max_same_ending = int(register_policy.get("max_consecutive_same_ending", 2) or 2)
    paragraph_break_line = _PARAGRAPH_BREAK_GUIDANCE.get(
        str(style_profile.paragraph_break_policy or ""),
        "意味役割が切り替わるところでだけ段落を変える。",
    )
    ending_line = _ENDING_DISTRIBUTION_GUIDANCE.get(
        str(style_profile.ending_distribution_hint or ""),
        "同じ終わり方を続けず、文末の型を固定しない。",
    )
    return [
        (
            f"- 改行リズム: 1段落{int(style_profile.paragraph_min)}〜{int(style_profile.paragraph_max)}文を目安にしつつ固定せず、"
            "短い段落と少し厚い段落を混ぜる。"
        ),
        f"- 段落切替: {paragraph_break_line}",
        f"- 文末運用: 主文末は {preferred_text} を回し、{ending_line}",
        f"- 連続制約: 同じ文末を{max_same_ending}回までに抑え、3回以上続けない。",
    ]


def _normalize_generation_system_hints(
    article_type: str,
    semantic_key: str,
    system_hints: Iterable[str],
) -> list[str]:
    hint_items = _clean_items(system_hints, limit=4, char_limit=72)
    if article_type != "branding" or semantic_key != "branding":
        return hint_items
    filtered = [
        item
        for item in hint_items
        if item not in {
            "会社紹介として、背景・提供価値・信頼材料を自然につなぐ。",
            "まず存在と利用場面を迷わず理解できる構成にする。",
        }
    ]
    if "ブランド記事として、迷いが生まれる場面と判断材料を自然につなぐ。" not in filtered:
        filtered.insert(0, "ブランド記事として、迷いが生まれる場面と判断材料を自然につなぐ。")
    return filtered[:4]


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
        text = _normalize_inline_text(str(line or ""), char_limit=140)
        if text.startswith("- "):
            text = text[2:].strip()
        if text:
            normalized.append(text)
        if len(normalized) >= 18:
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


def _build_compare_patch_scope_lines(
    article_type: str,
    flagged_spans: Iterable[Mapping[str, Any]] | None,
) -> list[str]:
    if str(article_type or "").strip().lower() != "comparative_review":
        return []
    headings: list[str] = []
    for item in flagged_spans or []:
        if str(item.get("issue_type") or "").strip() != "comparative_thin_section":
            continue
        heading = _clean_inline_text(item.get("section_heading") or "", limit=32)
        if heading and heading not in headings:
            headings.append(heading)
    if not headings:
        return []
    return [
        "comparative_patch=repair only the span-specified heading and keep every other section unchanged",
        "comparative_patch=keep the same comparison axis and candidate pairing, and expand the thin section into 2-3 sentences",
        "comparative_patch=do not add new winner claims, new candidates, or new comparison axes",
        "target_headings=" + " / ".join(headings[:4]),
    ]


def _uses_experimental_prompt_stack(contract: Mapping[str, Any]) -> bool:
    return str(contract.get("body_generation_experiment") or "").strip().lower() == "experimental_prompt_stack"


def _build_experimental_comparative_repair_guard_lines(contract: Mapping[str, Any]) -> list[str]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type != "comparative_review" or not _uses_experimental_prompt_stack(contract):
        return []
    raw_topic = _clean_inline_text(
        contract.get("topic") or contract.get("prompt_raw") or contract.get("topic_statement") or "",
        limit=180,
    )
    must_cover = [str(item).strip() for item in _to_plain_list(contract.get("must_cover")) if str(item).strip()][:6]
    comparison_axes = [
        str(item).strip() for item in _to_plain_list(contract.get("comparison_axes")) if str(item).strip()
    ][:4]
    resolved_axes = _resolve_comparison_axes(article_type, raw_topic, comparison_axes, must_cover)
    guard_lines = [
        "comparative_echo=結論節を直す場合でも、topic や prompt_raw の言い回しをそのまま再掲しない。",
        "comparative_echo=比較条件の説明文を closing へ持ち込まず、結論では軸差と向く運用だけを短くまとめ直す。",
    ]
    if resolved_axes:
        guard_lines.append(
            "comparative_echo=結論節を直す場合は、"
            + " / ".join(resolved_axes[:3])
            + " を同じ順番で見比べる要約に戻し、別軸へ言い換えない。"
        )
    if "複数部門" in raw_topic:
        joined_axes = "・".join(resolved_axes[:3]) if len(resolved_axes) >= 3 else "と".join(resolved_axes[:2])
        if joined_axes:
            guard_lines.append(
                "comparative_closing_seed="
                + f"結論では、{joined_axes}を同じ順番で見比べると、部門横断運用で何を優先するかが整理しやすくなります。"
            )
    return guard_lines[:4]


def _extract_flagged_headings(
    flagged_spans: Iterable[Mapping[str, Any]] | None,
    *,
    issue_type: str,
) -> list[str]:
    headings: list[str] = []
    for item in flagged_spans or []:
        if str(item.get("issue_type") or "").strip() != issue_type:
            continue
        heading = _clean_inline_text(item.get("section_heading") or "", limit=32)
        if heading and heading not in headings:
            headings.append(heading)
    return headings[:4]


def _filter_section_shadow_lines(
    section_shadow_lines: Iterable[str] | None,
    target_headings: Iterable[str] | None,
) -> list[str]:
    headings = [str(item or "").strip() for item in target_headings or [] if str(item or "").strip()]
    if not headings:
        return _clean_items(section_shadow_lines or [], limit=4, char_limit=140)
    filtered: list[str] = []
    for line in section_shadow_lines or []:
        text = str(line or "").strip()
        if not text:
            continue
        section_heading = text.split("=", 1)[1].split(" / ", 1)[0].strip() if "=" in text else ""
        if section_heading in headings:
            filtered.append(_clean_inline_text(text, limit=140))
        if len(filtered) >= 4:
            break
    return filtered


def _build_shadow_patch_scope_lines(flagged_spans: Iterable[Mapping[str, Any]] | None) -> list[str]:
    headings = _extract_flagged_headings(flagged_spans, issue_type="shadow_section_drift")
    if not headings:
        return []
    return [
        "shadow_patch=repair only the span-specified heading and keep every other section unchanged",
        "shadow_patch=restore the listed focus and claim in the opening 1-2 sentences, then keep the same section role",
        "shadow_patch=do not add new headings, new examples, or a new conclusion outside the target span",
        "target_headings=" + " / ".join(headings[:4]),
    ]


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


def _build_company_intro_structure_lines(
    speaker_profile: str,
    audience_profile: str,
) -> list[str]:
    audience = audience_profile or "読者"
    speaker = str(speaker_profile or "").strip()
    if speaker == "自動判定":
        speaker = ""
    speaker_line = (
        "会社紹介の記事として、"
        f"{audience} が全体像をつかみやすい距離で書く。"
        "書き手の役割語は前面に出さず、文体の距離感だけを整える。"
        "役割語を本文へ不自然に差し込まない。"
    )
    if speaker:
        speaker_line = (
            f"会社紹介の記事として、{audience} が全体像をつかみやすい距離で書く。"
            f"{speaker} の立場は文体の手がかりとして使い、役割語を本文へ不自然に差し込まない。"
        )
    return [
        speaker_line,
        "会社紹介では、事業内容だけで終えず、会社が何を重視し、どのような価値を届けようとしているかを1〜2箇所は具体で見せる。",
        "『運営側』『運営担当として』『広報として見ると』のような役割語を説明の都合で本文に露出させず、source にない限り『運営』も便利語として安易に置かない。会社紹介として自然な主語や言い回しへ言い換える。",
        "lead は『会社の輪郭が自然に伝わるよう』『背景と具体を行き来しながら』のような編集メモ調の定型句で始めず、会社の判断軸か事業の見え方から入る。",
        "各節の文量と改行をそろえすぎず、短い段落と少し厚い段落を混ぜて、均一な説明カードの並びに見せない。",
        "導入や締めはやや短め、判断材料や支え方を説明する節はやや厚めでもよい。全節を同じ分量・同じ改行数でそろえない。",
        "『だからこそ』『たとえば』を便利なつなぎとして各節で繰り返さない。同じ接続の出し方を連続させない。",
        "『輪郭』『強みがあります』『と捉えています』のような抽象まとめ語だけで段落を閉じず、事実・条件・動作で閉じる段落も混ぜる。",
    ]


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
    hint_items = _normalize_generation_system_hints(article_type, semantic_key, system_hints)
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
        "全見出しを同じ厚みで並べず、短めの節・中くらいの節・厚めの節を混ぜる。全節を1段落固定にしない。",
    ]
    if semantic_key == "company_introduction":
        structure_lines.extend(_build_company_intro_structure_lines(speaker_profile, audience_profile))
    if article_type == "comparative_review":
        structure_lines.append("各見出しの冒頭で比較軸名を先に示し、2つ以上の候補を同じ軸で並べて差を書く。")
        structure_lines.append("sourceに具体名がない場合は、立ち上がり重視・運用定着重視・統制重視のようなタイプ名で比べ、候補A/Bのダミー表現を使わない。")
        structure_lines.append("導入1段落で候補名を横並びに要約しない。最初の2文は比較条件か判断基準から入り、『いずれも〜ですが』の型を避ける。")
        structure_lines.append("『第一候補』『最有力』『一番向く』『最もおすすめ』のような順位語は避け、『候補に入りやすい』『合いやすい』のように条件付きで書く。")
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


def _collect_source_prompt_material(source_pack: Mapping[str, Any]) -> Dict[str, list[str]]:
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
    return {
        "source_facts": source_facts,
        "source_excerpts": source_excerpts,
        "source_titles": source_titles,
    }


def _extract_grounded_source_titles(source_pack: Mapping[str, Any]) -> list[str]:
    grounded_titles: list[str] = []
    for item in list(source_pack.get("grounding_items") or [])[:10]:
        reference = _clean_inline_text(item.get("reference") or "", limit=120)
        if not reference:
            continue
        title = reference.split(" / ", 1)[0].strip()
        if title and title not in grounded_titles:
            grounded_titles.append(title)
    return grounded_titles


def _build_experimental_support_source_lines(source_pack: Mapping[str, Any]) -> list[str]:
    source_material = _collect_source_prompt_material(source_pack)
    support_lines: list[str] = []
    for line in list(source_material.get("source_facts") or [])[:8]:
        text = _clean_inline_text(line, limit=180)
        if text and text not in support_lines:
            support_lines.append(text)
    grounded_titles = set(_extract_grounded_source_titles(source_pack))
    for item in list(source_pack.get("source_summaries") or [])[:6]:
        title = sanitize_untrusted_text(str(item.get("title") or ""), max_length=48)
        excerpt = sanitize_untrusted_text(str(item.get("excerpt") or ""), max_length=120)
        if not title and not excerpt:
            continue
        if title and title in grounded_titles:
            continue
        if title and excerpt:
            summary_line = f"[summary] {title}: {excerpt}"
        elif excerpt:
            summary_line = f"[summary] {excerpt}"
        else:
            summary_line = f"[summary] {title}"
        text = _clean_inline_text(summary_line, limit=180)
        if text and text not in support_lines:
            support_lines.append(text)
    if support_lines:
        return support_lines[:8]
    return source_material["source_excerpts"][:4] or ["sourceなし。未確認の情報は足さない。"]


def _build_experimental_ui_slot_lines(contract: Mapping[str, Any]) -> list[str]:
    article_type = str(contract.get("article_type") or "").strip().lower() or "explanatory_article"
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower() or article_type
    tone_profile = str(contract.get("tone_profile") or "auto").strip().lower() or "auto"
    content_goal = str(contract.get("content_goal") or "auto").strip().lower() or "auto"
    writing_focus = str(contract.get("writing_focus") or "auto").strip().lower() or "auto"
    speaker_profile = _clean_inline_text(contract.get("speaker_profile") or "自動判定", limit=80)
    audience_profile = _clean_inline_text(contract.get("audience_profile") or "一般読者", limit=80)
    core_message = _clean_inline_text(contract.get("core_message") or "", limit=120)
    raw_topic = _clean_inline_text(
        contract.get("topic") or contract.get("prompt_raw") or contract.get("topic_statement") or "",
        limit=160,
    )
    comparison_axes = [
        str(item).strip() for item in _to_plain_list(contract.get("comparison_axes")) if str(item).strip()
    ][:4]
    normalized_comparison_axes = _resolve_comparison_axes(
        article_type,
        raw_topic,
        comparison_axes,
        _to_plain_list(contract.get("must_cover")),
    )
    ui_lines = [
        f"article_type={article_type}",
        f"semantic_article_key={semantic_key}",
        f"tone_profile={tone_profile}",
        f"content_goal={content_goal}",
        f"writing_focus={writing_focus}",
        f"speaker_profile={speaker_profile}",
        f"audience_profile={audience_profile}",
    ]
    if core_message:
        ui_lines.append(f"core_message={core_message}")
    if raw_topic:
        ui_lines.append(f"topic={raw_topic}")
    if normalized_comparison_axes:
        ui_lines.append("comparison_axes=" + " / ".join(normalized_comparison_axes))
    return ui_lines


def _build_experimental_comparative_stage_lines(
    contract: Mapping[str, Any],
    *,
    source_titles: Sequence[str],
) -> Dict[str, list[str]]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type != "comparative_review":
        return {}
    raw_topic = _clean_inline_text(
        contract.get("topic") or contract.get("prompt_raw") or contract.get("topic_statement") or "",
        limit=180,
    )
    comparison_axes = [
        str(item).strip() for item in _to_plain_list(contract.get("comparison_axes")) if str(item).strip()
    ][:4]
    must_cover = [str(item).strip() for item in _to_plain_list(contract.get("must_cover")) if str(item).strip()][:6]
    resolved_axes = _resolve_comparison_axes(article_type, raw_topic, comparison_axes, must_cover)
    compare_goal_key = ""
    ui_journey = contract.get("ui_journey")
    if isinstance(ui_journey, Mapping):
        compare_goal_key = str(ui_journey.get("detail_key") or "").strip().lower()
    stage_lines: Dict[str, list[str]] = {}
    if resolved_axes:
        joined_axes = " / ".join(resolved_axes)
        common_line = f"比較軸は {joined_axes} を固定し、price や導入負荷など別の汎用軸へすり替えない。"
        stage_lines["support"] = [
            common_line,
            "section_briefs は比較条件、軸差、向くケース、確認点、結論のどれを担う節かが分かるように並べる。",
        ]
        stage_lines["planner"] = [
            common_line,
            f"sections の must_cover には {joined_axes} のどれを扱う節かを明記し、同じ軸を別 section に再利用しない。",
        ]
        stage_lines["writer"] = [
            common_line,
            "比較条件→軸差→向くケース→確認点→結論の流れを守り、候補紹介だけの section を作らない。",
        ]
        stage_lines["editor"] = [
            "draft が contract 外の汎用軸へずれた場合だけ、比較軸を contract 指定へ戻す局所修正を行う。",
        ]
    if not source_titles:
        no_source_lines = [
            "sourceに具体サービス名がないため、候補A/B/Cや実名の捏造は禁止。",
            "承認段階を細かく分けたい運用、部門ごとに担当責任を明確にしたい運用、監査記録を追いやすくしたい運用のように、運用タイプ名で比べる。",
        ]
        for stage_name in ("support", "planner", "writer", "editor"):
            stage_lines.setdefault(stage_name, []).extend(no_source_lines)
    compare_goal_rule = _COMPARATIVE_GOAL_RULES.get(compare_goal_key, "")
    if compare_goal_rule:
        for stage_name in ("support", "planner", "writer", "editor"):
            stage_lines.setdefault(stage_name, []).append(compare_goal_rule)
    return stage_lines


def _build_experimental_overlap_guard_lines(article_type: str, semantic_key: str) -> list[str]:
    normalized_article_type = str(article_type or "").strip().lower()
    normalized_semantic_key = str(semantic_key or "").strip().lower() or normalized_article_type
    lines = [
        "各見出しは役割を一つずつずらし、同じ結論の言い換えを別節で繰り返さない。",
        "前節で説明した理由を次節で繰り返さず、次節では判断・実務・条件のどれを進めるかを明示する。",
        "見出し同士の重複が出そうな場合は、新情報のない節を増やさず既存節へ統合する。",
    ]
    if normalized_article_type == "comparative_review":
        lines.append("比較記事では軸ごとに節を分け、同じ比較軸を別見出しで再利用しない。")
    elif normalized_semantic_key == "company_introduction":
        lines.append("会社紹介では事業説明と価値説明を混線させず、同じ強みの言い換えを節分けしない。")
    elif normalized_article_type == "explanatory_article":
        lines.append("解説記事では前提・判断軸・実務の見方を分け、同じ要点の再説明で節数を稼がない。")
    return lines


def _build_writer_stylometry_guard_lines(article_type: str, tone_profile: str) -> list[str]:
    normalized_article_type = str(article_type or "").strip().lower()
    normalized_tone_profile = str(tone_profile or "auto").strip().lower() or "auto"
    lines = [
        "段落長をそろえすぎない。短め・中くらい・やや厚めを混ぜ、全節を同じ厚みで並べない。",
        "文の長さもそろえすぎない。短く切る文と、理由をつなぐやや長めの文を混ぜる。",
        "一文だけの独立段落を連続させない。短い段落の直後は2〜3文の段落を挟む。",
        "各見出しの1文目の始め方を変え、同じ接続詞や同じ主語で連続開始しない。",
        "topic や core_message をそのまま導入でなぞらず、自然な言い換えか状況描写から入る。",
        "抽象語だけで段落を閉じず、source にある固有名詞・運用条件・判断材料を本文に散らす。",
        "一人称は必要な箇所だけ使い、段落冒頭や連続文で『私』『私たち』『当社』『弊社』を立て続けに出さない。",
        "主語は日本語として自然な範囲で省略してよいが、誰の経験や判断かが消えるほど削りすぎない。",
        "『重要です』『大切です』だけで終わる低情報文を連打せず、各段落に事実・条件・判断理由の少なくとも1つを置く。",
        "『だからこそ』『たとえば』のような接続の便利語を節ごとに置かない。同じつなぎは近い段落で反復しない。",
        "『輪郭』『強み』『価値』の抽象語を連呼して節を前に進めた気にならず、固有名詞か具体動作を1つ混ぜる。",
    ]
    if normalized_article_type == "announcement":
        lines.append("お知らせでは人間味を無理に足さず、簡潔さを優先する。ただし同じ定型句の連打は避ける。")
    elif normalized_article_type == "daily_story":
        lines.append("体験記事では短文を混ぜてよいが、感想の連打だけで節を埋めず、出来事と気づきを往復させる。")
    elif normalized_article_type == "branding":
        lines.append("紹介文では会社名や『当社』を段落冒頭で反復せず、価値説明と支援姿勢を交互に見せる。")
    if normalized_tone_profile == "formal":
        lines.append("formal は端正に保つが、『〜が重要です』だけを見出しごとに繰り返さない。")
    elif normalized_tone_profile == "warm":
        lines.append("warm は寄り添いを入れてよいが、『迷いやすい』『安心』の同語反復は避ける。")
    elif normalized_tone_profile == "passionate":
        lines.append("passionate は勢いを出してよいが、感嘆や断定の連打ではなく、変化の手触りで熱量を出す。")
    return lines


def _build_editor_stylometry_guard_lines(article_type: str, tone_profile: str) -> list[str]:
    normalized_article_type = str(article_type or "").strip().lower()
    normalized_tone_profile = str(tone_profile or "auto").strip().lower() or "auto"
    lines = [
        "以下の違和感を局所補修対象とする: 段落長の均一化、見出し冒頭の反復、同じ文末の連打、抽象語だけの段落、同じ結論の言い換え重複。",
        "文長が均一な箇所は、短く切る文と少し長くつなぐ文を混ぜて呼吸を戻す。",
        "修正は span 単位にとどめ、section の役割と source grounding は保つ。",
        "改行は自然な意味の切れ目でだけ変える。見た目のためだけに空段落を増やさない。",
        "人間らしさは『崩すこと』ではなく『均一さを減らすこと』として扱う。",
        "一人称の出しすぎは局所的に間引き、会社名や自然な主語省略へ置き換えてよい。ただし視点主を別人に変えない。",
        "主語を省略しすぎて誰の判断か曖昧な文だけは最小限に主語を戻す。全文で主語を立て直し続けない。",
        "抽象評価だけの低情報文が続く箇所は、事実・条件・理由を1つ足して密度を戻す。全面的な書き換えはしない。",
        "『だからこそ』『たとえば』『私たちが』のような繰り返しやすい出だしは、近い段落で重なったぶんだけ間引く。",
    ]
    if normalized_article_type == "announcement":
        lines.append("announcement は簡潔さを優先し、硬めでもよい。単調な定型の連打だけを抑える。")
    else:
        lines.append("お知らせ以外では、説明カードの連続に見える均一な節運びを避ける。")
    if normalized_tone_profile == "formal":
        lines.append("formal は硬さを残してよいが、同じ判断表現の反復は別の構文へ散らす。")
    elif normalized_tone_profile == "warm":
        lines.append("warm は距離感を残しつつ、過剰な共感テンプレややさしさの定型句を削る。")
    return lines


def build_experimental_dynamic_hint_bundle(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    article_type = str(contract.get("article_type") or "").strip().lower() or "explanatory_article"
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower() or article_type
    tone_profile = str(contract.get("tone_profile") or "auto").strip().lower() or "auto"
    tone_rule = _TONE_RULES.get(tone_profile, _TONE_RULES["auto"])
    source_material = _collect_source_prompt_material(source_pack)
    source_anchor_lines = source_material["source_facts"][:4] or source_material["source_excerpts"][:3]
    return {
        "opening_strategy": tone_rule.get("lead") or "導入は論点整理から始める。",
        "title_intent": tone_rule.get("title") or "タイトルは topic の繰り返しではなく論点を短く示す。",
        "body_temperature": tone_rule.get("body") or "本文中盤では節ごとに別の判断材料を進める。",
        "section_opening": tone_rule.get("section_opening") or "各見出しの1文目でその節の役割を明確にする。",
        "empathy_distance": tone_rule.get("distance") or "読み手との距離は記事タイプに合わせて自然に保つ。",
        "sentence_rhythm": tone_rule.get("rhythm") or "文のテンポは記事タイプに合わせて自然に変える。",
        "source_usage": (
            "各節で source grounding を1つ以上使い、source にない一般論で節を埋めない。"
            if source_anchor_lines
            else "source が薄い場合でも未確認の断定や水増しはしない。"
        ),
        "overlap_guard": _build_experimental_overlap_guard_lines(article_type, semantic_key),
        "source_anchor_examples": list(source_anchor_lines),
    }


def _build_experimental_stage_prompt(
    *,
    role_lines: Sequence[str],
    ui_slot_lines: Sequence[str],
    dynamic_hint_bundle: Mapping[str, Any],
    source_lines: Sequence[str],
    task_lines: Sequence[str],
    output_lines: Sequence[str],
) -> str:
    prompt_lines: list[str] = []
    _append_block(prompt_lines, "ROLE", role_lines)
    _append_block(prompt_lines, "UI_SLOTS", list(ui_slot_lines))
    dynamic_lines = [
        f"opening_strategy={_clean_inline_text(dynamic_hint_bundle.get('opening_strategy') or '', limit=140)}",
        f"title_intent={_clean_inline_text(dynamic_hint_bundle.get('title_intent') or '', limit=140)}",
        f"body_temperature={_clean_inline_text(dynamic_hint_bundle.get('body_temperature') or '', limit=140)}",
        f"section_opening={_clean_inline_text(dynamic_hint_bundle.get('section_opening') or '', limit=140)}",
        f"empathy_distance={_clean_inline_text(dynamic_hint_bundle.get('empathy_distance') or '', limit=140)}",
        f"sentence_rhythm={_clean_inline_text(dynamic_hint_bundle.get('sentence_rhythm') or '', limit=140)}",
        f"source_usage={_clean_inline_text(dynamic_hint_bundle.get('source_usage') or '', limit=140)}",
    ]
    dynamic_lines.extend(
        f"overlap_guard[{idx}]={_clean_inline_text(line, limit=140)}"
        for idx, line in enumerate(dynamic_hint_bundle.get("overlap_guard") or [], start=1)
        if str(line or "").strip()
    )
    _append_block(prompt_lines, "DYNAMIC_HINTS", dynamic_lines)
    _append_block(prompt_lines, "SOURCE_GROUNDING", source_lines)
    _append_block(prompt_lines, "TASK", task_lines)
    _append_block(prompt_lines, "OUTPUT", output_lines)
    return "\n".join(prompt_lines).strip()


def build_experimental_prompt_stack_from_contract(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    article_type = str(contract.get("article_type") or "").strip().lower() or "explanatory_article"
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower() or article_type
    tone_profile = str(contract.get("tone_profile") or "auto").strip().lower() or "auto"
    ui_slot_lines = _build_experimental_ui_slot_lines(contract)
    dynamic_hint_bundle = build_experimental_dynamic_hint_bundle(contract, source_pack)
    source_material = _collect_source_prompt_material(source_pack)
    support_source_lines = _build_experimental_support_source_lines(source_pack)
    comparative_stage_lines = _build_experimental_comparative_stage_lines(
        contract,
        source_titles=source_material["source_titles"],
    )
    support_focus_lines: list[str] = []
    if article_type == "branding" or semantic_key == "company_introduction":
        support_focus_lines.extend(
            [
                "branding では価値観だけでなく、日々の運用姿勢や見直し方が分かる source を最低1つは独立した brief に割り当てる。",
                "具体例は顧客事例に限らず、問い合わせ振り返り・手順改善・導線見直しなど source にある内部運用例で満たしてよい。",
            ]
        )
    writer_stylometry_lines = _build_writer_stylometry_guard_lines(article_type, tone_profile)
    editor_stylometry_lines = _build_editor_stylometry_guard_lines(article_type, tone_profile)
    writer_output_lines = [
        "タグ以外を出さない。",
        "[TITLE] / [/TITLE]",
        "[LEAD] / [/LEAD]",
        "[BODY] / [/BODY]",
        "[HASHTAGS] / [/HASHTAGS]",
    ]
    stack = {
        "ui_slots": {
            "article_type": article_type,
            "semantic_article_key": semantic_key,
            "tone_profile": tone_profile,
            "speaker_profile": _clean_inline_text(contract.get("speaker_profile") or "自動判定", limit=80),
            "audience_profile": _clean_inline_text(contract.get("audience_profile") or "一般読者", limit=80),
            "core_message": _clean_inline_text(contract.get("core_message") or "", limit=120),
        },
        "dynamic_hint_bundle": dynamic_hint_bundle,
    }
    stack["support"] = {
        **_EXPERIMENTAL_STAGE_MODEL_CONFIG["support"],
        "prompt": _build_experimental_stage_prompt(
            role_lines=[
                "複数 source を writer が使いやすい脚本へ変換する support/script 担当。",
                "本文は書かず、読者・核メッセージ・節ごとの fact anchor を薄い handoff JSON に整える。",
            ],
            ui_slot_lines=ui_slot_lines,
            dynamic_hint_bundle=dynamic_hint_bundle,
            source_lines=support_source_lines,
            task_lines=[
                "source はそのまま writer に渡さず、読者に必要な論点だけを section ごとに整理する。",
                "複数 source がある場合は、重複を畳み、何が核事実で何が重複かを分けてから節ごとへ再配置する。",
                "source_digest は全文要約ではなく、重複除去済みの核事実束として返す。",
                "section_briefs では heading ごとに、この節で使う fact_anchor、why_it_matters、混ぜない論点 do_not_mix を必ず明示する。",
                "writer が迷わないように、reader / core_message / source_digest / section_briefs / writing_cautions を JSON で返す。",
                *support_focus_lines,
                *comparative_stage_lines.get("support", []),
            ],
            output_lines=[
                '{"reader":"...", "core_message":"...", "source_digest":["..."], "section_briefs":[{"heading":"...", "section_focus":"...", "fact_anchor":"...", "why_it_matters":"...", "do_not_mix":"..."}], "writing_cautions":["..."]}',
            ],
        ),
    }
    stack["planner"] = {
        **_EXPERIMENTAL_STAGE_MODEL_CONFIG["planner"],
        "prompt": _build_experimental_stage_prompt(
            role_lines=[
                "source と UI 指定から重複のない section plan を作る planner。",
                "各節は役割をずらし、同じ結論の言い換えを別 section にしない。",
            ],
            ui_slot_lines=ui_slot_lines,
            dynamic_hint_bundle=dynamic_hint_bundle,
            source_lines=[],
            task_lines=[
                "support/script の結果は <SCRIPT_JSON>...</SCRIPT_JSON> に入る想定。",
                "section 数は 4〜6 本。各 section に heading / purpose / must_cover / evidence_ids / forbidden_overlap_with を割り当てる。",
                "tone は title・lead・section opening の方針として plan に反映する。",
                "script の section_briefs を骨格に使い、source にない新論点を作らず、同じ evidence を全節で使い回さない。",
                *comparative_stage_lines.get("planner", []),
            ],
            output_lines=[
                '{"title_intent":"...", "lead_intent":"...", "sections":[{"heading":"...", "purpose":"...", "must_cover":["..."], "evidence_ids":["fact1"], "forbidden_overlap_with":["..."]}]}',
            ],
        ),
    }
    stack["writer"] = {
        **_EXPERIMENTAL_STAGE_MODEL_CONFIG["writer"],
        "prompt": _build_experimental_stage_prompt(
            role_lines=[
                "source-grounded な日本語記事を書く writer。人間の編集者の自然さを優先する。",
                "tone と骨格は守るが、topic をそのままなぞる導入や節ごとの反復を避ける。",
            ],
            ui_slot_lines=ui_slot_lines,
            dynamic_hint_bundle=dynamic_hint_bundle,
            source_lines=[],
            task_lines=[
                "support/script の結果は <SCRIPT_JSON>...</SCRIPT_JSON> に入る想定。",
                "section plan は <PLANNER_JSON>...</PLANNER_JSON> に入る想定。",
                "raw source ではなく SCRIPT_JSON を主入力として使い、source_digest と section_briefs を先に読んでから書き始める。",
                "各 section は対応する brief を1つ主に使い、fact_anchor と why_it_matters を本文へ自然に展開する。",
                "script の fact_anchor と writing_cautions を優先し、各 section は plan の purpose と must_cover だけを扱う。",
                "do_not_mix に書かれた論点は同じ section に持ち込まず、別 section の結論を言い換えて再利用しない。",
                "別 section の結論を言い換えて再利用せず、script にない新論点を膨らませない。",
                "タイトルは汎用語に落とさず、lead は tone に合わせて自然に始める。",
                "source-specific な固有名詞や判断材料を残し、一般論だけで段落を埋めない。",
                *comparative_stage_lines.get("writer", []),
                *writer_stylometry_lines,
            ],
            output_lines=writer_output_lines,
        ),
    }
    stack["editor"] = {
        **_EXPERIMENTAL_STAGE_MODEL_CONFIG["editor"],
        "prompt": _build_experimental_stage_prompt(
            role_lines=[
                "局所補修に徹する editor。良い箇所は残し、必要箇所だけ直す。",
                "加筆は許可するが、section の役割変更や全面書換はしない。",
            ],
            ui_slot_lines=ui_slot_lines,
            dynamic_hint_bundle=dynamic_hint_bundle,
            source_lines=[],
            task_lines=[
                "support/script の結果は <SCRIPT_JSON>...</SCRIPT_JSON> に入る想定。",
                "section plan は <PLANNER_JSON>...</PLANNER_JSON> に入る想定。",
                "draft は <DRAFT_ARTICLE>...</DRAFT_ARTICLE> に入る想定。",
                "脚本と本文のズレを見ながら、改行、段落呼吸、AIっぽい反復、title の弱さ、source density の薄さを局所的に直す。",
                "未指定の section は保ち、見出し追加・論旨変更・段落の大量移動はしない。",
                "見出しは markdown の ## で保ち、[SECTION]...[/SECTION] や類似 wrapper を残さない。",
                *comparative_stage_lines.get("editor", []),
                *editor_stylometry_lines,
            ],
            output_lines=writer_output_lines,
        ),
    }
    stack["legal"] = {
        **_EXPERIMENTAL_STAGE_MODEL_CONFIG["legal"],
        "prompt": _build_experimental_stage_prompt(
            role_lines=[
                "法務上の危険箇所だけを直す legal editor。",
                "記事を安全にすることが目的であり、文体や論調を別物に作り替えることではない。",
            ],
            ui_slot_lines=ui_slot_lines,
            dynamic_hint_bundle=dynamic_hint_bundle,
            source_lines=[],
            task_lines=[
                *build_legal_rewrite_guard_lines(article_type=article_type, tone_profile=tone_profile),
                "draft は <LEGAL_DRAFT_ARTICLE>...</LEGAL_DRAFT_ARTICLE> に入る想定。",
                "法令名・断定表現・越権誘導の修正が必要な箇所だけを直し、他の paragraph は触らない。",
            ],
            output_lines=writer_output_lines,
        ),
    }
    return stack


def _strip_code_fences(text: str) -> str:
    stripped = re.sub(r"^\s*`{3,}[^\S\n]*\S*[^\S\n]*\n", "", str(text or ""))
    stripped = re.sub(r"\n\s*`{3,}[^\S\n]*$", "", stripped)
    return stripped.strip()


def _summarize_compact_plan(compact_plan: Iterable[Mapping[str, Any]] | None) -> list[str]:
    lines: list[str] = []
    items = list(compact_plan or [])[:6]
    for index, item in enumerate(items, start=1):
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
    items = list(compact_plan or [])[:6]
    for index, item in enumerate(items, start=1):
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


def _summarize_section_shadow(
    compact_plan: Iterable[Mapping[str, Any]] | None,
    shadow_spec_inputs: Mapping[str, Any] | None,
) -> list[str]:
    if not isinstance(shadow_spec_inputs, Mapping):
        return []
    semantic_key = _clean_inline_text(shadow_spec_inputs.get("semantic_article_key") or "", limit=40).lower()
    company_intro_shadow = semantic_key == "company_introduction"
    main_focus = _clean_inline_text(shadow_spec_inputs.get("main_focus") or "", limit=72)
    support_points = _clean_items(shadow_spec_inputs.get("support_points") or [], limit=3, char_limit=40)
    comparison_axes = _clean_items(shadow_spec_inputs.get("comparison_axes") or [], limit=2, char_limit=32)
    source_fact_pool = _clean_items(shadow_spec_inputs.get("source_fact_pool") or [], limit=6, char_limit=96)
    register_policy = dict(shadow_spec_inputs.get("register_policy") or {})
    base_register = _clean_inline_text(register_policy.get("base_register") or "polite", limit=16)
    relationship_mode = _clean_inline_text(shadow_spec_inputs.get("relationship_mode") or "guide", limit=24)
    lines: list[str] = []
    if company_intro_shadow and main_focus:
        lines.append("company_intro_shadow=main_focus は記事全体の軸として保持し、各節では heading と claim の役割差を優先する。")
    for index, item in enumerate(list(compact_plan or [])[:6], start=1):
        heading = _clean_inline_text(item.get("heading") or "", limit=40)
        claim = _clean_inline_text(item.get("claim") or item.get("key_message") or "", limit=72)
        if not heading:
            continue
        parts = [f"shadow[{index}]={heading}"]
        if main_focus and not company_intro_shadow:
            parts.append(f"focus={main_focus}")
        if claim:
            parts.append(f"claim={claim}")
        if support_points:
            if company_intro_shadow:
                if index <= len(support_points):
                    parts.append(f"support={support_points[index - 1]}")
            else:
                parts.append(f"support={support_points[min(index - 1, len(support_points) - 1)]}")
        if comparison_axes:
            parts.append(f"axes={' / '.join(comparison_axes)}")
        if source_fact_pool:
            if company_intro_shadow:
                if index <= len(source_fact_pool):
                    parts.append(f"fact={source_fact_pool[index - 1]}")
            else:
                parts.append(f"fact={source_fact_pool[min(index - 1, len(source_fact_pool) - 1)]}")
        if not company_intro_shadow:
            parts.append(f"voice={base_register}/{relationship_mode}")
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
            f"chars≈{target_chars(length_mode, article_type, source_count=len(_to_plain_list(contract.get('source_documents'))))} / headings≈{heading_target(length_mode, article_type, semantic_key)}",
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
            "全 section を同じ厚みに寄せず、短めに畳む節とやや厚めに説明する節を混ぜる。",
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
    shadow_spec_inputs: Mapping[str, Any] | None = None,
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
            "facts外の断定禁止。topicの語順をそのままなぞる導入を避け、主語・書き出し・言い換え反復を避け、1段落1〜4文で自然改行し、各見出しを1文で終えない。一文だけの独立段落を連続させない。",
            *block_map["HARD_CONTRACT"],
        ],
    )
    structure_lines = list(block_map["STRUCTURE"])
    plan_lines = _summarize_compact_plan(compact_plan)
    semantic_lines = _summarize_semantic_ledger(compact_plan)
    section_shadow_lines = _summarize_section_shadow(compact_plan, shadow_spec_inputs)
    if plan_lines:
        structure_lines = [*plan_lines, *structure_lines]
    _append_block(prompt_lines, "STRUCTURE", structure_lines)
    if section_shadow_lines:
        _append_block(
            prompt_lines,
            "SECTION_SHADOW",
            [
                "sectionごとの責務メモ。各節は listed focus / support / fact の範囲で膨らませる。",
                "main_focus と claim を保ち、未指定の新論点へ広げない。",
                "各節は listed fact を最低1つ自然に織り込む。複数可。数字・サイズ・公開条件・固有名詞を抽象語に置き換えすぎない。",
                *section_shadow_lines,
            ],
        )
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
    section_shadow: Iterable[str] | None = None,
    flagged_spans: Iterable[Mapping[str, Any]] | None = None,
    article_guard_lines: Iterable[str] | None = None,
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
    shadow_lines = _filter_section_shadow_lines(
        section_shadow,
        _extract_flagged_headings(flagged_spans, issue_type="shadow_section_drift"),
    )
    if shadow_lines:
        _append_block(
            prompt_lines,
            "SECTION_SHADOW",
            [
                "focus / claim / support は listed heading に戻し、補修は対象見出しの冒頭2文と本文1-2文だけに限定する。",
                *shadow_lines,
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
                *_build_compare_patch_scope_lines(article_type, flagged_spans),
                *_build_shadow_patch_scope_lines(flagged_spans),
            ],
        )
    guard_lines = _clean_items(article_guard_lines or [], limit=4, char_limit=160)
    if guard_lines:
        _append_block(
            prompt_lines,
            "ARTICLE_GUARD",
            guard_lines,
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
    raw_topic = _clean_inline_text(
        contract.get("topic") or contract.get("prompt_raw") or contract.get("topic_statement") or contract.get("core_message") or "",
        limit=180,
    )
    compact_topic = _compact_topic_for_prompt(article_type, raw_topic)
    ui_journey = contract.get("ui_journey") if isinstance(contract.get("ui_journey"), Mapping) else {}
    compare_goal_key = str(ui_journey.get("detail_key") or "").strip().lower()
    source_material = _collect_source_prompt_material(source_pack)
    shadow_spec_inputs = contract.get("_shadow_spec_inputs") if isinstance(contract.get("_shadow_spec_inputs"), Mapping) else None
    return build_generation_prompt(
        article_type=article_type,
        semantic_key=semantic_key,
        target_chars=target_chars(
            length_mode,
            article_type,
            source_count=len(_to_plain_list(contract.get("source_documents"))),
        ),
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
        source_titles=source_material["source_titles"],
        source_facts=source_material["source_facts"],
        source_excerpts=source_material["source_excerpts"],
        compare_goal_rule=_COMPARATIVE_GOAL_RULES.get(compare_goal_key, ""),
        compact_plan=compact_plan,
        shadow_spec_inputs=shadow_spec_inputs,
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
    shadow_spec_inputs = contract.get("_shadow_spec_inputs") if isinstance(contract.get("_shadow_spec_inputs"), Mapping) else None
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
        section_shadow=_summarize_section_shadow(effective_plan, shadow_spec_inputs),
        flagged_spans=effective_flagged_spans,
        article_guard_lines=_build_experimental_comparative_repair_guard_lines(contract),
    )
