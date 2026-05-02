"""診断スクリプト: パイプライン動作状況・設定・アウトライン解析を一括チェック。

使い方:
  cd C:\tetie\notecode
  .venv\Scripts\python.exe diagnose_pipeline.py
  .venv\Scripts\python.exe diagnose_pipeline.py --outline "LLMの生応答テキスト"
  .venv\Scripts\python.exe diagnose_pipeline.py --log          # 直近ログからフォールバック検出
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ── プロジェクトルートを sys.path に追加 ──
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

SEP = "=" * 60


def _load_config() -> dict:
    cfg_path = PROJECT_ROOT / "config.json"
    if not cfg_path.exists():
        return {}
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
# 1. 設定チェック
# ──────────────────────────────────────────────
def check_config(cfg: dict) -> list[str]:
    issues: list[str] = []

    # generation_mode
    gen_mode = cfg.get("generation_mode", "legacy")
    print(f"  generation_mode          : {gen_mode}")
    if gen_mode == "hlcv2":
        issues.append(
            "[WARN] generation_mode=hlcv2 → Resonance Phase 1-4"
            " (共感/興味/人間味/リズム) がスキップされます"
        )

    resonance_phases = [
        "phase0_persona",
        "phase1_empathy",
        "phase2_curiosity",
        "phase3_humanity",
        "phase4_rhythm",
        "phase5_editor",
        "phase6_legal",
        "phase7_sanitize",
    ]
    if gen_mode == "hlcv2":
        resonance_phases = [
            "phase0_persona",
            "phase5_editor",
            "phase6_legal",
            "phase7_sanitize",
        ]
    print(f"  resonance.effective      : {', '.join(resonance_phases)}")

    # quality_pipeline
    qp = cfg.get("quality_pipeline", {})
    qp_enabled = qp.get("enabled", False)
    qp_mode = qp.get("mode", "off")
    print(f"  quality_pipeline.enabled : {qp_enabled}")
    print(f"  quality_pipeline.mode    : {qp_mode}")
    if not qp_enabled:
        issues.append("[WARN] quality_pipeline が無効です")
    elif qp_mode == "shadow":
        issues.append(
            "[WARN] quality_pipeline.mode=shadow → 計測のみ。"
            " Burstiness調整等の書き換えは記事に反映されません"
        )
    elif qp_mode == "off":
        issues.append("[WARN] quality_pipeline.mode=off → 完全無効")

    # 各Phase有効/無効
    phase_keys = [
        ("phase01_lexical_enabled", "Phase01 語彙多様性"),
        ("phase02_burstiness_enabled", "Phase02 Burstiness"),
        ("phase03_nominalization_enabled", "Phase03 名詞化"),
        ("phase04_style_drift_enabled", "Phase04 文体ドリフト"),
        ("phase05_layout_guard_enabled", "Phase05 レイアウト"),
        ("phase06_orchestrator_enabled", "Phase06 オーケストレータ"),
        ("phase07_rollout_enabled", "Phase07 ロールアウト"),
    ]
    for key, label in phase_keys:
        val = qp.get(key, False)
        status = "ON" if val else "OFF"
        print(f"    {label:24s}: {status}")
        if not val:
            issues.append(f"[INFO] {label} ({key}) が無効")

    # resonance_tuning
    rt = qp.get("resonance_tuning_enabled", False)
    print(f"    Resonance Tuning       : {'ON' if rt else 'OFF'}")

    # Burstiness パラメータ
    print(f"  burstiness_target_min    : {qp.get('burstiness_target_min', '?')}")
    print(f"  burstiness_target_max    : {qp.get('burstiness_target_max', '?')}")
    print(f"  max_sentence_split_ratio : {qp.get('max_sentence_split_ratio', '?')}")

    # LLM設定
    llm = cfg.get("llm", {})
    print(f"  llm.model_name           : {llm.get('model_name', '?')}")
    print(f"  llm.reasoning_effort     : {llm.get('reasoning_effort', '?')}")
    print(f"  llm.timeout              : {llm.get('timeout', '?')}")

    # human_resonance
    hr = cfg.get("human_resonance", {})
    print(f"  use_llm_for_editor       : {hr.get('use_llm_for_editor', '?')}")
    print(f"  use_llm_for_legal        : {hr.get('use_llm_for_legal', '?')}")

    # cognitive_drift
    cd = cfg.get("cognitive_drift", {})
    print(f"  cognitive_drift.enabled  : {cd.get('enabled', '?')}")

    return issues


# ──────────────────────────────────────────────
# 2. アウトライン解析テスト
# ──────────────────────────────────────────────
def check_outline(raw_text: str) -> list[str]:
    issues: list[str] = []
    from note.outline_mixin import OutlineMixin

    # _strip_code_fences テスト
    cleaned = OutlineMixin._strip_code_fences(raw_text)
    fences_removed = cleaned != raw_text
    print(f"  コードフェンス除去       : {'実行' if fences_removed else 'なし（フェンスなし）'}")

    # JSON抽出テスト
    match = re.search(r"\{.*\}", cleaned, re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            sections = data.get("sections", [])
            print(f"  JSONパース               : 成功 ({len(sections)} sections)")
            for i, s in enumerate(sections):
                heading = s.get("heading", "")
                valid = OutlineMixin._is_valid_heading(heading)
                mark = "✓" if valid else "✗ REJECTED"
                print(f"    [{i+1}] {mark} {heading[:60]}")
                if not valid:
                    issues.append(f"[WARN] 見出し{i+1} がJSON断片: {heading[:60]}")
        except json.JSONDecodeError as e:
            print(f"  JSONパース               : 失敗 ({e})")
            issues.append("[ERROR] コードフェンス除去後もJSONパース失敗 → フォールバック発生")
    else:
        print("  JSONパース               : マッチなし → フォールバック発生")
        issues.append("[ERROR] JSON抽出失敗 → フォールバック行パーサに落ちます")

    return issues


# ──────────────────────────────────────────────
# 3. ログ解析
# ──────────────────────────────────────────────
def check_log(log_path: Path, tail_lines: int = 500) -> list[str]:
    issues: list[str] = []
    if not log_path.exists():
        print(f"  ログファイルなし: {log_path}")
        return issues

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    recent = lines[-tail_lines:] if len(lines) > tail_lines else lines
    print(f"  ログ行数                 : {len(lines)} (直近 {len(recent)} 行を解析)")

    # パターン検出
    patterns = {
        "fallback_outline": (
            re.compile(r"Outline JSON path failed|fallback line parser"),
            "[WARN] アウトラインがフォールバック行パーサに落ちた",
        ),
        "heading_rejected": (
            re.compile(r"Outline heading rejected|Section heading contains JSON noise"),
            "[INFO] JSON断片の見出しが検出・拒否された",
        ),
        "resonance_skip": (
            re.compile(r"Resonance.*skip|Phase 1-4.*skip|enable_empathy.*False"),
            "[WARN] Resonance Phase がスキップされた",
        ),
        "quality_shadow": (
            re.compile(r"mode.*shadow|effective_mode.*shadow"),
            "[INFO] Quality Pipeline が shadow モードで動作",
        ),
        "editor_skip": (
            re.compile(r"editor LLM step skipped"),
            "[INFO] Editor LLM ステップがスキップされた",
        ),
        "legal_skip": (
            re.compile(r"legal LLM step skipped"),
            "[INFO] Legal LLM ステップがスキップされた",
        ),
        "api_error": (
            re.compile(r"APIError|RateLimitError|Timeout|openai.*error", re.I),
            "[ERROR] API エラー検出",
        ),
        "codefence_strip": (
            re.compile(r"strip_code_fences|code.?fence"),
            "[INFO] コードフェンス除去が実行された",
        ),
    }

    counts: dict[str, int] = {k: 0 for k in patterns}
    last_match: dict[str, str] = {}

    for line in recent:
        for key, (pat, _) in patterns.items():
            if pat.search(line):
                counts[key] += 1
                last_match[key] = line.strip()[-120:]

    for key, (_, msg) in patterns.items():
        c = counts[key]
        if c > 0:
            print(f"    {msg}: {c}回")
            print(f"      最新: {last_match[key]}")
            if "WARN" in msg or "ERROR" in msg:
                issues.append(f"{msg} ({c}回)")

    if all(c == 0 for c in counts.values()):
        print("    特記事項なし")

    return issues


# ──────────────────────────────────────────────
# main
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="TECHIE パイプライン診断")
    parser.add_argument("--outline", type=str, help="アウトライン生テキストを解析")
    parser.add_argument("--log", action="store_true", help="直近ログを解析")
    parser.add_argument("--log-lines", type=int, default=500, help="解析するログ末尾行数")
    args = parser.parse_args()

    cfg = _load_config()
    all_issues: list[str] = []

    print(SEP)
    print(" 1. 設定チェック")
    print(SEP)
    all_issues.extend(check_config(cfg))

    if args.outline:
        print()
        print(SEP)
        print(" 2. アウトライン解析")
        print(SEP)
        all_issues.extend(check_outline(args.outline))

    if args.log:
        print()
        print(SEP)
        print(" 3. ログ解析")
        print(SEP)
        log_path = PROJECT_ROOT / "logs" / "app.log"
        all_issues.extend(check_log(log_path, tail_lines=args.log_lines))

    # サマリ
    print()
    print(SEP)
    print(" サマリ")
    print(SEP)
    if not all_issues:
        print("  問題なし ✓")
    else:
        for issue in all_issues:
            print(f"  {issue}")
    print()

    return 1 if any("[ERROR]" in i or "[WARN]" in i for i in all_issues) else 0


if __name__ == "__main__":
    sys.exit(main())
