from note.note_writer_app_journey_semantic_labels import (
    _get_journey_compare_axis_labels,
    _get_journey_target_options,
    _label_for_compare_goal_key,
    _label_for_semantic_article_key,
    _normalize_journey_target_selection,
)


def test_get_journey_compare_axis_labels_returns_empty_for_empty_list() -> None:
    assert _get_journey_compare_axis_labels([]) == []


def test_get_journey_compare_axis_labels_maps_known_axis_key() -> None:
    assert _get_journey_compare_axis_labels(["price"]) == ["価格"]


def test_get_journey_compare_axis_labels_falls_back_for_unknown_axis_key() -> None:
    assert _get_journey_compare_axis_labels(["custom_axis"]) == ["custom_axis"]


def test_get_journey_compare_axis_labels_deduplicates_labels() -> None:
    assert _get_journey_compare_axis_labels(["price", "price"]) == ["価格"]


def test_get_journey_compare_axis_labels_handles_mixed_known_and_unknown_keys() -> None:
    assert _get_journey_compare_axis_labels(["price", "custom_axis", "overall"]) == [
        "価格",
        "custom_axis",
        "総合",
    ]


def test_label_for_compare_goal_key_maps_known_key() -> None:
    assert _label_for_compare_goal_key("organize") == "違いを整理する"


def test_label_for_compare_goal_key_falls_back_for_unknown_key() -> None:
    assert _label_for_compare_goal_key("custom_goal") == "custom_goal"


def test_label_for_semantic_article_key_maps_known_key() -> None:
    assert _label_for_semantic_article_key("company_introduction") == "会社紹介"


def test_label_for_semantic_article_key_falls_back_for_unknown_key() -> None:
    assert _label_for_semantic_article_key("custom_semantic") == "custom_semantic"


def test_get_journey_target_options_returns_copy_for_purpose() -> None:
    options = _get_journey_target_options("introduce")

    assert options["company"] == "自社・会社紹介"
    options["product_service"] == "商品・サービス紹介記事"
    options["company"] = "changed"
    assert _get_journey_target_options("introduce")["company"] == "自社・会社紹介"


def test_normalize_journey_target_selection_maps_label_and_falls_back() -> None:
    selected = _normalize_journey_target_selection("explain", "業界・市場の話題")
    assert selected["target_key"] == "industry"
    assert selected["target_label"] == "業界・市場の話題"
    assert selected["option_labels"] == ["解説・ノウハウ", "業界・市場の話題"]

    fallback = _normalize_journey_target_selection("announce", "missing")
    assert fallback["target_key"] == "standard"
    assert fallback["target_label"] == "お知らせ"
