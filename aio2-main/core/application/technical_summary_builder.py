from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import unquote, urlsplit

from core.site_health.maintenance_risk import build_maintenance_risk_summary

def _safe_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0

def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()

def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)

def _json_clone(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=_json_default))
    except (TypeError, ValueError):
        return value

def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}

def _normalize_status_code(status: Any, *, default: str = "unverified") -> str:
    normalized = _safe_text(status).lower()
    if normalized in {"fail", "要対応"}:
        return "fail"
    if normalized in {"warn", "warning", "注意", "要確認"}:
        return "warn"
    if normalized in {"pass", "ok", "success", "通過", "問題なし"}:
        return "pass"
    if normalized in {"reference", "info", "参考"}:
        return "reference"
    if normalized in {"unknown", "unverified", "unchecked", "未確認", "未判定"}:
        return "unverified"
    if normalized in {"not_applicable", "not-applicable", "n/a", "na", "対象外"}:
        return "not_applicable"
    if normalized in {"error", "failed", "取得エラー", "検査エラー"}:
        return "error"
    return default

def _snapshot_status_label(status: Any) -> str:
    return {
        "fail": "要対応",
        "warn": "注意",
        "pass": "通過",
        "reference": "参考",
        "unverified": "未確認",
        "not_applicable": "対象外",
        "error": "取得エラー",
    }.get(_normalize_status_code(status), "未確認")

def _safe_text_list(values: Any, *, limit: int = 6) -> List[str]:
    normalized: List[str] = []
    for value in values or []:
        text = _safe_text(value)
        if text and text not in normalized:
            normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized

def _clean_page_focus(text: Any) -> str:
    normalized = _safe_text(text)
    if not normalized:
        return ""
    head = re.split(r"[|｜:：/\-‐–—・]", normalized, maxsplit=1)[0].strip()
    head = re.sub(r"\s+", " ", head)
    if head.lower() in {"home", "top", "トップ"}:
        return ""
    return head

def _build_legacy_page_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    report = results.get("legacy_page_report") or {}
    if not isinstance(report, dict):
        report = {}
    pages = [
        item for item in (report.get("pages") or [])
        if isinstance(item, dict) and _safe_text(item.get("final_url") or item.get("url"))
    ]
    found_count = _safe_int(report.get("found_count")) or len(pages)
    checked_count = _safe_int(report.get("checked_count"))
    status = _normalize_status_code(report.get("status"), default="reference")
    if found_count > 0:
        status = "fail"
    elif checked_count > 0 and status == "reference":
        status = "pass"

    if found_count > 0:
        detail = f"古いページが {found_count} 件公開されたままです。検索やAI回答が古い情報を拾う可能性があります。"
    else:
        detail = ""
    page_urls = [
        _safe_text(item.get("final_url") or item.get("url"))
        for item in pages[:5]
        if _safe_text(item.get("final_url") or item.get("url"))
    ]
    sample_url = page_urls[0] if page_urls else "対象URL"
    engineer_tasks = []
    verification_steps = []
    if found_count > 0:
        engineer_tasks = [
            {
                "title": "対応先URLを決める",
                "detail": "各旧URLに対して、現行のサービスページ・会社情報ページなど最も近い移転先を1つ決めてください。",
            },
            {
                "title": "サーバー側で恒久リダイレクトを設定する",
                "detail": "Webサーバー、CDN、CMSのリダイレクト機能で旧URLから対応先URLへ 301 または 308 を返すよう設定してください。",
            },
            {
                "title": "リダイレクトできない場合の暫定対応",
                "detail": "旧HTMLを残す必要がある場合は head に canonical を現行URLへ向け、robots noindex を追加してください。",
            },
            {
                "title": "旧URLの再混入を防ぐ",
                "detail": "sitemap、内部リンク、テンプレート、静的ファイル配信元に旧URLが残っていないか確認してください。",
            },
        ]
        verification_steps = [
            {
                "title": "旧URLのHTTP応答",
                "detail": f"`curl -I {sample_url}` で 301/308 と Location ヘッダーを確認してください。",
            },
            {
                "title": "移転先の到達確認",
                "detail": "Location の移転先が 200 で表示され、意図した現行ページになっていることを確認してください。",
            },
            {
                "title": "暫定対応時のhead確認",
                "detail": "リダイレクトしない場合は、旧HTMLに canonical と noindex が両方入っていることを確認してください。",
            },
            {
                "title": "再分析",
                "detail": "対応後に再分析し、古い公開ページの検出件数が0件になることを確認してください。",
            },
        ]

    return {
        "title": "古い公開ページ",
        "detail": detail,
        "technical_detail": (
            f"{found_count}件が 200 / index可能 / canonicalなし / 最終URL .html の条件に一致しました。"
            if found_count > 0
            else ""
        ),
        "status": status,
        "status_label": _snapshot_status_label(status),
        "found_count": found_count,
        "checked_count": checked_count,
        "pages": _json_clone(pages[:10]) or [],
        "checked_urls": _json_clone((report.get("checked_urls") or [])[:12]) or [],
        "recommendations": _json_clone((report.get("recommendations") or [])[:4]) or [],
        "engineer_tasks": engineer_tasks,
        "verification_steps": verification_steps,
        "errors": _json_clone((report.get("errors") or [])[:3]) or [],
    }

def _brief_texts(items: Any, *, keys: tuple[str, ...], limit: int = 3) -> List[str]:
    texts: List[str] = []
    if not isinstance(items, list):
        return texts
    for item in items:
        text = ""
        if isinstance(item, dict):
            for key in keys:
                text = _safe_text(item.get(key))
                if text:
                    break
        else:
            text = _safe_text(item)
        if not text or text in texts:
            continue
        texts.append(text)
        if len(texts) >= limit:
            break
    return texts

def _score_status(score: float, *, good: float, warn: float) -> str:
    if score >= good:
        return "pass"
    if score >= warn:
        return "warn"
    return "fail"

def _build_llms_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    aio_results = results.get("aio_results") or {}
    llms_payload = aio_results.get("llms_txt") or {}
    if not isinstance(llms_payload, dict):
        llms_payload = {}

    exists = bool(llms_payload.get("exists"))
    found_paths = [str(path).strip() for path in (llms_payload.get("found_paths") or []) if str(path).strip()]
    checked_paths = [str(path).strip() for path in (llms_payload.get("checked_paths") or []) if str(path).strip()]
    quality_score = _safe_int(llms_payload.get("quality_score"))
    quality_level = _safe_text(llms_payload.get("quality_level"))
    issues = _brief_texts(llms_payload.get("quality_issues") or [], keys=("issue",), limit=4)
    recommendations = _brief_texts(llms_payload.get("quality_recommendations") or [], keys=("recommendation",), limit=4)

    if exists:
        status = "pass"
        if quality_score and quality_score < 80:
            status = "warn"
        elif issues:
            status = "warn"
        detail_bits = ["設置済み"]
        if quality_score > 0:
            detail_bits.append(f"品質 {quality_score}点")
        if quality_level:
            detail_bits.append(f"判定 {quality_level}")
        if found_paths:
            detail_bits.append(f"検出: {', '.join(found_paths[:2])}")
        lead = issues[0] if issues else (recommendations[0] if recommendations else "")
        if lead:
            detail_bits.append(lead)
        detail = " / ".join([bit for bit in detail_bits if bit])
        title = "AI向け案内ファイル（llms.txt / 任意）"
    else:
        detail = "未設置です。必須ではありませんが、AI向け案内として運用するなら `/llms.txt` を推奨します。"
        if checked_paths:
            detail = f"{detail} 確認先: {', '.join(checked_paths[:3])}"
        status = "reference"
        title = "AI向け案内ファイル（llms.txt / 任意）"

    return {
        "title": title,
        "detail": detail,
        "status": status,
        "status_label": _snapshot_status_label(status),
        "exists": exists,
        "quality_score": quality_score,
        "quality_level": quality_level,
        "found_paths": found_paths,
        "checked_paths": checked_paths,
        "issues": issues,
        "recommendations": recommendations,
        "setup_judgment": "設置済み" if exists else "任意。AI向け目次を運用する場合は新規設置候補です。",
        "recommended_content": [
            "サイト名と提供サービスの短い要約",
            "重要ページのURL（サービス、料金、FAQ、会社概要、問い合わせ）",
            "AIに引用してほしい一次情報と更新日",
        ],
        "content_type": "text/plain; charset=utf-8",
        "fix_location": "サイトルート直下 `/llms.txt`",
        "command": f"curl -I {checked_paths[0] if checked_paths else '/llms.txt'}",
        "pass_condition": "HTTP 200、Content-Type が text/plain、本文に主要URLと更新日が含まれる",
    }

def _build_llms_notes(results: Dict[str, Any]) -> List[Dict[str, str]]:
    summary = _build_llms_summary(results)
    notes = [
        {
            "title": _safe_text(summary.get("title")),
            "detail": _safe_text(summary.get("detail")),
            "label": "対象ページで確認",
        }
    ]
    recommendations = summary.get("recommendations") or []
    if recommendations:
        notes.append(
            {
                "title": "llms.txt 改善メモ",
                "detail": " / ".join(recommendations[:2]),
                "label": "対象ページで確認",
            }
        )
    return [item for item in notes if _safe_text(item.get("detail"))]

def _build_reference_notes(results: Dict[str, Any]) -> List[Dict[str, str]]:
    platform_guidance = results.get("platform_guidance") or {}
    references: List[Dict[str, str]] = []
    for step in (platform_guidance.get("business_steps") or [])[:3]:
        references.append({"title": "運用ガイド", "detail": _safe_text(step), "label": "参考"})
    for step in (platform_guidance.get("technical_steps") or [])[:3]:
        references.append({"title": "技術ガイド", "detail": _safe_text(step), "label": "参考"})
    for link in (platform_guidance.get("help_links") or [])[:3]:
        references.append(
            {
                "title": _safe_text(link.get("label")) or "公式ドキュメント",
                "detail": _safe_text(link.get("url")),
                "label": "参考",
            }
        )
    return references

def _build_crawl_scope_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    sitemap_info = results.get("sitemap_info") or {}
    crawl_strategy = results.get("crawl_strategy") or {}
    priority_pages_crawled = results.get("priority_pages_crawled") or {}
    link_health = results.get("link_health_report") or {}

    total_urls = _safe_int(sitemap_info.get("total_urls"))
    sampled_count = _safe_int(sitemap_info.get("sampled_count"))
    update_frequency = _safe_text(sitemap_info.get("update_frequency"))
    parsed_sitemaps = _safe_int(sitemap_info.get("parsed_sitemaps"))
    warning = _safe_text(sitemap_info.get("warning"))
    error = _safe_text(sitemap_info.get("error"))
    source_sitemaps = [
        _safe_text(item)
        for item in (sitemap_info.get("source_sitemaps") or [])[:5]
        if _safe_text(item)
    ]
    priority_pages = [
        item for item in (priority_pages_crawled.get("pages") or []) if isinstance(item, dict)
    ]
    priority_candidates = crawl_strategy.get("priority_candidates") or crawl_strategy.get("priority_pages") or []
    audited_targets = _safe_int(link_health.get("audited_target_count"))

    detail_bits: List[str] = []
    if total_urls > 0:
        detail_bits.append(f"sitemap {total_urls:,}URL")
    if sampled_count > 0:
        detail_bits.append(f"サンプル {sampled_count:,}URL")
    if priority_pages:
        detail_bits.append(f"優先ページ取得 {len(priority_pages)}件")
    elif priority_candidates:
        detail_bits.append(f"優先候補 {len(priority_candidates)}件")
    if audited_targets > 0:
        detail_bits.append(f"内部リンク先監査 {audited_targets}件")
    if update_frequency and update_frequency != "不明":
        detail_bits.append(f"更新頻度 {update_frequency}")

    status = "warn" if warning or error else "reference"
    detail = " / ".join(detail_bits)
    if error and not detail:
        detail = error
    elif warning:
        detail = f"{detail} / {warning}" if detail else warning

    return {
        "title": "クロール範囲",
        "detail": detail or "sitemap と優先ページ取得の情報はありません。",
        "status": status,
        "status_label": _snapshot_status_label(status),
        "sitemap_total_urls": total_urls,
        "sampled_count": sampled_count,
        "update_frequency": update_frequency,
        "parsed_sitemaps": parsed_sitemaps,
        "warning": warning,
        "error": error,
        "priority_pages_fetched": len(priority_pages),
        "priority_pages_planned": len(priority_candidates),
        "priority_pages": _json_clone(priority_pages[:6]) or [],
        "source_sitemaps": source_sitemaps,
        "audited_target_count": audited_targets,
    }

def _link_candidate_url(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("url", "final_url", "canonical_url", "target_url"):
            text = _safe_text(value.get(key))
            if text:
                return text
        return _safe_text(value.get("title"))
    return _safe_text(value)

def _link_candidate_label(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("title", "label", "text", "url", "final_url"):
            text = _safe_text(value.get(key))
            if text:
                return text
    text = _safe_text(value)
    if "://" in text:
        return ""
    return text

def _page_topic_from_url(url: Any) -> str:
    raw = _safe_text(url)
    if not raw:
        return "対象ページ"
    try:
        parsed = urlsplit(raw)
        path = unquote(parsed.path or "")
    except Exception:
        path = raw
    parts = [part for part in re.split(r"[/_.\-]+", path) if part]
    stopwords = {"index", "html", "htm", "php", "page", "pages", "post", "entry", "service", "services"}
    useful = [
        part for part in parts
        if part.lower() not in stopwords and not part.isdigit() and len(part) > 1
    ]
    if useful:
        return _clean_page_focus(useful[-1]) or useful[-1]
    host = _safe_text(urlsplit(raw).netloc if "://" in raw else "")
    return host or "対象ページ"

def _build_link_anchor_text(target_url: str, target_label: str = "") -> str:
    topic = _clean_page_focus(target_label) or _page_topic_from_url(target_url)
    if not topic or topic == "対象ページ":
        return "対象ページの主題が分かる自然なアンカー"
    return f"{topic}の詳細"

def _build_internal_link_opportunities(
    *,
    results_url: str,
    internal_summary: Dict[str, Any],
    link_health: Dict[str, Any],
    limit: int = 3,
) -> List[Dict[str, Any]]:
    hub_pages = link_health.get("hub_pages") or []
    source_urls = [_link_candidate_url(item) for item in hub_pages]
    source_urls = [url for url in source_urls if url]
    if not source_urls and results_url:
        source_urls = [results_url]

    target_items: List[Any] = []
    for key, issue_label in (("orphan_pages", "孤立ページ"), ("low_link_pages", "内部リンクが少ないページ")):
        for item in internal_summary.get(key) or []:
            target_url = _link_candidate_url(item)
            if not target_url:
                continue
            target_items.append({"value": item, "issue_label": issue_label, "target_url": target_url})

    opportunities: List[Dict[str, Any]] = []
    seen_targets: set[str] = set()
    for index, target in enumerate(target_items):
        target_url = _safe_text(target.get("target_url"))
        if not target_url or target_url in seen_targets:
            continue
        seen_targets.add(target_url)
        source_url = source_urls[min(index, max(len(source_urls) - 1, 0))] if source_urls else ""
        target_label = _link_candidate_label(target.get("value"))
        anchor = _build_link_anchor_text(target_url, target_label)
        opportunities.append(
            {
                "title": f"{target.get('issue_label')}へ内部リンクを追加",
                "source_url": source_url,
                "target_url": target_url,
                "recommended_anchor": anchor,
                "reason": f"{target.get('issue_label')}は検索エンジンとAIが重要ページを見つけにくくなるため、関連ページから本文内リンクを追加します。",
                "placement": "本文中の関連説明、サービス一覧、導線ブロック",
                "check": "再分析後に孤立/低リンク件数が減り、リンク先がHTTP 200でindex可能であることを確認",
            }
        )
        if len(opportunities) >= limit:
            break
    return opportunities

def _build_link_health_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    internal_summary = results.get("internal_link_summary") or {}
    link_health = results.get("link_health_report") or {}
    if not isinstance(internal_summary, dict):
        internal_summary = {}
    if not isinstance(link_health, dict):
        link_health = {}
    if not internal_summary and not link_health:
        return {}

    health_score = float(link_health.get("health_score", 0.0) or 0.0)
    diagnosis = _safe_text(link_health.get("diagnosis"))
    known_pages = _safe_int(link_health.get("total_known_pages") or internal_summary.get("total_pages"))
    analyzed_pages = _safe_int(link_health.get("total_analyzed_pages") or internal_summary.get("total_pages"))
    orphan_count = _safe_int(link_health.get("orphan_count") or internal_summary.get("orphan_count"))
    low_link_count = _safe_int(link_health.get("low_link_count") or internal_summary.get("low_link_count"))
    avg_depth = float(link_health.get("avg_depth", 0.0) or 0.0)
    audited_targets = _safe_int(link_health.get("audited_target_count"))
    broken_count = _safe_int(link_health.get("broken_target_count"))
    redirected_count = _safe_int(link_health.get("redirected_target_count"))
    canonical_count = _safe_int(link_health.get("canonical_mismatch_count"))
    noindex_count = _safe_int(link_health.get("noindex_target_count"))

    if broken_count > 0 or health_score < 50:
        status = "fail"
    elif redirected_count > 0 or canonical_count > 0 or noindex_count > 0 or orphan_count > 0 or low_link_count > 0 or health_score < 80:
        status = "warn"
    else:
        status = "pass"

    detail_bits: List[str] = []
    if health_score > 0:
        detail_bits.append(f"健康度 {health_score:.0f}点")
    if known_pages > 0:
        detail_bits.append(f"把握 {known_pages}ページ")
    if audited_targets > 0:
        detail_bits.append(f"監査 {audited_targets}件")
    issue_bits: List[str] = []
    if broken_count > 0:
        issue_bits.append(f"エラー {broken_count}件")
    if orphan_count > 0:
        issue_bits.append(f"孤立 {orphan_count}件")
    if redirected_count > 0:
        issue_bits.append(f"リダイレクト {redirected_count}件")
    if canonical_count > 0:
        issue_bits.append(f"canonical {canonical_count}件")
    if noindex_count > 0:
        issue_bits.append(f"noindex {noindex_count}件")
    if low_link_count > 0 and not issue_bits:
        issue_bits.append(f"薄いリンク {low_link_count}件")
    if issue_bits:
        detail_bits.append(" / ".join(issue_bits[:3]))
    elif diagnosis:
        detail_bits.append(diagnosis)

    source_page_candidates = _json_clone((link_health.get("hub_pages") or [])[:3]) or []
    target_page_candidates = _json_clone(
        (internal_summary.get("orphan_pages") or internal_summary.get("low_link_pages") or [])[:5]
    ) or []
    link_opportunities = _build_internal_link_opportunities(
        results_url=_safe_text(results.get("url")),
        internal_summary=internal_summary,
        link_health=link_health,
        limit=3,
    )
    recommended_anchor = "ページの主題語を含む自然なアンカーテキスト"
    if link_opportunities:
        recommended_anchor = _safe_text(link_opportunities[0].get("recommended_anchor")) or recommended_anchor
    elif target_page_candidates:
        first_target = _link_candidate_url(target_page_candidates[0])
        if first_target:
            recommended_anchor = _build_link_anchor_text(first_target)
    engineering_steps = []
    if broken_count > 0:
        engineering_steps.append(
            {
                "observed": f"リンク先HTTPエラー候補 {broken_count}件",
                "fix_location": "該当リンクを含む本文、ナビゲーション、フッター",
                "command": "curl -I <リンク先URL>",
                "pass_condition": "最終URLがHTTP 200で、意図したページへ到達する",
            }
        )
    if orphan_count > 0 or low_link_count > 0:
        engineering_steps.append(
            {
                "observed": f"孤立ページ {orphan_count}件 / 薄いリンク {low_link_count}件",
                "fix_location": "関連する親ページ、サービス一覧、導線ブロック",
                "command": "対象ページへの内部リンク数とアンカーテキストを再クロールで確認",
                "pass_condition": "重要ページに本文内リンクが追加され、孤立/薄いリンク件数が減る",
            }
        )
    if redirected_count > 0 or canonical_count > 0 or noindex_count > 0:
        engineering_steps.append(
            {
                "observed": f"redirect {redirected_count}件 / canonical {canonical_count}件 / noindex {noindex_count}件",
                "fix_location": "リンク元URL、canonical設定、robots/meta robots設定",
                "command": "curl -I <リンク先URL> と HTML head の canonical / robots を確認",
                "pass_condition": "内部リンクが正規URLを指し、重要リンク先がindex可能になる",
            }
        )

    return {
        "title": "内部リンク健全性",
        "detail": " / ".join([bit for bit in detail_bits if bit]) or "内部リンクの追加情報はありません。",
        "status": status,
        "status_label": _snapshot_status_label(status),
        "score": round(health_score, 1),
        "health_score": round(health_score, 1),
        "diagnosis": diagnosis,
        "total_known_pages": known_pages,
        "total_analyzed_pages": analyzed_pages,
        "orphan_count": orphan_count,
        "low_link_count": low_link_count,
        "avg_depth": round(avg_depth, 2),
        "audited_target_count": audited_targets,
        "broken_target_count": broken_count,
        "redirected_target_count": redirected_count,
        "canonical_mismatch_count": canonical_count,
        "noindex_target_count": noindex_count,
        "hub_pages": _json_clone(link_health.get("hub_pages") or []) or [],
        "broken_targets": _json_clone(link_health.get("broken_targets") or []) or [],
        "redirected_targets": _json_clone(link_health.get("redirected_targets") or []) or [],
        "canonical_mismatches": _json_clone(link_health.get("canonical_mismatches") or []) or [],
        "noindex_targets": _json_clone(link_health.get("noindex_targets") or []) or [],
        "orphan_pages": _json_clone((internal_summary.get("orphan_pages") or [])[:5]) or [],
        "low_link_pages": _json_clone((internal_summary.get("low_link_pages") or [])[:5]) or [],
        "source_page_candidates": source_page_candidates,
        "target_page_candidates": target_page_candidates,
        "recommended_anchor": recommended_anchor,
        "link_opportunities": link_opportunities,
        "engineering_steps": engineering_steps,
    }

def _security_verification_for_issue(issue: Dict[str, Any], url: str) -> str:
    issue_id = _safe_text(issue.get("id"))
    evidence = _safe_text(issue.get("evidence"))
    if issue_id == "wordpress_rest_users_public" and evidence:
        return f"`curl -s {evidence}` で未認証ユーザー一覧が返らないことを確認"
    if issue_id == "jquery_before_3_5":
        return "ブラウザ開発者ツールまたはページソースで jQuery 3.5.0 以上に更新されたことを確認"
    if issue_id == "outdated_frontend_asset":
        return "ページソースで古い可能性のあるフロントエンド資産の読み込みが整理され、必要な資産だけが残っていることを確認"
    if issue_id == "external_cdn_without_sri":
        return "対象script/linkに integrity と crossorigin が付く、または自社ドメイン配信へ変わったことを確認"
    if issue_id == "stale_or_static_sitemap":
        root = ""
        try:
            parsed = urlsplit(url)
            root = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml" if parsed.scheme and parsed.netloc else ""
        except Exception:
            root = ""
        return f"`curl -s {root or '/sitemap.xml'}` で最新URLと新しいlastmodが出ることを確認"
    if issue_id == "universal_analytics_tag":
        return "ページソースに UA- 形式のタグが残っていないことを確認"
    if issue_id == "cms_generator_public":
        return "本体・テーマ・プラグイン更新後、公開HTMLに不要なgenerator/version露出がないことを確認"
    if issue_id == "legacy_ie_polyfills":
        return "ページソースから html5shiv / respond.js の読み込みが消えたことを確認"
    if issue_id == "suspicious_external_asset_domain":
        return "ページソースで対象ドメイン参照が消えていること、または信頼済みCDN/自社配信へ置き換わっていることを確認"
    if issue_id == "target_blank_without_noopener":
        return '対象リンクの target="_blank" に rel="noopener noreferrer" が付いていることをページソースで確認'
    if issue_id == "internal_http_navigation_link":
        return "ページソースとクリック導線を確認し、同一ドメイン内の http:// リンク/フォーム送信先が https:// または相対URLへ統一されたことを確認"
    if issue_id == "form_action_http":
        return "対象フォームの action が https:// または相対URLになり、送信先がHTTPSで到達することを確認"
    if issue_id == "password_form_without_https_page":
        return "ログイン/会員フォームの表示ページと送信先がどちらもHTTPSであることを確認"
    if issue_id == "file_upload_form_without_captcha_hint":
        return "アップロード容量・拡張子制限・ウイルスチェック・bot対策の設定を確認し、必要なら再分析で確認候補が消えることを確認"
    if issue_id == "personal_form_without_privacy_consent_hint":
        return "対象フォームにプライバシーポリシーリンク、利用目的、同意チェックが表示されることを確認"
    if issue_id == "post_form_without_csrf_hint":
        return "フォームHTMLまたはサーバー側設定でCSRF/nonce対策が有効であることを保守会社に確認"
    if issue_id == "sitemap_unavailable_or_invalid":
        return "`curl -I /sitemap.xml` と `curl -s /sitemap.xml` でHTTP 200かつXMLとして解析できることを確認"
    if issue_id == "visible_update_date_old":
        return "お知らせ/事例/採用/会社情報の最新日付を確認し、更新後に公開HTMLとsitemap lastmodの両方が新しくなることを確認"
    if issue_id == "update_signal_mismatch":
        return "公開HTML上の見える更新日と sitemap lastmod が同じ更新状態になり、Search Console登録先も一致していることを確認"
    if issue_id in {"robots_txt_html_fake_200", "robots_txt_invalid_or_empty"}:
        target = evidence or f"{_root_url(url)}/robots.txt"
        return f"`curl -i {target}` でHTTP status、Content-Type、robots.txt本文を確認"
    if issue_id in {"sitemap_endpoint_html_fake_200", "unused_endpoint_fake_200"}:
        target = evidence or f"{_root_url(url)}/sitemap.xml"
        return f"`curl -i {target}` でHTMLではなくXML/API応答または404/410になることを確認"
    if issue_id == "soft_404_missing_url_200":
        target = evidence or "存在しない確認用URL"
        return f"`curl -i {target}` で404/410、またはnoindex等の意図した扱いになっていることを確認"
    if issue_id == "server_environment_header_exposed":
        return " `curl -I` で X-Powered-By / Server にPHPバージョンやPleskLin等の不要な露出が残っていないことを確認"
    if issue_id == "form_action_external":
        return "対象フォームの外部送信先が正規サービスで、保存先権限・通知先・スパム対策が意図どおりであることを確認"
    if issue_id == "personal_form_without_public_protection_hints":
        return "公開HTMLまたはフォーム設定でtoken/nonce、captcha、privacy同意のいずれか、または同等のサーバー側対策が確認済みであることを確認"
    return "対応後に再分析し、同じ公開技術リスクが消えることを確認"


def _root_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
    except Exception:
        return ""


def _security_commands_for_issue(issue: Dict[str, Any], url: str) -> List[str]:
    issue_id = _safe_text(issue.get("id"))
    evidence = _safe_text(issue.get("evidence"))
    root = _root_url(url)
    sitemap_url = f"{root}/sitemap.xml" if root else "/sitemap.xml"
    target_url = url or root or "対象URL"
    endpoint_target = evidence or target_url
    if issue_id in {"stale_or_static_sitemap", "sitemap_unavailable_or_invalid", "update_signal_mismatch"}:
        return [
            f"curl -I {sitemap_url}",
            f"curl -sL {sitemap_url} | rg \"<lastmod>|<loc>\"",
            f"curl -sL {target_url} | rg \"20\\\\d{{2}}[./-]\"",
        ]
    if issue_id in {"robots_txt_html_fake_200", "robots_txt_invalid_or_empty"}:
        return [
            f"curl -i {endpoint_target}",
            f"curl -sL {endpoint_target} | rg \"^(User-agent|Disallow|Allow|Sitemap):|<html|<!doctype\"",
        ]
    if issue_id in {"sitemap_endpoint_html_fake_200", "unused_endpoint_fake_200"}:
        return [
            f"curl -i {endpoint_target}",
            f"curl -sL {endpoint_target} | rg \"<urlset|<sitemapindex|<html|<!doctype|wp-json\"",
        ]
    if issue_id == "soft_404_missing_url_200":
        return [
            f"curl -i {endpoint_target}",
            f"curl -sL {endpoint_target} | rg \"<title|canonical|noindex\"",
        ]
    if issue_id == "server_environment_header_exposed":
        return [f"curl -I {root or target_url}"]
    if issue_id in {"jquery_before_3_5", "outdated_frontend_asset", "legacy_ie_polyfills"}:
        scan_target = target_url
        return [
            f"curl -sL {scan_target} | rg \"jquery|jquery-ui|bootstrap|swiper|slick|modernizr|html5shiv|respond\"",
        ]
    if issue_id == "wordpress_rest_users_public" and evidence:
        return [f"curl -s {evidence}"]
    if issue_id == "cms_generator_public":
        return [f"curl -sL {target_url} | rg \"generator|wp-content|wp-json\""]
    if issue_id == "external_cdn_without_sri":
        return [f"curl -sL {target_url} | rg \"<script|<link|integrity=\""]
    if issue_id in {"form_action_http", "form_action_external", "password_form_without_https_page", "file_upload_form_without_captcha_hint", "personal_form_without_privacy_consent_hint", "personal_form_without_public_protection_hints", "post_form_without_csrf_hint"}:
        return [f"curl -sL {target_url} | rg \"<form|csrf|nonce|privacy|個人情報|captcha|file\""]
    if issue_id == "internal_http_navigation_link":
        return [f"curl -sL {target_url} | rg \"http://\""]
    return [f"curl -sL {target_url}"]


def _security_pass_condition_for_issue(issue: Dict[str, Any]) -> str:
    issue_id = _safe_text(issue.get("id"))
    if issue_id == "update_signal_mismatch":
        return "見える最新日付と sitemap lastmod がどちらも直近の更新を示し、差分理由を保守会社が説明できる状態。"
    if issue_id == "sitemap_unavailable_or_invalid":
        return "sitemap.xml がHTTP 200で取得でき、XMLとして解析できる状態。"
    if issue_id in {"stale_or_static_sitemap", "visible_update_date_old"}:
        return "公開ページとsitemapの更新日が実際の更新状況に合わせて新しくなっている状態。"
    if issue_id in {"jquery_before_3_5", "outdated_frontend_asset", "legacy_ie_polyfills"}:
        return "不要な古い資産が削除され、必要なテーマ/プラグイン資産だけに棚卸し済みの状態。"
    if issue_id == "wordpress_rest_users_public":
        return "未認証の users endpoint で管理者ユーザー名が返らない状態。"
    if issue_id in {"robots_txt_html_fake_200", "robots_txt_invalid_or_empty"}:
        return "robots.txt がテキストとして取得でき、User-agent / Disallow / Allow / Sitemap の意図した行が確認できる、または不要なら404/410になる状態。"
    if issue_id == "sitemap_endpoint_html_fake_200":
        return "sitemap endpoint がXMLを返す、または使わないendpointが404/410になる状態。"
    if issue_id == "unused_endpoint_fake_200":
        return "不要なwp系endpointがトップページHTMLを200で返さない状態。"
    if issue_id == "soft_404_missing_url_200":
        return "存在しないURLが404/410を返し、トップページ相当HTMLを200で返さない状態。"
    if issue_id == "server_environment_header_exposed":
        return "PHPバージョンやPleskLin等の不要な環境情報がHTTPヘッダーに残らず、EOL系列の場合は更新計画が確認済みの状態。"
    if issue_id in {"form_action_http", "form_action_external", "password_form_without_https_page", "file_upload_form_without_captcha_hint", "personal_form_without_privacy_consent_hint", "personal_form_without_public_protection_hints", "post_form_without_csrf_hint"}:
        return "公開HTML上のフォーム確認候補が解消し、サーバー側対策の有効性を保守会社が確認済みの状態。"
    return "再分析で同じ issue id が出ない状態。"

def _security_evidence_summary(issue: Dict[str, Any]) -> str:
    details = _safe_dict(issue.get("evidence_details"))
    if not details:
        return ""
    parts = []
    status = _safe_text(details.get("status_code"))
    content_type = _safe_text(details.get("content_type"))
    excerpt = _safe_text(details.get("excerpt"))
    urgency = _safe_text(details.get("urgency") or issue.get("urgency"))
    if status:
        parts.append(f"HTTP {status}")
    if content_type:
        parts.append(f"Content-Type: {content_type}")
    if excerpt:
        parts.append(f"抜粋: {excerpt[:120]}")
    if urgency:
        parts.append(f"緊急度: {urgency}")
    return " / ".join(parts)

def _build_security_engineering_tasks(
    *,
    issues: List[Dict[str, Any]],
    url: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    for issue in issues[:limit]:
        if not isinstance(issue, dict):
            continue
        title = _safe_text(issue.get("title") or issue.get("issue"))
        recommendation = _safe_text(issue.get("recommendation"))
        detail = _safe_text(issue.get("detail"))
        evidence = _safe_text(issue.get("evidence"))
        observed = _security_evidence_summary(issue)
        if not title and not recommendation:
            continue
        work = recommendation or detail
        if observed:
            work = f"{work} / 検出根拠: {observed}" if work else f"検出根拠: {observed}"
        tasks.append(
            {
                "title": title or "公開技術リスクを確認",
                "target": _safe_text(issue.get("confirmation_url")) or evidence or detail or "対象ページの公開HTML/HTTPヘッダー",
                "work": work,
                "verify": _security_verification_for_issue(issue, url),
                "commands": _security_commands_for_issue(issue, url),
                "pass_condition": _security_pass_condition_for_issue(issue),
                "severity": _safe_text(issue.get("severity")) or "medium",
                "source": _safe_text(issue.get("id")) or "public_technology_risks",
            }
        )
    return tasks

def _build_site_health_checks(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    site_health = results.get("site_health") or {}
    if not isinstance(site_health, dict):
        site_health = {}

    checks: List[Dict[str, Any]] = []
    definitions = (
        ("ogp", "OGP", 80.0, 50.0),
        ("security", "セキュリティ", 70.0, 40.0),
        ("accessibility", "見やすさ・使いやすさ", 80.0, 50.0),
    )
    for key, title, pass_threshold, warn_threshold in definitions:
        payload = site_health.get(key) or {}
        formatted = payload.get("formatted") or {}
        if not isinstance(formatted, dict) or not formatted:
            continue

        score = float(formatted.get("score", 0.0) or 0.0)
        status = _score_status(score, good=pass_threshold, warn=warn_threshold)
        detail_bits = [f"スコア {score:.0f}点"]
        formatted_status = _safe_text(formatted.get("status"))
        if formatted_status:
            detail_bits.append(formatted_status)
        if key == "accessibility":
            source = _safe_text(payload.get("source") or formatted.get("detection_source"))
            if source:
                detail_bits.append("実ブラウザ自動検出" if source == "browser" else "HTML自動検出")
        raw = payload.get("raw") or {}
        public_technology_risks = {}
        public_issues: List[Dict[str, Any]] = []
        maintenance_risk = {}
        if key == "security" and isinstance(raw, dict):
            public_technology_risks = raw.get("public_technology_risks") or {}
            if isinstance(public_technology_risks, dict):
                public_issues = [
                    item for item in (public_technology_risks.get("issues") or [])
                    if isinstance(item, dict)
                ]
                if public_issues:
                    detail_bits.append(f"公開技術リスク {len(public_issues)}件")
            maintenance_risk = build_maintenance_risk_summary({"site_health": site_health})
            if maintenance_risk:
                detail_bits.append(f"保守更新スコア {maintenance_risk.get('score', 100)}点")

        highlights = _brief_texts(formatted.get("items") or [], keys=("subtext", "text"), limit=3)
        if public_issues:
            public_highlights = _brief_texts(public_issues, keys=("title", "issue", "detail"), limit=3)
            highlights = public_highlights + [item for item in highlights if item not in public_highlights]
            highlights = highlights[:3]
        if not highlights:
            highlights = _brief_texts(formatted.get("recommendations") or [], keys=("recommendation",), limit=3)
        if not highlights:
            highlights = _brief_texts(formatted.get("issues") or [], keys=("issue", "suggestion"), limit=3)
        if highlights:
            detail_bits.append(highlights[0])

        checks.append(
            {
                "key": key,
                "title": title,
                "detail": " / ".join([bit for bit in detail_bits if bit]),
                "status": status,
                "status_label": _snapshot_status_label(status),
                "score": round(score, 1),
                "highlights": highlights,
                "items": _json_clone((formatted.get("items") or [])[:10]) or [],
                "recommendations": _brief_texts(formatted.get("recommendations") or [], keys=("recommendation",), limit=4),
                "issues": _brief_texts(public_issues or formatted.get("issues") or [], keys=("title", "issue", "detail", "suggestion"), limit=6),
                "public_technology_risks": _json_clone(public_technology_risks) or {},
                "maintenance_risk": _json_clone(maintenance_risk) or {},
                "engineer_tasks": _build_security_engineering_tasks(
                    issues=public_issues,
                    url=_safe_text(results.get("url")),
                ) if key == "security" else [],
            }
        )
    return checks

def _build_schema_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    schema_existing = results.get("schema_existing") or {}
    schema_suggestions = results.get("schema_suggestions") or []
    site_health = results.get("site_health") or {}
    structured_data = (site_health.get("structured_data") or {}) if isinstance(site_health, dict) else {}
    types = [str(item).strip() for item in (schema_existing.get("types") or []) if str(item).strip()]
    faq_validation = ((results.get("faq_detection") or {}).get("validation") or {})
    summary_lines: List[str] = []
    suggestion_rows = []
    missing_suggestions = 0
    if types:
        summary_lines.append(f"検出schema: {', '.join(types[:6])}")
    else:
        summary_lines.append("検出schema: なし")
    summary_lines.append(f"FAQPage: {'あり' if 'FAQPage' in types else 'なし'}")
    schema_site_type = _safe_text(structured_data.get("schema_site_type"))
    if schema_site_type:
        summary_lines.append(f"推定ページ型: {schema_site_type}")
    if faq_validation:
        summary_lines.append(
            f"FAQ整合: {faq_validation.get('consistent_count', 0)}/{faq_validation.get('checked', 0)}"
            f"（{faq_validation.get('consistency_level', '-')})"
        )
    for suggestion in schema_suggestions[:3]:
        if not isinstance(suggestion, dict):
            continue
        schema_type = _safe_text(suggestion.get("schema_type")) or "Schema"
        already_present = bool(suggestion.get("already_present"))
        if not already_present:
            missing_suggestions += 1
        explanation = suggestion.get("explanation") or {}
        summary = _safe_text(explanation.get("what_is")) or _safe_text(explanation.get("why_it_matters"))
        why_for_ai_answer = _safe_text(explanation.get("why_it_matters")) or f"{schema_type}としてページの役割を機械に伝え、AI回答で引用しやすい形にするためです。"
        required_fields_source = suggestion.get("required_fields")
        required_fields = required_fields_source if isinstance(required_fields_source, list) else ["@context", "@type", "name", "url"]
        suggestion_rows.append(
            {
                "schema_type": schema_type,
                "priority": _safe_text(suggestion.get("priority")) or "secondary",
                "already_present": already_present,
                "status": "pass" if already_present else "warn",
                "status_label": "設定済み" if already_present else "未設定",
                "summary": summary,
                "template": _safe_text(suggestion.get("template")),
                "why_for_ai_answer": why_for_ai_answer,
                "required_fields": _safe_text_list(required_fields, limit=8),
                "example_jsonld": _safe_text(suggestion.get("template")),
                "fix_location": "対象ページのhead内、またはCMSの構造化データ設定欄",
                "validation_method": "Google Rich Results Test / Schema Markup Validator で警告と必須項目を確認",
            }
        )
    suspicious_items = _json_clone((faq_validation.get("suspicious_items") or [])[:5]) or []
    if not types and suggestion_rows:
        status = "fail"
    elif suspicious_items or missing_suggestions > 0:
        status = "warn"
    elif types:
        status = "pass"
    else:
        # No structured-data payload is an unverified state, not a positive
        # reference result.  Keep the distinction for saved snapshots and
        # every downstream export.
        status = "unverified"
    detail_bits = [f"検出 {len(types)}種"]
    if suggestion_rows:
        detail_bits.append(f"追加候補 {len([row for row in suggestion_rows if not row.get('already_present')])}件")
    if "FAQPage" in types:
        detail_bits.append("FAQPage あり")
    elif suggestion_rows:
        detail_bits.append("FAQPage なし")
    return {
        "title": "構造化データ",
        "types": types,
        "faqpage_present": "FAQPage" in types,
        "validation": _json_clone(faq_validation) or {},
        "raw": _json_clone(schema_existing) or {},
        "summary_lines": summary_lines,
        "detail": " / ".join(detail_bits),
        "status": status,
        "status_label": _snapshot_status_label(status),
        "site_type": schema_site_type,
        "suggestions": suggestion_rows,
        "validation_issues": suspicious_items,
        "validation_method": "Google Rich Results Test / Schema Markup Validator",
        "command": "構造化データテストで対象URLを検証",
        "pass_condition": "必須プロパティのエラーがなく、本文FAQとJSON-LDの質問・回答が一致している",
    }

build_legacy_page_summary = _build_legacy_page_summary
build_llms_summary = _build_llms_summary
build_llms_notes = _build_llms_notes
build_reference_notes = _build_reference_notes
build_crawl_scope_summary = _build_crawl_scope_summary
build_link_health_summary = _build_link_health_summary
build_site_health_checks = _build_site_health_checks
build_schema_summary = _build_schema_summary
