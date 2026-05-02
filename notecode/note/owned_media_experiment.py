"""Standalone experimental route for owned-media blog generation.

This module does not modify the current mainline. It provides a staged
generation path optimized for Japanese owned-media articles where the target
reader is a company or team using owned media in practice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from statistics import pstdev
from typing import Any, Dict, List, Mapping, Optional, Sequence

from note.simple_note_pipeline.postprocess import DraftSections, apply_note_local_edits, parse_tagged_output

DEFAULT_AUDIENCE = "オウンドメディアを活用する企業の担当者"
DEFAULT_SPEAKER = "自社の編集担当"

_JSON_BLOCK_RE = re.compile(r"```json\s*([\s\S]*?)\s*```", re.IGNORECASE)
_JSON_OBJECT_RE = re.compile(r"(\{[\s\S]*\}|\[[\s\S]*\])")
_OFFICIAL_SELF_REFERENCE_RE_TEMPLATE = r"(?:^|[。！？\n])\s*{company}(?:は|が)"
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？])\s*")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")
_HEADING_RE = re.compile(r"^##\s+", re.MULTILINE)
_TOC_HEADING_RE = re.compile(r"^##\s*目次\s*$")
_LEADING_CONNECTIVE_RE = re.compile(r"^(また|そして|さらに|まず|次に|一方で|ただ|ただし|そのうえで|このとき)")
_BODY_TAG_RE = re.compile(r"\[BODY\]\s*([\s\S]*?)\s*\[/BODY\]", re.IGNORECASE)
_EXPLANATORY_EXCEPTION_RE = re.compile(r"(FAQ|例外|誤解|境界|脚注|差し戻し|法務|監修|レビュー|断定|引用|要約|解釈)")
_EXPLANATORY_OPERATIONAL_RE = re.compile(r"(確認|チェック|手順|書き始め|段落|レビュー|直後|見直し|仮置き|次の原稿|次に)")
_EXPLANATORY_SOURCE_FIT_RE = re.compile(r"(一次情報|引用|要約|解釈|脚注|出典|原文|資料|断定|根拠|監修|法務|レビュー|境界)")
_EXPLANATORY_DOCUMENT_EXAMPLE_RE = re.compile(r"(数字|統計|発表|資料|レポート|調査|原文)")


@dataclass(frozen=True)
class OwnedMediaSource:
    title: str
    content: str
    locator: str = ""


@dataclass(frozen=True)
class ArticleTypeProfile:
    key: str
    reader_value: str
    section_focus: tuple[str, ...]
    caution: str
    paragraph_breath: str
    closing_style: str


ARTICLE_TYPE_PROFILES: Dict[str, ArticleTypeProfile] = {
    "announcement": ArticleTypeProfile(
        key="announcement",
        reader_value="対象者が影響と確認事項を迷わず理解できること",
        section_focus=("何が変わるか", "誰に影響するか", "いつまでに何を確認するか"),
        caution="美文調に寄せず、対象者・時期・確認事項を落とさない。",
        paragraph_breath="2文前後の短段落を中心にしつつ、説明が必要な箇所だけ3〜4文へ伸ばす。",
        closing_style="最後は具体的な確認行動で閉じる。",
    ),
    "branding": ArticleTypeProfile(
        key="branding",
        reader_value="自社の価値を売り込みではなく背景と実務感で伝えること",
        section_focus=("どんな状況の読者に向けた話か", "自社が何を重視しているか", "読者にとっての意味"),
        caution="会社案内調・自画自賛・社名反復に寄せない。",
        paragraph_breath="1〜2文の短段落と3〜5文の段落を混在させ、導入だけ少し軽く入る。",
        closing_style="抽象スローガンではなく、読者側の判断材料で閉じる。",
    ),
    "case_study": ArticleTypeProfile(
        key="case_study",
        reader_value="変化だけでなく条件や再現可能性まで伝えること",
        section_focus=("最初に何で迷ったか", "どう直したか", "どの条件なら再現できるか"),
        caution="成功談の美化や、結果だけの抽象総括で閉じない。",
        paragraph_breath="工程説明は3〜4文、気づきや転換点は1〜2文で切る。",
        closing_style="試せる条件か最小ステップで閉じる。",
    ),
    "comparative_review": ArticleTypeProfile(
        key="comparative_review",
        reader_value="比較軸を明確にして判断材料を渡すこと",
        section_focus=("比較軸", "違いが出る場面", "どちらが向くか"),
        caution="中立を崩す煽りや、結論先行の単純化を避ける。",
        paragraph_breath="比較軸ごとに段落を切り、同じ長さの段落を並べない。",
        closing_style="おすすめ対象を分けて閉じる。",
    ),
    "daily_story": ArticleTypeProfile(
        key="daily_story",
        reader_value="日々の実務から読者が使える気づきを持ち帰れること",
        section_focus=("日常の具体場面", "そこから見えたこと", "読者に返せる小さな学び"),
        caution="エッセイ化しすぎず、自分語りだけで終わらせない。",
        paragraph_breath="短段落をやや多めにし、独白のリズムを残しつつ毎文改行は避ける。",
        closing_style="小さな納得や気づきで静かに閉じる。",
    ),
    "explanatory_article": ArticleTypeProfile(
        key="explanatory_article",
        reader_value="複雑な論点を読者の仕事目線で理解しやすく整理すること",
        section_focus=("前提", "誤解しやすい点", "実務での見方"),
        caution="抽象名詞の連打や教科書調に寄せない。",
        paragraph_breath="説明段落は3〜4文、要点整理の箇所だけ短段落を混ぜる。",
        closing_style="読者が次に何を確認すべきかで閉じる。",
    ),
    "industry_analysis": ArticleTypeProfile(
        key="industry_analysis",
        reader_value="市場の変化を比較軸付きで読み解けること",
        section_focus=("前提の変化", "何が評価軸として強まっているか", "意思決定への示唆"),
        caution="評論調の断定や、似た主張の言い換え反復を避ける。",
        paragraph_breath="論点の転換で段落を切り、導入と結びは少し短くする。",
        closing_style="市場観測ではなく意思決定示唆で閉じる。",
    ),
}


@dataclass(frozen=True)
class OwnedMediaExperimentRequest:
    article_type: str
    topic: str
    company_name: str = ""
    audience_profile: str = DEFAULT_AUDIENCE
    speaker_profile: str = DEFAULT_SPEAKER
    length_target_chars: int = 3000
    source_notes: tuple[OwnedMediaSource, ...] = field(default_factory=tuple)
    source_char_threshold: int = 4200
    force_compression: bool = False
    enable_polish: bool = True
    compress_task_type: str = "outline"
    blueprint_task_type: str = "outline"
    draft_task_type: str = "section"
    expand_task_type: str = "outline"
    polish_task_type: str = "outline"

    def normalized(self) -> "OwnedMediaExperimentRequest":
        article_type = str(self.article_type or "").strip().lower()
        if article_type not in ARTICLE_TYPE_PROFILES:
            raise ValueError(f"Unsupported article_type: {article_type}")
        topic = re.sub(r"\s+", " ", str(self.topic or "")).strip()
        if not topic:
            raise ValueError("topic is required")
        company_name = re.sub(r"\s+", " ", str(self.company_name or "")).strip()
        return OwnedMediaExperimentRequest(
            article_type=article_type,
            topic=topic,
            company_name=company_name,
            audience_profile=re.sub(r"\s+", " ", str(self.audience_profile or DEFAULT_AUDIENCE)).strip() or DEFAULT_AUDIENCE,
            speaker_profile=re.sub(r"\s+", " ", str(self.speaker_profile or DEFAULT_SPEAKER)).strip() or DEFAULT_SPEAKER,
            length_target_chars=max(1200, int(self.length_target_chars or 3000)),
            source_notes=tuple(self.source_notes or ()),
            source_char_threshold=max(1200, int(self.source_char_threshold or 4200)),
            force_compression=bool(self.force_compression),
            enable_polish=bool(self.enable_polish),
            compress_task_type=str(self.compress_task_type or "outline"),
            blueprint_task_type=str(self.blueprint_task_type or "outline"),
            draft_task_type=str(self.draft_task_type or "section"),
            expand_task_type=str(self.expand_task_type or "outline"),
            polish_task_type=str(self.polish_task_type or "outline"),
        )


@dataclass(frozen=True)
class ParagraphDiagnostics:
    body_chars: int
    paragraph_count: int
    paragraph_sentence_counts: tuple[int, ...]
    paragraph_sentence_cv: float
    one_sentence_paragraph_ratio: float
    leading_connective_repeat_count: int
    official_company_reference_count: int
    flags: tuple[str, ...]


@dataclass(frozen=True)
class OwnedMediaExperimentResult:
    request: OwnedMediaExperimentRequest
    source_packet: Dict[str, Any]
    blueprint: Dict[str, Any]
    prompts: Dict[str, str]
    responses: Dict[str, str]
    used_compression: bool
    title: str
    lead: str
    body: str
    diagnostics_before_polish: ParagraphDiagnostics
    diagnostics_after_polish: ParagraphDiagnostics
    phase_metadata: Dict[str, Dict[str, Any]]

    @property
    def final_text(self) -> str:
        return f"{self.title}\n\n{self.lead}\n\n{self.body}".strip()


def _phase_tasks(request: OwnedMediaExperimentRequest) -> Dict[str, str]:
    return {
        "compress": request.compress_task_type,
        "blueprint": request.blueprint_task_type,
        "draft": request.draft_task_type,
        "expand": request.expand_task_type,
        "polish": request.polish_task_type,
    }


def _target_body_floor(length_target_chars: int) -> int:
    return max(1600, int(length_target_chars * 0.88))


def _expand_target_ceiling(request: OwnedMediaExperimentRequest) -> int:
    if request.article_type == "daily_story":
        return request.length_target_chars + 650
    return request.length_target_chars + 400


def _needs_expand(request: OwnedMediaExperimentRequest, diagnostics: "ParagraphDiagnostics") -> bool:
    return diagnostics.body_chars < _target_body_floor(request.length_target_chars) or (
        "paragraph_length_uniform" in diagnostics.flags
    )


def _needs_expand_retry(request: OwnedMediaExperimentRequest, diagnostics: "ParagraphDiagnostics") -> bool:
    return request.article_type == "daily_story" and diagnostics.body_chars < _target_body_floor(request.length_target_chars)


def _source_total_chars(sources: Sequence[OwnedMediaSource]) -> int:
    return sum(len(str(item.content or "")) for item in sources)


def _use_compression(request: OwnedMediaExperimentRequest) -> bool:
    if request.force_compression:
        return True
    return _source_total_chars(request.source_notes) > request.source_char_threshold


def _extract_json_payload(text: str) -> Optional[Any]:
    raw = str(text or "").strip()
    if not raw:
        return None
    for candidate in (raw, *_JSON_BLOCK_RE.findall(raw)):
        candidate = str(candidate or "").strip()
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    match = _JSON_OBJECT_RE.search(raw)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _extract_body_payload(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    match = _BODY_TAG_RE.search(raw)
    if match:
        return str(match.group(1) or "").strip()
    return raw


def _truncate_text(value: str, *, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _self_reference_policy_text(request: OwnedMediaExperimentRequest) -> str:
    if request.company_name:
        return (
            f"正式社名「{request.company_name}」は本文初出で1回まで。"
            "それ以降は「当社」「私たち」または主語省略を優先し、"
            "正式社名+は を一人称のように繰り返さない。"
        )
    return "本文では「当社」「私たち」または主語省略を優先し、自社を外から説明する書き方を避ける。"


def _meta_narration_policy_text() -> str:
    return "「この記事では」「本記事では」「自社の編集担当として」のように書き手が前に出る言い方を避ける。"


def _expand_focus_hint(request: OwnedMediaExperimentRequest) -> str:
    if request.article_type == "announcement":
        return (
            "- announcement では、薄い節に次のうち2つ以上を足してよい: "
            "期限前後に誰が何を確認するか / 進行中案件と新規案件の判断例 / "
            "FAQや修正依頼の窓口 / 公開遅延懸念と差し戻し減少見込みの両方\n"
            "- announcement では、少なくとも1節を5～7文まで伸ばし、"
            "変更要約だけで止めず『いつ・誰が・何を見れば迷いにくいか』まで具体化する"
        )
    if request.article_type == "daily_story":
        return (
            "- daily_story では、薄い節に次のうち2つ以上を足してよい: "
            "会議で話が戻った瞬間 / 順番を変えた直後の空気 / 会議後に持ち帰りが決まった感覚\n"
            "- daily_story では、少なくとも1節を4～6文まで伸ばし、"
            "その場の小さな違和感から後半の納得まで時間差を残す"
        )
    return "- 各節で、source にある具体場面・理由・含意のどれを足すかを先に決めてから広げる"


def _expand_shortfall_hint(
    request: OwnedMediaExperimentRequest,
    diagnostics: "ParagraphDiagnostics",
) -> str:
    shortfall = max(0, _target_body_floor(request.length_target_chars) - diagnostics.body_chars)
    if shortfall <= 0:
        return ""
    if request.article_type == "announcement":
        return (
            f"- 今回は本文がまだ {shortfall} 字前後不足している。変更点の言い換えではなく、"
            "薄い節に source-backed な運用詳細だけを補って target に近づける\n"
            "- announcement では、未展開のものを優先して補う: "
            "4月中と5月1日以降で行動がどう変わるか / 進行中案件と新規案件の判断境界 / "
            "テーマ責任者・編集担当まわりのFAQや窓口 / 現場で出ている懸念と判断前提"
        )
    if request.article_type == "daily_story":
        return (
            f"- 今回は本文がまだ {shortfall} 字前後不足している。導入を引き延ばすのではなく、"
            "中盤か後半の薄い節を2か所選び、source にある出来事・会議中の空気・会議後の動きを補う\n"
            "- daily_story では、会議後に誰が何を持ち帰ったか、または次回までの停滞がどう減ったかを"
            "1段落ぶん具体化して入れる"
        )
    return f"- 今回は本文がまだ {shortfall} 字前後不足している。薄い節だけを source-backed に補って target に近づける"


def _accept_expand_retry(
    previous: "ParagraphDiagnostics",
    candidate: "ParagraphDiagnostics",
) -> bool:
    if candidate.official_company_reference_count > previous.official_company_reference_count:
        return False
    if candidate.body_chars >= previous.body_chars + 180:
        return True
    return candidate.body_chars >= previous.body_chars and len(candidate.flags) < len(previous.flags)


def _fallback_source_packet(
    request: OwnedMediaExperimentRequest,
    profile: ArticleTypeProfile,
) -> Dict[str, Any]:
    must_keep_facts: List[str] = []
    source_scenes: List[str] = []
    for source in request.source_notes[:4]:
        title = _truncate_text(source.title or "source", limit=60)
        snippet = _truncate_text(source.content, limit=220)
        if snippet:
            source_scenes.append(f"{title}: {snippet}")
            must_keep_facts.append(snippet)
    if not must_keep_facts:
        must_keep_facts.append(_truncate_text(request.topic, limit=180))
    packet = {
        "topic_core": request.topic,
        "reader_value": profile.reader_value,
        "must_keep_facts": must_keep_facts[:6],
        "useful_scenes": source_scenes[:4],
        "reader_questions": list(profile.section_focus[:3]),
        "forbidden_assumptions": [
            "自社を正式社名+は で一人称のように繰り返さない",
            "会社紹介文のような定型句に寄せない",
            "毎段落を同じ長さにしない",
        ],
        "self_reference_policy": _self_reference_policy_text(request),
        "paragraph_breath_cues": [
            "話題転換で改行する",
            "毎文改行しない",
            "1〜2文段落と3〜5文段落を混在させる",
        ],
        "source_count": len(request.source_notes),
    }
    return _with_explanatory_late_evidence_reservation(request, packet)


def _fallback_blueprint(
    request: OwnedMediaExperimentRequest,
    profile: ArticleTypeProfile,
    source_packet: Mapping[str, Any],
) -> Dict[str, Any]:
    section_roles = list(profile.section_focus)
    section_plan = []
    for index, role in enumerate(section_roles, start=1):
        section_plan.append(
            {
                "heading": role,
                "purpose": role,
                "must_include": list(source_packet.get("must_keep_facts", [])[:2]),
                "paragraph_shape": "short" if index == 1 else "mixed",
                "opening_move": "読者の現場から入る" if index == 1 else "前段を受けて焦点を絞る",
                "close_move": "次の論点につなぐ" if index < len(section_roles) else profile.closing_style,
            }
        )
    blueprint = {
        "title_hint": _truncate_text(request.topic, limit=48),
        "lead_angle": profile.reader_value,
        "stance": "企業の実務知見として語る",
        "self_reference_policy": _self_reference_policy_text(request),
        "paragraph_breath_plan": profile.paragraph_breath,
        "section_plan": section_plan,
    }
    return _apply_explanatory_late_evidence_to_blueprint(request, source_packet, blueprint)


def _section_plan_items(blueprint: Mapping[str, Any]) -> List[Dict[str, Any]]:
    items = blueprint.get("section_plan")
    if not isinstance(items, Sequence):
        return []
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _clone_blueprint_with_section_plan(
    blueprint: Mapping[str, Any],
    section_plan: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    cloned = dict(blueprint)
    cloned["section_plan"] = [dict(item) for item in section_plan]
    return cloned


def _should_use_semantic_split_draft(
    request: OwnedMediaExperimentRequest,
    blueprint: Mapping[str, Any],
) -> bool:
    reservation = blueprint.get("late_evidence_reservation")
    if isinstance(reservation, Mapping) and reservation.get("active"):
        return False
    return (
        request.article_type == "explanatory_article"
        and request.length_target_chars >= 2800
        and len(_section_plan_items(blueprint)) >= 4
    )


def _split_section_plan(
    blueprint: Mapping[str, Any],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    section_plan = _section_plan_items(blueprint)
    if len(section_plan) < 4:
        return section_plan, []
    split_index = max(2, len(section_plan) // 2)
    if len(section_plan) - split_index < 2:
        split_index = len(section_plan) - 2
    return section_plan[:split_index], section_plan[split_index:]


def _semantic_split_body_targets(request: OwnedMediaExperimentRequest) -> Dict[str, tuple[int, int]]:
    total_floor = _target_body_floor(request.length_target_chars)
    total_ceiling = _expand_target_ceiling(request)
    front_floor = max(980, int(total_floor * 0.42))
    front_ceiling = max(front_floor + 180, int(total_ceiling * 0.48))
    back_floor = max(1200, total_floor - front_floor)
    back_ceiling = max(back_floor + 220, total_ceiling - front_floor + 120)
    return {
        "front": (front_floor, front_ceiling),
        "back": (back_floor, back_ceiling),
    }


def _tokenized_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _candidate_tokens(value: str) -> List[str]:
    tokens = [item for item in re.split(r"[、。・/／（）()「」『』:：\s]+", str(value or "")) if len(item) >= 2]
    seen = set()
    unique: List[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique.append(token)
    return unique[:6]


def _text_mentions_candidate(text: str, candidate: str) -> bool:
    compact_text = _tokenized_text(text)
    compact_candidate = _tokenized_text(candidate)
    if not compact_text or not compact_candidate:
        return False
    if compact_candidate in compact_text:
        return True
    tokens = _candidate_tokens(candidate)
    if not tokens:
        return False
    hit_count = sum(1 for token in tokens if token in compact_text)
    return hit_count >= min(2, len(tokens))


def _unique_truncated_items(values: Sequence[str], *, limit: int, max_items: int) -> List[str]:
    kept: List[str] = []
    seen = set()
    for value in values:
        item = _truncate_text(value, limit=limit)
        if not item or item in seen:
            continue
        seen.add(item)
        kept.append(item)
        if len(kept) >= max_items:
            break
    return kept


def _string_items(value: Any) -> List[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _is_explanatory_reservation_placeholder(value: str) -> bool:
    compact = re.sub(r"\s+", "", str(value or ""))
    return compact in {
        "前提",
        "誤解しやすい点",
        "実務での見方",
        "判断境界",
        "FAQ",
        "例外",
    }


def _take_explanatory_reservation_items(
    *candidate_groups: Sequence[str],
    used: set[str],
    limit: int,
    max_items: int,
) -> List[str]:
    kept: List[str] = []
    local_seen = set()
    for group in candidate_groups:
        for value in group:
            item = _truncate_text(value, limit=limit)
            if not item or item in used or item in local_seen:
                continue
            if _is_explanatory_reservation_placeholder(item):
                continue
            local_seen.add(item)
            kept.append(item)
            if len(kept) >= max_items:
                used.update(kept)
                return kept
    used.update(kept)
    return kept


def _explanatory_prefers_document_examples(
    request: OwnedMediaExperimentRequest,
    source_packet: Mapping[str, Any],
) -> bool:
    candidates: List[str] = [request.topic]
    for source in request.source_notes[:5]:
        candidates.append(str(source.title or ""))
        candidates.append(str(source.content or ""))
    candidates.extend(_string_items(source_packet.get("must_keep_facts")))
    candidates.extend(_string_items(source_packet.get("useful_scenes")))
    return any(_EXPLANATORY_DOCUMENT_EXAMPLE_RE.search(str(item or "")) for item in candidates)


def _explanatory_generic_reservations(
    request: OwnedMediaExperimentRequest,
    source_packet: Mapping[str, Any],
) -> Dict[str, List[str]]:
    if _explanatory_prefers_document_examples(request, source_packet):
        specific_fact_fallback = "数字や発表内容を出した直後は、事実と見方を段落で分けると確認しやすい"
        operational_fallback = "数字や発表内容を置いた段落の直後で、自社の見方を分けて置く"
    else:
        specific_fact_fallback = "事実と見方が同じ段落に乗ると、確認の論点が増えやすい"
        operational_fallback = "根拠を置いた段落の次で、自社の見方を分けて置く"
    return {
        "specific_facts": _unique_truncated_items(
            [
                "脚注だけでは本文内の境界は伝わりきらない",
                specific_fact_fallback,
            ],
            limit=90,
            max_items=2,
        ),
        "faq_or_exceptions": _unique_truncated_items(
            [
                "引用・要約・解釈が同じ流れににじむと、本文だけ読んだ人には自社の断定に見えやすい",
                "資料名を並べるだけでは、読者は何をどう見ればいいか判断しにくい",
            ],
            limit=90,
            max_items=2,
        ),
        "operational_details": _unique_truncated_items(
            [
                "書き始める前に、各段落が引用・要約・解釈のどれかを仮置きしておく",
                operational_fallback,
            ],
            limit=90,
            max_items=2,
        ),
        "next_actions": _unique_truncated_items(
            [
                "次の原稿では、差し戻しが起きやすい段落だけでも引用・要約・解釈のどれかを先に決める",
            ],
            limit=90,
            max_items=1,
        ),
        "close_takeaways": _unique_truncated_items(
            [
                "脚注より先に、本文だけで根拠と見方の境界が追える状態を優先する",
            ],
            limit=90,
            max_items=1,
        ),
    }


def _is_explanatory_source_fit(
    request: OwnedMediaExperimentRequest,
    candidate: str,
) -> bool:
    text = str(candidate or "").strip()
    if not text:
        return False
    if _EXPLANATORY_SOURCE_FIT_RE.search(text):
        return True
    topic_tokens = [
        token
        for token in _candidate_tokens(request.topic)
        if token not in {"記事", "実務", "担当者", "説明する", "整理する", "迷いにくい", "噛み砕いて"}
    ]
    compact = _tokenized_text(text)
    hit_count = sum(1 for token in topic_tokens if token and token in compact)
    return hit_count >= 2


def _build_explanatory_late_evidence_reservation(
    request: OwnedMediaExperimentRequest,
    source_packet: Mapping[str, Any],
) -> Dict[str, Any]:
    raw_reservation = source_packet.get("late_evidence_reservation")
    reservation_payload = dict(raw_reservation) if isinstance(raw_reservation, Mapping) else {}
    generic = _explanatory_generic_reservations(request, source_packet)
    note_fragments: List[str] = []
    for source in request.source_notes[:5]:
        title = _truncate_text(source.title, limit=48)
        snippet = _truncate_text(source.content, limit=110)
        fragment = f"{title}: {snippet}".strip(": ")
        if fragment:
            note_fragments.append(fragment)

    must_keep_facts = _string_items(source_packet.get("must_keep_facts"))
    useful_scenes = _string_items(source_packet.get("useful_scenes"))
    reader_questions = _string_items(source_packet.get("reader_questions"))
    relevant_must_keep_facts = [item for item in must_keep_facts if _is_explanatory_source_fit(request, item)]
    relevant_useful_scenes = [item for item in useful_scenes if _is_explanatory_source_fit(request, item)]
    relevant_note_fragments = [item for item in note_fragments if _is_explanatory_source_fit(request, item)]
    combined_candidates = [*relevant_must_keep_facts, *relevant_useful_scenes, *relevant_note_fragments]
    fact_candidates = [
        item
        for item in combined_candidates
        if not _EXPLANATORY_EXCEPTION_RE.search(item) and not _EXPLANATORY_OPERATIONAL_RE.search(item)
    ]
    filtered_reader_questions = [
        item
        for item in reader_questions
        if not _is_explanatory_reservation_placeholder(item)
        and (
            _is_explanatory_source_fit(request, item)
            or _EXPLANATORY_EXCEPTION_RE.search(item)
            or _EXPLANATORY_OPERATIONAL_RE.search(item)
        )
    ]
    used_items: set[str] = set()

    def _pick_matches(pattern: re.Pattern[str], *, limit: int, fallback: Sequence[str]) -> List[str]:
        matched = [item for item in combined_candidates if pattern.search(item)]
        if not matched and filtered_reader_questions:
            matched = [item for item in filtered_reader_questions if pattern.search(item)]
        return _unique_truncated_items([*matched, *fallback], limit=90, max_items=limit)

    specific_facts = _take_explanatory_reservation_items(
        _string_items(reservation_payload.get("specific_facts"))
        or fact_candidates
        or relevant_must_keep_facts[1:]
        or relevant_useful_scenes[-2:],
        generic["specific_facts"],
        used=used_items,
        limit=90,
        max_items=2,
    )
    faq_or_exceptions = _take_explanatory_reservation_items(
        _string_items(reservation_payload.get("faq_or_exceptions"))
        or _pick_matches(
            _EXPLANATORY_EXCEPTION_RE,
            limit=2,
            fallback=[*filtered_reader_questions[1:], *generic["faq_or_exceptions"]],
        ),
        generic["faq_or_exceptions"],
        used=used_items,
        limit=90,
        max_items=2,
    )
    operational_details = _take_explanatory_reservation_items(
        _string_items(reservation_payload.get("operational_details"))
        or _pick_matches(
            _EXPLANATORY_OPERATIONAL_RE,
            limit=2,
            fallback=[*filtered_reader_questions, *generic["operational_details"]],
        ),
        generic["operational_details"],
        used=used_items,
        limit=90,
        max_items=2,
    )
    next_actions = _take_explanatory_reservation_items(
        _string_items(reservation_payload.get("next_actions")),
        generic["next_actions"],
        used=used_items,
        limit=90,
        max_items=1,
    )
    close_takeaways = _take_explanatory_reservation_items(
        _string_items(reservation_payload.get("close_takeaways")),
        generic["close_takeaways"],
        used=used_items,
        limit=90,
        max_items=1,
    )

    active = any((specific_facts, faq_or_exceptions, operational_details, next_actions, close_takeaways))
    return {
        "active": active,
        "specific_facts": specific_facts,
        "faq_or_exceptions": faq_or_exceptions,
        "operational_details": operational_details,
        "next_actions": next_actions,
        "close_takeaways": close_takeaways,
    }


def _with_explanatory_late_evidence_reservation(
    request: OwnedMediaExperimentRequest,
    source_packet: Mapping[str, Any],
) -> Dict[str, Any]:
    normalized = dict(source_packet)
    if request.article_type != "explanatory_article":
        return normalized
    normalized["late_evidence_reservation"] = _build_explanatory_late_evidence_reservation(request, normalized)
    return normalized


def _apply_explanatory_late_evidence_to_blueprint(
    request: OwnedMediaExperimentRequest,
    source_packet: Mapping[str, Any],
    blueprint: Mapping[str, Any],
) -> Dict[str, Any]:
    if request.article_type != "explanatory_article":
        return dict(blueprint)

    reservation = source_packet.get("late_evidence_reservation")
    if not isinstance(reservation, Mapping) or not reservation.get("active"):
        return dict(blueprint)

    section_plan = _section_plan_items(blueprint)
    if len(section_plan) < 3:
        cloned = dict(blueprint)
        cloned["late_evidence_reservation"] = dict(reservation)
        return cloned

    late_indices = [max(1, len(section_plan) - 2), len(section_plan) - 1]
    late_indices = sorted(set(index for index in late_indices if 0 <= index < len(section_plan)))
    late_assignments: Dict[int, List[str]] = {}
    middle_items = _unique_truncated_items(
        [*_string_items(reservation.get("specific_facts")), *_string_items(reservation.get("faq_or_exceptions"))],
        limit=90,
        max_items=3,
    )
    closing_items = _unique_truncated_items(
        [
            *_string_items(reservation.get("operational_details")),
            *_string_items(reservation.get("next_actions")),
            *_string_items(reservation.get("close_takeaways")),
        ],
        limit=90,
        max_items=4,
    )
    if len(late_indices) == 1:
        late_assignments[late_indices[0]] = _unique_truncated_items([*middle_items, *closing_items], limit=90, max_items=4)
    else:
        late_assignments[late_indices[0]] = _unique_truncated_items(middle_items, limit=90, max_items=2)
        late_assignments[late_indices[-1]] = _unique_truncated_items(closing_items, limit=90, max_items=3)

    reserved_items = {
        item
        for items in late_assignments.values()
        for item in items
        if item
    }
    early_defaults = [
        item
        for item in _string_items(source_packet.get("must_keep_facts"))[:3]
        if item not in reserved_items
    ]
    updated_sections: List[Dict[str, Any]] = []
    for index, item in enumerate(section_plan):
        updated = dict(item)
        existing = [
            entry
            for entry in _unique_truncated_items(_string_items(updated.get("must_include")), limit=90, max_items=4)
            if entry not in reserved_items
        ]
        if index in late_assignments:
            late_only = late_assignments[index]
            updated["must_include"] = _unique_truncated_items([*late_only, *existing], limit=90, max_items=4)
            updated["late_only"] = late_only
            updated["reservation_phase"] = "late"
        else:
            updated["must_include"] = _unique_truncated_items([*existing, *early_defaults], limit=90, max_items=3)
            updated["late_only"] = []
            updated["reservation_phase"] = "early"
        updated_sections.append(updated)

    cloned = dict(blueprint)
    cloned["section_plan"] = updated_sections
    cloned["late_evidence_reservation"] = {
        **dict(reservation),
        "late_section_headings": [
            str(updated_sections[index].get("heading") or "")
            for index in late_indices
        ],
    }
    return cloned


def _build_overlap_ledger(
    front_body: str,
    *,
    source_packet: Mapping[str, Any],
    front_blueprint: Mapping[str, Any],
    back_blueprint: Mapping[str, Any],
) -> Dict[str, List[str]]:
    front_plan = _section_plan_items(front_blueprint)
    back_plan = _section_plan_items(back_blueprint)
    used_facts: List[str] = []
    for item in front_plan:
        used_facts.extend(str(fact) for fact in item.get("must_include", []) if str(fact).strip())
    if not used_facts:
        used_facts = [str(item) for item in source_packet.get("must_keep_facts", []) if _text_mentions_candidate(front_body, str(item))]

    used_scenes = [
        str(item)
        for item in source_packet.get("useful_scenes", [])
        if _text_mentions_candidate(front_body, str(item))
    ]
    answered_questions: List[str] = []
    front_scope_text = "\n".join(
        " ".join(
            [
                str(item.get("heading") or ""),
                str(item.get("purpose") or ""),
                " ".join(str(part) for part in item.get("must_include", []) if str(part).strip()),
            ]
        )
        for item in front_plan
    )
    for question in source_packet.get("reader_questions", []):
        question_text = str(question)
        if _text_mentions_candidate(front_scope_text, question_text) or _text_mentions_candidate(front_body, question_text):
            answered_questions.append(question_text)

    sentences = [item.strip() for item in _SENTENCE_SPLIT_RE.split(front_body.strip()) if item.strip()]
    close_takeaways = sentences[-2:] if len(sentences) >= 2 else sentences

    pending_slots: List[str] = []
    unanswered = [
        str(question)
        for question in source_packet.get("reader_questions", [])
        if str(question) not in answered_questions
    ]
    pending_slots.extend(unanswered)
    for item in back_plan:
        heading = str(item.get("heading") or "").strip()
        purpose = str(item.get("purpose") or "").strip()
        must_include = [str(part).strip() for part in item.get("must_include", []) if str(part).strip()]
        if heading and purpose and heading != purpose:
            pending_slots.append(f"{heading}: {purpose}")
        elif heading:
            pending_slots.append(heading)
        pending_slots.extend(must_include[:2])

    return {
        "used_major_facts": _unique_truncated_items(used_facts, limit=90, max_items=5),
        "used_specific_scenes": _unique_truncated_items(used_scenes, limit=90, max_items=4),
        "answered_reader_questions": _unique_truncated_items(answered_questions, limit=70, max_items=4),
        "used_close_takeaways": _unique_truncated_items(close_takeaways, limit=85, max_items=2),
        "pending_slots": _unique_truncated_items(pending_slots, limit=80, max_items=6),
    }


def _build_source_packet_prompt(
    request: OwnedMediaExperimentRequest,
    profile: ArticleTypeProfile,
) -> str:
    source_blocks = []
    for index, source in enumerate(request.source_notes, start=1):
        source_blocks.append(
            "\n".join(
                [
                    f"[SOURCE {index}]",
                    f"title: {_truncate_text(source.title, limit=80)}",
                    f"locator: {_truncate_text(source.locator, limit=120)}",
                    f"content: {_truncate_text(source.content, limit=1200)}",
                ]
            )
        )
    joined_sources = "\n\n".join(source_blocks) if source_blocks else "[SOURCE]\ncontent: 追加ソースなし"
    explanatory_rules = ""
    if request.article_type == "explanatory_article":
        explanatory_rules = """
- explanatory_article の late_evidence_reservation は JSON object で返す
- late_evidence_reservation の keys は specific_facts / faq_or_exceptions / operational_details / next_actions / close_takeaways
- 後半で初出にしたい具体 fact、FAQ・例外・判断境界、実務上の next action だけを late_evidence_reservation に入れる
""".strip()
    return f"""
あなたは日本語のオウンドメディア編集メモを作るアシスタントです。
記事本文はまだ書かず、生成用の圧縮メモだけを JSON で返してください。

[goal]
- article_type: {request.article_type}
- topic: {request.topic}
- target_reader: {request.audience_profile}
- reader_value: {profile.reader_value}
- self_reference_policy: {_self_reference_policy_text(request)}

[required_json_keys]
- topic_core
- must_keep_facts
- useful_scenes
- reader_questions
- late_evidence_reservation
- forbidden_assumptions
- self_reference_policy
- paragraph_breath_cues

[rules]
- 断定してよい事実だけを must_keep_facts に入れる
- useful_scenes には本文で具体場面に使える断片だけを入れる
- forbidden_assumptions には AI っぽくなりやすい禁止事項を短く入れる
- paragraph_breath_cues には改行タイミングの指示を3つ以内で入れる
- late_evidence_reservation が不要な article_type では空 object {{}} を返してよい
{explanatory_rules}
- JSON 以外は出力しない

[sources]
{joined_sources}
""".strip()


def _build_blueprint_prompt(
    request: OwnedMediaExperimentRequest,
    profile: ArticleTypeProfile,
    source_packet: Mapping[str, Any],
) -> str:
    packet_json = json.dumps(dict(source_packet), ensure_ascii=False, indent=2)
    explanatory_rule = ""
    if request.article_type == "explanatory_article":
        explanatory_rule = "- explanatory_article では、後半で初出にする FAQ / 例外 / 判断境界 / next action を後ろ2節へ寄せる\n"
    return f"""
あなたは日本語の企業オウンドメディア編集者です。
下の source packet から、3000字前後の記事設計図だけを JSON で返してください。

[goal]
- article_type: {request.article_type}
- topic: {request.topic}
- target_reader: {request.audience_profile}
- reader_value: {profile.reader_value}
- caution: {profile.caution}
- paragraph_breath: {profile.paragraph_breath}

[required_json_keys]
- title_hint
- lead_angle
- stance
- self_reference_policy
- paragraph_breath_plan
- section_plan

[section_plan_item_keys]
- heading
- purpose
- must_include
- paragraph_shape
- opening_move
- close_move

[rules]
- section_plan は 3〜4 節
- heading は読者が読み進めやすい日本語にする
- must_include は短い箇条書きにする
- paragraph_shape は short / mixed / dense のいずれか
- 自社を正式社名+は で一人称のように語らない設計にする
- 毎段落同じ長さにならないよう paragraph_breath_plan を具体化する
{explanatory_rule}- JSON 以外は出力しない

[source_packet]
{packet_json}
""".strip()


def _build_draft_prompt(
    request: OwnedMediaExperimentRequest,
    profile: ArticleTypeProfile,
    source_packet: Mapping[str, Any],
    blueprint: Mapping[str, Any],
) -> str:
    packet_json = json.dumps(dict(source_packet), ensure_ascii=False, indent=2)
    blueprint_json = json.dumps(dict(blueprint), ensure_ascii=False, indent=2)
    length_floor = max(1800, request.length_target_chars - 400)
    length_ceiling = request.length_target_chars + 400
    explanatory_reservation_rules = ""
    explanatory_reservation_json = ""
    reservation = blueprint.get("late_evidence_reservation")
    if request.article_type == "explanatory_article" and isinstance(reservation, Mapping) and reservation.get("active"):
        explanatory_reservation_rules = """
- explanatory_article では、late_evidence_reservation の後半予約項目を前半節で使い切らない
- section_plan に late_only が付いた項目は、その見出しに入るまで先出ししない
- 最後の2節では FAQ / 例外 / 判断境界 / 実務上の next action を少なくとも1つずつ回収する
- 後半を前半の言い換えや総括だけで埋めない
""".strip()
        explanatory_reservation_json = (
            "\n\n[late_evidence_reservation]\n"
            + json.dumps(dict(reservation), ensure_ascii=False, indent=2)
        )
    return f"""
あなたは日本語の企業オウンドメディア編集者です。
source packet と blueprint を使って、自然な日本語ブログ本文を書いてください。

[target]
- article_type: {request.article_type}
- target_reader: {request.audience_profile}
- speaker: {request.speaker_profile}
- target_length_chars: {request.length_target_chars}
- allowed_range_chars: {length_floor}〜{length_ceiling}

[voice_rules]
- {_self_reference_policy_text(request)}
- {_meta_narration_policy_text()}
- 会社紹介文やプレスリリースの定型句に寄せない
- 段落は意味のまとまりで切る
- 毎文改行しない
- 1〜2文段落と3〜5文段落を混在させ、全段落を同じ長さにしない
- 接続詞の段落頭連打を避ける
- 「重要です」「必要です」「〜となります」の連打を避ける
- 読者の現場が見える具体場面を少なくとも1回入れる
- 見出しは blueprint に沿って `## ` 形式で入れる
- 目次は入れない
{explanatory_reservation_rules}

[output_format]
[TITLE]
タイトル
[/TITLE]
[LEAD]
導入文
[/LEAD]
[BODY]
本文
[/BODY]

[profile]
- reader_value: {profile.reader_value}
- caution: {profile.caution}
- paragraph_breath: {profile.paragraph_breath}
- closing_style: {profile.closing_style}

[source_packet]
{packet_json}

[blueprint]
{blueprint_json}
{explanatory_reservation_json}
""".strip()


def _build_split_draft_front_prompt(
    request: OwnedMediaExperimentRequest,
    profile: ArticleTypeProfile,
    source_packet: Mapping[str, Any],
    blueprint: Mapping[str, Any],
    *,
    block_target: tuple[int, int],
) -> str:
    packet_json = json.dumps(dict(source_packet), ensure_ascii=False, indent=2)
    blueprint_json = json.dumps(dict(blueprint), ensure_ascii=False, indent=2)
    headings = [str(item.get("heading") or "") for item in _section_plan_items(blueprint)]
    return f"""
あなたは日本語の企業オウンドメディア編集者です。
この記事は explanatory_article の長文なので、前半ブロックだけを先に書きます。

[target]
- article_type: {request.article_type}
- target_reader: {request.audience_profile}
- speaker: {request.speaker_profile}
- block_scope: 前半
- block_headings: {" / ".join(heading for heading in headings if heading)}
- target_body_chars_for_this_block: {block_target[0]}～{block_target[1]}

[voice_rules]
- {_self_reference_policy_text(request)}
- {_meta_narration_policy_text()}
- 会社紹介文やプレスリリースの定型句に寄せない
- 段落は意味のまとまりで切る
- 毎文改行しない
- 1～2文段落と3～5文段落を混在させる
- この前半では、後半の結論を先取りしすぎない
- 読者が後半で確認したくなる論点を残しつつ、前半だけで話が閉じたように見せない
- 見出しは blueprint に沿って `## ` 形式で入れる
- 目次は入れない

[output_format]
[TITLE]
タイトル
[/TITLE]
[LEAD]
導入文
[/LEAD]
[BODY]
前半本文
[/BODY]

[profile]
- reader_value: {profile.reader_value}
- caution: {profile.caution}
- paragraph_breath: {profile.paragraph_breath}
- closing_style: {profile.closing_style}

[source_packet]
{packet_json}

[blueprint]
{blueprint_json}
""".strip()


def _build_split_draft_back_prompt(
    request: OwnedMediaExperimentRequest,
    profile: ArticleTypeProfile,
    source_packet: Mapping[str, Any],
    blueprint: Mapping[str, Any],
    overlap_ledger: Mapping[str, Sequence[str]],
    *,
    block_target: tuple[int, int],
) -> str:
    packet_json = json.dumps(dict(source_packet), ensure_ascii=False, indent=2)
    blueprint_json = json.dumps(dict(blueprint), ensure_ascii=False, indent=2)
    ledger_json = json.dumps(dict(overlap_ledger), ensure_ascii=False, indent=2)
    headings = [str(item.get("heading") or "") for item in _section_plan_items(blueprint)]
    return f"""
あなたは日本語の企業オウンドメディア編集者です。
この記事は explanatory_article の長文なので、後半ブロックだけを書いてください。
前半はすでに確定しているため、overlap ledger を見て重複を避けます。

[target]
- article_type: {request.article_type}
- target_reader: {request.audience_profile}
- speaker: {request.speaker_profile}
- block_scope: 後半
- block_headings: {" / ".join(heading for heading in headings if heading)}
- target_body_chars_for_this_block: {block_target[0]}～{block_target[1]}

[back_half_rules]
- {_self_reference_policy_text(request)}
- {_meta_narration_policy_text()}
- 見出しは blueprint に沿って `## ` 形式で入れる
- 前半の言い換え禁止
- 同じ論点の総括禁止
- overlap ledger にある used_major_facts / used_specific_scenes / answered_reader_questions / used_close_takeaways をなぞらない
- overlap ledger の pending_slots にある未充足 slot のみ補う
- FAQ・例外・判断境界・読者が誤解しやすい点のうち、まだ未充足のものを優先する
- 新しい事実や unsupported な主張は足さない
- 後半に入ってすぐ結論へ寄せず、残りの節ごとに新しい具体点を足す
- 段落は意味のまとまりで切り、1～2文段落と3～5文段落を混在させる
- 毎文改行しない
- 目次は入れない

[output_format]
[BODY]
後半本文
[/BODY]

[profile]
- reader_value: {profile.reader_value}
- caution: {profile.caution}
- paragraph_breath: {profile.paragraph_breath}
- closing_style: {profile.closing_style}

[overlap_ledger]
{ledger_json}

[source_packet]
{packet_json}

[blueprint]
{blueprint_json}
""".strip()


def _polish_focus_hint(request: OwnedMediaExperimentRequest) -> str:
    if request.article_type == "daily_story":
        return (
            "- daily_story では、4文以上の密度段落だけに寄せず、回想や気づきの橋渡しになる短段落を2〜4個は残す\n"
            "- daily_story では、静かな独白の呼吸を説明段落に均しすぎず、短段落と密度段落の交互感を優先する"
        )
    return ""


def _build_polish_prompt(
    request: OwnedMediaExperimentRequest,
    diagnostics: ParagraphDiagnostics,
    draft: DraftSections,
) -> str:
    flags = ", ".join(diagnostics.flags) if diagnostics.flags else "none"
    return f"""
あなたは日本語の企業オウンドメディアの仕上げ編集者です。
下の draft を、内容を変えすぎず surface だけ自然化してください。

[focus_flags]
{flags}

[edit_rules]
- {_self_reference_policy_text(request)}
- {_meta_narration_policy_text()}
- 正式社名+は を一人称のように使っていたら直す
- 段落の長さが一律なら、意味のまとまりを保って再配置する
- 橋渡しになる一文は1文段落として独立させてよい
- 関連する説明はまとめて、少なくとも一部は4文以上の密度段落にする
- {_polish_focus_hint(request)}
- 毎文改行に見える箇所はまとめる
- 逆に説明が詰まりすぎる箇所は短く切る
- 見出し構成は維持する
- 事実や主張の追加はしない

[output_format]
[TITLE]
タイトル
[/TITLE]
[LEAD]
導入文
[/LEAD]
[BODY]
本文
[/BODY]

[draft]
[TITLE]
{draft.title}
[/TITLE]
[LEAD]
{draft.lead}
[/LEAD]
[BODY]
{draft.body}
[/BODY]
""".strip()


def _build_expand_prompt(
    request: OwnedMediaExperimentRequest,
    profile: ArticleTypeProfile,
    source_packet: Mapping[str, Any],
    blueprint: Mapping[str, Any],
    diagnostics: ParagraphDiagnostics,
    draft: DraftSections,
) -> str:
    packet_json = json.dumps(dict(source_packet), ensure_ascii=False, indent=2)
    blueprint_json = json.dumps(dict(blueprint), ensure_ascii=False, indent=2)
    flags = ", ".join(diagnostics.flags) if diagnostics.flags else "none"
    target_floor = _target_body_floor(request.length_target_chars)
    target_ceiling = _expand_target_ceiling(request)
    return f"""
あなたは日本語の企業オウンドメディア編集者です。
下の draft は論旨は使える一方で、文字量や段落呼吸が不足しています。
構成を壊さずに中身を厚くし、AIらしい均一さを減らしてください。

[target]
- article_type: {request.article_type}
- target_reader: {request.audience_profile}
- speaker: {request.speaker_profile}
- target_body_chars: {target_floor}〜{target_ceiling}

[focus_flags]
{flags}

[expand_rules]
- {_self_reference_policy_text(request)}
- {_meta_narration_policy_text()}
- 見出し構成は維持する
- 新しい事実や unsupported な主張は足さない
- 薄い箇所だけを広げ、全段落を均等に長くしない
- 各節で必要に応じて次のどれかを1つだけ補う: 具体場面 / 理由 / 読者への含意
- 本文全体で1文段落を1〜2個まで許容し、4文以上の段落も少なくとも2個は作る
- 1〜2文段落、3〜4文段落、やや密度の高い段落を混在させる
- 毎文改行しない
- 説明を言い換えて水増ししない
- 会社案内調やプレスリリース調に寄せない
{_expand_focus_hint(request)}
{_expand_shortfall_hint(request, diagnostics)}

[profile]
- reader_value: {profile.reader_value}
- caution: {profile.caution}
- paragraph_breath: {profile.paragraph_breath}
- closing_style: {profile.closing_style}

[output_format]
[TITLE]
タイトル
[/TITLE]
[LEAD]
導入文
[/LEAD]
[BODY]
本文
[/BODY]

[source_packet]
{packet_json}

[blueprint]
{blueprint_json}

[draft]
[TITLE]
{draft.title}
[/TITLE]
[LEAD]
{draft.lead}
[/LEAD]
[BODY]
{draft.body}
[/BODY]
""".strip()


def _paragraphs(body: str) -> List[str]:
    chunks = [chunk.strip() for chunk in _PARAGRAPH_SPLIT_RE.split(str(body or "").strip()) if chunk.strip()]
    return [chunk for chunk in chunks if not _HEADING_RE.match(chunk)]


def _strip_toc_block(body: str) -> str:
    lines = str(body or "").splitlines()
    if not lines:
        return ""
    kept: List[str] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if _TOC_HEADING_RE.match(stripped):
            index += 1
            while index < len(lines):
                candidate = lines[index].strip()
                if _HEADING_RE.match(candidate):
                    break
                if not candidate or candidate.startswith(("-", "*")) or re.match(r"^\d+\.\s", candidate):
                    index += 1
                    continue
                break
            continue
        kept.append(lines[index])
        index += 1
    compact = "\n".join(kept).strip()
    return re.sub(r"\n{3,}", "\n\n", compact)


def _apply_experiment_local_edits(sections: DraftSections, *, title_hint: str) -> DraftSections:
    edited, _ = apply_note_local_edits(sections, title_hint=title_hint)
    return DraftSections(
        title=edited.title,
        lead=edited.lead,
        body=_strip_toc_block(edited.body),
        hashtags=edited.hashtags,
    )


def _sentence_count(paragraph: str) -> int:
    sentences = [item.strip() for item in _SENTENCE_SPLIT_RE.split(str(paragraph or "").strip()) if item.strip()]
    return max(1, len(sentences))


def analyze_paragraph_breath(body: str, *, company_name: str = "") -> ParagraphDiagnostics:
    paragraphs = _paragraphs(body)
    counts = tuple(_sentence_count(item) for item in paragraphs)
    body_chars = len(str(body or ""))
    paragraph_count = len(paragraphs)
    if not counts:
        return ParagraphDiagnostics(
            body_chars=body_chars,
            paragraph_count=0,
            paragraph_sentence_counts=(),
            paragraph_sentence_cv=0.0,
            one_sentence_paragraph_ratio=0.0,
            leading_connective_repeat_count=0,
            official_company_reference_count=0,
            flags=("empty_body",),
        )
    mean = sum(counts) / len(counts)
    cv = 0.0 if mean <= 0 else pstdev(counts) / mean
    one_sentence_ratio = sum(1 for item in counts if item == 1) / len(counts)
    connective_repeat_count = 0
    previous_connective = ""
    for paragraph in paragraphs:
        first_line = paragraph.splitlines()[0].strip()
        match = _LEADING_CONNECTIVE_RE.match(first_line)
        token = str(match.group(1) if match else "")
        if token and token == previous_connective:
            connective_repeat_count += 1
        previous_connective = token
    official_company_reference_count = 0
    if company_name:
        pattern = re.compile(_OFFICIAL_SELF_REFERENCE_RE_TEMPLATE.format(company=re.escape(company_name)))
        official_company_reference_count = len(pattern.findall(body))
    flags: List[str] = []
    if cv < 0.24 and paragraph_count >= 4:
        flags.append("paragraph_length_uniform")
    if one_sentence_ratio >= 0.72 and paragraph_count >= 4:
        flags.append("one_sentence_paragraph_overuse")
    if connective_repeat_count >= 2:
        flags.append("leading_connective_repeat")
    if official_company_reference_count >= 1:
        flags.append("official_company_name_as_first_person")
    return ParagraphDiagnostics(
        body_chars=body_chars,
        paragraph_count=paragraph_count,
        paragraph_sentence_counts=counts,
        paragraph_sentence_cv=round(cv, 4),
        one_sentence_paragraph_ratio=round(one_sentence_ratio, 4),
        leading_connective_repeat_count=connective_repeat_count,
        official_company_reference_count=official_company_reference_count,
        flags=tuple(flags),
    )


class OwnedMediaExperimentalPipeline:
    """Standalone staged prompt route for owned-media article experiments."""

    def __init__(self, llm_client: Any | None) -> None:
        self._llm_client = llm_client

    def preview(self, request: OwnedMediaExperimentRequest) -> Dict[str, Any]:
        normalized = request.normalized()
        profile = ARTICLE_TYPE_PROFILES[normalized.article_type]
        source_packet_prompt = _build_source_packet_prompt(normalized, profile)
        source_packet = _fallback_source_packet(normalized, profile)
        blueprint_prompt = _build_blueprint_prompt(normalized, profile, source_packet)
        blueprint = _fallback_blueprint(normalized, profile, source_packet)
        draft_prompt = _build_draft_prompt(normalized, profile, source_packet, blueprint)
        return {
            "article_type": normalized.article_type,
            "task_types": _phase_tasks(normalized),
            "use_compression": _use_compression(normalized),
            "semantic_split_candidate": _should_use_semantic_split_draft(normalized, blueprint),
            "source_chars": _source_total_chars(normalized.source_notes),
            "source_packet_prompt_chars": len(source_packet_prompt),
            "blueprint_prompt_chars": len(blueprint_prompt),
            "draft_prompt_chars": len(draft_prompt),
            "self_reference_policy": _self_reference_policy_text(normalized),
        }

    def run(self, request: OwnedMediaExperimentRequest) -> OwnedMediaExperimentResult:
        if self._llm_client is None:
            raise RuntimeError("llm_client is required for live generation")

        normalized = request.normalized()
        profile = ARTICLE_TYPE_PROFILES[normalized.article_type]
        prompts: Dict[str, str] = {}
        responses: Dict[str, str] = {}
        phase_metadata: Dict[str, Dict[str, Any]] = {}

        use_compression = _use_compression(normalized)
        if use_compression:
            prompts["compress"] = _build_source_packet_prompt(normalized, profile)
            responses["compress"] = self._llm_client.generate_text(
                prompts["compress"],
                max_tokens=2200,
                task_type=normalized.compress_task_type,
                article_type=normalized.article_type,
                verbosity="low",
            )
            phase_metadata["compress"] = self._safe_last_call_metadata()
            payload = _extract_json_payload(responses["compress"])
            source_packet = payload if isinstance(payload, Mapping) else _fallback_source_packet(normalized, profile)
        else:
            source_packet = _fallback_source_packet(normalized, profile)
        source_packet = _with_explanatory_late_evidence_reservation(normalized, source_packet)

        prompts["blueprint"] = _build_blueprint_prompt(normalized, profile, source_packet)
        responses["blueprint"] = self._llm_client.generate_text(
            prompts["blueprint"],
            max_tokens=2200,
            task_type=normalized.blueprint_task_type,
            article_type=normalized.article_type,
            verbosity="low",
        )
        phase_metadata["blueprint"] = self._safe_last_call_metadata()
        blueprint_payload = _extract_json_payload(responses["blueprint"])
        blueprint = blueprint_payload if isinstance(blueprint_payload, Mapping) else _fallback_blueprint(normalized, profile, source_packet)
        blueprint = _apply_explanatory_late_evidence_to_blueprint(normalized, source_packet, blueprint)

        draft_sections = self._run_draft_phase(
            normalized,
            profile,
            source_packet,
            blueprint,
            prompts=prompts,
            responses=responses,
            phase_metadata=phase_metadata,
        )
        diagnostics_before = analyze_paragraph_breath(draft_sections.body, company_name=normalized.company_name)

        final_sections = draft_sections
        working_diagnostics = diagnostics_before
        if _needs_expand(normalized, diagnostics_before):
            prompts["expand"] = _build_expand_prompt(
                normalized,
                profile,
                source_packet,
                blueprint,
                diagnostics_before,
                draft_sections,
            )
            responses["expand"] = self._llm_client.generate_text(
                prompts["expand"],
                max_tokens=5600,
                task_type=normalized.expand_task_type,
                article_type=normalized.article_type,
                verbosity="high",
            )
            phase_metadata["expand"] = self._safe_last_call_metadata()
            expanded_sections = self._parse_sections(responses["expand"])
            expanded_sections = _apply_experiment_local_edits(expanded_sections, title_hint=draft_sections.title)
            if expanded_sections.body:
                final_sections = expanded_sections
                working_diagnostics = analyze_paragraph_breath(final_sections.body, company_name=normalized.company_name)
                if _needs_expand_retry(normalized, working_diagnostics):
                    prompts["expand_retry"] = _build_expand_prompt(
                        normalized,
                        profile,
                        source_packet,
                        blueprint,
                        working_diagnostics,
                        final_sections,
                    )
                    responses["expand_retry"] = self._llm_client.generate_text(
                        prompts["expand_retry"],
                        max_tokens=5600,
                        task_type=normalized.expand_task_type,
                        article_type=normalized.article_type,
                        verbosity="high",
                    )
                    phase_metadata["expand_retry"] = self._safe_last_call_metadata()
                    retried_sections = self._parse_sections(responses["expand_retry"])
                    retried_sections = _apply_experiment_local_edits(retried_sections, title_hint=final_sections.title)
                    if retried_sections.body:
                        retried_diagnostics = analyze_paragraph_breath(
                            retried_sections.body,
                            company_name=normalized.company_name,
                        )
                        if _accept_expand_retry(working_diagnostics, retried_diagnostics):
                            final_sections = retried_sections
                            working_diagnostics = retried_diagnostics

        diagnostics_after = working_diagnostics
        if normalized.enable_polish and working_diagnostics.flags:
            prompts["polish"] = _build_polish_prompt(normalized, working_diagnostics, final_sections)
            responses["polish"] = self._llm_client.generate_text(
                prompts["polish"],
                max_tokens=5200,
                task_type=normalized.polish_task_type,
                article_type=normalized.article_type,
                verbosity="medium",
            )
            phase_metadata["polish"] = self._safe_last_call_metadata()
            polished_sections = self._parse_sections(responses["polish"])
            polished_sections = _apply_experiment_local_edits(polished_sections, title_hint=final_sections.title)
            if polished_sections.body:
                final_sections = polished_sections
                diagnostics_after = analyze_paragraph_breath(final_sections.body, company_name=normalized.company_name)

        return OwnedMediaExperimentResult(
            request=normalized,
            source_packet=dict(source_packet),
            blueprint=dict(blueprint),
            prompts=prompts,
            responses=responses,
            used_compression=use_compression,
            title=final_sections.title,
            lead=final_sections.lead,
            body=final_sections.body,
            diagnostics_before_polish=diagnostics_before,
            diagnostics_after_polish=diagnostics_after,
            phase_metadata=phase_metadata,
        )

    def _parse_sections(self, raw_text: str) -> DraftSections:
        sections = parse_tagged_output(raw_text)
        if sections.body:
            return sections
        compact = str(raw_text or "").strip()
        if not compact:
            return DraftSections(title="", lead="", body="", hashtags="")
        lines = [line.strip() for line in compact.splitlines() if line.strip()]
        title = lines[0] if lines else ""
        remaining = "\n".join(lines[1:]).strip()
        if "\n\n" not in remaining:
            return DraftSections(title=title, lead="", body=remaining, hashtags="")
        blocks = [block.strip() for block in _PARAGRAPH_SPLIT_RE.split(remaining) if block.strip()]
        lead = blocks[0] if blocks else ""
        body = "\n\n".join(blocks[1:] if len(blocks) > 1 else blocks)
        return DraftSections(title=title, lead=lead, body=body, hashtags="")

    def _safe_last_call_metadata(self) -> Dict[str, Any]:
        getter = getattr(self._llm_client, "get_last_call_metadata", None)
        if not callable(getter):
            return {}
        value = getter()
        return dict(value) if isinstance(value, Mapping) else {}

    def _run_draft_phase(
        self,
        request: OwnedMediaExperimentRequest,
        profile: ArticleTypeProfile,
        source_packet: Mapping[str, Any],
        blueprint: Mapping[str, Any],
        *,
        prompts: Dict[str, str],
        responses: Dict[str, str],
        phase_metadata: Dict[str, Dict[str, Any]],
    ) -> DraftSections:
        split_sections = self._run_semantic_split_draft(
            request,
            profile,
            source_packet,
            blueprint,
            prompts=prompts,
            responses=responses,
            phase_metadata=phase_metadata,
        )
        if split_sections is not None:
            return split_sections

        prompts["draft"] = _build_draft_prompt(request, profile, source_packet, blueprint)
        responses["draft"] = self._llm_client.generate_text(
            prompts["draft"],
            max_tokens=5200,
            task_type=request.draft_task_type,
            article_type=request.article_type,
            verbosity="high",
        )
        phase_metadata["draft"] = self._safe_last_call_metadata()
        draft_sections = self._parse_sections(responses["draft"])
        return _apply_experiment_local_edits(
            draft_sections,
            title_hint=str(blueprint.get("title_hint") or ""),
        )

    def _run_semantic_split_draft(
        self,
        request: OwnedMediaExperimentRequest,
        profile: ArticleTypeProfile,
        source_packet: Mapping[str, Any],
        blueprint: Mapping[str, Any],
        *,
        prompts: Dict[str, str],
        responses: Dict[str, str],
        phase_metadata: Dict[str, Dict[str, Any]],
    ) -> Optional[DraftSections]:
        if not _should_use_semantic_split_draft(request, blueprint):
            return None

        front_plan, back_plan = _split_section_plan(blueprint)
        if not front_plan or not back_plan:
            return None

        split_targets = _semantic_split_body_targets(request)
        front_blueprint = _clone_blueprint_with_section_plan(blueprint, front_plan)
        back_blueprint = _clone_blueprint_with_section_plan(blueprint, back_plan)

        prompts["draft_front"] = _build_split_draft_front_prompt(
            request,
            profile,
            source_packet,
            front_blueprint,
            block_target=split_targets["front"],
        )
        responses["draft_front"] = self._llm_client.generate_text(
            prompts["draft_front"],
            max_tokens=3200,
            task_type=request.draft_task_type,
            article_type=request.article_type,
            verbosity="high",
        )
        phase_metadata["draft_front"] = self._safe_last_call_metadata()
        front_sections = self._parse_sections(responses["draft_front"])
        front_sections = _apply_experiment_local_edits(
            front_sections,
            title_hint=str(blueprint.get("title_hint") or ""),
        )
        if not front_sections.body:
            return None

        overlap_ledger = _build_overlap_ledger(
            front_sections.body,
            source_packet=source_packet,
            front_blueprint=front_blueprint,
            back_blueprint=back_blueprint,
        )
        prompts["draft_back"] = _build_split_draft_back_prompt(
            request,
            profile,
            source_packet,
            back_blueprint,
            overlap_ledger,
            block_target=split_targets["back"],
        )
        responses["draft_back"] = self._llm_client.generate_text(
            prompts["draft_back"],
            max_tokens=3400,
            task_type=request.draft_task_type,
            article_type=request.article_type,
            verbosity="high",
        )
        phase_metadata["draft_back"] = self._safe_last_call_metadata()
        phase_metadata["draft_back"]["semantic_split"] = {
            "used_overlap_ledger": True,
            "pending_slots": list(overlap_ledger.get("pending_slots") or []),
        }
        back_body = _strip_toc_block(_extract_body_payload(responses["draft_back"]))
        if not back_body:
            return None

        merged_body = re.sub(
            r"\n{3,}",
            "\n\n",
            "\n\n".join(part.strip() for part in (front_sections.body, back_body) if part.strip()),
        ).strip()
        merged_sections = DraftSections(
            title=front_sections.title,
            lead=front_sections.lead,
            body=merged_body,
            hashtags="",
        )
        return _apply_experiment_local_edits(merged_sections, title_hint=front_sections.title or str(blueprint.get("title_hint") or ""))
