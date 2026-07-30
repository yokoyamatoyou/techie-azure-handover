"""Runtime behavior tests for LLMClient retry/parameter handling."""
from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from core.token_tracker import TokenTracker
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


def _build_client(monkeypatch, *, chat_create, image_generate=None, responses_create=None):
    if image_generate is None:
        def image_generate(**kwargs):  # type: ignore[no-untyped-def]
            return SimpleNamespace(data=[], usage=None)
    if responses_create is None:
        def responses_create(**kwargs):  # type: ignore[no-untyped-def]
            return SimpleNamespace(output_text="")

    class FakeOpenAI:
        def __init__(self, timeout=None):  # type: ignore[no-untyped-def]
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=chat_create),
            )
            self.images = SimpleNamespace(generate=image_generate)
            self.responses = SimpleNamespace(
                create=responses_create,
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
    metadata = client.get_last_call_metadata()
    assert metadata["same_model_retry_count"] == 1
    assert metadata["retry_events"] == ["finish_reason_length"]
    assert metadata["last_retry_event"] == "finish_reason_length"


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
    monkeypatch.setattr(llm_module, "DEFAULT_TOP_P", None)

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


def test_generate_images_does_not_retry_inside_low_level_client(monkeypatch):
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

    with pytest.raises(TypeError):
        client.generate_images("画像テスト", n=1)

    assert attempts["count"] == 1


def test_gpt_image2_params_are_sanitized_and_preserve_size(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        return _chat_response("unused")

    def image_generate(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return SimpleNamespace(data=[], usage=None)

    client = _build_client(
        monkeypatch,
        chat_create=chat_create,
        image_generate=image_generate,
    )

    result = client.generate_images(
        "文字入り画像",
        n=1,
        model="gpt-image-2",
        size="1280x672",
        quality="medium",
        output_format="jpeg",
        background="transparent",
        moderation="auto",
        allow_text=True,
    )

    assert result == []
    assert len(calls) == 1
    params = calls[0]
    assert params["model"] == "gpt-image-2"
    assert params["size"] == "1280x672"
    assert params["quality"] == "medium"
    assert params["output_format"] == "jpeg"
    assert params["moderation"] == "auto"
    assert "background" not in params
    assert "input_fidelity" not in params
    assert "No text, letters" not in params["prompt"]


def test_generate_images_appends_no_text_constraint_by_default(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        return _chat_response("unused")

    def image_generate(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return SimpleNamespace(data=[], usage=None)

    client = _build_client(
        monkeypatch,
        chat_create=chat_create,
        image_generate=image_generate,
    )

    client.generate_images("文字なし画像", n=1, model="gpt-image-2")

    assert "No text, letters, or words in the image." in calls[0]["prompt"]


def test_token_tracker_prices_gpt_image2_image_tokens():
    tracker = TokenTracker()

    usage = tracker.add_image_usage(
        model="gpt-image-2",
        task_type="image_generation",
        input_text_tokens=1000,
        input_image_tokens=0,
        output_text_tokens=0,
        output_image_tokens=1000,
    )

    assert usage.cost_usd == pytest.approx(0.035)


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


def test_build_image_variation_prompt_reflects_selected_pattern(monkeypatch):
    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        return _chat_response("unused")

    client = _build_client(monkeypatch, chat_create=chat_create)

    prompt = client._build_image_variation_prompt("base prompt", 0, pattern_key="rich")

    assert "Rich Context Style" in prompt
    assert "Let GPT Image 2 decide how much contextual richness is useful" in prompt
    assert "4-7" not in prompt


def test_describe_image_uses_configured_description_model(monkeypatch, tmp_path):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        return _chat_response("unused")

    def responses_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return SimpleNamespace(output_text="画像の説明")

    monkeypatch.setattr(llm_module, "DEFAULT_IMAGE_DESCRIPTION_MODEL", "gpt-5.4-mini")
    monkeypatch.setattr(llm_module, "FALLBACK_IMAGE_DESCRIPTION_MODEL", "gpt-4.1-mini-2025-04-14")
    client = _build_client(
        monkeypatch,
        chat_create=chat_create,
        responses_create=responses_create,
    )
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    out = client.describe_image(str(image_path))

    assert out == "画像の説明"
    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-5.4-mini"


def test_describe_image_retries_with_fallback_description_model(monkeypatch, tmp_path, caplog):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        return _chat_response("unused")

    def responses_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("temporary vision failure")
        return SimpleNamespace(output_text="画像の説明")

    monkeypatch.setattr(llm_module, "DEFAULT_IMAGE_DESCRIPTION_MODEL", "gpt-5.4-mini")
    monkeypatch.setattr(llm_module, "FALLBACK_IMAGE_DESCRIPTION_MODEL", "gpt-4.1-mini-2025-04-14")
    client = _build_client(
        monkeypatch,
        chat_create=chat_create,
        responses_create=responses_create,
    )
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    with caplog.at_level(logging.WARNING):
        out = client.describe_image(str(image_path))

    assert out == "画像の説明"
    assert len(calls) == 2
    assert calls[0]["model"] == "gpt-5.4-mini"
    assert calls[1]["model"] == "gpt-4.1-mini-2025-04-14"
    assert "Retrying with fallback image description model" in caplog.text


def test_gpt5_family_skips_penalty_params_upfront(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return _chat_response("ok")

    client = _build_client(monkeypatch, chat_create=chat_create)
    out = client.generate_text(
        "比較レビュー",
        max_tokens=200,
        task_type="section",
        article_type="comparative_review",
    )

    assert out == "ok"
    assert len(calls) == 1
    assert "presence_penalty" not in calls[0]
    assert "frequency_penalty" not in calls[0]
    assert "extra_body" not in calls[0] or "presence_penalty" not in calls[0].get("extra_body", {})
    metadata = client.get_last_call_metadata()
    assert metadata["selected_model"] == "gpt-5.4"
    assert metadata["model_source"] == "task_models.section"
    assert metadata["task_type"] == "section"
    assert metadata["effective_temperature"] is None
    assert metadata["effective_top_p"] is None
    assert metadata["effective_presence_penalty"] is None
    assert metadata["effective_frequency_penalty"] is None
    assert set(metadata["compatibility_suppressed_params"]) >= {
        "temperature",
        "top_p",
        "presence_penalty",
        "frequency_penalty",
    }


def test_primary_model_retry_does_not_switch_to_fallback(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        if len(calls) < 3:
            raise RuntimeError("TRN_UPSTREAM_5XX: upstream failure")
        return _chat_response("ok")

    client = _build_client(monkeypatch, chat_create=chat_create)
    out = client.generate_text("堅牢性テスト", max_tokens=120, task_type="section")

    assert out == "ok"
    assert len(calls) == 3
    assert all(call["model"] == calls[0]["model"] for call in calls)
    metadata = client.get_last_call_metadata()
    assert metadata["same_model_retry_count"] == 2
    assert metadata["retry_events"] == ["retryable_upstream_5xx", "retryable_upstream_5xx"]
    assert metadata["last_retry_event"] == "retryable_upstream_5xx"
    assert metadata["model_fallback_attempted"] is False
    assert metadata["model_fallback_blocked"] is True


def test_primary_model_retry_exhaustion_raises_reason_code(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        raise RuntimeError("timeout while waiting for response")

    client = _build_client(monkeypatch, chat_create=chat_create)

    with pytest.raises(llm_module.LLMRuntimeError) as exc_info:
        client.generate_text("堅牢性テスト", max_tokens=120, task_type="section")

    assert len(calls) == 3
    assert exc_info.value.reason_code == "TRN_PRIMARY_MODEL_TIMEOUT"
    assert exc_info.value.call_metadata["same_model_retry_count"] == 2
    assert exc_info.value.call_metadata["model_fallback_attempted"] is False


def test_primary_model_connection_error_retries_and_raises_network_reset(monkeypatch):
    calls = []

    class APIConnectionError(RuntimeError):
        pass

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        raise APIConnectionError("Connection error.")

    client = _build_client(monkeypatch, chat_create=chat_create)

    with pytest.raises(llm_module.LLMRuntimeError) as exc_info:
        client.generate_text("接続テスト", max_tokens=120, task_type="section")

    assert len(calls) == 3
    assert exc_info.value.reason_code == "TRN_PRIMARY_MODEL_NETWORK_RESET"
    assert exc_info.value.call_metadata["same_model_retry_count"] == 2
    assert exc_info.value.call_metadata["last_error_class"] == "network_reset"


def test_exact_gpt5_alias_converts_reasoning_none_to_low(monkeypatch):
    calls = []

    def chat_create(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return _chat_response("ok")

    client = _build_client(monkeypatch, chat_create=chat_create)
    client.model = "gpt-5"
    out = client.generate_text("alias test", max_tokens=80, task_type="article")

    assert out == "ok"
    assert len(calls) == 1
    assert calls[0]["reasoning_effort"] == "low"
    metadata = client.get_last_call_metadata()
    assert metadata["selected_model"] == "gpt-5"
    assert metadata["effective_reasoning_effort"] == "low"
