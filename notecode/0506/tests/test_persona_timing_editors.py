from app.services.global_consistency_editor import run_global_consistency_editor
from app.services.opening_editor import run_opening_editor


def _brief() -> dict:
    return {
        "article_brief": {
            "narrator": "私たち",
            "style_profile_id": "note_hatena_owned_media_soft",
            "editor_profile_id": "note_hatena_structural_editor",
        }
    }


def _knowledge_pack() -> dict:
    return {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {
                    "claim_id": "C001",
                    "preferred_expression": "私たち京都工業は京都市伏見稲荷大社のお膝元で1885（明治18）年に創業。",
                },
                {
                    "claim_id": "C002",
                    "preferred_expression": "データ入力やデジタル化を支援しています。",
                },
            ]
        }
    }


def _price_knowledge_pack() -> dict:
    return {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {
                    "claim_id": "C001",
                    "preferred_expression": "名前6円、住所10円、名簿・名刺情報の入力は1セットあたり38円（税別）です。",
                }
            ]
        }
    }


def _route_v_brief() -> dict:
    return {
        "article_brief": {
            "narrator": "私たち",
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "source_shape": "table_or_list",
            "source_use_mode": "representative",
            "paragraph_function_plan": [
                "導入: 見に来ただけの読者が読み続ける理由を、source-backedな具体から作る。"
            ],
            "sections": [{"section_id": "S1", "assigned_claim_ids": ["C001"]}],
        }
    }


def _route_v_reader_hook_brief() -> dict:
    brief = _route_v_brief()
    brief["article_brief"].update(
        {
            "interest_hook": "料金表をただ並べず、どんな依頼単位で考えればよいかが見えるように始める。",
            "self_authored_angle": "私たちは、料金を単なる一覧ではなく、依頼内容を整理するための目安として伝える。",
            "reading_reward": "全部の項目を覚えなくても、代表的な依頼単位と相談前に見る観点が分かる。",
            "sections": [
                {
                    "section_id": "S1",
                    "heading": "データ入力サービスの料金体系について",
                    "assigned_claim_ids": ["C001"],
                }
            ],
        }
    )
    return brief


def _first_body(text: str) -> str:
    for block in [part.strip() for part in text.strip().split("\n\n") if part.strip()]:
        if not block.startswith("#"):
            return block
    return ""


def test_opening_editor_replaces_meta_or_flat_opening_with_source_based_opening():
    text = "# 私たちについて\n\n私たちは、公開・提供されたソースに基づいて内容を整理します。\n\n本文です。"

    result = run_opening_editor(text, _brief(), _knowledge_pack())

    assert result.report["editor_profile_id"] == "note_hatena_opening_editor"
    assert "公開・提供されたソース" not in result.text
    assert "京都・伏見稲荷大社のお膝元" in result.text
    assert result.report["checks"]["opening_uses_narrator"] is True


def test_opening_editor_keeps_v1_replacement_even_when_first_paragraph_has_numbers():
    text = "# 料金\n\n私たちは、名前6円、住所10円、1セット38円を目安として掲載しています。\n\n本文です。"

    result = run_opening_editor(text, _brief(), _price_knowledge_pack())

    assert result.report["changed"] is True
    assert result.report["route_v_opening_preserved"] is False
    assert _first_body(result.text) == "私たちの取り組みを、少し具体的に紹介します。"


def test_opening_editor_preserves_route_v_source_backed_first_paragraph():
    text = "# 料金\n\n私たちは、名前6円、住所10円、1セット38円を目安として掲載しています。\n\n本文です。"

    result = run_opening_editor(text, _route_v_brief(), _price_knowledge_pack())

    assert result.report["changed"] is False
    assert result.report["route_v_opening_preserved"] is True
    assert result.report["route_v_opening_preserve_reason"] == "route_v_source_backed_first_paragraph"
    assert _first_body(result.text) == "私たちは、名前6円、住所10円、1セット38円を目安として掲載しています。"


def test_opening_editor_preserves_route_v_reader_oriented_source_hook_without_numbers():
    text = (
        "# 料金\n\n"
        "「どこまで頼めば、どのくらいの料金になるのか」。"
        "私たちはデータ入力サービスの料金を、単なる一覧ではなく、"
        "依頼内容を整理するための目安としてまとめています。\n\n"
        "本文です。"
    )

    result = run_opening_editor(text, _route_v_reader_hook_brief(), _price_knowledge_pack())

    assert result.report["changed"] is False
    assert result.report["route_v_opening_preserved"] is True
    assert _first_body(result.text).startswith("「どこまで頼めば、どのくらいの料金になるのか」。")


def test_opening_editor_still_replaces_route_v_generic_first_paragraph():
    text = "# 料金\n\n私たちの取り組みについて紹介します。\n\n本文です。"

    result = run_opening_editor(text, _route_v_brief(), _price_knowledge_pack())

    assert result.report["changed"] is True
    assert result.report["route_v_opening_preserved"] is False
    assert _first_body(result.text) == "私たちの取り組みを、少し具体的に紹介します。"


def test_opening_editor_still_replaces_route_v_meta_first_paragraph():
    text = "# 料金\n\nこの記事では、内容をわかりやすく説明します。\n\n本文です。"

    result = run_opening_editor(text, _route_v_reader_hook_brief(), _price_knowledge_pack())

    assert result.report["changed"] is True
    assert result.report["route_v_opening_preserved"] is False
    assert _first_body(result.text) == "私たちの取り組みを、少し具体的に紹介します。"


def test_opening_editor_preserves_route_v_non_generic_hook_without_brief_features():
    text = (
        "# 料金\n\n"
        "どこまで考えればよいのか。私たちは読者に向けて、考え方をやさしく整理しています。\n\n"
        "本文です。"
    )

    result = run_opening_editor(text, _route_v_reader_hook_brief(), _price_knowledge_pack())

    assert result.report["changed"] is False
    assert result.report["route_v_opening_preserved"] is True
    assert result.report["route_v_opening_preserve_reason"] == "route_v_non_generic_first_paragraph"
    assert _first_body(result.text).startswith("どこまで考えればよいのか。")


def test_opening_editor_preserves_route_v_153638_question_fixture():
    first_body = (
        "「どこまで頼めば、どのくらいの料金になるのか」。"
        "私たちはデータ入力サービスの料金を、単なる一覧ではなく、"
        "依頼内容を整理するための目安としてまとめています。"
        "料金表は複雑に見えるかもしれませんが、"
        "必要な情報単位ごとに基準が決まっているため、"
        "ご依頼前の判断材料としてご活用いただけます。"
    )
    text = f"# 料金\n\n{first_body}\n\n本文です。"

    result = run_opening_editor(text, _route_v_reader_hook_brief(), _price_knowledge_pack())

    assert result.report["changed"] is False
    assert result.report["route_v_opening_preserved"] is True
    assert _first_body(result.text) == first_body


def test_opening_editor_preserves_route_v_161036_run01_fixture():
    first_body = (
        "私たちナレッジデータサービス株式会社では、"
        "データ入力業務をどのような単位で依頼できるのか、"
        "またその料金がどのように設定されているのかを分かりやすくご案内しています。 "
        "サービスごとに細かい料金表が用意されていますが、"
        "依頼する際に代表的な単位や観点を知っておくことで、"
        "全ての項目を暗記しなくても検討の目安になります。"
    )
    text = f"# 料金\n\n{first_body}\n\n本文です。"

    result = run_opening_editor(text, _route_v_reader_hook_brief(), _price_knowledge_pack())

    assert result.report["changed"] is False
    assert result.report["route_v_opening_preserved"] is True
    assert _first_body(result.text) == first_body


def test_opening_editor_preserves_route_v_161036_run02_fixture():
    first_body = (
        "ナレッジデータサービス株式会社でご提供している各種入力・集計サービスの料金体系についてご案内します。 "
        "私たちは、単なる価格の一覧ではなく"
        "「どのような依頼単位で料金が決まるのか」を整理し、"
        "判断材料としてお役立ていただけることを心がけています。"
    )
    text = f"# 料金\n\n{first_body}\n\n本文です。"

    result = run_opening_editor(text, _route_v_reader_hook_brief(), _price_knowledge_pack())

    assert result.report["changed"] is False
    assert result.report["route_v_opening_preserved"] is True
    assert _first_body(result.text) == first_body


def test_global_consistency_editor_reduces_duplicate_motto_and_aligns_voice():
    text = (
        "# 私たちについて\n\n"
        "京都随一のデータ入力支援・分析センターとして事業を行っています。\n\n"
        "「データで可能性を創造する」という言葉を掲げています。\n\n"
        "私たち京都工業は京都市伏見稲荷大社のお膝元で1885（明治18）年に創業。\n\n"
        "京都工業は織機の部品製造会社として創業し130年余り経過しました。\n\n"
        "前処理から後処理まで一貫対応しています。\n\n"
        "RPAとデータエントリの総合力を強みとしています。\n\n"
        "「データで可能性を創造する」という言葉を掲げています。"
    )

    result = run_global_consistency_editor(text, _brief())

    assert result.text.count("データで可能性を創造する") == 1
    assert "京都随一" not in result.text
    assert "京都・伏見稲荷大社のお膝元で歩みを重ねてきました。" in result.text
    assert "私たちは、織機の部品製造会社として創業してから130年余りの歴史があります。" in result.text
    assert "一貫して対応できる体制です。" in result.text
    assert "総合力が強みです。" in result.text
    assert result.report["checks"]["duplicate_motto_reduced"] is True
