from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.llm_client import LLMClient


@dataclass
class ObservedCall:
    index: int
    stage_name: str
    call_type: str
    instructions: str
    payload_summary: dict[str, Any]
    output_summary: dict[str, Any]


@dataclass
class PipelineObserver:
    calls: list[ObservedCall] = field(default_factory=list)

    def record(
        self,
        stage_name: str,
        call_type: str,
        instructions: str,
        payload: dict[str, Any],
        output: Any,
    ) -> None:
        self.calls.append(
            ObservedCall(
                index=len(self.calls) + 1,
                stage_name=stage_name,
                call_type=call_type,
                instructions=instructions,
                payload_summary=summarize_payload(stage_name, payload),
                output_summary=summarize_output(stage_name, output),
            )
        )

    def report(self) -> dict[str, Any]:
        stages = [call.stage_name for call in self.calls]
        return {
            "call_count": len(self.calls),
            "stages": stages,
            "checks": {
                "draft_writer_called": "draft_writer" in stages,
                "opening_editor_called": "opening_editor" in stages,
                "global_consistency_editor_called": "global_consistency_editor" in stages,
                "style_editor_called": "style_editor" in stages,
                "structural_editor_called": "structural_editor" in stages,
                "targeted_rewriter_called": "targeted_rewriter" in stages,
            },
            "calls": [
                {
                    "index": call.index,
                    "stage_name": call.stage_name,
                    "call_type": call.call_type,
                    "instructions": call.instructions,
                    "payload_summary": call.payload_summary,
                    "output_summary": call.output_summary,
                }
                for call in self.calls
            ],
        }

    def write(self, path: Path) -> Path:
        path.write_text(json.dumps(self.report(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path


class ObservedLLMClient:
    def __init__(self, inner: LLMClient, observer: PipelineObserver) -> None:
        self.inner = inner
        self.observer = observer

    def generate_json(
        self,
        stage_name: str,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        output = self.inner.generate_json(stage_name, instructions, payload, schema_name)
        self.observer.record(stage_name, "json", instructions, payload, output)
        return output

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        output = self.inner.generate_text(stage_name, instructions, payload)
        self.observer.record(stage_name, "text", instructions, payload, output)
        return output


def summarize_payload(stage_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if stage_name == "source_card_extraction":
        packet = payload["source_packet"]
        return {
            "source_id": packet["source_id"],
            "source_type": packet["source_type"],
            "title": packet["title"],
            "chunk_count": len(packet["chunks"]),
            "included_text_chars": packet["metadata"].get("included_text_chars"),
            "extraction_confidence": packet["metadata"].get("extraction_confidence"),
            "source_over_limit": packet["metadata"].get("source_over_limit"),
            "warnings": packet.get("warnings", []),
        }
    if stage_name == "knowledge_pack_integration":
        cards = payload["source_cards"]
        return {
            "source_card_count": len(cards),
            "fact_count": sum(len(card.get("facts", [])) for card in cards),
            "source_ids": [card.get("source_id") for card in cards],
        }
    if stage_name == "article_brief_builder":
        claims = payload["knowledge_pack"]["article_knowledge_pack"]["confirmed_facts"]
        return {
            "genre_id": payload["genre_id"],
            "persona_id": payload["persona_id"],
            "writer_role": payload["writer_role"],
            "viewpoint_mode": payload["viewpoint_mode"],
            "narrator": payload["narrator"],
            "style_profile_id": payload.get("style_profile", {}).get("style_profile_id"),
            "editor_profile_id": payload.get("editor_profile", {}).get("editor_profile_id"),
            "confirmed_claim_count": len(claims),
        }
    if stage_name == "draft_writer":
        brief = payload["article_brief"]["article_brief"]
        claims = payload["knowledge_pack"]["article_knowledge_pack"]["confirmed_facts"]
        return {
            "raw_source_packets_passed": "source_packets" in payload,
            "structured_claims_passed": bool(claims),
            "confirmed_claim_count": len(claims),
            "genre_id": brief["genre_id"],
            "persona_id": brief["persona_id"],
            "writer_role": brief["writer_role"],
            "narrator": brief["narrator"],
            "style_profile_id": brief.get("style_profile_id"),
            "editor_profile_id": brief.get("editor_profile_id"),
            "section_count": len(brief.get("sections", [])),
        }
    if stage_name in {"opening_editor", "global_consistency_editor", "style_editor", "structural_editor", "targeted_rewriter"}:
        key = "draft" if stage_name == "style_editor" else "article_text"
        text = payload.get(key, "")
        brief = payload.get("article_brief", {}).get("article_brief", {})
        return {
            "input_chars": len(text),
            "narrator": brief.get("narrator"),
            "style_profile_id": brief.get("style_profile_id"),
            "editor_profile_id": brief.get("editor_profile_id"),
            "knowledge_claim_count": len(payload.get("knowledge_pack", {}).get("article_knowledge_pack", {}).get("confirmed_facts", [])),
            "issue_count": len(payload.get("quality_check", {}).get("quality_check", {}).get("issues", [])),
        }
    return {"payload_keys": sorted(payload)}


def summarize_output(stage_name: str, output: Any) -> dict[str, Any]:
    if isinstance(output, str):
        return {"output_chars": len(output), "line_count": len(output.splitlines())}
    if stage_name == "source_card_extraction":
        return {"fact_count": len(output.get("facts", [])), "warning_count": len(output.get("warnings", []))}
    if stage_name == "knowledge_pack_integration":
        pack = output["article_knowledge_pack"]
        return {"confirmed_claim_count": len(pack["confirmed_facts"]), "conflict_count": len(pack["conflicts"])}
    if stage_name == "article_brief_builder":
        brief = output["article_brief"]
        return {
            "section_count": len(brief["sections"]),
            "target_length_chars": brief.get("target_length_chars"),
            "style_profile_id": brief.get("style_profile_id"),
            "editor_profile_id": brief.get("editor_profile_id"),
        }
    return {"output_type": type(output).__name__}
