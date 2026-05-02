"""Tests for zero-base phase05 semantic dedupe with embeddings."""

from __future__ import annotations

from typing import Sequence

import pytest

import note.article_generator as ag
from note.article_fetcher import FetchedContent
from note.article_generator import ArticleGenerator
from note.zero_base.semantic_dedupe import OpenAIEmbeddingProvider, semantic_dedupe_text


class RuleEmbedder:
    def __init__(self, rules: Sequence[tuple[str, list[float]]]) -> None:
        self.rules = list(rules)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for idx, text in enumerate(texts):
            selected: list[float] | None = None
            for pattern, vector in self.rules:
                if pattern in text:
                    selected = list(vector)
                    break
            if selected is None:
                selected = [0.0, 0.0, float(idx + 1)]
            vectors.append(selected)
        return vectors


class FailingEmbedder:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        raise RuntimeError("embedding api unavailable")


class CaptureEmbedder:
    def __init__(self) -> None:
        self.captured: list[str] = []

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        self.captured = [str(item) for item in texts]
        return [[1.0, 0.0, 0.0] for _ in texts]


def test_phase05_semantic_duplicate_detection_triggers() -> None:
    body = (
        "## 見出しA\n\n"
        "導入初期は小規模に試し、失敗コストを抑えます。\n\n"
        "## 見出しB\n\n"
        "導入初期は小規模に試し、失敗コストを抑えます。"
    )
    deduped, audit = semantic_dedupe_text(
        body,
        {"article_type": "ai", "must_cover": []},
        config={"similarity_threshold": 0.86, "content_overlap_threshold": 0.45},
        embedder=RuleEmbedder([("導入初期", [1.0, 0.0, 0.0])]),
    )
    assert audit["duplicate_pairs"] >= 1
    assert "前段と重なる説明は省略し" in deduped


def test_phase05_non_duplicate_is_not_over_detected() -> None:
    body = (
        "## 見出しA\n\n"
        "編集工数を減らすためにテンプレートを再設計します。\n\n"
        "## 見出しB\n\n"
        "公開告知の問い合わせ窓口は専用フォームで受け付けます。"
    )
    deduped, audit = semantic_dedupe_text(
        body,
        {"article_type": "ai", "must_cover": []},
        config={"similarity_threshold": 0.86, "content_overlap_threshold": 0.45},
        embedder=RuleEmbedder(
            [
                ("テンプレート", [1.0, 0.0, 0.0]),
                ("問い合わせ窓口", [0.0, 1.0, 0.0]),
            ]
        ),
    )
    assert audit["duplicate_pairs"] == 0
    assert deduped == body


def test_phase05_api_error_is_fail_open() -> None:
    body = (
        "## 見出しA\n\n重複確認のテキストです。\n\n"
        "## 見出しB\n\n重複確認のテキストです。"
    )
    deduped, audit = semantic_dedupe_text(
        body,
        {"article_type": "ai", "must_cover": []},
        embedder=FailingEmbedder(),
    )
    assert deduped == body
    assert audit["fail_open"] is True


def test_phase05_must_cover_is_not_removed() -> None:
    body = (
        "## 見出しA\n\n導入は小規模に始めます。\n\n"
        "## 見出しB\n\n導入は小規模に始めます。初期費用は月額5万円です。"
    )
    deduped, audit = semantic_dedupe_text(
        body,
        {"article_type": "ai", "must_cover": ["初期費用は月額5万円です。"]},
        embedder=RuleEmbedder([("導入は小規模", [1.0, 0.0, 0.0])]),
    )
    assert "初期費用は月額5万円です。" in deduped
    assert audit["must_cover_protected_count"] >= 1


def test_phase05_announcement_datetime_is_preserved() -> None:
    body = (
        "## 見出しA\n\n2026年3月10日 10:00に公開します。\n\n"
        "## 見出しB\n\n2026年3月10日 10:00に公開します。"
    )
    deduped, _audit = semantic_dedupe_text(
        body,
        {"article_type": "announcement", "must_cover": []},
        embedder=RuleEmbedder([("公開します", [1.0, 0.0, 0.0])]),
    )
    assert "2026年3月10日 10:00" in deduped


def test_phase05_embedding_input_masks_sensitive_text() -> None:
    body = (
        "## 見出しA\n\napi_key=sk-AAAAAAAAAAAAAAAAAAAAAA を貼り付けないでください。\n\n"
        "## 見出しB\n\nAuthorization: Bearer SECRET_TOKEN_123456789012"
    )
    embedder = CaptureEmbedder()
    _deduped, audit = semantic_dedupe_text(
        body,
        {"article_type": "ai", "must_cover": []},
        embedder=embedder,
    )
    joined = " ".join(embedder.captured)
    assert "sk-AAAA" not in joined
    assert "SECRET_TOKEN" not in joined
    assert audit["redaction_applied_count"] >= 1


def test_phase06_exact_text_match_is_always_deduped() -> None:
    body = (
        "## 見出しA\n\n"
        "導入初期は小規模に試し、失敗コストを抑えます。\n\n"
        "## 見出しB\n\n"
        "導入初期は小規模に試し、失敗コストを抑えます。"
    )
    deduped, audit = semantic_dedupe_text(
        body,
        {"article_type": "ai", "must_cover": []},
        config={
            "similarity_threshold": 0.99,
            "content_overlap_threshold": 0.9,
            "min_shared_content_words": 10,
        },
        embedder=RuleEmbedder([("導入初期", [1.0, 0.0, 0.0])]),
    )
    assert audit["duplicate_pairs"] >= 1
    assert any(reason.get("reason") == "exact_text_match" for reason in audit["deletion_reasons"])
    assert "前段と重なる説明は省略し" in deduped


def test_phase06_required_sentence_priority_is_recorded() -> None:
    body = (
        "## Section A\n\n"
        "rollout starts small and validates each workflow milestone.\n\n"
        "## Section B\n\n"
        "rollout starts small and validates each workflow milestone with customer interview notes."
    )
    deduped, audit = semantic_dedupe_text(
        body,
        {"article_type": "ai", "must_cover": ["customer interview notes"]},
        config={
            "similarity_threshold": 0.84,
            "content_overlap_threshold": 0.4,
            "min_shared_content_words": 2,
        },
        embedder=RuleEmbedder([("rollout starts small", [1.0, 0.0, 0.0])]),
    )
    assert "customer interview notes" in deduped
    assert any(reason.get("reason") == "required_sentence_priority" for reason in audit["deletion_reasons"])
    assert any(reason.get("reason") == "must_cover_protected" for reason in audit["protection_reasons"])


def test_phase06_audit_excerpt_masks_secret_text() -> None:
    body = "## 見出しA\n\napi_key=sk-AAAAAAAAAAAAAAAAAAAAAA の取り扱いを確認します。"
    _deduped, audit = semantic_dedupe_text(
        body,
        {"article_type": "ai", "must_cover": ["api_key=sk-AAAAAAAAAAAAAAAAAAAAAA"]},
        embedder=RuleEmbedder([("api_key", [1.0, 0.0, 0.0])]),
    )
    excerpts = [str(item.get("text_excerpt", "")) for item in audit["protection_reasons"]]
    joined = " ".join(excerpts)
    assert "sk-AAAA" not in joined
    assert "[REDACTED" in joined


def test_phase05_rate_limit_retry_is_bounded() -> None:
    class _RateLimitClient:
        def __init__(self) -> None:
            self.calls = 0
            self.embeddings = self

        def create(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls += 1
            raise RuntimeError("429 rate limit")

    provider = object.__new__(OpenAIEmbeddingProvider)
    provider.model = "text-embedding-3-small"
    provider.max_retries = 1
    provider.retry_backoff_seconds = 0.01
    provider.client = _RateLimitClient()

    with pytest.raises(RuntimeError):
        provider.embed_texts(["a", "b"])
    assert provider.client.calls == 2


class _Phase05LLM:
    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        if task_type == "title":
            return "phase05タイトル"
        if task_type == "lead":
            return "導入です。"
        if task_type == "hashtags":
            return "#phase05 #zero_base"
        if task_type == "editor_consistency":
            return '{"lead":"導入です。","body":"## 見出しA\\n\\n本文。\\n\\n## 見出しB\\n\\n本文。"}'
        if task_type == "zero_base_section":
            return "導入初期は小規模に試し、失敗コストを抑えます。"
        if "アウトライン" in prompt:
            return (
                '{"sections":['
                '{"heading":"見出しA","purpose":"導入","required_elements":["要素1"],"key_message":"結論A"},'
                '{"heading":"見出しB","purpose":"本論","required_elements":["要素2"],"key_message":"結論B"}'
                "]}",
            )[0]
        return "本文です。"


def test_phase05_generator_continues_when_embedding_fails(monkeypatch) -> None:
    monkeypatch.setattr(ag, "get_generation_mode", lambda: "zero_base_v2")
    generator = ArticleGenerator(llm_client=_Phase05LLM())
    generator._zero_base_embedding_provider = FailingEmbedder()
    result = generator.generate(
        [FetchedContent(title="source", content="本文", source_type="url")],
        "phase05 fail-open test",
        "ai",
    )
    assert result["full_text"]
    assert result["zero_base_dedupe_audit"]["fail_open"] is True


def test_phase05_zero_base_prompt_invariants_include_rhythm_rules() -> None:
    generator = ArticleGenerator(llm_client=_Phase05LLM())
    prompt = generator._zero_base_build_section_prompt(
        heading="見出し",
        new_information="新情報",
        reader_question="疑問",
        previous_summary="要約",
        recent_summaries=[],
        audience="読者",
        must_not_repeat=["同義反復"],
        section_plan={"sentence_min": 2, "sentence_max": 4, "target_chars": 240},
    )
    assert "定型句" in prompt
    assert "接続詞" in prompt
    assert "文末" in prompt


def test_phase05_linebreak_profile_applies_by_category() -> None:
    generator = ArticleGenerator(llm_client=_Phase05LLM())
    body = "## 見出し\n\n一文目です。二文目です。三文目です。四文目です。"
    profiled, report = generator._zero_base_apply_linebreak_profile(
        body=body,
        contract={"article_type": "announcement", "category_base_template": "announcement"},
    )
    assert report["profile"] == "announcement_compact"
    assert report["paragraph_after"] >= report["paragraph_before"]
    assert "\n\n" in profiled


def test_phase05_rhythm_report_is_emitted_in_zero_base(monkeypatch) -> None:
    monkeypatch.setattr(ag, "get_generation_mode", lambda: "zero_base_v2")
    generator = ArticleGenerator(llm_client=_Phase05LLM())
    result = generator.generate(
        [FetchedContent(title="source", content="本文", source_type="url")],
        "phase05 rhythm report",
        "ai",
    )
    rhythm = result["zero_base_rhythm_report"]
    assert "linebreak_profile" in rhythm
    assert rhythm["linebreak_profile"]["profile"] in {"analysis_balanced", "announcement_compact", "default"}
    alignment = result["pipeline_check"]["contract_alignment"]
    assert "linebreak_profile" in alignment

