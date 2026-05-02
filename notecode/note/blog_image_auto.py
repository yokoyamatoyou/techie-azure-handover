"""Automatic blog image generation helpers for post-success UI flow."""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from note.image_cover_strategy import (
    build_cover_visual_brief_lines,
    build_display_copy_prompt,
    clean_display_text,
    fallback_display_text,
    is_article_specific_display_text,
)
from note.image_config import (
    DEFAULT_IMAGE_BACKGROUND,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_IMAGE_MODERATION,
    DEFAULT_IMAGE_OUTPUT_FORMAT,
    DEFAULT_IMAGE_QUALITY,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_TEXT_IMAGE_QUALITY,
)
from note.image_prompt_helpers import _build_image_pattern_suffix, _normalize_image_pattern_key

logger = logging.getLogger(__name__)

AUTO_IMAGE_LOG_DIR = Path(__file__).resolve().parent.parent / "logs" / "gpt_image2_blog_image_auto_2026-04-22"
BLOG_IMAGE_VARIANTS = (
    {
        "key": "with_text",
        "label": "文字入り画像",
        "allow_text": True,
        "description": "article cover with exact Japanese headline text",
    },
    {
        "key": "without_text",
        "label": "文字なし画像",
        "allow_text": False,
        "description": "article cover without any text",
    },
)


@dataclass
class BlogImageVariantResult:
    key: str
    label: str
    status: str
    path: str = ""
    prompt: str = ""
    retry_prompt: str = ""
    retry_count: int = 0
    error: str = ""
    model: str = DEFAULT_IMAGE_MODEL
    size: str = DEFAULT_IMAGE_SIZE
    quality: str = DEFAULT_IMAGE_QUALITY
    output_format: str = DEFAULT_IMAGE_OUTPUT_FORMAT
    usage: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _compact_text(value: str, *, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


_NON_RETRYABLE_IMAGE_ERROR_RE = re.compile(
    r"(?:authentication|unauthorized|forbidden|permission|api key|billing|insufficient[_ ]quota|invalid organization)",
    flags=re.I,
)


def _should_retry_image_generation_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}"
    return not _NON_RETRYABLE_IMAGE_ERROR_RE.search(text)


def infer_image_display_text(
    llm: Any,
    *,
    title: str,
    lead: str,
    body: str,
    article_type: str = "",
) -> str:
    prompt, fallback = build_display_copy_prompt(
        title=title,
        lead=lead,
        body=body,
        article_type=article_type,
    )
    try:
        raw = llm.generate_text(
            prompt,
            max_tokens=80,
            task_type="image_display_text",
            temperature_override=0.2,
            verbosity="low",
            article_type=article_type or None,
        )
    except Exception as exc:
        logger.debug("Image display text inference failed", exc_info=exc)
        return fallback
    cleaned = clean_display_text(raw)
    if not is_article_specific_display_text(cleaned, title, lead, article_type=article_type):
        return fallback
    return cleaned or fallback


def _visual_direction(pattern_key: str) -> str:
    return _build_image_pattern_suffix(_normalize_image_pattern_key(pattern_key), language="en")


def build_blog_image_prompt(
    *,
    title: str,
    lead: str,
    body: str,
    article_type: str,
    display_text: str,
    variant_key: str,
    pattern_key: str = "simple",
) -> str:
    title_text = _compact_text(title, max_chars=120) or "Untitled article"
    lead_text = _compact_text(lead, max_chars=260) or _compact_text(body, max_chars=260) or "No summary provided"
    body_focus = _compact_text(body, max_chars=650) or lead_text
    visual_direction = _visual_direction(pattern_key)

    common = [
        "Create a polished horizontal cover image for a Japanese note blog article.",
        f"Article title: {title_text}",
        f"Article type: {article_type or 'general'}",
        f"Article summary: {lead_text}",
        f"Important article context: {body_focus}",
        f"Visual direction: {visual_direction}",
        "Composition: landscape article cover, one clear focal subject, article-specific supporting context, readable at thumbnail size.",
        "Information density: let GPT Image 2 choose the amount of supporting detail needed for this article; richer context is welcome, but keep at least 15% clean breathing room and avoid clutter.",
        "Style: modern Japanese visual, natural lighting, clean details, no copyrighted characters, no brand logos.",
        "Output must look like a finished article cover, not a UI screenshot or poster mockup.",
        *build_cover_visual_brief_lines(article_type=article_type, variant_key=variant_key),
    ]

    if variant_key == "with_text":
        copy_text = clean_display_text(display_text) or fallback_display_text(title, lead, article_type=article_type)
        common.extend(
            [
                "Include exactly one short Japanese headline in the image.",
                f'Text to render EXACTLY, once, with no extra characters: "{copy_text}"',
                "Let GPT Image 2 design the typography and placement naturally for a polished Japanese note cover.",
                "Prioritize clear readability after resizing, balanced composition, and a natural relationship between text and subject.",
                "Do not add any other text, captions, letters, numbers, logos, signatures, or watermarks.",
            ]
        )
    else:
        common.extend(
            [
                "Do not include any text.",
                "No letters, no numbers, no captions, no signs, no logos, no UI text, no watermark, no signature.",
                "Communicate the article theme only through subject, composition, color, and atmosphere.",
            ]
        )
    return "\n".join(common).strip()


def build_retry_prompt(
    *,
    title: str,
    lead: str,
    display_text: str,
    variant_key: str,
    article_type: str = "",
    pattern_key: str = "simple",
) -> str:
    title_text = _compact_text(title, max_chars=90) or "Japanese blog article"
    lead_text = _compact_text(lead, max_chars=160) or title_text
    visual_direction = _visual_direction(pattern_key)
    lines = [
        "Create a simple horizontal Japanese blog cover image.",
        f"Theme: {title_text}",
        f"Context: {lead_text}",
        f"Style constraints: {visual_direction}",
        "One main subject with GPT Image 2 choosing useful supporting context, at least 15% clean breathing room, no visual clutter, no famous characters, no brand logos.",
        *build_cover_visual_brief_lines(article_type=article_type, variant_key=variant_key),
    ]
    if variant_key == "with_text":
        copy_text = clean_display_text(display_text) or fallback_display_text(title, lead)
        lines.extend(
            [
                f'Render this exact Japanese text once: "{copy_text}"',
                "Let the image model choose natural typography and placement; keep the text clearly readable after resizing.",
                "No other words, letters, numbers, logos, or watermarks.",
            ]
        )
    else:
        lines.append("No text, no letters, no numbers, no signs, no logos, no watermark.")
    return "\n".join(lines).strip()


def _latest_usage_dict(llm: Any, *, task_type: str = "") -> Optional[Dict[str, Any]]:
    tracker = getattr(llm, "token_tracker", None)
    getter = getattr(tracker, "get_latest_usage", None)
    if not callable(getter):
        return None
    try:
        usage = getter()
    except Exception:
        return None
    if usage is None:
        return None
    to_dict = getattr(usage, "to_dict", None)
    if callable(to_dict):
        data = to_dict()
    elif isinstance(usage, dict):
        data = dict(usage)
    else:
        return None
    if task_type and str(data.get("task_type") or "") != task_type:
        return None
    return data


def _write_auto_image_log(payload: Dict[str, Any], log_dir: Path = AUTO_IMAGE_LOG_DIR) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(payload.get("run_id") or uuid.uuid4().hex)
    path = log_dir / f"{run_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path = log_dir / "latest.json"
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def generate_blog_images_for_article(
    *,
    llm: Any,
    title: str,
    lead: str,
    body: str,
    article_type: str = "",
    pattern_key: str = "simple",
    model: str = DEFAULT_IMAGE_MODEL,
    size: str = DEFAULT_IMAGE_SIZE,
    plain_quality: str = DEFAULT_IMAGE_QUALITY,
    text_quality: str = DEFAULT_TEXT_IMAGE_QUALITY,
    output_format: str = DEFAULT_IMAGE_OUTPUT_FORMAT,
    background: str = DEFAULT_IMAGE_BACKGROUND,
    moderation: str = DEFAULT_IMAGE_MODERATION,
    log_dir: Path = AUTO_IMAGE_LOG_DIR,
) -> Dict[str, Any]:
    started = time.monotonic()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    display_text = infer_image_display_text(
        llm,
        title=title,
        lead=lead,
        body=body,
        article_type=article_type,
    )
    results: List[BlogImageVariantResult] = []

    for variant in BLOG_IMAGE_VARIANTS:
        key = str(variant["key"])
        quality = text_quality if key == "with_text" else plain_quality
        prompt = build_blog_image_prompt(
            title=title,
            lead=lead,
            body=body,
            article_type=article_type,
            display_text=display_text,
            variant_key=key,
            pattern_key=pattern_key,
        )
        result = BlogImageVariantResult(
            key=key,
            label=str(variant["label"]),
            status="failed",
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            output_format=output_format,
        )

        try:
            paths = llm.generate_images(
                prompt,
                n=1,
                size=size,
                quality=quality,
                model=model,
                pattern_key=pattern_key,
                output_format=output_format,
                background=background,
                moderation=moderation,
                allow_text=bool(variant["allow_text"]),
            )
            if not paths:
                raise RuntimeError("image API returned no saved image")
            result.path = str(paths[0])
            result.status = "success"
            result.usage = _latest_usage_dict(llm, task_type="image_generation")
        except Exception as exc:
            result.error = str(exc)
            if not _should_retry_image_generation_error(exc):
                logger.warning("Blog image generation failed variant=%s; not retrying non-recoverable error", key, exc_info=exc)
                results.append(result)
                continue
            logger.warning("Blog image generation failed variant=%s; retrying with simplified prompt", key, exc_info=exc)
            result.retry_count = 1
            result.retry_prompt = build_retry_prompt(
                title=title,
                lead=lead,
                display_text=display_text,
                variant_key=key,
                article_type=article_type,
                pattern_key=pattern_key,
            )
            try:
                paths = llm.generate_images(
                    result.retry_prompt,
                    n=1,
                    size=size,
                    quality=quality,
                    model=model,
                    pattern_key=pattern_key,
                    output_format=output_format,
                    background=background,
                    moderation=moderation,
                    allow_text=bool(variant["allow_text"]),
                )
                if not paths:
                    raise RuntimeError("image API retry returned no saved image")
                result.path = str(paths[0])
                result.status = "success"
                result.error = ""
                result.usage = _latest_usage_dict(llm, task_type="image_generation")
            except Exception as retry_exc:
                logger.warning("Blog image retry exhausted variant=%s", key, exc_info=retry_exc)
                result.error = str(retry_exc)
        results.append(result)

    success_count = len([item for item in results if item.status == "success"])
    if success_count == len(results):
        status = "success"
    elif success_count:
        status = "partial"
    else:
        status = "failed"

    payload = {
        "run_id": run_id,
        "status": status,
        "created_at": datetime.now().isoformat(),
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "model": model,
        "size": size,
        "plain_quality": plain_quality,
        "text_quality": text_quality,
        "output_format": output_format,
        "background": background,
        "moderation": moderation,
        "article_type": article_type,
        "title": title,
        "display_text": display_text,
        "variants": [item.to_dict() for item in results],
    }
    try:
        payload["log_path"] = str(_write_auto_image_log(payload, log_dir=log_dir))
    except Exception as exc:
        logger.warning("Failed to write blog image auto log", exc_info=exc)
    return payload


def successful_image_paths(result: Dict[str, Any]) -> List[str]:
    paths: List[str] = []
    for item in result.get("variants", []) if isinstance(result, dict) else []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if path:
            paths.append(path)
    return paths
