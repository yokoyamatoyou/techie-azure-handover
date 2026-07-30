"""Generated-image result panel shell for note_writer_app."""
from __future__ import annotations

from typing import Any, Callable, Mapping

from nicegui import ui

from note.note_writer_app_subviews import render_generated_images_subview


def build_image_pattern_label_options(
    image_pattern_options: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    return [str(option["label"]) for option in image_pattern_options.values()]


def resolve_default_image_pattern_label(
    *,
    image_pattern_options: Mapping[str, Mapping[str, Any]],
    default_image_pattern_key: str,
) -> str:
    return str(image_pattern_options[default_image_pattern_key]["label"])


def create_generated_images_container(
    *,
    generated_image_variants: Callable[[], Any],
    generated_images: Callable[[], Any],
    image_generation_status: Callable[[], str],
    on_download_image: Callable[[str], None],
) -> Callable[[], None]:
    @ui.refreshable
    def generated_images_container() -> None:
        render_generated_images_subview(
            generated_image_variants=generated_image_variants(),
            generated_images=generated_images(),
            image_generation_status=str(image_generation_status() or ""),
            on_download_image=on_download_image,
        )

    return generated_images_container


def render_generated_image_auto_panel(
    *,
    note_image_size_label: str,
    render_generated_images_container: Callable[[], None],
) -> dict[str, Any]:
    image_section_widgets: dict[str, Any] = {}

    ui.separator()
    with ui.card().classes("w-full bg-[#FFF8F2] border border-[#E8D7C8] p-4 rounded-lg"):
        with ui.row().classes("items-center gap-2 mb-1"):
            ui.icon("image").classes("text-[#8A4A1C]")
            ui.label("記事に合わせた画像").classes("output-section-title text-[#5D4A41]")
        ui.label("記事生成後に、文字入り画像と文字なし画像を自動で作成します。").classes("section-muted-note mb-1")
        ui.label(f"推奨サイズに自動整形: {note_image_size_label}").classes("text-xs text-gray-600 mb-2")
        ui.label("保存ボタンを押すと、ブラウザの保存画面が開きます（保存先はブラウザ設定に従います）。").classes("text-xs text-gray-600 mt-2")
        render_generated_images_container()

    return image_section_widgets
