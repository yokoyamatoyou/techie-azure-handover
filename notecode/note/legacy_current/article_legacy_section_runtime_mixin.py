"""Legacy section runtime helpers for ArticleGenerator."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from note.article_cognitive_drift_mixin import (
    PARAGRAPH_COMPLEXITY_HINTS,
    PARAGRAPH_DENSITY_HINTS,
    PHASE_PARAGRAPH_TONE_HINTS,
)
from note.legacy_current.article_runtime_symbols import (
    CLOSING_HEADING_PATTERN,
    VERIFICATION_MAX_REWRITE_RATIO,
)

logger = logging.getLogger(__name__)


class ArticleLegacySectionRuntimeMixin:
    """Mixin providing legacy prompt/paragraph runtime and verification helpers."""

    _SECTION_CONTEXT_FLOOR = 2200

    def _resolve_context_overlap_ratio(self, section_index: int, total_sections: int) -> float:
        cfg = self._get_section_generation_config()
        overlap_cfg = cfg.get("context_overlap", {}) if isinstance(cfg, dict) else {}
        if not isinstance(overlap_cfg, dict):
            overlap_cfg = {}

        base_ratio = float(overlap_cfg.get("base_ratio", 0.40) or 0.40)
        ratio = base_ratio
        enabled = bool(overlap_cfg.get("enabled", False))

        if enabled:
            if total_sections <= 1:
                ratio = base_ratio
            else:
                pos = section_index / max(1, total_sections - 1)
                if pos <= 0.25:
                    ratio = float(overlap_cfg.get("intro_ratio", base_ratio) or base_ratio)
                elif pos >= 0.80:
                    ratio = float(overlap_cfg.get("closing_ratio", base_ratio) or base_ratio)
                else:
                    ratio = float(overlap_cfg.get("middle_ratio", base_ratio) or base_ratio)

            reduce_on_redundancy = float(overlap_cfg.get("reduce_on_redundancy", 0.08) or 0.08)
            if reduce_on_redundancy > 0:
                telemetry = list(getattr(self, "_last_retry_telemetry", []) or [])
                had_overlap_signal = any(
                    bool(item.get("redundant")) or bool(item.get("low_novelty"))
                    for item in telemetry
                    if isinstance(item, dict)
                )
                if had_overlap_signal:
                    ratio -= reduce_on_redundancy

        min_ratio = float(overlap_cfg.get("min_ratio", 0.10) or 0.10)
        max_ratio = float(overlap_cfg.get("max_ratio", 0.55) or 0.55)
        if max_ratio < min_ratio:
            min_ratio, max_ratio = max_ratio, min_ratio
        return max(min_ratio, min(max_ratio, ratio))

    def _slice_context_for_section(
        self, merged_context: str, section_index: int, total_sections: int, source_focus: str = ""
    ) -> str:
        """セクションごとに異なるソース抜粋を返す。"""
        if not merged_context:
            return ""
        floor = self._SECTION_CONTEXT_FLOOR
        if source_focus:
            if isinstance(source_focus, list):
                source_focus = ", ".join(str(item) for item in source_focus)
            keywords = [kw.strip() for kw in source_focus.replace("、", ",").split(",") if kw.strip()]
            for kw in keywords:
                idx = merged_context.find(kw)
                if idx >= 0:
                    start = max(0, idx - 1500)
                    end = min(len(merged_context), idx + 1500)
                    sliced = merged_context[start:end]
                    if len(sliced) < floor:
                        return merged_context[:floor]
                    return sliced
        if total_sections <= 1:
            return merged_context[:floor]
        chunk_size = len(merged_context) // total_sections
        overlap_ratio = self._resolve_context_overlap_ratio(section_index, total_sections)
        overlap = int(chunk_size * overlap_ratio)
        start = max(0, section_index * chunk_size - overlap)
        end = min(len(merged_context), (section_index + 1) * chunk_size + overlap)
        sliced = merged_context[start:end]
        if len(sliced) < floor:
            return merged_context[:floor]
        return sliced

    @staticmethod
    def _summarize_prior_section_memory(prior_section_memory: str, *, max_chars: int = 320) -> str:
        """既出要点メモを短く要約し、段落プロンプトで使える形にする。"""
        raw = (prior_section_memory or "").strip()
        if not raw:
            return "なし"

        picks: List[str] = []
        for line in raw.splitlines():
            current = (line or "").strip()
            if not current:
                continue
            current = re.sub(r"^\s*[-*]\s*", "", current)
            if ":" in current:
                _, tail = current.split(":", 1)
                current = tail.strip()
            current = current.split(" / ")[0].strip().rstrip("。")
            if current:
                picks.append(current)
            if len(picks) >= 3:
                break

        summary = " / ".join(picks).strip()
        if not summary:
            summary = raw.replace("\n", " ").strip()
        if len(summary) > max_chars:
            summary = summary[:max_chars].rstrip(" 、。")
        return summary or "なし"

    def _build_section_brief(
        self,
        *,
        heading: str,
        purpose: str,
        required_elements: str,
        key_message: str,
        do_not_cover: str,
        stage_role_label: str,
        section_source: str,
        quote_instruction: str,
        prior_section_memory: str,
        transition_from_prev: str,
        title: Optional[str],
        target_audience: str,
        force_non_overlap: bool = False,
    ) -> str:
        """Tier A: セクション共通の文脈ブロック。"""
        exclusivity_block = ""
        if key_message:
            exclusivity_block += f"\n【固有結論】{key_message}"
        if do_not_cover:
            exclusivity_block += f"\n【触れない話題】{do_not_cover}"
        prior_summary = self._summarize_prior_section_memory(prior_section_memory)
        new_scope = (key_message or required_elements or purpose or "見出し固有の論点").strip()
        if len(new_scope) > 220:
            new_scope = new_scope[:220].rstrip(" 、。")
        non_overlap_rule = "既出論点の焼き直しは禁止。既出を参照する場合は1文以内で、新規論点へ進む。"
        if force_non_overlap:
            non_overlap_rule = "既出論点の言い換えは禁止。既出にない具体論点を最低2つ示す。"
        stage_line = f" / 役割: {stage_role_label}" if stage_role_label else ""
        return f"""\
【執筆者】{self._current_persona}
【タイトル】{title or "指定なし"}
【読者】{target_audience}
【見出し】## {heading}（{purpose}{stage_line}）
【要素】{required_elements}{exclusivity_block}
【参考】{section_source[:600] if section_source else "なし"}{quote_instruction}
【前セクション既出論点】{prior_summary}
【このセクション新規論点】{new_scope}
【非重複ルール】{non_overlap_rule}
【既出要点（詳細）】{prior_section_memory[:640] if prior_section_memory else "なし"}
{("【接続】" + transition_from_prev) if transition_from_prev else ""}""".strip()

    @staticmethod
    def _trim_prompt_anchor_for_question(text: str, *, max_chars: int = 72) -> str:
        cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
        if not cleaned:
            return ""
        cleaned = cleaned.strip("「」『』\"' ")
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[:max_chars].rstrip(" 、。,.")

    def _build_reader_question_guideline(self) -> str:
        interview_msg = str(self._interview_answers.get("message", "") or "").strip()
        prompt_anchor = str(getattr(self, "_latest_user_prompt", "") or "").strip()
        anchor = self._trim_prompt_anchor_for_question(interview_msg or prompt_anchor, max_chars=64)
        if not anchor:
            return "- 読者への問いかけは記事全体で1回まで。論点の確認に使い、連発しない。"
        return (
            f"- 読者への問いかけは記事全体で1〜2回まで。"
            f"「{anchor}」に直結する短い問いにする"
        )

    def _build_style_invariants(self) -> str:
        """Tier B: 不変の文体ルール。"""
        banned = ", ".join(self._get_active_banned_phrases())
        reader_question_line = self._build_reader_question_guideline()
        no_experience_line = (
            "\n- 「わたし自身」「わたしの経験では」等の一人称体験談は使わない"
            if not self._allow_experience
            else ""
        )
        return f"""\
- 一人称は「{self._current_pronoun}」で統一（絶対に変更しない）
- 読者に語りかける語り口（丁寧体基調、同じ語尾を連続させない）
- 文頭の型を連続させない（接続詞の連発禁止、無接続も混ぜる）
- 文末を単調化しない（同一終止を3回以上連続させない）
- 主語省略がデフォルト。話題の主語が変わるときのみ明示する
- 段落内で一人称を連発しない（2回目以降は主語省略優先）
- 見出し直下の1文目は、見出し語を1語以上含めて論点を明示
- 「Xは/Xが」で始まる文頭を連続させすぎない（2文連続まで）
- 指示語は参照先が曖昧なら具体名詞に
- 太字は0〜1箇所（語頭から語末まで、必ず同一行で閉じる）
- ダッシュ（――、—）禁止。フリガナ括弧禁止
- 受動態は1段落1回まで。能動態を優先する
- 構文テンプレの反復禁止（「単なる〜にとどまらず」等は記事全体で1回まで）
- 各段落に最低1つ具体物を入れる（抽象語だけで終わる段落は禁止）
- 記事テーマの中核語はそのまま一貫して使う（同義語に散らさない）
- {reader_question_line}
- 禁止語: {banned}{no_experience_line}""".strip()

    def _distribute_elements_to_paragraphs(
        self,
        required_elements: List[str],
        paragraph_plan: List[Dict[str, Any]],
    ) -> List[List[str]]:
        """必須要素を段落のroleに基づいて配分する。"""
        n = len(paragraph_plan)
        if n == 0:
            return []
        distributed: List[List[str]] = [[] for _ in range(n)]
        if not required_elements:
            return distributed

        intro_indices = [i for i, p in enumerate(paragraph_plan) if p.get("role") == "導入"]
        peak_indices = [i for i, p in enumerate(paragraph_plan) if p.get("role") == "山場"]
        closing_indices = [i for i, p in enumerate(paragraph_plan) if p.get("role") == "収束"]
        middle_indices = [i for i, p in enumerate(paragraph_plan) if p.get("role") in ("展開", "山場")]

        for ei, elem in enumerate(required_elements):
            elem_lower = elem.lower()
            if any(k in elem_lower for k in ("概要", "背景", "前提", "定義")) and intro_indices:
                distributed[intro_indices[0]].append(elem)
            elif any(k in elem_lower for k in ("行動", "次の一歩", "判断", "まとめ")) and closing_indices:
                distributed[closing_indices[0]].append(elem)
            elif middle_indices:
                target_idx = middle_indices[ei % len(middle_indices)]
                distributed[target_idx].append(elem)
            elif peak_indices:
                target_idx = peak_indices[ei % len(peak_indices)]
                distributed[target_idx].append(elem)
            else:
                distributed[ei % n].append(elem)

        return distributed

    def _generate_paragraph(
        self,
        *,
        section_brief: str,
        style_invariants: str,
        paragraph_spec: Dict[str, Any],
        paragraph_elements: List[str],
        previous_last_sentence: str,
        paragraph_char_target: int,
        is_first: bool,
        is_last: bool,
        is_closing_section: bool,
        section_opening_hint: str,
    ) -> str:
        """段落単位でLLMを呼び出し、1段落に1トピック制約を課す。"""
        index = int(paragraph_spec.get("index", 1))
        total = int(paragraph_spec.get("_total", index))
        role = paragraph_spec.get("role", "展開")
        phase_key = str(paragraph_spec.get("phase", "building"))
        complexity_key = str(paragraph_spec.get("sentence_complexity", "moderate"))
        density_key = str(paragraph_spec.get("information_density", "medium"))

        complexity_hint = PARAGRAPH_COMPLEXITY_HINTS.get(complexity_key, PARAGRAPH_COMPLEXITY_HINTS["moderate"])
        density_hint = PARAGRAPH_DENSITY_HINTS.get(density_key, PARAGRAPH_DENSITY_HINTS["medium"])
        tone_hint = PHASE_PARAGRAPH_TONE_HINTS.get(phase_key, PHASE_PARAGRAPH_TONE_HINTS["building"])

        elements_line = "、".join(paragraph_elements) if paragraph_elements else "前後の流れに合わせて自然に展開"

        opening_line = ""
        if is_first and section_opening_hint:
            opening_line = f"セクション冒頭は「{section_opening_hint}」を参考にする（固定しない）。"
        closing_line = ""
        if is_last and is_closing_section:
            closing_line = "締め段落: 定義や背景の繰り返しを避け、判断軸・次の一手を示す。"
        elif is_last:
            closing_line = "末段落: 「要点は/まとめると」型の要約文を置かない。"

        prev_line = (
            f"直前段落の末文: 「{previous_last_sentence}」\n→ここから自然につなげる。"
            if previous_last_sentence
            else ""
        )

        prompt = f"""\
{section_brief}

{style_invariants}

【この段落の仕事】
段落{index}/{total}: {role}（{tone_hint}）
トピック: {elements_line}
文の複雑さ: {complexity_hint} / 情報密度: {density_key}（{density_hint}）
{prev_line}
{opening_line}
{closing_line}
段落内で話題の主語が変わるときは必ず主語を明示する。
前セクションと同じ結論・同じ具体例の言い換えは禁止。既出を踏まえる場合は1文以内で新規論点へ接続する。
抽象語（重要/必要/効果的/適切/有効/可能）を使ったら、直後に具体例・数字で裏付ける。
長さ: {paragraph_char_target}文字前後。本文のみ出力。
""".strip()

        max_tokens = min(800, max(150, int(paragraph_char_target * 1.2)))
        temp_override = paragraph_spec.get("temperature")

        return self.llm.generate_text(
            prompt,
            max_tokens=max_tokens,
            task_type="section",
            temperature_override=temp_override,
        )

    def _generate_section(
        self,
        section_meta: Dict[str, Any],
        merged: str,
        user_prompt: str,
        article_type: str,
        quote_candidates: List[str],
        target_audience: str,
        target_chars: Optional[int] = None,
        title: Optional[str] = None,
        section_index: int = 0,
        total_sections: int = 1,
        prior_section_memory: str = "",
        force_non_overlap: bool = False,
        cognitive_profile: Optional[Dict[str, Any]] = None,
        section_feedback: Optional[Dict[str, Any]] = None,
    ) -> str:
        paragraph_plan = (cognitive_profile or {}).get("paragraph_plan", [])
        if not isinstance(paragraph_plan, list):
            paragraph_plan = []
        if len(paragraph_plan) < 2:
            paragraph_plan = [
                {
                    "index": 1,
                    "role": "導入",
                    "phase": "building",
                    "sentence_complexity": "moderate",
                    "information_density": "medium",
                    "temperature": (cognitive_profile or {}).get("temperature"),
                },
                {
                    "index": 2,
                    "role": "展開",
                    "phase": "peak",
                    "sentence_complexity": "moderate",
                    "information_density": "medium",
                    "temperature": (cognitive_profile or {}).get("temperature"),
                },
                {
                    "index": 3,
                    "role": "収束",
                    "phase": "settling",
                    "sentence_complexity": "simple",
                    "information_density": "medium",
                    "temperature": (cognitive_profile or {}).get("temperature"),
                },
            ]
        return self._generate_section_paragraph_mode(
            section_meta=section_meta,
            merged=merged,
            user_prompt=user_prompt,
            article_type=article_type,
            quote_candidates=quote_candidates,
            target_audience=target_audience,
            target_chars=target_chars,
            title=title,
            section_index=section_index,
            total_sections=total_sections,
            prior_section_memory=prior_section_memory,
            force_non_overlap=force_non_overlap,
            cognitive_profile=cognitive_profile,
            section_feedback=section_feedback,
            paragraph_plan=paragraph_plan,
        )

    def _generate_section_paragraph_mode(
        self,
        *,
        section_meta: Dict[str, Any],
        merged: str,
        user_prompt: str,
        article_type: str,
        quote_candidates: List[str],
        target_audience: str,
        target_chars: Optional[int],
        title: Optional[str],
        section_index: int,
        total_sections: int,
        prior_section_memory: str,
        force_non_overlap: bool,
        cognitive_profile: Optional[Dict[str, Any]],
        section_feedback: Optional[Dict[str, Any]],
        paragraph_plan: List[Dict[str, Any]],
    ) -> str:
        _ = (user_prompt, article_type, cognitive_profile, section_feedback)
        heading = section_meta.get("heading", f"セクション{section_index + 1}")
        purpose = section_meta.get("purpose", "本文執筆")
        required_elements_list = section_meta.get("required_elements", [])
        required_elements = ", ".join(required_elements_list)
        key_message = section_meta.get("key_message", "")
        do_not_cover = section_meta.get("do_not_cover", "")
        source_focus = section_meta.get("source_focus", "")
        transition_from_prev = section_meta.get("transition_from_prev", "")
        stage_role = section_meta.get("stage_role", "")
        for attr_name in ("key_message", "do_not_cover", "transition_from_prev", "stage_role"):
            val = locals()[attr_name]
            if isinstance(val, list):
                locals()[attr_name] = "、".join(str(item) for item in val)
        key_message = str(key_message if not isinstance(key_message, list) else "、".join(str(i) for i in key_message))
        do_not_cover = str(do_not_cover if not isinstance(do_not_cover, list) else "、".join(str(i) for i in do_not_cover))
        transition_from_prev = str(
            transition_from_prev if not isinstance(transition_from_prev, list) else "、".join(str(i) for i in transition_from_prev)
        ).strip()
        stage_role = str(stage_role if not isinstance(stage_role, list) else "、".join(str(i) for i in stage_role)).strip()

        stage_role_label_map = {
            "intro": "導入",
            "mechanism": "仕組み",
            "case": "事例",
            "countermeasure": "対策",
            "closing": "結論",
        }
        stage_role_label = stage_role_label_map.get(stage_role, "")
        section_opening_hint = self._get_section_opening_hint(section_index)
        section_source = self._slice_context_for_section(merged, section_index, total_sections, source_focus)

        quotes = "\n".join(f"- {q}" for q in quote_candidates[:3]) or ""
        quote_instruction = f"\n参考（エピソード/事実の種）:\n{quotes}" if quotes else ""

        is_closing_section = bool(
            stage_role == "closing"
            or CLOSING_HEADING_PATTERN.search(heading)
            or re.search(r"(要点|結論|締め|行動|判断軸|次の一歩)", purpose)
        )

        section_brief = self._build_section_brief(
            heading=heading,
            purpose=purpose,
            required_elements=required_elements,
            key_message=key_message,
            do_not_cover=do_not_cover,
            stage_role_label=stage_role_label,
            section_source=section_source,
            quote_instruction=quote_instruction,
            prior_section_memory=prior_section_memory,
            transition_from_prev=transition_from_prev,
            title=title,
            target_audience=target_audience,
            force_non_overlap=force_non_overlap,
        )
        style_invariants = self._build_style_invariants()

        for p_spec in paragraph_plan:
            p_spec["_total"] = len(paragraph_plan)
        distributed = self._distribute_elements_to_paragraphs(required_elements_list, paragraph_plan)

        per_para_chars = max(80, (target_chars or 600) // max(1, len(paragraph_plan)))

        paragraphs: List[str] = []
        prev_last = transition_from_prev or ""
        for i, p_spec in enumerate(paragraph_plan):
            para = self._generate_paragraph(
                section_brief=section_brief,
                style_invariants=style_invariants,
                paragraph_spec=p_spec,
                paragraph_elements=distributed[i],
                previous_last_sentence=prev_last,
                paragraph_char_target=per_para_chars,
                is_first=(i == 0),
                is_last=(i == len(paragraph_plan) - 1),
                is_closing_section=is_closing_section,
                section_opening_hint=section_opening_hint,
            )
            paragraphs.append(para.strip())
            sentences = [s for s in re.split(r"(?<=[。！？])", para) if s.strip()]
            prev_last = sentences[-1].strip() if sentences else ""

        section_body = "\n\n".join(paragraphs)
        section = f"## {heading}\n\n{section_body}"

        if self._should_verify_section_content(section, section_source):
            section = self._verify_section_content(section, section_source, heading)
        return section

    def _should_verify_section_content(self, section: str, source: str) -> bool:
        """重い検証LLMを必要時だけ実行する。"""
        if not section or not source or not source.strip():
            return False

        policy = getattr(self, "_pipeline_policy", {}) or {}
        evidence_mode = str(policy.get("evidence_mode", "normal")).lower()
        if evidence_mode == "strict":
            return True

        numeric_claims = len(
            re.findall(r"\d+(?:[.,]\d+)?(?:%|％|倍|件|年|月|日|人|社|回|円|万|億)", section)
        )
        if numeric_claims >= 3:
            return True

        legal_risk_patterns = [
            r"(No\.?1|ナンバーワン|世界一|日本一|唯一無二|最強|最高)",
            r"(絶対|必ず|確実に)",
            r"(治る|治療効果|痩せる|美白効果)",
            r"(他社|競合).{0,10}より.{0,12}(優れ|高性能|高機能)",
        ]
        if any(re.search(pattern, section, re.IGNORECASE) for pattern in legal_risk_patterns):
            return True

        return False

    def _verify_section_content(self, content: str, source: str, heading: str) -> str:
        """生成されたコンテンツがソースに基づいているか検証し、修正する。"""
        article_type = str(getattr(self, "_current_type", "") or "")
        editor_persona_block = self._build_editor_persona_block(
            pass_type="verification",
            article_type=article_type,
        )
        prompt = f"""
以下の記事セクションを「ファクトチェック」してください。
特に【数字】（金額、年号、％など）と【固有名詞】が、参考情報に基づいているか厳密に確認すること。
文法（主語述語の不一致、助詞抜け、係り受けの不自然さ）がある場合のみ最小限で修正すること。
{editor_persona_block}

参考情報:
{source[:5000]}

検証対象のセクション（見出し: {heading}）:
{content}

【修正ルール】
1. 参考情報に記載のない「具体的な数字」や「固有名詞」が含まれていれば削除、または「多くの」「一部の」等の抽象表現に修正する。
2. 数字がまたく含まれていない、または明らかに正しい場合は、元の文章をそのまま出力する。
3. 日本語として自然な流れを維持する。
4. 内容を大きく変えたり、要約したりしない。あくまで事後検証。
5. 感情表現・語り口は維持し、過度に硬い文体にしない。

出力は修正後の本文のみ。
        """.strip()
        try:
            verified = self.llm.generate_text(prompt, max_tokens=900, task_type="verification").strip()
        except Exception as exc:
            logger.debug("Verification pass failed. Keep original section.", exc_info=exc)
            return content

        if not verified:
            return content

        before_heading = re.search(r"^##\s+(.+)$", content, re.MULTILINE)
        after_heading = re.search(r"^##\s+(.+)$", verified, re.MULTILINE)
        if before_heading and after_heading:
            if before_heading.group(1).strip() != after_heading.group(1).strip():
                logger.info(
                    "verification rejected: heading mismatch %s -> %s",
                    before_heading.group(1),
                    after_heading.group(1),
                )
                return content

        rejection = self._rewrite_guard_check(
            "",
            content,
            "",
            verified,
            max_rewrite_ratio=VERIFICATION_MAX_REWRITE_RATIO,
            label="verification",
        )
        if rejection:
            logger.info("%s", rejection)
            return content

        return verified
