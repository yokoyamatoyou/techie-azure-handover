from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
WORKSPACE = PACKAGE.parents[2]
OUT = PACKAGE / "artifacts/past_a_vs_current_b"
HISTORICAL_ROOT = (
    WORKSPACE
    / "notecode/logs/0624/"
    "route_v_company_intro_reader_inference_contract_sanrei_one_article_api_validation_after_diagnosis_20260624_204407"
)
PAST_ARTICLE = HISTORICAL_ROOT / "route_b_artifacts/01_sanrei_foods/latest_generation_output.md"
SAVED_SOURCE = HISTORICAL_ROOT / "route_b_artifacts/01_sanrei_foods/selected_source_excerpts.json"
HISTORICAL_VALIDATION = HISTORICAL_ROOT / "validation_results.json"
LIVE_ROOT = PACKAGE / "artifacts/live_ab_once"
CURRENT_ARTICLE = LIVE_ROOT / "arm_b_article.md"
PREFLIGHT = LIVE_ROOT / "preflight.json"

ANALYZER_PATH = PACKAGE / "prototype/simple_blogger_no_api.py"
SPEC = importlib.util.spec_from_file_location("simple_blogger_no_api", ANALYZER_PATH)
assert SPEC and SPEC.loader
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def workspace_suffix(path: Path) -> str:
    value = path.as_posix()
    return "notecode/" + value.split("notecode/", 1)[1] if "notecode/" in value else value


def table_row(label: str, metrics: dict) -> str:
    return (
        f"| {label} | {metrics['body_chars']} | {metrics['h1_count']}/{metrics['h2_count']} | "
        f"{metrics['sentence_chars']['maximum']} | {metrics['narrator_total']} | "
        f"{metrics['meta_sentence_ratio']:.3f} | {len(metrics['zero_anaphora_candidates'])} | "
        f"{metrics['source_overlap']['opening_ratio']:.3f} | "
        f"{metrics['source_overlap']['body_ratio']:.3f} |"
    )


def main() -> int:
    old_source = json.loads(SAVED_SOURCE.read_text(encoding="utf-8"))
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    validation = json.loads(HISTORICAL_VALIDATION.read_text(encoding="utf-8"))
    live_response = json.loads((LIVE_ROOT / "arm_b_stage2_response.json").read_text(encoding="utf-8"))
    past = PAST_ARTICLE.read_text(encoding="utf-8")
    current = CURRENT_ARTICLE.read_text(encoding="utf-8")

    old_ids = [claim for item in old_source for claim in item["claim_ids"]]
    live_ids = [claim for item in preflight["ledger"] for claim in item["claim_ids"]]
    old_texts = [normalized(item["text"]) for item in old_source]
    live_texts = [normalized(item["text"]) for item in preflight["ledger"]]
    source = "\n\n".join(
        f"[{','.join(item['claim_ids'])}] {item['text']}" for item in old_source
    )

    metrics = {
        "A_past_route_v": ANALYZER.analyze(past, source, 1200),
        "B_current_luna_two_stage": ANALYZER.analyze(current, source, 1200),
    }
    historical = validation["result"]
    lineage = {
        "same_saved_source_file": workspace_suffix(Path(preflight["source_path"])) == workspace_suffix(SAVED_SOURCE),
        "same_excerpt_count": len(old_source) == preflight["excerpt_count"] == 4,
        "same_claim_id_sequence": old_ids == live_ids,
        "same_normalized_excerpt_texts": old_texts == live_texts,
        "claim_ids": old_ids,
        "saved_source_sha256": sha256(SAVED_SOURCE.read_text(encoding="utf-8")),
        "important_input_caveat": (
            "同じ4 excerptのsource lineageだが、過去Route Vはarticle brief/knowledge packも入力し、"
            "今回Bはcompact ledgerを入力したためprompt payloadは同一ではない"
        ),
    }
    result = {
        "comparison": "past Route V A vs current Luna same-blogger two-stage B",
        "api_send_count": 0,
        "user_preference": "B",
        "decision": "B preferred for this one-source human comparison",
        "articles": {
            "A_past_route_v": {
                "path": workspace_suffix(PAST_ARTICLE),
                "sha256": sha256(past),
            },
            "B_current_luna_two_stage": {
                "path": workspace_suffix(CURRENT_ARTICLE),
                "sha256": sha256(current),
                "matches_saved_api_response_output_text": current == live_response["output_text"],
            },
        },
        "source_lineage": lineage,
        "common_analyzer": {
            "name": "simple_blogger_no_api.py analyze",
            "display_floor": 1200,
            "metrics": metrics,
            "limits": [
                "character trigram overlap is not semantic grounding proof",
                "zero-anaphora detection is a manual-review candidate heuristic",
                "the two historical generation contracts and prompt payloads differ",
            ],
        },
        "historical_official_record": {
            "body_chars": historical["final_body_chars"],
            "floor": historical["body_length_floor_chars"],
            "floor_reached": historical["final_floor_reached"],
            "h1_count": historical["h1_count"],
            "quality_score": historical["quality_score"],
            "quality_issue_types": historical["quality_issue_types"],
            "reader_inference_disallowed_count": historical["reader_inference_bridge_review"]["disallowed_reader_inference_bridge_count"],
        },
        "contract_floor_views": {
            "past_A_official_1400": historical["final_floor_reached"],
            "past_A_common_analyzer_1200": metrics["A_past_route_v"]["body_floor_reached"],
            "current_B_common_analyzer_1200": metrics["B_current_luna_two_stage"]["body_floor_reached"],
            "current_B_common_analyzer_1400": metrics["B_current_luna_two_stage"]["body_chars"] >= 1400,
        },
        "manual_review": {
            "past_A_known_reader_inference": "会社の約束とグループの方向性を、同じ場所で確認できます。",
            "current_B_known_zero_anaphora_candidate": metrics["B_current_luna_two_stage"]["zero_anaphora_candidates"],
            "adoption_status": "not authorized; Route V accepted state unchanged",
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "evaluation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    comparison = f"""# Past Route V A vs Current Luna B

## Outcome

User preference: **B**. For this saved Sanrei source comparison, current Luna B is the human-preferred article.

This supersedes the earlier machine-only provisional preference for the one-call live arm. It does not alter Route V or prove multi-source adoption readiness.

## Source comparability

- Same saved Sanrei source lineage: 4 excerpts, claim IDs `{', '.join(old_ids)}`.
- Normalized excerpt texts match exactly: `{lineage['same_normalized_excerpt_texts']}`.
- Important caveat: the prompt payloads are not identical. Past Route V also received its article brief and knowledge pack; current B received the compact ledger.
- New API sends for this comparison: `0`.

## Common analyzer

| article | body chars | H1/H2 | max sentence | narrator | meta ratio | zero candidates | opening proxy | body proxy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{table_row('A: past Route V', metrics['A_past_route_v'])}
{table_row('B: current Luna two-stage', metrics['B_current_luna_two_stage'])}

The common analyzer supports the user's preference on opening source specificity, maximum sentence length, H2 structure, narrator repetition, and meta-language. B's remaining regression is one paragraph-boundary zero-anaphora candidate; a human should read that sentence with the preceding paragraph rather than treating the heuristic as an automatic rejection.

## Historical record kept separate

Past A's original Route V record was `1219/1400`, quality score `76`, with `sentence_too_long`, `model_frequent_word`, and `body_length_below_floor`; it also had one disallowed reader-inference frame ending in 「確認できます」.

Current B reaches its own 1200-character contract under the common analyzer, but does not reach 1400. Therefore floor status is not used as evidence that B is universally better; the contracts differ.

## Decision

`B preferred for this one-source human comparison`.

The result is evidence for the same-blogger second stage, not authorization to connect it to Route V. A multi-source variance check and direct grounding review would still be required before any adoption proposal.
"""
    (OUT / "comparison.md").write_text(comparison, encoding="utf-8")

    bundle = f"""# Human A/B Bundle — Saved Sanrei Source

> Both candidates use the same saved four-excerpt Sanrei source lineage. No API was called for this comparison.

## Candidate A — past Route V

{past}

## Candidate B — current Luna two-stage

{current}

## Recorded judgment

- User preference: `B`
- Scope: one-source article preference only
- Route V adoption or accepted-state change: `not authorized`
"""
    (OUT / "human_ab_bundle.md").write_text(bundle, encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "metrics": metrics}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
