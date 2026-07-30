import json
import logging

from note.note_writer_app_logging import _BenignNiceGUIErrorFilter, _JSONFormatter


def test_json_formatter_keeps_app_log_fields(monkeypatch) -> None:
    monkeypatch.setenv("SERVICE_NAME", "notecode-test")
    formatter = _JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    record = logging.LogRecord(
        name="note.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )

    data = json.loads(formatter.format(record))

    assert data["level"] == "INFO"
    assert data["service"] == "notecode-test"
    assert data["message"] == "hello world"
    assert data["module"] == "test_note_writer_app_logging"
    assert "timestamp" in data


def test_benign_nicegui_filter_drops_parent_slot_noise() -> None:
    filter_ = _BenignNiceGUIErrorFilter()
    noisy = logging.LogRecord(
        name="nicegui",
        level=logging.ERROR,
        pathname=__file__,
        lineno=10,
        msg="The parent slot of the element has been deleted.",
        args=(),
        exc_info=None,
    )
    normal = logging.LogRecord(
        name="nicegui",
        level=logging.ERROR,
        pathname=__file__,
        lineno=11,
        msg="real error",
        args=(),
        exc_info=None,
    )

    assert filter_.filter(noisy) is False
    assert filter_.filter(normal) is True
