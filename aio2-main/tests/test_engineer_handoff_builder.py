from __future__ import annotations

from core.engineer_handoff_builder import build_engineer_handoff_items


def _busy_snapshot() -> dict:
    return {
        "implementation_workspace": {
            "legacy_page_summary": {
                "found_count": 3,
                "pages": [{"final_url": f"https://example.com/old-{index}.html"} for index in range(3)],
                "engineer_tasks": [
                    {"detail": "旧URLを現行ページへ301リダイレクトする。"},
                    {"detail": "canonicalを現行URLへ統一する。"},
                    {"detail": "旧ページのサイト内リンクを削除する。"},
                ],
                "verification_steps": [{"detail": "curl -I で301とcanonicalを確認する。"}],
            },
            "link_health_summary": {
                "link_opportunities": [
                    {
                        "source_url": f"https://example.com/source-{index}/",
                        "target_url": f"https://example.com/target-{index}/",
                        "recommended_anchor": f"サービス{index}",
                        "placement": "本文中段",
                    }
                    for index in range(4)
                ],
                "engineering_steps": [
                    {
                        "fix_location": "/sitemap.xml",
                        "observed": "孤立ページが多いためsitemapと内部リンクを確認する。",
                        "command": "curl -I https://example.com/sitemap.xml",
                    }
                ],
            },
            "schema_summary": {
                "validation_method": "Rich Results Testで確認する。",
                "suggestions": [
                    {
                        "schema_type": "FAQPage",
                        "summary": "FAQ構造化データを追加する。",
                        "required_fields": ["mainEntity", "acceptedAnswer"],
                        "fix_location": "FAQセクションのJSON-LD",
                        "template": '{"@type":"FAQPage"}',
                    },
                    {"schema_type": "Service", "summary": "Service構造化データを追加する。"},
                    {"schema_type": "BreadcrumbList", "summary": "パンくず構造化データを追加する。"},
                ],
            },
            "llms_summary": {
                "fix_location": "/llms.txt",
                "detail": "AI向けサイト要約を設置する。",
                "command": "curl -I https://example.com/llms.txt",
            },
            "site_health_checks": [
                {
                    "key": "security",
                    "title": "セキュリティ",
                    "engineer_tasks": [
                        {
                            "title": "古いjQueryが読み込まれています",
                            "target": "https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js",
                            "work": "jQuery 3.5.0以上への更新、依存テーマ/プラグインの互換確認をしてください。",
                            "verify": "ページソースで jQuery 3.5.0 以上に更新されたことを確認",
                            "severity": "high",
                            "source": "jquery_before_3_5",
                        }
                    ],
                }
            ],
            "accessibility_improvements": {
                "actions": [
                    {
                        "title": f"アクセシビリティ改善 {index}",
                        "affected_count": 1,
                        "group": f"group-{index}",
                        "engineer": {
                            "target_element": f'<img src="missing-{index}.jpg">',
                            "task": f"画像{index}へ説明的なaltを設定する。",
                            "verification": f"画像{index}のaltを検査する。",
                            "detection_source": "HTML自動検出",
                        },
                    }
                    for index in range(5)
                ]
            },
            "technical_actions": [
                {
                    "category": "アクセシビリティ",
                    "area": "技術補足",
                    "title": "抽象的なアクセシビリティ補足",
                    "action": "詳細タブで確認する。",
                }
            ],
        }
    }


def test_handoff_prioritizes_accessibility_before_limit_cutoff() -> None:
    items = build_engineer_handoff_items(_busy_snapshot(), limit=12)

    accessibility_items = [item for item in items if item["category"] == "アクセシビリティ"]
    assert len(accessibility_items) == 5
    assert [item["category"] for item in items[:5]] == ["アクセシビリティ"] * 5
    assert accessibility_items[0]["target"] == '<img src="missing-0.jpg">'
    assert accessibility_items[0]["work"] == "画像0へ説明的なaltを設定する。"
    assert accessibility_items[0]["verify"] == "画像0のaltを検査する。"
    assert "技術補足" not in {item["target"] for item in items}


def test_handoff_adds_concrete_link_and_schema_verification() -> None:
    items = build_engineer_handoff_items(_busy_snapshot(), limit=16)

    link_item = next(item for item in items if item["category"] == "内部リンク")
    assert "curl -I https://example.com/target-0/" in link_item["verify"]
    assert "推奨アンカー" in link_item["verify"]
    assert "再分析後" in link_item["verify"]

    schema_item = next(item for item in items if item["category"].startswith("構造化データ"))
    assert "必須/優先フィールド: mainEntity, acceptedAnswer" in schema_item["work"]
    assert "実装例:" in schema_item["work"]
    assert "Schema Validator" in schema_item["verify"]


def test_handoff_includes_public_security_tasks() -> None:
    items = build_engineer_handoff_items(_busy_snapshot(), limit=16)

    security_item = next(item for item in items if item["source"] == "jquery_before_3_5")

    assert security_item["category"] == "公開技術リスク"
    assert "jquery/2.2.4" in security_item["target"]
    assert "jQuery 3.5.0以上" in security_item["work"]
    assert "ページソース" in security_item["verify"]
