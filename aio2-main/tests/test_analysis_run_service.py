from __future__ import annotations

import json
from types import SimpleNamespace

from core.application.analysis_run_service import (
    SNAPSHOT_SCHEMA_VERSION,
    TRANSIENT_RETRY_DELAY_SECONDS,
    _build_priority_actions,
    _build_faq_suggestion_payload,
    _build_faq_suggestions,
    _build_implementation_workspace,
    _build_ui_snapshot,
    _extract_legal_summary_items,
    _normalize_status_code,
    _snapshot_status_label,
    build_token_usage_text,
    execute_competitor_analysis,
    load_saved_run_bundle,
    persist_analysis_run,
    execute_primary_analysis,
    _snapshot_needs_refresh,
)
from core.industry_detector import IndustryAnalysis
from seo_aio_engine import ScrapeBlockedError
from core.safe_fetch import UnsafeURLError


class _CompetitorAnalyzerStub:
    def __init__(self, results: dict | None = None, *, blocked: bool = False) -> None:
        self._results = results or {"url": "https://competitor.example.com"}
        self._blocked = blocked

    def analyze_url(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self._blocked:
            raise ScrapeBlockedError("https://competitor.example.com", "blocked by test")
        return self._results

    def generate_competitor_action_advice(self, current_results, competitor_results, max_actions=5):  # type: ignore[no-untyped-def]
        return {"actions": [{"title": "差分を埋める"}], "max_actions": max_actions}


class _PrimaryAnalyzerStub:
    def __init__(self, failures: int = 0, exc_factory=None) -> None:
        self.failures = failures
        self.calls = 0
        self.exc_factory = exc_factory or (lambda: RuntimeError("transient"))

    def analyze_url(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls <= self.failures:
            raise self.exc_factory()
        return {"url": "https://example.com", "integrated_results": {"seo_score": 80, "aio_score": 70}}


def test_execute_competitor_analysis_returns_results_and_advice() -> None:
    outcome = execute_competitor_analysis(
        "https://competitor.example.com",
        "一般",
        50,
        True,
        "自動判定",
        {"url": "https://example.com"},
        analyzer_factory=lambda **kwargs: _CompetitorAnalyzerStub(),
    )

    assert outcome.results == {"url": "https://competitor.example.com"}
    assert outcome.action_advice == {"actions": [{"title": "差分を埋める"}], "max_actions": 5}
    assert outcome.blocked is None
    assert outcome.error is None


def test_legal_summary_omits_pass_affiliate_detection_from_actions() -> None:
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


def test_execute_competitor_analysis_returns_block_reason() -> None:
    outcome = execute_competitor_analysis(
        "https://competitor.example.com",
        "一般",
        50,
        True,
        "自動判定",
        {"url": "https://example.com"},
        analyzer_factory=lambda **kwargs: _CompetitorAnalyzerStub(blocked=True),
    )

    assert outcome.results is None
    assert outcome.action_advice is None
    assert outcome.blocked == "blocked by test"
    assert outcome.error is None


def test_ui_snapshot_promotes_legacy_pages_without_extra_clean_state_card() -> None:
    snapshot = _build_ui_snapshot(
        99,
        "2026-06-07T10:00:00",
        {
            "url": "https://example.com",
            "timestamp": "2026-06-07T10:00:00",
            "integrated_results": {
                "seo_score": 80,
                "aio_score": 70,
                "legal_score": 90,
                "integrated_score": 75,
                "business_goal": "自動判定",
            },
            "final_industry": {"primary": "IT・SaaS"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "summary": {"improvements": [], "issue_count": 1},
            "warnings": [],
            "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
            "seo_results": {"technical": {}, "structure": {}, "basics": {}, "immediate_actions": [], "web_vitals": {}},
            "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
            "legacy_page_report": {
                "status": "fail",
                "found_count": 2,
                "checked_count": 19,
                "pages": [
                    {
                        "url": "https://example.com/data.html",
                        "final_url": "https://example.com/data.html",
                        "reason": "200 / index可能 / canonicalなし",
                    }
                ],
                "recommendations": ["301リダイレクトしてください。"],
            },
        },
        None,
    )

    assert snapshot["header"]["top_actions"][0]["title"] == "古い公開ページを整理"
    assert "古い情報" in snapshot["header"]["top_actions"][0]["action"]
    assert snapshot["summary_workspace"]["blocking_issues"][0]["label"] == "公開リスク"
    assert "検索やAI回答" in snapshot["summary_workspace"]["blocking_issues"][0]["detail"]
    assert any(
        item["label"] == "公開リスク" and item["count"] == 2
        for item in snapshot["summary_workspace"]["priority_counts"]
    )
    assert snapshot["technical_workspace"]["legacy_pages"]["pages"][0]["final_url"] == "https://example.com/data.html"
    assert "canonicalなし" in snapshot["technical_workspace"]["legacy_pages"]["technical_detail"]
    assert snapshot["technical_workspace"]["legacy_pages"]["engineer_tasks"][1]["title"] == "サーバー側で恒久リダイレクトを設定する"
    assert "curl -I" in snapshot["technical_workspace"]["legacy_pages"]["verification_steps"][0]["detail"]


def test_ui_snapshot_ranks_critical_accessibility_before_seo_aio_actions() -> None:
    snapshot = _build_ui_snapshot(
        201,
        "2026-06-11T10:00:00",
        {
            "url": "https://example.com/accessibility",
            "timestamp": "2026-06-11T10:00:00",
            "integrated_results": {
                "seo_score": 62,
                "aio_score": 58,
                "legal_score": 90,
                "integrated_score": 64,
                "business_goal": "自動判定",
            },
            "final_industry": {"primary": "IT・SaaS"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "summary": {"improvements": [], "issue_count": 3},
            "warnings": [],
            "site_health": {
                "accessibility": {
                    "formatted": {"score": 48},
                    "raw": {
                        "score": 48,
                        "issue_groups": [
                            {
                                "id": "image_alt",
                                "label": "img alt",
                                "weight": 14,
                                "status": "needs_work",
                                "total_count": 1,
                                "affected_count": 1,
                                "issues": [{"element": '<img src="hero.jpg">', "issue": "altなし"}],
                            },
                            {
                                "id": "interactive_names",
                                "label": "a/button accessible name候補",
                                "weight": 12,
                                "status": "needs_work",
                                "total_count": 1,
                                "affected_count": 1,
                                "issues": [{"element": "<button>", "issue": "button名なし"}],
                            },
                            {
                                "id": "form_labels",
                                "label": "input/select/textarea label",
                                "weight": 12,
                                "status": "needs_work",
                                "total_count": 1,
                                "affected_count": 1,
                                "issues": [{"element": '<input name="email">', "issue": "labelなし"}],
                            },
                        ],
                    },
                }
            },
            "deep_recommendations": {
                "business": [
                    {
                        "title": "冒頭要約の追加",
                        "recommended_action": "結論をページ冒頭に追加する",
                        "expected_impact": "High",
                    }
                ],
                "technical": [],
                "title_rewrites": [],
                "description_rewrites": [],
            },
            "seo_results": {
                "immediate_actions": [
                    {"title": "title改善", "action": "検索意図をtitleに入れる", "impact": "High"}
                ],
                "technical": {},
                "structure": {},
                "basics": {},
                "web_vitals": {},
            },
            "aio_results": {
                "provider_readiness": {"google": {"status": "pass"}},
                "immediate_actions": [
                    {"action": "FAQを追加", "method": "質問と回答を本文に追加する", "reason": "AI認識向け"}
                ],
            },
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
        },
        None,
    )

    top_actions = snapshot["header"]["top_actions"]
    assert [item["category"] for item in top_actions] == ["アクセシビリティ"] * 3
    assert {item["group"] for item in top_actions} == {"image_alt", "interactive_names", "form_labels"}
    assert all(item["impact"] == "高" and item["urgency"] == "高" for item in top_actions)
    assert all("target_element" not in item for item in top_actions)
    assert "<img" not in "\n".join(str(item.get("action", "")) for item in top_actions)
    exported = snapshot["exports"]["priority_actions"]
    seo_aio_index = min(
        index
        for index, item in enumerate(exported)
        if item["category"] in {"SEO", "AIO"}
    )
    assert seo_aio_index > 2


def test_browser_zoom_accessibility_risk_is_not_treated_as_task_blocker() -> None:
    snapshot = _build_ui_snapshot(
        211,
        "2026-06-12T09:30:00",
        {
            "url": "https://example.com/zoom",
            "timestamp": "2026-06-12T09:30:00",
            "integrated_results": {"seo_score": 80, "aio_score": 74, "legal_score": 90, "integrated_score": 78},
            "final_industry": {"primary": "IT・SaaS"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "summary": {"improvements": [], "issue_count": 1},
            "warnings": [],
            "site_health": {
                "accessibility": {
                    "source": "browser",
                    "formatted": {"score": 72},
                    "raw": {
                        "score": 72,
                        "detection_source": "browser",
                        "issue_groups": [
                            {
                                "id": "zoom_scaling",
                                "label": "拡大表示",
                                "weight": 10,
                                "status": "needs_work",
                                "max_severity": "serious",
                                "total_count": 1,
                                "affected_count": 1,
                                "issues": [{"element": "head > meta", "issue": "拡大表示が制限されています"}],
                            }
                        ],
                    },
                }
            },
            "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
            "seo_results": {"immediate_actions": [], "technical": {}, "structure": {}, "basics": {}, "web_vitals": {}},
            "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
        },
        None,
    )

    exported = snapshot["exports"]["priority_actions"]
    zoom_action = next(item for item in exported if item.get("group") == "zoom_scaling")
    assert zoom_action["area"] == "技術補足"
    assert zoom_action["impact"] == "中"
    assert zoom_action["urgency"] == "中"
    header_zoom = next(item for item in snapshot["header"]["top_actions"] if item.get("group") == "zoom_scaling")
    assert header_zoom["area"] == "技術補足"
    assert header_zoom["impact"] == "中"


def test_implementation_workspace_keeps_interactive_accessibility_details() -> None:
    def group(group_id: str, *, weight: int, affected_count: int, element: str) -> dict:
        return {
            "id": group_id,
            "label": group_id,
            "status": "needs_work",
            "weight": weight,
            "affected_count": affected_count,
            "total_count": affected_count,
            "issues": [{"element": element, "issue": f"{group_id} issue"}],
        }

    workspace = _build_implementation_workspace(
        {
            "site_health": {
                "accessibility": {
                    "source": "html",
                    "raw": {
                        "score": 68,
                        "issue_groups": [
                            group("landmarks", weight=20, affected_count=2, element="main/nav/header/footer landmark"),
                            group("form_labels", weight=18, affected_count=8, element='<input name="kw">'),
                            group("h1", weight=17, affected_count=1, element="<h1>"),
                            group("iframe_titles", weight=16, affected_count=5, element='<iframe src="/map">'),
                            group("image_alt", weight=15, affected_count=24, element='<img src="/icon.svg">'),
                            group("interactive_names", weight=12, affected_count=14, element='<button class="header_btn">'),
                        ],
                    },
                }
            }
        },
        actions=[],
    )

    actions = workspace["accessibility_improvements"]["actions"]
    interactive = next(item for item in actions if item["group"] == "interactive_names")
    assert interactive["engineer"]["target_element"] == '<button class="header_btn">'
    assert "操作目的" in interactive["engineer"]["task"]
    assert interactive["engineer"]["verification"]


def test_ui_snapshot_keeps_browser_accessibility_source_in_technical_supplement() -> None:
    snapshot = _build_ui_snapshot(
        212,
        "2026-06-12T10:00:00",
        {
            "url": "https://example.com/browser-accessibility",
            "timestamp": "2026-06-12T10:00:00",
            "integrated_results": {"seo_score": 70, "aio_score": 65, "legal_score": 90, "integrated_score": 72},
            "final_industry": {"primary": "IT・SaaS"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "summary": {"improvements": [], "issue_count": 0},
            "warnings": [],
            "site_health": {
                "accessibility": {
                    "source": "browser",
                    "formatted": {
                        "score": 90,
                        "status": "改善スコア: 良好",
                        "detection_source": "browser",
                        "recommendations": [
                            {"recommendation": "1ページのみの評価でサンプル信頼度がlowです。"}
                        ],
                    },
                    "raw": {"score": 90, "detection_source": "browser"},
                    "wcag": {"method": "実ブラウザ自動検出"},
                }
            },
            "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
            "seo_results": {"immediate_actions": [], "technical": {}, "structure": {}, "basics": {}, "web_vitals": {}},
            "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
        },
        None,
    )

    accessibility_check = next(
        item for item in snapshot["technical_workspace"]["site_health_checks"] if item["key"] == "accessibility"
    )
    assert "実ブラウザ自動検出" in accessibility_check["detail"]
    assert snapshot["technical_workspace"]["accessibility_improvements"]["confirmation_items"]


def test_ui_snapshot_routes_minor_accessibility_to_seo_or_technical_supplement() -> None:
    snapshot = _build_ui_snapshot(
        202,
        "2026-06-11T10:05:00",
        {
            "url": "https://example.com/minor-accessibility",
            "timestamp": "2026-06-11T10:05:00",
            "integrated_results": {"seo_score": 75, "aio_score": 70, "legal_score": 90, "integrated_score": 74},
            "final_industry": {"primary": "IT・SaaS"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "summary": {"improvements": [], "issue_count": 1},
            "warnings": [],
            "site_health": {
                "accessibility": {
                    "formatted": {"score": 88},
                    "raw": {
                        "score": 88,
                        "issue_groups": [
                            {
                                "id": "iframe_titles",
                                "label": "iframe title",
                                "weight": 6,
                                "status": "warning",
                                "total_count": 3,
                                "affected_count": 1,
                                "issues": [{"element": '<iframe src="/map">', "issue": "titleなし"}],
                            }
                        ],
                    },
                }
            },
            "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
            "seo_results": {"immediate_actions": [], "technical": {}, "structure": {}, "basics": {}, "web_vitals": {}},
            "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
        },
        None,
    )

    action = snapshot["exports"]["priority_actions"][0]
    assert action["category"] == "アクセシビリティ"
    assert action["area"] == "技術補足"
    assert action["urgency"] == "中"


def test_ui_snapshot_builds_internal_link_opportunity_map() -> None:
    snapshot = _build_ui_snapshot(
        101,
        "2026-06-07T11:00:00",
        {
            "url": "https://example.com/",
            "timestamp": "2026-06-07T11:00:00",
            "integrated_results": {
                "seo_score": 78,
                "aio_score": 72,
                "legal_score": 90,
                "integrated_score": 76,
                "business_goal": "自動判定",
            },
            "final_industry": {"primary": "生活サービス"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "summary": {"improvements": [], "issue_count": 1},
            "warnings": [],
            "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
            "seo_results": {"technical": {}, "structure": {}, "basics": {}, "immediate_actions": [], "web_vitals": {}},
            "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
            "internal_link_summary": {
                "total_pages": 6,
                "orphan_count": 1,
                "low_link_count": 1,
                "orphan_pages": ["https://example.com/price"],
                "low_link_pages": ["https://example.com/faq"],
            },
            "link_health_report": {
                "health_score": 68,
                "total_known_pages": 6,
                "total_analyzed_pages": 4,
                "orphan_count": 1,
                "low_link_count": 1,
                "hub_pages": ["https://example.com/service", "https://example.com/"],
                "diagnosis": "孤立ページが1件あります。内部リンクを追加してください。",
            },
        },
        None,
    )

    link_health = snapshot["technical_workspace"]["link_health"]
    opportunities = link_health["link_opportunities"]
    assert len(opportunities) == 2
    assert opportunities[0]["source_url"] == "https://example.com/service"
    assert opportunities[0]["target_url"] == "https://example.com/price"
    assert opportunities[0]["recommended_anchor"] == "priceの詳細"
    assert "再分析後" in opportunities[0]["check"]
    assert snapshot["implementation_workspace"]["link_health_summary"]["link_opportunities"] == opportunities


def test_ui_snapshot_builds_search_intent_role_map_for_unknown_b2c_page() -> None:
    snapshot = _build_ui_snapshot(
        102,
        "2026-06-07T12:00:00",
        {
            "url": "https://example.com/service/reservation",
            "timestamp": "2026-06-07T12:00:00",
            "integrated_results": {
                "seo_score": 76,
                "aio_score": 74,
                "legal_score": 90,
                "integrated_score": 77,
                "business_goal": "自動判定",
            },
            "final_industry": {"primary": "生活サービス"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "summary": {"improvements": ["料金と予約の説明をCTA付近へ追加する"], "issue_count": 1},
            "warnings": ["料金説明が不足しています", "予約から利用までの流れが分かりにくい"],
            "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
            "seo_results": {
                "technical": {},
                "structure": {"headings": {"h1": ["写真スタジオ"], "h2": ["料金", "予約方法", "当日の流れ", "相談"]}},
                "basics": {
                    "title": "写真スタジオ 予約・料金案内",
                    "meta_description": "初めての撮影でも分かるよう、料金、予約、当日の流れ、衣装相談をご案内します。",
                },
                "immediate_actions": [],
                "web_vitals": {},
            },
            "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
        },
        None,
    )

    role_map = snapshot["summary_workspace"]["intent_role_map"]
    assert role_map["page_role"] == "料金/予約/相談・資料請求ページ"
    assert role_map["confidence"] in {"high", "medium"}
    assert role_map["confidence_label"] in {"判定根拠: 高", "判定根拠: 中"}
    assert len(role_map["overview_items"]) == 3
    assert {"このページの役割", "不足", "次にやること"} == {item["label"] for item in role_map["overview_items"]}
    assert any(item["source"] == "title" and item["term"] == "料金" for item in role_map["intent_signals"])
    assert any(item["source"] == "heading" and item["term"] == "予約" for item in role_map["intent_signals"])
    assert any(item["source"] == "url_path" and item["term"] == "reservation" for item in role_map["intent_signals"]) or any(
        item["source"] == "url_path" and item["term"] == "予約" for item in role_map["intent_signals"]
    )
    assert "料金/予約/相談・資料請求ページ" in snapshot["technical_workspace"]["intent_role_map"]["page_role"]
    assert snapshot["implementation_workspace"]["intent_role_map"]["engineer_notes"]["add_headings"]
    assert snapshot["implementation_workspace"]["intent_role_map"]["engineer_notes"]["add_faq"]
    assert snapshot["implementation_workspace"]["intent_role_map"]["engineer_notes"]["fix_locations"] == [
        "本文上部",
        "CTA直前",
        "FAQセクション",
        "head内JSON-LD",
        "関連ページの内部リンク",
    ]
    assert "FAQPage" in snapshot["implementation_workspace"]["intent_role_map"]["engineer_notes"]["structured_data"]
    assert any(item["area"] == "検索意図" for item in snapshot["task_workspace"]["actions"])
    assert all(
        item.get("title") != "検索意図・ページ役割マップ"
        for item in snapshot["technical_workspace"]["summary_cards"]
    )
    assert snapshot["technical_workspace"]["intent_role_map"]["intent_signals"]


def test_ui_snapshot_role_map_defaults_to_attraction_without_vertical_lock() -> None:
    snapshot = _build_ui_snapshot(
        103,
        "2026-06-07T12:30:00",
        {
            "url": "https://example.com/guide/start",
            "timestamp": "2026-06-07T12:30:00",
            "integrated_results": {
                "seo_score": 74,
                "aio_score": 70,
                "legal_score": 88,
                "integrated_score": 74,
                "business_goal": "自動判定",
            },
            "final_industry": {"primary": "一般"},
            "url_type": {"effective": "サービス"},
            "platform": {"effective": "カスタム/その他"},
            "summary": {"improvements": ["対象者と次に見るページを冒頭に追加する"], "issue_count": 1},
            "warnings": ["問い合わせ導線が弱い"],
            "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
            "seo_results": {
                "technical": {},
                "structure": {"headings": {"h1": ["初めての利用ガイド"], "h2": ["できること", "流れ", "よくある質問"]}},
                "basics": {
                    "title": "初めての利用ガイド",
                    "meta_description": "サービス内容、利用の流れ、次に確認することをまとめています。",
                },
                "immediate_actions": [],
                "web_vitals": {},
            },
            "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
        },
        None,
    )

    role_map = snapshot["summary_workspace"]["intent_role_map"]
    assert role_map["page_role"] == "集客ページ"
    assert role_map["engineer_notes"]["internal_links"]
    assert role_map["page_role"] not in {"不動産", "飲食", "介護", "アパレル"}


def test_ui_snapshot_role_map_handles_public_application_without_purchase_bias() -> None:
    snapshot = _build_ui_snapshot(
        104,
        "2026-06-07T12:40:00",
        {
            "url": "https://example.org/program/application",
            "timestamp": "2026-06-07T12:40:00",
            "integrated_results": {
                "seo_score": 73,
                "aio_score": 71,
                "legal_score": 90,
                "integrated_score": 75,
                "business_goal": "自動判定",
            },
            "final_industry": {"primary": "公共・団体"},
            "url_type": {"effective": "団体"},
            "platform": {"effective": "カスタム/その他"},
            "summary": {"improvements": ["申込条件と資料請求の流れをCTA付近へ追加する"], "issue_count": 1},
            "warnings": ["申込条件が分かりにくい", "資料請求の導線が弱い"],
            "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
            "seo_results": {
                "technical": {},
                "structure": {"headings": {"h1": ["支援プログラム"], "h2": ["対象者", "申込方法", "資料請求", "相談窓口"]}},
                "basics": {
                    "title": "支援プログラム 申込・資料請求",
                    "meta_description": "対象者、申込方法、資料請求、相談窓口をご案内します。",
                },
                "immediate_actions": [],
                "web_vitals": {},
            },
            "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
            "citation_insights": {"phrases": []},
            "legal_summary": {"top_issues": []},
            "legal_checks": {},
            "is_ec": False,
        },
        None,
    )

    role_map = snapshot["summary_workspace"]["intent_role_map"]
    combined_text = " ".join(
        [
            role_map["page_role"],
            role_map["user_intent"],
            role_map["recommended_action"],
            role_map["non_engineer_summary"],
        ]
    )
    assert role_map["page_role"] == "料金/予約/相談・資料請求ページ"
    assert "資料請求" in combined_text
    assert "申込" in combined_text
    assert "費用・条件・必要情報" not in role_map["missing_content"]
    assert "変更・注意事項・対象外条件" in role_map["missing_content"]
    assert "変更・キャンセル条件" not in role_map["missing_content"]
    assert "料金・費用条件" not in role_map["missing_content"]
    assert "購入へ進む" not in combined_text
    assert "予約へ進む" not in combined_text


def test_execute_primary_analysis_retries_once_on_transient_error(monkeypatch) -> None:
    analyzer = _PrimaryAnalyzerStub(failures=1)
    slept = []
    monkeypatch.setattr("core.application.analysis_run_service.time.sleep", lambda seconds: slept.append(seconds))

    result = execute_primary_analysis(
        analyzer,
        "https://example.com",
        "一般",
        50,
        True,
        "自動判定",
        "企業",
        "自動判定",
        lambda stage, percent, detail=None: None,
    )

    assert result["url"] == "https://example.com"
    assert analyzer.calls == 2
    assert slept == [TRANSIENT_RETRY_DELAY_SECONDS]


def test_execute_primary_analysis_does_not_retry_non_retryable_errors(monkeypatch) -> None:
    analyzer = _PrimaryAnalyzerStub(failures=1, exc_factory=lambda: UnsafeURLError("https://example.com", "dns_resolution_failed"))
    slept = []
    monkeypatch.setattr("core.application.analysis_run_service.time.sleep", lambda seconds: slept.append(seconds))

    try:
        execute_primary_analysis(
            analyzer,
            "https://example.com",
            "一般",
            50,
            True,
            "自動判定",
            "企業",
            "自動判定",
            lambda stage, percent, detail=None: None,
        )
    except UnsafeURLError:
        pass
    else:
        raise AssertionError("UnsafeURLError should be re-raised")

    assert analyzer.calls == 1
    assert slept == []


def test_execute_competitor_analysis_retries_once_on_transient_error(monkeypatch) -> None:
    attempts = {"count": 0}
    slept = []
    monkeypatch.setattr("core.application.analysis_run_service.time.sleep", lambda seconds: slept.append(seconds))

    class _RetryingCompetitorAnalyzer:
        def analyze_url(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("temporary")
            return {"url": "https://competitor.example.com"}

        def generate_competitor_action_advice(self, current_results, competitor_results, max_actions=5):  # type: ignore[no-untyped-def]
            return {"actions": [{"title": "差分を埋める"}], "max_actions": max_actions}

    outcome = execute_competitor_analysis(
        "https://competitor.example.com",
        "一般",
        50,
        True,
        "自動判定",
        {"url": "https://example.com"},
        analyzer_factory=lambda **kwargs: _RetryingCompetitorAnalyzer(),
    )

    assert outcome.results == {"url": "https://competitor.example.com"}
    assert attempts["count"] == 2
    assert slept == [TRANSIENT_RETRY_DELAY_SECONDS]


def test_persist_analysis_run_saves_scores_and_priority_pages(monkeypatch) -> None:
    saved = {}

    monkeypatch.setattr(
        "core.application.analysis_run_service.aggregate_legal_check_results",
        lambda checks: {
            "aggregated_issues": [
                {
                    "category": "legal",
                    "severity": "high",
                    "representative": {"title": "特商法不足", "detail": "住所未掲載"},
                }
            ]
        },
    )
    monkeypatch.setattr("core.application.analysis_run_service.init_database", lambda: saved.setdefault("init", True))

    def _fake_save_analysis_run(url, scores, issues, is_ec=True):  # type: ignore[no-untyped-def]
        saved["run"] = {"url": url, "scores": scores, "issues": issues, "is_ec": is_ec}
        return 42

    monkeypatch.setattr(
        "core.application.analysis_run_service.save_analysis_run",
        _fake_save_analysis_run,
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.save_crawl_pages",
        lambda run_id, pages: saved.setdefault("pages", {"run_id": run_id, "pages": pages}),
    )

    results = {
        "legal_checks": {"commercial_transaction": []},
        "integrated_results": {"seo_score": 81, "aio_score": 72, "legal_score": 65},
        "is_ec": False,
        "crawl_strategy": {"priority_pages": ["https://example.com/privacy"], "depth": 1},
    }

    run_id = persist_analysis_run(
        "https://example.com",
        results,
        competitor_results={
            "url": "https://competitor.example.com",
            "integrated_results": {"seo_score": 76, "aio_score": 69, "integrated_score": 73},
        },
        competitor_action_advice={"actions": [{"title": "差分を埋める"}]},
    )

    assert run_id == 42
    assert saved["run"]["url"] == "https://example.com"
    assert saved["run"]["scores"] == {"seo": 81, "aio": 72, "legal": 65}
    assert saved["run"]["issues"][0]["title"] == "特商法不足"
    assert saved["pages"]["pages"][0]["url"] == "https://example.com/privacy"


def test_build_token_usage_text_formats_full_and_partial_labels() -> None:
    token_summary = SimpleNamespace(
        total_requests=3,
        total_input_tokens=1234,
        total_output_tokens=567,
        total_cost_jpy=12.5,
        total_cost_usd=0.08,
    )

    full_text = build_token_usage_text(token_summary)
    partial_text = build_token_usage_text(token_summary, partial=True)

    assert full_text is not None and "API呼び出し" in full_text
    assert partial_text is not None and "途中まで" in partial_text


def test_build_faq_suggestions_personalizes_non_ec_candidates() -> None:
    suggestions = _build_faq_suggestions(
        {
            "final_industry": {"primary": "IT・SaaS"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "industry_analysis": {"target_audience_clues": ["法人向け"]},
            "warnings": [
                "著者・運営者の信頼情報が弱い",
                "料金プランの説明が不足しています",
                "他社との違いが分かりにくい",
            ],
            "citation_insights": {"phrases": [{"phrase": "比較ポイント", "reason": "選び方の判断材料が不足"}]},
            "is_ec": False,
        }
    )

    questions = {item["question"] for item in suggestions}
    assert "運営会社・担当者情報はどこで確認できますか？" in questions
    assert "初期費用・月額・追加料金の考え方は？" in questions
    assert "他社サービスと比較するときの確認ポイントは？" in questions
    assert all(item.get("source_label") for item in suggestions)
    assert all(item.get("reason") for item in suggestions)
    assert all(item.get("persona_label") == "法人担当者向け" for item in suggestions)
    assert all(item.get("answer_outline") for item in suggestions)
    assert all(item.get("recommended_section") for item in suggestions)
    assert all(item.get("schema_candidate") for item in suggestions)
    assert all(item.get("confidence") in {"low", "medium", "high"} for item in suggestions)
    assert any(item.get("evidence_terms") for item in suggestions)
    assert any(item.get("question") != item.get("base_question") for item in suggestions)


def test_build_faq_suggestions_personalizes_ec_candidates() -> None:
    suggestions = _build_faq_suggestions(
        {
            "final_industry": {"primary": "EC"},
            "url_type": {"effective": "企業（EC機能あり）"},
            "platform": {"effective": "Shopify"},
            "warnings": ["送料と配送日数の説明が不足しています", "問い合わせ先が分かりにくい"],
            "is_ec": True,
        }
    )

    questions = {item["question"] for item in suggestions}
    assert "送料・配送日数・到着目安は？" in questions
    assert "問い合わせ窓口と回答目安は？" in questions
    assert all(item.get("source_label") == "EC / issue ベース" for item in suggestions)
    assert all(item.get("persona_label") == "購入前ユーザー向け" for item in suggestions)
    assert all(item.get("answer_outline") for item in suggestions)


def test_build_faq_suggestion_payload_personalizes_real_estate_without_corporate_drift() -> None:
    payload = _build_faq_suggestion_payload(
        {
            "url": "https://toki-shouji.example/sell/akiya",
            "final_industry": {"primary": "不動産"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "seo_results": {
                "basics": {
                    "title": "不動産売却・空き家相談",
                    "meta_description": "査定、買取、相続不動産の相談に対応します。",
                },
                "structure": {"headings": {"h1": ["不動産売却"], "h2": ["査定の流れ", "売却費用", "空き家相談"]}},
            },
            "warnings": ["料金説明が不足しています", "査定から売却までの流れが分かりにくい"],
            "is_ec": False,
        }
    )

    questions = {item["question"] for item in payload["suggestions"]}
    assert "査定や売却相談に費用はかかりますか？" in questions
    assert "査定から売却完了まではどんな流れですか？" in questions
    assert payload["debug"]["persona"]["label"] != "法人担当者向け"
    assert payload["debug"]["context"]["page_service_terms"]
    assert payload["debug"]["context"]["transaction_terms"]
    assert all(item.get("recommended_section") for item in payload["suggestions"])
    assert all("導入や申込" not in item["question"] for item in payload["suggestions"])


def test_build_faq_suggestion_payload_generalizes_b2c_verticals_without_corporate_drift() -> None:
    cases = [
        {
            "industry": "飲食・フード",
            "title": "梅田の焼肉店 メニュー・予約",
            "meta": "コース料金、個室、子連れ、アレルギー対応をご案内します。",
            "headings": ["メニュー", "予約から来店まで", "個室と駐車場"],
            "expected": {"メニューや予算の目安はどこで確認できますか？", "予約から来店までの流れは？"},
        },
        {
            "industry": "介護・福祉",
            "title": "デイサービス見学・利用相談",
            "meta": "利用料金、送迎範囲、医療連携、見学から利用開始までをご案内します。",
            "headings": ["見学の流れ", "自己負担額", "対応エリア"],
            "expected": {"利用料金や自己負担額はどのように確認できますか？", "見学・相談から利用開始までの流れは？"},
        },
        {
            "industry": "アパレル",
            "title": "レディースアパレル サイズ・素材ガイド",
            "meta": "価格帯、サイズ選び、試着、返品交換、素材の確認方法を紹介します。",
            "headings": ["サイズ選び", "返品交換", "素材とお手入れ"],
            "expected": {"価格帯や送料・返品条件はどこで確認できますか？", "サイズ選びや試着・交換の流れは？"},
        },
    ]

    for case in cases:
        payload = _build_faq_suggestion_payload(
            {
                "url": "https://example.com/b2c/service",
                "final_industry": {"primary": case["industry"]},
                "url_type": {"effective": "企業"},
                "platform": {"effective": "WordPress"},
                "seo_results": {
                    "basics": {"title": case["title"], "meta_description": case["meta"]},
                    "structure": {"headings": {"h1": [case["title"]], "h2": case["headings"]}},
                },
                "warnings": ["料金説明が不足しています", "予約や申込の流れが分かりにくい"],
                "is_ec": False,
            }
        )
        questions = {item["question"] for item in payload["suggestions"]}
        assert case["expected"] <= questions
        assert payload["debug"]["persona"]["label"] != "法人担当者向け"
        assert all("導入や申込" not in item["question"] for item in payload["suggestions"])
        assert all(item.get("evidence_terms") for item in payload["suggestions"])


def test_build_faq_suggestion_payload_handles_unknown_b2c_industry_by_customer_intent() -> None:
    payload = _build_faq_suggestion_payload(
        {
            "url": "https://example.com/service/reservation",
            "final_industry": {"primary": "生活サービス"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "seo_results": {
                "basics": {
                    "title": "写真スタジオ 予約・料金案内",
                    "meta_description": "初めての撮影でも分かるよう、料金、予約、当日の流れ、衣装相談をご案内します。",
                },
                "structure": {"headings": {"h1": ["写真スタジオ"], "h2": ["料金", "予約方法", "当日の流れ", "相談"]}},
            },
            "warnings": ["料金説明が不足しています", "予約から利用までの流れが分かりにくい"],
            "is_ec": False,
        }
    )

    questions = {item["question"] for item in payload["suggestions"]}
    assert "料金・費用・追加料金はどこで確認できますか？" in questions
    assert "予約・相談・申込から利用開始までの流れは？" in questions
    assert payload["debug"]["persona"]["label"] != "法人担当者向け"
    assert any("generic_b2c" in str(signal) for row in payload["debug"]["persona"]["candidates"] for signal in row.get("signals", []))
    assert all("導入や申込" not in item["question"] for item in payload["suggestions"])


def test_build_faq_suggestion_payload_uses_url_and_page_signals_for_persona() -> None:
    payload = _build_faq_suggestion_payload(
        {
            "url": "https://example.com/b2b/enterprise/pricing",
            "final_industry": {"primary": "一般"},
            "url_type": {"effective": "サービス"},
            "platform": {"effective": "WordPress"},
            "seo_results": {
                "basics": {
                    "title": "法人向け導入プランと料金",
                    "meta_description": "稟議前に確認したい導入条件と見積の考え方を紹介します。",
                },
                "structure": {"headings": {"h1": ["法人導入の進め方"], "h2": ["見積と導入フロー"]}},
            },
            "warnings": ["料金プランの説明が不足しています", "導入手順が分かりにくい"],
            "summary": {"improvements": ["導入条件を先に整理する"]},
            "is_ec": False,
        }
    )

    persona = payload["debug"]["persona"]
    assert persona["label"] == "法人担当者向け"
    assert persona["confidence"] in {"medium", "high"}
    assert any(str(signal).startswith("title:法人") or str(signal).startswith("url:b2b") for signal in persona["candidates"][0]["signals"])
    assert payload["debug"]["context"]["url_signal_tokens"][:3] == ["example", "b2b", "enterprise"]


def test_build_faq_suggestion_payload_accepts_industry_analysis_object() -> None:
    payload = _build_faq_suggestion_payload(
        {
            "url": "https://example.com/service",
            "final_industry": {"primary": "IT・SaaS"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "WordPress"},
            "industry_analysis": IndustryAnalysis(
                primary_industry="IT・SaaS",
                secondary_industries=[],
                confidence_score=90.0,
                industry_keywords=["SaaS"],
                specialized_terms=["導入"],
                regulatory_indicators=["個人情報"],
                target_audience_clues=["法人向け"],
            ),
            "warnings": ["導入手順が分かりにくい"],
            "is_ec": False,
        }
    )

    assert payload["debug"]["persona"]["label"] == "法人担当者向け"
    assert payload["debug"]["context"]["audience_clues"] == ["法人向け"]
    assert payload["debug"]["context"]["regulatory_indicators"] == ["個人情報"]


def test_build_faq_suggestion_payload_prefers_lmo_persona_for_food_site() -> None:
    payload = _build_faq_suggestion_payload(
        {
            "url": "https://example.co.jp/restaurant/umeda",
            "final_industry": {"primary": "飲食・フード"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "カスタム/その他"},
            "seo_results": {
                "basics": {
                    "title": "梅田の焼肉店 | メニュー・営業時間・アクセス",
                    "meta_description": "予約方法、営業時間、最寄り駅、駐車場をご案内します。",
                },
                "structure": {"headings": {"h1": ["ご予約"], "h2": ["アクセス", "営業時間", "メニュー"]}},
            },
            "warnings": ["営業時間の案内が不足しています", "アクセス方法が分かりにくい"],
            "is_ec": False,
        }
    )

    persona = payload["debug"]["persona"]
    topics = {item["topic"] for item in payload["suggestions"]}
    assert persona["label"] == "来訪前ユーザー向け"
    assert {"access", "hours", "reservation"} & topics
    assert "法人担当者向け" != persona["label"]


def test_build_faq_suggestion_payload_blocks_ec_faq_for_association_domain_without_checkout_signal() -> None:
    payload = _build_faq_suggestion_payload(
        {
            "url": "https://www.example.or.jp/guide/",
            "final_industry": {"primary": "教育・スクール"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "カスタム/その他"},
            "seo_results": {
                "basics": {
                    "title": "商工会議所の支援メニューと相談窓口",
                    "meta_description": "会員向け・一般向けの支援内容と申込方法をご案内します。",
                },
                "structure": {"headings": {"h1": ["相談窓口"], "h2": ["支援メニュー", "申込方法"]}},
            },
            "industry_analysis": {
                "target_audience_clues": ["法人向け", "個人向け"],
            },
            "warnings": ["問い合わせ先が分かりにくい"],
            "is_ec": True,
            "ec_detection_reason": "product_indicators（45件）",
        }
    )

    persona = payload["debug"]["persona"]
    topics = {item["topic"] for item in payload["suggestions"]}
    assert payload["debug"]["context"]["ec_guardrail"]["effective_is_ec"] is False
    assert persona["label"] == "案内確認ユーザー向け"
    assert not {"returns", "payment", "cancel", "delivery"} & topics
    assert {"public_services", "public_eligibility", "public_application"} & topics


def test_build_faq_suggestion_payload_blocks_ec_faq_for_association_domain_with_soft_commerce_signals() -> None:
    payload = _build_faq_suggestion_payload(
        {
            "url": "https://www.example.or.jp/event/",
            "final_industry": {"primary": "教育・スクール"},
            "url_type": {"effective": "企業"},
            "platform": {"effective": "カスタム/その他"},
            "seo_results": {
                "basics": {
                    "title": "商工会議所の講座案内",
                    "meta_description": "講座日程と申込窓口をご案内します。",
                },
                "structure": {"headings": {"h1": ["講座一覧"], "h2": ["申込方法", "窓口案内"]}},
            },
            "industry_analysis": {
                "target_audience_clues": ["法人向け", "個人向け"],
            },
            "warnings": ["問い合わせ先が分かりにくい"],
            "is_ec": True,
            "ec_detection_reason": "price_display（9件） / product_indicators（45件） / checkout（1件）",
        }
    )

    topics = {item["topic"] for item in payload["suggestions"]}
    guardrail = payload["debug"]["context"]["ec_guardrail"]
    assert guardrail["effective_is_ec"] is False
    assert guardrail["forced_non_ec_reasons"] == ["domain:association_like"]
    assert not {"returns", "payment", "cancel", "delivery"} & topics
    assert {"public_services", "public_eligibility", "public_application"} & topics


def test_persist_analysis_run_updates_snapshot_artifacts(monkeypatch, tmp_path) -> None:
    captured = {}

    monkeypatch.setattr(
        "core.application.analysis_run_service.aggregate_legal_check_results",
        lambda checks: {"aggregated_issues": []},
    )
    monkeypatch.setattr("core.application.analysis_run_service.init_database", lambda: None)
    monkeypatch.setattr("core.application.analysis_run_service.RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(
        "core.application.analysis_run_service.save_analysis_run",
        lambda url, scores, issues, is_ec=True: 7,
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.update_run_artifacts",
        lambda run_id, **kwargs: captured.update({"run_id": run_id, **kwargs}),
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.save_crawl_pages",
        lambda run_id, pages: None,
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_previous_run",
        lambda url, current_run_id=None: {
            "id": 3,
            "seo_score": 70,
            "aio_score": 60,
            "legal_score": 80,
            "analyzed_at": "2026-04-01 12:00:00",
        },
    )

    results = {
        "url": "https://example.com",
        "timestamp": "2026-04-02T21:00:00",
        "legal_checks": {},
        "integrated_results": {"seo_score": 81, "aio_score": 72, "legal_score": 65, "business_goal": "自動判定"},
        "final_industry": {"primary": "IT・SaaS"},
        "url_type": {"effective": "企業"},
        "platform": {"effective": "WordPress"},
        "summary": {"improvements": ["冒頭を短くする"], "issue_count": 4},
        "warnings": ["冒頭要約が弱い"],
        "site_health": {
            "accessibility": {
                "formatted": {"score": 76},
                "raw": {
                    "score": 76,
                    "issue_groups": [
                        {
                            "id": "image_alt",
                            "label": "img alt",
                            "weight": 14,
                            "affected_count": 2,
                            "issues": [{"element": '<img src="product.jpg">', "issue": "altなし"}],
                        },
                        {
                            "id": "interactive_names",
                            "label": "a/button accessible name候補",
                            "weight": 12,
                            "affected_count": 1,
                            "issues": [{"element": "<button>", "issue": "操作名なし"}],
                        },
                    ],
                },
            }
        },
        "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
        "seo_results": {
            "immediate_actions": [],
            "basics": {},
            "technical": {
                "international_targeting": {"summary": "html lang=ja / hreflang 2件", "status": "warn"},
                "x_robots_tag": {"summary": "X-Robots-Tag なし", "status": "pass"},
                "mobile_parity": {"summary": "viewport=yes", "status": "pass"},
                "page_experience": {"summary": "LCP=2200ms / CLS=0.040", "status": "pass"},
                "media_discovery": {"summary": "images=3 discoverable=3", "status": "warn"},
            },
            "structure": {"link_quality": {"summary": "crawlable=8/10 / empty=1", "status": "warn"}},
            "web_vitals": {"lcp_ms": 2200, "cls_score": 0.04},
        },
        "aio_results": {
            "immediate_actions": [],
            "provider_readiness": {
                "google": {"status": "warn"},
                "special_notes": {
                    "openai_commerce": {"summary": "商品データの整形を強める余地があります。"},
                    "perplexity_operational": {"summary": "WAF allowlist はHTMLから確認できません。"},
                },
            },
        },
        "citation_insights": {"phrases": []},
        "legal_summary": {"top_issues": []},
        "is_ec": False,
    }

    run_id = persist_analysis_run(
        "https://example.com",
        results,
        competitor_results={
            "url": "https://competitor.example.com",
            "integrated_results": {"seo_score": 76, "aio_score": 69, "integrated_score": 73},
        },
        competitor_action_advice={"actions": [{"title": "差分を埋める"}]},
    )

    assert run_id == 7
    assert captured["run_id"] == 7
    snapshot = json.loads(captured["snapshot_json"])
    assert snapshot["meta"]["url"] == "https://example.com"
    assert snapshot["meta"]["industry"] == "IT・SaaS"
    assert snapshot["header"]["priority_level"] == "中"
    assert snapshot["header"]["previous_diff"]["label"] == "+11"
    assert [item["label"] for item in snapshot["summary_workspace"]["headline_metrics"]] == ["AI認識", "SEO", "総合優先度"]
    assert snapshot["summary_workspace"]["accessibility_score_snapshot"] == 76
    assert snapshot["summary_workspace"]["priority_counts"][0]["label"] == "AI公開条件"
    assert snapshot["summary_workspace"]["priority_counts"][1]["label"] == "表示アドバイス"
    assert any(item["area"] == "検索意図" for item in snapshot["task_workspace"]["actions"])
    assert snapshot["summary_workspace"]["intent_role_map"]["page_role"]
    summary_lines = snapshot["summary_workspace"]["summary_lines"]
    assert summary_lines[0].startswith("ページ役割:")
    assert any(line.startswith("最初の一手:") for line in summary_lines)
    assert "前回比: +11" in summary_lines
    assert snapshot["writing_workspace"]["faq_detection_summary"]["count"] == 0
    assert snapshot["writing_workspace"]["faq_suggestions"][0]["source_label"]
    assert snapshot["writing_workspace"]["faq_suggestions"][0]["presentation_mode"] == "contextualized"
    assert snapshot["writing_workspace"]["faq_suggestions"][0]["persona_label"]
    assert snapshot["writing_workspace"]["faq_suggestions"][0]["answer_outline"]
    assert snapshot["writing_workspace"]["faq_suggestions"][0]["recommended_section"]
    assert snapshot["writing_workspace"]["faq_suggestions"][0]["schema_candidate"]
    assert snapshot["writing_workspace"]["faq_suggestions"][0]["confidence"] in {"low", "medium", "high"}
    assert snapshot["writing_workspace"]["faq_debug"]["strategy"] == "template_plus_context_rewrite"
    assert snapshot["writing_workspace"]["faq_debug"]["persona"]["confidence"] in {"low", "medium", "high"}
    assert snapshot["writing_workspace"]["faq_debug"]["persona"]["candidates"]
    assert snapshot["implementation_workspace"]["provider_payload"]["google"]["status"] == "warn"
    accessibility_actions = snapshot["implementation_workspace"]["accessibility_improvements"]["actions"]
    assert accessibility_actions[0]["title"] == "画像に内容が分かる説明文を入れる"
    assert accessibility_actions[0]["target_element"] == '<img src="product.jpg">'
    assert accessibility_actions[0]["audience"]["handoff_to"]
    assert "<img" not in accessibility_actions[0]["audience"]["action"]
    assert accessibility_actions[0]["engineer"]["target_element"] == '<img src="product.jpg">'
    assert accessibility_actions[0]["engineer"]["detection_source"] == "HTML自動検出"
    assert accessibility_actions[0]["reason"]
    assert accessibility_actions[0]["verification"]
    technical_accessibility_actions = snapshot["technical_workspace"]["accessibility_improvements"]["actions"]
    assert technical_accessibility_actions[0]["engineer"]["verification"]
    assert snapshot["implementation_workspace"]["seo_audit_notes"][0]["status"] == "warn"
    assert snapshot["implementation_workspace"]["seo_audit_notes"][0]["source_label"] == "実データ"
    assert {
        item["title"] for item in snapshot["implementation_workspace"]["seo_audit_notes"]
    } >= {"国際化 / インデックス制御", "リンク品質", "画像 / 動画の発見性"}
    assert snapshot["comparison_workspace"]["competitor_summary"]["status"] == "available"
    assert snapshot["comparison_workspace"]["competitor_summary"]["actions"][0]["title"] == "差分を埋める"
    assert captured["result_path"].endswith("analysis_result.json")

    canonical_ids = [
        item["action_id"]
        for item in snapshot["exports"]["priority_actions"]
    ]
    assert canonical_ids == [
        item["action_id"]
        for item in snapshot["task_workspace"]["actions"]
    ]
    assert canonical_ids[:3] == [
        item["action_id"]
        for item in snapshot["summary_workspace"]["top_actions"]
    ]
    assert [
        item["priority_rank"]
        for item in snapshot["exports"]["priority_actions"]
    ] == list(range(1, len(canonical_ids) + 1))
    assert all(item["audience"] and item["evidence"] for item in snapshot["exports"]["priority_actions"])
    assert all(item["status"] == "unverified" for item in snapshot["exports"]["priority_actions"])
    assert all(
        {"action_id", "priority_rank", "audience", "evidence", "status"}.issubset(item)
        for item in snapshot["task_workspace"]["actions"]
    )


def test_load_saved_run_bundle_reads_snapshot_and_result(monkeypatch, tmp_path) -> None:
    runs_dir = tmp_path / "runs"
    result_path = runs_dir / "9" / "analysis_result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(json.dumps({"url": "https://example.com", "integrated_results": {"seo_score": 80}}), encoding="utf-8")
    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "meta": {"url": "https://example.com"},
        "header": {"priority_level": "低"},
        "summary_workspace": {
            "headline_metrics": [],
            "priority_counts": [],
            "accessibility_score_snapshot": 0,
            "summary_personalization_version": 1,
        },
        "implementation_workspace": {
            "seo_audit_notes": [],
            "intent_role_map": {},
            "llms_summary": {},
            "schema_summary": {},
            "link_health_summary": {},
            "crawl_scope_summary": {},
            "site_health_checks": [],
        },
        "technical_workspace": {
            "summary_cards": [],
            "crawl_scope": {},
            "intent_role_map": {},
            "link_health": {},
            "schema": {},
            "llms": {},
            "site_health_checks": [],
        },
    }

    monkeypatch.setattr("core.application.analysis_run_service.RUNS_DIR", runs_dir)
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_run_detail",
        lambda run_id: {
            "id": 9,
            "url": "https://example.com",
            "analyzed_at": "2026-04-02 20:00:00",
            "result_path": str(result_path),
            "snapshot_json": json.dumps(snapshot, ensure_ascii=False),
            "issues": [],
            "crawl_pages": [],
        },
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_history",
        lambda url=None, limit=10, **kwargs: [{"id": 9, "url": "https://example.com"}],
    )

    bundle = load_saved_run_bundle(9)

    assert bundle is not None
    assert bundle["snapshot"]["header"]["priority_level"] == "低"
    assert bundle["result"]["integrated_results"]["seo_score"] == 80
    assert bundle["same_url_history"][0]["id"] == 9


def test_load_saved_run_bundle_refreshes_saved_stealth_formatter(monkeypatch, tmp_path) -> None:
    runs_dir = tmp_path / "runs"
    result_path = runs_dir / "10" / "analysis_result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "url": "https://example.com",
                "integrated_results": {"seo_score": 80},
                "legal_checks": {
                    "stealth_marketing": {
                        "raw": {
                            "compliance_status": "ok",
                            "affiliate_detection": {
                                "is_affiliate": False,
                                "confidence": 0.2,
                                "indicators": [],
                                "affiliate_links_count": 0,
                                "content_pattern_count": 2,
                            },
                            "disclosure_check": {"has_disclosure": False},
                            "issues": [],
                            "recommendations": [],
                        },
                        "formatted": {
                            "items": [
                                {
                                    "icon": "✓",
                                    "text": "アフィリエイトコンテンツ: 検出されず",
                                    "subtext": "",
                                }
                            ]
                        },
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    snapshot = {
        "schema_version": 13,
        "header": {"priority_level": "低"},
        "summary_workspace": {
            "headline_metrics": [],
            "priority_counts": [],
            "accessibility_score_snapshot": 0,
            "summary_personalization_version": 1,
        },
        "implementation_workspace": {
            "seo_audit_notes": [],
            "intent_role_map": {},
            "llms_summary": {},
            "schema_summary": {},
            "link_health_summary": {},
            "crawl_scope_summary": {},
            "site_health_checks": [],
        },
        "technical_workspace": {
            "summary_cards": [],
            "crawl_scope": {},
            "intent_role_map": {},
            "link_health": {},
            "schema": {},
            "llms": {},
            "site_health_checks": [],
        },
    }

    monkeypatch.setattr("core.application.analysis_run_service.RUNS_DIR", runs_dir)
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_run_detail",
        lambda run_id: {
            "id": 10,
            "url": "https://example.com",
            "analyzed_at": "2026-04-02 20:00:00",
            "result_path": str(result_path),
            "snapshot_json": json.dumps(snapshot, ensure_ascii=False),
            "issues": [],
            "crawl_pages": [],
        },
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_history",
        lambda url=None, limit=10, **kwargs: [],
    )

    bundle = load_saved_run_bundle(10)

    assert bundle is not None
    formatted = bundle["result"]["legal_checks"]["stealth_marketing"]["formatted"]
    assert formatted["items"][0]["text"] == "PR表記が必要なアフィリエイト要素: 未検出"
    assert "スコア低下/要対応になるのは" in formatted["items"][0]["subtext"]


def test_load_saved_run_bundle_rejects_result_path_outside_runs_dir(monkeypatch, tmp_path) -> None:
    unsafe_result_path = tmp_path / "outside" / "analysis_result.json"
    unsafe_result_path.parent.mkdir(parents=True)
    unsafe_result_path.write_text(
        json.dumps({"integrated_results": {"seo_score": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )
    snapshot = {
        "schema_version": 13,
        "header": {"integrated_score": 77, "priority_level": "低"},
        "summary_workspace": {
            "headline_metrics": [],
            "priority_counts": [],
            "accessibility_score_snapshot": 0,
            "summary_personalization_version": 1,
        },
        "implementation_workspace": {
            "seo_audit_notes": [],
            "intent_role_map": {},
            "llms_summary": {},
            "schema_summary": {},
            "link_health_summary": {},
            "crawl_scope_summary": {},
            "site_health_checks": [],
        },
        "technical_workspace": {
            "summary_cards": [],
            "crawl_scope": {},
            "intent_role_map": {},
            "link_health": {},
            "schema": {},
            "llms": {},
            "site_health_checks": [],
        },
    }

    monkeypatch.setattr("core.application.analysis_run_service.RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_run_detail",
        lambda run_id: {
            "id": 19,
            "url": "https://example.com",
            "analyzed_at": "2026-06-07 14:00:00",
            "result_path": str(unsafe_result_path),
            "snapshot_json": json.dumps(snapshot, ensure_ascii=False),
            "issues": [],
            "crawl_pages": [],
        },
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_history",
        lambda url=None, limit=10, **kwargs: [{"id": 19, "url": "https://example.com"}],
    )

    bundle = load_saved_run_bundle(19)

    assert bundle is not None
    assert bundle["snapshot"]["header"]["integrated_score"] == 77
    assert bundle["result"] == {}


def test_load_saved_run_bundle_refreshes_legacy_snapshot(monkeypatch, tmp_path) -> None:
    runs_dir = tmp_path / "runs"
    result_path = runs_dir / "11" / "analysis_result.json"
    result_path.parent.mkdir(parents=True)
    result_payload = {
        "url": "https://example.com",
        "timestamp": "2026-04-06T10:00:00",
        "integrated_results": {"seo_score": 80, "aio_score": 70, "legal_score": 90, "business_goal": "自動判定"},
        "final_industry": {"primary": "IT・SaaS"},
        "url_type": {"effective": "企業"},
        "platform": {"effective": "WordPress"},
        "summary": {"improvements": [], "issue_count": 1},
        "warnings": [],
        "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
        "seo_results": {"technical": {}, "structure": {}, "basics": {}, "immediate_actions": [], "web_vitals": {}},
        "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
        "citation_insights": {"phrases": []},
        "legal_summary": {"top_issues": []},
        "legal_checks": {},
        "is_ec": False,
    }
    result_path.write_text(json.dumps(result_payload, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr("core.application.analysis_run_service.RUNS_DIR", runs_dir)
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_run_detail",
        lambda run_id: {
            "id": 11,
            "url": "https://example.com",
            "analyzed_at": "2026-04-06 10:00:00",
            "result_path": str(result_path),
            "snapshot_json": json.dumps(
                {
                    "schema_version": 13,
                    "header": {"priority_level": "旧"},
                    "comparison_workspace": {
                        "competitor_summary": {
                            "status": "available",
                            "target_url": "https://competitor.example.com",
                            "actions": [{"title": "差分を埋める"}],
                        }
                    },
                },
                ensure_ascii=False,
            ),
            "issues": [],
            "crawl_pages": [],
        },
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_history",
        lambda url=None, limit=10, **kwargs: [{"id": 11, "url": "https://example.com"}],
    )
    monkeypatch.setattr("core.application.analysis_run_service.get_previous_run", lambda url, current_run_id=None: None)
    monkeypatch.setattr(
        "core.application.analysis_run_service.update_run_artifacts",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("saved GET must not write")),
    )

    bundle = load_saved_run_bundle(11)

    assert bundle is not None
    assert "seo_audit_notes" in bundle["snapshot"]["implementation_workspace"]
    assert bundle["snapshot"]["implementation_workspace"]["seo_audit_notes"][0]["source"] == "measured"
    assert bundle["snapshot"]["implementation_workspace"]["seo_audit_notes"][0]["status_label"] == "未確認"
    assert bundle["snapshot"]["comparison_workspace"]["competitor_summary"]["target_url"] == "https://competitor.example.com"
    assert bundle["snapshot"]["meta"]["persisted_snapshot_unchanged"] is True


def test_snapshot_needs_refresh_when_accessibility_score_snapshot_is_missing() -> None:
    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "summary_workspace": {"headline_metrics": [], "priority_counts": []},
        "implementation_workspace": {
            "seo_audit_notes": [],
            "intent_role_map": {},
            "llms_summary": {},
            "schema_summary": {},
            "link_health_summary": {},
            "crawl_scope_summary": {},
            "site_health_checks": [],
        },
        "technical_workspace": {
            "summary_cards": [],
            "crawl_scope": {},
            "intent_role_map": {},
            "link_health": {},
            "schema": {},
            "llms": {},
            "site_health_checks": [],
        },
    }

    assert _snapshot_needs_refresh(snapshot) is True
    snapshot["summary_workspace"]["accessibility_score_snapshot"] = 76
    assert _snapshot_needs_refresh(snapshot) is True
    snapshot["summary_workspace"]["summary_personalization_version"] = 1
    assert _snapshot_needs_refresh(snapshot) is False


def test_load_saved_run_bundle_refreshes_snapshot_when_old_legal_labels_remain(monkeypatch, tmp_path) -> None:
    runs_dir = tmp_path / "runs"
    result_path = runs_dir / "12" / "analysis_result.json"
    result_path.parent.mkdir(parents=True)
    result_payload = {
        "url": "https://example.com",
        "timestamp": "2026-04-06T10:00:00",
        "integrated_results": {"seo_score": 80, "aio_score": 70, "legal_score": 90, "business_goal": "自動判定"},
        "final_industry": {"primary": "IT・SaaS"},
        "url_type": {"effective": "企業"},
        "platform": {"effective": "WordPress"},
        "summary": {"improvements": [], "issue_count": 1},
        "warnings": [],
        "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
        "seo_results": {"technical": {}, "structure": {}, "basics": {}, "immediate_actions": [], "web_vitals": {}},
        "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
        "citation_insights": {"phrases": []},
        "legal_summary": {"top_issues": [{"title": "特商法", "summary": "補足が必要", "severity": "medium"}]},
        "legal_checks": {},
        "is_ec": False,
    }
    result_path.write_text(json.dumps(result_payload, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr("core.application.analysis_run_service.RUNS_DIR", runs_dir)
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_run_detail",
        lambda run_id: {
            "id": 12,
            "url": "https://example.com",
            "analyzed_at": "2026-04-06 10:00:00",
            "result_path": str(result_path),
            "snapshot_json": json.dumps(
                {
                    "summary_workspace": {
                        "headline_metrics": [{"label": "法務", "value": 90}],
                        "priority_counts": [{"label": "法務・表示", "count": 1}],
                    },
                    "implementation_workspace": {"seo_audit_notes": []},
                },
                ensure_ascii=False,
            ),
            "issues": [],
            "crawl_pages": [],
        },
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_history",
        lambda url=None, limit=10, **kwargs: [{"id": 12, "url": "https://example.com"}],
    )
    monkeypatch.setattr("core.application.analysis_run_service.get_previous_run", lambda url, current_run_id=None: None)

    bundle = load_saved_run_bundle(12)

    assert bundle is not None
    assert [item["label"] for item in bundle["snapshot"]["summary_workspace"]["headline_metrics"]] == ["AI認識", "SEO", "総合優先度"]
    assert bundle["snapshot"]["summary_workspace"]["priority_counts"][1]["label"] == "表示アドバイス"


def test_persist_analysis_run_snapshot_prefers_actual_integrated_score(monkeypatch, tmp_path) -> None:
    captured = {}
    runs_dir = tmp_path / "runs"
    previous_result_path = runs_dir / "5" / "analysis_result.json"
    previous_result_path.parent.mkdir(parents=True)
    previous_result_path.write_text(
        json.dumps({"integrated_results": {"integrated_score": 68}}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "core.application.analysis_run_service.aggregate_legal_check_results",
        lambda checks: {"aggregated_issues": []},
    )
    monkeypatch.setattr("core.application.analysis_run_service.init_database", lambda: None)
    monkeypatch.setattr("core.application.analysis_run_service.RUNS_DIR", runs_dir)
    monkeypatch.setattr(
        "core.application.analysis_run_service.save_analysis_run",
        lambda url, scores, issues, is_ec=True: 8,
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.update_run_artifacts",
        lambda run_id, **kwargs: captured.update({"run_id": run_id, **kwargs}),
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.save_crawl_pages",
        lambda run_id, pages: None,
    )
    monkeypatch.setattr(
        "core.application.analysis_run_service.get_previous_run",
        lambda url, current_run_id=None: {
            "id": 5,
            "seo_score": 70,
            "aio_score": 60,
            "legal_score": 80,
            "result_path": str(previous_result_path),
            "snapshot_json": json.dumps({"header": {"integrated_score": 70}}, ensure_ascii=False),
            "analyzed_at": "2026-04-01 12:00:00",
        },
    )

    results = {
        "url": "https://example.com",
        "timestamp": "2026-04-02T21:00:00",
        "legal_checks": {},
        "integrated_results": {
            "seo_score": 81,
            "aio_score": 72,
            "legal_score": 65,
            "integrated_score": 91,
            "business_goal": "自動判定",
        },
        "final_industry": {"primary": "IT・SaaS"},
        "url_type": {"effective": "企業"},
        "platform": {"effective": "WordPress"},
        "summary": {"improvements": [], "issue_count": 2},
        "warnings": [],
        "deep_recommendations": {"business": [], "technical": [], "title_rewrites": [], "description_rewrites": []},
        "seo_results": {"technical": {}, "structure": {}, "basics": {}, "immediate_actions": [], "web_vitals": {}},
        "aio_results": {"provider_readiness": {"google": {"status": "pass"}}, "immediate_actions": []},
        "citation_insights": {"phrases": []},
        "legal_summary": {"top_issues": []},
        "is_ec": False,
    }

    run_id = persist_analysis_run("https://example.com", results)

    assert run_id == 8
    snapshot = json.loads(captured["snapshot_json"])
    assert snapshot["header"]["integrated_score"] == 91
    assert snapshot["header"]["previous_diff"]["integrated_diff"] == 23
    assert snapshot["header"]["previous_diff"]["label"] == "+23"
