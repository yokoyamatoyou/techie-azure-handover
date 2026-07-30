"""Deterministic screening of URL strings before they become fetch or AI inputs.

The guard deliberately returns only structured, masked observations.  It is not a
web-vulnerability detector and never interprets foreign-language text by itself
as unsafe.
"""

from __future__ import annotations

import base64
from hashlib import sha256
import html
import re
import time
import unicodedata
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import parse_qsl, unquote_plus, urlsplit


MAX_URL_LENGTH = 8192
MAX_VALUE_LENGTH = 2048
MAX_DECODED_LENGTH = 2048
MAX_VALUES = 32
MAX_DECODE_LAYERS = 2
MAX_PROCESSING_MS = 40

_SENSITIVE_QUERY_KEYS = {"token", "access_token", "id_token", "jwt", "api_key", "apikey", "key", "signature", "sig", "auth"}
_ZERO_WIDTH_RE = re.compile("[\\u200b-\\u200f\\u2060\\ufeff]")
_BIDI_RE = re.compile("[\\u202a-\\u202e\\u2066-\\u2069]")
_ESCAPED_UNICODE_RE = re.compile(r"\\\\u([0-9a-fA-F]{4})")
_BASE64_RE = re.compile(r"[A-Za-z0-9+/]{8,252}={0,2}")
_HEX_RE = re.compile(r"[0-9a-fA-F]{8,128}")
_CONFUSABLES = str.maketrans({"а": "a", "е": "e", "і": "i", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "Α": "A", "Β": "B", "Ε": "E", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Χ": "X"})

_OVERRIDE_PATTERNS = (r"ignore (?:all |any |the )?(?:previous|prior|above) instructions?", r"disregard (?:previous|prior) instructions?", r"以前の指示を無視", r"指示を無視", r"忽略(?:之前|先前)?指令", r"이전 지시(?:를)? 무시")
_PROMPT_PATTERNS = (r"(?:system|developer)\s*(?:prompt|message|instructions?)", r"\b(?:ai|assistant|system|prompt|tool)\b", r"システム(?:プロンプト|指示)", r"開発者(?:プロンプト|指示)", r"系统(?:提示|指令)", r"시스템\s*(?:프롬프트|지시)")
_SECRET_PATTERNS = (r"\b(?:cookie|api[ _-]?key|secret|environment variable|env(?:ironment)?|password)\b", r"(?:秘密情報|環境変数|APIキー|クッキー)", r"(?:密钥|环境变量|cookie)", r"(?:비밀|환경 변수|api 키|쿠키)")
_EXFIL_PATTERNS = (r"\b(?:send|upload|exfiltrat(?:e|ion)|post)\b.*\b(?:to|http|url|server)\b", r"(?:外部(?:URL|へ)|送信|持ち出し)", r"(?:发送|上传|外部网址)", r"(?:전송|업로드|외부 url)")
_TOOL_PATTERNS = (r"\b(?:run|execute|use)\b.*\b(?:tool|command|shell|file|fetch|open)\b", r"(?:ツール実行|ファイル操作|追加(?:URL|取得))", r"(?:执行工具|读取文件|获取(?:额外)?网址)", r"(?:도구 실행|파일 작업|추가 url(?: 가져오기)?)")


def inspect_url_for_untrusted_instruction(url: str, *, link_text: str = "") -> Dict[str, Any]:
    """Return a bounded, payload-free URL instruction screening result."""
    started = time.monotonic()
    raw = str(url or "")
    if len(raw) > MAX_URL_LENGTH:
        return _result("suspicious_untrusted_instruction", "url", ("input_length_limit",), 0, started)
    parsed = urlsplit(raw)
    values: List[Tuple[str, str, bool]] = [("path", parsed.path, False), ("fragment", parsed.fragment, False)]
    for key, value in parse_qsl(parsed.query, keep_blank_values=True)[:MAX_VALUES]:
        values.append(("query", value, str(key).casefold() in _SENSITIVE_QUERY_KEYS))
    if link_text:
        values.append(("link_text", str(link_text), False))

    observations: List[Tuple[str, Iterable[str], int]] = []
    for location, value, sensitive in values:
        if (time.monotonic() - started) * 1000 > MAX_PROCESSING_MS:
            return _result("suspicious_untrusted_instruction", location, ("processing_limit",), 0, started)
        if not value:
            continue
        normalized_values, layers, obfuscation = _normalize_candidates(value, sensitive=sensitive)
        for candidate in normalized_values:
            signals = set(obfuscation)
            signals.update(_instruction_signals(candidate))
            if _is_suspicious(signals, decoded=layers > 0):
                observations.append((location, signals, layers))

    if not observations:
        return _result("clean", "", (), 0, started)
    location, signals, layers = max(observations, key=lambda item: (len(tuple(item[1])), item[2]))
    return _result("suspicious_untrusted_instruction", location, tuple(sorted(signals)), layers, started)


def _normalize_candidates(value: str, *, sensitive: bool) -> Tuple[List[str], int, Tuple[str, ...]]:
    text = str(value)[:MAX_VALUE_LENGTH]
    obfuscation: List[str] = []
    if _ZERO_WIDTH_RE.search(text):
        obfuscation.append("zero_width_obfuscation")
    if _BIDI_RE.search(text):
        obfuscation.append("bidi_control")
    normalized = unicodedata.normalize("NFKC", html.unescape(text))
    normalized = _ESCAPED_UNICODE_RE.sub(lambda match: chr(int(match.group(1), 16)), normalized)
    # A zero-width character may split an instruction token; retain a normal
    # separator for matching rather than accidentally concatenating words.
    cleaned = _BIDI_RE.sub("", _ZERO_WIDTH_RE.sub(" ", normalized))
    confusable = cleaned.translate(_CONFUSABLES)
    if confusable != cleaned and _contains_latin_and_lookalike(cleaned):
        obfuscation.append("confusable_instruction_token")
    candidates = [cleaned, confusable]
    if sensitive or _looks_like_jwt(cleaned):
        return _unique_bounded(candidates), 0, tuple(obfuscation + ["opaque_sensitive_query_value"])

    current = cleaned
    decoded_layers = 0
    for _ in range(MAX_DECODE_LAYERS):
        decoded = _single_safe_decode(current)
        if not decoded or decoded == current:
            break
        decoded_layers += 1
        current = decoded
        candidates.append(current)
    return _unique_bounded(candidates), decoded_layers, tuple(obfuscation)


def _single_safe_decode(value: str) -> str:
    percent = unquote_plus(value)
    if percent != value and len(percent) <= MAX_DECODED_LENGTH:
        return percent
    if _BASE64_RE.fullmatch(value) and len(value) % 4 == 0:
        try:
            decoded = base64.b64decode(value, validate=True)
            return _safe_text_bytes(decoded)
        except Exception:
            return ""
    if _HEX_RE.fullmatch(value) and len(value) % 2 == 0:
        try:
            return _safe_text_bytes(bytes.fromhex(value))
        except ValueError:
            return ""
    return ""


def _safe_text_bytes(value: bytes) -> str:
    if not value or len(value) > MAX_DECODED_LENGTH:
        return ""
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return ""
    printable = sum(char.isprintable() or char.isspace() for char in text)
    return text if printable / max(len(text), 1) >= 0.9 else ""


def _instruction_signals(text: str) -> Tuple[str, ...]:
    lowered = text.casefold()
    signals = []
    if _matches(lowered, _OVERRIDE_PATTERNS):
        signals.append("instruction_override_request")
    if _matches(lowered, _PROMPT_PATTERNS):
        signals.append("ai_prompt_direct_address")
    if _matches(lowered, _SECRET_PATTERNS):
        signals.append("secret_exfiltration_request")
    if _matches(lowered, _EXFIL_PATTERNS):
        signals.append("external_send_request")
    if _matches(lowered, _TOOL_PATTERNS):
        signals.append("tool_or_fetch_instruction")
    return tuple(signals)


def _is_suspicious(signals: Iterable[str], *, decoded: bool) -> bool:
    items = set(signals)
    command = bool(items & {"instruction_override_request", "tool_or_fetch_instruction", "external_send_request"})
    target = bool(items & {"ai_prompt_direct_address", "secret_exfiltration_request"})
    return (command and target) or (decoded and command and len(items) >= 2) or ("instruction_override_request" in items and len(items) >= 2)


def _result(status: str, location: str, signals: Iterable[str], decoded_layers: int, started: float) -> Dict[str, Any]:
    return {"status": status, "location": location, "signals": list(signals), "decoded_layers": decoded_layers, "action": "AI入力から除外し、追加取得には使用しない" if status != "clean" else "許可されたURL文字列として扱う", "limits": {"max_decode_layers": MAX_DECODE_LAYERS, "max_value_length": MAX_VALUE_LENGTH, "max_processing_ms": MAX_PROCESSING_MS}, "processing_ms": min(int((time.monotonic() - started) * 1000), MAX_PROCESSING_MS)}


def _matches(value: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in patterns)


def _looks_like_jwt(value: str) -> bool:
    return value.count(".") == 2 and all(part and re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in value.split("."))


def _contains_latin_and_lookalike(value: str) -> bool:
    return bool(re.search(r"[A-Za-z]", value) and re.search(r"[\u0370-\u03ff\u0400-\u04ff]", value))


def _unique_bounded(values: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(value[:MAX_DECODED_LENGTH] for value in values if value))[:4]
