from app.agents.article_brief_builder import ArticleBriefBuilder
from app.services.local_llm_client import LocalPipelineClient


class BridgeReturningClient:
    def generate_json(self, stage_name, instructions, payload, schema_name):
        assert stage_name == "article_brief_builder"
        return {
            "article_brief": {
                "brief_id": "brief_with_bridge",
                "genre_id": payload["genre_id"],
                "persona_id": "external_reviewer",
                "writer_role": "external_reviewer",
                "viewpoint_mode": "third_party",
                "target_reader": payload["target_reader"],
                "article_goal": payload["article_goal"],
                "narrator": "outside reviewer",
                "self_viewpoint_owner": "outside reviewer",
                "qa_policy_id": "external_review_default",
                "style_profile_id": "external_review_style",
                "style_edit_policy": {
                    "preferred_sentences_per_paragraph": 2,
                    "max_sentences_per_paragraph": 3,
                    "line_break_policy": "topic_shift_or_two_sentences",
                    "subject_omission_policy": "clear_context_only",
                    "ending_bucket_policy": "structural_variation",
                    "protected_subject_terms": ["年", "月", "日", "円", "担当"],
                },
                "editor_profile_id": "external_review_editor",
                "editor_pass_policy": {
                    "focus_late_half": True,
                    "split_late_paragraph_over_sentences": 2,
                    "align_first_person_to_narrator": True,
                    "preserve_facts": True,
                    "preserve_numbers_dates_names": True,
                    "do_not_add_claims": True,
                },
                "target_length_chars": 1200,
                "section_count": 1,
                "source_thickness": "medium",
                "editorial_bridge_policy": {
                    "enabled": True,
                    "max_items": 1,
                    "max_sentences_each": 1,
                    "max_article_ratio_percent": 1,
                    "required_grounding": "source_claim_ids",
                    "factual_status": "not_a_fact_claim",
                    "allowed_kinds": ["company_posture"],
                    "forbidden_claims": ["unsupported_numbers"],
                },
                "editorial_bridge_candidates": [
                    {
                        "bridge_id": "B001",
                        "kind": "company_posture",
                        "section_id": "s1",
                        "source_claim_ids": ["C001"],
                        "angle": "姿勢につなぐ",
                        "usage_note": "使わない",
                    }
                ],
                "claim_allocation": [{"section_id": "s1", "claim_ids": ["C001"], "reuse_allowed": False}],
                "sections": [
                    {
                        "section_id": "s1",
                        "heading": "私たちについて",
                        "purpose": "概要を伝える",
                        "assigned_claim_ids": ["C001"],
                        "main_subject": payload["narrator"],
                        "discourse_rules": ["同社を使わない"],
                    }
                ],
                "style_rules": ["一人称を統一する"],
                "forbidden_viewpoint_terms": ["同社"],
                "config_refs": ["app/config/article_genres.yaml"],
                "persona_refs": ["app/personas/writer_roles.yaml"],
            }
        }

    def generate_text(self, stage_name, instructions, payload):
        raise AssertionError("generate_text should not be called")


def _knowledge_pack() -> dict:
    return {
        "article_knowledge_pack": {
            "pack_id": "pack_test",
            "source_card_ids": ["manual_001"],
            "confirmed_facts": [
                {
                    "claim_id": f"C{index:03d}",
                    "claim": f"根拠のある事実{index}",
                    "supporting_fact_ids": [f"F{index:03d}"],
                    "confidence": "medium",
                    "preferred_expression": f"根拠のある事実{index}",
                    "risk_flags": [],
                }
                for index in range(1, 7)
            ],
            "conflicts": [],
            "deduped_themes": ["テスト"],
            "do_not_infer": ["ソースにないことは書かない"],
        }
    }


def test_all_six_genres_build_briefs_with_expected_personas():
    builder = ArticleBriefBuilder(LocalPipelineClient())
    expectations = {
        "market_explanation": ("in_house_explanatory_blog_editor", "私たち", "note_hatena_owned_media_soft"),
        "company_service_intro": ("in_house_brand_blog_editor", "私たち", "note_hatena_owned_media_soft"),
        "announcement": ("in_house_announcement_editor", "当社", "formal_notice_compact"),
        "case_study": ("in_house_case_study_editor", "私たち", "note_hatena_owned_media_soft"),
        "comparison_guide": ("in_house_comparison_guide_editor", "私たち", "note_hatena_owned_media_soft"),
        "daily_activity": ("in_house_daily_activity_blog_writer", "私たち", "note_hatena_owned_media_soft"),
    }

    for genre_id, (persona_id, narrator, style_profile_id) in expectations.items():
        brief = builder.build(
            _knowledge_pack(),
            genre_id=genre_id,
            target_reader="読者",
            article_goal="ソースに基づいて記事を書く",
        )["article_brief"]

        assert brief["persona_id"] == persona_id
        assert brief["narrator"] == narrator
        assert brief["self_viewpoint_owner"] == narrator
        assert brief["style_profile_id"] == style_profile_id
        assert brief["editorial_bridge_policy"]["required_grounding"] == "source_claim_ids"
        assert brief["editorial_bridge_policy"]["enabled"] is False
        assert brief["editorial_bridge_policy"]["max_items"] == 0
        assert brief["editorial_bridge_candidates"] == []


def test_article_brief_preserves_explicit_self_viewpoint_owner():
    builder = ArticleBriefBuilder(LocalPipelineClient())

    brief = builder.build(
        _knowledge_pack(),
        genre_id="company_service_intro",
        target_reader="読者",
        article_goal="私たちの事業を伝える",
        narrator="私たち",
        self_viewpoint_owner="株式会社A",
    )["article_brief"]

    assert brief["self_viewpoint_owner"] == "株式会社A"
    assert brief["editorial_bridge_candidates"] == []


def test_article_brief_enforces_self_viewpoint_contract_and_clears_bridges():
    builder = ArticleBriefBuilder(BridgeReturningClient())

    brief = builder.build(
        _knowledge_pack(),
        genre_id="company_service_intro",
        target_reader="読者",
        article_goal="私たちの事業を伝える",
        narrator="私たち",
        self_viewpoint_owner="株式会社A",
    )["article_brief"]

    assert brief["editorial_bridge_policy"]["enabled"] is False
    assert brief["editorial_bridge_policy"]["max_items"] == 0
    assert brief["editorial_bridge_candidates"] == []
    assert brief["persona_id"] == "in_house_brand_blog_editor"
    assert brief["writer_role"] == "in_house_brand_blog_editor"
    assert brief["viewpoint_mode"] == "self_perspective"
    assert brief["narrator"] == "私たち"
    assert brief["self_viewpoint_owner"] == "株式会社A"
    assert brief["qa_policy_id"] == "self_perspective_blog_default"
    assert brief["style_profile_id"] == "note_hatena_owned_media_soft"
    assert brief["editor_profile_id"] == "note_hatena_structural_editor"
    assert "\u540c\u793e" in brief["forbidden_viewpoint_terms"]


def test_announcement_remains_compact_and_daily_activity_is_not_overlong():
    builder = ArticleBriefBuilder(LocalPipelineClient())

    announcement = builder.build(
        _knowledge_pack(),
        genre_id="announcement",
        target_reader="関係者",
        article_goal="必要事項を簡潔に伝える",
    )["article_brief"]
    daily = builder.build(
        _knowledge_pack(),
        genre_id="daily_activity",
        target_reader="日々の様子を知りたい読者",
        article_goal="できごとを自然に伝える",
    )["article_brief"]

    assert announcement["section_count"] == 2
    assert announcement["target_length_chars"] <= 1600
    assert daily["section_count"] == 2
    assert daily["target_length_chars"] == 1200


def test_comparison_guide_adds_target_category_from_target_reader():
    builder = ArticleBriefBuilder(LocalPipelineClient())

    brief = builder.build(
        _knowledge_pack(),
        genre_id="comparison_guide",
        target_reader="社内ナレッジ管理ツールを比較している営業企画担当者",
        article_goal="候補を用途別に整理する",
    )["article_brief"]

    assert brief["comparison_target_category"] == "社内ナレッジ管理ツール"


def test_comparison_guide_adds_target_category_from_confirmed_claim_when_reader_is_generic():
    builder = ArticleBriefBuilder(LocalPipelineClient())
    knowledge_pack = _knowledge_pack()
    knowledge_pack["article_knowledge_pack"]["confirmed_facts"][0][
        "preferred_expression"
    ] = "NoteFlow Liteは、月額8000円で5名まで利用できる社内ナレッジ管理ツールです。"

    brief = builder.build(
        knowledge_pack,
        genre_id="comparison_guide",
        target_reader="営業企画担当者",
        article_goal="候補を用途別に整理する",
    )["article_brief"]

    assert brief["comparison_target_category"] == "社内ナレッジ管理ツール"


def test_comparison_target_category_is_not_added_to_other_genres():
    builder = ArticleBriefBuilder(LocalPipelineClient())

    brief = builder.build(
        _knowledge_pack(),
        genre_id="company_service_intro",
        target_reader="社内ナレッジ管理ツールを比較している営業企画担当者",
        article_goal="私たちの事業を伝える",
    )["article_brief"]

    assert "comparison_target_category" not in brief
