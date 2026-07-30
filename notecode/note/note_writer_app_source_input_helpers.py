"""State/action helpers for note_writer_app source input."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Iterable, List, Tuple

from note.note_writer_app_source_helpers import (
    build_recent_uploaded_source_drafts,
    copy_local_pdf_to_uploads,
    extract_upload_payload,
    prepare_source_add,
    remove_source_by_id,
    remove_upload_paths,
    save_uploaded_payload,
    select_stale_upload_paths,
)


NotifyFn = Callable[..., None]
RefreshFn = Callable[[], None]


def _refresh_step_callback(state: Any) -> None:
    callback = getattr(state, "step_refresh_callback", None)
    if callable(callback):
        try:
            callback()
        except Exception:
            pass


def find_recent_pdf_candidates(
    since_ts: float,
    *,
    downloads_dir: Path | None = None,
    limit: int = 8,
) -> List[str]:
    downloads = Path.home() / "Downloads" if downloads_dir is None else Path(downloads_dir)
    if not downloads.exists():
        return []
    candidates: List[Tuple[float, str]] = []
    for path in downloads.glob("*.pdf"):
        try:
            stat = path.stat()
        except OSError:
            continue
        if stat.st_size <= 0 or stat.st_size > 10 * 1024 * 1024:
            continue
        if stat.st_mtime < max(0.0, since_ts - 30):
            continue
        candidates.append((stat.st_mtime, str(path)))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in candidates[:limit]]


def ingest_local_pdf_to_uploads(*, path: str, upload_dir: Path) -> str:
    return str(copy_local_pdf_to_uploads(src_path=path, upload_dir=upload_dir))


def add_source_to_state(
    *,
    state: Any,
    source_item_factory: Callable[..., Any],
    label: str,
    value: str,
    source_type: str,
    notify: NotifyFn,
    sources_refresh: RefreshFn,
    snapshot_source_session: Callable[[Any], None],
    logger: logging.Logger,
) -> bool:
    prepared = prepare_source_add(
        label=label,
        value=value,
        source_type=source_type,
        existing_values=[source.value for source in state.sources],
    )
    normalized_value = prepared.normalized_value
    if not prepared.accepted:
        if prepared.reason == "empty_value":
            logger.warning("Source add rejected: reason=empty_value source_type=%s", source_type)
            notify("値を入力してください", color="negative")
            return False
        if prepared.reason == "invalid_url_scheme":
            logger.warning(
                "Source add rejected: reason=invalid_url_scheme source_type=%s value=%s",
                source_type,
                normalized_value,
            )
            notify("有効なURLプロトコル(http/https)を入力してください", color="negative")
            return False
        if prepared.reason == "duplicate":
            logger.info("Source add skipped: reason=duplicate source_type=%s value=%s", source_type, normalized_value)
            notify("同じソースが追加されています", color="warning")
            return False
        logger.warning("Source add rejected: reason=empty_value source_type=%s", source_type)
        return False

    if prepared.item is None:
        logger.warning(
            "Source add rejected: reason=missing_item_payload source_type=%s value=%s",
            source_type,
            normalized_value,
        )
        return False

    state.sources.append(
        source_item_factory(
            id=prepared.item.id,
            label=prepared.item.label,
            value=prepared.item.value,
            source_type=prepared.item.source_type,
        )
    )
    state.source_session_restored = False
    snapshot_source_session(state)
    logger.info("Source added: source_type=%s value=%s", source_type, normalized_value)
    sources_refresh()
    _refresh_step_callback(state)
    return True


def remove_source_from_state(
    *,
    state: Any,
    source_id: str,
    sources_refresh: RefreshFn,
    clear_source_session_sources: Callable[[Any], None],
    snapshot_source_session: Callable[[Any], None],
) -> None:
    state.sources = remove_source_by_id(state.sources, source_id)
    if not state.sources:
        clear_source_session_sources(state)
    else:
        snapshot_source_session(state)
    sources_refresh()
    _refresh_step_callback(state)


def restore_recent_uploaded_sources(
    *,
    state: Any,
    upload_dir: Path,
    image_extensions: Iterable[str],
    source_item_factory: Callable[..., Any],
    mark_source_session_review_required: Callable[[Any], None],
    snapshot_source_session: Callable[[Any], None],
    sources_refresh: RefreshFn,
    max_age_sec: int = 600,
) -> int:
    if state.sources:
        return 0
    recovered_drafts = build_recent_uploaded_source_drafts(
        upload_dir=upload_dir,
        existing_values=[source.value for source in state.sources],
        image_extensions=image_extensions,
        max_age_sec=max_age_sec,
    )
    for draft in recovered_drafts:
        state.sources.append(
            source_item_factory(
                id=draft.id,
                label=draft.label,
                value=draft.value,
                source_type=draft.source_type,
            )
        )

    if recovered_drafts:
        mark_source_session_review_required(state)
        snapshot_source_session(state)
        sources_refresh()
    return len(recovered_drafts)


def cleanup_old_upload_files(*, upload_dir: Path, max_age_sec: int = 24 * 60 * 60) -> int:
    stale_paths = select_stale_upload_paths(upload_dir=upload_dir, max_age_sec=max_age_sec)
    return remove_upload_paths(stale_paths)


async def handle_upload(
    event: Any,
    *,
    upload_dir: Path,
    image_extensions: Iterable[str],
    io_bound_runner: Callable[..., Any],
    add_source: Callable[[str, str, str], bool],
    notify: NotifyFn,
    logger: logging.Logger,
) -> None:
    try:
        payload = await extract_upload_payload(event)
    except Exception:
        logger.exception("Upload payload extraction failed")
        notify("ファイル取り込みに失敗しました。ページ再読み込み後に再試行してください。", color="negative")
        return

    try:
        saved_upload = await save_uploaded_payload(
            upload_dir=upload_dir,
            original_name=payload.original_name,
            data=payload.data,
            image_extensions=image_extensions,
            io_bound_runner=io_bound_runner,
        )
    except TypeError:
        notify("アップロードデータ形式が不正です。", color="negative")
        return
    except ValueError as exc:
        notify(str(exc), color="negative")
        return

    added = add_source(payload.original_name, str(saved_upload.destination), saved_upload.source_type)
    if added:
        notify(f"アップロード完了: {saved_upload.safe_name}（追加済みソースに登録しました）", color="primary")
    else:
        notify(f"ファイル保存のみ完了: {saved_upload.safe_name}（ソース追加は未反映）", color="warning")
