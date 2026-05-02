# -*- coding: utf-8 -*-
"""OGP/SNS最適化チェッカー"""

from typing import Dict, Optional
from bs4 import BeautifulSoup


# OGPタグ定義
OGP_TAGS = {
    "og:title": {
        "name_simple": "シェア時のタイトル",
        "required": True,
        "max_length": 60,
        "min_length": 10,
        "fallback": "title",
        "description": "SNSでシェアされた時に表示されるタイトル"
    },
    "og:description": {
        "name_simple": "シェア時の説明文",
        "required": True,
        "max_length": 200,
        "min_length": 50,
        "best_min_length": 80,
        "best_max_length": 120,
        "fallback": "meta_description",
        "description": "SNSでシェアされた時に表示される説明文"
    },
    "og:image": {
        "name_simple": "シェア時の画像",
        "required": True,
        "recommended_size": {"width": 1200, "height": 630},
        "min_size": {"width": 600, "height": 315},
        "description": "SNSでシェアされた時に表示されるサムネイル画像"
    },
    "og:url": {
        "name_simple": "シェアされるURL",
        "required": True,
        "description": "正規URLを指定（canonical相当）"
    },
    "og:type": {
        "name_simple": "ページの種類",
        "required": False,
        "values": ["website", "article", "product", "profile"],
        "default": "website",
        "description": "ページの種類（通常はwebsiteまたはarticle）"
    },
    "og:site_name": {
        "name_simple": "サイト名",
        "required": False,
        "description": "ウェブサイトの名前"
    },
    "og:locale": {
        "name_simple": "言語設定",
        "required": False,
        "default": "ja_JP",
        "description": "コンテンツの言語"
    }
}

# Twitter Card定義
TWITTER_TAGS = {
    "twitter:card": {
        "name_simple": "X(Twitter)での表示形式",
        "required": True,
        "values": ["summary", "summary_large_image", "player", "app"],
        "recommended": "summary_large_image",
        "description": "Xでの表示サイズ（summary_large_imageで大きい画像表示）"
    },
    "twitter:title": {
        "name_simple": "X用タイトル",
        "required": False,
        "fallback": "og:title",
        "description": "og:titleと異なる場合のみ設定"
    },
    "twitter:description": {
        "name_simple": "X用説明文",
        "required": False,
        "fallback": "og:description",
        "description": "og:descriptionと異なる場合のみ設定"
    },
    "twitter:image": {
        "name_simple": "X用画像",
        "required": False,
        "fallback": "og:image",
        "description": "og:imageと異なる場合のみ設定"
    },
    "twitter:site": {
        "name_simple": "X公式アカウント",
        "required": False,
        "description": "@ユーザー名形式で指定"
    }
}


class OGPChecker:
    """OGP/SNS最適化チェッカー"""

    def __init__(self, html: str, url: str):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')
        self.url = url

    def check_ogp(self) -> Dict:
        """OGPタグをチェック"""
        results = []

        for tag_name, config in OGP_TAGS.items():
            meta = self.soup.find('meta', property=tag_name)
            content = meta.get('content', '').strip() if meta else None

            status = "not_found"
            issues = []
            value = content

            if content:
                status = "found"

                if "max_length" in config and len(content) > config["max_length"]:
                    issues.append(f"{config['max_length']}文字を超えています（現在{len(content)}文字）")
                if "min_length" in config and len(content) < config["min_length"]:
                    issues.append(f"{config['min_length']}文字以上を推奨（現在{len(content)}文字）")
                if "best_min_length" in config and "best_max_length" in config:
                    best_min = config["best_min_length"]
                    best_max = config["best_max_length"]
                    if best_min <= len(content) <= best_max:
                        pass
                    elif config.get("min_length", 0) <= len(content) <= config.get("max_length", len(content)):
                        issues.append(f"推奨範囲は{best_min}-{best_max}文字です（現在{len(content)}文字）")

                if issues:
                    status = "warning"

            elif config.get("fallback"):
                fallback_value = self._get_fallback(config["fallback"])
                if fallback_value:
                    status = "fallback"
                    value = f"（{config['fallback']}から取得: {fallback_value[:50]}...）"

            results.append({
                "tag": tag_name,
                "name_simple": config["name_simple"],
                "required": config["required"],
                "status": status,
                "value": value,
                "issues": issues,
                "description": config["description"]
            })

        return {
            "tags": results,
            "found_count": len([r for r in results if r["status"] in ["found", "warning"]]),
            "required_count": len([r for r in results if r["required"]]),
            "required_found": len([r for r in results if r["required"] and r["status"] in ["found", "warning", "fallback"]])
        }

    def check_twitter_card(self) -> Dict:
        """Twitter Cardをチェック"""
        results = []

        for tag_name, config in TWITTER_TAGS.items():
            meta = self.soup.find('meta', attrs={'name': tag_name})
            content = meta.get('content', '').strip() if meta else None

            status = "not_found"
            value = content

            if content:
                status = "found"
            elif config.get("fallback"):
                og_meta = self.soup.find('meta', property=config["fallback"])
                if og_meta:
                    status = "fallback"
                    value = f"（{config['fallback']}から取得）"

            results.append({
                "tag": tag_name,
                "name_simple": config["name_simple"],
                "required": config["required"],
                "status": status,
                "value": value,
                "description": config["description"]
            })

        return {
            "tags": results,
            "found_count": len([r for r in results if r["status"] in ["found", "fallback"]])
        }

    def _get_fallback(self, fallback_type: str) -> Optional[str]:
        """フォールバック値を取得"""
        if fallback_type == "title":
            title = self.soup.find('title')
            return title.get_text().strip() if title else None
        if fallback_type == "meta_description":
            meta = self.soup.find('meta', attrs={'name': 'description'})
            return meta.get('content', '').strip() if meta else None
        return None

    def generate_preview(self) -> Dict:
        """SNSシェア時のプレビューデータ生成"""
        ogp = self.check_ogp()

        def get_value(tag_name: str) -> Optional[str]:
            for tag in ogp["tags"]:
                if tag["tag"] == tag_name and tag["value"]:
                    return tag["value"]
            return None

        return {
            "title": get_value("og:title") or self._get_fallback("title") or "（タイトル未設定）",
            "description": get_value("og:description") or self._get_fallback("meta_description") or "（説明文未設定）",
            "image": get_value("og:image"),
            "url": get_value("og:url") or self.url,
            "site_name": get_value("og:site_name")
        }

    def run_all_checks(self) -> Dict:
        """全チェック実行"""
        ogp = self.check_ogp()
        twitter = self.check_twitter_card()
        preview = self.generate_preview()

        issues = []
        recommendations = []

        missing_required = [t for t in ogp["tags"] if t["required"] and t["status"] == "not_found"]
        for tag in missing_required:
            issues.append({
                "severity": "high",
                "issue": f"{tag['name_simple']}が未設定",
                "suggestion": f"{tag['description']}"
            })

        og_image = next((t for t in ogp["tags"] if t["tag"] == "og:image"), None)
        if og_image and og_image["status"] == "not_found":
            recommendations.append("SNSでシェアされた時に画像が表示されません。1200x630ピクセルの画像を設定することを強く推奨します。")

        twitter_card = next((t for t in twitter["tags"] if t["tag"] == "twitter:card"), None)
        if twitter_card and twitter_card["status"] == "not_found":
            recommendations.append("twitter:cardを設定すると、X(Twitter)での表示が改善されます。summary_large_imageを推奨します。")

        score = 0
        if ogp["required_found"] == ogp["required_count"]:
            score += 60
        else:
            score += int(60 * ogp["required_found"] / max(ogp["required_count"], 1))

        if twitter["found_count"] >= 1:
            score += 20
        if og_image and og_image["status"] == "found":
            score += 20

        return {
            "ogp": ogp,
            "twitter": twitter,
            "preview": preview,
            "issues": issues,
            "recommendations": recommendations,
            "score": min(score, 100)
        }


# ============================================================
# プラットフォーム別最適化提案
# ============================================================

PLATFORM_REQUIREMENTS = {
    "facebook": {
        "name": "Facebook",
        "image_min": {"width": 600, "height": 315},
        "image_recommended": {"width": 1200, "height": 630},
        "title_max": 60,
        "description_max": 200,
        "notes": "正方形画像より横長画像を推奨"
    },
    "twitter": {
        "name": "X (Twitter)",
        "summary_image": {"width": 144, "height": 144, "min": True},
        "summary_large_image": {"width": 300, "height": 157, "min": True},
        "image_recommended": {"width": 1200, "height": 630},
        "title_max": 70,
        "description_max": 200,
        "notes": "summary_large_imageで大きく表示"
    },
    "line": {
        "name": "LINE",
        "image_recommended": {"width": 1200, "height": 630},
        "title_max": 100,
        "notes": "OGPに準拠"
    },
    "linkedin": {
        "name": "LinkedIn",
        "image_recommended": {"width": 1200, "height": 627},
        "notes": "ビジネス向けSNS"
    }
}


def get_platform_specific_suggestions(ogp_data: Dict) -> Dict:
    """プラットフォーム別の最適化提案"""
    suggestions = {}

    for platform, config in PLATFORM_REQUIREMENTS.items():
        platform_suggestions = []

        og_image = next((t for t in ogp_data.get("tags", []) if t["tag"] == "og:image"), None)
        if not og_image or og_image["status"] == "not_found":
            rec = config.get("image_recommended", {})
            platform_suggestions.append(
                f"画像を設定してください（推奨サイズ: {rec.get('width', 1200)}x{rec.get('height', 630)}px）"
            )

        og_title = next((t for t in ogp_data.get("tags", []) if t["tag"] == "og:title"), None)
        if og_title and og_title.get("value"):
            title_len = len(og_title["value"])
            max_len = config.get("title_max", 60)
            if title_len > max_len:
                platform_suggestions.append(
                    f"タイトルが長すぎる可能性（{title_len}文字 > {max_len}文字）"
                )

        suggestions[platform] = {
            "name": config["name"],
            "suggestions": platform_suggestions,
            "notes": config.get("notes", "")
        }

    return suggestions


# ============================================================
# 結果フォーマット
# ============================================================

def format_ogp_result(result: Dict, mode: str = "simple") -> Dict:
    """チェック結果のフォーマット"""
    from core.ui.design_system import LEGAL_ICONS_FALLBACK

    score = result["score"]
    if score >= 80:
        status = "良好"
        status_color = "success"
    elif score >= 50:
        status = "一部未設定"
        status_color = "warning"
    else:
        status = "要設定"
        status_color = "danger"

    items = []

    for tag in result["ogp"]["tags"]:
        if tag["status"] == "found":
            icon = LEGAL_ICONS_FALLBACK["compliant"]
            text = f"{tag['name_simple']}: 設定済み"
            if tag["value"]:
                text += f"（{tag['value'][:30]}...）" if len(str(tag['value'])) > 30 else f"（{tag['value']}）"
        elif tag["status"] == "warning":
            icon = LEGAL_ICONS_FALLBACK["warning"]
            text = f"{tag['name_simple']}: {', '.join(tag['issues'])}"
        elif tag["status"] == "fallback":
            icon = LEGAL_ICONS_FALLBACK["partial"]
            text = f"{tag['name_simple']}: フォールバックあり"
        else:
            icon = LEGAL_ICONS_FALLBACK["error"] if tag["required"] else LEGAL_ICONS_FALLBACK["info"]
            text = f"{tag['name_simple']}: 未設定"
            if tag["required"]:
                text += "（設定推奨）"

        items.append({
            "icon": icon,
            "text": text,
            "required": tag["required"]
        })

    twitter_card = next((t for t in result["twitter"]["tags"] if t["tag"] == "twitter:card"), None)
    if twitter_card:
        if twitter_card["status"] == "found":
            items.append({
                "icon": LEGAL_ICONS_FALLBACK["compliant"],
                "text": f"X(Twitter)表示設定: {twitter_card['value']}",
                "required": True
            })
        else:
            items.append({
                "icon": LEGAL_ICONS_FALLBACK["warning"],
                "text": "X(Twitter)表示設定: 未設定（summary_large_image推奨）",
                "required": True
            })

    faq = [
        {
            "question": "OGPとは何ですか？",
            "answer": "Open Graph Protocolの略で、FacebookやXでURLをシェアした時に表示されるタイトル・説明文・画像を設定する仕組みです。"
        },
        {
            "question": "og:imageのサイズは？",
            "answer": "1200x630ピクセルが推奨です。この比率（約1.91:1）であれば、ほとんどのSNSで綺麗に表示されます。"
        }
    ]

    return {
        "title": "SNSシェア設定チェック",
        "subtitle": "Facebook・X・LINEでシェアされた時の見え方を確認",
        "status": status,
        "status_color": status_color,
        "score": score,
        "preview": result["preview"],
        "items": items,
        "recommendations": result["recommendations"],
        "faq": faq if mode == "simple" else []
    }


# ============================================================
# テンプレート生成
# ============================================================

def generate_ogp_template(page_data: Dict, business_type: str = None) -> str:
    """OGPタグのテンプレートを生成"""
    title = page_data.get("title", "ページタイトル")
    description = page_data.get("description", "ページの説明文（80-120文字程度）")
    url = page_data.get("url", "https://example.com/page")
    image = page_data.get("image", "https://example.com/ogp-image.jpg")
    site_name = page_data.get("site_name", "サイト名")

    og_type = "article" if business_type in ["affiliate_media", "corporate"] else "website"

    template = f'''<!-- OGP (SNSシェア設定) -->
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{site_name}">
<meta property="og:locale" content="ja_JP">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image}">
'''

    return template
