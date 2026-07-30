from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from note.current_mainline_ui_matrix import SHORT_SWEEP_CASES, UISweepCase, run_ui_sweep_cases


FIXED_CASE_IDS: List[str] = [
    "ui-short-branding-company-grounded",
    "ui-short-branding-trust",
    "ui-short-case-study-explain",
]

GENERIC_PROMPTS: Dict[str, str] = {
    "ui-short-branding-company-grounded": "医療支援SaaS企業の企業紹介。事業内容、選ばれる理由、現場で大切にしている姿勢を、資料に沿って簡潔に伝える",
    "ui-short-branding-trust": "小規模SaaSの導入初期で、機能の多さより運用の迷いを減らす価値を伝えるブランド記事",
    "ui-short-case-study-explain": "オンボーディング初回設定の案内導線を見直した事例。成功談に寄せすぎず、最初にどこで迷ったか、どう直したか、どの条件で再現できるかを含める",
}

STEP_OPTIMIZED_PROMPTS: Dict[str, str] = {
    "ui-short-branding-company-grounded": (
        "医療支援SaaS企業の会社紹介記事を書いてください。導入前に概要を知りたい読者向けに、事業内容と導入初期を支える姿勢が自然に伝わる文章にしてください。"
        "資料にある事実を軸に、何をしている会社か、なぜ導入初期支援を重視するのか、問い合わせを運用改善へ戻す進め方、最後に読者がどう理解すればよいか、の順で整理してください。"
        "宣伝調に寄せすぎず、現場での支え方が見える会社紹介にしてください。文の長さを揃えすぎず、同じ文末を続けすぎず、見出しごとに適度に改行し、ソースにない実績や数値は足さない。"
    ),
    "ui-short-branding-trust": (
        "導入初期のブランド記事を書いてください。機能の多さを売り込むより、運用の迷いを減らす価値が自然に伝わる文章にしてください。"
        "導入前の担当者が読み、何を支える会社なのか、どの場面で安心感が出るのか、なぜ初期設計が効くのか、最後にどう捉えればよいかの順に整理してください。"
        "断定や宣伝調を強めすぎず、文末と段落の運びを揃えすぎず、資料にない実績は足さない。"
    ),
    "ui-short-case-study-explain": (
        "オンボーディング導線を見直した事例記事を書いてください。成功談として盛らず、最初にどこで迷いが起きていたか、何をどう直したか、どの条件なら再現しやすいかが自然に読める文章にしてください。"
        "説明の順番を無理に整えすぎず、資料にある事実を軸に、改善の前後が見える事例記事にしてください。"
    ),
}


def _case_by_id(case_id: str) -> UISweepCase:
    return next(case for case in SHORT_SWEEP_CASES if case.case_id == case_id)


def _build_cases(prompt_map: Dict[str, str], note_suffix: str) -> List[UISweepCase]:
    built: List[UISweepCase] = []
    for case_id in FIXED_CASE_IDS:
        base = _case_by_id(case_id)
        built.append(
            UISweepCase(
                case_id=case_id,
                article_type=base.article_type,
                user_prompt_text=prompt_map[case_id],
                audience_profile_input=base.audience_profile_input,
                content_goal_key=base.content_goal_key,
                writing_focus_key=base.writing_focus_key,
                tone_profile_key=base.tone_profile_key,
                length_mode_key=base.length_mode_key,
                speaker_profile_input=base.speaker_profile_input,
                core_message_input=base.core_message_input,
                self_reference_policy_key=base.self_reference_policy_key,
                allow_experience=base.allow_experience,
                source_values=list(base.source_values),
                source_documents=deepcopy(base.source_documents),
                interview_answers=deepcopy(base.interview_answers),
                strict_saas_mode=base.strict_saas_mode,
                body_generation_experiment=base.body_generation_experiment,
                ui_journey=deepcopy(base.ui_journey),
                comparison_axes=list(base.comparison_axes),
                note=f"{base.note} / {note_suffix}".strip(" /"),
            )
        )
    return built


def _write_payload(root: Path, name: str, payload: Dict[str, object]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--step-name", default="step")
    parser.add_argument("--artifact-root", default="")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    default_artifact_root = Path(__file__).resolve().parents[1] / "logs" / "stepwise_three_article_gate"
    artifact_root = (
        Path(args.artifact_root)
        if args.artifact_root
        else default_artifact_root / f"{timestamp}-{args.step_name}"
    )

    generic_dir = artifact_root / "generic"
    optimized_dir = artifact_root / "optimized"

    generic_payload = run_ui_sweep_cases(
        _build_cases(GENERIC_PROMPTS, "generic"),
        live=bool(args.live),
        artifact_dir=generic_dir,
    )
    optimized_payload = run_ui_sweep_cases(
        _build_cases(STEP_OPTIMIZED_PROMPTS, "step-optimized"),
        live=bool(args.live),
        artifact_dir=optimized_dir,
    )

    _write_payload(generic_dir, "summary.json", generic_payload)
    _write_payload(optimized_dir, "summary.json", optimized_payload)

    report = {
        "artifact_root": str(artifact_root),
        "generic_summary": str(generic_dir / "summary.json"),
        "optimized_summary": str(optimized_dir / "summary.json"),
        "live": bool(args.live),
        "case_ids": list(FIXED_CASE_IDS),
        "step_name": str(args.step_name),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
