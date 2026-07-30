from __future__ import annotations

from types import SimpleNamespace

import core.ui.panels as panels_mod
import core.ui.panel_components as panel_components_mod
import core.ui.tabs.seo_tab as seo_tab_mod
from core.ui.panel_context import PanelContext


def test_saved_status_helpers_keep_unverified_distinct_from_reference() -> None:
    assert panel_components_mod._normalize_status_key("unknown") == "unverified"
    assert panel_components_mod._status_label("unverified") == "未確認"
    assert panel_components_mod._status_label("reference") == "参考"
    assert panel_components_mod._status_label("not_applicable") == "対象外"


class _FakeElement:
    def __init__(self, sink: list[tuple[str, str]]) -> None:
        self._sink = sink

    def classes(self, value: str):  # type: ignore[no-untyped-def]
        self._sink.append(("classes", value))
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeUI:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def column(self):  # type: ignore[no-untyped-def]
        self.events.append(("column", "open"))
        return _FakeElement(self.events)

    def label(self, text: str):  # type: ignore[no-untyped-def]
        self.events.append(("label", text))
        return _FakeElement(self.events)


def test_bind_panel_dependencies_sets_required_runtime_hooks() -> None:
    fake_state = SimpleNamespace(results={})

    panels_mod.bind_panel_dependencies(
        state=fake_state,
        trim_text=lambda text, limit=0: text,
        format_reason_text_ui=lambda text: text,
        calc_citation_index=lambda citation: 1.0,
        aio_score_labels={"pid_density": "命題密度"},
        aio_score_help={"pid_density": "help"},
    )

    assert panels_mod._require_state() is fake_state
    assert panels_mod._require_trim_text()("abc") == "abc"
    assert panels_mod._require_format_reason_text_ui()("abc") == "abc"
    assert panels_mod._require_calc_citation_index()({}) == 1.0
    assert panels_mod._require_panel_context().aio_score_labels == {"pid_density": "命題密度"}


def test_set_panel_context_updates_runtime_owner() -> None:
    fake_state = SimpleNamespace(results={"ok": True})
    context = PanelContext(
        state=fake_state,
        trim_text=lambda text, limit=0: text,
        format_reason_text_ui=lambda text: text,
        calc_citation_index=lambda citation: 0.5,
        aio_score_labels={"structure": "構造"},
        aio_score_help={"structure": "help"},
    )

    panels_mod.set_panel_context(context)

    assert panels_mod._require_panel_context() is context
    assert panels_mod._require_state() is fake_state


def test_render_output_gate_notice_block_path_renders_smoke(monkeypatch) -> None:
    fake_ui = _FakeUI()
    monkeypatch.setattr(panels_mod, "ui", fake_ui)

    rendered = panels_mod._render_output_gate_notice(
        {
            "output_gate": {
                "status": "block",
                "strict_check": {"decision": "block"},
                "consumer_check": {"decision": "warn"},
                "reason": "要確認",
                "reasons": ["表現が強い"],
            }
        }
    )

    assert rendered is True
    assert ("label", "通知") in fake_ui.events
    assert ("label", "一部の分析結果を非表示にしています") in fake_ui.events
    assert ("label", "詳細な分析結果はゲートにより非表示です。") in fake_ui.events


def test_build_decision_actions_prefers_deep_recommendations() -> None:
    actions = panels_mod._build_decision_actions(
        deep_recs={
            "business": [
                {
                    "title": "導線改善",
                    "recommended_action": "CTAを整理する",
                    "expected_impact": "High",
                }
            ],
            "technical": [
                {
                    "title": "構造化データ",
                    "implementation": "JSON-LDを追加する",
                    "expected_impact": "Medium",
                }
            ],
        },
        aio_results={"immediate_actions": []},
        seo_results={"immediate_actions": []},
        summary={"improvements": ["見出しを整理する"]},
        business_goal="自動判定",
    )

    assert len(actions) >= 2
    assert actions[0]["title"] == "導線改善"
    assert actions[1]["title"] == "構造化データ"


def test_build_provider_summary_rows_uses_status_labels() -> None:
    rows = panels_mod._build_provider_summary_rows(
        {
            "provider_readiness": {
                "google": {"status": "pass"},
                "openai_search": {"status": "warn"},
                "perplexity": {"status": "fail"},
                "claude_search": {},
            }
        }
    )

    assert [row["status"] for row in rows] == ["通過", "注意", "要対応", "未判定"]


def test_sort_decision_actions_by_goal_moves_ai_quote_actions_first() -> None:
    actions = [
        {"title": "会社情報の整理", "action": "会社概要を整える", "role": "運用", "kpi": "信頼"},
        {"title": "引用されやすい構成へ変更", "action": "冒頭要約と数値根拠を追加する", "role": "運用", "kpi": "AI引用"},
    ]

    ranked = panels_mod._sort_decision_actions_by_goal(
        actions,
        "AI検索での引用増加（GEO/AIO優先）",
    )

    assert ranked[0]["title"] == "引用されやすい構成へ変更"


def test_build_context_note_rows_compacts_premise_and_diagnostic_lines() -> None:
    premise_rows, diagnostic_rows = panels_mod._build_context_note_rows(
        results={
            "url_type": {"effective": "企業", "selected": "自動判定", "detected": "企業"},
            "final_industry": {"primary": "IT・SaaS", "source": "自動判定（信頼度: 88）", "confidence": 88},
            "is_ec": False,
            "ec_detection_reason": "購入導線なし",
            "crawl_strategy": {"reason": "主要ページのみ確認", "depth": 1, "link_count": 12},
            "internal_link_summary": {"orphan_count": 2, "total_pages": 18},
        },
        aio_results={
            "schema_validation": {"found_types": ["Organization"], "missing_recommended": ["FAQPage"], "score": 72},
            "content_schema_gap": {"aio_improvement_potential": 64, "gaps": ["FAQ", "要約"]},
        },
        integrated={"seo_score": 70, "aio_score": 55, "legal_score": 80},
        summary={"issue_count": 4},
        previous_run={"id": 9, "analyzed_at": "2026-03-01", "seo_score": 65, "aio_score": 50, "legal_score": 78, "total_issues": 6},
    )

    assert any("サイト種別: 企業" in row for row in premise_rows)
    assert any("業界見立て: IT・SaaS" in row for row in premise_rows)
    assert any("前回比較:" in row for row in diagnostic_rows)
    assert any("構造化データ:" in row for row in diagnostic_rows)


def test_extract_row_id_from_event_args_supports_dict_and_list_payloads() -> None:
    assert panels_mod._extract_row_id_from_event_args({"row": {"id": 84}}) == 84
    assert panels_mod._extract_row_id_from_event_args([{"row": {"id": 91}}]) == 91
    assert panels_mod._extract_row_id_from_event_args([{"x": 1}, {"id": 104}, 0]) == 104


def test_implementation_helpers_use_user_facing_labels() -> None:
    assert panels_mod._provider_check_status_label("pass") == "通過"
    assert panels_mod._provider_check_status_label("warn") == "注意"
    assert panels_mod._provider_check_status_label("fail") == "要対応"

    rows = panels_mod._describe_google_controls(
        {
            "noindex": False,
            "nosnippet": True,
            "max_snippet": 0,
            "data_nosnippet_count": 2,
        }
    )

    assert rows[0]["detail"] == "設定なし"
    assert rows[1]["detail"] == "設定あり"
    assert rows[2]["detail"] == "2箇所で抜粋除外"
    assert panels_mod._provider_has_actionable_details({"official_checks": [{"status": "pass"}], "heuristic_notes": []}) is False
    assert panels_mod._provider_has_actionable_details({"official_checks": [{"status": "warn"}], "heuristic_notes": []}) is True


def test_build_summary_priority_note_prefers_actionable_counts() -> None:
    note = panels_mod._build_summary_priority_note(
        {
            "priority_counts": [
                {"label": "AI公開条件", "count": 2},
                {"label": "表示アドバイス", "count": 1},
                {"label": "最優先アクション", "count": 3},
            ]
        }
    )

    assert note["title"] == "先に直す項目があります"
    assert "AI公開条件 2件" in note["detail"]
    assert note["status"] == "warn"


def test_split_task_actions_returns_primary_and_secondary_groups() -> None:
    actions = [{"title": f"task-{i}"} for i in range(5)]

    primary, secondary = panels_mod._split_task_actions(actions, primary_count=3)

    assert [item["title"] for item in primary] == ["task-0", "task-1", "task-2"]
    assert [item["title"] for item in secondary] == ["task-3", "task-4"]


def test_saved_run_intent_role_overview_uses_only_non_engineer_items() -> None:
    items = panels_mod._intent_role_overview_items(
        {
            "page_role": "料金/予約/相談・資料請求ページ",
            "recommended_action": "CTA直前に条件と流れを追加する",
            "missing_content": ["費用・条件・必要情報", "変更・注意事項・対象外条件"],
            "confidence": "high",
            "source_hits": {"title": ["料金"]},
            "intent_signals": [{"source": "heading", "term": "相談"}],
            "page_signals": {"schema_types": ["FAQPage"]},
            "engineer_notes": {"structured_data": "FAQPage JSON-LD"},
            "overview_items": [
                {
                    "label": "このページの役割",
                    "title": "相談前の判断ページ",
                    "detail": "料金や申込条件を確認するページです。",
                },
                {
                    "label": "不足",
                    "title": "判断材料が不足",
                    "detail": "費用・条件・必要情報",
                },
                {
                    "label": "次にやること",
                    "title": "条件を追加",
                    "detail": "CTA直前に流れと対象外条件を追加します。",
                },
                {
                    "label": "判定根拠",
                    "title": "高",
                    "detail": "debug",
                },
            ],
        }
    )

    assert [item["label"] for item in items] == ["このページの役割", "不足", "次にやること"]
    rendered_text = "\n".join(
        part
        for item in items
        for part in (item["label"], item["title"], item["detail"])
    )
    assert "confidence" not in rendered_text
    assert "source_hits" not in rendered_text
    assert "intent_signals" not in rendered_text
    assert "FAQPage" not in rendered_text
    assert "JSON-LD" not in rendered_text


def test_saved_run_secondary_actions_keep_search_intent_visible_after_limit() -> None:
    actions = [{"title": f"task-{i}", "area": "SEO"} for i in range(6)] + [
        {"title": "検索意図・ページ役割マップ", "area": "検索意図"}
    ]

    visible = panels_mod._prioritize_search_intent_secondary_actions(actions)[:5]

    assert len(visible) == 5
    assert visible[0]["area"] == "検索意図"
    assert any(item["title"] == "検索意図・ページ役割マップ" for item in visible)


def test_build_provider_focus_summary_counts_status_buckets() -> None:
    summary = panels_mod._build_provider_focus_summary(
        [
            {"status": "要対応"},
            {"status": "注意"},
            {"status": "通過"},
            {"status": "未判定"},
        ]
    )

    assert summary == {"fail": 1, "warn": 1, "pass": 1, "other": 1}


def test_build_workspace_tab_plan_keeps_primary_tabs_light_and_secondary_tabs_deferred() -> None:
    plan = panels_mod._build_workspace_tab_plan(
        {"comparison_workspace": {"competitor_summary": {"status": "available"}}},
        same_url_history=[{"id": 1}],
    )

    assert [item["name"] for item in plan["primary"]] == ["サマリー", "やること", "文章改善", "実装・設定"]
    assert [item["name"] for item in plan["secondary"]] == ["エンジニア向け", "履歴と比較"]


def test_build_implementation_stop_message_guides_when_primary_actions_exist() -> None:
    assert "上段 4 件" in panels_mod._build_implementation_stop_message(actionable_count=4, refresh_count=0)
    assert "旧データ由来" in panels_mod._build_implementation_stop_message(actionable_count=0, refresh_count=2)
    assert "参考情報だけ確認" in panels_mod._build_implementation_stop_message(actionable_count=0, refresh_count=0)


def test_intent_role_ui_helpers_keep_confidence_and_locations_human_readable() -> None:
    assert panels_mod._intent_confidence_label({"confidence": "high"}) == "判定根拠: 高"
    assert panels_mod._intent_confidence_label({"confidence": "medium"}) == "判定根拠: 中"
    assert panels_mod._intent_confidence_label({"confidence": "low"}) == "判定根拠: 低"

    assert panels_mod._intent_note_values(
        {"fix_locations": ["本文上部", "CTA直前", "FAQセクション"]},
        "fix_locations",
    ) == ["本文上部", "CTA直前", "FAQセクション"]
    assert panels_mod._intent_note_values(
        {"fix_location": "本文上部、CTA直前"},
        "fix_locations",
    ) == ["本文上部、CTA直前"]


def test_filter_actionable_google_controls_keeps_only_restrictive_items() -> None:
    rows = panels_mod._filter_actionable_google_controls(
        {
            "noindex": False,
            "nosnippet": True,
            "max_snippet": 120,
            "data_nosnippet_count": 0,
        }
    )

    assert rows == [
        {"title": "抜粋禁止（nosnippet）", "detail": "設定あり"},
    ]


def test_seo_additional_audit_rows_are_sorted_by_status_priority() -> None:
    rows = seo_tab_mod._build_additional_audit_rows(
        {
            "technical": {
                "international_targeting": {"summary": "hreflang不足", "status": "fail"},
                "x_robots_tag": {"summary": "X-Robots-Tag なし", "status": "pass"},
                "mobile_parity": {"summary": "viewport=yes", "status": "pass"},
                "page_experience": {"summary": "LCP=2200ms", "status": "warn"},
                "media_discovery": {"summary": "images=3", "status": "pass"},
            },
            "structure": {
                "link_quality": {"summary": "empty=1", "status": "warn"},
            },
            "web_vitals": {"lcp_ms": 2200, "cls_score": 0.03},
        },
        {
            "special_notes": {
                "openai_commerce": {"summary": "整備余地あり", "status": "warn"},
                "perplexity_operational": {"summary": "allowlistは別管理"},
            }
        },
    )

    assert rows[0]["title"] == "国際化 / インデックス制御"
    assert [row["status"] for row in rows] == ["fail", "warn", "warn", "warn", "pass", "reference"]
    assert {row["title"] for row in rows[1:4]} == {"リンク品質", "モバイル / ページ体験", "OpenAI Commerce"}
    assert rows[-2]["title"] == "画像 / 動画の発見性"
    assert rows[-1]["title"] == "Perplexity WAF / IP"


def test_short_reason_text_prefers_sentence_boundary() -> None:
    text = "比較・選び方の観点が不足しているためです。候補比較を短く先に示すと理解が速くなります。"

    short = panels_mod._short_reason_text(text, limit=30)

    assert short == "比較・選び方の観点が不足しているためです。"
