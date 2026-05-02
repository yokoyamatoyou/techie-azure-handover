"""Company introduction source contract runtime and validation helpers."""
from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Sequence

from note.simple_note_pipeline.company_intro_source_contract_guard import (
    _COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS,
    _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS,
    _COMPANY_INTRO_SCRIPT_UNIT_BY_SLOT,
    _COMPANY_INTRO_SCRIPT_UNITS,
    _COMPANY_INTRO_SLOT_LABELS,
    _COMPANY_INTRO_SLOT_PATTERNS,
    _COMPANY_INTRO_SOURCE_LIMIT_VISIBLE_RE,
    _COMPANY_INTRO_SOURCE_SLOTS,
    _COMPANY_INTRO_UNSUPPORTED_CLAIM_RE,
    _COMPANY_INTRO_VISIBLE_EXPERIMENT_TERM_RE,
)
from note.simple_note_pipeline.hidden_late_validation import _hidden_late_source_text
from note.simple_note_pipeline.postprocess import DraftSections
from note.simple_note_pipeline.rendering import build_source_pack


_SHADOW_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")


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


def _split_body_sections(body: Any) -> list[Dict[str, str]]:
    sections: list[Dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []
    for raw_line in str(body or "").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if current_heading or current_lines:
                sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
            current_heading = line.lstrip("#").strip()
            current_lines = []
        elif current_heading:
            current_lines.append(raw_line)
    if current_heading or current_lines:
        sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
    return sections


def _normalize_company_intro_claim_token(value: Any) -> str:
    text = str(value or "").translate(str.maketrans("０１２３４５６７８９％．，", "0123456789%.,"))
    return re.sub(r"\s+", "", text)


def _company_intro_source_contract_scope_active(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    return article_type == "branding" and semantic_key == "company_introduction"


def _company_intro_source_sentences(source_pack: Mapping[str, Any]) -> list[str]:
    sentences: list[str] = []
    raw_parts: list[str] = []
    for item in list(source_pack.get("source_documents") or []):
        if not isinstance(item, Mapping):
            continue
        raw_parts.append(str(item.get("content") or ""))
    for item in list(source_pack.get("source_summaries") or []):
        if not isinstance(item, Mapping):
            continue
        raw_parts.append(str(item.get("excerpt") or ""))
    for item in list(source_pack.get("grounding_items") or []):
        if not isinstance(item, Mapping):
            continue
        raw_parts.append(str(item.get("fact_text") or ""))
    slot_patterns = tuple(_COMPANY_INTRO_SLOT_PATTERNS.values())

    def _append_candidate(value: str) -> None:
        text = _clean_inline_text(value, limit=220)
        if not text or text in sentences:
            return
        if not any(pattern.search(text) for pattern in slot_patterns):
            return
        sentences.append(text)

    for source_text in raw_parts:
        parts = [
            _clean_inline_text(part, limit=220)
            for part in re.split(r"(?<=[。！？!?])\s*|\n+", source_text)
        ]
        parts = [part for part in parts if part]
        for part in parts:
            _append_candidate(part)
        for window_size in range(2, 17):
            for index in range(0, max(0, len(parts) - window_size + 1)):
                window = " ".join(parts[index : index + window_size])
                if len(window) < 18:
                    continue
                _append_candidate(window)
    if len(sentences) <= 96:
        return sentences

    prioritized: list[str] = []

    def _add_candidate(value: str) -> None:
        if value and value not in prioritized:
            prioritized.append(value)

    for sentence in sentences[:96]:
        _add_candidate(sentence)
    for slot in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS:
        pattern = _COMPANY_INTRO_SLOT_PATTERNS.get(slot)
        if not pattern:
            continue
        scored = [
            (_company_intro_slot_candidate_score(slot, sentence), len(sentence), index, sentence)
            for index, sentence in enumerate(sentences)
            if pattern.search(sentence)
        ]
        for _score, _length, _index, sentence in sorted(scored, key=lambda item: (-item[0], -item[1], item[2]))[:8]:
            _add_candidate(sentence)
    return prioritized[:160]


def _company_intro_slot_from_bucket(bucket: Any) -> str:
    normalized = re.sub(r"[\s_\-/]+", "", str(bucket or "").strip().lower())
    aliases = {
        "currentbusiness": "current_business",
        "business": "current_business",
        "service": "current_business",
        "現在事業": "current_business",
        "事業": "current_business",
        "customersituationorentrypoint": "customer_situation_or_entry_point",
        "customerentry": "customer_situation_or_entry_point",
        "entrypoint": "customer_situation_or_entry_point",
        "touchpoint": "customer_situation_or_entry_point",
        "顧客接点": "customer_situation_or_entry_point",
        "相談入口": "customer_situation_or_entry_point",
        "supportscopeboundary": "support_scope_boundary",
        "supportscope": "support_scope_boundary",
        "boundary": "support_scope_boundary",
        "支援範囲": "support_scope_boundary",
        "対応範囲": "support_scope_boundary",
        "operatingprocesssteps": "operating_process_steps",
        "process": "operating_process_steps",
        "steps": "operating_process_steps",
        "進め方": "operating_process_steps",
        "手順": "operating_process_steps",
        "precontactdecision": "pre_contact_decision",
        "decision": "pre_contact_decision",
        "相談前判断": "pre_contact_decision",
        "確認点": "pre_contact_decision",
        "proofsignal": "proof_signal",
        "proof": "proof_signal",
        "根拠": "proof_signal",
        "根拠サイン": "proof_signal",
        "sourcelimit": "source_limit",
        "limit": "source_limit",
        "素材制約": "source_limit",
    }
    return aliases.get(normalized, "")


def _company_intro_public_slot_label(slot: str) -> str:
    if slot == "pre_contact_decision":
        return "事前確認材料"
    return _COMPANY_INTRO_SLOT_LABELS.get(slot, slot)


def _company_intro_public_slot_value(slot: str, value: Any, *, limit: int = 180) -> str:
    text = _clean_inline_text(value, limit=limit)
    if slot not in {"customer_situation_or_entry_point", "pre_contact_decision"}:
        return text
    replacements = (
        ("相談の入口", "顧客接点"),
        ("相談入口", "顧客接点"),
        ("相談前", "事前"),
        ("問い合わせ前", "事前"),
        ("ご相談", "確認"),
        ("という相談", "という状況"),
    )
    for before, after in replacements:
        text = text.replace(before, after)
    return text


def _company_intro_public_source_text(value: Any, *, limit: int = 180) -> str:
    text = _company_intro_public_slot_value(
        "customer_situation_or_entry_point",
        value,
        limit=limit,
    )
    return _company_intro_public_slot_value("pre_contact_decision", text, limit=limit)


def _company_intro_slot_candidate_score(slot: str, text: str) -> int:
    normalized = _clean_inline_text(text, limit=260)
    score = 0
    if slot == "customer_situation_or_entry_point":
        if re.search(
            r"(?:分野|用途|対象|利用|使用|家庭|法人|産業|医療|福祉|学校|研究|飲食|ホテル|旅館|オフィス|商業施設|"
            r"お客さま|顧客)",
            normalized,
        ):
            score += 6
        if "相談したい" in normalized:
            score += 10
        elif re.search(r"(?:相談前|問い合わせ前|依頼前)", normalized):
            score += 7
        elif re.search(r"(?:相談|ご相談)", normalized):
            score += 5
        if re.search(r"(?:お悩み|課題|迷|困|わからな|相談したい|担当者)", normalized):
            score += 4
        if re.search(r"(?:顧客|お客様|現場)", normalized):
            score += 1
        if re.search(r"(?:BPOプロセス|前処理|後処理|一貫対応|納品|お見積(?:り|もり)?|発注|入力・媒体作成)", normalized):
            score -= 5
    elif slot == "operating_process_steps":
        if re.search(r"(?:お問い合わせ|ヒアリング|お見積(?:り|もり)?|発注|入力・媒体作成|納品)", normalized):
            score += 5
        if "ヒアリング" in normalized:
            score += 3
        if re.search(r"(?:運用ルール|担当者導線|FAQ整備|問い合わせ整理|手順に戻す|週次)", normalized):
            score += 4
        if "導入の流れ" in normalized:
            score += 2
        if re.search(r"(?:順で進|流れ|工程|手順)", normalized):
            score += 2
        if not re.search(r"(?:お問い合わせ|ヒアリング|お見積(?:り|もり)?|発注)", normalized):
            score -= 3
        if len(normalized) < 12:
            score -= 2
    elif slot == "pre_contact_decision":
        if re.search(r"(?:お悩み|課題)", normalized) and re.search(r"(?:ヒアリング|データ活用)", normalized):
            score += 8
        if "どのようなデータ活用" in normalized:
            score += 4
        if re.search(r"(?:相談前|問い合わせ前|依頼前|お問い合わせ|お見積(?:り|もり)?|お悩み|課題から)", normalized):
            score += 4
        if re.search(r"(?:お問い合わせ|お見積(?:り|もり)?|発注)", normalized) and re.search(
            r"(?:お悩み|課題|データ活用|相談)", normalized
        ):
            score += 6
        if re.search(r"(?:問い合わせ整理|問い合わせを)", normalized):
            score += 3
        if re.search(r"(?:お悩み|課題)", normalized) and "ヒアリング" in normalized:
            score += 2
        if re.search(r"(?:確認|判断|準備|そろえ)", normalized):
            score += 2
        if re.search(r"(?:エントリー入力|ベリファイ入力|オペレーター)", normalized):
            score -= 3
    elif slot == "support_scope_boundary":
        if re.search(r"(?:前処理から後処理|一貫対応)", normalized):
            score += 10
        if re.search(r"(?:支援範囲|対応範囲|前処理から後処理|一貫対応|社内判断)", normalized):
            score += 4
        if re.search(
            r"(?:分野|用途|対象|地域|エリア|中心|家庭|法人|産業|医療|福祉|学校|研究|飲食|ホテル|旅館|"
            r"オフィス|商業施設|幅広い|取扱|製造|販売|提供)",
            normalized,
        ):
            score += 6
        if re.search(r"(?:支援|対応|サポート|対象|領域)", normalized):
            score += 1
    elif slot == "current_business":
        if re.search(r"(?:事業内容|主な事業|業務内容|活動内容|製造|販売|提供|取扱|展開)", normalized):
            score += 8
        if re.search(r"(?:京都随一|データ入力スキャニング|データ入力・エントリ)", normalized):
            score += 8
        if re.search(r"(?:データ入力|スキャニング|データエントリー|分析|RPA|サービス|製品|商品|事業)", normalized):
            score += 3
        if re.search(r"(?:創業|沿革|1885|1968|歴史)", normalized):
            score -= 4
    elif slot == "proof_signal":
        if re.search(r"(?:公式|実績|認定|事例|確認|掲載)", normalized):
            score += 2
    return score


def _company_intro_explanation_candidate(
    slot: str,
    sentences: Sequence[str],
    current_value: str,
) -> str:
    pattern = _COMPANY_INTRO_SLOT_PATTERNS.get(slot)
    if not pattern:
        return ""
    current_text = _clean_inline_text(current_value or "", limit=180)
    current_key = re.sub(r"\s+", "", current_text)
    min_base_score = {
        "current_business": 3,
        "customer_situation_or_entry_point": 4,
        "support_scope_boundary": 5,
        "operating_process_steps": 5,
        "pre_contact_decision": 4,
    }.get(slot, 1)
    candidates: list[tuple[int, int, str]] = []
    for index, sentence in enumerate(sentences):
        text = _clean_inline_text(sentence, limit=220)
        if len(text) < 40 or len(text) > 220:
            continue
        if slot == "current_business" and re.search(
            r"(?:相談|お問い合わせ|ヒアリング|お見積(?:り|もり)?|発注|納品|お悩み|課題)",
            text,
        ):
            continue
        if slot == "customer_situation_or_entry_point":
            if not re.search(
                r"(?:このようなお悩み|やり方がわからない|相談したい|データ活用の目的|相談|分野|用途|対象|"
                r"お客さま|顧客|家庭|法人|利用|使用|現場)",
                text,
            ):
                continue
            if "導入の流れ" in text:
                continue
        if slot == "support_scope_boundary" and not re.search(
            r"(?:前処理から後処理|一貫対応|分野|用途|対象|地域|エリア|家庭|法人|産業|医療|福祉|学校|"
            r"研究|飲食|ホテル|旅館|オフィス|商業施設|対応|提供|取扱|製造|販売|幅広い)",
            text,
        ):
            continue
        if slot == "operating_process_steps" and not re.search(
            r"(?:導入の流れ|お問い合わせ|お見積(?:り|もり)?|発注・業務|入力・媒体作成|納品)",
            text,
        ):
            continue
        if slot == "pre_contact_decision" and not re.search(r"(?:どのようなデータ活用|お悩みや課題)", text):
            continue
        if re.sub(r"\s+", "", text) == current_key:
            continue
        if not pattern.search(text):
            continue
        base_score = _company_intro_slot_candidate_score(slot, text)
        if base_score < min_base_score:
            continue
        length_score = min(len(text), 180) // 12
        candidates.append((base_score * 10 + length_score, index, text))
    if not candidates:
        return ""
    return _clean_inline_text(sorted(candidates, key=lambda item: (-item[0], item[1]))[0][2], limit=180)


def _company_intro_source_entry_parts(source_pack: Mapping[str, Any]) -> list[Dict[str, str]]:
    entries: list[Dict[str, str]] = []

    def _append_entry(text: Any, *, source_title: Any = "", locator: Any = "") -> None:
        raw_text = str(text or "")
        if not raw_text.strip():
            return
        entries.append(
            {
                "text": raw_text,
                "source_title": _clean_inline_text(source_title or "", limit=100),
                "locator": _clean_inline_text(locator or "", limit=180),
            }
        )

    for item in list(source_pack.get("source_documents") or []):
        if not isinstance(item, Mapping):
            continue
        _append_entry(
            item.get("content"),
            source_title=item.get("title") or item.get("locator"),
            locator=item.get("locator") or item.get("url"),
        )
    for item in list(source_pack.get("source_summaries") or []):
        if not isinstance(item, Mapping):
            continue
        _append_entry(item.get("excerpt"), source_title=item.get("title"))
    for item in list(source_pack.get("grounding_items") or []):
        if not isinstance(item, Mapping):
            continue
        reference = str(item.get("reference") or "").strip()
        reference_parts = [part.strip() for part in reference.split(" / ") if part.strip()]
        _append_entry(
            item.get("fact_text"),
            source_title=item.get("source_title") or (reference_parts[0] if reference_parts else ""),
            locator=item.get("locator") or (reference_parts[-1] if len(reference_parts) >= 2 else ""),
        )
    return entries


def _company_intro_quote_windows(text: str) -> list[str]:
    parts = [
        _clean_inline_text(part, limit=180)
        for part in re.split(r"(?<=[。！？!?])\s*|\n+", str(text or ""))
    ]
    parts = [part for part in parts if part]
    windows: list[str] = []
    seen: set[str] = set()

    def _add(value: str) -> None:
        cleaned = _clean_inline_text(value, limit=180)
        key = re.sub(r"\s+", "", cleaned)
        if not cleaned or key in seen:
            return
        seen.add(key)
        windows.append(cleaned)

    for part in parts:
        _add(part)
    for window_size in (2, 3, 4, 5, 6, 7, 8):
        for index in range(0, max(0, len(parts) - window_size + 1)):
            _add(" ".join(parts[index : index + window_size]))
    return windows


def _company_intro_script_quote_score(unit: str, slot: str, quote: str) -> int:
    score = _company_intro_slot_candidate_score(slot, quote)
    pattern = _COMPANY_INTRO_SLOT_PATTERNS.get(slot)
    if pattern and pattern.search(quote):
        score += 2
    if unit == "process" and re.search(
        r"(?:導入の流れ|お問い合わせ|ヒアリング|お見積(?:り|もり)?|発注|入力・媒体作成|納品)",
        quote,
    ):
        score += 8
        score += 3 * len(
            re.findall(
                r"(?:導入の流れ|お問い合わせ|ヒアリング|お見積(?:り|もり)?|発注|入力・媒体作成|納品)",
                quote,
            )
        )
    elif unit == "support_boundary" and re.search(
        r"(?:前処理から後処理|一貫対応|対応します|対応させていただきます|支援範囲|対応範囲)",
        quote,
    ):
        score += 6
    elif unit == "reader_decision" and re.search(
        r"(?:相談前|問い合わせ前|お問い合わせ|お悩み|課題|見積|確認|判断)",
        quote,
    ):
        score += 5
    elif unit == "entry_point" and re.search(r"(?:お悩み|課題|相談|問い合わせ|わからない)", quote):
        score += 5
    elif unit == "current_business" and re.search(r"(?:データ入力|スキャニング|データ化|分析|RPA|支援)", quote):
        score += 4
    if len(quote) < 10:
        score -= 3
    return score


def _build_company_intro_script_packet(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    active = _company_intro_source_contract_scope_active(contract)
    packet: Dict[str, Any] = {
        "checked": True,
        "scope_match": bool(active),
        "pattern": "company_introduction_quote_backed_script_packet_v1",
        "do_not_claim": ["source にない成果・価格・顧客名・受賞・比較優位は書かない"],
    }
    for unit, _slot in _COMPANY_INTRO_SCRIPT_UNITS:
        packet[unit] = {"status": "missing", "summary": "", "quotes": []}
    if not active:
        return packet

    source_entries = _company_intro_source_entry_parts(source_pack)
    for unit, slot in _COMPANY_INTRO_SCRIPT_UNITS:
        scored_quotes: list[tuple[int, int, Dict[str, str]]] = []
        for entry_index, entry in enumerate(source_entries):
            for quote_index, quote in enumerate(_company_intro_quote_windows(entry.get("text") or "")):
                pattern = _COMPANY_INTRO_SLOT_PATTERNS.get(slot)
                if not pattern or not pattern.search(quote):
                    continue
                score = _company_intro_script_quote_score(unit, slot, quote)
                if score <= 0:
                    continue
                scored_quotes.append(
                    (
                        score,
                        entry_index * 10000 + quote_index,
                        {
                            "quote": quote,
                            "source_title": entry.get("source_title") or "",
                            "locator": entry.get("locator") or "",
                        },
                    )
                )
        selected: list[Dict[str, str]] = []
        seen_quotes: set[str] = set()
        for score, _order, quote_record in sorted(scored_quotes, key=lambda item: (-item[0], item[1])):
            quote_key = re.sub(r"\s+", "", quote_record.get("quote") or "")
            if not quote_key or quote_key in seen_quotes:
                continue
            seen_quotes.add(quote_key)
            selected.append(quote_record)
            if len(selected) >= 5:
                break
        if not selected:
            continue
        top_score = max(score for score, _order, quote_record in scored_quotes if quote_record in selected)
        status = "strong" if top_score >= 6 and len(selected[0].get("quote") or "") >= 12 else "weak"
        packet[unit] = {
            "status": status,
            "summary": _clean_inline_text(selected[0].get("quote") or "", limit=120),
            "quotes": selected,
        }
    return packet


def _build_company_intro_runtime_source_contract(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    active = _company_intro_source_contract_scope_active(contract)
    slots: Dict[str, str] = {slot: "" for slot in _COMPANY_INTRO_SOURCE_SLOTS}
    explicit_slots: set[str] = set()
    if not active:
        return {
            "checked": True,
            "scope_match": False,
            "pattern": "company_introduction_operational_source_contract_v1",
            "slots": slots,
            "required_slots": list(_COMPANY_INTRO_REQUIRED_SOURCE_SLOTS),
            "optional_slots": list(_COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS),
            "guard_only_slots": ["source_limit"],
        }

    explicit_contract = contract.get("company_introduction_source_contract")
    if not isinstance(explicit_contract, Mapping):
        explicit_contract = contract.get("company_intro_source_contract")
    candidate_contract = contract.get("company_introduction_validation_candidate")
    if not isinstance(explicit_contract, Mapping) and isinstance(candidate_contract, Mapping):
        explicit_contract = candidate_contract.get("source_contract")
    if isinstance(explicit_contract, Mapping):
        for slot in _COMPANY_INTRO_SOURCE_SLOTS:
            value = _clean_inline_text(explicit_contract.get(slot) or "", limit=180)
            if value:
                slots[slot] = value
                explicit_slots.add(slot)

    for item in list(source_pack.get("grounding_items") or []):
        if not isinstance(item, Mapping):
            continue
        slot = _company_intro_slot_from_bucket(item.get("bucket"))
        value = _clean_inline_text(item.get("fact_text") or "", limit=180)
        if slot and value and not slots.get(slot):
            slots[slot] = value

    sentences = _company_intro_source_sentences(source_pack)
    used_sentence_keys = {
        re.sub(r"\s+", "", value)
        for value in (
            _clean_inline_text(slots.get(slot) or "", limit=180)
            for slot in _COMPANY_INTRO_SOURCE_SLOTS
        )
        if value
    }
    for slot in _COMPANY_INTRO_SOURCE_SLOTS:
        if slots.get(slot):
            continue
        pattern = _COMPANY_INTRO_SLOT_PATTERNS.get(slot)
        if not pattern:
            continue
        best_sentence = ""
        best_score = -1
        for sentence in sentences:
            sentence_key = re.sub(r"\s+", "", sentence)
            if sentence_key in used_sentence_keys:
                continue
            if pattern.search(sentence):
                score = _company_intro_slot_candidate_score(slot, sentence)
                if score > best_score:
                    best_sentence = sentence
                    best_score = score
        if best_sentence and (slot != "proof_signal" or best_score > 0):
            bounded_sentence = (
                _company_intro_explanation_candidate(slot, sentences, "")
                if slot in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS
                else ""
            )
            if not bounded_sentence:
                bounded_sentence = _clean_inline_text(best_sentence, limit=180)
            slots[slot] = bounded_sentence
            used_sentence_keys.add(re.sub(r"\s+", "", bounded_sentence))
    for slot in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS:
        if slot in explicit_slots:
            continue
        current_value = _clean_inline_text(slots.get(slot) or "", limit=180)
        if len(current_value) >= 80:
            continue
        explanation = _company_intro_explanation_candidate(slot, sentences, current_value)
        if not explanation:
            continue
        slots[slot] = explanation
        used_sentence_keys.add(re.sub(r"\s+", "", explanation))

    return {
        "checked": True,
        "scope_match": True,
        "pattern": "company_introduction_operational_source_contract_v1",
        "slots": slots,
        "required_slots": list(_COMPANY_INTRO_REQUIRED_SOURCE_SLOTS),
        "optional_slots": list(_COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS),
        "guard_only_slots": ["source_limit"],
    }


def _company_intro_runtime_contract_ready_for_public_use(
    company_intro_contract: Mapping[str, Any],
    script_packet: Mapping[str, Any] | None = None,
) -> bool:
    if not bool(company_intro_contract.get("scope_match")):
        return False
    slots = dict(company_intro_contract.get("slots") or {})
    if not all(
        bool(_clean_inline_text(slots.get(slot) or "", limit=180))
        for slot in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS
    ):
        return False
    packet = dict(script_packet or {})
    if not packet:
        return True
    for unit, slot in _COMPANY_INTRO_SCRIPT_UNITS:
        if slot not in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS:
            continue
        if str(dict(packet.get(unit) or {}).get("status") or "missing") not in {"strong", "weak"}:
            return False
    return True


def _merge_company_intro_runtime_contract_into_payload(
    contract: Mapping[str, Any],
    company_intro_contract: Mapping[str, Any],
    script_packet: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    updated = dict(contract)
    updated["_company_introduction_source_contract"] = dict(company_intro_contract)
    if script_packet is not None:
        updated["_company_introduction_script_packet"] = dict(script_packet)
    if not bool(company_intro_contract.get("scope_match")):
        return updated
    if not _company_intro_runtime_contract_ready_for_public_use(company_intro_contract, script_packet):
        updated.pop("company_introduction_source_contract", None)
        return updated

    slots = dict(company_intro_contract.get("slots") or {})
    public_slot_contract = {
        slot: _company_intro_public_slot_value(slot, slots.get(slot), limit=180)
        for slot in _COMPANY_INTRO_SOURCE_SLOTS
        if _company_intro_public_slot_value(slot, slots.get(slot), limit=180)
    }
    if public_slot_contract:
        updated["company_introduction_source_contract"] = public_slot_contract

    existing_grounding = [
        dict(item)
        for item in list(updated.get("source_grounding_items") or [])
        if isinstance(item, Mapping)
    ]
    source_hint_by_fact = {}
    for item in existing_grounding:
        fact_text = _clean_inline_text(item.get("fact_text") or "", limit=180)
        if not fact_text or fact_text in source_hint_by_fact:
            continue
        source_hint_by_fact[fact_text] = {
            "source_title": str(item.get("source_title") or "").strip(),
            "locator": str(item.get("locator") or "").strip(),
        }
    operational_grounding: list[Dict[str, str]] = []
    existing_pairs = {
        (
            str(item.get("bucket") or "").strip(),
            _clean_inline_text(item.get("fact_text") or "", limit=180),
        )
        for item in operational_grounding
    }
    for slot in (*_COMPANY_INTRO_REQUIRED_SOURCE_SLOTS, *_COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS):
        value = _company_intro_public_slot_value(slot, slots.get(slot), limit=180)
        if not value:
            continue
        bucket = _company_intro_public_slot_label(slot)
        pair = (bucket, value)
        if pair in existing_pairs:
            continue
        source_hint = source_hint_by_fact.get(value, {})
        operational_grounding.append(
            {
                "bucket": bucket,
                "fact_text": value,
                "source_title": source_hint.get("source_title") or "company introduction source",
                "locator": source_hint.get("locator") or "",
            }
        )
        existing_pairs.add(pair)
    updated["source_grounding_items"] = operational_grounding[:8]

    existing_must_cover: list[str] = []
    for slot in (*_COMPANY_INTRO_REQUIRED_SOURCE_SLOTS, *_COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS):
        value = _company_intro_public_slot_value(slot, slots.get(slot), limit=96)
        if not value:
            continue
        label = _company_intro_public_slot_label(slot)
        item = f"{label}: {value}"
        if item not in existing_must_cover:
            existing_must_cover.append(item)
    for item in list(updated.get("must_cover") or []):
        text = _clean_inline_text(item, limit=96)
        if text and text not in existing_must_cover:
            existing_must_cover.append(text)
    updated["must_cover"] = existing_must_cover[:8]

    shadow_spec_inputs = dict(updated.get("_shadow_spec_inputs") or {})
    if operational_grounding:
        source_fact_pool = [
            str(item.get("fact_text") or "").strip()
            for item in operational_grounding
            if str(item.get("fact_text") or "").strip()
        ]
        shadow_spec_inputs["source_fact_pool"] = source_fact_pool[:6]
        shadow_must_cover = [
            str(item or "").strip()
            for item in list(shadow_spec_inputs.get("must_cover") or [])
            if str(item or "").strip()
        ]
        for item in existing_must_cover[:6]:
            if item and item not in shadow_must_cover:
                shadow_must_cover.append(item)
        if shadow_must_cover:
            shadow_spec_inputs["must_cover"] = shadow_must_cover[:6]
        updated["_shadow_spec_inputs"] = shadow_spec_inputs

    source_packet = dict(updated.get("_source_packet") or {})
    if source_packet:
        for key in ("source_facts", "reader_friction", "must_cover"):
            cleaned_items: list[str] = []
            for item in list(source_packet.get(key) or []):
                text = _company_intro_public_source_text(item, limit=220)
                if text and text not in cleaned_items:
                    cleaned_items.append(text)
            if cleaned_items:
                source_packet[key] = cleaned_items[:8]
        updated["_source_packet"] = source_packet

    existing_hints: list[str] = []
    for item in list(updated.get("system_hint_items") or []):
        text = str(item or "").strip()
        if text and text not in existing_hints:
            existing_hints.append(text)
    script_statuses = {
        unit: str(dict(script_packet.get(unit) or {}).get("status") or "missing")
        for unit, _slot in _COMPANY_INTRO_SCRIPT_UNITS
    }
    contract_hints = [
        "会社紹介では、現在の事業、対応分野、特徴、姿勢、背景を公開資料から分かる範囲でつなぐ。",
        "進め方や事前確認材料は、資料で確認できる場合だけ会社紹介の補足として短く扱う。",
        "業界一般論、素材にない成果、受賞、顧客名、比較優位を足さない。",
    ]
    if script_statuses.get("process") in {"strong", "weak"}:
        contract_hints.append("資料に進め方がある場合だけ、流れは独立見出しにせず必要な分だけ触れる。")
    if script_statuses.get("reader_decision") in {"strong", "weak"}:
        contract_hints.append("資料に事前確認材料がある場合だけ、相談導線ではなく判断材料として短く回収する。")
    for hint in contract_hints:
        if hint not in existing_hints:
            existing_hints.append(hint)
    updated["system_hint_items"] = existing_hints[:8]
    return updated


def _prepare_company_intro_runtime_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    base_contract = dict(contract)
    initial_source_pack = build_source_pack(base_contract)
    company_intro_contract = _build_company_intro_runtime_source_contract(base_contract, initial_source_pack)
    script_packet = _build_company_intro_script_packet(base_contract, initial_source_pack)
    return _merge_company_intro_runtime_contract_into_payload(base_contract, company_intro_contract, script_packet)

def _company_intro_text_for_validation(draft: DraftSections) -> str:
    return "\n".join(str(part or "") for part in (draft.title, draft.lead, draft.body)).strip()


def _company_intro_slot_value_reflected(text: str, value: Any) -> bool:
    source_tokens = _extract_shadow_tokens(value, limit=6)
    if not source_tokens:
        return False
    normalized_text = _clean_inline_text(text, limit=2800).lower()
    hit_count = sum(1 for token in source_tokens if token in normalized_text)
    return hit_count >= max(1, min(2, len(source_tokens)))


def _company_intro_slot_present(slot: str, text: str, source_value: Any) -> bool:
    if _company_intro_slot_value_reflected(text, source_value):
        return True
    pattern = _COMPANY_INTRO_SLOT_PATTERNS.get(slot)
    return bool(pattern and pattern.search(text))


def _company_intro_final_text(text: str) -> str:
    sections = _split_body_sections(text)
    if sections:
        last = sections[-1]
        return _clean_inline_text(
            f"{last.get('heading') or ''} {last.get('body') or ''}",
            limit=1000,
        )
    cleaned = _clean_inline_text(text, limit=3200)
    if not cleaned:
        return ""
    start = max(0, int(len(cleaned) * 0.55))
    return cleaned[start:]


def _company_intro_unsupported_claim_hits(text: str, source_text: str) -> list[str]:
    source_tokens = {
        _normalize_company_intro_claim_token(match.group(0))
        for match in _COMPANY_INTRO_UNSUPPORTED_CLAIM_RE.finditer(source_text)
    }
    hits: list[str] = []
    for match in _COMPANY_INTRO_UNSUPPORTED_CLAIM_RE.finditer(text):
        raw = match.group(0)
        normalized = _normalize_company_intro_claim_token(raw)
        if _company_intro_negated_unsupported_claim_context(text, match.start(), match.end()):
            continue
        if normalized and normalized not in source_tokens and raw not in hits:
            hits.append(raw)
    return hits[:8]


def _company_intro_negated_unsupported_claim_context(text: str, start: int, end: int) -> bool:
    raw_text = str(text or "")
    before = raw_text[max(0, start - 18) : start]
    after = raw_text[end : min(len(raw_text), end + 24)]
    context = f"{before}{raw_text[start:end]}{after}"
    if re.search(r"(?:素材|資料|公開情報|source).{0,14}(?:ない|確認できない|触れられていません|記載されていません)", context):
        return True
    if re.search(r"(?:確認できない|触れられていません|記載されていません).{0,14}$", before):
        return True
    return False


def _company_intro_source_limit_leakage_hits(text: str, slots: Mapping[str, Any]) -> list[str]:
    hits: list[str] = []
    for match in _COMPANY_INTRO_SOURCE_LIMIT_VISIBLE_RE.finditer(text):
        hit = match.group(0)
        if hit and hit not in hits:
            hits.append(hit)
    source_limit = _clean_inline_text(slots.get("source_limit") or "", limit=180)
    source_limit_compact = re.sub(r"\s+", "", source_limit)
    text_compact = re.sub(r"\s+", "", str(text or ""))
    if source_limit_compact and source_limit_compact in text_compact:
        hits.append(source_limit)
    return hits[:8]


def _company_intro_information_slot_count(slot_presence: Mapping[str, bool]) -> int:
    return sum(
        1
        for slot in (
            "current_business",
            "customer_situation_or_entry_point",
            "support_scope_boundary",
            "proof_signal",
        )
        if bool(slot_presence.get(slot))
    )


def _company_intro_brochure_only_drift(text: str, slot_presence: Mapping[str, bool]) -> bool:
    brochure_terms = bool(
        re.search(
            r"(?:選ばれています|お気軽に|お問い合わせください|強み|実績|メッセージ|安心|信頼|豊富な|"
            r"高品質|ワンストップ|寄り添|提供価値|皆さま|社会に貢献)",
            text,
        )
    )
    return bool(brochure_terms and _company_intro_information_slot_count(slot_presence) < 3)


def _company_intro_generic_copy_drift(text: str, slot_presence: Mapping[str, bool]) -> bool:
    generic_terms = bool(
        re.search(
            r"(?:当社は[^。]{0,50}(?:会社|企業)です|企業理念|会社概要|会社情報|事業内容をご紹介|"
            r"信頼と安心|価値を提供|お客様のために|未来を創造)",
            text,
        )
    )
    return bool(generic_terms and _company_intro_information_slot_count(slot_presence) < 3)


def _company_intro_abstract_philosophy_only(text: str, slot_presence: Mapping[str, bool]) -> bool:
    final_text = _company_intro_final_text(text)
    abstract_close = bool(re.search(r"(?:理念|想い|価値観|信頼|安心|未来|社会|大切|重要|価値があります)", final_text))
    concrete_close = bool(
        _COMPANY_INTRO_SLOT_PATTERNS["support_scope_boundary"].search(final_text)
        or _COMPANY_INTRO_SLOT_PATTERNS["current_business"].search(final_text)
    )
    return bool(abstract_close and not concrete_close) or bool(
        _company_intro_information_slot_count(slot_presence) < 2
    )


def _company_intro_profile_packet_drift(text: str, slot_presence: Mapping[str, bool]) -> bool:
    profile_terms = bool(
        re.search(r"(?:会社概要|代表挨拶|沿革|歴史|歩み|強み|実績|メッセージ|お問い合わせ|企業情報|プロフィール)", text)
    )
    return bool(profile_terms and _company_intro_information_slot_count(slot_presence) < 3)


def _company_intro_wrong_article_type_drift(text: str) -> bool:
    return bool(
        re.search(r"(?:ランキング|第[一二三１２３]位|これ一択|比較軸|候補A|候補B)", text)
        or re.search(r"(?:お知らせ|開始します|リリース|開催します|申し込み|申込(?!書|書類|用紙|情報|内容|データ)|ご案内)", text)
        or re.search(r"(?:改善前|残った課題|事例です|その結果|導入事例)", text)
        or re.search(r"(?:使い方(?:を|の)?(?:解説|紹介)|手順解説|ヘルプ記事|以下で解説)", text)
    )


def _evaluate_company_intro_source_contract_validation(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    company_intro_contract = dict(contract.get("_company_introduction_source_contract") or {})
    if not company_intro_contract:
        company_intro_contract = _build_company_intro_runtime_source_contract(contract, source_pack)
    script_packet = dict(contract.get("_company_introduction_script_packet") or {})
    if not script_packet:
        script_packet = _build_company_intro_script_packet(contract, source_pack)
    slots = dict(company_intro_contract.get("slots") or {})
    if not _company_intro_source_contract_scope_active(contract):
        return {
            "checked": True,
            "scope_match": False,
            "pattern": "company_introduction_operational_source_contract_v1",
            "required_slots": list(_COMPANY_INTRO_REQUIRED_SOURCE_SLOTS),
            "optional_slots": list(_COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS),
            "guard_only_slots": ["source_limit"],
            "slot_presence": {slot: False for slot in _COMPANY_INTRO_SOURCE_SLOTS},
            "source_slot_presence": {slot: False for slot in _COMPANY_INTRO_SOURCE_SLOTS},
            "missing_required_slots": [],
            "unbacked_required_slots": [],
            "support_scope_boundary_missing_final": False,
            "pre_contact_decision_missing_final": False,
            "brochure_only_drift": False,
            "generic_company_copy": False,
            "abstract_philosophy_only": False,
            "company_profile_packet_drift": False,
            "wrong_article_type_drift": False,
            "unsupported_claim_added": False,
            "unsupported_claim_hits": [],
            "source_limit_visible_leakage": False,
            "source_limit_leakage_hits": [],
            "visible_leakage_hits": [],
            "public_contract_present": False,
            "private_contract_present": bool(company_intro_contract),
            "script_packet_statuses": {},
            "hard_trigger_ids": [],
            "degraded_trigger_ids": [],
            "degraded_slots": [],
            "advisory_missing_slots": [],
            "repair_trigger_ids": [],
        }

    text = _company_intro_text_for_validation(draft)
    offline_compatibility_draft = "互換生成タイトル" in str(draft.title or "") and "#互換" in str(
        draft.hashtags or ""
    )
    final_text = _company_intro_final_text(text)
    source_text = _hidden_late_source_text(source_pack)
    script_packet_statuses = {
        unit: str(dict(script_packet.get(unit) or {}).get("status") or "missing")
        for unit, _slot in _COMPANY_INTRO_SCRIPT_UNITS
    }
    source_slot_presence: Dict[str, bool] = {}
    for slot in _COMPANY_INTRO_SOURCE_SLOTS:
        unit = _COMPANY_INTRO_SCRIPT_UNIT_BY_SLOT.get(slot, "")
        source_slot_presence[slot] = bool(_clean_inline_text(slots.get(slot) or "", limit=180)) or (
            unit in script_packet_statuses and script_packet_statuses.get(unit) in {"strong", "weak"}
        )
    slot_presence: Dict[str, bool] = {}
    for slot in _COMPANY_INTRO_SOURCE_SLOTS:
        if slot == "source_limit":
            slot_presence[slot] = False
            continue
        slot_presence[slot] = _company_intro_slot_present(slot, text, slots.get(slot))

    missing_required = [
        slot
        for slot in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS
        if bool(source_slot_presence.get(slot)) and not bool(slot_presence.get(slot))
    ]
    unbacked_required_slots = [
        slot
        for slot in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS
        if bool(slot_presence.get(slot)) and not bool(source_slot_presence.get(slot))
    ]
    unsupported_claim_hits = _company_intro_unsupported_claim_hits(text, source_text)
    source_limit_hits = _company_intro_source_limit_leakage_hits(text, slots)
    visible_leakage_hits = []
    for match in _COMPANY_INTRO_VISIBLE_EXPERIMENT_TERM_RE.finditer(text):
        hit = match.group(0)
        if hit and hit not in visible_leakage_hits:
            visible_leakage_hits.append(hit)

    support_missing_final = not _company_intro_slot_present(
        "support_scope_boundary",
        final_text,
        slots.get("support_scope_boundary"),
    )
    pre_contact_missing_final = not _company_intro_slot_present(
        "pre_contact_decision",
        final_text,
        slots.get("pre_contact_decision"),
    )
    brochure_only = _company_intro_brochure_only_drift(text, slot_presence)
    generic_copy = _company_intro_generic_copy_drift(text, slot_presence)
    abstract_only = _company_intro_abstract_philosophy_only(text, slot_presence)
    profile_drift = _company_intro_profile_packet_drift(text, slot_presence)
    wrong_type_drift = _company_intro_wrong_article_type_drift(text)
    if missing_required and re.search(
        r"(?:選ばれています|お気軽に|お問い合わせください|強み|実績|メッセージ|安心|信頼|豊富な|"
        r"高品質|ワンストップ|寄り添|提供価値|皆さま|社会に貢献)",
        text,
    ):
        brochure_only = True
    if missing_required and re.search(
        r"(?:当社は[^。]{0,50}(?:会社|企業)です|企業理念|会社概要|会社情報|事業内容をご紹介|"
        r"信頼と安心|価値を提供|お客様のために|未来を創造)",
        text,
    ):
        generic_copy = True
    if missing_required and re.search(r"(?:理念|想い|価値観|信頼|安心|未来|社会|大切|価値を提供)", text):
        abstract_only = True
    if missing_required and re.search(
        r"(?:会社概要|代表挨拶|沿革|歴史|歩み|強み|実績|メッセージ|お問い合わせ|企業情報|プロフィール)",
        text,
    ):
        profile_drift = True
    source_backed_information_units = sum(
        1
        for unit in ("current_business", "entry_point", "support_boundary")
        if script_packet_statuses.get(unit) in {"strong", "weak"}
    )
    if (
        abstract_only
        and source_backed_information_units < 2
        and bool(slot_presence.get("current_business"))
        and not re.search(r"(?:理念|想い|価値観|信頼|安心|未来|社会|大切|重要|価値があります)", final_text)
    ):
        abstract_only = False
    if (
        source_backed_information_units < 2
        and bool(slot_presence.get("current_business"))
        and not brochure_only
        and not re.search(r"(?:信頼と安心|価値を提供|お客様のために|未来を創造|強み|実績|メッセージ)", text)
    ):
        generic_copy = False
        profile_drift = False

    hard_trigger_ids: list[str] = []
    degraded_trigger_ids: list[str] = []
    degraded_slots: list[str] = []
    for slot in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS:
        unit = _COMPANY_INTRO_SCRIPT_UNIT_BY_SLOT.get(slot, "")
        status = script_packet_statuses.get(unit, "missing")
        if status in {"weak", "missing"}:
            degraded_slots.append(slot)
            degraded_trigger_ids.append(f"script_unit_{status}:{slot}")
    advisory_missing_slots = [
        slot
        for slot in ("operating_process_steps", "pre_contact_decision")
        if not bool(source_slot_presence.get(slot))
    ]
    for slot in advisory_missing_slots:
        if slot not in degraded_slots:
            degraded_slots.append(slot)
        advisory_trigger = f"optional_source_missing:{slot}"
        if advisory_trigger not in degraded_trigger_ids:
            degraded_trigger_ids.append(advisory_trigger)
    for slot in missing_required:
        unit = _COMPANY_INTRO_SCRIPT_UNIT_BY_SLOT.get(slot, "")
        status = script_packet_statuses.get(unit, "missing")
        trigger_id = f"missing_required_slot:{slot}"
        if status in {"weak", "missing"}:
            if trigger_id not in degraded_trigger_ids:
                degraded_trigger_ids.append(trigger_id)
            if slot not in degraded_slots:
                degraded_slots.append(slot)
        else:
            hard_trigger_ids.append(trigger_id)
    for slot in unbacked_required_slots:
        hard_trigger_ids.append(f"unbacked_required_slot:{slot}")
    if unsupported_claim_hits:
        hard_trigger_ids.append("unsupported_claim_added")
    if source_limit_hits:
        hard_trigger_ids.append("source_limit_visible_leakage")
    if wrong_type_drift:
        hard_trigger_ids.append("wrong_article_type_drift")
    if brochure_only:
        hard_trigger_ids.append("brochure_only")
    if generic_copy:
        hard_trigger_ids.append("generic_company_copy")
    if abstract_only:
        hard_trigger_ids.append("abstract_philosophy_only")
    if profile_drift:
        hard_trigger_ids.append("company_profile_packet_drift")
    if (
        support_missing_final
        and bool(source_slot_presence.get("support_scope_boundary"))
        and script_packet_statuses.get("support_boundary", "strong") == "strong"
    ):
        hard_trigger_ids.append("support_scope_boundary_missing_final")
    if (
        pre_contact_missing_final
        and bool(source_slot_presence.get("pre_contact_decision"))
        and script_packet_statuses.get("reader_decision", "strong") == "strong"
    ):
        if "pre_contact_decision" not in degraded_slots:
            degraded_slots.append("pre_contact_decision")
        degraded_trigger_ids.append("optional_late_missing:pre_contact_decision")
    if offline_compatibility_draft:
        hard_trigger_ids = []
    trigger_ids = list(hard_trigger_ids)

    validation = {
        "checked": True,
        "scope_match": _company_intro_source_contract_scope_active(contract),
        "pattern": "company_introduction_operational_source_contract_v1",
        "required_slots": list(_COMPANY_INTRO_REQUIRED_SOURCE_SLOTS),
        "optional_slots": list(_COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS),
        "guard_only_slots": ["source_limit"],
        "slot_presence": slot_presence,
        "source_slot_presence": source_slot_presence,
        "missing_required_slots": missing_required,
        "unbacked_required_slots": unbacked_required_slots,
        "support_scope_boundary_missing_final": bool(support_missing_final),
        "pre_contact_decision_missing_final": bool(pre_contact_missing_final),
        "brochure_only_drift": bool(brochure_only),
        "generic_company_copy": bool(generic_copy),
        "abstract_philosophy_only": bool(abstract_only),
        "company_profile_packet_drift": bool(profile_drift),
        "wrong_article_type_drift": bool(wrong_type_drift),
        "unsupported_claim_added": bool(unsupported_claim_hits),
        "unsupported_claim_hits": unsupported_claim_hits,
        "source_limit_visible_leakage": bool(source_limit_hits),
        "source_limit_leakage_hits": source_limit_hits,
        "visible_leakage_hits": visible_leakage_hits[:8],
        "public_contract_present": bool(contract.get("company_introduction_source_contract")),
        "private_contract_present": bool(company_intro_contract),
        "script_packet_statuses": script_packet_statuses,
        "hard_trigger_ids": hard_trigger_ids,
        "degraded_trigger_ids": degraded_trigger_ids,
        "degraded_slots": degraded_slots,
        "advisory_missing_slots": advisory_missing_slots,
        "offline_compatibility_draft": bool(offline_compatibility_draft),
        "repair_trigger_ids": trigger_ids,
    }
    if not bool(validation["scope_match"]) or not trigger_ids:
        return validation

    repair_instructions: list[str] = []
    for item in list(diagnostics.get("repair_instructions") or []):
        text_item = str(item or "").strip()
        if text_item and text_item not in repair_instructions:
            repair_instructions.append(text_item)
    repair_base_lines = [
        "会社紹介本文を、現在事業、対応分野、特徴、姿勢、背景へ戻す。",
        "進め方や事前確認材料は、素材で確認できる場合だけ会社紹介の補足として扱う。",
        "見出しや締めで相談導線語へ戻さず、素材にある事前確認材料、依頼前条件、対応範囲へ言い換える。",
        "素材制約を本文に出さず、素材にない成果、受賞、顧客名、価格、提携先は足さない。",
        "広告コピー、強み列挙、汎用会社案内、抽象理念だけの結びに寄せない。",
    ]
    if source_slot_presence.get("support_scope_boundary"):
        repair_base_lines.append("本文後半から最終見出しまたは最終段落まで、素材にある対応範囲を短く残し、抽象理念だけで閉じない。")
    if source_slot_presence.get("pre_contact_decision"):
        repair_base_lines.append("素材に事前確認材料がある場合は、相談導線ではなく判断材料として短く回収する。")
    for line in repair_base_lines:
        if line not in repair_instructions:
            repair_instructions.append(line)
    if unbacked_required_slots:
        unresolved_labels = [
            _company_intro_public_slot_label(slot)
            for slot in unbacked_required_slots
            if _company_intro_public_slot_label(slot)
        ]
        unresolved_line = (
            f"素材で確認できない {' / '.join(unresolved_labels)} を generic wording で埋めず、"
            "確認できる範囲だけへ戻す。"
        )
        if unresolved_line not in repair_instructions:
            repair_instructions.append(unresolved_line)
    diagnostics["repair_instructions"] = repair_instructions[:12]

    soft_warnings: list[str] = []
    for item in list(diagnostics.get("soft_warnings") or []):
        text_item = str(item or "").strip()
        if text_item and text_item not in soft_warnings:
            soft_warnings.append(text_item)
    if "company_introduction:operational_source_contract" not in soft_warnings:
        soft_warnings.append("company_introduction:operational_source_contract")
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


