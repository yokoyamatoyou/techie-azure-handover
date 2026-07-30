from note.note_writer_app_subviews import (
    BASE_TEMPLATE_LABELS,
    EVIDENCE_LABELS,
    FOCUS_DEFAULT_LABELS,
    LEVEL_LABELS,
    build_copy_to_clipboard_script,
    build_custom_genre_meta_summary,
    build_custom_genre_prompt_preview,
    build_generated_image_variant_cards,
    build_scroll_to_anchor_script,
    open_custom_genre_delete_dialog_with_actions,
    open_custom_genre_edit_dialog_with_actions,
    privacy_blur_targets_selected,
    resolve_privacy_option_key,
)


def test_custom_genre_metadata_option_labels_keep_current_order() -> None:
    assert list(BASE_TEMPLATE_LABELS.values()) == ["branding", "ai", "announcement", "case_study"]
    assert list(FOCUS_DEFAULT_LABELS.values()) == ["analysis", "explanation", "experience"]
    assert list(LEVEL_LABELS.values()) == ["low", "med", "high"]
    assert list(EVIDENCE_LABELS.values()) == ["strict", "normal"]


def test_build_custom_genre_prompt_preview_keeps_existing_ellipsis_behavior() -> None:
    assert build_custom_genre_prompt_preview("短い説明") == "短い説明..."


def test_build_custom_genre_meta_summary_formats_expected_line() -> None:
    summary = build_custom_genre_meta_summary(
        {
            "base_template": "branding",
            "focus_default": "analysis",
            "empathy_level": "med",
            "humanity_level": "high",
            "evidence_mode": "strict",
        }
    )

    assert summary == "base=branding / focus=analysis / empathy=med / humanity=high / evidence=strict"


def test_build_generated_image_variant_cards_uses_legacy_generated_images() -> None:
    cards = build_generated_image_variant_cards(
        generated_image_variants=[],
        generated_images=["/tmp/text.png", "/tmp/plain.png"],
    )

    assert [card.label for card in cards] == ["文字入り画像", "文字なし画像"]
    assert [card.path for card in cards] == ["/tmp/text.png", "/tmp/plain.png"]
    assert all(card.status == "success" for card in cards)


def test_build_generated_image_variant_cards_keeps_variant_payload_fields() -> None:
    cards = build_generated_image_variant_cards(
        generated_image_variants=[
            {
                "key": "plain",
                "label": "文字なし画像",
                "status": "failed",
                "error": "timeout",
                "retry_count": 2,
            }
        ],
        generated_images=["/tmp/ignored.png"],
    )

    assert len(cards) == 1
    assert cards[0].key == "plain"
    assert cards[0].label == "文字なし画像"
    assert cards[0].status == "failed"
    assert cards[0].error == "timeout"
    assert cards[0].retry_count == 2
    assert cards[0].path == ""


def test_resolve_privacy_option_key_falls_back_when_label_missing() -> None:
    assert resolve_privacy_option_key(
        options={"light": "弱", "medium": "標準", "strong": "強"},
        selected_label="未設定",
        fallback="medium",
    ) == "medium"


def test_privacy_blur_targets_selected_requires_at_least_one_target() -> None:
    assert not privacy_blur_targets_selected(
        blur_faces=False,
        blur_license_plates=False,
        blur_qr_codes=False,
        blur_personal_text=False,
    )
    assert privacy_blur_targets_selected(
        blur_faces=False,
        blur_license_plates=True,
        blur_qr_codes=False,
        blur_personal_text=False,
    )


def test_build_scroll_to_anchor_script_targets_expected_anchor() -> None:
    script = build_scroll_to_anchor_script()

    assert "generation-result-anchor" in script
    assert "scrollIntoView" in script


def test_build_copy_to_clipboard_script_serializes_text_for_javascript() -> None:
    script = build_copy_to_clipboard_script('改行\n"quote"')

    assert script == 'navigator.clipboard.writeText("\\u6539\\u884c\\n\\"quote\\"")'


def test_open_custom_genre_edit_dialog_with_actions_wires_save_callbacks(monkeypatch) -> None:
    import note.note_writer_app_subviews as subviews

    captured: dict[str, object] = {}

    def fake_open_custom_genre_edit_dialog(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(subviews, "open_custom_genre_edit_dialog", fake_open_custom_genre_edit_dialog)
    calls: list[tuple[str, object]] = []

    open_custom_genre_edit_dialog_with_actions(
        genre={"key": "custom_1"},
        normalize_meta=lambda meta: dict(meta or {}),
        base_template_options=["branding"],
        focus_default_options=["trust"],
        level_options=["medium"],
        evidence_options=["strict"],
        update_genre=lambda key, label, prompt, meta: calls.append(
            ("update", (key, label, prompt, dict(meta)))
        ),
        notify=lambda message, **kwargs: calls.append(("notify", (message, kwargs))),
        log_usage=lambda feature, action, **kwargs: calls.append(("log", (feature, action, kwargs))),
        refresh_custom_genres=lambda: calls.append(("refresh_genres", None)),
        refresh_article_type_select=lambda: calls.append(("refresh_article_type", None)),
    )

    payload = subviews.CustomGenreEditPayload(
        key="custom_1",
        label="採用",
        prompt="prompt",
        meta={"base_template": "branding"},
    )
    captured["on_save"](payload)

    assert calls[0][0] == "log"
    assert ("update", ("custom_1", "採用", "prompt", {"base_template": "branding"})) in calls
    assert ("refresh_genres", None) in calls
    assert ("refresh_article_type", None) in calls


def test_open_custom_genre_delete_dialog_with_actions_wires_delete_callbacks(monkeypatch) -> None:
    import note.note_writer_app_subviews as subviews

    captured: dict[str, object] = {}

    def fake_open_custom_genre_delete_dialog(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(subviews, "open_custom_genre_delete_dialog", fake_open_custom_genre_delete_dialog)
    calls: list[tuple[str, object]] = []

    open_custom_genre_delete_dialog_with_actions(
        genre={"key": "custom_1"},
        delete_genre=lambda key: calls.append(("delete", key)),
        notify=lambda message, **kwargs: calls.append(("notify", (message, kwargs))),
        log_usage=lambda feature, action, **kwargs: calls.append(("log", (feature, action, kwargs))),
        refresh_custom_genres=lambda: calls.append(("refresh_genres", None)),
        refresh_article_type_select=lambda: calls.append(("refresh_article_type", None)),
    )
    captured["on_confirm_delete"]("custom_1")

    assert ("delete", "custom_1") in calls
    assert ("refresh_genres", None) in calls
    assert ("refresh_article_type", None) in calls
