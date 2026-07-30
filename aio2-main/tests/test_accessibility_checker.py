from pathlib import Path

from core.site_health.accessibility_checker import (
    SCORING_VERSION,
    AccessibilityChecker,
    format_accessibility_result,
    get_wcag_compliance_level,
)
from core.site_health.browser_accessibility_scanner import (
    BROWSER_SCORING_VERSION,
    build_browser_accessibility_payload,
    build_browser_accessibility_raw,
)
from core.application.accessibility_improvement_builder import build_accessibility_improvement_actions


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "accessibility"


def _fixture_html(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_accessibility_score_full_machine_readable_html():
    html = """
    <!doctype html>
    <html lang="ja">
      <head><title>サービス紹介</title></head>
      <body>
        <header><a href="/">ホーム</a></header>
        <nav><a href="/service">サービス紹介</a></nav>
        <main>
          <h1>サービス紹介</h1>
          <section>
            <h2>入力支援</h2>
            <p>データ入力、スキャニング、分析、運用支援をまとめて提供します。</p>
            <img src="service.jpg" alt="データ入力サービスの作業風景">
            <a href="/contact" aria-label="お問い合わせへ進む"></a>
            <button aria-label="メニューを開く"></button>
            <label for="email">メールアドレス</label>
            <input id="email" type="email">
            <select aria-label="相談内容"><option>見積もり</option></select>
            <textarea title="補足内容"></textarea>
            <iframe src="/map" title="アクセス地図"></iframe>
          </section>
        </main>
        <footer>会社情報</footer>
      </body>
    </html>
    """

    result = AccessibilityChecker(html).run_all_checks()

    assert result["score"] == 100
    assert result["score_status"] == "good"
    assert result["scoring_version"] == SCORING_VERSION
    assert result["affected_counts"]["total_issues"] == 0
    assert result["issue_groups"] == []
    assert set(result) >= {
        "score",
        "score_status",
        "issue_groups",
        "affected_counts",
        "top_actions",
        "scoring_version",
    }


def test_accessibility_score_reports_targeted_issues():
    html = """
    <html>
      <head></head>
      <body>
        <h2>会社情報</h2>
        <h4>沿革</h4>
        <img src="logo.png">
        <a href="/contact"><img src="icon.png"></a>
        <button></button>
        <input name="email">
        <iframe src="/embed"></iframe>
        <p>お問い合わせ前に会社情報、沿革、アクセス、実績を確認できます。</p>
      </body>
    </html>
    """

    result = AccessibilityChecker(html).run_all_checks()

    assert result["score"] < 50
    assert result["score_status"] == "needs_work"
    assert result["affected_counts"]["html_lang"] == 1
    assert result["affected_counts"]["title"] == 1
    assert result["affected_counts"]["h1"] == 1
    assert result["affected_counts"]["image_alt"] == 2
    assert result["affected_counts"]["interactive_names"] == 2
    assert result["affected_counts"]["form_labels"] == 1
    assert result["affected_counts"]["iframe_titles"] == 1
    assert {group["id"] for group in result["issue_groups"]} >= {
        "html_lang",
        "title",
        "h1",
        "heading_hierarchy",
        "landmarks",
        "image_alt",
        "interactive_names",
        "form_labels",
        "iframe_titles",
    }
    assert result["top_actions"]


def test_accessibility_score_caps_blank_page():
    html = '<html lang="ja"><head><title>空白</title></head><body></body></html>'

    result = AccessibilityChecker(html).run_all_checks()

    assert result["score"] <= 35
    assert result["score_cap"]["applied"] is True
    assert result["affected_counts"]["score_cap"] == 35
    assert result["top_actions"][0]["group"] == "content_structure_volume"


def test_accessibility_format_uses_improvement_score_and_automatic_detection_words():
    result = AccessibilityChecker(
        """
        <html lang="ja"><head><title>タイトル</title></head><body>
        <header>上部</header><nav>ナビ</nav><main><h1>見出し</h1>
        <h2>本文</h2><p>本文が十分にあり、自動検出の対象となる構造もあります。</p>
        </main><footer>下部</footer></body></html>
        """
    ).run_all_checks()

    formatted = format_accessibility_result(result)
    score_summary = get_wcag_compliance_level(result)

    assert formatted["title"] == "見やすさ・使いやすさ改善スコア"
    assert "改善スコア" in formatted["status"]
    assert formatted["subtitle"].startswith("自動検出")
    assert score_summary["method"] == "自動検出"
    assert "準拠" not in str(formatted)
    assert "準拠" not in str(score_summary)


def test_accessibility_improvement_actions_are_specific_and_non_engineer_readable():
    result = AccessibilityChecker(
        """
        <html>
          <head><title>商品紹介</title></head>
          <body>
            <header><a href="/">ホーム</a></header><main>
              <h2>商品紹介</h2><h4>特徴</h4>
              <img src="product.jpg">
              <button></button>
              <input name="email">
              <p>商品画像、サービス説明画像、問い合わせ導線を掲載しています。</p>
            </main>
          </body>
        </html>
        """
    ).run_all_checks()

    payload = build_accessibility_improvement_actions(
        {"accessibility": {"raw": result, "formatted": {"score": result["score"]}}},
        limit=5,
    )

    assert payload["score"] == result["score"]
    assert 3 <= len(payload["actions"]) <= 5
    engineer_rendered = "\n".join(
        str(action.get(key, ""))
        for action in payload["actions"]
        for key in ("title", "action", "target_element", "reason", "verification")
    )
    audience_rendered = "\n".join(
        str((action.get("audience") or {}).get(key, ""))
        for action in payload["actions"]
        for key in ("action", "impact", "review_area", "handoff_to", "confirmation")
    )
    assert "alt" in engineer_rendered
    assert "aria-label" in engineer_rendered
    assert "対象:" not in engineer_rendered
    assert "aria-label" not in audience_rendered
    assert "<img" not in audience_rendered
    assert all((action.get("audience") or {}).get("handoff_to") for action in payload["actions"])
    assert all((action.get("engineer") or {}).get("target_element") for action in payload["actions"])
    assert all((action.get("engineer") or {}).get("verification") for action in payload["actions"])
    assert all(action.get("target_element") for action in payload["actions"])
    assert all(action.get("reason") for action in payload["actions"])
    assert all(action.get("verification") for action in payload["actions"])


def test_accessibility_improvement_actions_do_not_frontload_generic_fallback_for_zero_findings():
    result = AccessibilityChecker(_fixture_html("good_basic_page.html")).run_all_checks()

    payload = build_accessibility_improvement_actions(
        {"accessibility": {"raw": result, "formatted": {"score": result["score"]}}},
        limit=5,
    )

    assert result["issue_groups"] == []
    assert payload["actions"] == []
    assert payload["actual_issue_count"] == 0
    assert payload["confirmation_items"]
    assert "汎用修正カード" in payload["confirmation_items"][0]["detail"]


def test_browser_accessibility_report_maps_to_existing_action_shape() -> None:
    report = {
        "scan_run": {
            "requested_url": "https://example.com/",
            "final_url": "https://example.com/",
            "status": "completed",
            "profile_ids": ["jis-2016-aa"],
            "standards_checked_at": "2026-06-11",
        },
        "pages": [
            {
                "page_id": "page-1",
                "page_role": "top",
                "url": "https://example.com/",
                "http_status": 200,
                "title": "Example",
                "lang": "ja",
                "headings": [{"level": 1, "text": "Example", "selector": "h1"}],
                "landmarks": [{"role": "main", "label": "", "selector": "main"}],
                "controls": [{"role": "button", "name": "", "selector": "button", "disabled": False}],
                "images": [{"selector": "img", "alt_state": "missing", "alt": None}],
                "tab_order_sample": [{"step": 1, "role": "button", "name": "", "selector": "button"}],
                "screen_reader_preview": {
                    "missing_accessible_names": [{"role": "button", "selector": "button", "reason": "名前なし"}],
                    "possible_reading_risks": [{"type": "image-alt", "selector": "img", "message": "altなし"}],
                },
            }
        ],
        "findings": [
            {
                "rule_id": "color-contrast",
                "severity": "serious",
                "selector": ".hero-copy",
                "message": "文字のコントラスト不足",
                "user_impact": "文字が読みにくい",
                "remediation": "文字色と背景色を見直してください。",
                "source": "axe-core",
            },
            {
                "rule_id": "meta-viewport",
                "severity": "critical",
                "selector": "head > meta",
                "message": "拡大表示が制限されています",
                "user_impact": "文字を拡大しにくい",
                "remediation": "user-scalable=no を外してください。",
                "source": "axe-core",
            },
            {
                "rule_id": "button-name",
                "severity": "critical",
                "selector": "button",
                "message": "ボタン名がありません",
                "user_impact": "操作内容が伝わりません",
                "remediation": "aria-label を付けてください。",
                "source": "axe-core",
            },
        ],
        "score_snapshot": {
            "score": 42,
            "max_score": 100,
            "raw_score": 54.2,
            "score_cap": 59,
            "score_cap_reason": "Criticalの自動検出があるため、上限を59点にしました。",
            "sample_confidence": "low",
            "evidence_level": "standard",
            "manual_risk_count": 2,
            "scanned_page_count": 1,
            "severity_counts": {"critical": 2, "serious": 1, "moderate": 0, "minor": 0},
            "not_scored_risks": [{"rule_id": "color-contrast", "reason": "文脈確認"}],
        },
    }

    raw = build_browser_accessibility_raw(report)
    payload = build_browser_accessibility_payload(report)
    actions = build_accessibility_improvement_actions({"accessibility": payload}, limit=5)

    assert raw["score"] == 42
    assert raw["scoring_version"] == BROWSER_SCORING_VERSION
    assert raw["detection_source"] == "browser"
    assert raw["affected_counts"]["manual_review_pending"] == 2
    assert {group["id"] for group in raw["issue_groups"]} >= {"color_contrast", "zoom_scaling", "interactive_names"}
    assert payload["formatted"]["title"] == "見やすさ・使いやすさ改善スコア"
    assert payload["formatted"]["detection_source"] == "browser"
    assert actions["title"] == "見やすさ・使いやすさ改善"
    rendered = "\n".join(str(action) for action in actions["actions"])
    assert "文字色" in rendered
    assert "拡大" in rendered


def test_accessibility_action_builder_llm_failure_keeps_fallback_count_and_order():
    html = """
    <html>
      <head></head>
      <body>
        <main>
          <h2>商品紹介</h2><h4>特徴</h4>
          <img src="product.jpg">
          <button></button>
          <input name="email">
          <iframe src="/map"></iframe>
          <p>商品画像、問い合わせ導線、アクセス地図を掲載しています。</p>
        </main>
      </body>
    </html>
    """
    result = AccessibilityChecker(html).run_all_checks()
    site_health = {"accessibility": {"raw": result, "formatted": {"score": result["score"]}}}

    class FailingResponses:
        def create(self, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("network unavailable")

    class FailingClient:
        responses = FailingResponses()

    fallback = build_accessibility_improvement_actions(site_health, limit=5, html=html, use_llm=False)
    with_llm_failure = build_accessibility_improvement_actions(
        site_health,
        limit=5,
        html=html,
        use_llm=True,
        llm_client=FailingClient(),
        reasoning_effort="medium",
        max_parallel=99,
    )

    fallback_groups = [action["group"] for action in fallback["actions"]]
    llm_failure_groups = [action["group"] for action in with_llm_failure["actions"]]
    assert llm_failure_groups == fallback_groups
    assert len(with_llm_failure["actions"]) == len(fallback["actions"])
    assert [action["priority_rank"] for action in with_llm_failure["actions"]] == [
        action["priority_rank"] for action in fallback["actions"]
    ]

    metadata = with_llm_failure["metadata"]
    assert metadata["fallback_used"] is True
    assert metadata["llm_used"] is False
    assert metadata["prompt_version"] == "accessibility-action-copy-v1"
    assert metadata["ruleset_version"] == "accessibility-action-builder-v1"
    assert metadata["model"] == "gpt-5.4-nano"
    assert metadata["reasoning"] == {"effort": "low"}
    assert metadata["temperature"] == 0.0
    assert metadata["max_parallel"] == 5
    assert len(metadata["html_hash"]) == 64


def test_accessibility_action_builder_llm_copy_keeps_rule_based_order():
    html = """
    <html><body>
      <main>
        <img src="product.jpg">
        <button></button>
        <input name="email">
        <p>問い合わせ導線を掲載しています。</p>
      </main>
    </body></html>
    """
    result = AccessibilityChecker(html).run_all_checks()
    site_health = {"accessibility": {"raw": result, "formatted": {"score": result["score"]}}}

    class Response:
        output_text = '{"title":"整形済みタイトル","action":"整形済みアクション","reason":"整形済み理由","verification":"整形済み確認"}'

    class Responses:
        def __init__(self) -> None:
            self.calls = []

        def create(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            return Response()

    class Client:
        def __init__(self) -> None:
            self.responses = Responses()

    client = Client()
    fallback = build_accessibility_improvement_actions(site_health, limit=3, html=html, use_llm=False)
    formatted = build_accessibility_improvement_actions(
        site_health,
        limit=3,
        html=html,
        use_llm=True,
        llm_client=client,
        reasoning_effort="none",
        max_parallel=3,
    )

    assert [action["group"] for action in formatted["actions"]] == [
        action["group"] for action in fallback["actions"]
    ]
    assert all(action["title"] == "整形済みタイトル" for action in formatted["actions"])
    assert formatted["metadata"]["llm_used"] is True
    first_call = client.responses.calls[0]
    assert first_call["model"] == "gpt-5.4-nano"
    assert first_call["reasoning"] == {"effort": "none"}
    assert "temperature" not in first_call
    assert first_call["text"]["format"]["type"] == "json_schema"


def test_accessibility_action_builder_llm_model_switch_gates_incompatible_params():
    html = """
    <html><body>
      <main>
        <img src="product.jpg">
        <button></button>
        <p>問い合わせ導線を掲載しています。</p>
      </main>
    </body></html>
    """
    result = AccessibilityChecker(html).run_all_checks()
    site_health = {"accessibility": {"raw": result, "formatted": {"score": result["score"]}}}

    class Response:
        output_text = '{"title":"T","action":"A","reason":"R","verification":"V"}'

    class Responses:
        def __init__(self) -> None:
            self.calls = []

        def create(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            return Response()

    class Client:
        def __init__(self) -> None:
            self.responses = Responses()

    gpt5_client = Client()
    build_accessibility_improvement_actions(
        site_health,
        limit=1,
        html=html,
        use_llm=True,
        llm_client=gpt5_client,
        model="gpt-5.6-luna",
        reasoning_effort="low",
    )
    gpt5_call = gpt5_client.responses.calls[0]
    assert gpt5_call["model"] == "gpt-5.6-luna"
    assert gpt5_call["reasoning"] == {"effort": "low"}
    assert "temperature" not in gpt5_call
    assert "top_p" not in gpt5_call

    gpt41_client = Client()
    build_accessibility_improvement_actions(
        site_health,
        limit=1,
        html=html,
        use_llm=True,
        llm_client=gpt41_client,
        model="gpt-4.1-mini-2025-04-14",
        reasoning_effort="low",
    )
    gpt41_call = gpt41_client.responses.calls[0]
    assert gpt41_call["model"] == "gpt-4.1-mini-2025-04-14"
    assert "reasoning" not in gpt41_call
    assert gpt41_call["temperature"] == 0.0


def test_accessibility_fixture_blank_page_is_capped_low() -> None:
    result = AccessibilityChecker(_fixture_html("blank_page.html")).run_all_checks()

    assert result["score"] <= 35
    assert result["score_cap"]["applied"] is True
    assert result["top_actions"][0]["group"] == "content_structure_volume"


def test_accessibility_fixture_good_basic_page_scores_full() -> None:
    result = AccessibilityChecker(_fixture_html("good_basic_page.html")).run_all_checks()

    assert result["score"] == 100
    assert result["issue_groups"] == []
    assert result["affected_counts"]["total_issues"] == 0


def test_accessibility_fixture_many_missing_alt_prioritizes_image_alt() -> None:
    result = AccessibilityChecker(_fixture_html("many_missing_alt.html")).run_all_checks()

    assert result["affected_counts"]["image_alt"] == 5
    assert result["checks"]["image_alt"]["status"] == "needs_work"
    assert result["top_actions"][0]["group"] == "image_alt"


def test_accessibility_fixture_repeated_common_header_button_is_not_overcounted() -> None:
    result = AccessibilityChecker(_fixture_html("repeated_header_button_missing_name.html")).run_all_checks()

    assert result["affected_counts"]["interactive_names"] == 1
    assert result["checks"]["interactive_names"]["affected_count"] == 1
    assert result["score"] >= 95


def test_accessibility_fixture_missing_form_labels_are_reported() -> None:
    result = AccessibilityChecker(_fixture_html("missing_form_labels.html")).run_all_checks()

    assert result["affected_counts"]["form_labels"] == 3
    assert result["checks"]["form_labels"]["status"] == "needs_work"
    assert any(group["id"] == "form_labels" for group in result["issue_groups"])


def test_accessibility_fixture_heading_skip_is_reported() -> None:
    result = AccessibilityChecker(_fixture_html("heading_skip.html")).run_all_checks()

    assert result["affected_counts"]["heading_hierarchy"] == 1
    assert result["checks"]["heading_hierarchy"]["headings"] == [
        {"level": 1, "text": "Heading Skip"},
        {"level": 2, "text": "Main Section"},
        {"level": 4, "text": "Skipped Detail"},
    ]


def test_accessibility_fixture_no_landmarks_is_reported() -> None:
    result = AccessibilityChecker(_fixture_html("no_landmarks.html")).run_all_checks()

    assert result["affected_counts"]["landmarks"] == 4
    assert result["checks"]["landmarks"]["status"] == "needs_work"
    assert any(group["id"] == "landmarks" for group in result["issue_groups"])


def test_accessibility_fixture_llm_fallback_keeps_rank_for_representative_html() -> None:
    html = _fixture_html("many_missing_alt.html")
    result = AccessibilityChecker(html).run_all_checks()
    site_health = {"accessibility": {"raw": result, "formatted": {"score": result["score"]}}}

    class FailingResponses:
        def create(self, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("offline")

    class FailingClient:
        responses = FailingResponses()

    fallback = build_accessibility_improvement_actions(site_health, limit=5, html=html, use_llm=False)
    failed_llm = build_accessibility_improvement_actions(
        site_health,
        limit=5,
        html=html,
        use_llm=True,
        llm_client=FailingClient(),
    )

    assert [item["group"] for item in failed_llm["actions"]] == [
        item["group"] for item in fallback["actions"]
    ]
    assert [item["priority_rank"] for item in failed_llm["actions"]] == [
        item["priority_rank"] for item in fallback["actions"]
    ]
    assert len(failed_llm["actions"]) == len(fallback["actions"])
