"""Legacy compatibility helpers for ArticleGenerator."""
from __future__ import annotations

import json
import logging
import random
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from note.article_fetcher import FetchedContent
from note.legacy_current.article_final_consistency_mixin import ArticleFinalConsistencyMixin
from note.legacy_current.article_runtime_symbols import (
    ARTICLE_TYPE_LABELS,
    EDITOR_CONSISTENCY_CONTEXT_LIMIT,
    EDITOR_CONSISTENCY_MAX_RETRIES,
    NON_CASUAL_COLLOQUIAL_ENDING_MAX,
    READABILITY_POLISH_CONTEXT_LIMIT,
    READABILITY_POLISH_MAX_REWRITE_RATIO,
    SECTION_OPENING_HINTS,
)

logger = logging.getLogger(__name__)


class ArticleLegacyCompatibilityMixin:
    """Legacy compatibility aliases, dormant shells, and post-polish helpers."""

    def _generate_single_section_task(
        self,
        section_index: int,
        section_meta: Dict[str, Any],
        section_target: int,
        *,
        merged_context: str,
        user_prompt: str,
        article_type: str,
        distributed_quotes: List[List[str]],
        target_audience: str,
        title: Optional[str],
        total_sections: int,
        existing_sections: List[str],
        cognitive_drift_enabled: bool,
        cognitive_drift_config: Dict[str, Any],
    ) -> str:
        """Single legacy section-generation task shell."""
        section_feedback = self._build_section_generation_feedback(existing_sections)
        cognitive_profile = (
            self._get_cognitive_profile(
                section_index,
                total_sections,
                target_chars=section_target,
                drift_config=cognitive_drift_config,
            )
            if cognitive_drift_enabled
            else None
        )
        return self._generate_section_with_retry(
            section_meta=section_meta,
            merged=merged_context,
            user_prompt=user_prompt,
            article_type=article_type,
            quote_candidates=(
                distributed_quotes[section_index] if section_index < len(distributed_quotes) else []
            ),
            target_audience=target_audience,
            target_chars=section_target,
            title=title,
            section_index=section_index,
            total_sections=total_sections,
            existing_sections=existing_sections,
            cognitive_profile=cognitive_profile,
            section_feedback=section_feedback,
        )

    def _build_even_summary_memory(self, sections_by_index: Dict[int, str]) -> str:
        """Build summary memory from even-indexed sections."""
        parts = []
        for idx in sorted(sections_by_index.keys()):
            sec = sections_by_index[idx]
            heading_match = re.search(r"^##\s+(.+)", sec, re.MULTILINE)
            heading = heading_match.group(1) if heading_match else f"Section {idx}"
            body_lines = [l for l in sec.split("\n") if l.strip() and not l.strip().startswith("##")]
            snippet = "。".join(body_lines[:2])[:120] if body_lines else ""
            parts.append(f"[{idx}] {heading}: {snippet}")
        return "\n".join(parts)

    def _generate_sections_parallel(
        self,
        section_inputs: List[tuple],
        *,
        merged_context: str,
        user_prompt: str,
        article_type: str,
        distributed_quotes: List[List[str]],
        target_audience: str,
        title: Optional[str],
        total_sections: int,
        cognitive_drift_enabled: bool,
        cognitive_drift_config: Dict[str, Any],
    ) -> List[str]:
        """Generate even sections sequentially, then odd sections in parallel."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        even_indices = [i for i in range(len(section_inputs)) if i % 2 == 0]
        odd_indices = [i for i in range(len(section_inputs)) if i % 2 == 1]

        sections_map: Dict[int, str] = {}
        even_history: List[str] = []
        for idx in even_indices:
            section_meta, section_target = section_inputs[idx]
            self._set_generation_progress(
                stage="body",
                message=f"本文を生成中... ({len(sections_map)}/{max(1, total_sections)})",
                current=len(sections_map),
                total=max(1, total_sections),
                partial_body=self._combine_sections(
                    [sections_map.get(i, "") for i in range(max(sections_map.keys()) + 1)]
                    if sections_map
                    else []
                ),
            )
            sec = self._generate_single_section_task(
                idx,
                section_meta,
                section_target,
                merged_context=merged_context,
                user_prompt=user_prompt,
                article_type=article_type,
                distributed_quotes=distributed_quotes,
                target_audience=target_audience,
                title=title,
                total_sections=total_sections,
                existing_sections=even_history,
                cognitive_drift_enabled=cognitive_drift_enabled,
                cognitive_drift_config=cognitive_drift_config,
            )
            sections_map[idx] = sec
            even_history.append(sec)

        _ = self._build_even_summary_memory(sections_map)
        all_even_sections = [sections_map[i] for i in sorted(sections_map.keys())]

        if odd_indices:

            def _gen_odd(idx: int) -> tuple:
                section_meta, section_target = section_inputs[idx]
                neighbor_sections = list(all_even_sections)
                sec = self._generate_single_section_task(
                    idx,
                    section_meta,
                    section_target,
                    merged_context=merged_context,
                    user_prompt=user_prompt,
                    article_type=article_type,
                    distributed_quotes=distributed_quotes,
                    target_audience=target_audience,
                    title=title,
                    total_sections=total_sections,
                    existing_sections=neighbor_sections,
                    cognitive_drift_enabled=cognitive_drift_enabled,
                    cognitive_drift_config=cognitive_drift_config,
                )
                return (idx, sec)

            with ThreadPoolExecutor(max_workers=min(3, len(odd_indices))) as pool:
                futures = {pool.submit(_gen_odd, idx): idx for idx in odd_indices}
                for future in as_completed(futures):
                    idx, sec = future.result()
                    sections_map[idx] = sec
                    self._set_generation_progress(
                        stage="body",
                        message=f"本文を生成中... ({len(sections_map)}/{max(1, total_sections)})",
                        current=len(sections_map),
                        total=max(1, total_sections),
                    )

        return [sections_map[i] for i in range(len(section_inputs))]

    def _generate_section_with_retry(
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
        existing_sections: Optional[List[str]] = None,
        cognitive_profile: Optional[Dict[str, Any]] = None,
        section_feedback: Optional[Dict[str, Any]] = None,
    ) -> str:
        history = existing_sections or []
        fallback = ""
        forbidden_terms: List[str] = []
        retry_telemetry: List[Dict[str, Any]] = []
        section_cfg = self._get_section_generation_config()
        novelty_cfg = section_cfg.get("novelty_gate", {}) if isinstance(section_cfg, dict) else {}
        if not isinstance(novelty_cfg, dict):
            novelty_cfg = {}
        max_attempts = int(novelty_cfg.get("max_retries", 3) or 3)
        max_attempts = max(1, min(3, max_attempts))
        max_forbidden_terms = int(novelty_cfg.get("max_forbidden_terms", 10) or 10)
        max_forbidden_terms = max(1, min(24, max_forbidden_terms))
        focus = str((getattr(self, "_pipeline_policy", {}) or {}).get("focus") or self._get_effective_writing_focus())
        stage_role = str((section_meta or {}).get("stage_role", "") or "").strip().lower()
        is_closing_stage = stage_role == "closing"

        for attempt in range(max_attempts):
            overlap_memory = self._build_section_overlap_memory(history)
            if forbidden_terms:
                forbidden_block = "【使用禁止語（既出セクションと被る語）】: " + "、".join(
                    forbidden_terms[:max_forbidden_terms]
                )
                overlap_memory = f"{overlap_memory}\n{forbidden_block}" if overlap_memory else forbidden_block

            section = self._generate_section(
                section_meta,
                merged,
                user_prompt,
                article_type,
                quote_candidates,
                target_audience,
                target_chars=target_chars,
                title=title,
                section_index=section_index,
                total_sections=total_sections,
                prior_section_memory=overlap_memory,
                force_non_overlap=(attempt > 0 or (is_closing_stage and bool(history))),
                cognitive_profile=cognitive_profile,
                section_feedback=section_feedback,
            )
            fallback = section

            is_redundant, overlap_terms = self._check_redundancy_with_reason(section, history)
            novelty_report = self._compute_section_novelty_report(
                section,
                history,
                redundancy_result=(is_redundant, overlap_terms),
            )
            novelty_threshold = self._get_novelty_threshold(section_index, total_sections, focus)
            low_novelty = self._should_retry_due_to_low_novelty(
                novelty_report,
                section_index=section_index,
                total_sections=total_sections,
                focus=focus,
                has_history=bool(history),
            )
            if is_closing_stage and history:
                closing_floor = max(novelty_threshold, 0.44)
                if float(novelty_report.get("novelty_ratio", 1.0) or 1.0) < closing_floor:
                    low_novelty = True
            retry_telemetry.append(
                {
                    "attempt": attempt,
                    "redundant": is_redundant,
                    "overlap_terms_count": len(overlap_terms),
                    "low_novelty": bool(low_novelty),
                    "novelty_ratio": float(novelty_report.get("novelty_ratio", 1.0) or 1.0),
                    "novelty_threshold": float(novelty_threshold),
                    "overlap_term_ratio": float(novelty_report.get("overlap_term_ratio", 0.0) or 0.0),
                }
            )

            if not is_redundant and not low_novelty:
                if retry_telemetry:
                    self._last_retry_telemetry = retry_telemetry
                return section

            next_overlap_terms: List[str] = list(overlap_terms)
            if low_novelty:
                next_overlap_terms.extend(list(novelty_report.get("overlap_terms", [])))

            for term in self._dedupe_terms(next_overlap_terms, max_items=max_forbidden_terms * 2):
                if term not in forbidden_terms:
                    forbidden_terms.append(term)
                if len(forbidden_terms) >= max_forbidden_terms:
                    break

        logger.info(
            "Section overlap/novelty remained after retries: heading=%s index=%s forbidden=%s",
            (section_meta or {}).get("heading", ""),
            section_index,
            forbidden_terms[:5],
        )
        self._last_retry_telemetry = retry_telemetry
        return fallback

    def _distribute_quotes(self, quote_candidates: List[str], total_sections: int) -> List[List[str]]:
        """Distribute quote candidates round-robin for legacy section generation."""
        if not quote_candidates or total_sections <= 0:
            return [[] for _ in range(max(1, total_sections))]
        buckets: List[List[str]] = [[] for _ in range(total_sections)]
        for index, quote in enumerate(quote_candidates):
            buckets[index % total_sections].append(quote)
        return buckets

    def _prepare_section_opening_sequence(self, section_count: int) -> None:
        if section_count <= 0:
            self._section_opening_sequence = []
            return
        focus = self._get_effective_writing_focus()
        opening_hints = SECTION_OPENING_HINTS
        hints = list(opening_hints.get(focus, opening_hints["auto"]))
        if not hints:
            self._section_opening_sequence = ["論点提示から入る"] * section_count
            return

        seed_text = (
            f"{focus}|{getattr(self, '_current_type', '')}|"
            f"{getattr(self, '_opening_variation_nonce', 0)}|{section_count}"
        )
        seed = sum(ord(ch) for ch in seed_text)
        rng = random.Random(seed)
        rng.shuffle(hints)

        sequence: List[str] = []
        while len(sequence) < section_count:
            cycle = list(hints)
            rng.shuffle(cycle)
            if sequence and cycle and sequence[-1] == cycle[0] and len(cycle) > 1:
                cycle = cycle[1:] + cycle[:1]
            sequence.extend(cycle)
        self._section_opening_sequence = sequence[:section_count]

    def _editor_consistency_signals(self, lead: str, body: str) -> Dict[str, bool]:
        combined = f"{lead}\n\n{body}" if (lead or body) else ""
        if not combined:
            return {
                "missing_intro": False,
                "missing_closing": False,
                "duplicate_openings": False,
                "pronoun_conflict": False,
                "style_mixed": False,
                "stance_anchor_missing": False,
            }

        headings = re.findall(r"^##\s+(.+)$", combined, re.MULTILINE)
        content_headings = [
            heading for heading in headings if not re.search(r"(参考資料|参考文献|出典)", heading, re.IGNORECASE)
        ]
        closing_pattern = (
            r"(まとめ|結論|おわり|最後に|要点|次の一歩|一歩|行動|これから|未来|"
            r"判断ポイント|実務ポイント|チェックリスト)"
        )
        intro_pattern = r"(はじめに|導入|背景|概要|問題提起|課題|出発点|きっかけ)"
        has_intro = (
            any(re.search(intro_pattern, heading, re.IGNORECASE) for heading in content_headings[:2])
            if content_headings
            else False
        )
        missing_intro = len(content_headings) >= 3 and not has_intro
        has_closing = (
            any(re.search(closing_pattern, heading, re.IGNORECASE) for heading in content_headings[-2:])
            if content_headings
            else False
        )
        missing_closing = len(content_headings) >= 3 and not has_closing

        duplicate_openings = False
        section_openings: List[str] = []
        for match in re.finditer(r"^##\s+.+\n+(.*?)(?=\n|$)", combined, re.MULTILINE):
            first_line = match.group(1).strip()
            if first_line:
                section_openings.append(re.sub(r"\s+", "", first_line)[:30])
        if len(section_openings) >= 3:
            for left_index in range(len(section_openings) - 1):
                for right_index in range(left_index + 1, len(section_openings)):
                    ratio = SequenceMatcher(
                        None,
                        section_openings[left_index],
                        section_openings[right_index],
                    ).ratio()
                    if ratio >= 0.75:
                        duplicate_openings = True
                        break
                if duplicate_openings:
                    break

        pronoun_conflict = self._has_pronoun_conflict(combined)
        register_report = self._analyze_style_register(combined)
        style_mixed = bool(register_report.get("mixed"))
        stance_anchor_missing = self._has_corporate_stance_anchor_gap(lead, body)
        return {
            "missing_intro": missing_intro,
            "missing_closing": missing_closing,
            "duplicate_openings": duplicate_openings,
            "pronoun_conflict": pronoun_conflict,
            "style_mixed": style_mixed,
            "stance_anchor_missing": stance_anchor_missing,
        }

    def _should_run_editor_consistency(self, lead: str, body: str) -> bool:
        """Run editor consistency only when structural issues are detected."""
        signals = self._editor_consistency_signals(lead, body)
        return any(signals.values())

    def _run_editor_consistency_pass(
        self,
        lead: str,
        body: str,
        *,
        merged_context: str,
        article_type: str,
        target_audience: str,
        review_points: Optional[List[str]] = None,
        readability_focus: bool = False,
    ) -> Tuple[str, str]:
        """Run a single editor-consistency pass for legacy compatibility flow."""
        if not lead and not body:
            return lead, body

        self._editor_consistency_failed = False
        writing_focus_guide = self._get_writing_focus_guide()
        editor_persona_block = self._build_editor_persona_block(
            pass_type="editor_consistency",
            article_type=article_type,
        )
        review_text = " / ".join((review_points or [])[:3]) if review_points else "なし"
        readability_extra = ""
        if readability_focus:
            readability_extra = """
8. review_points に段落過密/文体混在/導入句反復がある場合、最小限で可読性を補正する
9. 不必要な要約・圧縮を避け、情報量と具体性を維持する"""
        article_type_labels = ARTICLE_TYPE_LABELS
        context_limit = int(EDITOR_CONSISTENCY_CONTEXT_LIMIT)
        prompt = f"""
あなたは編集者です。以下の lead/body を最小限だけ調整してください。
{editor_persona_block}

【最優先】
- 人間らしい語り口・感情の揺らぎ・読みやすさは維持する
- 一人称は「{self._current_pronoun}」を維持する
- 文体を硬くしすぎない
- セクションごとの文体の違い（語彙の難易度、文の複雑さ、勢い）は意図的な設計なので均一化しない
- 人間の記事は冒頭と中盤と終盤でテンションが違うのが自然。その揺らぎを保つ

【チェック観点】
1. セクション間の矛盾（結論の食い違い、時系列矛盾、重複）を解消する
2. 文法の不自然さ（助詞、係り受け、主語述語）だけ最小限で直す
3. 参考情報にない数字/固有名詞の断定を弱める（必要なら抽象化）
4. タイトルとターゲット読者への整合を保つ
5. 導入の定型反復（「〜ありませんか？」「〜だと思っていたんですが」）を避ける
6. まったく同じ結論を繰り返している段落のみ統合する
7. 「補足」「FAQ」「注意点」など補助セクションは、導入直後ではなく中盤以降に配置する
{readability_extra}

【禁止】
- セクション間で語彙レベルや文の長さを統一しようとすること
- あるセクションの文体を別セクションに合わせて書き換えること

【記事タイプ】
{article_type_labels.get(article_type, article_type)}

【ターゲット読者】
{target_audience}

【本文の重心】
{writing_focus_guide or "自動判定"}

【要修正ポイント（該当時のみ）】
{review_text}

【参考情報（抜粋）】
{merged_context[:context_limit] if merged_context else "なし"}

【入力（そのまま保持したい本文）】
[LEAD]
{lead}

[BODY]
{body}

【出力形式】
JSONのみ:
{{"lead": "...", "body": "..."}}
        """.strip()

        max_tokens = min(5200, max(1300, int((len(lead) + len(body)) * 1.1)))
        guard_rejected = False
        last_failure_reason = ""
        max_retries = int(EDITOR_CONSISTENCY_MAX_RETRIES)
        for attempt in range(1, max_retries + 1):
            try:
                raw = self.llm.generate_text(
                    prompt,
                    max_tokens=max_tokens,
                    task_type="editor_consistency",
                ).strip()
            except Exception as exc:
                logger.debug(
                    "Editor consistency pass failed (attempt %s/%s).",
                    attempt,
                    max_retries,
                    exc_info=exc,
                )
                last_failure_reason = f"llm_error:{type(exc).__name__}:{exc}"
                continue

            try:
                match = re.search(r"\{.*\}", raw, re.S)
                if not match:
                    logger.debug(
                        "Editor consistency JSON block missing (attempt %s/%s).",
                        attempt,
                        max_retries,
                    )
                    last_failure_reason = "json_block_missing"
                    continue
                data = json.loads(match.group(0))
                new_lead = data.get("lead")
                new_body = data.get("body")
                if isinstance(new_lead, str) and isinstance(new_body, str):
                    resolved_lead = new_lead.strip() or lead
                    resolved_body = new_body.strip() or body
                    rejection = self._rewrite_guard_check(
                        lead,
                        body,
                        resolved_lead,
                        resolved_body,
                        max_rewrite_ratio=0.24,
                        label="editor_consistency",
                    )
                    if rejection:
                        guard_rejected = True
                        logger.info("%s (attempt %s/%s).", rejection, attempt, max_retries)
                        continue
                    return resolved_lead, resolved_body
                logger.debug(
                    "Editor consistency payload invalid (attempt %s/%s).",
                    attempt,
                    max_retries,
                )
                last_failure_reason = "payload_invalid"
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.debug(
                    "Failed to parse editor consistency JSON (attempt %s/%s).",
                    attempt,
                    max_retries,
                    exc_info=exc,
                )
                last_failure_reason = f"json_parse_error:{type(exc).__name__}:{exc}"

        if guard_rejected:
            logger.info("Editor consistency skipped due to aggressive rewrite guard.")
            self._editor_consistency_failed = False
            return lead, body
        logger.warning(
            "Editor consistency all retries failed (%s/%s). Keep original text. reason=%s",
            max_retries,
            max_retries,
            last_failure_reason or "unknown",
        )
        self._editor_consistency_failed = True
        return lead, body

    def _run_post_generation_polish_pass(
        self,
        lead: str,
        body: str,
        *,
        merged_context: str,
        article_type: str,
        target_audience: str,
        review_points: List[str],
    ) -> Tuple[str, str]:
        """Run dormant post-polish pass only when legacy risks require it."""
        signals = self._editor_consistency_signals(lead, body)
        needs_editor = self._should_run_editor_consistency(lead, body)
        needs_readability = self._should_run_readability_polish(review_points, body=body)

        long_multisection = self._heading_count(body) >= 4 and len((body or "").strip()) >= 1600
        hard_consistency_risk = (
            bool(signals.get("missing_intro"))
            or bool(signals.get("missing_closing"))
            or bool(signals.get("pronoun_conflict"))
            or bool(signals.get("style_mixed"))
            or bool(signals.get("stance_anchor_missing"))
        )
        if (
            long_multisection
            and not hard_consistency_risk
            and (bool(signals.get("duplicate_openings")) or needs_readability)
        ):
            logger.info(
                "Post polish skipped for long multi-section body to preserve voice (dup_openings=%s readability=%s).",
                bool(signals.get("duplicate_openings")),
                needs_readability,
            )
            self._editor_consistency_failed = False
            return lead, body

        if not needs_editor and not needs_readability:
            logger.info("Post polish skipped: no structural/readability issues detected.")
            self._editor_consistency_failed = False
            return lead, body

        if needs_editor and needs_readability:
            logger.info("Post polish: running combined editor+readability pass.")
            return self._run_editor_consistency_pass(
                lead,
                body,
                merged_context=merged_context,
                article_type=article_type,
                target_audience=target_audience,
                review_points=review_points,
                readability_focus=True,
            )

        if needs_editor:
            logger.info("Post polish: running editor consistency pass.")
            return self._run_editor_consistency_pass(
                lead,
                body,
                merged_context=merged_context,
                article_type=article_type,
                target_audience=target_audience,
            )

        logger.info("Post polish: running readability polish pass.")
        self._editor_consistency_failed = False
        return self._run_readability_polish_pass(
            lead,
            body,
            merged_context=merged_context,
            article_type=article_type,
            target_audience=target_audience,
            review_points=review_points,
        )

    def _should_run_readability_polish(self, review_points: List[str], *, body: str = "") -> bool:
        if not review_points:
            return False
        high_impact_triggers = (
            "段落が長く論点が混在",
            "文体混在",
            "導入句の反復",
            "見出し順の一貫性不足",
            "結論見出しが早すぎる",
            "断定的な結果・保証表現",
        )
        trigger_hits = sum(
            1
            for point in review_points
            if any(trigger in point for trigger in high_impact_triggers)
        )
        heading_flow_risk = any("見出し順の一貫性不足" in point for point in review_points)
        required_hits = 1 if heading_flow_risk else 2
        if trigger_hits < required_hits:
            return False

        normalized_body = (body or "").strip()
        if len(normalized_body) < 1200:
            return False
        if self._heading_count(normalized_body) < 2:
            return False

        return True

    def _run_readability_polish_pass(
        self,
        lead: str,
        body: str,
        *,
        merged_context: str,
        article_type: str,
        target_audience: str,
        review_points: List[str],
    ) -> Tuple[str, str]:
        if not lead and not body:
            return lead, body
        if not self._should_run_readability_polish(review_points, body=body):
            return lead, body

        writing_focus_guide = self._get_writing_focus_guide()
        editor_persona_block = self._build_editor_persona_block(
            pass_type="readability_polish",
            article_type=article_type,
        )
        review_text = " / ".join(review_points[:3]) if review_points else "なし"
        article_type_labels = ARTICLE_TYPE_LABELS
        context_limit = int(READABILITY_POLISH_CONTEXT_LIMIT)
        prompt = f"""
あなたは日本語編集者です。以下の lead/body を最小限だけ整えてください。
{editor_persona_block}

【目的】
- 読みやすさを上げる（段落過密・文体混在・不自然なつなぎの是正）
- 人間らしい語り口と主旨は維持する

【記事タイプ】
{article_type_labels.get(article_type, article_type)}

【ターゲット読者】
{target_audience}

【本文の重心】
{writing_focus_guide or "自動判定"}

【要修正ポイント】
{review_text}

【参考情報（抜粋）】
{merged_context[:context_limit] if merged_context else "なし"}

【厳守ルール】
1. 事実・数値・固有名詞・見出しは勝手に追加しない。
2. 見出し構成は維持。順序変更は「結論が極端に早い場合」のみ最小限で許可。
3. 長い段落は意味単位で分割し、1段落1トピックを優先する。
4. 文体は原文の会話調・語り口の揺らぎをそのまま保持する。セクションごとのテンション差は意図的な設計。
5. 内容の削除は最小限。要約しすぎない。

【入力】
[LEAD]
{lead}

[BODY]
{body}

【出力形式】
JSONのみ:
{{"lead": "...", "body": "..."}}
""".strip()
        max_tokens = min(4600, max(1200, int((len(lead) + len(body)) * 1.05)))
        try:
            raw = self.llm.generate_text(
                prompt,
                max_tokens=max_tokens,
                task_type="readability_polish",
            ).strip()
        except Exception as exc:
            logger.warning(
                "Readability polish pass failed. Keep original text. (%s: %s)",
                type(exc).__name__,
                exc,
            )
            return lead, body

        if not raw:
            return lead, body
        try:
            match = re.search(r"\{.*\}", raw, re.S)
            if not match:
                logger.warning("Readability polish response missing JSON block. Keep original text.")
                return lead, body
            data = json.loads(match.group(0))
            new_lead = data.get("lead")
            new_body = data.get("body")
            if isinstance(new_lead, str) and isinstance(new_body, str):
                polished_lead = new_lead.strip() or lead
                polished_body = new_body.strip() or body
                if len(polished_body) < max(120, int(len(body) * 0.55)):
                    return lead, body
                rejection = self._rewrite_guard_check(
                    lead,
                    body,
                    polished_lead,
                    polished_body,
                    max_rewrite_ratio=float(READABILITY_POLISH_MAX_REWRITE_RATIO),
                    label="readability_polish",
                )
                if rejection:
                    logger.info("%s", rejection)
                    return lead, body
                return polished_lead, polished_body
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning(
                "Readability polish JSON parse failed. Keep original text. (%s: %s)",
                type(exc).__name__,
                exc,
            )
        return lead, body

    def _extract_quote_candidates(self, merged: str) -> List[str]:
        """Extract story-oriented quote candidates from legacy merged context."""
        if not merged:
            return []
        sentences = re.split(r"(?<=[。！？])", merged)
        candidates = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30 or len(sentence) > 200:
                continue
            story_indicators = r"\d|％|%|とは|定義|研究|調査|実験|こだわ|想い|苦労|背景|きっかけ|気づい|発見|意外|実は"
            if re.search(story_indicators, sentence):
                candidates.append(sentence)

        random.shuffle(candidates)
        return candidates[:5]

    def _legacy_generate_linkedin_addendum(
        self,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        target_chars: int,
        title: Optional[str] = None,
    ) -> str:
        return self._generate_linkedin_addendum(
            merged,
            user_prompt,
            article_type,
            target_audience,
            target_chars,
            title=title,
        )

    def _legacy_adjust_note_length(
        self,
        lead: str,
        body: str,
        references_md: str,
        merged_context: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        title: Optional[str] = None,
    ) -> Tuple[str, str]:
        return self._adjust_note_length(
            lead,
            body,
            references_md,
            merged_context,
            user_prompt,
            article_type,
            target_audience,
            title=title,
        )

    def _legacy_estimate_linkedin_target_chars(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> int:
        return self._estimate_linkedin_target_chars(contexts, user_prompt, article_type)

    def _legacy_detect_linkedin_purpose(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> str:
        return self._detect_linkedin_purpose(contexts, user_prompt, article_type)

    def _legacy_dedupe_lead_body(self, lead: str, body: str) -> Tuple[str, str]:
        return self._dedupe_lead_body(lead, body)

    @staticmethod
    def _legacy_is_reference_or_list_paragraph(paragraph: str) -> bool:
        return ArticleFinalConsistencyMixin._is_reference_or_list_paragraph(paragraph)

    def _legacy_get_active_style_profile(self) -> str:
        return self._get_active_style_profile()

    def _legacy_cap_colloquial_endings(self, text: str, max_allowed: Optional[int] = None) -> str:
        if max_allowed is None:
            max_allowed = int(NON_CASUAL_COLLOQUIAL_ENDING_MAX)
        return self._cap_colloquial_endings(text, max_allowed=max_allowed)

    @classmethod
    def _legacy_break_ending_monotony(cls, text: str, max_consecutive: int = 3) -> str:
        return cls._break_ending_monotony(text, max_consecutive=max_consecutive)

    @staticmethod
    def _legacy_rewrite_ending_for_variety(sentence: str) -> str:
        return ArticleFinalConsistencyMixin._rewrite_ending_for_variety(sentence)

    def _legacy_analyze_style_register(self, text: str) -> Dict[str, Any]:
        return self._analyze_style_register(text)

    def _legacy_should_enforce_polite_register(self) -> bool:
        return self._should_enforce_polite_register()

    def _legacy_normalize_register_to_polite(self, text: str) -> str:
        return self._normalize_register_to_polite(text)

    def _legacy_has_corporate_stance_anchor_gap(self, lead: str, body: str) -> bool:
        return self._has_corporate_stance_anchor_gap(lead, body)

    def _legacy_extract_primary_org_name(self, text: str) -> str:
        return self._extract_primary_org_name(text)

    def _legacy_inject_corporate_stance_anchor(self, lead: str, body: str) -> str:
        return self._inject_corporate_stance_anchor(lead, body)

    def _legacy_normalize_pronoun_usage(self, text: str, target_pronoun: str) -> str:
        return self._normalize_pronoun_usage(text, target_pronoun)

    @staticmethod
    def _legacy_dedupe_cross_section_sentences(body: str, min_phrase_len: int = 14) -> str:
        return ArticleFinalConsistencyMixin._dedupe_cross_section_sentences(
            body,
            min_phrase_len=min_phrase_len,
        )

    def _legacy_dedupe_body_repetition(self, body: str) -> str:
        return self._dedupe_body_repetition(body)

    def _legacy_diversify_overused_phrases(self, text: str) -> str:
        return self._diversify_overused_phrases(text)

    def _legacy_clean_redundant_connectives(self, text: str) -> str:
        return self._clean_redundant_connectives(text)

    @staticmethod
    def _legacy_soften_assertive_expressions(text: str) -> str:
        return ArticleFinalConsistencyMixin._soften_assertive_expressions(text)

    @staticmethod
    def _legacy_strip_heading_top_adversative(text: str) -> str:
        return ArticleFinalConsistencyMixin._strip_heading_top_adversative(text)

    def _legacy_get_concise_compaction_config(self) -> Dict[str, Any]:
        return self._get_concise_compaction_config()

    @staticmethod
    def _legacy_is_summary_marker_sentence(sentence: str) -> bool:
        return ArticleFinalConsistencyMixin._is_summary_marker_sentence(sentence)

    def _legacy_apply_concise_rewrites(self, sentence: str) -> str:
        return self._apply_concise_rewrites(sentence)

    def _legacy_aggressive_sentence_pruning(
        self,
        sentence: str,
        *,
        min_keep_chars: int = 28,
        max_ratio: float = 0.45,
    ) -> str:
        return self._aggressive_sentence_pruning(
            sentence,
            min_keep_chars=min_keep_chars,
            max_ratio=max_ratio,
        )

    def _legacy_compress_redundant_explanations(self, text: str) -> str:
        return self._compress_redundant_explanations(text)

    def _legacy_trim_nonclosing_section_tail_summaries(self, body: str) -> str:
        return self._trim_nonclosing_section_tail_summaries(body)

    @staticmethod
    def _legacy_normalize_opening_token(token: str) -> str:
        return ArticleFinalConsistencyMixin._normalize_opening_token(token)

    @staticmethod
    def _legacy_is_logical_required_opening(token: str) -> bool:
        return ArticleFinalConsistencyMixin._is_logical_required_opening(token)

    @staticmethod
    def _legacy_is_suppressible_template_opening(token: str) -> bool:
        return ArticleFinalConsistencyMixin._is_suppressible_template_opening(token)

    @staticmethod
    def _legacy_strip_opening_safely(sentence: str, pattern: str) -> Tuple[str, bool]:
        return ArticleFinalConsistencyMixin._strip_opening_safely(sentence, pattern)

    def _legacy_trim_redundant_template_opening(
        self,
        sentence: str,
        *,
        is_first_sentence: bool = False,
    ) -> str:
        return self._trim_redundant_template_opening(
            sentence,
            is_first_sentence=is_first_sentence,
        )

    def _legacy_reduce_ai_like_openings(self, text: str) -> str:
        return self._reduce_ai_like_openings(text)

    def _legacy_reduce_ai_like_endings(self, text: str) -> str:
        return self._reduce_ai_like_endings(text)

    def _legacy_reduce_target_term_overuse(
        self,
        text: str,
        *,
        target_audience: str,
        keep: int = 2,
    ) -> str:
        return self._reduce_target_term_overuse(text, target_audience=target_audience, keep=keep)

    def _legacy_normalize_ai_like_heading_labels(self, text: str) -> str:
        return self._normalize_ai_like_heading_labels(text)

    def _legacy_repair_subjectless_openings(self, text: str) -> str:
        return self._repair_subjectless_openings(text)

    @staticmethod
    def _legacy_extract_theme_entities(title: str, outline: object = None) -> List[str]:
        return ArticleFinalConsistencyMixin._extract_theme_entities(title, outline=outline)

    def _legacy_apply_prodrop_zero_anaphora(
        self,
        text: str,
        theme_entities: Optional[List[str]] = None,
    ) -> str:
        return self._apply_prodrop_zero_anaphora(text, theme_entities=theme_entities)

    def _legacy_reduce_repeated_named_entity_openings(self, body: str) -> str:
        return self._reduce_repeated_named_entity_openings(body)

    def _legacy_compress_repeated_subject_openings(self, body: str) -> str:
        return self._compress_repeated_subject_openings(body)

    @staticmethod
    def _legacy_dedupe_similar_headings(body: str) -> str:
        return ArticleFinalConsistencyMixin._dedupe_similar_headings(body)

    def _legacy_apply_unified_dedupe_pass(self, body: str) -> str:
        return self._apply_unified_dedupe_pass(body)

    def _legacy_apply_final_consistency_guards(self, lead: str, body: str) -> Tuple[str, str]:
        return self._apply_final_consistency_guards(lead, body)
