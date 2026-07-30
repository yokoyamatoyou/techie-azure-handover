from __future__ import annotations

import json
from pathlib import Path

from app.services.announcement_followthrough import announcement_selected_excerpt_floor_followthrough
from app.services.company_intro_followthrough import company_intro_selected_excerpt_floor_followthrough
from app.services.draft_followthrough import (
    body_chars_excluding_headings,
)
from app.services.market_explanation_followthrough import (
    market_explanation_selected_excerpt_floor_followthrough,
    _passes_market_explanation_followthrough_quality_gate,
)
from app.services.human_visible_surface_gate import check_human_visible_surface


NOTECODE_ROOT = Path(__file__).resolve().parents[2]


def test_market_explanation_followthrough_gates_reader_meta_source_viewpoint() -> None:
    draft = "# Market\n\n## Market Use\n\nShort note."
    brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 200,
            "sections": [{"section_id": "s1", "heading": "Market Use"}],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C007"],
            "text": "GENIACは、国内の生成AI開発力強化や情報発信に関する経済産業省の取組です。"
            "GENIAC通信では、採択事業者のキックオフイベント、共創事例、ユースケース、イベントレポートなどが掲載されています。"
            "生成AIのモデル開発だけでなく、建設、医療、研究開発などの現場でどのように使われるかを示す周辺情報として参照できます。",
        }
    ]
    old_reader_meta = "GENIAC通信の共創事例、ユースケース、イベントレポートは、開発力強化だけでなく利用現場の広がりを追う手がかりになります。"
    dense_source_fact = "GENIAC通信には、採択事業者の共創事例、ユースケース、イベントレポートなどの情報発信が含まれます。"

    result = market_explanation_selected_excerpt_floor_followthrough(draft, brief, excerpts)

    assert not _passes_market_explanation_followthrough_quality_gate(old_reader_meta)
    assert _passes_market_explanation_followthrough_quality_gate(dense_source_fact)
    assert old_reader_meta not in result
    assert dense_source_fact in result
    assert body_chars_excluding_headings(result) >= 200


def test_market_explanation_followthrough_sanitizes_saved_artifact_surface_context() -> None:
    draft = "# 市場解説\n\n## ビジネスモデルを考える視点\n\n短い導入です。\n\n## 市場性をどう見立てるか\n\n短い整理です。"
    brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 360,
            "sections": [
                {"section_id": "s1", "heading": "ビジネスモデルを考える視点"},
                {"section_id": "s3", "heading": "市場性をどう見立てるか"},
            ],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "生成AIに関する実態調査報告書\nver. 1.0\n令 和 ７ 年 ６ 月\n公 正 取 引 委 員 会\n"
            "J a p a n F a i r T r a d e C o m m i s s i o n\n"
            "2024年10月、関係各方面から広く情報・意見を募集するため、ディスカッションペーパー「生成AIを巡る競争」（前回ペーパー）を公表。\n"
            "公正取引委員会は、我が国の生成AI関連市場における公正かつ自由な競争環境を維持し、生成AIの持続的な進展を確保することにより、更なる\n"
            "イノベーションを生み出す観点から、生成AI関連市場の実態を把握するための調\n査を開始。\n"
            "（※）本報告書は最終的なものではなく、現時点版としての公表であるため、タイトルに「",
        },
        {
            "excerpt_id": "E002",
            "section_ids": ["s3"],
            "claim_ids": ["C007"],
            "text": "GENIACは、国内の生成AI開発力強化や情報発信に関する経済産業省の取組です。"
            "GENIAC通信では、採択事業者のキックオフイベント、共創事例、ユースケース、イベントレポートなどが掲載されています。"
            "生成AIのモデル開発だけでなく、建設、医療、研究開発などの現場でどのように使われるかを示す周辺情報として参照できます。",
        },
    ]

    result = market_explanation_selected_excerpt_floor_followthrough(draft, brief, excerpts)
    gate = check_human_visible_surface(result, brief)["human_visible_surface_gate"]

    assert gate["pass"] is True
    assert "令 和" not in result
    assert "公 正" not in result
    assert "J a p a n" not in result
    assert "タイトルに「" not in result
    assert "更なる。イノベーション" not in result
    assert body_chars_excluding_headings(result) >= 360


def test_market_explanation_followthrough_uses_sanitized_residual_claims_for_floor_buffer() -> None:
    draft = "# 市場解説\n\n## 見立て方\n\n" + ("私たちは生成AI市場の論点をsourceに基づいて整理します。" * 14)
    brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 500,
            "sections": [{"section_id": "s1", "heading": "見立て方"}],
            "claim_allocation": [{"section_id": "s1", "claim_ids": ["C001", "C002", "C003", "C005"]}],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "短い補助行。\n生成AIのモデル開発だけでなく、建設、医療、研究開発などの現場でどのように使われるかを示す周辺情報として参照できます。",
        }
    ]
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "preferred_expression": "生成AIにはメリットとデメリットの両方が存在"},
                {"claim_id": "C002", "preferred_expression": "GENIAC通信では、採択事業者の共創事例、ユースケース、イベントレポートなどが掲載されています。"},
                {"claim_id": "C003", "preferred_expression": "今後も調査と情報更新を継続していく方針である。"},
                {"claim_id": "C004", "preferred_expression": "ガバメントAIとは、政府職員が安全・安心にAIを活用できる基盤です。"},
                {"claim_id": "C005", "preferred_expression": "公正取引委員会は、生成AI関連市場の実態を把握するための調査を開始した。"},
            ]
        }
    }

    result = market_explanation_selected_excerpt_floor_followthrough(draft, brief, excerpts, knowledge_pack)

    assert "GENIAC通信では" in result
    assert "今後も調査と情報更新" in result
    assert "ガバメントAI" not in result
    assert "source_documents" not in result
    assert body_chars_excluding_headings(result) >= 596


def test_announcement_followthrough_uses_selected_excerpt_and_confirmed_claims() -> None:
    draft = "# お知らせ\n\n## お知らせの概要\n\n短い概要です。\n\n## 変更内容と対象\n\n対象を確認してください。"
    brief = {
        "article_brief": {
            "genre_id": "announcement",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 520,
            "sections": [
                {"section_id": "s1", "heading": "お知らせの概要"},
                {"section_id": "s2", "heading": "変更内容と対象"},
            ],
            "claim_allocation": [
                {"section_id": "s1", "claim_ids": ["C001", "C002"]},
                {"section_id": "s2", "claim_ids": ["C003", "C004"]},
            ],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001"],
            "text": "現在位置\nホーム\n公開日:\n2026年5月28日\n"
            "デジタル庁においては、ガバメントAIに係る取組の一環として、デジタル庁全職員が利用できる生成AI利用環境（プロジェクト名：源内（げんない））の構築・運営を行ってきましたが、令和8年（2026年）5月より大規模実証実験を開始しました。\n"
            "5月29日時点では、約10万人の政府職員が源内を利用可能な状況となります。今後、順次対象府省庁・職員数を拡大し、全府省庁の約18万人が利用できるよう環境整備を進めてまいります。",
        }
    ]
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "preferred_expression": "全府省庁の約18万人の政府職員を対象としたガバメントAI（源内）の大規模実証を開始しました"},
                {"claim_id": "C002", "preferred_expression": "2026年5月28日"},
                {"claim_id": "C003", "preferred_expression": "5月29日時点では、約10万人の政府職員が源内を利用可能な状況となります。"},
                {"claim_id": "C004", "preferred_expression": "ガバメントAIとは、政府職員が安全・安心にAIを活用できる基盤です。"},
            ]
        }
    }

    result = announcement_selected_excerpt_floor_followthrough(draft, brief, excerpts, knowledge_pack)

    assert "当社では、ガバメントAIに係る取組の一環として" in result
    assert "約10万人の政府職員" in result
    assert "安全・安心にAIを活用できる基盤" in result
    assert "現在位置" not in result
    assert "source_documents" not in result
    assert body_chars_excluding_headings(result) >= 520


def test_announcement_followthrough_sanitizes_saved_surface_findings_without_source_packets() -> None:
    root = NOTECODE_ROOT / "logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260626_194056"
    article = (root / "generated_article.md").read_text(encoding="utf-8")
    brief = json.loads((root / "rb/r/article_brief.json").read_text(encoding="utf-8"))
    excerpts = json.loads((root / "rb/r/selected_source_excerpts.json").read_text(encoding="utf-8"))
    knowledge_pack = json.loads((root / "rb/r/article_knowledge_pack.json").read_text(encoding="utf-8"))

    result = announcement_selected_excerpt_floor_followthrough(article, brief, excerpts, knowledge_pack)
    gate = check_human_visible_surface(result, brief)["human_visible_surface_gate"]

    assert gate["pass"] is True
    assert gate["findings"] == []
    assert body_chars_excluding_headings(result) >= 900


def test_announcement_followthrough_replays_latest_live_underfill_to_floor() -> None:
    roots = [
        NOTECODE_ROOT / "logs/0628/route_v_announcement_local_surface_sanitization_one_article_api_validation_after_approval_20260628_105216",
        NOTECODE_ROOT / "logs/0628/route_v_announcement_live_floor_buffer_h2_preservation_one_article_api_validation_after_approval_20260628_111853",
    ]
    for root in roots:
        draft = (root / "rb/r/draft.md").read_text(encoding="utf-8")
        brief = json.loads((root / "rb/r/article_brief.json").read_text(encoding="utf-8"))
        excerpts = json.loads((root / "rb/r/selected_source_excerpts.json").read_text(encoding="utf-8"))
        knowledge_pack = json.loads((root / "rb/r/article_knowledge_pack.json").read_text(encoding="utf-8"))

        result = announcement_selected_excerpt_floor_followthrough(draft, brief, excerpts, knowledge_pack)

        assert body_chars_excluding_headings(draft) < 900
        assert body_chars_excluding_headings(result) >= 930
        assert "source_documents" not in result


def test_company_intro_followthrough_uses_selected_excerpts_and_confirmed_claims() -> None:
    draft = "# 会社紹介\n\n## 私たちの仕事\n\n短い紹介です。\n\n## 届け方と考え方\n\n概要だけです。"
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 300,
            "narrator": "私たち",
            "self_viewpoint_owner": "山陰酸素",
            "sections": [
                {"section_id": "s1", "heading": "私たちの仕事"},
                {"section_id": "s2", "heading": "届け方と考え方"},
            ],
            "claim_allocation": [
                {"section_id": "s1", "claim_ids": ["C001", "C002"]},
                {"section_id": "s2", "claim_ids": ["C003", "C004"]},
            ],
        }
    }
    excerpts = [
        {
            "excerpt_id": "E001",
            "section_ids": ["s1"],
            "claim_ids": ["C001", "C002"],
            "text": "山陰酸素は、LPガス、産業用ガス、医療用ガスなどを地域の暮らしと事業活動に向けて供給しています。\n"
            "山陰酸素は、家庭向けのエネルギーだけでなく、工場、医療現場、研究開発の場面にも関わる商品を扱っています。",
        },
        {
            "excerpt_id": "E002",
            "section_ids": ["s2"],
            "claim_ids": ["C003", "C004"],
            "text": "山陰酸素は、地域の安全な利用を支えるため、点検、配送、相談対応を日々の接点として続けています。\n"
            "山陰酸素は、事業を通じて地域社会の基盤を支える姿勢を大切にしています。",
        },
    ]
    knowledge_pack = {
        "article_knowledge_pack": {
            "confirmed_facts": [
                {"claim_id": "C001", "preferred_expression": "山陰酸素はLPガス、産業用ガス、医療用ガスを扱っています"},
                {"claim_id": "C002", "preferred_expression": "山陰酸素は家庭、工場、医療現場、研究開発の場面に関わる商品を扱っています"},
                {"claim_id": "C003", "preferred_expression": "山陰酸素は点検、配送、相談対応を日々の接点として続けています"},
                {"claim_id": "C004", "preferred_expression": "山陰酸素は地域社会の基盤を支える姿勢を大切にしています"},
            ]
        }
    }

    result = company_intro_selected_excerpt_floor_followthrough(draft, brief, excerpts, knowledge_pack)

    assert "私たちは、LPガス、産業用ガス、医療用ガス" in result
    assert "私たちは、地域の安全な利用を支えるため" in result
    assert "山陰酸素は" not in result
    assert "source_documents" not in result
    assert result.index("LPガス") > result.index("## 私たちの仕事")
    assert result.index("地域の安全な利用") > result.index("## 届け方と考え方")
    assert body_chars_excluding_headings(result) >= 300


def test_company_intro_followthrough_does_not_touch_floor_reaching_draft() -> None:
    draft = "# 会社紹介\n\n## 私たちの仕事\n\n" + ("私たちはsourceに基づいて仕事を説明します。" * 40)
    brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "body_length_floor_chars": 500,
            "sections": [{"section_id": "s1", "heading": "私たちの仕事"}],
        }
    }
    excerpts = [{"excerpt_id": "E001", "section_ids": ["s1"], "text": "山陰酸素は、追加の説明材料を持っています。"}]

    assert company_intro_selected_excerpt_floor_followthrough(draft, brief, excerpts, None) == draft
