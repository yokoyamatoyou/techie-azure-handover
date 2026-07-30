from __future__ import annotations

from typing import Any

from app.agents.article_brief_builder import build_editorial_bridge_policy
from app.services.global_consistency_editor import run_global_consistency_editor
from app.services.local_draft_renderer import render_local_draft
from app.services.local_source_card_builder import build_local_source_card
from app.services.opening_editor import run_opening_editor
from app.services.structural_editor import run_structural_editor
from app.services.style_postprocessor import postprocess_style


class LocalPipelineClient:
    """Deterministic local client used for tests and no-key MVP runs."""

    def generate_json(
        self,
        stage_name: str,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        if stage_name == "source_card_extraction":
            return self._source_card(payload)
        if stage_name == "knowledge_pack_integration":
            return self._knowledge_pack(payload)
        if stage_name == "article_brief_builder":
            return self._article_brief(payload)
        raise ValueError(f"unsupported local JSON stage: {stage_name}")

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        if stage_name == "draft_writer":
            return self._draft(payload)
        if stage_name == "opening_editor":
            return run_opening_editor(
                payload["article_text"],
                payload["article_brief"],
                payload["knowledge_pack"],
            ).text
        if stage_name == "global_consistency_editor":
            return run_global_consistency_editor(payload["article_text"], payload["article_brief"]).text
        if stage_name == "style_editor":
            return postprocess_style(payload["draft"], payload.get("article_brief"))
        if stage_name == "structural_editor":
            return run_structural_editor(payload["article_text"], payload.get("article_brief")).text
        if stage_name == "targeted_rewriter":
            text = payload["article_text"]
            text = text.replace("いかがでしたでしょうか。", "")
            text = text.replace("第一歩", "具体的な準備")
            return text.strip()
        raise ValueError(f"unsupported local text stage: {stage_name}")

    def _source_card(self, payload: dict[str, Any]) -> dict[str, Any]:
        return build_local_source_card(payload["source_packet"])

    def _knowledge_pack(self, payload: dict[str, Any]) -> dict[str, Any]:
        cards = payload["source_cards"]
        confirmed = []
        for card in cards:
            for index, fact in enumerate(card["facts"], start=len(confirmed) + 1):
                confirmed.append(
                    {
                        "claim_id": f"C{index:03d}",
                        "claim": fact["claim"],
                        "supporting_fact_ids": [fact["fact_id"]],
                        "confidence": fact["confidence"],
                        "preferred_expression": fact["claim"],
                        "risk_flags": fact.get("risk_flags", []),
                    }
                )
        return {
            "article_knowledge_pack": {
                "pack_id": "pack_local_001",
                "source_card_ids": [card["source_id"] for card in cards],
                "confirmed_facts": confirmed,
                "conflicts": [],
                "deduped_themes": [card["title"] for card in cards],
                "do_not_infer": ["ソースにない実績、価格、日付、効果を追加しない"],
            }
        }

    def _article_brief(self, payload: dict[str, Any]) -> dict[str, Any]:
        claims = payload["knowledge_pack"]["article_knowledge_pack"]["confirmed_facts"]
        length_plan = _plan_length(payload["genre_id"], len(claims))
        sections = _plan_sections(payload["genre_id"], payload["narrator"], claims, length_plan["section_count"])
        bridge_policy = payload.get("editorial_bridge_policy") or build_editorial_bridge_policy()
        style_profile = payload.get("style_profile", {})
        editor_profile = payload.get("editor_profile", {})
        style_edit_policy = _style_edit_policy(style_profile)
        editor_pass_policy = _editor_pass_policy(editor_profile)
        self_viewpoint_owner = str(payload.get("self_viewpoint_owner") or payload["narrator"]).strip()
        return {
            "article_brief": {
                "brief_id": "brief_local_001",
                "genre_id": payload["genre_id"],
                "persona_id": payload["persona_id"],
                "writer_role": payload["writer_role"],
                "viewpoint_mode": payload["viewpoint_mode"],
                "target_reader": payload["target_reader"],
                "article_goal": payload["article_goal"],
                "narrator": payload["narrator"],
                "self_viewpoint_owner": self_viewpoint_owner,
                "qa_policy_id": payload["qa_policy_id"],
                "style_profile_id": style_profile.get("style_profile_id", "note_hatena_owned_media_soft"),
                "style_edit_policy": style_edit_policy,
                "editor_profile_id": editor_profile.get("editor_profile_id", "note_hatena_structural_editor"),
                "editor_pass_policy": editor_pass_policy,
                "target_length_chars": length_plan["target_length_chars"],
                "section_count": length_plan["section_count"],
                "source_thickness": length_plan["source_thickness"],
                "editorial_bridge_policy": bridge_policy,
                "editorial_bridge_candidates": [],
                "claim_allocation": [
                    {"section_id": section["section_id"], "claim_ids": section["assigned_claim_ids"], "reuse_allowed": False}
                    for section in sections
                ],
                "sections": sections,
                "style_rules": [
                    "note/はてなブログ向けに段落を詰めすぎない",
                    f"{payload['narrator']}は{self_viewpoint_owner}本人の声として扱う",
                    "公式サイトを読んで紹介する第三者視点にしない",
                    style_profile.get("codex_visibility", "改行、読点、主語省略、文末バケットを確認する。"),
                    editor_profile.get("codex_visibility", "後半中心に記事全体の破綻を確認する。"),
                ],
                "forbidden_viewpoint_terms": ["同社", "同サービス", "同店", "同院"],
                "allowed_external_voice": "attributed_quotes_only",
                "config_refs": ["app/config/article_genres.yaml", "app/config/platform_style_targets.yaml"],
                "persona_refs": [
                    "app/personas/writer_roles.yaml",
                    "app/personas/viewpoint_profiles.yaml",
                    "app/personas/style_profiles.yaml",
                    "app/personas/editor_profiles.yaml",
                ],
            }
        }

    def _draft(self, payload: dict[str, Any]) -> str:
        return render_local_draft(payload["article_brief"], payload["knowledge_pack"])


def _plan_length(genre_id: str, claim_count: int) -> dict[str, Any]:
    if claim_count <= 2:
        thickness = "thin"
        target = 700
        sections = 1
    elif claim_count <= 5:
        thickness = "medium"
        target = 1200
        sections = 2
    else:
        thickness = "thick"
        target = 1800
        sections = 3
    if genre_id == "announcement":
        target = max(600, target - 200)
        sections = min(sections, 2)
    if genre_id == "daily_activity":
        target = min(target, 1200)
        sections = min(sections, 2)
    return {"source_thickness": thickness, "target_length_chars": target, "section_count": sections}


def _plan_sections(
    genre_id: str,
    narrator: str,
    claims: list[dict[str, Any]],
    section_count: int,
) -> list[dict[str, Any]]:
    headings = _headings_for_genre(genre_id, narrator, section_count)
    chunks = _split_claims_for_genre(genre_id, claims, section_count)
    sections = []
    for index, assigned in enumerate(chunks, start=1):
        sections.append(
            {
                "section_id": f"s{index}",
                "heading": headings[index - 1],
                "purpose": _purpose_for_genre(genre_id, index),
                "assigned_claim_ids": assigned,
                "main_subject": narrator,
                "discourse_rules": ["同社を使わない", "根拠のない効果を足さない"],
            }
        )
    return sections


def _headings_for_genre(genre_id: str, narrator: str, section_count: int) -> list[str]:
    if genre_id == "market_explanation":
        base = ["ビジネスモデルを考える視点", "マーケティングで押さえたいこと", "市場性をどう見立てるか"]
    elif genre_id == "announcement":
        base = ["お知らせの概要", "変更内容と対象"]
    elif genre_id == "case_study":
        base = ["お客様の状況", "私たちが行ったこと", "声や変化から見えること"]
    elif genre_id == "comparison_guide":
        base = ["選ぶ前に整理したいこと", "比較するときの見方", "確認しておきたいポイント"]
    elif genre_id == "daily_activity":
        base = ["できごとのきっかけ", "当日の様子"]
    elif narrator == "当社":
        base = ["当社について", "提供していること", "ご相談の流れ"]
    else:
        base = ["私たちについて", "私たちが提供していること", "ご相談の流れ"]
    return base[:section_count]


def _purpose_for_genre(genre_id: str, index: int) -> str:
    if genre_id == "market_explanation":
        return ["論点の全体像を伝える", "価値の届け方を説明する", "市場の見立て方を整理する"][min(index - 1, 2)]
    if genre_id == "announcement":
        return ["事実関係を簡潔に伝える", "日時や対象を明確に伝える"][min(index - 1, 1)]
    if genre_id == "case_study":
        return ["お客様の背景を伝える", "提供内容を伝える", "声や学びを根拠付きで伝える"][min(index - 1, 2)]
    if genre_id == "comparison_guide":
        return ["選ぶ前の論点を整理する", "比較軸を伝える", "確認ポイントを伝える"][min(index - 1, 2)]
    if genre_id == "daily_activity":
        return ["場面やきっかけを伝える", "できごとと気づきを自然に伝える"][min(index - 1, 1)]
    return ["概要を伝える", "提供価値を伝える", "次の行動を伝える"][min(index - 1, 2)]


def _split_claim_ids(claim_ids: list[str], section_count: int) -> list[list[str]]:
    if section_count <= 1:
        return [claim_ids]
    chunk_size = max(1, (len(claim_ids) + section_count - 1) // section_count)
    return [
        claim_ids[index : index + chunk_size]
        for index in range(0, len(claim_ids), chunk_size)
    ][:section_count]


def _split_claims_for_genre(
    genre_id: str,
    claims: list[dict[str, Any]],
    section_count: int,
) -> list[list[str]]:
    claim_ids = [claim["claim_id"] for claim in claims]
    if genre_id != "market_explanation" or section_count < 3:
        return _split_claim_ids(claim_ids, section_count)

    groups = {"business": [], "marketing": [], "market": []}
    for claim in claims:
        text = claim["preferred_expression"]
        if any(term in text for term in ("Marketing", "マーケティング", "仲間", "フィードバック", "不確実")):
            groups["marketing"].append(claim["claim_id"])
        elif any(term in text for term in ("市場性", "市場", "ポテンシャル")):
            groups["market"].append(claim["claim_id"])
        else:
            groups["business"].append(claim["claim_id"])
    return [groups["business"], groups["marketing"], groups["market"]][:section_count]


def _style_edit_policy(style_profile: dict[str, Any]) -> dict[str, Any]:
    paragraph = style_profile.get("paragraph_policy", {})
    subject = style_profile.get("subject_omission_policy", {})
    ending = style_profile.get("ending_bucket_policy", {})
    return {
        "preferred_sentences_per_paragraph": int(paragraph.get("preferred_sentences_per_paragraph", 2)),
        "max_sentences_per_paragraph": int(paragraph.get("max_sentences_per_paragraph", 3)),
        "line_break_policy": str(paragraph.get("line_break_policy", "topic_shift_or_two_sentences")),
        "subject_omission_policy": str(subject.get("mode", "clear_context_only")),
        "ending_bucket_policy": "structural_variation"
        if ending.get("prefer_structural_variation", True)
        else "preserve_formal_endings",
        "protected_subject_terms": list(subject.get("protected_fact_terms", [])),
    }


def _editor_pass_policy(editor_profile: dict[str, Any]) -> dict[str, Any]:
    policy = editor_profile.get("policy", {})
    return {
        "focus_late_half": bool(policy.get("focus_late_half", True)),
        "split_late_paragraph_over_sentences": int(policy.get("split_late_paragraph_over_sentences", 2)),
        "align_first_person_to_narrator": bool(policy.get("align_first_person_to_narrator", True)),
        "preserve_facts": bool(policy.get("preserve_facts", True)),
        "preserve_numbers_dates_names": bool(policy.get("preserve_numbers_dates_names", True)),
        "do_not_add_claims": bool(policy.get("do_not_add_claims", True)),
    }
