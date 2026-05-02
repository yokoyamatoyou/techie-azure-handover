from __future__ import annotations

from note.article_fetcher import FetchedContent
from note.article_generator import ArticleGenerator
from note.natural_blog_core import (
    build_note4000_discourse_plan,
    build_note4000_length_plan,
    build_note4000_section_prompt,
    build_note4000_style_profile,
)
from note.natural_blog_types import DiscourseSectionPlan


class DummyLLM:
    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        if task_type == "title":
            return "自然なブログタイトル"
        if task_type == "lead":
            return "導入です。読者の関心を先に受け止めます。"
        if task_type == "hashtags":
            return "#自然文 #ブログ"
        if task_type == "zero_base_section":
            return "論点を具体例に落とし込み、次の判断が見えるように整理します。"
        return "本文です。"


def test_note4000_length_plan_has_expected_targets() -> None:
    plan = build_note4000_length_plan(length_mode="normal", section_count=0)

    assert plan["planner"] == "note_4000"
    assert plan["mode"] == "normal"
    assert plan["targets"]["note_chars"] == 4000
    assert plan["targets"]["section_count_target"] == 6
    assert len(plan["section_plans"]) == 6


def test_note4000_discourse_plan_includes_bridge_and_topic_seed() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="ai",
        base_template="ai",
        user_prompt="運用手順と判断基準を整理したい",
        must_cover=["判断基準", "運用手順"],
        user_instruction_terms=["導入手順", "改善サイクル"],
        thesis="読者が迷わず次の一歩を選べることが重要",
        reader_question_candidates=["何から着手すべきか？"],
        length_plan=length_plan,
    )

    assert len(plan) == 6
    assert plan[0].topic_seed
    assert plan[1].bridge_hint
    assert plan[-1].intent == "closing"


def test_note4000_discourse_plan_announcement_filters_generic_audience_from_must_cover() -> None:
    length_plan = build_note4000_length_plan(length_mode="short", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="announcement",
        base_template="announcement",
        user_prompt="メッセージアプリ変更のお知らせ",
        must_cover=["メッセージアプリが変わります", "一般読者"],
        user_instruction_terms=[],
        thesis="変更点と確認事項を整理する",
        reader_question_candidates=["何が変わるか", "何を確認すべきか"],
        length_plan=length_plan,
    )

    assert all("一般読者" not in section.topic_seed for section in plan)
    assert all("一般読者" not in " ".join(section.must_cover) for section in plan)


def test_note4000_discourse_plan_announcement_later_sections_do_not_reuse_opening_fact_as_related_term() -> None:
    length_plan = build_note4000_length_plan(length_mode="short", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="announcement",
        base_template="announcement",
        user_prompt="メッセージアプリ変更のお知らせ",
        must_cover=["メッセージアプリが変わります", "確認事項"],
        user_instruction_terms=[],
        thesis="変更点と確認事項を整理する",
        reader_question_candidates=["何が変わるか", "いつから・誰が対象か", "何を確認すべきか"],
        length_plan=length_plan,
    )

    assert "メッセージアプリが変わります" in plan[0].related_terms
    assert "メッセージアプリが変わります" not in plan[1].related_terms


def test_note4000_section_prompt_uses_positive_rules() -> None:
    style = build_note4000_style_profile(
        article_type="ai",
        focus="explanation",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="背景と論点整理",
            intent="hook",
            target_chars=520,
            topic_seed="判断基準",
            related_terms=["判断基準", "運用手順"],
            reader_question="何から着手すべきか？",
            bridge_hint="次の判断材料へ自然につなぐ",
            must_cover=["判断基準"],
            new_information="判断基準",
        ),
        speaker_profile="編集担当",
        audience_profile="実務担当者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="導入の第一歩を作る",
        recent_summaries=["導入の第一歩を作る"],
        forbidden_topics=["採用活動"],
        allowed_pronouns=["私たち"],
        user_instruction="実務で迷わない記事にする",
        instruction_anchor_terms=["判断基準", "運用手順"],
    )

    assert "【不変ルール】" in prompt
    assert "ユーザー指示（最優先）" in prompt
    assert "直前要約:" in prompt
    assert "無関係に以下の話題へ逸脱しない" in prompt


def test_note4000_section_prompt_snapshot_compact_phase03() -> None:
    style = build_note4000_style_profile(
        article_type="branding",
        focus="experience",
        tone_profile="passionate",
        style_profile="casual",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="価値をどう伝えるか",
            intent="value",
            target_chars=560,
            topic_seed="顧客価値",
            related_terms=["顧客価値", "利用場面", "判断基準", "導入メリット"],
            reader_question="どの価値が自分に関係あるのか？",
            bridge_hint="次の実務判断へ自然につなぐ",
            must_cover=["利用場面の具体化"],
            new_information="顧客価値",
        ),
        speaker_profile="運営担当",
        audience_profile="導入検討者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段で課題を共有した",
        recent_summaries=["前段で課題を共有した", "価値の見立てを整理した"],
        forbidden_topics=["採用活動", "福利厚生"],
        allowed_pronouns=["私たち", "当社"],
        user_instruction="導入判断に必要な情報だけを具体化する",
        instruction_anchor_terms=["顧客価値", "利用場面", "判断基準"],
    )

    non_empty_lines = [line for line in prompt.splitlines() if line.strip()]
    negative_markers = ["使わない", "逸脱しない", "始めない"]
    negative_count = sum(prompt.count(marker) for marker in negative_markers)

    assert len(non_empty_lines) <= 32
    assert "この節の中心語:" in prompt
    assert "関連語:" in prompt
    assert "つなぎ方のヒント:" in prompt
    assert "アンカー語:" in prompt
    assert negative_count <= 4


def test_note4000_section_prompt_snapshot_compact_across_article_types() -> None:
    cases = [
        {
            "article_type": "announcement",
            "heading": "変更内容の整理",
            "intent": "clarify",
            "speaker": "広報担当",
            "audience": "既存ユーザー",
            "topic": "変更点",
            "must_cover": ["影響範囲"],
        },
        {
            "article_type": "case_study",
            "heading": "導入時の判断軸",
            "intent": "practice",
            "speaker": "導入支援担当",
            "audience": "導入検討者",
            "topic": "判断軸",
            "must_cover": ["再現条件"],
        },
    ]

    for case in cases:
        style = build_note4000_style_profile(
            article_type=case["article_type"],
            focus="analysis",
            tone_profile="calm",
            style_profile="formal",
            base_register="polite",
        )
        prompt = build_note4000_section_prompt(
            section=DiscourseSectionPlan(
                heading=case["heading"],
                intent=case["intent"],
                target_chars=520,
                topic_seed=case["topic"],
                related_terms=[case["topic"], "運用手順", "確認ポイント"],
                reader_question="どこを確認すればよいか？",
                bridge_hint="次の段落へ自然につなぐ",
                must_cover=list(case["must_cover"]),
                new_information=case["topic"],
            ),
            speaker_profile=case["speaker"],
            audience_profile=case["audience"],
            relationship_mode="guide",
            style_profile=style,
            previous_summary="直前の要点を整理した",
            recent_summaries=["直前の要点を整理した"],
            forbidden_topics=[],
            allowed_pronouns=["私", "私たち"],
            user_instruction="事実と判断材料を優先する",
            instruction_anchor_terms=[case["topic"], "確認ポイント"],
        )
        non_empty_lines = [line for line in prompt.splitlines() if line.strip()]

        assert len(non_empty_lines) <= 32
        assert "ユーザー指示（最優先）" in prompt
        assert "この節の中心語:" in prompt
        assert "【不変ルール】" in prompt


def test_article_generator_exposes_rich_discourse_plan(monkeypatch) -> None:
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v2")
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_input_contract(
        {
            "speaker_profile": "編集担当",
            "audience_profile": "実務担当者",
            "relationship_mode": "guide",
            "register_policy": {"base_register": "polite"},
        }
    )
    contexts = [FetchedContent(title="テスト資料", content="本文です。", source_type="url")]

    result = generator.generate(contexts, "読者が迷わず進められる記事にする", "ai")

    assert result["zero_base_outline"]
    assert result["zero_base_discourse_plan"]
    assert result["natural_style_profile"]["profile_name"].startswith("note_4000_")
    assert result["pipeline_check"]["input_contract"]["discourse_plan_version"] == "note_4000_v1"
