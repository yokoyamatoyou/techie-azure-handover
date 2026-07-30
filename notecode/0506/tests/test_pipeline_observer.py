from app.evals.pipeline_observer import ObservedLLMClient, PipelineObserver
from app.services.local_llm_client import LocalPipelineClient


def test_observed_llm_client_records_draft_writer_payload_summary():
    observer = PipelineObserver()
    client = ObservedLLMClient(LocalPipelineClient(), observer)
    article_brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "persona_id": "in_house_brand_blog_editor",
            "writer_role": "in_house_brand_blog_editor",
            "narrator": "私たち",
            "style_profile_id": "note_hatena_owned_media_soft",
            "editor_profile_id": "note_hatena_structural_editor",
            "sections": [],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "preferred_expression": "私たちはデータ入力を支援しています。"}
            ]
        }
    }

    client.generate_text(
        "draft_writer",
        "Write",
        {"article_brief": article_brief, "knowledge_pack": knowledge_pack},
    )

    report = observer.report()
    call = report["calls"][0]
    assert call["stage_name"] == "draft_writer"
    assert call["payload_summary"]["raw_source_packets_passed"] is False
    assert call["payload_summary"]["structured_claims_passed"] is True
    assert call["payload_summary"]["style_profile_id"] == "note_hatena_owned_media_soft"
