from __future__ import annotations

from pathlib import Path
from typing import Any

from app.evals.rubric import diagnose_issue_owners


ROOT = Path(__file__).resolve().parents[2]


def verify_claim_traceability(knowledge_pack: dict[str, Any], article_brief: dict[str, Any]) -> list[str]:
    claims = knowledge_pack["article_knowledge_pack"]["confirmed_facts"]
    known_claim_ids = {claim["claim_id"] for claim in claims}
    problems: list[str] = []
    for section in article_brief["article_brief"]["sections"]:
        for claim_id in section["assigned_claim_ids"]:
            if claim_id not in known_claim_ids:
                problems.append(f"unknown claim_id in section {section['section_id']}: {claim_id}")
    for claim in claims:
        if not claim["supporting_fact_ids"]:
            problems.append(f"claim has no supporting facts: {claim['claim_id']}")
    return problems


def inspect_bloat(paths: list[Path] | None = None) -> dict[str, Any]:
    target_paths = paths or list((ROOT / "app").glob("**/*.py")) + list((ROOT / "app" / "prompts").glob("*.md"))
    files = []
    failures = []
    for path in target_paths:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        relative = str(path.relative_to(ROOT))
        limit = 120 if path.suffix == ".md" else 300
        files.append({"path": relative, "line_count": line_count, "limit": limit})
        if line_count > limit:
            failures.append({"path": relative, "line_count": line_count, "limit": limit})
    return {"files": files, "failures": failures, "pass": not failures}


def create_hardening_report(
    quality_check: dict[str, Any],
    knowledge_pack: dict[str, Any],
    article_brief: dict[str, Any],
) -> dict[str, Any]:
    traceability_problems = verify_claim_traceability(knowledge_pack, article_brief)
    bloat = inspect_bloat()
    return {
        "owner_diagnosis": diagnose_issue_owners(quality_check),
        "traceability_problems": traceability_problems,
        "bloat": bloat,
        "ready_for_quality_tuning": not traceability_problems and bloat["pass"],
    }
