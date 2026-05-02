# -*- coding: utf-8 -*-
"""Doorknock Tool: 2-page PDF generator (fpdf2).

Page 1: Trimmed logo (large) + catch copy + SEO / LLMO as big graphical numbers
Page 2: Rewrite Before/After + AIO detail scores (mystery hook) + agent space
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fpdf import FPDF

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # C:\tetie
_AIO2_ROOT = _PROJECT_ROOT / "aio2-main"
_FONT_DIR = _AIO2_ROOT / "PDFreport" / "fonts"
_LOGO_TRIMMED = Path(__file__).resolve().parent / "assets" / "logo_trimmed.png"
_LOGO_FALLBACK = _PROJECT_ROOT / "ロゴ１.png"
_OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# ---------------------------------------------------------------------------
# Brand colours (RGB tuples)
# ---------------------------------------------------------------------------
COLOR_ORANGE = (232, 68, 36)       # #E84424
COLOR_DARK = (36, 24, 19)          # #241813
COLOR_GREY = (136, 136, 136)       # #888888
COLOR_LIGHT_GREY = (220, 220, 220)
COLOR_WHITE = (255, 255, 255)
COLOR_RED_STRIKE = (200, 60, 60)
COLOR_BG_BEFORE = (255, 245, 245)
COLOR_BG_AFTER = (245, 255, 245)
COLOR_PAGE_BG = (253, 247, 243)    # light pink-beige from UI


def _logo_path() -> Optional[Path]:
    """Return best available logo path (trimmed preferred)."""
    if _LOGO_TRIMMED.exists():
        return _LOGO_TRIMMED
    if _LOGO_FALLBACK.exists():
        return _LOGO_FALLBACK
    return None


def _setup_fonts(pdf: FPDF) -> str:
    """Register Noto Sans JP and return the family name to use."""
    regular = _FONT_DIR / "NotoSansJP-Regular.ttf"
    bold = _FONT_DIR / "NotoSansJP-Bold.ttf"
    if regular.exists() and bold.exists():
        pdf.add_font("NotoSansJP", "", str(regular), uni=True)
        pdf.add_font("NotoSansJP", "B", str(bold), uni=True)
        return "NotoSansJP"
    return "Helvetica"


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_big_score(
    pdf: FPDF,
    cx: float,
    y: float,
    label: str,
    score: float,
    color: tuple,
    font: str,
) -> None:
    """Draw a score as a huge number with label underneath, centred at cx."""
    score_str = str(int(round(score)))
    # Huge number (121pt = ~230% of original 52pt)
    pdf.set_font(font, "B", 121)
    pdf.set_text_color(*color)
    sw = pdf.get_string_width(score_str)
    pdf.set_xy(cx - sw / 2, y)
    pdf.cell(sw, 50, score_str, align="C")
    # Label underneath
    pdf.set_font(font, "B", 24)
    pdf.set_text_color(*COLOR_DARK)
    lw = pdf.get_string_width(label)
    pdf.set_xy(cx - lw / 2, y + 52)
    pdf.cell(lw, 12, label, align="C")


def _draw_before_box(
    pdf: FPDF, x: float, y: float, w: float, text: str, font: str,
) -> float:
    """Draw Before box with red strikethrough text. Returns bottom y."""
    pdf.set_xy(x, y)
    pdf.set_font(font, "B", 10)
    pdf.set_text_color(*COLOR_RED_STRIKE)
    pdf.cell(30, 6, "Before")

    box_y = y + 8
    clipped = text[:180] + ("..." if len(text) > 180 else "")
    # Measure height needed
    lines = pdf.multi_cell(w - 10, 5, clipped, dry_run=True, output="LINES")
    num_lines = len(lines) if lines else 3
    box_h = max(num_lines * 5 + 8, 22)

    pdf.set_fill_color(*COLOR_BG_BEFORE)
    pdf.set_draw_color(*COLOR_RED_STRIKE)
    pdf.set_line_width(0.4)
    pdf.rect(x, box_y, w, box_h, "DF")

    pdf.set_xy(x + 5, box_y + 4)
    pdf.set_font(font, "", 9.5)
    pdf.set_text_color(*COLOR_RED_STRIKE)
    pdf.multi_cell(w - 10, 5, clipped)

    # Strikethrough lines
    pdf.set_draw_color(*COLOR_RED_STRIKE)
    pdf.set_line_width(0.25)
    for i in range(num_lines):
        ly = box_y + 6.5 + i * 5
        if ly < box_y + box_h - 2:
            pdf.line(x + 5, ly, x + w - 5, ly)

    return box_y + box_h


def _draw_after_box(
    pdf: FPDF, x: float, y: float, w: float, text: str, font: str,
) -> float:
    """Draw After box with bold highlighted text. Returns bottom y."""
    pdf.set_xy(x, y)
    pdf.set_font(font, "B", 10)
    pdf.set_text_color(*COLOR_ORANGE)
    pdf.cell(30, 6, "After")

    box_y = y + 8
    clipped = text[:180] + ("..." if len(text) > 180 else "")
    lines = pdf.multi_cell(w - 10, 5, clipped, dry_run=True, output="LINES")
    num_lines = len(lines) if lines else 3
    box_h = max(num_lines * 5 + 8, 22)

    pdf.set_fill_color(*COLOR_BG_AFTER)
    pdf.set_draw_color(*COLOR_ORANGE)
    pdf.set_line_width(0.6)
    pdf.rect(x, box_y, w, box_h, "DF")

    pdf.set_xy(x + 5, box_y + 4)
    pdf.set_font(font, "B", 9.5)
    pdf.set_text_color(*COLOR_DARK)
    pdf.multi_cell(w - 10, 5, clipped)

    return box_y + box_h


def _score_color(score: float) -> tuple:
    """Return colour based on score value."""
    if score >= 70:
        return (60, 160, 60)   # green
    elif score >= 40:
        return COLOR_ORANGE
    else:
        return COLOR_RED_STRIKE


def _draw_score_card(
    pdf: FPDF, x: float, y: float, w: float, h: float,
    label: str, score: float, font: str,
) -> None:
    """Draw a single score card: rounded-feel box with big number + label."""
    color = _score_color(score)
    # Card background (very light grey)
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(*COLOR_LIGHT_GREY)
    pdf.set_line_width(0.3)
    pdf.rect(x, y, w, h, "DF")
    # Colour accent bar at top of card
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, 2.5, "F")
    # Big score number
    score_str = str(int(round(score)))
    pdf.set_font(font, "B", 28)
    pdf.set_text_color(*color)
    pdf.set_xy(x, y + 6)
    pdf.cell(w, 14, score_str, align="C")
    # Label (smaller, dark)
    pdf.set_font(font, "", 8)
    pdf.set_text_color(*COLOR_DARK)
    pdf.set_xy(x, y + h - 12)
    pdf.cell(w, 8, label, align="C")


# ===================================================================
# Public API
# ===================================================================

def generate_doorknock_pdf(
    analysis_results: Dict[str, Any],
    agent_name: str = "",
    output_path: Optional[Path] = None,
) -> Path:
    """Generate a 2-page doorknock PDF and return the file path."""
    # --- Extract data ------------------------------------------------
    url = analysis_results.get("url", "")
    integrated = analysis_results.get("integrated_results", {})
    seo_score = float(integrated.get("seo_score", 0))
    aio_score = float(integrated.get("aio_score", 0))

    # AIO detail scores (for mystery hook on page 2)
    aio_results = analysis_results.get("aio_results", {})
    aio_scores = aio_results.get("scores", {})

    # orchestrator returns UI-formatted scores: {"pid_density": {"score": 42.3, ...}}
    # Fallback to raw aio_analyzer keys if flat numbers exist
    # Apply TOTAL penalty so page 2 scores match page 1's LLMO.
    # Two penalty layers exist:
    #   1) aio_analyzer penalty (e.g. no JSON-LD) → already in aio_results.total_score
    #   2) ScoringEngine penalty (e.g. domain mismatch) → only in integrated_results.aio_score
    # Derive effective multiplier: integrated aio_score / aio raw_score
    aio_raw = float(aio_results.get("raw_score", 0) or 0)
    aio_final = float(integrated.get("aio_score", 0) or 0)  # page 1 LLMO value
    if aio_raw > 0:
        penalty_mult = aio_final / aio_raw
    else:
        penalty_mult = float(aio_results.get("penalty_multiplier", 1.0) or 1.0)

    def _get_aio_score(ui_key: str, raw_key: str) -> float:
        val = aio_scores.get(ui_key, {})
        if isinstance(val, dict):
            raw = float(val.get("score", 0))
        else:
            raw = float(aio_scores.get(raw_key, 0))
        return round(raw * penalty_mult, 1)

    detail_items: List[Tuple[str, float]] = [
        ("命題密度 (PID)", _get_aio_score("pid_density", "pid_score")),
        ("構造化・文書パース性", _get_aio_score("structure", "structure_score")),
        ("エンティティ重要度", _get_aio_score("entity_salience", "entity_score")),
        ("技術的AIO適合性", _get_aio_score("technical", "tech_score")),
    ]
    # Also pull enhanced metrics if available (also penalized)
    breakdown = aio_results.get("score_breakdown", {})
    enhanced = breakdown.get("enhanced_metrics", {})
    if enhanced.get("citation", 0) > 0:
        detail_items.append(("引用準備度", round(float(enhanced["citation"]) * 100 * penalty_mult, 1)))
    if enhanced.get("freshness", 0) > 0:
        detail_items.append(("情報鮮度シグナル", round(float(enhanced["freshness"]) * 100 * penalty_mult, 1)))

    # Rewrite data — try multiple sources in priority order
    rewrite_before = ""
    rewrite_after = ""
    rewrite_reason = ""

    # Source 1: aio_results.rewrite_suggestions (always populated by aio_suggester)
    rewrite_suggestions = aio_results.get("rewrite_suggestions", []) or []
    for sugg in rewrite_suggestions:
        orig = sugg.get("original_segment", "") or sugg.get("original", "")
        improved = sugg.get("improved_segment", "") or sugg.get("improved", "")
        if orig and improved:
            rewrite_before = orig
            rewrite_after = improved
            rewrite_reason = sugg.get("reason", "")
            break

    # Source 2: deep_recommendations (LLM-generated)
    if not rewrite_before:
        deep_recs = analysis_results.get("deep_recommendations", {}) or {}
        biz_recs = deep_recs.get("business", []) or []
        tech_recs = deep_recs.get("technical", []) or []
        all_recs = biz_recs + tech_recs
        for rec in all_recs:
            before = (rec.get("current_state", "") or rec.get("current_issue", "")
                      or rec.get("current", ""))
            after = (rec.get("recommended_action", "") or rec.get("implementation", "")
                     or rec.get("recommendation", ""))
            if before and after:
                rewrite_before = before
                rewrite_after = after
                rewrite_reason = rec.get("reason", "") or rec.get("expected_impact", "")
                break

    if not rewrite_before:
        rewrite_before = "（現在のページ本文から自動抽出）"
        rewrite_after = "（AI引用されやすい表現に改善した例をここに表示）"

    # --- PDF setup ---------------------------------------------------
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    font = _setup_fonts(pdf)

    W = 210
    H = 297
    MARGIN = 25
    content_w = W - 2 * MARGIN

    # =================================================================
    # PAGE 1 — Trimmed logo + catch copy + URL + big score numbers
    # =================================================================
    pdf.add_page()
    # Page background
    pdf.set_fill_color(*COLOR_PAGE_BG)
    pdf.rect(0, 0, W, H, "F")

    logo = _logo_path()
    if logo:
        logo_w = 130
        logo_x = (W - logo_w) / 2
        pdf.image(str(logo), x=logo_x, y=22, w=logo_w)

    # TECHIE tagline under logo
    pdf.set_xy(MARGIN, 58)
    pdf.set_font(font, "", 10)
    pdf.set_text_color(*COLOR_GREY)
    pdf.cell(content_w, 6, "TECHIE \u2014 \u30b3\u30c8\u30d0\u3092\u78e8\u304d\u3001\u898b\u3064\u304b\u308b\u30b5\u30a4\u30c8\u3078", align="C")

    # Catch copy (23pt = 130% of 18pt)
    pdf.set_xy(MARGIN, 78)
    pdf.set_font(font, "B", 23)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(content_w, 14, "あなたのサイト、", align="C", ln=True)
    pdf.set_x(MARGIN)
    pdf.set_font(font, "B", 23)
    pdf.set_text_color(*COLOR_ORANGE)
    pdf.cell(content_w, 14, "AI検索で見つかりますか？", align="C", ln=True)

    # Thin accent line
    line_y = 114
    pdf.set_draw_color(*COLOR_ORANGE)
    pdf.set_line_width(0.8)
    pdf.line(W / 2 - 30, line_y, W / 2 + 30, line_y)

    # Target URL — right below the accent line
    display_url = url if len(url) <= 65 else url[:62] + "..."
    pdf.set_xy(MARGIN, line_y + 5)
    pdf.set_font(font, "", 10)
    pdf.set_text_color(*COLOR_GREY)
    pdf.cell(content_w, 6, display_url, align="C", ln=True)
    # Date
    pdf.set_x(MARGIN)
    pdf.set_font(font, "", 8)
    pdf.cell(content_w, 5, datetime.now().strftime("%Y.%m.%d"), align="C")

    # Big scores — side by side, pushed down for max impact
    score_y = 165
    left_cx = W * 0.28
    right_cx = W * 0.72

    _draw_big_score(pdf, left_cx, score_y, "SEO", seo_score, COLOR_DARK, font)
    _draw_big_score(pdf, right_cx, score_y, "LLMO", aio_score, COLOR_ORANGE, font)

    # Divider between scores
    pdf.set_draw_color(*COLOR_LIGHT_GREY)
    pdf.set_line_width(0.3)
    pdf.line(W / 2, score_y + 12, W / 2, score_y + 56)

    # =================================================================
    # PAGE 2 — Rewrite + Detail grid + Agent space
    # =================================================================
    pdf.add_page()
    # Page background
    pdf.set_fill_color(*COLOR_PAGE_BG)
    pdf.rect(0, 0, W, H, "F")

    # --- Rewrite section ---
    y = 15
    pdf.set_xy(MARGIN, y)
    pdf.set_font(font, "B", 12)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(content_w, 7, "リライト提案", ln=True)

    before_bottom = _draw_before_box(pdf, MARGIN, y + 10, content_w, rewrite_before, font)

    # Arrow
    arrow_y = before_bottom + 2
    pdf.set_xy(W / 2 - 5, arrow_y)
    pdf.set_font(font, "B", 18)
    pdf.set_text_color(*COLOR_ORANGE)
    pdf.cell(10, 8, chr(0x2193), align="C")

    after_bottom = _draw_after_box(pdf, MARGIN, arrow_y + 9, content_w, rewrite_after, font)

    # Reason
    if rewrite_reason:
        pdf.set_xy(MARGIN, after_bottom + 2)
        pdf.set_font(font, "", 8)
        pdf.set_text_color(*COLOR_GREY)
        pdf.multi_cell(content_w, 4, f"理由: {rewrite_reason[:80]}")

    # --- AIO Detail grid (2 cols × 3 rows) ---
    grid_y = after_bottom + 14
    pdf.set_draw_color(*COLOR_LIGHT_GREY)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN, grid_y, W - MARGIN, grid_y)

    grid_y += 4
    pdf.set_xy(MARGIN, grid_y)
    pdf.set_font(font, "B", 11)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(content_w, 7, "AI検索 詳細スコア", ln=True)

    # Ensure exactly 6 items for 2×3 grid
    grid_items = detail_items[:6]
    while len(grid_items) < 6:
        grid_items.append(("-", 0))

    card_gap = 6
    card_w = (content_w - card_gap) / 2
    card_h = 32
    row_gap = 6
    start_y = grid_y + 10

    for idx, (label, score) in enumerate(grid_items):
        col = idx % 2
        row = idx // 2
        cx = MARGIN + col * (card_w + card_gap)
        cy = start_y + row * (card_h + row_gap)
        _draw_score_card(pdf, cx, cy, card_w, card_h, label, score, font)

    # --- Agent name space (bottom) ---
    agent_area_y = H - 45
    pdf.set_draw_color(*COLOR_LIGHT_GREY)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN, agent_area_y, W - MARGIN, agent_area_y)

    pdf.set_xy(MARGIN, agent_area_y + 5)
    pdf.set_font(font, "", 9)
    pdf.set_text_color(*COLOR_GREY)
    pdf.cell(content_w, 5, "お問い合わせ", align="L", ln=True)

    # Dotted line for handwriting
    line_y = agent_area_y + 16
    pdf.set_draw_color(*COLOR_LIGHT_GREY)
    pdf.set_line_width(0.2)
    pdf.dashed_line(MARGIN, line_y, W - MARGIN, line_y, dash_length=2, space_length=2)

    if agent_name:
        pdf.set_xy(MARGIN, agent_area_y + 10)
        pdf.set_font(font, "", 11)
        pdf.set_text_color(*COLOR_DARK)
        pdf.cell(content_w, 6, agent_name, align="L")

    # Company credit
    pdf.set_xy(W - MARGIN - 50, H - 15)
    pdf.set_font(font, "", 7)
    pdf.set_text_color(*COLOR_GREY)
    pdf.cell(50, 5, "kyotokogyo.co.jp", align="R")

    # --- Save --------------------------------------------------------
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        safe_url = "".join(c if c.isalnum() else "_" for c in url[:40])
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = _OUTPUT_DIR / f"doorknock_{safe_url}_{ts}.pdf"

    pdf.output(str(output_path))
    return output_path
