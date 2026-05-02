"""Comparative review source contract constants and pure helpers."""
from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Sequence

from note.simple_note_pipeline.hidden_late_validation import _hidden_late_source_text
from note.simple_note_pipeline.postprocess import DraftSections
from note.simple_note_pipeline.rendering import build_source_pack


_SHADOW_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")
_COMPARATIVE_SOURCE_SLOTS: tuple[str, ...] = (
    "comparison_context",
    "evaluation_axes",
    "option_differences",
    "fit_conditions",
    "tradeoffs_or_cautions",
    "decision_next_step",
    "price_or_plan",
    "source_limit",
)
_COMPARATIVE_REQUIRED_SOURCE_SLOTS: tuple[str, ...] = (
    "comparison_context",
    "evaluation_axes",
    "option_differences",
    "fit_conditions",
    "tradeoffs_or_cautions",
    "decision_next_step",
)
_COMPARATIVE_SLOT_LABELS = {
    "comparison_context": "比較前提",
    "evaluation_axes": "評価軸",
    "option_differences": "候補差分",
    "fit_conditions": "向く条件",
    "tradeoffs_or_cautions": "注意点",
    "decision_next_step": "確認順",
    "price_or_plan": "価格/プラン",
    "source_limit": "素材制約",
}
_COMPARATIVE_SLOT_PATTERNS = {
    "comparison_context": re.compile(r"(?:比較|選び方|前提|条件|用途|目的|検討|候補|運用)"),
    "evaluation_axes": re.compile(r"(?:評価軸|軸|観点|価格|料金|運用|サポート|導入|承認|責任|監査|移行|定着)"),
    "option_differences": re.compile(r"(?:違い|差|差分|一方|対して|候補|A|B|タイプ|向き|強み|弱み)"),
    "fit_conditions": re.compile(r"(?:向く|合う|適する|場合|条件|チーム|用途|規模|重視|避ける)"),
    "tradeoffs_or_cautions": re.compile(r"(?:注意|留意|懸念|弱み|トレードオフ|ただし|一方で|避ける|確認が必要)"),
    "decision_next_step": re.compile(r"(?:確認|順番|先に|次に|見る|比べる|洗い出|試す|問い合わせ|判断)"),
    "price_or_plan": re.compile(r"(?:価格|料金|費用|無料|有料|プラン|月額|年額|円|万円)"),
    "source_limit": re.compile(r"(?:素材|source|公開情報|範囲|未確認|分からない|記載なし|確認できない)"),
}
_COMPARATIVE_AXIS_LABELS = {
    "price": "価格",
    "cost": "価格",
    "pricing": "価格",
    "approval_flow": "承認フロー",
    "review_flow": "承認フロー",
    "support": "サポート",
    "support_density": "サポート密度 / 導入支援",
    "onboarding": "導入支援",
    "initial_setup": "初期設定",
    "use_case": "用途",
    "fit": "向く条件",
    "auditability": "監査のしやすさ",
    "ownership": "担当責任の置き方",
    "overall": "",
    "総合": "",
}
_COMPARATIVE_GENERIC_MUST_COVER = {
    "総合",
    "全体",
    "差分",
    "違い",
    "用途別の結論",
    "用途別結論",
    "結論",
}
_COMPARATIVE_APPROVAL_RE = re.compile(r"(?:承認|レビュー|部門|チーム|権限|監査|統制)")
_COMPARATIVE_SUPPORT_RE = re.compile(r"(?:サポート|支援|CS|テンプレート|メール|同席|専任)")
_COMPARATIVE_FIT_RE = re.compile(r"(?:向け|向く|合う|適する|単一チーム|複数部門|大規模|監査|要件)")
_COMPARATIVE_PRICE_OR_PLAN_RE = re.compile(
    r"(?:[0-9０-９]+(?:[.,．][0-9０-９]+)?\s*(?:円|万円|ドル|USD|税込|税別)|"
    r"無料|有料|価格|料金|費用|月額|年額|プラン|エンタープライズ|スターター|Pro|Free)",
    flags=re.IGNORECASE,
)
_COMPARATIVE_RESULT_OR_VENDOR_CLAIM_RE = re.compile(
    r"(?:[0-9０-９]+(?:[.,．][0-9０-９]+)?\s*(?:%|％|割|倍|件|時間|分|日|人|社|回|ポイント)|"
    r"成果|実績|削減|改善率|満足度|導入企業|顧客名|受賞|表彰|提携|協業|パートナー|"
    r"No\.?1|シェア|トップ|業界初|唯一|株式会社[一-龥A-Za-z0-9・ー]{1,24}|[一-龥A-Za-z0-9・ー]{1,24}株式会社)",
    flags=re.IGNORECASE,
)
_COMPARATIVE_VISIBLE_EXPERIMENT_TERM_RE = re.compile(
    r"(?:persona|ペルソナ|hidden|editor|full_rewrite|middle_onward|late_35_only|sparse|source_contract|"
    r"comparative_review_source_contract_v1|comparative_01|trial|実験)",
    flags=re.IGNORECASE,
)


def _clean_inline_text(value: Any, *, limit: int = 180) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _extract_shadow_tokens(value: Any, *, limit: int = 4) -> list[str]:
    tokens: list[str] = []
    for token in _SHADOW_TOKEN_RE.findall(_clean_inline_text(value or "", limit=240)):
        normalized = token.lower().strip()
        if re.fullmatch(r"[ぁ-ん]{2,}", normalized):
            continue
        if not normalized or normalized in tokens:
            continue
        tokens.append(normalized)
        if len(tokens) >= limit:
            break
    return tokens


def _normalize_comparative_claim_token(value: Any) -> str:
    text = str(value or "").translate(str.maketrans("０１２３４５６７８９％．，", "0123456789%.,"))
    return re.sub(r"\s+", "", text)


def _comparative_source_contract_scope_active(contract: Mapping[str, Any]) -> bool:
    return str(contract.get("article_type") or "").strip().lower() == "comparative_review"


def _comparative_source_sentences(source_pack: Mapping[str, Any]) -> list[str]:
    source_text = _hidden_late_source_text(source_pack)
    sentences: list[str] = []
    for part in re.split(r"(?<=[。！？!?])\s*|\n+", source_text):
        text = _clean_inline_text(part, limit=220)
        if text and text not in sentences:
            sentences.append(text)
    return sentences[:24]


def _comparative_axis_labels(contract: Mapping[str, Any]) -> list[str]:
    ui_journey = dict(contract.get("ui_journey") or {})
    raw_axes = [
        *list(contract.get("comparison_axes") or []),
        *list(ui_journey.get("comparison_axes") or []),
    ]
    labels: list[str] = []
    for item in raw_axes:
        text = _clean_inline_text(item, limit=80)
        if not text:
            continue
        normalized = re.sub(r"[\s_\-/]+", "_", text.strip().lower())
        label = _COMPARATIVE_AXIS_LABELS.get(normalized, text)
        if not label:
            continue
        for fragment in re.split(r"\s*/\s*", label):
            fragment = _clean_inline_text(fragment, limit=40)
            if fragment and fragment not in labels:
                labels.append(fragment)
    return labels[:5]


def _comparative_first_matching_sentence(sentences: list[str], pattern: re.Pattern[str]) -> str:
    for sentence in sentences:
        if pattern.search(sentence):
            return sentence
    return ""


def _comparative_join_matching_sentences(
    sentences: list[str],
    pattern: re.Pattern[str],
    *,
    limit: int = 2,
) -> str:
    matches: list[str] = []
    for sentence in sentences:
        if not pattern.search(sentence):
            continue
        if sentence not in matches:
            matches.append(sentence)
        if len(matches) >= limit:
            break
    return _clean_inline_text(" ".join(matches), limit=220)


def _comparative_source_backed_fallback_slots(
    contract: Mapping[str, Any],
    sentences: list[str],
) -> tuple[Dict[str, str], set[str], list[str]]:
    if not _comparative_source_contract_scope_active(contract) or not sentences:
        return {}, set(), []

    price_text = _comparative_join_matching_sentences(sentences, _COMPARATIVE_PRICE_OR_PLAN_RE, limit=3)
    approval_text = _comparative_join_matching_sentences(sentences, _COMPARATIVE_APPROVAL_RE, limit=3)
    support_text = _comparative_join_matching_sentences(sentences, _COMPARATIVE_SUPPORT_RE, limit=3)
    fit_text = _comparative_join_matching_sentences(sentences, _COMPARATIVE_FIT_RE, limit=3)
    difference_text = _clean_inline_text(" ".join(sentences[:3]), limit=260)
    axis_labels = _comparative_axis_labels(contract)
    if not axis_labels:
        inferred_axes = [
            ("価格", price_text),
            ("承認フロー", approval_text),
            ("導入支援", support_text),
        ]
        axis_labels = [label for label, evidence in inferred_axes if evidence]

    slots: Dict[str, str] = {}
    source_backed: set[str] = set()
    if axis_labels:
        slots["evaluation_axes"] = "、".join(axis_labels[:4]) + "を見る。"
        source_backed.add("evaluation_axes")
    if difference_text:
        slots["comparison_context"] = _comparative_first_matching_sentence(
            sentences,
            _COMPARATIVE_SLOT_PATTERNS["comparison_context"],
        ) or difference_text
        slots["option_differences"] = difference_text
        source_backed.update({"comparison_context", "option_differences"})
    if fit_text:
        slots["fit_conditions"] = fit_text
        source_backed.add("fit_conditions")
    if price_text:
        slots["price_or_plan"] = price_text
        source_backed.add("price_or_plan")

    caution_parts = [
        item
        for item in (
            price_text,
            approval_text,
            support_text,
            fit_text,
        )
        if item
    ]
    if caution_parts:
        slots["tradeoffs_or_cautions"] = _clean_inline_text(
            " / ".join(caution_parts[:3])
            + "。価格だけでなく、承認範囲と支援体制を合わせて確認する。",
            limit=220,
        )
        source_backed.add("tradeoffs_or_cautions")

    decision_terms = axis_labels or ["価格", "承認フロー", "導入支援"]
    if caution_parts or decision_terms:
        slots["decision_next_step"] = _clean_inline_text(
            "、".join(decision_terms[:4]) + "を見る。",
            limit=180,
        )
        source_backed.add("decision_next_step")

    must_cover = [item for item in axis_labels if item]
    for item in ("向く条件", "注意点", "確認順"):
        if item not in must_cover:
            must_cover.append(item)
    return slots, source_backed, must_cover[:6]


def _comparative_must_cover_is_generic(items: Any) -> bool:
    values = [_clean_inline_text(item, limit=80) for item in list(items or [])]
    values = [item for item in values if item]
    if not values:
        return True
    return all(item in _COMPARATIVE_GENERIC_MUST_COVER for item in values)


def _comparative_slot_from_bucket(bucket: Any) -> str:
    normalized = re.sub(r"[\s_\-/]+", "", str(bucket or "").strip().lower())
    aliases = {
        "comparisoncontext": "comparison_context",
        "context": "comparison_context",
        "比較前提": "comparison_context",
        "比較条件": "comparison_context",
        "evaluationaxes": "evaluation_axes",
        "axis": "evaluation_axes",
        "axes": "evaluation_axes",
        "評価軸": "evaluation_axes",
        "比較軸": "evaluation_axes",
        "optiondifferences": "option_differences",
        "difference": "option_differences",
        "differences": "option_differences",
        "候補差分": "option_differences",
        "差分": "option_differences",
        "fitconditions": "fit_conditions",
        "fit": "fit_conditions",
        "向く条件": "fit_conditions",
        "適合条件": "fit_conditions",
        "tradeoffsorcautions": "tradeoffs_or_cautions",
        "tradeoff": "tradeoffs_or_cautions",
        "caution": "tradeoffs_or_cautions",
        "注意点": "tradeoffs_or_cautions",
        "トレードオフ": "tradeoffs_or_cautions",
        "decisionnextstep": "decision_next_step",
        "nextstep": "decision_next_step",
        "確認順": "decision_next_step",
        "次の確認": "decision_next_step",
        "priceorplan": "price_or_plan",
        "price": "price_or_plan",
        "plan": "price_or_plan",
        "価格": "price_or_plan",
        "プラン": "price_or_plan",
        "sourcelimit": "source_limit",
        "limit": "source_limit",
        "素材制約": "source_limit",
    }
    return aliases.get(normalized, "")


def _build_comparative_runtime_source_contract(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    active = _comparative_source_contract_scope_active(contract)
    slots: Dict[str, str] = {slot: "" for slot in _COMPARATIVE_SOURCE_SLOTS}
    if not active:
        return {
            "checked": True,
            "scope_match": False,
            "pattern": "comparative_review_source_contract_v1",
            "slots": slots,
            "required_slots": list(_COMPARATIVE_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["price_or_plan", "source_limit"],
        }

    explicit_contract = contract.get("comparative_review_source_contract")
    candidate_contract = contract.get("comparative_review_validation_candidate")
    if not isinstance(explicit_contract, Mapping) and isinstance(candidate_contract, Mapping):
        explicit_contract = candidate_contract.get("source_contract")
    has_explicit_contract = isinstance(explicit_contract, Mapping)
    if isinstance(explicit_contract, Mapping):
        for slot in _COMPARATIVE_SOURCE_SLOTS:
            value = _clean_inline_text(explicit_contract.get(slot) or "", limit=180)
            if value:
                slots[slot] = value

    comparison_axes = _comparative_axis_labels(contract)
    if comparison_axes and not slots.get("evaluation_axes"):
        slots["evaluation_axes"] = " / ".join(comparison_axes[:5])

    source_backed_slots: set[str] = set()
    for item in list(source_pack.get("grounding_items") or []):
        if not isinstance(item, Mapping):
            continue
        slot = _comparative_slot_from_bucket(item.get("bucket"))
        value = _clean_inline_text(item.get("fact_text") or "", limit=180)
        if slot and value:
            source_backed_slots.add(slot)
            if not slots.get(slot):
                slots[slot] = value

    sentences = _comparative_source_sentences(source_pack)
    for slot in _COMPARATIVE_SOURCE_SLOTS:
        if slots.get(slot):
            continue
        pattern = _COMPARATIVE_SLOT_PATTERNS.get(slot)
        if not pattern:
            continue
        for sentence in sentences:
            if pattern.search(sentence):
                source_backed_slots.add(slot)
                slots[slot] = sentence
                break

    fallback_slots, fallback_source_slots, fallback_must_cover = _comparative_source_backed_fallback_slots(
        contract,
        sentences,
    )
    for slot, value in fallback_slots.items():
        if not value:
            continue
        if slot == "evaluation_axes" or not slots.get(slot):
            slots[slot] = value
    source_backed_slots.update(fallback_source_slots)

    source_contract_available = bool(
        has_explicit_contract
        or all(slot in source_backed_slots for slot in _COMPARATIVE_REQUIRED_SOURCE_SLOTS)
    )
    if not source_contract_available:
        return {
            "checked": True,
            "scope_match": False,
            "pattern": "comparative_review_source_contract_v1",
            "slots": slots,
            "required_slots": list(_COMPARATIVE_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["price_or_plan", "source_limit"],
            "source_contract_available": False,
            "fallback_must_cover": fallback_must_cover,
        }

    return {
        "checked": True,
        "scope_match": True,
        "pattern": "comparative_review_source_contract_v1",
        "slots": slots,
        "required_slots": list(_COMPARATIVE_REQUIRED_SOURCE_SLOTS),
        "optional_slots": ["price_or_plan", "source_limit"],
        "source_contract_available": True,
        "fallback_must_cover": fallback_must_cover,
    }


def _merge_comparative_runtime_contract_into_payload(
    contract: Mapping[str, Any],
    comparative_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    updated = dict(contract)
    updated["_comparative_review_source_contract"] = dict(comparative_contract)
    if not bool(comparative_contract.get("scope_match")):
        return updated

    slots = dict(comparative_contract.get("slots") or {})
    existing_grounding = [
        dict(item)
        for item in list(updated.get("source_grounding_items") or [])
        if isinstance(item, Mapping)
    ]
    existing_pairs = {
        (
            str(item.get("bucket") or "").strip(),
            _clean_inline_text(item.get("fact_text") or "", limit=180),
        )
        for item in existing_grounding
    }
    for slot in _COMPARATIVE_SOURCE_SLOTS:
        value = _clean_inline_text(slots.get(slot) or "", limit=180)
        if not value:
            continue
        bucket = _COMPARATIVE_SLOT_LABELS.get(slot, slot)
        pair = (bucket, value)
        if pair in existing_pairs:
            continue
        existing_grounding.append(
            {
                "bucket": bucket,
                "fact_text": value,
                "source_title": "comparative review source",
                "locator": "",
            }
        )
        existing_pairs.add(pair)
    updated["source_grounding_items"] = existing_grounding[:12]
    fallback_must_cover = [
        _clean_inline_text(item, limit=80)
        for item in list(comparative_contract.get("fallback_must_cover") or [])
        if _clean_inline_text(item, limit=80)
    ]
    if fallback_must_cover and _comparative_must_cover_is_generic(updated.get("must_cover")):
        updated["must_cover"] = fallback_must_cover

    existing_hints: list[str] = []
    for item in list(updated.get("system_hint_items") or []):
        text = str(item or "").strip()
        if text and text not in existing_hints:
            existing_hints.append(text)
    contract_hints = [
        "比較記事では、同じ評価軸で複数候補を比べ、勝敗ではなく条件別判断に戻す。",
        "向く条件、避ける条件、確認順を後半まで維持し、一般的なおすすめだけで閉じない。",
        "価格、プラン、成果、ベンダー優位は素材にある場合だけ書く。",
    ]
    for hint in contract_hints:
        if hint not in existing_hints:
            existing_hints.append(hint)
    updated["system_hint_items"] = existing_hints[:8]
    return updated


def _prepare_comparative_runtime_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    base_contract = dict(contract)
    initial_source_pack = build_source_pack(base_contract)
    comparative_contract = _build_comparative_runtime_source_contract(base_contract, initial_source_pack)
    return _merge_comparative_runtime_contract_into_payload(base_contract, comparative_contract)


def _comparative_text_for_validation(draft: DraftSections) -> str:
    return "\n".join(str(part or "") for part in (draft.title, draft.lead, draft.body)).strip()


def _comparative_slot_value_reflected(text: str, value: Any) -> bool:
    source_tokens = _extract_shadow_tokens(value, limit=6)
    if not source_tokens:
        return False
    normalized_text = _clean_inline_text(text, limit=2600).lower()
    hit_count = sum(1 for token in source_tokens if token in normalized_text)
    return hit_count >= max(1, min(2, len(source_tokens)))


def _comparative_slot_present(slot: str, text: str, source_value: Any) -> bool:
    if _comparative_slot_value_reflected(text, source_value):
        return True
    pattern = _COMPARATIVE_SLOT_PATTERNS.get(slot)
    return bool(pattern and pattern.search(text))


def _comparative_unsupported_hits(
    text: str,
    source_text: str,
    pattern: re.Pattern[str],
) -> list[str]:
    source_tokens = {
        _normalize_comparative_claim_token(match.group(0))
        for match in pattern.finditer(source_text)
    }
    hits: list[str] = []
    for match in pattern.finditer(text):
        raw = match.group(0)
        normalized = _normalize_comparative_claim_token(raw)
        if normalized and normalized not in source_tokens and raw not in hits:
            hits.append(raw)
    return hits[:8]


def _filter_comparative_unsupported_price_hits(
    hits: Sequence[str],
    slots: Mapping[str, Any],
) -> list[str]:
    has_price_context = bool(
        _clean_inline_text(slots.get("price_or_plan") or "", limit=180)
        or _clean_inline_text(slots.get("source_limit") or "", limit=180)
    )
    if not has_price_context:
        return list(hits)
    generic_price_terms = {"価格", "料金", "費用", "プラン"}
    filtered: list[str] = []
    for hit in hits:
        text = str(hit or "").strip()
        if text in generic_price_terms:
            continue
        filtered.append(text)
    return filtered


def _comparative_ranking_drift(text: str) -> bool:
    return bool(re.search(r"(?:ランキング|順位|第[一二三１２３]位|1位|2位|3位|トップ\d|ベスト\d)", text))


def _comparative_absolute_winner_drift(text: str) -> bool:
    return bool(
        re.search(
            r"(?:これ一択|一択|唯一の正解|絶対に|迷わず|最有力|第一候補|最もおすすめ|一番(?:向く|おすすめ)|"
            r"総合的に勝っている|勝者|優勝|決定版)",
            text,
        )
    )


def _comparative_exaggerated_superiority(text: str) -> bool:
    return bool(re.search(r"(?:圧倒的|完全に上回る|抜群|最高|最強|圧勝|他を寄せ付けない|業界初|唯一)", text))


def _comparative_affiliate_review_tone(text: str) -> bool:
    return bool(
        re.search(
            r"(?:今すぐ|公式サイトへ|申し込みはこちら|キャンペーン|限定|クーポン|ぜひ試して|購入すべき|"
            r"おすすめランキング|アフィリエイト)",
            text,
            flags=re.IGNORECASE,
        )
    )


def _comparative_generic_recommendation_only(text: str, slot_presence: Mapping[str, bool]) -> bool:
    final_text = _clean_inline_text(text[-720:], limit=720)
    generic_close = bool(
        re.search(r"(?:自社に合ったものを選びましょう|まずは確認してみましょう|比較して選ぶことが大切です)", final_text)
    )
    return bool(generic_close and not (slot_presence.get("fit_conditions") and slot_presence.get("tradeoffs_or_cautions")))


def _comparative_wrong_article_type_drift(text: str) -> bool:
    return bool(
        re.search(r"(?:会社紹介|当社は[^。]{0,40}(?:会社|企業)です|事業内容|沿革|創業)", text)
        or re.search(r"(?:お知らせ|開始します|リリース|開催します|ご案内|申し込み)", text)
        or re.search(r"(?:改善前|残った課題|事例です|結果として)", text)
    )


def _comparative_source_contract_failure_count(validation: Mapping[str, Any]) -> int:
    return (
        len(list(validation.get("missing_required_slots") or []))
        + len(list(validation.get("unsupported_price_or_plan_hits") or []))
        + len(list(validation.get("unsupported_result_or_vendor_claim_hits") or []))
        + (1 if bool(validation.get("ranking_drift")) else 0)
        + (1 if bool(validation.get("absolute_winner_drift")) else 0)
        + (1 if bool(validation.get("exaggerated_superiority")) else 0)
        + (1 if bool(validation.get("affiliate_review_tone")) else 0)
        + (1 if bool(validation.get("generic_recommendation_only")) else 0)
        + (1 if bool(validation.get("missing_fit_conditions")) else 0)
        + (1 if bool(validation.get("missing_tradeoff_or_caution")) else 0)
        + (1 if bool(validation.get("wrong_article_type_drift")) else 0)
    )


def _comparative_source_contract_improved(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
) -> bool:
    if not bool(current.get("scope_match")):
        return True
    if bool(repaired.get("unsupported_price_or_plan")) or bool(repaired.get("unsupported_result_or_vendor_claim")):
        return False
    return _comparative_source_contract_failure_count(repaired) < _comparative_source_contract_failure_count(current)


def _evaluate_comparative_source_contract_validation(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    comparative_contract = dict(contract.get("_comparative_review_source_contract") or {})
    if not comparative_contract:
        comparative_contract = _build_comparative_runtime_source_contract(contract, source_pack)
    slots = dict(comparative_contract.get("slots") or {})
    if not _comparative_source_contract_scope_active(contract) or (
        bool(comparative_contract.get("checked")) and not bool(comparative_contract.get("scope_match"))
    ):
        return {
            "checked": True,
            "scope_match": False,
            "pattern": "comparative_review_source_contract_v1",
            "required_slots": list(_COMPARATIVE_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["price_or_plan", "source_limit"],
            "slot_presence": {slot: False for slot in _COMPARATIVE_SOURCE_SLOTS},
            "missing_required_slots": [],
            "ranking_drift": False,
            "absolute_winner_drift": False,
            "unsupported_price_or_plan": False,
            "unsupported_price_or_plan_hits": [],
            "unsupported_result_or_vendor_claim": False,
            "unsupported_result_or_vendor_claim_hits": [],
            "exaggerated_superiority": False,
            "affiliate_review_tone": False,
            "generic_recommendation_only": False,
            "missing_fit_conditions": False,
            "missing_tradeoff_or_caution": False,
            "wrong_article_type_drift": False,
            "visible_leakage_hits": [],
            "repair_trigger_ids": [],
        }

    text = _comparative_text_for_validation(draft)
    source_text = _hidden_late_source_text(source_pack)
    slot_presence: Dict[str, bool] = {}
    for slot in _COMPARATIVE_SOURCE_SLOTS:
        slot_presence[slot] = _comparative_slot_present(slot, text, slots.get(slot))

    missing_required = [
        slot
        for slot in _COMPARATIVE_REQUIRED_SOURCE_SLOTS
        if not bool(slot_presence.get(slot))
    ]
    unsupported_price_hits = _filter_comparative_unsupported_price_hits(
        _comparative_unsupported_hits(text, source_text, _COMPARATIVE_PRICE_OR_PLAN_RE),
        slots,
    )
    unsupported_result_vendor_hits = _comparative_unsupported_hits(
        text,
        source_text,
        _COMPARATIVE_RESULT_OR_VENDOR_CLAIM_RE,
    )
    visible_leakage_hits = []
    for match in _COMPARATIVE_VISIBLE_EXPERIMENT_TERM_RE.finditer(text):
        hit = match.group(0)
        if hit and hit not in visible_leakage_hits:
            visible_leakage_hits.append(hit)

    ranking_drift = _comparative_ranking_drift(text)
    absolute_winner_drift = _comparative_absolute_winner_drift(text)
    exaggerated_superiority = _comparative_exaggerated_superiority(text)
    affiliate_review_tone = _comparative_affiliate_review_tone(text)
    generic_recommendation_only = _comparative_generic_recommendation_only(text, slot_presence)
    missing_fit_conditions = not bool(slot_presence.get("fit_conditions"))
    missing_tradeoff_or_caution = not bool(slot_presence.get("tradeoffs_or_cautions"))
    wrong_type_drift = _comparative_wrong_article_type_drift(text)

    trigger_ids: list[str] = []
    for slot in missing_required:
        trigger_ids.append(f"missing_required_slot:{slot}")
    if unsupported_price_hits:
        trigger_ids.append("unsupported_price_or_plan")
    if unsupported_result_vendor_hits:
        trigger_ids.append("unsupported_result_or_vendor_claim")
    if wrong_type_drift:
        trigger_ids.append("wrong_article_type_drift")
    if ranking_drift:
        trigger_ids.append("ranking_drift")
    if absolute_winner_drift:
        trigger_ids.append("absolute_winner_drift")
    if exaggerated_superiority:
        trigger_ids.append("exaggerated_superiority")
    if generic_recommendation_only:
        trigger_ids.append("generic_recommendation_only")
    if missing_fit_conditions:
        trigger_ids.append("missing_fit_conditions")
    if missing_tradeoff_or_caution:
        trigger_ids.append("missing_tradeoff_or_caution")

    validation = {
        "checked": True,
        "scope_match": _comparative_source_contract_scope_active(contract),
        "pattern": "comparative_review_source_contract_v1",
        "required_slots": list(_COMPARATIVE_REQUIRED_SOURCE_SLOTS),
        "optional_slots": ["price_or_plan", "source_limit"],
        "slot_presence": slot_presence,
        "missing_required_slots": missing_required,
        "ranking_drift": bool(ranking_drift),
        "absolute_winner_drift": bool(absolute_winner_drift),
        "unsupported_price_or_plan": bool(unsupported_price_hits),
        "unsupported_price_or_plan_hits": unsupported_price_hits,
        "unsupported_result_or_vendor_claim": bool(unsupported_result_vendor_hits),
        "unsupported_result_or_vendor_claim_hits": unsupported_result_vendor_hits,
        "exaggerated_superiority": bool(exaggerated_superiority),
        "affiliate_review_tone": bool(affiliate_review_tone),
        "generic_recommendation_only": bool(generic_recommendation_only),
        "missing_fit_conditions": bool(missing_fit_conditions),
        "missing_tradeoff_or_caution": bool(missing_tradeoff_or_caution),
        "wrong_article_type_drift": bool(wrong_type_drift),
        "visible_leakage_hits": visible_leakage_hits[:8],
        "repair_trigger_ids": trigger_ids,
    }
    if not bool(validation["scope_match"]) or not trigger_ids:
        return validation

    repair_instructions: list[str] = []
    for item in list(diagnostics.get("repair_instructions") or []):
        text_item = str(item or "").strip()
        if text_item and text_item not in repair_instructions:
            repair_instructions.append(text_item)
    for line in (
        "比較本文を、比較前提、評価軸、候補差分、向く条件、注意点、次の確認順へ戻す。",
        "勝敗やランキングではなく、同じ評価軸で複数候補を比べる条件別判断にする。",
        "素材にない価格、プラン、成果、ベンダー優位は足さない。",
    ):
        if line not in repair_instructions:
            repair_instructions.append(line)
    diagnostics["repair_instructions"] = repair_instructions[:12]

    soft_warnings: list[str] = []
    for item in list(diagnostics.get("soft_warnings") or []):
        text_item = str(item or "").strip()
        if text_item and text_item not in soft_warnings:
            soft_warnings.append(text_item)
    if "comparative_review:source_contract" not in soft_warnings:
        soft_warnings.append("comparative_review:source_contract")
    diagnostics["soft_warnings"] = soft_warnings[:14]
    diagnostics["repair_trigger_score"] = max(float(diagnostics.get("repair_trigger_score") or 0.0), 0.63)
    diagnostics["repair_required"] = True
    diagnostics["issue_count"] = max(
        int(diagnostics.get("issue_count", 0) or 0),
        len(repair_instructions),
        len(soft_warnings),
        len(trigger_ids),
    )
    diagnostics["severity"] = max(int(diagnostics.get("severity", 0) or 0), 2)
    return validation
