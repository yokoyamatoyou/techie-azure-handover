from __future__ import annotations

import re
from typing import Any


ROUTE_V_GENRES = {
    "market_explanation",
    "company_service_intro",
    "announcement",
    "case_study",
    "comparison_guide",
    "daily_activity",
}
LOCAL_RENDERER_FINGERPRINTS = (
    (
        "generic_local_opening",
        "style_mismatch",
        "私たちの取り組みを、少し具体的に紹介します。",
        "local deterministic opening text remains in the final human-visible article",
    ),
    (
        "generic_local_opening",
        "style_mismatch",
        "私たちが取り組んでいることを、少し具体的に紹介します。",
        "local deterministic opening text remains in the final human-visible article",
    ),
    (
        "generic_local_opening",
        "style_mismatch",
        "当社の取り組みを、少し具体的に紹介します。",
        "local deterministic opening text remains in the final human-visible article",
    ),
    (
        "unrelated_local_cta",
        "cta_issue",
        "データの扱いに迷ったときは、小さなことでもご相談ください",
        "local deterministic CTA remains in a final article where it is not source-specific",
    ),
)
SPACED_SOURCE_TEXT_RE = re.compile(
    r"(?:[A-Za-z0-9０-９一-龯ぁ-んァ-ン]\s+){5,}[A-Za-z0-9０-９一-龯ぁ-んァ-ン]"
)


def is_human_visible_surface_gate_enabled(article_brief: dict[str, Any] | None) -> bool:
    brief = _unwrap_brief(article_brief)
    genre_id = str(brief.get("genre_id") or "")
    if genre_id == "case_study":
        return True
    if genre_id not in ROUTE_V_GENRES:
        return False
    return _has_route_v_surface_contract_marker(brief)


def check_human_visible_surface(
    article_text: str,
    article_brief: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = str(article_text or "")
    enabled = True if article_brief is None else is_human_visible_surface_gate_enabled(article_brief)
    findings = _find_surface_issues(text) if enabled else []
    return {
        "human_visible_surface_gate": {
            "pass": not findings,
            "enabled_for_brief": enabled,
            "findings": findings,
        }
    }


def surface_gate_quality_issues(article_text: str) -> list[dict[str, Any]]:
    report = check_human_visible_surface(article_text)
    findings = report["human_visible_surface_gate"]["findings"]
    return [
        {
            "type": finding["issue_type"],
            "severity": finding["severity"],
            "text": finding["text"],
            "reason": finding["reason"],
            "fix_instruction": finding["fix_instruction"],
            "claim_ids": [],
        }
        for finding in findings
    ]


def _find_surface_issues(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    findings.extend(_local_renderer_fingerprint_findings(text))
    findings.extend(_ocr_spaced_source_text_findings(text))
    findings.extend(_dangling_quote_findings(text))
    findings.extend(_duplicate_long_sentence_findings(text))
    return _dedupe_findings(findings)


def _local_renderer_fingerprint_findings(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for code, issue_type, phrase, reason in LOCAL_RENDERER_FINGERPRINTS:
        if phrase not in text:
            continue
        findings.append(
            _finding(
                code=code,
                issue_type=issue_type,
                severity="high",
                text=phrase,
                reason=reason,
                fix_instruction="treat the artifact as not user-visible release-ready until this local-stage surface is removed by the responsible generation/editing owner",
            )
        )
    return findings


def _ocr_spaced_source_text_findings(text: str) -> list[dict[str, str]]:
    match = SPACED_SOURCE_TEXT_RE.search(text)
    if not match:
        return []
    return [
        _finding(
            code="ocr_spaced_source_text",
            issue_type="formatting_mismatch",
            severity="high",
            text=_snippet(match.group(0)),
            reason="OCR-spaced source text remains visible in the final article",
            fix_instruction="block release-readiness and re-enter the responsible source/article surface owner without refetching or patching this generated article",
        )
    ]


def _dangling_quote_findings(text: str) -> list[dict[str, str]]:
    for sentence in _sentences(text):
        if "「" not in sentence:
            continue
        if sentence.count("「") <= sentence.count("」"):
            continue
        return [
            _finding(
                code="dangling_japanese_quote_fragment",
                issue_type="formatting_mismatch",
                severity="high",
                text=_snippet(sentence),
                reason="a Japanese quote opens without a matching close before the visible sentence boundary",
                fix_instruction="block release-readiness and diagnose the upstream source-fragment or editor-output owner",
            )
        ]
    return []


def _duplicate_long_sentence_findings(text: str) -> list[dict[str, str]]:
    seen: dict[str, str] = {}
    for sentence in _sentences(text):
        normalized = _normalize_sentence(sentence)
        if len(normalized) < 14:
            continue
        previous = seen.get(normalized)
        if previous is not None:
            return [
                _finding(
                    code="duplicate_long_sentence",
                    issue_type="duplication",
                    severity="medium",
                    text=_snippet(sentence),
                    reason="a long visible sentence is duplicated in the final article surface",
                    fix_instruction="block release-readiness and diagnose duplicate source-title or local-stage carryover before release",
                )
            ]
        seen[normalized] = sentence
    return []


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.findall(r"[^。！？!?\n]+[。！？!?]?", text) if part.strip()]


def _normalize_sentence(sentence: str) -> str:
    return re.sub(r"\s+", "", sentence).strip("。！？!?「」")


def _dedupe_findings(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for finding in findings:
        key = (finding["code"], finding["text"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


def _finding(
    *,
    code: str,
    issue_type: str,
    severity: str,
    text: str,
    reason: str,
    fix_instruction: str,
) -> dict[str, str]:
    return {
        "code": code,
        "issue_type": issue_type,
        "severity": severity,
        "text": text,
        "reason": reason,
        "fix_instruction": fix_instruction,
    }


def _snippet(text: str, limit: int = 90) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()[:limit]


def _unwrap_brief(article_brief: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(article_brief, dict):
        return {}
    brief = article_brief.get("article_brief")
    return brief if isinstance(brief, dict) else article_brief


def _has_route_v_surface_contract_marker(brief: dict[str, Any]) -> bool:
    try:
        if int(brief.get("body_length_floor_chars") or 0) > 0:
            return True
    except (TypeError, ValueError):
        pass
    return any(
        brief.get(key)
        for key in (
            "source_shape",
            "source_use_mode",
            "paragraph_function_plan",
            "daily_activity_source_role_contract",
            "editor_persona_contract",
        )
    )
