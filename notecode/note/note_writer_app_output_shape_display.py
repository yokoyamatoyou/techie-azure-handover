"""Pure display helpers for note output shape labels."""
from __future__ import annotations


def _describe_note_output_shape(article_type_key: str) -> str:
    key = str(article_type_key or "").strip()
    if key == "announcement":
        return "出力形: リード→本文。案内文として短くまとめ、目次は入れません。"
    if key == "daily_story":
        return "出力形: リード→本文。長くても観察と内省の流れを優先し、目次は入れません。"
    if key in {"branding", "case_study"}:
        return "出力形: 中量は「この記事でわかること」のみ、かなり長い場合だけ目次を足します。"
    return "出力形: 長文では「この記事でわかること」→目次→本文の順に整えます。"
