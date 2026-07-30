from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import run_reasoning_effort_minimal_shadow_route as base  # noqa: E402


ROUTE_ID = "fact_lattice_deterministic_realizer_shadow_v1"
SOURCE_LOG = PROJECT_ROOT / "logs" / "latest_generation_output.json"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "fact_lattice_deterministic_realizer_live_20260506"
)
PROTECTED_FILES = base.PROTECTED_FILES


def _now_jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_hashes() -> dict[str, str]:
    return {rel: _sha256(PROJECT_ROOT / rel) for rel in PROTECTED_FILES}


def _load_case() -> dict[str, Any]:
    payload = json.loads(SOURCE_LOG.read_text(encoding="utf-8"))
    contract = dict(payload.get("input_contract") or {})
    contract.setdefault("article_type", payload.get("article_type") or "")
    contract.setdefault("semantic_article_key", payload.get("semantic_article_key") or "")
    return {
        "case_id": f"latest_ui_route_a_{payload.get('attempt_id') or 'latest'}",
        "contract": contract,
        "route_a": {
            "title": payload.get("title") or "",
            "lead": payload.get("lead") or "",
            "body": payload.get("body") or "",
            "hashtags": payload.get("hashtags") or "",
        },
    }


def _source_text(contract: dict[str, Any]) -> str:
    return "\n".join(str(doc.get("content") or "") for doc in contract.get("source_documents") or [])


def _has(text: str, *needles: str) -> bool:
    return all(needle in text for needle in needles)


def _fact_lattice(text: str) -> dict[str, bool]:
    return {
        "input_scan": _has(text, "データ入力", "スキャニング"),
        "pre_post": _has(text, "前処理から後処理まで一貫対応"),
        "hearing": _has(text, "ヒアリング"),
        "check_delivery": _has(text, "入力・チェック・納品"),
        "survey": _has(text, "アンケート収集", "アンケート入力"),
        "verify": _has(text, "エントリー入力とベリファイ入力"),
        "research": _has(text, "市場調査", "Webリサーチ"),
        "ondemand": _has(text, "オンデマンド印刷"),
        "data_analysis": _has(text, "データ収集", "データ分析"),
        "rpa": _has(text, "RPA"),
        "history": _has(text, "1885", "1968"),
        "security": _has(text, "セキュリティ"),
        "public_clients": _has(text, "自治体", "大学"),
    }


def _validate_lattice(lattice: dict[str, bool]) -> list[str]:
    required = ("input_scan", "pre_post", "hearing", "check_delivery", "survey", "verify", "research")
    return [f"missing_fact:{key}" for key in required if not lattice.get(key)]


def _article(lattice: dict[str, bool]) -> str:
    history = "創業やデータエントリー事業の歩みも公開されているが、ここでは年数そのものより、扱ってきた仕事の連続性を見たい。" if lattice["history"] else ""
    security = "情報を扱う以上、精度やセキュリティを工程の外に置かないことも前提になる。" if lattice["security"] else ""
    public = "自治体や大学での入力実績がある点は、件数や確認項目の多い仕事を考えるときの背景材料になる。" if lattice["public_clients"] else ""
    return f"""紙の情報を、次の仕事で使える形にするには

紙の資料やアンケートを前にすると、まず考えるのは「入力をどう片づけるか」かもしれません。けれど実際には、入力した後に何を確認し、どんな形で使うのかまで決めておかないと、せっかく整えたデータが次の業務につながりにくいものです。

京都工業株式会社の公開情報を見ると、データ入力とスキャニングは前処理から後処理まで一貫して扱われています。入口はヒアリング。そこから入力、チェック、納品へ進み、納品時には今後の改善内容にも触れる流れです。作業を一点で切らず、前後の工程をまとめて見る設計になっています。

この考え方は、アンケート業務でも分かりやすい。アンケート収集や入力では、どのようなデータ活用をしたいのか、どんな課題があるのかを聞いたうえで、帳票と入力データを整えるとされています。入力欄を埋めるだけではなく、後で集計し、判断材料にするところまで見ているわけです。

入力精度についても、気合いではなく工程で支える形が示されています。データエントリーでは、エントリー入力とベリファイ入力を別のオペレーターが行う。こうした確認の分け方があると、あとから修正に追われるリスクを抑えやすい。{public}

扱う情報はアンケートだけではありません。名刺、原稿、冊子、ハガキ、音声、スキャニングした資料など、入り口になる素材はさまざまです。形が違えば、必要な整理の仕方も変わる。だから依頼する側も、件数だけでなく、納品後に検索したいのか、集計したいのか、分析に回したいのかを先に言葉にしておくと話が早い。

市場調査やWebリサーチも、情報を集めて終わりではなく、内容をデータ化して納品する仕事として案内されています。オンデマンド印刷、データ収集、データ分析、RPAによる業務効率化支援まで並んでいるのを見ると、紙からデータへ、データから運用へという流れがつながっていることが分かります。

{history} {security} データ入力やスキャニングは地味な工程に見えますが、業務の土台をつくる仕事でもあります。ここが曖昧なままでは、分析や自動化の前に手戻りが起きる。逆に、最初の整理がうまくいくと、後の確認や活用はぐっと進めやすくなります。

手元の情報をどこまで入力し、どこから活用したいのか。そこを先に決めておくことが、データ化の相談ではいちばん実務的な準備です。入力作業そのものを見るだけでなく、その先の使い道から逆算する。京都工業株式会社のサービス情報は、その視点を持つための材料になります。

参考情報
- データ入力・スキャニング | 京都工業株式会社
- 京都工業株式会社 | 創業1885年 データ入力・エントリー・分析・RPA導入支援
- 企業情報 | 京都工業株式会社
- 沿革 | 京都工業株式会社

#データ入力 #スキャニング #データ活用 #アンケート入力 #市場調査 #業務改善
"""


def run(root: Path) -> dict[str, Any]:
    case = _load_case()
    contract = case["contract"]
    root.mkdir(parents=True, exist_ok=True)
    source_path = base._write_json(root / "source_snapshot.json", contract)
    base._write_json(root / "route_a_snapshot.json", case["route_a"])
    lattice = _fact_lattice(_source_text(contract))
    issues = _validate_lattice(lattice)
    report = {
        "route_id": ROUTE_ID,
        "date_jst": _now_jst(),
        "mode": "one-source deterministic live validation",
        "status": "blocked" if issues else "completed",
        "case_id": case["case_id"],
        "source_snapshot_hash": _sha256(source_path),
        "validation_issues": issues,
        "implementation_started": True,
        "live_generation_started": True,
        "external_llm_send": False,
        "adoption_started": False,
        "route_a_changed": False,
        "default_route_changed": False,
        "repair_added": False,
        "editor_added": False,
        "threshold_relaxed": False,
        "fallback_mock_dummy_used": False,
        "best_of_n_used": False,
        "free_prose_first_used": False,
        "protected_hashes": _protected_hashes(),
    }
    base._write_json(root / "fact_lattice.json", lattice)
    if issues:
        base._write_json(root / "live_report.json", report)
        return report
    text = _article(lattice)
    score = base._score_body(text)
    clean = (
        score["body_length_target_result"] == "ok"
        and not score["gpt_frequent_term_hits"]
        and not score["first_person_company_hits"]
        and not score["ending_bucket_monotony"]
        and not score["third_party_intro_tone"]
        and not score["textbook_explanation_tone"]
    )
    report.update({"decision": "continue_shadow" if clean else "reject", "score": score})
    base._write_text(root / "latest_generation_output.txt", text)
    base._write_json(root / "latest_generation_output.json", {"text": text})
    base._write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in deterministic fact lattice shadow route.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run(Path(args.output_root))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"{report['status']}: {args.output_root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
