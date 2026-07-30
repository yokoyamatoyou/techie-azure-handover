from __future__ import annotations

import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator
from note.legacy_current.zero_base_section_helper_mixin import ZeroBaseSectionHelperMixin


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE_ROOT = (REPO_ROOT / "note").resolve()
LEGACY_CURRENT_ROOT = (NOTE_ROOT / "legacy_current").resolve()


class _DummyZeroBaseSectionHelper(ZeroBaseSectionHelperMixin):
    def _safe_contract_value(self, value: object) -> str:
        return str(value or "").strip()

    def _build_audience_prompt_hint(self, audience: str) -> str:
        return f"hint:{audience}"

    def _sanitize_contract_text(self, text: object, max_length: int = 0) -> str:
        sanitized = str(text or "").strip()
        if max_length > 0:
            return sanitized[:max_length]
        return sanitized


def test_slice6_root_zero_base_section_helper_is_same_name_shim() -> None:
    path = NOTE_ROOT / "zero_base_section_helper_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.zero_base_section_helper_mixin import "
        "ZeroBaseSectionHelperMixin"
    ) in content
    assert "from note.article_generator import" not in content
    assert "from note.article_helper_facade import" not in content
    assert content.count("note.legacy_current") == 1


def test_slice6_article_generator_zero_base_section_helper_methods_resolve_to_quarantine() -> None:
    expected = (LEGACY_CURRENT_ROOT / "zero_base_section_helper_mixin.py").resolve()
    method_names = [
        "_zero_base_build_contract_retry_guidance",
        "_zero_base_apply_sanitize_pass",
        "_zero_base_build_section_prompt",
        "_zero_base_extract_section_summary",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).resolve() == expected


def test_slice6_quarantined_zero_base_section_helper_keeps_phase7_dependency() -> None:
    path = LEGACY_CURRENT_ROOT / "zero_base_section_helper_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert "from note import article_generator as" not in content
    assert "from note.article_generator import" not in content
    assert "from human_resonance.phase7_sanitize import Phase7Sanitize" in content
    assert "article_runtime_symbols" not in content


def test_slice6_zero_base_section_helper_smoke_calls() -> None:
    helper = _DummyZeroBaseSectionHelper()

    guidance = helper._zero_base_build_contract_retry_guidance(
        {
            "third_person_speaker_mentions": 1,
            "disallowed_pronoun_hits": ["彼"],
            "advice_tone_count": 1,
        }
    )
    sanitized = helper._zero_base_apply_sanitize_pass("PLACEHOLDER を含む本文です。")
    prompt = helper._zero_base_build_section_prompt(
        heading="見出し",
        new_information="新情報",
        reader_question="疑問",
        previous_summary="要約",
        recent_summaries=["導入", "背景"],
        audience="一般読者",
        must_not_repeat=["同義反復"],
        user_instruction="具体例を入れる",
        instruction_anchor_terms=["導入", "実例"],
        forbidden_topics=["無関係な話題"],
        section_plan={"sentence_min": 2, "sentence_max": 4, "target_chars": 220},
        speaker_profile="担当者として語る",
        relationship_mode="guide",
        register_policy={"allowed_endings": ["です"], "banned_endings": ["だよ"]},
        allowed_pronouns=["私たち"],
        retry_feedback="第三者説明を避ける",
    )
    summary = helper._zero_base_extract_section_summary(
        section_text="## 見出し\n\n第一文です。第二文です。第三文です。",
        fallback="fallback",
    )

    assert "語り手を第三者として説明せず" in guidance
    assert isinstance(sanitized, str)
    assert "【不変ルール】" in prompt
    assert "再生成時の補正指示" in prompt
    assert summary == "第一文です。 第二文です。"
