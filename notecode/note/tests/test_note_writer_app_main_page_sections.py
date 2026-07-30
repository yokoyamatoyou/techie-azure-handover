import inspect

from note.note_writer_app_main_page_sections import (
    apply_generation_progress_widgets,
    build_article_type_descriptions,
    build_source_mode_choice_card_copy,
    refresh_core_message_input_widgets,
    refresh_generation_step_indicators,
    refresh_interview_followup_widgets,
    refresh_journey_confirmation_cta_widgets,
    refresh_journey_confirm_status_widget,
    refresh_journey_direction_wizard_widgets,
    refresh_profile_control_widgets,
    refresh_required_input_status_widgets,
    refresh_required_input_wizard_widgets,
    refresh_writer_role_select_options_widget,
    refresh_writer_role_status_widgets,
    refresh_source_mode_choice_card_widgets,
    refresh_source_mode_status_widgets,
    render_result_output_sections,
)


def test_article_type_descriptions_keep_current_labels() -> None:
    descriptions = build_article_type_descriptions()

    assert descriptions["解説"] == "専門情報を読者が行動できる形に翻訳する。"
    assert descriptions["日常"] == "日々の出来事と学びを短く自然に共有する。"
    assert descriptions["ブランド"] == "価値訴求を読者視点で具体化する。"
    assert descriptions["お知らせ"] == "変更点を簡潔かつ正確に伝える。"
    assert descriptions["事例"] == "再現可能な実行手順と成果を示す。"
    assert descriptions["業界分析"] == "比較軸と根拠を明示して分析する。"
    assert descriptions["比較レビュー"] == "候補の違いを評価軸で整理する。"


def test_source_mode_choice_card_copy_keeps_visible_surface() -> None:
    cards = build_source_mode_choice_card_copy()

    assert list(cards) == ["grounded", "web", "prompt_only"]
    assert cards["grounded"]["title"] == "資料あり"
    assert "URL / PDF / 画像 / テキスト" in cards["grounded"]["summary"]
    assert cards["web"]["title"] == "お任せ"
    assert "公開済み3件以上" in cards["web"]["detail"]
    assert cards["prompt_only"]["title"] == "プロンプトのみ"
    assert "事実ソースにはしません" in cards["prompt_only"]["detail"]


def test_result_output_section_builder_keeps_phase06a_callback_boundary() -> None:
    signature = inspect.signature(render_result_output_sections)

    assert list(signature.parameters) == [
        "preview_placeholder",
        "render_between_preview_and_details",
    ]
    assert signature.parameters["render_between_preview_and_details"].default is None


def test_result_output_section_source_shows_sns_area() -> None:
    source = inspect.getsource(render_result_output_sections)

    assert "SNS用文章" in source
    assert "SNS投稿用テキスト" in source
    assert 'with ui.expansion("SNS用文章"' not in source
    assert "SNS互換出力" in source
    assert "LinkedIn用出力" not in source
    assert "LinkedIn投稿用テキスト" not in source


class _FakeBadge:
    def __init__(self, value: str = "") -> None:
        self.value = value
        self.text = ""
        self.class_calls: list[dict[str, str]] = []
        self.update_count = 0

    def classes(self, *, remove: str = "", add: str = "") -> "_FakeBadge":
        self.class_calls.append({"remove": remove, "add": add})
        return self

    def update(self) -> None:
        self.update_count += 1


class _FakeState:
    def __init__(self, *, sources: list[object] | None = None, busy: bool = False) -> None:
        self.sources = list(sources or [])
        self.busy = busy


def _fake_step_widgets() -> dict[str, _FakeBadge]:
    return {
        "step1_badge": _FakeBadge(),
        "step2_badge": _FakeBadge(),
        "step3_badge": _FakeBadge(),
        "sticky_step1": _FakeBadge(),
        "sticky_step2": _FakeBadge(),
        "sticky_step3": _FakeBadge(),
    }


def test_refresh_generation_step_indicators_marks_input_state() -> None:
    widgets = _fake_step_widgets()
    calls = {"refresh": 0}

    state = refresh_generation_step_indicators(
        state=_FakeState(),
        note_body_text=_FakeBadge(""),
        refresh_output_stage_visibility=lambda: calls.__setitem__("refresh", calls["refresh"] + 1),
        **widgets,
    )

    assert state == "input"
    assert widgets["step1_badge"].text == "← 入力"
    assert widgets["step2_badge"].text == "生成準備"
    assert widgets["step3_badge"].text == "生成結果"
    assert calls["refresh"] == 1


def test_refresh_generation_step_indicators_marks_prepare_state() -> None:
    widgets = _fake_step_widgets()

    state = refresh_generation_step_indicators(
        state=_FakeState(sources=[object()]),
        note_body_text=_FakeBadge(""),
        refresh_output_stage_visibility=lambda: None,
        **widgets,
    )

    assert state == "prepare"
    assert widgets["step1_badge"].text == "✓ 入力"
    assert widgets["step2_badge"].text == "← 生成準備"
    assert widgets["sticky_step1"].text == "✓ 入力"


def test_refresh_generation_step_indicators_marks_result_state() -> None:
    widgets = _fake_step_widgets()

    state = refresh_generation_step_indicators(
        state=_FakeState(),
        note_body_text=_FakeBadge("本文あり"),
        refresh_output_stage_visibility=lambda: None,
        **widgets,
    )

    assert state == "result"
    assert widgets["step1_badge"].text == "✓ 入力"
    assert widgets["step2_badge"].text == "✓ 生成準備"
    assert widgets["step3_badge"].text == "← 生成結果"


def test_apply_generation_progress_widgets_updates_live_draft_stream() -> None:
    status = _FakeBadge()
    progress_bar = _FakeBadge()
    progress_note = _FakeBadge()
    body = _FakeBadge("old")
    lead = _FakeBadge("リード")
    note_body = _FakeBadge("")
    title = _FakeBadge("タイトル")
    preview = _FakeBadge("")
    stats = _FakeBadge("")

    apply_generation_progress_widgets(
        status_label=status,
        generation_progress=progress_bar,
        generation_progress_note=progress_note,
        label_text="本文を生成中...",
        display_percent=42,
        elapsed="（経過3秒）",
        stage="body",
        live_draft_stream_enabled=True,
        progress={"partial_body": "本文"},
        body_area=body,
        lead_area=lead,
        note_body_text=note_body,
        title_area=title,
        preview=preview,
        stats_label=stats,
        sanitize_markdown_preview=lambda text: f"safe:{text}",
    )

    assert status.text == "本文を生成中... 42%"
    assert progress_bar.value == 0.42
    assert progress_note.visible is True
    assert body.value == "本文"
    assert note_body.value == "リード\n\n本文"
    assert preview.content == "safe:タイトル\n\nリード\n\n本文"
    assert stats.text == "記事本文: 7文字"


class _FakeWizardWidget:
    def __init__(self) -> None:
        self.visible = False
        self.text = ""
        self.enabled = False
        self.class_calls: list[dict[str, str]] = []
        self.style_calls: list[str] = []
        self.update_count = 0
        self.clear_count = 0

    def classes(self, *, remove: str = "", add: str = "") -> "_FakeWizardWidget":
        self.class_calls.append({"remove": remove, "add": add})
        return self

    def style(self, value: str) -> "_FakeWizardWidget":
        self.style_calls.append(value)
        return self

    def update(self) -> None:
        self.update_count += 1

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def clear(self) -> None:
        self.clear_count += 1


def test_refresh_required_input_wizard_widgets_applies_explicit_widget_state() -> None:
    widgets = {
        "audience_step_card": _FakeWizardWidget(),
        "writer_step_card": _FakeWizardWidget(),
        "audience_summary_row": _FakeWizardWidget(),
        "writer_summary_row": _FakeWizardWidget(),
        "audience_summary_value_label": _FakeWizardWidget(),
        "writer_summary_value_label": _FakeWizardWidget(),
        "audience_next_button": _FakeWizardWidget(),
        "writer_done_button": _FakeWizardWidget(),
        "required_input_summary_label": _FakeWizardWidget(),
        "journey_step4_card": _FakeWizardWidget(),
    }

    refresh_required_input_wizard_widgets(
        view_state={
            "audience_editor_visible": False,
            "writer_editor_visible": True,
            "audience_summary_visible": True,
            "writer_summary_visible": False,
        },
        focused_step=3,
        article_type_ready=True,
        audience_ready=True,
        writer_ready=True,
        audience_committed=True,
        writer_committed=False,
        audience_profile_text="採用担当者",
        selected_writer_role="広報担当",
        helper_text_builder=lambda step: f"step-{step}",
        **widgets,
    )

    assert widgets["audience_step_card"].visible is False
    assert widgets["writer_step_card"].visible is True
    assert widgets["audience_summary_row"].visible is True
    assert widgets["audience_summary_value_label"].text == "採用担当者"
    assert widgets["writer_summary_value_label"].text == "広報担当"
    assert widgets["audience_next_button"].enabled is False
    assert widgets["writer_done_button"].enabled is True
    assert widgets["required_input_summary_label"].text == "step-3"
    assert widgets["journey_step4_card"].visible is False


def test_refresh_source_mode_choice_card_widgets_updates_visible_and_active_state() -> None:
    cards = {
        "grounded": _FakeWizardWidget(),
        "web": _FakeWizardWidget(),
        "prompt_only": _FakeWizardWidget(),
    }

    refresh_source_mode_choice_card_widgets(
        source_mode_choice_cards=cards,
        available_modes=["grounded", "web"],
        selected_mode_key="web",
    )

    assert cards["grounded"].visible is True
    assert cards["web"].visible is True
    assert cards["prompt_only"].visible is False
    assert cards["grounded"].class_calls[-1]["remove"] == "source-mode-choice-card-active"
    assert cards["web"].class_calls[-1]["add"] == "source-mode-choice-card-active"
    assert cards["prompt_only"].update_count == 1


def test_refresh_source_mode_status_widgets_updates_input_and_omakase_surfaces() -> None:
    widgets = {
        "input_stage_helper_label": _FakeWizardWidget(),
        "source_mode_helper_label": _FakeWizardWidget(),
        "user_prompt": _FakeWizardWidget(),
        "user_prompt_helper_label": _FakeWizardWidget(),
        "announcement_inline_error_label": _FakeWizardWidget(),
        "added_sources_section": _FakeWizardWidget(),
        "source_inputs_section": _FakeWizardWidget(),
        "source_inputs_title_label": _FakeWizardWidget(),
        "source_inputs_helper_label": _FakeWizardWidget(),
        "prompt_input_section": _FakeWizardWidget(),
        "omakase_status_card": _FakeWizardWidget(),
        "omakase_status_title": _FakeWizardWidget(),
        "omakase_status_message": _FakeWizardWidget(),
        "omakase_status_inventory": _FakeWizardWidget(),
        "omakase_status_detail": _FakeWizardWidget(),
    }

    refresh_source_mode_status_widgets(
        input_surface={
            "section_intro_text": "入力説明",
            "source_mode_helper_text": "資料モード",
            "prompt_label": "テーマ",
            "prompt_placeholder": "短く入力",
            "prompt_helper_text": "補足",
            "source_title_text": "資料",
            "source_helper_text": "資料補足",
            "prompt_visible": True,
        },
        omakase_state={
            "visible": True,
            "title": "お任せOK",
            "message": "候補があります",
            "inventory_text": "3件",
            "detail_text": "使えます",
        },
        source_mode_key="grounded",
        has_sources=True,
        input_required_modes={"grounded"},
        announcement_inline_error_text="入力エラー",
        **widgets,
    )

    assert widgets["input_stage_helper_label"].text == "入力説明"
    assert widgets["source_mode_helper_label"].text == "資料モード"
    assert widgets["user_prompt"].label == "テーマ"
    assert widgets["user_prompt"].placeholder == "短く入力"
    assert widgets["announcement_inline_error_label"].visible is True
    assert widgets["added_sources_section"].visible is True
    assert widgets["source_inputs_section"].visible is True
    assert widgets["source_inputs_section"].style_calls[-1] == "order: 2;"
    assert widgets["prompt_input_section"].visible is True
    assert widgets["prompt_input_section"].style_calls[-1] == "order: 4;"
    assert widgets["omakase_status_card"].visible is True
    assert widgets["omakase_status_title"].text == "お任せOK"
    assert widgets["omakase_status_detail"].text == "使えます"


def test_refresh_required_input_status_widgets_updates_labels_and_audience_state() -> None:
    article_label = _FakeWizardWidget()
    audience_label = _FakeWizardWidget()
    summary_label = _FakeWizardWidget()

    refresh_required_input_status_widgets(
        article_type_label="ブランド",
        semantic_label="会社紹介",
        audience_profile_text="採用候補者",
        default_audience_placeholder="例: 採用候補者",
        summary_text="helper",
        required_article_type_label=article_label,
        audience_profile_status_label=audience_label,
        required_input_summary_label=summary_label,
    )

    assert article_label.text == "記事タイプ: ブランド / 会社紹介"
    assert audience_label.text == "読者指定あり。誰向けの記事かが明示されています。"
    assert audience_label.class_calls[-1]["add"] == "text-gray-600"
    assert summary_label.text == "helper"


def test_refresh_journey_direction_wizard_widgets_updates_step_visibility() -> None:
    widgets = {
        "journey_purpose_step_card": _FakeWizardWidget(),
        "journey_purpose_summary_row": _FakeWizardWidget(),
        "journey_purpose_summary_value": _FakeWizardWidget(),
        "journey_purpose_next_button": _FakeWizardWidget(),
        "journey_target_step_card": _FakeWizardWidget(),
        "journey_target_summary_row": _FakeWizardWidget(),
        "journey_target_summary_value": _FakeWizardWidget(),
        "journey_target_next_button": _FakeWizardWidget(),
    }

    refresh_journey_direction_wizard_widgets(
        focused_step=2,
        purpose_ready=True,
        target_ready=True,
        purpose_label="note",
        target_label="採用広報",
        **widgets,
    )

    assert widgets["journey_purpose_step_card"].visible is False
    assert widgets["journey_purpose_summary_row"].visible is True
    assert widgets["journey_purpose_summary_value"].text == "note"
    assert widgets["journey_purpose_next_button"].enabled is False
    assert widgets["journey_target_step_card"].visible is True
    assert widgets["journey_target_summary_row"].visible is False
    assert widgets["journey_target_summary_value"].text == "採用広報"
    assert widgets["journey_target_next_button"].enabled is True


def test_refresh_core_message_input_widgets_updates_visibility_and_copy() -> None:
    input_widget = _FakeWizardWidget()
    helper_label = _FakeWizardWidget()

    refresh_core_message_input_widgets(
        requires_core_message=True,
        placeholder="核メッセージ",
        helper_text="補足",
        core_message_input=input_widget,
        core_message_helper_label=helper_label,
    )

    assert input_widget.visible is True
    assert input_widget.placeholder == "核メッセージ"
    assert helper_label.text == "補足"
    assert input_widget.update_count == 1


def test_refresh_profile_control_widgets_updates_branding_visibility() -> None:
    subtype = _FakeWizardWidget()
    focus = _FakeWizardWidget()
    helper = _FakeWizardWidget()

    refresh_profile_control_widgets(
        type_key="branding",
        semantic_key="company_introduction",
        branding_subtype_select=subtype,
        branding_focus_select=focus,
        branding_profile_helper_label=helper,
    )

    assert subtype.visible is True
    assert focus.visible is True
    assert "ブランド記事では" in helper.text


def test_refresh_writer_role_status_widgets_updates_auto_missing_theme_and_ready_copy() -> None:
    status = _FakeWizardWidget()
    pronoun = _FakeWizardWidget()

    result = refresh_writer_role_status_widgets(
        selected_writer_role="",
        type_key="branding",
        self_reference_policy_key="auto",
        company_intro_auto_mode=True,
        looks_theme_like_writer_role=lambda value: value == "theme",
        predict_pronoun_hint=lambda type_key, selected, policy: f"{type_key}:{selected}:{policy}",
        writer_role_status_label=status,
        pronoun_hint_label=pronoun,
    )
    assert result == "company_intro_auto"
    assert status.text == "話者: 自動（役割語を前面に出さない）"
    assert status.class_calls[-1]["add"] == "text-gray-600"
    assert pronoun.text == "branding::auto"

    result = refresh_writer_role_status_widgets(
        selected_writer_role="",
        type_key="branding",
        self_reference_policy_key="auto",
        company_intro_auto_mode=False,
        looks_theme_like_writer_role=lambda value: value == "theme",
        predict_pronoun_hint=lambda type_key, selected, policy: "",
        writer_role_status_label=status,
        pronoun_hint_label=pronoun,
    )
    assert result == "missing"
    assert status.text == "この内容では、書き手を選んでください。"
    assert status.class_calls[-1]["add"] == "text-red-600"

    result = refresh_writer_role_status_widgets(
        selected_writer_role="theme",
        type_key="branding",
        self_reference_policy_key="auto",
        company_intro_auto_mode=False,
        looks_theme_like_writer_role=lambda value: value == "theme",
        predict_pronoun_hint=lambda type_key, selected, policy: "",
        writer_role_status_label=status,
        pronoun_hint_label=pronoun,
    )
    assert result == "theme_like"
    assert "肩書きだけ" in status.text
    assert status.class_calls[-1]["add"] == "text-red-600"

    result = refresh_writer_role_status_widgets(
        selected_writer_role="広報担当",
        type_key="branding",
        self_reference_policy_key="auto",
        company_intro_auto_mode=False,
        looks_theme_like_writer_role=lambda value: False,
        predict_pronoun_hint=lambda type_key, selected, policy: "",
        writer_role_status_label=status,
        pronoun_hint_label=pronoun,
    )
    assert result == "ready"
    assert status.text == "書き手: 広報担当"
    assert status.class_calls[-1]["add"] == "text-gray-600"


def test_refresh_writer_role_select_options_widget_applies_default_when_needed() -> None:
    select = _FakeWizardWidget()
    select.value = "旧ラベル"
    refresh_state = {"active": False, "expected_value": ""}

    default_label = refresh_writer_role_select_options_widget(
        type_key="branding",
        semantic_key="company_introduction",
        get_writer_role_options=lambda type_key, semantic_key: ["自動", "広報担当"],
        get_default_writer_role_label=lambda type_key, semantic_key: "自動",
        is_article_type_managed_writer_role_label=lambda value: value == "旧ラベル",
        writer_role_user_overridden=False,
        writer_role_select=select,
        writer_role_default_refresh_state=refresh_state,
    )

    assert default_label == "自動"
    assert select.options == ["自動", "広報担当"]
    assert select.value == "自動"
    assert refresh_state["expected_value"] == "自動"
    assert refresh_state["active"] is False
    assert select.update_count == 1


def test_refresh_journey_confirmation_cta_widgets_preserves_nonjourney_generate_button() -> None:
    generate_button = _FakeWizardWidget()
    generate_gate_hint = _FakeWizardWidget()

    refresh_journey_confirmation_cta_widgets(
        ui_mode="classic",
        busy=False,
        confirmation_ready=True,
        cta_state={},
        gate_surface={},
        confirm_button_text="",
        journey_confirm_badge=_FakeWizardWidget(),
        journey_confirm_action_hint=_FakeWizardWidget(),
        journey_preview_button=_FakeWizardWidget(),
        journey_confirm_button=_FakeWizardWidget(),
        generate_button=generate_button,
        generate_gate_hint=generate_gate_hint,
    )

    assert generate_gate_hint.visible is False
    assert generate_gate_hint.text == ""
    assert generate_button.enabled is True
    assert generate_button.text == "記事を生成"


def test_refresh_journey_confirmation_cta_widgets_updates_generate_gate_hint() -> None:
    badge = _FakeWizardWidget()
    action_hint = _FakeWizardWidget()
    preview_button = _FakeWizardWidget()
    confirm_button = _FakeWizardWidget()
    generate_button = _FakeWizardWidget()
    generate_gate_hint = _FakeWizardWidget()

    refresh_journey_confirmation_cta_widgets(
        ui_mode="journey",
        busy=False,
        confirmation_ready=True,
        cta_state={
            "badge_text": "要入力",
            "badge_classes": "bg-amber-100 text-amber-700",
            "card_hint_text": "資料確認が必要です",
            "preview_button_text": "不足を確認",
            "generate_button_text": "この内容で生成を開始",
            "generate_hint_text": "生成できます",
            "generate_hint_classes": "text-green-700",
        },
        gate_surface={"enabled": False, "hint_text": "資料を確認してください", "hint_classes": "text-amber-700"},
        confirm_button_text="内容を確認",
        journey_confirm_badge=badge,
        journey_confirm_action_hint=action_hint,
        journey_preview_button=preview_button,
        journey_confirm_button=confirm_button,
        generate_button=generate_button,
        generate_gate_hint=generate_gate_hint,
    )

    assert badge.text == "要入力"
    assert action_hint.text == "資料確認が必要です"
    assert preview_button.enabled is True
    assert confirm_button.text == "内容を確認"
    assert generate_button.visible is True
    assert generate_button.enabled is False
    assert generate_gate_hint.visible is True
    assert generate_gate_hint.text == "資料を確認してください"
    assert generate_gate_hint.class_calls[-1]["add"] == "text-amber-700"


def test_refresh_interview_followup_widgets_updates_status_and_clears_questions() -> None:
    note = _FakeWizardWidget()
    status = _FakeWizardWidget()
    questions = _FakeWizardWidget()
    container = _FakeWizardWidget()

    refresh_interview_followup_widgets(
        visible=True,
        note_text="不足があります",
        status_text="確認してください",
        tone="amber",
        clear_questions=True,
        interview_followup_note=note,
        interview_followup_status=status,
        interview_questions_container=questions,
        interview_followup_container=container,
    )

    assert note.text == "不足があります"
    assert status.text == "確認してください"
    assert status.class_calls[-1]["add"] == "text-amber-700"
    assert questions.clear_count == 1
    assert container.visible is True


def test_refresh_journey_confirm_status_widget_updates_tone_classes() -> None:
    status = _FakeWizardWidget()

    refresh_journey_confirm_status_widget(
        text="確認済み",
        tone="green",
        journey_confirm_status=status,
    )

    assert status.text == "確認済み"
    assert "bg-green-50" in status.class_calls[-1]["add"]
    assert status.update_count == 1
