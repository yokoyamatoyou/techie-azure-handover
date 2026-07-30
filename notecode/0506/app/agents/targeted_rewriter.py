from __future__ import annotations

from typing import Any

from app.services.llm_client import LLMClient


class TargetedRewriter:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def rewrite(self, article_text: str, quality_check: dict[str, Any], article_brief: dict[str, Any]) -> str:
        if not quality_check["quality_check"]["rewrite_needed"]:
            return article_text
        return self.client.generate_text(
            "targeted_rewriter",
            "Return only the complete edited Markdown article. Rewrite only flagged spans. Do not add facts or change claim IDs. Do not explain.",
            {"article_text": article_text, "quality_check": quality_check, "article_brief": article_brief},
        )
