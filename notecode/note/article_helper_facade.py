"""UI-safe helper facade around ArticleGenerator legacy helper flows."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from note.article_fetcher import FetchedContent
from note.article_generator import ArticleGenerator
from note.llm_client import LLMClient


class ArticleHelperFacade:
    """Expose only helper flows that remain UI-owned after mainline extraction."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self._generator = ArticleGenerator(llm_client=llm_client)

    @property
    def llm(self) -> LLMClient:
        return self._generator.llm

    def set_term_clarifications(self, clarifications: Dict[str, str]) -> None:
        self._generator.set_term_clarifications(clarifications)

    def generate_interview_questions(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
        force_questions: bool = False,
    ) -> List[Dict[str, str]]:
        return self._generator.generate_interview_questions(
            contexts,
            user_prompt,
            article_type,
            force_questions=force_questions,
        )

    def get_last_interview_generation_status(self) -> Dict[str, str]:
        return self._generator.get_last_interview_generation_status()

    def reset_generation_progress(self) -> None:
        self._generator.reset_generation_progress()

    def get_generation_progress(self) -> Dict[str, Any]:
        return self._generator.get_generation_progress()

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
        return self._generator.generate_image_prompts(
            contexts,
            user_prompt,
            title,
            lead,
            body,
            count,
            mode,
        )

    def to_japanese_image_prompt(self, prompt_text: str) -> str:
        return self._generator.to_japanese_image_prompt(prompt_text)

    def to_english_image_prompt(self, prompt_text: str) -> str:
        return self._generator.to_english_image_prompt(prompt_text)
