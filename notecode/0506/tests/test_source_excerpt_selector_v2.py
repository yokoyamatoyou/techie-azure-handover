from app.services.source_excerpt_selector_v2 import build_selected_source_excerpts_v2


def _knowledge_pack() -> dict:
    return {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {
                    "claim_id": "C001",
                    "claim": "Alpha plan includes source-backed setup support.",
                    "supporting_fact_ids": ["F001"],
                    "confidence": "high",
                    "preferred_expression": "Alpha plan includes source-backed setup support.",
                    "risk_flags": [],
                }
            ]
        }
    }


def _source_cards() -> list[dict]:
    return [
        {
            "source_id": "manual_001",
            "facts": [
                {
                    "fact_id": "F001",
                    "claim": "Alpha plan includes source-backed setup support.",
                    "source_span": "manual:1",
                }
            ],
        }
    ]


def _source_packets() -> list[dict]:
    return [
        {
            "source_id": "manual_001",
            "source_type": "manual",
            "title": "Manual Source",
            "chunks": [
                {
                    "chunk_id": "manual_001_chunk_001",
                    "source_id": "manual_001",
                    "source_type": "manual",
                    "text": (
                        "Opening context.\n"
                        "Alpha plan includes source-backed setup support.\n"
                        "The source explains this near a short service overview.\n"
                        "This nearby wording should be visible to the writer."
                    ),
                    "source_span_ids": ["manual_001"],
                    "source_locations": ["manual:1"],
                }
            ],
        }
    ]


def test_selector_covers_one_excerpt_per_section_before_adjacent_claims() -> None:
    brief = {
        "article_brief": {
            "voice_mode": "self_authored_blogger",
            "source_shape": "service_catalog",
            "source_use_mode": "selective",
            "section_count": 3,
            "sections": [
                {"section_id": "S1", "assigned_claim_ids": ["C001", "C002"]},
                {"section_id": "S2", "assigned_claim_ids": ["C003"]},
                {"section_id": "S3", "assigned_claim_ids": ["C004"]},
            ],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "claim": "Alpha setup support.", "supporting_fact_ids": ["F001"], "preferred_expression": "Alpha setup support.", "risk_flags": []},
                {"claim_id": "C002", "claim": "Alpha onboarding checklist.", "supporting_fact_ids": ["F002"], "preferred_expression": "Alpha onboarding checklist.", "risk_flags": []},
                {"claim_id": "C003", "claim": "Beta market structure.", "supporting_fact_ids": ["F003"], "preferred_expression": "Beta market structure.", "risk_flags": []},
                {"claim_id": "C004", "claim": "Gamma operational risk.", "supporting_fact_ids": ["F004"], "preferred_expression": "Gamma operational risk.", "risk_flags": []},
            ]
        }
    }
    source_cards = [
        {
            "source_id": "manual_001",
            "facts": [
                {"fact_id": "F001", "claim": "Alpha setup support.", "source_span": "manual:1"},
                {"fact_id": "F002", "claim": "Alpha onboarding checklist.", "source_span": "manual:2"},
                {"fact_id": "F003", "claim": "Beta market structure.", "source_span": "manual:3"},
                {"fact_id": "F004", "claim": "Gamma operational risk.", "source_span": "manual:4"},
            ],
        }
    ]
    source_packets = [
        {
            "source_id": "manual_001",
            "source_type": "manual",
            "title": "Manual Source",
            "chunks": [
                {"chunk_id": "chunk_001", "source_id": "manual_001", "source_type": "manual", "text": "Alpha setup support.", "source_span_ids": ["manual:1"], "source_locations": ["manual:1"]},
                {"chunk_id": "chunk_002", "source_id": "manual_001", "source_type": "manual", "text": "Alpha onboarding checklist.", "source_span_ids": ["manual:2"], "source_locations": ["manual:2"]},
                {"chunk_id": "chunk_003", "source_id": "manual_001", "source_type": "manual", "text": "Beta market structure.", "source_span_ids": ["manual:3"], "source_locations": ["manual:3"]},
                {"chunk_id": "chunk_004", "source_id": "manual_001", "source_type": "manual", "text": "Gamma operational risk.", "source_span_ids": ["manual:4"], "source_locations": ["manual:4"]},
            ],
        }
    ]

    excerpts = build_selected_source_excerpts_v2(brief, knowledge_pack, source_cards, source_packets)

    assert [excerpt["claim_ids"][0] for excerpt in excerpts[:3]] == ["C001", "C003", "C004"]
    assert [excerpt["section_ids"][0] for excerpt in excerpts[:3]] == ["S1", "S2", "S3"]


def test_selector_adds_bounded_context_for_final_usage_hinted_unassigned_claims() -> None:
    brief = {
        "article_brief": {
            "voice_mode": "self_authored_blogger",
            "source_shape": "service_catalog",
            "source_use_mode": "selective",
            "section_count": 3,
            "article_goal": "Connect the report with GENIAC and Gennai public implementation examples.",
            "protected_subject_terms": ["GENIAC", "源内"],
            "sections": [
                {"section_id": "S1", "assigned_claim_ids": ["C001"]},
                {"section_id": "S2", "assigned_claim_ids": ["C002"]},
                {"section_id": "S3", "assigned_claim_ids": ["C003"]},
            ],
            "unassigned_claim_ids": ["C013", "C014", "C015"],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "claim": "Report purpose.", "supporting_fact_ids": ["F001"], "preferred_expression": "Report purpose.", "risk_flags": []},
                {"claim_id": "C002", "claim": "Market structure.", "supporting_fact_ids": ["F002"], "preferred_expression": "Market structure.", "risk_flags": []},
                {"claim_id": "C003", "claim": "Data quality.", "supporting_fact_ids": ["F003"], "preferred_expression": "Data quality.", "risk_flags": []},
                {"claim_id": "C013", "claim": "GENIAC supports domestic generative AI development.", "supporting_fact_ids": ["F013"], "preferred_expression": "GENIAC support.", "risk_flags": []},
                {"claim_id": "C014", "claim": "デジタル庁のガバメントAI「源内」は政府職員向けAI基盤である。", "supporting_fact_ids": ["F014"], "preferred_expression": "源内 AI基盤", "risk_flags": []},
                {"claim_id": "C015", "claim": "Unhinted unrelated claim.", "supporting_fact_ids": ["F015"], "preferred_expression": "Unhinted claim.", "risk_flags": []},
            ]
        }
    }
    source_cards = [
        {"source_id": "report", "facts": [{"fact_id": "F001", "claim": "Report purpose.", "source_span": "report:1"}, {"fact_id": "F002", "claim": "Market structure.", "source_span": "report:2"}, {"fact_id": "F003", "claim": "Data quality.", "source_span": "report:3"}]},
        {"source_id": "geniac", "facts": [{"fact_id": "F013", "claim": "GENIAC supports domestic generative AI development.", "source_span": "geniac:1"}]},
        {"source_id": "gennai", "facts": [{"fact_id": "F014", "claim": "デジタル庁のガバメントAI「源内」は政府職員向けAI基盤である。", "source_span": "gennai:1"}]},
        {"source_id": "other", "facts": [{"fact_id": "F015", "claim": "Unhinted unrelated claim.", "source_span": "other:1"}]},
    ]
    source_packets = [
        {"source_id": "report", "source_type": "url", "title": "Report", "chunks": [
            {"chunk_id": "report_1", "source_id": "report", "source_type": "url", "text": "Report purpose.", "source_span_ids": ["report:1"], "source_locations": ["report:1"]},
            {"chunk_id": "report_2", "source_id": "report", "source_type": "url", "text": "Market structure.", "source_span_ids": ["report:2"], "source_locations": ["report:2"]},
            {"chunk_id": "report_3", "source_id": "report", "source_type": "url", "text": "Data quality.", "source_span_ids": ["report:3"], "source_locations": ["report:3"]},
        ]},
        {"source_id": "geniac", "source_type": "url", "title": "GENIAC", "chunks": [{"chunk_id": "geniac_1", "source_id": "geniac", "source_type": "url", "text": "GENIAC supports domestic generative AI development.", "source_span_ids": ["geniac:1"], "source_locations": ["geniac:1"]}]},
        {"source_id": "gennai", "source_type": "url", "title": "Gennai", "chunks": [{"chunk_id": "gennai_1", "source_id": "gennai", "source_type": "url", "text": "デジタル庁のガバメントAI「源内」は政府職員向けAI基盤である。", "source_span_ids": ["gennai:1"], "source_locations": ["gennai:1"]}]},
        {"source_id": "other", "source_type": "url", "title": "Other", "chunks": [{"chunk_id": "other_1", "source_id": "other", "source_type": "url", "text": "Unhinted unrelated claim.", "source_span_ids": ["other:1"], "source_locations": ["other:1"]}]},
    ]

    excerpts = build_selected_source_excerpts_v2(brief, knowledge_pack, source_cards, source_packets)

    claim_ids = [excerpt["claim_ids"][0] for excerpt in excerpts]
    assert claim_ids == ["C001", "C002", "C003", "C013", "C014"]
    assert "C015" not in claim_ids
    assert excerpts[3]["section_ids"] == ["S3"]
    assert excerpts[4]["section_ids"] == ["S3"]
    assert {excerpt["source_id"] for excerpt in excerpts[-2:]} == {"geniac", "gennai"}


def test_selector_returns_empty_for_v1_brief() -> None:
    brief = {"article_brief": {"sections": [{"section_id": "s1", "assigned_claim_ids": ["C001"]}]}}

    excerpts = build_selected_source_excerpts_v2(brief, _knowledge_pack(), _source_cards(), _source_packets())

    assert excerpts == []


def test_selector_builds_bounded_excerpt_for_route_v_assigned_claim() -> None:
    brief = {
        "article_brief": {
            "voice_mode": "self_authored_blogger",
            "source_shape": "narrative",
            "source_use_mode": "selective",
            "section_count": 1,
            "sections": [{"section_id": "s1", "assigned_claim_ids": ["C001"]}],
        }
    }

    excerpts = build_selected_source_excerpts_v2(brief, _knowledge_pack(), _source_cards(), _source_packets())

    assert len(excerpts) == 1
    assert excerpts[0]["excerpt_id"] == "E001"
    assert excerpts[0]["claim_ids"] == ["C001"]
    assert excerpts[0]["section_ids"] == ["s1"]
    assert excerpts[0]["source_locations"] == ["manual:1"]
    assert "Alpha plan includes source-backed setup support." in excerpts[0]["text"]
    assert len(excerpts[0]["text"]) <= 650


def test_selector_does_not_cross_sources_when_fact_ids_collide() -> None:
    brief = {
        "article_brief": {
            "voice_mode": "self_authored_blogger",
            "source_shape": "service_catalog",
            "source_use_mode": "selective",
            "section_count": 1,
            "sections": [{"section_id": "s1", "assigned_claim_ids": ["C001"]}],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {
                    "claim_id": "C001",
                    "claim": "Alpha plan includes source-backed setup support.",
                    "supporting_fact_ids": ["F004"],
                    "confidence": "high",
                    "preferred_expression": "Alpha setup support",
                    "risk_flags": [],
                }
            ]
        }
    }
    source_cards = [
        {"source_id": "wrong_source", "facts": [{"fact_id": "F004", "claim": "Gennai government AI implementation details.", "source_span": "wrong:1"}]},
        {"source_id": "assigned_source", "facts": [{"fact_id": "F004", "claim": "Alpha plan includes source-backed setup support.", "source_span": "assigned:1"}]},
    ]
    source_packets = [
        {"source_id": "wrong_source", "source_type": "url", "title": "Wrong", "chunks": [{"chunk_id": "wrong_chunk", "source_id": "wrong_source", "source_type": "url", "text": "Gennai government AI implementation details.", "source_span_ids": ["wrong:1"], "source_locations": ["wrong:1"]}]},
        {"source_id": "assigned_source", "source_type": "manual", "title": "Assigned", "chunks": [{"chunk_id": "assigned_chunk", "source_id": "assigned_source", "source_type": "manual", "text": "Alpha plan includes source-backed setup support near this service overview.", "source_span_ids": ["assigned:1"], "source_locations": ["assigned:1"]}]},
    ]

    excerpts = build_selected_source_excerpts_v2(brief, knowledge_pack, source_cards, source_packets)

    assert len(excerpts) == 1
    assert excerpts[0]["source_id"] == "assigned_source"
    assert "Alpha plan" in excerpts[0]["text"]
    assert "Gennai" not in excerpts[0]["text"]


def test_company_intro_thin_selected_material_adds_high_novelty_support_without_more_slots() -> None:
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "source_shape": "announcement_details",
            "source_use_mode": "selective",
            "section_count": 2,
            "article_goal": "Use ShortHint only if it helps the ending.",
            "sections": [
                {"section_id": "S1", "assigned_claim_ids": ["C002"]},
                {"section_id": "S2", "assigned_claim_ids": ["C008"]},
            ],
            "unassigned_claim_ids": ["C010", "C012", "C014"],
        }
    }
    knowledge_pack, source_cards, source_packets = _company_intro_material_fixture(
        short_final_support=True,
        second_final_support=False,
    )

    excerpts = build_selected_source_excerpts_v2(brief, knowledge_pack, source_cards, source_packets)

    claim_ids = [excerpt["claim_ids"][0] for excerpt in excerpts]
    total_chars = sum(len(excerpt["text"]) for excerpt in excerpts)
    assert claim_ids[:2] == ["C002", "C008"]
    assert set(claim_ids) == {"C002", "C008", "C012", "C014"}
    assert total_chars == 2600
    assert len(excerpts) == 4
    assert "C010" not in claim_ids


def test_company_intro_selector_does_not_broaden_already_saturated_material() -> None:
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "source_shape": "announcement_details",
            "source_use_mode": "selective",
            "section_count": 2,
            "article_goal": "Use HintOne and HintTwo only if they help the ending.",
            "sections": [
                {"section_id": "S1", "assigned_claim_ids": ["C002"]},
                {"section_id": "S2", "assigned_claim_ids": ["C008"]},
            ],
            "unassigned_claim_ids": ["C010", "C011", "C012"],
        }
    }
    knowledge_pack, source_cards, source_packets = _company_intro_material_fixture(
        short_final_support=False,
        second_final_support=True,
    )

    excerpts = build_selected_source_excerpts_v2(brief, knowledge_pack, source_cards, source_packets)

    claim_ids = [excerpt["claim_ids"][0] for excerpt in excerpts]
    total_chars = sum(len(excerpt["text"]) for excerpt in excerpts)
    assert claim_ids[:2] == ["C002", "C008"]
    assert set(claim_ids) == {"C002", "C008", "C010", "C011"}
    assert total_chars == 2600
    assert "C012" not in claim_ids


def _company_intro_material_fixture(
    *,
    short_final_support: bool,
    second_final_support: bool,
) -> tuple[dict, list[dict], list[dict]]:
    claim_texts = {
        "C002": "Assigned seafood processing material for section one.",
        "C008": "Assigned frozen food operations material for section two.",
        "C010": "ShortHint ending support material.",
        "C011": "HintTwo saturated ending support material.",
        "C012": "Mission source philosophy material with daily food continuity.",
        "C014": "Value source posture material with partner health and growth.",
    }
    confirmed_facts = [
        {
            "claim_id": claim_id,
            "claim": text,
            "supporting_fact_ids": [claim_id.replace("C", "F")],
            "preferred_expression": text,
            "risk_flags": [],
        }
        for claim_id, text in claim_texts.items()
    ]
    source_cards = [
        {
            "source_id": "company",
            "facts": [
                {
                    "fact_id": claim_id.replace("C", "F"),
                    "claim": text,
                    "source_span": claim_id.lower(),
                }
                for claim_id, text in claim_texts.items()
            ],
        }
    ]
    chunks = []
    for claim_id, text in claim_texts.items():
        chunk_text = _long_source_text(text, claim_id)
        if claim_id == "C010" and short_final_support:
            chunk_text = text
        if claim_id == "C011" and not second_final_support:
            chunk_text = text.replace("HintTwo", "Unused")
        chunks.append(
            {
                "chunk_id": f"{claim_id.lower()}_chunk",
                "source_id": "company",
                "source_type": "url",
                "text": chunk_text,
                "source_span_ids": [claim_id.lower()],
                "source_locations": [claim_id.lower()],
            }
        )
    return (
        {"article_knowledge_pack": {"confirmed_facts": confirmed_facts}},
        source_cards,
        [{"source_id": "company", "source_type": "url", "title": "Company", "chunks": chunks}],
    )


def _long_source_text(anchor: str, claim_id: str) -> str:
    topic = {
        "C002": "seafood cold chain regional kitchen logistics",
        "C008": "frozen meal preparation manufacturing quality",
        "C010": "ending support company outline closing",
        "C011": "saturated second ending support detail",
        "C012": "mission philosophy daily table continuity",
        "C014": "value posture partner health growth",
    }[claim_id]
    return (anchor + " " + (topic + " ") * 80).strip()
