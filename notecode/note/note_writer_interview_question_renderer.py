"""Interview question card rendering helpers for note_writer_app."""
from __future__ import annotations

from collections.abc import Callable, Iterable, MutableMapping
from typing import Any, Dict, List

from nicegui import ui

from note.note_text_format_helpers import _to_plain_dict, _to_plain_list


_ANSWER_KEY_MAP = {
    "speaker_profile": "writer_role",
    "audience_profile": "target",
    "core_message": "message",
}


def normalize_interview_question_items(question_items: Iterable[Any] | None) -> List[Dict[str, Any]]:
    normalized_items: List[Dict[str, Any]] = []
    for item in question_items or []:
        normalized_item = _to_plain_dict(item)
        option_items = [
            _to_plain_dict(option)
            for option in _to_plain_list(normalized_item.get("options"))
            if str(_to_plain_dict(option).get("value") or "").strip()
            and str(_to_plain_dict(option).get("label") or "").strip()
        ]
        normalized_item["options"] = option_items
        normalized_item["answer_key"] = _ANSWER_KEY_MAP.get(
            str(normalized_item.get("field", "") or ""),
            str(normalized_item.get("field", "") or "") or "message",
        )
        normalized_items.append(normalized_item)
    return normalized_items


def render_interview_question_items(
    question_items: Iterable[Any] | None,
    *,
    interview_answers: MutableMapping[str, Any],
    container: Any,
    on_answer_change: Callable[[], None],
) -> int:
    current_question_items = normalize_interview_question_items(question_items)
    if not current_question_items:
        return 0
    container.clear()
    with container:
        for item in current_question_items:
            answer_key = str(item.get("answer_key") or "message")
            question_text = str(item.get("question_template", "") or item.get("field") or "")
            example_answer = str(item.get("example_answer", "") or "")
            option_items = _to_plain_list(item.get("options"))
            with ui.card().classes("w-full p-3"):
                ui.label(question_text).classes("font-semibold mb-2 w-full").style(
                    "white-space: normal; overflow-wrap: anywhere;"
                )
                if option_items:
                    option_map = {
                        str(option.get("value") or ""): str(option.get("label") or "")
                        for option in option_items
                    }
                    select_field = ui.select(
                        options=option_map,
                        value=str(interview_answers.get(answer_key) or "").strip() or None,
                        label="選択してください",
                    ).classes("w-full").props("outlined stack-label")
                    select_field.bind_value_to(interview_answers, answer_key)
                    select_field.on("update:model-value", lambda _: on_answer_change())
                    for option in option_items:
                        description = str(option.get("description") or "").strip()
                        if description:
                            ui.label(f"{str(option.get('label') or '').strip()}: {description}").classes(
                                "text-xs text-gray-600"
                            )
                else:
                    input_field = ui.input(
                        label="自由入力",
                        placeholder=example_answer or "入力してください",
                    ).classes("w-full").props("outlined stack-label")
                    input_field.bind_value_to(interview_answers, answer_key)
                    input_field.on("update:model-value", lambda _: on_answer_change())
    return len(current_question_items)
