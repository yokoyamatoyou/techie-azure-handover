"""Fetch failure display helpers for note_writer_app."""
from __future__ import annotations

from typing import Any, List

from note.note_writer_app_generation_delay_display import _build_generation_delay_notice


def _classify_reason_code(reason_code: str) -> str:
    code = str(reason_code or "").strip().upper()
    if code.startswith("INP_"):
        return "user_input"
    if code.startswith(("POL_", "SEC_")):
        return "policy"
    if code.startswith("TRN_"):
        return "transient"
    return "system"


def _format_fetch_failures(failures: List[Any]) -> str:
    if not failures:
        return ""
    labels = {
        "robots_blocked": ("E-ROBOTS", "robots.txtにより取得できません"),
        "invalid_or_unsafe_url": ("E-URL", "URL形式または安全性の検証で失敗しました"),
        "redirect_not_supported": ("E-REDIRECT", "リダイレクトURLは未対応です"),
        "http_403_forbidden": ("E-403", "アクセス拒否のため取得できません"),
        "http_error": ("E-HTTP", "HTTPエラーで取得できません"),
        "network_error": ("E-NET", "通信エラーで取得できません"),
        "unauthorized_file_path": ("E-PATH", "許可外のファイルパスです"),
        "file_not_found": ("E-FILE", "ファイルが見つかりません"),
        "pdf_extractor_missing": ("E-PDF-LIB", "PDF抽出ライブラリが見つかりません"),
        "pdf_no_text": ("E-PDF-TEXT", "PDFから抽出可能なテキストが見つかりません"),
        "pdf_parse_failed": ("E-PDF-PARSE", "PDFの解析に失敗しました"),
        "docx_extractor_missing": ("E-DOCX-LIB", "DOCX抽出ライブラリが見つかりません"),
        "docx_no_text": ("E-DOCX-TEXT", "DOCXから抽出可能なテキストが見つかりません"),
        "docx_parse_failed": ("E-DOCX-PARSE", "DOCXの解析に失敗しました"),
        "fetch_failed": ("E-FETCH", "ソース取得に失敗しました"),
    }
    recovery = {
        "robots_blocked": "公開資料を手動でPDF化してアップロードするか、取得可能な公式資料URLに変更してください。",
        "invalid_or_unsafe_url": "URLをコピーし直し、http/https・ホスト名・末尾記号を確認してください。",
        "redirect_not_supported": "最終到達URL（リダイレクト先）を直接入力してください。",
        "http_403_forbidden": "ブラウザで閲覧可能な場合は、必要箇所をPDF化してファイル入力してください。",
        "http_error": "URLが生きているか確認し、時間をおいて再試行してください。",
        "network_error": "ネットワーク状態を確認し、再試行してください。",
        "unauthorized_file_path": "アップロード機能からファイルを再選択してください。",
        "file_not_found": "ファイルの場所を確認し、再アップロードしてください。",
        "pdf_extractor_missing": "実行中のPython環境にpdfplumber/pypdfをインストールしてください。",
        "pdf_no_text": "OCR済みPDFかテキスト入りPDFを使用してください（スキャン画像PDFは不可）。",
        "pdf_parse_failed": "PDFを開き直して再保存するか、別形式（txt/md）で投入してください。",
        "docx_extractor_missing": "実行中のPython環境にpython-docxをインストールしてください。",
        "docx_no_text": "本文テキストを含むDOCXを使用してください（図のみ文書は不可）。",
        "docx_parse_failed": "DOCXを開き直して再保存するか、別形式（txt/md）で投入してください。",
        "fetch_failed": "入力ソースを見直して再試行してください。",
    }
    lines: List[str] = []
    for failure in failures[:5]:
        reason_key = getattr(failure, "reason", "")
        detail = getattr(failure, "detail", "") or ""
        if reason_key in {"fetch_failed", "", None}:
            lowered = detail.lower()
            if "pdf extractor not available" in lowered:
                reason_key = "pdf_extractor_missing"
            elif "no extractable text found in pdf" in lowered:
                reason_key = "pdf_no_text"
            elif "pdf parsing failed" in lowered:
                reason_key = "pdf_parse_failed"
            elif "docx extractor not available" in lowered:
                reason_key = "docx_extractor_missing"
            elif "no extractable text found in docx" in lowered:
                reason_key = "docx_no_text"
            elif "docx parsing failed" in lowered:
                reason_key = "docx_parse_failed"
        _code, reason = labels.get(reason_key, ("E-UNKNOWN", "取得失敗"))
        source = getattr(failure, "source", "unknown")
        step = recovery.get(reason_key, "入力を見直して再試行してください。")
        lines.append(f"- {reason}\n  対象: {source}\n  詳細: {detail}\n  対処: {step}")
    if len(failures) > 5:
        lines.append(f"- ...他 {len(failures) - 5} 件")
    return "\n".join(lines)


def _extract_403_urls(failures: List[Any]) -> List[str]:
    urls: List[str] = []
    for failure in failures or []:
        reason = getattr(failure, "reason", "")
        source = (getattr(failure, "source", "") or "").strip()
        if reason == "http_403_forbidden" and source.startswith(("http://", "https://")) and source not in urls:
            urls.append(source)
    return urls


def _collect_source_notices(contexts: List[Any]) -> List[str]:
    notices: List[str] = []
    for ctx in contexts or []:
        source_label = (
            getattr(ctx, "title", None)
            or getattr(ctx, "source_path", None)
            or getattr(ctx, "url", None)
            or "ソース"
        )
        for note in (getattr(ctx, "notices", None) or []):
            note_text = str(note).strip()
            if note_text:
                notices.append(f"{source_label}: {note_text}")
    return notices[:5]


def _prepare_current_mainline_fetch_summary(
    *,
    contents: List[Any],
    failures: List[Any],
    elapsed_ms: int,
) -> dict[str, Any]:
    total_source_chars = sum(len(getattr(content, "content", "") or "") for content in contents)
    return {
        "success_count": len(contents),
        "failure_count": len(failures),
        "elapsed_ms": int(elapsed_ms),
        "total_source_chars": total_source_chars,
        "event_extra": {
            "success_count": len(contents),
            "failure_count": len(failures),
            "elapsed_ms": int(elapsed_ms),
            "total_source_chars": total_source_chars,
        },
        "post_delay_notice": _build_generation_delay_notice(len(contents), total_source_chars),
        "failure_details": _format_fetch_failures(failures),
        "blocked_urls": _extract_403_urls(failures),
    }
