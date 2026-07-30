from note.note_writer_app_article_source_mode import (
    FIXED_ARTICLE_TYPE_LABELS,
    SOURCE_MODE_LABELS,
    _build_source_mode_helper_text,
    _build_source_mode_input_surface,
    _get_combined_article_types,
    _get_combined_prompts,
    _resolve_source_mode_selection,
    _source_mode_allows_no_sources,
    _source_mode_options_for_article_type,
)


def test_get_combined_article_types_includes_fixed_article_types() -> None:
    combined = _get_combined_article_types()

    assert combined == FIXED_ARTICLE_TYPE_LABELS
    assert combined["daily_story"] == "日常のできごと"


def test_get_combined_article_types_preserves_existing_ordering() -> None:
    assert list(_get_combined_article_types()) == [
        "explanatory_article",
        "daily_story",
        "branding",
        "announcement",
        "case_study",
        "industry_analysis",
        "comparative_review",
    ]


def test_get_combined_prompts_returns_expected_keys_labels_and_ordering() -> None:
    combined = _get_combined_prompts()

    assert list(combined) == list(_get_combined_article_types())
    assert combined == {
        key: f"fixed:{key}"
        for key in _get_combined_article_types()
    }


def test_source_mode_options_for_prompt_only_allowed_and_unlocked() -> None:
    assert _source_mode_options_for_article_type(
        "daily_story",
        past_blog_unlocked=True,
    ) == SOURCE_MODE_LABELS


def test_source_mode_options_for_prompt_only_not_allowed() -> None:
    assert _source_mode_options_for_article_type(
        "branding",
        past_blog_unlocked=True,
    ) == {
        "grounded": "資料あり",
        "web": "お任せ",
    }


def test_source_mode_options_past_blog_unlocked_and_locked() -> None:
    locked = _source_mode_options_for_article_type("daily_story", past_blog_unlocked=False)
    unlocked = _source_mode_options_for_article_type("daily_story", past_blog_unlocked=True)

    assert locked == {
        "grounded": "資料あり",
        "web": "お任せ",
    }
    assert unlocked == SOURCE_MODE_LABELS


def test_source_mode_allows_no_sources_for_allowed_prompt_only_with_prompt() -> None:
    assert _source_mode_allows_no_sources(
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        prompt_raw="夕方の打ち合わせで気づいたこと",
        past_blog_unlocked=True,
    )


def test_source_mode_allows_no_sources_rejects_not_allowed_case() -> None:
    assert not _source_mode_allows_no_sources(
        article_type_key="branding",
        source_mode_key="prompt_only",
        prompt_raw="会社紹介を書きたい",
        past_blog_unlocked=True,
    )


def test_resolve_source_mode_selection_keeps_valid_current_selection() -> None:
    assert _resolve_source_mode_selection("お任せ") == {
        "source_mode_key": "web",
        "source_mode_label": "お任せ",
        "requires_source_inputs": False,
        "uses_web_research": True,
    }


def test_resolve_source_mode_selection_invalid_current_selection_falls_back() -> None:
    assert _resolve_source_mode_selection("存在しない選択") == {
        "source_mode_key": "grounded",
        "source_mode_label": "資料あり",
        "requires_source_inputs": True,
        "uses_web_research": False,
    }


def test_resolve_source_mode_selection_prompt_only_gating_fallback_contract_is_external() -> None:
    selection = _resolve_source_mode_selection("プロンプトのみ")
    available_modes = _source_mode_options_for_article_type(
        "branding",
        past_blog_unlocked=True,
    )

    assert selection["source_mode_key"] == "prompt_only"
    assert selection["source_mode_key"] not in available_modes
    assert available_modes["grounded"] == "資料あり"


def test_build_source_mode_helper_text_for_prompt_only() -> None:
    assert _build_source_mode_helper_text(
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        past_blog_unlocked=True,
    ) == (
        "プロンプトのみで始めます。1行テーマを体験メモとして使い、公開済みブログは書き味と関心領域の参考に限定します。"
        "統計・価格・法律・医療・金融・比較優位・会社実績は足しません。"
    )


def test_build_source_mode_helper_text_for_source_required() -> None:
    assert _build_source_mode_helper_text(
        article_type_key="branding",
        source_mode_key="grounded",
        past_blog_unlocked=False,
    ) == "資料ありを選択中です。1行テーマは使いません。"


def test_build_source_mode_helper_text_for_past_blog_unlocked_web() -> None:
    assert _build_source_mode_helper_text(
        article_type_key="explanatory_article",
        source_mode_key="web",
        past_blog_unlocked=True,
    ) == "お任せで始めます。1行テーマと公開済みブログの蓄積がそろうと、生成前に外部ソースの材料集めへ進みます。公開済みブログ本文は今回の記事の事実ソースには使いません。"


def test_build_source_mode_input_surface_returns_existing_dict_contract() -> None:
    surface = _build_source_mode_input_surface(
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        past_blog_unlocked=True,
    )

    assert list(surface) == [
        "section_intro_text",
        "source_mode_helper_text",
        "prompt_visible",
        "prompt_label",
        "prompt_placeholder",
        "prompt_helper_text",
        "source_title_text",
        "source_helper_text",
    ]
    assert surface["prompt_visible"] is True
    assert surface["prompt_label"] == "1行テーマ"
    assert surface["source_title_text"] == "資料入力"


def test_build_source_mode_input_surface_keys_and_labels_for_grounded_unchanged() -> None:
    surface = _build_source_mode_input_surface(
        article_type_key="branding",
        source_mode_key="grounded",
        past_blog_unlocked=False,
    )

    assert surface["prompt_visible"] is False
    assert surface["prompt_label"] == ""
    assert surface["source_title_text"] == "先にそろえる資料"
    assert surface["source_helper_text"] == (
        "資料ありでは、URL / PDF / 画像 / テキストのいずれかを1件以上追加すると開始できます。入力済みの方針や読者は保持します。"
    )


def test_build_source_mode_input_surface_has_no_ui_mutation_contract() -> None:
    first = _build_source_mode_input_surface(
        article_type_key="explanatory_article",
        source_mode_key="web",
        past_blog_unlocked=True,
    )
    second = _build_source_mode_input_surface(
        article_type_key="explanatory_article",
        source_mode_key="web",
        past_blog_unlocked=True,
    )

    assert first == second
    assert first is not second
