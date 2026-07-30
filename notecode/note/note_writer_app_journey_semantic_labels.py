"""Pure journey/semantic article label helpers for note_writer_app."""
from __future__ import annotations

from typing import Any, Dict, List


JOURNEY_PURPOSE_LABELS = {
    "explain": "解説・市場を伝える",
    "introduce": "会社・サービスの紹介記事を書く",
    "announce": "お知らせを伝える",
    "case": "事例・お客様の声を伝える",
    "compare": "比較・選び方を整理する",
    "daily": "日常のできごとを伝える",
}
JOURNEY_TARGET_LABELS = {
    "explain": {
        "concept": "解説・ノウハウ",
        "industry": "業界・市場の話題",
    },
    "introduce": {
        "company": "自社・会社紹介",
        "product_service": "商品・サービス紹介記事",
    },
    "announce": {
        "standard": "お知らせ",
    },
    "case": {
        "implementation": "事例・お客様の声",
    },
    "compare": {
        "tool_service": "比較・選び方",
    },
    "daily": {
        "day_to_day": "日常のできごと",
    },
}
JOURNEY_TARGET_LABELS_ALL = {
    **JOURNEY_TARGET_LABELS,
    "introduce": {
        **JOURNEY_TARGET_LABELS["introduce"],
        "activity_project": "活動・プロジェクト紹介記事",
        "recruit_culture": "採用・カルチャー紹介記事",
    },
    "case": {
        **JOURNEY_TARGET_LABELS["case"],
        "improvement": "改善事例",
        "incident": "事故・障害・インシデント",
        "learning": "学習用ケーススタディ",
    },
    "compare": {
        **JOURNEY_TARGET_LABELS["compare"],
        "method": "方法・進め方の比較",
        "vendor": "会社・ベンダー比較",
    },
    "daily": {
        **JOURNEY_TARGET_LABELS["daily"],
        "behind_the_scenes": "舞台裏・裏側",
    },
}
JOURNEY_COMPARE_AXIS_OPTIONS = {
    "price": "価格",
    "performance": "性能",
    "use_case": "用途",
    "safety": "安全性",
    "overall": "総合",
}
JOURNEY_COMPARE_GOAL_LABELS = {
    "fit_explain": "条件別に選び分ける",
    "organize": "違いを整理する",
    "prioritize": "優先順位をつける",
}
SEMANTIC_ARTICLE_KEY_LABELS = {
    "explanatory_article": "解説・ノウハウ",
    "industry_analysis": "業界・市場の話題",
    "company_introduction": "会社紹介",
    "product_introduction": "商品・サービス紹介記事",
    "activity_introduction": "活動・プロジェクト紹介記事",
    "recruit_culture": "採用・カルチャー紹介記事",
    "announcement": "お知らせ",
    "implementation_case": "事例・お客様の声",
    "improvement_case": "改善事例",
    "incident_case": "事故・障害・インシデント",
    "learning_case": "学習用ケーススタディ",
    "comparative_review": "比較・選び方",
    "daily_story": "日常のできごと",
    "branding": "紹介",
    "case_study": "事例・お客様の声",
}


def _get_journey_compare_axis_labels(axis_keys: List[str]) -> List[str]:
    labels: List[str] = []
    for key in axis_keys:
        label = JOURNEY_COMPARE_AXIS_OPTIONS.get(str(key or "").strip(), str(key or "").strip())
        if label and label not in labels:
            labels.append(label)
    return labels


def _get_journey_target_options(purpose_key: str) -> Dict[str, str]:
    return dict(JOURNEY_TARGET_LABELS.get(str(purpose_key or "").strip(), {}))


def _normalize_journey_target_selection(purpose_key: str, selected_label: Any) -> Dict[str, Any]:
    normalized_purpose = str(purpose_key or "").strip()
    options = _get_journey_target_options(normalized_purpose)
    option_labels = list(options.values())
    selected_text = str(selected_label or "").strip()
    target_key = next((key for key, label in options.items() if label == selected_text), "")
    target_label = selected_text
    if not target_key and options:
        target_key, target_label = next(iter(options.items()))
    return {
        "purpose_key": normalized_purpose,
        "target_key": target_key,
        "target_label": target_label,
        "option_labels": option_labels,
    }


def _label_for_compare_goal_key(goal_key: str) -> str:
    key = str(goal_key or "").strip()
    return JOURNEY_COMPARE_GOAL_LABELS.get(key, key)


def _label_for_semantic_article_key(semantic_key: str) -> str:
    key = str(semantic_key or "").strip()
    return SEMANTIC_ARTICLE_KEY_LABELS.get(key, key)
