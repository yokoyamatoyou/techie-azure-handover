from __future__ import annotations

import time
from typing import Any, Callable

from analysis_lib import build_overview_metrics, build_query_rollup_rows, build_source_priority_actions, format_timestamp
from config import AppConfig
from ui.result_story_builders import build_intent_map_rows, build_page_gap_rows, build_portfolio_story, localize_analysis_mode


def build_report_summary_markdown(
    rows: list[dict[str, Any]],
    config: AppConfig,
    source_loader: Callable[[str], list[dict[str, Any]]],
) -> str:
    generated_at = format_timestamp(time.time())
    if not rows:
        return (
            "# コトメガネ 報告用まとめ\n\n"
            f"- 生成: {generated_at}\n"
            "- 対象: まだ保存済み結果がありません\n\n"
            "分析結果が保存されると、このファイルに共有用の要約を出力します。"
        )

    query_rollup_rows = build_query_rollup_rows(rows)
    metrics = build_overview_metrics(query_rollup_rows, config.pricing.usd_to_jpy, config)
    portfolio_story = build_portfolio_story(query_rollup_rows, config)
    intent_rows = build_intent_map_rows(query_rollup_rows, config)
    page_gap_rows = build_page_gap_rows(query_rollup_rows, config)
    source_priority_actions = build_source_priority_actions(rows, source_loader, config)
    weakest_intent = intent_rows[0] if intent_rows else None
    top_gap = page_gap_rows[0] if page_gap_rows else None

    lines = [
        "# コトメガネ 報告用まとめ",
        "",
        f"- 生成: {generated_at}",
        f"- 監査モード: {localize_analysis_mode(config.analysis_mode)}",
        f"- 対象試行数: {int(metrics.get('trial_count') or 0)}回",
        f"- 自社露出率: {metrics['target_hit_rate']:.1f}%",
        f"- 平均判定スコア: {metrics['avg_score']:.1f}/100",
        f"- 外部サイト優勢率: {metrics['external_lead_rate']:.1f}%",
        "",
        "## 今の見立て",
        f"- 総評: {portfolio_story['overall_label']}",
        f"- 状態要約: {portfolio_story['overall_summary']}",
        f"- 競合との位置: {portfolio_story['competition_summary']}",
        "",
        "## 今すぐ共有したい論点",
    ]
    if weakest_intent:
        lines.append(
            f"- 弱い意図: {weakest_intent['intent_label']}。"
            f" {weakest_intent['needs_fix_count']}/{weakest_intent['question_count']}件で外部優勢または未露出です。"
        )
    if top_gap:
        lines.append(f"- 不足している情報タイプ: {top_gap['page_type_label']}。{top_gap['next_step']}")
    if source_priority_actions:
        for action in source_priority_actions[:3]:
            lines.append(f"- 質問の系統: {action['summary']}")
    else:
        lines.append("- まだ優先アクションはありません。結果の蓄積後に表示します。")

    lines.extend(
        [
            "",
            "## 読み方の注意",
            "- 「引用された」は、回答の根拠として実際に使われたURLです。",
            "- 「検索ソースに出たが未引用」は、provider の web_search source に出たが回答根拠には使われなかったURLです。",
            "- 「判定保留」は、保存条件の違いなどで未引用と断定しない方が安全な状態です。",
        ]
    )
    return "\n".join(lines)
