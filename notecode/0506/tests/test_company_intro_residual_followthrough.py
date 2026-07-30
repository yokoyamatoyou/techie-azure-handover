from __future__ import annotations

from app.services.company_intro_followthrough import company_intro_selected_excerpt_floor_followthrough
from app.services.draft_followthrough import body_chars_excluding_headings


def test_company_intro_followthrough_uses_residual_unassigned_claims_after_assigned_cap() -> None:
    draft = "# Company\n\n## About\n\nShort source-backed intro."
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 450,
            "narrator": "私たち",
            "self_viewpoint_owner": "kintone",
            "sections": [{"section_id": "s1", "heading": "About"}],
            "claim_allocation": [{"section_id": "s1", "claim_ids": [f"C{i:03d}" for i in range(1, 11)]}],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "kintoneは、アプリ作成の接点を提供します。",
        }
    ]
    assigned_facts = [
        {
            "claim_id": f"C{i:03d}",
            "preferred_expression": f"kintoneは私たちの事業に関わるsource-backed claim {i}です。",
        }
        for i in range(1, 11)
    ]
    residual_facts = [
        {
            "claim_id": "C011",
            "preferred_expression": "kintoneはAIとノーコードでデータベース機能とコミュニケーション機能を提供します。",
        },
        {
            "claim_id": "C012",
            "preferred_expression": "kintoneはプランやコースの確認に関わるsource-backedな料金情報を提供します。",
        },
    ]
    knowledge_pack = {"article_knowledge_pack": {"confirmed_facts": assigned_facts + residual_facts}}

    result = company_intro_selected_excerpt_floor_followthrough(draft, brief, excerpts, knowledge_pack)

    assert "データベース機能" in result
    assert "料金情報" in result
    assert body_chars_excluding_headings(result) >= 450


def test_company_intro_followthrough_adds_live_residual_floor_buffer() -> None:
    draft = "# Company\n\n## About\n\n" + ("私たちはsource-backedな説明を続けます。" * 29)
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 900,
            "narrator": "私たち",
            "self_viewpoint_owner": "kintoneのサービス提供者",
            "sections": [{"section_id": "s1", "heading": "About"}],
            "claim_allocation": [{"section_id": "s1", "claim_ids": ["C001", "C002"]}],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "kintone（キントーン）は、AIとノーコード・ローコードで現場の業務にフィットする業務アプリがつくれるサービスです。",
        }
    ]
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "preferred_expression": "kintone（キントーン）は、AIとノーコード・ローコードで業務アプリがつくれる"},
                {"claim_id": "C002", "preferred_expression": "アプリには、データを蓄積したり一覧できるデータベース機能、業務を円滑に進めるためのコミュニケーション機能、業務の進捗を見える化できるプロセス管理機能があります"},
                {"claim_id": "C003", "preferred_expression": "ご利用規模や目的に応じて、3つのコースをご用意しています"},
                {"claim_id": "C004", "preferred_expression": "初期費用無料で、1か月から契約可能です"},
            ]
        }
    }

    result = company_intro_selected_excerpt_floor_followthrough(draft, brief, excerpts, knowledge_pack)

    assert "データベース機能" in result
    assert "3つのコース" in result
    assert "source_documents" not in result
    assert "同社" not in result
    assert body_chars_excluding_headings(result) >= 996
