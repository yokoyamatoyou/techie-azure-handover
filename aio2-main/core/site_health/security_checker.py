# -*- coding: utf-8 -*-
"""セキュリティ基本チェッカー（公開情報ベースの軽量チェックのみ）"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from core.safe_fetch import safe_fetch_url
from core.site_health.endpoint_health_checker import audit_endpoint_health
from core.site_health.vulnerability_intelligence import (
    build_known_vulnerability_issue,
    match_known_vulnerabilities_for_components,
)


SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "name_simple": "常時HTTPS強制",
        "importance": "high",
        "risk": "中間者攻撃",
        "description": "HTTPからHTTPSへの自動転送を強制",
        "recommendation": "max-age=31536000; includeSubDomains を設定"
    },
    "X-Frame-Options": {
        "name_simple": "埋め込み防止",
        "importance": "medium",
        "risk": "クリックジャッキング",
        "description": "他サイトへのiframe埋め込みを防止",
        "recommendation": "DENY または SAMEORIGIN を設定"
    },
    "X-Content-Type-Options": {
        "name_simple": "ファイル形式の厳格化",
        "importance": "medium",
        "risk": "MIMEスニッフィング",
        "description": "ブラウザによるファイル形式の推測を防止",
        "recommendation": "nosniff を設定"
    },
    "Content-Security-Policy": {
        "name_simple": "スクリプト実行制限",
        "importance": "high",
        "risk": "XSS攻撃",
        "description": "不正なスクリプトの実行を防止",
        "recommendation": "適切なポリシーを設定（専門家に相談推奨）"
    },
    "X-XSS-Protection": {
        "name_simple": "XSS防止（旧式）",
        "importance": "low",
        "risk": "XSS攻撃",
        "description": "ブラウザのXSSフィルター（現在は非推奨）",
        "recommendation": "CSPの設定を優先"
    },
    "Referrer-Policy": {
        "name_simple": "参照元情報の制御",
        "importance": "low",
        "risk": "情報漏洩",
        "description": "リンク先に送信する参照元情報を制御",
        "recommendation": "strict-origin-when-cross-origin を推奨"
    },
    "Permissions-Policy": {
        "name_simple": "機能制限",
        "importance": "low",
        "risk": "不要なブラウザ機能利用の懸念",
        "description": "カメラ・マイク等の機能使用を制限",
        "recommendation": "不要な機能を無効化"
    }
}

RISKY_EXTERNAL_ASSET_DOMAINS: Tuple[str, ...] = (
    "polyfill.io",
    "bootcdn.net",
    "bootcss.com",
    "staticfile.net",
    "staticfile.org",
    "unionadjs.com",
    "xhsbpza.com",
    "union.macoms.la",
    "newcrbpc.com",
    "googie-anaiytics.com",
    "polyfill.site",
    "polyfillcache.com",
)

RELATED_EXTERNAL_TRACE_DOMAINS: Tuple[str, ...] = (
    "kuurza.com",
)

JQUERY_ASSET_VERSION_MAX_BYTES = 256 * 1024


class SecurityChecker:
    """セキュリティ基本チェッカー"""

    def __init__(
        self,
        url: str,
        headers: Dict,
        html: str,
        sitemap_info: Optional[Dict[str, Any]] = None,
        *,
        enable_endpoint_health: bool = True,
    ):
        self.url = url
        self.headers = headers or {}
        self.html = html
        self.sitemap_info = sitemap_info or {}
        self.enable_endpoint_health = enable_endpoint_health
        self.soup = BeautifulSoup(html, 'html.parser')
        self.parsed_url = urlparse(url)

    def check_https(self) -> Dict:
        """HTTPS対応チェック"""
        is_https = self.parsed_url.scheme == 'https'

        return {
            "check": "HTTPS対応",
            "name_simple": "通信の暗号化",
            "status": "ok" if is_https else "warning",
            "value": "対応済み" if is_https else "未対応",
            "risk": "通信内容が盗聴される可能性" if not is_https else None,
            "recommendation": "SSL証明書を取得してHTTPS化してください" if not is_https else None
        }

    def check_security_headers(self) -> Dict:
        """セキュリティヘッダーチェック"""
        results = []

        for header_name, config in SECURITY_HEADERS.items():
            header_value = None
            for key, value in self.headers.items():
                if key.lower() == header_name.lower():
                    header_value = value
                    break

            if header_value:
                status = "ok"
                value = header_value[:100]
            else:
                status = "not_found"
                value = None

            results.append({
                "header": header_name,
                "name_simple": config["name_simple"],
                "importance": config["importance"],
                "status": status,
                "value": value,
                "risk": config["risk"] if status == "not_found" else None,
                "recommendation": config["recommendation"] if status == "not_found" else None
            })

        high_missing = len([r for r in results if r["importance"] == "high" and r["status"] == "not_found"])
        medium_missing = len([r for r in results if r["importance"] == "medium" and r["status"] == "not_found"])

        return {
            "headers": results,
            "high_missing": high_missing,
            "medium_missing": medium_missing,
            "found_count": len([r for r in results if r["status"] == "ok"])
        }

    def check_mixed_content(self) -> Dict:
        """混合コンテンツチェック"""
        if self.parsed_url.scheme != 'https':
            return {
                "check": "混合コンテンツ",
                "status": "skip",
                "reason": "HTTPSサイトでないためスキップ"
            }

        http_resources = []

        for img in self.soup.find_all('img', src=True):
            src = img.get('src', '')
            if src.startswith('http://'):
                http_resources.append({"type": "image", "url": src[:100]})

        for script in self.soup.find_all('script', src=True):
            src = script.get('src', '')
            if src.startswith('http://'):
                http_resources.append({"type": "script", "url": src[:100]})

        for link in self.soup.find_all('link', href=True):
            if link.get('rel') == ['stylesheet']:
                href = link.get('href', '')
                if href.startswith('http://'):
                    http_resources.append({"type": "stylesheet", "url": href[:100]})

        return {
            "check": "混合コンテンツ",
            "name_simple": "暗号化されていない要素",
            "status": "ok" if len(http_resources) == 0 else "warning",
            "count": len(http_resources),
            "resources": http_resources[:10],
            "risk": "ブラウザに警告が表示される可能性" if http_resources else None
        }

    def check_form_security(self) -> Dict:
        """フォームのセキュリティチェック"""
        forms = self.soup.find_all('form')
        issues = []

        for i, form in enumerate(forms):
            action = form.get('action', '')

            if action.startswith('http://'):
                issues.append({
                    "form_index": i,
                    "issue": "フォームの送信先がHTTP",
                    "action": action[:100]
                })

            password_fields = form.find_all('input', type='password')
            if password_fields and not action.startswith('https://') and not action.startswith('/'):
                issues.append({
                    "form_index": i,
                    "issue": "パスワードフィールドがあるがHTTPS送信でない可能性"
                })

        return {
            "check": "フォームセキュリティ",
            "name_simple": "フォームの安全性",
            "form_count": len(forms),
            "status": "ok" if len(issues) == 0 else "warning",
            "issues": issues
        }

    def check_public_technology_risks(self) -> Dict[str, Any]:
        """公開HTML/headers/既知公開endpointから技術的な露出リスクを確認する。"""
        issues: List[Dict[str, Any]] = []
        signals: Dict[str, Any] = {}

        generator = self._extract_generator_meta()
        if generator:
            signals["generator"] = generator
            generator_lower = generator.lower()
            if "wordpress" in generator_lower:
                version = self._extract_version(generator)
                severity = "medium" if version else "low"
                detail = f"CMS generator に `{generator}` が表示されています。"
                if version:
                    detail += " WordPress本体の世代を外部から推測できます。"
                issues.append(
                    self._issue(
                        "cms_generator_public",
                        severity,
                        "CMSバージョン情報が公開されています",
                        detail,
                        "本体・テーマ・プラグインを更新し、generator meta の公開要否を確認してください。",
                        generator,
                    )
                )

        script_rows, stylesheet_rows = self._collect_external_resources()
        library_findings = self._detect_library_versions(script_rows)
        library_findings.extend(self._detect_jquery_versions_from_asset_content(script_rows, library_findings))
        if library_findings:
            signals["library_versions"] = library_findings

        fixed_vulnerability_report = match_known_vulnerabilities_for_components(library_findings)
        if fixed_vulnerability_report.get("status") != "not_checked":
            signals["fixed_vulnerability_intelligence"] = fixed_vulnerability_report
        fixed_vulnerability_issue = build_known_vulnerability_issue(fixed_vulnerability_report)
        if fixed_vulnerability_issue:
            issues.append(fixed_vulnerability_issue)

        for finding in library_findings:
            if finding.get("library") == "jquery" and self._version_lt(finding.get("version"), (3, 5, 0)):
                issues.append(
                    self._issue(
                        "jquery_before_3_5",
                        "high",
                        "古いjQueryが読み込まれています",
                        f"jQuery {finding.get('version')} が `{finding.get('url')}` から読み込まれています。",
                        "jQuery 3.5.0以上への更新、依存テーマ/プラグインの互換確認、自前配信への変更を検討してください。",
                        finding.get("url", ""),
                    )
                )

        frontend_asset_inventory = self._detect_outdated_frontend_assets(script_rows, stylesheet_rows, library_findings)
        if frontend_asset_inventory:
            signals["frontend_asset_inventory"] = frontend_asset_inventory[:12]
            sample_urls = [item.get("url", "") for item in frontend_asset_inventory[:4] if item.get("url")]
            asset_names = []
            for item in frontend_asset_inventory:
                label = str(item.get("label") or item.get("library") or "").strip()
                if label and label not in asset_names:
                    asset_names.append(label)
            severity = "medium" if any(item.get("severity") == "medium" for item in frontend_asset_inventory) else "low"
            issues.append(
                self._issue(
                    "outdated_frontend_asset",
                    severity,
                    "古い可能性のあるフロントエンド資産があります",
                    f"URLから {', '.join(asset_names[:6])} の読み込みを確認しました。",
                    "古い可能性のあるフロントエンド資産が残っています。テーマ・プラグイン・CDN読み込みの棚卸しをしてください。",
                    " / ".join(sample_urls),
                )
            )

        suspicious_assets = self._detect_suspicious_external_assets(script_rows, stylesheet_rows)
        if suspicious_assets:
            signals["suspicious_external_assets"] = suspicious_assets[:8]
            risky_assets = [
                item for item in suspicious_assets
                if item.get("classification") == "risky_cdn"
            ]
            sample_urls = [item.get("url", "") for item in suspicious_assets[:4] if item.get("url")]
            domains = sorted({
                str(item.get("matched_domain") or item.get("host") or "")
                for item in suspicious_assets
                if item.get("matched_domain") or item.get("host")
            })
            related_only = bool(suspicious_assets) and not risky_assets
            has_script = any(item.get("kind") == "script" for item in risky_assets)
            severity = "low" if related_only else ("high" if has_script else "medium")
            issues.append(
                self._issue(
                    "suspicious_external_asset_domain",
                    severity,
                    "要確認の外部アセットドメイン参照があります",
                    f"公開HTML内で {', '.join(domains[:5])} への参照を確認しました。",
                    "該当script/link/iframeの必要性を確認し、不要なら削除してください。必要な場合も信頼できるCDNまたは自社配信へ置き換え、CSP/SRIと外部通信先の棚卸しを行ってください。",
                    " / ".join(sample_urls),
                )
            )

        sri_candidates = [
            row for row in script_rows + stylesheet_rows
            if row.get("external") and row.get("sri_candidate") and not row.get("integrity")
        ]
        if sri_candidates:
            signals["external_dependency_count"] = len(sri_candidates)
            sample_urls = [row.get("url", "") for row in sri_candidates[:4] if row.get("url")]
            issues.append(
                self._issue(
                    "external_cdn_without_sri",
                    "medium",
                    "外部CDN資産にSRIがありません",
                    f"改ざん検知なしで外部CDN資産を {len(sri_candidates)} 件読み込んでいます。",
                    "静的CDN資産は自前配信または integrity/crossorigin 付きにし、CSPと合わせて制限してください。",
                    " / ".join(sample_urls),
                )
            )

        ua_tags = sorted(set(re.findall(r"UA-\d+-\d+", self.html or "", flags=re.IGNORECASE)))
        if ua_tags:
            signals["universal_analytics_ids"] = ua_tags[:5]
            issues.append(
                self._issue(
                    "universal_analytics_tag",
                    "low",
                    "停止済みのUniversal Analyticsタグが残っています",
                    f"{', '.join(ua_tags[:3])} がページ内に残っています。",
                    "GA4タグへ整理し、不要なUAタグと関連イベントを削除してください。",
                    ", ".join(ua_tags[:3]),
                )
            )

        old_polyfills = self._detect_old_polyfills(script_rows)
        if old_polyfills:
            signals["old_polyfills"] = old_polyfills[:5]
            issues.append(
                self._issue(
                    "legacy_ie_polyfills",
                    "low",
                    "旧IE向けポリフィルが残っています",
                    f"{', '.join(old_polyfills[:3])} が読み込まれています。",
                    "IE8/9対応が不要であれば削除し、外部CDN依存と表示速度の負担を減らしてください。",
                    ", ".join(old_polyfills[:3]),
                )
            )

        target_blank_links = self._detect_target_blank_without_noopener()
        if target_blank_links:
            signals["target_blank_without_noopener"] = target_blank_links[:8]
            issues.append(
                self._issue(
                    "target_blank_without_noopener",
                    "low",
                    'target="_blank" の rel 属性が不足しています',
                    f"外部リンクなど {len(target_blank_links)} 件で noopener が確認できませんでした。",
                    'target="_blank" を使うリンクには rel="noopener noreferrer" を付け、遷移先ページから元ページを操作されないようにしてください。',
                    " / ".join(target_blank_links[:4]),
                )
            )

        internal_http_links = self._detect_internal_http_navigation()
        if internal_http_links:
            signals["internal_http_navigation"] = internal_http_links[:10]
            sample_urls = [item.get("url", "") for item in internal_http_links[:4] if item.get("url")]
            issue_types = sorted({str(item.get("type") or "") for item in internal_http_links if item.get("type")})
            issues.append(
                self._issue(
                    "internal_http_navigation_link",
                    "medium",
                    "HTTPSページ内にHTTPの内部導線が残っています",
                    f"同一ドメイン内のHTTPリンク/フォーム送信先を {len(internal_http_links)} 件確認しました。種別: {', '.join(issue_types[:3])}。",
                    "内部リンク、問い合わせ、資料請求などの導線をHTTPS URLまたは相対URLへ統一してください。",
                    " / ".join(sample_urls),
                )
            )

        form_audit = self._audit_forms()
        if form_audit.get("form_count"):
            signals["forms"] = form_audit
        for issue in form_audit.get("issues") or []:
            issues.append(issue)

        rest_issue, rest_signal = self._check_wordpress_rest_users()
        if rest_signal:
            signals["wordpress_rest"] = rest_signal
        if rest_issue:
            issues.append(rest_issue)

        sitemap_issue, sitemap_signal = self._check_sitemap_freshness()
        if sitemap_signal:
            signals["sitemap"] = sitemap_signal
        if sitemap_issue:
            issues.append(sitemap_issue)

        sitemap_availability_issue, sitemap_availability_signal = self._check_sitemap_availability()
        if sitemap_availability_signal:
            signals["sitemap_availability"] = sitemap_availability_signal
        if sitemap_availability_issue:
            issues.append(sitemap_availability_issue)

        visible_freshness_issue, visible_freshness_signal = self._check_visible_update_freshness()
        if visible_freshness_signal:
            signals["visible_update_freshness"] = visible_freshness_signal
        if visible_freshness_issue:
            issues.append(visible_freshness_issue)

        update_consistency_issue, update_consistency_signal = self._check_update_signal_consistency(
            sitemap_signal=sitemap_signal,
            visible_signal=visible_freshness_signal,
            sitemap_unavailable=bool(sitemap_availability_issue),
        )
        if update_consistency_signal:
            signals["update_signal_consistency"] = update_consistency_signal
        if update_consistency_issue:
            issues.append(update_consistency_issue)

        if self.enable_endpoint_health:
            endpoint_health = audit_endpoint_health(
                self.url,
                self.html,
                self.headers,
                has_wordpress_hint=self._has_wordpress_hint(),
            )
            if endpoint_health:
                signals["endpoint_health"] = {
                    key: value
                    for key, value in endpoint_health.items()
                    if key != "issues"
                }
            for issue in endpoint_health.get("issues") or []:
                issues.append(issue)

        severity_score = {"high": 10, "medium": 5, "low": 2}
        penalty = min(sum(severity_score.get(item.get("severity"), 1) for item in issues if not item.get("score_exempt")), 25)
        return {
            "check": "公開技術リスク",
            "name_simple": "公開設定・外部依存の健全性",
            "status": "ok" if not issues else "warning",
            "issues": issues,
            "signals": signals,
            "issue_count": len(issues),
            "score_penalty": penalty,
        }

    def run_all_checks(self) -> Dict:
        """全チェック実行"""
        https_check = self.check_https()
        headers_check = self.check_security_headers()
        mixed_content = self.check_mixed_content()
        form_security = self.check_form_security()
        public_technology_risks = self.check_public_technology_risks()

        score = 0
        if https_check["status"] == "ok":
            score += 30

        header_score = headers_check["found_count"] / len(SECURITY_HEADERS) * 40
        score += int(header_score)

        if mixed_content["status"] == "ok":
            score += 15

        if form_security["status"] == "ok":
            score += 15

        score = max(0, score - int(public_technology_risks.get("score_penalty") or 0))

        if score >= 70:
            risk_level = "low"
        elif score >= 40:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "https": https_check,
            "headers": headers_check,
            "mixed_content": mixed_content,
            "form_security": form_security,
            "public_technology_risks": public_technology_risks,
            "score": score,
            "risk_level": risk_level
        }

    def _extract_generator_meta(self) -> str:
        tag = self.soup.find("meta", attrs={"name": re.compile(r"^generator$", re.I)})
        if not tag:
            return ""
        return str(tag.get("content") or "").strip()

    @staticmethod
    def _extract_version(text: str) -> str:
        match = re.search(r"(\d+(?:\.\d+){1,3})", text or "")
        return match.group(1) if match else ""

    @staticmethod
    def _parse_version(value: Any) -> Tuple[int, ...]:
        raw = str(value or "").strip()
        parts = re.findall(r"\d+", raw)
        return tuple(int(part) for part in parts[:4])

    @classmethod
    def _version_lt(cls, value: Any, minimum: Tuple[int, ...]) -> bool:
        parsed = cls._parse_version(value)
        if not parsed:
            return False
        width = max(len(parsed), len(minimum))
        return parsed + (0,) * (width - len(parsed)) < minimum + (0,) * (width - len(minimum))

    def _resource_url(self, raw_url: str) -> str:
        if not raw_url:
            return ""
        raw_url = raw_url.strip()
        if raw_url.startswith("//"):
            scheme = self.parsed_url.scheme or "https"
            return f"{scheme}:{raw_url}"
        return urljoin(self.url, raw_url)

    def _collect_external_resources(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        scripts: List[Dict[str, Any]] = []
        stylesheets: List[Dict[str, Any]] = []
        own_host = (self.parsed_url.hostname or self.parsed_url.netloc or "").lower()

        for tag in self.soup.find_all("script", src=True):
            url = self._resource_url(str(tag.get("src") or ""))
            parsed = urlparse(url)
            host = (parsed.hostname or parsed.netloc or "").lower()
            scripts.append(
                {
                    "url": url,
                    "host": host,
                    "external": bool(host and host != own_host),
                    "integrity": str(tag.get("integrity") or "").strip(),
                    "sri_candidate": self._is_static_cdn_host(host),
                }
            )

        for tag in self.soup.find_all("link", href=True):
            rel_values = [str(item).lower() for item in (tag.get("rel") or [])]
            if "stylesheet" not in rel_values:
                continue
            url = self._resource_url(str(tag.get("href") or ""))
            parsed = urlparse(url)
            host = (parsed.hostname or parsed.netloc or "").lower()
            stylesheets.append(
                {
                    "url": url,
                    "host": host,
                    "external": bool(host and host != own_host),
                    "integrity": str(tag.get("integrity") or "").strip(),
                    "sri_candidate": self._is_static_cdn_host(host),
                }
            )
        return scripts, stylesheets

    @staticmethod
    def _is_static_cdn_host(host: str) -> bool:
        host = (host or "").lower()
        return any(
            marker in host
            for marker in (
                "ajax.googleapis.com",
                "cdnjs.cloudflare.com",
                "code.jquery.com",
                "unpkg.com",
                "jsdelivr.net",
                "cdn.jsdelivr.net",
            )
        )

    @staticmethod
    def _host_matches_domain(host: str, domain: str) -> bool:
        normalized_host = (host or "").lower().rstrip(".")
        normalized_domain = (domain or "").lower().rstrip(".")
        return normalized_host == normalized_domain or normalized_host.endswith(f".{normalized_domain}")

    def _detect_suspicious_external_assets(
        self,
        scripts: List[Dict[str, Any]],
        stylesheets: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        candidates = [
            *[("script", row) for row in scripts],
            *[("stylesheet", row) for row in stylesheets],
        ]
        for kind, row in candidates:
            host = str(row.get("host") or "").lower().rstrip(".")
            url = str(row.get("url") or "")
            if not host or not url:
                continue
            for domain in RISKY_EXTERNAL_ASSET_DOMAINS:
                if self._host_matches_domain(host, domain):
                    rows.append(
                        {
                            "kind": kind,
                            "url": url,
                            "host": host,
                            "matched_domain": domain,
                            "classification": "risky_cdn",
                        }
                    )
                    break
            else:
                for domain in RELATED_EXTERNAL_TRACE_DOMAINS:
                    if self._host_matches_domain(host, domain):
                        rows.append(
                            {
                                "kind": kind,
                                "url": url,
                                "host": host,
                                "matched_domain": domain,
                                "classification": "related_trace",
                            }
                        )
                        break

        deduped: List[Dict[str, str]] = []
        seen = set()
        for row in rows:
            key = (row.get("kind", ""), row.get("url", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped

    def _detect_target_blank_without_noopener(self) -> List[str]:
        links: List[str] = []
        for tag in self.soup.find_all("a", href=True):
            target = str(tag.get("target") or "").strip().lower()
            if target != "_blank":
                continue
            rel_value = tag.get("rel") or []
            if isinstance(rel_value, str):
                rel_tokens = rel_value.lower().split()
            else:
                rel_tokens = [str(item).lower() for item in rel_value]
            if "noopener" in rel_tokens:
                continue
            href = self._resource_url(str(tag.get("href") or ""))
            if href:
                links.append(href)
        output: List[str] = []
        for href in links:
            if href not in output:
                output.append(href)
        return output

    def _is_same_host_http_url(self, candidate_url: str) -> bool:
        parsed = urlparse(candidate_url or "")
        if parsed.scheme != "http":
            return False
        own_host = (self.parsed_url.hostname or self.parsed_url.netloc or "").lower()
        candidate_host = (parsed.hostname or parsed.netloc or "").lower()
        return bool(own_host and candidate_host and own_host == candidate_host)

    def _detect_internal_http_navigation(self) -> List[Dict[str, str]]:
        if self.parsed_url.scheme != "https":
            return []
        rows: List[Dict[str, str]] = []
        for tag in self.soup.find_all("a", href=True):
            url = self._resource_url(str(tag.get("href") or ""))
            if self._is_same_host_http_url(url):
                rows.append({"type": "link", "url": url, "text": self._compact_text(tag.get_text(" ", strip=True))})
        for tag in self.soup.find_all("form"):
            url = self._resource_url(str(tag.get("action") or ""))
            if self._is_same_host_http_url(url):
                rows.append({"type": "form", "url": url, "text": self._form_label(tag)})

        deduped: List[Dict[str, str]] = []
        seen = set()
        for row in rows:
            key = (row.get("type", ""), row.get("url", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped

    def _audit_forms(self) -> Dict[str, Any]:
        forms = self.soup.find_all("form")
        if not forms:
            return {"form_count": 0, "forms": [], "issues": []}

        rows: List[Dict[str, Any]] = []
        issues: List[Dict[str, Any]] = []
        has_page_captcha = self._has_captcha_hint(self.soup)

        for index, form in enumerate(forms):
            action_raw = str(form.get("action") or "").strip()
            action_url = self._resource_url(action_raw) if action_raw else self.url
            method = str(form.get("method") or "get").strip().lower()
            inputs = form.find_all(["input", "textarea", "select"])
            input_types = [
                str(tag.get("type") or tag.name or "").strip().lower() or tag.name
                for tag in inputs
            ]
            hidden_names = [
                str(tag.get("name") or tag.get("id") or "").strip().lower()
                for tag in form.find_all("input", type=lambda value: str(value or "").lower() == "hidden")
            ]
            form_text = self._compact_text(form.get_text(" ", strip=True), limit=600)
            sensitive_terms = self._sensitive_terms(form)
            row = {
                "index": index,
                "label": self._form_label(form),
                "method": method,
                "action": action_url,
                "input_count": len(inputs),
                "input_types": sorted(set([value for value in input_types if value]))[:12],
                "has_file_upload": "file" in input_types,
                "has_password": "password" in input_types,
                "has_personal_fields": self._has_personal_field_hint(form),
                "has_sensitive_context": bool(sensitive_terms),
                "sensitive_terms": sensitive_terms[:6],
                "has_search_hint": self._has_search_form_hint(form),
                "has_csrf_hint": any(re.search(r"(csrf|token|nonce|_wpnonce|authenticity)", name, re.I) for name in hidden_names),
                "has_privacy_consent": self._has_privacy_consent_hint(form_text, form),
                "has_captcha_hint": has_page_captcha or self._has_captcha_hint(form),
                "is_external_action": self._is_external_form_action(action_url),
            }
            rows.append(row)

            if action_url.startswith("http://"):
                issues.append(
                    self._issue(
                        "form_action_http",
                        "high" if row["has_password"] or row["has_personal_fields"] else "medium",
                        "フォーム送信先がHTTPです",
                        f"{row['label']} の送信先が `{action_url}` です。",
                        "フォームのactionをHTTPSまたは相対URLへ変更し、送信先の証明書とリダイレクト設定を確認してください。",
                        action_url,
                    )
                )

            if row["is_external_action"] and method == "post":
                issues.append(
                    self._issue(
                        "form_action_external",
                        "high" if row["has_password"] or row["has_sensitive_context"] else "medium",
                        "フォーム送信先が外部ドメインです",
                        f"{row['label']} の送信先が外部URL `{action_url}` です。公開HTML上で確認できる送信先のため、意図したフォームサービスか確認が必要です。",
                        "フォームプラグイン、MA/採用/問い合わせサービス等の送信先が正規のものか、保存先権限・通知先・スパム対策を保守会社に確認してください。",
                        action_url,
                    )
                )

            if row["has_password"] and self.parsed_url.scheme != "https":
                issues.append(
                    self._issue(
                        "password_form_without_https_page",
                        "high",
                        "パスワード入力フォームがHTTPSページ上にありません",
                        f"{row['label']} にpassword入力がありますが、ページURLがHTTPSではありません。",
                        "ログイン/会員フォームはページ表示から送信完了までHTTPSに統一してください。",
                        action_url,
                    )
                )

            if row["has_file_upload"] and method == "post" and not row["has_captcha_hint"]:
                issues.append(
                    self._issue(
                        "file_upload_form_without_captcha_hint",
                        "medium",
                        "ファイルアップロード付きフォームにbot対策の表示が見えません",
                        f"{row['label']} にfile inputがありますが、reCAPTCHA/hCaptcha等の公開HTML上の痕跡を確認できませんでした。",
                        "アップロード容量制限、拡張子制限、ウイルスチェック、bot対策、保存先権限を保守会社に確認してください。",
                        action_url,
                    )
                )

            if (
                method == "post"
                and not row["has_search_hint"]
                and (row["has_personal_fields"] or row["has_sensitive_context"])
                and not (row["has_csrf_hint"] or row["has_captcha_hint"] or row["has_privacy_consent"])
            ):
                labels = []
                if row["has_personal_fields"]:
                    labels.append("個人情報項目")
                if row["has_sensitive_context"]:
                    labels.append(f"センシティブ語: {', '.join(row['sensitive_terms'])}")
                issues.append(
                    self._issue(
                        "personal_form_without_public_protection_hints",
                        "medium",
                        "個人情報フォームの基本対策痕跡が公開HTML上で見えません",
                        f"{row['label']} に {' / '.join(labels)} が見えますが、公開HTML上ではtoken/nonce、captcha、privacy同意の痕跡を確認できませんでした。",
                        "サーバー側対策の有無はHTMLだけでは断定できません。フォームプラグイン、スパム対策、CSRF対策、保存先権限、個人情報同意の設定を保守会社に確認してください。",
                        action_url,
                    )
                )

            if row["has_personal_fields"] and not row["has_privacy_consent"] and not row["has_search_hint"]:
                issues.append(
                    self._issue(
                        "personal_form_without_privacy_consent_hint",
                        "medium",
                        "個人情報フォームに同意表示の痕跡が見えません",
                        f"{row['label']} に氏名・メール等の入力項目がありますが、公開HTML上でプライバシー同意の表示を確認できませんでした。",
                        "個人情報の利用目的、プライバシーポリシーリンク、同意チェックの表示を確認してください。",
                        action_url,
                    )
                )

            if method == "post" and not row["has_csrf_hint"] and not row["has_search_hint"]:
                issues.append(
                    self._issue(
                        "post_form_without_csrf_hint",
                        "low",
                        "POSTフォームにCSRF/nonceの公開HTML上の痕跡が見えません",
                        f"{row['label']} にPOST送信がありますが、hidden token/nonceの痕跡を確認できませんでした。",
                        "サーバー側でCSRF対策が入っているか、フォームプラグイン/独自実装の設定を保守会社に確認してください。",
                        action_url,
                    )
                )

        return {"form_count": len(forms), "forms": rows[:20], "issues": issues}

    @staticmethod
    def _compact_text(value: Any, *, limit: int = 120) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        return text[:limit]

    def _form_label(self, form: Any) -> str:
        attrs = [
            str(form.get("id") or "").strip(),
            str(form.get("name") or "").strip(),
            " ".join(str(item) for item in (form.get("class") or []) if str(item).strip()),
            self._compact_text(form.get_text(" ", strip=True), limit=40),
        ]
        for value in attrs:
            if value:
                return f"フォーム({value[:40]})"
        return "フォーム"

    @staticmethod
    def _has_captcha_hint(node: Any) -> bool:
        haystack = str(node or "").lower()
        return any(marker in haystack for marker in ("recaptcha", "g-recaptcha", "hcaptcha", "turnstile"))

    @staticmethod
    def _has_search_form_hint(form: Any) -> bool:
        haystack = " ".join(
            [
                str(form.get("role") or ""),
                str(form.get("id") or ""),
                str(form.get("name") or ""),
                " ".join(str(item) for item in (form.get("class") or [])),
                str(form.get_text(" ", strip=True) or ""),
            ]
        ).lower()
        input_types = [
            str(tag.get("type") or "").lower()
            for tag in form.find_all("input")
        ]
        return "search" in input_types or any(marker in haystack for marker in ("search", "検索", "サイト内検索"))

    @staticmethod
    def _has_personal_field_hint(form: Any) -> bool:
        joined: List[str] = []
        for tag in form.find_all(["input", "textarea", "select", "label"]):
            joined.extend(
                [
                    tag.name if tag.name == "textarea" else "",
                    str(tag.get("name") or ""),
                    str(tag.get("id") or ""),
                    str(tag.get("placeholder") or ""),
                    str(tag.get("aria-label") or ""),
                    str(tag.get_text(" ", strip=True) or ""),
                ]
            )
        haystack = " ".join(joined).lower()
        return bool(
            re.search(
                r"(email|mail|e-mail|tel|phone|name|company|address|zip|postcode|age|sex|gender|birth|birthday|textarea|氏名|名前|お名前|メール|電話|住所|会社|郵便|年齢|性別|生年月日|相談|問い合わせ|問合せ|お問い合わせ)",
                haystack,
                flags=re.I,
            )
        )

    def _is_external_form_action(self, action_url: str) -> bool:
        parsed = urlparse(action_url or "")
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        own_host = (self.parsed_url.hostname or self.parsed_url.netloc or "").lower()
        action_host = (parsed.hostname or parsed.netloc or "").lower()
        return bool(own_host and action_host and action_host != own_host)

    @staticmethod
    def _sensitive_terms(form: Any) -> List[str]:
        haystack_parts: List[str] = []
        for tag in form.find_all(["input", "textarea", "select", "label"]):
            haystack_parts.extend(
                [
                    str(tag.get("name") or ""),
                    str(tag.get("id") or ""),
                    str(tag.get("placeholder") or ""),
                    str(tag.get("aria-label") or ""),
                    str(tag.get_text(" ", strip=True) or ""),
                ]
            )
        haystack_parts.append(str(form.get_text(" ", strip=True) or ""))
        haystack = " ".join(haystack_parts)
        terms = []
        for term in ("医療", "相談", "症状", "不妊", "妊娠", "治療", "病気", "介護"):
            if term in haystack and term not in terms:
                terms.append(term)
        return terms

    @staticmethod
    def _has_privacy_consent_hint(form_text: str, form: Any) -> bool:
        haystack = f"{form_text} {form}".lower()
        has_privacy_word = bool(re.search(r"(privacy|個人情報|プライバシ|同意|利用目的)", haystack, flags=re.I))
        has_checkbox = bool(form.find("input", type=lambda value: str(value or "").lower() == "checkbox"))
        return has_privacy_word and has_checkbox

    def _detect_library_versions(self, scripts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        findings: List[Dict[str, str]] = []
        patterns = (
            ("jquery", re.compile(r"jquery[/@-](\d+(?:\.\d+){1,3})", re.I)),
            ("jquery-ui", re.compile(r"jquery-ui[/@-](\d+(?:\.\d+){1,3})", re.I)),
            ("bootstrap", re.compile(r"bootstrap(?:\.bundle)?[/@-](\d+(?:\.\d+){1,3})", re.I)),
            ("swiper", re.compile(r"swiper@(\d+(?:\.\d+){0,3})", re.I)),
            ("swiper", re.compile(r"swiper[/@-](\d+(?:\.\d+){1,3})", re.I)),
            ("slick", re.compile(r"(?:slick-carousel|slick)[/@-](\d+(?:\.\d+){1,3})", re.I)),
            ("modernizr", re.compile(r"modernizr[/@-](\d+(?:\.\d+){1,3})", re.I)),
        )
        for row in scripts:
            url = str(row.get("url") or "")
            for library, pattern in patterns:
                match = pattern.search(url)
                if match:
                    findings.append({"library": library, "version": match.group(1), "url": url})
        return findings

    def _detect_jquery_versions_from_asset_content(
        self,
        scripts: List[Dict[str, Any]],
        known_findings: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        known_jquery_urls = {
            str(item.get("url") or "")
            for item in known_findings
            if str(item.get("library") or "").lower() == "jquery" and item.get("version")
        }
        findings: List[Dict[str, str]] = []
        fetched_count = 0
        for row in scripts:
            url = str(row.get("url") or "")
            if not url or url in known_jquery_urls or not self._is_possible_jquery_core_asset(url):
                continue
            if fetched_count >= 3:
                break
            fetched_count += 1
            try:
                response = safe_fetch_url(
                    url,
                    timeout=4.0,
                    max_bytes=JQUERY_ASSET_VERSION_MAX_BYTES,
                    max_redirects=2,
                )
            except Exception:
                continue
            if int(getattr(response, "status_code", 0) or 0) != 200:
                continue
            version = self._extract_jquery_core_version(str(getattr(response, "text", "") or ""))
            if not version:
                continue
            findings.append(
                {
                    "library": "jquery",
                    "version": version,
                    "url": url,
                    "source": "asset_header",
                }
            )
        return findings

    @staticmethod
    def _is_possible_jquery_core_asset(url: str) -> bool:
        path = urlparse(url or "").path.lower()
        filename = path.rsplit("/", 1)[-1]
        if not filename.endswith(".js") or "jquery" not in filename:
            return False
        if any(marker in filename for marker in ("jquery-ui", "jqueryauto", "jquery.auto", "validate", "migrate", "plugin")):
            return False
        return filename in {"jquery.js", "jquery.min.js"} or bool(
            re.match(r"jquery[.-](?:\d|min|latest)", filename)
        )

    @staticmethod
    def _extract_jquery_core_version(text: str) -> str:
        head = (text or "")[:8192]
        if "jquery" not in head.lower():
            return ""
        patterns = (
            re.compile(r"jQuery JavaScript Library v(\d+(?:\.\d+){1,3})", re.I),
            re.compile(r"jQuery v(\d+(?:\.\d+){1,3})", re.I),
        )
        for pattern in patterns:
            match = pattern.search(head)
            if match:
                return match.group(1)
        return ""

    def _detect_outdated_frontend_assets(
        self,
        scripts: List[Dict[str, Any]],
        stylesheets: List[Dict[str, Any]],
        library_findings: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        medium_libraries = {"jquery-ui", "bootstrap", "modernizr"}
        low_libraries = {"swiper", "slick"}
        for finding in library_findings:
            library = str(finding.get("library") or "").strip().lower()
            if library == "jquery":
                continue
            if library not in medium_libraries | low_libraries:
                continue
            rows.append(
                {
                    "library": library,
                    "label": library,
                    "version": str(finding.get("version") or ""),
                    "url": str(finding.get("url") or ""),
                    "severity": "medium" if library in medium_libraries else "low",
                    "reason": "URL上のバージョン露出・テーマ/プラグイン由来資産の棚卸し候補",
                }
            )

        for row in [*scripts, *stylesheets]:
            url = str(row.get("url") or "")
            lowered = url.lower()
            if not url:
                continue
            if "bootstrap" in lowered and not any(item.get("url") == url and item.get("library") == "bootstrap" for item in rows):
                rows.append({"library": "bootstrap", "label": "bootstrap", "version": "", "url": url, "severity": "medium", "reason": "URL名から検出"})
            if "slick" in lowered and not any(item.get("url") == url and item.get("library") == "slick" for item in rows):
                rows.append({"library": "slick", "label": "slick", "version": "", "url": url, "severity": "low", "reason": "URL名から検出"})
            if "jquery-ui" in lowered and not any(item.get("url") == url and item.get("library") == "jquery-ui" for item in rows):
                rows.append({"library": "jquery-ui", "label": "jquery-ui", "version": "", "url": url, "severity": "medium", "reason": "URL名から検出"})
            if "modernizr" in lowered and not any(item.get("url") == url and item.get("library") == "modernizr" for item in rows):
                rows.append({"library": "modernizr", "label": "modernizr", "version": "", "url": url, "severity": "medium", "reason": "URL名から検出"})

        deduped: List[Dict[str, str]] = []
        seen = set()
        for row in rows:
            key = (row.get("library", ""), row.get("url", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped

    @staticmethod
    def _detect_old_polyfills(scripts: List[Dict[str, Any]]) -> List[str]:
        names: List[str] = []
        for row in scripts:
            url = str(row.get("url") or "").lower()
            if "html5shiv" in url and "html5shiv" not in names:
                names.append("html5shiv")
            if re.search(r"/respond(?:\.min)?\.js(?:[?#]|$)", url) and "respond.js" not in names:
                names.append("respond.js")
        return names

    def _has_wordpress_hint(self) -> bool:
        generator = (self._extract_generator_meta() or "").lower()
        if "wordpress" in generator:
            return True
        link_header = ""
        for key, value in self.headers.items():
            if str(key).lower() == "link":
                link_header = str(value)
                break
        haystack = f"{link_header}\n{self.html or ''}".lower()
        return "api.w.org" in haystack or "/wp-json/" in haystack or "/wp-content/" in haystack

    def _check_wordpress_rest_users(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        if not self._has_wordpress_hint():
            return None, {}
        root = f"{self.parsed_url.scheme or 'https'}://{self.parsed_url.netloc}"
        endpoint = urljoin(root.rstrip("/") + "/", "wp-json/wp/v2/users")
        signal: Dict[str, Any] = {"checked": endpoint, "status_code": None}
        try:
            response = safe_fetch_url(
                endpoint,
                timeout=4.0,
                max_bytes=256 * 1024,
                max_redirects=2,
            )
            signal["status_code"] = int(getattr(response, "status_code", 0) or 0)
            if signal["status_code"] != 200:
                return None, signal
            payload = json.loads(response.text or "[]")
            if not isinstance(payload, list) or not payload:
                return None, signal
            users = []
            for item in payload[:5]:
                if not isinstance(item, dict):
                    continue
                slug = str(item.get("slug") or "").strip()
                name = str(item.get("name") or "").strip()
                if slug or name:
                    users.append({"slug": slug, "name": name})
            signal["public_users"] = users
            if not users:
                return None, signal
            has_admin = any((item.get("slug") or "").lower() == "admin" or (item.get("name") or "").lower() == "admin" for item in users)
            title = "WordPress REST APIでユーザー情報が見えます"
            detail = f"`{endpoint}` で公開ユーザー {len(users)} 件を確認しました。"
            if has_admin:
                detail += " `admin` も含まれています。"
            return (
                self._issue(
                    "wordpress_rest_users_public",
                    "high" if has_admin else "medium",
                    title,
                    detail,
                    "REST APIの users endpoint を未認証では返さない設定にし、管理者ログインIDが推測されない状態にしてください。",
                    endpoint,
                ),
                signal,
            )
        except Exception as exc:
            signal["error"] = str(exc)[:160]
            return None, signal

    def _check_sitemap_freshness(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        sitemap_info = self.sitemap_info if isinstance(self.sitemap_info, dict) else {}
        if not sitemap_info:
            return None, {}
        if str(sitemap_info.get("error") or "").strip():
            return None, {}
        signal: Dict[str, Any] = {
            "total_urls": sitemap_info.get("total_urls"),
            "parsed_sitemaps": sitemap_info.get("parsed_sitemaps"),
            "update_frequency": sitemap_info.get("update_frequency"),
            "generator_hint": sitemap_info.get("generator_hint"),
        }
        lastmods = [str(item).strip() for item in sitemap_info.get("lastmod_dates") or [] if str(item).strip()]
        signal["lastmod_dates"] = lastmods[:5]
        newest = self._newest_lastmod(lastmods)
        if not newest:
            return None, signal
        age_days = (datetime.now(timezone.utc).date() - newest.date()).days
        signal["newest_lastmod"] = newest.date().isoformat()
        signal["newest_lastmod_age_days"] = age_days
        generator_hint = str(sitemap_info.get("generator_hint") or "").strip()
        if age_days < 365 and "xml-sitemaps.com" not in generator_hint.lower():
            return None, signal
        severity = "medium" if age_days >= 365 else "low"
        detail = f"sitemap の最新 lastmod が {age_days} 日前です。"
        if generator_hint:
            detail += f" generator: {generator_hint}."
        return (
            self._issue(
                "stale_or_static_sitemap",
                severity,
                "sitemapが古い、または静的生成のまま残っています",
                detail,
                "CMS/SEOプラグインの自動sitemapに一本化し、Search Consoleへ再送信してください。",
                ", ".join(lastmods[:3]),
            ),
            signal,
        )

    def _check_update_signal_consistency(
        self,
        *,
        sitemap_signal: Dict[str, Any],
        visible_signal: Dict[str, Any],
        sitemap_unavailable: bool,
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        if sitemap_unavailable:
            return None, {}
        if not sitemap_signal or not visible_signal:
            return None, {}
        sitemap_age = sitemap_signal.get("newest_lastmod_age_days")
        visible_age = visible_signal.get("newest_visible_age_days")
        try:
            sitemap_age_int = int(sitemap_age)
            visible_age_int = int(visible_age)
        except (TypeError, ValueError):
            return None, {}
        if sitemap_age_int < 365:
            return None, {}

        sitemap_date = str(sitemap_signal.get("newest_lastmod") or (sitemap_signal.get("lastmod_dates") or [""])[0]).strip()
        visible_date = str(visible_signal.get("newest_visible_date") or "").strip()
        diff_days = abs(sitemap_age_int - visible_age_int)
        status_label = "更新停滞" if visible_age_int >= 365 else "要確認"
        signal = {
            "status": status_label,
            "visible_date": visible_date,
            "visible_age_days": visible_age_int,
            "sitemap_lastmod": sitemap_date,
            "sitemap_age_days": sitemap_age_int,
            "age_gap_days": diff_days,
        }
        if visible_age_int < 365:
            detail = "サイト上では新しい日付が見えますが、検索エンジンやAIクローラー向けの更新通知である sitemap lastmod が古い可能性があります。"
            severity = "medium"
        else:
            detail = "サイト上で見える最新日付と sitemap lastmod の両方が古い可能性があります。更新停滞サインとして保守会社に確認してください。"
            severity = "medium"
        if visible_date or sitemap_date:
            detail += f" visible={visible_date or '-'} / sitemap_lastmod={sitemap_date or '-'} / 差分={diff_days}日。"
        issue = self._issue(
            "update_signal_mismatch",
            severity,
            f"更新整合性チェック: {status_label}",
            detail,
            "お知らせ等の見える更新日、CMS/SEOプラグインのsitemap生成、Search Console登録URLが同じ更新状態になるよう確認してください。",
            f"visible={visible_date or '-'}; sitemap_lastmod={sitemap_date or '-'}; age_gap_days={diff_days}",
        )
        issue["evidence_details"] = signal
        return issue, signal

    def _check_sitemap_availability(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        sitemap_info = self.sitemap_info if isinstance(self.sitemap_info, dict) else {}
        if not sitemap_info:
            return None, {}
        error_text = str(sitemap_info.get("error") or "").strip()
        warning_text = str(sitemap_info.get("warning") or "").strip()
        signal = {
            "error": error_text,
            "warning": warning_text,
            "source_sitemaps": (sitemap_info.get("source_sitemaps") or [])[:5],
            "parsed_sitemaps": sitemap_info.get("parsed_sitemaps"),
        }
        if not error_text:
            return None, signal if warning_text else {}
        severity = "medium" if re.search(r"(404|見つかりません|not found|有効な子sitemap|解析できません)", error_text, re.I) else "low"
        return (
            self._issue(
                "sitemap_unavailable_or_invalid",
                severity,
                "sitemap.xmlを正常に解析できません",
                error_text,
                "robots.txt内のSitemap指定、CMS/SEOプラグインのsitemap出力、Search Console登録URLを確認してください。",
                "/sitemap.xml",
            ),
            signal,
        )

    def _check_visible_update_freshness(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        candidates = self._extract_visible_dates()
        if not candidates:
            return None, {}
        newest = max(item["date"] for item in candidates)
        age_days = (datetime.now(timezone.utc).date() - newest.date()).days
        signal = {
            "newest_visible_date": newest.date().isoformat(),
            "newest_visible_age_days": age_days,
            "candidate_count": len(candidates),
            "sample_dates": [item["raw"] for item in candidates[:6]],
        }
        if age_days < 365:
            return None, signal
        severity = "high" if age_days >= 1095 else ("medium" if age_days >= 730 else "low")
        return (
            self._issue(
                "visible_update_date_old",
                severity,
                "ページ上の見える更新日が古い可能性があります",
                f"公開HTML上で確認できる最新日付が {newest.date().isoformat()}（{age_days}日前）です。",
                "お知らせ、事例、採用、会社情報などの更新日を確認し、古い情報が残っている場合は更新または非表示化してください。可能ならJSON-LD/metaにも更新日を明示してください。",
                newest.date().isoformat(),
            ),
            signal,
        )

    def _extract_visible_dates(self) -> List[Dict[str, Any]]:
        text = self.soup.get_text(" ", strip=True)
        patterns = (
            re.compile(r"(?<!\d)(20\d{2})[./-](0?[1-9]|1[0-2])[./-](0?[1-9]|[12]\d|3[01])(?!\d)"),
            re.compile(r"(?<!\d)(20\d{2})年\s*(0?[1-9]|1[0-2])月\s*(0?[1-9]|[12]\d|3[01])日"),
        )
        rows: List[Dict[str, Any]] = []
        seen = set()
        now = datetime.now(timezone.utc).date()
        for pattern in patterns:
            for match in pattern.finditer(text):
                year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
                try:
                    parsed = datetime(year, month, day, tzinfo=timezone.utc)
                except ValueError:
                    continue
                # Ignore likely typo/future campaign dates far beyond the analysis date.
                if (parsed.date() - now).days > 30:
                    continue
                key = parsed.date().isoformat()
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"date": parsed, "raw": match.group(0)})
        rows.sort(key=lambda item: item["date"], reverse=True)
        return rows

    @staticmethod
    def _newest_lastmod(lastmods: List[str]) -> Optional[datetime]:
        dates: List[datetime] = []
        for raw in lastmods:
            normalized = raw.replace("Z", "+00:00")
            parsed: Optional[datetime] = None
            for candidate in (normalized, normalized[:10]):
                try:
                    parsed = datetime.fromisoformat(candidate)
                    break
                except Exception:
                    parsed = None
            if parsed is None:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            dates.append(parsed.astimezone(timezone.utc))
        return max(dates) if dates else None

    @staticmethod
    def _issue(
        issue_id: str,
        severity: str,
        title: str,
        detail: str,
        recommendation: str,
        evidence: str,
    ) -> Dict[str, Any]:
        return {
            "id": issue_id,
            "severity": severity,
            "issue": title,
            "title": title,
            "detail": detail,
            "recommendation": recommendation,
            "evidence": evidence,
        }


RISK_EXPLANATIONS = {
    "no_https": {
        "simple": "通信が暗号化されていないため、入力情報が盗み見られる可能性があります",
        "detail": "HTTPSに対応していない場合、ユーザーが入力したパスワードやクレジットカード情報が、第三者に傍受される可能性があります。また、Googleはランキング要因としてHTTPSを考慮しています。",
        "for_engineer": "TLS/SSL証明書が未設定。Let's Encrypt等で無料取得可能。Apache/nginxの設定変更が必要。"
    },
    "mixed_content": {
        "simple": "一部の画像等が暗号化されていない通信で読み込まれています",
        "detail": "HTTPSページ内でHTTPのリソース（画像、スクリプト等）を読み込むと、ブラウザが警告を表示したり、リソースがブロックされることがあります。",
        "for_engineer": "http://で読み込まれているリソースをhttps://に変更、または相対パスに修正。"
    },
    "missing_csp": {
        "simple": "不正なスクリプトが実行されるリスクがあります",
        "detail": "Content-Security-Policy（CSP）ヘッダーが未設定の場合、クロスサイトスクリプティング（XSS）攻撃のリスクが高まります。",
        "for_engineer": "CSPヘッダーを設定。例: Content-Security-Policy: default-src 'self'"
    },
    "missing_xframe": {
        "simple": "悪意あるサイトに埋め込まれるリスクがあります",
        "detail": "X-Frame-Optionsヘッダーが未設定の場合、クリックジャッキング攻撃（透明なiframeで騙す攻撃）を受ける可能性があります。",
        "for_engineer": "X-Frame-Options: DENY または SAMEORIGIN を設定"
    }
}


def get_risk_explanation(risk_type: str, mode: str = "simple") -> str:
    """リスク説明を取得"""
    if risk_type not in RISK_EXPLANATIONS:
        return ""

    return RISK_EXPLANATIONS[risk_type].get(mode, RISK_EXPLANATIONS[risk_type]["simple"])


def format_security_result(result: Dict, mode: str = "simple") -> Dict:
    """チェック結果のフォーマット"""
    from core.ui.design_system import LEGAL_ICONS_FALLBACK

    score = result["score"]
    if score >= 70:
        status = "良好"
        status_color = "success"
    elif score >= 40:
        status = "要改善"
        status_color = "warning"
    else:
        status = "要対応"
        status_color = "danger"

    items = []

    https_check = result["https"]
    https_subtext = ""
    if https_check["status"] != "ok":
        risk = https_check.get("risk", "通信内容が漏えいする可能性があります")
        recommendation = https_check.get("recommendation", "HTTPSを有効化してください")
        https_subtext = f"リスク: {risk} / 対処: {recommendation}"
    items.append({
        "icon": LEGAL_ICONS_FALLBACK["compliant"] if https_check["status"] == "ok" else LEGAL_ICONS_FALLBACK["error"],
        "text": f"通信の暗号化(HTTPS): {https_check['value']}",
        "subtext": https_subtext
    })

    mixed = result["mixed_content"]
    if mixed["status"] != "skip":
        if mixed["status"] == "ok":
            items.append({
                "icon": LEGAL_ICONS_FALLBACK["compliant"],
                "text": "暗号化されていない要素: なし",
                "subtext": ""
            })
        else:
            items.append({
                "icon": LEGAL_ICONS_FALLBACK["warning"],
                "text": f"暗号化されていない要素: {mixed['count']}件検出",
                "subtext": "リスク: ブラウザ警告や改ざんの可能性 / 対処: HTTPリソースをHTTPSに置換"
            })

    headers = result["headers"]
    for header in headers["headers"]:
        if header["importance"] in ["high", "medium"]:
            if header["status"] == "ok":
                items.append({
                    "icon": LEGAL_ICONS_FALLBACK["compliant"],
                    "text": f"{header['name_simple']}: 設定済み",
                    "subtext": ""
                })
            else:
                risk = header.get("risk", "攻撃リスクが高まります")
                recommendation = header.get("recommendation", "推奨ヘッダー値を設定してください")
                items.append({
                    "icon": LEGAL_ICONS_FALLBACK["warning"],
                    "text": f"{header['name_simple']}: 未設定",
                    "subtext": f"リスク: {risk} / 対処: {recommendation}"
                })

    public_risks = result.get("public_technology_risks") or {}
    public_issues = public_risks.get("issues") or []
    for issue in public_issues[:6]:
        severity = issue.get("severity", "medium")
        icon = LEGAL_ICONS_FALLBACK["error"] if severity == "high" else LEGAL_ICONS_FALLBACK["warning"]
        recommendation = issue.get("recommendation", "")
        subtext_parts = [issue.get("detail", "")]
        if recommendation:
            subtext_parts.append(f"対処: {recommendation}")
        items.append({
            "icon": icon,
            "text": issue.get("title") or issue.get("issue") or "公開技術リスク",
            "subtext": " / ".join([str(part).strip() for part in subtext_parts if str(part).strip()]),
        })

    faq = [
        {
            "question": "HTTPSは必須ですか？",
            "answer": "はい。ユーザーの安全のため、また検索順位への影響もあるため、全てのサイトでHTTPS化を推奨します。Let's Encryptで無料で取得できます。"
        },
        {
            "question": "セキュリティヘッダーは必須ですか？",
            "answer": "必須ではありませんが、設定することで攻撃リスクを軽減できます。特に個人情報を扱うサイトでは設定を推奨します。"
        },
        {
            "question": "クリックジャッキングとは？",
            "answer": "見えないボタンを重ねて意図しないクリックを誘導する攻撃です。X-Frame-Options（DENY/SAMEORIGIN）で防ぎます。"
        },
        {
            "question": "MIMEスニッフィングとは？",
            "answer": "ブラウザがファイル種別を推測して想定外に実行するリスクです。X-Content-Type-Options: nosniff を設定します。"
        },
        {
            "question": "中間者攻撃とは？",
            "answer": "通信経路で第三者に盗み見・改ざんされる攻撃です。HTTPS化とHSTS設定で対策します。"
        }
    ]

    return {
        "title": "セキュリティ基本設定チェック",
        "subtitle": "通信の安全性と基本的な保護設定を確認",
        "status": status,
        "status_color": status_color,
        "score": score,
        "items": items,
        "issues": public_issues,
        "disclaimer": "※詳細な脆弱性診断は専門サービスをご利用ください",
        "faq": faq if mode == "simple" else []
    }


SECURITY_IMPROVEMENT_GUIDES = {
    "wordpress": {
        "https": "Really Simple SSLプラグインで簡単にHTTPS化できます。または、サーバー側で証明書を設定し、.htaccessでリダイレクト設定。",
        "headers": "HTTP Headers プラグイン、または Security Headers プラグインを使用。functions.phpでの手動設定も可能。"
    },
    "shopify": {
        "https": "Shopifyでは全ストアで自動的にHTTPSが有効化されています。",
        "headers": "Shopifyの管理画面からは設定不可。Shopify Plusでは一部カスタマイズ可能。"
    },
    "wix": {
        "https": "Wixでは自動的にHTTPSが有効化されています。",
        "headers": "Wixでは直接設定できません。"
    },
    "squarespace": {
        "https": "Squarespaceでは自動的にHTTPSが有効化されています。",
        "headers": "Code Injectionで一部設定可能。"
    }
}


def get_improvement_guide(platform: str, check_type: str) -> str:
    """プラットフォーム別の改善ガイドを取得"""
    if platform not in SECURITY_IMPROVEMENT_GUIDES:
        return "ウェブサーバーの設定ファイル（Apache: .htaccess, nginx: nginx.conf）で設定してください。"

    return SECURITY_IMPROVEMENT_GUIDES[platform].get(check_type, "")
