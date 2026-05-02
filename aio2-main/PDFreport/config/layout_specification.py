"""
PDFレポートのレイアウト仕様定義
印刷物のデザイン原則に基づいた段組み・タイポグラフィ・視線誘導・余白の仕様
"""

from dataclasses import dataclass
from typing import Literal


# ============================================================================
# 1. 用紙・基本寸法
# ============================================================================

@dataclass
class PaperSpec:
    """用紙仕様"""
    width_mm: float = 210.0  # A4幅（mm）
    height_mm: float = 297.0  # A4高さ（mm）
    orientation: Literal["portrait", "landscape"] = "portrait"


# ============================================================================
# 2. 余白仕様
# ============================================================================

@dataclass
class MarginSpec:
    """余白仕様（印刷物のデザイン原則に基づく）"""
    top_mm: float = 15.0      # 上余白（mm）
    bottom_mm: float = 15.0   # 下余白（mm）
    inner_mm: float = 15.0   # 内側余白（ノド側、mm）
    outer_mm: float = 15.0    # 外側余白（小口側、mm）
    
    @property
    def usable_width_mm(self) -> float:
        """利用可能幅（mm）"""
        return 210.0 - self.inner_mm - self.outer_mm
    
    @property
    def usable_height_mm(self) -> float:
        """利用可能高さ（mm）"""
        return 297.0 - self.top_mm - self.bottom_mm


# ============================================================================
# 3. グリッド・段組み仕様
# ============================================================================

@dataclass
class GridSpec:
    """グリッド・段組み仕様"""
    # 段組み設定
    columns: int = 2  # 段数（本文ページ: 2段、表紙/サマリ/大型図版: 1段）
    column_gap_mm: float = 9.0  # 段間（mm）
    
    @property
    def column_width_mm(self) -> float:
        """1段の幅（mm）"""
        margin = MarginSpec()
        usable_width = margin.usable_width_mm
        if self.columns == 1:
            return usable_width
        else:
            return (usable_width - (self.columns - 1) * self.column_gap_mm) / self.columns
    
    @property
    def single_column_width_mm(self) -> float:
        """1段レイアウト時の幅（mm）"""
        margin = MarginSpec()
        return margin.usable_width_mm


# ============================================================================
# 4. タイポグラフィ仕様
# ============================================================================

@dataclass
class TypographySpec:
    """タイポグラフィ仕様（階層・サイズ・行間・字間）"""
    # H1（大見出し）
    h1_size_pt: float = 20.0
    h1_line_height: float = 1.4  # 行間（フォントサイズの倍数）
    h1_weight: str = "B"  # Bold
    h1_spacing_after_mm: float = 8.0  # 見出し後の余白（mm）
    
    # H2（中見出し）
    h2_size_pt: float = 16.0
    h2_line_height: float = 1.5
    h2_weight: str = "B"  # Bold
    h2_spacing_after_mm: float = 6.0
    
    # H3（小見出し）
    h3_size_pt: float = 13.0
    h3_line_height: float = 1.5
    h3_weight: str = "B"  # Bold
    h3_spacing_after_mm: float = 4.0
    
    # Body（本文）
    body_size_pt: float = 11.0
    body_line_height: float = 1.45  # 1.3-1.5の範囲（読みやすさ重視）
    body_weight: str = ""  # Regular
    body_spacing_after_mm: float = 3.0  # 段落後の余白（mm）
    
    # Caption（キャプション）
    caption_size_pt: float = 9.0  # Body - 2pt
    caption_line_height: float = 1.4
    caption_weight: str = ""  # Regular（italic可）
    caption_spacing_before_mm: float = 2.0  # 図版前の余白（mm）
    caption_spacing_after_mm: float = 4.0  # 図版後の余白（mm）
    
    # 未亡人・孤児行の抑制
    min_lines_at_start: int = 2  # 段頭の最低行数（孤児行の抑制）
    min_lines_at_end: int = 2    # 段末の最低行数（未亡人行の抑制）
    keep_with_next_lines: int = 2  # 見出しと次段落の最低行数（keep_with_next）


# ============================================================================
# 5. 視線誘導・余白ルール
# ============================================================================

@dataclass
class VisualFlowSpec:
    """視線誘導・余白ルール（Zの法則、アイキャッチ→導入→本文）"""
    # ブロック間の余白
    block_spacing_mm: float = 6.0  # ブロック間の標準余白（mm）
    section_spacing_mm: float = 12.0  # セクション間の余白（mm）
    
    # アイキャッチ（表紙・要約ページ）
    eyecatch_spacing_before_mm: float = 20.0  # アイキャッチ前の余白（mm）
    eyecatch_spacing_after_mm: float = 15.0   # アイキャッチ後の余白（mm）
    
    # 図版の余白
    figure_spacing_before_mm: float = 8.0   # 図版前の余白（mm）
    figure_spacing_after_mm: float = 6.0   # 図版後の余白（mm）
    
    # 箇条書きの余白
    list_item_spacing_mm: float = 2.0  # 箇条書き項目間の余白（mm）
    list_spacing_before_mm: float = 4.0  # 箇条書き前の余白（mm）
    list_spacing_after_mm: float = 4.0  # 箇条書き後の余白（mm）


# ============================================================================
# 6. 非分割ルール
# ============================================================================

@dataclass
class KeepTogetherSpec:
    """非分割ルール（keep_together, keep_with_next）"""
    # 図版とキャプション
    figure_caption_keep_together: bool = True  # 図版とキャプションは常に一緒
    
    # 見出しと次段落
    heading_keep_with_next: bool = True  # 見出しは次段落と一緒（最低2行）
    
    # 段落の最小行数
    paragraph_min_lines: int = 2  # 段落の最小行数（分割防止）
    
    # 箇条書き項目
    list_item_min_lines: int = 1  # 箇条書き項目の最小行数


# ============================================================================
# 7. カラムスパン仕様
# ============================================================================

@dataclass
class ColumnSpanSpec:
    """カラムスパン仕様（1段/2段の判定）"""
    # デフォルトスパン
    default_figure_span: int = 2  # 図版のデフォルトスパン（2段=全幅）
    default_table_span: int = 2   # 表のデフォルトスパン（2段=全幅）
    
    # 1段レイアウトの条件
    single_column_threshold_mm: float = 80.0  # この幅以下の図版は1段レイアウト
    
    # ページ頭配置の優先度
    prefer_page_start: bool = True  # span=2の要素はページ頭に配置を優先


# ============================================================================
# 8. 統合仕様クラス
# ============================================================================

@dataclass
class LayoutSpecification:
    """レイアウト仕様の統合クラス"""
    paper: PaperSpec = None
    margin: MarginSpec = None
    grid: GridSpec = None
    typography: TypographySpec = None
    visual_flow: VisualFlowSpec = None
    keep_together: KeepTogetherSpec = None
    column_span: ColumnSpanSpec = None
    
    def __post_init__(self):
        """デフォルト値の設定"""
        if self.paper is None:
            self.paper = PaperSpec()
        if self.margin is None:
            self.margin = MarginSpec()
        if self.grid is None:
            self.grid = GridSpec()
        if self.typography is None:
            self.typography = TypographySpec()
        if self.visual_flow is None:
            self.visual_flow = VisualFlowSpec()
        if self.keep_together is None:
            self.keep_together = KeepTogetherSpec()
        if self.column_span is None:
            self.column_span = ColumnSpanSpec()


# ============================================================================
# 9. グローバルインスタンス
# ============================================================================

# デフォルトのレイアウト仕様
default_layout_spec = LayoutSpecification()


# ============================================================================
# 10. ヘルパー関数
# ============================================================================

def get_column_width(columns: int = 2) -> float:
    """
    段幅を取得
    
    Args:
        columns: 段数（1または2）
    
    Returns:
        float: 段幅（mm）
    """
    spec = default_layout_spec
    if columns == 1:
        return spec.grid.single_column_width_mm
    else:
        return spec.grid.column_width_mm


def get_line_height(font_size_pt: float, line_height_ratio: float) -> float:
    """
    行の高さを計算（mm）
    
    Args:
        font_size_pt: フォントサイズ（pt）
        line_height_ratio: 行間比率
    
    Returns:
        float: 行の高さ（mm）
    """
    # 1pt = 0.352778mm
    font_size_mm = font_size_pt * 0.352778
    return font_size_mm * line_height_ratio


def calculate_block_height(
    text_lines: int,
    font_size_pt: float,
    line_height_ratio: float,
    spacing_after_mm: float = 0.0
) -> float:
    """
    ブロックの高さを計算（mm）
    
    Args:
        text_lines: テキスト行数
        font_size_pt: フォントサイズ（pt）
        line_height_ratio: 行間比率
        spacing_after_mm: 後の余白（mm）
    
    Returns:
        float: ブロックの高さ（mm）
    """
    line_height_mm = get_line_height(font_size_pt, line_height_ratio)
    return (text_lines * line_height_mm) + spacing_after_mm





