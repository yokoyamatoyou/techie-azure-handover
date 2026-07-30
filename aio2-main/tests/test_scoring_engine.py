from __future__ import annotations

from core.scoring_engine import ScoreContext, ScoringEngine


def test_integrate_keeps_ymyl_score_when_eeat_is_high() -> None:
    engine = ScoringEngine()

    result = engine.integrate(
        seo_results={
            "total_score": 80.0,
            "scores": {},
            "risk": {},
            "eeat": {"is_ymyl": True},
        },
        aio_results={
            "total_score": 70.0,
            "scores": {"eeat": {"score": 7.5}},
            "immediate_actions": [],
        },
        ctx=ScoreContext(intent="informational", industry="医療・クリニック", url_type="企業"),
    )

    assert result["aio_score_before_penalty"] == 70.0
    assert result["aio_score"] == 70.0
    assert result["applied_penalties"] == []
    assert result["heuristic_notes"] == []


def test_integrate_adds_ymyl_note_without_score_penalty_when_eeat_is_low() -> None:
    engine = ScoringEngine()

    result = engine.integrate(
        seo_results={
            "total_score": 80.0,
            "scores": {},
            "risk": {},
            "eeat": {"is_ymyl": True},
        },
        aio_results={
            "total_score": 70.0,
            "scores": {"eeat": {"score": 3.0}},
            "immediate_actions": [],
        },
        ctx=ScoreContext(intent="informational", industry="医療・クリニック", url_type="企業"),
    )

    assert result["aio_score_before_penalty"] == 70.0
    assert result["aio_score"] == 70.0
    assert result["applied_penalties"] == []
    assert result["heuristic_notes"] == [
        "YMYL領域では著者・資格・一次情報の補強を優先してください（内部ヒューリスティック警告、点数乗算なし）"
    ]


def test_integrate_applies_soft_parasitic_penalty() -> None:
    engine = ScoringEngine()

    result = engine.integrate(
        seo_results={
            "total_score": 80.0,
            "scores": {},
            "risk": {"parasitic_content_flag": True},
            "eeat": {"is_ymyl": False},
        },
        aio_results={
            "total_score": 70.0,
            "scores": {"eeat": {"score": 6.0}},
            "immediate_actions": [],
        },
        ctx=ScoreContext(intent="informational", industry="B2B SaaS", url_type="企業"),
    )

    assert result["aio_score_before_penalty"] == 84.0
    assert round(result["aio_score"], 1) == 71.4
    assert result["applied_penalties"] == ["ドメインテーマと内容の乖離が大きいため軽減点（内部ヒューリスティック 0.85x）"]
