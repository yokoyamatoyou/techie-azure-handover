from note.omakase_seed_builder import (
    OMAKASE_PREFLIGHT_AUTO_SOURCE_READY,
    OMAKASE_PREFLIGHT_FALLBACK,
    OMAKASE_PREFLIGHT_NEEDS_INPUT,
    OMAKASE_PREFLIGHT_READY,
    build_omakase_preflight,
    dominant_cluster_count,
    merge_omakase_seed_into_kwargs,
    omakase_available,
    total_body_chars,
    usable_posts_count,
)


def _build_post(
    *,
    title: str,
    summary: str,
    url: str,
    article_type: str = "daily_story",
    body_chars: int = 1800,
    quality_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "url": url,
        "summary": summary,
        "article_type": article_type,
        "body_chars": body_chars,
        "quality_summary": quality_summary
        or {
            "passed": True,
            "blocked": False,
            "alignment_score": 0.82,
            "soft_warning_count": 1,
            "naturalness_passed": True,
            "naturalness_issue_count": 0,
            "title_placeholder": False,
        },
    }


def test_omakase_preflight_returns_ready_when_sources_exist() -> None:
    result = build_omakase_preflight(
        requested_article_type="branding",
        user_prompt_text="会社紹介を自然に整える",
        source_values=["https://example.com/about"],
        source_documents=[
            {
                "title": "会社概要",
                "locator": "https://example.com/about",
                "content": "事業内容と強みを紹介しています。",
                "source_type": "url",
            }
        ],
        published_post_candidates=[
            _build_post(
                title="導入メモ 1",
                summary="導入メモの整理です。",
                url="https://example.com/posts/1",
            ),
            _build_post(
                title="導入メモ 2",
                summary="運用メモの整理です。",
                url="https://example.com/posts/2",
            ),
            _build_post(
                title="導入メモ 3",
                summary="改善メモの整理です。",
                url="https://example.com/posts/3",
            ),
        ],
    )

    assert result["status"] == OMAKASE_PREFLIGHT_READY
    assert result["charge_ready"] is True
    assert result["seed"]["source_mode"] == "grounded"
    assert result["seed"]["article_type"] == "branding"
    assert result["existing_post_count"] == 3
    assert result["total_body_chars"] == 5400
    assert result["omakase_available"] is True


def test_inventory_helpers_report_post_count_total_chars_and_unlock_state() -> None:
    posts = [
        _build_post(
            title="ローソン スイーツ 春の新作",
            summary="ローソン スイーツ 春の傾向を整理した記事。",
            url="https://example.com/posts/lawson-1",
        ),
        _build_post(
            title="ローソン スイーツ 食感の比較",
            summary="ローソン スイーツ 春の違いをまとめた記事。",
            url="https://example.com/posts/lawson-2",
        ),
        _build_post(
            title="ローソン スイーツ 売れ筋メモ",
            summary="ローソン スイーツ 春の売れ筋を追った記事。",
            url="https://example.com/posts/lawson-3",
        ),
    ]

    assert usable_posts_count(posts) == 3
    assert dominant_cluster_count(posts) == 3
    assert total_body_chars(posts) == 5400
    assert omakase_available(posts) is True


def test_omakase_preflight_returns_auto_source_ready_when_prompt_and_inventory_are_sufficient() -> None:
    result = build_omakase_preflight(
        requested_article_type="",
        user_prompt_text="生成AI導入で最初に決めることを実務向けに整理したい",
        preferred_source_mode="auto",
        published_post_candidates=[
            _build_post(title="記事1", summary="要約1", url="https://example.com/posts/1"),
            _build_post(title="記事2", summary="要約2", url="https://example.com/posts/2"),
            _build_post(title="記事3", summary="要約3", url="https://example.com/posts/3"),
        ],
        industry_hint="SaaS",
    )

    assert result["status"] == OMAKASE_PREFLIGHT_AUTO_SOURCE_READY
    assert result["charge_ready"] is False
    assert result["seed"]["source_mode"] == "web"
    assert result["seed"]["article_type"] == "explanatory_article"
    assert result["total_body_chars"] == 5400
    assert result["omakase_available"] is True


def test_omakase_preflight_blocks_when_post_count_is_below_threshold_even_if_chars_are_enough() -> None:
    result = build_omakase_preflight(
        requested_article_type="daily_story",
        user_prompt_text="運用で見えた変化を整理したい",
        preferred_source_mode="auto",
        published_post_candidates=[
            _build_post(title="記事1", summary="要約1", url="https://example.com/posts/1", body_chars=3000),
            _build_post(title="記事2", summary="要約2", url="https://example.com/posts/2", body_chars=3000),
        ],
    )

    assert result["status"] == OMAKASE_PREFLIGHT_FALLBACK
    assert result["reason_code"] == "OMK_FALLBACK_INVENTORY_POSTS_INSUFFICIENT"
    assert result["existing_post_count"] == 2
    assert result["total_body_chars"] == 6000
    assert result["omakase_available"] is False


def test_omakase_preflight_blocks_when_total_body_chars_are_below_threshold() -> None:
    result = build_omakase_preflight(
        requested_article_type="daily_story",
        user_prompt_text="運用で見えた変化を整理したい",
        preferred_source_mode="auto",
        published_post_candidates=[
            _build_post(title="記事1", summary="要約1", url="https://example.com/posts/1", body_chars=1000),
            _build_post(title="記事2", summary="要約2", url="https://example.com/posts/2", body_chars=1100),
            _build_post(title="記事3", summary="要約3", url="https://example.com/posts/3", body_chars=1100),
        ],
    )

    assert result["status"] == OMAKASE_PREFLIGHT_FALLBACK
    assert result["reason_code"] == "OMK_FALLBACK_TOTAL_BODY_CHARS_INSUFFICIENT"
    assert result["existing_post_count"] == 3
    assert result["total_body_chars"] == 3200
    assert result["omakase_available"] is False


def test_omakase_preflight_returns_fallback_for_blocked_article_without_sources() -> None:
    result = build_omakase_preflight(
        requested_article_type="announcement",
        user_prompt_text="認証方式変更のお知らせを書きたい",
        preferred_source_mode="auto",
        published_post_candidates=[
            _build_post(title="記事1", summary="要約1", url="https://example.com/posts/1"),
            _build_post(title="記事2", summary="要約2", url="https://example.com/posts/2"),
            _build_post(title="記事3", summary="要約3", url="https://example.com/posts/3"),
        ],
    )

    assert result["status"] == OMAKASE_PREFLIGHT_FALLBACK
    assert result["charge_ready"] is False
    assert result["reason_code"] == "OMK_FALLBACK_SOURCE_REQUIRED"
    assert result["fallback_options"][0]["source_mode"] == "grounded"


def test_omakase_preflight_disables_followup_mode_in_current_mainline() -> None:
    result = build_omakase_preflight(
        requested_article_type="daily_story",
        user_prompt_text="前回の続き",
        preferred_source_mode="followup",
        published_post_candidates=[
            _build_post(title="記事1", summary="要約1", url="https://example.com/posts/1"),
            _build_post(title="記事2", summary="要約2", url="https://example.com/posts/2"),
            _build_post(title="記事3", summary="要約3", url="https://example.com/posts/3"),
        ],
    )

    assert result["status"] == OMAKASE_PREFLIGHT_FALLBACK
    assert result["reason_code"] == "OMK_FALLBACK_FOLLOWUP_DISABLED"
    assert result["seed"] == {}


def test_omakase_preflight_returns_needs_input_for_blank_theme() -> None:
    result = build_omakase_preflight(
        requested_article_type="",
        user_prompt_text="",
        preferred_source_mode="auto",
        published_post_candidates=[],
    )

    assert result["status"] == OMAKASE_PREFLIGHT_NEEDS_INPUT
    assert result["charge_ready"] is False
    assert result["needs_input_items"][0]["field"] == "topic"
    assert result["fallback_options"]


def test_merge_omakase_seed_into_kwargs_overrides_only_seeded_fields() -> None:
    merged = merge_omakase_seed_into_kwargs(
        {
            "article_type": "branding",
            "user_prompt_text": "元の入力",
            "source_mode": "grounded",
            "source_values": [],
            "source_documents": [],
            "industry_hint": "",
            "retry_memo": [],
        },
        {
            "status": "AUTO_SOURCE_READY",
            "charge_ready": False,
            "reason_code": "OMK_AUTO_SOURCE_READY",
            "message": "自動で材料収集を始められます。",
            "fallback_options": [],
            "needs_input_items": [],
            "usable_posts_count": 4,
            "dominant_cluster_count": 3,
            "omakase_available": True,
            "seed": {
                "article_type": "explanatory_article",
                "user_prompt_text": "生成AI導入で最初に決めること",
                "source_mode": "web",
                "industry_hint": "SaaS",
            },
        },
    )

    assert merged["article_type"] == "explanatory_article"
    assert merged["user_prompt_text"] == "生成AI導入で最初に決めること"
    assert merged["source_mode"] == "web"
    assert merged["industry_hint"] == "SaaS"
    assert merged["omakase_preflight_status"] == "AUTO_SOURCE_READY"
    assert merged["omakase_charge_ready"] is False
    assert merged["omakase_reason_code"] == "OMK_AUTO_SOURCE_READY"
    assert merged["omakase_usable_posts_count"] == 4
    assert merged["omakase_dominant_cluster_count"] == 3
    assert merged["omakase_available"] is True


def test_merge_omakase_seed_into_kwargs_clears_stale_sources_for_auto_source_seed() -> None:
    merged = merge_omakase_seed_into_kwargs(
        {
            "article_type": "branding",
            "user_prompt_text": "元の入力",
            "source_mode": "grounded",
            "source_values": ["https://example.com/about"],
            "source_documents": [{"title": "会社概要"}],
            "source_trace": [{"url": "https://example.com/about"}],
        },
        {
            "status": "AUTO_SOURCE_READY",
            "charge_ready": False,
            "reason_code": "OMK_AUTO_SOURCE_READY",
            "message": "自動で材料収集を始められます。",
            "fallback_options": [],
            "needs_input_items": [],
            "usable_posts_count": 0,
            "dominant_cluster_count": 0,
            "omakase_available": False,
            "seed": {
                "article_type": "explanatory_article",
                "user_prompt_text": "生成AI導入で最初に決めること",
                "source_mode": "web",
                "source_values": [],
                "source_documents": [],
                "source_trace": [],
            },
        },
    )

    assert merged["source_mode"] == "web"
    assert merged["source_values"] == []
    assert merged["source_documents"] == []
    assert merged["source_trace"] == []
    assert merged["omakase_available"] is False
