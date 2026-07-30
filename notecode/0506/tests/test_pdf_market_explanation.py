from app.services.local_draft_renderer import render_local_draft
from app.services.local_source_card_builder import build_local_source_card


def test_pdf_source_card_samples_late_pages_for_horizontal_slide_pdf():
    chunks = [
        {"text": f"{index}ページ目の補足説明です。", "source_locations": [f"p.{index}"]}
        for index in range(1, 33)
    ]
    chunks[13]["text"] = "Business Model Canvas\n価値提案と顧客を整理します。"
    chunks[19]["text"] = "Marketingの本質\n仲間を増やしていく。"
    chunks[27]["text"] = "市場性 (Marketability)\n自ら市場を見出して定義する。"
    packet = {
        "source_id": "pdf_test",
        "source_type": "pdf",
        "title": "講義資料",
        "chunks": chunks,
        "warnings": [],
        "metadata": {"extraction_method": "pymupdf_text_blocks", "extraction_confidence": "high"},
    }

    card = build_local_source_card(packet)
    claims = "。".join(fact["claim"] for fact in card["facts"])
    locations = {fact["source_span"] for fact in card["facts"]}

    assert "Business Model Canvas" in claims
    assert "Marketingは" in claims
    assert "市場性" in claims
    assert {"p.14", "p.20", "p.28"} <= locations


def test_market_explanation_draft_uses_explanatory_opening_and_close():
    brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "narrator": "私たち",
            "sections": [
                {
                    "heading": "ビジネスモデルを考える視点",
                    "assigned_claim_ids": ["C001", "C002", "C003"],
                }
            ],
        }
    }
    pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "preferred_expression": "Business Model Canvas"},
                {"claim_id": "C002", "preferred_expression": "Marketingの本質"},
                {"claim_id": "C003", "preferred_expression": "市場性 (Marketability)"},
            ]
        }
    }

    article = render_local_draft(brief, pack)

    assert "価値の届け方と市場の見立て方" in article
    assert "Business Model Canvasは" in article
    assert "身近な事業を一つ選び" in article
