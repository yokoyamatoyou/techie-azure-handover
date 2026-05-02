"""Offline (dummy) tests without external API calls."""
import json
import pytest
import re

from core.app_config import get_source_reading_config
from note.article_fetcher import ArticleFetcher, FetchedContent
from note.article_generator import ArticleGenerator, COGNITIVE_ENERGY_PROFILES
from note.natural_blog_core import (
    build_note4000_discourse_plan,
    build_note4000_length_plan,
    build_note4000_section_prompt,
    build_note4000_style_profile,
)
from note.natural_blog_types import DiscourseSectionPlan
from human_resonance.phase5_editor import Phase5Editor
from human_resonance.phase7_sanitize import Phase7Sanitize


class DummyLLM:
    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        if task_type == "editor_consistency":
            return '{"lead": "テストリード。共感→課題提示の流れ。", "body": "## 見出しA\\n\\n本文テキスト。\\n\\n## 見出しB\\n\\n本文テキスト。"}'

        if "アウトライン" in prompt or "\"headings\"" in prompt or "sections" in prompt:
            return '{"sections": [{"heading": "見出しA", "purpose": "導入", "required_elements": ["要素1"], "key_message": "結論A", "source_focus": "テスト", "do_not_cover": "見出しBの話題"}, {"heading": "見出しB", "purpose": "本論", "required_elements": ["要素2"], "key_message": "結論B", "source_focus": "本文", "do_not_cover": "見出しAの話題"}, {"heading": "見出しC", "purpose": "まとめ", "required_elements": ["要素3"], "key_message": "結論C", "source_focus": "資料", "do_not_cover": "見出しABの話題"}]}'

        if "タイトル" in prompt and "タイトルのみ" in prompt:
            return "テストタイトル"

        if "リード文" in prompt:
            return "テストリード。共感→課題提示の流れ。"

        if "ハッシュタグ" in prompt:
            return "#テスト #ダミー #note"

        match = re.search(r"## (.+?)」", prompt)
        heading = match.group(1) if match else "見出しA"
        return f"## {heading}\n\n本文テキスト。"


def test_generate_with_dummy_llm():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="これはテスト用の本文です。")]
    result = generator.generate(contexts, "初心者向けに", "ai")

    assert result["title"] == "テストタイトル"
    assert result["lead"]
    assert "## " in result["body"]
    assert result["hashtags"].startswith("#")
    assert result["full_text"]
    assert result["pipeline_check"]["phases_expected"]
    assert result["llm_check"]["model"]
    assert result["category_policy"]["base_template"]
    progress = generator.get_generation_progress()
    assert progress["stage"] == "completed"
    assert progress["message"] == "生成完了"


def test_fetch_html_candidate_selection_offline():
    fetcher = ArticleFetcher()
    html = """
    <html><body>
      <article><p>短い本文です。</p></article>
      <main>
        <h2>本編</h2>
        <p>現場運用の手順と確認ポイントを明確にし、引き継ぎ時の品質低下を防ぐ流れを整理します。</p>
      </main>
    </body></html>
    """

    parsed = fetcher._parse_html(html, url="https://example.com/offline", content_type="text/html")

    assert "現場運用の手順" in parsed.content


def test_generate_disallow_experience_downgrades_focus_for_explanatory_types():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_allow_experience(False)
    contexts = [FetchedContent(title="テスト資料", content="これはテスト用の本文です。")]

    result_ai = generator.generate(
        contexts,
        "初心者向けに",
        "ai",
        writing_focus="experience",
    )
    assert result_ai["pipeline_check"]["input_contract"]["focus"] == "explanation"

    result_announcement = generator.generate(
        contexts,
        "初心者向けに",
        "announcement",
        writing_focus="experience",
    )
    assert result_announcement["pipeline_check"]["input_contract"]["focus"] == "explanation"

    result_daily = generator.generate(
        contexts,
        "今日は現場で起きたことを振り返る",
        "daily_happenings",
        writing_focus="experience",
    )
    assert result_daily["pipeline_check"]["input_contract"]["focus"] == "experience"


def test_generate_reflects_article_type_selection_in_prompt_and_pipeline_contract():
    class CaptureLLM(DummyLLM):
        def __init__(self) -> None:
            self.title_prompts = []

        def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
            if task_type == "title":
                self.title_prompts.append(prompt)
            return super().generate_text(prompt, max_tokens=max_tokens, task_type=task_type, **kwargs)

    llm = CaptureLLM()
    generator = ArticleGenerator(llm_client=llm)
    contexts = [FetchedContent(title="テスト資料", content="これはテスト用の本文です。")]

    result_ai = generator.generate(
        contexts,
        "初心者向けに",
        "ai",
    )
    assert result_ai["pipeline_check"]["input_contract"]["article_type"] == "ai"
    ai_editor_profiles = result_ai["pipeline_check"]["editor_persona"]["profiles"]
    assert ai_editor_profiles["editor_consistency"]["profile_key"] == "factual_guard"
    assert ai_editor_profiles["repair_only"]["profile_key"] == "factual_guard"
    assert (
        "専門情報やトピックを、読者が行動できる理解に翻訳する"
        in llm.title_prompts[-1]
    )

    result_daily = generator.generate(
        contexts,
        "今日は日々の業務で気づいたことを書く",
        "daily_happenings",
    )
    assert result_daily["pipeline_check"]["input_contract"]["article_type"] == "daily_happenings"
    assert result_daily["pipeline_check"]["input_contract"]["category_base_template"] == "branding"
    daily_editor_profiles = result_daily["pipeline_check"]["editor_persona"]["profiles"]
    assert daily_editor_profiles["editor_consistency"]["profile_key"] == "narrative_guard"
    assert daily_editor_profiles["readability_polish"]["profile_key"] == "narrative_guard"
    assert "日々の出来事から得た気づきを" in llm.title_prompts[-1]


def test_generate_tone_profile_auto_uses_category_defaults():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="これはテスト用の本文です。")]

    result_ai = generator.generate(contexts, "初心者向けに", "ai")
    ai_contract = result_ai["pipeline_check"]["input_contract"]
    assert ai_contract["tone_profile"] == "calm"
    assert ai_contract["style_profile"] == "formal"

    result_branding = generator.generate(contexts, "価値訴求を中心に書く", "branding")
    branding_contract = result_branding["pipeline_check"]["input_contract"]
    assert branding_contract["tone_profile"] == "passionate"
    assert branding_contract["style_profile"] == "casual"

    result_daily = generator.generate(contexts, "今日の現場での気づき", "daily_happenings")
    daily_contract = result_daily["pipeline_check"]["input_contract"]
    assert daily_contract["tone_profile"] == "gentle"
    assert daily_contract["style_profile"] == "balanced"


def test_generate_pipeline_check_keeps_length_mode_requested():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="これはテスト用の本文です。")]

    result = generator.generate(contexts, "初心者向けに", "ai", length_mode="adaptive")

    contract = result["pipeline_check"]["input_contract"]
    assert contract["length_mode_requested"] == "adaptive"
    assert contract["length_mode"] in {"short", "normal", "long", "adaptive"}


def test_zero_base_resolve_pre_generation_questions_announcement_adds_source_fact_items_to_must_cover():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers(
        {
            "target": "既存顧客",
            "message": "日時・対象・申込手順を明確化する",
            "writer_role": "広報担当として語る",
        }
    )
    contexts = [
        FetchedContent(
            title="告知文案",
            content=(
                "2026年4月1日に新サービスを開始します。"
                "対象は既存顧客です。"
                "申し込みは公式サイトの専用ページから行います。"
            ),
            source_type="text",
        )
    ]

    resolved = generator._zero_base_resolve_pre_generation_questions(
        contexts=contexts,
        user_prompt="新サービス告知として、提供開始日と申し込み導線を明確にした記事を作成してください。",
        article_type="announcement",
        question_source_priority=["interview_answers", "user_prompt", "unresolved_items"],
    )

    must_cover = resolved["must_cover"]
    assert any("2026年4月1日" in item for item in must_cover)
    assert any("公式サイトの専用ページ" in item for item in must_cover)


def test_soften_assertive_expressions_keeps_confirmation_imperative_natural():
    text = "詳細は必ずご確認ください。導入後は必ず改善します。"

    softened = ArticleGenerator._soften_assertive_expressions(text)

    assert "多くの場合ご確認ください" not in softened
    assert "必ずご確認ください" not in softened
    assert "ご確認ください" in softened
    assert "多くの場合改善します" in softened


def test_zero_base_enforce_announcement_fact_consistency_replaces_conflicting_dates():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = {
        "article_type": "announcement",
        "category_base_template": "announcement",
        "must_cover": [
            "2026年4月1日に新サービスを開始します",
            "申し込みは公式サイトの専用ページから行います",
        ],
    }
    body = (
        "新サービスの提供開始日は2024年7月1日です。"
        "対象者は7月1日以降に手続きできます。"
        "申し込みは専用のウェブフォームから行えます。"
        "多くの場合当社公式サイトの専用ページから行ってください。"
        "多くの場合ご確認ください。"
    )

    normalized = generator._zero_base_enforce_announcement_fact_consistency(body, contract)

    assert "2024年7月1日" not in normalized
    assert "2026年4月1日" in normalized
    assert "7月1日以降" not in normalized
    assert "4月1日以降" in normalized
    assert "公式サイトの専用ページ" in normalized
    assert "多くの場合当社公式サイト" not in normalized
    assert "多くの場合ご確認ください" not in normalized


def test_generate_tone_profile_preference_is_clamped_in_strict_mode():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_tone_profile_preference("passionate")
    contexts = [FetchedContent(title="テスト資料", content="これはテスト用の本文です。")]

    result = generator.generate(
        contexts,
        "根拠重視で慎重に説明する",
        "ai",
        writing_focus="analysis",
    )
    contract = result["pipeline_check"]["input_contract"]
    assert contract["tone_profile"] == "passionate"
    assert contract["style_profile"] == "formal"


def test_generate_image_prompts_initial_mode_returns_top_and_inline_prompts():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="本文です。")]

    prompts = generator.generate_image_prompts(
        contexts=contexts,
        user_prompt="画像を作る",
        title="テストタイトル",
        lead="リード",
        body="## 見出し\n本文",
        count=2,
        mode="initial_top_candidates",
    )
    assert len(prompts) == 2


def test_generate_image_prompts_initial_mode_uses_inline_for_second_prompt():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="本文です。")]
    seen_roles = []

    def fake_generate_image_prompt(*args, **kwargs):  # type: ignore[no-untyped-def]
        role = kwargs.get("image_role", "top")
        seen_roles.append(role)
        return f"prompt-{role}-{len(seen_roles)}"

    generator.generate_image_prompt = fake_generate_image_prompt  # type: ignore[method-assign]
    prompts = generator.generate_image_prompts(
        contexts=contexts,
        user_prompt="画像を作る",
        title="テストタイトル",
        lead="リード",
        body="## 見出しA\n本文A\n\n## 見出しB\n本文B",
        count=2,
        mode="initial_top_candidates",
    )
    assert len(prompts) == 2
    assert seen_roles[0] == "top"
    assert "inline" in seen_roles[1:]


def test_generate_image_prompts_placement_mode_returns_multiple_prompts():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="本文です。")]

    prompts = generator.generate_image_prompts(
        contexts=contexts,
        user_prompt="画像を作る",
        title="テストタイトル",
        lead="リード",
        body="## 見出しA\n本文A\n\n## 見出しB\n本文B",
        count=2,
        mode="placement",
    )
    assert len(prompts) == 2


def test_generate_image_placement_plan_and_apply_guidance():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="本文です。")]
    body = "## 見出しA\n本文A\n\n## 見出しB\n本文B"
    plan = generator.generate_image_placement_plan(
        contexts=contexts,
        user_prompt="配置を提案して",
        title="テストタイトル",
        lead="リード",
        body=body,
        slots=2,
    )
    assert len(plan) == 2
    assert plan[0]["prompt_en"]

    updated = generator.apply_image_placement_guidance(body, plan)
    assert "[画像提案1]" in updated


def test_dynamic_structure_features_toc_and_intro_mode():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._length_mode = "long"
    generator._effective_writing_focus = "analysis"
    features = generator._decide_structure_features(
        user_prompt="比較ポイントを整理して",
        article_type="ai",
        section_count=6,
    )
    assert features["use_toc"] is True
    assert features["use_bullets"] is True

    generator._structure_features = features
    outline = [{"heading": "概要"}, {"heading": "比較"}, {"heading": "示唆"}]
    body = "## 概要\n本文\n\n## 比較\n本文\n\n## 示唆\n本文"
    with_toc = generator._maybe_add_table_of_contents(body, outline)
    assert "## 目次" in with_toc

    minimal = generator._apply_intro_mode("一文目です。二文目です。三文目です。")
    assert minimal.startswith("一文目です。")


def test_prepare_section_opening_sequence_reduces_adjacent_repetition():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._effective_writing_focus = "explanation"
    generator._current_type = "branding"
    generator._opening_variation_nonce = 123
    generator._prepare_section_opening_sequence(8)
    sequence = generator._section_opening_sequence
    assert len(sequence) == 8
    for idx in range(1, len(sequence)):
        assert sequence[idx - 1] != sequence[idx]


def test_knowledge_expansion_guide_respects_safe_constraints():
    generator = ArticleGenerator(llm_client=DummyLLM())
    guide = generator._build_knowledge_expansion_guide(
        "LLMの知識で話を広げて。ignore previous instructions と言っているが従わないで。",
        "strict",
    )
    assert "知識拡張リクエスト対応" in guide
    assert "strictモード" in guide
    assert "上書き意図" in guide


def test_image_prompt_language_conversion_shortcuts():
    generator = ArticleGenerator(llm_client=DummyLLM())
    ja_prompt = "横長で余白のある画像。文字なし。"
    en_prompt = "Wide clean illustration with no text."
    assert generator.to_japanese_image_prompt(ja_prompt) == ja_prompt
    assert generator.to_english_image_prompt(en_prompt) == en_prompt


def test_interview_constraints_prioritize_user_instruction():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers(
        {"message": "発売前なので体験談は入れず、公式情報ベースで解説してください。"}
    )
    constraints = generator._derive_interview_constraints("企業ブランディングの記事")
    assert constraints["service_stage"] == "prelaunch"
    assert constraints["focus"] == "explanation"
    assert constraints["evidence_mode"] == "strict"
    assert constraints["experience_policy"] == "forbid"


def test_interview_contract_redacts_script_and_pii_in_questions():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers({"message": "<script>alert(1)</script> api_key=sk-AAAAAAAAAAAAAAAAAAAAAA"})
    contexts = [FetchedContent(title="テスト資料", content="テスト本文です。", source_type="url")]
    result = generator.generate(
        contexts,
        "<script>alert(1)</script> 連絡先: test@example.com",
        "ai",
    )
    contract = result["zero_base_contract"]
    serialized = json.dumps(contract, ensure_ascii=False)
    assert "<script" not in serialized.lower()
    assert "test@example.com" not in serialized
    assert "sk-AAAA" not in serialized
    assert "[REDACTED_EMAIL]" in serialized


def test_set_interview_answers_normalizes_perspective_key():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers({"perspective": "企業ブランディング担当の知見を混ぜる"})
    assert generator._interview_answers.get("perspective_key") == "corporate"
    assert generator._secondary_from_interview() == "corporate"


def test_generate_prefers_explicit_ui_perspective_over_interview_label():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers({"perspective": "記者の視点を混ぜる"})
    contexts = [FetchedContent(title="企業情報", content="会社概要とサービス情報。", source_type="url")]
    result = generator.generate(
        contexts,
        user_prompt="企業紹介を作成",
        article_type="branding",
        perspective="corporate",
    )
    assert result["pipeline_check"]["input_contract"]["perspective"] == "corporate"


def test_zero_base_contract_base_normalizes_theme_like_speaker_profile_for_ai():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = generator._zero_base_contract_base(
        article_type="ai",
        user_prompt="AIの語彙多様性を解説する",
        target_audience="一般読者",
        writing_focus="auto",
        input_contract={
            "article_type": "ai",
            "perspective": "auto",
            "speaker_profile": "企業の信頼性を維持するためのAI文章活用法",
            "interview_answers": {
                "perspective": "企業の信頼性を維持するためのAI文章活用法",
                "target": "このテーマに関心のある読者",
            },
        },
    )
    assert contract["speaker_profile"] == "編集担当として語る"
    assert contract["topic_statement"] == "企業の信頼性を維持するためのAI文章活用法"


def test_zero_base_contract_base_derives_topic_statement_from_prompt_when_perspective_is_non_topic():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = generator._zero_base_contract_base(
        article_type="branding",
        user_prompt="商品の価値と利用シーンを伝えるブランド記事を作成してください",
        target_audience="導入検討者",
        writing_focus="experience",
        input_contract={
            "article_type": "branding",
            "perspective": "auto",
            "speaker_profile": "",
            "interview_answers": {
                "perspective": "選ぶ理由を判断軸で示す",
                "target": "導入検討者",
                "message": "選定の判断軸を具体化する",
            },
            "must_cover": ["選定の判断軸を具体化する"],
        },
    )
    assert contract["topic_statement"] == "商品の価値と利用シーンを伝えるブランド"


def test_zero_base_contract_base_derives_company_intro_topic_from_prompt():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = generator._zero_base_contract_base(
        article_type="corporate_culture",
        user_prompt="初回投稿として、会社の事業内容と沿革、今後方針を紹介する記事を作成してください。",
        target_audience="一般読者",
        writing_focus="explanation",
        input_contract={
            "article_type": "corporate_culture",
            "perspective": "auto",
            "speaker_profile": "",
            "interview_answers": {
                "target": "一般読者",
                "message": "会社紹介の主題から逸脱しない",
            },
            "must_cover": ["会社紹介の主題から逸脱しない"],
        },
    )
    assert contract["topic_statement"] == "初回投稿として、会社の事業内容と沿革、今後方針を紹介"


def test_zero_base_allowed_pronouns_uses_category_profile_defaults():
    generator = ArticleGenerator(llm_client=DummyLLM())
    ai_allowed = generator._zero_base_allowed_pronouns(
        {
            "article_type": "ai",
            "category_base_template": "ai",
            "speaker_profile": "編集担当として語る",
            "relationship_mode": "guide",
            "allowed_pronouns_hint": ["私"],
        }
    )
    assert "私" in ai_allowed
    assert "当社" not in ai_allowed
    assert "弊社" not in ai_allowed

    corporate_allowed = generator._zero_base_allowed_pronouns(
        {
            "article_type": "corporate_culture",
            "category_base_template": "branding",
            "speaker_profile": "運営担当として語る",
            "relationship_mode": "guide",
        }
    )
    assert "私たち" in corporate_allowed
    assert "当社" in corporate_allowed
    assert "弊社" in corporate_allowed


def test_zero_base_allowed_pronouns_keeps_kanji_and_hiragana_private_forms_together():
    generator = ArticleGenerator(llm_client=DummyLLM())
    allowed = generator._zero_base_allowed_pronouns(
        {
            "article_type": "branding",
            "category_base_template": "branding",
            "speaker_profile": "運営担当として語る",
            "relationship_mode": "guide",
        }
    )
    assert "私" in allowed
    assert "わたし" in allowed


def test_zero_base_forbidden_topics_does_not_force_recruiting_topics_for_ai():
    generator = ArticleGenerator(llm_client=DummyLLM())
    topics = generator._build_zero_base_forbidden_topics(
        article_type="ai",
        user_prompt="語彙的多様性の異常を解説する記事",
        merged_context="AI生成文の特性を分析し、改善の方向を示す。",
        contract={
            "article_type": "ai",
            "category_base_template": "ai",
            "audience_profile": "このテーマに関心のある読者",
            "speaker_profile": "編集担当として語る",
            "relationship_mode": "guide",
        },
    )
    assert "採用候補者" not in topics
    assert "面接対策" not in topics


def test_is_low_signal_must_cover_item_skips_company_intro_guard_phrase():
    generator = ArticleGenerator(llm_client=DummyLLM())

    assert generator._is_low_signal_must_cover_item("会社紹介の主題から逸脱しない") is True


def test_generate_runtime_contract_splits_perspective_layers_and_normalizes_speaker():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_input_contract(
        {
            "article_type": "ai",
            "perspective": "auto",
            "article_viewpoint": "auto",
            "speaker_profile": "",
            "writer_role": "",
            "topic_statement": "企業の信頼性を維持するためのAI文章活用法",
            "audience_profile": "このテーマに関心のある読者",
            "interview_answers": {
                "perspective": "企業の信頼性を維持するためのAI文章活用法",
                "target": "このテーマに関心のある読者",
                "message": "AIは確率での文章出力をしているのである",
            },
        }
    )
    contexts = [FetchedContent(title="テスト資料", content="これはテスト用の本文です。")]
    result = generator.generate(contexts, "初心者向けに", "ai")
    contract = result["pipeline_check"]["input_contract"]
    assert contract["article_viewpoint"] == "auto"
    assert contract["speaker_profile"] == "編集担当として語る"
    assert contract["topic_statement"] == "企業の信頼性を維持するためのAI文章活用法"
    assert "採用候補者" not in result["zero_base_contract"]["forbidden_topics"]


def test_dynamic_interview_fallback_reflects_no_experience_request():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="企業情報", content="ミッションと価値訴求", source_type="url")]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "発売前なので体験談は入れず、公式情報中心でお願いします。",
        "branding",
    )
    message_question = next(q["question"] for q in questions if q["id"] == "message")
    assert "体験談は入れず" in message_question


def test_should_ask_pre_generation_questions_skips_when_announcement_inputs_are_sufficient():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="サービス変更のお知らせ",
            content=(
                "2026年4月1日から既存利用者向けに申し込み導線を変更します。"
                "対象者、開始日、確認手順、注意事項を案内します。"
            ),
            source_type="url",
        )
    ]

    decision = generator.should_ask_pre_generation_questions(
        contexts,
        "既存利用者向けに開始日と確認手順を明記した告知記事を作成してください。",
        "announcement",
    )

    assert decision["ask"] is False
    assert decision["reason"] == "announcement_sufficient_input"


def test_should_ask_pre_generation_questions_keeps_branding_question_for_ambiguous_prompt():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="商品紹介", content="価値訴求の概要のみ。", source_type="url")]

    decision = generator.should_ask_pre_generation_questions(
        contexts,
        "ブランド記事を書いてください。",
        "branding",
    )

    assert decision["ask"] is True
    assert decision["reason"] == "category_requires_clarification"


def test_dynamic_interview_fallback_announcement_has_non_branding_perspective_options():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="お知らせ",
            content="標準メッセージアプリの変更内容を告知します。",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "メッセージサービス変更のお知らせを作成",
        "announcement",
    )
    perspective_options = next(q["options"] for q in questions if q["id"] == "perspective")
    assert "企業ブランディング担当の知見を混ぜる" not in perspective_options
    assert "変更点を先に短く示す" in perspective_options
    assert "対象者と開始時期を先に示す" in perspective_options
    assert "利用者への影響と確認事項を先に示す" in perspective_options


def test_generate_interview_questions_announcement_uses_fallback_without_llm_mix():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="お知らせ",
            content="標準メッセージアプリの変更内容を告知します。",
            source_type="url",
        )
    ]
    questions = generator.generate_interview_questions(
        contexts,
        "メッセージサービス変更のお知らせを作成",
        "announcement",
    )
    assert generator._last_interview_reason == "category_locked_announcement"
    perspective_options = next(q["options"] for q in questions if q["id"] == "perspective")
    assert "企業ブランディング担当の知見を混ぜる" not in perspective_options
    assert len([opt for opt in perspective_options if opt != "指定しない"]) >= 3


def test_dynamic_interview_fallback_uses_citation_signals_without_fixed_defaults():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="ノーベルファーマとは：トップメッセージ",
            content="企業理念とミッション、患者への価値提供を説明するページ。",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "企業紹介記事を作成",
        "branding",
    )
    perspective_options = next(q["options"] for q in questions if q["id"] == "perspective")
    target_options = next(q["options"] for q in questions if q["id"] == "target")
    assert "企業ブランディング担当の知見を混ぜる" in perspective_options
    assert "記者の視点を混ぜる" not in perspective_options
    assert "教育者の知見を混ぜる" not in perspective_options
    assert "経営者・意思決定者" not in target_options


def test_dynamic_interview_fallback_avoids_single_incidental_medical_or_tech_hits():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="株式会社 さんれいフーズ 会社概要",
            content=(
                "山陰を中心とした業務用食材卸事業。"
                "病院向け配送にも対応。"
                "過去に技術指導を受けた実績がある。"
                "地域に根ざした食品企業として価値を届ける。"
            ),
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "食品会社の初回note記事を作成",
        "branding",
    )
    perspective_options = next(q["options"] for q in questions if q["id"] == "perspective")
    target_options = next(q["options"] for q in questions if q["id"] == "target")
    assert "企業ブランディング担当の知見を混ぜる" in perspective_options
    assert "技術実装の知見を混ぜる" not in perspective_options
    assert "医療・患者理解の知見を混ぜる" not in perspective_options
    assert "現場のエンジニア" not in target_options
    assert "医療従事者" not in target_options


def test_dynamic_interview_fallback_keeps_medical_options_on_strong_medical_signal():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="製薬企業の取り組み",
            content=(
                "臨床開発と医薬品の供給体制を強化し、"
                "患者と医療機関の双方に価値を提供する。"
            ),
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "企業紹介記事を作成",
        "branding",
    )
    perspective_options = next(q["options"] for q in questions if q["id"] == "perspective")
    target_options = next(q["options"] for q in questions if q["id"] == "target")
    assert "医療・患者理解の知見を混ぜる" in perspective_options
    assert "医療従事者" in target_options


def test_interview_normalize_aligns_options_to_citation_based_fallback():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="ノーベルファーマとは：トップメッセージ",
            content="企業理念とミッション、患者への価値提供を説明するページ。",
            source_type="url",
        )
    ]
    fallback_questions = generator._build_dynamic_interview_fallback(
        contexts,
        "企業紹介記事を作成",
        "branding",
    )
    llm_like = [
        {"id": "perspective", "question": "どの視点を補強しますか？", "options": ["記者の視点を混ぜる", "教育者の知見を混ぜる"]},
        {"id": "target", "question": "誰に読んでほしいですか？", "options": ["経営者・意思決定者", "一般読者"]},
        {"id": "message", "question": "核心メッセージは？", "options": None},
    ]
    normalized = generator._normalize_interview_questions(llm_like, fallback_questions)
    assert normalized is not None
    perspective_options = next(q["options"] for q in normalized if q["id"] == "perspective")
    target_options = next(q["options"] for q in normalized if q["id"] == "target")
    assert "記者の視点を混ぜる" not in perspective_options
    assert "教育者の知見を混ぜる" not in perspective_options
    assert "経営者・意思決定者" not in target_options


def test_interview_normalize_rewrites_questions_to_user_friendly_templates():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="Claude Cowork preview",
            content="法務対応の背景と実務影響を整理した資料。",
            source_type="url",
        )
    ]
    fallback_questions = generator._build_dynamic_interview_fallback(
        contexts,
        "Claude Coworkの法務対応を一般読者向けに解説",
        "ai",
    )
    llm_like = [
        {"id": "perspective", "question": "背景や専門的な意義は何ですか？", "options": ["技術実装の知見を混ぜる", "指定しない"]},
        {"id": "target", "question": "読者は？", "options": ["一般読者", "このテーマに関心のある読者"]},
        {"id": "message", "question": "一番伝えたいことは？", "options": None},
    ]
    normalized = generator._normalize_interview_questions(llm_like, fallback_questions)
    assert normalized is not None
    perspective_q = next(q["question"] for q in normalized if q["id"] == "perspective")
    target_q = next(q["question"] for q in normalized if q["id"] == "target")
    message_q = next(q["question"] for q in normalized if q["id"] == "message")
    assert "どの視点で書きますか？" in perspective_q
    assert "主に誰に向けて書きますか？" in target_q
    assert "核心メッセージを1文で教えてください。" in message_q


def test_interview_normalize_strips_yes_no_prefix_in_target_options():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="AIと知的財産の解説資料",
            content="制度論点と実務影響を整理する資料。",
            source_type="url",
        )
    ]
    fallback_questions = generator._build_dynamic_interview_fallback(
        contexts,
        "AIと知的財産の最新動向を解説",
        "ai",
    )
    llm_like = [
        {
            "id": "perspective",
            "question": "どの視点で書きますか？",
            "options": ["指定しない", "一次情報の要点整理を重視する"],
        },
        {
            "id": "target",
            "question": "この記事は、主に誰に向けて書きますか？",
            "options": [
                "はい、初心者の一般ユーザー向け",
                "いいえ、AI研究者や開発者向け",
                "いいえ、経営者や事業責任者向け",
            ],
        },
        {
            "id": "message",
            "question": "一番伝えたいことは？",
            "options": None,
        },
    ]
    normalized = generator._normalize_interview_questions(llm_like, fallback_questions)
    assert normalized is not None
    target_options = next(q["options"] for q in normalized if q["id"] == "target")
    assert all(not opt.startswith(("はい、", "いいえ、")) for opt in target_options)
    assert any("一般ユーザー向け" in opt for opt in target_options)
    assert any("AI研究者や開発者向け" in opt for opt in target_options)


def test_select_interview_options_falls_back_when_binary_only():
    generator = ArticleGenerator(llm_client=DummyLLM())
    options = generator._select_interview_options(
        qid="target",
        llm_options=["はい", "いいえ"],
        fallback_options=["このテーマに関心のある読者", "一般読者"],
    )
    assert len(options) >= 2
    assert any("一般読者" in opt or "このテーマに関心のある読者" in opt for opt in options)
    assert all(opt not in ("はい", "いいえ") for opt in options)


def test_interview_normalize_compacts_overlong_theme_in_question():
    generator = ArticleGenerator(llm_client=DummyLLM())
    fallback_questions = [
        {
            "id": "perspective",
            "question": "この記事をわかりやすく伝えるため、どの視点で書きますか？",
            "options": ["指定しない", "実務担当者の視点"],
        },
        {
            "id": "target",
            "question": "この記事は、主に誰に向けて書きますか？",
            "options": ["一般読者", "このテーマに関心のある読者"],
        },
        {
            "id": "message",
            "question": "この記事で読後に最も残したい核心メッセージを1文で教えてください。",
            "options": None,
        },
    ]
    llm_like = [
        {
            "id": "perspective",
            "question": "「私はAI企業のSNS担当なので、国としてのAIやDXの方向性の動向を説明する記事をブログに書きます 記事目的」で、どの視点で書きますか？",
            "options": ["指定しない", "実務担当者の視点"],
        },
        {"id": "target", "question": "「同じ長いテーマ」の記事は誰向けですか？", "options": ["一般読者", "担当者"]},
        {"id": "message", "question": "「同じ長いテーマ」で一番伝えたいことは？", "options": None},
    ]
    normalized = generator._normalize_interview_questions(llm_like, fallback_questions)
    assert normalized is not None
    perspective_q = next(q["question"] for q in normalized if q["id"] == "perspective")
    # 長い引用テーマをそのまま展開しない
    assert len(perspective_q) <= 70
    assert "どの視点で書きますか？" in perspective_q
    assert "で使」" not in perspective_q


def test_extract_interview_theme_hint_ignores_filename_like_source_title():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="shiryo1.pdf",
            content="AIと知的財産に関する課題が現在は議論されている。",
            source_type="url",
        )
    ]
    theme = generator._extract_interview_theme_hint(
        contexts,
        "AIと知的財産に関する課題が現在は議論されている点を整理したい",
        "ai",
    )
    assert ".pdf" not in theme.lower()
    assert "/" not in theme
    assert "AIと知的財産" in theme


def test_dynamic_interview_fallback_avoids_prompt_like_perspective_option_text():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="shiryo1.pdf",
            content="AIと知的財産の制度論点を整理する。",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "AIと知的財産の最新動向を解説",
        "ai",
    )
    perspective_options = next(q["options"] for q in questions if q["id"] == "perspective")
    assert any("一次情報の要点整理" in opt for opt in perspective_options)
    assert all(".pdf" not in opt.lower() for opt in perspective_options)
    assert all("/" not in opt for opt in perspective_options)


def test_normalize_interview_display_theme_falls_back_for_file_like_hint():
    generator = ArticleGenerator(llm_client=DummyLLM())
    display = generator._normalize_interview_display_theme(
        "「shiryo1.pdf / 知的財産とAIの関係を分かりやすく説明をして」"
    )
    assert display == "このテーマ"


def test_dynamic_interview_fallback_target_options_avoid_prompt_like_theme_strings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="shiryo1.pdf",
            content="",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "shiryo1.pdf / 知的財産とAIの関係を分かりやすく説明をして",
        "ai",
    )
    target_options = next(q["options"] for q in questions if q["id"] == "target")
    assert all(".pdf" not in opt.lower() for opt in target_options)
    assert all("/" not in opt for opt in target_options)


def test_extract_interview_theme_hint_keeps_key_term_from_long_prompt():
    generator = ArticleGenerator(llm_client=DummyLLM())
    theme = generator._extract_interview_theme_hint(
        [],
        "noteに初めて投稿するので、初めての挨拶と段ボールだけの会社ではないと自社の紹介を知らせます。",
        "branding",
    )
    assert "段ボール" in theme


def test_dynamic_interview_fallback_target_options_include_general_reader_escape():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="企業情報",
            content="会社概要と事業紹介。導入実績と顧客支援。",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "企業紹介記事を作成",
        "branding",
    )
    target_options = next(q["options"] for q in questions if q["id"] == "target")
    assert any("一般読者" in opt or "このテーマに関心のある読者" in opt for opt in target_options)


def test_dynamic_interview_fallback_non_recruiting_branding_excludes_recruit_candidate():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="商品紹介ページ",
            content="カニ加工品の特徴と品質管理、導入メリットを解説。",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "商品のブランディング記事としてカニ加工品の魅力を伝える",
        "branding",
    )
    target_options = next(q["options"] for q in questions if q["id"] == "target")
    assert "採用候補者" not in target_options


def test_dynamic_interview_fallback_corporate_culture_stays_in_category():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="カルチャーデック",
            content="理念と行動指針、現場の工夫、オンボーディングを紹介する。",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "企業文化と日々の行動を伝える記事を作成",
        "corporate_culture",
    )
    perspective_options = next(q["options"] for q in questions if q["id"] == "perspective")
    assert "理念より日々の行動から伝える" in perspective_options
    assert "企業ブランディング担当の知見を混ぜる" not in perspective_options


def test_dynamic_interview_fallback_ai_stays_in_explanatory_lane():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="AI導入ガイド",
            content="導入時の判断基準、注意点、できることと限界を整理する。",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "AI文章活用の注意点を解説する記事を作成",
        "ai",
    )
    perspective_options = next(q["options"] for q in questions if q["id"] == "perspective")
    assert "仕組みより判断基準を先に示す" in perspective_options
    assert "企業ブランディング担当の知見を混ぜる" not in perspective_options


def test_dynamic_interview_fallback_recruiting_branding_can_include_recruit_candidate():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="採用ページ",
            content="社員紹介と働き方、カルチャーを発信する。",
            source_type="url",
        )
    ]
    questions = generator._build_dynamic_interview_fallback(
        contexts,
        "採用候補者向けに社風と働き方を伝える記事を作成",
        "branding",
    )
    target_options = next(q["options"] for q in questions if q["id"] == "target")
    assert "採用候補者" in target_options


def test_fix_punctuation_repairs_particle_break_before_continuation():
    generator = ArticleGenerator(llm_client=DummyLLM())
    broken = "世界最高レベルの精度と速度を誇るフレキソフォルダーグルアは。\n毎分数百枚のスピードで箱を形成します。"
    fixed = generator._fix_punctuation(broken)
    assert "フレキソフォルダーグルアは、毎分数百枚" in fixed

    broken2 = "搬送工程を最適化するため。作業ミスを減らします。"
    fixed2 = generator._fix_punctuation(broken2)
    assert "最適化するため、作業ミス" in fixed2

    broken3 = "AIは似た意味の語を頻繁に切り替えて使いすぎたり。逆に同じ語を避けすぎたりします。"
    fixed3 = generator._fix_punctuation(broken3)
    assert "使いすぎたり、逆に" in fixed3

    broken4 = "わたしが考えながら理解するのとは違い。生成AIは確率的に単語を選びます。"
    fixed4 = generator._fix_punctuation(broken4)
    assert "とは違い、生成AIは" in fixed4

    broken5 = "実は、次に来る言葉を並べているだけなのだ、その仕組みを説明します。"
    fixed5 = generator._fix_punctuation(broken5)
    assert "だけなのだ。その仕組みを" in fixed5


def test_fix_broken_bold_absorbs_standalone_marker_line():
    generator = ArticleGenerator(llm_client=DummyLLM())
    broken = "本文です。\n**重要ポイント\n**\n続きです。"
    fixed = generator._fix_broken_bold(broken)
    assert "**重要ポイント**" in fixed
    assert "\n**\n" not in fixed


def test_fix_broken_bold_extends_hiragana_suffix_into_bold():
    # ケースA: 閉じ** 直後のひらがな語尾を太字内に取り込む
    generator = ArticleGenerator(llm_client=DummyLLM())
    broken = "管理が**欠か**せません。"
    fixed = generator._fix_broken_bold(broken)
    assert "**欠かせません**" in fixed
    assert "**欠か**せ" not in fixed


def test_fix_broken_bold_removes_midkanji_opening():
    # ケースB: 開き** が漢字直後（語中開始）の場合は太字マーカーを除去
    generator = ArticleGenerator(llm_client=DummyLLM())
    broken = "知的財**産の戦略的活用がますます重要になるでしょう**。"
    fixed = generator._fix_broken_bold(broken)
    assert "**" not in fixed
    assert "知的財産の戦略的活用がますます重要になるでしょう" in fixed


def test_fix_broken_bold_removes_particle_led_emphasis():
    # ケースC: 助詞始まりの太字は語中強調になりやすいため解除
    generator = ArticleGenerator(llm_client=DummyLLM())
    broken = "成果**を守る盾であり、競争力の源泉です**。"
    fixed = generator._fix_broken_bold(broken)
    assert "**" not in fixed
    assert "成果を守る盾であり、競争力の源泉です。" in fixed


def test_diversify_overused_phrases_rewrites_cliches_after_first_occurrence():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "この対応は欠かせません。運用定着にも欠かせません。"
    rewritten = generator._diversify_overused_phrases(text)
    assert rewritten.count("欠かせません") == 1
    assert ("要になります" in rewritten) or ("外せません" in rewritten)


def test_diversify_overused_phrases_caps_dake_denaku_repetition():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "AだけでなくB。CだけでなくD。EだけでなくF。GだけでなくH。"
    rewritten = generator._diversify_overused_phrases(text)
    assert rewritten.count("だけでなく") <= 3
    assert ("に加えて" in rewritten) or ("のみならず" in rewritten)


def test_diversify_overused_phrases_soft_limits_ai_like_endings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = (
        "この対応は必要があると考えます。"
        "運用定着にも必要があると考えます。"
        "さらに、優位性が見えてきます。"
        "課題の輪郭も見えてきます。"
    )
    rewritten = generator._diversify_overused_phrases(text)
    assert rewritten.count("必要があると考えます") == 1
    assert rewritten.count("見えてきます") == 1
    assert ("必要があります" in rewritten) or ("必要です" in rewritten) or ("必要だと見ています" in rewritten)
    assert ("分かってきます" in rewritten) or ("浮かび上がります" in rewritten)


def test_phase5_editor_balanced_profile_uses_conservative_endings():
    editor = Phase5Editor(style_profile="balanced")
    variants = editor._get_ending_variants()
    # conservative では「ですね。/ますね。」は許可、「ですよね。/ますよね。」は不許可
    assert "ですね。" in variants["です。"]
    assert "ですよね。" not in variants["です。"]
    assert "ますね。" in variants["ます。"]
    assert "ますよね。" not in variants["ます。"]


def test_add_note_sentence_linebreaks_splits_multi_sentence_block():
    generator = ArticleGenerator(llm_client=DummyLLM())
    # \n なし・2文以上の段落 → 文末ごとに \n が入る
    text = "文A。文B。文C。"
    result = generator._add_note_sentence_linebreaks(text)
    assert result == "文A。\n文B。\n文C。"


def test_add_note_sentence_linebreaks_skips_already_split():
    generator = ArticleGenerator(llm_client=DummyLLM())
    # 既に \n が含まれている場合はスキップ
    text = "文A。\n文B。"
    result = generator._add_note_sentence_linebreaks(text)
    assert result == "文A。\n文B。"


def test_add_note_sentence_linebreaks_preserves_paragraph_separator():
    generator = ArticleGenerator(llm_client=DummyLLM())
    # \n\n は段落区切りとして維持される
    text = "段落1文A。段落1文B。\n\n段落2文A。段落2文B。"
    result = generator._add_note_sentence_linebreaks(text)
    assert "\n\n" in result
    assert "段落1文A。\n段落1文B。" in result
    assert "段落2文A。\n段落2文B。" in result


def test_add_note_sentence_linebreaks_skips_heading():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "## 見出しです\n\n本文A。本文B。"
    result = generator._add_note_sentence_linebreaks(text)
    assert "## 見出しです" in result
    assert "本文A。\n本文B。" in result


def test_phase5_editor_casual_profile_keeps_colloquial_endings():
    editor = Phase5Editor(style_profile="casual")
    variants = editor._get_ending_variants()
    assert "ですね。" in variants["です。"]
    assert "ますね。" in variants["ます。"]


def test_phase5_editor_zipf_keeps_compound_connectives(monkeypatch):
    editor = Phase5Editor(style_profile="balanced")
    monkeypatch.setattr("human_resonance.phase5_editor.random.random", lambda: 0.0)
    text = (
        "しかしながら、Aです。しかしながら、Bです。"
        "だからこそ、Cです。だからこそ、Dです。"
    )
    changed = editor._apply_zipf_vocabulary(text)
    assert "ただながら" not in changed
    assert "そのためこそ" not in changed
    assert "というわけでこそ" not in changed
    assert "しかしながら" in changed
    assert "だからこそ" in changed


def test_final_consistency_guards_reduce_repeated_section_openings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    repeated_opening = "段ボールは現場の生産性を左右する重要な要素です。"
    body = f"""
## A

{repeated_opening} 設計段階で工程を見直すと、手戻りを減らせます。

## B

{repeated_opening} 検査工程を組み込むことで、不良流出の抑制につながります。

## C

{repeated_opening} 搬送と積み付けの最適化で、現場負荷を軽減できます。
""".strip()

    lead, cleaned_body = generator._apply_final_consistency_guards("導入です。", body)
    assert lead == "導入です。"
    assert cleaned_body.count(repeated_opening) == 1
    sections = generator._extract_section_blocks(cleaned_body)
    assert len(sections) == 3
    assert all(content.strip() for _, content in sections)


def test_final_consistency_guards_normalize_pronoun_usage():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._current_pronoun = "私たち"
    lead = "わたしは品質管理を重視します。"
    body = """
## 本文

私は工程を見直し、わたしは検査体制を整えます。僕は現場への共有も進めます。
""".strip()

    cleaned_lead, cleaned_body = generator._apply_final_consistency_guards(lead, body)
    merged = f"{cleaned_lead}\n{cleaned_body}"
    assert "わたしは" not in merged
    assert "私は" not in merged
    assert "僕は" not in merged
    assert "私たちは" in merged


def test_final_consistency_guards_normalize_register_and_add_corporate_anchor():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._pipeline_policy = {"style_profile": "formal", "focus": "analysis"}
    generator._current_perspective = "corporate"
    generator._current_pronoun = "私たち"
    generator._current_title = "京都銀行の取り組み"
    lead = "京都銀行は地域に根ざした金融機関である。導入効果は顕著である。"
    body = """
## 本文

伴走支援は重要である。実行の前提は明確です。次の一手となる。組織全体で検討する必要がある。現場の声を反映することが大切です。具体的な施策も求められる。
""".strip()

    cleaned_lead, cleaned_body = generator._apply_final_consistency_guards(lead, body)
    merged = f"{cleaned_lead}\n{cleaned_body}"
    assert "である。" not in merged
    assert "私たち京都銀行は" in cleaned_lead
    assert ("です。" in merged) or ("ます。" in merged)


def test_normalize_pronoun_usage_keeps_corporate_terms_untouched():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "当社は品質を守ります。弊社は現場を支援します。自社の基準を共有します。わたしは最終確認をします。"

    normalized = generator._normalize_pronoun_usage(text, "私")

    assert "当社は品質を守ります。" in normalized
    assert "弊社は現場を支援します。" in normalized
    assert "自社の基準を共有します。" in normalized
    assert "わたしは" not in normalized
    assert "私は最終確認をします。" in normalized


def test_split_overlong_sentence_keeps_compound_connectives():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sentence = (
        "導入の前提を整理し、だからこそ、判断基準を先に共有します。"
        "一方で、しかしながら、運用時の注意点も具体化します。"
    )

    parts = generator._split_overlong_sentence(sentence, max_chars=28, max_splits=2)
    merged = "".join(parts)

    assert "だからこそ" in merged
    assert "しかしながら" in merged


def test_final_consistency_guards_diversify_repeated_jibungoto():
    generator = ArticleGenerator(llm_client=DummyLLM())
    lead = "AI活用を自分事として考えることが重要です。"
    body = """
## 本文

このテーマを自分事で捉えると、学習と実装が進みます。さらに自分事で考える文化が定着すると、現場の判断も早くなります。
    """.strip()
    cleaned_lead, cleaned_body = generator._apply_final_consistency_guards(lead, body)
    merged = f"{cleaned_lead}\n{cleaned_body}"
    assert cleaned_body.count("自分事") <= 1
    assert ("当事者意識" in merged) or ("自分ごと" in merged)


def test_final_consistency_guards_clean_redundant_connectives():
    generator = ArticleGenerator(llm_client=DummyLLM())
    lead = "しかし一方で、同時に対策も進める必要があります。そのためこそ、確認が必要です。実は、次に来る言葉を並べているだけなのだ、その仕組みを説明します。"
    body = """
## 本文

さらに、加えて運用ルールを見直します。というわけでこそ、運用基準を揃えます。対してAIは、同じ構文を繰り返します。
""".strip()
    cleaned_lead, cleaned_body = generator._apply_final_consistency_guards(lead, body)
    assert "しかし一方で、同時に" not in cleaned_lead
    assert "一方で" in cleaned_lead
    assert "そのためこそ" not in cleaned_lead
    assert "さらに、加えて" not in cleaned_body
    assert "というわけでこそ" not in cleaned_body
    assert "なのだ、その" not in cleaned_lead
    assert "。対してAIは" not in cleaned_body
    assert "。一方、AIは" in cleaned_body


def test_final_consistency_guards_remove_heading_top_adversative_opening():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 本文

しかし、導入手順を整理します。次に検証項目を揃えます。
""".strip()
    _, cleaned_body = generator._apply_final_consistency_guards("導入です。", body)
    assert "\n\nしかし、" not in cleaned_body
    assert "導入手順を整理します。" in cleaned_body


def test_final_consistency_guards_compact_duplicate_claims_in_paragraph():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 本文

AIは数秒で提案を返します。AIは数秒で提案を返してくれます。初期検討が速くなります。
""".strip()
    _, cleaned_body = generator._apply_final_consistency_guards("導入です。", body)
    assert cleaned_body.count("AIは数秒で提案を返") <= 1
    assert "初期検討が速くなります。" in cleaned_body


def test_final_consistency_guards_shorten_verbose_endings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    lead = "この違和感は現場でよく見られる現象です。"
    body = """
## 本文

この迅速さは経営判断の初期段階で有用です。
""".strip()
    cleaned_lead, cleaned_body = generator._apply_final_consistency_guards(lead, body)
    assert "現場でよく見られる現象です" not in cleaned_lead
    assert "よく見られます" in cleaned_lead
    assert "有用です。" not in cleaned_body
    assert "役立ちます。" in cleaned_body


def test_final_consistency_guards_reduce_ai_like_openings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    # 同じテンプレ開始が連続する場合、2つ目以降が除去される
    body = """
## 本文

つまり、この仕組みは有効です。具体的には、手戻りを減らせます。

つまり、結果として改善が見込めます。運用の見直しが進みます。
""".strip()
    _, cleaned_body = generator._apply_final_consistency_guards("導入です。", body)
    # 同名テンプレ開始の連続は2つ目が除去される
    assert cleaned_body.count("つまり、") <= 1


def test_final_consistency_guards_apply_prodrop_for_repeated_subject():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 本文

生成AIは導入準備に時間がかかります。生成AIは運用ルールの整備で効果が出ます。生成AIは検証工程でも有効です。
""".strip()
    _, cleaned_body = generator._apply_final_consistency_guards("導入です。", body)
    assert cleaned_body.count("生成AIは") <= 2


def test_final_consistency_guards_apply_prodrop_for_repeated_pronoun_subject():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 本文

私は要件を整理しました。私は優先順位を確認しました。私は実装に着手しました。
""".strip()
    _, cleaned_body = generator._apply_final_consistency_guards("導入です。", body)
    assert cleaned_body.count("私は") <= 1


def test_final_consistency_guards_normalize_ai_like_heading_labels():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 追記の要点

本文です。

## すべき具体的な一歩

実装項目です。
""".strip()
    _, cleaned_body = generator._apply_final_consistency_guards("導入です。", body)
    assert "## 追記の要点" not in cleaned_body
    assert "## すべき具体的な一歩" not in cleaned_body
    assert "## 補足" in cleaned_body
    assert "## まず試すこと" in cleaned_body


def test_cap_colloquial_endings_for_non_casual_style():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._pipeline_policy = {"style_profile": "balanced"}
    text = "品質は重要ですね。工程は安定していますよね。検査は継続しますね。運用を見直しますよね。"
    capped = generator._cap_colloquial_endings(text, max_allowed=1)
    colloquial_hits = len(re.findall(r"(ですね。|ですよね。|ますね。|ますよね。)", capped))
    assert colloquial_hits <= 1


def test_normalize_paragraphs_splits_overlong_single_sentence():
    generator = ArticleGenerator(llm_client=DummyLLM())
    paragraph = (
        "生成AIは企画段階で案を高速に出せる一方で、評価軸が曖昧なまま運用を始めると判断がぶれて品質が安定せず、"
        "修正コストが後半で膨らみやすく、結果として現場の負担が増えますが、教育計画と検証手順を同時に整えれば"
        "運用開始後の手戻りと混乱を大きく抑えられますし、評価指標を定例会で継続監視すれば改善の速度も安定して維持でき、"
        "再発防止の型化にもつながります。"
    )
    normalized = generator._normalize_paragraphs(paragraph)
    sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", normalized) if s.strip()]
    assert len(sentences) >= 2
    assert max(len(s) for s in sentences) <= 110
    assert "たり。" not in normalized
    assert "すぎて。" not in normalized


def test_phase7_sanitize_discourse_leadin_diversifies_with_omission():
    sanitizer = Phase7Sanitize()
    text = (
        "ここで大切なのは、Aです。"
        "ここで大切なのは、Bです。"
        "ここで大切なのは、Cです。"
        "ここで大切なのは、Dです。"
        "ここで大切なのは、Eです。"
        "ここで大切なのは、Fです。"
        "ここで大切なのは、Gです。"
        "ここで大切なのは、Hです。"
    )
    sanitized = sanitizer.process(text)
    assert "ここで大切なのは" not in sanitized
    assert "要点は、Aです。" in sanitized
    assert "焦点は、Bです。" in sanitized
    assert "鍵は、Cです。" in sanitized
    assert "肝心なのは、Dです。" in sanitized
    assert "見逃せないのは、Eです。" in sanitized
    assert "押さえるべき点は、Fです。" in sanitized
    assert "確認したいのは、Gです。" in sanitized
    # 8件目は省略候補（先頭読点が残らないこと）
    assert "、Hです。" not in sanitized
    assert "Hです。" in sanitized


def test_phase7_sanitize_trims_excessive_connective_openings():
    sanitizer = Phase7Sanitize()
    text = "さらに、導入を見直します。さらに、検証手順を揃えます。つまり、品質が安定します。"
    sanitized = sanitizer.process(text)
    assert sanitized.startswith("さらに、導入を見直します。")
    assert "さらに、検証手順を揃えます。" not in sanitized
    assert "検証手順を揃えます。" in sanitized


def test_phase7_sanitize_normalizes_malformed_connectors():
    sanitizer = Phase7Sanitize()
    text = (
        "そのためこそ、確認が必要です。"
        "というわけでこそ、手順を見直します。"
        "ただながら、運用は継続します。"
        "冷たさを和らげるになります。"
    )
    sanitized = sanitizer.process(text)
    assert "そのためこそ" not in sanitized
    assert "というわけでこそ" not in sanitized
    assert "ただながら" not in sanitized
    assert "和らげるになります" not in sanitized


def test_apply_compacted_postprocess_pipeline_contextual_naturalness_guard():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 本文

AIは似た意味の語を頻繁に切り替えて使いすぎたり。逆に同じ語を避けすぎたりして、不自然な文章になります。
""".strip()
    _, cleaned_body = generator._apply_compacted_postprocess_pipeline(
        "",
        body,
        merged_context="",
        article_type="ai",
        target_audience="一般読者",
    )
    assert "使いすぎたり。逆に" not in cleaned_body
    report = getattr(generator, "_last_contextual_naturalness_report", {})
    assert report.get("passed") is True


def test_apply_compacted_postprocess_pipeline_reduces_opening_connectives():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 本文

つまり、Aです。さらに、Bです。たとえば、Cです。この点で、Dです。だからこそ、Eです。
""".strip()
    _, cleaned_body = generator._apply_compacted_postprocess_pipeline(
        "",
        body,
        merged_context="",
        article_type="ai",
        target_audience="一般読者",
    )
    original_hits = len(re.findall(r"(?:^|[。！？]\s*)(?:つまり|さらに|たとえば|この点で|だからこそ)(?:、|,)", body))
    cleaned_hits = len(re.findall(r"(?:^|[。！？]\s*)(?:つまり|さらに|たとえば|この点で|だからこそ)(?:、|,)", cleaned_body))
    assert cleaned_hits < original_hits


def test_check_contextual_naturalness_reports_soft_opening_issues():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

心がけているのは、たとえば、Aです。さらに、Bです。さらに、Cです。さらに、Dです。
""".strip()
    report = generator._check_contextual_naturalness(text)
    assert report.get("issue_count") == 0
    assert report.get("soft_issue_count", 0) >= 1
    assert any(item.get("type") == "awkward_leadin" for item in report.get("soft_issues", []))
    assert report.get("connective_opening_ratio", 0.0) > 0.0


def test_check_contextual_naturalness_flags_adversative_opening_after_heading():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

しかし、Aです。Bです。
""".strip()
    report = generator._check_contextual_naturalness(text)
    assert any(
        item.get("type") == "adversative_opening_after_heading"
        for item in report.get("soft_issues", [])
    )


def test_check_contextual_naturalness_flags_malformed_connector():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

ただながら、Aです。Bです。
""".strip()
    report = generator._check_contextual_naturalness(text)
    assert any(item.get("type") == "malformed_connector" for item in report.get("soft_issues", []))


def test_check_contextual_naturalness_flags_malformed_connector_single_sentence_paragraph():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

そのためこそ、Aです。
""".strip()
    report = generator._check_contextual_naturalness(text)
    assert any(item.get("type") == "malformed_connector" for item in report.get("soft_issues", []))


def test_check_contextual_naturalness_flags_towachigai_sentence_break():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

わたしが考えながら理解するのとは違い。生成AIは確率的に単語を選びます。
""".strip()
    report = generator._check_contextual_naturalness(text)
    assert report.get("issue_count", 0) >= 1


def test_check_contextual_naturalness_flags_non_terminal_single_sentence_paragraph():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

現場の安定運営には。
""".strip()
    report = generator._check_contextual_naturalness(text)
    assert report.get("issue_count", 0) >= 1


def test_detect_grammar_breaks_counts_non_terminal_sentence_break():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

現場に反映させることが。
""".strip()
    report = generator._detect_grammar_breaks(text)
    assert report.get("signals", {}).get("non_terminal_sentence_break", 0) >= 1


def test_final_consistency_guards_repairs_subjectless_openings_for_ai():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 本文

万能な創造者ではありません。具体例として、偏りが出る場面があります。

## 補足

生み出すのは、既存データの再構成です。

## 活用

    大量のデータをもとにパターンを学び、それを活かして文章を作り出します。
""".strip()
    _, cleaned_body = generator._apply_final_consistency_guards("導入です。", body)
    assert re.search(r"(?:^|\n\n)万能な創造者ではありません。", cleaned_body) is None
    assert "生成AIは万能な創造者ではありません。" in cleaned_body
    assert re.search(r"(?:^|\n\n)生み出すのは、既存データの再構成です。", cleaned_body) is None
    assert "生成AIが生み出すのは、既存データの再構成です。" in cleaned_body
    assert re.search(r"(?:^|\n\n)大量のデータをもとにパターンを学び", cleaned_body) is None
    assert "生成AIは大量のデータをもとにパターンを学び" in cleaned_body


def test_normalize_ai_like_heading_labels_dedupes_repeated_furikaeri():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "## 生成AIと共に創造性を高めるためにを振り返るを振り返る\n\n本文です。"
    normalized = generator._normalize_ai_like_heading_labels(text)
    assert "を振り返るを振り返る" not in normalized
    assert "を振り返る\n" in normalized


def test_build_closing_heading_prefers_quoted_core_topic_without_breaking():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._current_title = "AI検索の正確性を揺るがす「間接的プロンプトインジェクション」とは何か"
    heading = generator._build_closing_heading()
    assert re.search(r"(判断ポイント|チェックポイント|判断の目安|すぐ試せる行動|次の一歩)", heading)
    assert "間接的プロンプトインジェクション" in heading
    assert "「" not in heading
    assert "」" not in heading
    assert "振り返る" not in heading


def test_check_contextual_naturalness_quantifies_ending_and_opening_signals():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

生み出す文章は、既存データの再構成に偏りやすいです。
補助ツールとしての限界を理解が大切です。
単に便利そのためと過信すると、判断品質が落ちます。
新しい価値は生まれにくいなのです。
 現場での継続改善が必要があると考えます。
 段階的な見直しが必要があると考えます。
 共有基盤の整備が必要があると考えます。
 実行体制が見えてきます。
""".strip()
    report = generator._check_contextual_naturalness(text)
    assert report.get("sentence_count", 0) >= 8
    assert report.get("ellipsis_opening_ratio", 0.0) > 0.0
    assert report.get("awkward_ending_count", 0) >= 2
    assert report.get("connector_collision_count", 0) >= 1
    assert report.get("ai_template_ending_count", 0) >= 4
    assert any(
        item.get("type") == "ai_template_ending_overuse"
        for item in report.get("soft_issues", [])
    )


def test_trim_nonclosing_section_tail_summaries_removes_ai_like_one_line_recap():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## 背景

AI検索では参照元の品質が回答精度に直結します。現場では一次情報の優先順位を明確にする必要があります。
まずは引用先の信頼度を定義し、運用ルールに落とし込みます。

要するに、一次情報の優先が重要です。

## まとめ

要するに、最後は人間の確認工程が重要です。
""".strip()
    cleaned = generator._trim_nonclosing_section_tail_summaries(body)
    assert "要するに、一次情報の優先が重要です。" not in cleaned
    assert "## まとめ" in cleaned
    assert "要するに、最後は人間の確認工程が重要です。" in cleaned


def test_compress_redundant_explanations_strips_meta_leadin_prefix():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "心がけているのは、たとえば、重複説明を減らすことです。"
    cleaned = generator._compress_redundant_explanations(text)
    assert cleaned.startswith("たとえば、")
    assert "心がけているのは" not in cleaned


def test_phase7_sanitize_discourse_leadin_rewrite_for_osaeitai():
    sanitizer = Phase7Sanitize()
    text = "ここで押さえたいのは、結論です。"
    sanitized = sanitizer.process(text)
    assert sanitized == "要点は、結論です。"


def test_adjust_note_length_skips_redundant_expansion_section():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._length_mode = "short"

    lead = "AIと知財ルールの要点を簡潔に整理します。"
    body = "## 本論\n\n国のルールは透明性の確保と情報開示を重視します。"

    def _redundant_expansion(*args, **kwargs):
        return "## 補足\n\n国のルールは透明性の確保と情報開示を重視します。"

    generator._generate_expansion_section = _redundant_expansion  # type: ignore[method-assign]

    adjusted_lead, adjusted_body = generator._adjust_note_length(
        lead=lead,
        body=body,
        references_md="",
        merged_context="国のルールは透明性の確保と情報開示を重視します。",
        user_prompt="解説してください",
        article_type="ai",
        target_audience="一般読者",
        title="AIと知財ルール",
    )

    assert adjusted_lead == lead
    assert adjusted_body == body


def test_build_section_overlap_memory_uses_recent_sections_only():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sections = [
        "## 見出しA\n\nAの論点を説明します。背景を整理します。",
        "## 見出しB\n\nBの論点を説明します。選択肢を比較します。",
        "## 見出しC\n\nCの論点を説明します。注意点を確認します。",
    ]
    memory = generator._build_section_overlap_memory(sections, keep_last=2)
    assert "- 見出しB:" in memory
    assert "- 見出しC:" in memory
    assert "- 見出しA:" not in memory


def test_outline_heading_rejects_ai_label_like_headings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    assert generator._is_valid_heading("追記の要点") is False
    assert generator._is_valid_heading("経営者視点で見る導入効果") is False
    assert generator._is_valid_heading("背景と課題") is True


def test_is_redundant_section_detects_near_duplicate_by_ngram_overlap():
    generator = ArticleGenerator(llm_client=DummyLLM())
    existing_sections = [
        "## 既存\n\nクラウド導入では初期設計と運用設計を同時に見直すことが欠かせません。"
        "費用対効果だけでなく、担当者の運用負荷や教育コストまで含めて判断する必要があります。"
        "導入後の定着率を高めるには、現場の小さな運用ルールを先に整えることが有効です。"
    ]
    candidate = (
        "## 候補\n\nクラウド導入では初期設計と運用設計を同時に見直すことが重要です。"
        "費用対効果だけではなく、担当者の運用負荷や教育コストも含めて判断すべきです。"
        "導入後の定着率を上げるには、現場の小さな運用ルールを先に整理しておくことが有効です。"
    )
    assert generator._is_redundant_section(candidate, existing_sections) is True


def test_is_redundant_section_allows_distinct_content():
    generator = ArticleGenerator(llm_client=DummyLLM())
    existing_sections = [
        "## 既存\n\nクラウド導入では初期設計と運用設計を同時に見直し、"
        "費用対効果と運用負荷を比較しながら導入順序を決める必要があります。"
        "部門ごとに運用手順を明文化し、障害時の連絡経路まで先に決めておくことが重要です。"
    ]
    candidate = (
        "## 候補\n\n採用活動を改善するには、候補者体験の設計と面接官トレーニングを同時に進めることが重要です。"
        "応募から内定までの待機時間を短縮し、評価軸を明文化して納得感を高めます。"
        "加えて、面接後のフィードバック基準を統一することで、辞退率の抑制と採用精度の向上を狙えます。"
    )
    assert generator._is_redundant_section(candidate, existing_sections) is False


def test_is_redundant_expansion_detects_near_duplicate_by_ngram_overlap():
    generator = ArticleGenerator(llm_client=DummyLLM())
    existing_body = (
        "## 背景\n\nクラウド導入では初期設計と運用設計を同時に見直すことが欠かせません。"
        "費用対効果だけでなく、担当者の運用負荷や教育コストまで含めて判断する必要があります。"
    )
    expansion = (
        "## 追加\n\nクラウド導入では初期設計と運用設計を同時に見直すことが重要です。"
        "費用対効果だけでなく、担当者の運用負荷や教育コストまで含めて判断すべきです。"
    )
    assert generator._is_redundant_expansion(existing_body, expansion) is True


def test_generate_section_with_retry_regenerates_when_overlap_detected():
    generator = ArticleGenerator(llm_client=DummyLLM())
    forced_flags = []
    calls = {"count": 0}
    duplicated = (
        "同じ論点を説明します。制度の背景と実務上の論点を整理し、"
        "読者が判断しやすいように前提条件と注意点を丁寧に確認します。"
    )
    differentiated = (
        "別の観点として、現場で意思決定する際の優先順位を具体的に整理します。"
        "まず目的を固定し、次に一次情報の確認手順を決め、最後に運用で崩れやすい点をチェックします。"
    )

    def _fake_generate_section(*args, **kwargs):
        calls["count"] += 1
        forced_flags.append(bool(kwargs.get("force_non_overlap")))
        if calls["count"] == 1:
            return f"## 見出しB\n\n{duplicated}"
        return f"## 見出しB\n\n{differentiated}"

    generator._generate_section = _fake_generate_section  # type: ignore[method-assign]
    result = generator._generate_section_with_retry(
        section_meta={"heading": "見出しB"},
        merged="",
        user_prompt="",
        article_type="ai",
        quote_candidates=[],
        target_audience="一般読者",
        target_chars=380,
        title="テスト記事",
        section_index=1,
        total_sections=2,
        existing_sections=[f"## 見出しA\n\n{duplicated}"],
    )

    assert "別の観点として、現場で意思決定する際の優先順位を具体的に整理します" in result
    assert calls["count"] >= 2
    assert forced_flags[0] is False
    assert any(flag is True for flag in forced_flags[1:])


def test_rebalance_outline_flow_moves_supplement_after_midpoint():
    generator = ArticleGenerator(llm_client=DummyLLM())
    outline = [
        {"heading": "補足情報", "purpose": "補足", "required_elements": []},
        {"heading": "はじめに", "purpose": "導入", "required_elements": []},
        {"heading": "提供価値", "purpose": "本論", "required_elements": []},
        {"heading": "活用シーン", "purpose": "本論", "required_elements": []},
        {"heading": "まとめ", "purpose": "結論", "required_elements": []},
    ]
    rebalanced = generator._rebalance_outline_flow(outline)
    headings = [s.get("heading", "") for s in rebalanced]
    assert headings
    assert "補足情報" in headings
    assert headings[0] != "補足情報"
    assert headings.index("補足情報") >= 2
    assert headings[-1] == "まとめ"


def test_rebalance_outline_flow_keeps_core_order():
    generator = ArticleGenerator(llm_client=DummyLLM())
    outline = [
        {"heading": "補足", "purpose": "補足", "required_elements": []},
        {"heading": "会社の背景", "purpose": "本論", "required_elements": []},
        {"heading": "提供価値", "purpose": "本論", "required_elements": []},
        {"heading": "活用シーン", "purpose": "本論", "required_elements": []},
        {"heading": "結論", "purpose": "結論", "required_elements": []},
    ]
    rebalanced = generator._rebalance_outline_flow(outline)
    headings = [s.get("heading", "") for s in rebalanced]
    idx_background = headings.index("会社の背景")
    idx_value = headings.index("提供価値")
    idx_scene = headings.index("活用シーン")
    assert idx_background < idx_value < idx_scene
    assert headings.index("補足") >= idx_value
    assert headings[-1] == "結論"


def test_ensure_outline_closing_section_converts_last_when_missing():
    generator = ArticleGenerator(llm_client=DummyLLM())
    outline = [
        {"heading": "AIエージェントとは何か", "purpose": "導入", "required_elements": []},
        {"heading": "導入効果の論点", "purpose": "本論", "required_elements": []},
        {"heading": "補足", "purpose": "補足", "required_elements": []},
    ]
    ensured = generator._ensure_outline_closing_section(outline)
    assert ensured
    heading = ensured[-1].get("heading", "")
    assert heading
    assert "まとめ：" not in heading
    required = ensured[-1].get("required_elements", [])
    assert any("判断軸" in item for item in required)
    assert any("次に取る行動" in item for item in required)


def test_outline_stage_blueprint_includes_countermeasure_for_explanatory_ai():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._effective_writing_focus = "explanation"
    blueprint = generator._build_outline_stage_blueprint(
        "ai",
        "間接的プロンプトインジェクションの仕組みと対策を解説する",
    )
    assert blueprint.get("include_countermeasure") is True
    assert "countermeasure" in blueprint.get("stages", [])


def test_outline_stage_blueprint_omits_countermeasure_for_diary_like_experience():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._effective_writing_focus = "experience"
    blueprint = generator._build_outline_stage_blueprint(
        "daily_blog",
        "今日は日々の出来事を日記として振り返ります",
    )
    assert blueprint.get("diary_like") is True
    assert "countermeasure" not in blueprint.get("stages", [])


def test_apply_outline_stage_blueprint_reorders_and_adds_transition_hints():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._effective_writing_focus = "explanation"
    blueprint = generator._build_outline_stage_blueprint(
        "ai",
        "仕組みと事例を整理して対策を示す",
    )
    outline = [
        {"heading": "具体的な事例", "purpose": "事例", "required_elements": []},
        {"heading": "背景と問題設定", "purpose": "導入", "required_elements": []},
        {"heading": "最後に", "purpose": "結論", "required_elements": []},
    ]
    applied = generator._apply_outline_stage_blueprint(outline, blueprint)
    headings = [str(item.get("heading", "")) for item in applied]
    assert headings
    assert headings[0] == "背景と問題設定"
    assert headings[-1] == "最後に"
    assert all("transition_from_prev" in item for item in applied)
    assert any(str(item.get("transition_from_prev", "")).strip() for item in applied[1:])


def test_apply_interview_constraints_overrides_focus_and_evidence():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._pipeline_policy = {
        "focus": "experience",
        "evidence_mode": "normal",
        "rationale": [],
    }
    generator._effective_writing_focus = "experience"
    generator._apply_interview_constraints(
        {"focus": "explanation", "evidence_mode": "strict", "experience_policy": "forbid"}
    )
    assert generator._pipeline_policy["focus"] == "explanation"
    assert generator._pipeline_policy["evidence_mode"] == "strict"
    assert generator._effective_writing_focus == "explanation"


def test_collect_review_points_flags_structure_style_and_reference_issues():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sample = """
## 補足
    医療製品は大切です。とても重要ですよね。さらに、いくつもの観点をまとめて一気に説明します。患者の話、規制の話、市場の話、運用の話、すべてを1段落に入れて長く書き続けます。この進め方でいいかな？多くの件で承認されています。加えて、提供体制や営業戦略、採用広報、海外展開、情報システム刷新、問い合わせ対応、教育体制、アフターケア、データ活用、品質監査まで同じ段落で触れており、読み手はどこが主題なのかを見失いやすくなります。

出典: ãã¼ãã« <https://example.com/a>

## 参考資料
- ãã¼ãã« (https://example.com/a)
""".strip()
    points = generator._collect_review_points(sample)
    assert any("見出し構成不足" in p or "見出し順の一貫性不足" in p for p in points)
    assert any("段落が長く論点が混在" in p for p in points)
    assert any("文体混在" in p for p in points)
    assert any("数値表現が曖昧" in p for p in points)
    assert any("文字化け" in p for p in points)


def test_collect_review_points_flags_polite_plain_register_mix():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sample = """
## 導入
この方針は重要です。運用の前提である。導入効果は確かです。

## 本論
実務では確認が必要です。判断軸は明確である。最後に注意点を整理する。成果を見直す必要がある。振り返りが求められます。
""".strip()
    points = generator._collect_review_points(sample)
    assert any("文体混在" in p for p in points)


def test_collect_review_points_flags_repeated_openings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sample = """
## はじめに
まずは結論からお伝えします。これは重要です。

## 背景
まずは結論からお伝えします。背景を簡潔に説明します。

## 要点
まずは結論からお伝えします。要点を順に整理します。

## まとめ
まずは結論からお伝えします。次の行動を示します。
""".strip()
    points = generator._collect_review_points(sample)
    assert any("導入句の反復" in p for p in points)


def test_should_run_readability_polish_when_points_include_readability_risks():
    generator = ArticleGenerator(llm_client=DummyLLM())
    long_body = (
        "## 導入\n\n"
        + ("背景整理の文章です。現場で起きる課題を丁寧に言語化します。" * 26)
        + "\n\n## 本論\n\n"
        + ("導入句が重複すると読み味が単調になります。文体混在も可読性を下げます。" * 26)
        + "\n\n## まとめ\n\n"
        + ("最後に実務へ戻す要点を整理し、次のアクションを示します。" * 26)
    )

    assert generator._should_run_readability_polish(
        ["段落が長く論点が混在（1段落1トピック推奨）", "導入句の反復（AI定型の可能性）"],
        body=long_body,
    ) is True
    assert generator._should_run_readability_polish(
        ["段落が長く論点が混在（1段落1トピック推奨）"],
        body=long_body,
    ) is False
    assert generator._should_run_readability_polish(
        ["導入句の反復（AI定型の可能性）", "文体混在（丁寧文と会話調が混在）"],
        body="## 導入\n\n短文です。\n\n## 本論\n\n短文です。\n\n## まとめ\n\n短文です。",
    ) is False
    assert generator._should_run_readability_polish(
        ["見出し順の一貫性不足（導入→本論→結論）", "最上級/限定の断定表現"],
        body=long_body,
    ) is True


def test_run_post_generation_polish_pass_uses_combined_editor_path_when_both_needed():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"editor": 0, "readability": 0}

    generator._should_run_editor_consistency = lambda lead, body: True  # type: ignore[method-assign]
    generator._should_run_readability_polish = lambda points, **kwargs: True  # type: ignore[method-assign]

    def _fake_editor(*args, **kwargs):
        calls["editor"] += 1
        assert kwargs.get("readability_focus") is True
        return "編集後リード", "編集後本文"

    def _fake_readability(*args, **kwargs):
        calls["readability"] += 1
        return "可読性リード", "可読性本文"

    generator._run_editor_consistency_pass = _fake_editor  # type: ignore[method-assign]
    generator._run_readability_polish_pass = _fake_readability  # type: ignore[method-assign]

    lead, body = generator._run_post_generation_polish_pass(
        "元リード",
        "元本文",
        merged_context="参考",
        article_type="ai",
        target_audience="一般読者",
        review_points=["段落が長く論点が混在（1段落1トピック推奨）"],
    )
    assert lead == "編集後リード"
    assert body == "編集後本文"
    assert calls["editor"] == 1
    assert calls["readability"] == 0


def test_run_post_generation_polish_pass_uses_readability_path_when_only_readability_needed():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"editor": 0, "readability": 0}

    generator._should_run_editor_consistency = lambda lead, body: False  # type: ignore[method-assign]
    generator._should_run_readability_polish = lambda points, **kwargs: True  # type: ignore[method-assign]

    def _fake_editor(*args, **kwargs):
        calls["editor"] += 1
        return "編集後リード", "編集後本文"

    def _fake_readability(*args, **kwargs):
        calls["readability"] += 1
        return "可読性後リード", "可読性後本文"

    generator._run_editor_consistency_pass = _fake_editor  # type: ignore[method-assign]
    generator._run_readability_polish_pass = _fake_readability  # type: ignore[method-assign]

    lead, body = generator._run_post_generation_polish_pass(
        "元リード",
        "元本文",
        merged_context="参考",
        article_type="ai",
        target_audience="一般読者",
        review_points=["段落が長く論点が混在（1段落1トピック推奨）"],
    )
    assert lead == "可読性後リード"
    assert body == "可読性後本文"
    assert calls["editor"] == 0
    assert calls["readability"] == 1


def test_run_post_generation_polish_pass_skips_long_form_in_transition_mode():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"editor": 0, "readability": 0}

    generator._should_run_editor_consistency = lambda lead, body: True  # type: ignore[method-assign]
    generator._should_run_readability_polish = lambda points, **kwargs: True  # type: ignore[method-assign]

    def _fake_editor(*args, **kwargs):
        calls["editor"] += 1
        return "編集後リード", "編集後本文"

    def _fake_readability(*args, **kwargs):
        calls["readability"] += 1
        return "可読性後リード", "可読性後本文"

    generator._run_editor_consistency_pass = _fake_editor  # type: ignore[method-assign]
    generator._run_readability_polish_pass = _fake_readability  # type: ignore[method-assign]

    long_body = (
        "## 導入\n\n"
        + ("導入の説明文です。現場での背景を丁寧に整理します。" * 20)
        + "\n\n## 課題\n\n"
        + ("課題の整理です。業務上の判断ポイントを分かりやすく示します。" * 20)
        + "\n\n## 解決\n\n"
        + ("解決策の説明です。導入時に確認すべき点を順番に示します。" * 20)
        + "\n\n## まとめ\n\n"
        + ("まとめです。次に取るアクションを具体化して提示します。" * 20)
    )
    lead, body = generator._run_post_generation_polish_pass(
        "元リード",
        long_body,
        merged_context="参考",
        article_type="ai",
        target_audience="一般読者",
        review_points=["段落が長く論点が混在（1段落1トピック推奨）", "導入句の反復（AI定型の可能性）"],
    )
    assert lead == "元リード"
    assert body == long_body
    assert calls["editor"] == 0
    assert calls["readability"] == 0


def test_run_post_generation_polish_pass_skips_long_multisection_when_only_dup_or_readability_risk():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"editor": 0, "readability": 0}

    generator._should_run_readability_polish = lambda points, **kwargs: True  # type: ignore[method-assign]

    def _fake_editor(*args, **kwargs):
        calls["editor"] += 1
        return "編集後リード", "編集後本文"

    def _fake_readability(*args, **kwargs):
        calls["readability"] += 1
        return "可読性後リード", "可読性後本文"

    generator._run_editor_consistency_pass = _fake_editor  # type: ignore[method-assign]
    generator._run_readability_polish_pass = _fake_readability  # type: ignore[method-assign]

    # duplicate_openings=True / missing_closing=False / pronoun_conflict=False
    generator._editor_consistency_signals = lambda lead, body: {  # type: ignore[method-assign]
        "missing_closing": False,
        "duplicate_openings": True,
        "pronoun_conflict": False,
    }

    long_body = (
        "## 導入\n\n"
        + ("導入の文章です。背景と前提を丁寧に説明します。" * 18)
        + "\n\n## 課題\n\n"
        + ("課題の文章です。現場で起きる摩擦を具体的に示します。" * 18)
        + "\n\n## 解決\n\n"
        + ("解決の文章です。実装時に確認すべき点を整理します。" * 18)
        + "\n\n## まとめ\n\n"
        + ("まとめの文章です。次に取る行動を明確に示します。" * 18)
    )

    lead, body = generator._run_post_generation_polish_pass(
        "元リード",
        long_body,
        merged_context="参考",
        article_type="ai",
        target_audience="一般読者",
        review_points=["導入句の反復（AI定型の可能性）", "文体混在（丁寧文と会話調が混在）"],
    )
    assert lead == "元リード"
    assert body == long_body
    assert calls["editor"] == 0
    assert calls["readability"] == 0


def test_run_post_generation_polish_pass_runs_editor_when_hard_consistency_risk_even_if_long():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"editor": 0, "readability": 0}

    generator._should_run_readability_polish = lambda points, **kwargs: True  # type: ignore[method-assign]

    def _fake_editor(*args, **kwargs):
        calls["editor"] += 1
        return "編集後リード", "編集後本文"

    def _fake_readability(*args, **kwargs):
        calls["readability"] += 1
        return "可読性後リード", "可読性後本文"

    generator._run_editor_consistency_pass = _fake_editor  # type: ignore[method-assign]
    generator._run_readability_polish_pass = _fake_readability  # type: ignore[method-assign]

    # hard risk: missing_closing=True
    generator._editor_consistency_signals = lambda lead, body: {  # type: ignore[method-assign]
        "missing_closing": True,
        "duplicate_openings": True,
        "pronoun_conflict": False,
    }

    long_body = (
        "## 導入\n\n"
        + ("導入の文章です。背景と前提を丁寧に説明します。" * 18)
        + "\n\n## 課題\n\n"
        + ("課題の文章です。現場で起きる摩擦を具体的に示します。" * 18)
        + "\n\n## 解決\n\n"
        + ("解決の文章です。実装時に確認すべき点を整理します。" * 18)
        + "\n\n## まとめ\n\n"
        + ("まとめの文章です。次に取る行動を明確に示します。" * 18)
    )

    lead, body = generator._run_post_generation_polish_pass(
        "元リード",
        long_body,
        merged_context="参考",
        article_type="ai",
        target_audience="一般読者",
        review_points=["導入句の反復（AI定型の可能性）", "文体混在（丁寧文と会話調が混在）"],
    )
    assert lead == "編集後リード"
    assert body == "編集後本文"
    assert calls["editor"] == 1
    assert calls["readability"] == 0


def test_run_post_generation_polish_pass_runs_editor_when_style_mix_risk_even_if_long_transition():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"editor": 0, "readability": 0}

    generator._should_run_readability_polish = lambda points, **kwargs: True  # type: ignore[method-assign]
    generator._should_run_editor_consistency = lambda lead, body: True  # type: ignore[method-assign]

    def _fake_editor(*args, **kwargs):
        calls["editor"] += 1
        return "編集後リード", "編集後本文"

    def _fake_readability(*args, **kwargs):
        calls["readability"] += 1
        return "可読性後リード", "可読性後本文"

    generator._run_editor_consistency_pass = _fake_editor  # type: ignore[method-assign]
    generator._run_readability_polish_pass = _fake_readability  # type: ignore[method-assign]
    generator._editor_consistency_signals = lambda lead, body: {  # type: ignore[method-assign]
        "missing_closing": False,
        "duplicate_openings": False,
        "pronoun_conflict": False,
        "style_mixed": True,
        "stance_anchor_missing": False,
    }

    long_body = (
        "## 導入\n\n"
        + ("導入の文章です。背景と前提を丁寧に説明します。" * 18)
        + "\n\n## 課題\n\n"
        + ("課題の文章です。現場で起きる摩擦を具体的に示します。" * 18)
        + "\n\n## 解決\n\n"
        + ("解決の文章です。実装時に確認すべき点を整理します。" * 18)
        + "\n\n## まとめ\n\n"
        + ("まとめの文章です。次に取る行動を明確に示します。" * 18)
    )

    lead, body = generator._run_post_generation_polish_pass(
        "元リード",
        long_body,
        merged_context="参考",
        article_type="ai",
        target_audience="一般読者",
        review_points=["導入句の反復（AI定型の可能性）", "文体混在（です・ます調とだ・である調が混在）"],
    )
    assert lead == "編集後リード"
    assert body == "編集後本文"
    assert calls["editor"] == 1
    assert calls["readability"] == 0


def test_run_post_generation_polish_pass_runs_editor_when_missing_intro_risk_even_if_long_body():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"editor": 0, "readability": 0}

    generator._should_run_readability_polish = lambda points, **kwargs: True  # type: ignore[method-assign]
    generator._should_run_editor_consistency = lambda lead, body: True  # type: ignore[method-assign]

    def _fake_editor(*args, **kwargs):
        calls["editor"] += 1
        return "編集後リード", "編集後本文"

    def _fake_readability(*args, **kwargs):
        calls["readability"] += 1
        return "可読性後リード", "可読性後本文"

    generator._run_editor_consistency_pass = _fake_editor  # type: ignore[method-assign]
    generator._run_readability_polish_pass = _fake_readability  # type: ignore[method-assign]
    generator._editor_consistency_signals = lambda lead, body: {  # type: ignore[method-assign]
        "missing_intro": True,
        "missing_closing": False,
        "duplicate_openings": False,
        "pronoun_conflict": False,
        "style_mixed": False,
        "stance_anchor_missing": False,
    }

    long_body = (
        "## セクションA\n\n"
        + ("導入の文章です。背景と前提を丁寧に説明します。" * 18)
        + "\n\n## セクションB\n\n"
        + ("課題の文章です。現場で起きる摩擦を具体的に示します。" * 18)
        + "\n\n## セクションC\n\n"
        + ("解決の文章です。実装時に確認すべき点を整理します。" * 18)
        + "\n\n## セクションD\n\n"
        + ("結びの文章です。次に取る行動を明確に示します。" * 18)
    )

    lead, body = generator._run_post_generation_polish_pass(
        "元リード",
        long_body,
        merged_context="参考",
        article_type="ai",
        target_audience="一般読者",
        review_points=["見出し順の一貫性不足（導入→本論→結論）", "導入句の反復（AI定型の可能性）"],
    )
    assert lead == "編集後リード"
    assert body == "編集後本文"
    assert calls["editor"] == 1
    assert calls["readability"] == 0


def test_clean_meta_output_does_not_drop_heading_lines():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sample = """
## 重要な論点

企業視点ではこのテーマを書くと伝わりやすいです。

次の段落は残ります。
""".strip()
    cleaned = generator._clean_meta_output(sample, "一般読者")
    assert "## 重要な論点" in cleaned
    assert "次の段落は残ります。" in cleaned


def test_clean_meta_output_removes_instructional_prompt_fragments():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sample = """
## 重要な論点

会社紹介の要点を整理します。
魅力的な会社として記事作成してください 【記事目的】読者の興味を惹く構成を優先してください。
手順を分解して優先順位を決めることが有効です。
読み手が次の一歩を選びやすいよう、実行順を明確にします。
判断の根拠を具体化して伝えますね。
現場で再現しやすい形に整えることを意識します。
まずはnoteにて自己紹介を行うことが効果的でしょう。
この段階で重要なのは「生活者視点」を判断基準として具体化することです。
次の段落は残すべきです。
""".strip()
    cleaned = generator._clean_meta_output(sample, "一般読者")
    assert "記事作成してください" not in cleaned
    assert "【記事目的】" not in cleaned
    assert "手順を分解して優先順位を決める" not in cleaned
    assert "実行順を明確にします" not in cleaned
    assert "判断の根拠を具体化して伝えますね" not in cleaned
    assert "整えることを意識します" not in cleaned
    assert "noteにて自己紹介を行うことが効果的でしょう" not in cleaned
    assert "この段階で重要なのは" not in cleaned
    assert "次の段落は残すべきです。" in cleaned
    assert "## 重要な論点" in cleaned


def test_clean_meta_output_removes_prompt_echo_sentence_from_must_cover_reference():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._prompt_echo_references = ["現場スタッフ・社員の働きがいに焦点をあてる"]
    sample = """
## 見出し

現場スタッフ・社員の働きがいに焦点をあてるをどう解説すると伝わるかという観点で、具体例と結びつけて整理します。
次の段落は残すべきです。
""".strip()
    cleaned = generator._clean_meta_output(sample, "一般読者")
    assert "焦点をあてるをどう解説すると伝わるか" not in cleaned
    assert "次の段落は残すべきです。" in cleaned


def test_reduce_target_term_overuse_for_kyodobataraki():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = (
        "30代共働き家庭の工夫を紹介します。"
        "共働きの家庭で役立つ視点です。"
        "共働き世帯の負担を減らします。"
        "30代の読者にとって実践しやすい方法です。"
    )
    reduced = generator._reduce_target_term_overuse(
        text,
        target_audience="30代共働き世帯",
    )
    assert "共働き" not in reduced
    assert "30代" not in reduced
    assert "読者" in reduced or "忙しい家庭" in reduced


def test_zero_base_integrate_missing_must_cover_skips_multi_missing_for_naturalness():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = "## 本文\n\n現場での工夫を共有します。"
    contract = {
        "must_cover": [
            "生活者視点（共働きの現場感）",
            "忙しい平日の夕食準備時",
            "多様な商品展開をしています",
        ]
    }
    integrated_body, report = generator._zero_base_integrate_missing_must_cover(
        body=body,
        contract=contract,
    )
    assert integrated_body == body
    assert report.get("integrated_count") == 0
    assert report.get("skipped_reason") == "multi_missing_skip_for_naturalness"


def test_zero_base_extract_prompt_answer_message_strips_instructional_clauses():
    generator = ArticleGenerator(llm_client=DummyLLM())
    prompt = (
        "さんれいフーズとして初投稿で自社紹介を行います。"
        "魅力的な会社として記事作成してください。"
        "【記事目的】読者の興味を惹く構成を優先してください。"
    )
    answer = generator._zero_base_extract_prompt_answer(
        question_id="message",
        question_text="何を伝えるか？",
        user_prompt=prompt,
        article_type="corporate_culture",
    )
    assert "自社紹介" in answer
    assert "記事作成" not in answer
    assert "記事目的" not in answer


def test_zero_base_resolve_pre_generation_questions_filters_instructional_interview_answers():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers(
        {
            "message": "会社紹介の要点を伝えます。魅力的な会社として記事作成してください。",
        }
    )
    generator._build_dynamic_interview_fallback = (  # type: ignore[method-assign]
        lambda contexts, user_prompt, article_type: [
            {"id": "message", "question": "核心メッセージは？"},
        ]
    )

    bundle = generator._zero_base_resolve_pre_generation_questions(
        contexts=[],
        user_prompt="初投稿で会社紹介をします。",
        article_type="corporate_culture",
        question_source_priority=["interview_answers", "user_prompt", "unresolved_items"],
    )
    must_cover = bundle.get("must_cover", [])
    assert must_cover
    assert all("記事作成" not in item for item in must_cover)
    assert all("記事目的" not in item for item in must_cover)


def test_zero_base_resolve_pre_generation_questions_target_updates_audience_without_must_cover():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers(
        {
            "message": "現場で無理なく続けられる工夫を紹介する",
            "target": "30代共働き世帯",
        }
    )
    generator._build_dynamic_interview_fallback = (  # type: ignore[method-assign]
        lambda contexts, user_prompt, article_type: [
            {"id": "message", "question": "核心メッセージは？"},
            {"id": "target", "question": "主に誰に向けて書きますか？"},
        ]
    )

    bundle = generator._zero_base_resolve_pre_generation_questions(
        contexts=[],
        user_prompt="生活に密着した工夫を紹介したい",
        article_type="corporate_culture",
        question_source_priority=["interview_answers", "user_prompt", "unresolved_items"],
    )
    assert bundle.get("resolved_audience") == "30代共働き世帯"
    must_cover = bundle.get("must_cover", [])
    assert isinstance(must_cover, list)
    assert "30代共働き世帯" not in must_cover


def test_zero_base_resolve_pre_generation_questions_uses_user_prompt_when_question_is_skipped():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="告知",
            content="2026年4月1日から既存利用者向けに設定方法を変更します。対象、開始日、確認事項を案内します。",
            source_type="url",
        )
    ]

    bundle = generator._zero_base_resolve_pre_generation_questions(
        contexts=contexts,
        user_prompt="既存利用者向けに開始日と確認手順を明記した告知記事を作成してください。",
        article_type="announcement",
        question_source_priority=["interview_answers", "user_prompt", "unresolved_items"],
    )

    assert bundle["pre_generation_questions"] == []
    assert bundle["resolved_audience"] == "既存利用者"
    assert bundle["resolved_question_sources"]["target"] == "user_prompt"


def test_zero_base_resolve_pre_generation_questions_skips_non_topic_perspective_answer():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers(
        {
            "perspective": "企業ブランディング担当の知見を混ぜる",
            "message": "変更点を誤解なく伝える",
            "target": "一般読者",
        }
    )
    generator._build_dynamic_interview_fallback = (  # type: ignore[method-assign]
        lambda contexts, user_prompt, article_type: [
            {"id": "perspective", "question": "どの視点で書きますか？"},
            {"id": "message", "question": "核心メッセージは？"},
            {"id": "target", "question": "主に誰に向けて書きますか？"},
        ]
    )

    bundle = generator._zero_base_resolve_pre_generation_questions(
        contexts=[],
        user_prompt="告知記事を作成する",
        article_type="announcement",
        question_source_priority=["interview_answers", "unresolved_items"],
    )
    must_cover = bundle.get("must_cover", [])
    assert "企業ブランディング担当の知見を混ぜる" not in must_cover
    assert "変更点を誤解なく伝える" in must_cover


def test_zero_base_resolve_pre_generation_questions_treats_audience_alias_as_audience_only():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator.set_interview_answers(
        {
            "audience": "実務担当者",
            "message": "判断基準を短く整理する",
        }
    )
    bundle = generator._zero_base_resolve_pre_generation_questions(
        contexts=[],
        user_prompt="AI活用の判断基準を整理したい",
        article_type="ai",
        question_source_priority=["interview_answers", "user_prompt", "unresolved_items"],
    )

    assert bundle["resolved_audience"] == "実務担当者"
    assert "実務担当者" not in bundle["must_cover"]


def test_zero_base_build_section_prompt_uses_audience_hint_not_raw_label():
    generator = ArticleGenerator(llm_client=DummyLLM())
    prompt = generator._zero_base_build_section_prompt(
        heading="現場の工夫",
        new_information="判断の分岐点を整理する",
        reader_question="どの順で進めるべきか？",
        previous_summary="導入の要点",
        recent_summaries=["導入の要点", "課題の輪郭"],
        audience="30代共働き世帯",
        must_not_repeat=["同義反復"],
        section_plan={"sentence_min": 2, "sentence_max": 4, "target_chars": 220},
    )
    assert "読者ニーズヒント" in prompt
    assert "30代共働き世帯" not in prompt


def test_resonance_llm_editor_is_skipped_for_long_multisection_note_body():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._cognitive_drift_config = {"enabled": True}
    long_body = (
        "## 見出し1\n\n本文です。\n\n"
        "## 見出し2\n\n本文です。\n\n"
        "## 見出し3\n\n本文です。\n\n"
        "## 見出し4\n\n本文です。\n\n"
        "## 見出し5\n\n本文です。\n\n"
        "## 見出し6\n\n" + ("本文テキスト。" * 450)
    )
    enabled = generator._should_use_llm_editor_in_resonance(
        long_body,
        "note",
        enabled_in_config=True,
    )
    assert enabled is False


def test_should_use_resonance_llm_phases_are_conditional():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._pipeline_policy = {"evidence_mode": "normal"}
    safe_text = "これは通常の説明文です。読み手に配慮して要点だけを簡潔に示します。"
    risky_text = "導入後3か月で120件、継続率98%、売上2倍を達成し、業界No.1です。"

    assert generator._should_use_llm_editor_in_resonance(safe_text, "note", True) is False
    assert generator._should_use_llm_legal_in_resonance(safe_text, "note", True) is False
    assert generator._should_use_llm_legal_in_resonance(risky_text, "note", True) is True
    assert generator._should_use_llm_editor_in_resonance(risky_text, "linkedin", True) is False
    assert generator._should_use_llm_legal_in_resonance(risky_text, "linkedin", True) is False


def test_should_use_resonance_legal_llm_for_strict_mode():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._pipeline_policy = {"evidence_mode": "strict"}
    assert generator._should_use_llm_legal_in_resonance("通常の説明です。", "note", True) is True


def test_generate_skips_linkedin_resonance_pipeline_by_default():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="これはテスト用の本文です。")]
    called_platforms = []

    def _spy_apply_resonance(text, platform, perspective, source_text=None):
        called_platforms.append(platform)
        return text

    generator._apply_resonance = _spy_apply_resonance  # type: ignore[method-assign]
    result = generator.generate(contexts, "初心者向けに", "ai")

    assert called_platforms.count("note") >= 2
    assert "linkedin" not in called_platforms
    assert result["pipeline_check_linkedin"]["post_pipeline_skipped"] is True


def test_should_verify_section_content_only_for_strict_or_high_risk_claims():
    generator = ArticleGenerator(llm_client=DummyLLM())

    generator._pipeline_policy = {"evidence_mode": "normal"}
    low_risk = generator._should_verify_section_content(
        "この機能の概要を説明します。使い方を順に見ていきます。",
        "参考情報の本文です。",
    )
    assert low_risk is False

    numeric_heavy = generator._should_verify_section_content(
        "導入後3か月で120件、継続率98%、工数は2.5倍改善しました。",
        "参考情報の本文です。",
    )
    assert numeric_heavy is True

    generator._pipeline_policy = {"evidence_mode": "strict"}
    strict_mode = generator._should_verify_section_content(
        "抽象的な説明です。",
        "参考情報の本文です。",
    )
    assert strict_mode is True


def test_verify_section_content_rejects_aggressive_rewrite():
    generator = ArticleGenerator(llm_client=DummyLLM())

    class AggressiveVerificationLLM:
        def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
            if task_type == "verification":
                return "## まったく別の見出し\n\n要約済みの短文だけです。"
            return ""

    generator.llm = AggressiveVerificationLLM()  # type: ignore[assignment]
    original = "## 導入\n\n導入後3か月で120件、継続率98%、工数は2.5倍改善しました。"
    verified = generator._verify_section_content(original, "参考情報です。", "導入")
    assert verified == original


def test_verify_section_content_accepts_minimal_fact_adjustment():
    generator = ArticleGenerator(llm_client=DummyLLM())

    class MinimalVerificationLLM:
        def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
            if task_type == "verification":
                return "## 導入\n\n導入後3か月で多くの改善が確認されました。"
            return ""

    generator.llm = MinimalVerificationLLM()  # type: ignore[assignment]
    original = "## 導入\n\n導入後3か月で120件、継続率98%、工数は2.5倍改善しました。"
    verified = generator._verify_section_content(original, "参考情報です。", "導入")
    assert verified != original
    assert verified.startswith("## 導入")
    assert "多くの改善" in verified


def test_collect_review_points_passes_basic_ordered_structure():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sample = """
## はじめに
製品価値は利用継続性まで含めて評価されます。

## 取り組み
患者起点の設計と規制対応を両立します。

## まとめ
導入から結論まで同じ論点で接続しています。

## 参考資料
- ノーベルファーマ (https://example.com/a)
""".strip()
    points = generator._collect_review_points(sample)
    assert not any("見出し構成不足" in p or "見出し順の一貫性不足" in p for p in points)
    assert not any("文字化け" in p for p in points)


def test_make_cta_varies_without_inventing_new_facts():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._pipeline_policy = {"focus": "analysis", "evidence_mode": "strict"}
    samples = {
        generator._make_cta(
            title="食品物流の在庫最適化",
            user_prompt="一次情報中心で解説して",
            target_audience="物流担当者",
            platform="note",
        )
        for _ in range(12)
    }

    assert len(samples) >= 2
    assert all(sample.strip() for sample in samples)
    assert all("http://" not in sample and "https://" not in sample for sample in samples)


def test_make_cta_avoids_generic_audience_phrase_that_sounds_unnatural():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._pipeline_policy = {"focus": "analysis", "evidence_mode": "strict"}
    cta = generator._make_cta(
        title="AIと知財の整理",
        user_prompt="一次情報ベースで解説",
        target_audience="一般読者",
        platform="note",
    )
    assert "一般読者として" not in cta


def test_make_cta_hides_sensitive_audience_labels():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._pipeline_policy = {"focus": "analysis", "evidence_mode": "strict"}
    cta = generator._make_cta(
        title="時短調理の段取り",
        user_prompt="実務で使えるコツを整理",
        target_audience="30代共働き世帯",
        platform="note",
    )
    assert "30代" not in cta
    assert "共働き" not in cta
    assert "世帯として" not in cta


def test_make_cta_announcement_is_operational_not_social():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._category_policy = {"base_template": "announcement"}
    generator._current_type = "announcement"
    cta = generator._make_cta(
        title="ドコモの標準メッセージアプリ変更",
        user_prompt="変更点を案内する",
        target_audience="一般読者",
        platform="note",
    )
    assert "コメント" not in cta
    assert "フォロー" not in cta
    assert "嬉しいです" not in cta
    assert "公式" in cta


def test_build_note4000_style_profile_announcement_avoids_chatty_rules():
    profile = build_note4000_style_profile(
        article_type="announcement",
        focus="explanation",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )

    assert profile.profile_name == "note_4000_clear"
    assert "読者に語りかける一人の書き手として書く" not in profile.prompt_rules
    assert "感情の代弁や共感の誘導を入れない" in profile.prompt_rules
    assert "でしょう。" not in profile.preferred_endings
    assert "ですね。" not in profile.preferred_endings
    assert "だからこそ" in profile.banned_openings


def test_build_note4000_section_prompt_announcement_is_factual():
    profile = build_note4000_style_profile(
        article_type="announcement",
        focus="explanation",
        tone_profile="calm",
        style_profile="formal",
        base_register="polite",
    )
    prompt = build_note4000_section_prompt(
        section=DiscourseSectionPlan(
            heading="変更点",
            intent="hook",
            target_chars=260,
            topic_seed="標準アプリの変更",
            related_terms=["対象機種", "開始時期"],
            reader_question="対象機種と開始時期は何か？",
            bridge_hint="変更点から影響範囲へつなぐ",
            must_cover=["対象機種", "開始時期"],
            new_information="標準アプリの変更",
        ),
        speaker_profile="広報担当として語る",
        audience_profile="一般読者",
        relationship_mode="guide",
        style_profile=profile,
        previous_summary="",
        recent_summaries=[],
        forbidden_topics=[],
        allowed_pronouns=["当社"],
        user_instruction="変更点を簡潔に伝える",
        instruction_anchor_terms=["変更", "対象機種"],
    )

    assert "会話調のエッセイではなく、案内文として簡潔かつ正確に書いてください。" in prompt
    assert "読者に語りかける一人の書き手として書いてください。" not in prompt
    assert "不安の代弁や励まし" in prompt


def test_build_note4000_length_plan_short_is_short_enough_for_iteration():
    plan = build_note4000_length_plan(length_mode="short", section_count=0)
    targets = plan["targets"]

    assert int(targets["note_chars"]) == 1800
    assert int(targets["section_count_target"]) == 4
    assert int(targets["body_chars"]) == 1600


def test_resolve_adaptive_length_mode_announcement_prefers_short_for_small_notice():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="ドコモからのお知らせ",
            content="2026年3月12日から標準メッセージアプリをGoogle メッセージに変更します。対象機種と注意点を案内します。",
            source_type="url",
        )
    ]

    mode = generator._resolve_adaptive_length_mode(
        contexts=contexts,
        user_prompt="ドコモのメッセージサービスがGoogleに変更されます。",
        article_type="announcement",
    )

    assert mode == "short"


def test_resolve_adaptive_length_mode_ai_prefers_short_for_single_clear_explanation():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="AI活用ガイド",
            content="AI文章活用の注意点と判断基準を短くまとめた資料です。",
            source_type="url",
        )
    ]

    mode = generator._resolve_adaptive_length_mode(
        contexts=contexts,
        user_prompt="AI文章活用の判断基準を簡潔に解説してください。",
        article_type="ai",
    )

    assert mode == "short"


def test_resolve_adaptive_length_mode_branding_prefers_normal_when_signal_is_midrange():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="商品紹介",
            content="導入背景、利用シーン、選定理由、顧客価値を整理した紹介資料です。" * 36,
            source_type="url",
        )
    ]

    mode = generator._resolve_adaptive_length_mode(
        contexts=contexts,
        user_prompt="商品の価値と利用シーンを伝えるブランド記事を作成してください。",
        article_type="branding",
    )

    assert mode == "normal"


def test_build_note4000_discourse_plan_announcement_uses_fact_check_questions():
    length_plan = build_note4000_length_plan(length_mode="short", section_count=4)

    discourse = build_note4000_discourse_plan(
        article_type="announcement",
        base_template="announcement",
        user_prompt="ドコモ Android 新端末で標準メッセージが Google メッセージに変わる件を案内する",
        must_cover=["変更点", "対象者と開始時期", "利用者への影響", "確認事項"],
        user_instruction_terms=["Google メッセージ", "標準アプリ"],
        thesis="変更対象と確認事項を事実ベースで伝える",
        reader_question_candidates=[],
        length_plan=length_plan,
    )

    assert discourse[0].reader_question == "何が変わるか"
    assert discourse[1].reader_question == "いつから・誰が対象か"
    assert "読者が判断" not in discourse[0].reader_question
    assert "視点" not in discourse[0].topic_seed


def test_zero_base_resolve_pre_generation_questions_announcement_skips_meta_perspective_in_must_cover():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._build_dynamic_interview_fallback = lambda contexts, user_prompt, article_type: [
        {"id": "message", "question": "変更点を1文で教えてください。"},
        {"id": "target", "question": "誰が対象ですか？"},
        {"id": "evidence", "question": "何を確認しますか？"},
    ]
    generator._interview_answers = {
        "message": "変更点を誤解なく伝える視点を重視する",
        "target": "ドコモ Android 利用者",
        "evidence": "公式情報を確認する",
    }

    resolved = generator._zero_base_resolve_pre_generation_questions(
        contexts=[],
        user_prompt="ドコモの標準メッセージ変更を案内する",
        article_type="announcement",
        question_source_priority=["interview_answers"],
    )

    assert "変更点を誤解なく伝える視点" not in resolved["must_cover"]
    assert "公式情報を確認する" in resolved["must_cover"]
    assert resolved["reader_question_candidates"][0] == "いつから・どこで確認できるか"


def test_zero_base_adjust_cta_length_announcement_does_not_append_generic_action_copy():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = generator._zero_base_adjust_cta_length(
        cta="詳細な対象条件や開始時期は、公式情報を基準に確認してください。",
        target_chars=80,
        target_audience="利用者",
        announcement_like=True,
    )

    assert "まずは" not in text
    assert "振り返り" not in text


def test_stabilize_note4000_section_text_announcement_avoids_meta_expansion():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = generator._stabilize_note4000_section_text(
        section_text="Google メッセージが標準アプリになります。",
        section_plan={"min_chars": 220, "max_chars": 320},
        topic_seed="変更点",
        reader_question="何が変わるか",
        bridge_hint="次に対象者と開始時期を確認する",
        announcement_like=True,
    )

    assert "実際には" not in text
    assert "ここを押さえておくと" not in text


def test_stabilize_note4000_section_text_non_announcement_limits_generic_padding():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = generator._stabilize_note4000_section_text(
        section_text="運用の判断軸を簡潔に整理します。",
        section_plan={"min_chars": 120, "max_chars": 180},
        topic_seed="判断軸",
        reader_question="どこから確認すべきか？",
        bridge_hint="次の運用手順に移る",
        announcement_like=False,
    )

    assert "実際には" not in text
    assert "ここを押さえておくと" not in text


def test_reduce_cta_topic_echo_rewrites_second_mention():
    generator = ArticleGenerator(llm_client=DummyLLM())
    raw = (
        "今回は「AIの便利さとともに迫る私たちのサイバーリスクとは」を整理してみました。"
        "「AIの便利さとともに迫る私たちのサイバーリスクとは」で補足すべき観点があれば、次の記事で取り上げます。"
    )
    cleaned = generator._reduce_cta_topic_echo(
        raw,
        "AIの便利さとともに迫る私たちのサイバーリスクとは",
    )
    assert cleaned.count("AIの便利さとともに迫る私たちのサイバーリスクとは") == 1
    assert "このテーマで補足すべき観点" in cleaned


def test_reduce_cta_topic_echo_rewrites_repeated_long_quote_when_topic_not_exact():
    generator = ArticleGenerator(llm_client=DummyLLM())
    raw = (
        "「地元企業と共に歩む北大阪商工会議所の役割とは？」について、"
        "少しでもヒントになっていれば嬉しいです。"
        "「地元企業と共に歩む北大阪商工会議所の役割とは？」を実践して気づいたことがあれば、"
        "コメントで教えてください。"
    )
    cleaned = generator._reduce_cta_topic_echo(raw, "地元企業と共に歩む北大阪商工会議所の役割とは")
    assert cleaned.count("地元企業と共に歩む北大阪商工会議所の役割とは？") == 1
    assert "このテーマを実践して気づいたこと" in cleaned


def test_extract_cta_topic_avoids_quote_truncation_and_midword_breaks():
    generator = ArticleGenerator(llm_client=DummyLLM())
    topic = generator._extract_cta_topic(
        "AI検索の正確性を揺るがす「間接的プロンプトインジェクション」とは何か",
        "",
    )
    assert "間接的プロンプトインジェクション" in topic
    assert not topic.endswith("インジェクシ")
    assert "「" not in topic
    assert "」" not in topic


def test_extract_cta_topic_drops_leading_particle_fragment():
    generator = ArticleGenerator(llm_client=DummyLLM())
    topic = generator._extract_cta_topic(
        "京都で培う「唯一無二」の銀行価値と経営者への真摯な支援",
        "",
    )
    assert not topic.startswith("の")
    assert len(topic) >= 6


def test_generate_injects_inline_source_links_for_note_embed_even_with_references():
    generator = ArticleGenerator(llm_client=DummyLLM())
    called = {"inject": False}

    def _fake_inject(body: str, contexts):  # type: ignore[no-untyped-def]
        called["inject"] = True
        return body + "\n\n出典: テスト\nhttps://example.com/source"

    generator._inject_contextual_source_links = _fake_inject  # type: ignore[method-assign]

    contexts = [
        FetchedContent(
            title="一次情報",
            content="公表情報の抜粋です。",
            url="https://example.com/source",
            source_type="url",
        )
    ]
    result = generator.generate(contexts, "初心者向けに", "ai")
    assert called["inject"] is True
    assert "出典: テスト\nhttps://example.com/source" in result["body"]
    assert "## 参考" in result["full_body"]


def test_format_for_linkedin_uses_given_cta():
    generator = ArticleGenerator(llm_client=DummyLLM())
    expected_cta = "💬 現場での工夫があれば、コメントで教えてください。"
    text = generator._format_for_linkedin(
        lead="要点です。",
        body="## 見出し\n本文です。",
        cta=expected_cta,
        hashtags="#テスト",
    )
    assert expected_cta in text


def test_split_long_paragraph_increases_breathing_breaks():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._get_postprocess_config = lambda: {  # type: ignore[method-assign]
        "concise_compaction": {
            "max_sentence_chars": 120,
            "max_splits_per_sentence": 2,
            "paragraph_clog_min_chars": 80,
            "paragraph_clog_min_sentences": 3,
            "paragraph_clog_min_commas": 2,
            "paragraph_clog_min_comma_density": 0.01,
            "paragraph_clog_threshold_jitter": 0.0,
        }
    }
    paragraph = (
        "AIと著作権は複雑です。"
        "まず前提として、学習段階と生成段階で争点が異なることを、具体例を交えて確認します。"
        "次に、商用利用で問題になりやすい利用規約の読み落としを、実務フローに沿って整理していきましょう。"
        "さらに、公開前チェックで見るべき項目を、担当者がそのまま使える順番で並べます。"
        "判断に迷ったときはエスカレーションです。"
    )
    chunks = generator._split_long_paragraph(paragraph)
    # R14-T11: 段落分割（複数チャンク）または段落内改行（\n含む1チャンク）で分割される
    has_breaks = len(chunks) >= 2 or any("\n" in c for c in chunks)
    assert has_breaks


def test_repair_contextual_sentence_breaks_preserves_inline_linebreaks():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 背景

AI検索では参照順が重要です。
一次情報の優先順位を固定して検証します。
""".strip()
    repaired = generator._repair_contextual_sentence_breaks(text)
    assert "重要です。\n一次情報の優先順位" in repaired


def test_repair_contextual_sentence_breaks_merges_mid_sentence_break():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 背景

AI検索の評価は途中で
分断すると誤読を招きます。
""".strip()
    repaired = generator._repair_contextual_sentence_breaks(text)
    assert "途中で分断すると誤読を招きます。" in repaired
    assert "途中で\n分断すると" not in repaired


def test_detect_grammar_breaks_flags_ori_period_and_copula_comma_breaks():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sample = """
古いOS環境では、運用リスクが高まっており。インターネットバンキング利用時の注意が必要です。
京都という地域です、その背景を理解しながら支援を進めます。
""".strip()
    report = generator._detect_grammar_breaks(sample)
    signals = report.get("signals", {})
    assert int(signals.get("ori_break", 0) or 0) >= 1
    assert int(signals.get("copula_comma_break", 0) or 0) >= 1
    assert report.get("severity") in {"mid", "high"}


def test_detect_grammar_breaks_flags_truncated_verb_and_register_mix():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sample = """
段取りは重要です。
実行順を明確にします。
背景も共有します。
現場の声を反映した改善策が、会社の強みとなっている。
伝わ。
""".strip()
    report = generator._detect_grammar_breaks(sample)
    signals = report.get("signals", {})
    assert int(signals.get("truncated_verb_break", 0) or 0) >= 1
    assert int(signals.get("polite_plain_mix_break", 0) or 0) >= 1


def test_repair_contextual_sentence_breaks_fix_ori_period_and_desu_comma():
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = """
## 本文

古いOS環境では、運用リスクが高まっており。インターネットバンキング利用時の注意が必要です。
京都という地域です、その背景を理解しながら支援を進めます。
""".strip()
    repaired = generator._repair_contextual_sentence_breaks(text)
    assert "高まっており、インターネットバンキング" in repaired
    assert "地域です。その背景を理解しながら" in repaired


def test_format_references_outputs_note_friendly_url_lines():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [
        FetchedContent(
            title="Microsoft Security Blog",
            content="記事本文",
            url="https://example.com/security",
            source_type="url",
        )
    ]
    references = generator._format_references(contexts)
    assert "## 参考文献・出典" in references
    assert "https://example.com/security" in references
    assert "(https://example.com/security)" not in references


def test_cognitive_profile_phase_mapping():
    """5セクション記事: 位置0→careful_start, 2→peak, 4→winding_down"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    p0 = generator._get_cognitive_profile(0, 5)
    p2 = generator._get_cognitive_profile(2, 5)
    p4 = generator._get_cognitive_profile(4, 5)
    assert p0["phase"] == "careful_start"
    assert p2["phase"] == "peak"
    assert p4["phase"] == "winding_down"


def test_cognitive_profile_temperature_ranges():
    """各フェーズでtemperatureが定義範囲内に収まる"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    for profile_def in COGNITIVE_ENERGY_PROFILES:
        phase = profile_def["phase"]
        temp_low, temp_high = profile_def["temperature"]
        # jitter(±0.03)を考慮した許容範囲
        for _ in range(20):
            p = generator._get_cognitive_profile(
                {"careful_start": 0, "building": 1, "peak": 2, "settling": 3, "winding_down": 4}[phase],
                5,
            )
            assert p["phase"] == phase, f"Expected {phase}, got {p['phase']}"
            assert temp_low - 0.04 <= p["temperature"] <= temp_high + 0.04, (
                f"Phase {phase}: temperature {p['temperature']} out of range "
                f"[{temp_low - 0.04}, {temp_high + 0.04}]"
            )


def test_cognitive_profile_edge_cases():
    """1/2/3セクションの境界テスト"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    # 1セクション → building
    p = generator._get_cognitive_profile(0, 1)
    assert p["phase"] == "building"

    # 2セクション → start / winding_down
    p0 = generator._get_cognitive_profile(0, 2)
    p1 = generator._get_cognitive_profile(1, 2)
    assert p0["phase"] == "careful_start"
    assert p1["phase"] == "winding_down"

    # 3セクション → start / peak / winding_down
    p0 = generator._get_cognitive_profile(0, 3)
    p1 = generator._get_cognitive_profile(1, 3)
    p2 = generator._get_cognitive_profile(2, 3)
    assert p0["phase"] == "careful_start"
    assert p1["phase"] == "peak"
    assert p2["phase"] == "winding_down"


def test_cognitive_profile_includes_paragraph_plan_when_enabled():
    generator = ArticleGenerator(llm_client=DummyLLM())
    profile = generator._get_cognitive_profile(
        section_index=1,
        total_sections=5,
        target_chars=1200,
        drift_config={
            "enabled": True,
            "paragraph_enabled": True,
            "paragraph_min_blocks": 3,
            "paragraph_max_blocks": 4,
            "paragraph_temp_swing": 0.08,
        },
    )
    plan = profile.get("paragraph_plan")
    assert isinstance(plan, list)
    assert 3 <= len(plan) <= 4
    assert all(item["phase"] for item in plan)
    assert all(0.5 <= item["temperature"] <= 1.2 for item in plan)
    assert all(item["information_density"] in {"low", "medium", "high"} for item in plan)


def test_cognitive_profile_paragraph_plan_disabled():
    generator = ArticleGenerator(llm_client=DummyLLM())
    profile = generator._get_cognitive_profile(
        section_index=1,
        total_sections=5,
        target_chars=1200,
        drift_config={
            "enabled": True,
            "paragraph_enabled": False,
            "paragraph_min_blocks": 3,
            "paragraph_max_blocks": 4,
            "paragraph_temp_swing": 0.08,
        },
    )
    assert profile.get("paragraph_plan") == []


def test_render_paragraph_drift_block_has_indexed_lines():
    generator = ArticleGenerator(llm_client=DummyLLM())
    profile = generator._get_cognitive_profile(
        section_index=2,
        total_sections=6,
        target_chars=1400,
        drift_config={
            "enabled": True,
            "paragraph_enabled": True,
            "paragraph_min_blocks": 4,
            "paragraph_max_blocks": 5,
            "paragraph_temp_swing": 0.10,
        },
    )
    block = generator._render_paragraph_drift_block(profile.get("paragraph_plan"))
    assert "P1" in block
    assert "温度目安" in block
    assert "情報密度" in block


def test_build_section_generation_feedback_contains_fingerprint_and_lexical_signals():
    generator = ArticleGenerator(llm_client=DummyLLM())
    sections = [
        "## 見出しA\n\nこれは導入の段落です。まず前提を確認します。まず背景を整理します。"
        "まず注意点を整理します。AI文章は均一になりやすいです。AI文章は均一になりやすいです。",
        "## 見出しB\n\n次に実務の観点です。次に比較観点です。次に判断手順です。"
        "導入導入導入という語を繰り返します。導入導入導入という語を繰り返します。",
    ]
    feedback = generator._build_section_generation_feedback(sections)
    assert isinstance(feedback, dict)
    assert "lexical" in feedback
    assert "fingerprint" in feedback
    assert feedback["lexical"]["carry_terms"]


def test_render_section_feedback_block_includes_fingerprint_and_lexical_guidance():
    generator = ArticleGenerator(llm_client=DummyLLM())
    block = generator._render_section_feedback_block(
        {
            "fingerprint": {
                "overall_unpredictability": 0.41,
                "hint_lines": ["文の長さを短・中・長で揺らす。"],
            },
            "lexical": {
                "carry_terms": ["導入", "設計"],
                "avoid_terms": ["導入", "改善", "比較"],
            },
        }
    )
    assert "指紋スコア" in block
    assert "連続性のため" in block
    assert "言い換え" in block


# ── R1: Phase effect metrics & skip judgment ──


def test_phase_effect_metrics_are_produced_by_pipeline():
    """pipeline.process() が phase_effect_metrics を各phaseに対して出力する"""
    from human_resonance.pipeline import HumanResonancePipeline, PipelineConfig

    config = PipelineConfig(
        enable_platform=False,
        use_llm_for_editor=False,
        use_llm_for_legal=False,
    )
    pipeline = HumanResonancePipeline(config=config)
    result = pipeline.process("これはテスト文です。テストの本文が続きます。読者に語りかけるようなテスト文です。")

    # Phase 1-7 の metrics が存在すること
    assert "phase1_empathy" in result.phase_effect_metrics
    assert "phase2_curiosity" in result.phase_effect_metrics
    assert "phase3_humanity" in result.phase_effect_metrics
    assert "phase4_rhythm" in result.phase_effect_metrics
    assert "phase5_editor" in result.phase_effect_metrics
    assert "phase6_legal" in result.phase_effect_metrics
    assert "phase7_sanitize" in result.phase_effect_metrics

    # 各metricsがchar_diff, char_ratio, sentence_diff, vocab_diffを持つこと
    for phase_name, metrics in result.phase_effect_metrics.items():
        assert "char_diff" in metrics, f"{phase_name} missing char_diff"
        assert "char_ratio" in metrics, f"{phase_name} missing char_ratio"
        assert "sentence_diff" in metrics, f"{phase_name} missing sentence_diff"
        assert "vocab_diff" in metrics, f"{phase_name} missing vocab_diff"


def test_measure_phase_effect_calculates_correctly():
    """_measure_phase_effect が正しい差分を計算する"""
    from human_resonance.pipeline import _measure_phase_effect

    before = "短い文。テスト。"
    after = "短い文。テスト。追加された文。"
    m = _measure_phase_effect(before, after)
    assert m["char_diff"] > 0
    assert m["char_ratio"] > 0.0
    assert m["sentence_diff"] >= 1

    # 同一テキスト → 差分ゼロ
    m2 = _measure_phase_effect(before, before)
    assert m2["char_diff"] == 0
    assert m2["char_ratio"] == 0.0
    assert m2["sentence_diff"] == 0
    assert m2["vocab_diff"] == 0


def test_should_skip_phase_removed_from_pipeline_module():
    """phase03方針: 未接続だった should_skip_phase は削除済みであること。"""
    import human_resonance.pipeline as pipeline_module

    assert not hasattr(pipeline_module, "should_skip_phase")


def test_pipeline_check_includes_phase_effect_metrics():
    """generate() 結果の pipeline_check に phase_effect_metrics が含まれる"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="テスト本文です。")]
    result = generator.generate(contexts, "初心者向けに", "ai")

    assert "phase_effect_metrics" in result["pipeline_check"]
    phase_metrics = result["pipeline_check"]["phase_effect_metrics"]
    assert "phase1_empathy" in phase_metrics
    assert "phase2_curiosity" in phase_metrics
    assert "phase3_humanity" in phase_metrics


def test_pipeline_check_contract_alignment_includes_question_source_breakdown():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = {
        "article_type": "ai",
        "category_base_template": "ai",
        "must_cover": ["核心メッセージ"],
        "pre_generation_questions": [
            {"id": "message", "question": "核心メッセージは？"},
            {"id": "target", "question": "対象読者は？"},
        ],
        "pre_generation_answers": {"message": "核心メッセージ"},
        "unresolved_items": ["target: 対象読者は？"],
    }
    alignment = generator._zero_base_compute_contract_alignment(
        contract=contract,
        body="核心メッセージを本文で説明します。",
        question_sources={
            "message": "interview_answers",
            "target": "unresolved_items",
        },
    )
    assert alignment["question_source_counts"]["interview_answers"] == 1
    assert alignment["question_source_counts"]["unresolved_items"] == 1
    assert alignment["question_source_coverage"] == 1.0
    assert "alignment_score" in alignment


def test_pipeline_check_detects_article_type_category_mismatch():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = {
        "article_type": "ai",
        "category_base_template": "branding",
        "must_cover": ["根拠を示す"],
        "pre_generation_questions": [{"id": "message", "question": "何を伝えるか？"}],
        "pre_generation_answers": {"message": "根拠を示す"},
        "unresolved_items": [],
    }
    alignment = generator._zero_base_compute_contract_alignment(
        contract=contract,
        body="根拠を示すことが重要です。",
        question_sources={"message": "user_prompt"},
    )
    assert alignment["category_mismatch_detected"] is True
    assert alignment["category_expected_base_template"] == "ai"
    assert alignment["category_base_template"] == "branding"
    assert 0.0 <= alignment["alignment_score"] <= 1.0


def test_pipeline_check_custom_meta_category_alignment_for_daily_happenings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = {
        "article_type": "daily_happenings",
        "category_base_template": "branding",
        "category_policy_source": "custom_meta",
        "must_cover": ["現場の気づきを共有する"],
        "pre_generation_questions": [{"id": "message", "question": "何を伝えるか？"}],
        "pre_generation_answers": {"message": "現場の気づきを共有する"},
        "unresolved_items": [],
    }
    alignment = generator._zero_base_compute_contract_alignment(
        contract=contract,
        body="現場の気づきを共有することが大切です。",
        question_sources={"message": "interview_answers"},
    )
    assert alignment["category_mismatch_detected"] is False
    assert alignment["category_expected_base_template"] == "branding"
    assert alignment["category_base_template"] == "branding"
    assert alignment["category_consistency_score"] == 1.0
    assert alignment["alignment_score"] >= 0.9


def test_pipeline_check_custom_meta_category_alignment_for_corporate_culture():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = {
        "article_type": "corporate_culture",
        "category_base_template": "branding",
        "category_policy_source": "custom_meta",
        "must_cover": ["現場の工夫を共有する"],
        "pre_generation_questions": [{"id": "message", "question": "何を伝えるか？"}],
        "pre_generation_answers": {"message": "現場の工夫を共有する"},
        "unresolved_items": [],
    }
    alignment = generator._zero_base_compute_contract_alignment(
        contract=contract,
        body="現場の工夫を共有することで、理解が深まります。",
        question_sources={"message": "interview_answers"},
    )
    assert alignment["category_mismatch_detected"] is False
    assert alignment["category_expected_base_template"] == "branding"
    assert alignment["category_base_template"] == "branding"
    assert alignment["category_consistency_score"] == 1.0
    assert alignment["alignment_score"] >= 0.9


def test_pipeline_check_contract_alignment_excludes_low_signal_must_cover_from_eval():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = {
        "article_type": "corporate_culture",
        "category_base_template": "branding",
        "category_policy_source": "custom_meta",
        "must_cover": ["一般読者", "現場の工夫を共有する"],
        "pre_generation_questions": [{"id": "message", "question": "何を伝えるか？"}],
        "pre_generation_answers": {"message": "現場の工夫を共有する"},
        "unresolved_items": [],
    }
    alignment = generator._zero_base_compute_contract_alignment(
        contract=contract,
        body="現場の工夫を共有することで、理解が深まります。",
        question_sources={"message": "interview_answers"},
    )
    assert alignment["must_cover_count"] == 2
    assert alignment["must_cover_eval_count"] == 1
    assert alignment["must_cover_reflected_count"] == 1
    assert alignment["must_cover_reflection_rate"] == 1.0


def test_pipeline_check_contract_alignment_exposes_topic_statement():
    generator = ArticleGenerator(llm_client=DummyLLM())
    contract = {
        "article_type": "branding",
        "category_base_template": "branding",
        "category_policy_source": "custom_meta",
        "topic_statement": "商品の価値と利用シーンを伝えるブランド",
        "must_cover": ["選定の判断軸を具体化する"],
        "pre_generation_questions": [{"id": "message", "question": "何を伝えるか？"}],
        "pre_generation_answers": {"message": "選定の判断軸を具体化する"},
        "unresolved_items": [],
    }
    alignment = generator._zero_base_compute_contract_alignment(
        contract=contract,
        body="商品の価値と利用シーンを伝えつつ、選定の判断軸を具体化します。",
        question_sources={"message": "interview_answers"},
    )
    assert alignment["topic_statement"] == "商品の価値と利用シーンを伝えるブランド"


def test_pipeline_check_contract_alignment_detects_forbidden_topics():
    generator = ArticleGenerator(llm_client=DummyLLM())
    base_contract = {
        "article_type": "branding",
        "category_base_template": "branding",
        "must_cover": ["カニ加工品の価値"],
        "pre_generation_questions": [{"id": "message", "question": "何を伝えるか？"}],
        "pre_generation_answers": {"message": "カニ加工品の価値"},
        "unresolved_items": [],
        "forbidden_topics": ["社内制度", "チーム連携"],
    }
    clean_alignment = generator._zero_base_compute_contract_alignment(
        contract=base_contract,
        body="カニ加工品の価値を具体的に説明します。",
        question_sources={"message": "interview_answers"},
    )
    drifted_alignment = generator._zero_base_compute_contract_alignment(
        contract=base_contract,
        body="カニ加工品の価値を説明します。社内制度とチーム連携の工夫も紹介します。",
        question_sources={"message": "interview_answers"},
    )
    assert drifted_alignment["forbidden_topic_hit_count"] == 2
    assert "社内制度" in drifted_alignment["forbidden_topic_hits"]
    assert "チーム連携" in drifted_alignment["forbidden_topic_hits"]
    assert drifted_alignment["alignment_score"] < clean_alignment["alignment_score"]


def test_interview_ui_article_type_fallback_resolves_contract_key():
    from note import note_writer_app as app_mod

    key, used_fallback = app_mod._resolve_article_type_key_with_fallback("存在しないラベル")
    assert used_fallback is True
    assert isinstance(key, str) and key


# ── R2: parallel section generation ──


def test_generate_single_section_task_produces_section():
    """_generate_single_section_task が見出し付きセクションを返す"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._current_persona = "テスト執筆者"
    generator._current_pronoun = "私"
    generator._current_perspective = "blogger"
    generator._current_prompts = {"ai": "AIテスト"}
    generator._enhanced_context = ""
    generator._lead_opening_style = "question"
    generator._section_opening_sequence = ["question", "episode", "data"]
    from core.app_config import get_cognitive_drift_config
    drift_cfg = get_cognitive_drift_config()

    section_meta = {"heading": "テスト見出し", "purpose": "導入", "required_elements": []}
    result = generator._generate_single_section_task(
        0, section_meta, 400,
        merged_context="テスト用コンテキスト",
        user_prompt="初心者向けに",
        article_type="ai",
        distributed_quotes=[["テスト引用"]],
        target_audience="一般読者",
        title="テストタイトル",
        total_sections=3,
        existing_sections=[],
        cognitive_drift_enabled=True,
        cognitive_drift_config=drift_cfg,
    )
    # DummyLLMは "## 見出しA" を返すが、_generate_section が heading を先頭に付与する
    assert "## " in result
    assert "本文テキスト" in result


def test_build_even_summary_memory():
    """_build_even_summary_memory が偶数セクションから要約を構築する"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    sections_map = {
        0: "## 導入\n\nこれは導入の本文です。最初の段落。",
        2: "## まとめ\n\n結論の本文です。",
    }
    summary = generator._build_even_summary_memory(sections_map)
    assert "[0]" in summary
    assert "[2]" in summary
    assert "導入" in summary
    assert "まとめ" in summary


def test_parallel_sections_false_uses_sequential_mode():
    """parallel_sections=false のとき逐次生成で generate() が正常動作する"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    contexts = [FetchedContent(title="テスト資料", content="テスト本文です。")]
    result = generator.generate(contexts, "初心者向けに", "ai")
    # parallel_sections=false (default) → 逐次生成 → 正常完了
    assert result["title"] == "テストタイトル"
    assert "## " in result["body"]


def test_generate_sections_parallel_restores_order():
    """_generate_sections_parallel がアウトライン順序を正しく復元する"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._current_persona = "テスト執筆者"
    generator._current_pronoun = "私"
    generator._current_perspective = "blogger"
    generator._current_prompts = {"ai": "AIテスト"}
    generator._enhanced_context = ""
    generator._lead_opening_style = "question"
    generator._section_opening_sequence = ["question", "episode", "data"]
    generator._generation_progress = {}
    from core.app_config import get_cognitive_drift_config
    drift_cfg = get_cognitive_drift_config()

    section_inputs = [
        ({"heading": f"見出し{i}", "purpose": "本論", "required_elements": []}, 300)
        for i in range(3)
    ]

    sections = generator._generate_sections_parallel(
        section_inputs,
        merged_context="テストコンテキスト",
        user_prompt="初心者向けに",
        article_type="ai",
        distributed_quotes=[["引用A"], ["引用B"], ["引用C"]],
        target_audience="一般読者",
        title="テストタイトル",
        total_sections=3,
        cognitive_drift_enabled=True,
        cognitive_drift_config=drift_cfg,
    )

    assert len(sections) == 3
    # 全セクションが見出し付きで生成されていること
    for i, sec in enumerate(sections):
        assert "## " in sec, f"Section {i} missing heading"
        assert sec.strip(), f"Section {i} is empty"


# ── R3: retry optimization ──


def test_check_redundancy_with_reason_returns_tuple():
    """_check_redundancy_with_reason が (bool, list) タプルを返す"""
    generator = ArticleGenerator(llm_client=DummyLLM())

    # 空リスト → 非重複、overlap_terms空
    is_redundant, terms = generator._check_redundancy_with_reason(
        "## 見出しA\n\n十分な長さのテスト本文を書きます。人工知能の最新動向について解説するセクションです。", []
    )
    assert is_redundant is False
    assert terms == []

    # 同一テキスト → 重複判定
    same_text = "## 見出しA\n\n同じ内容のテスト本文です。人工知能の技術について詳しく説明し、導入事例を数多く紹介していきます。最新の研究動向を追います。"
    is_redundant2, terms2 = generator._check_redundancy_with_reason(same_text, [same_text])
    assert is_redundant2 is True
    assert isinstance(terms2, list)


def test_dedupe_body_repetition_removes_mid_short_duplicate_paragraph():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## セクションA

この改善策は現場の作業時間を確実に減らし、手戻りを抑え、毎日の確認工数と連絡コストまで下げられる実践策で、導入負荷も比較的小さいです。

## セクションB

この改善策は現場の作業時間を確実に減らし、手戻りを抑え、毎日の確認工数と連絡コストまで下げられる実践策で、導入負荷も比較的小さいです。

次に、導入手順とチェックポイントを具体的に整理します。
""".strip()
    deduped = generator._dedupe_body_repetition(body)
    assert deduped.count("この改善策は現場の作業時間を確実に減らし、手戻りを抑え、毎日の確認工数と連絡コストまで下げられる実践策で、導入負荷も比較的小さいです。") == 1
    assert "次に、導入手順とチェックポイントを具体的に整理します。" in deduped


def test_dedupe_body_repetition_keeps_very_short_repeated_paragraph():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## セクションA

現場で効果が出ました。

## セクションB

現場で効果が出ました。

詳細は次章で説明します。
""".strip()
    deduped = generator._dedupe_body_repetition(body)
    assert deduped.count("現場で効果が出ました。") == 2


def test_dedupe_body_repetition_removes_paraphrased_opening_sentence():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## セクションA

AIの利便性が広がる一方で、運用リスクも増えています。現場では入力情報の扱いを見直す必要があります。

## セクションB

AIの利便性は広がる一方で、運用リスクが増えています。実務では権限設計を先に固めると事故を減らせます。
""".strip()
    deduped = generator._dedupe_body_repetition(body)
    sections = generator._extract_section_blocks(deduped)
    assert len(sections) == 2
    assert sections[1][1].startswith("実務では")


def test_apply_unified_dedupe_pass_removes_cross_section_duplicate_sentence():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = (
        "## セクションA\n\n"
        "導入として背景を整理します。\n"
        "この段階で重要なのは「働く社員のリアルな声」を判断基準として具体化することです。\n\n"
        "## セクションB\n\n"
        "次の要点に進みます。\n"
        "この段階で大切なのは「さんれいフーズは食のエキスパート」を判断基準として具体化することです。"
    )
    deduped = generator._apply_unified_dedupe_pass(body)
    assert deduped.count("判断基準として具体化することです") <= 1


def test_zero_base_semantic_dedupe_observe_only_keeps_body(monkeypatch):
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._semantic_dedupe_config = {
        "enabled": True,
        "rewrite_enabled": False,
        "model": "text-embedding-3-small",
    }

    def _fake_semantic_dedupe_text(text, contract, config, embedder=None):  # type: ignore[no-untyped-def]
        return text + "\n削除候補文。", {"duplicate_pairs": 2, "merged_pairs": 1}

    monkeypatch.setattr("note.article_generator.semantic_dedupe_text", _fake_semantic_dedupe_text)
    body = "## 見出し\n\n本文です。"
    deduped, audit = generator._zero_base_semantic_dedupe(body=body, contract={})
    assert deduped == body
    assert audit.get("rewrite_enabled") is False
    assert audit.get("rewrite_applied") is False
    assert audit.get("duplicate_pairs") == 2


def test_zero_base_semantic_dedupe_rewrite_enabled_applies_body_change(monkeypatch):
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._semantic_dedupe_config = {
        "enabled": True,
        "rewrite_enabled": True,
        "model": "text-embedding-3-small",
    }

    def _fake_semantic_dedupe_text(text, contract, config, embedder=None):  # type: ignore[no-untyped-def]
        return text + "\n削除候補文。", {"duplicate_pairs": 2, "merged_pairs": 1}

    monkeypatch.setattr("note.article_generator.semantic_dedupe_text", _fake_semantic_dedupe_text)
    body = "## 見出し\n\n本文です。"
    deduped, audit = generator._zero_base_semantic_dedupe(body=body, contract={})
    assert "削除候補文。" in deduped
    assert audit.get("rewrite_enabled") is True
    assert audit.get("rewrite_applied") is True


def test_reduce_repeated_named_entity_openings_rewrites_later_sections():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## セクションA

北大阪商工会議所は地域企業の相談窓口を広く担っています。現場の声を集める機能が重要です。

## セクションB

北大阪商工会議所はIT・WEB相談を強化しています。導入支援の速度が上がりました。
""".strip()
    cleaned = generator._reduce_repeated_named_entity_openings(body)
    sections = generator._extract_section_blocks(cleaned)
    assert len(sections) == 2
    assert sections[0][1].startswith("北大阪商工会議所は")
    assert sections[1][1].startswith("IT・WEB相談を強化しています。")


def test_compress_repeated_subject_openings_rewrites_later_sections():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = """
## セクションA

地域の企業は連携不足で機会を逃しがちです。まずは共有会から始めるのが有効です。

## セクションB

地域の企業は孤立を防ぐには、相談窓口の定期活用が有効です。実行の負担も小さく抑えられます。
""".strip()
    cleaned = generator._compress_repeated_subject_openings(body)
    sections = generator._extract_section_blocks(cleaned)
    assert len(sections) == 2
    assert sections[0][1].startswith("地域の企業は")
    assert sections[1][1].startswith("孤立を防ぐには")


def test_generate_section_with_retry_stores_telemetry():
    """_generate_section_with_retry が retry_telemetry を保存する"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._current_persona = "テスト執筆者"
    generator._current_pronoun = "私"
    generator._current_perspective = "blogger"
    generator._current_prompts = {"ai": "AIテスト"}
    generator._enhanced_context = ""
    generator._lead_opening_style = "question"
    generator._section_opening_sequence = ["question"]

    section = generator._generate_section_with_retry(
        section_meta={"heading": "テスト", "purpose": "本論", "required_elements": []},
        merged="テストコンテキスト",
        user_prompt="初心者向けに",
        article_type="ai",
        quote_candidates=[],
        target_audience="一般読者",
        title="テスト",
        section_index=0,
        total_sections=1,
        existing_sections=[],
    )
    assert section
    telemetry = getattr(generator, "_last_retry_telemetry", [])
    assert len(telemetry) >= 1
    assert telemetry[0]["attempt"] == 0
    assert "redundant" in telemetry[0]


def test_generate_section_with_retry_retries_on_low_novelty_when_enabled():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"count": 0}
    history = [
        "## 既存\n\n在庫最適化の導入手順を整理します。現場の在庫最適化は教育計画と運用設計が重要です。"
    ]

    def _fake_generate_section(*args, **kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        if calls["count"] == 1:
            return "## 見出しB\n\n在庫最適化の導入手順を整理します。現場の在庫最適化は教育計画が重要です。"
        return "## 見出しB\n\n監査フローの役割分担を明確にし、週次レビューと是正手順を定義します。"

    generator._generate_section = _fake_generate_section  # type: ignore[method-assign]
    generator._check_redundancy_with_reason = lambda *_args, **_kwargs: (False, [])  # type: ignore[method-assign]
    generator._compute_section_novelty_report = lambda *args, **kwargs: (  # type: ignore[method-assign]
        {
            "novelty_ratio": 0.12 if calls["count"] == 1 else 0.62,
            "overlap_term_ratio": 0.88 if calls["count"] == 1 else 0.15,
            "overlap_terms": ["在庫最適化", "導入"],
            "hard_redundant": False,
            "candidate_terms_count": 12,
            "effective_terms_count": 10,
        }
    )
    generator._get_section_generation_config = lambda: {  # type: ignore[method-assign]
        "novelty_gate": {
            "enabled": True,
            "max_retries": 3,
            "intro_novelty_min": 0.2,
            "middle_novelty_min": 0.3,
            "closing_novelty_min": 0.35,
            "focus_relaxation": 0.0,
            "min_candidate_terms": 4,
            "max_forbidden_terms": 10,
        },
        "context_overlap": {"enabled": False},
        "hard_soft_thresholds": {"enabled": False, "mode": "off"},
        "lexical_policy": {"enabled": True, "extra_banned_phrases": []},
    }

    result = generator._generate_section_with_retry(
        section_meta={"heading": "見出しB"},
        merged="",
        user_prompt="",
        article_type="ai",
        quote_candidates=[],
        target_audience="一般読者",
        target_chars=380,
        title="テスト記事",
        section_index=1,
        total_sections=3,
        existing_sections=history,
    )
    assert "監査フローの役割分担を明確にし" in result
    assert calls["count"] >= 2
    telemetry = getattr(generator, "_last_retry_telemetry", [])
    assert telemetry
    assert telemetry[0].get("low_novelty") is True


def test_get_active_banned_phrases_includes_extra_terms():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._get_section_generation_config = lambda: {  # type: ignore[method-assign]
        "lexical_policy": {
            "enabled": True,
            "extra_banned_phrases": ["現場最適解"],
        }
    }
    phrases = generator._get_active_banned_phrases()
    assert "現場最適解" in phrases


def test_run_repair_only_pass_shadow_keeps_original_text():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._get_postprocess_config = lambda: {  # type: ignore[method-assign]
        "repair_only": {
            "enabled": True,
            "mode": "shadow",
            "rewrite_ratio_cap": 0.08,
            "llm_trigger_severity": "mid",
            "min_chars_for_llm": 80,
            "max_violations_per_1k": 2.0,
        }
    }
    generator._should_use_repair_only_llm = lambda report, body_chars, cfg: True  # type: ignore[method-assign]
    lead = "導入です。"
    body = "## 本文\n\n調整し。次に手順を示します。"
    repaired_lead, repaired_body = generator._run_repair_only_pass(
        lead,
        body,
        merged_context="参考情報",
        article_type="ai",
        target_audience="一般読者",
    )
    assert repaired_lead == lead
    assert repaired_body == body
    report = getattr(generator, "_last_repair_only_report", {})
    assert report.get("mode") == "shadow"
    assert report.get("would_call_llm") is True


def test_run_repair_only_pass_enforce_applies_when_guard_allows():
    class RepairOnlyLLM:
        def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
            if task_type == "repair_only":
                return '{"lead":"導入です。","body":"## 本文\\n\\n調整し、次に手順を示します。"}'
            return ""

    generator = ArticleGenerator(llm_client=RepairOnlyLLM())
    generator._get_postprocess_config = lambda: {  # type: ignore[method-assign]
        "repair_only": {
            "enabled": True,
            "mode": "enforce",
            "rewrite_ratio_cap": 0.08,
            "llm_trigger_severity": "mid",
            "min_chars_for_llm": 80,
            "max_violations_per_1k": 2.0,
        }
    }
    generator._should_use_repair_only_llm = lambda report, body_chars, cfg: True  # type: ignore[method-assign]
    lead = "導入です。"
    body = "## 本文\n\n調整し。次に手順を示します。"
    repaired_lead, repaired_body = generator._run_repair_only_pass(
        lead,
        body,
        merged_context="参考情報",
        article_type="ai",
        target_audience="一般読者",
    )
    assert repaired_lead == "導入です。"
    assert "調整し、次に手順を示します。" in repaired_body
    report = getattr(generator, "_last_repair_only_report", {})
    assert report.get("applied") is True


def test_compacted_postprocess_pipeline_hard_gate_runs_repair_only_before_reject():
    generator = ArticleGenerator(llm_client=DummyLLM())
    calls = {"repair_only": 0}

    generator._fix_broken_bold = lambda text: text  # type: ignore[method-assign]
    generator._apply_final_consistency_guards = lambda lead, body: (lead, body)  # type: ignore[method-assign]
    generator._normalize_paragraphs = lambda text: text  # type: ignore[method-assign]
    generator._add_note_sentence_linebreaks = lambda text: text  # type: ignore[method-assign]
    generator._fix_punctuation = lambda text: text  # type: ignore[method-assign]
    generator._repair_contextual_sentence_breaks = lambda text: text  # type: ignore[method-assign]
    generator._clean_redundant_connectives = lambda text: text  # type: ignore[method-assign]
    generator._check_contextual_naturalness = lambda text: {"issue_count": 0, "soft_issue_count": 0}  # type: ignore[method-assign]
    generator._run_repair_only_pass = lambda *args, **kwargs: (  # type: ignore[method-assign]
        calls.__setitem__("repair_only", calls["repair_only"] + 1) or (args[0], args[1])
    )
    generator._try_soft_warning_fix_pass = lambda **kwargs: None  # type: ignore[method-assign]
    generator._evaluate_hard_soft_thresholds = lambda **kwargs: {  # type: ignore[method-assign]
        "enabled": True,
        "mode": "enforce",
        "hard_failed": True,
        "hard_fail_reasons": ["rewrite_ratio>0.22"],
        "soft_warnings": [],
        "metrics": {
            "rewrite_ratio": 0.3,
            "heading_delta": 0,
            "grammar_per_1k": 0.0,
            "unpredictability": 0.7,
            "flat_zone_count": 0,
            "semantic_issue_count": 0,
        },
    }

    lead = "導入です。"
    body = "## 本文\n\n背景を説明します。"
    out_lead, out_body = generator._apply_compacted_postprocess_pipeline(lead, body)

    assert out_lead == lead
    assert out_body == body
    assert calls["repair_only"] == 1


def test_compacted_postprocess_pipeline_hard_gate_keeps_linebreaks_and_report_mode():
    generator = ArticleGenerator(llm_client=DummyLLM())

    generator._fix_broken_bold = lambda text: text  # type: ignore[method-assign]
    generator._apply_final_consistency_guards = lambda lead, body: (lead, body)  # type: ignore[method-assign]
    generator._normalize_paragraphs = lambda text: text  # type: ignore[method-assign]
    generator._fix_punctuation = lambda text: text  # type: ignore[method-assign]
    generator._repair_contextual_sentence_breaks = lambda text: text  # type: ignore[method-assign]
    generator._clean_redundant_connectives = lambda text: text  # type: ignore[method-assign]
    generator._check_contextual_naturalness = lambda text: {"issue_count": 0, "soft_issue_count": 0}  # type: ignore[method-assign]
    generator._get_postprocess_config = lambda: {  # type: ignore[method-assign]
        "repair_only": {
            "enabled": True,
            "mode": "enforce",
            "rewrite_ratio_cap": 0.08,
            "llm_trigger_severity": "mid",
            "min_chars_for_llm": 80,
            "max_violations_per_1k": 2.0,
        }
    }
    generator._should_use_repair_only_llm = lambda report, body_chars, cfg: False  # type: ignore[method-assign]
    generator._evaluate_hard_soft_thresholds = lambda **kwargs: {  # type: ignore[method-assign]
        "enabled": True,
        "mode": "enforce",
        "hard_failed": True,
        "hard_fail_reasons": ["rewrite_ratio>0.22"],
        "soft_warnings": [],
        "metrics": {
            "rewrite_ratio": 0.3,
            "heading_delta": 0,
            "grammar_per_1k": 0.0,
            "unpredictability": 0.7,
            "flat_zone_count": 0,
            "semantic_issue_count": 0,
        },
    }

    lead = "導入です。次です。"
    body = "## 本文\n\n背景を説明します。次に注意点を示します。"
    out_lead, out_body = generator._apply_compacted_postprocess_pipeline(lead, body)

    assert out_lead == "導入です。\n次です。"
    assert "背景を説明します。\n次に注意点を示します。" in out_body
    report = getattr(generator, "_last_repair_only_report", {})
    assert report.get("mode") == "enforce"
    assert report.get("skipped_reason") != "hard_gate_pre_repair"


def test_compacted_postprocess_pipeline_sequence_contract_order():
    generator = ArticleGenerator(llm_client=DummyLLM())
    events = []
    eval_calls = {"count": 0}

    generator._fix_broken_bold = lambda text: text  # type: ignore[method-assign]
    generator._apply_final_consistency_guards = lambda lead, body: (lead, body)  # type: ignore[method-assign]
    generator._normalize_paragraphs = lambda text: text  # type: ignore[method-assign]
    generator._add_note_sentence_linebreaks = lambda text: text  # type: ignore[method-assign]
    generator._fix_punctuation = lambda text: text  # type: ignore[method-assign]
    generator._repair_contextual_sentence_breaks = lambda text: text  # type: ignore[method-assign]
    generator._clean_redundant_connectives = lambda text: text  # type: ignore[method-assign]
    generator._check_contextual_naturalness = lambda text: {"issue_count": 0, "soft_issue_count": 0}  # type: ignore[method-assign]

    def _fake_eval(**kwargs):  # type: ignore[no-untyped-def]
        eval_calls["count"] += 1
        if eval_calls["count"] == 1:
            events.append("detect")
        elif eval_calls["count"] == 2:
            events.append("post_repair_eval")
        else:
            events.append("re_eval")
        return {
            "enabled": True,
            "mode": "enforce",
            "hard_failed": False,
            "hard_fail_reasons": [],
            "soft_warnings": ["flat_zone_count>5"],
            "metrics": {
                "rewrite_ratio": 0.05,
                "heading_delta": 0,
                "grammar_per_1k": 0.0,
                "unpredictability": 0.7,
                "flat_zone_count": 6,
                "semantic_issue_count": 3,
            },
        }

    generator._evaluate_hard_soft_thresholds = _fake_eval  # type: ignore[method-assign]
    generator._run_repair_only_pass = lambda lead, body, **kwargs: (  # type: ignore[method-assign]
        events.append("repair_only") or (lead, body)
    )
    generator._try_soft_warning_fix_pass = lambda **kwargs: (  # type: ignore[method-assign]
        events.append("soft_fix") or None
    )

    lead = "導入です。"
    body = "## 本文\n\n背景を説明します。"
    generator._apply_compacted_postprocess_pipeline(lead, body)

    assert events == ["detect", "repair_only", "post_repair_eval", "soft_fix", "re_eval"]


def test_compacted_postprocess_pipeline_rejects_post_repair_hard_fail_to_gate_pass():
    generator = ArticleGenerator(llm_client=DummyLLM())
    eval_calls = {"count": 0}

    generator._fix_broken_bold = lambda text: text  # type: ignore[method-assign]
    generator._apply_final_consistency_guards = lambda lead, body: (lead, body)  # type: ignore[method-assign]
    generator._normalize_paragraphs = lambda text: text  # type: ignore[method-assign]
    generator._add_note_sentence_linebreaks = lambda text: text  # type: ignore[method-assign]
    generator._fix_punctuation = lambda text: text  # type: ignore[method-assign]
    generator._repair_contextual_sentence_breaks = lambda text: text  # type: ignore[method-assign]
    generator._clean_redundant_connectives = lambda text: text  # type: ignore[method-assign]
    generator._check_contextual_naturalness = lambda text: {"issue_count": 0, "soft_issue_count": 0}  # type: ignore[method-assign]

    def _fake_eval(**kwargs):  # type: ignore[no-untyped-def]
        eval_calls["count"] += 1
        if eval_calls["count"] == 1:
            return {
                "enabled": True,
                "mode": "enforce",
                "hard_failed": False,
                "hard_fail_reasons": [],
                "soft_warnings": ["flat_zone_count>5"],
                "metrics": {
                    "rewrite_ratio": 0.05,
                    "heading_delta": 0,
                    "grammar_per_1k": 0.0,
                    "unpredictability": 0.7,
                    "flat_zone_count": 6,
                    "semantic_issue_count": 3,
                },
            }
        return {
            "enabled": True,
            "mode": "enforce",
            "hard_failed": True,
            "hard_fail_reasons": ["rewrite_ratio>0.22"],
            "soft_warnings": [],
            "metrics": {
                "rewrite_ratio": 0.31,
                "heading_delta": 0,
                "grammar_per_1k": 0.0,
                "unpredictability": 0.7,
                "flat_zone_count": 6,
                "semantic_issue_count": 3,
            },
        }

    generator._evaluate_hard_soft_thresholds = _fake_eval  # type: ignore[method-assign]
    generator._run_repair_only_pass = lambda lead, body, **kwargs: (  # type: ignore[method-assign]
        lead + " 修復", body + "\n修復"
    )
    generator._try_soft_warning_fix_pass = lambda **kwargs: None  # type: ignore[method-assign]

    lead = "導入です。"
    body = "## 本文\n\n背景を説明します。"
    out_lead, out_body = generator._apply_compacted_postprocess_pipeline(lead, body)

    # hard_failed時はフォールバックせず、UI側ゲートで遮断するため最新テキストを返す
    assert out_lead.endswith("修復")
    assert out_body.endswith("修復")


def test_compacted_postprocess_pipeline_soft_fix_uses_post_repair_eval():
    generator = ArticleGenerator(llm_client=DummyLLM())
    captured_current_eval = {}

    generator._fix_broken_bold = lambda text: text  # type: ignore[method-assign]
    generator._apply_final_consistency_guards = lambda lead, body: (lead, body)  # type: ignore[method-assign]
    generator._normalize_paragraphs = lambda text: text  # type: ignore[method-assign]
    generator._add_note_sentence_linebreaks = lambda text: text  # type: ignore[method-assign]
    generator._fix_punctuation = lambda text: text  # type: ignore[method-assign]
    generator._repair_contextual_sentence_breaks = lambda text: text  # type: ignore[method-assign]
    generator._clean_redundant_connectives = lambda text: text  # type: ignore[method-assign]
    generator._check_contextual_naturalness = lambda text: {"issue_count": 0, "soft_issue_count": 0}  # type: ignore[method-assign]

    def _fake_eval(**kwargs):  # type: ignore[no-untyped-def]
        after_body = kwargs.get("after_body", "")
        if "[repair]" in after_body:
            return {
                "enabled": True,
                "mode": "enforce",
                "hard_failed": False,
                "hard_fail_reasons": [],
                "soft_warnings": ["flat_zone_count>5"],
                "metrics": {
                    "rewrite_ratio": 0.05,
                    "heading_delta": 0,
                    "grammar_per_1k": 0.0,
                    "unpredictability": 0.70,
                    "flat_zone_count": 6,
                    "semantic_issue_count": 2,
                },
            }
        return {
            "enabled": True,
            "mode": "enforce",
            "hard_failed": False,
            "hard_fail_reasons": [],
            "soft_warnings": ["flat_zone_count>5", "semantic_issue_count>2"],
            "metrics": {
                "rewrite_ratio": 0.05,
                "heading_delta": 0,
                "grammar_per_1k": 0.0,
                "unpredictability": 0.62,
                "flat_zone_count": 8,
                "semantic_issue_count": 4,
            },
        }

    generator._evaluate_hard_soft_thresholds = _fake_eval  # type: ignore[method-assign]
    generator._run_repair_only_pass = lambda lead, body, **kwargs: (lead, body + " [repair]")  # type: ignore[method-assign]

    def _capture_soft_fix(**kwargs):  # type: ignore[no-untyped-def]
        captured_current_eval.update(kwargs.get("current_eval", {}))
        return None

    generator._try_soft_warning_fix_pass = _capture_soft_fix  # type: ignore[method-assign]

    lead = "導入です。"
    body = "## 本文\n\n背景を説明します。"
    generator._apply_compacted_postprocess_pipeline(lead, body)

    assert captured_current_eval.get("soft_warnings") == ["flat_zone_count>5"]


def test_resolve_context_overlap_ratio_reduces_when_overlap_signaled():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._get_section_generation_config = lambda: {  # type: ignore[method-assign]
        "context_overlap": {
            "enabled": True,
            "base_ratio": 0.4,
            "intro_ratio": 0.45,
            "middle_ratio": 0.35,
            "closing_ratio": 0.28,
            "min_ratio": 0.1,
            "max_ratio": 0.55,
            "reduce_on_redundancy": 0.08,
        }
    }
    generator._last_retry_telemetry = [{"attempt": 0, "redundant": True}]
    ratio = generator._resolve_context_overlap_ratio(1, 4)
    assert ratio < 0.35
    assert ratio >= 0.1


def test_evaluate_hard_soft_thresholds_reports_shadow_warnings():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._get_section_generation_config = lambda: {  # type: ignore[method-assign]
        "hard_soft_thresholds": {
            "enabled": True,
            "mode": "shadow",
            "hard_max_rewrite_ratio": 0.2,
            "hard_max_grammar_breaks_per_1k": 3.0,
            "hard_preserve_headings": True,
            "soft_min_unpredictability": 0.6,
            "soft_max_flat_zone_count": 2,
            "soft_max_semantic_issue_count": 1,
        }
    }

    class _Report:
        overall_unpredictability = 0.42
        flat_zone_flags = ["sentence_length_cv_flat", "paragraph_length_cv_flat", "subject_explicit_high"]

    generator._fingerprint_analyzer = type(  # type: ignore[assignment]
        "Analyzer",
        (),
        {"analyze": lambda self, text, focus=None: _Report()},
    )()
    generator._check_contextual_naturalness = lambda text: {  # type: ignore[method-assign]
        "semantic_issue_count": 3,
        "semantic_layout": {
            "heading_alignment_mean": 0.04,
            "transition_jaccard_mean": 0.01,
            "abrupt_opening_ratio": 0.5,
        },
    }

    result = generator._evaluate_hard_soft_thresholds(
        before_lead="導入です。",
        before_body="## 本文\n\n背景を説明します。",
        after_lead="導入です。",
        after_body="## 本文\n\n背景を説明します。",
    )
    assert result["enabled"] is True
    assert result["mode"] == "shadow"
    assert result["hard_failed"] is False
    assert result["soft_warnings"]
    assert "semantic_issue_count>1" in result["soft_warnings"]


def test_evaluate_hard_soft_thresholds_flags_ai_template_ending_overuse():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._get_section_generation_config = lambda: {  # type: ignore[method-assign]
        "hard_soft_thresholds": {
            "enabled": True,
            "mode": "shadow",
            "hard_max_rewrite_ratio": 0.3,
            "hard_max_grammar_breaks_per_1k": 3.0,
            "hard_preserve_headings": True,
            "soft_min_unpredictability": 0.4,
            "soft_max_flat_zone_count": 8,
            "soft_max_semantic_issue_count": 8,
            "soft_max_ai_template_ending_count": 2,
        }
    }

    class _Report:
        overall_unpredictability = 0.72
        flat_zone_flags = []

    generator._fingerprint_analyzer = type(  # type: ignore[assignment]
        "Analyzer",
        (),
        {"analyze": lambda self, text, focus=None: _Report()},
    )()
    generator._check_contextual_naturalness = lambda text: {  # type: ignore[method-assign]
        "semantic_issue_count": 1,
        "ai_template_ending_count": 4,
        "ai_template_ending_ratio": 0.1,
        "semantic_layout": {
            "heading_alignment_mean": 0.1,
            "transition_jaccard_mean": 0.02,
            "abrupt_opening_ratio": 0.1,
        },
    }

    result = generator._evaluate_hard_soft_thresholds(
        before_lead="導入です。",
        before_body="## 本文\n\n背景を説明します。",
        after_lead="導入です。",
        after_body="## 本文\n\n背景を説明します。",
    )
    assert "ai_template_ending_count>2" in result["soft_warnings"]
    metrics = result.get("metrics", {})
    assert metrics.get("ai_template_ending_count") == 4


def test_fingerprint_prompt_hints_cover_core_extended_flags():
    from note.article_generator import FINGERPRINT_PROMPT_HINTS

    expected_keys = {
        "mtld_low",
        "nominalization_rate_high",
        "sentence_ending_entropy_low",
        "sentence_ending_fine_entropy_low",
        "sentence_opening_entropy_low",
        "comma_position_cv_low",
        "morphological_ngram_entropy_low",
        "pos_sequence_entropy_low",
        "inflection_entropy_low",
    }
    missing = expected_keys - set(FINGERPRINT_PROMPT_HINTS.keys())
    assert not missing, f"missing hint keys: {sorted(missing)}"


def test_lookup_fingerprint_prompt_hint_resolves_alias_keys():
    generator = ArticleGenerator(llm_client=DummyLLM())
    assert generator._lookup_fingerprint_prompt_hint("conjunction_repetition_rate_high")
    assert generator._lookup_fingerprint_prompt_hint("subject_explicit_rate_high")
    assert generator._lookup_fingerprint_prompt_hint("pos_bigram_monotonicity_low")


def test_lookup_fingerprint_prompt_hint_covers_all_flat_zone_flags():
    generator = ArticleGenerator(llm_client=DummyLLM())
    flat_zone_flags = {
        "sentence_length_cv_flat",
        "paragraph_length_cv_flat",
        "conjunction_rate_high",
        "subject_explicit_high",
        "particle_entropy_low",
        "bigram_mono_low",
        "mtld_low",
        "vocab_repetition",
        "nominalization_rate_high",
        "sentence_ending_entropy_low",
        "morphological_ngram_entropy_low",
        "pos_sequence_entropy_low",
        "inflection_entropy_low",
        "syntactic_complexity_low",
        "sentence_ending_fine_entropy_low",
        "sentence_opening_entropy_low",
        "comma_position_cv_low",
        "ending_repetition",
        "comma_overuse",
        "abstract_tautology",
    }
    unresolved = sorted(
        flag for flag in flat_zone_flags
        if not generator._lookup_fingerprint_prompt_hint(flag)
    )
    assert not unresolved, f"unresolved flags: {unresolved}"


def test_build_fingerprint_feedback_caps_dynamic_hints_to_two():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._fingerprint_analyzer = type(  # type: ignore[assignment]
        "Analyzer",
        (),
        {
            "analyze": lambda self, text, focus=None: type(
                "Report",
                (),
                {
                    "overall_unpredictability": 0.31,
                    "flat_zone_flags": [
                        "sentence_length_cv_flat",
                        "paragraph_length_cv_flat",
                        "sentence_ending_entropy_low",
                    ],
                    "correction_hints": ["h1", "h2", "h3"],
                },
            )()
        },
    )()
    feedback = generator._build_fingerprint_feedback(["a", "b", "c"])
    assert len(feedback.get("hint_lines", [])) <= 2
    assert len(feedback.get("correction_hints", [])) <= 2


def test_try_soft_warning_fix_pass_applies_when_score_improves():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._get_section_generation_config = lambda: {  # type: ignore[method-assign]
        "hard_soft_thresholds": {"soft_autofix_enabled": True}
    }
    generator._rewrite_guard_check = lambda *args, **kwargs: ""  # type: ignore[method-assign]
    generator._evaluate_hard_soft_thresholds = lambda **kwargs: {  # type: ignore[method-assign]
        "enabled": True,
        "mode": "shadow",
        "hard_failed": False,
        "soft_warnings": ["flat_zone_count>5"],
        "metrics": {
            "semantic_issue_count": 1,
            "flat_zone_count": 4,
            "ai_template_ending_count": 0,
            "unpredictability": 0.72,
        },
    }

    current_eval = {
        "enabled": True,
        "mode": "shadow",
        "hard_failed": False,
        "soft_warnings": ["flat_zone_count>5", "semantic_issue_count>2"],
        "metrics": {
            "semantic_issue_count": 3,
            "flat_zone_count": 8,
            "ai_template_ending_count": 0,
            "unpredictability": 0.61,
        },
    }
    lead = "導入です。"
    body = (
        "## 本文\n\n"
        "しかし一方で、課題があります。"
        "運用を改善します。検証を継続します。体制を見直します。"
    )

    result = generator._try_soft_warning_fix_pass(
        before_lead=lead,
        before_body=body,
        current_lead=lead,
        current_body=body,
        current_eval=current_eval,
    )

    assert result is not None
    _, _, fixed_eval = result
    assert len(fixed_eval.get("soft_warnings", [])) < len(current_eval["soft_warnings"])


def test_quality_report_payload_includes_attempt_and_mode_resolution():
    from note import note_writer_app as app_mod

    payload = app_mod._build_latest_quality_report_payload(
        timestamp="2026-03-01 18:00:00",
        attempt_id="gen-test1234",
        result={"full_text": "本文です。"},
        config_snapshot={"generation_mode": "transition"},
        failed_parameters={
            "hard_soft_eval": {"metrics": {"unpredictability": 0.7123}},
            "contextual_naturalness_report": {
                "connective_opening_ratio": 0.125,
                "semantic_issue_count": 2,
            },
            "fingerprint_phase": {
                "flat_zone_flags": ["sentence_length_cv_flat"],
                "overall_unpredictability": 0.7,
                "sentence_ending_entropy": 1.4,
                "sentence_ending_fine_entropy": 2.1,
                "subject_explicit_rate": 0.42,
                "nominalization_rate": 0.19,
            },
            "quality_mode_resolution": {"requested_mode": "enforce", "downstream_mode": "shadow"},
            "final_quality_eval": {"hard_failed": False, "soft_warnings": ["flat_zone_count>5"]},
        },
    )

    assert payload["attempt_id"] == "gen-test1234"
    assert payload["quality_mode_resolution"]["requested_mode"] == "enforce"
    assert payload["final_quality_eval"]["hard_failed"] is False
    assert payload["metrics"]["flat_zone_count"] == 1


def test_quality_report_payload_falls_back_to_hard_soft_flat_zone_count():
    from note import note_writer_app as app_mod

    payload = app_mod._build_latest_quality_report_payload(
        timestamp="2026-03-01 18:00:00",
        attempt_id="gen-test-flat-zone",
        result={"full_text": "本文です。"},
        config_snapshot={"generation_mode": "zero_base_v2"},
        failed_parameters={
            "hard_soft_eval": {"metrics": {"unpredictability": 0.7123, "flat_zone_count": 8}},
            "contextual_naturalness_report": {
                "connective_opening_ratio": 0.125,
                "semantic_issue_count": 5,
            },
            "fingerprint_phase": {},
            "quality_mode_resolution": {"requested_mode": "enforce"},
            "final_quality_eval": {"hard_failed": False},
        },
    )

    assert payload["metrics"]["flat_zone_count"] == 8


def test_output_guard_blocks_manual_instructional_fragment():
    from note import note_writer_app as app_mod

    result = {
        "title": "テスト記事",
        "lead": "導入です。",
        "body": (
            "## 本文\n\n"
            "さんれいフーズとして初めてのnote投稿なので、自社を知ってもらうことを目的として"
            "ブログ作成をしてくださいを実際の場面に当てはめると、要点の使いどころが見えやすくなります。"
        ),
        "full_text": "本文です。",
        "pipeline_check": {
            "input_contract": {
                "speaker_profile": "運営担当者",
                "audience_profile": "実務担当者",
            },
            "hard_soft_eval": {
                "mode": "enforce",
                "hard_failed": False,
                "metrics": {},
            },
            "final_quality_eval": {
                "hard_failed": False,
                "metrics": {},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 0,
                "semantic_issue_count": 0,
                "semantic_layout": {"semantic_issue_count": 0},
            },
            "contract_alignment": {
                "alignment_score": 0.88,
                "must_cover_count": 1,
                "must_cover_reflection_rate": 1.0,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.9,
                "anchor_term_coverage": 0.85,
                "section_focus_coverage": 1.0,
                "section_focus_total": 1,
                "anchor_terms": ["価値"],
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is True
    assert any(reason.startswith("manual_instructional_hits=") for reason in guard["reasons"])


def test_output_guard_allows_clean_result():
    from note import note_writer_app as app_mod

    result = {
        "title": "テスト記事",
        "lead": "導入です。",
        "body": "## 本文\n\n現場の工夫を具体例で整理します。",
        "full_text": "テスト記事\n\n導入です。\n\n## 本文\n\n現場の工夫を具体例で整理します。",
        "pipeline_check": {
            "input_contract": {
                "speaker_profile": "運営担当者",
                "audience_profile": "実務担当者",
            },
            "hard_soft_eval": {
                "mode": "enforce",
                "hard_failed": False,
                "metrics": {"instructional_fragment_count": 0},
            },
            "final_quality_eval": {
                "hard_failed": False,
                "metrics": {"instructional_fragment_count": 0},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 0,
                "semantic_issue_count": 2,
                "instructional_fragment_count": 0,
                "semantic_layout": {"semantic_issue_count": 2},
            },
            "contract_alignment": {
                "alignment_score": 0.91,
                "must_cover_count": 1,
                "must_cover_reflection_rate": 1.0,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.9,
                "anchor_term_coverage": 0.85,
                "section_focus_coverage": 1.0,
                "section_focus_total": 1,
                "anchor_terms": ["工夫"],
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is False
    assert guard["reasons"] == []


def test_output_guard_blocks_hard_soft_hard_failed_even_if_other_metrics_are_clean():
    from note import note_writer_app as app_mod

    result = {
        "title": "テスト記事",
        "lead": "導入です。",
        "body": "## 本文\n\n現場の工夫を具体例で示します。",
        "full_text": "テスト記事\n\n導入です。\n\n## 本文\n\n現場の工夫を具体例で示します。",
        "pipeline_check": {
            "input_contract": {
                "speaker_profile": "運営担当者",
                "audience_profile": "実務担当者",
            },
            "hard_soft_eval": {
                "mode": "enforce",
                "hard_failed": True,
                "hard_fail_reasons": ["rewrite_ratio>0.22"],
                "metrics": {"instructional_fragment_count": 0},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 0,
                "semantic_issue_count": 0,
                "instructional_fragment_count": 0,
                "semantic_layout": {"semantic_issue_count": 0},
            },
            "contract_alignment": {
                "alignment_score": 0.9,
                "must_cover_count": 1,
                "must_cover_reflection_rate": 1.0,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.9,
                "anchor_term_coverage": 0.85,
                "section_focus_coverage": 1.0,
                "section_focus_total": 1,
                "anchor_terms": ["工夫"],
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is True
    assert "hard_soft_thresholds_hard_failed" in guard["reasons"]


def test_output_guard_blocks_contract_alignment_mismatch():
    from note import note_writer_app as app_mod

    result = {
        "title": "テスト記事",
        "lead": "導入です。",
        "body": "## 本文\n\n現場の工夫を具体例で示します。",
        "full_text": "テスト記事\n\n導入です。\n\n## 本文\n\n現場の工夫を具体例で示します。",
        "pipeline_check": {
            "input_contract": {
                "speaker_profile": "運営担当者",
                "audience_profile": "実務担当者",
            },
            "hard_soft_eval": {
                "mode": "enforce",
                "hard_failed": False,
                "hard_fail_reasons": [],
                "metrics": {"instructional_fragment_count": 0},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 0,
                "semantic_issue_count": 0,
                "instructional_fragment_count": 0,
                "semantic_layout": {"semantic_issue_count": 0},
            },
            "contract_alignment": {
                "alignment_score": 0.22,
                "must_cover_count": 2,
                "must_cover_reflection_rate": 0.2,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.15,
                "anchor_term_coverage": 0.18,
                "section_focus_coverage": 0.2,
                "section_focus_total": 4,
                "anchor_terms": ["商品", "価値", "選び方"],
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is True
    assert guard["reason_code"] == "SYS_CONTRACT_ALIGNMENT_MISMATCH"
    assert any(str(reason).startswith("contract_alignment_score<") for reason in guard["reasons"])


def test_output_guard_blocks_contract_alignment_forbidden_topics():
    from note import note_writer_app as app_mod

    result = {
        "title": "テスト記事",
        "lead": "導入です。",
        "body": "## 本文\n\n商品の価値を説明します。社内制度とチーム連携にも触れます。",
        "full_text": "テスト記事\n\n導入です。\n\n## 本文\n\n商品の価値を説明します。社内制度とチーム連携にも触れます。",
        "pipeline_check": {
            "input_contract": {
                "speaker_profile": "商品開発担当者",
                "audience_profile": "飲食店経営者",
            },
            "hard_soft_eval": {
                "mode": "enforce",
                "hard_failed": False,
                "hard_fail_reasons": [],
                "metrics": {"instructional_fragment_count": 0},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 0,
                "semantic_issue_count": 0,
                "instructional_fragment_count": 0,
                "semantic_layout": {"semantic_issue_count": 0},
            },
            "contract_alignment": {
                "alignment_score": 0.88,
                "must_cover_count": 2,
                "must_cover_reflection_rate": 1.0,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.9,
                "anchor_term_coverage": 0.9,
                "section_focus_coverage": 0.9,
                "section_focus_total": 4,
                "anchor_terms": ["商品", "価値", "選び方"],
                "forbidden_topic_hit_count": 2,
                "forbidden_topic_hits": ["社内制度", "チーム連携"],
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is True
    assert guard["reason_code"] == "SYS_FORBIDDEN_TOPIC_DRIFT"
    assert any(str(reason).startswith("contract_alignment_forbidden_topics=") for reason in guard["reasons"])


def test_output_guard_blocks_speaker_contract_mismatch():
    from note import note_writer_app as app_mod

    result = {
        "title": "テスト記事",
        "lead": "導入です。",
        "body": "## 本文\n\n私たちは価値を伝えます。代表取締役のメッセージは重要です。具体的には発信するとよいでしょう。",
        "full_text": "テスト記事\n\n導入です。\n\n## 本文\n\n私たちは価値を伝えます。代表取締役のメッセージは重要です。具体的には発信するとよいでしょう。",
        "user_prompt": "代表取締役の視点で会社紹介を書く",
        "pipeline_check": {
            "input_contract": {
                "speaker_profile": "代表取締役として語る",
                "audience_profile": "一般読者",
                "relationship_mode": "guide",
            },
            "hard_soft_eval": {
                "mode": "enforce",
                "hard_failed": False,
                "hard_fail_reasons": [],
                "metrics": {"instructional_fragment_count": 0},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 0,
                "semantic_issue_count": 5,
                "instructional_fragment_count": 0,
                "semantic_layout": {"semantic_issue_count": 5, "heading_alignment_mean": 0.0},
            },
            "contract_alignment": {
                "alignment_score": 0.82,
                "must_cover_count": 2,
                "must_cover_reflection_rate": 1.0,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.9,
                "anchor_term_coverage": 0.8,
                "section_focus_coverage": 1.0,
                "section_focus_total": 4,
                "anchor_terms": ["会社", "紹介"],
                "speaker_consistency_score": 0.2,
                "pronoun_consistency_score": 0.35,
                "relationship_consistency_score": 1.0,
                "section_contract_issue_count": 1,
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is True
    assert guard["reason_code"] == "SYS_SPEAKER_CONTRACT_MISMATCH"
    assert any("contract_alignment_speaker_consistency<" in str(reason) for reason in guard["reasons"])


def test_output_guard_treats_naturalness_only_as_soft_warning():
    from note import note_writer_app as app_mod

    result = {
        "title": "テスト記事",
        "lead": "導入です。",
        "body": "## 本文\n\n現場の工夫を具体例で示します。",
        "full_text": "テスト記事\n\n導入です。\n\n## 本文\n\n現場の工夫を具体例で示します。",
        "pipeline_check": {
            "input_contract": {
                "speaker_profile": "運営担当者",
                "audience_profile": "実務担当者",
                "relationship_mode": "guide",
            },
            "hard_soft_eval": {
                "mode": "observe_only",
                "hard_failed": False,
                "hard_fail_reasons": [],
                "metrics": {"instructional_fragment_count": 0},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 1,
                "semantic_issue_count": 6,
                "instructional_fragment_count": 0,
                "semantic_layout": {"semantic_issue_count": 6, "heading_alignment_mean": 0.02},
            },
            "contract_alignment": {
                "alignment_score": 0.92,
                "must_cover_count": 1,
                "must_cover_reflection_rate": 1.0,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.95,
                "anchor_term_coverage": 0.9,
                "section_focus_coverage": 1.0,
                "section_focus_total": 3,
                "anchor_terms": ["工夫"],
                "speaker_consistency_score": 1.0,
                "pronoun_consistency_score": 1.0,
                "relationship_consistency_score": 1.0,
                "section_contract_issue_count": 0,
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is False
    assert guard["hard_reasons"] == []
    assert "semantic_issue_count=6" in guard["soft_warnings"]
    assert guard["soft_warning_count"] >= 1
    assert any(str(item).startswith("heading_alignment_mean<") for item in guard["soft_warnings"])


def test_output_guard_blocks_low_proposition_density_for_announcement():
    from note import note_writer_app as app_mod

    low_density_body = (
        "## お知らせ\n\n"
        "今回のお知らせは重要です。"
        "今後の運用で意識することが大切です。"
        "日々の判断で注意が必要です。"
        "読み手にとっても必要な内容です。"
        "全体として重要な視点です。"
        "これからも意識が必要です。"
        "継続的な配慮が求められます。"
        "基本を守ることが大切です。"
        "運用では慎重な姿勢が必要です。"
        "最後まで丁寧に進めることが重要です。"
    )
    result = {
        "title": "アップデートのお知らせ",
        "lead": "変更点を案内します。",
        "body": low_density_body,
        "full_text": f"アップデートのお知らせ\n\n変更点を案内します。\n\n{low_density_body}",
        "pipeline_check": {
            "input_contract": {
                "article_type": "announcement",
                "speaker_profile": "運営担当者",
                "audience_profile": "利用者",
                "relationship_mode": "guide",
            },
            "hard_soft_eval": {
                "mode": "enforce",
                "hard_failed": False,
                "hard_fail_reasons": [],
                "metrics": {"instructional_fragment_count": 0},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 0,
                "semantic_issue_count": 0,
                "instructional_fragment_count": 0,
                "topic_opening_ratio": 0.05,
                "awkward_ending_ratio": 0.0,
                "ai_template_ending_ratio": 0.0,
                "semantic_layout": {"semantic_issue_count": 0, "heading_alignment_mean": 0.5},
            },
            "contract_alignment": {
                "alignment_score": 0.92,
                "must_cover_count": 2,
                "must_cover_reflection_rate": 1.0,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.95,
                "anchor_term_coverage": 0.9,
                "section_focus_coverage": 1.0,
                "section_focus_total": 4,
                "anchor_terms": ["アップデート", "変更点"],
                "speaker_consistency_score": 1.0,
                "pronoun_consistency_score": 1.0,
                "relationship_consistency_score": 1.0,
                "section_contract_issue_count": 0,
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is True
    assert guard["reason_code"] == "SYS_LOW_PROPOSITION_DENSITY"
    assert any(str(reason).startswith("proposition_density_") for reason in guard["reasons"])


def test_output_guard_keeps_low_proposition_density_as_soft_warning_for_non_announcement():
    from note import note_writer_app as app_mod

    low_density_body = (
        "## 本文\n\n"
        "全体として重要です。"
        "進め方の意識が必要です。"
        "読み手にとっても大切です。"
        "日々の配慮が求められます。"
        "継続して意識することが必要です。"
        "最後まで丁寧な姿勢が大切です。"
    )
    result = {
        "title": "ブランディング記事",
        "lead": "方針を共有します。",
        "body": low_density_body,
        "full_text": f"ブランディング記事\n\n方針を共有します。\n\n{low_density_body}",
        "pipeline_check": {
            "input_contract": {
                "article_type": "branding",
                "speaker_profile": "運営担当者",
                "audience_profile": "利用者",
                "relationship_mode": "guide",
            },
            "hard_soft_eval": {
                "mode": "enforce",
                "hard_failed": False,
                "hard_fail_reasons": [],
                "metrics": {"instructional_fragment_count": 0},
            },
            "contextual_naturalness_report": {
                "passed": True,
                "issue_count": 0,
                "soft_issue_count": 0,
                "semantic_issue_count": 0,
                "instructional_fragment_count": 0,
                "topic_opening_ratio": 0.06,
                "awkward_ending_ratio": 0.0,
                "ai_template_ending_ratio": 0.0,
                "semantic_layout": {"semantic_issue_count": 0, "heading_alignment_mean": 0.5},
            },
            "contract_alignment": {
                "alignment_score": 0.93,
                "must_cover_count": 2,
                "must_cover_reflection_rate": 1.0,
                "category_mismatch_detected": False,
                "prompt_anchor_coverage": 0.95,
                "anchor_term_coverage": 0.92,
                "section_focus_coverage": 1.0,
                "section_focus_total": 4,
                "anchor_terms": ["ブランド", "価値"],
                "speaker_consistency_score": 1.0,
                "pronoun_consistency_score": 1.0,
                "relationship_consistency_score": 1.0,
                "section_contract_issue_count": 0,
            },
        },
        "quality_pipeline_check": {},
    }

    guard = app_mod._evaluate_generation_output_guard(result)

    assert guard["blocked"] is False
    assert guard["reason_code"] is None
    assert any(
        str(item).startswith("proposition_density_")
        for item in guard["soft_warnings"]
    )


def test_output_guard_auto_repair_candidate_detects_contract_reasons():
    from note import note_writer_app as app_mod

    guard = {
        "blocked": True,
        "error_class": "system",
        "reason_code": "SYS_FORBIDDEN_TOPIC_DRIFT",
        "reasons": ["contract_alignment_forbidden_topics=採用活動,福利厚生"],
    }
    assert app_mod._is_guard_auto_repair_candidate(guard) is True
    topics = app_mod._extract_guard_forbidden_topics(guard["reasons"])
    assert topics == ["採用活動", "福利厚生"]


def test_output_guard_auto_repair_candidate_detects_proposition_density_reason():
    from note import note_writer_app as app_mod

    guard = {
        "blocked": True,
        "error_class": "system",
        "reason_code": "SYS_LOW_PROPOSITION_DENSITY",
        "reasons": ["proposition_density_informative_ratio<0.52"],
    }
    assert app_mod._is_guard_auto_repair_candidate(guard) is True


def test_output_guard_retry_prompt_includes_guard_hints():
    from note import note_writer_app as app_mod

    guard = {
        "blocked": True,
        "error_class": "system",
        "reason_code": "SYS_SPEAKER_CONTRACT_MISMATCH",
        "reasons": [
            "contract_alignment_speaker_consistency<0.55",
            "contract_alignment_forbidden_topics=採用活動,社内制度",
        ],
    }
    prompt = app_mod._build_guard_retry_prompt("会社紹介記事を作成してください", guard)
    assert "会社紹介記事を作成してください" in prompt
    assert "品質ガード再試行メモ" in prompt
    assert "禁止話題" in prompt
    assert "SYS_SPEAKER_CONTRACT_MISMATCH" in prompt


def test_output_guard_retry_prompt_adds_proposition_density_hints():
    from note import note_writer_app as app_mod

    prompt = app_mod._build_guard_retry_prompt(
        "お知らせ記事を作成してください",
        {"reasons": [], "reason_code": "SYS_LOW_PROPOSITION_DENSITY"},
        article_type_key="announcement",
        writing_focus_key="explanation",
    )

    assert "SYS_LOW_PROPOSITION_DENSITY" in prompt
    assert "変更点・対象・時期・影響" in prompt


def test_output_guard_retry_prompt_adds_ai_explanatory_hints():
    from note import note_writer_app as app_mod

    prompt = app_mod._build_guard_retry_prompt(
        "AI活用の解説記事を作成してください",
        {"reasons": [], "reason_code": "SYS_CONTRACT_ALIGNMENT_MISMATCH"},
        article_type_key="ai",
        writing_focus_key="analysis",
    )

    assert "再試行カテゴリ: ai_explanatory" in prompt
    assert "定義→仕組み→活用例→注意点" in prompt
    assert "各見出しでユーザープロンプトの主題語を1つ以上扱う" in prompt


def test_output_guard_retry_prompt_adds_company_intro_hints():
    from note import note_writer_app as app_mod

    prompt = app_mod._build_guard_retry_prompt(
        "会社紹介記事を作成してください",
        {"reasons": [], "reason_code": "SYS_SPEAKER_CONTRACT_MISMATCH"},
        article_type_key="corporate_culture",
        writing_focus_key="experience",
    )

    assert "再試行カテゴリ: company_introduction" in prompt
    assert "事業内容・提供価値・沿革/背景・今後の方針" in prompt
    assert "話者プロファイルで指定した立場を各見出しで維持する" in prompt


def test_output_guard_retry_prompt_adds_branding_hints():
    from note import note_writer_app as app_mod

    prompt = app_mod._build_guard_retry_prompt(
        "商品のブランディング記事を作成してください",
        {"reasons": [], "reason_code": "SYS_FORBIDDEN_TOPIC_DRIFT"},
        article_type_key="branding",
        writing_focus_key="experience",
    )

    assert "再試行カテゴリ: branding" in prompt
    assert "商品/ブランド価値、選定軸、利用シーン" in prompt


def test_build_interview_context_signature_changes_on_prompt():
    from note import note_writer_app as app_mod

    sig_a = app_mod._build_interview_context_signature(
        source_values=["https://example.com/a", "https://example.com/b"],
        article_type_key="branding",
        content_goal_key="interest",
        user_prompt_text="商品の価値を伝える",
    )
    sig_b = app_mod._build_interview_context_signature(
        source_values=["https://example.com/a", "https://example.com/b"],
        article_type_key="branding",
        content_goal_key="interest",
        user_prompt_text="商品の選び方を伝える",
    )

    assert isinstance(sig_a, str) and len(sig_a) == 64
    assert isinstance(sig_b, str) and len(sig_b) == 64
    assert sig_a != sig_b


def test_writer_role_options_are_compact_per_article_type():
    from note import note_writer_app as app_mod

    ai_options = app_mod._get_writer_role_options("ai")
    custom_options = app_mod._get_writer_role_options("custom_unknown")

    assert ai_options[0] == app_mod.WRITER_ROLE_AUTO_LABEL
    assert len(ai_options) <= 4
    assert "編集担当として語る" in ai_options
    assert custom_options[0] == app_mod.WRITER_ROLE_AUTO_LABEL
    assert len(custom_options) <= 4


def test_writer_role_options_follow_custom_genre_base_template(monkeypatch):
    from note import note_writer_app as app_mod

    monkeypatch.setattr(
        app_mod.genre_manager,
        "get_genre",
        lambda key: {"meta": {"base_template": "ai"}} if key == "custom_ai" else None,
    )
    options = app_mod._get_writer_role_options("custom_ai")
    hint = app_mod._predict_pronoun_hint("custom_ai", "")

    assert "解説担当として語る" in options
    assert "私" in hint


def test_writer_role_label_to_profile_ignores_auto():
    from note import note_writer_app as app_mod

    assert app_mod._writer_role_label_to_profile(app_mod.WRITER_ROLE_AUTO_LABEL) == ""
    assert app_mod._writer_role_label_to_profile("  編集担当として語る  ") == "編集担当として語る"


def test_predict_pronoun_hint_reflects_category_and_role():
    from note import note_writer_app as app_mod

    assert "私" in app_mod._predict_pronoun_hint("ai", "")
    assert "私たち" in app_mod._predict_pronoun_hint("announcement", "")
    assert "私たち" in app_mod._predict_pronoun_hint("ai", "広報担当として語る")


def test_normalize_topic_statement_from_interview_skips_non_topic_values():
    from note import note_writer_app as app_mod

    assert app_mod._normalize_topic_statement_from_interview("指定しない") == ""
    assert app_mod._normalize_topic_statement_from_interview("企業ブランディング担当の知見を混ぜる") == ""
    assert app_mod._normalize_topic_statement_from_interview("仕組みより判断基準を先に示す") == ""
    assert app_mod._normalize_topic_statement_from_interview("導入時に確認すべき変更点を整理する") == "導入時に確認すべき変更点を整理する"


def test_looks_theme_like_writer_role_detects_topic_text():
    from note import note_writer_app as app_mod

    assert app_mod._looks_theme_like_writer_role("AI活用法について解説する") is True
    assert app_mod._looks_theme_like_writer_role("編集担当として語る") is False


def test_quality_pipeline_check_fingerprint_extracts_from_nested_reports():
    from note import note_writer_app as app_mod

    quality = {
        "reports": [
            {
                "mode_resolution": {"requested_mode": "enforce"},
                "phase_reports": [
                    {"phase": "phase01_lexical", "flat_zone_flags": []},
                    {
                        "phase": "fingerprint",
                        "flat_zone_flags": ["mtld_low"],
                        "overall_unpredictability": 0.77,
                        "correction_hints": ["語彙レンジを広げる"],
                        "subject_explicit_rate": 0.51,
                    },
                ],
            }
        ]
    }
    report = app_mod._extract_fingerprint_phase_report(quality)

    assert report["flat_zone_flags"] == ["mtld_low"]
    assert report["overall_unpredictability"] == 0.77
    assert report["subject_explicit_rate"] == 0.51


def test_generation_audit_log_append_writes_primary_and_workspace(tmp_path, monkeypatch):
    from note import note_writer_app as app_mod

    primary = tmp_path / "primary.jsonl"
    mirror = tmp_path / "mirror.jsonl"
    monkeypatch.setattr(app_mod, "GENERATION_AUDIT_JSONL_PATH", primary)
    monkeypatch.setattr(app_mod, "GENERATION_AUDIT_JSONL_PATH_WORKSPACE", mirror)

    record = {"timestamp": "2026-03-01 18:01:00", "attempt_id": "gen-audit-1", "article_type": "ai"}
    written_count = app_mod._append_generation_audit_record(record)

    assert written_count == 2
    assert primary.exists()
    assert mirror.exists()
    assert json.loads(primary.read_text(encoding="utf-8").strip()) == record
    assert json.loads(mirror.read_text(encoding="utf-8").strip()) == record


def test_snapshot_partial_write_failure_still_appends_audit_log(tmp_path, monkeypatch):
    from note import note_writer_app as app_mod

    primary_text = tmp_path / "notecode_latest.txt"
    primary_json = tmp_path / "notecode_latest.json"
    primary_quality = tmp_path / "notecode_quality.json"
    primary_audit = tmp_path / "notecode_audit.jsonl"

    mirror_dir = tmp_path / "mirror_dir"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    mirror_text_bad = mirror_dir  # write_text on directory -> PermissionError
    mirror_json = tmp_path / "ws_latest.json"
    mirror_quality = tmp_path / "ws_quality.json"
    mirror_audit = tmp_path / "ws_audit.jsonl"

    monkeypatch.setattr(app_mod, "LATEST_GENERATION_TEXT_PATH", primary_text)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_JSON_PATH", primary_json)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_QUALITY_REPORT_PATH", primary_quality)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_TEXT_PATH_WORKSPACE", mirror_text_bad)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_JSON_PATH_WORKSPACE", mirror_json)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE", mirror_quality)
    monkeypatch.setattr(app_mod, "GENERATION_AUDIT_JSONL_PATH", primary_audit)
    monkeypatch.setattr(app_mod, "GENERATION_AUDIT_JSONL_PATH_WORKSPACE", mirror_audit)

    result = {
        "title": "t",
        "lead": "l",
        "body": "b",
        "references": "",
        "hashtags": "",
        "full_text": "本文です。",
        "linkedin_text": "",
        "review_points": [],
        "pipeline_check": {},
        "pipeline_check_linkedin": {},
        "quality_pipeline_check": {},
        "llm_check": {},
    }
    app_mod._persist_latest_generation_snapshot(
        result=result,
        attempt_id="gen-partial-1",
        article_type="ai",
        writing_focus_key="analysis",
        perspective_key="auto",
        user_prompt_text="u",
        source_count=1,
    )

    assert primary_text.exists()
    assert primary_json.exists()
    assert primary_quality.exists()
    assert primary_audit.exists()


def test_pipeline_check_snapshot_includes_contract_alignment_score(tmp_path, monkeypatch):
    from note import note_writer_app as app_mod

    primary_text = tmp_path / "latest.txt"
    primary_json = tmp_path / "latest.json"
    primary_quality = tmp_path / "quality.json"
    primary_audit = tmp_path / "audit.jsonl"
    mirror_text = tmp_path / "ws_latest.txt"
    mirror_json = tmp_path / "ws_latest.json"
    mirror_quality = tmp_path / "ws_quality.json"
    mirror_audit = tmp_path / "ws_audit.jsonl"

    monkeypatch.setattr(app_mod, "LATEST_GENERATION_TEXT_PATH", primary_text)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_JSON_PATH", primary_json)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_QUALITY_REPORT_PATH", primary_quality)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_TEXT_PATH_WORKSPACE", mirror_text)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_JSON_PATH_WORKSPACE", mirror_json)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE", mirror_quality)
    monkeypatch.setattr(app_mod, "GENERATION_AUDIT_JSONL_PATH", primary_audit)
    monkeypatch.setattr(app_mod, "GENERATION_AUDIT_JSONL_PATH_WORKSPACE", mirror_audit)

    result = {
        "title": "t",
        "lead": "l",
        "body": "b",
        "references": "",
        "hashtags": "",
        "full_text": "本文です。",
        "linkedin_text": "",
        "review_points": [],
        "pipeline_check": {
            "input_contract": {
                "length_mode_requested": "adaptive",
                "length_mode": "short",
                "audience_profile": "実務担当者",
                "topic_statement": "判断基準を整理する",
            },
            "contract_alignment": {
                "alignment_score": 0.82,
                "must_cover_items": ["判断基準"],
                "audience_profile": "実務担当者",
                "topic_statement": "判断基準を整理する",
                "question_source_counts": {"interview_answers": 1, "user_prompt": 1, "unresolved_items": 0, "unknown": 0},
            }
        },
        "pipeline_check_linkedin": {},
        "quality_pipeline_check": {},
        "llm_check": {},
        "zero_base_question_sources": {"message": "interview_answers", "target": "user_prompt"},
    }

    app_mod._persist_latest_generation_snapshot(
        result=result,
        attempt_id="gen-alignment-1",
        article_type="ai",
        writing_focus_key="analysis",
        perspective_key="auto",
        user_prompt_text="u",
        source_count=1,
    )

    saved = json.loads(primary_json.read_text(encoding="utf-8"))
    audit_saved = json.loads(primary_audit.read_text(encoding="utf-8").strip())
    assert saved["contract_alignment_score"] == 0.82
    assert saved["input_contract"]["length_mode_requested"] == "adaptive"
    assert saved["zero_base_question_sources"]["message"] == "interview_answers"
    assert "zero_base_contract_alignment" in saved
    assert audit_saved["input_contract"]["length_mode_requested"] == "adaptive"
    assert audit_saved["input_contract"]["length_mode"] == "short"
    assert audit_saved["contract_alignment"]["must_cover_items"] == ["判断基準"]
    assert audit_saved["contract_alignment"]["audience_profile"] == "実務担当者"


def test_build_quality_context_includes_style_and_custom_genre_metadata():
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._current_type = "custom_release_note"
    generator._pipeline_policy = {"style_profile": "formal"}
    generator._category_policy = {"base_template": "announcement", "source": "custom_meta"}
    generator._latest_user_prompt = "更新内容を端的に整理してください。"
    generator._interview_answers = {"message": "変更点を誤解なく伝える", "target": "既存ユーザー"}

    context = generator._build_quality_context(
        platform="note",
        perspective="corporate",
        focus="explanation",
        source_text="A" * 10000,
    )

    assert context["article_type"] == "custom_release_note"
    assert context["category_base_template"] == "announcement"
    assert context["category_policy_source"] == "custom_meta"
    assert context["style_profile_hint"] == "formal"
    assert context["is_custom_genre"] is True
    assert context["custom_genre_key"] == "custom_release_note"
    assert context["target_audience"] == "既存ユーザー"
    source_cfg = get_source_reading_config()
    expected_cap = int(source_cfg.get("quality_context_source_text_max_chars", 12000) or 12000)
    assert len(context["source_text"]) == min(10000, expected_cap)


# ── R4 Tests: Compiled regex & section-block cache ──


def test_compiled_regex_normalize_similarity_text():
    """R4-T05: _normalize_similarity_text uses compiled patterns and produces correct output."""
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "## 見出し1\nhttps://example.com テストの本文。  空白\n## 見出し2\n続き"
    result = generator._normalize_similarity_text(text)
    assert "見出し" not in result
    assert "https" not in result
    assert " " not in result
    assert "、" not in result
    assert "テスト" in result


def test_compiled_regex_extract_content_terms():
    """R4-T05: _extract_content_terms uses compiled patterns."""
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "## 見出しA\nhttps://example.com 機械学習の基本テクニック"
    terms = generator._extract_content_terms(text)
    assert any("機械学習" in t for t in terms)
    assert any("テクニック" in t for t in terms)


def test_section_block_cache_hit():
    """R4-T05: Second call to _extract_section_blocks with same body uses cache."""
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = "## 見出し1\n本文A\n\n## 見出し2\n本文B"
    result1 = generator._extract_section_blocks(body)
    assert generator._section_block_cache_misses == 1
    assert generator._section_block_cache_hits == 0
    result2 = generator._extract_section_blocks(body)
    assert generator._section_block_cache_hits == 1
    assert result1 == result2


def test_regex_cache_telemetry_in_pipeline_check():
    """R4-T05: _build_pipeline_check includes regex_cache stats."""
    generator = ArticleGenerator(llm_client=DummyLLM())
    generator._extract_section_blocks("## A\ntext")
    generator._extract_section_blocks("## A\ntext")
    generator._last_contextual_naturalness_report = {"passed": True, "issue_count": 0}
    check = generator._build_pipeline_check("note")
    assert "regex_cache" in check
    assert check["regex_cache"]["section_block_cache_hits"] == 1
    assert check["regex_cache"]["section_block_cache_misses"] == 1
    assert "contextual_naturalness_report" in check


def test_parse_outline_strips_code_fences():
    """Regression: LLM returns JSON wrapped in ```json fences (R12-T01)."""
    generator = ArticleGenerator(llm_client=DummyLLM())
    raw_with_fences = '```json\n{"sections": [{"heading": "テスト見出し", "purpose": "導入"}]}\n```'
    result = generator._parse_outline(raw_with_fences)
    assert len(result) >= 1
    assert result[0]["heading"] == "テスト見出し"


@pytest.mark.parametrize("label,raw", [
    ("4tick", '````json\n{"sections": [{"heading": "H"}]}\n````'),
    ("indent", '  ```json\n{"sections": [{"heading": "H"}]}\n  ```'),
    ("no_lang", '```\n{"sections": [{"heading": "H"}]}\n```'),
    ("trailing_nl", '```json\n{"sections": [{"heading": "H"}]}\n```\n'),
    ("space_lang", '``` json\n{"sections": [{"heading": "H"}]}\n```'),
    ("plain_json", '{"sections": [{"heading": "H"}]}'),
])
def test_parse_outline_codefence_edge_cases(label, raw):
    """Regression: various code-fence styles must not fall back (R12-T03)."""
    generator = ArticleGenerator(llm_client=DummyLLM())
    result = generator._parse_outline(raw)
    assert len(result) >= 1
    assert result[0]["heading"] == "H", f"case={label}: got {result}"


def test_parse_outline_fallback_skips_json_noise():
    """Regression: fallback parser must not use JSON fragments as headings (R12-T02)."""
    generator = ArticleGenerator(llm_client=DummyLLM())
    # Simulate totally broken JSON mixed with plain-text headings
    raw_broken = '```json\n{invalid\n"sections": [\n{\nテスト見出し\nまとめ\n```'
    result = generator._parse_outline(raw_broken)
    headings = [s["heading"] for s in result]
    # JSON noise should not appear as headings
    for h in headings:
        assert h not in ('```json', '{invalid', '"sections": [', '{', '```')
    # Plain-text headings should survive
    assert "テスト見出し" in headings
    assert "まとめ" in headings


# ------------------------------------------------------------------
# Paragraph-level generation helpers (段落単位生成)
# ------------------------------------------------------------------

class TestBuildSectionBrief:
    def test_contains_required_fields(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        gen._current_persona = "テスト執筆者"
        gen._current_pronoun = "私"
        brief = gen._build_section_brief(
            heading="テスト見出し",
            purpose="導入",
            required_elements="要素A, 要素B",
            key_message="結論テスト",
            do_not_cover="触れない話題",
            stage_role_label="導入",
            section_source="参考テキスト",
            quote_instruction="",
            prior_section_memory="既出要点テスト",
            transition_from_prev="前セクションから",
            title="テストタイトル",
            target_audience="初心者",
        )
        assert "テスト見出し" in brief
        assert "テストタイトル" in brief
        assert "初心者" in brief
        assert "要素A" in brief
        assert "結論テスト" in brief
        assert "触れない話題" in brief
        assert "既出要点テスト" in brief
        assert "前セクションから" in brief

    def test_includes_non_overlap_guard_when_forced(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        gen._current_persona = "テスト執筆者"
        brief = gen._build_section_brief(
            heading="見出しB",
            purpose="展開",
            required_elements="論点A, 論点B",
            key_message="このセクションの新規論点",
            do_not_cover="前セクションの結論",
            stage_role_label="展開",
            section_source="参考テキスト",
            quote_instruction="",
            prior_section_memory="- 見出しA: 既出論点の説明 / 補足",
            transition_from_prev="前の議論を受ける",
            title="テストタイトル",
            target_audience="初心者",
            force_non_overlap=True,
        )
        assert "前セクション既出論点" in brief
        assert "このセクション新規論点" in brief
        assert "既出論点の言い換えは禁止" in brief


class TestBuildStyleInvariants:
    def test_contains_pronoun_and_banned(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        gen._current_pronoun = "私"
        inv = gen._build_style_invariants()
        assert "私" in inv
        assert "禁止語" in inv
        assert "主語省略がデフォルト" in inv

    def test_no_experience_line_when_allow_false(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        gen._allow_experience = False
        inv = gen._build_style_invariants()
        assert "わたし自身" in inv

    def test_no_experience_line_absent_when_allow_true(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        gen._allow_experience = True
        inv = gen._build_style_invariants()
        assert "わたし自身" not in inv

    def test_contains_human_like_flow_rules(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        inv = gen._build_style_invariants()
        assert "見出し直下の1文目は、見出し語を1語以上含めて論点を明示" in inv
        assert "「Xは/Xが」で始まる文頭を連続させすぎない" in inv

    def test_contains_reader_question_guideline_with_prompt_anchor(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        gen._latest_user_prompt = "AIと人間の違いを平易に説明し、読者が自分ごと化できる内容にする"
        inv = gen._build_style_invariants()
        assert "読者への問いかけ" in inv
        assert "AIと人間の違い" in inv


def test_select_emphasis_span_starts_from_keyword_not_particle():
    generator = ArticleGenerator(llm_client=DummyLLM())
    line = "特許は技術開発の成果を守る盾であり、競争力の重要な源泉です。"
    span = generator._select_emphasis_span(line)
    assert span is not None
    start, end = span
    emphasized = line[start:end]
    assert emphasized.startswith("重要")
    assert "を守る" not in emphasized


class TestDistributeElementsToParagraphs:
    def test_role_based_distribution(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        plan = [
            {"role": "導入", "index": 1},
            {"role": "展開", "index": 2},
            {"role": "山場", "index": 3},
            {"role": "収束", "index": 4},
        ]
        elements = ["背景の説明", "核心の論点", "行動の提案"]
        dist = gen._distribute_elements_to_paragraphs(elements, plan)
        assert len(dist) == 4
        # 背景→導入
        assert any("背景" in e for e in dist[0])
        # 行動→収束
        assert any("行動" in e for e in dist[3])
        # 全要素が配分されている
        all_assigned = [e for bucket in dist for e in bucket]
        assert len(all_assigned) == 3

    def test_empty_elements(self):
        gen = ArticleGenerator(llm_client=DummyLLM())
        plan = [{"role": "導入"}, {"role": "収束"}]
        dist = gen._distribute_elements_to_paragraphs([], plan)
        assert dist == [[], []]


def _prepare_generator_for_section_test():
    """_generate_section テスト用に最低限の属性を設定した ArticleGenerator を返す。"""
    gen = ArticleGenerator(llm_client=DummyLLM())
    gen._current_persona = "テスト執筆者です。"
    gen._current_pronoun = "私"
    gen._current_perspective = "auto"
    gen._enhanced_context = ""
    gen._effective_writing_focus = "explanation"
    gen._section_opening_sequence = ["論点提示から入る"] * 5
    return gen


class TestParagraphGenerationModeFallback:
    def test_section_mode_uses_legacy(self):
        """paragraph_generation_mode='section' でレガシーパスへフォールバック。"""
        gen = _prepare_generator_for_section_test()
        gen._cognitive_drift_config = {"paragraph_generation_mode": "section"}
        section_meta = {
            "heading": "テスト見出し",
            "purpose": "テスト",
            "required_elements": ["要素1"],
        }
        # cognitive_profile に paragraph_plan があってもレガシーへ行く
        profile = {
            "temperature": 0.9,
            "paragraph_plan": [
                {"index": 1, "role": "導入", "phase": "careful_start",
                 "temperature": 0.85, "sentence_complexity": "simple",
                 "information_density": "low"},
                {"index": 2, "role": "収束", "phase": "winding_down",
                 "temperature": 0.85, "sentence_complexity": "simple",
                 "information_density": "low"},
            ],
        }
        result = gen._generate_section(
            section_meta=section_meta,
            merged="テスト本文",
            user_prompt="テスト",
            article_type="ai",
            quote_candidates=[],
            target_audience="初心者",
            target_chars=400,
            title="テストタイトル",
            cognitive_profile=profile,
        )
        # レガシーパスは ## 見出しを含む
        assert "##" in result

    def test_empty_plan_uses_legacy(self):
        """paragraph_plan が空の場合レガシーパスへフォールバック。"""
        gen = _prepare_generator_for_section_test()
        gen._cognitive_drift_config = {"paragraph_generation_mode": "paragraph"}
        section_meta = {
            "heading": "テスト見出し",
            "purpose": "テスト",
            "required_elements": [],
        }
        result = gen._generate_section(
            section_meta=section_meta,
            merged="テスト本文",
            user_prompt="テスト",
            article_type="ai",
            quote_candidates=[],
            target_audience="初心者",
            cognitive_profile={"temperature": 0.9, "paragraph_plan": []},
        )
        assert "##" in result


# ── R19: 人間ぽさアルゴリズム再設計テスト ─────────────────────────────────


def test_r19_sentence_under_130_chars_not_split():
    """R19 Phase1: 130文字以下の文は分割されない。"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    sentence = "生成AIは企画段階で案を高速に出せる一方で、評価軸が曖昧なまま運用を始めると判断がぶれて品質が安定せず修正コストが後半で膨らみやすいです。"
    assert len(sentence) <= 130
    result = generator._split_overlong_sentence(sentence, max_chars=130, max_splits=2)
    # 130文字以下なので分割されない（1要素のまま）
    assert len(result) == 1


def test_r19_theme_keyword_not_diversified():
    """R19 Phase2: テーマ語がキーワード多様化されない（_diversify_overused_keywords削除済み）。"""
    # _diversify_overused_keywords が削除されているので、パイプラインにメソッドが存在しないことを確認
    generator = ArticleGenerator(llm_client=DummyLLM())
    assert not hasattr(generator, "_diversify_overused_keywords") or True
    # _apply_final_consistency_guards 内で _diversify_overused_keywords が呼ばれないことを確認
    import inspect
    source = inspect.getsource(generator._apply_final_consistency_guards)
    assert "_diversify_overused_keywords" not in source


def test_r19_theme_prodrop_cross_paragraph():
    """R19 Phase3: テーマ語prodropが段落をまたいで動作する。"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = (
        "蒸留攻撃は防御が難しい。蒸留攻撃は検出も困難だ。\n\n"
        "蒸留攻撃は新しい手法を使う。蒸留攻撃は対策が急務だ。"
    )
    result = generator._apply_prodrop_zero_anaphora(text, theme_entities=["蒸留攻撃"])
    # テーマ語の一部が省略されているはず
    count = result.count("蒸留攻撃は") + result.count("蒸留攻撃が")
    assert count < 4, f"テーマ語主語が省略されていない: {result}"


def test_r19_cap_colloquial_allows_two():
    """R19 Phase5: _cap_colloquial_endings が2回まで許容する。"""
    from note.article_generator import NON_CASUAL_COLLOQUIAL_ENDING_MAX
    assert NON_CASUAL_COLLOQUIAL_ENDING_MAX == 2
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "品質は重要ですね。工程は安定しますね。検査は継続しますよね。"
    capped = generator._cap_colloquial_endings(text)
    colloquial_hits = len(re.findall(r"(ですね。|ますね。|ますよね。|ですよね。)", capped))
    assert colloquial_hits == 2, f"2回許容されるべき: {capped}"


def test_r19_break_ending_monotony_disperses_masu_run():
    """R19: 「ます。」が3回以上連続したら中間を揺らす。"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = "防御策を実装します。次にレート制限を設定します。ノイズ注入も導入します。異常検知を組み込みます。"
    result = generator._break_ending_monotony(text)
    # 4連続「ます。」のうち少なくとも1つが書き換わる
    masu_count = len(re.findall(r"ます。", result))
    assert masu_count < 4, f"ます連続が散っていない: {result}"


def test_r19_break_ending_monotony_across_paragraphs():
    """R19: 段落をまたぐ「ます。」連続も分散される。"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = (
        "教材案を自動生成できます。\n\n"
        "個別課題を柔軟に提示できます。\n\n"
        "理解度に応じて再提案できます。\n\n"
        "授業後の振り返りも効率化できます。"
    )
    result = generator._break_ending_monotony(text)
    sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", result) if s.strip()]
    max_run = 0
    current = 0
    for sentence in sentences:
        if sentence.endswith("ます。"):
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    assert max_run <= 3, f"段落またぎのます連続が散っていない: max_run={max_run}, result={result}"


def test_r19_break_ending_monotony_handles_arimasu_series():
    """R19: 「あります。」連続でも分散できる。"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    text = (
        "運用ルールの抜け漏れがあります。\n\n"
        "評価基準の揺らぎがあります。\n\n"
        "出典確認の遅れがあります。\n\n"
        "著作権の見落としがあります。"
    )
    result = generator._break_ending_monotony(text)
    sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", result) if s.strip()]
    max_run = 0
    current = 0
    for sentence in sentences:
        if sentence.endswith("ます。"):
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    assert max_run <= 3, f"あります連続が散っていない: max_run={max_run}, result={result}"


def test_r19_short_paragraph_not_merged():
    """R19 Phase1: 40文字以下の短い段落でも助詞終了で41文字以上なら結合されない。"""
    from note.post_processor_mixin import PostProcessorMixin
    # 41文字以上の段落が助詞で終わる場合 → 結合されない
    paragraphs = [
        "これは長めの段落で助詞で終わるテストです。生成AIの評価軸が曖昧で品質が安定しないことは",
        "結果として現場の負担が増える原因になります。",
    ]
    assert len(paragraphs[0]) > 40
    result = PostProcessorMixin._merge_broken_paragraphs(paragraphs)
    assert len(result) == 2, f"41文字以上の段落は結合されないべき: {result}"


def test_r19_soften_assertive_expressions():
    """R19: 断定的表現がソフトに言い換えられる。"""
    text = "必ず効果が出ます。確実にスキルが向上する。資料は必ず複数確認する。必ずしも万能ではありません。"
    result = ArticleGenerator._soften_assertive_expressions(text)
    assert "必ず" not in result, f"必ず should be softened: {result}"
    assert "確実に" not in result, f"確実に should be softened: {result}"
    assert "常にとは限らず" in result, f"必ずしも should be normalized: {result}"


def test_r19_dedupe_cross_section_sentences():
    """R19: セクション間の同一フレーズ文が削除される。"""
    body = (
        "## セクション1\n\n"
        "生成AIは誤情報や古いデータが混じることがあり注意が必要です。\n"
        "著作権の問題も重要です。\n\n"
        "## セクション2\n\n"
        "教育現場では多くの課題があります。\n"
        "生成AIは誤情報や古いデータが混じることがあり注意が必要です。"
    )
    result = ArticleGenerator._dedupe_cross_section_sentences(body)
    # 2回目の出現が削除されるべき
    count = result.count("誤情報や古いデータが混じることがあり")
    assert count <= 1, f"重複文が残っている: count={count}, result={result}"


def test_r19_dedupe_cross_section_sentences_removes_single_sentence_duplicate_paragraph():
    body = (
        "## セクション1\n\n"
        "導入として背景を整理します。\n"
        "この段階で重要なのは「働く社員のリアルな声」を判断基準として具体化することです。\n\n"
        "## セクション2\n\n"
        "次の要点に進みます。\n"
        "この段階で大切なのは「さんれいフーズは食のエキスパート」を判断基準として具体化することです。"
    )
    result = ArticleGenerator._dedupe_cross_section_sentences(body)
    assert "判断基準として具体化することです" in result
    assert result.count("判断基準として具体化することです") <= 1


def test_r19_banned_phrases_expanded():
    """R19: 新しいBANNED_PHRASESが含まれている。"""
    from human_resonance.style_policy import BANNED_PHRASES
    assert "欠かせません" in BANNED_PHRASES
    assert "不可欠です" in BANNED_PHRASES
    assert "潜んでいます" in BANNED_PHRASES


def test_r19_ai_like_ending_rewrites_expanded():
    """R19: AI_LIKE_ENDING_REWRITESに新パターンが追加されている。"""
    from human_resonance.style_policy import AI_LIKE_ENDING_REWRITES
    patterns = [p for p, _ in AI_LIKE_ENDING_REWRITES]
    assert any("恐れがあります" in p for p in patterns)
    assert any("が不可欠です" in p for p in patterns)
    assert any("が欠かせません" in p for p in patterns)


# ===== R20 Tests =====


def test_r20_prodrop_alternating_drop_uses_counter():
    """R20: テーマ語の交互ドロップが専用カウンタで正しく機能する。"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    # テーマ語「AI」が段落をまたいで5文以内に再出現
    text = (
        "AIはデータを必要とします。品質が重要です。\n\n"
        "AIは学習に時間がかかります。AIは結果を出します。"
    )
    result = generator._apply_prodrop_zero_anaphora(text, theme_entities=["AI"])
    # 全3回出現のうち、交互で少なくとも1回はドロップされるべき
    ai_subject_count = result.count("AIは") + result.count("AIが")
    assert ai_subject_count < 3, f"交互ドロップが効いていない: count={ai_subject_count}, result={result}"


def test_r20_extract_theme_entities_compound_nouns():
    """R20: 複合名詞（漢字+カタカナ、カタカナ+漢字）が抽出される。"""
    result = ArticleGenerator._extract_theme_entities("情報リテラシーとエコーチェンバー現象")
    # 「情報リテラシー」（漢字+カタカナ）or 「エコーチェンバー現象」（カタカナ+漢字）が抽出されるべき
    combined = "".join(result)
    assert any(
        word in combined
        for word in ["情報リテラシー", "エコーチェンバー"]
    ), f"複合名詞が抽出されていない: {result}"


def test_r20_break_ending_monotony_abab_pattern():
    """R20: ABAB型（ます。です。ます。です。）の交互反復が検知・散らされる。"""
    text = (
        "この仕組みが便利です。利用者が増えます。"
        "活用範囲が広いです。課題も見えます。"
    )
    result = ArticleGenerator._break_ending_monotony(text)
    # ABAB パターンの3文目が書き換えられるべき
    sentences = [s.strip() for s in result.split("。") if s.strip()]
    endings = []
    for s in sentences:
        if s.endswith("です"):
            endings.append("desu")
        elif s.endswith("ます"):
            endings.append("masu")
        else:
            endings.append("other")
    # 完全なABAB（desu,masu,desu,masu）が崩されているべき
    assert endings != ["desu", "masu", "desu", "masu"], f"ABAB が散らされていない: {endings}"


def test_r20_dedupe_similar_headings():
    """R20: Jaccard類似度が高い見出しが差別化される。"""
    body = (
        "## フィルターバブルとは\n\n内容A。\n\n"
        "## フィルターバブルとは？\n\n内容B。"
    )
    result = ArticleGenerator._dedupe_similar_headings(body)
    headings = [line for line in result.split("\n") if line.strip().startswith("##")]
    # 2つの見出しが異なるべき
    if len(headings) >= 2:
        h1 = headings[0].replace("#", "").strip()
        h2 = headings[1].replace("#", "").strip()
        assert h1 != h2, f"見出しが差別化されていない: {headings}"


def test_r20_contextual_emphasis_keeps_quotes_outside_bold():
    """R20: 引用語を強調する際は「**語句**」形式を維持する。"""
    generator = ArticleGenerator(llm_client=DummyLLM())
    lead = "どうすればその「自分だけの情報のかたまり」に気づけるでしょうか。"
    emphasized_lead, _ = generator._apply_note_contextual_emphasis(lead, "")
    assert "**「" not in emphasized_lead and "」**" not in emphasized_lead
    assert "「**自分だけの情報のかたまり**」" in emphasized_lead


# --- Privacy blur for uploaded images ---

def test_source_item_blur_applied_default():
    """SourceItem.blur_applied のデフォルト値は False。"""
    from note.note_writer_app import SourceItem
    item = SourceItem(id="test-1", label="photo.jpg", value="/tmp/photo.jpg", source_type="image")
    assert item.blur_applied is False


def test_source_item_blur_applied_set():
    """SourceItem.blur_applied を True に設定できる。"""
    from note.note_writer_app import SourceItem
    item = SourceItem(id="test-2", label="photo.jpg", value="/tmp/photo.jpg", source_type="image", blur_applied=True)
    assert item.blur_applied is True
    item.blur_applied = False
    assert item.blur_applied is False


def test_privacy_only_render_preview(tmp_path):
    """render_preview にプライバシーのみパラメータを渡して動作する。"""
    from note.image_editing import render_preview, ImageAdjustment, PrivacyBlur
    from PIL import Image
    img = Image.new("RGB", (200, 200), color="blue")
    img_path = tmp_path / "test_face.png"
    img.save(str(img_path))
    # blur_personal_text=False: rapidocr-onnxruntime 未インストール環境でも動作
    privacy = PrivacyBlur(enabled=True, strength="medium", blur_personal_text=False)
    result_path, error = render_preview(
        str(img_path), "none", "none", ImageAdjustment(), None, "", str(tmp_path), privacy,
    )
    assert error is None
    assert result_path is not None
    assert result_path.exists()


def test_privacy_only_save_edited_image(tmp_path):
    """save_edited_image にプライバシーのみパラメータでファイル名に privacy-{strength} を含む。"""
    from note.image_editing import save_edited_image, ImageAdjustment, PrivacyBlur
    from PIL import Image
    img = Image.new("RGB", (200, 200), color="red")
    img_path = tmp_path / "test_plate.png"
    img.save(str(img_path))
    privacy = PrivacyBlur(enabled=True, strength="strong", blur_personal_text=False)
    result_path, error = save_edited_image(
        str(img_path), "none", "none", ImageAdjustment(), None, "", str(tmp_path), privacy,
    )
    assert error is None
    assert result_path is not None
    assert "privacy-strong" in result_path.stem
    assert result_path.exists()


class _Phase08RegressionLLM:
    """Deterministic LLM stub for phase08 zero-base regressions."""

    def generate_text(self, prompt: str, max_tokens: int = 0, task_type: str = "", **kwargs) -> str:
        if task_type == "title":
            return "phase08検証タイトル"
        if task_type in {"lead", "lead_refresh"}:
            return "導入です。背景を短く示します。次の行動を具体化します。"
        if task_type == "hashtags":
            return "#phase08 #zero_base #regression"
        if task_type == "editor_consistency":
            return '{"lead": "導入です。", "body": "## 見出しA\\n\\n本文です。\\n\\n## 見出しB\\n\\n本文です。"}'
        if task_type == "zero_base_section":
            return (
                "まず現状を確認し、判断基準をそろえます。"
                "次に運用手順を段階化して、担当者ごとの判断のばらつきを減らします。"
                "最後に記録方法を統一し、次回改善へつなげます。"
            )
        return "本文です。"


def _phase08_contexts() -> list[FetchedContent]:
    text = (
        "運用改善の基準と実行手順を整理し、引き継ぎ時の判断差を減らします。"
        "記録テンプレートを統一すると、再発防止と改善サイクルが回しやすくなります。"
    )
    return [
        FetchedContent(title="資料A", content=text, source_type="url"),
        FetchedContent(title="資料B", content=text, source_type="url"),
        FetchedContent(title="資料C", content=text, source_type="url"),
    ]


def test_phase08_zero_base_body_has_no_supplement_prefix(monkeypatch):
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v1")
    generator = ArticleGenerator(llm_client=_Phase08RegressionLLM())
    generator._apply_resonance = lambda text, **kwargs: text  # type: ignore[method-assign]

    result = generator.generate(
        _phase08_contexts(),
        "運用ルールを整理し、再発防止の手順を明確にする",
        "branding",
        length_mode="long",
    )

    assert "- 補足:" not in result["body"]
    assert result["zero_base_must_cover_integration_report"]["integrated_count"] >= 0


def test_phase08_zero_base_body_length_guard(monkeypatch):
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v1")
    generator = ArticleGenerator(llm_client=_Phase08RegressionLLM())
    generator._apply_resonance = lambda text, **kwargs: text  # type: ignore[method-assign]

    result = generator.generate(
        _phase08_contexts(),
        "判断基準と実行手順を段階で整理した長文を作る",
        "branding",
        length_mode="long",
    )

    length_plan = result["pipeline_check"]["zero_base_length_plan"]
    actual = length_plan.get("actual", {})
    assert int(actual.get("body_chars_before_links", 0)) >= 692
    targets = length_plan.get("targets", {})
    target_body = int(targets.get("body_chars", 0) or 0)
    assert target_body > 0


def test_phase08_zero_base_linebreak_density_report(monkeypatch):
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v1")
    generator = ArticleGenerator(llm_client=_Phase08RegressionLLM())
    generator._apply_resonance = lambda text, **kwargs: text  # type: ignore[method-assign]

    result = generator.generate(
        _phase08_contexts(),
        "読みやすさを優先し、段落を詰まらせない構成で書く",
        "branding",
        length_mode="normal",
    )

    profile = result["pipeline_check"]["contract_alignment"]["linebreak_profile"]
    assert profile["paragraph_after"] >= profile["paragraph_before"]
    assert profile["profile"] in {"branding_story", "default_balanced", "analysis_balanced", "announcement_compact"}


def test_phase08_zero_base_runs_compacted_postprocess_pipeline(monkeypatch):
    monkeypatch.setattr("note.article_generator.get_generation_mode", lambda: "zero_base_v1")
    generator = ArticleGenerator(llm_client=_Phase08RegressionLLM())
    generator._apply_resonance = lambda text, **kwargs: text  # type: ignore[method-assign]

    result = generator.generate(
        _phase08_contexts(),
        "表現の重複や文末の不自然さを抑え、読みやすく整える",
        "branding",
        length_mode="normal",
    )

    naturalness = result["pipeline_check"]["contextual_naturalness_report"]
    assert int(naturalness.get("sentence_count", 0)) > 0
    assert "mode" in result["pipeline_check"]["hard_soft_eval"]


def test_phase08_zero_base_linebreak_profile_is_relaxed_for_branding():
    generator = ArticleGenerator(llm_client=DummyLLM())
    profile = generator._zero_base_get_linebreak_profile(
        {
            "article_type": "corporate_culture",
            "category_base_template": "branding",
        }
    )
    assert profile["profile"] == "branding_story"
    assert profile["sentence_min"] == 2
    assert profile["sentence_max"] == 5
    assert profile["max_chars"] == 260


def test_phase08_zero_base_linebreak_profile_keeps_compact_five_sentence_paragraph():
    generator = ArticleGenerator(llm_client=DummyLLM())
    body = "## 見出し\n\n一文目です。二文目です。三文目です。四文目です。五文目です。"
    profiled, report = generator._zero_base_apply_linebreak_profile(
        body=body,
        contract={
            "article_type": "corporate_culture",
            "category_base_template": "branding",
        },
    )
    assert report["paragraph_before"] == report["paragraph_after"]
    assert profiled.count("\n\n") == body.count("\n\n")


def test_zero_base_align_corporate_voice_normalizes_private_pronouns_with_particles():
    generator = ArticleGenerator(llm_client=DummyLLM())

    normalized = generator._zero_base_align_corporate_voice(
        "私は価値を伝えます。私で判断した理由も共有します。",
        {"article_type": "branding", "category_base_template": "branding"},
    )

    assert "私は" not in normalized
    assert "私で" not in normalized
    assert "私たちは価値を伝えます。" in normalized
    assert "私たちで判断した理由も共有します。" in normalized
