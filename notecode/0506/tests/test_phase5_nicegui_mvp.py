from pathlib import Path


UI_PATH = Path(__file__).resolve().parents[1] / "app" / "ui" / "main.py"


def test_p5_ui_module_imports_without_starting_server():
    import app.ui.main

    assert app.ui.main.GENRE_OPTIONS["company_service_intro"] == "会社・サービスの紹介記事を書く"
    assert app.ui.main.GENRE_OPTIONS["announcement"] == "お知らせを伝える"
    assert set(app.ui.main.GENRE_OPTIONS) == {
        "market_explanation",
        "company_service_intro",
        "announcement",
        "case_study",
        "comparison_guide",
        "daily_activity",
    }


def test_p5_ui_contains_required_mvp_surfaces():
    source = UI_PATH.read_text(encoding="utf-8")

    assert "手入力ソース" in source
    assert "URLソース" in source
    assert "記事ジャンル" in source
    assert "一人称" in source
    assert "生成を実行" in source
    assert "QA Issues" in source
    assert "Final Article" in source
    assert "artifact" in source
    assert "run_button.on_click" in source
    assert "set_target" not in source
