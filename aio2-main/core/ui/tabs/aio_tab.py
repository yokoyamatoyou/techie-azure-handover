# -*- coding: utf-8 -*-
"""AIO tab rendering logic."""

from typing import Any, Dict, Callable

from nicegui import ui


def _title_with_hint(title: str, hint: str, *, title_classes: str = "card-title") -> None:
    with ui.row().classes("items-center gap-2"):
        ui.label(title).classes(title_classes)
        ui.icon("info_outline").classes("text-sm text-[#9B7A60] opacity-70 cursor-help").tooltip(hint)


def _as_point(value: Any) -> float:
    try:
        num = float(value)
    except Exception:
        return 0.0
    return num * 100.0 if 0.0 <= num <= 1.0 else num


def _format_aio_phrase(value: str) -> str:
    text = str(value or "")
    replacements = [
        ("引用源(Source)", "引用元"),
        ("TL;DR", "冒頭要点まとめ"),
        ("E-E-A-T不足", "著者・運営者の信頼情報が不足"),
        ("E-E-A-T", "著者・運営者の信頼情報"),
        ("カスタム/その他", "その他 / 独自設定"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _normalize_metric(score: Any, *, max_score: float = 100.0) -> float:
    try:
        numeric = float(score)
    except Exception:
        return 0.0
    if max_score <= 0:
        return 0.0
    return max(0.0, min(1.0, numeric / max_score))


def _provider_status_style(status: str) -> tuple[str, str, str]:
    mapping = {
        "pass": ("通過", "text-green-600", "green"),
        "warn": ("注意", "text-amber-600", "amber"),
        "fail": ("要対応", "text-red-600", "red"),
    }
    return mapping.get(str(status or "").lower(), ("未判定", "text-gray-500", "grey"))


def render_aio_tab(
    aio_results: Dict[str, Any],
    aio_score_labels: Dict[str, str],
    aio_score_help: Dict[str, str],
    trim_text: Callable[[str, int], str],
    format_reason_text_ui: Callable[[str], str],
) -> None:
    """Render the AIO tab."""
    if not aio_results:
        ui.label("AIO分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
        return

    has_total_score = aio_results.get("total_score") is not None
    has_scores = bool(aio_results.get("scores"))
    has_errors = bool(aio_results.get("errors"))
    if not (has_total_score or has_scores or has_errors):
        ui.label("AIO分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
        return

    error_items = aio_results.get("errors", []) or []
    if error_items:
        ui.label("解析エラー/警告").classes("card-title text-red-600")
        for err in error_items[:6]:
            ui.label(f"- {trim_text(str(err), 220)}").classes("card-hint text-red-600")

    raw_score = aio_results.get("raw_score")
    penalty_multiplier = aio_results.get("penalty_multiplier")
    total_score = aio_results.get("total_score")
    penalties = aio_results.get("penalties", []) or []
    show_formula = (
        isinstance(raw_score, (int, float))
        and isinstance(penalty_multiplier, (int, float))
        and (abs(float(penalty_multiplier) - 1.0) > 1e-6 or bool(penalties))
    )
    if isinstance(raw_score, (int, float)) and isinstance(total_score, (int, float)):
        _title_with_hint("AIOスコア要約", "点数とは別に、公開されやすい状態も確認しています。")
        ui.label(f"最終スコア: {float(total_score):.1f}点").classes("card-sub")
    if show_formula:
        with ui.expansion("点数の内訳を見る", icon="unfold_more", value=False).classes("w-full mt-1"):
            calculated = float(raw_score) * float(penalty_multiplier)
            ui.label(f"調整前スコア: {float(raw_score):.1f}点").classes("card-sub")
            ui.label(f"調整係数: ×{float(penalty_multiplier):.2f}").classes("card-sub")
            ui.label(f"計算内容: {float(raw_score):.1f} × {float(penalty_multiplier):.2f} = {calculated:.1f}").classes("card-hint")

    if isinstance(raw_score, (int, float)) and isinstance(total_score, (int, float)):
        # 重み付き貢献度テーブル
        _scores = aio_results.get("scores", {}) or {}
        _weight_rows = [
            ("pid_density", 0.20, 100.0),
            ("structure", 0.15, 100.0),
            ("entity_salience", 0.12, 100.0),
            ("technical", 0.10, 100.0),
            ("eeat", 0.08, 10.0),
            ("citation", 0.10, 100.0),
            ("freshness", 0.06, 100.0),
            ("aeo", 0.05, 100.0),
            ("entity_linking", 0.04, 100.0),
            ("geo_tldr", 0.05, 5.0),
            ("geo_stats", 0.05, 10.0),
        ]
        with ui.expansion("スコア構成（重み付け）", icon="bar_chart").classes("w-full mt-1"):
            for metric_key, weight, max_score in _weight_rows:
                metric_payload = _scores.get(metric_key, {}) or {}
                row_label = metric_payload.get("label") or aio_score_labels.get(metric_key, metric_key)
                metric_score = metric_payload.get("score", 0.0)
                norm_val = _normalize_metric(metric_score, max_score=max_score)
                contrib = norm_val * weight * 100
                bar_color = "green" if norm_val >= 0.8 else ("amber" if norm_val >= 0.5 else "red")
                with ui.row().classes("items-center gap-2 w-full"):
                    ui.label(row_label).classes("card-hint w-44 shrink-0")
                    ui.linear_progress(
                        value=norm_val, size="6px", show_value=False, color=bar_color,
                    ).classes("flex-1")
                    ui.label(f"{weight*100:.0f}%  →  {contrib:.1f}点").classes("card-hint w-24 text-right shrink-0")
    if penalties:
        ui.label("適用ペナルティ").classes("card-sub")
        for penalty in penalties[:4]:
            ui.label(f"- {trim_text(str(penalty), 220)}").classes("card-hint text-red-600")

    scores = aio_results.get("scores", {})

    if scores:
        ui.label("AIO主要スコア").classes("card-title")
        ordered_metrics = [
            "pid_density",
            "structure",
            "entity_salience",
            "technical",
            "citation",
            "freshness",
            "aeo",
            "entity_linking",
            "eeat",
            "geo_tldr",
            "geo_stats",
        ]
        for key in ordered_metrics:
            data = scores.get(key, {}) or {}
            if not data:
                continue
            label = data.get("label") or aio_score_labels.get(key, key)
            score = data.get("score", 0)
            if key == "geo_tldr":
                ui.label(f"{label}: {float(score):.1f} / 5").classes("card-sub")
            elif key in {"eeat", "geo_stats"}:
                ui.label(f"{label}: {float(score):.1f} / 10").classes("card-sub")
            else:
                ui.label(f"{label}: {float(score):.0f}点").classes("card-sub")

            helper = aio_score_help.get(key)
            if helper:
                ui.label(f"・{helper}").classes("card-hint")

    details = aio_results.get("details", {}) or {}
    citation = details.get("citation_readiness", {}) or {}
    entity = details.get("entity_linking", {}) or {}
    if citation or entity:
        with ui.expansion("AIO算出根拠（詳細）", icon="unfold_more", value=False).classes("w-full mt-1"):
            if citation:
                ui.label("引用準備度（Citation Readiness）").classes("card-sub")
                citation_items = [
                    ("結論先出し", citation.get("conclusion_first")),
                    ("情報密度", citation.get("data_density")),
                    ("簡潔さ", citation.get("conciseness")),
                    ("出典明記", citation.get("source_attribution")),
                    ("事実比率", citation.get("fact_opinion_ratio")),
                    ("時系列明確さ", citation.get("temporal_clarity")),
                ]
                for label, value in citation_items:
                    if isinstance(value, (int, float)):
                        ui.label(f"- {label}: {_as_point(value):.0f}/100").classes("card-hint")
                if isinstance(citation.get("data_point_count"), int):
                    ui.label(
                        f"  数値根拠検出: {citation.get('data_point_count', 0)}件 / 出典語句: {citation.get('source_count', 0)}件"
                    ).classes("card-hint")

            if entity:
                ui.label("エンティティ連携（Entity Linking）").classes("card-sub")
                entity_items = [
                    ("連携スコア", entity.get("score")),
                    ("固有名詞数", entity.get("proper_noun_count")),
                    ("普通名詞数", entity.get("common_noun_count")),
                    ("ユニークエンティティ数", entity.get("unique_entity_count")),
                    ("総出現回数", entity.get("total_mentions")),
                ]
                for label, value in entity_items:
                    if isinstance(value, (int, float)):
                        if label == "連携スコア":
                            ui.label(f"- {label}: {_as_point(value):.0f}/100").classes("card-hint")
                        else:
                            ui.label(f"- {label}: {int(value)}").classes("card-hint")

                wikidata = entity.get("wikidata", {}) or {}
                linked_ratio = wikidata.get("linked_ratio")
                if isinstance(linked_ratio, (int, float)):
                    ui.label(f"- Wikidataリンク率: {_as_point(linked_ratio):.0f}/100").classes("card-hint")
                known_entities = entity.get("known_entities", []) or []
                if known_entities:
                    ui.label("  検出語例: " + "、".join([str(x) for x in known_entities[:5]])).classes("card-hint")

    # ===== P03: GEO基本指標セクション =====
    geo_tldr = details.get("geo_tldr", {}) or {}
    geo_stats = details.get("geo_stats", {}) or {}
    inline_eeat = details.get("inline_eeat", {}) or {}
    if geo_tldr or geo_stats or inline_eeat:
        ui.label("AI検索で見つけられやすい状態（GEO）スコア").classes("card-title")

        # TL;DR
        tldr_score = geo_tldr.get("score", 0.0)
        ui.label(f"冒頭の要点まとめ: {tldr_score:.1f} / 5").classes("card-sub")
        if geo_tldr.get("has_explicit_tldr"):
            ui.label("✅ 明示的な要約ラベルあり").classes("card-hint")
        elif geo_tldr.get("has_early_bullets"):
            ui.label("✅ 冒頭箇条書きあり").classes("card-hint")
        else:
            ui.label("ℹ️ 冒頭要約なし").classes("card-hint text-orange-600")
        if geo_tldr.get("advice"):
            ui.label(f"  → {_format_aio_phrase(str(geo_tldr['advice']))}").classes("card-hint")

        # 統計密度
        stats_score = geo_stats.get("score", 0.0)
        stats_count = geo_stats.get("stats_count", 0)
        density_per_1k = geo_stats.get("density_per_1k", 0.0)
        density_level = geo_stats.get("density_level", "low")
        level_label = {"high": "高", "medium": "中", "low": "低"}.get(density_level, density_level)
        ui.label(f"統計・数値密度: {stats_score:.1f} / 10").classes("card-sub")
        ui.label(f"  検出: {stats_count}件 / {density_per_1k:.1f}件/千字（{level_label}）").classes("card-hint")
        if geo_stats.get("has_citations"):
            ui.label("  ✅ 出典表記あり").classes("card-hint")
        else:
            ui.label("  ℹ️ 出典表記なし（「出典：〇〇」を追加すると効果的）").classes("card-hint")

        # インラインE-E-A-T
        eeat_score = inline_eeat.get("combined_score", 0.0)
        signals = inline_eeat.get("signals", {})
        ui.label(f"著者・運営者の信頼情報（文中確認）: {eeat_score:.1f} / 10").classes("card-sub")
        if signals.get("license"):
            ui.label("  ✅ 資格検出: " + "、".join(str(s) for s in signals["license"][:3])).classes("card-hint")
        else:
            ui.label("  ℹ️ 資格・専門性の記載なし").classes("card-hint")
        if signals.get("author_explicit"):
            ui.label("  ✅ 著者明示: " + "、".join(str(s) for s in signals["author_explicit"][:2])).classes("card-hint")
        else:
            ui.label("  ℹ️ 著者明示なし（例: 監修：山田太郎 税理士）").classes("card-hint")
        if not inline_eeat.get("has_json_ld_eeat"):
            ui.label("  ℹ️ JSON-LD の author/publisher は補助シグナルです。本文内の著者・組織情報が見えていれば直ちに必須不足とは扱いません。").classes("card-hint text-gray-600")

    # ===== Provider readiness section =====
    provider_readiness = aio_results.get("provider_readiness") or details.get("provider_readiness", {}) or {}
    provider_order = [
        ("google", "Google"),
        ("openai_search", "OpenAI Search"),
        ("perplexity", "Perplexity"),
        ("claude_search", "Claude Search"),
    ]
    if any(provider_readiness.get(key) for key, _ in provider_order):
        _title_with_hint("各AIサービスの公開条件チェック", "各サービスで公開されやすい状態かを見ています。細かい条件は展開して確認できます。")

        for key, label in provider_order:
            pdata = provider_readiness.get(key, {}) or {}
            if not pdata:
                continue
            if key == "perplexity" and pdata.get("status") == "pass":
                continue
            status_label, text_color, bar_color = _provider_status_style(pdata.get("status", ""))
            provider_exp = ui.expansion(f"{label}: {status_label}", icon="verified_user", value=pdata.get("status") != "pass").classes("w-full")
            with provider_exp:
                with ui.row().classes("items-center gap-3 w-full"):
                    ui.label(label).classes("card-sub font-bold")
                    ui.badge(status_label, color=bar_color).classes("text-xs")
                summary_text = pdata.get("summary")
                if summary_text:
                    ui.label(summary_text).classes(f"card-hint {text_color}")
                official_checks = pdata.get("official_checks", []) or []
                if official_checks:
                    ui.label("公式公開条件").classes("card-sub mt-2")
                    for check in official_checks[:6]:
                        check_status_label, check_color, _ = _provider_status_style(check.get("status", ""))
                        ui.label(f"・{check.get('label', '')}: {check_status_label}").classes(f"card-hint {check_color}")
                heuristic_notes = pdata.get("heuristic_notes", []) or []
                if heuristic_notes:
                    ui.label("内部ヒューリスティック").classes("card-sub mt-2")
                    for note in heuristic_notes[:4]:
                        ui.label(f"・{_format_aio_phrase(str(note))}").classes("card-hint text-amber-700")

        informational_notes = provider_readiness.get("informational_notes", []) or []
        if informational_notes:
            ui.label("任意メモ / 情報目的").classes("card-sub mt-2")
            for note in informational_notes[:8]:
                label = note.get("label", "補足")
                message = note.get("message", "")
                ui.label(f"・{label}: {message}").classes("card-hint text-gray-600")

    aio_actions = aio_results.get("immediate_actions", [])

    if aio_actions:
        ui.label("即時改善アクション（1〜2週間）").classes("card-title")

        for action in aio_actions[:4]:
            ui.label(format_reason_text_ui(f"- {action.get('action') or '確認項目がありません'}")).classes("card-sub whitespace-pre-line")

            method = action.get("method", "")
            if method:
                ui.label(format_reason_text_ui(trim_text(method, 240))).classes("card-hint whitespace-pre-line")
