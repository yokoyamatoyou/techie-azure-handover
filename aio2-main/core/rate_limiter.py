# -*- coding: utf-8 -*-
"""ドメインごとのレート制限"""
import time
from collections import defaultdict
from typing import Dict, Optional
from urllib.parse import urlparse

from core.config import config


class RateLimiter:
    """ドメインごとに最低限のアクセス間隔を強制"""

    def __init__(self, interval: Optional[float] = None):
        self.interval = interval if interval is not None else config.CRAWL_INTERVAL_SECONDS
        self._last_access: Dict[str, float] = defaultdict(float)

    def wait(self, url: str) -> None:
        """必要に応じてウェイトを入れる"""
        if not url:
            return
        domain = urlparse(url).netloc
        if not domain:
            return
        elapsed = time.time() - self._last_access[domain]
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self._last_access[domain] = time.time()


rate_limiter = RateLimiter()
