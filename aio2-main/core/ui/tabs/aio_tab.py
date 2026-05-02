# -*- coding: utf-8 -*-
"""AIO tab rendering logic."""

from typing import Any, Dict, Callable

from nicegui import ui


def _as_point(value: Any) -> float:
    try:
        num = float(value)
    except Exception:
        return 0.0
    return num * 100.0 if 0.0 <= num <= 1.0 else num


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
    if isinstance(raw_score, (int, float)) and isinstance(penalty_multiplier, (int, float)):
        ui.label("AIOスコア計算式").classes("card-title")
        calculated = float(raw_score) * float(penalty_multiplier)
        ui.label(f"生スコア: {float(raw_score):.1f}点").classes("card-sub")
        ui.label(f"ペナルティ係数: ×{float(penalty_multiplier):.2f}").classes("card-sub")
        if isinstance(total_score, (int, float)):
            ui.label(f"最終スコア: {float(total_score):.1f}点").classes("card-sub")
        ui.label(f"式: {float(raw_score):.1f} × {float(penalty_multiplier):.2f} = {calculated:.1f}").classes("card-hint")

        # 重み付き貢献度テーブル
        _scores = aio_results.get("scores", {}) or {}
        _eeat_score = (_scores.get("eeat") or {}).get("score", 0.0)
        _tldr_score = (_scores.get("geo_tldr") or {}).get("score", 0.0)
        _stats_score = (_scores.get("geo_stats") or {}).get("score", 0.0)
        _pid_label = aio_score_labels.get("pid_density", "命題密度 (PID)")
        _structure_label = aio_score_labels.get("structure", "HTML構造")
        _entity_label = aio_score_labels.get("entity_salience", "エンティティ重要度")
        _tech_label = aio_score_labels.get("technical", "技術スコア")
        _eeat_label = aio_score_labels.get("eeat", "E-E-A-T（著者信頼性）")
        _tldr_label = aio_score_labels.get("geo_tldr", "TL;DR 冒頭要約")
        _stats_label = aio_score_labels.get("geo_stats", "統計・数値密度")
        _weight_rows = [
            (_pid_label,             _as_point(_scores.get("pid_score", 0)) / 100,      0.20),
            (_structure_label,       _as_point(_scores.get("structure_score", 0)) / 100, 0.15),
            (_entity_label,          _as_point(_scores.get("entity_score", 0)) / 100,   0.12),
            (_tech_label,            _as_point(_scores.get("tech_score", 0)) / 100,      0.10),
            (_eeat_label,            float(_eeat_score) / 10.0,                         0.08),
            ("引用準備度・鮮度・AEO・知識グラフ", None,                                   0.25),
            (_tldr_label,            float(_tldr_score) / 5.0,                           0.05),
            (_stats_label,           float(_stats_score) / 10.0,                         0.05),
        ]
        with ui.expansion("スコア構成（重み付け）", icon="bar_chart").classes("w-full mt-1"):
            for row_label, norm_val, weight in _weight_rows:
                if norm_val is not None:
                    contrib = norm_val * weight * 100
                    bar_color = "green" if norm_val >= 0.8 else ("amber" if norm_val >= 0.5 else "red")
                    with ui.row().classes("items-center gap-2 w-full"):
                        ui.label(row_label).classes("card-hint w-44 shrink-0")
                        ui.linear_progress(
                            value=norm_val, size="6px", show_value=False, color=bar_color,
                        ).classes("flex-1")
                        ui.label(f"{weight*100:.0f}%  →  {contrib:.1f}点").classes("card-hint w-24 text-right shrink-0")
                else:
                    ui.label(
                        f"{row_label}: 重み {weight*100:.0f}%（内訳は省略）"
                    ).classes("card-hint text-gray-400")

        penalties = aio_results.get("penalties", []) or []
        if penalties:
            ui.label("適用ペナルティ").classes("card-sub")
            for penalty in penalties[:4]:
                ui.label(f"- {trim_text(str(penalty), 220)}").classes("card-hint text-red-600")

    scores = aio_results.get("scores", {})

    if scores:
        ui.label("AIO主要スコア").classes("card-title")

        for key, data in list(scores.items())[:8]:
            label = data.get("label") or aio_score_labels.get(key, key)
            score = data.get("score", 0)
            ui.label(f"{label}: {score:.0f}点").classes("card-sub")

            helper = aio_score_help.get(key)
            if helper:
                ui.label(f"・{helper}").classes("card-hint")

    details = aio_results.get("details", {}) or {}
    citation = details.get("citation_readiness", {}) or {}
    entity = details.get("entity_linking", {}) or {}
    if citation or entity:
        ui.label("AIO算出根拠（詳細）").classes("card-title")

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
        ui.label("GEO（生成AI引用最適化）スコア").classes("card-title")

        # TL;DR
        tldr_score = geo_tldr.get("score", 0.0)
        ui.label(f"冒頭要約（TL;DR）: {tldr_score:.1f} / 5").classes("card-sub")
        if geo_tldr.get("has_explicit_tldr"):
            ui.label("✅ 明示的な要約ラベルあり").classes("card-hint")
        elif geo_tldr.get("has_early_bullets"):
            ui.label("✅ 冒頭箇条書きあり").classes("card-hint")
        else:
            ui.label("ℹ️ 冒頭要約なし").classes("card-hint text-orange-600")
        if geo_tldr.get("advice"):
            ui.label(f"  → {geo_tldr['advice']}").classes("card-hint")

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
        ui.label(f"E-E-A-T（文中検出）: {eeat_score:.1f} / 10").classes("card-sub")
        if signals.get("license"):
            ui.label("  ✅ 資格検出: " + "、".join(str(s) for s in signals["license"][:3])).classes("card-hint")
        else:
            ui.label("  ℹ️ 資格・専門性の記載なし").classes("card-hint")
        if signals.get("author_explicit"):
            ui.label("  ✅ 著者明示: " + "、".join(str(s) for s in signals["author_explicit"][:2])).classes("card-hint")
        else:
            ui.label("  ℹ️ 著者明示なし（例: 監修：山田太郎 税理士）").classes("card-hint")
        if not inline_eeat.get("has_json_ld_eeat"):
            ui.label("  ℹ️ JSON-LD Author未設定（schema.org/Person の実装を推奨）").classes("card-hint text-orange-600")

    # ===== P05: プラットフォーム別引用適合度セクション =====
    platform_citation = details.get("platform_citation", {}) or {}
    if platform_citation:
        ui.label("🤖 プラットフォーム別 引用適合度（推定）").classes("card-title")
        ui.label("※ 実際のAIシステムへのアクセスに基づくものではありません").classes("card-hint text-gray-400")

        _level_color = {"高": "text-green-600", "中": "text-yellow-600", "低": "text-red-500"}
        _platform_labels = {
            "google_aio": "Google AI Mode",
            "chatgpt":    "ChatGPT",
            "perplexity": "Perplexity",
        }

        _bar_color = {"高": "green", "中": "amber", "低": "red"}

        for key, label in _platform_labels.items():
            pdata = platform_citation.get(key, {})
            score = pdata.get("score", 0.0)
            level = pdata.get("level", "低")
            text_color = _level_color.get(level, "")
            bar_color = _bar_color.get(level, "red")
            with ui.row().classes("items-center gap-2 w-full"):
                ui.label(label).classes("card-sub w-36 shrink-0")
                ui.linear_progress(
                    value=score / 100, size="10px", show_value=False, color=bar_color,
                ).classes("flex-1").props(f'aria-label="{label}: {score:.0f}点 ({level})"')
                ui.label(f"{score:.0f}点 [{level}]").classes(f"card-sub {text_color} w-20 text-right shrink-0")
            for factor in (pdata.get("key_factors") or [])[:3]:
                ui.label(f"  ℹ️ {factor}").classes("card-hint text-orange-600")

        overall = platform_citation.get("overall", {})
        overall_score = overall.get("score", 0.0)
        overall_level = overall.get("level", "低")
        overall_bar_color = _bar_color.get(overall_level, "red")
        with ui.row().classes("items-center gap-2 w-full mt-1"):
            ui.label("総合").classes("card-sub font-bold w-36 shrink-0")
            ui.linear_progress(
                value=overall_score / 100, size="12px", show_value=False, color=overall_bar_color,
            ).classes("flex-1").props(f'aria-label="総合引用適合度: {overall_score:.0f}点 ({overall_level})"')
            ui.label(f"{overall_score:.0f}点 [{overall_level}]").classes("card-sub font-bold w-20 text-right shrink-0")
        ui.label("（Google40%・ChatGPT35%・Perplexity25%の加重平均）").classes("card-hint")

    aio_actions = aio_results.get("immediate_actions", [])

    if aio_actions:
        ui.label("即時改善アクション（1〜2週間）").classes("card-title")

        for action in aio_actions[:4]:
            ui.label(f"- {action.get('action', 'N/A')}").classes("card-sub")

            method = action.get("method", "")
            if method:
                ui.label(format_reason_text_ui(trim_text(method, 240))).classes("card-hint whitespace-pre-line")
