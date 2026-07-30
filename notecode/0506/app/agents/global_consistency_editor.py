from __future__ import annotations

from typing import Any

from app.services.llm_client import LLMClient
from app.services.editor_stage_instructions import build_editor_stage_instructions


BASE_INSTRUCTIONS = (
    "Return only the complete edited Markdown article. Align voice and remove duplicate motifs without adding facts. Do not explain."
)


class GlobalConsistencyEditor:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def edit(self, article_text: str, article_brief: dict[str, Any]) -> str:
        instructions = build_editor_stage_instructions("global_consistency_editor", BASE_INSTRUCTIONS, article_brief)
        return self.client.generate_text(
            "global_consistency_editor",
            instructions,
            {"article_text": article_text, "article_brief": article_brief},
        )
