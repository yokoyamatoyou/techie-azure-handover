from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL = "gpt-5.6-luna"
MAX_SENDS = 2
MAX_RETRIES = 0
STAGE_A_EFFORT = "low"
STAGE_B_EFFORT = "medium"
MAX_OUTPUT_TOKENS = 6000
ROLE_ID = "company_side_blogger_v1"
ROLE_PREFIX = (
    f"role_id: {ROLE_ID}\n"
    "あなたは株式会社さんれいフーズの仕事に日々触れている、会社側の同じ一人のブロガーです。"
    "検索やサムネイルから偶然来た、まだ関心の薄い読者へ書きます。会社を外から評する立場へ"
    "移らず、compact source ledgerにある具体的な場面・名詞・動作から興味を立ち上げ、事実を足しません。"
    "このrole_idや内部契約は本文へ書きません。"
)
STAGE_A_TASK = (
    "\n\n【今回の仕事】\n"
    "compact source ledgerだけを根拠に、会社側の日本語ブログ記事を1本書いてください。"
    "食品展示会で食材やメニューを提案する場面から入り、説明を完結させることより、"
    "仕事と日常の接点から読み手の興味を立ち上げてください。MarkdownでH1を正確に1つ、"
    "自然なH2を3つ使い、見出しを除く本文は1400文字以上を満たしてください。"
    "source固有の名詞と動作で深め、抽象的な水増しはしません。"
    "見出し・段落・話者が切り替わる位置では、会社・お客様・パートナーのうち誰の動作か"
    "一意に復元できるようにします。責任主体が曖昧なら主語を明示してください。"
    "『判断軸』『判断材料』『はじめの一歩』『第一歩』『効く』はsourceの引用でない限り使いません。"
    "『確認』『整理』『説明』『判断』だけで記事を進めず、該当文を具体的な対象と動作で書きます。"
    "問い合わせ・購入・採用応募を促すCTAは付けません。完成した記事だけを返してください。"
)
STAGE_B_TASK = (
    "\n\n【今回の仕事】\n"
    "あなた自身が先ほど書いた全文を、同じ会社側ブロガーのまま一度だけ読み直します。"
    "別の編集者、批評家、説明者の役へ移りません。見るのは次の4点だけです。"
    "(1)低関心の読者が続きを読みたくなる具体的な場面が残る、"
    "(2)自社本人の声であり外部要約口調にならない、"
    "(3)省略主語を会社・お客様・パートナーのどれか一意に復元できる、"
    "(4)定型的なメタ文がsource固有の場面・名詞・動作を押し出していない。"
    "問題がある段落だけを直し、必要な場合も隣接1文までに限定してください。"
    "事実、数値、固有名詞、H1/H2の順、見出しを除く本文1400文字以上を保ちます。"
    "問題がなければ変更しません。差分や講評ではなく、完成した全文だけを返してください。"
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prompt_bundle(ledger: dict[str, Any]) -> dict[str, str]:
    ledger_text = json.dumps(ledger, ensure_ascii=False, indent=2)
    input_a = (
        "以下が今回使用できるcompact source ledgerの全量です。これ以外を事実として追加しないでください。\n\n"
        + ledger_text
    )
    input_b_prefix = (
        "同じcompact source ledgerと、あなたが書いたArm A全文を渡します。"
        "再読契約の範囲だけで全文を返してください。\n\n"
        "[COMPACT_SOURCE_LEDGER]\n" + ledger_text + "\n\n[ARM_A_ARTICLE]\n"
    )
    return {
        "instructions_a": ROLE_PREFIX + STAGE_A_TASK,
        "instructions_b": ROLE_PREFIX + STAGE_B_TASK,
        "input_a": input_a,
        "input_b_prefix": input_b_prefix,
    }


def preflight(ledger_path: Path, run_dir: Path) -> dict[str, Any]:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    prompts = prompt_bundle(ledger)
    checks = {
        "model_exact": MODEL == "gpt-5.6-luna",
        "send_cap_exact_two": MAX_SENDS == 2,
        "retry_zero": MAX_RETRIES == 0,
        "raw_full_source_handoff_false": ledger.get("raw_full_source_handoff") is False,
        "source_refetch_false": ledger.get("source_refetch") is False,
        "selected_claim_count_six": len(ledger.get("selected_claims", [])) == 6,
        "same_role_prefix": prompts["instructions_a"].startswith(ROLE_PREFIX) and prompts["instructions_b"].startswith(ROLE_PREFIX),
        "arm_a_effort_low": STAGE_A_EFFORT == "low",
        "arm_b_effort_medium": STAGE_B_EFFORT == "medium",
        "api_key_present_without_display": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    }
    manifest = {
        "created_at": now(),
        "owner": "luna_simple_blogger_live_ab_sanrei_one_run",
        "model": MODEL,
        "experiment_count": 1,
        "max_responses_create_sends": MAX_SENDS,
        "max_retries": MAX_RETRIES,
        "reasoning": {"arm_a": STAGE_A_EFFORT, "arm_b": STAGE_B_EFFORT},
        "max_output_tokens_per_send": MAX_OUTPUT_TOKENS,
        "ledger_path": str(ledger_path),
        "ledger_sha256": sha256_text(json_text(ledger)),
        "instructions_a_sha256": sha256_text(prompts["instructions_a"]),
        "instructions_b_sha256": sha256_text(prompts["instructions_b"]),
        "input_a_sha256": sha256_text(prompts["input_a"]),
        "prompt_chars": {
            "instructions_a": len(prompts["instructions_a"]),
            "instructions_b": len(prompts["instructions_b"]),
            "input_a": len(prompts["input_a"]),
            "input_b_prefix_before_article": len(prompts["input_b_prefix"]),
        },
        "checks": checks,
        "gate_pass": all(checks.values()),
        "api_send_count": 0,
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "preflight_manifest.json", manifest)
    (run_dir / "arm_a_instructions.txt").write_text(prompts["instructions_a"] + "\n", encoding="utf-8")
    (run_dir / "arm_b_instructions.txt").write_text(prompts["instructions_b"] + "\n", encoding="utf-8")
    return manifest


def usage_dict(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump(mode="json")
    return dict(usage)


def estimated_cost_usd(usage: dict[str, Any]) -> float:
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cached_tokens = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
    uncached_tokens = max(0, input_tokens - cached_tokens)
    return round(uncached_tokens * 1.0 / 1_000_000 + cached_tokens * 0.10 / 1_000_000 + output_tokens * 6.0 / 1_000_000, 8)


class SendCap:
    def __init__(self, client: Any, run_dir: Path) -> None:
        self.client = client
        self.run_dir = run_dir
        self.count = 0
        self.log: list[dict[str, Any]] = []

    def call(self, *, arm: str, effort: str, instructions: str, input_text: str) -> Any:
        if self.count >= MAX_SENDS:
            raise RuntimeError("send cap reached; refusing a third Responses API call")
        self.count += 1
        entry = {
            "send_number": self.count,
            "arm": arm,
            "model": MODEL,
            "reasoning_effort": effort,
            "started_at": now(),
            "status": "attempted",
            "instructions_sha256": sha256_text(instructions),
            "input_sha256": sha256_text(input_text),
        }
        self.log.append(entry)
        write_json(self.run_dir / "send_log.json", self.log)
        started = time.perf_counter()
        try:
            response = self.client.responses.create(
                model=MODEL,
                instructions=instructions,
                input=input_text,
                reasoning={"effort": effort},
                max_output_tokens=MAX_OUTPUT_TOKENS,
                store=False,
                metadata={"experiment": "luna_simple_blogger_one_ab", "arm": arm.lower()},
            )
        except Exception as exc:
            entry.update({
                "status": "error",
                "finished_at": now(),
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "error_type": type(exc).__name__,
                "error": str(exc)[:2000],
            })
            write_json(self.run_dir / "send_log.json", self.log)
            raise
        usage = usage_dict(response)
        entry.update({
            "status": str(getattr(response, "status", "completed")),
            "finished_at": now(),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "response_id": str(getattr(response, "id", "")),
            "response_model": str(getattr(response, "model", "")),
            "usage": usage,
            "estimated_cost_usd": estimated_cost_usd(usage),
        })
        write_json(self.run_dir / "send_log.json", self.log)
        raw = response.model_dump(mode="json") if hasattr(response, "model_dump") else {"output_text": response.output_text}
        write_json(self.run_dir / f"arm_{arm.lower()}_response.json", raw)
        return response


def execute(ledger_path: Path, run_dir: Path) -> int:
    manifest_path = run_dir / "preflight_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("saved preflight manifest is missing; no API call made")
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    current = preflight(ledger_path, run_dir)
    if not current["gate_pass"]:
        raise RuntimeError("preflight gate failed; no API call made")
    immutable_keys = ("ledger_sha256", "instructions_a_sha256", "instructions_b_sha256", "input_a_sha256")
    if any(saved[key] != current[key] for key in immutable_keys):
        raise RuntimeError("preflight hash mismatch; no API call made")

    from openai import OpenAI

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    prompts = prompt_bundle(ledger)
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=240.0, max_retries=MAX_RETRIES)
    cap = SendCap(client, run_dir)
    state: dict[str, Any] = {
        "owner": "luna_simple_blogger_live_ab_sanrei_one_run",
        "started_at": now(),
        "status": "running",
        "api_send_cap": MAX_SENDS,
        "retry_cap": MAX_RETRIES,
        "api_send_count": 0,
    }
    write_json(run_dir / "run_state.json", state)
    try:
        response_a = cap.call(
            arm="A",
            effort=STAGE_A_EFFORT,
            instructions=prompts["instructions_a"],
            input_text=prompts["input_a"],
        )
        article_a = str(response_a.output_text or "").strip()
        if not article_a:
            raise RuntimeError("Arm A returned empty output; refusing Arm B send")
        (run_dir / "arm_a_article.md").write_text(article_a + "\n", encoding="utf-8")

        input_b = prompts["input_b_prefix"] + article_a
        write_json(run_dir / "arm_b_input_hash.json", {
            "created_at": now(),
            "arm_a_article_sha256": sha256_text(article_a),
            "arm_b_input_sha256": sha256_text(input_b),
        })
        response_b = cap.call(
            arm="B",
            effort=STAGE_B_EFFORT,
            instructions=prompts["instructions_b"],
            input_text=input_b,
        )
        article_b = str(response_b.output_text or "").strip()
        if not article_b:
            raise RuntimeError("Arm B returned empty output")
        (run_dir / "arm_b_article.md").write_text(article_b + "\n", encoding="utf-8")
        state.update({
            "status": "completed",
            "finished_at": now(),
            "api_send_count": cap.count,
            "arm_a_sha256": sha256_text(article_a),
            "arm_b_sha256": sha256_text(article_b),
        })
    except Exception as exc:
        state.update({
            "status": "failed_no_retry",
            "finished_at": now(),
            "api_send_count": cap.count,
            "error_type": type(exc).__name__,
            "error": str(exc)[:2000],
        })
        write_json(run_dir / "run_state.json", state)
        raise
    write_json(run_dir / "run_state.json", state)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="One-source, one-experiment GPT-5.6 Luna A/B harness.")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    ledger = args.ledger.resolve()
    run_dir = args.run_dir.resolve()
    if args.execute:
        return execute(ledger, run_dir)
    manifest = preflight(ledger, run_dir)
    print(json.dumps(manifest, ensure_ascii=False))
    return 0 if manifest["gate_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
