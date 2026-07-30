from __future__ import annotations

import asyncio
import io
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

from note import note_writer_app_source_helpers as helpers
from note import note_writer_app_source_input_helpers as state_helpers


@dataclass
class _DummySource:
    id: str
    value: str


@dataclass
class _DummyState:
    sources: list = field(default_factory=list)
    source_session_restored: bool = True
    step_refresh_callback: object | None = None


class _AsyncUpload:
    def __init__(self, name: str, data) -> None:  # type: ignore[no-untyped-def]
        self.name = name
        self._data = data

    async def read(self):  # type: ignore[no-untyped-def]
        return self._data


class _FileEvent:
    def __init__(self, file_obj) -> None:  # type: ignore[no-untyped-def]
        self.file = file_obj


class _ContentEvent:
    def __init__(self, name: str, content) -> None:  # type: ignore[no-untyped-def]
        self.name = name
        self.content = content


def test_prepare_source_add_accepts_trimmed_value_and_builds_draft() -> None:
    prepared = helpers.prepare_source_add(
        label="Example",
        value="  https://example.com/path  ",
        source_type="url",
        existing_values=[],
        source_id_factory=lambda: "source-1",
    )

    assert prepared.accepted is True
    assert prepared.reason == ""
    assert prepared.normalized_value == "https://example.com/path"
    assert prepared.item == helpers.SourceItemDraft(
        id="source-1",
        label="Example",
        value="https://example.com/path",
        source_type="url",
    )


def test_prepare_source_add_rejects_invalid_url_scheme_and_duplicates() -> None:
    invalid = helpers.prepare_source_add(
        label="Example",
        value="ftp://example.com/path",
        source_type="url",
        existing_values=[],
    )
    duplicate = helpers.prepare_source_add(
        label="Example",
        value="https://example.com/path",
        source_type="url",
        existing_values=["https://example.com/path"],
    )

    assert invalid.accepted is False
    assert invalid.reason == "invalid_url_scheme"
    assert duplicate.accepted is False
    assert duplicate.reason == "duplicate"


def test_remove_source_by_id_filters_matching_item() -> None:
    source_items = [
        _DummySource(id="s1", value="https://example.com/1"),
        _DummySource(id="s2", value="https://example.com/2"),
    ]

    filtered = helpers.remove_source_by_id(source_items, "s1")

    assert filtered == [_DummySource(id="s2", value="https://example.com/2")]


def test_build_recent_uploaded_source_drafts_recovers_recent_supported_files(tmp_path: Path) -> None:
    now = time.time()
    recent_md = tmp_path / "recent.md"
    recent_md.write_text("markdown", encoding="utf-8")
    os.utime(recent_md, (now - 5, now - 5))

    recent_image = tmp_path / "recent.png"
    recent_image.write_bytes(b"png")
    os.utime(recent_image, (now - 10, now - 10))

    old_pdf = tmp_path / "old.pdf"
    old_pdf.write_bytes(b"pdf")
    os.utime(old_pdf, (now - 1000, now - 1000))

    unsupported = tmp_path / "recent.csv"
    unsupported.write_text("ignored", encoding="utf-8")
    os.utime(unsupported, (now - 1, now - 1))

    ids = iter(["source-1", "source-2", "source-3"])
    drafts = helpers.build_recent_uploaded_source_drafts(
        upload_dir=tmp_path,
        existing_values=[str(recent_image)],
        image_extensions={".png", ".jpg", ".jpeg", ".webp"},
        max_age_sec=600,
        now_ts=now,
        source_id_factory=lambda: next(ids),
    )

    assert drafts == [
        helpers.SourceItemDraft(
            id="source-1",
            label="recent.md",
            value=str(recent_md),
            source_type="file",
        )
    ]


def test_select_stale_upload_paths_and_remove_upload_paths_only_touch_old_files(tmp_path: Path) -> None:
    now = time.time()
    stale = tmp_path / "stale.txt"
    stale.write_text("old", encoding="utf-8")
    os.utime(stale, (now - 120, now - 120))

    fresh = tmp_path / "fresh.txt"
    fresh.write_text("new", encoding="utf-8")
    os.utime(fresh, (now - 5, now - 5))

    stale_paths = helpers.select_stale_upload_paths(
        upload_dir=tmp_path,
        max_age_sec=60,
        now_ts=now,
    )
    removed = helpers.remove_upload_paths(stale_paths)

    assert stale_paths == [stale]
    assert removed == 1
    assert stale.exists() is False
    assert fresh.exists() is True


def test_extract_upload_payload_reads_async_file_variant() -> None:
    payload = asyncio.run(
        helpers.extract_upload_payload(
            _FileEvent(_AsyncUpload("guide.pdf", b"%PDF-1.4")),
        )
    )

    assert payload.original_name == "guide.pdf"
    assert payload.data == b"%PDF-1.4"


def test_extract_upload_payload_reads_content_variant_and_encodes_text() -> None:
    payload = asyncio.run(
        helpers.extract_upload_payload(
            _ContentEvent("memo.txt", io.StringIO("hello")),
        )
    )

    assert payload.original_name == "memo.txt"
    assert payload.data == b"hello"


def test_save_uploaded_payload_validates_and_persists_file(tmp_path: Path) -> None:
    async def fake_io_bound(fn, *args):  # type: ignore[no-untyped-def]
        return fn(*args)

    saved = asyncio.run(
        helpers.save_uploaded_payload(
            upload_dir=tmp_path,
            original_name="企画メモ!.png",
            data=b"image-bytes",
            image_extensions={".png", ".jpg", ".jpeg", ".webp"},
            io_bound_runner=fake_io_bound,
            file_token_factory=lambda: "token1234",
        )
    )

    assert saved.safe_name == "_____.png"
    assert saved.source_type == "image"
    assert saved.destination == tmp_path / "token1234______.png"
    assert saved.destination.read_bytes() == b"image-bytes"


def test_save_uploaded_payload_rejects_large_payload(tmp_path: Path) -> None:
    async def fake_io_bound(fn, *args):  # type: ignore[no-untyped-def]
        return fn(*args)

    try:
        asyncio.run(
            helpers.save_uploaded_payload(
                upload_dir=tmp_path,
                original_name="guide.pdf",
                data=b"x" * (helpers.DEFAULT_MAX_UPLOAD_SIZE_BYTES + 1),
                image_extensions={".png", ".jpg", ".jpeg", ".webp"},
                io_bound_runner=fake_io_bound,
            )
        )
    except ValueError as exc:
        assert str(exc) == "ファイルサイズが大きすぎます (10MB上限)"
    else:
        raise AssertionError("ValueError was not raised")


def test_copy_local_pdf_to_uploads_preserves_pdf_bytes(tmp_path: Path) -> None:
    src = tmp_path / "source file.pdf"
    src.write_bytes(b"%PDF-content")

    copied = helpers.copy_local_pdf_to_uploads(
        src_path=src,
        upload_dir=tmp_path / "uploads",
        file_token_factory=lambda: "pdfcopy01",
    )

    assert copied == tmp_path / "uploads" / "pdfcopy01_source_file.pdf"
    assert copied.read_bytes() == b"%PDF-content"


def test_find_recent_pdf_candidates_filters_and_sorts(tmp_path: Path) -> None:
    now = time.time()
    newest = tmp_path / "newest.pdf"
    newest.write_bytes(b"%PDF-new")
    os.utime(newest, (now - 2, now - 2))

    older = tmp_path / "older.pdf"
    older.write_bytes(b"%PDF-old")
    os.utime(older, (now - 10, now - 10))

    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    os.utime(empty, (now - 1, now - 1))

    candidates = state_helpers.find_recent_pdf_candidates(
        now,
        downloads_dir=tmp_path,
        limit=5,
    )

    assert candidates == [str(newest), str(older)]


def test_add_source_to_state_updates_session_and_refreshes() -> None:
    events: list = []
    notifications: list = []
    state = _DummyState(step_refresh_callback=lambda: events.append("step"))

    added = state_helpers.add_source_to_state(
        state=state,
        source_item_factory=lambda **kwargs: SimpleNamespace(**kwargs),
        label="Example",
        value=" https://example.com ",
        source_type="url",
        notify=lambda message, **kwargs: notifications.append((message, kwargs)),
        sources_refresh=lambda: events.append("refresh"),
        snapshot_source_session=lambda current_state: events.append(
            ("snapshot", [source.value for source in current_state.sources])
        ),
        logger=logging.getLogger("test_add_source_to_state"),
    )

    assert added is True
    assert state.source_session_restored is False
    assert state.sources[0].value == "https://example.com"
    assert events == [("snapshot", ["https://example.com"]), "refresh", "step"]
    assert notifications == []


def test_add_source_to_state_rejects_duplicate_with_warning() -> None:
    notifications: list = []
    state = _DummyState(sources=[SimpleNamespace(value="https://example.com")])

    added = state_helpers.add_source_to_state(
        state=state,
        source_item_factory=lambda **kwargs: SimpleNamespace(**kwargs),
        label="Example",
        value="https://example.com",
        source_type="url",
        notify=lambda message, **kwargs: notifications.append((message, kwargs)),
        sources_refresh=lambda: None,
        snapshot_source_session=lambda _state: None,
        logger=logging.getLogger("test_add_source_to_state_duplicate"),
    )

    assert added is False
    assert notifications == [("同じソースが追加されています", {"color": "warning"})]


def test_remove_source_from_state_clears_empty_session_and_refreshes() -> None:
    events: list = []
    state = _DummyState(
        sources=[SimpleNamespace(id="source-1", value="https://example.com")],
        step_refresh_callback=lambda: events.append("step"),
    )

    state_helpers.remove_source_from_state(
        state=state,
        source_id="source-1",
        sources_refresh=lambda: events.append("refresh"),
        clear_source_session_sources=lambda current_state: events.append(("clear", len(current_state.sources))),
        snapshot_source_session=lambda _state: events.append("snapshot"),
    )

    assert state.sources == []
    assert events == [("clear", 0), "refresh", "step"]


def test_restore_recent_uploaded_sources_marks_review_and_refreshes(tmp_path: Path) -> None:
    now = time.time()
    recent = tmp_path / "recent.md"
    recent.write_text("markdown", encoding="utf-8")
    os.utime(recent, (now - 1, now - 1))
    state = _DummyState()
    events: list = []

    restored = state_helpers.restore_recent_uploaded_sources(
        state=state,
        upload_dir=tmp_path,
        image_extensions={".png", ".jpg", ".jpeg", ".webp"},
        source_item_factory=lambda **kwargs: SimpleNamespace(**kwargs),
        mark_source_session_review_required=lambda _state: events.append("mark_review"),
        snapshot_source_session=lambda _state: events.append("snapshot"),
        sources_refresh=lambda: events.append("refresh"),
        max_age_sec=600,
    )

    assert restored == 1
    assert state.sources[0].label == "recent.md"
    assert events == ["mark_review", "snapshot", "refresh"]


def test_handle_upload_saves_then_adds_source(tmp_path: Path) -> None:
    async def fake_io_bound(fn, *args):  # type: ignore[no-untyped-def]
        return fn(*args)

    added: list = []
    notifications: list = []

    asyncio.run(
        state_helpers.handle_upload(
            _ContentEvent("memo.txt", io.BytesIO(b"hello")),
            upload_dir=tmp_path,
            image_extensions={".png", ".jpg", ".jpeg", ".webp"},
            io_bound_runner=fake_io_bound,
            add_source=lambda label, value, source_type: added.append((label, value, source_type)) is None,
            notify=lambda message, **kwargs: notifications.append((message, kwargs)),
            logger=logging.getLogger("test_handle_upload"),
        )
    )

    assert added and added[0][0] == "memo.txt"
    assert added[0][2] == "file"
    assert Path(added[0][1]).read_bytes() == b"hello"
    assert notifications[-1][1] == {"color": "primary"}
