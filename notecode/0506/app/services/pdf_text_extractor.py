from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader


@dataclass(frozen=True)
class PdfTextExtraction:
    spans: list[tuple[str, str, str]]
    metadata: dict[str, Any]
    warnings: list[str]


def extract_pdf_text(path: Path) -> PdfTextExtraction:
    try:
        return _extract_with_pymupdf(path)
    except Exception as exc:
        fallback = _extract_with_pypdf(path)
        return PdfTextExtraction(
            spans=fallback.spans,
            metadata={**fallback.metadata, "pymupdf_error": str(exc)},
            warnings=[*fallback.warnings, "PyMuPDF extraction failed; used pypdf fallback"],
        )


def _extract_with_pymupdf(path: Path) -> PdfTextExtraction:
    import fitz

    spans: list[tuple[str, str, str]] = []
    image_pages = 0
    with fitz.open(str(path)) as document:
        for page_index, page in enumerate(document, start=1):
            blocks = page.get_text("blocks", sort=True)
            lines: list[str] = []
            for block in blocks:
                text = _clean_pdf_block(str(block[4]))
                if text:
                    lines.append(text)
            if page.get_images(full=True):
                image_pages += 1
            page_text = "\n".join(lines).strip()
            if page_text:
                spans.append((f"pdf_{page_index:03d}", page_text, f"p.{page_index}"))
        page_count = document.page_count

    warnings = []
    if image_pages:
        warnings.append(f"PDF contains images on {image_pages} pages; text layer was extracted without OCR")
    return PdfTextExtraction(
        spans=spans,
        metadata={
            "extraction_method": "pymupdf_text_blocks",
            "page_count": page_count,
            "image_page_count": image_pages,
        },
        warnings=warnings,
    )


def _extract_with_pypdf(path: Path) -> PdfTextExtraction:
    reader = PdfReader(str(path))
    spans: list[tuple[str, str, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = _clean_pdf_block(page.extract_text() or "")
        if page_text:
            spans.append((f"pdf_{index:03d}", page_text, f"p.{index}"))
    return PdfTextExtraction(
        spans=spans,
        metadata={"extraction_method": "pdf_text", "page_count": len(reader.pages), "image_page_count": None},
        warnings=[],
    )


def _clean_pdf_block(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        raw_line = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw_line)
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        lines.append(line)
    return "\n".join(lines)
