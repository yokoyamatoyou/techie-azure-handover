from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.agents.article_brief_builder import ArticleBriefBuilder
from app.agents.draft_writer import DraftWriter
from app.agents.global_consistency_editor import GlobalConsistencyEditor
from app.agents.opening_editor import OpeningEditor
from app.agents.japanese_quality_checker import JapaneseQualityChecker
from app.agents.knowledge_pack_integrator import KnowledgePackIntegrator
from app.agents.structural_editor import StructuralEditor
from app.agents.style_editor import StyleEditor
from app.agents.source_card_extractor import SourceCardExtractor
from app.services.editor_output_safety import deterministic_targeted_rewrite, guard_editor_output
from app.services.llm_client import LLMClient, select_default_llm_client
from app.services.pipeline_logging import PipelineLogger
from app.services.source_acquisition import ExtractedSource, ingest_manual_text
from app.services.source_excerpt_selector_v2 import build_selected_source_excerpts_v2
from app.services.source_preprocessor import build_generation_source_packets
from app.services.global_consistency_editor import build_global_consistency_report
from app.services.human_visible_surface_gate import check_human_visible_surface
from app.services.opening_editor import build_opening_edit_report
from app.services.structural_editor import build_structural_edit_report


SOURCE_CARD_MAX_WORKERS_ENV = "ROUTE_V_SOURCE_CARD_MAX_WORKERS"


@dataclass(frozen=True)
class BlogPipelineResult:
    final_article: str
    source_cards: list[dict[str, Any]]
    knowledge_pack: dict[str, Any]
    article_brief: dict[str, Any]
    quality_check: dict[str, Any]
    artifact_dir: Path
    draft: str
    opening_edited_draft: str
    global_consistency_edited_draft: str
    edited_draft: str
    structural_edited_draft: str


class BlogPipelineRunner:
    def __init__(self, client: LLMClient | None = None, logger: PipelineLogger | None = None) -> None:
        self.client = client or select_default_llm_client()
        self.logger = logger or PipelineLogger()
        bind_inflight_ledger = getattr(self.client, "set_inflight_ledger_path", None)
        if callable(bind_inflight_ledger):
            bind_inflight_ledger(self.logger.run_dir / "openai_inflight_ledger.jsonl")

    def run_manual_sources(
        self,
        sources: list[tuple[str, str]],
        genre_id: str = "company_service_intro",
        target_reader: str = "初めてサービスを知る読者",
        article_goal: str = "ソースに基づいて自然なブログ記事を作る",
        narrator: str | None = None,
        self_viewpoint_owner: str | None = None,
        blog_persona_profile: dict[str, Any] | None = None,
    ) -> BlogPipelineResult:
        extracted = [ingest_manual_text(text, title) for title, text in sources]
        return self.run_extracted_sources(
            extracted,
            genre_id=genre_id,
            target_reader=target_reader,
            article_goal=article_goal,
            narrator=narrator,
            self_viewpoint_owner=self_viewpoint_owner,
            blog_persona_profile=blog_persona_profile,
        )

    def run_extracted_sources(
        self,
        extracted: list[ExtractedSource],
        genre_id: str = "company_service_intro",
        target_reader: str = "初めてサービスを知る読者",
        article_goal: str = "ソースに基づいて自然なブログ記事を作る",
        narrator: str | None = None,
        self_viewpoint_owner: str | None = None,
        blog_persona_profile: dict[str, Any] | None = None,
    ) -> BlogPipelineResult:
        self._write_progress("source_packets", 12, "ソースを生成用パケットに整理しています。")
        packets = build_generation_source_packets(extracted)
        self.logger.write_json("source_packets", [asdict(packet) for packet in packets])

        self._write_progress(
            "source_card_extraction",
            18,
            f"ソースカードを作成しています。（0/{len(packets)}）",
            current=0,
            total=len(packets),
        )
        source_cards = self._extract_source_cards(packets)
        self.logger.write_json("source_cards", source_cards)

        self._write_progress("knowledge_pack_integration", 50, "根拠情報を統合しています。")
        knowledge_pack = KnowledgePackIntegrator(self.client).integrate(source_cards)
        self.logger.write_json("article_knowledge_pack", knowledge_pack)

        self._write_progress("article_brief_builder", 60, "記事の設計図を作成しています。")
        article_brief = ArticleBriefBuilder(self.client).build(
            knowledge_pack,
            genre_id=genre_id,
            target_reader=target_reader,
            article_goal=article_goal,
            narrator=narrator,
            self_viewpoint_owner=self_viewpoint_owner,
            blog_persona_profile=blog_persona_profile,
        )
        self.logger.write_json("article_brief", article_brief)

        selected_source_excerpts = build_selected_source_excerpts_v2(
            article_brief,
            knowledge_pack,
            source_cards,
            packets,
        )
        if selected_source_excerpts:
            self.logger.write_json("selected_source_excerpts", selected_source_excerpts)

        self._write_progress("draft_writer", 72, "本文の下書きを作成しています。")
        draft = DraftWriter(self.client).write(article_brief, knowledge_pack, selected_source_excerpts)
        self.logger.write_text("draft", draft)

        self._write_progress("opening_editor", 80, "冒頭の流れを整えています。")
        opening_edited = guard_editor_output(
            "opening_editor",
            draft,
            OpeningEditor(self.client).edit(draft, article_brief, knowledge_pack),
            article_brief,
        )
        self.logger.write_text("opening_edited_draft", opening_edited)
        self.logger.write_json(
            "opening_editor_report",
            build_opening_edit_report(draft, opening_edited, article_brief, knowledge_pack),
        )

        self._write_progress("global_consistency_editor", 86, "記事全体の整合性を確認しています。")
        global_edited = guard_editor_output(
            "global_consistency_editor",
            opening_edited,
            GlobalConsistencyEditor(self.client).edit(opening_edited, article_brief),
            article_brief,
        )
        self.logger.write_text("global_consistency_edited_draft", global_edited)
        self.logger.write_json(
            "global_consistency_report",
            build_global_consistency_report(opening_edited, global_edited, article_brief),
        )

        self._write_progress("style_editor", 90, "文体と段落を整えています。")
        edited = guard_editor_output(
            "style_editor",
            global_edited,
            StyleEditor(self.client).edit(global_edited, article_brief),
            article_brief,
        )
        self.logger.write_text("edited_draft", edited)

        self._write_progress("structural_editor", 94, "見出しと後半の流れを確認しています。")
        structural_edited = guard_editor_output(
            "structural_editor",
            edited,
            StructuralEditor(self.client).edit(edited, article_brief, knowledge_pack),
            article_brief,
        )
        self.logger.write_text("structural_edited_draft", structural_edited)
        self.logger.write_json("editor_pass_report", build_structural_edit_report(edited, structural_edited, article_brief))

        self._write_progress("quality_check", 97, "品質チェックを行っています。")
        checker = JapaneseQualityChecker()
        quality = checker.check(structural_edited, article_brief, knowledge_pack)
        final_article = guard_editor_output(
            "targeted_rewriter",
            structural_edited,
            deterministic_targeted_rewrite(structural_edited, quality, article_brief),
            article_brief,
        )
        final_quality = checker.check(final_article, article_brief, knowledge_pack)
        human_visible_surface_gate = check_human_visible_surface(final_article, article_brief)

        self.logger.write_json("latest_generation_quality_report", final_quality)
        self.logger.write_json("human_visible_surface_gate", human_visible_surface_gate)
        self.logger.write_text("latest_generation_output", final_article)
        self._write_progress("completed", 100, "記事生成が完了しました。")
        return BlogPipelineResult(
            final_article=final_article,
            source_cards=source_cards,
            knowledge_pack=knowledge_pack,
            article_brief=article_brief,
            quality_check=final_quality,
            artifact_dir=self.logger.run_dir,
            draft=draft,
            opening_edited_draft=opening_edited,
            global_consistency_edited_draft=global_edited,
            edited_draft=edited,
            structural_edited_draft=structural_edited,
        )

    def _extract_source_cards(self, packets: list[Any]) -> list[dict[str, Any]]:
        if not packets:
            return []
        workers = min(len(packets), max(1, _int_env(SOURCE_CARD_MAX_WORKERS_ENV, 3)))
        if workers <= 1:
            cards: list[dict[str, Any]] = []
            for index, packet in enumerate(packets, start=1):
                cards.append(SourceCardExtractor(self.client).extract(packet))
                self._write_source_card_progress(index, len(packets))
            return cards

        cards_by_index: dict[int, dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(SourceCardExtractor(self.client).extract, packet): index
                for index, packet in enumerate(packets)
            }
            completed = 0
            for future in as_completed(futures):
                index = futures[future]
                cards_by_index[index] = future.result()
                completed += 1
                self._write_source_card_progress(completed, len(packets), workers=workers)
        return [cards_by_index[index] for index in range(len(packets))]

    def _write_source_card_progress(self, current: int, total: int, *, workers: int = 1) -> None:
        span = 30
        percent = 18 + int(round(span * (current / max(1, total))))
        parallel_note = f" / 並列{workers}" if workers > 1 else ""
        self._write_progress(
            "source_card_extraction",
            min(48, percent),
            f"ソースカードを作成しています。（{current}/{total}{parallel_note}）",
            current=current,
            total=total,
        )

    def _write_progress(
        self,
        stage: str,
        percent: int,
        message: str,
        *,
        current: int = 0,
        total: int = 0,
    ) -> None:
        self.logger.write_json(
            "progress",
            {
                "stage": stage,
                "percent": max(0, min(100, int(percent))),
                "message": message,
                "current": int(current),
                "total": int(total),
            },
        )


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
