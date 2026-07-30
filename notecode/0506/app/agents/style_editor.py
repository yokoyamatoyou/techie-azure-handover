from __future__ import annotations

from typing import Any

from app.services.llm_client import LLMClient
from app.services.editor_stage_instructions import build_editor_stage_instructions


BASE_INSTRUCTIONS = (
    "Return only the complete edited Markdown article. Improve readability without changing facts, names, dates, numbers, or claim IDs. Do not explain."
)


class StyleEditor:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def edit(self, draft: str, article_brief: dict[str, Any]) -> str:
        instructions = build_editor_stage_instructions("style_editor", BASE_INSTRUCTIONS, article_brief)
        return self.client.generate_text(
            "style_editor",
            instructions,
            {"draft": draft, "article_brief": article_brief},
        )
