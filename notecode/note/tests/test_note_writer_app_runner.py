from pathlib import Path

from note.note_writer_app_runner import (
    is_headless_enabled,
    resolve_available_port,
    run_note_writer_app,
)


def test_resolve_available_port_keeps_first_free_port() -> None:
    checked: list[int] = []

    def port_in_use(_host: str, port: int) -> bool:
        checked.append(port)
        return port in {8080, 8081}

    messages: list[str] = []
    port = resolve_available_port(
        host="127.0.0.1",
        start_port=8080,
        port_in_use=port_in_use,
        notify=messages.append,
    )

    assert port == 8082
    assert checked == [8080, 8081, 8082]
    assert messages == [
        "[INFO] Port 8080 is in use, trying next...",
        "[INFO] Port 8081 is in use, trying next...",
    ]


def test_is_headless_enabled_accepts_current_truthy_values() -> None:
    assert is_headless_enabled({"HEADLESS": "1"}) is True
    assert is_headless_enabled({"HEADLESS": "true"}) is True
    assert is_headless_enabled({"HEADLESS": "yes"}) is True
    assert is_headless_enabled({"HEADLESS": ""}) is False


def test_run_note_writer_app_passes_existing_ui_run_contract(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    class _FakeUi:
        @staticmethod
        def run(**kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(
        "note.note_writer_app_runner.resolve_available_port",
        lambda *, host, start_port: start_port + 1,
    )

    run_note_writer_app(
        ui_module=_FakeUi,
        static_dir=tmp_path,
        host="127.0.0.1",
        port=18080,
        environ={"HEADLESS": "1", "PORT": "9999"},
    )

    assert calls == [
        {
            "host": "127.0.0.1",
            "port": 18081,
            "title": "コトメイク | TECHIE",
            "favicon": str(tmp_path / "favicon_v2.png"),
            "reload": False,
            "show": False,
        }
    ]
