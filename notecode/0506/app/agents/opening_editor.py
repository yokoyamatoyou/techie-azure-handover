from __future__ import annotations

from typing import Any

from app.services.llm_client import LLMClient
from app.services.editor_stage_instructions import build_editor_stage_instructions


BASE_INSTRUCTIONS = (
    "Return the complete Markdown article. Improve only the opening; copy all later sections unchanged. Do not explain."
)


class OpeningEditor:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def edit(
        self,
        article_text: str,
        article_brief: dict[str, Any],
        knowledge_pack: dict[str, Any],
    ) -> str:
        instructions = build_editor_stage_instructions("opening_editor", BASE_INSTRUCTIONS, article_brief)
        return self.client.generate_text(
            "opening_editor",
            instructions,
            {"article_text": article_text, "article_brief": article_brief, "knowledge_pack": knowledge_pack},
        )
