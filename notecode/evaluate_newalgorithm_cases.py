"""Fixed comparison runner for newalgorithm_mainline.

Usage:
  cd notecode (このファイルがあるディレクトリ)
  .venv\Scripts\python.exe evaluate_newalgorithm_cases.py
  .venv\Scripts\python.exe evaluate_newalgorithm_cases.py --live
  .venv\Scripts\python.exe evaluate_newalgorithm_cases.py --case case_study --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from note.llm_client import LLMClient  # noqa: E402
from note.newalgorithm_pipeline.pipeline import MinimalPipeline as _TransitionalEvaluationPipeline  # noqa: E402


FIXED_CASES: Dict[str, Dict[str, Any]] = {
    "branding": {
        "source": [],
        "topic": "小規模SaaSの導入初期で、機能の多さより運用の迷いを減らす価値を伝えるブランド記事",
        "article_type": "branding",
        "media": "note",
        "length_mode": "normal",
        "writing_focus": "experience",
        "tone_profile": "warm",
        "speaker_profile": "ブランド担当者",
        "audience_profile": "導入を検討する読者",
    },
    "industry_analysis": {
        "source": [],
        "topic": "AI導入支援ツール市場で、生成機能より運用定着支援が評価軸として強まっている流れを整理する",
        "article_type": "industry_analysis",
        "media": "note",
        "length_mode": "normal",
        "writing_focus": "analysis",
        "tone_profile": "calm",
        "speaker_profile": "業界分析担当者",
        "audience_profile": "意思決定者",
    },
    "case_study": {
        "source": [],
        "topic": "オンボーディング初回設定の案内導線を見直した事例。成功談に寄せすぎず、最初にどこで迷ったか、どう直したか、どの条件で再現できるかを含める",
        "article_type": "case_study",
        "media": "note",
        "length_mode": "normal",
        "writing_focus": "analysis",
        "tone_profile": "calm",
        "speaker_profile": "導入担当者",
        "audience_profile": "同じ課題を持つ実務担当者",
    },
    "announcement": {
        "source": [],
        "topic": "2026年4月1日に管理画面の権限設定フローを変更するお知らせ。対象者、影響、確認事項、移行時の注意点を含める",
        "article_type": "announcement",
        "media": "note",
        "length_mode": "normal",
        "writing_focus": "explanation",
        "tone_profile": "formal",
        "speaker_profile": "運営担当者",
        "audience_profile": "既存利用者",
    },
}

LEGAL_EVAL_CASES: Dict[str, Dict[str, Any]] = {
    "legal_a_notice": {
        "source": [],
        "topic": "2026年4月1日に請求書ダウンロード手順を変更するお知らせ。対象者、影響、確認事項を明確にする",
        "article_type": "announcement",
        "media": "note",
        "length_mode": "short",
        "writing_focus": "explanation",
        "tone_profile": "formal",
        "speaker_profile": "運営担当者",
        "audience_profile": "既存利用者",
    },
    "legal_b_compliance_explainer": {
        "source": [],
        "topic": "景表法や条文番号を推測で断定せず、関連法令の留意点として説明する",
        "article_type": "explanatory_article",
        "media": "note",
        "length_mode": "normal",
        "writing_focus": "analysis",
        "tone_profile": "calm",
        "speaker_profile": "実務担当者",
        "audience_profile": "実務担当者",
    },
}


def _build_evaluation_pipeline(*, live: bool) -> _TransitionalEvaluationPipeline:
    # Transitional: fixed evaluation cases still depend on wrapper-side
    # payload hydration and offline deterministic fallback behavior.
    llm_client = LLMClient() if live else None
    return _TransitionalEvaluationPipeline(llm_client=llm_client)


def _summarize_result(case_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    metrics = dict(result.get("pipeline_check", {}).get("quality_metrics", {}) or {})
    runtime = dict(result.get("pipeline_check", {}).get("runtime", {}) or {})
    summary = {
        "case_id": case_id,
        "success": bool(result.get("success")),
        "reason_code": str(result.get("reason_code") or ""),
        "title": str(result.get("title") or ""),
        "title_chars": len(str(result.get("title") or "")),
        "runtime": {
            "primary_model": runtime.get("primary_model"),
            "same_model_retry_count": runtime.get("same_model_retry_count"),
            "model_fallback_attempted": runtime.get("model_fallback_attempted"),
            "model_fallback_blocked": runtime.get("model_fallback_blocked"),
        },
        "metrics": {
            "body_chars": metrics.get("body_chars"),
            "topic_echo_ratio": metrics.get("topic_echo_ratio"),
            "topic_echo_body_only_ratio": metrics.get("topic_echo_body_only_ratio"),
            "topic_echo_long_span_count": metrics.get("topic_echo_long_span_count"),
            "section_opening_repetition_count": metrics.get("section_opening_repetition_count"),
            "ending_distribution_top": metrics.get("ending_distribution_top"),
            "example_specificity_count": metrics.get("example_specificity_count"),
            "abstract_example_fallback_count": metrics.get("abstract_example_fallback_count"),
            "unverified_legal_citation_count": metrics.get("unverified_legal_citation_count"),
        },
    }
    if case_id == "case_study":
        summary["metrics"].update(
            {
                "case_result_abstract_summary_count": metrics.get("case_result_abstract_summary_count"),
                "case_result_change_sentence_count": metrics.get("case_result_change_sentence_count"),
                "case_result_condition_sentence_count": metrics.get("case_result_condition_sentence_count"),
            }
        )
    if case_id == "announcement":
        summary["metrics"].update(
            {
                "fact_slot_coverage": metrics.get("fact_slot_coverage"),
                "fact_slot_reuse_count": metrics.get("fact_slot_reuse_count"),
                "announcement_invalid_modal_pattern_count": metrics.get("announcement_invalid_modal_pattern_count"),
            }
        )
    return summary


def _print_human(results: Iterable[Dict[str, Any]]) -> None:
    for item in results:
        print("=" * 72)
        print(f"[{item['case_id']}] success={item['success']} reason={item['reason_code']}")
        print(f"title ({item['title_chars']}): {item['title']}")
        runtime = item["runtime"]
        print(
            "runtime:"
            f" model={runtime.get('primary_model')}"
            f" retry={runtime.get('same_model_retry_count')}"
            f" fallback={runtime.get('model_fallback_attempted')}"
        )
        metrics = item["metrics"]
        print(
            "metrics:"
            f" echo={metrics.get('topic_echo_ratio')}"
            f" body_echo={metrics.get('topic_echo_body_only_ratio')}"
            f" heading_repeat={metrics.get('section_opening_repetition_count')}"
        )
        print(f"endings: {metrics.get('ending_distribution_top')}")
        if item["case_id"] == "case_study":
            print(
                "case_result:"
                f" abstract={metrics.get('case_result_abstract_summary_count')}"
                f" change={metrics.get('case_result_change_sentence_count')}"
                f" condition={metrics.get('case_result_condition_sentence_count')}"
            )
        if item["case_id"] == "announcement":
            print(
                "announcement:"
                f" fact_slot={metrics.get('fact_slot_coverage')}"
                f" reuse={metrics.get('fact_slot_reuse_count')}"
                f" invalid_modal={metrics.get('announcement_invalid_modal_pattern_count')}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fixed newalgorithm comparison cases.")
    parser.add_argument("--live", action="store_true", help="Use live OpenAI API instead of deterministic offline generation.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output.")
    parser.add_argument(
        "--include-legal-eval",
        action="store_true",
        help="Include non-gate legal evaluation cases in addition to the fixed regression set.",
    )
    parser.add_argument(
        "--case",
        dest="case_ids",
        action="append",
        choices=sorted({*FIXED_CASES.keys(), *LEGAL_EVAL_CASES.keys()}),
        help="Run only the specified case. Repeatable.",
    )
    args = parser.parse_args()

    all_cases = dict(FIXED_CASES)
    if args.include_legal_eval or any(case_id in LEGAL_EVAL_CASES for case_id in (args.case_ids or [])):
        all_cases.update(LEGAL_EVAL_CASES)
    selected_ids = list(args.case_ids or all_cases.keys())
    pipeline = _build_evaluation_pipeline(live=args.live)

    results: List[Dict[str, Any]] = []
    for case_id in selected_ids:
        payload = dict(all_cases[case_id])
        result = pipeline.generate(payload)
        results.append(_summarize_result(case_id, result))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        _print_human(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
