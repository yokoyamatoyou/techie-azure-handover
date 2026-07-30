from pathlib import Path

from note.blog_image_auto import (
    build_blog_image_prompt,
    generate_blog_images_for_article,
    infer_image_display_text,
    successful_image_paths,
)
from note.image_config import DEFAULT_IMAGE_QUALITY, DEFAULT_IMAGE_SIZE, DEFAULT_TEXT_IMAGE_QUALITY
from note.image_cover_strategy import (
    build_cover_visual_brief_lines,
    build_display_copy_prompt,
    clean_display_text,
    fallback_display_text,
    is_article_specific_display_text,
    resolve_cover_strategy,
)
from note.image_prompt_helpers import IMAGE_PATTERN_OPTIONS, _normalize_image_pattern_key


class _FakeLLM:
    def __init__(
        self,
        *,
        fail_first: bool = False,
        always_fail: bool = False,
        text_response: str = "変化の要点",
    ) -> None:
        self.fail_first = fail_first
        self.always_fail = always_fail
        self.text_response = text_response
        self.image_calls = []
        self.text_calls = []

    def generate_text(self, prompt, **kwargs):  # type: ignore[no-untyped-def]
        self.text_calls.append((prompt, kwargs))
        return self.text_response

    def generate_images(self, prompt, **kwargs):  # type: ignore[no-untyped-def]
        self.image_calls.append((prompt, kwargs))
        call_count = len(self.image_calls)
        if self.always_fail:
            raise RuntimeError("image down")
        if self.fail_first and call_count == 1:
            raise RuntimeError("temporary image failure")
        variant = "text" if kwargs.get("allow_text") else "plain"
        return [Path(f"C:/tmp/{variant}_{call_count}.jpg")]


def test_blog_image_defaults_use_note_cover_size_and_split_quality() -> None:
    assert DEFAULT_IMAGE_SIZE == "1280x672"
    assert DEFAULT_TEXT_IMAGE_QUALITY == "medium"
    assert DEFAULT_IMAGE_QUALITY == "low"


def test_image_touch_options_are_four_way_and_exclude_rejected_labels() -> None:
    labels = [option["label"] for option in IMAGE_PATTERN_OPTIONS.values()]

    assert list(IMAGE_PATTERN_OPTIONS) == [
        "simple",
        "blog_cover",
        "flat_illustration",
        "warm_handdrawn",
    ]
    assert labels == ["シンプル", "ブログ見出し画像風", "フラットイラスト", "温かい手描き風"]
    assert "note見出し画像風" not in labels
    assert "ビジネス資料風" not in labels
    assert "写真風" not in labels
    assert "図解・インフォグラフィック風" not in labels
    assert "バランス" not in labels
    assert "世界観重視" not in labels


def test_image_touch_options_are_reflected_in_prompts_without_editorial_cue() -> None:
    expected_terms = {
        "simple": "simple, clear cover",
        "blog_cover": "Japanese blog eyecatch cover",
        "flat_illustration": "modern flat illustration",
        "warm_handdrawn": "warm hand-drawn illustration",
    }

    for key, expected in expected_terms.items():
        prompt = build_blog_image_prompt(
            title="地域企業の採用力を高める方法",
            lead="採用広報の考え方を整理します。",
            body="本文では、候補者への伝わり方と継続発信を扱います。",
            article_type="owned_media",
            display_text="採用力を育てる",
            variant_key="with_text",
            pattern_key=key,
        )

        assert expected in prompt
        assert "Touch is an expression direction only" in prompt
        assert "editorial" not in prompt.lower()
        assert "編集調" not in prompt


def test_unknown_image_touch_key_falls_back_to_simple() -> None:
    assert _normalize_image_pattern_key("missing-key") == "simple"
    assert _normalize_image_pattern_key("balanced") == "blog_cover"
    assert _normalize_image_pattern_key("rich") == "blog_cover"

    prompt = build_blog_image_prompt(
        title="地域企業の採用力を高める方法",
        lead="採用広報の考え方を整理します。",
        body="本文では、候補者への伝わり方と継続発信を扱います。",
        article_type="owned_media",
        display_text="採用力を育てる",
        variant_key="with_text",
        pattern_key="missing-key",
    )

    assert "simple, clear cover" in prompt


def test_build_blog_image_prompt_handles_japanese_text_variants() -> None:
    text_prompt = build_blog_image_prompt(
        title="地域企業の採用力を高める方法",
        lead="採用広報の考え方を整理します。",
        body="本文では、候補者への伝わり方と継続発信を扱います。",
        article_type="owned_media",
        display_text="採用力を育てる",
        variant_key="with_text",
        pattern_key="balanced",
    )
    plain_prompt = build_blog_image_prompt(
        title="地域企業の採用力を高める方法",
        lead="採用広報の考え方を整理します。",
        body="本文では、候補者への伝わり方と継続発信を扱います。",
        article_type="owned_media",
        display_text="採用力を育てる",
        variant_key="without_text",
        pattern_key="balanced",
    )

    assert '"採用力を育てる"' in text_prompt
    assert text_prompt.count('"採用力を育てる"') == 1
    assert "Text to render EXACTLY" in text_prompt
    assert "Let GPT Image 2 design the typography and placement naturally" in text_prompt
    assert "let GPT Image 2 choose the amount of supporting detail" in text_prompt
    assert "at least 15% clean breathing room" in text_prompt
    assert "bold clean Japanese sans-serif" not in text_prompt
    assert "1-3" not in text_prompt
    assert "2-4" not in text_prompt
    assert "4-7" not in text_prompt
    assert "No letters, no numbers" in plain_prompt
    assert "no signs" in plain_prompt
    assert "no logos" in plain_prompt
    assert "no watermark" in plain_prompt
    assert "採用力を育てる" not in plain_prompt


def test_cover_strategy_lines_are_article_type_specific() -> None:
    announcement = build_cover_visual_brief_lines(article_type="announcement", variant_key="with_text")
    comparative = build_cover_visual_brief_lines(article_type="comparative_review", variant_key="without_text")

    assert any("concrete change or start date" in line for line in announcement)
    assert any("comparison axis" in line for line in comparative)
    assert "ranking language" in resolve_cover_strategy("comparative_review").display_copy_shape


def test_build_blog_image_prompt_uses_cover_strategy_without_copying_title() -> None:
    prompt = build_blog_image_prompt(
        title="AI議事録ツールを話者分離で選ぶときの見方",
        lead="要約精度だけでなく、話者分離と共有管理を同じ軸で見ます。",
        body="候補ごとの違いを、会議後の確認負担から整理します。",
        article_type="comparative_review",
        display_text="AI議事録ツールの話者分離",
        variant_key="with_text",
        pattern_key="balanced",
    )

    assert "Cover role:" in prompt
    assert "comparison cover" in prompt
    assert "ranking language" in prompt
    assert '"AI議事録ツールの話者分離"' in prompt


def test_infer_image_display_text_rejects_generic_copy_for_specific_title() -> None:
    llm = _FakeLLM(text_response="迷わない導入導線")

    display_text = infer_image_display_text(
        llm,
        title="小規模SaaSの導入初期で迷いを減らすには何が必要か",
        lead="小規模SaaSの導入初期では、最初の設定や相談先が見えることが重要です。",
        body="本文",
        article_type="branding",
    )

    assert display_text == "小規模SaaS、どこから相談する？"
    assert "主題エンティティ（必ず含める）: 小規模SaaS" in llm.text_calls[0][0]
    assert "記事タイトルとは別のカバー用コピー" in llm.text_calls[0][0]
    assert "ブログの見出し画像" in llm.text_calls[0][0]
    assert "note/はてなブログ" not in llm.text_calls[0][0]
    assert "説明ラベルではなく、読者が開く理由" in llm.text_calls[0][0]
    assert "推奨コピー候補: 小規模SaaS、どこから相談する？" in llm.text_calls[0][0]
    assert "抽象的なスローガン" in llm.text_calls[0][0]


def test_infer_image_display_text_rejects_unnatural_entity_suffix() -> None:
    llm = _FakeLLM(text_response="導入初期の迷いを減らすSaaS")

    display_text = infer_image_display_text(
        llm,
        title="小規模SaaSの導入初期で迷いを減らすには何が必要か",
        lead="小規模SaaSの導入初期では、最初の設定や相談先が見えることが重要です。",
        body="本文",
        article_type="branding",
    )

    assert display_text == "小規模SaaS、どこから相談する？"


def test_infer_image_display_text_company_intro_rejects_consultation_question() -> None:
    llm = _FakeLLM(text_response="1885年、相談先の見方は？")

    display_text = infer_image_display_text(
        llm,
        title="京都工業株式会社のサービス案内と判断の軸",
        lead="業務をどこへ相談すればよいか。私たち京都工業株式会社は1885年、機織機部品の製造から事業を開始しました。",
        body="私たちはデータ入力、スキャニング、RPA、Webリサーチを扱っています。",
        article_type="company_introduction",
    )

    assert display_text == "サービスの対応領域"


def test_company_intro_display_copy_prompt_avoids_judgment_axis_hook_shape() -> None:
    prompt, fallback = build_display_copy_prompt(
        title="京都工業株式会社の会社紹介",
        lead="私たちはデータ入力、スキャニング、RPA、Webリサーチを扱っています。",
        body="京都工業株式会社はデータ化とデジタル化を支援しています。",
        article_type="company_introduction",
    )

    assert fallback == "データ入力とスキャニング"
    assert "問い・相談導線・判断軸ではなく" in prompt
    assert "読者の状況 + 判断軸" not in prompt
    assert "事業領域、サービス、設備、地域、現在の仕事" in prompt


def test_infer_image_display_text_accepts_article_specific_hook_without_core_subject() -> None:
    llm = _FakeLLM(text_response="導入初期どこで迷う？")

    display_text = infer_image_display_text(
        llm,
        title="小規模SaaSの導入初期で迷いを減らすには何が必要か",
        lead="小規模SaaSの導入初期では、最初の設定や相談先が見えることが重要です。",
        body="本文",
        article_type="branding",
    )

    assert display_text == "導入初期どこで迷う？"


def test_display_text_validation_rejects_label_and_overclaim_but_accepts_hooks() -> None:
    title = "AI議事録ツールを話者分離で選ぶときの見方"
    lead = "要約精度だけでなく、話者分離と共有管理を同じ軸で見ます。"

    assert clean_display_text("「話者分離でどこを見る？」") == "話者分離でどこを見る？"
    assert not is_article_specific_display_text(
        "AI議事録ツールの話者分離",
        title,
        lead,
        article_type="comparative_review",
    )
    assert not is_article_specific_display_text(
        "売上が伸びる導入術",
        title,
        lead,
        article_type="comparative_review",
    )
    assert not is_article_specific_display_text(
        "絶対失敗しない選び方",
        title,
        lead,
        article_type="comparative_review",
    )
    assert not is_article_specific_display_text(
        "比較前に見る条件",
        title,
        lead,
        article_type="comparative_review",
    )
    assert is_article_specific_display_text(
        "話者分離でどこを見る？",
        title,
        lead,
        article_type="comparative_review",
    )
    assert is_article_specific_display_text(
        "AI議事録、どこで選ぶ？",
        title,
        lead,
        article_type="comparative_review",
    )


def test_display_text_validation_rejects_generic_company_question_and_internal_terms() -> None:
    title = "データ化支援の進め方"
    lead = "紙の申込書や台帳のデータ化サービスと対応領域を説明します。"

    assert not is_article_specific_display_text(
        "どこから相談できる？",
        title,
        lead,
        article_type="company_introduction",
    )
    assert not is_article_specific_display_text(
        "SEMANTIC_LEDGERで確認",
        title,
        lead,
        article_type="company_introduction",
    )
    assert not is_article_specific_display_text(
        "データ化、どこから相談する？",
        title,
        lead,
        article_type="company_introduction",
    )
    assert not is_article_specific_display_text(
        "会社紹介のポイント",
        title,
        lead,
        article_type="company_introduction",
    )
    assert is_article_specific_display_text(
        "データ化サービスの対応領域",
        title,
        lead,
        article_type="company_introduction",
    )


def test_fallback_display_text_uses_business_area_for_company_introduction() -> None:
    assert fallback_display_text(
        "ガス・電気・住まいで支える、山陰酸素工業株式会社の事業内容",
        "産業用・医療用ガス、LPガスやLNG、電気、設備設計、住宅リフォームまで扱います。",
        article_type="company_introduction",
    ) == "ガス・電気・住まいを支える"


def test_company_introduction_rejects_consultation_copy_and_allows_business_copy() -> None:
    title = "ガス・電気・住まいで支える、山陰酸素工業株式会社の事業内容"
    lead = "産業用・医療用ガス、LPガスやLNG、電気、関連機器、設備設計、住宅リフォームまで扱います。"

    assert not is_article_specific_display_text(
        "LNG、どこから相談する？",
        title,
        lead,
        article_type="company_introduction",
    )
    assert not is_article_specific_display_text(
        "支援範囲、どこまで？",
        title,
        lead,
        article_type="company_introduction",
    )
    assert is_article_specific_display_text(
        "ガス・電気・住まいを支える",
        title,
        lead,
        article_type="company_introduction",
    )


def test_company_introduction_fallback_ignores_source_consultation_word() -> None:
    assert fallback_display_text(
        "京都からデータ化・デジタル化を支える会社案内",
        "データ入力、スキャニング、データ活用相談、Webリサーチ、RPA導入支援まで扱います。",
        article_type="company_introduction",
    ) == "データ化・デジタル化事業"

    assert not is_article_specific_display_text(
        "Webの相談",
        "京都からデータ化・デジタル化を支える会社案内",
        "データ入力、スキャニング、データ活用相談、Webリサーチ、RPA導入支援まで扱います。",
        article_type="company_introduction",
    )


def test_company_introduction_rejects_repeated_display_copy_and_falls_back_to_business_area() -> None:
    title = "データ入力・市場調査・Webリサーチ・業務整理を支えるテティエの対応範囲"
    lead = (
        "紙やExcelに残った作業を、データ入力や市場調査、Webリサーチ、"
        "業務整理を通じて支援します。"
    )

    assert fallback_display_text(title, lead, article_type="company_introduction") == "データ入力と業務支援"

    for repeated in ("データ入力のデータ入力", "入力業務の入力業務", "ガスのガス", "ガス・ガス", "ガス、ガス"):
        assert not is_article_specific_display_text(
            repeated,
            title,
            lead,
            article_type="company_introduction",
        )

    llm = _FakeLLM(text_response="データ入力のデータ入力")
    assert (
        infer_image_display_text(
            llm,
            title=title,
            lead=lead,
            body="本文",
            article_type="company_introduction",
        )
        == "データ入力と業務支援"
    )


def test_company_introduction_allows_non_repeated_business_copy_examples() -> None:
    title = "紙書類のデータ化とLNGまで担う会社の事業内容"
    lead = (
        "紙書類のデータ化、デジタル化事業、産業用ガス、LPガス、LNG、"
        "電気、住まいまで扱います。"
    )

    for copy in (
        "データ化・デジタル化事業",
        "ガス・電気・住まいを支える",
        "LNGまで担う事業内容",
        "紙書類のデータ化事業",
    ):
        assert is_article_specific_display_text(
            copy,
            title,
            lead,
            article_type="company_introduction",
        )


def test_branding_keeps_company_contact_point_hook() -> None:
    assert fallback_display_text(
        "データ化支援の進め方",
        "紙の申込書や台帳をどう整理し、どこから相談できるかを説明します。",
        article_type="branding",
    ) == "データ化、どこから相談する？"


def test_fallback_display_text_uses_announcement_change_target_hook() -> None:
    assert fallback_display_text(
        "料金改定のお知らせ",
        "月額料金の改定前に、対象範囲と確認手順を案内します。",
        article_type="announcement",
    ) == "料金改定前に見ること"

    assert fallback_display_text(
        "申請手順の変更について",
        "手順変更の対象範囲と確認先を整理します。",
        article_type="announcement",
    ) == "手順変更、何を確認する？"


def test_fallback_display_text_uses_comparative_decision_axis_hook() -> None:
    assert fallback_display_text(
        "AI議事録ツールを話者分離で選ぶときの見方",
        "要約精度だけでなく、話者分離と共有管理を同じ軸で見ます。",
        article_type="comparative_review",
    ) == "話者分離でどこを見る？"

    assert is_article_specific_display_text(
        "話者分離でどこを見る？",
        "AI議事録ツールを話者分離で選ぶときの見方",
        "要約精度だけでなく、話者分離と共有管理を同じ軸で見ます。",
        article_type="comparative_review",
    )


def test_fallback_display_text_retains_concrete_subject_or_axis() -> None:
    assert fallback_display_text(
        "生成AIの運用条件を決める前に見ること",
        "生成AIを現場で使う前に、権限と確認体制を整理します。",
        article_type="explanatory_article",
    ) == "運用前に見る条件"


def test_generate_blog_images_success_uses_two_variants_and_same_size(tmp_path) -> None:
    llm = _FakeLLM()

    result = generate_blog_images_for_article(
        llm=llm,
        title="タイトル",
        lead="リード",
        body="本文",
        article_type="announcement",
        pattern_key="rich",
        size="1280x672",
        plain_quality="low",
        text_quality="medium",
        log_dir=tmp_path,
    )

    assert result["status"] == "success"
    assert result["touch_profile_key"] == "blog_cover"
    assert result["touch_profile_label"] == "ブログ見出し画像風"
    assert len(result["variants"]) == 2
    assert [path.replace("\\", "/") for path in successful_image_paths(result)] == [
        "C:/tmp/text_1.jpg",
        "C:/tmp/plain_2.jpg",
    ]
    assert llm.image_calls[0][1]["allow_text"] is True
    assert llm.image_calls[1][1]["allow_text"] is False
    assert {call[1]["pattern_key"] for call in llm.image_calls} == {"blog_cover"}
    assert {call[1]["size"] for call in llm.image_calls} == {"1280x672"}
    assert llm.image_calls[0][1]["quality"] == "medium"
    assert llm.image_calls[1][1]["quality"] == "low"
    assert (tmp_path / "latest.json").exists()


def test_generate_blog_images_retries_failed_variant_once(tmp_path) -> None:
    llm = _FakeLLM(fail_first=True)

    result = generate_blog_images_for_article(
        llm=llm,
        title="タイトル",
        lead="リード",
        body="本文",
        log_dir=tmp_path,
    )

    assert result["status"] == "success"
    assert result["variants"][0]["retry_count"] == 1
    assert result["variants"][0]["retry_prompt"]
    assert len(llm.image_calls) == 3


def test_generate_blog_images_fails_open_after_retry_exhaustion(tmp_path) -> None:
    llm = _FakeLLM(always_fail=True)

    result = generate_blog_images_for_article(
        llm=llm,
        title="タイトル",
        lead="リード",
        body="本文",
        log_dir=tmp_path,
    )

    assert result["status"] == "failed"
    assert len(result["variants"]) == 2
    assert all(item["status"] == "failed" for item in result["variants"])
    assert all(item["retry_count"] == 1 for item in result["variants"])
    assert successful_image_paths(result) == []
    assert (tmp_path / "latest.json").exists()


def test_generate_blog_images_skips_retry_for_non_recoverable_error(tmp_path) -> None:
    class _AuthFailureLLM(_FakeLLM):
        def generate_images(self, prompt, **kwargs):  # type: ignore[no-untyped-def]
            self.image_calls.append((prompt, kwargs))
            raise RuntimeError("authentication failed: invalid API key")

    llm = _AuthFailureLLM()

    result = generate_blog_images_for_article(
        llm=llm,
        title="タイトル",
        lead="リード",
        body="本文",
        log_dir=tmp_path,
    )

    assert result["status"] == "failed"
    assert len(llm.image_calls) == 2
    assert all(item["retry_count"] == 0 for item in result["variants"])
    assert all(not item["retry_prompt"] for item in result["variants"])
    assert successful_image_paths(result) == []
