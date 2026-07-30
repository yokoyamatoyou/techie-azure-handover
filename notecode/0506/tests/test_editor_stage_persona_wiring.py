from pathlib import Path
from typing import Any

from app.agents.opening_editor import OpeningEditor
from app.agents.structural_editor import StructuralEditor
from app.evals.pipeline_observer import ObservedLLMClient, PipelineObserver
from app.services.editor_stage_instructions import summarize_editor_stage_contract
from app.services.local_llm_client import LocalPipelineClient
from app.services.pipeline_logging import PipelineLogger
from app.services.pipeline_runner import BlogPipelineRunner


class RecordingTextClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_json(self, stage_name, instructions, payload, schema_name):
        raise AssertionError("JSON generation is not used in these editor wiring tests")

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        self.calls.append({"stage_name": stage_name, "instructions": instructions, "payload": payload})
        return payload.get("article_text") or payload.get("draft") or ""


def _brief(genre_id: str = "company_service_intro", narrator: str = "私たち") -> dict[str, Any]:
    return {
        "article_brief": {
            "genre_id": genre_id,
            "persona_id": "test",
            "writer_role": "test",
            "narrator": narrator,
            "self_viewpoint_owner": narrator,
            "style_profile_id": "note_hatena_owned_media_soft",
            "editor_profile_id": "note_hatena_structural_editor",
            "sections": [
                {
                    "section_id": "s1",
                    "heading": "お客様の状況",
                    "purpose": "before material",
                    "assigned_claim_ids": ["C001"],
                },
                {
                    "section_id": "s2",
                    "heading": "私たちが行ったこと",
                    "purpose": "after material",
                    "assigned_claim_ids": ["C002"],
                },
            ],
        }
    }


def _knowledge_pack() -> dict[str, Any]:
    return {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {
                    "claim_id": "C001",
                    "claim": "私たちは申請業務をオンラインで扱えるようにしました。",
                    "supporting_fact_ids": ["F001"],
                },
                {
                    "claim_id": "C002",
                    "claim": "私たちは導入後の声を整理しています。",
                    "supporting_fact_ids": ["F002"],
                }
            ],
            "source_card_ids": ["S001"],
            "do_not_infer": ["根拠のない成果を足さない"],
        }
    }


def _daily_activity_knowledge_pack() -> dict[str, Any]:
    return {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "claim": "2026年3月10日13:30-16:30に物撮りワークショップを開催しました。"},
                {"claim_id": "C002", "claim": "会場は宮城県産業技術総合センターBW-03室でした。"},
                {"claim_id": "C003", "claim": "クリップライト、デスクランプ、黒いボール紙、トレーシングペーパーを使いました。"},
                {"claim_id": "C004", "claim": "プラスチックのおもちゃ、透明な瓶、反射の強い金属部品を撮影対象にしました。"},
                {"claim_id": "C005", "claim": "講義から実技へ進む二部構成でした。"},
                {"claim_id": "C006", "claim": "受講料は1,200円で、定員は5人でした。"},
            ],
            "source_card_ids": ["S001"],
            "do_not_infer": ["参加者の感情や成果を根拠なく足さない"],
        }
    }


def test_opening_editor_wires_rendered_genre_persona_without_second_pass():
    client = RecordingTextClient()

    OpeningEditor(client).edit("# 見出し\n\n本文です。", _brief(), _knowledge_pack())

    instructions = client.calls[0]["instructions"]
    assert client.calls[0]["stage_name"] == "opening_editor"
    assert "Stage boundary: improve the opening/front half only" in instructions
    assert "# Editor Persona Contract" in instructions
    assert "Role: 会社・サービス提供者側の社内ブロガー" in instructions
    assert "Second pass: conditional:source-backed 後半編集者" in instructions
    assert "## Conditional Second Editor" not in instructions


def test_structural_editor_wires_non_announcement_second_editor_persona():
    client = RecordingTextClient()

    StructuralEditor(client).edit("# 見出し\n\n本文です。", _brief("comparison_guide"), _knowledge_pack())

    instructions = client.calls[0]["instructions"]
    assert client.calls[0]["stage_name"] == "structural_editor"
    assert "Stage boundary: focus on late-half structure and endings" in instructions
    assert "announcement/list guidance" not in instructions
    assert "Role: 選定アドバイザー" in instructions
    assert "## Conditional Second Editor" in instructions
    assert "Role: 根拠編集者" in instructions
    assert "source_fact と llm_general_context の分離" in instructions


def test_structural_editor_keeps_announcement_second_pass_disabled():
    client = RecordingTextClient()

    StructuralEditor(client).edit("# お知らせ\n\n本文です。", _brief("announcement", "当社"), _knowledge_pack())

    instructions = client.calls[0]["instructions"]
    assert "Role: 事実整理係" in instructions
    assert "Second pass: not_required" in instructions
    assert "## Conditional Second Editor" not in instructions


def test_structural_editor_payload_carries_claim_material_without_raw_sources():
    client = RecordingTextClient()

    StructuralEditor(client).edit("# 事例\n\n本文です。", _brief("case_study"), _knowledge_pack())

    payload = client.calls[0]["payload"]
    assert payload["knowledge_pack"]["article_knowledge_pack"]["confirmed_facts"][0]["claim_id"] == "C001"
    assert payload["knowledge_pack"]["article_knowledge_pack"]["confirmed_facts"][0]["supporting_fact_ids"] == ["F001"]
    assert payload["knowledge_pack"]["article_knowledge_pack"]["source_card_ids"] == ["S001"]
    assert payload["knowledge_pack"]["section_claim_material"][0]["heading"] == "お客様の状況"
    assert payload["knowledge_pack"]["section_claim_material"][1]["heading"] == "私たちが行ったこと"
    assert "source_documents" not in payload
    assert "source_packets" not in payload


def test_daily_activity_structural_editor_payload_carries_scene_preservation_contract():
    client = RecordingTextClient()

    StructuralEditor(client).edit("# 日々\n\n本文です。", _brief("daily_activity"), _daily_activity_knowledge_pack())

    instructions = client.calls[0]["instructions"]
    payload = client.calls[0]["payload"]
    scene_contract = payload["knowledge_pack"]["scene_material_preservation"]
    matched = scene_contract["matched_source_near_material"]

    assert "preserve source-near scene material" in instructions
    assert "announcement/list guidance" in instructions
    assert scene_contract["applies_to"] == "daily_activity_structural_editor"
    assert scene_contract["notice_list_drift_disallowed"] is True
    assert scene_contract["minimum_categories_to_keep_when_present"] == 4
    assert set(scene_contract["preserve_categories"]) == {
        "time",
        "place",
        "object_tool",
        "action",
        "sequence",
        "constraint",
    }
    assert {"time", "place", "object_tool", "action", "sequence", "constraint"} <= set(matched)
    assert "source_documents" not in payload
    assert "source_packets" not in payload
    assert "source_cards" not in payload


def test_non_daily_structural_editor_payload_does_not_add_scene_contract():
    client = RecordingTextClient()

    StructuralEditor(client).edit("# 比較\n\n本文です。", _brief("comparison_guide"), _daily_activity_knowledge_pack())

    assert "scene_material_preservation" not in client.calls[0]["payload"]["knowledge_pack"]


def test_pipeline_observer_records_editor_persona_stage_instructions(tmp_path: Path):
    observer = PipelineObserver()
    client = ObservedLLMClient(LocalPipelineClient(), observer)
    runner = BlogPipelineRunner(client=client, logger=PipelineLogger("editor_wiring", artifacts_dir=tmp_path))

    runner.run_manual_sources(
        [("会社メモ", "私たちは食品の相談を受け、地域の店舗に商品を届けています。" * 8)],
        genre_id="company_service_intro",
        narrator="私たち",
    )

    report = observer.report()
    stages = report["stages"]
    assert "opening_editor" in stages
    assert "global_consistency_editor" in stages
    assert "style_editor" in stages
    assert "structural_editor" in stages
    structural_call = next(call for call in report["calls"] if call["stage_name"] == "structural_editor")
    style_call = next(call for call in report["calls"] if call["stage_name"] == "style_editor")
    assert "Role: source-backed 後半編集者" in structural_call["instructions"]
    assert "For company_service_intro, deepen the back half" in structural_call["instructions"]
    assert structural_call["payload_summary"]["knowledge_claim_count"] > 0
    assert "source-backed meaning density, not filler" in style_call["instructions"]


def test_editor_stage_contract_summary_keeps_api_closed_in_current_owner():
    summary = summarize_editor_stage_contract("structural_editor", _brief("daily_activity"))

    assert summary["second_pass"] is True
    assert summary["preflight_pass"] is True
    assert summary["api_send_allowed_current_owner"] is False
    assert summary["prompt_line_count"] <= 60
    assert summary["prompt_char_count"] <= 2600
