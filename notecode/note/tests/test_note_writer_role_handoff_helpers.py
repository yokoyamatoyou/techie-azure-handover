from note.note_writer_role_handoff_helpers import (
    WRITER_ROLE_AUTO_LABEL,
    _get_default_writer_role_label,
    _get_writer_role_options,
    _predict_pronoun_hint,
)


def test_writer_role_options_use_injected_custom_genre_lookup() -> None:
    def lookup(key: str) -> object:
        if key == "custom_ai":
            return {"meta": {"base_template": "ai"}}
        return None

    options = _get_writer_role_options("custom_ai", custom_genre_lookup=lookup)
    hint = _predict_pronoun_hint("custom_ai", "", custom_genre_lookup=lookup)

    assert options[0] == WRITER_ROLE_AUTO_LABEL
    assert "解説担当として語る" in options
    assert "私" in hint


def test_writer_role_options_fall_back_without_custom_genre_lookup() -> None:
    options = _get_writer_role_options("custom_unknown", custom_genre_lookup=None)

    assert options == [
        WRITER_ROLE_AUTO_LABEL,
        "編集担当として語る",
        "運営担当として語る",
        "専門家として語る",
    ]
    assert _get_default_writer_role_label("custom_unknown", custom_genre_lookup=None) == "編集担当として語る"


def test_writer_role_options_fall_back_when_custom_genre_lookup_fails() -> None:
    def failing_lookup(_key: str) -> object:
        raise RuntimeError("lookup unavailable")

    options = _get_writer_role_options("custom_unknown", custom_genre_lookup=failing_lookup)

    assert options == [
        WRITER_ROLE_AUTO_LABEL,
        "編集担当として語る",
        "運営担当として語る",
        "専門家として語る",
    ]
