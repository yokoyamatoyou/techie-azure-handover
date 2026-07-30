from app.services.local_draft_renderer import render_claim_sentence, render_local_draft
from app.services.style_postprocessor import postprocess_style


def test_render_claim_sentence_completes_heading_like_fragments():
    assert render_claim_sentence("前処理から後処理まで一貫対応") == "前処理から後処理まで一貫対応しています。"
    assert render_claim_sentence("データ活用に関するご相談") == "データ活用に関するご相談を受けています。"
    assert render_claim_sentence("RPAとデータエントリの総合力") == "RPAとデータエントリの総合力を強みとしています。"
    assert (
        render_claim_sentence("データ活用の目的はあるがやり方がわからない")
        == "データ活用の目的はあるものの、進め方が分からないという相談に対応しています。"
    )
    assert (
        render_claim_sentence("データの集計・収集から分析まで一手に任せたい")
        == "データの集計・収集から分析まで任せたいという相談にも対応しています。"
    )


def test_render_claim_sentence_aligns_narrator_in_supported_sentence():
    assert (
        render_claim_sentence("弊社は「親切・丁寧」をモットーにしています。", narrator="私たち")
        == "私たちは「親切・丁寧」をモットーにしています。"
    )


def test_render_local_draft_does_not_start_with_meta_source_sentence():
    brief = {
        "article_brief": {
            "narrator": "私たち",
            "sections": [
                {
                    "heading": "私たちについて",
                    "assigned_claim_ids": ["C001"],
                }
            ],
        }
    }
    pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {
                    "claim_id": "C001",
                    "preferred_expression": "京都随一のデータ入力支援・分析センター",
                }
            ]
        }
    }

    draft = render_local_draft(brief, pack)

    assert "公開・提供されたソース" not in draft
    assert "私たちは京都で" in draft


def test_render_local_draft_keeps_exactly_one_h1_before_section_headings():
    brief = {
        "article_brief": {
            "genre_id": "comparison_guide",
            "narrator": "私たち",
            "sections": [
                {"heading": "選ぶ前に整理したいこと", "assigned_claim_ids": ["C001"]},
                {"heading": "比較するときの見方", "assigned_claim_ids": ["C002"]},
                {"heading": "確認しておきたいポイント", "assigned_claim_ids": ["C003"]},
            ],
        }
    }
    pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "preferred_expression": "料金体系を確認する"},
                {"claim_id": "C002", "preferred_expression": "対応範囲を比較する"},
                {"claim_id": "C003", "preferred_expression": "相談方法を見る"},
            ]
        }
    }

    draft = render_local_draft(brief, pack)
    lines = draft.splitlines()
    h1_lines = [line for line in lines if line.startswith("# ") and not line.startswith("## ")]
    h2_lines = [line for line in lines if line.startswith("## ")]

    assert h1_lines == ["# 選び方を整理する"]
    assert h2_lines == [
        "## 選ぶ前に整理したいこと",
        "## 比較するときの見方",
        "## 確認しておきたいポイント",
    ]
    assert draft.count("選ぶ前に整理したいこと") == 1
    assert draft.count("比較するときの見方") == 1
    assert draft.count("確認しておきたいポイント") == 1


def test_style_postprocessor_does_not_create_tokoro_desu_ending():
    text = "# 見出し\n\n私たちは支援しています。相談を受けています。提案します。"

    edited = postprocess_style(text)

    assert "しているところです" not in edited
    assert "する段階です" not in edited
    assert "ていく流れです" not in edited


def test_style_postprocessor_varies_late_half_masu_endings_with_safe_general_forms():
    text = (
        "# 見出し\n\n"
        "私たちは食材を届けています。"
        "商品を扱っています。"
        "理念も案内されています。"
        "情報が掲載されています。"
        "構成が見やすくなります。"
        "価値が伝わります。"
    )

    edited = postprocess_style(text)

    assert "掲載されている内容です。" in edited
    assert "見やすい形です。" in edited or "伝わる部分です。" in edited
