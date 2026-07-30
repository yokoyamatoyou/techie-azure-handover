from app.agents.article_brief_builder import _enforce_depth_contract
from app.services.local_llm_client import LocalPipelineClient
from app.services.pipeline_logging import PipelineLogger
from app.services.pipeline_runner import BlogPipelineRunner


def _run_with_text(tmp_path, text: str):
    runner = BlogPipelineRunner(
        client=LocalPipelineClient(),
        logger=PipelineLogger("length_case", artifacts_dir=tmp_path),
    )
    return runner.run_manual_sources([("長さテスト", text)], narrator="私たち").article_brief["article_brief"]


def test_article_brief_length_plan_changes_with_source_claim_count(tmp_path):
    thin = _run_with_text(tmp_path / "thin", "私たちは相談を受けています。")
    medium = _run_with_text(
        tmp_path / "medium",
        "私たちは2018年に創業しました。地域の相談を受けています。初回相談で状況を確認します。",
    )
    thick = _run_with_text(
        tmp_path / "thick",
        (
            "私たちは2018年に創業しました。地域の相談を受けています。初回相談で状況を確認します。"
            "担当者が内容を整理します。次に取れる選択肢を説明します。必要な資料を案内します。"
        ),
    )

    assert thin["source_thickness"] == "thin"
    assert thin["target_length_chars"] == 700
    assert thin["section_count"] == 1
    assert medium["source_thickness"] == "medium"
    assert medium["target_length_chars"] == 1200
    assert medium["section_count"] == 2
    assert medium["style_profile_id"] == "note_hatena_owned_media_soft"
    assert medium["style_edit_policy"]["preferred_sentences_per_paragraph"] == 2
    assert medium["editor_profile_id"] == "note_hatena_structural_editor"
    assert thick["source_thickness"] == "thick"
    assert thick["target_length_chars"] == 1800
    assert thick["section_count"] == 3


def test_announcement_length_plan_is_more_compact(tmp_path):
    runner = BlogPipelineRunner(
        client=LocalPipelineClient(),
        logger=PipelineLogger("announcement_length", artifacts_dir=tmp_path),
    )
    result = runner.run_manual_sources(
        [
            (
                "お知らせ",
                (
                    "当社は2026年6月1日から受付時間を変更します。平日の受付時間は9時から17時までです。"
                    "土曜日の受付は事前予約制です。対象は既存の利用者と新規相談者です。"
                ),
            )
        ],
        genre_id="announcement",
        narrator="当社",
    )
    brief = result.article_brief["article_brief"]

    assert brief["target_length_chars"] == 1000
    assert brief["section_count"] == 2
    assert brief["sections"][0]["heading"] == "お知らせの概要"
    assert brief["style_profile_id"] == "formal_notice_compact"
    assert brief["style_edit_policy"]["subject_omission_policy"] == "protected_facts_explicit"


def test_blog_persona_profile_adds_compact_style_rule_without_changing_viewpoint(tmp_path):
    runner = BlogPipelineRunner(
        client=LocalPipelineClient(),
        logger=PipelineLogger("persona_profile", artifacts_dir=tmp_path),
    )
    result = runner.run_manual_sources(
        [("会社メモ", "私たちは資料整理と入力支援を行っています。大学や企業の相談を受けています。" * 3)],
        narrator="私たち",
        self_viewpoint_owner="株式会社A",
        blog_persona_profile={
            "label": "ユーモアのあるサービス紹介担当",
            "profile_id": "humorous_service_pr",
            "style_rule": "軽いユーモアは比喩や言い回しに限定。自己視点を崩さず、サービス説明は明瞭にする。",
        },
    )
    brief = result.article_brief["article_brief"]

    assert brief["viewpoint_mode"] == "self_perspective"
    assert brief["narrator"] == "私たち"
    assert brief["self_viewpoint_owner"] == "株式会社A"
    assert "同社" in brief["forbidden_viewpoint_terms"]
    assert "軽いユーモアは比喩や言い回しに限定" in " ".join(brief["style_rules"])
    assert "ユーモアのあるサービス紹介担当" in brief["persona_refs"]


def test_thick_source_depth_contract_expands_concise_section_rules():
    article_brief = {
        "article_brief": {
            "target_length_chars": 3000,
            "source_thickness": "thick",
            "style_rules": ["既存の文体ルール"],
            "sections": [
                {
                    "section_id": "sec_001",
                    "assigned_claim_ids": ["C001", "C002", "C003"],
                    "discourse_rules": ["読者に分かりやすく分類し簡潔に列挙"],
                },
                {
                    "section_id": "sec_002",
                    "assigned_claim_ids": ["C004", "C005"],
                    "discourse_rules": ["料金は一例を簡潔に列挙", "会社情報は箇条書き的にまとめる"],
                },
            ],
        }
    }
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [{"claim_id": f"C{i:03d}"} for i in range(1, 17)]
        }
    }

    _enforce_depth_contract(article_brief, knowledge_pack)

    brief = article_brief["article_brief"]
    all_rules = " ".join(brief["style_rules"])
    section_rules = " ".join(
        rule
        for section in brief["sections"]
        for rule in section["discourse_rules"]
    )
    assert "短い要約で終えず" in all_rules
    assert "target_length_charsは水増しではなく" in all_rules
    assert "簡潔に列挙" not in section_rules
    assert "箇条書き的にまとめる" not in section_rules
    assert "分類して説明し、主要項目には1文ずつ文脈を添える" in section_rules
    assert "代表例を整理し、それぞれの見方を短く添える" in section_rules
    assert "割り当てclaim 3件を短く列挙して終えず" in section_rules
