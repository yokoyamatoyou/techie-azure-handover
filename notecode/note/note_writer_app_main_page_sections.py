"""Main-page pre-generation section builders for note_writer_app Phase 05."""
from __future__ import annotations

from typing import Any, Callable, Mapping

from nicegui import ui

from note.note_writer_app_generation_progress import _format_generation_progress_text


def build_article_type_descriptions() -> dict[str, str]:
    return {
        "解説": "専門情報を読者が行動できる形に翻訳する。",
        "日常": "日々の出来事と学びを短く自然に共有する。",
        "ブランド": "価値訴求を読者視点で具体化する。",
        "お知らせ": "変更点を簡潔かつ正確に伝える。",
        "事例": "再現可能な実行手順と成果を示す。",
        "業界分析": "比較軸と根拠を明示して分析する。",
        "比較レビュー": "候補の違いを評価軸で整理する。",
    }


def build_source_mode_choice_card_copy() -> dict[str, dict[str, str]]:
    return {
        "grounded": {
            "title": "資料あり",
            "summary": "URL / PDF / 画像 / テキストを先に追加して、その材料を軸に書きます。",
            "detail": "資料がある案件向け。必須項目と資料入力をまとめて進めます。",
        },
        "web": {
            "title": "お任せ",
            "summary": "1行テーマで始め、公開済みブログの蓄積が十分なときだけ外部ソースの材料収集へ進みます。",
            "detail": "利用条件は公開済み3件以上かつ合計本文4500字以上です（条件を満たさない場合は「資料あり」への切り替えを案内します）。公開済みブログ本文は今回の記事の事実ソースにしません。",
        },
        "prompt_only": {
            "title": "プロンプトのみ",
            "summary": "公開済みブログの蓄積がある日常記事だけ、1行テーマを体験メモとして使います。",
            "detail": "公開済みブログは書き味の参考です。今回記事の事実ソースにはしません。",
        },
    }


def render_brand_header(
    *,
    hub_url: str,
    kotomegane_url: str,
    sanitize_html: Callable[[str], str],
) -> None:
    with ui.row().classes("brand-header"):
        ui.html(
            '<img src="/static/brand/kotomake_logo_cropped.svg" alt="TECHIE" class="brand-logo-inline" />',
            sanitize=sanitize_html,
        )
        with ui.column().classes("brand-copy"):
            ui.label("TECHIE").classes("brand-pill")
            ui.html('<h1 class="hero-title">コトメイク</h1>', sanitize=False)
            ui.label("発信作成").classes("hero-role")
            ui.label("ブログ生成で流入導線を作る").classes("hero-sub")
            ui.label("次は見え方を観測する").classes("hero-next")
        with ui.row().classes("suite-link-row"):
            ui.label("入力: URL / PDF / 画像").classes("brand-pill")
            ui.link("見え方観測へ", kotomegane_url, new_tab=True).classes("suite-link-btn")


def render_step_track(*, current_mainline_ui_mode: str) -> dict[str, Any]:
    with ui.row().classes("step-track w-full") as step_track:
        sticky_step1 = ui.label("① 入力").classes("step-track-item step-track-active sticky-s1")
        ui.label("→").style("color: #D8B9AA; font-size: 14px; line-height: 1;")
        sticky_step2 = ui.label("② 生成準備").classes("step-track-item step-track-pending sticky-s2")
        ui.label("→").style("color: #D8B9AA; font-size: 14px; line-height: 1;")
        sticky_step3 = ui.label("③ 生成結果").classes("step-track-item step-track-pending sticky-s3")
    step_track.visible = current_mainline_ui_mode != "journey"
    return {
        "step_track": step_track,
        "sticky_step1": sticky_step1,
        "sticky_step2": sticky_step2,
        "sticky_step3": sticky_step3,
    }


_STEP_ALL_COLORS = (
    "bg-orange-500 text-white "
    "bg-green-100 text-green-700 "
    "bg-gray-100 text-gray-400 "
    "bg-orange-50 text-orange-600"
)
_STICKY_NOT_DONE = "step-track-active step-track-pending"


def _set_step_badge(badge: Any, style: str, text: str) -> None:
    badge.classes(remove=_STEP_ALL_COLORS, add=style)
    badge.text = text
    badge.update()


def _mark_sticky_done(badge: Any, text: str) -> None:
    badge.classes(remove=_STICKY_NOT_DONE, add="step-track-done")
    badge.text = text
    badge.update()


def _unmark_sticky_done(badge: Any) -> None:
    badge.classes(remove="step-track-done")
    badge.update()


def refresh_generation_step_indicators(
    *,
    state: Any,
    note_body_text: Any,
    step1_badge: Any,
    step2_badge: Any,
    step3_badge: Any,
    sticky_step1: Any,
    sticky_step2: Any,
    sticky_step3: Any,
    refresh_output_stage_visibility: Callable[[], None],
) -> str:
    has_sources = len(getattr(state, "sources", [])) > 0
    has_result = bool(getattr(note_body_text, "value", ""))
    is_busy = bool(getattr(state, "busy", False))
    refresh_output_stage_visibility()
    if has_result:
        _set_step_badge(step1_badge, "bg-green-100 text-green-700", "✓ 入力")
        _set_step_badge(step2_badge, "bg-green-100 text-green-700", "✓ 生成準備")
        _set_step_badge(step3_badge, "bg-orange-500 text-white", "← 生成結果")
        _mark_sticky_done(sticky_step1, "✓ 入力")
        _mark_sticky_done(sticky_step2, "✓ 生成準備")
        _unmark_sticky_done(sticky_step3)
        return "result"
    if is_busy or has_sources:
        _set_step_badge(step1_badge, "bg-green-100 text-green-700", "✓ 入力")
        _set_step_badge(step2_badge, "bg-orange-500 text-white", "← 生成準備")
        _set_step_badge(step3_badge, "bg-gray-100 text-gray-400", "生成結果")
        _mark_sticky_done(sticky_step1, "✓ 入力")
        _unmark_sticky_done(sticky_step2)
        _unmark_sticky_done(sticky_step3)
        return "prepare"
    _set_step_badge(step1_badge, "bg-orange-500 text-white", "← 入力")
    _set_step_badge(step2_badge, "bg-gray-100 text-gray-400", "生成準備")
    _set_step_badge(step3_badge, "bg-gray-100 text-gray-400", "生成結果")
    _unmark_sticky_done(sticky_step1)
    _unmark_sticky_done(sticky_step2)
    _unmark_sticky_done(sticky_step3)
    return "input"


def apply_generation_progress_widgets(
    *,
    status_label: Any,
    generation_progress: Any,
    generation_progress_note: Any,
    label_text: str,
    display_percent: int,
    elapsed: str,
    stage: str,
    live_draft_stream_enabled: bool,
    progress: Mapping[str, Any],
    body_area: Any,
    lead_area: Any,
    note_body_text: Any,
    title_area: Any,
    preview: Any,
    stats_label: Any,
    sanitize_markdown_preview: Callable[[str], str],
) -> None:
    if display_percent > 0 or stage == "completed":
        status_label.text = f"{label_text} {display_percent}%".strip()
    else:
        status_label.text = label_text
    generation_progress.value = display_percent / 100.0
    generation_progress_note.text = _format_generation_progress_text(
        percent=display_percent,
        label_text=label_text,
        elapsed=elapsed,
    )
    generation_progress_note.visible = True
    if not live_draft_stream_enabled:
        return
    partial_body = str(progress.get("partial_body", "") or "")
    if partial_body and partial_body != body_area.value:
        body_area.value = partial_body
        draft_parts = [lead_area.value, partial_body]
        note_body_text.value = "\n\n".join(p for p in draft_parts if p)
        draft_title = title_area.value or "生成中..."
        preview.content = sanitize_markdown_preview(f"{draft_title}\n\n{note_body_text.value}")
        stats_label.text = f"記事本文: {len(note_body_text.value)}文字"


_REQUIRED_INPUT_STEP_STYLES = {
    "done": "border-[rgba(82,145,96,0.28)] bg-[rgba(241,252,244,0.95)]",
    "active": "border-[rgba(222,146,73,0.28)] bg-[rgba(255,248,242,0.98)]",
    "pending": "border-[rgba(222,146,73,0.12)] bg-white",
}
_REQUIRED_INPUT_STEP_ALL_STYLES = " ".join(_REQUIRED_INPUT_STEP_STYLES.values())


def _apply_required_input_step_style(card: Any, state: str) -> None:
    card.classes(
        remove=_REQUIRED_INPUT_STEP_ALL_STYLES,
        add=_REQUIRED_INPUT_STEP_STYLES.get(state, _REQUIRED_INPUT_STEP_STYLES["pending"]),
    )
    card.update()


def refresh_required_input_wizard_widgets(
    *,
    view_state: Mapping[str, Any],
    focused_step: int,
    article_type_ready: bool,
    audience_ready: bool,
    writer_ready: bool,
    audience_committed: bool,
    writer_committed: bool,
    audience_profile_text: str,
    selected_writer_role: str,
    helper_text_builder: Callable[[int], str],
    audience_step_card: Any,
    writer_step_card: Any,
    audience_summary_row: Any = None,
    writer_summary_row: Any = None,
    audience_summary_value_label: Any = None,
    writer_summary_value_label: Any = None,
    audience_next_button: Any = None,
    writer_done_button: Any = None,
    required_input_summary_label: Any = None,
    journey_step4_card: Any = None,
) -> None:
    audience_step_card.visible = bool(view_state.get("audience_editor_visible"))
    audience_step_card.update()
    if article_type_ready:
        _apply_required_input_step_style(audience_step_card, "active")
    if audience_summary_row is not None:
        audience_summary_row.visible = bool(view_state.get("audience_summary_visible"))
        audience_summary_row.update()
    if audience_summary_value_label is not None:
        audience_summary_value_label.text = str(audience_profile_text or "").strip()
        audience_summary_value_label.update()
    if audience_next_button is not None:
        if article_type_ready and focused_step == 2 and audience_ready:
            audience_next_button.enable()
        else:
            audience_next_button.disable()
        audience_next_button.update()
    writer_step_card.visible = bool(view_state.get("writer_editor_visible"))
    writer_step_card.update()
    if article_type_ready and audience_ready:
        _apply_required_input_step_style(writer_step_card, "active")
    if writer_summary_row is not None:
        writer_summary_row.visible = bool(view_state.get("writer_summary_visible"))
        writer_summary_row.update()
    if writer_summary_value_label is not None:
        writer_summary_value_label.text = selected_writer_role or "自動"
        writer_summary_value_label.update()
    if writer_done_button is not None:
        if article_type_ready and audience_committed and focused_step == 3 and writer_ready:
            writer_done_button.enable()
        else:
            writer_done_button.disable()
        writer_done_button.update()
    if required_input_summary_label is not None:
        required_input_summary_label.text = helper_text_builder(focused_step)
        required_input_summary_label.update()
    if journey_step4_card is not None:
        journey_step4_card.visible = bool(focused_step == 4 and audience_committed and writer_committed)
        journey_step4_card.update()


def refresh_required_input_status_widgets(
    *,
    article_type_label: str,
    semantic_label: str,
    audience_profile_text: str,
    default_audience_placeholder: str,
    summary_text: str,
    required_article_type_label: Any = None,
    audience_profile_status_label: Any = None,
    required_input_summary_label: Any = None,
) -> None:
    if required_article_type_label is not None:
        suffix = f" / {semantic_label}" if semantic_label and semantic_label != article_type_label else ""
        required_article_type_label.text = f"記事タイプ: {article_type_label}{suffix}"
        required_article_type_label.update()
    if audience_profile_status_label is not None:
        audience_profile_status_label.classes(remove="text-gray-600 text-red-600")
        normalized_audience = str(audience_profile_text or "").strip()
        if normalized_audience:
            audience_profile_status_label.text = "読者指定あり。誰向けの記事かが明示されています。"
            audience_profile_status_label.classes(add="text-gray-600")
        else:
            audience_profile_status_label.text = (
                "誰向けが未入力です。"
                f"{default_audience_placeholder} のように短く入れてください。"
            )
            audience_profile_status_label.classes(add="text-red-600")
        audience_profile_status_label.update()
    if required_input_summary_label is not None:
        required_input_summary_label.text = summary_text
        required_input_summary_label.update()


def refresh_journey_direction_wizard_widgets(
    *,
    focused_step: int,
    purpose_ready: bool,
    target_ready: bool,
    purpose_label: str,
    target_label: str,
    journey_purpose_step_card: Any = None,
    journey_purpose_summary_row: Any = None,
    journey_purpose_summary_value: Any = None,
    journey_purpose_next_button: Any = None,
    journey_target_step_card: Any = None,
    journey_target_summary_row: Any = None,
    journey_target_summary_value: Any = None,
    journey_target_next_button: Any = None,
) -> None:
    if journey_purpose_step_card is not None:
        journey_purpose_step_card.visible = focused_step == 1
        journey_purpose_step_card.update()
    if journey_purpose_summary_row is not None:
        journey_purpose_summary_row.visible = purpose_ready and focused_step != 1
        journey_purpose_summary_row.update()
    if journey_purpose_summary_value is not None:
        journey_purpose_summary_value.text = str(purpose_label or "")
        journey_purpose_summary_value.update()
    if journey_purpose_next_button is not None:
        if purpose_ready and focused_step == 1:
            journey_purpose_next_button.enable()
        else:
            journey_purpose_next_button.disable()
        journey_purpose_next_button.update()
    if journey_target_step_card is not None:
        journey_target_step_card.visible = purpose_ready and focused_step == 2
        journey_target_step_card.update()
    if journey_target_summary_row is not None:
        journey_target_summary_row.visible = purpose_ready and target_ready and focused_step == 3
        journey_target_summary_row.update()
    if journey_target_summary_value is not None:
        journey_target_summary_value.text = str(target_label or "")
        journey_target_summary_value.update()
    if journey_target_next_button is not None:
        if purpose_ready and target_ready and focused_step == 2:
            journey_target_next_button.enable()
        else:
            journey_target_next_button.disable()
        journey_target_next_button.update()


def refresh_core_message_input_widgets(
    *,
    requires_core_message: bool,
    placeholder: str,
    helper_text: str,
    core_message_input: Any,
    core_message_helper_label: Any,
) -> None:
    core_message_input.visible = requires_core_message
    core_message_input.placeholder = placeholder
    core_message_helper_label.text = helper_text
    core_message_helper_label.update()
    core_message_input.update()


def refresh_profile_control_widgets(
    *,
    type_key: str,
    semantic_key: str,
    branding_subtype_select: Any = None,
    branding_focus_select: Any = None,
    branding_profile_helper_label: Any = None,
) -> None:
    branding_active = type_key == "branding"
    subtype_active = branding_active and semantic_key not in {"activity_introduction", "recruit_culture"}
    if branding_subtype_select is not None:
        branding_subtype_select.visible = subtype_active
        branding_subtype_select.update()
    if branding_focus_select is not None:
        branding_focus_select.visible = branding_active
        branding_focus_select.update()
    if branding_profile_helper_label is not None:
        if branding_active:
            branding_profile_helper_label.text = (
                "ブランド記事では、紹介の軸と強めたい観点だけをここで補えます。細かい説明は上の入力欄や資料で伝えてください。"
            )
        else:
            branding_profile_helper_label.text = "ブランド記事のときだけ、紹介の軸と強めたい観点を表示します。"
        branding_profile_helper_label.update()


def refresh_writer_role_status_widgets(
    *,
    selected_writer_role: str,
    type_key: str,
    self_reference_policy_key: str,
    company_intro_auto_mode: bool,
    looks_theme_like_writer_role: Callable[[str], bool],
    predict_pronoun_hint: Callable[[str, str, str], str],
    writer_role_status_label: Any,
    pronoun_hint_label: Any,
) -> str:
    selected = str(selected_writer_role or "")
    pronoun_hint_label.text = predict_pronoun_hint(
        str(type_key or ""),
        selected,
        str(self_reference_policy_key or ""),
    )
    writer_role_status_label.classes(remove="text-red-600 text-gray-600")
    if not selected and company_intro_auto_mode:
        writer_role_status_label.text = "話者: 自動（役割語を前面に出さない）"
        writer_role_status_label.classes(add="text-gray-600")
        return "company_intro_auto"
    if not selected:
        writer_role_status_label.text = "この内容では、書き手を選んでください。"
        writer_role_status_label.classes(add="text-red-600")
        return "missing"
    if looks_theme_like_writer_role(selected):
        writer_role_status_label.text = "書き手欄には肩書きだけを入れてください。記事の内容は上の入力欄へ入れてください。"
        writer_role_status_label.classes(add="text-red-600")
        return "theme_like"
    writer_role_status_label.text = f"書き手: {selected}"
    writer_role_status_label.classes(add="text-gray-600")
    return "ready"


def refresh_writer_role_select_options_widget(
    *,
    type_key: str,
    semantic_key: str,
    get_writer_role_options: Callable[[str, str], list[str]],
    get_default_writer_role_label: Callable[[str, str], str],
    is_article_type_managed_writer_role_label: Callable[[str], bool],
    writer_role_user_overridden: bool,
    writer_role_select: Any,
    writer_role_default_refresh_state: dict[str, Any],
) -> str:
    options = get_writer_role_options(str(type_key or ""), str(semantic_key or ""))
    current = str(writer_role_select.value or "")
    default_label = get_default_writer_role_label(str(type_key or ""), str(semantic_key or ""))
    writer_role_select.options = options
    should_apply_default = current not in options or (
        not writer_role_user_overridden
        and is_article_type_managed_writer_role_label(current)
        and current != default_label
    )
    if should_apply_default:
        writer_role_default_refresh_state["active"] = True
        writer_role_default_refresh_state["expected_value"] = default_label
        writer_role_select.value = default_label
    try:
        writer_role_select.update()
    finally:
        writer_role_default_refresh_state["active"] = False
    return default_label


def refresh_source_mode_choice_card_widgets(
    *,
    source_mode_choice_cards: Mapping[str, Any],
    available_modes: set[str] | list[str] | tuple[str, ...],
    selected_mode_key: str,
) -> None:
    available_mode_set = set(available_modes)
    for mode_key, mode_card in source_mode_choice_cards.items():
        mode_card.visible = mode_key in available_mode_set
        if mode_key == selected_mode_key:
            mode_card.classes(add="source-mode-choice-card-active")
        else:
            mode_card.classes(remove="source-mode-choice-card-active")
        mode_card.update()


def refresh_source_mode_status_widgets(
    *,
    input_surface: Mapping[str, Any],
    omakase_state: Mapping[str, Any],
    source_mode_key: str,
    has_sources: bool,
    input_required_modes: set[str] | list[str] | tuple[str, ...],
    announcement_inline_error_text: str,
    input_stage_helper_label: Any = None,
    source_mode_helper_label: Any = None,
    user_prompt: Any = None,
    user_prompt_helper_label: Any = None,
    announcement_inline_error_label: Any = None,
    added_sources_section: Any = None,
    source_inputs_section: Any = None,
    source_inputs_title_label: Any = None,
    source_inputs_helper_label: Any = None,
    prompt_input_section: Any = None,
    omakase_status_card: Any = None,
    omakase_status_title: Any = None,
    omakase_status_message: Any = None,
    omakase_status_inventory: Any = None,
    omakase_status_detail: Any = None,
) -> None:
    required_mode_set = set(input_required_modes)
    if input_stage_helper_label is not None:
        input_stage_helper_label.text = str(input_surface.get("section_intro_text") or "")
        input_stage_helper_label.update()
    if source_mode_helper_label is not None:
        source_mode_helper_label.text = str(input_surface.get("source_mode_helper_text") or "")
        source_mode_helper_label.update()
    if user_prompt is not None:
        user_prompt.label = str(input_surface.get("prompt_label") or "1行テーマ")
        user_prompt.placeholder = str(input_surface.get("prompt_placeholder") or "")
        user_prompt.update()
    if user_prompt_helper_label is not None:
        user_prompt_helper_label.text = str(input_surface.get("prompt_helper_text") or "")
        user_prompt_helper_label.update()
    if announcement_inline_error_label is not None:
        announcement_inline_error_label.text = str(announcement_inline_error_text or "")
        announcement_inline_error_label.visible = bool(announcement_inline_error_label.text)
        announcement_inline_error_label.update()
    if added_sources_section is not None:
        added_sources_section.visible = bool(has_sources)
        added_sources_section.update()
    if source_inputs_section is not None:
        source_inputs_section.visible = source_mode_key in required_mode_set
        if source_inputs_title_label is not None:
            source_inputs_title_label.text = str(input_surface.get("source_title_text") or "資料入力")
            source_inputs_title_label.update()
        if source_inputs_helper_label is not None:
            source_inputs_helper_label.text = str(input_surface.get("source_helper_text") or "")
            source_inputs_helper_label.update()
        source_section_order = 2 if source_mode_key in required_mode_set else 4
        source_inputs_section.style(f"order: {source_section_order};")
        source_inputs_section.update()
    if prompt_input_section is not None:
        prompt_input_section.visible = bool(input_surface.get("prompt_visible"))
        prompt_section_order = 4 if source_mode_key in required_mode_set else 2
        prompt_input_section.style(f"order: {prompt_section_order};")
        prompt_input_section.update()
    if omakase_status_card is not None:
        omakase_status_card.visible = bool(omakase_state.get("visible"))
        if bool(omakase_state.get("visible")):
            if omakase_status_title is not None:
                omakase_status_title.text = str(omakase_state.get("title") or "")
                omakase_status_title.update()
            if omakase_status_message is not None:
                omakase_status_message.text = str(omakase_state.get("message") or "")
                omakase_status_message.update()
            if omakase_status_inventory is not None:
                omakase_status_inventory.text = str(omakase_state.get("inventory_text") or "")
                omakase_status_inventory.update()
            if omakase_status_detail is not None:
                omakase_status_detail.text = str(omakase_state.get("detail_text") or "")
                omakase_status_detail.update()
        omakase_status_card.update()


_JOURNEY_CONFIRM_BADGE_CLASSES = "bg-amber-100 text-amber-700 bg-green-100 text-green-700"
_GENERATE_GATE_HINT_CLASSES = "text-green-700 text-amber-700 text-[#5D4A41]"


def refresh_journey_confirmation_cta_widgets(
    *,
    ui_mode: str,
    busy: bool,
    confirmation_ready: bool,
    cta_state: Mapping[str, Any],
    gate_surface: Mapping[str, Any],
    confirm_button_text: str,
    journey_confirm_badge: Any,
    journey_confirm_action_hint: Any,
    journey_preview_button: Any,
    journey_confirm_button: Any,
    generate_button: Any = None,
    generate_gate_hint: Any = None,
) -> None:
    if ui_mode != "journey":
        if generate_gate_hint is not None:
            generate_gate_hint.visible = False
            generate_gate_hint.text = ""
            generate_gate_hint.update()
        if generate_button is not None and not busy:
            generate_button.enable()
            generate_button.text = "記事を生成"
        return

    journey_confirm_badge.text = str(cta_state.get("badge_text") or "")
    journey_confirm_badge.classes(
        remove=_JOURNEY_CONFIRM_BADGE_CLASSES,
        add=str(cta_state.get("badge_classes") or ""),
    )
    journey_confirm_badge.update()
    journey_confirm_action_hint.text = str(cta_state.get("card_hint_text") or "")
    journey_confirm_action_hint.update()
    if generate_gate_hint is not None:
        generate_gate_hint.visible = False
        generate_gate_hint.text = ""
        generate_gate_hint.update()
    if not busy:
        journey_preview_button.enable()
        journey_preview_button.text = str(cta_state.get("preview_button_text") or "不足を確認")
        journey_confirm_button.enable()
        journey_confirm_button.text = confirm_button_text
    else:
        journey_preview_button.disable()
        journey_preview_button.text = "確認中..."
        journey_confirm_button.disable()
        journey_confirm_button.text = "生成中..."
    if generate_button is not None and not busy:
        gate_enabled = bool(gate_surface.get("enabled"))
        generate_button.visible = True
        if gate_enabled and confirmation_ready:
            generate_button.enable()
        else:
            generate_button.disable()
        generate_button.text = str(cta_state.get("generate_button_text") or "この内容で生成を開始")
        if generate_gate_hint is not None:
            generate_gate_hint.visible = True
            generate_gate_hint.text = str(
                cta_state.get("generate_hint_text")
                if gate_enabled
                else gate_surface.get("hint_text")
                or cta_state.get("generate_hint_text")
                or ""
            )
            generate_gate_hint.classes(
                remove=_GENERATE_GATE_HINT_CLASSES,
                add=str(
                    cta_state.get("generate_hint_classes")
                    if gate_enabled and confirmation_ready
                    else gate_surface.get("hint_classes")
                    or cta_state.get("generate_hint_classes")
                    or "text-amber-700"
                ),
            )
            generate_gate_hint.update()


_FOLLOWUP_STATUS_CLASSES = "text-gray-600 text-amber-700 text-green-700 text-red-500"
_JOURNEY_CONFIRM_STATUS_CLASSES = (
    "text-gray-600 text-amber-700 text-green-700 text-red-500 "
    "font-semibold bg-green-50 bg-amber-50 bg-red-50 rounded-lg px-3 py-2"
)


def refresh_interview_followup_widgets(
    *,
    visible: bool,
    note_text: str,
    status_text: str,
    tone: str,
    clear_questions: bool,
    interview_followup_note: Any = None,
    interview_followup_status: Any = None,
    interview_questions_container: Any = None,
    interview_followup_container: Any = None,
) -> None:
    if interview_followup_note is not None:
        interview_followup_note.text = str(note_text or "")
        interview_followup_note.update()
    if interview_followup_status is not None:
        interview_followup_status.text = str(status_text or "")
        interview_followup_status.classes(
            remove=_FOLLOWUP_STATUS_CLASSES,
            add={
                "amber": "text-amber-700",
                "green": "text-green-700",
                "red": "text-red-500",
            }.get(str(tone or "").strip(), "text-gray-600"),
        )
        interview_followup_status.update()
    if clear_questions and interview_questions_container is not None:
        interview_questions_container.clear()
    if interview_followup_container is not None:
        interview_followup_container.visible = bool(visible)
        interview_followup_container.update()


def refresh_journey_confirm_status_widget(
    *,
    text: str,
    tone: str,
    journey_confirm_status: Any = None,
) -> None:
    if journey_confirm_status is None:
        return
    journey_confirm_status.text = str(text or "")
    journey_confirm_status.classes(
        remove=_JOURNEY_CONFIRM_STATUS_CLASSES,
        add={
            "amber": "text-amber-700 font-semibold bg-amber-50 rounded-lg px-3 py-2",
            "green": "text-green-700 font-semibold bg-green-50 rounded-lg px-3 py-2",
            "red": "text-red-500 font-semibold bg-red-50 rounded-lg px-3 py-2",
        }.get(str(tone or "").strip(), "text-gray-600"),
    )
    journey_confirm_status.update()


def render_source_mode_choice_cards() -> dict[str, Any]:
    source_mode_choice_cards: dict[str, Any] = {}
    with ui.row().classes("w-full source-mode-choice-row"):
        for mode_key in ("grounded", "web", "prompt_only"):
            copy = build_source_mode_choice_card_copy()[mode_key]
            mode_card = ui.card().classes("w-full p-4 gap-2 source-mode-choice-card")
            source_mode_choice_cards[mode_key] = mode_card
            with mode_card:
                ui.label(str(copy["title"])).classes(
                    "source-mode-choice-title text-base font-semibold text-[#3D2E28]"
                )
                ui.label(str(copy["summary"])).classes(
                    "source-mode-choice-summary text-sm text-[#5D4A41]"
                )
                ui.label(str(copy["detail"])).classes(
                    "source-mode-choice-detail text-xs text-gray-600"
                )
    return source_mode_choice_cards


def render_required_input_fields(
    *,
    in_wizard: bool,
    initial_type_key: str,
    default_audience_profile_text: str,
    default_audience_profile_placeholder_text: str,
    get_writer_role_options: Callable[[str], list[str]],
    get_default_writer_role_label: Callable[[str], str],
) -> dict[str, Any]:
    container_classes = (
        "w-full gap-3 mt-3 p-4 required-input-card"
        if in_wizard
        else "w-full gap-3 mt-4 p-4 required-input-card"
    )
    heading_text = "記事の前提" if in_wizard else "生成前に決めること"
    helper_text = (
        "STEP3とSTEP4で、誰向けにどの立場で書くかをそろえます。"
        if in_wizard
        else "まず記事タイプ・誰向け・誰視点だけをそろえます。補助項目は詳細設定で調整します。"
    )
    audience_step_card = None
    writer_step_card = None
    audience_summary_row = None
    writer_summary_row = None
    audience_summary_value_label = None
    writer_summary_value_label = None
    audience_next_button = None
    writer_done_button = None
    audience_edit_button = None
    writer_edit_button = None
    required_article_type_label_widget = None
    audience_profile_input_widget = None
    audience_profile_status_label_widget = None
    writer_role_select_widget = None
    writer_role_status_label_widget = None
    pronoun_hint_label_widget = None
    writer_role_custom_toggle_widget = None
    writer_role_custom_widget = None

    with ui.column().classes(container_classes):
        ui.label(heading_text).classes("text-sm font-semibold text-gray-800")
        required_input_summary_label_widget = ui.label(helper_text).classes("text-xs text-gray-600")
        if in_wizard:
            with ui.column().classes(
                "w-full gap-2 p-3 rounded-xl border border-[rgba(222,146,73,0.14)] bg-white"
            ) as audience_step_card:
                ui.label("STEP3 読者").classes("text-[11px] font-bold tracking-wide text-amber-700")
                audience_profile_input_widget = ui.input(
                    "主な読者",
                    value=default_audience_profile_text,
                    placeholder=default_audience_profile_placeholder_text,
                ).classes("w-full").props("outlined stack-label")
                audience_profile_status_label_widget = ui.label(
                    "※誰向けに書くかだけ明示してください。"
                ).classes("text-xs text-gray-600")
                with ui.row().classes("w-full justify-end"):
                    audience_next_button = ui.button("次へ").classes("primary-btn")
            with ui.row().classes(
                "w-full items-center justify-between gap-3 rounded-xl border border-[rgba(82,145,96,0.20)] bg-[rgba(241,252,244,0.92)] px-4 py-3"
            ) as audience_summary_row:
                with ui.column().classes("gap-1"):
                    ui.label("STEP3 読者").classes("text-[11px] font-bold tracking-wide text-green-700")
                    audience_summary_value_label = ui.label("").classes("text-sm text-[#5D4A41]")
                audience_edit_button = ui.button("修正").props("outline")
            audience_summary_row.visible = False
            with ui.column().classes(
                "w-full gap-2 p-3 rounded-xl border border-[rgba(222,146,73,0.14)] bg-white"
            ) as writer_step_card:
                ui.label("STEP4 書き手").classes("text-[11px] font-bold tracking-wide text-amber-700")
                writer_role_select_widget = ui.select(
                    options=get_writer_role_options(initial_type_key),
                    value=get_default_writer_role_label(initial_type_key),
                    label="誰の立場で書くか",
                ).classes("w-full").props("outlined stack-label")
                writer_role_status_label_widget = ui.label(
                    "内容に合う書き手を初期選択しています。"
                ).classes("text-xs text-gray-600 -mt-1 pl-1")
                pronoun_hint_label_widget = ui.label("").classes("text-xs text-gray-600 -mt-1 pl-1")
                with ui.expansion("書き手を細かく指定する（任意）", icon="edit_note").classes("w-full"):
                    writer_role_custom_toggle_widget = ui.checkbox(
                        "自由入力で書き手を指定する",
                        value=False,
                    ).classes("w-full")
                    writer_role_custom_widget = ui.input(
                        "書き手（自由入力）",
                        placeholder="例: 編集担当として語る",
                    ).classes("w-full").props("outlined stack-label")
                    writer_role_custom_widget.visible = False
                with ui.row().classes("w-full justify-end"):
                    writer_done_button = ui.button("確認へ").classes("primary-btn")
            with ui.row().classes(
                "w-full items-center justify-between gap-3 rounded-xl border border-[rgba(82,145,96,0.20)] bg-[rgba(241,252,244,0.92)] px-4 py-3"
            ) as writer_summary_row:
                with ui.column().classes("gap-1"):
                    ui.label("STEP4 書き手").classes("text-[11px] font-bold tracking-wide text-green-700")
                    writer_summary_value_label = ui.label("").classes("text-sm text-[#5D4A41]")
                writer_edit_button = ui.button("修正").props("outline")
            writer_summary_row.visible = False
        else:
            required_article_type_label_widget = ui.label(
                "記事タイプ: 未選択"
            ).classes("text-xs font-medium text-amber-700 bg-amber-50 px-3 py-2 rounded-lg")
            writer_role_select_widget = ui.select(
                options=get_writer_role_options(initial_type_key),
                value=get_default_writer_role_label(initial_type_key),
                label="誰の立場で書くか",
            ).classes("w-full").props("outlined stack-label")
            writer_role_status_label_widget = ui.label(
                "内容に合う書き手を初期選択しています。"
            ).classes("text-xs text-gray-600 -mt-1 pl-1")
            pronoun_hint_label_widget = ui.label("").classes("text-xs text-gray-600 -mt-1 pl-1")
            audience_profile_input_widget = ui.input(
                "主な読者",
                value=default_audience_profile_text,
                placeholder=default_audience_profile_placeholder_text,
            ).classes("w-full").props("outlined stack-label")
            audience_profile_status_label_widget = ui.label(
                "※誰向けに書くかだけ明示してください。"
            ).classes("text-xs text-gray-600")
            with ui.expansion("書き手を細かく指定する（任意）", icon="edit_note").classes("w-full"):
                writer_role_custom_toggle_widget = ui.checkbox(
                    "自由入力で書き手を指定する",
                    value=False,
                ).classes("w-full")
                writer_role_custom_widget = ui.input(
                    "書き手（自由入力）",
                    placeholder="例: 編集担当として語る",
                ).classes("w-full").props("outlined stack-label")
                writer_role_custom_widget.visible = False
    return {
        "required_input_summary_label": required_input_summary_label_widget,
        "required_article_type_label": required_article_type_label_widget,
        "writer_role_select": writer_role_select_widget,
        "writer_role_status_label": writer_role_status_label_widget,
        "pronoun_hint_label": pronoun_hint_label_widget,
        "audience_profile_input": audience_profile_input_widget,
        "audience_profile_status_label": audience_profile_status_label_widget,
        "writer_role_custom_toggle": writer_role_custom_toggle_widget,
        "writer_role_custom": writer_role_custom_widget,
        "audience_step_card": audience_step_card,
        "writer_step_card": writer_step_card,
        "audience_summary_row": audience_summary_row,
        "writer_summary_row": writer_summary_row,
        "audience_summary_value_label": audience_summary_value_label,
        "writer_summary_value_label": writer_summary_value_label,
        "audience_next_button": audience_next_button,
        "writer_done_button": writer_done_button,
        "audience_edit_button": audience_edit_button,
        "writer_edit_button": writer_edit_button,
    }


def render_journey_flow_sections(
    *,
    current_mainline_ui_mode: str,
    journey_purpose_labels: Mapping[str, str],
    initial_journey_target_options: Mapping[str, str],
    journey_compare_axis_options: Mapping[str, str],
    journey_compare_goal_labels: Mapping[str, str],
    journey_outline_action_style: str,
    required_input_fields_renderer: Callable[..., Mapping[str, Any]],
) -> dict[str, Any]:
    required_input_widgets: Mapping[str, Any] = {}
    with ui.column().classes("w-full gap-3 mb-2") as journey_flow_container:
        with ui.card().classes("w-full p-4 gap-3 journey-stage-card journey-stage-card-active") as journey_direction_card:
            ui.label("記事の向き先").classes("text-sm font-semibold text-gray-700")
            ui.label("出し方と書く内容をここでそろえます。").classes("text-xs text-gray-600")
            with ui.column().classes(
                "w-full gap-2 p-3 rounded-xl border border-[rgba(222,146,73,0.20)] bg-[rgba(255,248,242,0.90)]"
            ) as journey_purpose_step_card:
                ui.label("STEP1 出し方").classes("text-[11px] font-bold tracking-wide text-amber-700")
                journey_purpose = ui.select(
                    options=list(journey_purpose_labels.values()),
                    value=journey_purpose_labels["explain"],
                    label="どこに出すか",
                ).classes("w-full").props("outlined stack-label")
                ui.label("読者にどう届く記事かを決めます。").classes("text-xs text-gray-600")
                with ui.row().classes("w-full justify-end"):
                    journey_purpose_next_button = ui.button("次へ").classes("primary-btn")
            with ui.row().classes(
                "w-full items-center justify-between gap-3 rounded-xl border border-[rgba(82,145,96,0.20)] bg-[rgba(241,252,244,0.92)] px-4 py-3"
            ) as journey_purpose_summary_row:
                with ui.column().classes("gap-1"):
                    ui.label("STEP1 出し方").classes("text-[11px] font-bold tracking-wide text-green-700")
                    journey_purpose_summary_value = ui.label("").classes("text-sm text-[#5D4A41]")
                journey_purpose_edit_button = ui.button("修正").props("outline")
            journey_purpose_summary_row.visible = False
            with ui.column().classes(
                "w-full gap-2 p-3 rounded-xl border border-[rgba(222,146,73,0.14)] bg-white"
            ) as journey_target_step_card:
                ui.label("STEP2 内容").classes("text-[11px] font-bold tracking-wide text-amber-700")
                journey_target_options = list(initial_journey_target_options.values())
                journey_target = ui.select(
                    options=journey_target_options,
                    value=journey_target_options[0],
                    label="何を書くか",
                ).classes("w-full").props("outlined stack-label")
                journey_target_hint = ui.label("上の選択に合わせて候補を絞っています。").classes("text-xs text-gray-600")
                with ui.row().classes("w-full justify-end"):
                    journey_target_next_button = ui.button("次へ").classes("primary-btn")
            with ui.row().classes(
                "w-full items-center justify-between gap-3 rounded-xl border border-[rgba(82,145,96,0.20)] bg-[rgba(241,252,244,0.92)] px-4 py-3"
            ) as journey_target_summary_row:
                with ui.column().classes("gap-1"):
                    ui.label("STEP2 内容").classes("text-[11px] font-bold tracking-wide text-green-700")
                    journey_target_summary_value = ui.label("").classes("text-sm text-[#5D4A41]")
                journey_target_edit_button = ui.button("修正").props("outline")
            journey_target_summary_row.visible = False
            if current_mainline_ui_mode == "journey":
                required_input_widgets = required_input_fields_renderer(in_wizard=True)
        with ui.card().classes("w-full p-4 gap-3 journey-stage-card journey-stage-card-active") as journey_step3_card:
            ui.label("比較の条件").classes("text-sm font-semibold text-gray-700")
            journey_detail_hint = ui.label("比較レビューのときだけ、比較の軸を補います。").classes("text-xs text-gray-600")
            with ui.column().classes("w-full gap-3") as compare_detail_container:
                with ui.row().classes("w-full gap-3"):
                    comparison_axis_checks: dict[str, Any] = {}
                    with ui.column().classes("gap-1"):
                        for axis_key, axis_label in journey_compare_axis_options.items():
                            comparison_axis_checks[axis_key] = ui.checkbox(axis_label, value=(axis_key == "overall"))
                custom_compare_axis_input = ui.input(
                    "比較軸を補足する（任意）",
                    placeholder="例: 導入しやすさ",
                ).classes("w-full").props("outlined stack-label")
                compare_goal_select = ui.select(
                    options=list(journey_compare_goal_labels.values()),
                    value=journey_compare_goal_labels["fit_explain"],
                    label="比較のゴール",
                ).classes("w-full").props("outlined stack-label")
        with ui.card().classes("w-full p-4 gap-3").style(
            "border: 1px solid rgba(72,58,50,0.16); "
            "background: linear-gradient(180deg, #FFFCFA 0%, #FFF6F1 100%); "
            "box-shadow: 0 10px 24px rgba(42,31,26,0.08);"
        ) as journey_step4_card:
            with ui.row().classes("w-full items-start justify-between gap-3"):
                with ui.column().classes("gap-1"):
                    ui.label("不足チェック").classes("text-sm font-semibold text-gray-700")
                    journey_confirm_action_hint = ui.label(
                        "不足や確認結果だけを表示します。生成は下の明示ボタンから始めます。"
                    ).classes("text-xs text-gray-700")
                journey_confirm_badge = ui.label("未確認").classes(
                    "text-xs font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full whitespace-nowrap"
                )
            journey_confirm_summary = ui.markdown("選択内容をまとめます。").classes("text-sm text-gray-700")
            journey_confirm_source_fit = ui.label("材料のそろい具合は、まだ確認していません。").classes("text-xs text-gray-600")
            journey_confirm_grounding = ui.label("記事に必要な根拠は、まだ確認していません。").classes("text-xs text-gray-600")
            journey_confirm_missing = ui.markdown("").classes("text-xs text-amber-700")
            journey_confirm_status = ui.label(
                "まだ未確認です。「内容を確認」で不足だけを確認できます。"
            ).classes("text-xs text-gray-600")
            with ui.row().classes("w-full justify-start gap-2"):
                journey_preview_button = ui.button("内容を確認").props("outline").style(journey_outline_action_style)
                journey_confirm_button = ui.button("内容を確認").classes("primary-btn")
            with ui.column().classes("w-full gap-2 mt-2") as interview_followup_container:
                interview_followup_container.visible = False
                with ui.card().classes("w-full p-3 narrow-support-card").style(
                    "border: 1px solid rgba(72,58,50,0.10); background: #FFFCFA;"
                ):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("quiz", size="sm").classes("text-orange-600")
                        ui.label("確認が必要な項目").classes("text-sm font-semibold text-gray-700")
                    interview_followup_note = ui.label(
                        "不足情報があるときだけ、必要な確認項目を表示します。"
                    ).classes("text-xs text-gray-600")
                    interview_followup_status = ui.label("").classes("text-xs text-gray-600")
                    interview_generate_button = ui.button(
                        "確認項目を表示",
                        icon="edit_note",
                    ).props("outline").classes("primary-btn mb-1")
                    interview_questions_container = ui.column().classes("w-full gap-3").style(
                        "max-height: 320px; overflow-y: auto; padding-right: 4px;"
                    )

    return {
        "journey_flow_container": journey_flow_container,
        "journey_direction_card": journey_direction_card,
        "journey_purpose_step_card": journey_purpose_step_card,
        "journey_target_step_card": journey_target_step_card,
        "journey_purpose_summary_row": journey_purpose_summary_row,
        "journey_target_summary_row": journey_target_summary_row,
        "journey_purpose_summary_value": journey_purpose_summary_value,
        "journey_target_summary_value": journey_target_summary_value,
        "journey_purpose_next_button": journey_purpose_next_button,
        "journey_target_next_button": journey_target_next_button,
        "journey_purpose_edit_button": journey_purpose_edit_button,
        "journey_target_edit_button": journey_target_edit_button,
        "journey_purpose": journey_purpose,
        "journey_target": journey_target,
        "journey_target_hint": journey_target_hint,
        "journey_step3_card": journey_step3_card,
        "journey_detail_hint": journey_detail_hint,
        "compare_detail_container": compare_detail_container,
        "comparison_axis_checks": comparison_axis_checks,
        "custom_compare_axis_input": custom_compare_axis_input,
        "compare_goal_select": compare_goal_select,
        "journey_step4_card": journey_step4_card,
        "journey_confirm_action_hint": journey_confirm_action_hint,
        "journey_confirm_badge": journey_confirm_badge,
        "journey_confirm_summary": journey_confirm_summary,
        "journey_confirm_source_fit": journey_confirm_source_fit,
        "journey_confirm_grounding": journey_confirm_grounding,
        "journey_confirm_missing": journey_confirm_missing,
        "journey_confirm_status": journey_confirm_status,
        "journey_preview_button": journey_preview_button,
        "journey_confirm_button": journey_confirm_button,
        "interview_followup_container": interview_followup_container,
        "interview_followup_note": interview_followup_note,
        "interview_followup_status": interview_followup_status,
        "interview_generate_button": interview_generate_button,
        "interview_questions_container": interview_questions_container,
        "required_input_widgets": dict(required_input_widgets),
    }


def render_result_output_sections(
    *,
    preview_placeholder: str,
    render_between_preview_and_details: Callable[[], None] | None = None,
) -> dict[str, Any]:
    with ui.column().classes("output-stage-shell") as output_stage_shell:
        ui.html('<div id="generation-result-anchor"></div>', sanitize=False)
        with ui.card().classes("output-card p-6 w-full fade-in step-card-3"):
            with ui.row().classes("items-center gap-2 mb-1"):
                step3_badge = ui.label("生成結果").classes(
                    "text-xs font-bold bg-gray-100 text-gray-400 px-2 py-0.5 rounded tracking-widest"
                )
                ui.label("生成結果").classes("section-title m-0")
            ui.separator()
            with ui.column().classes("generated-preview-shell"):
                with ui.row().classes("generated-preview-header"):
                    ui.label("記事プレビュー").classes("generated-chip")
                    stats_label = ui.label("").classes("generated-stats")
                with ui.column().classes("generated-preview-card"):
                    preview = ui.markdown(preview_placeholder).classes(
                        "article-preview article-preview-placeholder w-full"
                    )
                copy_note_format_button = ui.button("記事形式でコピー", icon="content_copy").classes(
                    "primary-btn w-full"
                )

            ui.separator()
            with ui.column().classes("w-full generated-sns-panel gap-2"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label("SNS用文章").classes("generated-chip")
                    copy_linkedin_short_button = ui.button(
                        "SNS用文章をコピー",
                        icon="content_copy",
                    ).classes("primary-btn")
                linkedin_short_area = ui.textarea("SNS投稿用テキスト", value="").props(
                    "readonly"
                ).classes("w-full generated-readonly")

            if render_between_preview_and_details is not None:
                render_between_preview_and_details()

            ui.separator()
            with ui.expansion("生成結果の詳細", icon="expand_more").classes(
                "w-full generated-output-expansion"
            ):
                ui.label("ここから下は生成済みの各出力です。必要なものだけ開いて使います。").classes(
                    "section-muted-note mb-2"
                )
                note_body_text = ui.textarea("本文（リード+本文+参考資料）", value="").props(
                    "readonly"
                ).classes("w-full generated-readonly")
                copy_markdown_button = ui.button("Markdownでコピー", icon="code").props("flat")

                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-grow"):
                        title_area = ui.textarea("タイトル", value="").props("readonly").classes(
                            "w-full generated-readonly"
                        )
                        copy_title_button = ui.button("タイトルをコピー").props("flat dense")
                    with ui.column().classes("flex-grow"):
                        hashtags_area = ui.textarea("ハッシュタグ", value="").props(
                            "readonly"
                        ).classes("w-full generated-readonly")
                        copy_hashtags_button = ui.button("ハッシュタグをコピー").props("flat dense")

                with ui.expansion("個別セクション", icon="unfold_more").classes(
                    "w-full generated-output-expansion"
                ):
                    lead_area = ui.textarea("リード", value="").props("readonly").classes(
                        "w-full generated-readonly"
                    )
                    copy_lead_button = ui.button("リードをコピー").props("flat dense")

                    body_area = ui.textarea("本文", value="").props("readonly").classes(
                        "w-full generated-readonly"
                    )
                    copy_body_button = ui.button("本文をコピー").props("flat dense")

                    references_area = ui.textarea("参考資料", value="").props("readonly").classes(
                        "w-full generated-readonly"
                    )
                    copy_references_button = ui.button("参考資料をコピー").props("flat dense")

                    full_text_area = ui.textarea("全文（タイトル含む）", value="").props(
                        "readonly"
                    ).classes("w-full generated-readonly")
                    copy_full_text_button = ui.button("全文をコピー").props("flat dense")

                with ui.expansion("SNS互換出力", icon="short_text").classes(
                    "w-full generated-output-expansion"
                ):
                    linkedin_area = ui.textarea("SNS互換テキスト", value="").props(
                        "readonly"
                    ).classes("w-full generated-readonly")
                    copy_linkedin_button = ui.button(
                        "互換テキストをコピー",
                        icon="content_copy",
                    ).props("flat")

        ui.separator()
        quality_summary_card = ui.column().classes("w-full quality-summary-card")
        quality_summary_card.visible = False
        quality_summary_row_widgets: list[dict[str, Any]] = []
        with quality_summary_card:
            with ui.row().classes("quality-summary-header"):
                quality_summary_badge = ui.label("").classes("quality-summary-badge")
                quality_summary_title = ui.label("").classes("quality-summary-title")
            quality_summary_note = ui.label("").classes("quality-summary-note")
            for _ in range(4):
                row = ui.row().classes("quality-summary-row")
                row.visible = False
                with row:
                    ui.icon("fact_check", size="sm").classes("text-[#8A3F18] mt-0.5")
                    with ui.column().classes("quality-summary-row-copy"):
                        title = ui.label("").classes("quality-summary-row-title")
                        detail = ui.label("").classes("quality-summary-row-detail")
                        codes = ui.label("").classes("quality-summary-row-codes")
                quality_summary_row_widgets.append(
                    {
                        "row": row,
                        "title": title,
                        "detail": detail,
                        "codes": codes,
                    }
                )

        review_container = ui.column().classes("w-full quality-hint-card")
        review_container.visible = False
        with review_container:
            with ui.row().classes("items-center gap-1 mb-1"):
                ui.icon("tips_and_updates", size="sm").classes("text-orange-600")
                ui.label("読みやすさのヒント").classes("quality-hint-title")
            review_row_kousei = ui.row().classes("items-center gap-2")
            review_row_kousei.visible = False
            with review_row_kousei:
                ui.label("構成").classes("quality-hint-chip")
                review_kousei_label = ui.label("").classes("quality-hint-text")
            review_row_buntai = ui.row().classes("items-center gap-2")
            review_row_buntai.visible = False
            with review_row_buntai:
                ui.label("文体").classes("quality-hint-chip")
                review_buntai_label = ui.label("").classes("quality-hint-text")
            review_row_konkyo = ui.row().classes("items-center gap-2")
            review_row_konkyo.visible = False
            with review_row_konkyo:
                ui.label("根拠").classes("quality-hint-chip")
                review_konkyo_label = ui.label("").classes("quality-hint-text")

    output_stage_shell.visible = False
    return {
        "output_stage_shell": output_stage_shell,
        "step3_badge": step3_badge,
        "stats_label": stats_label,
        "preview": preview,
        "note_body_text": note_body_text,
        "title_area": title_area,
        "hashtags_area": hashtags_area,
        "lead_area": lead_area,
        "body_area": body_area,
        "references_area": references_area,
        "full_text_area": full_text_area,
        "linkedin_area": linkedin_area,
        "linkedin_short_area": linkedin_short_area,
        "copy_note_format_button": copy_note_format_button,
        "copy_markdown_button": copy_markdown_button,
        "copy_title_button": copy_title_button,
        "copy_hashtags_button": copy_hashtags_button,
        "copy_lead_button": copy_lead_button,
        "copy_body_button": copy_body_button,
        "copy_references_button": copy_references_button,
        "copy_full_text_button": copy_full_text_button,
        "copy_linkedin_button": copy_linkedin_button,
        "copy_linkedin_short_button": copy_linkedin_short_button,
        "quality_summary_card": quality_summary_card,
        "quality_summary_badge": quality_summary_badge,
        "quality_summary_title": quality_summary_title,
        "quality_summary_note": quality_summary_note,
        "quality_summary_row_widgets": quality_summary_row_widgets,
        "review_container": review_container,
        "review_row_kousei": review_row_kousei,
        "review_kousei_label": review_kousei_label,
        "review_row_buntai": review_row_buntai,
        "review_buntai_label": review_buntai_label,
        "review_row_konkyo": review_row_konkyo,
        "review_konkyo_label": review_konkyo_label,
    }
