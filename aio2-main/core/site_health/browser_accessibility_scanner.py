# -*- coding: utf-8 -*-
"""Bridge Playwright/axe accessibility scan output into Kotomigaki shapes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


BROWSER_SCORING_VERSION = "seo_accessibility_ux_v1"
_BUNDLED_SCANNER_DIR = Path(__file__).resolve().parents[2] / "tools" / "accessibility_scanner"
DEFAULT_SCANNER_DIR = Path(os.getenv("KOTOMIGAKI_ACCESSIBILITY_SCANNER_DIR", str(_BUNDLED_SCANNER_DIR)))
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("KOTOMIGAKI_ACCESSIBILITY_SCAN_TIMEOUT", "60") or "60")

_DISABLED_VALUES = {"0", "false", "no", "off", "disabled"}
_SEVERITY_RANK = {"critical": 4, "serious": 3, "moderate": 2, "minor": 1}
_SEVERITY_WEIGHT = {"critical": 22, "serious": 10, "moderate": 3, "minor": 1}

_RULE_GROUPS: Dict[str, Dict[str, str]] = {
    "image-alt": {"id": "image_alt", "label": "img alt", "action": "画像の代替テキストを見直す"},
    "image-redundant-alt": {"id": "image_alt", "label": "img alt", "action": "画像説明の重複を減らす"},
    "button-name": {"id": "interactive_names", "label": "button accessible name", "action": "ボタンの操作名を付ける"},
    "link-name": {"id": "interactive_names", "label": "link accessible name", "action": "リンクの目的を分かる名前にする"},
    "label": {"id": "form_labels", "label": "form label", "action": "入力欄に項目名を付ける"},
    "select-name": {"id": "form_labels", "label": "form label", "action": "選択欄に項目名を付ける"},
    "input-button-name": {"id": "interactive_names", "label": "button accessible name", "action": "入力ボタンの操作名を付ける"},
    "page-has-heading-one": {"id": "h1", "label": "h1", "action": "ページ主題をh1で示す"},
    "heading-order": {"id": "heading_hierarchy", "label": "heading order", "action": "見出し階層を整理する"},
    "landmark-one-main": {"id": "landmarks", "label": "landmark", "action": "本文領域をmainで示す"},
    "landmark-unique": {"id": "landmarks", "label": "landmark", "action": "主要領域の名前を整理する"},
    "region": {"id": "landmarks", "label": "landmark", "action": "主要領域をランドマーク内に入れる"},
    "html-has-lang": {"id": "html_lang", "label": "html lang", "action": "ページの言語を指定する"},
    "document-title": {"id": "title", "label": "title", "action": "ページ固有のtitleを入れる"},
    "frame-title": {"id": "iframe_titles", "label": "iframe title", "action": "埋め込み枠に内容名を付ける"},
    "color-contrast": {"id": "color_contrast", "label": "文字のコントラスト", "action": "文字色と背景色を読みやすくする"},
    "meta-viewport": {"id": "zoom_scaling", "label": "拡大表示", "action": "利用者が拡大できる設定にする"},
}


def browser_accessibility_enabled(scanner_dir: Optional[Path] = None) -> bool:
    """Return whether the bundled browser scanner should be attempted."""
    flag = os.getenv("KOTOMIGAKI_BROWSER_ACCESSIBILITY", "auto").strip().lower()
    if flag in _DISABLED_VALUES:
        return False
    if flag == "auto" and os.getenv("PYTEST_CURRENT_TEST"):
        return False
    base_dir = scanner_dir or DEFAULT_SCANNER_DIR
    return _scanner_script(base_dir).exists() and _scanner_dependencies_available(base_dir)


def run_browser_accessibility_scan(
    url: str,
    *,
    scanner_dir: Optional[Path] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Optional[Dict[str, Any]]:
    """Run the external scanner and return a normalized report, or None on failure.

    The scanner is intentionally fail-open. Kotomigaki keeps using the existing
    HTML-based checker when Node.js, bundled dependencies, or Playwright scan is
    unavailable.
    """
    base_dir = scanner_dir or DEFAULT_SCANNER_DIR
    script = _scanner_script(base_dir)
    node = shutil.which("node")
    if not node or not script.exists() or not url:
        return None

    try:
        completed = subprocess.run(
            [node, str(script), str(url)],
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(5, int(timeout_seconds or DEFAULT_TIMEOUT_SECONDS)),
            check=False,
        )
    except Exception:
        return None

    report = _parse_report_json(completed.stdout)
    if not report:
        return None
    status = str(((report.get("scan_run") or {}).get("status") or "")).lower()
    if status not in {"completed", "partial"}:
        return None
    return report


def build_browser_accessibility_payload(report: Dict[str, Any], *, mode: str = "simple") -> Dict[str, Any]:
    """Convert external report JSON into existing site_health.accessibility shape."""
    raw = build_browser_accessibility_raw(report)
    formatted = format_browser_accessibility_result(raw, mode=mode)
    return {
        "raw": raw,
        "formatted": formatted,
        "wcag": {
            "label": "見やすさ・使いやすさ改善スコア",
            "method": "実ブラウザ自動検出",
            "score": int(raw.get("score", 0) or 0),
            "score_status": raw.get("score_status", "needs_work"),
            "scoring_version": raw.get("scoring_version", BROWSER_SCORING_VERSION),
        },
        "source": "browser",
    }


def build_browser_accessibility_raw(report: Dict[str, Any]) -> Dict[str, Any]:
    score_snapshot = report.get("score_snapshot") or {}
    score = _safe_int(score_snapshot.get("score"))
    max_score = _safe_int(score_snapshot.get("max_score")) or 100
    issue_groups = _build_issue_groups(report)
    severity_counts = _severity_counts(report)
    manual_count = _safe_int(score_snapshot.get("manual_risk_count") or score_snapshot.get("manual_review_pending_count"))
    affected_counts = {
        "total_issues": sum(_safe_int(group.get("affected_count")) for group in issue_groups),
        "critical": severity_counts.get("critical", 0),
        "serious": severity_counts.get("serious", 0),
        "moderate": severity_counts.get("moderate", 0),
        "minor": severity_counts.get("minor", 0),
        "manual_review_pending": manual_count,
        "scanned_pages": _safe_int(score_snapshot.get("scanned_page_count")) or len(report.get("pages") or []),
        "score_cap": _safe_int(score_snapshot.get("score_cap")) or max_score,
    }
    for group in issue_groups:
        affected_counts[str(group.get("id"))] = _safe_int(group.get("affected_count"))

    return {
        "score": score,
        "raw_score": score_snapshot.get("raw_score"),
        "score_status": _score_status(score),
        "issue_groups": issue_groups,
        "affected_counts": affected_counts,
        "top_actions": _top_actions(issue_groups),
        "scoring_version": BROWSER_SCORING_VERSION,
        "score_cap": {
            "cap": affected_counts["score_cap"],
            "applied": bool(score_snapshot.get("score_cap_reason")),
            "reason": score_snapshot.get("score_cap_reason") or "",
            "sample_confidence": score_snapshot.get("sample_confidence") or "",
            "evidence_level": score_snapshot.get("evidence_level") or "",
        },
        "manual_review_pending_count": manual_count,
        "not_scored_risks": _trim_list(score_snapshot.get("not_scored_risks") or [], 8),
        "browser_scan_summary": _browser_scan_summary(report),
        "detection_source": "browser",
    }


def format_browser_accessibility_result(result: Dict[str, Any], mode: str = "simple") -> Dict[str, Any]:
    score = _safe_int(result.get("score"))
    status = _score_status(score)
    status_text = {
        "good": "改善スコア: 良好",
        "needs_attention": "改善スコア: 改善推奨",
        "needs_work": "改善スコア: 要改善",
    }.get(status, "改善スコア: 要改善")
    status_color = {"good": "success", "needs_attention": "warning", "needs_work": "danger"}.get(status, "danger")
    groups = [group for group in (result.get("issue_groups") or []) if isinstance(group, dict)]
    manual_count = _safe_int(result.get("manual_review_pending_count"))

    items = []
    for group in groups[:8]:
        label = _safe_text(group.get("label") or group.get("name") or group.get("id"))
        affected = _safe_int(group.get("affected_count"))
        issues = group.get("issues") or []
        subtext = ""
        if issues and isinstance(issues[0], dict):
            subtext = _safe_text(issues[0].get("issue") or issues[0].get("suggestion"))
        items.append(
            {
                "icon": "自動検出",
                "text": f"{label}: {affected}件の改善候補",
                "subtext": subtext or _safe_text(group.get("action")),
                "group": group.get("id", ""),
            }
        )
    if manual_count:
        items.append(
            {
                "icon": "手動確認が必要",
                "text": f"自動判定外リスク: {manual_count}件",
                "subtext": "色、読み上げ順、操作感など文脈確認が必要な候補です。",
                "group": "manual_review",
            }
        )

    cap_info = result.get("score_cap") or {}
    recommendations = [
        {"recommendation": action.get("action", ""), "category": action.get("label", "")}
        for action in result.get("top_actions", [])
        if isinstance(action, dict)
    ]
    if cap_info.get("reason"):
        recommendations.insert(0, {"recommendation": _safe_text(cap_info.get("reason")), "category": "スコア上限"})

    return {
        "title": "見やすさ・使いやすさ改善スコア",
        "subtitle": "実ブラウザで自動検出した見やすさ・使いやすさ",
        "status": status_text,
        "status_color": status_color,
        "score": score,
        "max_score": 100,
        "score_status": status,
        "scoring_version": result.get("scoring_version", BROWSER_SCORING_VERSION),
        "items": items,
        "recommendations": recommendations,
        "issues": _brief_issues(groups),
        "faq": [] if mode == "simple" else [],
        "sample_confidence": cap_info.get("sample_confidence", ""),
        "evidence_level": cap_info.get("evidence_level", ""),
        "detection_source": "browser",
    }


def _scanner_script(scanner_dir: Path) -> Path:
    return Path(scanner_dir) / "scripts" / "run-safe-url-scan.mjs"


def _scanner_dependencies_available(scanner_dir: Path) -> bool:
    base_dir = Path(scanner_dir)
    return (
        (base_dir / "node_modules" / "@axe-core" / "playwright").exists()
        and (base_dir / "node_modules" / "@playwright" / "test").exists()
    )


def _parse_report_json(stdout: str) -> Optional[Dict[str, Any]]:
    try:
        parsed = json.loads(stdout or "{}")
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) and isinstance(parsed.get("scan_run"), dict) else None


def _build_issue_groups(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for finding in report.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        rule_id = _safe_text(finding.get("rule_id"))
        mapping = _group_mapping(rule_id)
        group_id = mapping["id"]
        severity = _safe_text(finding.get("severity")) or "moderate"
        current = grouped.setdefault(
            group_id,
            {
                "id": group_id,
                "name": mapping["label"],
                "label": mapping["label"],
                "weight": _SEVERITY_WEIGHT.get(severity, 8),
                "score": 0,
                "ratio": 0.0,
                "status": "warning",
                "total_count": 0,
                "affected_count": 0,
                "issues": [],
                "action": mapping["action"],
                "source_rules": [],
                "max_severity": severity,
            },
        )
        current["affected_count"] = _safe_int(current.get("affected_count")) + 1
        current["total_count"] = max(_safe_int(current.get("total_count")), current["affected_count"])
        current["weight"] = max(_safe_int(current.get("weight")), _SEVERITY_WEIGHT.get(severity, 8))
        if _SEVERITY_RANK.get(severity, 2) > _SEVERITY_RANK.get(_safe_text(current.get("max_severity")), 2):
            current["max_severity"] = severity
        if rule_id and rule_id not in current["source_rules"]:
            current["source_rules"].append(rule_id)
        if len(current["issues"]) < 10:
            current["issues"].append(
                {
                    "issue": _safe_text(finding.get("message") or finding.get("user_impact") or rule_id),
                    "suggestion": _safe_text(finding.get("remediation")),
                    "element": _safe_text(finding.get("selector")),
                    "rule_id": rule_id,
                    "severity": severity,
                    "source": _safe_text(finding.get("source")) or "axe-core",
                }
            )

    for group in grouped.values():
        severity = _safe_text(group.get("max_severity"))
        affected = _safe_int(group.get("affected_count"))
        group["ratio"] = 0.0
        group["status"] = "needs_work" if severity in {"critical", "serious"} or affected >= 2 else "warning"
    return sorted(grouped.values(), key=lambda item: (-_safe_int(item.get("weight")), -_safe_int(item.get("affected_count")), str(item.get("id"))))


def _group_mapping(rule_id: str) -> Dict[str, str]:
    normalized = (rule_id or "").lower()
    if normalized in _RULE_GROUPS:
        return _RULE_GROUPS[normalized]
    if normalized.startswith("aria-"):
        return {"id": "aria_semantics", "label": "ARIA / 支援技術への意味", "action": "ARIAの役割と状態を正しく整理する"}
    if "contrast" in normalized:
        return _RULE_GROUPS["color-contrast"]
    if "keyboard" in normalized or "focus" in normalized:
        return {"id": "keyboard_focus", "label": "キーボード操作", "action": "キーボードで自然に操作できるようにする"}
    return {"id": "screen_reader_structure", "label": "読み上げ構造", "action": "支援技術に伝わる構造へ整理する"}


def _top_actions(issue_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    actions = []
    for group in issue_groups[:5]:
        actions.append(
            {
                "group": group.get("id"),
                "label": group.get("label"),
                "action": group.get("action"),
                "affected_count": _safe_int(group.get("affected_count")),
                "weight": _safe_int(group.get("weight")),
            }
        )
    return actions


def _browser_scan_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    scan_run = report.get("scan_run") or {}
    score_snapshot = report.get("score_snapshot") or {}
    pages = []
    for page in _trim_list(report.get("pages") or [], 4):
        if not isinstance(page, dict):
            continue
        screen_reader = page.get("screen_reader_preview") or {}
        pages.append(
            {
                "page_id": page.get("page_id"),
                "page_role": page.get("page_role"),
                "url": page.get("url"),
                "http_status": page.get("http_status"),
                "title": page.get("title"),
                "lang": page.get("lang"),
                "headings_count": len(page.get("headings") or []),
                "landmarks_count": len(page.get("landmarks") or []),
                "controls_count": len(page.get("controls") or []),
                "images_count": len(page.get("images") or []),
                "tab_order_sample": _trim_list(page.get("tab_order_sample") or [], 12),
                "missing_accessible_names": _trim_list(screen_reader.get("missing_accessible_names") or [], 10),
                "possible_reading_risks": _trim_list(screen_reader.get("possible_reading_risks") or [], 10),
            }
        )
    return {
        "scan_run": {
            "requested_url": scan_run.get("requested_url"),
            "final_url": scan_run.get("final_url"),
            "status": scan_run.get("status"),
            "profile_ids": scan_run.get("profile_ids") or [],
            "standards_checked_at": scan_run.get("standards_checked_at"),
        },
        "score_snapshot": {
            "score": score_snapshot.get("score"),
            "raw_score": score_snapshot.get("raw_score"),
            "score_cap_reason": score_snapshot.get("score_cap_reason"),
            "sample_confidence": score_snapshot.get("sample_confidence"),
            "manual_risk_count": score_snapshot.get("manual_risk_count"),
            "critical_issue_count": score_snapshot.get("critical_issue_count"),
            "serious_issue_count": score_snapshot.get("serious_issue_count"),
            "severity_counts": score_snapshot.get("severity_counts") or {},
        },
        "pages": pages,
    }


def _severity_counts(report: Dict[str, Any]) -> Dict[str, int]:
    counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    snapshot_counts = ((report.get("score_snapshot") or {}).get("severity_counts") or {})
    if isinstance(snapshot_counts, dict) and snapshot_counts:
        for key in counts:
            counts[key] = _safe_int(snapshot_counts.get(key))
        return counts
    for finding in report.get("findings") or []:
        if isinstance(finding, dict):
            severity = _safe_text(finding.get("severity"))
            if severity in counts:
                counts[severity] += 1
    return counts


def _brief_issues(groups: Iterable[Dict[str, Any]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    for group in groups:
        for issue in group.get("issues") or []:
            if isinstance(issue, dict):
                issues.append(
                    {
                        "issue": _safe_text(issue.get("issue")),
                        "suggestion": _safe_text(issue.get("suggestion")),
                    }
                )
            if len(issues) >= 8:
                return issues
    return issues


def _trim_list(value: Any, limit: int) -> List[Any]:
    return list(value[:limit]) if isinstance(value, list) else []


def _score_status(score: int) -> str:
    if score >= 80:
        return "good"
    if score >= 50:
        return "needs_attention"
    return "needs_work"


def _safe_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _safe_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
