from note.note_writer_interview_question_renderer import normalize_interview_question_items


def test_normalize_interview_question_items_maps_answer_keys_and_filters_options() -> None:
    items = normalize_interview_question_items(
        [
            {
                "field": "audience_profile",
                "question_template": "誰向けですか",
                "options": [
                    {"value": "owner", "label": "経営者", "description": "意思決定者"},
                    {"value": "", "label": "空値"},
                    {"value": "staff", "label": ""},
                ],
            },
            {
                "field": "free_field",
                "question_template": "自由入力",
                "options": [],
            },
        ]
    )

    assert items[0]["answer_key"] == "target"
    assert items[0]["options"] == [
        {"value": "owner", "label": "経営者", "description": "意思決定者"}
    ]
    assert items[1]["answer_key"] == "free_field"


def test_normalize_interview_question_items_defaults_blank_field_to_message() -> None:
    items = normalize_interview_question_items([{"field": "", "question_template": "補足"}])

    assert items[0]["answer_key"] == "message"
    assert items[0]["options"] == []
