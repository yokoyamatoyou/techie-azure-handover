"""
PDFレポート用レイアウトマネージャ
非分割・スパン対応のレイアウト管理
"""

from typing import List, Dict, Any, Optional, Literal, Callable
from dataclasses import dataclass, field
from enum import Enum
from PDFreport.config.layout_specification import (
    LayoutSpecification,
    default_layout_spec,
    get_column_width,
    calculate_block_height,
)


class BlockType(Enum):
    """ブロックタイプ"""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    FIGURE = "figure"
    TABLE = "table"
    SPACER = "spacer"


@dataclass
class LayoutBlock:
    """レイアウトブロック"""
    block_type: BlockType
    content: Any  # テキスト、画像データ等
    keep_together: bool = False  # ブロック内の要素を一緒に保つ
    keep_with_next: bool = False  # 次のブロックと一緒に保つ
    column_span: int = 1  # カラムスパン（1または2）
    min_lines: int = 1  # 最小行数（分割防止）
    height_mm: float = 0.0  # ブロックの高さ（mm）
    estimated_height_mm: Optional[float] = None  # 推定高さ（mm）
    
    # ブロック固有の属性
    font_size_pt: float = 11.0
    line_height_ratio: float = 1.45
    spacing_before_mm: float = 0.0
    spacing_after_mm: float = 0.0
    
    # キャプション（図版用）
    caption: Optional[str] = None
    
    def estimate_height(self) -> float:
        """ブロックの高さを推定"""
        if self.estimated_height_mm is not None:
            return self.estimated_height_mm
        
        if self.block_type == BlockType.HEADING:
            # 見出しは1行 + 余白
            line_height = calculate_block_height(
                1, self.font_size_pt, self.line_height_ratio, 0.0
            )
            return line_height + self.spacing_after_mm
        
        elif self.block_type == BlockType.PARAGRAPH:
            # 段落はテキスト行数から推定
            if isinstance(self.content, str):
                # 簡易推定: 1行50文字、段幅85.5mmで約30文字/行
                lines = max(1, len(self.content) // 30)
                line_height = calculate_block_height(
                    lines, self.font_size_pt, self.line_height_ratio, 0.0
                )
                return line_height + self.spacing_after_mm
        
        elif self.block_type == BlockType.FIGURE:
            # 図版は高さを指定（デフォルト: 50mm）
            figure_height = self.height_mm if self.height_mm > 0 else 50.0
            caption_height = 0.0
            if self.caption:
                caption_lines = max(1, len(self.caption) // 30)
                caption_height = calculate_block_height(
                    caption_lines, 9.0, 1.4, 0.0  # Caption仕様
                )
            return figure_height + caption_height + self.spacing_before_mm + self.spacing_after_mm
        
        # デフォルト: 最小行数から推定
        line_height = calculate_block_height(
            self.min_lines, self.font_size_pt, self.line_height_ratio, 0.0
        )
        return line_height + self.spacing_after_mm


@dataclass
class ColumnState:
    """段の状態"""
    column_index: int  # 段のインデックス（0または1）
    current_y_mm: float  # 現在のY座標（mm）
    available_height_mm: float  # 利用可能な高さ（mm）
    
    def can_fit(self, block: LayoutBlock) -> bool:
        """ブロックが収まるか判定"""
        required_height = block.estimate_height()
        return required_height <= self.available_height_mm
    
    def add_block(self, block: LayoutBlock):
        """ブロックを追加（Y座標を更新）"""
        required_height = block.estimate_height()
        self.current_y_mm += required_height
        self.available_height_mm -= required_height


@dataclass
class PageState:
    """ページの状態"""
    page_number: int
    columns: List[ColumnState] = field(default_factory=list)
    is_single_column: bool = False  # 1段レイアウトかどうか
    
    def __post_init__(self):
        """初期化"""
        if not self.columns:
            if self.is_single_column:
                # 1段レイアウト
                spec = default_layout_spec
                usable_height = spec.margin.usable_height_mm
                self.columns = [
                    ColumnState(0, spec.margin.top_mm, usable_height)
                ]
            else:
                # 2段レイアウト
                spec = default_layout_spec
                usable_height = spec.margin.usable_height_mm
                column_width = get_column_width(2)
                self.columns = [
                    ColumnState(0, spec.margin.top_mm, usable_height),
                    ColumnState(1, spec.margin.top_mm, usable_height)
                ]


class LayoutManager:
    """レイアウトマネージャ"""
    
    def __init__(self, layout_spec: Optional[LayoutSpecification] = None):
        """
        レイアウトマネージャの初期化
        
        Args:
            layout_spec: レイアウト仕様（Noneの場合はデフォルトを使用）
        """
        self.spec = layout_spec or default_layout_spec
        self.pages: List[PageState] = []
        self.current_page: Optional[PageState] = None
        self.current_column_index: int = 0
        
    def start_page(self, is_single_column: bool = False):
        """新しいページを開始"""
        page_number = len(self.pages) + 1
        self.current_page = PageState(page_number, is_single_column=is_single_column)
        self.pages.append(self.current_page)
        self.current_column_index = 0
    
    def get_current_column(self) -> Optional[ColumnState]:
        """現在の段を取得"""
        if not self.current_page:
            return None
        if self.current_column_index >= len(self.current_page.columns):
            return None
        return self.current_page.columns[self.current_column_index]
    
    def can_fit_block(self, block: LayoutBlock) -> bool:
        """
        ブロックが現在の段に収まるか判定
        
        Args:
            block: レイアウトブロック
        
        Returns:
            bool: 収まる場合True
        """
        if block.column_span == 2:
            # 2段スパンの場合、ページ頭に配置を優先
            return True
        
        column = self.get_current_column()
        if not column:
            return False
        
        return column.can_fit(block)
    
    def add_block(self, block: LayoutBlock) -> bool:
        """
        ブロックを追加
        
        Args:
            block: レイアウトブロック
        
        Returns:
            bool: 追加成功時True
        """
        if not self.current_page:
            self.start_page()
        
        # 2段スパンの場合、ページ頭に配置
        if block.column_span == 2:
            if self.current_column_index != 0:
                # 次のページへ
                self.start_page()
            # 1段レイアウトで配置
            self.current_page.is_single_column = True
            self.current_page.columns = [
                ColumnState(0, self.spec.margin.top_mm, self.spec.margin.usable_height_mm)
            ]
            self.current_column_index = 0
        
        column = self.get_current_column()
        if not column:
            return False
        
        # keep_with_nextの処理
        if block.keep_with_next:
            # 次のブロックと一緒に保つ必要がある場合
            # 現在の段に収まらない場合は次ページへ
            if not column.can_fit(block):
                self._move_to_next_page()
                column = self.get_current_column()
                if not column:
                    return False
        
        # keep_togetherの処理
        if block.keep_together:
            # ブロック内の要素を一緒に保つ必要がある場合
            if not column.can_fit(block):
                self._move_to_next_page()
                column = self.get_current_column()
                if not column:
                    return False
        
        # 未亡人・孤児行の抑制
        if block.block_type == BlockType.PARAGRAPH:
            remaining_lines = self._estimate_remaining_lines(column, block)
            if remaining_lines < self.spec.typography.min_lines_at_end:
                # 段末に最低行数未満しか残らない場合、次段へ
                if not self._move_to_next_column():
                    self._move_to_next_page()
                    column = self.get_current_column()
                    if not column:
                        return False
        
        # ブロックを追加
        column.add_block(block)
        
        # 次の段へ移動（2段レイアウトの場合）
        if not self.current_page.is_single_column and block.column_span == 1:
            if self.current_column_index == 0:
                self.current_column_index = 1
            else:
                # 2段目も埋まった場合、次ページへ
                self._move_to_next_page()
        
        return True
    
    def _move_to_next_column(self) -> bool:
        """次の段へ移動"""
        if not self.current_page or self.current_page.is_single_column:
            return False
        
        if self.current_column_index == 0:
            self.current_column_index = 1
            return True
        
        return False
    
    def _move_to_next_page(self):
        """次のページへ移動"""
        self.start_page()
        self.current_column_index = 0
    
    def _estimate_remaining_lines(self, column: ColumnState, block: LayoutBlock) -> int:
        """残り行数を推定"""
        remaining_height = column.available_height_mm - block.estimate_height()
        line_height = calculate_block_height(
            1, block.font_size_pt, block.line_height_ratio, 0.0
        )
        if line_height == 0:
            return 0
        return int(remaining_height / line_height)
    
    def get_layout_info(self) -> Dict[str, Any]:
        """
        レイアウト情報を取得（デバッグ用）
        
        Returns:
            Dict[str, Any]: レイアウト情報
        """
        return {
            "total_pages": len(self.pages),
            "current_page": self.current_page.page_number if self.current_page else None,
            "current_column": self.current_column_index,
            "is_single_column": self.current_page.is_single_column if self.current_page else False,
        }





