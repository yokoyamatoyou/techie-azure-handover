"""PDF report generation and visualization utilities using fpdf2."""

from __future__ import annotations

import tempfile
import base64
import io
import os
import re
import sys
import asyncio
from pathlib import Path
from datetime import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF, HTMLMixin
from jinja2 import Environment, FileSystemLoader
from wordcloud import WordCloud
import json

try:
    from analysis import (
        ReportCommentary,
        generate_report_commentary,
    )
except Exception:
    from dataclasses import dataclass

    @dataclass
    class ReportCommentary:
        summary_text: str = ""
        action_items: list[str] = None
        sentiment_commentary: str = ""
        topics_commentary: str = ""

    def generate_report_commentary(*_args, **_kwargs):
        raise RuntimeError("analysis module not available")
from PDFreport.config.pdf_config import settings

def tokenize_texts(texts: List[str], allowed_pos: List[str] = ["名詞"]) -> List[str]:
    """日本語テキストを分割し、ストップワードを除外する（SudachiPy使用）。
    
    Args:
        texts: 分割対象のテキストリスト
        allowed_pos: 許可する品詞のリスト（デフォルト: ["名詞"]）
        
    Returns:
        List[str]: 分割・フィルタリングされた単語リスト
    """
    try:
        # SudachiPyベースのトークナイザーを使用
        from sudachipy import dictionary, tokenizer as sudachi_tokenizer
        
        # SudachiPyトークナイザーを初期化
        sudachi_mode = sudachi_tokenizer.Tokenizer.SplitMode.B
        sudachi = dictionary.Dictionary().create()
        
        # ストップワードファイルの読み込み
        stopwords = set()
        stopwords_file = os.path.join(os.path.dirname(__file__), 'stopwords_ja.txt')
        
        try:
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        stopwords.add(word)
        except FileNotFoundError:
            # ファイルが見つからない場合はデフォルトのストップワードを使用
            stopwords = {
                'だった', 'である', 'です', 'ます', 'でした', 'と思う', 'こと', 'もの', 'とき', 'ため',
                'ので', 'から', 'まで', 'より', 'ほど', 'だけ', 'のみ', 'ばかり', 'くらい', 'ぐらい',
                'など', 'なんか', 'なんて', 'なんと', 'なんの', 'これ', 'それ', 'あれ', 'どれ',
                'どこ', 'いつ', 'なぜ', 'どう', 'なに', 'わたし', 'ぼく', 'あなた', 'かれ', 'かのじょ',
                'みんな', 'みな', 'とても', 'すごく', 'かなり', 'けっこう', 'わりと', 'まあまあ',
                'ちょっと', 'すこし', 'だいぶ', 'そして', 'また', 'さらに', 'しかし', 'でも',
                'けれど', 'けれども', 'ただし', 'なお', 'ちなみに', 'よう', 'そう', 'こう', 'ああ'
            }
        
        # SudachiPyでトークン化
        words = []
        for text in texts:
            if not text or pd.isna(text):
                continue
                
            for m in sudachi.tokenize(str(text), sudachi_mode):
                # 名詞のみを抽出（代名詞・数詞は除外）
                pos = m.part_of_speech()
                if (pos[0] == "名詞" and 
                    pos[1] not in ["代名詞", "数詞"] and 
                    pos[2] not in ["代名詞", "数詞"]):
                    lemma = m.dictionary_form()
                    if (lemma and len(lemma) > 1 and 
                        lemma not in stopwords and
                        not lemma.isdigit()):
                        words.append(lemma)
        
        return words
        
    except ImportError:
        # SudachiPyが利用できない場合のフォールバック
        print("Warning: SudachiPy not available, using regex fallback")
        return _fallback_tokenize(texts, allowed_pos)
    except Exception as e:
        print(f"Warning: SudachiPy tokenization failed: {e}, using regex fallback")
        return _fallback_tokenize(texts, allowed_pos)


def _fallback_tokenize(texts: List[str], allowed_pos: List[str] = ["名詞"]) -> List[str]:
    """SudachiPyが利用できない場合のフォールバック関数"""
    import re
    
    # デフォルトのストップワード
    stopwords = {
        'だった', 'である', 'です', 'ます', 'でした', 'と思う', 'こと', 'もの', 'とき', 'ため',
        'ので', 'から', 'まで', 'より', 'ほど', 'だけ', 'のみ', 'ばかり', 'くらい', 'ぐらい',
        'など', 'なんか', 'なんて', 'なんと', 'なんの', 'これ', 'それ', 'あれ', 'どれ',
        'どこ', 'いつ', 'なぜ', 'どう', 'なに', 'わたし', 'ぼく', 'あなた', 'かれ', 'かのじょ',
        'みんな', 'みな', 'とても', 'すごく', 'かなり', 'けっこう', 'わりと', 'まあまあ',
        'ちょっと', 'すこし', 'だいぶ', 'そして', 'また', 'さらに', 'しかし', 'でも',
        'けれど', 'けれども', 'ただし', 'なお', 'ちなみに', 'よう', 'そう', 'こう', 'ああ'
    }
    
    words = []
    for text in texts:
        if not text or pd.isna(text):
            continue
            
        # ひらがな、カタカナ、漢字、英数字の連続を単語として抽出
        text_words = re.findall(r'[ひらがなカタカナ一-龯a-zA-Z0-9]+', str(text))
        
        # フィルタリング
        for word in text_words:
            # 長さが2文字以上
            if len(word) < 2:
                continue
            # ストップワードでない
            if word in stopwords:
                continue
            # 数字のみでない
            if word.isdigit():
                continue
            # 英数字のみでない（日本語が含まれている）
            if not re.search(r'[ひらがなカタカナ一-龯]', word):
                continue
                
            words.append(word)
    
    return words

# --- Constants ---------------------------------------------------------------
A4_WIDTH = 210
A4_HEIGHT = 297
MARGIN = 15

COLOR_PRIMARY = (44, 62, 80)  # #2c3e50
COLOR_SECONDARY = (52, 152, 219)  # #3498db
COLOR_TEXT = (51, 51, 51)  # #333333
COLOR_LIGHT_GRAY = (242, 242, 242)  # #f2f2f2

_FONT_CONFIGURED = False


# シンプルなテーマ設定（デザイン変更を容易にするための集中管理）
THEME = {
    "margins": {
        "left": 15,
        "top": 15,
        "right": 15,
        "bottom": 15,
    },
    "spacing": {
        "xs": 4,
        "sm": 6,
        "md": 10,
        "lg": 14,
        "xl": 20,
    },
    "font_sizes": {
        "title": 24,
        "h1": 18,
        "h2": 12,
        "body": 10,
        "small": 8,
    },
    "chart_widths": {
        "sentiment": 120,
        "topics": 170,
    },
}


def _content_width(pdf: "ReportPDF") -> float:
    """現在ページの描画可能幅を返す（左右マージンを除いた幅）。"""
    return float(pdf.w) - float(pdf.l_margin) - float(pdf.r_margin)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) == 6:
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        return (r, g, b)
    raise ValueError(f"Invalid hex color: {value}")


def _merge_theme(defaults: dict, overrides: dict) -> dict:
    merged = dict(defaults)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _merge_theme(merged[k], v)
        else:
            merged[k] = v
    return merged


def _determine_action_priority(index: int, max_items: int) -> str:
    """推奨アクションの優先度ラベルを決定"""
    if max_items <= 0:
        return "高"
    high_threshold = min(3, max_items)
    medium_threshold = min(max_items, high_threshold + 3)
    if index <= high_threshold:
        return "高"
    if index <= medium_threshold:
        return "中"
    return "低"


def load_theme() -> dict:
    """theme.json を読み込み、既定THEMEにマージ。なければ既定を返す。"""
    script_dir = Path(__file__).resolve().parent
    theme_path = script_dir / "theme.json"
    if theme_path.exists():
        try:
            with theme_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return _merge_theme(THEME, data)
        except Exception:
            return THEME
    return THEME


# 外部テーマの読み込みと色反映
THEME = load_theme()
try:
    if "colors" in THEME:
        COLOR_PRIMARY = _hex_to_rgb(THEME["colors"].get("primary", "#2c3e50"))
        COLOR_TEXT = _hex_to_rgb(THEME["colors"].get("text", "#333333"))
        # SECONDARY/LIGHT_GRAY は任意
        COLOR_SECONDARY = _hex_to_rgb(THEME["colors"].get("secondary", "#3498db"))
        COLOR_LIGHT_GRAY = _hex_to_rgb(THEME["colors"].get("border", "#f2f2f2"))
except Exception:
    pass


def get_font_paths() -> tuple[Optional[str], Optional[str]]:
    """同梱フォント NotoSansJP のパスを取得する。
    
    Returns:
        tuple[Optional[str], Optional[str]]: (通常フォントパス, 太字フォントパス)のタプル。
            見つからない場合は (None, None) を返す。
    """
    script_dir = Path(__file__).resolve().parent
    fonts_candidates = [
        script_dir / "fonts",
        script_dir.parent / "portable_app" / "fonts",
    ]
    candidates = [
        ("NotoSansJP-Regular.ttf", "NotoSansJP-Bold.ttf"),
        ("NotoSansJP-Regular.otf", "NotoSansJP-Bold.otf"),
        ("NotoSansJP-Regular.ttf", "NotoSansJP-Regular.ttf"),  # 太字なし時
        ("NotoSansJP-Regular.otf", "NotoSansJP-Regular.otf"),
    ]
    for fonts_dir in fonts_candidates:
        for reg, bold in candidates:
            reg_p = fonts_dir / reg
            bold_p = fonts_dir / bold
            if reg_p.exists():
                return reg_p.resolve(), (bold_p.resolve() if bold_p.exists() else reg_p.resolve())
    return None, None


def set_japanese_font() -> bool:
    """Matplotlibに同梱NotoSansJPを設定（失敗時はArial系にフォールバック）。"""
    global _FONT_CONFIGURED
    if _FONT_CONFIGURED:
        return True
    reg, _ = get_font_paths()
    if reg and reg.exists():
        try:
            mpl.font_manager.fontManager.addfont(str(reg))
            name = mpl.font_manager.FontProperties(fname=str(reg)).get_name()
            mpl.rcParams["font.family"] = name
            mpl.rcParams["font.sans-serif"] = [name]
            mpl.rcParams["axes.unicode_minus"] = False
            _FONT_CONFIGURED = True
            return True
        except Exception:
            pass
    # フォールバック（日本語表示は崩れる可能性あり）
    mpl.rcParams["font.family"] = "sans-serif"
    mpl.rcParams["font.sans-serif"] = ["Arial", "Liberation Sans"]
    mpl.rcParams["axes.unicode_minus"] = False
    _FONT_CONFIGURED = True
    return True


# --- Chart generation -------------------------------------------------------


def create_sentiment_pie_chart_base64(sentiment_counts) -> str:
    """Return a base64 PNG string of the sentiment distribution pie chart."""
    # キャッシュの確認
    try:
        from utils.chart_cache import get_chart_cache
        chart_cache = get_chart_cache()
        
        # データを辞書に変換（キャッシュキー生成用）
        if hasattr(sentiment_counts, 'to_dict'):
            data_dict = sentiment_counts.to_dict()
        elif isinstance(sentiment_counts, dict):
            data_dict = sentiment_counts
        else:
            data_dict = dict(sentiment_counts) if sentiment_counts else {}
        
        # キャッシュから取得を試みる
        cached_result = chart_cache.get_cached_chart(data_dict, "sentiment_pie")
        if cached_result:
            return cached_result
    except Exception:
        # キャッシュの取得に失敗した場合は通常処理を続行
        pass
    
    # データ型の互換性を確保（辞書またはpandas Seriesの両方に対応）
    if isinstance(sentiment_counts, dict):
        if not sentiment_counts:  # 空の辞書の場合
            return ""
        # 辞書をpandas Seriesに変換
        import pandas as pd
        sentiment_counts = pd.Series(sentiment_counts)
    elif hasattr(sentiment_counts, 'empty') and sentiment_counts.empty:
        return ""
    
    if not set_japanese_font():
        return ""

    fig, ax = plt.subplots()
    ax.pie(
        sentiment_counts,
        labels=sentiment_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=THEME.get("charts", {}).get("sentimentColors", ["#4CAF50", "#FFC107", "#F44336", "#9E9E9E"]),
    )
    ax.axis("equal")
    ax.set_title("感情分析サマリー")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    base64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    # キャッシュに保存
    try:
        from utils.chart_cache import get_chart_cache
        chart_cache = get_chart_cache()
        
        # データを辞書に変換（キャッシュキー生成用）
        if hasattr(sentiment_counts, 'to_dict'):
            data_dict = sentiment_counts.to_dict()
        elif isinstance(sentiment_counts, dict):
            data_dict = sentiment_counts
        else:
            data_dict = dict(sentiment_counts) if sentiment_counts else {}
        
        chart_cache.cache_chart(data_dict, "sentiment_pie", base64_image)
    except Exception:
        # キャッシュの保存に失敗した場合は無視
        pass
    
    return base64_image


def create_topics_bar_chart_base64(topic_counts) -> str:
    """Return a base64 PNG string of the top topics bar chart."""
    # データ型の互換性を確保（辞書またはpandas Seriesの両方に対応）
    if isinstance(topic_counts, dict):
        if not topic_counts:  # 空の辞書の場合
            return ""
        # 辞書をpandas Seriesに変換
        import pandas as pd
        topic_counts = pd.Series(topic_counts)
    elif hasattr(topic_counts, 'empty') and topic_counts.empty:
        return ""
    
    if not set_japanese_font():
        return ""

    # 文字詰まり改善のためサイズと間隔を調整
    fig, ax = plt.subplots(figsize=(12, 10))  # サイズを大きく（10,8→12,10）
    color = THEME.get("charts", {}).get("topicsColor", "#2c3e50")
    
    # Top 15に制限
    top_topics = topic_counts.sort_values(ascending=False).head(15)
    top_topics.sort_values().plot(kind="barh", ax=ax, color=color, height=0.7)  # バーの高さを調整
    
    ax.set_title("主要トピック Top 15", fontsize=15, fontweight="bold", pad=15)  # タイトル間隔改善
    ax.set_xlabel("出現回数", fontsize=13, fontweight="bold")
    ax.tick_params(axis='y', labelsize=11, pad=8)  # Y軸ラベルのフォントサイズと間隔を調整
    ax.tick_params(axis='x', labelsize=11)  # X軸ラベルのフォントサイズを調整
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def create_moderation_bar_chart_base64(moderation_summary: dict[str, int]) -> str:
    """Return a base64 PNG string of the moderation summary bar chart."""
    if not set_japanese_font() or not moderation_summary:
        return ""

    labels = list(moderation_summary.keys())
    values = list(moderation_summary.values())

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values, color=THEME.get("charts", {}).get("moderationBarColor", "skyblue"))
    ax.set_title("モデレーション結果サマリー")
    ax.set_ylabel("フラグ数")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def create_emotion_analysis_chart_base64(emotion_avg: dict[str, float]) -> str:
    """Return a base64 PNG string of the emotion analysis chart."""
    if not set_japanese_font() or not emotion_avg:
        return ""
    
    # 感情名の日本語マッピング
    emotion_names_jp = {
        "joy": "喜び", "sadness": "悲しみ", "fear": "恐れ",
        "surprise": "驚き", "anger": "怒り", "disgust": "嫌悪",
        "shame": "恥", "relief": "安心", "anticipation": "期待", 
        "disappointment": "失望"
    }
    
    # 感情カテゴリ分類
    emotion_categories = {
        "positive": ["joy", "surprise", "relief", "anticipation"],
        "negative": ["sadness", "fear", "anger", "disgust", "disappointment"],
        "contextual": ["shame"]
    }
    
    # データ準備
    emotions = []
    scores = []
    colors = []
    
    for emotion, score in emotion_avg.items():
        if emotion in emotion_names_jp:
            emotions.append(emotion_names_jp[emotion])
            scores.append(score)
            
            # カテゴリに応じた色分け
            category = next(
                (cat for cat, emotion_list in emotion_categories.items() 
                 if emotion in emotion_list), "other"
            )
            
            if category == "positive":
                colors.append("#2ecc71")  # 緑
            elif category == "negative":
                colors.append("#e74c3c")  # 赤
            elif category == "contextual":
                colors.append("#9b59b6")  # 紫
            else:
                colors.append("#95a5a6")  # グレー
    
    # チャート作成（文字詰まり改善のためサイズと間隔を調整）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))  # サイズを大きく（16,8→18,10）
    
    # 左側：個別感情スコア（横軸0～5、軸幅調整）
    bars = ax1.barh(emotions, scores, color=colors, height=0.6)  # バーの高さを調整（文字詰まり改善）
    ax1.set_xlabel("スコア", fontsize=13, fontweight="bold")
    ax1.set_ylabel("感情", fontsize=13, fontweight="bold")
    ax1.set_title("感情分析結果（個別スコア）", fontsize=15, fontweight="bold", pad=15)  # pad追加でタイトル間隔改善
    ax1.set_xlim(0, 5)
    ax1.set_xticks(range(0, 6))  # 0～5の目盛りを明示的に設定
    ax1.tick_params(axis='y', labelsize=11, pad=8)  # Y軸ラベルのフォントサイズと間隔を調整
    ax1.tick_params(axis='x', labelsize=11)  # X軸ラベルのフォントサイズを調整
    ax1.grid(True, alpha=0.3, axis='x')  # グリッドを追加して軸幅を明確化
    
    # スコア値をバーの右端に表示（小数点以下2位まで）
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                f"{score:.2f}", va='center', fontsize=10, ha='left')  # 小数点以下2位表示
    
    # 右側：カテゴリ別平均スコア
    category_scores = {}
    for emotion, score in emotion_avg.items():
        category = next(
            (cat for cat, emotion_list in emotion_categories.items() 
             if emotion in emotion_list), "other"
        )
        if category not in category_scores:
            category_scores[category] = []
        category_scores[category].append(score)
    
    category_names = {
        "positive": "ポジティブ", "negative": "ネガティブ", 
        "contextual": "文脈依存", "other": "その他"
    }
    
    category_labels = []
    category_means = []
    category_colors = []
    
    for category, scores_list in category_scores.items():
        if scores_list:
            category_labels.append(category_names.get(category, category))
            category_means.append(sum(scores_list) / len(scores_list))
            
            if category == "positive":
                category_colors.append("#2ecc71")
            elif category == "negative":
                category_colors.append("#e74c3c")
            elif category == "contextual":
                category_colors.append("#9b59b6")
            else:
                category_colors.append("#95a5a6")
    
    bars2 = ax2.bar(category_labels, category_means, color=category_colors, width=0.5)  # バーの幅を調整
    ax2.set_ylabel("平均スコア", fontsize=13, fontweight="bold")
    ax2.set_title("感情カテゴリ別平均スコア", fontsize=15, fontweight="bold", pad=15)  # pad追加でタイトル間隔改善
    ax2.set_ylim(0, 5)  # 0-5の6段階スケールに変更
    ax2.tick_params(axis='x', labelsize=12, pad=10)  # X軸ラベルのフォントサイズと間隔を調整
    ax2.tick_params(axis='y', labelsize=11)  # Y軸ラベルのフォントサイズを調整
    
    # スコア値をバーの上に表示（小数点以下2位まで）
    for bar, score in zip(bars2, category_means):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                f"{score:.2f}", ha='center', va='bottom', fontsize=10)  # 小数点以下2位表示
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# --- PDF generation ---------------------------------------------------------


class ReportPDF(FPDF):
    """Custom PDF class for 5-page survey reports with Japanese font."""

    def __init__(self):
        super().__init__()
        self.font_family = "Japanese"
        # 互換性確保: ロゴレンダラーが未提供でもエラーにしない
        class _NullLogoRenderer:
            def add_logo_to_pdf(self, pdf: "ReportPDF", context: str = "cover") -> None:
                # ロゴ未設定時は何もしない
                return
        self.logo_renderer = _NullLogoRenderer()

    def header(self) -> None:
        pass

    def footer(self) -> None:
        self.set_y(-15)
        # フォントが未登録でもエラーにせずArialへ退避
        try:
            self.set_font(self.font_family, "", 8)
        except Exception:
            self.set_font("Arial", "", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", border=0, align="C")

    def setup_fonts(self):
        """NotoSansJP を登録。未検出なら明確な例外を投げる。
        既存の .pkl キャッシュが古い絶対パスを保持していると不具合の原因になるため、登録前に削除する。
        登録ファミリ名は絶対パスに基づくハッシュで一意化する。
        日本語パス環境でのエラーを防ぐため、パス処理を強化。
        """
        reg, bold = get_font_paths()
        if not (reg and reg.exists()):
            raise FileNotFoundError(
                "同梱フォントが見つかりません。'coding/survey_analysis_mvp/fonts' に NotoSansJP-Regular.ttf を配置してください。"
            )
        fonts_dir = reg.parent
        # 古いキャッシュの削除（NotoSansJP関連）
        try:
            for pkl in fonts_dir.glob("*.pkl"):
                if pkl.name.lower().startswith("notosansjp") or "cw127" in pkl.name.lower():
                    try:
                        pkl.unlink()
                    except Exception:
                        pass
        except Exception:
            pass
        
        # 絶対パスから一意なファミリ名を生成（日本語パス対応）
        import hashlib
        try:
            # パスを正規化してからハッシュ化
            normalized_path = str(reg.resolve()).replace('\\', '/')
            digest = hashlib.sha1(normalized_path.encode("utf-8")).hexdigest()[:8]
            self.font_family = f"NotoSansJP_{digest}"
        except Exception:
            # フォールバック：シンプルな名前を使用
            self.font_family = "NotoSansJP"
        
        # fpdf2の推奨APIに沿って登録（uni引数は非推奨のため未使用）
        try:
            # パスを正規化してから登録
            reg_path = str(reg.resolve()).replace('\\', '/')
            bold_path = str((bold or reg).resolve()).replace('\\', '/')
            
            self.add_font(self.font_family, "", reg_path)
            self.add_font(self.font_family, "B", bold_path)
            
            print(f"フォント登録成功: {self.font_family}")
        except Exception as e:
            # より詳細なエラー情報を提供
            error_msg = f"フォント登録に失敗しました: {e}\n"
            error_msg += f"フォントパス: {reg}\n"
            error_msg += f"太字パス: {bold or reg}\n"
            error_msg += f"作業ディレクトリ: {os.getcwd()}\n"
            error_msg += f"Python実行パス: {sys.executable}"
            raise RuntimeError(error_msg)

    def add_perspective_pages(
        self,
        perspective_texts: dict[str, str],
        survey_type: str = "customer_satisfaction"
    ) -> None:
        """アンケート形態に応じた適切なペルソナ視点ページを追加する。"""
        def add_page_with_title(title: str, body: str):
            self.add_page()
            self.set_text_color(*COLOR_TEXT)
            self.add_heading(title, level="h1")
            self.add_paragraph(body or "本文が未生成です。")

        # アンケート形態に応じたペルソナ名のマッピング（見出し形式なし）
        persona_mapping = {
            "customer_satisfaction": {
                "marketing_perspective": "マーケティングマネージャー",
                "user_perspective": "プロダクトマネージャー", 
                "consultant_perspective": "カスタマーサクセスマネージャー"
            },
            "employee_satisfaction": {
                "marketing_perspective": "人事マネージャー",
                "user_perspective": "組織開発コンサルタント",
                "consultant_perspective": "経営陣"
            },
            "public_opinion": {
                "marketing_perspective": "政策アナリスト",
                "user_perspective": "行政学専門家",
                "consultant_perspective": "地域代表"
            },
            "market_research": {
                "marketing_perspective": "市場調査アナリスト",
                "user_perspective": "ブランドマネージャー",
                "consultant_perspective": "事業開発マネージャー"
            },
            "brand_research": {
                "marketing_perspective": "ブランド戦略家",
                "user_perspective": "クリエイティブディレクター",
                "consultant_perspective": "マーケティングコミュニケーションマネージャー"
            }
        }
        
        # デフォルトマッピング
        default_mapping = {
            "marketing_perspective": "マーケティング",
            "user_perspective": "ユーザー",
            "consultant_perspective": "コンサルタント"
        }
        
        # 適切なマッピングを選択
        mapping = persona_mapping.get(survey_type, default_mapping)
        
        # 各視点のページを追加
        for key, title in mapping.items():
            text = perspective_texts.get(key)
            if text:
                add_page_with_title(title, text)

    # Page builders ------------------------------------------------------

    # --- Component helpers (for consistent layout) ---------------------
    def add_heading(self, text: str, level: str = "h1") -> None:
        size_map = {
            "title": THEME["font_sizes"].get("title", 24),
            "h1": THEME["font_sizes"].get("h1", 18),
            "h2": THEME["font_sizes"].get("h2", 12),
        }
        height_map = {
            "title": THEME["spacing"].get("lg", 14),
            "h1": THEME["spacing"].get("lg", 14),
            "h2": THEME["spacing"].get("md", 10),
        }
        self.set_font(self.font_family, "B", size_map.get(level, size_map["h1"]))
        self.cell(0, height_map.get(level, height_map["h1"]), text, border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        if level in ("title", "h1"):
            self.ln(THEME["spacing"].get("sm", 6))

    def add_paragraph(self, text: str) -> None:
        self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
        self.set_x(THEME["margins"].get("left", 15))
        # 日本語折返し対応: CHARラップ
        self.multi_cell(_content_width(self), THEME["spacing"].get("sm", 6) + 1, text or "", 0, "L", wrapmode='CHAR')

    def add_table(self, headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None) -> None:
        self.set_font(self.font_family, "B", THEME["font_sizes"].get("body", 10))
        row_h = THEME["spacing"].get("sm", 6) + 2
        if not col_widths:
            total_w = _content_width(self)
            num_cols = max(1, len(headers))
            col_widths = [total_w / num_cols] * num_cols
        for header, w in zip(headers, col_widths):
            self.cell(w, row_h, header, border=1, align="C")
        self.cell(0, row_h, "", border=0, new_x="LMARGIN", new_y="NEXT")
        self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
        for row in rows:
            for cell_text, w in zip(row, col_widths):
                self.cell(w, row_h, str(cell_text), border=1, align="L")
            self.cell(0, row_h, "", border=0, new_x="LMARGIN", new_y="NEXT")

    def add_chart_with_caption(
        self, 
        title: str, 
        chart_base64: str, 
        caption_title: str, 
        caption_text: str, 
        chart_width: int
    ) -> None:
        self.set_text_color(*COLOR_TEXT)
        self.add_heading(title, level="h1")
        if chart_base64:
            tmp_file_path = ""
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    tmp_file.write(base64.b64decode(chart_base64))
                    tmp_file_path = tmp_file.name
                x_pos = (A4_WIDTH - chart_width) / 2
                self.image(tmp_file_path, x=x_pos, w=chart_width)
                self.ln(THEME["spacing"].get("sm", 6))
            finally:
                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
        self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
        self.cell(0, THEME["spacing"].get("md", 10), caption_title, border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        self.add_paragraph(caption_text)
    def create_cover_page(self, analysis_target: str = "（分析対象未設定）") -> None:
        self.add_page()
        
        # PRADA風デザイン：エレガントな背景
        self.set_fill_color(240, 240, 240)  # ライトグレー
        self.rect(0, 0, A4_WIDTH, A4_HEIGHT, "F")
        
        # アクセントライン（上部）
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 0, A4_WIDTH, 8, "F")
        
        # ロゴの追加
        self.logo_renderer.add_logo_to_pdf(self, "cover")
        
        # タイトルブロック（中央配置）
        self.set_y(THEME["margins"]["top"] + THEME["spacing"]["xl"] * 2)
        
        # メインタイトル
        self.set_font(self.font_family, "B", THEME["font_sizes"]["title"])
        self.set_text_color(*COLOR_PRIMARY)
        self.multi_cell(0, THEME["spacing"]["lg"], "顧客インサイト分析レポート", 0, "C", wrapmode='CHAR')
        self.ln(THEME["spacing"]["md"])
        
        # サブタイトル
        self.set_font(self.font_family, "", THEME["font_sizes"]["h2"])
        self.set_text_color(*COLOR_TEXT)
        self.multi_cell(0, THEME["spacing"]["md"], f"分析対象：{analysis_target}", 0, "C", wrapmode='CHAR')
        self.ln(THEME["spacing"]["xl"])
        
        # 日付と装飾的な要素
        today = datetime.now().strftime("%Y年%m月%d日")
        self.set_font(self.font_family, "", THEME["font_sizes"]["h2"])
        self.set_text_color(128, 128, 128)  # グレー
        self.cell(0, THEME["spacing"]["md"], f"レポート作成日: {today}", border=0, align="C")
        
        # 下部の装飾ライン
        self.set_y(A4_HEIGHT - THEME["margins"]["bottom"] - 20)
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(50, A4_HEIGHT - THEME["margins"]["bottom"] - 15, A4_WIDTH - 100, 2, "F")

    def create_executive_summary_page(
        self,
        summary_text: str,
        key_insights: list[dict],
        business_impact: dict,
        data_quality_warning: dict | None = None,
        recommendations: list[str] | None = None,
    ) -> None:
        """エグゼクティブサマリーページを作成"""
        self.add_page()
        self.set_text_color(*COLOR_TEXT)
        self.set_left_margin(THEME["margins"]["left"])
        self.set_right_margin(THEME["margins"]["right"])
        self.set_top_margin(THEME["margins"]["top"])
        
        # タイトル
        self.add_heading("エグゼクティブサマリー", level="h1")
        self.ln(THEME["spacing"]["md"])
        
        # サマリーテキスト
        self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
        self.add_paragraph(summary_text)
        self.ln(THEME["spacing"]["lg"])
        
        # キーインサイト
        if key_insights:
            self.add_heading("主要な発見事項", level="h2")
            self.ln(THEME["spacing"]["sm"])
            
            for i, insight in enumerate(key_insights[:3], 1):
                # データ構造の互換性を確保（文字列または辞書の両方に対応）
                if isinstance(insight, dict):
                    insight_text = insight.get("text", f"インサイト {i}")
                else:
                    insight_text = str(insight)
                
                self.set_font(self.font_family, "B", THEME["font_sizes"].get("h3", 10))
                self.cell(
                    0, 
                    THEME["spacing"].get("md", 10), 
                    f"■ {insight_text}", 
                    border=0, 
                    align="L", 
                    new_x="LMARGIN", 
                    new_y="NEXT"
                )
                self.ln(THEME["spacing"].get("sm", 6))
        
        # ビジネスインパクト
        if business_impact:
            self.ln(THEME["spacing"]["md"])
            self.add_heading("ビジネスインパクト", level="h2")
            self.ln(THEME["spacing"]["sm"])
            
            for key, value in business_impact.items():
                self.set_font(self.font_family, "B", THEME["font_sizes"].get("h3", 10))
                self.cell(
                    0, 
                    THEME["spacing"].get("md", 10), 
                    f"• {key}: {value}", 
                    border=0, 
                    align="L", 
                    new_x="LMARGIN", 
                    new_y="NEXT"
                )
                self.ln(THEME["spacing"].get("sm", 6))
        
        # データ品質警告
        if data_quality_warning:
            self.ln(THEME["spacing"].get("md"))
            self.add_heading("データ品質に関する注意事項", level="h2")
            self.ln(THEME["spacing"].get("sm"))
            warning_text = data_quality_warning.get("message", "データ品質に関する注意事項があります。")
            self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
            self.add_paragraph(warning_text)

        # 推奨事項（存在すれば表示）
        if recommendations:
            self.ln(THEME["spacing"].get("md"))
            self.add_heading("推奨事項", level="h2")
            self.ln(THEME["spacing"].get("sm"))
            for i, rec in enumerate(recommendations[:5], 1):
                self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
                self.add_paragraph(f"{i}. {rec}")

    def create_strategic_recommendations_page(
        self,
        action_items: list[str],
        implementation_roadmap: list[dict],
        risk_assessment: dict,
        roi_analysis: dict
    ) -> None:
        """戦略的提言とアクションプランページを作成"""
        self.add_page()
        self.set_text_color(*COLOR_TEXT)
        self.set_left_margin(THEME["margins"]["left"])
        self.set_right_margin(THEME["margins"]["right"])
        self.set_top_margin(THEME["margins"]["top"])
        
        # タイトル
        self.add_heading("戦略的提言とアクションプラン", level="h1")
        self.ln(THEME["spacing"]["md"])
        
        # アクションアイテム
        if action_items:
            self.add_heading("推奨アクション", level="h2")
            self.ln(THEME["spacing"]["sm"])
            max_items = settings.MAX_ACTION_ITEMS
            action_items_to_display = action_items[:max_items]

            for i, item in enumerate(action_items_to_display, 1):
                priority_label = _determine_action_priority(i, max_items)
                self.set_text_color(*COLOR_TEXT if priority_label != "低" else COLOR_LIGHT_GRAY)
                self.set_font(self.font_family, "B", THEME["font_sizes"].get("h3", 10))
                self.cell(
                    0,
                    THEME["spacing"].get("md", 10),
                    f"{i}. [{priority_label}] {item}",
                    border=0,
                    align="L",
                    new_x="LMARGIN",
                    new_y="NEXT",
                )
                self.ln(THEME["spacing"].get("sm", 6))

            self.set_text_color(*COLOR_TEXT)
            if len(action_items) > max_items:
                self.set_font(self.font_family, "", THEME["font_sizes"].get("small", 8))
                self.set_text_color(*COLOR_LIGHT_GRAY)
                self.add_paragraph(
                    f"※最上位{max_items}件まで表示しています。残りの項目はExcel/レポート本文でご確認ください。"
                )
                self.set_text_color(*COLOR_TEXT)
        
        # 実装ロードマップ
        if implementation_roadmap:
            self.ln(THEME["spacing"]["md"])
            self.add_heading("実装ロードマップ", level="h2")
            self.ln(THEME["spacing"]["sm"])
            
            for roadmap in implementation_roadmap[:3]:
                phase = roadmap.get("phase", "フェーズ")
                description = roadmap.get("description", "説明")
                self.set_font(self.font_family, "B", THEME["font_sizes"].get("h3", 10))
                self.cell(
                    0, 
                    THEME["spacing"].get("md", 10), 
                    f"• {phase}: {description}", 
                    border=0, 
                    align="L", 
                    new_x="LMARGIN", 
                    new_y="NEXT"
                )
                self.ln(THEME["spacing"].get("sm", 6))
        
        # リスク評価
        if risk_assessment:
            self.ln(THEME["spacing"]["md"])
            self.add_heading("リスク評価", level="h2")
            self.ln(THEME["spacing"]["sm"])
            
            for risk, level in risk_assessment.items():
                self.set_font(self.font_family, "B", THEME["font_sizes"].get("h3", 10))
                self.cell(0, THEME["spacing"].get("md", 10), f"• {risk}: {level}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
                self.ln(THEME["spacing"].get("sm", 6))
        
        # ROI分析
        if roi_analysis:
            self.ln(THEME["spacing"]["md"])
            self.add_heading("ROI分析", level="h2")
            self.ln(THEME["spacing"]["sm"])
            
            for metric, value in roi_analysis.items():
                self.set_font(self.font_family, "B", THEME["font_sizes"].get("h3", 10))
                self.cell(0, THEME["spacing"].get("md", 10), f"• {metric}: {value}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
                self.ln(THEME["spacing"].get("sm", 6))

    def create_key_insights_page(self, key_insights: list[dict]) -> None:
        """キーインサイトページを作成する。"""
        if not key_insights:
            # キーインサイトがない場合のデフォルト表示
            self.add_page()
            self.set_text_color(*COLOR_TEXT)
            self.set_left_margin(THEME["margins"]["left"])
            self.set_right_margin(THEME["margins"]["right"])
            self.set_top_margin(THEME["margins"]["top"])
            
            self.add_heading("注目すべきポイント", level="h1")
            self.ln(THEME["spacing"]["md"])
            
            self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
            self.add_paragraph("詳細な分析結果から、以下の重要なポイントが明らかになりました：")
            self.ln(THEME["spacing"]["md"])
            
            # デフォルトのインサイトを表示
            default_insights = [
                "データの品質とサンプルサイズを考慮した解釈が必要です",
                "感情分析結果から顧客の満足度傾向を把握できます",
                "主要トピックの分析により改善点を特定できます"
            ]
            
            for i, insight in enumerate(default_insights, 1):
                self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
                self.cell(0, THEME["spacing"].get("md", 10), f"■ {i}. {insight}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
                self.ln(THEME["spacing"].get("sm", 6))
            return
            
        self.add_page()
        self.set_text_color(*COLOR_TEXT)
        self.set_left_margin(THEME["margins"]["left"])
        self.set_right_margin(THEME["margins"]["right"])
        self.set_top_margin(THEME["margins"]["top"])

        self.add_heading("注目すべき3つのポイント", level="h1")
        self.ln(THEME["spacing"]["md"])

        for i, insight in enumerate(key_insights, 1):
            # データ構造の互換性を確保（文字列または辞書の両方に対応）
            if isinstance(insight, dict):
                impact_level = insight.get("impact_level", "medium")
                title = insight.get("title", f"インサイト {i}")
                description = insight.get("description", "")
            else:
                impact_level = "medium"
                title = str(insight)
                description = ""
            
            # インパクトレベルに応じた色設定
            if impact_level == "high":
                self.set_text_color(220, 53, 69)  # 赤色
            elif impact_level == "medium":
                self.set_text_color(255, 193, 7)  # 黄色
            else:
                self.set_text_color(40, 167, 69)  # 緑色
            
            # タイトル
            self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
            self.cell(0, THEME["spacing"].get("md", 10), f"■ {i}. {title}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            
            # 説明
            self.set_text_color(*COLOR_TEXT)
            self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
            self.add_paragraph(description)
            
            # データ根拠
            if isinstance(insight, dict):
                data_evidence = insight.get('data_evidence', '')
            else:
                data_evidence = ''
            
            self.set_font(self.font_family, "B", THEME["font_sizes"].get("small", 8))
            self.cell(0, THEME["spacing"].get("sm", 6), f"データ根拠: {data_evidence}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            
            # 推奨アクション
            if isinstance(insight, dict):
                recommended_action = insight.get('recommended_action', '')
            else:
                recommended_action = ''
            
            self.set_font(self.font_family, "B", THEME["font_sizes"].get("small", 8))
            self.cell(0, THEME["spacing"].get("sm", 6), f"推奨アクション: {recommended_action}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            
            self.ln(THEME["spacing"].get("lg", 14))

    def create_summary_page(self, summary_text: str, action_items: list[str], data_quality_warning: dict | None = None) -> None:
        self.add_page()
        self.set_text_color(*COLOR_TEXT)
        self.set_left_margin(THEME["margins"]["left"])
        self.set_right_margin(THEME["margins"]["right"])
        self.set_top_margin(THEME["margins"]["top"])

        self.add_heading("エグゼクティブサマリー", level="h1")
        
        # データ品質警告の表示
        if data_quality_warning:
            quality_level = data_quality_warning.get("quality_level", "unknown")
            warning_message = data_quality_warning.get("warning_message", "")
            recommendations = data_quality_warning.get("recommendations", [])
            
            self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
            self.cell(0, THEME["spacing"].get("md", 10), "■ データ品質について", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            
            if quality_level == "low":
                self.set_text_color(220, 53, 69)  # 赤色
                self.add_paragraph(f"⚠️ 警告: {warning_message}")
            elif quality_level == "medium":
                self.set_text_color(255, 193, 7)  # 黄色
                self.add_paragraph(f"⚠️ 注意: {warning_message}")
            else:
                self.set_text_color(40, 167, 69)  # 緑色
                self.add_paragraph(f"✅ {warning_message}")
            
            self.set_text_color(*COLOR_TEXT)
            if recommendations:
                self.add_paragraph("推奨事項:")
                for rec in recommendations:
                    self.add_paragraph(f"・ {rec}")
            
            self.ln(THEME["spacing"].get("md", 10))

        self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
        self.cell(0, THEME["spacing"].get("md", 10), "■ 分析結果の総括", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        self.add_paragraph(summary_text)
        self.ln(THEME["spacing"].get("md", 10))

        self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
        self.cell(0, THEME["spacing"].get("md", 10), "■ 推奨されるネクストアクション", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        for item in action_items:
            self.add_paragraph(f"・ {item}")

    def create_chart_commentary_page(
        self,
        title: str,
        chart_base64: str,
        commentary_text: str,
        chart_width: int = 160,
        additional_insights: list[str] | None = None,
    ) -> None:
        self.add_page()
        self.add_chart_with_caption(
            title=title,
            chart_base64=chart_base64,
            caption_title="■ 分析からの示唆",
            caption_text=commentary_text,
            chart_width=chart_width,
        )
        if additional_insights:
            self.ln(THEME["spacing"].get("sm", 6))
            self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
            self.cell(0, THEME["spacing"].get("md", 10), "■ 追加インサイト", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
            for ins in additional_insights[:5]:
                self.add_paragraph(f"・{ins}")

    def create_appendix_page(self, topic_counts_df: pd.DataFrame) -> None:
        self.add_page()
        self.set_text_color(*COLOR_TEXT)
        self.add_heading("付録：データ詳細", level="h1")
        self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
        self.cell(0, THEME["spacing"].get("md", 10), "■ 全トピック一覧", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        headers = ["トピック", "出現回数"]
        rows = [[str(index), str(row.values[0])] for index, row in topic_counts_df.iterrows()]
        self.add_table(headers, rows, col_widths=[120, 40])

    def create_business_impact_page(self, business_impact: dict) -> None:
        """ビジネスインパクト分析ページを作成"""
        self.add_page()
        self.set_text_color(*COLOR_TEXT)
        
        # タイトル
        self.set_font(self.font_family, "B", THEME["font_sizes"]["h1"])
        self.cell(0, THEME["spacing"]["lg"], "ビジネスインパクト分析", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(THEME["spacing"]["sm"])
        
        # 優先度レベル
        priority_level = business_impact.get("priority_level", "medium")
        urgency_score = business_impact.get("urgency_score", 0.5)
        
        self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"])
        self.cell(0, THEME["spacing"]["md"], "■ 優先度評価", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_font(self.font_family, "", THEME["font_sizes"]["body"])
        self.cell(0, THEME["spacing"]["sm"], f"優先度レベル: {priority_level}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, THEME["spacing"]["sm"], f"緊急度スコア: {urgency_score:.1f}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(THEME["spacing"]["md"])
        
        # 推奨アクション
        recommended_actions = business_impact.get("recommended_actions", [])
        if recommended_actions:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"])
            self.cell(0, THEME["spacing"]["md"], "■ 推奨アクション", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"]["body"])
            for i, action in enumerate(recommended_actions, 1):
                self.cell(0, THEME["spacing"]["sm"], f"{i}. {action}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.ln(THEME["spacing"]["md"])
        
        # リスク要因
        risk_factors = business_impact.get("risk_factors", [])
        if risk_factors:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"])
            self.cell(0, THEME["spacing"]["md"], "■ リスク要因", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"]["body"])
            for i, risk in enumerate(risk_factors, 1):
                self.cell(0, THEME["spacing"]["sm"], f"{i}. {risk}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.ln(THEME["spacing"]["md"])
        
        # 機会領域
        opportunity_areas = business_impact.get("opportunity_areas", [])
        if opportunity_areas:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"])
            self.cell(0, THEME["spacing"]["md"], "■ 機会領域", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"]["body"])
            for i, opportunity in enumerate(opportunity_areas, 1):
                self.cell(0, THEME["spacing"]["sm"], f"{i}. {opportunity}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")

    def create_action_plan_page(self, action_plans: dict) -> None:
        """アクションプランページを作成"""
        self.add_page()
        self.set_text_color(*COLOR_TEXT)
        
        # タイトル
        self.set_font(self.font_family, "B", THEME["font_sizes"]["h1"])
        self.cell(0, THEME["spacing"]["lg"], "アクションプラン", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(THEME["spacing"]["sm"])
        
        # 即座のアクション
        immediate_actions = action_plans.get("immediate_actions", [])
        if immediate_actions:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"])
            self.cell(0, THEME["spacing"]["md"], "■ 即座のアクション", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"]["body"])
            for i, action in enumerate(immediate_actions, 1):
                self.cell(0, THEME["spacing"]["sm"], f"{i}. {action}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.ln(THEME["spacing"]["md"])
        
        # 短期アクション
        short_term_actions = action_plans.get("short_term_actions", [])
        if short_term_actions:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"])
            self.cell(0, THEME["spacing"]["md"], "■ 短期アクション", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"]["body"])
            for i, action in enumerate(short_term_actions, 1):
                self.cell(0, THEME["spacing"]["sm"], f"{i}. {action}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.ln(THEME["spacing"]["md"])
        
        # 長期アクション
        long_term_actions = action_plans.get("long_term_actions", [])
        if long_term_actions:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"])
            self.cell(0, THEME["spacing"]["md"], "■ 長期アクション", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"]["body"])
            for i, action in enumerate(long_term_actions, 1):
                self.cell(0, THEME["spacing"]["sm"], f"{i}. {action}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.ln(THEME["spacing"]["md"])
        
        # 成功指標
        success_metrics = action_plans.get("success_metrics", [])
        if success_metrics:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"])
            self.cell(0, THEME["spacing"]["md"], "■ 成功指標", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"]["body"])
            for i, metric in enumerate(success_metrics, 1):
                self.cell(0, THEME["spacing"]["sm"], f"{i}. {metric}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")

    def create_success_stories_page(self, success_examples: list[dict], success_factors: dict | None = None) -> None:
        """成功事例ページを作成する。

        Args:
            success_examples: [{respondent_id, question, quote, sentiment, joy, topics, factors}]
            success_factors: {factor: count}
        """
        if not success_examples:
            return

        self.add_page()
        self.set_text_color(*COLOR_TEXT)
        self.add_heading("成功事例（代表例）", level="h1")
        self.ln(THEME["spacing"].get("sm", 6))

        # 成功要因のサマリー（上部）
        if success_factors:
            self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
            self.cell(0, THEME["spacing"].get("md", 10), "■ 成功要因（Top）", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            rows = [[k, str(v)] for k, v in list(success_factors.items())[:8]]
            if rows:
                self.add_table(["要因", "件数"], rows, col_widths=[100, 30])
            self.ln(THEME["spacing"].get("sm", 6))

        # 代表的な成功事例
        for i, ex in enumerate(success_examples[:5], 1):
            self.set_font(self.font_family, "B", THEME["font_sizes"].get("h2", 12))
            self.cell(0, THEME["spacing"].get("md", 10), f"■ 事例 {i}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.set_font(self.font_family, "", THEME["font_sizes"].get("body", 10))
            rid = ex.get("respondent_id")
            q = ex.get("question")
            meta = []
            if rid:
                meta.append(f"回答者: {rid}")
            if q:
                meta.append(f"設問: {q}")
            if meta:
                self.add_paragraph(" / ".join(meta))
            self.add_paragraph(f"引用: {str(ex.get('quote') or '')}")
            topics = ex.get("topics") or []
            factors = ex.get("factors") or []
            if topics:
                self.add_paragraph("トピック: " + ", ".join(topics[:5]))
            if factors:
                self.add_paragraph("成功要因: " + ", ".join(factors[:5]))
            self.ln(THEME["spacing"].get("sm", 6))

    def create_wordcloud_page(self, pos_wc: str | None, neg_wc: str | None) -> None:
        """Add a page containing positive and negative word cloud images."""
        if not (pos_wc or neg_wc):
            return

        self.add_page()
        self.set_text_color(*COLOR_TEXT)

        self.set_font(self.font_family, "B", THEME["font_sizes"]["h1"]) 
        self.cell(0, THEME["spacing"]["lg"], "ワードクラウド", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(THEME["spacing"]["sm"]) 

        if pos_wc:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"]) 
            self.cell(0, THEME["spacing"]["md"], "ポジティブ", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.image(pos_wc, x=(A4_WIDTH - 160) / 2, w=160)
            self.ln(THEME["spacing"]["md"]) 

        if neg_wc:
            self.set_font(self.font_family, "B", THEME["font_sizes"]["h2"]) 
            self.cell(0, THEME["spacing"]["md"], "ネガティブ", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            self.image(neg_wc, x=(A4_WIDTH - 160) / 2, w=160)


# --- Entry point ------------------------------------------------------------


def generate_high_quality_pdf_report(summary_data: dict, output_path: str, *, font_regular: Path | None = None, font_bold: Path | None = None, survey_type: str = "customer_satisfaction"):
    """
    高品質なPDFレポートを生成する（既存レポートより高品質）。
    日本語フォント（同梱NotoSansJP）を正しく登録。
    エラーハンドリングを強化し、詳細なエラー情報を提供。
    
    特徴:
    - 8ページ構成の詳細レポート
    - 高解像度チャートとグラフ
    - プロフェッショナルなデザイン
    - 詳細な分析とインサイト
    """
    try:
        # 入力データの検証
        if not isinstance(summary_data, dict):
            raise ValueError("summary_dataは辞書型である必要があります")
        
        if not output_path or not isinstance(output_path, str):
            raise ValueError("output_pathは有効な文字列である必要があります")
        
        # 高品質レポート用のデフォルト補完
        defaults_text = {
            "sentiment_commentary": "感情分析により、顧客の心理状態と満足度の深層を解明しました。ポジティブな感情は顧客満足度の向上を示し、ネガティブな感情は改善の機会を特定します。",
            "topics_commentary": "トピック分析により、顧客の関心事項と課題を明確化しました。主要トピックの傾向分析から、戦略的な改善方向性を導出できます。",
            "marketing_perspective": "マーケティング視点から、顧客の声を市場機会と課題に変換しました。競合優位性の確保と顧客価値の向上に向けた具体的な施策を提案します。",
            "user_perspective": "ユーザー視点から、顧客の真のニーズと期待を分析しました。ユーザーエクスペリエンスの向上と顧客満足度の最大化に向けた改善点を特定します。",
            "consultant_perspective": "コンサルタント視点から、データに基づく戦略的提言を提供します。組織の成長と競争力強化に向けた実行可能なアクションプランを策定しました。",
            "action_items": ["顧客満足度の向上に向けた具体的な改善施策を実施する", "データに基づく戦略的提言を組織全体で共有する", "継続的な顧客フィードバック収集システムを構築する"],
        }
        
        # プロンプト断片を検出するキーワード
        prompt_keywords = [
            "system:", "user:", "assistant:", "role:", "content:", "messages:",
            "You are a strict JSON generator", "Return ONLY a JSON object",
            "Use English keys only", "No explanations", "No extra keys",
            "temperature:", "model:", "response_format:", "schema:", "properties:",
            "type:", "description:", "enum:", "items:", "required:", "additionalProperties:",
            "Error occurred", "An error", "Exception", "Traceback", "ValueError", "TypeError"
        ]
        
        for key, default_val in defaults_text.items():
            val = summary_data.get(key)
            if not isinstance(val, str) or not val.strip():
                summary_data[key] = default_val
            else:
                val_lower = val.lower()
                if any(keyword in val_lower for keyword in prompt_keywords):
                    print(f"プロンプト断片を検出: {key}")
                    summary_data[key] = default_val

        # 厳密バリデーション
        _validate_summary_for_pdf(summary_data)
        
    except Exception as e:
        error_msg = f"PDF生成前のデータ検証でエラーが発生しました: {e}\n"
        error_msg += f"入力データ: {type(summary_data)} - {summary_data}\n"
        error_msg += f"出力パス: {output_path}\n"
        error_msg += f"調査タイプ: {survey_type}\n"
        print(error_msg)
        raise

    try:
        pdf = ReportPDF()
        pdf.setup_fonts()
        pdf.set_auto_page_break(auto=True, margin=15)

        # アンケート形態に応じたタイトル設定
        survey_type_names = {
            "customer_satisfaction": "顧客満足度調査レポート",
            "market_research": "市場調査レポート", 
            "employee_satisfaction": "従業員満足度調査レポート",
            "brand_research": "ブランド調査レポート",
            "public_opinion": "世論調査レポート"
        }
        
        report_title = survey_type_names.get(survey_type, "アンケート調査レポート")
        
        # ページ1: 表紙（高品質デザイン）
        pdf.create_cover_page(analysis_target=summary_data.get("analysis_target", report_title))

        # ページ2: エグゼクティブサマリー（詳細版）
        pdf.create_executive_summary_page(
            summary_text=summary_data.get("summary_text", summary_data.get("executive_summary", "総括テキストがありません。")),
            key_insights=summary_data.get("key_insights", []),
            business_impact=summary_data.get("business_impact", {}),
            recommendations=summary_data.get("recommendations", [])
        )

        # ページ3: 主要インサイト（詳細分析付き）
        key_insights = summary_data.get("key_insights", [])
        pdf.create_key_insights_page(key_insights)

        # ページ4: 戦略的提言とアクションプラン（実行可能版）
        pdf.create_strategic_recommendations_page(
            action_items=summary_data.get("action_items", ["アクションアイテムがありません。"]),
            implementation_roadmap=summary_data.get("implementation_roadmap", []),
            risk_assessment=summary_data.get("risk_assessment", {}),
            roi_analysis=summary_data.get("roi_analysis", {})
        )

        # ページ5: 感情分析詳細（高解像度チャート付き）
        emotion_chart = create_emotion_analysis_chart_base64(summary_data.get("emotion_avg", {}))
        pdf.create_chart_commentary_page(
            title="分析詳細①：感情分析（一次感情）",
            chart_base64=emotion_chart,
            commentary_text=summary_data.get("emotion_commentary", ""),
            additional_insights=summary_data.get("emotion_insights", [])
        )

        # ページ6: ビジネスインパクト分析（定量化版）
        pdf.create_business_impact_page(summary_data.get("business_impact", {}))
        
        # ページ7: アクションプラン（実行可能版）
        pdf.create_action_plan_page(summary_data.get("action_plans", {}))

        # 冗長ページ（分析詳細②・付録）は生成しない（要件により削除）

        # 追加ページ: 成功事例（存在する場合）
        success_examples = summary_data.get("success_examples")
        success_factors = summary_data.get("success_factors")
        if isinstance(success_examples, list) and success_examples:
            pdf.create_success_stories_page(success_examples, success_factors)

        # 追加ページ: アンケート形態に応じたペルソナ視点（詳細版）
        perspective_texts = {
            "marketing_perspective": summary_data.get("marketing_perspective", ""),
            "user_perspective": summary_data.get("user_perspective", ""),
            "consultant_perspective": summary_data.get("consultant_perspective", "")
        }
        pdf.add_perspective_pages(perspective_texts, survey_type)

        # PDFファイルを出力
        pdf.output(output_path)
        print(f"高品質PDFレポートが '{output_path}' として生成されました。")
        
    except FileNotFoundError as e:
        error_msg = f"フォントファイルが見つかりません: {e}\n"
        error_msg += f"フォントパス: {font_regular}, {font_bold}\n"
        error_msg += "解決方法:\n"
        error_msg += "1. フォントファイルの存在を確認してください\n"
        error_msg += "2. フォントファイルのパスが正しいか確認してください\n"
        print(error_msg)
        raise
        
    except PermissionError as e:
        error_msg = f"PDFファイルの書き込み権限がありません: {e}\n"
        error_msg += f"出力先: {output_path}\n"
        error_msg += "解決方法:\n"
        error_msg += "1. 出力先ディレクトリの書き込み権限を確認してください\n"
        error_msg += "2. ファイルが他のアプリケーションで開かれていないか確認してください\n"
        print(error_msg)
        raise
        
    except Exception as e:
        error_msg = f"PDF生成中にエラーが発生しました: {e}\n"
        error_msg += f"エラータイプ: {type(e).__name__}\n"
        error_msg += f"出力先: {output_path}\n"
        error_msg += f"調査タイプ: {survey_type}\n"
        print(error_msg)
        raise


def generate_pdf_report(summary_data: dict, output_path: str, *, font_regular: Path | None = None, font_bold: Path | None = None, survey_type: str = "customer_satisfaction"):
    """
    分析データから新しいデザインのPDFレポートを生成する。
    日本語フォント（同梱NotoSansJP）を正しく登録。
    エラーハンドリングを強化し、詳細なエラー情報を提供。
    
    【重要】この関数は堅牢なPDF生成システムに置き換えられました。
    エラーが発生した場合は、robust_pdf_generator.pyのgenerate_robust_pdf_report()を使用してください。
    """
    try:
        # 入力データの検証
        if not isinstance(summary_data, dict):
            raise ValueError("summary_dataは辞書型である必要があります")
        
        if not output_path or not isinstance(output_path, str):
            raise ValueError("output_pathは有効な文字列である必要があります")
        
        # 不足フィールドのデフォルト補完（テストや最小入力でも通すため）
        defaults_text = {
            "sentiment_commentary": "感情分析の詳細な解説が生成されませんでした。データの品質とサンプルサイズを考慮して解釈してください。",
            "topics_commentary": "トピック分析の詳細な解説が生成されませんでした。主要なトピックの傾向を注意深く観察してください。",
            "marketing_perspective": "マーケティング視点の分析が生成されませんでした。データから読み取れる市場機会と課題を検討してください。",
            "user_perspective": "ユーザー視点の分析が生成されませんでした。顧客の声から改善点を特定してください。",
            "consultant_perspective": "コンサルタント視点の分析が生成されませんでした。戦略的な改善提案を検討してください。",
        }
        # プロンプト断片を検出するキーワード（根本原因調査のため一時的に緩和）
        prompt_keywords = [
            # システムメッセージ系（確実にプロンプト断片）
            "system:", "user:", "assistant:", "role:", "content:", "messages:",
            # JSON生成指示系（確実にプロンプト断片）
            "You are a strict JSON generator", "Return ONLY a JSON object",
            "Use English keys only", "No explanations", "No extra keys",
            # APIパラメータ系（確実にプロンプト断片）
            "temperature:", "model:", "response_format:", "schema:", "properties:",
            "type:", "description:", "enum:", "items:", "required:", "additionalProperties:",
            # エラーメッセージ系（確実にエラー）
            "Error occurred", "An error", "Exception", "Traceback", "ValueError", "TypeError"
        ]
        
        for key, default_val in defaults_text.items():
            val = summary_data.get(key)
            if not isinstance(val, str) or not val.strip():
                summary_data[key] = default_val
            else:
                # プロンプト断片が含まれているかチェック
                val_lower = val.lower()
                if any(keyword in val_lower for keyword in prompt_keywords):
                    print(f"プロンプト断片を検出: {key}")
                    summary_data[key] = default_val

        # action_items が未設定/空の場合はプレースホルダーを挿入
        ai = summary_data.get("action_items")
        if not isinstance(ai, list) or not any(str(i).strip() for i in ai):
            summary_data["action_items"] = ["データ分析に基づく具体的なアクションアイテムを検討してください"]

        # データ検証（簡素化）
        # 事前サニタイズ（モデルがプロンプト断片を返した場合の保護）
        _sanitize_summary_text_fields(summary_data)
        # 厳密バリデーション：不正なら即エラーを送出
        _validate_summary_for_pdf(summary_data)
        
    except Exception as e:
        error_msg = f"PDF生成前のデータ検証でエラーが発生しました: {e}\n"
        error_msg += f"入力データ: {type(summary_data)} - {summary_data}\n"
        error_msg += f"出力パス: {output_path}\n"
        error_msg += f"調査タイプ: {survey_type}\n"
        error_msg += f"デバッグ情報: 必須フィールドの確認を実行してください"
        raise ValueError(error_msg) from e

    try:
        pdf = ReportPDF()
        # フォント登録（明確に検証）
        pdf.setup_fonts()
        pdf.set_auto_page_break(auto=True, margin=15)

        # アンケート形態に応じたタイトル設定
        survey_type_names = {
            "customer_satisfaction": "顧客満足度調査レポート",
            "market_research": "市場調査レポート", 
            "employee_satisfaction": "従業員満足度調査レポート",
            "brand_research": "ブランド調査レポート",
            "public_opinion": "世論調査レポート"
        }
        
        report_title = survey_type_names.get(survey_type, "アンケート調査レポート")
        
        # ページ1: 表紙（ReportPDFは create_cover_page を使用）
        pdf.create_cover_page(analysis_target=summary_data.get("analysis_target", report_title))

        # ページ2: エグゼクティブサマリー（PWC要件に適合）
        pdf.create_executive_summary_page(
            summary_text=summary_data.get("summary_text", summary_data.get("executive_summary", "総括テキストがありません。")),
            key_insights=summary_data.get("key_insights", []),
            business_impact=summary_data.get("business_impact", {}),
            data_quality_warning=summary_data.get("data_quality_warning")
        )

        # ページ3: 注目すべき3つのポイント
        key_insights = summary_data.get("key_insights", [])
        pdf.create_key_insights_page(key_insights)

        # ページ4: 戦略的提言とアクションプラン
        pdf.create_strategic_recommendations_page(
            action_items=summary_data.get("action_items", ["アクションアイテムがありません。"]),
            implementation_roadmap=summary_data.get("implementation_roadmap", []),
            risk_assessment=summary_data.get("risk_assessment", {}),
            roi_analysis=summary_data.get("roi_analysis", {})
        )

        # ページ4: 感情分析（一次感情）
        emotion_chart = create_emotion_analysis_chart_base64(summary_data.get("emotion_avg", {}))
        pdf.create_chart_commentary_page(
            title="分析詳細①：感情分析（一次感情）",
            chart_base64=emotion_chart,
            commentary_text=summary_data.get("emotion_commentary", ""),
            chart_width=THEME.get("charts", {}).get("emotionWidth", 160)
        )
        
        # ページ5: ビジネスインパクト分析
        pdf.create_business_impact_page(summary_data.get("business_impact", {}))
        
        # ページ6: アクションプラン
        pdf.create_action_plan_page(summary_data.get("action_plans", {}))

        # 追加ページ: 成功事例（存在する場合のみ）
        success_examples = summary_data.get("success_examples")
        success_factors = summary_data.get("success_factors")
        if isinstance(success_examples, list) and success_examples:
            pdf.create_success_stories_page(success_examples, success_factors)

        # 冗長ページ（分析詳細②・付録）は生成しない（要件により削除）

        # 追加ページ: アンケート形態に応じたペルソナ視点
        perspective_texts = {
            "marketing_perspective": summary_data.get("marketing_perspective"),
            "user_perspective": summary_data.get("user_perspective"),
            "consultant_perspective": summary_data.get("consultant_perspective"),
        }
        pdf.add_perspective_pages(perspective_texts, survey_type)

        # PDFファイルを出力
        pdf.output(output_path)
        print(f"新しいデザインのPDFレポートが '{output_path}' として生成されました。")
        
    except FileNotFoundError as e:
        error_msg = f"フォントファイルが見つかりません: {e}\n"
        error_msg += "解決方法:\n"
        error_msg += "1. 'coding/survey_analysis_mvp/fonts' フォルダに NotoSansJP-Regular.ttf を配置してください\n"
        error_msg += "2. フォントファイルの権限を確認してください\n"
        error_msg += "3. アプリケーションを管理者権限で実行してみてください"
        raise FileNotFoundError(error_msg) from e
        
    except PermissionError as e:
        error_msg = f"PDFファイルの書き込み権限がありません: {e}\n"
        error_msg += f"出力先: {output_path}\n"
        error_msg += "解決方法:\n"
        error_msg += "1. 出力先ディレクトリの書き込み権限を確認してください\n"
        error_msg += "2. ファイルが他のアプリケーションで開かれていないか確認してください\n"
        error_msg += "3. 管理者権限で実行してみてください"
        raise PermissionError(error_msg) from e
        
    except Exception as e:
        error_msg = f"PDF生成中にエラーが発生しました: {e}\n"
        error_msg += f"エラータイプ: {type(e).__name__}\n"
        error_msg += f"出力先: {output_path}\n"
        error_msg += f"調査タイプ: {survey_type}\n"
        error_msg += f"作業ディレクトリ: {os.getcwd()}\n"
        error_msg += f"Python実行パス: {sys.executable}"
        raise RuntimeError(error_msg) from e


def generate_wordcloud(words: list[str], output_path: str, exclude_words: list[str] | None = None) -> None:
    """Generate and save a word cloud image with timeout and error handling."""
    if not words:
        print("ワードクラウドを生成するための単語がありません。")
        return
    
    # 除外ワードの適用（完全一致・前後空白無視）
    if exclude_words:
        excluded = {str(w).strip() for w in exclude_words if str(w).strip()}
        words = [w for w in words if (str(w).strip() and str(w).strip() not in excluded)]
        if not words:
            print("除外語の適用後、ワードクラウド用の単語がありません。")
            return

    try:
        # Matplotlib/WordCloud用フォント
        reg, _ = get_font_paths()

        # Windows対応: signal.SIGALRMは使用しない
        import threading
        import time
        
        def generate_wordcloud():
            try:
                # 単語リストの前処理
                processed_words = [str(w).strip() for w in words if str(w).strip()]
                if not processed_words:
                    print("処理可能な単語がありません。")
                    return False
                
                # 単語の頻度を計算
                from collections import Counter
                word_freq = Counter(processed_words)
                
                # 頻度フィルタリングを大幅緩和（名詞のみなので）
                # 出力パス名に "_all" が含まれる場合はより多くの語を残す
                is_all = "_all" in os.path.basename(output_path)
                base_divisor = 100 if is_all else 80  # 大幅緩和
                min_freq = max(1, len(processed_words) // base_divisor)
                filtered_words = {word: freq for word, freq in word_freq.items() if freq >= min_freq}
                
                # フィルタリング後も単語が少ない場合は、さらに緩和
                if len(filtered_words) < 20:
                    min_freq = 1  # 最低頻度を1に設定
                    filtered_words = {word: freq for word, freq in word_freq.items() if freq >= min_freq}
                
                if not filtered_words:
                    print("頻度フィルタリング後、単語が残りませんでした。")
                    return False
                
                # 最小単語数保証（各カテゴリで十分な単語数を確保）
                min_words_required = 50 if is_all else 30
                if len(filtered_words) < min_words_required:
                    category_name = "ALL" if is_all else "POSITIVE/NEGATIVE"
                    print(f"警告: {category_name}の単語数が不足しています（{len(filtered_words)}語 < {min_words_required}語）")
                    # 不足分を補完（重複を避けて追加）
                    all_available_words = list(word_freq.keys())
                    additional_words = {word: 1 for word in all_available_words 
                                      if word not in filtered_words and len(word) >= 2}
                    filtered_words.update(additional_words)
                    print(f"補完後: {len(filtered_words)}語")
                
                # WordCloud生成（文字サイズの差を大幅に拡大）
                wc = WordCloud(
                    width=1200,  # キャンバスサイズをさらに拡大
                    height=600,  # キャンバスサイズをさらに拡大
                    background_color="white",
                    font_path=str(reg) if reg and reg.exists() else None,
                    collocations=False,
                    max_words=min(250 if is_all else 150, len(filtered_words)),  # 単語数を減らして各単語を大きく
                    relative_scaling=0.3,  # 文字サイズコントラストを大幅強化（0.3は非常に強い差）
                    min_font_size=8,  # 最小フォントサイズを上げて可読性向上
                    max_font_size=150,  # 最大フォントサイズを大幅拡大
                    prefer_horizontal=0.9,  # 水平配置を強化
                    colormap='plasma',  # より鮮明なカラーマップ
                    font_step=2,  # フォントステップを大きくして差を強調
                    margin=3,  # マージンを調整
                    scale=2  # 全体のスケールを上げて鮮明度向上
                ).generate_from_frequencies(filtered_words)

                # 画像が空でないかチェック
                import numpy as np
                if np.sum(wc.to_array()) == 0:
                    print("生成されたWordCloudが空です。")
                    return False

                # 高解像度で画像保存（DPIを上げて鮮明度向上）
                wc.to_file(output_path)
                print(f"ワードクラウドが '{output_path}' として保存されました。")
                print(f"単語数: {len(filtered_words)}, 最大頻度: {max(filtered_words.values()) if filtered_words else 0}, 最小頻度: {min(filtered_words.values()) if filtered_words else 0}")
                return True
            except Exception as e:
                print(f"ワードクラウド生成エラー: {e}")
                return False
        
        # タイムアウト付きでWordCloud生成（Windows対応）
        result = [False]
        def run_with_timeout():
            result[0] = generate_wordcloud()
        
        thread = threading.Thread(target=run_with_timeout)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)  # 30秒に延長（日本語フォント/語数多で時間がかかるため）
        
        if thread.is_alive():
            print("ワードクラウド生成がタイムアウトしました")
            result[0] = False
            
    except TimeoutError:
        print(f"ワードクラウド生成がタイムアウトしました: {output_path}")
        # 空の画像を作成
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "ワードクラウド生成タイムアウト", ha='center', va='center', fontsize=16, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.savefig(output_path, bbox_inches='tight', dpi=150, facecolor='white', edgecolor='none')
        plt.close(fig)
    except Exception as e:
        print(f"ワードクラウド生成エラー: {e}")
        # より詳細なエラー情報を含む画像を作成
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f"ワードクラウド生成エラー\n{str(e)[:50]}...", ha='center', va='center', fontsize=12, color='red')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.savefig(output_path, bbox_inches='tight', dpi=150, facecolor='white', edgecolor='none')
        plt.close(fig)


def create_report(
    df: pd.DataFrame,
    positive_summary: str,
    negative_summary: str,
    wordcloud_type: str,
    column_name: str,
    commentary: ReportCommentary | None = None,
) -> None:
    """Generate charts, word clouds and a PDF report from survey data.

    If ``commentary`` is provided it overrides the ``summary_text`` and
    ``action_items`` derived from the separate summaries. When both summaries are
    empty and no commentary is given, commentary is generated automatically using
    :func:`generate_report_commentary`.
    """

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # --- Sentiment chart -------------------------------------------------
    counts = (
        df["sentiment"]
        .value_counts()
        .reindex(["positive", "neutral", "negative"], fill_value=0)
    )
    chart_base64 = create_sentiment_pie_chart_base64(counts)
    if chart_base64:
        chart_path = os.path.join(output_dir, "sentiment_chart.png")
        with open(chart_path, "wb") as f:
            f.write(base64.b64decode(chart_base64))

    # --- Word cloud ------------------------------------------------------
    if wordcloud_type == "normal":
        texts = df[column_name].dropna().astype(str).tolist()
        words = tokenize_texts(texts, allowed_pos=["名詞"])  # 名詞のみ
        wc_path = os.path.join(output_dir, "wordcloud.png")
        generate_wordcloud(words, wc_path, [])
        pos_wc = neg_wc = wc_path
    else:
        pos_texts = (
            df[df["sentiment"].isin(["positive", "neutral"])][column_name]
            .dropna()
            .astype(str)
            .tolist()
        )
        neg_texts = (
            df[df["sentiment"].isin(["negative", "neutral"])][column_name]
            .dropna()
            .astype(str)
            .tolist()
        )
        pos_wc = os.path.join(output_dir, "positive_wordcloud.png")
        neg_wc = os.path.join(output_dir, "negative_wordcloud.png")
        generate_wordcloud(tokenize_texts(pos_texts, allowed_pos=["名詞"]), pos_wc, [])
        generate_wordcloud(tokenize_texts(neg_texts, allowed_pos=["名詞"]), neg_wc, [])

    # --- PDF report ------------------------------------------------------
    # Aggregate topic counts for optional commentary generation
    all_topics: list[str] = []
    if "analysis_key_topics" in df.columns:
        for topics in df["analysis_key_topics"]:
            if isinstance(topics, list):
                all_topics.extend(topics)
    topic_counts = pd.Series(all_topics).value_counts()

    if commentary is None and not (
        positive_summary.strip() or negative_summary.strip()
    ):
        try:
            commentary = asyncio.run(
                generate_report_commentary(
                    {
                        "sentiment_counts": counts,
                        "topic_counts": topic_counts.head(15),
                    }
                )
            )
        except Exception:
            commentary = None

    if commentary is not None:
        summary_text = commentary.summary_text
        action_items = commentary.action_items
        sentiment_commentary = commentary.sentiment_commentary
        topics_commentary = commentary.topics_commentary
    else:
        summary_text = "\n\n".join(
            s.strip() for s in [positive_summary, negative_summary] if s.strip()
        )
        action_items = [
            line.strip("・- ") for line in negative_summary.splitlines() if line.strip()
        ]
        sentiment_commentary = ""
        topics_commentary = ""

    summary = {
        "analysis_target": f"「{column_name}」列の回答",
        "summary_text": summary_text,
        "action_items": action_items or ["アクションアイテムがありません。"],
        "sentiment_counts": counts,
        "topic_counts": topic_counts.head(15),
        "pos_wc": pos_wc,
        "neg_wc": neg_wc,
    }
    if commentary is not None:
        summary["sentiment_commentary"] = sentiment_commentary
        summary["topics_commentary"] = topics_commentary
    elif chart_base64:
        summary["sentiment_commentary"] = ""
    generate_pdf_report(
        summary,
        os.path.join(output_dir, "survey_report.pdf"),
    )


# --- Helpers for text validation ---------------------------------------------

def _clean_minor_issues(text: str) -> str:
    """軽微な問題をクリーニング（エラーにはしない）"""
    minor_markers = (
        "視点：",
        "専門領域：",
        "注目領域：",
        "重要KPI：",
    )
    
    cleaned = text
    for marker in minor_markers:
        # 見出し行を除去
        cleaned = re.sub(f'^{marker}.*?\n', '', cleaned, flags=re.MULTILINE)
        # 文中の見出しを除去
        cleaned = re.sub(f'{marker}[^\n]*', '', cleaned)
    
    return cleaned.strip()


def _validate_summary_for_pdf(summary_data: dict) -> None:
    """PDFに描画するテキストが有効かを厳密チェックし、問題があれば例外を送出する。
    - 必須フィールドが空/非文字列の場合エラー
    - プロンプト/エラーメッセージ風の断片が含まれている場合もエラー
    """
    # 必須フィールドのデフォルト値設定
    default_values = {
        "summary_text": "アンケート分析結果の詳細な要約を生成中です。",
        "sentiment_commentary": "感情分析の詳細な解説が生成されませんでした。データの品質とサンプルサイズを考慮して解釈してください。",
        "topics_commentary": "トピック分析の詳細な解説が生成されませんでした。主要なトピックの傾向を注意深く観察してください。",
        "marketing_perspective": "マーケティング視点の分析が生成されませんでした。データから読み取れる市場機会と課題を検討してください。",
        "user_perspective": "ユーザー視点の分析が生成されませんでした。顧客の声から改善点を特定してください。",
        "consultant_perspective": "コンサルタント視点の分析が生成されませんでした。戦略的な改善提案を検討してください。",
    }
    
    for key, default_value in default_values.items():
        if key not in summary_data or not summary_data[key] or summary_data[key].strip() == "":
            summary_data[key] = default_value
    
    required_text_keys = (
        "summary_text",
        "sentiment_commentary",
        "topics_commentary",
        "marketing_perspective",
        "user_perspective",
        "consultant_perspective",
    )
    forbidden_markers = (
        # システムメッセージ系
        "system:",
        "user:",
        "assistant:",
        "role:",
        "content:",
        "messages:",
        # APIパラメータ系
        "temperature:",
        "model:",
        "response_format:",
        "schema:",
        "properties:",
        "type:",
        "description:",
        "enum:",
        "items:",
        "required:",
        "additionalProperties:",
        # エラーメッセージ系
        "Error occurred",
        "An error",
        "Exception",
        "Traceback",
        "ValueError",
        "TypeError",
        "AttributeError",
        "KeyError",
        "IndexError",
        "ImportError",
        "ModuleNotFoundError",
        "FileNotFoundError",
        "PermissionError",
        "OSError",
        "ConnectionError",
        "TimeoutError",
        "RuntimeError",
        # プロンプト断片系
        "You are a strict JSON generator",
        "Return ONLY a JSON object",
        "Use English keys only",
        "No explanations",
        "No extra keys",
        # 重大なプロンプト断片（エラーとする）
        # 軽微な問題は後でクリーニング
    )
    errors: list[str] = []

    for key in required_text_keys:
        value = summary_data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} が空です。LLM生成に失敗している可能性があります。")
            continue
        
        # 軽微な問題をクリーニング（エラーにはしない）
        cleaned_value = _clean_minor_issues(value)
        summary_data[key] = cleaned_value
        
        # 重大な問題のみエラーとする
        lowered = cleaned_value.strip().lower()
        if any(marker.lower() in lowered for marker in forbidden_markers):
            errors.append(f"{key} に重大なプロンプト/エラー文の断片が含まれています。生成処理を見直してください。")

    # 任意: アクションアイテムの簡易チェック
    action_items = summary_data.get("action_items")
    if not isinstance(action_items, list) or not any(str(i).strip() for i in action_items):
        errors.append("action_items が空です。")

    if errors:
        raise ValueError("PDF生成に必要な解説文が未生成または不正です:\n- " + "\n- ".join(errors))


def _sanitize_summary_text_fields(summary_data: dict) -> None:
    """軽微な問題をクリーニング（エラーにはしない）"""
    targets = (
        "summary_text",
        "sentiment_commentary",
        "topics_commentary",
        "marketing_perspective",
        "user_perspective",
        "consultant_perspective",
    )
    for key in targets:
        val = summary_data.get(key)
        if isinstance(val, str) and val:
            # 軽微な問題をクリーニング
            cleaned = _clean_minor_issues(val)
            summary_data[key] = cleaned


def _build_html_report_data(analysis_results: dict) -> dict:
    """分析結果からHTML+CSS PDF用のサマリを構築"""
    from datetime import datetime
    from core.evidence_pipeline import aggregate_legal_check_results, generate_deep_dive_summary

    integrated = analysis_results.get("integrated_results", {}) or {}
    aio_results = analysis_results.get("aio_results", {}) or {}
    legal_checks = analysis_results.get("legal_checks", {}) or {}

    aggregated = aggregate_legal_check_results(legal_checks) if isinstance(legal_checks, dict) else {}
    deep_summary = generate_deep_dive_summary(aggregated) if isinstance(aggregated, dict) else {}
    top_clusters = (deep_summary.get("high_priority") or []) + (deep_summary.get("medium_priority") or [])
    top_issues = []
    for cluster in top_clusters[:5]:
        rep = cluster.get("representative", {}) or {}
        title = (
            rep.get("title")
            or rep.get("issue")
            or rep.get("matched_text")
            or rep.get("detail")
            or cluster.get("category")
            or "問題"
        )
        top_issues.append(
            {
                "title": title[:80],
                "severity": cluster.get("severity", "info"),
            }
        )

    crawl_strategy = analysis_results.get("crawl_strategy") or {}
    crawl_data = None
    if isinstance(crawl_strategy, dict) and crawl_strategy:
        crawl_data = {
            "link_count": crawl_strategy.get("link_count"),
            "depth": crawl_strategy.get("depth"),
            "reason": crawl_strategy.get("reason") or crawl_strategy.get("description"),
            "priority_pages": crawl_strategy.get("priority_pages") or [],
        }

    schema_validation = (aio_results.get("schema_validation") or {}) if isinstance(aio_results, dict) else {}
    content_gap = (aio_results.get("content_schema_gap") or {}) if isinstance(aio_results, dict) else {}

    gap_items = []
    for gap in (content_gap.get("gaps") or [])[:5]:
        claim = gap.get("content_claim") or ""
        missing = gap.get("missing_in_schema") or ""
        if claim or missing:
            gap_items.append(f"{claim} -> {missing}".strip())

    internal_link_summary = analysis_results.get("internal_link_summary") or {}
    internal_links = None
    if isinstance(internal_link_summary, dict) and internal_link_summary:
        internal_links = {
            "total_pages": internal_link_summary.get("total_pages", 0),
            "total_internal_links": internal_link_summary.get("total_internal_links", 0),
            "orphan_count": internal_link_summary.get("orphan_count", 0),
            "low_link_count": internal_link_summary.get("low_link_count", 0),
        }

    summary_improvements = []
    summary = analysis_results.get("summary", {}) or {}
    summary_improvements.extend(summary.get("improvements", []) or [])

    if not summary_improvements:
        summary_improvements = integrated.get("improvements", []) or []

    ec_data = None
    if analysis_results.get("is_ec") is not None:
        ec_data = {
            "is_ec": bool(analysis_results.get("is_ec")),
            "reason": analysis_results.get("ec_detection_reason") or "",
        }

    return {
        "title": "SEO/AIO 統合分析レポート",
        "url": analysis_results.get("url", ""),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "scores": {
            "integrated": round(integrated.get("integrated_score", 0)),
            "seo": round(integrated.get("seo_score", 0)),
            "aio": round(integrated.get("aio_score", 0)),
            "legal": integrated.get("legal_score"),
        },
        "summary_improvements": summary_improvements[:8],
        "top_issues": top_issues,
        "crawl": crawl_data,
        "schema": schema_validation or None,
        "content_gap": {
            "potential": content_gap.get("aio_improvement_potential"),
            "gaps": gap_items,
        } if content_gap else None,
        "internal_links": internal_links,
        "ec": ec_data,
    }


def generate_pdf_report_v2(summary_data: dict, output_path: str) -> str:
    """HTMLテンプレート方式のPDF生成（本番）"""
    from PDFreport.simple_generator import generate_summary_pdf

    data = summary_data
    if isinstance(summary_data, dict) and "integrated_results" in summary_data:
        data = _build_html_report_data(summary_data)
    elif isinstance(summary_data, dict) and "scores" not in summary_data and "total_score" in summary_data:
        data = {
            "title": "サイト分析レポート",
            "url": "",
            "generated_at": "",
            "scores": {
                "integrated": summary_data.get("total_score", 0),
                "seo": summary_data.get("seo_score", 0),
                "aio": summary_data.get("aio_score", 0),
                "legal": summary_data.get("legal_score"),
            },
            "summary_improvements": summary_data.get("summary_improvements", []),
            "top_issues": summary_data.get("top_issues", []),
            "crawl": None,
            "schema": None,
            "content_gap": None,
            "internal_links": None,
            "ec": None,
        }
    return generate_summary_pdf(data, output_path)
