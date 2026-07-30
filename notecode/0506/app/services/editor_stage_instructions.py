from __future__ import annotations

from typing import Any

from app.services.editor_persona_contract import (
    EditorPersonaContractError,
    render_editor_persona_prompt,
    run_encoding_preflight,
)


SECOND_PASS_STAGE = "structural_editor"


class EditorStageInstructionError(ValueError):
    """Raised when editor persona instructions cannot be safely rendered."""


def build_editor_stage_instructions(
    stage_name: str,
    base_instructions: str,
    article_brief: dict[str, Any],
) -> str:
    brief = _brief(article_brief)
    genre_id = str(brief.get("genre_id") or "company_service_intro")
    narrator = str(brief.get("narrator") or "私たち")
    second_pass = stage_name == SECOND_PASS_STAGE and _second_pass_enabled(genre_id, narrator)
    persona_prompt = render_editor_persona_prompt(genre_id, narrator=narrator, second_pass=second_pass)
    preflight = run_encoding_preflight(persona_prompt, genre_id, narrator=narrator, second_pass=second_pass)
    if not preflight["pass"]:
        raise EditorStageInstructionError(f"editor persona preflight failed: {genre_id}/{stage_name}")

    stage_boundary = _stage_boundary(stage_name, genre_id)
    return "\n\n".join([base_instructions.strip(), stage_boundary, persona_prompt.strip()]) + "\n"


def summarize_editor_stage_contract(stage_name: str, article_brief: dict[str, Any]) -> dict[str, Any]:
    brief = _brief(article_brief)
    genre_id = str(brief.get("genre_id") or "company_service_intro")
    narrator = str(brief.get("narrator") or "私たち")
    second_pass = stage_name == SECOND_PASS_STAGE and _second_pass_enabled(genre_id, narrator)
    rendered = render_editor_persona_prompt(genre_id, narrator=narrator, second_pass=second_pass)
    preflight = run_encoding_preflight(rendered, genre_id, narrator=narrator, second_pass=second_pass)
    return {
        "stage_name": stage_name,
        "genre_id": genre_id,
        "narrator": narrator,
        "second_pass": second_pass,
        "prompt_line_count": preflight["prompt_line_count"],
        "prompt_char_count": preflight["prompt_char_count"],
        "preflight_pass": preflight["pass"],
        "api_send_allowed_current_owner": preflight["api_send_allowed_current_owner"],
    }


def _second_pass_enabled(genre_id: str, narrator: str) -> bool:
    try:
        render_editor_persona_prompt(genre_id, narrator=narrator, second_pass=True)
    except EditorPersonaContractError:
        return False
    return True


def _brief(article_brief: dict[str, Any]) -> dict[str, Any]:
    return article_brief.get("article_brief", article_brief)


def _stage_boundary(stage_name: str, genre_id: str) -> str:
    boundaries = {
        "opening_editor": "Stage boundary: improve the opening/front half only; keep later sections stable.",
        "global_consistency_editor": "Stage boundary: align voice across the whole article; remove repetition without new facts.",
        "style_editor": "Stage boundary: improve rhythm and readability; when adding text, add source-backed meaning density, not filler.",
        "structural_editor": "Stage boundary: focus on late-half structure and endings; preserve source-backed meaning density.",
    }
    boundary = boundaries.get(stage_name, "Stage boundary: edit only within the current stage responsibility.")
    if stage_name == SECOND_PASS_STAGE and genre_id == "daily_activity":
        return (
            boundary
            + " For daily_activity, preserve source-near scene material and do not compress into announcement/list guidance."
        )
    if stage_name == SECOND_PASS_STAGE and genre_id == "company_service_intro":
        return (
            boundary
            + " For company_service_intro, deepen the back half from selected excerpts and confirmed claims; keep provider-self voice."
        )
    return boundary
