# -*- coding: utf-8 -*-
"""Structured data checker and summarizer."""

import json
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from core.structured_data.schema_suggester import analyze_existing_schema


class StructuredDataChecker:
    """Extract and summarize JSON-LD structured data."""

    def check(self, html: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Analyze structured data from HTML.

        Args:
            html: Page HTML content.
            url: Page URL (reserved for future use).

        Returns:
            Dict with structured data summary.
        """
        _ = url  # reserved

        json_ld = self._extract_json_ld(html)
        existing = analyze_existing_schema(json_ld)
        types = existing.get("types", [])
        type_lc = {str(t).lower() for t in types}

        return {
            "has_json_ld": bool(json_ld),
            "types": types,
            "count": existing.get("count", 0),
            "has_organization": "organization" in type_lc,
            "has_author": "person" in type_lc or "author" in type_lc,
        }

    def _extract_json_ld(self, html: str) -> List[Dict[str, Any]]:
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        json_ld: List[Dict[str, Any]] = []

        for script in soup.find_all("script", {"type": "application/ld+json"}):
            raw = script.string
            if not raw or not raw.strip():
                continue
            try:
                parsed = json.loads(raw)
            except Exception:
                continue

            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        json_ld.append(item)
            elif isinstance(parsed, dict):
                json_ld.append(parsed)

        return json_ld
