from __future__ import annotations

import json
from typing import Any, Dict, List

from bs4 import BeautifulSoup


def audit_media_discovery(soup: BeautifulSoup, sitemap_info: Dict[str, Any] | None = None) -> Dict[str, Any]:
    sitemap_info = sitemap_info or {}
    media_hints = sitemap_info.get("media_hints") or {}

    images = soup.find_all("img")
    discoverable_images = 0
    deferred_images = 0
    image_object_count = 0
    image_alt_count = 0

    for img in images:
        src = str(img.get("src") or "").strip()
        if src and not src.startswith("data:"):
            discoverable_images += 1
        elif img.get("data-src") or img.get("data-lazy-src"):
            deferred_images += 1
        if str(img.get("alt") or "").strip():
            image_alt_count += 1

    video_tags = soup.find_all("video")
    iframe_videos = [
        iframe for iframe in soup.find_all("iframe")
        if any(token in str(iframe.get("src") or "").lower() for token in ("youtube", "youtu.be", "vimeo"))
    ]
    video_count = len(video_tags) + len(iframe_videos)
    video_object_count = 0
    transcript_count = 0
    caption_track_count = 0
    poster_missing_count = 0

    for video in video_tags:
        if not str(video.get("poster") or "").strip():
            poster_missing_count += 1
        for track in video.find_all("track"):
            kind = str(track.get("kind") or "").lower()
            if kind in {"captions", "subtitles"}:
                caption_track_count += 1

    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string
        if not raw or not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type")
            types = item_type if isinstance(item_type, list) else [item_type]
            if "ImageObject" in types:
                image_object_count += 1
            if "VideoObject" in types:
                video_object_count += 1
                if item.get("transcript"):
                    transcript_count += 1

    issues: List[Dict[str, str]] = []
    status = "pass"

    def add_issue(severity: str, message: str) -> None:
        nonlocal status
        issues.append({"severity": severity, "message": message})
        if severity == "fail":
            status = "fail"
        elif severity == "warn" and status == "pass":
            status = "warn"

    image_sitemap_detected = bool(media_hints.get("image_sitemap_detected"))
    video_sitemap_detected = bool(media_hints.get("video_sitemap_detected"))

    if images and discoverable_images < len(images):
        add_issue("warn", f"src を持たない遅延画像が {len(images) - discoverable_images} 件あります。HTML上で画像URLが見える形にしてください。")
    if len(images) >= 5 and not image_sitemap_detected:
        add_issue("warn", "画像数が多いページですが image sitemap の検出ヒントがありません。")
    if images and image_alt_count == 0:
        add_issue("warn", "画像に alt が付いていません。画像内容が検索に伝わりにくくなります。")

    if video_count and video_object_count == 0:
        add_issue("warn", "動画がありますが VideoObject schema が見つかりません。")
    if video_count and caption_track_count == 0 and transcript_count == 0:
        add_issue("warn", "動画の字幕または transcript が見つかりません。")
    if video_count and poster_missing_count:
        add_issue("warn", f"poster 未設定の native video が {poster_missing_count} 件あります。")
    if video_count and not video_sitemap_detected:
        add_issue("warn", "video sitemap の検出ヒントがありません。")

    return {
        "status": status,
        "image_discovery": {
            "images_total": len(images),
            "discoverable_images": discoverable_images,
            "deferred_images": deferred_images,
            "images_with_alt": image_alt_count,
            "image_object_count": image_object_count,
            "image_sitemap_detected": image_sitemap_detected,
        },
        "video_discovery": {
            "video_count": video_count,
            "video_object_count": video_object_count,
            "transcript_count": transcript_count,
            "caption_track_count": caption_track_count,
            "poster_missing_count": poster_missing_count,
            "video_sitemap_detected": video_sitemap_detected,
        },
        "sitemap_media": {
            "image_sitemap_detected": image_sitemap_detected,
            "video_sitemap_detected": video_sitemap_detected,
            "source_sitemaps": sitemap_info.get("source_sitemaps") or [],
        },
        "issues": issues,
        "summary": (
            f"images={len(images)} discoverable={discoverable_images} "
            f"/ videos={video_count} schema={video_object_count} "
            f"/ image_sitemap={'yes' if image_sitemap_detected else 'no'} "
            f"/ video_sitemap={'yes' if video_sitemap_detected else 'no'}"
        ),
    }
