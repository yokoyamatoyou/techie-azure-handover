from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.llm_client import LLMClient
from app.services.schema_validator import validate_payload
from app.services.source_preprocessor import GenerationSourcePacket


class SourceCardExtractor:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def extract(self, packet: GenerationSourcePacket) -> dict[str, Any]:
        payload = {"source_packet": asdict(packet)}
        result = self.client.generate_json(
            "source_card_extraction",
            "Extract source-grounded facts only. Do not infer missing facts.",
            payload,
            "source_card.schema.json",
        )
        validate_payload("source_card.schema.json", result)
        return result
