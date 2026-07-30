from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "kotomigaki_radar_ui.png"


W, H = 1600, 1000
BG = "#f7f4ee"
INK = "#2b3036"
MUTED = "#68737d"
TEAL = "#15958e"
TEAL_DARK = "#0f6f6b"
AMBER = "#f2a51a"
GREEN = "#55aa4a"
BLUE = "#3f73b8"
CARD = "#fffdf8"
LINE = "#dfd7ca"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/YuGothB.ttc" if bold else "C:/Windows/Fonts/YuGothM.ttc"
    return ImageFont.truetype(path, size=size, index=0)


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy, value: str, size: int, fill=INK, bold=False, anchor=None):
    draw.text(xy, value, font=font(size, bold), fill=fill, anchor=anchor)


def pill(draw: ImageDraw.ImageDraw, box, label: str, fill: str, fg="#ffffff", size=24):
    rounded(draw, box, 24, fill)
    x0, y0, x1, y1 = box
    text(draw, ((x0 + x1) / 2, (y0 + y1) / 2 - 1), label, size, fg, True, "mm")


def wrapped_text(draw: ImageDraw.ImageDraw, x: int, y: int, value: str, max_chars: int, size: int, fill=INK):
    lines = []
    line = ""
    for ch in value:
        line += ch
        if len(line) >= max_chars:
            lines.append(line)
            line = ""
    if line:
        lines.append(line)
    for i, line in enumerate(lines):
        text(draw, (x, y + i * (size + 8)), line, size, fill)


def radar(draw: ImageDraw.ImageDraw, center, radius: int, labels, values):
    cx, cy = center
    n = len(labels)
    angles = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]

    for step in range(1, 6):
        r = radius * step / 5
        pts = [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in angles]
        draw.line(pts + [pts[0]], fill="#d8e3df", width=2)

    for a in angles:
        draw.line((cx, cy, cx + math.cos(a) * radius, cy + math.sin(a) * radius), fill="#d8e3df", width=2)

    poly = []
    for a, v in zip(angles, values):
        r = radius * v / 100
        poly.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    draw.polygon(poly, fill=(21, 149, 142, 92), outline=TEAL)
    draw.line(poly + [poly[0]], fill=TEAL_DARK, width=5)

    for (x, y), v in zip(poly, values):
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=TEAL_DARK)

    for a, label in zip(angles, labels):
        lx = cx + math.cos(a) * (radius + 92)
        ly = cy + math.sin(a) * (radius + 68)
        anchor = "mm"
        if math.cos(a) < -0.3:
            anchor = "rm"
        elif math.cos(a) > 0.3:
            anchor = "lm"
        text(draw, (lx, ly), label, 25, INK, True, anchor)


def draw_icon_check(draw, x, y, color):
    draw.ellipse((x, y, x + 48, y + 48), fill=color)
    draw.line((x + 13, y + 25, x + 21, y + 33, x + 36, y + 16), fill="white", width=5, joint="curve")


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img, "RGBA")

    rounded(draw, (70, 56, 1530, 928), 34, CARD, "#e2d8c9", 2)
    rounded(draw, (100, 88, 1500, 176), 26, "#ffffff", "#eadfce", 2)
    text(draw, (134, 124), "TECHIE / コトミガキ", 30, TEAL_DARK, True)
    text(draw, (134, 158), "URLを入れるだけのホームページ健康診断", 23, MUTED)
    pill(draw, (1120, 112, 1300, 154), "1回 1,000円", TEAL)
    pill(draw, (1318, 112, 1466, 154), "15回 9,000円", AMBER)

    rounded(draw, (116, 214, 1458, 284), 28, "#fbfaf6", "#e4dacb", 2)
    text(draw, (152, 249), "https://example.co.jp", 27, "#46525c")
    rounded(draw, (1214, 226, 1428, 272), 23, TEAL, None)
    text(draw, (1321, 249), "診断する", 25, "#ffffff", True, "mm")

    rounded(draw, (114, 326, 880, 856), 28, "#ffffff", "#e5ddcf", 2)
    text(draw, (152, 372), "6軸 改善マップ", 36, INK, True)
    text(draw, (152, 414), "検索・ChatGPT・使いやすさ・サイトの弱点を一画面で確認", 23, MUTED)
    radar(
        draw,
        (505, 620),
        198,
        ["検索基礎", "ChatGPT", "信頼情報", "公開条件", "保守・技術", "使いやすさ"],
        [76, 64, 70, 58, 46, 62],
    )

    rounded(draw, (934, 326, 1458, 856), 28, "#ffffff", "#e5ddcf", 2)
    text(draw, (976, 374), "診断結果サマリー", 36, INK, True)
    items = [
        (GREEN, "すぐ直す", "サイトの弱点(セキュリティの穴)を確認"),
        (TEAL, "伸ばす", "ChatGPTに紹介されやすい情報整理"),
        (BLUE, "見直す", "スマホで読みやすい文字・ボタン"),
        (AMBER, "渡せる", "制作会社へ送れる改善リスト"),
    ]
    y = 438
    for color, tag, label in items:
        draw_icon_check(draw, 980, y - 16, color)
        pill(draw, (1044, y - 10, 1138, y + 34), tag, color, "#ffffff", 21)
        wrapped_text(draw, 1160, y - 2, label, 17, 22, INK)
        y += 98

    rounded(draw, (976, 782, 1418, 824), 21, "#f7fbfa", "#d7e8e5", 1)
    text(draw, (1197, 803), "専門用語のない改善レポート", 23, TEAL_DARK, True, "mm")

    img.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
