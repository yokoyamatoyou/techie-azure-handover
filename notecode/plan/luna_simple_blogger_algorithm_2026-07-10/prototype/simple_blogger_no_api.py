from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROLE_ID = "company_side_blogger_v1"
ROLE = (
    "この会社の仕事に日々触れているブロガーとして、検索やサムネイルから偶然来た、"
    "まだ関心の薄い読者へ書く。会社を外から評さず、sourceにある具体的な場面・名詞・"
    "動作から興味を立ち上げ、事実を足さない。"
)
STAGE1 = (
    "compact source ledgerだけを根拠に、H1を1つと自然なH2を持つ全文を書く。"
    "導入はsourceにある場面・物・動作・違和感から始める。自社本人の声を保ち、"
    "私たち/当社を機械的に反復せず、抽象的な読者誘導よりsource固有の名詞と動詞を優先する。"
)
STAGE2 = (
    "同じ書き手として全文を読み直す。低関心の読者の興味、自社本人の声、省略主語の一意性、"
    "source固有の場面・名詞・動作が定型的なメタ文に置き換わっていないかだけを見る。"
    "失敗した段落と隣接1文までを直し、他は保つ。事実・H1/H2順・本文floorを変えず、"
    "問題がなければ変更しない全文を返す。"
)
PHRASES = ("判断軸", "判断材料", "はじめの一歩", "第一歩", "効く", "確認", "整理", "説明", "判断")
NARRATORS = ("私たち", "当社", "弊社", "わたしたち")
COMPETITORS = ("お客様", "顧客", "利用者", "行政", "自治体", "担当者", "同社")
ACTIONS = ("行いました", "進めます", "確認します", "対応します", "提供します", "実施します", "扱います", "支援します", "案内します", "取り組みます")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_contract() -> dict:
    p1 = f"role_id: {ROLE_ID}\n{ROLE}\n\n{STAGE1}"
    p2 = f"role_id: {ROLE_ID}\n{ROLE}\n\n{STAGE2}"
    return {
        "role_id": ROLE_ID,
        "arm_a_fixed_calls": 1,
        "arm_b_fixed_calls": 2,
        "raw_full_source_handoff": False,
        "stage_1": {"prompt": p1, "chars": len(p1), "sha256": digest(p1)},
        "stage_2": {"prompt": p2, "chars": len(p2), "sha256": digest(p2)},
    }


def body(markdown: str) -> str:
    return "\n".join(line for line in markdown.splitlines() if not line.strip().startswith("#")).strip()


def split_sentences(text: str) -> list[str]:
    return [x for x in re.split(r"(?<=[。！？])", re.sub(r"\s+", "", text)) if x]


def ngrams(text: str, n: int) -> Counter:
    text = re.sub(r"[\s#`*_\-—・、。！？：:（）()\[\]「」『』]+", "", text)
    return Counter(text[i : i + n] for i in range(max(0, len(text) - n + 1)))


def overlap(article: str, source: str) -> dict:
    source_set = set(ngrams(source, 3))

    def ratio(text: str) -> float:
        article_set = set(ngrams(text, 3))
        return round(len(article_set & source_set) / len(article_set), 4) if article_set else 0.0

    return {
        "label": "character_trigram_proxy_not_semantic_grounding",
        "body_ratio": ratio(article),
        "opening_ratio": ratio("".join(split_sentences(article)[:3])),
        "unsupported_claim_status": "not_evaluable_statically",
    }


def zero_candidates(text: str) -> list[dict]:
    found, previous = [], ""
    for index, sentence in enumerate(split_sentences(text)):
        if any(action in sentence for action in ACTIONS) and not any(subject in sentence for subject in NARRATORS + COMPETITORS):
            found.append({
                "sentence_index": index,
                "text": sentence[:180],
                "competing_entity_in_previous_sentence": any(word in previous for word in COMPETITORS),
                "status": "manual_review_candidate",
            })
        previous = sentence
    return found


def stats(values: list[int]) -> dict:
    return {
        "mean": round(statistics.mean(values), 2) if values else 0,
        "median": round(statistics.median(values), 2) if values else 0,
        "maximum": max(values, default=0),
        "population_stdev": round(statistics.pstdev(values), 2) if len(values) > 1 else 0,
    }


def analyze(markdown: str, source: str, floor: int) -> dict:
    article = body(markdown)
    compact = re.sub(r"\s+", "", article)
    sentences = split_sentences(article)
    paragraphs = [re.sub(r"\s+", "", x) for x in re.split(r"\n\s*\n", article) if x.strip()]
    phrase_counts = {phrase: article.count(phrase) for phrase in PHRASES}
    narrator_counts = {word: article.count(word) for word in NARRATORS}
    meta = [sentence for sentence in sentences if any(phrase in sentence for phrase in PHRASES)]
    return {
        "body_chars": len(compact), "body_floor": floor, "body_floor_reached": len(compact) >= floor,
        "h1_count": len(re.findall(r"(?m)^#(?!#)\s+", markdown)),
        "h2_count": len(re.findall(r"(?m)^##(?!#)\s+", markdown)),
        "paragraph_count": len(paragraphs), "sentence_count": len(sentences),
        "sentence_chars": stats([len(x) for x in sentences]),
        "paragraph_chars": stats([len(x) for x in paragraphs]),
        "phrase_counts": phrase_counts,
        "meta_sentence_count": len(meta),
        "meta_sentence_ratio": round(len(meta) / len(sentences), 4) if sentences else 0.0,
        "narrator_counts": narrator_counts, "narrator_total": sum(narrator_counts.values()),
        "zero_anaphora_candidates": zero_candidates(article),
        "source_overlap": overlap(article, source),
    }


def repeated(all_articles: dict[str, str]) -> list[dict]:
    owners, totals = defaultdict(set), Counter()
    for case_id, text in all_articles.items():
        for gram, count in ngrams(body(text), 5).items():
            owners[gram].add(case_id); totals[gram] += count
    rows = [{"ngram": g, "article_count": len(owners[g]), "total_count": totals[g]} for g in owners if len(owners[g]) >= 2]
    return sorted(rows, key=lambda x: (-x["article_count"], -x["total_count"], x["ngram"]))[:30]


def review_markdown(report: dict) -> str:
    lines = ["# No-API Saved-Artifact Review Bundle", "", "> Historical editor outputs are controls, not same-blogger candidate outputs.", "",
             "| case | group | body/floor | H1/H2 | narrator | meta ratio | zero candidates | opening proxy |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for item in report["cases"]:
        m = item["metrics"]
        lines.append(f"| {item['id']} | {item['group']} | {m['body_chars']}/{m['body_floor']} | {m['h1_count']}/{m['h2_count']} | {m['narrator_total']} | {m['meta_sentence_ratio']:.3f} | {len(m['zero_anaphora_candidates'])} | {m['source_overlap']['opening_ratio']:.3f} |")
    lines += ["", "## Manual review", "", "1. 低関心の偶然訪問者にも導入の続きを読む理由があるか。", "2. 外部説明ではなく自社本人の声か。",
              "3. 省略主語を一意に復元できるか。", "4. 後半にもsource固有の場面・名詞・動作が残るか。", "5. 確認・整理・説明・判断の文が実質的な仕事をしているか。",
              "6. 文と段落のリズムが機械的でないか。", "", "No same-blogger Luna output exists yet; this bundle validates format and historical/control replay only."]
    return "\n".join(lines) + "\n"


def run(manifest_path: Path, out_dir: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package = manifest_path.parents[2]
    workspace = (package / manifest["workspace_root_from_package"]).resolve()
    report = {"decision": "conditionally_possible", "api_send_count": 0, "route_v_product_code_changed": False,
              "contract": render_contract(), "cases": []}
    all_articles = {}
    for case in manifest["cases"]:
        article_path, source_path = workspace / case["article"], workspace / case["source"]
        article, source = article_path.read_text(encoding="utf-8"), source_path.read_text(encoding="utf-8")
        all_articles[case["id"]] = article
        report["cases"].append({"id": case["id"], "group": case["group"], "article": case["article"], "source": case["source"],
                                "article_sha256": digest(article), "source_sha256": digest(source),
                                "metrics": analyze(article, source, int(case["floor"]))})
    report["cross_article_repeated_5grams"] = repeated(all_articles)
    report["limits"] = {"same_blogger_luna_output_present": False, "semantic_grounding_proven": False, "actual_latency_cost_known": False}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "contract_render.json").write_text(json.dumps(report["contract"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "replay_metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "human_review_bundle.md").write_text(review_markdown(report), encoding="utf-8")
    summary = {"decision": report["decision"], "api_send_count": 0, "case_count": len(report["cases"]),
               "arm_a_fixed_calls": 1, "arm_b_fixed_calls": 2,
               "stage_1_prompt_chars": report["contract"]["stage_1"]["chars"], "stage_2_prompt_chars": report["contract"]["stage_2"]["chars"],
               "same_role_both_stages": True, "same_blogger_luna_output_present": False,
               "next_owner": "luna_simple_blogger_live_ab_after_explicit_api_approval"}
    (out_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--manifest", type=Path, required=True); parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(run(args.manifest.resolve(), args.out_dir.resolve()), ensure_ascii=False)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
