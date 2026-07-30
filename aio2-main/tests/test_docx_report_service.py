from __future__ import annotations

from zipfile import ZipFile

from core.application.docx_report_service import export_detailed_docx_report


def _sample_bundle() -> dict:
    return {
        "run": {
            "id": 153,
            "url": "https://example.com/",
            "analyzed_at": "2026-06-08T10:30:27",
        },
        "snapshot": {
            "meta": {
                "run_id": 153,
                "url": "https://example.com/",
                "industry": "製造",
                "site_type": "企業",
                "business_goal": "自動判定",
            },
            "header": {
                "integrated_score": 56,
                "seo_score": 62,
                "aio_score": 48,
                "legal_score": 90,
                "priority_level": "中",
                "issue_count": 4,
            },
            "summary_workspace": {
                "summary_lines": [
                    "ページ役割: 集客ページ",
                    "不足: 比較・判断材料 / 次の行動",
                    "最初の一手: CTA直前に比較材料を追加",
                ],
            },
            "exports": {
                "priority_actions": [
                    {
                        "area": "SEO改善",
                        "title": "比較材料を追加",
                        "action": "CTA直前に比較表とFAQを追加する",
                        "role": "制作/開発",
                        "kpi": "CVR / 回遊率",
                    }
                ]
            },
            "implementation_workspace": {
                "legacy_page_summary": {
                    "detail": "古い公開ページが1件あります。",
                    "pages": [{"final_url": "https://example.com/data.html"}],
                    "engineer_tasks": [
                        {"title": "301を設定", "detail": "現行ページへ恒久リダイレクトします。"}
                    ],
                    "verification_steps": [
                        {"title": "HTTP確認", "detail": "curl -I で 301 を確認します。"}
                    ],
                },
                "accessibility_improvements": {
                    "actions": [
                        {
                            "title": "画像に説明文を追加",
                            "affected_count": 2,
                            "engineer": {
                                "target_element": '<img src="product.jpg">',
                                "task": "意味のある alt を設定します。",
                                "verification": "HTML上の alt と読み上げ結果を確認します。",
                                "detection_source": "HTML自動検出",
                            },
                        }
                    ]
                },
            },
            "technical_workspace": {
                "site_health_checks": [
                    {
                        "key": "accessibility",
                        "title": "アクセシビリティ",
                        "detail": "スコア 90 / 改善アクションあり",
                    }
                ]
            },
        },
        "result": {
            "url": "https://example.com/",
            "site_health": {
                "accessibility": {
                    "source": "html",
                    "formatted": {"detection_source": "html"},
                }
            },
            "internal_link_summary": {
                "total_known_pages": 50,
                "orphan_count": 4,
                "low_link_count": 7,
            },
            "legacy_page_report": {"found_count": 1},
        },
    }


def test_export_detailed_docx_report_writes_docx(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("core.application.docx_report_service.EXPORTS_DIR", tmp_path)

    path = export_detailed_docx_report(_sample_bundle())

    assert path.name.startswith("detailed-report-run-153-")
    assert path.suffix == ".docx"
    assert path.exists()
    assert path.stat().st_size > 0

    with ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")

    assert "コトミガキ" in document_xml
    assert "エンジニア作業票" in document_xml
    assert "画像に説明文を追加" in document_xml
    assert "https://example.com/data.html" in document_xml
