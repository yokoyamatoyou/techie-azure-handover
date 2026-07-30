from __future__ import annotations

import io
import json
import tarfile

from tools.extract_knb_metrics_style_card import (
    build_artifact_metrics_comparison,
    build_knb_style_card,
    parse_knb_archive,
    write_comparison_outputs,
    write_outputs,
)


def _fake_knb_archive() -> bytes:
    payloads = {
        "KNBC_v1.0_090925_utf8/corpus1/KN001_Test_1/KN001_Test_1-1-1-01": "\n".join(
            [
                "# S-ID:dummy",
                "* 0 1D",
                "今日は キョウ 名詞",
                "静かだ シズカダ 形容詞",
                "。 。 特殊",
                "EOS",
            ]
        ),
        "KNBC_v1.0_090925_utf8/corpus1/KN001_Test_1/KN001_Test_1-1-2-01": "\n".join(
            [
                "# S-ID:dummy",
                "* 0 1D",
                "ただし タダシ 接続詞",
                "無理は ムリハ 名詞",
                "しない シナイ 動詞",
                "。 。 特殊",
                "EOS",
            ]
        ),
        "KNBC_v1.0_090925_utf8/README.txt": "license only",
    }
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:bz2") as archive:
        for name, text in payloads.items():
            encoded = text.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(encoded)
            archive.addfile(info, io.BytesIO(encoded))
    return stream.getvalue()


def test_parse_knb_archive_reconstructs_sentences_without_readme() -> None:
    parsed = parse_knb_archive(_fake_knb_archive())

    assert len(parsed["sentences"]) == 2
    assert len(parsed["articles"]) == 1
    assert all("license" not in sentence for sentence in parsed["sentences"])


def test_build_knb_style_card_is_metrics_only() -> None:
    card = build_knb_style_card(_fake_knb_archive(), source_url="https://example.test/knb.tar.bz2")

    assert card["schema_version"] == "reference_style_card_v1"
    assert card["source_policy"]["raw_text_stored"] is False
    assert card["extraction_notes"]["article_text_in_prompt"] is False
    assert card["extraction_notes"]["raw_sentence_examples_saved"] is False
    assert card["sample_set"]["count"] == 1
    assert card["sample_set"]["sentence_count"] == 2
    serialized = json.dumps(card, ensure_ascii=False)
    assert "今日は静かだ。" not in serialized
    assert "ただし無理はしない。" not in serialized


def test_write_outputs_do_not_include_raw_examples(tmp_path) -> None:
    card = build_knb_style_card(_fake_knb_archive())
    outputs = write_outputs(card, tmp_path, source_url="https://example.test/knb.tar.bz2")

    style_card = outputs["style_card"].read_text(encoding="utf-8")
    report = outputs["report"].read_text(encoding="utf-8")
    audit = json.loads(outputs["audit"].read_text(encoding="utf-8"))

    assert "今日は静かだ。" not in style_card
    assert "ただし無理はしない。" not in report
    assert audit["raw_text_saved"] is False
    assert audit["live_generation_executed"] is False


def test_comparison_outputs_are_metrics_only(tmp_path) -> None:
    card = build_knb_style_card(_fake_knb_archive())
    route_a = tmp_path / "latest_generation_output.txt"
    route_a.write_text(
        "\n".join(
            [
                "# Latest Generation Output",
                "proposition_low_info_ratio: 0.0",
                "",
                "社内の確認を進めます。",
                "",
                "## 見出し",
                "",
                "ただし無理はしない。",
                "",
                "## 参考情報",
                "- source",
            ]
        ),
        encoding="utf-8",
    )
    comparison = build_artifact_metrics_comparison(card, route_a_output=route_a)
    outputs = write_comparison_outputs(comparison, tmp_path)

    serialized = outputs["comparison_json"].read_text(encoding="utf-8")
    report = outputs["comparison_report"].read_text(encoding="utf-8")

    assert comparison["route_a_metrics"]["sentence_count"] == 2
    assert comparison["live_generation_executed"] is False
    assert "社内の確認を進めます。" not in serialized
    assert "ただし無理はしない。" not in report
