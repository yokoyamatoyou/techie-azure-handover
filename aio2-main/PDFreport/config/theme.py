"""
プリセット別カラーパレットとテーマトークン定義
PDFレポートとUIで統一されたテーマカラーを提供
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ColorPalette:
    """カラーパレット定義クラス"""
    primary: Tuple[int, int, int]  # メインカラー（見出し、強調）
    accent: Tuple[int, int, int]    # アクセントカラー（リンク、ボタン）
    positive: Tuple[int, int, int]  # ポジティブ（成功、良い指標）
    negative: Tuple[int, int, int]  # ネガティブ（警告、悪い指標）
    neutral: Tuple[int, int, int]   # ニュートラル（本文、背景）
    bg: Tuple[int, int, int]        # 背景色
    grid: Tuple[int, int, int]      # グリッド線、罫線


# プリセット別カラーパレット定義
THEME_PALETTES: Dict[str, ColorPalette] = {
    "customer_satisfaction": ColorPalette(
        primary=(44, 62, 80),      # #2C3E50 - ダークブルーグレー（信頼感）
        accent=(52, 152, 219),     # #3498DB - ブルー（顧客満足）
        positive=(46, 204, 113),    # #2ECC71 - グリーン（満足）
        negative=(231, 76, 60),     # #E74C3C - レッド（不満）
        neutral=(52, 73, 94),      # #34495E - ダークグレー（本文）
        bg=(255, 255, 255),        # #FFFFFF - 白（背景）
        grid=(236, 240, 241),      # #ECF0F1 - ライトグレー（罫線）
    ),
    "market_research": ColorPalette(
        primary=(108, 92, 231),    # #6C5CE7 - パープル（市場分析）
        accent=(0, 188, 212),      # #00BCD4 - シアン（成長）
        positive=(46, 204, 113),   # #2ECC71 - グリーン（機会）
        negative=(255, 112, 67),   # #FF7043 - オレンジレッド（リスク）
        neutral=(97, 97, 97),      # #616161 - グレー（本文）
        bg=(255, 255, 255),        # #FFFFFF - 白（背景）
        grid=(224, 224, 224),      # #E0E0E0 - ライトグレー（罫線）
    ),
    "employee_satisfaction": ColorPalette(
        primary=(108, 92, 231),    # #6C5CE7 - パープル（エンゲージメント）
        accent=(0, 188, 212),      # #00BCD4 - シアン（成長）
        positive=(46, 204, 113),   # #2ECC71 - グリーン（満足）
        negative=(255, 112, 67),   # #FF7043 - オレンジレッド（不満）
        neutral=(97, 97, 97),      # #616161 - グレー（本文）
        bg=(255, 255, 255),        # #FFFFFF - 白（背景）
        grid=(224, 224, 224),      # #E0E0E0 - ライトグレー（罫線）
    ),
    "brand_research": ColorPalette(
        primary=(52, 73, 94),      # #34495E - ダークグレー（ブランド）
        accent=(241, 196, 15),     # #F1C40F - ゴールド（価値）
        positive=(39, 174, 96),    # #27AE60 - グリーン（信頼）
        negative=(192, 57, 43),    # #C0392B - ダークレッド（失望）
        neutral=(127, 140, 141),   # #7F8C8D - グレー（本文）
        bg=(255, 255, 255),        # #FFFFFF - 白（背景）
        grid=(236, 240, 241),      # #ECF0F1 - ライトグレー（罫線）
    ),
    "public_opinion": ColorPalette(
        primary=(45, 52, 54),      # #2D3436 - ダークグレー（公共性）
        accent=(9, 132, 227),      # #0984E3 - ブルー（信頼）
        positive=(0, 200, 83),     # #00C853 - グリーン（満足）
        negative=(213, 0, 0),      # #D50000 - レッド（懸念）
        neutral=(99, 110, 114),    # #636E72 - グレー（本文）
        bg=(255, 255, 255),        # #FFFFFF - 白（背景）
        grid=(223, 230, 233),      # #DFE6E9 - ライトグレー（罫線）
    ),
    "hospitality": ColorPalette(
        primary=(44, 62, 80),      # #2C3E50 - ダークブルーグレー（高級感）
        accent=(52, 152, 219),     # #3498DB - ブルー（サービス）
        positive=(46, 204, 113),   # #2ECC71 - グリーン（満足）
        negative=(231, 76, 60),    # #E74C3C - レッド（不満）
        neutral=(52, 73, 94),      # #34495E - ダークグレー（本文）
        bg=(255, 255, 255),        # #FFFFFF - 白（背景）
        grid=(236, 240, 241),      # #ECF0F1 - ライトグレー（罫線）
    ),
}


def get_theme_palette(survey_type: str) -> ColorPalette:
    """
    プリセット別のカラーパレットを取得
    
    Args:
        survey_type: アンケートタイプ（customer_satisfaction, market_research等）
    
    Returns:
        ColorPalette: カラーパレット（存在しない場合はデフォルトを返す）
    
    Raises:
        ValueError: survey_typeが無効な場合
    """
    if not survey_type or not isinstance(survey_type, str):
        raise ValueError(f"無効なsurvey_type: {survey_type}")
    
    # デフォルトはcustomer_satisfaction
    default_palette = THEME_PALETTES.get("customer_satisfaction")
    
    palette = THEME_PALETTES.get(survey_type, default_palette)
    
    if palette is None:
        # フォールバック: デフォルトパレット
        palette = ColorPalette(
            primary=(44, 62, 80),
            accent=(52, 152, 219),
            positive=(46, 204, 113),
            negative=(231, 76, 60),
            neutral=(52, 73, 94),
            bg=(255, 255, 255),
            grid=(236, 240, 241),
        )
    
    return palette


def get_color_rgb(survey_type: str, color_token: str) -> Tuple[int, int, int]:
    """
    カラートークンからRGB値を取得（簡易アクセサ）
    
    Args:
        survey_type: アンケートタイプ
        color_token: カラートークン（primary, accent, positive, negative, neutral, bg, grid）
    
    Returns:
        Tuple[int, int, int]: RGB値
    
    Raises:
        ValueError: 無効なcolor_tokenの場合
    """
    palette = get_theme_palette(survey_type)
    
    color_map = {
        "primary": palette.primary,
        "accent": palette.accent,
        "positive": palette.positive,
        "negative": palette.negative,
        "neutral": palette.neutral,
        "bg": palette.bg,
        "grid": palette.grid,
    }
    
    if color_token not in color_map:
        raise ValueError(
            f"無効なcolor_token: {color_token}. "
            f"有効な値: {list(color_map.keys())}"
        )
    
    return color_map[color_token]


def get_color_hex(survey_type: str, color_token: str) -> str:
    """
    カラートークンからHEX値を取得（Web/UI用）
    
    Args:
        survey_type: アンケートタイプ
        color_token: カラートークン
    
    Returns:
        str: HEX値（例: "#2C3E50"）
    """
    rgb = get_color_rgb(survey_type, color_token)
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


# 後方互換性: 既存コードとの統合用
def get_theme_colors(survey_type: str) -> Dict[str, Tuple[int, int, int]]:
    """
    プリセット別のカラー辞書を取得（後方互換性）
    
    Args:
        survey_type: アンケートタイプ
    
    Returns:
        Dict[str, Tuple[int, int, int]]: カラー辞書
    """
    palette = get_theme_palette(survey_type)
    return {
        "primary": palette.primary,
        "accent": palette.accent,
        "positive": palette.positive,
        "negative": palette.negative,
        "neutral": palette.neutral,
        "bg": palette.bg,
        "grid": palette.grid,
    }





