"""image_config.py - Shared image settings."""

from pathlib import Path

from core.app_config import get_image_config

_CONFIG = get_image_config()

NOTE_IMAGE_SIZE = (_CONFIG.note_width, _CONFIG.note_height)
NOTE_IMAGE_SIZE_LABEL = f"{_CONFIG.note_width}x{_CONFIG.note_height}"
DEFAULT_IMAGE_COUNT = _CONFIG.count
DEFAULT_IMAGE_MODEL = _CONFIG.model_name
FALLBACK_IMAGE_MODEL = _CONFIG.fallback_model
DEFAULT_IMAGE_DESCRIPTION_MODEL = _CONFIG.description_model_name
FALLBACK_IMAGE_DESCRIPTION_MODEL = _CONFIG.description_fallback_model
DEFAULT_IMAGE_SIZE = _CONFIG.size
DEFAULT_IMAGE_QUALITY = _CONFIG.quality
DEFAULT_TEXT_IMAGE_QUALITY = _CONFIG.text_quality
DEFAULT_IMAGE_OUTPUT_FORMAT = _CONFIG.output_format
DEFAULT_IMAGE_BACKGROUND = _CONFIG.background
DEFAULT_IMAGE_MODERATION = _CONFIG.moderation
NO_TEXT_IN_IMAGE = _CONFIG.no_text_in_image
# フォントパス: 設定値 → デフォルト(Noto Sans JP) → システムフォント
_DEFAULT_FONT_PATH = str(Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSansJP-Regular.otf")
TEXT_OVERLAY_FONT_PATH = (
    _CONFIG.text_overlay_font_path
    if _CONFIG.text_overlay_font_path
    else _DEFAULT_FONT_PATH
)
GENERATED_IMAGES_DIR = (
    _CONFIG.generated_images_dir
    if _CONFIG.generated_images_dir
    else str(Path(__file__).resolve().parent / "generated_images")
)
