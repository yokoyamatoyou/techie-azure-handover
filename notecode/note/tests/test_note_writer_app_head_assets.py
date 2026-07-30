from __future__ import annotations

from note import note_writer_app_head_assets as head_assets


class _FakeApp:
    def __init__(self) -> None:
        self.calls = []

    def colors(self, **kwargs) -> None:
        self.calls.append(kwargs)


class _FakeUi:
    def __init__(self) -> None:
        self.calls = []

    def add_head_html(self, html: str, *, shared: bool = False) -> None:
        self.calls.append({"html": html, "shared": shared})


def test_register_note_writer_app_colors_preserves_theme_palette() -> None:
    app = _FakeApp()

    head_assets.register_note_writer_app_colors(app)

    assert app.calls == [head_assets.APP_THEME_COLORS]


def test_register_note_writer_app_base_head_html_registers_shared_css_block() -> None:
    ui = _FakeUi()

    head_assets.register_note_writer_app_base_head_html(ui)

    assert ui.calls == [{"html": head_assets.BASE_HEAD_HTML, "shared": True}]
    html = ui.calls[0]["html"]
    assert '<link rel="icon" type="image/png" href="/static/favicon_v2.png">' in html
    assert "fonts.googleapis.com/css2?family=Sora" in html
    assert ".hub-nav" in html
    assert ".hub-nav .hub-nav-sep" in html
    assert "flex-wrap: nowrap;" in html
    assert ".step-track" in html
    assert ".journey-stage-card-active" in html
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in html
    assert ".source-mode-choice-detail" in html
    assert ".source-input-alert" in html
    assert ".input-stage-card > .source-inputs-section" in html
    assert ".input-stage-card > .source-mode-choice-section" in html
    assert "order: 1;" in html


def test_register_note_writer_app_sticky_step_head_html_registers_shared_script_block() -> None:
    ui = _FakeUi()

    head_assets.register_note_writer_app_sticky_step_head_html(ui)

    assert ui.calls == [{"html": head_assets.STICKY_STEP_HEAD_HTML, "shared": True}]
    html = ui.calls[0]["html"]
    assert "<script>" in html
    assert ".sticky-s1" in html
    assert "step-track-active" in html
    assert "setTimeout(initScrollSpy, 450);" in html
