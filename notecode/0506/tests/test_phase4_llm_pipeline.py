import threading
import time
from dataclasses import asdict
from pathlib import Path

from app.agents.japanese_quality_checker import JapaneseQualityChecker
import app.services.pipeline_runner as pipeline_runner
from app.services.local_source_card_builder import build_local_source_card
from app.services.local_llm_client import LocalPipelineClient
from app.services.pipeline_logging import PipelineLogger
from app.services.pipeline_runner import BlogPipelineRunner


def test_p4_s1_to_s8_fixture_pipeline_preserves_claim_traceability(tmp_path: Path):
    logger = PipelineLogger("phase4_test", artifacts_dir=tmp_path)
    runner = BlogPipelineRunner(client=LocalPipelineClient(), logger=logger)

    result = runner.run_manual_sources(
        [("会社メモ", "私たちは2018年に創業しました。地域の相談を受けています。初回相談で状況を確認します。")],
        narrator="私たち",
    )

    claims = result.knowledge_pack["article_knowledge_pack"]["confirmed_facts"]
    sections = result.article_brief["article_brief"]["sections"]
    assigned_claim_ids = [
        claim_id
        for section in sections
        for claim_id in section["assigned_claim_ids"]
    ]

    assert result.source_cards[0]["facts"][0]["source_span"] == "manual:1"
    assert claims[0]["supporting_fact_ids"] == ["F001"]
    assert set(assigned_claim_ids) == {claim["claim_id"] for claim in claims}
    assert len(assigned_claim_ids) == len(claims)
    assert result.article_brief["article_brief"]["target_length_chars"] == 1200
    assert result.article_brief["article_brief"]["source_thickness"] == "medium"
    assert result.article_brief["article_brief"]["style_profile_id"] == "note_hatena_owned_media_soft"
    assert result.article_brief["article_brief"]["style_edit_policy"]["subject_omission_policy"] == "clear_context_only"
    assert result.article_brief["article_brief"]["editor_profile_id"] == "note_hatena_structural_editor"
    assert result.article_brief["article_brief"]["editor_pass_policy"]["focus_late_half"] is True
    assert result.article_brief["article_brief"]["self_viewpoint_owner"] == "私たち"
    assert result.article_brief["article_brief"]["editorial_bridge_policy"]["enabled"] is False
    assert result.article_brief["article_brief"]["editorial_bridge_policy"]["max_items"] == 0
    assert result.article_brief["article_brief"]["editorial_bridge_candidates"] == []
    assert "沿革や歩みには" not in result.final_article
    assert "相談前" not in result.final_article
    assert "同社" not in result.final_article
    assert result.quality_check["quality_check"]["score"] >= 80
    assert (logger.run_dir / "structural_edited_draft.md").exists()
    assert (logger.run_dir / "editor_pass_report.json").exists()
    assert (logger.run_dir / "latest_generation_output.md").exists()
    assert (logger.run_dir / "latest_generation_quality_report.json").exists()
    progress = (logger.run_dir / "progress.json").read_text(encoding="utf-8")
    assert '"stage": "completed"' in progress
    assert '"percent": 100' in progress


def test_source_card_extraction_runs_in_parallel_and_preserves_source_order(monkeypatch, tmp_path: Path):
    lock = threading.Lock()
    active = 0
    max_active = 0

    class SlowSourceCardExtractor:
        def __init__(self, _client):
            pass

        def extract(self, packet):
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            try:
                time.sleep(0.05)
                return build_local_source_card(asdict(packet))
            finally:
                with lock:
                    active -= 1

    monkeypatch.setenv("ROUTE_V_SOURCE_CARD_MAX_WORKERS", "2")
    monkeypatch.setattr(pipeline_runner, "SourceCardExtractor", SlowSourceCardExtractor)
    logger = PipelineLogger("parallel_source_cards", artifacts_dir=tmp_path)
    runner = BlogPipelineRunner(client=LocalPipelineClient(), logger=logger)

    result = runner.run_manual_sources(
        [
            ("source A", "私たちはAの資料整理を支援しています。" * 12),
            ("source B", "私たちはBの入力支援を提供しています。" * 12),
        ],
        narrator="私たち",
    )

    assert max_active == 2
    assert [card["title"] for card in result.source_cards] == ["source A", "source B"]


def test_p4_s7_quality_checker_flags_ai_like_and_viewpoint_leakage():
    brief = {
        "article_brief": {
            "brief_id": "b1",
            "genre_id": "company_service_intro",
            "persona_id": "in_house_brand_blog_editor",
            "writer_role": "in_house_brand_blog_editor",
            "viewpoint_mode": "self_perspective",
            "target_reader": "読者",
            "article_goal": "紹介",
            "narrator": "私たち",
            "self_viewpoint_owner": "株式会社A",
            "qa_policy_id": "self_perspective_blog_default",
            "style_profile_id": "note_hatena_owned_media_soft",
            "style_edit_policy": {
                "preferred_sentences_per_paragraph": 2,
                "max_sentences_per_paragraph": 3,
                "line_break_policy": "topic_shift_or_two_sentences",
                "subject_omission_policy": "clear_context_only",
                "ending_bucket_policy": "structural_variation",
                "protected_subject_terms": ["年", "月", "日", "円", "担当"],
            },
            "target_length_chars": 1200,
            "section_count": 1,
            "source_thickness": "medium",
            "claim_allocation": [],
            "sections": [
                {
                    "section_id": "s1",
                    "heading": "見出し",
                    "purpose": "確認",
                    "assigned_claim_ids": [],
                    "main_subject": "私たち",
                    "discourse_rules": [],
                }
            ],
            "style_rules": [],
            "forbidden_viewpoint_terms": ["同社"],
            "config_refs": [],
            "persona_refs": [],
        }
    }
    text = "同社は第一歩を支えます。また、第一歩を整えます。いかがでしたでしょうか。"

    quality = JapaneseQualityChecker().check(text, brief, {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "third_party_viewpoint_leakage" in issue_types
    assert "model_frequent_word" in issue_types
    assert "ai_like_phrase" in issue_types
    assert quality["quality_check"]["rewrite_needed"] is True


def test_quality_checker_flags_self_viewpoint_owner_mismatch():
    brief = {
        "article_brief": {
            "viewpoint_mode": "self_perspective",
            "narrator": "私たち",
            "self_viewpoint_owner": "京都工業株式会社",
        }
    }
    text = "私たちが公式サイトを見て整理すると、京都工業株式会社はデータ入力を行う会社です。"

    quality = JapaneseQualityChecker().check(text, brief, {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "viewpoint_owner_mismatch" in issue_types


def test_quality_checker_flags_low_density_reader_meta_sentences():
    brief = {
        "article_brief": {
            "viewpoint_mode": "self_perspective",
            "narrator": "私たち",
            "self_viewpoint_owner": "京都工業株式会社",
        }
    }
    text = (
        "まずは「どんな会社で、何を支えるのか」を知りたい方に、私たちの輪郭をお伝えしたいと思います。"
        "紙資料をデジタル化して使いやすい形にする場面を思い浮かべると、私たちのサービスのつながりが見えやすくなります。"
        "就活でまず知りたいのは、何を長く支えてきた会社かという入口です。"
    )

    quality = JapaneseQualityChecker().check(text, brief, {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "reader_instruction_meta_commentary" in issue_types
    assert "low_density_bridge_sentence" in issue_types
    assert "abstract_navigation_phrase" in issue_types


def test_quality_checker_allows_dense_source_fact_sentences():
    brief = {
        "article_brief": {
            "viewpoint_mode": "self_perspective",
            "narrator": "私たち",
            "self_viewpoint_owner": "京都工業株式会社",
        }
    }
    text = (
        "京都工業株式会社は、データ入力・スキャニング・RPA支援を提供しています。"
        "データ入力・スキャニングでは、紙資料をデジタル化し、希望するデータ形式で納品しています。"
    )

    quality = JapaneseQualityChecker().check(text, brief, {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "reader_instruction_meta_commentary" not in issue_types
    assert "low_density_bridge_sentence" not in issue_types
    assert "abstract_navigation_phrase" not in issue_types


def test_quality_checker_allows_source_backed_entrypoint_sentences():
    brief = {
        "article_brief": {
            "viewpoint_mode": "self_perspective",
            "narrator": "私たち",
            "self_viewpoint_owner": "株式会社A",
        }
    }
    text = (
        "アプリの作成方法には、ドラッグ＆ドロップ、AIチャット、テンプレート、Excel読み込みなど複数の入口があります。"
        "権限と連携は別の機能ですが、運用の入口と出口をそろえる話として読むと全体の流れが見えてきます。"
    )

    quality = JapaneseQualityChecker().check(text, brief, {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "reader_instruction_meta_commentary" not in issue_types
    assert "low_density_bridge_sentence" not in issue_types
    assert "abstract_navigation_phrase" not in issue_types


def test_quality_checker_flags_route_v_body_length_below_floor():
    brief = {
        "article_brief": {
            "viewpoint_mode": "self_perspective",
            "narrator": "私たち",
            "self_viewpoint_owner": "株式会社A",
            "body_length_floor_chars": 80,
        }
    }
    text = "# タイトル\n\n短い本文です。"

    quality = JapaneseQualityChecker().check(text, brief, {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "body_length_below_floor" in issue_types
    assert quality["quality_check"]["pass"] is False
    assert quality["quality_check"]["rewrite_needed"] is True


def test_quality_checker_flags_route_v_missing_h1():
    brief = {
        "article_brief": {
            "viewpoint_mode": "self_perspective",
            "narrator": "私たち",
            "self_viewpoint_owner": "株式会社A",
            "body_length_floor_chars": 1,
        }
    }
    text = "H1のない本文です。"

    quality = JapaneseQualityChecker().check(text, brief, {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "missing_h1" in issue_types
    assert "body_length_below_floor" not in issue_types
    assert quality["quality_check"]["pass"] is False
