"""Main-page pre-generation section builders for note_writer_app Phase 05."""
from __future__ import annotations

from typing import Any, Callable, Mapping

from nicegui import ui


def build_article_type_descriptions() -> dict[str, str]:
    return {
        "解説": "専門情報を読者が行動できる形に翻訳する。",
        "日常": "日々の出来事と学びを短く自然に共有する。",
        "ブランド": "価値訴求を読者視点で具体化する。",
        "お知らせ": "変更点を簡潔かつ正確に伝える。",
        "事例": "再現可能な実行手順と成果を示す。",
        "業界分析": "比較軸と根拠を明示して分析する。",
        "比較レビュー": "候補の違いを評価軸で整理する。",
    }


def build_source_mode_choice_card_copy() -> dict[str, dict[str, str]]:
    return {
        "grounded": {
            "title": "資料あり",
            "summary": "URL / PDF / 画像 / テキストを先に追加して、その材料を軸に書きます。",
            "detail": "資料がある案件向け。必須項目と資料入力をまとめて進めます。",
        },
        "web": {
            "title": "お任せ",
            "summary": "1行テーマで始め、公開済みブログの蓄積が十分なときだけ外部ソースの材料収集へ進みます。",
            "detail": "利用条件は公開済み3件以上かつ合計本文4500字以上です。公開済みブログ本文は今回の記事の事実ソースにしません。",
        },
        "prompt_only": {
            "title": "プロンプトのみ",
            "summary": "公開済みブログの蓄積がある日常記事だけ、1行テーマを体験メモとして使います。",
            "detail": "公開済みブログは書き味の参考です。今回記事の事実ソースにはしません。",
        },
    }


def render_brand_header(
    *,
    hub_url: str,
    kotomegane_url: str,
    sanitize_html: Callable[[str], str],
) -> None:
    with ui.row().classes("brand-header"):
        ui.html(
            '<img src="/static/brand/kotomake_logo_cropped.svg" alt="TECHIE" class="brand-logo-inline" />',
            sanitize=sanitize_html,
        )
        with ui.column().classes("brand-copy"):
            ui.label("TECHIE").classes("brand-pill")
            ui.html('<h1 class="hero-title">コトメイク</h1>', sanitize=False)
            ui.label("発信作成").classes("hero-role")
            ui.label("ブログ生成で流入導線を作る").classes("hero-sub")
            ui.label("次は見え方を観測する").classes("hero-next")
        with ui.row().classes("suite-link-row"):
            ui.label("入力: URL / PDF / 画像").classes("brand-pill")
            ui.link("見え方観測へ", kotomegane_url, new_tab=True).classes("suite-link-btn")


def render_step_track(*, current_mainline_ui_mode: str) -> dict[str, Any]:
    with ui.row().classes("step-track w-full") as step_track:
        sticky_step1 = ui.label("① 入力").classes("step-track-item step-track-active sticky-s1")
        ui.label("→").style("color: #D8B9AA; font-size: 14px; line-height: 1;")
        sticky_step2 = ui.label("② 生成準備").classes("step-track-item step-track-pending sticky-s2")
        ui.label("→").style("color: #D8B9AA; font-size: 14px; line-height: 1;")
        sticky_step3 = ui.label("③ 生成結果").classes("step-track-item step-track-pending sticky-s3")
    step_track.visible = current_mainline_ui_mode != "journey"
    return {
        "step_track": step_track,
        "sticky_step1": sticky_step1,
        "sticky_step2": sticky_step2,
        "sticky_step3": sticky_step3,
    }


def render_source_mode_choice_cards() -> dict[str, Any]:
    source_mode_choice_cards: dict[str, Any] = {}
    with ui.row().classes("w-full source-mode-choice-row"):
        for mode_key in ("grounded", "web", "prompt_only"):
            copy = build_source_mode_choice_card_copy()[mode_key]
            mode_card = ui.card().classes("w-full p-4 gap-2 source-mode-choice-card")
            source_mode_choice_cards[mode_key] = mode_card
            with mode_card:
                ui.label(str(copy["title"])).classes("text-base font-semibold text-[#3D2E28]")
                ui.label(str(copy["summary"])).classes("text-sm text-[#5D4A41]")
                ui.label(str(copy["detail"])).classes("text-xs text-gray-600")
    return source_mode_choice_cards


def render_required_input_fields(
    *,
    in_wizard: bool,
    initial_type_key: str,
    default_audience_profile_text: str,
    default_audience_profile_placeholder_text: str,
    get_writer_role_options: Callable[[str], list[str]],
    get_default_writer_role_label: Callable[[str], str],
) -> dict[str, Any]:
    container_classes = (
        "w-full gap-3 mt-3 p-4 required-input-card"
        if in_wizard
        else "w-full gap-3 mt-4 p-4 required-input-card"
    )
    heading_text = "記事の前提" if in_wizard else "生成前に決めること"
    helper_text = (
        "STEP3とSTEP4で、誰向けにどの立場で書くかをそろえます。"
        if in_wizard
        else "まず記事タイプ・誰向け・誰視点だけをそろえます。補助項目は詳細設定で調整します。"
    )
    audience_step_card = None
    writer_step_card = None
    audience_summary_row = None
    writer_summary_row = None
    audience_summary_value_label = None
    writer_summary_value_label = None
    audience_next_button = None
    writer_done_button = None
    audience_edit_button = None
    writer_edit_button = None
    required_article_type_label_widget = None
    audience_profile_input_widget = None
    audience_profile_status_label_widget = None
    writer_role_select_widget = None
    writer_role_status_label_widget = None
    pronoun_hint_label_widget = None
    writer_role_custom_toggle_widget = None
    writer_role_custom_widget = None

    with ui.column().classes(container_classes):
        ui.label(heading_text).classes("text-sm font-semibold text-gray-800")
        required_input_summary_label_widget = ui.label(helper_text).classes("text-xs text-gray-600")
        if in_wizard:
            with ui.column().classes(
                "w-full gap-2 p-3 rounded-xl border border-[rgba(222,146,73,0.14)] bg-white"
            ) as audience_step_card:
                ui.label("STEP3 読者").classes("text-[11px] font-bold tracking-wide text-amber-700")
                audience_profile_input_widget = ui.input(
                    "主な読者",
                    value=default_audience_profile_text,
                    placeholder=default_audience_profile_placeholder_text,
                ).classes("w-full").props("outlined stack-label")
                audience_profile_status_label_widget = ui.label(
                    "※誰向けに書くかだけ明示してください。"
                ).classes("text-xs text-gray-600")
                with ui.row().classes("w-full justify-end"):
                    audience_next_button = ui.button("次へ").classes("primary-btn")
            with ui.row().classes(
                "w-full items-center justify-between gap-3 rounded-xl border border-[rgba(82,145,96,0.20)] bg-[rgba(241,252,244,0.92)] px-4 py-3"
            ) as audience_summary_row:
                with ui.column().classes("gap-1"):
                    ui.label("STEP3 読者").classes("text-[11px] font-bold tracking-wide text-green-700")
                    audience_summary_value_label = ui.label("").classes("text-sm text-[#5D4A41]")
                audience_edit_button = ui.button("修正").props("outline")
            audience_summary_row.visible = False
            with ui.column().classes(
                "w-full gap-2 p-3 rounded-xl border border-[rgba(222,146,73,0.14)] bg-white"
            ) as writer_step_card:
                ui.label("STEP4 書き手").classes("text-[11px] font-bold tracking-wide text-amber-700")
                writer_role_select_widget = ui.select(
                    options=get_writer_role_options(initial_type_key),
                    value=get_default_writer_role_label(initial_type_key),
                    label="誰の立場で書くか",
                ).classes("w-full").props("outlined stack-label")
                writer_role_status_label_widget = ui.label(
                    "内容に合う書き手を初期選択しています。"
                ).classes("text-xs text-gray-600 -mt-1 pl-1")
                pronoun_hint_label_widget = ui.label("").classes("text-xs text-gray-600 -mt-1 pl-1")
                with ui.expansion("書き手を細かく指定する（任意）", icon="edit_note").classes("w-full"):
                    writer_role_custom_toggle_widget = ui.checkbox(
                        "自由入力で書き手を指定する",
                        value=False,
                    ).classes("w-full")
                    writer_role_custom_widget = ui.input(
                        "書き手（自由入力）",
                        placeholder="例: 編集担当として語る",
                    ).classes("w-full").props("outlined stack-label")
                    writer_role_custom_widget.visible = False
                with ui.row().classes("w-full justify-end"):
                    writer_done_button = ui.button("確認へ").classes("primary-btn")
            with ui.row().classes(
                "w-full items-center justify-between gap-3 rounded-xl border border-[rgba(82,145,96,0.20)] bg-[rgba(241,252,244,0.92)] px-4 py-3"
            ) as writer_summary_row:
                with ui.column().classes("gap-1"):
                    ui.label("STEP4 書き手").classes("text-[11px] font-bold tracking-wide text-green-700")
                    writer_summary_value_label = ui.label("").classes("text-sm text-[#5D4A41]")
                writer_edit_button = ui.button("修正").props("outline")
            writer_summary_row.visible = False
        else:
            required_article_type_label_widget = ui.label(
                "記事タイプ: 未選択"
            ).classes("text-xs font-medium text-amber-700 bg-amber-50 px-3 py-2 rounded-lg")
            writer_role_select_widget = ui.select(
                options=get_writer_role_options(initial_type_key),
                value=get_default_writer_role_label(initial_type_key),
                label="誰の立場で書くか",
            ).classes("w-full").props("outlined stack-label")
            writer_role_status_label_widget = ui.label(
                "内容に合う書き手を初期選択しています。"
            ).classes("text-xs text-gray-600 -mt-1 pl-1")
            pronoun_hint_label_widget = ui.label("").classes("text-xs text-gray-600 -mt-1 pl-1")
            audience_profile_input_widget = ui.input(
                "主な読者",
                value=default_audience_profile_text,
                placeholder=default_audience_profile_placeholder_text,
            ).classes("w-full").props("outlined stack-label")
            audience_profile_status_label_widget = ui.label(
                "※誰向けに書くかだけ明示してください。"
            ).classes("text-xs text-gray-600")
            with ui.expansion("書き手を細かく指定する（任意）", icon="edit_note").classes("w-full"):
                writer_role_custom_toggle_widget = ui.checkbox(
                    "自由入力で書き手を指定する",
                    value=False,
                ).classes("w-full")
                writer_role_custom_widget = ui.input(
                    "書き手（自由入力）",
                    placeholder="例: 編集担当として語る",
                ).classes("w-full").props("outlined stack-label")
                writer_role_custom_widget.visible = False
    return {
        "required_input_summary_label": required_input_summary_label_widget,
        "required_article_type_label": required_article_type_label_widget,
        "writer_role_select": writer_role_select_widget,
        "writer_role_status_label": writer_role_status_label_widget,
        "pronoun_hint_label": pronoun_hint_label_widget,
        "audience_profile_input": audience_profile_input_widget,
        "audience_profile_status_label": audience_profile_status_label_widget,
        "writer_role_custom_toggle": writer_role_custom_toggle_widget,
        "writer_role_custom": writer_role_custom_widget,
        "audience_step_card": audience_step_card,
        "writer_step_card": writer_step_card,
        "audience_summary_row": audience_summary_row,
        "writer_summary_row": writer_summary_row,
        "audience_summary_value_label": audience_summary_value_label,
        "writer_summary_value_label": writer_summary_value_label,
        "audience_next_button": audience_next_button,
        "writer_done_button": writer_done_button,
        "audience_edit_button": audience_edit_button,
        "writer_edit_button": writer_edit_button,
    }


def render_journey_flow_sections(
    *,
    current_mainline_ui_mode: str,
    journey_purpose_labels: Mapping[str, str],
    initial_journey_target_options: Mapping[str, str],
    journey_compare_axis_options: Mapping[str, str],
    journey_compare_goal_labels: Mapping[str, str],
    journey_outline_action_style: str,
    required_input_fields_renderer: Callable[..., Mapping[str, Any]],
) -> dict[str, Any]:
    required_input_widgets: Mapping[str, Any] = {}
    with ui.column().classes("w-full gap-3 mb-2") as journey_flow_container:
        with ui.card().classes("w-full p-4 gap-3 journey-stage-card journey-stage-card-active") as journey_direction_card:
            ui.label("記事の向き先").classes("text-sm font-semibold text-gray-700")
            ui.label("出し方と書く内容をここでそろえます。").classes("text-xs text-gray-600")
            with ui.column().classes(
                "w-full gap-2 p-3 rounded-xl border border-[rgba(222,146,73,0.20)] bg-[rgba(255,248,242,0.90)]"
            ) as journey_purpose_step_card:
                ui.label("STEP1 出し方").classes("text-[11px] font-bold tracking-wide text-amber-700")
                journey_purpose = ui.select(
                    options=list(journey_purpose_labels.values()),
                    value=journey_purpose_labels["explain"],
                    label="どこに出すか",
                ).classes("w-full").props("outlined stack-label")
                ui.label("読者にどう届く記事かを決めます。").classes("text-xs text-gray-600")
                with ui.row().classes("w-full justify-end"):
                    journey_purpose_next_button = ui.button("次へ").classes("primary-btn")
            with ui.row().classes(
                "w-full items-center justify-between gap-3 rounded-xl border border-[rgba(82,145,96,0.20)] bg-[rgba(241,252,244,0.92)] px-4 py-3"
            ) as journey_purpose_summary_row:
                with ui.column().classes("gap-1"):
                    ui.label("STEP1 出し方").classes("text-[11px] font-bold tracking-wide text-green-700")
                    journey_purpose_summary_value = ui.label("").classes("text-sm text-[#5D4A41]")
                journey_purpose_edit_button = ui.button("修正").props("outline")
            journey_purpose_summary_row.visible = False
            with ui.column().classes(
                "w-full gap-2 p-3 rounded-xl border border-[rgba(222,146,73,0.14)] bg-white"
            ) as journey_target_step_card:
                ui.label("STEP2 内容").classes("text-[11px] font-bold tracking-wide text-amber-700")
                journey_target_options = list(initial_journey_target_options.values())
                journey_target = ui.select(
                    options=journey_target_options,
                    value=journey_target_options[0],
                    label="何を書くか",
                ).classes("w-full").props("outlined stack-label")
                journey_target_hint = ui.label("上の選択に合わせて候補を絞っています。").classes("text-xs text-gray-600")
                with ui.row().classes("w-full justify-end"):
                    journey_target_next_button = ui.button("次へ").classes("primary-btn")
            with ui.row().classes(
                "w-full items-center justify-between gap-3 rounded-xl border border-[rgba(82,145,96,0.20)] bg-[rgba(241,252,244,0.92)] px-4 py-3"
            ) as journey_target_summary_row:
                with ui.column().classes("gap-1"):
                    ui.label("STEP2 内容").classes("text-[11px] font-bold tracking-wide text-green-700")
                    journey_target_summary_value = ui.label("").classes("text-sm text-[#5D4A41]")
                journey_target_edit_button = ui.button("修正").props("outline")
            journey_target_summary_row.visible = False
            if current_mainline_ui_mode == "journey":
                required_input_widgets = required_input_fields_renderer(in_wizard=True)
        with ui.card().classes("w-full p-4 gap-3 journey-stage-card journey-stage-card-active") as journey_step3_card:
            ui.label("比較の条件").classes("text-sm font-semibold text-gray-700")
            journey_detail_hint = ui.label("比較レビューのときだけ、比較の軸を補います。").classes("text-xs text-gray-600")
            with ui.column().classes("w-full gap-3") as compare_detail_container:
                with ui.row().classes("w-full gap-3"):
                    comparison_axis_checks: dict[str, Any] = {}
                    with ui.column().classes("gap-1"):
                        for axis_key, axis_label in journey_compare_axis_options.items():
                            comparison_axis_checks[axis_key] = ui.checkbox(axis_label, value=(axis_key == "overall"))
                custom_compare_axis_input = ui.input(
                    "比較軸を補足する（任意）",
                    placeholder="例: 導入しやすさ",
                ).classes("w-full").props("outlined stack-label")
                compare_goal_select = ui.select(
                    options=list(journey_compare_goal_labels.values()),
                    value=journey_compare_goal_labels["fit_explain"],
                    label="比較のゴール",
                ).classes("w-full").props("outlined stack-label")
        with ui.card().classes("w-full p-4 gap-3").style(
            "border: 1px solid rgba(72,58,50,0.16); "
            "background: linear-gradient(180deg, #FFFCFA 0%, #FFF6F1 100%); "
            "box-shadow: 0 10px 24px rgba(42,31,26,0.08);"
        ) as journey_step4_card:
            with ui.row().classes("w-full items-start justify-between gap-3"):
                with ui.column().classes("gap-1"):
                    ui.label("不足チェック").classes("text-sm font-semibold text-gray-700")
                    journey_confirm_action_hint = ui.label(
                        "不足や確認結果だけを表示します。生成は下の明示ボタンから始めます。"
                    ).classes("text-xs text-gray-700")
                journey_confirm_badge = ui.label("未確認").classes(
                    "text-xs font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full whitespace-nowrap"
                )
            journey_confirm_summary = ui.markdown("選択内容をまとめます。").classes("text-sm text-gray-700")
            journey_confirm_source_fit = ui.label("材料のそろい具合は、まだ確認していません。").classes("text-xs text-gray-600")
            journey_confirm_grounding = ui.label("記事に必要な根拠は、まだ確認していません。").classes("text-xs text-gray-600")
            journey_confirm_missing = ui.markdown("").classes("text-xs text-amber-700")
            journey_confirm_status = ui.label(
                "まだ未確認です。「内容を確認」で不足だけを確認できます。"
            ).classes("text-xs text-gray-600")
            with ui.row().classes("w-full justify-start gap-2"):
                journey_preview_button = ui.button("内容を確認").props("outline").style(journey_outline_action_style)
                journey_confirm_button = ui.button("内容を確認").classes("primary-btn")
            with ui.column().classes("w-full gap-2 mt-2") as interview_followup_container:
                interview_followup_container.visible = False
                with ui.card().classes("w-full p-3 narrow-support-card").style(
                    "border: 1px solid rgba(72,58,50,0.10); background: #FFFCFA;"
                ):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("quiz", size="sm").classes("text-orange-600")
                        ui.label("確認が必要な項目").classes("text-sm font-semibold text-gray-700")
                    interview_followup_note = ui.label(
                        "不足情報があるときだけ、必要な確認項目を表示します。"
                    ).classes("text-xs text-gray-600")
                    interview_followup_status = ui.label("").classes("text-xs text-gray-600")
                    interview_generate_button = ui.button(
                        "確認項目を表示",
                        icon="edit_note",
                    ).props("outline").classes("primary-btn mb-1")
                    interview_questions_container = ui.column().classes("w-full gap-3").style(
                        "max-height: 320px; overflow-y: auto; padding-right: 4px;"
                    )

    return {
        "journey_flow_container": journey_flow_container,
        "journey_direction_card": journey_direction_card,
        "journey_purpose_step_card": journey_purpose_step_card,
        "journey_target_step_card": journey_target_step_card,
        "journey_purpose_summary_row": journey_purpose_summary_row,
        "journey_target_summary_row": journey_target_summary_row,
        "journey_purpose_summary_value": journey_purpose_summary_value,
        "journey_target_summary_value": journey_target_summary_value,
        "journey_purpose_next_button": journey_purpose_next_button,
        "journey_target_next_button": journey_target_next_button,
        "journey_purpose_edit_button": journey_purpose_edit_button,
        "journey_target_edit_button": journey_target_edit_button,
        "journey_purpose": journey_purpose,
        "journey_target": journey_target,
        "journey_target_hint": journey_target_hint,
        "journey_step3_card": journey_step3_card,
        "journey_detail_hint": journey_detail_hint,
        "compare_detail_container": compare_detail_container,
        "comparison_axis_checks": comparison_axis_checks,
        "custom_compare_axis_input": custom_compare_axis_input,
        "compare_goal_select": compare_goal_select,
        "journey_step4_card": journey_step4_card,
        "journey_confirm_action_hint": journey_confirm_action_hint,
        "journey_confirm_badge": journey_confirm_badge,
        "journey_confirm_summary": journey_confirm_summary,
        "journey_confirm_source_fit": journey_confirm_source_fit,
        "journey_confirm_grounding": journey_confirm_grounding,
        "journey_confirm_missing": journey_confirm_missing,
        "journey_confirm_status": journey_confirm_status,
        "journey_preview_button": journey_preview_button,
        "journey_confirm_button": journey_confirm_button,
        "interview_followup_container": interview_followup_container,
        "interview_followup_note": interview_followup_note,
        "interview_followup_status": interview_followup_status,
        "interview_generate_button": interview_generate_button,
        "interview_questions_container": interview_questions_container,
        "required_input_widgets": dict(required_input_widgets),
    }


def render_result_output_sections(
    *,
    preview_placeholder: str,
    render_between_preview_and_details: Callable[[], None] | None = None,
) -> dict[str, Any]:
    with ui.column().classes("output-stage-shell") as output_stage_shell:
        ui.html('<div id="generation-result-anchor"></div>', sanitize=False)
        with ui.card().classes("output-card p-6 w-full fade-in step-card-3"):
            with ui.row().classes("items-center gap-2 mb-1"):
                step3_badge = ui.label("生成結果").classes(
                    "text-xs font-bold bg-gray-100 text-gray-400 px-2 py-0.5 rounded tracking-widest"
                )
                ui.label("生成結果").classes("section-title m-0")
            ui.label(
                "生成前は小さく待機し、生成後はここから順に確認できる形で表示します。"
            ).classes("output-static-label")

            ui.separator()
            with ui.column().classes("generated-preview-shell"):
                with ui.row().classes("generated-preview-header"):
                    ui.label("記事プレビュー").classes("generated-chip")
                    stats_label = ui.label("").classes("generated-stats")
                with ui.column().classes("generated-preview-card"):
                    preview = ui.markdown(preview_placeholder).classes(
                        "article-preview article-preview-placeholder w-full"
                    )
                copy_note_format_button = ui.button("記事形式でコピー", icon="content_copy").classes(
                    "primary-btn w-full"
                )

            if render_between_preview_and_details is not None:
                render_between_preview_and_details()

            ui.separator()
            with ui.expansion("生成結果の詳細", icon="expand_more").classes(
                "w-full generated-output-expansion"
            ):
                ui.label("ここから下は生成済みの各出力です。必要なものだけ開いて使います。").classes(
                    "section-muted-note mb-2"
                )
                note_body_text = ui.textarea("本文（リード+本文+参考資料）", value="").props(
                    "readonly"
                ).classes("w-full generated-readonly")
                copy_markdown_button = ui.button("Markdownでコピー", icon="code").props("flat")

                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-grow"):
                        title_area = ui.textarea("タイトル", value="").props("readonly").classes(
                            "w-full generated-readonly"
                        )
                        copy_title_button = ui.button("タイトルをコピー").props("flat dense")
                    with ui.column().classes("flex-grow"):
                        hashtags_area = ui.textarea("ハッシュタグ", value="").props(
                            "readonly"
                        ).classes("w-full generated-readonly")
                        copy_hashtags_button = ui.button("ハッシュタグをコピー").props("flat dense")

                with ui.expansion("個別セクション", icon="unfold_more").classes(
                    "w-full generated-output-expansion"
                ):
                    lead_area = ui.textarea("リード", value="").props("readonly").classes(
                        "w-full generated-readonly"
                    )
                    copy_lead_button = ui.button("リードをコピー").props("flat dense")

                    body_area = ui.textarea("本文", value="").props("readonly").classes(
                        "w-full generated-readonly"
                    )
                    copy_body_button = ui.button("本文をコピー").props("flat dense")

                    references_area = ui.textarea("参考資料", value="").props("readonly").classes(
                        "w-full generated-readonly"
                    )
                    copy_references_button = ui.button("参考資料をコピー").props("flat dense")

                    full_text_area = ui.textarea("全文（タイトル含む）", value="").props(
                        "readonly"
                    ).classes("w-full generated-readonly")
                    copy_full_text_button = ui.button("全文をコピー").props("flat dense")

                with ui.expansion("SNS用出力", icon="share").classes(
                    "w-full generated-output-expansion"
                ):
                    ui.label("SNS用の生成結果です。必要なときだけ開いてコピーします。").classes(
                        "section-muted-note mb-2"
                    )
                    linkedin_area = ui.textarea("SNS投稿用テキスト（長文）", value="").props(
                        "readonly"
                    ).classes("w-full generated-readonly")
                    copy_linkedin_button = ui.button("SNSテキストをコピー", icon="content_copy").classes(
                        "primary-btn"
                    )
                    with ui.expansion("短縮版（任意）", icon="short_text").classes(
                        "w-full mt-2 generated-output-expansion"
                    ):
                        linkedin_short_area = ui.textarea("SNS投稿用テキスト（短文）", value="").props(
                            "readonly"
                        ).classes("w-full generated-readonly")
                        copy_linkedin_short_button = ui.button(
                            "短文SNSテキストをコピー",
                            icon="content_copy",
                        ).props("flat")

        ui.separator()
        quality_summary_card = ui.column().classes("w-full quality-summary-card")
        quality_summary_card.visible = False
        quality_summary_row_widgets: list[dict[str, Any]] = []
        with quality_summary_card:
            with ui.row().classes("quality-summary-header"):
                quality_summary_badge = ui.label("").classes("quality-summary-badge")
                quality_summary_title = ui.label("").classes("quality-summary-title")
            quality_summary_note = ui.label("").classes("quality-summary-note")
            for _ in range(4):
                row = ui.row().classes("quality-summary-row")
                row.visible = False
                with row:
                    ui.icon("fact_check", size="sm").classes("text-[#8A3F18] mt-0.5")
                    with ui.column().classes("quality-summary-row-copy"):
                        title = ui.label("").classes("quality-summary-row-title")
                        detail = ui.label("").classes("quality-summary-row-detail")
                        codes = ui.label("").classes("quality-summary-row-codes")
                quality_summary_row_widgets.append(
                    {
                        "row": row,
                        "title": title,
                        "detail": detail,
                        "codes": codes,
                    }
                )

        review_container = ui.column().classes("w-full quality-hint-card")
        review_container.visible = False
        with review_container:
            with ui.row().classes("items-center gap-1 mb-1"):
                ui.icon("tips_and_updates", size="sm").classes("text-orange-600")
                ui.label("読みやすさのヒント").classes("quality-hint-title")
            review_row_kousei = ui.row().classes("items-center gap-2")
            review_row_kousei.visible = False
            with review_row_kousei:
                ui.label("構成").classes("quality-hint-chip")
                review_kousei_label = ui.label("").classes("quality-hint-text")
            review_row_buntai = ui.row().classes("items-center gap-2")
            review_row_buntai.visible = False
            with review_row_buntai:
                ui.label("文体").classes("quality-hint-chip")
                review_buntai_label = ui.label("").classes("quality-hint-text")
            review_row_konkyo = ui.row().classes("items-center gap-2")
            review_row_konkyo.visible = False
            with review_row_konkyo:
                ui.label("根拠").classes("quality-hint-chip")
                review_konkyo_label = ui.label("").classes("quality-hint-text")

    output_stage_shell.visible = False
    return {
        "output_stage_shell": output_stage_shell,
        "step3_badge": step3_badge,
        "stats_label": stats_label,
        "preview": preview,
        "note_body_text": note_body_text,
        "title_area": title_area,
        "hashtags_area": hashtags_area,
        "lead_area": lead_area,
        "body_area": body_area,
        "references_area": references_area,
        "full_text_area": full_text_area,
        "linkedin_area": linkedin_area,
        "linkedin_short_area": linkedin_short_area,
        "copy_note_format_button": copy_note_format_button,
        "copy_markdown_button": copy_markdown_button,
        "copy_title_button": copy_title_button,
        "copy_hashtags_button": copy_hashtags_button,
        "copy_lead_button": copy_lead_button,
        "copy_body_button": copy_body_button,
        "copy_references_button": copy_references_button,
        "copy_full_text_button": copy_full_text_button,
        "copy_linkedin_button": copy_linkedin_button,
        "copy_linkedin_short_button": copy_linkedin_short_button,
        "quality_summary_card": quality_summary_card,
        "quality_summary_badge": quality_summary_badge,
        "quality_summary_title": quality_summary_title,
        "quality_summary_note": quality_summary_note,
        "quality_summary_row_widgets": quality_summary_row_widgets,
        "review_container": review_container,
        "review_row_kousei": review_row_kousei,
        "review_kousei_label": review_kousei_label,
        "review_row_buntai": review_row_buntai,
        "review_buntai_label": review_buntai_label,
        "review_row_konkyo": review_row_konkyo,
        "review_konkyo_label": review_konkyo_label,
    }
