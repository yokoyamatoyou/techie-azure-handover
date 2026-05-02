"""Runtime behavior tests for LLMClient retry/parameter handling."""
from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from note import llm_client as llm_module


def _chat_response(content: str, *, finish_reason: str = "stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=34),
    )


def _build_client(monkeypatch, *, chat_create, image_generate=None):
    if image_generate is None:
        def image_generate(**kwargs):  # type: ignore[no-untyped-def]
            return SimpleNamespace(data=[], usage=None)

    class FakeOpenAI:
        def __init__(self, timeout=None):  # type: ignore[no-untyped-def]
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=chat_create),
            )
            self.images = SimpleNamespace(generate=image_generate)
            self.responses = SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(output_text=""),
            )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm_module, "OpenAI", FakeOpenAI)
    return llm_module.LLMClient(model="gpt-5-mini")


def test_candidate_b_api_removed() -> None:
    assert not hasattr(llm_module.LLMClient, "generate_candidate_b")


def test_truncation_retry_expands_long_form_max_tokens(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        if len(calls) == 1:
            return _chat_response("partial", finish_reason="length")
        return _chat_response("final", finish_reason="stop")

    client = _build_client(monkeypatch, chat_create=chat_create)
    out = client.generate_text("長文テスト", max_tokens=5200, task_type="section")

    assert out == "final"
    assert len(calls) == 2
    assert calls[0]["max_completion_tokens"] == 5200
    assert calls[1]["max_completion_tokens"] == 7800


def test_truncation_retry_returns_partial_when_budget_exhausted(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return _chat_response(f"partial-{len(calls)}", finish_reason="length")

    client = _build_client(monkeypatch, chat_create=chat_create)
    out = client.generate_text("長文テスト", max_tokens=1000, task_type="section")

    assert out == "partial-3"
    assert len(calls) == 3
    assert calls[0]["max_completion_tokens"] == 1000
    assert calls[1]["max_completion_tokens"] == 1500
    assert calls[2]["max_completion_tokens"] == 2250


def test_truncation_retry_caps_at_long_form_max_tokens(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        if len(calls) == 1:
            return _chat_response("partial", finish_reason="length")
        return _chat_response("final", finish_reason="stop")

    client = _build_client(monkeypatch, chat_create=chat_create)
    out = client.generate_text("長文テスト", max_tokens=7000, task_type="section")

    assert out == "final"
    assert len(calls) == 2
    assert calls[0]["max_completion_tokens"] == 7000
    assert calls[1]["max_completion_tokens"] == llm_module.LONG_FORM_RETRY_MAX_TOKENS


def test_truncation_does_not_retry_for_non_long_form_task(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return _chat_response("partial", finish_reason="length")

    client = _build_client(monkeypatch, chat_create=chat_create)
    out = client.generate_text("短文タスク", max_tokens=300, task_type="article")

    assert out == "partial"
    assert len(calls) == 1


def test_context_length_error_logs_truncation_warning(monkeypatch, caplog):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("maximum context length exceeded")
        return _chat_response("ok")

    client = _build_client(monkeypatch, chat_create=chat_create)
    long_prompt = "あ" * 3500

    with caplog.at_level(logging.WARNING):
        out = client.generate_text(long_prompt, max_tokens=200, task_type="article")

    assert out == "ok"
    assert len(calls) == 2
    second_prompt = calls[1]["messages"][0]["content"]
    assert "[入力が長いため一部省略]" in second_prompt
    assert "Truncating prompt due to context length" in caplog.text


def test_parameter_error_logs_temperature_retry_warning(monkeypatch, caplog):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("temperature parameter is unsupported")
        return _chat_response("ok")

    client = _build_client(monkeypatch, chat_create=chat_create)
    client.model = "gpt-4.1-mini-2025-04-14"

    with caplog.at_level(logging.WARNING):
        out = client.generate_text("テスト", max_tokens=120, task_type="article")

    assert out == "ok"
    assert len(calls) == 2
    assert "temperature" in calls[0]
    assert "temperature" not in calls[1]
    assert "Retrying without temperature parameter" in caplog.text


def test_empty_llm_response_emits_warning(monkeypatch, caplog):
    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(choices=[], usage=None)

    client = _build_client(monkeypatch, chat_create=chat_create)

    with caplog.at_level(logging.WARNING):
        out = client.generate_text("タイトル", max_tokens=60, task_type="title")

    assert out == ""
    assert "LLM response empty for task_type=title" in caplog.text


def test_generate_images_retry_failure_logs_context(monkeypatch, caplog):
    attempts = {"count": 0}

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        return _chat_response("unused")

    def image_generate(**kwargs):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise TypeError("output_format is not a valid keyword argument")
        raise RuntimeError("Rate limit on retry")

    client = _build_client(
        monkeypatch,
        chat_create=chat_create,
        image_generate=image_generate,
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError):
            client.generate_images("画像テスト", n=1)

    assert attempts["count"] == 2
    assert "Image generation retry failed after parameter adjustment" in caplog.text


def test_generate_images_warns_when_response_has_no_b64(monkeypatch, caplog):
    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        return _chat_response("unused")

    def image_generate(**kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(data=[SimpleNamespace(url="https://example.com/image.jpg")], usage=None)

    client = _build_client(
        monkeypatch,
        chat_create=chat_create,
        image_generate=image_generate,
    )

    with caplog.at_level(logging.WARNING):
        results = client.generate_images("画像テスト", n=1)

    assert results == []
    assert "No images saved: response contained 1 item(s) without b64 payload" in caplog.text
