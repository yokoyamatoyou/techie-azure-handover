"""Tests for zero-base phase06 minimal postprocess and legal guard."""

from __future__ import annotations

import note.article_generator as ag
from note.article_fetcher import FetchedContent
from note.article_generator import ArticleGenerator


class _PassEmbedder:
    def embed_texts(self, texts):
        vectors = []
        for idx, _text in enumerate(texts):
            vectors.append([float(idx + 1), 0.0, 0.0])
        return vectors


class _Phase06LLM:
    def __init__(self) -> None:
        self.section_calls = 0

    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        if task_type == "title":
            return "phase06タイトル"
        if task_type == "lead":
            return "導入です。この記事の要点を共有します。"
        if task_type == "hashtags":
            return "#phase06 #zero_base #test"
        if task_type == "editor_consistency":
            return '{"lead":"導入です。","body":"## 見出しA\\n\\n本文。\\n\\n## 見出しB\\n\\n本文。"}'
        if task_type == "zero_base_section":
            self.section_calls += 1
            if self.section_calls == 1:
                return "2026年3月10日 10:00に公開し、この方法で必ず成果が出ます。"
            if self.section_calls == 2:
                return "法令上まったく問題ありません。導入は段階的に進めます。"
            return "診断なしで絶対に治ります。"
        if "アウトライン" in prompt or "\"sections\"" in prompt or "\"headings\"" in prompt:
            return (
                '{"sections":['
                '{"heading":"見出しA","purpose":"導入","required_elements":["要素1"],"key_message":"結論A"},'
                '{"heading":"見出しB","purpose":"本論","required_elements":["要素2"],"key_message":"結論B"},'
                '{"heading":"見出しC","purpose":"まとめ","required_elements":["要素3"],"key_message":"結論C"}'
                "]}",
            )[0]
        return "本文です。"


def _contexts() -> list[FetchedContent]:
    return [FetchedContent(title="テスト資料", content="本文です。", source_type="url")]


def _build_generator() -> ArticleGenerator:
    generator = ArticleGenerator(llm_client=_Phase06LLM())
    generator._zero_base_embedding_provider = _PassEmbedder()
    return generator


def test_phase06_heading_not_broken(monkeypatch) -> None:
    monkeypatch.setattr(ag, "get_generation_mode", lambda: "zero_base_v2")
    generator = _build_generator()
    result = generator.generate(_contexts(), "phase06 heading test", "announcement")
    assert result["body"].count("## ") == len(result["zero_base_outline"])
    assert result["zero_base_postprocess_audit"]["heading_preserved"] is True


def test_phase06_rewrite_ratio_is_limited(monkeypatch) -> None:
    monkeypatch.setattr(ag, "get_generation_mode", lambda: "zero_base_v2")
    generator = _build_generator()
    result = generator.generate(_contexts(), "phase06 rewrite ratio test", "ai")
    audit = result["zero_base_postprocess_audit"]
    assert audit["rewrite_ratio_body"] <= 0.5


def test_phase06_legal_risk_is_detected(monkeypatch) -> None:
    monkeypatch.setattr(ag, "get_generation_mode", lambda: "zero_base_v2")
    generator = _build_generator()
    result = generator.generate(_contexts(), "phase06 legal test", "ai")
    legal = result["zero_base_legal_guard_report"]
    assert legal["risk_hits"] >= 1
    assert legal["fail_open"] is False


def test_phase06_must_cover_is_preserved(monkeypatch) -> None:
    monkeypatch.setattr(ag, "get_generation_mode", lambda: "zero_base_v2")
    generator = _build_generator()
    generator.set_interview_answers({"message": "導入は段階的に進めます。"})
    result = generator.generate(_contexts(), "phase06 must_cover test", "ai")
    contract = result["zero_base_contract"]
    must_cover = [str(item).strip(" 　。") for item in contract.get("must_cover", [])]
    assert "導入は段階的に進めます" in must_cover
    assert result["zero_base_must_cover_integration_report"]["mode"] == "outline_only"


def test_phase06_article_type_format_is_kept(monkeypatch) -> None:
    monkeypatch.setattr(ag, "get_generation_mode", lambda: "zero_base_v2")
    generator = _build_generator()
    result = generator.generate(_contexts(), "phase06 format test", "announcement")
    contract = result["zero_base_contract"]
    assert contract["article_type"] == "announcement"
    assert "2026年3月10日 10:00" in result["body"]


def test_phase06_legal_guard_does_not_delete_full_text() -> None:
    generator = _build_generator()
    body, report = generator._zero_base_apply_minimal_legal_guard(
        body="法令に沿って運用を確認します。",
        contract={"must_cover": []},
    )
    assert body.strip()
    assert report["fail_open"] is False


def test_phase06_regex_paths_handle_long_input_without_exception() -> None:
    generator = _build_generator()
    long_body = ("法令" * 4000) + "必ず問題ありません。"
    fixed = generator._zero_base_light_grammar_fix(long_body)
    guarded, report = generator._zero_base_apply_minimal_legal_guard(
        body=fixed,
        contract={"must_cover": []},
    )
    assert guarded
    assert report["fail_open"] is False


def test_phase06_minimal_postprocess_runs_phase7_sanitize() -> None:
    generator = _build_generator()
    lead, body, audit = generator._zero_base_minimal_postprocess(
        lead="重要なのは、最初の一歩を踏み出すことが重要です。",
        body="## 見出しA\n\n最初の一歩として進めることが重要です。",
        target_audience="一般読者",
        contract={"must_cover": []},
    )

    assert "最初の一歩" not in lead
    assert "最初の一歩" not in body
    assert "phase7_sanitize" in audit["applied_steps"]

