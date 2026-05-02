"""post_processor_mixin.py - Post-processing mixin for ArticleGenerator."""
from __future__ import annotations

import logging
import random
import re
from typing import List
from note.prompt_echo_detector import detect_prompt_echo_sentences

logger = logging.getLogger(__name__)

_cached_re: dict = {}


def _re(name: str):
    """Lazy accessor to avoid circular import with article_generator."""
    if not _cached_re:
        from note import article_generator as _ag
        for _n in (
            "_RE_HEADING_NEWLINE_FIX", "_RE_SENTENCE_SPLIT",
            "_RE_STRUCTURE_LINE", "_RE_TRIPLE_NEWLINE",
        ):
            _cached_re[_n] = getattr(_ag, _n)
    return _cached_re[name]


class PostProcessorMixin:
    """Mixin providing paragraph normalization and meta-text cleaning."""

    _RE_NON_TERMINAL_FRAGMENT = re.compile(
        r"(?:たり|て|で|が|は|を|に|へ|と|も|や|けど|けれど|ものの|ため|ので|から|し|つつ|ながら|には|では|とは|への|での|からの)$"
    )

    def _get_sentence_split_limits(self) -> tuple[int, int]:
        """文長分割の上限を設定から取得する。"""
        max_chars = 90
        max_splits = 2
        getter = getattr(self, "_get_postprocess_config", None)
        if callable(getter):
            try:
                cfg = getter()
            except Exception:
                cfg = {}
            concise = cfg.get("concise_compaction", {}) if isinstance(cfg, dict) else {}
            if isinstance(concise, dict):
                raw_max_chars = concise.get("max_sentence_chars")
                raw_max_splits = concise.get("max_splits_per_sentence")
                if isinstance(raw_max_chars, (int, float)):
                    max_chars = int(raw_max_chars)
                if isinstance(raw_max_splits, (int, float)):
                    max_splits = int(raw_max_splits)
        max_chars = max(60, min(140, max_chars))
        max_splits = max(1, min(3, max_splits))
        return max_chars, max_splits

    @classmethod
    def _looks_non_terminal_fragment(cls, text: str) -> bool:
        core = (text or "").strip()
        if not core:
            return False
        core = core.rstrip("。！？!?").rstrip("、,").strip()
        if len(core) <= 4:
            return False
        return bool(cls._RE_NON_TERMINAL_FRAGMENT.search(core))

    @staticmethod
    def _is_terminal_line(text: str) -> bool:
        stripped = (text or "").strip()
        if not stripped:
            return False
        return bool(re.search(r"[。！？!?」』）\)]$", stripped))

    def _split_overlong_sentence(self, sentence: str, *, max_chars: int, max_splits: int) -> List[str]:
        """句読点を使って長文を最小分割する。"""
        current = sentence.strip()
        if len(current) <= max_chars or "、" not in current:
            return [current] if current else []

        parts: List[str] = []
        split_budget = max_splits
        while len(current) > max_chars and split_budget > 0 and "、" in current:
            commas = [idx for idx, ch in enumerate(current) if ch == "、"]
            if not commas:
                break

            target = len(current) // 2
            split_idx = None
            head = ""
            tail = ""
            for candidate_idx in sorted(commas, key=lambda idx: abs(idx - target)):
                candidate_head = current[:candidate_idx].strip()
                candidate_tail = current[candidate_idx + 1 :].strip()
                if len(candidate_head) < 24 or len(candidate_tail) < 18:
                    continue
                if self._looks_non_terminal_fragment(candidate_head):
                    continue
                split_idx = candidate_idx
                head = candidate_head
                tail = candidate_tail
                break

            if split_idx is None:
                break

            parts.append(head + "。")
            current = re.sub(
                r"^(?:そして|また|さらに|つまり|要するに|たとえば|例えば|この点で)(?:、|,)?\s*",
                "",
                tail,
            )
            split_budget -= 1

        if current:
            parts.append(current)
        return [p for p in parts if p]

    def _expand_overlong_sentences(self, sentences: List[str]) -> List[str]:
        """長文のみを段階分割して読みやすさを上げる。"""
        if not sentences:
            return sentences
        max_chars, max_splits = self._get_sentence_split_limits()
        expanded: List[str] = []
        for sentence in sentences:
            expanded.extend(
                self._split_overlong_sentence(
                    sentence,
                    max_chars=max_chars,
                    max_splits=max_splits,
                )
            )
        return expanded

    def _clean_meta_output(self, text: str, target_audience: str) -> str:
        """メタ的な視点説明や不自然な呼びかけを除去する。"""
        if not text:
            return ""

        before_headings = self._heading_count(text)

        # 視点メタの除去（本文で「視点/立場/として書く」は書かない）
        # NOTE: 「企業視点では〜」など本文上の正当な論点説明は削りすぎないよう
        # 「書く/述べる」等のメタ言及を伴う文だけを対象にする。
        meta_patterns = [
            r"(?:本記事|この記事|本稿).{0,16}(?:視点|立場).{0,12}(?:書|執筆|語|述べ|伝え)",
            r"(?:私は|わたしは|私たちは|筆者は).{0,16}(?:視点|立場).{0,12}(?:書|執筆|語|述べ|伝え)",
            r"(?:の)?立場から書(?:く|きます|いて)",
        ]

        # ターゲット属性への不自然な呼びかけを除去
        target_terms = [
            "経営層", "経営者", "役員", "取締役", "意思決定者",
            "経営陣", "管理職", "エグゼクティブ", "ボード",
        ]
        address_patterns = [
            r"(?:%s)[^。！？]*?(?:どう思いますか|いかがですか|でしょうか|ですか)[。！？]?" % "|".join(target_terms),
            r"(?:%s)(?:の皆さん|のみなさん|の方々|のみなさま)" % "|".join(target_terms),
        ]
        target_label = (target_audience or "").strip()
        sensitive_re = re.compile(r"(共働き|子育て|育児|単身|独身|高齢|学生|\d{2}代)")
        topic_marker_re = re.compile(r"(について|比較|実態|課題|傾向|分析|市場|調査|統計|データ|白書)")
        scope = " ".join(
            [
                str(getattr(self, "_latest_user_prompt", "") or "").strip(),
                str(getattr(self, "_current_title", "") or "").strip(),
            ]
        ).strip()
        topic_explicit = bool(sensitive_re.search(scope) and topic_marker_re.search(scope))
        suppress_demographic_labels = bool(sensitive_re.search(target_label) and not topic_explicit)

        audience_label_patterns: List[str] = []
        if suppress_demographic_labels:
            audience_label_patterns = [
                r"(?:\d{2}代(?:前半|後半)?)(?:の)?(?:読者|世帯|家庭)?",
                r"共働き(?:の)?(?:世帯|家庭|読者)?",
                r"独身(?:世帯|者)?",
                r"単身(?:世帯|者)?",
                r"子育て(?:世帯|家庭)?",
                r"育児(?:世帯|家庭)?",
                r"高齢(?:者|世帯)?",
                r"学生(?:向け|層)?",
            ]
            if target_label:
                audience_label_patterns.insert(0, re.escape(target_label))

        structure_line_pattern = _re("_RE_STRUCTURE_LINE")
        cleaned_lines: List[str] = []
        prompt_echo_references = list(getattr(self, "_prompt_echo_references", []) or [])

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()

            if not stripped:
                cleaned_lines.append("")
                continue

            if structure_line_pattern.match(stripped):
                cleaned_lines.append(line)
                continue

            # 1行単位で判定し、見出し行や隣接行を巻き込んで削除しない
            segments = [seg.strip() for seg in _re("_RE_SENTENCE_SPLIT").split(stripped) if seg.strip()]
            if not segments:
                cleaned_lines.append(line)
                continue

            kept_segments: List[str] = []
            for segment in segments:
                if any(re.search(p, segment) for p in meta_patterns):
                    continue
                if any(re.search(p, segment) for p in address_patterns):
                    continue
                if detect_prompt_echo_sentences(
                    segment,
                    references=prompt_echo_references,
                    max_hits=1,
                    reference_coverage=0.8,
                ):
                    continue
                normalized_segment = segment
                if audience_label_patterns:
                    for pattern in audience_label_patterns:
                        normalized_segment = re.sub(pattern, "読者", normalized_segment)
                    normalized_segment = re.sub(r"読者(?:の)?(?:読者|世帯|家庭)", "読者", normalized_segment)
                    normalized_segment = re.sub(r"読者{2,}", "読者", normalized_segment)
                normalized_segment = re.sub(r"\s+", " ", normalized_segment).strip()
                if normalized_segment:
                    kept_segments.append(normalized_segment)

            cleaned_lines.append(" ".join(kept_segments).strip() if kept_segments else "")

        cleaned = "\n".join(cleaned_lines)
        cleaned = _re("_RE_HEADING_NEWLINE_FIX").sub(r"\1\n\n", cleaned)
        cleaned = _re("_RE_TRIPLE_NEWLINE").sub("\n\n", cleaned).strip()

        after_headings = self._heading_count(cleaned)
        if before_headings and before_headings != after_headings:
            logger.info(
                "Skip clean_meta_output due heading count change %s->%s.",
                before_headings,
                after_headings,
            )
            return re.sub(r"\n{3,}", "\n\n", text).strip()

        return cleaned

    def _normalize_paragraphs(self, text: str) -> str:
        """段落の息継ぎを整える（長文の詰まりを軽減）。

        R9-T07: 4段落以上の多文段落が連続する場合、1文段落（呼吸段落）を
        1箇所保持してリズムの緩急を作る。
        """
        if not text:
            return ""

        blocks = [b for b in re.split(r"\n{2,}", text) if b.strip()]
        if not blocks:
            return text.strip()

        normalized: List[str] = []
        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # 見出し + 本文が同一ブロックの場合は分離
            if re.match(r"^#+\s+", block):
                lines = block.splitlines()
                heading = lines[0].strip()
                rest = "\n".join(lines[1:]).strip()
                normalized.append(heading)
                if rest:
                    normalized.extend(self._split_long_paragraph(rest))
                continue

            normalized.extend(self._split_long_paragraph(block))

        # R14: 文途中で分断された段落を結合
        normalized = self._merge_broken_paragraphs(normalized)

        # R9-T07: 呼吸段落の保持
        normalized = self._ensure_breathing_paragraph(normalized)

        return "\n\n".join(p.strip() for p in normalized if p.strip()).strip()

    @staticmethod
    def _count_paragraph_sentences(paragraph: str) -> int:
        """段落内の文数を数える（句点・感嘆符・疑問符で区切り）。"""
        return len(re.findall(r"[。！？!?]", paragraph))

    def _ensure_breathing_paragraph(self, paragraphs: List[str]) -> List[str]:
        """R9-T07: 4段落以上の多文段落が連続する場合、1文段落を1箇所保持する。

        既に1文段落が存在すればそのまま保持。存在しなければ、
        連続する多文段落群の中間付近で最初の文を独立段落として分離する。
        """
        if len(paragraphs) < 4:
            return paragraphs

        # 見出し以外の本文段落のみを対象にする
        body_indices = [
            i for i, p in enumerate(paragraphs)
            if p.strip() and not re.match(r"^#+\s+", p.strip())
        ]
        if len(body_indices) < 4:
            return paragraphs

        # 既に1文段落が存在するか確認
        for idx in body_indices:
            if self._count_paragraph_sentences(paragraphs[idx]) <= 1:
                return paragraphs  # 既に呼吸段落がある

        # 連続する多文段落の中間付近で分割
        mid = body_indices[len(body_indices) // 2]
        target = paragraphs[mid]
        sentences = [s for s in re.split(r"(?<=[。！？])\s*", target) if s.strip()]
        if len(sentences) >= 2:
            breathing = sentences[0].strip()
            rest = "".join(sentences[1:]).strip()
            result = list(paragraphs)
            result[mid] = breathing
            result.insert(mid + 1, rest)
            return result

        return paragraphs

    # R14: 文途中で段落が分断されたケースを検出するパターン
    # 前段落が句点「。」で終わるが、次段落が小文字接続（助詞・動詞連用形等）で始まる場合
    _RE_BROKEN_CONTINUATION = re.compile(
        r"^(?:攻撃|対策|防御|管理|組織|情報|全体|結果|影響|効果|問題|課題|状況|"
        r"[ぁ-ん]{1,3}(?:の|は|が|を|に|で|と|も|から|まで|より|へ|って|ので|ため|けど|けれど))"
    )

    @staticmethod
    def _merge_broken_paragraphs(paragraphs: "List[str]") -> "List[str]":
        """R14: 文途中で分断された段落を前段落に結合する。

        検出条件:
        - 前段落が「は。」「は、」「ことは。」等の不完全文で終わる
        - 前段落が助詞で終わる（「することは」等）
        - 次段落が句点なしの短い断片（40字以下）で始まる
        """
        if len(paragraphs) < 2:
            return paragraphs

        merged: "List[str]" = [paragraphs[0]]
        for para in paragraphs[1:]:
            stripped = para.strip()
            prev = merged[-1].strip() if merged else ""

            # 見出しは結合しない
            if re.match(r"^#+\s+", stripped) or re.match(r"^#+\s+", prev):
                merged.append(para)
                continue

            should_merge = False

            # パターン1: 前段落が助詞+句点で終わる不完全文
            # 例: 「参加することは。」「によって。」
            if re.search(r"[はがをにでともへ]。\s*$", prev):
                should_merge = True

            # パターン2: 前段落が助詞で終わる（句点なし）かつ短い段落
            # 例: 「参加することは」
            # R19: 40文字以下の短い段落のみ結合（長い段落のバースト性を保護）
            if not should_merge and len(prev) <= 40 and re.search(r"[はがをにでともへより]$", prev.rstrip("。！？")):
                # 次段落の先頭が文の続きっぽい場合のみ
                if not re.match(r"^(?:##|[-*]|\d+\.)", stripped):
                    should_merge = True

            if should_merge:
                merged[-1] = prev.rstrip() + stripped
            else:
                merged.append(para)

        return merged

    _TOPIC_CHANGE_RE = re.compile(
        r"^(?:ところで|一方で?|ただ(?:し)?|しかし|もっとも|それでも|"
        r"とはいえ|なお|ちなみに|実は|実際には|つまり|要するに)"
    )
    _RE_LINE_CONTINUATION_START = re.compile(
        r"^(?:[ぁ-ん]{1,3}(?:の|は|が|を|に|で|と|も|から|まで|より|へ|って|ので|ため|けど|けれど)|"
        r"ために|そのため|このため)"
    )

    @staticmethod
    def _add_note_sentence_linebreaks(text: str) -> str:
        """note.com 向けに段落内の文末後に改行を挿入する。

        _normalize_paragraphs() の後に適用。機械的な毎文改行を避けるため、
        文途中を切らず、2文以上の段落を文末単位で分割する。
        見出し・箇条書き・URL・既に \\n 済みのブロックはスキップする。
        """
        if not text:
            return text
        result_blocks: list = []
        for block in re.split(r"\n\n", text):
            stripped = block.strip()
            if not stripped:
                result_blocks.append("")
                continue
            # 見出し行は触らない
            if re.match(r"^#+\s", stripped):
                result_blocks.append(stripped)
                continue
            # 箇条書き・番号リストは触らない
            if re.search(r"^\s*[-*・]|\d+\.", stripped, re.M):
                result_blocks.append(stripped)
                continue
            # URL 単独行は触らない
            if re.match(r"^https?://", stripped):
                result_blocks.append(stripped)
                continue
            # 既に \n が含まれている（部分的に改行済み）場合はスキップ
            if "\n" in stripped:
                result_blocks.append(stripped)
                continue
            # 文途中を壊さず、文末ごとに改行を挿入
            sents = [s for s in re.split(r"(?<=[。！？])\s*", stripped) if s.strip()]
            if len(sents) >= 2:
                result_blocks.append("\n".join(sents))
            else:
                result_blocks.append(stripped)
        return "\n\n".join(result_blocks)

    def _get_paragraph_clog_config(self) -> dict:
        """段落の詰まり判定しきい値を取得する。"""
        defaults = {
            "paragraph_clog_min_chars": 240,
            "paragraph_clog_min_sentences": 4,
            "paragraph_clog_min_commas": 5,
            "paragraph_clog_min_comma_density": 0.017,
            "paragraph_clog_threshold_jitter": 0.12,
        }
        getter = getattr(self, "_get_postprocess_config", None)
        if not callable(getter):
            return defaults
        try:
            cfg = getter()
        except Exception:
            return defaults
        concise = cfg.get("concise_compaction", {}) if isinstance(cfg, dict) else {}
        if not isinstance(concise, dict):
            return defaults
        merged = dict(defaults)
        for key in defaults:
            value = concise.get(key)
            if isinstance(value, (int, float)):
                merged[key] = value

        # R19: focus別 paragraph_clog_min_chars override
        effective_focus = getattr(self, "_effective_writing_focus", "")
        focus_overrides = cfg.get("focus_pipeline_overrides", {})
        if effective_focus and isinstance(focus_overrides, dict) and effective_focus in focus_overrides:
            override_chars = focus_overrides[effective_focus].get("paragraph_clog_min_chars_override")
            if isinstance(override_chars, (int, float)):
                merged["paragraph_clog_min_chars"] = int(override_chars)

        merged["paragraph_clog_min_chars"] = max(120, min(320, int(merged["paragraph_clog_min_chars"])))
        merged["paragraph_clog_min_sentences"] = max(2, min(8, int(merged["paragraph_clog_min_sentences"])))
        merged["paragraph_clog_min_commas"] = max(0, min(16, int(merged["paragraph_clog_min_commas"])))
        merged["paragraph_clog_min_comma_density"] = max(
            0.0, min(0.08, float(merged["paragraph_clog_min_comma_density"]))
        )
        merged["paragraph_clog_threshold_jitter"] = max(
            0.0, min(0.35, float(merged["paragraph_clog_threshold_jitter"]))
        )
        return merged

    @staticmethod
    def _stable_text_seed(text: str) -> int:
        sample = (text or "")[:400]
        checksum = 0
        for idx, ch in enumerate(sample):
            checksum = (checksum + ((idx + 1) * ord(ch))) & 0xFFFFFFFF
        return (len(text or "") * 1315423911 + checksum) & 0xFFFFFFFF

    def _is_paragraph_clogged(self, paragraph: str, sentences: List[str], rng: random.Random) -> bool:
        """詰まり判定: 文字数・文数・読点密度の複合条件で評価する。"""
        if not paragraph or not sentences:
            return False

        cfg = self._get_paragraph_clog_config()
        jitter = float(cfg.get("paragraph_clog_threshold_jitter", 0.12) or 0.12)
        chars_floor = int(cfg.get("paragraph_clog_min_chars", 165) or 165)
        sentence_floor = int(cfg.get("paragraph_clog_min_sentences", 4) or 4)
        comma_floor = int(cfg.get("paragraph_clog_min_commas", 5) or 5)
        comma_density_floor = float(cfg.get("paragraph_clog_min_comma_density", 0.017) or 0.017)

        # 段落ごとに閾値を微揺らぎさせる（再現可能な乱数）
        chars_threshold = int(chars_floor * (1.0 + rng.uniform(-jitter, jitter)))
        sentence_threshold = max(2, int(round(sentence_floor + rng.uniform(-1.0, 1.0))))
        comma_threshold = max(0, int(round(comma_floor + rng.uniform(-1.0, 1.0))))
        comma_density_threshold = max(0.0, comma_density_floor * (1.0 + rng.uniform(-jitter * 0.6, jitter * 0.6)))

        comma_count = paragraph.count("、")
        comma_density = comma_count / max(1, len(paragraph))

        signals = 0
        if len(paragraph) >= chars_threshold:
            signals += 1
        if len(sentences) >= sentence_threshold:
            signals += 1
        if comma_count >= comma_threshold:
            signals += 1
        if comma_density >= comma_density_threshold:
            signals += 1

        # 最低2条件で詰まり扱い。1文長文でも読点密度が高い場合は救済。
        if signals >= 2:
            return True
        if len(sentences) == 1 and len(paragraph) >= max(150, chars_threshold - 10) and comma_count >= max(3, comma_threshold):
            return True
        return False

    @staticmethod
    def _sentence_length_cv(sentences: List[str]) -> float:
        """文長の変動係数(CV)を計算する。R19: CV が低い場合に分割をスキップ。"""
        if len(sentences) < 2:
            return 0.0
        lengths = [len(s) for s in sentences]
        mean = sum(lengths) / len(lengths)
        if mean == 0:
            return 0.0
        variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
        return (variance ** 0.5) / mean

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """長い段落を適度に分割する（R9-T06 + R14-T11）。

        R14-T11: 段落分割（\\n\\n）と段落内改行（\\n）を使い分ける。
        - 意味的区切り（話題転換マーカー）→ 段落分割（別チャンク）
        - 2〜3文ごとの区切り → 段落内改行（\\n で結合して1チャンク）
        """
        if not paragraph:
            return []

        # 箇条書きや複数行は無理に再構成しない
        if re.search(r"^\s*(?:-|\*|\d+\.)", paragraph, flags=re.M):
            return [paragraph.strip()]

        # 単一段落内の改行は吸収
        paragraph = paragraph.replace("\n", "")

        sentences = [s for s in re.split(r"(?<=[。！？])\s*", paragraph) if s.strip()]
        if not sentences:
            return [paragraph.strip()]
        sentences = self._expand_overlong_sentences(sentences)
        rng = random.Random(self._stable_text_seed(paragraph))

        # R19: 文長CVが低い（=均一すぎる）場合は分割スキップ（LLMの揺らぎ保護）
        if len(sentences) >= 3 and self._sentence_length_cv(sentences) < 0.15:
            return [paragraph.strip()]

        # 詰まりが弱い段落は分割しない（不自然な改行を防止）
        if not self._is_paragraph_clogged(paragraph, sentences, rng):
            return [paragraph.strip()]

        # R9-T06: 意味的区切り位置を検出（話題転換マーカーの直前）
        semantic_breaks: set = set()
        for idx, sent in enumerate(sentences):
            if idx > 0 and self._TOPIC_CHANGE_RE.match(sent.strip()):
                semantic_breaks.add(idx)

        # R14-T11: 段落分割と段落内改行を使い分ける
        # まず文をグループに分ける（意味的区切りで段落分割、それ以外は同一段落内）
        # Step 1: 意味的区切りで大グループに分ける
        groups: List[List[str]] = []
        current_group: List[str] = []
        for idx, sent in enumerate(sentences):
            if idx in semantic_breaks and current_group:
                groups.append(current_group)
                current_group = []
            current_group.append(sent)
        if current_group:
            groups.append(current_group)

        # Step 2: 各グループ内で段落内改行を入れる
        # UX観点: 改行ゼロだと読み飛ばしが増えるため、句点ごとに適度な確率で改行を挿入。
        # ただし毎文改行は分断感が強いため、1行あたり1〜2文を中心に保つ。
        chunks: List[str] = []
        for group in groups:
            if len(group) <= 2:
                # 短いグループはそのまま1チャンク
                chunks.append("".join(group).strip())
                continue

            lines: List[str] = []
            current_parts: List[str] = []
            current_chars = 0
            base_break_prob = 0.28
            if len(group) >= 6:
                base_break_prob += 0.07
            if len(paragraph) >= 260:
                base_break_prob += 0.04

            for idx, sent in enumerate(group):
                clean_sent = sent.strip()
                if not clean_sent:
                    continue
                current_parts.append(clean_sent)
                current_chars += len(clean_sent)
                remaining = len(group) - idx - 1
                if remaining <= 0:
                    continue

                line_sentence_count = len(current_parts)
                force_break = line_sentence_count >= 3
                prob = base_break_prob
                if line_sentence_count >= 2:
                    prob += 0.22
                if current_chars >= 70:
                    prob += 0.12
                if current_chars < 40 and line_sentence_count == 1:
                    prob -= 0.12
                if remaining == 1 and line_sentence_count == 1:
                    prob -= 0.20
                prob = max(0.10, min(0.66, prob))

                if force_break or rng.random() < prob:
                    line = "".join(current_parts).strip()
                    if line:
                        lines.append(line)
                    current_parts = []
                    current_chars = 0

            if current_parts:
                tail_line = "".join(current_parts).strip()
                if tail_line:
                    lines.append(tail_line)

            # 極端に短い行が連続した場合は前行に吸収して読みの断裂を防ぐ
            merged_lines: List[str] = []
            for line in lines:
                if merged_lines and (
                    self._looks_non_terminal_fragment(merged_lines[-1])
                    or self._RE_LINE_CONTINUATION_START.match(line.strip())
                ):
                    merged_lines[-1] = merged_lines[-1].rstrip() + line
                    continue
                if merged_lines and len(line) < 26 and len(merged_lines[-1]) < 90:
                    merged_lines[-1] = merged_lines[-1].rstrip() + line
                    continue
                merged_lines.append(line)

            if len(merged_lines) <= 1 and len(group) >= 3:
                midpoint = max(1, len(group) // 2)
                head = "".join(group[:midpoint]).strip()
                tail = "".join(group[midpoint:]).strip()
                merged_lines = [seg for seg in (head, tail) if seg]

            # 文途中で分断された行は前行に戻す（改行位置の安全性を優先）
            safe_lines: List[str] = []
            for line in merged_lines:
                cleaned_line = (line or "").strip()
                if not cleaned_line:
                    continue
                if not safe_lines:
                    safe_lines.append(cleaned_line)
                    continue

                prev = safe_lines[-1].rstrip()
                should_merge = (
                    self._looks_non_terminal_fragment(prev)
                    or (not self._is_terminal_line(prev) and len(prev) < 110)
                )
                if should_merge:
                    safe_lines[-1] = prev + cleaned_line.lstrip()
                else:
                    safe_lines.append(cleaned_line)
            merged_lines = safe_lines or merged_lines

            # 段落内改行（\n）で結合して1チャンクにする
            chunks.append("\n".join(merged_lines))

        return chunks or [paragraph.strip()]

    @staticmethod
    def _fix_broken_bold(text: str) -> str:
        """R14: Markdown太字（**）の片方閉じ忘れを修復する。

        - 段落をまたぐ太字（**...\\n\\n...**）を検出し、最初の段落末で閉じる
        - 孤立した `**` 行は前行へ吸収し、見た目崩れを防ぐ
        - 閉じ忘れの孤立 ** を除去する
        """
        if "**" not in text:
            return text

        lines = text.split("\n")
        result_lines: List[str] = []
        bold_open = False

        def _append_close_to_previous_line() -> bool:
            for idx in range(len(result_lines) - 1, -1, -1):
                prev = result_lines[idx].rstrip()
                if not prev:
                    continue
                if not prev.endswith("**"):
                    result_lines[idx] = prev + "**"
                return True
            return False

        for line in lines:
            stripped = line.strip()

            # 単独の強調マーカー行は前行へ吸収（表示崩れ対策）
            if stripped == "**":
                _append_close_to_previous_line()
                bold_open = False
                continue

            # 空行で太字が開いたままなら、前の行末で閉じる
            if not stripped and bold_open:
                _append_close_to_previous_line()
                bold_open = False
                result_lines.append(line)
                continue

            # この行内の ** の数をカウント
            count = stripped.count("**")
            if count % 2 == 1:
                # 奇数個 = 開くか閉じるかのどちらか
                bold_open = not bold_open

            result_lines.append(line)

        # 最終行で太字が開いたままなら閉じる
        if bold_open and result_lines:
            if not _append_close_to_previous_line():
                last = result_lines[-1].rstrip()
                if not last.endswith("**"):
                    result_lines[-1] = last + "**"

        # 念のため残存した孤立 `**` 行を除去
        cleaned_lines: List[str] = []
        for line in result_lines:
            if line.strip() == "**":
                if cleaned_lines:
                    cleaned_lines[-1] = cleaned_lines[-1].rstrip() + "**"
                continue
            cleaned_lines.append(line)

        result = "\n".join(cleaned_lines)

        # ケースA: 閉じ** の直後にひらがな語尾が続く場合、語尾を太字内に取り込む
        # 例: **欠か**せません → **欠かせません**
        result = re.sub(r"(\*\*[^*\n]*[ぁ-ん])\*\*([ぁ-ん]{1,6})", r"\1\2**", result)

        # ケースB: 開き** の直前が漢字の場合（語中開始）は太字マーカーを除去
        # 例: 知的財**産の活用** → 知的財産の活用
        result = re.sub(r"(?<=[一-龥])\*\*([^*\n]+)\*\*", r"\1", result)

        # ケースC: 太字が助詞で始まる場合は語中強調になりやすいため太字を解除
        # 例: 成果**を守る盾** → 成果を守る盾
        result = re.sub(
            r"\*\*((?:を|が|は|に|で|と|も|の|へ|から|より|まで|や|など)[^*\n]{1,42})\*\*",
            r"\1",
            result,
        )

        return result

    @staticmethod
    def _fix_punctuation(text: str) -> str:
        """LLM出力の明確な句読点異常のみを修復する。

        揺らぎ・口語表現は残しつつ、意味が崩れる文末のみ最小修復する。
        """
        if not text:
            return text
        # 0. 「ためにの」→「ための」（助詞重複誤り: 〜するためにの → 〜するための）
        text = re.sub(r"ためにの", "ための", text)
        # 1. 「のなのです」→「なのです」（明確な重複バグ）
        text = re.sub(r"のなのです", "なのです", text)
        # 2. 動詞連用形+「でき。」「つながり。」のみ修復（「し。」「あり。」は口語として正当）
        #    「活用でき。次に〜」→「活用でき、次に〜」
        text = re.sub(r"(でき|つながり)\。([^\n])", r"\1、\2", text)
        # 2-2. 非終止の接続形で誤切断された文を補修
        #    「使いすぎたり。逆に〜」→「使いすぎたり、逆に〜」
        text = re.sub(r"(たり|すぎて|けれど|けど)\。([^\n])", r"\1、\2", text)
        # 2-3. 比較構文の誤切断を補修
        #    「〜とは違い。生成AIは〜」→「〜とは違い、生成AIは〜」
        text = re.sub(r"(とは違い)\。([^\n])", r"\1、\2", text)
        # 3. 連用中止の誤切断を修復（「調整し。次に〜」→「調整し、次に〜」）
        text = re.sub(r"([一-龥々〆ヵヶ]{1,12})し。([^\n])", r"\1し、\2", text)
        # 3-2. 「です、なぜ〜」のような文境界崩れを補修
        text = re.sub(r"(です|ます|だ)、(?=(なぜ|どう|何|なに|いつ|どこ|誰))", r"\1。\2", text)
        # 3-3. 断定終止「〜なのだ、」の読点接続を補修
        text = re.sub(
            r"(なのだ|のだ|なのです|のです|んです)、(?=(その|この|こうした|そうした|実務で|まずは|まず|次に|一方で|加えて|さらに))",
            r"\1。",
            text,
        )
        # 4. 助詞・接続語で終わる不完全文の誤切断を修復
        #    「フレキソフォルダーグルアは。毎分〜」→「フレキソフォルダーグルアは、毎分〜」
        #    「行うため。作業ミス〜」→「行うため、作業ミス〜」
        text = re.sub(
            r"(ことは|ため|ので|によって|として|から|は|が|を|に|で|と|も|へ|より)\。\s*(?:\n\s*)?([^\n#\-\*\d])",
            r"\1、\2",
            text,
        )
        # 5. 「ますよね」「ですよね」は対話感を生む口語表現 → 残す（削除しない）
        return text

    def _combine_sections(self, sections: List[str]) -> str:
        return "\n\n".join(s.strip() for s in sections if s.strip())
