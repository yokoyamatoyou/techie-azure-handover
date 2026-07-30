import base64
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from note import llm_client as llm_client_module
from note.blog_image_auto import generate_blog_images_for_article
from note.llm_client import LLMClient
from note.writer_only_config import WriterOnlyModelConfig
from note.writer_only_openai_adapter import write_openai_draft


_DUMMY_IMAGE_B64 = base64.b64encode(b"not-a-real-image-but-never-resized").decode("ascii")


class _ApiSendCounter:
    def __init__(self) -> None:
        self.ledger: list[dict[str, str]] = []

    def record(self, kind: str, *, model: str = "") -> None:
        self.ledger.append({"kind": kind, "model": model})

    def count(self, kind: str) -> int:
        return Counter(item["kind"] for item in self.ledger)[kind]

    @property
    def total(self) -> int:
        return len(self.ledger)


class _CountingResponses:
    def __init__(self, counter: _ApiSendCounter) -> None:
        self._counter = counter

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self._counter.record("responses.create", model=str(kwargs.get("model") or ""))
        return SimpleNamespace(
            output_text=json.dumps(
                {
                    "article_markdown": (
                        "# 空き家相談前に見る判断軸\n\n"
                        "## 相談前につまずく理由\n\n"
                        "私たちは、空き家や貸家の相談前に条件を整理します。\n\n"
                        "## 判断軸\n\n"
                        "私たちは、現状、目的、費用を分けて見ます。\n\n"
                        "## 次の一歩\n\n"
                        "私たちは、相談前の不安を一緒にほどきます。"
                    ),
                    "linkedin_text": "私たちは空き家や貸家の相談前に、現状、目的、費用を分けて整理することを大切にしています。",
                    "linkedin_short_text": "空き家相談前に、現状、目的、費用を整理します。",
                },
                ensure_ascii=False,
            )
        )


class _CountingChatCompletions:
    def __init__(self, counter: _ApiSendCounter) -> None:
        self._counter = counter

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self._counter.record("chat.completions.create", model=str(kwargs.get("model") or ""))
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="空き家相談の判断軸は？"),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=4),
        )


class _CountingImages:
    def __init__(self, counter: _ApiSendCounter, *, failures_before_success: int = 0) -> None:
        self._counter = counter
        self.failures_before_success = failures_before_success

    def generate(self, **kwargs):  # type: ignore[no-untyped-def]
        self._counter.record("images.generate", model=str(kwargs.get("model") or ""))
        if self.failures_before_success > 0:
            self.failures_before_success -= 1
            raise RuntimeError("temporary image failure")
        return SimpleNamespace(data=[SimpleNamespace(b64_json=_DUMMY_IMAGE_B64)])


class _CountingOpenAI:
    def __init__(self, counter: _ApiSendCounter, *, image_failures_before_success: int = 0) -> None:
        self.responses = _CountingResponses(counter)
        self.chat = SimpleNamespace(completions=_CountingChatCompletions(counter))
        self.images = _CountingImages(
            counter,
            failures_before_success=image_failures_before_success,
        )


def _build_counted_llm(monkeypatch, tmp_path: Path, fake_client: _CountingOpenAI) -> LLMClient:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm_client_module, "GENERATED_IMAGES_DIR", str(tmp_path / "generated_images"))
    llm = LLMClient(model="gpt-4.1-mini-2025-04-14")
    llm.client = fake_client
    llm._resize_for_note = lambda image_path: image_path  # type: ignore[method-assign]
    return llm


def test_api_send_counter_covers_responses_chat_and_images(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    counter = _ApiSendCounter()
    fake_client = _CountingOpenAI(counter)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")

    writer_result = write_openai_draft(
        {"instruction": "空き家相談前の判断軸を書く"},
        model_config=WriterOnlyModelConfig(
            family="gpt-4.1",
            model="gpt-4.1-mini-2025-04-14",
            api="responses",
            parameters={"temperature": 0.2},
        ),
        client_factory=lambda **_: fake_client,
    )
    llm = _build_counted_llm(monkeypatch, tmp_path, fake_client)

    image_result = generate_blog_images_for_article(
        llm=llm,
        title="空き家や貸家の活用相談前に整理したい判断軸",
        lead="空き家や貸家の所有者が相談前に見る条件を整理します。",
        body="私たちは相談前に、物件の現状、活用目的、費用の見通しを分けて確認します。",
        article_type="explanatory_article",
        log_dir=tmp_path / "logs",
    )

    assert writer_result["api_send_count"] == 1
    assert image_result["status"] == "success"
    assert image_result["display_text"] == "空き家相談の判断軸は？"
    assert counter.count("responses.create") == 1
    assert counter.count("chat.completions.create") == 1
    assert counter.count("images.generate") == 2
    assert counter.total == 4


def test_api_send_counter_counts_image_retry_as_additional_image_send(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    counter = _ApiSendCounter()
    fake_client = _CountingOpenAI(counter, image_failures_before_success=1)
    llm = _build_counted_llm(monkeypatch, tmp_path, fake_client)

    image_result = generate_blog_images_for_article(
        llm=llm,
        title="空き家や貸家の活用相談前に整理したい判断軸",
        lead="空き家や貸家の所有者が相談前に見る条件を整理します。",
        body="私たちは相談前に、物件の現状、活用目的、費用の見通しを分けて確認します。",
        article_type="explanatory_article",
        log_dir=tmp_path / "logs",
    )

    assert image_result["status"] == "success"
    assert image_result["variants"][0]["retry_count"] == 1
    assert counter.count("chat.completions.create") == 1
    assert counter.count("images.generate") == 3
    assert counter.total == 4
