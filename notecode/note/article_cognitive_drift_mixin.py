"""Cognitive drift profile helpers for ArticleGenerator."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from core.app_config import get_postprocess_config

COGNITIVE_ENERGY_PROFILES = [
    {
        "phase": "careful_start",
        "range": (0.0, 0.15),
        "temperature": (0.65, 0.78),
        "sentence_complexity": "simple",
        "prompt_tone": "丁寧に定義し、信頼を構築する。慎重に書き始める。",
        "allow_digression": False,
    },
    {
        "phase": "building",
        "range": (0.15, 0.40),
        "temperature": (0.82, 0.95),
        "sentence_complexity": "moderate",
        "prompt_tone": "根拠を積み重ね、自分なりの解釈を加える。",
        "allow_digression": False,
    },
    {
        "phase": "peak",
        "range": (0.40, 0.65),
        "temperature": (0.98, 1.15),
        "sentence_complexity": "complex",
        "prompt_tone": "大胆な展開をする。思い切った主張や独自の切り口を入れる。",
        "allow_digression": True,
    },
    {
        "phase": "settling",
        "range": (0.65, 0.85),
        "temperature": (0.78, 0.92),
        "sentence_complexity": "moderate",
        "prompt_tone": "議論を整理し、トーンを落ち着かせる。",
        "allow_digression": False,
    },
    {
        "phase": "winding_down",
        "range": (0.85, 1.01),
        "temperature": (0.70, 0.85),
        "sentence_complexity": "simple",
        "prompt_tone": "端的に、素朴に、実践的にまとめる。",
        "allow_digression": False,
    },
]

PARAGRAPH_COMPLEXITY_HINTS = {
    "simple": "短文中心で、定義や要点を明快に置く",
    "moderate": "短文と中文を混ぜ、根拠と具体を往復する",
    "complex": "情報密度を一段上げるが、冗長化は避ける",
}

PARAGRAPH_DENSITY_HINTS = {
    "low": "情報量は軽めにし、読者が一息つける密度で書く",
    "medium": "情報量は中程度。具体と抽象を1往復させる",
    "high": "情報量を高め、固有名詞・数字・具体動作を優先する",
}

PHASE_PARAGRAPH_TONE_HINTS = {
    "careful_start": "慎重に前提を置き、断定は急がない",
    "building": "論点を積み上げ、読者の理解を段階的に進める",
    "peak": "切り口を一段深め、主張の勢いを出す",
    "settling": "論点を整理し、読者の納得感を作る",
    "winding_down": "要点を端的に回収し、実践に接続する",
}


class ArticleCognitiveDriftMixin:
    def _resolve_cognitive_phase(self, position: float) -> Dict[str, Any]:
        clamped = max(0.0, min(1.0, float(position)))
        phase = COGNITIVE_ENERGY_PROFILES[2]  # peak fallback
        for candidate in COGNITIVE_ENERGY_PROFILES:
            start, end = candidate["range"]
            if start <= clamped < end:
                phase = candidate
                break
        return phase

    def _estimate_paragraph_slot_count(
        self,
        target_chars: Optional[int],
        min_blocks: int,
        max_blocks: int,
    ) -> int:
        if target_chars is None:
            estimated = 3
        elif target_chars >= 1450:
            estimated = 5
        elif target_chars >= 1020:
            estimated = 4
        else:
            estimated = 3
        return max(min_blocks, min(max_blocks, estimated))

    def _resolve_information_density(
        self,
        *,
        local_index: int,
        slot_count: int,
        role: str,
        phase_key: str,
    ) -> str:
        if slot_count <= 1:
            return "medium"
        if role == "収束":
            return "low"
        if role == "山場":
            return "high"
        patterns = {
            2: ["medium", "low"],
            3: ["medium", "high", "low"],
            4: ["medium", "high", "medium", "low"],
            5: ["medium", "high", "low", "high", "low"],
        }
        base_pattern = patterns.get(slot_count)
        if not base_pattern:
            base_pattern = ["medium", "high"] + ["medium"] * max(0, slot_count - 3) + ["low"]
        density = base_pattern[min(local_index, len(base_pattern) - 1)]

        if phase_key == "peak" and density == "low":
            density = "medium"
        elif phase_key == "winding_down" and density == "high":
            density = "medium"
        elif phase_key == "careful_start" and density == "high":
            density = "medium"
        return density

    def _build_paragraph_drift_plan(
        self,
        *,
        section_index: int,
        total_sections: int,
        target_chars: Optional[int],
        section_profile: Dict[str, Any],
        drift_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if not drift_config.get("paragraph_enabled", True):
            return []

        min_blocks = int(drift_config.get("paragraph_min_blocks", 3))
        max_blocks = int(drift_config.get("paragraph_max_blocks", 4))
        slot_count = self._estimate_paragraph_slot_count(
            target_chars,
            min_blocks=min_blocks,
            max_blocks=max_blocks,
        )
        if slot_count <= 1:
            return []

        base_temp = float(section_profile.get("temperature", 0.9))
        effective_focus = getattr(self, "_effective_writing_focus", "")
        focus_overrides = (get_postprocess_config() or {}).get("focus_pipeline_overrides", {})
        if effective_focus and effective_focus in focus_overrides:
            peak_boost = float(focus_overrides[effective_focus].get("peak_temp_boost", 0))
            base_temp = min(1.2, base_temp + peak_boost)
        temp_swing = float(drift_config.get("paragraph_temp_swing", 0.08))
        peak_index = max(1, min(slot_count - 2, round((slot_count - 1) * 0.55)))
        plan: List[Dict[str, Any]] = []

        for local_index in range(slot_count):
            local_ratio = local_index / max(1, slot_count - 1)
            global_position = (section_index + local_ratio) / max(1, total_sections)
            phase = self._resolve_cognitive_phase(global_position)
            phase_low, phase_high = phase["temperature"]
            phase_mid = (phase_low + phase_high) / 2.0
            delta = max(-temp_swing, min(temp_swing, phase_mid - base_temp))
            paragraph_temp = max(0.5, min(1.2, base_temp + delta + random.uniform(-0.012, 0.012)))

            if local_index == 0:
                role = "導入"
            elif local_index == slot_count - 1:
                role = "収束"
            elif local_index == peak_index:
                role = "山場"
            else:
                role = "展開"

            information_density = self._resolve_information_density(
                local_index=local_index,
                slot_count=slot_count,
                role=role,
                phase_key=phase["phase"],
            )
            fatigue = self._resolve_fatigue_profile(
                global_position=global_position,
                drift_config=drift_config,
            )

            entry: Dict[str, Any] = {
                "index": local_index + 1,
                "role": role,
                "phase": phase["phase"],
                "temperature": round(paragraph_temp, 3),
                "sentence_complexity": phase["sentence_complexity"],
                "information_density": information_density,
            }
            if fatigue:
                entry["fatigue_profile"] = fatigue

            plan.append(entry)
        return plan

    def _resolve_fatigue_profile(
        self,
        *,
        global_position: float,
        drift_config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Return fatigue profile when position exceeds onset ratio (R5-T12)."""
        if not drift_config.get("fatigue_enabled", True):
            return None
        onset = float(drift_config.get("fatigue_onset_ratio", 0.55))
        if global_position < onset:
            return None
        intensity = min(1.0, (global_position - onset) / max(0.01, 1.0 - onset))
        syntax_relax = float(drift_config.get("fatigue_syntax_relaxation", 0.3))
        vocab_tol = float(drift_config.get("fatigue_vocab_repetition_tolerance", 0.4))
        meta_allowed = drift_config.get("fatigue_meta_linguistic_allowed", True)
        return {
            "intensity": round(intensity, 3),
            "syntax_relaxation": round(syntax_relax * intensity, 3),
            "vocab_repetition_tolerance": round(vocab_tol * intensity, 3),
            "meta_linguistic_allowed": meta_allowed and intensity > 0.3,
        }

    def _render_paragraph_drift_block(self, plan: Optional[List[Dict[str, Any]]]) -> str:
        items = plan or []
        if not items:
            return ""
        lines: List[str] = []
        for item in items:
            phase_key = str(item.get("phase", "building"))
            complexity_key = str(item.get("sentence_complexity", "moderate"))
            density_key = str(item.get("information_density", "medium"))
            complexity_hint = PARAGRAPH_COMPLEXITY_HINTS.get(
                complexity_key,
                PARAGRAPH_COMPLEXITY_HINTS["moderate"],
            )
            density_hint = PARAGRAPH_DENSITY_HINTS.get(
                density_key,
                PARAGRAPH_DENSITY_HINTS["medium"],
            )
            tone_hint = PHASE_PARAGRAPH_TONE_HINTS.get(
                phase_key,
                PHASE_PARAGRAPH_TONE_HINTS["building"],
            )
            lines.append(
                f"- P{int(item.get('index', 0) or 0)}（{item.get('role', '展開')}）: "
                f"{phase_key} / 温度目安 {float(item.get('temperature', 0.9)):.2f} / "
                f"{complexity_hint} / 情報密度 {density_key}（{density_hint}） / {tone_hint}"
            )
        return "\n".join(lines)

    def _get_cognitive_profile(
        self,
        section_index: int,
        total_sections: int,
        *,
        target_chars: Optional[int] = None,
        drift_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """セクション位置に応じた認知エネルギープロファイルを返す。"""
        if total_sections <= 1:
            phase = COGNITIVE_ENERGY_PROFILES[1]  # building
        elif total_sections == 2:
            phase = COGNITIVE_ENERGY_PROFILES[0] if section_index == 0 else COGNITIVE_ENERGY_PROFILES[4]
        elif total_sections == 3:
            phase = (
                COGNITIVE_ENERGY_PROFILES[[0, 2, 4][section_index]]
                if section_index < 3
                else COGNITIVE_ENERGY_PROFILES[2]
            )
        else:
            position = section_index / max(1, total_sections - 1)
            phase = self._resolve_cognitive_phase(position)

        temp_low, temp_high = phase["temperature"]
        jitter = random.uniform(-0.03, 0.03)
        temperature = max(0.5, min(1.2, random.uniform(temp_low, temp_high) + jitter))

        profile = {
            "phase": phase["phase"],
            "temperature": round(temperature, 3),
            "sentence_complexity": phase["sentence_complexity"],
            "prompt_tone": phase["prompt_tone"],
            "allow_digression": phase["allow_digression"],
        }
        resolved_config = (
            drift_config
            if isinstance(drift_config, dict)
            else getattr(self, "_cognitive_drift_config", {}) or {}
        )
        profile["paragraph_plan"] = self._build_paragraph_drift_plan(
            section_index=section_index,
            total_sections=total_sections,
            target_chars=target_chars,
            section_profile=profile,
            drift_config=resolved_config,
        )
        return profile
