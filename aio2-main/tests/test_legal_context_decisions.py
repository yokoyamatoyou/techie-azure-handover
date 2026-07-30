from types import SimpleNamespace

import pytest

import core.engine.orchestrator as orchestrator
from core.engine.orchestrator import SEOAIOAnalyzer
from core.application.markdown_report_service import build_detailed_markdown_report
from core.evidence_pipeline import aggregate_legal_check_results


class _Tracker:
    def __init__(self):
        self.calls = []

    def add_usage(self, *args):
        self.calls.append(args)


def _analyzer(*, client=None):
    analyzer = object.__new__(SEOAIOAnalyzer)
    analyzer.client = client
    analyzer.token_tracker = _Tracker()
    return analyzer


def _legal_checks(*issues):
    return {
        "premiums_labeling": {
            "raw": {
                "issues": list(issues),
                "risk_level": "high",
                "risk_score": 20,
                "summary": {},
                "recommendations": [],
            }
        }
    }


def test_operational_phrase_is_safe_and_not_scored():
    analyzer = _analyzer()
    result = analyzer._apply_legal_context_adjustment(
        legal_checks=_legal_checks({
            "matched_text": "完全",
            "evidence": "WEBによる完全予約制です。",
            "location": "本文内",
            "risk_level": "high_risk",
            "severity": "high",
        }),
        title="予約案内",
        meta_description="",
        h1="",
    )
    issue = result["premiums_labeling"]["raw"]["issues"][0]
    assert issue["legal_decision"] == "safe_context"
    assert result["premiums_labeling"]["raw"]["risk_score"] == 0
    assert result["premiums_labeling"]["formatted"]["items"] == []


def test_clear_guarantee_remains_action_required():
    analyzer = _analyzer()
    result = analyzer._apply_legal_context_adjustment(
        legal_checks=_legal_checks({
            "matched_text": "完全",
            "evidence": "完全に治ります。",
            "risk_level": "high_risk",
            "severity": "high",
        }),
        title="治療",
        meta_description="",
        h1="",
    )
    issue = result["premiums_labeling"]["raw"]["issues"][0]
    assert issue["legal_decision"] == "action_required"
    assert result["premiums_labeling"]["raw"]["risk_score"] == 20
    assert result["premiums_labeling"]["formatted"]["items"]


def test_double_negative_is_review_without_score_penalty():
    analyzer = _analyzer()
    result = analyzer._apply_legal_context_adjustment(
        legal_checks=_legal_checks({
            "matched_text": "絶対",
            "evidence": "絶対に効かないわけではない。",
            "risk_level": "high_risk",
            "severity": "high",
        }),
        title="説明",
        meta_description="",
        h1="",
    )
    issue = result["premiums_labeling"]["raw"]["issues"][0]
    assert issue["legal_decision"] == "review_needed"
    assert result["premiums_labeling"]["raw"]["risk_score"] == 0
    assert result["premiums_labeling"]["formatted"]["items"] == []


def test_ambiguous_candidates_are_batched_once(monkeypatch):
    analyzer = _analyzer(client=object())
    calls = []

    def fake_call(*args, **kwargs):
        calls.append(kwargs)
        return (
            {
                "judgements": [
                    {
                        "candidate_id": "c1",
                        "claim_target": "効果",
                        "polarity": "不明",
                        "usage_type": "その他",
                        "decision": "review_needed",
                        "reason": "前後文が不足しています。",
                        "confidence": 0.4,
                    }
                ]
            },
            SimpleNamespace(usage=SimpleNamespace(input_tokens=10, output_tokens=10)),
        )

    monkeypatch.setattr(orchestrator, "call_structured", fake_call)
    result = analyzer._apply_legal_context_adjustment(
        legal_checks=_legal_checks({
            "matched_text": "完全",
            "evidence": "完全な対応を目指します。",
            "risk_level": "high_risk",
            "severity": "high",
        }),
        title="案内",
        meta_description="",
        h1="",
    )
    assert len(calls) == 1
    assert result["premiums_labeling"]["raw"]["issues"][0]["legal_decision"] == "review_needed"


def test_batch_failure_is_fail_closed(monkeypatch):
    analyzer = _analyzer(client=object())

    def failing_call(*args, **kwargs):
        raise RuntimeError("timeout")

    monkeypatch.setattr(orchestrator, "call_structured", failing_call)
    result = analyzer._apply_legal_context_adjustment(
        legal_checks=_legal_checks({
            "matched_text": "絶対",
            "evidence": "絶対的な価値を目指します。",
            "risk_level": "high_risk",
            "severity": "high",
        }),
        title="案内",
        meta_description="",
        h1="",
    )
    issue = result["premiums_labeling"]["raw"]["issues"][0]
    assert issue["legal_decision"] == "review_needed"
    assert result["premiums_labeling"]["raw"]["risk_score"] == 0


def test_safe_context_is_not_aggregated_but_review_is_available_to_engineers():
    aggregated = aggregate_legal_check_results({
        "premiums_labeling": {
            "raw": {
                "issues": [
                    {"matched_text": "完全", "category": "優良誤認", "severity": "info", "legal_decision": "safe_context"},
                    {"matched_text": "絶対", "category": "優良誤認", "severity": "info", "legal_decision": "review_needed", "evidence": "絶対に効かないわけではない"},
                ]
            }
        }
    })
    clusters = aggregated["aggregated_issues"]
    assert all((c.get("representative") or {}).get("legal_decision") != "safe_context" for c in clusters)
    assert any((c.get("representative") or {}).get("legal_decision") == "review_needed" for c in clusters)


def test_markdown_keeps_review_context_in_engineer_section():
    markdown = build_detailed_markdown_report({
        "run": {"id": 999, "url": "https://example.test"},
        "snapshot": {"meta": {"run_id": 999, "url": "https://example.test"}},
        "result": {
            "legal_checks": {
                "premiums_labeling": {
                    "raw": {
                        "issues": [{
                            "matched_text": "絶対",
                            "evidence": "絶対に効かないわけではない",
                            "legal_decision": "review_needed",
                            "context_note": "二重否定の確認が必要",
                            "context_judgement": {"model": "gpt-5.4-nano", "reasoning_effort": "low"},
                        }]
                    }
                }
            }
        },
    })
    assert "法務文脈判定（実装担当向け）" in markdown
    assert "絶対に効かないわけではない" in markdown


@pytest.mark.parametrize(
    ("evidence", "expected"),
    [
        ("完全個室をご用意しています。", "safe_context"),
        ("正解や絶対がない領域です。", "safe_context"),
        ("絶対ではないことをご理解ください。", "safe_context"),
        ("効果を保証しない案内です。", "safe_context"),
        ("完全に治ると断言します。", "action_required"),
        ("絶対に安全です。", "action_required"),
        ("100%成功します。", "action_required"),
    ],
)
def test_representative_broad_phrases_follow_context_contract(evidence, expected):
    analyzer = _analyzer()
    matched_text = "100%" if "100%" in evidence else ("絶対" if "絶対" in evidence else "完全")
    result = analyzer._apply_legal_context_adjustment(
        legal_checks=_legal_checks({
            "matched_text": matched_text,
            "evidence": evidence,
            "risk_level": "high_risk",
            "severity": "high",
        }),
        title="文脈テスト",
        meta_description="",
        h1="",
    )
    assert result["premiums_labeling"]["raw"]["issues"][0]["legal_decision"] == expected
