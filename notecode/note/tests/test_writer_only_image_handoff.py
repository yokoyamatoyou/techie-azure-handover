from __future__ import annotations

import json
import sys

from note.writer_only_image_handoff import build_writer_only_image_context


def _write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_builds_context_from_result_title_and_body_only():
    context = build_writer_only_image_context(
        {
            "title": "相談前に整理すること",
            "body": "# 相談前に整理すること\n\n私たちは相談前の判断軸を整理します。",
        }
    )

    assert context["title"] == "相談前に整理すること"
    assert context["lead"] == "私たちは相談前の判断軸を整理します。"
    assert context["body"].startswith("# 相談前")
    assert context["article_type"] == "explanatory_article"
    assert context["source_claims"] == []


def test_title_falls_back_to_markdown_h1():
    context = build_writer_only_image_context(
        {"body": "# H1から取るタイトル\n\n本文です。", "article_type": "branding"}
    )

    assert context["title"] == "H1から取るタイトル"
    assert context["article_type"] == "branding"


def test_lead_falls_back_to_first_non_heading_paragraph_and_is_shortened():
    long_paragraph = "私たちは" + "相談前の整理を重視します。" * 40
    context = build_writer_only_image_context(
        {"body": f"# タイトル\n\n## 見出し\n\n{long_paragraph}\n\n次の段落"}
    )

    assert context["lead"].startswith("私たちは相談前の整理")
    assert len(context["lead"]) <= 260
    assert context["lead"].endswith("...")


def test_brief_internal_category_overrides_result_article_type(tmp_path):
    _write_json(tmp_path / "brief.json", {"internal_category": "industry_analysis"})

    context = build_writer_only_image_context(
        {"body": "# タイトル\n\n本文", "article_type": "branding", "artifact_root": str(tmp_path)}
    )

    assert context["article_type"] == "explanatory_article"


def test_route_v_industry_analysis_semantic_key_uses_explanatory_image_type(tmp_path):
    _write_json(
        tmp_path / "input_contract.json",
        {
            "article_type": "industry_analysis",
            "semantic_article_key": "industry_analysis",
        },
    )

    context = build_writer_only_image_context(
        {"body": "# 市場背景を見る\n\n私たちは資料に基づいて背景を説明します。", "artifact_root": str(tmp_path)}
    )

    assert context["article_type"] == "explanatory_article"


def test_route_v_company_intro_semantic_key_sets_image_article_type(tmp_path):
    _write_json(
        tmp_path / "input_contract.json",
        {
            "article_type": "branding",
            "semantic_article_key": "company_introduction",
        },
    )

    context = build_writer_only_image_context(
        {"body": "# 京都工業株式会社の会社紹介\n\n私たちはデータ入力を扱っています。", "artifact_root": str(tmp_path)}
    )

    assert context["article_type"] == "company_introduction"


def test_explicit_image_article_type_overrides_internal_article_type(tmp_path):
    _write_json(tmp_path / "brief.json", {"internal_category": "branding"})

    context = build_writer_only_image_context(
        {
            "body": "# タイトル\n\n本文",
            "image_article_type": "company_introduction",
            "article_type": "branding",
            "artifact_root": str(tmp_path),
        }
    )

    assert context["article_type"] == "company_introduction"


def test_explicit_0506_genre_aliases_use_supported_image_article_types():
    expected = {
        "company_service_intro": "company_introduction",
        "market_explanation": "explanatory_article",
        "comparison_guide": "comparative_review",
        "daily_activity": "daily_story",
    }

    for raw, normalized in expected.items():
        context = build_writer_only_image_context(
            {
                "body": "# タイトル\n\n本文",
                "image_article_type": raw,
                "article_type": "branding",
            }
        )

        assert context["article_type"] == normalized


def test_source_bundle_claims_are_limited_and_do_not_include_full_text(tmp_path):
    _write_json(tmp_path / "source_bundle.json", {"sources": [_source_with_claims("A", 4), _source_with_claims("B", 4)]})

    context = build_writer_only_image_context(
        {"title": "タイトル", "body": "本文", "artifact_root": str(tmp_path)}
    )

    assert len(context["source_claims"]) == 6
    assert context["source_claims"][0] == {
        "claim": "A claim 1",
        "source_title": "A",
        "source_url": "https://example.com/a",
    }
    assert "full_text" not in json.dumps(context, ensure_ascii=False)


def test_source_bundle_can_fall_back_to_brief_embedded_bundle(tmp_path):
    _write_json(
        tmp_path / "brief.json",
        {
            "internal_category": "case_study",
            "source_bundle": {"sources": [_source_with_claims("Brief", 2)]},
        },
    )

    context = build_writer_only_image_context({"body": "# タイトル\n\n本文"}, artifact_root=tmp_path)

    assert context["article_type"] == "case_study"
    assert [item["claim"] for item in context["source_claims"]] == ["Brief claim 1", "Brief claim 2"]
    assert "full_text" not in json.dumps(context, ensure_ascii=False)


def test_missing_or_unreadable_artifact_root_fails_open():
    context = build_writer_only_image_context(
        {"title": "タイトル", "body": "本文", "artifact_root": "Z:/missing/writer-only-artifact"}
    )

    assert context["title"] == "タイトル"
    assert context["article_type"] == "explanatory_article"
    assert context["source_claims"] == []


def test_import_does_not_load_legacy_body_generation_modules():
    bad = [
        name
        for name in sys.modules
        if any(x in name for x in ("route_0506", "current_mainline", "newalgorithm_pipeline", "simple_note_pipeline"))
    ]

    assert bad == []


def _source_with_claims(title: str, count: int) -> dict:
    return {
        "title": title,
        "url": f"https://example.com/{title.lower()}",
        "normalized_url": f"https://example.com/{title.lower()}",
        "excerpt": f"{title} excerpt",
        "full_text": "must never be copied",
        "claims": [f"{title} claim {index}" for index in range(1, count + 1)],
    }
