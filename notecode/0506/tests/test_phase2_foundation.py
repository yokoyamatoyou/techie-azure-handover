from pathlib import Path

import pytest

from app.services.config_loader import ConfigError, get_genre_config, load_project_config
from app.services.persona_loader import PersonaError, load_persona_bundle
from app.services.prompt_renderer import prompt_line_count, render_template
from app.services.stylometry import analyze_text


ROOT = Path(__file__).resolve().parents[1]


def test_p2_s1_import_smoke_and_pytest_discovery():
    import app
    import app.services.config_loader
    import app.services.persona_loader
    import app.services.prompt_renderer
    import app.services.stylometry

    assert app.__all__ == ["services"]


def test_p2_s2_config_loader_loads_valid_config_and_rejects_unknown_genre():
    config = load_project_config()
    genre = get_genre_config("company_service_intro", config)
    market_genre = get_genre_config("market_explanation", config)
    expected_genres = {
        "market_explanation",
        "company_service_intro",
        "announcement",
        "case_study",
        "comparison_guide",
        "daily_activity",
    }

    assert genre["default_narrator"] == "私たち"
    assert market_genre["default_persona_id"] == "in_house_explanatory_blog_editor"
    assert expected_genres <= set(config.article_genres["genres"])
    assert "source_priority" in config.source_acquisition
    with pytest.raises(ConfigError):
        get_genre_config("missing_genre", config)


def test_p2_s2_persona_loader_resolves_role_and_viewpoint():
    bundle = load_persona_bundle("in_house_brand_blog_editor")
    market_bundle = load_persona_bundle("in_house_explanatory_blog_editor")
    announcement_bundle = load_persona_bundle("in_house_announcement_editor")
    case_bundle = load_persona_bundle("in_house_case_study_editor")
    comparison_bundle = load_persona_bundle("in_house_comparison_guide_editor")
    daily_bundle = load_persona_bundle("in_house_daily_activity_blog_writer")

    assert bundle.viewpoint_profile["narrator"] == "私たち"
    assert "unsupported trend" in " ".join(market_bundle.writer_role["constraints"])
    assert announcement_bundle.viewpoint_profile["narrator"] == "当社"
    assert announcement_bundle.style_profile["style_profile_id"] == "formal_notice_compact"
    assert case_bundle.viewpoint_profile["narrator"] == "私たち"
    assert comparison_bundle.viewpoint_profile["narrator"] == "私たち"
    assert daily_bundle.viewpoint_profile["narrator"] == "私たち"
    assert bundle.style_profile["style_profile_id"] == "note_hatena_owned_media_soft"
    assert bundle.style_profile["paragraph_policy"]["preferred_sentences_per_paragraph"] == 2
    assert bundle.editor_profile["editor_profile_id"] == "note_hatena_structural_editor"
    assert "Do not describe the company as a third party." in bundle.writer_role["constraints"]
    with pytest.raises(PersonaError):
        load_persona_bundle("unknown_persona")


def test_p2_s3_prompt_renderer_uses_selected_persona_and_viewpoint_without_bloat():
    context = {
        "writer_role": "in_house_brand_blog_editor",
        "viewpoint_mode": "self_perspective",
        "narrator": "私たち",
        "target_reader": "初めてサービスを知る読者",
        "article_goal": "会社の姿勢を伝える",
        "sections": ["s1: C001 を使う", "s2: C002 を使う"],
        "style_rules": ["一人称を統一する"],
        "qa_policy_id": "self_perspective_blog_default",
    }

    rendered = render_template("draft_writer.md", context)

    assert "in_house_brand_blog_editor" in rendered
    assert "self_perspective" in rendered
    assert "私たち" in rendered
    assert prompt_line_count("draft_writer.md") < 120
    assert rendered.count("いかがでしたでしょうか") == 0


def test_p2_s4_stylometry_flags_watchlist_endings_connectors_and_narrator_mixing():
    text = (
        "私たちは地域の相談を受けています。また、支援を続けています。\n\n"
        "当社は第一歩を支えます。また、第一歩を整えます。\n\n"
        "同社は安心を大切にしています。さらに改善しています。"
    )

    result = analyze_text(text)
    issue_types = {issue["type"] for issue in result["issue_candidates"]}

    assert result["sentence_count"] == 6
    assert result["paragraph_shape"] == [2, 2, 2]
    assert "私たち" in result["first_person_variants"]
    assert "当社" in result["first_person_variants"]
    assert "同社" in result["third_party_terms"]
    assert any(item["term"] == "第一歩" and item["count"] == 2 for item in result["model_frequent_words"])
    assert "model_frequent_word" in issue_types
    assert "connector_repetition" in issue_types
    assert "narrator_mixing" in issue_types
    assert "third_party_viewpoint_leakage" in issue_types
    assert "paragraph_rhythm_monotony" in issue_types


def test_p2_s4_stylometry_flags_repeated_gpt_like_decision_words():
    text = (
        "私たちは相談前の判断軸を整理します。資料の見方も整理します。\n\n"
        "判断材料を整理し、料金表の観点ではなくサービスの観点から見方を伝えます。"
    )

    result = analyze_text(text)
    flagged = {item["term"] for item in result["model_frequent_words"]}

    assert {"整理", "観点", "見方"}.issubset(flagged)
    assert "model_frequent_word" in {issue["type"] for issue in result["issue_candidates"]}


def test_p2_s4_stylometry_ignores_markdown_headings_for_sentence_metrics():
    text = (
        "## 私たちのサービス領域\n"
        "私たちは、データ入力からスキャニング、システム開発、運用管理、RPA支援まで扱っています。"
    )

    result = analyze_text(text)

    assert result["sentence_count"] == 1
    assert result["max_sentence_length"] < 90
    assert result["paragraph_shape"] == [1]
