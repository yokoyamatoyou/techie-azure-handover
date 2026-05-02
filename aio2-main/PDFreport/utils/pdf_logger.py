"""PDF生成用統一ロガーの設定

統一されたログ出力のためのロガーを提供します。
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_unified_logger(
    logger_name: str = "pdf_generator",
    log_file: str = "pdf_generation.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """統一ロガーの設定
    
    Args:
        logger_name: ロガー名
        log_file: ログファイル名
        max_bytes: ログファイルの最大サイズ（バイト）
        backup_count: バックアップファイル数
    
    Returns:
        logging.Logger: 設定済みロガー
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    # 既存のハンドラーをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # ファイルハンドラー（ローテーション対応）
    try:
        file_handler = RotatingFileHandler(
            log_file,
            mode='a',
            encoding='utf-8',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # ファイルハンドラーの作成に失敗した場合はコンソールハンドラーのみ使用
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.warning(f"ログファイルの作成に失敗しました: {e}")
    
    # コンソールハンドラー（INFOレベル以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def cleanup_logger(logger: logging.Logger) -> None:
    """ロガーのクリーンアップ
    
    Args:
        logger: クリーンアップするロガー
    """
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()



