import pytest

from app.services.editor_persona_contract import (
    EditorPersonaContractError,
    load_editor_persona_contract,
    render_editor_persona_prompt,
    run_encoding_preflight,
    validate_editor_persona_matrix,
)


GENRE_NARRATORS = {
    "market_explanation": "私たち",
    "company_service_intro": "私たち",
    "announcement": "当社",
    "case_study": "私たち",
    "comparison_guide": "私たち",
    "daily_activity": "私たち",
}

SECOND_PASS_ROLES = {
    "company_service_intro": "source-backed 後半編集者",
    "daily_activity": "生活文芸編集者",
    "comparison_guide": "根拠編集者",
    "market_explanation": "構造整理編集者",
    "case_study": "証言境界編集者",
}


def test_editor_persona_matrix_is_complete_and_compact():
    check = validate_editor_persona_matrix()

    assert check["pass"] is True
    assert check["expected_genres_present"] is True
    assert check["genre_delta_keys_ok"] is True
    assert check["non_announcement_second_pass_only"] is True
    assert set(check["second_pass_enabled_genres"]) == set(SECOND_PASS_ROLES)
    assert check["second_pass_roles"] == SECOND_PASS_ROLES
    assert check["announcement_second_pass_needed"] is False
    assert check["daily_activity_role"] == "日々の文筆家"
    assert check["comparison_guide_role"] == "選定アドバイザー"
    assert check["comparison_evidence_rule"] == "split_source_fact_and_llm_general_context"


def test_rendered_prompt_uses_common_block_plus_one_genre_delta():
    contract = load_editor_persona_contract()

    for genre_id, narrator in GENRE_NARRATORS.items():
        prompt = render_editor_persona_prompt(genre_id, narrator=narrator)

        assert prompt.count("## Common Editor Rules") == 1
        assert prompt.count("## Genre Delta") == 1
        assert contract["genres"][genre_id]["role"] in prompt
        assert narrator in prompt
        assert "## Conditional Second Editor" not in prompt
        assert run_encoding_preflight(prompt, genre_id, narrator=narrator)["pass"] is True


def test_non_announcement_genres_render_second_editor_persona_with_common_rules_once():
    contract = load_editor_persona_contract()

    for genre_id, role in SECOND_PASS_ROLES.items():
        prompt = render_editor_persona_prompt(genre_id, narrator=GENRE_NARRATORS[genre_id], second_pass=True)

        assert role in prompt
        assert prompt.count("## Conditional Second Editor") == 1
        assert prompt.count("Common second-pass rules:") == 1
        assert prompt.count("Genre second-pass delta:") == 1
        for rule in contract["common"]["second_pass_rules"]:
            assert prompt.count(rule) == 1
        for other_genre, other_role in SECOND_PASS_ROLES.items():
            if other_genre != genre_id:
                assert other_role not in prompt
        assert run_encoding_preflight(
            prompt, genre_id, narrator=GENRE_NARRATORS[genre_id], second_pass=True
        )["pass"] is True

    with pytest.raises(EditorPersonaContractError):
        render_editor_persona_prompt("announcement", narrator="当社", second_pass=True)


def test_comparison_guide_splits_source_fact_and_llm_general_context():
    prompt = render_editor_persona_prompt("comparison_guide", narrator="私たち")

    assert "選定アドバイザー" in prompt
    assert "source_fact と llm_general_context を分け" in prompt
    assert "根拠がある範囲のおすすめ" in prompt
    assert run_encoding_preflight(prompt, "comparison_guide", narrator="私たち")["pass"] is True


def test_daily_activity_second_pass_preserves_scene_material_without_prompt_bloat():
    prompt = render_editor_persona_prompt("daily_activity", narrator="私たち", second_pass=True)
    check = run_encoding_preflight(prompt, "daily_activity", narrator="私たち", second_pass=True)

    assert "source由来の場面素材を残す" in prompt
    assert "日時、場所、道具、動作、順序、制約を削りすぎない" in prompt
    assert "告知文や一覧案内へ圧縮せず" in prompt
    assert check["pass"] is True
    assert check["prompt_line_count"] <= 60
    assert check["prompt_char_count"] <= 2600


def test_company_intro_front_back_contract_renders_required_provider_self_terms():
    prompt = render_editor_persona_prompt("company_service_intro", narrator="私たち", second_pass=True)
    check = run_encoding_preflight(prompt, "company_service_intro", narrator="私たち", second_pass=True)

    assert "会社・サービス提供者側の社内ブロガー" in prompt
    assert "私たちを会社・サービス提供者として保つ" in prompt
    assert "低関心の読者へ、仕事・暮らし・選定・運用の接点から入る" in prompt
    assert "source-backed な後半の厚みを保つ" in prompt
    assert "商品対応、運用、展示、沿革、統合、理念が source にある場合だけ深め、会社側の行動と価値へ回収する" in prompt
    assert "会社説明やプロフィールからの汎用開始" in prompt
    assert "外部レビュー口調" in prompt
    assert "読者が理解したという推測" in prompt
    assert "文字数だけの padding" in prompt
    assert check["pass"] is True
    assert check["api_send_allowed_current_owner"] is False
    assert check["prompt_line_count"] <= 60
    assert check["prompt_char_count"] <= 2600


def test_encoding_preflight_fails_closed_on_mojibake_or_replacement_chars():
    prompt = render_editor_persona_prompt("daily_activity", narrator="私たち")
    damaged = prompt + "縺 � ???"
    check = run_encoding_preflight(damaged, "daily_activity", narrator="私たち", future_api_context=True)

    assert check["pass"] is False
    assert check["api_send_allowed"] is False
    assert "縺" in check["mojibake_sentinel_hits"]
    assert check["replacement_character_count"] == 1
    assert check["question_mark_run_max"] == 3
