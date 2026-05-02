"""
Scraper module: Web scraping and robots.txt checking logic.
Extracted from seo_aio_engine.py for better separation of concerns.
"""

import re
from urllib.parse import urlparse, urljoin
from urllib import robotparser
from typing import Dict, Any

from core.config import config
from core.safe_fetch import (
    ContentTooLargeError,
    SafeFetchError,
    TooManyRedirectsError,
    UnsafeURLError,
    safe_fetch_url,
    validate_public_url,
)


class ScrapeBlockedError(Exception):
    """Raised when scraping is blocked by robots.txt or other restrictions."""

    def __init__(self, url: str, reason: str):
        super().__init__(f"SCRAPE_BLOCKED: {reason}")
        self.url = url
        self.reason = reason


class Scraper:
    """Handles web scraping, robots.txt checking, and AI crawler access analysis."""

    _ROBOTS_MAX_BYTES = 512 * 1024
    _LLMS_MAX_BYTES = 1024 * 1024

    def _analyze_llms_quality(
        self,
        *,
        site_url: str,
        found_path: str,
        content: str,
        content_type: str = "",
    ) -> Dict[str, Any]:
        """llms.txtの品質を簡易スコアリング（存在確認より一段深い検証）。"""
        score = 0
        issues: list[str] = []
        recommendations: list[str] = []
        checks: Dict[str, Any] = {}

        text = (content or "").strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        site_netloc = (urlparse(site_url).netloc or "").lower().replace("www.", "")

        # 1) 推奨パス
        preferred_path = found_path == "/llms.txt"
        checks["preferred_path"] = preferred_path
        if preferred_path:
            score += 15
        else:
            issues.append("推奨パス `/llms.txt` ではありません。")
            recommendations.append("可能であれば `https://example.com/llms.txt` に統一してください。")

        # 2) Content-Type
        ct = (content_type or "").lower()
        is_text_plain = "text/plain" in ct
        checks["content_type_text_plain"] = is_text_plain
        if is_text_plain:
            score += 10
        else:
            # 拡張子がtxtの場合は減点を緩和
            if str(found_path).endswith(".txt"):
                score += 5
            issues.append("Content-Type が text/plain ではない可能性があります。")
            recommendations.append("`text/plain; charset=utf-8` で配信してください。")

        # 3) 文字量
        text_length = len(text)
        checks["content_length"] = text_length
        if 200 <= text_length <= 8000:
            score += 15
        elif 50 <= text_length < 200:
            score += 8
            recommendations.append("内容が短いため、重要URLと要約を追加してください。")
        else:
            issues.append("内容が短すぎるか、長すぎる可能性があります。")
            recommendations.append("目安として200-8000文字程度で要点を整理してください。")

        # 4) URL数
        url_pattern = re.compile(r"https?://[^\s<>\"]+")
        urls = sorted(set(url_pattern.findall(text)))
        checks["url_count"] = len(urls)
        if len(urls) >= 3:
            score += 20
        elif len(urls) >= 1:
            score += 10
            recommendations.append("主要ページURLを3件以上記載すると案内性が上がります。")
        else:
            issues.append("本文にURLがほとんど含まれていません。")
            recommendations.append("重要ページの絶対URLを複数記載してください。")

        # 5) 同一ドメイン比率
        same_domain_count = 0
        for u in urls:
            netloc = (urlparse(u).netloc or "").lower().replace("www.", "")
            if site_netloc and netloc.endswith(site_netloc):
                same_domain_count += 1
        checks["same_domain_url_count"] = same_domain_count
        if urls:
            ratio = same_domain_count / max(len(urls), 1)
            checks["same_domain_ratio"] = round(ratio, 2)
            if ratio >= 0.8:
                score += 10
            elif ratio >= 0.5:
                score += 5
            else:
                issues.append("外部ドメインURLの比率が高い可能性があります。")
                recommendations.append("自サイトの重要ページURLを中心に記載してください。")

        # 6) 更新日の明記
        has_updated = bool(
            re.search(r"(最終更新|更新日|last\s*updated|updated\s*at)", text, re.IGNORECASE)
            or re.search(r"20\d{2}[/-]\d{1,2}[/-]\d{1,2}", text)
            or re.search(r"20\d{2}年\d{1,2}月\d{1,2}日", text)
        )
        checks["has_update_date"] = has_updated
        if has_updated:
            score += 10
        else:
            recommendations.append("更新日（例: 2026-02-06）を記載してください。")

        # 7) 読みやすさ（箇条書き/見出し）
        has_structure = any(
            ln.startswith(("-", "*", "#")) or ":" in ln for ln in lines[:40]
        )
        checks["has_structured_lines"] = has_structure
        if has_structure:
            score += 5
        else:
            recommendations.append("見出しや箇条書きで読みやすい構造にしてください。")

        # 8) 1行の長さ（機械処理しやすさ）
        max_line_length = max((len(ln) for ln in lines), default=0)
        checks["max_line_length"] = max_line_length
        if max_line_length <= 240:
            score += 5
        else:
            issues.append("1行が長すぎるため可読性が低下する可能性があります。")
            recommendations.append("1行を短く分割してください（目安: 240文字以下）。")

        quality_score = max(0, min(100, int(score)))
        if quality_score >= 80:
            quality_level = "high"
        elif quality_score >= 50:
            quality_level = "medium"
        else:
            quality_level = "low"

        # 重複除去
        uniq_issues = list(dict.fromkeys(issues))
        uniq_recs = list(dict.fromkeys(recommendations))

        return {
            "quality_score": quality_score,
            "quality_level": quality_level,
            "quality_issues": uniq_issues[:6],
            "quality_recommendations": uniq_recs[:6],
            "quality_checks": checks,
        }

    def check_scrape_permission(self, url: str) -> Dict[str, Any]:
        """robots.txtの一般クローラ許可を確認"""
        result = {"allowed": True, "robots_url": None, "error": None}
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return result
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            validate_public_url(url)
            validate_public_url(robots_url)
            parser = robotparser.RobotFileParser()
            parser.set_url(robots_url)
            response = safe_fetch_url(
                robots_url,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.TIMEOUT_DEFAULT,
                max_bytes=self._ROBOTS_MAX_BYTES,
            )
            result["robots_url"] = robots_url
            if not response.ok:
                # robots.txt が存在しないケースはクロール禁止ではないため許可扱いにする。
                if response.status_code == 404:
                    result["allowed"] = True
                    return result
                result["allowed"] = False
                result["error"] = f"robots_http_{response.status_code}"
                return result
            if response.ok and response.text:
                parser.parse(response.text.splitlines())
            result["allowed"] = parser.can_fetch("*", url)
        except (UnsafeURLError, TooManyRedirectsError, ContentTooLargeError, SafeFetchError) as exc:
            result["allowed"] = False
            result["error"] = str(exc)
        except Exception as exc:
            result["error"] = str(exc)
        return result

    def check_robots_txt(self, url: str) -> Dict[str, Any]:
        """robots.txtをチェックしGPTBotなどの許可状況を確認"""
        result = {"exists": False, "gptbot_allowed": None, "status_code": None, "has_gptbot_section": False}
        try:
            robots_url = urljoin(url, '/robots.txt')
            validate_public_url(url)
            resp = safe_fetch_url(
                robots_url,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.TIMEOUT_DEFAULT,
                max_bytes=self._ROBOTS_MAX_BYTES,
            )
            result["status_code"] = resp.status_code
            if resp.ok and resp.text:
                result["exists"] = True
                lines = resp.text.splitlines()
                lower_lines = [ln.strip().lower() for ln in lines]
                gptbot_allowed = None
                has_gptbot_section = False
                wildcard_blocked = False
                has_wildcard_section = False
                current_agent = None
                for ln in lower_lines:
                    if ln.startswith('user-agent:'):
                        current_agent = ln.split(':', 1)[1].strip()
                        if current_agent == 'gptbot':
                            has_gptbot_section = True
                        elif current_agent == '*':
                            has_wildcard_section = True
                        continue
                    if ln.startswith('disallow:'):
                        val = ln.split(':', 1)[1].strip()
                        is_root_blocked = (val == '/' or val == '/*')
                        if current_agent == 'gptbot' and is_root_blocked:
                            gptbot_allowed = False
                        elif current_agent == '*' and is_root_blocked:
                            wildcard_blocked = True
                    if ln.startswith('allow:'):
                        val = ln.split(':', 1)[1].strip()
                        is_root_allowed = (val == '/' or val == '/*')
                        if current_agent == 'gptbot':
                            gptbot_allowed = True if gptbot_allowed is None else gptbot_allowed
                        elif current_agent == '*' and is_root_allowed:
                            wildcard_blocked = False
                if gptbot_allowed is None and has_wildcard_section:
                    gptbot_allowed = not wildcard_blocked
                elif gptbot_allowed is None:
                    gptbot_allowed = True
                result["has_gptbot_section"] = has_gptbot_section
                result["gptbot_allowed"] = gptbot_allowed
        except (UnsafeURLError, TooManyRedirectsError, ContentTooLargeError, SafeFetchError):
            pass
        except Exception:
            pass
        return result

    def check_ai_crawler_access(self, url: str) -> Dict[str, Any]:
        """主要AIクローラーのrobots.txt許可状況を簡易判定"""
        result = {
            "exists": False,
            "status_code": None,
            "bots": {
                "oai-searchbot": None,
                "perplexitybot": None,
                "googlebot": None,
                "gptbot": None,
                # Google-Extended は Google Search の掲載/ランキングに影響しない（制御トークン）
                "google-extended": None,
            },
        }

        def _init_rule():
            return {"allow_root": False, "disallow_root": False}

        def _merge_rule(rule, directive, value):
            val = (value or "").strip()
            if directive == "disallow" and val == "":
                rule["allow_root"] = True
                return
            is_root = val in ("/", "/*")
            if directive == "allow" and is_root:
                rule["allow_root"] = True
            elif directive == "disallow" and is_root:
                rule["disallow_root"] = True

        def _resolve_agent_allowed(agent, rules, wildcard_rule):
            rule = rules.get(agent)
            if rule:
                if rule["allow_root"]:
                    return True
                if rule["disallow_root"]:
                    return False
                return None
            if wildcard_rule:
                if wildcard_rule["allow_root"]:
                    return True
                if wildcard_rule["disallow_root"]:
                    return False
            return True

        try:
            robots_url = urljoin(url, "/robots.txt")
            validate_public_url(url)
            resp = safe_fetch_url(
                robots_url,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.TIMEOUT_DEFAULT,
                max_bytes=self._ROBOTS_MAX_BYTES,
            )
            result["status_code"] = resp.status_code
            if not (resp.ok and resp.text):
                return result
            result["exists"] = True
            rules = {}
            wildcard_rule = None
            current_agents = []
            for raw_line in resp.text.splitlines():
                line = raw_line.split("#", 1)[0].strip().lower()
                if not line:
                    continue
                if line.startswith("user-agent:"):
                    agent = line.split(":", 1)[1].strip()
                    current_agents = [agent] if agent else []
                    if agent and agent not in rules:
                        rules[agent] = _init_rule()
                    continue
                if line.startswith("allow:") or line.startswith("disallow:"):
                    if not current_agents:
                        continue
                    directive, value = line.split(":", 1)
                    for agent in current_agents:
                        if agent == "*":
                            if wildcard_rule is None:
                                wildcard_rule = _init_rule()
                            _merge_rule(wildcard_rule, directive, value)
                        else:
                            if agent not in rules:
                                rules[agent] = _init_rule()
                            _merge_rule(rules[agent], directive, value)
            bots = result["bots"]
            for agent in bots.keys():
                bots[agent] = _resolve_agent_allowed(agent, rules, wildcard_rule)
        except (UnsafeURLError, TooManyRedirectsError, ContentTooLargeError, SafeFetchError):
            pass
        except Exception:
            pass
        return result

    def check_llms_txt(self, url: str) -> Dict[str, Any]:
        """
        Extended llms.txt checker.
        Checks multiple paths: /llms.txt, /llms-full.txt, /llms.md, /gpt.txt, /gpt.md
        """
        result = {
            "exists": False,
            "content": None,
            "valid": False,
            "found_paths": [],
            "checked_paths": [],
            "quality_score": 0,
            "quality_level": "low",
            "quality_issues": [],
            "quality_recommendations": [],
            "quality_checks": {},
        }

        # Extended paths to check
        paths_to_check = [
            "/llms.txt",
            "/llms-full.txt",
            "/llms.md",
            "/gpt.txt",
            "/gpt.md",
        ]

        first_content = ""
        first_path = ""
        first_content_type = ""

        for path in paths_to_check:
            result["checked_paths"].append(path)
            try:
                llms_url = urljoin(url, path)
                validate_public_url(url)
                resp = safe_fetch_url(
                    llms_url,
                    headers={"User-Agent": config.USER_AGENT},
                    timeout=config.TIMEOUT_DEFAULT,
                    max_bytes=self._LLMS_MAX_BYTES,
                )
                if resp.ok and resp.text and len(resp.text.strip()) > 10:
                    result["exists"] = True
                    result["found_paths"].append(path)
                    # Store content from the first valid file found
                    if result["content"] is None:
                        result["content"] = resp.text[:500]
                        first_content = resp.text
                        first_path = path
                        first_content_type = str(resp.headers.get("Content-Type", ""))
            except (UnsafeURLError, TooManyRedirectsError, ContentTooLargeError, SafeFetchError):
                continue
            except Exception:
                continue

        if result["exists"] and first_content:
            quality = self._analyze_llms_quality(
                site_url=url,
                found_path=first_path,
                content=first_content,
                content_type=first_content_type,
            )
            result.update(quality)
            result["valid"] = result.get("quality_score", 0) >= 50

        return result
