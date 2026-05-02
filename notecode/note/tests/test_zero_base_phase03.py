"""Tests for zero-base phase03 scaffold and dispatch (v2 only)."""

from __future__ import annotations

import re

from core import app_config
from note.article_fetcher import FetchedContent
from note.article_generator import ArticleGenerator


class DummyLLM:
    def __init__(self) -> None:
        self.section_max_tokens: list[int] = []

    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        if task_type == "editor_consistency":
            return '{"lead": "テストリード。", "body": "## 見出しA\\n\\n本文テキスト。\\n\\n## 見出しB\\n\\n本文テキスト。"}'
        if "アウトライン" in prompt or "\"sections\"" in prompt or "\"headings\"" in prompt:
            return (
                '{"sections": ['
                '{"heading": "見出しA", "purpose": "導入", "required_elements": ["要素1"], "key_message": "結論A"},'
                '{"heading": "見出しB", "purpose": "本論", "required_elements": ["要素2"], "key_message": "結論B"},'
                '{"heading": "見出しC", "purpose": "まとめ", "required_elements": ["要素3"], "key_message": "結論C"}'
                "]}",
            )[0]
        if task_type == "title" or ("タイトル" in prompt and "タイトルのみ" in prompt):
            return "テストタイトル"
        if task_type in ("lead", "lead_refresh", "readability_polish"):
            return "導入です。結論を先に示します。"
        if task_type == "hashtags" or "ハッシュタグ" in prompt:
            return "#テスト #生成AI #実装"
        if task_type == "zero_base_section":
            self.section_max_tokens.append(int(max_tokens or 0))
            return "論点を整理し、読者が次の行動を選べるようにします。"
        match = re.search(r"## (.+?)」", prompt)
        heading = match.group(1) if match else "見出しA"
        return f"## {heading}\n\n本文テキスト。"


class LongFormAnchorLLM(DummyLLM):
    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        if task_type != "zero_base_section":
            return super().generate_text(prompt, max_tokens=max_tokens, task_type=task_type, **kwargs)

        def _extract_terms(label: str) -> list[str]:
            match = re.search(rf"{label}:\s*(.+)", prompt)
            if not match:
                return []
            raw = match.group(1)
            terms: list[str] = []
            for item in re.split(r"[、,/]", raw):
                text = item.strip()
                if not text or text in {"なし", "本文の中心語をそのまま使う"}:
                    continue
                terms.append(text)
            return terms

        terms: list[str] = []
        for label in ("この節の中心語", "必ず触れる点", "アンカー語"):
            terms.extend(_extract_terms(label))
        unique_terms: list[str] = []
        for term in terms:
            if term in unique_terms:
                continue
            unique_terms.append(term)
        if not unique_terms:
            unique_terms = ["導入手順", "判断基準", "運用注意点", "改善サイクル"]

        sentences = [
            f"{term}を現場の判断に結びつける観点を先に示します。"
            for term in unique_terms[:4]
        ]
        sentences.append("終盤では、前段の要点を踏まえて次の一歩を明確にします。")
        return "".join(sentences)


def _build_contexts() -> list[FetchedContent]:
    return [
        FetchedContent(
            title="テスト資料",
            content="これはテスト用の本文です。導入と本論と結論を含みます。",
            source_type="url",
        )
    ]


def _build_rich_contexts() -> list[FetchedContent]:
    contexts: list[FetchedContent] = []
    for idx in range(5):
        contexts.append(
            FetchedContent(
                title=f"テスト資料{idx + 1}",
                content=(
                    "これはテスト用の本文です。"
                    "導入と本論と結論を含みます。"
                    "実行手順、判断基準、運用時の注意点を整理します。"
                ),
                source_type="url",
            )
        )
    return contexts


def test_phase03_generation_mode_accepts_only_zero_base_v2() -> None:
    original_loader = app_config._load_config_file
    try:
        app_config._load_config_file = lambda: {"generation_mode": "zero_base_v2"}  # type: ignore[assignment]
        assert app_config.get_generation_mode() == "zero_base_v2"
    finally:
        app_config._load_config_file = original_loader  # type: ignore[assignment]


def test_phase03_zero_base_mode_generates_min_output(monkeypatch) -> None:
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v2")
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_input_contract(
        {
            "speaker_profile": "運営担当者",
            "audience_profile": "導入検討中の担当者",
            "relationship_mode": "guide",
            "register_policy": {"base_register": "polite"},
        }
    )
    result = generator.generate(
        _build_contexts(),
        "読者が実行できる手順を簡潔に示したい",
        "ai",
    )
    assert result["title"]
    assert "## " in result["body"]
    assert result["pipeline_check"]["generation_dispatch"]["dispatch_path"] == "zero_base_v2_path"
    contract = result["zero_base_contract"]
    assert contract["article_type"] == "ai"
    assert contract["category_base_template"] == "ai"
    assert contract["question_source_priority"] == [
        "interview_answers",
        "unresolved_items",
    ]


def test_phase03_zero_base_contract_reflects_interview_answers(monkeypatch) -> None:
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v2")
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_input_contract(
        {
            "speaker_profile": "編集担当",
            "audience_profile": "導入検討中の担当者",
            "relationship_mode": "guide",
            "register_policy": {"base_register": "polite"},
        }
    )
    generator.set_interview_answers(
        {
            "message": "結論と根拠を分けて示す",
            "target": "導入検討中の担当者",
        }
    )
    result = generator.generate(
        _build_contexts(),
        "記事作成",
        "branding",
    )
    contract = result["zero_base_contract"]
    must_cover = contract.get("must_cover", [])
    unresolved = contract.get("unresolved_items", [])
    assert "結論と根拠を分けて示す" in must_cover
    assert isinstance(unresolved, list)


def test_phase03_unsupported_mode_raises_error(monkeypatch) -> None:
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "legacy")
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_input_contract(
        {
            "speaker_profile": "編集担当",
            "audience_profile": "導入検討中の担当者",
            "relationship_mode": "guide",
            "register_policy": {"base_register": "polite"},
        }
    )
    try:
        generator.generate(
            _build_contexts(),
            "既存モードの回帰確認",
            "ai",
        )
    except ValueError as exc:
        assert "INP_UNSUPPORTED_GENERATION_MODE" in str(exc)
    else:
        raise AssertionError("unsupported mode must raise ValueError")


def test_phase03_outline_section_count_scales_by_length_mode(monkeypatch) -> None:
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v2")
    short_generator = ArticleGenerator(llm_client=DummyLLM())
    long_generator = ArticleGenerator(llm_client=DummyLLM())
    base_contract = {
        "speaker_profile": "編集担当",
        "audience_profile": "導入検討中の担当者",
        "relationship_mode": "guide",
        "register_policy": {"base_register": "polite"},
    }
    short_generator.set_input_contract(dict(base_contract))
    long_generator.set_input_contract(dict(base_contract))
    prompt = "読者が実行できる手順を、背景・判断基準・運用注意点・改善サイクルまで含めて整理したいです。"

    short_result = short_generator.generate(
        _build_rich_contexts(),
        prompt,
        "ai",
        length_mode="short",
    )
    long_result = long_generator.generate(
        _build_rich_contexts(),
        prompt,
        "ai",
        length_mode="long",
    )

    short_sections = short_result["body"].count("## ")
    long_sections = long_result["body"].count("## ")
    assert long_sections >= short_sections
    assert (
        long_result["pipeline_check"]["zero_base_length_plan"]["targets"]["section_count_target"]
        >= short_result["pipeline_check"]["zero_base_length_plan"]["targets"]["section_count_target"]
    )


def test_phase03_section_token_budget_scales_by_length_mode(monkeypatch) -> None:
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v2")
    short_llm = DummyLLM()
    long_llm = DummyLLM()
    short_generator = ArticleGenerator(llm_client=short_llm)
    long_generator = ArticleGenerator(llm_client=long_llm)
    base_contract = {
        "speaker_profile": "編集担当",
        "audience_profile": "導入検討中の担当者",
        "relationship_mode": "guide",
        "register_policy": {"base_register": "polite"},
    }
    short_generator.set_input_contract(dict(base_contract))
    long_generator.set_input_contract(dict(base_contract))
    prompt = "運用手順を具体化し、現場実装時の判断を支えるブログにしたいです。"

    short_generator.generate(_build_rich_contexts(), prompt, "ai", length_mode="short")
    long_generator.generate(_build_rich_contexts(), prompt, "ai", length_mode="long")

    assert short_llm.section_max_tokens
    assert long_llm.section_max_tokens
    assert max(long_llm.section_max_tokens) > max(short_llm.section_max_tokens)


def test_phase03_pipeline_check_includes_zero_base_length_plan(monkeypatch) -> None:
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v2")
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_input_contract(
        {
            "speaker_profile": "編集担当",
            "audience_profile": "導入検討中の担当者",
            "relationship_mode": "guide",
            "register_policy": {"base_register": "polite"},
        }
    )
    result = generator.generate(
        _build_rich_contexts(),
        "読者が迷わず次の行動を選べる実務記事を作成したいです。",
        "ai",
        length_mode="normal",
    )

    length_plan = result["pipeline_check"]["zero_base_length_plan"]
    assert length_plan["mode"] == "normal"
    assert length_plan["planner"] == "note_4000"
    assert length_plan["targets"]["body_chars"] >= 1
    assert length_plan["actual"]["lead_chars"] == len(result["lead"])
    assert length_plan["actual"]["section_count"] == result["body"].count("## ")
    assert result["pipeline_check"]["input_contract"]["discourse_plan_version"] == "note_4000_v1"
    assert result["natural_style_profile"]["profile_name"].startswith("note_4000_")


def test_phase03_long_form_keeps_anchor_focus_to_closing(monkeypatch) -> None:
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v2")
    generator = ArticleGenerator(llm_client=LongFormAnchorLLM())
    generator.set_input_contract(
        {
            "speaker_profile": "編集担当",
            "audience_profile": "導入検討中の担当者",
            "relationship_mode": "guide",
            "register_policy": {"base_register": "polite"},
        }
    )
    generator.set_interview_answers(
        {
            "message": "導入手順を3段階で示す",
            "target": "導入検討中の担当者",
        }
    )
    result = generator.generate(
        _build_rich_contexts(),
        "導入手順と判断基準、運用注意点、改善サイクルを長文で整理する",
        "ai",
        length_mode="long",
    )

    alignment = result["pipeline_check"]["contract_alignment"]
    body_text = result["body"]
    tail = body_text[len(body_text) * 2 // 3:]

    assert result["pipeline_check"]["zero_base_length_plan"]["targets"]["section_count_target"] >= 6
    assert body_text.count("## ") >= 6
    assert float(alignment.get("anchor_term_coverage", 0.0) or 0.0) >= 0.5
    assert float(alignment.get("must_cover_reflection_rate", 0.0) or 0.0) >= 0.9
    assert any(term in tail for term in ["導入手順", "判断基準", "運用注意点", "改善サイクル"])
