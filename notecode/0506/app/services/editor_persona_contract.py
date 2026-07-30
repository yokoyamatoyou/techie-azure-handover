from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
PERSONA_DIR = ROOT / "app" / "personas"
CONTRACT_FILE = "editor_persona_contracts.yaml"
OWNER = "route_v_company_intro_front_back_editor_persona_contract_config_no_api_impl"
GENRE_DELTA_KEYS = {"role", "focus", "forbidden_boundary", "evidence_rule", "second_pass_need"}

class EditorPersonaContractError(ValueError):
    """Raised when the editor persona contract is missing or malformed."""

def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise EditorPersonaContractError(f"missing editor persona contract file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise EditorPersonaContractError(f"editor persona contract file must contain a mapping: {path}")
    return data

def load_editor_persona_contract(persona_dir: Path = PERSONA_DIR) -> dict[str, Any]:
    data = _load_yaml(persona_dir / CONTRACT_FILE)
    contract = data.get("editor_persona_contract")
    if not isinstance(contract, dict):
        raise EditorPersonaContractError("editor_persona_contracts.yaml must contain editor_persona_contract")
    _validate_contract(contract)
    return contract

def get_genre_editor_contract(genre_id: str, persona_dir: Path = PERSONA_DIR) -> dict[str, Any]:
    contract = load_editor_persona_contract(persona_dir)
    genres = contract["genres"]
    if genre_id not in genres:
        raise EditorPersonaContractError(f"unknown editor persona genre_id: {genre_id}")
    return genres[genre_id]

def render_editor_persona_prompt(
    genre_id: str,
    *,
    narrator: str,
    second_pass: bool = False,
    persona_dir: Path = PERSONA_DIR,
) -> str:
    contract = load_editor_persona_contract(persona_dir)
    genre = contract["genres"].get(genre_id)
    if genre is None:
        raise EditorPersonaContractError(f"unknown editor persona genre_id: {genre_id}")
    evidence_rule = _evidence_rule(contract, genre["evidence_rule"])
    second_pass_need = genre["second_pass_need"]
    if second_pass and not second_pass_need.get("needed"):
        raise EditorPersonaContractError(f"second editor persona is not configured for genre: {genre_id}")

    lines = [
        "# Editor Persona Contract",
        f"Owner: {contract['owner']}",
        f"Genre: {genre_id}",
        f"Role: {genre['role']}",
        f"Narrator: {narrator}",
        "",
        "## Common Editor Rules",
        *_bullets(contract["common"]["rules"]),
        "",
        "## Genre Delta",
        "Focus:",
        *_bullets(genre["focus"]),
        "Forbidden boundary:",
        *_bullets(genre["forbidden_boundary"]),
        "Evidence rule:",
        f"- key: {genre['evidence_rule']}",
        f"- general_knowledge: {evidence_rule['general_knowledge']}",
        f"- instruction: {evidence_rule['instruction']}",
        f"Second pass: {_second_pass_label(second_pass_need)}",
    ]

    if second_pass:
        lines.extend(
            [
                "",
                "## Conditional Second Editor",
                f"Role: {second_pass_need['role']}",
                "Common second-pass rules:",
                *_bullets(contract["common"]["second_pass_rules"]),
                "Genre second-pass delta:",
                *_bullets(second_pass_need["focus"]),
                "This is not a retry loop.",
            ]
        )

    return "\n".join(lines) + "\n"

def run_encoding_preflight(
    rendered_prompt: str | bytes,
    genre_id: str,
    *,
    narrator: str,
    second_pass: bool = False,
    future_api_context: bool = False,
    persona_dir: Path = PERSONA_DIR,
) -> dict[str, Any]:
    contract = load_editor_persona_contract(persona_dir)
    genre = contract["genres"].get(genre_id)
    if genre is None:
        raise EditorPersonaContractError(f"unknown editor persona genre_id: {genre_id}")

    if isinstance(rendered_prompt, bytes):
        prompt_bytes = rendered_prompt
    else:
        prompt_bytes = rendered_prompt.encode("utf-8")

    utf8_decode_pass = True
    try:
        decoded_prompt = prompt_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        utf8_decode_pass = False
        decoded_prompt = ""

    required_terms = [narrator, genre["role"]]
    second_pass_need = genre["second_pass_need"]
    if second_pass and second_pass_need.get("needed"):
        required_terms.append(second_pass_need["role"])
    required_terms.extend(_required_render_terms(contract, genre_id, second_pass=second_pass))

    encoding_rules = contract["common"]["encoding_preflight"]
    mojibake_hits = [marker for marker in encoding_rules["mojibake_sentinels"] if marker in decoded_prompt]
    replacement_count = decoded_prompt.count(encoding_rules["replacement_character"])
    question_mark_run_max = _max_question_mark_run(decoded_prompt)
    line_count = len(decoded_prompt.splitlines())
    char_count = len(decoded_prompt)
    bloat_pass = _bloat_pass(contract, genre, line_count, char_count)
    required_terms_present = all(term in decoded_prompt for term in required_terms)

    passed = (
        utf8_decode_pass
        and required_terms_present
        and not mojibake_hits
        and replacement_count == 0
        and question_mark_run_max <= encoding_rules["max_question_mark_run"]
        and bloat_pass
    )

    return {
        "owner": OWNER,
        "genre_id": genre_id,
        "utf8_decode_pass": utf8_decode_pass,
        "required_terms": required_terms,
        "required_terms_present": required_terms_present,
        "mojibake_sentinel_hits": mojibake_hits,
        "replacement_character_count": replacement_count,
        "question_mark_run_max": question_mark_run_max,
        "prompt_line_count": line_count,
        "prompt_char_count": char_count,
        "bloat_pass": bloat_pass,
        "pass": passed,
        "api_send_allowed": bool(passed and future_api_context),
        "api_send_allowed_current_owner": False,
    }

def validate_editor_persona_matrix(persona_dir: Path = PERSONA_DIR) -> dict[str, Any]:
    contract = load_editor_persona_contract(persona_dir)
    genres = contract["genres"]
    expected_genres = {
        "market_explanation",
        "company_service_intro",
        "announcement",
        "case_study",
        "comparison_guide",
        "daily_activity",
    }
    expected_second_pass_genres = expected_genres - {"announcement"}
    expected_second_pass_roles = {
        "company_service_intro": "source-backed 後半編集者",
        "daily_activity": "生活文芸編集者",
        "comparison_guide": "根拠編集者",
        "market_explanation": "構造整理編集者",
        "case_study": "証言境界編集者",
    }
    genre_keys_ok = all(set(genre.keys()) == GENRE_DELTA_KEYS for genre in genres.values())
    second_pass_enabled_genres = {
        genre_id for genre_id, genre in genres.items() if genre["second_pass_need"].get("needed") is True
    }
    second_pass_roles = {
        genre_id: genres[genre_id]["second_pass_need"].get("role") for genre_id in expected_second_pass_genres
    }
    evidence_refs_exist = all(genre["evidence_rule"] in contract["evidence_rules"] for genre in genres.values())
    return {
        "owner": OWNER,
        "expected_genres_present": set(genres) == expected_genres,
        "genre_delta_keys_ok": genre_keys_ok,
        "second_pass_enabled_genres": sorted(second_pass_enabled_genres),
        "non_announcement_second_pass_only": second_pass_enabled_genres == expected_second_pass_genres,
        "second_pass_roles": second_pass_roles,
        "announcement_second_pass_needed": genres["announcement"]["second_pass_need"].get("needed") is True,
        "daily_activity_role": genres["daily_activity"]["role"],
        "comparison_guide_role": genres["comparison_guide"]["role"],
        "comparison_evidence_rule": genres["comparison_guide"]["evidence_rule"],
        "evidence_refs_exist": evidence_refs_exist,
        "pass": set(genres) == expected_genres
        and genre_keys_ok
        and second_pass_enabled_genres == expected_second_pass_genres
        and second_pass_roles == expected_second_pass_roles
        and not genres["announcement"]["second_pass_need"].get("needed")
        and genres["daily_activity"]["role"] == "日々の文筆家"
        and genres["company_service_intro"]["role"] == "会社・サービス提供者側の社内ブロガー"
        and genres["comparison_guide"]["role"] == "選定アドバイザー"
        and genres["comparison_guide"]["evidence_rule"] == "split_source_fact_and_llm_general_context"
        and evidence_refs_exist,
    }

def _validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("owner") != OWNER:
        raise EditorPersonaContractError(f"unexpected owner: {contract.get('owner')}")
    common = contract.get("common")
    evidence_rules = contract.get("evidence_rules")
    genres = contract.get("genres")
    if not isinstance(common, dict) or not isinstance(common.get("rules"), list):
        raise EditorPersonaContractError("common.rules must be a list")
    if not isinstance(common.get("second_pass_rules"), list) or not common["second_pass_rules"]:
        raise EditorPersonaContractError("common.second_pass_rules must be a non-empty list")
    if not isinstance(evidence_rules, dict) or not evidence_rules:
        raise EditorPersonaContractError("evidence_rules must be a non-empty mapping")
    if not isinstance(genres, dict) or not genres:
        raise EditorPersonaContractError("genres must be a non-empty mapping")
    required_render_terms = common.get("required_render_terms", {})
    if required_render_terms and not isinstance(required_render_terms, dict):
        raise EditorPersonaContractError("common.required_render_terms must be a mapping when set")
    for genre_id, genre in genres.items():
        if not isinstance(genre, dict) or set(genre.keys()) != GENRE_DELTA_KEYS:
            raise EditorPersonaContractError(f"genre delta has invalid keys: {genre_id}")
        if genre["evidence_rule"] not in evidence_rules:
            raise EditorPersonaContractError(f"unknown evidence_rule for {genre_id}: {genre['evidence_rule']}")
        _require_list(genre, "focus", genre_id)
        _require_list(genre, "forbidden_boundary", genre_id)
        second_pass_need = genre["second_pass_need"]
        if not isinstance(second_pass_need, dict):
            raise EditorPersonaContractError(f"second_pass_need must be a mapping: {genre_id}")
        if second_pass_need.get("needed"):
            if not isinstance(second_pass_need.get("role"), str) or not second_pass_need["role"]:
                raise EditorPersonaContractError(f"second_pass role must be set: {genre_id}")
            if not isinstance(second_pass_need.get("focus"), list) or not second_pass_need["focus"]:
                raise EditorPersonaContractError(f"second_pass focus must be set: {genre_id}")

def _require_list(genre: dict[str, Any], key: str, genre_id: str) -> None:
    if not isinstance(genre.get(key), list) or not genre[key]:
        raise EditorPersonaContractError(f"{key} must be a non-empty list: {genre_id}")

def _evidence_rule(contract: dict[str, Any], evidence_rule_id: str) -> dict[str, Any]:
    rule = contract["evidence_rules"][evidence_rule_id]
    if not isinstance(rule, dict):
        raise EditorPersonaContractError(f"evidence rule must be a mapping: {evidence_rule_id}")
    return rule

def _required_render_terms(contract: dict[str, Any], genre_id: str, *, second_pass: bool) -> list[str]:
    required_terms = contract["common"].get("required_render_terms", {})
    genre_terms = required_terms.get(genre_id, {})
    if not isinstance(genre_terms, dict):
        raise EditorPersonaContractError(f"required render terms must be a mapping: {genre_id}")
    terms = list(genre_terms.get("base", []))
    if second_pass:
        terms.extend(genre_terms.get("second_pass", []))
    return terms

def _bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]

def _second_pass_label(second_pass_need: dict[str, Any]) -> str:
    if second_pass_need.get("needed"):
        return f"conditional:{second_pass_need['role']}"
    return second_pass_need.get("policy", "not_required")

def _max_question_mark_run(text: str) -> int:
    runs = re.findall(r"\?+", text)
    return max((len(run) for run in runs), default=0)

def _bloat_pass(contract: dict[str, Any], genre: dict[str, Any], line_count: int, char_count: int) -> bool:
    guard = contract["common"]["prompt_bloat_guard"]
    second_pass_need = genre["second_pass_need"]
    second_pass_items = 0
    if second_pass_need.get("needed"):
        second_pass_items = len(contract["common"]["second_pass_rules"]) + len(second_pass_need.get("focus", []))
    return (
        len(contract["common"]["rules"]) <= guard["max_common_rules"]
        and len(genre["focus"]) <= guard["max_focus_items"]
        and len(genre["forbidden_boundary"]) <= guard["max_forbidden_items"]
        and second_pass_items <= guard["max_second_pass_items"]
        and line_count <= guard["max_rendered_lines"]
        and char_count <= guard["max_rendered_chars"]
    )
