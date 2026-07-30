from __future__ import annotations

import difflib
import importlib.util
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
OUT = PACKAGE / "artifacts/live_ab_once"
ANALYZER_PATH = PACKAGE / "prototype/simple_blogger_no_api.py"
SPEC = importlib.util.spec_from_file_location("simple_blogger_no_api", ANALYZER_PATH)
assert SPEC and SPEC.loader
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


def load_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def cost(usage: dict) -> dict:
    input_tokens = usage["input_tokens"]
    details = usage.get("input_tokens_details", {})
    cached = details.get("cached_tokens", 0) or 0
    cache_write = details.get("cache_write_tokens", 0) or 0
    uncached = max(0, input_tokens - cached - cache_write)
    output_tokens = usage["output_tokens"]
    input_usd = (uncached * 1.0 + cached * 0.10 + cache_write * 1.25) / 1_000_000
    output_usd = output_tokens * 6.0 / 1_000_000
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "cache_write_tokens": cache_write,
        "uncached_input_tokens": uncached,
        "output_tokens_including_reasoning": output_tokens,
        "reasoning_tokens": usage.get("output_tokens_details", {}).get("reasoning_tokens", 0),
        "input_usd": round(input_usd, 8),
        "output_usd": round(output_usd, 8),
        "total_usd": round(input_usd + output_usd, 8),
    }


def paragraphs(text: str) -> list[str]:
    return [x.strip() for x in text.split("\n\n") if x.strip()]


def changed_paragraphs(before: str, after: str) -> dict:
    a, b = paragraphs(before), paragraphs(after)
    matcher = difflib.SequenceMatcher(a=a, b=b)
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            changes.append({"tag": tag, "before_indexes": [i1, i2], "after_indexes": [j1, j2], "before": a[i1:i2], "after": b[j1:j2]})
    return {"paragraph_similarity_ratio": round(matcher.ratio(), 4), "change_block_count": len(changes), "changes": changes}


def review_bundle(source: str, x: str, y: str) -> str:
    return f"""# Blind Human Review Bundle

## Source ledger

{source}

## Candidate X

{x}

## Candidate Y

{y}

## Review axes (1-5)

1. 自社本人の声として自然か
2. 低関心の偶然訪問者が続きを読みたくなる導入か
3. 省略主語を迷わず復元できるか
4. source固有の場面・名詞・動作が残っているか
5. 確認・整理・説明・判断などのメタ文が支配していないか
6. 文と段落のリズムが自然か
7. substantive rewriteなしで公開できるか

Hard gate: source外の数値・日付・成果・責任・顧客評価があれば不合格。
"""


def main() -> int:
    preflight = load_json("preflight.json")
    ra, rb1, rb2 = load_json("arm_a_response.json"), load_json("arm_b_stage1_response.json"), load_json("arm_b_stage2_response.json")
    source = "\n\n".join(f"[{','.join(x['claim_ids'])}] {x['text']}" for x in preflight["ledger"])
    articles = {"A": ra["output_text"], "B1": rb1["output_text"], "B2": rb2["output_text"]}
    responses = {"A": ra, "B1": rb1, "B2": rb2}
    metrics = {label: ANALYZER.analyze(text, source, 1200) for label, text in articles.items()}
    costs = {label: cost(responses[label]["usage"]) for label in responses}
    arm_a_cost = costs["A"]["total_usd"]
    arm_b_cost = costs["B1"]["total_usd"] + costs["B2"]["total_usd"]
    arm_a_latency = ra["elapsed_seconds"]
    arm_b_latency = rb1["elapsed_seconds"] + rb2["elapsed_seconds"]
    b_changes = changed_paragraphs(articles["B1"], articles["B2"])
    result = {
        "model": preflight["model"],
        "reasoning_effort": preflight["reasoning_effort"],
        "send_count": 3,
        "retry_count": 0,
        "metrics": metrics,
        "costs": costs,
        "arm_summary": {
            "A": {"calls": 1, "latency_seconds": arm_a_latency, "cost_usd": round(arm_a_cost, 8)},
            "B": {"calls": 2, "latency_seconds": round(arm_b_latency, 3), "cost_usd": round(arm_b_cost, 8)},
            "B_to_A_latency_ratio": round(arm_b_latency / arm_a_latency, 3),
            "B_to_A_cost_ratio": round(arm_b_cost / arm_a_cost, 3),
        },
        "b_stage2_change": b_changes,
        "pricing_basis": {"input_per_mtok": 1.0, "cached_input_per_mtok": 0.10, "cache_write_multiplier": 1.25, "output_per_mtok": 6.0},
        "semantic_source_audit_status": "manual_review_required",
    }
    (OUT / "evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "blind_review_bundle.md").write_text(review_bundle(source, articles["B2"], articles["A"]), encoding="utf-8")
    (OUT / "blind_mapping.json").write_text(json.dumps({"X": "B2", "Y": "A"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["arm_summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
