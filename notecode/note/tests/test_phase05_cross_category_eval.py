from __future__ import annotations

from puran6 import cross_category_eval as eval_mod


def test_phase05_normalize_key_handles_spaces_and_symbols() -> None:
    assert eval_mod.normalize_key("Company Introduction") == "company_introduction"
    assert eval_mod.normalize_key(" corporate-culture ") == "corporate_culture"
    assert eval_mod.normalize_key("Announcement!") == "announcement"


def test_phase05_extract_metrics_reads_contract_alignment_fields() -> None:
    payload = {
        "attempt_id": "gen-test",
        "article_type": "ai",
        "runtime_reason_code": "SYS_FORBIDDEN_TOPIC_DRIFT",
        "input_contract": {
            "length_mode_requested": "adaptive",
            "length_mode": "short",
        },
        "pipeline_check": {
            "input_contract": {
                "length_mode_requested": "adaptive",
                "length_mode": "short",
            },
            "contract_alignment": {
                "speaker_consistency_score": 0.35,
                "pronoun_consistency_score": 0.0,
                "section_contract_issue_count": 2,
                "forbidden_topic_hits": ["採用活動", "福利厚生"],
                "must_cover_items": ["判断基準", "注意点"],
                "audience_profile": "実務担当者",
                "topic_statement": "AI活用の判断軸を整理する",
                "question_source_counts": {
                    "interview_answers": 2,
                    "user_prompt": 1,
                    "unresolved_items": 0,
                    "unknown": 0,
                },
            }
        },
        "body": "本文です。",
        "blocked_output_redacted": True,
    }
    metrics = eval_mod.extract_metrics(payload)

    assert metrics["attempt_id"] == "gen-test"
    assert metrics["runtime_reason_code"] == "SYS_FORBIDDEN_TOPIC_DRIFT"
    assert metrics["speaker_consistency_score"] == 0.35
    assert metrics["pronoun_consistency_score"] == 0.0
    assert metrics["section_contract_issue_count"] == 2
    assert metrics["forbidden_topic_hit_count"] == 2
    assert metrics["body_chars"] == len("本文です。")
    assert metrics["blocked_output_redacted"] is True
    assert metrics["length_mode_requested"] == "adaptive"
    assert metrics["length_mode"] == "short"
    assert metrics["must_cover_items"] == "判断基準 / 注意点"
    assert metrics["audience_profile"] == "実務担当者"
    assert metrics["topic_statement"] == "AI活用の判断軸を整理する"
    assert metrics["question_source_counts"] == "interview_answers:2, user_prompt:1, unresolved_items:0, unknown:0"


def test_phase05_build_eval_rows_marks_pending_without_attempt() -> None:
    cases_payload = {
        "cases": [
            {
                "case_id": "ai_case",
                "category_key": "ai",
                "category": "ai",
                "article_type_key": "ai",
            },
            {
                "case_id": "branding_case",
                "category_key": "branding",
                "category": "branding",
                "article_type_key": "branding",
            },
        ]
    }
    attempts_payload = {
        "records": [
            {"case_id": "ai_case", "attempt_id": "gen-ai", "subjective_review": "B"},
            {"case_id": "branding_case", "attempt_id": ""},
        ]
    }
    audit_entries = [
        {
            "attempt_id": "gen-ai",
            "timestamp": "2026-03-06 12:00:00",
            "article_type": "ai",
            "runtime_reason_code": "",
            "input_contract": {
                "length_mode_requested": "adaptive",
                "length_mode": "normal",
            },
            "output_metrics": {"body_chars": 1234},
            "contract_alignment": {
                "speaker_consistency_score": 1.0,
                "pronoun_consistency_score": 1.0,
                "section_contract_issue_count": 0,
                "forbidden_topic_hit_count": 0,
                "must_cover_items": ["論点整理"],
                "audience_profile": "実務担当者",
                "topic_statement": "判断基準を整理する",
                "question_source_counts": {
                    "interview_answers": 1,
                    "user_prompt": 1,
                    "unresolved_items": 0,
                    "unknown": 0,
                },
            },
        }
    ]

    rows = eval_mod.build_eval_rows(
        cases_payload=cases_payload,
        attempts_payload=attempts_payload,
        audit_entries=audit_entries,
        latest_output_payload={},
    )

    ai_row = next(item for item in rows if item["case_id"] == "ai_case")
    branding_row = next(item for item in rows if item["case_id"] == "branding_case")

    assert ai_row["generation_status"] == "success"
    assert ai_row["body_chars"] == 1234
    assert ai_row["subjective_review"] == "B"
    assert ai_row["length_mode_requested"] == "adaptive"
    assert ai_row["length_mode"] == "normal"
    assert ai_row["must_cover_items"] == "論点整理"
    assert ai_row["audience_profile"] == "実務担当者"
    assert ai_row["topic_statement"] == "判断基準を整理する"
    assert ai_row["question_source_counts"] == "interview_answers:1, user_prompt:1, unresolved_items:0, unknown:0"
    assert branding_row["generation_status"] == "pending"
    assert branding_row["attempt_id"] == ""
    assert branding_row["length_mode_requested"] == "n/a"
