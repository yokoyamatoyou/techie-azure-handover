from app.evals.hardening import create_hardening_report, inspect_bloat, verify_claim_traceability
from app.evals.rubric import diagnose_issue_owners


def test_p7_owner_diagnosis_maps_one_issue_to_one_owner_scope():
    quality = {
        "quality_check": {
            "issues": [
                {"type": "model_frequent_word"},
                {"type": "third_party_viewpoint_leakage"},
            ]
        }
    }

    owners = diagnose_issue_owners(quality)

    assert owners == {
        "style_editor": ["model_frequent_word"],
        "article_brief_builder": ["third_party_viewpoint_leakage"],
    }


def test_p7_traceability_verifier_rejects_unknown_claim_ids():
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "supporting_fact_ids": ["F001"]},
            ]
        }
    }
    article_brief = {
        "article_brief": {
            "sections": [
                {"section_id": "s1", "assigned_claim_ids": ["C001", "C999"]},
            ]
        }
    }

    problems = verify_claim_traceability(knowledge_pack, article_brief)

    assert problems == ["unknown claim_id in section s1: C999"]


def test_p7_bloat_inspection_passes_current_modules_and_prompts():
    result = inspect_bloat()

    assert result["pass"] is True
    assert result["failures"] == []


def test_p7_hardening_report_marks_ready_only_when_guards_pass():
    quality = {"quality_check": {"issues": []}}
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "supporting_fact_ids": ["F001"]},
            ]
        }
    }
    article_brief = {
        "article_brief": {
            "sections": [
                {"section_id": "s1", "assigned_claim_ids": ["C001"]},
            ]
        }
    }

    report = create_hardening_report(quality, knowledge_pack, article_brief)

    assert report["owner_diagnosis"] == {}
    assert report["traceability_problems"] == []
    assert report["ready_for_quality_tuning"] is True
