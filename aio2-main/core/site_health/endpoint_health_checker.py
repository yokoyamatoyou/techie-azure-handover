from __future__ import annotations

import re
import uuid
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core.safe_fetch import safe_fetch_url


SITEMAP_ENDPOINT_PATHS = ("sitemap.xml", "wp-sitemap.xml", "sitemap_index.xml")
ROBOTS_DIRECTIVE_RE = re.compile(r"(?im)^\s*(user-agent|disallow|allow|sitemap)\s*:")
PHP_EOL_SERIES_RE = re.compile(r"\bPHP/?\s*(5\.\d+(?:\.\d+)?|7\.[0-4](?:\.\d+)?)\b", re.I)


def audit_endpoint_health(
    url: str,
    html: str,
    headers: Dict[str, Any] | None = None,
    *,
    has_wordpress_hint: bool = False,
    missing_path: str | None = None,
) -> Dict[str, Any]:
    """Audit a small fixed set of public endpoints without discovery scans."""
    return EndpointHealthChecker(
        url=url,
        html=html,
        headers=headers or {},
        has_wordpress_hint=has_wordpress_hint,
        missing_path=missing_path,
    ).run_all_checks()


class EndpointHealthChecker:
    def __init__(
        self,
        *,
        url: str,
        html: str,
        headers: Dict[str, Any],
        has_wordpress_hint: bool,
        missing_path: str | None = None,
    ) -> None:
        self.url = url
        self.html = html or ""
        self.headers = headers or {}
        self.has_wordpress_hint = has_wordpress_hint
        self.root_url = self._root_url(url)
        self.missing_path = missing_path or f"__kotomigaki_missing_{uuid.uuid4().hex[:12]}/"
        self.homepage_title = self._title(self.html)
        self.homepage_body = self._body_text(self.html)

    def run_all_checks(self) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []
        checked_endpoints: List[Dict[str, Any]] = []

        server_issue = self._check_server_environment_headers()
        if server_issue:
            issues.append(server_issue)

        robots_issue, robots_checked = self._check_robots_txt()
        if robots_checked:
            checked_endpoints.append(robots_checked)
        if robots_issue:
            issues.append(robots_issue)

        for path in SITEMAP_ENDPOINT_PATHS:
            sitemap_issue, sitemap_checked = self._check_sitemap_endpoint(path)
            if sitemap_checked:
                checked_endpoints.append(sitemap_checked)
            if sitemap_issue:
                issues.append(sitemap_issue)

        if not self.has_wordpress_hint:
            wp_json_issue, wp_json_checked = self._check_unused_wordpress_json_endpoint()
            if wp_json_checked:
                checked_endpoints.append(wp_json_checked)
            if wp_json_issue:
                issues.append(wp_json_issue)

        soft_404_issue, soft_404_checked = self._check_single_missing_url()
        if soft_404_checked:
            checked_endpoints.append(soft_404_checked)
        if soft_404_issue:
            issues.append(soft_404_issue)

        penalty = min(sum({"high": 8, "medium": 5, "low": 2}.get(str(item.get("severity")), 2) for item in issues), 20)
        return {
            "status": "warning" if issues else "ok",
            "issues": issues,
            "issue_count": len(issues),
            "checked_endpoints": checked_endpoints,
            "score_penalty": penalty,
        }

    def _check_robots_txt(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        endpoint = urljoin(self.root_url.rstrip("/") + "/", "robots.txt")
        response, checked = self._fetch(endpoint)
        if response is None:
            return None, checked
        status = checked.get("status_code")
        text = str(getattr(response, "text", "") or "")
        content_type = str(checked.get("content_type") or "")
        if status != 200:
            return None, checked
        if self._looks_like_html(text, content_type):
            return (
                self._issue(
                    "robots_txt_html_fake_200",
                    "medium",
                    "robots.txt がHTMLを返している可能性があります",
                    f"`{endpoint}` が 200 OK ですが、robots.txt ではなくHTML相当の内容に見えます。HTTP status={status}, Content-Type={content_type or '-'}。",
                    "サーバー/CMS/CDNのルーティングを確認し、robots.txt として妥当なテキストを返すか、不要なら適切な404にしてください。",
                    endpoint,
                    checked,
                    self._excerpt(text),
                    urgency="すぐ確認",
                ),
                checked,
            )
        if not ROBOTS_DIRECTIVE_RE.search(text):
            return (
                self._issue(
                    "robots_txt_invalid_or_empty",
                    "low",
                    "robots.txt の基本行が見えません",
                    f"`{endpoint}` が 200 OK ですが、User-agent / Disallow / Allow / Sitemap の基本行を確認できませんでした。",
                    "robots.txt の内容を保守会社に確認し、クロール制御とSitemap指定が意図どおりか点検してください。",
                    endpoint,
                    checked,
                    self._excerpt(text),
                    urgency="リニューアル前後で確認",
                ),
                checked,
            )
        return None, checked

    def _check_sitemap_endpoint(self, path: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        endpoint = urljoin(self.root_url.rstrip("/") + "/", path)
        response, checked = self._fetch(endpoint)
        if response is None:
            return None, checked
        status = checked.get("status_code")
        text = str(getattr(response, "text", "") or "")
        content_type = str(checked.get("content_type") or "")
        if status != 200:
            return None, checked
        looks_html = self._looks_like_html(text, content_type)
        if not looks_html:
            return None, checked
        if path.startswith("wp-") and not self.has_wordpress_hint and self._looks_like_homepage(text, checked):
            return (
                self._issue(
                    "unused_endpoint_fake_200",
                    "low",
                    "不要endpointがトップページHTMLを返している可能性があります",
                    f"`/{path}` が 200 OK でトップページ相当HTMLを返している可能性があります。HTTP status={status}, Content-Type={content_type or '-'}。",
                    "WordPressを使っていない場合は、不要なwp系endpointが200で見えないようにルーティング/404設定を確認してください。",
                    endpoint,
                    checked,
                    self._excerpt(text),
                    urgency="リニューアル時で可",
                ),
                checked,
            )
        return (
            self._issue(
                "sitemap_endpoint_html_fake_200",
                "medium",
                "sitemap endpoint がHTMLを返している可能性があります",
                f"`/{path}` が 200 OK ですが、XML sitemap ではなくHTML相当の内容に見えます。HTTP status={status}, Content-Type={content_type or '-'}。",
                "CMS/SEOプラグイン/CDNのsitemap出力を確認し、XMLを返すか、存在しないendpointは404/410にしてください。",
                endpoint,
                checked,
                self._excerpt(text),
                urgency="すぐ確認",
            ),
            checked,
        )

    def _check_unused_wordpress_json_endpoint(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        endpoint = urljoin(self.root_url.rstrip("/") + "/", "wp-json/")
        response, checked = self._fetch(endpoint)
        if response is None:
            return None, checked
        if checked.get("status_code") != 200:
            return None, checked
        text = str(getattr(response, "text", "") or "")
        content_type = str(checked.get("content_type") or "")
        if not self._looks_like_html(text, content_type):
            return None, checked
        if not self._looks_like_homepage(text, checked):
            return None, checked
        return (
            self._issue(
                "unused_endpoint_fake_200",
                "low",
                "不要endpointがトップページHTMLを返している可能性があります",
                "`/wp-json/` がWordPress APIではなくトップページ相当HTMLを返している可能性があります。",
                "WordPressを使っていない場合は、不要なwp系endpointが200で見えないようにルーティング/404設定を確認してください。",
                endpoint,
                checked,
                self._excerpt(text),
                urgency="リニューアル時で可",
            ),
            checked,
        )

    def _check_single_missing_url(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        missing_url = urljoin(self.root_url.rstrip("/") + "/", self.missing_path.lstrip("/"))
        response, checked = self._fetch(missing_url)
        if response is None:
            return None, checked
        status = int(checked.get("status_code") or 0)
        if status in {404, 410}:
            checked["soft_404_status"] = "ok"
            return None, checked
        text = str(getattr(response, "text", "") or "")
        content_type = str(checked.get("content_type") or "")
        if status == 200 and self._looks_like_html(text, content_type) and self._looks_like_homepage(text, checked):
            if self._has_noindex(text):
                checked["soft_404_status"] = "noindex_present"
                return None, checked
            return (
                self._issue(
                    "soft_404_missing_url_200",
                    "medium",
                    "存在しないURLがトップページ相当で200を返す可能性があります",
                    f"存在しない確認用URLが 200 OK でトップページ相当HTMLを返している可能性があります。HTTP status={status}, Content-Type={content_type or '-'}。",
                    "存在しないURLは404/410を返すようにし、トップページへ転送する場合も検索エンジンにsoft 404扱いされないか確認してください。",
                    missing_url,
                    checked,
                    self._excerpt(text),
                    urgency="すぐ確認",
                ),
                checked,
            )
        return None, checked

    def _check_server_environment_headers(self) -> Optional[Dict[str, Any]]:
        exposures: List[Dict[str, str]] = []
        for header_name in ("X-Powered-By", "Server"):
            value = self._header(header_name)
            if not value:
                continue
            lower = value.lower()
            if "php" in lower or "plesklin" in lower:
                exposures.append({"header": header_name, "value": value[:120]})
        if not exposures:
            return None

        haystack = " / ".join(item["value"] for item in exposures)
        eol_match = PHP_EOL_SERIES_RE.search(haystack)
        severity = "medium"
        if eol_match:
            version = eol_match.group(1)
            severity = "high" if version.startswith("5.") or re.match(r"7\.[0-3]\b", version) else "medium"
        elif "plesklin" in haystack.lower():
            severity = "medium"
        else:
            severity = "low"

        checked = {
            "url": self.root_url,
            "status_code": None,
            "content_type": "",
            "headers": exposures,
            "excerpt": haystack[:180],
        }
        exposure_text = " / ".join(f"{item['header']}: {item['value']}" for item in exposures[:3])
        return self._issue(
            "server_environment_header_exposed",
            severity,
            "サーバー/PHP環境情報がHTTPヘッダーに見えます",
            f"HTTPヘッダーに {exposure_text} が見えます。",
            "非表示化は根本対策ではありませんが、PHPバージョンやPleskLin等の露出は減らし、EOL系列の場合は更新計画を保守会社に確認してください。",
            self.root_url,
            checked,
            haystack[:180],
            urgency="すぐ確認" if severity == "high" else "リニューアル前後で確認",
        )

    def _fetch(self, endpoint: str) -> Tuple[Optional[Any], Dict[str, Any]]:
        checked: Dict[str, Any] = {"url": endpoint, "status_code": None, "content_type": "", "final_url": "", "excerpt": ""}
        try:
            response = safe_fetch_url(endpoint, timeout=4.0, max_bytes=256 * 1024, max_redirects=2)
        except Exception as exc:
            checked["error"] = str(exc)[:160]
            return None, checked
        checked["status_code"] = int(getattr(response, "status_code", 0) or 0)
        checked["content_type"] = self._response_header(response, "Content-Type")
        checked["final_url"] = str(getattr(response, "safe_final_url", "") or getattr(response, "url", "") or "")
        checked["redirect_count"] = int(getattr(response, "safe_redirect_count", 0) or 0)
        text = str(getattr(response, "text", "") or "")
        checked["excerpt"] = self._excerpt(text)
        return response, checked

    def _looks_like_homepage(self, html: str, checked: Dict[str, Any]) -> bool:
        final_url = str(checked.get("final_url") or "")
        if self._same_url(final_url, self.root_url):
            return True
        title = self._title(html)
        if title and self.homepage_title and title == self.homepage_title:
            return True
        body = self._body_text(html)
        if not body or not self.homepage_body:
            return False
        return SequenceMatcher(None, body[:3000], self.homepage_body[:3000]).ratio() >= 0.9

    @staticmethod
    def _looks_like_html(text: str, content_type: str) -> bool:
        head = (text or "")[:1200].lower()
        return "text/html" in (content_type or "").lower() or "<html" in head or "<!doctype html" in head

    @staticmethod
    def _has_noindex(html: str) -> bool:
        soup = BeautifulSoup(html or "", "html.parser")
        for meta in soup.find_all("meta"):
            name = str(meta.get("name") or meta.get("http-equiv") or "").lower()
            content = str(meta.get("content") or "").lower()
            if "robots" in name and "noindex" in content:
                return True
        return False

    @staticmethod
    def _title(html: str) -> str:
        soup = BeautifulSoup(html or "", "html.parser")
        title = soup.find("title")
        return re.sub(r"\s+", " ", title.get_text(" ", strip=True)).strip() if title else ""

    @staticmethod
    def _body_text(html: str) -> str:
        soup = BeautifulSoup(html or "", "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()

    @staticmethod
    def _excerpt(text: str, *, limit: int = 180) -> str:
        compact = re.sub(r"\s+", " ", str(text or "")).strip()
        return compact[:limit]

    @staticmethod
    def _same_url(left: str, right: str) -> bool:
        if not left or not right:
            return False
        left_parsed = urlparse(left)
        right_parsed = urlparse(right)
        left_path = (left_parsed.path or "/").rstrip("/") or "/"
        right_path = (right_parsed.path or "/").rstrip("/") or "/"
        return (
            left_parsed.scheme == right_parsed.scheme
            and left_parsed.netloc.lower() == right_parsed.netloc.lower()
            and left_path == right_path
        )

    def _header(self, name: str) -> str:
        target = name.lower()
        for key, value in self.headers.items():
            if str(key).lower() == target:
                return str(value or "").strip()
        return ""

    @staticmethod
    def _response_header(response: Any, name: str) -> str:
        headers = getattr(response, "headers", {}) or {}
        target = name.lower()
        for key, value in headers.items():
            if str(key).lower() == target:
                return str(value or "").strip()
        return ""

    @staticmethod
    def _root_url(url: str) -> str:
        parsed = urlparse(url or "")
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/"
        return url.rstrip("/") + "/"

    @staticmethod
    def _issue(
        issue_id: str,
        severity: str,
        title: str,
        detail: str,
        recommendation: str,
        evidence: str,
        checked: Dict[str, Any],
        excerpt: str,
        *,
        urgency: str,
    ) -> Dict[str, Any]:
        evidence_details = {
            "url": checked.get("url") or evidence,
            "final_url": checked.get("final_url") or checked.get("url") or evidence,
            "status_code": checked.get("status_code"),
            "content_type": checked.get("content_type") or "",
            "excerpt": excerpt or checked.get("excerpt") or "",
            "urgency": urgency,
        }
        if checked.get("headers"):
            evidence_details["headers"] = checked.get("headers")
        return {
            "id": issue_id,
            "severity": severity,
            "issue": title,
            "title": title,
            "detail": detail,
            "recommendation": recommendation,
            "evidence": evidence,
            "evidence_details": evidence_details,
            "confirmation_url": evidence_details["url"],
            "http_status": evidence_details["status_code"],
            "content_type": evidence_details["content_type"],
            "excerpt": evidence_details["excerpt"],
            "urgency": urgency,
        }
