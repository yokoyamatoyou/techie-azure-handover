"""policy_engine.py - category routing, UI policy mapping, and ambiguity checks."""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Dict, List, Mapping, Optional, Sequence

BASE_TEMPLATE_OPTIONS = ("branding", "ai", "announcement", "case_study")
FOCUS_OPTIONS = ("analysis", "explanation", "experience")
LEVEL_OPTIONS = ("low", "med", "high")
EVIDENCE_OPTIONS = ("strict", "normal")

DEFAULT_META_BY_TEMPLATE: Dict[str, Dict[str, str]] = {
    "branding": {
        "base_template": "branding",
        "focus_default": "experience",
        "empathy_level": "med",
        "humanity_level": "high",
        "evidence_mode": "normal",
    },
    "ai": {
        "base_template": "ai",
        "focus_default": "explanation",
        "empathy_level": "low",
        "humanity_level": "low",
        "evidence_mode": "strict",
    },
    "announcement": {
        "base_template": "announcement",
        "focus_default": "explanation",
        "empathy_level": "low",
        "humanity_level": "low",
        "evidence_mode": "strict",
    },
    "case_study": {
        "base_template": "case_study",
        "focus_default": "analysis",
        "empathy_level": "med",
        "humanity_level": "med",
        "evidence_mode": "normal",
    },
}

LEVEL_ORDER = {"low": 0, "med": 1, "high": 2}
EMPATHY_TARGET_MAP = {"low": 0.26, "med": 0.44, "high": 0.6}
HUMANITY_TARGET_MAP = {"low": 0.22, "med": 0.36, "high": 0.5}
RHYTHM_TARGET_MAP = {"low": 0.34, "med": 0.46, "high": 0.58}
PRONOUN_REDUCTION_MAP = {"low": 0.3, "med": 0.5, "high": 0.7}
FOCUS_CURIOSITY_TARGET = {"analysis": 0.4, "explanation": 0.45, "experience": 0.5}

TITLE_BANNED_PATTERNS = (
    r"(絶対|必ず|100%|完全保存版|知らないと損|衝撃|驚愕|最強|神(?:コスパ|回)|秒で)",
    r"(稼げる|爆益|必勝|一瞬で)",
)

PAPER_KEYWORDS = ("論文", "査読", "研究", "実験", "手法", "arxiv", "dataset", "アブストラクト")
BRANDING_KEYWORDS = ("ブランド", "企業", "理念", "沿革", "代表", "想い", "価値訴求", "ミッション", "ビジョン")
CORPORATE_BRANDING_KEYWORDS = (
    "企業ブランディング",
    "コーポレート",
    "企業紹介",
    "会社紹介",
    "企業情報",
    "理念",
    "ミッション",
    "ビジョン",
    "パーパス",
    "アイデンティティ",
    "identity",
    "philosophy",
    "社名由来",
    "価値訴求",
)
ANNOUNCE_KEYWORDS = ("お知らせ", "アップデート", "告知", "リリース", "メンテナンス")
CASE_KEYWORDS = ("導入事例", "ケーススタディ", "事例", "実績", "比較検証", "ビフォーアフター")

AMBIGUOUS_TERM_RULES = {
    "釣り": {
        "question": "「釣り」はどちらの意味ですか？",
        "options": (
            ("魚釣り", "魚を釣る活動のこと"),
            ("比喩（釣りタイトル/釣り広告）", "煽りやクリック誘導の比喩"),
        ),
        "disambiguate": {
            "魚釣り": ("魚", "海", "川", "釣具", "釣り竿", "ルアー", "釣果"),
            "比喩（釣りタイトル/釣り広告）": ("タイトル", "広告", "見出し", "煽り", "クリック", "bait"),
        },
    },
    "炎上": {
        "question": "「炎上」はどちらの文脈ですか？",
        "options": (
            ("SNS炎上", "SNS等での批判拡散"),
            ("比喩/演出", "火や過熱の比喩"),
        ),
        "disambiguate": {
            "SNS炎上": ("SNS", "投稿", "コメント", "拡散", "トレンド", "X", "炎上対応"),
            "比喩/演出": ("火", "燃焼", "演出", "熱量", "比喩"),
        },
    },
}


@dataclass(frozen=True)
class CategoryPolicy:
    article_type: str
    base_template: str
    focus_default: str
    empathy_level: str
    humanity_level: str
    evidence_mode: str
    source: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class PipelinePolicy:
    focus: str
    empathy_level: str
    humanity_level: str
    rhythm_level: str
    pronoun_level: str
    evidence_mode: str
    style_profile: str
    empathy_target: float
    curiosity_target: float
    humanity_target: float
    rhythm_target: float
    pronoun_reduction_ratio: float
    rationale: List[str]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AmbiguousTermCandidate:
    term: str
    question: str
    options: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AmbiguityCheckResult:
    requires_confirmation: bool
    signature: str
    candidates: List[AmbiguousTermCandidate]

    def to_dict(self) -> Dict[str, object]:
        return {
            "requires_confirmation": self.requires_confirmation,
            "signature": self.signature,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


def _pick_level(value: Optional[str], default: str) -> str:
    if value in LEVEL_OPTIONS:
        return value
    return default


def _pick_focus(value: Optional[str], default: str) -> str:
    if value in FOCUS_OPTIONS:
        return value
    return default


def _pick_template(value: Optional[str], default: str) -> str:
    if value in BASE_TEMPLATE_OPTIONS:
        return value
    return default


def _pick_evidence(value: Optional[str], default: str) -> str:
    if value in EVIDENCE_OPTIONS:
        return value
    return default


def _contains_any(text: str, words: Sequence[str]) -> bool:
    lowered = (text or "").lower()
    return any(word.lower() in lowered for word in words)


PARTICIPANT_MODE_OPTIONS = ("auto", "participant", "observer")


def _pick_participant_mode(value: Optional[str], default: str = "auto") -> str:
    if value in PARTICIPANT_MODE_OPTIONS:
        return value
    return default


def normalize_category_meta(meta: Optional[Mapping[str, str]]) -> Dict[str, str]:
    base_template = _pick_template((meta or {}).get("base_template"), "ai")
    defaults = DEFAULT_META_BY_TEMPLATE.get(base_template, DEFAULT_META_BY_TEMPLATE["ai"])
    participant_mode = _pick_participant_mode((meta or {}).get("participant_mode"))
    result = {
        "base_template": base_template,
        "focus_default": _pick_focus((meta or {}).get("focus_default"), defaults["focus_default"]),
        "empathy_level": _pick_level((meta or {}).get("empathy_level"), defaults["empathy_level"]),
        "humanity_level": _pick_level((meta or {}).get("humanity_level"), defaults["humanity_level"]),
        "evidence_mode": _pick_evidence((meta or {}).get("evidence_mode"), defaults["evidence_mode"]),
    }
    # R19: participant_mode による focus_default の上書き
    if participant_mode == "participant":
        result["focus_default"] = "experience"
    elif participant_mode == "observer":
        result["focus_default"] = "explanation"
    return result


def _infer_base_template(text: str, writing_focus: str) -> str:
    if _contains_any(text, PAPER_KEYWORDS):
        return "ai"
    if _contains_any(text, BRANDING_KEYWORDS):
        return "branding"
    if _contains_any(text, ANNOUNCE_KEYWORDS):
        return "announcement"
    if _contains_any(text, CASE_KEYWORDS):
        return "case_study"
    if writing_focus == "experience":
        return "branding"
    if writing_focus == "analysis":
        return "case_study"
    return "ai"


def estimate_category_meta(
    label: str,
    prompt: str,
    *,
    user_prompt: str = "",
    writing_focus: str = "auto",
) -> Dict[str, str]:
    focus_key = writing_focus if writing_focus in FOCUS_OPTIONS else "explanation"
    text = " ".join(part for part in [label, prompt, user_prompt] if part)
    base_template = _infer_base_template(text, focus_key)
    defaults = dict(DEFAULT_META_BY_TEMPLATE[base_template])

    if _contains_any(text, PAPER_KEYWORDS):
        defaults.update(
            {
                "base_template": "ai",
                "focus_default": "analysis" if focus_key == "analysis" else "explanation",
                "empathy_level": "low",
                "humanity_level": "low",
                "evidence_mode": "strict",
            }
        )
    elif _contains_any(text, CORPORATE_BRANDING_KEYWORDS):
        defaults.update(
            {
                "base_template": "branding",
                "focus_default": "explanation",
                "empathy_level": "med",
                "humanity_level": "med",
                "evidence_mode": "strict",
            }
        )
    elif _contains_any(text, BRANDING_KEYWORDS):
        defaults.update(
            {
                "base_template": "branding",
                "focus_default": "experience",
                "empathy_level": "high",
                "humanity_level": "high",
                "evidence_mode": "normal",
            }
        )

    if focus_key in FOCUS_OPTIONS:
        defaults["focus_default"] = focus_key
    return normalize_category_meta(defaults)


def resolve_category_policy(
    article_type: str,
    *,
    custom_prompt: str = "",
    custom_meta: Optional[Mapping[str, str]] = None,
    user_prompt: str = "",
    writing_focus: str = "auto",
) -> CategoryPolicy:
    if article_type in DEFAULT_META_BY_TEMPLATE:
        meta = normalize_category_meta(DEFAULT_META_BY_TEMPLATE[article_type])
        return CategoryPolicy(article_type=article_type, source="ui_selection", **meta)

    if custom_meta:
        normalized = normalize_category_meta(custom_meta)
        return CategoryPolicy(article_type=article_type, source="custom_meta", **normalized)

    estimated = estimate_category_meta(
        article_type,
        custom_prompt,
        user_prompt=user_prompt,
        writing_focus=writing_focus,
    )
    return CategoryPolicy(article_type=article_type, source="custom_prompt_inference", **estimated)


def _set_lower(current: str, target: str) -> str:
    if LEVEL_ORDER[target] < LEVEL_ORDER[current]:
        return target
    return current


def _set_higher(current: str, target: str) -> str:
    if LEVEL_ORDER[target] > LEVEL_ORDER[current]:
        return target
    return current


def build_pipeline_policy(
    *,
    article_type: str,
    perspective: str,
    psychology_structure: str,
    writing_focus: str,
    length_mode: str,
    user_prompt: str,
    category_policy: CategoryPolicy,
) -> PipelinePolicy:
    focus = category_policy.focus_default
    if writing_focus in FOCUS_OPTIONS:
        focus = writing_focus

    empathy = category_policy.empathy_level
    humanity = category_policy.humanity_level
    rhythm = "med"
    pronoun = "med"
    evidence = category_policy.evidence_mode
    rationale: List[str] = [f"category:{category_policy.source}"]

    if focus == "analysis":
        empathy = "low"
        humanity = "low"
        evidence = "strict"
        rationale.append("focus:analysis")
    elif focus == "experience":
        empathy = "high"
        humanity = "high"
        evidence = "normal"
        pronoun = "low"
        rationale.append("focus:experience")
    elif focus == "explanation":
        empathy = "med"
        humanity = "med"
        rationale.append("focus:explanation")

    if psychology_structure == "decision_support":
        empathy = "low"
        humanity = "low"
        evidence = "strict"
        rationale.append("structure:decision_support")

    if perspective == "journalist":
        empathy = "low"
        humanity = "low"
        pronoun = "high"
        evidence = "strict"
        rationale.append("perspective:journalist")
    elif perspective == "corporate":
        empathy = _set_higher(empathy, "med")
        humanity = _set_higher(humanity, "med")
        pronoun = _set_higher(pronoun, "med")
        rationale.append("perspective:corporate")

    if length_mode == "short":
        empathy = "low"
        humanity = "low"
        rhythm = "high"
        pronoun = "low"
        evidence = "strict"
        rationale.append("length:short")
    elif length_mode == "long":
        empathy = _set_higher(empathy, "med")
        humanity = _set_higher(humanity, "med")
        rhythm = "high"
        pronoun = _set_higher(pronoun, "med")
        rationale.append("length:long")

    text = f"{article_type} {user_prompt or ''}"
    if category_policy.base_template == "ai" and _contains_any(text, PAPER_KEYWORDS):
        empathy = "low"
        humanity = "low"
        evidence = "strict"
        focus = "analysis" if writing_focus == "analysis" else focus
        rationale.append("category_adjustment:ai_paper")
    if category_policy.base_template == "branding" and _contains_any(text, BRANDING_KEYWORDS):
        empathy = _set_higher(empathy, "high")
        humanity = _set_higher(humanity, "high")
        evidence = "normal"
        rationale.append("category_adjustment:branding")

    style_profile = "balanced"
    if evidence == "strict":
        style_profile = "formal"
    elif (
        focus == "experience"
        and LEVEL_ORDER[humanity] >= LEVEL_ORDER["high"]
        and LEVEL_ORDER[empathy] >= LEVEL_ORDER["med"]
    ):
        style_profile = "casual"
    if perspective == "corporate" and style_profile == "casual":
        style_profile = "balanced"
        rationale.append("style:corporate_guard")

    curiosity = FOCUS_CURIOSITY_TARGET.get(focus, 0.45)
    if length_mode == "short":
        curiosity = max(0.35, curiosity - 0.03)
    elif length_mode == "long":
        curiosity = min(0.6, curiosity + 0.02)

    return PipelinePolicy(
        focus=focus,
        empathy_level=empathy,
        humanity_level=humanity,
        rhythm_level=rhythm,
        pronoun_level=pronoun,
        evidence_mode=evidence,
        style_profile=style_profile,
        empathy_target=EMPATHY_TARGET_MAP[empathy],
        curiosity_target=round(curiosity, 3),
        humanity_target=HUMANITY_TARGET_MAP[humanity],
        rhythm_target=RHYTHM_TARGET_MAP[rhythm],
        pronoun_reduction_ratio=PRONOUN_REDUCTION_MAP[pronoun],
        rationale=rationale,
    )


def policy_directives(policy: CategoryPolicy) -> str:
    lines = []
    if policy.base_template == "ai" and policy.evidence_mode == "strict":
        lines.extend(
            [
                "- 論点の取り違えを避けるため、主張と根拠を対応させる。",
                "- 体験談は控えめにし、要点整理と一次情報ベースを優先する。",
                "- 根拠が弱い情報は断定しない。",
            ]
        )
    if policy.base_template == "branding":
        lines.extend(
            [
                "- 価値訴求を中心に構成し、便益が読者に伝わる語彙を選ぶ。",
                "- 体験・ストーリーは任意。公式情報中心の記事では無理に入れない。",
                "- 事実に基づく実感のある言い回しを優先する。",
            ]
        )
    if not lines:
        lines.append("- 具体性と読者適合を優先し、断定の根拠を明確にする。")
    return "\n".join(lines)


def evaluate_title_quality(title: str, focus: str, evidence_mode: str) -> List[str]:
    issues: List[str] = []
    normalized = (title or "").strip()
    if not normalized:
        return ["empty_title"]
    if re.search(r"(?:の考察|について)$", normalized):
        issues.append("vague_ending")
    for pattern in TITLE_BANNED_PATTERNS:
        if re.search(pattern, normalized):
            issues.append("clickbait_or_exaggeration")
            break
    if re.search(r"(すごい|やばい|圧倒的|究極|劇的)", normalized):
        issues.append("over_decorative_ai_tone")
    if focus == "analysis" and re.search(r"[?？]$", normalized):
        issues.append("analysis_title_should_avoid_question_hook")
    if evidence_mode == "strict" and re.search(r"(完全|絶対|必勝|保証)", normalized):
        issues.append("strict_mode_disallows_overclaim")
    return issues


def detect_ambiguous_terms(text: str) -> AmbiguityCheckResult:
    candidates: List[AmbiguousTermCandidate] = []
    source = text or ""
    explicit_clarify_request = bool(re.search(r"(意味\s*を\s*確認|どちらの意味|語義|意味を教えて)", source))

    for term, rule in AMBIGUOUS_TERM_RULES.items():
        if term not in source:
            continue
        decided = False
        around = source
        for option_label, words in rule["disambiguate"].items():
            if _contains_any(around, words):
                decided = True
                break
        if decided and not explicit_clarify_request:
            continue

        options = [{"value": value, "label": label} for value, label in rule["options"]]
        candidates.append(
            AmbiguousTermCandidate(
                term=term,
                question=rule["question"],
                options=options,
            )
        )

    signature_src = source + "|" + "|".join(candidate.term for candidate in candidates)
    signature = hashlib.sha1(signature_src.encode("utf-8")).hexdigest()[:12]
    return AmbiguityCheckResult(
        requires_confirmation=bool(candidates),
        signature=signature,
        candidates=candidates,
    )


def format_ambiguity_clarifications(selections: Mapping[str, str]) -> str:
    lines = []
    for term, meaning in (selections or {}).items():
        if term and meaning:
            lines.append(f"【語義確認】「{term}」は「{meaning}」として扱う。")
    return "\n".join(lines)
