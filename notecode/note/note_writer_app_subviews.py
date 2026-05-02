"""Subview builders and pure UI helpers for note_writer_app Phase 03."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from nicegui import ui


@dataclass(frozen=True)
class CustomGenreEditPayload:
    key: str
    label: str
    prompt: str
    meta: dict[str, str]


@dataclass(frozen=True)
class GeneratedImageVariantCard:
    key: str
    label: str
    status: str
    path: str
    error: str
    retry_count: int


@dataclass
class PrivacyBlurDialogControls:
    dialog: Any
    after_image: Any
    preview_status: Any
    preview_btn: Any
    save_btn: Any
    privacy_strength_select: Any
    blur_faces_cb: Any
    blur_plates_cb: Any
    blur_qr_cb: Any
    blur_text_cb: Any


def build_custom_genre_prompt_preview(prompt: str, limit: int = 50) -> str:
    return f"{str(prompt or '')[:limit]}..."


def build_custom_genre_meta_summary(meta: Mapping[str, Any]) -> str:
    return (
        f"base={meta['base_template']} / focus={meta['focus_default']} / "
        f"empathy={meta['empathy_level']} / humanity={meta['humanity_level']} / "
        f"evidence={meta['evidence_mode']}"
    )


def build_generated_image_variant_cards(
    *,
    generated_image_variants: Sequence[Mapping[str, Any]] | None,
    generated_images: Sequence[str] | None,
) -> list[GeneratedImageVariantCard]:
    cards: list[GeneratedImageVariantCard] = []
    variants = [
        item
        for item in (generated_image_variants or [])
        if isinstance(item, Mapping)
    ]
    if not variants and generated_images:
        labels = ["文字入り画像", "文字なし画像"]
        variants = [
            {
                "key": f"legacy_{idx}",
                "label": labels[idx] if idx < len(labels) else f"画像{idx + 1}",
                "status": "success",
                "path": path,
            }
            for idx, path in enumerate(generated_images)
        ]
    for item in variants:
        cards.append(
            GeneratedImageVariantCard(
                key=str(item.get("key") or ""),
                label=str(item.get("label") or item.get("key") or "画像"),
                status=str(item.get("status") or ""),
                path=str(item.get("path") or "").strip(),
                error=str(item.get("error") or "").strip(),
                retry_count=int(item.get("retry_count") or 0),
            )
        )
    return cards


def resolve_privacy_option_key(
    *,
    options: Mapping[str, str],
    selected_label: str,
    fallback: str,
) -> str:
    return next((key for key, label in options.items() if label == selected_label), fallback)


def privacy_blur_targets_selected(
    *,
    blur_faces: bool,
    blur_license_plates: bool,
    blur_qr_codes: bool,
    blur_personal_text: bool,
) -> bool:
    return any([blur_faces, blur_license_plates, blur_qr_codes, blur_personal_text])


def build_scroll_to_anchor_script(anchor_id: str = "generation-result-anchor") -> str:
    return (
        f"document.getElementById({json.dumps(anchor_id)})?.scrollIntoView("
        "{behavior:'smooth', block:'start'});"
    )


def build_copy_to_clipboard_script(text: str) -> str:
    return f"navigator.clipboard.writeText({json.dumps(text)})"


def render_sources_subview(
    *,
    source_items: Sequence[Any],
    on_open_privacy_blur_dialog: Callable[[str], None],
    on_remove_source: Callable[[str], None],
) -> None:
    with ui.column().classes("w-full gap-2"):
        if not source_items:
            ui.label("まだ追加されていません").classes("text-xs text-gray-600")
            return
        for item in source_items:
            if getattr(item, "source_type", "") == "image":
                with ui.row().classes("w-full items-center gap-2"):
                    ui.image(getattr(item, "value", "")).classes("rounded border").style(
                        "width: 64px; height: 64px; object-fit: cover; flex-shrink: 0;"
                    )
                    with ui.column().classes("flex-grow gap-0"):
                        ui.label(getattr(item, "label", "")).classes("text-sm")
                        if bool(getattr(item, "blur_applied", False)):
                            ui.label("ぼかし適用済み").classes("text-xs text-emerald-600")
                    with ui.row().classes("gap-1 flex-shrink-0"):
                        blur_label = "再度ぼかす" if bool(getattr(item, "blur_applied", False)) else "個人情報をぼかす"
                        ui.button(
                            blur_label,
                            on_click=lambda _=None, sid=getattr(item, "id", ""): on_open_privacy_blur_dialog(sid),
                        ).props("flat dense").classes("text-blue-600")
                        ui.button(
                            "削除",
                            on_click=lambda _=None, item_id=getattr(item, "id", ""): on_remove_source(item_id),
                        ).props("flat dense").classes("text-red-500")
            else:
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(getattr(item, "label", "")).classes("text-sm")
                    ui.button(
                        "削除",
                        on_click=lambda _=None, item_id=getattr(item, "id", ""): on_remove_source(item_id),
                    ).props("flat dense").classes("text-red-500")


def render_custom_genres_subview(
    *,
    custom_genres: Sequence[Mapping[str, Any]],
    normalize_meta: Callable[[Any], Mapping[str, Any]],
    on_edit_genre: Callable[[Mapping[str, Any]], None],
    on_delete_genre: Callable[[Mapping[str, Any]], None],
) -> None:
    with ui.column().classes("w-full gap-2"):
        if not custom_genres:
            ui.label("カスタムジャンルはありません").classes("text-xs text-gray-600")
            return
        for genre in custom_genres:
            meta = normalize_meta(genre.get("meta"))
            with ui.row().classes("w-full items-center justify-between source-item"):
                with ui.column().classes("flex-grow"):
                    ui.label(str(genre.get("label", ""))).classes("text-sm font-semibold")
                    ui.label(build_custom_genre_prompt_preview(str(genre.get("prompt", "")))).classes(
                        "text-xs text-gray-600"
                    )
                    ui.label(build_custom_genre_meta_summary(meta)).classes("text-[11px] text-gray-600")
                with ui.row().classes("gap-1"):
                    ui.button("編集", on_click=lambda g=genre: on_edit_genre(g)).props("flat dense").classes("text-blue-500")
                    ui.button("削除", on_click=lambda g=genre: on_delete_genre(g)).props("flat dense").classes("text-red-500")


def open_custom_genre_edit_dialog(
    *,
    genre: Mapping[str, Any],
    normalize_meta: Callable[[Any], Mapping[str, Any]],
    base_template_options: Sequence[str],
    focus_default_options: Sequence[str],
    level_options: Sequence[str],
    evidence_options: Sequence[str],
    on_validation_error: Callable[[str], None],
    on_save: Callable[[CustomGenreEditPayload], None],
) -> None:
    meta = normalize_meta(genre.get("meta"))
    with ui.dialog() as dialog, ui.card().classes("p-4 w-96"):
        ui.label("ジャンルを編集").classes("text-lg font-bold mb-2")
        label_input = ui.input("ラベル", value=genre.get("label", "")).classes("w-full").props("outlined stack-label")
        prompt_input = ui.textarea("プロンプト", value=genre.get("prompt", "")).classes("w-full").props("outlined stack-label")
        base_template = ui.select(
            options=list(base_template_options),
            value=meta["base_template"],
            label="base_template",
        ).classes("w-full")
        focus_default = ui.select(
            options=list(focus_default_options),
            value=meta["focus_default"],
            label="focus_default",
        ).classes("w-full")
        empathy_level = ui.select(
            options=list(level_options),
            value=meta["empathy_level"],
            label="empathy_level",
        ).classes("w-full")
        humanity_level = ui.select(
            options=list(level_options),
            value=meta["humanity_level"],
            label="humanity_level",
        ).classes("w-full")
        evidence_mode = ui.select(
            options=list(evidence_options),
            value=meta["evidence_mode"],
            label="evidence_mode",
        ).classes("w-full")

        def save_edit() -> None:
            label_value = str(label_input.value or "").strip()
            if not label_value:
                on_validation_error("ラベルを入力してください")
                return
            on_save(
                CustomGenreEditPayload(
                    key=str(genre.get("key", "")),
                    label=label_value,
                    prompt=str(prompt_input.value or "").strip(),
                    meta={
                        "base_template": str(base_template.value or ""),
                        "focus_default": str(focus_default.value or ""),
                        "empathy_level": str(empathy_level.value or ""),
                        "humanity_level": str(humanity_level.value or ""),
                        "evidence_mode": str(evidence_mode.value or ""),
                    },
                )
            )
            dialog.close()

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("キャンセル", on_click=dialog.close).props("flat")
            ui.button("保存", on_click=save_edit).classes("primary-btn")
    dialog.open()


def open_custom_genre_delete_dialog(
    *,
    genre: Mapping[str, Any],
    on_confirm_delete: Callable[[str], None],
) -> None:
    with ui.dialog() as dialog, ui.card().classes("p-4 w-80"):
        ui.label("削除の確認").classes("text-lg font-bold mb-2")
        ui.label(f"「{genre.get('label', '')}」を削除しますか？").classes("mb-4")

        def do_delete() -> None:
            on_confirm_delete(str(genre.get("key", "")))
            dialog.close()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("キャンセル", on_click=dialog.close).props("flat")
            ui.button("削除", on_click=do_delete).props("color=negative")
    dialog.open()


def open_privacy_blur_dialog_view(
    *,
    image_path: str,
    privacy_strength_labels: Sequence[str],
    on_close: Callable[[], None],
    on_preview: Callable[[], Any],
    on_save: Callable[[], Any],
    on_toggle_selection: Callable[[], None],
) -> PrivacyBlurDialogControls:
    with ui.dialog() as dialog, ui.card().classes("p-4").style(
        "width: min(92vw, 780px); height: min(88vh, 680px); display: flex; flex-direction: column;"
    ):
        ui.label("個人情報をぼかす").classes("text-lg font-bold mb-1")
        ui.label("写真に写った顔・QRコード・ナンバープレート・個人情報テキストを自動検出してぼかします").classes(
            "text-xs text-gray-600 mb-2"
        )

        with ui.row().classes("w-full items-start").style("flex: 1; min-height: 0; gap: 16px; flex-wrap: wrap;"):
            with ui.column().classes("gap-2").style("flex: 1 1 340px; min-width: 260px;"):
                ui.label("適用前").classes("text-xs text-gray-600")
                ui.image(image_path).classes("w-full rounded-lg border").style(
                    "height: min(36vh, 280px); object-fit: contain; background: #FBF4EF;"
                )
                ui.label("適用後").classes("text-xs text-gray-600 mt-2")
                after_image = ui.image(image_path).classes("w-full rounded-lg border").style(
                    "height: min(36vh, 280px); object-fit: contain; background: #FBF4EF;"
                )
                preview_status = ui.label("プレビュー待機中").classes("text-xs text-gray-600")

            with ui.column().classes("gap-3").style("flex: 0 0 200px; min-width: 180px;"):
                ui.label("検出対象").classes("text-sm font-semibold")
                blur_faces_cb = ui.checkbox("顔", value=True, on_change=lambda _: on_toggle_selection())
                blur_plates_cb = ui.checkbox("ナンバープレート", value=True, on_change=lambda _: on_toggle_selection())
                blur_qr_cb = ui.checkbox("QRコード", value=True, on_change=lambda _: on_toggle_selection())
                blur_text_cb = ui.checkbox("氏名・電話・メール", value=True, on_change=lambda _: on_toggle_selection())

                ui.separator()
                ui.label("ぼかし強度").classes("text-sm font-semibold")
                privacy_strength_select = ui.select(
                    options=list(privacy_strength_labels),
                    value="標準",
                    label="強度",
                ).classes("w-full")
                ui.label("通常は「標準」で十分です").classes("text-xs text-gray-600")

        with ui.row().classes("w-full items-center justify-end gap-2 mt-3").style(
            "position: sticky; bottom: 0; background: rgba(255,255,255,0.96); border-top: 1px solid #e5e7eb; "
            "padding-top: 8px; backdrop-filter: blur(2px);"
        ):
            ui.button("閉じる", on_click=on_close).props("flat")
            preview_btn = ui.button("プレビュー", on_click=on_preview).props("outline").classes("primary-btn")
            save_btn = ui.button("適用して保存", on_click=on_save).classes("primary-btn")

    return PrivacyBlurDialogControls(
        dialog=dialog,
        after_image=after_image,
        preview_status=preview_status,
        preview_btn=preview_btn,
        save_btn=save_btn,
        privacy_strength_select=privacy_strength_select,
        blur_faces_cb=blur_faces_cb,
        blur_plates_cb=blur_plates_cb,
        blur_qr_cb=blur_qr_cb,
        blur_text_cb=blur_text_cb,
    )


def render_generated_images_subview(
    *,
    generated_image_variants: Sequence[Mapping[str, Any]] | None,
    generated_images: Sequence[str] | None,
    image_generation_status: str,
    on_download_image: Callable[[str], None],
) -> None:
    with ui.column().classes("w-full gap-3"):
        ui.html('<div id="generated-images-anchor"></div>', sanitize=False)
        cards = build_generated_image_variant_cards(
            generated_image_variants=generated_image_variants,
            generated_images=generated_images,
        )
        if not cards:
            if str(image_generation_status or "") == "running":
                with ui.row().classes("items-center gap-2 text-sm text-gray-600"):
                    ui.spinner(size="sm")
                    ui.label("記事に合わせて画像を生成中です")
            else:
                ui.label("記事生成後に、文字入り画像と文字なし画像を自動生成します").classes("text-xs text-gray-600")
            return
        with ui.grid(columns=2).classes("w-full gap-3"):
            for item in cards:
                with ui.card().classes("w-full p-3 gap-2"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(item.label).classes("text-sm font-bold text-gray-800")
                        if item.retry_count:
                            ui.label("retry").classes("text-[11px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded")
                    if item.path:
                        ui.image(item.path).classes("w-full rounded border")
                        ui.button("保存", on_click=lambda p=item.path: on_download_image(p)).classes("primary-btn")
                    elif item.status == "failed":
                        ui.label("画像生成に失敗しました。記事本文はそのまま使えます。").classes("text-xs text-red-600")
                        if item.error:
                            ui.label(item.error[:160]).classes("text-[11px] text-gray-500")
                    else:
                        ui.label("生成待機中").classes("text-xs text-gray-600")
