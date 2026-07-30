from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from dotenv import load_dotenv  # noqa: E402
from note.llm_client import LLMClient  # noqa: E402
ROUTE_ID = "angle_claim_card_paragraph_local_shadow_v1"
SOURCE_LOG = PROJECT_ROOT / "logs" / "latest_generation_output.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "logs" / "shadow_autonomous_20260504-233916" / "routes" / "angle_claim_card_preflight_20260505"


BUCKET_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("reader_uncertainty", ("やり方がわからない", "相談したい", "お悩み", "課題", "目的")),
    ("entry_point", ("ヒアリング", "お問い合わせ", "相談", "承ります")),
    ("background_evidence", ("50年以上", "自治体", "大学", "官公庁", "歴史")),
    ("process_boundary", ("前処理", "後処理", "入力・チェック・納品", "入力", "チェック", "納品")),
    ("support_scope", ("市場調査", "Webリサーチ", "オンデマンド印刷", "スキャニング", "RPA", "データ分析")),
    ("brochure_risk", ("価格", "強み", "信頼", "健康経営", "採用", "選ば", "実績")),
    ("current_work", ("データ入力", "データエントリー", "スキャニング", "データ活用")),
)

GPT_TERMS = ("効く", "第一歩", "重要です", "大切です", "と言えるでしょう", "以下では", "まとめると", "いかがでしたか")
PROTECTED_FILES = (
    "note/current_mainline_runner.py",
    "note/newalgorithm_pipeline/pipeline.py",
    "note/simple_note_pipeline/pipeline.py",
    "note/simple_note_pipeline/prompt_builder.py",
    "note/simple_note_pipeline/repair_acceptance.py",
    "note/simple_note_pipeline/quality_guard.py",
)


def _now_jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST")


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _split_fact_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in re.split(r"[\r\n。]+", str(text or "")):
        line = re.sub(r"\s+", " ", raw).strip(" -\t")
        if 10 <= len(line) <= 90 and not re.match(r"^\d", line):
            lines.append(line)
    return lines


def _bucket_fact(text: str) -> str:
    for bucket, needles in BUCKET_PATTERNS:
        if any(needle in text for needle in needles):
            return bucket
    return "current_work"


def _fact_score(text: str, bucket: str) -> int:
    score = min(len(text), 80)
    if any(token in text for token in ("します", "承ります", "対応", "提供", "行います", "相談", "入力・チェック・納品")):
        score += 35
    if any(token in text for token in ("価格", "採用情報", "健康経営", "募集要項", "弊社", "お客様", "信頼", "安心", "モットー")):
        score -= 80
    if any(token in text for token in ("プレゼントキャンペーン", "社内業務", "力強い会社", "RPA事業")):
        score -= 70
    if re.search(r"(から|まで|に|を|と)$", text):
        score -= 45
    if bucket == "brochure_risk":
        score -= 50
    return score


def _load_saved_route_a_source() -> dict[str, Any]:
    payload = json.loads(SOURCE_LOG.read_text(encoding="utf-8"))
    contract = dict(payload.get("input_contract") or {})
    if not contract:
        raise ValueError("latest_generation_output_input_contract_missing")
    contract.setdefault("article_type", payload.get("article_type") or "branding")
    contract.setdefault("semantic_article_key", payload.get("semantic_article_key") or "company_introduction")
    return {
        "case_id": f"latest_ui_route_a_{payload.get('attempt_id') or 'latest'}",
        "attempt_id": payload.get("attempt_id") or "latest",
        "payload": contract,
        "route_a_title": payload.get("title") or "",
        "route_a_lead": payload.get("lead") or "",
        "route_a_body": payload.get("body") or "",
    }


def _extract_atomic_facts(contract: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for doc_index, doc in enumerate(contract.get("source_documents") or [], start=1):
        title = str(doc.get("title") or f"source_{doc_index}")
        for line in _split_fact_lines(str(doc.get("content") or "")):
            if line in seen:
                continue
            seen.add(line)
            bucket = _bucket_fact(line)
            facts.append(
                {
                    "fact_id": f"f{len(facts) + 1:02d}",
                    "text": line,
                    "bucket": bucket,
                    "score": _fact_score(line, bucket),
                    "source_title": title,
                    "brochure_risk": bucket == "brochure_risk",
                }
            )
    return facts


def _first_fact(
    facts: list[dict[str, Any]],
    bucket: str,
    *,
    skip: set[str],
    must_contain: tuple[str, ...] = (),
) -> dict[str, Any] | None:
    candidates = [
        fact
        for fact in facts
        if fact["bucket"] == bucket
        and fact["fact_id"] not in skip
        and (not must_contain or any(token in fact["text"] for token in must_contain))
    ]
    for fact in sorted(candidates, key=lambda item: int(item.get("score") or 0), reverse=True):
        skip.add(fact["fact_id"])
        return fact
    return None


def _make_card(
    card_id: str,
    angle: str,
    claim: str,
    evidence: list[dict[str, Any]],
    *,
    company_name_allowed: str = "when_ambiguous",
    zero_subject_allowed: str = "only_when_previous_sentence_keeps_same_topic",
) -> dict[str, Any]:
    return {
        "card_id": card_id,
        "reader_angle": angle,
        "micro_claim": claim,
        "allowed_evidence": [{"fact_id": item["fact_id"], "text": item["text"], "bucket": item["bucket"]} for item in evidence],
        "brochure_risk_fact_bucket": ["history", "trust", "price", "selected_reasons", "superiority"],
        "referent_policy": {
            "company_is_topic_entity": True,
            "company_name_allowed": company_name_allowed,
            "first_person_company_allowed": False,
            "zero_subject_allowed": zero_subject_allowed,
            "explicit_subject_required_when": ["service_boundary", "actor_switch", "delivery_scope"],
        },
    }


def _build_cards(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    used: set[str] = set()

    def take(*pairs: tuple[str, tuple[str, ...]], reuse: bool = False) -> list[dict[str, Any]]:
        picked: list[dict[str, Any]] = []
        local_skip = set() if reuse else used
        for bucket, needles in pairs:
            fact = _first_fact(facts, bucket, skip=local_skip, must_contain=needles)
            if fact:
                picked.append(fact)
        return picked[:2]

    cards = [
        _make_card(
            "p01",
            "paper or survey data is present, but the first step is unclear",
            "紙やアンケートの情報は、入力だけでなく使える形まで考える必要がある",
            take(("reader_uncertainty", ("お悩み", "課題")), ("process_boundary", ("活用方法", "一貫提案"))),
            company_name_allowed="lead_once_or_when_ambiguous",
        ),
        _make_card(
            "p02",
            "reader wants to know where the work begins",
            "データ入力・エントリ業務はヒアリングから始められる",
            take(("entry_point", ("ヒアリング",)), ("reader_uncertainty", ("どのようなデータ活用",))),
        ),
        _make_card(
            "p03",
            "reader needs the boundary of the support scope",
            "入力、チェック、納品までを一つの流れとして扱える",
            take(("process_boundary", ("入力・チェック・納品",)), ("process_boundary", ("前処理", "後処理"))),
            zero_subject_allowed="after_input_check_delivery_topic_is_established",
        ),
        _make_card(
            "p04",
            "reader compares adjacent work such as research or scanning",
            "市場調査やWebリサーチ、スキャニングも情報を使える形にする周辺作業としてつながる",
            take(("support_scope", ("市場調査", "Webリサーチ")), ("process_boundary", ("データ化して納品",))),
        ),
        _make_card(
            "p05",
            "reader needs background evidence without company brochure tone",
            "自治体や大学での入力実績は、作業を任せる時の背景材料になる",
            take(("background_evidence", ("自治体", "大学")), ("process_boundary", ("入力・チェック・納品",))),
        ),
        _make_card(
            "p06",
            "reader should know what to check next",
            "次に見るべきなのは、手元の情報をどこまで入力し、どこから活用したいかである",
            take(("reader_uncertainty", ("どのようなデータ活用",)), ("process_boundary", ("活用方法", "一貫提案")), reuse=True),
        ),
    ]
    return [card for card in cards if card["allowed_evidence"]]


def _validate_cards(cards: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for card in cards:
        evid = card.get("allowed_evidence") or []
        if not str(card.get("micro_claim") or "").strip():
            issues.append(f"{card.get('card_id')}:missing_micro_claim")
        if not (1 <= len(evid) <= 2):
            issues.append(f"{card.get('card_id')}:allowed_evidence_count_not_1_to_2")
        for item in evid:
            if re.search(r"(から|まで|に|を|と)$", str(item.get("text") or "")):
                issues.append(f"{card.get('card_id')}:fragment_evidence")
        if any(item.get("bucket") == "brochure_risk" for item in evid):
            issues.append(f"{card.get('card_id')}:brochure_risk_evidence_visible_to_writer")
        policy = card.get("referent_policy") or {}
        if policy.get("first_person_company_allowed") is not False:
            issues.append(f"{card.get('card_id')}:first_person_company_not_blocked")
    return issues


def _writer_prompt_for(card: dict[str, Any], previous_paragraph: str = "") -> str:
    evidence_lines = "\n".join(f"- {item['text']}" for item in card["allowed_evidence"])
    return f"""Write the next Japanese blog paragraph.
Use only this card and the previous paragraph.
Do not mention internal labels.
Keep the company as topic entity, not first person.
If the subject is clear from the previous sentence, omission is allowed.
If actor changes or service boundary is described, state the subject.

Reader angle:
{card['reader_angle']}

Micro-claim:
{card['micro_claim']}

Allowed evidence:
{evidence_lines}

Previous paragraph:
{previous_paragraph}
""".strip()


def _protected_hashes() -> dict[str, str]:
    return {rel: _sha256(PROJECT_ROOT / rel) for rel in PROTECTED_FILES}


def _score_body(body: str) -> dict[str, Any]:
    sentences = [s for s in re.split(r"[。！？]", body) if s.strip()]
    endings = [s.strip()[-4:] for s in sentences if s.strip()]
    buckets = ["polite" if e.endswith(("ます", "です", "ました", "でした")) else "other" for e in endings]
    max_run = 0
    run = 0
    prev = ""
    for bucket in buckets:
        run = run + 1 if bucket == prev else 1
        prev = bucket
        max_run = max(max_run, run)
    gpt_hits = [term for term in GPT_TERMS if term in body]
    first_person_hits = [term for term in ("私たち", "自社", "弊社") if term in body]
    return {
        "body_char_count": len(body),
        "gpt_frequent_term_hits": gpt_hits, "first_person_company_hits": first_person_hits,
        "ending_bucket_max_run": max_run, "ending_bucket_monotony": max_run >= 7,
        "body_length_target_result": "ok" if 1400 <= len(body) <= 2400 else ("short" if len(body) < 1400 else "long"),
        "third_party_intro_tone": any(x in body for x in ("について紹介", "強み", "選ばれて", "信頼されています")),
        "textbook_explanation_tone": any(x in body for x in ("重要です", "大切です", "ポイントです")),
    }


def run_preflight(root: Path) -> dict[str, Any]:
    case = _load_saved_route_a_source()
    contract = dict(case["payload"])
    if contract.get("article_type") != "branding" or contract.get("semantic_article_key") != "company_introduction":
        raise ValueError("angle_claim_card_requires_saved_branding_company_introduction")
    facts = _extract_atomic_facts(contract)
    cards = _build_cards(facts)
    issues = _validate_cards(cards)
    status = "ready_for_live_approval" if cards and not issues else "blocked"
    source_path = _write_json(root / "source_snapshot.json", contract)
    _write_json(root / "atomic_facts.json", facts)
    _write_json(root / "claim_cards.json", cards)
    _write_json(root / "writer_prompts_preview.json", {card["card_id"]: _writer_prompt_for(card) for card in cards})
    report = {
        "route_id": ROUTE_ID,
        "date_jst": _now_jst(),
        "mode": "local preflight only; no LLM send",
        "status": status,
        "case_id": case["case_id"],
        "source_snapshot_hash": _sha256(source_path),
        "fact_count": len(facts),
        "card_count": len(cards),
        "validation_issues": issues,
        "implementation_started": True,
        "live_generation_started": False,
        "adoption_started": False,
        "route_a_changed": False,
        "default_route_changed": False,
        "repair_added": False,
        "threshold_relaxed": False,
        "fallback_mock_dummy_used": False,
        "gpt_terms_scorer_terms": list(GPT_TERMS),
        "protected_hashes": _protected_hashes(),
    }
    _write_json(root / "plan_audit.json", report)
    _write_text(
        root / "blocked_or_ready.md",
        "\n".join(
            [
                "# angle claim card preflight",
                "",
                f"- status: `{status}`",
                f"- route_id: `{ROUTE_ID}`",
                f"- case_id: `{case['case_id']}`",
                f"- fact_count: `{len(facts)}`",
                f"- card_count: `{len(cards)}`",
                f"- validation_issues: `{', '.join(issues) if issues else 'none'}`",
                "- live_generation_started: `false`",
                "- next: request explicit approval for one saved-source live validation only",
            ]
        )
        + "\n",
    )
    return report


def run_live(root: Path) -> dict[str, Any]:
    report = run_preflight(root)
    if report["status"] == "blocked":
        return report
    cards = json.loads((root / "claim_cards.json").read_text(encoding="utf-8"))
    load_dotenv(PROJECT_ROOT / ".env")
    try:
        llm = LLMClient()
    except Exception as exc:
        report.update({"status": "blocked", "blocked_reason": str(exc), "live_generation_started": False})
        _write_json(root / "live_report.json", report)
        return report
    paragraphs: list[str] = []
    prompts: dict[str, str] = {}
    metadata: dict[str, Any] = {}
    try:
        for card in cards:
            prompt = _writer_prompt_for(card, "\n\n".join(paragraphs[-1:]))
            prompts[card["card_id"]] = prompt
            raw = llm.generate_text(prompt, max_tokens=900, task_type="section", article_type="branding", verbosity="medium")
            para = re.sub(r"^```(?:markdown|md|text)?\s*|\s*```$", "", str(raw).strip())
            para = re.sub(r"\n{2,}", "\n", para).strip()
            if not para:
                raise RuntimeError(f"{card['card_id']}:empty_paragraph")
            paragraphs.append(para)
            metadata[card["card_id"]] = dict(llm.get_last_call_metadata())
    except Exception as exc:
        report.update({"status": "blocked", "blocked_reason": str(exc), "live_generation_started": True})
        _write_json(root / "writer_prompts_live.json", prompts); _write_json(root / "live_report.json", report)
        return report
    body = "\n\n".join(paragraphs)
    result = {
        "title": "データ入力の前後まで見て、使える形を考える",
        "lead": "紙やアンケートの情報を扱うときは、入力作業だけでなく、その先の使い方まで見ておくと進め方を決めやすくなります。",
        "body": body,
        "hashtags": "#データ入力 #スキャニング #データ活用",
    }
    score = _score_body(body)
    clean = (
        score["body_length_target_result"] == "ok"
        and not score["gpt_frequent_term_hits"]
        and not score["first_person_company_hits"]
        and not score["ending_bucket_monotony"]
        and not score["third_party_intro_tone"]
        and not score["textbook_explanation_tone"]
    )
    report.update({"status": "completed", "live_generation_started": True, "paragraph_generation_call_count": len(paragraphs), "repair_call_executed": False, "shadow_editor_call_executed": False, "fallback_mock_dummy_used": False, "decision": "continue_shadow" if clean else "reject", "score": score})
    _write_json(root / "writer_prompts_live.json", prompts); _write_json(root / "model_metadata.json", metadata); _write_json(root / "latest_generation_output.json", result)
    _write_text(root / "latest_generation_output.txt", f"{result['title']}\n\n{result['lead']}\n\n{body}\n\n{result['hashtags']}\n")
    _write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build angle-first claim cards for the saved UI Route A source.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--live", action="store_true", help="Run the approved one-source live validation.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_live(Path(args.output_root)) if args.live else run_preflight(Path(args.output_root))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status']}: {args.output_root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
