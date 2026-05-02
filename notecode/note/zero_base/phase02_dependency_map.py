"""Phase02 dependency map and cutline definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DependencyEntry:
    module: str
    depended_by: tuple[str, ...]
    role_in_zero_base: str
    decision: str  # keep | drop | observe_only


DEPENDENCY_ENTRIES: tuple[DependencyEntry, ...] = (
    DependencyEntry(
        module="note.article_generator",
        depended_by=("note.note_writer_app",),
        role_in_zero_base="本流オーケストレーション（phase03以降でzero_base分岐を追加）",
        decision="keep",
    ),
    DependencyEntry(
        module="note.interview_mixin",
        depended_by=("note.article_generator",),
        role_in_zero_base="生成前AI質問の取得と回答反映（must_cover/unresolved_items）",
        decision="keep",
    ),
    DependencyEntry(
        module="note.policy_engine",
        depended_by=("note.article_generator", "note.interview_mixin"),
        role_in_zero_base="UIカテゴリ解決（article_type/category_base_template整合）",
        decision="keep",
    ),
    DependencyEntry(
        module="note/custom_genres.json",
        depended_by=("note.genre_manager", "note.policy_engine"),
        role_in_zero_base="カスタムカテゴリ方針データ",
        decision="keep",
    ),
    DependencyEntry(
        module="note.llm_client",
        depended_by=("note.article_generator",),
        role_in_zero_base="LLM I/Oと再試行/fallback制御",
        decision="keep",
    ),
    DependencyEntry(
        module="core.app_config",
        depended_by=("note.article_generator", "note.llm_client"),
        role_in_zero_base="generation_mode と各種しきい値設定",
        decision="keep",
    ),
    DependencyEntry(
        module="note.prompt_sanitizer",
        depended_by=("note.article_generator",),
        role_in_zero_base="入力無害化（注入対策）",
        decision="keep",
    ),
    DependencyEntry(
        module="human_resonance.pipeline",
        depended_by=("note.article_generator",),
        role_in_zero_base="新本流では除外対象（legacy互換のみ）",
        decision="drop",
    ),
    DependencyEntry(
        module="human_resonance.phase0_persona",
        depended_by=("note.article_generator",),
        role_in_zero_base="新本流では除外対象（legacy互換のみ）",
        decision="drop",
    ),
    DependencyEntry(
        module="human_resonance2.quality_pipeline",
        depended_by=("note.article_generator",),
        role_in_zero_base="監視専用（本文改変の実行経路から除外）",
        decision="observe_only",
    ),
    DependencyEntry(
        module="human_resonance2.fingerprint_metrics",
        depended_by=("note.article_generator",),
        role_in_zero_base="監視専用指標（本文改変なし）",
        decision="observe_only",
    ),
)

EMBEDDING_PLAN: dict[str, Any] = {
    "model": "text-embedding-3-small",
    "call_point": "phase05 semantic_dedupe（section generate 後、minimal postprocess 前）",
    "timeout_seconds": 20,
    "retry_policy": "1 retry with exponential backoff (0.8s -> 1.6s)",
    "failure_fallback": "fail-open: dedupeをスキップし、audit logにsemantic_dedupe_fail_openを記録",
}


def build_dependency_index() -> list[dict[str, Any]]:
    return [asdict(entry) for entry in DEPENDENCY_ENTRIES]


def _build_dependency_graph(entries: list[dict[str, Any]]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    modules = {str(entry["module"]) for entry in entries}
    for module in modules:
        graph[module] = set()
    for entry in entries:
        module = str(entry["module"])
        depended_by = entry.get("depended_by", ())
        if not isinstance(depended_by, (list, tuple)):
            continue
        for parent in depended_by:
            parent_name = str(parent)
            if parent_name not in graph:
                graph[parent_name] = set()
            graph[parent_name].add(module)
    return graph


def detect_cycles(entries: list[dict[str, Any]]) -> list[list[str]]:
    graph = _build_dependency_graph(entries)
    cycles: list[list[str]] = []
    temp_mark: set[str] = set()
    perm_mark: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in perm_mark:
            return
        if node in temp_mark:
            if node in stack:
                start = stack.index(node)
                cycles.append(stack[start:] + [node])
            return
        temp_mark.add(node)
        stack.append(node)
        for neighbor in sorted(graph.get(node, set())):
            visit(neighbor)
        stack.pop()
        temp_mark.remove(node)
        perm_mark.add(node)

    for node in sorted(graph.keys()):
        visit(node)
    return cycles


def render_dependency_map_markdown(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Dependency Map (Phase02)",
        "",
        "## Module Relation (Text Diagram)",
        "",
        "note.note_writer_app -> note.article_generator",
        "note.article_generator -> note.interview_mixin -> note.policy_engine -> note/custom_genres.json",
        "note.article_generator -> note.llm_client",
        "note.article_generator -> core.app_config",
        "note.article_generator -> note.prompt_sanitizer",
        "note.article_generator -X-> human_resonance.pipeline (drop target)",
        "note.article_generator -O-> human_resonance2.quality_pipeline (observe_only)",
        "note.article_generator -O-> human_resonance2.fingerprint_metrics (observe_only)",
        "",
        "## Keep / Drop / Observe-only",
        "",
        "| module | depended_by | role_in_zero_base | keep/drop/observe_only |",
        "|---|---|---|---|",
    ]
    for entry in entries:
        depended_by = entry.get("depended_by", ())
        if isinstance(depended_by, (list, tuple)):
            depended_by_text = ", ".join(str(item) for item in depended_by) or "-"
        else:
            depended_by_text = "-"
        lines.append(
            "| "
            + f"{entry['module']} | {depended_by_text} | {entry['role_in_zero_base']} | {entry['decision']} |"
        )

    lines.extend(
        [
            "",
            "## Embeddings Plan (`text-embedding-3-small`)",
            "",
            f"- 呼び出しポイント: {EMBEDDING_PLAN['call_point']}",
            f"- タイムアウト: {EMBEDDING_PLAN['timeout_seconds']}秒",
            f"- リトライ: {EMBEDDING_PLAN['retry_policy']}",
            f"- 失敗時フォールバック: {EMBEDDING_PLAN['failure_fallback']}",
            "",
            "## Decision Notes",
            "- `interview_mixin.py` / `policy_engine.py` / `custom_genres.json` は keep。",
            "- `human_resonance*` は新本流から drop 方針。",
            "- `human_resonance2*` は observe-only（監視専用）方針。",
            "",
        ]
    )
    return "\n".join(lines)


def write_phase02_dependency_map(output_dir: Path) -> Path:
    entries = build_dependency_index()
    content = render_dependency_map_markdown(entries)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "dependency_map_2026-03-04.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path
