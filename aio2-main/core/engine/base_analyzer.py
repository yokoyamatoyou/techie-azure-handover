# -*- coding: utf-8 -*-
"""Base analyzer with common initialization and utilities."""

import os
from typing import Optional

from core.env_keys import resolve_env_var


class BaseAnalyzer:
    """Base class for SEO/AIO analysis with API setup."""

    def __init__(self, analysis_mode: str = "standard"):
        self.analysis_mode = analysis_mode

        self.api_key: Optional[str] = resolve_env_var("OPENAI_API_KEY")
        self.client = None
        self.max_retries = 3
        self.timeout = 30

        if not self.api_key:
            return

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except Exception:
            self.client = None

    def _sanitize_text(self, text: str, max_chars: int = 3000) -> str:
        if not text:
            return ""
        compact = " ".join(text.split())
        return compact[:max_chars] if len(compact) > max_chars else compact
