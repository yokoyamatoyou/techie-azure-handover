"""PDF生成エラークラスの定義

統一されたエラーハンドリングのためのエラークラスを提供します。
"""

from datetime import datetime
from typing import Optional, Dict, Any


class PDFGenerationError(Exception):
    """PDF生成エラーの基底クラス"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}
        self.timestamp = datetime.now()
        self.error_type = self.__class__.__name__
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {super().__str__()}"
    
    def get_detailed_message(self) -> str:
        """詳細なエラーメッセージを取得
        
        Returns:
            str: 詳細なエラーメッセージ
        """
        return f"""
エラーが発生しました:

エラータイプ: {self.__class__.__name__}
エラーメッセージ: {super().__str__()}
発生時刻: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
コンテキスト: {self.context}
"""


class FontRegistrationError(PDFGenerationError):
    """フォント登録エラー"""
    pass


class ImageProcessingError(PDFGenerationError):
    """画像処理エラー"""
    pass


class LayoutError(PDFGenerationError):
    """レイアウトエラー"""
    pass


class DataValidationError(PDFGenerationError):
    """データ検証エラー"""
    pass


class FileIOError(PDFGenerationError):
    """ファイルI/Oエラー"""
    pass



