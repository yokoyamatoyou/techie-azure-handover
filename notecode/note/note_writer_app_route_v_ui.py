"""Route V UI card and click handler helpers for note_writer_app."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from nicegui import run, ui

from note.blog_image_auto import successful_image_paths
from note.preview_sanitizer import sanitize_markdown_preview
from note.writer_only_brief import CATEGORY_OPTIONS
from note.writer_only_image_handoff import build_writer_only_image_context
from note.route_v_generation_service import new_route_v_run_id, read_route_v_progress, run_route_v_generation

logger = logging.getLogger(__name__)

BLOG_PERSONA_PROFILE_OPTIONS = [
    "感情豊かな広報",
    "ユーモアのあるサービス紹介担当",
    "まじめな広報",
]
SOURCE_POLICY_REASON_CODES = {"ROUTE_V_SOURCE_POLICY_BLOCKED"}
API_FAILURE_REASON_CODES = {
    "ROUTE_V_OPENAI_TIMEOUT",
    "ROUTE_V_OPENAI_RATE_LIMIT",
    "ROUTE_V_OPENAI_AUTH_FAILED",
    "ROUTE_V_OPENAI_CONNECTION_FAILED",
    "ROUTE_V_OPENAI_API_ERROR",
}
SOURCE_RELATED_SMOKE_FAILURES = {"source_grounding"}
NON_BLOCKING_SMOKE_FAILURES = {
    "article_body_length",
    "audience_anchor",
    "voice_consistency",
    "section_reader_relevance",
}
NON_BLOCKING_QUALITY_ISSUES = {
    "connector_repetition",
    "model_frequent_word",
    "sentence_too_long",
    "sentence_length_outlier",
}
NON_BLOCKING_SNS_FAILURES = {
    "key_points_preserved",
}
ROUTE_V_DEFAULT_READER_PROBLEMS = {
    "会社・サービス紹介": "会社の背景やサービス内容を知りたい",
    "課題解説・ノウハウ": "困っていることの背景や手がかりを知りたい",
    "導入事例・ケース": "実際にどう進めたのかを知りたい",
    "お知らせ": "変更点や対象を知りたい",
    "比較・業界分析": "違いや背景を知りたい",
}
ROUTE_V_DEFAULT_ARTICLE_GOALS = {
    "会社・サービス紹介": "会社の事業内容、背景、提供価値を紹介する",
    "課題解説・ノウハウ": "課題の背景と取れる選択肢を説明する",
    "導入事例・ケース": "事例の流れと支援内容を伝える",
    "お知らせ": "必要な変更点や対象を簡潔に伝える",
    "比較・業界分析": "違いや背景を資料に基づいて伝える",
}
SMOKE_FAILURE_LABELS = {
    "markdown_title": "タイトル形式",
    "markdown_sections": "見出し構成",
    "article_body_length": "本文文字数",
    "self_perspective": "会社側の一人称",
    "no_third_person_article_voice": "第三者紹介文の回避",
    "audience_anchor": "冒頭の読者・課題接続",
    "voice_consistency": "語り手の一貫性",
    "section_reader_relevance": "各見出しの読者接続",
    "source_grounding": "資料に基づく根拠",
    "url_count_within_limit": "ソース件数",
    "persona_enabled": "読者・目的・語り手の入力",
    "writer_contract_first_person": "一人称ルール",
    "route_v_used": "Route V使用",
    "fallback_not_used": "fallback不使用",
    "route_0506_not_used": "旧Route 0506不使用",
    "legacy_body_route_not_used": "旧本文ルート不使用",
    "repair_not_used": "repair不使用",
}
QUALITY_ISSUE_LABELS = {
    "connector_repetition": "接続語の反復",
    "low_density_reader_meta_sentence": "AI的な低密度説明文",
    "model_frequent_word_repetition": "AI的な頻出語の反復",
    "model_frequent_word": "AI的な頻出語の反復",
    "sentence_too_long": "長い文の調整",
    "sentence_length_outlier": "文の長さの偏り",
}


@dataclass(frozen=True)
class RouteVControls:
    category: Any
    tone: Any
    instruction: Any
    target_reader: Any
    reader_problem: Any
    article_goal: Any
    company_speaker: Any
    button: Any
    image_pattern: Any | None = None


@dataclass(frozen=True)
class RouteVStatusTargets:
    generate_button: Any
    route_v_button: Any
    spinner: Any
    generation_progress: Any
    generation_progress_note: Any
    missing_source_alert: Any
    source_error_area: Any
    status_label: Any


@dataclass(frozen=True)
class RouteVResultTargets:
    title_area: Any
    lead_area: Any
    body_area: Any
    references_area: Any
    hashtags_area: Any
    full_text_area: Any
    note_body_text: Any
    linkedin_area: Any
    linkedin_short_area: Any
    preview: Any
    stats_label: Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _control_text(control: Any) -> str:
    return _text(getattr(control, "value", ""))


def _image_pattern_label_options(image_pattern_options: Mapping[str, Mapping[str, Any]]) -> list[str]:
    return [str(option["label"]) for option in image_pattern_options.values()]


def _default_image_pattern_label(
    *,
    image_pattern_options: Mapping[str, Mapping[str, Any]],
    default_image_pattern_key: str,
) -> str:
    return str(image_pattern_options[default_image_pattern_key]["label"])


def _category_value(controls: RouteVControls) -> str:
    return str(getattr(controls.category, "value", "") or "課題解説・ノウハウ")


def _default_reader_problem(category_label: str) -> str:
    return ROUTE_V_DEFAULT_READER_PROBLEMS.get(
        category_label,
        ROUTE_V_DEFAULT_READER_PROBLEMS["課題解説・ノウハウ"],
    )


def _default_article_goal(category_label: str) -> str:
    return ROUTE_V_DEFAULT_ARTICLE_GOALS.get(
        category_label,
        ROUTE_V_DEFAULT_ARTICLE_GOALS["課題解説・ノウハウ"],
    )


def render_route_v_generation_card(
    *,
    image_pattern_options: Mapping[str, Mapping[str, Any]],
    default_image_pattern_key: str,
) -> RouteVControls:
    """Render the visible Route V generation card and return its controls."""
    with ui.card().classes("w-full p-4 gap-3 mt-3").style(
        "border: 1px solid rgba(72,58,50,0.14); background: #FFFDFC;"
    ):
        ui.label("記事生成").classes("text-sm font-semibold text-[#5D4A41]")
        with ui.row().classes("w-full gap-3"):
            category = ui.select(
                options=list(CATEGORY_OPTIONS.keys()),
                value="課題解説・ノウハウ",
                label="目的",
            ).classes("w-full").props("outlined stack-label")
            tone = ui.select(
                options=BLOG_PERSONA_PROFILE_OPTIONS,
                value="まじめな広報",
                label="ブログ担当ペルソナ",
            ).classes("w-full").props("outlined stack-label")
            image_pattern = ui.select(
                options=_image_pattern_label_options(image_pattern_options),
                value=_default_image_pattern_label(
                    image_pattern_options=image_pattern_options,
                    default_image_pattern_key=default_image_pattern_key,
                ),
                label="画像のトーン",
            ).classes("w-full").props("outlined stack-label")
        ui.label("記事生成後に、選んだトーンで文字入り画像と文字なし画像も自動生成します。").classes(
            "text-xs text-[#7A3A16]"
        )
        instruction = ui.input(
            label="短い指示",
            placeholder="例: 会社の事業内容と大切にしている姿勢を自然に紹介したい",
        ).classes("w-full").props("outlined stack-label clearable")
        target_reader = ui.input(
            label="想定読者（任意）",
            placeholder="例: 空き家や瑕疵物件の所有者",
        ).classes("w-full").props("outlined stack-label clearable")
        button = ui.button("記事を生成").classes("primary-btn w-full")
    return RouteVControls(
        category=category,
        tone=tone,
        instruction=instruction,
        target_reader=target_reader,
        reader_problem=None,
        article_goal=None,
        company_speaker=None,
        button=button,
        image_pattern=image_pattern,
    )


def build_route_v_generation_kwargs(
    *,
    state: Any,
    controls: RouteVControls,
    fallback_instruction: Callable[[], Any],
) -> dict[str, Any]:
    instruction = _text(_control_text(controls.instruction) or fallback_instruction())
    category_label = _category_value(controls)
    article_goal = _control_text(controls.article_goal) or instruction or _default_article_goal(category_label)
    kwargs = {
        "sources": getattr(state, "sources", []),
        "category_label": category_label,
        "tone_label": str(controls.tone.value or "まじめな広報"),
        "target_reader": _control_text(controls.target_reader),
        "reader_problem": _control_text(controls.reader_problem) or _default_reader_problem(category_label),
        "article_goal": article_goal,
        "company_speaker": _control_text(controls.company_speaker) or "会社側の担当者",
        "instruction": instruction,
    }
    return kwargs


def apply_route_v_result(
    result: Mapping[str, Any],
    *,
    targets: RouteVResultTargets,
    sanitize_preview: Callable[[str], str] = sanitize_markdown_preview,
    refresh_output_stage_visibility: Callable[[], None],
    refresh_step_indicators: Callable[[], None],
) -> str:
    body = str(result.get("body") or result.get("full_text") or "")
    if not body:
        return ""
    targets.title_area.value = str(result.get("title") or "")
    targets.lead_area.value = ""
    targets.body_area.value = body
    targets.references_area.value = ""
    targets.hashtags_area.value = ""
    targets.full_text_area.value = body
    targets.note_body_text.value = body
    targets.linkedin_area.value = str(result.get("linkedin_text") or "")
    targets.linkedin_short_area.value = str(result.get("linkedin_short_text") or "")
    targets.preview.content = sanitize_preview(body)
    targets.preview.classes(remove="article-preview-placeholder")
    targets.stats_label.text = (
        f"Route V 本文: {len(body)}文字 / "
        f"SNS用文章: {len(str(result.get('linkedin_short_text') or result.get('linkedin_text') or ''))}文字"
    )
    refresh_output_stage_visibility()
    refresh_step_indicators()
    return body


def clear_route_v_result(
    *,
    targets: RouteVResultTargets,
    refresh_output_stage_visibility: Callable[[], None],
    refresh_step_indicators: Callable[[], None],
    placeholder: str = "",
) -> None:
    targets.title_area.value = ""
    targets.lead_area.value = ""
    targets.body_area.value = ""
    targets.references_area.value = ""
    targets.hashtags_area.value = ""
    targets.full_text_area.value = ""
    targets.note_body_text.value = ""
    targets.linkedin_area.value = ""
    targets.linkedin_short_area.value = ""
    targets.preview.content = placeholder
    targets.preview.classes(add="article-preview-placeholder")
    targets.stats_label.text = ""
    refresh_output_stage_visibility()
    refresh_step_indicators()


def _disable_generation_controls(targets: RouteVStatusTargets) -> None:
    targets.generate_button.disable()
    targets.route_v_button.disable()
    targets.spinner.visible = True
    targets.generation_progress.visible = True
    targets.generation_progress.value = 0.02
    targets.generation_progress_note.visible = True
    targets.generation_progress_note.text = "進行状況: 2% ブログ作成の準備をしています。"
    targets.source_error_area.content = ""
    targets.status_label.text = "ブログ作成を開始しました。"


def _enable_generation_controls(targets: RouteVStatusTargets) -> None:
    targets.spinner.visible = False
    targets.generate_button.enable()
    targets.route_v_button.enable()


def _show_completion(
    result: Mapping[str, Any],
    *,
    targets: RouteVStatusTargets,
    result_targets: RouteVResultTargets | None = None,
    refresh_output_stage_visibility: Callable[[], None] | None = None,
    refresh_step_indicators: Callable[[], None] | None = None,
    defer_final_progress: bool = False,
) -> None:
    targets.generation_progress.value = 0.9 if defer_final_progress else 1.0
    artifact_root = str(result.get("artifact_root") or "")
    non_blocking_quality_miss = (not bool(result.get("success"))) and _is_non_blocking_quality_miss(result)
    if bool(result.get("success")) or non_blocking_quality_miss:
        if non_blocking_quality_miss:
            warning_view = _build_stop_view(result, artifact_root=artifact_root)
            targets.source_error_area.content = warning_view["detail"]
        else:
            targets.source_error_area.content = ""
        if defer_final_progress:
            targets.status_label.text = "画像を作成しています。本文はあとでさらに磨けます。" if non_blocking_quality_miss else "画像を作成しています。"
            targets.generation_progress_note.text = (
                "本文を保持したまま、画像も続けて作成しています。"
                if non_blocking_quality_miss
                else "SNS文章を作成しました。画像を作成しています。"
            )
        else:
            if non_blocking_quality_miss:
                targets.status_label.text = warning_view["status"]
                targets.generation_progress_note.text = warning_view["progress"]
                ui.notify(warning_view["notification"], color="warning")
            else:
                targets.status_label.text = "ブログとSNS用文章を作成しました。"
                targets.generation_progress_note.text = "ブログ本文とSNS用文章を作成しました。"
                ui.notify("ブログとSNS用文章を作成しました。", color="positive")
        return
    stop_view = _build_stop_view(result, artifact_root=artifact_root)
    if (
        result_targets is not None
        and refresh_output_stage_visibility is not None
        and refresh_step_indicators is not None
        and not str(result.get("body") or result.get("full_text") or "").strip()
    ):
        clear_route_v_result(
            targets=result_targets,
            refresh_output_stage_visibility=refresh_output_stage_visibility,
            refresh_step_indicators=refresh_step_indicators,
            placeholder=stop_view["detail"],
        )
    targets.status_label.text = stop_view["status"]
    targets.source_error_area.content = stop_view["detail"]
    targets.generation_progress_note.text = stop_view["progress"]
    notification_color = "negative" if bool(result.get("blocked")) and not str(result.get("body") or result.get("full_text") or "").strip() else "warning"
    ui.notify(stop_view["notification"], color=notification_color)


def _build_stop_view(result: Mapping[str, Any], *, artifact_root: str) -> dict[str, str]:
    reason_code = str(result.get("reason_code") or "")
    failed = _failed_smoke_checks(result)
    failed_labels = _format_failed_smoke_checks(failed)
    has_body = bool(str(result.get("body") or result.get("full_text") or "").strip())

    if bool(result.get("blocked")) and not has_body and reason_code in API_FAILURE_REASON_CODES:
        message = str(result.get("message") or "").strip()
        message_line = f"\n- 詳細: {message[:240]}" if message else ""
        api_detail = _format_api_error_detail(result)
        return {
            "status": "OpenAI APIエラーで記事生成が停止しました。本文は作成されていません。",
            "detail": (
                "外部APIの応答で記事生成が停止しました。本文は作成されていません。古い本文は表示していません。"
                "入力やソースの内容が原因とは限りません。APIキー、利用制限、接続状態、OpenAI側の応答状況を確認してください。\n\n"
                f"- 理由: {reason_code}{api_detail}{message_line}\n"
                f"- 詳細保存先: `{artifact_root}`"
            ),
            "progress": "APIエラーのため本文は作成されていません。",
            "notification": "OpenAI APIエラーで記事生成が停止しました。",
        }

    if bool(result.get("blocked")) and not has_body and reason_code not in SOURCE_POLICY_REASON_CODES:
        message = str(result.get("message") or "").strip()
        message_line = f"\n- 詳細: {message[:240]}" if message else ""
        return {
            "status": "記事生成に失敗しました。本文は作成されていません。",
            "detail": (
                "記事生成の途中で処理が停止しました。本文は作成されていません。古い本文は表示していません。"
                "入力とソースを確認し、必要なら再生成してください。\n\n"
                f"- 理由: {reason_code or '未特定'}{message_line}\n"
                f"- 詳細保存先: `{artifact_root}`"
            ),
            "progress": "本文は作成されていません。",
            "notification": "記事生成に失敗しました。本文は作成されていません。",
        }

    if reason_code in SOURCE_POLICY_REASON_CODES:
        policy_detail = _format_policy_results(result)
        return {
            "status": "使えるソースが不足しているため、記事生成を開始できませんでした。",
            "detail": (
                "追加したURL/PDF/DOCX/txt/mdを取得または読み込みできませんでした。"
                "使えるソースを追加するか、読み込めるソースへ差し替えてください。\n\n"
                f"- 理由: {reason_code}{policy_detail}\n"
                f"- 詳細保存先: `{artifact_root}`"
            ),
            "progress": f"Route V source intake stopped: {artifact_root}",
            "notification": "使えるソースが不足しています。ソースを追加または差し替えてください。",
        }

    if SOURCE_RELATED_SMOKE_FAILURES.intersection(failed):
        unsupported = _unsupported_generalizations(result)
        unsupported_text = f"\n- 資料にない可能性がある語句: {', '.join(unsupported)}" if unsupported else ""
        prefix = "本文は生成されていますが、" if has_body else ""
        return {
            "status": f"{prefix}ソース根拠が不足している可能性があります。",
            "detail": (
                "生成文に対して、現在のソースだけでは根拠が不足している可能性があります。"
                "関連する公式ページ、PDF、説明資料などのソースを追加してから再生成してください。\n\n"
                f"- 未通過チェック: {failed_labels}{unsupported_text}\n"
                f"- 詳細保存先: `{artifact_root}`"
            ),
            "progress": f"Route V source-grounding review needed: {artifact_root}",
            "notification": "ソース不足の可能性があります。資料を追加してから再生成してください。",
        }

    prefix = "本文は生成されていますが、" if has_body else ""
    quality_issue_types = _quality_issue_types(result)
    if quality_issue_types and has_body:
        length_note = _length_warning_text(result)
        return {
            "status": f"{prefix}さらにコンテンツ力を高められます。",
            "detail": (
                "生成本文は下のプレビューで確認できます。より読みやすく、伝わりやすくするための改善ポイントがあります。"
                "本文と画像生成は保持したまま、内容を確認して仕上げられます。\n\n"
                f"- さらに良くできるポイント: {_format_quality_issue_types(quality_issue_types)}{length_note}"
            ),
            "progress": "本文を作成しました。内容を確認してさらに磨けます。",
            "notification": "本文を作成しました。さらに磨けるポイントがあります。",
        }
    if failed == ["article_body_length"] and has_body:
        details = _smoke_details(result)
        char_count = int(details.get("article_char_count") or 0)
        min_chars = int(details.get("article_min_chars") or 0)
        shortfall = max(0, min_chars - char_count)
        shortfall_text = f"現在は目安より約{shortfall}文字短い状態です。" if shortfall else "本文量の目安を超えています。"
        return {
            "status": f"{prefix}本文をもう少し詳しくできそうです。",
            "detail": (
                f"{shortfall_text}"
                "短い指示に、特に触れたい観点や読者が知りたい判断材料を1つ足して再生成してください。"
            ),
            "progress": "本文をもう少し詳しくできそうです。",
            "notification": "本文は生成されました。必要に応じて観点を足して再生成してください。",
        }
    return {
        "status": f"{prefix}さらに読みやすく整えられます。",
        "detail": (
            "生成本文は下のプレビューで確認できます。"
            "必要に応じて、短い指示へ具体的な観点を1つ足して再生成してください。\n\n"
            f"- さらに良くできるポイント: {failed_labels}"
        ),
        "progress": "本文を確認してください。",
        "notification": "本文を作成しました。必要に応じて観点を足して磨けます。",
    }


def _failed_smoke_checks(result: Mapping[str, Any]) -> list[str]:
    smoke = result.get("smoke_evaluator")
    if not isinstance(smoke, Mapping):
        return []
    failed = smoke.get("failed")
    return [str(item) for item in failed] if isinstance(failed, list) else []


def _format_failed_smoke_checks(failed: list[str]) -> str:
    if not failed:
        return "未特定"
    return "、".join(SMOKE_FAILURE_LABELS.get(item, item) for item in failed)


def _format_quality_issue_types(issue_types: list[str]) -> str:
    if not issue_types:
        return "未特定"
    return "、".join(QUALITY_ISSUE_LABELS.get(item, item) for item in issue_types)


def _length_warning_text(result: Mapping[str, Any]) -> str:
    length = result.get("length_observability")
    if not isinstance(length, Mapping):
        return ""
    if not bool(length.get("below_target")):
        return ""
    actual = int(length.get("actual_chars") or 0)
    target = int(length.get("target_length_chars") or 0)
    source_chars = int(length.get("source_chars") or 0)
    if not actual or not target:
        return ""
    return f"\n- 文字数: {actual}字 / 目標 {target}字（ソース約{source_chars}字）"


def _unsupported_generalizations(result: Mapping[str, Any]) -> list[str]:
    smoke = result.get("smoke_evaluator")
    if not isinstance(smoke, Mapping):
        return []
    details = smoke.get("details")
    if not isinstance(details, Mapping):
        return []
    values = details.get("unsupported_generalizations")
    return [str(item) for item in values] if isinstance(values, list) else []


def _format_policy_results(result: Mapping[str, Any]) -> str:
    policy_results = result.get("policy_results")
    if not isinstance(policy_results, list):
        return ""
    failed: list[str] = []
    for item in policy_results:
        if not isinstance(item, Mapping):
            continue
        if bool(item.get("allowed")):
            continue
        code = str(item.get("reason_code") or "").strip()
        detail = str(item.get("detail") or "").strip()
        if code and detail:
            failed.append(f"{code} ({detail})")
        elif code:
            failed.append(code)
    return f" / {', '.join(failed[:3])}" if failed else ""


def _format_api_error_detail(result: Mapping[str, Any]) -> str:
    api_error = result.get("api_error")
    if not isinstance(api_error, Mapping):
        return ""
    parts: list[str] = []
    stage = str(api_error.get("stage") or "").strip()
    error_type = str(api_error.get("error_type") or "").strip()
    reason_code = str(api_error.get("reason_code") or result.get("reason_code") or "").strip()
    kind = str(api_error.get("kind") or "").strip()
    status_code = int(api_error.get("status_code") or 0)
    timeout = float(api_error.get("request_timeout_seconds") or 0.0)
    elapsed = float(api_error.get("elapsed_seconds") or 0.0)
    retry_after = float(api_error.get("retry_after_seconds") or 0.0)
    if kind != "timeout" and reason_code != "ROUTE_V_OPENAI_TIMEOUT":
        timeout = 0.0
    attempt = int(api_error.get("attempt") or 0)
    max_retries = int(api_error.get("max_retries") or 0)
    send_count = int(api_error.get("api_send_count") or result.get("api_send_count") or 0)
    if status_code:
        parts.append(f"HTTP={status_code}")
    if elapsed:
        parts.append(f"elapsed={elapsed:g}s")
    if retry_after:
        parts.append(f"retry_after={retry_after:g}s")
    if error_type:
        parts.append(f"種別={error_type}")
    if stage:
        parts.append(f"停止段階={stage}")
    if timeout:
        parts.append(f"制限時間={timeout:g}秒")
    if attempt:
        parts.append(f"試行={attempt}/{max_retries + 1}")
    if send_count:
        parts.append(f"API送信={send_count}回")
    return f" / {', '.join(parts)}" if parts else ""


def _plain_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


async def run_route_v_post_success_images(
    *,
    state: Any,
    result: Mapping[str, Any],
    selected_image_pattern_key: Callable[[], str],
    refresh_generated_images: Callable[[], None],
    image_generation_callable: Callable[..., Mapping[str, Any]] | None,
    image_llm: Any = None,
    status_targets: RouteVStatusTargets | None = None,
    io_bound: Callable[[Callable[[], Mapping[str, Any]]], Any] = run.io_bound,
) -> None:
    if not _should_attempt_post_success_images(result) or image_generation_callable is None or image_llm is None:
        return
    context = build_writer_only_image_context(result, result.get("artifact_root"))
    if not str(context.get("body") or "").strip():
        return

    state.generated_images = []
    state.generated_image_variants = []
    state.image_generation_status = "running"
    if status_targets is not None:
        status_targets.generation_progress.visible = True
        status_targets.generation_progress.value = 0.92
        status_targets.status_label.text = "画像を生成しています。"
        status_targets.generation_progress_note.text = "画像を作成しています。"
    refresh_generated_images()

    pattern_key = str(selected_image_pattern_key() or "simple")
    try:
        image_result = await io_bound(
            lambda: image_generation_callable(
                llm=image_llm,
                title=str(context.get("title") or ""),
                lead=str(context.get("lead") or ""),
                body=str(context.get("body") or ""),
                article_type=str(context.get("article_type") or ""),
                pattern_key=pattern_key,
            )
        )
        image_result_dict = dict(image_result) if isinstance(image_result, Mapping) else {}
        state.generated_image_variants = _plain_list(image_result_dict.get("variants"))
        state.generated_images = successful_image_paths(image_result_dict)
        state.image_generation_status = str(image_result_dict.get("status") or "failed")
        if status_targets is not None:
            status_targets.generation_progress.value = 1.0
            if state.image_generation_status == "success" and state.generated_images:
                if _is_non_blocking_quality_miss(result):
                    status_targets.status_label.text = "画像まで作成しました。本文はさらに磨けます。"
                    status_targets.generation_progress_note.text = "画像まで作成しました。本文の改善ポイントを表示しています。"
                    ui.notify("画像まで作成しました。本文はさらに磨けます。", color="warning")
                else:
                    status_targets.status_label.text = "ブログ・SNS用文章・画像を作成しました。"
                    status_targets.generation_progress_note.text = "ブログ・SNS文章・画像を作成しました。"
                    ui.notify("ブログ・SNS文章・画像を作成しました。", color="positive")
            else:
                status_targets.status_label.text = "ブログとSNS用文章は作成済みです。画像生成の確認が必要です。"
                status_targets.generation_progress_note.text = "画像生成結果の確認が必要です。ブログ本文とSNS用文章はそのまま使えます。"
        logger.info(
            "Route V post-success image generation finished status=%s images=%s touch=%s",
            state.image_generation_status,
            len(state.generated_images),
            pattern_key,
        )
    except Exception:
        logger.exception("Route V post-success image generation failed open")
        state.generated_images = []
        state.generated_image_variants = []
        state.image_generation_status = "failed"
        if status_targets is not None:
            status_targets.generation_progress.value = 1.0
            status_targets.status_label.text = "ブログとSNS用文章は作成済みです。画像生成に失敗しました。"
            status_targets.generation_progress_note.text = "画像生成に失敗しました。ブログ本文とSNS用文章はそのまま使えます。"
    finally:
        refresh_generated_images()


async def run_route_v_generation_click(
    *,
    state: Any,
    controls: RouteVControls,
    status_targets: RouteVStatusTargets,
    result_targets: RouteVResultTargets,
    fallback_instruction: Callable[[], Any],
    refresh_output_stage_visibility: Callable[[], None],
    refresh_step_indicators: Callable[[], None],
    to_plain_dict: Callable[[Any], dict[str, Any]],
    generation_callable: Callable[..., Mapping[str, Any]] = run_route_v_generation,
    image_generation_callable: Callable[..., Mapping[str, Any]] | None = None,
    image_llm: Any = None,
    selected_image_pattern_key: Callable[[], str] = lambda: "simple",
    refresh_generated_images: Callable[[], None] = lambda: None,
    focus_source_input: Callable[[], None] = lambda: None,
    io_bound: Callable[[Callable[[], Mapping[str, Any]]], Any] = run.io_bound,
    sanitize_preview: Callable[[str], str] = sanitize_markdown_preview,
) -> None:
    if getattr(state, "busy", False):
        ui.notify("生成中です。完了後に再実行してください。", color="warning")
        return
    if not getattr(state, "sources", []):
        message = "資料を1件以上追加してください。URL / PDF / 画像 / テキストを追加すると記事を生成できます。"
        status_targets.status_label.text = ""
        status_targets.source_error_area.content = ""
        status_targets.missing_source_alert.content = (
            f"{message}\n\n"
            "入力済みの方針や読者設定はそのまま残っています。下の資料入力から追加してください。"
        )
        focus_source_input()
        return
    status_targets.missing_source_alert.content = ""
    state.busy = True
    _disable_generation_controls(status_targets)
    state.result = {}
    clear_route_v_result(
        targets=result_targets,
        refresh_output_stage_visibility=refresh_output_stage_visibility,
        refresh_step_indicators=refresh_step_indicators,
        placeholder="生成中です。完了するとここに新しい本文が表示されます。",
    )
    try:
        kwargs = build_route_v_generation_kwargs(
            state=state,
            controls=controls,
            fallback_instruction=fallback_instruction,
        )
        route_v_run_id = new_route_v_run_id()
        kwargs["run_id"] = route_v_run_id
        state.route_v_run_id = route_v_run_id
        status_targets.generation_progress.value = 0.06
        status_targets.status_label.text = "資料を確認しています。 6%"
        status_targets.generation_progress_note.text = "進行状況: 6% 資料を確認しています。"
        progress_task = asyncio.create_task(
            _poll_route_v_generation_progress(
                run_id=route_v_run_id,
                status_targets=status_targets,
                progress_reader=read_route_v_progress,
            )
        )
        try:
            result = await io_bound(lambda: generation_callable(**kwargs))
        finally:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
        state.result = to_plain_dict(result)
        apply_route_v_result(
            result,
            targets=result_targets,
            sanitize_preview=sanitize_preview,
            refresh_output_stage_visibility=refresh_output_stage_visibility,
            refresh_step_indicators=refresh_step_indicators,
        )
        will_attempt_images = bool(
            _should_attempt_post_success_images(result) and image_generation_callable is not None and image_llm is not None
        )
        _show_completion(
            result,
            targets=status_targets,
            result_targets=result_targets,
            refresh_output_stage_visibility=refresh_output_stage_visibility,
            refresh_step_indicators=refresh_step_indicators,
            defer_final_progress=will_attempt_images,
        )
        await run_route_v_post_success_images(
            state=state,
            result=result,
            selected_image_pattern_key=selected_image_pattern_key,
            refresh_generated_images=refresh_generated_images,
            image_generation_callable=image_generation_callable,
            image_llm=image_llm,
            status_targets=status_targets,
            io_bound=io_bound,
        )
        if _should_attempt_post_success_images(result) and float(status_targets.generation_progress.value or 0.0) < 1.0:
            status_targets.generation_progress.value = 1.0
            status_targets.generation_progress_note.text = "ブログ本文とSNS用文章を作成しました。"
        logger.info(
            "Route V UI generation finished success=%s run_id=%s artifact_root=%s route_v_used=%s legacy_body_route_used=%s fallback_used=%s",
            bool(result.get("success")),
            str(result.get("run_id") or ""),
            str(result.get("artifact_root") or ""),
            bool(result.get("route_v_used")),
            bool(result.get("legacy_body_route_used")),
            bool(result.get("fallback_used")),
        )
    except Exception:
        logger.exception("Route V UI generation failed")
        status_targets.status_label.text = "記事生成でエラーが発生しました。"
        error_message = "記事生成中にエラーが発生しました。本文は作成されていません。ログを確認してください。"
        status_targets.source_error_area.content = f"{error_message}\n\n- 詳細: `logs/app.log`"
        clear_route_v_result(
            targets=result_targets,
            refresh_output_stage_visibility=refresh_output_stage_visibility,
            refresh_step_indicators=refresh_step_indicators,
            placeholder=error_message,
        )
        ui.notify("記事生成でエラーが発生しました。", color="negative")
    finally:
        state.busy = False
        _enable_generation_controls(status_targets)


async def _poll_route_v_generation_progress(
    *,
    run_id: str,
    status_targets: RouteVStatusTargets,
    progress_reader: Callable[[str], Mapping[str, Any]],
    interval_seconds: float = 0.5,
    smooth_after_seconds: float = 0.5,
    smooth_step_percent: float = 0.15,
) -> None:
    loop = asyncio.get_running_loop()
    last_soft_advance_at = loop.time()
    while True:
        progress = progress_reader(run_id)
        if progress:
            percent = _bounded_percent(progress.get("percent"))
            current_percent = _progress_percent_float(status_targets.generation_progress.value)
            if 0 < percent < 100:
                now = loop.time()
                display_percent = max(current_percent, float(percent))
                if percent > current_percent:
                    last_soft_advance_at = now
                elif now - last_soft_advance_at >= max(0.0, float(smooth_after_seconds)):
                    display_percent = min(
                        _route_v_progress_soft_ceiling(percent),
                        current_percent + max(0.01, float(smooth_step_percent)),
                    )
                    last_soft_advance_at = now
                message = str(progress.get("message") or "記事生成を進めています。").strip()
                status_targets.generation_progress.visible = True
                if display_percent > current_percent:
                    status_targets.generation_progress.value = display_percent / 100.0
                display_label = _bounded_percent(display_percent)
                status_targets.status_label.text = f"{message} {display_label}%"
                status_targets.generation_progress_note.visible = True
                status_targets.generation_progress_note.text = f"進行状況: {display_label}% {message}"
        await asyncio.sleep(max(0.1, float(interval_seconds)))


def _bounded_percent(value: Any) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return max(0, min(100, int(round(number))))


def _progress_percent_float(progress_value: Any) -> float:
    try:
        number = float(progress_value or 0.0) * 100.0
    except (TypeError, ValueError):
        number = 0.0
    return max(0.0, min(100.0, number))


def _route_v_progress_soft_ceiling(checkpoint_percent: int) -> float:
    for next_checkpoint in (6, 12, 18, 48, 50, 60, 72, 80, 86, 90, 94, 97, 100):
        if checkpoint_percent < next_checkpoint:
            return float(next_checkpoint) - 0.1
    return 99.9


def _should_attempt_post_success_images(result: Mapping[str, Any]) -> bool:
    if bool(result.get("success")):
        return True
    return _is_non_blocking_quality_miss(result)


def _is_non_blocking_quality_miss(result: Mapping[str, Any]) -> bool:
    if not str(result.get("body") or result.get("full_text") or "").strip():
        return False
    sns_evaluator = result.get("sns_evaluator") if isinstance(result.get("sns_evaluator"), Mapping) else {}
    if sns_evaluator and not bool(sns_evaluator.get("passed")):
        failed_sns = sns_evaluator.get("failed")
        failed_sns_items = [str(item) for item in failed_sns] if isinstance(failed_sns, list) else []
        if not failed_sns_items or not all(item in NON_BLOCKING_SNS_FAILURES for item in failed_sns_items):
            return False
    failed = _failed_smoke_checks(result)
    if failed:
        return all(item in NON_BLOCKING_SMOKE_FAILURES for item in failed)
    issue_types = _quality_issue_types(result)
    return bool(issue_types) and all(item in NON_BLOCKING_QUALITY_ISSUES for item in issue_types)


def _quality_issue_types(result: Mapping[str, Any]) -> list[str]:
    quality_report = result.get("quality_report") if isinstance(result.get("quality_report"), Mapping) else {}
    quality = quality_report.get("quality_check") if isinstance(quality_report.get("quality_check"), Mapping) else {}
    nested_quality = quality.get("quality_check") if isinstance(quality.get("quality_check"), Mapping) else None
    if nested_quality is not None:
        quality = nested_quality
    issues = quality.get("issues")
    if not isinstance(issues, list):
        return []
    return [str(item.get("type") or "").strip() for item in issues if isinstance(item, Mapping) and str(item.get("type") or "").strip()]


def _smoke_details(result: Mapping[str, Any]) -> Mapping[str, Any]:
    evaluator = result.get("smoke_evaluator") if isinstance(result.get("smoke_evaluator"), Mapping) else {}
    details = evaluator.get("details") if isinstance(evaluator.get("details"), Mapping) else {}
    return details
