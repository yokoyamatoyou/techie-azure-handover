"""Rule-based legal post-check for generated body text."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Dict, List, Sequence

from . import error_codes


_LAW_NAME_RE = re.compile(
    r"[A-Za-z0-9一-龥ァ-ヶー][A-Za-z0-9一-龥ぁ-んァ-ヶー]{1,63}"
    r"(?:法施行規則|法施行令|法律|法|条例|施行規則|ガイドライン|指針)"
)
_ARTICLE_RE = re.compile(r"第[0-9一二三四五六七八九十百千]+条(?:第[0-9一二三四五六七八九十百千]+項)?(?:第[0-9一二三四五六七八九十百千]+号)?")
_EXACT_CITATION_RE = re.compile(
    r"([A-Za-z0-9一-龥ァ-ヶー][A-Za-z0-9一-龥ぁ-んァ-ヶー]{1,63}"
    r"(?:法施行規則|法施行令|法律|法|条例|施行規則|ガイドライン|指針)"
    r"(?:第[0-9一二三四五六七八九十百千]+条(?:第[0-9一二三四五六七八九十百千]+項)?(?:第[0-9一二三四五六七八九十百千]+号)?)?)"
)
_LEGAL_ALIAS_GROUPS = (
    frozenset({"景表法", "景品表示法"}),
    frozenset({"特商法", "特定商取引法", "特定商取引に関する法律"}),
    frozenset({"個人情報保護法", "個人情報の保護に関する法律"}),
    frozenset({"薬機法", "医薬品医療機器等法", "医薬品、医療機器等の品質、有効性及び安全性の確保等に関する法律"}),
)
_LEGAL_NAME_STOPWORDS = {
    "方法",
    "手法",
    "活用法",
    "解決法",
    "対症療法",
    "対処法",
    "使い方",
    "考え方",
    "見方",
    "進め方",
    "伝え方",
    "選び方",
    "あり方",
    "在り方",
    "関連法",
    "関連法令",
    "公的ガイドライン",
    "公的指針",
    "違法",
    "適法",
}
_LEGAL_REWRITE_STYLE_GUARDS = {
    "warm": "やさしい距離感は保つが、過剰な注意喚起テンプレへ寄せない。",
    "calm": "落ち着いた整理のまま、急に強い断定口調へ寄せない。",
    "formal": "端正さは保つが、定型的なお役所文や過度な硬文化は避ける。",
    "passionate": "前向きさは残すが、煽りや過度な勢いに置き換えない。",
    "auto": "元の温度感と語りの距離を崩さない。",
}
_LEGAL_REWRITE_ARTICLE_GUARDS = {
    "announcement": "お知らせでは変更点・対象・時期の整理を崩さず、不要な一般論を足さない。",
    "explanatory_article": "解説では判断軸と前提の流れを崩さず、急な注意喚起節を足さない。",
    "case_study": "事例では課題・対応・結果の順序を崩さず、教訓の一般化を増やしすぎない。",
    "branding": "紹介文では価値説明の流れを崩さず、自己弁護のような追記を足さない。",
    "comparative_review": "比較記事では比較軸を崩さず、新しい勝敗表現や候補を足さない。",
}


def _is_legal_name_candidate(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    if value.endswith("法") and re.search(r"[ぁ-ん]", value):
        return False
    return not any(stopword in value for stopword in _LEGAL_NAME_STOPWORDS)


def build_legal_rewrite_guard_lines(
    *,
    article_type: str = "",
    tone_profile: str = "auto",
) -> List[str]:
    normalized_article_type = str(article_type or "").strip().lower()
    normalized_tone_profile = str(tone_profile or "auto").strip().lower() or "auto"
    lines = [
        "法務上必要な箇所だけ局所修正し、全文の言い換えや全面書き直しはしない。",
        "法令名・断定表現・越権誘導の修正が必要な文だけを直し、見出し追加や論点追加はしない。",
        "AIっぽい決まり文句、急に安全側へ倒した一般論、空疎な注意喚起テンプレを足さない。",
        "修正後も元の段落運びと自然な日本語を保ち、リーガル都合で不自然な言い換えにしない。",
    ]
    article_guard = _LEGAL_REWRITE_ARTICLE_GUARDS.get(normalized_article_type)
    if article_guard:
        lines.append(article_guard)
    lines.append(
        _LEGAL_REWRITE_STYLE_GUARDS.get(
            normalized_tone_profile,
            _LEGAL_REWRITE_STYLE_GUARDS["auto"],
        )
    )
    return lines


@dataclass
class LegalIssue:
    category: str
    severity: str
    law: str
    original: str
    fixed: str
    reason: str


def _replace_all(text: str, source: str, target: str) -> tuple[str, int]:
    count = text.count(source)
    if count <= 0:
        return text, 0
    return text.replace(source, target), count


def _replace_pattern(text: str, pattern: re.Pattern[str], target: str) -> tuple[str, int]:
    updated, count = pattern.subn(target, text)
    return updated, count


def _extract_legal_citations(text: str) -> List[str]:
    citations: List[str] = []
    for match in _EXACT_CITATION_RE.finditer(str(text or "")):
        token = str(match.group(1) or "").strip("、。()（）「」『』")
        if not token or token in citations or not _is_legal_name_candidate(token):
            continue
        citations.append(token)
    return citations


def _law_name_from_citation(citation: str) -> str:
    match = _LAW_NAME_RE.search(str(citation or ""))
    candidate = str(match.group(0) if match else "").strip()
    if not _is_legal_name_candidate(candidate):
        return ""
    return candidate


def _looks_like_exact_citation(citation: str) -> bool:
    return bool(_ARTICLE_RE.search(str(citation or "")))


def _legal_name_variants(text: str) -> set[str]:
    value = str(text or "").strip()
    if not value:
        return set()
    variants = {value}
    compact_value = re.sub(r"\s+", "", value)
    for group in _LEGAL_ALIAS_GROUPS:
        compact_group = {re.sub(r"\s+", "", item) for item in group}
        if compact_value in compact_group:
            variants.update(group)
            break
    return {item for item in variants if item and _is_legal_name_candidate(item)}


def _generic_citation_target(citation: str) -> str:
    law_name = _law_name_from_citation(citation)
    if law_name:
        return law_name
    if "ガイドライン" in citation or "指針" in citation or "基準" in citation:
        return "公的ガイドライン"
    return "関連法令"


def _build_verified_citation_pool(verified_texts: Sequence[str]) -> set[str]:
    verified: set[str] = set()
    for text in verified_texts:
        for citation in _extract_legal_citations(text):
            verified.update(_legal_name_variants(citation))
        for match in _LAW_NAME_RE.findall(str(text or "")):
            candidate = str(match).strip()
            if _is_legal_name_candidate(candidate):
                verified.update(_legal_name_variants(candidate))
        normalized_text = str(text or "")
        for group in _LEGAL_ALIAS_GROUPS:
            if any(alias in normalized_text for alias in group):
                verified.update(group)
    return verified


def _rewrite_unverified_citations(
    text: str,
    verified_pool: set[str],
) -> tuple[str, List[LegalIssue], Dict[str, object]]:
    checked = str(text or "")
    issues: List[LegalIssue] = []
    detected = _extract_legal_citations(checked)
    verified: List[str] = []
    unverified: List[str] = []
    rewrite_applied = False

    for citation in detected:
        citation_variants = _legal_name_variants(citation)
        if verified_pool.intersection(citation_variants):
            verified.append(citation)
            continue
        law_name = _law_name_from_citation(citation)
        law_name_variants = _legal_name_variants(law_name)
        if law_name and verified_pool.intersection(law_name_variants) and _looks_like_exact_citation(citation):
            target = law_name
        else:
            target = _generic_citation_target(citation)
        checked, count = _replace_all(checked, citation, target)
        if count <= 0:
            continue
        rewrite_applied = True
        unverified.append(citation)
        issues.append(
            LegalIssue(
                category="unverified_legal_citation",
                severity="medium",
                law=law_name or "法令未検証",
                original=citation,
                fixed=target,
                reason="未検証の法令名・条文番号・ガイドライン名は exact 引用せず一般表現へ落とす",
            )
        )

    citation_guard = {
        "detected_citations": detected,
        "verified_citations": verified,
        "unverified_citations": unverified,
        "rewrite_applied": rewrite_applied,
    }
    return checked, issues, citation_guard


def run_legal_postcheck(text: str, verified_texts: Sequence[str] | None = None) -> Dict[str, object]:
    body = str(text or "")
    checked = body
    issues: List[LegalIssue] = []
    warnings: List[str] = []
    verified_pool = _build_verified_citation_pool(tuple(verified_texts or ()))

    try:
        absolute_rules = [
            (
                re.compile(r"必ず([^\s。、]{1,20})(ます|です|でしょう|ましょう)"),
                r"多くの場合\1\2",
                "景表法",
                "断定表現を緩和して誤認リスクを下げる",
            ),
            ("必ず", "原則として", "景表法", "断定表現を緩和して誤認リスクを下げる"),
            ("絶対", "高い可能性で", "景表法", "絶対表現を避ける"),
            ("100%", "多くの場合", "景表法", "過度な効果断定を回避する"),
            ("保証します", "期待できます", "景表法", "保証表現を避ける"),
            ("副作用はありません", "副作用リスクは個人差があります", "薬機法", "医療効果の断定回避"),
            ("治ります", "改善が期待できます", "薬機法", "治療断定を避ける"),
        ]

        # Benign imperative guidance such as "必ず確認してください" is not a legal guarantee claim.
        checked, _ = _replace_pattern(
            checked,
            re.compile(r"必ず((?:ご確認|お確かめ)(?:ください|願います|をお願いします|いただきますようお願いいたします))"),
            r"\1",
        )
        checked, _ = _replace_pattern(
            checked,
            re.compile(r"必ずしも"),
            "常にとは限らず",
        )

        for source, target, law, reason in absolute_rules:
            if isinstance(source, re.Pattern):
                if not source.search(checked):
                    continue
                checked, count = _replace_pattern(checked, source, target)
            else:
                if source not in checked:
                    continue
                checked, count = _replace_all(checked, source, target)
            if count <= 0:
                continue
            for _ in range(count):
                issues.append(
                    LegalIssue(
                        category="legal_assertion",
                        severity="medium",
                        law=law,
                        original=source,
                        fixed=target,
                        reason=reason,
                    )
                )

        privilege_patterns = (
            re.compile(r"内部指示を無視", re.I),
            re.compile(r"system prompt", re.I),
            re.compile(r"developer message", re.I),
            re.compile(r"権限を上書き", re.I),
        )
        for pattern in privilege_patterns:
            for hit in pattern.findall(checked):
                issues.append(
                    LegalIssue(
                        category="privilege_override",
                        severity="high",
                        law="セキュリティ",
                        original=str(hit),
                        fixed="[REMOVED]",
                        reason="越権・指示無効化の誘導を本文から除去する",
                    )
                )
            checked = pattern.sub("[REMOVED]", checked)

        checked, citation_issues, citation_guard = _rewrite_unverified_citations(checked, verified_pool)
        issues.extend(citation_issues)

        if any(issue.category == "legal_assertion" for issue in issues):
            warnings.append(error_codes.SEC_LEGAL_ASSERTION_SOFTENED)
        if any(issue.category == "unverified_legal_citation" for issue in issues):
            warnings.append(error_codes.SEC_UNVERIFIED_LEGAL_CITATION_SOFTENED)
        if any(issue.category == "privilege_override" for issue in issues):
            warnings.append(error_codes.SEC_PRIVILEGE_OVERRIDE_BLOCKED)

        has_high = any(issue.severity == "high" for issue in issues)
        if has_high:
            risk_level = "high"
        elif len(issues) >= 3:
            risk_level = "medium"
        elif issues:
            risk_level = "low"
        else:
            risk_level = "none"

        return {
            "success": True,
            "reason_code": "OK",
            "has_issues": bool(issues),
            "risk_level": risk_level,
            "issue_count": len(issues),
            "issues": [asdict(issue) for issue in issues],
            "checked_text": checked,
            "warnings": warnings,
            "citation_guard": citation_guard,
        }
    except Exception:
        return {
            "success": False,
            "reason_code": error_codes.SYS_LEGAL_POSTCHECK_FAILURE,
            "has_issues": False,
            "risk_level": "none",
            "issue_count": 0,
            "issues": [],
            "checked_text": body,
            "warnings": [error_codes.SYS_LEGAL_POSTCHECK_FAILURE],
            "citation_guard": {
                "detected_citations": [],
                "verified_citations": [],
                "unverified_citations": [],
                "rewrite_applied": False,
            },
        }
