"""outline_mixin.py - Outline generation and structure planning mixin for ArticleGenerator."""
from __future__ import annotations

import json
import logging
import random
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


_cached_consts: dict = {}


def _c(name: str):
    """Lazy accessor to avoid circular import with article_generator."""
    if not _cached_consts:
        from note import article_generator as _ag
        for _n in (
            "BASE_STRUCTURE_GUIDE", "CLOSING_HEADING_PATTERN",
            "FOCUS_SECTION_RULES", "INTRO_HEADING_PATTERN",
            "OPENING_STYLE_GUIDES", "OPENING_STYLE_OPTIONS",
            "PSYCHOLOGY_STRUCTURE_GUIDES", "SECTION_OPENING_HINTS",
            "SUPPLEMENT_HEADING_PATTERN", "WRITING_FOCUS_GUIDES",
        ):
            _cached_consts[_n] = getattr(_ag, _n)
    return _cached_consts[name]


class OutlineMixin:
    """Mixin providing outline generation, structure planning, and writing focus logic."""

    def _generate_outline(self, merged: str, user_prompt: str, article_type: str, target_audience: str) -> List[Dict[str, str]]:
        return self._generate_outline_with_requirements(
            merged=merged,
            user_prompt=user_prompt,
            article_type=article_type,
            target_audience=target_audience,
            title=None,
            required_items=None,
        )

    def _generate_outline_with_requirements(
        self,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        title: Optional[str],
        required_items: Optional[int],
    ) -> List[Dict[str, str]]:
        self._last_outline_user_prompt = user_prompt or ""
        section_min, section_max = self._get_outline_section_range()
        stage_blueprint = self._build_outline_stage_blueprint(article_type, user_prompt)
        flow_options = self._get_outline_flow_options(article_type, user_prompt=user_prompt)
        stage_blueprint_guide = self._render_outline_stage_blueprint_guide(stage_blueprint)
        requirement_line = ""
        if required_items:
            requirement_line = (
                f"- タイトルに合わせて「価値/理由/ポイント」のセクションを必ず{required_items}つ用意すること。\n"
                "- 価値セクションの見出しは「価値1: 〜」「価値2: 〜」のように番号を明示すること。"
            )

        # 参考情報はアウトライン用に圧縮（キーワード中心）
        outline_context_limit = 800 if self._length_mode == "short" else 1200
        ref_summary = (merged[:outline_context_limit] if merged else "なし")

        prompt = f"""
【記事タイトル】{title or "指定なし"}
【テーマ】{self._safe_user_prompt(user_prompt)}
【読者】{target_audience}
【執筆者】{self._current_persona}

【参考情報（抜粋）】
{ref_summary}

【構造ガイド】
- 流れの候補: {flow_options}
- 上記は参考。記事内容に合わせて自由に組み合わせてよい
- 各セクションは新情報または新視点を必ず1つ含め、同じ要旨の繰り返しは禁止
{stage_blueprint_guide}
{requirement_line}

{section_min}〜{section_max}セクションのアウトラインをJSON形式で出力してください。

{{"sections": [
  {{
    "heading": "見出し",
    "purpose": "役割",
    "key_message": "このセクション固有の結論（1文）",
    "source_focus": "参照情報のうち、このセクションで主に使う論点（短語）",
    "do_not_cover": "このセクションでは扱わない既出論点（短文）"
  }}
]}}

【ルール】
- タイトルのテーマ/キーワードに合わせる
- 先頭は背景/問題設定から入り、論点を順に展開する
- 最終は再説明ではなく、補足と実務で試せるヒントで締める
- 各セクションの key_message は互いに重複しないこと
- 各セクションの do_not_cover は、直前セクションで扱った論点を必ず1つ以上含めること
- source_focus は参考情報内の名詞・固有名詞ベースで具体的に書くこと
- JSONのみを出力
""".strip()
        raw = self.llm.generate_text(prompt, max_tokens=1500, task_type="outline")
        result = self._parse_outline(raw)
        result = self._apply_outline_stage_blueprint(result, stage_blueprint)

        # --- JSON完全パースに成功したか判定 ---
        # key_message が空のセクションばかり = 部分パースまたはフォールバック経由
        has_rich_outline = any(s.get("key_message") for s in result)
        if has_rich_outline and len(result) >= 2:
            return result

        # --- リトライ: さらに簡素なプロンプトで再生成 ---
        logger.info("Outline JSON was truncated or fell back. Retrying with minimal prompt.")
        minimal_prompt = f"""
記事タイトル: {title or "指定なし"}
テーマ: {self._safe_user_prompt(user_prompt)}
読者: {target_audience}

{section_min}〜{section_max}セクションの見出し一覧をJSONで出力。
{{"sections": [{{"heading": "見出し", "purpose": "役割", "key_message": "固有結論", "do_not_cover": "除外論点"}}]}}
先頭は背景/問題設定、最終は補足と実務ヒントで締める。JSONのみ出力。
""".strip()
        raw_retry = self.llm.generate_text(minimal_prompt, max_tokens=800, task_type="outline")
        retry_result = self._parse_outline(raw_retry)
        retry_result = self._apply_outline_stage_blueprint(retry_result, stage_blueprint)
        if len(retry_result) >= 2:
            logger.info("Minimal outline retry succeeded: %d sections", len(retry_result))
            return retry_result
        logger.warning("Minimal outline retry also failed. Using initial result.")
        # 両方失敗した場合、より良い方を返す
        return result if len(result) >= len(retry_result) else retry_result

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Remove markdown code fences (```json ... ``` etc.) wrapping JSON.

        Handles variable-length backtick fences (3+), optional language tags,
        leading whitespace, and trailing whitespace around fences.
        """
        # 1. ブロック単位で除去（```lang ... ``` を中身だけに置換）
        #    [^\S\n]* = 同一行の空白（改行以外）を許容
        #    \S* = 言語タグ（json 等）。``` json のようにスペース挟みも許容
        stripped = re.sub(
            r"^\s*`{3,}[^\S\n]*\S*[^\S\n]*\n(.*?)\n\s*`{3,}[^\S\n]*$",
            r"\1",
            text,
            flags=re.S | re.M,
        )
        if stripped != text:
            return stripped
        # 2. ブロック正規表現で取れなかった場合、行単位でフェンス行を除去
        return re.sub(r"^\s*`{3,}[^\S\n]*\S*[^\S\n]*$", "", text, flags=re.M)

    _HEADING_REJECT_RE = re.compile(
        r'[{}\[\]"`\\]'
        r'|^\s*```'
        r'|^\s*"\w+"\s*:'
        r'|^\s*\]\s*,?\s*$'
    )
    _HEADING_AI_LABEL_RE = re.compile(
        r"(追記の要点|すべき具体的な一歩|まず結論|結論から言うと|.+?視点で見る)"
    )

    @classmethod
    def _is_valid_heading(cls, text: str) -> bool:
        """見出しとして妥当か判定。JSON構文文字を含む場合は拒否。"""
        if not text or not text.strip():
            return False
        if cls._HEADING_AI_LABEL_RE.search(text.strip()):
            return False
        return not cls._HEADING_REJECT_RE.search(text)

    def _parse_outline(self, raw: str) -> List[Dict[str, str]]:
        _, section_max = self._get_outline_section_range()
        # --- 正規JSONパース ---
        try:
            cleaned = self._strip_code_fences(raw)
            match = re.search(r"\{.*\}", cleaned, re.S)
            if match:
                data = json.loads(match.group(0))
                sections = data.get("sections", [])
                valid_sections = self._validate_outline_sections(sections)
                if valid_sections:
                    return valid_sections[:section_max]
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.debug("Outline JSON parse failed", exc_info=exc)

        # --- 切れたJSONの部分パース（max_tokensで途中切断された場合） ---
        try:
            cleaned = self._strip_code_fences(raw)
            partial_sections = self._try_partial_json_parse(cleaned)
            if partial_sections:
                valid_sections = self._validate_outline_sections(partial_sections)
                if valid_sections:
                    logger.info("Outline recovered from truncated JSON: %d sections", len(valid_sections))
                    return valid_sections[:section_max]
        except Exception as exc:
            logger.debug("Outline partial JSON recovery failed", exc_info=exc)

        # フォールバック: テキスト解析
        logger.warning("Outline JSON path failed, using fallback line parser (raw=%s)", raw[:200])
        _json_noise = re.compile(
            r'^[\s\[\]{}"`,:\\]+$'
            r'|^```'
            r'|^\{'
            r'|^\]'
            r'|^"\w+"'
            r'|^まとめ[：:]'
            r'|purpose|required_elements|key_message|source_focus|do_not_cover'
        )
        headings = []
        for line in raw.splitlines():
            line = line.strip("-・ ").strip()
            if not line:
                continue
            if _json_noise.match(line):
                continue
            if not self._is_valid_heading(line):
                continue
            if re.match(r"^\d+\.", line):
                line = re.sub(r"^\d+\.\s*", "", line)
            if line:
                headings.append({"heading": line, "purpose": "本文執筆", "required_elements": [], "key_message": "", "source_focus": "", "do_not_cover": ""})

        if headings:
            return headings[:section_max]
        # 記事タイプに応じた最低限の構成を返す（複数バリエーションからランダム選択）
        import random as _rmod
        _type = getattr(self, "_current_type", "")
        _prompt = str(getattr(self, "_last_outline_user_prompt", "") or "")
        stage_fallback = self._build_fallback_outline_from_stage_blueprint(_type, _prompt)
        if stage_fallback:
            return stage_fallback[:section_max]
        _empty = {"required_elements": [], "key_message": "", "source_focus": "", "do_not_cover": ""}
        _type_variants = {
            "branding": [
                [
                    {"heading": "背景と課題", "purpose": "読者の共感を得る導入", **_empty},
                    {"heading": "取り組みと強み", "purpose": "具体的な価値を伝える", **_empty},
                    {"heading": "最後に", "purpose": "読者への提案で締める", **_empty},
                ],
                [
                    {"heading": "きっかけと想い", "purpose": "原点のストーリーで引き込む", **_empty},
                    {"heading": "価値と実績", "purpose": "提供する価値を具体的に伝える", **_empty},
                    {"heading": "これからの展望", "purpose": "読者と未来を共有する", **_empty},
                    {"heading": "補足", "purpose": "読者が判断しやすい観点を添える", **_empty},
                ],
            ],
            "case_study": [
                [
                    {"heading": "導入の背景", "purpose": "課題と経緯を整理する", **_empty},
                    {"heading": "実施内容と成果", "purpose": "具体的な取り組みと結果を示す", **_empty},
                    {"heading": "最後に", "purpose": "学びと実務示唆を示す", **_empty},
                ],
                [
                    {"heading": "課題の全体像", "purpose": "何が問題だったかを明確にする", **_empty},
                    {"heading": "選定と導入プロセス", "purpose": "意思決定の経緯を伝える", **_empty},
                    {"heading": "成果と気づき", "purpose": "定量・定性の結果を示す", **_empty},
                    {"heading": "追記", "purpose": "再現性のあるポイントを整理する", **_empty},
                ],
            ],
            "announcement": [
                [
                    {"heading": "概要", "purpose": "変更点を端的に伝える", **_empty},
                    {"heading": "詳細", "purpose": "背景と具体的な内容を説明する", **_empty},
                    {"heading": "補足", "purpose": "読者への影響と今後を示す", **_empty},
                ],
                [
                    {"heading": "何が変わるのか", "purpose": "変更点を順に示す", **_empty},
                    {"heading": "背景と経緯", "purpose": "なぜこの変更に至ったかを説明する", **_empty},
                    {"heading": "今後の予定", "purpose": "今後の予定とスケジュールを示す", **_empty},
                ],
            ],
        }
        default_variants = [
            [
                {"heading": "背景と問題設定", "purpose": "テーマの導入", **_empty},
                {"heading": "本題の整理", "purpose": "核心の解説", **_empty},
                {"heading": "最後に", "purpose": "結論と補足", **_empty},
            ],
            [
                {"heading": "なぜ今このテーマなのか", "purpose": "読者の関心と接続する", **_empty},
                {"heading": "押さえておきたい論点", "purpose": "論点を整理する", **_empty},
                {"heading": "実践のヒント", "purpose": "読者が動けるようにする", **_empty},
                {"heading": "追記", "purpose": "全体を振り返る", **_empty},
            ],
        ]
        variants = _type_variants.get(_type, default_variants)
        return _rmod.choice(variants)

    def _validate_outline_sections(self, sections: list) -> List[Dict[str, str]]:
        """セクションリストをバリデーションし、有効な見出しのみ返す。"""
        valid_sections: List[Dict[str, str]] = []
        for s in sections:
            if isinstance(s, dict) and "heading" in s:
                heading = str(s["heading"]).strip()
                if not self._is_valid_heading(heading):
                    logger.warning("Outline heading rejected (JSON noise): %s", heading[:80])
                    continue
                heading = self._normalize_summary_heading_if_needed(heading)
                s["heading"] = heading
                s.setdefault("key_message", "")
                s.setdefault("source_focus", "")
                s.setdefault("do_not_cover", "")
                valid_sections.append(s)
        return valid_sections

    def _normalize_summary_heading_if_needed(self, heading: str) -> str:
        """「まとめ」見出しを必要時のみ許可し、通常は自然な締め見出しへ寄せる。"""
        raw = (heading or "").strip()
        if not raw:
            return raw
        if not re.match(r"^まとめ(?:[：:].*)?$", raw):
            return raw
        # 解析コンテキストがない場合（テスト等の直接呼び出し）は現状維持
        if not hasattr(self, "_last_outline_user_prompt"):
            return raw
        if self._should_keep_summary_heading():
            return raw

        suffix = re.sub(r"^まとめ[：:]\s*", "", raw).strip()
        if suffix:
            compact = re.sub(r"\s+", " ", suffix).strip()
            if len(compact) <= 24:
                return f"{compact}の要点"
        return random.choice(["最後に", "補足", "要点整理"])

    def _should_keep_summary_heading(self) -> bool:
        """ユーザーが要約/総括を明示した場合のみ「まとめ」見出しを維持する。"""
        prompt = str(getattr(self, "_last_outline_user_prompt", "") or "")
        if not prompt:
            return True
        return bool(re.search(r"(まとめ|要約|総括|結論|締め|最後に|補足|追記)", prompt))

    @staticmethod
    def _try_partial_json_parse(text: str) -> Optional[list]:
        """max_tokensで途中切断されたJSONから heading を抽出する。

        LLMが ``{"sections": [{...}, {... `` のように途中で切れた場合、
        正規表現で個々の heading 値を拾い出す。
        """
        headings_found = re.findall(
            r'"heading"\s*:\s*"([^"]{2,80})"',
            text,
        )
        if not headings_found:
            return None
        sections = []
        for h in headings_found:
            h = h.strip()
            if h:
                sections.append({
                    "heading": h,
                    "purpose": "",
                    "required_elements": [],
                    "key_message": "",
                    "source_focus": "",
                    "do_not_cover": "",
                })
        return sections if sections else None

    def _fit_outline_to_length_mode(self, outline: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not outline:
            return outline
        _, section_max = self._get_outline_section_range()
        if len(outline) <= section_max:
            return outline

        if section_max <= 1:
            return [outline[0]]

        trimmed = outline[: section_max - 1]
        last = outline[-1]
        last_heading = (last or {}).get("heading", "")
        if last_heading and all(last_heading != (item or {}).get("heading", "") for item in trimmed):
            trimmed.append(last)
        else:
            trimmed.append(outline[section_max - 1])
        return trimmed

    def _classify_outline_heading_role(self, heading: str) -> str:
        text = (heading or "").strip()
        if not text:
            return "core"
        if _c("CLOSING_HEADING_PATTERN").search(text):
            return "closing"
        if _c("SUPPLEMENT_HEADING_PATTERN").search(text):
            return "supplement"
        if _c("INTRO_HEADING_PATTERN").search(text):
            return "intro"
        return "core"

    def _rebalance_outline_flow(self, outline: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """アウトラインの流れを整える（補足は中盤以降、結論は末尾寄せ）。"""
        if not outline or len(outline) < 3:
            return outline

        intro_sections: List[Dict[str, str]] = []
        core_sections: List[Dict[str, str]] = []
        supplement_sections: List[Dict[str, str]] = []
        closing_sections: List[Dict[str, str]] = []

        for section in outline:
            role = self._classify_outline_heading_role((section or {}).get("heading", ""))
            if role == "intro":
                intro_sections.append(section)
            elif role == "supplement":
                supplement_sections.append(section)
            elif role == "closing":
                closing_sections.append(section)
            else:
                core_sections.append(section)

        # 先頭は導入 > 本論 > 補足 > 結論の優先で配置
        ordered: List[Dict[str, str]] = []
        if intro_sections:
            ordered.append(intro_sections.pop(0))
        ordered.extend(core_sections)
        ordered.extend(intro_sections)

        # 補足は本文の中盤〜後半へ。末尾結論の直前が基本。
        if supplement_sections:
            if ordered:
                core_len = len(ordered)
                mid_index = max(1, core_len // 2)
                jitter = random.choice([0, 0, 1]) if core_len >= 4 else 0
                insert_at = min(core_len, mid_index + jitter)
                ordered[insert_at:insert_at] = supplement_sections
            else:
                ordered.extend(supplement_sections)

        ordered.extend(closing_sections)

        # 補足が先頭寄りに残る場合の最終補正（本論があるときのみ）
        if core_sections and len(ordered) >= 4:
            min_supp_index = max(2, len(ordered) // 2)
            closing_start = len(ordered)
            for idx, section in enumerate(ordered):
                role = self._classify_outline_heading_role((section or {}).get("heading", ""))
                if role == "closing":
                    closing_start = idx
                    break
            idx = 0
            while idx < len(ordered):
                role = self._classify_outline_heading_role((ordered[idx] or {}).get("heading", ""))
                if role == "supplement" and idx < min_supp_index:
                    section = ordered.pop(idx)
                    insert_at = min(max(min_supp_index, closing_start - 1), len(ordered))
                    ordered.insert(insert_at, section)
                    closing_start = len(ordered)
                    for j, sec in enumerate(ordered):
                        if self._classify_outline_heading_role((sec or {}).get("heading", "")) == "closing":
                            closing_start = j
                            break
                    continue
                idx += 1

        return ordered if ordered else outline

    def _ensure_outline_closing_section(self, outline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """終端に締めセクションが無い場合、末尾を締めロールに寄せる。"""
        if not outline:
            return outline

        normalized: List[Dict[str, Any]] = []
        for section in outline:
            normalized.append(dict(section) if isinstance(section, dict) else {"heading": str(section or "")})

        closing_indices: List[int] = []
        for idx, section in enumerate(normalized):
            heading = str((section or {}).get("heading", "") or "").strip()
            stage_role = str((section or {}).get("stage_role", "") or "").strip().lower()
            if (
                stage_role == "closing"
                or self._classify_outline_heading_role(heading) == "closing"
                or self._classify_outline_stage(section) == "closing"
            ):
                closing_indices.append(idx)

        has_explicit_closing = bool(closing_indices)
        target_idx = closing_indices[-1] if closing_indices else (len(normalized) - 1)
        target = normalized[target_idx]

        heading = str(target.get("heading", "") or "").strip()
        heading_placeholder_re = re.compile(
            r"^(本文|本題|補足|追記|見出し[A-Za-z0-9一二三四五六七八九十]*)$"
        )
        action_oriented_heading_re = re.compile(
            r"(最後に|まとめ|結論|要点|次の一歩|判断ポイント|実務ポイント|チェック)"
        )
        should_relabel = (
            not heading
            or bool(_c("SUPPLEMENT_HEADING_PATTERN").search(heading))
            or bool(heading_placeholder_re.search(heading))
            or (
                not has_explicit_closing
                and not action_oriented_heading_re.search(heading)
            )
        )
        if should_relabel:
            target["heading"] = self._build_closing_heading(heading)

        target["stage_role"] = "closing"

        purpose = str(target.get("purpose", "") or "").strip()
        purpose_generic = purpose in {"", "本文執筆", "本論", "補足", "導入", "結論", "まとめ"}
        purpose_recap_only = ("振り返" in purpose) and not re.search(r"(判断|行動|次に取る行動|優先順位)", purpose)
        if purpose_generic or purpose_recap_only:
            target["purpose"] = "定義や背景の再説明を避け、判断軸と次に取る行動を具体化する"

        required_elements = target.get("required_elements")
        if not isinstance(required_elements, list):
            required_elements = []
        normalized_elements = [str(item).strip() for item in required_elements if str(item).strip()]
        if not any(re.search(r"(判断軸|判断基準)", item) for item in normalized_elements):
            normalized_elements.append("判断軸")
        if not any(re.search(r"(次の一歩|次に取る行動|行動|アクション)", item) for item in normalized_elements):
            normalized_elements.append("次に取る行動")
        if not any(re.search(r"(注意点|落とし穴|優先順位)", item) for item in normalized_elements):
            normalized_elements.append("見落としやすい注意点")
        target["required_elements"] = normalized_elements[:4]

        return normalized

    def _build_closing_heading(self, _fallback_heading: str = "") -> str:
        """締めセクションの見出しを構築する。

        記事タイトルからテーマを抽出し、行動に繋がる見出しにする。
        タイトルが取得できない場合は簡潔なフォールバックを使う。
        """
        title = str(getattr(self, "_current_title", "") or "").strip()
        if title:
            theme = self._extract_closing_heading_theme(title, max_chars=18)
            if theme and len(theme) <= 16:
                return f"最後に: {theme}の判断ポイント"
        # タイトルが空の場合のフォールバック
        _closing_variants = [
            "最後に: 実務での判断ポイント",
            "最後に: チェックポイント",
            "最後に: 判断の目安",
            "最後に: すぐ試せる行動",
            "最後に: 次の一歩",
        ]
        _closing_weights = [0.34, 0.26, 0.20, 0.14, 0.06]
        import random as _rmod
        return _rmod.choices(_closing_variants, weights=_closing_weights, k=1)[0]

    def _extract_closing_heading_theme(self, title: str, max_chars: int = 24) -> str:
        """締め見出し用に、語中断しにくい短いテーマを抽出する。"""
        theme = re.sub(r"^#+\s*", "", title or "")
        theme = re.sub(r"[！!？?]+$", "", theme).strip()
        if not theme:
            return ""

        quoted = re.search(r"[「『]([^」』]{4,72})[」』]", theme)
        if quoted:
            candidate = re.sub(r"\s+", " ", quoted.group(1)).strip(" -:：")
            if 4 <= len(candidate) <= max_chars:
                return candidate

        normalized = theme.replace("「", " ").replace("」", " ").replace("『", " ").replace("』", " ")
        normalized = re.sub(r"\s+", " ", normalized).strip(" -:：")
        if len(normalized) <= max_chars:
            return normalized

        for pattern in (r"(.+?)とは何か", r"(.+?)とは", r"(.+?)について", r"(.+?)を(?:解説|整理|振り返)"):
            match = re.search(pattern, normalized)
            if not match:
                continue
            candidate = match.group(1).strip(" -:：")
            candidate = candidate.rstrip("、。,. のはがをにでとへも")
            if 6 <= len(candidate) <= max_chars:
                return candidate

        fragments = [
            frag.strip()
            for frag in re.split(r"[：:、,。!?！？／/|｜\-]", normalized)
            if frag and frag.strip()
        ]
        for frag in fragments:
            candidate = frag.rstrip("、。,. のはがをにでとへも")
            if 6 <= len(candidate) <= max_chars:
                return candidate

        prefix = normalized[: max_chars + 1]
        boundaries = [m.start() for m in re.finditer(r"[：:、,。!?！？／/|｜\s]", prefix) if m.start() >= 8]
        if boundaries:
            candidate = normalized[: boundaries[-1]]
            candidate = candidate.rstrip("、。,. のはがをにでとへも")
            if len(candidate) >= 6:
                return candidate

        clipped = normalized[:max_chars]
        clipped = re.sub(r"[（(]+$", "", clipped)
        clipped = clipped.rstrip("、。,. のはがをにでとへも")
        return clipped if len(clipped) >= 4 else ""

    def _extract_number_requirement(self, title: str, user_prompt: str) -> Optional[int]:
        """タイトル/ユーザー指示に含まれる数の要求を抽出する。"""
        text = f"{title} {user_prompt}"
        digit_pattern = re.search(
            r"(\d+)\s*(?:つ|個|大|項目?|大価値|価値|理由|ポイント|メリット|効果)",
            text,
        )
        if digit_pattern:
            try:
                value = int(digit_pattern.group(1))
                return value if 1 <= value <= 10 else None
            except ValueError:
                pass

        kanji_pattern = re.search(
            r"([一二三四五六七八九十])\s*(?:つ|個|大|項目?|大価値|価値|理由|ポイント|メリット|効果)",
            text,
        )
        if kanji_pattern:
            return self._kanji_to_int(kanji_pattern.group(1))

        return None

    def _prefers_numbered_title(self, user_prompt: str) -> bool:
        """ユーザー指示から番号タイトルの優先度を推定する。"""
        if not user_prompt:
            return False
        if re.search(r"\d+\s*(?:つ|個|大|項目?|大価値|価値|理由|ポイント|メリット|効果)", user_prompt):
            return True
        if re.search(r"(?:三|四|五|六|七|八|九|十)\s*(?:つ|個|大|項目?|大価値|価値|理由|ポイント|メリット|効果)", user_prompt):
            return True
        if re.search(r"\b3大\b|\b3つ\b", user_prompt):
            return True
        return False

    def _get_structure_guide(self) -> str:
        """選択された構造ガイドを返す（専門用語なし）。"""
        key = getattr(self, "_psychology_structure", "auto")
        extra = _c("PSYCHOLOGY_STRUCTURE_GUIDES").get(key, "")
        if extra:
            return f"{_c('BASE_STRUCTURE_GUIDE')}\n{extra}".strip()
        return _c("BASE_STRUCTURE_GUIDE")

    def _normalize_writing_focus(self, writing_focus: Optional[str]) -> str:
        key = (writing_focus or "auto").strip().lower()
        if key in _c("WRITING_FOCUS_GUIDES"):
            return key
        return "auto"

    def _infer_writing_focus(self, user_prompt: str, merged_context: str) -> str:
        text = "\n".join(
            [
                user_prompt or "",
                self._interview_answers.get("message", ""),
                merged_context[:1200] if merged_context else "",
            ]
        )
        scores = {
            "analysis": len(re.findall(r"(分析|比較|検証|統計|データ|調査|根拠|仮説|示唆|因果)", text)),
            "experience": len(re.findall(r"(体験|経験|失敗|気づき|実話|エピソード|感情|本音|振り返り|学び)", text)),
            "explanation": len(re.findall(r"(解説|初心者|わかりやす|入門|手順|使い方|基礎|まとめ|ポイント)", text)),
        }
        best = max(scores.items(), key=lambda kv: kv[1])
        if best[1] > 0:
            return best[0]
        type_default = {
            "branding": "experience",
            "ai": "explanation",
            "announcement": "explanation",
            "case_study": "analysis",
        }
        return type_default.get(getattr(self, "_current_type", ""), "explanation")

    def _get_effective_writing_focus(self) -> str:
        focus = getattr(self, "_effective_writing_focus", "")
        if focus in _c("WRITING_FOCUS_GUIDES"):
            return focus
        raw = getattr(self, "_writing_focus", "auto")
        if raw in _c("WRITING_FOCUS_GUIDES") and raw != "auto":
            return raw
        return "explanation"

    def _get_writing_focus_guide(self) -> str:
        """本文の重心（解説/経験/分析）を返す。"""
        key = self._get_effective_writing_focus()
        return _c("WRITING_FOCUS_GUIDES").get(key, "")

    def _get_focus_section_rules(self) -> str:
        key = self._get_effective_writing_focus()
        return _c("FOCUS_SECTION_RULES").get(key, "")

    def _get_outline_layer_rule(self) -> str:
        """R9-T10: 解説/分析記事向け3層構造ルールを返す。"""
        focus = self._get_effective_writing_focus()
        if focus not in ("explanation", "analysis"):
            return ""
        return (
            "【解説・分析記事の3層構造（R9）】\n"
            "各セクションの required_elements は以下の3層を意識して設計すること:\n"
            "  1. 主張（Claim）: そのセクションで伝えたい論点を1文で\n"
            "  2. 根拠（Evidence）: 主張を支えるデータ・事実・引用\n"
            "  3. 具体例（Example）: 読者がイメージできる実例・ケーススタディ\n"
            "- 3層すべてを毎セクションに入れる必要はないが、根拠なき主張・具体例なき抽象論を避ける\n"
            "- 導入セクションは「問い→背景」、結びセクションは「要約→補足/示唆」でよい"
        )

    def _is_diary_like_request(self, article_type: str, user_prompt: str) -> bool:
        """日記・日々の出来事中心の題材かを推定する。"""
        text = " ".join(
            [
                article_type or "",
                user_prompt or "",
                str(getattr(self, "_current_title", "") or ""),
            ]
        )
        if re.search(r"(日々|日記|出来事|雑記|近況|今日|昨日|一日|週末|暮らし|振り返り)", text):
            return True
        focus = self._get_effective_writing_focus()
        # customジャンルで経験寄りの場合は、台本を軽くして「対策」を強制しない。
        if focus == "experience" and article_type not in {"ai", "announcement", "case_study"}:
            return True
        return False

    def _should_include_countermeasure_stage(self, article_type: str, user_prompt: str) -> bool:
        """「対策」セクションを台本に含めるか判定する。"""
        text = " ".join(
            [
                article_type or "",
                user_prompt or "",
                str(getattr(self, "_current_title", "") or ""),
            ]
        )
        if re.search(r"(対策|防止|対応|改善|予防|チェック|手順|対処|ガイド|注意点|リスク管理)", text):
            return True
        if self._is_diary_like_request(article_type, user_prompt):
            return False
        if article_type in {"ai", "case_study"}:
            return True
        focus = self._get_effective_writing_focus()
        return focus in {"analysis", "explanation"} and article_type != "announcement"

    def _build_outline_stage_blueprint(self, article_type: str, user_prompt: str) -> Dict[str, Any]:
        """記事タイプに応じた段階台本（導入/仕組み/事例/対策/結論）を決める。"""
        focus = self._get_effective_writing_focus()
        diary_like = self._is_diary_like_request(article_type, user_prompt)
        include_countermeasure = self._should_include_countermeasure_stage(article_type, user_prompt)

        if article_type == "announcement":
            stages = ["intro", "mechanism", "closing"]
        elif diary_like:
            stages = ["intro", "case", "closing"]
        elif focus == "experience":
            stages = ["intro", "case"]
            if include_countermeasure:
                stages.append("countermeasure")
            stages.append("closing")
        else:
            stages = ["intro", "mechanism", "case"]
            if include_countermeasure:
                stages.append("countermeasure")
            stages.append("closing")

        return {
            "focus": focus,
            "diary_like": diary_like,
            "include_countermeasure": include_countermeasure,
            "stages": stages,
        }

    @staticmethod
    def _stage_label(stage: str) -> str:
        labels = {
            "intro": "導入",
            "mechanism": "仕組み",
            "case": "事例",
            "countermeasure": "対策",
            "closing": "結論",
        }
        return labels.get(stage, stage)

    def _render_outline_stage_blueprint_guide(self, blueprint: Dict[str, Any]) -> str:
        stages = [self._stage_label(stage) for stage in blueprint.get("stages", [])]
        if not stages:
            return ""
        lines = [
            "- 段階台本: " + " -> ".join(stages),
            "- 章ごとの役割を混在させず、1章1役割を優先する",
            "- 前章を受けた接続を1文入れてから新情報へ進む",
        ]
        if blueprint.get("diary_like"):
            lines.append("- 日々の出来事系では、無理に「対策」章を作らない")
        elif blueprint.get("include_countermeasure"):
            lines.append("- 「対策」章では、すぐ実行できる確認項目を具体化する")
        return "\n".join(lines)

    def _classify_outline_stage(self, section: Dict[str, Any]) -> str:
        heading = str((section or {}).get("heading", "") or "")
        purpose = str((section or {}).get("purpose", "") or "")
        text = f"{heading} {purpose}"
        if _c("CLOSING_HEADING_PATTERN").search(heading) or re.search(r"(結論|締め|最後に|振り返り)", text):
            return "closing"
        if re.search(r"(対策|防止|対応|改善|予防|チェック|手順|ガード)", text):
            return "countermeasure"
        if re.search(r"(事例|ケース|具体例|実例|体験|経験|出来事|現場)", text):
            return "case"
        if re.search(r"(仕組み|構造|メカニズム|背景|論点|原因|なぜ|全体像)", text):
            return "mechanism"
        if _c("INTRO_HEADING_PATTERN").search(heading) or re.search(r"(導入|はじめに|問題設定|きっかけ)", text):
            return "intro"
        return "core"

    def _retag_section_for_stage(self, section: Dict[str, Any], stage: str) -> Dict[str, Any]:
        updated = dict(section) if isinstance(section, dict) else {"heading": str(section or "")}
        purpose_defaults = {
            "intro": "読者の疑問と背景を短く共有する",
            "mechanism": "仕組みと論点の構造を整理する",
            "case": "具体的な事例で理解を固定する",
            "countermeasure": "実行可能な対策と確認項目を示す",
            "closing": "再説明を避け、判断軸と次に取る行動を示す",
        }
        heading_defaults = {
            "mechanism": "仕組みと論点",
            "case": "具体事例",
            "countermeasure": "対策と実務ポイント",
        }
        current_purpose = str(updated.get("purpose", "") or "").strip()
        if (not current_purpose) or current_purpose in {"本文執筆", "本論", "補足", "導入", "結論", "まとめ"}:
            updated["purpose"] = purpose_defaults.get(stage, "本文執筆")
        if stage in heading_defaults:
            heading = str(updated.get("heading", "") or "").strip()
            if not heading or re.search(r"^(本文|本題|補足|見出し[A-Za-z0-9一二三四五六七八九十]*)$", heading):
                updated["heading"] = heading_defaults[stage]
        updated["stage_role"] = stage
        return updated

    def _attach_outline_transition_hints(self, outline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not outline:
            return outline
        hints: List[Dict[str, Any]] = []
        prev_stage = ""
        prev_heading = ""
        for idx, section in enumerate(outline):
            item = dict(section) if isinstance(section, dict) else {"heading": str(section or "")}
            stage = self._classify_outline_stage(item)
            if idx == 0:
                item["transition_from_prev"] = ""
            else:
                transition_map = {
                    ("intro", "mechanism"): "直前で示した背景を受け、ここでは「なぜ起きるか」を構造で説明する。",
                    ("mechanism", "case"): "直前の仕組み説明を、具体的な事例に落として理解を固定する。",
                    ("case", "countermeasure"): "直前の事例で見えた課題を、実務で使える対策へ接続する。",
                    ("countermeasure", "closing"): "直前の対策を踏まえ、最後に判断軸と次に取る行動を短く整理する。",
                }
                item["transition_from_prev"] = transition_map.get(
                    (prev_stage, stage),
                    f"「{prev_heading}」で示した内容を受け、視点を一段進めて説明する。",
                )
            prev_stage = stage
            prev_heading = str(item.get("heading", "") or "")
            hints.append(item)
        return hints

    def _apply_outline_stage_blueprint(
        self,
        outline: List[Dict[str, Any]],
        blueprint: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """段階台本に沿って章順を整え、章間接続ヒントを付与する。"""
        if not outline:
            return outline
        stage_order = [str(s) for s in blueprint.get("stages", []) if s]
        if not stage_order:
            return outline

        buckets: Dict[str, List[Dict[str, Any]]] = {s: [] for s in stage_order}
        buckets["core"] = []
        for section in outline:
            item = dict(section) if isinstance(section, dict) else {"heading": str(section or "")}
            stage = self._classify_outline_stage(item)
            if stage in buckets:
                buckets[stage].append(item)
            elif stage in {"intro", "mechanism", "case", "countermeasure", "closing"} and stage not in buckets:
                buckets["core"].append(item)
            else:
                buckets["core"].append(item)

        ordered: List[Dict[str, Any]] = []
        for stage in stage_order:
            if buckets.get(stage):
                ordered.append(self._retag_section_for_stage(buckets[stage].pop(0), stage))
            elif stage in {"mechanism", "case", "countermeasure"} and buckets["core"]:
                ordered.append(self._retag_section_for_stage(buckets["core"].pop(0), stage))

        remaining: List[Dict[str, Any]] = []
        for stage in ("intro", "mechanism", "case", "countermeasure", "closing"):
            remaining.extend(buckets.get(stage, []))
        remaining.extend(buckets.get("core", []))

        if "closing" in stage_order:
            closings = [sec for sec in ordered + remaining if self._classify_outline_stage(sec) == "closing"]
            non_closings = [sec for sec in ordered + remaining if self._classify_outline_stage(sec) != "closing"]
            if closings:
                ordered = non_closings + closings
            else:
                ordered = non_closings
        else:
            ordered.extend(remaining)

        return self._attach_outline_transition_hints(ordered)

    def _build_fallback_outline_from_stage_blueprint(self, article_type: str, user_prompt: str) -> List[Dict[str, Any]]:
        """LLMアウトラインが壊れたとき、段階台本ベースで最低限の構成を返す。"""
        blueprint = self._build_outline_stage_blueprint(article_type, user_prompt)
        stages = [str(s) for s in blueprint.get("stages", []) if s]
        if not stages:
            return []

        _empty = {"required_elements": [], "key_message": "", "source_focus": "", "do_not_cover": ""}
        templates = {
            "intro": {"heading": "背景と問題設定", "purpose": "読者の疑問と前提をそろえる"},
            "mechanism": {"heading": "仕組みの整理", "purpose": "何が起きるかを構造で説明する"},
            "case": {"heading": "具体的な事例", "purpose": "具体例で論点を理解しやすくする"},
            "countermeasure": {"heading": "実務での対策", "purpose": "現場で試せる対策を示す"},
            "closing": {"heading": "最後に", "purpose": "再説明を避け、判断軸と次に取る行動を示す"},
        }
        outline: List[Dict[str, Any]] = []
        for stage in stages:
            base = templates.get(stage)
            if not base:
                continue
            outline.append({**base, **_empty})
        return self._attach_outline_transition_hints(outline)

    def _get_outline_flow_options(self, article_type: str, user_prompt: str = "") -> str:
        """記事タイプ別に、固定ではない「流れ候補」を返す。"""
        blueprint = self._build_outline_stage_blueprint(article_type, user_prompt)
        stages = [self._stage_label(stage) for stage in blueprint.get("stages", [])]
        if stages:
            primary = " -> ".join(stages)
            if blueprint.get("diary_like"):
                secondary = "導入 -> 出来事の描写 -> 気づき -> 結び"
            elif blueprint.get("include_countermeasure"):
                secondary = "導入 -> 仕組み -> 具体事例 -> 対策 -> 結論"
            else:
                secondary = "導入 -> 仕組み/事例 -> 振り返り"
            return "\n".join(
                [
                    f"- 候補A: {primary}",
                    f"- 候補B: {secondary}",
                ]
            )

        focus = self._get_effective_writing_focus()
        if article_type == "announcement":
            return "\n".join(
                [
                    "- 候補A: 変更点の要約 -> 対象者/影響 -> 対応手順 -> 問い合わせ先",
                    "- 候補B: 背景 -> 何が変わるか -> いつから/誰に影響 -> 次にやること",
                ]
            )
        if focus == "analysis":
            return "\n".join(
                [
                    "- 候補A: 背景整理 -> 根拠比較 -> 示唆 -> 実務アクション",
                    "- 候補B: 課題提起 -> 事実整理 -> 論点分解 -> 最終結論",
                ]
            )
        if focus == "experience":
            return "\n".join(
                [
                    "- 候補A: 問題意識 -> 体験/事例 -> 学び -> 補足",
                    "- 候補B: 失敗/違和感 -> 気づき -> 改善プロセス -> 最後に",
                ]
            )
        return "\n".join(
            [
                "- 候補A: 課題提起 -> 説明 -> 具体策 -> 最後に",
                "- 候補B: 背景説明 -> 詳細解説 -> 具体策 -> 最後に",
            ]
        )

    def _decide_structure_features(
        self,
        *,
        user_prompt: str,
        article_type: str,
        section_count: int,
    ) -> Dict[str, Any]:
        text = (user_prompt or "").strip()
        focus = self._get_effective_writing_focus()

        toc_keywords = ("目次", "全体像", "一覧", "索引")
        bullet_keywords = ("手順", "チェック", "比較", "ポイント", "箇条書き", "要点", "ステップ")

        use_toc = bool(
            self._length_mode == "long"
            or section_count >= 6
            or any(keyword in text for keyword in toc_keywords)
        )
        use_bullets = bool(
            focus in ("analysis", "explanation")
            and (
                any(keyword in text for keyword in bullet_keywords)
                or article_type in ("announcement", "case_study")
            )
        )

        intro_mode = "full"
        if self._length_mode == "short" or article_type == "announcement":
            intro_mode = "minimal"
        elif focus == "analysis" or use_toc:
            intro_mode = "short"

        return {
            "use_toc": use_toc,
            "use_bullets": use_bullets,
            "intro_mode": intro_mode,
        }

    def _get_dynamic_formatting_guide(self) -> str:
        features = self._structure_features or {}
        lines = []
        if features.get("use_toc"):
            lines.append("- 本文冒頭に目次を置いてもよい（必要な場合のみ）。")
        else:
            lines.append("- 目次は必須ではない。冗長なら省略する。")
        if features.get("use_bullets"):
            lines.append("- 手順・比較・チェック項目は箇条書きを活用してよい。")
        else:
            lines.append("- 箇条書きは必要な箇所に限定し、地の文を優先する。")

        intro_mode = features.get("intro_mode", "full")
        if intro_mode == "minimal":
            lines.append("- 導入は1〜2文で簡潔にし、すぐ本題へ入る。")
        elif intro_mode == "short":
            lines.append("- 導入は短め（2〜3文）で、本文への接続を優先する。")
        else:
            lines.append("- 導入で読者の疑問と価値を丁寧に接続する。")
        return "\n".join(lines)

    def _maybe_add_table_of_contents(
        self,
        body: str,
        outline_data: List[Dict[str, str]],
    ) -> str:
        if not body:
            return body
        features = self._structure_features or {}
        if not features.get("use_toc"):
            return body
        if "## 目次" in body:
            return body

        headings = []
        for section in outline_data:
            heading = (section or {}).get("heading", "").strip()
            if heading and self._is_valid_heading(heading):
                headings.append(f"- {heading}")
        if len(headings) < 3:
            return body

        toc = "## 目次\n" + "\n".join(headings[:7])
        return f"{toc}\n\n{body}".strip()

    def _apply_intro_mode(self, lead: str) -> str:
        if not lead:
            return lead
        intro_mode = (self._structure_features or {}).get("intro_mode", "full")
        if intro_mode == "full":
            return lead
        sentences = [s.strip() for s in re.split(r"(?<=[。！？])", lead) if s.strip()]
        if not sentences:
            return lead
        if intro_mode == "minimal":
            return " ".join(sentences[:1]).strip()
        return " ".join(sentences[:2]).strip()

    def _choose_opening_style(self, user_prompt: str, title: Optional[str] = None) -> str:
        focus = self._get_effective_writing_focus()
        options = _c("OPENING_STYLE_OPTIONS").get(focus, _c("OPENING_STYLE_OPTIONS")["auto"])
        if not options:
            return "benefit_first"
        seed_text = (
            f"{focus}|{getattr(self, '_current_type', '')}|{title or ''}|"
            f"{user_prompt[:120]}|{getattr(self, '_opening_variation_nonce', 0)}"
        )
        seed = sum(ord(ch) for ch in seed_text)
        rng = random.Random(seed)
        weights: List[int] = []
        for style in options:
            weight = 3
            if focus == "analysis" and style == "question_first":
                weight = 1
            elif focus == "experience" and style in ("scene_first", "micro_story_first"):
                weight = 4
            elif focus == "explanation" and style == "myth_bust_first":
                weight = 2
            weights.append(weight)
        return rng.choices(options, weights=weights, k=1)[0]

    def _get_opening_style_guide(self) -> str:
        style_key = getattr(self, "_lead_opening_style", "")
        if style_key in _c("OPENING_STYLE_GUIDES"):
            return _c("OPENING_STYLE_GUIDES")[style_key]
        return _c("OPENING_STYLE_GUIDES")["benefit_first"]

    def _get_section_opening_hint(self, section_index: int) -> str:
        sequence = getattr(self, "_section_opening_sequence", []) or []
        if 0 <= section_index < len(sequence):
            return sequence[section_index]
        focus = self._get_effective_writing_focus()
        hints = _c("SECTION_OPENING_HINTS").get(focus, _c("SECTION_OPENING_HINTS")["auto"])
        if not hints:
            return "論点提示から入る"
        return hints[section_index % len(hints)]

