"""Pure display helpers for note writer generation progress."""
from __future__ import annotations

from typing import Any, Callable, Mapping


def _format_generation_progress_text(
    *,
    percent: Any,
    label_text: str,
    detail: str = "",
    elapsed: str = "",
) -> str:
    bounded = _coerce_display_generation_percent(percent)
    parts = ["進行状況:", f"{bounded}%"]
    normalized_label = str(label_text or "").strip()
    normalized_detail = str(detail or "").strip()
    normalized_elapsed = str(elapsed or "").strip()
    if normalized_label:
        parts.append(normalized_label)
    if normalized_detail:
        parts.append(normalized_detail)
    if normalized_elapsed:
        parts.append(normalized_elapsed)
    return " ".join(parts).strip()


def _coerce_display_generation_percent(value: Any) -> int:
    try:
        numeric = float(value if value is not None else 0.0)
    except (TypeError, ValueError):
        numeric = 0.0
    if 0.0 <= numeric <= 1.0 and (
        isinstance(value, float) or "." in str(value)
    ):
        numeric *= 100.0
    return max(0, min(100, int(round(numeric))))


def _resolve_display_generation_percent(*, current_value: Any, reported_percent: Any) -> int:
    current_percent = _coerce_display_generation_percent(current_value)
    bounded_reported = _coerce_display_generation_percent(reported_percent)
    return max(current_percent, bounded_reported)


def build_generation_progress_display_state(
    progress: Mapping[str, Any],
    *,
    current_value: Any,
    elapsed_seconds: int | None = None,
    route_progress_view_builder: Callable[[str], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    stage = str(progress.get("stage", "") or "").strip().lower()
    reported_percent = 100 if stage == "completed" else progress.get("percent", 0)
    elapsed = "" if elapsed_seconds is None else f"（経過{max(0, int(elapsed_seconds))}秒）"
    return {
        "stage": stage,
        "label_text": _to_user_friendly_progress(
            progress,
            route_progress_view_builder=route_progress_view_builder,
        ),
        "display_percent": _resolve_display_generation_percent(
            current_value=current_value,
            reported_percent=reported_percent,
        ),
        "elapsed": elapsed,
    }


def _to_user_friendly_progress(
    progress: Mapping[str, Any],
    *,
    route_progress_view_builder: Callable[[str], Mapping[str, Any]] | None = None,
) -> str:
    stage = str(progress.get("stage", "") or "").strip().lower()
    if stage.startswith("route_0506"):
        if route_progress_view_builder is None:
            return "Route 0506 で処理中..."
        return str(route_progress_view_builder(stage).get("label_text") or "Route 0506 で処理中...")
    stage_labels = {
        "validate": "入力を確認中...",
        "prepare": "現在準備中...",
        "fetch_sources": "ソース取得中...",
        "outline": "現在執筆の準備中...",
        "body": "現在執筆中...",
        "polish": "現在編集中...",
        "generate_article": "本文を生成中...",
        "quality_output_guard": "品質を検証中...",
        "legal_postcheck": "リーガルチェック中...",
        "auto_retry_transient": "一時障害のため再試行中...",
        "render_output": "出力を整形中...",
        "generate_image_prompts": "画像用プロンプトを準備中...",
        "generate_images": "記事に合わせた画像を生成中...",
        "completed": "生成が完了しました。",
    }
    return stage_labels.get(stage, "現在処理中...")


def _generation_phase_progress(
    phase_key: str,
    *,
    route_progress_view_builder: Callable[[str], Mapping[str, Any]] | None = None,
) -> int:
    normalized_phase = str(phase_key or "").strip().lower()
    if normalized_phase.startswith("route_0506"):
        if route_progress_view_builder is None:
            return 0
        return int(route_progress_view_builder(normalized_phase).get("percent") or 0)
    phase_progress = {
        "validate": 3,
        "prepare": 8,
        "fetch_sources": 20,
        "generate_article": 65,
        "quality_output_guard": 82,
        "legal_postcheck": 88,
        "auto_retry_transient": 86,
        "render_output": 90,
        "generate_image_prompts": 94,
        "generate_images": 96,
        "complete": 100,
        "completed": 100,
    }
    return int(phase_progress.get(normalized_phase, 0))
