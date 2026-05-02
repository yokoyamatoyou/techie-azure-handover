"""Tests for zero-base phase01 baseline and contract utilities."""

from __future__ import annotations

from pathlib import Path

from note.zero_base.phase01_baseline_contract import (
    REQUIRED_INTENT_FIELDS,
    build_intent_contract,
    build_intent_contract_schema,
    compute_contract_kpis,
    load_jsonl_records,
    summarize_kpis,
)


def test_phase01_schema_has_required_keys() -> None:
    schema = build_intent_contract_schema()
    assert schema["required"] == REQUIRED_INTENT_FIELDS


def test_phase01_kpi_reproducibility() -> None:
    sample_records = [
        {
            "article_type": "ai",
            "category_base_template": "ai",
            "failed_parameters": {
                "hard_soft_eval": {"metrics": {"semantic_issue_count": 4}},
                "retry_failures": [{"redundant": True}, {"redundant": False}],
                "contextual_naturalness_report": {
                    "semantic_layout": {"transition_jaccard_mean": 0.25}
                },
                "fingerprint_phase": {"subject_explicit_rate": 0.62},
            },
        },
        {
            "article_type": "branding",
            "category_base_template": "branding",
            "failed_parameters": {
                "hard_soft_eval": {"metrics": {"semantic_issue_count": 2}},
                "retry_failures": [{"redundant": False}],
                "contextual_naturalness_report": {
                    "semantic_layout": {"transition_jaccard_mean": 0.4}
                },
                "fingerprint_phase": {"subject_explicit_rate": 0.55},
            },
        },
    ]
    first = summarize_kpis(sample_records)
    second = summarize_kpis(sample_records)
    assert first == second


def test_phase01_ui_category_consistency() -> None:
    matched_contract = build_intent_contract(
        {
            "article_type": "ai",
            "category_base_template": "ai",
            "pre_generation_questions": [],
            "pre_generation_answers": {},
        }
    )
    mismatch_contract = build_intent_contract(
        {
            "article_type": "ai",
            "category_base_template": "branding",
            "pre_generation_questions": [],
            "pre_generation_answers": {},
        }
    )
    assert compute_contract_kpis(matched_contract)["category_consistency_score"] == 1.0
    assert compute_contract_kpis(mismatch_contract)["category_consistency_score"] == 0.0


def test_phase01_question_reflection_and_unresolved_items() -> None:
    contract = build_intent_contract(
        {
            "article_type": "ai",
            "category_base_template": "ai",
            "must_cover": [],
            "pre_generation_questions": [
                {"id": "message", "question": "核心メッセージは？"},
                {"id": "target", "question": "誰向け？"},
            ],
            "pre_generation_answers": {
                "message": "結論と根拠を明確にする",
            },
        }
    )
    assert "結論と根拠を明確にする" in contract["must_cover"]
    assert "target" in contract["unresolved_items"]
    assert compute_contract_kpis(contract)["question_reflection_rate"] == 1.0


def test_phase01_target_and_perspective_answers_do_not_reenter_must_cover() -> None:
    contract = build_intent_contract(
        {
            "article_type": "branding",
            "category_base_template": "branding",
            "must_cover": ["価値訴求"],
            "pre_generation_questions": [
                {"id": "perspective", "question": "どの視点で書くか"},
                {"id": "target", "question": "誰向けか"},
                {"id": "message", "question": "何を伝えるか"},
            ],
            "pre_generation_answers": {
                "perspective": "ブランド担当として語る",
                "target": "導入検討者",
                "message": "選定の判断軸を具体化する",
            },
        }
    )

    assert "価値訴求" in contract["must_cover"]
    assert "選定の判断軸を具体化する" in contract["must_cover"]
    assert "ブランド担当として語る" not in contract["must_cover"]
    assert "導入検討者" not in contract["must_cover"]


def test_phase01_jsonl_loader_skips_malformed_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    log_path.write_text(
        '{"ok": 1}\n'
        '{"broken": \n'
        '{"ok": 2}\n',
        encoding="utf-8",
    )
    records, malformed_count = load_jsonl_records(log_path)
    assert len(records) == 2
    assert malformed_count == 1
