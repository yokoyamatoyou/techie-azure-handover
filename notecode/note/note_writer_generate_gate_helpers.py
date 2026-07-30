"""Pure source-mode and generation-gate surface helpers for note_writer_app."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Dict

from note.note_text_format_helpers import _to_plain_list
from note.note_writer_app_article_source_mode import _is_prompt_only_allowed_article_type
from note.note_writer_app_current_mainline_compat import build_omakase_preflight
from note.omakase_seed_builder import omakase_available as _omakase_inventory_available


_SOURCE_MODE_INPUT_REQUIRED_MODES = {"grounded"}
_OMAKASE_STATUS_LABELS = {
    "READY": "このまま始められます",
    "AUTO_SOURCE_READY": "必要な材料を先に集めます",
    "NEEDS_INPUT": "テーマを1行入れてください",
    "OMAKASE_FALLBACK": "まだお任せで始められません",
}


def _past_blog_prompt_unlock_available(published_post_candidates: Any = None) -> bool:
    return bool(_omakase_inventory_available(list(published_post_candidates or [])))


def _build_omakase_surface_state(
    *,
    article_type_key: str,
    prompt_raw: str,
    source_mode_key: str,
    source_values: Iterable[Any] | None = None,
    source_documents: Iterable[Any] | None = None,
    published_post_candidates: Iterable[Any] | None = None,
) -> Dict[str, Any]:
    normalized_source_mode = str(source_mode_key or "").strip().lower()
    if normalized_source_mode != "web":
        return {
            "visible": False,
            "status": "",
            "title": "",
            "message": "",
            "inventory_text": "",
            "detail_text": "",
            "allow_generate": False,
            "preflight": {},
        }
    preflight = build_omakase_preflight(
        requested_article_type=article_type_key,
        user_prompt_text=str(prompt_raw or "").strip(),
        source_values=list(source_values or []),
        source_documents=list(source_documents or []),
        published_post_candidates=list(published_post_candidates or []),
        preferred_source_mode="auto",
        industry_hint="",
    )
    status = str(preflight.get("status") or "").strip()
    existing_count = int(preflight.get("existing_post_count") or 0)
    total_body_chars = int(preflight.get("total_body_chars") or 0)
    min_posts = int(preflight.get("inventory_min_posts") or 0)
    min_total_body_chars = int(preflight.get("inventory_min_total_body_chars") or 0)
    source_count = int(preflight.get("source_count") or 0)
    prompt_is_blank = not bool(str(prompt_raw or "").strip())
    inventory_locked_without_sources = bool(source_count <= 0 and not bool(preflight.get("omakase_available")))
    inventory_locked_without_prompt = bool(inventory_locked_without_sources and prompt_is_blank)
    if inventory_locked_without_sources:
        status = "OMAKASE_FALLBACK"
    fallback_options = [
        str(item.get("label") or "").strip()
        for item in _to_plain_list(preflight.get("fallback_options"))
        if isinstance(item, dict) and str(item.get("label") or "").strip()
    ]
    needs_items = [
        str(item.get("question_template") or "").strip()
        for item in _to_plain_list(preflight.get("needs_input_items"))
        if isinstance(item, dict) and str(item.get("question_template") or "").strip()
    ]
    detail_parts: list[str] = []
    if min_posts > 0 and min_total_body_chars > 0:
        detail_parts.append(f"利用条件: 公開済み{min_posts}件以上 / 合計本文{min_total_body_chars}字以上")
    if fallback_options:
        detail_parts.append("代替案: " + " / ".join(fallback_options[:3]))
    if needs_items and not inventory_locked_without_prompt:
        detail_parts.append("追加入力: " + " / ".join(needs_items[:2]))
    if status == "AUTO_SOURCE_READY":
        detail_parts.append("生成を押すと、本生成の前に外部ソースの材料収集可否の確認で止まります。")
    if status == "OMAKASE_FALLBACK" and not str(preflight.get("message") or "").strip():
        detail_parts.append("公開済みブログが不足しているため、1行テーマだけでは開始できません。")
    message_text = (
        "公開済みブログの蓄積が足りないため、お任せはまだ開始しません。資料ありで材料を追加してください。"
        if inventory_locked_without_prompt
        else str(preflight.get("message") or "").strip()
    )
    return {
        "visible": True,
        "status": status,
        "title": _OMAKASE_STATUS_LABELS.get(status, "状況を確認してください"),
        "message": message_text,
        "inventory_text": f"現在の公開済み記事: {existing_count}件 / 合計本文 {total_body_chars}字",
        "detail_text": " ".join(part for part in detail_parts if part).strip(),
        "allow_generate": status == "AUTO_SOURCE_READY",
        "preflight": dict(preflight),
    }


def _build_generate_gate_surface(
    *,
    confirmation_ready: bool,
    source_mode_key: str,
    source_count: int,
    article_type_key: str = "",
    prompt_raw: str = "",
    omakase_state: Mapping[str, Any] | None = None,
    past_blog_unlocked: bool = False,
) -> Dict[str, Any]:
    normalized_source_mode = str(source_mode_key or "").strip().lower()
    normalized_omakase_state = dict(omakase_state or {})
    if normalized_source_mode in _SOURCE_MODE_INPUT_REQUIRED_MODES and source_count <= 0:
        return {
            "enabled": False,
            "button_text": "資料を追加する",
            "hint_text": "資料ありでは、URL / PDF / 画像 / テキストを1件以上そろえると進めます。入力済みの内容は保持したまま、資料入力へ戻ってください。",
            "hint_classes": "text-amber-700",
        }
    if normalized_source_mode == "prompt_only":
        if not _is_prompt_only_allowed_article_type(article_type_key):
            return {
                "enabled": False,
                "button_text": "資料ありで進める",
                "hint_text": "プロンプトのみは日常のできごとの記事だけで使えます。資料ありへ切り替えてください。",
                "hint_classes": "text-amber-700",
            }
        if not past_blog_unlocked:
            return {
                "enabled": False,
                "button_text": "資料ありで進める",
                "hint_text": "公開済みブログの蓄積が足りないため、1行テーマだけでは開始できません。資料ありで材料を追加してください。",
                "hint_classes": "text-amber-700",
            }
        if not str(prompt_raw or "").strip():
            return {
                "enabled": False,
                "button_text": "1行テーマを入力する",
                "hint_text": "プロンプトのみでは、まず何が起きたかを1行で入れると進めます。",
                "hint_classes": "text-amber-700",
            }
    omakase_status = str(normalized_omakase_state.get("status") or "").strip()
    if normalized_source_mode == "web":
        if not past_blog_unlocked:
            return {
                "enabled": False,
                "button_text": "資料ありで進める",
                "hint_text": str(
                    normalized_omakase_state.get("detail_text")
                    or normalized_omakase_state.get("message")
                    or "公開済みブログの蓄積が足りないため、お任せはまだ開始できません。資料ありで材料を追加してください。"
                ),
                "hint_classes": "text-amber-700",
            }
        if omakase_status == "NEEDS_INPUT":
            return {
                "enabled": False,
                "button_text": "1行テーマを入力する",
                "hint_text": "お任せでは、まず何について書くかを1行で入れると次に進めます。",
                "hint_classes": "text-amber-700",
            }
        if omakase_status == "OMAKASE_FALLBACK":
            return {
                "enabled": False,
                "button_text": "資料ありで進める",
                "hint_text": str(normalized_omakase_state.get("detail_text") or normalized_omakase_state.get("message") or ""),
                "hint_classes": "text-amber-700",
            }
        if omakase_status == "AUTO_SOURCE_READY":
            return {
                "enabled": True,
                "button_text": "材料集めの確認へ進む",
                "hint_text": "このボタンで材料集めの可否確認へ進みます。本生成はその確認のあとに始まります。",
                "hint_classes": "text-[#5D4A41]",
            }
    if not confirmation_ready:
        return {
            "enabled": False,
            "button_text": "方針を確認する",
            "hint_text": "入力は保持されています。生成前チェックで方針を確認すると、記事生成へ進めます。",
            "hint_classes": "text-amber-700",
        }
    return {
        "enabled": True,
        "button_text": "記事を生成",
        "hint_text": "この内容で記事生成に進めます。",
        "hint_classes": "text-green-700",
    }
