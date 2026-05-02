"""Source and upload helpers for note_writer_app Phase 02."""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Sequence


DEFAULT_MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
DEFAULT_ALLOWED_UPLOAD_EXTENSIONS = frozenset(
    {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"}
)


@dataclass(frozen=True)
class SourceItemDraft:
    id: str
    label: str
    value: str
    source_type: str


@dataclass(frozen=True)
class PreparedSourceAdd:
    accepted: bool
    reason: str
    normalized_value: str
    item: SourceItemDraft | None = None


@dataclass(frozen=True)
class UploadPayload:
    original_name: str
    data: bytes


@dataclass(frozen=True)
class SavedUpload:
    original_name: str
    safe_name: str
    destination: Path
    source_type: str
    suffix: str


def _default_source_id_factory() -> str:
    return str(uuid.uuid4())


def _default_file_token_factory() -> str:
    return uuid.uuid4().hex


def _normalize_extension_set(values: Iterable[str]) -> set[str]:
    return {str(value).lower() for value in values}


def _sanitize_upload_name(
    original_name: str,
    suffix: str,
    *,
    file_token_factory: Callable[[], str],
) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9\._\-]", "_", Path(original_name).name)
    if safe_name:
        return safe_name
    token = file_token_factory()[:8]
    return f"upload_{token}{suffix or '.bin'}"


def prepare_source_add(
    *,
    label: str,
    value: str,
    source_type: str,
    existing_values: Iterable[str],
    source_id_factory: Callable[[], str] = _default_source_id_factory,
) -> PreparedSourceAdd:
    normalized_value = str(value or "").strip()
    if not normalized_value:
        return PreparedSourceAdd(False, "empty_value", normalized_value)
    if source_type == "url" and not normalized_value.startswith(("http://", "https://")):
        return PreparedSourceAdd(False, "invalid_url_scheme", normalized_value)
    if normalized_value in {str(existing) for existing in existing_values}:
        return PreparedSourceAdd(False, "duplicate", normalized_value)
    return PreparedSourceAdd(
        True,
        "",
        normalized_value,
        SourceItemDraft(
            id=str(source_id_factory()),
            label=str(label),
            value=normalized_value,
            source_type=str(source_type),
        ),
    )


def remove_source_by_id(source_items: Sequence[Any], source_id: str) -> list[Any]:
    return [item for item in source_items if getattr(item, "id", None) != source_id]


def build_recent_uploaded_source_drafts(
    *,
    upload_dir: Path,
    existing_values: Iterable[str],
    image_extensions: Iterable[str],
    allowed_extensions: Iterable[str] = DEFAULT_ALLOWED_UPLOAD_EXTENSIONS,
    max_age_sec: int = 600,
    limit: int = 5,
    now_ts: float | None = None,
    source_id_factory: Callable[[], str] = _default_source_id_factory,
) -> list[SourceItemDraft]:
    if not upload_dir.exists():
        return []

    allowed = _normalize_extension_set(allowed_extensions)
    image_exts = _normalize_extension_set(image_extensions)
    existing = {str(value) for value in existing_values}
    now = time.time() if now_ts is None else now_ts
    candidates: list[tuple[float, Path]] = []

    for path in upload_dir.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in allowed:
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if now - mtime <= max_age_sec:
            candidates.append((mtime, path))

    candidates.sort(key=lambda item: item[0], reverse=True)
    drafts: list[SourceItemDraft] = []
    for _, path in candidates:
        path_value = str(path)
        if path_value in existing:
            continue
        source_type = "image" if path.suffix.lower() in image_exts else "file"
        drafts.append(
            SourceItemDraft(
                id=str(source_id_factory()),
                label=path.name,
                value=path_value,
                source_type=source_type,
            )
        )
        if len(drafts) >= limit:
            break
    return drafts


def select_stale_upload_paths(
    *,
    upload_dir: Path,
    max_age_sec: int = 24 * 60 * 60,
    now_ts: float | None = None,
) -> list[Path]:
    if not upload_dir.exists():
        return []

    now = time.time() if now_ts is None else now_ts
    stale_paths: list[Path] = []
    for path in upload_dir.iterdir():
        if not path.is_file():
            continue
        try:
            age = now - path.stat().st_mtime
        except OSError:
            continue
        if age > max_age_sec:
            stale_paths.append(path)
    return stale_paths


def remove_upload_paths(paths: Sequence[Path]) -> int:
    removed = 0
    for path in paths:
        try:
            path.unlink(missing_ok=True)
            removed += 1
        except OSError:
            continue
    return removed


async def extract_upload_payload(event: Any) -> UploadPayload:
    if hasattr(event, "file") and getattr(event, "file") is not None:
        uploaded = event.file
        original_name = str(getattr(uploaded, "name", "") or "uploaded_file")
        data = await uploaded.read()
    elif hasattr(event, "content"):
        original_name = str(getattr(event, "name", "") or "uploaded_file")
        payload = event.content
        data = payload.read() if hasattr(payload, "read") else payload
    else:
        raise ValueError("Upload payload is missing")

    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Upload payload must resolve to bytes")
    return UploadPayload(original_name=original_name, data=bytes(data))


async def save_uploaded_payload(
    *,
    upload_dir: Path,
    original_name: str,
    data: bytes | bytearray,
    image_extensions: Iterable[str],
    io_bound_runner: Callable[..., Awaitable[Any]],
    allowed_extensions: Iterable[str] = DEFAULT_ALLOWED_UPLOAD_EXTENSIONS,
    max_size_bytes: int = DEFAULT_MAX_UPLOAD_SIZE_BYTES,
    file_token_factory: Callable[[], str] = _default_file_token_factory,
) -> SavedUpload:
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Upload payload must resolve to bytes")

    payload = bytes(data)
    if len(payload) > max_size_bytes:
        raise ValueError("ファイルサイズが大きすぎます (10MB上限)")

    allowed = _normalize_extension_set(allowed_extensions)
    image_exts = _normalize_extension_set(image_extensions)
    suffix = Path(original_name).suffix.lower()
    if suffix not in allowed:
        raise ValueError("未対応の拡張子です（PDF/DOCX/txt/md/png/jpg/jpeg/webp）")

    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _sanitize_upload_name(
        original_name,
        suffix,
        file_token_factory=file_token_factory,
    )
    destination = upload_dir / f"{file_token_factory()}_{safe_name}"
    await io_bound_runner(destination.write_bytes, payload)
    source_type = "image" if suffix in image_exts else "file"
    return SavedUpload(
        original_name=str(original_name),
        safe_name=safe_name,
        destination=destination,
        source_type=source_type,
        suffix=suffix,
    )


def copy_local_pdf_to_uploads(
    *,
    src_path: str | Path,
    upload_dir: Path,
    max_size_bytes: int = DEFAULT_MAX_UPLOAD_SIZE_BYTES,
    file_token_factory: Callable[[], str] = _default_file_token_factory,
) -> Path:
    src = Path(src_path)
    if not src.exists() or src.suffix.lower() != ".pdf":
        raise ValueError("PDFファイルが見つからないか、拡張子が不正です。")

    data = src.read_bytes()
    if len(data) > max_size_bytes:
        raise ValueError("PDFサイズが上限(10MB)を超えています。")

    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _sanitize_upload_name(
        src.name,
        src.suffix.lower(),
        file_token_factory=file_token_factory,
    )
    destination = upload_dir / f"{file_token_factory()}_{safe_name}"
    destination.write_bytes(data)
    return destination
