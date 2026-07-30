from app.services.local_llm_client import LocalPipelineClient


def test_local_article_brief_allocates_claims_contiguously_by_section():
    client = LocalPipelineClient()
    claims = [
        {
            "claim_id": f"C{index:03d}",
            "claim": f"claim {index}",
            "supporting_fact_ids": [f"F{index:03d}"],
            "confidence": "medium",
            "preferred_expression": f"claim {index}",
            "risk_flags": [],
        }
        for index in range(1, 8)
    ]

    result = client.generate_json(
        "article_brief_builder",
        "",
        {
            "knowledge_pack": {"article_knowledge_pack": {"confirmed_facts": claims}},
            "genre_id": "company_service_intro",
            "persona_id": "in_house_brand_blog_editor",
            "writer_role": "in_house_brand_blog_editor",
            "viewpoint_mode": "self_perspective",
            "style_profile": {},
            "editor_profile": {},
            "narrator": "私たち",
            "qa_policy_id": "self_perspective_blog_default",
            "target_reader": "読者",
            "article_goal": "紹介",
        },
        "article_brief.schema.json",
    )

    sections = result["article_brief"]["sections"]
    assert sections[0]["assigned_claim_ids"] == ["C001", "C002", "C003"]
    assert sections[1]["assigned_claim_ids"] == ["C004", "C005", "C006"]
    assert sections[2]["assigned_claim_ids"] == ["C007"]
