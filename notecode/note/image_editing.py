"""Image editing utilities for note_writer_app."""
from __future__ import annotations

import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\-\s()]{8,}\d)(?!\d)")
NAME_PATTERN_JP_SPACED = re.compile(r"^[\u4E00-\u9FFF]{1,4}\s+[\u4E00-\u9FFF]{1,4}$")
NAME_PATTERN_EN = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$")
PERSONAL_LABEL_HINTS = (
    "氏名",
    "名前",
    "お名前",
    "name",
    "担当者",
    "連絡先",
    "電話",
    "tel",
    "mobile",
    "メール",
    "mail",
    "email",
    "e-mail",
)
_RAPID_OCR_ENGINE = None


@dataclass(frozen=True)
class ImageAdjustment:
    """Continuous enhancement controls."""

    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0
    sharpness: float = 1.0


@dataclass(frozen=True)
class TextOverlay:
    """Text overlay controls."""

    text: str
    position: str = "center"
    size: str = "medium"
    color: str = "auto"
    with_bar: bool = True
    font_style: str = "sans"
    background_preset: str = "image"


@dataclass(frozen=True)
class PrivacyBlur:
    """Automatic PII blur controls."""

    enabled: bool = False
    strength: str = "medium"
    blur_faces: bool = True
    blur_license_plates: bool = True
    blur_qr_codes: bool = True
    blur_personal_text: bool = True


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _ensure_output_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _measure_text(draw, text: str, font) -> Tuple[int, int]:
    sample = text if text else " "
    bbox = draw.textbbox((0, 0), sample, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _measure_text_bbox(draw, text: str, font, stroke_width: int = 0) -> Tuple[int, int, int, int]:
    sample = text if text else " "
    return draw.textbbox((0, 0), sample, font=font, stroke_width=max(int(stroke_width or 0), 0))


def _wrap_line(draw, line: str, font, max_width: int) -> List[str]:
    if not line:
        return [""]
    width, _ = _measure_text(draw, line, font)
    if width <= max_width:
        return [line]

    chunks: List[str] = []
    current = ""
    for ch in line:
        candidate = f"{current}{ch}"
        c_width, _ = _measure_text(draw, candidate, font)
        if c_width <= max_width or not current:
            current = candidate
            continue
        chunks.append(current)
        current = ch
    if current:
        chunks.append(current)
    return chunks if chunks else [line]


def _wrap_text(draw, text: str, font, max_width: int) -> List[str]:
    lines: List[str] = []
    raw_lines = text.splitlines() or [text]
    for raw in raw_lines:
        lines.extend(_wrap_line(draw, raw.strip(), font, max_width))
    filtered = [line for line in lines if line.strip()]
    return filtered or [""]


def _resolve_font_candidates(configured_font_path: str, font_style: str) -> List[str]:
    style = str(font_style or "sans").strip().lower()
    candidates: List[str] = []
    if style == "bold":
        candidates.extend(
            [
                "C:/Windows/Fonts/BIZ-UDGothicB.ttc",
                "C:/Windows/Fonts/YuGothB.ttc",
                "C:/Windows/Fonts/meiryob.ttc",
            ]
        )
    elif style == "yu_gothic":
        candidates.extend(
            [
                "C:/Windows/Fonts/YuGothM.ttc",
                "C:/Windows/Fonts/YuGothR.ttc",
                "C:/Windows/Fonts/YuGothB.ttc",
            ]
        )
    elif style == "yu_mincho":
        candidates.extend(
            [
                "C:/Windows/Fonts/yumin.ttf",
                "C:/Windows/Fonts/yumindb.ttf",
                "C:/Windows/Fonts/yuminl.ttf",
            ]
        )
    elif style == "meiryo":
        candidates.extend(
            [
                "C:/Windows/Fonts/meiryo.ttc",
                "C:/Windows/Fonts/meiryob.ttc",
            ]
        )
    elif style == "mincho":
        candidates.extend(
            [
                "C:/Windows/Fonts/BIZ-UDMinchoM.ttc",
                "C:/Windows/Fonts/yumin.ttf",
                "C:/Windows/Fonts/msmincho.ttc",
            ]
        )
    else:
        if configured_font_path:
            candidates.append(configured_font_path)
        candidates.extend(
            [
                "C:/Windows/Fonts/BIZ-UDGothicR.ttc",
                "C:/Windows/Fonts/meiryo.ttc",
                "C:/Windows/Fonts/msgothic.ttc",
            ]
        )
    if configured_font_path and configured_font_path not in candidates:
        candidates.append(configured_font_path)
    return candidates


def _normalize_overlay_position(position: str) -> Tuple[str, str, str]:
    raw = str(position or "center").strip().lower().replace("-", "_")
    alias_map = {
        "top": "top_center",
        "center": "middle_center",
        "middle": "middle_center",
        "bottom": "bottom_center",
        "left": "middle_left",
        "right": "middle_right",
    }
    normalized = alias_map.get(raw, raw)
    allowed = {
        "top_left",
        "top_center",
        "top_right",
        "middle_left",
        "middle_center",
        "middle_right",
        "bottom_left",
        "bottom_center",
        "bottom_right",
    }
    if normalized not in allowed:
        normalized = "middle_center"
    vertical, horizontal = normalized.split("_", 1)
    return normalized, vertical, horizontal


def _load_font(font_size: int, configured_font_path: str, font_style: str = "sans"):
    from PIL import ImageFont

    font = None
    for candidate in _resolve_font_candidates(configured_font_path, font_style):
        if not candidate or not Path(candidate).exists():
            continue
        try:
            font = ImageFont.truetype(candidate, font_size)
            break
        except OSError as exc:
            logger.debug("Failed to load overlay font candidate=%s", candidate, exc_info=exc)
    if font is None:
        font = ImageFont.load_default()
    return font


def _resolve_overlay_palette(img, block_rect: Tuple[int, int, int, int], color: str):
    from PIL import ImageStat

    color_key = (color or "auto").lower().strip()
    x0, y0, x1, y1 = block_rect
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(img.width, x1)
    y1 = min(img.height, y1)

    if color_key == "auto":
        crop = img.crop((x0, y0, max(x0 + 1, x1), max(y0 + 1, y1))).convert("L")
        mean_luminance = ImageStat.Stat(crop).mean[0] if crop.size[0] and crop.size[1] else 127
        color_key = "white" if mean_luminance < 140 else "black"

    if color_key == "black":
        return (0, 0, 0), (255, 255, 255), (255, 255, 255, 120)
    return (255, 255, 255), (0, 0, 0), (0, 0, 0, 130)


def _fit_overlay_layout(img, overlay: TextOverlay, configured_font_path: str):
    from PIL import ImageDraw

    ratio_map = {"small": 0.03, "medium": 0.05, "large": 0.07}
    ratio = ratio_map.get(overlay.size, 0.05)
    max_width = max(int(img.width * 0.82), 120)
    max_height = max(int(img.height * 0.62), 80)
    font_size = max(int(img.width * ratio), 16)
    draw = ImageDraw.Draw(img)

    lines: List[str] = [overlay.text]
    line_sizes: List[Tuple[int, int]] = [
        _measure_text(draw, overlay.text, _load_font(font_size, configured_font_path, overlay.font_style))
    ]
    line_spacing = max(int(font_size * 0.28), 4)
    font = _load_font(font_size, configured_font_path, overlay.font_style)

    for _ in range(12):
        font = _load_font(font_size, configured_font_path, overlay.font_style)
        lines = _wrap_text(draw, overlay.text, font, max_width)
        line_sizes = [_measure_text(draw, ln, font) for ln in lines]
        line_spacing = max(int(font_size * 0.28), 4)
        total_height = sum(h for _, h in line_sizes) + line_spacing * (len(lines) - 1)
        text_width = max((w for w, _ in line_sizes), default=0)
        if text_width <= max_width and total_height <= max_height:
            break
        font_size = max(int(font_size * 0.9), 14)

    total_height = sum(h for _, h in line_sizes) + line_spacing * (len(lines) - 1)
    text_width = max((w for w, _ in line_sizes), default=0)
    return font, lines, line_sizes, line_spacing, text_width, total_height, font_size


def _build_overlay_balance_report(
    image_size: Tuple[int, int],
    text_block_rect: Tuple[int, int, int, int],
    bar_rect: Tuple[int, int, int, int],
    position: str,
) -> dict:
    _normalized_position, vertical_position, horizontal_position = _normalize_overlay_position(position)
    width, height = image_size
    image_center_x = width / 2.0
    image_center_y = height / 2.0
    tx0, ty0, tx1, ty1 = text_block_rect
    bx0, by0, bx1, by1 = bar_rect
    text_center_x = (tx0 + tx1) / 2.0
    text_center_y = (ty0 + ty1) / 2.0
    bar_center_x = (bx0 + bx1) / 2.0
    bar_center_y = (by0 + by1) / 2.0
    text_inside_bar = tx0 >= bx0 and ty0 >= by0 and tx1 <= bx1 and ty1 <= by1
    bar_inside_image = bx0 >= 0 and by0 >= 0 and bx1 <= width and by1 <= height
    report = {
        "image_center_x": round(image_center_x, 2),
        "image_center_y": round(image_center_y, 2),
        "text_center_x": round(text_center_x, 2),
        "text_center_y": round(text_center_y, 2),
        "bar_center_x": round(bar_center_x, 2),
        "bar_center_y": round(bar_center_y, 2),
        "text_center_offset_x": round(text_center_x - image_center_x, 2),
        "bar_center_offset_x": round(bar_center_x - image_center_x, 2),
        "text_bar_center_delta_x": round(text_center_x - bar_center_x, 2),
        "text_bar_center_delta_y": round(text_center_y - bar_center_y, 2),
        "text_inside_bar": bool(text_inside_bar),
        "bar_inside_image": bool(bar_inside_image),
        "horizontal_position": horizontal_position,
        "vertical_position": vertical_position,
    }
    if horizontal_position == "center":
        report["expected_centered_x"] = True
    if vertical_position == "middle":
        report["expected_centered_y"] = True
        report["text_center_offset_y"] = round(text_center_y - image_center_y, 2)
        report["bar_center_offset_y"] = round(bar_center_y - image_center_y, 2)
    report["balanced"] = bool(
        text_inside_bar
        and bar_inside_image
        and (
            horizontal_position != "center"
            or (
                abs(float(report["text_center_offset_x"])) <= 1.0
                and abs(float(report["bar_center_offset_x"])) <= 1.0
            )
        )
        and abs(float(report["text_bar_center_delta_x"])) <= 1.0
        and abs(float(report["text_bar_center_delta_y"])) <= 1.0
        and (
            vertical_position != "middle"
            or (
                abs(float(report.get("text_center_offset_y", 0.0))) <= 1.0
                and abs(float(report.get("bar_center_offset_y", 0.0))) <= 1.0
            )
        )
    )
    return report


def _build_poster_background(base_size: Tuple[int, int], preset: str):
    from PIL import Image, ImageDraw

    width, height = base_size
    bg = Image.new("RGB", (width, height), "#F4EDE5")
    draw = ImageDraw.Draw(bg)
    preset_key = str(preset or "poster_frame").strip().lower()
    if preset_key == "poster_frame":
        outer_margin_x = max(int(width * 0.05), 28)
        outer_margin_y = max(int(height * 0.08), 28)
        inner_margin_x = outer_margin_x + max(int(width * 0.025), 14)
        inner_margin_y = outer_margin_y + max(int(height * 0.035), 14)
        frame_radius = max(int(min(width, height) * 0.028), 16)
        draw.rounded_rectangle(
            [outer_margin_x, outer_margin_y, width - outer_margin_x, height - outer_margin_y],
            radius=frame_radius,
            fill="#E6D5C7",
        )
        draw.rounded_rectangle(
            [inner_margin_x, inner_margin_y, width - inner_margin_x, height - inner_margin_y],
            radius=max(frame_radius - 8, 10),
            fill="#FFFDFC",
            outline="#D0B8A7",
            width=max(width // 420, 2),
        )
        accent_h = max(int(height * 0.03), 12)
        draw.rounded_rectangle(
            [
                inner_margin_x + max(int(width * 0.05), 16),
                inner_margin_y + max(int(height * 0.045), 16),
                width - inner_margin_x - max(int(width * 0.05), 16),
                inner_margin_y + max(int(height * 0.045), 16) + accent_h,
            ],
            radius=max(accent_h // 2, 6),
            fill="#E64424",
        )
        return bg
    return bg


def _resolve_overlay_geometry(img, overlay: TextOverlay, configured_font_path: str) -> dict:
    from PIL import ImageDraw

    width, height = img.size
    normalized_position, vertical_position, horizontal_position = _normalize_overlay_position(overlay.position)
    font, lines, _line_sizes, line_spacing, _max_text_width, _total_text_height, font_size = _fit_overlay_layout(
        img,
        overlay,
        configured_font_path,
    )
    draw = ImageDraw.Draw(img)
    stroke_width = max(int(font_size * 0.05), 1)
    line_boxes = [_measure_text_bbox(draw, line, font, stroke_width=stroke_width) for line in lines]
    line_widths = [bbox[2] - bbox[0] for bbox in line_boxes]
    line_heights = [bbox[3] - bbox[1] for bbox in line_boxes]
    max_text_width = max(line_widths, default=0)
    total_text_height = sum(line_heights) + line_spacing * max(len(line_heights) - 1, 0)

    if vertical_position == "top":
        block_y = int(height * 0.1)
    elif vertical_position == "bottom":
        block_y = int(height * 0.85) - total_text_height
    else:
        block_y = (height - total_text_height) // 2
    block_y = max(10, min(block_y, height - total_text_height - 10))

    pad_x = int(font_size * 0.6)
    pad_y = int(font_size * 0.4)
    bar_width = max_text_width + (pad_x * 2)
    side_margin = max(int(width * 0.06), 18)
    if horizontal_position == "left":
        bar_x0 = side_margin
    elif horizontal_position == "right":
        bar_x0 = width - bar_width - side_margin
    else:
        bar_x0 = (width - bar_width) // 2
    bar_x0 = max(0, min(bar_x0, width - bar_width))
    bar_y0 = max(0, block_y - pad_y)
    bar_x1 = min(width, bar_x0 + bar_width)
    bar_y1 = min(height, block_y + total_text_height + pad_y)
    bar_rect = (bar_x0, bar_y0, bar_x1, bar_y1)
    resolved_bar_width = bar_x1 - bar_x0

    text_rects: List[Tuple[int, int, int, int]] = []
    placements: List[Tuple[str, int, int]] = []
    cur_y = block_y
    for index, line in enumerate(lines):
        bbox = line_boxes[index]
        line_width = line_widths[index]
        line_height = line_heights[index]
        line_x = bar_x0 + (resolved_bar_width - line_width) // 2 - bbox[0]
        line_y = cur_y - bbox[1]
        placements.append((line, line_x, line_y))
        text_rects.append((line_x + bbox[0], line_y + bbox[1], line_x + bbox[2], line_y + bbox[3]))
        cur_y += line_height + line_spacing

    if text_rects:
        text_block_rect = (
            min(rect[0] for rect in text_rects),
            min(rect[1] for rect in text_rects),
            max(rect[2] for rect in text_rects),
            max(rect[3] for rect in text_rects),
        )
    else:
        text_block_rect = bar_rect

    return {
        "font": font,
        "font_size": font_size,
        "stroke_width": stroke_width,
        "bar_rect": bar_rect,
        "text_lines": placements,
        "text_block_rect": text_block_rect,
        "balance_report": _build_overlay_balance_report((width, height), text_block_rect, bar_rect, normalized_position),
    }


def _draw_text_overlay(
    img_rgb,
    overlay: TextOverlay,
    configured_font_path: str,
):
    from PIL import Image, ImageDraw

    text = (overlay.text or "").strip()
    if not text:
        return img_rgb

    img = img_rgb.convert("RGBA")
    width, height = img.size
    geometry = _resolve_overlay_geometry(img, overlay, configured_font_path)
    block_rect = geometry["bar_rect"]
    fill_color, stroke_color, bar_color = _resolve_overlay_palette(img, block_rect, overlay.color)

    if overlay.with_bar:
        bar_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar_layer)
        radius = max(int(int(geometry["font_size"]) * 0.3), 6)
        bar_draw.rounded_rectangle(list(block_rect), radius=radius, fill=bar_color)
        img = Image.alpha_composite(img, bar_layer)

    draw = ImageDraw.Draw(img)
    stroke_width = int(geometry["stroke_width"])
    for line, line_x, line_y in geometry["text_lines"]:
        draw.text(
            (line_x, line_y),
            line,
            font=geometry["font"],
            fill=fill_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_color,
        )
    if not bool(geometry["balance_report"].get("balanced")):
        logger.debug("Overlay balance report=%s", geometry["balance_report"])

    return img.convert("RGB")


def _apply_filter(img_rgb, filter_type: str):
    from PIL import ImageEnhance, Image

    filter_key = (filter_type or "none").lower().strip()
    if filter_key in ("none", ""):
        return img_rgb

    img = img_rgb.convert("RGB")
    if filter_key == "warm":
        img = ImageEnhance.Color(img).enhance(1.3)
        r, g, b = img.split()
        r = r.point(lambda v: min(v + 15, 255))
        return Image.merge("RGB", (r, g, b))
    if filter_key == "cool":
        img = ImageEnhance.Color(img).enhance(0.9)
        r, g, b = img.split()
        b = b.point(lambda v: min(v + 20, 255))
        return Image.merge("RGB", (r, g, b))
    if filter_key == "sepia":
        grey = img.convert("L")
        return Image.merge(
            "RGB",
            (
                grey.point(lambda v: min(int(v * 1.2), 255)),
                grey.point(lambda v: min(int(v * 1.0), 255)),
                grey.point(lambda v: min(int(v * 0.8), 255)),
            ),
        )
    if filter_key == "monochrome":
        return img.convert("L").convert("RGB")
    raise ValueError(f"不明なフィルタ: {filter_type}")


def _apply_gradient(img_rgb, gradient_type: str):
    from PIL import Image

    grad_key = (gradient_type or "none").lower().strip()
    if grad_key in ("none", ""):
        return img_rgb
    if grad_key not in ("top", "bottom"):
        raise ValueError(f"不明なグラデーション: {gradient_type}")

    img = img_rgb.convert("RGBA")
    width, height = img.size
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    grad_height = max(int(height * 0.4), 1)

    for y in range(grad_height):
        if grad_key == "top":
            alpha = int(180 * (1 - y / grad_height))
            row_y = y
        else:
            alpha = int(180 * (y / grad_height))
            row_y = height - grad_height + y
        row = Image.new("RGBA", (width, 1), (0, 0, 0, alpha))
        gradient.paste(row, (0, row_y))
    return Image.alpha_composite(img, gradient).convert("RGB")


def _apply_adjustments(img_rgb, adjustment: ImageAdjustment):
    from PIL import ImageEnhance

    img = img_rgb.convert("RGB")
    brightness = _clamp(adjustment.brightness, 0.5, 1.8)
    contrast = _clamp(adjustment.contrast, 0.5, 1.8)
    saturation = _clamp(adjustment.saturation, 0.0, 1.8)
    sharpness = _clamp(adjustment.sharpness, 0.0, 2.0)

    if abs(brightness - 1.0) > 1e-3:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if abs(contrast - 1.0) > 1e-3:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if abs(saturation - 1.0) > 1e-3:
        img = ImageEnhance.Color(img).enhance(saturation)
    if abs(sharpness - 1.0) > 1e-3:
        img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img


def _expand_rect(
    rect: Tuple[int, int, int, int],
    width: int,
    height: int,
    padding_ratio: float = 0.12,
) -> Tuple[int, int, int, int]:
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return (0, 0, 0, 0)
    pad_x = int(w * padding_ratio)
    pad_y = int(h * padding_ratio)
    x0 = max(0, x - pad_x)
    y0 = max(0, y - pad_y)
    x1 = min(width, x + w + pad_x)
    y1 = min(height, y + h + pad_y)
    if x1 <= x0 or y1 <= y0:
        return (0, 0, 0, 0)
    return (x0, y0, x1 - x0, y1 - y0)


def _kernel_size(strength: str, min_side: int) -> int:
    base_map = {"light": 19, "medium": 35, "strong": 59}
    base = base_map.get((strength or "medium").lower().strip(), 35)
    max_odd = min_side if min_side % 2 == 1 else (min_side - 1)
    max_odd = max(3, max_odd)
    kernel = min(base, max_odd)
    if kernel % 2 == 0:
        kernel = max(3, kernel - 1)
    return kernel


def _blur_rect(img_bgr, rect: Tuple[int, int, int, int], strength: str) -> None:
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    roi = img_bgr[y : y + h, x : x + w]
    if roi.size == 0:
        return
    min_side = min(roi.shape[:2])
    if min_side < 5:
        return
    kernel = _kernel_size(strength, min_side)
    import cv2

    blurred = cv2.GaussianBlur(roi, (kernel, kernel), sigmaX=0)
    img_bgr[y : y + h, x : x + w] = blurred


def _detect_rects_with_cascade(
    gray,
    cascade_filename: str,
    scale_factor: float,
    min_neighbors: int,
    min_size: Tuple[int, int],
) -> List[Tuple[int, int, int, int]]:
    import cv2

    # 日本語ユーザーパスでOpenCV C++がファイルを開けない問題を回避:
    # プロジェクト内のASCIIパスからcascadeを読み込み、失敗時にcv2.dataへフォールバック
    local_cascade_dir = Path(__file__).resolve().parent / "cv_data"
    local_path = local_cascade_dir / cascade_filename
    if local_path.exists():
        cascade = cv2.CascadeClassifier(str(local_path))
    else:
        cascade = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / cascade_filename))
    if cascade.empty():
        logger.debug("OpenCV cascade is empty: %s", cascade_filename)
        return []
    detected = cascade.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=min_size,
    )
    return [(int(x), int(y), int(w), int(h)) for x, y, w, h in detected]


def _detect_qr_rects(img_bgr) -> List[Tuple[int, int, int, int]]:
    import cv2
    import numpy as np

    detector = cv2.QRCodeDetector()
    rects: List[Tuple[int, int, int, int]] = []

    try:
        detected, _decoded, points, _ = detector.detectAndDecodeMulti(img_bgr)
        if detected and points is not None:
            for poly in points:
                poly_arr = np.array(poly, dtype=np.float32)
                x, y, w, h = cv2.boundingRect(poly_arr)
                rects.append((int(x), int(y), int(w), int(h)))
            return rects
    except Exception as exc:
        logger.debug("QR multi detect failed", exc_info=exc)

    try:
        _decoded, points, _ = detector.detectAndDecode(img_bgr)
        if points is not None:
            poly_arr = np.array(points, dtype=np.float32)
            x, y, w, h = cv2.boundingRect(poly_arr)
            rects.append((int(x), int(y), int(w), int(h)))
    except Exception as exc:
        logger.debug("QR single detect failed", exc_info=exc)

    return rects


def _normalize_text_for_matching(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def _looks_like_personal_text(text: str) -> bool:
    normalized = _normalize_text_for_matching(text)
    if len(normalized) < 2:
        return False

    lowered = normalized.lower()
    if EMAIL_PATTERN.search(lowered):
        return True

    if PHONE_PATTERN.search(normalized):
        digits = re.sub(r"\D", "", normalized)
        if 9 <= len(digits) <= 15:
            return True

    if any(hint in lowered for hint in PERSONAL_LABEL_HINTS):
        return True

    if NAME_PATTERN_JP_SPACED.fullmatch(normalized):
        return True
    if NAME_PATTERN_EN.fullmatch(normalized):
        return True
    return False


def _scale_for_ocr(img_bgr, max_side: int = 1280):
    import cv2

    height, width = img_bgr.shape[:2]
    longest = max(height, width)
    if longest <= max_side:
        return img_bgr, 1.0

    ratio = max_side / float(longest)
    resized = cv2.resize(
        img_bgr,
        (max(1, int(width * ratio)), max(1, int(height * ratio))),
        interpolation=cv2.INTER_AREA,
    )
    return resized, (1.0 / ratio)


def _extract_text_from_ocr_item(item) -> str:
    if not isinstance(item, (list, tuple)) or len(item) < 2:
        return ""
    candidate = item[1]
    if isinstance(candidate, (list, tuple)) and candidate:
        return str(candidate[0] or "").strip()
    return str(candidate or "").strip()


def _polygon_to_rect(points, scale_back: float = 1.0) -> Tuple[int, int, int, int]:
    xs: List[float] = []
    ys: List[float] = []

    if points is None:
        return (0, 0, 0, 0)

    for point in points:
        try:
            x = float(point[0]) * scale_back
            y = float(point[1]) * scale_back
        except (TypeError, ValueError, IndexError):
            continue
        xs.append(x)
        ys.append(y)

    if not xs or not ys:
        return (0, 0, 0, 0)

    x0 = int(max(min(xs), 0))
    y0 = int(max(min(ys), 0))
    x1 = int(max(xs))
    y1 = int(max(ys))
    if x1 <= x0 or y1 <= y0:
        return (0, 0, 0, 0)
    return (x0, y0, x1 - x0, y1 - y0)


def _get_rapidocr_engine():
    global _RAPID_OCR_ENGINE
    if _RAPID_OCR_ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR

        _RAPID_OCR_ENGINE = RapidOCR()
    return _RAPID_OCR_ENGINE


def _detect_personal_text_rects(img_bgr) -> List[Tuple[int, int, int, int]]:
    scaled_img, scale_back = _scale_for_ocr(img_bgr, max_side=1280)
    engine = _get_rapidocr_engine()
    raw_result = engine(scaled_img)
    records = raw_result[0] if isinstance(raw_result, tuple) else raw_result
    if not records:
        return []

    rects: List[Tuple[int, int, int, int]] = []
    for item in records:
        text = _extract_text_from_ocr_item(item)
        if not text or not _looks_like_personal_text(text):
            continue
        points = item[0] if isinstance(item, (list, tuple)) and item else None
        rect = _polygon_to_rect(points, scale_back=scale_back)
        if rect[2] <= 0 or rect[3] <= 0:
            continue
        rects.append(rect)
    return rects


def _apply_privacy_blur(img_rgb, privacy_blur: Optional[PrivacyBlur]):
    settings = privacy_blur or PrivacyBlur()
    if not settings.enabled:
        return img_rgb

    import cv2
    import numpy as np
    from PIL import Image

    img_bgr = cv2.cvtColor(np.array(img_rgb.convert("RGB")), cv2.COLOR_RGB2BGR)
    height, width = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    candidates: List[Tuple[int, int, int, int]] = []

    if settings.blur_faces:
        candidates.extend(
            _detect_rects_with_cascade(
                gray=gray,
                cascade_filename="haarcascade_frontalface_default.xml",
                scale_factor=1.08,
                min_neighbors=5,
                min_size=(32, 32),
            )
        )

    if settings.blur_license_plates:
        candidates.extend(
            _detect_rects_with_cascade(
                gray=gray,
                cascade_filename="haarcascade_russian_plate_number.xml",
                scale_factor=1.05,
                min_neighbors=3,
                min_size=(36, 12),
            )
        )

    if settings.blur_qr_codes:
        candidates.extend(_detect_qr_rects(img_bgr))
    if settings.blur_personal_text:
        candidates.extend(_detect_personal_text_rects(img_bgr))

    if not candidates:
        return img_rgb

    for rect in candidates:
        expanded = _expand_rect(rect, width=width, height=height)
        _blur_rect(img_bgr, expanded, settings.strength)

    return Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))


def _build_image(
    image_path: str,
    filter_type: str = "none",
    gradient_type: str = "none",
    adjustment: Optional[ImageAdjustment] = None,
    overlay: Optional[TextOverlay] = None,
    configured_font_path: str = "",
    privacy_blur: Optional[PrivacyBlur] = None,
):
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    if overlay and str(overlay.background_preset or "image").strip().lower() != "image":
        img = _build_poster_background(img.size, overlay.background_preset)
    else:
        img = _apply_privacy_blur(img, privacy_blur)
        img = _apply_filter(img, filter_type)
        img = _apply_gradient(img, gradient_type)
        img = _apply_adjustments(img, adjustment or ImageAdjustment())
    if overlay and overlay.text.strip():
        img = _draw_text_overlay(img, overlay, configured_font_path)
    return img


def _save_output(
    img,
    image_path: str,
    output_dir: str | Path,
    filename_prefix: str,
) -> Path:
    out_dir = _ensure_output_dir(output_dir)
    original_name = Path(image_path).stem
    out_name = f"{original_name}_{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
    out_path = out_dir / out_name
    img.save(out_path, format="PNG")
    return out_path


def _pillow_missing_message() -> str:
    return "Pillowがインストールされていません"


def _dependency_missing_message(exc: ImportError) -> str:
    missing = str(getattr(exc, "name", "") or "").strip()
    if missing.startswith("cv2"):
        return "opencv-python-headless がインストールされていません"
    if missing.startswith("numpy"):
        return "numpy がインストールされていません"
    if missing.startswith("rapidocr_onnxruntime"):
        return "rapidocr-onnxruntime がインストールされていません"
    return _pillow_missing_message()


def _run_with_error_boundary(fn):
    try:
        return fn(), None
    except ImportError as exc:
        return None, _dependency_missing_message(exc)
    except (OSError, ValueError, RuntimeError):
        logger.exception("Image editing failed")
        return None, "画像処理でエラーが発生しました"


def apply_filter_to_image(
    image_path: str,
    filter_type: str,
    output_dir: str | Path,
) -> Tuple[Optional[Path], Optional[str]]:
    """Apply only filter and save result."""

    def _work():
        img = _build_image(image_path, filter_type=filter_type)
        return _save_output(img, image_path, output_dir, f"filter_{filter_type}")

    return _run_with_error_boundary(_work)


def apply_gradient_to_image(
    image_path: str,
    gradient_type: str,
    output_dir: str | Path,
) -> Tuple[Optional[Path], Optional[str]]:
    """Apply only gradient and save result."""

    def _work():
        img = _build_image(image_path, gradient_type=gradient_type)
        return _save_output(img, image_path, output_dir, f"grad_{gradient_type}")

    return _run_with_error_boundary(_work)


def overlay_text_on_image(
    image_path: str,
    text: str,
    position: str,
    size: str,
    color: str,
    with_bar: bool,
    configured_font_path: str,
    output_dir: str | Path,
) -> Tuple[Optional[Path], Optional[str]]:
    """Apply only text overlay and save result."""

    text_value = (text or "").strip()
    if not text_value:
        return None, "テキストを入力してください"

    def _work():
        overlay = TextOverlay(
            text=text_value,
            position=position,
            size=size,
            color=color,
            with_bar=with_bar,
        )
        img = _build_image(
            image_path,
            overlay=overlay,
            configured_font_path=configured_font_path,
        )
        suffix = "textbar" if with_bar else "text"
        return _save_output(img, image_path, output_dir, suffix)

    return _run_with_error_boundary(_work)


def render_preview(
    image_path: str,
    filter_type: str,
    gradient_type: str,
    adjustment: ImageAdjustment,
    overlay: Optional[TextOverlay],
    configured_font_path: str,
    output_dir: str | Path,
    privacy_blur: Optional[PrivacyBlur] = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """Render composed preview image and save as temporary preview file."""

    def _work():
        img = _build_image(
            image_path,
            filter_type=filter_type,
            gradient_type=gradient_type,
            adjustment=adjustment,
            overlay=overlay,
            configured_font_path=configured_font_path,
            privacy_blur=privacy_blur,
        )
        return _save_output(img, image_path, output_dir, "preview")

    return _run_with_error_boundary(_work)


def save_edited_image(
    image_path: str,
    filter_type: str,
    gradient_type: str,
    adjustment: ImageAdjustment,
    overlay: Optional[TextOverlay],
    configured_font_path: str,
    output_dir: str | Path,
    privacy_blur: Optional[PrivacyBlur] = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """Save composed edited image."""

    tokens: List[str] = []
    if filter_type and filter_type != "none":
        tokens.append(f"filter-{filter_type}")
    if gradient_type and gradient_type != "none":
        tokens.append(f"grad-{gradient_type}")

    if (
        abs(adjustment.brightness - 1.0) > 1e-3
        or abs(adjustment.contrast - 1.0) > 1e-3
        or abs(adjustment.saturation - 1.0) > 1e-3
        or abs(adjustment.sharpness - 1.0) > 1e-3
    ):
        tokens.append("adj")
    if overlay and overlay.text.strip():
        tokens.append("textbar" if overlay.with_bar else "text")
        if str(overlay.background_preset or "image").strip().lower() != "image":
            tokens.append(str(overlay.background_preset).strip().lower().replace("_", "-"))
    if privacy_blur and privacy_blur.enabled:
        tokens.append(f"privacy-{privacy_blur.strength}")
    suffix = "edit"
    if tokens:
        suffix = f"edit_{'_'.join(tokens)}"

    def _work():
        img = _build_image(
            image_path,
            filter_type=filter_type,
            gradient_type=gradient_type,
            adjustment=adjustment,
            overlay=overlay,
            configured_font_path=configured_font_path,
            privacy_blur=privacy_blur,
        )
        return _save_output(img, image_path, output_dir, suffix)

    return _run_with_error_boundary(_work)
