# -*- coding: utf-8 -*-
"""アクセシビリティ簡易チェッカー（WCAG 2.1 基本項目）"""

from typing import Dict
from bs4 import BeautifulSoup
import re


WCAG_CRITERIA = {
    "1.1.1": {
        "name": "非テキストコンテンツ",
        "level": "A",
        "check": "images_alt",
        "description": "画像に代替テキスト（alt属性）を設定"
    },
    "1.3.1": {
        "name": "情報及び関係性",
        "level": "A",
        "check": "heading_hierarchy",
        "description": "見出しの階層構造が正しい"
    },
    "2.4.4": {
        "name": "リンクの目的",
        "level": "A",
        "check": "link_text",
        "description": "リンクテキストが分かりやすい"
    },
    "3.3.2": {
        "name": "ラベル又は説明",
        "level": "A",
        "check": "form_labels",
        "description": "フォーム要素にラベルが設定されている"
    },
    "1.4.3": {
        "name": "コントラスト（最低限）",
        "level": "AA",
        "check": "color_contrast",
        "description": "テキストと背景のコントラスト比が十分"
    }
}


class AccessibilityChecker:
    """アクセシビリティチェッカー"""

    def __init__(self, html: str):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')

    def check_images_alt(self) -> Dict:
        """画像のalt属性チェック"""
        images = self.soup.find_all('img')
        issues = []

        with_alt = 0
        without_alt = 0
        decorative = 0

        for img in images:
            src = img.get('src', '')[:50]
            alt = img.get('alt')

            if alt is None:
                without_alt += 1
                issues.append({
                    "element": f"<img src=\"{src}\">",
                    "issue": "alt属性がありません",
                    "suggestion": "画像の内容を説明するalt属性を追加してください"
                })
            elif alt == "":
                decorative += 1
            else:
                with_alt += 1

        return {
            "wcag": "1.1.1",
            "name": "画像の説明文",
            "total_images": len(images),
            "with_alt": with_alt,
            "without_alt": without_alt,
            "decorative": decorative,
            "status": "ok" if without_alt == 0 else "warning",
            "issues": issues[:10]
        }

    def check_heading_hierarchy(self) -> Dict:
        """見出し階層チェック"""
        headings = []
        for level in range(1, 7):
            for h in self.soup.find_all(f'h{level}'):
                headings.append({
                    "level": level,
                    "text": h.get_text()[:50].strip()
                })

        issues = []

        h1_count = len([h for h in headings if h["level"] == 1])
        if h1_count == 0:
            issues.append({
                "issue": "h1見出しがありません",
                "suggestion": "ページに1つのh1見出しを設定してください"
            })
        elif h1_count > 1:
            issues.append({
                "issue": f"h1見出しが{h1_count}個あります",
                "suggestion": "h1見出しは1ページに1つが推奨されます"
            })

        prev_level = 0
        for h in headings:
            if h["level"] > prev_level + 1 and prev_level > 0:
                issues.append({
                    "issue": f"h{prev_level}の後にh{h['level']}があります（h{prev_level+1}をスキップ）",
                    "suggestion": f"h{h['level']}の前にh{prev_level+1}を入れるか、見出しレベルを調整してください"
                })
            prev_level = h["level"]

        return {
            "wcag": "1.3.1",
            "name": "見出しの階層",
            "headings": headings[:20],
            "h1_count": h1_count,
            "status": "ok" if len(issues) == 0 else "warning",
            "issues": issues
        }

    def check_link_text(self) -> Dict:
        """リンクテキストの明確さチェック"""
        links = self.soup.find_all('a', href=True)
        issues = []

        vague_patterns = [
            r'^こちら$',
            r'^ここ$',
            r'^click$',
            r'^here$',
            r'^詳細$',
            r'^もっと見る$',
            r'^続きを読む$',
        ]

        link_texts = {}

        for link in links:
            text = link.get_text().strip()
            href = link.get('href', '')

            for pattern in vague_patterns:
                if re.match(pattern, text, re.IGNORECASE):
                    issues.append({
                        "element": f"<a href=\"{href[:30]}\">{text}</a>",
                        "issue": f"「{text}」だけではリンク先が分かりません",
                        "suggestion": "リンク先の内容が分かるテキストに変更してください"
                    })
                    break

            if text:
                if text not in link_texts:
                    link_texts[text] = []
                if href not in link_texts[text]:
                    link_texts[text].append(href)

        for text, hrefs in link_texts.items():
            if len(hrefs) > 1 and len(text) > 2:
                issues.append({
                    "issue": f"「{text[:20]}」が複数の異なるリンク先に使用されています",
                    "suggestion": "各リンクを区別できるテキストに変更してください"
                })

        return {
            "wcag": "2.4.4",
            "name": "リンクの分かりやすさ",
            "total_links": len(links),
            "status": "ok" if len(issues) == 0 else "warning",
            "issues": issues[:10]
        }

    def check_form_labels(self) -> Dict:
        """フォームラベルチェック"""
        inputs = self.soup.find_all(['input', 'select', 'textarea'])
        issues = []

        skip_types = ['hidden', 'submit', 'button', 'reset', 'image']

        for inp in inputs:
            input_type = inp.get('type', 'text')

            if input_type in skip_types:
                continue

            input_id = inp.get('id')
            input_name = inp.get('name', '')
            has_label = False

            if input_id:
                label = self.soup.find('label', attrs={'for': input_id})
                if label:
                    has_label = True

            if inp.get('aria-label') or inp.get('aria-labelledby'):
                has_label = True

            if inp.get('placeholder'):
                has_label = True

            if not has_label:
                issues.append({
                    "element": f"<{inp.name} name=\"{input_name}\">",
                    "issue": "ラベルが設定されていません",
                    "suggestion": "<label for=\"...\">を追加するか、aria-labelを設定してください"
                })

        return {
            "wcag": "3.3.2",
            "name": "フォームのラベル",
            "total_inputs": len([i for i in inputs if i.get('type', 'text') not in skip_types]),
            "status": "ok" if len(issues) == 0 else "warning",
            "issues": issues[:10]
        }

    def check_color_contrast(self) -> Dict:
        """色のコントラスト（簡易版）"""
        issues = []

        elements_with_color = self.soup.find_all(style=re.compile(r'color'))

        for elem in elements_with_color[:20]:
            style = elem.get('style', '')
            if re.search(r'color:\s*#[cdef]{3,6}', style, re.IGNORECASE):
                issues.append({
                    "element": elem.name,
                    "issue": "薄い色のテキストが使用されている可能性",
                    "suggestion": "コントラスト比4.5:1以上を確保してください"
                })

        return {
            "wcag": "1.4.3",
            "name": "色のコントラスト",
            "note": "インラインスタイルのみ簡易チェック",
            "status": "ok" if len(issues) == 0 else "info",
            "issues": issues,
            "recommendation": "詳細なコントラストチェックはブラウザの開発者ツールやaxeを使用してください"
        }

    def run_all_checks(self) -> Dict:
        """全チェック実行"""
        results = {
            "images_alt": self.check_images_alt(),
            "heading_hierarchy": self.check_heading_hierarchy(),
            "link_text": self.check_link_text(),
            "form_labels": self.check_form_labels(),
            "color_contrast": self.check_color_contrast()
        }

        level_a_checks = ["images_alt", "heading_hierarchy", "link_text", "form_labels"]
        level_a_passed = sum(1 for check in level_a_checks if results[check]["status"] == "ok")

        if level_a_passed == len(level_a_checks):
            wcag_level = "A準拠"
            score = 100
        elif level_a_passed >= len(level_a_checks) * 0.7:
            wcag_level = "部分準拠"
            score = 70
        else:
            wcag_level = "要改善"
            score = 40

        return {
            "checks": results,
            "wcag_level": wcag_level,
            "score": score,
            "level_a_passed": level_a_passed,
            "level_a_total": len(level_a_checks)
        }


def get_wcag_compliance_level(results: Dict) -> Dict:
    """WCAG準拠レベルを判定"""
    level_a_status = []
    level_aa_status = []

    for check_result in results.get("checks", {}).values():
        wcag = check_result.get("wcag", "")
        status = check_result.get("status", "")

        criteria = WCAG_CRITERIA.get(wcag, {})
        level = criteria.get("level", "A")

        if level == "A":
            level_a_status.append(status == "ok")
        elif level == "AA":
            level_aa_status.append(status == "ok")

    level_a_pass_rate = sum(level_a_status) / len(level_a_status) if level_a_status else 0
    level_aa_pass_rate = sum(level_aa_status) / len(level_aa_status) if level_aa_status else 0

    if level_a_pass_rate == 1.0 and level_aa_pass_rate == 1.0:
        compliance = "AA準拠"
    elif level_a_pass_rate == 1.0:
        compliance = "A準拠"
    elif level_a_pass_rate >= 0.7:
        compliance = "部分準拠"
    else:
        compliance = "要改善"

    return {
        "compliance_level": compliance,
        "level_a_pass_rate": round(level_a_pass_rate, 2),
        "level_aa_pass_rate": round(level_aa_pass_rate, 2)
    }


def format_accessibility_result(result: Dict, mode: str = "simple") -> Dict:
    """チェック結果のフォーマット"""
    from core.ui.design_system import LEGAL_ICONS_FALLBACK

    score = result["score"]
    wcag_level = result["wcag_level"]

    if score >= 80:
        status = "良好"
        status_color = "success"
    elif score >= 50:
        status = "改善推奨"
        status_color = "warning"
    else:
        status = "要改善"
        status_color = "danger"

    items = []

    for check_result in result["checks"].values():
        check_status = check_result["status"]
        issues = check_result.get("issues", [])

        if check_status == "ok":
            icon = LEGAL_ICONS_FALLBACK["compliant"]
            text = f"{check_result['name']}: 問題なし"
            subtext = ""
        else:
            icon = LEGAL_ICONS_FALLBACK["warning"]
            issue_count = len(issues)
            text = f"{check_result['name']}: {issue_count}件の改善点"
            subtext = issues[0]["issue"] if issues else ""

        items.append({
            "icon": icon,
            "text": text,
            "subtext": subtext,
            "wcag": check_result.get("wcag", "")
        })

    faq = [
        {
            "question": "アクセシビリティとは？",
            "answer": "障害のある人を含め、全ての人がウェブサイトを利用できるようにすることです。視覚障害者向けのスクリーンリーダー対応などが含まれます。"
        },
        {
            "question": "alt属性は必須ですか？",
            "answer": "はい。画像の内容を説明するalt属性は、視覚障害者がスクリーンリーダーで内容を理解するために必要です。装飾目的の画像はalt=\"\"（空）を設定します。"
        }
    ]

    return {
        "title": "アクセシビリティチェック",
        "subtitle": "全ての人がサイトを利用できるかを確認",
        "status": status,
        "status_color": status_color,
        "wcag_level": wcag_level,
        "score": score,
        "items": items,
        "faq": faq if mode == "simple" else []
    }


ACCESSIBILITY_IMPROVEMENTS = {
    "missing_alt": {
        "simple": "画像に説明文（alt属性）を追加してください",
        "detail": "alt属性は、画像が表示できない場合や、スクリーンリーダーが読み上げる際に使用されます。画像の内容を簡潔に説明するテキストを設定してください。",
        "example": '<img src="product.jpg" alt="青いTシャツ、Mサイズ、綿100%">'
    },
    "heading_skip": {
        "simple": "見出しの順番を正しくしてください（h1→h2→h3）",
        "detail": "見出しレベルを飛ばすと、スクリーンリーダーのユーザーがページ構造を理解しにくくなります。h1の次はh2、h2の次はh3というように順番に使用してください。",
        "example": "<h1>ページタイトル</h1><h2>セクション</h2><h3>サブセクション</h3>"
    },
    "vague_link": {
        "simple": "リンクテキストを分かりやすくしてください",
        "detail": "「こちら」「ここ」などの曖昧なリンクテキストは、スクリーンリーダーのユーザーがリンク先を理解しにくくなります。リンク先の内容が分かるテキストに変更してください。",
        "example": "× <a href=\"...\">こちら</a> → ○ <a href=\"...\">商品一覧を見る</a>"
    },
    "missing_label": {
        "simple": "フォーム入力欄にラベルを追加してください",
        "detail": "ラベルがないと、スクリーンリーダーのユーザーが何を入力すべきか分かりません。<label>要素を使用して入力欄と紐付けてください。",
        "example": '<label for="email">メールアドレス</label><input type="email" id="email">'
    }
}
