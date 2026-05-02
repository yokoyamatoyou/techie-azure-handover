from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

from config import AppConfig, DATA_DIR


_DEFAULT_STOPWORDS: frozenset[str] = frozenset(
    {
        "",
        " ",
        "こと",
        "もの",
        "ため",
        "よう",
        "これ",
        "それ",
        "あれ",
        "ここ",
        "そこ",
        "どこ",
        "です",
        "ます",
        "でした",
        "ました",
        "する",
        "した",
        "して",
        "いる",
        "ある",
        "なる",
        "できる",
        "方法",
        "ポイント",
        "ベスト",
        "プラクティス",
        "解説",
        "紹介",
        "情報",
        "記事",
        "一覧",
        "まとめ",
        "最新",
        "おすすめ",
        "キーワード",
        "とは",
        "について",
        "向け",
        "場合",
        "から",
        "まで",
        "より",
        "ほか",
        "など",
        "この",
        "その",
        "どの",
        "各",
        "的",
    }
)

_DOMAIN_STOPWORDS: frozenset[str] = frozenset(
    {
        "ai",
        "llm",
        "chatgpt",
        "saas",
        "b2b",
        "b2c",
        "生成ai",
        "検索",
        "可視性",
        "露出",
        "ブランド",
        "サービス",
        "ソフト",
        "ツール",
        "ソリューション",
        "会社",
        "企業",
        "www",
        "com",
        "co",
        "jp",
        "net",
        "org",
        "company",
        "contact",
        "information",
        "news",
        "blog",
        "home",
        "top",
    }
)

_PHRASE_ALIASES: dict[str, str] = {
    "よくある質問": "FAQ",
    "faq": "FAQ",
    "比較表": "比較表",
    "比較一覧": "比較表",
    "比較": "比較",
    "料金表": "料金",
    "料金一覧": "料金",
    "価格一覧": "料金",
    "価格表": "料金",
    "料金": "料金",
    "価格": "料金",
    "費用": "料金",
    "相場": "料金",
    "導入事例": "導入事例",
    "成功事例": "導入事例",
    "事例": "導入事例",
    "実績": "実績",
    "口コミ": "口コミ",
    "評判": "評判",
    "レビュー": "レビュー",
    "機能比較": "機能比較",
    "機能": "機能",
    "選び方": "選定基準",
    "選定基準": "選定基準",
    "導入フロー": "導入フロー",
    "導入手順": "導入フロー",
    "手順": "手順",
    "使い方": "使い方",
    "やり方": "使い方",
    "注意点": "注意点",
    "メリット": "メリット",
    "デメリット": "デメリット",
    "セキュリティ": "セキュリティ",
    "信頼性": "信頼性",
    "サポート": "サポート",
    "導入条件": "導入条件",
    "条件": "導入条件",
    "実例": "導入事例",
    "テンプレート": "テンプレート",
    "チェックリスト": "チェックリスト",
    "事例紹介": "導入事例",
    "比較検討": "比較",
}

_ALIAS_KEYS = sorted(_PHRASE_ALIASES.keys(), key=len, reverse=True)
_ASCII_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+._-]{1,24}")
_KATAKANA_TOKEN_RE = re.compile(r"[ァ-ヶー]{2,24}")
_KANJI_TOKEN_RE = re.compile(r"[一-龯]{2,12}")
_SPLIT_RE = re.compile(r"[\s\u3000/／|｜:：;；,，。.!！?？()\[\]{}（）「」『』【】<>＜＞\n\r\t]+")
_SEGMENT_SPLIT_RE = re.compile(r"[。.!！?？\n\r]+")


def _normalize_token(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    if not text:
        return ""
    text = text.strip("・/／,，。.!！?？()（）[]{}「」『』\"' ")
    return text


def _normalize_lookup(value: Any) -> str:
    return _normalize_token(value).lower()


def _load_word_list(path: Path) -> set[str]:
    if not path.exists():
        return set()
    words: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        token = _normalize_lookup(line)
        if token and not token.startswith("#"):
            words.add(token)
    return words


def _load_json_words(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    candidates: list[Any] = []
    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, dict):
        for value in raw.values():
            if isinstance(value, list):
                candidates.extend(value)
    words: set[str] = set()
    for item in candidates:
        token = _normalize_lookup(item)
        if token:
            words.add(token)
    return words


def _extract_domain_parts(domain: str) -> list[str]:
    parts: list[str] = []
    host = _normalize_lookup(domain)
    if not host:
        return parts
    for piece in re.split(r"[\.:/\-_]+", host):
        if piece and len(piece) >= 2 and piece not in {"www", "com", "co", "jp", "net", "org"}:
            parts.append(piece)
    return parts


def build_topic_stopwords(config: AppConfig, extra_terms: list[str] | None = None) -> set[str]:
    words = set(_DEFAULT_STOPWORDS)
    words.update(_DOMAIN_STOPWORDS)
    words.update(_load_word_list(DATA_DIR / "stopwords_ja.txt"))
    words.update(_load_json_words(DATA_DIR / "exclude_words_preset.json"))

    dynamic_terms: list[str] = list(extra_terms or [])
    dynamic_terms.extend(config.brand_terms or [])
    dynamic_terms.extend(config.competitor_terms or [])
    dynamic_terms.extend(_extract_domain_parts(str(config.target_domain or "")))
    for term in dynamic_terms:
        token = _normalize_lookup(term)
        if not token:
            continue
        words.add(token)
        if len(token) >= 2:
            words.add(token.replace(" ", ""))
    return words


def _canonicalize_token(token: str) -> str:
    normalized = _normalize_token(token)
    if not normalized:
        return ""
    alias = _PHRASE_ALIASES.get(normalized.lower())
    if alias:
        return alias
    return normalized


def _extract_phrase_hits(text: str) -> list[str]:
    lowered = _normalize_lookup(text)
    if not lowered:
        return []
    hits: list[str] = []
    seen: set[str] = set()
    for alias in _ALIAS_KEYS:
        if alias in lowered:
            label = _PHRASE_ALIASES[alias]
            if label not in seen:
                hits.append(label)
                seen.add(label)
    return hits


def extract_topic_tokens(text: str, stopwords: set[str], min_word_length: int = 2) -> list[str]:
    normalized = _normalize_token(text)
    if not normalized:
        return []

    tokens: list[str] = []
    seen: set[str] = set()
    for hit in _extract_phrase_hits(normalized):
        if hit not in seen:
            tokens.append(hit)
            seen.add(hit)

    chunks = [chunk for chunk in _SPLIT_RE.split(normalized) if chunk]
    for chunk in chunks:
        for match in _ASCII_TOKEN_RE.findall(chunk):
            token = _canonicalize_token(match)
            lookup = _normalize_lookup(token)
            if any(marker in token for marker in {".", "/", "_", "-"}):
                continue
            if token.lower() == token:
                continue
            if len(token) < min_word_length or lookup in stopwords or lookup.isdigit():
                continue
            if token not in seen:
                tokens.append(token)
                seen.add(token)
        for match in _KATAKANA_TOKEN_RE.findall(chunk):
            token = _canonicalize_token(match)
            lookup = _normalize_lookup(token)
            if len(token) < min_word_length or lookup in stopwords:
                continue
            if token not in seen:
                tokens.append(token)
                seen.add(token)
        for match in _KANJI_TOKEN_RE.findall(chunk):
            token = _canonicalize_token(match)
            lookup = _normalize_lookup(token)
            if len(token) < min_word_length or lookup in stopwords:
                continue
            if token not in seen:
                tokens.append(token)
                seen.add(token)
    return tokens


def _rank_topics(texts: list[str], stopwords: set[str], max_terms: int, max_doc_freq_ratio: float) -> list[str]:
    docs: list[list[str]] = []
    for text in texts:
        tokens = extract_topic_tokens(text, stopwords)
        if tokens:
            docs.append(tokens)

    if not docs:
        return []

    tf_counts: Counter[str] = Counter()
    df_counts: Counter[str] = Counter()
    cooccurrence_counts: Counter[str] = Counter()
    for tokens in docs:
        unique_tokens = list(dict.fromkeys(tokens))
        tf_counts.update(tokens)
        df_counts.update(unique_tokens)
        co_weight = max(0, len(unique_tokens) - 1)
        for token in unique_tokens:
            cooccurrence_counts[token] += co_weight

    max_doc_freq = max(1, int(len(docs) * max_doc_freq_ratio))
    ranked = sorted(
        (
            token
            for token in tf_counts
            if df_counts[token] <= max_doc_freq or len(docs) < 4
        ),
        key=lambda token: (
            -(tf_counts[token] * 3 + df_counts[token] * 2 + cooccurrence_counts[token]),
            -df_counts[token],
            -len(token),
            token,
        ),
    )
    return ranked[:max_terms]


def _get_row_payload(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("output_json")
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(str(raw))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _get_row_answer_text(row: dict[str, Any]) -> str:
    answer_text = _normalize_token(row.get("answer_text"))
    if answer_text:
        return answer_text
    payload = _get_row_payload(row)
    return _normalize_token(payload.get("answer_text") or payload.get("answer_snapshot"))


def _collect_context_terms(rows: list[dict[str, Any]], config: AppConfig) -> list[str]:
    terms: list[str] = []
    for row in rows:
        payload = _get_row_payload(row)
        context = payload.get("analysis_context") or {}
        for item in context.get("brand_terms") or []:
            terms.append(str(item))
        for item in context.get("competitor_terms") or []:
            terms.append(str(item))
        terms.extend(_extract_domain_parts(str(context.get("target_domain") or "")))
    terms.extend(config.brand_terms or [])
    terms.extend(config.competitor_terms or [])
    return terms


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        token = _normalize_token(item)
        if token and token not in seen:
            ordered.append(token)
            seen.add(token)
    return ordered


def build_page_gap_topic_hints(page_gap: dict[str, Any] | None) -> list[str]:
    label = _normalize_token((page_gap or {}).get("page_type_label"))
    next_step = _normalize_token((page_gap or {}).get("next_step"))
    hints: list[str] = []
    mapping = [
        ("比較", "比較"),
        ("料金", "料金"),
        ("FAQ", "FAQ"),
        ("事例", "導入事例"),
        ("地域", "地域対応"),
        ("信頼", "信頼性"),
        ("解説", "使い方"),
        ("論点", "選定基準"),
    ]
    for needle, hint in mapping:
        if needle in label or needle in next_step:
            hints.append(hint)
    return _dedupe(hints)


def build_topic_signal_summary(
    rows: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    config: AppConfig,
    *,
    page_gap: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not bool(getattr(config, "enable_topic_signals", True)):
        return {
            "enabled": False,
            "question_topics": [],
            "answer_topics": [],
            "competitive_topics": [],
            "self_topics": [],
            "candidate_topics": [],
            "missing_topics": [],
            "action_topics": [],
        }

    stopwords = build_topic_stopwords(config, _collect_context_terms(rows, config))
    max_terms = max(3, int(getattr(config, "topic_signal_max_terms", 5) or 5))
    max_doc_freq_ratio = float(getattr(config, "topic_signal_max_doc_freq_ratio", 0.85) or 0.85)

    question_texts = [str(row.get("keyword_raw") or row.get("keyword_norm") or "") for row in rows]
    answer_texts = [_get_row_answer_text(row) for row in rows]

    competitive_texts = [
        str(item.get("title") or "")
        for item in evidence_items
        if str(item.get("status") or "") == "cited" and str(item.get("owner_bucket") or "") in {"external", "competitor"}
    ]
    self_texts = [
        str(item.get("title") or "")
        for item in evidence_items
        if str(item.get("status") or "") == "cited" and str(item.get("owner_bucket") or "") == "self"
    ]
    candidate_texts = [
        str(item.get("title") or "")
        for item in evidence_items
        if str(item.get("status") or "") == "searched_only" and str(item.get("owner_bucket") or "") == "self"
    ]

    question_topics = _rank_topics(question_texts, stopwords, max_terms=max_terms, max_doc_freq_ratio=max_doc_freq_ratio)
    answer_topics = _rank_topics(answer_texts, stopwords, max_terms=max_terms, max_doc_freq_ratio=max_doc_freq_ratio)
    competitive_topics = _rank_topics(
        competitive_texts,
        stopwords,
        max_terms=max_terms,
        max_doc_freq_ratio=max_doc_freq_ratio,
    )
    self_topics = _rank_topics(self_texts, stopwords, max_terms=max_terms, max_doc_freq_ratio=max_doc_freq_ratio)
    candidate_topics = _rank_topics(candidate_texts, stopwords, max_terms=max_terms, max_doc_freq_ratio=max_doc_freq_ratio)

    protected_topics = {topic for topic in self_topics[:3]} | {topic for topic in candidate_topics[:2]}
    missing_topics = [topic for topic in competitive_topics if topic not in protected_topics][:max_terms]
    if not missing_topics:
        missing_topics = [topic for topic in answer_topics if topic not in protected_topics][:max_terms]

    action_topics = _dedupe(build_page_gap_topic_hints(page_gap) + candidate_topics + missing_topics + question_topics)[:max_terms]

    return {
        "enabled": True,
        "question_topics": question_topics,
        "answer_topics": answer_topics,
        "competitive_topics": competitive_topics,
        "self_topics": self_topics,
        "candidate_topics": candidate_topics,
        "missing_topics": missing_topics,
        "action_topics": action_topics,
    }


def build_topic_network_summary(
    rows: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    config: AppConfig,
) -> dict[str, Any]:
    if not bool(getattr(config, "enable_topic_signals", True)):
        return {
            "enabled": False,
            "top_nodes": [],
            "top_edges": [],
            "segment_count": 0,
            "summary": "topic signals が無効です。",
        }

    stopwords = build_topic_stopwords(config, _collect_context_terms(rows, config))
    max_terms = max(4, int(getattr(config, "topic_signal_max_terms", 5) or 5))
    question_texts = [str(row.get("keyword_raw") or row.get("keyword_norm") or "") for row in rows]
    answer_texts = [_get_row_answer_text(row) for row in rows]
    cited_titles = [
        str(item.get("title") or item.get("url") or "")
        for item in evidence_items
        if str(item.get("status") or "") == "cited"
    ]
    searched_titles = [
        str(item.get("title") or item.get("url") or "")
        for item in evidence_items
        if str(item.get("status") or "") == "searched_only"
    ]

    segments: list[list[str]] = []
    for text in question_texts + answer_texts + cited_titles + searched_titles:
        normalized = _normalize_token(text)
        if not normalized:
            continue
        for piece in _SEGMENT_SPLIT_RE.split(normalized):
            token_list = extract_topic_tokens(piece, stopwords)
            unique_tokens = list(dict.fromkeys(token_list))
            if len(unique_tokens) >= 2:
                segments.append(unique_tokens[:8])

    if not segments:
        return {
            "enabled": True,
            "top_nodes": [],
            "top_edges": [],
            "segment_count": 0,
            "summary": "共起を作れるだけの論点候補がまだありません。",
        }

    node_counts: Counter[str] = Counter()
    edge_counts: Counter[tuple[str, str]] = Counter()
    for tokens in segments:
        node_counts.update(tokens)
        for source, target in combinations(sorted(set(tokens)), 2):
            edge_counts[(source, target)] += 1

    top_nodes = [
        {"label": label, "weight": weight}
        for label, weight in sorted(
            node_counts.items(),
            key=lambda item: (-item[1], -len(item[0]), item[0]),
        )[: max_terms + 2]
    ]
    visible_node_labels = {item["label"] for item in top_nodes}
    top_edges = [
        {"source": source, "target": target, "weight": weight}
        for (source, target), weight in sorted(
            edge_counts.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )
        if source in visible_node_labels and target in visible_node_labels
    ][: max_terms + 1]

    if top_edges:
        summary = " / ".join(
            f"{item['source']} x {item['target']} ({item['weight']})"
            for item in top_edges[:3]
        )
    else:
        summary = " / ".join(item["label"] for item in top_nodes[:4]) or "論点候補なし"

    return {
        "enabled": True,
        "top_nodes": top_nodes,
        "top_edges": top_edges,
        "segment_count": len(segments),
        "summary": summary,
    }
