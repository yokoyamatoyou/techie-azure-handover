from __future__ import annotations
import os, re
from typing import Any
ALGORITHM_ENV = "ROUTE_V_ARTICLE_BRIEF_ALGORITHM"
EXHAUSTIVE_GOAL_TERMS = ("全部", "全料金", "全項目", "全て", "すべて", "一覧として", "網羅", "全サービス", "全プラン", "全FAQ", "全Q&A")
NON_EXHAUSTIVE_SHAPE_CLAIM_CAPS = {"announcement_details": 8, "company_profile": 10, "faq": 6, "mixed": 10, "narrative": 8, "pdf_slide": 10, "service_catalog": 10, "table_or_list": 10}
def use_source_shape_v2() -> bool:
    return os.getenv(ALGORITHM_ENV, "").strip().lower() in {"v2", "source_shape_v2", "experimental_v2"}
def apply_source_shape_v2(
    article_brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
    *,
    article_goal: str,
) -> None:
    brief = article_brief.get("article_brief")
    if not isinstance(brief, dict):
        return
    claims = _confirmed_claims(knowledge_pack)
    if not claims:
        return
    source_shape = detect_source_shape(knowledge_pack, article_goal=article_goal)
    source_shape = _resolve_company_intro_source_shape(brief, source_shape, knowledge_pack, article_goal=article_goal)
    source_use_mode = choose_source_use_mode(source_shape, article_goal=article_goal)
    plan = _plan_for(source_shape, source_use_mode)
    sections = _planned_sections(brief, plan["section_count"])
    section_count = len(sections) if sections else int(plan["section_count"])
    brief["source_shape"] = source_shape
    brief["source_use_mode"] = source_use_mode
    brief["target_length_chars"] = int(plan["target_length_chars"])
    brief["section_count"] = section_count
    brief["source_thickness"] = str(plan["source_thickness"])
    selected_claim_ids = _select_claim_ids(claims, source_shape, source_use_mode, section_count)
    selected_claim_ids = _apply_daily_activity_source_role_contract(brief, claims, selected_claim_ids)
    all_claim_ids = _claim_ids(claims)
    selected_set = set(selected_claim_ids)
    unassigned = [claim_id for claim_id in all_claim_ids if claim_id not in selected_set]
    brief["unassigned_claim_ids"] = unassigned
    _apply_interest_led_plan(brief, source_shape, source_use_mode, article_goal=article_goal)
    brief["aside_allowed_claim_ids"] = selected_claim_ids[:3]
    if sections:
        chunks = _split_claim_ids(selected_claim_ids, len(sections))
        for section, chunk in zip(sections, chunks):
            section["assigned_claim_ids"] = chunk
        brief["sections"] = sections
        brief["claim_allocation"] = [
            {
                "section_id": str(section.get("section_id") or f"s{index}"),
                "claim_ids": list(section.get("assigned_claim_ids") or []),
                "reuse_allowed": False,
            }
            for index, section in enumerate(sections, start=1)
        ]
    _append_v2_style_rule(brief, source_use_mode, claims, selected_set)
    _ensure_daily_activity_source_role_style_rule(brief)
def detect_source_shape(knowledge_pack: dict[str, Any], *, article_goal: str = "") -> str:
    text = _search_text(knowledge_pack, article_goal)
    scores = {
        "faq": _score(text, ("FAQ", "よくある質問", "Q.", "Q：", "質問", "回答", "できますか", "ですか", "？")),
        "announcement_details": _score(text, ("お知らせ", "発表", "開始", "変更", "開催", "日時", "対象", "受付", "終了")),
        "pdf_slide": _score(text, ("pdf", "slide", "スライド", "ページ", "図", "フレームワーク", "Canvas")),
        "table_or_list": _score(text, ("料金表", "価格表", "料金", "価格", "プラン", "コース", "月額", "税込", "円", "一覧", "表", "項目")),
        "company_profile": _score(text, ("会社", "所在地", "創業", "沿革", "代表", "事業内容", "従業員")),
        "service_catalog": _score(text, ("サービス", "提供", "対応", "支援", "業務", "メニュー", "コース", "プラン")),
    }
    scores["announcement_details"] += 2 if re.search(r"20[0-9]{2}年|[0-9]{1,2}月[0-9]{1,2}日", text) else 0
    scores["table_or_list"] += 2 if len(re.findall(r"[0-9,]+円|税込|月額", text)) >= 2 else 0
    scores["table_or_list"] += 3 if any(term in text for term in ("料金表", "価格表")) else 0
    if scores["faq"] >= 3:
        return "faq"
    if scores["announcement_details"] >= 5:
        return "announcement_details"
    if scores["table_or_list"] >= 5:
        return "table_or_list"
    if scores["pdf_slide"] >= 4:
        return "pdf_slide"
    if scores["service_catalog"] >= 5:
        return "service_catalog"
    if scores["company_profile"] >= 5:
        return "company_profile"
    active = [name for name, score in scores.items() if score >= 3]
    if len(active) >= 2:
        return "mixed"
    return "narrative"
def choose_source_use_mode(source_shape: str, *, article_goal: str = "") -> str:
    if any(term in article_goal for term in EXHAUSTIVE_GOAL_TERMS):
        return "exhaustive"
    if source_shape in {"faq", "service_catalog", "announcement_details"}:
        return "selective"
    if source_shape in {"table_or_list", "pdf_slide", "mixed"}:
        return "representative"
    return "selective"


def _resolve_company_intro_source_shape(
    brief: dict[str, Any],
    source_shape: str,
    knowledge_pack: dict[str, Any],
    *,
    article_goal: str,
) -> str:
    if str(brief.get("genre_id") or "") != "company_service_intro":
        return source_shape
    if source_shape != "table_or_list":
        return source_shape
    if any(term in article_goal for term in EXHAUSTIVE_GOAL_TERMS):
        return source_shape
    text = _search_text(knowledge_pack, article_goal)
    company_score = _score(text, ("会社", "所在地", "創業", "沿革", "代表", "事業内容", "従業員"))
    service_score = _score(text, ("サービス", "提供", "対応", "支援", "業務", "メニュー", "データ入力", "スキャニング", "RPA"))
    if company_score >= 5 or service_score >= 5:
        return "mixed"
    return source_shape
def detect_claim_reuse_violations(article_brief: dict[str, Any]) -> list[str]:
    brief = article_brief.get("article_brief") if isinstance(article_brief, dict) else {}
    allocations = brief.get("claim_allocation") if isinstance(brief, dict) else None
    if not isinstance(allocations, list):
        return []
    seen: dict[str, str] = {}
    problems: list[str] = []
    for allocation in allocations:
        if not isinstance(allocation, dict) or allocation.get("reuse_allowed") is True:
            continue
        section_id = str(allocation.get("section_id") or "")
        for claim_id in allocation.get("claim_ids") or []:
            claim = str(claim_id)
            previous = seen.get(claim)
            if previous and previous != section_id:
                problems.append(f"claim_id reused with reuse_allowed=false: {claim} in {previous} and {section_id}")
            else:
                seen[claim] = section_id
    return problems
def _confirmed_claims(knowledge_pack: dict[str, Any]) -> list[dict[str, Any]]:
    pack = knowledge_pack.get("article_knowledge_pack") if isinstance(knowledge_pack, dict) else {}
    claims = pack.get("confirmed_facts") if isinstance(pack, dict) else []
    return [claim for claim in claims if isinstance(claim, dict)]
def _claim_ids(claims: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id") or "").strip()
        if claim_id and claim_id not in result:
            result.append(claim_id)
    return result
def _search_text(knowledge_pack: dict[str, Any], article_goal: str) -> str:
    pack = knowledge_pack.get("article_knowledge_pack") if isinstance(knowledge_pack, dict) else {}
    parts = [article_goal]
    if isinstance(pack, dict):
        parts.extend(str(item) for item in pack.get("source_card_ids") or [])
        parts.extend(str(item) for item in pack.get("deduped_themes") or [])
        parts.extend(str(item) for item in pack.get("do_not_infer") or [])
        for claim in pack.get("confirmed_facts") or []:
            if isinstance(claim, dict):
                parts.append(str(claim.get("claim") or ""))
                parts.append(str(claim.get("preferred_expression") or ""))
    return "\n".join(parts)
def _score(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if term and term in text)
def _plan_for(source_shape: str, source_use_mode: str) -> dict[str, Any]:
    table = {
        ("table_or_list", "representative"): (1600, 3, "medium"),
        ("table_or_list", "exhaustive"): (2200, 4, "thick"),
        ("faq", "selective"): (1300, 2, "medium"),
        ("faq", "exhaustive"): (1800, 4, "thick"),
        ("service_catalog", "selective"): (1500, 3, "medium"),
        ("service_catalog", "exhaustive"): (2200, 4, "thick"),
        ("announcement_details", "selective"): (1200, 2, "medium"),
        ("announcement_details", "exhaustive"): (1600, 3, "medium"),
        ("pdf_slide", "representative"): (1400, 3, "medium"),
        ("company_profile", "selective"): (1600, 3, "medium"),
        ("mixed", "representative"): (1600, 3, "medium"),
        ("narrative", "selective"): (1400, 3, "medium"),
    }
    target, sections, thickness = table.get((source_shape, source_use_mode), (1400, 3, "medium"))
    return {"target_length_chars": target, "section_count": sections, "source_thickness": thickness}
def _apply_interest_led_plan(brief: dict[str, Any], source_shape: str, source_use_mode: str, *, article_goal: str) -> None:
    brief["voice_mode"] = "self_authored_blogger"
    brief["reader_arrival_context"] = _reader_arrival_context(source_shape)
    brief["interest_hook"] = _interest_hook(source_shape, source_use_mode)
    brief["reading_reward"] = _reading_reward(source_shape, article_goal)
    brief["self_authored_angle"] = _self_authored_angle(source_shape)
    brief["paragraph_function_plan"] = _paragraph_function_plan(source_shape, source_use_mode)
    brief["body_length_floor_chars"] = _body_length_floor(source_shape, source_use_mode)
    brief["source_derived_aside_policy"] = _aside_policy(source_shape, source_use_mode)
    brief["rhythm_break_plan"] = _rhythm_break_plan(source_shape, source_use_mode)
    _apply_genre_arrival_contract(brief)
    if str(brief.get("genre_id") or "") == "company_service_intro" and source_shape != "table_or_list":
        _apply_company_intro_low_intent_plan(brief)
_READER_CONTEXT = {"table_or_list": "料金やサービス内容をざっと見に来ているが、細かい項目を全部読む温度感とは限らない。", "faq": "知りたいことがありそうで眺めているが、FAQを上から全部読むとは限らない。", "service_catalog": "どんな対応範囲があるのかを軽く確かめに来ている。", "company_profile": "会社名やサービスを見かけて、どんな会社かを軽く確かめに来ている。"}
_INTEREST_HOOK = {"table_or_list": "料金表をただ並べず、どんな依頼単位で考えればよいかが見えるように始める。", "faq": "質問を羅列せず、読者が最初に知ると先を読みやすい問いから入る。", "service_catalog": "サービス名の一覧ではなく、相談できる範囲が見える入口から始める。", "company_profile": "沿革やプロフィールの前に、今どんな仕事をしている会社かを見せる。"}
_READING_REWARD = {"table_or_list": "全部の項目を覚えなくても、代表的な依頼単位と相談前に見る観点が分かる。", "faq": "すべての質問を読まなくても、最初に押さえたい確認点が分かる。", "service_catalog": "サービス一覧ではなく、どこまで相談できるかの見通しが分かる。", "company_profile": "会社の肩書きより、今の仕事と姿勢が分かる。"}
_SELF_ANGLE = {"table_or_list": "私たちは、料金を単なる一覧ではなく、依頼内容を整理するための目安として伝える。", "company_profile": "私たちは、会社紹介をプロフィールではなく、現在の仕事の説明として伝える。"}
_PARAGRAPH_PLAN = ["導入: 見に来ただけの読者が読み続ける理由を、source-backedな具体から作る。", "引き込み: sourceを一覧として消化せず、読者が見ればよい観点へ並べ替える。", "具体: assigned claimsを代表例として扱い、数字・名称・条件は正確に書く。", "背景: source外の体験や感想を足さず、私たち側の説明として自然につなぐ。", "締め: 一般論や強いCTAではなく、読者が次に確認する点へ静かに戻す。"]
_RHYTHM_PLAN = {"table_or_list": ["濃い料金・項目ブロックの直後に、項目ごとに数え方が違うことを短く受ける。", "すべてを覚えさせず、代表的に見ればよい単位へ戻す。"], "faq": ["Q&Aの羅列後に、最初に確認しやすい観点を一文で受ける。"], "service_catalog": ["サービス名の羅列後に、相談範囲の見通しへ短く戻す。"]}
_GENRE_CONTRACTS = {
    "market_explanation": ("テーマを軽く眺めに来た読者。専門的に知りたいとは限らない。", "資料要約ではなく、sourceの論点を見る順番から入る。", "軽く眺めた読者にも、何を見ればよいかが分かる。", "私たちは、資料の第三者要約ではなく自己視点の解説者として伝える。", "導入: 資料要約から始めず、読者が軽く追える論点の入口を作る。", "解説記事は資料要約調や第三者視点に寄せず、source上の論点を自己視点で並べ替える。", None),
    "announcement": ("必要情報だけを探す読者。長い読み物を求めていない可能性が高い。", "日付・対象・変更点・注意点など必要情報を先に示す。", "必要な情報と次に確認することが短く分かる。", "当社は、背景を膨らませず、sourceにある必要情報を簡潔に伝える。", "導入: 日記風にせず、必要情報を探す読者に対象・変更点・注意点を先に出す。", "お知らせは長文化・日記化せず、日付・対象・変更点・注意点をsource内で簡潔に扱う。", 900),
    "case_study": ("事例に少し関心があるが、成果話を信じに来たとは限らない読者。", "sourceから読める課題・対応・変化の順序から入る。", "何が課題で、どう対応したかの流れが分かる。", "私たちは、sourceから近く読める推論だけで事例の流れを伝える。", "導入: 成果断定ではなく、sourceにある課題・対応・変化の順番から入る。", "事例はsource由来の推論を許可するが、成果・顧客感情・強い因果・数字評価はsource明示時だけ扱う。", None),
    "comparison_guide": ("迷っているとは限らず、違いを軽く見たい読者。", "選び方の断定ではなく、source上の違いを見る観点から入る。", "ランキングではなく、違いを見る軸が分かる。", "私たちは、未根拠のおすすめではなくsource上の違いを整理する。", "導入: ポイント記事化せず、source上の違いを見る観点を示す。", "比較記事はポイント化・ランキング化・おすすめ断定を避け、source上の違いを見る観点を示す。", None),
    "daily_activity": ("なんとなく開いた低関心・探索中の読者。日記風でもよい。", "sourceにある場所・動作・道具・順番の近い場面から入る。", "その日の場面や準備、動きが少し分かる。", "私たちは、sourceにある場面を日記風に受けるが、感情・成果・強い因果は足さない。", "導入: 検索・サムネイル経由の読者にも見える、source内の場所・動作・道具から日記風に入る。", "日常記事はsourceにある場所・動作・道具・順番・制約から近接推論で膨らませ、第三者心理・成果・強い因果は断定しない。", 1200),
}
def _apply_company_intro_low_intent_plan(brief: dict[str, Any]) -> None:
    brief["reader_arrival_context"] = "検索結果やサムネイルからなんとなく訪問した低関心・探索中の読者。会社に強い関心がある前提にしない。"
    brief["interest_hook"] = "会社説明から始めず、暮らし・仕事・選定・運用・知見の小さな接点から入る。"
    brief["reading_reward"] = "会社の肩書きではなく、日々のどの場面を支え、どんな人・運用・考え方で届けているかが分かる。"
    brief["self_authored_angle"] = "私たちは、プロフィールや商品カタログではなく日々の接点とsource事実から自分たちの仕事を伝える。"
    brief["source_backed_reader_bridge_policy"] = "説明調のsourceしかない場合でも、sourceにある地名・用途・対象者・事業語を、暮らし・仕事・地域・選定・運用など読者に近い文脈へ翻訳してよい。ただし、公式ページ・商品カテゴリ・沿革・お知らせを読者が読む順番や確認先として案内せず、会社の仕事や考え方を説明する材料として扱う。sourceにない実績・効果・地域シェア・優位性・顧客感情・中心性は足さない。"
    plan = brief.get("paragraph_function_plan")
    if isinstance(plan, list) and plan:
        plan[0] = "導入: 会社に強い関心がある前提にせず、検索・サムネイル経由の読者にも触れる日々の場面・運用・知見から入る。"
        if len(plan) > 1: plan[1] = "引き込み: sourceを読む順番ではなく、会社の事業・商品・対象者・運用が読者の場面にどう関係するかへ組み替える。"
        if len(plan) > 4: plan[4] = "締め: 公式情報の確認順ではなく、本文で扱った会社の仕事・商品・背景を静かに結ぶ。"
    style_rules = brief.get("style_rules")
    brief["style_rules"] = (style_rules if isinstance(style_rules, list) else []) + ["会社・サービス・商品紹介は会社に強い関心がある前提にせず、sourceにある人・文化・採用・裏側だけを使って、低関心読者にも読む理由が見える導入にする。", "会社紹介のbridgeは公式ページの読み方を教える文にせず、sourceにある事業・商品・対象者・運用・理念を会社側の具体としてつなぐ。"]
    brief["body_length_floor_chars"] = max(int(brief.get("body_length_floor_chars") or 0), 1400)
    _align_company_intro_target_with_floor(brief)


def _align_company_intro_target_with_floor(brief: dict[str, Any]) -> None:
    floor = int(brief.get("body_length_floor_chars") or 0)
    if floor <= 0:
        return
    target = int(brief.get("target_length_chars") or 0)
    # Keep the low-intent opener, but do not let the brief ask for a body
    # shorter than the QA floor it must satisfy after editors.
    brief["target_length_chars"] = min(3000, max(target, floor + 280))
def _apply_genre_arrival_contract(brief: dict[str, Any]) -> None:
    contract = _GENRE_CONTRACTS.get(str(brief.get("genre_id") or ""))
    if not contract:
        return
    reader, hook, reward, angle, plan0, style_rule, floor_cap = contract
    for key, value in (
        ("reader_arrival_context", reader),
        ("interest_hook", hook),
        ("reading_reward", reward),
        ("self_authored_angle", angle),
    ):
        brief[key] = value
    plan = brief.get("paragraph_function_plan")
    if isinstance(plan, list) and plan:
        plan[0] = plan0
    style_rules = brief.get("style_rules")
    brief["style_rules"] = (style_rules if isinstance(style_rules, list) else []) + [style_rule]
    if floor_cap:
        current = int(brief.get("body_length_floor_chars") or 0)
        brief["body_length_floor_chars"] = min(current or floor_cap, floor_cap)
def _reader_arrival_context(source_shape: str) -> str:
    return _READER_CONTEXT.get(source_shape, "テーマに少し関心があり、読みながら必要な情報かを判断している。")
def _interest_hook(source_shape: str, source_use_mode: str) -> str:
    return _INTEREST_HOOK.get(source_shape, "必要項目を漏らさず、読者が追いやすい順番を先に示す。" if source_use_mode == "exhaustive" else "sourceの要約ではなく、読者が続きを読む理由になる具体から始める。")
def _reading_reward(source_shape: str, article_goal: str) -> str:
    return _READING_REWARD.get(source_shape, f"{article_goal}について、本文を読む理由が具体的に分かる。")
def _self_authored_angle(source_shape: str) -> str:
    return _SELF_ANGLE.get(source_shape, "私たちは、sourceにある事実だけを使い、読者が読み進めやすい順番で伝える。")
def _paragraph_function_plan(source_shape: str, source_use_mode: str) -> list[str]:
    plan = list(_PARAGRAPH_PLAN)
    if source_shape == "table_or_list" and source_use_mode != "exhaustive":
        plan.insert(2, "選び方ではなく見方: 全料金紹介にせず、依頼単位と注意点を代表的に見せる。")
    return plan[:6]
def _aside_policy(source_shape: str, source_use_mode: str) -> str:
    if source_use_mode == "exhaustive":
        return "全項目説明の邪魔をしない範囲で、濃い事実ブロック後に一文だけ読みやすさを作る。新事実・体験・成果・顧客行動は足さない。"
    return "濃い事実ブロック後に、source内の事実の見方だけを一文で受ける。余談は最大2文、体験談・感想・顧客事例・成果・優位性は足さない。"
def _rhythm_break_plan(source_shape: str, source_use_mode: str) -> list[str]:
    return _RHYTHM_PLAN.get(source_shape, ["事実説明が続いた後に、読者が次の段落へ進みやすい一文をsource内の情報だけで置く。"])[: 1 if source_use_mode == "exhaustive" else 2]
def _body_length_floor(source_shape: str, source_use_mode: str) -> int:
    return 1600 if source_use_mode == "exhaustive" else 1400 if source_shape in {"table_or_list", "company_profile", "service_catalog", "mixed"} else 1200
_DAILY_ACTIVITY_NOTICE_TERMS = ("募集", "募集案内", "参加者募集", "申込", "申し込み", "申込み", "締切", "受付", "定員", "受講料", "参加費", "開催予定", "対象は")
_DAILY_ACTIVITY_LIST_TERMS = ("一覧", "一覧ページ", "活動報告一覧", "複数", "各種", "投稿", "カテゴリ", "アーカイブ", "他の投稿", "別テーマ")
_DAILY_ACTIVITY_SCENE_TERMS = ("開催", "実施", "行われ", "講義", "実技", "撮影", "道具", "クリップライト", "デスクランプ", "黒いボール紙", "トレーシングペーパー", "手順", "説明", "確認", "体験", "会場", "室")
_DAILY_ACTIVITY_EVENT_TERMS = ("ワークショップ", "物撮り", "商品撮影", "研修", "セミナー")
_DAILY_ACTIVITY_ROLE_STYLE_RULE = "日常記事では、開催報告の場面を本文beatの中心にし、募集案内・一覧ページ由来の事実は同じ場面の時刻・場所・制約を補うcontextに留める。"
def _apply_daily_activity_source_role_contract(brief: dict[str, Any], claims: list[dict[str, Any]], selected_claim_ids: list[str]) -> list[str]:
    if str(brief.get("genre_id") or "") != "daily_activity":
        return selected_claim_ids
    roles = _classify_daily_activity_claim_roles(claims)
    primary = roles["primary_scene_report_claim_ids"]
    if not primary:
        return selected_claim_ids
    body_ids = [
        claim_id for claim_id in selected_claim_ids if claim_id in primary
        and claim_id not in roles["auxiliary_context_claim_ids"]
        and claim_id not in roles["auxiliary_suppressed_claim_ids"]
    ]
    if not body_ids:
        body_ids = list(primary[: max(1, len(selected_claim_ids))])
    brief["daily_activity_source_role_contract"] = {
        "primary_scene_report_claim_ids": primary,
        "auxiliary_context_claim_ids": roles["auxiliary_context_claim_ids"],
        "auxiliary_suppressed_claim_ids": roles["auxiliary_suppressed_claim_ids"],
        "scene_material_claim_ids": _unique_strings(primary + roles["auxiliary_context_claim_ids"]),
        "body_beat_claim_ids": body_ids,
        "role_boundary": "primary scene/report claims own body beats; auxiliary notice/list claims are context or provenance only.",
        "auxiliary_use_policy": "Use auxiliary same-scene notice/list facts only to clarify time, place, sequence, or constraint for the same event; do not make recruitment/list pages equal article themes.",
        "raw_source_handoff_allowed": False,
    }
    _ensure_daily_activity_source_role_style_rule(brief)
    return body_ids
def _ensure_daily_activity_source_role_style_rule(brief: dict[str, Any]) -> None:
    if not isinstance(brief.get("daily_activity_source_role_contract"), dict):
        return
    style_rules = brief.get("style_rules")
    brief["style_rules"] = _unique_strings((style_rules if isinstance(style_rules, list) else []) + [_DAILY_ACTIVITY_ROLE_STYLE_RULE])
def _classify_daily_activity_claim_roles(claims: list[dict[str, Any]]) -> dict[str, list[str]]:
    primary_anchor_text = "\n".join(_claim_text(claim) for claim in claims if _looks_daily_activity_primary_scene(_claim_text(claim), claim))
    primary_terms = _daily_activity_anchor_terms(primary_anchor_text)
    primary: list[str] = []
    auxiliary_context: list[str] = []
    auxiliary_suppressed: list[str] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id") or "").strip()
        if not claim_id:
            continue
        text = _claim_text(claim)
        if _looks_daily_activity_auxiliary(text, claim):
            if any(term in text for term in _DAILY_ACTIVITY_LIST_TERMS):
                auxiliary_suppressed.append(claim_id)
            elif _is_daily_activity_same_event_notice_context(text) or _is_same_daily_activity_scene(text, primary_terms):
                auxiliary_context.append(claim_id)
            else:
                auxiliary_suppressed.append(claim_id)
            continue
        if _looks_daily_activity_primary_scene(text, claim):
            primary.append(claim_id)
    return {
        "primary_scene_report_claim_ids": _unique_strings(primary),
        "auxiliary_context_claim_ids": _unique_strings(auxiliary_context),
        "auxiliary_suppressed_claim_ids": _unique_strings(auxiliary_suppressed),
    }
def _looks_daily_activity_auxiliary(text: str, claim: dict[str, Any]) -> bool:
    risk_flags = {str(flag) for flag in claim.get("risk_flags") or []}
    return (
        any(term in text for term in _DAILY_ACTIVITY_LIST_TERMS + _DAILY_ACTIVITY_NOTICE_TERMS)
        or bool(risk_flags.intersection({"old_information", "future_dated", "mixed_topics", "ambiguous"}))
        and any(term in text for term in _DAILY_ACTIVITY_EVENT_TERMS)
    )
def _looks_daily_activity_primary_scene(text: str, claim: dict[str, Any]) -> bool:
    if any(term in text for term in _DAILY_ACTIVITY_LIST_TERMS):
        return False
    if "募集案内" in text or "参加者募集" in text:
        return False
    if _looks_daily_activity_auxiliary(text, claim) and not any(term in text for term in _DAILY_ACTIVITY_SCENE_TERMS):
        return False
    return any(term in text for term in _DAILY_ACTIVITY_SCENE_TERMS) or any(term in text for term in _DAILY_ACTIVITY_EVENT_TERMS)
def _is_same_daily_activity_scene(text: str, primary_terms: set[str]) -> bool:
    if not primary_terms:
        return False
    overlap = sum(1 for term in primary_terms if term and term in text)
    date_overlap = bool(set(re.findall(r"20[0-9]{2}年[0-9]{1,2}月[0-9]{1,2}日", text)).intersection(primary_terms))
    return overlap >= 2 or (date_overlap and any(term in text for term in _DAILY_ACTIVITY_EVENT_TERMS))
def _is_daily_activity_same_event_notice_context(text: str) -> bool:
    if any(term in text for term in _DAILY_ACTIVITY_LIST_TERMS):
        return False
    return any(term in text for term in _DAILY_ACTIVITY_NOTICE_TERMS) and bool(re.search(r"20[0-9]{2}年|[0-9]{1,2}:[0-9]{2}|[0-9,]+円|定員|会場|室|締切", text))
def _daily_activity_anchor_terms(text: str) -> set[str]:
    terms = {term for term in _DAILY_ACTIVITY_EVENT_TERMS if term in text}
    terms.update(re.findall(r"20[0-9]{2}年[0-9]{1,2}月[0-9]{1,2}日", text))
    terms.update(re.findall(r"[「『]([^」』]{3,40})[」』]", text))
    return {term for term in terms if term}
def _unique_strings(values: list[Any] | tuple[Any, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
def _planned_sections(brief: dict[str, Any], planned_count: int) -> list[dict[str, Any]]:
    sections = brief.get("sections")
    if not isinstance(sections, list):
        return []
    usable = [section for section in sections if isinstance(section, dict)]
    if not usable:
        return []
    return usable[: max(1, min(int(planned_count), len(usable)))]
def _select_claim_ids(
    claims: list[dict[str, Any]],
    source_shape: str,
    source_use_mode: str,
    section_count: int,
) -> list[str]:
    claim_ids = _claim_ids(claims)
    if source_use_mode == "exhaustive":
        return claim_ids
    claim_count = len(claim_ids)
    base_limit = max(2 if source_shape == "faq" else 3, max(1, int(section_count or 1)) * 2)
    shape_cap = NON_EXHAUSTIVE_SHAPE_CLAIM_CAPS.get(source_shape, 8)
    limit = min(claim_count, max(base_limit, min(claim_count, shape_cap)))
    if limit == claim_count and claim_count > base_limit:
        limit = max(base_limit, claim_count - 1)
    return claim_ids[:limit]
def _split_claim_ids(claim_ids: list[str], section_count: int) -> list[list[str]]:
    if section_count <= 1:
        return [claim_ids]
    chunk_size = max(1, (len(claim_ids) + section_count - 1) // section_count)
    chunks = [claim_ids[index : index + chunk_size] for index in range(0, len(claim_ids), chunk_size)][:section_count]
    while len(chunks) < section_count:
        chunks.append([])
    return chunks
_BOUNDARY_STOP_TERMS = {"生成", "関連", "市場", "事業", "情報", "調査", "報告", "資料", "現時", "source", "読者", "本文", "項目", "実装"}
def _append_v2_style_rule(brief: dict[str, Any], source_use_mode: str, claims: list[dict[str, Any]], selected_set: set[str]) -> None:
    style_rules = brief.get("style_rules")
    if not isinstance(style_rules, list):
        style_rules = []
    if source_use_mode in {"representative", "selective"}:
        terms = _exclusive_unassigned_terms(claims, selected_set)
        style_rules = [rule for rule in style_rules if not _mentions_unassigned_only_topic(str(rule), terms)]
        _filter_section_guidance(brief, terms)
        style_rules.append("未使用claimは根拠確認用に保持し、本文へ全項目として詰め込まない。")
    else:
        style_rules.append("全項目指定があるため、assigned_claim_idsを漏らさず扱う。")
    seen: set[str] = set()
    brief["style_rules"] = [str(rule) for rule in style_rules if str(rule) and not (str(rule) in seen or seen.add(str(rule)))]
def _filter_section_guidance(brief: dict[str, Any], boundary_terms: set[str]) -> None:
    for section in brief.get("sections") or []:
        if not isinstance(section, dict):
            continue
        if isinstance(section.get("discourse_rules"), list):
            section["discourse_rules"] = [str(rule) for rule in section["discourse_rules"] if not _mentions_unassigned_only_topic(str(rule), boundary_terms)]
        for key in ("purpose", "main_subject"):
            if _mentions_unassigned_only_topic(str(section.get(key) or ""), boundary_terms):
                section[key] = "assigned_claim_idsの範囲で扱う。"
def _exclusive_unassigned_terms(claims: list[dict[str, Any]], selected_set: set[str]) -> set[str]:
    assigned_text = "\n".join(_claim_text(claim) for claim in claims if str(claim.get("claim_id") or "") in selected_set)
    terms: set[str] = set()
    for claim in claims:
        if str(claim.get("claim_id") or "") not in selected_set:
            terms.update(term for term in _boundary_terms(_claim_text(claim)) if term not in assigned_text)
    return terms
def _claim_text(claim: dict[str, Any]) -> str:
    return " ".join([str(claim.get("claim") or ""), str(claim.get("preferred_expression") or "")])
def _boundary_terms(text: str) -> set[str]:
    terms = set(re.findall(r"[A-Za-z][A-Za-z0-9.+-]{2,}|[0-9０-９][0-9０-９,，.．%％年月日年度万人億兆]*|[ァ-ヴー]{3,}", text))
    terms.update(re.findall(r"[一-龥々]{2}", text))
    return {term for term in terms if term and term not in _BOUNDARY_STOP_TERMS}
def _mentions_unassigned_only_topic(text: str, boundary_terms: set[str]) -> bool:
    hits = [term for term in boundary_terms if term in text]
    return len(hits) >= 2 or any(len(term) >= 4 for term in hits)
