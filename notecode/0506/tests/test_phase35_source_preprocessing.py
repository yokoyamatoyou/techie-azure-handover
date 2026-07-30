from app.services.source_acquisition import SourceSpan, ingest_manual_text
from app.services.source_preprocessor import build_generation_source_packet


def test_p35_s1_caps_one_source_at_12000_chars_and_warns_without_silent_cut():
    source = ingest_manual_text("あ" * 13050, "長い手入力")

    packet = build_generation_source_packet(source)

    assert packet.metadata["source_text_char_limit"] == 12000
    assert packet.metadata["original_text_chars"] == 13050
    assert packet.metadata["included_text_chars"] == 12000
    assert packet.metadata["excluded_text_chars"] == 1050
    assert packet.metadata["extraction_confidence"] == "high"
    assert packet.metadata["can_proceed"] is True
    assert packet.metadata["source_over_limit"] is True
    assert sum(len(chunk.text) for chunk in packet.chunks) == 12000
    assert len(packet.chunks) == 3
    assert any("source_over_limit" in warning for warning in packet.warnings)


def test_p35_s1_keeps_source_span_traceability_inside_chunks():
    source = ingest_manual_text("本文A" * 1000, "短い手入力")

    packet = build_generation_source_packet(source)

    assert packet.chunks[0].source_span_ids == ["manual_001"]
    assert packet.chunks[0].source_locations == ["manual:1"]
    assert packet.chunks[0].char_start == 0
    assert packet.chunks[0].char_end == len(packet.chunks[0].text)
    assert packet.metadata["source_over_limit"] is False


def test_p4_preprocessing_packet_carries_note_hatena_natural_blog_style_target():
    source = ingest_manual_text("私たちは地域の活動を紹介します。" * 50, "ブログ素材")

    packet = build_generation_source_packet(source, platform_style_target_id="note_hatena_natural_blog")
    target = packet.metadata["platform_style_target"]

    assert packet.metadata["preprocessing_method"] == "deterministic_source_packet_v1"
    assert target["output_platforms"] == ["note", "hatena_blog"]
    assert "heading_readability" in target["structure_signals"]
    assert "paragraph_rhythm" in target["structure_signals"]
    assert any("note.com" in url for url in target["research_refs"])
    assert any("hatenablog.com" in url for url in target["research_refs"])


def test_p35_s1_multi_span_source_stops_at_global_source_limit():
    source = ingest_manual_text("仮", "上書き用")
    object.__setattr__(
        source,
        "source_spans",
        [
            SourceSpan("s1", "a" * 7000, "manual:1"),
            SourceSpan("s2", "b" * 7000, "manual:2"),
        ],
    )
    object.__setattr__(source, "extracted_text", "a" * 7000 + "b" * 7000)

    packet = build_generation_source_packet(source)

    assert sum(len(chunk.text) for chunk in packet.chunks) == 12000
    assert packet.chunks[-1].source_span_ids == ["s2"]
    assert packet.chunks[-1].text == "b" * 1000
