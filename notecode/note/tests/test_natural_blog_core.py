from __future__ import annotations

from note.article_fetcher import FetchedContent
from note.article_generator import ArticleGenerator
from note.natural_blog_core import (
    _build_instruction_brief,
    _build_prompt_anchor_terms,
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


def test_note4000_discourse_plan_announcement_assigns_unique_fact_slots() -> None:
    length_plan = build_note4000_length_plan(length_mode="short", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="announcement",
        base_template="announcement",
        user_prompt="メッセージアプリ変更のお知らせ",
        must_cover=["2026年4月1日に開始", "対象は既存顧客", "申し込みは公式サイトの専用ページから行います"],
        user_instruction_terms=[],
        thesis="変更点と確認事項を整理する",
        reader_question_candidates=["何が変わるか", "誰が対象か", "何を確認すべきか"],
        length_plan=length_plan,
    )

    slots = [section.fact_slot for section in plan]
    assert slots[:5] == ["change", "who_when", "impact", "check", "caution"]


def test_note4000_discourse_plan_announcement_distributes_unmatched_dense_must_cover_to_later_sections() -> None:
    length_plan = build_note4000_length_plan(length_mode="short", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="announcement",
        base_template="announcement",
        user_prompt="SSO設定変更のお知らせ",
        must_cover=[
            "2026年4月1日に開始",
            "対象は既存顧客",
            "既存セッションは継続する",
            "申し込みは公式サイトの専用ページから行います",
        ],
        user_instruction_terms=[],
        thesis="変更点と確認事項を整理する",
        reader_question_candidates=["何が変わるか", "いつから・誰が対象か", "何を確認すべきか"],
        length_plan=length_plan,
    )

    impact_section = next(section for section in plan if section.intent == "impact")
    assert "既存セッションは継続する" in impact_section.must_cover


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
    assert "主題の要約:" in prompt
    assert "直前要約:" in prompt
    assert "無関係に以下の話題へ逸脱しない" in prompt
    assert "主語省略:" in prompt
    assert "文末運用:" in prompt
    assert "改行と構造:" in prompt
    assert "文の完結性:" in prompt


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

    instruction_brief = _build_instruction_brief(
        "導入判断に必要な情報だけを具体化する",
        topic_seed="顧客価値",
        must_cover=["利用場面の具体化"],
        article_profile=style.profile_name,
    )
    non_empty_lines = [line for line in prompt.splitlines() if line.strip()]
    negative_markers = ["使わない", "逸脱しない", "始めない"]
    negative_count = sum(prompt.count(marker) for marker in negative_markers)

    assert len(non_empty_lines) <= 28
    assert "この節の中心語:" in prompt
    assert "関連語:" in prompt
    assert "つなぎ方のヒント:" in prompt
    assert "アンカー語:" in prompt
    assert prompt.count(instruction_brief) == 1
    assert negative_count <= 6


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

        assert len(non_empty_lines) <= 28
        assert "主題の要約:" in prompt
        assert "この節の中心語:" in prompt
        assert "【不変ルール】" in prompt


def test_note4000_section_prompt_snapshot_compact_daily_and_comparative() -> None:
    cases = [
        {
            "article_type": "daily_story",
            "focus": "experience",
            "tone_profile": "warm",
            "style_profile": "casual",
            "heading": "その日に引っかかったこと",
            "intent": "hook",
            "speaker": "現場担当",
            "audience": "同じ立場の読者",
            "topic": "学び",
            "related_terms": ["学び", "背景", "変化"],
            "reader_question": "何から見ればよいか？",
            "must_cover": ["背景の共有"],
            "user_instruction": "現場で気づいた差を具体に書く",
            "instruction_anchor_terms": ["学び", "背景"],
        },
        {
            "article_type": "comparative_review",
            "focus": "analysis",
            "tone_profile": "calm",
            "style_profile": "formal",
            "heading": "比較の判断軸",
            "intent": "criteria",
            "speaker": "比較検証担当",
            "audience": "比較検討中の担当者",
            "topic": "比較軸",
            "related_terms": ["比較軸", "価格", "用途"],
            "reader_question": "どの条件を優先すべきか？",
            "must_cover": ["価格", "用途"],
            "user_instruction": "比較軸をずらさずに整理する",
            "instruction_anchor_terms": ["比較軸", "価格", "用途"],
        },
    ]

    for case in cases:
        style = build_note4000_style_profile(
            article_type=case["article_type"],
            focus=case["focus"],
            tone_profile=case["tone_profile"],
            style_profile=case["style_profile"],
            base_register="polite",
        )
        prompt = build_note4000_section_prompt(
            section=DiscourseSectionPlan(
                heading=case["heading"],
                intent=case["intent"],
                target_chars=520,
                topic_seed=case["topic"],
                related_terms=case["related_terms"],
                reader_question=case["reader_question"],
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
            user_instruction=case["user_instruction"],
            instruction_anchor_terms=case["instruction_anchor_terms"],
        )
        non_empty_lines = [line for line in prompt.splitlines() if line.strip()]

        assert len(non_empty_lines) <= 28
        assert "主題の要約:" in prompt


def test_note4000_style_profile_separates_branding_and_daily_story() -> None:
    branding_style = build_note4000_style_profile(
        article_type="branding",
        focus="experience",
        tone_profile="warm",
        style_profile="balanced",
        base_register="polite",
    )
    daily_style = build_note4000_style_profile(
        article_type="daily_story",
        focus="experience",
        tone_profile="warm",
        style_profile="balanced",
        base_register="polite",
    )

    assert branding_style.profile_name == "note_4000_branding"
    assert daily_style.profile_name == "note_4000_daily"
    assert branding_style.information_density == "value_evidence"
    assert daily_style.information_density == "scene_then_insight"
    assert branding_style.subject_omission_policy == "light_corporate_anchor"
    assert "ことです。" not in branding_style.preferred_endings
    assert "と思います。" not in branding_style.preferred_endings
    assert "と感じます。" in branding_style.preferred_endings
    assert daily_style.ending_distribution_hint == "reflective_mix"


def test_note4000_discourse_plan_separates_branding_and_daily_story_headings() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    branding_plan = build_note4000_discourse_plan(
        article_type="branding",
        base_template="branding",
        user_prompt="サービスの価値を伝えたい",
        must_cover=["価値", "現場の工夫"],
        user_instruction_terms=["判断理由"],
        thesis="価値が伝わる背景を書く",
        reader_question_candidates=["何が価値なのか"],
        length_plan=length_plan,
    )
    daily_plan = build_note4000_discourse_plan(
        article_type="daily_story",
        base_template="daily_story",
        user_prompt="日々の気づきを書きたい",
        must_cover=["気づき", "変化"],
        user_instruction_terms=["違和感"],
        thesis="小さな学びに着地する",
        reader_question_candidates=["何が引っかかったのか"],
        length_plan=length_plan,
    )

    assert branding_plan[0].heading == "私たちが向き合っている課題"
    assert daily_plan[0].heading == "その日に引っかかったこと"


def test_note4000_section_prompt_contains_article_specific_guidance() -> None:
    branding_style = build_note4000_style_profile(
        article_type="branding",
        focus="experience",
        tone_profile="warm",
        style_profile="balanced",
        base_register="polite",
    )
    daily_style = build_note4000_style_profile(
        article_type="daily_story",
        focus="experience",
        tone_profile="warm",
        style_profile="balanced",
        base_register="polite",
    )
    section = DiscourseSectionPlan(
        heading="見出し",
        intent="hook",
        target_chars=520,
        topic_seed="気づき",
        related_terms=["気づき", "背景"],
        reader_question="何が変わったのか？",
        bridge_hint="次の流れへつなぐ",
        must_cover=["背景"],
        new_information="気づき",
    )

    branding_prompt = build_note4000_section_prompt(
        section=section,
        speaker_profile="ブランド担当",
        audience_profile="見込み読者",
        relationship_mode="guide",
        style_profile=branding_style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私たち"],
        user_instruction="価値を具体化する",
        instruction_anchor_terms=["価値", "背景"],
    )
    daily_prompt = build_note4000_section_prompt(
        section=section,
        speaker_profile="現場担当",
        audience_profile="読者",
        relationship_mode="guide",
        style_profile=daily_style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="小さな気づきを書く",
        instruction_anchor_terms=["気づき", "背景"],
    )

    assert "ブランド記事として" in branding_prompt
    assert "日常記事として" in daily_prompt


def test_note4000_style_profile_separates_industry_analysis_and_comparative_review() -> None:
    industry_style = build_note4000_style_profile(
        article_type="industry_analysis",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    review_style = build_note4000_style_profile(
        article_type="comparative_review",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )

    assert industry_style.profile_name == "note_4000_industry_analysis"
    assert review_style.profile_name == "note_4000_comparative_review"
    assert industry_style.information_density == "market_structure"
    assert review_style.information_density == "criteria_then_fit"
    assert "考えられます。" in industry_style.preferred_endings
    assert "向いています。" in review_style.preferred_endings


def test_prompt_anchor_terms_budget_prefers_must_cover_over_topic_seed_for_branding() -> None:
    anchors = _build_prompt_anchor_terms(
        must_cover=["使い始めた直後に迷わない", "判断がそろう設計"],
        topic_seed="運用の迷いを減らす",
        related_terms=["導入初期", "利用場面", "機能比較"],
        reader_question="何を基準に選ぶべきか？",
        article_profile="note_4000_branding",
        extra_terms=["小規模SaaS", "機能の多さ"],
        limit=4,
    )

    assert len(anchors) <= 4
    assert "使い始めた直後に迷わない" in anchors
    assert "判断がそろう設計" in anchors
    assert "運用の迷いを減らす" not in anchors


def test_prompt_anchor_terms_skip_extra_term_when_it_matches_topic_seed() -> None:
    anchors = _build_prompt_anchor_terms(
        must_cover=["比較軸を明示する"],
        topic_seed="市場差分を整理する",
        related_terms=["市場", "差分"],
        reader_question="何が変わっているのか？",
        article_profile="note_4000_industry_analysis",
        extra_terms=["市場差分を整理する", "意思決定"],
        limit=4,
    )

    assert len(anchors) <= 4
    assert "市場差分を整理する" not in anchors
    assert "意思決定" in anchors


def test_case_study_anchor_budget_skips_topic_seed_echo_in_extra_terms() -> None:
    anchors = _build_prompt_anchor_terms(
        must_cover=["再現条件を残す"],
        topic_seed="初動整理の見直し",
        related_terms=["進め方", "結果", "再現条件"],
        reader_question="どこまで再現できるか？",
        article_profile="note_4000_case_study",
        extra_terms=["初動整理の見直し", "限界"],
        limit=4,
    )

    assert len(anchors) <= 4
    assert "初動整理の見直し" not in anchors
    assert "再現条件を残す" in anchors
    assert "結果" not in anchors


def test_case_study_instruction_brief_normalizes_long_topic_phrase() -> None:
    brief = _build_instruction_brief(
        "オンボーディング初回設定の案内導線を見直した事例。成功談に寄せすぎず、最初にどこで迷ったか、どう直したか、どの条件で再現できるかを含める",
        topic_seed="再現条件",
        must_cover=["最初にどこで迷ったか", "どの条件で再現できるか"],
        article_profile="note_4000_case_study",
    )

    assert "オンボーディング初回設定の案内導線を見直した事例" not in brief
    assert "最初にどこで迷ったか" in brief or "再現条件" in brief


def test_case_study_discourse_plan_does_not_use_long_raw_topic_phrase_as_seed() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="case_study",
        base_template="analysis",
        user_prompt="オンボーディング初回設定の案内導線を見直した事例。成功談に寄せすぎず、最初にどこで迷ったか、どう直したか、どの条件で再現できるかを含める",
        must_cover=["課題を定義する", "再現手順を崩さない", "結果の条件を明示する"],
        user_instruction_terms=["課題を定義する", "再現手順を崩さない", "結果の条件を明示する"],
        thesis="最初にどこで迷ったかと再現条件を分けて示す",
        reader_question_candidates=["何を先に理解すべきか"],
        length_plan=length_plan,
    )

    assert plan
    assert all("オンボーディング初回設定の案内導線を見直した事例" not in section.topic_seed for section in plan)
    assert any("再現" in section.topic_seed or "課題" in section.topic_seed for section in plan)


def test_case_study_discourse_plan_reserves_change_and_condition_sections() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="case_study",
        base_template="analysis",
        user_prompt="初回設定の導線を見直した事例",
        must_cover=["どこで迷ったか", "どう直したか", "どの条件で再現できるか"],
        user_instruction_terms=["導線見直し"],
        thesis="迷いが生まれた場面と再現条件を分けて示す",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    intents = [section.intent for section in plan]

    assert "change" in intents
    assert "condition" in intents
    assert any(section.heading == "結果として何が変わったか" for section in plan)
    assert any(section.heading == "どの条件なら再現できるか" for section in plan)


def test_company_intro_discourse_plan_sparse_input_does_not_frontload_depth_defaults() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="branding",
        base_template="company_introduction",
        user_prompt="監査対応SaaS企業の紹介",
        must_cover=["事業内容"],
        user_instruction_terms=[],
        thesis="何をしている会社かが分かるようにする",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    assert "歩み" not in plan[0].related_terms
    assert "提供価値" not in plan[0].related_terms
    assert "提供価値" not in plan[1].related_terms


def test_company_intro_discourse_plan_sparse_input_avoids_hardcoded_depth_seed_for_later_sections() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="branding",
        base_template="company_introduction",
        user_prompt="監査対応SaaS企業の紹介",
        must_cover=["事業内容"],
        user_instruction_terms=[],
        thesis="何をしている会社かが分かるようにする",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    assert plan[3].topic_seed != "歩み"


def test_company_intro_discourse_plan_overview_only_source_prunes_unsupported_depth_terms() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="branding",
        base_template="company_introduction",
        user_prompt="医療支援SaaS企業の紹介",
        must_cover=[],
        user_instruction_terms=[],
        thesis="何をしている会社かが分かるようにする",
        reader_question_candidates=[],
        length_plan=length_plan,
        source_grounding_items=[
            {"bucket": "overview", "fact_text": "医療機関向けの業務SaaSを提供する。"},
        ],
    )

    topic_seeds = [section.topic_seed for section in plan]
    headings = [section.heading for section in plan]
    reader_questions = [section.reader_question for section in plan]
    bridge_hints = [section.bridge_hint for section in plan]

    assert "強み" not in topic_seeds
    assert "歩み" not in topic_seeds
    assert "いま提供している価値" not in topic_seeds
    assert headings == [
        "会社の輪郭を最初に置く",
        "どんな事業を担っているか",
        "会社の輪郭をあらためて結ぶ",
    ]
    assert not any("歩み" in item for item in reader_questions)
    assert not any("価値" in item for item in reader_questions)
    assert not any("歩み" in item for item in bridge_hints)
    assert not any("提供価値" in item for item in bridge_hints)
    assert topic_seeds[-1] == "会社の輪郭を結ぶ"


def test_company_intro_discourse_plan_promotes_only_source_backed_depth_buckets() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="branding",
        base_template="company_introduction",
        user_prompt="京都の業務代行会社の紹介",
        must_cover=[],
        user_instruction_terms=[],
        thesis="会社の輪郭と歩みを伝える",
        reader_question_candidates=[],
        length_plan=length_plan,
        source_grounding_items=[
            {"bucket": "overview", "fact_text": "データ入力と事務代行を担う。"},
            {"bucket": "history", "fact_text": "1964年創業。"},
        ],
    )

    topic_seeds = [section.topic_seed for section in plan]
    headings = [section.heading for section in plan]

    assert "歩み" in topic_seeds
    assert "強み" not in topic_seeds
    assert "いま提供している価値" not in topic_seeds
    assert headings == [
        "会社の輪郭を最初に置く",
        "どんな事業を担っているか",
        "歩みから見える姿勢",
        "会社の輪郭をあらためて結ぶ",
    ]


def test_company_intro_discourse_plan_adds_trust_intro_reference_policy() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="branding",
        base_template="company_introduction",
        user_prompt="監査対応SaaS企業の紹介",
        must_cover=["事業内容", "強み", "導入初期の支援体制"],
        user_instruction_terms=["導入初期", "支援体制"],
        thesis="現在の事業と支え方が分かるようにする",
        reader_question_candidates=[],
        length_plan=length_plan,
        source_grounding_items=[
            {"bucket": "overview", "fact_text": "監査対応SaaSを提供する。"},
            {"bucket": "strength", "fact_text": "導入初期の支援体制を強みとしている。"},
        ],
    )

    assert getattr(plan[0], "direction_family", "") == "trust_intro"
    assert getattr(plan[0], "speaker_reference_policy", "") == "company_name_once"
    assert getattr(plan[0], "subject_reintroduction_policy", "") == "lead_only"
    assert getattr(plan[0], "proper_noun_repeat_cap", None) == 1
    assert any(
        getattr(section, "speaker_reference_policy", "") in {"tousha_preferred", "subject_omission_preferred"}
        for section in plan[1:-1]
    )
    assert getattr(plan[-1], "speaker_reference_policy", "") == "watashitachi_preferred"
    assert getattr(plan[-1], "subject_reintroduction_policy", "") == "closing_reanchor"


def test_explanatory_discourse_plan_adds_no_first_person_reference_policy() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="explanatory_article",
        base_template="analysis",
        user_prompt="オンボーディング時に入力項目を増やしすぎない考え方を整理する",
        must_cover=["入力項目", "判断条件", "例外"],
        user_instruction_terms=["入力項目", "判断条件"],
        thesis="増やす条件と増やさない条件を分ける",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    assert plan
    assert all(getattr(section, "direction_family", "") == "explain_analysis" for section in plan)
    assert all(getattr(section, "speaker_reference_policy", "") == "no_first_person" for section in plan)
    assert all(getattr(section, "proper_noun_repeat_cap", None) == 1 for section in plan)
    assert all(
        getattr(section, "subject_reintroduction_policy", "") == "section_shift_only" for section in plan[:-1]
    )
    assert getattr(plan[-1], "subject_reintroduction_policy", "") == "closing_reanchor"


def test_daily_story_discourse_plan_does_not_add_reference_policy_in_first_slice() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="daily_story",
        base_template="daily_story",
        user_prompt="導入初期の問い合わせ対応で気づいたことを書く",
        must_cover=["気づき", "変化"],
        user_instruction_terms=["導入初期"],
        thesis="小さな学びを次の行動につなげる",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    assert plan
    assert all(getattr(section, "direction_family", "") == "" for section in plan)
    assert all(getattr(section, "speaker_reference_policy", "") == "" for section in plan)


def test_case_study_long_discourse_plan_keeps_canonical_six_sections() -> None:
    length_plan = build_note4000_length_plan(length_mode="long", section_count=6, max_section_count=6)
    plan = build_note4000_discourse_plan(
        article_type="case_study",
        base_template="analysis",
        user_prompt="オンボーディング初回設定の案内導線を見直した事例",
        must_cover=["最初にどこで迷ったか", "どう直したか", "どの条件で再現できるか"],
        user_instruction_terms=["導線見直し", "再現条件"],
        thesis="迷いが生まれた場面と再現条件を分けて示す",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    headings = [section.heading for section in plan]

    assert len(plan) == 6
    assert "実務補足 3" not in headings
    assert headings[-1] == "どの条件なら再現できるか"


def test_case_study_condition_section_prefers_condition_terms_over_cycled_must_cover() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="case_study",
        base_template="analysis",
        user_prompt="オンボーディング初回設定の案内導線を見直した事例",
        must_cover=["課題", "進め方", "結果の条件"],
        user_instruction_terms=["最初にどこで迷ったか", "どう直したか", "どの条件で再現できるか"],
        thesis="最初にどこで迷ったかと再現条件を分けて示す",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    condition_section = next(section for section in plan if section.intent == "condition")

    assert "条件" in condition_section.topic_seed or "再現" in condition_section.topic_seed
    assert any("条件" in item or "再現" in item or "前提" in item for item in condition_section.must_cover)
    assert any("再現" in item or "前提" in item or "限界" in item for item in condition_section.related_terms)


def test_industry_analysis_discourse_plan_compresses_raw_topic_phrase() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="industry_analysis",
        base_template="analysis",
        user_prompt="SaaS導入の現場で、機能数の話に引っ張られず、運用差分と移行条件の見方を整理したい業界分析記事",
        must_cover=["構造変化", "主要差分", "意思決定の示唆"],
        user_instruction_terms=["運用差分", "移行条件"],
        thesis="機能数ではなく運用差分と移行条件で判断する",
        reader_question_candidates=["何を先に見るべきか"],
        length_plan=length_plan,
    )

    assert plan
    assert all("業界分析記事" not in section.topic_seed for section in plan)
    assert any("運用" in section.topic_seed or "差分" in section.topic_seed for section in plan)


def test_branding_discourse_plan_compresses_raw_prompt_terms() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="branding",
        base_template="branding",
        user_prompt="小規模SaaSの導入初期で、機能の多さより運用の迷いを減らす価値を伝えるブランド記事",
        must_cover=["使い始めた直後に迷わない", "判断がそろう設計"],
        user_instruction_terms=["導入初期", "現場判断"],
        thesis="価値が立ち上がる背景と現場の工夫を書く",
        reader_question_candidates=["何を基準に選ぶべきか"],
        length_plan=length_plan,
    )

    assert plan
    assert all("小規模SaaSの導入初期で、機能の多さより運用の迷いを減らす価値を伝えるブランド記事" not in section.topic_seed for section in plan)
    assert all("ブランド記事" not in section.topic_seed for section in plan)
    assert any("判断" in section.topic_seed or "導入初期" in section.topic_seed for section in plan)


def test_note4000_discourse_plan_separates_industry_analysis_and_comparative_review_headings() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    industry_plan = build_note4000_discourse_plan(
        article_type="industry_analysis",
        base_template="analysis",
        user_prompt="業界の流れを整理したい",
        must_cover=["構造変化", "主要差分"],
        user_instruction_terms=["意思決定"],
        thesis="市場変化を判断につなげる",
        reader_question_candidates=["何が変わっているのか"],
        length_plan=length_plan,
    )
    review_plan = build_note4000_discourse_plan(
        article_type="comparative_review",
        base_template="analysis",
        user_prompt="複数候補を比較したい",
        must_cover=["比較条件", "用途別の結論"],
        user_instruction_terms=["評価軸"],
        thesis="比較条件をそろえて選び方を示す",
        reader_question_candidates=["どう比べればよいか"],
        length_plan=length_plan,
    )

    assert industry_plan[0].heading == "市場の前提と論点"
    assert review_plan[0].heading == "比較の前提条件をそろえる"


def test_comparative_review_long_discourse_plan_keeps_canonical_six_sections() -> None:
    length_plan = build_note4000_length_plan(length_mode="long", section_count=6, max_section_count=6)
    plan = build_note4000_discourse_plan(
        article_type="comparative_review",
        base_template="analysis",
        user_prompt="複数候補の比較レビュー",
        must_cover=["比較条件", "評価軸", "用途別の結論"],
        user_instruction_terms=["比較条件", "評価軸", "用途別"],
        thesis="比較条件をそろえて用途別に結論を分ける",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    headings = [section.heading for section in plan]
    intents = [section.intent for section in plan]

    assert len(plan) == 6
    assert headings == [
        "比較の前提条件をそろえる",
        "評価軸を先に決める",
        "候補ごとの強みと弱み",
        "用途別に向く選び方",
        "選ぶ前に確認したい点",
        "結論とおすすめの分け方",
    ]
    assert intents == ["hook", "criteria", "comparison", "fit", "caution", "closing"]


def test_comparative_review_discourse_plan_prefers_intent_local_focus_terms() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="comparative_review",
        base_template="analysis",
        user_prompt="SaaS導入支援ツールを比較し、比較条件、評価軸、用途別の向き不向きを整理する",
        must_cover=["比較条件", "評価軸", "用途別に向くケース"],
        user_instruction_terms=["前提条件", "判断基準", "向くケース"],
        thesis="比較条件を先にそろえ、用途別に結論を分ける",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    criteria_section = next(section for section in plan if section.intent == "criteria")
    fit_section = next(section for section in plan if section.intent == "fit")
    caution_section = next(section for section in plan if section.intent == "caution")
    closing_section = next(section for section in plan if section.intent == "closing")

    assert any("評価軸" in item or "判断基準" in item for item in criteria_section.must_cover)
    assert any("用途" in item or "向く" in item for item in fit_section.must_cover)
    assert any("前提" in item or "例外" in item for item in caution_section.must_cover)
    assert any("結論" in item or "おすすめ" in item for item in closing_section.must_cover)
    assert "結論" in closing_section.topic_seed


def test_comparative_review_discourse_plan_uses_specific_fit_carry_for_caution() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="comparative_review",
        base_template="analysis",
        user_prompt="社内ナレッジ共有SaaSの比較レビュー。比較条件、価格、用途別の向き不向き、運用体制の違いを整理する",
        must_cover=["価格", "用途", "差分"],
        user_instruction_terms=["価格", "用途"],
        thesis="価格と用途を軸に、用途別の向き不向きまで整理する",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    criteria_section = next(section for section in plan if section.intent == "criteria")
    comparison_section = next(section for section in plan if section.intent == "comparison")
    fit_section = next(section for section in plan if section.intent == "fit")
    caution_section = next(section for section in plan if section.intent == "caution")
    closing_section = next(section for section in plan if section.intent == "closing")

    assert "価格" in criteria_section.related_terms
    assert comparison_section.related_terms == ["価格", "差分", "強み", "弱み"]
    assert fit_section.related_terms == ["差分", "価格", "用途別", "向くケース"]
    assert caution_section.related_terms == ["向くケース", "価格", "確認事項", "前提"]
    assert "用途別" not in caution_section.related_terms
    assert closing_section.related_terms == ["前提", "価格", "結論", "おすすめの分け方"]


def test_comparative_review_discourse_plan_keeps_generic_closing_carry_without_specific_axis_terms() -> None:
    length_plan = build_note4000_length_plan(length_mode="normal", section_count=0)
    plan = build_note4000_discourse_plan(
        article_type="comparative_review",
        base_template="analysis",
        user_prompt="SaaS導入支援ツールの比較レビュー。比較条件、評価軸、候補差分、用途別の向き不向き、確認事項を含める",
        must_cover=["比較条件", "評価軸", "差分", "用途別の向き不向き"],
        user_instruction_terms=["評価軸", "用途別"],
        thesis="比較条件を先にそろえ、用途別に結論を分ける",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    closing_section = next(section for section in plan if section.intent == "closing")

    assert closing_section.related_terms == ["前提", "用途別", "評価軸", "結論"]


def test_note4000_section_prompt_contains_analysis_specific_guidance() -> None:
    industry_style = build_note4000_style_profile(
        article_type="industry_analysis",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    review_style = build_note4000_style_profile(
        article_type="comparative_review",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    section = DiscourseSectionPlan(
        heading="見出し",
        intent="comparison",
        target_chars=520,
        topic_seed="差分",
        related_terms=["差分", "評価軸"],
        reader_question="どこを比べるべきか？",
        bridge_hint="次へつなぐ",
        must_cover=["評価軸"],
        new_information="差分",
    )

    industry_prompt = build_note4000_section_prompt(
        section=section,
        speaker_profile="アナリスト",
        audience_profile="意思決定者",
        relationship_mode="guide",
        style_profile=industry_style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="市場差分を整理する",
        instruction_anchor_terms=["市場", "差分"],
    )
    review_prompt = build_note4000_section_prompt(
        section=section,
        speaker_profile="比較検証担当",
        audience_profile="比較検討中の読者",
        relationship_mode="guide",
        style_profile=review_style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="比較条件をそろえる",
        instruction_anchor_terms=["比較条件", "差分"],
    )

    assert "業界分析記事として" in industry_prompt
    assert "比較レビューとして" in review_prompt
    assert "差分や示唆は『ことです』で名詞化せず" in industry_prompt
    assert "比較条件、評価軸ごとの差分、用途別の向き不向きを順に書く" not in review_prompt
    assert "比較条件を先に示し、その後に評価軸ごとの差分、最後に用途別の結論を置く" not in review_prompt
    assert "ことです運用:" not in review_prompt
    assert "ことです運用:" not in industry_prompt


def test_comparative_review_section_prompt_adds_intent_local_rules() -> None:
    review_style = build_note4000_style_profile(
        article_type="comparative_review",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="用途別に向く選び方",
            intent="fit",
            target_chars=520,
            topic_seed="用途別の向き不向き",
            related_terms=["用途別", "向くケース", "向かないケース"],
            reader_question="どの用途に向いているか？",
            bridge_hint="確認事項へつなぐ",
            must_cover=["用途別", "向くケース", "向かないケース"],
            new_information="用途別の向き不向き",
        ),
        speaker_profile="比較検証担当",
        audience_profile="比較検討中の読者",
        relationship_mode="guide",
        style_profile=review_style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="比較条件をそろえる",
        instruction_anchor_terms=["用途別", "向くケース", "向かないケース"],
    )

    assert "節の補足:" in prompt
    assert "万人向けの断定にしない" in prompt
    assert "誰にでも最適" in prompt
    assert "助詞や接続の途中で句点を打たず" in prompt


def test_comparative_review_comparison_and_caution_prompts_guard_dangling_fragments() -> None:
    review_style = build_note4000_style_profile(
        article_type="comparative_review",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    comparison_prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="候補ごとの強みと弱み",
            intent="comparison",
            target_chars=520,
            topic_seed="候補差分",
            related_terms=["評価軸", "比較条件", "強み"],
            reader_question="候補ごとの差分は何か？",
            bridge_hint="次に用途別の向き不向きへつなぐ",
            must_cover=["強み", "弱み", "差分"],
            new_information="候補差分",
        ),
        speaker_profile="比較検証担当",
        audience_profile="比較検討中の読者",
        relationship_mode="guide",
        style_profile=review_style,
        previous_summary="評価軸を固定した",
        recent_summaries=["比較条件をそろえた", "評価軸を固定した"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="候補差分",
        instruction_anchor_terms=["評価軸", "比較条件", "差分"],
    )
    caution_prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="選ぶ前に確認したい点",
            intent="caution",
            target_chars=520,
            topic_seed="確認事項",
            related_terms=["用途別", "前提", "例外"],
            reader_question="選ぶ前に何を確認すべきか？",
            bridge_hint="最後の結論へつなぐ",
            must_cover=["確認事項", "前提", "例外"],
            new_information="確認事項",
        ),
        speaker_profile="比較検証担当",
        audience_profile="比較検討中の読者",
        relationship_mode="guide",
        style_profile=review_style,
        previous_summary="用途別の向き不向きを分けた",
        recent_summaries=["候補差分を比較した", "用途別の向き不向きを分けた"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="確認事項",
        instruction_anchor_terms=["確認事項", "前提", "例外"],
    )

    assert "『〜ではなく。』『〜なら。』『〜は。』のような切れ文で終えない" in comparison_prompt
    assert "『〜ではなく。』『〜なら。』『〜は。』のような切れ文で終えない" in caution_prompt


def test_section_prompt_opening_rule_discourages_heading_restatement_in_first_sentence() -> None:
    style = build_note4000_style_profile(
        article_type="explanatory_article",
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
            topic_seed="背景",
            related_terms=["論点", "前提", "判断軸"],
            reader_question="何を先に理解すべきか？",
            bridge_hint="次に現場で起きやすい課題へつなぐ",
            must_cover=["前提", "判断軸", "実務での使いどころ"],
            new_information="背景",
        ),
        speaker_profile="編集担当",
        audience_profile="実務担当者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="導入の第一歩を作る",
        recent_summaries=["導入の第一歩を作る"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="背景",
        instruction_anchor_terms=["前提", "判断軸", "実務"],
    )

    assert "文頭表現に変化をつけ、接続詞頼みの開始を続けない" in prompt
    assert "見出しや主題文を言い換えただけの一文で始めない" in prompt


def test_comparative_review_closing_prompt_avoids_absolute_winner_wording() -> None:
    review_style = build_note4000_style_profile(
        article_type="comparative_review",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="結論とおすすめの分け方",
            intent="closing",
            target_chars=520,
            topic_seed="結論",
            related_terms=["前提", "結論", "おすすめの分け方"],
            reader_question="用途別にどう結論づけるか？",
            bridge_hint="最後に一律の優劣ではなく、用途別に結論を分けて結ぶ",
            must_cover=["結論", "おすすめの分け方", "用途別"],
            new_information="結論",
        ),
        speaker_profile="比較検証担当",
        audience_profile="比較検討中の読者",
        relationship_mode="guide",
        style_profile=review_style,
        previous_summary="前提と例外を整理した",
        recent_summaries=["用途別の向き不向きを分けた", "前提と例外を整理した"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="用途別にどう結論づけるか？",
        instruction_anchor_terms=["結論", "おすすめの分け方", "用途別", "前提"],
    )

    assert "一律の優劣" in prompt
    assert "絶対優劣" not in prompt
    assert "誰にでも最適" in prompt
    assert "『〜ではなく。』『〜なら。』『〜は。』のような切れ文で終えない" in prompt


def test_industry_decision_prompt_adds_local_kotodesu_policy() -> None:
    style = build_note4000_style_profile(
        article_type="industry_analysis",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="意思決定で見るべき指標",
            intent="decision",
            target_chars=520,
            topic_seed="判断指標",
            related_terms=["比較軸", "意思決定"],
            reader_question="何を基準に判断するか？",
            bridge_hint="次の示唆へつなぐ",
            must_cover=["比較軸"],
            new_information="判断指標",
        ),
        speaker_profile="アナリスト",
        audience_profile="意思決定者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私"],
        user_instruction="市場差分を整理する",
        instruction_anchor_terms=["比較軸", "意思決定"],
    )

    assert "ことです運用:" in prompt
    assert "0〜1回までに抑え" in prompt


def test_case_study_closing_prompt_does_not_add_local_kotodesu_policy() -> None:
    style = build_note4000_style_profile(
        article_type="case_study",
        focus="analysis",
        tone_profile="calm",
        style_profile="balanced",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="まとめと次の一歩",
            intent="closing",
            target_chars=520,
            topic_seed="次の一歩",
            related_terms=["結果", "再現条件"],
            reader_question="次に何をするか？",
            bridge_hint="本文全体を踏まえて着地する",
            must_cover=["再現条件"],
            new_information="次の一歩",
        ),
        speaker_profile="導入担当",
        audience_profile="実務担当者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私たち"],
        user_instruction="進め方と結果を整理する",
        instruction_anchor_terms=["結果", "再現条件"],
    )

    assert "ことです運用:" not in prompt
    assert "節の組み立て:" not in prompt
    assert "節の補足:" in prompt
    assert "本文の要約だけで閉じず" in prompt
    assert "『なります』で締めない" in prompt


def test_case_study_reflection_prompt_does_not_add_closing_local_rule() -> None:
    style = build_note4000_style_profile(
        article_type="case_study",
        focus="analysis",
        tone_profile="calm",
        style_profile="balanced",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="改善につなげる見方",
            intent="reflection",
            target_chars=520,
            topic_seed="改善の見方",
            related_terms=["結果", "再現条件"],
            reader_question="何が分かったか？",
            bridge_hint="ここから締めに向かう",
            must_cover=["再現条件"],
            new_information="改善の見方",
        ),
        speaker_profile="導入担当",
        audience_profile="実務担当者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私たち"],
        user_instruction="進め方と結果を整理する",
        instruction_anchor_terms=["結果", "再現条件"],
    )

    assert "節の補足:" not in prompt


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


def test_section_prompt_avoids_raw_topic_echo_and_meta_lines() -> None:
    style = build_note4000_style_profile(
        article_type="branding",
        focus="experience",
        tone_profile="warm",
        style_profile="balanced",
        base_register="polite",
    )
    section = DiscourseSectionPlan(
        heading="判断の基準と優先順位",
        intent="decision",
        target_chars=520,
        topic_seed="運用の迷いを減らす",
        related_terms=["運用", "判断", "導入初期"],
        reader_question="何を基準に選ぶべきか？",
        bridge_hint="ここから選定基準へつなぐ",
        must_cover=["使い始めた直後に迷わない", "判断がそろう設計"],
        new_information="運用の迷いを減らす",
    )
    long_instruction = "小規模SaaSの導入初期で、機能の多さより運用の迷いを減らす価値を伝えるブランド記事"

    prompt = build_note4000_section_prompt(
        section=section,
        speaker_profile="ブランド担当",
        audience_profile="見込み読者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私たち"],
        user_instruction=long_instruction,
        instruction_anchor_terms=["運用", "判断", "導入初期"],
    )

    assert long_instruction not in prompt
    assert "主題の要約:" in prompt
    assert "『この記事で』『この記事として言えば』" in prompt
    assert "見出しや主題文を言い換えただけの一文で始めない" in prompt
    assert "偏り回避:" in prompt


def test_case_study_prompt_discourages_kotodesu_summary_endings() -> None:
    style = build_note4000_style_profile(
        article_type="case_study",
        focus="analysis",
        tone_profile="calm",
        style_profile="balanced",
        base_register="polite",
    )
    section = DiscourseSectionPlan(
        heading="結果と再現条件",
        intent="closing",
        target_chars=520,
        topic_seed="結果の整理",
        related_terms=["結果", "再現条件"],
        reader_question="どこまで再現できるか？",
        bridge_hint="制約条件へつなぐ",
        must_cover=["結果", "再現条件"],
        new_information="結果の整理",
    )

    prompt = build_note4000_section_prompt(
        section=section,
        speaker_profile="導入担当",
        audience_profile="実務担当者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私たち"],
        user_instruction="進め方と結果を整理する",
        instruction_anchor_terms=["結果", "再現条件"],
    )

    assert "結果や学びは『ことです』でまとめず" in prompt
    assert "なります・ことです・ください を上位の語尾にしない" in prompt


def test_case_study_condition_prompt_blocks_meta_closure_and_nested_headings() -> None:
    style = build_note4000_style_profile(
        article_type="case_study",
        focus="analysis",
        tone_profile="calm",
        style_profile="balanced",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="どの条件なら再現できるか",
            intent="condition",
            target_chars=420,
            topic_seed="再現条件",
            related_terms=["再現条件", "前提", "限界"],
            reader_question="どの条件なら再現できるか？",
            bridge_hint="成功談だけで閉じない",
            must_cover=["再現条件", "前提", "限界"],
            new_information="再現条件",
        ),
        speaker_profile="導入担当",
        audience_profile="実務担当者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私たち"],
        user_instruction="進め方と結果を整理する",
        instruction_anchor_terms=["再現条件", "前提", "限界"],
    )

    assert "向く条件、前提、限界の少なくとも2つを本文に含め" in prompt
    assert "新しい見出し（## / ###）や番号付き補足を追加しない" in prompt
    assert "『前段と重なる説明は省略』のようなメタ説明で締めない" in prompt


def test_branding_prompt_adds_composite_example_grounding_rule() -> None:
    style = build_note4000_style_profile(
        article_type="branding",
        focus="experience",
        tone_profile="warm",
        style_profile="balanced",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="現場で続けている工夫",
            intent="practice",
            target_chars=520,
            topic_seed="現場の工夫",
            related_terms=["運用", "導入初期"],
            reader_question="どこで差が出るか？",
            bridge_hint="次の判断へつなぐ",
            must_cover=["現場での摩擦を具体化する"],
            new_information="現場の工夫",
        ),
        speaker_profile="ブランド担当者",
        audience_profile="導入を検討する読者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私たち"],
        user_instruction="導入直後の迷いを減らす価値を伝える",
        instruction_anchor_terms=["導入初期", "現場の工夫"],
    )

    assert "事例の具体化:" in prompt
    assert "日本企業でありそうな匿名の合成事例" in prompt
    assert "sourceにない実在企業名" in prompt


def test_branding_prompt_adds_reference_realization_hint() -> None:
    style = build_note4000_style_profile(
        article_type="branding",
        focus="experience",
        tone_profile="warm",
        style_profile="balanced",
        base_register="polite",
    )
    section = DiscourseSectionPlan(
        heading="どんな事業を担っているか",
        intent="value",
        target_chars=520,
        topic_seed="事業内容",
        related_terms=["事業内容", "支援体制"],
        reader_question="何をしている会社か？",
        bridge_hint="次に支えている強みへつなぐ",
        must_cover=["支援体制"],
        new_information="事業内容",
    )
    setattr(section, "speaker_reference_policy", "tousha_preferred")
    setattr(section, "subject_reintroduction_policy", "section_shift_only")
    setattr(section, "proper_noun_repeat_cap", 1)

    prompt = build_note4000_section_prompt(
        section=section,
        speaker_profile="企業広報",
        audience_profile="導入を検討している読者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段で会社の輪郭を置いた",
        recent_summaries=["前段で会社の輪郭を置いた"],
        forbidden_topics=[],
        allowed_pronouns=["私たち", "当社"],
        user_instruction="現在の事業内容を先に伝える",
        instruction_anchor_terms=["事業内容", "支援体制"],
    )

    assert "参照表現:" in prompt
    assert "必要な場面だけ『当社』を使う" in prompt
    assert "主語は話題や対象が切り替わる場面だけ戻す" in prompt
    assert "固有名詞反復は同一節で1回まで" in prompt


def test_legal_like_prompt_adds_non_quoted_citation_rule() -> None:
    style = build_note4000_style_profile(
        article_type="explanatory_article",
        focus="analysis",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="景表法で見たいポイント",
            intent="problem",
            target_chars=520,
            topic_seed="景表法の留意点",
            related_terms=["条文", "表示"],
            reader_question="どこに注意すべきか？",
            bridge_hint="次の判断へつなぐ",
            must_cover=["景表法に関する留意点"],
            new_information="景表法の留意点",
        ),
        speaker_profile="実務担当者",
        audience_profile="実務担当者",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="前段の整理",
        recent_summaries=["前段の整理"],
        forbidden_topics=[],
        allowed_pronouns=["私たち"],
        user_instruction="法令や条文の話題は慎重に説明する",
        instruction_anchor_terms=["景表法", "条文"],
    )

    assert "法令引用:" in prompt
    assert "確認できない exact 引用は" in prompt
    assert "推測で第◯条や固有名を補わない" in prompt
    assert "正式名称や条文番号へ勝手に展開しない" in prompt


def test_announcement_section_prompt_includes_fact_role_line() -> None:
    style = build_note4000_style_profile(
        article_type="announcement",
        focus="explanation",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="今回の変更で押さえたいこと",
            intent="clarify",
            target_chars=420,
            topic_seed="対象者と開始時期",
            fact_slot="who_when",
            related_terms=["対象者", "開始時期"],
            reader_question="いつから・誰が対象か",
            bridge_hint="次に利用者への影響を確認する",
            must_cover=["2026年4月1日に開始", "対象は既存顧客"],
            new_information="対象者と開始時期",
        ),
        speaker_profile="広報担当",
        audience_profile="既存顧客",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="変更点を先に示した",
        recent_summaries=["変更点を先に示した"],
        forbidden_topics=[],
        allowed_pronouns=["当社"],
        user_instruction="提供開始日と対象を明確にした案内文にする",
        instruction_anchor_terms=["提供開始日", "対象者"],
    )

    assert "この節の役割補足:" in prompt
    assert "対象者と開始時期を混ぜずに示す" in prompt
    assert "『ご確認ください』『お手続きください』などの依頼文は action 節に寄せる" in prompt


def test_announcement_action_section_prompt_limits_request_line() -> None:
    style = build_note4000_style_profile(
        article_type="announcement",
        focus="explanation",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="次に取るべき行動",
            intent="closing",
            target_chars=420,
            topic_seed="公式情報の確認先",
            fact_slot="action",
            related_terms=["公式サイト", "手順"],
            reader_question="どこを見て何をするか",
            bridge_hint="締めとして行動を明確にする",
            must_cover=["公式サイトの専用ページを確認", "必要な手続きを進める"],
            new_information="公式情報の確認先",
        ),
        speaker_profile="広報担当",
        audience_profile="既存顧客",
        relationship_mode="guide",
        style_profile=style,
        previous_summary="確認事項までを整理した",
        recent_summaries=["変更点を示した", "確認事項までを整理した"],
        forbidden_topics=[],
        allowed_pronouns=["当社"],
        user_instruction="確認先と必要な手順を簡潔に示す",
        instruction_anchor_terms=["公式サイト", "手順"],
    )

    assert "依頼文は末尾の1文までに抑える" in prompt
    assert "ください は最終の行動案内に寄せる" in prompt

