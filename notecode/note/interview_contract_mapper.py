"""Shared mapping from interview answers to input-contract hints."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping

_INTERVIEW_PERSPECTIVE_NON_TOPIC_PATTERN = re.compile(
    r"(指定しない|任せる|おまかせ|自動判定|auto|知見を混ぜる|視点を補強する|要点整理を重視する|"
    r"先に短く示す|開始時期を先に示す|確認事項を先に示す|判断基準を先に示す|"
    r"限界を分けて説明する|注意点を先に示す|価値の違いを具体化する|利用シーンから価値を伝える|"
    r"選ぶ理由を判断軸で示す|理念より日々の行動から伝える|制度より現場の工夫を中心にする|"
    r"価値観が判断に出る場面を示す)",
    re.I,
)
_INTERVIEW_PERSPECTIVE_SKIP_PATTERN = re.compile(r"^(?:指定しない|任せる|おまかせ|自動判定|auto)$", re.I)
_INTERVIEW_KNOWLEDGE_LENS_PATTERN = re.compile(
    r"(知見を混ぜる|法務|コンプライアンス|リーガル|ブランド|ブランディング|広報|編集|記者|ジャーナリスト)",
    re.I,
)
_INTERVIEW_NARRATIVE_AXIS_PATTERN = re.compile(
    r"(利用シーン|価値|判断軸|判断基準|日々の行動|現場の工夫|制度より|理念より|先に短く示す|確認事項を先に示す|注意点を先に示す)",
    re.I,
)
_CORPORATE_WRITER_ROLE_PATTERN = re.compile(r"(ブランド担当|広報担当)")


def normalize_interview_list_value(value: Any) -> List[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list):
        return []
    normalized: List[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            normalized.append(text)
    return normalized


def normalize_topic_statement_from_interview(perspective_answer: str) -> str:
    text = str(perspective_answer or "").strip()
    if not text:
        return ""
    if _INTERVIEW_PERSPECTIVE_NON_TOPIC_PATTERN.search(text):
        return ""
    return text[:180]


def normalize_narrative_axis_from_interview(perspective_answer: str) -> str:
    text = str(perspective_answer or "").strip()
    if (
        not text
        or _INTERVIEW_PERSPECTIVE_SKIP_PATTERN.fullmatch(text)
        or _INTERVIEW_KNOWLEDGE_LENS_PATTERN.search(text)
    ):
        return ""
    if normalize_topic_statement_from_interview(text):
        return ""
    if not _INTERVIEW_NARRATIVE_AXIS_PATTERN.search(text):
        return ""
    return text[:120]


def derive_knowledge_lenses_from_interview(
    answers: Mapping[str, Any],
    *,
    writer_role: str = "",
) -> List[str]:
    raw_values = normalize_interview_list_value((answers or {}).get("knowledge_lenses"))
    perspective_answer = str((answers or {}).get("perspective") or "").strip()
    if perspective_answer and _INTERVIEW_KNOWLEDGE_LENS_PATTERN.search(perspective_answer):
        raw_values.append(perspective_answer)
    writer_role_text = str(writer_role or "").strip()
    if writer_role_text and _CORPORATE_WRITER_ROLE_PATTERN.search(writer_role_text):
        raw_values.append("企業ブランディング担当の知見を混ぜる")
    normalized: List[str] = []
    for item in raw_values:
        text = str(item or "").strip()
        if (
            not text
            or _INTERVIEW_PERSPECTIVE_SKIP_PATTERN.fullmatch(text)
            or not _INTERVIEW_KNOWLEDGE_LENS_PATTERN.search(text)
            or text in normalized
        ):
            continue
        normalized.append(text[:80])
    return normalized[:4]


def build_interview_contract_patch(
    answers: Mapping[str, Any],
    *,
    writer_role: str = "",
) -> Dict[str, Any]:
    perspective_answer = str((answers or {}).get("perspective") or "").strip()
    patch = {
        "topic_statement": normalize_topic_statement_from_interview(perspective_answer),
        "narrative_axis": normalize_narrative_axis_from_interview(perspective_answer),
        "knowledge_lenses": derive_knowledge_lenses_from_interview(
            answers or {},
            writer_role=writer_role,
        ),
    }
    fallback_narrative = str((answers or {}).get("narrative_axis") or "").strip()
    patch["narrative_axis"] = patch["narrative_axis"] or normalize_narrative_axis_from_interview(
        fallback_narrative
    )
    return patch
