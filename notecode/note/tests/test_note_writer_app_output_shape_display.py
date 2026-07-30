from note.note_writer_app_output_shape_display import _describe_note_output_shape


def test_describe_note_output_shape_for_announcement() -> None:
    assert _describe_note_output_shape("announcement") == (
        "出力形: リード→本文。案内文として短くまとめ、目次は入れません。"
    )


def test_describe_note_output_shape_for_daily_story() -> None:
    assert _describe_note_output_shape("daily_story") == (
        "出力形: リード→本文。長くても観察と内省の流れを優先し、目次は入れません。"
    )


def test_describe_note_output_shape_for_branding() -> None:
    assert _describe_note_output_shape("branding") == (
        "出力形: 中量は「この記事でわかること」のみ、かなり長い場合だけ目次を足します。"
    )


def test_describe_note_output_shape_for_case_study() -> None:
    assert _describe_note_output_shape("case_study") == (
        "出力形: 中量は「この記事でわかること」のみ、かなり長い場合だけ目次を足します。"
    )


def test_describe_note_output_shape_falls_back_for_unknown_key() -> None:
    assert _describe_note_output_shape("unknown") == (
        "出力形: 長文では「この記事でわかること」→目次→本文の順に整えます。"
    )
