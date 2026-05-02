# -*- coding: utf-8 -*-
"""Doorknock Tool: URL → Analysis → 2-page PDF.

Usage:
    python doorknock_app.py <URL> [--agent "代理店名"]

Requires aio2-main's venv (run with aio2-main/.venv/Scripts/python.exe).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Add aio2-main to sys.path so we can import its core modules directly
# ---------------------------------------------------------------------------
_AIO2_ROOT = Path(__file__).resolve().parent.parent / "aio2-main"
if str(_AIO2_ROOT) not in sys.path:
    sys.path.insert(0, str(_AIO2_ROOT))

from core.engine.orchestrator import SEOAIOAnalyzer  # noqa: E402
from doorknock_pdf import generate_doorknock_pdf      # noqa: E402


def run(url: str, agent_name: str = "") -> Path:
    """Run analysis and generate doorknock PDF."""
    print(f"\n[doorknock] 対象URL: {url}")
    print("[doorknock] 分析を開始します...\n")

    analyzer = SEOAIOAnalyzer(analysis_mode="standard")

    results = analyzer.analyze_url(
        url=url,
        user_industry="",          # auto-detect
        balance=50,                 # SEO/AIO even
        deep_mode=False,            # lightweight
        platform_override=None,     # auto-detect
        enable_question_simulation=False,
        url_type_selected="自動判定",
    )

    print("\n[doorknock] 分析完了。PDFを生成します...")

    pdf_path = generate_doorknock_pdf(
        analysis_results=results,
        agent_name=agent_name,
    )

    print(f"[doorknock] PDF生成完了: {pdf_path}\n")
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Doorknock診断ツール")
    parser.add_argument("url", help="診断対象のURL")
    parser.add_argument("--agent", default="", help="代理店名（PDFフッターに表示）")
    args = parser.parse_args()

    try:
        pdf_path = run(args.url, args.agent)
        print(f"完了！ PDF: {pdf_path}")
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
