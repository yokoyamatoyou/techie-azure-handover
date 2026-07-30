from __future__ import annotations

from typing import Any

from app.services.llm_client import LLMClient
from app.services.schema_validator import validate_payload


class KnowledgePackIntegrator:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def integrate(self, source_cards: list[dict[str, Any]]) -> dict[str, Any]:
        result = self.client.generate_json(
            "knowledge_pack_integration",
            "Merge source cards into confirmed claims and conflicts. Do not add unsupported facts.",
            {"source_cards": source_cards},
            "knowledge_pack.schema.json",
        )
        validate_payload("knowledge_pack.schema.json", result)
        return result
