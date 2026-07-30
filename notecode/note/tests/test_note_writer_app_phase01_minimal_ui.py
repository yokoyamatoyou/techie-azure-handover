import json

from note import note_writer_app as app_mod


_UNLOCKED_PAST_BLOGS = [
    {"title": "記事1", "url": "https://example.com/1", "body_chars": 1600},
    {"title": "記事2", "url": "https://example.com/2", "body_chars": 1600},
    {"title": "記事3", "url": "https://example.com/3", "body_chars": 1600},
]


def _patch_latest_generation_paths(monkeypatch, tmp_path):
    latest_json = tmp_path / "latest_generation_output.json"
    latest_txt = tmp_path / "latest_generation_output.txt"
    route_v_log_root = tmp_path / "route_v_generation"
    writer_log_root = tmp_path / "legacy_writer_only_generation"
    route_v_log_root.mkdir()
    writer_log_root.mkdir()
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_JSON_PATH", latest_json)
    monkeypatch.setattr(app_mod, "LATEST_GENERATION_TEXT_PATH", latest_txt)
    monkeypatch.setattr(app_mod, "ROUTE_V_GENERATION_LOG_ROOT", route_v_log_root)
    monkeypatch.setattr(app_mod, "LEGACY_WRITER_ONLY_GENERATION_LOG_ROOT", writer_log_root)
    return latest_json, latest_txt, route_v_log_root, writer_log_root


def test_latest_generation_display_is_empty_by_default(monkeypatch, tmp_path) -> None:
    latest_json, _latest_txt, _route_v_log_root, _writer_log_root = _patch_latest_generation_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(app_mod, "RESTORE_PREVIOUS_GENERATION_ON_START", False)
    latest_json.write_text(
        json.dumps(
            {
                "route_v_used": True,
                "fallback_used": False,
                "route_0506_used": False,
                "legacy_body_route_used": False,
                "repair_used": False,
                "quality_pipeline_used": False,
                "title": "前回記事",
                "body": "# 前回記事\n\n起動時には表示しない本文です。",
                "full_text": "# 前回記事\n\n起動時には表示しない本文です。",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert app_mod._load_latest_generation_snapshot_for_display() == {}


def test_latest_generation_display_prefers_route_v_artifact_over_legacy_latest(monkeypatch, tmp_path) -> None:
    latest_json, _latest_txt, route_v_log_root, _writer_log_root = _patch_latest_generation_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(app_mod, "RESTORE_PREVIOUS_GENERATION_ON_START", True)
    latest_json.write_text(
        json.dumps(
            {
                "title": "Route 0506 legacy",
                "body": "Route 0506 body\nC:\\tetie\\notecode\\note\\uploads\\legacy.txt",
                "route_0506_used": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    run_dir = route_v_log_root / "route_v_20260617_010101_safe"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "route_v_used": True,
                "fallback_used": False,
                "route_0506_used": False,
                "legacy_body_route_used": False,
                "repair_used": False,
                "quality_pipeline_used": False,
                "title": "安全な前回記事",
                "body": "# 安全な前回記事\n\n企業note向けの本文です。",
                "full_text": "# 安全な前回記事\n\n企業note向けの本文です。",
                "linkedin_short_text": "SNS文",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    display = app_mod._load_latest_generation_snapshot_for_display()

    assert display["title"] == "安全な前回記事"
    assert "企業ブログ向けの本文です。" in display["note_body"]
    assert "企業note" not in display["note_body"]
    assert "Route 0506" not in "\n".join(display.values())
    assert "C:\\" not in "\n".join(display.values())


def test_latest_generation_display_blocks_legacy_only_payload(monkeypatch, tmp_path) -> None:
    latest_json, _latest_txt, _route_v_log_root, _writer_log_root = _patch_latest_generation_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(app_mod, "RESTORE_PREVIOUS_GENERATION_ON_START", True)
    latest_json.write_text(
        json.dumps(
            {
                "title": "Route A legacy",
                "body": "validation log\nC:\\tetie\\notecode\\note\\uploads\\legacy.txt",
                "legacy_body_route_used": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    display = app_mod._load_latest_generation_snapshot_for_display()

    assert display["title"] == "前回生成結果は旧形式です"
    assert "現在の表示形式と異なる" in display["note_body"]
    assert "Route A" not in "\n".join(display.values())
    assert "C:\\" not in "\n".join(display.values())


def test_latest_generation_display_uses_safe_route_v_latest_json(monkeypatch, tmp_path) -> None:
    latest_json, _latest_txt, _route_v_log_root, _writer_log_root = _patch_latest_generation_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(app_mod, "RESTORE_PREVIOUS_GENERATION_ON_START", True)
    latest_json.write_text(
        json.dumps(
            {
                "route_v_used": True,
                "fallback_used": False,
                "route_0506_used": False,
                "legacy_body_route_used": False,
                "repair_used": False,
                "quality_pipeline_used": False,
                "title": "route current latest",
                "body": "# route current latest\n\n本文です。",
                "references": "C:\\tetie\\notecode\\note\\uploads\\hidden.txt\nhttps://example.com/source",
                "full_text": "# route current latest\n\n本文です。",
                "linkedin_text": "SNS文",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    display = app_mod._load_latest_generation_snapshot_for_display()

    assert display["title"] == "route current latest"
    assert "https://example.com/source" in display["references"]
    assert "C:\\" not in "\n".join(display.values())


def test_resolve_source_mode_selection_defaults_to_grounded() -> None:
    resolved = app_mod._resolve_source_mode_selection("")

    assert resolved["source_mode_key"] == "grounded"
    assert resolved["source_mode_label"] == "資料あり"
    assert resolved["requires_source_inputs"] is True
    assert resolved["uses_web_research"] is False


def test_build_source_mode_helper_text_blocks_web_for_announcement() -> None:
    helper = app_mod._build_source_mode_helper_text(
        article_type_key="announcement",
        source_mode_key="web",
    )

    assert "この種類は資料ありで進めます" in helper


def test_visible_source_modes_do_not_include_followup() -> None:
    resolved = app_mod._resolve_source_mode_selection("続編")

    assert "followup" not in app_mod.SOURCE_MODE_LABELS
    assert resolved["source_mode_key"] == "grounded"
    assert resolved["uses_web_research"] is False


def test_prompt_only_source_mode_requires_daily_story_and_past_blog_unlock() -> None:
    assert app_mod._past_blog_prompt_unlock_available(_UNLOCKED_PAST_BLOGS)
    daily_locked_options = app_mod._source_mode_options_for_article_type("daily_story")
    daily_unlocked_options = app_mod._source_mode_options_for_article_type(
        "daily_story",
        past_blog_unlocked=True,
    )
    announcement_options = app_mod._source_mode_options_for_article_type(
        "announcement",
        past_blog_unlocked=True,
    )

    assert "prompt_only" not in daily_locked_options
    assert daily_unlocked_options["prompt_only"] == "プロンプトのみ"
    assert "prompt_only" not in announcement_options


def test_grounded_input_surface_hides_one_line_theme() -> None:
    surface = app_mod._build_source_mode_input_surface(
        article_type_key="explanatory_article",
        source_mode_key="grounded",
    )
    gate = app_mod._build_generate_gate_surface(
        confirmation_ready=False,
        article_type_key="explanatory_article",
        source_mode_key="grounded",
        source_count=0,
        prompt_raw="入力済みテーマは保持する",
    )

    assert surface["prompt_visible"] is False
    assert surface["prompt_label"] == ""
    assert gate["enabled"] is False
    assert gate["button_text"] == "資料を追加する"
    assert "資料入力へ戻ってください" in gate["hint_text"]


def test_omakase_locked_surface_hides_one_line_theme() -> None:
    surface = app_mod._build_source_mode_input_surface(
        article_type_key="daily_story",
        source_mode_key="web",
        past_blog_unlocked=False,
    )
    omakase = app_mod._build_omakase_surface_state(
        article_type_key="daily_story",
        prompt_raw="",
        source_mode_key="web",
        published_post_candidates=[],
    )
    gate = app_mod._build_generate_gate_surface(
        confirmation_ready=True,
        article_type_key="daily_story",
        source_mode_key="web",
        source_count=0,
        prompt_raw="",
        omakase_state=omakase,
        past_blog_unlocked=False,
    )

    assert surface["prompt_visible"] is False
    assert omakase["status"] == "OMAKASE_FALLBACK"
    assert gate["enabled"] is False
    assert gate["button_text"] == "資料ありで進める"


def test_prompt_only_input_surface_requires_past_blog_unlock() -> None:
    surface = app_mod._build_source_mode_input_surface(
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        past_blog_unlocked=True,
    )
    omakase = app_mod._build_omakase_surface_state(
        article_type_key="daily_story",
        prompt_raw="夕方の打ち合わせで言葉の受け取り方が少しズレた話",
        source_mode_key="prompt_only",
    )
    gate = app_mod._build_generate_gate_surface(
        confirmation_ready=True,
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        source_count=0,
        prompt_raw="夕方の打ち合わせで言葉の受け取り方が少しズレた話",
        past_blog_unlocked=True,
    )
    locked_gate = app_mod._build_generate_gate_surface(
        confirmation_ready=True,
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        source_count=0,
        prompt_raw="夕方の打ち合わせで言葉の受け取り方が少しズレた話",
        past_blog_unlocked=False,
    )

    assert surface["prompt_visible"] is True
    assert surface["prompt_label"] == "1行テーマ"
    assert "外部事実の根拠にはしません" in surface["section_intro_text"]
    assert omakase["visible"] is False
    assert gate["enabled"] is True
    assert locked_gate["enabled"] is False
    assert "公開済みブログの蓄積が足りない" in locked_gate["hint_text"]


def test_prompt_only_no_source_helper_requires_daily_story_and_prompt() -> None:
    assert not app_mod._source_mode_allows_no_sources(
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        prompt_raw="朝の確認で返事が少し遅れた話",
    )
    assert app_mod._source_mode_allows_no_sources(
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        prompt_raw="朝の確認で返事が少し遅れた話",
        past_blog_unlocked=True,
    )
    assert not app_mod._source_mode_allows_no_sources(
        article_type_key="announcement",
        source_mode_key="prompt_only",
        prompt_raw="日程変更のお知らせ",
    )
    assert not app_mod._source_mode_allows_no_sources(
        article_type_key="daily_story",
        source_mode_key="prompt_only",
        prompt_raw="",
    )


def test_build_announcement_inline_error_requires_date_target_and_change() -> None:
    error_text = app_mod._build_announcement_inline_error(
        article_type_key="announcement",
        source_mode_key="grounded",
        prompt_raw="お知らせを作る",
        source_values=[],
    )

    assert "日付" in error_text
    assert "対象" in error_text
    assert "変更点" in error_text


def test_build_announcement_inline_error_clears_when_core_facts_exist() -> None:
    error_text = app_mod._build_announcement_inline_error(
        article_type_key="announcement",
        source_mode_key="grounded",
        prompt_raw="2026年4月20日に利用者向け管理画面の仕様変更をお知らせする",
        source_values=["https://example.com/notice"],
    )

    assert error_text == ""


def test_build_announcement_inline_error_rejects_web_mode() -> None:
    error_text = app_mod._build_announcement_inline_error(
        article_type_key="announcement",
        source_mode_key="web",
        prompt_raw="2026年4月20日の更新内容",
        source_values=[],
    )

    assert "資料ベースのみ" in error_text
