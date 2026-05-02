"""Visibility tests for fail-open paths."""
from __future__ import annotations

import logging

from human_resonance.phase6_legal import Phase6Legal
from note.article_generator import ArticleGenerator


class _FailingLLM:
    def __init__(self, failed_task: str) -> None:
        self.failed_task = failed_task

    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        if task_type == self.failed_task:
            raise RuntimeError(f"{task_type} failed")
        return '{"lead":"ok","body":"## 見出し\\n本文"}'


class _RecorderLLM:
    def __init__(self) -> None:
        self.calls = []

    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        self.calls.append({
            "max_tokens": max_tokens,
            "task_type": task_type,
        })
        return "a" * 7000


def test_repair_only_failure_emits_warning(caplog):
    generator = ArticleGenerator(llm_client=_FailingLLM("repair_only"))
    generator._get_postprocess_config = lambda: {  # type: ignore[method-assign]
        "repair_only": {
            "enabled": True,
            "mode": "enforce",
            "rewrite_ratio_cap": 0.08,
            "min_chars_for_llm": 1,
        }
    }
    generator._should_use_repair_only_llm = lambda report, body_chars, cfg: True  # type: ignore[method-assign]

    with caplog.at_level(logging.WARNING):
        out_lead, out_body = generator._run_repair_only_pass(
            "導入文",
            "本文",
            merged_context="",
            article_type="ai",
            target_audience="読者",
        )

    assert out_lead == "導入文"
    assert out_body == "本文"
    assert "repair_only pass failed. Keep original text." in caplog.text


def test_editor_consistency_all_retries_emit_warning(caplog):
    generator = ArticleGenerator(llm_client=_FailingLLM("editor_consistency"))
    generator._current_pronoun = "私"

    with caplog.at_level(logging.WARNING):
        out_lead, out_body = generator._run_editor_consistency_pass(
            "導入文",
            "## 見出し\n本文",
            merged_context="",
            article_type="ai",
            target_audience="読者",
            review_points=[],
        )

    assert out_lead == "導入文"
    assert out_body == "## 見出し\n本文"
    assert generator._editor_consistency_failed is True
    assert "Editor consistency all retries failed" in caplog.text


def test_readability_polish_failure_emits_warning(caplog):
    generator = ArticleGenerator(llm_client=_FailingLLM("readability_polish"))
    generator._should_run_readability_polish = lambda review_points, body="": True  # type: ignore[method-assign]

    with caplog.at_level(logging.WARNING):
        out_lead, out_body = generator._run_readability_polish_pass(
            "導入文",
            "## 見出し\n本文",
            merged_context="",
            article_type="ai",
            target_audience="読者",
            review_points=["段落が長く論点が混在"],
        )

    assert out_lead == "導入文"
    assert out_body == "## 見出し\n本文"
    assert "Readability polish pass failed. Keep original text." in caplog.text


def test_phase6_legal_llm_tokens_are_capped():
    recorder = _RecorderLLM()
    legal = Phase6Legal(llm_client=recorder)
    text = "a" * 12000

    _ = legal._llm_legal_check(text)

    assert recorder.calls
    assert recorder.calls[0]["task_type"] == "legal_check"
    assert recorder.calls[0]["max_tokens"] == 4096
