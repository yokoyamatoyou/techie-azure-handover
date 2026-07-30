from __future__ import annotations

import argparse
import bz2
import io
import json
import math
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.request import Request, urlopen


DEFAULT_KNB_URL = "http://nlp.ist.i.kyoto-u.ac.jp/kuntt/KNBC_v1.0_090925_utf8.tar.bz2"
KNB_SOURCE_PAGE = "http://nlp.ist.i.kyoto-u.ac.jp/kuntt/#ga739fe2"
KNB_HELPER_PAGE = "https://masatohagiwara.net/nltk-japanese-corpus.html"
CARD_SCHEMA_VERSION = "reference_style_card_v1"

GPT_FREQUENT_TERMS = (
    "効く",
    "第一歩",
    "大切です",
    "重要です",
    "につながります",
    "しやすくなります",
    "見えてきます",
    "できるでしょう",
)

CONNECTOR_TERMS = (
    "ただし",
    "一方で",
    "また",
    "そのため",
    "だから",
    "とはいえ",
    "まず",
    "次に",
)

ABSTRACT_TERMS = (
    "重要",
    "大切",
    "効果",
    "改善",
    "活用",
    "課題",
    "価値",
    "支援",
)

FUNCTION_WORD_PROXY_TERMS = ("の", "に", "を", "が", "は", "と", "で", "も", "から", "まで")
PUNCTUATION_TERMS = ("、", "。", "「", "」", "・", "：", "；", "？", "！", "（", "）")
FIRST_PERSON_TERMS = ("私", "僕", "自分", "当社", "弊社", "当店")
THIRD_PERSON_TERMS = ("同社", "同店", "その会社", "この会社")
EXPLICIT_SUBJECT_PATTERNS = (
    "私は",
    "僕は",
    "自分は",
    "会社は",
    "サービスは",
    "この記事は",
    "KNBは",
)


def download_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def build_knb_style_card(archive_bytes: bytes, *, source_url: str = DEFAULT_KNB_URL) -> dict[str, Any]:
    corpus = parse_knb_archive(archive_bytes)
    sentences = corpus["sentences"]
    articles = corpus["articles"]
    article_sentence_groups = [[sentences[index] for index in indices] for indices in articles.values()]
    joined = "\n".join(sentences)
    sentence_lengths = [_compact_len(sentence) for sentence in sentences if _compact_len(sentence)]
    article_sentence_counts = [len(item) for item in articles.values() if item]

    sentence_p50 = _percentile(sentence_lengths, 50)
    sentence_p90 = _percentile(sentence_lengths, 90)
    sentence_variance = _variance(sentence_lengths)
    article_sentence_p50 = _percentile(article_sentence_counts, 50)

    compact_len = max(1, _compact_len(joined))
    gpt_counts = _term_counts(joined, GPT_FREQUENT_TERMS)
    connector_counts = _term_counts(joined, CONNECTOR_TERMS)
    abstract_counts = _term_counts(joined, ABSTRACT_TERMS)

    return {
        "schema_version": CARD_SCHEMA_VERSION,
        "adapter_hint": "knb_metrics_only_reference_band_v1",
        "source_policy": {
            "raw_text_stored": False,
            "prompt_examples_allowed": False,
            "named_creator_imitation_allowed": False,
            "urls_allowed_in_generation_prompt": False,
        },
        "extraction_notes": {
            "article_text_in_prompt": False,
            "copied_expressions_recorded": False,
            "named_creator_imitation": False,
            "route_created": False,
            "live_generation_executed": False,
            "raw_sentence_examples_saved": False,
            "archive_bytes_persisted": False,
        },
        "sample_set": {
            "name": "KNB Corpus metrics-only aggregate",
            "count": len(articles),
            "sentence_count": len(sentences),
            "source_url": source_url,
            "source_page": KNB_SOURCE_PAGE,
            "helper_page": KNB_HELPER_PAGE,
            "license_signal": "modified_BSD_or_3_clause_BSD_reported_by_source_pages",
            "topics": ["Kyoto tourism", "mobile phones", "sports", "gourmet"],
            "fit_note": "Japanese blog reference band only; not company-introduction prose imitation.",
        },
        "paragraph_rhythm": {
            "paragraph_count_p50": article_sentence_p50,
            "short_paragraph_ratio": _ratio([count <= 2 for count in article_sentence_counts]),
            "note": "KNB article sentence count is used as paragraph proxy; raw paragraphs are not preserved.",
        },
        "sentence_rhythm": {
            "chars_per_sentence_p50": sentence_p50,
            "chars_per_sentence_p90": sentence_p90,
            "sentence_length_variance": round(sentence_variance, 3),
            "sentence_length_variance_bucket": _variance_bucket(sentence_variance),
        },
        "heading_shape": {
            "heading_density_per_1000_chars": 0,
            "list_section_ratio": 0,
            "note": "KNB corpus extraction does not use headings as target prose.",
        },
        "viewpoint": {
            "explicit_subject_ratio": round(_count_patterns(joined, EXPLICIT_SUBJECT_PATTERNS) / max(1, len(sentences)), 4),
            "first_person_count": _count_patterns(joined, FIRST_PERSON_TERMS),
            "third_person_count": _count_patterns(joined, THIRD_PERSON_TERMS),
            "company_name_as_first_person_allowed": False,
        },
        "connectors": {
            "connector_counts": connector_counts,
            "connector_total": sum(connector_counts.values()),
            "connector_density_per_1000_chars": round(sum(connector_counts.values()) * 1000 / compact_len, 3),
        },
        "endings": _ending_metrics(sentences, groups=article_sentence_groups),
        "gpt_stock_phrases": {
            "stock_phrase_counts": gpt_counts,
            "stock_phrase_total": sum(gpt_counts.values()),
            "stock_phrase_density_per_1000_chars": round(sum(gpt_counts.values()) * 1000 / compact_len, 3),
            "policy": "metrics only; do not expand hard-ban list from this card.",
        },
        "abstract_terms": {
            "abstract_term_counts": abstract_counts,
            "abstract_term_total": sum(abstract_counts.values()),
            "abstract_terms_per_1000_chars": round(sum(abstract_counts.values()) * 1000 / compact_len, 3),
        },
        "function_word_proxy_profile": _function_word_proxy_profile(joined),
        "punctuation_profile": _punctuation_profile(joined),
        "raw_text_proof": {
            "raw_text_fields_present": False,
            "sentence_examples_present": False,
            "article_examples_present": False,
            "output_payload_contains_only_aggregates": True,
        },
    }


def parse_knb_archive(archive_bytes: bytes) -> dict[str, Any]:
    sentences: list[str] = []
    articles: dict[str, list[int]] = defaultdict(list)
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:bz2") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            name = member.name.replace("\\", "/")
            if "/corpus1/" not in name:
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            text = extracted.read().decode("utf-8", errors="replace")
            sentence = _sentence_from_knp_like_text(text)
            if not sentence:
                continue
            article_id = Path(name).parent.name
            articles[article_id].append(len(sentences))
            sentences.append(sentence)
    return {
        "sentences": sentences,
        "articles": dict(articles),
    }


def write_outputs(card: Mapping[str, Any], output_dir: Path, *, source_url: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    style_card_path = output_dir / "knb_metrics_style_card.json"
    report_path = output_dir / "knb_metrics_preflight_report.md"
    audit_path = output_dir / "knb_raw_text_safety_audit.json"

    style_card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "raw_text_saved": False,
        "raw_examples_saved": False,
        "prompt_payload_changed": False,
        "live_generation_executed": False,
        "route_created": False,
        "source_url": source_url,
        "style_card_path": str(style_card_path),
    }
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(_build_report(card, style_card_path, audit_path), encoding="utf-8")
    return {
        "style_card": style_card_path,
        "report": report_path,
        "audit": audit_path,
    }


def build_artifact_metrics_comparison(
    card: Mapping[str, Any],
    *,
    route_a_output: Path | None = None,
    shadow_root: Path | None = None,
) -> dict[str, Any]:
    route_a_metrics: dict[str, Any] = {}
    if route_a_output and route_a_output.exists():
        route_a_metrics = text_metrics(_article_text_from_generation_output(route_a_output.read_text(encoding="utf-8")))

    shadow_metrics: list[dict[str, Any]] = []
    if shadow_root and shadow_root.exists():
        for output_path in sorted(shadow_root.glob("*/variants/*/latest_generation_output.txt")):
            variant_id = output_path.parent.name
            text = _article_text_from_generation_output(output_path.read_text(encoding="utf-8"))
            item = text_metrics(text)
            item["variant_id"] = variant_id
            item["artifact_path"] = str(output_path)
            shadow_metrics.append(item)

    return {
        "comparison_version": "knb_route_a_shadow_metrics_comparison_v1",
        "policy": "metrics_only_no_raw_text_no_generation_no_adoption",
        "knb_reference": {
            "article_count": card.get("sample_set", {}).get("count"),
            "sentence_count": card.get("sample_set", {}).get("sentence_count"),
            "sentence_chars_p50": card.get("sentence_rhythm", {}).get("chars_per_sentence_p50"),
            "sentence_chars_p90": card.get("sentence_rhythm", {}).get("chars_per_sentence_p90"),
            "ending_max_run": card.get("endings", {}).get("max_same_ending_bucket_run_p90"),
            "gpt_stock_density_per_1000_chars": card.get("gpt_stock_phrases", {}).get(
                "stock_phrase_density_per_1000_chars"
            ),
            "connector_density_per_1000_chars": card.get("connectors", {}).get(
                "connector_density_per_1000_chars"
            ),
        },
        "route_a_metrics": route_a_metrics,
        "shadow_metrics": shadow_metrics,
        "raw_text_saved": False,
        "prompt_payload_changed": False,
        "live_generation_executed": False,
        "route_created": False,
    }


def write_comparison_outputs(comparison: Mapping[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "knb_route_a_shadow_metrics_comparison.json"
    report_path = output_dir / "knb_route_a_shadow_metrics_comparison.md"
    json_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(_build_comparison_report(comparison, json_path), encoding="utf-8")
    return {"comparison_json": json_path, "comparison_report": report_path}


def text_metrics(text: str) -> dict[str, Any]:
    body = str(text or "")
    sentences = _split_sentences(body)
    sentence_lengths = [_compact_len(sentence) for sentence in sentences if _compact_len(sentence)]
    compact_len = max(1, _compact_len(body))
    gpt_counts = _term_counts(body, GPT_FREQUENT_TERMS)
    connector_counts = _term_counts(body, CONNECTOR_TERMS)
    abstract_counts = _term_counts(body, ABSTRACT_TERMS)
    return {
        "char_count": _compact_len(body),
        "sentence_count": len(sentences),
        "chars_per_sentence_p50": _percentile(sentence_lengths, 50),
        "chars_per_sentence_p90": _percentile(sentence_lengths, 90),
        "heading_count": len(re.findall(r"(?m)^##\s+", body)),
        "paragraph_count": len([item for item in re.split(r"\n\s*\n", body.strip()) if item.strip()]),
        "gpt_frequent_term_total": sum(gpt_counts.values()),
        "gpt_frequent_density_per_1000_chars": round(sum(gpt_counts.values()) * 1000 / compact_len, 3),
        "connector_total": sum(connector_counts.values()),
        "connector_density_per_1000_chars": round(sum(connector_counts.values()) * 1000 / compact_len, 3),
        "abstract_terms_per_1000_chars": round(sum(abstract_counts.values()) * 1000 / compact_len, 3),
        "explicit_subject_count": _count_patterns(body, EXPLICIT_SUBJECT_PATTERNS),
        "first_person_count": _count_patterns(body, FIRST_PERSON_TERMS),
        "third_person_count": _count_patterns(body, THIRD_PERSON_TERMS),
        "ending_metrics": _ending_metrics(sentences),
        "function_word_proxy_profile": _function_word_proxy_profile(body),
        "punctuation_profile": _punctuation_profile(body),
    }


def _sentence_from_knp_like_text(text: str) -> str:
    surfaces: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line == "EOS" or line.startswith("#") or line.startswith("*") or line.startswith("+"):
            continue
        cells = line.split()
        if cells:
            surfaces.append(cells[0])
    return "".join(surfaces).strip()


def _build_report(card: Mapping[str, Any], style_card_path: Path, audit_path: Path) -> str:
    sample = dict(card.get("sample_set") or {})
    sentence = dict(card.get("sentence_rhythm") or {})
    endings = dict(card.get("endings") or {})
    stock = dict(card.get("gpt_stock_phrases") or {})
    viewpoint = dict(card.get("viewpoint") or {})
    return "\n".join(
        [
            "# KNB metrics-only preflight report",
            "",
            "## Scope",
            "",
            "- raw text saved: no",
            "- raw examples saved: no",
            "- prompt payload changed: no",
            "- live generation: no",
            "- new route: no",
            "- Route A change: no",
            "- adoption: no",
            "",
            "## Source",
            "",
            f"- corpus: {sample.get('name')}",
            f"- source url: {sample.get('source_url')}",
            f"- source page: {sample.get('source_page')}",
            f"- helper page: {sample.get('helper_page')}",
            f"- license signal: {sample.get('license_signal')}",
            f"- article count: {sample.get('count')}",
            f"- sentence count: {sample.get('sentence_count')}",
            "",
            "## Aggregate Metrics",
            "",
            f"- sentence chars p50: {sentence.get('chars_per_sentence_p50')}",
            f"- sentence chars p90: {sentence.get('chars_per_sentence_p90')}",
            f"- sentence variance bucket: {sentence.get('sentence_length_variance_bucket')}",
            f"- ending max same bucket run: {endings.get('max_same_ending_bucket_run_p90')}",
            f"- explicit subject ratio: {viewpoint.get('explicit_subject_ratio')}",
            f"- GPT stock phrase density per 1000 chars: {stock.get('stock_phrase_density_per_1000_chars')}",
            "",
            "## Artifacts",
            "",
            f"- style card: `{style_card_path}`",
            f"- safety audit: `{audit_path}`",
            "",
            "## Decision",
            "",
            "This report is a metrics-only reference band. It does not authorize live generation, route implementation, prompt examples, or adoption.",
            "",
        ]
    )


def _build_comparison_report(comparison: Mapping[str, Any], json_path: Path) -> str:
    knb = dict(comparison.get("knb_reference") or {})
    route_a = dict(comparison.get("route_a_metrics") or {})
    shadows = list(comparison.get("shadow_metrics") or [])
    ranked = sorted(
        shadows,
        key=lambda item: (
            abs(float(item.get("chars_per_sentence_p50", 0) or 0) - float(knb.get("sentence_chars_p50", 0) or 0)),
            int(item.get("gpt_frequent_term_total", 0) or 0),
            int(item.get("ending_metrics", {}).get("max_same_ending_bucket_run_p90", 999) or 999),
        ),
    )
    lines = [
        "# KNB / Route A / shadow metrics comparison",
        "",
        "## Scope",
        "",
        "- raw text saved: no",
        "- prompt payload changed: no",
        "- live generation: no",
        "- new route: no",
        "- adoption: no",
        "",
        "## Reference Band",
        "",
        f"- KNB article count: {knb.get('article_count')}",
        f"- KNB sentence count: {knb.get('sentence_count')}",
        f"- KNB sentence chars p50: {knb.get('sentence_chars_p50')}",
        f"- KNB sentence chars p90: {knb.get('sentence_chars_p90')}",
        f"- KNB GPT stock density / 1000 chars: {knb.get('gpt_stock_density_per_1000_chars')}",
        "",
        "## Route A Saved Output",
        "",
        f"- chars: {route_a.get('char_count')}",
        f"- sentence chars p50: {route_a.get('chars_per_sentence_p50')}",
        f"- sentence chars p90: {route_a.get('chars_per_sentence_p90')}",
        f"- GPT frequent total: {route_a.get('gpt_frequent_term_total')}",
        f"- ending max run: {route_a.get('ending_metrics', {}).get('max_same_ending_bucket_run_p90') if route_a else ''}",
        "",
        "## Shadow Artifacts",
        "",
    ]
    for item in ranked[:12]:
        lines.append(
            "- {variant}: chars={chars} sentence_p50={p50} gpt_total={gpt} ending_max_run={run}".format(
                variant=item.get("variant_id"),
                chars=item.get("char_count"),
                p50=item.get("chars_per_sentence_p50"),
                gpt=item.get("gpt_frequent_term_total"),
                run=item.get("ending_metrics", {}).get("max_same_ending_bucket_run_p90"),
            )
        )
    lines.extend(
        [
            "",
            "## Artifact",
            "",
            f"- comparison json: `{json_path}`",
            "",
            "## Decision",
            "",
            "This comparison is preflight-only. It does not select a clean candidate or authorize live generation.",
            "",
        ]
    )
    return "\n".join(lines)


def _ending_metrics(sentences: Iterable[str], *, groups: Iterable[Iterable[str]] | None = None) -> dict[str, Any]:
    sentence_list = [sentence for sentence in sentences if sentence]
    buckets = [_ending_bucket(sentence) for sentence in sentence_list]
    counts = Counter(buckets)
    grouped_sentences = list(groups) if groups is not None else [sentence_list]
    grouped_max_runs = [_max_ending_run([_ending_bucket(sentence) for sentence in group if sentence]) for group in grouped_sentences]
    return {
        "sentence_ending_distribution": dict(counts),
        "max_same_ending_bucket_run_p90": _percentile([int(item) for item in grouped_max_runs], 90),
        "max_same_ending_bucket_run_max": max(grouped_max_runs) if grouped_max_runs else 0,
        "soft_assertive_ending_ratio": round(counts.get("soft_assertive", 0) / max(1, len(buckets)), 4),
    }


def _max_ending_run(buckets: Iterable[str]) -> int:
    max_run = 0
    current = ""
    run = 0
    for bucket in buckets:
        if bucket == current:
            run += 1
        else:
            current = bucket
            run = 1
        max_run = max(max_run, run)
    return max_run


def _article_text_from_generation_output(text: str) -> str:
    lines = str(text or "").splitlines()
    start = 0
    for index, line in enumerate(lines):
        if line.startswith("proposition_low_info_ratio:"):
            start = index + 1
            break
    trimmed = lines[start:]
    while trimmed and not trimmed[0].strip():
        trimmed.pop(0)
    for index, line in enumerate(trimmed):
        if line.strip() == "## 参考情報":
            trimmed = trimmed[:index]
            break
    return "\n".join(trimmed).strip()


def _split_sentences(text: str) -> list[str]:
    return [item for item in re.split(r"(?<=[。！？!?])\s*", str(text or "")) if item.strip()]


def _ending_bucket(sentence: str) -> str:
    stripped = sentence.strip()
    if stripped.endswith(("です。", "ます。", "でした。", "ました。")):
        return "polite"
    if stripped.endswith(("だ。", "である。", "だった。")):
        return "assertive"
    if stripped.endswith(("ない。", "ません。")):
        return "negative"
    if stripped.endswith(("たい。", "よう。", "そう。")):
        return "soft_assertive"
    if stripped.endswith(("？", "?")):
        return "question"
    return "other"


def _function_word_proxy_profile(text: str) -> dict[str, Any]:
    compact_len = max(1, _compact_len(text))
    counts = _term_counts(text, FUNCTION_WORD_PROXY_TERMS)
    total = sum(counts.values())
    return {
        "method": "surface_substring_proxy_no_morphology",
        "counts": counts,
        "total": total,
        "density_per_1000_chars": round(total * 1000 / compact_len, 3),
    }


def _punctuation_profile(text: str) -> dict[str, Any]:
    compact_len = max(1, _compact_len(text))
    counts = _term_counts(text, PUNCTUATION_TERMS)
    comma_count = counts.get("、", 0)
    period_count = counts.get("。", 0)
    return {
        "counts": counts,
        "total": sum(counts.values()),
        "comma_count": comma_count,
        "period_count": period_count,
        "comma_per_period": round(comma_count / max(1, period_count), 3),
        "density_per_1000_chars": round(sum(counts.values()) * 1000 / compact_len, 3),
    }


def _term_counts(text: str, terms: Iterable[str]) -> dict[str, int]:
    return {term: str(text or "").count(term) for term in terms}


def _count_patterns(text: str, terms: Iterable[str]) -> int:
    return sum(str(text or "").count(term) for term in terms)


def _compact_len(text: str) -> int:
    return len(re.sub(r"\s+", "", str(text or "")))


def _percentile(values: list[int], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile / 100
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(ordered[int(index)])
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower), 3)


def _variance(values: list[int]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def _variance_bucket(value: float) -> str:
    if value < 80:
        return "low"
    if value < 220:
        return "mid"
    return "high"


def _ratio(flags: Iterable[bool]) -> float:
    items = list(flags)
    if not items:
        return 0.0
    return round(sum(1 for item in items if item) / len(items), 4)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract metrics-only style card from KNB Corpus without saving raw text.")
    parser.add_argument("--url", default=DEFAULT_KNB_URL)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--route-a-output", default="")
    parser.add_argument("--shadow-root", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    archive_bytes = download_bytes(args.url)
    card = build_knb_style_card(archive_bytes, source_url=args.url)
    outputs = write_outputs(card, Path(args.output_dir), source_url=args.url)
    if args.route_a_output or args.shadow_root:
        comparison = build_artifact_metrics_comparison(
            card,
            route_a_output=Path(args.route_a_output) if args.route_a_output else None,
            shadow_root=Path(args.shadow_root) if args.shadow_root else None,
        )
        outputs.update(write_comparison_outputs(comparison, Path(args.output_dir)))
    result = {
        "status": "ok",
        "raw_text_saved": False,
        "prompt_payload_changed": False,
        "live_generation_executed": False,
        "route_created": False,
        "outputs": {key: str(value) for key, value in outputs.items()},
        "article_count": card["sample_set"]["count"],
        "sentence_count": card["sample_set"]["sentence_count"],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"style_card={outputs['style_card']}")
        print(f"report={outputs['report']}")
        print(f"audit={outputs['audit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
