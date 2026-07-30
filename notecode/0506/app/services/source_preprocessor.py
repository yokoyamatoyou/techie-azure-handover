from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.services.source_acquisition import ExtractedSource, SourceSpan, load_source_config


ROOT = Path(__file__).resolve().parents[2]
STYLE_TARGET_PATH = ROOT / "app" / "config" / "platform_style_targets.yaml"


@dataclass(frozen=True)
class SourceChunk:
    chunk_id: str
    source_id: str
    source_type: str
    text: str
    source_span_ids: list[str]
    source_locations: list[str]
    char_start: int
    char_end: int


@dataclass(frozen=True)
class GenerationSourcePacket:
    source_id: str
    source_type: str
    title: str
    chunks: list[SourceChunk]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


def load_platform_style_targets(path: Path = STYLE_TARGET_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("platform style targets config must be a mapping")
    targets = data.get("platform_style_targets")
    if not isinstance(targets, dict) or not targets:
        raise ValueError("platform_style_targets.yaml must contain platform_style_targets")
    return targets


def build_generation_source_packet(
    source: ExtractedSource,
    platform_style_target_id: str | None = None,
    source_config: dict[str, Any] | None = None,
    style_targets: dict[str, Any] | None = None,
) -> GenerationSourcePacket:
    cfg = source_config or load_source_config()
    preprocessing = cfg.get("generation_preprocessing", {})
    max_source_chars = int(preprocessing.get("max_chars_per_source", 12000))
    max_chunk_chars = int(preprocessing.get("max_chars_per_chunk", 4000))
    target_id = platform_style_target_id or preprocessing.get(
        "default_platform_style_target", "note_hatena_natural_blog"
    )
    targets = style_targets or load_platform_style_targets()
    if target_id not in targets:
        raise ValueError(f"unknown platform_style_target_id: {target_id}")

    chunks = _chunk_source_spans(source, max_source_chars, max_chunk_chars)
    included_chars = sum(len(chunk.text) for chunk in chunks)
    original_chars = len(source.extracted_text)
    warnings = list(source.warnings)
    if original_chars > max_source_chars:
        warnings.append(f"source_over_limit: original {original_chars} chars capped at {max_source_chars}")

    metadata = {
        **source.metadata,
        "platform_style_target_id": target_id,
        "platform_style_target": targets[target_id],
        "source_text_char_limit": max_source_chars,
        "max_chars_per_chunk": max_chunk_chars,
        "original_text_chars": original_chars,
        "included_text_chars": included_chars,
        "excluded_text_chars": max(original_chars - included_chars, 0),
        "extraction_confidence": source.extraction_confidence,
        "can_proceed": source.can_proceed,
        "source_over_limit": original_chars > max_source_chars,
        "preprocessing_method": "deterministic_source_packet_v1",
    }
    return GenerationSourcePacket(
        source_id=source.source_id,
        source_type=source.source_type,
        title=source.title,
        chunks=chunks,
        metadata=metadata,
        warnings=warnings,
    )


def build_generation_source_packets(
    sources: list[ExtractedSource],
    platform_style_target_id: str | None = None,
) -> list[GenerationSourcePacket]:
    return [
        build_generation_source_packet(source, platform_style_target_id=platform_style_target_id)
        for source in sources
    ]


def _chunk_source_spans(
    source: ExtractedSource,
    max_source_chars: int,
    max_chunk_chars: int,
) -> list[SourceChunk]:
    chunks: list[SourceChunk] = []
    used_chars = 0
    chunk_index = 1
    for span in source.source_spans:
        if used_chars >= max_source_chars:
            break
        remaining_source_chars = max_source_chars - used_chars
        span_text = span.text[:remaining_source_chars]
        for piece in _split_text(span_text, max_chunk_chars):
            if not piece:
                continue
            start = used_chars
            used_chars += len(piece)
            chunks.append(
                SourceChunk(
                    chunk_id=f"{source.source_id}_chunk_{chunk_index:03d}",
                    source_id=source.source_id,
                    source_type=source.source_type,
                    text=piece,
                    source_span_ids=[span.span_id],
                    source_locations=[span.location],
                    char_start=start,
                    char_end=used_chars,
                )
            )
            chunk_index += 1
    return chunks


def _split_text(text: str, max_chunk_chars: int) -> list[str]:
    if len(text) <= max_chunk_chars:
        return [text]
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chunk_chars, len(text))
        pieces.append(text[start:end])
        start = end
    return pieces
