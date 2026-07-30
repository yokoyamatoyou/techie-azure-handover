from __future__ import annotations

from pathlib import Path

from app.agents.japanese_quality_checker import JapaneseQualityChecker
from app.services.human_visible_surface_gate import (
    check_human_visible_surface,
    is_human_visible_surface_gate_enabled,
)


NOTECODE_ROOT = Path(__file__).resolve().parents[2]


FOLLOWUP_REQUIRED_ARTICLES = {
    "market_explanation": (
        "logs/0626/mxrq_api_20260626_161500/generated_article.md",
        {"ocr_spaced_source_text", "dangling_japanese_quote_fragment", "duplicate_long_sentence"},
    ),
    "announcement": (
        "logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260626_194056/generated_article.md",
        {"generic_local_opening", "unrelated_local_cta", "duplicate_long_sentence"},
    ),
    "daily_activity": (
        "logs/0626/daily_activity_targeted_rewrite_sentence_split_followthrough_one_article_api_validation_after_approval_20260626_110732/generated_article.md",
        {"generic_local_opening", "unrelated_local_cta", "dangling_japanese_quote_fragment"},
    ),
    "case_study": (
        "logs/0625/route_v_case_study_structural_editor_knowledge_pack_payload_contract_one_article_api_validation_after_approval_20260625_152645/generated_article.md",
        {"generic_local_opening", "unrelated_local_cta"},
    ),
}


VISUALLY_ACCEPTABLE_ARTICLES = {
    "comparison_guide": "logs/0625/route_v_comparison_guide_category_field_one_article_api_validation_after_approval_20260625_132712/generated_article.md",
    "company_service_intro": "logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/human_review_articles/company_service_intro.md",
}


def test_surface_gate_replays_saved_followup_required_articles_without_api() -> None:
    for genre_id, (path, expected_codes) in FOLLOWUP_REQUIRED_ARTICLES.items():
        report = check_human_visible_surface(_read_article(path), _brief(genre_id))
        gate = report["human_visible_surface_gate"]
        codes = {finding["code"] for finding in gate["findings"]}

        assert gate["enabled_for_brief"] is True
        assert gate["pass"] is False
        assert expected_codes <= codes


def test_surface_gate_preserves_saved_visually_acceptable_articles() -> None:
    for genre_id, path in VISUALLY_ACCEPTABLE_ARTICLES.items():
        report = check_human_visible_surface(_read_article(path), _brief(genre_id))
        gate = report["human_visible_surface_gate"]

        assert gate["enabled_for_brief"] is True
        assert gate["pass"] is True
        assert gate["findings"] == []


def test_quality_checker_blocks_route_v_final_quality_on_surface_findings() -> None:
    text = _read_article(FOLLOWUP_REQUIRED_ARTICLES["daily_activity"][0])
    quality = JapaneseQualityChecker().check(
        text,
        _brief("daily_activity"),
        {"article_knowledge_pack": {"confirmed_facts": []}},
    )
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert quality["quality_check"]["pass"] is False
    assert quality["quality_check"]["rewrite_needed"] is True
    assert {"style_mismatch", "cta_issue", "formatting_mismatch"} <= issue_types


def test_surface_gate_is_route_v_scoped_for_quality_checker() -> None:
    assert is_human_visible_surface_gate_enabled(_brief("daily_activity")) is True
    assert is_human_visible_surface_gate_enabled({"article_brief": {"genre_id": "case_study"}}) is True
    assert is_human_visible_surface_gate_enabled(_brief("legacy_misc")) is False


def _read_article(relative_path: str) -> str:
    return (NOTECODE_ROOT / relative_path).read_text(encoding="utf-8")


def _brief(genre_id: str) -> dict:
    return {
        "article_brief": {
            "genre_id": genre_id,
            "viewpoint_mode": "self_perspective",
            "narrator": "私たち" if genre_id != "announcement" else "当社",
            "self_viewpoint_owner": "テスト提供者",
            "body_length_floor_chars": 1,
        }
    }
