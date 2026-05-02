from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analysis_lib import classify_keyword_intent, dedupe_preserve_order, normalize_query_text, normalize_text


@dataclass(frozen=True)
class ManagedPromptTemplate:
    key: str
    label: str
    family: str
    suffix: str
    signals: tuple[str, ...]
    purpose: str


DEFAULT_MANAGED_PROMPT_TEMPLATES: dict[str, tuple[ManagedPromptTemplate, ...]] = {
    "business_ja": (
        ManagedPromptTemplate("comparison", "比較", "検討", "比較 違い", ("比較", "違い", "vs", "versus", "おすすめ", "代替"), "候補差分と選定軸を確認する"),
        ManagedPromptTemplate("price", "料金", "検討", "料金 月額 初期費用", ("料金", "価格", "費用", "相場", "プラン", "月額"), "費用条件と導入前提を確認する"),
        ManagedPromptTemplate("case_study", "事例", "信頼", "導入事例 実績", ("事例", "導入", "実績", "成功例", "レビュー"), "実績と成果の根拠を確認する"),
        ManagedPromptTemplate("faq", "FAQ", "検討", "FAQ 導入前の疑問", ("faq", "よくある質問", "とは", "疑問", "できますか"), "導入前の疑問を先回りで確認する"),
        ManagedPromptTemplate("support", "サポート", "運用", "サポート 運用体制", ("サポート", "運用", "体制", "保守"), "運用体制と継続支援を確認する"),
        ManagedPromptTemplate("reputation", "評判", "信頼", "評判 口コミ", ("評判", "口コミ", "イメージ"), "第三者評価とブランド想起を確認する"),
        ManagedPromptTemplate("anxiety", "導入不安", "障壁", "導入前の不安", ("不安", "失敗", "注意点"), "失敗リスクや不安要素を確認する"),
        ManagedPromptTemplate("how_to", "手順", "実装", "使い方 導入手順", ("使い方", "方法", "手順", "howto"), "導入方法と進め方を確認する"),
    )
}

PROMPT_FAMILY_ORDER = ("指名", "検討", "信頼", "障壁", "実装", "運用", "地域", "探索")

INTENT_TO_PROMPT_KEY = {
    "comparison": "comparison",
    "price": "price",
    "case_study": "case_study",
    "faq": "faq",
    "how_to": "how_to",
    "local": "local",
    "branded": "branded",
    "general": "general",
}

PROMPT_KEY_METADATA: dict[str, dict[str, str]] = {
    "comparison": {"label": "比較", "family": "検討", "purpose": "候補差分と選定軸を確認する"},
    "price": {"label": "料金", "family": "検討", "purpose": "費用条件と導入前提を確認する"},
    "case_study": {"label": "事例", "family": "信頼", "purpose": "実績と成果の根拠を確認する"},
    "faq": {"label": "FAQ", "family": "検討", "purpose": "導入前の疑問を先回りで確認する"},
    "support": {"label": "サポート", "family": "運用", "purpose": "運用体制と継続支援を確認する"},
    "reputation": {"label": "評判", "family": "信頼", "purpose": "第三者評価とブランド想起を確認する"},
    "anxiety": {"label": "導入不安", "family": "障壁", "purpose": "失敗リスクや不安要素を確認する"},
    "how_to": {"label": "手順", "family": "実装", "purpose": "導入方法と進め方を確認する"},
    "local": {"label": "地域", "family": "地域", "purpose": "地域条件や対応範囲を確認する"},
    "branded": {"label": "指名", "family": "指名", "purpose": "ブランド想起と指名検索の反応を見る"},
    "general": {"label": "探索", "family": "探索", "purpose": "入口となる探索系の質問として扱う"},
}


def get_managed_prompt_templates(template_set: str) -> tuple[ManagedPromptTemplate, ...]:
    return DEFAULT_MANAGED_PROMPT_TEMPLATES.get(template_set, DEFAULT_MANAGED_PROMPT_TEMPLATES["business_ja"])


def build_fallback_expansions_from_templates(
    base_query: str,
    original_query: str,
    *,
    template_set: str,
    max_expansions: int,
) -> list[str]:
    normalized_base = normalize_text(base_query or original_query)
    lowered = normalize_query_text(normalized_base)
    expansions: list[str] = []
    for template in get_managed_prompt_templates(template_set):
        if any(signal in lowered for signal in template.signals):
            continue
        expansions.append(f"{normalized_base} {template.suffix}")
        if len(expansions) >= max(0, int(max_expansions or 0)):
            break
    return expansions


def infer_prompt_key(query: str, *, template_set: str = "business_ja", brand_terms: list[str] | None = None) -> str:
    normalized_query = normalize_text(query)
    lowered = normalize_query_text(normalized_query)
    templates = get_managed_prompt_templates(template_set)
    for template in templates:
        suffix_norm = normalize_query_text(template.suffix)
        if suffix_norm and (lowered.endswith(suffix_norm) or lowered == suffix_norm or f"{suffix_norm}" in lowered):
            return template.key
    scored_matches: list[tuple[int, int, str]] = []
    for index, template in enumerate(templates):
        score = sum(1 for signal in template.signals if signal in lowered)
        if score > 0:
            scored_matches.append((score, -index, template.key))
    if scored_matches:
        scored_matches.sort(reverse=True)
        return scored_matches[0][2]
    intent = classify_keyword_intent(normalized_query, brand_terms=brand_terms)
    return INTENT_TO_PROMPT_KEY.get(str(intent.get("primary") or "general"), "general")


def build_prompt_taxonomy_records(
    user_query_raw: str,
    expanded_queries: list[str],
    *,
    template_set: str,
    brand_terms: list[str] | None = None,
    user_query_short: str = "",
    query_was_shortened: bool = False,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    base_query = normalize_text(user_query_short if query_was_shortened and user_query_short else user_query_raw)
    normalized_queries = dedupe_preserve_order([normalize_text(item) for item in expanded_queries if normalize_text(item)])
    if not normalized_queries and base_query:
        normalized_queries = [base_query]
    for index, query in enumerate(normalized_queries, start=1):
        prompt_key = infer_prompt_key(query, template_set=template_set, brand_terms=brand_terms)
        metadata = PROMPT_KEY_METADATA.get(prompt_key, PROMPT_KEY_METADATA["general"])
        records.append(
            {
                "query": query,
                "query_norm": normalize_query_text(query),
                "query_index": index,
                "role": "base" if index == 1 else "expansion",
                "prompt_key": prompt_key,
                "prompt_label": metadata["label"],
                "prompt_family": metadata["family"],
                "purpose": metadata["purpose"],
            }
        )
    return records
