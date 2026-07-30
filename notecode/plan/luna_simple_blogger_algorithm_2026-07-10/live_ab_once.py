from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI


MODEL = "gpt-5.6-luna"
EFFORT = "low"
SEND_CAP = 3
PACKAGE = Path(__file__).resolve().parent
WORKSPACE = PACKAGE.parents[1]
SOURCE_PATH = WORKSPACE / "logs/0624/route_v_company_intro_reader_inference_contract_sanrei_one_article_api_validation_after_diagnosis_20260624_204407/route_b_artifacts/01_sanrei_foods/selected_source_excerpts.json"
OUT = PACKAGE / "artifacts/live_ab_once"
ROLE_ID = "company_side_blogger_v1"
ROLE = "この会社の仕事に日々触れているブロガーとして、偶然来たまだ関心の薄い読者へ書く。会社を外から評さず、sourceの具体的な場面・名詞・動作から興味を立ち上げ、事実を足さない。"


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def compact_ledger() -> list[dict]:
    data = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    ledger = []
    for item in data:
        text = " ".join(str(item.get("text", "")).split())
        ledger.append({"claim_ids": item.get("claim_ids", []), "section_ids": item.get("section_ids", []), "text": text[:2600]})
    return ledger


def stage1_prompt(ledger: list[dict]) -> str:
    facts = "\n\n".join(f"[claims {','.join(x['claim_ids'])}] {x['text']}" for x in ledger)
    return f"""role_id: {ROLE_ID}
あなたは{ROLE}

source ledger（ここだけを事実の根拠にする）:
{facts}

書く条件:
- sourceにある食品、地域、仕事、展示会、商品、動作のどれか具体的な場面から始める
- 自社本人の声を保ち、外部レビューや検索結果の説明口調にしない
- 抽象的な読者誘導、判断軸、判断材料、第一歩、はじめの一歩、効く、過剰な確認・整理を避ける
- sourceにない数値、日付、成果、感情、顧客評価、比較優位を足さない
- Markdownでタイトルは#を1つ、本文は適切な##を使い、記事本文だけを返す
- 1200〜1600字程度を目安にするが、事実を水増ししない
"""


def stage2_prompt(ledger: list[dict], draft: str) -> str:
    facts = "\n\n".join(f"[claims {','.join(x['claim_ids'])}] {x['text']}" for x in ledger)
    return f"""role_id: {ROLE_ID}
あなたは{ROLE}

同じ書き手として、以下の初稿を一度だけ読み直す。
source ledger:
{facts}

初稿:
{draft}

見るのは次の4点だけ:
1. 偶然来た低関心の読者が続きを読みたくなる具体的な入口があるか
2. 自社本人の声が外部説明へずれていないか
3. 見出し・段落・引用の切替後も省略主語を一意に復元できるか
4. source固有の場面・名詞・動作が定型的なメタ文に置き換わっていないか

問題がある段落だけと隣接1文までを書き直し、他の段落、事実、H1/H2順を保つ。問題がなければ初稿をそのまま返す。部分出力ではなく、記事全文だけを返す。新しい事実は足さない。
"""


def call(client: OpenAI, prompt: str, label: str) -> dict:
    started = time.perf_counter()
    response = client.responses.create(model=MODEL, reasoning={"effort": EFFORT}, input=prompt, max_output_tokens=5000)
    elapsed = round(time.perf_counter() - started, 3)
    text = response.output_text
    usage = getattr(response, "usage", None)
    usage_data = usage.model_dump() if usage is not None and hasattr(usage, "model_dump") else str(usage)
    return {"label": label, "elapsed_seconds": elapsed, "output_text": text, "usage": usage_data, "response_id": getattr(response, "id", None)}


def main() -> int:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing")
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(SOURCE_PATH)
    ledger = compact_ledger()
    preflight = {"model": MODEL, "reasoning_effort": EFFORT, "send_cap": SEND_CAP, "source_path": str(SOURCE_PATH), "excerpt_count": len(ledger), "ledger": ledger, "route_v_connected": False, "raw_full_source_handoff": False, "retry": False}
    OUT.mkdir(parents=True, exist_ok=True)
    dump(OUT / "preflight.json", preflight)
    client = OpenAI()
    sends = []
    try:
        p_a = stage1_prompt(ledger)
        (OUT / "arm_a_prompt.txt").write_text(p_a, encoding="utf-8")
        result_a = call(client, p_a, "A")
        sends.append(result_a)
        dump(OUT / "arm_a_response.json", result_a)
        (OUT / "arm_a_article.md").write_text(result_a["output_text"], encoding="utf-8")
        if not result_a["output_text"].strip():
            raise RuntimeError("Arm A returned empty output")

        p_b1 = stage1_prompt(ledger)
        (OUT / "arm_b_stage1_prompt.txt").write_text(p_b1, encoding="utf-8")
        result_b1 = call(client, p_b1, "B1")
        sends.append(result_b1)
        dump(OUT / "arm_b_stage1_response.json", result_b1)
        (OUT / "arm_b_stage1_article.md").write_text(result_b1["output_text"], encoding="utf-8")
        if not result_b1["output_text"].strip():
            raise RuntimeError("Arm B stage 1 returned empty output")

        p_b2 = stage2_prompt(ledger, result_b1["output_text"])
        (OUT / "arm_b_stage2_prompt.txt").write_text(p_b2, encoding="utf-8")
        result_b2 = call(client, p_b2, "B2")
        sends.append(result_b2)
        dump(OUT / "arm_b_stage2_response.json", result_b2)
        (OUT / "arm_b_article.md").write_text(result_b2["output_text"], encoding="utf-8")
        if not result_b2["output_text"].strip():
            raise RuntimeError("Arm B stage 2 returned empty output")
    except Exception as exc:
        dump(OUT / "failure.json", {"error_type": type(exc).__name__, "error": str(exc), "sends_completed": [x["label"] for x in sends]})
        dump(OUT / "send_manifest.json", {"model": MODEL, "reasoning_effort": EFFORT, "send_count": len(sends), "cap": SEND_CAP, "labels": [x["label"] for x in sends], "status": "failed"})
        return 1
    dump(OUT / "send_manifest.json", {"model": MODEL, "reasoning_effort": EFFORT, "send_count": len(sends), "cap": SEND_CAP, "labels": [x["label"] for x in sends], "status": "completed", "retry": False})
    return 0


if __name__ == "__main__":
    sys.exit(main())
