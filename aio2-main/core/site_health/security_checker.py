# -*- coding: utf-8 -*-
"""セキュリティ基本チェッカー（パッシブチェックのみ）"""

from typing import Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse


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
        "risk": "プライバシー侵害",
        "description": "カメラ・マイク等の機能使用を制限",
        "recommendation": "不要な機能を無効化"
    }
}


class SecurityChecker:
    """セキュリティ基本チェッカー"""

    def __init__(self, url: str, headers: Dict, html: str):
        self.url = url
        self.headers = headers or {}
        self.html = html
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

    def run_all_checks(self) -> Dict:
        """全チェック実行"""
        https_check = self.check_https()
        headers_check = self.check_security_headers()
        mixed_content = self.check_mixed_content()
        form_security = self.check_form_security()

        score = 0
        if https_check["status"] == "ok":
            score += 30

        header_score = headers_check["found_count"] / len(SECURITY_HEADERS) * 40
        score += int(header_score)

        if mixed_content["status"] == "ok":
            score += 15

        if form_security["status"] == "ok":
            score += 15

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
            "score": score,
            "risk_level": risk_level
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
