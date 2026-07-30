from __future__ import annotations

from typing import Any

from app.agents.draft_writer import DraftWriter
from app.services.draft_followthrough import body_chars_excluding_headings


class RecordingClient:
    def __init__(self, response: str) -> None:
        self.calls: list[dict[str, Any]] = []
        self.response = response

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        self.calls.append({"stage_name": stage_name, "instructions": instructions, "payload": payload})
        return self.response


def test_draft_writer_applies_company_intro_selected_excerpt_floor_followthrough() -> None:
    client = RecordingClient("# 会社紹介\n\n## 私たちの仕事\n\n短い紹介です。")
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 300,
            "narrator": "私たち",
            "self_viewpoint_owner": "山陰酸素",
            "sections": [{"section_id": "s1", "heading": "私たちの仕事"}],
            "claim_allocation": [{"section_id": "s1", "claim_ids": ["C001", "C002"]}],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "山陰酸素は、LPガス、産業用ガス、医療用ガスなどを地域の暮らしと事業活動に向けて供給しています。\n"
            "山陰酸素は、家庭、工場、医療現場、研究開発の場面に向けた商品とサービスを扱っています。\n"
            "山陰酸素は、点検、配送、相談対応を日々の接点として続けています。",
        }
    ]
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "preferred_expression": "山陰酸素はLPガス、産業用ガス、医療用ガスを扱っています"},
                {"claim_id": "C002", "preferred_expression": "山陰酸素は点検、配送、相談対応を日々の接点として続けています"},
                {"claim_id": "C003", "preferred_expression": "山陰酸素は地域社会の基盤を支える姿勢を大切にしています"},
                {"claim_id": "C004", "preferred_expression": "山陰酸素は家庭、工場、医療現場、研究開発の場面に関わる商品を扱っています"},
                {"claim_id": "C005", "preferred_expression": "山陰酸素は地域の暮らしと事業活動に向けてエネルギーを提供しています"},
                {"claim_id": "C006", "preferred_expression": "山陰酸素は安全な利用を支えるための対応を継続しています"},
            ]
        }
    }

    result = DraftWriter(client).write(brief, knowledge_pack, excerpts)

    assert "私たちは、LPガス、産業用ガス、医療用ガス" in result
    assert "私たちは点検、配送、相談対応" in result
    assert body_chars_excluding_headings(result) >= 300
    assert "source_documents" not in client.calls[0]["payload"]
