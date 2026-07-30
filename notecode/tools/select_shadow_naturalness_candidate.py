from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


HARD_SHAPE_FLAGS = (
    "ai_summary_tone",
    "third_party_intro_tone",
    "textbook_explanation_tone",
    "generic_listicle_shape",
    "source_by_source_summary_shape",
)


def load_compare_summary(path: str | Path) -> dict[str, Any]:
    summary_path = Path(path)
    if summary_path.is_dir():
        summary_path = summary_path / "compare_summary.json"
    return json.loads(summary_path.read_text(encoding="utf-8"))


def iter_observations(summary: Mapping[str, Any], *, source: str = "") -> Iterable[dict[str, Any]]:
    for item in list(summary.get("variant_observations") or []):
        if not isinstance(item, Mapping):
            continue
        observation = dict(item)
        observation["_artifact_source"] = source
        observation["_summary_decision"] = str(summary.get("decision") or "")
        observation["_run_id"] = str(summary.get("run_id") or "")
        yield observation


def hard_issues(observation: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if observation.get("blocked"):
        issues.append("blocked")
    if observation.get("internal_term_leakage"):
        issues.append("internal_term_leakage")
    if observation.get("first_person_safety") == "unsafe":
        issues.append("unsafe_first_person")
    if int(observation.get("unsupported_claim_count", 0) or 0) > 0:
        issues.append("unsupported_claim")
    if int(observation.get("source_grounding_warning_count", 0) or 0) > 0:
        issues.append("source_grounding_warning")
    if int(observation.get("must_cover_warning_count", 0) or 0) > 0:
        issues.append("must_cover_warning")
    if observation.get("legal_guarantee_warning"):
        issues.append("legal_guarantee_warning")
    shape = dict(observation.get("shape_flags") or {})
    issues.extend(flag for flag in HARD_SHAPE_FLAGS if bool(shape.get(flag)))
    if observation.get("body_length_target_result") != "in_range":
        issues.append("body_length_not_in_range")
    if bool(observation.get("ending_bucket_monotony")):
        issues.append("ending_bucket_monotony")
    return issues


def score_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    body_chars = int(observation.get("body_char_count", 0) or 0)
    max_run = int(observation.get("ending_bucket_max_run", 0) or 0)
    metrics = dict(observation.get("stylometry_metrics") or {})
    gpt_total = int(metrics.get("gpt_frequent_term_total", 0) or 0)
    abstract_density = float(metrics.get("abstract_terms_per_1000_chars", 0.0) or 0.0)
    explicit_subject_count = int(metrics.get("explicit_subject_count", 0) or 0)
    connector_total = int(metrics.get("connector_total", 0) or 0)
    function_word_profile = dict(metrics.get("function_word_proxy_profile") or {})
    punctuation_profile = dict(metrics.get("punctuation_profile") or {})

    score = 0.0
    score += 24.0 if not observation.get("blocked") else -80.0
    score += 18.0 if int(observation.get("unsupported_claim_count", 0) or 0) == 0 else -40.0
    score += 16.0 if int(observation.get("source_grounding_warning_count", 0) or 0) == 0 else -40.0
    score += 12.0 if int(observation.get("must_cover_warning_count", 0) or 0) == 0 else -30.0
    score += 12.0 if not observation.get("legal_guarantee_warning") else -50.0
    score += 8.0 if observation.get("first_person_safety") == "safe" else -30.0
    score += 6.0 if observation.get("closing_recall_success") else -8.0

    if 1800 <= body_chars <= 2200:
        score += 24.0
    elif body_chars < 1800:
        score += max(0.0, body_chars / 1800.0 * 18.0)
        score -= 10.0
    else:
        score += 12.0
        score -= min(12.0, (body_chars - 2200) / 100.0)

    if max_run <= 5:
        score += 18.0
    elif max_run <= 7:
        score += 10.0
    elif max_run <= 10:
        score += 2.0
    else:
        score -= min(18.0, float(max_run - 10) * 3.0)

    score -= min(20.0, gpt_total * 4.0)
    score -= min(10.0, abstract_density * 2.0)
    score -= max(0.0, explicit_subject_count - 4) * 1.5
    score += min(4.0, connector_total * 0.5)

    if function_word_profile.get("method") == "surface_substring_proxy_no_morphology":
        score += 2.0
    if punctuation_profile.get("period_count"):
        score += 2.0

    issues = hard_issues(observation)
    return {
        "variant_id": str(observation.get("variant_id") or ""),
        "run_id": str(observation.get("_run_id") or ""),
        "artifact_source": str(observation.get("_artifact_source") or ""),
        "summary_decision": str(observation.get("_summary_decision") or ""),
        "score": round(score, 3),
        "hard_issues": issues,
        "candidate_state": "candidate_for_manual_review" if not issues and score >= 90 else "not_candidate",
        "body_char_count": body_chars,
        "body_length_target_result": str(observation.get("body_length_target_result") or ""),
        "ending_bucket_max_run": max_run,
        "gpt_frequent_term_total": gpt_total,
        "abstract_terms_per_1000_chars": abstract_density,
        "explicit_subject_count": explicit_subject_count,
        "source_grounding_warning_count": int(observation.get("source_grounding_warning_count", 0) or 0),
        "unsupported_claim_count": int(observation.get("unsupported_claim_count", 0) or 0),
        "must_cover_warning_count": int(observation.get("must_cover_warning_count", 0) or 0),
        "legal_guarantee_warning": bool(observation.get("legal_guarantee_warning")),
        "shape_flags": dict(observation.get("shape_flags") or {}),
    }


def select_naturalness_candidate(summaries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    skipped_summaries: list[dict[str, str]] = []
    for index, summary in enumerate(summaries):
        source = str(summary.get("_artifact_source") or f"summary_{index + 1}")
        observations = list(iter_observations(summary, source=source))
        if not observations:
            skipped_summaries.append(
                {
                    "artifact_source": source,
                    "run_id": str(summary.get("run_id") or ""),
                    "decision": str(summary.get("decision") or ""),
                    "reason": "no_variant_observations",
                }
            )
        for observation in observations:
            scored.append(score_observation(observation))
    scored.sort(key=lambda item: (item["candidate_state"] == "candidate_for_manual_review", item["score"]), reverse=True)
    best = scored[0] if scored else {}
    return {
        "selector_version": "shadow_naturalness_selector_v1",
        "selection_policy": "artifact_only_no_generation_no_adoption",
        "candidate_count": len(scored),
        "skipped_summary_count": len(skipped_summaries),
        "skipped_summaries": skipped_summaries,
        "best": best,
        "recommendation": "manual_review_candidate" if best.get("candidate_state") == "candidate_for_manual_review" else "no_clean_candidate",
        "ranked_candidates": scored,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select the best existing shadow naturalness artifact without generation.")
    parser.add_argument("summary", nargs="+", help="compare_summary.json paths or artifact directories.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args()

    summaries: list[dict[str, Any]] = []
    for raw_path in args.summary:
        path = Path(raw_path)
        summary = load_compare_summary(path)
        summary["_artifact_source"] = str(path)
        summaries.append(summary)

    result = select_naturalness_candidate(summaries)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json or not args.output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"output={args.output}")
        print(f"recommendation={result.get('recommendation')}")
        if result.get("best"):
            print(f"best_variant={result['best'].get('variant_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
