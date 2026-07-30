import asyncio
from pathlib import Path
from types import SimpleNamespace

import note.note_writer_app_route_v_ui as writer_ui
from note.image_prompt_helpers import IMAGE_PATTERN_OPTIONS
from note.note_writer_app_route_v_ui import (
    RouteVControls,
    RouteVResultTargets,
    RouteVStatusTargets,
    apply_route_v_result,
    build_route_v_generation_kwargs,
    clear_route_v_result,
    _build_stop_view,
    _poll_route_v_generation_progress,
    run_route_v_generation_click,
)
from note.note_writer_app_generated_image_panel import (
    build_image_pattern_label_options,
    resolve_default_image_pattern_label,
)
from note.note_writer_app_ui_compat import HiddenGenerateButtonCompatibility


class FakeElement:
    def __init__(self, value=""):
        self.value_history = []
        self._value = ""
        self.value = value
        self.text = ""
        self.content = ""
        self.visible = False
        self.enabled = True
        self.class_calls = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.value_history.append(value)

    def classes(self, *args, **kwargs):
        self.class_calls.append((args, kwargs))
        return self

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True


def _controls(**overrides):
    values = {
        "category": FakeElement("販促・BtoB"),
        "tone": FakeElement("まじめな広報"),
        "instruction": FakeElement("相談前の判断軸"),
        "target_reader": FakeElement("空き家所有者"),
        "reader_problem": FakeElement("条件の見方が分からない"),
        "article_goal": FakeElement("相談前の確認点を整理する"),
        "company_speaker": FakeElement("不動産会社の担当者"),
        "button": FakeElement(),
    }
    values.update(overrides)
    return RouteVControls(**values)


def _status_targets():
    return RouteVStatusTargets(
        generate_button=FakeElement(),
        route_v_button=FakeElement(),
        spinner=FakeElement(),
        generation_progress=FakeElement(),
        generation_progress_note=FakeElement(),
        missing_source_alert=FakeElement(),
        source_error_area=FakeElement(),
        status_label=FakeElement(),
    )


def _nonempty_alert_count(status: RouteVStatusTargets) -> int:
    return sum(
        bool(str(alert.content or "").strip())
        for alert in (status.missing_source_alert, status.source_error_area)
    )


def _result_targets():
    return RouteVResultTargets(
        title_area=FakeElement(),
        lead_area=FakeElement("old lead"),
        body_area=FakeElement(),
        references_area=FakeElement("old refs"),
        hashtags_area=FakeElement("old tags"),
        full_text_area=FakeElement(),
        note_body_text=FakeElement(),
        linkedin_area=FakeElement(),
        linkedin_short_area=FakeElement(),
        preview=FakeElement(),
        stats_label=FakeElement(),
    )


def test_image_touch_selector_label_and_four_options_are_available():
    writer_source = Path(writer_ui.__file__).read_text(encoding="utf-8")
    image_panel_source = Path(writer_ui.__file__).with_name("note_writer_app_generated_image_panel.py").read_text(
        encoding="utf-8"
    )

    assert 'label="画像のトーン"' in writer_source
    assert 'label="画像のトーン"' not in image_panel_source
    assert "画像の設定を見る" not in writer_source
    assert "記事生成後に、選んだトーンで文字入り画像と文字なし画像も自動生成します。" in writer_source
    assert build_image_pattern_label_options(IMAGE_PATTERN_OPTIONS) == [
        "シンプル",
        "ブログ見出し画像風",
        "フラットイラスト",
        "温かい手描き風",
    ]
    assert resolve_default_image_pattern_label(
        image_pattern_options=IMAGE_PATTERN_OPTIONS,
        default_image_pattern_key="simple",
    ) == "シンプル"


def test_generation_progress_hides_raw_fraction_value_without_shrinking_bar():
    writer_source = Path(writer_ui.__file__).with_name("note_writer_app.py").read_text(encoding="utf-8")

    assert 'ui.linear_progress(value=0.0, show_value=False, size="20px")' in writer_source


def test_route_v_normal_card_hides_redundant_contract_inputs():
    source = Path(writer_ui.__file__).read_text(encoding="utf-8")

    assert 'label="会社側の語り手"' not in source
    assert 'label="記事目的"' not in source
    assert 'label="読者の課題"' not in source
    assert 'label="想定読者（任意）"' in source
    assert '"company_speaker": _control_text(controls.company_speaker) or "会社側の担当者"' in source
    assert "_default_reader_problem(category_label)" in source


def test_hidden_generate_button_uses_noop_compatibility_target():
    button = HiddenGenerateButtonCompatibility(text="記事を生成")

    button.disable()
    button.visible = True
    button.text = "確認後に生成を開始"
    assert button.props("hidden").style("display: none !important;") is button
    button.enable()

    assert button.enabled is True
    assert button.visible is True
    assert button.text == "確認後に生成を開始"

    source = Path(writer_ui.__file__).with_name("note_writer_app.py").read_text(encoding="utf-8")
    assert 'generate_button = HiddenGenerateButtonCompatibility(text="記事を生成")' in source
    assert 'generate_button = ui.button("記事を生成")' not in source
    assert 'generate_button.on("click", run_generation)' not in source


def test_source_shortage_ui_copy_is_warning_not_error_colored():
    source = Path(writer_ui.__file__).with_name("note_writer_app.py").read_text(encoding="utf-8")

    assert '"source-input-alert text-sm font-medium text-amber-800"' in source
    assert source.count('props("role=alert aria-live=assertive")') == 2
    assert '"missing-source-alert source-input-alert text-sm font-medium text-amber-800"' in source
    assert '.classes("source-url-input w-full").props("outlined stack-label")' in source
    assert "document.querySelector('.source-url-input')" in source
    assert "id=source-url-input" not in source
    assert "sourceField.scrollIntoView({behavior: 'smooth', block: 'center'});" in source
    assert "if (input) input.focus({preventScroll: true});" in source
    assert "ソース不足のため、確認項目を作成できません。" in source
    assert "使えるソースが不足しています。URL/ファイルを見直してください。" in source
    assert "読み込めないソースがあります。修正後にもう一度確認項目を作成してください。" not in source
    assert 'ui.notify("使えるソースがまだありません。URLやファイルを見直すと進めます。", color="negative")' not in source


def test_build_route_v_generation_kwargs_keeps_field_contract():
    state = SimpleNamespace(sources=["https://example.com"])

    kwargs = build_route_v_generation_kwargs(
        state=state,
        controls=_controls(),
        fallback_instruction=lambda: "fallback",
    )

    assert kwargs == {
        "sources": ["https://example.com"],
        "category_label": "販促・BtoB",
        "tone_label": "まじめな広報",
        "target_reader": "空き家所有者",
        "reader_problem": "条件の見方が分からない",
        "article_goal": "相談前の確認点を整理する",
        "company_speaker": "不動産会社の担当者",
        "instruction": "相談前の判断軸",
    }


def test_build_route_v_generation_kwargs_uses_internal_defaults_for_hidden_inputs():
    state = SimpleNamespace(sources=["https://example.com"])

    kwargs = build_route_v_generation_kwargs(
        state=state,
        controls=_controls(
            instruction=FakeElement(""),
            reader_problem=None,
            article_goal=None,
            company_speaker=None,
        ),
        fallback_instruction=lambda: "資料アップロードから一通り確認する記事",
    )

    assert kwargs["company_speaker"] == "会社側の担当者"
    assert kwargs["article_goal"] == "資料アップロードから一通り確認する記事"
    assert kwargs["reader_problem"] == "困っていることの背景や手がかりを知りたい"
    assert kwargs["instruction"] == "資料アップロードから一通り確認する記事"


def test_build_route_v_generation_kwargs_uses_company_intro_defaults_for_blank_request():
    state = SimpleNamespace(sources=["https://example.com"])

    kwargs = build_route_v_generation_kwargs(
        state=state,
        controls=_controls(
            category=FakeElement("会社・サービス紹介"),
            instruction=FakeElement(""),
            reader_problem=None,
            article_goal=None,
            company_speaker=None,
        ),
        fallback_instruction=lambda: "",
    )

    assert kwargs["reader_problem"] == "会社の背景やサービス内容を知りたい"
    assert kwargs["article_goal"] == "会社の事業内容、背景、提供価値を紹介する"
    assert kwargs["instruction"] == ""


def test_build_route_v_generation_kwargs_does_not_expose_model_or_temperature_controls():
    state = SimpleNamespace(sources=["https://example.com"])

    kwargs = build_route_v_generation_kwargs(
        state=state,
        controls=_controls(),
        fallback_instruction=lambda: "fallback",
    )

    assert "llm_model" not in kwargs
    assert "temperature_profile" not in kwargs
    assert kwargs["tone_label"] == "まじめな広報"


def test_route_v_card_presents_blog_persona_profiles_not_model_controls():
    source = Path(writer_ui.__file__).read_text(encoding="utf-8")

    assert 'label="ブログ担当ペルソナ"' in source
    assert 'label="温度感"' not in source
    assert '"感情豊かな広報"' in source
    assert '"ユーモアのあるサービス紹介担当"' in source
    assert '"まじめな広報"' in source


def test_apply_route_v_result_keeps_article_and_sns_mapping():
    targets = _result_targets()
    refreshed = []

    body = apply_route_v_result(
        {
            "title": "記事タイトル",
            "body": "# 記事タイトル\n\n## 見出し\n本文",
            "linkedin_text": "LinkedIn本文",
            "linkedin_short_text": "短縮SNS",
        },
        targets=targets,
        sanitize_preview=lambda text: f"preview:{text}",
        refresh_output_stage_visibility=lambda: refreshed.append("output"),
        refresh_step_indicators=lambda: refreshed.append("steps"),
    )

    assert body.startswith("# 記事タイトル")
    assert targets.title_area.value == "記事タイトル"
    assert targets.lead_area.value == ""
    assert targets.body_area.value == body
    assert targets.full_text_area.value == body
    assert targets.note_body_text.value == body
    assert targets.linkedin_area.value == "LinkedIn本文"
    assert targets.linkedin_short_area.value == "短縮SNS"
    assert targets.preview.content.startswith("preview:# 記事タイトル")
    assert targets.stats_label.text == "Route V 本文: 19文字 / SNS用文章: 5文字"
    assert refreshed == ["output", "steps"]


def test_clear_route_v_result_removes_stale_article_and_sns_text():
    targets = _result_targets()
    targets.title_area.value = "古いタイトル"
    targets.body_area.value = "古い本文"
    targets.full_text_area.value = "古い本文"
    targets.note_body_text.value = "古い本文"
    targets.linkedin_area.value = "古いSNS"
    targets.linkedin_short_area.value = "古い短縮SNS"
    targets.preview.content = "古いプレビュー"
    targets.stats_label.text = "古い統計"
    refreshed = []

    clear_route_v_result(
        targets=targets,
        refresh_output_stage_visibility=lambda: refreshed.append("output"),
        refresh_step_indicators=lambda: refreshed.append("steps"),
        placeholder="生成中です。",
    )

    assert targets.title_area.value == ""
    assert targets.body_area.value == ""
    assert targets.full_text_area.value == ""
    assert targets.note_body_text.value == ""
    assert targets.linkedin_area.value == ""
    assert targets.linkedin_short_area.value == ""
    assert targets.preview.content == "生成中です。"
    assert targets.stats_label.text == ""
    assert refreshed == ["output", "steps"]


def test_route_v_click_success_cleans_up_and_does_not_call_image_or_old_routes(monkeypatch):
    notifications = []
    monkeypatch.setattr(writer_ui.ui, "notify", lambda message, color=None: notifications.append((message, color)))
    state = SimpleNamespace(sources=["https://example.com"], busy=False, result={})
    status = _status_targets()
    targets = _result_targets()
    calls = []

    def fake_generation(**kwargs):
        calls.append(kwargs)
        return {
            "success": True,
            "run_id": "run-1",
            "title": "タイトル",
            "body": "本文",
            "linkedin_text": "LinkedIn",
            "linkedin_short_text": "SNS",
            "artifact_root": "logs/run-1",
            "route_v_used": True,
            "draft_path": "logs/run-1/draft.md",
            "route_0506_used": False,
            "legacy_body_route_used": False,
            "fallback_used": False,
            "repair_used": False,
        }

    async def fake_io_bound(fn):
        return fn()

    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=status,
            result_targets=targets,
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: None,
            refresh_step_indicators=lambda: None,
            to_plain_dict=dict,
            generation_callable=fake_generation,
            io_bound=fake_io_bound,
            sanitize_preview=lambda text: text,
        )
    )

    assert calls and calls[0]["sources"] == ["https://example.com"]
    assert state.busy is False
    assert state.result["route_v_used"] is True
    assert state.result["route_0506_used"] is False
    assert state.result["legacy_body_route_used"] is False
    assert state.result["fallback_used"] is False
    assert status.generate_button.enabled is True
    assert status.route_v_button.enabled is True
    assert status.spinner.visible is False
    assert status.generation_progress.value_history[:3] == ["", 0.02, 0.06]
    assert 0.35 not in status.generation_progress.value_history
    assert status.generation_progress.value == 1.0
    assert status.generation_progress_note.text == "ブログ本文とSNS用文章を作成しました。"
    assert targets.linkedin_area.value == "LinkedIn"
    assert targets.linkedin_short_area.value == "SNS"
    assert notifications == [("ブログとSNS用文章を作成しました。", "positive")]


def test_route_v_click_success_calls_injected_image_generator_with_handoff_context(monkeypatch, tmp_path):
    notifications = []
    monkeypatch.setattr(writer_ui.ui, "notify", lambda message, color=None: notifications.append((message, color)))
    (tmp_path / "brief.json").write_text('{"internal_category": "branding"}', encoding="utf-8")
    state = SimpleNamespace(
        sources=["https://example.com"],
        busy=False,
        result={},
        generated_images=["stale.jpg"],
        generated_image_variants=[{"key": "old"}],
        image_generation_status="old",
    )
    image_calls = []
    refreshes = []
    llm = object()

    def fake_generation(**_kwargs):
        return {
            "success": True,
            "run_id": "run-image",
            "title": "結果タイトル",
            "body": "# 結果タイトル\n\n私たちは画像生成用のリードを本文から渡します。",
            "linkedin_text": "LinkedIn",
            "linkedin_short_text": "SNS",
            "artifact_root": str(tmp_path),
            "route_v_used": True,
            "route_0506_used": False,
            "legacy_body_route_used": False,
            "fallback_used": False,
            "repair_used": False,
        }

    def fake_image_generation(**kwargs):
        image_calls.append(kwargs)
        return {
            "status": "success",
            "variants": [
                {"key": "with_text", "label": "文字入り画像", "path": "C:/tmp/text.jpg"},
                {"key": "without_text", "label": "文字なし画像", "path": "C:/tmp/plain.jpg"},
            ],
        }

    async def fake_io_bound(fn):
        return fn()

    targets = _result_targets()
    status = _status_targets()
    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=status,
            result_targets=targets,
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: None,
            refresh_step_indicators=lambda: None,
            to_plain_dict=dict,
            generation_callable=fake_generation,
            image_generation_callable=fake_image_generation,
            image_llm=llm,
            selected_image_pattern_key=lambda: "flat_illustration",
            refresh_generated_images=lambda: refreshes.append("refresh"),
            io_bound=fake_io_bound,
            sanitize_preview=lambda text: text,
        )
    )

    assert len(image_calls) == 1
    assert image_calls[0]["llm"] is llm
    assert image_calls[0]["title"] == "結果タイトル"
    assert image_calls[0]["lead"] == "私たちは画像生成用のリードを本文から渡します。"
    assert image_calls[0]["body"].startswith("# 結果タイトル")
    assert image_calls[0]["article_type"] == "branding"
    assert image_calls[0]["pattern_key"] == "flat_illustration"
    assert state.generated_image_variants == [
        {"key": "with_text", "label": "文字入り画像", "path": "C:/tmp/text.jpg"},
        {"key": "without_text", "label": "文字なし画像", "path": "C:/tmp/plain.jpg"},
    ]
    assert state.generated_images == ["C:/tmp/text.jpg", "C:/tmp/plain.jpg"]
    assert state.image_generation_status == "success"
    assert status.status_label.text == "ブログ・SNS用文章・画像を作成しました。"
    assert status.generation_progress_note.text == "ブログ・SNS文章・画像を作成しました。"
    assert [value for value in status.generation_progress.value_history if isinstance(value, float)] == [
        0.02,
        0.06,
        0.9,
        0.92,
        1.0,
    ]
    assert refreshes == ["refresh", "refresh"]
    assert targets.linkedin_area.value == "LinkedIn"
    assert targets.linkedin_short_area.value == "SNS"
    assert notifications == [("ブログ・SNS文章・画像を作成しました。", "positive")]


def test_route_v_image_generator_failure_is_fail_open(monkeypatch):
    monkeypatch.setattr(writer_ui.ui, "notify", lambda *_args, **_kwargs: None)
    state = SimpleNamespace(
        sources=["https://example.com"],
        busy=False,
        result={},
        generated_images=["stale.jpg"],
        generated_image_variants=[{"key": "old"}],
        image_generation_status="old",
    )

    def fake_generation(**_kwargs):
        return {
            "success": True,
            "title": "タイトル",
            "body": "# タイトル\n\n本文",
            "linkedin_text": "LinkedIn保持",
            "linkedin_short_text": "SNS保持",
        }

    def fail_image_generation(**_kwargs):
        raise RuntimeError("stubbed image failure")

    async def fake_io_bound(fn):
        return fn()

    targets = _result_targets()
    status = _status_targets()
    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=status,
            result_targets=targets,
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: None,
            refresh_step_indicators=lambda: None,
            to_plain_dict=dict,
            generation_callable=fake_generation,
            image_generation_callable=fail_image_generation,
            image_llm=object(),
            selected_image_pattern_key=lambda: "blog_cover",
            refresh_generated_images=lambda: None,
            io_bound=fake_io_bound,
            sanitize_preview=lambda text: text,
        )
    )

    assert state.busy is False
    assert state.result["success"] is True
    assert targets.body_area.value == "# タイトル\n\n本文"
    assert targets.linkedin_area.value == "LinkedIn保持"
    assert targets.linkedin_short_area.value == "SNS保持"
    assert state.generated_images == []
    assert state.generated_image_variants == []
    assert state.image_generation_status == "failed"
    assert status.status_label.text == "ブログとSNS用文章は作成済みです。画像生成に失敗しました。"
    assert status.generation_progress_note.text == "画像生成に失敗しました。ブログ本文とSNS用文章はそのまま使えます。"


def test_route_v_failure_does_not_call_image_generator(monkeypatch):
    monkeypatch.setattr(writer_ui.ui, "notify", lambda *_args, **_kwargs: None)
    state = SimpleNamespace(
        sources=["https://example.com"],
        busy=False,
        result={},
        generated_images=[],
        generated_image_variants=[],
        image_generation_status="",
    )
    image_calls = []

    def stopped_generation(**_kwargs):
        return {"success": False, "reason_code": "SMOKE_FAILED", "artifact_root": "logs/stopped"}

    def image_generation(**kwargs):
        image_calls.append(kwargs)
        return {"status": "success", "variants": []}

    async def fake_io_bound(fn):
        return fn()

    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=_status_targets(),
            result_targets=_result_targets(),
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: None,
            refresh_step_indicators=lambda: None,
            to_plain_dict=dict,
            generation_callable=stopped_generation,
            image_generation_callable=image_generation,
            image_llm=object(),
            selected_image_pattern_key=lambda: "blog_cover",
            refresh_generated_images=lambda: None,
            io_bound=fake_io_bound,
        )
    )

    assert image_calls == []
    assert state.image_generation_status == ""


def test_route_v_blocked_without_body_clears_stale_article_and_explains_error(monkeypatch):
    notifications = []
    monkeypatch.setattr(writer_ui.ui, "notify", lambda message, color=None: notifications.append((message, color)))
    state = SimpleNamespace(sources=["https://example.com"], busy=False, result={"body": "古い本文"})
    status = _status_targets()
    targets = _result_targets()
    targets.body_area.value = "古い本文"
    targets.full_text_area.value = "古い本文"
    targets.note_body_text.value = "古い本文"
    targets.preview.content = "古いプレビュー"
    refreshed = []

    def blocked_generation(**_kwargs):
        return {
            "success": False,
            "blocked": True,
            "reason_code": "ROUTE_V_GENERATION_FAILED",
            "message": "ValidationError: ['F002'] is too short",
            "artifact_root": "logs/route_v_generation/run-blocked",
        }

    async def fake_io_bound(fn):
        return fn()

    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=status,
            result_targets=targets,
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: refreshed.append("output"),
            refresh_step_indicators=lambda: refreshed.append("steps"),
            to_plain_dict=dict,
            generation_callable=blocked_generation,
            io_bound=fake_io_bound,
            sanitize_preview=lambda text: text,
        )
    )

    assert state.busy is False
    assert state.result["blocked"] is True
    assert targets.body_area.value == ""
    assert targets.full_text_area.value == ""
    assert targets.note_body_text.value == ""
    assert "本文は作成されていません" in targets.preview.content
    assert "ROUTE_V_GENERATION_FAILED" in status.source_error_area.content
    assert status.missing_source_alert.content == ""
    assert _nonempty_alert_count(status) == 1
    assert status.status_label.text == "記事生成に失敗しました。本文は作成されていません。"
    assert notifications == [("記事生成に失敗しました。本文は作成されていません。", "negative")]
    assert refreshed == ["output", "steps", "output", "steps"]


def test_route_v_stop_view_explains_openai_timeout_as_api_failure():
    view = _build_stop_view(
        {
            "blocked": True,
            "reason_code": "ROUTE_V_OPENAI_TIMEOUT",
            "message": "OpenAI APIの応答が制限時間内に返らなかったため、記事生成を停止しました。本文は作成されていません。",
            "api_error": {
                "error_type": "APITimeoutError",
                "stage": "knowledge_pack_integration",
                "request_timeout_seconds": 120.0,
                "attempt": 1,
                "max_retries": 0,
                "api_send_count": 1,
            },
        },
        artifact_root="logs/route_v_generation/run-timeout",
    )

    assert view["status"] == "OpenAI APIエラーで記事生成が停止しました。本文は作成されていません。"
    assert "入力やソースの内容が原因とは限りません" in view["detail"]
    assert "ROUTE_V_OPENAI_TIMEOUT" in view["detail"]
    assert "種別=APITimeoutError" in view["detail"]
    assert "停止段階=knowledge_pack_integration" in view["detail"]
    assert "制限時間=120秒" in view["detail"]
    assert view["progress"] == "APIエラーのため本文は作成されていません。"
    assert view["notification"] == "OpenAI APIエラーで記事生成が停止しました。"


def test_route_v_stop_view_shows_openai_http_error_without_timeout_label():
    view = _build_stop_view(
        {
            "blocked": True,
            "reason_code": "ROUTE_V_OPENAI_API_ERROR",
            "message": "OpenAI APIエラーにより記事生成を停止しました。本文は作成されていません。",
            "api_error": {
                "reason_code": "ROUTE_V_OPENAI_API_ERROR",
                "kind": "api_error",
                "error_type": "InternalServerError",
                "status_code": 520,
                "stage": "article_brief_builder",
                "request_timeout_seconds": 120.0,
                "elapsed_seconds": 11.079,
                "retry_after_seconds": 60.0,
                "attempt": 1,
                "max_retries": 0,
                "api_send_count": 6,
            },
        },
        artifact_root="logs/route_v_generation/run-api-error",
    )

    assert "ROUTE_V_OPENAI_API_ERROR" in view["detail"]
    assert "HTTP=520" in view["detail"]
    assert "elapsed=11.079s" in view["detail"]
    assert "retry_after=60s" in view["detail"]
    assert "article_brief_builder" in view["detail"]
    assert "request_timeout=120s" not in view["detail"]


def test_route_v_progress_poll_updates_percent_label():
    status = _status_targets()

    async def run_poll_once():
        task = asyncio.create_task(
            _poll_route_v_generation_progress(
                run_id="route_v_progress",
                status_targets=status,
                progress_reader=lambda _run_id: {
                    "stage": "knowledge_pack_integration",
                    "percent": 50,
                    "message": "根拠情報を統合しています。",
                },
                interval_seconds=0.01,
            )
        )
        await asyncio.sleep(0.03)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_poll_once())

    assert status.generation_progress.value == 0.5
    assert status.status_label.text == "根拠情報を統合しています。 50%"
    assert status.generation_progress_note.text == "進行状況: 50% 根拠情報を統合しています。"


def test_route_v_progress_poll_advances_gently_while_checkpoint_is_unchanged():
    status = _status_targets()
    status.generation_progress.value = 0.5

    async def run_poll_briefly():
        task = asyncio.create_task(
            _poll_route_v_generation_progress(
                run_id="route_v_progress",
                status_targets=status,
                progress_reader=lambda _run_id: {
                    "stage": "knowledge_pack_integration",
                    "percent": 50,
                    "message": "根拠情報を統合しています。",
                },
                interval_seconds=0.1,
            )
        )
        await asyncio.sleep(0.65)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_poll_briefly())

    assert 0.5 < status.generation_progress.value < 0.6
    assert status.status_label.text.startswith("根拠情報を統合しています。 50%")


def test_route_v_progress_poll_keeps_early_checkpoints_below_the_next_real_stage():
    status = _status_targets()
    status.generation_progress.value = 0.06

    async def run_poll_briefly():
        task = asyncio.create_task(
            _poll_route_v_generation_progress(
                run_id="route_v_progress",
                status_targets=status,
                progress_reader=lambda _run_id: {
                    "stage": "fetch_sources",
                    "percent": 6,
                    "message": "ソースを確認しています。",
                },
                interval_seconds=0.01,
                smooth_after_seconds=0.0,
                smooth_step_percent=1.0,
            )
        )
        await asyncio.sleep(0.08)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_poll_briefly())

    assert 0.06 < status.generation_progress.value <= 0.119
    assert status.status_label.text.startswith("ソースを確認しています。")


def test_route_v_body_length_failure_with_body_still_calls_image_generator(monkeypatch):
    monkeypatch.setattr(writer_ui.ui, "notify", lambda *_args, **_kwargs: None)
    state = SimpleNamespace(
        sources=["https://example.com"],
        busy=False,
        result={},
        generated_images=[],
        generated_image_variants=[],
        image_generation_status="",
    )
    status = _status_targets()
    targets = _result_targets()
    image_calls = []

    def short_body_generation(**_kwargs):
        return {
            "success": False,
            "artifact_root": "logs/short-body",
            "title": "生成済み",
            "body": "# 生成済み\n\n## 見出し\n\n本文",
            "full_text": "# 生成済み\n\n## 見出し\n\n本文",
            "linkedin_text": "SNS本文",
            "linkedin_short_text": "SNS本文",
            "smoke_evaluator": {
                "passed": False,
                "failed": ["article_body_length", "section_reader_relevance"],
                "details": {"article_char_count": 320, "article_min_chars": 1300},
            },
            "sns_evaluator": {"passed": True, "failed": []},
        }

    def image_generation(**kwargs):
        image_calls.append(kwargs)
        return {
            "status": "success",
            "variants": [{"key": "with_text", "label": "文字入り画像", "path": "C:/tmp/text.jpg"}],
        }

    async def fake_io_bound(fn):
        return fn()

    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=status,
            result_targets=targets,
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: None,
            refresh_step_indicators=lambda: None,
            to_plain_dict=dict,
            generation_callable=short_body_generation,
            image_generation_callable=image_generation,
            image_llm=object(),
            selected_image_pattern_key=lambda: "flat_illustration",
            refresh_generated_images=lambda: None,
            io_bound=fake_io_bound,
        )
    )

    assert image_calls
    assert image_calls[0]["pattern_key"] == "flat_illustration"
    assert state.image_generation_status == "success"
    assert status.generation_progress.value == 1.0
    assert "Route V quality review needed" not in status.generation_progress_note.text
    assert "さらに良くできるポイント: 本文文字数、各見出しの読者接続" in status.source_error_area.content


def test_route_v_connector_repetition_warning_with_body_still_calls_image_generator(monkeypatch):
    monkeypatch.setattr(writer_ui.ui, "notify", lambda *_args, **_kwargs: None)
    state = SimpleNamespace(
        sources=["https://example.com"],
        busy=False,
        result={},
        generated_images=[],
        generated_image_variants=[],
        image_generation_status="",
    )
    image_calls = []

    def connector_warning_generation(**_kwargs):
        return {
            "success": False,
            "artifact_root": "logs/route-v-connector-warning",
            "title": "生成済み",
            "body": "# 生成済み\n\n## 見出し\n\n本文",
            "full_text": "# 生成済み\n\n## 見出し\n\n本文",
            "linkedin_text": "SNS本文",
            "linkedin_short_text": "SNS本文",
            "quality_report": {
                "quality_check": {
                    "pass": False,
                    "score": 92,
                    "issues": [
                        {"type": "connector_repetition", "severity": "medium"},
                        {"type": "model_frequent_word", "severity": "medium"},
                    ],
                }
            },
            "sns_evaluator": {"passed": False, "failed": ["key_points_preserved"]},
        }

    def image_generation(**kwargs):
        image_calls.append(kwargs)
        return {
            "status": "success",
            "variants": [{"key": "with_text", "label": "文字入り画像", "path": "C:/tmp/text.jpg"}],
        }

    async def fake_io_bound(fn):
        return fn()

    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=_status_targets(),
            result_targets=_result_targets(),
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: None,
            refresh_step_indicators=lambda: None,
            to_plain_dict=dict,
            generation_callable=connector_warning_generation,
            image_generation_callable=image_generation,
            image_llm=object(),
            selected_image_pattern_key=lambda: "blog_cover",
            refresh_generated_images=lambda: None,
            io_bound=fake_io_bound,
        )
    )

    assert image_calls
    assert state.generated_images == ["C:/tmp/text.jpg"]
    assert state.image_generation_status == "success"


def test_route_v_sentence_length_warning_with_body_still_calls_image_generator(monkeypatch):
    monkeypatch.setattr(writer_ui.ui, "notify", lambda *_args, **_kwargs: None)
    state = SimpleNamespace(
        sources=["https://example.com"],
        busy=False,
        result={},
        generated_images=[],
        generated_image_variants=[],
        image_generation_status="",
    )
    image_calls = []

    def sentence_warning_generation(**_kwargs):
        return {
            "success": False,
            "artifact_root": "logs/route-v-sentence-warning",
            "title": "サービス概要",
            "body": "# サービス概要\n\n私たちは本文を作成しています。",
            "full_text": "# サービス概要\n\n私たちは本文を作成しています。",
            "linkedin_text": "SNS本文",
            "linkedin_short_text": "SNS本文",
            "quality_report": {
                "quality_check": {
                    "pass": False,
                    "score": 76,
                    "issues": [
                        {"type": "sentence_too_long", "severity": "medium"},
                        {"type": "connector_repetition", "severity": "medium"},
                        {"type": "model_frequent_word", "severity": "medium"},
                    ],
                }
            },
            "sns_evaluator": {"passed": False, "failed": ["key_points_preserved"]},
        }

    def image_generation(**kwargs):
        image_calls.append(kwargs)
        return {
            "status": "success",
            "variants": [{"key": "with_text", "label": "文字入り画像", "path": "C:/tmp/text.jpg"}],
        }

    async def fake_io_bound(fn):
        return fn()

    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=_status_targets(),
            result_targets=_result_targets(),
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: None,
            refresh_step_indicators=lambda: None,
            to_plain_dict=dict,
            generation_callable=sentence_warning_generation,
            image_generation_callable=image_generation,
            image_llm=object(),
            selected_image_pattern_key=lambda: "blog_cover",
            refresh_generated_images=lambda: None,
            io_bound=fake_io_bound,
        )
    )

    assert image_calls
    assert state.generated_images == ["C:/tmp/text.jpg"]
    assert state.image_generation_status == "success"


def test_route_v_stop_view_tells_user_to_add_sources_for_source_grounding_failure():
    view = _build_stop_view(
        {
            "body": "# 生成済み本文",
            "smoke_evaluator": {
                "failed": ["source_grounding"],
                "details": {"unsupported_generalizations": ["人口減少", "再開発"]},
            },
        },
        artifact_root="logs/source-needed",
    )

    assert view["status"] == "本文は生成されていますが、ソース根拠が不足している可能性があります。"
    assert "関連する公式ページ、PDF、説明資料などのソースを追加" in view["detail"]
    assert "資料にない可能性がある語句: 人口減少, 再開発" in view["detail"]
    assert view["notification"] == "ソース不足の可能性があります。資料を追加してから再生成してください。"


def test_route_v_stop_view_tells_user_sources_are_insufficient_for_policy_failure():
    view = _build_stop_view(
        {
            "reason_code": "ROUTE_V_SOURCE_POLICY_BLOCKED",
            "policy_results": [
                {
                    "allowed": False,
                    "reason_code": "robots_denied",
                    "detail": "robots.txt disallows this path",
                }
            ],
        },
        artifact_root="logs/source-policy",
    )

    assert view["status"] == "使えるソースが不足しているため、記事生成を開始できませんでした。"
    assert "使えるソースを追加するか、読み込めるソースへ差し替えてください" in view["detail"]
    assert "robots_denied (robots.txt disallows this path)" in view["detail"]
    assert view["notification"] == "使えるソースが不足しています。ソースを追加または差し替えてください。"


def test_route_v_stop_view_marks_non_source_quality_failure_for_investigation():
    view = _build_stop_view(
        {
            "body": "# 生成済み本文",
            "smoke_evaluator": {
                "failed": ["audience_anchor", "section_reader_relevance"],
                "details": {"unsupported_generalizations": []},
            },
        },
        artifact_root="logs/quality-review",
    )

    assert view["status"] == "本文は生成されていますが、さらに読みやすく整えられます。"
    assert "必要に応じて、短い指示へ具体的な観点を1つ足して再生成してください" in view["detail"]
    assert "冒頭の読者・課題接続、各見出しの読者接続" in view["detail"]
    assert view["notification"] == "本文を作成しました。必要に応じて観点を足して磨けます。"


def test_route_v_stop_view_body_length_failure_hides_technical_log_path():
    view = _build_stop_view(
        {
            "body": "# 生成済み本文",
            "smoke_evaluator": {
                "failed": ["article_body_length"],
                "details": {"article_char_count": 1267, "article_min_chars": 1300},
            },
        },
        artifact_root="logs/quality-review",
    )

    assert view["status"] == "本文は生成されていますが、本文をもう少し詳しくできそうです。"
    assert "約33文字短い" in view["detail"]
    assert "logs/quality-review" not in view["detail"]
    assert view["progress"] == "本文をもう少し詳しくできそうです。"


def test_route_v_click_without_sources_returns_before_generation(monkeypatch):
    notifications = []
    focus_calls = []
    monkeypatch.setattr(writer_ui.ui, "notify", lambda message, color=None: notifications.append((message, color)))
    state = SimpleNamespace(sources=[], busy=False, result={})
    status = _status_targets()

    def fail_generation(**_kwargs):
        raise AssertionError("generation should not run without sources")

    asyncio.run(
        run_route_v_generation_click(
            state=state,
            controls=_controls(),
            status_targets=status,
            result_targets=_result_targets(),
            fallback_instruction=lambda: "",
            refresh_output_stage_visibility=lambda: None,
            refresh_step_indicators=lambda: None,
            to_plain_dict=dict,
            generation_callable=fail_generation,
            focus_source_input=lambda: focus_calls.append("source-url-input"),
        )
    )

    assert state.busy is False
    assert status.status_label.text == ""
    assert status.source_error_area.content == ""
    assert "資料を1件以上追加してください" in status.missing_source_alert.content
    assert "入力済みの方針や読者設定はそのまま残っています" in status.missing_source_alert.content
    assert _nonempty_alert_count(status) == 1
    assert focus_calls == ["source-url-input"]
    assert notifications == []
