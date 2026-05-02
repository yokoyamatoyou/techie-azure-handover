"""Human Resonance Pipeline

統計言語学に依存せず、心理学・言語学の知見を活用して
「共感・興味・人間味」を生み出すテキスト処理パイプライン。
"""

from .pipeline import (
    HumanResonancePipeline,
    PipelineConfig,
    PipelineResult,
    process_text,
    analyze_text,
)

from .phase0_persona import (
    Phase0Persona,
    Persona,
    create_persona_from_context,
    PERSPECTIVE_DEFAULTS,
)

from .phase1_empathy import (
    Phase1Empathy,
    EmpathyScore,
    calculate_empathy_score,
)

from .phase2_curiosity import (
    Phase2Curiosity,
    CuriosityScore,
    calculate_curiosity_score,
)

from .phase3_humanity import (
    Phase3Humanity,
    HumanityScore,
    calculate_humanity_score,
)

from .phase4_rhythm import (
    Phase4Rhythm,
    RhythmScore,
    calculate_rhythm_score,
)

from .phase5_editor import (
    Phase5Editor,
    EditorIssue,
    FactCheckResult,
    run_editorial_check,
)

from .phase6_legal import (
    Phase6Legal,
    LegalIssue,
    LegalCheckResult,
    RiskLevel,
    run_legal_check,
    fix_legal_issues,
)

from .phase7_sanitize import (
    Phase7Sanitize,
    SanitizeResult,
    sanitize_text,
    analyze_sanitize_needs,
)

from .phase8_platform import (
    Phase8Platform,
    Platform,
    optimize_for_note,
    optimize_for_linkedin,
)

__version__ = "1.0.0"
__all__ = [
    # Pipeline
    "HumanResonancePipeline",
    "PipelineConfig",
    "PipelineResult",
    "process_text",
    "analyze_text",
    # Phase 0
    "Phase0Persona",
    "Persona",
    "create_persona_from_context",
    "PERSPECTIVE_DEFAULTS",
    # Phase 1
    "Phase1Empathy",
    "EmpathyScore",
    "calculate_empathy_score",
    # Phase 2
    "Phase2Curiosity",
    "CuriosityScore",
    "calculate_curiosity_score",
    # Phase 3
    "Phase3Humanity",
    "HumanityScore",
    "calculate_humanity_score",
    # Phase 4
    "Phase4Rhythm",
    "RhythmScore",
    "calculate_rhythm_score",
    # Phase 5
    "Phase5Editor",
    "EditorIssue",
    "FactCheckResult",
    "run_editorial_check",
    # Phase 6
    "Phase6Legal",
    "LegalIssue",
    "LegalCheckResult",
    "RiskLevel",
    "run_legal_check",
    "fix_legal_issues",
    # Phase 7
    "Phase7Sanitize",
    "SanitizeResult",
    "sanitize_text",
    "analyze_sanitize_needs",
    # Phase 8
    "Phase8Platform",
    "Platform",
    "optimize_for_note",
    "optimize_for_linkedin",
]
