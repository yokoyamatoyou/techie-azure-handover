from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from note import note_writer_app as ui_mod
from note.current_mainline_runner import (
    build_current_mainline_input_contract,
    execute_current_mainline_generation,
)
from note.llm_client import LLMClient
from note.newalgorithm_pipeline.output_guard import (
    extract_existing_output_guard,
    scan_instructional_fragments,
)
from note.simple_note_pipeline.pipeline import MinimalPipeline
from note.prompt_echo_detector import build_prompt_echo_references
from note.newalgorithm_pipeline.strict_saas import normalize_strict_saas_mode

LONG_FORM_PROMOTION_LENGTH_BY_ARTICLE_TYPE: Dict[str, str] = {
    "explanatory_article": "long",
    "daily_story": "normal",
    "branding": "long",
    "announcement": "normal",
    "case_study": "long",
    "industry_analysis": "long",
    "comparative_review": "long",
}

LONG_FORM_REVIEW_CHECKLIST_BY_ARTICLE_TYPE: Dict[str, List[str]] = {
    "announcement": [
        "変更点・対象者・確認事項が混ざらず案内文として読めるか",
        "依頼文が action 節に寄り、曖昧な表現や modal 崩れがないか",
    ],
    "case_study": [
        "結果節が成功談の要約だけで終わらず、状態変化が読めるか",
        "condition 節に再現条件・前提・限界が残っているか",
    ],
    "comparative_review": [
        "criteria で置いた比較軸が comparison / fit / closing まで維持されているか",
        "絶対優劣や万人向け断定に流れていないか",
    ],
    "default": [
        "メタ説明や指示文が本文に混ざっていないか",
        "語尾や段落の運びが平坦すぎず、AI っぽい反復が目立たないか",
    ],
}

LIVE_PREFLIGHT_PROMPT = "疎通確認です。OK のみ返してください。"
SHORT_BATTERY_VERSION = "short10-v1"
SHORT_BATTERY_LIVE_EXECUTION_REASON = (
    "モデル差は static code と既存 audit だけでは判定できないため、algorithm 固定のまま短文 10 本だけ live 実行する。"
)
SHORT_BATTERY_RUBRIC_AXES: List[str] = [
    "contract_fit",
    "article_type_fit",
    "human_visible_ai_feel",
    "structural_clarity",
    "grounding_factual_caution",
]
SHORT_BATTERY_HARD_FAIL_RULES: List[str] = [
    "runtime failure",
    "pipeline source mismatch",
    "output_guard blocked",
    "prompt echo detected",
    "empty title/body",
    "quality hard fail",
    "material same_model_retry_count > 0",
    "model_fallback_attempted = true",
    "effective_temperature != null",
    "effective_top_p != null",
]
SHORT_BATTERY_LONG_FORM_GO_NO_GO_RULES: List[str] = [
    "all short_gate cases passed",
    "topic_echo_body_only_ratio < 0.28 for every case",
    "section_opening_repetition_count <= 1 for every case",
    "announcement_invalid_modal_pattern_count == 0",
    "case_result_condition_sentence_count >= 1 for case_study",
    "rubric mean total >= 8.0 / 10",
]
SHORT_BATTERY_BASELINE_VARIANT_COMPARE_POINTS: List[str] = [
    "hard_fail count",
    "rubric total and axis deltas",
    "quality report watch items",
    "runtime contract drift",
    "human-visible AI signals",
]
BENIGN_RUNTIME_RETRY_EVENTS = {"finish_reason_length"}
_REPO_ROOT = Path(__file__).resolve().parents[1]
_HISTORICAL_COMPARE_ARTIFACT_PATHS: Dict[str, Path] = {
    "latest_generation_quality_report": _REPO_ROOT / "logs" / "latest_generation_quality_report.json",
    "ad_hoc_quality_compare": _REPO_ROOT
    / "logs"
    / "ad_hoc_quality_compare"
    / "20260410-083045-prompt-only-vs-current-mainline-company-grounded"
    / "summary.json",
    "direct_gpt54_prompt_only_same_source": _REPO_ROOT
    / "logs"
    / "direct_gpt54_prompt_only_same_source_2026-04-03.json",
    "prompt_only_probe_same_source": _REPO_ROOT
    / "logs"
    / "prompt_only_probe_2026-04-03_same_source.json",
    "prompt_only_probe_same_source_force_accept": _REPO_ROOT
    / "logs"
    / "prompt_only_probe_2026-04-03_same_source_force_accept.json",
}


@dataclass(frozen=True)
class UISweepCase:
    case_id: str
    article_type: str
    user_prompt_text: str
    audience_profile_input: str
    content_goal_key: str = "auto"
    writing_focus_key: str = "auto"
    tone_profile_key: str = "auto"
    length_mode_key: str = "short"
    speaker_profile_input: str = ""
    core_message_input: str = ""
    self_reference_policy_key: str = "auto"
    allow_experience: bool = False
    source_values: List[str] = field(default_factory=list)
    source_documents: List[Dict[str, Any]] = field(default_factory=list)
    source_mode: str = "grounded"
    industry_hint: str = ""
    source_trace: List[Dict[str, Any]] = field(default_factory=list)
    interview_answers: Dict[str, Any] = field(default_factory=dict)
    strict_saas_mode: str = "medium"
    body_generation_experiment: str = ""
    ui_journey: Dict[str, Any] = field(default_factory=dict)
    comparison_axes: List[str] = field(default_factory=list)
    note: str = ""


def _source_doc(title: str, content: str, locator: str) -> Dict[str, Any]:
    return {
        "title": title,
        "content": content,
        "locator": locator,
        "source_type": "url",
        "notices": [],
    }


SHORT_SWEEP_CASES: List[UISweepCase] = [
    UISweepCase(
        case_id="ui-short-explanatory-default",
        article_type="explanatory_article",
        user_prompt_text="AI導入支援ツールを比較ではなく運用定着の判断材料として整理する解説記事",
        audience_profile_input="実務担当者",
        length_mode_key="adaptive",
        note="UI 初期値の smoke case",
    ),
    UISweepCase(
        case_id="ui-short-daily-interest",
        article_type="daily_story",
        user_prompt_text="新しい業務フローを試した日に感じた小さな変化と学びを、背伸びせず共有する日常記事",
        audience_profile_input="同じ立場の読者",
        content_goal_key="interest",
        writing_focus_key="experience",
        tone_profile_key="warm",
        length_mode_key="short",
        speaker_profile_input="現場担当として語る",
    ),
    UISweepCase(
        case_id="ui-short-branding-trust",
        article_type="branding",
        user_prompt_text="小規模SaaSの導入初期で、機能の多さより運用の迷いを減らす価値を伝えるブランド記事",
        audience_profile_input="導入検討中の担当者",
        content_goal_key="trust",
        writing_focus_key="explanation",
        tone_profile_key="passionate",
        length_mode_key="short",
        speaker_profile_input="ブランド担当として語る",
        core_message_input="機能の多さより運用の迷いを減らす価値を具体化する",
        self_reference_policy_key="watashitachi",
    ),
    UISweepCase(
        case_id="ui-short-announcement-action",
        article_type="announcement",
        user_prompt_text="2026年4月1日に管理画面の権限設定フローを変更するお知らせ。対象者、影響、確認事項、移行時の注意点を含める",
        audience_profile_input="既存利用者",
        content_goal_key="action",
        writing_focus_key="explanation",
        tone_profile_key="formal",
        length_mode_key="short",
        speaker_profile_input="運営担当として語る",
        core_message_input="変更点と確認事項を迷わず把握できるようにする",
    ),
    UISweepCase(
        case_id="ui-short-case-study-explain",
        article_type="case_study",
        user_prompt_text="オンボーディング初回設定の案内導線を見直した事例。成功談に寄せすぎず、最初にどこで迷ったか、どう直したか、どの条件で再現できるかを含める",
        audience_profile_input="同じ課題を持つ実務担当者",
        content_goal_key="explain",
        writing_focus_key="analysis",
        tone_profile_key="calm",
        length_mode_key="short",
        speaker_profile_input="導入支援担当として語る",
        core_message_input="成功談に寄せず再現条件まで含めて共有する",
        source_values=[
            "https://fixture.techie/case-study/onboarding-funnel-audit",
            "https://fixture.techie/case-study/onboarding-funnel-playbook",
        ],
        source_documents=[
            _source_doc(
                "初回設定導線の見直しメモ",
                "初回設定では権限設定画面の手前で離脱が多く、利用者は通知設定と権限設定の順番を迷っていた。案内文では管理者向けの前提説明が先に出ており、実務担当者は自分の次の操作を判断しにくかった。",
                "https://fixture.techie/case-study/onboarding-funnel-audit",
            ),
            _source_doc(
                "案内導線の再設計手順",
                "改善後は最初の画面で担当者別の入口を分け、初回設定を三段階に整理した。再現条件として、管理者権限の有無を冒頭で分岐し、通知設定より先に権限設定を案内し、FAQへの退避リンクを各段階に置くと離脱が減りやすかった。",
                "https://fixture.techie/case-study/onboarding-funnel-playbook",
            ),
        ],
        ui_journey={"purpose_key": "case", "target_key": "improvement"},
        note="source-grounded case study stress",
    ),
    UISweepCase(
        case_id="ui-short-industry-analysis",
        article_type="industry_analysis",
        user_prompt_text="AI導入支援ツール市場で、生成機能より運用定着支援が評価軸として強まっている流れを整理する",
        audience_profile_input="意思決定者",
        content_goal_key="auto",
        writing_focus_key="analysis",
        tone_profile_key="calm",
        length_mode_key="short",
        speaker_profile_input="アナリストとして語る",
    ),
    UISweepCase(
        case_id="ui-short-comparative-review",
        article_type="comparative_review",
        user_prompt_text="SaaS導入支援ツールの比較レビュー。比較条件、評価軸、候補差分、用途別の向き不向き、確認事項を含める",
        audience_profile_input="比較検討中の読者",
        content_goal_key="auto",
        writing_focus_key="analysis",
        tone_profile_key="calm",
        length_mode_key="short",
        speaker_profile_input="比較検証担当として語る",
        ui_journey={"purpose_key": "compare", "target_key": "tool_service", "detail_key": "fit_explain"},
    ),
    UISweepCase(
        case_id="ui-short-web-explanatory-grounded",
        article_type="explanatory_article",
        user_prompt_text="生成AI導入で、利用範囲と運用責任をどう切り分けるかを最新の判断材料として整理する",
        audience_profile_input="実務担当者",
        content_goal_key="explain",
        writing_focus_key="analysis",
        tone_profile_key="calm",
        length_mode_key="short",
        source_mode="web",
        industry_hint="SaaS",
        source_documents=[
            _source_doc(
                "Example Research レポート",
                "生成AI導入では利用範囲の明確化と運用責任の分担が初期判断を左右する。特にSaaS運用では、誰が承認し、誰が日次確認を担うかを先に定めた組織ほど定着が早い。",
                "https://fixture.techie/web/example-research-report",
            ),
            _source_doc(
                "Example Analysis 解説",
                "実務運用では、試験導入の段階から入力禁止領域と確認フローを短く固定し、担当者が迷う分岐を増やしすぎないことが重要である。",
                "https://fixture.techie/web/example-analysis",
            ),
        ],
        source_trace=[
            {
                "query": "生成AI 導入 判断材料 最新 SaaS",
                "url": "https://fixture.techie/web/example-research-report",
                "publisher": "Example Research",
                "exact_date": "2026-04-01",
                "excerpt": "生成AI導入では利用範囲の明確化と運用責任の分担が初期判断を左右すると報告している。",
            },
            {
                "query": "生成AI 運用責任 解説 最新 SaaS",
                "url": "https://fixture.techie/web/example-analysis",
                "publisher": "Example Analysis",
                "exact_date": "2026-04-03",
                "excerpt": "入力禁止領域と確認フローを短く固定した組織ほど定着が早いと整理している。",
            },
        ],
        note="representative web-grounded explanatory case",
    ),
    UISweepCase(
        case_id="ui-short-branding-company-grounded",
        article_type="branding",
        user_prompt_text="医療支援SaaS企業の企業紹介。事業内容、選ばれる理由、現場で大切にしている姿勢を、資料に沿って簡潔に伝える",
        audience_profile_input="導入前に概要を知りたい読者",
        content_goal_key="trust",
        writing_focus_key="explanation",
        tone_profile_key="calm",
        length_mode_key="short",
        speaker_profile_input="企業広報として語る",
        core_message_input="事業内容と運用支援の姿勢を根拠付きで伝える",
        self_reference_policy_key="watashitachi",
        source_values=[
            "https://fixture.techie/branding/company-profile",
            "https://fixture.techie/branding/support-policy",
        ],
        source_documents=[
            _source_doc(
                "テティエ株式会社 会社概要",
                "テティエ株式会社は、医療機関と製薬企業向けに導入定着を支援する業務SaaSを提供する。主力は導入初期の権限設計、教育導線、問い合わせ整理を一体で整える支援である。",
                "https://fixture.techie/branding/company-profile",
            ),
            _source_doc(
                "導入支援方針",
                "運用現場が迷わず使い始められる状態を重視し、導入初期は機能追加よりも運用ルール、担当者導線、FAQ整備を優先する。現場の問い合わせを週次で振り返り、説明不足の箇所を手順に戻す。",
                "https://fixture.techie/branding/support-policy",
            ),
        ],
        ui_journey={"purpose_key": "introduce", "target_key": "company"},
        note="source-grounded company introduction stress",
    ),
    UISweepCase(
        case_id="ui-short-announcement-dense-must-cover",
        article_type="announcement",
        user_prompt_text="2026年5月15日にSSO設定の必須項目を変更するお知らせ。対象者、停止時間、事前準備、当日の確認事項、旧設定の扱いを含める",
        audience_profile_input="既存利用者",
        content_goal_key="action",
        writing_focus_key="explanation",
        tone_profile_key="formal",
        length_mode_key="short",
        speaker_profile_input="運営担当として語る",
        core_message_input="対象者と事前準備を迷わず確認できるようにする",
        source_values=[
            "https://fixture.techie/announcement/sso-change",
            "https://fixture.techie/announcement/sso-change-faq",
        ],
        source_documents=[
            _source_doc(
                "SSO設定変更のお知らせ",
                "2026年5月15日22時から23時30分にSSO設定画面を更新する。対象は管理者とSSOを利用する既存利用者である。事前準備はIdP metadataの再取得と設定バックアップで、旧設定は2026年6月30日まで参照専用で保持する。",
                "https://fixture.techie/announcement/sso-change",
            ),
            _source_doc(
                "SSO変更 FAQ",
                "当日の確認事項はログインテスト、管理者権限の引き継ぎ確認、失敗時の連絡先確認である。停止時間中はSSOログインのみ停止し、既存セッションは継続する。",
                "https://fixture.techie/announcement/sso-change-faq",
            ),
        ],
        ui_journey={"purpose_key": "announce", "target_key": "standard"},
        note="dense must-cover announcement stress",
    ),
    UISweepCase(
        case_id="ui-short-comparative-axis-lock",
        article_type="comparative_review",
        user_prompt_text="社内ナレッジ共有SaaSの比較レビュー。比較条件、価格、用途別の向き不向き、運用体制の違いを整理する",
        audience_profile_input="比較検討中の担当者",
        content_goal_key="auto",
        writing_focus_key="analysis",
        tone_profile_key="calm",
        length_mode_key="short",
        speaker_profile_input="比較検証担当として語る",
        source_values=[
            "https://fixture.techie/compare/knowledge-share-a",
            "https://fixture.techie/compare/knowledge-share-b",
            "https://fixture.techie/compare/knowledge-share-c",
        ],
        source_documents=[
            _source_doc(
                "Product A",
                "Product A は月額5万円から導入でき、100名以下のチーム向けで、初期設定テンプレートが多い。サポートはメール中心である。",
                "https://fixture.techie/compare/knowledge-share-a",
            ),
            _source_doc(
                "Product B",
                "Product B は月額9万円で、複数部門の運用を想定し、CS同席の導入支援と柔軟な承認フロー設定を提供する。",
                "https://fixture.techie/compare/knowledge-share-b",
            ),
            _source_doc(
                "Product C",
                "Product C は月額12万円で、厳格な権限管理と専任CSを特徴とし、大規模運用や監査要件が厳しい組織向けである。",
                "https://fixture.techie/compare/knowledge-share-c",
            ),
        ],
        ui_journey={"purpose_key": "compare", "target_key": "tool_service", "detail_key": "fit_explain"},
        comparison_axes=["price", "use_case"],
        note="axis lock comparative stress",
    ),
]


def get_available_ui_option_keys() -> Dict[str, List[str]]:
    return {
        "article_type": list(ui_mod._get_combined_article_types().keys()),
        "content_goal": list(ui_mod.CONTENT_GOAL_LABELS.keys()),
        "writing_focus": list(ui_mod.WRITING_FOCUS_LABELS.keys()),
        "tone_profile": list(ui_mod.TONE_PROFILE_LABELS.keys()),
        "length_mode": list(ui_mod.LENGTH_MODE_LABELS.keys()),
    }


def get_short_sweep_cases() -> List[UISweepCase]:
    return list(SHORT_SWEEP_CASES)


def summarize_short_matrix_coverage(cases: Sequence[UISweepCase]) -> Dict[str, Any]:
    available = get_available_ui_option_keys()
    used = {
        "article_type": sorted({case.article_type for case in cases}),
        "content_goal": sorted({case.content_goal_key for case in cases}),
        "writing_focus": sorted({case.writing_focus_key for case in cases}),
        "tone_profile": sorted({case.tone_profile_key for case in cases}),
        "length_mode": sorted({case.length_mode_key for case in cases}),
    }
    return {
        "available": available,
        "used": used,
        "missing": {
            key: [value for value in values if value not in used.get(key, [])]
            for key, values in available.items()
        },
    }


def summarize_all_phase_length_coverage(cases: Sequence[UISweepCase]) -> Dict[str, List[str]]:
    short_lengths = sorted({case.length_mode_key for case in cases})
    promoted_lengths = sorted(
        {
            LONG_FORM_PROMOTION_LENGTH_BY_ARTICLE_TYPE.get(case.article_type, "")
            for case in cases
            if LONG_FORM_PROMOTION_LENGTH_BY_ARTICLE_TYPE.get(case.article_type, "")
        }
    )
    available = list(ui_mod.LENGTH_MODE_LABELS.keys())
    used = sorted({*short_lengths, *promoted_lengths})
    return {
        "available": available,
        "short_phase_used": short_lengths,
        "promoted_phase_used": promoted_lengths,
        "missing_after_promotion": [value for value in available if value not in used],
    }


def build_current_mainline_payload(case: UISweepCase) -> Dict[str, Any]:
    contract = build_current_mainline_input_contract(
        source_values=list(case.source_values),
        source_documents=list(case.source_documents),
        article_type=case.article_type,
        user_prompt_text=case.user_prompt_text,
        content_goal_key=case.content_goal_key,
        writing_focus_key=case.writing_focus_key,
        structure_key="auto",
        length_mode_key=case.length_mode_key,
        tone_profile_key=case.tone_profile_key,
        perspective_key="auto",
        allow_experience=bool(case.allow_experience),
        interview_answers=dict(case.interview_answers),
        speaker_profile_input=case.speaker_profile_input,
        audience_profile_input=case.audience_profile_input,
        core_message_input=case.core_message_input,
        self_reference_policy_key=case.self_reference_policy_key,
        strict_saas_mode=case.strict_saas_mode,
        ui_journey=dict(case.ui_journey) if case.ui_journey else None,
        comparison_axes=list(case.comparison_axes),
        body_generation_experiment=case.body_generation_experiment,
        source_mode=case.source_mode,
        industry_hint=case.industry_hint,
        source_trace=list(case.source_trace),
    )
    return contract


def _build_selection_summary(case: UISweepCase) -> Dict[str, Any]:
    summary = {
        "article_type_key": case.article_type,
        "article_type_label": ui_mod._get_combined_article_types().get(case.article_type, case.article_type),
        "content_goal_key": case.content_goal_key,
        "content_goal_label": ui_mod.CONTENT_GOAL_LABELS.get(case.content_goal_key, case.content_goal_key),
        "writing_focus_key": case.writing_focus_key,
        "writing_focus_label": ui_mod.WRITING_FOCUS_LABELS.get(case.writing_focus_key, case.writing_focus_key),
        "tone_profile_key": case.tone_profile_key,
        "tone_profile_label": ui_mod.TONE_PROFILE_LABELS.get(case.tone_profile_key, case.tone_profile_key),
        "length_mode_key": case.length_mode_key,
        "length_mode_label": ui_mod.LENGTH_MODE_LABELS.get(case.length_mode_key, case.length_mode_key),
        "requested_strict_saas_mode": normalize_strict_saas_mode(case.strict_saas_mode),
        "speaker_profile_input": case.speaker_profile_input,
        "self_reference_policy_key": case.self_reference_policy_key,
        "audience_profile_input": case.audience_profile_input,
        "allow_experience": bool(case.allow_experience),
        "source_mode": case.source_mode,
    }
    if case.ui_journey:
        summary["ui_journey"] = dict(case.ui_journey)
    if case.comparison_axes:
        summary["comparison_axes"] = list(case.comparison_axes)
    if str(case.body_generation_experiment or "").strip():
        summary["body_generation_experiment"] = str(case.body_generation_experiment or "").strip()
    return summary


def _collect_prompt_echo_hits(result: Dict[str, Any], prompt_raw: str) -> List[str]:
    references = build_prompt_echo_references(
        user_prompt=str(prompt_raw or "").strip(),
        include_must_cover=False,
    )
    article_type_key = str(
        ((result.get("pipeline_check") or {}).get("input_contract") or {}).get("article_type")
        or result.get("article_type")
        or ""
    ).strip().lower()
    texts: List[str] = []
    if article_type_key != "announcement":
        texts.append(str(result.get("title", "") or ""))
    texts.append(str(result.get("lead", "") or ""))
    texts.append(str(result.get("body", "") or ""))
    return scan_instructional_fragments(
        *texts,
        references=references,
        max_hits=5,
    )


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_string_list(value: Any, *, max_items: int = 8) -> List[str]:
    if not isinstance(value, list):
        return []
    normalized: List[str] = []
    for item in value:
        text = str(item or "").strip()
        if not text:
            continue
        normalized.append(text)
        if len(normalized) >= max_items:
            break
    return normalized


def _extract_quality_metrics(result: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(((result.get("pipeline_check") or {}).get("quality_metrics") or {}))


def _extract_contract_alignment(result: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(((result.get("pipeline_check") or {}).get("contract_alignment") or {}))


def _extract_final_quality_eval(result: Mapping[str, Any]) -> Dict[str, Any]:
    pipeline_check = dict(result.get("pipeline_check") or {})
    return dict(
        pipeline_check.get("final_quality_eval")
        or pipeline_check.get("failed_parameters", {}).get("final_quality_eval")
        or {}
    )


def _extract_fingerprint_phase(result: Mapping[str, Any]) -> Dict[str, Any]:
    pipeline_check = dict(result.get("pipeline_check") or {})
    return dict(pipeline_check.get("fingerprint_phase") or {})


def _extract_runtime_gate_metadata(result: Mapping[str, Any]) -> Dict[str, Any]:
    runtime: Dict[str, Any] = {}
    pipeline_check = dict(result.get("pipeline_check") or {})
    section_generation = dict(pipeline_check.get("section_generation") or {})
    candidates = [
        pipeline_check.get("runtime"),
        section_generation.get("llm_check"),
        result.get("llm_check"),
    ]
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            runtime.update(dict(candidate))
    return runtime


def _extract_runtime_retry_events(runtime: Mapping[str, Any]) -> List[str]:
    return _normalize_string_list(runtime.get("retry_events"), max_items=16)


def _has_only_benign_runtime_retry(runtime: Mapping[str, Any]) -> bool:
    retry_count = int(runtime.get("same_model_retry_count", 0) or 0)
    if retry_count <= 0:
        return False
    retry_events = _extract_runtime_retry_events(runtime)
    if not retry_events:
        return False
    return all(event in BENIGN_RUNTIME_RETRY_EVENTS for event in retry_events)


def _has_material_runtime_retry(runtime: Mapping[str, Any]) -> bool:
    retry_count = int(runtime.get("same_model_retry_count", 0) or 0)
    if retry_count <= 0:
        return False
    return not _has_only_benign_runtime_retry(runtime)


def _build_human_visible_ai_signals(result: Mapping[str, Any], prompt_echo_hits: Sequence[str]) -> List[str]:
    metrics = _extract_quality_metrics(result)
    fingerprint_phase = _extract_fingerprint_phase(result)
    final_quality_eval = _extract_final_quality_eval(result)
    signals: List[str] = []
    if prompt_echo_hits:
        signals.append(f"prompt_echo_hits={len(prompt_echo_hits)}")
    fingerprint_count = len(_normalize_string_list(fingerprint_phase.get("flat_zone_flags"), max_items=12))
    if fingerprint_count > 0:
        signals.append(f"fingerprint_flat_zone_flags={fingerprint_count}")
    section_opening_repetition_count = int(metrics.get("section_opening_repetition_count", 0) or 0)
    if section_opening_repetition_count > 1:
        signals.append(f"section_opening_repetition_count={section_opening_repetition_count}")
    bridge_phrase_count = int(metrics.get("bridge_phrase_count", 0) or 0)
    if bridge_phrase_count > 0:
        signals.append(f"bridge_phrase_count={bridge_phrase_count}")
    reader_emotion_proxy_count = int(metrics.get("reader_emotion_proxy_count", 0) or 0)
    if reader_emotion_proxy_count > 0:
        signals.append(f"reader_emotion_proxy_count={reader_emotion_proxy_count}")
    soft_warning_count = int(final_quality_eval.get("soft_warning_count", 0) or 0)
    if soft_warning_count > 0:
        signals.append(f"final_quality_soft_warning_count={soft_warning_count}")
    return signals


def _score_contract_fit(case: UISweepCase, result: Mapping[str, Any], prompt_echo_hits: Sequence[str]) -> tuple[int, str]:
    metrics = _extract_quality_metrics(result)
    contract_alignment = _extract_contract_alignment(result)
    if prompt_echo_hits:
        return 0, "prompt_echo"
    if not bool(result.get("success", False)):
        return 0, "runtime_failure"
    topic_echo_body_only_ratio = _safe_float(metrics.get("topic_echo_body_only_ratio"))
    must_cover_reflection_rate = _safe_float(contract_alignment.get("must_cover_reflection_rate"))
    prompt_anchor_coverage = _safe_float(contract_alignment.get("prompt_anchor_coverage"))
    source_trace_coverage = _safe_float(contract_alignment.get("source_trace_coverage"))
    fact_slot_coverage = _safe_float(metrics.get("fact_slot_coverage"))
    announcement_action_sentence_count = int(metrics.get("announcement_action_sentence_count", 0) or 0)
    if topic_echo_body_only_ratio is not None and topic_echo_body_only_ratio >= 0.28:
        return 0, "topic_echo_body_only_ratio>=0.28"
    announcement_contract_fallback = (
        case.article_type == "announcement"
        and must_cover_reflection_rate is not None
        and must_cover_reflection_rate < 0.5
        and fact_slot_coverage is not None
        and fact_slot_coverage >= 0.8
        and announcement_action_sentence_count >= 4
        and (
            not bool(case.source_values or case.source_documents)
            or source_trace_coverage is None
            or source_trace_coverage >= 0.8
        )
    )
    if must_cover_reflection_rate is not None and must_cover_reflection_rate < 0.5 and not announcement_contract_fallback:
        return 0, "must_cover_reflection_rate<0.50"
    if (
        (must_cover_reflection_rate is not None and must_cover_reflection_rate < 0.8)
        or (prompt_anchor_coverage is not None and prompt_anchor_coverage < 0.75)
        or (
            bool(case.source_values or case.source_documents)
            and source_trace_coverage is not None
            and source_trace_coverage < 0.8
        )
    ):
        return 1, "partial_contract_reflection"
    return 2, "contract_clear"


def _score_article_type_fit(case: UISweepCase, result: Mapping[str, Any]) -> tuple[int, str]:
    metrics = _extract_quality_metrics(result)
    contract_alignment = _extract_contract_alignment(result)
    article_type = str(case.article_type or "")
    if article_type == "announcement":
        invalid_modal = int(metrics.get("announcement_invalid_modal_pattern_count", 0) or 0)
        fact_slot_coverage = _safe_float(metrics.get("fact_slot_coverage"))
        if invalid_modal > 0:
            return 0, "announcement_invalid_modal"
        if fact_slot_coverage is not None and fact_slot_coverage < 0.8:
            return 1, "announcement_fact_slot_partial"
        return 2, "announcement_clear"
    if article_type == "case_study":
        condition_sentence_count = int(metrics.get("case_result_condition_sentence_count", 0) or 0)
        abstract_summary_count = int(metrics.get("case_result_abstract_summary_count", 0) or 0)
        if condition_sentence_count < 1:
            return 0, "case_result_condition_missing"
        if abstract_summary_count > 0:
            return 1, "case_result_too_abstract"
        return 2, "case_result_grounded"
    if article_type == "comparative_review":
        comparative_eval = _classify_comparative_axis_state(
            metrics.get("comparative_axis_shift_count"),
            metrics.get("comparative_absolute_winner_claim_count"),
        )
        return comparative_eval["score"], comparative_eval["reason"]
    if article_type == "branding" and bool(case.source_values or case.source_documents):
        source_trace_coverage = _safe_float(contract_alignment.get("source_trace_coverage"))
        if source_trace_coverage is not None and source_trace_coverage < 0.5:
            return 0, "branding_source_trace_low"
        if source_trace_coverage is not None and source_trace_coverage < 0.8:
            return 1, "branding_source_trace_partial"
    section_opening_repetition_count = int(metrics.get("section_opening_repetition_count", 0) or 0)
    if section_opening_repetition_count > 1:
        return 1, "section_opening_repetition"
    return 2, "article_type_clear"


def _classify_comparative_axis_state(
    axis_shift_count: Any,
    absolute_winner_count: Any,
) -> Dict[str, Any]:
    axis_shift = int(axis_shift_count or 0)
    absolute_winner = int(absolute_winner_count or 0)
    if absolute_winner > 0 or axis_shift > 4:
        score = 0
        reason = "comparative_axis_broken"
    elif axis_shift > 1:
        score = 1
        reason = "comparative_axis_soft_shift"
    else:
        score = 2
        reason = "comparative_axis_locked"
    return {
        "score": score,
        "reason": reason,
        "comparative_axis_shift_count": axis_shift,
        "comparative_absolute_winner_claim_count": absolute_winner,
    }


def _extract_comparative_stage_payload(result: Mapping[str, Any], stage_name: str) -> Dict[str, Any]:
    diagnostic = dict(((result.get("pipeline_check") or {}).get("comparative_stage_diagnostic") or {}))
    for item in list(diagnostic.get("stages") or []):
        stage = dict(item or {})
        if str(stage.get("stage") or "") == str(stage_name or ""):
            return stage
    return {}


def _build_comparative_stability_summary(
    case: UISweepCase,
    result: Mapping[str, Any],
    rubric: Mapping[str, Any],
) -> Dict[str, Any]:
    if str(case.article_type or "") != "comparative_review":
        return {"enabled": False}
    stage_payload = _extract_comparative_stage_payload(result, "section_generation")
    diagnostic = dict(((result.get("pipeline_check") or {}).get("comparative_stage_diagnostic") or {}))
    stage_metrics = dict(stage_payload.get("metrics") or stage_payload)
    stage_eval = _classify_comparative_axis_state(
        stage_metrics.get("comparative_axis_shift_count"),
        stage_metrics.get("comparative_absolute_winner_claim_count"),
    )
    rubric_axis = dict((dict(rubric.get("axis_scores") or {}).get("article_type_fit") or {}))
    rubric_reason = str(rubric_axis.get("reason") or "")
    return {
        "enabled": True,
        "primary_stage": "section_generation",
        "section_generation_available": bool(stage_payload),
        "axis_shift_count": stage_eval["comparative_axis_shift_count"],
        "absolute_winner_claim_count": stage_eval["comparative_absolute_winner_claim_count"],
        "stage_bucket": stage_eval["reason"],
        "stage_score": stage_eval["score"],
        "rubric_reason": rubric_reason,
        "rubric_score": int(rubric_axis.get("score", 0) or 0),
        "bucket_matches_rubric": stage_eval["reason"] == rubric_reason,
        "first_changed_stage": str(diagnostic.get("first_changed_stage") or ""),
        "changed_stage_names": _normalize_string_list(diagnostic.get("changed_stage_names"), max_items=8),
        "section_generation_metrics": {
            "body_chars": stage_metrics.get("body_chars"),
            "comparative_axis_shift_count": stage_eval["comparative_axis_shift_count"],
            "comparative_absolute_winner_claim_count": stage_eval["comparative_absolute_winner_claim_count"],
            "topic_echo_body_only_ratio": stage_metrics.get("topic_echo_body_only_ratio"),
            "paragraph_break_semantic_score": stage_metrics.get("paragraph_break_semantic_score"),
            "connective_opening_rate": stage_metrics.get("connective_opening_rate"),
            "paragraph_sentence_count_cv": stage_metrics.get("paragraph_sentence_count_cv"),
        },
    }


def _score_human_visible_ai_feel(result: Mapping[str, Any], prompt_echo_hits: Sequence[str]) -> tuple[int, str]:
    metrics = _extract_quality_metrics(result)
    final_quality_eval = _extract_final_quality_eval(result)
    fingerprint_phase = _extract_fingerprint_phase(result)
    if prompt_echo_hits:
        return 0, "prompt_echo"
    bridge_phrase_count = int(metrics.get("bridge_phrase_count", 0) or 0)
    reader_emotion_proxy_count = int(metrics.get("reader_emotion_proxy_count", 0) or 0)
    section_opening_repetition_count = int(metrics.get("section_opening_repetition_count", 0) or 0)
    fingerprint_flag_count = len(_normalize_string_list(fingerprint_phase.get("flat_zone_flags"), max_items=12))
    soft_warning_count = int(final_quality_eval.get("soft_warning_count", 0) or 0)
    if bridge_phrase_count > 0 or reader_emotion_proxy_count > 0:
        return 0, "explicit_ai_signal"
    if section_opening_repetition_count > 1 or fingerprint_flag_count >= 6 or soft_warning_count >= 4:
        return 1, "flat_or_repetitive"
    return 2, "human_visible_ok"


def _score_structural_clarity(result: Mapping[str, Any]) -> tuple[int, str]:
    metrics = _extract_quality_metrics(result)
    guard = extract_existing_output_guard(dict(result))
    body_text = str(result.get("body", "") or "").strip()
    title_text = str(result.get("title", "") or "").strip()
    sentence_integrity_warning_count = int(metrics.get("sentence_integrity_warning_count", 0) or 0)
    section_opening_repetition_count = int(metrics.get("section_opening_repetition_count", 0) or 0)
    body_chars = int(metrics.get("body_chars", len(body_text)) or len(body_text))
    if bool(guard.get("blocked", False)) or not title_text or not body_text or sentence_integrity_warning_count > 0:
        return 0, "blocked_or_incomplete"
    if section_opening_repetition_count > 1 or body_chars < 700:
        return 1, "structure_thin_or_repetitive"
    return 2, "structure_clear"


def _score_grounding_factual_caution(case: UISweepCase, result: Mapping[str, Any]) -> tuple[int, str]:
    metrics = _extract_quality_metrics(result)
    contract_alignment = _extract_contract_alignment(result)
    input_contract = dict(((result.get("pipeline_check") or {}).get("input_contract") or {}))
    source_grounding_reflection_ratio = _safe_float(metrics.get("source_grounding_reflection_ratio"))
    source_trace_coverage = _safe_float(contract_alignment.get("source_trace_coverage"))
    fact_slot_coverage = _safe_float(metrics.get("fact_slot_coverage"))
    unverified_legal_citation_count = int(metrics.get("unverified_legal_citation_count", 0) or 0)
    source_expected = bool(
        case.source_values
        or case.source_documents
        or input_contract.get("source_grounding_required", False)
    )
    if unverified_legal_citation_count > 0:
        return 0, "unverified_legal_citation"
    if (
        source_expected
        and (
            (source_grounding_reflection_ratio is not None and source_grounding_reflection_ratio < 0.5)
            or (source_trace_coverage is not None and source_trace_coverage < 0.5)
        )
    ):
        return 0, "source_grounding_low"
    if case.article_type == "announcement" and fact_slot_coverage is not None and fact_slot_coverage < 0.5:
        return 0, "announcement_fact_slot_low"
    if (
        source_expected
        and (
            (source_grounding_reflection_ratio is not None and source_grounding_reflection_ratio < 0.8)
            or (source_trace_coverage is not None and source_trace_coverage < 0.8)
        )
    ) or (
        case.article_type == "announcement"
        and fact_slot_coverage is not None
        and fact_slot_coverage < 0.8
    ):
        return 1, "grounding_partial"
    return 2, "grounding_clear"


def _build_rubric_summary(case: UISweepCase, result: Mapping[str, Any], prompt_echo_hits: Sequence[str]) -> Dict[str, Any]:
    contract_score, contract_reason = _score_contract_fit(case, result, prompt_echo_hits)
    article_type_score, article_type_reason = _score_article_type_fit(case, result)
    human_visible_score, human_visible_reason = _score_human_visible_ai_feel(result, prompt_echo_hits)
    structure_score, structure_reason = _score_structural_clarity(result)
    grounding_score, grounding_reason = _score_grounding_factual_caution(case, result)
    axis_scores = {
        "contract_fit": {"score": contract_score, "max_score": 2, "reason": contract_reason},
        "article_type_fit": {"score": article_type_score, "max_score": 2, "reason": article_type_reason},
        "human_visible_ai_feel": {"score": human_visible_score, "max_score": 2, "reason": human_visible_reason},
        "structural_clarity": {"score": structure_score, "max_score": 2, "reason": structure_reason},
        "grounding_factual_caution": {"score": grounding_score, "max_score": 2, "reason": grounding_reason},
    }
    total_score = sum(int(item["score"]) for item in axis_scores.values())
    return {
        "version": SHORT_BATTERY_VERSION,
        "axis_scores": axis_scores,
        "total_score": total_score,
        "max_score": len(SHORT_BATTERY_RUBRIC_AXES) * 2,
    }


def _build_contract_summary(result: Mapping[str, Any]) -> Dict[str, Any]:
    contract_alignment = _extract_contract_alignment(result)
    return {
        "must_cover_reflection_rate": _safe_float(contract_alignment.get("must_cover_reflection_rate")),
        "question_reflection_rate": _safe_float(contract_alignment.get("question_reflection_rate")),
        "prompt_anchor_coverage": _safe_float(contract_alignment.get("prompt_anchor_coverage")),
        "section_focus_coverage": _safe_float(contract_alignment.get("section_focus_coverage")),
        "source_trace_coverage": _safe_float(contract_alignment.get("source_trace_coverage")),
        "source_grounding_required": bool(
            ((result.get("pipeline_check") or {}).get("input_contract") or {}).get("source_grounding_required", False)
        ),
    }


def _build_quality_read_summary(result: Mapping[str, Any], prompt_echo_hits: Sequence[str]) -> Dict[str, Any]:
    quality_mode_resolution = dict(((result.get("pipeline_check") or {}).get("quality_mode_resolution") or {}))
    final_quality_eval = _extract_final_quality_eval(result)
    fingerprint_phase = _extract_fingerprint_phase(result)
    return {
        "quality_mode": {
            "requested_mode": str(quality_mode_resolution.get("requested_mode") or ""),
            "effective_mode": str(quality_mode_resolution.get("effective_mode") or ""),
            "decision_reason": str(quality_mode_resolution.get("decision_reason") or ""),
        },
        "final_quality_eval": {
            "hard_failed": bool(final_quality_eval.get("hard_failed", False)),
            "hard_fail_reasons": _normalize_string_list(final_quality_eval.get("hard_fail_reasons"), max_items=8),
            "soft_warning_count": int(final_quality_eval.get("soft_warning_count", 0) or 0),
            "soft_warnings": _normalize_string_list(final_quality_eval.get("soft_warnings"), max_items=8),
        },
        "fingerprint_flat_zone_flags": _normalize_string_list(fingerprint_phase.get("flat_zone_flags"), max_items=8),
        "human_visible_ai_signals": _build_human_visible_ai_signals(result, prompt_echo_hits),
    }


def _evaluate_short_gate(result: Dict[str, Any], prompt_echo_hits: Sequence[str]) -> Dict[str, Any]:
    guard = extract_existing_output_guard(result)
    section_generation = dict(((result.get("pipeline_check") or {}).get("section_generation") or {}))
    runtime = _extract_runtime_gate_metadata(result)
    final_quality_eval = _extract_final_quality_eval(result)
    fallback_used = bool(section_generation.get("fallback_used", False))
    runtime_reason_code = str(result.get("runtime_reason_code") or result.get("reason_code") or "")
    output_guard_reason = str(guard.get("reason_code") or "")
    failures: List[str] = []
    exemptions: List[str] = []
    prompt_echo_only_fallback = (
        fallback_used
        and runtime_reason_code == "POL_PROMPT_ECHO"
        and output_guard_reason == "POL_PROMPT_ECHO"
        and bool(prompt_echo_hits)
    )
    if prompt_echo_only_fallback:
        exemptions.append("offline_fallback_prompt_echo")
    elif not bool(result.get("success", False)):
        failures.append(f"runtime_reason_code={runtime_reason_code}")
    if str(result.get("pipeline_source") or "") != "newalgorithm_mainline":
        failures.append("pipeline_source_mismatch")
    if bool(guard.get("blocked", False)) and not prompt_echo_only_fallback:
        failures.append(f"output_guard_blocked={output_guard_reason or 'unknown'}")
    if prompt_echo_hits and not prompt_echo_only_fallback:
        failures.append(f"prompt_echo_hits={len(prompt_echo_hits)}")
    if not str(result.get("body", "") or "").strip():
        failures.append("empty_body")
    if not str(result.get("title", "") or "").strip():
        failures.append("empty_title")
    if bool(final_quality_eval.get("hard_failed", False)):
        failures.append("final_quality_hard_failed")
    if _has_material_runtime_retry(runtime):
        failures.append(f"same_model_retry_count={int(runtime.get('same_model_retry_count', 0) or 0)}")
    elif _has_only_benign_runtime_retry(runtime):
        exemptions.append("benign_length_retry")
    if bool(runtime.get("model_fallback_attempted", False)):
        failures.append("model_fallback_attempted")
    if runtime.get("effective_temperature") is not None:
        failures.append(f"effective_temperature={runtime.get('effective_temperature')}")
    if runtime.get("effective_top_p") is not None:
        failures.append(f"effective_top_p={runtime.get('effective_top_p')}")
    return {
        "passed": len(failures) == 0,
        "failures": failures,
        "exemptions": exemptions,
        "fallback_used": fallback_used,
        "evaluation_mode": "offline_smoke" if fallback_used else "live_quality",
    }


def _build_long_watch_items(result: Dict[str, Any], prompt_echo_hits: Sequence[str], article_type: str) -> List[str]:
    metrics = dict(((result.get("pipeline_check") or {}).get("quality_metrics") or {}))
    watches: List[str] = []
    if prompt_echo_hits:
        watches.append(f"prompt_echo_hits={len(prompt_echo_hits)}")
    if int(metrics.get("bridge_phrase_count", 0) or 0) > 0:
        watches.append(f"bridge_phrase_count={int(metrics.get('bridge_phrase_count', 0) or 0)}")
    if int(metrics.get("reader_emotion_proxy_count", 0) or 0) > 0:
        watches.append(f"reader_emotion_proxy_count={int(metrics.get('reader_emotion_proxy_count', 0) or 0)}")
    if int(metrics.get("sentence_integrity_warning_count", 0) or 0) > 0:
        watches.append(
            f"sentence_integrity_warning_count={int(metrics.get('sentence_integrity_warning_count', 0) or 0)}"
        )
    if float(metrics.get("topic_echo_body_only_ratio", 0.0) or 0.0) >= 0.28:
        watches.append(f"topic_echo_body_only_ratio={round(float(metrics.get('topic_echo_body_only_ratio', 0.0) or 0.0), 4)}")
    if int(metrics.get("section_opening_repetition_count", 0) or 0) > 1:
        watches.append(f"section_opening_repetition_count={int(metrics.get('section_opening_repetition_count', 0) or 0)}")
    if article_type == "case_study":
        if int(metrics.get("case_result_condition_sentence_count", 0) or 0) < 1:
            watches.append("case_result_condition_sentence_count<1")
        if int(metrics.get("case_result_abstract_summary_count", 0) or 0) > 0:
            watches.append(
                f"case_result_abstract_summary_count={int(metrics.get('case_result_abstract_summary_count', 0) or 0)}"
            )
    if article_type == "comparative_review":
        if int(metrics.get("comparative_axis_shift_count", 0) or 0) > 4:
            watches.append(f"comparative_axis_shift_count={int(metrics.get('comparative_axis_shift_count', 0) or 0)}")
        if int(metrics.get("comparative_absolute_winner_claim_count", 0) or 0) > 0:
            watches.append(
                "comparative_absolute_winner_claim_count="
                f"{int(metrics.get('comparative_absolute_winner_claim_count', 0) or 0)}"
            )
    if article_type == "announcement":
        if int(metrics.get("announcement_invalid_modal_pattern_count", 0) or 0) > 0:
            watches.append(
                "announcement_invalid_modal_pattern_count="
                f"{int(metrics.get('announcement_invalid_modal_pattern_count', 0) or 0)}"
            )
    return watches


def _build_metric_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    metrics = _extract_quality_metrics(result)
    return {
        "body_chars": metrics.get("body_chars"),
        "topic_echo_ratio": metrics.get("topic_echo_ratio"),
        "topic_echo_body_only_ratio": metrics.get("topic_echo_body_only_ratio"),
        "source_grounding_reflection_ratio": metrics.get("source_grounding_reflection_ratio"),
        "fact_slot_coverage": metrics.get("fact_slot_coverage"),
        "section_opening_repetition_count": metrics.get("section_opening_repetition_count"),
        "sentence_integrity_warning_count": metrics.get("sentence_integrity_warning_count"),
        "bridge_phrase_count": metrics.get("bridge_phrase_count"),
        "reader_emotion_proxy_count": metrics.get("reader_emotion_proxy_count"),
        "case_result_condition_sentence_count": metrics.get("case_result_condition_sentence_count"),
        "case_result_abstract_summary_count": metrics.get("case_result_abstract_summary_count"),
        "comparative_axis_shift_count": metrics.get("comparative_axis_shift_count"),
        "comparative_absolute_winner_claim_count": metrics.get("comparative_absolute_winner_claim_count"),
        "announcement_invalid_modal_pattern_count": metrics.get("announcement_invalid_modal_pattern_count"),
        "unverified_legal_citation_count": metrics.get("unverified_legal_citation_count"),
    }


def _extract_runtime_details(result: Mapping[str, Any]) -> Dict[str, Any]:
    return _extract_runtime_gate_metadata(result)


def _extract_body_generation_summary(result: Mapping[str, Any]) -> Dict[str, Any]:
    projected_summary = result.get("body_generation_summary")
    if isinstance(projected_summary, Mapping):
        return dict(projected_summary)
    pipeline_check = result.get("pipeline_check")
    if not isinstance(pipeline_check, Mapping):
        return {}
    body_generation = pipeline_check.get("body_generation")
    if not isinstance(body_generation, Mapping):
        return {}
    experimental_prompt_stack = body_generation.get("experimental_prompt_stack")
    if not isinstance(experimental_prompt_stack, Mapping):
        return {}
    visibility_summary = experimental_prompt_stack.get("visibility_summary")
    if not isinstance(visibility_summary, Mapping):
        return {}
    return dict(visibility_summary)


def _read_historical_compare_payload(path: Path) -> Dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(loaded) if isinstance(loaded, Mapping) else {}


def _extract_historical_needs_input_fields(payload: Mapping[str, Any]) -> List[str]:
    result = payload.get("result")
    result_mapping = dict(result) if isinstance(result, Mapping) else {}
    needs_input_items = list(result_mapping.get("needs_input_items") or [])
    if not needs_input_items:
        pipeline_check = result_mapping.get("pipeline_check")
        pipeline_check_mapping = dict(pipeline_check) if isinstance(pipeline_check, Mapping) else {}
        input_contract = pipeline_check_mapping.get("input_contract")
        input_contract_mapping = dict(input_contract) if isinstance(input_contract, Mapping) else {}
        input_decision = input_contract_mapping.get("input_decision")
        input_decision_mapping = dict(input_decision) if isinstance(input_decision, Mapping) else {}
        needs_input_items = list(
            input_decision_mapping.get("needs_input_items")
            or input_decision_mapping.get("question_items")
            or []
        )
    fields: List[str] = []
    for item in needs_input_items:
        if not isinstance(item, Mapping):
            continue
        field = str(item.get("field") or "").strip()
        if field and field not in fields:
            fields.append(field)
    return fields


def _summarize_latest_generation_quality_report(path: Path) -> Dict[str, Any]:
    payload = _read_historical_compare_payload(path)
    output_guard = dict(payload.get("output_guard") or {})
    final_quality_eval = dict(payload.get("final_quality_eval") or {})
    failure_parameters = dict(payload.get("failure_parameters") or {})
    runtime_reason_code = str(
        failure_parameters.get("runtime_reason_code")
        or output_guard.get("reason_code")
        or payload.get("runtime_reason_code")
        or ""
    )
    hard_failed = bool(final_quality_eval.get("hard_failed", False))
    blocked = bool(output_guard.get("blocked", False) or hard_failed or failure_parameters.get("has_failure", False))
    return {
        "target_id": "latest_generation_quality_report",
        "artifact_kind": "quality_report",
        "source_path": str(path),
        "available": bool(payload),
        "result_type": "quality_report",
        "success": not blocked,
        "reason_code": runtime_reason_code,
        "runtime_error_class": str(
            failure_parameters.get("runtime_error_class")
            or output_guard.get("error_class")
            or ""
        ),
        "quality_gate": "blocked" if blocked else "passed",
        "soft_warning_count": int(
            output_guard.get("soft_warning_count")
            or final_quality_eval.get("soft_warning_count")
            or 0
        ),
        "compare_eligible": bool(payload),
        "compare_reason": "quality_report_available" if payload else "quality_report_missing",
    }


def _summarize_ad_hoc_quality_compare(path: Path) -> Dict[str, Any]:
    payload = _read_historical_compare_payload(path)
    runs = dict(payload.get("runs") or {})
    prompt_only_runs = [item for item in list(runs.get("prompt_only") or []) if isinstance(item, Mapping)]
    algorithm_runs = [item for item in list(runs.get("algorithm") or []) if isinstance(item, Mapping)]
    algorithm_ok_repeat_count = sum(
        1 for item in algorithm_runs if str(item.get("reason_code") or "").strip() == "OK"
    )
    prompt_only_titled_repeat_count = sum(
        1 for item in prompt_only_runs if str(item.get("title") or "").strip()
    )
    has_compare_runs = bool(prompt_only_runs or algorithm_runs)
    return {
        "target_id": "ad_hoc_quality_compare",
        "artifact_kind": "repeat_compare_summary",
        "source_path": str(path),
        "available": bool(payload),
        "result_type": "repeat_compare_artifact",
        "success": has_compare_runs,
        "reason_code": "OK" if algorithm_ok_repeat_count else "",
        "runtime_error_class": "",
        "compare_eligible": has_compare_runs,
        "compare_reason": (
            "repeat_compare_artifact_available" if has_compare_runs else "repeat_compare_artifact_missing"
        ),
        "case_id": str(payload.get("case_id") or ""),
        "prompt_only_repeat_count": len(prompt_only_runs),
        "prompt_only_titled_repeat_count": prompt_only_titled_repeat_count,
        "algorithm_repeat_count": len(algorithm_runs),
        "algorithm_ok_repeat_count": algorithm_ok_repeat_count,
    }


def _summarize_direct_prompt_only_probe(path: Path) -> Dict[str, Any]:
    payload = _read_historical_compare_payload(path)
    call_metadata = dict(payload.get("call_metadata") or {})
    output = str(payload.get("output") or "").strip()
    output_lines = [line.strip() for line in output.splitlines() if line.strip()]
    return {
        "target_id": "direct_gpt54_prompt_only_same_source",
        "artifact_kind": "prompt_only_probe",
        "source_path": str(path),
        "available": bool(payload),
        "result_type": "content_generation_result",
        "success": bool(output),
        "reason_code": str(call_metadata.get("last_reason_code") or "OK"),
        "runtime_error_class": str(call_metadata.get("last_error_class") or ""),
        "compare_eligible": bool(output),
        "compare_reason": "prompt_only_content_available" if output else "prompt_only_content_missing",
        "selected_model": str(call_metadata.get("selected_model") or payload.get("model") or ""),
        "output_chars": len(output),
        "title_preview": output_lines[0] if output_lines else "",
    }


def _summarize_prompt_only_probe(path: Path, *, force_accept: bool) -> Dict[str, Any]:
    payload = _read_historical_compare_payload(path)
    result_summary = dict(payload.get("result_summary") or {})
    result = dict(payload.get("result") or {})
    reason_code = str(
        result_summary.get("reason_code")
        or result.get("runtime_reason_code")
        or result.get("reason_code")
        or ""
    )
    runtime_error_class = str(
        result_summary.get("runtime_error_class")
        or result.get("runtime_error_class")
        or ""
    )
    full_text = str(result.get("full_text") or "").strip()
    if reason_code.startswith(("INP_", "SEC_")) or runtime_error_class == "user_input":
        result_type = "input_contract_block"
        compare_eligible = False
        compare_reason = (
            "input_contract_block_persisted_after_override"
            if force_accept
            else "input_contract_blocked_before_generation"
        )
    elif bool(result_summary.get("success", result.get("success", False))) or full_text:
        result_type = "content_generation_result"
        compare_eligible = True
        compare_reason = "prompt_only_content_available"
    else:
        result_type = "content_generation_failure"
        compare_eligible = True
        compare_reason = "content_generation_failed"
    return {
        "target_id": (
            "prompt_only_probe_same_source_force_accept"
            if force_accept
            else "prompt_only_probe_same_source"
        ),
        "artifact_kind": "prompt_only_probe",
        "source_path": str(path),
        "available": bool(payload),
        "result_type": result_type,
        "success": bool(result_summary.get("success", result.get("success", False))),
        "reason_code": reason_code,
        "runtime_error_class": runtime_error_class,
        "compare_eligible": compare_eligible,
        "compare_reason": compare_reason,
        "missing_input_fields": _extract_historical_needs_input_fields(payload),
        "full_text_chars": len(full_text),
        "force_accept_override": force_accept,
    }


def _build_current_proposal_compare_summary(results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    experimental_items = []
    for item in results:
        if not isinstance(item, Mapping):
            continue
        body_generation_summary = item.get("body_generation_summary")
        if not isinstance(body_generation_summary, Mapping):
            continue
        if str(body_generation_summary.get("experiment") or "").strip():
            experimental_items.append((item, dict(body_generation_summary)))
    case_ids = [str(item.get("case_id") or "") for item, _ in experimental_items if str(item.get("case_id") or "").strip()]
    compare_ready_case_ids = [
        str(item.get("case_id") or "")
        for item, summary in experimental_items
        if bool(summary.get("compare_ready", False)) and str(item.get("case_id") or "").strip()
    ]
    run_states = sorted(
        {
            str(summary.get("run_state") or "").strip()
            for _, summary in experimental_items
            if str(summary.get("run_state") or "").strip()
        }
    )
    audit_verdicts = sorted(
        {
            str(summary.get("audit_verdict") or "").strip()
            for _, summary in experimental_items
            if str(summary.get("audit_verdict") or "").strip()
        }
    )
    next_actions = sorted(
        {
            str(summary.get("next_action") or "").strip()
            for _, summary in experimental_items
            if str(summary.get("next_action") or "").strip()
        }
    )
    compare_reason_values = sorted(
        {
            str(summary.get("compare_reason") or "").strip()
            for _, summary in experimental_items
            if str(summary.get("compare_reason") or "").strip()
        }
    )
    return {
        "experimental_case_count": len(experimental_items),
        "case_ids": case_ids,
        "compare_ready_case_ids": compare_ready_case_ids,
        "compare_ready": bool(experimental_items) and len(compare_ready_case_ids) == len(experimental_items),
        "run_states": run_states,
        "audit_verdicts": audit_verdicts,
        "next_actions": next_actions,
        "compare_reason_values": compare_reason_values,
    }


def _build_historical_compare_summary(results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    targets = [
        _summarize_latest_generation_quality_report(
            _HISTORICAL_COMPARE_ARTIFACT_PATHS["latest_generation_quality_report"]
        ),
        _summarize_ad_hoc_quality_compare(_HISTORICAL_COMPARE_ARTIFACT_PATHS["ad_hoc_quality_compare"]),
        _summarize_direct_prompt_only_probe(
            _HISTORICAL_COMPARE_ARTIFACT_PATHS["direct_gpt54_prompt_only_same_source"]
        ),
        _summarize_prompt_only_probe(
            _HISTORICAL_COMPARE_ARTIFACT_PATHS["prompt_only_probe_same_source"],
            force_accept=False,
        ),
        _summarize_prompt_only_probe(
            _HISTORICAL_COMPARE_ARTIFACT_PATHS["prompt_only_probe_same_source_force_accept"],
            force_accept=True,
        ),
    ]
    missing_target_ids = [item["target_id"] for item in targets if not bool(item.get("available", False))]
    input_contract_block_target_ids = [
        item["target_id"] for item in targets if str(item.get("result_type") or "") == "input_contract_block"
    ]
    content_generation_target_ids = [
        item["target_id"] for item in targets if str(item.get("result_type") or "") == "content_generation_result"
    ]
    content_failure_target_ids = [
        item["target_id"] for item in targets if str(item.get("result_type") or "") == "content_generation_failure"
    ]
    explanation_points: List[str] = []
    if "prompt_only_probe_same_source" in input_contract_block_target_ids:
        explanation_points.append(
            "prompt_only_probe_same_source is an input-contract block with INP_MISSING_REQUIRED, not a content-quality loss."
        )
    if "prompt_only_probe_same_source_force_accept" in input_contract_block_target_ids:
        explanation_points.append(
            "prompt_only_probe_same_source_force_accept stays blocked after override, so the failure remains pre-generation."
        )
    if "direct_gpt54_prompt_only_same_source" in content_generation_target_ids:
        explanation_points.append(
            "direct_gpt54_prompt_only_same_source is the prompt-only content-generation reference because it produced article output."
        )
    latest_quality = next(
        (item for item in targets if item["target_id"] == "latest_generation_quality_report"),
        {},
    )
    if latest_quality:
        explanation_points.append(
            "latest_generation_quality_report captures the current visible baseline quality state for historical comparison."
        )
    return {
        "enabled": True,
        "current_proposal": _build_current_proposal_compare_summary(results),
        "historical_targets": targets,
        "target_counts": {
            "loaded": len(targets) - len(missing_target_ids),
            "missing": len(missing_target_ids),
            "input_contract_blocks": len(input_contract_block_target_ids),
            "content_generation_results": len(content_generation_target_ids),
            "content_generation_failures": len(content_failure_target_ids),
        },
        "readiness": {
            "historical_compare_readable": len(missing_target_ids) == 0,
            "distinguishes_input_contract_failure": bool(input_contract_block_target_ids)
            and bool(content_generation_target_ids or content_failure_target_ids),
        },
        "missing_target_ids": missing_target_ids,
        "input_contract_block_target_ids": input_contract_block_target_ids,
        "content_generation_target_ids": content_generation_target_ids,
        "content_failure_target_ids": content_failure_target_ids,
        "explanation_points": explanation_points,
    }


def _build_promotion_gate_summary(
    results: Sequence[Mapping[str, Any]],
    historical_compare: Mapping[str, Any],
) -> Dict[str, Any]:
    current_proposal = dict(historical_compare.get("current_proposal") or {})
    readiness = dict(historical_compare.get("readiness") or {})
    measured_checks = {
        "experiment_propagation_visible": int(current_proposal.get("experimental_case_count", 0) or 0) > 0,
        "success_visibility_ready": bool(current_proposal.get("compare_ready", False)),
        "historical_compare_readable": bool(readiness.get("historical_compare_readable", False)),
        "historical_compare_distinguishes_failures": bool(
            readiness.get("distinguishes_input_contract_failure", False)
        ),
    }
    missing_checks = [name for name, passed in measured_checks.items() if not passed]
    external_checks = ["targeted_tests_pass", "shared_checks_pass"]
    return {
        "switch_condition": "promotion_gate_pass_only",
        "default_flip_allowed": False,
        "next_action": "hold_default_route" if not missing_checks else "fix_measured_gate_failures",
        "measured_checks": measured_checks,
        "missing_checks": missing_checks,
        "external_checks_required": external_checks,
        "unverified_checks": list(external_checks),
        "case_count": len(results),
    }


def _write_historical_compare_artifact(
    *,
    artifact_dir: Path,
    historical_compare: Mapping[str, Any],
) -> str:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "historical_compare_summary.json"
    artifact_path.write_text(
        json.dumps(dict(historical_compare or {}), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(artifact_path)


def _build_runtime_summary(result: Mapping[str, Any]) -> Dict[str, Any]:
    runtime = _extract_runtime_details(result)
    return {
        "primary_model": str(runtime.get("primary_model") or ""),
        "selected_model": str(runtime.get("selected_model") or ""),
        "base_model": str(runtime.get("base_model") or ""),
        "model_source": str(runtime.get("model_source") or ""),
        "task_type": str(runtime.get("task_type") or ""),
        "effective_reasoning_effort": str(runtime.get("effective_reasoning_effort") or ""),
        "effective_temperature": runtime.get("effective_temperature"),
        "effective_top_p": runtime.get("effective_top_p"),
        "effective_presence_penalty": runtime.get("effective_presence_penalty"),
        "effective_frequency_penalty": runtime.get("effective_frequency_penalty"),
        "effective_verbosity": str(runtime.get("effective_verbosity") or ""),
        "compatibility_suppressed_params": _normalize_string_list(
            runtime.get("compatibility_suppressed_params"),
            max_items=8,
        ),
        "same_model_retry_count": int(runtime.get("same_model_retry_count", 0) or 0),
        "retry_events": _extract_runtime_retry_events(runtime),
        "last_retry_event": str(runtime.get("last_retry_event") or ""),
        "model_fallback_attempted": bool(runtime.get("model_fallback_attempted", False)),
        "model_fallback_blocked": bool(runtime.get("model_fallback_blocked", False)),
        "last_error_class": str(runtime.get("last_error_class") or ""),
        "last_reason_code": str(
            runtime.get("last_reason_code")
            or result.get("runtime_reason_code")
            or result.get("reason_code")
            or ""
        ),
        "execution_mode": str(runtime.get("execution_mode") or ""),
    }


def _build_probe_summary(
    *,
    success: bool,
    task_type: str,
    runtime: Mapping[str, Any],
    reason_code: str,
    message: str = "",
    response_preview: str = "",
) -> Dict[str, Any]:
    return {
        "success": bool(success),
        "task_type": str(task_type or ""),
        "selected_model": str(runtime.get("selected_model") or runtime.get("primary_model") or ""),
        "base_model": str(runtime.get("base_model") or ""),
        "model_source": str(runtime.get("model_source") or ""),
        "same_model_retry_count": int(runtime.get("same_model_retry_count", 0) or 0),
        "last_error_class": str(runtime.get("last_error_class") or ""),
        "reason_code": str(reason_code or runtime.get("last_reason_code") or ""),
        "execution_mode": str(runtime.get("execution_mode") or ""),
        "message": str(message or ""),
        "response_preview": str(response_preview or "")[:80],
    }


def _run_live_llm_probe(llm_client: LLMClient, *, task_type: str) -> Dict[str, Any]:
    try:
        response = llm_client.generate_text(
            LIVE_PREFLIGHT_PROMPT,
            max_tokens=24,
            task_type=task_type,
        ).strip()
        runtime = dict(llm_client.get_last_call_metadata() or {})
        return _build_probe_summary(
            success=True,
            task_type=task_type,
            runtime=runtime,
            reason_code=str(runtime.get("last_reason_code") or "OK"),
            response_preview=response,
        )
    except Exception as exc:
        runtime = dict(getattr(exc, "call_metadata", {}) or {})
        if not runtime:
            getter = getattr(llm_client, "get_last_call_metadata", None)
            if callable(getter):
                value = getter()
                if isinstance(value, dict):
                    runtime = dict(value)
        return _build_probe_summary(
            success=False,
            task_type=task_type,
            runtime=runtime,
            reason_code=str(
                getattr(exc, "reason_code", "")
                or runtime.get("last_reason_code")
                or "SYS_PRIMARY_MODEL_RETRY_EXHAUSTED"
            ),
            message=str(exc),
        )


def _is_connection_like_probe(probe: Mapping[str, Any]) -> bool:
    reason_code = str(probe.get("reason_code") or "")
    error_class = str(probe.get("last_error_class") or "")
    message = str(probe.get("message") or "").lower()
    if error_class in {"network_reset", "timeout"}:
        return True
    if reason_code in {"TRN_PRIMARY_MODEL_NETWORK_RESET", "TRN_PRIMARY_MODEL_TIMEOUT"}:
        return True
    return any(
        token in message
        for token in (
            "connection error",
            "connection reset",
            "network reset",
            "timed out",
            "timeout",
            "getaddrinfo",
            "name resolution",
            "dns",
        )
    )


def _is_validation_runtime_config_probe(probe: Mapping[str, Any]) -> bool:
    reason_code = str(probe.get("reason_code") or "")
    message = str(probe.get("message") or "").lower()
    if reason_code.startswith(("INP_", "SEC_")):
        return True
    return any(
        token in message
        for token in (
            "invalid api key",
            "authentication",
            "unauthorized",
            "forbidden",
            "model not found",
            "unknown model",
            "does not exist",
            "invalid parameter",
            "unsupported parameter",
            "bad request",
            " 400",
            " 401",
            " 403",
            " 404",
        )
    )


def run_live_preflight(llm_client: LLMClient) -> Dict[str, Any]:
    section_probe = _run_live_llm_probe(llm_client, task_type="section")
    if bool(section_probe.get("success", False)):
        return {
            "mode": "live",
            "passed": True,
            "blocker_owner": "",
            "section_probe": section_probe,
            "base_probe": {"skipped": True, "reason": "section_probe_passed"},
        }
    base_probe = _run_live_llm_probe(llm_client, task_type="article")
    if bool(base_probe.get("success", False)):
        blocker_owner = "section_model_availability"
    elif _is_connection_like_probe(section_probe) or _is_connection_like_probe(base_probe):
        blocker_owner = "environment_connectivity"
    elif _is_validation_runtime_config_probe(section_probe) or _is_validation_runtime_config_probe(base_probe):
        blocker_owner = "validation_runtime_config"
    else:
        blocker_owner = "runtime_unknown"
    return {
        "mode": "live",
        "passed": False,
        "blocker_owner": blocker_owner,
        "section_probe": section_probe,
        "base_probe": base_probe,
    }


def _build_long_form_case_gate(
    case: UISweepCase,
    short_gate: Mapping[str, Any],
    result: Mapping[str, Any],
) -> Dict[str, Any]:
    metrics = _extract_quality_metrics(result)
    reasons: List[str] = []
    if not bool(short_gate.get("passed", False)):
        reasons.extend(str(item) for item in list(short_gate.get("failures") or [])[:8])
    topic_echo_body_only_ratio = _safe_float(metrics.get("topic_echo_body_only_ratio"))
    if topic_echo_body_only_ratio is not None and topic_echo_body_only_ratio >= 0.28:
        reasons.append(f"topic_echo_body_only_ratio={round(topic_echo_body_only_ratio, 4)}")
    section_opening_repetition_count = int(metrics.get("section_opening_repetition_count", 0) or 0)
    if section_opening_repetition_count > 1:
        reasons.append(f"section_opening_repetition_count={section_opening_repetition_count}")
    if case.article_type == "announcement":
        invalid_modal = int(metrics.get("announcement_invalid_modal_pattern_count", 0) or 0)
        if invalid_modal > 0:
            reasons.append(f"announcement_invalid_modal_pattern_count={invalid_modal}")
    if case.article_type == "case_study":
        condition_sentence_count = int(metrics.get("case_result_condition_sentence_count", 0) or 0)
        if condition_sentence_count < 1:
            reasons.append("case_result_condition_sentence_count<1")
    return {
        "passed": len(reasons) == 0,
        "reasons": reasons,
    }


def _build_battery_policy(*, live: bool, case_count: int) -> Dict[str, Any]:
    return {
        "version": SHORT_BATTERY_VERSION,
        "case_count": int(case_count),
        "rubric_axes": list(SHORT_BATTERY_RUBRIC_AXES),
        "hard_fail_rules": list(SHORT_BATTERY_HARD_FAIL_RULES),
        "long_form_go_no_go_rules": list(SHORT_BATTERY_LONG_FORM_GO_NO_GO_RULES),
        "baseline_variant_compare_points": list(SHORT_BATTERY_BASELINE_VARIANT_COMPARE_POINTS),
        "live_execution_reason": SHORT_BATTERY_LIVE_EXECUTION_REASON if live else "",
    }


def _build_runtime_contract_rollup(results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    selected_models = sorted(
        {
            str(((item.get("runtime_summary") or {}).get("selected_model") or "")).strip()
            for item in results
            if str(((item.get("runtime_summary") or {}).get("selected_model") or "")).strip()
        }
    )
    model_sources = sorted(
        {
            str(((item.get("runtime_summary") or {}).get("model_source") or "")).strip()
            for item in results
            if str(((item.get("runtime_summary") or {}).get("model_source") or "")).strip()
        }
    )
    reasoning_efforts = sorted(
        {
            str(((item.get("runtime_summary") or {}).get("effective_reasoning_effort") or "")).strip()
            for item in results
            if str(((item.get("runtime_summary") or {}).get("effective_reasoning_effort") or "")).strip()
        }
    )
    verbosity_values = sorted(
        {
            str(((item.get("runtime_summary") or {}).get("effective_verbosity") or "")).strip()
            for item in results
            if str(((item.get("runtime_summary") or {}).get("effective_verbosity") or "")).strip()
        }
    )
    non_null_temperatures = sorted(
        {
            str((item.get("runtime_summary") or {}).get("effective_temperature"))
            for item in results
            if (item.get("runtime_summary") or {}).get("effective_temperature") is not None
        }
    )
    non_null_top_p = sorted(
        {
            str((item.get("runtime_summary") or {}).get("effective_top_p"))
            for item in results
            if (item.get("runtime_summary") or {}).get("effective_top_p") is not None
        }
    )
    retry_case_ids = [
        str(item.get("case_id") or "")
        for item in results
        if _has_material_runtime_retry(dict(item.get("runtime_summary") or {}))
    ]
    fallback_case_ids = [
        str(item.get("case_id") or "")
        for item in results
        if bool((item.get("runtime_summary") or {}).get("model_fallback_attempted", False))
    ]
    return {
        "selected_models": selected_models,
        "model_sources": model_sources,
        "effective_reasoning_efforts": reasoning_efforts,
        "effective_verbosity_values": verbosity_values,
        "all_temperature_suppressed": len(non_null_temperatures) == 0,
        "all_top_p_suppressed": len(non_null_top_p) == 0,
        "non_null_effective_temperature_values": non_null_temperatures,
        "non_null_effective_top_p_values": non_null_top_p,
        "retry_case_ids": retry_case_ids,
        "fallback_case_ids": fallback_case_ids,
    }


def _build_battery_summary(results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    case_count = len(results)
    short_gate_passed_count = sum(
        1 for item in results if bool(dict(item.get("short_gate") or {}).get("passed", False))
    )
    rubric_totals = [int(dict(item.get("rubric") or {}).get("total_score", 0) or 0) for item in results]
    long_form_blockers = [
        {
            "case_id": str(item.get("case_id") or ""),
            "reasons": list(dict(item.get("long_form_case_gate") or {}).get("reasons") or []),
        }
        for item in results
        if not bool(dict(item.get("long_form_case_gate") or {}).get("passed", False))
    ]
    go_no_go_reasons: List[str] = []
    if short_gate_passed_count != case_count:
        go_no_go_reasons.append(f"short_gate_passed={short_gate_passed_count}/{case_count}")
    if long_form_blockers:
        go_no_go_reasons.append(f"case_threshold_failures={len(long_form_blockers)}")
    rubric_mean_total = round(sum(rubric_totals) / len(rubric_totals), 2) if rubric_totals else 0.0
    if rubric_totals and rubric_mean_total < 8.0:
        go_no_go_reasons.append(f"rubric_mean_total={rubric_mean_total}<8.0")
    return {
        "version": SHORT_BATTERY_VERSION,
        "case_count": case_count,
        "short_gate_passed_count": short_gate_passed_count,
        "hard_fail_case_ids": [
            str(item.get("case_id") or "")
            for item in results
            if not bool(dict(item.get("short_gate") or {}).get("passed", False))
        ],
        "rubric_mean_total": rubric_mean_total,
        "rubric_min_total": min(rubric_totals) if rubric_totals else 0,
        "rubric_case_totals": [
            {
                "case_id": str(item.get("case_id") or ""),
                "total_score": int(dict(item.get("rubric") or {}).get("total_score", 0) or 0),
            }
            for item in results
        ],
        "runtime_contract": _build_runtime_contract_rollup(results),
        "long_form_blockers": long_form_blockers,
        "go_for_long_form": len(go_no_go_reasons) == 0,
        "go_no_go_reasons": go_no_go_reasons,
    }


def _write_case_artifacts(
    *,
    artifact_dir: Path,
    case: UISweepCase,
    contract: Mapping[str, Any],
    result: Mapping[str, Any],
    prompt_echo_hits: Sequence[str],
    short_gate: Mapping[str, Any],
    contract_summary: Mapping[str, Any],
    quality_read: Mapping[str, Any],
    rubric: Mapping[str, Any],
    comparative_stability: Mapping[str, Any],
    long_form_case_gate: Mapping[str, Any],
    review_checklist: Sequence[str],
    runtime_summary: Mapping[str, Any],
) -> Dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_base = artifact_dir / str(case.case_id or "case")
    json_path = artifact_base.with_suffix(".json")
    text_path = artifact_base.with_suffix(".txt")
    pipeline_check = dict(result.get("pipeline_check") or {})
    body_generation_summary = _extract_body_generation_summary(result)
    json_payload = {
        "case_id": case.case_id,
        "note": case.note,
        "selections": _build_selection_summary(case),
        "contract": dict(contract or {}),
        "success": bool(result.get("success", False)),
        "reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or ""),
        "runtime_summary": dict(runtime_summary or {}),
        "prompt_echo_hits": list(prompt_echo_hits),
        "short_gate": dict(short_gate or {}),
        "contract_summary": dict(contract_summary or {}),
        "quality_read": dict(quality_read or {}),
        "rubric": dict(rubric or {}),
        "comparative_stability": dict(comparative_stability or {}),
        "long_form_case_gate": dict(long_form_case_gate or {}),
        "long_review_checklist": list(review_checklist),
        "body_generation_summary": dict(body_generation_summary or {}),
        "pipeline_check": dict(pipeline_check),
        "result": {
            "title": str(result.get("title", "") or ""),
            "lead": str(result.get("lead", "") or ""),
            "body": str(result.get("body", "") or ""),
            "full_text": str(result.get("full_text", "") or ""),
            "pipeline_source": str(result.get("pipeline_source") or ""),
            "runtime_reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or ""),
            "runtime_error_class": str(result.get("runtime_error_class") or ""),
            "pipeline_check": dict(pipeline_check),
        },
    }
    text_payload = str(result.get("full_text", "") or "").strip()
    if not text_payload:
        text_payload = "\n\n".join(
            segment
            for segment in (
                str(result.get("title", "") or "").strip(),
                str(result.get("lead", "") or "").strip(),
                str(result.get("body", "") or "").strip(),
            )
            if segment
        ).strip()
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    text_path.write_text(text_payload, encoding="utf-8")
    return {
        "json": str(json_path),
        "text": str(text_path),
    }


def run_ui_sweep_cases(
    cases: Sequence[UISweepCase],
    *,
    live: bool = False,
    artifact_dir: str | Path | None = None,
) -> Dict[str, Any]:
    artifact_root = Path(artifact_dir) if artifact_dir else None
    llm_client = LLMClient() if live else None
    preflight = {
        "mode": "offline",
        "passed": True,
        "skipped": True,
    }
    if live and llm_client is not None:
        preflight = run_live_preflight(llm_client)
        if not bool(preflight.get("passed", False)):
            historical_compare = _build_historical_compare_summary([])
            promotion_gate = _build_promotion_gate_summary([], historical_compare)
            payload = {
                "live": True,
                "matrix": "ui_short_sweep",
                "matrix_status": "blocked_preflight",
                "preflight": preflight,
                "battery_policy": _build_battery_policy(live=True, case_count=len(cases)),
                "coverage": summarize_short_matrix_coverage(cases),
                "length_coverage_after_promotion": summarize_all_phase_length_coverage(cases),
                "historical_compare": historical_compare,
                "promotion_gate": promotion_gate,
                "results": [],
            }
            if artifact_root is not None:
                payload["artifact_dir"] = str(artifact_root)
                payload["historical_compare_artifact_path"] = _write_historical_compare_artifact(
                    artifact_dir=artifact_root,
                    historical_compare=historical_compare,
                )
            return payload
    pipeline = MinimalPipeline(llm_client=llm_client)
    results: List[Dict[str, Any]] = []
    for case in cases:
        execution_case = case if live else replace(case, strict_saas_mode="small")
        contract = build_current_mainline_payload(execution_case)
        result = execute_current_mainline_generation(pipeline, contract, contract["prompt_raw"])
        prompt_echo_hits = _collect_prompt_echo_hits(result, contract.get("prompt_raw", ""))
        short_gate = _evaluate_short_gate(result, prompt_echo_hits)
        review_checklist = LONG_FORM_REVIEW_CHECKLIST_BY_ARTICLE_TYPE.get(
            case.article_type,
            LONG_FORM_REVIEW_CHECKLIST_BY_ARTICLE_TYPE["default"],
        )
        runtime_summary = _build_runtime_summary(result)
        contract_summary = _build_contract_summary(result)
        quality_read = _build_quality_read_summary(result, prompt_echo_hits)
        rubric = _build_rubric_summary(case, result, prompt_echo_hits)
        comparative_stability = _build_comparative_stability_summary(case, result, rubric)
        long_form_case_gate = _build_long_form_case_gate(case, short_gate, result)
        body_generation_summary = _extract_body_generation_summary(result)
        pipeline_check = dict(result.get("pipeline_check") or {})
        item = {
            "case_id": case.case_id,
            "note": case.note,
            "selections": _build_selection_summary(case),
            "execution": {
                "live": bool(live),
                "executed_strict_saas_mode": normalize_strict_saas_mode(execution_case.strict_saas_mode),
            },
            "success": bool(result.get("success", False)),
            "reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or ""),
            "pipeline_source": str(result.get("pipeline_source") or ""),
            "runtime_summary": runtime_summary,
            "short_gate": short_gate,
            "prompt_echo_hits": list(prompt_echo_hits),
            "output_guard": {
                "blocked": bool(extract_existing_output_guard(result).get("blocked", False)),
                "reason_code": str(extract_existing_output_guard(result).get("reason_code") or ""),
                "soft_warning_count": int(extract_existing_output_guard(result).get("soft_warning_count", 0) or 0),
            },
            "metrics": _build_metric_summary(result),
            "contract_summary": contract_summary,
            "quality_read": quality_read,
            "rubric": rubric,
            "comparative_stability": comparative_stability,
            "long_form_case_gate": long_form_case_gate,
            "long_review_watch_items": _build_long_watch_items(result, prompt_echo_hits, case.article_type),
            "long_review_checklist": list(review_checklist),
            "body_generation_summary": body_generation_summary,
            "pipeline_check": pipeline_check,
            "artifact_path": "",
            "artifact_text_path": "",
        }
        if artifact_root is not None:
            artifact_paths = _write_case_artifacts(
                artifact_dir=artifact_root,
                case=case,
                contract=contract,
                result=result,
                prompt_echo_hits=prompt_echo_hits,
                short_gate=short_gate,
                contract_summary=contract_summary,
                quality_read=quality_read,
                rubric=rubric,
                comparative_stability=comparative_stability,
                long_form_case_gate=long_form_case_gate,
                review_checklist=review_checklist,
                runtime_summary=runtime_summary,
            )
            item["artifact_path"] = artifact_paths["json"]
            item["artifact_text_path"] = artifact_paths["text"]
        results.append(item)
    historical_compare = _build_historical_compare_summary(results)
    promotion_gate = _build_promotion_gate_summary(results, historical_compare)
    payload = {
        "live": bool(live),
        "matrix": "ui_short_sweep",
        "matrix_status": "ready",
        "preflight": preflight,
        "battery_policy": _build_battery_policy(live=bool(live), case_count=len(cases)),
        "battery_summary": _build_battery_summary(results),
        "coverage": summarize_short_matrix_coverage(cases),
        "length_coverage_after_promotion": summarize_all_phase_length_coverage(cases),
        "historical_compare": historical_compare,
        "promotion_gate": promotion_gate,
        "results": results,
    }
    if artifact_root is not None:
        payload["artifact_dir"] = str(artifact_root)
        payload["historical_compare_artifact_path"] = _write_historical_compare_artifact(
            artifact_dir=artifact_root,
            historical_compare=historical_compare,
        )
    return payload


def build_promoted_long_cases(short_results: Mapping[str, Any], cases: Sequence[UISweepCase]) -> Dict[str, Any]:
    if str(short_results.get("matrix_status") or "ready") == "blocked_preflight":
        preflight = dict(short_results.get("preflight") or {})
        return {
            "promoted_cases": [],
            "skipped": [],
            "promotion_blocked": True,
            "block_reason": "short_matrix_blocked_preflight",
            "blocker_owner": str(preflight.get("blocker_owner") or ""),
        }
    battery_summary = dict(short_results.get("battery_summary") or {})
    if battery_summary and not bool(battery_summary.get("go_for_long_form", False)):
        return {
            "promoted_cases": [],
            "skipped": list(battery_summary.get("long_form_blockers") or []),
            "promotion_blocked": True,
            "block_reason": "short_battery_no_go",
            "blocker_owner": "note.current_mainline_ui_matrix.short_battery",
        }
    by_case_id = {case.case_id: case for case in cases}
    promoted: List[UISweepCase] = []
    skipped: List[Dict[str, Any]] = []
    for item in list(short_results.get("results", []) or []):
        if not isinstance(item, dict):
            continue
        case_id = str(item.get("case_id") or "").strip()
        base_case = by_case_id.get(case_id)
        if base_case is None:
            continue
        short_gate = dict(item.get("short_gate", {}) or {})
        if not bool(short_gate.get("passed", False)):
            skipped.append({"case_id": case_id, "reason": "short_gate_failed"})
            continue
        promoted_length = LONG_FORM_PROMOTION_LENGTH_BY_ARTICLE_TYPE.get(base_case.article_type, "")
        if not promoted_length:
            skipped.append({"case_id": case_id, "reason": "promotion_length_missing"})
            continue
        promoted.append(
            replace(
                base_case,
                case_id=f"{base_case.case_id}-promoted-{promoted_length}",
                length_mode_key=promoted_length,
                note=f"promoted_from={base_case.case_id}",
            )
        )
    return {
        "promoted_cases": promoted,
        "skipped": skipped,
        "promotion_blocked": False,
        "block_reason": "",
        "blocker_owner": "",
    }


def summarize_promoted_case_ids(cases: Iterable[UISweepCase]) -> List[str]:
    return [case.case_id for case in cases]
