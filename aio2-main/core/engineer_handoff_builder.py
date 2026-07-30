from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\x00", "").strip()
    return " ".join(text.split())


def _as_list(value: Any, *, limit: int = 8) -> List[Any]:
    if isinstance(value, list):
        return value[:limit]
    if value:
        return [value]
    return []


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return ""


def _append_handoff_item(
    items: List[Dict[str, str]],
    *,
    category: Any,
    target: Any = "",
    work: Any = "",
    verify: Any = "",
    source: Any = "",
) -> None:
    work_text = _text(work)
    target_text = _text(target)
    if not work_text and not target_text:
        return
    item = {
        "category": _text(category) or "技術対応",
        "target": target_text or "-",
        "work": work_text or "-",
        "verify": _text(verify) or "実装後に該当URLを再分析して、同じ指摘が消えることを確認してください。",
        "source": _text(source) or "自動検出",
    }
    signature = (item["category"], item["target"], item["work"])
    for existing in items:
        if (existing.get("category"), existing.get("target"), existing.get("work")) == signature:
            return
    items.append(item)


def _dedup_join(parts: List[str]) -> str:
    values: List[str] = []
    for part in parts:
        text = _text(part)
        if text and text not in values:
            values.append(text)
    return " / ".join(values)


def _link_verify_text(link: Dict[str, Any], *, source_url: str = "", target_url: str = "") -> str:
    steps = []
    if target_url:
        steps.append(f"curl -I {target_url} で HTTP 200 と noindex なしを確認")
    if source_url and target_url:
        steps.append("リンク元ページ上で推奨アンカーが表示され、リンク先へ遷移できることを確認")
    check = _text(link.get("check"))
    steps.append(check)
    if "再分析後" not in check:
        steps.append("再分析後に孤立ページ・内部リンク不足の指摘が減ることを確認")
    return _dedup_join(steps)


def _schema_verify_text(suggestion: Dict[str, Any], schema: Dict[str, Any], *, field_text: str = "") -> str:
    schema_type = _text(suggestion.get("schema_type") or "Schema")
    steps = [
        _text(suggestion.get("validation_method") or schema.get("validation_method")),
        f"Rich Results Test または Schema Validator で {schema_type} が検出されることを確認",
    ]
    if field_text:
        steps.append(f"必須/優先フィールド（{field_text}）にエラーが残らないことを確認")
    return _dedup_join(steps)


_HANDOFF_CATEGORY_PRIORITY = {
    "アクセシビリティ": 0,
    "公開技術リスク": 1,
    "セキュリティ": 2,
    "旧公開ページ": 3,
    "リンク健全性": 4,
    "内部リンク": 5,
    "構造化データ": 6,
    "llms.txt": 7,
}


def _handoff_sort_key(row: tuple[int, Dict[str, str]]) -> tuple[int, int]:
    index, item = row
    category = _text(item.get("category"))
    priority = 9
    for prefix, rank in _HANDOFF_CATEGORY_PRIORITY.items():
        if category.startswith(prefix):
            priority = rank
            break
    return (priority, index)


def build_engineer_handoff_items(snapshot: Dict[str, Any], *, limit: int = 16) -> List[Dict[str, str]]:
    """Build concrete engineer handoff rows from a saved UI snapshot."""
    implementation = _as_dict(snapshot.get("implementation_workspace"))
    technical = _as_dict(snapshot.get("technical_workspace"))
    items: List[Dict[str, str]] = []

    legacy = _as_dict(_first_present(technical.get("legacy_pages"), implementation.get("legacy_page_summary")))
    if int(legacy.get("found_count") or 0) > 0:
        urls = [
            _text(page.get("final_url") or page.get("url"))
            for page in _as_list(legacy.get("pages"), limit=3)
            if isinstance(page, dict) and _text(page.get("final_url") or page.get("url"))
        ]
        target = " / ".join(urls) or _text(legacy.get("technical_detail"))
        verify_steps = [
            _text(step.get("detail") or step.get("title"))
            for step in _as_list(legacy.get("verification_steps"), limit=2)
            if isinstance(step, dict)
        ]
        for task in _as_list(legacy.get("engineer_tasks"), limit=3):
            if isinstance(task, dict):
                _append_handoff_item(
                    items,
                    category="旧公開ページ",
                    target=target,
                    work=_first_present(task.get("detail"), task.get("title")),
                    verify=" / ".join([step for step in verify_steps if step]),
                    source=legacy.get("title") or "legacy_page_report",
                )

    link_health = _as_dict(_first_present(technical.get("link_health"), implementation.get("link_health_summary")))
    for link in _as_list(link_health.get("link_opportunities"), limit=4):
        if not isinstance(link, dict):
            continue
        source_url = _text(link.get("source_url"))
        target_url = _text(link.get("target_url"))
        anchor = _text(link.get("recommended_anchor"))
        placement = _text(link.get("placement"))
        work_bits = [
            f"{source_url} から {target_url} へ内部リンクを追加" if source_url and target_url else "",
            f"アンカー: {anchor}" if anchor else "",
            f"配置: {placement}" if placement else "",
            _text(link.get("reason")),
        ]
        _append_handoff_item(
            items,
            category="内部リンク",
            target=target_url or source_url,
            work=" / ".join(bit for bit in work_bits if bit),
            verify=_link_verify_text(link, source_url=source_url, target_url=target_url),
            source="link_health_summary",
        )
    for step in _as_list(link_health.get("engineering_steps"), limit=4):
        if isinstance(step, dict):
            _append_handoff_item(
                items,
                category="リンク健全性",
                target=step.get("fix_location") or step.get("observed"),
                work=step.get("observed"),
                verify=_first_present(step.get("command"), step.get("pass_condition")),
                source="link_health_summary",
            )

    schema = _as_dict(_first_present(technical.get("schema"), implementation.get("schema_summary")))
    for suggestion in _as_list(schema.get("suggestions"), limit=3):
        if not isinstance(suggestion, dict):
            continue
        fields = suggestion.get("required_fields") or []
        field_text = ", ".join(str(field) for field in fields[:8]) if isinstance(fields, list) else ""
        work_bits = [
            _text(suggestion.get("summary")),
            f"必須/優先フィールド: {field_text}" if field_text else "",
            _text(suggestion.get("fix_location")),
        ]
        template = _text(suggestion.get("template"))
        if template:
            work_bits.append(f"実装例: {template[:240]}")
        _append_handoff_item(
            items,
            category=f"構造化データ: {_text(suggestion.get('schema_type') or 'Schema')}",
            target=suggestion.get("fix_location") or "head内 JSON-LD",
            work=" / ".join(bit for bit in work_bits if bit),
            verify=_schema_verify_text(suggestion, schema, field_text=field_text),
            source="schema_summary",
        )
    if schema and not schema.get("suggestions"):
        _append_handoff_item(
            items,
            category="構造化データ",
            target=schema.get("fix_location") or "head内 JSON-LD",
            work=schema.get("detail"),
            verify=_first_present(schema.get("command"), schema.get("pass_condition"), schema.get("validation_method")),
            source="schema_summary",
        )

    llms = _as_dict(_first_present(technical.get("llms"), implementation.get("llms_summary")))
    if llms:
        _append_handoff_item(
            items,
            category="llms.txt",
            target=llms.get("fix_location") or "/llms.txt",
            work=_first_present(llms.get("setup_judgment"), llms.get("detail"), "必要に応じて /llms.txt を設置または内容更新してください。"),
            verify=_first_present(llms.get("command"), llms.get("pass_condition")),
            source="llms_summary",
        )

    site_health_checks = _as_list(
        _first_present(technical.get("site_health_checks"), implementation.get("site_health_checks")),
        limit=8,
    )
    for check in site_health_checks:
        if not isinstance(check, dict) or _text(check.get("key")) != "security":
            continue
        for task in _as_list(check.get("engineer_tasks"), limit=8):
            if not isinstance(task, dict):
                continue
            severity = _text(task.get("severity"))
            category = "公開技術リスク" if severity in {"high", "medium"} else "セキュリティ確認"
            command_text = " / ".join(_text(command) for command in _as_list(task.get("commands"), limit=3) if _text(command))
            verify_text = _dedup_join([
                _text(task.get("verify")),
                f"確認コマンド: {command_text}" if command_text else "",
                f"合格条件: {_text(task.get('pass_condition'))}" if _text(task.get("pass_condition")) else "",
            ])
            _append_handoff_item(
                items,
                category=category,
                target=_first_present(task.get("target"), task.get("title")),
                work=_first_present(task.get("work"), task.get("title")),
                verify=verify_text,
                source=_first_present(task.get("source"), check.get("title"), "site_health.security"),
            )

    accessibility = _as_dict(
        _first_present(technical.get("accessibility_improvements"), implementation.get("accessibility_improvements"))
    )
    for action in _as_list(accessibility.get("actions"), limit=8):
        if not isinstance(action, dict):
            continue
        engineer = _as_dict(action.get("engineer"))
        _append_handoff_item(
            items,
            category="アクセシビリティ",
            target=_first_present(engineer.get("target_element"), action.get("target_element"), action.get("target")),
            work=_first_present(engineer.get("task"), action.get("action")),
            verify=engineer.get("verification") or action.get("verification"),
            source=_first_present(engineer.get("detection_source"), action.get("group"), "accessibility"),
        )

    for action in _as_list(_first_present(technical.get("actions"), implementation.get("technical_actions")), limit=4):
        if isinstance(action, dict):
            category = _first_present(action.get("category"), action.get("area"), "技術アクション")
            if _text(category) == "アクセシビリティ" and not _text(action.get("target_element")):
                continue
            _append_handoff_item(
                items,
                category=category,
                target=action.get("target_element") or action.get("area"),
                work=action.get("action") or action.get("title"),
                verify=action.get("detail") or action.get("kpi"),
                source="priority_actions",
            )

    ranked = [item for _, item in sorted(enumerate(items), key=_handoff_sort_key)]
    return ranked[: max(1, int(limit or 16))]
