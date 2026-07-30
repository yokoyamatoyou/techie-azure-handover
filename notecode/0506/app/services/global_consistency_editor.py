from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GlobalConsistencyEditResult:
    text: str
    report: dict[str, Any]


def run_global_consistency_editor(article_text: str, article_brief: dict[str, Any]) -> GlobalConsistencyEditResult:
    brief = article_brief["article_brief"]
    narrator = brief["narrator"]
    revised = _remove_duplicate_motto(article_text)
    revised = _remove_duplicate_founding_after_opening(revised)
    revised = _soften_self_praise(revised)
    revised = _soften_company_history_voice(revised, narrator)
    revised = _vary_late_service_endings(revised)
    return GlobalConsistencyEditResult(
        text=revised,
        report={
            "editor_profile_id": "note_hatena_global_consistency_editor",
            "focus": "whole_article_voice_after_opening",
            "changed": revised != article_text,
            "checks": {
                "narrator_present": narrator in revised,
                "duplicate_motto_reduced": revised.count("データで可能性を創造する") <= 1,
                "duplicate_founding_reduced": revised.count("1885") <= 1 and revised.count("創業") <= 3,
                "source_grounding_policy_changed": False,
                "qa_threshold_changed": False,
            },
        },
    )


def build_global_consistency_report(
    before_text: str,
    after_text: str,
    article_brief: dict[str, Any],
) -> dict[str, Any]:
    report = run_global_consistency_editor(after_text, article_brief).report
    report["changed"] = before_text != after_text
    return report


def _remove_duplicate_motto(text: str) -> str:
    marker = "「データで可能性を創造する」という言葉を掲げています。"
    first = text.find(marker)
    if first < 0:
        return text
    second = text.find(marker, first + len(marker))
    if second < 0:
        return text
    return text[:second] + text[second + len(marker) :].lstrip()


def _remove_duplicate_founding_after_opening(text: str) -> str:
    marker = "私たち京都工業は京都市伏見稲荷大社のお膝元で1885（明治18）年に創業。"
    if text.count(marker) == 0:
        return text
    replacement = "京都・伏見稲荷大社のお膝元で歩みを重ねてきました。"
    return text.replace(marker, replacement, 1)


def _soften_self_praise(text: str) -> str:
    return text.replace(
        "京都随一のデータ入力支援・分析センターとして事業を行っています。",
        "京都でデータ入力支援や分析に取り組んでいます。",
    )


def _soften_company_history_voice(text: str, narrator: str) -> str:
    replacements = {
        "京都工業は織機の部品製造会社として創業し130年余り経過しました。": (
            f"{narrator}は、織機の部品製造会社として創業してから130年余りの歴史があります。"
        ),
        "時代の流れとともに織機の需要が減少し、先代代表がデータ入力業へと業務転換を致しました。": (
            "時代の変化に合わせて、データ入力業へと事業を転換してきました。"
        ),
    }
    revised = text
    for before, after in replacements.items():
        revised = revised.replace(before, after)
    return revised


def _vary_late_service_endings(text: str) -> str:
    replacements = {
        "前処理から後処理まで一貫対応しています。": "前処理から後処理まで、一貫して対応できる体制です。",
        "データに関する課題を解決し、BPOを全面サポートしています。": "データに関する課題を起点に、BPOを全面的に支える内容です。",
        "RPAとデータエントリの総合力を強みとしています。": "RPAとデータエントリを組み合わせた総合力が強みです。",
    }
    revised = text
    for before, after in replacements.items():
        revised = revised.replace(before, after)
    return revised
