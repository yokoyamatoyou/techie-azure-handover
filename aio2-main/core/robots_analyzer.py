"""
RobotsAnalyzer module: AI crawler compatibility, SSR detection, and multimodal content analysis.
Extracted from seo_aio_engine.py for better separation of concerns.
"""

import json
import re
from typing import Dict, Any, List, Optional

from core.scraper import Scraper
from sudachipy import tokenizer, dictionary


class RobotsAnalyzer:
    """Analyzes AI crawler compatibility, SSR requirements, and multimodal content."""

    def __init__(self):
        self.scraper = Scraper()
        self._warnings: List[str] = []
        self.dict_obj = None
        self.tokenizer_obj = None
        load_errors = []
        for dict_name, kwargs in (
            ("full", {"dict": "full"}),
            ("core", {"dict": "core"}),
            ("small", {"dict": "small"}),
            ("default", {}),
        ):
            try:
                dict_obj = dictionary.Dictionary(**kwargs) if kwargs else dictionary.Dictionary()
                self.dict_obj = dict_obj
                self.tokenizer_obj = dict_obj.create()
                break
            except Exception as e:
                load_errors.append(f"{dict_name}: {e}")
        if self.tokenizer_obj is None and load_errors:
            self._warnings.append("Sudachi辞書を初期化できず、alt評価は簡易モードで実行します。")

    def get_warnings(self) -> List[str]:
        """Return accumulated warnings."""
        return self._warnings

    def clear_warnings(self):
        """Clear accumulated warnings."""
        self._warnings = []

    def analyze_ai_crawler_compatibility(self, soup, url: str, response_time_ms: Optional[float] = None) -> Dict[str, Any]:
        """AIクローラー適合性の簡易評価（robots/SSR推定/応答速度）"""
        html_code = soup.prettify()
        ssr_info = self.detect_ssr_needs(soup, html_code)
        render_parity_est = 0.9 if not ssr_info.get("is_ssr_needed") else 0.6
        render_note = "SSR不要と推定" if render_parity_est >= 0.8 else "SSR/プリレンダリング推奨"

        robots_info = self.scraper.check_ai_crawler_access(url)
        search_agents = ["oai-searchbot", "perplexitybot", "googlebot"]
        allowed_flags = [robots_info["bots"].get(a) for a in search_agents]
        known_flags = [v for v in allowed_flags if v is not None]

        if known_flags:
            allowed_ratio = sum(1 for v in known_flags if v) / len(known_flags)
        else:
            allowed_ratio = 1.0 if not robots_info.get("exists") else 0.5

        latency_ratio = 1.0
        if isinstance(response_time_ms, (int, float)):
            latency_ratio = max(0.0, 1.0 - (response_time_ms / 1000))

        tech_score = (allowed_ratio * 50) + (render_parity_est * 30) + (latency_ratio * 20)
        blocked_search_agents = [a for a in search_agents if robots_info["bots"].get(a) is False]

        if blocked_search_agents:
            blocked_label = ", ".join(blocked_search_agents)
            self._warnings.append(f"AI検索系ボットがrobots.txtでブロックされています（{blocked_label}）。AIO露出に重大な影響があります。")

        return {
            "tech_score": round(tech_score, 1),
            "render_parity_estimate": render_parity_est,
            "render_note": render_note,
            "response_time_ms": response_time_ms,
            "robots": robots_info,
            "bots": robots_info.get("bots", {}),
            "ssr_info": ssr_info,
        }

    def detect_ssr_needs(self, soup, html_code) -> Dict[str, Any]:
        """SSR/プリレンダリングの必要性をヒューリスティック判定"""
        html_lower = html_code.lower()
        frameworks = []
        for key in ['__next', 'data-reactroot', 'ng-version', 'nuxt', 'gatsby', 'astro', 'svelte', 'alpinejs', 'vite', 'webpack']:
            if key in html_lower:
                frameworks.append(key)

        text_content = soup.get_text(separator=' ', strip=True)
        text_html_ratio = (len(text_content) / max(len(html_code), 1)) * 100
        script_count = len(soup.find_all('script'))
        noscript_present = (soup.find('noscript') is not None)

        reasons = []
        if text_html_ratio < 10:
            reasons.append('本文比率が低い（text/html比 < 10%）')
        if frameworks:
            reasons.append(f'JSフレームワーク検出: {", ".join(frameworks[:3])}')
        if script_count > 20:
            reasons.append(f'スクリプト過多（{script_count}件）')
        if not noscript_present:
            reasons.append('noscriptフォールバックなし')

        is_ssr_needed = (len([r for r in reasons if r]) >= 2) or (bool(frameworks) and text_html_ratio < 15)
        return {
            "is_ssr_needed": is_ssr_needed,
            "reasons": reasons,
            "frameworks": frameworks,
            "text_html_ratio": text_html_ratio
        }

    def analyze_multimodal_content(self, soup) -> Dict[str, Any]:
        """画像・動画・図表のマルチモーダル適合性を簡易評価"""

        def is_meaningful_alt(alt_text: str) -> bool:
            """
            Enhanced alt-text quality check with deep evaluation.
            Checks for:
            - NG patterns (filename-like patterns)
            - Verb presence (using Sudachi)
            - Length appropriateness
            """
            if not alt_text:
                return False
            alt_text = alt_text.strip()

            # 1. NG Pattern Check: Filename patterns
            ng_patterns = [
                r'DSC_',
                r'IMG_',
                r'\.jpg',
                r'\.png',
                r'\.gif',
                r'\.jpeg',
                r'screenshot',
                r'image\d+',
                r'photo\d+',
                r'スクリーンショット'
            ]
            for pattern in ng_patterns:
                if re.search(pattern, alt_text, re.IGNORECASE):
                    return False

            # 2. Verb Check (before length check): Using Sudachi to detect verbs
            if self.tokenizer_obj:
                try:
                    mode_a = tokenizer.Tokenizer.SplitMode.A
                    tokens = self.tokenizer_obj.tokenize(alt_text, mode_a)
                    has_verb = False
                    for token in tokens:
                        pos = token.part_of_speech()
                        if pos[0] == '動詞':
                            has_verb = True
                            break

                    # If verb found and length >= 15, it's good
                    if has_verb and len(alt_text) >= 15:
                        return True

                    # If no verb found, check for descriptive patterns
                    if not has_verb:
                        # Check for descriptive patterns like "〜の様子", "〜している"
                        descriptive_patterns = ['の様子', 'している', 'した', 'の状態', 'を示す', 'を表す', '撮影']
                        if any(p in alt_text for p in descriptive_patterns):
                            # Has descriptive pattern, more lenient length requirement
                            if len(alt_text) >= 13:  # Lowered from 15 for descriptive patterns
                                return True

                        # No verb and no descriptive patterns - need longer text
                        if len(alt_text) < 20:
                            return False
                except Exception:
                    pass  # If tokenization fails, fall back to basic checks

            return True

        def is_chart_like(text: str) -> bool:
            t = (text or "").lower()
            chart_keywords = ["chart", "graph", "plot", "diagram", "figure", "infographic", "visual"]
            jp_keywords = ["グラフ", "チャート", "図", "表", "インフォグラフィック"]
            return any(k in t for k in chart_keywords) or any(k in text for k in jp_keywords)

        images = soup.find_all("img")
        total_images = len(images)
        meaningful_alt = 0
        chart_images = 0
        chart_with_table = 0

        for img in images:
            alt_text = img.get("alt", "")
            src_text = img.get("src", "")
            if is_meaningful_alt(alt_text):
                meaningful_alt += 1
            if is_chart_like(alt_text) or is_chart_like(src_text):
                chart_images += 1
                parent = img.parent
                has_table = False
                for _ in range(3):
                    if not parent:
                        break
                    if parent.find("table"):
                        has_table = True
                        break
                    parent = parent.parent
                if not has_table:
                    next_sib = img.find_next_sibling()
                    steps = 0
                    while next_sib is not None and steps < 3:
                        if getattr(next_sib, "find", None) and next_sib.find("table"):
                            has_table = True
                            break
                        next_sib = next_sib.find_next_sibling()
                        steps += 1
                if has_table:
                    chart_with_table += 1

        video_tags = soup.find_all("video")
        iframe_tags = soup.find_all("iframe")
        video_iframes = [
            iframe for iframe in iframe_tags
            if iframe.get("src") and any(k in iframe.get("src") for k in ["youtube", "vimeo", "youtu.be"])
        ]
        total_videos = len(video_tags) + len(video_iframes)
        video_schema_count = 0
        transcript_count = 0
        clip_count = 0

        # Enhanced video analysis
        video_details = []
        for video_tag in video_tags:
            video_info = {
                "type": "native_video",
                "has_chapters": False,
                "has_subtitles": False
            }
            # Check for chapter markers (track elements with kind="chapters")
            chapters = video_tag.find_all("track", {"kind": "chapters"})
            video_info["has_chapters"] = len(chapters) > 0
            # Check for subtitles/captions
            subtitles = video_tag.find_all("track", {"kind": ["subtitles", "captions"]})
            video_info["has_subtitles"] = len(subtitles) > 0
            video_details.append(video_info)

        # Calculate video quality score
        video_quality_score = 0.0
        if video_details:
            with_chapters = sum(1 for v in video_details if v["has_chapters"])
            with_subtitles = sum(1 for v in video_details if v["has_subtitles"])
            chapter_ratio = with_chapters / len(video_details)
            subtitle_ratio = with_subtitles / len(video_details)
            video_quality_score = (subtitle_ratio * 0.6 + chapter_ratio * 0.4)

        for sc in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                raw = sc.string
                if not raw or not raw.strip():
                    continue
                data = json.loads(raw)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if item.get("@type") == "VideoObject":
                        video_schema_count += 1
                        if item.get("transcript"):
                            transcript_count += 1
                        if item.get("hasPart"):
                            clip_count += 1
            except Exception:
                continue

        alt_coverage = (meaningful_alt / total_images) if total_images else None
        chart_coverage = (chart_with_table / chart_images) if chart_images else None
        video_transcript_ratio = (transcript_count / video_schema_count) if video_schema_count else None

        score = 70.0
        notes = []
        if total_images == 0 and total_videos == 0:
            notes.append("画像・動画がないため評価は限定的です。")
        else:
            alt_score = (alt_coverage or 0) * 100
            chart_score = (chart_coverage or 0) * 100
            video_score = (video_transcript_ratio or 0) * 100
            score = alt_score * 0.4 + chart_score * 0.3 + video_score * 0.3
            if total_images and (alt_coverage or 0) < 0.6:
                notes.append("画像のaltが不足しています。要約的で具体的なaltを追加してください。")
            if chart_images and (chart_coverage or 0) < 0.5:
                notes.append("チャート画像に対応するテーブル/データが不足しています。")
            if total_videos and video_schema_count == 0:
                notes.append("動画がある場合はVideoObjectスキーマを追加してください。")
            if video_schema_count and (video_transcript_ratio or 0) < 0.5:
                notes.append("動画のトランスクリプトが不足しています。")

        return {
            "images_total": total_images,
            "images_with_meaningful_alt": meaningful_alt,
            "alt_coverage": alt_coverage,
            "chart_images": chart_images,
            "chart_images_with_table": chart_with_table,
            "video_count": total_videos,
            "video_schema_count": video_schema_count,
            "video_transcript_count": transcript_count,
            "video_clip_count": clip_count,
            "video_details": video_details,
            "video_quality_score": round(video_quality_score, 2),
            "score": round(score, 1),
            "notes": notes,
        }
