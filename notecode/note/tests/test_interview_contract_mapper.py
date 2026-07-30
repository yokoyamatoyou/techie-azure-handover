from __future__ import annotations

from note.interview_contract_mapper import build_interview_contract_patch


def test_build_interview_contract_patch_separates_narrative_axis_and_knowledge_lenses() -> None:
    patch = build_interview_contract_patch(
        {"perspective": "利用シーンから価値を伝える"},
        writer_role="ブランド担当として語る",
    )

    assert patch["topic_statement"] == ""
    assert patch["narrative_axis"] == "利用シーンから価値を伝える"
    assert patch["knowledge_lenses"] == ["企業ブランディング担当の知見を混ぜる"]


def test_build_interview_contract_patch_uses_explicit_narrative_axis_fallback() -> None:
    patch = build_interview_contract_patch(
        {
            "perspective": "指定しない",
            "narrative_axis": "判断基準を先に示す",
            "knowledge_lenses": ["法務・コンプライアンスの知見を混ぜる"],
        }
    )

    assert patch["topic_statement"] == ""
    assert patch["narrative_axis"] == "判断基準を先に示す"
    assert patch["knowledge_lenses"] == ["法務・コンプライアンスの知見を混ぜる"]
