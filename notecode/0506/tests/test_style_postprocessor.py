from app.agents.japanese_quality_checker import JapaneseQualityChecker
from app.services.style_postprocessor import postprocess_style


def _brief() -> dict:
    return {
        "article_brief": {
            "brief_id": "b1",
            "genre_id": "company_service_intro",
            "persona_id": "in_house_brand_blog_editor",
            "writer_role": "in_house_brand_blog_editor",
            "viewpoint_mode": "self_perspective",
            "target_reader": "読者",
            "article_goal": "紹介",
            "narrator": "私たち",
            "qa_policy_id": "self_perspective_blog_default",
            "style_profile_id": "note_hatena_owned_media_soft",
            "style_edit_policy": {
                "preferred_sentences_per_paragraph": 2,
                "max_sentences_per_paragraph": 3,
                "line_break_policy": "topic_shift_or_two_sentences",
                "subject_omission_policy": "clear_context_only",
                "ending_bucket_policy": "structural_variation",
                "protected_subject_terms": ["年", "月", "日", "円", "担当"],
            },
            "target_length_chars": 1200,
            "section_count": 2,
            "source_thickness": "medium",
            "claim_allocation": [],
            "sections": [
                {
                    "section_id": "s1",
                    "heading": "見出し",
                    "purpose": "確認",
                    "assigned_claim_ids": [],
                    "main_subject": "私たち",
                    "discourse_rules": [],
                }
            ],
            "style_rules": [],
            "forbidden_viewpoint_terms": ["同社"],
            "editorial_bridge_candidates": [
                {
                    "bridge_id": "B001",
                    "kind": "business_history",
                    "section_id": "s1",
                    "source_claim_ids": ["C001"],
                    "angle": "沿革を現在の事業理解につなぐ",
                    "usage_note": "事実断定にしない",
                },
                {
                    "bridge_id": "B002",
                    "kind": "service_use_case",
                    "section_id": "s2",
                    "source_claim_ids": ["C002"],
                    "angle": "サービスを相談前の観点につなぐ",
                    "usage_note": "事実断定にしない",
                },
            ],
            "config_refs": [],
            "persona_refs": [],
        }
    }


def test_style_postprocessor_uses_profile_for_line_breaks_and_safe_subject_omission():
    text = """# 私たちについて

私たちは、公開・提供されたソースに基づいて内容を整理します。

私たちは2018年に創業しました。

私たちは地域の相談を受けています。

担当者が選択肢を説明します。"""

    result = postprocess_style(text, _brief())

    assert "私たちは2018年に創業しました。" in result
    assert "地域の相談を受けています。" in result
    assert "私たちは地域の相談を受けています。" not in result
    assert "内容を整理します。私たちは2018年に創業しました。" in result


def test_style_postprocessor_reduces_rhythm_without_phrase_specific_replacements():
    text = """# 私たちについて

私たちは、公開・提供されたソースに基づいて内容を整理します。

私たちは2018年に創業しました。

私たちは地域の相談を受けています。

担当者が選択肢を説明します。

必要な情報を確認しながら、無理のない形で相談につなげます。"""

    processed = postprocess_style(text, _brief())
    quality = JapaneseQualityChecker().check(processed, _brief(), {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "paragraph_rhythm_monotony" not in issue_types
    assert "流れです。" not in processed
    assert "つなげます。" in processed


def test_style_postprocessor_accepts_late_half_bucket_policy_alias():
    brief = _brief()
    brief["article_brief"]["style_edit_policy"]["ending_bucket_policy"] = "avoid_late_half_bucket_concentration"
    text = """# 信頼性

私たちは、データ入力精度で信頼を得ています。

チェック体制を整えています。

情報セキュリティ方針を策定し、プライバシーマークを取得しています。

健康経営優良法人にも認定されています。

京都から全国へ対応しています。"""

    processed = postprocess_style(text, brief)
    quality = JapaneseQualityChecker().check(processed, brief, {"article_knowledge_pack": {"confirmed_facts": []}})
    issue_types = {issue["type"] for issue in quality["quality_check"]["issues"]}

    assert "ending_bucket_monotony" not in issue_types
    assert "プライバシーマークを取得済みです。" in processed
    assert "健康経営優良法人にも認定済みです。" in processed


def test_style_postprocessor_processes_body_after_heading_without_blank_line():
    text = """## 見出し
私たちは地域の相談を受けています。

私たちは業務の確認を続けています。"""

    processed = postprocess_style(text, _brief())

    assert processed.startswith("## 見出し\n\n")
    assert "## 見出し\n私たちは" not in processed
    assert "業務の確認を続けています。" in processed


def test_style_postprocessor_removes_first_person_title_tail_only():
    text = """# 京都工業株式会社の歴史・事業・体制を、私たちの視点でご紹介します

## 私たちが大切にしていること

私たちは地域の相談を受けています。"""

    processed = postprocess_style(text, _brief())

    assert processed.startswith("# 京都工業株式会社の歴史・事業・体制\n\n")
    assert "私たちの視点でご紹介します" not in processed.splitlines()[0]
    assert "## 私たちが大切にしていること" in processed
    assert "私たちは地域の相談を受けています。" in processed


def test_style_postprocessor_removes_bare_first_person_title_tail_only():
    text = """# 京都工業株式会社とは？歴史・事業・信頼性を私たちの視点でご紹介

## 私たちの視点でご紹介

本文では私たちの視点を残します。"""

    processed = postprocess_style(text, _brief())

    assert processed.splitlines()[0] == "# 京都工業株式会社とは？歴史・事業・信頼性"
    assert "## 私たちの視点でご紹介" in processed
    assert "本文では私たちの視点を残します。" in processed


def test_style_postprocessor_removes_bare_first_person_title_tail_from_viewpoint_variant():
    text = "# 京都工業株式会社とは？歴史・事業・信頼性を私たちの視点から紹介"

    processed = postprocess_style(text, _brief())

    assert processed.splitlines()[0] == "# 京都工業株式会社とは？歴史・事業・信頼性"


def test_style_postprocessor_keeps_original_when_title_sanitizer_would_empty_h1():
    text = "# 私たちの視点でご紹介"

    processed = postprocess_style(text, _brief())

    assert processed.splitlines()[0] == "# 私たちの視点でご紹介"


def test_style_postprocessor_does_not_add_bridge_when_missing():
    text = """# 京都工業株式会社の歩みと事業

## 沿革

私たちは1968年にデータエントリー業務へ転換しました。

## サービス

データ入力やスキャニングに対応しています。"""

    processed = postprocess_style(text, _brief())

    assert "現在の事業に至る背景が含まれています。" not in processed
    assert "相談前に確認したい業務範囲が表れています。" not in processed
    assert "私たちは1968年にデータエントリー業務へ転換しました。" in processed
    assert "データ入力やスキャニングに対応しています。" in processed


def test_style_postprocessor_removes_existing_low_density_bridge_language():
    text = """# 京都工業株式会社の歩みと事業

## 沿革

沿革は現在の事業を知る手がかりになります。

私たちは1968年にデータエントリー業務へ転換しました。"""

    processed = postprocess_style(text, _brief())

    assert "手がかりになります" not in processed
    assert "現在の事業に至る背景が含まれています。" not in processed
    assert "私たちは1968年にデータエントリー業務へ転換しました。" in processed


def test_style_postprocessor_removes_low_density_reader_meta_sentences_but_keeps_facts():
    text = """# 京都工業株式会社の会社紹介

## 事業

まずは「どんな会社で、何を支えるのか」を知りたい方に、私たちの輪郭をお伝えしたいと思います。

京都工業株式会社は、データ入力・スキャニング・RPA支援を提供しています。

紙資料をデジタル化して使いやすい形にする場面を思い浮かべると、私たちのサービスのつながりが見えやすくなります。

データ入力・スキャニングでは、紙資料をデジタル化し、希望するデータ形式で納品しています。"""

    processed = postprocess_style(text, _brief())

    assert "輪郭をお伝えしたい" not in processed
    assert "思い浮かべると" not in processed
    assert "京都工業株式会社は、データ入力・スキャニング・RPA支援を提供しています。" in processed
    assert "希望するデータ形式で納品しています。" in processed


def test_style_postprocessor_keeps_source_backed_entrypoint_sentences():
    text = """# kintoneの紹介

## 使い始める単位

アプリの作成方法には、ドラッグ＆ドロップ、AIチャット、テンプレート、Excel読み込みなど複数の入口があります。
権限と連携は別の機能ですが、運用の入口と出口をそろえる話として読むと全体の流れが見えてきます。"""

    processed = postprocess_style(text, _brief())

    assert "複数の入口があります" in processed
    assert "入口と出口をそろえる" in processed


def test_style_postprocessor_preserves_floor_critical_reader_meta_bridge():
    brief = _brief()
    text = """# さんれいフーズの会社紹介

## 商品と提案

商品ページと展示会の案内を並べると、扱う食材と提案の方向が見えやすくなります。

私たちは、業務用カニ加工品、業務用冷凍調理品、量販店水産売り場向け商品を扱っています。

私たちは総合食品展示会で、取り扱っている食材に加え、お客様のニーズに合わせた新たな食材やメニューをご紹介しています。"""
    brief["article_brief"]["body_length_floor_chars"] = len("".join(text.split())) - 10

    processed = postprocess_style(text, brief)

    assert "見えやすくなります" in processed
    assert "私たちは総合食品展示会で" in processed
    assert len("".join(processed.split())) >= brief["article_brief"]["body_length_floor_chars"]


def test_style_postprocessor_removes_low_density_reader_meta_when_floor_safe():
    brief = _brief()
    brief["article_brief"]["body_length_floor_chars"] = 1
    text = """# 京都工業株式会社の会社紹介

## 事業

紙資料をデジタル化して使いやすい形にする場面を思い浮かべると、私たちのサービスのつながりが見えやすくなります。

データ入力・スキャニングでは、紙資料をデジタル化し、希望するデータ形式で納品しています。"""

    processed = postprocess_style(text, brief)

    assert "思い浮かべると" not in processed
    assert "希望するデータ形式で納品しています。" in processed


def test_style_postprocessor_rewrites_company_intro_page_summary_voice():
    text = """# さんれいフーズの会社紹介

## 事業

私たちは、業務用で食材をお使いのお客様に安全安心な食材をお届けすると案内しています。

あわせて、「食の幸せ」は美味しい料理、楽しい会食、長く食事を続けられることまで含むと案内しています。

私たちは「食」を通して山陰の魅力を全国に発信しているとも案内しています。"""

    processed = postprocess_style(text, _brief())

    assert "と案内しています" not in processed
    assert "安全安心な食材をお届けしています。" in processed
    assert "まで含むという考え方です。" in processed
    assert "山陰の魅力を全国に発信しています。" in processed


def test_style_postprocessor_keeps_page_summary_voice_outside_company_intro():
    brief = _brief()
    brief["article_brief"]["genre_id"] = "market_explanation"
    text = "# 市場の解説\n\n資料では、新しい利用場面が広がると案内しています。"

    processed = postprocess_style(text, brief)

    assert "広がると案内しています。" in processed
