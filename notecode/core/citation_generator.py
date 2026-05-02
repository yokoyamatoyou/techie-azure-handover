"""
Citation Snippet Generator

AIに引用されやすい文を抽出し、JSON-LD speakable マークアップ付きで出力する。

References:
- speakable: https://schema.org/speakable
- Nielsen's Heuristic #6: 記憶負荷の軽減 - コピー可能なカード化
"""

import json
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


class CitationSnippetGenerator:
    """
    高スコアの引用候補文を抽出し、JSON-LD speakable マークアップ付きで出力。
    """

    # 引用されやすい文のパターン（正規表現）
    CITATION_PATTERNS = [
        # 定義文
        r"[^。]+(?:とは|とは、)[^。]+(?:です|である|ことです|こと)。",
        # 数値・統計を含む文
        r"[^。]*(?:\d+(?:\.\d+)?(?:％|%|倍|件|人|円|万|億))[^。]*。",
        # 結論・要約文
        r"(?:つまり|要するに|結論として|まとめると)[^。]+。",
        # リスト冒頭
        r"(?:以下の|次の|主な|代表的な)\d*(?:つ|点|項目)[^。]*。",
    ]

    # 低品質文のパターン（除外用）
    EXCLUDE_PATTERNS = [
        r"詳しくは[^。]*。",
        r"こちらをご覧ください",
        r"お問い合わせ",
        r"クリックしてください",
    ]

    def __init__(self, min_length: int = 30, max_length: int = 200):
        """
        Args:
            min_length: 抽出する文の最小文字数
            max_length: 抽出する文の最大文字数
        """
        self.min_length = min_length
        self.max_length = max_length

    def extract_snippets(
        self,
        html: str,
        top_n: int = 3,
        existing_citation_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        引用されやすい文を抽出。

        Args:
            html: 分析対象のHTML
            top_n: 抽出する候補数
            existing_citation_data: 既存の引用分析データ（あれば優先利用）

        Returns:
            [{"text": str, "score": float, "reason": str, "markup": str}]
        """
        soup = BeautifulSoup(html, "html.parser")

        # 本文テキストを抽出（スクリプト・スタイル除去）
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        sentences = self._split_sentences(text)

        candidates = []

        for sentence in sentences:
            if not self._is_valid_sentence(sentence):
                continue

            score, reason = self._score_sentence(sentence)
            if score > 0:
                candidates.append({
                    "text": sentence.strip(),
                    "score": score,
                    "reason": reason,
                })

        # 既存の引用分析データがあれば、そのスコアも加味
        if existing_citation_data:
            axes = existing_citation_data.get("axes", [])
            for axis in axes:
                sample = axis.get("sample_sentence")
                if sample and len(sample) >= self.min_length:
                    # 既存サンプルを高スコアで追加
                    quality_score = axis.get("quality_score", 50)
                    candidates.append({
                        "text": sample.strip(),
                        "score": quality_score + 20,  # 既存分析からのボーナス
                        "reason": f"{axis.get('label', '引用分析')}からの候補",
                    })

        # スコア順にソートして上位を返す
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # 重複除去
        seen = set()
        unique_candidates = []
        for c in candidates:
            text_key = c["text"][:50]
            if text_key not in seen:
                seen.add(text_key)
                unique_candidates.append(c)

        return unique_candidates[:top_n]

    def generate_speakable_markup(
        self,
        snippets: List[Dict[str, Any]],
        url: str,
    ) -> str:
        """
        JSON-LD speakable マークアップを生成。

        Args:
            snippets: extract_snippets() の戻り値
            url: 対象ページのURL

        Returns:
            JSON-LD文字列（そのままHTMLに埋め込み可能）
        """
        if not snippets:
            return ""

        # speakable用のセレクタ生成（CSSセレクタは簡易版）
        speakable_texts = [s["text"] for s in snippets[:3]]

        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "url": url,
            "speakable": {
                "@type": "SpeakableSpecification",
                "cssSelector": [".speakable-content"],
            },
            "description": speakable_texts[0] if speakable_texts else "",
        }

        return json.dumps(schema, ensure_ascii=False, indent=2)

    def generate_html_snippet(self, snippet: Dict[str, Any]) -> str:
        """
        コピー用のHTML断片を生成（speakableクラス付き）。

        Args:
            snippet: 単一のスニペット辞書

        Returns:
            HTML文字列
        """
        text = snippet.get("text", "")
        escaped_text = text.replace("<", "&lt;").replace(">", "&gt;")
        return f'<p class="speakable-content">{escaped_text}</p>'

    def _split_sentences(self, text: str) -> List[str]:
        """日本語の文を分割"""
        # 句点で分割
        sentences = re.split(r"(?<=[。！？])", text)
        return [s.strip() for s in sentences if s.strip()]

    def _is_valid_sentence(self, sentence: str) -> bool:
        """有効な文かどうかを判定"""
        length = len(sentence)
        if length < self.min_length or length > self.max_length:
            return False

        # 除外パターンに一致したらNG
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, sentence):
                return False

        return True

    def _score_sentence(self, sentence: str) -> tuple:
        """
        文のスコアと理由を算出。

        Returns:
            (score: float, reason: str)
        """
        score = 0.0
        reasons = []

        # パターンマッチによるスコアリング
        for i, pattern in enumerate(self.CITATION_PATTERNS):
            if re.search(pattern, sentence):
                if i == 0:  # 定義文
                    score += 30
                    reasons.append("定義文パターン")
                elif i == 1:  # 数値・統計
                    score += 25
                    reasons.append("数値・統計を含む")
                elif i == 2:  # 結論・要約
                    score += 20
                    reasons.append("結論・要約文")
                elif i == 3:  # リスト冒頭
                    score += 15
                    reasons.append("リスト導入文")

        # 文長による調整（60-120文字が最適）
        length = len(sentence)
        if 60 <= length <= 120:
            score += 10
            reasons.append("最適な文長")
        elif 40 <= length < 60 or 120 < length <= 150:
            score += 5

        # 具体的な固有名詞・専門用語（カタカナ語）
        katakana_count = len(re.findall(r"[ァ-ヶー]+", sentence))
        if katakana_count >= 2:
            score += 5
            reasons.append("専門用語を含む")

        reason = "・".join(reasons) if reasons else "一般的な文"
        return score, reason


def extract_citation_snippets(
    html: str,
    url: str,
    existing_citation_data: Optional[Dict[str, Any]] = None,
    top_n: int = 3,
) -> Dict[str, Any]:
    """
    便利関数: スニペット抽出とマークアップ生成を一括実行。

    Returns:
        {
            "snippets": [...],
            "speakable_markup": "...",
            "html_snippets": [...]
        }
    """
    generator = CitationSnippetGenerator()
    snippets = generator.extract_snippets(html, top_n, existing_citation_data)

    return {
        "snippets": snippets,
        "speakable_markup": generator.generate_speakable_markup(snippets, url),
        "html_snippets": [generator.generate_html_snippet(s) for s in snippets],
    }
