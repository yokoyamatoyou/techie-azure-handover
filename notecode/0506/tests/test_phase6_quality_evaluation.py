from pathlib import Path

from app.agents.japanese_quality_checker import JapaneseQualityChecker
from app.agents.targeted_rewriter import TargetedRewriter
from app.evals.evaluator import load_eval_cases, run_eval_case, run_eval_suite
from app.evals.rubric import QUALITY_AXES
from app.services.local_llm_client import LocalPipelineClient


def test_p6_s1_eval_corpus_design_loads_cases():
    cases = load_eval_cases()

    assert {case["case_id"] for case in cases} == {"company_intro_basic", "announcement_basic"}
    assert all(case["sources"] for case in cases)


def test_p6_s2_ai_like_writing_rubric_contains_required_axes():
    assert QUALITY_AXES == [
        "source_grounding",
        "self_perspective_consistency",
        "first_person_consistency",
        "third_party_viewpoint_leakage",
        "paragraph_rhythm",
        "line_break_naturalness",
        "ending_bucket_monotony",
        "model_frequent_words",
        "generic_encouragement",
        "note_hatena_readability",
        "cta_naturalness",
    ]


def test_p6_s3_generation_quality_test_saves_artifacts(tmp_path: Path):
    report = run_eval_case(load_eval_cases()[0], tmp_path)
    artifact_dir = Path(report["artifact_dir"])

    assert report["case_id"] == "company_intro_basic"
    assert (artifact_dir / "draft.md").exists()
    assert (artifact_dir / "edited_draft.md").exists()
    assert (artifact_dir / "latest_generation_output.md").exists()
    assert (artifact_dir / "latest_generation_quality_report.json").exists()
    assert (artifact_dir / "phase6_quality_report.json").exists()


def test_p6_s4_targeted_rewrite_effect_test_removes_flagged_ai_like_phrase():
    brief = {
        "article_brief": {
            "brief_id": "b1",
            "genre_id": "company_service_intro",
            "persona_id": "in_house_brand_blog_editor",
            "writer_role": "in_house_brand_blog_editor",
            "viewpoint_mode": "self_perspective",
            "target_reader": "読者",
            "article_goal": "紹介",
            "narrator": "私たち",
            "qa_policy_id": "self_perspective_blog_default",
            "style_profile_id": "note_hatena_owned_media_soft",
            "style_edit_policy": {
                "preferred_sentences_per_paragraph": 2,
                "max_sentences_per_paragraph": 3,
                "line_break_policy": "topic_shift_or_two_sentences",
                "subject_omission_policy": "clear_context_only",
                "ending_bucket_policy": "structural_variation",
                "protected_subject_terms": ["年", "月", "日", "円", "担当"],
            },
            "target_length_chars": 1200,
            "section_count": 1,
            "source_thickness": "medium",
            "claim_allocation": [],
            "sections": [
                {
                    "section_id": "s1",
                    "heading": "見出し",
                    "purpose": "確認",
                    "assigned_claim_ids": [],
                    "main_subject": "私たち",
                    "discourse_rules": [],
                }
            ],
            "style_rules": [],
            "forbidden_viewpoint_terms": ["同社"],
            "config_refs": [],
            "persona_refs": [],
        }
    }
    text = "私たちは内容を整理します。いかがでしたでしょうか。"
    quality = JapaneseQualityChecker().check(text, brief, {"article_knowledge_pack": {"confirmed_facts": []}})

    rewritten = TargetedRewriter(LocalPipelineClient()).rewrite(text, quality, brief)

    assert "いかがでしたでしょうか" not in rewritten


def test_p6_s5_note_hatena_review_suite_writes_suite_report(tmp_path: Path):
    suite = run_eval_suite(tmp_path)

    assert suite["case_count"] == 2
    assert (tmp_path / "phase6_suite_report.json").exists()
    assert all("note_hatena_readability" in {item["axis"] for item in report["rubric"]} for report in suite["reports"])
