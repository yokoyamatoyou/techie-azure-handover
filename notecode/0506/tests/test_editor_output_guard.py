import json
from pathlib import Path

from app.services.announcement_followthrough import announcement_selected_excerpt_floor_followthrough
from app.services.editor_output_safety import _split_one_sentence, deterministic_targeted_rewrite, guard_editor_output
from app.services.human_visible_surface_gate import check_human_visible_surface


NOTECODE_ROOT = Path(__file__).resolve().parents[2]


def test_editor_output_guard_keeps_previous_article_when_opening_edit_drops_late_sections() -> None:
    before = "\n\n".join(
        [
            "## 京都工業株式会社の歩み",
            "私たちは京都で歩みを重ねてきました。",
            "## データ入力とRPA支援",
            "データ入力、スキャニング、RPA支援に取り組んでいます。",
            "## 品質管理",
            "確認体制を整えています。",
        ]
    )
    after = "私たちは京都で歩みを重ねてきました。"

    assert guard_editor_output("opening_editor", before, after) == before


def test_editor_output_guard_reverts_announcement_generic_local_opening() -> None:
    root = NOTECODE_ROOT / "logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260626_194056"
    article = (root / "generated_article.md").read_text(encoding="utf-8")
    brief = json.loads((root / "rb/r/article_brief.json").read_text(encoding="utf-8"))
    excerpts = json.loads((root / "rb/r/selected_source_excerpts.json").read_text(encoding="utf-8"))
    knowledge_pack = json.loads((root / "rb/r/article_knowledge_pack.json").read_text(encoding="utf-8"))
    before = announcement_selected_excerpt_floor_followthrough(article, brief, excerpts, knowledge_pack)
    after = (root / "rb/r/opening_edited_draft.md").read_text(encoding="utf-8")

    before_codes = {finding["code"] for finding in check_human_visible_surface(before, brief)["human_visible_surface_gate"]["findings"]}
    after_codes = {finding["code"] for finding in check_human_visible_surface(after, brief)["human_visible_surface_gate"]["findings"]}

    assert "generic_local_opening" not in before_codes
    assert "generic_local_opening" in after_codes
    assert guard_editor_output("opening_editor", before, after, brief) == before


def test_editor_output_guard_reverts_announcement_h2_loss_from_latest_validation() -> None:
    root = NOTECODE_ROOT / "logs/0628/route_v_announcement_local_surface_sanitization_one_article_api_validation_after_approval_20260628_105216"
    before = (root / "rb/r/global_consistency_edited_draft.md").read_text(encoding="utf-8")
    after = (root / "rb/r/edited_draft.md").read_text(encoding="utf-8")
    brief = json.loads((root / "rb/r/article_brief.json").read_text(encoding="utf-8"))

    assert _h2_count_for_test(before) == 2
    assert _h2_count_for_test(after) == 1
    assert guard_editor_output("style_editor", before, after, brief) == before


def test_editor_output_guard_keeps_previous_article_when_editor_returns_review() -> None:
    before = "## 見出し\n\n私たちはデータ入力を支援しています。"
    after = "全体を見ると、現状の2段落の中では大きな矛盾はありません。"

    assert guard_editor_output("structural_editor", before, after) == before


def test_editor_output_guard_accepts_complete_article_edit() -> None:
    before = "## 見出し\n\n私たちはデータ入力を支援しています。"
    after = "## 見出し\n\n私たちはデータ入力やスキャニングを支援しています。"

    assert guard_editor_output("style_editor", before, after) == after


def test_editor_output_guard_reverts_structural_edit_when_floor_reaching_input_drops_below_floor() -> None:
    before = "# 日々の取り組みから\n\n## できごとのきっかけ\n\n" + ("私たちは取り組みを紹介します。" * 80)
    after = "# 日々の取り組みから\n\n## できごとのきっかけ\n\n" + ("私たちは紹介します。" * 50)
    brief = {"article_brief": {"body_length_floor_chars": 1200}}

    assert _body_chars_excluding_headings_for_test(before) >= 1200
    assert _body_chars_excluding_headings_for_test(after) < 1200
    assert guard_editor_output("structural_editor", before, after, brief) == before


def test_editor_output_guard_accepts_subfloor_output_when_input_was_already_below_floor() -> None:
    before = "# 比較の視点\n\n## 選び方\n\n" + ("私たちは整理します。" * 20)
    after = "# 比較の視点\n\n## 選び方\n\n" + ("私たちは比べます。" * 20)
    brief = {"article_brief": {"body_length_floor_chars": 1200}}

    assert _body_chars_excluding_headings_for_test(before) < 1200
    assert _body_chars_excluding_headings_for_test(after) < 1200
    assert guard_editor_output("structural_editor", before, after, brief) == after


def test_editor_output_guard_accepts_floor_preserving_output_for_other_genres() -> None:
    before = "# 比較の視点\n\n## 選び方\n\n" + ("私たちは選定の観点を整理します。" * 80)
    after = "# 比較の視点\n\n## 選び方\n\n" + ("私たちは選定軸と確認点を整理します。" * 80)
    brief = {"article_brief": {"genre_id": "comparison_guide", "body_length_floor_chars": 1200}}

    assert _body_chars_excluding_headings_for_test(before) >= 1200
    assert _body_chars_excluding_headings_for_test(after) >= 1200
    assert guard_editor_output("structural_editor", before, after, brief) == after


def test_editor_output_guard_ignores_floor_guard_when_brief_has_no_floor() -> None:
    before = "# お知らせ\n\n## 概要\n\n" + ("当社からお知らせします。" * 60)
    after = "# お知らせ\n\n## 概要\n\n" + ("当社から伝えます。" * 20)
    brief = {"article_brief": {"genre_id": "announcement"}}

    assert guard_editor_output("structural_editor", before, after, brief) == after


def test_deterministic_targeted_rewrite_splits_overlong_sentence_without_external_llm() -> None:
    text = (
        "## 見出し\n\n"
        "私たちはデータ入力、スキャニング、RPA支援、システム開発、運用管理、"
        "データ収集分析、データ加工、帳票確認、運用設計を組み合わせ、"
        "相談内容に応じて前処理から後処理まで一貫して支援しています。"
    )
    quality = {
        "quality_check": {
            "rewrite_needed": True,
            "issues": [{"type": "sentence_too_long"}],
        }
    }
    brief = {
        "article_brief": {
            "narrator": "私たち",
            "style_edit_policy": {
                "preferred_sentences_per_paragraph": 2,
                "max_sentences_per_paragraph": 3,
                "line_break_policy": "topic_shift_or_two_sentences",
                "subject_omission_policy": "clear_context_only",
                "ending_bucket_policy": "structural_variation",
                "protected_subject_terms": [],
            },
        }
    }

    rewritten = deterministic_targeted_rewrite(text, quality, brief)

    assert "データ加工。帳票確認" in rewritten
    assert rewritten.startswith("## 見出し\n\n")
    assert "データ収集分析" in rewritten


def _body_chars_excluding_headings_for_test(markdown: str) -> int:
    return len(
        "".join(
            "".join(line.split())
            for line in markdown.splitlines()
            if not line.lstrip().startswith("#")
        )
    )


def _h2_count_for_test(markdown: str) -> int:
    return sum(
        1
        for line in markdown.splitlines()
        if line.lstrip().startswith("## ") and not line.lstrip().startswith("### ")
    )


def test_deterministic_targeted_rewrite_splits_overlong_sentence_after_heading_line() -> None:
    text = (
        "## 私たちのサービス領域\n"
        "私たちは、データ入力からスキャニング、システム開発、運用管理、"
        "RPAによる業務効率化支援、データ収集・データ分析、OCR処理、帳票確認、"
        "データ加工、BPO、一般人材派遣まで扱っています。"
    )
    quality = {
        "quality_check": {
            "rewrite_needed": True,
            "issues": [{"type": "sentence_too_long"}],
        }
    }
    brief = {
        "article_brief": {
            "narrator": "私たち",
            "style_edit_policy": {
                "preferred_sentences_per_paragraph": 2,
                "max_sentences_per_paragraph": 3,
                "line_break_policy": "topic_shift_or_two_sentences",
                "subject_omission_policy": "clear_context_only",
                "ending_bucket_policy": "avoid_late_half_bucket_concentration",
                "protected_subject_terms": [],
            },
        }
    }

    rewritten = deterministic_targeted_rewrite(text, quality, brief)

    assert rewritten.startswith("## 私たちのサービス領域\n\n")
    assert "RPAによる業務効率化支援。" in rewritten
    assert "RPAによる業務効率化支援" in rewritten


def test_deterministic_targeted_rewrite_does_not_split_after_continuative_verb() -> None:
    text = (
        "## どんな商品を扱い、どう提案しているか\n\n"
        "私たちの歩みは、1972年4月創立から始まっています。"
        "山陰酸素工業の開発部門による液体窒素を使った急速冷凍食品の開発と、"
        "食品メーカーからの技術指導を経て発足し、"
        "地元日本海の恵みを活かした冷凍加工食品の製造販売と食品メーカー製品の販売を始めました。"
    )
    quality = {
        "quality_check": {
            "rewrite_needed": True,
            "issues": [{"type": "sentence_too_long"}],
        }
    }
    brief = {"article_brief": {"narrator": "私たち"}}

    rewritten = deterministic_targeted_rewrite(text, quality, brief)

    assert "発足し。" not in rewritten
    assert "発足しました。地元日本海" in rewritten
    assert "冷凍加工食品の製造販売" in rewritten


def test_deterministic_targeted_rewrite_does_not_split_quoted_event_without_predicate() -> None:
    text = (
        "## 採用情報とさんれい情報\n\n"
        "2026.06.16の採用情報では6/27（土）「マイナビ インターンシップ＆キャリア発見フェア（松江会場）」、"
        "2026.06.08の採用情報では6/20（土）「タイプ診断×謎解き とっとりインターンフェスタin大阪」が案内されています。"
    )
    quality = {
        "quality_check": {
            "rewrite_needed": True,
            "issues": [{"type": "sentence_too_long"}],
        }
    }
    brief = {"article_brief": {"narrator": "私たち"}}

    rewritten = deterministic_targeted_rewrite(text, quality, brief)

    assert "（松江会場）」。" not in rewritten
    assert "（松江会場）」、2026.06.08" in rewritten


def test_split_one_sentence_recursively_splits_remaining_safe_segments() -> None:
    sentence = (
        "私たちはデータ入力、スキャニング、RPA支援、システム開発、運用管理、"
        "データ収集分析、データ加工、帳票確認、運用設計、品質確認、納品管理、保守確認を組み合わせています。"
    )

    split = _split_one_sentence(sentence, 35)

    assert len(split) >= 3
    assert all(part.endswith("。") for part in split)
    assert "発足し。" not in "".join(split)


def test_split_one_sentence_followthrough_completes_need_response_boundary() -> None:
    sentence = (
        "「自社製品をもっと魅力的に撮りたい」というニーズに応え、"
        "身近にあるクリップライトやホームセンターで揃う資材を活用した撮影テクニックの習得を目標に、"
        "「講義」と「実技」の二部構成で学んでいきました。"
    )

    split = _split_one_sentence(sentence, 90)

    assert split[0] == "「自社製品をもっと魅力的に撮りたい」というニーズに応えました。"
    assert all(len(part.rstrip("。！？!?")) <= 90 for part in split)


def test_split_one_sentence_followthrough_completes_instructor_boundary() -> None:
    sentence = (
        "当センターの商品開発支援班の職員が講師となり、"
        "身近にあるクリップライトや資材を使って物撮り（商品撮影）を行う手法を学ぶ"
        "「【初心者向け】 手軽に物撮り（商品撮影）ワークショップ」を開催しました。"
    )

    split = _split_one_sentence(sentence, 90)

    assert "当センターの商品開発支援班の職員が講師となりました。" in split
    assert all(len(part.rstrip("。！？!?")) <= 90 for part in split)


def test_split_one_sentence_followthrough_completes_suru_event_boundary() -> None:
    sentence = (
        "公正取引委員会は、我が国の生成AI関連市場における公正かつ自由な競争環境を維持し、"
        "生成AIの持続的な進展を確保することにより、"
        "更なるイノベーションを生み出す観点から、また、"
        "生成AIを健全な形で経済社会に実装する観点も踏まえ、"
        "生成AI関連市場の実態を把握するための調査を開始。"
    )

    split = _split_one_sentence(sentence, 90)

    assert any(part.endswith("生成AIの持続的な進展を確保します。") for part in split)
    assert all(len(part.rstrip("。！？!?")) <= 90 for part in split)


def test_deterministic_targeted_rewrite_reduces_repeated_model_frequent_word() -> None:
    text = "## 体制で支える安心感\n\n私たちはデータ業務と自動化の両方を支える姿を紹介します。"
    quality = {
        "quality_check": {
            "rewrite_needed": True,
            "issues": [{"type": "model_frequent_word"}],
            "stylometry": {"model_frequent_words": [{"term": "支える", "count": 2, "risk": "medium"}]},
        }
    }
    brief = {
        "article_brief": {
            "narrator": "私たち",
            "style_edit_policy": {
                "preferred_sentences_per_paragraph": 2,
                "max_sentences_per_paragraph": 3,
                "line_break_policy": "topic_shift_or_two_sentences",
                "subject_omission_policy": "clear_context_only",
                "ending_bucket_policy": "avoid_late_half_bucket_concentration",
                "protected_subject_terms": [],
            },
        }
    }

    rewritten = deterministic_targeted_rewrite(text, quality, brief)

    assert rewritten.count("支える") == 1
    assert "両方を担う姿" in rewritten
