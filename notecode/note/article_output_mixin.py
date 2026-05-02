"""Output assembly helpers for ArticleGenerator."""
from __future__ import annotations

import logging
import random
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from note.article_fetcher import FetchedContent
from note.policy_engine import evaluate_title_quality
from note.prompt_sanitizer import sanitize_untrusted_text

logger = logging.getLogger(__name__)

ARTICLE_TYPE_LABELS = {
    "branding": "商品・サービスブランディング",
    "ai": "解説記事",
    "announcement": "お知らせ・アップデート",
    "case_study": "導入事例・ケーススタディ",
}

CTA_PATTERNS = [
    "この記事が少しでも参考になれば、スキをぽちっと押してくれると嬉しいです。",
    "違う見方があれば、コメントで教えてください。議論できると助かります。",
    "次も読んでもらえると励みになります。フォローも気が向いたらぜひ。",
]

LINKEDIN_CTA_PATTERNS = [
    "💡 この投稿が参考になったら、いいね＆保存をお願いします！",
    "🔔 フォローしていただくと、最新の投稿をお届けします。",
    "💬 ご意見やご質問があれば、コメント欄でお聞かせください。",
    "📩 もっと詳しく話したい方はDMでお気軽にどうぞ！",
]

LINKEDIN_MIN_CHARS = 387
LINKEDIN_MAX_CHARS = 1568
MAX_INLINE_SOURCE_LINKS = 4
TITLE_QUALITY_RETRY_LIMIT = 2

SOURCE_MATCH_STOPWORDS = {
    "こと",
    "ため",
    "これ",
    "それ",
    "もの",
    "よう",
    "です",
    "ます",
    "する",
    "した",
    "して",
    "いる",
    "なる",
    "ある",
    "ない",
    "note",
    "article",
}

_RE_SECTION_BLOCK = re.compile(r"^##\s*(.+?)\n+([\s\S]*?)(?=^##\s+|\Z)", re.MULTILINE)
_RE_BRACKET_ANGLE = re.compile(r"[\[\]<>]+")
_RE_MULTI_SPACE = re.compile(r"\s{2,}")


def randomize_length(base: int) -> int:
    return int(base * random.uniform(0.8, 1.2))


class ArticleOutputMixin:
    def _generate_title(
        self,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        prefer_numbered: bool = False,
    ) -> str:
        target = randomize_length(34)
        number_rule = (
            "数字を入れると効果的な場合は入れてよい。"
            if prefer_numbered
            else "数字は必須ではない。自然な時だけ使い、無理に入れないこと。"
        )
        prompt = f"""
{self._current_prompts[article_type]}

【ターゲット読者】
{target_audience}

ユーザー指示（最優先）:
{self._safe_user_prompt(user_prompt)}

参考資料（抜粋）:
{merged[:1000] if merged else "なし"}

【追加ガイド】
{self._enhanced_context or "なし"}

noteでクリックされる魅力的なタイトルを1つ作成してください。
【重要ルール】
- 必ず日本語で作成すること。英語の専門用語（AI、API等）は使ってもよいが、文の構造は日本語にする。
- 参考資料の英語タイトルをそのまま使用しないこと。日本語読者向けに再構成する。
- 毎回同じ表現（「30〜40代必見」など）にならないよう、記事ごとに独自性のある切り口で作成すること。
- 目安は{target}文字前後。
- {number_rule}
- ターゲット読者が「自分のことだ」と思うキーワードを含める。
- 「〜の考察」「〜について」等の曖昧な表現は禁止。
- 誇大・煽り・クリック狙いの表現は禁止。
- 具体性と便益が伝わる語にする。
- AIらしい過剰修飾語（圧倒的・劇的など）を避ける。
- 出力はタイトルのみ。
""".strip()
        title = self.llm.generate_text(prompt, max_tokens=60, task_type="title").strip()
        title = self._normalize_title_candidate(title)
        if not self._is_mostly_japanese(title):
            title = self._regenerate_japanese_title(
                merged=merged,
                user_prompt=user_prompt,
                article_type=article_type,
                target_audience=target_audience,
                prefer_numbered=prefer_numbered,
                original_title=title,
            )
            title = self._normalize_title_candidate(title)
            if not self._is_mostly_japanese(title):
                title = self._force_japanese_title(user_prompt, article_type, target_audience)
        title = self._enforce_title_quality(
            title=title,
            merged=merged,
            user_prompt=user_prompt,
            article_type=article_type,
            target_audience=target_audience,
            prefer_numbered=prefer_numbered,
        )
        return title

    def _normalize_title_candidate(self, title: str) -> str:
        line = (title or "").strip().splitlines()[0] if title else ""
        line = re.sub(r"^タイトル[:：]\s*", "", line)
        return line.strip("「」\"' ")

    def _enforce_title_quality(
        self,
        *,
        title: str,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        prefer_numbered: bool,
    ) -> str:
        checked = self._normalize_title_candidate(title)
        focus = self._get_effective_writing_focus()
        evidence_mode = str(self._pipeline_policy.get("evidence_mode", "normal"))

        for _ in range(TITLE_QUALITY_RETRY_LIMIT):
            issues = evaluate_title_quality(checked, focus, evidence_mode)
            if not issues:
                break
            checked = self._regenerate_title_for_quality(
                merged=merged,
                user_prompt=user_prompt,
                article_type=article_type,
                target_audience=target_audience,
                prefer_numbered=prefer_numbered,
                previous_title=checked,
                issues=issues,
            )
            checked = self._normalize_title_candidate(checked)

        final_issues = evaluate_title_quality(checked, focus, evidence_mode)
        if final_issues:
            checked = self._force_japanese_title(user_prompt, article_type, target_audience)
        return checked

    def _regenerate_title_for_quality(
        self,
        *,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        prefer_numbered: bool,
        previous_title: str,
        issues: List[str],
    ) -> str:
        target = randomize_length(32)
        number_rule = (
            "数字は自然に有効な場合のみ使う。"
            if prefer_numbered
            else "数字は無理に入れない。"
        )
        issue_text = ", ".join(issues) if issues else "quality_warning"
        prompt = f"""
{self._current_prompts[article_type]}

【ターゲット読者】
{target_audience}

【本文の重心】
{self._get_writing_focus_guide() or "自動判定"}

【追加ガイド】
{self._enhanced_context or "なし"}

ユーザー指示（最優先）:
{self._safe_user_prompt(user_prompt)}

参考資料（抜粋）:
{merged[:900] if merged else "なし"}

直前タイトル:
{previous_title}

品質警告:
{issue_text}

タイトルを1本だけ再生成してください。
【ルール】
- 具体的な便益・対象読者・論点を含める
- 誇大・煽り・断定過多・曖昧語を使わない
- 目安は{target}文字前後
- {number_rule}
- 出力はタイトルのみ
""".strip()
        return self.llm.generate_text(prompt, max_tokens=60, task_type="title").strip()

    def _is_mostly_japanese(self, text: str) -> bool:
        if not text:
            return True
        stripped = re.sub(r"\s+", "", text)
        letters = re.findall(r"[A-Za-z\u3040-\u30FF\u4E00-\u9FFF]", stripped)
        if not letters:
            return False
        jp_chars = re.findall(r"[\u3040-\u30FF\u4E00-\u9FFF]", stripped)
        return (len(jp_chars) / len(letters)) >= 0.2

    def _contains_japanese(self, text: str) -> bool:
        return bool(re.search(r"[\u3040-\u30FF\u4E00-\u9FFF]", text or ""))

    def _force_japanese_title(
        self,
        user_prompt: str,
        article_type: str,
        target_audience: str,
    ) -> str:
        label = ARTICLE_TYPE_LABELS.get(article_type, "記事")
        cleaned_prompt = (user_prompt or "").strip()
        if cleaned_prompt:
            cleaned_prompt = re.sub(r"[\"'`]+", "", cleaned_prompt)
            cleaned_prompt = re.sub(r"\s+", " ", cleaned_prompt)
            cleaned_prompt = re.sub(r"[。．！？!?]+", "", cleaned_prompt).strip()
            if self._contains_japanese(cleaned_prompt):
                return f"{cleaned_prompt[:24]}をやさしく整理する話"

        cleaned_audience = (target_audience or "").strip()
        cleaned_audience = re.sub(r"[。．！？!?].*$", "", cleaned_audience).strip()
        if self._contains_japanese(cleaned_audience):
            return f"{cleaned_audience}に伝えたい{label}のポイント"
        return f"{label}をやさしく整理するポイント"

    def _regenerate_japanese_title(
        self,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        prefer_numbered: bool,
        original_title: str,
    ) -> str:
        target = randomize_length(34)
        number_rule = (
            "数字を入れると効果的な場合は入れてよい。"
            if prefer_numbered
            else "数字は必須ではない。自然な時だけ使い、無理に入れないこと。"
        )
        prompt = f"""
{self._current_prompts[article_type]}

【ターゲット読者】
{target_audience}

ユーザー指示（最優先）:
{self._safe_user_prompt(user_prompt)}

参考資料（抜粋）:
{merged[:1000] if merged else "なし"}

【追加ガイド】
{self._enhanced_context or "なし"}

直前に英語寄りのタイトルが出ました。日本語タイトルに必ず直してください。
必要なら意味を保った自然な日本語に翻訳して構いません。

【英語寄りのタイトル】
{original_title or "なし"}

noteでクリックされる魅力的なタイトルを1つ作成してください。
【重要ルール】
- 必ず日本語で作成すること。英語の専門用語（AI、API等）は使ってもよいが、文の構造は日本語にする。
- 参考資料の英語タイトルをそのまま使用しないこと。日本語読者向けに再構成する。
- 目安は{target}文字前後。
- {number_rule}
- ターゲット読者が「自分のことだ」と思うキーワードを含める。
- 「〜の考察」「〜について」等の曖昧な表現は禁止。
- 出力はタイトルのみ。
""".strip()
        return self.llm.generate_text(prompt, max_tokens=60, task_type="title").strip()

    def _generate_lead(
        self,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        target_chars: Optional[int] = None,
        title: Optional[str] = None,
    ) -> str:
        target = target_chars or randomize_length(150)
        structure_guide = self._get_structure_guide()
        writing_focus_guide = self._get_writing_focus_guide()
        opening_style_guide = self._get_opening_style_guide()
        focus_section_rules = self._get_focus_section_rules()
        dynamic_formatting_guide = self._get_dynamic_formatting_guide()
        prompt = f"""
{self._current_prompts[article_type]}

【記事タイトル】
{title or "指定なし"}

【ターゲット読者】
{target_audience}

ユーザー指示:
{self._safe_user_prompt(user_prompt)}

参考資料（抜粋）:
{merged[:1000] if merged else "なし"}

【追加ガイド】
{self._enhanced_context or "なし"}

【心理学ベースの構造ガイド】
{structure_guide}

【本文の重心】
{writing_focus_guide or "自動判定"}

【導入スタイル（この生成で固定）】
{opening_style_guide}

【重心別セクションルール】
{focus_section_rules or "なし"}

【構造フォーマット方針】
{dynamic_formatting_guide}

記事の「リード文（冒頭部分）」を作成してください。
noteにおいて、最初の3行で読者を引き込めるかが勝負です。

【執筆ルール】
1. 冒頭1文は【導入スタイル】の要件を必ず満たす。
2. 共感/問題意識を示し、すぐに結論のチラ見せへつなぐ。
3. 記事を読むメリットを簡潔に伝え、スクロールを促す。
4. 全体で{target}文字程度。挨拶（こんにちは等）は不要。
5. タイトルの約束を冒頭でチラ見せする。
6. 「〜視点では」「〜の立場から書く」など、視点の説明文は書かない。
7. 「経営層のみなさん」「経営層はどう思いますか？」のような属性呼びかけは避ける。
8. 自分の肩書きを名乗らない（例: 専門家として/当社として）。
9. 冒頭の定型句（「〜ありませんか？」「〜だと思っていたんですが」）は使わない。
10. タイトル直後の導入を毎回同じ型に固定しない（短文導入/要点直行/場面導入を使い分ける）。

出力は本文のみ。
""".strip()
        max_tokens = min(600, max(300, int(target * 1.2)))
        return self.llm.generate_text(prompt, max_tokens=max_tokens, task_type="lead").strip()

    def _needs_opening_refresh(self, lead: str) -> bool:
        if not lead:
            return False
        first_line = lead.strip().splitlines()[0].strip()
        first_sentence = re.split(r"[。！？]", first_line, maxsplit=1)[0]
        if not first_sentence:
            return False
        if re.search(r"(ありませんか[？?]|ないでしょうか[？?]|と思っていたんですが|だと思っていたんですが)", first_sentence):
            return True
        if self._get_effective_writing_focus() == "analysis" and ("?" in first_line or "？" in first_line):
            return True
        return False

    def _refresh_lead_opening(
        self,
        lead: str,
        *,
        merged_context: str,
        title: str,
        article_type: str,
        target_audience: str,
    ) -> str:
        if not self._needs_opening_refresh(lead):
            return lead

        opening_style_guide = self._get_opening_style_guide()
        writing_focus_guide = self._get_writing_focus_guide()
        focus_section_rules = self._get_focus_section_rules()
        prompt = f"""
あなたは編集者です。以下のリード文を、意味を変えずに冒頭だけ自然に直してください。

【記事タイプ】
{ARTICLE_TYPE_LABELS.get(article_type, article_type)}

【記事タイトル】
{title}

【ターゲット読者】
{target_audience}

【本文の重心】
{writing_focus_guide or "自動判定"}

【導入スタイル】
{opening_style_guide}

【重心別セクションルール】
{focus_section_rules or "なし"}

【参考情報（抜粋）】
{merged_context[:2500] if merged_context else "なし"}

【修正ルール】
1. リード全体の意味は維持し、主に冒頭2〜3文だけ調整する。
2. 「〜ありませんか？」「〜だと思っていたんですが」の定型を使わない。
3. 分析メイン時は疑問文で始めない。
4. 人間らしい語り口は残すが、同じ導入型の反復は避ける。
5. 出力は修正後のリード本文のみ。

【入力リード】
{lead}
""".strip()
        max_tokens = min(700, max(280, int(len(lead) * 1.25)))
        try:
            rewritten = self.llm.generate_text(
                prompt,
                max_tokens=max_tokens,
                task_type="lead_refresh",
            ).strip()
        except Exception as exc:
            logger.debug("Lead opening refresh failed. Keep original lead.", exc_info=exc)
            return lead

        if not rewritten:
            return lead
        if len(rewritten) < max(40, int(len(lead) * 0.55)):
            return lead
        return rewritten

    def _generate_hashtags(self, merged: str, article_type: str) -> str:
        prompt = f"""
{self._current_prompts[article_type]}

参考資料（抜粋）:
{merged or "なし"}

note用のハッシュタグを3〜6個。
出力は「#タグ #タグ」の形式のみ。ハッシュタグ以外の文字やラベルは書かない。
""".strip()
        raw = self.llm.generate_text(prompt, max_tokens=80, task_type="hashtags").strip()
        result = self._normalize_hashtags(raw, merged, article_type)
        if result.count("#") < 3:
            retry_prompt = (
                f"参考資料: {(merged or '')[:600]}\n\n"
                "上記に基づき、noteハッシュタグを4〜6個。\n"
                "出力形式: #タグ #タグ #タグ #タグ\n"
                "これ以外の文字は一切書かないでください。"
            )
            raw2 = self.llm.generate_text(retry_prompt, max_tokens=80, task_type="hashtags").strip()
            retry_result = self._normalize_hashtags(raw2, merged, article_type)
            if retry_result.count("#") > result.count("#"):
                result = retry_result
        return result

    def _normalize_hashtags(self, raw: str, merged: str, article_type: str) -> str:
        if not raw:
            raw = ""

        raw = raw.replace("＃", "#")
        raw = re.sub(r"[、,／・\u3000]+", " ", raw)

        tags = re.findall(r"#\S+", raw)
        cleaned = []
        for tag in tags:
            tag = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF#]+", "", tag)
            tag_body = tag.lstrip("#")
            if len(tag_body) <= 0 or len(tag) > 20:
                continue
            if re.match(r"^\d+$", tag_body) and len(tag_body) < 4:
                continue
            cleaned.append(tag)

        if len(cleaned) < 3:
            base_label = ARTICLE_TYPE_LABELS.get(article_type, "note")
            base_tag = "#" + re.sub(r"\s+", "", base_label)
            if base_tag not in cleaned:
                cleaned.append(base_tag)

            stop = {
                "する", "いる", "ある", "こと", "もの", "よう", "ため", "です", "ます",
                "これ", "それ", "あれ", "ここ", "そこ", "こちら", "そちら",
                "また", "さらに", "ただし", "しかし", "ところ", "なかで",
                "について", "として", "において", "に対して",
                "ました", "ません", "ください", "くわしく", "くわしくは",
                "できる", "なる", "いく", "くる", "おく", "みる",
                "という", "といった", "のような", "における",
                "から", "まで", "だけ", "ほど", "など",
                "つまり", "すなわち", "一方", "ただ",
                "その", "この", "あの", "どの",
            }
            words = re.findall(r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]{2,8}", merged)
            freq: Dict[str, int] = {}
            for word in words:
                if word in stop:
                    continue
                freq[word] = freq.get(word, 0) + 1
            for word, _ in sorted(freq.items(), key=lambda kv: kv[1], reverse=True):
                tag = "#" + word
                if tag not in cleaned:
                    cleaned.append(tag)
                if len(cleaned) >= 6:
                    break

        cleaned = cleaned[:6]
        if len(cleaned) < 3:
            type_fallbacks = {
                "branding": ["#企業ブランディング", "#ブランド戦略"],
                "case_study": ["#導入事例", "#ケーススタディ"],
                "announcement": ["#お知らせ", "#アップデート"],
            }
            fallback = type_fallbacks.get(article_type, ["#ブログ", "#まとめ"])
            for tag in fallback:
                if tag not in cleaned:
                    cleaned.append(tag)
                if len(cleaned) >= 3:
                    break

        return " ".join(cleaned[:6])

    def _tokenize_for_source_match(self, text: str) -> List[str]:
        if not text:
            return []
        lowered = text.lower()
        raw_tokens = re.findall(r"[a-z][a-z0-9_-]{1,24}|[\u3040-\u30ff\u4e00-\u9fff]{2,12}", lowered)
        tokens: List[str] = []
        for token in raw_tokens:
            if token in SOURCE_MATCH_STOPWORDS:
                continue
            if token.isdigit():
                continue
            tokens.append(token)
        return tokens

    def _sanitize_source_label(self, label: str) -> str:
        cleaned = (label or "").strip()
        cleaned = cleaned.replace("\n", " ").replace("\r", " ")
        cleaned = _RE_BRACKET_ANGLE.sub("", cleaned)
        cleaned = _RE_MULTI_SPACE.sub(" ", cleaned)
        return cleaned or "参考資料"

    def _extract_section_blocks(self, body: str) -> List[Tuple[str, str]]:
        if not body:
            return []
        key = hash(body)
        cached = self._section_block_cache.get(key)
        if cached is not None:
            self._section_block_cache_hits += 1
            return cached
        self._section_block_cache_misses += 1
        matches = _RE_SECTION_BLOCK.findall(body)
        result = [(heading.strip(), content.strip()) for heading, content in matches if heading.strip()]
        if len(self._section_block_cache) > 64:
            self._section_block_cache.clear()
        self._section_block_cache[key] = result
        return result

    def _build_source_candidates(self, contexts: List[FetchedContent]) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for ctx in contexts:
            if not ctx.url:
                continue
            url = ctx.url.strip()
            if not url:
                continue
            try:
                domain = urlparse(url).netloc.lower().replace("www.", "")
            except (ValueError, TypeError):
                domain = ""
            label = self._sanitize_source_label(ctx.title or domain or "参考資料")
            source_text = f"{label} {domain} {(ctx.content or '')[:1600]}"
            token_set = set(self._tokenize_for_source_match(source_text))
            candidates.append(
                {
                    "url": url,
                    "label": label,
                    "tokens": token_set,
                }
            )
        return candidates

    def _inject_contextual_source_links(self, body: str, contexts: List[FetchedContent]) -> str:
        if not body:
            return body
        sections = self._extract_section_blocks(body)
        if not sections:
            return body
        candidates = self._build_source_candidates(contexts)
        if not candidates:
            return body

        section_count = len(sections)
        max_links = min(MAX_INLINE_SOURCE_LINKS, len(candidates), max(1, section_count // 2))
        if max_links <= 0:
            return body

        existing_urls = set(re.findall(r"https?://[^\s)>]+", body))
        used_urls: set = set(existing_urls)
        assignments: Dict[int, Dict[str, Any]] = {}
        center = (section_count - 1) / 2
        section_order = sorted(range(section_count), key=lambda idx: abs(idx - center))

        for idx in section_order:
            if len(assignments) >= max_links:
                break
            heading, content = sections[idx]
            if "http://" in content or "https://" in content:
                continue

            section_tokens = set(self._tokenize_for_source_match(f"{heading} {content[:1200]}"))
            best: Optional[Dict[str, Any]] = None
            best_score = 0

            for candidate in candidates:
                if candidate["url"] in used_urls:
                    continue
                overlap = section_tokens & candidate["tokens"]
                score = len(overlap)
                if score > best_score:
                    best = candidate
                    best_score = score

            # 単純な機械挿入を避けるため、最低限の関連度を要求
            if best and best_score >= 1:
                assignments[idx] = best
                used_urls.add(best["url"])

        # 一致語が弱いケースでも、少なくとも1件は中央セクションに出典を残す
        if not assignments:
            for idx in section_order:
                _, content = sections[idx]
                if "http://" in content or "https://" in content:
                    continue
                candidate = next((c for c in candidates if c["url"] not in used_urls), None)
                if candidate:
                    assignments[idx] = candidate
                    used_urls.add(candidate["url"])
                    break

        if not assignments:
            return body

        rebuilt_sections: List[str] = []
        for idx, (heading, content) in enumerate(sections):
            block = f"## {heading}\n\n{content.strip()}"
            candidate = assignments.get(idx)
            if candidate and candidate["url"] not in content:
                citation_line = f"出典: {candidate['label']}\n{candidate['url']}"
                block = f"{block.rstrip()}\n\n{citation_line}"
            rebuilt_sections.append(block.strip())

        return "\n\n".join(rebuilt_sections).strip()

    def _format_references(self, contexts: List[FetchedContent]) -> str:
        if not contexts:
            return ""
        lines: List[str] = []
        index = 0
        for ctx in contexts:
            url = str(ctx.url or "").strip()
            if not url:
                continue
            index += 1
            try:
                domain = urlparse(url).netloc.lower().replace("www.", "")
            except (ValueError, TypeError):
                domain = ""
            label = self._sanitize_source_label(ctx.title or domain or "参考資料")
            lines.append(f"{index}. {label}\n{url}")
        if not lines:
            return ""
        return "## 参考文献・出典\n\n" + "\n\n".join(lines)

    def _extract_cta_topic_candidates(self, text: str) -> List[str]:
        """CTA向けに短く扱えるテーマ候補を抽出する。"""
        candidates: List[str] = []

        # 鍵括弧内の語は主題である可能性が高いため優先する
        for phrase in re.findall(r"[「『]([^」』]{4,72})[」』]", text or ""):
            candidate = re.sub(r"\s+", " ", phrase).strip(" -:：")
            if candidate:
                candidates.append(candidate)

        pattern_candidates = (
            r"(.+?)とは何か",
            r"(.+?)とは",
            r"(.+?)について",
            r"(.+?)を(?:解説|整理|振り返|考える|見直す)",
        )
        for pattern in pattern_candidates:
            match = re.search(pattern, text)
            if not match:
                continue
            candidate = re.sub(r"\s+", " ", match.group(1)).strip(" -:：")
            candidate = candidate.rstrip("、。,. のはがをにでとへも")
            if candidate:
                candidates.append(candidate)

        fragments = [
            frag.strip()
            for frag in re.split(r"[：:、,。!?！？／/|｜\-\s]+", text or "")
            if frag and frag.strip()
        ]
        for frag in fragments:
            candidate = re.sub(r"\s+", " ", frag).strip(" -:：")
            candidate = candidate.rstrip("、。,. のはがをにでとへも")
            if candidate:
                candidates.append(candidate)

        deduped: List[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            norm = candidate.strip().lower()
            if not norm or norm in seen:
                continue
            seen.add(norm)
            deduped.append(candidate)
        return deduped

    def _truncate_topic_safely(self, text: str, max_chars: int = 28) -> str:
        """語中断を避けつつCTAトピックを短縮する。"""
        topic = re.sub(r"\s+", " ", text or "").strip(" -:：")
        topic = topic.replace("「", "").replace("」", "").replace("『", "").replace("』", "")
        topic = topic.lstrip("、。,. のはがをにでとへも")
        if not topic:
            return ""
        if len(topic) <= max_chars:
            return topic

        # 区切り記号がある場合は、直前で切る
        prefix = topic[: max_chars + 1]
        boundary_indexes = [
            m.start()
            for m in re.finditer(r"[：:、,。!?！？／/|｜\s]", prefix)
            if m.start() >= 8
        ]
        if boundary_indexes:
            candidate = topic[: boundary_indexes[-1]]
            candidate = candidate.lstrip("、。,. のはがをにでとへも")
            candidate = candidate.rstrip("、。,. のはがをにでとへも")
            if len(candidate) >= 6:
                return candidate

        trimmed = topic[:max_chars]
        trimmed = re.sub(r"[「『（(]+$", "", trimmed)
        trimmed = trimmed.lstrip("、。,. のはがをにでとへも")
        trimmed = trimmed.rstrip("、。,. のはがをにでとへも")
        if len(trimmed) >= 6:
            return trimmed
        return ""

    def _extract_cta_topic(self, title: str, user_prompt: str) -> str:
        """CTAで触れるテーマ名を安全に抽出する。"""
        raw = (title or "").strip() or (user_prompt or "").strip()
        if not raw:
            return "今回のテーマ"
        cleaned = sanitize_untrusted_text(raw, max_length=80)
        cleaned = re.sub(r"https?://\S+", " ", cleaned)
        cleaned = re.sub(r"[\n\r\t]+", " ", cleaned)
        candidate_source = re.sub(r"\s+", " ", cleaned).strip(" -:：")
        candidate_source = re.sub(r"^(今回は|本記事では|この記事では)", "", candidate_source).strip()
        cleaned = re.sub(r"[#*`\"'「」『』\[\]\(\)\{\}<>]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:：")
        cleaned = re.sub(r"^(今回は|本記事では|この記事では)", "", cleaned).strip()
        if not cleaned:
            return "今回のテーマ"

        for candidate in self._extract_cta_topic_candidates(candidate_source or cleaned):
            topic = self._truncate_topic_safely(candidate, max_chars=28)
            if 6 <= len(topic) <= 28:
                return topic

        topic = self._truncate_topic_safely(cleaned, max_chars=28)
        return topic or "今回のテーマ"

    def _normalize_cta_audience(self, target_audience: str) -> str:
        cleaned = sanitize_untrusted_text(target_audience or "", max_length=36)
        cleaned = re.sub(r"[\n\r\t]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:：")
        if re.search(r"(共働き|子育て|育児|単身|高齢|学生|\d{2}代)", cleaned):
            return "読んでくださる方"
        return cleaned or "読んでくださった方"

    def _build_cta_audience_clause(self, audience: str) -> str:
        text = (audience or "").strip()
        if not text:
            return ""
        if re.search(r"(共働き|子育て|育児|単身|高齢|学生|\d{2}代)", text):
            return ""
        if re.search(r"(一般読者|読者|初心者|みなさん|みなさま|利用者|ユーザー)", text):
            return ""
        if len(text) >= 20:
            return ""
        return f"{text}として"

    def _reduce_cta_topic_echo(self, text: str, topic: str) -> str:
        """CTA内で同じトピック名が連続反復する場合、2回目以降を言い換える。"""
        cta = (text or "").strip()
        topic_text = (topic or "").strip()
        if not cta:
            return cta

        def _normalize_phrase(value: str) -> str:
            norm = re.sub(r"\s+", "", value or "")
            return re.sub(r"[?？!！。．・]+$", "", norm)

        # まず topic 指定がある場合は、その引用句を優先して2回目以降だけ置換
        if topic_text:
            topic_norm = _normalize_phrase(topic_text)
            seen_topic = 0

            def _replace_topic(match: re.Match[str]) -> str:
                nonlocal seen_topic
                phrase = match.group(1)
                if _normalize_phrase(phrase) != topic_norm:
                    return match.group(0)
                seen_topic += 1
                if seen_topic >= 2:
                    return "このテーマ"
                return match.group(0)

            cta = re.sub(r"「([^」]+)」", _replace_topic, cta)

        # topic 抽出が弱いケース向けに、同一の長い引用句の連続反復を追加で抑制
        seen_quotes: Dict[str, int] = {}

        def _replace_repeated_quote(match: re.Match[str]) -> str:
            phrase = (match.group(1) or "").strip()
            key = _normalize_phrase(phrase)
            if len(key) < 10:
                return match.group(0)
            seen_quotes[key] = seen_quotes.get(key, 0) + 1
            if seen_quotes[key] >= 2:
                return "このテーマ"
            return match.group(0)

        cta = re.sub(r"「([^」]+)」", _replace_repeated_quote, cta)
        return cta

    def _make_cta(
        self,
        title: str = "",
        user_prompt: str = "",
        target_audience: str = "",
        platform: str = "",
    ) -> str:
        """本文文脈に沿った行動喚起を、過度な断定を避けて生成する。"""
        rng = random.SystemRandom()
        target_platform = (platform or getattr(self, "_output_format", "note") or "note").lower()
        policy = getattr(self, "_pipeline_policy", {}) or {}
        focus = str(policy.get("focus") or self._get_effective_writing_focus() or "explanation")
        evidence_mode = str(policy.get("evidence_mode") or "normal")
        category_policy = getattr(self, "_category_policy", {}) or {}
        category_base = self._safe_contract_value(category_policy.get("base_template")).lower()
        current_type = self._safe_contract_value(getattr(self, "_current_type", "")).lower()
        announcement_like = (
            category_base == "announcement"
            or current_type in {"announcement", "お知らせ", "④お知らせ"}
        )
        topic = self._extract_cta_topic(title, user_prompt)
        audience = self._normalize_cta_audience(target_audience)
        audience_clause = self._build_cta_audience_clause(audience)

        if announcement_like and target_platform == "linkedin":
            templates = [
                f"対象機種や切り替え時期は、公式案内で確認しておくと安心です。",
                f"{audience_clause}設定変更の有無や利用条件は、公式のお知らせを先に確認してください。",
                "利用中の端末や設定に影響がある場合は、事前に案内内容を確認しておくと対応しやすくなります。",
            ]
            return self._clean_redundant_connectives(rng.choice(templates)).strip()

        if announcement_like:
            templates = [
                "対象機種、切り替え時期、設定変更の有無は、公式案内で確認してください。",
                "利用中の端末に影響があるかどうかを、公式のお知らせで先に確認しておくと安心です。",
                "詳細な対象条件や開始時期は、公式情報を基準に確認してください。",
            ]
            return self._clean_redundant_connectives(rng.choice(templates)).strip()

        if target_platform == "linkedin":
            openings = [
                "最後までお読みいただきありがとうございます。",
                "ここまで読んでいただきありがとうございます。",
                "ご覧いただきありがとうございました。",
            ]
            closings = [
                "🔖 必要なタイミングで見返せるよう、保存しておいてください。",
                "🤝 異なる視点があれば、ディスカッションできるとうれしいです。",
                "📣 有益だと感じたら、周囲の方にも共有してください。",
            ]
            if evidence_mode == "strict" or focus == "analysis":
                actions = [
                    f"💬 「{topic}」で重視している確認ポイントがあれば、コメントで教えてください。",
                    f"🔎 {audience_clause}気になる論点や注意点があれば、ぜひ共有してください。",
                    "🧭 一次情報で確認したい論点があれば、次回の整理に反映します。",
                ]
            elif focus == "experience":
                actions = [
                    f"💬 「{topic}」を実践した際の工夫や学びがあれば、共有してください。",
                    f"📌 {audience_clause}現場でのリアルな手触りをコメントでもらえると参考になります。",
                    "🤝 うまくいった点・難しかった点の両方を、次回改善に活かします。",
                ]
            else:
                actions = [
                    f"💬 「{topic}」で分かりにくかった点があれば、コメントで知らせてください。",
                    f"📌 {audience_clause}追加してほしい解説テーマがあれば、教えてください。",
                    "🛠 実務でつまずいたポイントがあれば、次回の補足候補にします。",
                ]

            templates = [
                "{opening}{action}",
                "{action}{closing}",
                "{opening}{action}{closing}",
            ]
            cta = rng.choice(templates).format(
                opening=rng.choice(openings),
                action=rng.choice(actions),
                closing=rng.choice(closings),
            ).strip()
            cta = cta or rng.choice(LINKEDIN_CTA_PATTERNS)
            cta = self._reduce_cta_topic_echo(cta, topic)
            return self._clean_redundant_connectives(cta).strip()

        openings = [
            f"「{topic}」について、少しでもヒントになっていれば嬉しいです。",
            f"「{topic}」の全体像、つかめたでしょうか。",
            f"今回は「{topic}」を整理してみました。",
        ]
        closings = [
            "気になった部分があれば、あとで見返せるように保存しておいてください。",
            "うまくいった点も難しかった点も、次の記事の参考にします。スキで反応をもらえると、次に書くテーマの参考になります。",
            "続きが気になる方は、フォローしておくと新しい記事が届きます。",
        ]
        if evidence_mode == "strict" or focus == "analysis":
            actions = [
                f"「{topic}」について、違う角度からの見方があればコメントで教えてください。",
                f"{audience_clause}実務で確認しているポイントがあれば、ぜひ共有してください。",
                f"「{topic}」で補足すべき観点があれば、次の記事で取り上げます。",
            ]
        elif focus == "experience":
            actions = [
                f"{audience_clause}試してみた感想や工夫があれば、差し支えない範囲で共有してください。",
                f"「{topic}」を実践して気づいたことがあれば、コメントで教えてください。",
                "うまくいった点も難しかった点も、次の記事の参考にします。",
            ]
        else:
            actions = [
                f"「{topic}」で分かりにくかった箇所があれば、コメントで教えてください。",
                f"{audience_clause}もっと掘り下げてほしい部分があれば、追記の参考にします。",
                f"「{topic}」に関して気になることがあれば、気軽にコメントしてください。",
            ]

        templates = [
            "{opening}{action}",
            "{action}{closing}",
        ]
        cta = rng.choice(templates).format(
            opening=rng.choice(openings),
            action=rng.choice(actions),
            closing=rng.choice(closings),
        ).strip()
        cta = cta or rng.choice(CTA_PATTERNS)
        cta = self._reduce_cta_topic_echo(cta, topic)
        return self._clean_redundant_connectives(cta).strip()
    
    def _format_for_linkedin(
        self,
        lead: str,
        body: str,
        cta: str,
        hashtags: str,
        extra_body: Optional[str] = None,
    ) -> str:
        """本文をLinkedIn向けにフォーマット（短縮 + 絵文字 + プレーンテキスト）"""
        import re
        
        # Markdown記法を除去（LinkedInはプレーンテキスト推奨）
        text = re.sub(r'^##\s*', '📌 ', body, flags=re.MULTILINE)  # 見出しを絵文字に
        text = re.sub(r'\*\*(.+?)\*\*', r'【\1】', text)  # 太字を【】に
        text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)  # リストをブレットに
        text = re.sub(r'^---$', '', text, flags=re.MULTILINE)  # 水平線除去
        
        # リード文を先頭に
        linkedin_lead = lead.replace('##', '').strip()
        
        # 渡されたCTAを優先し、空の場合のみ固定候補へフォールバック
        linkedin_cta = (cta or "").strip() or random.choice(LINKEDIN_CTA_PATTERNS)
        
        # ハッシュタグは3〜5個に制限
        tags = hashtags.split()[:5] if hashtags else []
        linkedin_tags = ' '.join(tags)

        target_chars = getattr(self, "_linkedin_target_chars", LINKEDIN_MAX_CHARS)
        target_chars = max(LINKEDIN_MIN_CHARS, min(LINKEDIN_MAX_CHARS, target_chars))

        # 目標文字数に合わせて本文を調整
        separator_len = len("\n\n")
        overhead = len(linkedin_lead) + len(linkedin_cta) + len(linkedin_tags) + separator_len * 3
        body_limit = max(0, target_chars - overhead)
        trimmed_body = text.strip()
        if extra_body:
            trimmed_body = f"{trimmed_body}\n\n{extra_body.strip()}".strip()
        if body_limit and len(trimmed_body) > body_limit:
            trimmed_body = trimmed_body[:body_limit].rstrip()
            # 可能なら文末で切る
            last_break = max(trimmed_body.rfind("。"), trimmed_body.rfind("！"), trimmed_body.rfind("？"), trimmed_body.rfind("\n"))
            if last_break >= max(20, int(body_limit * 0.6)):
                trimmed_body = trimmed_body[: last_break + 1].rstrip()
        
        # 全体を組み立て
        parts = [
            linkedin_lead,
            "",
            trimmed_body,
            "",
            linkedin_cta,
            "",
            linkedin_tags,
        ]
        
        result = "\n".join(parts)
        
        # 最終的な文字数を上限内に収める
        if len(result) > target_chars:
            result = result[:max(0, target_chars - 3)].rstrip() + "..."
        
        return result.strip()
