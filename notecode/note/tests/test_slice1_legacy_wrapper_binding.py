from __future__ import annotations

from typing import Any

from note.article_final_consistency_mixin import ArticleFinalConsistencyMixin
from note.article_generator import ArticleGenerator
from note.article_legacy_compatibility_mixin import ArticleLegacyCompatibilityMixin


STATIC_WRAPPER_CASES: list[tuple[str, str, tuple[Any, ...]]] = [
    (
        "_legacy_is_reference_or_list_paragraph",
        "_is_reference_or_list_paragraph",
        ("出典: https://example.com/source",),
    ),
    (
        "_legacy_rewrite_ending_for_variety",
        "_rewrite_ending_for_variety",
        ("判断材料を整理することが大切です。",),
    ),
    (
        "_legacy_dedupe_cross_section_sentences",
        "_dedupe_cross_section_sentences",
        (
            "## 導入\n判断材料を先に整理することが重要です。\n\n"
            "## 比較\n判断材料を先に整理することが重要です。別の視点も確認します。",
        ),
    ),
    (
        "_legacy_soften_assertive_expressions",
        "_soften_assertive_expressions",
        ("この方法なら必ず成果が出ます。",),
    ),
    (
        "_legacy_strip_heading_top_adversative",
        "_strip_heading_top_adversative",
        ("しかし、導入で確認したいポイントです。",),
    ),
    (
        "_legacy_is_summary_marker_sentence",
        "_is_summary_marker_sentence",
        ("まとめると、判断材料を先にそろえることが重要です。",),
    ),
    (
        "_legacy_normalize_opening_token",
        "_normalize_opening_token",
        ("  しかし  ",),
    ),
    (
        "_legacy_is_logical_required_opening",
        "_is_logical_required_opening",
        ("一方で",),
    ),
    (
        "_legacy_is_suppressible_template_opening",
        "_is_suppressible_template_opening",
        ("まず",),
    ),
    (
        "_legacy_strip_opening_safely",
        "_strip_opening_safely",
        ("まず、結論から共有します。", "まず、"),
    ),
    (
        "_legacy_extract_theme_entities",
        "_extract_theme_entities",
        ("SaaS導入時に確認したい判断ポイント", None),
    ),
    (
        "_legacy_dedupe_similar_headings",
        "_dedupe_similar_headings",
        ("## 導入\n本文\n\n## 導入\n別本文",),
    ),
]


def test_static_wrapper_descriptors_remain_staticmethod() -> None:
    wrapper_names = [wrapper_name for wrapper_name, _, _ in STATIC_WRAPPER_CASES]

    for wrapper_name in wrapper_names:
        descriptor = ArticleLegacyCompatibilityMixin.__dict__[wrapper_name]
        assert isinstance(descriptor, staticmethod), wrapper_name


def test_classmethod_wrapper_descriptor_remains_classmethod() -> None:
    descriptor = ArticleLegacyCompatibilityMixin.__dict__["_legacy_break_ending_monotony"]
    assert isinstance(descriptor, classmethod)


def test_instance_wrapper_descriptors_remain_plain_methods() -> None:
    wrapper_names = [
        "_legacy_dedupe_lead_body",
        "_legacy_get_active_style_profile",
        "_legacy_reduce_target_term_overuse",
        "_legacy_apply_final_consistency_guards",
    ]

    for wrapper_name in wrapper_names:
        descriptor = ArticleLegacyCompatibilityMixin.__dict__[wrapper_name]
        assert not isinstance(descriptor, (staticmethod, classmethod)), wrapper_name
        assert callable(descriptor), wrapper_name


def test_static_wrappers_match_article_final_consistency_owner_outputs() -> None:
    for wrapper_name, owner_name, args in STATIC_WRAPPER_CASES:
        wrapper = getattr(ArticleGenerator, wrapper_name)
        owner = getattr(ArticleFinalConsistencyMixin, owner_name)
        assert wrapper(*args) == owner(*args), wrapper_name


def test_classmethod_wrapper_dispatches_to_cls_override() -> None:
    class _ClassProbe(ArticleGenerator):
        @classmethod
        def _break_ending_monotony(cls, text: str, max_consecutive: int = 3) -> str:
            return f"{cls.__name__}:{text}:{max_consecutive}"

    assert _ClassProbe._legacy_break_ending_monotony("本文", max_consecutive=4) == "_ClassProbe:本文:4"


def test_instance_wrappers_dispatch_to_self_overrides() -> None:
    class _InstanceProbe(ArticleGenerator):
        def _dedupe_lead_body(self, lead: str, body: str) -> tuple[str, str]:
            return ("probe-lead", f"deduped:{lead}|{body}")

        def _get_active_style_profile(self) -> str:
            return "probe-style"

        def _reduce_target_term_overuse(
            self,
            text: str,
            *,
            target_audience: str,
            keep: int = 2,
        ) -> str:
            return f"{text}|{target_audience}|{keep}"

        def _apply_final_consistency_guards(self, lead: str, body: str) -> tuple[str, str]:
            return (f"lead:{lead}", f"body:{body}")

    probe = object.__new__(_InstanceProbe)

    assert probe._legacy_dedupe_lead_body("L", "B") == ("probe-lead", "deduped:L|B")
    assert probe._legacy_get_active_style_profile() == "probe-style"
    assert (
        probe._legacy_reduce_target_term_overuse(
            "本文",
            target_audience="導入担当者",
            keep=5,
        )
        == "本文|導入担当者|5"
    )
    assert probe._legacy_apply_final_consistency_guards("lead", "body") == ("lead:lead", "body:body")
