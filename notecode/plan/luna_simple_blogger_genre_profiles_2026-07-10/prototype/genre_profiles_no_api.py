from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROLE_ID = "company_side_blogger_v1"
FIXED_CALLS = 2
FORBIDDEN_PROFILE_KEYS = {"persona", "identity", "stage_2", "editor", "critic", "explainer", "repair_loop", "fallback"}
FORBIDDEN_RENDER_TERMS = ("別persona", "editor", "critic", "explainer", "第三段階", "repair loop", "fallback")

# These strings are common B-core instructions. A genre profile is rendered beside
# them; it cannot replace the identity, call count, source gate, or Stage 2 scope.
CORE_STAGE_1 = (
    "role_id: company_side_blogger_v1\n"
    "あなたはこの会社の仕事に日々触れているブロガーとして、偶然来たまだ関心の薄い読者へ書く。"
    "会社を外から評さず、compact source ledgerの具体的な場面・名詞・動作から興味を立ち上げ、事実を足さない。\n\n"
    "ledgerだけを根拠に、#を1つ、自然な##、指定された本文floorを満たす記事本文だけを返す。"
    "自社本人の声を保ち、抽象的な読者誘導よりsource固有の名詞と動詞を優先する。"
    "sourceにない数値、日付、成果、感情、顧客評価、比較優位を足さない。"
    "判断軸・判断材料・第一歩・過剰な確認/整理/説明へ逃げず、事実を水増ししない。"
    "段落ごとに、誰が何をしているかがわかるように書く。日付、価格、約束、依頼、責任は主語を明示する。Markdown以外の注釈や内部説明は出力しない。本文の水増しはしない。内部の注釈を出力しない。"
)
CORE_STAGE_2 = (
    "role_id: company_side_blogger_v1\n"
    "同じ書き手として、compact source ledgerと初稿全文を一度だけ読み直す。"
    "見るのは、低関心読者の続きを読む理由、自社本人の声、省略主語の一意性、"
    "source固有の場面・名詞・動作が定型的なメタ文に置き換わっていないかの4点だけ。\n\n"
    "問題がある段落だけと隣接1文までを書き直し、他の段落、事実、# / ##順、本文floorを保つ。"
    "問題がなければ初稿をそのまま返す。部分出力ではなく記事本文だけを返し、新しい事実は足さない。"
    "見出しや段落、引用の切替で話者が競合するときは、責任を持つ主語を明示する。過去の段落を言い換えるためだけに内容を増減させず、sourceの根拠がない評価や感想を置かない。本文の長さを削らず、本文全文を返す。部分的な差分は返さない。根拠のない評価、感情、成果、比較優位を足さない。見出しと本文の順序を保つ。"
)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compact_ledger(case: dict) -> str:
    signals = "、".join(case["saved_signal_labels"])
    return f"saved compact ledger reference: {case['id']} | claim/use signals: {signals}"


def validate_profile(profile: dict) -> None:
    required = {
        "id", "intro_source_priority", "reader_arrival_goal", "paragraph_flow",
        "subject_omission_handling", "major_risk", "body_floor", "cta_mode",
    }
    keys = set(profile)
    missing = required - keys
    extra = keys - required
    if missing or extra:
        raise ValueError(f"profile keys mismatch: missing={sorted(missing)} extra={sorted(extra)}")
    if keys & FORBIDDEN_PROFILE_KEYS:
        raise ValueError("profile contains a forbidden pipeline/persona key")
    if not isinstance(profile["intro_source_priority"], list) or not 1 <= len(profile["intro_source_priority"]) <= 3:
        raise ValueError("intro_source_priority must be a compact 1..3 item list")
    if not isinstance(profile["paragraph_flow"], list) or not 3 <= len(profile["paragraph_flow"]) <= 4:
        raise ValueError("paragraph_flow must have 3..4 broad moves")
    if profile["cta_mode"] not in {"none", "source_optional"}:
        raise ValueError("CTA may be absent or source-optional only")
    if not isinstance(profile["body_floor"], int) or profile["body_floor"] < 600:
        raise ValueError("body_floor must remain a meaningful fixed integer")


def render_profile(profile: dict) -> str:
    validate_profile(profile)
    return "\n".join((
        f"genre profile: {profile['id']}",
        f"導入で優先するsource材料: {'、'.join(profile['intro_source_priority'])}",
        f"読者の到達目的: {profile['reader_arrival_goal']}",
        f"大まかな段落の流れ: {' → '.join(profile['paragraph_flow'])}",
        f"話者・主語省略: {profile['subject_omission_handling']}",
        f"このタイプ固有の重大リスク: {profile['major_risk']}",
        f"body floor: {profile['body_floor']} / CTA: {profile['cta_mode']}",
    ))


def render_contract(profile: dict, case: dict, draft: str = "<stage_1_full_article>") -> dict:
    profile_text = render_profile(profile)
    ledger = compact_ledger(case)
    stage_1 = f"{CORE_STAGE_1}\n\n{profile_text}\n\n{ledger}"
    stage_2 = f"{CORE_STAGE_2}\n\n{profile_text}\n\n{ledger}\n\n初稿全文:\n{draft}"
    if any(term in profile_text for term in FORBIDDEN_RENDER_TERMS):
        raise ValueError("forbidden role/pipeline term reached a rendered profile")
    return {
        "role_id": ROLE_ID,
        "fixed_calls": FIXED_CALLS,
        "raw_full_source_handoff": False,
        "stage_2_scope": "failed_paragraph_plus_adjacent_one_sentence_only",
        "core": {
            "stage_1_chars": len(CORE_STAGE_1), "stage_1_sha256": digest(CORE_STAGE_1),
            "stage_2_chars": len(CORE_STAGE_2), "stage_2_sha256": digest(CORE_STAGE_2),
        },
        "profile": {"chars": len(profile_text), "sha256": digest(profile_text)},
        "stage_1": {"chars": len(stage_1), "sha256": digest(stage_1), "prompt": stage_1},
        "stage_2": {"chars": len(stage_2), "sha256": digest(stage_2), "prompt": stage_2},
    }


def review_bundle(profile: dict, case: dict, contract: dict) -> str:
    return "\n".join((
        f"# {profile['id']} — Luna B genre-profile human review", "",
        "> This is a no-API contract/replay bundle. It does not claim that a Luna B article was generated for this type.", "",
        "## Saved-artifact fixture", "",
        f"- saved baseline article: `{case['baseline_article']}`", f"- saved source-packet reference: `{case['source_packet']}`",
        f"- compact saved-signal labels: {', '.join(case['saved_signal_labels'])}",
        f"- baseline body floor: `{profile['body_floor']}`", "",
        "## Rendered profile", "", "```text", render_profile(profile), "```", "",
        "## Invariants checked", "",
        f"- same role: `{contract['role_id']}`", f"- fixed calls: `{contract['fixed_calls']}`",
        f"- Stage 2 scope: `{contract['stage_2_scope']}`", "- raw full source handoff: `false`",
        "- unsupported claims remain a hard gate; static replay does not mark them as passed.", "",
        "## Human review questions", "",
        "1. Does the chosen opening material exist in the saved source packet, rather than merely sounding genre-appropriate?",
        "2. Does the intended reader outcome keep a company-side voice rather than turning into an outside explanation?",
        "3. Could the subject still be uniquely recovered after a heading, paragraph, or quoted-speaker boundary?",
        f"4. Does the profile directly prevent this type's major risk: {profile['major_risk']}?",
        "5. Does the profile add only type framing, not a new persona, stage, repair path, or fallback?", "",
        "## Prompt accounting", "",
        f"- common Stage 1 core chars: `{contract['core']['stage_1_chars']}`",
        f"- common Stage 2 core chars: `{contract['core']['stage_2_chars']}`",
        f"- profile chars: `{contract['profile']['chars']}`",
        f"- rendered Stage 1 chars (stub ledger): `{contract['stage_1']['chars']}`",
        f"- rendered Stage 2 chars (stub ledger + draft marker): `{contract['stage_2']['chars']}`", "",
    ))


def run(manifest_path: Path, profiles_path: Path, out_dir: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    profile_by_id = {profile["id"]: profile for profile in profiles["profiles"]}
    if len(profile_by_id) != 6 or set(profile_by_id) != set(manifest["article_types"]):
        raise ValueError("exactly the six declared UI article types are required")

    out_dir.mkdir(parents=True, exist_ok=True)
    prompts = out_dir / "rendered_prompts"; prompts.mkdir(exist_ok=True)
    reviews = out_dir / "human_review_bundle"; reviews.mkdir(exist_ok=True)
    rows, index_lines = [], ["# Luna B Genre Profile Review Index", "", "> No Luna B article was generated for the six UI types in this no-API package.", "", "| type | profile chars | Stage 1 / Stage 2 chars | calls | major risk |", "|---|---:|---:|---:|---|"]
    for case in manifest["cases"]:
        profile = profile_by_id[case["id"]]
        contract = render_contract(profile, case)
        (prompts / f"{case['id']}_stage_1.txt").write_text(contract["stage_1"]["prompt"] + "\n", encoding="utf-8")
        (prompts / f"{case['id']}_stage_2.txt").write_text(contract["stage_2"]["prompt"] + "\n", encoding="utf-8")
        (reviews / f"{case['id']}.md").write_text(review_bundle(profile, case, contract), encoding="utf-8")
        row = {"type": case["id"], "profile_chars": contract["profile"]["chars"], "stage_1_chars": contract["stage_1"]["chars"], "stage_2_chars": contract["stage_2"]["chars"], "fixed_calls": 2, "major_risk": profile["major_risk"], "body_floor": profile["body_floor"], "cta_mode": profile["cta_mode"]}
        rows.append(row)
        index_lines.append(f"| {row['type']} | {row['profile_chars']} | {row['stage_1_chars']} / {row['stage_2_chars']} | 2 | {row['major_risk']} |")
    (reviews / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    report = {
        "decision": "conditionally_possible", "api_send_count": 0, "source_refetch": False,
        "raw_full_source_handoff": False, "generated_article_patch": False,
        "route_v_product_code_changed": False, "route_v_ui_connected": False,
        "same_role_all_types": all(render_contract(profile_by_id[c["id"]], c)["role_id"] == ROLE_ID for c in manifest["cases"]),
        "fixed_calls_all_types": all(render_contract(profile_by_id[c["id"]], c)["fixed_calls"] == FIXED_CALLS for c in manifest["cases"]),
        "profile_rows": rows,
        "limits": [
            "No generated Luna B article exists for five types; company_service_intro has one saved source only.",
            "Static replay cannot prove semantic grounding or unsupported-claim absence.",
            "Route V connection, UI adoption, default selection, and live validation remain unapproved.",
        ],
        "next_owner": "luna_simple_blogger_genre_profiles_human_contract_review_wait",
    }
    (out_dir / "profile_comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    no_api_lines = [
        "# No-API Decision Report", "", "## Decision", "", "`conditionally_possible`", "",
        "## Recorded boundaries", "",
        "- API send count: `0`", "- source refetch: `false`", "- raw full source handoff: `false`",
        "- generated article patch: `false`", "- Route V product code changed: `false`", "- Route V UI connected: `false`", "",
        "## Structural evidence", "",
        f"- six profiles: `{len(rows)}`", f"- shared role: `{report['same_role_all_types']}`",
        f"- fixed two calls: `{report['fixed_calls_all_types']}`", f"- Stage 1 / Stage 2 fixed core chars: `{len(CORE_STAGE_1)} / {len(CORE_STAGE_2)}`", "",
        "## What this does not prove", "",
        "No six-type Luna B article was generated. Static replay cannot prove semantic grounding, unsupported-claim absence, reader preference, body-floor attainment, or rhythm. Route V connection and UI adoption remain unapproved.", "",
        "## One current next owner", "", f"`{report['next_owner']}`", "",
    ]
    (out_dir / "no_api_decision_report.md").write_text("\n".join(no_api_lines), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--profiles", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.manifest, args.profiles, args.out_dir), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
