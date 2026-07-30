from __future__ import annotations

from nicegui import ui

from app.services.pipeline_runner import BlogPipelineRunner
from app.services.source_acquisition import ExtractedSource, extract_url_source, ingest_manual_text


GENRE_OPTIONS = {
    "market_explanation": "解説・市場を伝える",
    "company_service_intro": "会社・サービスの紹介記事を書く",
    "announcement": "お知らせを伝える",
    "case_study": "事例・お客様の声を伝える",
    "comparison_guide": "比較・選び方を整理する",
    "daily_activity": "日常のできごとを伝える",
}


def create_ui() -> None:
    ui.colors(primary="#1f6f68", secondary="#334155", accent="#c2410c")
    ui.add_head_html(
        """
        <style>
        body { background: #f7f7f4; color: #1f2933; }
        .app-shell { max-width: 1180px; margin: 0 auto; padding: 20px; }
        .panel { background: #fff; border: 1px solid #d8d8d2; border-radius: 8px; padding: 16px; }
        .dense-label { font-size: 13px; color: #475569; margin-bottom: 4px; }
        .result-box { white-space: pre-wrap; line-height: 1.85; background: #ffffff; border: 1px solid #d8d8d2; border-radius: 8px; padding: 16px; }
        .status-line { color: #334155; font-size: 13px; }
        </style>
        """
    )

    state: dict[str, object] = {"result": None}

    with ui.column().classes("app-shell w-full gap-4"):
        ui.label("Japanese Blog Generator").classes("text-2xl font-bold")
        ui.label("note / はてなブログ向けのソース根拠型オウンドメディア記事生成").classes("status-line")

        with ui.grid(columns=2).classes("w-full gap-4"):
            with ui.column().classes("panel gap-3"):
                ui.label("Source").classes("text-lg font-semibold")
                source_title = ui.input("ソース名", value="会社メモ").classes("w-full")
                manual_text = ui.textarea(
                    "手入力ソース",
                    value=(
                        "私たちは2018年に創業しました。地域の相談を受けています。"
                        "初回相談では、現在の状況、困っていること、希望する進め方を確認します。"
                        "そのうえで、必要な情報を整理し、次に取れる選択肢を説明します。"
                    ),
                ).classes("w-full").props("rows=8")
                url_input = ui.input("URLソース").classes("w-full")
                ui.label("URLは公開HTMLだけを取得します。ログイン、API、検索、アーカイブ系URLは警告で止まります。").classes("status-line")

            with ui.column().classes("panel gap-3"):
                ui.label("Brief").classes("text-lg font-semibold")
                genre = ui.select(GENRE_OPTIONS, value="company_service_intro", label="記事ジャンル").classes("w-full")
                narrator = ui.input("一人称", value="私たち").classes("w-full")
                target_reader = ui.input("対象読者", value="初めてサービスを知る読者").classes("w-full")
                article_goal = ui.input("記事の目的", value="ソースに基づいて自然なブログ記事を作る").classes("w-full")
                ui.label("生成は明示ボタンを押した時だけ実行します。").classes("status-line")

        status = ui.label("待機中").classes("status-line")
        with ui.row().classes("items-center gap-3"):
            run_button = ui.button("生成を実行", icon="play_arrow").props("color=primary")
            artifact_link = ui.link("artifact", "#").classes("hidden")

        with ui.grid(columns=2).classes("w-full gap-4"):
            with ui.column().classes("panel gap-2"):
                ui.label("QA Issues").classes("text-lg font-semibold")
                qa_area = ui.column().classes("w-full gap-2")
            with ui.column().classes("panel gap-2"):
                ui.label("Final Article").classes("text-lg font-semibold")
                final_article = ui.label("").classes("result-box w-full")

        def render_issues(issues: list[dict[str, object]]) -> None:
            qa_area.clear()
            with qa_area:
                if not issues:
                    ui.label("QA issues: 0").classes("status-line")
                    return
                for issue in issues:
                    ui.label(f"{issue['severity']} / {issue['type']}: {issue['reason']}").classes("status-line")

        def collect_sources() -> list[ExtractedSource]:
            sources: list[ExtractedSource] = []
            if str(manual_text.value).strip():
                sources.append(ingest_manual_text(str(manual_text.value), str(source_title.value or "手入力ソース")))
            if str(url_input.value).strip():
                sources.append(extract_url_source(str(url_input.value).strip()))
            return sources

        def run_generation() -> None:
            status.text = "生成中"
            try:
                sources = collect_sources()
                if not sources:
                    status.text = "ソースを入力してください"
                    return
                blocked = [source for source in sources if not source.can_proceed]
                if blocked:
                    status.text = "低信頼または取得不可のソースがあります"
                    render_issues(
                        [
                            {
                                "severity": "high",
                                "type": "source_warning",
                                "reason": f"{source.title}: {'; '.join(source.warnings)}",
                            }
                            for source in blocked
                        ]
                    )
                    return
                result = BlogPipelineRunner().run_extracted_sources(
                    sources,
                    genre_id=str(genre.value),
                    target_reader=str(target_reader.value),
                    article_goal=str(article_goal.value),
                    narrator=str(narrator.value),
                )
                state["result"] = result
                final_article.text = result.final_article
                render_issues(result.quality_check["quality_check"]["issues"])
                artifact_link.set_text(str(result.artifact_dir))
                artifact_link._props["href"] = str(result.artifact_dir)
                artifact_link.update()
                artifact_link.classes(remove="hidden")
                status.text = f"完了: score {result.quality_check['quality_check']['score']}"
            except Exception as exc:
                status.text = f"エラー: {exc}"

        run_button.on_click(run_generation)


create_ui()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Japanese Blog Generator", host="127.0.0.1", port=18080, reload=False)
