from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agents.draft_writer import DraftWriter
from app.services.draft_followthrough import body_chars_excluding_headings, case_study_surface_followthrough
from app.services.human_visible_surface_gate import check_human_visible_surface


NOTECODE_ROOT = Path(__file__).resolve().parents[2]


class RecordingClient:
    def __init__(self, response: str = "# draft") -> None:
        self.calls: list[dict[str, Any]] = []
        self.response = response

    def generate_json(
        self,
        stage_name: str,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        raise AssertionError("generate_json should not be called")

    def generate_text(self, stage_name: str, instructions: str, payload: dict[str, Any]) -> str:
        self.calls.append(
            {
                "stage_name": stage_name,
                "instructions": instructions,
                "payload": payload,
            }
        )
        return self.response


def test_draft_writer_uses_target_length_as_soft_depth_for_thick_sources() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "target_length_chars": 3000,
            "source_thickness": "thick",
            "section_count": 5,
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [{"claim_id": f"C{i:03d}"} for i in range(1, 15)]
        }
    }

    assert DraftWriter(client).write(brief, knowledge_pack) == "# draft"

    instructions = client.calls[0]["instructions"]
    assert "soft depth target" in instructions
    assert "85 percent" in instructions
    assert "For 5 planned sections and 14 confirmed claims" in instructions
    assert "full article rather than a short summary" in instructions
    assert "do not shrink the article below the depth target" in instructions
    assert "editorial_bridge_candidates" not in instructions
    assert "avoid filler" in instructions
    assert "third-party review or source-summary voice" in instructions
    assert len(instructions) < 1150


def test_draft_writer_keeps_thin_sources_concise() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "target_length_chars": 700,
            "source_thickness": "thin",
        }
    }

    DraftWriter(client).write(brief, {"article_knowledge_pack": {"confirmed_facts": []}})

    instructions = client.calls[0]["instructions"]
    assert "soft depth target" not in instructions
    assert "Keep the article concise" in instructions
    assert "editorial_bridge_candidates" not in instructions
    assert "selected_source_excerpts" not in client.calls[0]["payload"]


def test_route_v_draft_writer_accepts_selected_source_excerpts() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "voice_mode": "self_authored_blogger",
            "target_length_chars": 1600,
            "body_length_floor_chars": 1400,
            "section_count": 2,
            "source_use_mode": "selective",
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "claim_ids": ["C001"],
            "section_ids": ["s1"],
            "text": "Source context around the assigned claim.",
        }
    ]

    DraftWriter(client).write(
        brief,
        {"article_knowledge_pack": {"confirmed_facts": [{"claim_id": "C001"}]}},
        excerpts,
    )

    instructions = client.calls[0]["instructions"]
    payload = client.calls[0]["payload"]
    assert payload["selected_source_excerpts"] == excerpts
    assert "source_documents" not in payload
    assert "Use selected_source_excerpts as primary section context" in instructions
    assert "bounded primary material for matching sections" in instructions
    assert "assigned/confirmed claims as verification anchors" in instructions
    assert "Do not add facts absent from selected_source_excerpts or confirmed claims" in instructions


def test_route_v_company_table_floor_uses_assigned_claim_anchors_without_raw_sources() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "source_shape": "table_or_list",
            "source_use_mode": "representative",
            "target_length_chars": 1600,
            "body_length_floor_chars": 1400,
            "section_count": 3,
            "claim_allocation": [
                {"section_id": "sec_01", "claim_ids": ["C001", "C002", "C003", "C004"], "reuse_allowed": False},
                {"section_id": "sec_02", "claim_ids": ["C005", "C006", "C007", "C008"], "reuse_allowed": False},
                {"section_id": "sec_03", "claim_ids": ["C009", "C010"], "reuse_allowed": False},
            ],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [{"claim_id": f"C{i:03d}"} for i in range(1, 25)]
        }
    }

    DraftWriter(client).write(brief, knowledge_pack)

    instructions = client.calls[0]["instructions"]
    payload = client.calls[0]["payload"]
    assert "Body floor actuation" in instructions
    assert "Use assigned claims as anchors" in instructions
    assert "Depth budget contract" in instructions
    assert "draft about 2100 source-backed body chars before editors" in instructions
    assert "roughly 700 per section" in instructions
    assert "preserving a 700-char floor buffer" in instructions
    assert "at least 13 source-grounded body paragraphs" in instructions
    assert "Japanese chars per anchor" not in instructions
    assert "split dense assigned claims into adjacent context, example, or transition paragraphs" in instructions
    assert "Representative/selective mode is not short-summary mode" in instructions
    assert "do not enumerate unassigned claims" in instructions
    assert "For 3 sections, 10 assigned claims, and 24 confirmed claims" in instructions
    assert "source_documents" not in payload
    assert len(instructions) < 3300


def test_route_v_service_catalog_selective_floor_expands_assigned_claims_not_raw_sources() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "source_shape": "service_catalog",
            "source_use_mode": "selective",
            "target_length_chars": 1500,
            "body_length_floor_chars": 1400,
            "section_count": 3,
            "claim_allocation": [
                {"section_id": "S1", "claim_ids": ["C001", "C002", "C003", "C004"], "reuse_allowed": False},
                {"section_id": "S2", "claim_ids": ["C005", "C006", "C007", "C008"], "reuse_allowed": False},
                {"section_id": "S3", "claim_ids": ["C009", "C010"], "reuse_allowed": False},
            ],
            "unassigned_claim_ids": [f"C{i:03d}" for i in range(11, 25)],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [{"claim_id": f"C{i:03d}"} for i in range(1, 25)]
        }
    }
    excerpts = [{"excerpt_id": "E001", "claim_ids": ["C001"], "text": "Bounded texture."}]

    DraftWriter(client).write(brief, knowledge_pack, excerpts)

    instructions = client.calls[0]["instructions"]
    payload = client.calls[0]["payload"]
    assert payload["selected_source_excerpts"] == excerpts
    assert "source_documents" not in payload
    assert "Representative/selective mode is not short-summary mode" in instructions
    assert "deepen assigned claims" in instructions
    assert "do not enumerate unassigned claims" in instructions
    assert "Floor_chars is not padding" in instructions
    assert "Depth budget contract" in instructions
    assert "draft about 2100 source-backed body chars before editors" in instructions
    assert "preserving a 700-char floor buffer" in instructions
    assert "Use 1 selected_source_excerpts as primary section context" in instructions
    assert "Keep assigned claims as verification anchors" in instructions
    assert "at least 13 source-grounded body paragraphs" in instructions
    assert "Japanese chars per anchor" not in instructions
    assert "Backfill paragraphs with assigned-claim depth or relevant unassigned confirmed claims as company-side context, not inventory" in instructions
    assert len(instructions) < 3300


def test_route_v_narrative_selective_floor_and_h1_contract_are_bounded() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "source_shape": "narrative",
            "source_use_mode": "selective",
            "target_length_chars": 1400,
            "body_length_floor_chars": 1400,
            "section_count": 3,
            "claim_allocation": [
                {"section_id": "S1", "claim_ids": ["C001", "C002", "C003"], "reuse_allowed": False},
                {"section_id": "S2", "claim_ids": ["C004", "C005", "C006"], "reuse_allowed": False},
                {"section_id": "S3", "claim_ids": ["C007", "C008"], "reuse_allowed": False},
            ],
            "unassigned_claim_ids": [f"C{i:03d}" for i in range(9, 20)],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [{"claim_id": f"C{i:03d}"} for i in range(1, 20)]
        }
    }
    excerpts = [{"excerpt_id": "E001", "claim_ids": ["C001", "C004"], "text": "Bounded narrative texture."}]

    DraftWriter(client).write(brief, knowledge_pack, excerpts)

    instructions = client.calls[0]["instructions"]
    payload = client.calls[0]["payload"]
    assert payload["selected_source_excerpts"] == excerpts
    assert "source_documents" not in payload
    assert 'exactly one H1 heading line ("# " + title)' in instructions
    assert "no second H1" in instructions
    assert "Representative/selective mode is not short-summary mode" in instructions
    assert "deepen assigned claims" in instructions
    assert "do not enumerate unassigned claims" in instructions
    assert "at least 13 source-grounded body paragraphs" in instructions
    assert "Japanese chars per anchor" not in instructions
    assert "For 3 sections, 8 assigned claims, and 19 confirmed claims" in instructions
    assert "assigned/confirmed claims as verification anchors" in instructions
    assert "company-side context, not inventory" in instructions
    assert len(instructions) < 3300


def test_route_v_company_intro_navigation_block_redirects_sanrei_shape_budget() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "source_shape": "announcement_details",
            "source_use_mode": "selective",
            "target_length_chars": 1680,
            "body_length_floor_chars": 1400,
            "section_count": 2,
            "claim_allocation": [
                {"section_id": "S1", "claim_ids": ["C001", "C002", "C003", "C004"], "reuse_allowed": False},
                {"section_id": "S2", "claim_ids": ["C005", "C006", "C007", "C008"], "reuse_allowed": False},
            ],
            "unassigned_claim_ids": [f"C{i:03d}" for i in range(9, 18)],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [{"claim_id": f"C{i:03d}"} for i in range(1, 18)]
        }
    }
    excerpts = [
        {"excerpt_id": f"E{i:03d}", "claim_ids": [f"C{i:03d}"], "text": "Bounded company context."}
        for i in range(1, 5)
    ]

    DraftWriter(client).write(brief, knowledge_pack, excerpts)

    instructions = client.calls[0]["instructions"]
    assert "company-side work/action/value statements" in instructions
    assert "outside-observer inference" in instructions
    assert "company-side context, not inventory" in instructions
    assert "do not enumerate unassigned claims" in instructions
    assert "For 2 sections, 8 assigned claims, and 17 confirmed claims" in instructions
    assert len(instructions) < 3300


def test_route_v_company_intro_payload_normalizes_legacy_reader_navigation_plan() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "source_shape": "announcement_details",
            "source_use_mode": "selective",
            "target_length_chars": 1680,
            "body_length_floor_chars": 1400,
            "section_count": 2,
            "claim_allocation": [
                {"section_id": "S1", "claim_ids": ["C001", "C002"], "reuse_allowed": False},
                {"section_id": "S2", "claim_ids": ["C003", "C004"], "reuse_allowed": False},
            ],
            "article_goal": "検索結果やサムネイルから来た読者が、どの公式情報を見ると判断しやすいかを自然に理解できる会社紹介記事を書く。",
            "style_rules": [
                "本文では私たちを基準にし、外部レビューのような語り口にしない。",
                "最後は読み手が次に確認しやすい情報の並びで穏やかに締める。",
            ],
            "interest_hook": "会社説明から始めず、暮らし・仕事・選定・運用・知見の小さな接点から入る。",
            "reading_reward": "会社の肩書きではなく、日々のどの場面を支え、どんな人・運用・考え方で届けているかが分かる。",
            "self_authored_angle": "私たちは、プロフィールや商品カタログではなく日々の接点とsource事実から自分たちの仕事を伝える。",
            "source_backed_reader_bridge_policy": "sourceの内容を読者に近い文脈へ翻訳し、読む順番や確認先として案内せずに扱う。",
            "source_derived_aside_policy": "濃い事実ブロック後に、source内の事実の見方だけを一文で受ける。",
            "rhythm_break_plan": [
                "事実説明が続いた後に、読者が次の段落へ進みやすい一文をsource内の情報だけで置く。"
            ],
            "paragraph_function_plan": [
                "導入: 見に来ただけの読者が読み続ける理由を、source-backedな具体から作る。",
                "引き込み: sourceを一覧として消化せず、読者が見ればよい観点へ並べ替える。",
                "具体: assigned claimsを代表例として扱い、数字・名称・条件は正確に書く。",
                "背景: source外の体験や感想を足さず、私たち側の説明として自然につなぐ。",
                "締め: 一般論や強いCTAではなく、読者が次に確認する点へ静かに戻す。",
            ],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [{"claim_id": f"C{i:03d}"} for i in range(1, 7)]
        }
    }

    DraftWriter(client).write(brief, knowledge_pack, [])

    payload_brief = client.calls[0]["payload"]["article_brief"]["article_brief"]
    payload_plan = payload_brief["paragraph_function_plan"]
    assert "読者が見ればよい観点" not in " ".join(payload_plan)
    assert "読者が次に確認する点" not in " ".join(payload_plan)
    assert "sourceを読む順番ではなく" not in " ".join(payload_plan)
    assert "公式情報の確認順ではなく" not in " ".join(payload_plan)
    assert "私たちの仕事・行動・価値" in payload_plan[1]
    assert "私たちが何を大切にしているか" in payload_plan[4]
    assert "どの公式情報を見ると判断しやすいか" not in payload_brief["article_goal"]
    assert "自然に理解できる" not in payload_brief["article_goal"]
    assert "私たちが何を扱い" in payload_brief["article_goal"]
    assert "分かる" not in payload_brief["reading_reward"]
    assert "私たちがどの場面を支え" in payload_brief["reading_reward"]
    assert "source_backed_reader_bridge_policy" not in payload_brief
    assert "company_action_value_bridge_contract" in payload_brief
    assert "どう届け、何を大切にするか" in payload_brief["company_action_value_bridge_contract"]
    assert "読者が次の段落へ進みやすい" not in " ".join(payload_brief["rhythm_break_plan"])
    assert "私たちの仕事・運用・価値" in " ".join(payload_brief["rhythm_break_plan"])
    assert "読み手が次に確認しやすい" not in " ".join(payload_brief["style_rules"])
    assert "仕事・行動・価値" in " ".join(payload_brief["style_rules"])
    assert brief["article_brief"]["paragraph_function_plan"][1].startswith("引き込み: sourceを一覧")


def test_route_v_company_intro_reader_inference_contract_does_not_affect_non_self_authored() -> None:
    client = RecordingClient()
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "source_shape": "announcement_details",
            "style_rules": ["最後は読み手が次に確認しやすい情報の並びで穏やかに締める。"],
            "reading_reward": "何を大切にしている会社かが自然に見えてきます。",
        }
    }

    DraftWriter(client).write(brief, {"article_knowledge_pack": {"confirmed_facts": []}}, [])

    payload_brief = client.calls[0]["payload"]["article_brief"]["article_brief"]
    assert payload_brief["style_rules"] == ["最後は読み手が次に確認しやすい情報の並びで穏やかに締める。"]
    assert payload_brief["reading_reward"] == "何を大切にしている会社かが自然に見えてきます。"
    assert "company_action_value_bridge_contract" not in payload_brief


def test_route_v_draft_writer_adds_non_company_genre_contracts_only_in_route_v() -> None:
    client = RecordingClient()
    route_v_daily = {
        "article_brief": {
            "genre_id": "daily_activity",
            "voice_mode": "self_authored_blogger",
            "target_length_chars": 1200,
            "body_length_floor_chars": 1000,
            "section_count": 3,
        }
    }
    v1_daily = {
        "article_brief": {
            "genre_id": "daily_activity",
            "target_length_chars": 1200,
            "section_count": 3,
        }
    }

    DraftWriter(client).write(route_v_daily, {"article_knowledge_pack": {"confirmed_facts": []}})
    DraftWriter(client).write(v1_daily, {"article_knowledge_pack": {"confirmed_facts": []}})

    route_v_instructions = client.calls[0]["instructions"]
    v1_instructions = client.calls[1]["instructions"]
    assert "diary style is allowed" in route_v_instructions
    assert "third-party feelings, outcomes, or strong causality" in route_v_instructions
    assert "diary style is allowed" not in v1_instructions


def test_route_v_draft_writer_keeps_announcement_compact() -> None:
    client = RecordingClient()
    route_v_announcement = {
        "article_brief": {
            "genre_id": "announcement",
            "voice_mode": "self_authored_blogger",
            "target_length_chars": 1000,
            "body_length_floor_chars": 900,
            "section_count": 2,
            "source_use_mode": "selective",
            "claim_allocation": [
                {"section_id": "S1", "claim_ids": ["C001", "C002", "C003", "C004"], "reuse_allowed": False},
                {"section_id": "S2", "claim_ids": ["C005", "C006", "C007", "C008"], "reuse_allowed": False},
            ],
        }
    }

    DraftWriter(client).write(
        route_v_announcement,
        {"article_knowledge_pack": {"confirmed_facts": [{"claim_id": f"C{i:03d}"} for i in range(1, 9)]}},
    )

    instructions = client.calls[0]["instructions"]
    assert "compact and factual" in instructions
    assert "do not warm it into a diary or long blog essay" in instructions
    assert "Body floor actuation" in instructions
    assert "at least 9 source-grounded body paragraphs" in instructions
    assert "Japanese chars per anchor" not in instructions
    assert "Representative/selective mode is not short-summary mode" in instructions
    assert "do not enumerate unassigned claims" in instructions


def test_daily_activity_short_draft_expands_from_selected_excerpt_scene_material() -> None:
    client = RecordingClient("# Daily\n\n## Scene\n\nShort claim summary.\n\n## Practice\n\nThin note.")
    brief = {
        "article_brief": {
            "genre_id": "daily_activity",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 800,
            "section_count": 2,
            "sections": [
                {"section_id": "s1", "heading": "Scene"},
                {"section_id": "s2", "heading": "Practice"},
            ],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "The workshop opened with a light box, camera lens, shutter, and small material samples.\nThe instructor explained focal length, aperture, shutter speed, and ISO as connected camera settings.",
        },
        {
            "excerpt_id": "E002",
            "section_ids": ["s2"],
            "claim_ids": ["C004"],
            "text": "Participants checked the camera angle, the position of the object, and how the light changed the surface.\nThey compared the same object under different constraints without adding result claims.",
        },
    ]

    result = DraftWriter(client).write(brief, {"article_knowledge_pack": {"confirmed_facts": []}}, excerpts)

    assert "light box, camera lens, shutter" in result
    assert "camera angle, the position of the object" in result
    assert result.index("light box") > result.index("## Scene")
    assert result.index("camera angle") > result.index("## Practice")
    assert "source_documents" not in client.calls[0]["payload"]


def test_daily_activity_followthrough_replays_saved_surface_defects_without_local_artifacts() -> None:
    root = NOTECODE_ROOT / "logs/0626/daily_activity_targeted_rewrite_sentence_split_followthrough_one_article_api_validation_after_approval_20260626_110732"
    draft = (root / "rb/r/draft.md").read_text(encoding="utf-8")
    brief = json.loads((root / "rb/r/article_brief.json").read_text(encoding="utf-8"))
    excerpts = json.loads((root / "rb/r/selected_source_excerpts.json").read_text(encoding="utf-8"))
    knowledge_pack = json.loads((root / "rb/r/article_knowledge_pack.json").read_text(encoding="utf-8"))

    result = DraftWriter(RecordingClient(draft)).write(brief, knowledge_pack, excerpts)
    gate = check_human_visible_surface(result, brief)["human_visible_surface_gate"]

    assert body_chars_excluding_headings(result) >= 1200
    assert gate["pass"] is True
    assert gate["findings"] == []
    assert "私たちの取り組みを、少し具体的に紹介します" not in result
    assert "データの扱いに迷ったときは、小さなことでもご相談ください" not in result
    assert "日時：2026年3。" not in result
    assert "学んでいきました。」を理解する" not in result
    assert "ロボット導入" not in result
    assert "自動販売機" not in result
    assert "10年後の自社" not in result
    assert "ワークショップ」を開催します" not in result
    assert "シャッターを押すと開閉する）のこと" not in result


def test_daily_activity_scene_followthrough_does_not_change_other_genres() -> None:
    draft = "# Article\n\n## Scene\n\nShort claim summary."
    excerpts = [{"excerpt_id": "E001", "section_ids": ["s1"], "claim_ids": ["C001"], "text": "Source scene material with enough detail to be usable."}]
    for genre_id in ["comparison_guide", "case_study"]:
        client = RecordingClient(draft)
        brief = {
            "article_brief": {
                "genre_id": genre_id,
                "voice_mode": "self_authored_blogger",
                "body_length_floor_chars": 800,
                "sections": [{"section_id": "s1", "heading": "Scene"}],
            }
        }

        assert DraftWriter(client).write(brief, {"article_knowledge_pack": {"confirmed_facts": []}}, excerpts) == draft


def test_case_study_surface_followthrough_replays_saved_surface_defects_without_local_artifacts() -> None:
    root = NOTECODE_ROOT / "logs/0625/route_v_case_study_structural_editor_knowledge_pack_payload_contract_one_article_api_validation_after_approval_20260625_152645"
    article = (root / "generated_article.md").read_text(encoding="utf-8")
    brief = {"article_brief": {"genre_id": "case_study", "body_length_floor_chars": 1}}

    result = case_study_surface_followthrough(article, brief)
    gate = check_human_visible_surface(result, brief)["human_visible_surface_gate"]

    assert "# 事例から見える取り組み" in result
    assert "## お客様の状況" in result
    assert "## 私たちが行ったこと" in result
    assert "## 声や変化から見えること" in result
    assert gate["pass"] is True
    assert gate["findings"] == []
    assert "私たちの取り組みを、少し具体的に紹介します" not in result
    assert "データの扱いに迷ったときは、小さなことでもご相談ください" not in result
    assert "さらに、「アナログだった市役所に革命を / 5,000枚以上の紙の日報を廃止！" not in result
    assert "/ 数百人のスタッフの情報共有を円滑に！" not in result


def test_market_explanation_short_draft_expands_from_selected_excerpts() -> None:
    client = RecordingClient(
        "# Market\n\n## Background\n\nShort label summary.\n\n## Use Cases\n\nThin note."
    )
    brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 450,
            "section_count": 2,
            "sections": [
                {"section_id": "s1", "heading": "Background"},
                {"section_id": "s2", "heading": "Use Cases"},
            ],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "2024年10月、関係各方面から広く情報・意見を募集するため、ディスカッションペーパーを公表。\n"
            "公正取引委員会は、生成AI関連市場の公正かつ自由な競争環境を維持し、生成AIの持続的な進展を確保する観点から調査を開始。\n"
            "同調査は、現状の生成AI関連市場の流動的な状況を踏まえ、迅速かつ柔軟な方法で進めることとした。\n"
            "公正取引委員会は、前回ペーパーをアップデートする形で生成AIに関する実態調査報告書ver.1.0を取りまとめた。\n"
            "今後も調査と情報更新を継続していく方針である。",
        },
        {
            "excerpt_id": "E002",
            "section_ids": ["s2"],
            "claim_ids": ["C007"],
            "text": "GENIACは、国内の生成AI開発力強化や情報発信に関する経済産業省の取組です。"
            "GENIAC通信では、採択事業者のキックオフイベント、共創事例、ユースケース、イベントレポートなどが掲載されています。"
            "生成AIのモデル開発だけでなく、建設、医療、研究開発などの現場でどのように使われるかを示す周辺情報として参照できます。"
            "モデル開発と利用現場の両方を見ながら、市場の広がりを確認する材料になります。",
        },
    ]

    result = DraftWriter(client).write(brief, {"article_knowledge_pack": {"confirmed_facts": []}}, excerpts)

    assert "生成AI関連市場の公正かつ自由な競争環境" in result
    assert "GENIAC通信では" in result
    assert result.index("生成AI関連市場の公正") > result.index("## Background")
    assert result.index("GENIAC通信では") > result.index("## Use Cases")
    assert "source_documents" not in client.calls[0]["payload"]
    assert len("".join("".join(line.split()) for line in result.splitlines() if not line.startswith("#"))) >= 450


def test_market_explanation_sanitizes_writer_context_payload_without_mutating_sources() -> None:
    client = RecordingClient("# Market\n\n## Background\n\nShort note.")
    brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 600,
            "section_count": 1,
            "sections": [{"section_id": "s1", "heading": "Background"}],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "生成AIに関する実態調査報告書\nver. 1.0\n令 和 ７ 年 ６ 月\n公 正 取 引 委 員 会\n"
            "J a p a n F a i r T r a d e C o m m i s s i o n\n"
            "公正取引委員会は、生成AI関連市場の実態を把握するための調\n査を開始。\n"
            "（※）本報告書は最終的なものではなく、現時点版としての公表であるため、タイトルに「",
        }
    ]
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C002", "claim": "ver. 1.0 令 和 ７ 年 ６ 月", "preferred_expression": "ver. 1.0 令 和 ７ 年 ６ 月"},
                {"claim_id": "C003", "claim": "公 正 取 引 委 員 会", "preferred_expression": "公 正 取 引 委 員 会"},
                {
                    "claim_id": "C004",
                    "claim": "J a p a n F a i r T r a d e C o m m i s s i o n 生成AIに関する実態調査報告書ver.1.0（概要）",
                    "preferred_expression": "J a p a n F a i r T r a d e C o m m i s s i o n 生成AIに関する実態調査報告書ver.1.0（概要）",
                },
            ]
        }
    }

    DraftWriter(client).write(brief, knowledge_pack, excerpts)

    payload = client.calls[0]["payload"]
    payload_text = str(payload)
    assert "令 和" not in payload_text
    assert "公 正" not in payload_text
    assert "J a p a n" not in payload_text
    assert "タイトルに「" not in payload_text
    assert "公正取引委員会は、生成AI関連市場の実態を把握するための調査を開始。" in payload_text
    assert excerpts[0]["text"].count("令 和") == 1
    assert knowledge_pack["article_knowledge_pack"]["confirmed_facts"][0]["preferred_expression"] == "ver. 1.0 令 和 ７ 年 ６ 月"


def test_market_explanation_followthrough_does_not_touch_floor_reaching_draft() -> None:
    draft = "# Market\n\n## Background\n\n" + ("source-backed sentence." * 80)
    client = RecordingClient(draft)
    brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 650,
            "sections": [{"section_id": "s1", "heading": "Background"}],
        }
    }
    excerpts = [{"excerpt_id": "E001", "section_ids": ["s1"], "claim_ids": ["C001"], "text": "Unused selected excerpt text."}]

    assert DraftWriter(client).write(brief, {"article_knowledge_pack": {"confirmed_facts": []}}, excerpts) == draft
