"""Private persona/source trial helpers for current mainline contracts."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Mapping, Sequence

INITIATIVE_ID = "persona_iterative_trial_2026-04-23"
DEFAULT_AUDIENCE = "一般読者"
_BRANDING_LEXICAL_LOOP_WATCH_TERMS = (
    "迷い",
    "迷",
    "整える",
    "整え",
    "判断材料",
    "導線",
)


def _clean_inline_text(value: Any, *, limit: int = 180) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _normalize_unique_texts(
    values: Iterable[Any] | None,
    *,
    limit: int = 6,
    char_limit: int = 180,
) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        text = _clean_inline_text(value, limit=char_limit)
        if not text or text in normalized:
            continue
        normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def _family(
    *,
    family_key: str,
    lead_focus: str,
    heading_flow: str,
    fact_priority: str,
    paragraph_emphasis: str,
    late_return: str,
    generation_mission: str,
    editing_mission: str,
    regeneration_mission: str,
    reader_friction: Sequence[str],
    forbidden_expansion: Sequence[str],
) -> Dict[str, Any]:
    return {
        "family_key": family_key,
        "lead_focus": lead_focus,
        "heading_flow": heading_flow,
        "fact_priority": fact_priority,
        "paragraph_emphasis": paragraph_emphasis,
        "late_return": late_return,
        "generation_mission": generation_mission,
        "editing_mission": editing_mission,
        "regeneration_mission": regeneration_mission,
        "reader_friction": list(reader_friction),
        "forbidden_expansion": list(forbidden_expansion),
    }


_DEFAULT_FAMILY = _family(
    family_key="balanced_explainer",
    lead_focus="読者が最初に迷う論点と、その場での短い結論を置く。",
    heading_flow="背景、判断材料、実務での見方、最後の確認点の順で進める。",
    fact_priority="断定より判断材料と条件差を優先する。",
    paragraph_emphasis="一段落ごとに役割を一つに絞り、説明の型を繰り返さない。",
    late_return="最後は読者が次にどこを見れば判断しやすいかへ戻す。",
    generation_mission="導入で問いと短い結論を置き、本文は判断材料へ進める。",
    editing_mission="抽象化しすぎた節と後半の追従低下だけを局所補修する。",
    regeneration_mission="論点順を崩さず、終盤を同じ戻り先へ再整列する。",
    reader_friction=("何を基準に判断すればよいか見えないと読み進めにくい。",),
    forbidden_expansion=("source にない数値、実績、制度、比較優位は足さない。",),
)

_FAMILY_BY_ROUTE: Dict[tuple[str, str], Dict[str, Any]] = {
    ("explanatory_article", "explanatory_article"): _family(
        family_key="explanatory_bridge",
        lead_focus="問いと短い結論で入り、背景より先に判断軸を見せる。",
        heading_flow="背景、判断軸、実務での使い方、最後の確認点の順で進める。",
        fact_priority="用語説明だけで止めず、判断に使える差分を優先する。",
        paragraph_emphasis="定義と示唆を同じ段落に詰め込みすぎず、役割ごとに分ける。",
        late_return="最後は次にどこを見れば判断しやすいかへ戻す。",
        generation_mission="背景の要約より、読者が使える判断材料を前に置く。",
        editing_mission="導入の topic なぞりと終盤の抽象反復だけを狭く戻す。",
        regeneration_mission="判断軸と実務の使い方を保ったまま終盤を戻す。",
        reader_friction=("前提説明だけが続くと、判断軸が見えず離脱しやすい。",),
        forbidden_expansion=("source にない統計、制度、ベンダー評価は足さない。",),
    ),
    ("industry_analysis", "industry_analysis"): _family(
        family_key="industry_signal_map",
        lead_focus="市場変化そのものより、読み手にとっての意味を先に置く。",
        heading_flow="変化、評価軸、買い手 signal、最後の示唆の順で進める。",
        fact_priority="市場構造と意思決定への影響を同じ軸で結び直す。",
        paragraph_emphasis="構造説明と示唆を分け、観測事実から離れすぎない。",
        late_return="最後は意思決定で見落としやすい確認点へ戻す。",
        generation_mission="市場の出来事より、判断に効く signal の整理を優先する。",
        editing_mission="概念の言い換え反復と示唆の散漫化だけを補修する。",
        regeneration_mission="市場 signal から意思決定の戻り先へ同じ筋で戻す。",
        reader_friction=("市場変化が自社判断にどう効くか見えないと読後に残りにくい。",),
        forbidden_expansion=("source にない市場順位、成長率、優位性断定は足さない。",),
    ),
    ("daily_story", "daily_story"): _family(
        family_key="daily_reflection",
        lead_focus="起きた場面と小さな違和感から入り、感想だけに寄せない。",
        heading_flow="場面、気づき、次に変える一つの行動の順で進める。",
        fact_priority="感情語より、起きた順番と手触りを優先する。",
        paragraph_emphasis="感傷を重ねず、場面の動きと気づきを短く往復する。",
        late_return="最後は次に変える一つの行動へ戻す。",
        generation_mission="日記化せず、場面から気づきと次の小さな変更へ進める。",
        editing_mission="言い過ぎた感想と抽象化した締めだけを局所補修する。",
        regeneration_mission="同じ場面の延長で、最後を次の行動へ戻す。",
        reader_friction=("感想だけが続くと、自分の場面へ置き換えにくい。",),
        forbidden_expansion=("prompt/context にない外部事実、数値、比較優位は足さない。",),
    ),
    ("branding", "branding"): _family(
        family_key="branding_operational",
        lead_focus="読者の入口にある不安を起点にしつつ、すぐ会社の運用行動へ移す。",
        heading_flow="顧客接点、運用行動、支援プロセス、行動としての姿勢の順で進める。",
        fact_priority="価値語より行動と支え方の記述を優先する。",
        paragraph_emphasis="理念を膨らませず、行動として見える根拠を残す。",
        late_return="最後は会社の姿勢がどの運用行動、見直し方、支援プロセスに出ているかへ戻す。",
        generation_mission="ブランド姿勢を抽象語ではなく行動として見せる。",
        editing_mission="広告 copy 化した節と抽象価値だけの終盤を狭く戻す。",
        regeneration_mission="読者の入口から、会社の運用行動と支援プロセスへ流れを戻す。",
        reader_friction=("価値語だけだと、何をしてくれるのかが見えにくい。",),
        forbidden_expansion=("source にない成果、顧客名、価格、受賞、提携は足さない。",),
    ),
    ("branding", "product_introduction"): _family(
        family_key="branding_operational",
        lead_focus="読者の迷いと価値の背景を先に置き、理念だけで始めない。",
        heading_flow="迷い、支え方、判断基準、続けやすさの順で進める。",
        fact_priority="価値語より行動と支え方の記述を優先する。",
        paragraph_emphasis="理念を膨らませず、行動として見える根拠を残す。",
        late_return="最後は相談前に何を確かめると判断しやすいかへ戻す。",
        generation_mission="ブランド姿勢を抽象語ではなく行動として見せる。",
        editing_mission="広告 copy 化した節と抽象価値だけの終盤を狭く戻す。",
        regeneration_mission="読者の迷いから判断材料への流れを保って戻す。",
        reader_friction=("価値語だけだと、何をしてくれるのかが見えにくい。",),
        forbidden_expansion=("source にない成果、顧客名、価格、受賞、提携は足さない。",),
    ),
    ("branding", "company_introduction"): _family(
        family_key="company_intro_operational",
        lead_focus="沿革より先に、今の事業内容と扱っている製品・サービスを置く。",
        heading_flow="現在事業、製品・サービス、対応範囲、事業の特徴、姿勢や背景の順で進める。",
        fact_priority="事業内容、扱う領域、対応範囲、会社としての姿勢に効く事実を優先する。",
        paragraph_emphasis="歩みは背景に留め、現在の事業内容と対応範囲を前半で具体化する。",
        late_return="最後は私たちの事業内容、扱う領域、対応範囲、会社としての姿勢へ戻す。",
        generation_mission="会社の全体像を、事業内容・製品サービス・対応範囲から読み取れるようにする。",
        editing_mission="会社案内の羅列化と沿革だけが先行する流れを局所補修する。",
        regeneration_mission="現在事業、対応範囲、会社としての姿勢を同じ筋で保って終盤を戻す。",
        reader_friction=("会社紹介が沿革先行になると、今の役割がつかみにくい。",),
        forbidden_expansion=(
            "公開情報で確認できない支援範囲、成果、顧客名、受賞、手間削減や進めやすさの効果推測は足さない。",
        ),
    ),
    ("announcement", "announcement"): _family(
        family_key="notice_action",
        lead_focus="変更点と対象を先に置き、背景説明を引き延ばさない。",
        heading_flow="変更点、影響範囲、確認事項、次の行動の順で進める。",
        fact_priority="日時、対象、影響、確認順を一文一要件で優先する。",
        paragraph_emphasis="案内文として迷わない順番を守り、説明文へ脱線しない。",
        late_return="最後は日付と確認順へ戻す。",
        generation_mission="何が変わるかと誰が確認すべきかを先に固定する。",
        editing_mission="対象者の埋没と確認順の崩れだけを局所補修する。",
        regeneration_mission="変更点と確認順を保ったまま最後を明瞭に戻す。",
        reader_friction=("対象者、影響、確認事項が混ざると行動しにくい。",),
        forbidden_expansion=("source にない停止範囲、日時、対象者、移行条件は足さない。",),
    ),
    ("case_study", "case_study"): _family(
        family_key="case_repro",
        lead_focus="改善前のつまずきと、何を変えたかを先に置く。",
        heading_flow="改善前、変更、結果、再現条件の順で進める。",
        fact_priority="成功談より、状態変化と再現条件を優先する。",
        paragraph_emphasis="結果だけで閉じず、条件と限界を後半に残す。",
        late_return="最後はどの条件で再現しやすいかへ戻す。",
        generation_mission="成功談に寄せず、再現条件まで見える事例にする。",
        editing_mission="結果の誇張と条件欠落だけを局所補修する。",
        regeneration_mission="改善前後の差と再現条件を保ったまま戻す。",
        reader_friction=("結果だけ先に出ると、再現条件が見えにくい。",),
        forbidden_expansion=("source にない数値成果、顧客名、受賞、一般論だけの助言は足さない。",),
    ),
    ("comparative_review", "comparative_review"): _family(
        family_key="comparison_fit",
        lead_focus="比較前提と評価軸を先に置き、勝敗から始めない。",
        heading_flow="比較条件、軸差、向く条件、注意点、確認順の順で進める。",
        fact_priority="絶対優劣より、条件別の向き不向きを優先する。",
        paragraph_emphasis="同じ軸で複数候補を比べ、ランキング調で流さない。",
        late_return="最後は確認順と見落としやすい条件へ戻す。",
        generation_mission="比較軸を固定し、条件別判断として最後まで運ぶ。",
        editing_mission="軸ずれ、勝敗化、注意点の欠落だけを局所補修する。",
        regeneration_mission="同じ比較軸のまま向く条件と確認順へ戻す。",
        reader_friction=("比較軸が途中でずれると、何で選ぶべきか分からなくなる。",),
        forbidden_expansion=("source にない価格、プラン、成果、絶対優位、ランキングは足さない。",),
    ),
}


def _resolve_family(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized_contract = dict(contract or {})
    article_type = str(normalized_contract.get("article_type") or "").strip().lower()
    semantic_key = str(normalized_contract.get("semantic_article_key") or "").strip().lower() or article_type
    return dict(
        _FAMILY_BY_ROUTE.get((article_type, semantic_key))
        or _FAMILY_BY_ROUTE.get((article_type, article_type))
        or _DEFAULT_FAMILY
    )


def _slot_values_from_private_runtime_contract(
    private_contract: Mapping[str, Any] | None,
    *,
    blocked_slots: Sequence[str] = (),
) -> list[str]:
    slots = dict((private_contract or {}).get("slots") or {})
    blocked = {str(item or "").strip() for item in blocked_slots}
    values: list[str] = []
    for key, value in slots.items():
        if str(key or "").strip() in blocked:
            continue
        text = _clean_inline_text(value, limit=180)
        if text and text not in values:
            values.append(text)
    return values[:8]


def _collect_source_packet_facts(contract: Mapping[str, Any] | None) -> list[str]:
    normalized_contract = dict(contract or {})
    company_intro_contract = dict(normalized_contract.get("_company_introduction_source_contract") or {})
    if bool(company_intro_contract.get("scope_match")):
        return _slot_values_from_private_runtime_contract(
            company_intro_contract,
            blocked_slots=("source_limit",),
        )
    comparative_contract = dict(normalized_contract.get("_comparative_review_source_contract") or {})
    if bool(comparative_contract.get("scope_match")):
        return _slot_values_from_private_runtime_contract(
            comparative_contract,
            blocked_slots=("source_limit",),
        )
    branding_contract = dict(normalized_contract.get("_branding_source_contract") or {})
    if bool(branding_contract.get("scope_match")):
        return _slot_values_from_private_runtime_contract(branding_contract)

    facts: list[str] = []
    for item in list(normalized_contract.get("source_grounding_items") or [])[:10]:
        if not isinstance(item, Mapping):
            continue
        fact_text = _clean_inline_text(item.get("fact_text") or "", limit=180)
        if fact_text and fact_text not in facts:
            facts.append(fact_text)
    if facts:
        return facts[:8]

    for item in list(normalized_contract.get("source_documents") or [])[:4]:
        if not isinstance(item, Mapping):
            continue
        raw_content = str(item.get("content") or "")
        for part in re.split(r"(?<=[。！？!?])\s*|\n+", raw_content):
            text = _clean_inline_text(part, limit=180)
            if text and text not in facts:
                facts.append(text)
            if len(facts) >= 6:
                return facts
    return facts[:6]


def _collect_reader_friction(
    contract: Mapping[str, Any] | None,
    family: Mapping[str, Any],
) -> list[str]:
    normalized_contract = dict(contract or {})
    company_intro_contract = dict(normalized_contract.get("_company_introduction_source_contract") or {})
    if bool(company_intro_contract.get("scope_match")):
        slots = dict(company_intro_contract.get("slots") or {})
        for slot_key in ("current_business", "support_scope_boundary"):
            focus = _clean_inline_text(slots.get(slot_key) or "", limit=160)
            if focus:
                return [focus]
        return _normalize_unique_texts(family.get("reader_friction"), limit=2, char_limit=160)
    branding_contract = dict(normalized_contract.get("_branding_source_contract") or {})
    if bool(branding_contract.get("scope_match")):
        slots = dict(branding_contract.get("slots") or {})
        friction = _clean_inline_text(slots.get("customer_touchpoint") or "", limit=160)
        if friction:
            return [friction]
    comparative_contract = dict(normalized_contract.get("_comparative_review_source_contract") or {})
    if bool(comparative_contract.get("scope_match")):
        slots = dict(comparative_contract.get("slots") or {})
        friction = _clean_inline_text(
            slots.get("comparison_context") or slots.get("fit_conditions") or "",
            limit=160,
        )
        if friction:
            return [friction]

    friction_items: list[str] = []
    for item in list(normalized_contract.get("source_grounding_items") or [])[:8]:
        if not isinstance(item, Mapping):
            continue
        bucket = _clean_inline_text(item.get("bucket") or "", limit=40)
        if bucket and bucket not in {"つまずき", "顧客接点", "比較前提"}:
            continue
        fact_text = _clean_inline_text(item.get("fact_text") or "", limit=160)
        if fact_text and fact_text not in friction_items:
            friction_items.append(fact_text)
    if friction_items:
        return friction_items[:2]
    return _normalize_unique_texts(family.get("reader_friction"), limit=2, char_limit=160)


def _collect_forbidden_expansion(
    contract: Mapping[str, Any] | None,
    family: Mapping[str, Any],
) -> list[str]:
    normalized_contract = dict(contract or {})
    lines = _normalize_unique_texts(family.get("forbidden_expansion"), limit=4, char_limit=160)
    source_mode = str(normalized_contract.get("source_mode") or "").strip().lower()
    if source_mode == "prompt_only":
        lines.append("外部 source 扱いではない prompt/context から事実を増やさない。")
    elif bool(normalized_contract.get("source_grounding_required")):
        lines.append("source にない数字、実績、価格、固有名詞、制度は足さない。")

    company_intro_contract = dict(normalized_contract.get("_company_introduction_source_contract") or {})
    if bool(company_intro_contract.get("scope_match")):
        source_limit = _clean_inline_text(
            dict(company_intro_contract.get("slots") or {}).get("source_limit") or "",
            limit=160,
        )
        if source_limit:
            lines.append(source_limit)
    comparative_contract = dict(normalized_contract.get("_comparative_review_source_contract") or {})
    if bool(comparative_contract.get("scope_match")):
        source_limit = _clean_inline_text(
            dict(comparative_contract.get("slots") or {}).get("source_limit") or "",
            limit=160,
        )
        if source_limit:
            lines.append(source_limit)
    return _normalize_unique_texts(lines, limit=5, char_limit=160)


def _build_source_packet(contract: Mapping[str, Any] | None, family: Mapping[str, Any]) -> Dict[str, Any]:
    normalized_contract = dict(contract or {})
    packet = {
        "source_facts": _collect_source_packet_facts(normalized_contract),
        "reader_friction": _collect_reader_friction(normalized_contract, family),
        "must_cover": _normalize_unique_texts(normalized_contract.get("must_cover"), limit=6, char_limit=96),
        "late_return": _clean_inline_text(family.get("late_return") or "", limit=160),
        "forbidden_expansion": _collect_forbidden_expansion(normalized_contract, family),
    }
    article_type = str(normalized_contract.get("article_type") or "").strip().lower()
    semantic_key = str(normalized_contract.get("semantic_article_key") or "").strip().lower() or article_type
    if article_type == "branding" and semantic_key in {"", "branding"}:
        packet["lexical_loop_watch"] = {
            "terms": list(_BRANDING_LEXICAL_LOOP_WATCH_TERMS),
            "hard_ban": False,
            "surface_budget": "title / heading / section opening / final section で同じ source 語へ戻り続ける場合だけ loop として扱う。",
            "positive_rewrite_direction": (
                "続く箇所は、会社が何を見直すか、どの運用へ戻すか、どの支援動作をするかへ言い換える。"
            ),
        }
    return packet


def enrich_persona_trial_contract(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized_contract = dict(contract or {})
    family = _resolve_family(normalized_contract)
    late_return = _clean_inline_text(family.get("late_return") or "", limit=160)
    normalized_contract["_persona_contract"] = {
        "generation": {
            "family_key": str(family.get("family_key") or ""),
            "mission": _clean_inline_text(family.get("generation_mission") or "", limit=160),
            "late_return": late_return,
        },
        "editing": {
            "family_key": str(family.get("family_key") or ""),
            "mission": _clean_inline_text(family.get("editing_mission") or "", limit=160),
            "late_return": late_return,
        },
        "regeneration": {
            "family_key": str(family.get("family_key") or ""),
            "mission": _clean_inline_text(family.get("regeneration_mission") or "", limit=160),
            "late_return": late_return,
        },
    }
    normalized_contract["_source_packet"] = _build_source_packet(normalized_contract, family)
    normalized_contract["_persona_trial"] = {
        "explicit_audience_required": True,
        "default_audience_valid": False,
        "initiative_id": INITIATIVE_ID,
    }
    return normalized_contract


def build_generation_guard_lines(contract: Mapping[str, Any] | None) -> list[str]:
    normalized_contract = enrich_persona_trial_contract(contract)
    family = _resolve_family(normalized_contract)
    source_packet = dict(normalized_contract.get("_source_packet") or {})
    article_type = str(normalized_contract.get("article_type") or "").strip().lower()
    semantic_key = str(normalized_contract.get("semantic_article_key") or "").strip().lower() or article_type
    is_company_intro = article_type == "branding" and semantic_key == "company_introduction"
    is_branding_operational = article_type == "branding" and semantic_key in {"", "branding"}
    lines = [
        _clean_inline_text(family.get("lead_focus") or "", limit=160),
        _clean_inline_text(family.get("heading_flow") or "", limit=160),
    ]
    reader_friction = _normalize_unique_texts(source_packet.get("reader_friction"), limit=1, char_limit=160)
    if reader_friction:
        if is_company_intro:
            lines.append(
                "会社紹介で中心に置く事実: 事業内容・扱う製品サービス・対応範囲。"
                "sourceに相談・窓口表現があってもタイトル・見出し・締めの軸にしない。"
            )
        else:
            lines.append(f"読者が止まりやすい点: {reader_friction[0]}")
    lexical_watch = dict(source_packet.get("lexical_loop_watch") or {})
    if is_branding_operational and lexical_watch:
        lines.append("source語はhard banではないが、title・見出し・節冒頭・締めで同じ語へ戻り続けない。")
        lines.append(
            "同じ語が続く箇所は、会社が見直す対象、戻す運用、支援プロセスへ言い換える。"
        )
    forbidden = _normalize_unique_texts(source_packet.get("forbidden_expansion"), limit=1, char_limit=160)
    if forbidden:
        lines.append(f"広げない範囲: {forbidden[0]}")
    return _normalize_unique_texts(lines, limit=6, char_limit=160)


def build_repair_guard_lines(contract: Mapping[str, Any] | None) -> list[str]:
    normalized_contract = enrich_persona_trial_contract(contract)
    persona_contract = dict(normalized_contract.get("_persona_contract") or {})
    editing = dict(persona_contract.get("editing") or {})
    regeneration = dict(persona_contract.get("regeneration") or {})
    source_packet = dict(normalized_contract.get("_source_packet") or {})
    article_type = str(normalized_contract.get("article_type") or "").strip().lower()
    semantic_key = str(normalized_contract.get("semantic_article_key") or "").strip().lower() or article_type
    is_branding_operational = article_type == "branding" and semantic_key in {"", "branding"}
    lines = [
        _clean_inline_text(editing.get("mission") or "", limit=160),
        _clean_inline_text(regeneration.get("mission") or "", limit=160),
        "補修で戻すときも、同じ記事タイプの論点順を保ち、別タイプの語り口へ寄せない。",
    ]
    late_return = _clean_inline_text(editing.get("late_return") or source_packet.get("late_return") or "", limit=160)
    if late_return:
        lines.append(f"終盤は {late_return} を見失わない。")
    if is_branding_operational and isinstance(source_packet.get("lexical_loop_watch"), Mapping):
        lines.append(
            "『迷い』『整える』『判断材料』『導線』が続く箇所は、会社が何を見直すか、"
            "どの運用へ戻すか、どの支援動作をするかへ言い換える。source語は必要箇所で使ってよい。"
        )
    forbidden = _normalize_unique_texts(source_packet.get("forbidden_expansion"), limit=1, char_limit=160)
    if forbidden:
        lines.append(f"補修でも {forbidden[0]}")
    return _normalize_unique_texts(lines, limit=6, char_limit=160)


def _collect_quality_flatness_flags(diagnostics: Mapping[str, Any] | None) -> set[str]:
    normalized = dict(diagnostics or {})
    flags: set[str] = set()
    for key in ("company_intro_fingerprint_repair", "explanatory_fingerprint_repair"):
        packet = dict(normalized.get(key) or {})
        if bool(packet.get("activated")):
            flags.update(
                str(item or "").strip()
                for item in list(packet.get("flat_zone_flags") or [])
                if str(item or "").strip()
            )
    fingerprint_guard = dict(normalized.get("fingerprint_guard") or {})
    flags.update(
        str(item or "").strip()
        for item in list(fingerprint_guard.get("flat_zone_flags") or [])
        if str(item or "").strip()
    )
    return flags


def build_diagnostic_repair_guard_lines(
    contract: Mapping[str, Any] | None,
    diagnostics: Mapping[str, Any] | None,
) -> list[str]:
    """Convert quality diagnostics into compact article-type repair operations."""

    normalized_contract = dict(contract or {})
    article_type = str(normalized_contract.get("article_type") or "").strip().lower()
    semantic_key = (
        str(normalized_contract.get("semantic_article_key") or "").strip().lower()
        or article_type
    )
    normalized_diagnostics = dict(diagnostics or {})
    flags = _collect_quality_flatness_flags(normalized_diagnostics)
    soft_warnings = {
        str(item or "").strip()
        for item in list(normalized_diagnostics.get("soft_warnings") or [])
        if str(item or "").strip()
    }
    lines: list[str] = []

    if {
        "paragraph_length_cv_flat",
        "bigram_mono_low",
        "syntactic_complexity_low",
        "comma_overuse",
    }.intersection(flags):
        lines.append(
            "対象見出し内で段落の長短と文の組み立てをずらし、読点でつないだ同型文を分ける。"
        )
    if {
        "sentence_ending_entropy_low",
        "ending_repetition",
    }.intersection(flags) or any("ending:bucket_monotony" in item for item in soft_warnings):
        lines.append(
            "丁寧調は保ちつつ、同じ文末を続けず、説明・留保・確認の閉じ方を混ぜる。"
        )
    if {"vocab_repetition", "nominalization_rate_high"}.intersection(flags):
        lines.append(
            "重要語以外の反復を減らし、名詞で畳んだ説明を人や業務の動きが見える文へ戻す。"
        )

    if article_type == "branding" and semantic_key == "company_introduction" and lines:
        lines.append(
            "会社紹介の補修は、現在事業・製品サービス・対応範囲・会社としての姿勢を保ったまま対象箇所だけ直す。"
        )
    if (
        article_type == "branding"
        and semantic_key in {"", "branding"}
        and {"vocab_repetition", "nominalization_rate_high"}.intersection(flags)
    ):
        lines.append(
            "ブランド記事でsource語の反復が続く箇所は、会社が何を見直すか、どの運用へ戻すか、どの支援動作をするかへ言い換える。source語は必要箇所で使ってよい。"
        )

    return _normalize_unique_texts(lines, limit=4, char_limit=160)


def _classify_dominant_failure(
    contract: Mapping[str, Any] | None,
    *,
    result: Mapping[str, Any] | None = None,
) -> str:
    normalized_contract = dict(contract or {})
    normalized_result = dict(result or {})
    pipeline_check = dict(normalized_result.get("pipeline_check") or {})
    audience = _clean_inline_text(normalized_contract.get("audience_profile") or "", limit=80) or DEFAULT_AUDIENCE
    persona_trial = dict(normalized_contract.get("_persona_trial") or {})
    default_audience_valid = bool(persona_trial.get("default_audience_valid"))
    if audience == DEFAULT_AUDIENCE and not default_audience_valid:
        return "default_audience"

    runtime_reason_code = str(
        normalized_result.get("runtime_reason_code")
        or normalized_result.get("reason_code")
        or ""
    ).strip()
    if runtime_reason_code and runtime_reason_code != "OK":
        if runtime_reason_code.startswith("INP_"):
            return "input_gate"
        return "runtime_failure"

    body_generation = dict(pipeline_check.get("body_generation") or {})
    repair_entry = dict(body_generation.get("repair_entry") or {})
    rejection_reason = _clean_inline_text(repair_entry.get("acceptance_rejection_reason") or "", limit=80)
    if rejection_reason:
        if "late" in rejection_reason or "opener" in rejection_reason:
            return "late_return_drift"
        if "source_contract" in rejection_reason or "unsupported" in rejection_reason:
            return "source_packet_drift"
        return "repair_rejected"

    for key in (
        "company_introduction_source_contract_validation",
        "comparative_review_source_contract_validation",
        "branding_source_contract_validation",
        "case_study_source_contract_validation",
    ):
        validation = dict(body_generation.get(key) or {})
        if list(validation.get("repair_trigger_ids") or []):
            return "source_packet_drift"

    final_quality_eval = dict(pipeline_check.get("final_quality_eval") or {})
    if int(final_quality_eval.get("soft_warning_count") or 0) > 0:
        return "quality_warning"
    return "accepted"


def build_persona_trial_telemetry(
    contract: Mapping[str, Any] | None,
    *,
    result: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized_contract = enrich_persona_trial_contract(contract)
    persona_contract = dict(normalized_contract.get("_persona_contract") or {})
    source_packet = dict(normalized_contract.get("_source_packet") or {})
    persona_trial = dict(normalized_contract.get("_persona_trial") or {})
    resolved_audience = (
        _clean_inline_text(normalized_contract.get("audience_profile") or "", limit=80)
        or DEFAULT_AUDIENCE
    )
    default_audience_fallback_used = resolved_audience == DEFAULT_AUDIENCE
    family_keys = _normalize_unique_texts(
        [
            dict(persona_contract.get("generation") or {}).get("family_key"),
            dict(persona_contract.get("editing") or {}).get("family_key"),
            dict(persona_contract.get("regeneration") or {}).get("family_key"),
        ],
        limit=3,
        char_limit=80,
    )
    late_return_target = _clean_inline_text(
        dict(persona_contract.get("generation") or {}).get("late_return")
        or source_packet.get("late_return")
        or "",
        limit=160,
    )
    dominant_failure_classification = _classify_dominant_failure(
        normalized_contract,
        result=result,
    )
    acceptance_blockers: list[str] = []
    if (
        bool(persona_trial.get("explicit_audience_required"))
        and not bool(persona_trial.get("default_audience_valid"))
        and default_audience_fallback_used
    ):
        acceptance_blockers.append("default_audience")
    return {
        "initiative_id": str(persona_trial.get("initiative_id") or INITIATIVE_ID),
        "resolved_audience": resolved_audience,
        "default_audience_fallback_used": bool(default_audience_fallback_used),
        "persona_family_keys": family_keys,
        "late_return_target": late_return_target,
        "dominant_failure_classification": dominant_failure_classification,
        "audience_valid_for_trial": not acceptance_blockers,
        "acceptance_blockers": acceptance_blockers,
    }


def iter_persona_trial_family_specs() -> list[Dict[str, Any]]:
    specs: list[Dict[str, Any]] = []
    for (article_type, semantic_key), family in sorted(_FAMILY_BY_ROUTE.items()):
        specs.append(
            {
                "article_type": article_type,
                "semantic_article_key": semantic_key,
                "family_key": str(family.get("family_key") or ""),
                "late_return": _clean_inline_text(family.get("late_return") or "", limit=160),
                "generation_mission": _clean_inline_text(family.get("generation_mission") or "", limit=160),
                "editing_mission": _clean_inline_text(family.get("editing_mission") or "", limit=160),
                "regeneration_mission": _clean_inline_text(family.get("regeneration_mission") or "", limit=160),
            }
        )
    return specs
