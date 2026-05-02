import os
import sqlite3
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict

import requests

from core.config import config


_DEFAULT_TTL_DAYS = 30
_WIKIDATA_ENDPOINT = "https://www.wikidata.org/w/api.php"
_DEFAULT_USER_AGENT = "KotomigakiAIO/3.0 (analysis tool)"
logger = logging.getLogger(__name__)

# Avoid overly generic terms that are unlikely to be helpful for QID linking.
_GENERIC_BLACKLIST = {
    "こと", "もの", "それ", "これ", "あれ", "今回", "当社", "弊社", "商品", "サービス",
    "情報", "詳細", "公式", "お問い合わせ", "価格", "料金", "会社", "企業", "サイト",
    "ページ", "紹介", "概要", "方法", "理由",
}


@dataclass
class WikidataMatch:
    term: str
    qid: str
    label: str
    description: str
    source: str


class WikidataCache:
    def __init__(self, db_path: str, ttl_days: int = _DEFAULT_TTL_DAYS):
        self.db_path = db_path
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        self._ensure_db()

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS wikidata_cache (
                    term TEXT PRIMARY KEY,
                    qid TEXT,
                    label TEXT,
                    description TEXT,
                    updated_at INTEGER
                )
                """
            )
            conn.commit()

    def get(self, term: str) -> Optional[Dict[str, str]]:
        if not term:
            return None
        now = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT qid, label, description, updated_at FROM wikidata_cache WHERE term = ?",
                (term,),
            ).fetchone()
        if not row:
            return None
        qid, label, description, updated_at = row
        if not updated_at or now - int(updated_at) > self.ttl_seconds:
            return None
        return {"qid": qid, "label": label or "", "description": description or ""}

    def set(self, term: str, qid: str, label: str, description: str) -> None:
        if not term:
            return
        now = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO wikidata_cache (term, qid, label, description, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (term, qid, label or "", description or "", now),
            )
            conn.commit()


class WikidataClient:
    def __init__(
        self,
        cache_path: Optional[str] = None,
        ttl_days: int = _DEFAULT_TTL_DAYS,
        min_interval_sec: float = 0.5,
        user_agent: Optional[str] = None,
    ):
        if cache_path is None:
            cache_path = os.path.join("outputs", "wikidata_cache.sqlite")
        self.cache = WikidataCache(cache_path, ttl_days=ttl_days)
        self.min_interval_sec = min_interval_sec
        self._last_call_at = 0.0
        self.last_error: Optional[str] = None
        self.user_agent = user_agent or os.getenv("WIKIDATA_USER_AGENT", _DEFAULT_USER_AGENT)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            }
        )

    def _is_blacklisted(self, term: str) -> bool:
        if not term or len(term) < 2:
            return True
        if term.isdigit():
            return True
        return term in _GENERIC_BLACKLIST

    def search(self, term: str, language: str = "ja") -> Optional[WikidataMatch]:
        self.last_error = None
        if not term or self._is_blacklisted(term):
            return None

        cached = self.cache.get(term)
        if cached:
            return WikidataMatch(
                term=term,
                qid=cached.get("qid", ""),
                label=cached.get("label", ""),
                description=cached.get("description", ""),
                source="cache",
            )

        # Rate limit
        elapsed = time.time() - self._last_call_at
        if elapsed < self.min_interval_sec:
            time.sleep(self.min_interval_sec - elapsed)

        params = {
            "action": "wbsearchentities",
            "search": term,
            "language": language,
            "format": "json",
            "limit": 1,
        }
        try:
            resp = self.session.get(_WIKIDATA_ENDPOINT, params=params, timeout=config.TIMEOUT_DEFAULT)
            self._last_call_at = time.time()
            if resp.status_code != 200:
                self.last_error = f"http_{resp.status_code}"
                logger.warning("Wikidata API HTTP %s for term=%s", resp.status_code, term)
                return None
            data = resp.json()
            results = data.get("search", []) or []
            if not results and language != "en":
                # Fallback to English if Japanese search yields no results
                return self.search(term, language="en")
            if not results:
                self.last_error = "not_found"
                return None
            top = results[0]
            qid = top.get("id") or ""
            label = top.get("label") or ""
            description = top.get("description") or ""
            if qid:
                self.cache.set(term, qid, label, description)
                return WikidataMatch(term=term, qid=qid, label=label, description=description, source="api")
        except Exception as e:
            self.last_error = str(e)
            logger.warning("Wikidata API request error for term=%s: %s", term, e)
            return None
        return None
