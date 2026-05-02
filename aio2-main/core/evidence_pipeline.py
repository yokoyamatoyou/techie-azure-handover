# -*- coding: utf-8 -*-
"""
証拠抽出・正規化パイプライン基盤

Phase 01: Baseline and Evidence Pipeline
- 共通スキーマ定義
- 正規化ユーティリティ
- HTMLロケーター
- 証拠抽出ラッパー
"""

import re
import unicodedata
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from bs4 import BeautifulSoup, Tag
from difflib import SequenceMatcher


# ============================================================
# 共通スキーマ定義
# ============================================================

@dataclass
class EvidenceItem:
    """検出結果の共通スキーマ"""
    issue_id: str                          # 一意のID (category + hash)
    category: str                          # カテゴリ (tokushoho, stealth, premiums, security, etc.)
    severity: str                          # 重要度 (high, medium, low, info)
    matched_text: str                      # マッチしたテキスト
    location: str                          # 検出位置 (heading, title, meta, table, list, footer, etc.)
    evidence: str                          # 根拠となるスニペット (周辺文脈を含む)
    confidence: float                      # 信頼度 (0.0 - 1.0)

    # 追加フィールド（オプション）
    sub_category: str = ""                 # サブカテゴリ
    suggestion: str = ""                   # 改善提案
    legal_basis: str = ""                  # 法的根拠
    dom_path: str = ""                     # DOM上のパス
    char_position: int = -1                # テキスト内の文字位置

    def to_dict(self) -> Dict:
        """辞書形式で返す"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'EvidenceItem':
        """辞書からインスタンスを生成"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def generate_issue_id(category: str, text: str, location: str = "") -> str:
    """一意の問題IDを生成"""
    normalized = normalize_text(text)[:50]
    hash_input = f"{category}:{normalized}:{location}"
    return f"{category}_{abs(hash(hash_input)) % 100000:05d}"


# ============================================================
# 正規化ユーティリティ
# ============================================================

def normalize_text(text: str) -> str:
    """
    テキストの正規化
    - 全角→半角変換
    - 空白・改行の正規化
    - 記号の統一
    """
    if not text:
        return ""

    # Unicode正規化 (NFKC)
    text = unicodedata.normalize('NFKC', text)

    # 全角英数字→半角
    text = _fullwidth_to_halfwidth(text)

    # 全角記号の一部を半角に
    symbol_map = {
        '：': ':', '；': ';', '，': ',', '．': '.',
        '！': '!', '？': '?', '（': '(', '）': ')',
        '［': '[', '］': ']', '｛': '{', '｝': '}',
        '＠': '@', '＃': '#', '＄': '$', '％': '%',
        '＆': '&', '＊': '*', '＋': '+', '－': '-',
        '＝': '=', '＜': '<', '＞': '>', '／': '/',
        '＼': '\\', '｜': '|', '～': '~', '＾': '^',
    }
    for full, half in symbol_map.items():
        text = text.replace(full, half)

    # 連続空白を単一に
    text = re.sub(r'[ \t　]+', ' ', text)

    # 改行の正規化
    text = re.sub(r'\r\n|\r|\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _fullwidth_to_halfwidth(text: str) -> str:
    """全角英数字を半角に変換"""
    result = []
    for char in text:
        code = ord(char)
        # 全角英数字 (0xFF01-0xFF5E) → 半角 (0x0021-0x007E)
        if 0xFF01 <= code <= 0xFF5E:
            result.append(chr(code - 0xFEE0))
        # 全角スペース
        elif code == 0x3000:
            result.append(' ')
        else:
            result.append(char)
    return ''.join(result)


def normalize_whitespace(text: str) -> str:
    """空白・改行のみ正規化（文字変換なし）"""
    if not text:
        return ""
    text = re.sub(r'[ \t　]+', ' ', text)
    text = re.sub(r'\r\n|\r|\n', '\n', text)
    return text.strip()


def extract_japanese_name(text: str) -> Optional[str]:
    """日本人名の抽出"""
    # 姓名パターン (漢字2-4文字 + 空白 + 漢字1-4文字)
    patterns = [
        r'([一-龯]{1,4})[\s　]+([一-龯]{1,4})',  # 姓 名
        r'([一-龯]{2,4})([一-龯]{1,4})',          # 姓名（空白なし）
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group().strip()
    return None


def extract_postal_code(text: str) -> Optional[str]:
    """郵便番号の抽出"""
    patterns = [
        r'〒?\s*(\d{3})-?(\d{4})',
        r'郵便番号[:：]?\s*(\d{3})-?(\d{4})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
    return None


def extract_phone_number(text: str) -> Optional[str]:
    """電話番号の抽出"""
    patterns = [
        r'0\d{1,4}[-ー]?\d{1,4}[-ー]?\d{4}',
        r'0\d{9,10}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None


def extract_email(text: str) -> Optional[str]:
    """メールアドレスの抽出"""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group() if match else None


# ============================================================
# HTMLロケーター
# ============================================================

class HTMLLocator:
    """HTML内の要素位置を特定するクラス"""

    LOCATION_TYPES = {
        'title': 'titleタグ',
        'meta_description': 'meta description',
        'meta_keywords': 'meta keywords',
        'h1': 'h1見出し',
        'h2': 'h2見出し',
        'h3': 'h3見出し',
        'h4': 'h4見出し',
        'h5': 'h5見出し',
        'h6': 'h6見出し',
        'header': 'ヘッダー',
        'footer': 'フッター',
        'nav': 'ナビゲーション',
        'sidebar': 'サイドバー',
        'main': 'メインコンテンツ',
        'article': '記事本文',
        'table': 'テーブル',
        'list': 'リスト',
        'form': 'フォーム',
        'button': 'ボタン',
        'link': 'リンク',
        'paragraph': '段落',
        'unknown': '本文内',
    }

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        self._text_cache = None
        self._position_map = {}

    def locate_text(self, text: str) -> Dict[str, Any]:
        """
        テキストの出現位置を特定

        Returns:
            {
                "location": "h2見出し",
                "location_type": "h2",
                "dom_path": "body > article > h2",
                "context": "周辺テキスト...",
                "char_position": 1234,
                "confidence": 0.95
            }
        """
        if not text:
            return self._empty_location()

        normalized_text = normalize_whitespace(text)

        # 特定の要素内を順に検索
        locations_to_check = [
            ('title', self.soup.find('title')),
            ('meta_description', self.soup.find('meta', attrs={'name': 'description'})),
        ]

        # title
        title = self.soup.find('title')
        if title and normalized_text in normalize_whitespace(title.get_text()):
            return self._build_location('title', title, text)

        # meta description
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        if meta_desc and normalized_text in normalize_whitespace(meta_desc.get('content', '')):
            return self._build_location('meta_description', meta_desc, text)

        # 見出し (h1-h6)
        for i in range(1, 7):
            for heading in self.soup.find_all(f'h{i}'):
                if normalized_text in normalize_whitespace(heading.get_text()):
                    return self._build_location(f'h{i}', heading, text)

        # header/footer/nav
        for section in ['header', 'footer', 'nav']:
            elem = self.soup.find(section)
            if elem and normalized_text in normalize_whitespace(elem.get_text()):
                return self._build_location(section, elem, text)

        # table
        for table in self.soup.find_all('table'):
            if normalized_text in normalize_whitespace(table.get_text()):
                return self._build_location('table', table, text)

        # リスト (ul/ol/dl)
        for list_type in ['ul', 'ol', 'dl']:
            for lst in self.soup.find_all(list_type):
                if normalized_text in normalize_whitespace(lst.get_text()):
                    return self._build_location('list', lst, text)

        # article/main
        for section in ['article', 'main']:
            elem = self.soup.find(section)
            if elem and normalized_text in normalize_whitespace(elem.get_text()):
                return self._build_location(section, elem, text)

        # ボタン/リンク
        for tag in self.soup.find_all(['button', 'a']):
            if normalized_text in normalize_whitespace(tag.get_text()):
                location_type = 'button' if tag.name == 'button' else 'link'
                return self._build_location(location_type, tag, text)

        # 段落
        for p in self.soup.find_all('p'):
            if normalized_text in normalize_whitespace(p.get_text()):
                return self._build_location('paragraph', p, text)

        # 最終的にbody全体から検索
        body = self.soup.find('body')
        if body and normalized_text in normalize_whitespace(body.get_text()):
            return self._build_location('unknown', body, text)

        return self._empty_location()

    def _build_location(self, location_type: str, element: Tag, text: str) -> Dict[str, Any]:
        """位置情報を構築"""
        dom_path = self._get_dom_path(element)
        context = self._extract_context(element, text)
        full_text = self.soup.get_text() if self.soup else ""
        char_position = full_text.find(text) if text else -1

        return {
            "location": self.LOCATION_TYPES.get(location_type, '本文内'),
            "location_type": location_type,
            "dom_path": dom_path,
            "context": context,
            "char_position": char_position,
            "confidence": self._calculate_location_confidence(location_type, element)
        }

    def _empty_location(self) -> Dict[str, Any]:
        """空の位置情報"""
        return {
            "location": "本文内",
            "location_type": "unknown",
            "dom_path": "",
            "context": "",
            "char_position": -1,
            "confidence": 0.0
        }

    def _get_dom_path(self, element: Tag) -> str:
        """DOM上のパスを取得"""
        if not element or not hasattr(element, 'name'):
            return ""

        path_parts = []
        current = element
        while current and hasattr(current, 'name') and current.name:
            if current.name == '[document]':
                break
            classes = current.get('class', [])
            class_str = f".{'.'.join(classes)}" if classes else ""
            id_str = f"#{current.get('id')}" if current.get('id') else ""
            path_parts.append(f"{current.name}{id_str}{class_str}")
            current = current.parent

        return ' > '.join(reversed(path_parts[-5:]))  # 最大5階層

    def _extract_context(self, element: Tag, text: str, context_chars: int = 50) -> str:
        """周辺文脈を抽出"""
        if not element:
            return ""

        full_text = element.get_text()
        if not full_text:
            return ""

        pos = full_text.find(text)
        if pos == -1:
            # 正規化後で再検索
            normalized = normalize_whitespace(full_text)
            pos = normalized.find(normalize_whitespace(text))
            if pos == -1:
                return full_text[:100] + "..." if len(full_text) > 100 else full_text

        start = max(0, pos - context_chars)
        end = min(len(full_text), pos + len(text) + context_chars)

        context = full_text[start:end].strip()
        if start > 0:
            context = "..." + context
        if end < len(full_text):
            context = context + "..."

        return context

    def _calculate_location_confidence(self, location_type: str, element: Tag) -> float:
        """位置の信頼度を計算"""
        # 重要な位置ほど高い信頼度
        confidence_map = {
            'title': 1.0,
            'h1': 0.95,
            'meta_description': 0.9,
            'h2': 0.85,
            'header': 0.8,
            'footer': 0.75,
            'table': 0.85,
            'list': 0.8,
            'article': 0.7,
            'main': 0.7,
            'nav': 0.6,
            'sidebar': 0.5,
            'paragraph': 0.6,
            'link': 0.5,
            'button': 0.5,
            'unknown': 0.3,
        }
        return confidence_map.get(location_type, 0.5)


# ============================================================
# DOM構造からのラベル-値抽出
# ============================================================

class LabelValueExtractor:
    """DOM構造からラベル:値のペアを抽出"""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def extract_all(self) -> List[Dict[str, str]]:
        """全てのラベル-値ペアを抽出"""
        results = []

        # テーブルから抽出
        results.extend(self._extract_from_tables())

        # dl/dt/ddから抽出
        results.extend(self._extract_from_dl())

        # ラベル: 値 形式のテキストから抽出
        results.extend(self._extract_from_text_patterns())

        return results

    def _extract_from_tables(self) -> List[Dict[str, str]]:
        """テーブルからラベル-値を抽出"""
        results = []

        for table in self.soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                # th + td パターン
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    label = normalize_whitespace(th.get_text())
                    value = normalize_whitespace(td.get_text())
                    if label and value:
                        results.append({
                            'label': label,
                            'value': value,
                            'source': 'table',
                            'element': row
                        })
                else:
                    # td + td パターン (最初のtdがラベル)
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        label = normalize_whitespace(tds[0].get_text())
                        value = normalize_whitespace(tds[1].get_text())
                        if label and value and len(label) < 30:  # ラベルは短いはず
                            results.append({
                                'label': label,
                                'value': value,
                                'source': 'table',
                                'element': row
                            })

        return results

    def _extract_from_dl(self) -> List[Dict[str, str]]:
        """dl/dt/ddからラベル-値を抽出"""
        results = []

        for dl in self.soup.find_all('dl'):
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')

            for dt, dd in zip(dts, dds):
                label = normalize_whitespace(dt.get_text())
                value = normalize_whitespace(dd.get_text())
                if label and value:
                    results.append({
                        'label': label,
                        'value': value,
                        'source': 'dl',
                        'element': dl
                    })

        return results

    def _extract_from_text_patterns(self) -> List[Dict[str, str]]:
        """テキストパターンからラベル-値を抽出"""
        results = []

        # ラベル: 値 または ラベル：値 パターン
        text = self.soup.get_text()
        pattern = r'([^\n:：]{2,20})[:：]\s*([^\n]+)'

        for match in re.finditer(pattern, text):
            label = normalize_whitespace(match.group(1))
            value = normalize_whitespace(match.group(2))

            # フィルタリング: 明らかにラベルでないもの
            if label and value and not re.match(r'^https?://', value):
                results.append({
                    'label': label,
                    'value': value[:200],  # 長すぎる値は切り詰め
                    'source': 'text_pattern',
                    'element': None
                })

        return results

    def find_by_labels(self, label_patterns: List[str]) -> List[Dict[str, str]]:
        """指定したラベルパターンに一致する値を検索"""
        all_pairs = self.extract_all()
        results = []

        for pair in all_pairs:
            label = pair['label'].lower()
            for pattern in label_patterns:
                if re.search(pattern, label, re.IGNORECASE):
                    results.append(pair)
                    break

        return results


# ============================================================
# 証拠抽出ラッパー
# ============================================================

def extract_evidence_snippet(text: str, match_text: str, context_chars: int = 50) -> str:
    """
    マッチしたテキストの周辺を含む証拠スニペットを抽出
    """
    if not text or not match_text:
        return ""

    pos = text.find(match_text)
    if pos == -1:
        # 正規化して再検索
        normalized_text = normalize_text(text)
        normalized_match = normalize_text(match_text)
        pos = normalized_text.find(normalized_match)
        if pos == -1:
            return match_text[:100]

    start = max(0, pos - context_chars)
    end = min(len(text), pos + len(match_text) + context_chars)

    snippet = text[start:end].strip()

    # 前後に省略記号
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


def wrap_check_result(
    result: Dict,
    category: str,
    soup: BeautifulSoup = None
) -> Dict:
    """
    既存のチェック結果に証拠・位置・信頼度を追加するラッパー

    既存の返却構造は壊さず、追加フィールドとして拡張
    """
    if soup:
        locator = HTMLLocator(soup)
    else:
        locator = None

    # issuesキーがある場合
    if 'issues' in result and isinstance(result['issues'], list):
        enhanced_issues = []
        for issue in result['issues']:
            enhanced = _enhance_issue(issue, category, locator)
            enhanced_issues.append(enhanced)
        result['issues'] = enhanced_issues

    # itemsキーがある場合
    if 'items' in result and isinstance(result['items'], list):
        enhanced_items = []
        for item in result['items']:
            enhanced = _enhance_issue(item, category, locator)
            enhanced_items.append(enhanced)
        result['items'] = enhanced_items

    return result


def _enhance_issue(issue: Dict, category: str, locator: HTMLLocator = None) -> Dict:
    """個別の問題にevidence/location/confidenceを追加"""
    enhanced = dict(issue)

    # 既存のマッチテキストを取得
    matched_text = issue.get('matched_text', issue.get('detected_value', ''))

    # issue_idを生成
    if 'issue_id' not in enhanced:
        enhanced['issue_id'] = generate_issue_id(
            category,
            matched_text,
            issue.get('location', '')
        )

    # categoryを追加
    if 'category' not in enhanced:
        enhanced['category'] = category

    # severityの正規化
    if 'severity' not in enhanced:
        risk_level = issue.get('risk_level', issue.get('importance', 'medium'))
        enhanced['severity'] = _normalize_severity(risk_level)

    # evidenceを追加
    if 'evidence' not in enhanced and matched_text:
        enhanced['evidence'] = matched_text[:150]

    # locationを追加/強化
    if locator and matched_text:
        location_info = locator.locate_text(matched_text)
        if 'location' not in enhanced or enhanced['location'] == '本文内':
            enhanced['location'] = location_info['location']
        enhanced['dom_path'] = location_info.get('dom_path', '')
        enhanced['char_position'] = location_info.get('char_position', -1)
        if 'confidence' not in enhanced:
            enhanced['confidence'] = location_info.get('confidence', 0.5)

    # confidenceのデフォルト
    if 'confidence' not in enhanced:
        enhanced['confidence'] = 0.5

    return enhanced


def _normalize_severity(risk_level: str) -> str:
    """リスクレベルをseverityに正規化"""
    mapping = {
        'high': 'high',
        'high_risk': 'high',
        'very_strict': 'high',
        'strict': 'high',
        'medium': 'medium',
        'medium_risk': 'medium',
        'normal': 'medium',
        'low': 'low',
        'low_risk': 'low',
        'info': 'info',
    }
    return mapping.get(risk_level.lower() if risk_level else 'medium', 'medium')


# ============================================================
# 重複検出・類似度計算
# ============================================================

def calculate_similarity(text1: str, text2: str) -> float:
    """2つのテキスト間の類似度を計算 (0.0 - 1.0)"""
    if not text1 or not text2:
        return 0.0

    # 正規化
    norm1 = normalize_text(text1).lower()
    norm2 = normalize_text(text2).lower()

    # 完全一致
    if norm1 == norm2:
        return 1.0

    # SequenceMatcherで類似度計算
    return SequenceMatcher(None, norm1, norm2).ratio()


def is_duplicate(item1: Dict, item2: Dict, threshold: float = 0.8) -> bool:
    """2つの検出項目が重複かどうか判定"""
    # 同じカテゴリでないと重複とみなさない
    if item1.get('category') != item2.get('category'):
        return False

    text1 = item1.get('matched_text', item1.get('evidence', ''))
    text2 = item2.get('matched_text', item2.get('evidence', ''))

    return calculate_similarity(text1, text2) >= threshold


def deduplicate_issues(issues: List[Dict], threshold: float = 0.8) -> List[Dict]:
    """重複する問題を統合"""
    if not issues:
        return []

    # 重複グループを構築
    groups = []
    used = set()

    for i, issue in enumerate(issues):
        if i in used:
            continue

        group = [issue]
        used.add(i)

        for j, other in enumerate(issues[i+1:], i+1):
            if j in used:
                continue
            if is_duplicate(issue, other, threshold):
                group.append(other)
                used.add(j)

        groups.append(group)

    # 各グループから代表を選択（最も信頼度が高いもの）
    result = []
    for group in groups:
        representative = max(group, key=lambda x: x.get('confidence', 0))

        # 統合情報を追加
        if len(group) > 1:
            representative['duplicate_count'] = len(group)
            representative['merged_from'] = [
                g.get('issue_id', '') for g in group if g != representative
            ]

        result.append(representative)

    return result


# ============================================================
# Phase 04: 高度な重複統合と証拠集約
# ============================================================

@dataclass
class IssueCluster:
    """統合された問題クラスター"""
    representative: Dict                   # 代表となる問題
    members: List[Dict] = field(default_factory=list)  # 統合されたメンバー
    category: str = ""
    severity: str = "medium"
    total_confidence: float = 0.0
    evidence_summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "representative": self.representative,
            "member_count": len(self.members),
            "category": self.category,
            "severity": self.severity,
            "total_confidence": self.total_confidence,
            "evidence_summary": self.evidence_summary,
            "merged_issue_ids": [m.get('issue_id', '') for m in self.members],
        }


class IssueDeduplicator:
    """高度な重複統合処理（Phase 04）"""

    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold

    def deduplicate_and_cluster(self, issues: List[Dict]) -> Dict:
        """
        問題を重複統合し、クラスタリング

        Returns:
            {
                "clusters": [...],
                "total_original": 10,
                "total_deduplicated": 6,
                "by_category": {...},
                "by_severity": {...}
            }
        """
        if not issues:
            return self._empty_result()

        # カテゴリごとにグループ化
        by_category = {}
        for issue in issues:
            cat = issue.get('category', 'unknown')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(issue)

        # 各カテゴリ内で重複統合
        all_clusters = []
        for category, category_issues in by_category.items():
            clusters = self._cluster_within_category(category_issues, category)
            all_clusters.extend(clusters)

        # 統計情報を計算
        by_severity = {"high": 0, "medium": 0, "low": 0}
        for cluster in all_clusters:
            sev = cluster.severity
            if sev in by_severity:
                by_severity[sev] += 1

        return {
            "clusters": [c.to_dict() for c in all_clusters],
            "total_original": len(issues),
            "total_deduplicated": len(all_clusters),
            "reduction_rate": round(1 - len(all_clusters) / len(issues), 2) if issues else 0,
            "by_category": {cat: len(items) for cat, items in by_category.items()},
            "by_severity": by_severity,
        }

    def _cluster_within_category(self, issues: List[Dict], category: str) -> List[IssueCluster]:
        """カテゴリ内でクラスタリング"""
        if not issues:
            return []

        clusters = []
        used = set()

        # 正規化キーでグループ化
        key_groups = {}
        for i, issue in enumerate(issues):
            key = self._generate_normalization_key(issue)
            if key not in key_groups:
                key_groups[key] = []
            key_groups[key].append((i, issue))

        # 完全一致グループを先にクラスタ化
        for key, group in key_groups.items():
            if len(group) > 1:
                indices = [g[0] for g in group]
                members = [g[1] for g in group]
                used.update(indices)
                clusters.append(self._create_cluster(members, category))

        # 残りを類似度でクラスタリング
        remaining = [(i, issue) for i, issue in enumerate(issues) if i not in used]

        while remaining:
            i, issue = remaining.pop(0)
            if i in used:
                continue

            group = [issue]
            used.add(i)

            for j, other in remaining[:]:
                if j in used:
                    continue
                if self._is_similar(issue, other):
                    group.append(other)
                    used.add(j)
                    remaining = [(idx, iss) for idx, iss in remaining if idx != j]

            clusters.append(self._create_cluster(group, category))

        return clusters

    def _generate_normalization_key(self, issue: Dict) -> str:
        """正規化キーを生成"""
        matched_text = issue.get('matched_text', issue.get('evidence', ''))
        normalized = normalize_text(matched_text).lower()[:50]
        category = issue.get('category', '')
        return f"{category}:{normalized}"

    def _is_similar(self, issue1: Dict, issue2: Dict) -> bool:
        """2つの問題が類似かどうか判定"""
        text1 = issue1.get('matched_text', issue1.get('evidence', ''))
        text2 = issue2.get('matched_text', issue2.get('evidence', ''))
        return calculate_similarity(text1, text2) >= self.similarity_threshold

    def _create_cluster(self, members: List[Dict], category: str) -> IssueCluster:
        """クラスタを作成"""
        # 最も信頼度の高いものを代表に
        representative = max(members, key=lambda x: x.get('confidence', 0))

        # 重要度は最も高いものを採用
        severity_order = {"high": 3, "medium": 2, "low": 1, "info": 0}
        highest_severity = max(
            members,
            key=lambda x: severity_order.get(x.get('severity', 'medium'), 1)
        ).get('severity', 'medium')

        # 証拠サマリを生成
        evidence_summary = self._generate_evidence_summary(members)

        # 合計信頼度
        total_confidence = sum(m.get('confidence', 0) for m in members) / len(members)

        return IssueCluster(
            representative=representative,
            members=members,
            category=category,
            severity=highest_severity,
            total_confidence=round(total_confidence, 2),
            evidence_summary=evidence_summary,
        )

    def _generate_evidence_summary(self, members: List[Dict]) -> str:
        """証拠のサマリを生成"""
        if len(members) == 1:
            return members[0].get('evidence', members[0].get('matched_text', ''))[:100]

        # 代表的な証拠 + 追加件数
        representative = members[0].get('evidence', members[0].get('matched_text', ''))[:60]
        return f"{representative}（他{len(members)-1}件）"

    def _empty_result(self) -> Dict:
        return {
            "clusters": [],
            "total_original": 0,
            "total_deduplicated": 0,
            "reduction_rate": 0,
            "by_category": {},
            "by_severity": {"high": 0, "medium": 0, "low": 0},
        }


def aggregate_legal_check_results(results: Dict) -> Dict:
    """
    法務チェック結果を統合（Phase 04）

    各チェッカーの結果を統合し、重複を除去
    """
    all_issues = []

    def _collect_issues(section: Dict) -> List[Dict]:
        collected: List[Dict] = []
        if not isinstance(section, dict):
            return collected

        # 1) 直接 issues/items を持つケース
        for key in ("issues", "items"):
            entries = section.get(key, [])
            if isinstance(entries, list):
                collected.extend([e for e in entries if isinstance(e, dict)])

        # 2) legal_checks の標準構造（raw/formatted）を再帰走査
        for nested_key in ("raw", "formatted"):
            nested = section.get(nested_key)
            if isinstance(nested, dict):
                collected.extend(_collect_issues(nested))

        # 3) consumer_protection 固有構造
        for key in ("visibility", "best_practices", "lawyer_report"):
            entries = section.get(key, [])
            if isinstance(entries, list):
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    normalized = dict(entry)
                    normalized.setdefault("category", key)
                    collected.append(normalized)

        return collected

    # 各チェッカーからissuesを収集
    for _, value in results.items():
        if isinstance(value, dict):
            all_issues.extend(_collect_issues(value))

    # 重複統合
    deduplicator = IssueDeduplicator()
    dedup_result = deduplicator.deduplicate_and_cluster(all_issues)

    return {
        "aggregated_issues": dedup_result["clusters"],
        "total_original": dedup_result["total_original"],
        "total_deduplicated": dedup_result["total_deduplicated"],
        "reduction_rate": dedup_result["reduction_rate"],
        "by_category": dedup_result["by_category"],
        "by_severity": dedup_result["by_severity"],
    }


def generate_deep_dive_summary(aggregated: Dict) -> Dict:
    """
    深掘り表示用のサマリを生成（Phase 04）
    """
    clusters = aggregated.get("aggregated_issues", [])

    # 重要度別に分類
    high_priority = [c for c in clusters if c.get("severity") == "high"]
    medium_priority = [c for c in clusters if c.get("severity") == "medium"]
    low_priority = [c for c in clusters if c.get("severity") == "low"]

    # 1行サマリ
    if high_priority:
        headline = f"重要: {len(high_priority)}件の高リスク項目があります"
    elif medium_priority:
        headline = f"注意: {len(medium_priority)}件の確認項目があります"
    else:
        headline = "問題は検出されませんでした"

    return {
        "headline": headline,
        "high_priority": high_priority[:5],  # 上位5件
        "medium_priority": medium_priority[:5],
        "low_priority": low_priority[:3],
        "total_issues": len(clusters),
        "category_breakdown": aggregated.get("by_category", {}),
    }
