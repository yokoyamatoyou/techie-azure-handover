from __future__ import annotations

import re


SENTENCE_RE = re.compile(r"[^。！？!?]+[。！？!?]?")
NOISE_TERMS = {
    "TOP",
    "SERVICE",
    "ABOUT",
    "ABOUT US",
    "PROFILE",
    "STRENGTH",
    "RECRUIT",
    "CONTACT",
    "お知らせ一覧",
    "トップページ",
}
INCOMPLETE_SUFFIXES = ("、", "が", "から", "に", "を", "と", "の")


def extract_fact_candidates(text: str, limit: int = 6) -> list[str]:
    candidates: list[str] = []
    for block in _text_blocks(text):
        for sentence in _split_block(block):
            cleaned = _clean_candidate(sentence)
            if _is_usable_candidate(cleaned):
                candidates.append(cleaned)
            if len(candidates) >= limit:
                return candidates
    return candidates or [_clean_candidate(text[:80])]


def _text_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    pending = ""
    for raw_line in text.splitlines():
        line = _clean_candidate(raw_line)
        if not line or _is_noise_line(line):
            continue
        if pending:
            line = f"{pending} {line}" if _ascii_heading(pending) else f"{pending}{line}"
            pending = ""
        if _ascii_heading(line):
            pending = line
            continue
        if line.endswith(INCOMPLETE_SUFFIXES):
            pending = line
            continue
        blocks.append(line)
    if pending:
        blocks.append(pending)
    return blocks


def _split_block(block: str) -> list[str]:
    if len(block) <= 90 and not any(mark in block for mark in "。！？!?"):
        return [block]
    parts: list[str] = []
    for match in SENTENCE_RE.finditer(block):
        sentence = match.group(0).strip()
        if sentence:
            parts.extend(_split_long_candidate(sentence))
    return parts


def _clean_candidate(text: str) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return re.sub(r"\s+", " ", text).strip(" ・•*-−－l")


def _split_long_candidate(text: str, max_chars: int = 90) -> list[str]:
    if len(text) <= max_chars or "、" not in text:
        return [text]
    output: list[str] = []
    current = ""
    for part in text.rstrip("。").split("、"):
        piece = part.strip()
        if not piece:
            continue
        next_text = f"{current}、{piece}" if current else piece
        if len(next_text) > max_chars and current:
            output.append(_ensure_sentence_end(current))
            current = piece
        else:
            current = next_text
    if current:
        output.append(_ensure_sentence_end(current))
    return output


def _ensure_sentence_end(text: str) -> str:
    return text if text.endswith(("。", "！", "？", "!", "?")) else f"{text}。"


def _is_usable_candidate(text: str) -> bool:
    if not text or _is_noise_line(text):
        return False
    if not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text):
        return False
    if len(text) < 10 and not re.search(r"[0-9０-９]", text):
        return False
    if text.endswith(("まで", "から")):
        return False
    if "私で" in text:
        return False
    return True


def _is_noise_line(text: str) -> bool:
    if text in NOISE_TERMS:
        return True
    if "|" in text:
        return True
    if text.startswith("この度は") and "HP" in text:
        return True
    if "お知らせ" in text and len(text) < 24:
        return True
    if "慶應義塾" in text and len(text) < 40:
        return True
    if "Day" in text and len(text) < 30:
        return True
    return False


def _ascii_heading(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text)) and not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text) and len(text) <= 48
