"""Minimal editor guard for readability and legal-safe phrasing."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

_AI_PHRASE_REPLACEMENTS = {
    "することができます": "できます",
    "ということになります": "になります",
}
_LEAD_CLICHE_REPLACEMENTS = (
    (
        re.compile(r"^会社の輪郭が自然に伝わるよう、背景と具体を行き来しながら見ていきます。?$"),
        "事業の中身と、その背景にある考え方を順に見ていきます。",
    ),
)

_SENTENCE_SPLIT_RE = re.compile(r"[^。！？!?]+[。！？!?]?")
_CONNECTIVE_STACK_REPLACEMENTS = (
    (re.compile(r"^だからでは[、,]?"), "だから、"),
    (re.compile(r"^しかしですが[、,]?"), "しかし、"),
    (re.compile(r"^ただしですが[、,]?"), "ただし、"),
    (re.compile(r"^ですがしかし[、,]?"), "しかし、"),
    (re.compile(r"^ではですが[、,]?"), "では、"),
    (re.compile(r"^そのためですが[、,]?"), "そのため、"),
)
_MODAL_COLLISION_PATTERNS = (
    re.compile(r"(可能性があります)(?=[一-龥ぁ-んァ-ヶA-Za-z])"),
    re.compile(r"(考えられます)(?=[一-龥ぁ-んァ-ヶA-Za-z])"),
    re.compile(r"(見えてきます)(?=[一-龥ぁ-んァ-ヶA-Za-z])"),
)
_SOFTENED_MODAL_FRAGMENT_PATTERNS = (
    re.compile(
        r"(?P<prefix>[^\n。！？!?]{0,48}?(?:を|に|は|へ|で|と|も|から|まで))"
        r"高い可能性があります"
        r"(?P<suffix>(?:確認|参照|共有|整理|判断|対応|準備|設定|把握|見直し|案内|前提|移行|対象|必要|手順|最新)"
        r"[^。！？!?]{0,48})"
    ),
)
_DUPLICATE_PREDICATE_PATTERNS = (
    (re.compile(r"([一-龥々ぁ-んァ-ヶA-Za-z]{1,24})ますます(?=[。！？])"), r"\1ます"),
    (re.compile(r"(です){2,}(?=[。！？])"), "です"),
    (re.compile(r"(ます){2,}(?=[。！？])"), "ます"),
    (re.compile(r"(でした){2,}(?=[。！？])"), "でした"),
    (re.compile(r"(ました){2,}(?=[。！？])"), "ました"),
)
_DANGLING_CLAUSE_ENDINGS = ("ものの", "けれど", "ので", "ため", "なく", "れば", "が", "し", "を", "の", "で")
_PARTICLE_TERMINAL_ENDINGS = ("ことは", "ため", "ので", "によって", "として", "から", "より", "まで")
_TRUNCATED_VERB_SENTENCE_RE = re.compile(
    r"[一-龥々ぁ-んァ-ヶ]{1,16}(?:わ|ら|り|き|し|ち|み|え|け|せ|て|ね|め|れ|げ|べ|ぜ|で|じ|ぎ|び|ぴ|に|ひ)[。！？!?]$"
)
_SENTENCE_INTEGRITY_MAX_REPAIRS = 8
_SENTENCE_INTEGRITY_MAX_ACTIONS = 12
_SENTENCE_INTEGRITY_WARNING = "editor_guard_sentence_integrity_warning"
_SENTENCE_INTEGRITY_BUDGET_EXCEEDED = "editor_guard_sentence_integrity_budget_exceeded"


@dataclass
class EditorGuardRepairAction:
    kind: str
    sentence_index: int
    before_excerpt: str
    after_excerpt: str
    applied: bool = True


@dataclass
class EditorGuardReport:
    ai_phrase_replaced_count: int = 0
    legal_softened_count: int = 0
    duplicate_line_removed_count: int = 0
    grammar_repair_count: int = 0
    sentence_integrity_repair_count: int = 0
    sentence_integrity_warning_count: int = 0
    repair_actions: List[EditorGuardRepairAction] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _safe_excerpt(text: str, limit: int = 60) -> str:
    compact = " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split())
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "..."


def _append_warning(report: EditorGuardReport, warning: str) -> None:
    if warning and warning not in report.warnings:
        report.warnings.append(warning)


def _append_repair_action(
    report: EditorGuardReport,
    *,
    kind: str,
    sentence_index: int,
    before_text: str,
    after_text: str,
    applied: bool,
) -> None:
    if len(report.repair_actions) >= _SENTENCE_INTEGRITY_MAX_ACTIONS:
        return
    report.repair_actions.append(
        EditorGuardRepairAction(
            kind=kind,
            sentence_index=sentence_index,
            before_excerpt=_safe_excerpt(before_text),
            after_excerpt=_safe_excerpt(after_text),
            applied=applied,
        )
    )


def _estimate_change_cost(before_text: str, after_text: str) -> int:
    cost = 0
    for tag, i1, i2, j1, j2 in SequenceMatcher(a=before_text, b=after_text).get_opcodes():
        if tag != "equal":
            cost += max(i2 - i1, j2 - j1)
    return cost


def _split_sentences(line: str) -> List[str]:
    parts = [item for item in _SENTENCE_SPLIT_RE.findall(str(line or "")) if item]
    return parts or ([str(line or "")] if str(line or "") else [])


def _repair_connective_stack(sentence: str) -> Optional[str]:
    for pattern, replacement in _CONNECTIVE_STACK_REPLACEMENTS:
        candidate = pattern.sub(replacement, sentence, count=1)
        if candidate != sentence:
            return candidate
    return None


def _repair_modal_collision(sentence: str) -> Optional[str]:
    updated = sentence
    changed = False
    for pattern in _MODAL_COLLISION_PATTERNS:
        candidate = pattern.sub(r"\1。", updated)
        if candidate != updated:
            updated = candidate
            changed = True
    return updated if changed else None


def _repair_softened_modal_fragment(sentence: str) -> Optional[str]:
    updated = sentence
    changed = False

    def _replace(match: re.Match[str]) -> str:
        prefix = str(match.group("prefix") or "").rstrip()
        suffix = str(match.group("suffix") or "").lstrip()
        if prefix.endswith("は"):
            return f"{prefix}、{suffix}"
        return f"{prefix}{suffix}"

    for pattern in _SOFTENED_MODAL_FRAGMENT_PATTERNS:
        candidate = pattern.sub(_replace, updated, count=1)
        if candidate != updated:
            updated = candidate
            changed = True
    return updated if changed else None


def _repair_duplicate_predicate_tail(sentence: str) -> Optional[str]:
    updated = sentence
    changed = False
    for pattern, replacement in _DUPLICATE_PREDICATE_PATTERNS:
        candidate = pattern.sub(replacement, updated)
        if candidate != updated:
            updated = candidate
            changed = True
    return updated if changed else None


def _truncated_verb_issue(sentence: str) -> bool:
    normalized = str(sentence or "").strip()
    if not normalized:
        return False
    return bool(_TRUNCATED_VERB_SENTENCE_RE.search(normalized)) and not re.search(
        r"(?:つつ|けど|けれど|ものの)[。！？!?]$",
        normalized,
    )


def _particle_terminal_issue(sentence: str) -> bool:
    normalized = str(sentence or "").strip()
    if not normalized:
        return False
    base = re.sub(r"[。！？!?]+$", "", normalized)
    return any(base.endswith(ending) for ending in _PARTICLE_TERMINAL_ENDINGS)


def _repair_particle_terminal_join(sentence: str, next_sentence: str) -> Optional[str]:
    if not _particle_terminal_issue(sentence) or not str(next_sentence or "").strip():
        return None
    base = re.sub(r"[。！？!?]+\s*$", "", str(sentence or "").rstrip())
    joined_next = str(next_sentence or "").lstrip()
    if not base or not joined_next:
        return None
    connector = "" if base.endswith("、") else "、"
    return f"{base}{connector}{joined_next}"


def _repair_truncated_verb_join(sentence: str, next_sentence: str) -> Optional[str]:
    if not _truncated_verb_issue(sentence) or not str(next_sentence or "").strip():
        return None
    base = re.sub(r"[。！？!?]+\s*$", "", str(sentence or "").rstrip())
    joined_next = str(next_sentence or "").lstrip()
    if not base or not joined_next:
        return None
    connector = "" if base.endswith("、") else "、"
    return f"{base}{connector}{joined_next}"


def _dangling_clause_issue(sentence: str) -> bool:
    normalized = str(sentence or "").strip()
    if not normalized:
        return False
    base = re.sub(r"[。！？!?]+$", "", normalized)
    return any(base.endswith(ending) for ending in _DANGLING_CLAUSE_ENDINGS)


def _repair_dangling_clause_join(sentence: str, next_sentence: str) -> Optional[str]:
    if not _dangling_clause_issue(sentence) or not str(next_sentence or "").strip():
        return None
    base = re.sub(r"[。！？!?]+\s*$", "", str(sentence or "").rstrip())
    joined_next = str(next_sentence or "").lstrip()
    if not base or not joined_next:
        return None
    connector = "" if base.endswith("、") else "、"
    return f"{base}{connector}{joined_next}"


def _try_apply_sentence_repair(
    report: EditorGuardReport,
    *,
    kind: str,
    sentence_index: int,
    before_text: str,
    after_text: str,
    remaining_budget: int,
) -> tuple[str, int, bool]:
    change_cost = _estimate_change_cost(before_text, after_text)
    if (
        report.sentence_integrity_repair_count >= _SENTENCE_INTEGRITY_MAX_REPAIRS
        or change_cost <= 0
        or change_cost > remaining_budget
    ):
        report.sentence_integrity_warning_count += 1
        warning_code = (
            _SENTENCE_INTEGRITY_BUDGET_EXCEEDED
            if change_cost > remaining_budget or report.sentence_integrity_repair_count >= _SENTENCE_INTEGRITY_MAX_REPAIRS
            else _SENTENCE_INTEGRITY_WARNING
        )
        _append_warning(report, warning_code)
        _append_repair_action(
            report,
            kind=kind,
            sentence_index=sentence_index,
            before_text=before_text,
            after_text=after_text,
            applied=False,
        )
        return before_text, remaining_budget, False
    report.sentence_integrity_repair_count += 1
    _append_repair_action(
        report,
        kind=kind,
        sentence_index=sentence_index,
        before_text=before_text,
        after_text=after_text,
        applied=True,
    )
    return after_text, remaining_budget - change_cost, True


def _apply_sentence_integrity_repairs(body: str, report: EditorGuardReport) -> str:
    change_budget = max(8, int(round(len(body) * 0.015)))
    softened_fragment_budget = max(24, int(round(len(body) * 0.02)))
    duplicate_predicate_budget = max(12, int(round(len(body) * 0.01)))
    lines = body.splitlines()
    rewritten_lines: List[str] = []
    sentence_index = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            rewritten_lines.append(line)
            continue
        sentences = _split_sentences(line)
        rebuilt: List[str] = []
        idx = 0
        while idx < len(sentences):
            sentence = sentences[idx]
            sentence_index += 1
            candidate = _repair_connective_stack(sentence)
            if candidate and candidate != sentence:
                sentence, change_budget, _ = _try_apply_sentence_repair(
                    report,
                    kind="connective_stack_collapse",
                    sentence_index=sentence_index,
                    before_text=sentences[idx],
                    after_text=candidate,
                    remaining_budget=change_budget,
                )
            else:
                candidate = _repair_softened_modal_fragment(sentence)
                if candidate and candidate != sentence:
                    sentence, softened_fragment_budget, _ = _try_apply_sentence_repair(
                        report,
                        kind="softened_modal_fragment_drop",
                        sentence_index=sentence_index,
                        before_text=sentences[idx],
                        after_text=candidate,
                        remaining_budget=softened_fragment_budget,
                    )
                else:
                    candidate = _repair_modal_collision(sentence)
                    if candidate and candidate != sentence:
                        sentence, change_budget, _ = _try_apply_sentence_repair(
                            report,
                            kind="modal_verb_collision",
                            sentence_index=sentence_index,
                            before_text=sentences[idx],
                            after_text=candidate,
                            remaining_budget=change_budget,
                        )
                    else:
                        candidate = _repair_duplicate_predicate_tail(sentence)
                        if candidate and candidate != sentence:
                            repaired_sentence, duplicate_predicate_budget, applied = _try_apply_sentence_repair(
                                report,
                                kind="duplicate_predicate_tail",
                                sentence_index=sentence_index,
                                before_text=sentences[idx],
                                after_text=candidate,
                                remaining_budget=duplicate_predicate_budget,
                            )
                            if applied:
                                report.grammar_repair_count += 1
                            sentence = repaired_sentence
                        else:
                            next_sentence = sentences[idx + 1] if idx + 1 < len(sentences) else ""
                            candidate = _repair_particle_terminal_join(sentence, next_sentence)
                            if candidate and candidate != sentence:
                                repaired_sentence, change_budget, applied = _try_apply_sentence_repair(
                                    report,
                                    kind="particle_terminal_join",
                                    sentence_index=sentence_index,
                                    before_text=f"{sentences[idx]}{next_sentence}",
                                    after_text=candidate,
                                    remaining_budget=change_budget,
                                )
                                sentence = repaired_sentence
                                if applied:
                                    idx += 1
                                    sentence_index += 1
                            else:
                                candidate = _repair_truncated_verb_join(sentence, next_sentence)
                                if candidate and candidate != sentence:
                                    repaired_sentence, change_budget, applied = _try_apply_sentence_repair(
                                        report,
                                        kind="truncated_verb_join",
                                        sentence_index=sentence_index,
                                        before_text=f"{sentences[idx]}{next_sentence}",
                                        after_text=candidate,
                                        remaining_budget=change_budget,
                                    )
                                    sentence = repaired_sentence
                                    if applied:
                                        idx += 1
                                        sentence_index += 1
                                else:
                                    candidate = _repair_dangling_clause_join(sentence, next_sentence)
                                    if candidate and candidate != sentence:
                                        repaired_sentence, change_budget, applied = _try_apply_sentence_repair(
                                            report,
                                            kind="dangling_clause_join",
                                            sentence_index=sentence_index,
                                            before_text=f"{sentences[idx]}{next_sentence}",
                                            after_text=candidate,
                                            remaining_budget=change_budget,
                                        )
                                        sentence = repaired_sentence
                                        if applied:
                                            idx += 1
                                            sentence_index += 1
                                    elif (
                                        _particle_terminal_issue(sentence)
                                        or _truncated_verb_issue(sentence)
                                        or _dangling_clause_issue(sentence)
                                    ):
                                        report.sentence_integrity_warning_count += 1
                                        _append_warning(report, _SENTENCE_INTEGRITY_WARNING)
                                        _append_repair_action(
                                            report,
                                            kind=(
                                                "particle_terminal_join"
                                                if _particle_terminal_issue(sentence)
                                                else "truncated_verb_join"
                                                if _truncated_verb_issue(sentence)
                                                else "dangling_clause_join"
                                            ),
                                            sentence_index=sentence_index,
                                            before_text=sentences[idx],
                                            after_text=sentences[idx],
                                            applied=False,
                                        )
            rebuilt.append(sentence)
            idx += 1
        rewritten_lines.append("".join(rebuilt))
    return "\n".join(rewritten_lines)


def apply_minimal_editor_guard(text: str) -> Tuple[str, EditorGuardReport]:
    body = str(text or "")
    report = EditorGuardReport()

    for source, target in _AI_PHRASE_REPLACEMENTS.items():
        if source in body:
            replaced = body.count(source)
            body = body.replace(source, target)
            report.ai_phrase_replaced_count += replaced

    lines = body.splitlines()
    for index, line in enumerate(lines):
        stripped = str(line or "").strip()
        if not stripped or stripped.startswith("#"):
            continue
        for pattern, replacement in _LEAD_CLICHE_REPLACEMENTS:
            if not pattern.match(stripped):
                continue
            updated = pattern.sub(replacement, stripped, count=1)
            if updated == stripped:
                continue
            lines[index] = line.replace(stripped, updated, 1)
            report.ai_phrase_replaced_count += 1
            _append_repair_action(
                report,
                kind="lead_cliche_rewrite",
                sentence_index=1,
                before_text=stripped,
                after_text=updated,
                applied=True,
            )
            break
    body = "\n".join(lines)

    # Remove exact duplicated non-heading lines.
    unique_lines: List[str] = []
    seen_plain_lines = set()
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            unique_lines.append(line)
            continue
        if stripped in seen_plain_lines:
            report.duplicate_line_removed_count += 1
            continue
        seen_plain_lines.add(stripped)
        unique_lines.append(line)
    body = "\n".join(unique_lines)

    # Minimal grammar repair for repeated punctuation and unsafe sentence endings.
    before = body
    body = re.sub(r"[。．]{2,}", "。", body)
    body = re.sub(r"[、,]{2,}", "、", body)
    body = re.sub(r"(ますし。|でしたし。|ましたし。)", "ます。", body)
    report.grammar_repair_count = 1 if body != before else 0
    body = _apply_sentence_integrity_repairs(body, report)

    return body, report
