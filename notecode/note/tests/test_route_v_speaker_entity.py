from __future__ import annotations

from note.route_v_speaker_entity import infer_speaker_entity


def test_infer_speaker_entity_uses_explicit_non_generic_speaker() -> None:
    source_documents = [{"title": "株式会社A 会社概要", "content": "株式会社Aの説明"}]

    assert infer_speaker_entity("株式会社B", source_documents) == "株式会社B"


def test_infer_speaker_entity_extracts_company_name_for_generic_speaker() -> None:
    source_documents = [
        {
            "title": "京都工業株式会社 | 会社概要",
            "content": "私たちはデータ入力や事務処理を行っています。",
        }
    ]

    assert infer_speaker_entity("会社側の担当者", source_documents) == "京都工業株式会社"


def test_infer_speaker_entity_falls_back_to_narrator_when_owner_is_unknown() -> None:
    source_documents = [{"title": "サービス紹介", "content": "私たちは相談前の整理を支援します。"}]

    assert infer_speaker_entity("私たち", source_documents) == "私たち"
