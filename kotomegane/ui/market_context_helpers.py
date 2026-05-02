from __future__ import annotations

import re
import unicodedata
from typing import Any

_TERM_SPLIT_RE = re.compile(r"[\n\r,，/／|｜;；]+")
_REGION_ENTITY_RE = re.compile(r"([一-龯ぁ-んァ-ヶー]{2,8}(?:都|道|府|県|市|区|町|村))")

_CATEGORY_LABELS = {
    "region": "地域",
    "industry": "業界",
    "use_case": "用途",
    "other": "その他",
}

_RULES: dict[str, tuple[tuple[str, str], ...]] = {
    "region": (
        ("全国", "全国"),
        ("地域密着", "地域密着"),
        ("ローカル", "地域密着"),
        ("首都圏", "首都圏"),
        ("関東", "関東"),
        ("関西", "関西"),
        ("東海", "東海"),
        ("中部", "中部"),
        ("東北", "東北"),
        ("北海道", "北海道"),
        ("九州", "九州"),
        ("沖縄", "沖縄"),
        ("東京", "東京"),
        ("都内", "東京"),
        ("大阪", "大阪"),
        ("名古屋", "名古屋"),
        ("福岡", "福岡"),
        ("札幌", "札幌"),
        ("仙台", "仙台"),
        ("京都", "京都"),
        ("神戸", "神戸"),
        ("横浜", "横浜"),
    ),
    "industry": (
        ("製造", "製造業"),
        ("工場", "製造業"),
        ("建設", "建設業"),
        ("不動産", "不動産"),
        ("医療", "医療"),
        ("病院", "医療"),
        ("クリニック", "医療"),
        ("歯科", "歯科"),
        ("美容", "美容"),
        ("士業", "士業"),
        ("弁護士", "士業"),
        ("税理士", "士業"),
        ("社労士", "士業"),
        ("会計", "士業"),
        ("IT", "IT"),
        ("saas", "SaaS"),
        ("人材", "人材"),
        ("採用", "人材"),
        ("教育", "教育"),
        ("学校", "教育"),
        ("介護", "介護"),
        ("物流", "物流"),
        ("飲食", "飲食"),
        ("ホテル", "観光"),
        ("観光", "観光"),
        ("小売", "小売"),
        ("ec", "EC"),
        ("通販", "EC"),
    ),
    "use_case": (
        ("比較", "比較検討"),
        ("違い", "比較検討"),
        ("vs", "比較検討"),
        ("versus", "比較検討"),
        ("料金", "料金訴求"),
        ("価格", "料金訴求"),
        ("費用", "料金訴求"),
        ("相場", "料金訴求"),
        ("導入事例", "導入事例"),
        ("事例", "導入事例"),
        ("実績", "導入事例"),
        ("faq", "FAQ"),
        ("よくある質問", "FAQ"),
        ("質問", "FAQ"),
        ("使い方", "使い方"),
        ("手順", "使い方"),
        ("導入方法", "使い方"),
        ("評判", "評判"),
        ("口コミ", "評判"),
        ("レビュー", "評判"),
        ("問い合わせ", "問い合わせ獲得"),
        ("資料請求", "問い合わせ獲得"),
        ("予約", "予約獲得"),
        ("集客", "集客"),
        ("採用", "採用強化"),
        ("業務効率", "業務効率化"),
        ("効率化", "業務効率化"),
        ("セキュリティ", "信頼性"),
        ("信頼", "信頼性"),
        ("導入支援", "導入支援"),
        ("サポート", "サポート"),
    ),
}


def _normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def _normalize_lookup(value: Any) -> str:
    return _normalize_text(value).lower()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        value = _normalize_text(item)
        if value and value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def split_market_context_terms(value: Any) -> list[str]:
    if isinstance(value, list):
        raw_items = [str(item or "") for item in value]
    else:
        raw_items = _TERM_SPLIT_RE.split(_normalize_text(value))
    return _dedupe([item for item in raw_items if _normalize_text(item)])


def merge_market_context_terms(existing: list[str], additions: list[str]) -> list[str]:
    return _dedupe([*existing, *additions])


def classify_market_context_terms(terms: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"region": [], "industry": [], "use_case": [], "other": []}
    for term in split_market_context_terms(terms):
        lookup = _normalize_lookup(term)
        matched_category = ""
        for category in ("region", "industry", "use_case"):
            for needle, _ in _RULES[category]:
                if needle.lower() in lookup:
                    matched_category = category
                    break
            if matched_category:
                break
        grouped[matched_category or "other"].append(term)
    return {key: _dedupe(values) for key, values in grouped.items()}


def infer_market_context_candidates(keywords: list[str]) -> dict[str, list[str]]:
    text = " ".join(_normalize_text(keyword) for keyword in keywords if _normalize_text(keyword))
    lookup = text.lower()
    grouped: dict[str, list[str]] = {"region": [], "industry": [], "use_case": []}

    for region in _REGION_ENTITY_RE.findall(text):
        grouped["region"].append(region)

    for category in ("region", "industry", "use_case"):
        for needle, label in _RULES[category]:
            if needle.lower() in lookup:
                grouped[category].append(label)

    return {key: _dedupe(values) for key, values in grouped.items()}


def market_context_category_label(category: str) -> str:
    return _CATEGORY_LABELS.get(str(category or ""), "その他")
