"""Legacy helper bridge for interview/image helpers only.

Allowed dependencies:
- note.legacy_current.article_helper_facade
- note.article_fetcher
- note.llm_client
- note.vnext.types
- stdlib

Forbidden dependencies:
- note.article_generator
- note.vnext.planner
- note.vnext.writer
- note.vnext.evaluator
- current_mainline_runtime_logging.py
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from note.article_fetcher import FetchedContent
from note.legacy_current.article_helper_facade import ArticleHelperFacade
from note.llm_client import LLMClient


class LegacyHelperAdapter:
    """Bridge helper-only legacy flows without exposing legacy generation ownership."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self._helper = ArticleHelperFacade(llm_client=llm_client)

    @property
    def llm(self) -> LLMClient:
        return self._helper.llm

    def set_term_clarifications(self, clarifications: Dict[str, str]) -> None:
        self._helper.set_term_clarifications(clarifications)

    def generate_interview_questions(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
        force_questions: bool = False,
    ) -> List[Dict[str, str]]:
        return self._helper.generate_interview_questions(
            contexts,
            user_prompt,
            article_type,
            force_questions=force_questions,
        )

    def get_last_interview_generation_status(self) -> Dict[str, str]:
        return self._helper.get_last_interview_generation_status()

    def reset_generation_progress(self) -> None:
        self._helper.reset_generation_progress()

    def get_generation_progress(self) -> Dict[str, Any]:
        return self._helper.get_generation_progress()

    def generate_image_prompts(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        title: str,
        lead: str,
        body: str,
        count: int = 1,
        mode: str = "initial_top_candidates",
    ) -> List[str]:
        return self._helper.generate_image_prompts(
            contexts,
            user_prompt,
            title,
            lead,
            body,
            count,
            mode,
        )

    def to_japanese_image_prompt(self, prompt_text: str) -> str:
        return self._helper.to_japanese_image_prompt(prompt_text)

    def to_english_image_prompt(self, prompt_text: str) -> str:
        return self._helper.to_english_image_prompt(prompt_text)
