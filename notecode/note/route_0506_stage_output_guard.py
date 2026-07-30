"""Stage-output guard for the route_0506 OpenAI candidate bridge."""
from __future__ import annotations

import copy
import re
from typing import Any, Mapping


ROUTE_0506_ARTICLE_OUTPUT_STAGES = {
    "opening_editor",
    "global_consistency_editor",
    "style_editor",
    "structural_editor",
    "targeted_rewriter",
}

ROUTE_0506_META_REVIEW_MARKERS = (
    "総評として",
    "全体として",
    "一致している点",
    "気になる点",
    "気になった点",
    "要確認",
    "軽微な調整候補",
    "不正確に見えます",
    "briefとの全体整合",
    "未回収",
    "全体の一致度",
    "必要であれば",
    "必要なら",
    "整合性チェック",
    "確認できます",
    "現状のまま",
)

ROUTE_0506_FIRST_PERSON_VARIANTS = ("私たち", "当社", "弊社", "当店")
ROUTE_0506_DEFAULT_FORBIDDEN_VIEWPOINT_TERMS = ("同社", "同サービス", "同店", "同院")
ROUTE_0506_VISIBLE_OUTPUT_CONTRACT_TYPES = {
    "reader_facing_preface",
    "revision_wrapper_heading",
    "markdown_fence",
    "meta_review_output",
}
ROUTE_0506_READER_FACING_PREFACE_PATTERNS = (
    r"^以下[、はの].{0,60}(本文|記事).{0,30}(です|ます|ました|ください)[。.!！]?$",
    r"^(読みやすさ|表現|構成|全体).{0,30}(整え|調整|修正).{0,30}(本文|記事).{0,30}(です|ます|ました)[。.!！]?$",
    r"^(修正後|編集後|調整後)の?(本文|記事).{0,30}(です|ます|ました)?[。.!！]?$",
)


def wrap_route_0506_stage_output_guard(client: Any) -> Any:
    return _Route0506StageOutputGuardClient(client)


class _Route0506StageOutputGuardClient:
    def __init__(self, client: Any) -> None:
        self._client = client
        self.route_0506_stage_output_guard_violations: list[dict[str, Any]] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def generate_structured(
        self,
        stage_name: str,
        instruction: str,
        payload: Mapping[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        return self._client.generate_structured(stage_name, instruction, payload, schema_name)

    def generate_text(self, stage_name: str, instruction: str, payload: Mapping[str, Any]) -> str:
        if stage_name not in ROUTE_0506_ARTICLE_OUTPUT_STAGES:
            return self._client.generate_text(stage_name, instruction, payload)
        previous_article = route_0506_stage_input_article(stage_name, payload)
        guarded_payload = route_0506_enrich_targeted_rewriter_payload(stage_name, payload)
        generated = self._client.generate_text(stage_name, instruction, guarded_payload)
        violations = route_0506_stage_output_article_contract_violations(
            previous_article,
            generated,
            guarded_payload,
        )
        if violations:
            self.route_0506_stage_output_guard_violations.append(
                {
                    "stage_name": stage_name,
                    "violation_types": violations,
                    "visible_output_contract_failed": any(
                        route_0506_is_visible_output_contract_violation_type(violation)
                        for violation in violations
                    ),
                    "previous_char_count": len(previous_article),
                    "generated_char_count": len(str(generated or "").strip()),
                }
            )
            return previous_article
        return generated


def route_0506_stage_input_article(stage_name: str, payload: Mapping[str, Any]) -> str:
    key = "draft" if stage_name == "style_editor" else "article_text"
    return str(payload.get(key) or "").strip()


def route_0506_stage_output_violates_article_contract(
    previous_article: str,
    generated: str,
    payload: Mapping[str, Any] | None = None,
) -> bool:
    return bool(route_0506_stage_output_article_contract_violations(previous_article, generated, payload))


def route_0506_stage_output_article_contract_violations(
    previous_article: str,
    generated: str,
    payload: Mapping[str, Any] | None = None,
) -> list[str]:
    previous = previous_article.strip()
    output = str(generated or "").strip()
    if not previous:
        return []
    if not output:
        return ["empty_output"]
    violations: list[str] = []
    if route_0506_self_perspective_contract_was_lost(previous, output, payload):
        violations.append("self_perspective_contract_lost")
    if looks_like_route_0506_meta_review(output):
        violations.append("meta_review_output")
    violations.extend(route_0506_visible_output_contract_violations(output))
    if len(previous) >= 600 and len(output) < int(len(previous) * 0.65):
        violations.append("collapse_vs_previous_article")
    previous_headings = route_0506_markdown_heading_count(previous)
    output_headings = route_0506_markdown_heading_count(output)
    if previous_headings >= 3 and output_headings < max(2, previous_headings // 2):
        violations.append("heading_collapse")
    if previous_headings >= 2 and output_headings < previous_headings - 1:
        violations.append("heading_loss")
    return _route_0506_unique_strings(violations)


def looks_like_route_0506_meta_review(text: str) -> bool:
    stripped = str(text or "").strip()
    if stripped.startswith("総評として"):
        return True
    marker_count = sum(1 for marker in ROUTE_0506_META_REVIEW_MARKERS if marker in stripped)
    if marker_count >= 2:
        return True
    numbered_review = bool(re.search(r"(?m)^\s*\d+\.\s+\*\*.+\*\*", stripped))
    if numbered_review and any(term in stripped for term in ("整合性", "ソース寄り", "不自然", "brief", "本文")):
        return True
    return False


def route_0506_self_perspective_contract_was_lost(
    previous_article: str,
    generated: str,
    payload: Mapping[str, Any] | None = None,
) -> bool:
    brief = route_0506_article_brief_payload(payload)
    if str(brief.get("viewpoint_mode") or "") != "self_perspective":
        return False
    narrator = str(brief.get("narrator") or "").strip()
    if narrator and narrator in previous_article and narrator not in generated:
        return True
    forbidden_terms = brief.get("forbidden_viewpoint_terms")
    if not isinstance(forbidden_terms, list):
        forbidden_terms = list(ROUTE_0506_DEFAULT_FORBIDDEN_VIEWPOINT_TERMS)
    previous_forbidden = {str(term) for term in forbidden_terms if str(term) and str(term) in previous_article}
    generated_forbidden = {str(term) for term in forbidden_terms if str(term) and str(term) in generated}
    if generated_forbidden - previous_forbidden:
        return True
    variants = {term for term in ROUTE_0506_FIRST_PERSON_VARIANTS if term in generated}
    return bool(narrator and variants and variants != {narrator})


def route_0506_article_brief_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    root = payload.get("article_brief")
    if not isinstance(root, Mapping):
        return {}
    brief = root.get("article_brief")
    return dict(brief) if isinstance(brief, Mapping) else dict(root)


def route_0506_output_has_article_wrapper_or_fence(text: str) -> bool:
    return bool(route_0506_visible_output_contract_violations(text))


def route_0506_visible_output_contract_violations(text: str) -> list[str]:
    stripped = str(text or "").strip()
    if not stripped:
        return []
    violations: list[str] = []
    first_line = route_0506_first_visible_line(stripped)
    if first_line and not first_line.lstrip().startswith("#") and route_0506_line_is_reader_facing_preface(first_line):
        violations.append("reader_facing_preface")
    if re.search(r"(?m)^#{1,6}\s*修正版\s*$", stripped):
        violations.append("revision_wrapper_heading")
    if re.search(r"(?m)^```[A-Za-z0-9_-]*\s*$", stripped):
        violations.append("markdown_fence")
    return _route_0506_unique_strings(violations)


def route_0506_first_visible_line(text: str) -> str:
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def route_0506_line_is_reader_facing_preface(line: str) -> bool:
    normalized = " ".join(str(line or "").strip().split())
    if not normalized:
        return False
    return any(re.search(pattern, normalized) for pattern in ROUTE_0506_READER_FACING_PREFACE_PATTERNS)


def route_0506_is_visible_output_contract_violation_type(violation_type: str) -> bool:
    return str(violation_type or "") in ROUTE_0506_VISIBLE_OUTPUT_CONTRACT_TYPES


def route_0506_stage_output_guard_violations(client: Any) -> list[dict[str, Any]]:
    violations = getattr(client, "route_0506_stage_output_guard_violations", [])
    if not isinstance(violations, list):
        return []
    return [dict(item) for item in violations if isinstance(item, Mapping)]


def _route_0506_unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def route_0506_markdown_heading_count(text: str) -> int:
    return sum(1 for line in str(text or "").splitlines() if line.lstrip().startswith("#"))


def route_0506_enrich_targeted_rewriter_payload(stage_name: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if stage_name != "targeted_rewriter":
        return payload
    quality_check = payload.get("quality_check")
    if not isinstance(quality_check, Mapping):
        return payload
    article_text = str(payload.get("article_text") or "").strip()
    long_sentence = route_0506_first_long_sentence(article_text)
    if not long_sentence:
        return payload

    enriched = copy.deepcopy(dict(payload))
    quality_root = enriched.get("quality_check")
    quality = quality_root.get("quality_check") if isinstance(quality_root, dict) else None
    issues = quality.get("issues") if isinstance(quality, dict) else None
    if not isinstance(issues, list):
        return payload
    changed = False
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        if issue.get("type") == "sentence_too_long" and not str(issue.get("text") or "").strip():
            issue["text"] = long_sentence
            changed = True
    return enriched if changed else payload


def route_0506_first_long_sentence(article_text: str, *, long_limit: int = 90) -> str:
    normalized = route_0506_markdown_heading_sentence_boundaries(article_text)
    sentences = [match.group(0).strip() for match in re.finditer(r"[^。！？!?]+[。！？!?]?", normalized) if match.group(0).strip()]
    long_sentences = [
        sentence
        for sentence in sorted(sentences, key=lambda item: len(item.rstrip("。！？!?")), reverse=True)
        if len(sentence.rstrip("。！？!?")) > long_limit
    ]
    return long_sentences[0] if long_sentences else ""


def route_0506_markdown_heading_sentence_boundaries(text: str) -> str:
    lines: list[str] = []
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.endswith(("。", "！", "？", "!", "?")):
            lines.append(f"{line}。")
        else:
            lines.append(line)
    return "\n".join(lines)
