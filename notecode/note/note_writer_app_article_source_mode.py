from typing import Any, Dict, List


FIXED_ARTICLE_TYPE_LABELS = {
    "explanatory_article": "解説・ノウハウ",
    "daily_story": "日常のできごと",
    "branding": "紹介",
    "announcement": "お知らせ",
    "case_study": "事例・お客様の声",
    "industry_analysis": "業界・市場の話題",
    "comparative_review": "比較・選び方",
}

ARTICLE_TYPE_PRIORITY_KEYS = [
    "explanatory_article",
    "daily_story",
    "branding",
    "announcement",
    "case_study",
    "industry_analysis",
    "comparative_review",
]

SOURCE_MODE_LABELS = {
    "grounded": "資料あり",
    "web": "お任せ",
    "prompt_only": "プロンプトのみ",
}

_PROMPT_ONLY_ALLOWED_ARTICLE_TYPES = {"daily_story"}


def _order_article_type_keys(keys: List[str]) -> List[str]:
    priority = {key: idx for idx, key in enumerate(ARTICLE_TYPE_PRIORITY_KEYS)}
    return sorted(keys, key=lambda key: (priority.get(key, 999), key))


def _get_combined_article_types() -> dict:
    """Get article type labels for current UI mode."""
    combined = dict(FIXED_ARTICLE_TYPE_LABELS)
    ordered_keys = _order_article_type_keys(list(combined.keys()))
    return {key: combined[key] for key in ordered_keys}


def _get_combined_prompts() -> dict:
    """Get prompt catalog keys used for UI validation."""
    combined = {key: f"fixed:{key}" for key in FIXED_ARTICLE_TYPE_LABELS}
    ordered_keys = _order_article_type_keys(list(combined.keys()))
    return {key: combined[key] for key in ordered_keys}


def _is_prompt_only_allowed_article_type(article_type_key: str) -> bool:
    return str(article_type_key or "").strip().lower() in _PROMPT_ONLY_ALLOWED_ARTICLE_TYPES


def _prompt_only_ui_unlocked(
    *,
    article_type_key: str,
    past_blog_unlocked: bool = False,
) -> bool:
    return bool(
        _is_prompt_only_allowed_article_type(article_type_key)
        and bool(past_blog_unlocked)
    )


def _source_mode_options_for_article_type(
    article_type_key: str,
    *,
    past_blog_unlocked: bool = False,
) -> Dict[str, str]:
    options = {
        key: label
        for key, label in SOURCE_MODE_LABELS.items()
        if key != "prompt_only"
        or _prompt_only_ui_unlocked(
            article_type_key=article_type_key,
            past_blog_unlocked=past_blog_unlocked,
        )
    }
    return options or {"grounded": SOURCE_MODE_LABELS["grounded"]}


def _source_mode_allows_no_sources(
    *,
    article_type_key: str,
    source_mode_key: str,
    prompt_raw: str = "",
    past_blog_unlocked: bool = False,
) -> bool:
    return bool(
        _prompt_only_ui_unlocked(
            article_type_key=article_type_key,
            past_blog_unlocked=past_blog_unlocked,
        )
        and str(source_mode_key or "").strip().lower() == "prompt_only"
        and str(prompt_raw or "").strip()
    )


def _resolve_source_mode_selection(selected_label: Any) -> Dict[str, Any]:
    selected_text = str(selected_label or "").strip()
    source_mode_key = next(
        (key for key, label in SOURCE_MODE_LABELS.items() if label == selected_text),
        "grounded",
    )
    return {
        "source_mode_key": source_mode_key,
        "source_mode_label": SOURCE_MODE_LABELS[source_mode_key],
        "requires_source_inputs": source_mode_key == "grounded",
        "uses_web_research": source_mode_key == "web",
    }


def _build_source_mode_helper_text(
    *,
    article_type_key: str,
    source_mode_key: str,
    past_blog_unlocked: bool = False,
) -> str:
    normalized_article_type = str(article_type_key or "").strip()
    normalized_source_mode = str(source_mode_key or "").strip() or "grounded"
    if normalized_source_mode == "grounded":
        # Kept short on purpose: this renders directly under the mode
        # selector, right below section_intro_text's fuller explanation
        # of the same "資料あり" requirement (see _build_source_mode_input_surface
        # -> section_intro_text). Only state what that text doesn't cover.
        return "資料ありを選択中です。1行テーマは使いません。"
    if normalized_source_mode == "prompt_only":
        if not _is_prompt_only_allowed_article_type(normalized_article_type):
            return "プロンプトのみは日常のできごとの記事だけで使えます。"
        if not past_blog_unlocked:
            return "プロンプトのみは、公開済みブログの蓄積条件を満たした日常のできごとだけで使えます。"
        return "プロンプトのみで始めます。1行テーマを体験メモとして使い、公開済みブログは書き味と関心領域の参考に限定します。統計・価格・法律・医療・金融・比較優位・会社実績は足しません。"
    if normalized_article_type in {"branding", "announcement", "case_study", "comparative_review"}:
        return "この種類は資料ありで進めます。先に資料をそろえると次に進めます。"
    if not past_blog_unlocked:
        return "お任せは公開済みブログの蓄積条件を満たすまで選べません。いまは資料ありで進めてください。"
    return "お任せで始めます。1行テーマと公開済みブログの蓄積がそろうと、生成前に外部ソースの材料集めへ進みます。公開済みブログ本文は今回の記事の事実ソースには使いません。"


def _build_source_mode_input_surface(
    *,
    article_type_key: str,
    source_mode_key: str,
    past_blog_unlocked: bool = False,
) -> Dict[str, Any]:
    normalized_source_mode = str(source_mode_key or "").strip().lower() or "grounded"
    helper_text = _build_source_mode_helper_text(
        article_type_key=article_type_key,
        source_mode_key=normalized_source_mode,
        past_blog_unlocked=past_blog_unlocked,
    )
    if normalized_source_mode == "grounded":
        return {
            "section_intro_text": "資料ありでは、先に材料をそろえます。URL / PDF / 画像 / テキストを追加すると、生成前チェックへ進めます。",
            "source_mode_helper_text": helper_text,
            "prompt_visible": False,
            "prompt_label": "",
            "prompt_placeholder": "",
            "prompt_helper_text": "",
            "source_title_text": "先にそろえる資料",
            "source_helper_text": "資料ありでは、URL / PDF / 画像 / テキストのいずれかを1件以上追加すると開始できます。入力済みの方針や読者は保持します。",
        }
    if normalized_source_mode == "prompt_only":
        return {
            "section_intro_text": "公開済みブログの蓄積条件を満たした日常のできごとだけ、1行テーマから始められます。テーマは体験メモであり、外部事実の根拠にはしません。",
            "source_mode_helper_text": helper_text,
            "prompt_visible": bool(past_blog_unlocked),
            "prompt_label": "1行テーマ",
            "prompt_placeholder": "例: 夕方の打ち合わせで、言葉の受け取り方が少しズレた話",
            "prompt_helper_text": "起きた場面や引っかかりを短く入れます。公開済みブログは書き味の参考であり、今回記事の事実ソースではありません。",
            "source_title_text": "資料入力",
            "source_helper_text": "プロンプトのみでは資料を使いません。URL / PDF / 画像 / テキストを使う場合は資料ありへ切り替えます。",
        }
    if not past_blog_unlocked:
        return {
            "section_intro_text": "お任せは、公開済みブログの蓄積条件を満たすまで1行テーマから開始できません。いまは資料ありで材料を追加してください。",
            "source_mode_helper_text": helper_text,
            "prompt_visible": False,
            "prompt_label": "",
            "prompt_placeholder": "",
            "prompt_helper_text": "",
            "source_title_text": "資料入力",
            "source_helper_text": "公開済みブログが不足している場合は、URL / PDF / 画像 / テキストを使う資料ありで進めます。",
        }
    return {
        "section_intro_text": "必須入力を決めたあと、お任せでは1行テーマから始めます。公開済みブログの蓄積が十分なときだけ、外部ソースの材料集めへ進みます。",
        "source_mode_helper_text": helper_text,
        "prompt_visible": True,
        "prompt_label": "1行テーマ",
        "prompt_placeholder": "例: 選ぶ判断材料がすぐ伝わる記事にしたい",
        "prompt_helper_text": "何を書くか・何を重視するかだけを1行で入れます。タイトルは不要です。",
        "source_title_text": "必要に応じて足す資料",
        "source_helper_text": "手元の URL / PDF / 画像 / テキストを使いたい場合は、資料ありへ切り替えます。",
    }
