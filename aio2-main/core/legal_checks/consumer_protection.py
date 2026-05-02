# -*- coding: utf-8 -*-
"""Consumer protection checks (visibility + best practices + lawyer comments)."""

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from core.legal_checks.best_practices import check_best_practices
from core.legal_checks.lawyer_perspective import attach_lawyer_comments
from core.legal_checks.visibility_checker import VisibilityChecker


class ConsumerProtectionChecker:
    """Wrapper to aggregate consumer protection related checks."""

    def check(self, html: str, url: Optional[str] = None, is_ec: bool = True) -> Dict[str, Any]:
        """Run visibility and best-practice checks and attach lawyer comments.

        Args:
            html: Page HTML content.
            url: Page URL (reserved for future use).
            is_ec: ECサイトの場合は厳格、非ECは参考情報に格下げ。

        Returns:
            Dict with visibility issues, best practices issues, and lawyer report.
        """
        _ = url  # reserved

        visibility_issues: List[Dict[str, Any]] = []
        best_practice_issues: List[Dict[str, Any]] = []
        lawyer_report: List[Dict[str, Any]] = []

        if not html:
            return {
                "visibility": visibility_issues,
                "best_practices": best_practice_issues,
                "lawyer_report": lawyer_report,
            }

        try:
            soup = BeautifulSoup(html, "html.parser")
            visibility_checker = VisibilityChecker()
            visibility_issues = visibility_checker.check_visibility(soup, is_ec=is_ec)
            text = soup.get_text(" ", strip=True)
            if is_ec:
                best_practice_issues = check_best_practices(text)
            else:
                best_practice_issues = []

            if not is_ec:
                for issue in visibility_issues + best_practice_issues:
                    if issue.get("severity") != "info":
                        issue["severity"] = "info"
                    title = issue.get("title") or ""
                    if title and not title.startswith("【参考】"):
                        issue["title"] = f"【参考】{title}"

            combined = visibility_issues + best_practice_issues
            lawyer_report = attach_lawyer_comments(combined)
        except Exception:
            visibility_issues = []
            best_practice_issues = []
            lawyer_report = []

        return {
            "visibility": visibility_issues,
            "best_practices": best_practice_issues,
            "lawyer_report": lawyer_report,
        }
