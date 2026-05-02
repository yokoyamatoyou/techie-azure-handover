"""Plain-data helpers for current mainline result projection inside the UI shell."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

_REVIEW_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "構成": ["見出し", "段落が長く", "論点が混在", "構成"],
    "文体": ["文体", "語調", "一人称", "文末", "表現"],
    "根拠": ["根拠", "出典", "証拠", "事実", "データ", "情報源"],
}
_QUALITY_WARNING_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "key": "ending",
        "headline": "文末の型が続いています",
        "detail": "同じ言い切り方が続きやすく、読み味が平坦に見える状態です。",
        "matches": (
            "ending:",
            "fingerprint:sentence_ending_entropy_low",
            "fingerprint:ending_repetition",
        ),
    },
    {
        "key": "structure",
        "headline": "段落と節の役割差が弱めです",
        "detail": "文の長さや節の運びがそろい、見出しごとのメリハリが見えにくくなっています。",
        "matches": (
            "ai:paragraph_variation",
            "ai:sentence_variation",
            "shadow:section_drift",
            "omission:heading_reanchor",
            "fingerprint:sentence_length_cv_flat",
            "fingerprint:syntactic_complexity_low",
        ),
    },
    {
        "key": "vocabulary",
        "headline": "語彙が寄りすぎています",
        "detail": "同じ語や抽象表現が続き、説明カード調に寄って見える可能性があります。",
        "matches": (
            "fingerprint:vocab_repetition",
            "fingerprint:nominalization_rate_high",
            "fingerprint:bigram_mono_low",
        ),
    },
    {
        "key": "sentence_load",
        "headline": "一文が詰まり気味です",
        "detail": "読点の多さや情報量の詰め込みで、息継ぎしにくい箇所があります。",
        "matches": (
            "fingerprint:comma_overuse",
        ),
    },
)
_COMPANY_INTRODUCTION_FAIL_CLOSED_DETAILS: frozenset[str] = frozenset(
    {
        "Company introduction naturalness rescue remained unresolved after repair",
        "Company introduction source contract remained unresolved after repair",
    }
)
_COMPANY_INTRODUCTION_FAIL_CLOSED_STATUS_TEXT = (
    "会社紹介に必要な情報がソースから十分に読み取れませんでした。"
    "事業内容・支援範囲・進め方が分かるURLや資料を追加して、もう一度お試しください。"
)
_COMPANY_INTRODUCTION_FAIL_CLOSED_NOTIFY_TEXT = (
    "会社紹介に必要な情報が不足しています。URLや資料を追加して再実行してください。"
)


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _format_missing_required_input_message(missing_fields: List[str]) -> str:
    label_map = {
        "speaker_profile": "誰視点",
        "audience_profile": "誰向け",
        "tone_profile": "語り口",
        "core_message": "核メッセージ",
        "comparison_axes": "比較軸",
    }
    labels = [label_map.get(field, field) for field in missing_fields]
    return f"{'・'.join(labels)}を入力してください。"


def is_transient_exception(exc: Exception) -> bool:
    text = str(exc or "").upper()
    if text.startswith("TRN_"):
        return True
    transient_markers = (
        "RATE LIMIT",
        "RATE_LIMIT",
        "TIMEOUT",
        "TIMED OUT",
        "429",
        "503",
        "UPSTREAM",
        "NETWORK RESET",
        "CONNECTION RESET",
    )
    return any(marker in text for marker in transient_markers)


def classify_generation_exception(exc: Exception) -> Dict[str, Any]:
    message = str(exc or "")
    normalized = message.strip().upper()
    reason_code = "SYS_GENERATION_FAILURE"
    error_class = "system"
    retryable = False
    if normalized.startswith(("INP_", "POL_", "SYS_", "TRN_")):
        reason_code = normalized.split(":", 1)[0]
        prefix = reason_code.split("_", 1)[0]
        error_class = {
            "INP": "user_input",
            "POL": "policy",
            "SYS": "system",
            "TRN": "transient",
        }.get(prefix, "system")
        retryable = error_class == "transient"
    elif is_transient_exception(exc):
        if "429" in normalized or "RATE_LIMIT" in normalized or "RATE LIMIT" in normalized:
            reason_code = "TRN_RATE_LIMIT"
        elif "TIMEOUT" in normalized or "TIMED OUT" in normalized:
            reason_code = "TRN_TIMEOUT"
        elif "NETWORK RESET" in normalized or "CONNECTION RESET" in normalized:
            reason_code = "TRN_NETWORK_RESET"
        elif "503" in normalized or "UPSTREAM" in normalized:
            reason_code = "TRN_UPSTREAM_5XX"
        else:
            reason_code = "TRN_RETRYABLE_FAILURE"
        error_class = "transient"
        retryable = True
    return {
        "error_class": error_class,
        "reason_code": reason_code,
        "retryable": retryable,
        "message": message,
    }


def build_current_mainline_user_input_feedback(
    *,
    reason_code: str,
    needs_input_items: Any = None,
) -> Tuple[str, str, str]:
    normalized_reason = str(reason_code or "INP_MISSING_REQUIRED")
    items = [_to_plain_dict(item) for item in _to_plain_list(needs_input_items)[:3]]
    if normalized_reason == "INP_NON_GENERATION_REQUEST":
        return (
            "記事にしたい内容がまだ見えていません。生成したいテーマや要点を入れると進めます。",
            (
                "- 記事化したい内容がまだ不足しています。\n"
                f"- reason_code: {normalized_reason}\n"
                "- 対処: モデル名やアルゴリズム説明ではなく、生成したい記事内容を入力してください。"
            ),
            "生成したい記事内容を入力してください。",
        )
    if normalized_reason == "INP_NEEDS_CLARIFICATION" and items:
        lines = [
            "- 内容を整えるため、先に確認したい点があります。",
            f"- reason_code: {normalized_reason}",
            "- 確認したい点:",
        ]
        for item in items:
            field = str(item.get("field", "") or "")
            template = str(item.get("question_template", "") or "")
            required_format = str(item.get("required_format", "") or "")
            example_answer = str(item.get("example_answer", "") or "")
            if template:
                label = f"{field}: " if field else ""
                lines.append(f"- {label}{template}")
            if required_format:
                lines.append(f"- 回答形式: {required_format}")
            if example_answer:
                lines.append(f"- 例: {example_answer}")
        return (
            "確認したい点に答えると、生成に進めます。",
            "\n".join(lines),
            "確認したい点に回答してください。",
        )

    if items:
        lines = [
            "- 先に補いたい入力があります。",
            f"- reason_code: {normalized_reason}",
            "- 必要な追加入力:",
        ]
        for item in items:
            field = str(item.get("field", "") or "")
            template = str(item.get("question_template", "") or "")
            if field and template:
                lines.append(f"- {field}: {template}")
            elif template:
                lines.append(f"- {template}")
        return (
            "入力を補うと生成に進めます。必要項目を入れてからもう一度お試しください。",
            "\n".join(lines),
            "先に必要項目を入力してください。",
        )

    return (
        "入力を補うと生成に進めます。必要項目を入れてからもう一度お試しください。",
        (
            "- 先に補いたい入力があります。\n"
            f"- reason_code: {normalized_reason}\n"
            "- 話者（誰が語るか）と読者（誰向けか）を指定してください。"
        ),
        "先に必要項目を入力してください。",
    )


def _is_company_introduction_fail_closed_detail(error_message: str) -> bool:
    return str(error_message or "").strip() in _COMPANY_INTRODUCTION_FAIL_CLOSED_DETAILS


def build_current_mainline_generation_error_view(
    *,
    reason_code: str,
    error_class: str,
    error_message: str = "",
    needs_input_items: Any = None,
) -> Dict[str, Any]:
    normalized_reason_code = str(reason_code or "SYS_PIPELINE_FAILURE")
    normalized_error_class = str(error_class or "system")
    normalized_error_message = str(error_message or "").strip()
    normalized_items = [_to_plain_dict(item) for item in _to_plain_list(needs_input_items)]
    if normalized_error_class == "user_input":
        status_text, source_error_content, notify_text = build_current_mainline_user_input_feedback(
            reason_code=normalized_reason_code,
            needs_input_items=normalized_items,
        )
        return {
            "status_text": status_text,
            "source_error_content": source_error_content,
            "notify_text": notify_text,
            "notify_color": "warning",
            "outcome": "needs_input_generation",
        }
    if _is_company_introduction_fail_closed_detail(normalized_error_message):
        return {
            "status_text": _COMPANY_INTRODUCTION_FAIL_CLOSED_STATUS_TEXT,
            "source_error_content": (
                "- 会社紹介に必要な情報がソースから十分に読み取れませんでした。\n"
                f"- error_class: {normalized_error_class}\n"
                f"- reason_code: {normalized_reason_code}\n"
                "- 対処: 事業内容・支援範囲・進め方が分かるURLや資料を追加して、もう一度お試しください。"
            ),
            "notify_text": _COMPANY_INTRODUCTION_FAIL_CLOSED_NOTIFY_TEXT,
            "notify_color": "negative",
            "outcome": f"fail_closed_{normalized_error_class}",
        }
    detail_line = (
        f"\n- detail: {normalized_error_message}"
        if normalized_error_message and normalized_error_message != normalized_reason_code
        else ""
    )
    return {
        "status_text": "生成を安全に止めました。入力や設定を確認してから、あらためてお試しください。",
        "source_error_content": (
            "- 生成処理を安全停止しました。\n"
            f"- error_class: {normalized_error_class}\n"
            f"- reason_code: {normalized_reason_code}"
            f"{detail_line}"
        ),
        "notify_text": "生成を安全に止めました。入力や設定を確認してから再実行してください。",
        "notify_color": "negative",
        "outcome": f"fail_closed_{normalized_error_class}",
    }


def build_current_mainline_guard_retry_exception_view(
    *,
    reason_code: str,
    error_class: str,
) -> Dict[str, Any]:
    normalized_reason_code = str(reason_code or "SYS_GENERATION_FAILURE")
    normalized_error_class = str(error_class or "system")
    return {
        "status_text": "品質を整える途中で止まりました。入力を見直してから、もう一度お試しください。",
        "source_error_content": (
            "- 品質補修リトライ中に生成が停止しました。\n"
            f"- error_class: {normalized_error_class}\n"
            f"- reason_code: {normalized_reason_code}\n"
            "- 対処: 入力を見直して再実行してください。"
        ),
        "notify_text": "品質を整える途中で止まりました。入力を見直してから再実行してください。",
        "notify_color": "negative",
        "outcome": "fail_closed_guard_retry_exception",
    }


def build_current_mainline_generation_busy_view() -> Dict[str, Any]:
    return {
        "event_name": "generation_rejected_busy",
        "reason_code": "UI_BUSY",
        "error_class": "ui",
        "status_text": "記事生成中のため実行できません。",
        "notify_text": "",
        "notify_color": "",
        "extra": {},
    }


def build_current_mainline_generation_no_sources_view() -> Dict[str, Any]:
    return {
        "event_name": "generation_rejected_no_sources",
        "reason_code": "INP_MISSING_REQUIRED",
        "error_class": "user_input",
        "status_text": "記事の材料がまだありません。URL追加かファイルアップロードで進めます。",
        "notify_text": "先にURLを追加するか、ファイルをアップロードしてください。",
        "notify_color": "negative",
        "extra": {},
    }


def build_current_mainline_invalid_article_type_view(
    *,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "event_name": "generation_rejected_invalid_article_type",
        "reason_code": "INP_INVALID_ARTICLE_TYPE",
        "error_class": "user_input",
        "status_text": "記事タイプを選び直すと進めます。",
        "notify_text": "選択した記事タイプを確認して、もう一度選んでください。",
        "notify_color": "negative",
        "extra": _to_plain_dict(extra),
    }


def build_current_mainline_confirmation_required_view(
    *,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "event_name": "generation_rejected_confirmation_required",
        "reason_code": "INP_MISSING_REQUIRED",
        "error_class": "user_input",
        "status_text": "まだ内容を確認していません。STEP4で「内容を確認」を押してから、「この内容で生成を開始」を押してください。",
        "notify_text": "先に内容を確認してください。確認だけでは生成は始まりません。",
        "notify_color": "warning",
        "extra": _to_plain_dict(extra),
    }


def build_current_mainline_ambiguity_confirmation_view(
    *,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "event_name": "generation_paused_ambiguity_confirmation",
        "reason_code": "INP_AMBIGUITY_CONFIRMATION_REQUIRED",
        "error_class": "user_input",
        "status_text": "曖昧語の意味確認が必要です",
        "notify_text": "",
        "notify_color": "",
        "extra": _to_plain_dict(extra),
    }


def build_current_mainline_missing_required_inputs_view(
    *,
    missing_fields: List[str],
) -> Dict[str, Any]:
    return {
        "event_name": "generation_rejected_missing_required_inputs",
        "reason_code": "INP_MISSING_REQUIRED",
        "error_class": "user_input",
        "status_text": "先に必須入力をそろえると、記事生成に進めます。",
        "notify_text": _format_missing_required_input_message(missing_fields),
        "notify_color": "warning",
        "extra": {"missing_fields": ",".join(missing_fields)},
    }


def build_current_mainline_fetch_failure_view(
    *,
    details: str,
    blocked_urls: List[str],
    failure_count: int,
) -> Dict[str, Any]:
    source_error_content = str(details or "").strip()
    if source_error_content:
        source_error_content += "\n\n"
    source_error_content += "reason_code: INP_SOURCE_FETCH_FAILED"
    return {
        "pdf_assist_status": (
            "403のため直接取得できないURLがあります。下の『半自動PDF取り込み』から続けてください。"
            if blocked_urls
            else "読み込めなかった資料があります。URLやファイルを見直すと再開できます。"
        ),
        "status_text": "一部の資料を読み込めませんでした。開けるURLかPDF取り込みに切り替えると進めます。",
        "source_error_content": source_error_content,
        "outcome": "needs_input_fetch_failures",
        "notify_text": "読み込めない資料があります。修正後にもう一度お試しください。",
        "notify_color": "warning",
        "event_name": "generation_blocked_fetch_failures",
        "reason_code": "INP_SOURCE_FETCH_FAILED",
        "error_class": "user_input",
        "event_extra": {
            "failure_count": int(failure_count),
            "blocked_403_count": len(blocked_urls),
        },
    }


def build_current_mainline_no_valid_sources_view() -> Dict[str, Any]:
    return {
        "pdf_assist_status": "使える資料がまだ見つかっていません。",
        "status_text": "使える資料をまだ取得できていません。URLやファイルを見直すと進めます。",
        "source_error_content": (
            "- 有効なソースがありません\n"
            "  対処: URL/ファイルを見直して再試行してください。\n"
            "reason_code: INP_MISSING_REQUIRED"
        ),
        "outcome": "needs_input_no_contents",
        "notify_text": "入力ソースが不足しています。URL/ファイルを追加してください。",
        "notify_color": "warning",
        "event_name": "generation_blocked_no_valid_sources",
        "reason_code": "INP_MISSING_REQUIRED",
        "error_class": "user_input",
        "event_extra": {},
    }


def attach_prompt_context_to_result(
    result: Dict[str, Any],
    *,
    prompt_raw: str,
    system_hint_items: Optional[List[str]],
    retry_memo: Optional[List[str]],
    strict_saas_mode: str,
    question_generation_owner: str = "",
    default_strict_saas_mode: str = "medium",
) -> Dict[str, Any]:
    enriched = dict(result or {})
    normalized_prompt_raw = str(prompt_raw or "").strip()
    normalized_system_hint_items = [
        str(item).strip() for item in (system_hint_items or []) if str(item or "").strip()
    ]
    normalized_retry_memo = [
        str(item).strip() for item in (retry_memo or []) if str(item or "").strip()
    ]
    normalized_strict_saas_mode = str(strict_saas_mode or default_strict_saas_mode)
    normalized_question_generation_owner = str(question_generation_owner or "").strip()

    enriched["user_prompt"] = normalized_prompt_raw
    enriched["prompt_raw"] = normalized_prompt_raw
    enriched["system_hint_items"] = normalized_system_hint_items
    enriched["retry_memo"] = normalized_retry_memo
    enriched["strict_saas_mode"] = normalized_strict_saas_mode
    enriched["question_generation_owner"] = normalized_question_generation_owner

    pipeline_check = _to_plain_dict(enriched.get("pipeline_check"))
    input_contract = _to_plain_dict(pipeline_check.get("input_contract"))
    if input_contract:
        input_contract["prompt_raw"] = normalized_prompt_raw
        input_contract["topic"] = normalized_prompt_raw
        input_contract["system_hint_items"] = normalized_system_hint_items
        input_contract["retry_memo"] = normalized_retry_memo
        input_contract["strict_saas_mode"] = normalized_strict_saas_mode
        input_contract["question_generation_owner"] = normalized_question_generation_owner
        pipeline_check["input_contract"] = input_contract
        enriched["pipeline_check"] = pipeline_check
    return enriched


def hashtags_to_plain(hashtags: str, limit: int = 5) -> str:
    source = (hashtags or "").strip()
    if not source:
        return ""

    tags = re.findall(r"#\S+", source)
    cleaned: List[str] = []
    if tags:
        for tag in tags:
            tag_body = tag.lstrip("#")
            tag_body = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+", "", tag_body)
            if tag_body:
                cleaned.append(tag_body)
    else:
        for token in re.split(r"\s+", source):
            token = token.strip().lstrip("#")
            if not token:
                continue
            token = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+", "", token)
            if token:
                cleaned.append(token)

    if limit and cleaned:
        cleaned = cleaned[:limit]
    return " ".join(cleaned)


def replace_hashtags_for_preview(full_text: str, hashtags_plain: str) -> str:
    if not full_text:
        return ""
    if not hashtags_plain:
        return full_text

    marker = "\n---\n\n"
    if marker in full_text:
        head, _ = full_text.rsplit(marker, 1)
        return f"{head}{marker}{hashtags_plain}"
    return full_text


def build_short_sns_text(text: str, target_chars: int = 320) -> str:
    source = (text or "").strip()
    if not source:
        return ""
    if len(source) <= target_chars:
        return source

    trimmed = source[:target_chars].rstrip()
    cut = max(trimmed.rfind("。"), trimmed.rfind("！"), trimmed.rfind("？"), trimmed.rfind("\n"))
    if cut >= int(target_chars * 0.55):
        trimmed = trimmed[: cut + 1].rstrip()
    if not trimmed.endswith("..."):
        trimmed += "..."
    return trimmed


def _classify_review_point(point: str) -> str:
    for category, keywords in _REVIEW_CATEGORY_KEYWORDS.items():
        if any(keyword in point for keyword in keywords):
            return category
    return "構成"


def _build_review_sections(review_points: Any) -> Dict[str, str]:
    categorized: dict[str, list[str]] = {"構成": [], "文体": [], "根拠": []}
    for item in _to_plain_list(review_points):
        text = str(item or "").strip()
        if not text:
            continue
        category = _classify_review_point(text)
        categorized.setdefault(category, []).append(text)
    return {
        "構成": " / ".join(categorized.get("構成", [])),
        "文体": " / ".join(categorized.get("文体", [])),
        "根拠": " / ".join(categorized.get("根拠", [])),
    }


def _collect_quality_warning_codes(result: Dict[str, Any]) -> List[str]:
    projected_result = _to_plain_dict(result)
    warning_codes: List[str] = []
    for item in _to_plain_list(projected_result.get("ui_quality_warnings")):
        code = str(item or "").strip()
        if code and code not in warning_codes:
            warning_codes.append(code)
    pipeline_check = _to_plain_dict(projected_result.get("pipeline_check"))
    output_guard = _to_plain_dict(pipeline_check.get("output_guard"))
    final_quality_eval = _to_plain_dict(pipeline_check.get("final_quality_eval"))
    for source in (output_guard.get("soft_warnings"), final_quality_eval.get("soft_warnings")):
        for item in _to_plain_list(source):
            code = str(item or "").strip()
            if code and code not in warning_codes:
                warning_codes.append(code)
    return warning_codes


def _build_quality_warning_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    warning_codes = _collect_quality_warning_codes(result)
    if not warning_codes:
        return {
            "visible": False,
            "title": "",
            "badge_text": "",
            "rows": [],
            "note": "",
            "warning_codes": [],
        }

    rows: List[Dict[str, str]] = []
    matched_codes: set[str] = set()
    for group in _QUALITY_WARNING_GROUPS:
        group_codes = [
            code
            for code in warning_codes
            if any(code.startswith(prefix) or code == prefix for prefix in tuple(group.get("matches") or ()))
        ]
        if not group_codes:
            continue
        matched_codes.update(group_codes)
        rows.append(
            {
                "headline": str(group.get("headline") or ""),
                "detail": str(group.get("detail") or ""),
                "codes": "",
            }
        )

    unmatched_codes = [code for code in warning_codes if code not in matched_codes]
    for code in unmatched_codes[:2]:
        rows.append(
            {
                "headline": "ほかにも確認したい点があります",
                "detail": "機械的な癖が残っていないか、本文全体を軽く見直してください。",
                "codes": "",
            }
        )

    return {
        "visible": True,
        "title": "記事完成へのアドバイス",
        "badge_text": f"確認ポイント {len(warning_codes)}件",
        "rows": rows[:4],
        "note": "上から順に見ると、読みやすさを整えやすくなります。",
        "warning_codes": warning_codes,
    }


def build_current_mainline_success_view(
    result: Dict[str, Any],
    *,
    quality_warning_only: bool,
    guard_retry_count: int = 0,
    hashtag_limit: int = 5,
    short_sns_target_chars: int = 320,
) -> Dict[str, Any]:
    projected_result = dict(result or {})
    if guard_retry_count > 0:
        projected_result["ui_guard_retry_count"] = int(guard_retry_count)
    if quality_warning_only:
        projected_result["ui_quality_warning_only"] = True
        projected_result["output_guard_warning_only"] = True

    title = str(projected_result.get("title", "") or "")
    lead = str(projected_result.get("lead", "") or "")
    body = str(projected_result.get("body", "") or "")
    references = str(projected_result.get("references", "") or "")
    full_text = str(projected_result.get("full_text", "") or "")
    full_body = str(projected_result.get("full_body", "") or "")
    hashtags_plain = hashtags_to_plain(str(projected_result.get("hashtags", "") or ""), limit=hashtag_limit)
    if full_body:
        note_body_text = full_body
    else:
        note_body_text = "\n\n".join(part for part in (lead, body, references) if part)
    linkedin_text = str(projected_result.get("linkedin_text", "") or "")
    linkedin_short_text = build_short_sns_text(
        linkedin_text,
        target_chars=short_sns_target_chars,
    )
    preview_text = replace_hashtags_for_preview(full_text, hashtags_plain)
    review_sections = _build_review_sections(projected_result.get("review_points"))
    quality_warning_summary = _build_quality_warning_summary(projected_result)
    review_rows = {
        section: {
            "text": str(text or ""),
            "visible": bool(text),
        }
        for section, text in review_sections.items()
    }
    review_visible = any(bool(value) for value in review_sections.values())
    note_body_chars = len(note_body_text)
    linkedin_chars = len(linkedin_text)
    status_text = (
        "生成が完了しました。記事完成へのアドバイスがあります。"
        if quality_warning_only
        else "生成が完了しました。"
    )
    notify_text = (
        "生成が完了しました。記事完成へのアドバイスがあります。"
        if quality_warning_only
        else "生成が完了しました"
    )
    notify_color = "warning" if quality_warning_only else "positive"
    outcome = "success_quality_warning" if quality_warning_only else "success"
    stats_text = f"記事本文: {note_body_chars}文字 / LinkedIn: {linkedin_chars}文字"
    render_fields = {
        "title": title,
        "lead": lead,
        "body": body,
        "references": references,
        "full_text": full_text,
        "hashtags_plain": hashtags_plain,
        "note_body_text": note_body_text,
        "preview_text": preview_text,
        "linkedin_text": linkedin_text,
        "linkedin_short_text": linkedin_short_text,
    }
    completion_view = {
        "review_sections": review_sections,
        "review_rows": review_rows,
        "review_visible": review_visible,
        "quality_warning_summary": quality_warning_summary,
        "status_text": status_text,
        "notify_text": notify_text,
        "notify_color": notify_color,
        "outcome": outcome,
        "stats_text": stats_text,
        "note_body_chars": note_body_chars,
        "linkedin_chars": linkedin_chars,
    }

    return {
        "result": projected_result,
        "render_fields": render_fields,
        "completion_view": completion_view,
        "title": title,
        "lead": lead,
        "body": body,
        "references": references,
        "full_text": full_text,
        "hashtags_plain": hashtags_plain,
        "note_body_text": note_body_text,
        "preview_text": preview_text,
        "linkedin_text": linkedin_text,
        "linkedin_short_text": linkedin_short_text,
        "review_sections": review_sections,
        "review_visible": review_visible,
        "quality_warning_summary": quality_warning_summary,
        "status_text": status_text,
        "notify_text": notify_text,
        "notify_color": notify_color,
        "render_status_text": "生成結果をUIに反映しました。",
        "render_event_extra": {"quality_warning_only": bool(quality_warning_only)},
        "outcome": outcome,
        "stats_text": stats_text,
        "note_body_chars": note_body_chars,
        "linkedin_chars": linkedin_chars,
    }


def build_current_mainline_completion_payload(
    *,
    success_view: Dict[str, Any],
    completion_view: Dict[str, Any],
    note_body_text: str,
    linkedin_text: str,
    quality_warning_only: bool,
    elapsed_ms: int,
) -> Dict[str, Any]:
    normalized_success_view = _to_plain_dict(success_view)
    normalized_completion_view = _to_plain_dict(completion_view)
    note_body_chars = int(
        normalized_completion_view.get("note_body_chars")
        or normalized_success_view.get("note_body_chars")
        or len(str(note_body_text or ""))
    )
    linkedin_chars = int(
        normalized_completion_view.get("linkedin_chars")
        or normalized_success_view.get("linkedin_chars")
        or len(str(linkedin_text or ""))
    )
    stats_text = str(
        normalized_completion_view.get("stats_text")
        or normalized_success_view.get("stats_text")
        or f"記事本文: {note_body_chars}文字 / LinkedIn: {linkedin_chars}文字"
    )
    review_sections = _to_plain_dict(
        normalized_completion_view.get("review_sections")
        or normalized_success_view.get("review_sections")
    )
    review_rows = _to_plain_dict(normalized_completion_view.get("review_rows"))
    prepared_review_rows: Dict[str, Dict[str, Any]] = {}
    for section in ("構成", "文体", "根拠"):
        row = _to_plain_dict(review_rows.get(section))
        fallback_text = str(review_sections.get(section) or "")
        prepared_review_rows[section] = {
            "text": str(row.get("text") or fallback_text),
            "visible": bool(row.get("visible") if row else fallback_text),
        }
    review_visible = bool(
        normalized_completion_view.get("review_visible")
        if "review_visible" in normalized_completion_view
        else normalized_success_view.get("review_visible")
    )
    quality_warning_summary = _to_plain_dict(
        normalized_completion_view.get("quality_warning_summary")
        or normalized_success_view.get("quality_warning_summary")
    )
    status_text = str(
        normalized_completion_view.get("status_text")
        or normalized_success_view.get("status_text")
        or "生成が完了しました。"
    )
    outcome = str(
        normalized_completion_view.get("outcome")
        or normalized_success_view.get("outcome")
        or ("success_quality_warning" if quality_warning_only else "success")
    )
    notify_text = str(
        normalized_completion_view.get("notify_text")
        or normalized_success_view.get("notify_text")
        or "生成が完了しました"
    )
    notify_color = str(
        normalized_completion_view.get("notify_color")
        or normalized_success_view.get("notify_color")
        or ("warning" if quality_warning_only else "positive")
    )
    return {
        "note_body_chars": note_body_chars,
        "linkedin_chars": linkedin_chars,
        "stats_text": stats_text,
        "review_sections": review_sections,
        "review_rows": prepared_review_rows,
        "review_visible": review_visible,
        "quality_warning_summary": quality_warning_summary,
        "status_text": status_text,
        "outcome": outcome,
        "notify_text": notify_text,
        "notify_color": notify_color,
        "event_extra": {
            "note_body_chars": note_body_chars,
            "linkedin_chars": linkedin_chars,
            "quality_warning_only": bool(quality_warning_only),
            "elapsed_ms": int(elapsed_ms),
        },
    }


def build_current_mainline_legal_postcheck_payload(
    *,
    auto_legal_postcheck: Dict[str, Any],
    note_body_text: str,
) -> Dict[str, Any]:
    normalized_payload = _to_plain_dict(auto_legal_postcheck)
    legal_result = _to_plain_dict(normalized_payload.get("legal_result"))
    usage_action = str(normalized_payload.get("usage_action") or "")
    usage_log_extra: Dict[str, Any] = {}
    if usage_action == "auto_run":
        usage_log_extra["risk_level"] = str(normalized_payload.get("usage_risk_level") or "none")
    elif usage_action:
        usage_log_extra["reason"] = str(normalized_payload.get("usage_reason") or "")
    return {
        "legal_result": legal_result,
        "legal_input_text": str(normalized_payload.get("legal_input_text") or str(note_body_text or "")),
        "legal_status_text": str(normalized_payload.get("legal_status_text") or ""),
        "usage_action": usage_action,
        "usage_log_extra": usage_log_extra,
    }


def build_current_mainline_output_guard_blocked_view(
    output_guard: Dict[str, Any],
    *,
    guard_retry_count: int = 0,
) -> Dict[str, Any]:
    normalized_guard = _to_plain_dict(output_guard)
    guard_reasons = [
        str(item).strip()
        for item in _to_plain_list(normalized_guard.get("reasons"))
        if str(item or "").strip()
    ]
    error_class = str(normalized_guard.get("error_class") or "system")
    reason_code = str(normalized_guard.get("reason_code") or "SYS_QUALITY_GATE_HARD_FAIL")
    needs_input_items = [
        _to_plain_dict(item)
        for item in _to_plain_list(normalized_guard.get("needs_input_items"))
        if isinstance(item, dict)
    ]
    manual_hits = [
        str(item).strip()
        for item in _to_plain_list(normalized_guard.get("manual_instructional_hits"))
        if str(item or "").strip()
    ]

    def _public_guard_reason_lines(reasons: List[str]) -> List[str]:
        public_lines: List[str] = []

        def _append_once(text: str) -> None:
            if text not in public_lines:
                public_lines.append(text)

        for reason in reasons:
            normalized_reason = str(reason or "").lower()
            if (
                normalized_reason.startswith("fingerprint")
                or "bigram" in normalized_reason
                or "vocab" in normalized_reason
                or "nominalization" in normalized_reason
                or "syntactic" in normalized_reason
                or "comma" in normalized_reason
                or "sentence_ending" in normalized_reason
                or "paragraph_length" in normalized_reason
            ):
                _append_once("- 文章の単調さや不自然な繰り返しが残りました。")
            elif (
                normalized_reason.startswith("source_grounding")
                or normalized_reason.startswith("contract")
                or "must_cover" in normalized_reason
                or "source_trace" in normalized_reason
            ):
                _append_once("- 資料の根拠が本文に十分反映されませんでした。")
            elif "manual" in normalized_reason or "instruction" in normalized_reason:
                _append_once("- 本文に表示すべきでない断片が含まれる可能性があります。")

        if not public_lines:
            public_lines.append("- 生成結果の品質が基準に届きませんでした。")
        return public_lines

    issue_lines = [
        "- 生成結果に不整合が見つかったため、本文の表示を止めました。",
    ]
    issue_lines.extend(_public_guard_reason_lines(guard_reasons))
    if guard_retry_count > 0:
        issue_lines.append(f"- 自動補修リトライ: {int(guard_retry_count)}回実施済み")
    if needs_input_items:
        issue_lines.append("- 追加で必要なこと:")
        for item in needs_input_items[:3]:
            template = str(item.get("question_template", "") or "")
            if template:
                issue_lines.append(f"  - {template}")
    if manual_hits:
        issue_lines.append("- 本文に表示すべきでない断片が含まれる可能性があります。")

    if error_class == "user_input":
        issue_lines.append("- 対処: 必須入力を補って再実行してください。")
        status_text = "入力不足を検出しました。必要項目を入力してください。"
        notify_text = "入力不足を検出しました。"
        notify_color = "warning"
        outcome = "needs_input_guard"
    else:
        issue_lines.append("- 対処: 入力内容や資料を見直して、もう一度生成してください。")
        status_text = "品質確認で停止しました。本文は表示していません。"
        notify_text = "生成結果に重大な不整合があったため表示を停止しました。"
        notify_color = "negative"
        outcome = "blocked_quality_guard"

    return {
        "status_text": status_text,
        "notify_text": notify_text,
        "notify_color": notify_color,
        "outcome": outcome,
        "reason_code": reason_code,
        "error_class": error_class,
        "needs_input_items": needs_input_items,
        "source_error_content": "\n".join(issue_lines),
        "result_patch": {
            "runtime_error_class": error_class,
            "runtime_reason_code": reason_code,
            "needs_input_items": needs_input_items,
        },
        "event_extra": {
            "guard_reason_count": len(guard_reasons),
            "manual_hit_count": len(manual_hits),
        },
    }
