from __future__ import annotations

from pathlib import Path


KOTOMEGANE_ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (KOTOMEGANE_ROOT / path).read_text(encoding="utf-8")


def test_mobile_top_navigation_has_single_row_compact_contract() -> None:
    app_source = _source("ui/styles.py")

    assert 'top-shell top-nav-shell items-center px-5 py-3' in app_source
    assert 'top-nav-layout w-full max-w-7xl' in app_source
    assert 'top-nav-links items-center gap-3 flex-wrap' in app_source
    assert ".top-nav-layout {" in app_source
    assert "flex-wrap: nowrap !important;" in app_source
    assert ".top-nav-links .nav-link {" in app_source
    assert "font-size: 11px !important;" in app_source
    assert ".top-nav-layout .top-logo-wordmark-image" in app_source


def test_result_action_and_saved_condition_surfaces_avoid_empty_desktop_columns() -> None:
    styles_source = _source("ui/styles.py")

    assert ".settings-overview-row {" in styles_source
    assert "flex-direction: column !important;" in styles_source
    assert "grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.95fr);" in styles_source
    assert ".input-main-grid > .input-side-column > .input-action-card" in styles_source
    assert "grid-column: 1 / -1;" in styles_source
    assert ".settings-saved-card" in styles_source
    assert "min-width: 0 !important;" in styles_source


def test_cross_suite_context_links_keep_active_link_affordance_in_readonly_mode() -> None:
    page_source = _source("app.py")
    styles_source = _source("ui/styles.py")

    assert page_source.count('"hero-context-link text-[13px]"') == 2
    assert ".hero-context-link {" in styles_source
    assert "color: #9A3412 !important;" in styles_source
    assert "text-decoration: underline;" in styles_source
    assert ".hero-context-link:hover," in styles_source
