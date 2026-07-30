from note.note_writer_interview_question_workflow import (
    build_current_mainline_generation_selection_payload,
    build_confirm_preview_request_kwargs,
    build_interview_context_signature,
    build_question_policy_request_kwargs,
    filter_current_mainline_question_items_for_ui,
    label_for_question_policy_reason,
    prepare_current_mainline_generation_request_inputs,
    prepare_current_mainline_interview_state_for_generation,
    project_missing_required_fields,
)


def test_project_missing_required_fields_filters_blank_values() -> None:
    assert project_missing_required_fields(
        {"missing_required_fields": ["speaker_profile", "", None, "audience_profile"]}
    ) == ["speaker_profile", "audience_profile"]


def test_label_for_question_policy_reason_uses_known_label_and_falls_back() -> None:
    assert label_for_question_policy_reason("json_parse_error") == "JSON解析失敗"
    assert label_for_question_policy_reason("custom_reason") == "custom_reason"


def test_build_interview_context_signature_is_stable_and_prompt_sensitive() -> None:
    base = build_interview_context_signature(
        source_values=["https://b.example", " https://a.example "],
        article_type_key="branding",
        content_goal_key="lead",
        user_prompt_text="採用向け",
    )
    reordered = build_interview_context_signature(
        source_values=["https://a.example", "https://b.example"],
        article_type_key="branding",
        content_goal_key="lead",
        user_prompt_text="採用向け",
    )
    changed = build_interview_context_signature(
        source_values=["https://a.example", "https://b.example"],
        article_type_key="branding",
        content_goal_key="lead",
        user_prompt_text="販促向け",
    )

    assert base == reordered
    assert base != changed


def test_build_question_policy_request_kwargs_preserves_policy_contract() -> None:
    kwargs = build_question_policy_request_kwargs(
        source_values=["https://example.com"],
        source_documents=[{"title": "source"}],
        article_type="branding",
        selection={"ui_journey": {"purpose_key": "brand"}, "comparison_axes": ["price"]},
        user_prompt_text="会社紹介を書いて",
        content_goal_key="trust",
        writing_focus_key="story",
        length_mode_key="short",
        tone_profile_key="serious",
        perspective_key="first_person",
        allow_experience=True,
        interview_answers={"target": "採用候補者"},
        speaker_profile_input="広報担当",
        audience_profile_input="採用候補者",
        core_message_input="現場の雰囲気",
        self_reference_policy_key="company",
        branding_subtype_key="company_intro",
        branding_focus_key="culture",
        pattern_key="standard",
        strict_saas_mode="medium",
        source_mode_key="grounded",
    )

    assert kwargs["source_values"] == ["https://example.com"]
    assert kwargs["source_documents"] == [{"title": "source"}]
    assert kwargs["ui_journey"] == {"purpose_key": "brand"}
    assert kwargs["comparison_axes"] == ["price"]
    assert kwargs["structure_key"] == "auto"
    assert kwargs["source_mode"] == "grounded"
    assert kwargs["interview_answers"] == {"target": "採用候補者"}


def test_build_confirm_preview_request_kwargs_adds_preview_only_fields() -> None:
    kwargs = build_confirm_preview_request_kwargs(
        source_values=[],
        source_documents=[],
        article_type="explanatory_article",
        selection={},
        user_prompt_text="説明記事",
        content_goal_key="auto",
        writing_focus_key="auto",
        length_mode_key="adaptive",
        tone_profile_key="auto",
        perspective_key="auto",
        allow_experience=False,
        interview_answers={},
        speaker_profile_input="",
        audience_profile_input="一般読者",
        core_message_input="",
        self_reference_policy_key="auto",
        branding_subtype_key="",
        branding_focus_key="",
        pattern_key="",
        system_hint_items=["hint"],
        retry_memo=["retry"],
        strict_saas_mode="medium",
        source_mode_key="web",
    )

    assert kwargs["system_hint_items"] == ["hint"]
    assert kwargs["retry_memo"] == ["retry"]
    assert kwargs["structure_key"] == "auto"
    assert kwargs["source_mode"] == "web"


def test_prepare_current_mainline_generation_request_inputs_filters_empty_answers() -> None:
    prepared = prepare_current_mainline_generation_request_inputs(
        interview_answers={"target": "採用候補者", "message": "", "empty": None},
        speaker_profile_input="広報担当",
        prompt_raw="  会社紹介を書いて  ",
    )

    assert prepared["interview_answers"] == {"target": "採用候補者"}
    assert prepared["interview_answer_keys"] == ["target"]
    assert prepared["interview_answer_count"] == 1
    assert prepared["speaker_profile_input"] == "広報担当"
    assert prepared["prompt_raw"] == "会社紹介を書いて"
    assert prepared["retry_memo"] == []


def test_prepare_current_mainline_generation_request_inputs_ignores_theme_like_speaker() -> None:
    prepared = prepare_current_mainline_generation_request_inputs(
        interview_answers={},
        speaker_profile_input="採用広報の記事テーマ",
        prompt_raw="テーマ",
    )

    assert prepared["speaker_profile_input"] == ""
    assert prepared["writer_role_ignored_theme_like"] is True


def test_prepare_current_mainline_interview_state_resets_stale_context() -> None:
    state = prepare_current_mainline_interview_state_for_generation(
        interview_answers={"target": "採用候補者"},
        interview_questions_loaded=True,
        stored_context_signature="old",
        current_context_signature="new",
    )

    assert state["reset_required"] is True
    assert state["interview_questions_loaded"] is False
    assert state["stored_context_signature"] == ""
    assert state["answered_count"] == 0


def test_prepare_current_mainline_interview_state_counts_loaded_answers() -> None:
    state = prepare_current_mainline_interview_state_for_generation(
        interview_answers={"target": "採用候補者", "message": "", "other": "x"},
        interview_questions_loaded=True,
        stored_context_signature="same",
        current_context_signature="same",
    )

    assert state["reset_required"] is False
    assert state["answered_count"] == 1
    assert state["notify_unanswered"] is False


def test_filter_current_mainline_question_items_for_ui_keeps_allowed_fields() -> None:
    filtered = filter_current_mainline_question_items_for_ui(
        [
            {"field": "perspective_mode", "label": "視点"},
            {"field": "target", "label": "読者"},
            {"field": "allow_experience", "label": "体験"},
            {"field": "", "label": "empty"},
        ]
    )

    assert filtered == [
        {"field": "perspective_mode", "label": "視点"},
        {"field": "allow_experience", "label": "体験"},
    ]


def test_build_current_mainline_generation_selection_payload_overwrites_runtime_fields() -> None:
    payload = build_current_mainline_generation_selection_payload(
        base_selections={"article_type": "old", "kept": "value"},
        article_type_key="branding",
        selected_article_type_label="ブランディング",
        content_goal_key="trust",
        writing_focus_key="story",
        structure_key="auto",
        length_mode_key="short",
        tone_profile_key="serious",
        perspective_key="first_person",
        allow_experience=True,
        strict_saas_mode="strict",
    )

    assert payload["kept"] == "value"
    assert payload["article_type"] == "branding"
    assert payload["selected_label"] == "ブランディング"
    assert payload["content_goal"] == "trust"
    assert payload["allow_experience"] is True
    assert payload["strict_saas_mode"] == "strict"


def test_build_current_mainline_generation_selection_payload_uses_defaults() -> None:
    payload = build_current_mainline_generation_selection_payload(
        base_selections=None,
        article_type_key="",
        selected_article_type_label="",
        content_goal_key="",
        writing_focus_key="",
        structure_key="",
        length_mode_key="",
        tone_profile_key="",
        perspective_key="",
        allow_experience=False,
        strict_saas_mode="",
    )

    assert payload["content_goal"] == "auto"
    assert payload["writing_focus"] == "auto"
    assert payload["structure"] == "auto"
    assert payload["length_mode"] == "adaptive"
    assert payload["tone_profile"] == "auto"
    assert payload["perspective"] == "auto"
    assert payload["strict_saas_mode"] == "medium"
