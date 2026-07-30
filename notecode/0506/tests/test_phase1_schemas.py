import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "app" / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate(schema_name: str, payload: dict) -> None:
    schema = load_schema(schema_name)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)


def test_p1_s1_source_card_validates_source_facts_spans_warnings_metadata():
    payload = {
        "source_id": "pdf_001",
        "source_type": "pdf",
        "title": "会社案内2026",
        "published_or_updated_at": "2026-04-20",
        "reliability": "user_uploaded",
        "main_topics": ["事業内容", "沿革"],
        "facts": [
            {
                "fact_id": "F001",
                "claim": "株式会社Aは2018年に創業した",
                "category": "company_profile",
                "importance": 5,
                "source_span": "p.2",
                "usable_in_article": True,
                "confidence": "high",
                "risk_flags": [],
            }
        ],
        "quotes_or_phrases": [
            {"text": "地域に根ざしたサービス", "usage": "tone_reference", "source_span": "p.4"}
        ],
        "warnings": [
            {"type": "old_information", "message": "売上高の記載は古い可能性あり", "source_span": "p.8"}
        ],
        "metadata": {
            "source_label": "会社案内PDF",
            "url": None,
            "canonical_url": None,
            "author": None,
            "retrieved_at": "2026-05-08T00:00:00+09:00",
            "source_priority": 2,
            "extraction_method": "pdf_text",
            "extraction_confidence": "high",
        },
    }

    validate("source_card.schema.json", payload)


def test_p1_s1_source_card_rejects_missing_source_span():
    payload = {
        "source_id": "manual_001",
        "source_type": "manual",
        "title": "メモ",
        "published_or_updated_at": None,
        "reliability": "user_uploaded",
        "main_topics": ["特徴"],
        "facts": [
            {
                "fact_id": "F001",
                "claim": "手入力された事実",
                "category": "memo",
                "importance": 3,
                "usable_in_article": True,
                "confidence": "medium",
            }
        ],
        "quotes_or_phrases": [],
        "warnings": [],
        "metadata": {"source_label": "手入力"},
    }

    with pytest.raises(Exception):
        validate("source_card.schema.json", payload)


def test_p1_s2_knowledge_pack_validates_merge_and_conflict_examples():
    payload = {
        "article_knowledge_pack": {
            "pack_id": "pack_001",
            "source_card_ids": ["pdf_001", "url_001"],
            "confirmed_facts": [
                {
                    "claim_id": "C001",
                    "claim": "株式会社Aは2018年創業で、地域密着型のサービスを展開している",
                    "supporting_fact_ids": ["F001", "F014"],
                    "confidence": "high",
                    "preferred_expression": "2018年の創業以来、地域に根ざしたサービスを展開",
                    "risk_flags": [],
                }
            ],
            "conflicts": [
                {
                    "issue": "従業員数がPDFでは30名、Webでは35名",
                    "involved_fact_ids": ["F010", "F011"],
                    "resolution": "Webの更新日が新しいため35名を採用",
                    "do_not_mention": False,
                }
            ],
            "deduped_themes": ["地域密着"],
            "do_not_infer": ["業界No.1とは書かない"],
        }
    }

    validate("knowledge_pack.schema.json", payload)


def test_p1_s3_article_brief_validates_self_perspective_company_example():
    payload = {
        "article_brief": {
            "brief_id": "brief_001",
            "genre_id": "company_service_intro",
            "persona_id": "in_house_brand_blog_editor",
            "writer_role": "in_house_brand_blog_editor",
            "viewpoint_mode": "self_perspective",
            "target_reader": "初めてサービスを知る読者",
            "article_goal": "私たちの事業内容を自然に伝える",
            "narrator": "私たち",
            "self_viewpoint_owner": "株式会社A",
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
            "editor_profile_id": "note_hatena_structural_editor",
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
                "enabled": False,
                "max_items": 0,
                "max_sentences_each": 1,
                "max_article_ratio_percent": 1,
                "required_grounding": "source_claim_ids",
                "factual_status": "not_a_fact_claim",
                "allowed_kinds": [],
                "forbidden_claims": [
                    "unsupported_numbers",
                    "prices",
                    "outcomes",
                    "superiority_claims",
                    "market_trends",
                    "customer_cases",
                    "legal_medical_financial_advice",
                ],
            },
            "editorial_bridge_candidates": [],
            "claim_allocation": [
                {"section_id": "s1", "claim_ids": ["C001"], "reuse_allowed": False}
            ],
            "sections": [
                {
                    "section_id": "s1",
                    "heading": "私たちが大切にしていること",
                    "purpose": "事業の背景を伝える",
                    "assigned_claim_ids": ["C001"],
                    "main_subject": "私たち",
                    "discourse_rules": ["同社を使わない"],
                }
            ],
            "style_rules": ["一人称を私たちに統一する"],
            "forbidden_viewpoint_terms": ["同社", "同サービス"],
            "allowed_external_voice": "attributed_quotes_only",
            "config_refs": ["app/config/article_genres.yaml"],
            "persona_refs": ["app/personas/writer_roles.yaml"],
        }
    }

    validate("article_brief.schema.json", payload)


def test_p1_s4_quality_schema_validates_stylometry_issue_candidates():
    payload = {
        "quality_check": {
            "pass": False,
            "score": 82,
            "issues": [
                {
                    "type": "model_frequent_word",
                    "severity": "medium",
                    "text": "第一歩",
                    "reason": "汎用的な締め表現として重複している",
                    "fix_instruction": "source-grounded な具体語に置き換える",
                    "claim_ids": ["C001"],
                }
            ],
            "rewrite_needed": True,
            "stylometry": {
                "sentence_count": 18,
                "paragraph_count": 7,
                "issue_candidates": [
                    {
                        "type": "ending_bucket_monotony",
                        "severity": "medium",
                        "reason": "後半の文末が同じ bucket に偏っている",
                    }
                ],
            },
        }
    }

    validate("quality_check.schema.json", payload)


def test_p1_s5_publish_readiness_locks_high_risk_auto_publish():
    valid_payload = {
        "publish_readiness": {
            "score": 91,
            "auto_publish_allowed": False,
            "review_required": True,
            "risk_categories": ["financial"],
            "reasons": ["金融カテゴリは人間レビューが必要"],
            "blocking_reasons": ["high-risk category lockout"],
        }
    }
    invalid_payload = {
        "publish_readiness": {
            "score": 91,
            "auto_publish_allowed": True,
            "review_required": False,
            "risk_categories": ["financial"],
            "reasons": ["高スコア"],
        }
    }

    validate("publish_readiness.schema.json", valid_payload)
    with pytest.raises(Exception):
        validate("publish_readiness.schema.json", invalid_payload)
