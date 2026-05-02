"""
視認性・到達性チェック（Phase 04強化版）
"""

import re
from typing import Dict, List, Optional


class VisibilityChecker:
    """文字サイズや隠しテキストの簡易チェックを行う"""

    MIN_FONT_SIZE_PX = 12
    LEGAL_KEYWORDS = [
        "特定商取引",
        "特商法",
        "特定商取引法に基づく表記",
        "特定商取引法に基づく表示",
        "返品",
        "返金",
        "交換",
        "返品・交換",
        "返品条件",
        "返金条件",
        "配送",
        "送料",
        "配送方法",
        "お届け",
        "支払い",
        "決済",
        "お支払い方法",
        "FAQ",
        "よくある質問",
        "ガイド",
        "ご利用案内",
        "会社概要",
        "会社情報",
        "利用規約",
        "プライバシー",
        "個人情報",
    ]

    # Phase 04: ページネーション除外パターン
    PAGINATION_PATTERNS = [
        r"^[<>«»‹›]$",           # 矢印記号
        r"^[<>]{2,4}$",          # >> / << / >>> 等
        r"^[«»]{2,4}$",          # »» 等
        r"^[‹›]{2,4}$",          # ›› 等
        r"^(prev|next|前|次|前へ|次へ)$",  # ナビゲーションテキスト
        r"^\.{2,3}$",            # 省略記号 (.. or ...)
        r"^…$",                  # 三点リーダー
        r"^\d{1,3}$",            # ページ番号 (1-999)
    ]

    # Phase 04: SNSアイコン除外パターン（hrefで判定）
    SNS_HREF_PATTERNS = [
        r"twitter\.com",
        r"x\.com",
        r"facebook\.com",
        r"instagram\.com",
        r"line\.me",
        r"youtube\.com",
        r"linkedin\.com",
        r"tiktok\.com",
    ]

    def check_visibility(self, soup, is_ec: bool = True) -> List[Dict]:
        """文字サイズ・非表示・リンク到達性の簡易チェックを実行
        
        Args:
            soup: BeautifulSoupオブジェクト
            is_ec: ECサイトかどうか（Falseの場合、リンク到達性は参考情報に格下げ）
        """
        issues = []

        for element in soup.find_all(style=True):
            style = element.get("style", "")
            text = element.get_text(strip=True)

            match = re.search(r"font-size\s*:\s*([0-9.]+)px", style, re.IGNORECASE)
            if match and text:
                size_px = float(match.group(1))
                if size_px < self.MIN_FONT_SIZE_PX:
                    is_legal_text = any(keyword in text for keyword in self.LEGAL_KEYWORDS)
                    if is_legal_text:
                        issues.append(
                            {
                                "type": "small_font_legal",
                                "severity": "high",
                                "title": "規約・重要情報の文字サイズが小さい",
                                "detail": f"{size_px}px: {text[:60]}",
                            }
                        )
                    else:
                        issues.append(
                            {
                                "type": "small_font",
                                "severity": "warning",
                                "title": "文字サイズが小さい",
                                "detail": f"{size_px}px: {text[:60]}",
                            }
                        )

            if any(token in style.replace(" ", "").lower() for token in ["display:none", "visibility:hidden", "opacity:0"]):
                if text:
                    issues.append(
                        {
                            "type": "hidden_text",
                            "severity": "warning",
                            "title": "非表示テキストの可能性",
                            "detail": text[:60],
                        }
                    )

        # Phase 04: 改善されたリンク到達性チェック
        low_reachability_issues = self._check_link_reachability(soup, is_ec)
        issues.extend(low_reachability_issues)

        return issues

    def _check_link_reachability(self, soup, is_ec: bool) -> List[Dict]:
        """Phase 04: リンク到達性チェック（改善版）"""
        candidates: List[Dict] = []

        for link in soup.find_all("a"):
            link_text = link.get_text(strip=True)
            label = link.get("aria-label") or link.get("title") or ""
            href = link.get("href") or ""

            # 十分なテキストがあればスキップ
            if len(link_text) > 1 or label:
                continue

            # Phase 04: 除外チェック
            if self._is_excluded_link(link, link_text, href):
                continue

            # HTML抜粋を生成（デバッグ用）
            html_snippet = self._generate_html_snippet(link)

            # 位置情報を取得
            location = self._get_link_location(link)

            # Phase 04: ECサイト以外は参考情報に格下げ
            severity = "warning" if is_ec else "info"
            category = "アクセシビリティ" if not is_ec else "到達性"

            candidates.append(
                {
                    "href": href,
                    "location": location,
                    "html_snippet": html_snippet,
                }
            )

        if not candidates:
            return []

        # 1リンクごとに同一カードが並ばないよう、代表例をまとめて1件に集約
        examples = []
        for item in candidates[:3]:
            href = item.get("href") or ""
            loc = item.get("location") or ""
            snippet = item.get("html_snippet") or ""
            parts = []
            if loc:
                parts.append(loc)
            if href:
                parts.append(href[:80])
            if snippet:
                parts.append(snippet[:80])
            if parts:
                examples.append(" / ".join(parts))

        detail = f"リンクテキストが短すぎます（{len(candidates)}件）。"
        if examples:
            detail += " 例: " + " | ".join(examples)

        return [
            {
                "type": "low_reachability",
                "severity": "warning" if is_ec else "info",
                "title": "リンクの到達性が低い",
                "detail": detail,
                "category": "アクセシビリティ" if not is_ec else "到達性",
                "location": candidates[0].get("location") or "本文内",
                "html_snippet": candidates[0].get("html_snippet") or "",
            }
        ]

    def _is_excluded_link(self, link, link_text: str, href: str) -> bool:
        """Phase 04: 除外すべきリンクか判定"""
        # 1. 画像を含むリンクは除外（バナー等）
        if link.find("img"):
            img = link.find("img")
            alt = (img.get("alt") or "").strip()
            aria = (link.get("aria-label") or "").strip()
            title = (link.get("title") or "").strip()
            # 代替テキストがある画像リンクは除外、ない場合は要確認として残す
            if alt or aria or title:
                return True

        # 2. ページネーションパターンに一致
        for pattern in self.PAGINATION_PATTERNS:
            if re.match(pattern, link_text, re.IGNORECASE):
                return True

        # 3. SNSリンクは除外
        for pattern in self.SNS_HREF_PATTERNS:
            if re.search(pattern, href, re.IGNORECASE):
                return True

        # 4. アンカーリンク（#から始まる）は除外
        if href.startswith("#"):
            return True

        # 5. javascriptリンクは除外
        if href.lower().startswith("javascript:"):
            return True

        return False

    def _generate_html_snippet(self, link, max_length: int = 80) -> str:
        """リンクのHTML抜粋を生成"""
        try:
            html_str = str(link)
            if len(html_str) > max_length:
                return html_str[:max_length] + "..."
            return html_str
        except Exception:
            return "<a>...</a>"

    def _get_link_location(self, link) -> str:
        """リンクの配置場所を特定"""
        parent = link.parent
        depth = 0
        max_depth = 10

        while parent and depth < max_depth:
            tag_name = parent.name if parent.name else ""
            classes = parent.get("class", []) or []
            element_id = parent.get("id", "") or ""

            # タグ名チェック
            if tag_name == "footer":
                return "フッター"
            if tag_name == "header":
                return "ヘッダー"
            if tag_name == "nav":
                return "ナビゲーション"
            if tag_name == "aside":
                return "サイドバー"

            # クラス名/IDでサイドバー検出
            class_str = " ".join(classes).lower() if classes else ""
            id_str = element_id.lower()

            if any(pat in class_str or pat in id_str for pat in ["sidebar", "side-bar", "menu", "nav", "pagination", "pager"]):
                return "ナビゲーション/サイドバー"

            parent = parent.parent
            depth += 1

        return "本文内"
