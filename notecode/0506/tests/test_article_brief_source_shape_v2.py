from app.agents.article_brief_builder import ArticleBriefBuilder
from app.agents.draft_writer import _build_draft_writer_instructions
from app.services.article_brief_source_shape_v2 import apply_source_shape_v2, detect_claim_reuse_violations, detect_source_shape
from app.services.local_llm_client import LocalPipelineClient
from app.services.openai_schema_compat import schema_for_openai_response_format
from app.services.schema_validator import load_schema


def _knowledge_pack(claim_texts: list[str], *, source_card_ids: list[str] | None = None) -> dict:
    return {
        "article_knowledge_pack": {
            "pack_id": "pack_source_shape",
            "source_card_ids": source_card_ids or ["manual_001"],
            "confirmed_facts": [
                {
                    "claim_id": f"C{index:03d}",
                    "claim": text,
                    "supporting_fact_ids": [f"F{index:03d}"],
                    "confidence": "medium",
                    "preferred_expression": text,
                    "risk_flags": [],
                }
                for index, text in enumerate(claim_texts, start=1)
            ],
            "conflicts": [],
            "deduped_themes": ["source_shape_fixture"],
            "do_not_infer": ["ソースにない価格、実績、効果を追加しない"],
        }
    }


def _build_brief(
    monkeypatch,
    claims: list[str],
    goal: str,
    *,
    genre_id: str = "company_service_intro",
    source_card_ids: list[str] | None = None,
) -> dict:
    monkeypatch.setenv("ROUTE_V_ARTICLE_BRIEF_ALGORITHM", "v2")
    return ArticleBriefBuilder(LocalPipelineClient()).build(
        _knowledge_pack(claims, source_card_ids=source_card_ids),
        genre_id=genre_id,
        target_reader="読者",
        article_goal=goal,
        narrator="私たち",
        self_viewpoint_owner="株式会社A",
    )["article_brief"]


def _assigned_claim_ids(brief: dict) -> list[str]:
    return [claim_id for section in brief["sections"] for claim_id in section["assigned_claim_ids"]]


def _assert_claim_inventory_consistent(brief: dict, claim_count: int) -> None:
    assigned = _assigned_claim_ids(brief)
    allocated = [claim_id for allocation in brief["claim_allocation"] for claim_id in allocation["claim_ids"]]

    assert allocated == assigned
    assert all(allocation["reuse_allowed"] is False for allocation in brief["claim_allocation"])
    assert not detect_claim_reuse_violations({"article_brief": brief})
    assert set(assigned).isdisjoint(set(brief["unassigned_claim_ids"]))
    assert set(assigned + brief["unassigned_claim_ids"]) == {f"C{index:03d}" for index in range(1, claim_count + 1)}


def test_default_v1_does_not_emit_source_shape_fields(monkeypatch):
    monkeypatch.delenv("ROUTE_V_ARTICLE_BRIEF_ALGORITHM", raising=False)

    brief = ArticleBriefBuilder(LocalPipelineClient()).build(
        _knowledge_pack(["私たちは資料整理を支援しています。", "初回相談で状況を確認します。"]),
        genre_id="company_service_intro",
        target_reader="読者",
        article_goal="サービスを紹介する",
    )["article_brief"]

    assert "source_shape" not in brief
    assert "source_use_mode" not in brief
    assert "unassigned_claim_ids" not in brief
    assert "voice_mode" not in brief
    assert "reader_arrival_context" not in brief
    assert "interest_hook" not in brief
    assert "comparison_target_category" not in brief
    assert "paragraph_function_plan" not in brief
    assert "body_length_floor_chars" not in brief
    assert "source_derived_aside_policy" not in brief
    assert "rhythm_break_plan" not in brief
    assert "aside_allowed_claim_ids" not in brief
    assert "source_backed_reader_bridge_policy" not in brief
    assert "daily_activity_source_role_contract" not in brief


def test_openai_schema_excludes_v2_experimental_fields_from_strict_response_schema():
    schema = schema_for_openai_response_format(load_schema("article_brief.schema.json"))
    brief_properties = schema["properties"]["article_brief"]["properties"]

    assert "source_shape" not in brief_properties
    assert "source_use_mode" not in brief_properties
    assert "unassigned_claim_ids" not in brief_properties
    assert "voice_mode" not in brief_properties
    assert "reader_arrival_context" not in brief_properties
    assert "interest_hook" not in brief_properties
    assert "reading_reward" not in brief_properties
    assert "self_authored_angle" not in brief_properties
    assert "comparison_target_category" not in brief_properties
    assert "paragraph_function_plan" not in brief_properties
    assert "body_length_floor_chars" not in brief_properties
    assert "source_derived_aside_policy" not in brief_properties
    assert "rhythm_break_plan" not in brief_properties
    assert "aside_allowed_claim_ids" not in brief_properties
    assert "source_backed_reader_bridge_policy" not in brief_properties
    assert "daily_activity_source_role_contract" not in brief_properties


def test_v2_table_or_list_uses_representative_mode_without_all_claim_consumption(monkeypatch):
    claims = [
        "ライトプランは月額10,000円です。",
        "スタンダードプランは月額20,000円です。",
        "プレミアムプランは月額30,000円です。",
        "初期費用は50,000円です。",
        "オプションAは5,000円です。",
        "オプションBは8,000円です。",
        "料金表にはサポート範囲の項目があります。",
        "一覧には契約期間の項目があります。",
        "税込価格の注意事項があります。",
        "支払い方法の項目があります。",
    ]

    brief = _build_brief(monkeypatch, claims, "料金表を自然な記事として紹介する")
    assigned = [claim_id for section in brief["sections"] for claim_id in section["assigned_claim_ids"]]

    assert brief["source_shape"] == "table_or_list"
    assert brief["source_use_mode"] == "representative"
    assert brief["section_count"] < 5
    assert brief["target_length_chars"] >= 1500
    assert brief["voice_mode"] == "self_authored_blogger"
    assert "ざっと見に来ている" in brief["reader_arrival_context"]
    assert "料金表" in brief["interest_hook"]
    assert "paragraph_function_plan" in brief
    assert "source_derived_aside_policy" in brief
    assert "体験談" in brief["source_derived_aside_policy"]
    assert brief["rhythm_break_plan"]
    assert brief["aside_allowed_claim_ids"] == assigned[:3]
    assert len(assigned) < len(claims)
    assert len(brief["unassigned_claim_ids"]) == len(claims) - len(assigned)
    assert set(assigned + brief["unassigned_claim_ids"]) == {f"C{index:03d}" for index in range(1, 11)}
    _assert_claim_inventory_consistent(brief, len(claims))


def test_v2_company_intro_with_prices_and_profile_does_not_become_table_article(monkeypatch):
    claims = [
        "京都工業株式会社は1885年に創業しました。",
        "京都工業株式会社は京都市伏見区に本社があります。",
        "代表者は吉川毅です。",
        "事業内容はデータ入力業務、運用管理、アプリケーション開発です。",
        "京都工業株式会社はデータ入力とスキャニングを提供しています。",
        "RPAによる業務効率化支援を提供しています。",
        "名刺入力は38円からです。",
        "アンケート入力・集計は1.5円からです。",
        "ハガキ入力・集計は20円からです。",
        "原稿・冊子情報は0.5円からです。",
        "音声テープ起こしは200円からです。",
    ]

    brief = _build_brief(monkeypatch, claims, "京都工業株式会社の会社紹介ブログを書く")

    assert brief["source_shape"] == "mixed"
    assert brief["source_use_mode"] == "representative"
    assert "検索結果やサムネイル" in brief["reader_arrival_context"]
    assert "会社説明から始めず" in brief["interest_hook"]
    assert "料金表" not in brief["interest_hook"]
    assert "source_backed_reader_bridge_policy" in brief
    _assert_claim_inventory_consistent(brief, len(claims))


def test_v2_service_catalog_selective_can_use_more_than_section_double_when_source_is_thick(monkeypatch):
    claims = [
        "私たちは業務改善サービスを提供しています。",
        "問い合わせ内容に応じて初期相談に対応します。",
        "導入前の課題整理を支援します。",
        "業務フローの確認を行います。",
        "運用開始後の見直しメニューがあります。",
        "社内共有の進め方を一緒に整理します。",
        "現場ごとの利用状況を確認します。",
        "管理者向けの設定確認を行います。",
        "入力画面の使いやすさを点検します。",
        "利用部門ごとの権限を整理します。",
        "移行前のデータ形式を確認します。",
        "定着に向けた説明会を準備します。",
        "社内問い合わせの受け方を整理します。",
        "運用ルールの見直しを行います。",
        "利用開始後の改善相談を受けます。",
        "部署横断の情報共有を支えます。",
        "既存資料の整理を手伝います。",
        "管理台帳の見直しを行います。",
        "承認フローの確認を行います。",
        "社内通知の運用方法を整理します。",
        "問い合わせ履歴の残し方を確認します。",
        "利用者向けの説明資料を準備します。",
        "継続利用時の確認事項をまとめます。",
        "改善候補の優先順位を整理します。",
    ]

    brief = _build_brief(monkeypatch, claims, "サービス内容を自然な記事として紹介する")
    assigned = _assigned_claim_ids(brief)

    assert brief["source_shape"] == "service_catalog"
    assert brief["source_use_mode"] == "selective"
    assert brief["section_count"] == 3
    assert brief["target_length_chars"] >= brief["body_length_floor_chars"] + 200
    assert len(assigned) > brief["section_count"] * 2
    assert 8 <= len(assigned) <= 10
    assert len(brief["unassigned_claim_ids"]) == len(claims) - len(assigned)
    _assert_claim_inventory_consistent(brief, len(claims))


def test_v2_filters_writer_guidance_that_points_to_unassigned_topics() -> None:
    claims = [
        "生成AI市場の全体像を整理している。",
        "市場規模は2023年から2030年に伸びる推計である。",
        "GPUは生成AIの計算資源として重要である。",
        "データ品質が用途によって重視される。",
        "専門人材の需要が増えている。",
        "アプリケーションレイヤーの競争が激化している。",
        "クラウドサービス市場では大手3社が先行している。",
        "海外事業者を中心に競争がある。",
        "生成AIモデルの開発競争が活発である。",
        "開発環境の整備が競争条件になっている。",
        "政府職員向けの生成AI利用環境『源内』が展開されている。",
        "GENIACは国内の生成AI開発力強化支援施策である。",
    ]
    knowledge_pack = _knowledge_pack(claims)
    article_brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "target_length_chars": 1500,
            "source_thickness": "medium",
            "sections": [
                {"section_id": "s1", "heading": "全体像", "purpose": "市場を見る。", "assigned_claim_ids": ["C001"], "main_subject": "市場", "discourse_rules": ["市場全体を扱う。"]},
                {"section_id": "s2", "heading": "土台", "purpose": "GPUを見る。", "assigned_claim_ids": ["C002"], "main_subject": "GPU", "discourse_rules": ["GPUとデータを扱う。"]},
                {"section_id": "s3", "heading": "競争", "purpose": "政府職員向け源内の話へ広げる。", "assigned_claim_ids": ["C003"], "main_subject": "クラウドとGENIAC", "discourse_rules": ["GENIACと源内を詳しく扱う。", "クラウド競争を扱う。"]},
            ],
            "style_rules": ["前半は市場、中盤はGPU、後半は政府実装と支援施策へ流す。", "数字は確認済み表現を守る。"],
        }
    }

    apply_source_shape_v2(article_brief, knowledge_pack, article_goal="生成AI市場とサービスの構造を解説する")

    brief = article_brief["article_brief"]
    assert "C011" in brief["unassigned_claim_ids"]
    assert "C012" in brief["unassigned_claim_ids"]
    assert all("政府実装" not in rule and "支援施策" not in rule for rule in brief["style_rules"])
    assert brief["sections"][2]["purpose"] == "assigned_claim_idsの範囲で扱う。"
    assert brief["sections"][2]["main_subject"] == "assigned_claim_idsの範囲で扱う。"
    assert "GENIACと源内を詳しく扱う。" not in brief["sections"][2]["discourse_rules"]
    assert "クラウド競争を扱う。" in brief["sections"][2]["discourse_rules"]
    _assert_claim_inventory_consistent(brief, len(claims))


def test_v2_announcement_details_selective_uses_bounded_soft_cap_when_source_is_thick(monkeypatch):
    claims = [
        "お知らせでは2026年7月1日に新しい受付を開始します。",
        "対象は既存利用者と新規相談者です。",
        "受付日時は平日9時から17時までです。",
        "説明会は2026年7月15日に開催します。",
        "申し込みはWebフォームで受け付けます。",
        "受付終了日は2026年8月31日です。",
        "問い合わせ先はサポート窓口です。",
        "参加前に確認事項の提出が必要です。",
        "会場は本社セミナールームです。",
        "オンライン参加にも対応します。",
        "資料は当日に配布します。",
        "変更がある場合は公式サイトで案内します。",
    ]

    brief = _build_brief(
        monkeypatch,
        claims,
        "お知らせを伝える",
        genre_id="announcement",
    )
    assigned = _assigned_claim_ids(brief)

    assert brief["source_shape"] == "announcement_details"
    assert brief["source_use_mode"] == "selective"
    assert brief["section_count"] == 2
    assert brief["target_length_chars"] == 1200
    assert len(assigned) > 4
    assert 6 <= len(assigned) <= 8
    assert len(assigned) < len(claims)
    _assert_claim_inventory_consistent(brief, len(claims))


def test_v2_daily_activity_announcement_shape_uses_more_than_four_claims_when_source_is_thick(monkeypatch):
    claims = [
        "お知らせでは2026年3月10日にワークショップを開催しました。",
        "対象は初心者向けの商品撮影に関心がある参加者です。",
        "受付日時は当日の午前です。",
        "会場では撮影用の背景紙を使いました。",
        "参加者は照明の当て方を確認しました。",
        "講師は道具の置き方を説明しました。",
        "商品を台の上に置いて撮影しました。",
        "スマートフォンで撮る手順も確認しました。",
        "活動後に道具を片付けました。",
        "資料は会場で配布しました。",
        "次回の案内は公式サイトで知らせます。",
        "申し込みはWebフォームで受け付けました。",
        "終了後に質問時間を設けました。",
    ]

    brief = _build_brief(
        monkeypatch,
        claims,
        "日常のできごとを伝える",
        genre_id="daily_activity",
    )
    assigned = _assigned_claim_ids(brief)

    assert brief["source_shape"] == "announcement_details"
    assert brief["source_use_mode"] == "selective"
    assert brief["section_count"] == 2
    assert brief["body_length_floor_chars"] <= 1200
    assert len(assigned) > 4
    assert 6 <= len(assigned) <= 8
    _assert_claim_inventory_consistent(brief, len(claims))


def test_v2_daily_activity_separates_primary_scene_from_auxiliary_notice_and_listing(monkeypatch):
    claims = [
        "2026年3月10日に、宮城県産業技術総合センターの商品開発支援班の職員が講師を務める初心者向けの物撮り（商品撮影）ワークショップが開催された。",
        "募集案内では、2026年3月10日（火）13:30～16:30にBW-03室で開催、受講料1,200円（税込）、定員5人、申込締切2026/2/10（火）とされていた。",
        "ワークショップは「講義」と「実技」の二部構成で実施された。",
        "講義では、デジタルカメラの基本構造と、焦点距離・絞り値・シャッタースピード・ISO感度の関係が説明された。",
        "実技では、プラスチックのおもちゃ、透明な瓶、反射の強い金属部品を題材に撮影を体験した。",
        "撮影には市販のクリップライトやデスクランプを使い、光の位置を変えて影やハイライトの変化を確認した。",
        "透明な瓶の撮影では、黒いボール紙を写り込ませて輪郭を強調する「黒締め」を試した。",
        "反射する金属部品の撮影では、トレーシングペーパーで光を拡散させる特設ブースを作り、斜め後方から柔らかい光を当てた。",
        "このワークショップをもって、今年度の『商品開発系』研修・セミナーはすべて終了した。",
        "『高度技術者養成研修 活動報告一覧』は、活動報告やお知らせをまとめた一覧ページである。",
        "この一覧ページには、2026年7月30日の構想セミナー案内や、2025～2024年の各種研修報告など、複数の異なるテーマの投稿が含まれている。",
    ]

    brief = _build_brief(
        monkeypatch,
        claims,
        "物撮りワークショップ当日の講義、実技、道具、流れを、私たちの視点で日常記事として伝える。",
        genre_id="daily_activity",
    )
    assigned = _assigned_claim_ids(brief)
    contract = brief["daily_activity_source_role_contract"]

    assert "C001" in contract["primary_scene_report_claim_ids"]
    assert "C003" in contract["primary_scene_report_claim_ids"]
    assert "C006" in contract["primary_scene_report_claim_ids"]
    assert "C002" in contract["auxiliary_context_claim_ids"]
    assert "C010" in contract["auxiliary_suppressed_claim_ids"]
    assert "C011" in contract["auxiliary_suppressed_claim_ids"]
    assert "C002" in contract["scene_material_claim_ids"]
    assert "C002" not in assigned
    assert "C010" not in assigned
    assert "C011" not in assigned
    assert assigned == contract["body_beat_claim_ids"]
    assert contract["raw_source_handoff_allowed"] is False
    assert "source_documents" not in brief
    assert "source_packets" not in brief
    assert "source_cards" not in brief
    assert any("募集案内・一覧ページ" in rule for rule in brief["style_rules"])
    _assert_claim_inventory_consistent(brief, len(claims))


def test_detects_table_or_list_from_article_goal_when_claims_are_compressed():
    shape = detect_source_shape(
        _knowledge_pack(["Aコースの利用条件があります。", "Bコースの利用条件があります。"]),
        article_goal="料金表をもとに代表的な違いを紹介する",
    )

    assert shape == "table_or_list"


def test_v2_faq_uses_selective_mode(monkeypatch):
    claims = [
        "Q. 申し込みはできますか？ A. Webフォームから申し込みできます。",
        "Q. キャンセルできますか？ A. 期限内なら変更できます。",
        "Q. 支払い方法は何ですか？ A. 請求書払いに対応しています。",
        "Q. サポート対象は何ですか？ A. 初期設定を支援します。",
        "Q. 法人利用できますか？ A. 法人で利用できます。",
        "Q. 追加費用はありますか？ A. オプションにより異なります。",
    ]

    brief = _build_brief(monkeypatch, claims, "FAQから読者に必要な質問を選んで紹介する")

    assert brief["source_shape"] == "faq"
    assert brief["source_use_mode"] == "selective"
    assert brief["section_count"] == 2
    assert brief["unassigned_claim_ids"]
    _assert_claim_inventory_consistent(brief, len(claims))


def test_v2_faq_selective_does_not_expand_to_all_questions(monkeypatch):
    claims = [
        "Q. 申し込みはできますか？ A. Webフォームから申し込みできます。",
        "Q. キャンセルできますか？ A. 期限内なら変更できます。",
        "Q. 支払い方法は何ですか？ A. 請求書払いに対応しています。",
        "Q. サポート対象は何ですか？ A. 初期設定を支援します。",
        "Q. 法人利用できますか？ A. 法人で利用できます。",
        "Q. 追加費用はありますか？ A. オプションにより異なります。",
        "Q. 契約期間はありますか？ A. 利用条件により異なります。",
        "Q. 資料請求はできますか？ A. 問い合わせフォームから依頼できます。",
        "Q. 導入相談はできますか？ A. 初回相談を受け付けています。",
        "Q. 変更手続きはできますか？ A. 窓口で確認できます。",
        "Q. 利用開始日は選べますか？ A. 申し込み時に確認します。",
        "Q. 請求書は発行できますか？ A. 契約内容に応じて発行します。",
    ]

    brief = _build_brief(monkeypatch, claims, "FAQから読者に必要な質問を選んで紹介する")
    assigned = _assigned_claim_ids(brief)

    assert brief["source_shape"] == "faq"
    assert brief["source_use_mode"] == "selective"
    assert len(assigned) <= 6
    assert len(assigned) < len(claims)
    _assert_claim_inventory_consistent(brief, len(claims))


def test_v2_announcement_details_can_be_exhaustive_when_goal_explicit(monkeypatch):
    claims = [
        "お知らせでは2026年7月1日から受付時間を変更します。",
        "対象は既存利用者と新規相談者です。",
        "受付時間は平日9時から17時までです。",
        "土曜日は事前予約制です。",
        "申込方法はWebフォームです。",
        "終了日は2026年8月31日です。",
        "問い合わせ先はサポート窓口です。",
    ]

    brief = _build_brief(monkeypatch, claims, "お知らせの全項目を紹介する")
    assigned = [claim_id for section in brief["sections"] for claim_id in section["assigned_claim_ids"]]

    assert brief["source_shape"] == "announcement_details"
    assert brief["source_use_mode"] == "exhaustive"
    assert assigned == [f"C{index:03d}" for index in range(1, 8)]
    assert brief["unassigned_claim_ids"] == []
    _assert_claim_inventory_consistent(brief, len(claims))


def test_detects_reused_claim_id_when_reuse_is_not_allowed():
    article_brief = {
        "article_brief": {
            "claim_allocation": [
                {"section_id": "s1", "claim_ids": ["C001", "C002"], "reuse_allowed": False},
                {"section_id": "s2", "claim_ids": ["C001"], "reuse_allowed": False},
            ]
        }
    }

    problems = detect_claim_reuse_violations(article_brief)

    assert problems == ["claim_id reused with reuse_allowed=false: C001 in s1 and s2"]


def test_v2_keeps_self_perspective_and_third_party_ban(monkeypatch):
    brief = _build_brief(
        monkeypatch,
        ["株式会社Aは資料整理を支援しています。", "株式会社Aは初回相談で状況を確認します。"],
        "会社紹介を書く",
    )

    assert brief["viewpoint_mode"] == "self_perspective"
    assert brief["narrator"] == "私たち"
    assert brief["self_viewpoint_owner"] == "株式会社A"
    assert "同社" in brief["forbidden_viewpoint_terms"]


def test_v2_company_intro_uses_low_intent_visitor_contract(monkeypatch):
    brief = _build_brief(
        monkeypatch,
        [
            "株式会社Aは食品卸売業を営んでいます。",
            "株式会社Aは冷凍食品を取り扱っています。",
            "株式会社Aは学校給食向けの商品を扱っています。",
            "株式会社Aは業務用食材を提供しています。",
        ],
        "会社の紹介を書く",
    )

    assert brief["voice_mode"] == "self_authored_blogger"
    assert "検索結果" in brief["reader_arrival_context"]
    assert "サムネイル" in brief["reader_arrival_context"]
    assert "会社に強い関心がある前提にしない" in brief["reader_arrival_context"]
    assert "暮らし・仕事・選定・運用・知見" in brief["interest_hook"]
    assert "日々のどの場面" in brief["reading_reward"]
    assert "どんな人・運用・考え方" in brief["reading_reward"]
    assert "自分たちの仕事" in brief["self_authored_angle"]
    assert "商品カタログ" in brief["self_authored_angle"]
    assert "検索・サムネイル経由" in brief["paragraph_function_plan"][0]
    assert "運用・知見" in brief["paragraph_function_plan"][0]
    assert "sourceを読む順番ではなく" in brief["paragraph_function_plan"][1]
    assert "公式情報の確認順ではなく" in brief["paragraph_function_plan"][4]
    assert any("低関心読者" in rule and "人・文化・採用・裏側" in rule for rule in brief["style_rules"])
    assert any("公式ページの読み方を教える文にせず" in rule for rule in brief["style_rules"])
    assert "地名・用途・対象者・事業語" in brief["source_backed_reader_bridge_policy"]
    assert "暮らし・仕事・地域・選定・運用" in brief["source_backed_reader_bridge_policy"]
    assert "読む順番や確認先として案内せず" in brief["source_backed_reader_bridge_policy"]
    assert "地域シェア・優位性・顧客感情・中心性は足さない" in brief["source_backed_reader_bridge_policy"]
    assert brief["body_length_floor_chars"] >= 1400
    assert brief["target_length_chars"] >= brief["body_length_floor_chars"] + 200


def test_v2_daily_activity_uses_diary_contract_without_company_length_floor(monkeypatch):
    brief = _build_brief(
        monkeypatch,
        [
            "年長組が園庭でさつまいもの苗を植えました。",
            "苗を置いてから土をかぶせました。",
            "活動後に道具を片付けました。",
        ],
        "日常のできごとを伝える",
        genre_id="daily_activity",
    )

    assert "日記風" in brief["reader_arrival_context"]
    assert "場所・動作・道具" in brief["interest_hook"]
    assert "感情・成果・強い因果" in brief["self_authored_angle"]
    assert "場所・動作・道具" in brief["paragraph_function_plan"][0]
    assert any("近接推論" in rule for rule in brief["style_rules"])
    assert brief["body_length_floor_chars"] <= 1200


def test_v2_case_study_allows_source_derived_inference_but_blocks_outcomes(monkeypatch):
    brief = _build_brief(
        monkeypatch,
        [
            "導入前は申請書の確認に時間がかかっていました。",
            "担当者が手順を整理しました。",
            "確認項目を一覧化しました。",
        ],
        "事例を紹介する",
        genre_id="case_study",
    )

    assert "課題・対応・変化" in brief["interest_hook"]
    assert "sourceから近く読める推論" in brief["self_authored_angle"]
    assert any("成果・顧客感情・強い因果" in rule for rule in brief["style_rules"])


def test_v2_announcement_stays_compact_and_not_diary(monkeypatch):
    brief = _build_brief(
        monkeypatch,
        [
            "2026年7月1日から受付時間を変更します。",
            "対象は既存利用者です。",
            "問い合わせ先はサポート窓口です。",
        ],
        "お知らせを伝える",
        genre_id="announcement",
    )

    assert "必要情報だけ" in brief["reader_arrival_context"]
    assert "必要情報を先に" in brief["interest_hook"]
    assert "日記風にせず" in brief["paragraph_function_plan"][0]
    assert any("長文化・日記化せず" in rule for rule in brief["style_rules"])
    assert brief["body_length_floor_chars"] <= 900
    assert "daily_activity_source_role_contract" not in brief


def test_v2_comparison_guide_avoids_points_rankings_and_recommendations(monkeypatch):
    brief = _build_brief(
        monkeypatch,
        [
            "Aプランは月額料金を抑えた構成です。",
            "Bプランはサポート範囲が広い構成です。",
            "契約期間はプランにより異なります。",
        ],
        "比較・選び方を整理する",
        genre_id="comparison_guide",
    )

    assert "違いを軽く見たい" in brief["reader_arrival_context"]
    assert "選び方の断定ではなく" in brief["interest_hook"]
    assert "ポイント記事化" in brief["paragraph_function_plan"][0]
    assert any("ランキング化" in rule and "おすすめ断定" in rule for rule in brief["style_rules"])


def test_v2_market_explanation_avoids_third_party_summary_voice(monkeypatch):
    brief = _build_brief(
        monkeypatch,
        [
            "資料では市場規模の推移を示しています。",
            "資料では利用場面の変化を説明しています。",
            "資料では導入時の課題を整理しています。",
        ],
        "解説・市場を伝える",
        genre_id="market_explanation",
    )

    assert "軽く眺めに来た読者" in brief["reader_arrival_context"]
    assert "資料要約ではなく" in brief["interest_hook"]
    assert "第三者要約" in brief["self_authored_angle"]
    assert any("第三者視点" in rule for rule in brief["style_rules"])


def test_draft_writer_uses_interest_led_instructions_only_for_route_v():
    route_v_brief = {
        "article_brief": {
            "voice_mode": "self_authored_blogger",
            "target_length_chars": 1600,
            "body_length_floor_chars": 1400,
            "section_count": 3,
            "source_use_mode": "representative",
            "rhythm_break_plan": ["濃い事実ブロックの直後に一文だけ置く。"],
        }
    }
    v1_brief = {"article_brief": {"target_length_chars": 1600, "section_count": 3, "source_thickness": "medium"}}
    knowledge_pack = _knowledge_pack(["料金表には代表的な項目があります。"])

    route_v_instructions = _build_draft_writer_instructions(route_v_brief, knowledge_pack)
    v1_instructions = _build_draft_writer_instructions(v1_brief, knowledge_pack)

    assert "casually browsing" in route_v_instructions
    assert "body_length_floor_chars=1400" in route_v_instructions
    assert "never as a reason to stop below the floor" in route_v_instructions
    assert "Do not mention those field names" in route_v_instructions
    assert "source-derived asides" in route_v_instructions
    assert "at most 2" in route_v_instructions
    assert "casually browsing" not in v1_instructions
    assert "source-derived asides" not in v1_instructions


def test_draft_writer_company_intro_adds_low_intent_source_label_guard():
    route_v_company_brief = {
        "article_brief": {
            "genre_id": "company_service_intro",
            "voice_mode": "self_authored_blogger",
            "target_length_chars": 1600,
            "body_length_floor_chars": 1400,
            "section_count": 3,
            "source_use_mode": "selective",
        }
    }
    route_v_other_brief = {
        "article_brief": {
            "genre_id": "market_explanation",
            "voice_mode": "self_authored_blogger",
            "target_length_chars": 1600,
            "body_length_floor_chars": 1400,
            "section_count": 3,
            "source_use_mode": "selective",
        }
    }
    knowledge_pack = _knowledge_pack(["会社紹介の根拠があります。"])

    company_instructions = _build_draft_writer_instructions(route_v_company_brief, knowledge_pack)
    other_instructions = _build_draft_writer_instructions(route_v_other_brief, knowledge_pack)

    assert "daily/work/selection/operations context" in company_instructions
    assert "Source-backed company bridge" in company_instructions
    assert "company-side work/action/value statements" in company_instructions
    assert "outside-observer inference" in company_instructions
    assert "avoid page/category/official-info navigation" in company_instructions
    assert "Treat page/category/source labels as material, not the subject" in company_instructions
    assert "Each H2 needs source detail plus relevance" in company_instructions
    assert "in 2-section plans, make both H2s substantial" in company_instructions
    assert "market share, centrality, indispensability" in company_instructions
    assert "一手に, 中心企業, 不可欠, トップ" in company_instructions
    assert "people, culture, recruitment, or behind-the-scenes angles only when source-supported" in company_instructions
    assert "参考, CTA, Copyright, ポイント, or 同社" in company_instructions
    assert "daily/work/selection/operations context" not in other_instructions
    assert "Source-backed company bridge" not in other_instructions
