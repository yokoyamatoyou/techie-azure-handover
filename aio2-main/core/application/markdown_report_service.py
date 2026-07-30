from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.application.time_display import (
    current_jst_datetime_text,
    current_jst_filename_timestamp,
    format_jst_datetime,
)
from core.config import config
from core.engineer_handoff_builder import build_engineer_handoff_items
from core.site_health.maintenance_risk import build_maintenance_risk_summary

EXPORTS_DIR = config.POC_OUTPUT_DIR / "exports"


def _text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\x00", "").strip()
    return " ".join(text.split())


def _md(value: Any) -> str:
    text = _text(value)
    return text.replace("<", "&lt;").replace(">", "&gt;")


def _table_cell(value: Any) -> str:
    return _md(value).replace("|", "\\|")


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


_SEO_SCORE_LABELS = {
    "title_score": "タイトル",
    "meta_description_score": "メタディスクリプション",
    "headings_score": "見出し構造",
    "content_score": "本文量・構成",
    "links_score": "内部/外部リンク",
    "images_score": "画像情報",
    "technical_score": "技術基盤",
}

_AIO_DETAIL_LABELS = {
    "pid": "主題の明確さ",
    "entity_coverage": "固有名詞・サービス情報",
    "citation_readiness": "引用しやすさ",
    "answerability": "回答への使いやすさ",
    "llms_txt": "llms.txt整備",
}


def _numeric_text(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if 0 <= number <= 1:
        return f"{round(number * 100)} / 100 相当"
    if 1 < number <= 10:
        return f"{round(number * 10)} / 100 相当"
    if 10 < number <= 100:
        return f"{round(number)} / 100"
    return f"{number:g}"


def _driver_label(prefix: str, key: Any) -> str:
    raw_key = _text(key)
    if prefix == "SEO":
        return _SEO_SCORE_LABELS.get(raw_key, raw_key.replace("_", " "))
    return _AIO_DETAIL_LABELS.get(raw_key, raw_key.replace("_", " "))


def _driver_value(value: Any) -> str:
    numeric = _numeric_text(value)
    return numeric or _md(value)


def _append_bullets(lines: List[str], items: Iterable[Any], *, key: Optional[str] = None, limit: int = 8) -> None:
    count = 0
    for item in items:
        if count >= limit:
            break
        value = item.get(key) if key and isinstance(item, dict) else item
        text = _md(value)
        if not text:
            continue
        lines.append(f"- {text}")
        count += 1


def _append_action(lines: List[str], action: Dict[str, Any], index: int) -> None:
    title = _md(action.get("title") or action.get("label") or f"アクション {index}")
    lines.append(f"### {index}. {title}")
    for label, key in (
        ("アクションID", "action_id"),
        ("優先順位", "priority_rank"),
        ("状態", "status_label"),
        ("領域", "area"),
        ("担当", "role"),
        ("実施内容", "action"),
        ("詳細", "detail"),
        ("期待KPI", "kpi"),
        ("工数", "effort"),
        ("効果", "impact"),
    ):
        value = _md(action.get(key))
        if value:
            lines.append(f"- {label}: {value}")
    audience = action.get("audience") if isinstance(action.get("audience"), dict) else {}
    evidence = action.get("evidence") if isinstance(action.get("evidence"), dict) else {}
    audience_text = _md(audience.get("label") or audience.get("role"))
    evidence_text = _md(evidence.get("detail") or evidence.get("source"))
    if audience_text:
        lines.append(f"- 対象読者: {audience_text}")
    if evidence_text:
        lines.append(f"- 根拠: {evidence_text}")
    lines.append("")


def _append_engineer_handoff_section(lines: List[str], snapshot: Dict[str, Any]) -> None:
    items = build_engineer_handoff_items(snapshot)
    if not items:
        lines.append("### エンジニア作業票")
        lines.append("- 対象要素・修正作業・確認方法まで揃った技術タスクは保存済みデータにありません。")
        lines.append("")
        return

    lines.append("### エンジニア作業票")
    lines.append("| No | 分類 | 対象 | 作業 | 確認方法 | 検出元 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for index, item in enumerate(items, 1):
        lines.append(
            "| "
            + " | ".join(
                [
                    _table_cell(index),
                    _table_cell(item.get("category")),
                    _table_cell(item.get("target")),
                    _table_cell(item.get("work")),
                    _table_cell(item.get("verify")),
                    _table_cell(item.get("source")),
                ]
            )
            + " |"
        )
    lines.append("")


def _find_intent_role_map(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    for workspace_key in ("summary_workspace", "implementation_workspace", "technical_workspace"):
        workspace = _as_dict(snapshot.get(workspace_key))
        role_map = _as_dict(workspace.get("intent_role_map"))
        if role_map:
            return role_map
    return {}


def _score_rows(snapshot: Dict[str, Any], run_row: Dict[str, Any], result: Dict[str, Any]) -> List[tuple[str, Any]]:
    header = _as_dict(snapshot.get("header"))
    integrated = _as_dict(result.get("integrated_results"))
    return [
        ("総合スコア", _first_present(header.get("integrated_score"), integrated.get("integrated_score"))),
        ("SEO", _first_present(header.get("seo_score"), integrated.get("seo_score"), run_row.get("seo_score"))),
        ("AI認識", _first_present(header.get("aio_score"), integrated.get("aio_score"), run_row.get("aio_score"))),
        ("法務・表示", _first_present(header.get("legal_score"), integrated.get("legal_score"), run_row.get("legal_score"))),
        ("総合優先度", header.get("priority_level")),
        ("検出課題数", _first_present(header.get("issue_count"), run_row.get("total_issues"))),
    ]


def _append_score_drivers(lines: List[str], snapshot: Dict[str, Any], result: Dict[str, Any]) -> None:
    summary_workspace = _as_dict(snapshot.get("summary_workspace"))
    lines.append("## 3. スコア低下の主因")
    added = False
    for item in _as_list(summary_workspace.get("blocking_issues"), limit=8):
        if not isinstance(item, dict):
            continue
        title = _md(item.get("title"))
        detail = _md(item.get("detail"))
        if title or detail:
            lines.append(f"- {title}: {detail}".rstrip(": "))
            added = True

    seo_results = _as_dict(result.get("seo_results"))
    seo_scores = _as_dict(seo_results.get("scores") or seo_results.get("score_breakdown"))
    for key, value in list(seo_scores.items())[:8]:
        if value not in (None, ""):
            lines.append(f"- SEO {_md(_driver_label('SEO', key))}: {_driver_value(value)}")
            added = True

    aio_results = _as_dict(result.get("aio_results"))
    aio_details = _as_dict(aio_results.get("details"))
    for key, value in list(aio_details.items())[:8]:
        if isinstance(value, (str, int, float)) and _md(value):
            lines.append(f"- AIO {_md(_driver_label('AIO', key))}: {_driver_value(value)}")
            added = True

    if not added:
        lines.append("- 保存済みsnapshot内に追加の減点内訳はありません。画面の各タブで詳細を確認してください。")
    lines.append("")


def _append_intent_section(lines: List[str], snapshot: Dict[str, Any]) -> None:
    role_map = _find_intent_role_map(snapshot)
    lines.append("## 4. 検索意図と不足コンテンツ")
    if not role_map:
        lines.append("- 検索意図・ページ役割マップは保存データにありません。")
        lines.append("")
        return

    fields = [
        ("現行アルゴリズムのページ役割判定", role_map.get("page_role")),
        ("想定ユーザー意図", role_map.get("user_intent")),
        ("次にやること", role_map.get("recommended_action")),
    ]
    for label, value in fields:
        text = _md(value)
        if text:
            lines.append(f"- {label}: {text}")

    missing = role_map.get("missing_content")
    if missing:
        lines.append("- 不足判定:")
        _append_bullets(lines, _as_list(missing, limit=8))

    engineer_notes = _as_dict(role_map.get("engineer_notes"))
    if engineer_notes:
        lines.append("- 推奨配置・実装メモ:")
        for label, key in (
            ("実装場所", "fix_locations"),
            ("追加見出し", "add_headings"),
            ("FAQ", "add_faq"),
            ("構造化データ", "structured_data"),
            ("内部リンク", "internal_links"),
        ):
            value = engineer_notes.get(key)
            if isinstance(value, list):
                text = " / ".join(_md(item) for item in value if _md(item))
            else:
                text = _md(value)
            if text:
                lines.append(f"  - {label}: {text}")
    lines.append("")


def _append_writing_section(lines: List[str], snapshot: Dict[str, Any]) -> None:
    writing = _as_dict(snapshot.get("writing_workspace"))
    lines.append("## 5. 文章・FAQ・引用候補")

    title_rewrites = _as_list(writing.get("title_rewrites"), limit=3)
    description_rewrites = _as_list(writing.get("description_rewrites"), limit=3)
    faq_suggestions = _as_list(writing.get("faq_suggestions"), limit=5)
    citation_phrases = _as_list(writing.get("citation_phrases"), limit=5)

    if title_rewrites:
        lines.append("### タイトル案")
        for item in title_rewrites:
            if isinstance(item, dict):
                lines.append(f"- 現状: {_md(item.get('current'))}")
                lines.append(f"  - 提案: {_md(item.get('proposed'))}")

    if description_rewrites:
        lines.append("### ディスクリプション案")
        for item in description_rewrites:
            if isinstance(item, dict):
                lines.append(f"- 提案: {_md(item.get('proposed'))}")

    if faq_suggestions:
        lines.append("### FAQ候補")
        for item in faq_suggestions:
            if not isinstance(item, dict):
                continue
            question = _md(item.get("question") or item.get("title"))
            outline = _md(item.get("answer_outline") or item.get("answer"))
            section = _md(item.get("recommended_section"))
            schema = _md(item.get("schema_candidate"))
            lines.append(f"- {question}")
            if outline:
                lines.append(f"  - 回答骨子: {outline}")
            if section:
                lines.append(f"  - 推奨配置: {section}")
            if schema:
                lines.append(f"  - schema候補: {schema}")

    if citation_phrases:
        lines.append("### 引用候補")
        for item in citation_phrases:
            if isinstance(item, dict):
                phrase = _md(item.get("phrase") or item.get("title"))
                template = _md(item.get("template_non_engineer") or item.get("template"))
                if phrase or template:
                    lines.append(f"- {phrase}: {template}".rstrip(": "))

    if not (title_rewrites or description_rewrites or faq_suggestions or citation_phrases):
        lines.append("- 文章改善・FAQ・引用候補は保存データにありません。")
    lines.append("")


def _append_technical_section(lines: List[str], snapshot: Dict[str, Any], result: Dict[str, Any]) -> None:
    implementation = _as_dict(snapshot.get("implementation_workspace"))
    technical = _as_dict(snapshot.get("technical_workspace"))
    lines.append("## 7. エンジニア向け実装メモ")

    _append_engineer_handoff_section(lines, snapshot)

    for title, payload in (
        ("古い公開ページ", _first_present(technical.get("legacy_pages"), implementation.get("legacy_page_summary"))),
        ("クロール範囲", _first_present(technical.get("crawl_scope"), implementation.get("crawl_scope_summary"))),
        ("内部リンク健全性", _first_present(technical.get("link_health"), implementation.get("link_health_summary"))),
        ("構造化データ", _first_present(technical.get("schema"), implementation.get("schema_summary"))),
        ("llms.txt", _first_present(technical.get("llms"), implementation.get("llms_summary"))),
    ):
        data = _as_dict(payload)
        if not data:
            continue
        lines.append(f"### {title}")
        for label, key in (
            ("状態", "status_label"),
            ("概要", "detail"),
            ("確認コマンド", "command"),
            ("合格条件", "pass_condition"),
            ("検証方法", "validation_method"),
            ("技術詳細", "technical_detail"),
        ):
            value = _md(data.get(key))
            if value:
                lines.append(f"- {label}: {value}")

        pages = _as_list(data.get("pages"), limit=5)
        if pages:
            lines.append("- 対象URL:")
            for page in pages:
                if isinstance(page, dict):
                    lines.append(f"  - {_md(page.get('final_url') or page.get('url'))}")

        opportunities = _as_list(data.get("link_opportunities"), limit=5)
        if opportunities:
            lines.append("- 内部リンク追加候補:")
            for item in opportunities:
                if isinstance(item, dict):
                    lines.append(
                        "  - "
                        f"{_md(item.get('source_url'))} -> {_md(item.get('target_url'))}"
                        f" / anchor: {_md(item.get('recommended_anchor'))}"
                    )

        tasks = _as_list(data.get("engineer_tasks"), limit=6)
        if tasks:
            lines.append("- 対応タスク:")
            for item in tasks:
                if isinstance(item, dict):
                    lines.append(f"  - {_md(item.get('title'))}: {_md(item.get('detail'))}".rstrip(": "))

        checks = _as_list(data.get("verification_steps"), limit=6)
        if checks:
            lines.append("- 完了確認:")
            for item in checks:
                if isinstance(item, dict):
                    lines.append(f"  - {_md(item.get('title'))}: {_md(item.get('detail'))}".rstrip(": "))
        lines.append("")

    site_health = _as_list(_first_present(technical.get("site_health_checks"), implementation.get("site_health_checks")), limit=8)
    if site_health:
        lines.append("### サイトヘルス")
        for item in site_health:
            if isinstance(item, dict):
                title = _md(item.get("title"))
                detail = _md(item.get("detail"))
                if item.get("key") == "accessibility":
                    accessibility = _as_dict(_as_dict(result.get("site_health")).get("accessibility"))
                    formatted = _as_dict(accessibility.get("formatted"))
                    source = _md(_first_present(accessibility.get("source"), formatted.get("detection_source")))
                    source_label = "実ブラウザ自動検出" if source == "browser" else ("HTML自動検出" if source else "")
                    if source_label and source_label not in detail:
                        detail = " / ".join(bit for bit in (detail, source_label) if bit)
                lines.append(f"- {title}: {detail}".rstrip(": "))
                issues = _as_list(item.get("issues"), limit=6)
                for issue in issues:
                    issue_text = _md(issue)
                    if issue_text:
                        lines.append(f"  - 要確認: {issue_text}")
                for task in _as_list(item.get("engineer_tasks"), limit=4):
                    if not isinstance(task, dict):
                        continue
                    task_title = _md(task.get("title") or "技術対応")
                    work = _md(task.get("work"))
                    verify = _md(task.get("verify"))
                    if task_title or work:
                        lines.append(f"  - エンジニア対応: {task_title}" + (f" / {work}" if work else ""))
                    commands = [_md(command) for command in _as_list(task.get("commands"), limit=3) if _md(command)]
                    for command in commands:
                        lines.append(f"    - 確認コマンド: {command}")
                    if verify:
                        lines.append(f"    - 確認方法: {verify}")
                    pass_condition = _md(task.get("pass_condition"))
                    if pass_condition:
                        lines.append(f"    - 合格条件: {pass_condition}")
        lines.append("")

    accessibility_improvements = _as_dict(
        _first_present(technical.get("accessibility_improvements"), implementation.get("accessibility_improvements"))
    )
    accessibility_actions = _as_list(accessibility_improvements.get("actions"), limit=8)
    confirmation_items = _as_list(accessibility_improvements.get("confirmation_items"), limit=3)
    if accessibility_actions:
        lines.append("### アクセシビリティ技術詳細")
        for index, action in enumerate(accessibility_actions, 1):
            if not isinstance(action, dict):
                continue
            engineer = _as_dict(action.get("engineer"))
            title = _md(action.get("title") or f"見やすさ・使いやすさ改善 {index}")
            lines.append(f"#### {index}. {title}")
            for label, key in (
                ("対象要素", "target_element"),
                ("行うべき作業", "task"),
                ("確認方法", "verification"),
                ("検出元", "detection_source"),
            ):
                value = _md(_first_present(engineer.get(key), action.get(key)))
                if value:
                    lines.append(f"- {label}: {value}")
            raw_issue = _md(engineer.get("raw_issue"))
            if raw_issue:
                lines.append(f"- 検出内容: {raw_issue}")
            if action.get("affected_count") not in (None, ""):
                lines.append(f"- 検出件数: {_md(action.get('affected_count'))}")
            lines.append("")
    elif confirmation_items:
        lines.append("### アクセシビリティ確認項目")
        for item in confirmation_items:
            if not isinstance(item, dict):
                continue
            title = _md(item.get("title") or "確認項目")
            detail = _md(item.get("detail"))
            source = _md(item.get("detection_source"))
            lines.append(f"- {title}: {detail}".rstrip(": "))
            if source:
                lines.append(f"  - 検出元: {source}")
        lines.append("")

    legal_checks = _as_dict(result.get("legal_checks"))
    premiums_raw = _as_dict(_as_dict(legal_checks.get("premiums_labeling")).get("raw"))
    review_items = [
        item for item in _as_list(premiums_raw.get("issues"), limit=20)
        if isinstance(item, dict) and item.get("legal_decision") == "review_needed"
    ]
    if review_items:
        lines.append("### 法務文脈判定（実装担当向け）")
        lines.append("- 主画面の減点・優先アクションには含めていない、前後文確認が必要な候補です。")
        for item in review_items[:8]:
            context = _as_dict(item.get("context_judgement"))
            lines.append(f"- 表現: {_md(item.get('matched_text'))}")
            lines.append(f"  - 周辺文脈: {_md(item.get('evidence'))}")
            lines.append(f"  - 判定理由: {_md(item.get('context_note') or context.get('reason'))}")
            if context.get("model"):
                lines.append(f"  - 判定モデル: {_md(context.get('model'))} / reasoning: {_md(context.get('reasoning_effort'))}")
        lines.append("")


def _append_maintenance_section(lines: List[str], snapshot: Dict[str, Any], result: Dict[str, Any]) -> None:
    implementation = _as_dict(snapshot.get("implementation_workspace"))
    technical = _as_dict(snapshot.get("technical_workspace"))
    maintenance = _as_dict(_first_present(implementation.get("maintenance_risk"), technical.get("maintenance_risk")))
    if not maintenance and _as_dict(result.get("site_health")).get("security"):
        maintenance = build_maintenance_risk_summary(result)
    cards = _as_list(maintenance.get("cards"), limit=8)
    if not cards:
        return
    lines.append("## 6. 保守・更新管理")
    summary = _md(maintenance.get("summary"))
    if summary:
        lines.append(f"- {summary}")
    for card in cards:
        if not isinstance(card, dict):
            continue
        title = _md(card.get("title"))
        status = _md(card.get("status_label"))
        detail = _md(card.get("summary") or card.get("detail"))
        lines.append(f"- {title}: {status}" + (f" / {detail}" if detail else ""))
        metrics = _as_dict(card.get("metrics"))
        metric_bits = []
        for label, key in (
            ("フォーム数", "form_count"),
            ("personal fields", "personal_fields"),
            ("CSRF/nonce痕跡", "csrf_or_nonce"),
            ("privacy同意", "privacy_consent"),
            ("captcha痕跡", "captcha"),
            ("file upload", "file_upload"),
            ("sensitive", "sensitive_context"),
            ("external action", "external_action"),
            ("checked endpoints", "checked_endpoints"),
            ("problem endpoints", "problem_endpoints"),
        ):
            if key in metrics:
                metric_bits.append(f"{label}: {_md(metrics.get(key))}")
        if metric_bits:
            lines.append(f"  - {' / '.join(metric_bits)}")
        for bullet in _as_list(card.get("bullets"), limit=4):
            bullet_text = _md(bullet)
            if bullet_text:
                lines.append(f"  - {bullet_text}")
    lines.append("")


def _append_raw_appendix(lines: List[str], result: Dict[str, Any]) -> None:
    lines.append("## 8. 補足データ")
    sitemap = _as_dict(result.get("sitemap_info") or result.get("sitemap_analysis"))
    crawl = _as_dict(result.get("crawl_strategy"))
    internal = _as_dict(result.get("internal_link_summary"))
    legacy = _as_dict(result.get("legacy_page_report"))
    rows = [
        ("sitemap URL数", _first_present(sitemap.get("url_count"), sitemap.get("total_urls"))),
        ("把握ページ", _first_present(internal.get("total_known_pages"), internal.get("total_pages"))),
        ("分析ページ", _first_present(internal.get("analyzed_pages"), crawl.get("analyzed_pages"))),
        ("孤立ページ", internal.get("orphan_count")),
        ("低リンクページ", internal.get("low_link_count")),
        ("旧HTML検出", legacy.get("found_count")),
    ]
    emitted = False
    for label, value in rows:
        if value not in (None, ""):
            lines.append(f"- {label}: {_md(value)}")
            emitted = True
    if not emitted:
        lines.append("- 追加の補足データは保存結果にありません。")
    lines.append("")


def build_detailed_markdown_report(bundle: Dict[str, Any]) -> str:
    run_row = _as_dict(bundle.get("run"))
    snapshot = _as_dict(bundle.get("snapshot"))
    result = _as_dict(bundle.get("result"))
    meta = _as_dict(snapshot.get("meta"))

    run_id = _first_present(run_row.get("id"), meta.get("run_id"))
    analyzed_at = _first_present(run_row.get("analyzed_at"), meta.get("analyzed_at"))
    analyzed_at_display = format_jst_datetime(analyzed_at)
    url = _first_present(run_row.get("url"), meta.get("url"), result.get("url"))

    lines: List[str] = [
        "# コトミガキ 詳細分析レポート",
        "",
        f"- run_id: {_md(run_id)}",
        f"- URL: {_md(url)}",
        f"- 分析日時: {_md(analyzed_at_display)}",
        f"- 出力日時: {current_jst_datetime_text(seconds=True)}",
    ]
    for label, key in (("業界", "industry"), ("サイト種別", "site_type"), ("プラットフォーム", "platform"), ("目的", "business_goal")):
        value = _md(meta.get(key) or run_row.get(key))
        if value:
            lines.append(f"- {label}: {value}")
    lines.append("")

    summary_workspace = _as_dict(snapshot.get("summary_workspace"))
    summary_lines = [
        _md(item)
        for item in _as_list(summary_workspace.get("summary_lines"), limit=7)
        if _md(item)
    ]
    if summary_lines:
        lines.append("## 0. このURL固有の見立て")
        for item in summary_lines:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## 1. スコアと判定")
    lines.append("| 指標 | 値 |")
    lines.append("| --- | --- |")
    for label, value in _score_rows(snapshot, run_row, result):
        if value not in (None, ""):
            lines.append(f"| {_table_cell(label)} | {_table_cell(value)} |")
    lines.append("")

    lines.append("## 2. 最優先アクション")
    actions = _as_list(_as_dict(snapshot.get("exports")).get("priority_actions"), limit=20)
    if actions:
        for index, action in enumerate(actions, 1):
            if isinstance(action, dict):
                _append_action(lines, action, index)
    else:
        lines.append("- 保存済みsnapshot内に優先アクションはありません。")
        lines.append("")

    _append_score_drivers(lines, snapshot, result)
    _append_intent_section(lines, snapshot)
    _append_writing_section(lines, snapshot)
    _append_maintenance_section(lines, snapshot, result)
    _append_technical_section(lines, snapshot, result)
    _append_raw_appendix(lines, result)

    lines.append("---")
    lines.append("このMarkdownは保存済みresult JSON / snapshot JSONから生成しています。追加API送信は行いません。")
    lines.append("")
    return "\n".join(lines)


def export_detailed_markdown_report(bundle: Dict[str, Any]) -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    run_row = _as_dict(bundle.get("run"))
    snapshot = _as_dict(bundle.get("snapshot"))
    meta = _as_dict(snapshot.get("meta"))
    run_id = _first_present(run_row.get("id"), meta.get("run_id"), "unknown")
    timestamp = current_jst_filename_timestamp()
    output_path = EXPORTS_DIR / f"detailed-report-run-{run_id}-{timestamp}.md"
    output_path.write_text(build_detailed_markdown_report(bundle), encoding="utf-8")
    return output_path
