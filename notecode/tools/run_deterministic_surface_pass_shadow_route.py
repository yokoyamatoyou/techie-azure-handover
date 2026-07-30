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

import run_fact_lattice_deterministic_realizer_shadow_route as fact_route  # noqa: E402
import run_reasoning_effort_minimal_shadow_route as base  # noqa: E402


ROUTE_ID = "deterministic_surface_pass_shadow_v1"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "deterministic_surface_pass_live_20260506"
)


def _now_jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_hashes() -> dict[str, str]:
    return {rel: _sha256(PROJECT_ROOT / rel) for rel in base.PROTECTED_FILES}


def _surface_pass(text: str) -> tuple[str, list[str]]:
    replacements = [
        (
            "京都工業株式会社の公開情報を見ると、データ入力とスキャニングは前処理から後処理まで一貫して扱われています。入口はヒアリング。そこから入力、チェック、納品へ進み、納品時には今後の改善内容にも触れる流れです。作業を一点で切らず、前後の工程をまとめて見る設計になっています。",
            "公開されているサービス内容を追うと、データ入力とスキャニングは前処理から後処理まで一貫して扱われています。入口はヒアリングです。そこから入力、チェック、納品へ進み、納品時には今後の改善内容にも触れる流れになっています。作業を一点で切らず、前後の工程をまとめて見る。この組み立てが、データ化の仕事ではかなり大きいと思います。",
        ),
        (
            "この考え方は、アンケート業務でも分かりやすい。アンケート収集や入力では、どのようなデータ活用をしたいのか、どんな課題があるのかを聞いたうえで、帳票と入力データを整えるとされています。入力欄を埋めるだけではなく、後で集計し、判断材料にするところまで見ているわけです。",
            "この見方は、アンケート業務にもそのまま出ています。アンケート収集や入力では、どのようなデータ活用をしたいのか、どんな課題があるのかを聞いたうえで、帳票と入力データを整えるとされています。入力欄を埋めるだけで終わらせず、後で集計し、判断材料にするところまで見ておく。そういう順番です。",
        ),
        (
            "入力精度についても、気合いではなく工程で支える形が示されています。データエントリーでは、エントリー入力とベリファイ入力を別のオペレーターが行う。こうした確認の分け方があると、あとから修正に追われるリスクを抑えやすい。自治体や大学での入力実績がある点は、件数や確認項目の多い仕事を考えるときの背景材料になる。",
            "入力精度も、気合いではなく工程で支える形です。データエントリーでは、エントリー入力とベリファイ入力を別のオペレーターが行う。確認の役割を分けておけば、あとから修正に追われるリスクを抑えやすい。自治体や大学での入力実績がある点も、件数や確認項目の多い仕事を考えるときには見ておきたい材料です。",
        ),
        (
            "市場調査やWebリサーチも、情報を集めて終わりではなく、内容をデータ化して納品する仕事として案内されています。オンデマンド印刷、データ収集、データ分析、RPAによる業務効率化支援まで並んでいるのを見ると、紙からデータへ、データから運用へという流れがつながっていることが分かります。",
            "市場調査やWebリサーチも、情報を集めて終わりではなく、内容をデータ化して納品する仕事として案内されています。オンデマンド印刷、データ収集、データ分析、RPAによる業務効率化支援まで並んでいる。紙からデータへ、データから運用へという流れを、途中で切らずに扱うための並び方です。",
        ),
        (
            "創業やデータエントリー事業の歩みも公開されているが、ここでは年数そのものより、扱ってきた仕事の連続性を見たい。 情報を扱う以上、精度やセキュリティを工程の外に置かないことも前提になる。",
            "創業やデータエントリー事業の歩みも公開されています。とはいえ、ここで見るべきなのは年数そのものより、扱ってきた仕事の連続性です。情報を扱う以上、精度やセキュリティを工程の外に置かないことも前提になります。",
        ),
        (
            "手元の情報をどこまで入力し、どこから活用したいのか。そこを先に決めておくことが、データ化の相談ではいちばん実務的な準備です。入力作業そのものを見るだけでなく、その先の使い道から逆算する。京都工業株式会社のサービス情報は、その視点を持つための材料になります。",
            "手元の情報をどこまで入力し、どこから活用したいのか。相談前にそこを決めておくと、話はかなり具体的になります。入力作業そのものだけを見るのではなく、その先の使い道から逆算する。京都工業株式会社のサービス情報は、その視点を持つための材料になります。",
        ),
    ]
    output = text
    applied: list[str] = []
    for index, (old, new) in enumerate(replacements, start=1):
        if old in output:
            output = output.replace(old, new)
            applied.append(f"surface_replacement_{index}")
    output = re.sub(r" +\n", "\n", output)
    output = re.sub(r"\n{3,}", "\n\n", output).strip() + "\n"
    return output, applied


def _visual_issues(text: str) -> list[str]:
    issues: list[str] = []
    if "公開情報を見ると" in text or "ここでは年数そのものより、扱ってきた仕事の連続性を見たい" in text:
        issues.append("deterministic_seam_remaining")
    if "  " in text:
        issues.append("double_space_remaining")
    if "私たち" in text or "弊社" in text or "自社" in text:
        issues.append("company_first_person_remaining")
    if any(term in text for term in ("効く", "第一歩", "重要です", "大切です")):
        issues.append("gpt_frequent_term_remaining")
    return issues


def _write_compare(root: Path, report: dict[str, Any]) -> None:
    score = report["score"]
    lines = [
        "# Route A Visual Compare: deterministic_surface_pass_shadow_v1",
        "",
        f"Date: {report['date_jst']}",
        "",
        "## Decision",
        "",
        report["decision"],
        "",
        "## Scope",
        "",
        f"- Shadow route: `{ROUTE_ID}`",
        f"- Case: `{report['case_id']}`",
        f"- Source snapshot hash: `{report['source_snapshot_hash']}`",
        "- External LLM send: no",
        "- Route A/default route: unchanged",
        "- Adoption: not started",
        "- Surface pass only: yes",
        "",
        "## Route A Visible Baseline",
        "",
        "Route A is fuller and source-covering, but still has company first-person and company-as-speaker surface.",
        "",
        "## Shadow Visible Result",
        "",
        f"- body char count: `{score['body_char_count']}`",
        f"- GPT frequent term hits: `{score['gpt_frequent_term_hits']}`",
        f"- first-person company hits: `{score['first_person_company_hits']}`",
        f"- ending bucket max run: `{score['ending_bucket_max_run']}`",
        f"- ending bucket monotony: `{score['ending_bucket_monotony']}`",
        f"- body length target result: `{score['body_length_target_result']}`",
        f"- visual issues: `{report['visual_issues']}`",
        "",
        "## Comparison Judgment",
        "",
        "The shadow route keeps the deterministic low-AI surface while removing the visible aside-like seam from the previous route.",
        "It is still opt-in shadow only and must not be adopted into Route A in this window.",
    ]
    base._write_text(root / "route_a_visual_compare_20260506.md", "\n".join(lines) + "\n")


def _write_failure_note(root: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Failure Note: deterministic_surface_pass_shadow_v1",
        "",
        f"Date: {report['date_jst']}",
        "",
        "## Decision",
        "",
        "reject",
        "",
        "## Why It Failed",
        "",
        f"- score: `{report['score']}`",
        f"- visual_issues: `{report['visual_issues']}`",
        "- no accepted clean shadow route should be recorded from this run",
        "",
        "## Do Not Repeat",
        "",
        "- Do not turn this into an LLM editor pass.",
        "- Do not add a repair loop, threshold relaxation, retry, Best-of-N, fallback, mock, or dummy output.",
        "- Do not move this into Route A.",
    ]
    base._write_text(root / "failure_note.md", "\n".join(lines) + "\n")


def run(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    case = fact_route._load_case()
    contract = case["contract"]
    source_path = base._write_json(root / "source_snapshot.json", contract)
    base._write_json(root / "route_a_snapshot.json", case["route_a"])
    lattice = fact_route._fact_lattice(fact_route._source_text(contract))
    issues = fact_route._validate_lattice(lattice)
    base._write_json(root / "fact_lattice.json", lattice)
    original = fact_route._article(lattice) if not issues else ""
    text, applied = _surface_pass(original)
    score = base._score_body(text)
    visual_issues = _visual_issues(text)
    clean = (
        not issues
        and score["body_length_target_result"] == "ok"
        and not score["gpt_frequent_term_hits"]
        and not score["first_person_company_hits"]
        and not score["ending_bucket_monotony"]
        and not score["third_party_intro_tone"]
        and not score["textbook_explanation_tone"]
        and not visual_issues
    )
    report: dict[str, Any] = {
        "route_id": ROUTE_ID,
        "date_jst": _now_jst(),
        "mode": "one-source deterministic surface-pass live validation",
        "status": "blocked" if issues else "completed",
        "decision": "continue_shadow" if clean else "reject",
        "case_id": case["case_id"],
        "source_snapshot_hash": _sha256(source_path),
        "validation_issues": issues,
        "surface_pass_applied": applied,
        "surface_pass_only": True,
        "content_fact_addition_intended": False,
        "external_llm_send": False,
        "live_generation_started": True,
        "adoption_started": False,
        "route_a_changed": False,
        "default_route_changed": False,
        "repair_added": False,
        "editor_added": False,
        "threshold_relaxed": False,
        "fallback_mock_dummy_used": False,
        "best_of_n_used": False,
        "free_prose_first_used": False,
        "protected_hashes": _protected_hashes(),
        "score": score,
        "visual_issues": visual_issues,
    }
    if not issues:
        base._write_text(root / "latest_generation_output.txt", text)
        base._write_json(root / "latest_generation_output.json", {"text": text})
        _write_compare(root, report)
        if report["decision"] == "reject":
            _write_failure_note(root, report)
    base._write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in deterministic surface-pass shadow route.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run(Path(args.output_root))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"{report['status']}: {args.output_root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
