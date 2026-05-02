"""Style/tone/editor-persona helpers for ArticleGenerator."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

TONE_PROFILE_OPTIONS = {"auto", "calm", "gentle", "passionate"}
DEFAULT_TONE_PROFILE_BY_ARTICLE_TYPE = {
    "announcement": "calm",
    "ai": "calm",
    "branding": "passionate",
    "daily_happenings": "gentle",
}
DEFAULT_TONE_PROFILE_BY_BASE_TEMPLATE = {
    "announcement": "calm",
    "ai": "calm",
    "branding": "passionate",
}
TONE_TO_STYLE_PROFILE = {
    "calm": "formal",
    "gentle": "balanced",
    "passionate": "casual",
}

EDITOR_PASS_TYPES = (
    "editor_consistency",
    "readability_polish",
    "repair_only",
    "verification",
)

EDITOR_PASS_MISSIONS = {
    "editor_consistency": "構成と意味の整合を最小差分で回復する",
    "readability_polish": "可読性を上げつつ語り口の温度を維持する",
    "repair_only": "文法破綻のみ最小差分で補修する",
    "verification": "根拠範囲を守り断定リスクを下げる",
}

EDITOR_PERSONA_PROFILES = {
    "brand_balance": {
        "role": "ブランド編集デスク",
        "principles": [
            "企業らしい信頼感と人間味のバランスを保つ",
            "宣伝臭を抑え、便益と具体性を優先する",
            "必要以上の書き換えで声色を平坦化しない",
        ],
    },
    "factual_guard": {
        "role": "事実整合エディター",
        "principles": [
            "断定を抑え、事実と推定の境界を明確にする",
            "数字・固有名詞の扱いを慎重にし、誤認を防ぐ",
            "簡潔さを維持しつつ意味欠落を起こさない",
        ],
    },
    "reproducibility_guard": {
        "role": "再現性レビュー編集者",
        "principles": [
            "条件・前提・限界を残して再現可能性を担保する",
            "成功談の美化を避け、判断材料を欠かさない",
            "手順と結果の対応関係を崩さない",
        ],
    },
    "narrative_guard": {
        "role": "語り口保全エディター",
        "principles": [
            "現場の体温を残し、機械的な均一化を避ける",
            "段落の呼吸と自然な改行を優先する",
            "感情表現を削りすぎず、過度な誇張だけ抑える",
        ],
    },
}


class ArticleStylePersonaMixin:
    def _resolve_editor_persona_profile(
        self,
        *,
        pass_type: str,
        article_type: str,
        focus: str,
        evidence_mode: str,
    ) -> Dict[str, Any]:
        pass_key = pass_type if pass_type in EDITOR_PASS_TYPES else "editor_consistency"
        focus_key = (focus or "").strip().lower()
        evidence_key = (evidence_mode or "normal").strip().lower()
        article_key = (article_type or "").strip().lower()

        if article_key == "daily_happenings" or (focus_key == "experience" and evidence_key != "strict"):
            profile_key = "narrative_guard"
        elif article_key == "case_study" or focus_key == "analysis":
            profile_key = "reproducibility_guard"
        elif evidence_key == "strict" or article_key in {"ai", "announcement"}:
            profile_key = "factual_guard"
        else:
            profile_key = "brand_balance"

        base = dict(EDITOR_PERSONA_PROFILES.get(profile_key, EDITOR_PERSONA_PROFILES["brand_balance"]))
        base["profile_key"] = profile_key
        base["pass_type"] = pass_key
        base["pass_mission"] = EDITOR_PASS_MISSIONS.get(pass_key, EDITOR_PASS_MISSIONS["editor_consistency"])
        return base

    def _snapshot_editor_personas(
        self,
        *,
        article_type: str,
        focus: str,
        evidence_mode: str,
    ) -> None:
        snapshots: Dict[str, Dict[str, Any]] = {}
        for pass_type in EDITOR_PASS_TYPES:
            snapshots[pass_type] = self._resolve_editor_persona_profile(
                pass_type=pass_type,
                article_type=article_type,
                focus=focus,
                evidence_mode=evidence_mode,
            )
        self._editor_persona_snapshots = snapshots

    def _get_editor_persona_profile(
        self,
        *,
        pass_type: str,
        article_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass_key = pass_type if pass_type in EDITOR_PASS_TYPES else "editor_consistency"
        snapshots = getattr(self, "_editor_persona_snapshots", {}) or {}
        if isinstance(snapshots, dict):
            cached = snapshots.get(pass_key)
            if isinstance(cached, dict) and cached:
                return dict(cached)

        policy = getattr(self, "_pipeline_policy", {}) or {}
        return self._resolve_editor_persona_profile(
            pass_type=pass_key,
            article_type=article_type or str(getattr(self, "_current_type", "") or ""),
            focus=str(policy.get("focus", getattr(self, "_effective_writing_focus", "explanation"))),
            evidence_mode=str(policy.get("evidence_mode", "normal")),
        )

    def _build_editor_persona_block(
        self,
        *,
        pass_type: str,
        article_type: Optional[str] = None,
    ) -> str:
        profile = self._get_editor_persona_profile(pass_type=pass_type, article_type=article_type)
        principles = profile.get("principles")
        if not isinstance(principles, list):
            principles = []
        principle_lines = "\n".join(f"- {str(line)}" for line in principles[:3] if str(line).strip())
        return (
            "【編集ペルソナ】\n"
            f"役割: {profile.get('role', '編集者')}\n"
            f"ミッション: {profile.get('pass_mission', '')}\n"
            "方針:\n"
            f"{principle_lines or '- 最小差分で品質を回復する'}"
        ).strip()

    def set_allow_experience(self, allow: bool) -> None:
        """経験談の許可設定を更新する（R14-T15）。"""
        self._allow_experience = allow
        logger.info("Experience allowance set to: %s", allow)

    def _normalize_tone_profile(self, tone_profile: Optional[str]) -> str:
        key = str(tone_profile or "auto").strip().lower()
        if key in TONE_PROFILE_OPTIONS:
            return key
        return "auto"

    def set_tone_profile_preference(self, tone_profile: Optional[str]) -> None:
        """語り口トーンの優先設定を更新する。"""
        normalized = self._normalize_tone_profile(tone_profile)
        self._tone_profile_preference = normalized
        logger.info("Tone profile preference set to: %s", normalized)

    def _resolve_effective_tone_profile(
        self,
        *,
        article_type: str = "",
        base_template: str = "",
    ) -> str:
        preferred = self._normalize_tone_profile(getattr(self, "_tone_profile_preference", "auto"))
        if preferred != "auto":
            return preferred

        article_key = (article_type or getattr(self, "_current_type", "") or "").strip().lower()
        if article_key in DEFAULT_TONE_PROFILE_BY_ARTICLE_TYPE:
            return DEFAULT_TONE_PROFILE_BY_ARTICLE_TYPE[article_key]

        policy = getattr(self, "_category_policy", {}) or {}
        base_key = str(base_template or policy.get("base_template", "") or "").strip().lower()
        return DEFAULT_TONE_PROFILE_BY_BASE_TEMPLATE.get(base_key, "auto")

    def _resolve_style_profile_from_tone(
        self,
        *,
        style_profile: str,
        tone_profile: str,
        focus: str,
        evidence_mode: str,
        perspective: str,
    ) -> str:
        resolved = str(style_profile or "balanced").strip().lower()
        if resolved not in {"formal", "balanced", "casual"}:
            resolved = "balanced"

        tone_key = self._normalize_tone_profile(tone_profile)
        if tone_key != "auto":
            resolved = TONE_TO_STYLE_PROFILE.get(tone_key, resolved)

        evidence_key = str(evidence_mode or "normal").strip().lower()
        focus_key = str(focus or "explanation").strip().lower()
        perspective_key = str(perspective or "").strip().lower()

        if evidence_key == "strict":
            return "formal"
        if focus_key == "analysis" and resolved == "casual":
            return "formal"
        if focus_key == "explanation" and resolved == "casual":
            return "balanced"
        if perspective_key == "corporate" and resolved == "casual":
            return "balanced"
        return resolved

    def _apply_tone_profile_preference(
        self,
        *,
        article_type: str = "",
        category_base_template: str = "",
    ) -> None:
        policy = dict(getattr(self, "_pipeline_policy", {}) or {})
        if not policy:
            self._effective_tone_profile = self._normalize_tone_profile(
                getattr(self, "_tone_profile_preference", "auto")
            )
            return

        tone_key = self._resolve_effective_tone_profile(
            article_type=article_type,
            base_template=category_base_template,
        )
        resolved_style = self._resolve_style_profile_from_tone(
            style_profile=str(policy.get("style_profile", "") or ""),
            tone_profile=tone_key,
            focus=str(policy.get("focus", self._get_effective_writing_focus()) or ""),
            evidence_mode=str(policy.get("evidence_mode", "normal") or "normal"),
            perspective=str(self._current_perspective or ""),
        )
        policy["tone_profile"] = tone_key
        policy["style_profile"] = resolved_style
        rationale = [str(item) for item in (policy.get("rationale") or []) if str(item).strip()]
        rationale.append(f"tone:{tone_key}->{resolved_style}")
        policy["rationale"] = rationale[-12:]
        self._pipeline_policy = policy
        self._effective_tone_profile = tone_key
