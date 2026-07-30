from __future__ import annotations

from core.application.markdown_report_service import (
    build_detailed_markdown_report,
    export_detailed_markdown_report,
)


def _sample_bundle() -> dict:
    return {
        "run": {
            "id": 153,
            "url": "https://example.com/",
            "analyzed_at": "2026-06-08T10:30:27",
            "seo_score": 62,
            "aio_score": 48,
            "legal_score": 90,
            "total_issues": 4,
        },
        "snapshot": {
            "meta": {
                "run_id": 153,
                "url": "https://example.com/",
                "industry": "介護",
                "site_type": "企業",
                "platform": "その他CMS",
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
                    "ページ役割: 料金/予約/相談・資料請求ページ",
                    "不足: 費用・条件・必要情報, 変更・注意事項・対象外条件",
                    "最初の一手: 条件説明を追加",
                ],
                "blocking_issues": [
                    {"title": "AI認識", "detail": "引用しやすい定義ブロックが不足しています。"}
                ],
                "intent_role_map": {
                    "page_role": "料金/予約/相談・資料請求ページ",
                    "user_intent": "費用と相談条件を確認したい",
                    "missing_content": ["費用・条件・必要情報", "変更・注意事項・対象外条件"],
                    "recommended_action": "CTA直前に条件説明を追加する",
                    "engineer_notes": {
                        "fix_locations": ["本文上部", "CTA直前", "FAQセクション"],
                        "structured_data": "FAQPage / Service",
                        "internal_links": "関連ページから相談ページへリンク",
                    },
                },
            },
            "writing_workspace": {
                "faq_suggestions": [
                    {
                        "question": "相談前に何を準備すればよいですか？",
                        "answer_outline": "必要情報、相談窓口、所要時間をまとめる。",
                        "recommended_section": "CTA直前",
                        "schema_candidate": "FAQPage",
                    }
                ],
                "citation_phrases": [
                    {"phrase": "介護用品レンタルの相談", "template": "料金と利用開始までの流れを明記する。"}
                ],
            },
            "implementation_workspace": {
                "legacy_page_summary": {
                    "found_count": 1,
                    "detail": "古いページが 1 件公開されたままです。",
                    "technical_detail": "200 / index可能 / canonicalなし",
                    "pages": [{"final_url": "https://example.com/data.html"}],
                    "engineer_tasks": [
                        {"title": "恒久リダイレクト", "detail": "301 または 308 を返す。"}
                    ],
                    "verification_steps": [
                        {"title": "HTTP応答", "detail": "curl -I で確認する。"}
                    ],
                },
                "link_health_summary": {
                    "detail": "孤立ページが多数あります。",
                    "link_opportunities": [
                        {
                            "source_url": "https://example.com/",
                            "target_url": "https://example.com/service/",
                            "recommended_anchor": "サービス詳細",
                        }
                    ],
                },
                "accessibility_improvements": {
                    "score": 76,
                    "actions": [
                        {
                            "title": "画像に内容が分かる説明文を入れる",
                            "affected_count": 2,
                            "engineer": {
                                "target_element": '<img src="product.jpg">',
                                "task": "内容画像には説明的なaltを設定してください。",
                                "verification": "主要画像のaltを確認する。",
                                "detection_source": "HTML自動検出",
                                "raw_issue": "altなし",
                            },
                        }
                    ],
                },
                "maintenance_risk": {
                    "score": 54,
                    "summary": "保守会社に確認すべき公開サイン 3件 / 保守更新スコア 54点",
                    "cards": [
                        {
                            "title": "更新整合性チェック",
                            "status_label": "注意",
                            "summary": "サイト上では新しい日付が見えますが、sitemap lastmod が古い可能性があります。",
                            "bullets": ["visible date: 2026-05-01", "sitemap lastmod: 2022-03-01"],
                        },
                        {
                            "title": "フォーム確認",
                            "status_label": "参考",
                            "summary": "外部入力フォームあり。公開HTML上では基本的な対策痕跡があります。",
                            "metrics": {
                                "form_count": 1,
                                "personal_fields": 1,
                                "csrf_or_nonce": 1,
                                "privacy_consent": 1,
                                "captcha": 0,
                                "file_upload": 0,
                            },
                        },
                    ],
                },
            },
            "technical_workspace": {
                "site_health_checks": [
                    {
                        "key": "security",
                        "title": "セキュリティ",
                        "detail": "スコア 35点 / 要対応 / 公開技術リスク 2件",
                        "issues": [
                            "古いjQueryが読み込まれています",
                            "WordPress REST APIでユーザー情報が見えます",
                        ],
                        "engineer_tasks": [
                            {
                                "title": "古いjQueryが読み込まれています",
                                "target": "https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js",
                                "work": "jQuery 3.5.0以上への更新、依存テーマ/プラグインの互換確認をしてください。",
                                "verify": "ページソースで jQuery 3.5.0 以上に更新されたことを確認",
                                "commands": ["curl -sL https://example.com/ | rg \"jquery\""],
                                "pass_condition": "jQuery 3.5.0 以上になっている状態。",
                                "severity": "high",
                                "source": "jquery_before_3_5",
                            }
                        ],
                    },
                    {
                        "key": "accessibility",
                        "title": "アクセシビリティ",
                        "detail": "スコア 90点 / 改善スコア: 良好",
                    }
                ]
            },
            "exports": {
                "priority_actions": [
                    {
                        "action_id": "act_example",
                        "priority_rank": 1,
                        "status": "unverified",
                        "status_label": "未確認",
                        "audience": {"role": "運用", "label": "対象ページで確認"},
                        "evidence": {"source": "SEO", "detail": "本文の構成"},
                        "area": "SEO改善",
                        "title": "条件説明を追加",
                        "action": "CTA直前に費用・条件を追記する",
                        "role": "運用",
                        "kpi": "問い合わせ率",
                    }
                ]
            },
        },
        "result": {
            "url": "https://example.com/",
            "seo_results": {
                "scores": {
                    "technical_score": 6.6666666667,
                }
            },
            "aio_results": {
                "details": {
                    "pid": 0.753,
                }
            },
            "site_health": {
                "accessibility": {
                    "source": "browser",
                    "formatted": {"detection_source": "browser"},
                }
            },
            "internal_link_summary": {
                "total_known_pages": 500,
                "orphan_count": 440,
                "low_link_count": 70,
            },
            "legacy_page_report": {"found_count": 1},
        },
    }


def test_build_detailed_markdown_report_includes_actionable_sections() -> None:
    content = build_detailed_markdown_report(_sample_bundle())

    assert "# コトミガキ 詳細分析レポート" in content
    assert "- 分析日時: 2026-06-08 19:30 JST" in content
    assert "- 出力日時: " in content
    assert "JST" in content
    assert "## 0. このURL固有の見立て" in content
    assert "ページ役割: 料金/予約/相談・資料請求ページ" in content
    assert "不足: 費用・条件・必要情報" in content
    assert "料金/予約/相談・資料請求ページ" in content
    assert "相談前に何を準備すればよいですか？" in content
    assert "https://example.com/data.html" in content
    assert "https://example.com/ -> https://example.com/service/" in content
    assert "公開技術リスク 2件" in content
    assert "## 6. 保守・更新管理" in content
    assert "保守会社に確認すべき公開サイン 3件" in content
    assert "更新整合性チェック" in content
    assert "確認コマンド: curl -sL https://example.com/ | rg &quot;jquery&quot;" in content or "確認コマンド: curl -sL https://example.com/ | rg \"jquery\"" in content
    assert "合格条件: jQuery 3.5.0 以上になっている状態。" in content
    assert "古いjQueryが読み込まれています" in content
    assert "jQuery 3.5.0以上への更新" in content
    assert "jquery_before_3_5" in content
    assert "実ブラウザ自動検出" in content
    assert "アクセシビリティ技術詳細" in content
    assert "### エンジニア作業票" in content
    assert "- アクションID: act_example" in content
    assert "- 状態: 未確認" in content
    assert "- 対象読者: 対象ページで確認" in content
    assert "- 根拠: 本文の構成" in content
    assert "| No | 分類 | 対象 | 作業 | 確認方法 | 検出元 |" in content
    assert "アクセシビリティ" in content
    assert "&lt;img src=\"product.jpg\"&gt;" in content
    assert "行うべき作業" in content
    assert "SEO 技術基盤: 67 / 100 相当" in content
    assert "AIO 主題の明確さ: 75 / 100 相当" in content
    assert "SEO technical_score" not in content
    assert "AIO pid" not in content
    assert "追加API送信は行いません" in content


def test_export_detailed_markdown_report_writes_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("core.application.markdown_report_service.EXPORTS_DIR", tmp_path)

    path = export_detailed_markdown_report(_sample_bundle())

    assert path.name.startswith("detailed-report-run-153-")
    assert path.suffix == ".md"
    assert "条件説明を追加" in path.read_text(encoding="utf-8")
