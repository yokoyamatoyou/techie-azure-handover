from note.note_writer_core_message_helpers import (
    _build_core_message_helper_text,
    _build_core_message_placeholder,
    _requires_core_message_input,
)


def test_build_core_message_placeholder_preserves_existing_priority() -> None:
    assert (
        _build_core_message_placeholder("branding", "company_introduction", "trust")
        == "例: 事業内容と運用支援の姿勢を根拠付きで伝える"
    )
    assert (
        _build_core_message_placeholder("announcement", "", "trust")
        == "例: 変更点と必要な対応を迷わず把握できるようにする"
    )
    assert (
        _build_core_message_placeholder("case_study", "", "trust")
        == "例: どこで迷い、何を変え、どの条件で再現できるかを伝える"
    )
    assert (
        _build_core_message_placeholder("branding", "", "trust")
        == "例: 判断材料と根拠が自然に伝わるようにする"
    )
    assert (
        _build_core_message_placeholder("")
        == "例: 初期設定の負担を減らし、導入判断を進めやすくする価値を伝える"
    )


def test_build_core_message_helper_text_preserves_existing_priority() -> None:
    assert (
        _build_core_message_helper_text("branding", "company_introduction", "trust")
        == "※会社紹介では必須です。事業内容の説明ではなく、この会社の何を伝え切るかを1文で入れてください。"
    )
    assert (
        _build_core_message_helper_text("announcement", "", "trust")
        == "※お知らせで目的を選んだ場合に入力してください。変更点の要約ではなく、読後に何を迷わせないかを1文で入れます。"
    )
    assert (
        _build_core_message_helper_text("case_study", "", "trust")
        == "※事例で目的を選んだ場合に入力してください。成功談ではなく、読者に残す学びや再現条件を1文で入れます。"
    )
    assert (
        _build_core_message_helper_text("branding", "", "trust")
        == "※ブランド記事で目的を選んだ場合に入力してください。紹介文全体で押し出す判断軸を1文で入れます。"
    )
    assert (
        _build_core_message_helper_text("explanatory_article", "", "")
        == "※核メッセージは、ブランド / 事例 / お知らせで目的を選んだ場合だけ表示します。"
    )


def test_requires_core_message_input_preserves_existing_requiredness() -> None:
    assert _requires_core_message_input("branding", "trust")
    assert _requires_core_message_input("case_study", "learning")
    assert _requires_core_message_input("announcement", "notice")
    assert not _requires_core_message_input("branding", "auto")
    assert not _requires_core_message_input("branding", "")
    assert not _requires_core_message_input("explanatory_article", "trust")
