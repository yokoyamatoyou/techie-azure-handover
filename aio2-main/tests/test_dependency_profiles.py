from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _requirements_lines(path: Path) -> set[str]:
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def test_windows_profile_includes_docx_export_dependency() -> None:
    canonical = _requirements_lines(ROOT / "requirements.txt")
    windows = _requirements_lines(ROOT / "requirements-windows.txt")

    assert "python-docx==1.2.0" in canonical
    assert "python-docx==1.2.0" in windows


def test_windows_profile_includes_nicegui_startup_dependencies() -> None:
    canonical = _requirements_lines(ROOT / "requirements.txt")
    windows = _requirements_lines(ROOT / "requirements-windows.txt")

    assert "html-sanitizer==2.6.0" in canonical
    assert "html-sanitizer==2.6.0" in windows
