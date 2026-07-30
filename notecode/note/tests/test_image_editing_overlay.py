from PIL import Image

from note.image_editing import (
    TextOverlay,
    _resolve_font_candidates,
    _resolve_overlay_geometry,
    _resolve_overlay_palette,
)


def test_overlay_geometry_supports_grid_positions() -> None:
    img = Image.new("RGB", (1280, 670), color="white")
    overlay = TextOverlay(
        text="比較ポイント",
        position="top_left",
        size="medium",
        color="white",
        with_bar=True,
        font_style="sans",
        background_preset="image",
    )

    geometry = _resolve_overlay_geometry(img, overlay, "")
    report = geometry["balance_report"]

    assert report["balanced"] is True
    assert report["horizontal_position"] == "left"
    assert report["vertical_position"] == "top"
    assert float(report["text_center_offset_x"]) < 0.0
    assert report["text_inside_bar"] is True
    assert report["bar_inside_image"] is True


def test_overlay_geometry_preserves_center_alias() -> None:
    img = Image.new("RGB", (1280, 670), color="white")
    overlay = TextOverlay(
        text="中央タイトル",
        position="top",
        size="medium",
        color="auto",
        with_bar=True,
        font_style="sans",
        background_preset="image",
    )

    geometry = _resolve_overlay_geometry(img, overlay, "")
    report = geometry["balance_report"]

    assert report["balanced"] is True
    assert report["horizontal_position"] == "center"
    assert report["vertical_position"] == "top"
    assert abs(float(report["text_center_offset_x"])) <= 1.0


def test_overlay_palette_supports_explicit_black_and_white() -> None:
    img = Image.new("RGB", (120, 120), color="white")

    white_fill, white_stroke, _white_bar = _resolve_overlay_palette(img, (0, 0, 120, 120), "white")
    black_fill, black_stroke, _black_bar = _resolve_overlay_palette(img, (0, 0, 120, 120), "black")

    assert white_fill == (255, 255, 255)
    assert white_stroke == (0, 0, 0)
    assert black_fill == (0, 0, 0)
    assert black_stroke == (255, 255, 255)


def test_overlay_font_candidates_cover_six_presets() -> None:
    expected_styles = {"sans", "bold", "mincho", "yu_gothic", "yu_mincho", "meiryo"}

    for style in expected_styles:
        candidates = _resolve_font_candidates("", style)
        assert candidates
