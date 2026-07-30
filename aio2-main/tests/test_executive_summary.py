from __future__ import annotations

from core.ui.reports.executive_summary import (
    _build_improvement_map_payload,
    _build_personalized_summary_text,
    _extract_legal_summary_items,
)
from core.ui.saved_workspace import (
    _build_workspace_improvement_map,
    _dedupe_detail_lines,
    _intent_signal_source_label,
    _page_signal_label,
)


def test_build_personalized_summary_text_mentions_url_context_and_goal() -> None:
    text = _build_personalized_summary_text(
        results={
            "url_type": {"effective": "企業"},
            "final_industry": {"primary": "IT・SaaS"},
        },
        integrated={
            "business_goal": "AI検索での引用増加（GEO/AIO優先）",
            "seo_score": 78,
            "aio_score": 52,
            "geo_score": 38,
            "legal_score": 82,
        },
        summary={"issue_count": 3},
    )

    assert "IT・SaaS" in text
    assert "企業" in text
    assert "AI検索" in text
    assert "内部診断" in text
    assert "3 件" in text


def test_saved_workspace_detail_lines_dedupe_across_sections() -> None:
    seen: set[str] = set()

    highlights = _dedupe_detail_lines(
        [
            "CMSバージョン情報が公開されています",
            "既知脆弱性候補があります",
            "古いjQueryが読み込まれています",
        ],
        seen=seen,
        limit=3,
    )
    issues = _dedupe_detail_lines(
        [
            "・CMSバージョン情報が公開されています",
            "既知脆弱性候補があります",
            "古いjQueryが読み込まれています",
            "robots.txt がHTMLを返している可能性があります",
        ],
        seen=seen,
        limit=3,
    )

    assert highlights == [
        "CMSバージョン情報が公開されています",
        "既知脆弱性候補があります",
        "古いjQueryが読み込まれています",
    ]
    assert issues == ["robots.txt がHTMLを返している可能性があります"]


def test_saved_workspace_internal_signal_labels_are_plain_japanese() -> None:
    assert _intent_signal_source_label("title") == "タイトル"
    assert _intent_signal_source_label("url_path") == "URL"
    assert _intent_signal_source_label("") == "確認箇所"
    assert _page_signal_label("schema_types") == "構造化データ"
    assert _page_signal_label("") == "確認項目"


def test_executive_summary_omits_pass_affiliate_detection_from_alerts() -> None:
    issues = _extract_legal_summary_items(
        {
            "legal_summary": {
                "top_issues": [],
                "medium_priority": [
                    {
                        "representative": {
                            "icon": "✓",
                            "text": "アフィリエイトコンテンツ: 検出されず",
                            "subtext": "",
                            "status_color": "success",
                        },
                        "member_count": 12,
                        "severity": "medium",
                        "evidence_summary": "（他11件）",
                    },
                    {
                        "representative": {
                            "icon": "✕",
                            "text": "PR表記: 未検出",
                            "subtext": "アフィリエイトコンテンツにはPR表記が必要です",
                        }
                    },
                ],
            }
        }
    )

    titles = [item["title"] for item in issues]

    assert all("アフィリエイトコンテンツ: 検出されず" not in title for title in titles)
    assert any("PR表記: 未検出" in title for title in titles)


def test_improvement_map_uses_accessibility_axis_and_keeps_legal_as_alert() -> None:
    payload = _build_improvement_map_payload(
        results={
            "accessibility_score_snapshot": 44,
            "site_health": {
                "ogp": {"formatted": {"score": 80}},
                "security": {"formatted": {"score": 70}},
                "accessibility": {"formatted": {"score": 99}},
            },
            "link_health_report": {"health_score": 20},
            "legal_summary": {"top_issues": [{"title": "表示確認", "summary": "表現を確認"}]},
            "aio_results": {
                "scores": {
                    "citation": {"score": 60},
                    "eeat": {"score": 7},
                },
                "provider_readiness": {
                    "google": {"status": "pass"},
                    "openai_search": {"status": "pass"},
                    "perplexity": {"status": "pass"},
                    "claude_search": {"status": "pass"},
                },
            },
        },
        integrated={
            "seo_score": 82,
            "aio_score": 64,
            "geo_score": 55,
            "legal_score": 10,
        },
    )

    axes = {axis["label"]: axis for axis in payload["axes"]}

    assert "表示安全" not in axes
    assert axes["見やすさ・使いやすさ"]["value"] == 44
    assert axes["見やすさ・使いやすさ"]["hint"] == "自動検出 / 読み上げ / 操作名"
    assert round(axes["保守・技術基盤"]["value"], 1) == 67.5
    assert axes["保守・技術基盤"]["hint"] == "リンク健全性 / OGP / セキュリティ / 保守更新"
    assert any(item["label"] == "表示アドバイス" for item in payload["alerts"])
    assert "表示安全" not in str(payload["options"]["radar"]["indicator"])


def test_improvement_map_falls_back_to_live_accessibility_score() -> None:
    payload = _build_improvement_map_payload(
        results={
            "site_health": {"accessibility": {"formatted": {"score": 73}}},
            "aio_results": {},
        },
        integrated={"seo_score": 70, "aio_score": 60, "geo_score": 50},
    )

    axes = {axis["label"]: axis for axis in payload["axes"]}

    assert axes["見やすさ・使いやすさ"]["value"] == 73


def test_saved_workspace_improvement_map_keeps_radar_with_accessibility_fallback() -> None:
    payload = _build_workspace_improvement_map(
        summary_workspace={
            "technical_foundation_score_snapshot": 64,
            "priority_counts": [
                {"label": "表示アドバイス", "count": 2},
                {"label": "AI公開条件", "count": 1},
            ]
        },
        header={"seo_score": 72, "aio_score": 61, "legal_score": 30},
    )

    axes = {axis["label"]: axis for axis in payload["axes"]}

    assert "表示安全" not in axes
    assert axes["保守・技術基盤"]["value"] == 64
    assert axes["保守・技術基盤"]["hint"] == "リンク健全性 / OGP / セキュリティ / 保守更新"
    assert axes["見やすさ・使いやすさ"]["value"] == 50
    assert axes["見やすさ・使いやすさ"]["hint"] == "自動検出 / 読み上げ / 操作名"
    assert any(item["label"] == "表示アドバイス" for item in payload["alerts"])
    assert payload["options"]["series"][0]["data"][0]["value"]


def test_saved_workspace_improvement_map_uses_accessibility_snapshot() -> None:
    payload = _build_workspace_improvement_map(
        summary_workspace={
            "accessibility_score_snapshot": 68,
            "priority_counts": [],
        },
        header={"seo_score": 72, "aio_score": 61, "legal_score": 30},
    )

    axes = {axis["label"]: axis for axis in payload["axes"]}

    assert axes["見やすさ・使いやすさ"]["value"] == 68
