from app.services.structural_editor import run_structural_editor


def _brief(narrator: str = "私たち") -> dict:
    return {
        "article_brief": {
            "narrator": narrator,
            "editor_profile_id": "note_hatena_structural_editor",
            "editor_pass_policy": {
                "focus_late_half": True,
                "split_late_paragraph_over_sentences": 2,
                "align_first_person_to_narrator": True,
                "preserve_facts": True,
                "preserve_numbers_dates_names": True,
                "do_not_add_claims": True,
            },
        }
    }


def test_structural_editor_splits_late_half_long_paragraph_without_changing_facts():
    text = """# 前半

私たちは2018年に創業しました。地域の相談を受けています。

# 後半

初回相談では状況を確認します。確認した内容を整理します。必要な資料を案内します。"""

    result = run_structural_editor(text, _brief())

    assert "初回相談では状況を確認します。確認した内容を整理します。\n\n必要な資料を案内します。" in result.text
    assert "2018年" in result.text
    assert result.report["checks"]["late_half_paragraph_split"] is True
    assert result.report["checks"]["source_grounding_policy_changed"] is False


def test_structural_editor_aligns_first_person_and_third_party_self_terms():
    text = "私たちは相談を受けています。当社は内容を整理します。同社は資料を案内します。"

    result = run_structural_editor(text, _brief("私たち"))

    assert "当社" not in result.text
    assert "同社" not in result.text
    assert result.text.count("私たち") == 3
    assert result.report["checks"]["first_person_aligned"] is True
