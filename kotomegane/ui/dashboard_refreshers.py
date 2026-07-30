from __future__ import annotations

from typing import Any, Callable

from nicegui import ui

from analysis_lib import dedupe_preserve_order
from config import AppConfig, resolve_provider_cache_policy
from ui import charts
from ui.result_story_builders import shorten_question_label


def build_guardrail_text_class(status: str) -> str:
    if status == "ok":
        return "text-self"
    if status in {"warning", "blocked"}:
        return "text-external"
    return "text-support"


def update_summary_refs(
    metric_refs: dict[str, tuple[ui.label, ui.label]],
    summary_refs: dict[str, Any],
    current_result_story: dict[str, Any],
    portfolio_story: dict[str, Any],
    metrics: dict[str, Any],
    tracked_query_rollup_rows: list[dict[str, Any]],
    tracked_delta_summary: dict[str, Any],
    *,
    show_current_result: bool,
) -> None:
    current_status_label = summary_refs.get("current_scope_status")
    current_note_label = summary_refs.get("current_scope_note")
    if show_current_result:
        if current_status_label is not None:
            current_status_label.text = "今回の分析結果"
        if current_note_label is not None:
            current_note_label.text = "ここは今の入力条件で実行した最新結果だけです。保存済みの累積傾向とは分けて見ます。"
        metric_refs["overall"][0].text = current_result_story["overall_label"]
        metric_refs["overall"][1].text = current_result_story["overall_summary"]
        metric_refs["competition"][0].text = current_result_story["competition_label"]
        metric_refs["competition"][1].text = current_result_story["competition_summary"]
        metric_refs["action"][0].text = current_result_story["action_headline"]
        metric_refs["action"][1].text = current_result_story["action_summary"]
    else:
        if current_status_label is not None:
            current_status_label.text = "今の入力では未分析"
        if current_note_label is not None:
            current_note_label.text = "今の入力ではまだ分析していません。これはエラーではありません。保存済み結果は下の累積傾向と履歴だけに置いています。"
        metric_refs["overall"][0].text = "今の入力では未分析"
        metric_refs["overall"][1].text = "質問と自社URLを確認したら、「1回だけ分析」で今回の結果を作ります。"
        metric_refs["competition"][0].text = "保存済み結果は混ぜません"
        metric_refs["competition"][1].text = "前回の保存結果は下の累積傾向と履歴で確認できます。"
        metric_refs["action"][0].text = "今回実行後に表示します"
        metric_refs["action"][1].text = "入力条件を変えたときも、ここは前回結果を残さず空状態に戻します。"
    for label in (current_status_label, current_note_label):
        if label is not None:
            label.update()
    for headline_label, detail_label in metric_refs.values():
        headline_label.update()
        detail_label.update()
    summary_refs["saved_scope"][0].text = portfolio_story["overall_label"]
    summary_refs["saved_scope"][1].text = (
        f"これは今の入力で実行した結果ではなく、保存済みデータの累積集計です。 "
        f"観測した {portfolio_story['total_trials']} 試行のうち {portfolio_story['visible_trials']} 回で自社が見えています。 "
        f"{portfolio_story['competition_summary']}"
    )
    summary_refs["saved_scope"][0].update()
    summary_refs["saved_scope"][1].update()

    if tracked_query_rollup_rows:
        trial_count = int(metrics.get("trial_count") or len(tracked_query_rollup_rows) or 0)
        visible_trial_count = int(metrics.get("visible_trial_count") or 0)
        external_trial_count = int(metrics.get("external_trial_count") or 0)
        owned_citation_trial_count = int(metrics.get("owned_citation_trial_count") or 0)
        summary_refs["kpis"]["target_hit_rate"][0].text = f"{metrics['target_hit_rate']:.1f}%"
        summary_refs["kpis"]["target_hit_rate"][1].text = (
            f"観測した {trial_count} 試行のうち {visible_trial_count} 回で自社URLが根拠に入りました"
        )
        summary_refs["kpis"]["owned_citation_rate"][0].text = f"{float(metrics.get('owned_citation_trial_rate') or 0.0):.1f}%"
        summary_refs["kpis"]["owned_citation_rate"][1].text = (
            f"観測した {trial_count} 試行のうち {owned_citation_trial_count} 回で自社URLが引用されました"
        )
        summary_refs["kpis"]["external_lead_rate"][0].text = f"{metrics['external_lead_rate']:.1f}%"
        summary_refs["kpis"]["external_lead_rate"][1].text = (
            f"観測した {trial_count} 試行のうち {external_trial_count} 回で外部サイトが先行しました"
        )
    else:
        summary_refs["kpis"]["target_hit_rate"][0].text = "--"
        summary_refs["kpis"]["target_hit_rate"][1].text = "自動チェックの履歴がまだありません。"
        summary_refs["kpis"]["owned_citation_rate"][0].text = "--"
        summary_refs["kpis"]["owned_citation_rate"][1].text = "自動チェックの結果から集計します。"
        summary_refs["kpis"]["external_lead_rate"][0].text = "--"
        summary_refs["kpis"]["external_lead_rate"][1].text = "1回だけ確認はここに混ぜません。"

    if tracked_delta_summary.get("available"):
        summary_refs["kpis"]["delta"][0].text = f"{float(tracked_delta_summary['target_hit_rate_delta']):+.1f}pt"
        summary_refs["kpis"]["delta"][1].text = "前回の自動チェックとの差"
    else:
        summary_refs["kpis"]["delta"][0].text = "--"
        summary_refs["kpis"]["delta"][1].text = str(tracked_delta_summary.get("reason") or "前回の保存結果との差はまだありません。")
    for value_label, detail_label in summary_refs["kpis"].values():
        value_label.update()
        detail_label.update()

    if tracked_query_rollup_rows:
        summary_refs["tracking_note"].text = (
            f"ここは自動チェック {len(tracked_query_rollup_rows)}件分だけを集計しています。"
            " ここに出す割合はすべて観測試行数を分母にしています。"
            " 点が少ない間は、横軸に保存時刻をそのまま表示します。"
            " 1回だけ確認の結果は今回の結果と履歴、質問別推移で見ます。"
        )
    else:
        summary_refs["tracking_note"].text = (
            "まだ自動チェックはありません。ここには自動チェックの結果だけが入ります。"
            " 履歴はありますが、グラフ化できる自動チェック結果はまだありません。"
            " 1回だけ確認の結果は今回の結果と履歴、質問別推移で見てください。"
        )
    summary_refs["tracking_note"].update()


def update_decision_refs(
    decision_refs: dict[str, dict[str, Any]],
    intent_rows: list[dict[str, Any]],
    page_gap_rows: list[dict[str, Any]],
    total_trial_count: int,
    budget_guardrail: dict[str, Any],
    config: AppConfig,
) -> None:
    if intent_rows:
        weakest_intent = intent_rows[0]
        decision_refs["intent"]["headline"].text = f"{weakest_intent['intent_label']} の露出が弱い"
        decision_refs["intent"]["summary"].text = (
            f"観測した {total_trial_count} 試行のうち {weakest_intent['needs_fix_count']} 回で見えにくい状態です。"
            " この質問タイプはまだ弱めです。"
        )
    else:
        decision_refs["intent"]["headline"].text = "弱い質問タイプは未判定"
        decision_refs["intent"]["summary"].text = "自動チェックの結果が保存されると、どの質問タイプで弱いかをここで示します。"
    decision_refs["intent"]["headline"].update()
    decision_refs["intent"]["summary"].update()
    decision_refs["intent"]["table"].rows = intent_rows
    decision_refs["intent"]["table"].update()

    if page_gap_rows:
        top_gap = page_gap_rows[0]
        decision_refs["gap"]["headline"].text = f"{top_gap['page_type_label']} が不足"
        decision_refs["gap"]["summary"].text = (
            f"観測した {total_trial_count} 試行のうち {top_gap['needs_fix_count']} 回でこの情報タイプが見えにくい状態です。"
        )
    else:
        decision_refs["gap"]["headline"].text = "不足している情報タイプは未判定"
        decision_refs["gap"]["summary"].text = "自動チェックの結果が保存されると、どの情報タイプが不足しているかをここに出します。"
    decision_refs["gap"]["headline"].update()
    decision_refs["gap"]["summary"].update()
    decision_refs["gap"]["table"].rows = page_gap_rows
    decision_refs["gap"]["table"].update()

    if decision_refs.get("budget"):
        decision_refs["budget"]["headline"].text = budget_guardrail["headline"]
        decision_refs["budget"]["headline"].classes(replace=f"summary-mainline mt-2 {build_guardrail_text_class(budget_guardrail['status'])}")
        decision_refs["budget"]["summary"].text = budget_guardrail["summary"]
        decision_refs["budget"]["today"].text = f"{int(budget_guardrail['today_result_count'] or 0)}件"
        decision_refs["budget"]["estimate"].text = f"{int(budget_guardrail['request_count'] or 0)}件"
        decision_refs["budget"]["remaining"].text = budget_guardrail["guardrail_mode_label"]
        cache_policy = resolve_provider_cache_policy(config.provider, config.model, config.prompt_cache_retention)
        decision_refs["budget"]["efficiency"].text = cache_policy["display_label"]
        decision_refs["budget"]["note"].text = (
            cache_policy["switch_note"]
            if cache_policy.get("switch_note")
            else f"{cache_policy['note']} 金額は非表示のまま内部の実行ガードだけ維持しています。"
        )
        for key in ("headline", "summary", "today", "estimate", "remaining", "efficiency", "note"):
            decision_refs["budget"][key].update()


def update_tracking_widgets(
    summary_refs: dict[str, Any],
    tracked_recent_rows: list[dict[str, Any]],
    heatmap_rows: list[dict[str, Any]],
    heatmap_raw_rows: list[dict[str, Any]],
    drilldown_rows: list[dict[str, Any]],
    query_select: ui.select,
    drilldown_query_rows: list[dict[str, Any]],
    question_heatmap_plot: Any,
    query_drilldown_plot: Any,
    intent_trend_plot: Any,
    page_gap_trend_plot: Any,
    config: AppConfig,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
) -> None:
    visibility_plot = (summary_refs.get("plots") or {}).get("visibility")
    if visibility_plot is not None:
        visibility_plot.figure = charts.build_overall_visibility_chart(tracked_recent_rows, config)
        visibility_plot.update()
    history_focus_plot = (summary_refs.get("plots") or {}).get("history_focus")
    if history_focus_plot is not None:
        history_focus_plot.figure = charts.build_visibility_focus_chart(tracked_recent_rows, config)
        history_focus_plot.update()

    query_options = {
        keyword: shorten_question_label(keyword, limit=28)
        for keyword in dedupe_preserve_order([str(row.get("keyword_raw") or "") for row in drilldown_query_rows if row.get("keyword_raw")])
    }
    query_select.options = query_options
    if query_select.value not in query_options and query_options:
        query_select.value = next(iter(query_options))
    query_select.update()

    if question_heatmap_plot is not None:
        question_heatmap_plot.figure = charts.build_question_result_heatmap_chart(
            heatmap_rows,
            heatmap_raw_rows,
            config,
            source_loader,
        )
        question_heatmap_plot.update()
    if query_drilldown_plot is not None:
        query_drilldown_plot.figure = charts.build_query_drilldown_chart(drilldown_rows, str(query_select.value or ""))
        query_drilldown_plot.update()
    if intent_trend_plot is not None:
        intent_trend_plot.figure = charts.build_intent_cluster_chart(tracked_recent_rows, config)
        intent_trend_plot.update()
    if page_gap_trend_plot is not None:
        page_gap_trend_plot.figure = charts.build_page_gap_trend_chart(tracked_recent_rows, config)
        page_gap_trend_plot.update()
