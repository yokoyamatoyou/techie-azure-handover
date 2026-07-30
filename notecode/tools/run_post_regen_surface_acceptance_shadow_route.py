from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import run_persona_anchor_trigger_shadow_route as anchor_route  # noqa: E402
import run_reasoning_effort_minimal_shadow_route as base  # noqa: E402


ROUTE_ID = "post_regen_surface_acceptance_shadow_v1"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "post_regen_surface_acceptance_live_20260506"
)


def _now_jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_hashes() -> dict[str, str]:
    return {rel: _sha256(PROJECT_ROOT / rel) for rel in base.PROTECTED_FILES}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[。！？]", text) if s.strip()]


def _ending_buckets(text: str) -> list[str]:
    buckets: list[str] = []
    for sentence in _sentences(text):
        tail = sentence[-8:]
        if tail.endswith(("ます", "です", "ました", "でした", "でしょう")):
            buckets.append("polite")
        elif tail.endswith(("こと", "もの", "ところ", "流れ", "材料", "準備", "土台")):
            buckets.append("noun")
        elif tail.endswith(("やすい", "にくい", "ほしい", "よい", "多い", "変わる")):
            buckets.append("plain_adj")
        else:
            buckets.append("other")
    return buckets


def _max_run(items: list[str]) -> int:
    best = 0
    run = 0
    prev = ""
    for item in items:
        run = run + 1 if item == prev else 1
        prev = item
        best = max(best, run)
    return best


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def _surface_metrics(text: str) -> dict[str, Any]:
    paragraphs = _paragraphs(text)
    lengths = [len(p) for p in paragraphs]
    buckets = _ending_buckets(text)
    sentence_counts = [len(_sentences(p)) for p in paragraphs]
    polite_count = sum(1 for bucket in buckets if bucket == "polite")
    return {
        "char_count": len(text),
        "paragraph_count": len(paragraphs),
        "paragraph_lengths": lengths,
        "paragraph_length_variance": (max(lengths) - min(lengths)) if lengths else 0,
        "one_sentence_paragraph_count": sum(1 for count in sentence_counts if count == 1),
        "sentence_count": len(buckets),
        "ending_buckets": buckets,
        "ending_bucket_max_run": _max_run(buckets),
        "polite_ending_ratio": round(polite_count / len(buckets), 4) if buckets else 0.0,
    }


def _surface_gate(full_text: str, rewritten_tail: str) -> list[str]:
    full_metrics = _surface_metrics(full_text)
    tail_metrics = _surface_metrics(rewritten_tail)
    issues: list[str] = []
    if full_metrics["ending_bucket_max_run"] >= 7:
        issues.append("full_body_ending_run_too_high")
    if tail_metrics["ending_bucket_max_run"] >= 5:
        issues.append("tail_ending_run_too_high")
    if tail_metrics["paragraph_count"] >= 2 and tail_metrics["paragraph_length_variance"] < 60:
        issues.append("tail_paragraph_breathing_low_variance")
    if tail_metrics["paragraph_count"] >= 2 and tail_metrics["one_sentence_paragraph_count"] == 0 and tail_metrics["polite_ending_ratio"] >= 0.75:
        issues.append("tail_polite_explanation_block")
    return issues


def _regen_prompt(contract: dict[str, Any], text: str, trigger: dict[str, Any]) -> str:
    _, paragraphs, _ = anchor_route._split_main_and_tail(text)
    context = "\n\n".join(paragraphs[-4:-2])
    target = "\n\n".join(paragraphs[-2:])
    return f"""persona:
後半だけを見る会社運営ブログ編集者。意味は保ち、語尾だけで説明文に寄せない。

trigger:
{json.dumps(trigger, ensure_ascii=False)}

keep context:
{context}

rewrite only these last two body paragraphs:
{target}

surface budget:
同じ文末を続けない。です・ますだけで押し切らない。短い一文段落を一つだけ使ってよい。内容追加ではなく、後半の呼吸を整える。

meaning anchors:
相談前に決めること、入力から納品までの流れ、データ化後の使い道。

rules:
最後の二つの本文段落だけを書く。source外の事実を足さない。私たち・弊社・自社は使わない。参考情報とハッシュタグは出さない。

source:
{anchor_route._source_brief(contract)}
""".strip()


def _write_compare(root: Path, report: dict[str, Any]) -> None:
    score = report.get("score") or {}
    lines = [
        "# Route A Visual Compare: post_regen_surface_acceptance_shadow_v1",
        "",
        f"Date: {report['date_jst']}",
        "",
        "## Decision",
        "",
        report.get("decision", "blocked"),
        "",
        "## Scope",
        "",
        f"- Shadow route: `{ROUTE_ID}`",
        f"- Case: `{report['case_id']}`",
        f"- Source snapshot hash: `{report['source_snapshot_hash']}`",
        "- Route A/default route: unchanged",
        "- Adoption: not started",
        "- Regeneration calls: at most one late-section call",
        "- Surface gate: stricter reject gate, not threshold relaxation",
        "",
        "## Score",
        "",
        f"- body char count: `{score.get('body_char_count')}`",
        f"- GPT frequent term hits: `{score.get('gpt_frequent_term_hits')}`",
        f"- first-person company hits: `{score.get('first_person_company_hits')}`",
        f"- ending bucket max run: `{score.get('ending_bucket_max_run')}`",
        f"- body length target result: `{score.get('body_length_target_result')}`",
        f"- surface gate issues: `{report.get('surface_gate_issues')}`",
        "",
        "## Judgment",
        "",
        "This route tests whether late regeneration can be rejected by surface distribution instead of accepted by semantic anchors alone.",
    ]
    base._write_text(root / "route_a_visual_compare_20260506.md", "\n".join(lines) + "\n")


def _write_failure_note(root: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Failure Note: post_regen_surface_acceptance_shadow_v1",
        "",
        f"Date: {report['date_jst']}",
        "",
        "## Decision",
        "",
        "reject",
        "",
        "## Why It Failed",
        "",
        f"- score: `{report.get('score')}`",
        f"- trigger_report: `{report.get('trigger_report')}`",
        f"- tail_surface_metrics: `{report.get('tail_surface_metrics')}`",
        f"- surface_gate_issues: `{report.get('surface_gate_issues')}`",
        "- accepted clean shadow route remains absent",
        "",
        "## Do Not Repeat",
        "",
        "- Do not relax the surface gate to pass this route.",
        "- Do not add another regeneration call.",
        "- Do not keep the pre-regeneration draft as fallback.",
        "- Do not move this into Route A.",
    ]
    base._write_text(root / "failure_note.md", "\n".join(lines) + "\n")


def run(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    case = anchor_route._load_case()
    contract = case["contract"]
    source_path = base._write_json(root / "source_snapshot.json", contract)
    base._write_json(root / "route_a_snapshot.json", case["route_a"])
    writer_prompt = anchor_route._writer_prompt(contract)
    base._write_text(root / "writer_prompt_preview.txt", writer_prompt)
    model = anchor_route._model()
    capability = anchor_route._sdk_capability()
    issues = []
    if case["case_id"] != "latest_ui_route_a_gen-453da287":
        issues.append("case_id_not_latest_ui_route_a_gen-453da287")
    if contract.get("article_type") != "branding":
        issues.append("article_type_not_branding")
    if contract.get("semantic_article_key") != "company_introduction":
        issues.append("semantic_article_key_not_company_introduction")
    report: dict[str, Any] = {
        "route_id": ROUTE_ID,
        "date_jst": _now_jst(),
        "mode": "one-source post-regeneration surface-acceptance live validation",
        "status": "blocked" if issues else "started",
        "case_id": case["case_id"],
        "source_snapshot_hash": _sha256(source_path),
        "writer_prompt_sha256": hashlib.sha256(writer_prompt.encode("utf-8")).hexdigest(),
        "writer_prompt_chars": len(writer_prompt),
        "configured_generation_model": model,
        "validation_issues": issues,
        "external_llm_send": False,
        "live_generation_started": False,
        "adoption_started": False,
        "route_a_changed": False,
        "default_route_changed": False,
        "repair_added_to_route_a": False,
        "editor_added_to_route_a": False,
        "threshold_relaxed": False,
        "fallback_mock_dummy_used": False,
        "best_of_n_used": False,
        "protected_hashes": _protected_hashes(),
    }
    if issues:
        base._write_json(root / "live_report.json", report)
        return report
    try:
        anchor_route.load_dotenv(PROJECT_ROOT / ".env")
        draft = anchor_route._call_chat(writer_prompt, model, capability)
        trigger = anchor_route._trigger_report(draft)
        final_text = draft
        replacement = ""
        regen_executed = False
        if trigger["triggered"]:
            regen_prompt = _regen_prompt(contract, draft, trigger)
            base._write_text(root / "regeneration_prompt_preview.txt", regen_prompt)
            replacement = anchor_route._call_chat(regen_prompt, model, capability)
            final_text = anchor_route._replace_last_two_body_paragraphs(draft, replacement)
            regen_executed = True
    except Exception as exc:
        report.update(
            {
                "status": "blocked",
                "blocked_reason": str(exc),
                "external_llm_send": True,
                "live_generation_started": True,
            }
        )
        base._write_json(root / "live_report.json", report)
        return report
    score = base._score_body(final_text)
    surface_gate_issues = _surface_gate(final_text, replacement or final_text)
    visual_issues = anchor_route._visual_issues(final_text)
    clean = (
        score["body_length_target_result"] == "ok"
        and not score["gpt_frequent_term_hits"]
        and not score["first_person_company_hits"]
        and not score["ending_bucket_monotony"]
        and not score["third_party_intro_tone"]
        and not score["textbook_explanation_tone"]
        and not visual_issues
        and not surface_gate_issues
    )
    report.update(
        {
            "status": "completed",
            "decision": "continue_shadow" if clean else "reject",
            "external_llm_send": True,
            "live_generation_started": True,
            "trigger_report": trigger,
            "trigger_fired": trigger["triggered"],
            "regeneration_call_executed": regen_executed,
            "score": score,
            "visual_issues": visual_issues,
            "tail_surface_metrics": _surface_metrics(replacement or final_text),
            "full_surface_metrics": _surface_metrics(final_text),
            "surface_gate_issues": surface_gate_issues,
        }
    )
    base._write_text(root / "draft_before_trigger.txt", draft + "\n")
    if replacement:
        base._write_text(root / "rewritten_tail.txt", replacement + "\n")
    base._write_text(root / "latest_generation_output.txt", final_text + "\n")
    base._write_json(root / "latest_generation_output.json", {"text": final_text})
    _write_compare(root, report)
    if report["decision"] == "reject":
        _write_failure_note(root, report)
    base._write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in post-regeneration surface acceptance shadow route.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run(Path(args.output_root))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"{report['status']}: {args.output_root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
